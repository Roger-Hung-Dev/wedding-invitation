# 可動臉產線的回歸測試（2026-10-14）：改了產線程式後，拿 heads.json 裡幾顆「各代表一種臉型」的 AI 頭全部重跑，
#   跟 baseline.json（上次確認過的結果）比，超出容許範圍就標出來。系統 Python 執行。
#   為什麼要有：偵測規則照一兩張臉調的話，換一種臉型就出錯（攝影師 v2：嘴巴抓成鼻孔）；
#   修了新臉又可能把舊臉弄壞 → 每次改都要拿全部舊臉重驗。
#
# 用法（在這個資料夾或任何地方都可以）：
#   python regress.py --init                 第一次：把 heads.json 的頭從 source 複製到 root/heads/<名稱>/（已存在就跳過）
#   python regress.py                        快速：每顆只跑 eyes＋landmarks（約 20 秒／顆），比五官位置
#   python regress.py --full                 完整：整條（eyes～finish），再比 summary.json 的數字和成品正面圖（約 4～6 分鐘／顆，兩顆一起跑）
#   python regress.py --heads bride,ph2      只跑這幾顆
#   python regress.py [--full] --accept      這次的結果看過、沒問題 → 存成新的基準（寫 baseline.json；--full 時也存正面圖）
#   python regress.py [--full] --reuse       不重跑，拿上一次跑完的結果（root/runs/）重新比、重出報告；加 --accept 就直接存成基準
#   結果：主控台表格＋ root/report.html（完整模式有「基準｜這次」正面圖並排）；有差異時結束代碼 1
import argparse, json, os, shutil, subprocess, sys, time, glob, hashlib
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.normpath(os.path.join(HERE, "..", "run_face_rig.py"))
CFG = json.load(open(os.path.join(HERE, "heads.json"), encoding="utf-8"))
BASE_P = os.path.join(HERE, "baseline.json")
ROOT = CFG["root"]
TOL = 0.01          # 位置容許差（頭檔單位；頭寬約 0.8＝20 cm → 0.01 約 2.5 mm）
TOL_BROW = 0.02     # 眉毛厚度
TOL_RATIO = 0.02    # ZEPETO 比例
TOL_IMG = 3.0       # 正面圖平均像素差（0～255）

ap = argparse.ArgumentParser()
ap.add_argument("--init", action="store_true")
ap.add_argument("--full", action="store_true")
ap.add_argument("--heads", default="")
ap.add_argument("--accept", action="store_true")
ap.add_argument("--jobs", type=int, default=2)
ap.add_argument("--reuse", action="store_true", help="不重跑，用上一次的結果")
opt = ap.parse_args()
names = [h for h in (opt.heads.split(",") if opt.heads else CFG["heads"]) if h]
for h in names:
    if h not in CFG["heads"]:
        sys.exit("heads.json 沒有 %s" % h)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def head_dir(h):
    return os.path.join(ROOT, "heads", h)


if opt.init:
    for h in names:
        d = head_dir(h)
        if os.path.exists(os.path.join(d, "stylized_face_zepeto.blend")):
            print("%-6s 已存在，跳過（要換頭：先刪 %s）" % (h, d)); continue
        src = CFG["heads"][h]["source"]
        os.makedirs(d, exist_ok=True)
        for f in ["stylized_face_zepeto.blend"] + [os.path.basename(p) for p in glob.glob(os.path.join(src, "stylized_face_generated_*.png"))]:
            shutil.copy2(os.path.join(src, f), os.path.join(d, f))
        print("%-6s 複製完成（%s，blend sha %s）" % (h, src, sha(os.path.join(d, "stylized_face_zepeto.blend"))))
    sys.exit(0)

for h in names:
    if not os.path.exists(os.path.join(head_dir(h), "stylized_face_zepeto.blend")):
        sys.exit("%s 還沒複製：先跑 python regress.py --init" % h)


