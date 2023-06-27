import bpy
import numpy as np
import math as mt
import mathutils as mu
import copy
import os
import blf
from bpy_extras import view3d_utils

from .INTACT_Utils import *

def placeSeed(context, event):
    #define selected objects
    selectedObjects = bpy.context.selected_objects

    #define boundary conditions
    scene = context.scene
    region = context.region
    rv3d = context.region_data
    mouseCoordinates = event.mouse_region_x, event.mouse_region_y

    #convert cursor location and view direction
    viewVector = view3d_utils.region_2d_to_vector_3d(region, rv3d, mouseCoordinates)
    rayOrigin = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouseCoordinates)
    rayTarget = rayOrigin + viewVector

    #ray cast procedure for selected objects
    successArray = []
    hitLocationArray = []
    distanceArray = []

    for object in selectedObjects:
        #convert to object space
        matrixInverted = object.matrix_world.inverted()
        rayOriginObject = matrixInverted @ rayOrigin
        rayTargetObject = matrixInverted @ rayTarget
        rayVectorObject = rayTargetObject - rayOriginObject

        #raycast procedure
        success, hitLocation, _, _ = object.ray_cast(rayOriginObject, rayVectorObject)

        #store success, location and distance
        successArray.append(success)
        hitLocationArray.append(hitLocation)
        distanceArray.append(np.linalg.norm(hitLocation - rayOriginObject))

    #if raycast successful on both objects, take the one closest to viewer
    if np.all(successArray):
        object = selectedObjects[np.argmin(distanceArray)]
        hitLocation = hitLocationArray[np.argmin(distanceArray)]
    #return nothing if no raycast hit
    elif not np.any(successArray):
        return None, None
    #in both other scenarios, only one object was hit
    else:
        object = selectedObjects[np.squeeze(np.where(successArray))]
        hitLocation = hitLocationArray[np.squeeze(np.where(successArray))]

    #build kd tree to get closest vertex
    tree = []
    tree = mu.kdtree.KDTree(len(object.data.vertices))
    for i, v in enumerate(object.data.vertices):
        tree.insert(v.co, i)
    tree.balance()

    _, seedIndex, _ = tree.find(hitLocation)
    return object, seedIndex


