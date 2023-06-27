import bpy
from . import INTACT_Utils
from bpy.app.handlers import persistent

from .INTACT_Utils import *

# ---------------------------------------------------------------------------
#          Operators
# ---------------------------------------------------------------------------


class CroppingCubeCreation(bpy.types.Operator):
    """Create a cropping cube that cuts through the surface scan and CT"""
    bl_idname = "intact.cropping_cube_creation"
    bl_label = "Cropping Cube Creation"

    def cropping_cube_boolean(self, context):
        """
        This part of the script ensures that the cropping cubes are in fact cropping the objects.
        """
        INTACT_Props = context.scene.INTACT_Props

        ct_vol = INTACT_Props.CT_Vol
        surf_3d = INTACT_Props.Surf_3D
        cropping_cube = INTACT_Props.Cropping_Cube

        # Add boolean to ct volume + surface scan (if it exists)
        to_add_boolean = [ct_vol]
        if surf_3d:
            to_add_boolean.append(surf_3d)

        for obj in to_add_boolean:
            obj_bool = obj.modifiers.new(type="BOOLEAN", name="Cropping Cube")
            obj_bool.operation = 'DIFFERENCE'
            obj_bool.object = cropping_cube

        print("\nBoolean modifiers applied")

    def execute(self, context):
        INTACT_Props = context.scene.INTACT_Props
        ct_vol = INTACT_Props.CT_Vol
        surf_3d = INTACT_Props.Surf_3D
        cropping_cube_name = "Crop CT"
        cube_collection_name = "Cropping Cubes"

        if not ct_vol:
            message = [" Please input CT Volume first "]
            INTACT_Utils.ShowMessageBox(message=message, icon="COLORSET_02_VEC")
            return {"CANCELLED"}

        cropping_cube = context.scene.objects.get(cropping_cube_name)
        cube_exists = cropping_cube and cropping_cube.users_collection[0].name == cube_collection_name
        if not cube_exists:
            # Make cropping cube slightly larger than the CT volume to avoid glitchy artefacts caused by the cube
            # faces exactly matching the CT volume edges.
            croppingcubedim = ct_vol.dimensions*1.001
            croppingcube_x = croppingcubedim[0]

            croppingcubeloc = ct_vol.location
            loc_x = croppingcubeloc[0]
            loc_y = croppingcubeloc[1]
            loc_z = croppingcubeloc[2]
            print("\nDimensions of CT voxel representation extracted.")

            # Create one cropping cube, to use for all axes
            bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD',
                                            location=(loc_x + croppingcube_x, loc_y, loc_z), scale=croppingcubedim)
            cropct = bpy.context.active_object
            INTACT_Props.Cropping_Cube = cropct
            cropct.name = cropping_cube_name
            # Display as bounds, so can see through the cube to the object inside
            cropct.display_type = "BOUNDS"

            # If there's a surface scan, add a material with alpha of 0. This will make the surface mesh's boolean faces
            # transparent, as long as it has a material slot with the same material
            if surf_3d:
                cropct_material_name = "crop_transparent"
                cropct_material = bpy.data.materials.new(name=cropct_material_name)
                cropct_material.use_nodes = True
                cropct_material.blend_method = "HASHED"
                tree_nodes = cropct_material.node_tree.nodes
                tree_nodes['Principled BSDF'].inputs["Alpha"].default_value = 0

                cropct.data.materials.append(cropct_material)
                surf_3d.data.materials.append(cropct_material)

            # Lock rotation and scale, so it can only be translated along x/y/z
            cropct.lock_rotation[0] = True
            cropct.lock_rotation[1] = True
            cropct.lock_rotation[2] = True
            cropct.lock_scale[0] = True
            cropct.lock_scale[1] = True
            cropct.lock_scale[2] = True
            cropct.hide_render = True

            if cube_collection_name not in bpy.data.collections:
                cube_collection = bpy.data.collections.new("Cropping Cubes")
                bpy.context.scene.collection.children.link(cube_collection)
            else:
                cube_collection = bpy.data.collections[cube_collection_name]

            # remove from default collection
            for collection in cropct.users_collection[:]:
                collection.objects.unlink(cropct)
            # add to cropping cubes collection
            cube_collection.objects.link(cropct)

            # Add booleans
            self.cropping_cube_boolean(context)

            # select ct volume, so it's easy to carry on with further operations (with all deselected the ui
            # says 'please load data first')
            #bpy.ops.object.select_all(action="DESELECT")
            #ct_vol.select_set(True)

        return {'FINISHED'}


