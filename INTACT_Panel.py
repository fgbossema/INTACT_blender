import bpy, os, sys
from os.path import join, dirname, exists, abspath

import bpy
import numpy as np
import math as mt
import mathutils as mu
import copy
import os
import blf
from bpy_extras import view3d_utils

ADDON_DIR = dirname(abspath(__file__))
Addon_Version_Path = join(ADDON_DIR, "Resources", "INTACT_Version.txt")
if exists(Addon_Version_Path):
    with open(Addon_Version_Path, "r") as rf:
        lines = rf.readlines()
        Addon_Version_Date = lines[0].split(";")[0]
else:
    Addon_Version_Date = "  "
# Selected icons :
red_icon = "COLORSET_01_VEC"
orange_icon = "COLORSET_02_VEC"
green_icon = "COLORSET_03_VEC"
blue_icon = "COLORSET_04_VEC"
violet_icon = "COLORSET_06_VEC"
yellow_icon = "COLORSET_09_VEC"
yellow_point = "KEYTYPE_KEYFRAME_VEC"
blue_point = "KEYTYPE_BREAKDOWN_VEC"


class INTACT_PT_MainPanel(bpy.types.Panel):
    """ INTACT Main Panel"""

    bl_idname = "INTACT_PT_MainPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # blender 2.7 and lower = TOOLS
    bl_category = "INTACT"
    bl_label = "INTACT"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):

        # Draw Addon UI :
        layout = self.layout
        INTACT_Props = context.scene.INTACT_Props

        box = layout.box()

        row = box.row()
        row.alert = True
        row.alignment = "CENTER"
        row.label(text=f"WINDOWS VERSION : {Addon_Version_Date}")
        
        row = box.row()
        row.alignment = "LEFT"
        row.label(text="Description of plugin:")
        
        row = box.row()
        row.alignment = "LEFT"
        row.label(text="A plugin designed for visualising CT scans and 3D visualisations of cultural heritage objects.")
        
        row = box.row()
        row.alignment = "LEFT"
        row.label(text="The plugin has the following submodules") 
        
        row = box.row()
        row.alignment = "LEFT"
        row.label(text="1. Loading of CT and surface scan data.")
        
        row = box.row()
        row.alignment = "LEFT"
        row.label(text="2. CT mesh generation and Registration of two data modalities.")
        
        row = box.row()
        row.alignment = "LEFT"
        row.label(text="3. Interactive visualisation.")
        
        row = box.row()
        row.alignment = "LEFT"
        row.label(text="4. Images and output.")

        row = box.row()
        row.alignment = "LEFT"
        row.label(text="Designed and developed by Paul van Laar, Francien Bossema & Kimberly Meechan.")
        
        row = box.row()
        row.alignment = "LEFT"
        row.label(text="ACKNOWLEDGEMENTS")
        
        row = box.row()
        row.alignment = "LEFT"
        row.label(text="Issam Dakir, whose plugin BDENTAL served as the base for this plugin.")

        row = box.row()
        row.alignment = "LEFT"
        row.label(text="See: https://github.com/issamdakir/BDENTAL ")
        
        row = box.row()
        row.alignment = "LEFT"
        row.label(text="Niels Klop, whose plugins ICP Registration/Alignment and Distance Map are incorporated in the Registration module.")
        
        row = box.row()
        row.alignment = "LEFT"
        row.label(text="See: https://3d-operators.com/")

        row = layout.row()
        split = row.split()
        col = split.column()
        col.label(text="Project Directory :")
        col = split.column()
        col.prop(INTACT_Props, "UserProjectDir", text="")
        
        row = layout.row()
        split = row.split()
        col = split.column()
        col.label(text="Optional: use a theme with light background.")
        col = split.column()
        col.operator("intact.template", text="INTACT THEME")


