# 整段數字檢查（頭髮、裙擺物理開啟，2026-10-09）：照 run_prod MODE=full 同一個物理迴圈（scene_lib.render_cast）再跑一次，
# 影格已經存在所以不重新渲染（skip_existing），每格只量：
#   - 兩個角色：手／前臂穿身體、雙手互穿、雙腿互穿、鞋底高度（check_lib.Checker）
#   - 裙擺穿腿：新娘腿的頂點（離地 15 cm 以上、骨盆以下）往外水平打射線，打不到任何裙子層＝腿露出裙外
#   - 物件之間：裙子×新郎、新郎×新娘身體、槌×新娘、槌×新郎（三角形穿插對數、最近距離）
#   "$BL" -b couple.blend -P prod_cli.py -- --run v2_phys_check SHOT=v2_02 RATE=24 RES=1280,720 OUT="D:/render-work/opening-v12/preview-v2"
#   → <OUT>/shots/<幕>/phys_check.json，主控台印每格與摘要
import bpy, os, json, time
from mathutils import Vector
from mathutils.bvhtree import BVHTree

MODE = "setup"
use("run_prod")
sid = str(globals().get("SHOT", "v2_02"))
S = SHOTS[sid]; S["build"](); stage(S["set"], cast=S.get("cast", False))
res = tuple(int(x) for x in str(globals().get("RES", "1280,720")).split(","))
root = os.path.join(globals().get("OUT") or PWORK, "shots", sid)
frames_dir = os.path.join(root, "beauty")
n = int(round(S["dur"] * FPS)) + int(S.get("tail", 0) * FPS)
miss = [i for i in range(n) if not os.path.exists(os.path.join(frames_dir, f"{i + 1:04d}.png"))]
assert not miss, f"影格還沒齊（缺 {len(miss)} 格），這支只跑物理不渲染"
T0 = S.get("t0", 0.0); actors = S.get("actors", [])
CAST = [("groom", GR), ("bride", B)]
for who, ns in CAST:
    if "Checker" not in ns:
        ns["use"]("check_lib")
CHK = {who: ns["Checker"](ns["ARM"], ns["WHO"]) for who, ns in CAST}
for who, ns in CAST:
    cs = bpy.data.objects.get(ns["WHO"] + "_Cos_Shoes")
    if cs is not None:
        CHK[who].shoes = cs
SKIRT = ("bride_Cos_Tulle", "bride_Cos_Frill", "bride_Cos_Peplum", "bride_Cos_Lining", "bride_Cos_Ruffle", "bride_Cos_Cascade", "bride_Cos_Petal")
SKIP = ("_SRC", "_BaseTop", "_Tee", "_Shorts")


def objs(prefixes, exclude=SKIP):
    return [o for o in bpy.data.objects if o.type == "MESH" and not o.hide_render
            and any(o.name.startswith(p) for p in prefixes) and not any(x in o.name for x in exclude)]


def bvh_world(obs):
    dg = bpy.context.evaluated_depsgraph_get(); V, F = [], []
    for o in obs:
        oe = o.evaluated_get(dg); me = oe.to_mesh(); M = oe.matrix_world
        b = len(V); V += [M @ v.co for v in me.vertices]; F += [tuple(b + i for i in p.vertices) for p in me.polygons]
        oe.to_mesh_clear()
    return (BVHTree.FromPolygons(V, F), V) if F else (None, V)


def min_dist(bB, VA, step=3):
    best = 9.0
    for v in VA[::step]:
        r = bB.find_nearest(v)
        if r[0] is not None:
            best = min(best, r[3])
    return best


# 新娘腿的頂點（身體網格裡主要權重在大腿／小腿的頂點，每 4 個取 1 個）
body_b = bpy.data.objects["bride_Body"]
leg_idx = [i for i, c in enumerate(_dominant(body_b)) if ("UpperLeg" in c or "LowerLeg" in c)][::4] if "_dominant" in B else []
if not leg_idx:
    B["use"]("check_lib")
    leg_idx = [i for i, c in enumerate(B["_dominant"](body_b)) if ("UpperLeg" in c or "LowerLeg" in c)][::4]
