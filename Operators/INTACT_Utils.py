# Python imports :
import os, sys, shutil, threading
from os.path import join, dirname, exists, abspath

from math import degrees, radians, pi
import numpy as np
from time import sleep, perf_counter as Tcounter
from queue import Queue
from importlib import reload
from bpy.app.handlers import persistent

# Blender Imports :
import bpy
import bmesh
import mathutils
from mathutils import Matrix, Vector, Euler, kdtree, geometry as Geo

import SimpleITK as sitk
import vtk
import cv2

try:
    cv2 = reload(cv2)
except ImportError:
    pass
from vtk.util import numpy_support
from vtk import vtkCommand

# Global Variables :

ProgEvent = vtkCommand.ProgressEvent

#######################################################################################
# Popup message box function :
#######################################################################################


def ShowMessageBox(message=[], title="INFO", icon="INFO"):
    def draw(self, context):
        for txtLine in message:
            self.layout.label(text=txtLine)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


#######################################################################################
# Load CT Scan functions :
#######################################################################################
def get_all_addons(display=False):
    """
    Prints the addon state based on the user preferences.

    """
    import bpy as _bpy
    from addon_utils import check, paths, enable
    import sys

    # RELEASE SCRIPTS: official scripts distributed in Blender releases
    paths_list = paths()
    addon_list = []
    for path in paths_list:
        _bpy.utils._sys_path_ensure(path)
        for mod_name, mod_path in _bpy.path.module_names(path):
            is_enabled, is_loaded = check(mod_name)
            addon_list.append(mod_name)
            if display:  # for example
                print("%s default:%s loaded:%s" % (mod_name, is_enabled, is_loaded))

    return addon_list


def Addon_Enable(AddonName, Enable=True):
    import addon_utils as AU

    is_enabled, is_loaded = AU.check(AddonName)
    if Enable:
        if not is_enabled:
            AU.enable(AddonName, default_set=True)
    if not Enable:
        if is_enabled:
            AU.disable(AddonName, default_set=True)

    is_enabled, is_loaded = AU.check(AddonName)


def CleanScanData(Preffix):
    D = bpy.data
    Objects = D.objects
    Meshes = D.meshes
    Images = D.images
    Materials = D.materials
    NodeGroups = D.node_groups

    # Remove Voxel data :
    [Meshes.remove(m) for m in Meshes if f"{Preffix}_PLANE_" in m.name]
    [Images.remove(img) for img in Images if f"{Preffix}_img" in img.name]
    [Materials.remove(mat) for mat in Materials if "IT001_Voxelmat_" in mat.name]
    [NodeGroups.remove(NG) for NG in NodeGroups if "IT001_VGS_" in NG.name]

    # Remove old Slices :
    SlicePlanes = [
        Objects.remove(obj)
        for obj in Objects
        if Preffix in obj.name and "SLICE" in obj.name
    ]
    SliceMeshes = [
        Meshes.remove(m) for m in Meshes if Preffix in m.name and "SLICE" in m.name
    ]
    SliceMats = [
        Materials.remove(mat)
        for mat in Materials
        if Preffix in mat.name and "SLICE" in mat.name
    ]
    SliceImages = [
        Images.remove(img)
        for img in Images
        if Preffix in img.name and "SLICE" in img.name
    ]


def CtxOverride(context):
    Override = context.copy()
    area3D = [area for area in context.screen.areas if area.type == "VIEW_3D"][0]
    space3D = [space for space in area3D.spaces if space.type == "VIEW_3D"][0]
    region3D = [reg for reg in area3D.regions if reg.type == "WINDOW"][0]
    Override["area"], Override["space_data"], Override["region"] = (
        area3D,
        space3D,
        region3D,
    )
    return Override, area3D, space3D


def AbsPath(P):
    # if P.startswith('//') :
    P = abspath(bpy.path.abspath(P))
    return P


def RelPath(P):
    if not P.startswith("//"):
        P = bpy.path.relpath(abspath(P))
    return P


############################
# Make directory function :
############################
def make_directory(Root, DirName):

    DirPath = join(Root, DirName)
    if not DirName in os.listdir(Root):
        os.mkdir(DirPath)
    return DirPath


################################
# Copy DcmSerie To ProjDir function :
################################
def CopyDcmSerieToProjDir(DcmSerie, DicomSeqDir):
    for i in range(len(DcmSerie)):
        shutil.copy2(DcmSerie[i], DicomSeqDir)


##########################################################################################
######################### INTACT Volume Render : ########################################
##########################################################################################


def PlaneCut(Target, Plane, inner=False, outer=False, fill=False):

    bpy.ops.object.select_all(action="DESELECT")
    Target.select_set(True)
    bpy.context.view_layer.objects.active = Target

    Pco = Plane.matrix_world.translation
    Pno = Plane.matrix_world.to_3x3().transposed()[2]

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.bisect(
        plane_co=Pco,
        plane_no=Pno,
        use_fill=fill,
        clear_inner=inner,
        clear_outer=outer,
    )
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")


def AddBooleanCube(DimX, DimY, DimZ):
    bpy.ops.mesh.primitive_cube_add(
        size=max(DimX, DimY, DimZ) * 1.5,
        enter_editmode=False,
        align="WORLD",
        location=(0, 0, 0),
        scale=(1, 1, 1),
    )

    VOI = VolumeOfInterst = bpy.context.object
    VOI.name = "VOI"
    VOI.display_type = "WIRE"
    return VOI


def AddNode(nodes, type, name):

    node = nodes.new(type)
    node.name = name
    # node.location[0] -= 200

    return node


def AddFrankfortPoint(PointsList, color, CollName):
    FrankfortPointsNames = ["R_Or", "L_Or", "R_Po", "L_Po"]
    if not PointsList:
        P = AddMarkupPoint(FrankfortPointsNames[0], color, CollName)
        return P
    if PointsList:
        CurrentPointsNames = [P.name for P in PointsList]
        P_Names = [P for P in FrankfortPointsNames if not P in CurrentPointsNames]
        if P_Names:
            P = AddMarkupPoint(P_Names[0], color, CollName)
            return P
    else:
        return None


def AddMarkupPoint(name, color, loc, CollName=None):

    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.2, location=loc)
    P = bpy.context.object
    P.name = name
    P.data.name = name + "_mesh"

    if CollName:
        MoveToCollection(P, CollName)

    matName = f"{name}_Mat"
    mat = bpy.data.materials.get(matName) or bpy.data.materials.new(matName)
    mat.diffuse_color = color
    mat.use_nodes = False
    P.active_material = mat
    P.show_name = True
    return P


def ProjectPoint(Plane, Point):

    V1, V2, V3, V4 = [Plane.matrix_world @ V.co for V in Plane.data.vertices]
    Ray = Plane.matrix_world.to_3x3() @ Plane.data.polygons[0].normal

    Orig = Point
    Result = Geo.intersect_ray_tri(V1, V2, V3, Ray, Orig, False)
    if not Result:
        Ray *= -1
        Result = Geo.intersect_ray_tri(V1, V2, V3, Ray, Orig, False)
    return Result


