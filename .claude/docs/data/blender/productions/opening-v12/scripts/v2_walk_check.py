# ② 走路段的快速迭代檢查（2026-10-08，blender-motion-library references/fast-iteration.md 第 1～3 節）：
#   "$BL" -b couple.blend -P prod_cli.py -- --run v2_walk_check RATE=24 [T0=0.8 T1=4.4] [TAG=after] [SHEET_KEYS=3.2,3.6,3.95,4.45] [PREVIEW=1]
# 1. 逐格（24fps）量兩個角色：滑步（check_lib.slide_between）、鞋底高度與手／腿穿模（check_lib.Checker）、每格轉角（Checker.motion）、
#    骨盆前後傾、膝蓋彎曲、頭相對骨盆前後、手腕彎曲、臉有沒有被擋 → D:\render-work\opening-v12\preview-v2\walk_check\<TAG>\metrics.json，主控台印摘要
# 2. 快速預覽：960×540、EEVEE 8 取樣、無頭髮裙擺物理 → walk_check\<TAG>\frames\ → videos/preview-v2/s02_walk_quick_<TAG>.mp4
# 3. 多角度檢查圖：SHEET_KEYS 每個時間點 × 正面／側面／背面／3/4，每個角色一張（另一個角色、樹籬、拱門暫時藏起來）
#    → pictures/preview-v2/v2_02_walk_check_<who>_<TAG>.jpg
import bpy, math, json, os, time, subprocess
from mathutils import Vector

MODE = "setup"
use("run_prod")

TAG = str(globals().get("TAG", "after"))
T0 = float(globals().get("T0", 0.8)); T1 = float(globals().get("T1", 4.4))
_sk = globals().get("SHEET_KEYS", "3.2,3.6,3.95,4.45")          # prod_cli 會把 *KEYS 變成清單
KEYS_SHEET = [float(x) for x in (_sk if isinstance(_sk, list) else str(_sk).split(","))]
OUTW = os.path.join(r"D:\render-work\opening-v12\preview-v2\walk_check", TAG); os.makedirs(OUTW, exist_ok=True)
S = SHOTS["v2_02"]; S["build"](); stage(S["set"], cast=True)
ST = V2S["02"]
CAST = [("groom", GR, "Cast_groom"), ("bride", B, "Cast_bride")]
for who, ns, _ in CAST:
    if "Checker" not in ns:
        ns["use"]("check_lib")
CHK = {who: ns["Checker"](ns["ARM"], ns["WHO"]) for who, ns, _ in CAST}
for who, ns, _ in CAST:                       # 服裝版穿的是 <who>_Cos_Shoes（新郎皮鞋）；check_lib 預設量 <who>_Shoes（便服鞋，藏起來時取不到頂點）
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
    tilt = math.degrees(math.atan2(hy.dot(f), hy.z))                       # 骨盆骨頭往前斜幾度（VRoid rest 13.5）
    out = dict(pelvis_tilt=round(tilt, 1))
    for sd in "LR":
        hip, kn, an = (bw(ns, f"J_Bip_{sd}_{n}") for n in ("UpperLeg", "LowerLeg", "Foot"))
        out[f"knee_{sd}"] = round(ang(kn - hip, an - kn), 1)
        el, wr = bw(ns, f"J_Bip_{sd}_LowerArm"), bw(ns, f"J_Bip_{sd}_Hand")
        ht = bw(ns, f"J_Bip_{sd}_Hand", "tail")
        out[f"wrist_{sd}"] = round(ang(wr - el, ht - wr), 1)
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
            if hit and ob is not None and not ob.name.startswith(owner):
                out[ob.name] = out.get(ob.name, 0) + 1
    return out


# ── 1. 逐格量 ──
for who, ns, _ in CAST:
    mesh_eval(True, ns["ARM"].name)
