# 四肢活動範圍檢查（references/research-limb-deformation.md 第 3、5、6 節）。開 body.blend（唯讀，不存檔），左側肢體：
#   ROM 掃描：手肘 0～145°、膝 0～150°、肩往下／往上／往前、髖屈／外展／內收、腳踝往上／往下、腳趾往上，每 15° 一格
#     L1 截面積比（關節角平分面，靜止＝1）、L3 同一肢體上下兩節互陷（摺進去）最深 mm、L4 不同部位互穿（手臂↔軀幹、腿↔腿）最深 mm、
#     L6 關節附近翻面的面數、L7 相鄰兩格截面積比跳動
#   MIX：Mixamo 片自動挑手肘、膝、髖最彎那一格（含跪姿 kneeling_idle）量 L1／L3／L4
#   STANCE（第 6 節）：F10 靜止時兩腿各高度皮膚最小距離；F11 兩條大腿一起內收到兩踝碰在一起要幾度、那時左右腿互陷；F12 待機片左右腿互陷
#   SPREAD（第 3 節）：S1 靜止相鄰手指最小距離；S2 四指張開（食指 +20、無名指 −15、小指 −25）指蹼邊長拉伸、面積比、翻面；
#     S3 併攏擠壓互陷；S4 只張食指時中指第 2、3 節被拖多遠；S5 拇指捏食指尖（OK、交換戒指）互陷
# 用法：blender -b <body.blend> -P limb_probe.py -- [OUT=<json>] [ONLY=rom,mix,stance,spread]
#   只量數字、不拍照；手肘、膝蓋、胯下、小腿的近照用 limb_shots.py。body_checks.py 會用 exec 呼叫（LIMB_EMBED），結果寫進 checks.json 的 limbs
import bpy, sys, os, math, json
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
sys.path.insert(0, r"D:\SideProject\wedding-invitation\.claude\skills\blender-motion-library\scripts")
import mixamo_retarget as mr

A = dict(a.split("=", 1) for a in sys.argv[sys.argv.index("--") + 1:] if "=" in a) if "--" in sys.argv else {}
EMBED = globals().get("LIMB_EMBED", False)
if EMBED:
    A = dict(ONLY=globals().get("LIMB_ONLY", "rom,mix,stance,spread"))
ONLY = set(A.get("ONLY", "rom,mix,stance,spread").split(","))
O = bpy.data.objects; body = O["Body"]; arm = O["Body_Armature"]; B = arm.data.bones; PB = arm.pose.bones
tgt = mr.Target(arm); AW = arm.matrix_world; MW = body.matrix_world
for pb in PB:
    pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
bpy.context.view_layer.update()
R0 = {n: (AW.to_quaternion() @ B[n].matrix_local.to_quaternion()) for n in tgt.keys}
H0 = tgt.rest_h["J_Bip_C_Hips"].copy()
me = body.data
REST = [MW @ v.co for v in me.vertices]
FACES = [tuple(p.vertices) for p in me.polygons]
DEF = [b.name for b in B if b.use_deform and (b.name.startswith("J_Bip") or b.name.startswith("J_Adj_"))]
SEG = {n: (AW @ B[n].head_local, AW @ B[n].tail_local) for n in DEF}


def sd(p, a, b):
    d = b - a; t = max(0.0, min(1.0, (p - a).dot(d) / d.length_squared)); return (p - (a + d * t)).length


def chain(n):
    """骨頭 → 部位鏈：armL／armR／legL／legR／handL…（手指算手）／torso／head"""
    if "Head" in n or "Neck" in n:
        return "head"
    s = "L" if "_L_" in n else "R" if "_R_" in n else ""
    if not s:
        return "torso"
    if any(k in n for k in ("UpperArm", "LowerArm", "Elbow")):   # 含扭轉骨 LowerArmTwist、半轉骨 ElbowHalf
        return "arm" + s
    if any(k in n for k in ("Hand", "Thumb", "Index", "Middle", "Ring", "Little")):
        return "hand" + s
    if any(k in n for k in ("UpperLeg", "LowerLeg", "Knee")):
        return "leg" + s
    if any(k in n for k in ("Foot", "ToeBase")):
        return "foot" + s
    if "Shoulder" in n:
        return "torso"
    return "torso"