def PointsToFrankfortPlane(ctx, Model, CurrentPointsList, color, CollName=None):

    Dim = max(Model.dimensions) * 1.5
    Na, R_Or, L_Or, R_Po, L_Po = [P.location for P in CurrentPointsList]

    Center = (R_Or + L_Or + R_Po + L_Po) / 4

    FrankZ = (R_Or - Center).cross((L_Or - Center)).normalized()
    FrankX = (Center - Na).cross(FrankZ).normalized()
    FrankY = FrankZ.cross(FrankX).normalized()

    FrankMtx = Matrix((FrankX, FrankY, FrankZ)).to_4x4().transposed()
    FrankMtx.translation = Center

    SagZ = -FrankX
    SagX = FrankZ
    SagY = FrankY

    SagMtx = Matrix((SagX, SagY, SagZ)).to_4x4().transposed()
    SagMtx.translation = Center

    CorZ = -FrankY
    CorX = FrankX
    CorY = FrankZ

    CorMtx = Matrix((CorX, CorY, CorZ)).to_4x4().transposed()
    CorMtx.translation = Center

    bpy.ops.mesh.primitive_plane_add(ctx, size=Dim)
    FrankfortPlane = bpy.context.object
    name = "Frankfort_Plane"
    FrankfortPlane.name = name
    FrankfortPlane.data.name = f"{name}_Mesh"
    FrankfortPlane.matrix_world = FrankMtx
    matName = f"RefPlane_Mat"
    mat = bpy.data.materials.get(matName) or bpy.data.materials.new(matName)
    mat.diffuse_color = color
    mat.use_nodes = False
    FrankfortPlane.active_material = mat

    if CollName:
        MoveToCollection(FrankfortPlane, CollName)
    # Add Sagital Plane :
    bpy.ops.object.duplicate_move()
    SagPlane = bpy.context.object
    name = "Sagital_Median_Plane"
    SagPlane.name = name
    SagPlane.data.name = f"{name}_Mesh"
    SagPlane.matrix_world = SagMtx
    if CollName:
        MoveToCollection(SagPlane, CollName)

    # Add Coronal Plane :
    bpy.ops.object.duplicate_move()
    CorPlane = bpy.context.object
    name = "Coronal_Plane"
    CorPlane.name = name
    CorPlane.data.name = f"{name}_Mesh"
    CorPlane.matrix_world = CorMtx
    if CollName:
        MoveToCollection(CorPlane, CollName)

    # Project Na to Coronal Plane :
    Na_Projection_1 = ProjectPoint(Plane=CorPlane, Point=Na)

    # Project Na_Projection_1 to frankfort Plane :
    Na_Projection_2 = ProjectPoint(Plane=FrankfortPlane, Point=Na_Projection_1)

    for Plane in (FrankfortPlane, CorPlane, SagPlane):
        Plane.location = Na_Projection_2
    return [FrankfortPlane, SagPlane, CorPlane]


def PointsToOcclusalPlane(ctx, Model, R_pt, A_pt, L_pt, color, subdiv):

    Dim = max(Model.dimensions) * 1.2

    Rco = R_pt.location
    Aco = A_pt.location
    Lco = L_pt.location

    Center = (Rco + Aco + Lco) / 3

    Z = (Rco - Center).cross((Aco - Center)).normalized()
    X = Z.cross((Aco - Center)).normalized()
    Y = Z.cross(X).normalized()

    Mtx = Matrix((X, Y, Z)).to_4x4().transposed()
    Mtx.translation = Center

    bpy.ops.mesh.primitive_plane_add(ctx, size=Dim)
    OcclusalPlane = bpy.context.object
    name = "Occlusal_Plane"
    OcclusalPlane.name = name
    OcclusalPlane.data.name = f"{name}_Mesh"
    OcclusalPlane.matrix_world = Mtx

    matName = f"{name}_Mat"
    mat = bpy.data.materials.get(matName) or bpy.data.materials.new(matName)
    mat.diffuse_color = color
    mat.use_nodes = False
    OcclusalPlane.active_material = mat
    if subdiv:
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.subdivide(number_cuts=50)
        bpy.ops.object.mode_set(mode="OBJECT")

    return OcclusalPlane


##############################################
def TriPlanes_Point_Intersect(P1, P2, P3, CrossLenght):

    P1N = P1.matrix_world.to_3x3() @ P1.data.polygons[0].normal
    P2N = P2.matrix_world.to_3x3() @ P2.data.polygons[0].normal
    P3N = P3.matrix_world.to_3x3() @ P3.data.polygons[0].normal

    Condition = np.dot(np.array(P1N), np.cross(np.array(P2N), np.array(P3N))) != 0

    C1, C2, C3 = P1.location, P2.location, P3.location

    F1 = sum(list(P1.location * P1N))
    F2 = sum(list(P2.location * P2N))
    F3 = sum(list(P3.location * P3N))

    # print(Matrix((P1N,P2N,P3N)))
    if Condition:

        P_Intersect = Matrix((P1N, P2N, P3N)).inverted() @ Vector((F1, F2, F3))
        P1P2_Vec = (
            Vector(np.cross(np.array(P1N), np.array(P2N))).normalized() * CrossLenght
        )
        P2P3_Vec = (
            Vector(np.cross(np.array(P2N), np.array(P3N))).normalized() * CrossLenght
        )
        P1P3_Vec = (
            Vector(np.cross(np.array(P1N), np.array(P3N))).normalized() * CrossLenght
        )

        P1P2 = [P_Intersect + P1P2_Vec, P_Intersect - P1P2_Vec]
        P2P3 = [P_Intersect + P2P3_Vec, P_Intersect - P2P3_Vec]
        P1P3 = [P_Intersect + P1P3_Vec, P_Intersect - P1P3_Vec]

        return P_Intersect, P1P2, P2P3, P1P3
    else:
        return None


###########################################################
def AddPlaneMesh(DimX, DimY, Name):
    x = DimX / 2
    y = DimY / 2
    verts = [(-x, -y, 0.0), (x, -y, 0.0), (-x, y, 0.0), (x, y, 0.0)]
    faces = [(0, 1, 3, 2)]
    mesh_data = bpy.data.meshes.new(f"{Name}_mesh")
    mesh_data.from_pydata(verts, [], faces)
    uvs = mesh_data.uv_layers.new(name=f"{Name}_uv")
    # Returns True if any invalid geometry was removed.
    corrections = mesh_data.validate(verbose=True, clean_customdata=True)
    # Load BMesh with mesh data.
    bm = bmesh.new()
    bm.from_mesh(mesh_data)
    bm.to_mesh(mesh_data)
    bm.free()
    mesh_data.update(calc_edges=True, calc_edges_loose=True)

    return mesh_data


def AddPlaneObject(Name, mesh, CollName):
    Plane_obj = bpy.data.objects.new(Name, mesh)
    MyColl = bpy.data.collections.get(CollName)

    if not MyColl:
        MyColl = bpy.data.collections.new(CollName)

    if not MyColl in bpy.context.scene.collection.children[:]:
        bpy.context.scene.collection.children.link(MyColl)

    if not Plane_obj in MyColl.objects[:]:
        MyColl.objects.link(Plane_obj)

    return Plane_obj


