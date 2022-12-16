bl_info = {
    "name": "Distance Map",
    "author": "Niels Klop",
    "version": (1, 21),
    "blender": (2, 92, 0),
    "location": "View3D > Sidebar > Distance Map",
    "description": "Calculate and visualize the distance between two objects",
    "category": "Object",
}

import bpy
import numpy as np
import mathutils as mu
import blf
import bpy_extras
import copy
import random
import os
from bpy_extras import view3d_utils

#callback function for plotting text map
def drawTextCallback(context, dummy):
    object = bpy.context.active_object
    
    #check if distance map
    if not object.name[0:2] == "DM" and not "distances" in object.keys():
        return
    
    lookupTable = [item for item in object["distances"]] #retrieve lookup table from custom properties
    verts = [object.matrix_world @ v.co for v in object.data.vertices] #retrieve object's vertex locations
    
    for count, item in enumerate(lookupTable):
        if item == 10**9: #10**9 = None (no raycast hit)
            continue
        vertLocOnScreen = view3d_utils.location_3d_to_region_2d(context.region, context.space_data.region_3d, verts[count]) #3d vertex location to 2d region location
        blf.position(0, vertLocOnScreen[0], vertLocOnScreen[1], 0) #set text location
        blf.size(0, bpy.context.scene.fontSize, 72) #set text size
        fontColor = bpy.context.scene.fontColor
        blf.color(0, fontColor[0], fontColor[1], fontColor[2], 1) #set text color
        txt = '{:.{prec}f}'.format(item, prec = bpy.context.scene.decimals) #format number of decimals
        blf.draw(0, txt) #draw text
    return

#callback function for plotting color map
def drawColorMapCallback(context, dummy):
    object = bpy.context.active_object
    
    #check if distance map
    if not object.name[0:2] == "DM" and not "distances" in object.keys():
        return
    
    #set color map range and minimum distance
    if object["method"] == 'normals':
        discreteVals = np.linspace(-1, 1, object["levels"])
        strings = [("", (1,1,1)), ('{:.{prec}f}'.format(-object["maxDistance"], prec = bpy.context.scene.decimals) + " ", bpy.context.scene.fontColor)]
    elif object["method"] == 'nearest':
        discreteVals = np.linspace(0, 1, object["levels"])
        strings = [("", (1,1,1)), (str(0) + " ", bpy.context.scene.fontColor)]
    
    #assign color map gradient to unicode blocks
    for val in discreteVals:
        if val >= 0:
            col = [1 - (1 - i) * np.abs(val) for i in object["posCol"]]
        else:
            col = [1 - (1 - i) * np.abs(val) for i in object["negCol"]]
        
        if object["levels"] < 7:
            strings.append((u"\u2588" * 4, col))
        elif object["levels"] >= 7 and object["levels"] < 11:
            strings.append((u"\u2588" * 3, col))
        elif object["levels"] >= 11 and object["levels"] < 25:
            strings.append((u"\u2588" * 2, col))
        elif object["levels"] >= 25:
            strings.append((u"\u2588", col))
        
    #add maximum distance
    strings.append((" +" + '{:.{prec}f}'.format(object["maxDistance"], prec = bpy.context.scene.decimals), bpy.context.scene.fontColor))
    
    #draw color map
    offset = 0
    for txt, col in strings:
        blf.color(0, col[0], col[1], col[2], 1)
        width, height = blf.dimensions(0, txt)
        blf.position(0, 25 + offset, 25, 0)
        blf.size(0, np.int8(bpy.context.scene.fontSize) * 2, 72)
        blf.draw(0, txt)
        blf.aspect(0, 0.2)
        offset += width - 1
    return

