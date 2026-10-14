# 輕亮澤：不加表面光澤層（Coat 會整張臉泛白、眼珠眉毛發灰），只降粗糙度
import bpy, os
for m in bpy.data.materials:
    if not m.use_nodes or "Cavity" in m.name or "Gum" in m.name: continue
    for n in m.node_tree.nodes:
        if n.type != 'BSDF_PRINCIPLED': continue
        n.inputs['Roughness'].default_value = float(os.environ.get("GLOSS_ROUGH", 0.5))
        for k in ('Subsurface Weight', 'Subsurface'):
            if k in n.inputs: n.inputs[k].default_value = float(os.environ.get("GLOSS_SSS", 0.15))
        if 'Specular IOR Level' in n.inputs: n.inputs['Specular IOR Level'].default_value = 0.5
        if 'Coat Weight' in n.inputs: n.inputs['Coat Weight'].default_value = 0.0
print("[gloss] ok")
if os.environ.get("GLOSS_SAVE"):  # 產線用：存回檔案（檢查工具渲圖時不存）
    bpy.ops.wm.save_as_mainfile(filepath=os.environ["GLOSS_SAVE"])