def lm_metrics(L):
    e, b, m = L["eyes"], L["brows"], L["mouth"]
    return {"U": L["U"], "眼 z": (e["L"]["c"][2] + e["R"]["c"][2]) / 2, "左眼 x": e["L"]["c"][0], "右眼 x": e["R"]["c"][0],
            "眼半寬": (e["L"]["ew"] + e["R"]["ew"]) / 2, "左嘴角 x": m["L"][0], "左嘴角 z": m["L"][2], "右嘴角 x": m["R"][0],
            "右嘴角 z": m["R"][2], "唇縫 z": m["center"][2], "下巴": L["chin_z"], "左眉厚": b["L"]["thick"], "右眉厚": b["R"]["thick"]}


def full_metrics(S):
    out = {"合計問題": S.get("total_issues"), "打開時非 0 形態鍵": S.get("rest_nonzero"), "骨架通過": S.get("rig_ok"),
           "接口環點數": (S.get("neck_ring") or {}).get("ring_marked"), "接口環整圈": (S.get("neck_ring") or {}).get("ring_closed"),
           "接口環高度": (S.get("neck_ring") or {}).get("ring_z"), "長髮插進身體": (S.get("hairfit") or {}).get("inside_after")}
    for k, it in ((S.get("zepeto_ratio") or {}).get("items") or {}).items():
        out["比例 " + k] = it.get("value")
    return out


