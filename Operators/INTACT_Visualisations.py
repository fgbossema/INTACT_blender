#bl_info = {
 #   "name": "CT and 3D for Cultural Heritage visualisations",
  #  "author": "Paul van Laar",
   # "version": (0, 1),
    #"blender": (2, 91, 2),
    #"location": "View3D > Sidebar > INTACT_Visualisations",
    #"descripton": "Allows for the simultaneous inspection of CT voxel data and 3D surface scans",
   # "warning": "",
    #"wiki_url": "",
    #"category": "Cultural Heritage",
#}

import bpy
from mathutils import Euler
import math

#bpy.context=bpy.context
#bpy.data=bpy.data

#---------------------------------------------------------------------------
#          Scene Properties
#---------------------------------------------------------------------------

class MyProperties(bpy.types.PropertyGroup):
    
    ct_vis : bpy.props.BoolProperty(
        name="Enable CT-scan",
        description="Enable or Disable the visibility of the CT-Scan",
        default = True
        )
    surf_vis : bpy.props.BoolProperty(
        name="Enable Surface-scan",
        description="Enable or Disable the visibility of the 3D Surface Scan",
        default = True
        )
    axi_vis : bpy.props.BoolProperty(
        name="Enable Axial Slice",
        description="Enable or Disable the visibility of the Axial Slice",
        default = False
        )
    cor_vis : bpy.props.BoolProperty(
        name="Enable Coronal Slice",
        description="Enable or Disable the visibility of the Coronal Slice",
        default = False
        )
    sag_vis : bpy.props.BoolProperty(
        name="Enable Sagital Slice",
        description="Enable or Disable the visibility of the Sagital Slice",
        default = False
        )
    seg_vis : bpy.props.BoolProperty(
        name="Enable Segmentation",
        description="Enable or Disable the visibility of the CT Segmented Mesh",
        default = False
        )
    
#---------------------------------------------------------------------------
#          Operators
#---------------------------------------------------------------------------
class Init_Setup(bpy.types.Operator):
    """
    After importing your data (using BDental and Blender) and aligning the two data-types (either manually or via ICP), click this button. 
    This function sets up the right parameters for the render and view-port.
    """
    bl_idname = "intact.init_setup"
    bl_label = "Initial Setup"
    
    def execute(self, context):
        for a in bpy.context.screen.areas:
            if a.type == 'VIEW_3D':
                for s in a.spaces:
                    if s.type == 'VIEW_3D':
                        s.clip_start = 0.5
                        s.clip_end = 5000
        print("Viewport FOV set")
        bpy.context.scene.render.engine = 'BLENDER_EEVEE'
        print("Eevee Render engine enabled")
        bpy.context.space_data.shading.type = 'MATERIAL'
        print("Material shading in Viewport enabled")
        print("Setup complete")
        return {'FINISHED'}

class Object_Selection(bpy.types.Operator):
    """
    This part of the script asks the user to define their CT voxel representation as well as their
    3D surface scan. These will be then be re-named, such that later operations and actions can be
    applied to them in the right order.

    Select the CT voxel representation first, then Shift+click the 3D scan. The CT voxel representation
    will now be the 'active' object, whereas the 3D scan is just a selected object.
    """
    bl_idname = "intact.object_selection"
    bl_label = "Object Selection"
    
    def execute(self, context):
        INTACT_Props = context.scene.INTACT_Props

        CT_Vol = INTACT_Props.CT_Vol
        Surf_3D = INTACT_Props.Surf_3D
        
        # bpy.ops.object.select_all(action='DESELECT') #deselect all objects
        # bpy.context.view_layer.objects.active = Surf_3D
        # Surf_3D.select_set(True)
        #
        # if not Surf_3D.users_collection[0].name == '3D Surface Scan':
        #     bpy.ops.object.move_to_collection(collection_index=0, is_new=True, new_collection_name='3D Surface Scan')
        # else:
        #     pass
        #
        # print("\nPlease select your CT scan first, and then Shift+click your 3D scan.")
        
        try:
            slices = bpy.data.collections['SLICES'].all_objects
            INTACT_Props.Axial_Slice = slices[0]
            INTACT_Props.Coronal_Slice = slices[1]
            INTACT_Props.Sagital_Slice = slices[2]

            # Give slices a tiny bit of thickness, so they don't give z fighting artefacts when tracked right on top of the
            # boolean faces of meshes
            # TODO - this should probably go somewhere else
            for slice in slices:
                solidify = slice.modifiers.new(type="SOLIDIFY", name="Solidify")
                solidify.thickness = 1
                solidify.offset = 0
        except:
            print("\nNo slices found. Ensure the collection in which they are kept has not changed name ('SLICES')")

        # try:
        #     Segments = bpy.data.collections['SEGMENTS'].all_objects
        #     Seg = Segments[0]
        #     try:
        #         Seg.modifier_remove(modifier="CorrectiveSmooth")
        #     except:
        #         pass
        # except:
        #     print("\nNo segment found. Ensure the collection in which it is kept has not changed name ('SEGMENTS')")

        # q1 = ''
        # q1q = str("\nIs '" + CT_Vol.name + "' your CT voxel representation, and '" + Surf_3D.name + "' your 3D Surface scan? (answer y/n)")
        #
        # while q1 == '':
        #     q1 = input(q1q)
        #     if q1 == 'y' or q1 == 'Y' or q1 == 'Yes' or q1 == 'yes':
        #         print("\nInput succesful. Move on to the next step.")
        #         break
        #     elif q1 == 'n' or q1 == 'N' or q1 == 'No' or q1 == 'no':
        #         q1 = ''
        #         print("\nUnsuccesful. Try selecting your two objects in the proper order, and click the button again. Select your CT object first, then SHIFT+Click your 3D Surface scan.")
        #         break
        #     else:
        #         q1 = ''
        #         print("\nPlease answer the question with 'y' or 'n'. Try again")
        #         continue
        #
        # print("Your CT Volume: " + str(CT_Vol.name))
        # print("Your 3D Surface Scan: " + str(Surf_3D.name))
        # try:
        #     print("Your Segmentation: " + str(Seg.name))
        # except:
        #     pass
        # try:
        #     print("Your Axial Slice: " + str(Axial_Slice.name))
        #     print("Your Coronal Slice: " + str(Coronal_Slice.name))
        #     print("Your Sagital Slice: " + str(Sagital_Slice.name))
        # except:
        #     pass
        return {'FINISHED'}
    
