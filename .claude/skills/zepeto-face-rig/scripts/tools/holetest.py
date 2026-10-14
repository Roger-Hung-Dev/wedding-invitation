# 破洞檢查（不影響打光）：鏡頭直接看到的背景＝亮綠，反光、照明仍用原本的灰；AI 皮背面＝洋紅
import bpy
sc = bpy.context.scene
w = sc.world or bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
nt = w.node_tree
bg = next(n for n in nt.nodes if n.type == 'BACKGROUND')
lp = nt.nodes.new("ShaderNodeLightPath")
mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'
src = bg.inputs[0].links[0].from_socket if bg.inputs[0].links else None
if src: nt.links.new(src, mx.inputs['A'])
else: mx.inputs['A'].default_value = bg.inputs[0].default_value
mx.inputs['B'].default_value = (0, 1, 0, 1)
nt.links.new(lp.outputs['Is Camera Ray'], mx.inputs['Factor'])
nt.links.new(mx.outputs[2], bg.inputs[0])
sc.render.film_transparent = False
ai = bpy.data.objects["AI_Driven"]
for n in ai.material_slots[0].material.node_tree.nodes:
    if n.type == 'MIX' and n.inputs['Factor'].links and n.inputs['Factor'].links[0].from_node.type == 'NEW_GEOMETRY':
        n.inputs['B'].default_value = (1, 0, 1, 1)
print("[hole2] ok")
