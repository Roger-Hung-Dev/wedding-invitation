# 交接給服裝的尺寸（references/research-body-surface-handoff.md 第 3 節）。T 字靜止、修改器算完的網格、世界座標，左側，單位 mm。
# 量法：切一刀 → 邊和平面的交點 → 只留目標附近的 → 交點投影到切面取凸包 → 凸包周長＝皮尺圍；寬、高＝指定方向的範圍。
# 定義照 IBV／ISO（轉述，見研究報告）：腳長沿腳軸、腳掌圍過第 1、5 蹠骨頭（大拇趾根、小趾根凸點）垂直地面、腳背圍在離腳跟 50% 腳長、
#   腳跟寬在 16% 腳長、手腕圍在手腕點垂直前臂、小腿最粗圍、膝圍、大腿最粗圍；外加沿前臂、小腿每 5 mm 一圈（profile）。
# 用法：blender -b <body.blend> -P body_measure.py -- [OUT=<json>]；body_build.py 結尾用 exec 呼叫（MEASURE_EMBED），結果寫進 build.json 的 measure
#      TEST=1：先量一根半徑 30 mm 的圓柱（應 188.5 mm）驗證程式
import bpy, sys, os, math, json
from mathutils import Vector
from mathutils.geometry import convex_hull_2d

A = dict(a.split("=", 1) for a in sys.argv[sys.argv.index("--") + 1:] if "=" in a) if "--" in sys.argv else {}
if globals().get("MEASURE_EMBED"):
    A = {}
O = bpy.data.objects


def mesh_world(obj):
    dg = bpy.context.evaluated_depsgraph_get(); ev = obj.evaluated_get(dg); me = ev.to_mesh()
    V = [obj.matrix_world @ v.co for v in me.vertices]; E = [tuple(e.vertices) for e in me.edges]; ev.to_mesh_clear()
    return V, E


def section(V, E, co, no, center, rmax, ax_w=None, ax_h=None, keep=None):
    no = no.normalized()
    if ax_w is None:
        ax_w = no.orthogonal()
    ax_w = (ax_w - no * ax_w.dot(no)).normalized()
    ax_h = no.cross(ax_w).normalized() if ax_h is None else (ax_h - no * ax_h.dot(no) - ax_w * ax_h.dot(ax_w)).normalized()
    pts = []
    for a_, b_ in E:
        a, b = V[a_], V[b_]
        da, db = (a - co).dot(no), (b - co).dot(no)
        if da * db < 0:
            p = a.lerp(b, da / (da - db))
            if (p - center).length < rmax and (keep is None or keep(p)):
                pts.append(p)
    if len(pts) < 3:
        return None
    p2 = [Vector(((p - co).dot(ax_w), (p - co).dot(ax_h))) for p in pts]
    hull = [p2[i] for i in convex_hull_2d(p2)]
    tape = sum((hull[i] - hull[i - 1]).length for i in range(len(hull)))
    w = [q.x for q in p2]; h = [q.y for q in p2]
    return dict(girth=round(tape * 1000, 1), width=round((max(w) - min(w)) * 1000, 1), height=round((max(h) - min(h)) * 1000, 1),
                hmax=max(h), n=len(pts))


def r1(x):
    return round(x * 1000, 1)


