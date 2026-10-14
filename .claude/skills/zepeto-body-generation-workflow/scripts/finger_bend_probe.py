# 手指彎曲驗收：骨頭位置與長度、指節權重過渡寬度、手指網格密度、四指各節彎 0/30/60/90° 與半握拳的近照＋指節厚度保留率。
# 用法：blender -b body.blend -P finger_bend_probe.py -- OUT=<資料夾>
import bpy, sys, os, math, json, bmesh
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree
sys.path.insert(0, r"D:\SideProject\wedding-invitation\.claude\skills\blender-motion-library\scripts")
import mixamo_retarget as mr
A = dict(a.split("=", 1) for a in sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else {}
OUT = A.get("OUT", r"D:\render-work\zepeto-body\build\finger_bend"); os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene; O = bpy.data.objects
arm = O["Body_Armature"]; body = O["Body"]; cam = O["Camera"]; tgt = mr.Target(arm)
S = "L"; FN = ("Index", "Middle", "Ring", "Little")
rep = {}

# 1) 骨頭：每指幾節、各節長度（mm）
B = arm.data.bones
rep["bones"] = {f: [round(B[f"J_Bip_{S}_{f}{i}"].length * 1000, 1) for i in (1, 2, 3)] for f in FN + ("Thumb",)}
rep["finger_radius_mm"] = None

# 2) 權重過渡：沿食指軸，每個頂點的 t（0＝Index1 根、1＝Index3 尖）與 Index1／Index2／Index3 權重 → 找 0.1→0.9 的過渡寬度
gi = {g.name: g.index for g in body.vertex_groups}
def axis_param(p, a, b):
    d = b - a; return (p - a).dot(d) / d.length_squared, ((p - a) - d * ((p - a).dot(d) / d.length_squared)).length
trans = {}
for f in FN:
    h1 = B[f"J_Bip_{S}_{f}1"].head_local; t3 = B[f"J_Bip_{S}_{f}3"].tail_local
    L = (t3 - h1).length
    rows = []
    for v in body.data.vertices:
        t, dist = axis_param(v.co, h1, t3)
        if -0.05 < t < 1.05 and dist < 0.012:
            w = {g.group: g.weight for g in v.groups}
            rows.append((t * L, [w.get(gi.get(f"J_Bip_{S}_{f}{i}"), 0.0) for i in (1, 2, 3)], dist))
    rows.sort()
    out = {}
    for j, (pa, ch) in enumerate(((0, 1), (1, 2))):            # 第 1→2 節、第 2→3 節的交界
        joint = (B[f"J_Bip_{S}_{f}{ch + 1}"].head_local - h1).length
        lo = [s for s, w, _ in rows if w[ch] >= 0.1]; hi = [s for s, w, _ in rows if w[ch] >= 0.9]
        a_ = min(lo) if lo else None; b_ = min(hi) if hi else None
        out[f"joint{ch}"] = dict(at_mm=round(joint * 1000, 1), w10_mm=round(a_ * 1000, 1) if a_ is not None else None,
                                 w90_mm=round(b_ * 1000, 1) if b_ is not None else None,
                                 width_mm=round((b_ - a_) * 1000, 1) if a_ is not None and b_ is not None else None)
    out["verts"] = len(rows)
    out["radius_mm"] = round(sorted(d for _, _, d in rows)[int(len(rows) * 0.9)] * 1000, 1) if rows else None
    trans[f] = out
rep["weight_transition"] = trans

# 3) 網格密度：手指範圍內邊長平均
bm = bmesh.new(); bm.from_mesh(body.data)
h1 = B[f"J_Bip_{S}_Index1"].head_local; t3 = B[f"J_Bip_{S}_Little3"].tail_local
xs = sorted([B[f"J_Bip_{S}_{f}1"].head_local.x for f in FN] + [B[f"J_Bip_{S}_{f}3"].tail_local.x for f in FN])
el = [e.calc_length() for e in bm.edges if all(xs[0] - 0.003 < v.co.x < xs[-1] + 0.01 and abs(v.co.z - h1.z) < 0.015 for v in e.verts)]
rep["finger_mesh"] = dict(edges=len(el), mean_edge_mm=round(sum(el) / len(el) * 1000, 2) if el else None,
                          max_edge_mm=round(max(el) * 1000, 2) if el else None)
bm.free()

# 4) 彎曲測試
for pb in arm.pose.bones:
    pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = (1, 0, 0, 0)
bpy.context.view_layer.update()
R0 = {n: (arm.matrix_world.to_quaternion() @ B[n].matrix_local.to_quaternion()) for n in tgt.keys}
h0 = tgt.rest_h["J_Bip_C_Hips"].copy()
dg = bpy.context.evaluated_depsgraph_get()


def thickness(f, i):
    """第 i 節與第 i+1 節交界：沿「背側平分線」從關節往兩邊射，碰到表面的距離和（＝指節厚度）"""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg); me = ev.to_mesh()
    bv = BVHTree.FromPolygons([body.matrix_world @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    ev.to_mesh_clear()
    pa = arm.pose.bones[f"J_Bip_{S}_{f}{i}"]; pc = arm.pose.bones[f"J_Bip_{S}_{f}{i + 1}"]
    P = arm.matrix_world @ pc.head
    up = lambda pb: (arm.matrix_world.to_3x3() @ pb.matrix.to_3x3() @ B[pb.name].matrix_local.to_3x3().inverted() @ Vector((0, 0, 1))).normalized()
    b = (up(pa) + up(pc)).normalized()
    tot = 0.0
    for s_ in (1, -1):
        hit = bv.ray_cast(P, b * s_, 0.05)
        if hit[0] is None:
            return None
        tot += hit[3]
    return tot


rep["bend"] = {}
STATES = [("rest", None), ("c30", 30), ("c60", 60), ("c90", 90), ("halffist", "grip"), ("relaxed", "relaxed")]
base = {}
for name, val in STATES:
    if val is None:
        R = R0
    elif isinstance(val, str):
        R = mr.gesture(tgt, R0, S, val)
    else:
        R = mr.finger_pose(tgt, R0, S, {f: (val, val, val) for f in FN})
    mr.apply_pose(arm, tgt, R, h0); bpy.context.view_layer.update()
    th = {f: [thickness(f, i) for i in (1, 2)] for f in FN}
    if name == "rest":
        base = th
    rep["bend"][name] = {f: [round(th[f][k] / base[f][k], 2) if th[f][k] and base[f][k] else None for k in (0, 1)] for f in FN}
    pb = arm.pose.bones[f"J_Bip_{S}_Middle1"]; c = arm.matrix_world @ pb.head + Vector((0.01, 0, -0.005))
    cam.data.type = "PERSP"; cam.data.lens = 60
    sc.render.resolution_x = sc.render.resolution_y = 480
    for vn, d in (("side", Vector((0.05, 1, 0.05))), ("front", Vector((0.0, -1, 0.15))), ("palm", Vector((0.0, -0.001, -1)))):
        cam.location = c + d.normalized() * 0.20
        cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(OUT, f"{name}_{vn}.png"); bpy.ops.render.render(write_still=True)
json.dump(rep, open(os.path.join(OUT, "report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("REPORT", json.dumps(rep, ensure_ascii=False))