class Cropping_Cube_Creation(bpy.types.Operator):
    """
    This part of the script creates a node-based transparent material that can be applied to the 
    cropping cubes.
    """  
    bl_idname = "intact.cropping_cube_creation"
    bl_label = "Cropping Cube Creation"
    
    def execute(self, context):
        INTACT_Props = context.scene.INTACT_Props
        CT_Vol = INTACT_Props.CT_Vol

        # global mat
        # mat = bpy.data.materials.new(name='Transparent Material')  # Create a material.
        # print("\nEmpty material created")
        #
        # #Enable 'Use Nodes'
        # mat.use_nodes = True
        #
        # #Remove the standard Principled BSDF
        # mat.node_tree.nodes.remove(mat.node_tree.nodes.get('Principled BSDF'))
        #
        # #Define the material output
        # mat_output = mat.node_tree.nodes.get('Material Output')
        #
        # #add a transparent shader and set its location
        # transparent = mat.node_tree.nodes.new('ShaderNodeBsdfTransparent')
        # print("\nMaterial made transparent.")
        #
        # #link the translucent node to the material output
        # mat.node_tree.links.new(mat_output.inputs[0], transparent.outputs[0])
        
        """
        This part of the script creates cropping cubes in all dimensions, that will allow to cut through
        both the CT representation and the 3D surface scan, to view internal features. 
        """
        #Extracts the dimensions of the object. The dimensions of the cropping cube will be identical,
        #such that the entire object can be cropped in any dimension
        # croppingcubedim = CT_Vol.dimensions*1.002
        # croppingcubedim_2 = croppingcubedim*1.02    #The cube that crops the 3D scan has to be ever so slightly bigger to ensure the visible face shows the
                                                    #internal CT data, and not a Boolean-generated face of the 3D scan

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
        
        # global cropctx, cropcty, cropctz, crop3dx, crop3dy, crop3dz
        
        
        #Creates 3 pairs of cropping cubes. Two in each direction (x,y,z) for both the CT-Voxel representation and the 3D surface scan
        # bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(loc_x + croppingcube_x*1.02, loc_y, loc_z), scale=croppingcubedim)
        print("\nCropping cube 1 created", end = "\r")
        # cropctx = bpy.context.active_object
        # cropctx.name = "Crop CT_X"
        # if cropctx.data.materials:
        #     # assign to 1st material slot
        #     cropctx.data.materials[0] = mat
        #     cropctx.active_material.blend_method = 'BLEND'
        # else:
        #    # no slots
        #     cropctx.data.materials.append(mat)
        #     cropctx.active_material.blend_method = 'BLEND'
        #
        # bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(loc_x + croppingcube_x*1.02, loc_y, loc_z), scale=croppingcubedim_2)
        # print("\nCropping cube 2 created", end = "\r")
        # crop3dx = bpy.context.active_object
        # crop3dx.name = "Crop 3D_X"
        # if crop3dx.data.materials:
        #     # assign to 1st material slot
        #     crop3dx.data.materials[0] = mat
        #     crop3dx.active_material.blend_method = 'BLEND'
        # else:
        #    # no slots
        #     crop3dx.data.materials.append(mat)
        #     crop3dx.active_material.blend_method = 'BLEND'
        #
        # bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(loc_x, loc_y + croppingcube_y*1.02, loc_z), scale=croppingcubedim)
        # print("\nCropping cube 3 created", end = "\r")
        # cropcty = bpy.context.active_object
        # cropcty.name = "Crop CT_Y"
        # if cropcty.data.materials:
        #     # assign to 1st material slot
        #     cropcty.data.materials[0] = mat
        #     cropcty.active_material.blend_method = 'BLEND'
        # else:
        #    # no slots
        #     cropcty.data.materials.append(mat)
        #     cropcty.active_material.blend_method = 'BLEND'
        #
        # bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(loc_x, loc_y + croppingcube_y*1.02, loc_z), scale=croppingcubedim_2)
        # print("\nCropping cube 4 created", end = "\r")
        # crop3dy = bpy.context.active_object
        # crop3dy.name = "Crop 3D_Y"
        # if crop3dy.data.materials:
        #     # assign to 1st material slot
        #     crop3dy.data.materials[0] = mat
        #     crop3dy.active_material.blend_method = 'BLEND'
        # else:
        #    # no slots
        #     crop3dy.data.materials.append(mat)
        #     crop3dy.active_material.blend_method = 'BLEND'
        #
        # bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(loc_x, loc_y, loc_z + croppingcube_z*1.02), scale=croppingcubedim)
        # print("\nCropping cube 5 created", end = "\r")
        # cropctz = bpy.context.active_object
        # cropctz.name = "Crop CT_Z"
        # if cropctz.data.materials:
        #     # assign to 1st material slot
        #     cropctz.data.materials[0] = mat
        #     cropctz.active_material.blend_method = 'BLEND'
        # else:
        #    # no slots
        #     cropctz.data.materials.append(mat)
        #     cropctz.active_material.blend_method = 'BLEND'
        #
        # bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(loc_x, loc_y, loc_z + croppingcube_z*1.02), scale=croppingcubedim_2)
        # print("\nCropping cube 6 created. Done.")
        # crop3dz = bpy.context.active_object
        # bpy.context.active_object.name = "Crop 3D_Z"
        # if crop3dz.data.materials:
        #     # assign to 1st material slot
        #     crop3dz.data.materials[0] = mat
        #     crop3dz.active_material.blend_method = 'BLEND'
        # else:
        #    # no slots
        #     crop3dz.data.materials.append(mat)
        #     crop3dz.active_material.blend_method = 'BLEND'

            #Put the Cropping cubes into a collection
        # bpy.ops.object.select_all(action='DESELECT') #deselect all objects
        # bpy.ops.object.select_pattern(pattern="Crop*")
        # bpy.ops.object.move_to_collection(collection_index=0, is_new=True, new_collection_name='Cropping Cubes')
        return {'FINISHED'}
    