def MoveToCollection(obj, CollName):

    OldColl = obj.users_collection  # list of all collection the obj is in
    NewColl = bpy.data.collections.get(CollName)
    if not NewColl:
        NewColl = bpy.data.collections.new(CollName)
        bpy.context.scene.collection.children.link(NewColl)
    if not obj in NewColl.objects[:]:
        NewColl.objects.link(obj)  # link obj to scene
    if OldColl:
        for Coll in OldColl:  # unlink from all  precedent obj collections
            if Coll is not NewColl:
                Coll.objects.unlink(obj)


def VolumeRender(DcmInfo, GpShader, ShadersBlendFile):

    INTACT_Props = bpy.context.scene.INTACT_Props

    CtVolumeList = [
        obj for obj in bpy.context.scene.objects if "INTACT_CTVolume_" in obj.name
    ]
    Preffix = DcmInfo["Preffix"]

    Sp = Spacing = DcmInfo["RenderSp"]
    Sz = Size = DcmInfo["RenderSz"]
    Origin = DcmInfo["Origin"]
    Direction = DcmInfo["Direction"]
    TransformMatrix = DcmInfo["TransformMatrix"]
    DimX, DimY, DimZ = (Sz[0] * Sp[0], Sz[1] * Sp[1], Sz[2] * Sp[2])
    Offset = Sp[2]
    # ImagesList = sorted(os.listdir(PngDir))
    ImagesNamesList = sorted(
        [img.name for img in bpy.data.images if img.name.startswith(Preffix)]
    )
    ImagesList = [bpy.data.images[Name] for Name in ImagesNamesList]
    #################################################################################
    Start = Tcounter()
    #################################################################################
    # ///////////////////////////////////////////////////////////////////////////#
    ######################## Set Render settings : #############################
    Scene_Settings()
    ###################### Change to ORTHO persp with nice view angle :##########
    # ViewMatrix = Matrix(
    #     (
    #         (0.8435, -0.5371, -0.0000, 1.2269),
    #         (0.2497, 0.3923, 0.8853, -15.1467),
    #         (-0.4755, -0.7468, 0.4650, -55.2801),
    #         (0.0000, 0.0000, 0.0000, 1.0000),
    #     )
    # )
    ViewMatrix = Matrix(
        (
            (0.8677, -0.4971, 0.0000, 4.0023),
            (0.4080, 0.7123, 0.5711, -14.1835),
            (-0.2839, -0.4956, 0.8209, -94.0148),
            (0.0000, 0.0000, 0.0000, 1.0000),
        )
    )
    for scr in bpy.data.screens:
        # if scr.name in ["Layout", "Scripting", "Shading"]:
        for area in [ar for ar in scr.areas if ar.type == "VIEW_3D"]:
            for space in [sp for sp in area.spaces if sp.type == "VIEW_3D"]:
                r3d = space.region_3d
                r3d.view_perspective = "ORTHO"
                r3d.view_distance = 400
                r3d.view_matrix = ViewMatrix
                r3d.update()

    ################### Load all PNG images : ###############################
    # for ImagePNG in ImagesList:
    #     image_path = join(PngDir, ImagePNG)
    #     bpy.data.images.load(image_path)

    # bpy.ops.file.pack_all()

    ###############################################################################################
    # Add Planes with textured material :
    ###############################################################################################
    PlansList = []
    ############################# START LOOP ##################################

    for i, ImageData in enumerate(ImagesList):
        # # Add Plane :
        # ##########################################
        Name = f"{Preffix}_PLANE_{i}"
        mesh = AddPlaneMesh(DimX, DimY, Name)
        CollName = "CT_Voxel"

        obj = AddPlaneObject(Name, mesh, CollName)
        obj.location[2] = i * Offset
        PlansList.append(obj)

        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj



        ##########################################
        # Add Material:
        mat = bpy.data.materials.new(f"{Preffix}_Voxelmat_{i}")
        mat.use_nodes = True
        node_tree = mat.node_tree
        nodes = node_tree.nodes
        links = node_tree.links

        for node in nodes:
            if node.type != "OUTPUT_MATERIAL":
                nodes.remove(node)

        # ImageData = bpy.data.images.get(ImagePNG)
        TextureCoord = AddNode(nodes, type="ShaderNodeTexCoord", name="TextureCoord")
        ImageTexture = AddNode(nodes, type="ShaderNodeTexImage", name="Image Texture")

        ImageTexture.image = ImageData
        ImageData.colorspace_settings.name = "Non-Color"

        materialOutput = nodes["Material Output"]

        links.new(TextureCoord.outputs[0], ImageTexture.inputs[0])

        # Load VGS Group Node :
        VGS = bpy.data.node_groups.get(GpShader)
        if not VGS:
            filepath = join(ShadersBlendFile, "NodeTree", GpShader)
            directory = join(ShadersBlendFile, "NodeTree")
            filename = GpShader
            bpy.ops.wm.append(filepath=filepath, filename=filename, directory=directory)
            VGS = bpy.data.node_groups.get(GpShader)

        GroupNode = nodes.new("ShaderNodeGroup")
        GroupNode.node_tree = VGS

        links.new(ImageTexture.outputs["Color"], GroupNode.inputs[0])
        links.new(GroupNode.outputs[0], materialOutput.inputs["Surface"])
        for slot in obj.material_slots:
            bpy.ops.object.material_slot_remove()

        obj.active_material = mat

        mat.blend_method = "HASHED"
        mat.shadow_method = "HASHED"

        # print(f"{ImagePNG} Processed ...")
        # bpy.ops.wm.redraw_timer(type="DRAW_SWAP", iterations=3)  # --Work good but Slow down volume Render

        ############################# END LOOP ##################################

    # Join Planes Make Cube Voxel :
    bpy.ops.object.select_all(action="DESELECT")
    for obj in PlansList:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
    bpy.context.view_layer.layer_collection.children["CT_Voxel"].hide_viewport = False
    bpy.ops.object.join()

    Voxel = bpy.context.object

    Voxel.name = f"{Preffix}_CTVolume"
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="MEDIAN")

    Voxel.matrix_world = TransformMatrix
    Override, area3D, space3D = CtxOverride(bpy.context)

    bpy.ops.view3d.view_selected(Override, use_all_regions=False)

    for scr in bpy.data.screens:
        # if scr.name in ["Layout", "Scripting", "Shading"]:
        for area in [ar for ar in scr.areas if ar.type == "VIEW_3D"]:
            for space in [sp for sp in area.spaces if sp.type == "VIEW_3D"]:
                space.shading.type = "MATERIAL"

    for i in range(3):
        # Voxel.lock_location[i] = True
        # Voxel.lock_rotation[i] = True
        Voxel.lock_scale[i] = True

    Finish = Tcounter()
    print(f"CT-Scan loaded in {Finish-Start} secondes")


