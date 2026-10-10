# 動作自動檢查：穿模（手/前臂穿進身體或頭、雙手互穿、雙腿互穿）、腳底高度、每格骨頭轉角（流暢度）。
# exec 在 pose_lib.py / actions.py 之後。
import bpy, math
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree

ARM_KEYS = ("UpperArm", "LowerArm", "Hand", "Thumb", "Index", "Middle", "Ring", "Little")
FORE_KEYS = ("LowerArm", "Hand", "Thumb", "Index", "Middle", "Ring", "Little")
LEG_KEYS = ("UpperLeg", "LowerLeg", "Foot", "ToeBase")


def _dominant(ob):
    names = {g.index: g.name for g in ob.vertex_groups}
    out = []
    for v in ob.data.vertices:
        best = max(v.groups, key=lambda g: g.weight, default=None)
        out.append(names.get(best.group, "") if best else "")
    return out


def _cls(name):
    for side in ("L", "R"):
        if f"_{side}_" in name:
            if any(k in name for k in FORE_KEYS): return "fore" + side
            if "UpperArm" in name or "Shoulder" in name: return "upper" + side
            if any(k in name for k in LEG_KEYS): return "leg" + side
    return "core"


class Checker:
    """拓撲固定，所以面的分組只算一次；每格只用 numpy 一次取出變形後的頂點座標"""
    def __init__(self, arm, who=None, probe_step=4):
        who = who or WHO
        import numpy as np
        self.np = np
        O = bpy.data.objects
        self.arm = arm
        self.parts = [O[n] for n in (f"{who}_Body", f"{who}_BodyFill") if n in O]   # 沒有補皮膚的角色就只有 Body
        self.face = O[f"{who}_Face"]; self.shoes = O[f"{who}_Shoes"]
        self.groups = {}
        for ob in self.parts:
            C = [_cls(n) for n in _dominant(ob)]
            me = ob.data
            vg = [set() for _ in me.vertices]          # 每個頂點周圍的面屬於哪些群組
            for p in me.polygons:
                c = {C[i] for i in p.vertices}; lab = c.pop() if len(c) == 1 else "mix"
                for i in p.vertices: vg[i].add(lab)
            ec = {}
            for p in me.polygons:
                for e in p.edge_keys: ec[e] = ec.get(e, 0) + 1
            for (a, b_), n in ec.items():
                if n == 1: vg[a].add("hole"); vg[b_].add("hole")
            gf = {}
            for p in me.polygons:
                c = {C[i] for i in p.vertices}
                if len(c) == 1:
                    k = c.pop()
                    edge = any(len(vg[i]) > 1 for i in p.vertices)   # 切口邊緣的面：最近點落在這裡時內外判斷不可靠
                    gf.setdefault(k, []).append((tuple(p.vertices), edge))
            probes = {k: [i for i, c in enumerate(C) if c == k][::probe_step] for k in ("foreL", "foreR", "legL", "legR")}
            self.groups[ob.name] = (gf, probes)
        self.face_polys = [tuple(p.vertices) for p in self.face.data.polygons]
        self.prev = None

    def _co(self, ob):
        np = self.np
        for m in ob.modifiers:
            if m.type == "ARMATURE" and not m.show_viewport:
                m.show_viewport = True
        dg = bpy.context.evaluated_depsgraph_get()
        oe = ob.evaluated_get(dg); me = oe.to_mesh()
        a = np.empty(len(me.vertices) * 3, dtype=np.float64); me.vertices.foreach_get("co", a)
        nn = np.empty(len(me.vertices) * 3, dtype=np.float64); me.vertices.foreach_get("normal", nn)
        oe.to_mesh_clear()
        a = a.reshape(-1, 3); nn = nn.reshape(-1, 3)
        M = np.array(ob.matrix_world)
        self._last_n = nn @ M[:3, :3].T
        return a @ M[:3, :3].T + M[:3, 3]

    def frame(self):
        np = self.np
        tgt = {k: ([], []) for k in ("core", "foreL", "foreR", "legL", "legR")}
        fnorm = {k: [] for k in tgt}
        probes = {k: [] for k in ("foreL", "foreR", "legL", "legR")}
        for ob in self.parts:
            V = self._co(ob); gf, pr = self.groups[ob.name]; Nv = self._last_n
            Vl = [Vector(v) for v in V]
            for k, fs in gf.items():
                if k not in tgt: continue
                vs, ff = tgt[k]; b = len(vs)
                # 直接用整份頂點表（簡單），面索引加上偏移
                vs.extend(Vl); ff.extend(tuple(i + b for i in f) for f, _ in fs)
                fnorm[k].extend(None if e else Vector(Nv[list(f)].mean(axis=0)).normalized() for f, e in fs)
            for k, idx in pr.items():
                probes[k].extend(Vl[i] for i in idx)
        Vf = [Vector(v) for v in self._co(self.face)]; Nf = self._last_n
        vs, ff = tgt["core"]; b = len(vs); vs.extend(Vf); ff.extend(tuple(i + b for i in f) for f in self.face_polys)
        fnorm["core"].extend(Vector(Nf[list(f)].mean(axis=0)).normalized() for f in self.face_polys)
        bvh = {k: BVHTree.FromPolygons(v, f) for k, (v, f) in tgt.items() if f}

        gaps = {}; self.worst_at = {}
        def pen(points, key, tag=None):
            target = bvh[key]; FN = fnorm[key]
            worst = 0.0; gap = 0.05
            for p in points:
                loc, n, i, d = target.find_nearest(p, 0.05)
                if loc is None: continue
                sn = FN[i]                     # 平滑法線：在細長的手指邊角也能正確分辨內外
                if sn is None:                 # 切口邊緣：跳過
                    continue
                sd = d if (p - loc).dot(sn) >= 0 else -d
                if sd < -0.02:                 # 比手掌還深的「穿入」是量測誤判（最近點在背面），不計
                    continue
                if sd < 0:                     # 交叉確認：往外射一條短射線，要從裡面穿出表面才算真的在裡面
                    hl, hn, hi, hd = target.ray_cast(p, sn, 0.03)
                    if hl is None or FN[hi] is None or FN[hi].dot(sn) <= 0:
                        continue
                if sd < worst:
                    worst = sd
                    if tag: self.worst_at[tag] = (tuple(round(x, 3) for x in p), tuple(round(x, 3) for x in loc))
                if sd > 0: gap = min(gap, sd)
            if tag: gaps[tag] = min(gaps.get(tag, 0.05), gap)
            return -worst * 1000
        r = {}
        r["pen_core"] = max(pen(probes["foreL"], "core", "core"), pen(probes["foreR"], "core", "core"))
        r["pen_hands"] = max(pen(probes["foreL"], "foreR", "hands"), pen(probes["foreR"], "foreL", "hands"))
        r["gap_core"] = gaps.get("core", 0.05) * 1000; r["gap_hands"] = gaps.get("hands", 0.05) * 1000
        r["pen_legs"] = max(pen(probes["legL"], "legR"), pen(probes["legR"], "legL"))
        S = self._co(self.shoes)
        mw = self.arm.matrix_world
        fl = np.array(mw @ self.arm.pose.bones["J_Bip_L_Foot"].head); fr = np.array(mw @ self.arm.pose.bones["J_Bip_R_Foot"].head)
        nearL = np.linalg.norm(S - fl, axis=1) < np.linalg.norm(S - fr, axis=1)
        zl = float(S[nearL, 2].min()); zr = float(S[~nearL, 2].min())
        r["foot_min"] = min(zl, zr)
        mesh_eval(False)
        return r

    def motion(self):
        """和上一格比，世界空間（含整體旋轉）的最大轉角（度/格）→ (身體, 腳踝腳趾)。
        身體＝手指、腳踝（Foot）、腳趾（ToeBase）以外的骨頭；腳踝腳趾另計（門檻 VMAX_FOOT）；手指不擋（2026-10-08 起不算進 vmax）"""
        A = self.arm
        cur = {pb.name: (A.matrix_world @ pb.matrix).to_quaternion() for pb in A.pose.bones if pb.name.startswith("J_Bip")}
        if self.prev is None:
            self.prev = cur; return 0.0, 0.0
        body = foot = 0.0
        for k, q in cur.items():
            a = q.rotation_difference(self.prev[k]).angle; d = math.degrees(min(a, 2 * math.pi - a))
            g = bone_group(k)
            if g == "body": body = max(body, d)
            elif g == "foot": foot = max(foot, d)
        self.prev = cur
        return body, foot


