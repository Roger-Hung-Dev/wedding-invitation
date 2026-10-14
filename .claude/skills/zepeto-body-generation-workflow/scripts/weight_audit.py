# 權重污染檢查（references/research-limb-deformation.md 第 4 節 G1～G7）。開 body.blend（唯讀），全身每個點：
#   G1 跨指：手指 A 的點吃到手指 B 的骨頭（> 0.01）；指蹼帶（靜止時離兩根相鄰手指第 1 節都很近）可以吃相鄰手指第 1 節
#   G2 越節：第 2、3 節的點吃到手掌；第 3 節吃到第 1 節
#   G3 跨肢：離正中線 > 4 cm 的點吃到另一側骨頭；或吃到離它很遠的骨頭（> max(2.5×最近骨頭距離, 最近距離＋4 cm)）
#   G4 骨頭數（> 1e-4）≤ 4；G5 總和 1 ± 0.001；G6 碎權重（0 < w < 0.01）數——參考：連續清理一定會留一些 0.01 以下的權重（不能一刀切，見 body_build.clean_weights）
#   G7 動一根看鄰居：轉一根骨頭，量「不該跟著動」的點最大位移（mm）
# 用法：blender -b <body.blend> -P weight_audit.py -- [OUT=<json>] [DIAG=1]
# 也給 body_checks.py 用：audit(body, arm) 回傳 dict
import bpy, sys, os, math, json
from mathutils import Vector, Quaternion

FINGERS = ("Thumb", "Index", "Middle", "Ring", "Little")


def _seg_dist(p, a, b):
    d = b - a; t = max(0.0, min(1.0, (p - a).dot(d) / d.length_squared)); return (p - (a + d * t)).length


LIMB = ("UpperArm", "LowerArm", "Hand", "Thumb", "Index", "Middle", "Ring", "Little", "UpperLeg", "LowerLeg", "Foot", "ToeBase")


def _limb(n):
    return any(k in n for k in LIMB)


def _side(n):
    return "L" if "_L_" in n else "R" if "_R_" in n else "C"


def _part(n):
    """J_Bip_L_Index2 → ('L', 'Index', 2)；J_Bip_L_Hand → ('L', 'Hand', 0)"""
    s = _side(n); core = n.replace("J_Bip_L_", "").replace("J_Bip_R_", "").replace("J_Bip_C_", "")
    for f in FINGERS:
        if core.startswith(f) and core[len(f):].isdigit():
            return s, f, int(core[len(f):])
    return s, core, 0


def audit(body, arm, diag=False):
    B = arm.data.bones
    deform = [b.name for b in B if b.use_deform and (b.name.startswith("J_Bip") or b.name.startswith("J_Adj_"))]
    seg = {n: (B[n].head_local.copy(), B[n].tail_local.copy()) for n in deform}
    gname = {g.index: g.name for g in body.vertex_groups}
    me = body.data
    bad = {k: [] for k in ("G1", "G2", "G3_side", "G3_far")}
    nb_over, sum_off, crumbs, nbmax = 0, 0, 0, 0
    for v in me.vertices:
        ws = [(gname[g.group], g.weight) for g in v.groups if gname.get(g.group) in seg and g.weight > 1e-4]
        if not ws:
            continue
        nbmax = max(nbmax, len(ws)); nb_over += len(ws) > 4
        tot = sum(w for _, w in ws); sum_off += abs(tot - 1.0) > 1e-3
        crumbs += sum(1 for _, w in ws if w < 0.01)
        p = v.co
        dist = {n: _seg_dist(p, *seg[n]) for n in seg}
        near = min(dist, key=dist.get); dmin = dist[near]
        rs, rp, ri = _part(near)
        for n, w in ws:
            if w <= 0.01:
                continue
            s, part, idx = _part(n)
            # G3 左右：離正中線 4 cm 以上，吃到另一側（body_build.clean_weights 在 1～4 cm 之間漸減，帶內本來就允許混）
            if s != "C" and ((s == "L" and p.x < -0.04) or (s == "R" and p.x > 0.04)):
                bad["G3_side"].append((v.index, n, round(w, 3))); continue
            # G3 遠骨頭（只看四肢上的點、四肢的骨頭；頭骨在脖子頂、軀幹很粗，不適用這個距離規則）
            if _limb(near) and _limb(n) and dist[n] > max(2.5 * dmin, dmin + 0.04):
                bad["G3_far"].append((v.index, n, round(w, 3), round(dist[n] * 100, 1))); continue
            # 手指
            if rp in FINGERS and part in FINGERS and rp != part:
                web = idx == 1 and ri == 1 and dist[n] < 1.6 * dmin       # 指蹼帶：兩根相鄰手指第 1 節都很近
                web = web or (part == "Thumb" and idx == 1 and rp == "Index" and ri == 1)   # 虎口：拇指根的權重延伸到食指根那側（手模板設計如此）
                if not web:
                    bad["G1"].append((v.index, n, round(w, 3)))
            elif rp in FINGERS and ri >= 2 and part == "Hand":
                bad["G2"].append((v.index, n, round(w, 3)))
            elif rp in FINGERS and ri == 3 and part == rp and idx == 1:
                bad["G2"].append((v.index, n, round(w, 3)))
    res = dict(G1_cross_finger=len(bad["G1"]), G2_skip_joint=len(bad["G2"]), G3_left_right=len(bad["G3_side"]), G3_far_bone=len(bad["G3_far"]),
               G4_over4=nb_over, bones_max=nbmax, G5_sum_off=sum_off, G6_crumbs=crumbs)
    if diag:
        for k, L in bad.items():
            print("WDIAG", k, len(L), L[:8])
    res["G7_drag_mm"] = drag_test(body, arm, diag)
    return res