class OBJECT_OT_distanceMapReadme_operator(bpy.types.Operator):
    """Export read me"""
    bl_idname = "object.distancemapreadme"
    bl_label = "Export read me"
    filepath: bpy.props.StringProperty(subtype = "FILE_PATH")

    def execute(self, context):
        #readme
        readme = '*** DISTANCE MAP READ ME ***' + '\n\n' 'The Distance Map addon is visible in the Sidebar (hotkey N) > Distance Map. To generate a distance map, select two objects with mesh data. The distance map is built onto the last selected (active) object. The first selected (inactive) object serves as the target object, i.e. the object to which the distance is calculated. NOTE1: Modifiers are not applied before calculating the distance map. NOTE2: Color and text maps are not updated when an object is transformed after calculating the distance map. NOTE3: Editing the geometry of an existing distance map will lead to invalid measurements.' + '\n\n' '* Generate Distance Map' + '\n' 'Generate a distance map of two selected mesh objects. A new DM (Distance Map) object is added in the Outliner. Multiple distance maps of the same objects will get a prefix DM_v1, DM_v2, etc. Upon generating a distance map, the viewport shading is set to studio lighting "paint.sl" and viewport color is set to "Vertex".' + '\n\n' '* Raycast Mode' + '\n' 'There are two methods to calculate a distance map. The "Normals" mode searches for the shortest distance from the base object to the target object along the vertex normals. Whether a hit was found along the positive or negative normal direction determines the color. If no hit was found, the out of range color is used. The "Nearest" mode searches for the shortest distance to the target object in any direction. The terms "positive" and "negative" are ill-defined in this context; this method therefore only uses the positive color. In contrary to the "Normals" mode, this method yields results for every vertex, as it searches in any direction.' + '\n\n' '* Maximum Distance' + '\n' 'This is the maximum search depth and hence, also the maximum distance for the color map. The out of range color is used for distances beyond the maximum search depth.' + '\n\n' '* Color Map Levels' + '\n' 'Number of color levels that is used for the color map.' + '\n\n' '* Use Selected Geometry' + '\n' 'If this box is checked, the distance map is calculated using only the selected geometry of the base and target objects. Make sure a selection is made on both objects in Edit Mode.' + '\n\n' '* Positive Color' + '\n' 'Color that is used for positive distances.' + '\n\n' '* Negative Color' + '\n' 'Color that is used for negative distances (disabled in "Nearest" mode).' + '\n\n' '* Out Of Range Color' + '\n' 'Color that is used when no raycast hit was found (disabled in "Nearest" mode).' + '\n\n' '* Show Distances' '\n' 'Display the distances of the active DM object in the viewport.' + '\n\n' '* Show Color Map' '\n' 'Display the color map of the active DM object in the viewport.' + '\n\n' '* Font Size' '\n' 'The font size of the distances in the viewport.' + '\n\n' '* Decimals' '\n' 'The number of decimals of the distances in the viewport.' + '\n\n' '* Font Color' + '\n' 'The font color of the distances in the viewport.' + '\n\n' '* Export Distances' + '\n' 'Export the distances of the active DM object to a text file. The values can be copied to other software for further analysis. In the text file, row index corresponds to vertex index (both starting at 0). A "nan" value indicates that there was no raycast hit for this vertex.'
        
        #write readme
        file = open(self.filepath, 'w')
        file.write(readme)
        return {'FINISHED'}
        
    def invoke(self, context, event):
        #open explorer
        context.window_manager.fileselect_add(self)
        
        #set path and file name
        defaultFileName = 'readme.txt'
        if os.path.split(self.filepath)[1] != 'readme.txt':
            self.filepath = self.filepath + defaultFileName
        return {'RUNNING_MODAL'}

