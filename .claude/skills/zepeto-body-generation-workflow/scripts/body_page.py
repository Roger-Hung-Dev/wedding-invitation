# 身體審看頁：讀 <工作資料夾>/build.json、checks.json、page.json（選填）與圖 → 一頁 HTML（圖片內嵌 JPEG）。
# 用法：python -I body_page.py <工作資料夾> <輸出 html> [--prev <已出廠的資料夾>]
#   工作資料夾＝build/<人>.work；--prev 給 build/<人> 時，最上面放「出廠版 vs 這版」並排
#   page.json（工作流寫）：{"title","lead","changes":[...],"issues":[...],"asks":[...]}，全部選填
# 2026-10-12 v9 改寫成通用版（舊版是 v1～v7 逐版對照、寫死文字）。
import base64, io, json, os, sys
from PIL import Image

args = sys.argv[1:]
PREV = None
if "--prev" in args:
    i = args.index("--prev"); PREV = args[i + 1]; del args[i:i + 2]
D, OUT = args[0], args[1]
J = lambda f, d=None: json.load(open(os.path.join(D, f), encoding="utf-8")) if os.path.exists(os.path.join(D, f)) else d
info, checks, meta = J("build.json", {}), J("checks.json", {}), J("page.json", {})
name = os.path.basename(D.rstrip("/\\")).replace(".work", "")
esc = lambda s: str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def uri(path, size=520):
    im = Image.open(path).convert("RGB"); im.thumbnail((size, size), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "JPEG", quality=84)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def figs(items, base=D, size=520):
    return "".join(f'<figure><img src="{uri(os.path.join(base, f), size)}" alt="{esc(c)}" loading="lazy"><figcaption>{esc(c)}</figcaption></figure>'
                   for f, c in items if os.path.exists(os.path.join(base, f)))


def group(title, note, items, cols="200px", base=D):
    body = figs(items, base)
    if not body:
        return ""
    return f'<section><h2>{esc(title)}</h2>{"<p>" + note + "</p>" if note else ""}<div class="views" style="--min:{cols}">{body}</div></section>'


A4 = (("0", "正面"), ("45", "右前方"), ("90", "右側面"), ("180", "背面"))
LABEL = {"bend": "手指彎曲不塌", "interpen": "手指不互相穿插", "crease": "關節內側擠壓", "weight_trans": "關節權重過渡",
         "rest_fingers": "靜止手指和 Mixamo 一致", "gestures": "9 個共用手勢", "retarget": "套 Mixamo 後手指方向", "basic": "權重、兩腿分開", "uv": "UV（布紋座標）",
         "v2ref": "手指掃描（參考）", "feet": "腳（參考）", "weights": "權重乾淨", "wrist": "手腕扭轉不塌", "limbs": "四肢活動範圍（參考）", "fingerprint": "手腳指紋（資訊）",
         "neck_ring": "頭身接口環"}
MLABEL = {"length": "腳長", "heel_to_ball": "腳跟到腳掌", "ankle_joint_height": "腳踝關節高", "ball_girth": "腳掌圍", "ball_width": "腳掌寬",
          "ball_height": "腳掌高", "instep_girth": "腳背圍", "instep_width": "腳背寬", "instep_height": "腳背高", "heel_width": "腳跟寬",
          "waist_girth": "鞋楦腰圍", "toe_height": "腳趾高", "toe_girth": "腳趾圍", "arch_height": "足弓高", "ankle_girth": "腳踝圍",
          "min_leg_girth": "最小腿圍", "calf_girth": "小腿最粗圍", "knee_girth": "膝圍", "thigh_girth": "大腿最粗圍", "wrist_girth": "手腕圍",
          "forearm_max_girth": "前臂最粗圍", "upper_arm_girth": "上臂圍", "hand_length": "手長", "hand_breadth": "手寬",
          "ring_girth": "脖子接口圍", "min_girth": "脖子最細圍", "cut_z": "脖子接口高"}


