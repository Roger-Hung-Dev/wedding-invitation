# ⑦ 第 5 輪：酒杯的數字檢查（2026-10-10）
#   "$BL" -b couple.blend -P prod_cli.py -- --run v2_07_glass [V2_07_R2=1]
# 1. 6.0～12.0 秒逐格（30fps）：兩只杯子的世界位置 → 舉杯停留（7.65～8.8）杯子最大位移與每格速度、碰杯那幾格兩只杯子網格的最近距離
# 2. 指定時間點（網格變形）：拿杯那隻手每根手指到杯腳（半徑 4.2 mm 圓柱，握點上下 3 cm）的最近距離；喝酒時下唇到杯緣圓的距離
# → D:\render-work\opening-v12\preview-v2-quick-0507\v2_07\glass_<TAG>.json
import bpy, math, os, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
MODE = "setup"
use("run_prod")
TAG = "r2" if int(globals().get("V2_07_R2", 0)) else "r5"
S = SHOTS["v2_07"]; S["build"](); stage(S["set"], cast=True)
FPS_ = 30.0
CAST = [("groom", GR, "L"), ("bride", B, "R")]
GOBJ = {w: bpy.data.objects[f"V2_Wine_{w}"] for w, _, _ in CAST}
out = dict(tag=TAG)
for o in bpy.data.objects:
    if o.type == "MESH" and not (o.name.endswith("_Body") or o.name.endswith("_Face")):
        for m in o.modifiers:
            m.show_viewport = False


def bvh_of(o):
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); m = e.to_mesh(); M = o.matrix_world
    vs = [M @ v.co for v in m.vertices]; m.calc_loop_triangles(); tr = [tuple(t.vertices) for t in m.loop_triangles]
    e.to_mesh_clear()
    return BVHTree.FromPolygons(vs, tr), vs


rows = []
hold = T07R5["hold"] if not int(globals().get("V2_07_R2", 0)) else (7.4, 8.4)
for i in range(int(6.0 * FPS_), int(12.0 * FPS_)):
    t = i / FPS_
    for w, ns, _ in CAST:
        mesh_eval(False, ns["ARM"].name)
    S["frame"](t, cam=False); bpy.context.view_layer.update()
    r = dict(t=round(t, 3))
    for w, _, _ in CAST:
        r[w] = [round(x, 5) for x in GOBJ[w].matrix_world.translation]
    if 6.85 <= t <= 7.15 or (int(globals().get("V2_07_R2", 0)) and 7.05 <= t <= 7.35):
        bg, _ = bvh_of(GOBJ["groom"]); bb, vb = bvh_of(GOBJ["bride"])
        r["glass_gap_mm"] = round(min(bg.find_nearest(v)[3] for v in vb[::3]) * 1000, 1)
    rows.append(r)
seg_ = [r for r in rows if hold[0] + 0.25 <= r["t"] <= hold[1]]
st = {}
for w, _, _ in CAST:
    p0 = Vector(seg_[0][w]) if seg_ else Vector()
    dmax = max(((Vector(r[w]) - p0).length for r in seg_), default=0)
    vmax = max(((Vector(a[w]) - Vector(b[w])).length for a, b in zip(seg_[:-1], seg_[1:])), default=0)
    zs = [r[w][2] for r in seg_]
    st[w] = dict(hold_from=seg_[0]["t"] if seg_ else None, hold_to=seg_[-1]["t"] if seg_ else None, drift_mm=round(dmax * 1000, 1),
                 step_max_mm=round(vmax * 1000, 2), z_m=[round(min(zs), 3), round(max(zs), 3)] if zs else None)
out["hold"] = st
gaps = [(r["glass_gap_mm"], r["t"]) for r in rows if "glass_gap_mm" in r]
out["clink_gap_min_mm"] = min(gaps) if gaps else None
out["clink_gaps"] = gaps

# 2. 手指到杯腳、唇到杯緣
FINGERS = ("Thumb", "Index", "Middle", "Ring", "Little")
ct = {}
KEYS = [6.6, 7.0, 7.4, 8.3, 9.0, 9.5, 10.5, 11.5] if TAG == "r5" else [6.6, 7.2, 8.0, 9.4, 10.5, 11.5]
for w, ns, sd in CAST:
    A = ns["ARM"]; BODY = bpy.data.objects[ns["WHO"] + "_Body"]
    gi = {g.index: g.name for g in BODY.vertex_groups}
    FV = {f: [] for f in FINGERS}
    for v in BODY.data.vertices:
        for g in v.groups:
            n = gi.get(g.group, "")
            if g.weight > 0.5 and n.startswith(f"J_Bip_{sd}_"):
                for f in FINGERS:
                    if f in n:
                        FV[f].append(v.index)
    lips = ns["lips_rest"](A)
    for t in KEYS:
        for ww, nn, _ in CAST:
            mesh_eval(True, nn["ARM"].name)
        S["frame"](t, cam=False); bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get(); e = BODY.evaluated_get(dg); m = e.to_mesh(); Mb = BODY.matrix_world
        Mi = GOBJ[w].matrix_world.inverted(); d = {}
        for f, idx in FV.items():
            best = 9.9
            for i in idx:
                p = Mi @ (Mb @ m.vertices[i].co); rr = math.hypot(p.x, p.y); dz = max(0.0, abs(p.z) - 0.03)
                best = min(best, (rr - 0.0042) if dz == 0 else math.hypot(max(rr - 0.0042, 0), dz))
            d[f] = round(best * 1000, 1)
        e.to_mesh_clear()
        pb = A.pose.bones["J_Bip_C_Head"]
        Lw = A.matrix_world @ pb.matrix @ pb.bone.matrix_local.inverted() @ lips
        Mg = GOBJ[w].matrix_world; c = Mg @ Vector((0, 0, 0.135)); zc = Mg.col[2].to_3d().normalized()
        v = Lw - c; vp = v - zc * v.dot(zc)
        rim = c + vp.normalized() * 0.042 if vp.length > 1e-6 else c
        ct[f"{w} {t}"] = dict(fingers_mm=d, lip_rim_mm=round((Lw - rim).length * 1000, 1))
        print("V07G", w, t, json.dumps(ct[f"{w} {t}"]), flush=True)
out["contact"] = ct
p = os.path.join(r"D:\render-work\opening-v12\preview-v2-quick-0507\v2_07", f"glass_{TAG}.json")
json.dump(dict(out, rows=rows), open(p, "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("V07G_SUM", json.dumps({k: v for k, v in out.items() if k != "clink_gaps"}, ensure_ascii=False), flush=True)
print("V07G_DONE", p, flush=True)