class OBJECT_OT_distanceMap_operator(bpy.types.Operator):
    """Generate distance map of two selected mesh objects; adds a new DM (Distance Map) object"""
    bl_idname = "object.generatedistancemap"
    bl_label = "Generate Distance Map"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) == 2 and bpy.context.selected_objects[0].type == 'MESH' and bpy.context.selected_objects[1].type == 'MESH'
    
    def execute(self, context):
        #assign objects
        baseObject = bpy.context.active_object
        
        targetObject = bpy.context.selected_objects
        targetObject.remove(baseObject)
        targetObject = targetObject[0]
        
        ver = 0
        DMname = 'DM_v' + str(ver) + '_' + baseObject.name + '+' + targetObject.name #store original object names
        while DMname[0:63] in bpy.data.objects.keys():
            ver += 1
            DMname = 'DM_v' + str(ver) + '_' + baseObject.name + '+' + targetObject.name #store original object names
        
        if bpy.context.scene.useSelection:
            baseSelection = [v for v in baseObject.data.vertices if v.select]
            targetSelection = [v for v in targetObject.data.vertices if v.select]
            if len(baseSelection) == 0 or len(targetSelection) == 0:
                self.report({'ERROR'}, "No selection on one or both objects.")
                return {'FINISHED'}
            
            baseObject.select_set(False)
            bpy.context.view_layer.objects.active = targetObject
            bpy.ops.object.mode_set(mode = 'EDIT')
            bpy.ops.mesh.duplicate_move()
            bpy.ops.mesh.separate(type = 'SELECTED')
            bpy.ops.object.mode_set(mode = 'OBJECT')
            targetObject.select_set(False)
            targetObject = bpy.context.selected_objects[0]
            
            targetObject.select_set(False)
            baseObject.select_set(True)
            bpy.context.view_layer.objects.active = baseObject
            bpy.ops.object.mode_set(mode = 'EDIT')
            bpy.ops.mesh.duplicate_move()
            bpy.ops.mesh.separate(type = 'SELECTED')
            bpy.ops.object.mode_set(mode = 'OBJECT')
            baseObject.select_set(False)
            baseObject = bpy.context.selected_objects[0]
            
        else:
            targetObject.select_set(False)
            bpy.ops.object.duplicate_move()
            baseObject = bpy.context.active_object
        
        #assign new distance map object
        baseObject.name = DMname[0:63] #max. 64 characters in name
        
        targetPolygons = []
        targetVerts = []
        for f in targetObject.data.polygons:
            currentPolygon = []
            for loopIndex in f.loop_indices:
                currentPolygon.append(targetObject.data.loops[loopIndex].vertex_index)
            targetPolygons.append(currentPolygon)
        
        for v in targetObject.data.vertices:
            targetVerts.append(targetObject.matrix_world @ v.co)

        #build target tree
        targetTree = mu.bvhtree.BVHTree.FromPolygons(targetVerts, targetPolygons, all_triangles = False, epsilon = 0.0)
        
        #raycast procedure
        lookupTable = []
        
        #normals raycast mode
        if bpy.context.scene.raycastMode == 'normals':
            for v in baseObject.data.vertices:
                vertCo = baseObject.matrix_world @ v.co
                vertNormal = np.asarray(baseObject.matrix_world)[0:3,0:3] @ v.normal
                raycastPositive = targetTree.ray_cast(vertCo, vertNormal, bpy.context.scene.maxDistance)[3]
                raycastNegative = targetTree.ray_cast(vertCo, -vertNormal, bpy.context.scene.maxDistance)[3]
                
                #build lookup table
                if raycastNegative == None and raycastPositive == None:
                    lookupTable.append(None) #no raycast hit
                elif raycastNegative == None:
                    lookupTable.append(-raycastPositive) #only positive raycast hit
                elif raycastPositive == None:
                    lookupTable.append(raycastNegative) #only negative raycast hit
                elif np.abs(raycastNegative) < np.abs(raycastPositive):
                    lookupTable.append(raycastNegative) #negative raycast hit is smaller than positive
                elif np.abs(raycastNegative) >= np.abs(raycastPositive):
                    lookupTable.append(-raycastPositive) #positive raycast hit is smaller than or equal to negative
                
        #nearest raycast mode
        elif bpy.context.scene.raycastMode == 'nearest':
            for v in baseObject.data.vertices:
                vertCo = baseObject.matrix_world @ v.co
                raycast = targetTree.find_nearest(vertCo, bpy.context.scene.maxDistance)
                
                #build lookup table
                lookupTable.append(raycast[3])
        
        #add variables to custom properties (and remove all other custom properties)
        lookupTableCustomProp = copy.deepcopy(lookupTable)
        for count, item in enumerate(lookupTableCustomProp):
            if item is None:
                lookupTableCustomProp[count] = 10**9 #replace None with 10**9; only float, int or dict allowed in custom properties, but dict is very slow, float and int do not allow None    
        
        for k in list(baseObject.keys()):
            del baseObject[k]
        
        baseObject["distances"] = lookupTableCustomProp
        baseObject["method"] = bpy.context.scene.raycastMode
        baseObject["levels"] = bpy.context.scene.levels
        baseObject["maxDistance"] = bpy.context.scene.maxDistance
        
        #lookup table normalization and discretization
        lookupTableNormDisc = copy.deepcopy(lookupTable)
        
        #baseObject["levels"] = bpy.context.scene.levels
        if bpy.context.scene.raycastMode == 'normals':
            discreteVals = np.linspace(-1, 1, bpy.context.scene.levels)
        elif bpy.context.scene.raycastMode == 'nearest':
            discreteVals = np.linspace(0, 1, bpy.context.scene.levels)
        
        for v, item in enumerate(lookupTableNormDisc):
            if item is not None: #None for no raycast hit
                normValue = item / bpy.context.scene.maxDistance
                discreteValue = discreteVals[np.argmin(np.abs(discreteVals - normValue))]
                lookupTableNormDisc[v] = discreteValue
        
        #color assignment, sRGB to RGB (gamma correction of 2.2)
        positiveColorRGB = np.power(bpy.context.scene.positiveColor, 1 / 2.2)
        negativeColorRGB = np.power(bpy.context.scene.negativeColor, 1 / 2.2)
        outOfRangeColorRGB = np.power(bpy.context.scene.outOfRangeColor, 1 / 2.2)
        baseObject["posCol"] = positiveColorRGB
        baseObject["negCol"] = negativeColorRGB
        
        #add vertex color map (and remove all other color maps)
        vertexColors = baseObject.data.vertex_colors
        while vertexColors:
            vertexColors.remove(vertexColors[0])
        
        colorLayer = baseObject.data.vertex_colors.new(name = "distances")
        baseObject.data.vertex_colors.active = colorLayer
        
        #color assignment works by iterating over every corner of every polygon
        for f in baseObject.data.polygons:
            for loopIndex in f.loop_indices:
                vertIndex = baseObject.data.loops[loopIndex].vertex_index
                if lookupTableNormDisc[vertIndex] == None:
                    colorLayer.data[loopIndex].color = [outOfRangeColorRGB[0], outOfRangeColorRGB[1], outOfRangeColorRGB[2], 1] #no raycast hit
                elif lookupTableNormDisc[vertIndex] >= 0:
                    vertColor = [1 - (1 - i) * np.abs(lookupTableNormDisc[vertIndex]) for i in positiveColorRGB] #gradient to white for smaller distances
                    colorLayer.data[loopIndex].color = [vertColor[0], vertColor[1], vertColor[2], 1] #positive raycast hit
                elif lookupTableNormDisc[vertIndex] < 0:
                    vertColor = [1 - (1 - i) * np.abs(lookupTableNormDisc[vertIndex]) for i in negativeColorRGB] #gradient to white for smaller distances
                    colorLayer.data[loopIndex].color = [vertColor[0], vertColor[1], vertColor[2], 1] #negative raycast hit
        
        #delete duplicate target object if only selection is used
        if bpy.context.scene.useSelection:
            baseObject.select_set(False)
            targetObject.select_set(True)
            bpy.context.view_layer.objects.active = targetObject
            bpy.ops.object.delete()
            baseObject.select_set(True)
            bpy.context.view_layer.objects.active = baseObject
        
        #set shading and coloring
        bpy.context.space_data.shading.show_object_outline = False
        
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'SOLID'
                        space.shading.color_type = 'VERTEX'
        
        bpy.context.space_data.shading.type = 'SOLID'
        bpy.context.space_data.shading.light = 'STUDIO'
        bpy.context.space_data.shading.studio_light = 'paint.sl'
        return {'FINISHED'}

