import bpy
import stat
import os
import threading
import shutil
import numpy as np
from time import perf_counter as Tcounter
from os.path import split, join, exists, abspath, dirname
from queue import Queue
from mathutils import Matrix, Vector
import SimpleITK as sitk
import cv2

from vtkmodules.vtkCommonCore import vtkCommand
from . import INTACT_Utils as utils

# Global Variables :
ProgEvent = vtkCommand.ProgressEvent


def rmtree(top):
    for root, dirs, files in os.walk(top, topdown=False):
        for name in files:
            filename = join(root, name)
            os.chmod(filename, stat.S_IWUSR)
            os.remove(filename)
        for name in dirs:
            os.rmdir(join(root, name))
    os.rmdir(top)


def GetMaxSerie(UserDcmDir):

    SeriesDict = {}
    Series_reader = sitk.ImageSeriesReader()
    series_IDs = Series_reader.GetGDCMSeriesIDs(UserDcmDir)

    if not series_IDs:

        message = ["No valid DICOM Serie found in DICOM Folder ! "]
        print(message)
        utils.ShowMessageBox(message=message, icon="COLORSET_01_VEC")
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


def all_files_exist(user_project_dir, user_image_path, image_type):

    image_path_is_dir = os.path.isdir(user_image_path)

    if not exists(user_project_dir):

        message = ["The Selected Project Directory Path is not valid ! "]
        utils.ShowMessageBox(message=message, icon="COLORSET_02_VEC")
        return False

    elif not exists(user_image_path):

        message = [f" The Selected {image_type} Path is not valid ! "]
        utils.ShowMessageBox(message=message, icon="COLORSET_02_VEC")
        return False

    elif image_path_is_dir and not os.listdir(user_image_path):
        message = [f"No valid {image_type} stack found in folder ! "]
        utils.ShowMessageBox(message=message, icon="COLORSET_02_VEC")
        return False

    return True


def is_intact_nrrd(UserImageFile):
    image_filename = os.path.split(UserImageFile)[1]
    if image_filename.startswith("IT") and image_filename.endswith("_Image3D255.nrrd"):
        return True
    else:
        return False


def is_image_supported(UserImageFile):
    reader = sitk.ImageFileReader()
    IO = reader.GetImageIOFromFileName(UserImageFile)
    FileExt = os.path.splitext(UserImageFile)[1]

    if not IO:
        message = [
            f"{FileExt} files are not Supported! for more info about supported files please refer to Addon wiki "
        ]
        utils.ShowMessageBox(message=message, icon="COLORSET_01_VEC")
        return False

    Image3D = sitk.ReadImage(UserImageFile)
    Depth = Image3D.GetDepth()

    if Depth == 0:
        message = [
            "Can't Build 3D Volume from 2D Image !",
            "for more info about supported files,",
            "please refer to Addon wiki",
        ]
        utils.ShowMessageBox(message=message, icon="COLORSET_01_VEC")
        return False

    INTACT_nrrd = is_intact_nrrd(UserImageFile)

    HU_Image = False
    if Image3D.GetPixelIDTypeAsString() in [
        "32-bit signed integer",
        "16-bit signed integer",
    ]:
        HU_Image = True

    if not INTACT_nrrd and not HU_Image:
        message = [
            "Only Images with Hunsfield data or INTACT nrrd images are supported !"
        ]
        utils.ShowMessageBox(message=message, icon="COLORSET_01_VEC")
        return False

    return True


def save_blend_file(user_project_dir):

    Split = split(user_project_dir)
    ProjectName = Split[-1] or Split[-2]
    BlendFile = f"{ProjectName}_CT-SCAN.blend"
    Blendpath = join(user_project_dir, BlendFile)

    if not exists(Blendpath) or bpy.context.blend_data.filepath == Blendpath:
        bpy.ops.wm.save_as_mainfile(filepath=Blendpath)
    else:
        bpy.ops.wm.save_mainfile()


def read_dicom_image(user_dcm_dir):
    # Start Reading Dicom data :
    Series_reader = sitk.ImageSeriesReader()
    MaxSerie, MaxCount = GetMaxSerie(user_dcm_dir)
    DcmSerie = Series_reader.GetGDCMSeriesFileNames(user_dcm_dir, MaxSerie)

    # Get StudyInfo :
    reader = sitk.ImageFileReader()
    reader.SetImageIO('GDCMImageIO')
    reader.SetFileName(DcmSerie[0])
    reader.LoadPrivateTagsOn()
    reader.ReadImageInformation()

    Image3D = sitk.ReadImage(DcmSerie, imageIO='GDCMImageIO')

    # Get Dicom Info :
    Spacing = Image3D.GetSpacing()
    Size = Image3D.GetSize()
    Origin = Image3D.GetOrigin()

    return Image3D, Spacing, Size, Origin