def Scene_Settings():
    scn = bpy.context.scene
    scn.render.engine = "BLENDER_EEVEE"
    scn.eevee.use_gtao = True
    scn.eevee.gtao_distance = 15
    scn.eevee.gtao_factor = 2.0
    scn.eevee.gtao_quality = 0.4
    scn.eevee.use_gtao_bounce = True
    scn.eevee.use_gtao_bent_normals = True
    scn.eevee.shadow_cube_size = "512"
    scn.eevee.shadow_cascade_size = "512"
    scn.eevee.use_soft_shadows = True
    scn.eevee.taa_samples = 16
    scn.view_settings.look = "High Contrast"
    scn.eevee.use_ssr = True

    # boost the near clip distance, to avoid z fighting of planes on boolean 3D mesh + the end clip distance
    # to avoid cutting off the back end of larger meshes
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            space = area.spaces.active
            space.clip_start = 2
            space.clip_end = 5000
            break


#################################################################################################
# Add Slices :
#################################################################################################
def SlicesUpdate(scene, slice_index):
    """ Update slices when moved in UI. Slice index determines which slice to update 0 = axial, 1 = Coronal,
    2 = Sagital
    """
    INTACT_Props = bpy.context.scene.INTACT_Props
    slice_name_suffixes = ["_AXIAL_SLICE", "_CORONAL_SLICE", "_SAGITAL_SLICE"]
    position_properties = ["Axial_Slice_Pos", "Coronal_Slice_Pos", "Sagital_Slice_Pos"]
    rotation_properties = ["Axial_Slice_Rot", "Coronal_Slice_Rot", "Sagital_Slice_Rot"]

    Planes = [
        obj
        for obj in bpy.context.scene.objects
        if (obj.name[2:4] == "IT" and obj.name.endswith(slice_name_suffixes[slice_index]))
    ]
    SLICES_POINTER = [
        obj
        for obj in bpy.context.scene.objects
        if (obj.name.startswith("IT") and obj.name.endswith("_SLICES_POINTER"))
    ]

    if Planes:
        ActiveObject = bpy.context.view_layer.objects.active
        position_property = position_properties[slice_index]
        rotation_property = rotation_properties[slice_index]

        Condition1 = True
        Preffix = Planes[0].name[2:7]

        if Condition1:

            Plane = [obj for obj in Planes if Preffix in obj.name][0]
            DcmInfoDict = eval(INTACT_Props.DcmInfo)
            DcmInfo = DcmInfoDict[Preffix]
            ImageData = AbsPath(DcmInfo["Nrrd255Path"])

            Condition = exists(ImageData)

            if Condition:

                CTVolume = bpy.data.objects.get(f"{Preffix}_CTVolume")
                TransformMatrix = CTVolume.matrix_world

                SlicesDir = AbsPath(DcmInfo["SlicesDir"])
                # TransformMatrix = DcmInfo["TransformMatrix"]
                ImageName = f"{Plane.name}.png"
                ImagePath = join(SlicesDir, ImageName)

                #########################################
                #########################################
                # Get ImageData Infos :
                Image3D_255 = sitk.ReadImage(ImageData)
                Sp = Spacing = Image3D_255.GetSpacing()
                Sz = Size = Image3D_255.GetSize()
                Ortho_Origin = (
                        -0.5 * np.array(Sp) * (np.array(Sz) - np.array((1, 1, 1)))
                )
                Image3D_255.SetOrigin(Ortho_Origin)
                Image3D_255.SetDirection(np.identity(3).flatten())

                # Output Parameters :
                if slice_index == 0:
                    Out_Origin = [Ortho_Origin[0], Ortho_Origin[1], 0]
                    Out_Size = (Sz[0], Sz[1], 1)
                elif slice_index == 1:
                    Out_Origin = [Ortho_Origin[0], Ortho_Origin[2], 0]
                    Out_Size = (Sz[0], Sz[2], 1)
                elif slice_index == 2:
                    Out_Origin = [Ortho_Origin[1], Ortho_Origin[2], 0]
                    Out_Size = (Sz[1], Sz[2], 1)

                Out_Direction = Vector(np.identity(3).flatten())
                Out_Spacing = Sp

                ######################################
                # Get Plane Orientation and location :
                PlanMatrix = TransformMatrix.inverted() @ Plane.matrix_world
                Rot = PlanMatrix.to_euler()
                Trans = PlanMatrix.translation
                Rvec = (Rot.x, Rot.y, Rot.z)
                Tvec = Trans

                ##########################################
                # Euler3DTransform :
                Euler3D = sitk.Euler3DTransform()
                Euler3D.SetCenter((0, 0, 0))
                Euler3D.SetRotation(Rvec[0], Rvec[1], Rvec[2])
                Euler3D.SetTranslation(Tvec)
                Euler3D.ComputeZYXOn()
                #########################################

                Image2D = sitk.Resample(
                    Image3D_255,
                    Out_Size,
                    Euler3D,
                    sitk.sitkLinear,
                    Out_Origin,
                    Out_Spacing,
                    Out_Direction,
                    0,
                )

                #Change contrast based on user input#
                Image2D = sitk.Cast(
                sitk.IntensityWindowing(
                Image2D,
                windowMinimum=INTACT_Props.Slice_min,
                windowMaximum=INTACT_Props.Slice_max,
                outputMinimum=0.0,
                outputMaximum=255.0,
                ),
                sitk.sitkUInt8,
                )

                #############################################
                # Write Image :
                Array = sitk.GetArrayFromImage(Image2D)
                Flipped_Array = np.flipud(Array.reshape(Array.shape[1], Array.shape[2]))

                cv2.imwrite(ImagePath, Flipped_Array)
                ############################################
                # Update Blender Image data :
                BlenderImage = bpy.data.images.get(f"{Plane.name}.png")
                if not BlenderImage:
                    bpy.data.images.load(ImagePath)
                    BlenderImage = bpy.data.images.get(f"{Plane.name}.png")
                else:
                    BlenderImage.filepath = ImagePath
                    BlenderImage.reload()

                # This is necessary, as if the cube boolean is added (while the cropping cube
                # is outside of the 3D mesh) it leads to some of the slices being displayed solid white.
                # This seems to be a bug within blender.
                if INTACT_Props.Remove_slice_outside_object:
                    Plane.data.update()


@persistent
def AxialSliceUpdate(scene):
    SlicesUpdate(scene, 0)


@persistent
def CoronalSliceUpdate(scene):
    SlicesUpdate(scene, 1)


@persistent
def SagitalSliceUpdate(scene):
    SlicesUpdate(scene, 2)

def SlicesUpdateAll(scene):
    SlicesUpdate(scene, 0)
    SlicesUpdate(scene, 1)
    SlicesUpdate(scene, 2)



