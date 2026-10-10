# ⑦ 新郎左手握叉的手指彎曲搜尋（2026-10-10 第 5 輪）：擺好整幕某一格（叉子在手上）→ 手指換成「fork 往 fist 內插 c」→
# 用變形後的網格量每根手指到叉柄的最近距離（v2_07_fork 同一套）。每根手指各自挑「距離 ≤ 3 mm 且不穿進去超過 1.5 mm」的最小 c。
#   "$BL" -b couple.blend -P prod_cli.py -- --run v2_07_grip_search [GT=1.3,2.0] [CS=0,0.1,…]
import bpy, os, json
from mathutils import Vector
MODE = "setup"
use("run_prod")
S = SHOTS["v2_07"]; S["build"](); stage(S["set"], cast=True)
A = GR["ARM"]; BODY = bpy.data.objects[GR["WHO"] + "_Body"]; FORK = bpy.data.objects["V2_Fork"]
FINGERS = ("Thumb", "Index", "Middle", "Ring", "Little")
gi = {g.index: g.name for g in BODY.vertex_groups}
FV = {f: [] for f in FINGERS}
for v in BODY.data.vertices:
    for g in v.groups:
        n = gi.get(g.group, "")
        if g.weight > 0.5 and n.startswith("J_Bip_L_"):
            for f in FINGERS:
                if f in n:
                    FV[f].append(v.index)
HALF = (0.0045, 0.00175); Z0, Z1 = -0.065, 0.075


def box_dist(p):
    q = Vector((abs(p.x) - HALF[0], abs(p.y) - HALF[1], max(Z0 - p.z, p.z - Z1)))
    return Vector((max(q.x, 0), max(q.y, 0), max(q.z, 0))).length + min(max(q.x, q.y, q.z), 0.0)


def dists():
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); e = BODY.evaluated_get(dg); m = e.to_mesh(); Mb = BODY.matrix_world
    Mi = FORK.matrix_world.inverted()
    out = {f: round(min(box_dist(Mi @ (Mb @ m.vertices[i].co)) for i in idx) * 1000, 1) for f, idx in FV.items()}
    e.to_mesh_clear()
    return out


H = GR["HANDS"]; base = dict(H["fork"]); fist = H["fist"]
CS = [float(x) for x in str(globals().get("CS") or "0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0").split(",")]
TH = [float(x) for x in str(globals().get("THS") or "0").split(",")]       # 拇指另外多彎幾度
res = {}
NAMES = []
for c in CS:                                    # 手勢要在 rest 狀態算一次（之後快取成相對父骨的旋轉）
    for th in TH:
        nm = f"_srch_{c:.2f}_{th:.0f}"
        H[nm] = {k: (tuple(a + (b - a) * c for a, b in zip(base[k], fist[k])) if k != "Thumb" else tuple(a + th for a in base[k])) for k in FINGERS}
        H[nm]["spread"] = base.get("spread", 0)
        NAMES.append((c, th, nm))
for pb in A.pose.bones:
    pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
A.location = (0, 0, 0); A.rotation_euler = (0, 0, 0)
for c, th, nm in NAMES:
    for pb in A.pose.bones:
        pb.rotation_quaternion = (1, 0, 0, 0)
    GR["hand_pose"](A, "L", nm)
DX = [float(x) for x in str(globals().get("DXS") or "0,0.006,0.012,0.018").split(",")]    # 叉子往掌心挪（手骨局部 x，左手掌心＝+X）
DZ = [float(x) for x in str(globals().get("DZS") or "0,0.008,0.016,0.024").split(",")]    # 往小指那側挪（局部 −z）
DY = [float(x) for x in str(globals().get("DYS") or "0,-0.012").split(",")]              # 往手腕挪（局部 −y）
best = {}
for t in [float(x) for x in str(globals().get("GT") or "1.3").split(",")]:
    S["frame"](t, cam=False)
    for c, th, nm in NAMES:
        GR["hand_pose"](A, "L", nm); bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get(); e = BODY.evaluated_get(dg); m = e.to_mesh(); Mb = BODY.matrix_world
        Mh = A.matrix_world @ A.pose.bones["J_Bip_L_Hand"].matrix; Mhi = Mh.inverted()
        FL = Mhi @ FORK.matrix_world                                       # 叉子在手骨局部
        loc = {f: [Mhi @ (Mb @ m.vertices[i].co) for i in idx] for f, idx in FV.items()}
        e.to_mesh_clear()
        for dx in DX:
            for dz in DZ:
                for dy in DY:
                    F2 = FL.copy(); F2.translation = FL.translation + Vector((dx, dy, -dz)); F2i = F2.inverted()
                    d = {f: round(min(box_dist(F2i @ p) for p in ps) * 1000, 1) for f, ps in loc.items()}
                    key = f"{t} c{c} th{th} dx{dx} dy{dy} dz{dz}"; res[key] = d
                    core = [d["Thumb"], d["Index"], d["Middle"]]
                    sc = sum(max(0, v - 3.0) for v in core) + 3 * sum(max(0, -1.5 - v) for v in d.values()) + 0.2 * max(0, d["Ring"] - 5)
                    best.setdefault(t, []).append((round(sc, 2), key, d))
    for b in sorted(best[t], key=lambda q: q[0])[:12]:
        print("GRIP_BEST", json.dumps(b, ensure_ascii=False), flush=True)
json.dump(res, open(r"D:\render-work\opening-v12\preview-v2-quick-0507\v2_07\grip_search.json", "w"), indent=1)
print("GRIP_DONE", flush=True)
