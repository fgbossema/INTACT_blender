from os.path import join, dirname, exists, abspath

import bpy

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
    bl_region_type = "UI" 
    bl_category = "INTACT"
    bl_label = "INTACT INFORMATION"
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
        row.label(text="A plugin designed for visualising CT scans and surface scans of cultural heritage objects.")
        
        row = box.row()
        row.alignment = "LEFT"
        row.label(text="The plugin is associated with the article by Bossema et. al.: 'Fusing 3D imaging modalities for the internal and external investigation of multi-material museum objects.'")
      
        row = box.row()
        row.alignment = "LEFT"
        row.label(text="The most current version can be found on Github. We welcome contributions via that channel.")
        
        row = box.row()
        row.alignment = "LEFT"
        row.label(text="The plugin can be used and adjusted freely, if used for an article or other publication we would appreciate if you would cite above mentioned article and Github repository.'")
      
        
        row = box.row()
        row.alignment = "LEFT"
        row.label(text="The plugin has the following submodules") 
        
        row = box.row()
        row.alignment = "LEFT"
        row.label(text="1. Loading CT data.")
        
        row = box.row()
        row.alignment = "LEFT"
        row.label(text="2. Loading surface scan data.")
        
        row = box.row()
        row.alignment = "LEFT"
        row.label(text="3. CT mesh generation.")
        
        row = box.row()
        row.alignment = "LEFT"
        row.label(text="4. Registration.")
        
        row = box.row()
        row.alignment = "LEFT"
        row.label(text="5. Interactive visualisation.")
        
        row = box.row()
        row.alignment = "LEFT"
        row.label(text="6. Images and output.")

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
        row.label(text="Niels Klop, whose plugin ICP Registration/Alignment was the base for the Registration module.")
        
        row = box.row()
        row.alignment = "LEFT"
        row.label(text="See: https://3d-operators.com/")

class INTACT_WorkingDIR(bpy.types.Panel):

    """ INTACT Workin dir"""

    bl_idname = "INTACT_PT_workingdir"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI" 
    bl_category = "INTACT"
    bl_label = "WORKING DIRECTORY"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):

        # Draw Addon UI :
        layout = self.layout
        INTACT_Props = context.scene.INTACT_Props

        row = layout.row()
        split = row.split()
        col = split.column()
        col.label(text="Project Directory :")
        col = split.column()
        col.prop(INTACT_Props, "UserProjectDir", text="")
        
class INTACT_PT_ScanPanel(bpy.types.Panel):
    """ INTACT CT load"""

    bl_idname = "INTACT_PT_ScanPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI" 
    bl_category = "INTACT"
    bl_label = "1. CT SCAN LOAD"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):

        INTACT_Props = context.scene.INTACT_Props

        # Draw Addon UI :
        layout = self.layout

          
        if not INTACT_Props.UserProjectDir:
            row = layout.row()
            row.alignment = "LEFT"
            row.label(text = "Please select working directory in INTACT panel.")
            
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
                    row = Box.row()
                    row.alignment = "CENTER"
                    row.scale_y = 2
                    row.operator("intact.volume_render", icon="IMPORT")

            if INTACT_Props.DataType == "NRRD File":

                row = layout.row()
                split = row.split()
                col = split.column()
                col.label(text="NRRD File:")
                col = split.column()
                col.prop(INTACT_Props, "UserImageFile", text="")

                if INTACT_Props.UserImageFile:

                    Box = layout.box()
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
                row.prop(INTACT_Props, "Threshold", text="THRESHOLD", slider=True)
                   


class INTACT_PT_SurfacePanel(bpy.types.Panel):
    """ INTACT Surface load"""

    bl_idname = "INTACT_PT_SurfacePanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  
    bl_category = "INTACT"
    bl_label = "2. SURFACE SCAN LOAD"
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw(self, context):

       INTACT_Props = context.scene.INTACT_Props
        # Draw Addon UI :
       layout = self.layout
       
       if not INTACT_Props.UserProjectDir:
           row = layout.row()
           row.alignment = "LEFT"
           row.label(text = "Please select working directory in INTACT panel.")
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
        