SLIDE_Z = 0.005          # 鞋底取樣點離地 ≤ 5 mm 算「踩在地上」

# 流暢度門檻（2026-10-08 使用者決定）：身體骨頭每格 ≤ 15°、速度突變 ≤ 6（只看身體骨頭）；
# 腳踝（Foot）、腳趾（ToeBase）每格 ≤ 35°、不套速度突變（真人走路蹬地時腳踝本來就會到 20～32°/格）；手指不擋
VMAX_BODY = 15.0
VMAX_FOOT = 35.0
JERK_BODY = 6.0
_FINGERS = ("Thumb", "Index", "Middle", "Ring", "Little")


def bone_group(name):
    """骨頭分組：'finger'／'foot'（Foot、ToeBase）／'body'（其餘）"""
    if any(f in name for f in _FINGERS):
        return "finger"
    if name.endswith("_Foot") or name.endswith("_ToeBase"):
        return "foot"
    return "body"


# 滑步門檻：每格 ≤ 1 mm、累計 ≤ 5 mm。例外：真人走路（walk_fwd 的 style='mocap'）每格 ≤ 1.1 mm（2026-10-08 使用者決定）——
# 步幅 0.4～0.5 m 時，腳跟著地後腳掌放平那一格，離地 2～5 mm 的鞋底點跟著轉，帶出 1.04～1.08 mm 的水平位移（看不出來：1 px ≈ 3 mm）
SLIDE_STEP = 1.0
SLIDE_STEP_MOCAP_WALK = 1.1
SLIDE_TOTAL = 5.0