def add_cube_boolean(obj, cropping_cube, cube_boolean_name):
    cube_bool = obj.modifiers.new(type="BOOLEAN", name=cube_boolean_name)
    cube_bool.operation = 'INTERSECT'
    cube_bool.object = cropping_cube


def set_modifier_visibility(obj, modifier_names, is_visible):
    for modifier_name in modifier_names:
        if modifier_name in obj.modifiers:
            modifier = obj.modifiers.get(modifier_name)
            modifier.show_viewport = is_visible
            modifier.show_render = is_visible


def enable_surf3d_slice(context):
    """Cut areas outside the surf3d mesh using a boolean modifier - two booleans are added, one for the surface mesh
    and one for the cropping cube. This ensures that only the parts of the slices inside the mesh + inside the cube
    are shown"""

    surface_copy_name = "Surface scan copy"
    mesh_boolean_name = "3D scan"
    INTACT_Props = context.scene.INTACT_Props
    surf_3d = INTACT_Props.Surf_3D
    slices = [INTACT_Props.Axial_Slice, INTACT_Props.Coronal_Slice, INTACT_Props.Sagital_Slice]
    cropping_cube_collection = bpy.data.collections['Cropping Cubes']
    cube_boolean_name = "Cropping Cube"

    # Make a copy of the surface scan (if it doesn't already exist). This will be used to boolean the slices.
    # Can't use original as this is already being cut into by the cropping cube.
    surf_copy = context.scene.objects.get(surface_copy_name)
    surf_copy_exists = surf_copy and surf_copy.users_collection[0] == cropping_cube_collection
    if not surf_copy_exists:
        surf_copy = surf_3d.copy()
        surf_copy.name = surface_copy_name
        surf_copy.modifiers.clear()
        surf_copy.hide_viewport = True
        surf_copy.hide_render = True
        cropping_cube_collection.objects.link(surf_copy)

    # Add boolean modifier. If it already exists, just enable it in viewport and render
    for slice in slices:
        if mesh_boolean_name not in slice.modifiers and cube_boolean_name not in slice.modifiers:
            mesh_bool = slice.modifiers.new(type="BOOLEAN", name=mesh_boolean_name)
            mesh_bool.operation = 'INTERSECT'
            mesh_bool.object = surf_copy

            # Move to top of modifier stack
            bpy.ops.object.modifier_move_to_index({'object': slice}, modifier=mesh_bool.name, index=0)
            add_cube_boolean(slice, INTACT_Props.Cropping_Cube, cube_boolean_name)
        else:
            set_modifier_visibility(slice, [mesh_boolean_name, cube_boolean_name], True)