class INTACT_PT_CTmeshPanel(bpy.types.Panel):
    bl_category = "INTACT"
    bl_label = "3. CT MESH GENERATION"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        INTACT_Props = context.scene.INTACT_Props
         
        condition_CT = False

        for obj in context.scene.objects: 
            if obj.name.endswith("CTVolume"):
                condition_CT = True
                
        if condition_CT:
            row = layout.row()
            split = row.split()
            col = split.column()
            col.label(text="CT Volume:")
            col = split.column()
            col.prop(INTACT_Props, "CT_Vol", text="")
            
            row = layout.row()
            row.label(text="If the CT volume has moved, reset it's position.")
                
            row = layout.row()
            row.operator("intact.reset_ctvolume_position")
                
            row = layout.row()
            row.label(text="Determine the threshold to separate air and object.")
            row = layout.row()
            row.prop(INTACT_Props, "Threshold", text="THRESHOLD", slider=True)
                   
            layout.separator()

            row = layout.row()
            row.label(text="Choose color for segmentation, then click SEGMENTATION. ")

            row = layout.row()
            split = row.split()
            col = split.column()
            col.label(text = "Color of segmentation:")
            col = split.column()

            col.prop(INTACT_Props, "Thres1SegmentColor", text="")

            Box = layout.box()
            row = Box.row()
            row.alignment = "CENTER"
            row.scale_y = 2
            row.operator("intact.multitresh_segment")
        elif (condition_CT and not obj.name.endswith("CTVolume")): 
            row = layout.row()
            row.label(text="Please select CT volume for segmentation.")


class OBJECT_PT_ICP_panel(bpy.types.Panel):
    bl_category = "INTACT"
    bl_label = "4. REGISTRATION"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        INTACT_Props = context.scene.INTACT_Props
         
        condition_CT = False
        condition_surface = False


        for obj in context.scene.objects: 
            if obj.name.endswith("CTVolume"):
                condition_CT = True
            if obj.name.startswith("IT_surface"):
                condition_surface = True
            if obj.name.endswith("SEGMENTATION"): 
                 condition_seg = True
        if not (condition_CT or condition_surface):
            row = layout.row()
            row.label(text="Please load your data first.")
        elif (condition_surface and not condition_CT):
            row = layout.row()
            row.label(text="Please load CT scan.")
        elif (condition_CT and not condition_surface):
            row = layout.row()
            row.label(text="Please load a surface scan.")
           
        condition_segment = False

        if context.object:
            for obj in context.scene.objects: 
                if obj.name.endswith("SEGMENTATION"):
                    condition_segment = True
            if (condition_CT and condition_surface and not condition_segment):
                row = layout.row()
                row.label(text="Please select CT volume and make segmentation.")
            if (condition_CT and condition_segment and not condition_surface):
                row = layout.row()
                row.label(text="Please load a surface scan.")
            
        if (condition_surface and condition_segment):
            
            row = layout.row()
            split = row.split()
            col = split.column()
            col.label(text="Surface scan to register:")
            col = split.column()
            col.prop(INTACT_Props, "Surf_3D", text="")

            row = layout.row()
            split = row.split()
            col = split.column()
            col.label(text="CT Segmentation:")
            col = split.column()
            col.prop(INTACT_Props, "Seg", text="")
        
        
        #fine alignment panel
            layout.label(text = "ICP Alignment")
            layout.label(text = "Manually move the surface scan for a rough alignment first.")
            layout.label(text = "Check the boxes below to allow scaling of the surface scan or to use only selected vertices.")
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


