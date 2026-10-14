# ZEPETO 穿戴物品產生器入口：開一個已出廠的身體 → 照某套服裝的 outfit.py 長出所有衣物配件 → 藏住被蓋住的身體
# → 另存成 <OUT>/outfit.blend（絕不存回 body.blend：存回去 sha 會變，身體出廠閘門會擋住所有人）→ 拍檢查圖、量穿模 → <OUT>/build.json。
#
# 用法（背景 Blender；body.blend 由 list_bodies.py --released 選出）：
#   blender -b <body.blend> -P outfit_build.py -- OUTFIT=<服裝資料夾> OUT=D:/render-work/zepeto-costume/<服裝代號>/<身體名稱> [QA=rest,close,motion]
#
# outfit.py 要提供：
#   build()               → 回傳 [物件, ...]（用 garment_lib 的配方做）
#   covered(位置)          → 選用；身體哪些點被蓋住要藏。沒寫就用 garment_lib.default_covered（長袖＋長褲＋包鞋）
#   EXTRA_CLOSEUPS         → 選用；[(代號, 目標點 fn(A, g)→Vector, 距離, 角度們), ...] 這套服裝特有的近照
import bpy, bmesh, math, os, sys, json, time, importlib.util
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "blender-motion-library", "scripts"))
import garment_lib as G
import mixamo_retarget as mr

ARGS = dict(a.split("=", 1) for a in sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else {}
OUTFIT = ARGS["OUTFIT"]; OUT = ARGS["OUT"]
QA = ARGS.get("QA", "rest,close,motion").split(",")
RAW = r"D:\render-work\mixamo\raw"
os.makedirs(OUT, exist_ok=True)
T0 = time.time()

sc = bpy.context.scene; O = bpy.data.objects
body, arm, head, fr = G.body, G.arm, G.head, G.fr
A = G.A
H = 0.30; HL = 0.38 * H
MOUTH_FILE = Vector((-0.0148, -0.655, -0.3585))       # 可動臉檔座標的嘴（和 zepeto-body 的 body_build.py 同一點）

spec = importlib.util.spec_from_file_location("outfit", os.path.join(OUTFIT, "outfit.py"))
outfit = importlib.util.module_from_spec(spec); spec.loader.exec_module(outfit)

# ════════ 長衣服、藏身體、存檔 ════════
items = outfit.build()
n_hidden = G.hide_body(getattr(outfit, "covered", G.default_covered))
bpy.context.view_layer.update()
info = dict(outfit=os.path.basename(OUTFIT.rstrip("/\\")), body_blend=bpy.data.filepath,
            anchors={k: round(v, 3) for k, v in A.items()}, hidden_body_verts=n_hidden,
            faces={o.name: len(o.data.polygons) for o in items}, build_sec=round(time.time() - T0, 1))
print("BUILT", json.dumps(info, ensure_ascii=False))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "outfit.blend"), copy=True)


# ════════ 穿模檢查：衣服的點跑進身體（或頭）裡面的比例 ════════
def bvh_of(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg); me = ev.to_mesh()
    vs = [obj.matrix_world @ v.co for v in me.vertices]
    bvh = BVHTree.FromPolygons(vs, [p.vertices[:] for p in me.polygons])
    ev.to_mesh_clear()
    return bvh, vs


def inside_ratio(cloth, solid, tol=0.002):
    bvh, _ = bvh_of(solid)
    _, vs = bvh_of(cloth)
    bad = 0
    for v in vs[::3]:
        hit = bvh.find_nearest(v, 0.05)
        if hit[0] is not None and (v - hit[0]).dot(hit[1]) < -tol:
            bad += 1
    return round(100.0 * bad / max(1, len(vs[::3])), 2)


BIG = [o for o in items if len(o.data.polygons) > 2000]       # 大件衣物才量（小配件貼在衣服上，量了沒意義）
PAIRS = [(o, body) for o in BIG] + [(o, head) for o in BIG if max((o.matrix_world @ v.co).z for v in o.data.vertices) > A["SH_Z"]]


def clip_report():
    m = body.modifiers["HideUnderOutfit"]
    m.show_viewport = False; bpy.context.view_layer.update()
    try:
        return {f"{a.name}→{b.name}": inside_ratio(a, b) for a, b in PAIRS}
    finally:
        m.show_viewport = True; bpy.context.view_layer.update()


# ════════ 攝影（沿用身體檔裡的攝影棚：Camera、燈、地板） ════════
cam = O["Camera"]


