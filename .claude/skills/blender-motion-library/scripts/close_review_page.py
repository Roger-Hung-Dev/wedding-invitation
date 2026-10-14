# 動作近照確認頁（/fix-animation 用）：一個時刻一列、每列幾個角度並排，圖片內嵌成 data URI，發布成 Claude Artifact。
# 2026-10-11 由 ⑦a 握叉近照頁（https://claude.ai/artifact/UmtR9YTfUbHEX7WKRdn5eP）整理成通用版：
#   使用者指定「某一幕的哪個動作」→ 只拍那個部位的近照（mx_preview 的 CLOSE=角色:骨頭:距離），附上改了什麼、客觀檢查的數字，
#   使用者在對話裡說「可以」或指出哪個時刻哪裡不對，確認後才渲整幕。
#
# 用法：python close_review_page.py <spec.json>
# spec.json：
#   {"title": "⑦a 新娘握叉近照",                      // 頁面名稱（短名詞片語）
#    "intro": ["這頁只看…", "…"],                       // 開頭說明，一段一個字串
#    "changes": [{"version": 2, "text": "照你「…」改：…"}],   // 每一版改了什麼（新的放後面）
#    "checks": ["穿模檢查：…0 點", "最近處離叉子 0.4 mm"],   // 客觀檢查的數字（小標籤）
#    "ask": "請在對話裡回我：…",
#    "src": "D:/render-work/mixamo/preview/s07a/m4/close_bride_J_Bip_R_Hand",   // CLOSE 出圖的資料夾（檔名 <秒>_<角度>.jpg）
#    "rows": [["00.30", "放著（叉尖靠在盤緣）"], …],     // 時刻（檔名前綴）＋這一刻在做什麼
#    "views": [["main", "影片鏡頭方向（放大）"], ["front", "正面"], ["side", "側面"]],   // 可省略（預設這三個）
#    "videos": [["D:/…/clip.mp4", "整段低畫質（樣張渲的）"]],   // 選填（2026-10-12 動畫工作流加）：放在開頭的短片，內嵌成 data URI，一支建議 2 MB 以內
#    "out": "C:/…/scratchpad/<頁名>/index.html"}
import base64, io, json, os, sys
from PIL import Image

spec = json.load(open(sys.argv[1], encoding="utf8"))
VIEWS = spec.get("views") or [["main", "影片鏡頭方向（放大）"], ["front", "正面"], ["side", "側面"]]
esc = lambda s: str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def uri(path, size=420):
    im = Image.open(path).convert("RGB").resize((size, size), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "JPEG", quality=82)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


rows = []
for t, label in spec["rows"]:
    figs = []
    for v, vl in VIEWS:
        p = os.path.join(spec["src"], "%s_%s.jpg" % (t, v))
        if os.path.exists(p):
            figs.append('<figure><img src="%s" alt="%s 秒 %s"><figcaption>%s</figcaption></figure>' % (uri(p), esc(t), esc(vl), esc(vl)))
    rows.append('<section class="moment"><h2><span class="t">%.1f 秒</span>%s</h2><div class="views" style="--n:%d">%s</div></section>'
                % (float(t), esc(label), max(1, len(figs)), "".join(figs)))

intro = "".join("<p>%s</p>" % esc(x) for x in spec.get("intro", []))
changes = "".join('<p><b>第 %s 版</b>：%s</p>' % (esc(c["version"]), esc(c["text"])) for c in spec.get("changes", []))
checks = "".join("<li>%s</li>" % esc(x) for x in spec.get("checks", []))
videos = "".join('<figure class="clip"><video src="data:video/mp4;base64,%s" controls loop muted playsinline preload="metadata"></video><figcaption>%s</figcaption></figure>'
                 % (base64.b64encode(open(v, "rb").read()).decode(), esc(c)) for v, c in spec.get("videos", []) if os.path.exists(v))
TPL = """<title>%TITLE%</title>
<style>
/* 版面：一個時刻一列、幾個角度並排；手機上疊成一欄 */
:root { --bg: #FAF6F4; --fg: #2E2426; --muted: #7A6A6D; --line: #E6DADC; --accent: #B4536A; --chip: #F1E3E6;
  --f-body: "Noto Sans TC", "PingFang TC", "Microsoft JhengHei", system-ui, sans-serif; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg: #1E1A1B; --fg: #EFE6E8; --muted: #A9999C; --line: #3A3033; --accent: #E58BA0; --chip: #3A2A2F; color-scheme: dark } }
:root[data-theme="dark"] { --bg: #1E1A1B; --fg: #EFE6E8; --muted: #A9999C; --line: #3A3033; --accent: #E58BA0; --chip: #3A2A2F; color-scheme: dark }
body { background: var(--bg); color: var(--fg); font-family: var(--f-body); font-size: 15px; line-height: 1.7; }
.wrap { max-width: 1040px; margin: 0 auto; padding-inline: 16px; padding-block: 28px 48px; display: grid; gap: 28px; }
header { display: grid; gap: 10px; max-width: 68ch; }
h1 { font-size: 1.6rem; line-height: 1.3; margin: 0; text-wrap: balance; }
header p { margin: 0; }
.checks { display: flex; flex-wrap: wrap; gap: 8px; margin: 4px 0 0; padding: 0; list-style: none; }
.checks li { background: var(--chip); border-radius: 999px; padding: 2px 12px; font-size: 0.85rem; font-variant-numeric: tabular-nums; }
.ask { border-left: 3px solid var(--accent); padding: 4px 0 4px 14px; }
.moment { display: grid; gap: 10px; border-top: 1px solid var(--line); padding-top: 16px; }
.moment h2 { font-size: 1.05rem; margin: 0; display: flex; gap: 12px; align-items: baseline; }
.t { color: var(--accent); font-variant-numeric: tabular-nums; min-width: 4.5em; }
.views { display: grid; grid-template-columns: repeat(var(--n), minmax(0, 1fr)); gap: 10px; }
figure { margin: 0; display: grid; gap: 4px; }
figure img { width: 100%; height: auto; border-radius: 6px; display: block; }
figcaption { color: var(--muted); font-size: 0.82rem; }
.clip video { width: 100%; height: auto; border-radius: 8px; display: block; background: #000; }
@media (max-width: 640px) { .views { grid-template-columns: 1fr; } }
</style>
<div class="wrap">
<header>
  <h1>%TITLE%</h1>
  %INTRO%
  %CHANGES%
  <ul class="checks">%CHECKS%</ul>
  <p class="ask">%ASK%</p>
</header>
%VIDEOS%
%ROWS%
</div>"""
html = (TPL.replace("%TITLE%", esc(spec["title"])).replace("%INTRO%", intro).replace("%CHANGES%", changes)
        .replace("%CHECKS%", checks).replace("%ASK%", esc(spec.get("ask", "請在對話裡回我：可以就說「可以」；不對的話說是哪個時刻、哪個角度、哪裡不像。")))
        .replace("%VIDEOS%", videos).replace("%ROWS%","\n".join(rows)))
os.makedirs(os.path.dirname(spec["out"]), exist_ok=True)
open(spec["out"], "w", encoding="utf8").write(html)
print("CLOSEPAGE", spec["out"], len(html), "rows", len(rows))