class INTACT_PT_ScanPanel(bpy.types.Panel):
    """ INTACT Scan Panel"""

    bl_idname = "INTACT_PT_ScanPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # blender 2.7 and lower = TOOLS
    bl_category = "INTACT"
    bl_label = "CT SCAN LOAD"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):

        INTACT_Props = context.scene.INTACT_Props
        GroupNodeName = INTACT_Props.GroupNodeName
        VGS = bpy.data.node_groups.get(GroupNodeName)

        # Draw Addon UI :
        layout = self.layout

          
        if not INTACT_Props.UserProjectDir:
            row = layout.row()
            row.alignment = "LEFT"
            row.label(text = "Please select working directory in INTACT panel")
            
        if INTACT_Props.UserProjectDir:

            row = layout.row()
            split = row.split()
            col = split.column()
            col.label(text="Scan Data Type :")
            col = split.column()
            col.prop(INTACT_Props, "DataType", text="")
            
            if INTACT_Props.DataType == "TIFF Stack":

                row = layout.row()
                split = row.split()
                col = split.column()
                col.label(text="TIFF Directory :")
                col = split.column()
                col.prop(INTACT_Props, "UserTiffDir", text="")
                
                #input for resolution
                row = layout.row()
                split = row.split()
                col = split.column()
                col.label(text="Resolution (voxel size in mm) :")
                col = split.column()                
                col.prop(INTACT_Props, "Resolution", text = "")

                if INTACT_Props.UserTiffDir:
                    Box = layout.box()
                    # Box.alert = True
                    row = Box.row()
                    row.alignment = "CENTER"
                    row.scale_y = 2
                    row.operator("intact.volume_render", icon="IMPORT")
                    
            if INTACT_Props.DataType == "DICOM Series":

                row = layout.row()
                split = row.split()
                col = split.column()
                col.label(text="DICOM Directory :")
                col = split.column()
                col.prop(INTACT_Props, "UserDcmDir", text="")

                if INTACT_Props.UserDcmDir:

                    Box = layout.box()
                    # Box.alert = True
                    row = Box.row()
                    row.alignment = "CENTER"
                    row.scale_y = 2
                    row.operator("intact.volume_render", icon="IMPORT")

            if INTACT_Props.DataType == "3D Image File":

                row = layout.row()
                split = row.split()
                col = split.column()
                col.label(text="3D Image File :")
                col = split.column()
                col.prop(INTACT_Props, "UserImageFile", text="")

                if INTACT_Props.UserImageFile:

                    Box = layout.box()
                    # Box.alert = True
                    row = Box.row()
                    row.alignment = "CENTER"
                    row.scale_y = 2
                    row.operator("intact.volume_render", icon="IMPORT")

        if context.object:
            if context.object.name.startswith("IT") and context.object.name.endswith(
                "CTVolume"
            ):
                row = layout.row()
                split = row.split()
                col = split.column()
                col.label(text = "Color of volume render:")
                col = split.column()
                col.prop(INTACT_Props, "CTcolor", text="")
                
                row = layout.row()
                split = row.split()
                col = split.column()
                col.label(text = "Shading of volume render:")
                col = split.column()
                col.prop(INTACT_Props, "ColorPos", text="", slider=True)
                
                row = layout.row()
                row.label(text=f"Threshold:")
                row = layout.row()
                row.prop(INTACT_Props, "Thres1Treshold", text="THRESHOLD", slider=True)
                   
                # layout.separator()

                # row = layout.row()
                # row.label(text="Segments :")

                # Box = layout.box()
                # row = Box.row()
                # #row.prop(INTACT_Props, "Thres1Treshold", text="Threshold 1")
                # row.prop(INTACT_Props, "Thres1SegmentColor", text="")
                # #row.prop(INTACT_Props, "Thres1Bool", text="")
                # # row = Box.row()
                # # row.prop(INTACT_Props, "Thres2Treshold", text="Threshold 2")
                # # row.prop(INTACT_Props, "Thres2SegmentColor", text="")
                # # row.prop(INTACT_Props, "Thres2Bool", text="")

                # # row = Box.row()
                # # row.prop(INTACT_Props, "Thres3Treshold", text="Threshold 3")
                # # row.prop(INTACT_Props, "Thres3SegmentColor", text="")
                # # row.prop(INTACT_Props, "Thres3Bool", text="")

                # Box = layout.box()
                # row = Box.row()
                # row.operator("intact.multitresh_segment")
                


