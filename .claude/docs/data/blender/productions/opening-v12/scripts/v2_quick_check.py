# ⑤ ⑦ 情境版的快速迭代檢查（2026-10-09，blender-motion-library references/fast-iteration.md 第 1～3 節；v2_walk_check.py 的整幕版）：
#   "$BL" -b couple.blend -P prod_cli.py -- --run v2_quick_check SHOT=v2_05 [TAG=after] [METRICS=1] [PREVIEW=1] [SHEET=1] [BEFORE=1]
# 1. METRICS：逐格（RATE，預設 30fps＝正式版）量每個角色：滑步、鞋底高度、手／腿穿模、每格轉角與速度突變、
#    骨盆前後傾、膝蓋彎曲、頭相對骨盆前後、手腕彎曲、臉有沒有被擋 → <WORK>/<幕>/<TAG>/metrics.json、summary.json
# 2. PREVIEW：整幕快速預覽（960×540、EEVEE 8 取樣、PREV_RATE 預設 24fps、不跑頭髮裙擺物理）→ videos/preview-v2/<NAME>.mp4
# 3. SHEET：多角度檢查圖（每個角色自己的關鍵時間點 × 正面／側面／背面／3/4；其他角色、樹籬、拱門暫時藏起來）
#    → pictures/preview-v2/<幕短名>_check[_<TAG>].jpg
# BEFORE=1：把每個角色命名空間的 STAND_FIX 關掉（＝男性站姿統一修正之前的動作庫），用來做改前對照
# 不改 set_v2.py／shots_v2.py：只呼叫 SHOTS[幕] 的 build／frame
import bpy, math, json, os, time, subprocess
from mathutils import Vector

MODE = "setup"
use("run_prod")

SID = str(globals().get("SHOT", "v2_05"))
TAG = str(globals().get("TAG", "after"))
WORK = os.path.join(r"D:\render-work\opening-v12\preview-v2-quick-0507", SID, TAG); os.makedirs(WORK, exist_ok=True)
S = SHOTS[SID]; S["build"](); stage(S["set"], cast=True)
ST = V2S[SID[3:]]

if SID == "v2_05":
    PB = V2S["PB"]
    CAST = [("groom", GR, "Cast_groom"), ("bride", B, "Cast_bride"), ("passerby", PB, "Cast_passerby")]
    SEGS = {"groom": ([("peace", 0.0, 3.6), ("→lookout 淡入", 3.6, 4.0), ("lookout", 4.0, 6.6), ("→nod 淡入", 6.6, 6.9), ("nod", 6.9, 9.0)]
                      if int(globals().get("LOOK_LEGACY", 0)) or int(globals().get("G05_LEGACY", 0)) else      # 第 3 輪：垂手＋頭看路人甲
                      [("peace", 0.0, 3.6), ("→垂手 淡入", 3.6, 4.2), ("垂手＋看路人甲", 4.2, 6.6), ("→nod 淡入", 6.6, 6.9), ("nod＋看路人甲", 6.9, 9.0)]),
            "bride": ([("捧花", 0.0, 3.6), ("→tilt 淡入", 3.6, 3.9), ("捧花＋tilt", 3.9, 6.3), ("→shake 淡入", 6.3, 6.6), ("捧花＋shake", 6.6, 9.0)]
                      if int(globals().get("LOOK_LEGACY", 0)) or int(globals().get("G05_LEGACY", 0)) else
                      [("捧花", 0.0, ST["look_b"][2]), ("捧花＋轉頭看路人甲", ST["look_b"][2], 9.0)]),
            "passerby": [("walk_in_photo 走", ST["t_in"], ST["t_in"] + ST["WI"].walk_end), ("轉身舉手機拍", ST["t_in"] + ST["WI"].walk_end, 6.7),
                         ("oops_bow", 6.7, 7.5), ("turn_exit", 7.5, 9.0)]}
    SHEET_KEYS = {"groom": [1.5, 4.0, 5.0, 6.6, 7.5, 8.6], "bride": [1.5, 4.6, 5.5, 7.0, 8.0, 8.9], "passerby": [4.6, 6.4, 7.2, 7.45, 7.75, 8.1]}
    VIEWS = [("正面", 0.0), ("側面", 90.0), ("背面", 180.0), ("3/4", 45.0)]
    T_ON = {"passerby": ST["t_in"]}
