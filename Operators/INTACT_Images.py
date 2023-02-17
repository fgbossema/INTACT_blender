import bpy
import os
from . import INTACT_Utils


# ---------------------------------------------------------------------------
#          Operators
# ---------------------------------------------------------------------------

def update_render_resolution(self, context):
    context.scene.render.resolution_x = self.Resolution_x
    context.scene.render.resolution_y = self.Resolution_y


class TakeScreenshot(bpy.types.Operator):
    """Take screenshot"""
    bl_idname = "intact.take_screenshot"
    bl_label = "Take Screenshot"

    def execute(self, context):
        INTACT_Props = context.scene.INTACT_Props
        # Set render resolution back to defaults (this is changed e.g. by the multi-view to a lower res)
        context.scene.render.resolution_x = INTACT_Props.Resolution_x
        context.scene.render.resolution_y = INTACT_Props.Resolution_y
        bpy.ops.render.opengl('INVOKE_DEFAULT')
        return {'FINISHED'}


def setup_world_hdri(context):
    world_name = "Forest HDRI"
    INTACT_Props = context.scene.INTACT_Props

    if context.scene.world.name != world_name:
        new_world = bpy.data.worlds.new("Forest HDRI")
        new_world.use_nodes = True
        context.scene.world = new_world

        node_tree = new_world.node_tree
        tree_nodes = node_tree.nodes
        tree_nodes.clear()

        hdri_background_node = tree_nodes.new(type='ShaderNodeBackground')
        hdri_background_node.name = "hdri_background"
        hdri_node = tree_nodes.new('ShaderNodeTexEnvironment')
        hdri_node.name = "hdri"
        # Get path to one of the default blender hdris
        for light in context.preferences.studio_lights:
            if light.type == 'WORLD' and light.name == "forest.exr":
                forest_exr_path = light.path
        hdri_node.image = bpy.data.images.load(forest_exr_path)
        hdri_node.location = -300, 0
        hdri_background_node.location = 0, 0

        node_output = tree_nodes.new(type='ShaderNodeOutputWorld')
        node_output.name = "Output"
        node_output.location = 600, 0

        colour_background_node = tree_nodes.new(type='ShaderNodeBackground')
        colour_background_node.name = "colour_background"
        light_path_node = tree_nodes.new(type="ShaderNodeLightPath")
        light_path_node.name = "light_path"
        mix_shader_node = tree_nodes.new(type="ShaderNodeMixShader")
        mix_shader_node.name = "mix_shader"
        mix_shader_node.location = 300, 0
        light_path_node.location = 0, 500
        colour_background_node.location = 0, -300

        # Link all nodes
        links = node_tree.links
        links.new(hdri_node.outputs["Color"], hdri_background_node.inputs["Color"])
        links.new(light_path_node.outputs["Is Camera Ray"], mix_shader_node.inputs["Fac"])
        links.new(hdri_background_node.outputs["Background"], mix_shader_node.inputs[1])
        links.new(colour_background_node.outputs["Background"], mix_shader_node.inputs[2])
        links.new(mix_shader_node.outputs["Shader"], node_output.inputs["Surface"])

    nodes = context.scene.world.node_tree.nodes
    nodes["colour_background"].inputs["Color"].default_value = INTACT_Props.Background_colour
    nodes["hdri_background"].inputs["Strength"].default_value = INTACT_Props.Lighting_strength


def hide_objects_in_render():
    """Hide all objects that are hidden in viewport in render"""
    for obj in bpy.data.objects:
        if obj.hide_viewport or obj.hide_get():
            obj.hide_render = True


class RenderImage(bpy.types.Operator):
    """Render an image using the current camera position"""
    bl_idname = "intact.render_image"
    bl_label = "Render image"

    def execute(self, context):
        """Render image using one of the default blender hdris for lighting, and a solid colour background via the
        light path node"""
        INTACT_Props = context.scene.INTACT_Props

        # Set render resolution
        context.scene.render.resolution_x = INTACT_Props.Resolution_x
        context.scene.render.resolution_y = INTACT_Props.Resolution_y

        # for ease, all objects that are hidden in viewport, should be hidden in render
        hide_objects_in_render()

        # Set up lighting
        setup_world_hdri(context)

        bpy.ops.render.render('INVOKE_DEFAULT')
        return {'FINISHED'}


