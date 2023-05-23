from pathlib import Path

import laspy
import sys

from three_d_fin.processing.standalone_processing import StandaloneLASProcessing
from three_d_fin.processing.progress import Progress
from qgis.core import QgsPointCloudLayer, QgsProject


class QGISLASProcessing(StandaloneLASProcessing):
    """Implement the FinProcessing interface for LAS files QGIS execution context.
    
    Since we are working on filesytem it's basically the same as the standalone.
    """

    def __init__(self, filename, qgis_instance):
        super().__init__()
        self.filename = filename
        self.qgis_instance = qgis_instance
        self.progress = Progress(output=sys.stdout)

    def _construct_output_path(self):
        basename_las = self.filename.stem
        self.output_basepath = Path(self.config.misc.output_dir) / Path(basename_las)
        self.dtm_path = str(self.output_basepath) + "_dtm_points.las"
        self.stripe_path = str(self.output_basepath) + "_stripe.las"
        self.tree_id_dist_axes_path = (
            str(self.output_basepath) + "_tree_ID_dist_axes.las"
        )
        self.tree_height_path = str(self.output_basepath) + "_tree_heights.las"
        self.circ_path = str(self.output_basepath) + "_circ.las"
        self.axes_path = str(self.output_basepath) + "_axes.las"
        self.tree_locator_path = str(self.output_basepath) + "_tree_locator.las"

    def _load_cloud(self, path: str, name: str, visible: bool = True):
        """Load individual an point cloud into QGIS
        
        Parameters
        ----------

        path : str
            The path to the point cloud
        name : str
            The name of the cloud to be displayed In QGIS LayerTree
        visible : bool
            Whether the cloud should be se visible or not.
        """
        layer = QgsPointCloudLayer(path, name, "PDAL")
        if not layer.isValid():
            print(f"Layer {name} failed to load!")

        else:
            project_instance = QgsProject().instance()
            project_instance.addMapLayer(layer)
            if not visible:
                node_layer = project_instance.layerTreeRoot().findLayer(layer.id())
                node_layer.setItemVisibilityChecked(False)

    def _post_processing_hook(self):  # touched
        """Load resulting point clouds on QGIS"""
        self._load_cloud(self.dtm_path, "DTM", False)
        self._load_cloud(self.stripe_path, "Stems in stripe", False)
        self._load_cloud(self.tree_id_dist_axes_path, "Tree_ID", False)
        self._load_cloud(self.tree_height_path, "Highest points", False)
        self._load_cloud(self.circ_path, "Fitted sections")
        self._load_cloud(self.axes_path, "Axes")
        self._load_cloud(self.tree_locator_path, "Tree locator", False)

    def _load_base_cloud(self):
        self.base_cloud = laspy.read(str(self.filename))  # touched
