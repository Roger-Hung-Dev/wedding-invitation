# 剪接樣式庫的產生器（2026-10-12）：
#   1. 檢查 catalog.json 的每個字卡、轉場 id 在 edit_styles.js 都有實作
#   2. 展示頁 showcase/index.html（＋ showcase/vid/*.mp4）→ 用 Artifact 發布（網址記在 README）
#   3. 本機預覽樣板 D:/render-work/zepeto-anim/edit/preview_template.html → render-settings mod 按 p 時填入設定、用瀏覽器打開
#   4. 縮圖 thumbs/<種類>_<id>.png（Chrome 無頭截圖）→ mod 面板顯示
# 用法：python build_showcase.py [--no-thumbs]
import asyncio, json, os, re, shutil, sys
from urllib.parse import quote

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = r"D:/render-work/zepeto-anim/edit"
sys.path.insert(0, HERE)


def load():
    cat = json.load(open(os.path.join(HERE, "catalog.json"), encoding="utf8"))
    js = open(os.path.join(HERE, "edit_styles.js"), encoding="utf8").read()
    tpl = open(os.path.join(HERE, "page_template.html"), encoding="utf8").read()
    return cat, js, tpl


def check(cat, js):
    bad = []
    for kind, block in (("captions", "CAPTIONS"), ("transitions", "TRANSITIONS")):
        body = js[js.index(f"const {block} = {{"):]
        body = body[:body.index("\n  };")]
        have = set(re.findall(r"^\s{4}(\w+)[(:]", body, re.M))
        bad += [f"{kind}/{x['id']}" for x in cat[kind] if x["id"] not in have]
    if bad:
        raise SystemExit("catalog 裡有、edit_styles.js 沒實作：" + "、".join(bad))


def fonts_link(cat):
    fam = "&".join("family=" + quote(f["google"]).replace("%20", "+") + ":wght@400;700" for f in cat["fonts"] if f.get("google"))
    return f'<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{fam}&display=swap">'


def page(cat, js, tpl, program, mode, settings=None, local=False):
    h = tpl.replace("<!--FONTS-->", fonts_link(cat)).replace("/*EDIT_STYLES_JS*/", js)
    h = h.replace("/*CATALOG*/null", json.dumps(cat, ensure_ascii=False)).replace("/*PROGRAM*/null", json.dumps(program, ensure_ascii=False))
    h = h.replace('/*MODE*/"view"', json.dumps(mode))
    if settings is not None:
        h = h.replace("/*SETTINGS*/null", json.dumps(settings, ensure_ascii=False))
    if local:                                              # 本機檔沒有 Artifact 外框，自己補 doctype 和編碼
        h = '<!doctype html>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n' + h
    return h


def local_program(cat):
    return {"shots": [dict(s, src="file:///" + s["src"]) for s in cat["demo"]["shots"]]}


def build(thumbs=True):
    cat, js, tpl = load()
    check(cat, js)
    # 展示頁：影片放 showcase/vid/（不進版控）
    sd = os.path.join(HERE, "showcase"); os.makedirs(os.path.join(sd, "vid"), exist_ok=True)
    prog = {"shots": []}
    for s in cat["demo"]["shots"]:
        fn = os.path.basename(s["src"]); shutil.copy(s["src"], os.path.join(sd, "vid", fn))
        prog["shots"].append(dict(s, src="vid/" + fn))
    open(os.path.join(sd, "index.html"), "w", encoding="utf8").write(page(cat, js, tpl, prog, "view"))
    # 本機預覽樣板（設定留空，mod 填）
    os.makedirs(WORK, exist_ok=True)
    open(os.path.join(WORK, "preview_template.html"), "w", encoding="utf8").write(page(cat, js, tpl, local_program(cat), "preview", local=True))
    out = dict(showcase=os.path.join(sd, "index.html"), preview_template=os.path.join(WORK, "preview_template.html"))
    if thumbs:
        out["thumbs"] = asyncio.run(make_thumbs(cat, js, tpl))
    print("SHOWCASE", json.dumps(out, ensure_ascii=False))


async def make_thumbs(cat, js, tpl):
    """每個字卡樣式、轉場、配色、字型、版面各一張 480×270 縮圖（照預設值，只換那一項）"""
    from cdp_capture import Chrome
    td = os.path.join(HERE, "thumbs"); os.makedirs(td, exist_ok=True)
    prog = local_program(cat); D = cat["defaults"]; sh0 = prog["shots"][0]
    jobs = []
    for x in cat["captions"]:          # 字卡進場到一半的樣子最看得出差別
        jobs.append((f"caption_{x['id']}", dict(D, caption_style=x["id"]), sh0["cue"][0] + 0.35))
    for x in cat["palettes"]:
        jobs.append((f"palette_{x['id']}", dict(D, palette=x["id"]), sh0["cue"][0] + 1.5))
    for x in cat["fonts"]:
        jobs.append((f"font_{x['id']}", dict(D, font=x["id"]), sh0["cue"][0] + 1.5))
    for x in cat["layouts"]:
        jobs.append((f"layout_{x['id']}", dict(D, layout=x["id"]), sh0["cue"][0] + 1.5))
    for x in cat["transitions"]:       # 轉場進行到一半
        jobs.append((f"transition_{x['id']}", dict(D, transition=x["id"], transition_s=1.0), None))
    tmp = os.path.join(WORK, "_thumb.html")
    done = []
    async with Chrome(480, 270) as c:
        for name, s, t in jobs:
            open(tmp, "w", encoding="utf8").write(page(cat, js, tpl, prog, "render", s, local=True))
            await c.goto(tmp)
            if t is None:
                j = await c.eval("window.__player.joints[0]")
                tr = next(x for x in cat["transitions"] if x["id"] == s["transition"])
                t = j if tr["overlap"] else j - 0.15 if s["transition"] in ("flash", "black") else j + 0.05
            await c.eval(f"window.__player.seek({t})", await_promise=True)
            f = os.path.join(td, name + ".png"); await c.shot(f); done.append(name)
    os.remove(tmp)
    return done


if __name__ == "__main__":
    build(thumbs="--no-thumbs" not in sys.argv)