class Cropping_Cube_Boolean(bpy.types.Operator):
    """
    This part of the script ensures that the cropping cubes are in fact cropping the objects.
    """
    bl_idname = "intact.cropping_cube_boolean"
    bl_label = "Cropping Cube Boolean"
    
    def execute(self, context):
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

       #  #Make Boolean modifiers for CT
       #  bpy.ops.object.select_all(action='DESELECT') #deselect all objects
       #  bpy.context.view_layer.objects.active = CT_Vol #Selects the CT Volume
       #  CT_Vol.select_set(True)
       #
       #  bpy.ops.object.modifier_add(type='BOOLEAN')
       #  CT_Vol.modifiers["Boolean"].name = "Crop X"
       #  CT_Vol.modifiers["Crop X"].object = bpy.data.objects["Crop CT_X"]
       #  #CT_Vol.modifiers["Crop X"].solver = 'FAST'
       #
       #  bpy.ops.object.modifier_add(type='BOOLEAN')
       #  CT_Vol.modifiers["Boolean"].name = "Crop Y"
       #  CT_Vol.modifiers["Crop Y"].object = bpy.data.objects["Crop CT_Y"]
       #  #CT_Vol.modifiers["Crop Y"].solver = 'FAST'
       #
       #  bpy.ops.object.modifier_add(type='BOOLEAN')
       #  CT_Vol.modifiers["Boolean"].name = "Crop Z"
       #  CT_Vol.modifiers["Crop Z"].object = bpy.data.objects["Crop CT_Z"]
       #  #CT_Vol.modifiers["Crop Z"].solver = 'FAST'
       #
       #      #Make Boolean modifiers for 3D
       #  bpy.ops.object.select_all(action='DESELECT') #deselect all objects
       #  bpy.context.view_layer.objects.active = Surf_3D #Selects the 3D Surface scan
       #  Surf_3D.select_set(True)
       #
       #  bpy.ops.object.modifier_add(type='BOOLEAN')
       #  Surf_3D.modifiers["Boolean"].name = "Crop X"
       #  Surf_3D.modifiers["Crop X"].object = bpy.data.objects["Crop 3D_X"]
       # # Surf_3D.modifiers["Crop X"].solver = 'FAST'
       #
       #  bpy.ops.object.modifier_add(type='BOOLEAN')
       #  Surf_3D.modifiers["Boolean"].name = "Crop Y"
       #  Surf_3D.modifiers["Crop Y"].object = bpy.data.objects["Crop 3D_Y"]
       #  #Surf_3D.modifiers["Crop Y"].solver = 'FAST'
       #
       #  bpy.ops.object.modifier_add(type='BOOLEAN')
       #  Surf_3D.modifiers["Boolean"].name = "Crop Z"
       #  Surf_3D.modifiers["Crop Z"].object = bpy.data.objects["Crop 3D_Z"]
       #  #Surf_3D.modifiers["Crop Z"].solver = 'FAST'

        print("\nBoolean modifiers applied to both CT visualisation and 3D surface scan")
        return {'FINISHED'}

