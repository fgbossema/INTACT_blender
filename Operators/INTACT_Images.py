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
    

#---------------------------------------------------------------------------
#          Registration
#---------------------------------------------------------------------------

classes = [
    Take_Screenshot
    ]
            
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
  
if __name__ == "__main__":
    register()