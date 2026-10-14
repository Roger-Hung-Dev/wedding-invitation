# 服裝審看頁：讀 <服裝資料夾>/outfit.json（文字）＋ 每個身體的 <輸出資料夾>/build.json（數字與圖）→ 一頁 HTML（圖片內嵌），
# 順便把幾張小預覽圖存進 <服裝資料夾>/previews/<身體名稱>/（進版控，素材庫總覽用）。
# 同一套服裝穿在好幾個身體上時，最上面先放「每個人穿起來」並排比較，下面再依身體分節列細節。
# 用法：python -I outfit_page.py <服裝資料夾> <輸出 html> <身體輸出資料夾 1> [<身體輸出資料夾 2> ...]
#       （身體輸出資料夾＝D:/render-work/zepeto-costume/<服裝代號>/<身體名稱>，資料夾名就是身體名稱）
import base64, io, json, os, sys
from PIL import Image

OUTFIT, OUT, DIRS = sys.argv[1], sys.argv[2], sys.argv[3:]
meta = json.load(open(os.path.join(OUTFIT, "outfit.json"), encoding="utf-8"))
esc = lambda s: str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
bname = lambda d: os.path.basename(d.rstrip("/\\"))
BODY_LABEL = meta.get("body_labels", {})          # 例：{"groom": "新郎", "bride": "新娘"}；沒寫就用身體代號
blabel = lambda d: BODY_LABEL.get(bname(d), bname(d))


def uri(path, size=520):
    im = Image.open(path).convert("RGB"); im.thumbnail((size, size), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "JPEG", quality=84)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def group(title, note, items, size=520, cols="220px", base=None, tag="h2"):
    """items＝[(檔名, 說明)] 或 [(檔名, 說明, 資料夾)]；不存在的圖略過"""
    figs = ""
    for it in items:
        f, c = it[0], it[1]; b = it[2] if len(it) > 2 else base
        if os.path.exists(os.path.join(b, f)):
            figs += f'<figure><img src="{uri(os.path.join(b, f), size)}" alt="{esc(c)}" loading="lazy"><figcaption>{esc(c)}</figcaption></figure>'
    if not figs:
        return ""
    return f'<section><{tag}>{esc(title)}</{tag}>{"<p>" + esc(note) + "</p>" if note else ""}<div class="views" style="--min:{cols}">{figs}</div></section>'


POSE = [("idle", "站著"), ("walk", "走路"), ("wave_both", "雙手舉高"), ("sit", "坐著"), ("thumbs", "坐著比讚"), ("crouch", "蹲（Mixamo）"), ("kneel_mx", "單膝跪（Mixamo）"), ("kneel", "單膝跪蹲"), ("mouth", "握叉子餵食")]
NAMES = {i["object"]: i["name"] for i in meta.get("items", []) if "object" in i}
A4 = (("0", "正面"), ("45", "右前方"), ("90", "右側面"), ("180", "背面"))


def label(k):
    a, b = k.split("→")
    return f"{NAMES.get(a, a)} → {'頭' if b == 'Head' else '身體' if b == 'Body' else NAMES.get(b, b)}"


def cell(v):
    cls = "ok" if v < 1 else ("mid" if v < 5 else "bad")
    return f'<td class="{cls}">{v:.1f}%</td>'


def clip_table(D):
    cl = json.load(open(os.path.join(D, "build.json"), encoding="utf-8")).get("clips", {})
    keys = sorted({k for v in cl.values() for k in v}, key=lambda k: (k.endswith("Head"), k))
    poses = [(p, n) for p, n in POSE if p in cl]
    if not poses:
        return "<p>這次沒有跑穿模檢查。</p>"
    rows = "".join(f"<tr><th>{esc(label(k))}</th>" + "".join(cell(cl[p][k]) if k in cl[p] else "<td>—</td>" for p, _ in poses) + "</tr>" for k in keys)
    return (f'<div class="tbl"><table><thead><tr><th></th>{"".join(f"<th>{esc(n)}</th>" for _, n in poses)}</tr></thead>'
            f'<tbody>{rows}</tbody></table></div>')


