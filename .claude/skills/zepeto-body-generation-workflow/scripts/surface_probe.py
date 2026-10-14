# 身體表面品質診斷（references/research-body-surface-handoff.md 1.4 的 T2、T6）：開 body.blend（唯讀，不存檔），
#   T2 截面圓度：在小腿肚、上臂、大腿、胸口、前臂（手模板，當光滑的對照）垂直骨頭切一刀，從骨頭軸往外打 720 條射線量半徑，
#      做傅立葉分析看第 4／8／16／32／64 個波各多大（mm）。第 16 個波明顯突出＝Skin 截面（4 角方框細分 2 次＝16 邊形）留下的稜。
#   T6 三角形形狀：每個面「最長邊 ÷ 最短高」的分布（不含手腳模板）。
# 用法：blender -b <body.blend> -P surface_probe.py -- [OUT=<json>]
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

A = dict(a.split("=", 1) for a in sys.argv[sys.argv.index("--") + 1:] if "=" in a) if "--" in sys.argv else {}
O = bpy.data.objects; body = O["Body"]; arm = O["Body_Armature"]; B = arm.data.bones
MW = body.matrix_world
V = [MW @ v.co for v in body.data.vertices]
T = BVHTree.FromPolygons(V, [tuple(p.vertices) for p in body.data.polygons])
AW = arm.matrix_world
H = lambda n: AW @ B[n].head_local
TL = lambda n: AW @ B[n].tail_local


def section(c, ax, n=720):
    """以 c 為中心、垂直 ax 的截面：每個角度的半徑（m）"""
    ax = ax.normalized()
    u = ax.orthogonal().normalized(); w = ax.cross(u)
    r = []
    for i in range(n):
        a = 2 * math.pi * i / n
        d = u * math.cos(a) + w * math.sin(a)
        h = T.ray_cast(c, d, 0.3)
        r.append(h[3] if h[0] is not None else float("nan"))
    return np.array(r)


def harmonics(r):
    r = r.copy()
    bad = np.isnan(r)
    if bad.any():
        idx = np.arange(len(r)); r[bad] = np.interp(idx[bad], idx[~bad], r[~bad], period=len(r))
    F = np.abs(np.fft.rfft(r)) * 2 / len(r)
    return {k: round(float(F[k]) * 1000, 3) for k in (2, 4, 8, 16, 32, 64)}, round(float(np.mean(r)) * 1000, 1)


def curv(r):
    """曲率 × 半徑（完美的圓處處＝1）：轉角 ÷ 弧長 × 平均半徑；回傳最大值、標準差"""
    n = len(r); a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    x, y = r * np.cos(a), r * np.sin(a)
    P = np.stack([x, y], 1)
    d1 = np.roll(P, -1, 0) - P; d0 = P - np.roll(P, 1, 0)
    ang = np.arctan2(d0[:, 0] * d1[:, 1] - d0[:, 1] * d1[:, 0], (d0 * d1).sum(1))
    ds = (np.linalg.norm(d0, axis=1) + np.linalg.norm(d1, axis=1)) / 2
    k = ang / ds * np.mean(r)
    return round(float(np.max(np.abs(k))), 2), round(float(np.std(k)), 3)


SITES = []
for s in "LR":
    J = lambda n: f"J_Bip_{s}_{n}"
    SITES.append((f"calf_{s}", H(J("LowerLeg")).lerp(H(J("Foot")), 0.30) + Vector((0, 0.009, 0)), H(J("Foot")) - H(J("LowerLeg"))))
    SITES.append((f"upperarm_{s}", H(J("UpperArm")).lerp(H(J("LowerArm")), 0.40), H(J("LowerArm")) - H(J("UpperArm"))))
    SITES.append((f"thigh_{s}", H(J("UpperLeg")).lerp(H(J("LowerLeg")), 0.45), H(J("LowerLeg")) - H(J("UpperLeg"))))
    SITES.append((f"forearm_tpl_{s}", H(J("LowerArm")).lerp(H(J("Hand")), 0.85), H(J("Hand")) - H(J("LowerArm"))))
hz = H("J_Bip_C_Hips").z; sz = H("J_Bip_L_UpperArm").z
SITES.append(("chest", Vector((0, -0.012, hz + 0.62 * (sz - hz))), Vector((0, 0, 1))))
SITES.append(("waist", Vector((0, 0.006, hz + 0.35 * (sz - hz))), Vector((0, 0, 1))))
out = {}
for name, c, ax in SITES:
    r = section(c, ax)
    hm, rm = harmonics(r)
    km, ks = curv(r)
    out[name] = dict(mean_r_mm=rm, harmonics_mm=hm, curv_max=km, curv_std=ks)
    print("SEC", name, out[name])
# T6：三角形長寬比（不含手腳模板與過渡帶）
me = body.data
atts = [a for a in (me.attributes.get(n) for n in ("hand_tpl", "foot_tpl")) if a]
asp = []
for p in me.polygons:
    if any(a.data[k].value != 0 for a in atts for k in p.vertices):
        continue
    vs = [V[k] for k in p.vertices]
    for i in range(1, len(vs) - 1):
        a, b, c_ = vs[0], vs[i], vs[i + 1]
        e = [(b - a).length, (c_ - b).length, (a - c_).length]
        area = (b - a).cross(c_ - a).length / 2
        if area < 1e-14:
            asp.append(99.0); continue
        L = max(e); h = 2 * area / L
        asp.append(L / h)
asp = np.array(asp)
tri = dict(n=int(len(asp)), over6_pct=round(float((asp > 6).mean() * 100), 2), over10_pct=round(float((asp > 10).mean() * 100), 2),
           p50=round(float(np.median(asp)), 2), p95=round(float(np.percentile(asp, 95)), 2))
print("TRI", tri)
res = dict(body=bpy.data.filepath, sections=out, triangles=tri,
           note="harmonics_mm＝截面半徑第 k 個波的振幅（mm）；Skin 細分 2 次的稜在第 16 個波；forearm_tpl 是手模板的前臂（光滑對照）")
if A.get("OUT"):
    os.makedirs(os.path.dirname(A["OUT"]), exist_ok=True)
    json.dump(res, open(A["OUT"], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
