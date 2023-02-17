import bpy
from . import INTACT_Utils
from bpy.app.handlers import persistent
    
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

        ct_bool = ct_vol.modifiers.new(type="BOOLEAN", name="Cropping Cube")
        ct_bool.operation = 'DIFFERENCE'
        ct_bool.object = cropping_cube

        surf_bool = surf_3d.modifiers.new(type="BOOLEAN", name="Cropping Cube")
        surf_bool.operation = "DIFFERENCE"
        surf_bool.object = cropping_cube

        print("\nBoolean modifiers applied to both CT visualisation and 3D surface scan")

    def execute(self, context):
        INTACT_Props = context.scene.INTACT_Props
        ct_vol = INTACT_Props.CT_Vol

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
        cropct.name = "Crop CT"
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

        collection = bpy.data.collections.new("Cropping Cubes")
        bpy.context.scene.collection.children.link(collection)
        collection.objects.link(cropct)

        # Add booleans
        self.cropping_cube_boolean(context)

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


def calculate_slice_location(cropping_cube_location, cropping_cube_dim, ct_vol_location, ct_vol_dim):
    left_ct_vol_edge = ct_vol_location - (0.5 * ct_vol_dim)
    right_ct_vol_edge = ct_vol_location + (0.5 * ct_vol_dim)
    left_cropping_cube_edge = cropping_cube_location - (0.5 * cropping_cube_dim)
    right_cropping_cube_edge = cropping_cube_location + (0.5 * cropping_cube_dim)

    if left_cropping_cube_edge < left_ct_vol_edge <= right_cropping_cube_edge:
        location = right_cropping_cube_edge
    elif right_cropping_cube_edge > right_ct_vol_edge >= left_cropping_cube_edge:
        location = left_cropping_cube_edge
    elif left_cropping_cube_edge < left_ct_vol_edge and right_cropping_cube_edge < left_ct_vol_edge:
        location = left_ct_vol_edge
    else:
        location = right_ct_vol_edge

    return location


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
        cropping_cube_location.name = "cropping_cube_location"
        cropping_cube_location.type = 'TRANSFORMS'
        cropping_cube_location.targets[0].id = cropping_cube
        cropping_cube_location.targets[0].transform_type = f'LOC_{transforms[i]}'

        ct_vol_location = location_driver.driver.variables.new()
        ct_vol_location.name = "ct_vol_location"
        ct_vol_location.type = 'TRANSFORMS'
        ct_vol_location.targets[0].id = ct_vol
        ct_vol_location.targets[0].transform_type = f'LOC_{transforms[i]}'

        cropping_cube_dim = location_driver.driver.variables.new()
        cropping_cube_dim.name = "cropping_cube_dim"
        cropping_cube_dim.type = 'SINGLE_PROP'
        cropping_cube_dim.targets[0].id = cropping_cube
        cropping_cube_dim.targets[0].data_path = f"dimensions[{i}]"

        ct_vol_dim = location_driver.driver.variables.new()
        ct_vol_dim.name = "ct_vol_dim"
        ct_vol_dim.type = 'SINGLE_PROP'
        ct_vol_dim.targets[0].id = ct_vol
        ct_vol_dim.targets[0].data_path = f"dimensions[{i}]"

        location_driver.driver.expression = "calculate_slice_location(cropping_cube_location, cropping_cube_dim, " \
                                            "ct_vol_location, ct_vol_dim)"

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

    
# class Switch_Boolean_Solver(bpy.types.Operator):
#     """
#     This part of the script switch between "Fast" and "Exact" boolean solving. The first is, as the name suggests, not very computationally heavy,
#     making the tool very interactive and quick to use. However, this is also, at times, prone to some buggy visualisations, that are (mostly)
#     circumvented when the "Exact" solver is switched on. This is recommended for renders and other output.
#     """
#     bl_idname = "intact.switch_boolean_solver"
#     bl_label = "Switch Boolean Solver"
#
#     def execute(self, context):
#         INTACT_Props = context.scene.INTACT_Props
#         CT_Vol = INTACT_Props.CT_Vol
#         Surf_3D = INTACT_Props.Surf_3D
#
#         if CT_Vol.modifiers["Crop X"].solver == 'FAST':
#             #Select the CT scan
#             bpy.ops.object.select_all(action='DESELECT') #deselect all objects
#             bpy.context.view_layer.objects.active = CT_Vol #Selects the CT Volume
#             CT_Vol.select_set(True)
#
#             CT_Vol.modifiers["Crop X"].solver = 'EXACT'
#             CT_Vol.modifiers["Crop Y"].solver = 'EXACT'
#             CT_Vol.modifiers["Crop Z"].solver = 'EXACT'
#
#             #Select the 3D scan
#             bpy.ops.object.select_all(action='DESELECT') #deselect all objects
#             bpy.context.view_layer.objects.active = Surf_3D #Selects the 3D Surface scan
#             Surf_3D.select_set(True)
#
#             Surf_3D.modifiers["Crop X"].solver = 'EXACT'
#             Surf_3D.modifiers["Crop Y"].solver = 'EXACT'
#             Surf_3D.modifiers["Crop Z"].solver = 'EXACT'
#
#         elif CT_Vol.modifiers["Crop X"].solver == 'EXACT':
#             #Select the CT scan
#             bpy.ops.object.select_all(action='DESELECT') #deselect all objects
#             bpy.context.view_layer.objects.active = CT_Vol #Selects the CT Volume
#             CT_Vol.select_set(True)
#
#             CT_Vol.modifiers["Crop X"].solver = 'FAST'
#             CT_Vol.modifiers["Crop Y"].solver = 'FAST'
#             CT_Vol.modifiers["Crop Z"].solver = 'FAST'
#
#             #Select the 3D scan
#             bpy.ops.object.select_all(action='DESELECT') #deselect all objects
#             bpy.context.view_layer.objects.active = Surf_3D #Selects the 3D Surface scan
#             Surf_3D.select_set(True)
#
#             Surf_3D.modifiers["Crop X"].solver = 'FAST'
#             Surf_3D.modifiers["Crop Y"].solver = 'FAST'
#             Surf_3D.modifiers["Crop Z"].solver = 'FAST'
#
#         else:
#             print("ERROR. No boolean modifiers found. Check if you haven't renamed your CT scan and 3D-surface scan, and ensure you have gone through all prior steps.")
#
#         return {'FINISHED'}
        
# ---------------------------------------------------------------------------
#          Registration
# ---------------------------------------------------------------------------

classes = [
    CroppingCubeCreation]


@persistent
def load_handler(dummy):
    # print("Loading driver function for slices")
    bpy.app.driver_namespace['calculate_slice_location'] = calculate_slice_location


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        bpy.app.handlers.load_post.append(load_handler)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        bpy.app.handlers.load_post.remove(load_handler)


if __name__ == "__main__":
    register()