class INTACT_PT_SurfacePanel(bpy.types.Panel):
    """ INTACT Scan Panel"""

    bl_idname = "INTACT_PT_SurfacePanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # blender 2.7 and lower = TOOLS
    bl_category = "INTACT"
    bl_label = "SURFACE SCAN LOAD"
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw(self, context):

       INTACT_Props = context.scene.INTACT_Props
       GroupNodeName = INTACT_Props.GroupNodeName
       VGS = bpy.data.node_groups.get(GroupNodeName)
        # Draw Addon UI :
       layout = self.layout
       
       if not INTACT_Props.UserProjectDir:
           row = layout.row()
           row.alignment = "LEFT"
           row.label(text = "Please select working directory in INTACT panel")
       else: 
           row = layout.row()
           split = row.split()
           col = split.column()
           col.label(text="Surface scan directory (.obj file) :")
           col = split.column()
           col.prop(INTACT_Props, "UserObjDir", text="")
        
       if INTACT_Props.UserObjDir:
           Box = layout.box()
           row = Box.row()
           row.alignment = "CENTER"
           row.scale_y = 2
           row.operator("intact.obj_render", icon="IMPORT")
        
        

class INTACT_PT_Measurements(bpy.types.Panel):
    """ INTACT_FULL Scan Panel"""

    bl_idname = "INTACT_PT_Measurements"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # blender 2.7 and lower = TOOLS
    bl_category = "INTACT"
    bl_label = "MEASUREMENTS"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        Box = layout.box()
        row = Box.row()
        row.operator("intact.add_markup_point")
        row.operator("intact.add_reference_planes")
        row = Box.row()
        row.operator("intact.ctvolume_orientation")


class INTACT_PT_MeshesTools_Panel(bpy.types.Panel):
    """ INTACT Meshes Tools Panel"""

    bl_idname = "INTACT_PT_MeshesTools_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # blender 2.7 and lower = TOOLS
    bl_category = "INTACT"
    bl_label = "MESH TOOLS"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        INTACT_Props = context.scene.INTACT_Props
        layout = self.layout

        # Join / Link ops :

        row = layout.row()
        row.label(text="PARENT / JOIN :")
        row = layout.row()
        row.operator("intact.parent_object", text="Parent", icon="LINKED")
        row.operator(
            "intact.unparent_objects", text="Un-Parent", icon="LIBRARY_DATA_OVERRIDE"
        )
        row.operator("intact.join_objects", text="Join", icon="SNAP_FACE")
        row.operator("intact.separate_objects", text="Separate", icon="SNAP_VERTEX")

        # Align Tools :
        layout.row().separator()
        row = layout.row()
        row.label(text="Align Tools")
        row = layout.row()
        row.operator("intact.align_to_front", text="ALIGN FRONT", icon="AXIS_FRONT")
        row.operator("intact.to_center", text="TO CENTER", icon="SNAP_FACE_CENTER")
        row.operator("intact.center_cursor", text="Center Cursor", icon="PIVOT_CURSOR")

        split = layout.split(factor=2 / 3, align=False)
        col = split.column()
        row = col.row()
        row.operator("intact.occlusalplane", text="OCCLUSAL PLANE")
        col = split.column()
        row = col.row()
        row.alert = True
        row.operator("intact.occlusalplaneinfo", text="INFO", icon="INFO")

        # Model Repair Tools :
        layout.row().separator()
        row = layout.row()
        row.label(text="REPAIR TOOLS", icon=yellow_point)

        split = layout.split(factor=2 / 3, align=False)
        col = split.column()

        row = col.row(align=True)
        row.operator("intact.decimate", text="DECIMATE", icon="MOD_DECIM")
        row.prop(INTACT_Props, "decimate_ratio", text="")
        row = col.row()
        row.operator("intact.fill", text="FILL", icon="OUTLINER_OB_LIGHTPROBE")
        row.operator("intact.retopo_smooth", text="RETOPO SMOOTH", icon="BRUSH_SMOOTH")
        try:
            ActiveObject = bpy.context.view_layer.objects.active
            if ActiveObject:
                if ActiveObject.mode == "SCULPT":
                    row.operator(
                        "sculpt.sample_detail_size", text="", icon="EYEDROPPER"
                    )
        except Exception:
            pass

        col = split.column()
        row = col.row()
        # row.scale_y = 2
        row.operator("intact.clean_mesh", text="CLEAN MESH", icon="BRUSH_DATA")
        row = col.row()
        row.operator("intact.voxelremesh")

        # Cutting Tools :
        layout.row().separator()
        row = layout.row()
        row.label(text="Cutting Tools :", icon=yellow_point)
        row = layout.row()
        row.prop(INTACT_Props, "Cutting_Tools_Types_Prop", text="")
        if INTACT_Props.Cutting_Tools_Types_Prop == "Curve Cutter 1":
            row = layout.row()
            row.operator("intact.curvecutteradd", icon="GP_SELECT_STROKES")
            row.operator("intact.curvecuttercut", icon="GP_MULTIFRAME_EDITING")

        elif INTACT_Props.Cutting_Tools_Types_Prop == "Curve Cutter 2":
            row = layout.row()
            row.operator("intact.curvecutteradd2", icon="GP_SELECT_STROKES")
            row.operator("intact.curvecutter2_shortpath", icon="GP_MULTIFRAME_EDITING")

        elif INTACT_Props.Cutting_Tools_Types_Prop == "Square Cutting Tool":

            # Cutting mode column :
            row = layout.row()
            row.label(text="Select Cutting Mode :")
            row.prop(INTACT_Props, "cutting_mode", text="")

            row = layout.row()
            row.operator("intact.square_cut")
            row.operator("intact.square_cut_confirm")
            row.operator("intact.square_cut_exit")

        elif INTACT_Props.Cutting_Tools_Types_Prop == "Paint Cutter":

            row = layout.row()
            row.operator("intact.paintarea_toggle")
            row.operator("intact.paintarea_plus", text="", icon="ADD")
            row.operator("intact.paintarea_minus", text="", icon="REMOVE")
            row = layout.row()
            row.operator("intact.paint_cut")

