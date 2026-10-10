# ⑤ 路人甲右手抱頭／放下的量測（2026-10-09 第 3 輪）：
#   "$BL" -b couple.blend -P prod_cli.py -- --run v2_05_hand [HKEYS=7.1,7.25,…] [OUT=…json]
# 每個時間點：擺好整幕 → 用「變形後」的網格量
#   palm_c_mm：掌心中心（手骨局部 _palm_pt、gap 0，取最近的手部皮膚頂點）到頭髮表面的距離（負＝在頭髮裡面）
#   palm_min_mm：掌心那一側的手部頂點到頭髮表面的最近距離（負＝穿進頭髮多深）
#   wrist：前臂方向和手骨方向的夾角（v2_quick_check 同一套）；W：手腕世界座標（看路徑）
import bpy, math, os, json, time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
MODE = "setup"
use("run_prod")
SID = "v2_05"
S = SHOTS[SID]; S["build"](); stage(S["set"], cast=True)
PB = V2S["PB"]; A = PB["ARM"]; WHO = PB["WHO"]
KEYS = [float(x) for x in (globals().get("HKEYS") or [round(7.0 + 0.05 * i, 2) for i in range(29)])]
print("V05H objects", [o.name for o in bpy.data.objects if o.name.startswith(WHO) and o.type == "MESH"], flush=True)
HAIR = [o for o in bpy.data.objects if o.name.startswith(WHO) and o.type == "MESH" and "Hair" in o.name and not o.hide_render]
BODY = bpy.data.objects.get(WHO + "_Body")
print("V05H hair", [o.name for o in HAIR], "body", BODY and BODY.name, flush=True)


def bw(name, end="head"):
    pb = A.pose.bones[name]
    return A.matrix_world @ (pb.head if end == "head" else pb.tail)


def hand_verts():
    """手骨權重 > 0.5 的皮膚頂點 index（rest 時算一次）"""
    gi = {g.name: g.index for g in BODY.vertex_groups}
    want = {gi[n] for n in gi if n == "J_Bip_R_Hand" or n.startswith("J_Bip_R_") and any(f in n for f in ("Thumb", "Index", "Middle", "Ring", "Little"))}
    out = []
    for v in BODY.data.vertices:
        w = sum(g.weight for g in v.groups if g.group in want)
        if w > 0.5:
            out.append(v.index)
    return out


HV = hand_verts()
print("V05H hand verts", len(HV), flush=True)


def measure():
    dg = bpy.context.evaluated_depsgraph_get()
    tris, vs = [], []
    for o in HAIR:
        e = o.evaluated_get(dg); m = e.to_mesh(); M = o.matrix_world
        base = len(vs); vs += [M @ v.co for v in m.vertices]
        m.calc_loop_triangles(); tris += [tuple(base + i for i in t.vertices) for t in m.loop_triangles]
        e.to_mesh_clear()
    bvh = BVHTree.FromPolygons(vs, tris)
    eb = BODY.evaluated_get(dg); mb = eb.to_mesh(); Mb = BODY.matrix_world
    pts = [Mb @ mb.vertices[i].co for i in HV]; eb.to_mesh_clear()
    gn = {g.index: g.name for g in BODY.vertex_groups}
    pbn = A.pose.bones["J_Bip_R_Hand"]; Mh = A.matrix_world @ pbn.matrix
    k = PB["_kof"](A)
    pc = Mh @ PB["_palm_pt"](A, "R", k)
    pn = -(Mh.to_3x3() @ Vector((1, 0, 0))).normalized()          # 右手掌心朝 -X（手骨局部）
    wr = Mh.translation

    def sd(p):
        loc, nrm, idx, d = bvh.find_nearest(p)
        if loc is None:
            return 9.9
        # 符號：照射線往頭中心打的方向判斷裡外（頭髮網格法線不一定朝外）
        hc = bw("J_Bip_C_Head") + Vector((0, 0, 0.09))
        return d if (p - hc).length >= (loc - hc).length else -d
    palm = [p for p in pts if (p - wr).dot(pn) > 0.004 and (p - wr).dot(Mh.to_3x3() @ Vector((0, 1, 0))) > 0.01]
    near_c = min(pts, key=lambda p: (p - pc).length)
    dmin = min((sd(p), j) for j, p in enumerate(pts) if p in palm) if palm else (9.9, None)
    worst = {}
    for j, p in enumerate(pts):
        d_ = sd(p)
        if d_ < -0.003:
            v = BODY.data.vertices[HV[j]]; g = max(v.groups, key=lambda g: g.weight)
            nm = gn[g.group].replace("J_Bip_R_", ""); worst[nm] = min(worst.get(nm, 0), round(d_ * 1000, 1))
    el, h, tl = bw("J_Bip_R_LowerArm"), bw("J_Bip_R_Hand"), bw("J_Bip_R_Hand", "tail")
    return dict(palm_c_mm=round(sd(near_c) * 1000, 1), palm_min_mm=round(dmin[0] * 1000, 1),
                worst=worst, n_in=sum(1 for p in palm if sd(p) < -0.002), wrist=round(math.degrees((h - el).angle(tl - h)), 1),
                W=[round(x, 3) for x in wr], E=[round(x, 3) for x in el])


rows = []
t0 = time.time()
CHKR = None
if int(globals().get("CHK", 0)):
    if "Checker" not in PB:
        PB["use"]("check_lib")
    CHKR = PB["Checker"](A, WHO)
    if bpy.data.objects.get(WHO + "_Cos_Shoes") is not None:       # 服裝版的鞋（v2_quick_check 同一套）
        CHKR.shoes = bpy.data.objects[WHO + "_Cos_Shoes"]
ROTB = [b.name for b in A.pose.bones if b.name.startswith("J_Bip_") and not any(f in b.name for f in ("Thumb", "Index", "Middle", "Ring", "Little"))]
_prevq = {}


def rot_step():
    """和上一個時間點相比，身體骨頭（不含手指）轉最多的角度與骨頭名（時間點間隔 1/30 秒時＝每格轉角）"""
    global _prevq
    q = {n: (A.matrix_world @ A.pose.bones[n].matrix).to_quaternion() for n in ROTB}
    best = (0.0, None)
    if _prevq:
        for n in ROTB:
            a = math.degrees(_prevq[n].rotation_difference(q[n]).angle); a = min(a, 360 - a)
            if a > best[0]:
                best = (a, n)
    _prevq = q
    return round(best[0], 1), best[1]
for t in KEYS:
    PB["mesh_eval"](False, A.name)
    S["frame"](t, props=False, cam=False); bpy.context.view_layer.update()
    if not int(globals().get("NOMESH", 0)):
        PB["mesh_eval"](True, A.name); bpy.context.view_layer.update()
    rs = rot_step()
    pc_ = None
    if CHKR is not None:
        c_ = CHKR.frame(); pc_ = (c_["pen_core"], c_.get("pen_hands"))
        PB["mesh_eval"](True, A.name); bpy.context.view_layer.update()
    r = dict(t=t, rot=rs[0], rot_bone=rs[1], pen=pc_, **(measure() if not int(globals().get("NOMESH", 0)) else {})); rows.append(r)
    print("V05H", json.dumps(r), flush=True)
out = globals().get("OUT")
if out:
    json.dump(rows, open(out, "w", encoding="utf8"), indent=1)
print("V05H_DONE", round(time.time() - t0, 1), "s", flush=True)