def enable_ct_alpha_slice(context):
    """Show areas of slices below the threshold as transparent. This uses the same threshold as the volume render +
    also adds a boolean for the cropping cube, so areas outside the cube are hidden"""

    INTACT_Props = context.scene.INTACT_Props
    slices = [INTACT_Props.Axial_Slice, INTACT_Props.Coronal_Slice, INTACT_Props.Sagital_Slice]
    cube_boolean_name = "Cropping Cube"

    # Create alpha material + cube boolean. If already exists, just enable material + boolean.
    for slice in slices:
        default_material_name = f"{slice.name}_mat"
        alpha_material_name = f"{default_material_name}_transparency"

        if alpha_material_name not in bpy.data.materials:
            default_material = bpy.data.materials[default_material_name]
            default_material_image_node = default_material.node_tree.nodes["Image Texture"]

            # make material
            alpha_material = bpy.data.materials.new(name=alpha_material_name)
            alpha_material.use_nodes = True
            alpha_material.use_fake_user = True
            alpha_material.blend_method = "HASHED"
            tree_nodes = alpha_material.node_tree.nodes
            tree_nodes.clear()

            tex_coord_node = tree_nodes.new(type="ShaderNodeTexCoord")
            tex_coord_node.location = -257, 121

            image_node = tree_nodes.new(type='ShaderNodeTexImage')
            image_node.image = default_material_image_node.image
            image_node.location = -49, 136

            transparency_node = tree_nodes.new(type="ShaderNodeBsdfTransparent")
            transparency_node.location = 331, 89
            emission_node = tree_nodes.new(type="ShaderNodeEmission")
            emission_node.location = 337, -49
            mix_node = tree_nodes.new(type="ShaderNodeMixShader")
            mix_node.location = 580, 144

            # threshold node group from resources blend file
            threshold_node = tree_nodes.new("ShaderNodeGroup")
            threshold_node.node_tree = bpy.data.node_groups[INTACT_Props.ThresholdGroupNodeName]
            threshold_node.location = 325, 266

            node_output = tree_nodes.new(type='ShaderNodeOutputMaterial')
            node_output.name = "Output"
            node_output.location = 776, 139

            # Link all nodes
            links = alpha_material.node_tree.links
            links.new(tex_coord_node.outputs["Generated"], image_node.inputs["Vector"])
            links.new(image_node.outputs["Color"], threshold_node.inputs["Value"])
            links.new(threshold_node.outputs["Value"], mix_node.inputs["Fac"])
            links.new(image_node.outputs["Color"], emission_node.inputs["Color"])
            links.new(transparency_node.outputs["BSDF"], mix_node.inputs[1])
            links.new(emission_node.outputs["Emission"], mix_node.inputs[2])
            links.new(mix_node.outputs["Shader"], node_output.inputs["Surface"])

            slice.material_slots[0].material = alpha_material

            add_cube_boolean(slice, INTACT_Props.Cropping_Cube, cube_boolean_name)

        else:
                slice.material_slots[0].material = bpy.data.materials[alpha_material_name]
                set_modifier_visibility(slice, ["Cropping Cube"], True)


def enable_boolean_slice(context):
    """
    This part of the script ensures that the surface scan mesh acts as a boolean to cut into the slices.
    """
    INTACT_Props = context.scene.INTACT_Props
    surf_3d = INTACT_Props.Surf_3D

    if surf_3d:
        enable_surf3d_slice(context)

    else:
        enable_ct_alpha_slice(context)

    print("\nBoolean modifiers applied to all slices")


def disable_boolean_slice(context):
    """
    This part of the script disables the boolean modifier in viewport + render.
    """
    INTACT_Props = context.scene.INTACT_Props
    slices = [INTACT_Props.Axial_Slice, INTACT_Props.Coronal_Slice, INTACT_Props.Sagital_Slice]

    for slice in slices:
        set_modifier_visibility(slice, ["3D scan", "Cropping Cube"], False)

        default_slice_material = f"{slice.name}_mat"
        if slice.material_slots[0].material.name != default_slice_material:
            slice.material_slots[0].material = bpy.data.materials[default_slice_material]

    print("\nBoolean modifiers disabled on all slices")


def boolean_slice(self, context):
    if self.Remove_slice_outside_object:
        enable_boolean_slice(context)
    else:
        disable_boolean_slice(context)


def lock_location_rotation(slice, driver_axis, lock):
    """lock location on all axes without driver, lock rotation on all axes"""
    for i in range(3):
        slice.lock_rotation[i] = lock
        if i != driver_axis:
            slice.lock_location[i] = lock


def get_original_dimensions(obj):
    """Get original dimensions, before any modifiers"""
    coords = np.empty(3 * len(obj.data.vertices))
    obj.data.vertices.foreach_get("co", coords)

    x, y, z = coords.reshape((-1, 3)).T

    return (
        x.max() - x.min(),
        y.max() - y.min(),
        z.max() - z.min()
    )