class Cropping_Cube_Drivers(bpy.types.Operator):
    """
    This part of the script links the two cropping cubes that move in the same direction to one another.
    Using Blender - drivers
    """
    bl_idname = "intact.cropping_cube_drivers"
    bl_label = "Cropping Cube Drivers"

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT') #deselect all objects
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


class Slices_Tracking(bpy.types.Operator):
    """
    These 6 blocks of code link the location and rotation of the axial slice to that of the X-cropping cube.
    """
    bl_idname = "intact.slices_tracking"
    bl_label = "Slices Tracking"
    
    def execute(self, context):
        INTACT_Props = context.scene.INTACT_Props
        Sagital_Slice = INTACT_Props.Sagital_Slice
        Coronal_Slice = INTACT_Props.Coronal_Slice
        Axial_Slice = INTACT_Props.Axial_Slice

        saglocx = Sagital_Slice.driver_add("location", 0) 
        var1 = saglocx.driver.variables.new()
        var1.name = "var1"
        var1.type = 'TRANSFORMS'
        var1.targets[0].transform_type = 'LOC_X'
        var1.targets[0].id = bpy.data.objects["Crop 3D_X"]
        x = bpy.data.objects["Crop 3D_X"].dimensions[0]
        x = 0.5 * x -1
        saglocx.driver.expression = "var1 - " + str(x)
        
        saglocy = Sagital_Slice.driver_add("location", 1) 
        var1 = saglocy.driver.variables.new()
        var1.name = "var1"
        var1.type = 'TRANSFORMS'
        var1.targets[0].transform_type = 'LOC_Y'
        var1.targets[0].id = bpy.data.objects["Crop 3D_X"]
        saglocy.driver.expression = "var1"
        
        saglocz = Sagital_Slice.driver_add("location", 2) 
        var1 = saglocz.driver.variables.new()
        var1.name = "var1"
        var1.type = 'TRANSFORMS'
        var1.targets[0].transform_type = 'LOC_Z'
        var1.targets[0].id = bpy.data.objects["Crop 3D_X"]
        saglocz.driver.expression = "var1"
        
        sagrotx = Sagital_Slice.driver_add("rotation_euler", 0) 
        var1 = sagrotx.driver.variables.new()
        var1.name = "var1"
        var1.type = 'TRANSFORMS'
        var1.targets[0].transform_type = 'ROT_X'
        var1.targets[0].id = bpy.data.objects["Crop 3D_X"]
        sagrotx.driver.expression = "var1 + 1.5708"
        
        sagroty = Sagital_Slice.driver_add("rotation_euler", 1) 
        var1 = sagroty.driver.variables.new()
        var1.name = "var1"
        var1.type = 'TRANSFORMS'
        var1.targets[0].transform_type = 'ROT_Y'
        var1.targets[0].id = bpy.data.objects["Crop 3D_X"]
        sagroty.driver.expression = "var1"
        
        sagrotz = Sagital_Slice.driver_add("rotation_euler", 2) 
        var1 = sagrotz.driver.variables.new()
        var1.name = "var1"
        var1.type = 'TRANSFORMS'
        var1.targets[0].transform_type = 'ROT_Z'
        var1.targets[0].id = bpy.data.objects["Crop 3D_X"]
        sagrotz.driver.expression = "var1 - 1.5708"    
        
        """
        These 6 blocks of code link the location and rotation of the coronal slice to that of the Y-cropping cube.
        """
        corlocx = Coronal_Slice.driver_add("location", 0) 
        var1 = corlocx.driver.variables.new()
        var1.name = "var1"
        var1.type = 'TRANSFORMS'
        var1.targets[0].transform_type = 'LOC_X'
        var1.targets[0].id = bpy.data.objects["Crop 3D_Y"]
        corlocx.driver.expression = "var1"
        
        corlocy = Coronal_Slice.driver_add("location", 1) 
        var1 = corlocy.driver.variables.new()
        var1.name = "var1"
        var1.type = 'TRANSFORMS'
        var1.targets[0].transform_type = 'LOC_Y'
        var1.targets[0].id = bpy.data.objects["Crop 3D_Y"]
        y = bpy.data.objects["Crop 3D_Y"].dimensions[1]
        y = 0.5 * y -1
        corlocy.driver.expression = "var1 - " + str(y)
        
        corlocz = Coronal_Slice.driver_add("location", 2) 
        var1 = corlocz.driver.variables.new()
        var1.name = "var1"
        var1.type = 'TRANSFORMS'
        var1.targets[0].transform_type = 'LOC_Z'
        var1.targets[0].id = bpy.data.objects["Crop 3D_Y"]
        corlocz.driver.expression = "var1"
        
        corrotx = Coronal_Slice.driver_add("rotation_euler", 0) 
        var1 = corrotx.driver.variables.new()
        var1.name = "var1"
        var1.type = 'TRANSFORMS'
        var1.targets[0].transform_type = 'ROT_X'
        var1.targets[0].id = bpy.data.objects["Crop 3D_Y"]
        corrotx.driver.expression = "var1 + 1.5708"
        
        corroty = Coronal_Slice.driver_add("rotation_euler", 1) 
        var1 = corroty.driver.variables.new()
        var1.name = "var1"
        var1.type = 'TRANSFORMS'
        var1.targets[0].transform_type = 'ROT_Y'
        var1.targets[0].id = bpy.data.objects["Crop 3D_Y"]
        corroty.driver.expression = "var1"
        
        corrotz = Coronal_Slice.driver_add("rotation_euler", 2) 
        var1 = corrotz.driver.variables.new()
        var1.name = "var1"
        var1.type = 'TRANSFORMS'
        var1.targets[0].transform_type = 'ROT_Z'
        var1.targets[0].id = bpy.data.objects["Crop 3D_Y"]
        corrotz.driver.expression = "var1"
            
        """
        These 6 blocks of code link the location and rotation of the sagital slice to that of the Z-cropping cube.
        """
        axilocx = Axial_Slice.driver_add("location", 0) 
        var1 = axilocx.driver.variables.new()
        var1.name = "var1"
        var1.type = 'TRANSFORMS'
        var1.targets[0].transform_type = 'LOC_X'
        var1.targets[0].id = bpy.data.objects["Crop 3D_Z"]
        axilocx.driver.expression = "var1"
        
        axilocy = Axial_Slice.driver_add("location", 1) 
        var1 = axilocy.driver.variables.new()
        var1.name = "var1"
        var1.type = 'TRANSFORMS'
        var1.targets[0].transform_type = 'LOC_Y'
        var1.targets[0].id = bpy.data.objects["Crop 3D_Z"]
        axilocy.driver.expression = "var1"
        
        axilocz = Axial_Slice.driver_add("location", 2) 
        var1 = axilocz.driver.variables.new()
        var1.name = "var1"
        var1.type = 'TRANSFORMS'
        var1.targets[0].transform_type = 'LOC_Z'
        var1.targets[0].id = bpy.data.objects["Crop 3D_Z"]
        z = bpy.data.objects["Crop 3D_Z"].dimensions[2]
        z = 0.5 * z -1
        axilocz.driver.expression = "var1 - " + str(z)
        
        axirotx = Axial_Slice.driver_add("rotation_euler", 0) 
        var1 = axirotx.driver.variables.new()
        var1.name = "var1"
        var1.type = 'TRANSFORMS'
        var1.targets[0].transform_type = 'ROT_X'
        var1.targets[0].id = bpy.data.objects["Crop 3D_Z"]
        axirotx.driver.expression = "var1"
        
        axiroty = Axial_Slice.driver_add("rotation_euler", 1) 
        var1 = axiroty.driver.variables.new()
        var1.name = "var1"
        var1.type = 'TRANSFORMS'
        var1.targets[0].transform_type = 'ROT_Y'
        var1.targets[0].id = bpy.data.objects["Crop 3D_Z"]
        axiroty.driver.expression = "var1"
        
        axirotz = Axial_Slice.driver_add("rotation_euler", 2) 
        var1 = axirotz.driver.variables.new()
        var1.name = "var1"
        var1.type = 'TRANSFORMS'
        var1.targets[0].transform_type = 'ROT_Z'
        var1.targets[0].id = bpy.data.objects["Crop 3D_Z"]
        axirotz.driver.expression = "var1"
        return {'FINISHED'}
        
