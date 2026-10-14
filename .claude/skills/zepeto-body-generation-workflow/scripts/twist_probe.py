# 手腕扭轉、彎曲檢查（references/research-limb-deformation.md 1.8 的 W1、W3、W4、W5、W8＋動畫端要求的「烘焙後再量」）。
# 開 body.blend（唯讀，不存檔），左手：
#   W1 手掌繞前臂扭 −30°／+80°／+150°：前臂 t＝0.2～1.0 每 0.1 切一刀，最小「截面積 ÷ 靜止」
#   W3 手腕往掌心 70°、往手背 60°、往拇指側 20°、往小指側 30°：手腕平分面截面積比
#   W4 只彎不扭時扭轉骨的轉角（應 ≈ 0）
#   W5 往掌心 60°＋扭 90°（看手機）
#   W8 Mixamo 片（texting_standing、thumbs_up、open_door、waving_one_hand、push_heavy、sitting_drinking）各取手腕扭轉最大那格，左右手都量
#   BAKE open_door 那格：照動畫端做法（每格所有骨頭歸零 → 擺姿勢 → 只對 J_Bip_ 打關鍵影格），換到那一格再量，確認約束照樣生效
# 用法：blender -b <body.blend> -P twist_probe.py -- [OUT=<json>] [IMG=<資料夾>（另拍扭 0／80／150° 近照）]
import bpy, sys, os, math, json
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree
sys.path.insert(0, r"D:\SideProject\wedding-invitation\.claude\skills\blender-motion-library\scripts")
import mixamo_retarget as mr

A = dict(a.split("=", 1) for a in sys.argv[sys.argv.index("--") + 1:] if "=" in a) if "--" in sys.argv else {}
EMBED = globals().get("TWIST_EMBED", False)               # body_checks.py 用 exec 叫：不讀命令列參數（那是 body_checks 的 OUT）、W8 只跑開門那支
if EMBED:
    A = {}
O = bpy.data.objects; body = O["Body"]; arm = O["Body_Armature"]; B = arm.data.bones; PB = arm.pose.bones
tgt = mr.Target(arm); AW = arm.matrix_world
for pb in PB:
    pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
bpy.context.view_layer.update()
R0 = {n: (AW.to_quaternion() @ B[n].matrix_local.to_quaternion()) for n in tgt.keys}
H0 = tgt.rest_h["J_Bip_C_Hips"].copy()
TW = [b.name for b in B if b.name.startswith("J_Adj_") and "Twist" in b.name]


def ev():
    dg = bpy.context.evaluated_depsgraph_get(); e = body.evaluated_get(dg); m = e.to_mesh()
    V = [body.matrix_world @ v.co for v in m.vertices]; F = [tuple(p.vertices) for p in m.polygons]; e.to_mesh_clear()
    return V, F


def pose(R):
    mr.apply_pose(arm, tgt, R, H0); bpy.context.view_layer.update()


def seg(side):
    a = AW @ PB[f"J_Bip_{side}_LowerArm"].head; b = AW @ PB[f"J_Bip_{side}_Hand"].head
    return a, b


def area_at(T, c, ax, n=120):
    ax = ax.normalized(); u = ax.orthogonal().normalized(); w = ax.cross(u); pts = []
    for i in range(n):
        a = 2 * math.pi * i / n; h = T.ray_cast(c, u * math.cos(a) + w * math.sin(a), 0.08)
        if h[0] is None:
            return None
        pts.append(((h[0] - c).dot(u), (h[0] - c).dot(w)))
    return abs(sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))) / 2


def forearm_areas(side):
    V, F = ev(); T = BVHTree.FromPolygons(V, F)
    a, b = seg(side)
    return [area_at(T, a.lerp(b, t), b - a) for t in [x / 10 for x in range(2, 11)]]


def wrist_area(side):
    V, F = ev(); T = BVHTree.FromPolygons(V, F)
    a, b = seg(side)
    hd = (AW @ PB[f"J_Bip_{side}_Hand"].tail) - b
    return area_at(T, b, (b - a).normalized() + hd.normalized())


pose(R0)
REST = {s: forearm_areas(s) for s in "LR"}
REST_W = {s: wrist_area(s) for s in "LR"}


def ratio_min(side):
    cur = forearm_areas(side)
    rs = [c / r for c, r in zip(cur, REST[side]) if c and r]
    return round(min(rs), 3) if rs else None


def rot_hand(R, side, axis, deg):
    return mr.rotate_subtree(tgt, R, f"J_Bip_{side}_Hand", Quaternion(axis, math.radians(deg)))   # 回傳新的 R（不改原本的）


def twist_bone_deg(side):
    out = []
    for n in TW:
        if f"_{side}_" not in n:
            continue
        rel = (PB[f"J_Bip_{side}_LowerArm"].matrix.to_quaternion().inverted() @ PB[n].matrix.to_quaternion())
        rest = (B[f"J_Bip_{side}_LowerArm"].matrix_local.to_quaternion().inverted() @ B[n].matrix_local.to_quaternion())
        out.append(round(math.degrees((rest.inverted() @ rel).angle), 2))
    return out