def drag_test(body, arm, diag=False):
    """動一根看鄰居：每次只轉一根骨頭，量不該跟著動的點最大位移（mm）"""
    B = arm.data.bones; PB = arm.pose.bones
    me = body.data
    rest = [v.co.copy() for v in me.vertices]
    deform = [b.name for b in B if b.use_deform and (b.name.startswith("J_Bip") or b.name.startswith("J_Adj_"))]
    seg = {n: (B[n].head_local.copy(), B[n].tail_local.copy()) for n in deform}
    region = []
    for p in rest:
        region.append(min(seg, key=lambda n: _seg_dist(p, *seg[n])))

    def ev():
        dg = bpy.context.evaluated_depsgraph_get(); e = body.evaluated_get(dg); m = e.to_mesh()
        r = [x.co.copy() for x in m.vertices]; e.to_mesh_clear(); return r

    def reset():
        for pb in PB:
            pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
        bpy.context.view_layer.update()
    reset(); base = ev()
    # 不該跟著動的點：別根手指的第 2、3 節（第 1 節靠指根的指蹼本來就會被拉動）；另一側、離正中線 2 cm 以上的點
    tests = []
    for f in ("Index", "Middle", "Ring", "Little"):
        tests.append((f"J_Bip_L_{f}1", (1, 0, 0), 60, lambda r, i, f=f: _part(r)[1] in FINGERS and _part(r)[1] != f and _part(r)[2] >= 2))
    tests.append(("J_Bip_L_UpperLeg", (0, 1, 0), 30, lambda r, i: _side(r) == "R" and rest[i].x < -0.04))
    tests.append(("J_Bip_L_UpperArm", (0, 1, 0), 45, lambda r, i: rest[i].x < -0.04 or _part(r)[1] in ("UpperLeg", "LowerLeg", "Foot", "ToeBase")))
    out = {}
    for bn, axis, deg, other in tests:
        reset()
        pb = PB[bn]; pb.rotation_quaternion = Quaternion(axis, math.radians(deg)); bpy.context.view_layer.update()
        cur = ev(); worst = 0.0; wi = None
        for i, (a, b) in enumerate(zip(base, cur)):
            if other(region[i], i):
                d = (a - b).length
                if d > worst:
                    worst, wi = d, i
        out[bn.replace("J_Bip_", "")] = round(worst * 1000, 2)
        if diag and wi is not None:
            print("WDRAG", bn, round(worst * 1000, 2), "v", wi, region[wi], tuple(round(c, 3) for c in rest[wi]))
    reset()
    return out


if __name__ == "__main__":
    A = dict(a.split("=", 1) for a in sys.argv[sys.argv.index("--") + 1:] if "=" in a) if "--" in sys.argv else {}
    r = audit(bpy.data.objects["Body"], bpy.data.objects["Body_Armature"], diag=A.get("DIAG") == "1")
    print("WEIGHTS", json.dumps(r, ensure_ascii=False))
    if A.get("OUT"):
        json.dump(r, open(A["OUT"], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
