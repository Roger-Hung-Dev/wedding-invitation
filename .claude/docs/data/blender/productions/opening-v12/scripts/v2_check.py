# 情境版的幾何檢查（背景 Blender）：擺到指定秒數、用「變形後」的網格量道具與角色之間的穿插與距離。
#   "$BL" -b couple.blend -P prod_cli.py -- --run v2_check SHOT=v2_02 KEYS=5.3,6.0 [RATE=24]
# 每一幕要量什麼寫在 CHECKS[幕]：pairs＝(名稱, 物件前綴 A, 物件前綴 B) → 穿插的三角形對數、最近距離；extra(t)＝自訂量測（回傳 dict）。
import bpy, math, json, time
from mathutils import Vector
from mathutils.bvhtree import BVHTree

MODE = "setup"
use("run_prod")                               # 只做共用的設定（prod_env、景、幕），不渲染

dg_ = lambda: bpy.context.evaluated_depsgraph_get()


def objs(prefixes, exclude=()):
    out = []
    for o in bpy.data.objects:
        if o.type != "MESH" or o.hide_render:
            continue
        if any(o.name.startswith(p) for p in prefixes) and not any(x in o.name for x in exclude):
            out.append(o)
    return out


def bvh_world(obs):
    dg = dg_(); V, F = [], []
    for o in obs:
        oe = o.evaluated_get(dg); me = oe.to_mesh(); M = oe.matrix_world
        b = len(V); V += [M @ v.co for v in me.vertices]; F += [tuple(b + i for i in p.vertices) for p in me.polygons]
        oe.to_mesh_clear()
    return (BVHTree.FromPolygons(V, F), V) if F else (None, V)


def min_dist(bA, VA, bB, VB, step=3):
    """A 的頂點到 B 表面的最近距離（每 step 個頂點取一個）"""
    best = 9.0
    if bB is None:
        return best
    for v in VA[::step]:
        r = bB.find_nearest(v)
        if r[0] is not None:
            best = min(best, r[3])
    return best


CHECKS = {}

_CAST_SKIP = ("_SRC", "_BaseTop", "_Tee", "_Shorts")       # 便服、原始檔不量（服裝版看不到）


def _ch_02(t):
    S = V2S["02"]; out = {}
    head = objs(("V2_MalletHeadMesh",)); hb, hv = bvh_world(head)
    if hv and not bpy.data.objects["V2_MalletHeadMesh"].hide_render:
        out["mallet_top_z"] = round(max(v.z for v in hv), 3)
        gh, gv = bvh_world(objs(("groom_Hair", "groom_HairBack")))
        out["groom_hair_top_z"] = round(max(v.z for v in gv), 3)
        out["mallet_to_groom_hair_mm"] = round(min_dist(hb, hv, gh, gv, 1) * 1000, 1)
    cl = sc.camera.matrix_world.translation
    out["groom_face_blocked"] = face_blocked(GR, "groom_", cl); out["bride_face_blocked"] = face_blocked(B, "bride_", cl)
    return out


CHECKS["v2_02"] = dict(pairs=[("mallet×groom", ("V2_Mallet",), ("groom_",)), ("mallet×bride", ("V2_Mallet",), ("bride_",)),
                              ("stars×groom", ("V2_Star",), ("groom_",)),
                              ("bride_skirt×groom", ("bride_Cos_Tulle", "bride_Cos_Frill", "bride_Cos_Peplum", "bride_Cos_Lining", "bride_Cos_Ruffle", "bride_Cos_Cascade", "bride_Cos_Petal"), ("groom_",)),
                              ("groom×bride_body", ("groom_",), ("bride_Body", "bride_Hair", "bride_Face", "bride_Cos_Bodice"))],
                       extra=_ch_02)

def _ch_07(t):
    S = V2S["07"]; out = {}
    O = bpy.data.objects
    Mf = O["V2_Fork"].matrix_world; tip = Mf @ Vector((0, 0, 0.115))
    if t < 4.5:
        out["fork_tip_to_mouth_mm"] = round((tip - S["FD"].mouth_world(t / 4.5)).length * 1000, 1)
    cg = O["V2_Wine_groom"].matrix_world @ Vector((0, 0, 0.085)); cb = O["V2_Wine_bride"].matrix_world @ Vector((0, 0, 0.085))
    out["bowl_centers_mm"] = round((cg - cb).length * 1000, 1)
    gb, gv = bvh_world([O["V2_Wine_groom"]]); bb, bv = bvh_world([O["V2_Wine_bride"]])
    out["glass_overlap"] = len(gb.overlap(bb)); out["glass_gap_mm"] = round(min_dist(gb, gv, bb, bv, 1) * 1000, 1)
    if globals().get("FACES"):                                  # 臉有沒有被酒瓶、酒杯、叉子、對方擋住（每張臉 15 點射線）
        cl = sc.camera.matrix_world.translation
        out["groom_face_blocked"] = face_blocked(GR, "groom_", cl); out["bride_face_blocked"] = face_blocked(B, "bride_", cl)
    return out