KD = KDTree(len(REST))
for i, p in enumerate(REST):
    KD.insert(p, i)
KD.balance()
REGION = {}


def region(i):
    r = REGION.get(i)
    if r is None:
        p = REST[i]; r = min(SEG, key=lambda n: sd(p, *SEG[n])); REGION[i] = r
    return r


GN = {g.index: g.name for g in body.vertex_groups}
VW = None


def vweights():
    global VW
    if VW is None:
        VW = [[(GN[g.group], g.weight) for g in v.groups if GN.get(g.group) in PB and g.weight > 0] for v in me.vertices]
    return VW


RN = [(MW.to_3x3() @ v.normal).normalized() for v in me.vertices]


def expected_normals(ids):
    rot = {}; out = {}
    W = vweights()
    for i in ids:
        acc = Vector((0, 0, 0)); tot = 0.0
        for n, w in W[i]:
            if n not in rot:
                rot[n] = (AW @ PB[n].matrix @ B[n].matrix_local.inverted() @ AW.inverted()).to_3x3()
            acc += (rot[n] @ RN[i]) * w; tot += w
        out[i] = acc.normalized() if tot > 0 else RN[i]
    return out


DIRS = [Vector(d) for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]


def inside(t, q):
    odd = 0
    for i, d in enumerate(DIRS):
        k = 0; o = q
        for _ in range(64):
            h = t.ray_cast(o, d)
            if h[0] is None:
                break
            k += 1; o = h[0] + d * 1e-6
        odd += k % 2
        if odd >= 4 or odd + (5 - i) < 4:
            break
    return odd >= 4


def ev():
    dg = bpy.context.evaluated_depsgraph_get(); e = body.evaluated_get(dg); m = e.to_mesh()
    V = [MW @ v.co for v in m.vertices]; e.to_mesh_clear(); return V


def pose(R, hips=None):
    mr.apply_pose(arm, tgt, R, hips if hips is not None else H0); bpy.context.view_layer.update()


def rot(R, bone, axis, deg):
    return mr.rotate_subtree(tgt, R, bone, Quaternion(Vector(axis), math.radians(deg)))


def near_ids(center, radius):
    return [i for (co, i, d) in KD.find_range(center, radius)]


def contact(V, ids, joint_chainpair=None):
    """ids 這些點：埋進肉裡的點，分「同一肢體上下兩節（摺進去）」和「不同部位互穿」，各取最深（mm，離最近沒被埋住的皮膚／別的部位表面）"""
    T = BVHTree.FromPolygons(V, FACES)
    NE = expected_normals(ids)
    bur = [i for i in ids if inside(T, V[i] + NE[i] * 2e-4)]
    if not bur:
        return dict(buried=0, crease_mm=0.0, cross_mm=0.0, cross_pair=None)
    bs = set(bur)
    near_faces = {}
    crease = cross = 0.0; pair = None
    # 最近沒被埋住的皮膚：用「附近的面裡沒有埋住點的」建一棵樹
    cand = set()
    for i in bur:
        for (co, j, d) in KD.find_range(REST[i], 0.06):
            cand.add(j)
    fl = [f for f in FACES if f[0] in cand and not any(k in bs for k in f)]
    TE = BVHTree.FromPolygons(V, fl) if fl else None
    for i in bur:
        ra = chain(region(i))
        h = T.ray_cast(V[i] + NE[i] * 2e-4, NE[i], 0.05)
        rc = chain(region(FACES[h[2]][0])) if h[0] is not None else ra
        if rc == ra or {ra, rc} <= {"arm" + ra[-1:], "hand" + ra[-1:]} or {ra, rc} <= {"leg" + ra[-1:], "foot" + ra[-1:]}:
            g = TE.find_nearest(V[i], 0.05) if TE else (None,)
            if g[0] is not None:
                crease = max(crease, g[3])
        else:
            best = None
            for loc, nor, fi, dist in T.find_nearest_range(V[i], 0.03):
                if chain(region(FACES[fi][0])) not in (ra,) and (best is None or dist < best[0]):
                    best = (dist, chain(region(FACES[fi][0])))
            if best and best[0] > cross:
                cross, pair = best[0], f"{ra}↔{best[1]}"
    return dict(buried=len(bur), crease_mm=round(crease * 1000, 2), cross_mm=round(cross * 1000, 2), cross_pair=pair)


