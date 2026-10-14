# ZEPETO 動畫工作流的核心（2026-10-12 由 B1→B2 的 b12_mcp 抽出共通部分）：
#   開工作場景、附加角色、攝影棚 → 讀 Mixamo → 接段 → 每格姿勢（STATE["poses"]）→ 擺到第 t 秒 → 拍近照 → 清場景。
# 不動使用者目前的場景：另開工作場景、把角色附加進來；渲染用 temp_override 指定這個場景；做完 cleanup() 整個刪掉。
# 每一步控制在 MCP 單次 120 秒內；中間結果放在 STATE（GUI Blender 的 Python 一直開著，下一次呼叫接著用）。
#
# 每一鏡的程式（.claude/docs/data/blender/zepeto/anim/<片名>/<鏡>/<鏡>_shot.py）用這裡的函式，
# 道具要跟著每一格動時，把函式加進 POSE_HOOKS（pose_at 擺好骨架後呼叫 hook(i)）；
# 拍照時要跟鏡頭位置有關的（例：星星轉向鏡頭）加進 CAM_HOOKS（hook(鏡頭位置)）。
#
# MCP 用法：
#   # BODY=groom    ← 身體出廠閘門只核對點名的身體
#   import sys; sys.path.insert(0, r"D:/SideProject/wedding-invitation/.claude/skills/zepeto-animation-generation-workflow/scripts")
#   import zanim as Z; Z.use_shot("opening-proposal-b", "b1_b2"); import b1b2_shot as S; S.run()
import bpy, os, sys, math, json, time
from mathutils import Vector, Quaternion, Matrix
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import zanim_lib as L
mr = L.mr

REPO = r"D:/SideProject/wedding-invitation"
SHOTS = REPO + "/.claude/docs/data/blender/zepeto/anim"          # 每一鏡的程式、規格、定案參數（進版控）
WORK = r"D:/render-work/zepeto-anim"                               # 圖、確認頁、樣張（不進版控）
RELEASE = r"D:/render-work/zepeto-body/build/RELEASE.json"
SKIP = {"Sun", "Rim", "Fill", "Floor", "Camera"}
STATE = globals().setdefault("STATE", {})
POSE_HOOKS = globals().setdefault("POSE_HOOKS", [])
CAM_HOOKS = globals().setdefault("CAM_HOOKS", [])


def use_shot(film, shot):
    """把這一鏡的程式資料夾加進 import 路徑，回傳 (程式資料夾, 輸出資料夾)"""
    d = f"{SHOTS}/{film}/{shot}"
    if d not in sys.path:
        sys.path.insert(0, d)
    out = f"{WORK}/{film}/{shot}"
    os.makedirs(out, exist_ok=True)
    return d, out


def body_blend(name):
    """已出廠身體的 .blend（讀 RELEASE.json；沒出廠就報錯，閘門也會擋）"""
    r = json.load(open(RELEASE, encoding="utf8"))
    b = r["bodies"][name]
    if b.get("status", r.get("status")) != "released":
        raise RuntimeError(f"身體 {name} 還沒出廠")
    return b["path"]


def _ctx(sc):
    return dict(scene=sc, view_layer=sc.view_layers[0], collection=sc.collection)


class in_scene:
    """在同一次呼叫裡暫時把視窗切到 sc（FBX 匯入器只認視窗正在顯示的場景），結束立刻切回原場景。
    MCP 的一次呼叫在 Blender 主執行緒裡一口氣跑完，中間不重畫，使用者看不到切換。背景 Blender 沒有視窗，直接跑"""
    def __init__(self, sc):
        self.sc = sc; self.win = getattr(bpy.context, "window", None); self.prev = None

    def __enter__(self):
        if self.win is not None:
            self.prev = self.win.scene; self.win.scene = self.sc
        return self

    def __exit__(self, *a):
        if self.win is not None and self.prev is not None:
            self.win.scene = self.prev
        return False


