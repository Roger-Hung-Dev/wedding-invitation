# ZEPETO 可動臉一鍵產線（AI 網格路線）：AI 生成的頭本身當成品，模板只當「籠子」算出 52 個表情、轉移到 AI 網格。系統 Python 執行。
#   2026-10-14 取代舊路線（模板當成品；封存在 D:/render-work/archive/zepeto-face-rig-old-route-20261014）。
#   說明與坑見 references/ai-mesh-route.md；籠子程式（cage/）的細節見 references/cage-pipeline.md。
#
#   post       （face.json 有 obj 才跑）OBJ → 後處理成 .blend（zepeto-character-face-generation-workflow 的 postprocess.py）
#   eyes       眼睛自動偵測：正面貼圖原色圖 → 找眼珠、量眼睛開口（eyes_auto.py＋eyes_find.py）；face.json 有 eyes_manual 就用手動值
#   landmarks  五官（cage/detect_landmarks.py，眼睛用上一步的值）；唇縫高度改用細線偵測（eyes_find.find_seam）
#   cage       籠子：模板包到 AI 頭上（V 臉）＋ 52 表情（cage/ 的 align／wrap／materials／arkit52）
#   transfer   表情轉移到 AI 網格＋切嘴縫＋自建口腔袋（transfer.py）
#   shade      材質眼睛、眨眼、看方向、黑髮、亮澤（eyes_shader.py＋gloss.py）
#   check      自動檢查（check.py 數字）＋總表、五官近照、張嘴序列與切片 → check/report.html
#   rig        舊版 head_rig.blend 封存 → 整理成交接格式（pack_head.py：Head／Hair／Ears／ZEPETO_Lips）
#              → 標準脖子接口環（neck_ring.py：48 點、後頸缺皮就補；身體端照抄座標接上，合約見 references/research-head-body-seam.md 5.4）→ 控制骨架（face_rig.py）
#              → head_rig.blend；骨架檢查（rig_check.py：每根控制骨頭拉到底，量形態鍵／材質數值＋總表）
#   hairfit    長髮避開身體（hair_fit.py：厚頭髮壓縮到背後、細髮絲往前），改寫 head_rig.blend。
#              face.json 的 body：auto（預設）＝用身體端的 body_build.py 照這顆頭試接一副身體來調；也可給身體檔路徑；none＝不跑
#   finish     貼圖打包進 head_rig.blend（身體檔、封存的舊版都不再讀外部圖檔）→ 用成品再試接一次身體、拉遠拍側面
#              → 預覽圖 preview/（mat_front_ai／new、mat_34_ai／new、sheet_combos、sheet_keys 52 表情、rig、body_side）＋ check/summary.json
#
# 用法：python run_face_rig.py --work <這張臉的資料夾> [--ai-blend <AI 頭 .blend>] [--body auto|none|<body.blend>] [--steps eyes,landmarks,...]
#   一條龍：--work <OUT>/rig（AI 頭預設讀 <OUT>/stylized_face_zepeto.blend）
#   face.json：第一次跑自動寫一份（欄位見 FACE_DEFAULTS），之後手動修正都改它（路徑可寫相對於 --work）；命令列給的值只用在這一次
import argparse, os, re, subprocess, sys, json, shutil, time, glob

