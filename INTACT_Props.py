import bpy
import os
from .Operators import INTACT_Visualisations
from .Operators import INTACT_Images
from mathutils import Matrix, Vector, Euler, kdtree

from bpy.props import (
    StringProperty,
    IntProperty,
    FloatProperty,
    EnumProperty,
    FloatVectorProperty,
    BoolProperty,
    PointerProperty
)

def ColorUpdateFunction(self, context):
    INTACT_Props = context.scene.INTACT_Props
    GpShader = INTACT_Props.GroupNodeName
    Treshold = INTACT_Props.Thres1Treshold
    CtVolumeList = [
        obj
        for obj in bpy.context.scene.objects
        if obj.name.startswith("IT") and obj.name.endswith("_CTVolume")
    ]
    if context.object in CtVolumeList:
        Vol = context.object
        Preffix = Vol.name[:5]
        GpNode = bpy.data.node_groups.get(f"{Preffix}_{GpShader}")
        
        if GpShader == "VGS_INTACT":
            GpNode.nodes["ColorPresetRamp"].color_ramp.elements[1].color = INTACT_Props.CTcolor

def ShaderUpdateFunction(self, context):
    INTACT_Props = context.scene.INTACT_Props
    GpShader = INTACT_Props.GroupNodeName
    Treshold = INTACT_Props.Thres1Treshold
    CtVolumeList = [
        obj
        for obj in bpy.context.scene.objects
        if obj.name.startswith("IT") and obj.name.endswith("_CTVolume")
    ]
    if context.object in CtVolumeList:
        Vol = context.object
        Preffix = Vol.name[:5]
        GpNode = bpy.data.node_groups.get(f"{Preffix}_{GpShader}")
        
        if GpShader == "VGS_INTACT":
            GpNode.nodes["ColorPresetRamp"].color_ramp.elements[1].position = INTACT_Props.ColorPos



def TresholdUpdateFunction(self, context):
    INTACT_Props = context.scene.INTACT_Props
    GpShader = INTACT_Props.GroupNodeName
    Treshold = INTACT_Props.Thres1Treshold
    CtVolumeList = [
        obj
        for obj in bpy.context.scene.objects
        if obj.name.startswith("IT") and obj.name.endswith("_CTVolume")
    ]
    if context.object in CtVolumeList:
        Vol = context.object
        Preffix = Vol.name[:5]
        GpNode = bpy.data.node_groups.get(f"{Preffix}_{GpShader}")

        if GpShader == "VGS_Marcos_modified":
            Low_Treshold = GpNode.nodes["Low_Treshold"].outputs[0]
            Low_Treshold.default_value = Treshold
            
            GpNode.nodes["ColorPresetRamp"].color_ramp.elements[4].color = INTACT_Props.CTcolor

            
        if GpShader == "VGS_INTACT":
            Low_Treshold = GpNode.nodes["Low_Treshold"].outputs[0]
            Low_Treshold.default_value = Treshold



def text_body_update(self, context):
    props = context.scene.ODC_modops_props
    if context.object:
        ob = context.object
        if ob.type == "FONT":
            mode = ob.mode
            bpy.ops.object.mode_set(mode="OBJECT")
            ob.data.body = props.text_body_prop

            # Check font options and apply them if toggled :
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.font.select_all()

            dict_font_options = {
                "BOLD": props.bold_toggle_prop,
                "ITALIC": props.italic_toggle_prop,
                "UNDERLINE": props.underline_toggle_prop,
            }
            for key, value in dict_font_options.items():
                if value == True:
                    bpy.ops.font.style_toggle(style=key)

            ob.name = ob.data.body
            bpy.ops.object.mode_set(mode=mode)


def text_bold_toggle(self, context):
    if context.object:
        ob = context.object
        if ob.type == "FONT":
            mode = ob.mode
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.font.select_all()
            bpy.ops.font.style_toggle(style="BOLD")
            bpy.ops.object.mode_set(mode=mode)


def text_italic_toggle(self, context):
    if context.object:
        ob = context.object
        if ob.type == "FONT":
            mode = ob.mode
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.font.select_all()
            bpy.ops.font.style_toggle(style="ITALIC")
            bpy.ops.object.mode_set(mode=mode)