def read_tiff_image(user_tiff_dir, resolution):
    TiffSerie = sorted(os.listdir(user_tiff_dir))

    # Get StudyInfo :
    reader = sitk.ImageFileReader()
    reader.SetImageIO('TIFFImageIO')
    reader.SetFileName(TiffSerie[0])
    reader.LoadPrivateTagsOn()
    TiffSerie = [join(user_tiff_dir, s) for s in TiffSerie]

    Image3D = sitk.ReadImage(TiffSerie, imageIO='TIFFImageIO')

    # Get Info :
    Spacing = (resolution, resolution, resolution)
    Size = Image3D.GetSize()

    Origin = (
        -(Size[0]-1)/2*Spacing[0],
        (Size[1]-1)/2*Spacing[1],
        (Size[2]-1)/2*Spacing[2]
        )

    Image3D = sitk.Cast(Image3D, sitk.sitkFloat32)

    return Image3D, Spacing, Size, Origin


def read_nrrd_image(user_nrrd_path):
    reader = sitk.ImageFileReader()
    reader.SetFileName(user_nrrd_path)
    reader.LoadPrivateTagsOn()
    reader.ReadImageInformation()

    Image3D = reader.Execute()

    Spacing = Image3D.GetSpacing()
    Size = Image3D.GetSize()
    Origin = Image3D.GetOrigin()

    return Image3D, Spacing, Size, Origin


def get_min_max(Image3D):
    minmax = sitk.MinimumMaximumImageFilter()
    minmax.Execute(Image3D)
    Wmax = minmax.GetMaximum()
    Wmin = minmax.GetMinimum()

    return Wmin, Wmax


def flatten_matrix(matrix):
    dim = len(matrix)
    return [matrix[j][i] for i in range(dim) for j in range(dim)]


def get_matrices(Origin, Direction, VCenter):

    DirectionMatrix_4x4 = Matrix(
        (
            (Direction[0], Direction[1], Direction[2], 0.0),
            (Direction[3], Direction[4], Direction[5], 0.0),
            (Direction[6], Direction[7], Direction[8], 0.0),
            (0.0, 0.0, 0.0, 1.0),
        )
    )

    TransMatrix_4x4 = Matrix(
        (
            (1.0, 0.0, 0.0, Origin[0]),
            (0.0, 1.0, 0.0, Origin[1]),
            (0.0, 0.0, 1.0, Origin[2]),
            (0.0, 0.0, 0.0, 1.0),
        )
    )

    VtkTransform_4x4 = TransMatrix_4x4 @ DirectionMatrix_4x4

    TransformMatrix = Matrix(
        (
            (Direction[0], Direction[1], Direction[2], VCenter[0]),
            (Direction[3], Direction[4], Direction[5], VCenter[1]),
            (Direction[6], Direction[7], Direction[8], VCenter[2]),
            (0.0, 0.0, 0.0, 1.0),
        ))

    return TransformMatrix, DirectionMatrix_4x4, TransMatrix_4x4, VtkTransform_4x4


def create_image_info(UserProjectDir, Image3D, Spacing, Size,
                      Origin, Direction, VCenter, INTACT_Props):

    INTACT_Props.CT_ID = INTACT_Props.CT_ID + 1
    Prefix = f"IT{INTACT_Props.CT_ID:03}"

    Wmin, Wmax = get_min_max(Image3D)

    (TransformMatrix,
     DirectionMatrix_4x4,
     TransMatrix_4x4,
     VtkTransform_4x4) = get_matrices(Origin, Direction, VCenter)

    # Add directories :
    SlicesDir = join(UserProjectDir, "Slices")
    if not exists(SlicesDir):
        os.makedirs(SlicesDir)

    Nrrd255Path = join(UserProjectDir, f"{Prefix}_Image3D255.nrrd")

    image = INTACT_Props.Images.add()
    image.name = Prefix
    image.UserProjectDir = utils.RelPath(UserProjectDir)
    image.Prefix = Prefix
    image.RenderSz = Size
    image.RenderSp = Spacing
    image.PixelType = Image3D.GetPixelIDTypeAsString()
    image.Wmin = Wmin
    image.Wmax = Wmax
    image.Size = Size
    image.Dims = Image3D.GetDimension()
    image.Spacing = Spacing
    image.Origin = Origin
    image.Direction = Direction
    image.TransformMatrix = flatten_matrix(TransformMatrix)
    image.DirectionMatrix_4x4 = flatten_matrix(DirectionMatrix_4x4)
    image.TransMatrix_4x4 = flatten_matrix(TransMatrix_4x4)
    image.VtkTransform_4x4 = flatten_matrix(VtkTransform_4x4)
    image.VolumeCenter = VCenter
    image.SlicesDir = utils.RelPath(SlicesDir)
    image.Nrrd255Path = utils.RelPath(Nrrd255Path)

    INTACT_Props.UserProjectDir = utils.RelPath(INTACT_Props.UserProjectDir)
    bpy.ops.wm.save_mainfile()

    return image