def enable_track_slices_to_cropping_cube(context):
    """
    Link the location / rotation of slices to the cropping cube
    """
    INTACT_Props = context.scene.INTACT_Props
    ct_vol = INTACT_Props.CT_Vol
    sagital_slice = INTACT_Props.Sagital_Slice
    coronal_slice = INTACT_Props.Coronal_Slice
    axial_slice = INTACT_Props.Axial_Slice
    cropping_cube = INTACT_Props.Cropping_Cube

    transforms = ["X", "Y", "Z"]
    slices = [sagital_slice, coronal_slice, axial_slice]

    # reset position/rotation of all
    INTACT_Utils.set_slice_orientation(ct_vol, slices[0], 2)
    INTACT_Utils.set_slice_orientation(ct_vol, slices[1], 1)
    INTACT_Utils.set_slice_orientation(ct_vol, slices[2], 0)

    for i in range(len(transforms)):
        location_driver = slices[i].driver_add("location", i)
        cropping_cube_location = location_driver.driver.variables.new()
        cropping_cube_location.name = "cl"
        cropping_cube_location.type = 'TRANSFORMS'
        cropping_cube_location.targets[0].id = cropping_cube
        cropping_cube_location.targets[0].transform_type = f'LOC_{transforms[i]}'

        ct_vol_location = location_driver.driver.variables.new()
        ct_vol_location.name = "ctl"
        ct_vol_location.type = 'TRANSFORMS'
        ct_vol_location.targets[0].id = ct_vol
        ct_vol_location.targets[0].transform_type = f'LOC_{transforms[i]}'

        cropping_cube_dim = location_driver.driver.variables.new()
        cropping_cube_dim.name = "cd"
        cropping_cube_dim.type = 'SINGLE_PROP'
        cropping_cube_dim.targets[0].id = cropping_cube
        cropping_cube_dim.targets[0].data_path = f"dimensions[{i}]"

        # The CT volume dimensions will change dynamically as it is cut into with the boolean. Therefore we need to put
        # the original CT dimensions directly into the driver expression
        original_ct_dim = get_original_dimensions(ct_vol)
        half_ct_vol_dim = 0.5*original_ct_dim[i]

        location_driver.driver.expression = \
            f"cl+0.5*cd if cl-0.5*cd < ctl-{half_ct_vol_dim} <= cl+0.5*cd else " \
            f"cl-0.5*cd if cl+0.5*cd > ctl+{half_ct_vol_dim} >= cl-0.5*cd else " \
            f"ctl-{half_ct_vol_dim} if cl-0.5*cd < ctl-{half_ct_vol_dim} and " \
            f"cl+0.5*cd < ctl-{half_ct_vol_dim} else ctl+{half_ct_vol_dim}"

        lock_location_rotation(slices[i], i, True)

    # Give slices a tiny bit of thickness, so they don't give z fighting artefacts when tracked right on top of the
    # boolean faces of meshes
    solidify_modifier_name = "Solidify"
    for slice in slices:
        if solidify_modifier_name not in slice.modifiers:
            solidify = slice.modifiers.new(type="SOLIDIFY", name=solidify_modifier_name)
            solidify.thickness = 1
            solidify.offset = 0

    # force planes to update. Otherwise, the wrong slice will be shown on initialisation.
    context.view_layer.update()

    return {'FINISHED'}


def disable_track_slices_to_cropping_cube(context):
    """
    This block of code removes the drivers that link the slices to the cropping cubes, to save computational power
    """
    INTACT_Props = context.scene.INTACT_Props
    slices = [INTACT_Props.Sagital_Slice, INTACT_Props.Coronal_Slice, INTACT_Props.Axial_Slice]

    for i in range(len(slices)):
        slices[i].driver_remove("location", i)
        lock_location_rotation(slices[i], i, False)

    return {'FINISHED'}


def track_slices(self, context):
    if self.Track_slices_to_cropping_cube:
        enable_track_slices_to_cropping_cube(context)
    else:
        disable_track_slices_to_cropping_cube(context)


def surface_scan_roughness(self, context):
    """Set roughness of the surface scan material"""
    INTACT_Props = context.scene.INTACT_Props
    surf_3d = INTACT_Props.Surf_3D
    if surf_3d:
        material = surf_3d.material_slots[0].material
        material.node_tree.nodes["Principled BSDF"].inputs['Roughness'].default_value = self.Surface_scan_roughness


def slice_thickness(self, context):
    """Set thickness of the slices"""
    INTACT_Props = context.scene.INTACT_Props
    slices = [INTACT_Props.Axial_Slice, INTACT_Props.Coronal_Slice, INTACT_Props.Sagital_Slice]
    solidify_modifier_name = "Solidify"

    for slice in slices:
        if slice and (solidify_modifier_name in slice.modifiers):
            slice.modifiers[solidify_modifier_name].thickness = self.Slice_thickness

