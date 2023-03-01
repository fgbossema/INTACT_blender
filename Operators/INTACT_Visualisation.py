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
        #add the default here?
        
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
        cropping_cube_name = "Crop CT"
        cube_collection_name = "Cropping Cubes"

        if not ct_vol:
            message = [" Please input CT Volume first "]
            INTACT_Utils.ShowMessageBox(message=message, icon="COLORSET_02_VEC")
            return {"CANCELLED"}

        cropping_cube = context.scene.objects.get(cropping_cube_name)
        cube_exists = cropping_cube and cropping_cube.users_collection[0].name == cube_collection_name
        if not cube_exists:
            croppingcubedim = ct_vol.dimensions
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
            bpy.ops.object.select_all(action="DESELECT")
            context.view_layer.objects.active = ct_vol

        return {'FINISHED'}


def enable_boolean_slice(context):
    """
    This part of the script ensures that the surface scan mesh acts as a boolean to cut into the slices.
    """
    INTACT_Props = context.scene.INTACT_Props
    surf_3d = INTACT_Props.Surf_3D
    slices = [INTACT_Props.Axial_Slice, INTACT_Props.Coronal_Slice, INTACT_Props.Sagital_Slice]

    cropping_cube_collection = bpy.data.collections['Cropping Cubes']
    surface_copy_name = "Surface scan copy"
    mesh_boolean_name = "3D scan"
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
            bpy.ops.object.modifier_move_to_index({'object':slice}, modifier=mesh_bool.name, index=0)

            cube_bool = slice.modifiers.new(type="BOOLEAN", name=cube_boolean_name)
            cube_bool.operation = 'INTERSECT'
            cube_bool.object = INTACT_Props.Cropping_Cube
        else:
            for modifier_name in [mesh_boolean_name, cube_boolean_name]:
                modifier = slice.modifiers.get(modifier_name)
                modifier.show_viewport = True
                modifier.show_render = True

    print("\nBoolean modifiers applied to all slices")


def disable_boolean_slice(context):
    """
    This part of the script disables the boolean modifier in viewport + render.
    """
    INTACT_Props = context.scene.INTACT_Props
    slices = [INTACT_Props.Axial_Slice, INTACT_Props.Coronal_Slice, INTACT_Props.Sagital_Slice]

    for slice in slices:
        for modifier_name in ["3D scan", "Cropping Cube"]:
            modifier = slice.modifiers.get(modifier_name)
            modifier.show_viewport = False
            modifier.show_render = False

    print("\nBoolean modifiers disabled on all slices")


def boolean_slice(self, context):
    if self.Remove_slice_outside_surface:
        enable_boolean_slice(context)
    else:
        disable_boolean_slice(context)


def lock_location_rotation(slice, driver_axis, lock):
    """lock location on all axes without driver, lock rotation on all axes"""
    for i in range(3):
        slice.lock_rotation[i] = lock
        if i != driver_axis:
            slice.lock_location[i] = lock


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

        ct_vol_dim = location_driver.driver.variables.new()
        ct_vol_dim.name = "ctd"
        ct_vol_dim.type = 'SINGLE_PROP'
        ct_vol_dim.targets[0].id = ct_vol
        ct_vol_dim.targets[0].data_path = f"dimensions[{i}]"

        location_driver.driver.expression = \
            "cl+0.5*cd if cl-0.5*cd < ctl-0.5*ctd <= cl+0.5*cd else " \
            "cl-0.5*cd if cl+0.5*cd > ctl+0.5*ctd >= cl-0.5*cd else " \
            "ctl-0.5*ctd if cl-0.5*cd < ctl-0.5*ctd and " \
            "cl+0.5*cd < ctl-0.5*ctd else ctl+0.5*ctd"

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

        
# ---------------------------------------------------------------------------
#          Registration
# ---------------------------------------------------------------------------

classes = [INTACT_OT_AddSlices,
    CroppingCubeCreation]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