HERE = os.path.dirname(os.path.abspath(__file__))                   # zepeto-face-rig/scripts
CAGE = os.path.join(HERE, "cage")
TOOLS = os.path.join(HERE, "tools")
SKILLS = os.path.normpath(os.path.join(HERE, "..", ".."))
TEMPLATE = os.path.normpath(os.path.join(SKILLS, "..", "docs", "data", "blender", "zepeto", "templates", "cartoon-head-lucadrech"))
GEN = os.path.join(SKILLS, "zepeto-character-face-generation-workflow", "scripts")
BODY_BUILD = os.path.join(SKILLS, "zepeto-body-generation-workflow", "scripts", "body_build.py")  # 身體端的身體產生器（只拿來試接，不改它）
ALL = ["post", "eyes", "landmarks", "cage", "transfer", "shade", "check", "rig", "hairfit", "finish"]
FACE_DEFAULTS = {
    "name": None,                                   # 影格、試接身體放 D:/render-work/blender-work/zepeto-rig/<name>/；不填＝從資料夾名猜
    "ai_blend": "../stylized_face_zepeto.blend",    # 後處理後的 AI 頭（一條龍：<OUT>/rig 的上一層）
    "obj": None,                                    # 有給才跑 post：Rodin 匯出的 OBJ
    "eyes_manual": None,                            # [左眼x, 右眼x, 高度, 半寬, 半高]；自動偵測不準時填
    "mouth_zc": None,                               # 唇縫中央高度；自動偵測（唇縫細線）不準時填
    "hair_rgb": [0.075, 0.068, 0.072],              # 「像頭髮又偏藍灰」的貼圖點換成這個顏色（sRGB）：Rodin 常把黑髮生成藍灰；照片不是黑髮時填照片髮色
    "iris_rgb": [0.26, 0.15, 0.10],                 # 程式眼珠的虹膜顏色（sRGB）
    "gloss": {"rough": 0.5, "sss": 0.15},           # 亮澤：皮膚粗糙度、次表面散射（2026-10-13 使用者選亮澤、不用 Coat）
    "mouth_cut": 0.8,                               # 嘴縫切到嘴寬的幾成
    "lip_smooth": 40, "lip_rz": 0.18,               # 嘴唇一帶多抹順幾次、範圍（唇線上下）
    "brow_gain": 1.6,                               # 眉毛動作放大（粗黑眉太誇張時降，攝影師 1.2）
    "corner_smooth": 6,                             # 嘴角周圍抹平幾次（新娘 AI 頭嘴角有小凹痕要抹；攝影師 0）
    "tongue_len": 0.75,                             # 吐舌頭伸出長度（1＝模板原樣）
    "body": "auto",                                 # 長髮避開身體用的身體：auto／none／身體檔路徑
}

