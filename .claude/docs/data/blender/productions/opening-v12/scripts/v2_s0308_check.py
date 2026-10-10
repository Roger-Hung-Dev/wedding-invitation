# ③ v2_03／⑧ v2_08 的快速迭代（2026-10-09，fast-iteration.md 第 1～3 節；做法同 v2_walk_check.py，換成整幕）：
#   "$BL" -b couple.blend -P prod_cli.py -- --run v2_s0308_check SHOT=v2_03 RATE=24 [TAG=r1] [SHEET_KEYS=…] [METRICS=1 PREVIEW=1 SHEET=1]
# 1. 逐格量兩個角色：滑步、鞋底高度、手／腿／身體穿模、每格轉角、骨盆前後傾、膝蓋、頭相對骨盆、手腕、臉有沒有被擋、
#    頭頂／腳底／手最高點在畫面的位置（%）→ D:\render-work\opening-v12\preview-v2\quick\<幕>_<TAG>\metrics.json、summary.json
# 2. 快速預覽：960×540、EEVEE 8 取樣、無頭髮裙擺物理、整幕 → videos/preview-v2/<名>.mp4
#    （⑧：6.4 秒角色淡入 0.5 秒，預覽時另渲 set 層、用系統 Python 疊；正式版由合成做）
# 3. 多角度檢查圖：SHEET_KEYS × 正面／側面／背面／3/4，兩個角色上下排 → pictures/preview-v2/<幕>_check_<TAG>.jpg
import bpy, math, json, os, time, subprocess
from mathutils import Vector

MODE = "setup"
use("run_prod")
use("shots_v2_s0308")
use("shots_v2_s03carpet")

SID = str(globals().get("SHOT", "v2_03"))
TAG = str(globals().get("TAG", "r1"))
S = SHOTS[SID]; S["build"](); stage(S["set"], cast=True)
T0 = float(globals().get("T0", S["t0"])); T1 = float(globals().get("T1", S["t0"] + S["dur"]))
NAME = str(globals().get("OUTNAME") or {"v2_03": "s03_milestone_quick", "v2_08": "s08_arch_quick", "v2_03c": "s03_carpet_quick"}[SID])   # OUTNAME＝只重渲一段時另存的檔名
SHEETN = {"v2_03": "v2_03_check", "v2_08": "v2_08_check", "v2_03c": "v2_03c_check"}[SID]
_sk = globals().get("SHEET_KEYS") or S["stills"]
KEYS_SHEET = [float(x) for x in (_sk if isinstance(_sk, list) else str(_sk).split(","))]
OUTW = os.path.join(r"D:\render-work\opening-v12\preview-v2\quick", f"{SID}_{TAG}"); os.makedirs(OUTW, exist_ok=True)
CAST = [("groom", GR, "Cast_groom"), ("bride", B, "Cast_bride")]
for who, ns, _ in CAST:
    if "Checker" not in ns:
        ns["use"]("check_lib")
CHK = {who: ns["Checker"](ns["ARM"], ns["WHO"]) for who, ns, _ in CAST}
for who, ns, _ in CAST:
    cs = bpy.data.objects.get(ns["WHO"] + "_Cos_Shoes")
    if cs is not None:
        CHK[who].shoes = cs


def bw(ns, name, end="head"):
    A = ns["ARM"]; pb = A.pose.bones[name]
    return A.matrix_world @ (pb.head if end == "head" else pb.tail)


def forward(ns):
    f = Vector((0, 0, 0))
    for sd in "LR":
        d = bw(ns, f"J_Bip_{sd}_ToeBase") - bw(ns, f"J_Bip_{sd}_Foot"); d.z = 0; f += d
    return f.normalized() if f.length > 1e-6 else Vector((0, -1, 0))


def ang(a, b):
    return math.degrees(a.angle(b)) if a.length > 1e-9 and b.length > 1e-9 else 0.0


