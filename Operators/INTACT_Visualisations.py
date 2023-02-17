import bpy
from mathutils import Euler
import math
from . import INTACT_Utils
from bpy.app.handlers import persistent
    
#---------------------------------------------------------------------------
#          Operators
#---------------------------------------------------------------------------
# class Init_Setup(bpy.types.Operator):
#     """
#     After importing your data (using BDental and Blender) and aligning the two data-types (either manually or via ICP), click this button.
#     This function sets up the right parameters for the render and view-port.
#     """
#     bl_idname = "intact.init_setup"
#     bl_label = "Initial Setup"
#
#     def execute(self, context):
#         for a in bpy.context.screen.areas:
#             if a.type == 'VIEW_3D':
#                 for s in a.spaces:
#                     if s.type == 'VIEW_3D':
#                         s.clip_start = 0.5
#                         s.clip_end = 5000
#         print("Viewport FOV set")
#         bpy.context.scene.render.engine = 'BLENDER_EEVEE'
#         print("Eevee Render engine enabled")
#         bpy.context.space_data.shading.type = 'MATERIAL'
#         print("Material shading in Viewport enabled")
#         print("Setup complete")
#         return {'FINISHED'}

# class Object_Selection(bpy.types.Operator):
#     """
#     This part of the script asks the user to define their CT voxel representation as well as their
#     3D surface scan. These will be then be re-named, such that later operations and actions can be
#     applied to them in the right order.
#
#     Select the CT voxel representation first, then Shift+click the 3D scan. The CT voxel representation
#     will now be the 'active' object, whereas the 3D scan is just a selected object.
#     """
#     bl_idname = "intact.object_selection"
#     bl_label = "Object Selection"
#
#     def execute(self, context):
#         INTACT_Props = context.scene.INTACT_Props
#
#         CT_Vol = INTACT_Props.CT_Vol
#         Surf_3D = INTACT_Props.Surf_3D
#
#         # bpy.ops.object.select_all(action='DESELECT') #deselect all objects
#         # bpy.context.view_layer.objects.active = Surf_3D
#         # Surf_3D.select_set(True)
#         #
#         # if not Surf_3D.users_collection[0].name == '3D Surface Scan':
#         #     bpy.ops.object.move_to_collection(collection_index=0, is_new=True, new_collection_name='3D Surface Scan')
#         # else:
#         #     pass
#         #
#         # print("\nPlease select your CT scan first, and then Shift+click your 3D scan.")
#
#         try:
#             slices = bpy.data.collections['SLICES'].all_objects
#             INTACT_Props.Axial_Slice = slices[0]
#             INTACT_Props.Coronal_Slice = slices[1]
#             INTACT_Props.Sagital_Slice = slices[2]
#
#             # Give slices a tiny bit of thickness, so they don't give z fighting artefacts when tracked right on top of the
#             # boolean faces of meshes
#             # TODO - this should probably go somewhere else
#             for slice in slices:
#                 solidify = slice.modifiers.new(type="SOLIDIFY", name="Solidify")
#                 solidify.thickness = 1
#                 solidify.offset = 0
#         except:
#             print("\nNo slices found. Ensure the collection in which they are kept has not changed name ('SLICES')")
#
#         # try:
#         #     Segments = bpy.data.collections['SEGMENTS'].all_objects
#         #     Seg = Segments[0]
#         #     try:
#         #         Seg.modifier_remove(modifier="CorrectiveSmooth")
#         #     except:
#         #         pass
#         # except:
#         #     print("\nNo segment found. Ensure the collection in which it is kept has not changed name ('SEGMENTS')")
#
#         # q1 = ''
#         # q1q = str("\nIs '" + CT_Vol.name + "' your CT voxel representation, and '" + Surf_3D.name + "' your 3D Surface scan? (answer y/n)")
#         #
#         # while q1 == '':
#         #     q1 = input(q1q)
#         #     if q1 == 'y' or q1 == 'Y' or q1 == 'Yes' or q1 == 'yes':
#         #         print("\nInput succesful. Move on to the next step.")
#         #         break
#         #     elif q1 == 'n' or q1 == 'N' or q1 == 'No' or q1 == 'no':
#         #         q1 = ''
#         #         print("\nUnsuccesful. Try selecting your two objects in the proper order, and click the button again. Select your CT object first, then SHIFT+Click your 3D Surface scan.")
#         #         break
#         #     else:
#         #         q1 = ''
#         #         print("\nPlease answer the question with 'y' or 'n'. Try again")
#         #         continue
#         #
#         # print("Your CT Volume: " + str(CT_Vol.name))
#         # print("Your 3D Surface Scan: " + str(Surf_3D.name))
#         # try:
#         #     print("Your Segmentation: " + str(Seg.name))
#         # except:
#         #     pass
#         # try:
#         #     print("Your Axial Slice: " + str(Axial_Slice.name))
#         #     print("Your Coronal Slice: " + str(Coronal_Slice.name))
#         #     print("Your Sagital Slice: " + str(Sagital_Slice.name))
#         # except:
#         #     pass
#         return {'FINISHED'}