class INTACT_OT_AddSlices(bpy.types.Operator):
    """ Add Volume Slices """

    bl_idname = "intact.addslices"
    bl_label = "SLICE VOLUME"

    def execute(self, context):
        INTACT_Props = bpy.context.scene.INTACT_Props

        if not INTACT_Props.CT_Vol:
            message = [" Please input CT Volume first "]
            ShowMessageBox(message=message, icon="COLORSET_02_VEC")
            return {"CANCELLED"}
        else:
            Vol = INTACT_Props.CT_Vol
            Preffix = Vol.name[:5]
            DcmInfoDict = eval(INTACT_Props.DcmInfo)
            DcmInfo = DcmInfoDict[Preffix]

            AxialPlane = AddSlice(0, Preffix, DcmInfo)
            MoveToCollection(obj=AxialPlane, CollName="SLICES")
            INTACT_Props.Axial_Slice = AxialPlane

            CoronalPlane = AddSlice(1, Preffix, DcmInfo)
            MoveToCollection(obj=CoronalPlane, CollName="SLICES")
            INTACT_Props.Coronal_Slice = CoronalPlane

            SagitalPlane = AddSlice(2, Preffix, DcmInfo)
            MoveToCollection(obj=SagitalPlane, CollName="SLICES")
            INTACT_Props.Sagital_Slice = SagitalPlane

            # Add Cameras :

            bpy.context.scene.render.resolution_x = 512
            bpy.context.scene.render.resolution_y = 512

            [
                bpy.data.cameras.remove(cam)
                for cam in bpy.data.cameras
                if f"{AxialPlane.name}_CAM" in cam.name
            ]
            AxialCam = Add_Cam_To_Plane(AxialPlane, CamDistance=100, ClipOffset=1)
            MoveToCollection(obj=AxialCam, CollName="SLICES-CAMERAS")

            [
                bpy.data.cameras.remove(cam)
                for cam in bpy.data.cameras
                if f"{CoronalPlane.name}_CAM" in cam.name
            ]
            CoronalCam = Add_Cam_To_Plane(
                CoronalPlane, CamDistance=100, ClipOffset=1
            )
            MoveToCollection(obj=CoronalCam, CollName="SLICES-CAMERAS")

            [
                bpy.data.cameras.remove(cam)
                for cam in bpy.data.cameras
                if f"{SagitalPlane.name}_CAM" in cam.name
            ]
            SagitalCam = Add_Cam_To_Plane(
                SagitalPlane, CamDistance=100, ClipOffset=1
            )
            MoveToCollection(obj=SagitalCam, CollName="SLICES-CAMERAS")

            for obj in bpy.data.objects:
                if obj.name == f"{Preffix}_SLICES_POINTER":
                    bpy.data.objects.remove(obj)

            bpy.ops.object.empty_add(
                type="PLAIN_AXES",
                align="WORLD",
                location=AxialPlane.location,
                scale=(1, 1, 1),
            )
            SLICES_POINTER = bpy.context.object
            SLICES_POINTER.empty_display_size = 20
            SLICES_POINTER.show_name = True
            SLICES_POINTER.show_in_front = True
            SLICES_POINTER.name = f"{Preffix}_SLICES_POINTER"

            Override, _, _ = CtxOverride(bpy.context)

            bpy.ops.object.select_all(Override, action="DESELECT")
            AxialPlane.select_set(True)
            CoronalPlane.select_set(True)
            SagitalPlane.select_set(True)
            SLICES_POINTER.select_set(True)
            bpy.context.view_layer.objects.active = SLICES_POINTER
            bpy.ops.object.parent_set(type="OBJECT", keep_transform=True)
            bpy.ops.object.select_all(Override, action="DESELECT")
            SLICES_POINTER.select_set(True)
            Vol.select_set(True)
            bpy.context.view_layer.objects.active = Vol
            bpy.ops.object.parent_set(type="OBJECT", keep_transform=True)

            bpy.ops.object.select_all(Override, action="DESELECT")
            SLICES_POINTER.select_set(True)
            bpy.context.view_layer.objects.active = SLICES_POINTER
            MoveToCollection(obj=SLICES_POINTER, CollName="SLICES_POINTERS")

            return {"FINISHED"}