####################################################################
def Add_Cam_To_Plane(Plane, CamDistance, ClipOffset):
    Override, _, _ = CtxOverride(bpy.context)
    bpy.ops.object.camera_add(Override)
    Cam = bpy.context.object
    Cam.name = f"{Plane.name}_CAM"
    Cam.data.name = f"{Plane.name}_CAM_data"
    Cam.data.type = "ORTHO"
    Cam.data.ortho_scale = max(Plane.dimensions) * 1.1
    Cam.data.display_size = 10

    Cam.matrix_world = Plane.matrix_world
    bpy.ops.transform.translate(
        value=(0, 0, CamDistance),
        orient_type="LOCAL",
        orient_matrix=Plane.matrix_world.to_3x3(),
        orient_matrix_type="LOCAL",
        constraint_axis=(False, False, True),
    )
    Cam.data.clip_start = CamDistance - ClipOffset
    Cam.data.clip_end = CamDistance + ClipOffset

    Plane.select_set(True)
    bpy.context.view_layer.objects.active = Plane
    bpy.ops.object.parent_set(type="OBJECT", keep_transform=True)
    Cam.hide_set(True)
    Cam.select_set(False)
    return Cam

####################################################################


def set_slice_orientation(ct_volume, slice, slice_index):
    """ Sets position/rotation of slices. Slice index determines which slice to set 0 = axial, 1 = Coronal,
    2 = Sagital"""
    if slice_index == 0:
        # AxialPlane.location = VC
        slice.matrix_world = ct_volume.matrix_world
    elif slice_index == 1:
        rotation_euler = Euler((pi / 2, 0.0, 0.0), "XYZ")
        RotMtx = rotation_euler.to_matrix().to_4x4()
        slice.matrix_world = ct_volume.matrix_world @ RotMtx
    elif slice_index == 2:
        rotation_euler = Euler((pi / 2, 0.0, -pi / 2), "XYZ")
        RotMtx = rotation_euler.to_matrix().to_4x4()
        slice.matrix_world = ct_volume.matrix_world @ RotMtx


def AddSlice(slice_index, Preffix, DcmInfo):
    """ Add slices to the UI. Slice index determines which slice to add 0 = axial, 1 = Coronal,
        2 = Sagital
    """
    CTVolume = bpy.data.objects.get(f"{Preffix}_CTVolume")

    Sp, Sz, Origin, Direction, VC = (
        DcmInfo["Spacing"],
        DcmInfo["Size"],
        DcmInfo["Origin"],
        DcmInfo["Direction"],
        DcmInfo["VolumeCenter"],
    )

    DimX, DimY, DimZ = (Sz[0] * Sp[0], Sz[1] * Sp[1], Sz[2] * Sp[2])

    if slice_index == 0:
        name = f"1_{Preffix}_AXIAL_SLICE"
        PlaneDims = Vector((DimX, DimY, 0.0))
    elif slice_index == 1:
        name = f"2_{Preffix}_CORONAL_SLICE"
        PlaneDims = Vector((DimX, DimZ, 0.0))
    elif slice_index == 2:
        name = f"3_{Preffix}_SAGITAL_SLICE"
        PlaneDims = Vector((DimY, DimZ, 0.0))

    # Remove old Slices and their data meshs :
    OldSlices = [obj for obj in bpy.context.view_layer.objects if name in obj.name]
    OldSliceMeshs = [mesh for mesh in bpy.data.meshes if name in mesh.name]

    for obj in OldSlices:
        bpy.data.objects.remove(obj)
    for mesh in OldSliceMeshs:
        bpy.data.meshes.remove(mesh)

    # Add Slice :
    bpy.ops.mesh.primitive_plane_add()
    Plane = bpy.context.active_object
    Plane.name = name
    Plane.data.name = f"{name}_mesh"
    Plane.rotation_mode = "XYZ"
    Plane.dimensions = PlaneDims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    set_slice_orientation(CTVolume, Plane, slice_index)

    # Add Material :
    mat = bpy.data.materials.get(f"{name}_mat") or bpy.data.materials.new(f"{name}_mat")
    mat.use_fake_user = True

    for slot in Plane.material_slots:
        bpy.ops.object.material_slot_remove()
    bpy.ops.object.material_slot_add()
    Plane.active_material = mat

    mat.use_nodes = True
    node_tree = mat.node_tree
    nodes = node_tree.nodes
    links = node_tree.links

    for node in nodes:
        if node.type != "OUTPUT_MATERIAL":
            nodes.remove(node)
    SlicesDir = AbsPath(DcmInfo["SlicesDir"])
    ImageName = f"{name}.png"
    ImagePath = join(SlicesDir, ImageName)

    # write "name.png" to here ImagePath
    SlicesUpdate(bpy.context.scene, slice_index)

    # BlenderImage = bpy.data.images.get(ImageName)
    BlenderImage = bpy.data.images.get(ImageName) or bpy.data.images.load(ImagePath)

    TextureCoord = AddNode(nodes, type="ShaderNodeTexCoord", name="TextureCoord")
    ImageTexture = AddNode(nodes, type="ShaderNodeTexImage", name="Image Texture")
    ImageTexture.image = BlenderImage
    BlenderImage.colorspace_settings.name = "Non-Color"
    materialOutput = nodes["Material Output"]
    links.new(TextureCoord.outputs[0], ImageTexture.inputs[0])
    links.new(ImageTexture.outputs[0], materialOutput.inputs[0])
    bpy.context.scene.transform_orientation_slots[0].type = "LOCAL"
    bpy.context.scene.transform_orientation_slots[1].type = "LOCAL"
    bpy.ops.wm.tool_set_by_id(name="builtin.move")

    return Plane


#############################################################################
# SimpleITK vtk Image to Mesh Functions :
#############################################################################
def HuTo255(Hu, Wmin, Wmax):
    V255 = int(((Hu - Wmin) / (Wmax - Wmin)) * 255)
    return V255


def ResizeImage(sitkImage, Ratio):
    image = sitkImage
    Sz = image.GetSize()
    Sp = image.GetSpacing()
    new_size = [int(Sz[0] * Ratio), int(Sz[1] * Ratio), int(Sz[2] * Ratio)]
    new_spacing = [Sp[0] / Ratio, Sp[1] / Ratio, Sp[2] / Ratio]

    ResizedImage = sitk.Resample(
        image,
        new_size,
        sitk.Transform(),
        sitk.sitkLinear,
        image.GetOrigin(),
        new_spacing,
        image.GetDirection(),
        0,
    )
    return ResizedImage


# def VTK_Terminal_progress(caller, event, q):
#     ProgRatio = round(float(caller.GetProgress()), 2)
#     q.put(
#         ["loop", f"PROGRESS : {step} processing...", "", {start}, {finish}, ProgRatio]
#     )


def VTKprogress(caller, event):
    pourcentage = int(caller.GetProgress() * 100)
    calldata = str(int(caller.GetProgress() * 100)) + " %"
    # print(calldata)
    sys.stdout.write(f"\r {calldata}")
    sys.stdout.flush()
    progress_bar(pourcentage, Delay=1)