def measures(ns):
    f = forward(ns)
    hy = bw(ns, "J_Bip_C_Hips", "tail") - bw(ns, "J_Bip_C_Hips")
    out = dict(pelvis_tilt=round(math.degrees(math.atan2(hy.dot(f), hy.z)), 1))
    tr = bw(ns, "J_Bip_C_Neck") - bw(ns, "J_Bip_C_Hips")
    out["trunk_lean"] = round(math.degrees(math.atan2(tr.dot(f), tr.z)), 1)          # 上身（骨盆→脖子）往前傾幾度
    for sd in "LR":
        hip, kn, an = (bw(ns, f"J_Bip_{sd}_{n}") for n in ("UpperLeg", "LowerLeg", "Foot"))
        out[f"knee_{sd}"] = round(ang(kn - hip, an - kn), 1)
        el, wr = bw(ns, f"J_Bip_{sd}_LowerArm"), bw(ns, f"J_Bip_{sd}_Hand")
        out[f"wrist_{sd}"] = round(ang(wr - el, bw(ns, f"J_Bip_{sd}_Hand", "tail") - wr), 1)
    out["head_fwd_cm"] = round((bw(ns, "J_Bip_C_Head") - bw(ns, "J_Bip_C_Hips")).dot(f) * 100, 1)
    # 畫面位置（%，由上往下）：頭頂（頭骨往上 20 cm×體型）、腳底、兩手最高點
    k = ns["BODY_S"]
    def sy(p):
        return round(screen_px(p, (100, 100))[1], 1)
    out["scr_head"] = sy(bw(ns, "J_Bip_C_Head") + Vector((0, 0, 0.20 * k)))
    out["scr_feet"] = sy(min((bw(ns, f"J_Bip_{sd}_ToeBase") for sd in "LR"), key=lambda v: v.z))
    out["scr_hand"] = min(sy(bw(ns, f"J_Bip_{sd}_Hand", "tail")) for sd in "LR")
    out["scr_x"] = round(screen_px(bw(ns, "J_Bip_C_Hips"), (100, 100))[0], 1)
    return out


def face_hits(ns, owner, cl):
    A = ns["ARM"]; k = ns["BODY_S"]
    Mh = world_of_rest(ns, "J_Bip_C_Head"); h0 = A.data.bones["J_Bip_C_Head"].head_local
    dg = bpy.context.evaluated_depsgraph_get(); out = {}
    for dx in (-0.035, 0.0, 0.035):
        for dz in (0.03, 0.06, 0.09, 0.12, 0.15):
            p = Mh @ (h0 + Vector((dx, -0.085, dz)) * k); d = p - cl
            hit, loc, nrm, idx, ob, M = sc.ray_cast(dg, cl, d.normalized(), distance=d.length - 0.03)
            if hit and ob is not None and not ob.name.startswith(owner):
                out[ob.name] = out.get(ob.name, 0) + 1
    return out


n = int(round((T1 - T0) * FPS)) + 1
PEN_EVERY = int(globals().get("PEN_EVERY", 1))
rows = []
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080; sc.render.resolution_percentage = 100      # 畫面位置（%）照成片的 16:9 算
if globals().get("STILL_KEYS"):          # 試看：只渲幾張成片構圖（不量、不出影片）
    for who, ns, _ in CAST:
        mesh_eval(False, ns["ARM"].name)
    _vp = [(m, m.show_viewport) for o in bpy.data.objects if o.type == "MESH" for m in o.modifiers]   # 只渲染：修改器關掉視窗評估（見下面 FAST_POSE）；之後要量網格時再開回來
    for m, _ in _vp:
        m.show_viewport = False
    for t in [float(x) for x in globals()["STILL_KEYS"]]:
        S["frame"](t); render_still(os.path.join(OUTW, f"still_{t:05.2f}.jpg"), (960, 540), 8)
        print("QUICK_STILL", t, flush=True)
    for m, v in _vp:
        m.show_viewport = v
