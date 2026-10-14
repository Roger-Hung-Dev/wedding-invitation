# ZEPETO 大頭 .blend 的驗收（zepeto-avatar-crafter 用）：量網格與材質數值，並渲四個角度給人看。
# 用法（背景執行）：
#   blender.exe -b <OUT>/stylized_face_zepeto.blend --python verify.py -- <OUT>/qa
# 輸出：一行「[verify] {JSON}」＋ qa/front.png、qa/34.png、qa/side.png、qa/back.png（720×720）
# 不存檔：鏡頭只在這次執行中移動。
import bpy, bmesh, os, sys, json
from mathutils import Vector

qa_dir = sys.argv[sys.argv.index("--") + 1]
os.makedirs(qa_dir, exist_ok=True)
sc = bpy.context.scene
head = bpy.data.objects["ZEPETO_Head"]

bm = bmesh.new()
bm.from_mesh(head.data)
seen, islands = set(), []
for v in bm.verts:
    if v.index in seen:
        continue
    stack, n = [v], 0
    seen.add(v.index)
    while stack:
        x = stack.pop()
        n += 1
        for e in x.link_edges:
            o = e.other_vert(x)
            if o.index not in seen:
                seen.add(o.index)
                stack.append(o)
    islands.append(n)

mat = head.data.materials[0] if head.data.materials else None
bsdf = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if mat else None
tex = next((n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image), None) if mat else None
report = {
    "verts": len(head.data.vertices),
    "faces": len(head.data.polygons),
    "islands": len(islands),
    "island_sizes": sorted(islands, reverse=True)[:8],
    "boundary_edges": sum(1 for e in bm.edges if e.is_boundary),
    "non_manifold_edges": sum(1 for e in bm.edges if not e.is_manifold),
    "location": [round(x, 4) for x in head.location],
    "rotation": [round(x, 4) for x in head.rotation_euler],
    "scale": [round(x, 4) for x in head.scale],
    "dimensions": [round(x, 3) for x in head.dimensions],
    "smooth": all(p.use_smooth for p in head.data.polygons),
    "custom_normals": head.data.has_custom_normals,
    "modifiers": [(m.type, getattr(m, "levels", None), getattr(m, "render_levels", None)) for m in head.modifiers],
    "material": mat.name if mat else None,
    "roughness": round(bsdf.inputs['Roughness'].default_value, 3) if bsdf else None,
    "metallic": round(bsdf.inputs['Metallic'].default_value, 3) if bsdf else None,
    "sss_weight": round(bsdf.inputs['Subsurface Weight'].default_value, 3) if bsdf else None,
    "sss_radius": [round(x, 3) for x in bsdf.inputs['Subsurface Radius'].default_value] if bsdf else None,
    "sss_scale": round(bsdf.inputs['Subsurface Scale'].default_value, 3) if bsdf else None,
    "base_color_linked": bool(bsdf and bsdf.inputs['Base Color'].is_linked),
    "texture": tex.image.filepath if tex else None,
    "texture_loaded": bool(tex and tex.image.size[0] > 0),
    "objects": sorted(o.name for o in bpy.data.objects),
    "engine": sc.render.engine,
}

sc.render.resolution_x = sc.render.resolution_y = 720
try:
    sc.eevee.taa_render_samples = 32
except AttributeError:
    pass
cam = sc.camera
target = Vector((0.0, 0.0, 0.05))
renders = []
for name, loc in (("front", (0.0, -5.6, 0.05)), ("34", (3.9, -3.9, 0.3)), ("side", (5.6, 0.0, 0.05)), ("back", (0.0, 5.6, 0.3))):
    cam.location = loc
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(qa_dir, name + ".png")
    bpy.ops.render.render(write_still=True)
    renders.append(sc.render.filepath)
report["renders"] = renders
print("[verify] " + json.dumps(report, ensure_ascii=False))