PAIRS = [("skirt×groom", SKIRT, ("groom_",)), ("groom×bride_body", ("groom_",), ("bride_Body", "bride_Hair", "bride_Face", "bride_Cos_Bodice")),
         ("mallet×bride", ("V2_Mallet",), ("bride_",)), ("mallet×groom", ("V2_Mallet",), ("groom_",))]
rows = []


def skirt_leg(t):
    dg = bpy.context.evaluated_depsgraph_get()
    oe = body_b.evaluated_get(dg); me = oe.to_mesh(); M = oe.matrix_world
    pts = [M @ me.vertices[i].co for i in leg_idx]; oe.to_mesh_clear()
    hips = ARM.matrix_world @ ARM.pose.bones["J_Bip_C_Hips"].head
    sb, _ = bvh_world(objs(SKIRT))
    out = 0; worst = None
    for p in pts:
        if p.z < 0.15 or p.z > hips.z:
            continue
        d = Vector((p.x - hips.x, p.y - hips.y, 0.0))
        if d.length < 1e-4:
            continue
        hit = sb.ray_cast(p, d.normalized(), 1.0)
        if hit[0] is None:
            out += 1; worst = tuple(round(x, 3) for x in p)
    return dict(legs_out=out, legs_out_at=worst)


def on_frame(i):
    t = T0 + i / FPS
    bpy.context.view_layer.update()
    r = dict(t=round(t, 3))
    for who, ns in CAST:
        mesh_eval(True, ns["ARM"].name)
        c = CHK[who].frame()
        r[who] = dict(pen_core=round(c["pen_core"], 1), pen_hands=round(c["pen_hands"], 1), pen_legs=round(c["pen_legs"], 1),
                      foot_min_cm=round(c["foot_min"] * 100, 2))
    for who, ns in CAST:
        mesh_eval(True, ns["ARM"].name)
    r.update(skirt_leg(t))
    for name, pa, pb in PAIRS:
        A_, B_ = objs(pa), objs(pb)
        bA, vA = bvh_world(A_); bB, vB = bvh_world(B_)
        if bA is None or bB is None:
            continue
        r[name] = dict(overlap=len(bA.overlap(bB)), min_mm=round(min_dist(bB, vA) * 1000, 1))
    for who, ns in CAST:
        mesh_eval(False, ns["ARM"].name)
    rows.append(r)
    print("PHYS", json.dumps(r, ensure_ascii=False), flush=True)


def pose_fn(f):
    S["frame"](T0 + f / FPS, props=True, cast=True, cam=False)


def cam_fn(i):
    S["frame"](T0 + i / FPS, props=False, cast=False, cam=True)


for A in (ARM, G["ARM"]):
    mesh_eval(False, A.name)
t0 = time.time()
sk = skirts_of(actors) if S.get("skirt", True) else []
render_cast(frames_dir, n, pose_fn, cam_fn, arms_of(actors), skirts=sk, fps=FPS, res=res, on_frame=on_frame, skip_existing=True)
json.dump(rows, open(os.path.join(root, "phys_check.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)


def mx(key, sub=None, f=max):
    v = [(r[key][sub] if sub else r[key]) for r in rows if key in r and (sub is None or sub in r[key])]
    v = [x for x in v if x is not None]
    return (f(v), [r["t"] for r in rows if key in r and (r[key][sub] if sub else r[key]) == f(v)][:5]) if v else None


summ = {}
for who in ("groom", "bride"):
    for k in ("pen_core", "pen_hands", "pen_legs"):
        summ[f"{who}.{k}"] = mx(who, k)
    summ[f"{who}.foot_min_cm"] = mx(who, "foot_min_cm", min)
summ["legs_out"] = mx("legs_out")
for name, _, _ in PAIRS:
    summ[name + ".overlap"] = mx(name, "overlap")
    summ[name + ".min_mm"] = mx(name, "min_mm", min)
json.dump(summ, open(os.path.join(root, "phys_check_summary.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("PHYS_SUM", json.dumps(summ, ensure_ascii=False), flush=True)
print("PHYS_DONE", n, "frames", round(time.time() - t0, 1), "s", flush=True)