def area_at(V, c, ax, ids, rmax=0.12, n=96):
    T = BVHTree.FromPolygons(V, [f for f in FACES if f[0] in ids])
    ax = ax.normalized(); u = ax.orthogonal().normalized(); w = ax.cross(u); pts = []
    for i in range(n):
        a = 2 * math.pi * i / n; h = T.ray_cast(c, u * math.cos(a) + w * math.sin(a), rmax)
        if h[0] is None:
            return None
        pts.append(((h[0] - c).dot(u), (h[0] - c).dot(w)))
    return abs(sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))) / 2


def joint_area(V, upper, lower, ids):
    a = AW @ PB[upper].head; j = AW @ PB[lower].head; b = AW @ PB[lower].tail
    d = (j - a).normalized() + (b - j).normalized()
    return area_at(V, j, d, ids)


def joint_areas(V, upper, lower, ids, offs=(0.02, 0.035)):
    """關節正中間（角平分面）＋上下兩節各往外 offs 公尺、垂直該節骨頭切的截面積（m²）。
    只量正中間不夠：加了半轉骨後中間那圈被撐住，塌的地方移到兩側（2026-10-14）"""
    a = AW @ PB[upper].head; j = AW @ PB[lower].head; b = AW @ PB[lower].tail
    du = (j - a).normalized(); dl = (b - j).normalized()
    out = [area_at(V, j, du + dl, ids)]
    for o in offs:
        out.append(area_at(V, j - du * o, du, ids)); out.append(area_at(V, j + dl * o, dl, ids))
    return out


def folds(V, ids):
    s = set(ids); NE = expected_normals(ids); n = 0
    for f in FACES:
        if f[0] in s and f[1] in s and f[2] in s:
            a, b, c = V[f[0]], V[f[1]], V[f[2]]
            fn = (b - a).cross(c - a)
            if fn.length > 1e-12 and fn.dot(NE[f[0]] + NE[f[1]] + NE[f[2]]) < 0:
                n += 1
    return n