elif SID == "v2_02":                          # 2026-10-09 加：② 走路被鐵鎚敲頭（手腕反折修正）
    CAST = [("groom", GR, "Cast_groom"), ("bride", B, "Cast_bride")]
    if ST.get("dance"):                       # 2026-10-10 第 5 輪：跳舞版（真人轉身＋同一段查爾斯頓）
        tb = ST["t_bow"]; tt, td = D02["t_turn"], ST["t_dance"]
        sg = [("真人走路＋停步", 0.8, tt), ("真人轉身", tt, td), ("查爾斯頓", td, tb), ("鞠躬", tb, 9.0)]
        SEGS = {"groom": sg, "bride": sg}
        SHEET_KEYS = {"groom": [3.9, 4.6, 5.6, 6.3, 7.0, 8.6], "bride": [3.9, 4.6, 5.6, 6.3, 7.0, 8.6]}
        VIEWS = [("正面", 0.0), ("側面", 90.0), ("背面", 180.0), ("3/4", 45.0)]
        T_ON = {}
    else:
      SEGS = {"groom": [("真人走路＋停步", 0.8, 3.95), ("原地轉身（qa_skip）", 3.95, 4.45), ("sneak", 4.45, 6.0), ("被敲", 6.0, 7.3), ("鞠躬", 7.45, 9.0)],
            "bride": [("真人走路＋停步（提裙）", 0.8, 3.95), ("轉身＋伸手到背後", 3.95, 4.3), ("mallet_draw", 4.3, 5.0), ("跳起來敲", 5.0, 7.25), ("鞠躬", 7.25, 9.0)]}
      SHEET_KEYS = {"groom": [2.6, 3.5, 3.9, 4.6, 6.0, 8.2], "bride": [2.6, 3.5, 3.9, 5.5, 6.0, 8.2]}
      VIEWS = [("正面", 0.0), ("側面", 90.0), ("背面", 180.0), ("3/4", 45.0)]
      T_ON = {}
else:
    CAST = [("groom", GR, "Cast_groom"), ("bride", B, "Cast_bride")]
    if int(globals().get("V2_07_R2", 0)):         # 第 2 版（改前對照）
        segs = [("feed / fed", 0.0, 4.5), ("glass_pick", 4.5, 6.3), ("toast_sit", 6.3, 8.5), ("sip", 8.5, 12.0)]
        SEGS = {"groom": segs, "bride": segs}
        SHEET_KEYS = {"groom": [1.0, 2.5, 5.4, 7.2, 10.0], "bride": [1.0, 2.5, 5.4, 7.2, 10.0]}
        VIEWS = [("正面", 0.0), ("3/4", 45.0), ("側面", 90.0)]
    else:                                         # 2026-10-10 第 5 輪：toast2（碰杯 → 舉杯停留 → 直接喝 → 放下笑）
        segs = [("feed / fed", 0.0, 4.5), ("glass_pick", 4.5, 6.3), ("碰杯", 6.3, 7.65), ("舉杯停留", 7.65, 8.8), ("喝", 8.8, 10.15),
                ("放下＋笑", 10.15, 12.0)]
        SEGS = {"groom": segs, "bride": segs}
        SHEET_KEYS = {"groom": [1.0, 2.6, 5.1, 7.0, 8.3, 9.6, 11.0], "bride": [1.0, 2.6, 5.1, 7.0, 8.3, 9.6, 11.0]}
        VIEWS = [("正面", 0.0), ("3/4", 45.0), ("側面", 90.0), ("背面", 180.0)]
    T_ON = {}
