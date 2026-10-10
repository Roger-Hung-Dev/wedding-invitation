# 快修：小改動作或時間軸後，幾分鐘內看到結果（2026-10-09，blender-motion-library references/fast-iteration.md 第 5 節「快修」）
#   "$BL" -b couple.blend -P prod_cli.py -- --run quick_tweak SHOT=v2_02 T0=0.8 T1=4.6 [TAG=try1] [ENGINE=workbench|eevee]
#        [RES=960,540] [RATE=24] [CHECK=1] [VIDEO=1] [HANDLE=0.5]
# 和整段預覽的差別：
#   1. 只算 T0～T1（前後各加 HANDLE 秒），不跑整幕
#   2. 預設用 Workbench（灰模＋貼圖顏色、無光影），每格不到 0.1 秒；ENGINE=eevee 改用 EEVEE 4 取樣
#   3. 不跑頭髮裙擺物理
#   4. 只量骨頭的快速檢查（不算網格，幾秒內）：每個角色的滑步（兩格都踩地的鞋底點）、鞋底高度、
#      身體骨頭最大轉速與速度突變、腳踝腳趾轉速；穿模檢查留到使用者確認、做完整品質前再跑（v2_quick_check／v2_phys_check）
# 輸出：D:\render-work\opening-v12\quick\<幕>\<TAG>\（影格、quick.mp4、check.json），結尾印一行 QUICK_DONE {json}
# 不改 set_v2.py／shots_v2.py：只呼叫 SHOTS[幕] 的 build／frame
import bpy, os, json, time, math, subprocess

MODE = "setup"
use("run_prod")

T_START = time.time()
SID = str(globals().get("SHOT", "v2_02"))
TAG = str(globals().get("TAG", "quick"))
S = SHOTS[SID]
HANDLE = float(globals().get("HANDLE", 0.5))
T0 = max(0.0, float(globals().get("T0", 0.0)) - HANDLE)
T1 = min(float(S["dur"]), float(globals().get("T1", S["dur"])) + HANDLE)
RES = tuple(int(x) for x in str(globals().get("RES", "960,540")).split(","))
ENGINE = str(globals().get("ENGINE", "workbench")).lower()
DO_CHECK = int(globals().get("CHECK", 1)); DO_VIDEO = int(globals().get("VIDEO", 1))
OUT = os.path.join(r"D:\render-work\opening-v12\quick", SID, TAG); os.makedirs(OUT, exist_ok=True)

S["build"](); stage(S["set"], cast=True)
actors = S.get("actors", [])
ST0 = S.get("t0", 0.0)
skip = list(S.get("qa_skip", ()))
t_build = round(time.time() - T_START, 1)

# ── 渲染設定 ──
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = RES; sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 88
if ENGINE == "workbench":
    try:
        sc.render.engine = "BLENDER_WORKBENCH"
    except TypeError as e:
        print("ENGINE_FALLBACK", e, flush=True)
    sh = sc.display.shading
    sh.light = "STUDIO"; sh.color_type = "TEXTURE"; sh.show_shadows = False; sh.show_cavity = False
    sc.display.render_aa = "FXAA"
else:
    sc.eevee.taa_render_samples = int(globals().get("SAMPLES", 4))
# 擺姿勢加速：關掉所有網格修改器的「視窗評估」（衣服的 Solidify／幾何節點、骨架變形）。
# 實測（2026-10-09，v2_02）：每次 view_layer.update 從 111 ms 降到 13 ms，每格擺姿勢從 5.5 秒降到 0.35 秒。
# 渲染走 show_render，畫面不受影響；擺姿勢只讀骨頭矩陣，不讀網格。
for o in bpy.data.objects:
    if o.type == "MESH":
        for m in o.modifiers:
            m.show_viewport = False
if ENGINE == "workbench":             # Workbench 的貼圖模式：沒有貼圖的材質（場景）用 diffuse_color，從節點的底色抄過去
    for mat in bpy.data.materials:
        if mat.use_nodes and mat.node_tree:
            bs = next((nd for nd in mat.node_tree.nodes if nd.type == "BSDF_PRINCIPLED"), None)
            if bs is not None and not bs.inputs["Base Color"].is_linked:
                mat.diffuse_color = tuple(bs.inputs["Base Color"].default_value)

# ── 檢查工具（骨頭層級，不算網格） ──
CHK = {}
if DO_CHECK:
    for a in actors:
        ns = a.ns
        if "Checker" not in ns:
            ns["use"]("check_lib")
        CHK[ns["WHO"]] = dict(ns=ns, ck=ns["Checker"](ns["ARM"], ns["WHO"]), prev=None,
                              vel=[], fvel=[], slide_mx=0.0, slide_at=None, tot={"L": 0.0, "R": 0.0},
                              zmin=9.0, zmin_at=None, zmax_planted=0.0, vmax_at=None)