# ════════ 1. 場景 ════════
def setup(body="groom", scene="ANIM_WORK", prefix="ZA_", res=(640, 640), blend=None):
    """開工作場景、附加角色（已出廠的 body.blend，只讀不存）、攝影棚。prefix：攝影棚物件、集合的名稱前綴"""
    blend = blend or body_blend(body)
    POSE_HOOKS.clear(); CAM_HOOKS.clear()
    if scene in bpy.data.scenes:
        sc = bpy.data.scenes[scene]
    else:
        sc = bpy.data.scenes.new(scene)
        with bpy.data.libraries.load(blend, link=False) as (src, dst):
            dst.objects = [n for n in src.objects if n not in SKIP]
        col = bpy.data.collections.new(prefix + "char"); sc.collection.children.link(col)
        for o in dst.objects:
            if o is not None:
                col.objects.link(o)
        for o in col.objects:                             # 原檔藏起來的（控制骨架形狀）照藏
            if o.name.startswith("WGT"):
                o.hide_render = True; o.hide_viewport = True
        _studio(sc, prefix)
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.render.fps = 30
    arm = L.find_arm(sc)
    STATE.update(sc=sc, scene=scene, prefix=prefix, body=body, arm=arm, tgt=mr.Target(arm), added=[o.name for o in sc.objects])
    STATE["measure"] = L.measure(arm, STATE["tgt"])
    return STATE["measure"]


def _studio(sc, prefix):
    try:
        sc.render.engine = "BLENDER_EEVEE"
    except TypeError:
        pass
    sc.eevee.taa_render_samples = 16
    sc.view_settings.view_transform = "Standard"; sc.view_settings.exposure = -0.5
    w = bpy.data.worlds.new(prefix + "World"); sc.world = w
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (0.93, 0.91, 0.89, 1)
    col = bpy.data.collections.new(prefix + "studio"); sc.collection.children.link(col)

    def light(name, kind, loc, rot, e, size=None):
        o = bpy.data.objects.new(name, bpy.data.lights.new(name, kind)); col.objects.link(o)
        o.location = loc; o.rotation_euler = [math.radians(a) for a in rot]; o.data.energy = e
        if size:
            o.data.size = size
        return o
    light(prefix + "Sun", "SUN", (2, -4, 5), (50, 0, 20), 2.5)
    light(prefix + "Fill", "AREA", (-3, -3, 2.5), (60, 0, -45), 250, 3)
    light(prefix + "Rim", "AREA", (1.5, 3.0, 2.6), (-60, 0, 155), 200, 2)
    # 地板：淺色棋盤（每 0.5 m 一格，看腳有沒有滑）
    me = bpy.data.meshes.new(prefix + "Floor"); me.from_pydata([(-3, -3, 0), (15, -3, 0), (15, 3, 0), (-3, 3, 0)], [], [(0, 1, 2, 3)])
    fl = bpy.data.objects.new(prefix + "Floor", me); col.objects.link(fl)
    m = bpy.data.materials.new(prefix + "FloorMat")
    nt = m.node_tree; p = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tc = nt.nodes.new("ShaderNodeTexCoord"); ck = nt.nodes.new("ShaderNodeTexChecker")
    ck.inputs["Scale"].default_value = 1.0
    ck.inputs["Color1"].default_value = (0.62, 0.58, 0.55, 1); ck.inputs["Color2"].default_value = (0.52, 0.49, 0.46, 1)
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (2, 2, 2)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], ck.inputs["Vector"])
    nt.links.new(ck.outputs["Color"], p.inputs["Base Color"]); p.inputs["Roughness"].default_value = 0.9
    me.materials.append(m)
    cam = bpy.data.objects.new(prefix + "Cam", bpy.data.cameras.new(prefix + "Cam")); col.objects.link(cam); sc.camera = cam


def studio_col():
    return bpy.data.collections[STATE["prefix"] + "studio"]


# ════════ 2. 動作 ════════
def load_clips(names):
    """讀 Mixamo 並重定向（匯入暫存在工作場景，不經過使用者的場景）。names：D:/render-work/mixamo/raw/ 底下的檔名（不含 .fbx）"""
    sc, tgt = STATE["sc"], STATE["tgt"]
    t0 = time.time(); out = {}
    with in_scene(sc):
        for n in names:
            if n not in L._CL:
                L.clip(tgt, n)
            out[n] = mr.summarize(L._CL[n])
    out["sec"] = round(time.time() - t0, 1)
    return out


def sequence(plan, lock=False):
    """plan：{segs: [mr.Seg…], blend: 秒, anchor: (秒, (x, y), 面向°), post: 選用 (t, R, h) → (R, h)}
    → 接成一條，STATE["poses"]＝每格 (R, hips)；回傳每段的起點與長度"""
    import zanim_fix as F
    tgt = STATE["tgt"]
    seq = mr.Sequence(tgt, plan["segs"], blend=plan.get("blend", 0.3))
    ta, xy, yaw = plan["anchor"]; seq.place(ta, xy, yaw)
    n = int(seq.dur * L.FPS) + 1
    poses, labels = [], []
    for i in range(n):
        R, h, _y = seq.at(i / L.FPS)
        if plan.get("post"):
            R, h = plan["post"](i / L.FPS, R, h)
        poses.append((R, h)); labels.append(seq.which(i / L.FPS))
    if lock:
        poses, li = F.foot_lock(tgt, poses, L.sole_points(STATE["arm"]))
        STATE["lock"] = li
    STATE.update(seq=seq, poses=poses, labels=labels,
                 segs=[(round(seq.T[i][0], 2), round(s.dur, 2), s.name) for i, s in enumerate(plan["segs"])])
    return dict(frames=n, dur=round(seq.dur, 2), segs=STATE["segs"])


