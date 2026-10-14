# 第 3 關自我審查（2026-10-11，使用者指定四個重點）：正式版骨骼（FINAL=1）逐格掃描
#   1 動作生硬：整個人停住 ≥0.8 秒；手／頭／骨盆加速度異常（換段時跳一下）
#   2 非人類動作：手肘、膝蓋反折或往側面彎；手腕彎 >80°；手腕扭 >60°、前臂扭 >110°（扭麻花）；脖子轉 >75°、抬低 >45°；腰扭 >50°
#   3 方向角度：頭仰／低 >40°；頭＋眼珠（自然範圍左右 18°、上下 10°）還對不到要看的人 >10°；走路時身體和前進方向差 >60°
#   4 穿模：身體各段當膠囊，手／手臂和自己或別人的身體、頭、腿重疊 >1.5 cm；腳低於地板 >1.5 cm；關節進到道具（桌子、柱子、卷子）裡
# "$BL" -b blend/couple.blend -P scripts/mx_audit.py -- <幕> [<幕>…] → D:\render-work\mixamo\audit\s<幕>.txt（＋ .json）
# 規範：blender-motion-library references/fast-iteration.md §0.6。開發時的工作複本在 D:\render-work\mixamo\tools\pose_audit.py
import bpy, os, sys, math, json, re
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
SIDS = [a for a in args if "=" not in a]
OUTD = r"D:\render-work\mixamo\audit"; os.makedirs(OUTD, exist_ok=True)
SCR = r"D:\SideProject\wedding-invitation\.claude\docs\data\blender\productions\opening-v12\scripts"
MXP = os.path.join(SCR, "mx_skeleton.py")

# 眼珠看的目標：直接從 mx_preview.py 讀 GAZE（同一份設定）
_src = open(os.path.join(SCR, "mx_preview.py"), encoding="utf8").read()
_m = re.search(r"^GAZE = \{.*?^\}\n", _src, re.S | re.M)
OC_LENS = (-2.05, -2.35, 1.31)
GAZE = eval(_m.group(0)[len("GAZE = "):], {"OC_LENS": OC_LENS}) if _m else {}

FINGERS = ("Thumb", "Index", "Middle", "Ring", "Little")
# 膠囊半徑（m）：穿衣服的大概粗細
RAD = {"groom": dict(torso=0.13, head=0.105, uarm=0.05, farm=0.042, hand=0.035, thigh=0.075, shin=0.055),
       "bride": dict(torso=0.11, head=0.10, uarm=0.04, farm=0.035, hand=0.032, thigh=0.07, shin=0.05),
       "passerby": dict(torso=0.12, head=0.105, uarm=0.048, farm=0.04, hand=0.035, thigh=0.072, shin=0.052)}


def seg_dist(p1, q1, p2, q2):
    """兩線段最近距離"""
    d1 = q1 - p1; d2 = q2 - p2; r = p1 - p2
    a = d1.dot(d1); e = d2.dot(d2); f = d2.dot(r)
    if a < 1e-9 and e < 1e-9:
        return (p1 - p2).length
    if a < 1e-9:
        s = 0.0; t = max(0.0, min(1.0, f / e))
    else:
        c = d1.dot(r)
        if e < 1e-9:
            t = 0.0; s = max(0.0, min(1.0, -c / a))
        else:
            b = d1.dot(d2); den = a * e - b * b
            s = max(0.0, min(1.0, (b * f - c * e) / den)) if den > 1e-12 else 0.0
            t = (b * s + f) / e
            if t < 0:
                t = 0.0; s = max(0.0, min(1.0, -c / a))
            elif t > 1:
                t = 1.0; s = max(0.0, min(1.0, (b - c) / a))
    return ((p1 + d1 * s) - (p2 + d2 * t)).length