def soles(ns):
    A = ns["ARM"]; mw = A.matrix_world; out = {"L": [], "R": []}
    for b, co in ns["sole_points"](A, ns["WHO"]):
        out["L" if "_L_" in b else "R"].append(mw @ A.pose.bones[b].matrix @ co)
    return out


def check_frame(t):
    for who, c in CHK.items():
        ns = c["ns"]
        vb, vf = c["ck"].motion()
        if c["prev"] is not None and not any(a_ <= t <= b_ for a_, b_ in skip):    # qa_skip 時段（例：原地轉身）轉速也不算
            c["vel"].append((vb, t)); c["fvel"].append(vf)
        cur = soles(ns)
        low = min(p.z for side in "LR" for p in cur[side])
        if low < c["zmin"]:
            c["zmin"], c["zmin_at"] = low, round(t, 2)
        if c["prev"] is not None and not any(a_ <= t <= b_ for a_, b_ in skip):
            for side in "LR":
                idx = [i for i, (p, q) in enumerate(zip(c["prev"][side], cur[side])) if p.z <= 0.005 and q.z <= 0.005]
                if len(idx) >= 3:
                    dx = sum(cur[side][i].x - c["prev"][side][i].x for i in idx) / len(idx)
                    dy = sum(cur[side][i].y - c["prev"][side][i].y for i in idx) / len(idx)
                    d = math.hypot(dx, dy); c["tot"][side] += d
                    if d > c["slide_mx"]:
                        c["slide_mx"], c["slide_at"] = d, round(t, 2)
        c["prev"] = cur


# ── 主迴圈 ──
n0, n1 = int(round(T0 * FPS)), int(round(T1 * FPS))
t_r = time.time()
for k, i in enumerate(range(n0, n1 + 1)):
    t = i / FPS
    S["frame"](ST0 + t)
    bpy.context.view_layer.update()
    if DO_CHECK:
        check_frame(t)
    if DO_VIDEO:
        sc.render.filepath = os.path.join(OUT, f"{k + 1:04d}.jpg")
        bpy.ops.render.render(write_still=True)
t_render = round(time.time() - t_r, 1)
nfr = n1 - n0 + 1

res = dict(shot=SID, tag=TAG, t0=round(T0, 2), t1=round(T1, 2), frames=nfr, fps=FPS, engine=ENGINE, res=list(RES),
           build_s=t_build, loop_s=t_render, per_frame_s=round(t_render / max(1, nfr), 3))
if DO_CHECK:
    ns0 = next(iter(CHK.values()))["ns"]
    VB, VF, JK = ns0.get("VMAX_BODY", 15.0), ns0.get("VMAX_FOOT", 35.0), ns0.get("JERK_BODY", 6.0)
    rows = {}
    for who, c in CHK.items():
        vs = [v for v, _ in c["vel"]]
        jerk = max([abs(vs[j] - vs[j - 1]) for j in range(1, len(vs))] or [0.0])
        vmax, vat = max(c["vel"]) if c["vel"] else (0.0, None)
        rows[who] = dict(slide_step_mm=round(c["slide_mx"] * 1000, 2), slide_at_s=c["slide_at"],
                         slide_total_mm=round(max(c["tot"].values()) * 1000, 1),
                         sole_min_cm=round(c["zmin"] * 100, 2), sole_min_at_s=c["zmin_at"],
                         body_vmax=round(vmax, 1), body_vmax_at_s=round(vat, 2) if vat is not None else None,
                         jerk=round(jerk, 1), foot_vmax=round(max(c["fvel"] or [0.0]), 1))
        r = rows[who]
        r["flags"] = [s for s, bad in [(f"滑步 {r['slide_step_mm']} mm（{r['slide_at_s']}s）", r["slide_step_mm"] > 1.1),
                                       (f"陷地 {r['sole_min_cm']} cm（{r['sole_min_at_s']}s）", r["sole_min_cm"] < -0.5),
                                       (f"身體轉速 {r['body_vmax']}°/格（{r['body_vmax_at_s']}s）", r["body_vmax"] > VB),
                                       (f"速度突變 {r['jerk']}", r["jerk"] > JK),
                                       (f"腳踝腳趾 {r['foot_vmax']}°/格", r["foot_vmax"] > VF)] if bad]
    res["check"] = rows
    res["skip"] = skip
    json.dump(res, open(os.path.join(OUT, "check.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if DO_VIDEO:
    mp4 = os.path.join(OUT, "quick.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", os.path.join(OUT, "%04d.jpg"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-preset", "veryfast", mp4], check=False)
    res["video"] = mp4
res["total_s"] = round(time.time() - T_START, 1)
print("QUICK_DONE", json.dumps(res, ensure_ascii=False), flush=True)
