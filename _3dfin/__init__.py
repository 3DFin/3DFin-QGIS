
from PyQt5.QtWidgets import QAction, QMessageBox
from qgis.core import QgsMapLayerType, QgsTask, QgsApplication

from three_d_fin.gui.layout import Application

from ._3dfin.processing import QGISLASProcessing

from pathlib import Path

def classFactory(iface):
    return _3DFinQGIS(iface)


def _create_app_and_run(
    plugin_processing: QGISLASProcessing, scalar_fields: list[str]
):
    """Encapsulate the 3DFin GUI and processing.

    It also embed a custom fix for the HiDPI support that is broken when using tk
    under the CloudCompare runtime. This function allow to run the fix and the app
    on a dedicated thread thanx to pycc.RunInThread.

    Parameters
    ----------
    plugin_processing : CloudComparePluginProcessing
        The instance of FinProcessing dedicated to CloudCompare (as a plugin)
    scalar_fields : list[str]
        A list of scalar field names. These list will feed the dropdown menu
        inside the 3DFin GUI.
    """
    # FIX for HiDPI support on windows 10+
    # The "bug" was sneaky for two reasons:
    # - First, you should turn the DpiAwareness value to a counter intuitive value
    # in other context you would assume to turn Dpi awarness at least >= 1 (PROCESS_SYSTEM_DPI_AWARE)
    # but here, with TK the right value is 0 (PROCESS_DPI_UNAWARE) maybe because DPI is handled by CC process
    # - Second, you can't use the usual SetProcessDpiAwareness function here because it could not be redefined
    # when defined once somewhere (TODO: maybe we could try to redefine it at startup of CC-PythonPlugin see if it works)
    # so we have to force it for the current thread with this one:
    # TODO: we do not know how it's handled in other OSes.
    import ctypes
    import platform

    awareness_code = ctypes.c_int()
    if platform.system() == "Windows" and (
        platform.release() == "10" or platform.release() == "11"
    ):
        import ctypes.wintypes  # reimport here, because sometimes it's not initialized

        ctypes.windll.shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness_code))
        if awareness_code.value > 0:
            ctypes.windll.user32.SetThreadDpiAwarenessContext(
                ctypes.wintypes.HANDLE(-1)
            )
    fin_app = Application(
        plugin_processing, file_externally_defined=True, cloud_fields=scalar_fields
    )
    fin_app.run()


class _3DFinQGIS:
    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        # create action that will start plugin configuration
        self.action = QAction("3DFin",
                          self.iface.mainWindow())
        self.action.setObjectName("3DFinAction")
        self.action.setWhatsThis("Run 3DFin Plugin")
        self.action.setStatusTip("Automatic dendrometry and forest inventory for terrestrial point clouds")
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
        if len(layers) == 0 or len(layers) > 1 or layers[0].type() != QgsMapLayerType.PointCloud:
            QMessageBox.information(None, "3DFin Plugin", "Please select a single point cloud layer")
            return
        else: 
            pc_layer = layers[0]

            # get file path needed for the 3DFin processing implementation
            file_path = pc_layer.dataProvider().dataSourceUri()
            
            # get attributes name for the 3DFin processing implementation
            attributes = pc_layer.attributes().attributes() # sic.
            attribute_names = [attribute.name() for attribute in attributes]
            
            plugin_processing = QGISLASProcessing(Path(file_path), self.iface)
            #fin_task = QgsTask.fromFunction("3DFin processing", _create_app_and_run, plugin_processing, attribute_names)
            print(file_path)
            _create_app_and_run(plugin_processing, attribute_names)