_k = globals().get("SHEET_KEYS_OVERRIDE")
if _k:
    for w in SHEET_KEYS:
        SHEET_KEYS[w] = [float(x) for x in str(_k).split(",")]

if int(globals().get("HAND_LEGACY", 0)):        # 改前對照：mocap_retarget 2026-10-09 之前的手掌算法（手掌往回折）
    for _, ns, _c in CAST:
        ns["MOCAP_HAND_LEGACY"] = True
if int(globals().get("BEFORE", 0)):
    for _, ns, _c in CAST:
        ns["STAND_FIX"] = False
    print("BEFORE: STAND_FIX off", flush=True)

for who, ns, _ in CAST:
    if "Checker" not in ns:
        ns["use"]("check_lib")
CHK = {who: ns["Checker"](ns["ARM"], ns["WHO"]) for who, ns, _ in CAST}
for who, ns, _ in CAST:                       # 服裝版的鞋是 <who>_Cos_Shoes
    cs = bpy.data.objects.get(ns["WHO"] + "_Cos_Shoes")
    if cs is not None:
        CHK[who].shoes = cs


def bw(ns, name, end="head"):
    A = ns["ARM"]; pb = A.pose.bones[name]
    return A.matrix_world @ (pb.head if end == "head" else pb.tail)


def forward(ns):
    """骨盆的正前方（坐姿、轉身時腳尖不一定朝前，改用骨盆左右軸）"""
    l = bw(ns, "J_Bip_L_UpperLeg") - bw(ns, "J_Bip_R_UpperLeg"); l.z = 0
    if l.length < 1e-6:
        return Vector((0, -1, 0))
    l.normalize()
    return Vector((l.y, -l.x, 0.0))            # 左手方向轉 −90° ＝ 前方（VRoid 面向 −Y 時左腿在 +X）


def ang(a, b):
    return math.degrees(a.angle(b)) if a.length > 1e-9 and b.length > 1e-9 else 0.0


def measures(ns):
    f = forward(ns)
    hy = bw(ns, "J_Bip_C_Hips", "tail") - bw(ns, "J_Bip_C_Hips")
    out = dict(pelvis_tilt=round(math.degrees(math.atan2(hy.dot(f), hy.z)), 1))     # 骨盆骨頭往前斜幾度（VRoid rest 13.5）
    for sd in "LR":
        hip, kn, an = (bw(ns, f"J_Bip_{sd}_{n}") for n in ("UpperLeg", "LowerLeg", "Foot"))
        out[f"knee_{sd}"] = round(ang(kn - hip, an - kn), 1)
        el, wr = bw(ns, f"J_Bip_{sd}_LowerArm"), bw(ns, f"J_Bip_{sd}_Hand")
        out[f"wrist_{sd}"] = round(ang(wr - el, bw(ns, f"J_Bip_{sd}_Hand", "tail") - wr), 1)
    out["head_fwd_cm"] = round((bw(ns, "J_Bip_C_Head") - bw(ns, "J_Bip_C_Hips")).dot(f) * 100, 1)
    return out


def face_hits(ns, owner, cl):
    A = ns["ARM"]; k = ns["BODY_S"]
    Mh = world_of_rest(ns, "J_Bip_C_Head"); h0 = A.data.bones["J_Bip_C_Head"].head_local
    dg = bpy.context.evaluated_depsgraph_get(); out = {}
    for dx in (-0.035, 0.0, 0.035):
        for dz in (0.03, 0.06, 0.09, 0.12, 0.15):
            p = Mh @ (h0 + Vector((dx, -0.085, dz)) * k); d = p - cl
            hit, loc, nrm, idx, ob, M = sc.ray_cast(dg, cl, d.normalized(), distance=d.length - 0.03)
            if hit and ob is not None and not ob.name.startswith(owner) and ob.name != "G_Petals":
                out[ob.name] = out.get(ob.name, 0) + 1
    return out


