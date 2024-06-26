import bpy
import os
from .Operators import INTACT_Visualisation
from .Operators import INTACT_ImagesOutput
from .Operators import INTACT_Utils

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
    GpNode = bpy.data.node_groups.get(GpShader)
    GpNode.nodes["ColorPresetRamp"].color_ramp.elements[1].color = INTACT_Props.CTcolor


def ShaderUpdateFunction(self, context):
    INTACT_Props = context.scene.INTACT_Props
    GpShader = INTACT_Props.GroupNodeName
    GpNode = bpy.data.node_groups.get(GpShader)
    GpNode.nodes["ColorPresetRamp"].color_ramp.elements[1].position = INTACT_Props.ColorPos


def TresholdUpdateFunction(self, context):
    INTACT_Props = context.scene.INTACT_Props
    GpShader = INTACT_Props.ThresholdGroupNodeName
    Threshold = INTACT_Props.Threshold
    GpNode = bpy.data.node_groups.get(GpShader)
    Low_Treshold = GpNode.nodes["Low_Treshold"].outputs[0]
    Low_Treshold.default_value = Threshold


def SliceIntensityUpdate(self, scene):
    INTACT_Utils.SlicesUpdateAll(scene)


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
                if value:
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


class ImageInfo(bpy.types.PropertyGroup):
    """Group of properties representing metadata of a loaded image"""

    name: bpy.props.StringProperty(
        name="name",
        description="Name used to access this image - equal to the Prefix",
        default=""
    )

    UserProjectDir: bpy.props.StringProperty(
        name="User project directory",
        description="User project directory",
        default=""
    )

    Prefix: bpy.props.StringProperty(
        name="Prefix",
        description="Filename prefix",
        default=""
    )

    RenderSz: bpy.props.IntVectorProperty(
        name="Render Size",
        description="Render Size",
        default=(0, 0, 0),
        min=0,
        size=3
    )

    RenderSp: bpy.props.FloatVectorProperty(
        name="Render Spacing",
        description="Render Spacing",
        default=(1.0, 1.0, 1.0),
        min=0.0,
        size=3
    )

    PixelType: bpy.props.StringProperty(
        name="Pixel type",
        description="Pixel type",
        default=""
    )

    Wmin: bpy.props.FloatProperty(
        name="W min",
        description="W min",
        default=0.0
    )

    Wmax: bpy.props.FloatProperty(
        name="W max",
        description="W max",
        default=0.0
    )

    Size: bpy.props.IntVectorProperty(
        name="Size",
        description="Size",
        default=(0, 0, 0),
        min=0,
        size=3
    )

    Dims: bpy.props.IntProperty(
        name="Number of dimensions",
        description="Number of dimensions",
        default=3
    )

    Spacing: bpy.props.FloatVectorProperty(
        name="Spacing",
        description="Image Spacing (i.e. resolution)",
        default=(1.0, 1.0, 1.0),
        min=0.0,
        size=3
    )

    Origin: bpy.props.FloatVectorProperty(
        name="Origin",
        description="Image origin",
        default=(0.0, 0.0, 0.0),
        size=3
    )

    Direction: bpy.props.FloatVectorProperty(
        name="Direction",
        description="Image direction",
        default=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        size=9
    )

    TransformMatrix: bpy.props.FloatVectorProperty(
        name="Transform Matrix",
        description="Transform Matrix",
        default=(0.0, 0.0, 0.0, 0.0,
                 0.0, 0.0, 0.0, 0.0,
                 0.0, 0.0, 0.0, 0.0,
                 0.0, 0.0, 0.0, 0.0),
        size=16,
        subtype="MATRIX"
    )

    DirectionMatrix_4x4: bpy.props.FloatVectorProperty(
        name="Direction Matrix 4x4",
        description="Direction Matrix 4x4",
        default=(0.0, 0.0, 0.0, 0.0,
                 0.0, 0.0, 0.0, 0.0,
                 0.0, 0.0, 0.0, 0.0,
                 0.0, 0.0, 0.0, 0.0),
        size=16,
        subtype="MATRIX"
    )

    TransMatrix_4x4: bpy.props.FloatVectorProperty(
        name="Trans Matrix 4x4",
        description="Trans Matrix 4x4",
        default=(0.0, 0.0, 0.0, 0.0,
                 0.0, 0.0, 0.0, 0.0,
                 0.0, 0.0, 0.0, 0.0,
                 0.0, 0.0, 0.0, 0.0),
        size=16,
        subtype="MATRIX"
    )

    VtkTransform_4x4: bpy.props.FloatVectorProperty(
        name="Vtk Transform 4x4",
        description="Vtk Transform 4x4",
        default=(0.0, 0.0, 0.0, 0.0,
                 0.0, 0.0, 0.0, 0.0,
                 0.0, 0.0, 0.0, 0.0,
                 0.0, 0.0, 0.0, 0.0),
        size=16,
        subtype="MATRIX"
    )

    VolumeCenter: bpy.props.FloatVectorProperty(
        name="Volume Center",
        description="Volume Center",
        default=(0.0, 0.0, 0.0),
        size=3
    )

    SlicesDir: bpy.props.StringProperty(
        name="Slices directory",
        description="Slices directory",
        default=""
    )

    Nrrd255Path: bpy.props.StringProperty(
        name="Nrrd 255 Path",
        description="Nrrd 255 Path",
        default=""
    )

    CT_Loaded: bpy.props.BoolProperty(
        name="CT data loaded",
        description="CT data loaded",
        default=False
    )


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
        update=lambda s, c: make_path_absolute('UserDcmDir'),
        description="DICOM Directory Path",
        subtype="DIR_PATH",
    )

    UserTiffDir: StringProperty(
        name="TIFF Path",
        default="",
        update=lambda s, c: make_path_absolute('UserTiffDir'),
        description="TIFF Directory Path",
        subtype="DIR_PATH",
    )

    UserImageFile: StringProperty(
        name="User 3D Image File Path",
        default="",
        update=lambda s, c: make_path_absolute('UserImageFile'),
        description="User Image File Path",
        subtype="FILE_PATH",
    )

    UserObjDir: StringProperty(
        name="OBJ Path",
        update=lambda s, c: make_path_absolute('UserObjDir'),
        default="",
        description="OBJ Directory Path",
        subtype="FILE_PATH",
    )

    CT_ID: IntProperty(
        name="CT ID",
        description="ID of this CT stack - used in the filename prefix",
        default=0,
        min=0
    )

    #####################

    Data_Types = ["TIFF Stack", "DICOM Series", "NRRD File", ""]
    items = []
    for i in range(len(Data_Types)):
        item = (str(Data_Types[i]), str(Data_Types[i]), str(""), int(i))
        items.append(item)

    DataType: EnumProperty(items=items, description="Data type", default="TIFF Stack")

    #######################

    Images: bpy.props.CollectionProperty(
        type=ImageInfo,
        name="Images",
        description="Metadata of currently loaded images",
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

    Wmin: FloatProperty()
    Wmax: FloatProperty()

    Slice_min: FloatProperty(
        name="Slice min",
        description="Choose a minimum for slice visualisation.",
        default=0,
        soft_min=0.0,
        soft_max=255.0,
        update=SliceIntensityUpdate,
    )
    Slice_max: FloatProperty(
        name="Slice min",
        description="Choose a minimum for slice visualisation.",
        default=255,
        soft_min=0.0,
        soft_max=255.0,
        update=SliceIntensityUpdate,
    )

    Resolution: FloatProperty(
        name="Resolution",
        default=1.0,
        description="Voxel resolution in mm",
        precision=4)

    #######################

    GroupNodeName: StringProperty(
        name="Group shader Name",
        default="",
        description="Group shader Name",
    )
    ThresholdGroupNodeName: StringProperty(
        name="Threshold node group Name",
        default="",
        description="Threshold node group Name",
    )

    # Intact_vis props
    ct_vis: bpy.props.BoolProperty(
        name="Enable CT-scan",
        description="Enable or Disable the visibility of the CT-Scan",
        default=True
        )
    surf_vis: bpy.props.BoolProperty(
        name="Enable Surface-scan",
        description="Enable or Disable the visibility of the 3D Surface Scan",
        default=True
        )
    axi_vis: bpy.props.BoolProperty(
        name="Enable Axial Slice",
        description="Enable or Disable the visibility of the Axial Slice",
        default=False
        )
    cor_vis: bpy.props.BoolProperty(
        name="Enable Coronal Slice",
        description="Enable or Disable the visibility of the Coronal Slice",
        default=False
        )
    sag_vis: bpy.props.BoolProperty(
        name="Enable Sagital Slice",
        description="Enable or Disable the visibility of the Sagital Slice",
        default=False
        )
    seg_vis: bpy.props.BoolProperty(
        name="Enable Segmentation",
        description="Enable or Disable the visibility of the CT Segmented Mesh",
        default=False
        )

    #######################

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

    Threshold: FloatProperty(
        name="Threshold 1",
        description="Threshold 1",
        default=100.0,
        min=0.0,
        max=255.0,
        soft_min=0.0,
        soft_max=255.0,
        update=TresholdUpdateFunction,
    )

    Thres1Bool: BoolProperty(description="", default=True)

    Thres1SegmentColor: FloatVectorProperty(
        name="Segmentation Color 1",
        description="Color 1",
        default=[0.07, 0.75, 0.8, 1.0],
        soft_min=0.0,
        soft_max=1.0,
        size=4,
        subtype="COLOR",
    )

    CTcolor: FloatVectorProperty(
        name="CT volume render color",
        description="Choose a color for the volume render.",
        default=[0.799, 0.448, 0.058, 1.000000],
        soft_min=0.0,
        soft_max=1.0,
        size=4,
        subtype="COLOR",
        update=ColorUpdateFunction,
    )

    ColorPos: FloatProperty(
        default=0.25,
        min=0.0,
        max=10.0,
        soft_min=0.0,
        soft_max=1.0,
        update=ShaderUpdateFunction,
    )

    #######################

    CT_Loaded: BoolProperty(description="CT loaded ", default=False)
    CT_Rendered: BoolProperty(description="CT Rendered ", default=False)
    sceneUpdate: BoolProperty(description="scene update ", default=True)
    AlignModalState: BoolProperty(description="Align Modal state ", default=False)

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
        name='', update=INTACT_Visualisation.track_slices)

    Remove_slice_outside_object: BoolProperty(
        name='', update=INTACT_Visualisation.boolean_slice)

    Surface_scan_roughness: FloatProperty(
        name='', soft_min=0.0, soft_max=1.0, default=0.0, precision=1,
        update=INTACT_Visualisation.surface_scan_roughness)

    Slice_thickness: FloatProperty(
        name='', soft_min=0.0, default=1.0, precision=2,
        update=INTACT_Visualisation.slice_thickness)

    Resolution_x: IntProperty(
        name='', soft_min=500, soft_max=4000, default=1920, step=10, update=INTACT_ImagesOutput.update_render_resolution)

    Resolution_y: IntProperty(
        name='', soft_min=500, soft_max=4000, default=1080, step=10, update=INTACT_ImagesOutput.update_render_resolution)

    Set_camera_enabled: BoolProperty(name='', default=False, update=INTACT_ImagesOutput.set_camera_position)

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
    ImageInfo,
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
