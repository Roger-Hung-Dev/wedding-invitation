# 建立角色專案（系統 Python，不在 Blender 裡跑）。
#
#   python new_project.py --name bride --vroid D:\...\bride.vroid --face face.jpg --front front.jpg --back back.jpg
#                         --desc "使用者的描述原文" [--who bride] [--bust yes|no] [--vrm D:\...\bride.vrm]
#
# 做的事：
#   1. 檢查輸入：臉部模型只收 *.vroid；照片收 jpg/jpeg/png/webp；專案名稱只能是小寫英數與 -。
#   2. 建 .claude/docs/data/blender/projects/<name>/（source/ qa/ pictures/ videos/ scripts/ report/）並把輸入檔複製進 source/。
#   3. 找 .vroid 匯出的 VRM：--vrm 指定 → 同資料夾同檔名的 .vrm → 專案 source/model.vrm。找不到就標記 needs_vrm_export
#      （VRoid MCP 不能匯出 VRM，只能由使用者在 VRoid Studio 按 F8 匯出 VRM 1.0）。
#   4. 寫 project.json，最後印出一行 JSON 摘要（給代理讀）。已存在的專案不覆蓋輸入檔，只補缺的。
import argparse, json, os, re, shutil, sys
sys.stdout.reconfigure(encoding="utf-8")   # 中文輸出不要變亂碼（Windows 主控台預設 cp950）

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
ROOT = os.path.join(REPO, ".claude", "docs", "data", "blender", "projects")
IMG = (".jpg", ".jpeg", ".png", ".webp")

ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True)
ap.add_argument("--vroid", required=True)
ap.add_argument("--face"); ap.add_argument("--front"); ap.add_argument("--back")
ap.add_argument("--desc", default="")
ap.add_argument("--who"); ap.add_argument("--bust", choices=("yes", "no"))
ap.add_argument("--vrm")
a = ap.parse_args()

errors = []
if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,40}", a.name):
    errors.append(f"專案名稱「{a.name}」不合規則：只能用小寫英文、數字、-，2～41 字")
if not a.vroid.lower().endswith(".vroid"):
    errors.append(f"臉部模型只接受 .vroid 檔，收到的是「{os.path.basename(a.vroid)}」")
elif not os.path.isfile(a.vroid):
    errors.append(f"找不到 .vroid 檔：{a.vroid}")
for k in ("face", "front", "back"):
    v = getattr(a, k)
    if v and (not v.lower().endswith(IMG) or not os.path.isfile(v)):
        errors.append(f"{k} 照片不存在或格式不對（只收 {', '.join(IMG)}）：{v}")
if a.vrm and (not a.vrm.lower().endswith(".vrm") or not os.path.isfile(a.vrm)):
    errors.append(f"指定的 VRM 不存在：{a.vrm}")
if errors:
    print(json.dumps({"ok": False, "errors": errors}, ensure_ascii=False)); sys.exit(1)

P = os.path.join(ROOT, a.name)
for d in ("source", "qa", "pictures", "videos", "scripts"):
    os.makedirs(os.path.join(P, d), exist_ok=True)


def put(src, dst_name):
    if not src:
        return None
    ext = os.path.splitext(src)[1].lower()
    dst = os.path.join(P, "source", dst_name + ext)
    if not os.path.exists(dst):
        shutil.copy2(src, dst)
    return os.path.relpath(dst, P).replace("\\", "/")


sources = {"vroid": put(a.vroid, "model"), "face": put(a.face, "face"), "front": put(a.front, "front"), "back": put(a.back, "back")}
vrm_candidates = [a.vrm, os.path.splitext(a.vroid)[0] + ".vrm", os.path.join(P, "source", "model.vrm")]
vrm = next((c for c in vrm_candidates if c and os.path.isfile(c)), None)
if vrm and os.path.abspath(vrm) != os.path.abspath(os.path.join(P, "source", "model.vrm")):
    shutil.copy2(vrm, os.path.join(P, "source", "model.vrm"))
sources["vrm"] = "source/model.vrm" if vrm else None

mf = os.path.join(P, "project.json")
M = json.load(open(mf, encoding="utf8")) if os.path.exists(mf) else {}
who = a.who or M.get("who") or re.sub(r"[^a-z0-9]", "", a.name)[:12] or "chara"
M.update({
    "name": a.name, "who": who,
    "description": a.desc or M.get("description", ""),
    "sources": {**M.get("sources", {}), **{k: v for k, v in sources.items() if v}},
    "body": {**M.get("body", {}), **({"bust": a.bust == "yes"} if a.bust else {})},
    "blend": M.get("blend", {"base": f"{a.name}.blend", "costume": f"{a.name}_costume.blend"}),
    "stages": M.get("stages", {"01": "pending", "02": "pending", "03": "pending"}),
    "costume": M.get("costume", {"spec": "costume.json", "summary": "", "parts": []}),
    "scenes": M.get("scenes", []),
    "report": M.get("report", {"artifact_url": None, "s1_facts": [], "s3_summary": "", "limits": []}),
})
M["vrm_status"] = "found" if vrm else "needs_vrm_export"
json.dump(M, open(mf, "w", encoding="utf8"), ensure_ascii=False, indent=2)
out = {"ok": True, "project": P, "who": who, "vrm_status": M["vrm_status"], "sources": M["sources"]}
if not vrm:
    out["next"] = (f"請使用者用 VRoid Studio 開啟 {a.vroid}，按 F8 匯出 VRM 1.0，存成 "
                   f"{os.path.join(P, 'source', 'model.vrm')}（或和 .vroid 同資料夾同檔名），再重跑一次")
print(json.dumps(out, ensure_ascii=False))