def val(k, v):
    v = {a: b for a, b in v.items() if a != "detail"}
    if k == "bend":
        return f"彎 90° 剩 {v.get('min_90')}、60° 剩 {v.get('min_60')}（標準 ≥0.85、≥0.92）"
    if k == "interpen":                                   # v2 起 value 裡還有 tri_cross／fold 等字典，只取數字
        return "最深 " + str(max([b for a, b in v.items() if a != "unit" and isinstance(b, (int, float))] or [0])) + " mm（≤1）"
    if k == "crease":
        return "最深 " + str(max([b for a, b in v.items() if a != "unit" and isinstance(b, (int, float))] or [0])) + " mm"
    if k == "retarget":
        return f"最多差 {v.get('max_deg')}°（≤2°）"
    if k == "basic":
        return f"沒綁到的點 {v.get('unweighted')}、胯下 {v.get('crotch_z')} m"
    if k == "uv":
        return f"格子大小離散 {v.get('density_spread')}（≤4）、壓扁 {v.get('flat_pct')}%、超出 {v.get('outside')}"
    if k == "weights":
        return (f"跨指 {v.get('G1_cross_finger')}、越節 {v.get('G2_skip_joint')}、每點最多 {v.get('bones_max')} 根、總和不是 1 的 {v.get('G5_sum_off')} 點；"
                f"動一根看鄰居最多 {max((v.get('G7_drag_mm') or {'-': 0}).values())} mm（≤0.3）")
    if k == "wrist":
        t = v.get("twist_min_area", {}); b = v.get("baked_open_door") or {}
        return (f"手掌扭 80° 前臂最細剩 {t.get('80')}（≥0.90）、150° 剩 {t.get('150')}（≥0.78）；只彎時扭轉骨轉 {v.get('twist_bones_when_bending_max_deg')}°（≤2）；"
                f"開門片烘焙後 {b.get('forearm_min_area')}")
    if k == "feet":
        so = v.get("sole", {}); po = v.get("poses", {})
        return (f"腳跟離地 {so.get('heel_min_mm')}、前腳掌 {so.get('ball_min_mm')}、足弓 {so.get('arch_mm')} mm；"
                f"轉腳踝、翹腳趾埋住最多 {max([x.get('buried', 0) for x in po.values()] or [0])} 點")
    if k == "limbs":
        r = v.get("rom", {})
        e90 = (r.get("elbow", {}).get("90") or {}).get("area"); k90 = (r.get("knee", {}).get("90") or {}).get("area")
        return f"手肘彎 90° 截面剩 {e90}、膝 90° 剩 {k90}（一般變形的塌陷，見下方「四肢」）"
    if k == "v2ref":
        return "四指 0～110° 掃描：從幾度開始超標 " + esc(json.dumps(v.get("first_over_deg", {}), ensure_ascii=False))
    if k == "fingerprint":
        return "手 " + str((v.get("hand_L") or {}).get("sha")) + "、腳 " + str((v.get("foot_L") or {}).get("sha"))
    if k == "neck_ring":
        if not v.get("ring"):
            return esc(v.get("note", "頭沒有接口環"))
        gap = max(v.get(x) or 0 for x in ("rest_gap_mm", "turn35_gap_mm", "down25_gap_mm", "up25_gap_mm", "jawopen_gap_mm"))
        return (f"頭和身體接口最大縫 {round(gap, 3)} mm（靜止、轉頭、低頭、抬頭、張嘴；≤0.1）、法線差 {v.get('normal_diff_max_deg')}°（≤1）、"
                f"張嘴時環動 {v.get('jawopen_ring_move_mm')} mm（≤0.1）")
    return esc(json.dumps(v, ensure_ascii=False))[:120]


rows = "".join(f'<tr><td>{esc(LABEL.get(k, k))}</td><td><span class="chip {"ok" if v.get("pass") else "ng"}">{"通過" if v.get("pass") else "沒過"}</span></td><td>{val(k, v.get("value", {}))}</td></tr>'
               for k, v in checks.items())
n_ok = sum(1 for v in checks.values() if v.get("pass"))
hd = info.get("head", {})
title = meta.get("title") or f"{name} 身體"
lead = meta.get("lead") or ""
lst = lambda key: "".join(f"<li>{x}</li>" for x in meta.get(key, []))

sections = []
if PREV and os.path.isdir(PREV):
    items = []
    for a, c in (("0", "正面"), ("90", "側面")):
        for tag, d in (("出廠版", PREV), ("這版", D)):
            f = os.path.join(d, f"idle_{a}.png")
            if os.path.exists(f):
                items.append(f'<figure><img src="{uri(f)}" alt="{tag} {c}"><figcaption>{tag}・{c}</figcaption></figure>')
    if items:
        sections.append(f'<section><h2>出廠版 → 這版</h2><div class="views" style="--min:200px">{"".join(items)}</div></section>')