class OBJECT_PT_ICP_panel(bpy.types.Panel):
    #bl_category = "INTACT_Registration"
    bl_category = "INTACT"
    bl_label = "REGISTRATION"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        INTACT_Props = context.scene.INTACT_Props
        GroupNodeName = INTACT_Props.GroupNodeName
        VGS = bpy.data.node_groups.get(GroupNodeName)
        
        if not context.object:
            row = layout.row()
            row.label(text = "Please load your data first.")
           
        
        if context.object:
            if context.object.name.endswith("CTVolume"):
                row = layout.row()
                row.label(text="If the CT volume has moved, reset it's position.")
                
                row = layout.row()
                row.operator("intact.reset_ctvolume_position")
                
                row = layout.row()
                row.label(text="Determine the threshold to separate air and object.")
                row = layout.row()
                row.prop(INTACT_Props, "Thres1Treshold", text="THRESHOLD", slider=True)
                   
                layout.separator()

                row = layout.row()
                row.label(text="Choose color for segmentation, then click SEGMENTATION. ")

                row = layout.row()
                split = row.split()
                col = split.column()
                col.label(text = "Color of segmentation:")
                col = split.column()
                #row.prop(INTACT_Props, "Thres1Treshold", text="Threshold 1")
                col.prop(INTACT_Props, "Thres1SegmentColor", text="")
                
                
                
                #row.prop(INTACT_Props, "Thres1Bool", text="")
                # row = Box.row()
                # row.prop(INTACT_Props, "Thres2Treshold", text="Threshold 2")
                # row.prop(INTACT_Props, "Thres2SegmentColor", text="")
                # row.prop(INTACT_Props, "Thres2Bool", text="")

                # row = Box.row()
                # row.prop(INTACT_Props, "Thres3Treshold", text="Threshold 3")
                # row.prop(INTACT_Props, "Thres3SegmentColor", text="")
                # row.prop(INTACT_Props, "Thres3Bool", text="")

                Box = layout.box()
                row = Box.row()
                row.alignment = "CENTER"
                row.scale_y = 2
                row.operator("intact.multitresh_segment")


        
        condition1 = False
        condition2 = False

        if context.object:
            for obj in context.scene.objects: 
                if obj.name.endswith("SEGMENTATION"):
                    condition1 = True
                if obj.name.startswith("IT_surface"):
                    condition2 = True
            if not condition1:
                row = layout.row()
                row.label(text="Please select CT volume to create a segmentation first.")
            if not condition2:
                row = layout.row()
                row.label(text="Please load a surface scan.")
            
        # row = layout.row()
        # row.alignment = "RIGHT"
        # row.scale_x = 2
        # row.operator("object.icpreadme", text = "", icon = "QUESTION")
        if (condition1 and condition2):
        #rough alignment panel
            layout.label(text = "Initial Alignment")
            layout.label(text = "Either manually move the surface scan for a rough alignment or place landmarks on each object (CT first, press enter to confirm) and align.")
            layout.prop(context.scene, "allowScaling", text = "Allow Scaling")
            layout.operator("object.placelandmarks")
            layout.operator("object.deletelandmarks")
            Box = layout.box()
            row = Box.row()
            row.alignment = "CENTER"
            row.scale_y = 2
            row.operator("object.initialalignment")
              
            layout.separator()
        
        #fine alignment panel
            layout.label(text = "ICP Alignment")
            layout.prop(context.scene, "allowScaling", text = "Allow Scaling")
            layout.prop(context.scene, "vertexSelect", text = "Use Vertex Selections")
            layout.prop(context.scene, "iterations", text = "Iterations")
            layout.prop(context.scene, "outlierPerc", text = "Outlier %")
            layout.prop(context.scene, "downsamplingPerc", text = "Downsampling %")
            Box = layout.box()
            row = Box.row()
            row.alignment = "CENTER"
            row.scale_y = 2
            row.operator("object.icp")
        
        #transformations panel
            layout.separator()
            layout.label(text = "Transformations export and import")
            layout.prop(context.scene, "exportTransformation", text = "")
            layout.operator("object.icpexport")
            layout.operator("object.icpset")

