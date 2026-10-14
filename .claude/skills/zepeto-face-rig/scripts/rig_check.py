# AI 網格路線 ⑥ 骨架檢查：每根控制骨頭拉到底，量對應的形態鍵、材質數值有沒有跟著動（數字），並渲一張全臉總表（圖）。
#   數字：每個姿勢列出「應該變成 1 的」實際值；全部 ≥ 0.99 才算過。寫 rig_metrics.json。
#   圖：姿勢一格一張，鏡頭框住眼睛到嘴巴（照 landmarks）。
# 用法：blender -b rig.blend -P rig_check.py -- <landmarks.json> <輸出資料夾>
import bpy, sys, os, json
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
LM = json.load(open(a[0], encoding="utf-8")); OUT = a[1]
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
rig = bpy.data.objects["Face_Rig"]
ai = bpy.data.objects.get("Head") or bpy.data.objects["AI_Driven"]
L = 0.12
mat_nodes = {}
for m in bpy.data.materials:
    if m.node_tree:
        for nd in m.node_tree.nodes:
            if nd.type == 'VALUE' and nd.name.startswith(("BLINK_", "LOOK_", "JAW_OPEN")) and m is ai.data.materials[0]:
                mat_nodes[nd.name] = nd
# 姿勢：名稱、{骨頭: (x, y)}、{要檢查的: 期望值}（"物件:形態鍵" 或 "@材質數值"）
POSES = [
    ("原樣", {}, {}),
    ("張嘴", {"CTRL_Jaw": (0, -L)}, {"AI_Driven:jawOpen": 1, "bottom_teeth:jawOpen": 1, "Tongue:jawOpen": 1, "@JAW_OPEN": 1}),
    ("下巴往左", {"CTRL_Jaw": (L, -0.5 * L)}, {"AI_Driven:jawLeft": 1, "bottom_teeth:jawLeft": 1}),
    ("微笑", {"CTRL_Smile": (0, L)}, {"AI_Driven:mouthSmileLeft": 1, "AI_Driven:mouthSmileRight": 1}),
    ("嘴角下撇", {"CTRL_Mouth": (0, -L)}, {"AI_Driven:mouthFrownLeft": 1, "AI_Driven:mouthFrownRight": 1}),
    ("嘴往右", {"CTRL_Mouth": (-L, 0)}, {"AI_Driven:mouthRight": 1}),
    ("閉左眼", {"CTRL_Blink_L": (0, -L)}, {"@BLINK_Left": 1}),
    ("閉雙眼", {"CTRL_Blink_L": (0, -L), "CTRL_Blink_R": (0, -L)}, {"@BLINK_Left": 1, "@BLINK_Right": 1}),
    ("往畫面右看", {"CTRL_Eyes": (L, 0)}, {"@LOOK_L_X": 1, "@LOOK_R_X": 1}),  # 左右看沒有形態鍵：模板的 eyeLookIn/Out 只轉眼球、不動皮膚，轉移時沒產生
    ("往上看", {"CTRL_Eyes": (0, L)}, {"@LOOK_L_Z": 1, "@LOOK_R_Z": 1, "AI_Driven:eyeLookUpLeft": 1}),
    ("挑眉", {"CTRL_Brow_L": (0, L), "CTRL_Brow_R": (0, L), "CTRL_Brow_Inner": (0, L)},
     {"AI_Driven:browOuterUpLeft": 1, "AI_Driven:browOuterUpRight": 1, "AI_Driven:browInnerUp": 1}),
    ("皺眉", {"CTRL_Brow_L": (0, -L), "CTRL_Brow_R": (0, -L)}, {"AI_Driven:browDownLeft": 1, "AI_Driven:browDownRight": 1}),
    ("吐舌頭", {"CTRL_Tongue": (0, -L)}, {"Tongue:tongueOut": 1, "AI_Driven:jawOpen": 0.45}),
    ("閉嘴下巴", {"CTRL_MouthClose": (0, -L)}, {"AI_Driven:mouthClose": 1, "AI_Driven:jawOpen": 1}),
    ("大笑", {"CTRL_Jaw": (0, -0.55 * L), "CTRL_Smile": (0, L)}, {"AI_Driven:jawOpen": 0.55, "AI_Driven:mouthSmileLeft": 1}),
]


def val(spec):
    if spec.startswith("@"):
        nd = mat_nodes.get(spec[1:])
        return None if nd is None else nd.outputs[0].default_value
    on, key = spec.split(":")
    o = bpy.data.objects.get(on) or (ai if on == "AI_Driven" else None)
    kb = o.data.shape_keys.key_blocks.get(key) if o and o.data.shape_keys else None
    return None if kb is None else kb.value


def pose(d):
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0)
    for b, (x, y) in d.items():
        rig.pose.bones[b].location = (x, y, 0)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()


res, ok_all = {}, True
for name, d, want in POSES:
    pose(d)
    # 驅動器在 depsgraph 評估後才寫回；再更新一次讓材質節點值也同步
    bpy.context.view_layer.update()
    got = {k: (round(val(k), 3) if val(k) is not None else None) for k in want}
    ok = all(g is not None and abs(g - w) < 0.01 for (k, w), g in zip(want.items(), got.values()))
    ok_all &= ok
    res[name] = dict(want=want, got=got, ok=ok)
    print("[rig_check] %-6s %s %s" % (name, "OK " if ok else "NG ", got))
json.dump(dict(poses=res, ok=ok_all), open(os.path.join(OUT, "rig_metrics.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("[rig_check] 全部 %s" % ("通過" if ok_all else "有問題"))

# 圖：每個姿勢一格（關鍵影格＋animation，比逐格 render 快）
ez = (LM["eyes"]["L"]["c"][2] + LM["eyes"]["R"]["c"][2]) / 2
mz = LM["mouth"]["center"][2]
tgt = Vector((0, -0.5, (ez + mz) / 2 + 0.02))
cam = sc.camera
cam.data.type = 'PERSP'
cam.location = tgt + Vector((0, -2.2 - 2.5 * (ez - mz), 0.03))
cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
for f, (name, d, _) in enumerate(POSES):
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0)
        pb.keyframe_insert("location", frame=f)
    for b, (x, y) in d.items():
        rig.pose.bones[b].location = (x, y, 0)
        rig.pose.bones[b].keyframe_insert("location", frame=f)
ad = rig.animation_data
if ad and ad.action:
    for fc in getattr(ad.action, "fcurves", []):
        for kp in fc.keyframe_points:
            kp.interpolation = 'CONSTANT'
rig.hide_render = True
sc.frame_start, sc.frame_end = 0, len(POSES) - 1
sc.render.resolution_x = sc.render.resolution_y = 380
try:
    sc.eevee.taa_render_samples = 24
except Exception:
    pass
sc.render.filepath = os.path.join(OUT, "")
sc.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(animation=True)
open(os.path.join(OUT, "frames.txt"), "w", encoding="utf-8").write("\n".join(p[0] for p in POSES))
print("[rig_check] 影格 %d" % len(POSES))
