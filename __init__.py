# ----------------------------------------------------------
# File __init__.py
# ----------------------------------------------------------

#    Addon info
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Thres1ware Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Thres1ware Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
##############################################################################################
bl_info = {
    "name": "IntACT",  ###################Addon name
    "author": "Francien Bossema, Paul van Laar & Kimberly Meechan",
    "version": (1, 0, 0),
    "blender": (2, 90, 1),  ################# Blender working version
    "location": "3D View -> UI SIDE PANEL ",
    "description": "3D Tools suite for Cultural Heritage X-ray CT and 3D scan visualisation",  ########### Addon description
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "Cultural Heritage",  ################## Addon category
}
#############################################################################################
# IMPORTS :
#############################################################################################
# Python imports :
import sys, os, bpy
from importlib import import_module
from os.path import dirname, join, realpath, abspath, exists

from .Operators.INTACT_InstallReq import REQ_LIST, REQ_INSTALLATION_DIR


if sys.platform == "win32":
    sys.stdout.reconfigure(
        encoding="cp65001"
    )  # activate unicode characters in windows CLI

###################################################
if not exists(REQ_INSTALLATION_DIR):
    os.mkdir(REQ_INSTALLATION_DIR)

if not sys.path[0] == REQ_INSTALLATION_DIR:
    sys.path.insert(0, REQ_INSTALLATION_DIR)

#############################################################
def ImportReq(requirements_list):
    Pkgs = []
    for requirement in requirements_list:
        try:
            import_module(requirement.test_string)
        except ImportError:
            Pkgs.append(requirement.package_name)

    return Pkgs

NotFoundPkgs = ImportReq(REQ_LIST)
if NotFoundPkgs:
    ############################
    # Install Req Registration :
    ############################
    from .Operators import INTACT_InstallReq

    def register():

        INTACT_InstallReq.register()

    def unregister():

        INTACT_InstallReq.unregister()

    if __name__ == "__main__":
        register()

else:
    ######################
    # Addon Registration :
    ######################

    # Addon modules imports :
    from . import INTACT_Props, INTACT_Panel
    from .Operators import INTACT_ScanLoad, INTACT_Registration, INTACT_Visualisation, INTACT_ImagesOutput

    addon_modules = [
        INTACT_Props,
        INTACT_Panel,
        INTACT_ScanLoad,
        INTACT_Registration,
        INTACT_Visualisation,
        INTACT_ImagesOutput
    ]
    init_classes = []

    def register():

        for module in addon_modules:
            module.register()
        for cl in init_classes:
            bpy.utils.register_class(cl)

    def unregister():
        for cl in init_classes:
            bpy.utils.unregister_class(cl)
        for module in reversed(addon_modules):
            module.unregister()

    if __name__ == "__main__":
        register()