class Slices_Tracking2(bpy.types.Operator):
    """
    These 6 blocks of code link the location and rotation of the axial slice to that of the X-cropping cube.
    """
    bl_idname = "intact.slices_tracking2"
    bl_label = "Slices Tracking"

    def calculate_slice_location(self, cropping_cube_location, cropping_cube_dim, ct_vol_location, ct_vol_dim):
        location = cropping_cube_location - (0.5 * cropping_cube_dim)
        if location < (ct_vol_location - (0.5 * ct_vol_dim)):
            location = cropping_cube_location + (0.5 * cropping_cube_dim)

        return location
    
    def execute(self, context):
        INTACT_Props = context.scene.INTACT_Props
        CT_Vol = INTACT_Props.CT_Vol
        Sagital_Slice = INTACT_Props.Sagital_Slice
        Coronal_Slice = INTACT_Props.Coronal_Slice
        Axial_Slice = INTACT_Props.Axial_Slice
        Cropping_Cube = INTACT_Props.Cropping_Cube

        transforms = ["X", "Y", "Z"]
        slices = [Sagital_Slice, Coronal_Slice, Axial_Slice]
        bpy.app.driver_namespace['calculate_slice_location'] = self.calculate_slice_location

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

            #
            # cube_dim = Cropping_Cube.dimensions[i]
            # location = Cropping_Cube.location[i] - (0.5 * cube_dim)
            # # location = Cropping_Cube.location[i] - (0.5 * cube_dim) - (max_CT_dim * 0.002)
            #
            # if location < (CT_Vol.location[i] - (0.5 * CT_Vol.dimensions[i])):
            #     location = Cropping_Cube.location[i] + (0.5 * cube_dim)
            # location_driver.driver.expression = "var1 - " + str(location)

        # saglocx = bpy.data.objects["Crop 3D_X"].driver_add("location", 0)
        # var1 = saglocx.driver.variables.new()
        # var1.name = "var1"
        # var1.type = 'TRANSFORMS'
        # var1.targets[0].transform_type = 'LOC_X'
        # var1.targets[0].id = bpy.data.objects["3_IT001_SAGITAL_SLICE"]
        # x = bpy.data.objects["Crop 3D_X"].dimensions[0]
        # x = 0.5 * x  - 2
        # saglocx.driver.expression = "var1 - " + str(x)
        #
        # saglocy = bpy.data.objects["Crop 3D_X"].driver_add("location", 1)
        # var1 = saglocy.driver.variables.new()
        # var1.name = "var1"
        # var1.type = 'TRANSFORMS'
        # var1.targets[0].transform_type = 'LOC_Y'
        # var1.targets[0].id = bpy.data.objects["3_IT001_SAGITAL_SLICE"]
        # saglocy.driver.expression = "var1"
        #
        # saglocz = bpy.data.objects["Crop 3D_X"].driver_add("location", 2)
        # var1 = saglocz.driver.variables.new()
        # var1.name = "var1"
        # var1.type = 'TRANSFORMS'
        # var1.targets[0].transform_type = 'LOC_Z'
        # var1.targets[0].id = bpy.data.objects["3_IT001_SAGITAL_SLICE"]
        # saglocz.driver.expression = "var1"
        #
        # sagrotx = bpy.data.objects["Crop 3D_X"].driver_add("rotation_euler", 0)
        # var1 = sagrotx.driver.variables.new()
        # var1.name = "var1"
        # var1.type = 'TRANSFORMS'
        # var1.targets[0].transform_type = 'ROT_X'
        # var1.targets[0].id = bpy.data.objects["3_IT001_SAGITAL_SLICE"]
        # sagrotx.driver.expression = "var1 + 1.5708"
        #
        # sagroty = bpy.data.objects["Crop 3D_X"].driver_add("rotation_euler", 1)
        # var1 = sagroty.driver.variables.new()
        # var1.name = "var1"
        # var1.type = 'TRANSFORMS'
        # var1.targets[0].transform_type = 'ROT_Y'
        # var1.targets[0].id = bpy.data.objects["3_IT001_SAGITAL_SLICE"]
        # sagroty.driver.expression = "var1"
        #
        # sagrotz = bpy.data.objects["Crop 3D_X"].driver_add("rotation_euler", 2)
        # var1 = sagrotz.driver.variables.new()
        # var1.name = "var1"
        # var1.type = 'TRANSFORMS'
        # var1.targets[0].transform_type = 'ROT_Z'
        # var1.targets[0].id = bpy.data.objects["3_IT001_SAGITAL_SLICE"]
        # sagrotz.driver.expression = "var1 - 1.5708"
        #
        # """
        # These 6 blocks of code link the location and rotation of the coronal slice to that of the Y-cropping cube.
        # """
        # corlocx = bpy.data.objects["Crop 3D_Y"].driver_add("location", 0)
        # var1 = corlocx.driver.variables.new()
        # var1.name = "var1"
        # var1.type = 'TRANSFORMS'
        # var1.targets[0].transform_type = 'LOC_X'
        # var1.targets[0].id = bpy.data.objects["2_IT001_CORONAL_SLICE"]
        # corlocx.driver.expression = "var1"
        #
        # corlocy = bpy.data.objects["Crop 3D_Y"].driver_add("location", 1)
        # var1 = corlocy.driver.variables.new()
        # var1.name = "var1"
        # var1.type = 'TRANSFORMS'
        # var1.targets[0].transform_type = 'LOC_Y'
        # var1.targets[0].id = bpy.data.objects["2_IT001_CORONAL_SLICE"]
        # y = bpy.data.objects["Crop 3D_Y"].dimensions[1]
        # y = -(0.5 * y - 2)
        # corlocy.driver.expression = "var1 -" + str(y)
        #
        # corlocz = bpy.data.objects["Crop 3D_Y"].driver_add("location", 2)
        # var1 = corlocz.driver.variables.new()
        # var1.name = "var1"
        # var1.type = 'TRANSFORMS'
        # var1.targets[0].transform_type = 'LOC_Z'
        # var1.targets[0].id = bpy.data.objects["2_IT001_CORONAL_SLICE"]
        # corlocz.driver.expression = "var1"
        #
        #
        # corrotx = bpy.data.objects["Crop 3D_Y"].driver_add("rotation_euler", 0)
        # var1 = corrotx.driver.variables.new()
        # var1.name = "var1"
        # var1.type = 'TRANSFORMS'
        # var1.targets[0].transform_type = 'ROT_X'
        # var1.targets[0].id = bpy.data.objects["2_IT001_CORONAL_SLICE"]
        # corrotx.driver.expression = "var1 + 1.5708"
        #
        # corroty = bpy.data.objects["Crop 3D_Y"].driver_add("rotation_euler", 1)
        # var1 = corroty.driver.variables.new()
        # var1.name = "var1"
        # var1.type = 'TRANSFORMS'
        # var1.targets[0].transform_type = 'ROT_Y'
        # var1.targets[0].id = bpy.data.objects["2_IT001_CORONAL_SLICE"]
        # corroty.driver.expression = "var1"
        #
        # corrotz = bpy.data.objects["Crop 3D_Y"].driver_add("rotation_euler", 2)
        # var1 = corrotz.driver.variables.new()
        # var1.name = "var1"
        # var1.type = 'TRANSFORMS'
        # var1.targets[0].transform_type = 'ROT_Z'
        # var1.targets[0].id = bpy.data.objects["2_IT001_CORONAL_SLICE"]
        # corrotz.driver.expression = "var1"
        #
        # """
        # These 6 blocks of code link the location and rotation of the sagital slice to that of the Z-cropping cube.
        # """
        # axilocx = bpy.data.objects["Crop 3D_Z"].driver_add("location", 0)
        # var1 = axilocx.driver.variables.new()
        # var1.name = "var1"
        # var1.type = 'TRANSFORMS'
        # var1.targets[0].transform_type = 'LOC_X'
        # var1.targets[0].id = bpy.data.objects["1_IT001_AXIAL_SLICE"]
        # axilocx.driver.expression = "var1"
        #
        # axilocy = bpy.data.objects["Crop 3D_Z"].driver_add("location", 1)
        # var1 = axilocy.driver.variables.new()
        # var1.name = "var1"
        # var1.type = 'TRANSFORMS'
        # var1.targets[0].transform_type = 'LOC_Y'
        # var1.targets[0].id = bpy.data.objects["1_IT001_AXIAL_SLICE"]
        # axilocy.driver.expression = "var1"
        #
        # axilocz = bpy.data.objects["Crop 3D_Z"].driver_add("location", 2)
        # var1 = axilocz.driver.variables.new()
        # var1.name = "var1"
        # var1.type = 'TRANSFORMS'
        # var1.targets[0].transform_type = 'LOC_Z'
        # var1.targets[0].id = bpy.data.objects["1_IT001_AXIAL_SLICE"]
        # z = bpy.data.objects["Crop 3D_Z"].dimensions[2]
        # z = (0.5 * z - 1)
        # axilocz.driver.expression = "var1 - " + str(z)
        #
        # axirotx = bpy.data.objects["Crop 3D_Z"].driver_add("rotation_euler", 0)
        # var1 = axirotx.driver.variables.new()
        # var1.name = "var1"
        # var1.type = 'TRANSFORMS'
        # var1.targets[0].transform_type = 'ROT_X'
        # var1.targets[0].id = bpy.data.objects["1_IT001_AXIAL_SLICE"]
        # axirotx.driver.expression = "var1"
        #
        # axiroty = bpy.data.objects["Crop 3D_Z"].driver_add("rotation_euler", 1)
        # var1 = axiroty.driver.variables.new()
        # var1.name = "var1"
        # var1.type = 'TRANSFORMS'
        # var1.targets[0].transform_type = 'ROT_Y'
        # var1.targets[0].id = bpy.data.objects["1_IT001_AXIAL_SLICE"]
        # axiroty.driver.expression = "var1"
        #
        # axirotz = bpy.data.objects["Crop 3D_Z"].driver_add("rotation_euler", 2)
        # var1 = axirotz.driver.variables.new()
        # var1.name = "var1"
        # var1.type = 'TRANSFORMS'
        # var1.targets[0].transform_type = 'ROT_Z'
        # var1.targets[0].id = bpy.data.objects["1_IT001_AXIAL_SLICE"]
        # axirotz.driver.expression = "var1"
        return {'FINISHED'}
    