def body_sections(D, multi):
    """一個身體的全部細節；好幾個身體時每節標題前面加上是誰"""
    who = (blabel(D) + "・") if multi else ""
    sec = [
        f'<section><h2>{esc(who)}穿模檢查</h2><p>數字是「衣服有多少比例的點跑進身體或頭裡面」。被衣服蓋住的身體已經藏起來，所以「→ 身體」有數字也看不到；'
        f'要看的是「→ 頭」那幾列，以及走路、舉手、坐下時的圖。</p>{clip_table(D)}</section>',
        group(who + "站姿（手放下）", "Mixamo 待機動作的第一格。", [(f"idle_{a}.png", c) for a, c in A4], base=D),
        group(who + "綁骨架用的 T 字站姿", "衣服是在這個姿勢下做、下綁的。", [(f"rest_{a}.png", c) for a, c in A4], base=D),
        group(who + "領口（近照）", "", [(f"neck_{a}.png", c) for a, c in A4], 640, base=D),
        group(who + "胸前（近照）", "", [("chest_0.png", "正面"), ("chest_30.png", "右前方"), ("chest_-30.png", "左前方")], 640, base=D),
        group(who + "袖口（近照）", "", [("cuff_0.png", "正面"), ("cuff_90.png", "側面"), ("cuff_180.png", "背面")], 640, base=D),
        group(who + "腳（近照）", "", [("feet_0.png", "正面"), ("feet_45.png", "右前方"), ("feet_90.png", "側面")], 640, base=D),
    ]
    for key, title in meta.get("extra_closeups", {}).items():
        files = sorted(f for f in os.listdir(D) if f.startswith(key + "_") and f.endswith(".png"))
        sec.append(group(who + title, "", [(f, f[len(key) + 1:-4] + "°") for f in files], 640, base=D))
    sec += [
        group(who + "動作測試", "Mixamo 動作原樣套上（坐姿沒有椅子，所以看起來懸空）。",
              [("motion_walk_0.png", "走路・正面"), ("motion_walk_90.png", "走路・側面"), ("motion_wave_both_0.png", "雙手舉高・正面"),
               ("motion_wave_both_45.png", "雙手舉高・右前方"), ("motion_sit_45.png", "坐著"), ("motion_thumbs_0.png", "坐著比讚")], base=D),
        group(who + "蹲姿（Mixamo）", "Low Crouching Idle 與 Kneeling Idle 原樣套上，蹲得比手擺的低。看膝蓋、褲襠、屁股。",
              [("motion_crouch_0.png", "蹲・正面"), ("motion_crouch_45.png", "蹲・右前方"), ("motion_crouch_90.png", "蹲・側面"),
               ("motion_kneel_mx_0.png", "單膝跪・正面"), ("motion_kneel_mx_45.png", "單膝跪・右前方"), ("motion_kneel_mx_90.png", "單膝跪・側面")], base=D),
        group(who + "單膝跪蹲", "動作庫沒有蹲的 Mixamo 片段，用待機姿勢改腿擺的：右膝著地、左腳踩地、上身前傾。看膝蓋、褲襠、屁股。",
              [("motion_kneel_0.png", "正面"), ("motion_kneel_45.png", "右前方"), ("motion_kneel_90.png", "側面"), ("motion_kneel_180.png", "背面")], 640, base=D),
        group(who + "握叉子餵食", "手臂彎得最緊的姿勢，看手肘和肩膀的布會不會破。",
              [("motion_mouth_0.png", "正面"), ("motion_mouth_45.png", "右前方"), ("motion_mouth_90.png", "側面")], 640, base=D),
    ]
    return "".join(sec)


# ── 小預覽圖進服裝資料夾（版控用，寬 360）
for D in DIRS:
    pv = os.path.join(OUTFIT, "previews", bname(D)); os.makedirs(pv, exist_ok=True)
    for f in ("idle_0.png", "idle_45.png", "idle_180.png", "chest_30.png", "feet_45.png"):
        if os.path.exists(os.path.join(D, f)):
            im = Image.open(os.path.join(D, f)).convert("RGB"); im.thumbnail((360, 360), Image.LANCZOS)
            im.save(os.path.join(pv, f.replace(".png", ".jpg")), "JPEG", quality=82)

multi = len(DIRS) > 1
refs = [(r["file"], r.get("caption", ""), OUTFIT) for r in meta.get("refs", [])]
sec = [group("對照：參考照", "", refs, 520, "160px") if refs else ""]
if multi:
    sec.append(group("每個人穿起來", "同一套衣服照每個人的身形各做一份，所以每個人都是合身的。",
                     [(f"idle_{a}.png", f"{blabel(D)}・{c}", D) for a, c in (("0", "正面"), ("45", "右前方")) for D in DIRS], 520, "180px"))
for D in DIRS:
    if multi:
        sec.append(f'<section class="who"><h2>{esc(blabel(D))}</h2></section>')
    sec.append(body_sections(D, multi))
