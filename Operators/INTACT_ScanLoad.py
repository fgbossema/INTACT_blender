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
import cv2

from vtkmodules.vtkCommonCore import vtkCommand

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


def Load_Dicom_funtion(context, q):

    ################################################################################################
    start = Tcounter()
    ################################################################################################
    INTACT_Props = context.scene.INTACT_Props
    UserProjectDir = AbsPath(INTACT_Props.UserProjectDir)
    UserDcmDir = AbsPath(INTACT_Props.UserDcmDir)

    ################################################################################################

    if not exists(UserProjectDir):

        message = ["The Selected Project Directory Path is not valid ! "]
        ShowMessageBox(message=message, icon="COLORSET_02_VEC")
        return {"CANCELLED"}

    elif not exists(UserDcmDir):

        message = [" The Selected Dicom Directory Path is not valid ! "]
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

        # Start Reading Dicom data :
        ######################################################################################
        Series_reader = sitk.ImageSeriesReader()
        MaxSerie, MaxCount = GetMaxSerie(UserDcmDir)
        DcmSerie = Series_reader.GetGDCMSeriesFileNames(UserDcmDir, MaxSerie)

        ##################################### debug_02 ###################################
        debug_01 = Tcounter()
        message = f"MaxSerie ID : {MaxSerie}, MaxSerie Count : {MaxCount} (Time : {round(debug_01-start,2)} seconds)"
        print(message)
        # q.put("Max DcmSerie extracted...")
        ####################################################################################

        # Get StudyInfo :
        reader = sitk.ImageFileReader()
        reader.SetImageIO('GDCMImageIO')
        reader.SetFileName(DcmSerie[0])
        reader.LoadPrivateTagsOn()
        reader.ReadImageInformation()

        Image3D = sitk.ReadImage(DcmSerie, imageIO='GDCMImageIO')
        minmax = sitk.MinimumMaximumImageFilter()
        minmax.Execute(Image3D)
        Wmax = minmax.GetMaximum()
        Wmin = minmax.GetMinimum()
        INTACT_Props.Wmin = Wmin
        INTACT_Props.Wmax = Wmax

        # Get Dicom Info :
        Sp = Spacing = Image3D.GetSpacing()
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
            "Wmin": Wmin,
            "Wmax": Wmax,
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
        # tags = {
            # "StudyDate": "0008|0020",
            # "PatientName": "0010|0010",
            # "PatientID": "0010|0020",
            # "BirthDate": "0010|0030",
            # "WinCenter": "0028|1050",
            # "WinWidth": "0028|1051",
        # }
        # for k, tag in tags.items():

            # if tag in reader.GetMetaDataKeys():
                # v = reader.GetMetaData(tag)

            # else:
                # v = ""

            # DcmInfo[k] = v
            # Image3D.SetMetaData(tag, v)

        ###################################### debug_02 ##################################
        debug_02 = Tcounter()
        message = f"DcmInfo {Preffix} set (Time : {debug_02-debug_01} seconds)"
        print(Origin, Direction)
        # q.put("Dicom Info extracted...")
        ##################################################################################

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
        # set IntensityWindowing  :
        Image3D_255 = sitk.Cast(
            sitk.IntensityWindowing(
                Image3D,
                windowMinimum=Wmin,
                windowMaximum=Wmax,
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
        # sitk.WriteImage(Image3D, NrrdHuPath)
        sitk.WriteImage(Image3D_255, Nrrd255Path)

        ################################## debug_03 ######################################
        debug_03 = Tcounter()
        message = f"Nrrd255 Export done!  (Time : {debug_03-debug_02} seconds)"
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
            # print(f"{img_Name} was processed...")

        #########################################################################################
        # Get slices list :
        MaxSp = max(Vector(Sp))
        if MaxSp < 0.25:
            SampleRatio = round(MaxSp / 0.25, 2)
            Image3D_255 = ResizeImage(sitkImage=Image3D_255, Ratio=SampleRatio)
            DcmInfo["RenderSz"] = Image3D_255.GetSize()
            DcmInfo["RenderSp"] = Image3D_255.GetSpacing()
            print(sample_ratio)

        Array = sitk.GetArrayFromImage(Image3D_255)
        slices = [np.flipud(Array[i, :, :]) for i in range(Array.shape[0])]

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
        message = f"Data Loaded in {finish-start} seconds"
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

def Load_Tiff_function(context, q):

    ################################################################################################
    start = Tcounter()
    ################################################################################################
    INTACT_Props = context.scene.INTACT_Props
    UserProjectDir = AbsPath(INTACT_Props.UserProjectDir)
    UserTiffDir = AbsPath(INTACT_Props.UserTiffDir)

    ################################################################################################

    if not exists(UserProjectDir):

        message = ["The Selected Project Directory Path is not valid ! "]
        ShowMessageBox(message=message, icon="COLORSET_02_VEC")
        return {"CANCELLED"}

    elif not exists(UserTiffDir):

        message = [" The Selected Tiff Directory Path is not valid ! "]
        ShowMessageBox(message=message, icon="COLORSET_02_VEC")
        return {"CANCELLED"}

    elif not os.listdir(UserTiffDir):
        message = ["No valid TIFF Stack found in DICOM Folder ! "]
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
        BlendFile = f"{ProjectName}_CT-SCAN.blend"
        Blendpath = join(UserProjectDir, BlendFile)

        if not exists(Blendpath) or bpy.context.blend_data.filepath == Blendpath:
            bpy.ops.wm.save_as_mainfile(filepath=Blendpath)
        else:
            bpy.ops.wm.save_mainfile()

        # Start Reading Dicom data :
        ######################################################################################


        TiffSerie = sorted(os.listdir(UserTiffDir))
        MaxCount = len(TiffSerie)
        ##################################### debug_02 ###################################
        debug_01 = Tcounter()
        message = f"MaxSerie Count : {MaxCount} (Time : {round(debug_01-start,2)} seconds)"
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

        # Get Info :
        Sp = Spacing = (INTACT_Props.Resolution, INTACT_Props.Resolution, INTACT_Props.Resolution)
        Sz = Size = Image3D.GetSize()

        Dims = Dimensions = Image3D.GetDimension()


        Origin = (-(Sz[0]-1)/2*Sp[0], (Sz[1]-1)/2*Sp[1], (Sz[2]-1)/2*Sp[2])



        Image3D = sitk.Cast(Image3D, sitk.sitkFloat32)
        minmax = sitk.MinimumMaximumImageFilter()
        minmax.Execute(Image3D)
        Wmax = minmax.GetMaximum()
        Wmin = minmax.GetMinimum()



        # calculate Informations :
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

        C = (0.0,0.0,0.0)
        VCenter = C

        TransformMatrix = Matrix(
            (
                (D[0], D[1], D[2], C[0]),
                (D[3], D[4], D[5], C[1]),
                (D[6], D[7], D[8], C[2]),
                (0.0, 0.0, 0.0, 1.0),
            )
        )



        DcmInfo = {
            "UserProjectDir": RelPath(UserProjectDir),
            "Preffix": Preffix,
            "RenderSz": Sz,
            "RenderSp": Sp,
            "PixelType": Image3D.GetPixelIDTypeAsString(),
            "Wmin": Wmin,
            "Wmax": Wmax,
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
        message = f"DcmInfo {Preffix} set (Time : {debug_02-debug_01} seconds)"


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
        # set IntensityWindowing  :
        Image3D_255 = sitk.Cast(
            sitk.IntensityWindowing(
                Image3D,
                windowMinimum=Wmin,
                windowMaximum=Wmax,
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

        # Convert to nrrd file :
        sitk.WriteImage(Image3D_255, Nrrd255Path)

        ################################## debug_03 ######################################
        debug_03 = Tcounter()
        message = f"Nrrd255 Export done!  (Time : {debug_03-debug_02} seconds)"
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


        Array = sitk.GetArrayFromImage(Image3D_255)
        slices = [np.flipud(Array[i, :, :]) for i in range(Array.shape[0])]

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
        DcmInfoDict[Preffix] = DcmInfo
        INTACT_Props.DcmInfo = str(DcmInfoDict)
        INTACT_Props.UserProjectDir = RelPath(INTACT_Props.UserProjectDir)
        bpy.ops.wm.save_mainfile()


        #############################################################################################
        finish = Tcounter()
        message = f"Data Loaded in {finish-start} seconds"
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
    ####### End Load_Tiff_function ##############


#######################################################################################
# INTACT CT Scan 3DImage File Load :


def Load_3DImage_function(context, q):

    INTACT_Props = context.scene.INTACT_Props
    UserProjectDir = AbsPath(INTACT_Props.UserProjectDir)
    UserImageFile = AbsPath(INTACT_Props.UserImageFile)

    #######################################################################################

    if not exists(UserProjectDir):

        message = ["The Selected Project Directory Path is not valid ! "]
        ShowMessageBox(message=message, icon="COLORSET_02_VEC")
        return {"CANCELLED"}

    if not exists(UserImageFile):
        message = [" The Selected Image File Path is not valid ! "]

        ShowMessageBox(message=message, icon="COLORSET_02_VEC")
        return {"CANCELLED"}

    reader = sitk.ImageFileReader()
    IO = reader.GetImageIOFromFileName(UserImageFile)
    FileExt = os.path.splitext(UserImageFile)[1]

    if not IO:
        message = [
            f"{FileExt} files are not Supported! for more info about supported files please refer to Addon wiki "
        ]
        ShowMessageBox(message=message, icon="COLORSET_01_VEC")
        return {"CANCELLED"}

    Image3D = sitk.ReadImage(UserImageFile)
    Depth = Image3D.GetDepth()

    if Depth == 0:
        message = [
            "Can't Build 3D Volume from 2D Image !",
            "for more info about supported files,",
            "please refer to Addon wiki",
        ]
        ShowMessageBox(message=message, icon="COLORSET_01_VEC")
        return {"CANCELLED"}

    ImgFileName = os.path.split(UserImageFile)[1]
    INTACT_nrrd = HU_Image = False
    if ImgFileName.startswith("IT") and ImgFileName.endswith("_Image3D255.nrrd"):
        INTACT_nrrd = True
    if Image3D.GetPixelIDTypeAsString() in [
        "32-bit signed integer",
        "16-bit signed integer",
    ]:
        HU_Image = True

    if not INTACT_nrrd and not HU_Image:
        message = [
            "Only Images with Hunsfield data or INTACT nrrd images are supported !"
        ]
        ShowMessageBox(message=message, icon="COLORSET_01_VEC")
        return {"CANCELLED"}
    ###########################################################################################################

    else:

        start = Tcounter()
        ####################################
        # Get Preffix and save file :
        DcmInfoDict = eval(INTACT_Props.DcmInfo)
        Preffixs = list(DcmInfoDict.keys())

        for i in range(1, 100):
            Preffix = f"IT{i:03}"
            if not Preffix in Preffixs:
                break
        ########################################################
        Split = split(UserProjectDir)
        ProjectName = Split[-1] or Split[-2]
        BlendFile = f"{ProjectName}_CT-SCAN.blend"
        Blendpath = join(UserProjectDir, BlendFile)

        if not exists(Blendpath) or bpy.context.blend_data.filepath == Blendpath:
            bpy.ops.wm.save_as_mainfile(filepath=Blendpath)
        else:
            bpy.ops.wm.save_mainfile()
        Image3D = sitk.ReadImage(UserImageFile)

        # Start Reading Dicom data :
        ######################################################################################
        # Get Dicom Info :
        reader = sitk.ImageFileReader()
        reader.SetFileName(UserImageFile)
        reader.LoadPrivateTagsOn()
        reader.ReadImageInformation()

        Image3D = reader.Execute()

        Sp = Spacing = Image3D.GetSpacing()
        Sz = Size = Image3D.GetSize()
        Dims = Dimensions = Image3D.GetDimension()
        Origin = Image3D.GetOrigin()
        Direction = Image3D.GetDirection()

        #Set Wmin and Wmax
        minmax = sitk.MinimumMaximumImageFilter()
        minmax.Execute(Image3D)
        Wmax = minmax.GetMaximum()
        Wmin = minmax.GetMinimum()
        INTACT_Props.Wmin = Wmin
        INTACT_Props.Wmax = Wmax

        # calculate Informations :
        D = Direction
        O = Origin
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

        C = VCenter

        TransformMatrix = Matrix(
            (
                (D[0], D[1], D[2], C[0]),
                (D[3], D[4], D[5], C[1]),
                (D[6], D[7], D[8], C[2]),
                (0.0, 0.0, 0.0, 1.0),
            )
        )

        # Set DcmInfo :

        DcmInfo = {
            "UserProjectDir": RelPath(UserProjectDir),
            "Preffix": Preffix,
            "RenderSz": Sz,
            "RenderSp": Sp,
            "PixelType": Image3D.GetPixelIDTypeAsString(),
            "Wmin": Wmin,
            "Wmax": Wmax,
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
        tags = {
            "StudyDate": "0008|0020",
            "PatientName": "0010|0010",
            "PatientID": "0010|0020",
            "BirthDate": "0010|0030",
            "WinCenter": "0028|1050",
            "WinWidth": "0028|1051",
        }

        for k, tag in tags.items():

            if tag in reader.GetMetaDataKeys():
                v = reader.GetMetaData(tag)

            else:
                v = ""

            DcmInfo[k] = v
            Image3D.SetMetaData(tag, v)

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
        print(Wmin,Wmax)

        if INTACT_nrrd:
            Image3D_255 = Image3D
            print('Not rescaled')

        else:
            #######################################################################################
            # set IntensityWindowing  :
            Image3D_255 = sitk.Cast(
                sitk.IntensityWindowing(
                    Image3D,
                    windowMinimum=Wmin,
                    windowMaximum=Wmax,
                    outputMinimum=0.0,
                    outputMaximum=255.0,
                ),
                sitk.sitkUInt8,
            )

        # Convert Dicom to nrrd file :
        # sitk.WriteImage(Image3D, NrrdHuPath)
        sitk.WriteImage(Image3D_255, Nrrd255Path)



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
            # print(f"{img_Name} was processed...")

        #########################################################################################
        # Get slices list :
        MaxSp = max(Vector(Sp))
        if MaxSp < 0.25:
            SampleRatio = round(MaxSp / 0.25, 2)
            Image3D_255 = ResizeImage(sitkImage=Image3D_255, Ratio=SampleRatio)
            DcmInfo["RenderSz"] = Image3D_255.GetSize()
            DcmInfo["RenderSp"] = Image3D_255.GetSpacing()

        Array = sitk.GetArrayFromImage(Image3D_255)
        slices = [np.flipud(Array[i, :, :]) for i in range(Array.shape[0])]
        # slices = [Image3D_255[:, :, i] for i in range(Image3D_255.GetDepth())]

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
        DcmInfoDict[Preffix] = DcmInfo
        INTACT_Props.DcmInfo = str(DcmInfoDict)
        INTACT_Props.UserProjectDir = RelPath(INTACT_Props.UserProjectDir)
        bpy.ops.wm.save_mainfile()

        #############################################################################################
        finish = Tcounter()
        print(f"Data Loaded in {finish-start} second(s)")
        #############################################################################################
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
            DcmInfo = Load_Tiff_function(context, self.q)
        if DataType == "DICOM Series":
            DcmInfo = Load_Dicom_funtion(context, self.q)
        if DataType == "NRRD File":
            DcmInfo = Load_3DImage_function(context, self.q)

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
        Low_Treshold.default_value = 100
        WminNode = GpNode.nodes["WminNode"].outputs[0]
        WminNode.default_value = Wmin
        WmaxNode = GpNode.nodes["WmaxNode"].outputs[0]
        WmaxNode.default_value = Wmax

        INTACT_Props.CT_Rendered = True
        bpy.context.scene.unit_settings.scale_length = 0.001
        bpy.context.scene.unit_settings.length_unit = "MILLIMETERS"
        bpy.ops.view3d.view_selected(use_all_regions=False)
        bpy.ops.wm.save_mainfile()

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