class OBJECT_PT_Visualisation_Panel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_category = "INTACT"
    bl_label = "5. INTERACTIVE VISUALISATION"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        scene = context.scene

        INTACT_Props = context.scene.INTACT_Props
        
        condition_CT = False
        condition_surface = False


        for obj in context.scene.objects: 
            if obj.name.endswith("CTVolume"):
                condition_CT = True
            if obj.name.startswith("IT_surface"):
                condition_surface = True
        if not (condition_CT or condition_surface):
            row = layout.row()
            row.label(text="Please load your data first.")
            
        if (condition_CT or condition_surface):
            row = layout.row()
            split = row.split()
            col = split.column()
            col.label(text="CT Volume:")
            col = split.column()
            col.prop(INTACT_Props, "CT_Vol", text="")

            row = layout.row()
            split = row.split()
            col = split.column()
            col.label(text="Surface scan:")
            col = split.column()
            col.prop(INTACT_Props, "Surf_3D", text="")

            row = layout.row()
            split = row.split()
            col = split.column()
            col.label(text="CT Segmentation:")
            col = split.column()
            col.prop(INTACT_Props, "Seg", text="")
            
            Box = layout.box()
            row = Box.row()
            row.alignment = "CENTER"
            row.scale_y = 2
            row.operator("intact.addslices", icon="EMPTY_AXIS")
            
            row = layout.row()
            row.label(text="Slices contrast adjustment")
            row = layout.row()
            row.label(text="Slice min value:")
            row = layout.row()
            row.prop(INTACT_Props, "Slice_min", text="Minimum value", slider=True)
            row = layout.row()
            row.label(text="Slice max value:")
            row = layout.row()
            row.prop(INTACT_Props, "Slice_max", text="Maximum value", slider=True)
                

        
        if (condition_CT or condition_surface):
            layout.label(text="Make cropping cube:")
            layout.operator("intact.cropping_cube_creation", text="Create Cropping Cube")

            row = layout.row()
            row.prop(INTACT_Props, "Track_slices_to_cropping_cube", text="Track slices")
            # disable checkbox while there are no slices + no cropping cube
            row.enabled = INTACT_Props.Axial_Slice is not None and INTACT_Props.Cropping_Cube is not None

            row = layout.row()
            row.prop(INTACT_Props, "Remove_slice_outside_object", text="Crop slices outside object")
            # disable checkbox while there are no slices + no cropping cube
            row.enabled = INTACT_Props.Axial_Slice is not None and INTACT_Props.Cropping_Cube is not None
        
            row = layout.row()
            row.label(text="Open viewing in multiple directions.")
            row = layout.row()
            row.operator("intact.multiview")

            row = layout.row()
            row.label(text="Display settings:")
            layout.prop(INTACT_Props, "Surface_scan_roughness", text="Surface scan roughness")
            layout.prop(INTACT_Props, "Slice_thickness", text="Slice thickness")

        
class OBJECT_PT_Image_Panel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_category = "INTACT"
    bl_label = "6. IMAGES AND OUTPUT"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        scene = context.scene
        INTACT_Props = context.scene.INTACT_Props
        
        condition_CT = False
        condition_surface = False


        for obj in context.scene.objects: 
            if obj.name.endswith("CTVolume"):
                condition_CT = True
            if obj.name.startswith("IT_surface"):
                 condition_surface = True
        if not (condition_CT and condition_surface):
            row = layout.row()
            row.label(text="Please load your data first.")
            
        if (condition_CT or condition_surface):
            row = layout.row()
            row.label(text="Quick screenshot:")
            layout.operator("intact.take_screenshot", text="Take Screenshot")
            
            row = layout.row()
            row.label(text="Camera setup:")
            layout.prop(INTACT_Props, "Resolution_x", text="Resolution x (pixels)")
            layout.prop(INTACT_Props, "Resolution_y", text="Resolution y (pixels)")
           
            if not INTACT_Props.Set_camera_enabled:
                icon = "PLAY"
                txt = 'Set Camera Position'
            else:
                icon = "PAUSE"
                txt = 'Confirm Camera Position'
            
            layout.prop(INTACT_Props, 'Set_camera_enabled', text=txt, icon=icon, toggle=True)
            
            row = layout.row()
            row.label(text="Render options:")
            layout.prop(INTACT_Props, 'Lighting_strength', text="Lighting strength")
            layout.prop(INTACT_Props, 'Background_colour', text="Background colour")
            row = layout.row()
            row.label(text="Render image/movie:")
            layout.operator("intact.render_image", text="Render image")
            row = layout.row()
            split = row.split()
            col = split.column()
            col.label(text="Movie filename:")
            col = split.column()
            col.prop(INTACT_Props, "Movie_filename", text="")
            row = layout.row(align=True)
            row.label(text="Axis")
            row.prop_enum(INTACT_Props, "Movie_rotation_axis", "X")
            row.prop_enum(INTACT_Props, "Movie_rotation_axis", "Y")
            row.prop_enum(INTACT_Props, "Movie_rotation_axis", "Z")
            layout.operator("intact.render_turntable", text="Render turntable movie")
        
        
#################################################################################################
# Registration :
#################################################################################################

classes = [
    INTACT_PT_MainPanel,
    INTACT_WorkingDIR,
    INTACT_PT_ScanPanel,
    INTACT_PT_SurfacePanel,
    INTACT_PT_CTmeshPanel,
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
    