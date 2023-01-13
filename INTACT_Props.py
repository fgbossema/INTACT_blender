import bpy
from os.path import abspath

from bpy.props import (
    StringProperty,
    IntProperty,
    FloatProperty,
    EnumProperty,
    FloatVectorProperty,
    BoolProperty,
)


def TresholdUpdateFunction(self, context):
    INTACT_Props = context.scene.INTACT_Props
    GpShader = INTACT_Props.GroupNodeName
    Treshold = INTACT_Props.Treshold

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
        if GpShader == "VGS_Dakir_01":
            DcmInfo = eval(INTACT_Props.DcmInfo)
            Wmin = DcmInfo["Wmin"]
            Wmax = DcmInfo["Wmax"]
            treshramp = GpNode.nodes["TresholdRamp"].color_ramp.elements[0]
            value = (Treshold - Wmin) / (Wmax - Wmin)
            treshramp = value


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
        description="DICOM Directory Path",
        subtype="DIR_PATH",
    )
    
    UserTiffDir: StringProperty(
        name="TIFF Path",
        default="",
        description="TIFF Directory Path",
        subtype="DIR_PATH",
    )

    UserImageFile: StringProperty(
        name="User 3D Image File Path",
        default="",
        description="User Image File Path",
        subtype="FILE_PATH",
    )
    
    UserObjDir: StringProperty(
        name="OBJ Path",
        default="",
        description="OBJ Directory Path",
        subtype="FILE_PATH",
    )

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
       
    
    Treshold: IntProperty(
        name="Treshold",
        description="Volume Treshold",
        default=600,
        min=-400,
        max=3000,
        soft_min=-400,
        soft_max=3000,
        step=1,
        update=TresholdUpdateFunction,
    )
    
    # INTACT_Props = context.scene.INTACT_Props
    # DcmInfo = 
    #eval(bpy.context.scene.INTACT_Props.DcmInfo)["Wmin"]
            # Wmin = DcmInfo["Wmin"]
            # Wmax = DcmInfo["Wmax"]
            
    # INTACT_Props = context.scene.INTACT_Props
    # DcmInfo = eval(INTACT_Props.DcmInfo)
            # Wmin = DcmInfo["Wmin"]
            # Wmax = DcmInfo["Wmax"]
            
    # Treshold: FloatProperty(
        # name="Treshold",
        # description="Volume Treshold",
        # default=0.05,
        # min=0.0,
        # max= 0.07,
        # soft_min=0.0,
        # soft_max= 0.07,
        # precision = 4,
        # step=0.01,
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
        default=0,
        min=-400,
        max=3000,
        soft_min=-400,
        soft_max=3000,
        step=1,
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
    Thres1Bool: BoolProperty(description="", default=False)
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