class OBJECT_OT_ICP_operator(bpy.types.Operator):
    """Start iterative closest point registration (first selected object = moving, last selected object = fixed)"""
    bl_idname = "object.icp"
    bl_label = "Perform Registration"
    bl_options = {'REGISTER', 'UNDO'}



    @classmethod
    def poll(cls, context):
        INTACT_Props = context.scene.INTACT_Props
        ct_seg = INTACT_Props.Seg
        surf_3d = INTACT_Props.Surf_3D
        ct_seg.select_set(True)
        surf_3d.select_set(True)
        condition = (ct_seg.type == 'MESH' and surf_3d.type == 'MESH')
        ct_seg.select_set(False)
        surf_3d.select_set(False)
        return condition

    def execute(self, context):
        INTACT_Props = context.scene.INTACT_Props
        ct_seg = INTACT_Props.Seg
        surf_3d = INTACT_Props.Surf_3D
        ct_seg.select_set(True)
        surf_3d.select_set(True)

        #assign fixed object
        fixedObject = ct_seg

        #vertex selections
        if bpy.context.scene.vertexSelect:
            fixedVerts = [fixedObject.matrix_world @ v.co for v in fixedObject.data.vertices if v.select]
        else:
            fixedVerts = [fixedObject.matrix_world @ v.co for v in fixedObject.data.vertices]

        #downsampling
        fixedDownsampleNumber = mt.ceil(((100 - bpy.context.scene.downsamplingPerc) / 100) * len(fixedVerts))
        fixedDownsampleIndices = np.random.choice(range(len(fixedVerts)), fixedDownsampleNumber, replace = False)
        fixedVerts = [fixedVerts[idx] for idx in fixedDownsampleIndices]

        #build kdtree
        fixedVertsTree = mu.kdtree.KDTree(len(fixedVerts))
        for fixedIndex, fixedVertex in enumerate(fixedVerts):
            fixedVertsTree.insert(fixedVertex, fixedIndex)
        fixedVertsTree.balance()

        #assign moving object
        movingObject = surf_3d


        #vertex selections
        if bpy.context.scene.vertexSelect:
            movingVertsCount = len([v for v in movingObject.data.vertices if v.select])
        else:
            movingVertsCount = len(movingObject.data.vertices)

        #error message if no vertices are selected
        if len(fixedVerts) == 0 or movingVertsCount == 0:
            self.report({'ERROR'}, 'No vertices selected on one or both objects. Disable "Use Vertex Selections" or make a vertex selection in Edit Mode.')
            return {'FINISHED'}

        #downsampling
        movingDownsampleNumber = mt.ceil(((100 - bpy.context.scene.downsamplingPerc) / 100) * movingVertsCount)
        movingDownsampleIndices = np.random.choice(range(movingVertsCount), movingDownsampleNumber, replace = False)

        #copy T0 transformations
        transformationFineT0 = copy.deepcopy(movingObject.matrix_world)

        #icp loop
        for iteration in range(bpy.context.scene.iterations):
            #vertex selections
            if bpy.context.scene.vertexSelect:
                movingVerts = [movingObject.matrix_world @ v.co for v in movingObject.data.vertices if v.select]
            else:
                movingVerts = [movingObject.matrix_world @ v.co for v in movingObject.data.vertices]

            #downsampling
            movingVerts = [movingVerts[idx] for idx in movingDownsampleIndices]

            #nearest neighbor search
            fixedPairIndices = []
            movingPairIndices = range(len(movingVerts))
            pairDistances = []
            for vertex in range(len(movingVerts)):
                _, minIndex, minDist = fixedVertsTree.find(movingVerts[vertex])
                fixedPairIndices.append(minIndex)
                pairDistances.append(minDist)

            #select inliers
            pairDistancesSorted = np.argsort(pairDistances)
            pairInliers = pairDistancesSorted[range(mt.ceil((100 - bpy.context.scene.outlierPerc) / 100 * len(pairDistancesSorted)))]
            fixedPairIndices = [fixedPairIndices[idx] for idx in pairInliers]
            movingPairIndices = [movingPairIndices[idx] for idx in pairInliers]
            fixedPairVerts = [fixedVerts[idx] for idx in fixedPairIndices]
            movingPairVerts = [movingVerts[idx] for idx in movingPairIndices]

            #calculate centroids
            fixedCentroid = np.mean(fixedPairVerts, axis = 0)
            movingCentroid = np.mean(movingPairVerts, axis = 0)

            #normalize vertices
            fixedVertsNorm = fixedPairVerts - fixedCentroid
            movingVertsNorm = movingPairVerts - movingCentroid

            #singular value decomposition
            covMatrix = np.matrix.transpose(movingVertsNorm) @ fixedVertsNorm
            try:
                U, _, Vt = np.linalg.svd(covMatrix)
            except:
                self.report({'ERROR'}, 'Singular value decomposition did not converge. Disable "Allow Scaling" or ensure a better initial alignment.')
                movingObject.matrix_world = transformationFineT0
                return {'FINISHED'}

            #scaling
            if bpy.context.scene.allowScaling:
                scalingMatrix = np.eye(4)
                scalingFactor = mt.sqrt(np.sum(fixedVertsNorm ** 2) / np.sum(movingVertsNorm ** 2))
                for i in range(3):
                    scalingMatrix[i,i] *= scalingFactor
                normMatrix = np.eye(4)
                normMatrix[0:3,3] = -np.matrix.transpose(movingCentroid)
                movingObject.matrix_world = mu.Matrix(normMatrix) @ movingObject.matrix_world
                movingObject.matrix_world = mu.Matrix(scalingMatrix) @ movingObject.matrix_world
                normMatrix[0:3,3] = -normMatrix[0:3,3]
                movingObject.matrix_world = mu.Matrix(normMatrix) @ movingObject.matrix_world

            #rotation
            rotation3x3 = np.matrix.transpose(Vt) @ np.matrix.transpose(U)
            rotationMatrix = np.eye(4)
            rotationMatrix[0:3,0:3] = rotation3x3
            movingObject.matrix_world = mu.Matrix(rotationMatrix) @ movingObject.matrix_world

            #translation
            translationMatrix = np.eye(4)
            translationMatrix[0:3,3] = np.matrix.transpose(fixedCentroid - rotation3x3 @ movingCentroid)
            movingObject.matrix_world = mu.Matrix(translationMatrix) @ movingObject.matrix_world

            #redraw scene
            bpy.ops.wm.redraw_timer(type = 'DRAW_WIN_SWAP', iterations = 1)

        #copy T1 transformations
        transformationFineT1 = copy.deepcopy(movingObject.matrix_world)

        #compute transformation matrix
        globalVars.transformationFine = transformationFineT1 @ transformationFineT0.inverted_safe()
        ct_seg.select_set(False)
        surf_3d.select_set(False)
        return {'FINISHED'}


