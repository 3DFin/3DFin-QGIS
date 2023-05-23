# 3DFin QGIS plugin

This is a proof of concept of QGIS plugin for 3DFin processing. It is in a separate repository for now as it's not
clear, from a code architecture standpoint, if the plugin will be part of the main 3DFin repository in the end.

## Installation

QGIS Plugin installation with external dependencies suffers from multiple issues that are summarized in these
threads.
 - https://github.com/qgis/QGIS-Enhancement-Proposals/issues/179
 - https://github.com/opengisch/QgisModelBaker/pull/644
For the possible collision in dependencies, the same may apply to CloudComparet context but the latter offer 
the advantage of having a mechanism to handle virtual environements. Hopefully, at this point, dependencies installed 
by 3DFin should not collides with one from OSGEO4W.


On Windows you should rely on OSGEO4W distribution since the QGIS desktop installer does not ship with Tkinter.
the following package needs to be installed from OSGEO4W installer.
```    
python3-pip
python3-tcltk
qgis or qgis-nigtly, see below.
```

If you have an HDPi display you need at least QGIS 3.32 that come with a fix on scaling issue. Thus, as of may 2023,
you need to install nightly build of QGIS in OSGeo (and not 3.30). The fix is not fully operant (unlike in CloudCompare).
A PyQT version of 3DFin is under developement and should remove the need of tricky HDPI fix and remove the dependency on
TK.

Clone the 3DFin git repository somewhere on your computer (note that this step won't be necessary once 3DFin will be available on PyPi)
```console
git clone https://github.com/3DFin/3DFin.git
```

Then open the OSGEO4W console and install dependencies with pip
```console
python -m pip install path_to_3DFin_repository
```

On Linux just pip install 3DFin and install the python-tcltk package and QGIS too from your package manager. Please refer to your distribution documentation
to know how to. On macOS the process should be roughly the same.

Then clone this repository and zip the folder and in QGIS use the Plugins > Manage and Install Plugins > Install From Zip. 

## How to use?

You should add a las/laz file to QGIS by using the add Layer. Please beware that the plugin will only work with Las/Laz point clouds for now. Then select the layer in the QGIS Tree layer, on the left of the window and click on the 3DFin button on the toolbar (or plugin > 3DFin)