res = {}
L = "L"
JOINTS = {
    # 名稱: (上節, 下節, 轉哪根（連子骨頭）, 世界軸, 角度表, 量截面?)
    "elbow": ("J_Bip_L_UpperArm", "J_Bip_L_LowerArm", "J_Bip_L_LowerArm", (0, 0, 1), [-a for a in range(0, 146, 15)] + [-145], True),
    "knee": ("J_Bip_L_UpperLeg", "J_Bip_L_LowerLeg", "J_Bip_L_LowerLeg", (1, 0, 0), list(range(0, 151, 15)), True),
    "shoulder_down": ("J_Bip_L_Shoulder", "J_Bip_L_UpperArm", "J_Bip_L_UpperArm", (0, 1, 0), [0, 45, 70, 85], False),
    "shoulder_up": ("J_Bip_L_Shoulder", "J_Bip_L_UpperArm", "J_Bip_L_UpperArm", (0, 1, 0), [0, -40, -80], False),
    "shoulder_fwd": ("J_Bip_L_Shoulder", "J_Bip_L_UpperArm", "J_Bip_L_UpperArm", (0, 0, 1), [0, -45, -90], False),
    "hip_flex": ("J_Bip_C_Hips", "J_Bip_L_UpperLeg", "J_Bip_L_UpperLeg", (1, 0, 0), [0, -45, -90, -120], False),
    "hip_abduct": ("J_Bip_C_Hips", "J_Bip_L_UpperLeg", "J_Bip_L_UpperLeg", (0, 1, 0), [0, -20, -40], False),
    "hip_adduct": ("J_Bip_C_Hips", "J_Bip_L_UpperLeg", "J_Bip_L_UpperLeg", (0, 1, 0), [0, 10, 15], False),
    "ankle": ("J_Bip_L_LowerLeg", "J_Bip_L_Foot", "J_Bip_L_Foot", (1, 0, 0), [0, -20, -30, 45, 50], False),
    "toes": ("J_Bip_L_Foot", "J_Bip_L_ToeBase", "J_Bip_L_ToeBase", (1, 0, 0), [0, -40, -70, -90, 30], False),
}
pose(R0); V0 = ev()
AREA0 = {}
if "rom" in ONLY:
    rom = {}
    for name, (up, lo, mv, axis, degs, sec) in JOINTS.items():
        jc = AW @ PB[lo].head
        ids = near_ids(jc, 0.16)
        if sec:
            AREA0[name] = joint_areas(V0, up, lo, set(ids))
        rows = []; prev = None
        for d in degs:
            pose(rot(R0, mv, axis, d)); V = ev()
            row = dict(deg=abs(d) if name in ("elbow",) else d)
            if sec:
                cur = joint_areas(V, up, lo, set(ids))
                rr = [c / r0 for c, r0 in zip(cur, AREA0[name]) if c and r0]
                row["area"] = round(min(rr), 3) if rr else None            # 關節中間＋兩側最小的那個
                row["area_mid"] = round(rr[0], 3) if rr else None
                if prev is not None and row["area"] is not None and prev is not None:
                    row["jump"] = round(abs(row["area"] - prev), 3)
                prev = row["area"]
            row.update(contact(V, ids)); row["fold"] = folds(V, ids)
            rows.append(row)
        rom[name] = rows
        print("ROM", name, [(r["deg"], r.get("area"), r.get("area_mid"), r["crease_mm"], r["cross_mm"], r["fold"]) for r in rows])
    res["rom"] = rom
if "mix" in ONLY:
    RAW = r"D:\render-work\mixamo\raw"
    mix = {}

    def bend(R, up, lo):
        dp = R[up] @ tgt.rest_q[up].inverted(); dc = R[lo] @ tgt.rest_q[lo].inverted()
        d0 = (tgt.rest_t[lo] - tgt.rest_h[lo]).normalized()
        return math.degrees(d0.angle(dp.inverted() @ (dc @ d0)))
    for clip_name, up, lo, label in (("kneeling_idle", "UpperLeg", "LowerLeg", "kneel"), ("crouch_idle", "UpperLeg", "LowerLeg", "crouch"),
                                     ("swing_charleston", "UpperArm", "LowerArm", "elbow"), ("sitting_drinking", "UpperArm", "LowerArm", "drink"),
                                     ("push_forward", "UpperLeg", "LowerLeg", "lunge"), ("sitting_idle", "UpperLeg", "LowerLeg", "sit")):
        fp = os.path.join(RAW, clip_name + ".fbx")
        if not os.path.exists(fp):
            continue
        clip = mr.retarget(mr.read_fbx(fp), tgt)
        b, f, s = max((bend(clip["R"][f], f"J_Bip_{s}_{up}", f"J_Bip_{s}_{lo}"), f, s) for f in range(clip["n"]) for s in "LR")
        pose(clip["R"][f], clip["hips"][f]); V = ev()
        lo_n = f"J_Bip_{s}_{lo}"; up_n = f"J_Bip_{s}_{up}"
        ids = near_ids(AW @ B[lo_n].head_local, 0.18)
        a0 = joint_area(V0, up_n, lo_n, set(ids)) if s == "L" or True else None
        # 靜止截面：照同一個關節在 T 字時量
        pose(R0); Vr = ev(); a0 = joint_areas(Vr, up_n, lo_n, set(ids)); pose(clip["R"][f], clip["hips"][f]); V = ev()
        a = joint_areas(V, up_n, lo_n, set(ids))
        rr = [c / r0 for c, r0 in zip(a, a0) if c and r0]
        row = dict(clip=clip_name, frame=f, side=s, bend_deg=round(b, 1), area=round(min(rr), 3) if rr else None)
        # 跪、蹲、坐：兩條腿和腳都看（左右腿互穿、腳背貼地）
        if label in ("kneel", "crouch", "sit", "lunge"):
            ids = list(set(ids) | set(near_ids(AW @ B[f"J_Bip_{'R' if s == 'L' else 'L'}_LowerLeg"].head_local, 0.18)))
        row.update(contact(V, ids)); row["fold"] = folds(V, ids)
        mix[label] = row
        print("MIX", label, row)
    res["mix"] = mix