def capsules(who, P, T, R):
    r = RAD.get(who, RAD["groom"])
    hd = P["J_Bip_C_Head"]
    caps = {"torso": (P["J_Bip_C_Hips"] + Vector((0, 0, 0.05)), P["J_Bip_C_UpperChest"] + Vector((0, 0, 0.06)), r["torso"]),
            "head": (hd + Vector((0, 0, 0.07)), hd + Vector((0, 0, 0.11)), r["head"])}
    for s in "LR":
        caps[f"uarm{s}"] = (P[f"J_Bip_{s}_UpperArm"], P[f"J_Bip_{s}_LowerArm"], r["uarm"])
        caps[f"farm{s}"] = (P[f"J_Bip_{s}_LowerArm"], P[f"J_Bip_{s}_Hand"], r["farm"])
        palm = (P[f"J_Bip_{s}_Hand"] + P[f"J_Bip_{s}_Middle1"]) * 0.5
        caps[f"hand{s}"] = (P[f"J_Bip_{s}_Hand"], P[f"J_Bip_{s}_Middle1"] + (P[f"J_Bip_{s}_Middle1"] - P[f"J_Bip_{s}_Hand"]) * 0.6, r["hand"])
        caps[f"thigh{s}"] = (P[f"J_Bip_{s}_UpperLeg"], P[f"J_Bip_{s}_LowerLeg"], r["thigh"])
        caps[f"shin{s}"] = (P[f"J_Bip_{s}_LowerLeg"], P[f"J_Bip_{s}_Foot"], r["shin"])
    return caps


ADJ = {("uarmL", "torso"), ("uarmR", "torso"), ("thighL", "torso"), ("thighR", "torso"), ("uarmL", "farmL"), ("uarmR", "farmR"),
       ("farmL", "handL"), ("farmR", "handR"), ("thighL", "shinL"), ("thighR", "shinR"), ("thighL", "thighR"), ("head", "torso")}
SELF_PAIRS = [(a, b) for a in ("farmL", "farmR", "handL", "handR") for b in ("torso", "head", "thighL", "thighR")] + \
             [("handL", "handR"), ("farmL", "farmR"), ("handL", "farmR"), ("handR", "farmL"), ("uarmL", "head"), ("uarmR", "head")]


def axis(T, R, b, v):
    return (R[b] @ T.rest_q[b].inverted()) @ Vector(v)


def ang(u, v):
    return math.degrees(u.angle(v)) if u.length > 1e-6 and v.length > 1e-6 else 0.0


def perp(v, ax):
    return v - ax * v.dot(ax)


G = {}


def twist(T, R, b_parent, b_child, ax=None, ref=None):
    """用動作庫的 swing-twist 拆法（mixamo_retarget._twist_about），手臂舉到垂直也穩定"""
    return G["_twist_about"](T, R, b_parent, b_child)


def in_prop(p, pr, margin=0.0):
    if pr["kind"] == "box":
        mn, mx = pr["min"], pr["max"]
        return all(mn[k] + margin < p[k] < mx[k] - margin for k in range(3))
    if pr["kind"] == "cyl":
        c = pr["c"]; r = pr["r"]; ax = pr.get("axis", "z")
        if ax == "x":
            return (math.hypot(p.y - c[1], p.z - c[2]) < r - margin) and pr.get("x0", -99) < p.x < pr.get("x1", 99)
        return math.hypot(p.x - c[0], p.y - c[1]) < r - margin and pr["z0"] + margin < p.z < pr["z1"] - margin
    return False


def merge(hits, gap=4):
    """[(frame, sev, detail)…] → [(f0, f1, 最嚴重的 sev, detail)]；照「角色＋部位」（detail 數字前的字）分開合併，
    不同角色、不同部位的命中不會被串成同一段（2026-10-11 修：之前 ⑤ 被串成「0～9 秒整段」）"""
    import re as _re
    groups = {}
    for f, val, det in hits:
        key = _re.split(r"[-+]?\d", det, maxsplit=1)[0]
        groups.setdefault(key, []).append((f, val, det))
    out = []
    for key, hs in groups.items():
        cur = None
        for f, val, det in sorted(hs):
            if cur and f - cur[1] <= gap:
                cur = (cur[0], f, max(cur[2], val), det if val >= cur[2] else cur[3])
            else:
                if cur:
                    out.append(cur)
                cur = (f, f, val, det)
        if cur:
            out.append(cur)
    return sorted(out)