###############################################################################
####################### INTACT_FULL VOLUME to Mesh : ################################
##############################################################################
class INTACT_OT_MultiTreshSegment(bpy.types.Operator):
    """ Add a mesh Segmentation using Treshold """

    bl_idname = "intact.multitresh_segment"
    bl_label = "SEGMENTATION"

    TimingDict = {}

    def ImportMeshStl(self, Segment, SegmentStlPath, SegmentColor):

        # import stl to blender scene :
        bpy.ops.import_mesh.stl(filepath=SegmentStlPath)
        obj = bpy.context.object
        obj.name = f"{self.Preffix}_{Segment}_SEGMENTATION"
        obj.data.name = f"{self.Preffix}_{Segment}_mesh"

        bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="MEDIAN")

        self.step7 = Tcounter()
        self.TimingDict["Mesh Import"] = self.step7 - self.step6

        ############### step 8 : Add material... #########################
        mat = bpy.data.materials.get(obj.name) or bpy.data.materials.new(obj.name)
        mat.diffuse_color = SegmentColor
        obj.data.materials.append(mat)
        MoveToCollection(obj=obj, CollName="SEGMENTS")
        bpy.ops.object.shade_smooth()

        bpy.ops.object.modifier_add(type="CORRECTIVE_SMOOTH")
        bpy.context.object.modifiers["CorrectiveSmooth"].iterations = 2
        bpy.context.object.modifiers["CorrectiveSmooth"].use_only_smooth = True
        bpy.ops.object.modifier_apply(modifier="CorrectiveSmooth")

        self.step8 = Tcounter()
        self.TimingDict["Add material"] = self.step8 - self.step7
        print(f"{Segment} Mesh Import Finished")

        return obj

        # self.q.put(["End"])

    def DicomToStl(self, Segment, Image3D):
        print(f"{Segment} processing ...")
        # Load Infos :
        #########################################################################
        INTACT_Props = bpy.context.scene.INTACT_Props
        UserProjectDir = AbsPath(INTACT_Props.UserProjectDir)
        DcmInfo = self.DcmInfo
        Origin = DcmInfo["Origin"]
        VtkTransform_4x4 = DcmInfo["VtkTransform_4x4"]
        TransformMatrix = DcmInfo["TransformMatrix"]
        VtkMatrix_4x4 = (
            self.Vol.matrix_world @ TransformMatrix.inverted() @ VtkTransform_4x4
        )

        VtkMatrix = list(np.array(VtkMatrix_4x4).ravel())
        print(self.DcmInfo)
        SmoothIterations = SmthIter = 5
        Thikness = 1

        SegmentThreshold = self.SegmentsDict[Segment]["Threshold"]
        SegmentColor = self.SegmentsDict[Segment]["Color"]
        SegmentStlPath = join(UserProjectDir, f"{Segment}_SEGMENTATION.stl")

        # Convert Hu treshold value to 0-255 UINT8 :
        #Treshold255 = HuTo255(Hu=SegmentTreshold, Wmin=DcmInfo["Wmin"], Wmax=DcmInfo["Wmax"])

        Treshold255 = SegmentThreshold
        if Treshold255 == 0:
            Treshold255 = 1
        elif Treshold255 == 255:
            Treshold255 = 254
        print(Treshold255)

        ############### step 2 : Extracting mesh... #########################
        # print("Extracting mesh...")
        vtkImage = sitkTovtk(sitkImage=Image3D)

        ExtractedMesh = vtk_MC_Func(vtkImage=vtkImage, Treshold=Treshold255)
        Mesh = ExtractedMesh

        polysCount = Mesh.GetNumberOfPolys()
        polysLimit = 800000

        self.step2 = Tcounter()
        self.TimingDict["Mesh Extraction Time"] = self.step2 - self.step1
        print(f"{Segment} Mesh Extraction Finished")
        ############### step 3 : mesh Reduction... #########################
        if polysCount > polysLimit:

            Reduction = round(1 - (polysLimit / polysCount), 2)
            ReductedMesh = vtkMeshReduction(
                q=self.q,
                mesh=Mesh,
                reduction=Reduction,
                step="Mesh Reduction",
                start=0.11,
                finish=0.75,
            )
            Mesh = ReductedMesh

        self.step3 = Tcounter()
        self.TimingDict["Mesh Reduction Time"] = self.step3 - self.step2
        print(f"{Segment} Mesh Reduction Finished")
        ############### step 4 : mesh Smoothing... #########################
        SmoothedMesh = vtkSmoothMesh(
            q=self.q,
            mesh=Mesh,
            Iterations=SmthIter,
            step="Mesh Smoothing",
            start=0.76,
            finish=0.78,
        )

        self.step4 = Tcounter()
        self.TimingDict["Mesh Smoothing Time"] = self.step4 - self.step3
        print(f"{Segment} Mesh Smoothing Finished")
        ############### step 5 : Set mesh orientation... #########################
        TransformedMesh = vtkTransformMesh(
            mesh=SmoothedMesh,
            Matrix=VtkMatrix,
        )
        print(VtkMatrix)
        self.step5 = Tcounter()
        self.TimingDict["Mesh Orientation"] = self.step5 - self.step4
        print(f"{Segment} Mesh Orientation Finished")
        ############### step 6 : exporting mesh stl... #########################
        writer = vtk.vtkSTLWriter()
        writer.SetInputData(TransformedMesh)
        writer.SetFileTypeToBinary()
        writer.SetFileName(SegmentStlPath)
        writer.Write()

        self.step6 = Tcounter()
        self.TimingDict["Mesh Export"] = self.step6 - self.step5
        print(f"{Segment} Mesh Export Finished")
        self.Exported.put([Segment, SegmentStlPath, SegmentColor])

    def execute(self, context):

        self.counter_start = Tcounter()

        INTACT_Props = bpy.context.scene.INTACT_Props

        Active_Obj = INTACT_Props.CT_Vol

        if not Active_Obj:
            message = [" Please select CT VOLUME for segmentation! "]
            ShowMessageBox(message=message, icon="COLORSET_02_VEC")
            return {"CANCELLED"}
        else:
            if Active_Obj:

                self.Thres1 = INTACT_Props.Thres1Bool

                self.Threshold = INTACT_Props.Threshold

                self.Thres1SegmentColor = INTACT_Props.Thres1SegmentColor


                self.SegmentsDict = {
                    "Thres1": {
                        "State": self.Thres1,
                        "Threshold": self.Threshold,
                        "Color": self.Thres1SegmentColor,
                    },
                }

                ActiveSegmentsList = [
                    k for k, v in self.SegmentsDict.items() if v["State"]
                ]
                if Active_Obj:

                    self.Vol = Active_Obj
                    self.Preffix = self.Vol.name[:5]
                    DcmInfoDict = eval(INTACT_Props.DcmInfo)
                    self.DcmInfo = DcmInfoDict[self.Preffix]
                    self.Nrrd255Path = AbsPath(self.DcmInfo["Nrrd255Path"])
                    self.q = Queue()
                    self.Exported = Queue()

                    if not exists(self.Nrrd255Path):

                        message = [" Image File not Found in Project Folder ! "]
                        ShowMessageBox(message=message, icon="COLORSET_01_VEC")
                        return {"CANCELLED"}

                    else:

                        ############### step 1 : Reading DICOM #########################
                        self.step1 = Tcounter()
                        self.TimingDict["Read DICOM"] = self.step1 - self.counter_start
                        print(f"step 1 : Read DICOM ({self.step1-self.counter_start})")

                        Image3D = sitk.ReadImage(self.Nrrd255Path)
                        minmax = sitk.MinimumMaximumImageFilter()
                        minmax.Execute(Image3D)
                        Imax = minmax.GetMaximum()
                        Imin = minmax.GetMinimum()
                        print(Imin, Imax)


                        Sp = self.DcmInfo["Spacing"]
                        print('Resolution', Sp)
                        MaxSp = max(Vector(Sp))
                        if MaxSp < 0.3:
                            SampleRatio = round(MaxSp / 0.3, 2)
                            ResizedImage = ResizeImage(
                                sitkImage=Image3D, Ratio=SampleRatio
                            )
                            Image3D = ResizedImage
                            print(f"Image DOWN Sampled : SampleRatio = {SampleRatio}")

                        ############### step 2 : Dicom To Stl Threads #########################

                        self.MeshesCount = len(ActiveSegmentsList)
                        Imported_Meshes = []
                        Threads = [
                            threading.Thread(
                                target=self.DicomToStl,
                                args=[Segment, Image3D],
                                daemon=True,
                            )
                            for Segment in ActiveSegmentsList
                        ]
                        for t in Threads:
                            t.start()
                        count = 0
                        while count < self.MeshesCount:
                            if not self.Exported.empty():
                                (
                                    Segment,
                                    SegmentStlPath,
                                    SegmentColor,
                                ) = self.Exported.get()
                                obj = self.ImportMeshStl(
                                    Segment, SegmentStlPath, SegmentColor
                                )
                                Imported_Meshes.append(obj)
                                count += 1
                            else:
                                sleep(0.1)
                        for t in Threads:
                            t.join()

                        for obj in Imported_Meshes:
                            bpy.ops.object.select_all(action="DESELECT")
                            obj.select_set(True)
                            bpy.context.view_layer.objects.active = obj
                            for i in range(3):
                                obj.lock_location[i] = True
                                obj.lock_rotation[i] = True
                                obj.lock_scale[i] = True

                        bpy.ops.object.select_all(action="DESELECT")
                        for obj in Imported_Meshes:
                            obj.select_set(True)
                        self.Vol.select_set(True)
                        bpy.context.view_layer.objects.active = self.Vol
                        bpy.ops.object.parent_set(type="OBJECT", keep_transform=True)
                        bpy.ops.object.select_all(action="DESELECT")

                        self.counter_finish = Tcounter()
                        self.TimingDict["Total Time"] = (
                            self.counter_finish - self.counter_start
                        )

                        for obj in bpy.context.scene.objects:
                            if obj.name.endswith("_SEGMENTATION"):
                                INTACT_Props.Seg = obj

                        print(self.TimingDict)

                        return {"FINISHED"}





