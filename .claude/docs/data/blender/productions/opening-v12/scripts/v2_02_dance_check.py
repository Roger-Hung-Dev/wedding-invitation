# ② 跳舞版（2026-10-10 第 5 輪）網格檢查（不跑物理＝快速預覽的狀態）：每 STEP 秒量
#   - legs_out：新娘腿的頂點（離地 15 cm 以上、骨盆以下）往外水平打射線，打不到任何裙子層＝腿從裙子露出來
#   - hands_in：新娘手（前臂＋手掌）的頂點，在骨盆以下、從頂點往外水平打射線會打到裙子＝手在裙子裡面
#   - skirt×groom、groom×bride：兩個網格之間最近距離（cm；0＝碰到或穿插）＋ 三角形互相穿插的對數
#   "$BL" -b couple.blend -P prod_cli.py -- --run v2_02_dance_check RATE=24 [T0=3.8] [T1=9.0] [STEP=0.0833]
import bpy, os, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

MODE = "setup"
use("run_prod")
S = SHOTS["v2_02"]; S["build"](); stage(S["set"], cast=True)
for o in (ARM, G["ARM"]):
    mesh_eval(True, o.name)
if "_dominant" not in B:
    B["use"]("check_lib")
SKIRT = ("bride_Cos_Tulle", "bride_Cos_Frill", "bride_Cos_Peplum", "bride_Cos_Lining", "bride_Cos_Ruffle", "bride_Cos_Cascade", "bride_Cos_Petal")
SKIP = ("_SRC", "_BaseTop", "_Tee", "_Shorts")
body_b = bpy.data.objects["bride_Body"]
dom = B["_dominant"](body_b)
leg_idx = [i for i, c in enumerate(dom) if ("UpperLeg" in c or "LowerLeg" in c)][::4]
hand_idx = [i for i, c in enumerate(dom) if ("LowerArm" in c or "_Hand" in c or "Index" in c or "Middle" in c or "Thumb" in c or "Ring" in c or "Little" in c)][::3]


def objs(prefixes):
    return [o for o in bpy.data.objects if o.type == "MESH" and not o.hide_render
            and any(o.name.startswith(p) for p in prefixes) and not any(x in o.name for x in SKIP)]


def bvh_world(obs):
    dg = bpy.context.evaluated_depsgraph_get(); V, F = [], []
    for o in obs:
        oe = o.evaluated_get(dg); me = oe.to_mesh(); M = oe.matrix_world
        b = len(V); V += [M @ v.co for v in me.vertices]; F += [tuple(b + i for i in p.vertices) for p in me.polygons]
        oe.to_mesh_clear()
    return BVHTree.FromPolygons(V, F), V


def min_dist(bB, VA, step=4):
    best = 9.0
    for v in VA[::step]:
        r = bB.find_nearest(v)
        if r[0] is not None:
            best = min(best, r[3])
    return best


rows = []
t0 = float(globals().get("T0", 3.8)); t1 = float(globals().get("T1", 9.0)); st = float(globals().get("STEP", 1 / 12))
t = t0
while t <= t1 + 1e-6:
    S["frame"](t, props=False, cam=False); bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    oe = body_b.evaluated_get(dg); me = oe.to_mesh(); M = oe.matrix_world
    legs = [M @ me.vertices[i].co for i in leg_idx]; hands = [M @ me.vertices[i].co for i in hand_idx]; oe.to_mesh_clear()
    hips = ARM.matrix_world @ ARM.pose.bones["J_Bip_C_Hips"].head
    sb, sv = bvh_world(objs(SKIRT))
    out = 0; worst = None
    for p in legs:
        if p.z < 0.15 or p.z > hips.z:
            continue
        d = Vector((p.x - hips.x, p.y - hips.y, 0.0))
        if d.length < 1e-4:
            continue
        if sb.ray_cast(p, d.normalized(), 1.5)[0] is None:
            out += 1; worst = tuple(round(x, 3) for x in p)
    hin = 0
    for p in hands:
        if p.z > hips.z - 0.05:
            continue
        d = Vector((p.x - hips.x, p.y - hips.y, 0.0))
        if d.length > 1e-4 and sb.ray_cast(p, d.normalized(), 1.5)[0] is not None:
            hin += 1
    gb, gv = bvh_world(objs(("groom_",)))
    bb, bv = bvh_world(objs(("bride_Body", "bride_Hair", "bride_Face", "bride_Cos_Bodice")))
    r = dict(t=round(t, 3), legs_out=out, legs_out_at=worst, hands_in=hin,
             skirt_groom_cm=round(min_dist(gb, sv) * 100, 1), skirt_groom_x=len(sb.overlap(gb)),
             groom_bride_cm=round(min_dist(gb, bv) * 100, 1), groom_bride_x=len(bb.overlap(gb)))
    rows.append(r); print("DC", json.dumps(r), flush=True)
    t += st
od = r"D:\render-work\opening-v12\v2_02_dance"; os.makedirs(od, exist_ok=True)
json.dump(rows, open(os.path.join(od, "dance_check.json"), "w"), indent=1)
summ = dict(legs_out_max=max((x["legs_out"], x["t"]) for x in rows), legs_out_frames=sum(1 for x in rows if x["legs_out"]),
            hands_in_max=max((x["hands_in"], x["t"]) for x in rows), hands_in_frames=sum(1 for x in rows if x["hands_in"]),
            skirt_groom_min_cm=min((x["skirt_groom_cm"], x["t"]) for x in rows), skirt_groom_x_frames=sum(1 for x in rows if x["skirt_groom_x"]),
            groom_bride_min_cm=min((x["groom_bride_cm"], x["t"]) for x in rows), n=len(rows))
print("DC_SUM", json.dumps(summ), flush=True)