class RenderTurntable(bpy.types.Operator):
    """Render and save a turntable movie using the current camera position"""
    bl_idname = "intact.render_turntable"
    bl_label = "Render turntable"

    def execute(self, context):
        """Render a simple turntable animation - using one of the default blender hdris for lighting, and a
        solid colour background via the light path node. It uses the current position of the camera, and parents
        this to an empty rotating on a circle in the xy plane.
        Diameter of circle is set by camera distance from origin of object."""
        INTACT_Props = context.scene.INTACT_Props
        ct_vol = INTACT_Props.CT_Vol

        if not ct_vol:
            message = [" Please input CT Volume first "]
            INTACT_Utils.ShowMessageBox(message=message, icon="COLORSET_02_VEC")
            return {"CANCELLED"}

        # Set render resolution
        context.scene.render.resolution_x = INTACT_Props.Resolution_x
        context.scene.render.resolution_y = INTACT_Props.Resolution_y
        # return to first frame
        context.scene.frame_set(1)

        # for ease, all objects that are hidden in viewport, should be hidden in render
        hide_objects_in_render()
        setup_world_hdri(context)

        rotation_origin = ct_vol.location
        camera = context.scene.camera

        collection_name = "turntable"
        if collection_name not in bpy.data.collections:
            turntable_collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(turntable_collection)
        else:
            turntable_collection = bpy.data.collections[collection_name]
            # delete any existing objects in collection
            for obj in turntable_collection.objects:
                bpy.data.objects.remove(obj)

        # location of camera, but setting z == rotation origin z, as we are only interested in the distance in this
        # plane
        camera_location_xy = camera.location.copy()
        camera_location_xy[2] = rotation_origin[2]
        radius = (camera_location_xy - rotation_origin).length
        bpy.ops.curve.primitive_bezier_circle_add(radius=radius, enter_editmode=False, align='WORLD',
                                                  location=rotation_origin, scale=(1, 1, 1))
        path = bpy.context.active_object
        path.name = "Circle_path"
        path.data.use_path = True
        path.data.use_path_follow = True
        # Make circle higher resolution so camera moves smoothly with no jitter
        path.data.splines[0].resolution_u = 128

        empty = bpy.data.objects.new("empty", None)
        empty.name = "rotation_empty"
        empty.empty_display_type = 'PLAIN_AXES'

        # put them all in the collection
        turntable_collection.objects.link(path)
        turntable_collection.objects.link(empty)

        # Make empty follow path
        follow_path_constraint = empty.constraints.new('FOLLOW_PATH')
        follow_path_constraint.target = path
        follow_path_constraint.use_fixed_location = False
        follow_path_constraint.forward_axis = 'FORWARD_Y'
        follow_path_constraint.up_axis = 'UP_Z'
        follow_path_constraint.use_curve_follow = True

        # Add animation along the circular path
        frame_start = 1
        length = 300
        anim = path.data.animation_data_create()
        anim.action = bpy.data.actions.new("%sAction" % path.data.name)
        fcurve = anim.action.fcurves.new("eval_time")
        fcurve_modifier = fcurve.modifiers.new('GENERATOR')
        fcurve_modifier.coefficients = (-frame_start / length * 100, frame_start / length / frame_start * 100)

        # force update of view, otherwise the camera doesn't parent to the empty's new location on the curve
        context.view_layer.update()

        camera.parent = empty
        camera.matrix_parent_inverse = empty.matrix_world.inverted()

        movies_dir = os.path.join(os.path.dirname(bpy.data.filepath), "Movies")
        if not os.path.exists(movies_dir):
            os.mkdir(movies_dir)

        context.scene.render.filepath = os.path.join(movies_dir, INTACT_Props.Movie_filename)
        context.scene.render.image_settings.file_format = "FFMPEG"
        context.scene.render.ffmpeg.format = "MPEG4"
        context.scene.render.ffmpeg.codec = "H264"
        context.scene.frame_start = frame_start
        context.scene.frame_end = length

        # hide empty and path to avoid cluttering viewport
        path.hide_set(True)
        empty.hide_set(True)

        bpy.ops.render.render('INVOKE_DEFAULT', animation=True)

        return {'FINISHED'}


def lock_camera_to_view(lock_camera):
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            space = area.spaces.active
            space.lock_camera = lock_camera
            break


def enable_camera_position(context):
    """Enable interactive positioning of the camera"""
    INTACT_Props = context.scene.INTACT_Props
    context.scene.render.resolution_x = INTACT_Props.Resolution_x
    context.scene.render.resolution_y = INTACT_Props.Resolution_y

    # If no active camera, make one + set to be active
    if context.scene.camera is None:
        camera_data = bpy.data.cameras.new(name='Camera')
        camera_object = bpy.data.objects.new('Camera', camera_data)
        context.scene.camera = camera_object
        collection = bpy.data.collections.new("Camera")
        bpy.context.scene.collection.children.link(collection)
        collection.objects.link(camera_object)

    # Make sure camera has no parent, so it can move freely, this is necessary if e.g. it was previously being
    # controlled by a follow path constraint
    context.scene.camera.parent = None

    # align camera to current view
    bpy.ops.view3d.camera_to_view()

    # set clip distance
    context.scene.camera.data.clip_start = 2
    context.scene.camera.data.clip_end = 5000

    # lock camera to move with viewport movement
    lock_camera_to_view(True)


def disable_camera_position(context):
    """Confirm camera position, and stop interactive movement with viewport"""
    lock_camera_to_view(False)

    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            space = area.spaces.active
            space.region_3d.view_perspective = "PERSP"
            break


def set_camera_position(self, context):
    if self.Set_camera_enabled:
        enable_camera_position(context)
    else:
        disable_camera_position(context)


# ---------------------------------------------------------------------------
#          Registration
# ---------------------------------------------------------------------------

classes = [
    TakeScreenshot,
    RenderImage,
    RenderTurntable
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
