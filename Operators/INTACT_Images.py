import bpy
from mathutils import Euler
import math


#---------------------------------------------------------------------------
#          Operators
#---------------------------------------------------------------------------

class Take_Screenshot(bpy.types.Operator):
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


class Render_image(bpy.types.Operator):
    """Render an image - using one of the default blender hdris for lighting, and a solid colour background via the
    light path node"""
    bl_idname = "intact.render_image"
    bl_label = "Render image"

    def execute(self, context):
        INTACT_Props = context.scene.INTACT_Props

        # Set render resolution
        context.scene.render.resolution_x = INTACT_Props.Resolution_x
        context.scene.render.resolution_y = INTACT_Props.Resolution_y

        # for ease, all objects that are hidden in viewport, should be hidden in render
        for obj in bpy.data.objects:
            if obj.hide_viewport or obj.hide_get():
                obj.hide_render = True

        # Set up lighting
        world_name = "Forest HDRI"
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
        bpy.ops.render.render('INVOKE_DEFAULT')
        return {'FINISHED'}


def lock_camera_to_view(lock_camera):
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            space = area.spaces.active
            space.lock_camera = lock_camera
            break


def enable_camera_position(context):
    INTACT_Props = context.scene.INTACT_Props
    context.scene.render.resolution_x = INTACT_Props.Resolution_x
    context.scene.render.resolution_y = INTACT_Props.Resolution_y

    # If no active camera, make one + set to be active
    print(context.scene.camera)
    if context.scene.camera is None:
        print("here")
        camera_data = bpy.data.cameras.new(name='Camera')
        camera_object = bpy.data.objects.new('Camera', camera_data)
        context.scene.camera = camera_object
        collection = bpy.data.collections.new("Camera")
        bpy.context.scene.collection.children.link(collection)
        collection.objects.link(camera_object)

    # align camera to current view
    bpy.ops.view3d.camera_to_view()

    # set clip distance
    context.scene.camera.data.clip_start = 0.1
    context.scene.camera.data.clip_end = 1000

    # lock camera to move with viewport movement
    lock_camera_to_view(True)


def disable_camera_position(context):
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

    

#---------------------------------------------------------------------------
#          Registration
#---------------------------------------------------------------------------

classes = [
    Take_Screenshot,
    Render_image
    ]
            
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
  
if __name__ == "__main__":
    register()