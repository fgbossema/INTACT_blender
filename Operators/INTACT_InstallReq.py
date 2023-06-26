# Python imports :
import sys, os, bpy, socket, shutil
from importlib import import_module
from os.path import dirname, join, realpath, abspath, exists
from subprocess import call


#############################################################
def ShowMessageBox(message=[], title="INFO", icon="INFO"):
    def draw(self, context):
        for txtLine in message:
            self.layout.label(text=txtLine)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


#############################################################
def isConnected():
    try:
        sock = socket.create_connection(("www.google.com", 80))
        if sock is not None:
            print("Closing socket")
            sock.close
        return True
    except OSError:
        pass
        return False


#############################################################
def ImportReq(REQ_DICT):
    Pkgs = []
    for mod, pkg in REQ_DICT.items():
        try:
            import_module(mod)
        except ImportError:
            Pkgs.append(pkg)

    return Pkgs


#############################################################
def ReqInternetInstall(path, modules):
    # Download and install requirement if not AddonPacked version:
    if bpy.app.version >= (2, 80, 0):
        PythonPath = sys.executable
    else:
        PythonPath = bpy.app.binary_path_python

    call(f'"{PythonPath}" -m ensurepip ', shell=True)

    for module in modules:
        command = f' "{PythonPath}" -m pip install {module} --target "{path}" '
        call(command, shell=True)


#############################################################
def ReqInstall(REQ_DICT, REQ_ZIP_DIR, INTACT_Modules_DIR):

    Pkgs = list(REQ_DICT.values())
    Preffix = sys.platform
    ZippedModuleFiles = [f"{Preffix}_{Pkg}.zip" for Pkg in Pkgs]
    condition = all([(mod in os.listdir(REQ_ZIP_DIR)) for mod in ZippedModuleFiles])

    if condition:
        os.chdir(REQ_ZIP_DIR)
        for Pkg in ZippedModuleFiles:
            shutil.unpack_archive(Pkg, INTACT_Modules_DIR)

        print("Requirements installed from ARCHIVE!")
        print("Please Restart Blender")
        message = [
            "Required Modules installation completed! ",
            "Please Restart Blender",
        ]
        ShowMessageBox(message=message, icon="COLORSET_03_VEC")

    else:
        if isConnected():

            ReqInternetInstall(path=INTACT_Modules_DIR, modules=Pkgs)

            ##########################
            print("requirements Internet installation completed.")
            print("Please Restart Blender")
            message = [
                "Required Modules installation completed! ",
                "Please Restart Blender",
            ]
            ShowMessageBox(message=message, icon="COLORSET_03_VEC")

        else:
            message = ["Please Check Internet Connexion and retry! "]
            ShowMessageBox(message=message, icon="COLORSET_02_VEC")
            print(message)


#############################################################
# Install Requirements Operators :
#############################################################


class INTACT_OT_InstallRequirements(bpy.types.Operator):
    """ Requirement installer """

    bl_idname = "intact.installreq"
    bl_label = "INSTALL INTACT MODULES"

    def execute(self, context):

        REQ_DICT = {
            "SimpleITK": "SimpleITK==2.0.2",
            "vtk": "vtk==9.0.1",
            "cv2": "opencv-contrib-python==4.4.0.46",
        }
        ADDON_DIR = dirname(dirname(abspath(__file__)))
        REQ_ZIP_DIR = join(ADDON_DIR, "Resources", "REQ_ZIP_DIR")
        INTACT_Modules_DIR = join(os.path.expanduser("~/INTACT_Modules"))
        INTACT_Theme = join(ADDON_DIR, "Resources", "INTACT.xml")

        ReqInstall(REQ_DICT, REQ_ZIP_DIR, INTACT_Modules_DIR)

        return {"FINISHED"}


class INTACT_PT_InstallReqPanel(bpy.types.Panel):
    """ Install Req Panel"""

    bl_idname = "INTACT_PT_InstallReqPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # blender 2.7 and lower = TOOLS
    bl_category = "INTACT"
    bl_label = "INTACT"
    # bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("intact.installreq")


#################################################################################################
# Registration :
#################################################################################################

classes = [
    INTACT_OT_InstallRequirements,
    INTACT_PT_InstallReqPanel,
]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
