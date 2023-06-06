from PyQt5.QtWidgets import QAction, QMessageBox, QDockWidget
from PyQt5.QtCore import QEventLoop
from qgis.core import QgsMapLayerType, QgsApplication

from three_d_fin.gui.application import Application

from ._3dfin.processing import QGISLASProcessing

from pathlib import Path


def classFactory(iface):
    return _3DFinQGIS(iface)


def _create_app_and_run(plugin_processing: QGISLASProcessing, scalar_fields: list[str]):
    """Encapsulate the 3DFin GUI and processing.

    Parameters
    ----------
    plugin_processing : QGISLASProcessing
        The instance of FinProcessing dedicated to QGIS (as a plugin)
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

class _3DFinQGIS(object):
    is_running:bool = False

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
        if self.is_running:
            QMessageBox.information(
                None, "3DFin Plugin", "Another 3DFin instance is already running"
            )
            return
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
            # Shows python console. it's is needed as long as Dendromatics / 3DFin  use 
            # print functions instead of a proper logging management.
            from console import console
            if not console._console:
                self.iface.actionShowPythonDialog().trigger()
                console._console.setVisible(console._console.isUserVisible())
            # Process events now in order to shows console before 3DFin Dialog
            # Else 3DFin dialog could be put into the background
            QgsApplication.instance().processEvents()
            
            self.is_running = True
            pc_layer = layers[0]

            # get file path needed for the 3DFin processing implementation
            file_path = pc_layer.dataProvider().dataSourceUri()

            # get attributes name for the 3DFin processing implementation
            attributes = pc_layer.attributes().attributes()  # sic.
            attribute_names = [attribute.name() for attribute in attributes]

            plugin_processing = QGISLASProcessing(Path(file_path), self.iface)
            try:
                _create_app_and_run(plugin_processing, attribute_names)
            except Exception as e:
                raise e
            finally:
                self.is_running = False