class No_Slices_Tracking(bpy.types.Operator):
    """
    This block of code removes the drivers that link the slices to the cropping cubes, to save computational power"
    """
    bl_idname = "intact.no_slices_tracking"
    bl_label = "Disable Tracking Slices"
    
    def execute(self, context):
        INTACT_Props = context.scene.INTACT_Props
        x = range(3)
        for n in x:
            INTACT_Props.Axial_Slice.driver_remove("location", n)
            # INTACT_Props.Axial_Slice.driver_remove("rotation_euler", n)
            INTACT_Props.Coronal_Slice.driver_remove("location", n)
            # INTACT_Props.Coronal_Slice.driver_remove("rotation_euler", n)
            INTACT_Props.Sagital_Slice.driver_remove("location", n)
            # INTACT_Props.Sagital_Slice.driver_remove("rotation_euler", n)
        return {'FINISHED'}
    
class Slices_Update(bpy.types.Operator):
    """
    This block of code re-selects all three slices, such that they are updated. No work-around was found (yet) to make them 
    update continuously.
    """
    bl_idname = "intact.slices_update"
    bl_label = "Slices Update"
    
    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT') #deselect all objects
        
        for obj in bpy.data.collections['SLICES'].all_objects:
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.select_all(action='DESELECT') #deselect all objects 

        return {'FINISHED'}
    
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
    