def audit(sid):
    MX = {"__name__": "mx_lib", "MX_LIB": True, "MX_OPT": {"FINAL": "1"}}
    exec(compile(open(MXP, encoding="utf8").read(), MXP, "exec"), MX)
    out, poses = MX["build"](sid, write=False)
    G.update(MX["_g"])
    T = {w: MX["tgt"](w) for w in poses}
    fps = 30
    N = min(len(p) for p in poses.values())
    POS = {w: [T[w].fk(*poses[w][i]) for i in range(N)] for w in poses}
    props = [p for p in out.get("props", []) if p.get("kind") in ("box", "cyl")]
    cam = Vector(out["cam"]["pos"]) if out.get("cam") else None
    F = {k: [] for k in ("1 停住", "1 跳一下", "2 手肘", "2 膝蓋", "2 手腕彎", "2 手腕扭", "2 前臂扭", "2 上臂扭", "2 脖子", "2 腰扭",
                         "3 頭仰低", "3 看不到人", "3 側著走", "4 自己穿模", "4 和別人穿模", "4 腳進地板", "4 進道具", "4 進裙子")}
    for w in poses:
        Tw = T[w]
        for i in range(N):
            R, h = poses[w][i]; P = POS[w][i]; t = i / fps
            # ── 1 生硬 ──
            if 1 <= i < N - 1:
                for b, lim in (("J_Bip_L_Hand", 40.0), ("J_Bip_R_Hand", 40.0), ("J_Bip_C_Head", 18.0), ("J_Bip_C_Hips", 10.0)):
                    a = (POS[w][i + 1][b] - 2 * P[b] + POS[w][i - 1][b]).length * fps * fps
                    if a > lim:
                        F["1 跳一下"].append((i, a / lim, f"{w} {b[6:]} 加速度 {a:.0f} m/s²（上限 {lim:.0f}）"))
            # ── 2 關節 ──
            for s in "LR":
                ua, la, hn = f"J_Bip_{s}_UpperArm", f"J_Bip_{s}_LowerArm", f"J_Bip_{s}_Hand"
                u = (P[la] - P[ua]).normalized(); fa = (P[hn] - P[la]).normalized()
                bend = ang(u, fa)
                if bend > 15:
                    fr = perp(axis(Tw, R, ua, (0, -1, 0)), u).normalized(); fp = perp(fa, u).normalized()
                    off = ang(fr, fp)
                    if off > 70:
                        F["2 手肘"].append((i, off / 70, f"{w} {s} 手肘往{'後' if off > 120 else '側面'}彎（偏 {off:.0f}°，彎 {bend:.0f}°）"))
                hd_ = (P[f"J_Bip_{s}_Middle1"] - P[hn]).normalized()
                wb = ang(fa, hd_)
                if wb > 80:
                    F["2 手腕彎"].append((i, wb / 80, f"{w} {s} 手腕彎 {wb:.0f}°"))
                tw = twist(Tw, R, la, hn, fa)
                if abs(tw) > 60:
                    F["2 手腕扭"].append((i, abs(tw) / 60, f"{w} {s} 手腕扭 {tw:+.0f}°"))
                tw2 = twist(Tw, R, ua, la, fa)
                if abs(tw2) > 110:
                    F["2 前臂扭"].append((i, abs(tw2) / 110, f"{w} {s} 前臂扭 {tw2:+.0f}°"))
                tw3 = twist(Tw, R, f"J_Bip_{s}_Shoulder", ua, u)
                if abs(tw3) > 110:
                    F["2 上臂扭"].append((i, abs(tw3) / 110, f"{w} {s} 上臂相對肩膀扭 {tw3:+.0f}°"))
                ul, ll, ft = f"J_Bip_{s}_UpperLeg", f"J_Bip_{s}_LowerLeg", f"J_Bip_{s}_Foot"
                th = (P[ll] - P[ul]).normalized(); sh = (P[ft] - P[ll]).normalized()
                kb = ang(th, sh)
                if kb > 12:
                    bk = perp(axis(Tw, R, ul, (0, 1, 0)), th).normalized(); sp = perp(sh, th).normalized()
                    off = ang(bk, sp)
                    if off > 70:
                        F["2 膝蓋"].append((i, off / 70, f"{w} {s} 膝蓋往{'前' if off > 120 else '側面'}彎（偏 {off:.0f}°，彎 {kb:.0f}°）"))
            chest_f = axis(Tw, R, "J_Bip_C_UpperChest", (0, -1, 0)); head_f = axis(Tw, R, "J_Bip_C_Head", (0, -1, 0))
            hips_f = axis(Tw, R, "J_Bip_C_Hips", (0, -1, 0))
            up = Vector((0, 0, 1))
            def yaw(v):
                return math.degrees(math.atan2(v.y, v.x))
            def dyaw(a, b):
                d = (yaw(a) - yaw(b) + 180) % 360 - 180; return d
            def pitch(v):
                return math.degrees(math.atan2(v.z, math.hypot(v.x, v.y)))
            ny = dyaw(head_f, chest_f); npch = pitch(head_f) - pitch(chest_f)
            if abs(ny) > 75 or abs(npch) > 45:
                F["2 脖子"].append((i, max(abs(ny) / 75, abs(npch) / 45), f"{w} 脖子轉 {ny:+.0f}°、抬低 {npch:+.0f}°（相對胸口）"))
            sy = dyaw(chest_f, hips_f)
            if abs(sy) > 50:
                F["2 腰扭"].append((i, abs(sy) / 50, f"{w} 胸口相對骨盆扭 {sy:+.0f}°"))
            # ── 3 方向 ──
            hp = pitch(head_f)
            if abs(hp) > 40:
                F["3 頭仰低"].append((i, abs(hp) / 40, f"{w} 頭{'仰' if hp > 0 else '低'} {abs(hp):.0f}°"))
            for a_, b_, tg in GAZE.get(sid, {}).get(w, []):
                if a_ + 0.3 <= t <= b_:
                    if isinstance(tg, str) and tg != "cam":
                        if tg not in POS:
                            continue
                        tp = POS[tg][i]["J_Bip_C_Head"] + Vector((0, 0, 0.06))
                    else:
                        tp = cam if tg == "cam" else Vector(tg)
                    eye = P["J_Bip_C_Head"] + Vector((0, 0, 0.06))
                    d = tp - eye
                    lft = axis(Tw, R, "J_Bip_C_Head", (1, 0, 0)); upv = axis(Tw, R, "J_Bip_C_Head", (0, 0, 1))
                    gy = math.degrees(math.atan2(d.dot(lft), max(1e-4, d.dot(head_f))))
                    gp = math.degrees(math.atan2(d.dot(upv), math.hypot(d.dot(lft), d.dot(head_f))))
                    if d.dot(head_f) < 0:
                        gy = 180.0
                    res = math.hypot(max(0, abs(gy) - 18), max(0, abs(gp) - 10))   # 眼珠看起來自然的範圍：左右 18°、上下 10°（mx_preview EYE_GAIN，2026-10-11 第 2 輪修正）
                    if math.degrees(head_f.angle(d)) > 65:               # 對方在頭看不到的角度：mx_preview 會讓眼珠回正，不算「看不到」
                        continue
                    if res > 10:
                        F["3 看不到人"].append((i, res / 20, f"{w} 看 {tg if isinstance(tg, str) else '固定點'}：頭＋眼珠還差 {res:.0f}°（左右 {gy:+.0f}° 上下 {gp:+.0f}°）"))
            if 1 <= i < N - 1:
                v = (POS[w][i + 1]["J_Bip_C_Hips"] - POS[w][i - 1]["J_Bip_C_Hips"]) * (fps / 2); v.z = 0
                if v.length > 0.35:
                    bf = hips_f.copy(); bf.z = 0
                    if ang(v, bf) > 60:
                        F["3 側著走"].append((i, ang(v, bf) / 60, f"{w} 移動 {v.length:.2f} m/s，身體和前進方向差 {ang(v, bf):.0f}°"))
            # ── 4 穿模 ──
            C = capsules(w, P, Tw, R)
            for a_, b_ in SELF_PAIRS:
                if (a_, b_) in ADJ or (b_, a_) in ADJ:
                    continue
                pa, qa, ra = C[a_]; pb, qb, rb = C[b_]
                pen = ra + rb - seg_dist(pa, qa, pb, qb)
                if pen > 0.015:
                    F["4 自己穿模"].append((i, pen / 0.015, f"{w} {a_}×{b_} 重疊 {pen * 100:.1f} cm"))
            for o in poses:
                if o <= w:
                    continue
                C2 = capsules(o, POS[o][i], T[o], poses[o][i][0])
                for a_, ca in C.items():
                    for b_, cb in C2.items():
                        pen = ca[2] + cb[2] - seg_dist(ca[0], ca[1], cb[0], cb[1])
                        if pen > 0.015:
                            F["4 和別人穿模"].append((i, pen / 0.015, f"{w}.{a_} × {o}.{b_} 重疊 {pen * 100:.1f} cm"))
            for s in "LR":
                for b in (f"J_Bip_{s}_Foot", f"J_Bip_{s}_ToeBase"):
                    if P[b].z < -0.015:
                        F["4 腳進地板"].append((i, -P[b].z / 0.015, f"{w} {b[6:]} 低於地板 {-P[b].z * 100:.1f} cm"))
            for pr in props:
                if not pr.get("on", 0) <= t:
                    continue
                for b in ("J_Bip_L_Hand", "J_Bip_R_Hand", "J_Bip_L_LowerArm", "J_Bip_R_LowerArm", "J_Bip_L_Foot", "J_Bip_R_Foot",
                          "J_Bip_L_LowerLeg", "J_Bip_R_LowerLeg", "J_Bip_C_Head", "J_Bip_C_UpperChest"):
                    pp = pr
                    if pr.get("path"):                                  # 會動的道具：照路徑的位置
                        pth = pr["path"]; cur = pth[0]
                        for q in pth:
                            if q[0] <= t:
                                cur = q
                        pp = dict(pr); c = list(pr.get("c", [0, 0, 0]))
                        if pr["kind"] == "cyl" and pr.get("axis") == "x":
                            c = [c[0], cur[2], c[2] if len(c) > 2 else pr.get("r", 0)]
                        else:
                            c = [cur[1], cur[2]] + ([cur[3]] if len(cur) > 3 else [])
                        pp["c"] = c
                    if in_prop(P[b], pp, margin=0.01):
                        F["4 進道具"].append((i, 1.0, f"{w} {b[6:]} 在「{pr.get('name', '道具')}」裡面"))
    # 蓬裙（硬殼、預覽不跑物理）：圓錐，地面半徑 r_floor、腰 h_waist 高時 r_waist，中心跟著新娘骨盆
    sk = out.get("skirt") or {}
    if sk.get("who") in POS:
        sw = sk["who"]
        for i in range(N):
            hip = POS[sw][i]["J_Bip_C_Hips"]; t = i / fps
            def inside(p):
                if p.z > sk["h_waist"] or p.z < 0.02:
                    return -1.0
                r = sk["r_floor"] + (sk["r_waist"] - sk["r_floor"]) * p.z / sk["h_waist"]
                return r - math.hypot(p.x - hip.x, p.y - hip.y)
            for w in POS:
                pts = ["J_Bip_L_Hand", "J_Bip_R_Hand", "J_Bip_L_Middle1", "J_Bip_R_Middle1"] +                       ([] if w == sw else ["J_Bip_L_LowerLeg", "J_Bip_R_LowerLeg", "J_Bip_L_Foot", "J_Bip_R_Foot", "J_Bip_L_UpperLeg", "J_Bip_R_UpperLeg"])
                for b in pts:
                    d = inside(POS[w][i][b])
                    if d > 0.02:
                        F["4 進裙子"].append((i, d / 0.02, f"{w} {b[6:]} 在{('自己' if w == sw else '新娘')}的蓬裙裡 {d * 100:.0f} cm"))
    # 停住：全身（不含手指）每格位移總和
    for w in poses:
        still = []
        for i in range(1, N):
            m = sum((POS[w][i][b] - POS[w][i - 1][b]).length for b in POS[w][i] if not any(f in b for f in FINGERS))
            still.append(m * 30)
        run = 0
        for i, m in enumerate(still):
            run = run + 1 if m < 0.06 else 0
            if run == 24:
                F["1 停住"].append((i - 23, 1.0, f"{w} 全身幾乎不動（每秒總位移 <6 cm）"))
            elif run > 24:
                F["1 停住"].append((i, 1.0, f"{w} 全身幾乎不動（每秒總位移 <6 cm）"))
    lines = [f"=== ⑤ ⑦ … 第 {sid} 幕 自我審查（{N / fps:.1f} 秒）==="]
    res = {}
    for k, hits in F.items():
        segs = merge(hits)
        res[k] = [dict(t0=round(a / fps, 2), t1=round(b / fps, 2), sev=round(v, 2), detail=d) for a, b, v, d in segs]
        lines.append(f"[{k}] {len(segs)} 段")
        for s_ in res[k][:12]:
            lines.append(f"    {s_['t0']:5.2f}～{s_['t1']:5.2f}s ×{s_['sev']:.1f}  {s_['detail']}")
        if len(res[k]) > 12:
            lines.append(f"    …還有 {len(res[k]) - 12} 段")
    txt = "\n".join(lines)
    open(os.path.join(OUTD, f"s{sid}.txt"), "w", encoding="utf8").write(txt)
    json.dump(res, open(os.path.join(OUTD, f"s{sid}.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print("AUDIT_DONE", sid, flush=True)


for sid in SIDS:
    audit(sid)