class OBJECT_OT_showDistances_operator(bpy.types.Operator):
    """Show distances of selected DM (Distance Map) object in viewport"""
    bl_idname = "object.showdistances"
    bl_label = ""
    bl_options = {'REGISTER', 'UNDO'}
    
    def invoke(self, context, event):
        if globalVars.showdistances:
            #switch show/hide status
            globalVars.showdistances = 0
            
            #add handler (text is drawn every frame)
            bpy.types.SpaceView3D.draw_handler_remove(globalVars.drawHandleDistances, 'WINDOW')
            
            #redraw scene
            bpy.ops.wm.redraw_timer(type = 'DRAW_WIN_SWAP', iterations = 1)
            return {'FINISHED'}
        else:
            #switch show/hide status
            globalVars.showdistances = 1
            
            #remove handler (text is drawn every frame)
            globalVars.drawHandleDistances = bpy.types.SpaceView3D.draw_handler_add(drawTextCallback, (bpy.context, None), 'WINDOW', 'POST_PIXEL')
            
            #redraw scene
            bpy.ops.wm.redraw_timer(type = 'DRAW_WIN_SWAP', iterations = 1)
            return {'RUNNING_MODAL'}

class OBJECT_OT_showColorMap_operator(bpy.types.Operator):
    """Show color map of selected DM (Distance Map) object in viewport"""
    bl_idname = "object.showcolormap"
    bl_label = ""
    bl_options = {'REGISTER', 'UNDO'}
    
    def invoke(self, context, event):
        if globalVars.showcolormap:
            #switch show/hide status
            globalVars.showcolormap = 0
            
            #add handler (map is drawn every frame)
            bpy.types.SpaceView3D.draw_handler_remove(globalVars.drawHandleColorMap, 'WINDOW')
            
            #redraw scene
            bpy.ops.wm.redraw_timer(type = 'DRAW_WIN_SWAP', iterations = 1)
            return {'FINISHED'}
        else:
            #switch show/hide status
            globalVars.showcolormap = 1
            
            #remove handler (map is drawn every frame)
            globalVars.drawHandleColorMap = bpy.types.SpaceView3D.draw_handler_add(drawColorMapCallback, (bpy.context, None), 'WINDOW', 'POST_PIXEL')
            
            #redraw scene
            bpy.ops.wm.redraw_timer(type = 'DRAW_WIN_SWAP', iterations = 1)
            return {'RUNNING_MODAL'}

