# 從 catalog.json＋page.json 產生素材庫展示頁 index.html（系統 Python，不用 Blender）
#   python make_page.py            → 本資料夾 index.html（圖片用相對路徑 previews/…，本機直接開就看得到）
#   python make_page.py --files    → 另外印出發布用的 files 對照（JSON），給 Artifact 發布時用
#   python make_page.py --inline   → 圖片改成 base64 內嵌（單一檔案約 5 MB；Claude app 看得到圖），發布時不用帶 files
# 分段規則：每個分類一段（順序照 catalog.json 的 catalogs）；該分類的場景示意（group＝分類）當大圖，下面是單品
# 外部素材的單品卡會顯示來源與授權；頁尾列出所有要標註作者的素材（同 ATTRIBUTION.md）
import json, os, sys, html

HERE = os.path.dirname(os.path.abspath(__file__))
cat = json.load(open(os.path.join(HERE, "catalog.json"), encoding="utf8"))
page = json.load(open(os.path.join(HERE, "page.json"), encoding="utf8"))
items = [i for i in cat["items"] if i["catalog"] != "scenes"]
scenes = [i for i in cat["items"] if i["catalog"] == "scenes"]
esc = html.escape

groups = []
for ck, cn in cat["catalogs"].items():
    if ck == "scenes":
        continue
    its = [i for i in items if i["catalog"] == ck]
    scs = [s for s in scenes if s.get("group") == ck]
    if its or scs:
        groups.append(dict(key=ck, title=cn, sub=page.get("group_subs", {}).get(ck, ""), scenes=scs, items=its))


def fmt(v):
    return "%.2f m" % v if v >= 1 else "%d cm" % round(v * 100)


def card(i):
    w, d, h = i["size"]
    src = i.get("source")
    lic = ""
    if src:
        lic = '<span class="chip src">%s・%s</span>' % (esc(src.get("license", "?")), esc(src.get("site", "")))
    return ('<article class="card" tabindex="0" data-src="%s" data-cap="%s"><img src="%s" alt="%s" loading="lazy">'
            '<div><b>%s</b><span class="meta"><span class="chip">%s</span>%s<span>寬 %s・深 %s・高 %s</span></span></div></article>'
            % (i["img"], esc(i["label"]), i["img"], esc(i["label"]), esc(i["label"]), esc(i["scenes"] or "—"), lic, fmt(w), fmt(d), fmt(h)))


sections = []
for g in groups:
    def hero(s):
        h = ('<figure class="hero" tabindex="0" data-src="%s" data-cap="%s"><img src="%s" alt="%s" loading="lazy"><figcaption>%s</figcaption></figure>'
             % (s["img"], esc(s["label"]), s["img"], esc(s["label"]), esc(s["label"])))
        views = [v for v in g["scenes"] if v.get("view_of") == s["key"]]       # 同一個場景的各鏡頭視角，排成小圖格
        if views:
            h += '<div class="grid views">%s</div>' % "".join(
                '<figure class="card" tabindex="0" data-src="%s" data-cap="%s"><img src="%s" alt="%s" loading="lazy"><div><span class="meta">%s</span></div></figure>'
                % (v["img"], esc(v["label"]), v["img"], esc(v["label"]), esc(v["label"])) for v in views)
        return h
    heroes = "".join(hero(s) for s in g["scenes"] if not s.get("view_of"))
    sections.append('<section id="%s"><h2>%s<small>%s</small></h2>%s<div class="grid">%s</div></section>'
                    % (g["key"], esc(g["title"]), esc(g["sub"]), heroes, "".join(card(i) for i in g["items"])))

credits = [i for i in items if i.get("source") and i["source"].get("license", "").upper().startswith("CC BY")]
credit_html = ""
if credits:
    credit_html = '<div class="notes"><h2>素材來源與標註</h2><ul>%s</ul></div>' % "".join(
        '<li>%s：<a href="%s">%s</a> by %s（%s）</li>' % (esc(i["label"]), esc(i["source"].get("page", "")), esc(i["source"].get("title", i["source"].get("site", ""))),
                                                     esc(i["source"].get("author", "?")), esc(i["source"]["license"])) for i in credits)
notes = "".join("<li>%s</li>" % n for n in page.get("notes", []))
facts = "".join('<div class="fact"><b>%s</b><span>%s</span></div>' % (esc(a), esc(b)) for a, b in page.get("facts", []))
n_items = len(items); n_scenes = len([s for s in scenes if not s.get("view_of")])

STYLE = open(os.path.join(HERE, "page_style.css"), encoding="utf8").read()
out = """<title>%(title)s</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@500;700&family=Noto+Sans+TC:wght@400;500&display=swap">
<style>
%(style)s
</style>

<div class="wrap">
  <header>
    <h1>%(h1)s</h1>
    <p>%(intro)s</p>
    <p class="count">目前 %(n)d 樣道具、%(s)d 個場景示意（%(built)s 更新）</p>
    <div class="facts">%(facts)s</div>
  </header>
  %(sections)s
  %(credits)s
  %(notes)s
</div>

<dialog id="zoom"><img id="zoomImg" alt=""><p id="zoomCap"></p></dialog>
<script>
const dlg = document.getElementById("zoom");
function openZoom(el) { const im = document.getElementById("zoomImg"); im.src = el.dataset.src || el.querySelector("img").src; im.alt = el.dataset.cap;
  document.getElementById("zoomCap").textContent = el.dataset.cap; dlg.showModal(); }
document.addEventListener("click", e => { const el = e.target.closest("[data-src]"); if (el && !dlg.open) openZoom(el); });
document.addEventListener("keydown", e => { const el = e.target.closest && e.target.closest("[data-src]"); if (el && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); openZoom(el); } });
dlg.addEventListener("click", () => dlg.close());
</script>
""" % dict(title=esc(page["title"]), style=STYLE, h1=esc(page["h1"]), intro=esc(page["intro"]), n=n_items, s=n_scenes, built=cat.get("built", ""),
           facts=facts, sections="\n  ".join(sections), credits=credit_html,
           notes=('<div class="notes"><h2>%s</h2><ul>%s</ul></div>' % (esc(page.get("notes_title", "備註")), notes)) if notes else "")
if "--inline" in sys.argv:                                               # 圖片改成 base64 內嵌（Claude app 看不到外部圖檔時用）；放大沿用同一張，不重複嵌
    import base64, re
    out = re.sub(r'data-src="previews/[^"]+"', 'data-src=""', out)
    out = re.sub(r'src="(previews/[^"]+\.jpg)"', lambda m: 'src="data:image/jpeg;base64,%s"' % base64.b64encode(open(os.path.join(HERE, m.group(1)), "rb").read()).decode(), out)
open(os.path.join(HERE, "index.html"), "w", encoding="utf8").write(out)
print("PAGE", os.path.join(HERE, "index.html"), n_items, "items", n_scenes, "scenes")
if "--files" in sys.argv:
    print(json.dumps({i["img"]: i["img"] for i in cat["items"]}, ensure_ascii=False))
