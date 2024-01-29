# 3DFin QGIS plugin

This is a proof of concept of QGIS plugin for 3DFin processing. It will eventually be part of the 3DFin directory.
for now build is managed by https://pypi.org/project/hatch-zipped-directory/ but the root directory could be zipped by anything :).

## Installation

QGIS Plugin installation with external dependencies suffers from multiple issues that are summarized in these
threads.
 - https://github.com/qgis/QGIS-Enhancement-Proposals/issues/179
 - https://github.com/opengisch/QgisModelBaker/pull/644
For the "possible collision in dependencies" issue, the same may apply to CloudCompare and "pure pip" contexts but the latters offer the advantage of having a mechanism to handle virtual environements. Hopefully, at this point, dependencies installed by 3DFin should not collides with one provided by OSGEO4W (but we should be careful with numpy and PyQT)

With HiDPI displays, it may requires at least QGIS 3.32 in order to display the QT dialog properly. On prior QGIS version the plugin works but the layout of the QT Dialog could be messed up (be smaller but still very usable) if you have a HiDPI display.

On Windows system you should use QGIS from [OSGEO4W network installer](https://www.qgis.org/en/site/forusers/alldownloads.html#osgeo4w-installer) and install `pip` during the installation process.

Then open the OSGEO4W console and install `3DFin` and its dependencies with `pip`
```console
python -m pip install 3DFin 
```

On Linux just pip install `3DFin` and install `QGIS` from your package manager. Please refer to your distribution documentation
to know how. On macOS the process should be roughly the same. 

The last step is to clone this repository and zip the folder.

```console
hatch build --target zipped-directory
```

In QGIS use the `Plugins > Manage and Install Plugins > Install From Zip`.

## How to use?

You should add a las/laz file to QGIS by using the "add Layer" menu entry. Please beware that the plugin will only work with Las/Laz point clouds for now. Then select the layer in the QGIS Tree layer, on the left of the window and click on the 3DFin button on the toolbar (or plugin > 3DFin).
