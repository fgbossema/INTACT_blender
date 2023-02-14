import bpy
from mathutils import Euler
import math

#---------------------------------------------------------------------------
#          Scene Properties
#---------------------------------------------------------------------------

# class MyProperties(bpy.types.PropertyGroup):
#
#     ct_vis : bpy.props.BoolProperty(
#         name="Enable CT-scan",
#         description="Enable or Disable the visibility of the CT-Scan",
#         default = True
#         )
#     surf_vis : bpy.props.BoolProperty(
#         name="Enable Surface-scan",
#         description="Enable or Disable the visibility of the 3D Surface Scan",
#         default = True
#         )
#     axi_vis : bpy.props.BoolProperty(
#         name="Enable Axial Slice",
#         description="Enable or Disable the visibility of the Axial Slice",
#         default = False
#         )
#     cor_vis : bpy.props.BoolProperty(
#         name="Enable Coronal Slice",
#         description="Enable or Disable the visibility of the Coronal Slice",
#         default = False
#         )
#     sag_vis : bpy.props.BoolProperty(
#         name="Enable Sagital Slice",
#         description="Enable or Disable the visibility of the Sagital Slice",
#         default = False
#         )
#     seg_vis : bpy.props.BoolProperty(
#         name="Enable Segmentation",
#         description="Enable or Disable the visibility of the CT Segmented Mesh",
#         default = False
#         )
    
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
    """
    This part of the script creates a cropping cubes for all dimensions, that will allow to cut through
    both the CT representation and the 3D surface scan, to view internal features.
    """
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
        bpy.ops.object.move_to_collection(collection_index=0, is_new=True, new_collection_name='Cropping Cubes')

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
    boolean_modifier_name = "3D scan"

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
        if boolean_modifier_name not in slice.modifiers:
            slice_bool = slice.modifiers.new(type="BOOLEAN", name=boolean_modifier_name)
            slice_bool.operation = 'INTERSECT'
            slice_bool.object = surf_copy
            # Move to top of modifier stack
            bpy.ops.object.modifier_move_to_index({'object':slice}, modifier=slice_bool.name, index=0)
        else:
            modifier = slice.modifiers.get(boolean_modifier_name)
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
        modifier = slice.modifiers.get("3D scan")
        modifier.show_viewport = False
        modifier.show_render = False

    print("\nBoolean modifiers disabled on all slices")


def boolean_slice(self, context):
    if self.Remove_slice_outside_surface:
        enable_boolean_slice(context)
    else:
        disable_boolean_slice(context)