res = {"twist_bones": TW}
L = "L"; fx = (AW.to_3x3() @ Vector((1, 0, 0))).normalized()
# W1：繞前臂（左手＝世界 +X）扭
w1 = {}
for deg in (-30, 80, 150):
    pose(rot_hand(R0, L, fx, deg)); w1[deg] = ratio_min(L)
res["W1_twist_min_area"] = w1
# W3／W4：彎（左手指向 +X、掌心朝 −Z：往掌心＝繞 +Y 正轉，往拇指側＝繞 +Z 負轉）
w3 = {}; w4 = {}
for name, axis, deg in (("flex70", (0, 1, 0), 70), ("ext60", (0, 1, 0), -60), ("radial20", (0, 0, 1), -20), ("ulnar30", (0, 0, 1), 30)):
    pose(rot_hand(R0, L, Vector(axis), deg))
    w3[name] = round(wrist_area(L) / REST_W[L], 3) if REST_W[L] else None
    w4[name] = twist_bone_deg(L)
res["W3_bend_wrist_area"] = w3; res["W4_twist_bones_when_bending_deg"] = w4
# W5：往掌心 60°＋扭 90°
pose(rot_hand(rot_hand(R0, L, Vector((0, 1, 0)), 60), L, fx, 90))
res["W5_flex60_twist90"] = dict(forearm=ratio_min(L), wrist=round(wrist_area(L) / REST_W[L], 3) if REST_W[L] else None)
# W8：Mixamo 片
RAW = r"D:\render-work\mixamo\raw"
w8 = {}; keep = {}
for clip_name in (("open_door",) if EMBED else ("texting_standing", "thumbs_up", "open_door", "waving_one_hand", "push_heavy", "sitting_drinking")):
    fp = os.path.join(RAW, clip_name + ".fbx")
    if not os.path.exists(fp):
        continue
    clip = mr.retarget(mr.read_fbx(fp), tgt)
    best = max(((abs(mr._twist_about(tgt, clip["R"][f], f"J_Bip_{s}_LowerArm", f"J_Bip_{s}_Hand")), f, s)
                for f in range(clip["n"]) for s in "LR"))
    tw, f, s = best
    mr.apply_pose(arm, tgt, clip["R"][f], clip["hips"][f]); bpy.context.view_layer.update()
    w8[clip_name] = dict(frame=f, side=s, twist_deg=round(tw, 1), forearm_min_area=ratio_min(s))
    if clip_name == "open_door":
        keep = dict(clip=clip, frame=f, side=s)
res["W8_mixamo"] = w8
# BAKE：照動畫端的做法烘焙 open_door 前後 3 格（只對 J_Bip_ 打關鍵影格），換到那格再量
if keep:
    clip, f0, s = keep["clip"], keep["frame"], keep["side"]
    sc = bpy.context.scene
    arm.animation_data_create(); act = bpy.data.actions.new("_twist_bake"); arm.animation_data.action = act
    frames = [max(0, f0 - 1), f0, min(clip["n"] - 1, f0 + 1)]
    for i, f in enumerate(frames):
        mr.apply_pose(arm, tgt, clip["R"][f], clip["hips"][f]); bpy.context.view_layer.update()
        for pb in PB:
            if pb.name.startswith("J_Bip_"):
                pb.keyframe_insert("rotation_quaternion", frame=i + 1); pb.keyframe_insert("location", frame=i + 1)
    for pb in PB:                                         # 動畫端：每格先把所有骨頭歸零，扭轉骨沒有關鍵影格
        pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
    sc.frame_set(3); sc.frame_set(2); bpy.context.view_layer.update()
    res["BAKE_open_door"] = dict(frame=f0, side=s, forearm_min_area=ratio_min(s), twist_bones_deg=twist_bone_deg(s))
    arm.animation_data.action = None; bpy.data.actions.remove(act)
# 近照
if A.get("IMG"):
    os.makedirs(A["IMG"], exist_ok=True)
    cam = O["Camera"]; sc = bpy.context.scene; sc.render.resolution_x = sc.render.resolution_y = 520
    for deg in (0, 80, 150):
        pose(rot_hand(R0, L, fx, deg))
        a, b = seg(L); c = a.lerp(b, 0.75)
        for view, d in (("top", Vector((0, -0.25, 1))), ("side", Vector((0, -1, 0.15))), ("under", Vector((0, -0.25, -1)))):
            cam.location = c + d.normalized() * 0.32; cam.data.type = "PERSP"; cam.data.lens = 55
            cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
            sc.render.filepath = os.path.join(A["IMG"], f"twist{deg}_{view}.png"); bpy.ops.render.render(write_still=True)
pose(R0)
if not EMBED:
    print("TWIST", json.dumps(res, ensure_ascii=False))
if A.get("OUT"):
    json.dump(res, open(A["OUT"], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