CHECKS["v2_07"] = dict(pairs=[("bride×chairB", ("bride_",), ("V2_ChairB",)), ("groom×chairG", ("groom_",), ("V2_ChairG",)),
                              ("bride×table_items", ("bride_",), ("V2_Wine_groom", "V2_Wine_bride", "V2_Fork", "V2_Main", "V2_Dessert", "V2_Fruit", "V2_WineBottle", "V2_Napkin", "V2_Easel", "V2_Board")),
                              ("groom×table_items", ("groom_",), ("V2_Wine_groom", "V2_Wine_bride", "V2_Fork", "V2_Main", "V2_Dessert", "V2_Fruit", "V2_WineBottle", "V2_Napkin")),
                              ("groom×bride", ("groom_",), ("bride_",))],
                       extra=_ch_07)

def face_blocked(ns, owner, cam_loc):
    """從鏡頭往這個人臉上的 15 個點打射線（臉前方、rest 骨架空間換到世界），回傳被誰擋住：{物件名稱: 被擋的點數}"""
    A = ns["ARM"]; k = ns["BODY_S"]
    Mh = world_of_rest(ns, "J_Bip_C_Head")
    h0 = A.data.bones["J_Bip_C_Head"].head_local
    dg = dg_(); out = {}
    for dx in (-0.035, 0.0, 0.035):
        for dz in (0.03, 0.06, 0.09, 0.12, 0.15):
            p = Mh @ (h0 + Vector((dx, -0.085, dz)) * k)
            d = p - cam_loc; L = d.length
            hit, loc, nrm, idx, ob, M = sc.ray_cast(dg, cam_loc, d.normalized(), distance=L - 0.03)
            if hit and ob is not None and not ob.name.startswith(owner):
                out[ob.name] = out.get(ob.name, 0) + 1
    return out


def _ch_05(t):
    S = V2S["05"]; out = {}
    cl = sc.camera.matrix_world.translation
    if t >= S["t_in"]:
        out["groom_face_blocked"] = face_blocked(GR, "groom_", cl)
        out["bride_face_blocked"] = face_blocked(B, "bride_", cl)
        ph = objs(("V2_PhoneMesh",)); hb, hv = bvh_world(ph)
        if hb:
            hands = [o for o in objs(("passerby_Body",))]
            bb, bv = bvh_world(hands)
            out["phone_to_passerby_body_mm"] = round(min_dist(hb, hv, bb, bv, 1) * 1000, 1)
    return out


CHECKS["v2_05"] = dict(pairs=[("passerby×groom", ("passerby_",), ("groom_",)), ("passerby×bride", ("passerby_",), ("bride_",)),
                              ("passerby×oldcam", ("passerby_",), ("G_Tripod", "G_OldCam")), ("phone×passerby", ("V2_PhoneMesh",), ("passerby_",))],
                       extra=_ch_05)

sid = str(globals().get("SHOT"))
S = SHOTS[sid]
S["build"](); stage(S["set"], cast=True)
arms = [a.ns["ARM"] for a in S.get("actors", [])] or [ARM, G["ARM"]]
for A in arms:
    mesh_eval(True, A.name)
C = CHECKS.get(sid, dict(pairs=[], extra=None))
rows = {}
VAR = globals().get("VARIANTS") or [None]                 # VARIANTS='[{"gx":-0.3},…]'：同一次執行比較好幾組站位（改 V2_<幕> 的值）
jobs = []
for var in VAR:
    for t in [float(k) for k in (globals().get("KEYS") or S.get("stills", [0.0]))]:
        jobs.append((var, t))
cur = "init"
for var, t in jobs:
    if var != cur:
        cur = var
        if var:
            globals()["V2_" + sid[3:]].update(var); V2S.pop(sid[3:], None); S["build"]()
            print("VARIANT", json.dumps(var), flush=True)
    t0 = time.time()
    S["frame"](t); bpy.context.view_layer.update()
    r = {}
    only = [x for x in str(globals().get("ONLY") or "").split("|") if x]       # ONLY="名稱|名稱"：只量這幾組（逐格量時省時間）
    for name, pa, pb in C["pairs"]:
        if only and name not in only:
            continue
        A_ = objs(pa, _CAST_SKIP); B_ = objs(pb, _CAST_SKIP)
        bA, vA = bvh_world(A_); bB, vB = bvh_world(B_)
        if bA is None or bB is None:
            continue
        ov = bA.overlap(bB)
        r[name] = dict(overlap=len(ov), min_mm=round(min_dist(bA, vA, bB, vB) * 1000, 1))
        if ov and globals().get("DETAIL"):                  # 哪兩個物件在穿插
            det = {}
            for oa in A_:
                ba, _ = bvh_world([oa])
                for ob in B_:
                    bb, _ = bvh_world([ob])
                    if ba and bb:
                        n = len(ba.overlap(bb))
                        if n:
                            det[f"{oa.name}|{ob.name}"] = n
            r[name]["by"] = det
    if C.get("extra"):
        r.update(C["extra"](t))
    rows[t] = r
    print("CHECK", sid, f"{t:.2f}", json.dumps(r, ensure_ascii=False), round(time.time() - t0, 1), "s", flush=True)
print("CHECK_DONE", sid)