class Cropping_Cube_Creation(bpy.types.Operator):
    """Create a cropping cube that cuts through the surface scan and CT"""
    bl_idname = "intact.cropping_cube_creation"
    bl_label = "Cropping Cube Creation"

    def cropping_cube_boolean(self, context):
        """
        This part of the script ensures that the cropping cubes are in fact cropping the objects.
        """
        INTACT_Props = context.scene.INTACT_Props
        CT_Vol = INTACT_Props.CT_Vol
        Surf_3D = INTACT_Props.Surf_3D
        Cropping_Cube = INTACT_Props.Cropping_Cube

        CT_bool = CT_Vol.modifiers.new(type="BOOLEAN", name="Cropping Cube")
        CT_bool.operation = 'DIFFERENCE'
        CT_bool.object = Cropping_Cube

        Surf_bool = Surf_3D.modifiers.new(type="BOOLEAN", name="Cropping Cube")
        Surf_bool.operation = "DIFFERENCE"
        Surf_bool.object = Cropping_Cube

        print("\nBoolean modifiers applied to both CT visualisation and 3D surface scan")

    def execute(self, context):
        INTACT_Props = context.scene.INTACT_Props
        CT_Vol = INTACT_Props.CT_Vol

        croppingcubedim = CT_Vol.dimensions
        croppingcube_x = croppingcubedim[0]
        # croppingcube_y = croppingcubedim[1]
        # croppingcube_z = croppingcubedim[2]
        
        croppingcubeloc = CT_Vol.location
        loc_x = croppingcubeloc[0]
        loc_y = croppingcubeloc[1]
        loc_z = croppingcubeloc[2]
        print("\nDimensions of CT voxel representation extracted.")

        # Just have one cropping cube
        # TODO - must be way to name it without selecting it, same for putting in collection
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
    Surf_3D = INTACT_Props.Surf_3D
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
        surf_copy = Surf_3D.copy()
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
    elif left_cropping_cube_edge < left_ct_vol_edge and right_cropping_cube_edge < left_ct_vol_edge:
        location = left_ct_vol_edge
    elif right_cropping_cube_edge > right_ct_vol_edge >= left_cropping_cube_edge:
        location = left_cropping_cube_edge
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
    These 6 blocks of code link the location and rotation of the axial slice to that of the X-cropping cube.
    """
    INTACT_Props = context.scene.INTACT_Props
    CT_Vol = INTACT_Props.CT_Vol
    Sagital_Slice = INTACT_Props.Sagital_Slice
    Coronal_Slice = INTACT_Props.Coronal_Slice
    Axial_Slice = INTACT_Props.Axial_Slice
    Cropping_Cube = INTACT_Props.Cropping_Cube

    transforms = ["X", "Y", "Z"]
    slices = [Sagital_Slice, Coronal_Slice, Axial_Slice]
    # bpy.app.driver_namespace['calculate_slice_location'] = calculate_slice_location

    # reset position/rotation of all
    INTACT_Utils.set_slice_orientation(CT_Vol, slices[0], 2)
    INTACT_Utils.set_slice_orientation(CT_Vol, slices[1], 1)
    INTACT_Utils.set_slice_orientation(CT_Vol, slices[2], 0)

    for i in range(len(transforms)):
        location_driver = slices[i].driver_add("location", i)
        cropping_cube_location = location_driver.driver.variables.new()
        cropping_cube_location.name = "cropping_cube_location"
        cropping_cube_location.type = 'TRANSFORMS'
        cropping_cube_location.targets[0].id = Cropping_Cube
        cropping_cube_location.targets[0].transform_type = f'LOC_{transforms[i]}'

        ct_vol_location = location_driver.driver.variables.new()
        ct_vol_location.name = "ct_vol_location"
        ct_vol_location.type = 'TRANSFORMS'
        ct_vol_location.targets[0].id = CT_Vol
        ct_vol_location.targets[0].transform_type = f'LOC_{transforms[i]}'

        cropping_cube_dim = location_driver.driver.variables.new()
        cropping_cube_dim.name = "cropping_cube_dim"
        cropping_cube_dim.type = 'SINGLE_PROP'
        cropping_cube_dim.targets[0].id = Cropping_Cube
        cropping_cube_dim.targets[0].data_path = f"dimensions[{i}]"

        ct_vol_dim = location_driver.driver.variables.new()
        ct_vol_dim.name = "ct_vol_dim"
        ct_vol_dim.type = 'SINGLE_PROP'
        ct_vol_dim.targets[0].id = CT_Vol
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
    Surf_3D = INTACT_Props.Surf_3D
    if Surf_3D:
        material = Surf_3D.material_slots[0].material
        material.node_tree.nodes["Principled BSDF"].inputs['Roughness'].default_value = self.Surface_scan_roughness


def slice_thickness(self, context):
    """Set roughness of the surface scan material"""
    INTACT_Props = context.scene.INTACT_Props
    slices = [INTACT_Props.Axial_Slice, INTACT_Props.Coronal_Slice, INTACT_Props.Sagital_Slice]
    solidify_modifier_name = "Solidify"

    for slice in slices:
        if slice and (solidify_modifier_name in slice.modifiers):
            slice.modifiers[solidify_modifier_name].thickness = self.Slice_thickness


# class Slices_Update(bpy.types.Operator):
#     """
#     This block of code re-selects all three slices, such that they are updated. No work-around was found (yet) to make them
#     update continuously.
#     """
#     bl_idname = "intact.slices_update"
#     bl_label = "Slices Update"
#
#     def execute(self, context):
#         bpy.ops.object.select_all(action='DESELECT') #deselect all objects
#
#         for obj in bpy.data.collections['SLICES'].all_objects:
#             bpy.context.view_layer.objects.active = obj
#             bpy.ops.object.select_all(action='DESELECT') #deselect all objects
#
#         return {'FINISHED'}
    