if int(globals().get("METRICS", 1)):
    for who, ns, _ in CAST:
        mesh_eval(True, ns["ARM"].name)
    prev = {}; t_start = time.time()
    for i in range(n):
        t = min(T1, T0 + i / FPS)
        S["frame"](t); bpy.context.view_layer.update()
        cl = sc.camera.matrix_world.translation
        r = dict(t=round(t, 3))
        for who, ns, _ in CAST:
            cur = ns["sole_world"](ns["ARM"])
            sl = ns["slide_between"](prev[who], cur) if who in prev else {"L": None, "R": None}
            prev[who] = cur
            if i % PEN_EVERY == 0 or i == n - 1:          # 穿模要算變形後的網格（慢）：每 PEN_EVERY 格量一次；腳底、滑步、轉角每格量
                mesh_eval(True, ns["ARM"].name)               # Checker.frame() 結尾會把網格變形關掉（mesh_eval(False)），每次量之前要重開
                try:
                    c = CHK[who].frame()
                except ValueError as e:                   # 鞋子網格全部離同一隻腳較近（量不到另一腳）：記下來，腳底改用鞋底取樣點
                    S_ = CHK[who]._co(CHK[who].shoes); mw_ = ns["ARM"].matrix_world
                    print("CHK_FAIL", who, round(t, 3), e, len(S_), [round(x, 3) for x in S_.mean(axis=0)],
                          [round(x, 3) for x in mw_ @ ns["ARM"].pose.bones["J_Bip_L_Foot"].head], flush=True)
                    mesh_eval(False)
                    c = dict(foot_min=min(p.z for sd in "LR" for p in cur[sd]), pen_core=-1.0, pen_hands=-1.0, pen_legs=-1.0)
            else:
                c = dict(foot_min=min(p.z for sd in "LR" for p in cur[sd]), pen_core=-0.0, pen_hands=-0.0, pen_legs=-0.0)
            vmax, vfoot = CHK[who].motion() if hasattr(CHK[who], "motion") else (None, None)
            r[who] = dict(slide_L_mm=None if sl["L"] is None else round(sl["L"] * 1000, 2), slide_R_mm=None if sl["R"] is None else round(sl["R"] * 1000, 2),
                          foot_min_cm=round(c["foot_min"] * 100, 2), pen_core_mm=round(c["pen_core"], 1), pen_hands_mm=round(c["pen_hands"], 1),
                          pen_legs_mm=round(c["pen_legs"], 1), vmax=None if vmax is None else round(vmax, 1), vfoot=None if vfoot is None else round(vfoot, 1),
                          face_blocked=face_hits(ns, ns["WHO"] + "_", cl), **measures(ns))
        rows.append(r)
    json.dump(rows, open(os.path.join(OUTW, "metrics.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print("QUICK_METRICS_DONE", SID, len(rows), "frames", round(time.time() - t_start, 1), "s", flush=True)
    skip = list(S.get("qa_skip", ()))

    def summ(who, a, b):
        sel = [x for x in rows if a <= x["t"] <= b]
        def mx(key, f=max):
            v = [x[who][key] for x in sel if x[who].get(key) is not None]
            return round(f(v), 2) if v else None
        sl = [(v, x["t"]) for x in sel if not any(p <= x["t"] <= q for p, q in skip) for v in (x[who]["slide_L_mm"], x[who]["slide_R_mm"]) if v is not None]
        fb = [x["t"] for x in sel if x[who]["face_blocked"] and not set(x[who]["face_blocked"]) <= {"G_Petals"}]
        fbo = sorted({o for x in sel for o in x[who]["face_blocked"]})
        w = max(sl) if sl else None
        return dict(slide_step_max_mm=w[0] if w else None, slide_at=w[1] if w else None, slide_total_mm=round(sum(v for v, _ in sl), 1),
                    foot_min_cm=(mx("foot_min_cm", min), mx("foot_min_cm")), pen_core_mm=mx("pen_core_mm"), pen_hands_mm=mx("pen_hands_mm"),
                    pen_legs_mm=mx("pen_legs_mm"), vmax=mx("vmax"), vfoot=mx("vfoot"), pelvis_tilt=(mx("pelvis_tilt", min), mx("pelvis_tilt")),
                    trunk_lean=(mx("trunk_lean", min), mx("trunk_lean")), knee_L=(mx("knee_L", min), mx("knee_L")), knee_R=(mx("knee_R", min), mx("knee_R")),
                    head_fwd_cm=(mx("head_fwd_cm", min), mx("head_fwd_cm")), wrist=max(mx("wrist_L") or 0, mx("wrist_R") or 0),
                    scr_head=mx("scr_head", min), scr_feet=mx("scr_feet"), scr_hand=mx("scr_hand", min), scr_x=(mx("scr_x", min), mx("scr_x")),
                    face_blocked=(fb[0], fb[-1], len(fb), fbo) if fb else (None, None, 0, fbo))
    if SID == "v2_03":
        st = V2S["03"]; ts = st["F"].settle
        W = dict(walk=(T0, S03["t99"]), stuck=(S03["t99"], st["F"].t_go), walk2=(st["F"].t_go, ts), turn=st["turn"], bride_turn=st["b_turn"],
                 after=(st["turn"][1], T1), all=(T0, T1))
    elif SID == "v2_03c":
        st = V2S["03c"]; FGc = st["FG"]
        W = dict(push=(T0, FGc.t_strain), strain=(FGc.t_strain, C3["t100"]), after=(C3["t100"], st["turn_g"][0]), turn=st["turn_g"],
                 bride_turn=st["turn_b"], cheer=(st["turn_b"][1], T1), all=(T0, T1))
    else:
        W = dict(idle=(T0, S08["act"]), act=(S08["act"], T1), all=(T0, T1))
    SUMS = {who: {k_: summ(who, a, b_) for k_, (a, b_) in W.items()} for who, _, _ in CAST}
    for who in SUMS:
        for k_, v in SUMS[who].items():
            print("QUICK_SUM", SID, who, k_, W[k_], json.dumps(v, ensure_ascii=False), flush=True)
    json.dump(dict(windows=W, sums=SUMS), open(os.path.join(OUTW, "summary.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)

# 之後只渲染、不量網格：所有網格的修改器關掉視窗評估（服裝的 Solidify／幾何節點每次 view_layer.update 都會重算，擺一格要 5 秒以上；
# 渲染走 show_render，畫面不變。做法同 quick_tweak.py）。量穿模的第 1 段已經在前面跑完
if int(globals().get("FAST_POSE", 1)):
    for o in bpy.data.objects:
        if o.type == "MESH":
            for m in o.modifiers:
                m.show_viewport = False

# ── 2. 快速預覽 ──
if int(globals().get("PREVIEW", 1)):
    fd = os.path.join(OUTW, "frames"); os.makedirs(fd, exist_ok=True)
    for who, ns, _ in CAST:
        mesh_eval(False, ns["ARM"].name)
    fade = SID == "v2_08"
    if fade:
        fs = os.path.join(OUTW, "frames_set"); os.makedirs(fs, exist_ok=True)
    t_start = time.time()
    for i in range(n):
        t = min(T1, T0 + i / FPS)
        S["frame"](t)
        render_still(os.path.join(fd, f"{i + 1:04d}.jpg"), (960, 540), 8)
        if fade and t < S08["act"] + 0.5:
            show("Cast_bride", False); show("Cast_groom", False)
            render_still(os.path.join(fs, f"{i + 1:04d}.jpg"), (960, 540), 8)
            show("Cast_bride", True); show("Cast_groom", True)
    if fade:          # 角色 6.4 秒起淡入 0.5 秒（set 墊底、beauty 疊上）
        code = ("import sys,os;from PIL import Image;fd,fs,t0,fps,a0,a1=sys.argv[1],sys.argv[2],*map(float,sys.argv[3:7])\n"
                "for f in sorted(os.listdir(fs)):\n"
                " i=int(f[:4]);t=t0+(i-1)/fps;a=max(0,min(1,(t-a0)/(a1-a0)));a=a*a*(3-2*a)\n"
                " Image.blend(Image.open(os.path.join(fs,f)),Image.open(os.path.join(fd,f)),a).save(os.path.join(fd,f),quality=90)")
        subprocess.run(["python", "-c", code, fd, fs, str(T0), str(FPS), str(S08["act"]), str(S08["act"] + 0.5)], check=True)
    mp4 = os.path.join(PROD, "videos", "preview-v2", NAME + ".mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", os.path.join(fd, "%04d.jpg"), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "22", mp4], check=True)
    print("QUICK_PREVIEW", mp4, n, "frames", round(time.time() - t_start, 1), "s", flush=True)

# ── 3. 多角度檢查圖 ──
if int(globals().get("SHEET", 1)):
    HIDE = ("G_Hedge", "G_Arch", "G_ArchFlowers", "G_FlowerBed", "G_Trees", "G_Petals")
    for nm in HIDE:
        o = bpy.data.objects.get(nm)
        if o: o.hide_render = True
    _cpw = [o for o in bpy.data.objects if o.name.startswith("CP_Wall") and not o.hide_render]     # ③ 推紅毯：文字牆會擋住檢查圖的相機
    for o in _cpw:
        o.hide_render = True
    VIEWS = [("正面", 0.0), ("側面", 90.0), ("背面", 180.0), ("3/4", 45.0)]
    W_, H_ = 360, 300; tiles = []; labels = []
    for wi, (who, ns, coll) in enumerate(CAST):
        other = [c_ for w, _, c_ in CAST if w != who][0]
        show(other, False)
        for ci, t in enumerate(KEYS_SHEET):
            S["frame"](t, cam=False); bpy.context.view_layer.update()
            f = forward(ns); left = Vector((-f.y, f.x, 0)); c = bw(ns, "J_Bip_C_Hips"); c.z = 0.88
            for ri, (lab, a) in enumerate(VIEWS):
                r_ = math.radians(a); d = f * math.cos(r_) + left * math.sin(r_)
                look(c + d * 3.9 + Vector((0, 0, 0.15)), c, 50.0)
                sc.camera.data.dof.use_dof = False
                p = os.path.join(OUTW, f"_v_{who}_{ci}_{ri}.jpg"); render_still(p, (W_, H_), 8)
                tiles.append((ci, wi * len(VIEWS) + ri, p))
        show(other, True)
        labels += [f"{'新郎' if who == 'groom' else '新娘'} {v[0]}" for v in VIEWS]
    for nm in HIDE:
        o = bpy.data.objects.get(nm)
        if o: o.hide_render = False
    for o in _cpw:
        o.hide_render = False
    outp = os.path.join(PROD, "pictures", "preview-v2", f"{SHEETN}_{TAG}.jpg")
    lay = dict(W=W_, H=H_, keys=KEYS_SHEET, views=labels, tiles=tiles, out=outp, title=f"{SID} {TAG}")
    lp = os.path.join(OUTW, "_layout.json"); json.dump(lay, open(lp, "w", encoding="utf8"), ensure_ascii=False)
    code = ("import json,sys;from PIL import Image,ImageDraw,ImageFont;L=json.load(open(sys.argv[1],encoding='utf8'));W,H=L['W'],L['H'];"
            "S=Image.new('RGB',(W*len(L['keys'])+130,H*len(L['views'])+34),'white');d=ImageDraw.Draw(S);f=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',20);"
            "[S.paste(Image.open(p),(130+c*W,34+r*H)) for c,r,p in L['tiles']];"
            "[d.text((130+i*W+8,4),f'{k:.2f}s',font=f,fill='black') for i,k in enumerate(L['keys'])];"
            "[d.text((6,34+i*H+H//2),v,font=f,fill='black') for i,v in enumerate(L['views'])];d.text((6,4),L['title'],font=f,fill='black');S.save(L['out'],quality=86)")
    subprocess.run(["python", "-c", code, lp], check=True)
    print("QUICK_SHEET", outp, flush=True)
print("QUICK_CHECK_DONE", SID, flush=True)