# class Update_Visibilities(bpy.types.Operator):
    # bl_label = "Update Visibilities"
    # bl_idname = "intact.update_visibilities"
    
    # def execute(self, context):
        # scene = context.scene
        # mytool = scene.my_tool
        
        # CT_Vol.hide_viewport = not mytool.ct_vis
        # CT_Vol.hide_render = not mytool.ct_vis
        # Surf_3D.hide_viewport = not mytool.surf_vis
        # Surf_3D.hide_render = not mytool.surf_vis
        # Axial_Slice.hide_viewport = not mytool.axi_vis
        # Axial_Slice.hide_render = not mytool.axi_vis
        # Coronal_Slice.hide_viewport = not mytool.cor_vis
        # Coronal_Slice.hide_render = not mytool.cor_vis
        # Sagital_Slice.hide_viewport = not mytool.sag_vis
        # Sagital_Slice.hide_render = not mytool.sag_vis
        # Seg.hide_viewport = not mytool.seg_vis
        # Seg.hide_render = not mytool.seg_vis
        
        # return {'FINISHED'}

class Debug_1(bpy.types.Operator):
    """
    Use this debugger if your cropping cubes do not appear transparent, but instead take on some part of your 3D scan texture or CT-scan appearance.
    """
    bl_idname = "intact.debug_1"
    bl_label = "Debug 1: Cropping Transparency"
    
    def execute(self, context):
        mat.blend_method = 'OPAQUE'
        mat.blend_method = 'BLEND'  
        return {'FINISHED'}
    
