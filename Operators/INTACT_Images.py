import bpy
from mathutils import Euler
import math


#---------------------------------------------------------------------------
#          Operators
#---------------------------------------------------------------------------
    
class Example_class(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "intact.example_class"
    bl_label = "Camera Setup"
    
    def execute(self, context):
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
    

#---------------------------------------------------------------------------
#          Registration
#---------------------------------------------------------------------------

classes = [
    Init_Setup,
    Example_class,
    #]
            
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
  
if __name__ == "__main__":
    register()