rows = []; prev = {}
n = int(round((T1 - T0) * FPS)) + 1
t_start = time.time()
for i in range(n):
    t = T0 + i / FPS
    S["frame"](t); bpy.context.view_layer.update()
    cl = sc.camera.matrix_world.translation
    r = dict(t=round(t, 3))
    for who, ns, _ in CAST:
        cur = ns["sole_world"](ns["ARM"])
        sl = ns["slide_between"](prev[who], cur) if who in prev else {"L": None, "R": None}
        prev[who] = cur
        for who_ in (who,):
            mesh_eval(True, ns["ARM"].name)
        c = CHK[who].frame(); mesh_eval(True, ns["ARM"].name)
        vmax, vfoot = CHK[who].motion() if hasattr(CHK[who], "motion") else (None, None)
        r[who] = dict(slide_L_mm=None if sl["L"] is None else round(sl["L"] * 1000, 2), slide_R_mm=None if sl["R"] is None else round(sl["R"] * 1000, 2),
                      foot_min_cm=round(c["foot_min"] * 100, 2), pen_core_mm=round(c["pen_core"], 1), pen_hands_mm=round(c["pen_hands"], 1),
                      pen_legs_mm=round(c["pen_legs"], 1), vmax=None if vmax is None else round(vmax, 1), vfoot=None if vfoot is None else round(vfoot, 1),
                      face_blocked=face_hits(ns, ns["WHO"] + "_", cl), **measures(ns))
        if c["pen_core"] > 0.5:                   # 穿模在哪：最深那一點、離哪隻手腕近
            pa = CHK[who].worst_at.get("core")
            if pa:
                pv = Vector(pa[0]); dl, dr_ = ((pv - bw(ns, f"J_Bip_{s_}_Hand")).length for s_ in "LR")
                r[who]["pen_at"] = dict(p=pa[0], side="L" if dl < dr_ else "R", d_wrist_cm=round(min(dl, dr_) * 100, 1))
    rows.append(r)
