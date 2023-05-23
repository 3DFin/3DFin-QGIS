from pathlib import Path

import laspy
import numpy as np
import sys

from three_d_fin.processing.abstract_processing import FinProcessing
from three_d_fin.processing.progress import Progress
from qgis.core import QgsPointCloudLayer, QgsProject


class QGISLASProcessing(FinProcessing):
    """Implement the FinProcessing interface for LAS files QGIS execution context."""

    def __init__(self, filename, qgis_instance): # touched
        super().__init__()
        self.filename = filename
        self.qgis_instance = qgis_instance
        self.progress = Progress(output = sys.stdout)

    def _construct_output_path(self): # touched
        basename_las = self.filename.stem
        self.output_basepath = Path(self.config.misc.output_dir) / Path(basename_las)
        self.dtm_path = str(self.output_basepath) + "_dtm_points.las"
        self.stripe_path = str(self.output_basepath) + "_stripe.las"
        self.tree_id_dist_axes_path = str(self.output_basepath) + "_tree_ID_dist_axes.las"
        self.tree_height_path = str(self.output_basepath) + "_tree_heights.las"
        self.circ_path = str(self.output_basepath) + "_circ.las"
        self.axes_path = str(self.output_basepath) + "_axes.las"
        self.tree_locator_path = str(self.output_basepath) + "_tree_locator.las"
    
    def check_already_computed_data(self) -> bool:
        """Check for already computed data in target directory."""
        self._construct_output_path()
        any_of = False
        # Check existence of las output
        any_of |= Path(self.dtm_path).exists()
        any_of |= Path(self.stripe_path).exists()
        any_of |= Path(self.tree_id_dist_axes_path).exists()
        any_of |= Path(self.tree_height_path).exists()
        any_of |= Path(self.circ_path).exists()
        any_of |= Path(self.axes_path).exists()
        any_of |= Path(self.tree_locator_path).exists()

        # Check existence of tabular output
        if self.config.misc.export_txt:
            any_of |= Path(str(self.output_basepath) + "_diameters.txt").exists()
            any_of |= Path(str(self.output_basepath) + "_X_c.txt").exists()
            any_of |= Path(str(self.output_basepath) + "_Y_c.txt").exists()
            any_of |= Path(str(self.output_basepath) + "_check_circle.txt").exists()
            any_of |= Path(str(self.output_basepath) + "_n_points_in.txt").exists()
            any_of |= Path(str(self.output_basepath) + "_sector_perct.txt").exists()
            any_of |= Path(str(self.output_basepath) + "_outliers.txt").exists()
            any_of |= Path(str(self.output_basepath) + "_dbh_and_heights.txt").exists()
            any_of |= Path(str(self.output_basepath) + "_sections.txt").exists()
        else:
            any_of |= Path(str(self.output_basepath) + ".xlsx").exists()
        # Check existence of ini output
        any_of |= Path(str(self.output_basepath) + "_config.ini").exists()

        return any_of

    def _pre_processing_hook(self):
        pass

    def _load_cloud(self, path:str, name:str): # touched
        layer = QgsPointCloudLayer(path, name, "PDAL")
        if not layer.isValid():
            print(f"Layer {name} failed to load!")
        else:
            QgsProject().instance().addMapLayer(layer)

    def _post_processing_hook(self): # touched
        """load resulting point clouds on QGIS"""
        self._load_cloud(self.dtm_path, "DTM")
        self._load_cloud(self.stripe_path, "Stems in stripe")
        self._load_cloud(self.tree_id_dist_axes_path, "Tree_ID")
        self._load_cloud(self.tree_height_path, "Highest points")
        self._load_cloud(self.circ_path, "Fitted sections")
        self._load_cloud(self.axes_path, "Axes")
        self._load_cloud(self.tree_locator_path,"Tree locator")


    def _load_base_cloud(self):
        self.base_cloud = laspy.read(str(self.filename)) # touched

    def _get_xyz_z0_from_base(self) -> np.ndarray:
        return np.vstack(
            (
                self.base_cloud.x,
                self.base_cloud.y,
                self.base_cloud.z,
                self.base_cloud[self.config.basic.z0_name],
            )
        ).transpose()

    def _get_xyz_from_base(self) -> np.ndarray:
        return np.vstack(
            (self.base_cloud.x, self.base_cloud.y, self.base_cloud.z)
        ).transpose()

    def _export_dtm(self, dtm: np.ndarray):
        las_dtm_points = laspy.create(point_format=2, file_version="1.4")
        las_dtm_points.x = dtm[:, 0]
        las_dtm_points.y = dtm[:, 1]
        las_dtm_points.z = dtm[:, 2]

        las_dtm_points.write(str(self.output_basepath) + "_dtm_points.las")

    def _export_stripe(self, clust_stripe: np.ndarray):
        las_stripe = laspy.create(point_format=2, file_version="1.4")
        las_stripe.x = clust_stripe[:, 0]
        las_stripe.y = clust_stripe[:, 1]
        las_stripe.z = clust_stripe[:, 2]

        las_stripe.add_extra_dim(laspy.ExtraBytesParams(name="tree_ID and dist axes", type=np.int32))
        las_stripe.tree_ID = clust_stripe[:, -1]
        las_stripe.write(str(self.output_basepath) + "_stripe.las")

    def _enrich_base_cloud(self, assigned_cloud: np.ndarray):
        self.base_cloud.add_extra_dims(
            [
                laspy.ExtraBytesParams(name="dist_axes", type=np.float64),
                laspy.ExtraBytesParams(name="tree_ID", type=np.int32),
            ]
        )

        self.base_cloud.dist_axes = assigned_cloud[:, 5]
        self.base_cloud.tree_ID = assigned_cloud[:, 4]

        if not self.config.misc.is_normalized:
            # In the case the user still want to use our CSF normalization but already have
            # a field called Z0, adding the field with the same name will raise an exception.
            # So we have to check its existence before.
            # In this case no need to ask if we want to override, since it's saved
            # in another file instance
            # TODO: Maybe name this field in accordance with z0_name value
            if self.base_cloud.Z0 is None:
                self.base_cloud.add_extra_dim(
                    laspy.ExtraBytesParams(name="Z0", type=np.float64)
                )
            self.base_cloud.Z0 = assigned_cloud[:, 3]

        if self.base_cloud.header.version < laspy.header.Version(major=1, minor=4):
            # The base file is maybe not in point_format == 6 but since it's a copy it won't hurt
            # the base file in it selft
            self.base_cloud = laspy.convert(
                self.base_cloud, point_format_id=2, file_version="1.4"
            )

        self.base_cloud.write(str(self.output_basepath) + "_tree_ID_dist_axes.las")

    def _export_tree_height(self, tree_heights):
        las_tree_heights = laspy.create(point_format=2, file_version="1.4")
        las_tree_heights.x = tree_heights[:, 0]
        las_tree_heights.y = tree_heights[:, 1]
        las_tree_heights.z = tree_heights[:, 2]
        las_tree_heights.add_extra_dims(
            [
                laspy.ExtraBytesParams(name="z0", type=np.float64),
                laspy.ExtraBytesParams(name="deviated", type=np.int32),
            ]
        )
        las_tree_heights.z0 = tree_heights[:, 3]
        # vertical deviation binary indicator
        las_tree_heights.deviated = tree_heights[:, 4]

        las_tree_heights.write(str(self.output_basepath) + "_tree_heights.las")

    def _export_circles(self, circles_coords: np.ndarray):
        # LAS file containing circle coordinates.
        las_circ = laspy.create(point_format=2, file_version="1.4")
        las_circ.x = circles_coords[:, 0]
        las_circ.y = circles_coords[:, 1]
        las_circ.z = circles_coords[:, 2]

        las_circ.add_extra_dims(
            [
                laspy.ExtraBytesParams(name="tree_ID", type=np.int32),
                laspy.ExtraBytesParams(
                    name="sector_occupancy_percent", type=np.float64
                ),
                laspy.ExtraBytesParams(name="pts_inner_circle", type=np.int32),
                laspy.ExtraBytesParams(name="Z0", type=np.float64),
                laspy.ExtraBytesParams(name="Diameter", type=np.float64),
                laspy.ExtraBytesParams(name="outlier_prob", type=np.float64),
                laspy.ExtraBytesParams(name="quality", type=np.int32),
            ]
        )

        las_circ.tree_ID = circles_coords[:, 4]
        las_circ.sector_occupancy_percent = circles_coords[:, 5]
        las_circ.pts_inner_circle = circles_coords[:, 6]
        las_circ.Z0 = circles_coords[:, 7]
        las_circ.Diameter = circles_coords[:, 8]
        las_circ.outlier_prob = circles_coords[:, 9]
        las_circ.quality = circles_coords[:, 10]

        las_circ.write(str(self.output_basepath) + "_circ.las")

    def _export_axes(self, axes_points: np.ndarray, tilt: np.ndarray):
        las_axes = laspy.create(point_format=2, file_version="1.4")
        las_axes.x = axes_points[:, 0]
        las_axes.y = axes_points[:, 1]
        las_axes.z = axes_points[:, 2]
        las_axes.add_extra_dim(
            laspy.ExtraBytesParams(name="tilting_degree", type=np.float64)
        )
        las_axes.tilting_degree = tilt

        las_axes.write(str(self.output_basepath) + "_axes.las")

    def _export_tree_locations(
        self, tree_locations: np.ndarray, dbh_values: np.ndarray
    ):
        las_tree_locations = laspy.create(point_format=2, file_version="1.4")
        las_tree_locations.x = tree_locations[:, 0]
        las_tree_locations.y = tree_locations[:, 1]
        las_tree_locations.z = tree_locations[:, 2]
        las_tree_locations.add_extra_dim(
            laspy.ExtraBytesParams(name="diameters", type=np.float64)
        )
        las_tree_locations.diameters = dbh_values[:, 0]

        las_tree_locations.write(str(self.output_basepath) + "_tree_locator.las")