class OBJECT_OT_exportDistances_operator(bpy.types.Operator):
    """Export distances of active distance map of active object to file"""
    bl_idname = "object.exportdistances"
    bl_label = "Export Distances"
    filepath: bpy.props.StringProperty(subtype = "FILE_PATH")
    
    @classmethod
    def poll(cls, context):
        object = bpy.context.active_object
        if object != None:
            return len(context.selected_objects) == 1 and len(object.data.vertex_colors) > 0 and object.data.vertex_colors.active.name in object.keys()
    
    def execute(self, context):
        object =  bpy.context.active_object
        if len(object.data.vertex_colors) > 0: #if there is at least one vertex color map
            if object.data.vertex_colors.active.name in object.keys(): #check if color map name corresponds to one of the object's custom properties
                mapID = object.data.vertex_colors.active.name #retrieve active color map name
                #lookupTable = np.array([item for item in object[mapID].values()], dtype = np.float) #retrieve lookup table from custom properties
                lookupTable = object[mapID].to_list()
                for count, item in enumerate(lookupTable):
                    if item == 10**9:
                        lookupTable[count] = np.nan
                
        #write distances
        np.savetxt(self.filepath, np.array(lookupTable), fmt = "%.3f")
        return {'FINISHED'}
        
    def invoke(self, context, event):
        #open explorer
        context.window_manager.fileselect_add(self)
        
        #set path and file name
        defaultFileName = 'distances.txt'
        if os.path.split(self.filepath)[1] != 'distances.txt':
            self.filepath = self.filepath + defaultFileName
        return {'RUNNING_MODAL'}