json.dump(rows, open(os.path.join(OUTW, "metrics.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("WALK_METRICS_DONE", len(rows), "frames", round(time.time() - t_start, 1), "s", flush=True)


def summ(who, a, b):
    sel = [r[who] for r in rows if a <= r["t"] <= b]
    def mx(key, f=max):
        v = [x[key] for x in sel if x.get(key) is not None]
        return round(f(v), 2) if v else None
    sl = [x for x in sel for x in (x["slide_L_mm"], x["slide_R_mm"]) if x is not None]
    fb = [r["t"] for r in rows if a <= r["t"] <= b and r[who]["face_blocked"] and not set(r[who]["face_blocked"]) <= {"G_Petals"}]
    return dict(slide_step_max_mm=round(max(sl), 2) if sl else None, slide_total_mm=round(sum(sl), 1),
                foot_min_cm=mx("foot_min_cm", min), pen_core_mm=mx("pen_core_mm"), pen_hands_mm=mx("pen_hands_mm"), pen_legs_mm=mx("pen_legs_mm"),
                vmax=mx("vmax"), vfoot=mx("vfoot"), pelvis_tilt=(mx("pelvis_tilt", min), mx("pelvis_tilt")),
                knee_L=(mx("knee_L", min), mx("knee_L")), knee_R=(mx("knee_R", min), mx("knee_R")),
                head_fwd_cm=(mx("head_fwd_cm", min), mx("head_fwd_cm")), wrist=(max(mx("wrist_L") or 0, mx("wrist_R") or 0)),
                face_blocked_t=(fb[0], fb[-1], len(fb)) if fb else None)


we = T02["walk_end"]
SUMS = {}
for who, ns, _ in CAST:
    F = ST["WG"] if who == "groom" else ST["WB"]
    t_start = we - F.dur
    tj = t_start + F.join["t_join"] if getattr(F, "join", None) else we - 0.5
    ts = t_start + getattr(F, "settle", F.dur)
    print("WALK_TIMES", who, json.dumps(dict(start=round(t_start, 3), join=round(tj, 3), settle=round(ts, 3), end=we, dur=round(F.dur, 3),
                                             join_info=getattr(F, "join", None)), ensure_ascii=False), flush=True)
    W = dict(walk=(max(T0, t_start), tj), stop=(tj, we), stop_all=(tj, 4.0 + 1e-3), hold=(we, 4.0 + 1e-3), blend_turn=(4.0, 4.45), after=(4.45, T1),
             settle_turn=(we, T1))
    SUMS[who] = {k: summ(who, a, b_) for k, (a, b_) in W.items()}
    for k, v in SUMS[who].items():
        print("WALK_SUM", who, k, W[k], json.dumps(v, ensure_ascii=False), flush=True)
json.dump(SUMS, open(os.path.join(OUTW, "summary.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)

# ── 2. 快速預覽 ──
if int(globals().get("PREVIEW", 1)):
    fd = os.path.join(OUTW, "frames"); os.makedirs(fd, exist_ok=True)
    for who, ns, _ in CAST:
        mesh_eval(False, ns["ARM"].name)
    for i in range(n):
        t = T0 + i / FPS
        S["frame"](t)
        render_still(os.path.join(fd, f"{i + 1:04d}.jpg"), (960, 540), 8)
    mp4 = os.path.join(PROD, "videos", "preview-v2", f"s02_walk_quick_{TAG}.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", os.path.join(fd, "%04d.jpg"), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "22", mp4], check=True)
    print("WALK_PREVIEW", mp4, flush=True)

if int(globals().get("SHEET", 1)):
    # ── 3. 多角度檢查圖 ──
    HIDE = ("G_Hedge", "G_Arch", "G_ArchFlowers", "G_FlowerBed", "G_Trees", "G_Petals")
    for nm in HIDE:
        o = bpy.data.objects.get(nm)
        if o: o.hide_render = True
    VIEWS = [("正面", 0.0), ("側面（左）", 90.0), ("背面", 180.0), ("3/4", 45.0)]
    for who, ns, coll in CAST:
        other = [c for w, _, c in CAST if w != who][0]
        show(other, False)
        W, H = 480, 360; tiles = []
        for ci, t in enumerate(KEYS_SHEET):
            S["frame"](t, cam=False); bpy.context.view_layer.update()
            f = forward(ns); left = Vector((-f.y, f.x, 0)); c = bw(ns, "J_Bip_C_Hips"); c.z = 0.85
            for ri, (lab, a) in enumerate(VIEWS):
                r_ = math.radians(a); d = f * math.cos(r_) + left * math.sin(r_)
                look(c + d * 3.6 + Vector((0, 0, 0.15)), c, 50.0)
                sc.camera.data.dof.use_dof = False
                p = os.path.join(OUTW, f"_v_{who}_{ci}_{ri}.jpg"); render_still(p, (W, H), 8)
                tiles.append((ci, ri, p))
        show(other, True)
        outp = os.path.join(PROD, "pictures", "preview-v2", f"v2_02_walk_check_{who}_{TAG}.jpg")
        lay = dict(W=W, H=H, keys=KEYS_SHEET, views=[v[0] for v in VIEWS], tiles=tiles, out=outp, title=f"{who} {TAG}")
        lp = os.path.join(OUTW, f"_layout_{who}.json"); json.dump(lay, open(lp, "w", encoding="utf8"), ensure_ascii=False)
        # Blender 的 Python 沒有 PIL：用系統 Python 拼圖
        code = ("import json,sys;from PIL import Image,ImageDraw,ImageFont;L=json.load(open(sys.argv[1],encoding='utf8'));W,H=L['W'],L['H'];"
                "S=Image.new('RGB',(W*len(L['keys'])+110,H*len(L['views'])+34),'white');d=ImageDraw.Draw(S);f=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',22);"
                "[S.paste(Image.open(p),(110+c*W,34+r*H)) for c,r,p in L['tiles']];"
                "[d.text((110+i*W+8,4),f'{k:.2f}s',font=f,fill='black') for i,k in enumerate(L['keys'])];"
                "[d.text((6,34+i*H+H//2),v,font=f,fill='black') for i,v in enumerate(L['views'])];d.text((6,4),L['title'],font=f,fill='black');S.save(L['out'],quality=88)")
        subprocess.run(["python", "-c", code, lp], check=True)
        print("WALK_SHEET", outp, flush=True)
    for nm in HIDE:
        o = bpy.data.objects.get(nm)
        if o: o.hide_render = False
print("WALK_CHECK_DONE", flush=True)