ap = argparse.ArgumentParser()
ap.add_argument("--work", required=True)
ap.add_argument("--ai-blend", default=None, help="這次用這顆 AI 頭（不寫進 face.json）")
ap.add_argument("--body", default=None, help="auto／none／身體檔路徑（不寫進 face.json）")
ap.add_argument("--steps", default=",".join(ALL))
ap.add_argument("--blender", default=r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")
opt = ap.parse_args()
work = os.path.abspath(opt.work)
os.makedirs(work, exist_ok=True)
cfg_path = os.path.join(work, "face.json")
_guess = os.path.basename(os.path.dirname(work)) if os.path.basename(work).lower() == "rig" else os.path.basename(work)
if not os.path.exists(cfg_path):  # 第一次跑：寫一份設定檔，之後手動修正改這裡
    init = {"name": _guess, "ai_blend": FACE_DEFAULTS["ai_blend"], "body": FACE_DEFAULTS["body"]}
    if opt.ai_blend:
        init["ai_blend"] = os.path.relpath(os.path.abspath(opt.ai_blend), work).replace("\\", "/")
    json.dump(init, open(cfg_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("寫了設定檔：", cfg_path)
cfg = dict(FACE_DEFAULTS, **json.load(open(cfg_path, encoding="utf-8")))
if opt.ai_blend:
    cfg["ai_blend"] = os.path.abspath(opt.ai_blend)
if opt.body:
    cfg["body"] = opt.body
NAME = cfg.get("name") or _guess
W = lambda *p: os.path.join(work, *p)
def R(p):  # face.json 裡的路徑：相對於 --work
    return p if p is None or os.path.isabs(p) else os.path.normpath(os.path.join(work, p))
AI = R(cfg["ai_blend"])
LMJ = W("landmarks.json")
CG = W("cage")
RW = os.path.join(os.environ.get("BLENDER_WORK_ROOT", r"D:\render-work\blender-work"), "zepeto-rig", NAME)  # 影格、試接身體（不進專案）
for d in (CG, W("check"), RW):
    os.makedirs(d, exist_ok=True)
ENV = dict(os.environ, ZEPETO_RIG_WORK=CG, ZEPETO_RIG_TEMPLATE=TEMPLATE)


def blender(args, env=None, tag=""):
    t0 = time.time()
    r = subprocess.run([opt.blender, "-b"] + args, env=env or ENV, capture_output=True, text=True, encoding="utf-8", errors="replace")
    log = r.stdout + r.stderr
    for l in log.splitlines():
        if l.startswith("[") and not l.startswith("[Warning"):
            print("   ", l)
    if r.returncode != 0 or "Traceback" in log or re.search(r"^\s*\w*(Error|Exception):", log, re.M):  # 語法錯誤不會印 Traceback
        print(log[-3000:])
        sys.exit(f"失敗：{tag or args}")
    print("    （%s %.0f 秒）" % (tag, time.time() - t0))
    return log


def sheet(src, out, cols, labels=None, cell=300):
    from PIL import Image, ImageDraw, ImageFont
    fs = sorted(glob.glob(os.path.join(src, "*.png")))
    names = labels or open(os.path.join(src, "frames.txt"), encoding="utf-8").read().split("\n")
    f = ImageFont.truetype(r"C:\Windows\Fonts\msjh.ttc", 16)
    im = Image.new("RGB", (cols * cell, ((len(fs) + cols - 1) // cols) * (cell + 22)), (30, 30, 30)); d = ImageDraw.Draw(im)
    for i, p in enumerate(fs):
        x, y = (i % cols) * cell, (i // cols) * (cell + 22)
        im.paste(Image.open(p).convert("RGB").resize((cell, cell)), (x, y))
        d.text((x + 4, y + cell + 2), names[i] if i < len(names) else "", fill=(230, 230, 230), font=f)
    im.save(out)


def report_section(title, html):
    """report.html 換掉（或補上）某一節：每一節以 <h2 id="..."> 開頭，重跑時只換那一節"""
    rp = W("check", "report.html")
    if not os.path.exists(rp):
        return
    h = open(rp, encoding="utf-8").read()
    h = re.sub(r'<h2 id="%s">.*?(?=<h2 id="|\Z)' % title, "", h, flags=re.S)
    open(rp, "w", encoding="utf-8").write(h + '<h2 id="%s">' % title + html)


def step_post():
    if not cfg.get("obj"):
        print("    （face.json 沒有 obj，跳過）"); return
    blender(["--factory-startup", "--python", os.path.join(GEN, "postprocess.py"), "--", "--obj", R(cfg["obj"]), "--blend", AI], tag="postprocess")
    blender([AI, "--python", os.path.join(GEN, "verify.py"), "--", W("qa")], tag="verify")


def step_eyes():
    if not os.path.exists(AI):
        sys.exit("找不到 AI 頭：%s（face.json 的 ai_blend，或 --ai-blend）" % AI)
    if cfg.get("eyes_manual"):
        ev = dict(eyes=cfg["eyes_manual"], source="manual")
    else:
        blender([AI, "-P", os.path.join(HERE, "eyes_auto.py"), "--", W("check", "eyes_front.png"), W("check", "eyes_front.json")], tag="eyes_auto")
        sys.path.insert(0, HERE)
        import eyes_find
        r = eyes_find.find(W("check", "eyes_front.png"), json.load(open(W("check", "eyes_front.json"))), W("check", "eyes_detect.png"))
        bad = r is None or abs(r["eyes"][0] + r["eyes"][1]) > 0.06 or not (0.04 < r["eyes"][3] < 0.2)
        if bad:
            sys.exit("眼睛自動偵測失敗（%s）：看 check/eyes_detect.png，量好後填 face.json 的 eyes_manual" % r)
        ev = dict(r, source="auto")
    json.dump(ev, open(W("eyes.json"), "w"), indent=1)
    print("    眼睛（%s）：%s" % (ev["source"], ev["eyes"]))


def step_landmarks():
    ev = json.load(open(W("eyes.json")))
    env = dict(ENV, ZEPETO_EYES=",".join(str(v) for v in ev["eyes"]))
    blender([AI, "--python", os.path.join(CAGE, "detect_landmarks.py"), "--", LMJ], env=env, tag="landmarks")
    # 嘴巴中心高度改用唇縫細線（偵測到的「紅色帶中間」在閉嘴微笑時偏高；見 eyes_find.find_seam）
    sys.path.insert(0, HERE)
    import eyes_find
    L = json.load(open(LMJ, encoding="utf-8"))
    png, meta = W("check", "eyes_front.png"), W("check", "eyes_front.json")
    if not os.path.exists(png):
        blender([AI, "-P", os.path.join(HERE, "eyes_auto.py"), "--", png, meta], tag="eyes_auto")
    zc, line, conf = eyes_find.find_seam(png, json.load(open(meta)), L["mouth"]["L"], L["mouth"]["R"])
    if cfg.get("mouth_zc") is not None:
        zc = cfg["mouth_zc"]; print("    唇縫高度：用 face.json 的 mouth_zc %.3f" % zc)
    elif conf < 0.01:
        print("    唇縫細線太淡（%.3f），沿用偵測值 %.3f" % (conf, L["mouth"]["center"][2])); zc = L["mouth"]["center"][2]
    else:
        print("    唇縫高度 %.3f（原偵測 %.3f、嘴角 %.3f、細線深度 %.3f）" % (zc, L["mouth"]["center"][2], (L["mouth"]["L"][2] + L["mouth"]["R"][2]) / 2, conf))
    L["mouth"]["center"][2] = zc
    L["mouth"]["seam"] = line
    json.dump(L, open(LMJ, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def step_cage():
    env = dict(ENV, ZEPETO_CONTOUR="1", CAGE_ONLY="1")
    shutil.copy(LMJ, os.path.join(CG, "landmarks.json"))  # materials.py 從工作資料夾讀五官
    blender([os.path.join(TEMPLATE, "template_clean.blend"), "--python", os.path.join(CAGE, "align.py"), "--", AI, LMJ], env=env, tag="align")
    blender([os.path.join(CG, "aligned.blend"), "--python", os.path.join(CAGE, "wrap.py"), "--", LMJ], env=env, tag="wrap")
    blender([os.path.join(CG, "wrapped.blend"), "--python", os.path.join(CAGE, "materials.py"), "--", os.path.join(CG, "preview")], env=env, tag="materials")
    blender([os.path.join(CG, "head_v1.blend"), "--python", os.path.join(CAGE, "arkit52.py"), "--", LMJ], env=env, tag="arkit")


def step_transfer():
    env = dict(ENV, AI_BLEND=AI, AI_LM=LMJ, MOUTH_CUT=str(cfg["mouth_cut"]), LIP_SMOOTH=str(cfg["lip_smooth"]),
               LIP_RZ=str(cfg["lip_rz"]), BROW_GAIN=str(cfg["brow_gain"]), TONGUE_LEN=str(cfg["tongue_len"]),
               CORNER_SMOOTH=str(cfg["corner_smooth"]))
    blender([os.path.join(CG, "head_arkit.blend"), "-P", os.path.join(HERE, "transfer.py"), "--", W("xfer.blend"), "3"], env=env, tag="transfer")


def step_shade():
    env = dict(ENV, IRIS_RGB=",".join(str(v) for v in cfg["iris_rgb"]))
    args = [W("xfer.blend"), "-P", os.path.join(HERE, "eyes_shader.py"), "--", LMJ, W("face.blend")]
    if cfg.get("hair_rgb"):
        args.append(",".join(str(v) for v in cfg["hair_rgb"]))
    blender(args, env=env, tag="eyes_shader")
    env = dict(ENV, GLOSS_ROUGH=str(cfg["gloss"]["rough"]), GLOSS_SSS=str(cfg["gloss"]["sss"]), GLOSS_SAVE=W("face.blend"))
    blender([W("face.blend"), "-P", os.path.join(HERE, "gloss.py")], env=env, tag="gloss")
    shutil.copy(W("diffuse_blackhair.png"), W("diffuse_blackhair_shade.png"))  # 原版留一份：hairfit 會改這張圖（見 step_rig）


def step_check():
    C = W("check")
    blender([W("face.blend"), "-P", os.path.join(HERE, "check.py"), "--", LMJ, os.path.join(C, "metrics.json")], tag="check")
    for sub in ("sheet", "mouth", "eyes", "series_c", "series_s"):
        shutil.rmtree(os.path.join(C, sub), ignore_errors=True)
    blender([W("face.blend"), "-P", os.path.join(HERE, "render_set.py"), "--", os.path.join(C, "sheet"), "", "front"], tag="render_set")
    env = dict(ENV, CU_BG="0.05,0.15,0.6")
    blender([W("face.blend"), "-P", os.path.join(HERE, "closeup.py"), "--", os.path.join(C, "mouth"), LMJ,
             "basis,jawOpen,surprise,laugh,smile,tongue,pucker,angry,sad", "mouth,m34,m34R"], env=env, tag="closeup mouth")
    blender([W("face.blend"), "-P", os.path.join(HERE, "closeup.py"), "--", os.path.join(C, "eyes"), LMJ,
             "basis,blink,wink,smile,surprise,lookSide,lookUp,angry,sad", "eyeL,eyeR,brow"], env=env, tag="closeup eyes")
    blender([W("face.blend"), "-P", os.path.join(HERE, "open_series.py"), "--", os.path.join(C, "series_c"), LMJ], tag="series")
    blender([W("face.blend"), "-P", os.path.join(HERE, "slice_colors.py"), "-P", os.path.join(HERE, "open_series.py"), "--", os.path.join(C, "series_s"), LMJ],
            env=dict(ENV, CLIP_END="2.04"), tag="slice")
    sheet(os.path.join(C, "sheet"), os.path.join(C, "sheet.png"), 7,
          labels=[l.split()[-1] for l in open(os.path.join(C, "sheet", "frames.txt")).read().split("\n")])
    sheet(os.path.join(C, "mouth"), os.path.join(C, "mouth.png"), 6)
    sheet(os.path.join(C, "eyes"), os.path.join(C, "eyes.png"), 6)
    from PIL import Image
    S = Image.new("RGB", (4 * 420, 2 * 420), (30, 30, 30))
    for i in range(4):
        S.paste(Image.open(os.path.join(C, "series_c", "p_%d.png" % i)).convert("RGB"), (i * 420, 0))
        S.paste(Image.open(os.path.join(C, "series_s", "s_%d.png" % i)).convert("RGB"), (i * 420, 420))
    S.save(os.path.join(C, "series.png"))
    M = json.load(open(os.path.join(C, "metrics.json"), encoding="utf-8"))
    rows = "".join("<tr><td>%s</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td></tr>" % (
        k, v["teeth_front"], v["pocket_out"], v["poke"], v["holes"], v["backface"]) for k, v in M["expressions"].items())
    ok = M["total_issues"] == 0
    html = f"""<!doctype html><meta charset="utf-8"><title>{NAME} 檢查</title>
<style>body{{font-family:'Microsoft JhengHei',sans-serif;background:#1e1e1e;color:#eee;margin:24px}}img{{max-width:100%;margin:8px 0}}
table{{border-collapse:collapse}}td,th{{border:1px solid #555;padding:4px 10px;text-align:center}}.ok{{color:#7d7}}.ng{{color:#f77}}</style>
<h1>{NAME}：可動臉自動檢查</h1>
<p class="{'ok' if ok else 'ng'}">合計問題 {M['total_issues']}（{'通過' if ok else '要看'}）；打開檔案時非 0 的形態鍵 {M.get('rest_nonzero', '-')} 個；嘴唇綁到模板內面 {M.get('lip_back_bind', '-')} 點；眼睛 {json.load(open(W('eyes.json')))}</p>
<table><tr><th>表情</th><th>牙齒舌頭在唇前</th><th>口腔袋穿出（點）</th><th>口腔袋穿出（畫面）</th><th>破洞</th><th>看到皮背面</th></tr>{rows}</table>
<h2>表情總表</h2><img src="sheet.png"><h2>嘴巴（正面、兩側斜面）</h2><img src="mouth.png">
<h2>眼睛、眉毛</h2><img src="eyes.png"><h2>張嘴 0／0.3／0.6／1.0（上：正面，下：正中切片）</h2><img src="series.png">
<h2>眼睛偵測</h2><img src="eyes_detect.png">"""
    open(os.path.join(C, "report.html"), "w", encoding="utf-8").write(html)
    print("    報告：", os.path.join(C, "report.html"), "（合計問題 %d）" % M["total_issues"])


def archive_old():
    """每個人只留一個現役 head_rig.blend（身體端的頭清單只認這個檔名）：舊版連同它的 preview/ 改名封存"""
    cur = W("head_rig.blend")
    if not os.path.exists(cur):
        return
    t = time.localtime(os.path.getmtime(cur))
    sfx = time.strftime("%Y%m%d", t)
    if os.path.exists(W(f"head_rig_{sfx}.blend")):
        sfx += time.strftime("_%H%M", t)
    os.replace(cur, W(f"head_rig_{sfx}.blend"))
    if os.path.isdir(W("preview")) and not os.path.exists(W(f"preview_{sfx}")):
        os.replace(W("preview"), W(f"preview_{sfx}"))
    print("    舊版封存：head_rig_%s.blend（預覽圖 preview_%s/）" % (sfx, sfx))


def step_rig():
    C = W("check")
    archive_old()
    # 貼圖還原成 shade 產的原版：hairfit 會把耳垂以下改成膚色、存回同一張圖；pack_head 照貼圖顏色分頭髮，
    #   讀到改過的圖，後頸分出來的範圍就變了（新娘重跑：脖子那層 64 點變 67 點，接口環跟著不同）
    if os.path.exists(W("diffuse_blackhair_shade.png")):
        shutil.copy(W("diffuse_blackhair_shade.png"), W("diffuse_blackhair.png"))
    else:
        print("    ⚠️ 沒有 diffuse_blackhair_shade.png（舊資料夾）：貼圖可能被上次 hairfit 改過，要結果穩定請從 shade 重跑")
    # 先整理成交接格式（Head／Hair／Ears／ZEPETO_Lips，見 pack_head.py），再接骨架（驅動器要建在切開後的每個物件上）
    blender([W("face.blend"), "-P", os.path.join(HERE, "pack_head.py"), "--", LMJ, W("pack.blend")], tag="pack_head")
    blender([W("pack.blend"), "-P", os.path.join(HERE, "neck_ring.py"), "--", LMJ, W("ring.blend"), os.path.join(C, "ring.json")], tag="neck_ring")
    blender([W("ring.blend"), "-P", os.path.join(HERE, "face_rig.py"), "--", W("head_rig.blend"), LMJ], tag="face_rig")
    shutil.rmtree(os.path.join(C, "rig"), ignore_errors=True)
    blender([W("head_rig.blend"), "-P", os.path.join(HERE, "rig_check.py"), "--", LMJ, os.path.join(C, "rig")], tag="rig_check")
    sheet(os.path.join(C, "rig"), os.path.join(C, "rig.png"), 5)
    M = json.load(open(os.path.join(C, "rig", "rig_metrics.json"), encoding="utf-8"))
    rows = "".join("<tr><td>%s</td><td class='%s'>%s</td><td>%s</td></tr>" % (k, "ok" if v["ok"] else "ng", "OK" if v["ok"] else "NG",
                   "、".join("%s=%s" % (a, b) for a, b in v["got"].items())) for k, v in M["poses"].items())
    report_section("rig", "控制骨架（每根拉到底）</h2><p class='%s'>%s</p><table><tr><th>姿勢</th><th></th><th>實際值</th></tr>%s</table><img src='rig.png'>" % (
        "ok" if M["ok"] else "ng", "全部通過" if M["ok"] else "有問題", rows))
    print("    骨架檢查：%s → %s" % ("全部通過" if M["ok"] else "有問題", W("head_rig.blend")))


def build_body(head, tag):
    """用身體端的 body_build.py 照這顆頭試接一副身體（不出廠、不留紀錄，放 render-work）"""
    d = os.path.join(RW, "body_try", tag)
    shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    shutil.copy(head, os.path.join(d, "head_rig.blend"))
    blender([os.path.join(d, "head_rig.blend"), "-P", BODY_BUILD, "--", "OUT=" + os.path.join(d, "out"), "QA=none"], tag="試接身體 " + tag)
    return os.path.join(d, "out", "body.blend")


def body_mode():
    b = cfg.get("body")
    return None if not b or str(b).lower() == "none" else "auto" if str(b).lower() == "auto" else R(b)


def step_hairfit():
    C = W("check")
    b = body_mode()
    if b is None:
        print("    （face.json 的 body 是 none，跳過）"); return
    if b == "auto":
        b = build_body(W("head_rig.blend"), "prefit")
    log = blender([W("head_rig.blend"), "--python", os.path.join(HERE, "hair_fit.py"), "--", b, LMJ], tag="hair_fit")
    m = re.findall(r"修正後：插進身體 (\d+) 點", log)
    json.dump(dict(body=b, inside_after=int(m[-1]) if m else None), open(os.path.join(C, "hairfit.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    blender([W("head_rig.blend"), "-P", os.path.join(TOOLS, "dbg_hair_split.py"), "--", os.path.join(C, "final_split")], tag="final_split")
    shutil.rmtree(os.path.join(C, "final"), ignore_errors=True)  # 最終成品（含長髮）的骨架總表
    blender([W("head_rig.blend"), "-P", os.path.join(HERE, "rig_check.py"), "--", LMJ, os.path.join(C, "final")], tag="final rig_check")
    sheet(os.path.join(C, "final"), os.path.join(C, "final.png"), 5)


def step_finish():
    C, PV = W("check"), W("preview")
    os.makedirs(PV, exist_ok=True)
    for f in glob.glob(os.path.join(PV, "*.png")):
        os.remove(f)  # sheet_keys.png 最後才產（頭清單用它判斷「做完了」）
    # 1. 貼圖打包：head_rig.blend 讀的是外部 diffuse_blackhair.png，重跑 shade 會覆寫它 → 已出廠的身體、封存的舊版跟著變（新娘 v4 出過事）
    blender([W("head_rig.blend"), "--python-expr",
             "import bpy;bpy.ops.file.pack_all();miss=[i.name for i in bpy.data.images if i.source=='FILE' and not i.packed_file];"
             "print('[finish] 打包貼圖',[i.name for i in bpy.data.images if i.packed_file],'沒打包',miss);bpy.ops.wm.save_mainfile()"], tag="pack")
    # 2. 用成品試接一次身體（順便驗證身體端讀得了這顆頭），拉遠拍側面：長髮一定要看這組，近照只看得到肩膀折角
    side = None
    if body_mode() is not None:
        bb = build_body(W("head_rig.blend"), "final")
        blender([bb, "-P", os.path.join(TOOLS, "shot_body_side.py"), "--", os.path.join(RW, "body_side")], tag="body_side")
        from PIL import Image
        ims = [Image.open(os.path.join(RW, "body_side_%d.png" % i)).convert("RGB") for i in range(3)]
        side = Image.new("RGB", (sum(i.width for i in ims), ims[0].height))
        x = 0
        for im in ims:
            side.paste(im, (x, 0)); x += im.width
        side.save(os.path.join(C, "body_side.png")); side.save(os.path.join(PV, "body_side.png"))
    # 3. 預覽圖
    blender([W("head_rig.blend"), "-P", os.path.join(HERE, "previews.py"), "--", "mat", PV, AI], tag="previews mat")
    kd = os.path.join(RW, "keys")
    shutil.rmtree(kd, ignore_errors=True)
    blender([W("head_rig.blend"), "-P", os.path.join(HERE, "previews.py"), "--", "keys", kd], tag="previews keys")
    for src, dst in (("sheet.png", "sheet_combos.png"), ("final.png" if os.path.exists(os.path.join(C, "final.png")) else "rig.png", "rig.png")):
        if os.path.exists(os.path.join(C, src)):
            shutil.copy(os.path.join(C, src), os.path.join(PV, dst))
    # 3b. 耳朵、後頸近照：髮際線鋸齒、深色毛邊、細黑線、後頸缺皮（2026-10-14 使用者、身體端在這兩區各抓到問題，總表縮圖看不出來）
    from PIL import Image

    def strip(paths, out, cell=400):
        ims = [Image.open(p).convert("RGB").resize((cell, cell)) for p in paths if os.path.exists(p)]
        if not ims:
            return None
        S_ = Image.new("RGB", (cell * len(ims), cell))
        for i, im in enumerate(ims):
            S_.paste(im, (i * cell, 0))
        S_.save(out); return out
    rows_ = []
    for sd in ("R", "L"):
        blender([W("head_rig.blend"), "-P", os.path.join(TOOLS, "ear_closeup.py"), "--", os.path.join(RW, "ear_" + sd), sd], tag="ear " + sd)
        rows_.append(strip([os.path.join(RW, "ear_%s_%d.png" % (sd, i)) for i in range(3)], os.path.join(RW, "ear_%s.png" % sd)))
    ear_png = None
    if all(rows_):
        E_ = Image.new("RGB", (1200, 800))
        for r_, p in enumerate(rows_):
            E_.paste(Image.open(p), (0, r_ * 400))
        ear_png = os.path.join(C, "ear.png"); E_.save(ear_png)
    nape_png = None
    if side is not None:
        blender([bb, "-P", os.path.join(TOOLS, "nape_closeup.py"), "--", os.path.join(RW, "nape"), "0.3", "R"], tag="nape")
        nape_png = strip([os.path.join(RW, "nape_%d.png" % i) for i in range(3)], os.path.join(C, "nape.png"))
    # 4. 摘要（可動臉端子代理讀這個回報）
    M = json.load(open(os.path.join(C, "metrics.json"), encoding="utf-8")) if os.path.exists(os.path.join(C, "metrics.json")) else {}
    RM = os.path.join(C, "final" if os.path.exists(os.path.join(C, "final", "rig_metrics.json")) else "rig", "rig_metrics.json")
    rig_ok = json.load(open(RM, encoding="utf-8"))["ok"] if os.path.exists(RM) else None
    hf = json.load(open(os.path.join(C, "hairfit.json"), encoding="utf-8")) if os.path.exists(os.path.join(C, "hairfit.json")) else {}
    ring = json.load(open(os.path.join(C, "ring.json"), encoding="utf-8")) if os.path.exists(os.path.join(C, "ring.json")) else {}
    summary = dict(name=NAME, head_rig=W("head_rig.blend"), ai_blend=AI, total_issues=M.get("total_issues"), rest_nonzero=M.get("rest_nonzero"), neck_ring=ring,
                   lip_back_bind=M.get("lip_back_bind"), rig_ok=rig_ok, eyes=json.load(open(W("eyes.json"))) if os.path.exists(W("eyes.json")) else None,
                   hairfit=hf, body_side=os.path.join(C, "body_side.png") if side else None, ear=ear_png, nape=nape_png, report=os.path.join(C, "report.html"),
                   previews=sorted(glob.glob(os.path.join(PV, "*.png"))) + [os.path.join(PV, "sheet_keys.png")])
    json.dump(summary, open(os.path.join(C, "summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    report_section("finish", "成品（head_rig.blend）</h2><p>長髮插進身體 %s 點（試接身體：%s）</p>"
                   "<h3>像不像 AI 原頭（左：AI 原頭，右：成品）</h3><img src='../preview/mat_front_ai.png' width=420><img src='../preview/mat_front_new.png' width=420>"
                   "<img src='../preview/mat_34_ai.png' width=420><img src='../preview/mat_34_new.png' width=420>"
                   "<h3>接上身體、拉遠看側面</h3><img src='body_side.png'>"
                   "<h3>耳朵附近（上：右耳、下：左耳；斜前、正側、斜下往上）：髮際線有沒有一排深色三角</h3><img src='ear.png'>"
                   "<h3>接上身體，耳朵下方到後頸（側面、斜後、正後）：深色鋸齒、細黑線、後頸缺皮</h3><img src='nape.png'>"
                   "<h3>只看頭：頭髮灰、細髮絲紅</h3>%s"
                   "<h3>52 個 ARKit 單一表情</h3><img src='../preview/sheet_keys.png'>" % (
                       hf.get("inside_after", "-"), hf.get("body", "沒跑"),
                       "".join("<img src='final_split_%d.png' width=420>" % i for i in range(3) if os.path.exists(os.path.join(C, "final_split_%d.png" % i)))))
    sheet(kd, os.path.join(PV, "sheet_keys.png"), 8)  # 最後一個：頭清單看到它才算做完
    print("    摘要：", os.path.join(C, "summary.json"))


STEPS = dict(post=step_post, eyes=step_eyes, landmarks=step_landmarks, cage=step_cage, transfer=step_transfer, shade=step_shade,
             check=step_check, rig=step_rig, hairfit=step_hairfit, finish=step_finish)
t_all = time.time()
print("設定：", json.dumps({k: cfg[k] for k in ("name", "ai_blend", "body")}, ensure_ascii=False), "→", work)
for s in [x.strip() for x in opt.steps.split(",") if x.strip()]:
    print(f"== {s}")
    STEPS[s]()
print("完成（%.0f 秒）：%s" % (time.time() - t_all, W("head_rig.blend") if os.path.exists(W("head_rig.blend")) else W("face.blend")))