FACE_CHECK = ("groom", "bride")               # 路人甲背對鏡頭，不量他的臉


def viewport_mods_off():
    """只渲染、不量網格時：所有網格的修改器關掉視窗評估（服裝的 Solidify／幾何節點不必每次 update 重算，擺姿勢 5.5 → 0.35 秒／格）；
    渲染走 show_render，畫面不變。之後不能再量變形後的網格（所以放在數字檢查之後）"""
    for o in bpy.data.objects:
        if o.type == "MESH":
            for m in o.modifiers:
                m.show_viewport = False

# ── 1. 逐格量 ──
if int(globals().get("METRICS", 1)):
    MR = int(globals().get("MRATE", FPS))
    PE = int(globals().get("PEN_EVERY", 3))  # 穿模／網格鞋底／臉被擋：每 PE 格量一次（網格變形很慢）；滑步、轉速、姿勢角度每格都量
    rows = []; prev = {}; vprev = {}
    n = int(round(S["dur"] * MR))
    t_start = time.time()
    for i in range(n):
        t = i / MR
        for who, ns, _ in CAST:
            mesh_eval(False, ns["ARM"].name)
        S["frame"](t); bpy.context.view_layer.update()
        heavy = i % PE == 0
        if heavy:
            for who, ns, _ in CAST:
                mesh_eval(True, ns["ARM"].name)
            bpy.context.view_layer.update()
        cl = sc.camera.matrix_world.translation
        r = dict(t=round(t, 3))
        for who, ns, _ in CAST:
            if t < T_ON.get(who, -1.0):
                continue
            cur = ns["sole_world"](ns["ARM"])
            sl = ns["slide_between"](prev[who], cur) if who in prev else {"L": None, "R": None}
            prev[who] = cur
            sole_min = min(p.z for sd in "LR" for p in cur[sd])
            if heavy:
                c = CHK[who].frame(); mesh_eval(True, ns["ARM"].name); bpy.context.view_layer.update()
                fb = face_hits(ns, ns["WHO"] + "_", cl) if who in FACE_CHECK else {}
            else:
                c = dict(foot_min=sole_min, pen_core=None, pen_hands=None, pen_legs=None); fb = {}
            vmax, vfoot = CHK[who].motion()
            if who not in vprev:
                vmax = vfoot = None
            jerk = None if vmax is None or vprev.get(who) is None else abs(vmax - vprev[who])
            vprev[who] = vmax if vmax is not None else 0.0
            r[who] = dict(slide_L_mm=None if sl["L"] is None else round(sl["L"] * 1000, 2), slide_R_mm=None if sl["R"] is None else round(sl["R"] * 1000, 2),
                          sole_min_cm=round(sole_min * 100, 2), foot_min_cm=round(c["foot_min"] * 100, 2) if heavy else None,
                          pen_core_mm=None if c["pen_core"] is None else round(c["pen_core"], 1),
                          pen_hands_mm=None if c["pen_hands"] is None else round(c["pen_hands"], 1),
                          pen_legs_mm=None if c["pen_legs"] is None else round(c["pen_legs"], 1), vmax=None if vmax is None else round(vmax, 1),
                          vfoot=None if vfoot is None else round(vfoot, 1), jerk=None if jerk is None else round(jerk, 1),
                          face_blocked=fb, **measures(ns))
        rows.append(r)
    json.dump(rows, open(os.path.join(WORK, "metrics.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print("QC_METRICS_DONE", SID, len(rows), "frames", round(time.time() - t_start, 1), "s", flush=True)

    def summ(who, a, b):
        sel = [(r["t"], r[who]) for r in rows if who in r and a <= r["t"] < b]
        def mx(key, f=max):
            v = [(x[key], t) for t, x in sel if x.get(key) is not None]
            if not v:
                return None
            best = f(v, key=lambda q: q[0])
            return [round(best[0], 2), best[1]]                     # [值, 在第幾秒]
        sl = [(v, t) for t, x in sel for v in (x["slide_L_mm"], x["slide_R_mm"]) if v is not None]
        tot = {sd: round(sum(x[f"slide_{sd}_mm"] or 0 for _, x in sel), 1) for sd in "LR"}
        fb = [t for t, x in sel if x["face_blocked"]]
        return dict(slide_step_max_mm=[round(max(sl)[0], 2), max(sl)[1]] if sl else None, slide_total_mm=tot,
                    sole_min_cm=mx("sole_min_cm", min), foot_min_cm=mx("foot_min_cm", min), foot_max_cm=mx("foot_min_cm", max), pen_core_mm=mx("pen_core_mm"), pen_hands_mm=mx("pen_hands_mm"),
                    pen_legs_mm=mx("pen_legs_mm"), vmax=mx("vmax"), vfoot=mx("vfoot"), jerk=mx("jerk"),
                    pelvis_tilt=(mx("pelvis_tilt", min), mx("pelvis_tilt")), knee_L=(mx("knee_L", min), mx("knee_L")), knee_R=(mx("knee_R", min), mx("knee_R")),
                    head_fwd_cm=(mx("head_fwd_cm", min), mx("head_fwd_cm")), wrist_L=mx("wrist_L"), wrist_R=mx("wrist_R"),
                    face_blocked=dict(first=fb[0], last=fb[-1], n=len(fb), by=sorted({k for t, x in sel if x["face_blocked"] for k in x["face_blocked"]})) if fb else None)

    SUMS = {}
    for who, ns, _ in CAST:
        SUMS[who] = {f"{lab} {a:.2f}-{b:.2f}": summ(who, a, b) for lab, a, b in SEGS[who]}
        SUMS[who]["整幕"] = summ(who, 0.0, S["dur"] + 1)
        for k_, v in SUMS[who].items():
            print("QC_SUM", SID, who, k_, json.dumps(v, ensure_ascii=False), flush=True)
    json.dump(SUMS, open(os.path.join(WORK, "summary.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)

# ── 2. 快速預覽 ──
if int(globals().get("PREVIEW", 1)):
    PR = int(globals().get("PREV_RATE", 24))
    fd = os.path.join(WORK, "frames"); os.makedirs(fd, exist_ok=True)
    viewport_mods_off()
    n = int(round(S["dur"] * PR)); t_start = time.time()
    i0 = int(globals().get("FROM", 0)); i1 = min(n, int(globals().get("UPTO", n)))   # 只渲 FROM～UPTO 格（分給好幾個背景 Blender 並行；已存在的格會跳過）
    for i in range(i0, i1):
        p = os.path.join(fd, f"{i + 1:04d}.jpg")
        if os.path.exists(p):
            continue
        S["frame"](i / PR)
        render_still(p, (960, 540), 8)
        if i % 24 == 0:
            print("QC_FRAME", SID, i + 1, "/", n, round(time.time() - t_start, 1), "s", flush=True)
    if globals().get("NO_MP4"):
        print("QC_PART_DONE", SID, i0, i1, flush=True); raise SystemExit
    name = str(globals().get("NAME") or (SID + "_quick"))
    mp4 = os.path.join(PROD, "videos", "preview-v2", name + ".mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(PR), "-i", os.path.join(fd, "%04d.jpg"), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "22", "-movflags", "+faststart", mp4], check=True)
    print("QC_PREVIEW", mp4, n, "frames", round(time.time() - t_start, 1), "s", flush=True)

# ── 3. 多角度檢查圖 ──
if int(globals().get("SHEET", 1)):
    HIDE = ("G_Hedge", "G_Arch", "G_ArchFlowers", "G_FlowerBed", "G_Trees", "G_Petals", "G_Cam", "G_Tripod", "G_OldCam", "V2_Easel", "V2_Board")
    hid = []
    for o in bpy.data.objects:
        if any(o.name.startswith(h) for h in HIDE) and not o.hide_render:
            o.hide_render = True; hid.append(o)
    viewport_mods_off()
    W, H = 400, 300; tiles = []; blocks = []; y0 = 0
    for who, ns, coll in CAST:
        others = [c for w, _, c in CAST if w != who]
        keys = SHEET_KEYS[who]
        blocks.append(dict(who=who, y=y0, keys=keys))
        for ci, t in enumerate(keys):
            S["frame"](t, cam=False)
            for c in others:
                show(c, False)
            show(coll, True)
            if who == "bride" and SID == "v2_05":
                v2_05_props(t)                        # 捧花跟著手
            for o in bpy.data.objects:                # 別人手上的道具（捧花、手機）也藏起來
                if o.name.startswith("G_Bouquet") or o.name.startswith("V2_Phone"):
                    o.hide_render = not ((who == "bride") == o.name.startswith("G_Bouquet") and who in ("bride", "passerby"))
            bpy.context.view_layer.update()
            f = forward(ns); left = Vector((-f.y, f.x, 0)); c0 = bw(ns, "J_Bip_C_Hips"); c0.z = max(0.62, c0.z * 0.98)
            for ri, (lab, a) in enumerate(VIEWS):
                r_ = math.radians(a); d = f * math.cos(r_) + left * math.sin(r_)
                look(c0 + d * 4.0 + Vector((0, 0, 0.1)), c0, 50.0)
                sc.camera.data.dof.use_dof = False
                p = os.path.join(WORK, f"_v_{who}_{ci}_{ri}.jpg"); render_still(p, (W, H), 8)
                tiles.append((110 + ci * W, y0 + 34 + ri * H, p))
        y0 += 34 + len(VIEWS) * H + 10
    for _, _, c in CAST:
        show(c, True)
    for o in hid:
        o.hide_render = False
    suffix = "" if TAG == "after" else "_" + TAG
    outp = os.path.join(PROD, "pictures", "preview-v2", f"{SID}_check{suffix}.jpg")
    ncol = max(len(b["keys"]) for b in blocks)
    lay = dict(W=W, H=H, Wt=110 + ncol * W, Ht=y0, blocks=blocks, views=[v[0] for v in VIEWS], tiles=tiles, out=outp,
               title=f"{SID} {TAG}")
    lp = os.path.join(WORK, "_layout.json"); json.dump(lay, open(lp, "w", encoding="utf8"), ensure_ascii=False)
    code = ("import json,sys;from PIL import Image,ImageDraw,ImageFont;L=json.load(open(sys.argv[1],encoding='utf8'));W,H=L['W'],L['H'];"
            "S=Image.new('RGB',(L['Wt'],L['Ht']),'white');d=ImageDraw.Draw(S);f=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',22);"
            "[S.paste(Image.open(p),(x,y)) for x,y,p in L['tiles']]\n"
            "for b in L['blocks']:\n"
            " d.text((6,b['y']+4),b['who'],font=f,fill='black')\n"
            " [d.text((110+i*W+8,b['y']+4),f'{k:.2f}s  '+L['title'],font=f,fill='black') for i,k in enumerate(b['keys'])]\n"
            " [d.text((6,b['y']+34+i*H+H//2),v,font=f,fill='black') for i,v in enumerate(L['views'])]\n"
            "S.save(L['out'],quality=86)")
    for o in bpy.data.objects:
        if o.name.startswith("G_Bouquet") or o.name.startswith("V2_Phone"):
            o.hide_render = False
    subprocess.run(["python", "-c", code, lp], check=True)
    print("QC_SHEET", outp, flush=True)
print("QC_DONE", SID, TAG, flush=True)