def text_underline_toggle(self, context):
    if context.object:
        ob = context.object
        if ob.type == "FONT":
            mode = ob.mode
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.font.select_all()
            bpy.ops.font.style_toggle(style="UNDERLINE")
            bpy.ops.object.mode_set(mode=mode)


def make_path_absolute(key):
    """ Prevent Blender's relative paths """
    props = bpy.context.scene.INTACT_Props
    sane_path = lambda p: os.path.abspath(bpy.path.abspath(p))
    if key in props and props[key].startswith('//'):
        props[key] = sane_path(props[key]) 


class INTACT_Props(bpy.types.PropertyGroup):

    #####################
    #############################################################################################
    # CT_Scan props :
    #############################################################################################
    #####################

    UserProjectDir: StringProperty(
        name="Project Directory Path",
        default="",
        description="Project Directory Path",
        subtype="DIR_PATH",
    )

    #####################

    UserDcmDir: StringProperty(
        name="DICOM Path",
        default="",
        update = lambda s,c: make_path_absolute('UserDcmDir'),
        description="DICOM Directory Path",
        subtype="DIR_PATH",
    )
    
    UserTiffDir: StringProperty(
        name="TIFF Path",
        default="",
        update = lambda s,c: make_path_absolute('UserTiffDir'),
        description="TIFF Directory Path",
        subtype="DIR_PATH",
    )

    UserImageFile: StringProperty(
        name="User 3D Image File Path",
        default="",
        update = lambda s,c: make_path_absolute('UserImageFile'),
        description="User Image File Path",
        subtype="FILE_PATH",
    )
    
    UserObjDir: StringProperty(
        name="OBJ Path",
        update = lambda s,c: make_path_absolute('UserObjDir'),
        default="",
        description="OBJ Directory Path",
        subtype="FILE_PATH",
    )
    
    # my_filepath: StringProperty(
        # name = 'Absolute filepath',
        # update = lambda s,c: make_path_absolute('my_filepath'),
        # subtype = 'FILE_PATH')
    #####################

    Data_Types = ["TIFF Stack", "DICOM Series", "3D Image File", ""]
    items = []
    for i in range(len(Data_Types)):
        item = (str(Data_Types[i]), str(Data_Types[i]), str(""), int(i))
        items.append(item)

    DataType: EnumProperty(items=items, description="Data type", default="TIFF Stack")

    #######################

    DcmInfo: StringProperty(
        name="(str) DicomInfo",
        default="{'Deffault': None}",
        description="Dicom series files list",
    )
    
    TiffInfo: StringProperty(
        name="(str) TiffInfo",
        default="{'Deffault': None}",
        description="Tiff stack files list",
    )
    #######################

    PngDir: StringProperty(
        name="Png Directory",
        default="",
        description=" PNG files Sequence Directory Path",
    )
    #######################

    SlicesDir: StringProperty(
        name="Slices Directory",
        default="",
        description="Slices PNG files Directory Path",
    )
    #######################

    NrrdHuPath: StringProperty(
        name="NrrdHuPath",
        default="",
        description="Nrrd image3D file Path",
    )
    Nrrd255Path: StringProperty(
        name="Nrrd255Path",
        default="",
        description="Nrrd image3D file Path",
    )

    #######################

    IcpVidDict: StringProperty(
        name="IcpVidDict",
        default="None",
        description="ICP Vertices Pairs str(Dict)",
    )
    #######################

    Wmin: IntProperty()
    Wmax: IntProperty()
    
    Resolution: FloatProperty(
        name="Resolution",
        default=1.0,
        description="Voxel resolution in mm",
        precision = 4)

    #######################
    # Thres1TissueMode = BoolProperty(description="Thres1Tissue Mode ", default=False)

    GroupNodeName: StringProperty(
        name="Group shader Name",
        default="",
        description="Group shader Name",
    )
    ####################### Intact_vis props
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

    #######################
       
    
    # Treshold: IntProperty(
        # name="Treshold",
        # description="Volume Treshold",
        # default=600,
        # min=-400,
        # max=3000,
        # soft_min=-400,
        # soft_max=3000,
        # step=1,
        # update=TresholdUpdateFunction,
    # )
    
    
    Progress_Bar: FloatProperty(
        name="Progress_Bar",
        description="Progress_Bar",
        subtype="PERCENTAGE",
        default=0.0,
        min=0.0,
        max=100.0,
        soft_min=0.0,
        soft_max=100.0,
        step=1,
        precision=1,
    )

    
    Thres1Treshold: IntProperty(
        name="Threshold 1",
        description="Threshold 1",
        default = 600,
        step=1,
        min=-400,
        max=3000,
        soft_min=-400,
        soft_max=3000,
        update=TresholdUpdateFunction,
    )
    
    Thres2Treshold: IntProperty(
        name="Threshold 2",
        description="Threshold 2",
        default=100,
        min=-400,
        max=3000,
        soft_min=-400,
        soft_max=3000,
        step=1,
    )
    Thres3Treshold: IntProperty(
        name="Threshold 3",
        description="Threshold 3",
        default=200,
        min=-400,
        max=3000,
        soft_min=-400,
        soft_max=3000,
        step=1,
    )
    Thres1Bool: BoolProperty(description="", default=True)
    Thres2Bool: BoolProperty(description="", default=False)
    Thres3Bool: BoolProperty(description="", default=False)

    Thres1SegmentColor: FloatVectorProperty(
        name="Segmentation Color 1",
        description="Color 1",
        default=[0.07, 0.75, 0.8, 1.0],  # [0.63, 0.37, 0.30, 1.0]
        soft_min=0.0,
        soft_max=1.0,
        size=4,
        subtype="COLOR",
    )
    Thres2SegmentColor: FloatVectorProperty(
        name="Segmentation Color 2",
        description="Color 2",
        default=[0.44, 0.4, 0.5, 1.0],  # (0.8, 0.46, 0.4, 1.0),
        soft_min=0.0,
        soft_max=1.0,
        size=4,
        subtype="COLOR",
    )
    Thres3SegmentColor: FloatVectorProperty(
        name="Segmentation Color 3",
        description="Color 3",
        default=[0.55, 0.645, 0.67, 1.000000],  # (0.8, 0.46, 0.4, 1.0),
        soft_min=0.0,
        soft_max=1.0,
        size=4,
        subtype="COLOR",
    )
    
    CTcolor: FloatVectorProperty(
        name="CT volume render color",
        description="Choose a color for the volume render.",
        default=[0.799, 0.448, 0.058, 1.000000],  # (0.8, 0.46, 0.4, 1.0),
        soft_min=0.0,
        soft_max=1.0,
        size=4,
        subtype="COLOR",
        update = ColorUpdateFunction,
    )
    
    ColorPos: FloatProperty(
        default=0.25,
        min=0.0,
        max=10.0,
        soft_min=0.0,
        soft_max=1.0,
        update = ShaderUpdateFunction,
    )

    #######################

    CT_Loaded: BoolProperty(description="CT loaded ", default=False)
    CT_Rendered: BoolProperty(description="CT Rendered ", default=False)
    sceneUpdate: BoolProperty(description="scene update ", default=True)
    AlignModalState: BoolProperty(description="Align Modal state ", default=False)

    #######################

    #########################################################################################
    # Mesh Tools Props :
    #########################################################################################

    # Decimate ratio prop :
    #######################
    decimate_ratio: FloatProperty(
        description="Enter decimate ratio ", default=0.5, step=1, precision=2
    )
    #########################################################################################

    CurveCutterNameProp: StringProperty(
        name="Cutter Name",
        default="",
        description="Current Cutter Object Name",
    )

    #####################

    CuttingTargetNameProp: StringProperty(
        name="Cutting Target Name",
        default="",
        description="Current Cutting Target Object Name",
    )

    #####################

    Cutting_Tools_Types = [
        "Curve Cutter 1",
        "Curve Cutter 2",
        "Square Cutting Tool",
        "Paint Cutter",
    ]
    items = []
    for i in range(len(Cutting_Tools_Types)):
        item = (
            str(Cutting_Tools_Types[i]),
            str(Cutting_Tools_Types[i]),
            str(""),
            int(i),
        )
        items.append(item)

    Cutting_Tools_Types_Prop: EnumProperty(
        items=items, description="Select a cutting tool", default="Curve Cutter 1"
    )

    cutting_mode_list = ["Cut inner", "Keep inner"]
    items = []
    for i in range(len(cutting_mode_list)):
        item = (str(cutting_mode_list[i]), str(cutting_mode_list[i]), str(""), int(i))
        items.append(item)

    cutting_mode: EnumProperty(items=items, description="", default="Cut inner")

    #########################################################################################
    # Visualisation Props :
    #########################################################################################
    CT_Vol: PointerProperty(
        name="CT_Vol",
        type=bpy.types.Object)

    Surf_3D: PointerProperty(
        name="Surf_3D",
        type=bpy.types.Object)

    Seg: PointerProperty(
        name="Seg",
        type=bpy.types.Object)

    Axial_Slice: PointerProperty(
        name="Seg",
        type=bpy.types.Object)

    Coronal_Slice: PointerProperty(
        name="Seg",
        type=bpy.types.Object)

    Sagital_Slice: PointerProperty(
        name="Seg",
        type=bpy.types.Object)

    Cropping_Cube: PointerProperty(
        name="Cropping_Cube",
        type=bpy.types.Object)

    Axial_Slice_Pos: FloatVectorProperty(
        name='', size=3, subtype="TRANSLATION")

    Coronal_Slice_Pos: FloatVectorProperty(
        name='', size=3, subtype="TRANSLATION")

    Sagital_Slice_Pos: FloatVectorProperty(
        name='', size=3, subtype="TRANSLATION")

    Axial_Slice_Rot: FloatVectorProperty(
        name='', size=3, subtype="EULER")

    Coronal_Slice_Rot: FloatVectorProperty(
        name='', size=3, subtype="EULER")

    Sagital_Slice_Rot: FloatVectorProperty(
        name='', size=3, subtype="EULER")

    Track_slices_to_cropping_cube: BoolProperty(
        name='', update=INTACT_Visualisations.track_slices)

    Remove_slice_outside_surface: BoolProperty(
        name='', update=INTACT_Visualisations.boolean_slice)

    Surface_scan_roughness: FloatProperty(
        name='', soft_min=0.0, soft_max=1.0, default=0.0, precision=1,
        update=INTACT_Visualisations.surface_scan_roughness)

    Slice_thickness: FloatProperty(
        name='', soft_min=0.0, default=1.0, precision=2,
        update=INTACT_Visualisations.slice_thickness)

    Resolution_x: IntProperty(
        name='', soft_min=500, soft_max=4000, default=1920, step=10, update=INTACT_Images.update_render_resolution)

    Resolution_y: IntProperty(
        name='', soft_min=500, soft_max=4000, default=1080, step=10, update=INTACT_Images.update_render_resolution)

    Set_camera_enabled: BoolProperty(name='', default=False, update=INTACT_Images.set_camera_position)

    Lighting_strength: FloatProperty(name='', default=1.0, soft_min=0.1, precision=1)

    Background_colour: FloatVectorProperty(name='', subtype="COLOR", size=4,
                                           min=0.0, max=1.0, default=[0.0, 0.0, 0.0, 1.0])

    Movie_rotation_axis: EnumProperty(items=(("X", ) * 3, ("Y",) * 3, ("Z",) * 3),
                                      description="Rotation axis for turntable", default="Z")

    Movie_filename: StringProperty(name='', default='movie-')