def aim(loc, target, lens=50, ortho=None):
    cam.location = loc
    if ortho:
        cam.data.type = "ORTHO"; cam.data.ortho_scale = ortho
    else:
        cam.data.type = "PERSP"; cam.data.lens = lens
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


def shot(path, res=(640, 640)):
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"; sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def views(prefix, target, dist, angles, lens=50, res=(640, 640), ortho=None, h_off=0.0):
    """角度：0＝正面、45＝角色右前方、90＝右側、180＝背面、負的＝左邊"""
    out = []
    for a in angles:
        r = math.radians(a)
        aim(Vector(target) + Vector((-math.sin(r) * dist, -math.cos(r) * dist, h_off)), target, lens, ortho)
        p = f"{prefix}_{a}.png"; shot(p, res); out.append(os.path.basename(p))
    return out


tgt = mr.Target(arm)
idle = mr.retarget(mr.read_fbx(os.path.join(RAW, "female_idle.fbx")), tgt)


def pose_from_clip(clip, f, ref=None):
    ref = f if ref is None else ref
    mr.apply_pose(arm, tgt, clip["R"][f], clip["hips"][f])
    y = clip["yaw"][ref]; h = clip["hips"][ref]
    arm.rotation_euler = (0, 0, -y)
    arm.location = -(Matrix.Rotation(-y, 4, "Z") @ Vector((h.x, h.y, 0)))
    bpy.context.view_layer.update()


def rest_pose():
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
    arm.location = (0, 0, 0); arm.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()


g = lambda n: arm.matrix_world @ arm.pose.bones[n].head
imgs, clips = {}, {}
if "rest" in QA:
    rest_pose()
    clips["rest"] = clip_report()
    imgs["rest"] = views(os.path.join(OUT, "rest"), (0, 0, 0.78), 6, (0, 45, 90, 180), ortho=1.75, res=(560, 640))
    pose_from_clip(idle, 0)
    clips["idle"] = clip_report()
    imgs["idle"] = views(os.path.join(OUT, "idle"), (0, 0, 0.78), 6, (0, 45, 90, 180), ortho=1.75, res=(560, 640))
if "close" in QA:
    pose_from_clip(idle, 0)
    imgs["neck"] = views(os.path.join(OUT, "neck"), Vector((0, 0, A["SH_Z"])), 0.6, (0, 45, 90, 180), h_off=0.05)
    imgs["chest"] = views(os.path.join(OUT, "chest"), g("J_Bip_C_Chest") + Vector((0, 0, 0.05)), 0.9, (0, 30, -30))
    imgs["cuff"] = views(os.path.join(OUT, "cuff"), g("J_Bip_R_Hand"), 0.45, (0, 90, 180))
    ft = g("J_Bip_L_Foot")
    imgs["feet"] = views(os.path.join(OUT, "feet"), Vector((0, ft.y - 0.03, 0.10)), 0.8, (0, 45, 90), h_off=0.15)
    for key, fn, dist, angles in getattr(outfit, "EXTRA_CLOSEUPS", []):
        imgs[key] = views(os.path.join(OUT, key), fn(A, g), dist, angles)
