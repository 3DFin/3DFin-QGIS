from PyQt5.QtWidgets import QAction, QMessageBox
from PyQt5.QtCore import QEventLoop
from qgis.core import QgsMapLayerType, QgsTask, QgsApplication

from three_d_fin.gui.application import Application

from ._3dfin.processing import QGISLASProcessing


def classFactory(iface):
    return _3DFinQGIS(iface)


def _create_app_and_run(plugin_processing: QGISLASProcessing, scalar_fields: list[str]):
    """Encapsulate the 3DFin GUI and processing.
    Parameters
    ----------
    plugin_processing : CloudComparePluginProcessing
        The instance of FinProcessing dedicated to CloudCompare (as a plugin)
    scalar_fields : list[str]
        A list of scalar field names. These list will feed the dropdown menu
        inside the 3DFin GUI.
    """
    plugin_widget = Application(
        plugin_processing, file_externally_defined=True, cloud_fields=scalar_fields
    )
    plugin_widget.show()
    loop = QEventLoop()
    plugin_widget.show()
    plugin_widget.set_event_loop(loop)
    loop.exec_()
class _3DFinQGIS:
    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        # create action that will start plugin configuration
        self.action = QAction("3DFin", self.iface.mainWindow())
        self.action.setObjectName("3DFinAction")
        self.action.setWhatsThis("Run 3DFin Plugin")
        self.action.setStatusTip(
            "Automatic dendrometry and forest inventory for terrestrial point clouds"
        )
        self.action.triggered.connect(self.run)

        # add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&3DFin", self.action)

    def unload(self):
        self.iface.removePluginMenu("&3DFin", self.action)
        self.iface.removeToolBarIcon(self.action)
        del self.action

    def run(self):
        layers = self.iface.layerTreeView().selectedLayers()
        if (
            len(layers) == 0
            or len(layers) > 1
            or layers[0].type() != QgsMapLayerType.PointCloud
        ):
            QMessageBox.information(
                None, "3DFin Plugin", "Please select a single point cloud layer"
            )
            return
        else:
            pc_layer = layers[0]

            # get file path needed for the 3DFin processing implementation
            file_path = pc_layer.dataProvider().dataSourceUri()

            # get attributes name for the 3DFin processing implementation
            attributes = pc_layer.attributes().attributes()  # sic.
            attribute_names = [attribute.name() for attribute in attributes]

            plugin_processing = QGISLASProcessing(Path(file_path), self.iface)
            # fin_task = QgsTask.fromFunction("3DFin processing", _create_app_and_run, plugin_processing, attribute_names)
            _create_app_and_run(plugin_processing, attribute_names)