# 耳朵下方到後頸近照（開接好身體的 body.blend；不存檔）：下巴後面、耳朵下方有沒有深色鋸齒、細黑線、後頸缺皮。
# 用法：blender -b body.blend [-P dbg_body_parts.py] -P nape_closeup.py -- <輸出前綴> [距離 0.3] [R|L]
#   先跑 dbg_body_parts.py 就是分色（Head 紅、Body 藍、Hair 灰／背面洋紅、Ears 綠）
#   三張：側面、斜後 45°、正後；對準耳朵最低點和脖子骨頭的中間
#   身體是 T 字姿勢（身體檔原樣）；手臂放下的姿勢請用身體端的 neck_probe.py（見 ai-mesh-route.md 4.1）
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
out = a[0]
dist = float(a[1]) if len(a) > 1 else 0.3
side = a[2] if len(a) > 2 else "R"
sg = -1 if side == "R" else 1
ears = bpy.data.objects["Ears"]
pts = [ears.matrix_world @ v.co for v in ears.data.vertices]
S = [p for p in pts if p.x * sg > 0] or pts
low = min(S, key=lambda p: p.z)
arm = bpy.data.objects.get("Body_Armature")
neck = (arm.matrix_world @ arm.pose.bones["J_Bip_C_Neck"].head) if arm else low
tgt = Vector((low.x * 0.6, (low.y + neck.y) / 2 + 0.02, (low.z + neck.z) / 2))
sc = bpy.context.scene; cam = sc.camera; sc.render.resolution_x = sc.render.resolution_y = 500
for i, d in enumerate([Vector((sg, 0, 0)), Vector((sg * 0.7, 0.7, 0)), Vector((0, 1, 0))]):
    cam.location = tgt + d.normalized() * dist + Vector((0, 0, 0.02))
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = out + "_%d.png" % i
    bpy.ops.render.render(write_still=True)
print("[nape] 對準 %s → %s_*.png" % (tuple(round(x, 3) for x in tgt), out))