def TerminalProgressBar(
    q,
    counter_start,
    iter=100,
    maxfill=20,
    symb1="\u2588",
    symb2="\u2502",
    periode=10,
):

    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="cp65001")
        # cmd = "chcp 65001 & set PYTHONIOENCODING=utf-8"
        # subprocess.call(cmd, shell=True)

    print("\n")

    while True:
        if not q.empty():
            signal = q.get()

            if "End" in signal[0]:
                finish = Tcounter()
                line = f"{symb1*maxfill}  100% Finished.------Total Time : {round(finish-counter_start,2)}"
                # clear sys.stdout line and return to line start:
                # sys.stdout.write("\r")
                # sys.stdout.write(" " * 100)
                # sys.stdout.flush()
                # sys.stdout.write("\r")
                # write line :
                sys.stdout.write("\r" + " " * 80 + "\r" + line)  # f"{Char}"*i*2
                sys.stdout.flush()
                break

            if "GuessTime" in signal[0]:
                _, Uptxt, Lowtxt, start, finish, periode = signal
                for i in range(iter):

                    if q.empty():

                        ratio = start + (((i + 1) / iter) * (finish - start))
                        pourcentage = int(ratio * 100)
                        symb1_fill = int(ratio * maxfill)
                        symb2_fill = int(maxfill - symb1_fill)
                        line = f"{symb1*symb1_fill}{symb2*symb2_fill}  {pourcentage}% {Uptxt}"
                        # clear sys.stdout line and return to line start:
                        # sys.stdout.write("\r"+" " * 80)
                        # sys.stdout.flush()
                        # write line :
                        sys.stdout.write("\r" + " " * 80 + "\r" + line)  # f"{Char}"*i*2
                        sys.stdout.flush()
                        sleep(periode / iter)
                    else:
                        break

            if "loop" in signal[0]:
                _, Uptxt, Lowtxt, start, finish, progFloat = signal
                ratio = start + (progFloat * (finish - start))
                pourcentage = int(ratio * 100)
                symb1_fill = int(ratio * maxfill)
                symb2_fill = int(maxfill - symb1_fill)
                line = f"{symb1*symb1_fill}{symb2*symb2_fill}  {pourcentage}% {Uptxt}"
                # clear sys.stdout line and return to line start:
                # sys.stdout.write("\r")
                # sys.stdout.write(" " * 100)
                # sys.stdout.flush()
                # sys.stdout.write("\r")
                # write line :
                sys.stdout.write("\r" + " " * 80 + "\r" + line)  # f"{Char}"*i*2
                sys.stdout.flush()

        else:
            sleep(0.1)


def sitkTovtk(sitkImage):
    """Convert sitk image to a VTK image"""
    sitkArray = sitk.GetArrayFromImage(sitkImage)  # .astype(np.uint8)
    vtkImage = vtk.vtkImageData()

    Sp = Spacing = sitkImage.GetSpacing()
    Sz = Size = sitkImage.GetSize()

    vtkImage.SetDimensions(Sz)
    vtkImage.SetSpacing(Sp)
    vtkImage.SetOrigin(0, 0, 0)
    vtkImage.SetDirectionMatrix(1, 0, 0, 0, 1, 0, 0, 0, 1)
    vtkImage.SetExtent(0, Sz[0] - 1, 0, Sz[1] - 1, 0, Sz[2] - 1)

    VtkArray = numpy_support.numpy_to_vtk(
        sitkArray.ravel(), deep=True, array_type=VTK_UNSIGNED_INT
    )
    VtkArray.SetNumberOfComponents(1)
    vtkImage.GetPointData().SetScalars(VtkArray)

    vtkImage.Modified()
    return vtkImage


def vtk_MC_Func(vtkImage, Treshold):
    MCFilter = vtk.vtkMarchingCubes()
    MCFilter.ComputeNormalsOn()
    MCFilter.SetValue(0, Treshold)
    MCFilter.SetInputData(vtkImage)
    MCFilter.Update()
    mesh = vtk.vtkPolyData()
    mesh.DeepCopy(MCFilter.GetOutput())
    return mesh


def vtkMeshReduction(q, mesh, reduction, step, start, finish):
    """Reduce a mesh using VTK's vtkQuadricDecimation filter."""

    def VTK_Terminal_progress(caller, event):
        ProgRatio = round(float(caller.GetProgress()), 2)
        q.put(
            [
                "loop",
                f"PROGRESS : {step}...",
                "",
                start,
                finish,
                ProgRatio,
            ]
        )

    decimatFilter = vtk.vtkQuadricDecimation()
    decimatFilter.SetInputData(mesh)
    decimatFilter.SetTargetReduction(reduction)

    decimatFilter.AddObserver(ProgEvent, VTK_Terminal_progress)
    decimatFilter.Update()

    mesh.DeepCopy(decimatFilter.GetOutput())
    return mesh


def vtkSmoothMesh(q, mesh, Iterations, step, start, finish):
    """Smooth a mesh using VTK's vtkSmoothPolyData filter."""

    def VTK_Terminal_progress(caller, event):
        ProgRatio = round(float(caller.GetProgress()), 2)
        q.put(
            [
                "loop",
                f"PROGRESS : {step}...",
                "",
                start,
                finish,
                ProgRatio,
            ]
        )

    SmoothFilter = vtk.vtkSmoothPolyDataFilter()
    SmoothFilter.SetInputData(mesh)
    SmoothFilter.SetNumberOfIterations(int(Iterations))
    SmoothFilter.SetFeatureAngle(45)
    SmoothFilter.SetRelaxationFactor(0.05)
    SmoothFilter.AddObserver(ProgEvent, VTK_Terminal_progress)
    SmoothFilter.Update()
    mesh.DeepCopy(SmoothFilter.GetOutput())
    return mesh


def vtkTransformMesh(mesh, Matrix):
    """Transform a mesh using VTK's vtkTransformPolyData filter."""

    Transform = vtk.vtkTransform()
    Transform.SetMatrix(Matrix)

    transformFilter = vtk.vtkTransformPolyDataFilter()
    transformFilter.SetInputData(mesh)
    transformFilter.SetTransform(Transform)
    transformFilter.Update()
    mesh.DeepCopy(transformFilter.GetOutput())
    return mesh


def vtkfillholes(mesh, size):
    FillHolesFilter = vtk.vtkFillHolesFilter()
    FillHolesFilter.SetInputData(mesh)
    FillHolesFilter.SetHoleSize(size)
    FillHolesFilter.Update()
    mesh.DeepCopy(FillHolesFilter.GetOutput())
    return mesh


def vtkCleanMesh(mesh, connectivityFilter=False):
    """Clean a mesh using VTK's CleanPolyData filter."""

    ConnectFilter = vtk.vtkPolyDataConnectivityFilter()
    CleanFilter = vtk.vtkCleanPolyData()

    if connectivityFilter:

        ConnectFilter.SetInputData(mesh)
        ConnectFilter.SetExtractionModeToLargestRegion()
        CleanFilter.SetInputConnection(ConnectFilter.GetOutputPort())

    else:
        CleanFilter.SetInputData(mesh)

    CleanFilter.Update()
    mesh.DeepCopy(CleanFilter.GetOutput())
    return mesh