# ════════ 3. 檢查數字（共用） ════════
def _head_bvh():
    """頭網格（評估後）轉到頭骨 rest 局部座標建 BVH：之後每格把手的點轉進頭骨座標查「在不在頭裡面」"""
    if "head_bvh" in STATE:
        return STATE["head_bvh"]
    arm = STATE["arm"]
    hd = L.head_mesh(arm)
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
    arm.location = (0, 0, 0); arm.rotation_euler = (0, 0, 0)
    vl = STATE["sc"].view_layers[0]; vl.update()
    oe = hd.evaluated_get(vl.depsgraph); me = oe.to_mesh()
    Mi = (arm.matrix_world @ arm.data.bones["J_Bip_C_Head"].matrix_local).inverted() @ hd.matrix_world
    V = [Mi @ v.co for v in me.vertices]; F = [tuple(p.vertices) for p in me.polygons]
    oe.to_mesh_clear()
    STATE["head_bvh"] = BVHTree.FromPolygons(V, F)
    return STATE["head_bvh"]


def _inside(bvh, p):
    loc, nrm, _i, d = bvh.find_nearest(p)
    if loc is None:
        return False, 9.9
    if d > 0.13:
        return False, d
    # 法線判斷＋往上、往前、往後三條射線都要打到頭（頭底部是開口：只靠法線會把頸部下方的點誤判成在裡面）
    if (p - loc).dot(nrm) >= 0:
        return False, d
    hits = sum(1 for v in (Vector((0, 0, 1)), Vector((0, 1, 0)), Vector((0, -1, 0))) if bvh.ray_cast(p, v)[0] is not None)
    return hits == 3, d


HAND_PTS = ["J_Bip_{s}_Hand", "J_Bip_{s}_Index3", "J_Bip_{s}_Middle3", "J_Bip_{s}_Thumb3", "J_Bip_{s}_LowerArm"]


def stats():
    """滑步、腳底高度、手離頭（骨頭估），依 sequence() 的段彙整"""
    tgt, poses = STATE["tgt"], STATE["poses"]
    pts = L.sole_points(STATE["arm"])
    rows = L.contact_stats(poses, tgt, pts)
    bvh = _head_bvh()
    worst_head = (9.9, None, None)
    for i, (R, h) in enumerate(poses):
        Hd = tgt.fk(R, h)
        Mi = (Matrix.Translation(Hd["J_Bip_C_Head"]) @ R["J_Bip_C_Head"].to_matrix().to_4x4()).inverted()   # 骨架空間 → 頭骨局部（和 BVH 同一套）
        for s in "LR":
            for tmpl in HAND_PTS:
                b = tmpl.format(s=s)
                p = Hd[b] if not b.endswith("3") else tgt.tail(R, Hd, b)
                ins, d = _inside(bvh, Mi @ p)
                sd = -d if ins else d
                if sd < worst_head[0]:
                    worst_head = (sd, i, b)
        rows[i]["hips"] = tuple(h)
    STATE["rows"] = rows
    seg_rows = []
    if "seq" in STATE:
        T = STATE["seq"].T
        for k, (t0, dur, name) in enumerate(STATE["segs"]):
            a = int(round(t0 * 30)); b = int(round((T[k + 1][0] if k + 1 < len(T) else STATE["seq"].dur) * 30))
            rr = rows[a:b + 1]
            sl = [r["slide" + s] for r in rr for s in "LR" if r["slide" + s] is not None]
            low = [min(r["lowL"], r["lowR"]) for r in rr]
            seg_rows.append(dict(seg=name, t=(round(a / 30, 2), round(b / 30, 2)), slide_max_mm=round(max(sl), 2) if sl else 0,
                                 slide_frames_over_1mm=sum(1 for x in sl if x > 1.0),
                                 low_min_mm=round(1000 * min(low), 1), low_max_mm=round(1000 * max(low), 1)))
    sl_all = [(r["slide" + s], r["i"], s) for r in rows for s in "LR" if r["slide" + s] is not None]
    worst = max(sl_all) if sl_all else (0, 0, "")
    summary = dict(slide_worst_mm=round(worst[0], 2), slide_worst_at=round(worst[1] / 30, 2), slide_worst_foot=worst[2],
                   frames_slide_over_1mm=sum(1 for x in sl_all if x[0] > 1.0),
                   sole_low_min_mm=round(1000 * min(min(r["lowL"], r["lowR"]) for r in rows), 1),
                   sole_low_max_mm=round(1000 * max(min(r["lowL"], r["lowR"]) for r in rows), 1),
                   hand_head_min_mm=round(1000 * worst_head[0], 1), hand_head_at=round((worst_head[1] or 0) / 30, 2), hand_head_pt=worst_head[2])
    return dict(summary=summary, segments=seg_rows)