class INTACT_OT_MultiView(bpy.types.Operator):
    """ MultiView Toggle """

    bl_idname = "intact.multiview"
    bl_label = "MULTI-VIEW"

    def execute(self, context):

        INTACT_Props = bpy.context.scene.INTACT_Props
        Vol = INTACT_Props.CT_Vol
        AxialPlane = INTACT_Props.Axial_Slice
        CoronalPlane = INTACT_Props.Coronal_Slice
        SagitalPlane = INTACT_Props.Sagital_Slice

        if not Vol:
            message = [" Please input CT Volume first "]
            ShowMessageBox(message=message, icon="COLORSET_02_VEC")
            return {"CANCELLED"}
        elif not AxialPlane or not CoronalPlane or not SagitalPlane:
            message = [" Please click 'Slice Volume' first "]
            ShowMessageBox(message=message, icon="COLORSET_02_VEC")
            return {"CANCELLED"}
        else:
            Preffix = INTACT_Props.CT_Vol.name[:5]
            SLICES_POINTER = bpy.data.objects.get(f"{Preffix}_SLICES_POINTER")

            bpy.context.scene.unit_settings.scale_length = 0.001
            bpy.context.scene.unit_settings.length_unit = "MILLIMETERS"

            (
                MultiView_Window,
                OUTLINER,
                PROPERTIES,
                AXIAL,
                CORONAL,
                SAGITAL,
                VIEW_3D,
            ) = INTACT_MultiView_Toggle(Preffix)
            MultiView_Screen = MultiView_Window.screen
            AXIAL_Space3D = [
                Space for Space in AXIAL.spaces if Space.type == "VIEW_3D"
            ][0]
            AXIAL_Region = [
                reg for reg in AXIAL.regions if reg.type == "WINDOW"
            ][0]

            CORONAL_Space3D = [
                Space for Space in CORONAL.spaces if Space.type == "VIEW_3D"
            ][0]
            CORONAL_Region = [
                reg for reg in CORONAL.regions if reg.type == "WINDOW"
            ][0]

            SAGITAL_Space3D = [
                Space for Space in SAGITAL.spaces if Space.type == "VIEW_3D"
            ][0]
            SAGITAL_Region = [
                reg for reg in SAGITAL.regions if reg.type == "WINDOW"
            ][0]
            # AXIAL Cam view toggle :

            AxialCam = bpy.data.objects.get(f"{AxialPlane.name}_CAM")
            AXIAL_Space3D.use_local_collections = True
            AXIAL_Space3D.use_local_camera = True
            AXIAL_Space3D.camera = AxialCam
            Override = {
                "window": MultiView_Window,
                "screen": MultiView_Screen,
                "area": AXIAL,
                "space_data": AXIAL_Space3D,
                "region": AXIAL_Region,
            }
            bpy.ops.view3d.view_camera(Override)

            # CORONAL Cam view toggle :
            CoronalCam = bpy.data.objects.get(f"{CoronalPlane.name}_CAM")
            CORONAL_Space3D.use_local_collections = True
            CORONAL_Space3D.use_local_camera = True
            CORONAL_Space3D.camera = CoronalCam
            Override = {
                "window": MultiView_Window,
                "screen": MultiView_Screen,
                "area": CORONAL,
                "space_data": CORONAL_Space3D,
                "region": CORONAL_Region,
            }
            bpy.ops.view3d.view_camera(Override)

            # AXIAL Cam view toggle :
            SagitalCam = bpy.data.objects.get(f"{SagitalPlane.name}_CAM")
            SAGITAL_Space3D.use_local_collections = True
            SAGITAL_Space3D.use_local_camera = True
            SAGITAL_Space3D.camera = SagitalCam
            Override = {
                "window": MultiView_Window,
                "screen": MultiView_Screen,
                "area": SAGITAL,
                "space_data": SAGITAL_Space3D,
                "region": SAGITAL_Region,
            }
            bpy.ops.view3d.view_camera(Override)

            bpy.ops.object.select_all(Override, action="DESELECT")
            SLICES_POINTER.select_set(True)
            bpy.context.view_layer.objects.active = SLICES_POINTER

        return {"FINISHED"}

# ---------------------------------------------------------------------------
#          Registration
# ---------------------------------------------------------------------------

classes = [INTACT_OT_AddSlices,
    INTACT_OT_MultiView,
    CroppingCubeCreation]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