def sitkToContourArray(sitkImage, HuMin, HuMax, Wmin, Wmax, Thikness):
    """Convert sitk image to a VTK image"""

    def HuTo255(Hu, Wmin, Wmax):
        V255 = ((Hu - Wmin) / (Wmax - Wmin)) * 255
        return V255

    Image3D_255 = sitk.Cast(
        sitk.IntensityWindowing(
            sitkImage,
            windowMinimum=Wmin,
            windowMaximum=Wmax,
            outputMinimum=0.0,
            outputMaximum=255.0,
        ),
        sitk.sitkUInt8,
    )
    Array = sitk.GetArrayFromImage(Image3D_255)
    ContourArray255 = Array.copy()
    for i in range(ContourArray255.shape[0]):
        Slice = ContourArray255[i, :, :]
        ret, binary = cv2.threshold(
            Slice,
            HuTo255(HuMin, Wmin, Wmax),
            HuTo255(HuMax, Wmin, Wmax),
            cv2.THRESH_BINARY,
        )
        contours, hierarchy = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        SliceContour = np.ones(binary.shape, dtype="uint8")
        cv2.drawContours(SliceContour, contours, -1, 255, Thikness)

        ContourArray255[i, :, :] = SliceContour

    return ContourArray255


def vtkContourFilter(vtkImage, isovalue=0.0):
    """Extract an isosurface from a volume."""

    ContourFilter = vtk.vtkContourFilter()
    ContourFilter.SetInputData(vtkImage)
    ContourFilter.SetValue(0, isovalue)
    ContourFilter.Update()
    mesh = vtk.vtkPolyData()
    mesh.DeepCopy(ContourFilter.GetOutput())
    return mesh


def GuessTimeLoopFunc(signal, q):
    _, Uptxt, Lowtxt, start, finish, periode = signal
    i = 0
    iterations = 10
    while i < iterations and q.empty():
        ProgRatio = start + (((i + 1) / iterations) * (finish - start))
        q.put(
            [
                "loop",
                Uptxt,
                "",
                start,
                finish,
                ProgRatio,
            ]
        )
        sleep(periode / iterations)
        i += 1


def CV2_progress_bar(q, iter=100):
    while True:
        if not q.empty():
            signal = q.get()

            if "End" in signal[0]:
                pourcentage = 100
                Uptxt = "Finished."
                progress_bar(pourcentage, Uptxt)
                break
            if "GuessTime" in signal[0]:
                _, Uptxt, Lowtxt, start, finish, periode = signal
                i = 0
                iterations = 10
                Delay = periode / iterations
                while i < iterations:
                    if q.empty():
                        ProgRatio = start + (
                            round(((i + 1) / iterations), 2) * (finish - start)
                        )
                        pourcentage = int(ProgRatio * 100)
                        progress_bar(
                            pourcentage, Uptxt, Delay=int(Delay * 1000)
                        )  # , Delay = int(Delay*1000)
                        sleep(Delay)
                        i += 1
                    else:
                        break
                # t = threading.Thread(target=GuessTimeLoopFunc, args=[signal, q], daemon=True)
                # t.start()
                # t.join()
                # while i < iterations and q.empty() :
                #     ratio = start + (((i + 1) / iter) * (finish - start))
                #     pourcentage = int(ratio * 100)
                #     progress_bar(pourcentage, Uptxt)
                #     sleep(periode / iter)

                # iter = 5
                # _, Uptxt, Lowtxt, start, finish, periode = signal
                # for i in range(iter):

                #     if q.empty():

                #         ratio = start + (((i + 1) / iter) * (finish - start))
                #         pourcentage = int(ratio * 100)
                #         progress_bar(pourcentage, Uptxt)
                #         sleep(periode / iter)
                #     else:
                #         break

            if "loop" in signal[0]:
                _, Uptxt, Lowtxt, start, finish, progFloat = signal
                ratio = start + (progFloat * (finish - start))
                pourcentage = int(ratio * 100)
                progress_bar(pourcentage, Uptxt)

        else:
            sleep(0.01)


def progress_bar(pourcentage, Uptxt, Lowtxt="", Title="INTACT", Delay=1):

    X, Y = WindowWidth, WindowHeight = (500, 100)
    BackGround = np.ones((Y, X, 3), dtype=np.uint8) * 255
    # Progress bar Parameters :
    maxFill = X - 70
    minFill = 40
    barColor = (50, 200, 0)
    BarHeight = 20
    barUp = Y - 60
    barBottom = barUp + BarHeight
    # Text :
    font = cv2.FONT_HERSHEY_SIMPLEX
    fontScale = 0.5
    fontThikness = 1
    fontColor = (0, 0, 0)
    lineStyle = cv2.LINE_AA

    chunk = (maxFill - 40) / 100

    img = BackGround.copy()
    fill = minFill + int(pourcentage * chunk)
    img[barUp:barBottom, minFill:fill] = barColor

    img = cv2.putText(
        img,
        f"{pourcentage}%",
        (maxFill + 10, barBottom - 8),
        # (fill + 10, barBottom - 10),
        font,
        fontScale,
        fontColor,
        fontThikness,
        lineStyle,
    )

    img = cv2.putText(
        img,
        Uptxt,
        (minFill, barUp - 10),
        font,
        fontScale,
        fontColor,
        fontThikness,
        lineStyle,
    )
    cv2.imshow(Title, img)

    cv2.waitKey(Delay)

    if pourcentage == 100:
        img = BackGround.copy()
        img[barUp:barBottom, minFill:maxFill] = (50, 200, 0)
        img = cv2.putText(
            img,
            "100%",
            (maxFill + 10, barBottom - 8),
            font,
            fontScale,
            fontColor,
            fontThikness,
            lineStyle,
        )

        img = cv2.putText(
            img,
            Uptxt,
            (minFill, barUp - 10),
            font,
            fontScale,
            fontColor,
            fontThikness,
            lineStyle,
        )
        cv2.imshow(Title, img)
        cv2.waitKey(Delay)
        sleep(4)
        cv2.destroyAllWindows()