# ════════ 4. 擺姿勢、拍近照 ════════
def pose_at(t):
    """擺到第 t 秒：骨架＋POSE_HOOKS（道具等）"""
    i = max(0, min(len(STATE["poses"]) - 1, int(round(t * 30))))
    R, h = STATE["poses"][i]
    mr.apply_pose(STATE["arm"], STATE["tgt"], R, h)
    for hk in POSE_HOOKS:
        hk(i)
    STATE["sc"].view_layers[0].update()
    return i


def _aim(cam, loc, target, lens):
    cam.location = loc; cam.data.lens = lens
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


def bone_world(n):
    arm = STATE["arm"]
    return arm.matrix_world @ arm.pose.bones[n].head


def render_still(path):
    sc = STATE["sc"]
    sc.render.image_settings.file_format = "JPEG"
    sc.render.filepath = path
    with bpy.context.temp_override(**_ctx(sc)):
        bpy.ops.render.render(write_still=True, scene=sc.name)
    return path


def shots(times, focus="J_Bip_C_Hips", dist=1.6, out=None, views=None, dz=0.0, lens=50, up=0.12):
    """每個時刻、每個角度一張：<秒>_<角度>.jpg。
    focus：骨頭名，或 callable(i)→世界座標；views：[(名稱, 方位角°)]（0＝從 −Y 看、90＝從 +X 看）或 [(名稱, (dx, dy, dz) 偏移)]"""
    sc = STATE["sc"]; cam = sc.camera
    views = views or [("main", 0), ("front", 90), ("side", 35)]
    out = out or STATE.get("out_dir", WORK) + "/close"
    os.makedirs(out, exist_ok=True)
    t0 = time.time(); done = []
    for t in times:
        i = pose_at(t)
        c = (focus(i) if callable(focus) else bone_world(focus)) + Vector((0, 0, dz))
        for name, az in views:
            if isinstance(az, tuple):
                loc = c + Vector(az)
            else:
                r = math.radians(az); loc = c + Vector((math.sin(r) * dist, -math.cos(r) * dist, up * dist))
            _aim(cam, loc, c, lens)
            for hk in CAM_HOOKS:
                hk(loc)
            done.append(render_still(os.path.join(out, "%05.2f_%s.jpg" % (t, name))))
    return dict(n=len(done), sec=round(time.time() - t0, 1), out=out)


def cleanup(scene=None):
    """刪掉工作場景與附加進來的物件、資料（使用者原本的場景不受影響）"""
    scene = scene or STATE.get("scene")
    sc = bpy.data.scenes.get(scene) if scene else None
    if not sc:
        return "none"
    prefix = STATE.get("prefix", "ZA_")
    objs = list(sc.collection.all_objects)
    others = [s for s in bpy.data.scenes if s != sc]

    def only_here(c):                                     # 集合沒有 users_scene：看其他場景有沒有用到它
        return not any(c in s.collection.children_recursive for s in others)
    for col in list(sc.collection.children):
        if col.name.startswith(prefix) or only_here(col):
            for sub in list(col.children_recursive):      # 底下複製進來的場景、道具集合也一起刪（留著會變成空集合，下次載入會沿用）
                if only_here(sub):
                    bpy.data.collections.remove(sub)
            bpy.data.collections.remove(col)
    for o in objs:
        if o.users_scene == () or all(s.name == scene for s in o.users_scene):
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.scenes.remove(sc)
    for c in list(bpy.data.collections):                  # 道具集合實例（例 ZP_buffet_table）的來源集合：物件刪了就沒人用，留著下次載入會沿用
        if c.users == 0 and not c.library:
            bpy.data.collections.remove(c)
    for a in list(bpy.data.actions):
        if a.users == 0:
            bpy.data.actions.remove(a)
    STATE.clear(); POSE_HOOKS.clear(); CAM_HOOKS.clear()
    return "removed"