if "motion" in QA:
    tests = (("walk", "male_standard_walk.fbx", "mid"), ("wave_both", "waving_both_hands.fbx", "top"),
             ("sit", "sitting_idle.fbx", 0), ("thumbs", "sitting_thumbsup.fbx", "top"),
             ("crouch", "crouch_idle.fbx", 0), ("kneel_mx", "kneeling_idle.fbx", 0))      # 蹲、單膝跪（2026-10-12 下載；沒檔案就跳過）
    for key, fbx, which in tests:
        if not os.path.exists(os.path.join(RAW, fbx)):
            continue
        clip = mr.retarget(mr.read_fbx(os.path.join(RAW, fbx)), tgt)
        if which == "mid":
            f = clip["n"] // 3
        elif which == "top":
            best = (-1e9, 0)
            for f_ in range(0, clip["n"], 2):
                pose_from_clip(clip, f_, 0)
                z = max(g(f"J_Bip_{s}_Hand").z for s in ("L", "R"))
                if z > best[0]:
                    best = (z, f_)
            f = best[1]
        else:
            f = which
        pose_from_clip(clip, f, 0)
        clips[key] = clip_report()
        imgs[key] = views(os.path.join(OUT, f"motion_{key}"), g("J_Bip_C_Spine") + Vector((0, 0, 0.12)), 2.6, (0, 45, 90), res=(560, 640))
    # 單膝跪蹲（攝影師蹲著拍照那種）：動作庫沒有這個 Mixamo 片段，用待機姿勢改腿自己擺。
    # 左大腿往前平舉、左小腿垂直（左腳踩地）；右大腿垂直、右小腿往後平放（右膝跪地）；上身前傾 15°
    pose_from_clip(idle, 0)

    def turn(name, deg):
        pb = arm.pose.bones[name]; h = pb.head.copy()
        pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, "X") @ Matrix.Translation(-h) @ pb.matrix
        bpy.context.view_layer.update()
    for name, deg in (("J_Bip_L_UpperLeg", -88), ("J_Bip_L_LowerLeg", 88), ("J_Bip_R_UpperLeg", -8), ("J_Bip_R_LowerLeg", 95),
                      ("J_Bip_R_Foot", 30), ("J_Bip_C_Spine", 15)):
        if name in arm.pose.bones:
            turn(name, deg)
    knee = g("J_Bip_R_LowerLeg").z
    arm.location.z -= knee - 0.045; bpy.context.view_layer.update()
    clips["kneel"] = clip_report()
    imgs["kneel"] = views(os.path.join(OUT, "motion_kneel"), g("J_Bip_C_Hips") + Vector((0, 0, 0.1)), 2.2, (0, 45, 90, 180), res=(560, 640))
    # 手到嘴邊：右手握叉子、叉尖送到嘴唇（和 zepeto-body 的身體檢查同一套姿勢，兩邊的測試圖才對得起來）
    R, hips = dict(idle["R"][0]), idle["hips"][0].copy(); hips.x = hips.y = 0
    mr.apply_pose(arm, tgt, R, hips); arm.location = (0, 0, 0); arm.rotation_euler = (0, 0, 0); bpy.context.view_layer.update()
    mouth = fr.matrix_world @ MOUTH_FILE
    appr = Vector((0.30, 0.85, 0.35)).normalized()             # 叉子從右前下方往嘴巴送（角色右手在 −X）
    palm = Vector((0.45, 0.0, -0.9)).normalized()              # 掌心朝下、朝身體中線
    FORK = 0.09                                                 # 食指根到叉尖（m）
    tip_goal = mouth - appr * 0.004
    wrist = tip_goal - appr * (FORK + 0.5 * HL)
    for _ in range(4):
        R2 = mr.arm_ik(tgt, R, hips, "R", wrist, Vector((-0.5, -0.15, -0.85)))
        R2 = mr.aim_hand(tgt, R2, hips, "R", appr, palm=palm)
        R2 = mr.gesture(tgt, R2, "R", "fork_grip")
        mr.apply_pose(arm, tgt, R2, hips); bpy.context.view_layer.update()
        i0 = g("J_Bip_R_Index1"); i3 = arm.matrix_world @ arm.pose.bones["J_Bip_R_Index3"].tail
        fd = (i3 - i0).normalized(); tip = i0 + fd * FORK
        wrist = wrist + (tip_goal - tip)
    bm = bmesh.new()
    d_ = (tip - fd * 0.025) - (i0 - fd * 0.03)
    g_ = bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.0028, radius2=0.0024, depth=d_.length)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(i0 - fd * 0.03 + d_ / 2) @ Vector((0, 0, 1)).rotation_difference(d_).to_matrix().to_4x4(), verts=g_["verts"])
    g_ = bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=1.0)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(tip - fd * 0.012) @ fd.to_track_quat("Y", "Z").to_matrix().to_4x4() @ Matrix.Diagonal((0.006, 0.006, 0.0015, 1)), verts=g_["verts"])
    me = bpy.data.meshes.new("QA_Fork"); bm.to_mesh(me); bm.free()
    fk = O.new("QA_Fork", me); sc.collection.objects.link(fk)
    me.materials.append(G.material("QA_ForkMat", (200, 200, 205), 0.3, metallic=1.0))
    clips["mouth"] = clip_report()
    imgs["mouth"] = views(os.path.join(OUT, "motion_mouth"), g("J_Bip_C_Head") + Vector((-0.05, 0, -0.15)), 1.2, (0, 45, 90))
    O.remove(fk, do_unlink=True)

info["clips"] = clips
info["imgs"] = imgs
info["total_sec"] = round(time.time() - T0, 1)
json.dump(info, open(os.path.join(OUT, "build.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("DONE", json.dumps(clips, ensure_ascii=False), info["total_sec"])