class INTACT_OT_ResetCtVolumePosition(bpy.types.Operator):
    """ Reset the CtVolume to its original position """

    bl_idname = "intact.reset_ctvolume_position"
    bl_label = "RESET CTVolume POSITION"

    def execute(self, context):
        INTACT_Props = bpy.context.scene.INTACT_Props
        ct_vol = INTACT_Props.CT_Vol
        Preffix = ct_vol.name[:5]
        DcmInfoDict = eval(INTACT_Props.DcmInfo)
        DcmInfo = DcmInfoDict[Preffix]
        TransformMatrix = DcmInfo["TransformMatrix"]
        ct_vol.matrix_world = TransformMatrix

        return {"FINISHED"}


class INTACT_OT_CTVolumeOrientation(bpy.types.Operator):
    """ CtVolume Orientation according to Frankfort Plane """

    bl_idname = "intact.ctvolume_orientation"
    bl_label = "CTVolume Orientation"

    def execute(self, context):

        INTACT_Props = bpy.context.scene.INTACT_Props
        ct_vol = INTACT_Props.CT_Vol
        Active_Obj = ct_vol
        Preffix = Active_Obj.name[:5]
        DcmInfo = eval(INTACT_Props.DcmInfo)
        if not "Frankfort" in DcmInfo[Preffix].keys():
            message = ["CTVOLUME Orientation : ",
                        "Please Add Reference Planes before CTVOLUME Orientation ! ",]
            ShowMessageBox(message=message, icon="COLORSET_02_VEC")
            return {"CANCELLED"}
        else:
            Frankfort_Plane = bpy.data.objects.get(
                  DcmInfo[Preffix]["Frankfort"])

            if not Frankfort_Plane:
                 message = [
                            "CTVOLUME Orientation : ",
                            "Frankfort Reference Plane has been removed",
                            "Please Add Reference Planes before CTVOLUME Orientation ! ",
                        ]
                 ShowMessageBox(message=message, icon="COLORSET_02_VEC")
                 return {"CANCELLED"}
            else:
                 Active_Obj.matrix_world = (
                      Frankfort_Plane.matrix_world.inverted()
                      @ Active_Obj.matrix_world)
                 bpy.ops.view3d.view_center_cursor()
                 return {"FINISHED"}




class globalVars():
    pass



classes = (
    OBJECT_OT_ICP_operator,
    INTACT_OT_ResetCtVolumePosition,
    INTACT_OT_MultiTreshSegment,
    INTACT_OT_CTVolumeOrientation)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    #icp panel
    bpy.types.Scene.allowScaling = bpy.props.BoolProperty(
        default = False,
        description = "Allow uniform scaling of the moving object")
    bpy.types.Scene.vertexSelect = bpy.props.BoolProperty(
        default = False,
        description = "Use only selected vertices for registration")
    bpy.types.Scene.iterations = bpy.props.IntProperty(
        default = 50, min = 1,
        description = "Number of iterations")
    bpy.types.Scene.outlierPerc = bpy.props.IntProperty(
        default = 20, min = 0, max = 99,
        description = "Outlier percentage")
    bpy.types.Scene.downsamplingPerc = bpy.props.IntProperty(
        default = 0, min = 0, max = 99,
        description = "Downsampling percentage")



def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()