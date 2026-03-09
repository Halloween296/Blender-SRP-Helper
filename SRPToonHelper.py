bl_info = {
    "name": "SRPToon Helper (Unity/UE)",
    "author": "halloween123",
    "version": (2, 2),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > SRP Tools",
    "description": "Bake Smooth Normals and Vertex AO.",
    "category": "Mesh",
}

import bpy

#通用烘培（适配LOD）
def bake_on_obj(context,obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    context.view_layer.objects.active = obj

    mesh = obj.data
    name = "Pack Data"

    if name in mesh.attributes:
          mesh.attributes.remove(mesh.attributes[name])
    color = mesh.attributes.new(name=name, type='FLOAT_COLOR', domain='CORNER')
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
    print(f"正在对{obj.name}算 AO...")
    bpy.ops.object.bake(type='AO')

    print(f"正在对{obj.name}打包法线数据...")
    for poly in mesh.polygons:
       for loop_idx in poly.loop_indices:
          bake_ao = color.data[loop_idx].color[0]

          vidx = mesh.loops[loop_idx].vertex_index
          snormal = mesh.vertices[vidx].normal
                    
          r = snormal.x*0.5+0.5
          g = snormal.y*0.5+0.5
          b = snormal.z*0.5+0.5
          color.data[loop_idx].color = (r,g,b,bake_ao) 
    context.scene.render.engine = old
         

#仅打包当前物体
class BakePackData(bpy.types.Operator):
        bl_idname = "mesh.bake_vertex_ao"
        bl_label = "Bake Vertex AO/Normal"
        bl_description = "只对当前选中模型烘培"
        def execute(self,context):
             obj = context.active_object
             if obj is None or obj.type != 'MESH':
                    self.report({'WARNING'},"chose one no Model")
                    return {'CANCELLED'}
             
             bake_on_obj(context,obj)
             self.report({'INFO'}, f"打包完成！请导出 FBX")
             return {'FINISHED'}


#lod生成/权重画笔
class MESH_Weight(bpy.types.Operator):
     bl_idname = "mesh.create_weight"
     bl_label = "创建/编辑权重"
     bl_description = "新建顶点组并且进入权重绘制，红色区域不被减面"

     def execute(self,context):
          obj = context.active_object
          if obj is None or obj.type != 'MESH':
            self.report({'WARNING'}, "请先选中一个模型！")
            return {'CANCELLED'}
          
          group_name = "维持细节"
          if group_name not in obj.vertex_groups:
               obj.vertex_groups.new(name=group_name)
          else:
               obj.vertex_groups.active = obj.vertex_groups[group_name]
          bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
          self.report({'INFO'}, "请用画笔涂上去 (红=不减面, 蓝=减面权重大)")
          return {'FINISHED'}

#生成lod
class Mesh_LODs(bpy.types.Operator):
     bl_idname = "mesh.create_lods"
     bl_label = "一键生成多级LOD"
     bl_description = "根据输入层级自动减面数，并且自动识别权重（先减面再烘培其他）"
     
     def execute(self,context):
          obj = context.active_object
          if obj is None or obj.type != 'MESH':
                self.report({'WARNING'}, "请先选择 LOD0 模型！")
                return {'CANCELLED'}
          #需要切换回物体模式
          if context.mode != "OBJECT":
                bpy.ops.object.mode_set(mode='OBJECT')
          lod_count = context.scene.srp_lod_count
          ratios = [0.5, 0.2, 0.05] # LOD1 50%, LOD2 20%, LOD3 5%

          b_name = obj.name
          #改名标注
          if not b_name.endswith("_LOD0"):
               obj.name = b_name + "_LOD0"
               b_name = b_name.replace("_LOD0","")
          bpy.ops.object.select_all(action='DESELECT')
          weight_group_name = "维持细节"
          has_weight = weight_group_name in obj.vertex_groups

          #根据权重生成低模后再烘培
          g_lods = []

          for i in range(1,lod_count + 1):
               bpy.ops.object.select_all(action='DESELECT')


               new_obj = obj.copy()
               new_obj.data = obj.data.copy()
               new_obj.name = f"{b_name}_LOD{i}"
               context.collection.objects.link(new_obj)

               mod = new_obj.modifiers.new(name="Decimate", type='DECIMATE')
               mod.ratio = ratios[i-1]
               #是否有权重图
               if has_weight:
                    mod.vertex_group = weight_group_name
                    mod.invert_vertex_group = True 
               
               context.view_layer.objects.active = new_obj
               new_obj.select_set(True)
               bpy.ops.object.modifier_apply(modifier=mod.name)
               g_lods.append(new_obj)
          

          bake_all_models = [obj] + g_lods

          for obj_bake in bake_all_models:
               bake_on_obj(context,obj_bake)

          bpy.ops.object.select_all(action='DESELECT')
          context.view_layer.objects.active = obj
          obj.select_set(True)

          self.report({'INFO'}, f"成功生成 {lod_count} 级 LOD并且全部烘培完成")
          return {'FINISHED'}


#ui面板
class SRPTools(bpy.types.Panel):
    bl_label = "SRP Baker + LOD Helper"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SRP Tools'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.label(text="顶点色一键打包AO+平滑法线:")
        layout.operator(BakePackData.bl_idname, icon='SHADING_RENDERED')
        layout.label(text="RGB=平滑法线, A=AO", icon='INFO') 

        layout.separator()
        layout.separator()

        layout.label(text="可绘制权重的LOD减面")
        layout.operator(MESH_Weight.bl_idname,icon = 'WPAINT_HLT')

        row = layout.row()
        row.prop(scene, "srp_lod_count", text="生成LOD级数：")
        layout.operator(Mesh_LODs.bl_idname, icon='MOD_DECIM')

classes = (BakePackData,MESH_Weight,Mesh_LODs,SRPTools)

def register():
     bpy.types.Scene.srp_lod_count = bpy.props.IntProperty(
        name="LOD Level",
        default=2,
        min=1,
        max=3,
        description="生成的 LOD 层级数量"
    )
     for c in classes:
          bpy.utils.register_class(c)

def unregister():
    del bpy.types.Scene.srp_lod_counts
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