def run_head(h):
    w = os.path.join(ROOT, "runs", h, "rig")
    if opt.reuse:
        return collect(h, w, None, 0)
    shutil.rmtree(os.path.join(ROOT, "runs", h), ignore_errors=True)
    os.makedirs(w)
    face = dict(name="regress-" + h, ai_blend=os.path.join(head_dir(h), "stylized_face_zepeto.blend").replace("\\", "/"), **CFG["heads"][h]["face"])
    json.dump(face, open(os.path.join(w, "face.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    steps = [] if opt.full else ["--steps", "eyes,landmarks"]
    t0 = time.time()
    r = subprocess.run([sys.executable, "-u", RUN, "--work", w] + steps, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    open(os.path.join(ROOT, "runs", h, "run.log"), "w", encoding="utf-8").write(r.stdout + r.stderr)
    fail = None
    if r.returncode != 0:
        fail = next((l.strip() for l in reversed((r.stdout + r.stderr).splitlines()) if l.strip().startswith("[") or "失敗" in l), "失敗（看 run.log）")
    return collect(h, w, fail, round(time.time() - t0))


def collect(h, w, fail, secs):
    if opt.reuse and not os.path.exists(os.path.join(w, "landmarks.json")):
        fail = "上一次沒有結果（先跑一次）"
    if opt.reuse and opt.full and not os.path.exists(os.path.join(w, "check", "summary.json")):
        fail = "上一次不是完整模式（沒有 summary.json）"
    res = dict(head=h, secs=secs, fail=fail, work=w)
    lj = os.path.join(w, "landmarks.json")
    if os.path.exists(lj):
        res["landmarks"] = lm_metrics(json.load(open(lj, encoding="utf-8")))
    sj = os.path.join(w, "check", "summary.json")
    if opt.full and os.path.exists(sj):
        res["full"] = full_metrics(json.load(open(sj, encoding="utf-8")))
        res["front"] = os.path.join(w, "preview", "mat_front_new.png")
    print("  %-6s %s%s" % (h, "用上一次的結果" if opt.reuse else "跑完（%d 秒）" % secs, "：" + fail if fail else ""))
    return res


def img_diff(a, b):
    from PIL import Image, ImageChops
    import numpy as np
    A, B = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
    if A.size != B.size:
        B = B.resize(A.size)
    return float(np.asarray(ImageChops.difference(A, B)).mean())


print("回歸測試（%s）：%s" % ("完整" if opt.full else "快速：eyes＋landmarks", "、".join(names)))
with ThreadPoolExecutor(max_workers=max(1, opt.jobs if opt.full else 4)) as ex:
    results = list(ex.map(run_head, names))

base = json.load(open(BASE_P, encoding="utf-8")) if os.path.exists(BASE_P) else {}
rows, bad = [], 0
for r in results:
    h = r["head"]
    B = base.get(h, {})
    diffs = []
    if r["fail"]:
        diffs.append(("跑不完", r["fail"], "", ""))
    for sec, tolf in (("landmarks", lambda k: TOL_BROW if "眉厚" in k else TOL),
                      ("full", lambda k: TOL_RATIO if k.startswith("比例") else TOL)):
        cur, ref = r.get(sec), B.get(sec)
        if cur is None:
            continue
        if ref is None:
            diffs.append(("沒有基準", sec, "", "")); continue
        for k, v in cur.items():
            rv = ref.get(k)
            if isinstance(v, (int, float)) and not isinstance(v, bool) and isinstance(rv, (int, float)) and not isinstance(rv, bool):
                if abs(v - rv) > tolf(k):
                    diffs.append((k, "%.4f" % v, "%.4f" % rv, "%+.4f" % (v - rv)))
            elif v != rv:
                diffs.append((k, str(v), str(rv), ""))
    if opt.full and r.get("front") and os.path.exists(r["front"]):
        bf = os.path.join(ROOT, "baseline", h + "_front.png")
        r["base_front"] = bf if os.path.exists(bf) else None
        if r["base_front"]:
            d = img_diff(r["front"], bf)
            r["img_diff"] = d
            if d > TOL_IMG:
                diffs.append(("正面圖平均像素差", "%.1f" % d, "≤ %.0f" % TOL_IMG, ""))
    r["diffs"] = diffs
    bad += bool(diffs)
    print("%-6s %s" % (h, "一樣（在容許範圍內）" if not diffs else "有 %d 項不同" % len(diffs)))
    for d in diffs:
        print("        %-16s 這次 %-10s 基準 %-10s %s" % d)

# 報告
html = ["<!doctype html><meta charset='utf-8'><title>可動臉回歸測試</title><style>body{font-family:'Microsoft JhengHei',sans-serif;background:#1e1e1e;color:#eee;margin:24px}"
        "table{border-collapse:collapse;margin:8px 0}td,th{border:1px solid #555;padding:3px 9px}.ok{color:#7d7}.ng{color:#f77}img{width:420px;margin:4px}</style>",
        "<h1>可動臉回歸測試（%s，%s）</h1>" % ("完整" if opt.full else "快速", time.strftime("%Y-%m-%d %H:%M"))]
for r in results:
    h = r["head"]
    html.append("<h2>%s <span class='%s'>%s</span></h2><p>%s</p>" % (h, "ng" if r["diffs"] else "ok", "有差異" if r["diffs"] else "一樣", CFG["heads"][h]["label"]))
    if r["diffs"]:
        html.append("<table><tr><th>項目</th><th>這次</th><th>基準</th><th>差</th></tr>%s</table>" % "".join("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % d for d in r["diffs"]))
    if r.get("front"):
        html.append("<div>%s<img src='%s'> <span>這次（平均像素差 %s）</span></div>" % (
            "<img src='%s'> " % ("file:///" + r["base_front"].replace("\\", "/")) if r.get("base_front") else "（沒有基準圖）",
            "file:///" + r["front"].replace("\\", "/"), "%.1f" % r["img_diff"] if "img_diff" in r else "-"))
    html.append("<p>工作資料夾：%s；紀錄：%s</p>" % (r["work"], os.path.join(ROOT, "runs", h, "run.log")))
open(os.path.join(ROOT, "report.html"), "w", encoding="utf-8").write("\n".join(html))
print("報告：", os.path.join(ROOT, "report.html"))

if opt.accept:
    if any(r["fail"] for r in results):
        sys.exit("有頭跑不完，不能存成基準")
    for r in results:
        e = base.setdefault(r["head"], {})
        e["landmarks"] = r.get("landmarks")
        e["head_sha"] = sha(os.path.join(head_dir(r["head"]), "stylized_face_zepeto.blend"))
        if opt.full:
            e["full"] = r.get("full")
            os.makedirs(os.path.join(ROOT, "baseline"), exist_ok=True)
            if r.get("front"):
                shutil.copy2(r["front"], os.path.join(ROOT, "baseline", r["head"] + "_front.png"))
        e["accepted"] = time.strftime("%Y-%m-%d %H:%M")
    json.dump(base, open(BASE_P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("已存成新的基準：", BASE_P)
sys.exit(1 if bad and not opt.accept else 0)