# class Cropping_Cube_Drivers(bpy.types.Operator):
#     """
#     This part of the script links the two cropping cubes that move in the same direction to one another.
#     Using Blender - drivers
#     """
#     bl_idname = "intact.cropping_cube_drivers"
#     bl_label = "Cropping Cube Drivers"
#
#     def execute(self, context):
#         bpy.ops.object.select_all(action='DESELECT') #deselect all objects
#
#         #Create the drivers for the X-direction cropping cubes
#         bpy.context.view_layer.objects.active = cropctx
#         xlocx = cropctx.driver_add("location", 0)
#         var1 = xlocx.driver.variables.new()
#         var1.name = "var1"
#         var1.type = 'TRANSFORMS'
#         var1.targets[0].transform_type = 'LOC_X'
#         var1.targets[0].id = bpy.data.objects["Crop 3D_X"]
#         xlocx.driver.expression = "var1"
#
#         xlocy = cropctx.driver_add("location", 1)
#         var2 = xlocy.driver.variables.new()
#         var2.name = "var2"
#         var2.type = 'TRANSFORMS'
#         var2.targets[0].transform_type = 'LOC_Y'
#         var2.targets[0].id = bpy.data.objects["Crop 3D_X"]
#         xlocy.driver.expression = "var2"
#
#         xlocz = cropctx.driver_add("location", 2)
#         var3 = xlocz.driver.variables.new()
#         var3.name = "var3"
#         var3.type = 'TRANSFORMS'
#         var3.targets[0].transform_type = 'LOC_Z'
#         var3.targets[0].id = bpy.data.objects["Crop 3D_X"]
#         xlocz.driver.expression = "var3"
#
#         xrotx = cropctx.driver_add("rotation_euler", 0)
#         var4 = xrotx.driver.variables.new()
#         var4.name = "var4"
#         var4.type = 'TRANSFORMS'
#         var4.targets[0].transform_type = 'ROT_X'
#         var4.targets[0].id = bpy.data.objects["Crop 3D_X"]
#         xrotx.driver.expression = "var4"
#
#         xroty = cropctx.driver_add("rotation_euler", 1)
#         var5 = xroty.driver.variables.new()
#         var5.name = "var5"
#         var5.type = 'TRANSFORMS'
#         var5.targets[0].transform_type = 'ROT_Y'
#         var5.targets[0].id = bpy.data.objects["Crop 3D_X"]
#         xroty.driver.expression = "var5"
#
#         xrotz = cropctx.driver_add("rotation_euler", 2)
#         var6 = xrotz.driver.variables.new()
#         var6.name = "var6"
#         var6.type = 'TRANSFORMS'
#         var6.targets[0].transform_type = 'ROT_Z'
#         var6.targets[0].id = bpy.data.objects["Crop 3D_X"]
#         xrotz.driver.expression = "var6"
#
#         #Do the same for the Y direction cropping cube
#         bpy.context.view_layer.objects.active = cropcty
#         ylocx = cropcty.driver_add("location", 0)
#         var1 = ylocx.driver.variables.new()
#         var1.name = "var1"
#         var1.type = 'TRANSFORMS'
#         var1.targets[0].transform_type = 'LOC_X'
#         var1.targets[0].id = bpy.data.objects["Crop 3D_Y"]
#         ylocx.driver.expression = "var1"
#
#         ylocy = cropcty.driver_add("location", 1)
#         var2 = ylocy.driver.variables.new()
#         var2.name = "var2"
#         var2.type = 'TRANSFORMS'
#         var2.targets[0].transform_type = 'LOC_Y'
#         var2.targets[0].id = bpy.data.objects["Crop 3D_Y"]
#         ylocy.driver.expression = "var2"
#
#         ylocz = cropcty.driver_add("location", 2)
#         var3 = ylocz.driver.variables.new()
#         var3.name = "var3"
#         var3.type = 'TRANSFORMS'
#         var3.targets[0].transform_type = 'LOC_Z'
#         var3.targets[0].id = bpy.data.objects["Crop 3D_Y"]
#         ylocz.driver.expression = "var3"
#
#         yrotx = cropcty.driver_add("rotation_euler", 0)
#         var4 = yrotx.driver.variables.new()
#         var4.name = "var4"
#         var4.type = 'TRANSFORMS'
#         var4.targets[0].transform_type = 'ROT_X'
#         var4.targets[0].id = bpy.data.objects["Crop 3D_Y"]
#         yrotx.driver.expression = "var4"
#
#         yroty = cropcty.driver_add("rotation_euler", 1)
#         var5 = yroty.driver.variables.new()
#         var5.name = "var5"
#         var5.type = 'TRANSFORMS'
#         var5.targets[0].transform_type = 'ROT_Y'
#         var5.targets[0].id = bpy.data.objects["Crop 3D_Y"]
#         yroty.driver.expression = "var5"
#
#         yrotz = cropcty.driver_add("rotation_euler", 2)
#         var6 = yrotz.driver.variables.new()
#         var6.name = "var6"
#         var6.type = 'TRANSFORMS'
#         var6.targets[0].transform_type = 'ROT_Z'
#         var6.targets[0].id = bpy.data.objects["Crop 3D_Y"]
#         yrotz.driver.expression = "var6"
#
#         #Do the same for the Z direction cropping cube
#         bpy.context.view_layer.objects.active = cropctz
#         zlocx = cropctz.driver_add("location", 0)
#         var1 = zlocx.driver.variables.new()
#         var1.name = "var1"
#         var1.type = 'TRANSFORMS'
#         var1.targets[0].transform_type = 'LOC_X'
#         var1.targets[0].id = bpy.data.objects["Crop 3D_Z"]
#         zlocx.driver.expression = "var1"
#
#         zlocy = cropctz.driver_add("location", 1)
#         var2 = zlocy.driver.variables.new()
#         var2.name = "var2"
#         var2.type = 'TRANSFORMS'
#         var2.targets[0].transform_type = 'LOC_Y'
#         var2.targets[0].id = bpy.data.objects["Crop 3D_Z"]
#         zlocy.driver.expression = "var2"
#
#         zlocz = cropctz.driver_add("location", 2)
#         var3 = zlocz.driver.variables.new()
#         var3.name = "var3"
#         var3.type = 'TRANSFORMS'
#         var3.targets[0].transform_type = 'LOC_Z'
#         var3.targets[0].id = bpy.data.objects["Crop 3D_Z"]
#         zlocz.driver.expression = "var3"
#
#         zrotx = cropctz.driver_add("rotation_euler", 0)
#         var4 = zrotx.driver.variables.new()
#         var4.name = "var4"
#         var4.type = 'TRANSFORMS'
#         var4.targets[0].transform_type = 'ROT_X'
#         var4.targets[0].id = bpy.data.objects["Crop 3D_Z"]
#         zrotx.driver.expression = "var4"
#
#         zroty = cropctz.driver_add("rotation_euler", 1)
#         var5 = zroty.driver.variables.new()
#         var5.name = "var5"
#         var5.type = 'TRANSFORMS'
#         var5.targets[0].transform_type = 'ROT_Y'
#         var5.targets[0].id = bpy.data.objects["Crop 3D_Z"]
#         zroty.driver.expression = "var5"
#
#         zrotz = cropctz.driver_add("rotation_euler", 2)
#         var6 = zrotz.driver.variables.new()
#         var6.name = "var6"
#         var6.type = 'TRANSFORMS'
#         var6.targets[0].transform_type = 'ROT_Z'
#         var6.targets[0].id = bpy.data.objects["Crop 3D_Z"]
#         zrotz.driver.expression = "var6"
#
#         print("\nTranslation and Rotation of cropping cube pairs are linked.")
#         return {'FINISHED'}