def write_image(UserProjectDir, Image3D, ImageInfo, INTACT_Props,
                rescale_intensity=True, resize_image=True):
    # Set info in Image3D metadata:
    Image3D.SetSpacing(ImageInfo.Spacing)
    Image3D.SetDirection(ImageInfo.Direction)
    Image3D.SetOrigin(ImageInfo.Origin)

    if rescale_intensity:
        # set IntensityWindowing  :
        Image3D_255 = sitk.Cast(
            sitk.IntensityWindowing(
                Image3D,
                windowMinimum=ImageInfo.Wmin,
                windowMaximum=ImageInfo.Wmax,
                outputMinimum=0.0,
                outputMaximum=255.0,
            ),
            sitk.sitkUInt8,
        )
    else:
        Image3D_255 = Image3D
        print('Not rescaled')

    Wmin, Wmax = get_min_max(Image3D_255)
    INTACT_Props.Wmin = Wmin
    INTACT_Props.Wmax = Wmax

    # Convert Dicom to nrrd file :
    sitk.WriteImage(Image3D_255, utils.AbsPath(ImageInfo.Nrrd255Path))

    if resize_image:
        MaxSp = max(Vector(ImageInfo.Spacing))
        if MaxSp < 0.25:
            SampleRatio = round(MaxSp / 0.25, 2)
            Image3D_255 = utils.ResizeImage(sitkImage=Image3D_255,
                                            Ratio=SampleRatio)
            ImageInfo.RenderSz = Image3D_255.GetSize()
            ImageInfo.RenderSp = Image3D_255.GetSpacing()

    PngDir = join(UserProjectDir, "PNG")
    if not exists(PngDir):
        os.makedirs(PngDir)

    Array = sitk.GetArrayFromImage(Image3D_255)
    slices = [np.flipud(Array[i, :, :]) for i in range(Array.shape[0])]

    threads = [
        threading.Thread(
            target=Image3DToPNG,
            args=[i, slices, PngDir, ImageInfo.Prefix],
            daemon=True,
        )
        for i in range(len(slices))
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    shutil.rmtree(PngDir)


def Image3DToPNG(i, slices, PngDir, Prefix):
    """MultiThreading PNG Writer"""
    img_Slice = slices[i]
    img_Name = f"{Prefix}_img{i:04}.png"
    image_path = join(PngDir, img_Name)
    cv2.imwrite(image_path, img_Slice)
    image = bpy.data.images.load(image_path)
    image.pack()
    # print(f"{img_Name} was processed...")


def set_blender_properties():
    """Remove blender's default objects and ensure render column is visible in
    outliner"""

    # Remove Blenders default objects.
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


def calculate_vcenter(Image3D, Size):
    P0 = Image3D.TransformContinuousIndexToPhysicalPoint((0, 0, 0))
    P_diagonal = Image3D.TransformContinuousIndexToPhysicalPoint(
        (Size[0] - 1, Size[1] - 1, Size[2] - 1)
    )
    VCenter = (Vector(P0) + Vector(P_diagonal)) * 0.5

    return VCenter


def load_image_function(context, q, imageType, imagePath):

    INTACT_Props = context.scene.INTACT_Props
    UserProjectDir = utils.AbsPath(INTACT_Props.UserProjectDir)
    UserImagePath = utils.AbsPath(imagePath)

    if not all_files_exist(UserProjectDir, UserImagePath, imageType):
        return {"CANCELLED"}
    else:
        startTime = Tcounter()
        save_blend_file(UserProjectDir)
        rescale_intensity = True
        resize_image = True

        if imageType == "DICOM":
            (Image3D,
             Spacing,
             Size,
             Origin) = read_dicom_image(UserImagePath)

            VCenter = calculate_vcenter(Image3D, Size)
            Direction = (1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, -1.0)

        elif imageType == "TIFF":
            (Image3D,
             Spacing,
             Size,
             Origin) = read_tiff_image(UserImagePath, INTACT_Props.Resolution)
            VCenter = (0.0, 0.0, 0.0)
            Direction = (1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, -1.0)
            resize_image = False

        elif imageType == "NRRD" and is_image_supported(UserImagePath):
            (Image3D,
             Spacing,
             Size,
             Origin) = read_nrrd_image(UserImagePath)

            VCenter = calculate_vcenter(Image3D, Size)
            Direction = Image3D.GetDirection()
            if is_intact_nrrd(UserImagePath):
                rescale_intensity = False

        else:
            return {"CANCELLED"}

        ImageInfo = create_image_info(UserProjectDir, Image3D, Spacing, Size,
                                      Origin, Direction, VCenter, INTACT_Props)
        write_image(UserProjectDir, Image3D, ImageInfo, INTACT_Props,
                    rescale_intensity, resize_image)
        ImageInfo.CT_Loaded = True

        finishTime = Tcounter()
        message = f"Data Loaded in {finishTime-startTime} seconds"
        print(message)
        # q.put(message)

        if (imageType != "NRRD"):
            message = [f"{imageType} loaded successfully. "]
            utils.ShowMessageBox(message=message, icon="COLORSET_03_VEC")

        set_blender_properties()

        return ImageInfo


def set_scale_mm():
    bpy.context.scene.unit_settings.scale_length = 0.001
    bpy.context.scene.unit_settings.length_unit = "MILLIMETERS"
    bpy.ops.view3d.view_selected(use_all_regions=False)
    bpy.ops.wm.save_mainfile()


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
        ShadersBlendFile = join(addon_dir, "Resources", "BlendData",
                                "INTACT_BlendData.blend")

        INTACT_Props = context.scene.INTACT_Props

        DataType = INTACT_Props.DataType
        if DataType == "TIFF Stack":
            ImageInfo = load_image_function(context, self.q, "TIFF",
                                            INTACT_Props.UserTiffDir)
        if DataType == "DICOM Series":
            ImageInfo = load_image_function(context, self.q, "DICOM",
                                            INTACT_Props.UserDcmDir)
        if DataType == "NRRD File":
            ImageInfo = load_image_function(context, self.q, "NRRD",
                                            INTACT_Props.UserImageFile)

        if ImageInfo == {"CANCELLED"}:
            return {"CANCELLED"}

        Wmin = INTACT_Props.Wmin
        Wmax = INTACT_Props.Wmax

        print("\n##########################\n")
        print("Voxel Rendering START...")
        utils.VolumeRender(ImageInfo, GpShader, ShadersBlendFile)
        scn = bpy.context.scene
        scn.render.engine = "BLENDER_EEVEE"
        INTACT_Props.GroupNodeName = GpShader
        INTACT_Props.ThresholdGroupNodeName = GpThreshold

        GpNode = bpy.data.node_groups.get(GpThreshold)
        Low_Treshold = GpNode.nodes["Low_Treshold"].outputs[0]
        Low_Treshold.default_value = 100
        WminNode = GpNode.nodes["WminNode"].outputs[0]
        WminNode.default_value = Wmin
        WmaxNode = GpNode.nodes["WmaxNode"].outputs[0]
        WmaxNode.default_value = Wmax

        INTACT_Props.CT_Rendered = True
        set_scale_mm()

        for obj in bpy.context.scene.objects:
            if obj.name.startswith("IT") and obj.name.endswith("_CTVolume"):
                INTACT_Props.CT_Vol = obj

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
        UserOBjDir = utils.AbsPath(INTACT_Props.UserObjDir)

        print("\n##########################\n")
        print("Loading Surface scan...")

        set_blender_properties()

        if 'Surface' not in bpy.data.collections:
            print('Make surface collection')
            bpy.data.collections.new('Surface')
            coll = bpy.data.collections.get('Surface')
            context.collection.children.link(coll)

        bpy.ops.import_scene.obj(filepath=UserOBjDir, filter_glob="*.obj;*.mtl")
        obj_object = bpy.context.selected_objects[0]
        obj_object.name = "IT_surface_" + obj_object.name

        bpy.data.collections['Surface'].objects.link(obj_object)
        bpy.context.scene.collection.objects.unlink(obj_object)

        set_scale_mm()

        Finish = Tcounter()
        for obj in bpy.context.scene.objects:
            if obj.name.startswith("IT_surface_"):
                INTACT_Props.Surf_3D = obj

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
        utils.AxialSliceUpdate,
        utils.CoronalSliceUpdate,
        utils.SagitalSliceUpdate,
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
