bl_info = {
    "name": "SRPToon Helper (Unity/UE)",
    "author": "halloween123",
    "version": (2, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > SRP Tools",
    "description": "Bake Smooth Normals and Vertex AO.",
    "category": "Mesh",
}

import bpy


class BakePackData(bpy.types.Operator):
        bl_idname = "mesh.bake_vertex_ao"
        bl_label = "Bake Vertex AO"
        bl_description = "Cycles计算 AO,写入属性 'VertexAO'"
        def execute(self,context):
             obj = context.active_object
             if obj is None or obj.type != 'MESH':
                    self.report({'WARNING'},"chose one no Model")
                    return {'CANCELLED'}
             mesh = obj.data
             aname = "Pack Data"
             if aname  in mesh.attributes:
                  mesh.attributes.remove(mesh.attributes[aname])
             color  = mesh.attributes.new(name=aname, type='FLOAT_COLOR', domain='CORNER')
             mesh.attributes.active_color = color
             old = context.scene.render.engine
             context.scene.render.engine = 'CYCLES'
             context.scene.cycles.device = 'GPU'
             context.scene.cycles.samples = 128
             #头发修正
             context.scene.world.light_settings.distance = 0.1 
             try:
                context.scene.render.bake.target = 'VERTEX_COLORS'
             except TypeError:
                  context.scene.render.bake.target = 'ATTRIBUTE'
             self.report({'INFO'}, "正在算 AO...")
             bpy.ops.object.bake(type='AO')
             context.scene.render.engine = old
             self.report({'INFO'}, f"正在打包数据")
             
             for poly in mesh.polygons:
                for loop_idx in poly.loop_indices:
                    bake_ao = color.data[loop_idx].color[0]

                    vidx = mesh.loops[loop_idx].vertex_index
                    snormal = mesh.vertices[vidx].normal
                    
                    r = snormal.x*0.5+0.5
                    g = snormal.y*0.5+0.5
                    b = snormal.z*0.5+0.5
                    color.data[loop_idx].color = (r,g,b,bake_ao) 
             self.report({'INFO'}, f"打包完成！请导出 FBX")
             return {'FINISHED'}

  
#ui面板
class SRPTools(bpy.types.Panel):
    bl_label = "SRP Baker"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SRP Tools'

    def draw(self, context):
        layout = self.layout
        layout.label(text="顶点色一键打包AO+平滑法线:")
        layout.operator(BakePackData.bl_idname, icon='SHADING_RENDERED')
        layout.label(text="RGB=平滑法线, A=AO", icon='INFO') 

classes = (BakePackData,SRPTools)

def register():
     for c in classes:
          bpy.utils.register_class(c)

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()