class OBJECT_PT_distanceMap_panel(bpy.types.Panel):
    bl_category = "Distance Map"
    bl_label = "Distance Map"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"

    def draw(self, context):
        #readme panel
        layout = self.layout
        row = layout.row()
        row.alignment = "RIGHT"
        row.scale_x = 2
        row.operator("object.distancemapreadme", text = "", icon = "QUESTION")
        layout.separator()
        
        #color map panel
        layout.label(text = "Color Map Settings")
        layout.operator("object.generatedistancemap")
        row = layout.row()
        row.label(text = "Raycast Mode")
        row.prop(context.scene, "raycastMode", text = "")
        layout.prop(context.scene, "maxDistance", text = "Maximum Distance")
        layout.prop(context.scene, "levels", text = "Color Map Levels")
        layout.prop(context.scene, "useSelection", text = "Use Selected Geometry")
        layout.prop(context.scene, "positiveColor", text = "Positive Color")
        row = layout.row()
        row.prop(context.scene, "negativeColor", text = "Negative Color")
        if bpy.context.scene.raycastMode == 'nearest':
            row.enabled = False
        row = layout.row()
        row.prop(context.scene, "outOfRangeColor", text = "Out Of Range Color")
        if bpy.context.scene.raycastMode == 'nearest':
            row.enabled = False
        layout.separator()
        
        #text map panel
        layout.label(text = "Text Map Settings")
        if globalVars.showdistances:
            txt = "Hide Distances"
        else:
            txt = "Show Distances"
        layout.operator("object.showdistances", text = txt)
        if globalVars.showcolormap:
            txt = "Hide Color Map"
        else:
            txt = "Show Color Map"
        layout.operator("object.showcolormap", text = txt)
        layout.prop(context.scene, "fontSize", text = "Font Size")
        layout.prop(context.scene, "decimals", text = "Decimals")
        layout.prop(context.scene, "fontColor", text = "Font Color")
        layout.operator("object.exportdistances")

class globalVars():
    pass

classes = (
    OBJECT_OT_distanceMapReadme_operator,
    OBJECT_OT_distanceMap_operator,
    OBJECT_OT_showDistances_operator,
    OBJECT_OT_showColorMap_operator,
    OBJECT_OT_exportDistances_operator,
    OBJECT_PT_distanceMap_panel)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    globalVars.showdistances = 0
    globalVars.showcolormap = 0
    
    bpy.types.Scene.raycastMode = bpy.props.EnumProperty(
        items = [("normals", "Normals", "Shortest distance to target object along positive or negative direction of vertex normals"),
        ("nearest", "Nearest", "Shortest distance to target object in any direction (only positive colors)")])
    bpy.types.Scene.maxDistance = bpy.props.FloatProperty(
        description = "Maximum search depth",
        default = 5.0, min = 10**-6)
    bpy.types.Scene.levels = bpy.props.IntProperty(
        description = "Number of color levels",
        default = 11, min = 3, max = 50)
    bpy.types.Scene.useSelection = bpy.props.BoolProperty(
        default = False,
        description = "Use selected geometry only (Edit Mode)")
    bpy.types.Scene.positiveColor = bpy.props.FloatVectorProperty(
        name = "Positive color",
        subtype = 'COLOR', min = 0, max = 1, 
        default = (0.0, 0.523, 0.238)) # gamma corrected mint green
    bpy.types.Scene.negativeColor = bpy.props.FloatVectorProperty(
        name = "Negative color",
        subtype = 'COLOR', min = 0, max = 1, 
        default = (0.523, 0.0, 0.041)) #gamma corrected cherry red
    bpy.types.Scene.outOfRangeColor = bpy.props.FloatVectorProperty(
        name = "Out of range color",
        subtype = 'COLOR', min = 0, max = 1, 
        default = (0.214, 0.214, 0.214)) #gamma corrected 50% grey
    bpy.types.Scene.fontSize = bpy.props.IntProperty(
        description = "Font size",
        default = 15, min = 1, max = 30)
    bpy.types.Scene.decimals = bpy.props.IntProperty(
        description = "Number of decimals",
        default = 1, min = 0, max = 6)
    bpy.types.Scene.fontColor = bpy.props.FloatVectorProperty(
        name = "Font color",
        subtype = 'COLOR', min = 0, max = 1, 
        default = (1.0, 1.0, 1.0)) #white

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