class Debug_2(bpy.types.Operator):
    """
    Use this debugger if your cropping cubes crop in a buggy way. A slight rotation in all directions sometimes solves this problem.
    """
    bl_idname = "intact.debug_2"
    bl_label = "Debug 2: Cropping Rotation"
    
    def execute(self, context):
        unrot = Euler((0.0, 0.0, 0.0), 'XYZ')
        rot = Euler((math.radians(0.5), math.radians(0.5), math.radians(0.5)), 'XYZ')
        
        if crop3dx.rotation_euler == unrot:
            crop3dx.rotation_euler = rot
            crop3dy.rotation_euler = rot
            crop3dz.rotation_euler = rot

        else: 
            crop3dx.rotation_euler = unrot
            crop3dy.rotation_euler = unrot
            crop3dz.rotation_euler = unrot
        return {'FINISHED'}     
    
#---------------------------------------------------------------------------
#          Panel in Side UI
#---------------------------------------------------------------------------

# class OBJECT_PT_IntACT_Panel(bpy.types.Panel):
    # """Creates a Panel in the scene context of the properties editor"""
    # bl_category = "IntACT_Visualisation"
    # bl_label = "IntACT CT/3D Visualisation"
    # bl_space_type = "VIEW_3D"
    # bl_region_type = "UI"
    # bl_context = "objectmode"
    
    # def draw(self, context):
        # layout = self.layout
        # row = layout.row()
        # scene = context.scene
        # mytool = scene.my_tool
        
        # layout.label(text="Tool Setup:")
        # layout.operator("intact.init_setup")
        # layout.operator("intact.object_selection")
        # layout.operator("intact.cropping_cube_creation")
        # layout.operator("intact.cropping_cube_boolean")
        # layout.operator("intact.cropping_cube_drivers")
        
        # layout.label(text="Operators:")
        # layout.operator("intact.camera_setup")
        # layout.operator("intact.animation_path")
        # layout.operator("intact.slices_tracking2")
        # layout.operator("intact.no_slices_tracking")
        # layout.operator("intact.slices_update")
        
        # layout.label(text="Visibilities:")
        # layout.prop(mytool, "ct_vis")
        # layout.prop(mytool, "surf_vis")
        # layout.prop(mytool, "axi_vis")
        # layout.prop(mytool, "cor_vis")
        # layout.prop(mytool, "sag_vis")
        # layout.prop(mytool, "seg_vis")
        # layout.operator("intact.update_visibilities")
        
        # layout.label(text="Debugging:")
        # layout.operator("intact.switch_boolean_solver")
        # layout.operator("intact.debug_1")
        # layout.operator("intact.debug_2")
        
#---------------------------------------------------------------------------
#          Registration
#---------------------------------------------------------------------------

classes = [
    MyProperties,
    Init_Setup,
    Object_Selection,
    Cropping_Cube_Creation,
    Cropping_Cube_Boolean,
    Cropping_Cube_Drivers,
    Slices_Tracking2,
    No_Slices_Tracking,
    Slices_Update,
    Camera_Setup,
    Animation_Path,
    Switch_Boolean_Solver,
    #Update_Visibilities,
    Debug_1,
    Debug_2]#,
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