if "stance" in ONLY:
    st = {}
    pose(R0); V = ev()
    LV = [i for i in range(len(REST)) if REST[i].x > 0.003 and REST[i].z < 0.62]
    RV = [i for i in range(len(REST)) if REST[i].x < -0.003 and REST[i].z < 0.62]
    def gap(V, z0, z1):
        kd = KDTree(len(RV))
        for k, i in enumerate(RV):
            kd.insert(V[i], k)
        kd.balance()
        best = 1e9
        for i in LV:
            if z0 <= REST[i].z < z1:
                co, k, d = kd.find(V[i])
                best = min(best, d)
        return round(best * 1000, 1)
    st["F10_rest_gap_mm"] = {nm: gap(V, z0, z1) for nm, z0, z1 in (("ankle", 0.05, 0.13), ("calf", 0.13, 0.28), ("knee", 0.28, 0.40), ("thigh", 0.40, 0.54))}
    # F11：兩條大腿一起內收
    ang = None; rows = []
    for d in [x * 0.5 for x in range(0, 21)]:
        R = rot(rot(R0, "J_Bip_L_UpperLeg", (0, 1, 0), d), "J_Bip_R_UpperLeg", (0, 1, 0), -d)
        pose(R); V = ev()
        g = gap(V, 0.0, 0.13)
        rows.append((d, g))
        if g <= 2.0:
            ang = d
            ids = [i for i in LV + RV if REST[i].z < 0.6]
            c = contact(V, ids)
            st["F11"] = dict(adduct_deg_each=d, ankle_gap_mm=g, knee_gap_mm=gap(V, 0.28, 0.40), thigh_gap_mm=gap(V, 0.40, 0.54), **c)
            break
    st["F11_sweep"] = rows
    if ang is None:
        st["F11"] = dict(adduct_deg_each=None, note="內收 10° 兩踝還沒碰到")
    st["F13_clearance_deg"] = {lab: next((d for d, g in rows if g < need), None) for lab, need in (("trousers_16mm", 16), ("trousers_36mm", 36), ("shoes_28mm", 28))}
    # F12：待機片左右腿互穿
    RAW = r"D:\render-work\mixamo\raw"; f12 = {}
    for clip_name in ("standing_idle", "female_idle", "happy_idle", "breathing_idle"):
        fp = os.path.join(RAW, clip_name + ".fbx")
        if not os.path.exists(fp):
            continue
        clip = mr.retarget(mr.read_fbx(fp), tgt)
        worst = None
        for f in range(0, clip["n"], max(1, clip["n"] // 6)):
            pose(clip["R"][f], clip["hips"][f]); V = ev()
            g = gap(V, 0.0, 0.54)
            if worst is None or g < worst[0]:
                worst = (g, f)
        pose(clip["R"][worst[1]], clip["hips"][worst[1]]); V = ev()
        c = contact(V, [i for i in LV + RV if REST[i].z < 0.6])
        f12[clip_name] = dict(frame=worst[1], min_gap_mm=worst[0], **c)
    st["F12_idle"] = f12
    res["stance"] = st
    print("STANCE", st)
if "spread" in ONLY:
    sp = {}
    FN = ("Index", "Middle", "Ring", "Little")
    hand_ids = [i for i in range(len(REST)) if REST[i].x > (AW @ B["J_Bip_L_Hand"].head_local).x - 0.004]
    reg = {i: region(i) for i in hand_ids}
    pose(R0); V = ev()
    kd = {}
    def finger_gap(V):
        best = {}
        for a, b in (("Index", "Middle"), ("Middle", "Ring"), ("Ring", "Little")):
            A_ = [i for i in hand_ids if a in reg[i] and reg[i][-1] in "23"]
            B_ = [i for i in hand_ids if b in reg[i] and reg[i][-1] in "23"]
            t = KDTree(len(B_))
            for k, i in enumerate(B_):
                t.insert(V[i], k)
            t.balance()
            best[f"{a}-{b}"] = round(min(t.find(V[i])[2] for i in A_) * 1000, 2) if A_ and B_ else None
        return best
    sp["S1_rest_gap_mm"] = finger_gap(V)
    # 指蹼帶：手指第 1 節的點、離手掌骨頭比離自己骨頭近 1.5 倍以內
    web = [i for i in hand_ids if reg[i][-1:] == "1" and any(f in reg[i] for f in FN) and sd(REST[i], *SEG["J_Bip_L_Hand"]) < 1.5 * sd(REST[i], *SEG[reg[i]])]
    webs = set(web)
    wf = [f for f in FACES if all(k in webs for k in f)]
    def web_stretch(V):
        er = 0.0; ar = 0.0
        for f in wf:
            for k in range(len(f)):
                a, b = f[k], f[(k + 1) % len(f)]
                l0 = (REST[a] - REST[b]).length
                if l0 > 1e-9:
                    er = max(er, (V[a] - V[b]).length / l0)
            a0 = (REST[f[1]] - REST[f[0]]).cross(REST[f[2]] - REST[f[0]]).length
            a1 = (V[f[1]] - V[f[0]]).cross(V[f[2]] - V[f[0]]).length
            if a0 > 1e-12:
                ar = max(ar, a1 / a0)
        return round(er, 2), round(ar, 2)
    Z0 = {f: (0, 0, 0) for f in FN}                     # finger_pose 只對 curl 裡有的手指套 spread，所以四指都要寫（彎 0）
    pose(mr.finger_pose(tgt, R0, "L", Z0, spread={"Index": 20, "Middle": 0, "Ring": -15, "Little": -25})); V = ev()
    e_, a_ = web_stretch(V)
    sp["S2_spread"] = dict(web_edge_stretch_max=e_, web_area_ratio_max=a_, fold=folds(V, hand_ids), **contact(V, hand_ids))
    pose(mr.finger_pose(tgt, R0, "L", Z0, spread={"Index": -5, "Middle": 0, "Ring": 5, "Little": 8})); V = ev()
    sp["S3_squeeze"] = dict(gap_mm=finger_gap(V), **contact(V, hand_ids))
    pose(R0); Vr = ev()
    pose(mr.finger_pose(tgt, R0, "L", {"Index": (0, 0, 0)}, spread={"Index": 20})); V = ev()
    mid = [i for i in hand_ids if "Middle" in reg[i] and reg[i][-1] in "23"]
    sp["S4_drag_middle_mm"] = round(max((V[i] - Vr[i]).length for i in mid) * 1000, 3) if mid else None
    for nm, tt in (("S5_pinch_index_tip", "Index3"), ("S5_pinch_little_tip", "Little3")):
        curl = {"Thumb": (20, 30, 25)}
        if tt.startswith("Index"):
            curl["Index"] = (35, 45, 30)
        else:
            curl["Little"] = (45, 55, 35); curl["Ring"] = (30, 40, 25)
        try:
            pose(mr.finger_pose(tgt, R0, "L", curl, thumb_to=tt)); V = ev()
            sp[nm] = dict(fold=folds(V, hand_ids), **contact(V, hand_ids))
        except Exception as e:
            sp[nm] = dict(error=str(e)[:120])
    res["spread"] = sp
    print("SPREAD", sp)
pose(R0)
if not EMBED:
    print("LIMB", json.dumps(res, ensure_ascii=False)[:3000])
if A.get("OUT"):
    os.makedirs(os.path.dirname(A["OUT"]), exist_ok=True)
    json.dump(res, open(A["OUT"], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