def slide_limit(fn):
    """這個動作的每格滑步門檻（mm）：真人走路 1.1，其餘 1.0"""
    return SLIDE_STEP_MOCAP_WALK if getattr(fn, "style", None) == "mocap" else SLIDE_STEP


def slide_ok(step_mm, total_mm, fn=None):
    return step_mm <= (slide_limit(fn) if fn is not None else SLIDE_STEP) and total_mm <= SLIDE_TOTAL


def motion_ok(vmax, jerk, foot_vmax=0.0):
    """流暢度是否過門檻（vmax、jerk 只算身體骨頭；foot_vmax＝腳踝腳趾）"""
    return vmax <= VMAX_BODY and jerk <= JERK_BODY and foot_vmax <= VMAX_FOOT


def sole_world(arm):
    """左右腳的鞋底取樣點（世界座標，順序固定）：用骨頭矩陣換算，不必算網格"""
    bpy.context.view_layer.update()
    mw = arm.matrix_world
    out = {"L": [], "R": []}
    for b, co in sole_points(arm):
        out["L" if "_L_" in b else "R"].append(mw @ arm.pose.bones[b].matrix @ co)
    return out


def slide_between(prev, cur):
    """滑步：兩格之間，每隻腳「兩格都踩在地上」的取樣點平均水平位移（公尺）。
    只算兩格都著地的同一批點，所以抬腳跟、墊腳尖不會被當成滑動；這隻腳沒踩地（< 3 點）回 None"""
    res = {}
    for side in "LR":
        idx = [i for i, (a, b) in enumerate(zip(prev[side], cur[side])) if a.z <= SLIDE_Z and b.z <= SLIDE_Z]
        if len(idx) < 3:
            res[side] = None
            continue
        dx = sum(cur[side][i].x - prev[side][i].x for i in idx) / len(idx)
        dy = sum(cur[side][i].y - prev[side][i].y for i in idx) / len(idx)
        res[side] = math.hypot(dx, dy)
    return res


def analyse(key, nsamp=None):
    """不渲染，只算數字：每格骨頭轉角（含頭尾相接那一格）＋取樣格的穿模/腳底＋每格的滑步"""
    name, fn, n = ACT[key]
    ck = Checker(ARM)
    mesh_eval(False)
    vel = []; fvel = []; pens = []; feet = []
    slide_mx = 0.0; slide_tot = {"L": 0.0, "R": 0.0}; sw_prev = None
    frames = list(range(n)) + [0]
    samp = set(range(0, n, max(1, n // (nsamp or 16))))
    for j, i in enumerate(frames):
        pose_frame(ARM, fn(i / n))
        bpy.context.view_layer.update()
        a, fa = ck.motion()
        if j > 0: vel.append(a); fvel.append(fa)
        sw = sole_world(ARM)
        if sw_prev is not None:
            for side, d in slide_between(sw_prev, sw).items():
                if d is not None:
                    slide_mx = max(slide_mx, d); slide_tot[side] += d
        sw_prev = sw
        if j < n and i in samp:
            r = ck.frame(); pens.append(r); feet.append(r["foot_min"])
    acc = [abs(vel[i] - vel[i - 1]) for i in range(1, len(vel))]
    res = dict(key=key, name=name, frames=n, vmax=round(max(vel), 1), jerk=round(max(acc), 1),
               seam=round(vel[-1], 1), foot_vmax=round(max(fvel), 1),
               pen_core=round(max(p["pen_core"] for p in pens), 1), pen_hands=round(max(p["pen_hands"] for p in pens), 1),
               pen_legs=round(max(p["pen_legs"] for p in pens), 1),
               foot_min=round(min(feet) * 100, 1), foot_float=round(max(feet) * 100, 1),
               slide_step=round(slide_mx * 1000, 1), slide_total=round(max(slide_tot.values()) * 1000, 1),
               slide_limit=slide_limit(fn))
    mesh_eval(True)
    pose_frame(ARM, dict(STAND))
    return res


def probe(fn, t, tune=None):
    """單一格的穿模/間隙（mm），tune：暫時覆寫 TUNE 參數"""
    old = dict(TUNE)
    if tune: TUNE.update(tune)
    try:
        mesh_eval(False); pose_frame(ARM, fn(t)); ck = Checker(ARM) if "_CK" not in globals() else _CK
        r = ck.frame()
    finally:
        TUNE.clear(); TUNE.update(old)
    return {k: round(v, 1) for k, v in r.items() if k != "foot_min"}