sections += [
    group("站姿（自然站）", "套 Mixamo 待機動作第一格。", [(f"idle_{a}.png", c) for a, c in A4]),
    group("靜止姿勢（T 字）", "給服裝與動畫的基準姿勢。", [(f"rest_{a}.png", c) for a, c in A4]),
    group("脖子接口", "頭和身體的接縫：看有沒有鋸齒、破口、顏色斷層。", [(f"neck_{a}.png", c) for a, c in A4]),
    group("脖子接口近照（自然站、低頭、抬頭、轉頭）", "neck_probe.py 拍的：專看頭和身體接縫的粗細、顏色、縫線。",
          [(f"neck_probe/neck_{k}.png", c) for k, c in (("front", "正面"), ("front_r", "右前方"), ("side_r", "右側面"), ("back", "背面"), ("below", "從下往上"),
                                                         ("down_front", "低頭・正面"), ("down_side", "低頭・側面"), ("up_front", "抬頭・正面"), ("up_side", "抬頭・側面"), ("turn", "轉頭"), ("jaw_front", "張嘴・正面"), ("jaw_side", "張嘴・側面"))]),
    group("手（T 字）", "手指根部不能有蹼、手心虎口不能有膜。", [("hand_top.png", "手背"), ("hand_under.png", "手心"), ("hand_0.png", "正面"), ("hand_180.png", "背面")]),
    group("9 個共用手勢（左手）", "每個手勢拍手背、手心、拇指側。", [(f"gestures/g_{g}_{v}.png", f"{g}・{vz}") for g in ("peace", "fist", "thumbs_up", "grip", "hold", "fork_grip", "relaxed", "cup", "flat") for v, vz in (("back", "手背"), ("palm", "手心"), ("thumb", "拇指側"))], cols="150px"),
    group("動作", "走路、雙手揮手（舉最高那格）、坐、坐著比讚、握叉子送到嘴邊、比 YA。", [(f"motion_{k}_{a}.png", f"{c}・{ac}") for k, c in (("walk", "走路"), ("wave_both", "雙手揮手"), ("sit", "坐"), ("thumbs", "比讚"), ("mouth", "叉子到嘴邊")) for a, ac in (("0", "正面"), ("45", "右前"), ("90", "側面"))] + [(f"motion_ya_{a}.png", f"比 YA・{a}°") for a in ("0", "30", "-30")], cols="170px"),
    group("腳", "鞋子會包住，只看站得穩、不穿地。", [(f"feet_{a}.png", c) for a, c in (("0", "正面"), ("45", "右前方"), ("90", "側面"))]),
    group("UV（布紋座標）", "暫時換成格子材質拍的：格子全身大小差不多＝之後衣服布紋粗細一致。格子方向會轉，屬已知（有方向的布紋由衣服自己對齊）。", [("uv_0.png", "正面"), ("uv_180.png", "背面")]),
    group("手腕扭轉（左手）", "twist_probe.py：手掌繞前臂扭 0／80／150°（150° 約等於手心翻朝上）。前臂有扭轉輔助骨時，扭轉會平均分散在整段前臂，手腕不會扭成細頸。",
          [(f"twist/twist{d}_{v}.png", f"扭 {d}°・{vz}") for d in (0, 80, 150) for v, vz in (("top", "上方"), ("side", "側面"), ("under", "下方"))], cols="170px"),
    group("腳近照（左腳）", "foot_probe.py：靜止、腳踝往上 30°、往下 50°（踮腳）、腳趾往上 70°（走路蹬地）。",
          [(f"feet/f_{p}_{v}.png", f"{pz}・{vz}") for p, pz in (("rest", "靜止"), ("ankle_up30", "腳踝上 30°"), ("ankle_down50", "腳踝下 50°"), ("toes_up70", "腳趾上 70°"))
           for v, vz in (("out", "外側"), ("front", "前方"), ("in", "內側"))] + [("feet/f_rest_sole.png", "腳底")], cols="170px"),
    group("手肘、膝蓋、胯下、小腿（左側）", "limb_shots.py：手肘、膝蓋彎 90°／130°（一般變形 90° 以上會塌，2026-10-14 使用者選維持現狀）；"
          "兩條大腿各扭 35°、往前抬腿（下腹、胯下不該皺出凹凸）；小腿表面（不該有一條條直紋）。",
          [(f"limbs/{k}.png", c) for k, c in (("elbow90", "手肘 90°"), ("elbow130", "手肘 130°"), ("knee90", "膝 90°"), ("knee130", "膝 130°"),
                                               ("hip_front", "扭腿・正面"), ("hip_back", "扭腿・背面"), ("hip_low", "扭腿・從下往上"), ("legup", "抬腿"),
                                               ("shin_front", "小腿・正面"), ("shin_side", "小腿・側面"), ("shin_back", "小腿・背面"))], cols="170px"),
]