class OBJECT_PT_Visualisation_Panel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_category = "INTACT"
    bl_label = "VISUALISATION"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        scene = context.scene

        INTACT_Props = context.scene.INTACT_Props
        GroupNodeName = INTACT_Props.GroupNodeName
        VGS = bpy.data.node_groups.get(GroupNodeName)
        
        if not context.object:
            row = layout.row()
            row.label(text = "Please load your data first.")
        
        else:
            if not (context.object.name.startswith("IT") and context.object.name.endswith(
                ("CTVolume"))):
                row = layout.row()
                row.label(text = "Please select CT volume, to generate slices.")
            else:
                row = layout.row()
                row.operator("intact.addslices", icon="EMPTY_AXIS")
        
        if context.object:
            layout.label(text="Tool Setup:")
            layout.operator("intact.init_setup")
            layout.operator("intact.object_selection")
            layout.operator("intact.cropping_cube_creation")
            layout.operator("intact.cropping_cube_boolean")
            layout.operator("intact.cropping_cube_drivers")
            layout.operator("intact.slices_tracking2")
            layout.operator("intact.no_slices_tracking")
        
            row = layout.row()
            row.label(text = "Open viewing in multiple directions.")
            row = layout.row()
            row.operator("intact.multiview")
            layout.operator("intact.slices_tracking2")
            layout.operator("intact.no_slices_tracking")

        
            layout.label(text="Debugging:")
            layout.operator("intact.switch_boolean_solver")
            layout.operator("intact.debug_1")
            layout.operator("intact.debug_2")
        
class OBJECT_PT_Image_Panel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_category = "INTACT"
    bl_label = "IMAGES AND OUTPUT"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        scene = context.scene
        #mytool = scene.my_tool
        INTACT_Props = context.scene.INTACT_Props
        GroupNodeName = INTACT_Props.GroupNodeName
        VGS = bpy.data.node_groups.get(GroupNodeName)
        
        if not context.object:
            row = layout.row()
            row.label(text = "Please load your data first.")
        else:
            layout.label(text="Operators:")
            layout.operator("intact.camera_setup")
            layout.operator("intact.animation_path")
        
        
#################################################################################################
# Registration :
#################################################################################################

classes = [
    INTACT_PT_MainPanel,
    INTACT_PT_ScanPanel,
    INTACT_PT_SurfacePanel,
    #INTACT_PT_MeshesTools_Panel,
    OBJECT_PT_ICP_panel,
    OBJECT_PT_Visualisation_Panel,
    OBJECT_PT_Image_Panel
    ]


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
        
    #export transformations panel
    bpy.types.Scene.exportTransformation = bpy.props.EnumProperty(
        name = "Export Transformation",
        items = [("combined", "Combined Transformation", "Export the combined initial and ICP transformation"),
            ("roughAlignment", "Initial Transformation", "Export only the initial transformation"),
            ("fineAlignment", "ICP Transformation", "Export only the ICP transformation")])
    

def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    