def measure():
    body = O["Body"]; arm = O["Body_Armature"]; B = arm.data.bones; AW = arm.matrix_world
    H = lambda n: AW @ B[n].head_local
    T = lambda n: AW @ B[n].tail_local
    V, E = mesh_world(body)
    an, toe = H("J_Bip_L_Foot"), H("J_Bip_L_ToeBase")
    Z = Vector((0, 0, 1))
    left_leg = lambda p: p.x > 0.004
    foot = [p for p in V if p.x > 0.004 and p.z < max(0.07, an.z * 0.9) and abs(p.x - an.x) < 0.07]
    heel = max(foot, key=lambda p: p.y); tip = min(foot, key=lambda p: p.y)
    # 第 1、5 蹠骨頭：腳趾關節前後 6 mm 內、最內側／最外側（貼地 3 cm 內）的點
    band = [p for p in foot if abs(p.y - toe.y) < 0.006 and p.z < 0.03]
    mtp1 = min(band, key=lambda p: p.x); mtp5 = max(band, key=lambda p: p.x)
    mid = (mtp1 + mtp5) / 2
    axis = Vector((mid.x - heel.x, mid.y - heel.y, 0)).normalized()          # 腳軸：腳跟最後點 → 兩蹠骨頭中點（投影到地面）
    proj = lambda p: (p - heel).dot(axis)
    L = max(proj(p) for p in foot)
    side = Z.cross(axis).normalized()
    out = {"ver": 1, "pose": "T 字靜止", "unit": "mm", "side": "L"}
    lm = dict(heel_back=heel, toe_tip=tip, mtp1=mtp1, mtp5=mtp5, ankle_joint=an)
    f = {"length": r1(L), "heel_to_ball": r1(proj(mtp1)), "ankle_joint_height": r1(an.z)}
    nb = (mtp5 - mtp1).cross(Z)
    s = section(V, E, mid, nb, mid, 0.08, ax_w=(mtp5 - mtp1), ax_h=Z, keep=left_leg)
    if s:
        f.update(ball_girth=s["girth"], ball_width=s["width"], ball_height=s["height"])
    for key, frac in (("instep", 0.50), ("heel", 0.16)):
        c = heel + axis * (L * frac); c.z = 0.03
        s = section(V, E, c, axis, c, 0.08, ax_w=side, ax_h=Z, keep=left_leg)
        if s:
            if key == "instep":
                f.update(instep_girth=s["girth"], instep_width=s["width"], instep_height=r1(s["hmax"] + c.z))
                lm["instep_pt"] = c
            else:
                f.update(heel_width=s["width"])
    # 鞋楦腰圍：腳掌圍和腳背圍之間最小的一圈
    wg = []
    for k in range(1, 10):
        c = heel + axis * (L * (0.50 + (proj(mtp1) / L - 0.50) * k / 10)); c.z = 0.03
        s = section(V, E, c, axis, c, 0.08, ax_w=side, ax_h=Z, keep=left_leg)
        if s:
            wg.append(s["girth"])
    if wg:
        f["waist_girth"] = min(wg)
    # 腳趾高：腳趾那段（離腳尖 15% 腳長）的最高點
    c = heel + axis * (L * 0.85); c.z = 0.02                                   # 腳軸從腳跟往前，離腳尖 15%＝離腳跟 85%
    s = section(V, E, c, axis, c, 0.08, ax_w=side, ax_h=Z, keep=left_leg)
    if s:
        f.update(toe_height=r1(max(p.z for p in V if abs(proj(p) - L * 0.85) < 0.002 and p.x > 0.004 and abs(p.x - an.x) < 0.07)), toe_girth=s["girth"])
    # 足弓：腳趾關節到腳踝中段、內側邊兩成寬，最低點離地
    ay0, ay1 = toe.y + 0.25 * (an.y - toe.y), toe.y + 0.75 * (an.y - toe.y)
    mx = min(p.x for p in foot if ay0 < p.y < ay1)
    mw = max(p.x for p in foot if ay0 < p.y < ay1) - mx
    arch = [p.z for p in foot if ay0 < p.y < ay1 and p.x < mx + 0.2 * mw and p.z < 0.03]
    f["arch_height"] = r1(min(arch)) if arch else None
    # 腳踝圍（腳踝關節高度的水平一圈）、最小腿圍（腳踝到小腿肚之間最細的一圈）
    kn = H("J_Bip_L_LowerLeg")
    leg_c = lambda z: Vector((an.x, 0.004, z))
    s = section(V, E, leg_c(an.z), Z, leg_c(an.z), 0.09, keep=left_leg)
    if s:
        f["ankle_girth"] = s["girth"]
    shin = []
    z = an.z + 0.005
    while z < kn.z:
        s = section(V, E, leg_c(z), Z, leg_c(z), 0.08, keep=left_leg)
        if s:
            shin.append([r1(z - an.z), s["girth"]])
        z += 0.005
    if shin:
        lower = [g for d, g in shin if d < (kn.z - an.z) * 1000 * 0.6]
        f["min_leg_girth"] = min(lower) if lower else None
    out["foot"] = f
    # 腿：小腿最粗、膝、大腿最粗（胯下以下）
    leg = {}
    if shin:
        leg["calf_girth"] = max(g for d, g in shin)
    s = section(V, E, leg_c(kn.z), Z, leg_c(kn.z), 0.10, keep=left_leg)
    if s:
        leg["knee_girth"] = s["girth"]
    crotch = min([p.z for p in V if abs(p.x) < 0.01 and p.z < H("J_Bip_C_Hips").z + 0.1] or [kn.z + 0.2])
    th = []
    z = kn.z + 0.05
    while z < crotch - 0.01:
        c = Vector((H("J_Bip_L_UpperLeg").x, 0.0, z))
        s = section(V, E, c, Z, c, 0.12, keep=left_leg)
        if s:
            th.append(s["girth"])
        z += 0.01
    if th:
        leg["thigh_girth"] = max(th)
    out["leg"] = leg
    # 手臂：手腕圍（手腕點垂直前臂）、前臂最粗、上臂中段、手長、手寬
    a1, a2 = H("J_Bip_L_LowerArm"), H("J_Bip_L_Hand"); a0 = H("J_Bip_L_UpperArm")
    fd = (a2 - a1).normalized()
    left_arm = lambda p: p.x > 0.15
    armd = {}
    s = section(V, E, a2, fd, a2, 0.06, keep=left_arm)
    if s:
        armd["wrist_girth"] = s["girth"]
    fore = []
    for k in range(0, 41):
        t = k / 40; c = a1.lerp(a2, t)
        s = section(V, E, c, fd, c, 0.07, keep=left_arm)
        if s:
            fore.append([r1((a2 - c).length), s["girth"]])
    if fore:
        armd["forearm_max_girth"] = max(g for d, g in fore if d > (a2 - a1).length * 1000 * 0.5)
    c = a0.lerp(a1, 0.5)
    s = section(V, E, c, (a1 - a0), c, 0.08, keep=left_arm)
    if s:
        armd["upper_arm_girth"] = s["girth"]
    mid3 = T("J_Bip_L_Middle3")
    tipx = max(p.x for p in V if p.x > mid3.x - 0.01 and abs(p.y - mid3.y) < 0.008 and abs(p.z - mid3.z) < 0.01)
    armd["hand_length"] = r1(tipx - a2.x)
    mcp = [H(f"J_Bip_L_{n}1") for n in ("Index", "Little")]
    c = (mcp[0] + mcp[1]) / 2
    s = section(V, E, c, fd, c, 0.07, ax_w=Vector((0, 1, 0)), ax_h=Z, keep=left_arm)
    if s:
        armd["hand_breadth"] = s["width"]
    armd["thumb_root"] = [round(x, 4) for x in H("J_Bip_L_Thumb1")]
    out["arm"] = armd
    # 脖子：接口環那圈、脖子底（肩線上方 2 cm）
    neck = {}
    hd = O.get("Head")
    nz = H("J_Bip_C_Neck"); hz = H("J_Bip_C_Head")
    ring_z = None
    att = body.data.attributes.get("neck_ring")
    if att:
        rz = [V[i].z for i, d in enumerate(att.data) if d.value > 0]
        ring_z = sum(rz) / len(rz) if rz else None
    # 脖子：接口環下 3 mm 那圈（環上剛好是網格邊緣，切不到）、脖子骨頭到環之間最細的一圈；肩線（脖子骨頭頭部）以下會切到肩膀，不量
    if ring_z is not None:
        c = Vector((0, -0.02, ring_z - 0.003))
        s = section(V, E, c, Z, c, 0.09, keep=lambda p: abs(p.x) < 0.09)
        if s:
            neck["ring_girth"] = s["girth"]
        gs = []
        z = nz.z + 0.01
        while z < ring_z - 0.003:
            c = Vector((0, -0.02, z)); s = section(V, E, c, Z, c, 0.09, keep=lambda p: abs(p.x) < 0.09)
            if s:
                gs.append(s["girth"])
            z += 0.004
        if gs:
            neck["min_girth"] = min(gs)
    neck["cut_z"] = r1(ring_z) if ring_z else None
    out["neck"] = neck
    out["profile"] = {"forearm_from_wrist": fore, "shin_from_ankle": shin}
    out["landmarks"] = {k: [round(x, 4) for x in v] for k, v in lm.items()}
    return out


def self_test():
    bpy.ops.mesh.primitive_cylinder_add(vertices=256, radius=0.03, depth=0.2, location=(5, 0, 0))
    cyl = bpy.context.active_object
    V, E = mesh_world(cyl)
    s = section(V, E, Vector((5, 0, 0)), Vector((0, 0, 1)), Vector((5, 0, 0)), 0.1)
    me = cyl.data; O.remove(cyl); bpy.data.meshes.remove(me)
    return dict(expect=round(2 * math.pi * 30, 1), got=s["girth"] if s else None)


res = {}
if A.get("TEST") == "1":
    print("MTEST", self_test())
res = measure()
if not globals().get("MEASURE_EMBED"):
    print("MEASURE", json.dumps({k: v for k, v in res.items() if k not in ("profile",)}, ensure_ascii=False))
    if A.get("OUT"):
        json.dump(res, open(A["OUT"], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