# class Camera_Setup(bpy.types.Operator):
#     """Tooltip"""
#     bl_idname = "intact.camera_setup"
#     bl_label = "Camera Setup"
#
#     def execute(self, context):
#         INTACT_Props = context.scene.INTACT_Props
#         CT_Vol = INTACT_Props.CT_Vol
#
#         loc = CT_Vol.location
#         dim = CT_Vol.dimensions
#         maxdim = max(dim)
#
#         path = bpy.ops.curve.primitive_bezier_circle_add(radius=maxdim * 2.5, enter_editmode=False, align='WORLD', location=loc, scale=(1, 1, 1))
#         path = bpy.context.active_object
#         path.name = "Std_Path"
#         print("\nCamera path created.")
#
#         empty = bpy.ops.object.empty_add(type='CUBE', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
#         empty = bpy.context.active_object
#         empty.name = "Std_Empty"
#         bpy.context.scene.objects["Std_Empty"].scale = (maxdim / 4, maxdim / 4, maxdim /4)
#
#         cam = bpy.ops.object.camera_add(enter_editmode=False, align='VIEW', location=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1))
#         cam = bpy.context.active_object
#         cam.name = "Std_Cam"
#         bpy.context.scene.objects["Std_Cam"].scale = (0.1, 0.1, 0.1)
#         bpy.context.object.data.clip_start = 0.5
#         bpy.context.object.data.clip_end = 5000
#
#
#         #put them all in a collection
#         bpy.ops.object.select_all(action='DESELECT') #deselect all objects
#         bpy.ops.object.select_pattern(pattern="Std_*")
#         bpy.ops.object.move_to_collection(collection_index=0, is_new=True, new_collection_name='Standard Camera Path')
#
#         #parent the camera to the empty
#         cam = bpy.context.scene.objects["Std_Cam"]
#         empty = bpy.context.scene.objects["Std_Empty"]
#         cam.parent = empty
#
#         con1 = empty.constraints.new('FOLLOW_PATH')
#         con1.target = path
#         con1.use_fixed_location = False
#         con1.forward_axis = 'FORWARD_Y'
#         con1.up_axis = 'UP_Z'
#
#         con2 = cam.constraints.new('TRACK_TO')
#         con2.target = CT_Vol
#         con2.track_axis = 'TRACK_NEGATIVE_Z'
#         con2.up_axis = 'UP_Y'
#         print("\nCamera following path, and following the object created.")
#         return {'FINISHED'}
    