#################################################################################################
# Registration :
#################################################################################################

classes = [
    INTACT_Props,
]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.INTACT_Props = bpy.props.PointerProperty(type=INTACT_Props)


def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.INTACT_Props


# props examples :

# Axial_Loc: FloatVectorProperty(
#     name="AXIAL location",
#     description="AXIAL location",
#     subtype="TRANSLATION",
#     update=AxialSliceUpdate,
# )
# Axial_Rot: FloatVectorProperty(
#     name="AXIAL Rotation",
#     description="AXIAL Rotation",
#     subtype="EULER",
#     update=AxialSliceUpdate,
# )
################################################
# Str_Prop_Search_1: StringProperty(
#     name="String Search Property 1",
#     default="",
#     description="Str_Prop_Search_1",
# )
# Float Props :
#########################################################################################

# F_Prop_1: FloatProperty(
#     description="Float Property 1 ",
#     default=0.0,
#     min=-200.0,
#     max=200.0,
#     step=1,
#     precision=1,
#     unit="NONE",
#     update=None,
#     get=None,
#     set=None,
# )
#########################################################################################
# # FloatVector Props :
#     ##############################################
#     FloatV_Prop_1: FloatVectorProperty(
#         name="FloatVectorProperty 1", description="FloatVectorProperty 1", size=3
#     )
#########################################################################################