def table(head, rows_):
    return ('<div class="card tw"><table><thead><tr>' + "".join(f"<th>{esc(h)}</th>" for h in head) + "</tr></thead><tbody>"
            + "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows_) + "</tbody></table></div>")


lim = (checks.get("limbs") or {}).get("value") or {}
if lim.get("rom"):
    r = lim["rom"]
    rr = []
    for jn, jz in (("elbow", "手肘"), ("knee", "膝蓋")):
        for d, x in r.get(jn, {}).items():
            if d in ("0", "45", "75", "90", "105", "120", "135", "145", "150"):
                rr.append([jz, d + "°", x.get("area"), x.get("crease_mm"), x.get("fold")])
    oth = []
    for jn, jz in (("shoulder_down", "手臂往下"), ("shoulder_up", "手臂往上"), ("shoulder_fwd", "手臂往前"), ("hip_flex", "大腿往前抬"), ("hip_abduct", "大腿外展"),
                   ("hip_adduct", "大腿內收"), ("ankle", "腳踝"), ("toes", "腳趾")):
        for d, x in r.get(jn, {}).items():
            if d != "0":
                oth.append([jz, d + "°", x.get("crease_mm"), x.get("cross_mm"), x.get("fold")])
    mx = [[k, f"{x.get('clip')} 第 {x.get('frame')} 格（{x.get('side')}）", x.get("bend_deg"), x.get("area"), x.get("crease_mm"), f"{x.get('cross_mm')}（{x.get('cross_pair') or '-'}）"]
          for k, x in (lim.get("mixamo") or {}).items()]
    st = lim.get("stance") or {}; sp = lim.get("spread") or {}
    f11 = st.get("F11") or {}
    sections.append('<section><h2>四肢活動範圍（參考、還沒定門檻）</h2><p>limb_probe.py 量的（左側）。截面積比＝關節中間和前後各兩刀最小的那個，靜止＝1；摺進去＝同一肢體上下兩節擠進去多深；互穿＝不同部位（手臂↔軀幹、腿↔腿）。</p>'
                    + table(["關節", "角度", "截面積比", "摺進去 mm", "翻面"], rr)
                    + "<p style='margin-top:10px'>肩、髖、腳踝、腳趾：</p>" + table(["關節", "角度", "摺進去 mm", "互穿 mm", "翻面"], oth)
                    + "<p style='margin-top:10px'>Mixamo 最彎那格：</p>" + table(["動作", "片與格", "彎幾度", "截面積比", "摺進去 mm", "互穿 mm（誰對誰）"], mx)
                    + f"<p style='margin-top:10px'>併腳：靜止兩腿最近（腳踝／小腿／膝／大腿）{esc(json.dumps(st.get('F10_rest_gap_mm', {}), ensure_ascii=False))} mm；兩條大腿各內收 {f11.get('adduct_deg_each')}° 兩腳就碰到（那時膝蓋差 {f11.get('knee_gap_mm')} mm）。"
                    + f"手指：靜止相鄰手指距離 {esc(json.dumps(sp.get('S1_rest_gap_mm', {}), ensure_ascii=False))} mm；四指張開指蹼拉伸 {(sp.get('S2_spread') or {}).get('web_edge_stretch_max')} 倍、翻面 {(sp.get('S2_spread') or {}).get('fold')}；只張食指時中指被拖 {sp.get('S4_drag_middle_mm')} mm。</p></section>")
for ex in meta.get("extra", []):                          # page.json 的 extra：[{"title","note","cols","items":[[絕對路徑, 說明], …]}]
    body_ = "".join(f'<figure><img src="{uri(f)}" alt="{esc(c)}" loading="lazy"><figcaption>{esc(c)}</figcaption></figure>' for f, c in ex.get("items", []) if os.path.exists(f))
    if body_:
        sections.append(f'<section><h2>{esc(ex.get("title", ""))}</h2>{"<p>" + ex["note"] + "</p>" if ex.get("note") else ""}<div class="views" style="--min:{ex.get("cols", "200px")}">{body_}</div></section>')
meas = info.get("measure") or {}
if meas and "error" not in meas:
    mrows = []
    for grp, gz in (("foot", "腳"), ("leg", "腿"), ("arm", "手臂"), ("neck", "脖子")):
        for k, v in (meas.get(grp) or {}).items():
            if isinstance(v, (int, float)):
                mrows.append([gz, MLABEL.get(k, k), v])
    sections.append('<section><h2>交接給服裝的尺寸（mm，T 字靜止、左側）</h2><p>body_measure.py：圍度是皮尺量法（截面凸包周長）；定義照 IBV／ISO。沿前臂、小腿每 5 mm 一圈的圍度在 build.json 的 measure.profile。</p>'
                    + table(["部位", "尺寸", "mm"], mrows) + "</section>")
html = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<style>
:root{{--bg:#F6F3F8;--surface:#fff;--fg:#34293B;--muted:#776B7F;--line:#E3DAE8;--accent:#7E64A6;--ok:#4F7D5A;--ok-soft:#E4F0E5;--ng:#B8485E;--ng-soft:#F8E3E7}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#1D1821;--surface:#28212D;--fg:#F0E9F3;--muted:#B2A6B9;--line:#3C3343;--accent:#C3AEE6;--ok:#9CCBA5;--ok-soft:#24362A;--ng:#F09AAB;--ng-soft:#43262D;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#1D1821;--surface:#28212D;--fg:#F0E9F3;--muted:#B2A6B9;--line:#3C3343;--accent:#C3AEE6;--ok:#9CCBA5;--ok-soft:#24362A;--ng:#F09AAB;--ng-soft:#43262D;color-scheme:dark}}
body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.7 "Noto Sans TC","Microsoft JhengHei",sans-serif}}
.wrap{{max-width:1100px;margin:0 auto;padding:32px 16px 64px;display:grid;gap:36px}}
h1{{font-size:clamp(26px,4vw,34px);margin:0}} h2{{font-size:21px;margin:0 0 8px}} p{{margin:0 0 8px;max-width:70ch}}
.card{{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px 18px}}
.views{{display:grid;grid-template-columns:repeat(auto-fill,minmax(var(--min),1fr));gap:10px}}
figure{{margin:0;background:var(--surface);border:1px solid var(--line);border-radius:10px;overflow:hidden}}
figure img{{display:block;width:100%;height:auto}} figcaption{{font-size:13px;color:var(--muted);padding:4px 8px}}
.tw{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;min-width:520px;font-size:15px}}
td,th{{text-align:left;padding:8px 12px;border-bottom:1px solid var(--line);vertical-align:top}}
.chip{{border-radius:999px;padding:1px 10px;font-size:13px;white-space:nowrap}} .chip.ok{{background:var(--ok-soft);color:var(--ok)}} .chip.ng{{background:var(--ng-soft);color:var(--ng)}}
ul{{margin:0;padding-left:1.3em}} .muted{{color:var(--muted);font-size:14px}} code{{font-size:.86em;overflow-wrap:anywhere}}
</style></head><body><div class="wrap">
<header><h1>{esc(title)}</h1>{"<p>" + lead + "</p>" if lead else ""}
<p class="muted">頭：<code>{esc(hd.get("path", "?"))}</code>（sha {esc(str(hd.get("sha256", ""))[:12])}）・身高 {info.get("T")} m・{info.get("N")} 頭身・{info.get("faces")} 面・出廠檢查 {n_ok}／{len(checks)} 項通過</p></header>
{('<section class="card"><h2>這版改了什麼</h2><ul>' + lst("changes") + "</ul></section>") if meta.get("changes") else ""}
<section><h2>出廠檢查</h2><div class="card tw"><table><thead><tr><th>項目</th><th>結果</th><th>數字</th></tr></thead><tbody>{rows or '<tr><td colspan="3">還沒跑 body_checks.py</td></tr>'}</tbody></table></div></section>
{"".join(sections)}
{('<section class="card"><h2>已知問題</h2><ul>' + lst("issues") + "</ul></section>") if meta.get("issues") else ""}
{('<section class="card"><h2>要你決定的事</h2><ul>' + lst("asks") + "</ul></section>") if meta.get("asks") else ""}
</div></body></html>"""
open(OUT, "w", encoding="utf-8").write(html)
print("PAGE", OUT, round(len(html) / 1e6, 2), "MB")