body_tags = "".join(f'<span class="tag">身體：{esc(blabel(D))}</span> ' for D in DIRS)

items_html = "".join(f"<li><b>{esc(i['name'])}</b>：{esc(i.get('desc', ''))}</li>" for i in meta.get("items", []))
issues_html = "".join(f"<li>{esc(x)}</li>" for x in meta.get("issues", []))
asks_html = "".join(f"<p>{n}. {esc(x)}</p>" for n, x in enumerate(meta.get("asks", []), 1))
status = {"draft": "製作中", "approved": "已定案", "approved_pending_body": "使用者已同意・等新身體再定案"}.get(meta.get("status"), meta.get("status", ""))

html = f"""<title>{esc(meta['title'])}</title>
<style>
/* 版面：單欄，每一節是一組多角度圖；開頭先列內容、數字與已知問題 */
:root {{
  --bg: #f4f4f6; --fg: #22242b; --muted: #656a76; --line: #d8dae1; --card: #ffffff; --accent: #3d4a6b;
  --ok: #2f7a4a; --mid: #a86a12; --bad: #b5524f;
  --display: "Noto Serif TC", "Songti TC", serif; --body: "Noto Sans TC", "PingFang TC", "Microsoft JhengHei", sans-serif;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #1a1b20; --fg: #e8e9ee; --muted: #a2a6b2; --line: #363944; --card: #24262d; --accent: #9fb0d8;
  --ok: #6cc28d; --mid: #e0a64e; --bad: #e08a86; color-scheme: dark }} }}
:root[data-theme="dark"] {{ --bg: #1a1b20; --fg: #e8e9ee; --muted: #a2a6b2; --line: #363944; --card: #24262d; --accent: #9fb0d8;
  --ok: #6cc28d; --mid: #e0a64e; --bad: #e08a86; color-scheme: dark }}
body {{ background: var(--bg); color: var(--fg); font-family: var(--body); font-size: 16px; line-height: 1.7; }}
main {{ max-width: 1180px; margin: 0 auto; padding-inline: 16px; padding-block: 28px 64px; display: grid; gap: 36px; }}
h1 {{ font-family: var(--display); font-size: 2rem; margin: 0; text-wrap: balance; }}
h2 {{ font-family: var(--display); font-size: 1.35rem; margin: 0 0 6px; text-wrap: balance; }}
p, li {{ max-width: 70ch; }}
.lead {{ color: var(--muted); }}
.tag {{ display: inline-block; font-size: .8rem; padding: 2px 10px; border-radius: 999px; border: 1px solid var(--line); color: var(--muted); }}
section {{ display: grid; gap: 10px; min-width: 0; }}
.views {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(var(--min, 220px), 1fr)); gap: 10px; }}
figure {{ margin: 0; min-width: 0; }}
figure img {{ width: 100%; height: auto; border-radius: 6px; display: block; background: var(--card); }}
figcaption {{ font-size: .85rem; color: var(--muted); margin-top: 4px; }}
.tbl {{ overflow-x: auto; }}
table {{ border-collapse: collapse; font-variant-numeric: tabular-nums; min-width: 560px; }}
th, td {{ padding: 6px 12px; border-bottom: 1px solid var(--line); text-align: right; white-space: nowrap; }}
th:first-child {{ text-align: left; }}
thead th {{ color: var(--muted); font-weight: 500; font-size: .9rem; }}
td.ok {{ color: var(--ok); }} td.mid {{ color: var(--mid); font-weight: 600; }} td.bad {{ color: var(--bad); font-weight: 700; }}
.issues li {{ margin-bottom: 6px; }}
.who h2 {{ font-size: 1.7rem; border-top: 2px solid var(--line); padding-top: 18px; }}
.ask {{ background: var(--card); border: 1px solid var(--line); border-left: 4px solid var(--accent); border-radius: 8px; padding: 16px 18px; }}
</style>
<main>
<header>
  <h1>{esc(meta['title'])}</h1>
  <p><span class="tag">{esc(status)}</span> {body_tags}</p>
  <p class="lead">{esc(meta.get('lead', ''))}</p>
</header>
<section><h2>這套有什麼</h2><ul>{items_html}</ul></section>
{'<section><h2>已知問題</h2><ul class="issues">' + issues_html + '</ul></section>' if issues_html else ''}
{''.join(sec)}
{'<section class="ask"><h2>請你決定</h2>' + asks_html + '</section>' if asks_html else ''}
</main>
"""
open(OUT, "w", encoding="utf-8").write(html)
print("wrote", OUT, round(len(html) / 1e6, 2), "MB")