###########################################################################
# Add INTACT MultiView :
def INTACT_MultiView_Toggle(Preffix):

    WM = bpy.context.window_manager

    # Duplicate Area3D to new window :
    MainWindow = WM.windows[0]
    LayoutScreen = bpy.data.screens["Layout"]
    LayoutArea3D = [area for area in LayoutScreen.areas if area.type == "VIEW_3D"][0]

    Override = {"window": MainWindow, "screen": LayoutScreen, "area": LayoutArea3D}
    bpy.ops.screen.area_dupli(Override, "INVOKE_DEFAULT")

    # Get MultiView (Window, Screen, Area3D, Space3D, Region3D) and set prefferences :
    MultiView_Window = WM.windows[-1]
    MultiView_Screen = MultiView_Window.screen

    MultiView_Area3D = [
        area for area in MultiView_Screen.areas if area.type == "VIEW_3D"
    ][0]
    MultiView_Space3D = [
        space for space in MultiView_Area3D.spaces if space.type == "VIEW_3D"
    ][0]
    MultiView_Region3D = [
        reg for reg in MultiView_Area3D.regions if reg.type == "WINDOW"
    ][0]

    MultiView_Area3D.type = (
        "CONSOLE"  # change area type for update : bug dont respond to spliting
    )

    # 1rst Step : Vertical Split .

    Override = {
        "window": MultiView_Window,
        "screen": MultiView_Screen,
        "area": MultiView_Area3D,
        "space_data": MultiView_Space3D,
        "region": MultiView_Region3D,
    }

    bpy.ops.screen.area_split(Override, direction="VERTICAL", factor=1 / 5)
    MultiView_Screen.areas[0].type = "OUTLINER"
    MultiView_Screen.areas[1].type = "OUTLINER"

    # 2nd Step : Horizontal Split .
    Active_Area = MultiView_Screen.areas[0]
    Active_Space = [space for space in Active_Area.spaces if space.type == "VIEW_3D"][0]
    Active_Region = [reg for reg in Active_Area.regions if reg.type == "WINDOW"][0]
    Override = {
        "window": MultiView_Window,
        "screen": MultiView_Screen,
        "area": Active_Area,
        "space_data": Active_Space,
        "region": Active_Region,
    }

    bpy.ops.screen.area_split(Override, direction="HORIZONTAL", factor=1 / 2)
    MultiView_Screen.areas[0].type = "VIEW_3D"
    MultiView_Screen.areas[1].type = "VIEW_3D"
    MultiView_Screen.areas[2].type = "VIEW_3D"

    # 3rd Step : Vertical Split .
    Active_Area = MultiView_Screen.areas[0]
    Active_Space = [space for space in Active_Area.spaces if space.type == "VIEW_3D"][0]
    Active_Region = [reg for reg in Active_Area.regions if reg.type == "WINDOW"][0]
    Override = {
        "window": MultiView_Window,
        "screen": MultiView_Screen,
        "area": Active_Area,
        "space_data": Active_Space,
        "region": Active_Region,
    }

    bpy.ops.screen.area_split(Override, direction="VERTICAL", factor=1 / 2)
    MultiView_Screen.areas[0].type = "OUTLINER"
    MultiView_Screen.areas[1].type = "OUTLINER"
    MultiView_Screen.areas[2].type = "OUTLINER"
    MultiView_Screen.areas[3].type = "OUTLINER"

    # 4th Step : Vertical Split .
    Active_Area = MultiView_Screen.areas[2]
    Active_Space = [space for space in Active_Area.spaces if space.type == "VIEW_3D"][0]
    Active_Region = [reg for reg in Active_Area.regions if reg.type == "WINDOW"][0]
    Override = {
        "window": MultiView_Window,
        "screen": MultiView_Screen,
        "area": Active_Area,
        "space_data": Active_Space,
        "region": Active_Region,
    }

    bpy.ops.screen.area_split(Override, direction="VERTICAL", factor=1 / 2)
    MultiView_Screen.areas[0].type = "VIEW_3D"
    MultiView_Screen.areas[1].type = "VIEW_3D"
    MultiView_Screen.areas[2].type = "VIEW_3D"
    MultiView_Screen.areas[3].type = "VIEW_3D"
    MultiView_Screen.areas[4].type = "VIEW_3D"

    # 4th Step : Horizontal Split .
    Active_Area = MultiView_Screen.areas[1]
    Active_Space = [space for space in Active_Area.spaces if space.type == "VIEW_3D"][0]
    Active_Region = [reg for reg in Active_Area.regions if reg.type == "WINDOW"][0]
    Override = {
        "window": MultiView_Window,
        "screen": MultiView_Screen,
        "area": Active_Area,
        "space_data": Active_Space,
        "region": Active_Region,
    }

    bpy.ops.screen.area_split(Override, direction="HORIZONTAL", factor=1 / 2)

    MultiView_Screen.areas[1].type = "OUTLINER"
    MultiView_Screen.areas[5].type = "PROPERTIES"

    # Set MultiView Areas 3D prefferences :
    for MultiView_Area3D in MultiView_Screen.areas:

        if MultiView_Area3D.type == "VIEW_3D":
            MultiView_Space3D = [
                space for space in MultiView_Area3D.spaces if space.type == "VIEW_3D"
            ][0]

            Override = {
                "window": MultiView_Window,
                "screen": MultiView_Screen,
                "area": MultiView_Area3D,
                "space_data": MultiView_Space3D,
            }

            bpy.ops.wm.tool_set_by_id(Override, name="builtin.move")
            MultiView_Space3D.overlay.show_text = True
            MultiView_Space3D.show_region_ui = False
            MultiView_Space3D.show_region_toolbar = True
            MultiView_Space3D.region_3d.view_perspective = "ORTHO"
            MultiView_Space3D.show_gizmo_navigate = False
            MultiView_Space3D.show_region_tool_header = False
            MultiView_Space3D.overlay.show_floor = False
            MultiView_Space3D.overlay.show_ortho_grid = False
            MultiView_Space3D.overlay.show_relationship_lines = False
            MultiView_Space3D.overlay.show_extras = True
            MultiView_Space3D.overlay.show_bones = False
            MultiView_Space3D.overlay.show_motion_paths = False

            MultiView_Space3D.shading.type = "SOLID"
            MultiView_Space3D.shading.light = "STUDIO"
            MultiView_Space3D.shading.studio_light = "outdoor.sl"
            MultiView_Space3D.shading.color_type = "TEXTURE"
            MultiView_Space3D.shading.background_type = "VIEWPORT"
            MultiView_Space3D.shading.background_color = [0.7, 0.7, 0.7]

            MultiView_Space3D.shading.type = "MATERIAL"
            # 'Material' Shading Light method :
            MultiView_Space3D.shading.use_scene_lights = True
            MultiView_Space3D.shading.use_scene_world = False

            # 'RENDERED' Shading Light method :
            MultiView_Space3D.shading.use_scene_lights_render = False
            MultiView_Space3D.shading.use_scene_world_render = True

            MultiView_Space3D.shading.studio_light = "forest.exr"
            MultiView_Space3D.shading.studiolight_rotate_z = 0
            MultiView_Space3D.shading.studiolight_intensity = 1.5
            MultiView_Space3D.shading.studiolight_background_alpha = 0.0
            MultiView_Space3D.shading.studiolight_background_blur = 0.0

            MultiView_Space3D.shading.render_pass = "COMBINED"

            MultiView_Space3D.show_region_header = False

    OUTLINER = TopLeft = MultiView_Screen.areas[1]
    PROPERTIES = DownLeft = MultiView_Screen.areas[5]
    AXIAL = TopMiddle = MultiView_Screen.areas[3]
    CORONAL = TopRight = MultiView_Screen.areas[0]
    SAGITAL = DownRight = MultiView_Screen.areas[2]
    VIEW_3D = DownMiddle = MultiView_Screen.areas[4]

    return MultiView_Window, OUTLINER, PROPERTIES, AXIAL, CORONAL, SAGITAL, VIEW_3D