# class Animation_Path(bpy.types.Operator):
#     """Tooltip"""
#     bl_idname = "intact.animation_path"
#     bl_label = "Animation Path"
#
#     def execute(self, context):
#         print("\nthis still needs to be made... if. time. permits.")
#         return {'FINISHED'}
    
class Switch_Boolean_Solver(bpy.types.Operator):
    """
    This part of the script switch between "Fast" and "Exact" boolean solving. The first is, as the name suggests, not very computationally heavy,
    making the tool very interactive and quick to use. However, this is also, at times, prone to some buggy visualisations, that are (mostly) 
    circumvented when the "Fast" solver is switched on. This is recommended for renders and other output.
    """
    bl_idname = "intact.switch_boolean_solver"
    bl_label = "Switch Boolean Solver"
    
    def execute(self, context):
        INTACT_Props = context.scene.INTACT_Props
        CT_Vol = INTACT_Props.CT_Vol
        Surf_3D = INTACT_Props.Surf_3D

        if CT_Vol.modifiers["Crop X"].solver == 'FAST':
            #Select the CT scan
            bpy.ops.object.select_all(action='DESELECT') #deselect all objects    
            bpy.context.view_layer.objects.active = CT_Vol #Selects the CT Volume
            CT_Vol.select_set(True)

            CT_Vol.modifiers["Crop X"].solver = 'EXACT'
            CT_Vol.modifiers["Crop Y"].solver = 'EXACT'
            CT_Vol.modifiers["Crop Z"].solver = 'EXACT'
            
            #Select the 3D scan
            bpy.ops.object.select_all(action='DESELECT') #deselect all objects    
            bpy.context.view_layer.objects.active = Surf_3D #Selects the 3D Surface scan
            Surf_3D.select_set(True)

            Surf_3D.modifiers["Crop X"].solver = 'EXACT'
            Surf_3D.modifiers["Crop Y"].solver = 'EXACT'
            Surf_3D.modifiers["Crop Z"].solver = 'EXACT'
        
        elif CT_Vol.modifiers["Crop X"].solver == 'EXACT':
            #Select the CT scan
            bpy.ops.object.select_all(action='DESELECT') #deselect all objects    
            bpy.context.view_layer.objects.active = CT_Vol #Selects the CT Volume
            CT_Vol.select_set(True)

            CT_Vol.modifiers["Crop X"].solver = 'FAST'
            CT_Vol.modifiers["Crop Y"].solver = 'FAST'
            CT_Vol.modifiers["Crop Z"].solver = 'FAST'
            
            #Select the 3D scan
            bpy.ops.object.select_all(action='DESELECT') #deselect all objects    
            bpy.context.view_layer.objects.active = Surf_3D #Selects the 3D Surface scan
            Surf_3D.select_set(True)

            Surf_3D.modifiers["Crop X"].solver = 'FAST'
            Surf_3D.modifiers["Crop Y"].solver = 'FAST'
            Surf_3D.modifiers["Crop Z"].solver = 'FAST'
            
        else:
            print("ERROR. No boolean modifiers found. Check if you haven't renamed your CT scan and 3D-surface scan, and ensure you have gone through all prior steps.")
            
        return {'FINISHED'}
        
#---------------------------------------------------------------------------
#          Registration
#---------------------------------------------------------------------------

classes = [
    # MyProperties,
    # Init_Setup,
    # Object_Selection,
    Cropping_Cube_Creation,
    # Cropping_Cube_Boolean,
    # Slices_Boolean,
    # Cropping_Cube_Drivers,
    # Slices_Tracking2,
    # No_Slices_Tracking,
    # Slices_Update,
    # Camera_Setup,
    # Animation_Path,
    Switch_Boolean_Solver]
    #Update_Visibilities,
    # Debug_1,
    # Debug_2]#,
    #OBJECT_PT_IntACT_Panel
    #]

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