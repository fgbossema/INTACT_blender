import stat
from os.path import split

# Blender Imports :
from bpy.props import (
    StringProperty,
    IntProperty,
    FloatProperty,
    EnumProperty,
    FloatVectorProperty,
    BoolProperty,
)
import SimpleITK as sitk
import vtk
import cv2

from vtk import vtkCommand

# Global Variables :

from .INTACT_Utils import *

ProgEvent = vtkCommand.ProgressEvent

#######################################################################################
########################### CT Scan Load : Operators ##############################
#######################################################################################
def rmtree(top):
    for root, dirs, files in os.walk(top, topdown=False):
        for name in files:
            filename = os.path.join(root, name)
            os.chmod(filename, stat.S_IWUSR)
            os.remove(filename)
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(top)

def GetMaxSerie(UserDcmDir):

    SeriesDict = {}
    Series_reader = sitk.ImageSeriesReader()
    series_IDs = Series_reader.GetGDCMSeriesIDs(UserDcmDir)

    if not series_IDs:

        message = ["No valid DICOM Serie found in DICOM Folder ! "]
        print(message)
        ShowMessageBox(message=message, icon="COLORSET_01_VEC")
        return {"CANCELLED"}

    def GetSerieCount(sID):
        count = len(Series_reader.GetGDCMSeriesFileNames(UserDcmDir, sID))
        SeriesDict[count] = sID

    threads = [
        threading.Thread(
            target=GetSerieCount,
            args=[sID],
            daemon=True,
        )
        for sID in series_IDs
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()
    MaxCount = sorted(SeriesDict, reverse=True)[0]
    MaxSerie = SeriesDict[MaxCount]
    return MaxSerie, MaxCount


def Load_function(context, image_type, q):

    ################################################################################################
    start = Tcounter()
    ################################################################################################
    INTACT_Props = context.scene.INTACT_Props
    UserProjectDir = AbsPath(INTACT_Props.UserProjectDir)
    UserDcmDir = AbsPath(INTACT_Props.UserDcmDir)
    UserTiffDir = AbsPath(INTACT_Props.UserTiffDir)
    UserImageFile = AbsPath(INTACT_Props.UserImageFile)
    INTACT_nrrd = False
    ################################################################################################

    if not exists(UserProjectDir):

        message = ["The Selected Project Directory Path is not valid ! "]
        ShowMessageBox(message=message, icon="COLORSET_02_VEC")
        return {"CANCELLED"}

    elif not (exists(UserDcmDir) or exists(UserTiffDir) or exists(UserImageFile)):

        message = [" The Selected Path is not valid ! "]
        ShowMessageBox(message=message, icon="COLORSET_02_VEC")
        return {"CANCELLED"}

    elif not os.listdir(UserDcmDir):
        message = ["No valid DICOM Serie found in DICOM Folder ! "]
        ShowMessageBox(message=message, icon="COLORSET_02_VEC")
        return {"CANCELLED"}

    else:
        # Get Preffix and save file :
        DcmInfoDict = eval(INTACT_Props.DcmInfo)
        Preffixs = list(DcmInfoDict.keys())

        for i in range(1, 100):
            Preffix = f"IT{i:03}"
            if not Preffix in Preffixs:
                break

        Split = split(UserProjectDir)
        ProjectName = Split[-1] or Split[-2]
        BlendFile = f"{ProjectName}_INTACT.blend"
        Blendpath = join(UserProjectDir, BlendFile)

        if not exists(Blendpath) or bpy.context.blend_data.filepath == Blendpath:
            bpy.ops.wm.save_as_mainfile(filepath=Blendpath)
        else:
            bpy.ops.wm.save_mainfile()

        # Start Reading data :
        ######################################################################################
        if image_type == 'Dicom':
            Series_reader = sitk.ImageSeriesReader()
            MaxSerie, MaxCount = GetMaxSerie(UserDcmDir)
            DcmSerie = Series_reader.GetGDCMSeriesFileNames(UserDcmDir, MaxSerie)

        ##################################### debug_02 ###################################
            debug_01 = Tcounter()
            message = f"MaxSerie ID : {MaxSerie}, MaxSerie Count : {MaxCount} (Time : {round(debug_01-start,2)} secondes)"
            print(message)
        
            # Get StudyInfo :
            reader = sitk.ImageFileReader()
            reader.SetImageIO('GDCMImageIO')
            reader.SetFileName(DcmSerie[0])
            reader.LoadPrivateTagsOn()
            reader.ReadImageInformation()

            Image3D = sitk.ReadImage(DcmSerie, imageIO='GDCMImageIO')
            Sp = Spacing = Image3D.GetSpacing()
        
        if image_type == 'Tiff':
            TiffSerie = sorted(os.listdir(UserTiffDir))
            MaxCount = len(TiffSerie)
            ##################################### debug_02 ###################################
            debug_01 = Tcounter()
            message = f"MaxSerie Count : {MaxCount} (Time : {round(debug_01-start,2)} secondes)"
            print(message)
  
            ####################################################################################
            print(UserTiffDir)
            # Get StudyInfo :
            reader = sitk.ImageFileReader()
            reader.SetImageIO('TIFFImageIO')
            reader.SetFileName(TiffSerie[0])
            reader.LoadPrivateTagsOn()
            TiffSerie = [os.path.join(UserTiffDir,s) for s in TiffSerie]
        
            Image3D = sitk.ReadImage(TiffSerie, imageIO='TIFFImageIO')
            Sp = Spacing = (INTACT_Props.Resolution, INTACT_Props.Resolution, INTACT_Props.Resolution)
            
        if image_type == 'Nrrd':
            reader = sitk.ImageFileReader()
            IO = reader.GetImageIOFromFileName(UserImageFile)
            FileExt = os.path.splitext(UserImageFile)[1]
            debug_01 = Tcounter()

            if not IO:
                message = [
                f"{FileExt} files are not Supported! for more info about supported files please refer to Addon wiki "
                ]
                ShowMessageBox(message=message, icon="COLORSET_01_VEC")
                return {"CANCELLED"}

            Image3D = sitk.ReadImage(UserImageFile)
            Sp = Spacing = Image3D.GetSpacing()
            
            Depth = Image3D.GetDepth()

            if Depth == 0:
                message = [
                "Can't Build 3D Volume from 2D Image !",
                ]
                ShowMessageBox(message=message, icon="COLORSET_01_VEC")
                return {"CANCELLED"}

            ImgFileName = os.path.split(UserImageFile)[1]
            
            if ImgFileName.startswith("IT") and ImgFileName.endswith("_Image3D255.nrrd"):
                INTACT_nrrd = True

            if not INTACT_nrrd:
                message = [
                    "Only INTACT nrrd images are supported !"
                ]
                ShowMessageBox(message=message, icon="COLORSET_01_VEC")
                return {"CANCELLED"}
         

        minmax = sitk.MinimumMaximumImageFilter()
        minmax.Execute(Image3D)
        Imax = minmax.GetMaximum()
        Imin = minmax.GetMinimum()

        # Get Dicom Info :
        
        Sz = Size = Image3D.GetSize()
		
        Dims = Dimensions = Image3D.GetDimension()
        Origin = Image3D.GetOrigin()
        Direction = Image3D.GetDirection()
		

        # calculate Informations :
        #D = Direction
        D = (1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, -1.0)
        O = Origin
        Direction = D

        DirectionMatrix_4x4 = Matrix(
            (
                (D[0], D[1], D[2], 0.0),
                (D[3], D[4], D[5], 0.0),
                (D[6], D[7], D[8], 0.0),
                (0.0, 0.0, 0.0, 1.0),
            )
        )

        TransMatrix_4x4 = Matrix(
            (
                (1.0, 0.0, 0.0, O[0]),
                (0.0, 1.0, 0.0, O[1]),
                (0.0, 0.0, 1.0, O[2]),
                (0.0, 0.0, 0.0, 1.0),
            )
        )

        VtkTransform_4x4 = TransMatrix_4x4 @ DirectionMatrix_4x4
        P0 = Image3D.TransformContinuousIndexToPhysicalPoint((0, 0, 0))
        P_diagonal = Image3D.TransformContinuousIndexToPhysicalPoint(
            (Sz[0] - 1, Sz[1] - 1, Sz[2] - 1)
        )
        VCenter = (Vector(P0) + Vector(P_diagonal)) * 0.5

        #C = (0.0,0.0,0.0)
        #VCenter = C
        C = VCenter

        TransformMatrix = Matrix(
            (
                (D[0], D[1], D[2], C[0]),
                (D[3], D[4], D[5], C[1]),
                (D[6], D[7], D[8], C[2]),
                (0.0, 0.0, 0.0, 1.0),
            ))
        # Set DcmInfo :

        DcmInfo = {
            "UserProjectDir": RelPath(UserProjectDir),
            "Preffix": Preffix,
            "RenderSz": Sz,
            "RenderSp": Sp,
            "PixelType": Image3D.GetPixelIDTypeAsString(),
            "Wmin": Imin,
            "Wmax": Imax,
            "Size": Sz,
            "Dims": Dims,
            "Spacing": Sp,
            "Origin": Origin,
            "Direction": Direction,
            "TransformMatrix": TransformMatrix,
            "DirectionMatrix_4x4": DirectionMatrix_4x4,
            "TransMatrix_4x4": TransMatrix_4x4,
            "VtkTransform_4x4": VtkTransform_4x4,
            "VolumeCenter": VCenter,
        }
        print(DcmInfo)

        ###################################### debug_02 ##################################
        debug_02 = Tcounter()
        message = f"DcmInfo {Preffix} set (Time : {debug_02-debug_01} secondes)"


        #######################################################################################
        # Add directories :
        SlicesDir = join(UserProjectDir, "Slices")
        if not exists(SlicesDir):
            os.makedirs(SlicesDir)
        DcmInfo["SlicesDir"] = RelPath(SlicesDir)

        PngDir = join(UserProjectDir, "PNG")
        if not exists(PngDir):
            os.makedirs(PngDir)

        Nrrd255Path = join(UserProjectDir, f"{Preffix}_Image3D255.nrrd")

        DcmInfo["Nrrd255Path"] = RelPath(Nrrd255Path)
         
        ###Set info in Image3D metadata:
        Image3D.SetSpacing(Sp)
        Image3D.SetDirection(D)
        Image3D.SetOrigin(O)
        
        #######################################################################################
        if INTACT_nrrd:
            Image3D_255 = Image3D
 
        else:
            #######################################################################################
            # set IntensityWindowing  :
            Image3D_255 = sitk.Cast(
                sitk.IntensityWindowing(
                    Image3D,
                    windowMinimum=Imin,
                    windowMaximum=Imax,
                    outputMinimum=0.0,
                    outputMaximum=255.0,
                ),
                sitk.sitkUInt8,
            )
            
            
        minmax = sitk.MinimumMaximumImageFilter()
        minmax.Execute(Image3D_255)
        Wmax = minmax.GetMaximum()
        Wmin = minmax.GetMinimum()
        INTACT_Props.Wmin = Wmin 
        INTACT_Props.Wmax = Wmax

        # Convert Dicom to nrrd file :
        if not INTACT_nrrd:
            sitk.WriteImage(Image3D_255, Nrrd255Path)

        ################################## debug_03 ######################################
        debug_03 = Tcounter()
        message = f"Nrrd255 Export done!  (Time : {debug_03-debug_02} secondes)"
        print(message)
        # q.put("nrrd 3D image file saved...")
        ##################################################################################

        #############################################################################################
        # MultiThreading PNG Writer:
        #########################################################################################
        def Image3DToPNG(i, slices, PngDir, Preffix):
            img_Slice = slices[i]
            img_Name = f"{Preffix}_img{i:04}.png"
            image_path = join(PngDir, img_Name)
            cv2.imwrite(image_path, img_Slice)
            image = bpy.data.images.load(image_path)
            image.pack()

        #########################################################################################
        # Get slices list :
        MaxSp = max(Vector(Sp))
        print(MaxSp)
        if MaxSp < 0.25:
            SampleRatio = round(MaxSp / 0.25, 2)
            Image3D_255 = ResizeImage(sitkImage=Image3D_255, Ratio=SampleRatio)
            DcmInfo["RenderSz"] = Image3D_255.GetSize()
            DcmInfo["RenderSp"] = Image3D_255.GetSpacing()
            print('Reducing number of slices for visualisation by ratio:', sample_ratio)

        Array = sitk.GetArrayFromImage(Image3D_255)
        slices = [np.flipud(Array[i, :, :]) for i in range(Array.shape[0])]
        print('Number of slices', len(slices))
 
        threads = [
            threading.Thread(
                target=Image3DToPNG,
                args=[i, slices, PngDir, Preffix],
                daemon=True,
            )
            for i in range(len(slices))
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # os.removedirs(PngDir)
        shutil.rmtree(PngDir)
        DcmInfo["CT_Loaded"] = True
        # Set DcmInfo property :
        DcmInfoDict = eval(INTACT_Props.DcmInfo)
        print(INTACT_Props.DcmInfo)
        DcmInfoDict[Preffix] = DcmInfo
        INTACT_Props.DcmInfo = str(DcmInfoDict)
        INTACT_Props.UserProjectDir = RelPath(INTACT_Props.UserProjectDir)
        bpy.ops.wm.save_mainfile() 


        #############################################################################################
        finish = Tcounter()
        message = f"Data Loaded in {finish-start} secondes"
        print(message)
        # q.put(message)
        #############################################################################################
        message = ["DICOM loaded successfully. "]
        ShowMessageBox(message=message, icon="COLORSET_03_VEC")
        
        #Remove Blenders default objects. 
        if 'Camera' in bpy.data.objects:
           bpy.data.objects.remove(bpy.data.objects["Camera"], do_unlink=True)
        if 'Cube' in bpy.data.objects:
           bpy.data.objects.remove(bpy.data.objects["Cube"], do_unlink=True)   
        if 'Light' in bpy.data.objects:
           bpy.data.objects.remove(bpy.data.objects["Light"], do_unlink=True)
        if 'Collection' in bpy.data.collections:
           bpy.data.collections.remove(bpy.data.collections["Collection"])
        # Fetch the area
        outliner = next(a for a in bpy.context.screen.areas if a.type == "OUTLINER") 
        # Fetch the space
        outliner.spaces[0].show_restrict_column_render = True

        return DcmInfo
    ####### End Load_Dicom_fuction ##############

    
##########################################################################################
######################### INTACT Volume Render : ########################################
##########################################################################################
class INTACT_OT_Volume_Render(bpy.types.Operator):
    """ Volume Render """

    bl_idname = "intact.volume_render"
    bl_label = "LOAD CT SCAN"

    q = Queue()

    def execute(self, context):

        Start = Tcounter()
        print("Data Loading START...")

        GpShader = "VGS_INTACT"
        GpThreshold = "VGS_Threshold"
        addon_dir = dirname(dirname(abspath(__file__)))
        ShadersBlendFile = join(addon_dir, "Resources", "BlendData", "INTACT_BlendData.blend")

        INTACT_Props = context.scene.INTACT_Props

        DataType = INTACT_Props.DataType
        if DataType == "TIFF Stack":
            DcmInfo = Load_function(context, 'Tiff', self.q)
        if DataType == "DICOM Series":
            DcmInfo = Load_function(context, 'Dicom', self.q)
        if DataType == "NRRD File":
            DcmInfo = Load_function(context, 'Nrrd', self.q)

        UserProjectDir = AbsPath(INTACT_Props.UserProjectDir)
        Preffix = DcmInfo["Preffix"]
        Wmin = INTACT_Props.Wmin
        Wmax = INTACT_Props.Wmax
        # PngDir = AbsPath(INTACT_Props.PngDir)
        print("\n##########################\n")
        print("Voxel Rendering START...")
        VolumeRender(DcmInfo, GpShader, ShadersBlendFile)
        scn = bpy.context.scene
        scn.render.engine = "BLENDER_EEVEE"
        INTACT_Props.GroupNodeName = GpShader
        INTACT_Props.ThresholdGroupNodeName = GpThreshold

        GpNode = bpy.data.node_groups.get(GpThreshold)
        Low_Treshold = GpNode.nodes["Low_Treshold"].outputs[0]
        Low_Treshold.default_value = 50
        WminNode = GpNode.nodes["WminNode"].outputs[0]
        WminNode.default_value = Wmin
        WmaxNode = GpNode.nodes["WmaxNode"].outputs[0]
        WmaxNode.default_value = Wmax

        INTACT_Props.CT_Rendered = True
        bpy.context.scene.unit_settings.scale_length = 0.001
        bpy.context.scene.unit_settings.length_unit = "MILLIMETERS"
        bpy.ops.view3d.view_selected(use_all_regions=False)
        bpy.ops.wm.save_mainfile()


        Finish = Tcounter()

        print(f"Finished (Time : {Finish-Start}")

        return {"FINISHED"}

class INTACT_OT_Surface_Render(bpy.types.Operator):
    """ Surface scan Render """

    bl_idname = "intact.obj_render"
    bl_label = "LOAD SURFACE SCAN"

    q = Queue()

    def execute(self, context):

        Start = Tcounter()
        print("Data Loading START...")

        INTACT_Props = context.scene.INTACT_Props

        #UserProjectDir = AbsPath(INTACT_Props.UserProjectDir)
        UserOBjDir = AbsPath(INTACT_Props.UserObjDir)
        print("\n##########################\n")
        print("Loading Surface scan...")
        
        if 'Surface' not in bpy.data.collections: 
            print('Make surface collection')
            bpy.data.collections.new('Surface')
            coll = bpy.data.collections.get('Surface')
            context.collection.children.link(coll)
            
            
        imported_object = bpy.ops.import_scene.obj(filepath=UserOBjDir, filter_glob="*.obj;*.mtl")
        obj_object = bpy.context.selected_objects[0] 
        obj_object.name = "IT_surface_" + obj_object.name
        
        bpy.data.collections['Surface'].objects.link(obj_object)
        bpy.context.scene.collection.objects.unlink(obj_object)
        
        
        #Remove Blenders default objects. 
        if 'Camera' in bpy.data.objects:
           bpy.data.objects.remove(bpy.data.objects["Camera"], do_unlink=True)
        if 'Cube' in bpy.data.objects:
           bpy.data.objects.remove(bpy.data.objects["Cube"], do_unlink=True)   
        if 'Light' in bpy.data.objects:
           bpy.data.objects.remove(bpy.data.objects["Light"], do_unlink=True)
        if 'Collection' in bpy.data.collections:
           bpy.data.collections.remove(bpy.data.collections["Collection"])
        
        
        # Fetch the area
        outliner = next(a for a in bpy.context.screen.areas if a.type == "OUTLINER") 
        # Fetch the space
        outliner.spaces[0].show_restrict_column_render = True

        #INTACT_Props.Surface_Rendered = True
        bpy.context.scene.unit_settings.scale_length = 0.001
        bpy.context.scene.unit_settings.length_unit = "MILLIMETERS"
        bpy.ops.view3d.view_selected(use_all_regions=False)
        bpy.ops.wm.save_mainfile()

        Finish = Tcounter()

        print(f"Finished (Time : {Finish-Start}")

        return {"FINISHED"}



#################################################################################################
# Registration :
#################################################################################################

classes = [
    INTACT_OT_Volume_Render,
    INTACT_OT_Surface_Render,
]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)
    post_handlers = bpy.app.handlers.depsgraph_update_post
    MyPostHandlers = [
        "AxialSliceUpdate",
        "CoronalSliceUpdate",
        "SagitalSliceUpdate",
    ]

    # Remove old handlers :
    handlers_To_Remove = [h for h in post_handlers if h.__name__ in MyPostHandlers]
    if handlers_To_Remove:
        for h in handlers_To_Remove:
            bpy.app.handlers.depsgraph_update_post.remove(h)

    handlers_To_Add = [
        AxialSliceUpdate,
        CoronalSliceUpdate,
        SagitalSliceUpdate,
    ]
    for h in handlers_To_Add:
        post_handlers.append(h)



def unregister():

    post_handlers = bpy.app.handlers.depsgraph_update_post
    MyPostHandlers = [
        "AxialSliceUpdate",
        "CoronalSliceUpdate",
        "SagitalSliceUpdate",
    ]
    handlers_To_Remove = [h for h in post_handlers if h.__name__ in MyPostHandlers]

    if handlers_To_Remove:
        for h in handlers_To_Remove:
            bpy.app.handlers.depsgraph_update_post.remove(h)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)