def calculate_slice_location(cropping_cube_location, cropping_cube_dim, ct_vol_location, ct_vol_dim):
    location = cropping_cube_location - (0.5 * cropping_cube_dim)
    if location < (ct_vol_location - (0.5 * ct_vol_dim)):
        location = cropping_cube_location + (0.5 * cropping_cube_dim)

    return location


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
    bpy.app.driver_namespace['calculate_slice_location'] = calculate_slice_location

    for i in range(0, len(transforms)):
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

    # Give slices a tiny bit of thickness, so they don't give z fighting artefacts when tracked right on top of the
    # boolean faces of meshes
    for slice in slices:
        solidify = slice.modifiers.new(type="SOLIDIFY", name="Solidify")
        solidify.thickness = 1
        solidify.offset = 0

    return {'FINISHED'}


def disable_track_slices_to_cropping_cube(context):
    """
    This block of code removes the drivers that link the slices to the cropping cubes, to save computational power"
    """
    INTACT_Props = context.scene.INTACT_Props
    slices = [INTACT_Props.Sagital_Slice, INTACT_Props.Coronal_Slice, INTACT_Props.Axial_Slice]

    for i in range(0, len(slices)):
        slices[i].driver_remove("location", i)
    return {'FINISHED'}


def track_slices(self, context):
    if self.Track_slices_to_cropping_cube:
        enable_track_slices_to_cropping_cube(context)
    else:
        disable_track_slices_to_cropping_cube(context)


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
    
class Camera_Setup(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "intact.camera_setup"
    bl_label = "Camera Setup"
    
    def execute(self, context):
        INTACT_Props = context.scene.INTACT_Props
        CT_Vol = INTACT_Props.CT_Vol

        loc = CT_Vol.location
        dim = CT_Vol.dimensions
        maxdim = max(dim)
        
        path = bpy.ops.curve.primitive_bezier_circle_add(radius=maxdim * 2.5, enter_editmode=False, align='WORLD', location=loc, scale=(1, 1, 1))
        path = bpy.context.active_object
        path.name = "Std_Path"
        print("\nCamera path created.")
        
        empty = bpy.ops.object.empty_add(type='CUBE', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        empty = bpy.context.active_object
        empty.name = "Std_Empty"
        bpy.context.scene.objects["Std_Empty"].scale = (maxdim / 4, maxdim / 4, maxdim /4)
        
        cam = bpy.ops.object.camera_add(enter_editmode=False, align='VIEW', location=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1))
        cam = bpy.context.active_object
        cam.name = "Std_Cam"
        bpy.context.scene.objects["Std_Cam"].scale = (0.1, 0.1, 0.1)
        bpy.context.object.data.clip_start = 0.5
        bpy.context.object.data.clip_end = 5000
        
        
        #put them all in a collection
        bpy.ops.object.select_all(action='DESELECT') #deselect all objects
        bpy.ops.object.select_pattern(pattern="Std_*")
        bpy.ops.object.move_to_collection(collection_index=0, is_new=True, new_collection_name='Standard Camera Path')
        
        #parent the camera to the empty
        cam = bpy.context.scene.objects["Std_Cam"]
        empty = bpy.context.scene.objects["Std_Empty"]
        cam.parent = empty
        
        con1 = empty.constraints.new('FOLLOW_PATH')
        con1.target = path
        con1.use_fixed_location = False
        con1.forward_axis = 'FORWARD_Y'
        con1.up_axis = 'UP_Z'
        
        con2 = cam.constraints.new('TRACK_TO')
        con2.target = CT_Vol
        con2.track_axis = 'TRACK_NEGATIVE_Z' 
        con2.up_axis = 'UP_Y'
        print("\nCamera following path, and following the object created.") 
        return {'FINISHED'}
    
class Animation_Path(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "intact.animation_path"
    bl_label = "Animation Path"
    
    def execute(self, context):
        print("\nthis still needs to be made... if. time. permits.")
        return {'FINISHED'}            
    
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
    Camera_Setup,
    Animation_Path,
    Switch_Boolean_Solver]
    #Update_Visibilities,
    # Debug_1,
    # Debug_2]#,
    #OBJECT_PT_IntACT_Panel
    #]
            
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
        #bpy.types.Scene.my_tool = bpy.props.PointerProperty(type= MyProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
        #del bpy.types.Scene.my_tool
  
if __name__ == "__main__":
    register()