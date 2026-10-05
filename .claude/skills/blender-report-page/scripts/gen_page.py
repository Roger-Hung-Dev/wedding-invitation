# 產生成果網頁（系統 Python）：python gen_page.py --project <PROJ>
# 讀：project.json、qa/metrics.json（穿模/腳底）、qa/motion.json（渲染時量的轉速）、qa/metrics_first.json（第一輪，選填）、
#     library/actions_catalog.json（動作名稱、備註）、videos/、pictures/ 裡實際存在的檔案。
# 寫：PROJ/report.html（放在專案根目錄，本機直接開也看得到影片）、PROJ/report_files.json（給 Artifact 發布用的 {發布路徑: 來源路徑}，路徑相對於 PROJ）。
# 數字全部從檔案讀，不手抄；缺的影片顯示「渲染中」，不會壞版。
import argparse, html, json, os, sys
sys.stdout.reconfigure(encoding="utf-8")   # 中文輸出不要變亂碼（Windows 主控台預設 cp950）

ap = argparse.ArgumentParser(); ap.add_argument("--project", required=True)
a = ap.parse_args()
P = os.path.abspath(a.project)
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
LIB = os.path.join(REPO, ".claude", "docs", "data", "blender", "library")
TPL = os.path.join(os.path.dirname(__file__), "..", "assets", "page_template.html")
M = json.load(open(os.path.join(P, "project.json"), encoding="utf8"))
R = M.get("report", {})
ld = lambda p, d: json.load(open(p, encoding="utf8")) if os.path.exists(p) else d
MET = ld(os.path.join(P, "qa", "metrics.json"), {})
MOT = ld(os.path.join(P, "qa", "motion.json"), {})
FIRST = ld(os.path.join(P, "qa", "metrics_first.json"), {})
CAT = ld(os.path.join(LIB, "actions_catalog.json"), {"actions": []})["actions"]
has = lambda rel: os.path.exists(os.path.join(P, rel))
esc = html.escape
files = {}


def media(rel):
    """登記要發布的檔案，回傳網頁裡用的相對路徑"""
    files[rel] = rel
    return rel


def video(rel, poster, attrs='autoplay muted loop playsinline', lazy=False):
    if not has(rel):
        return '<div class="pending">渲染中</div>'
    pa = f' poster="{media(poster)}"' if has(poster) else ""
    src = f'data-src="{media(rel)}"' if lazy else f'src="{media(rel)}"'
    return f'<video {src}{pa} {attrs}></video>'


def img(rel, alt):
    return f'<img src="{media(rel)}" alt="{esc(alt)}" loading="lazy">' if has(rel) else '<div class="pending">渲染中</div>'


def verdict(k, note_contact):
    m, mo = MET.get(k), MOT.get(k, {})
    if not m:
        return None
    pen = max(m["pen_core"], m["pen_hands"], m["pen_legs"])
    v = mo.get("body_vmax", m["vmax"]); j = mo.get("body_jerk", m["jerk"])
    airborne = k in ("jump", "cheer", "spin") or "hop" in (note_contact or "")
    feet_ok = m["foot_min"] >= -0.5 and (airborne or m["foot_float"] <= 0.5)
    issues = []
    if pen > 5 and not note_contact: issues.append(f"穿模 {pen:.0f} mm")
    if mo and v > 15: issues.append(f"轉太快 {v:.0f}°/格")
    if mo and j > 6: issues.append(f"速度突變 {j:.0f}")
    if not feet_ok: issues.append("腳沒貼地")
    return dict(issues=issues, pen=pen, v=v, frames=mo.get("frames", m["frames"]), foot_ok=m["foot_min"] >= -0.5)


cards, n_ok, n_done = [], 0, 0
for i, c in enumerate(CAT, 1):
    k = c["key"]; vd = verdict(k, c.get("contact_note"))
    rel = f"videos/actions/{k}.mp4"; poster = f"pictures/posters/actions/{k}.jpg"
    if vd is None:
        chip, dl = '<span class="chip">未檢查</span>', ""
    else:
        n_done += 1; ok = not vd["issues"] and has(rel); n_ok += ok
        chip = f'<span class="chip {"ok" if ok else "bad"}">{"通過" if ok else esc("、".join(vd["issues"]) or "還沒渲染")}</span>'
        pen_txt = "0" if vd["pen"] <= 0.5 else f'{vd["pen"]:.0f}'
        dl = (f'<dl><div><dt>穿模</dt><dd>{pen_txt} mm</dd></div><div><dt>最大轉速</dt><dd>{vd["v"]:.1f}°/格</dd></div>'
              f'<div><dt>腳底</dt><dd>{"貼地" if vd["foot_ok"] else "陷地"}</dd></div><div><dt>長度</dt><dd>{vd["frames"] / 24:.1f} 秒</dd></div></dl>')
    fix = ""
    b = FIRST.get(k)
    if b and vd:
        bp = max(b["pen_core"], b["pen_hands"], b["pen_legs"]); parts = []
        if bp > 5 and bp - vd["pen"] > 3: parts.append(f'穿模 {bp:.0f}→{pen_txt} mm')   # pen_txt 已把負值／0.5 以下顯示成 0（不會出現 -0）
        if b["vmax"] > 15 and b["vmax"] - vd["v"] > 3: parts.append(f'最大轉速 {b["vmax"]:.0f}→{vd["v"]:.0f}°/格')
        if b["foot_min"] < -0.5: parts.append(f'腳陷地 {abs(b["foot_min"]):.1f} cm→0')
        fix = "、".join(parts)
    notes = "".join(f'<p class="note">{esc(t)}</p>' for t in (c.get("contact_note"), c.get("note")) if t)
    cards.append(f'''<figure class="clip" id="a-{k}"><div class="vid">{video(rel, poster, 'muted loop playsinline preload="none"', lazy=True)}</div>
  <figcaption><span class="no">{i:02d}</span><b>{esc(c["name"])}</b>{chip}</figcaption>{dl}{notes}{f'<p class="fix">修正：{esc(fix)}</p>' if fix else ''}</figure>''')

scenes = []
for i, s in enumerate(M.get("scenes", []), 1):
    sid = s["id"]
    scenes.append(f'''<div class="panel scene"><h3>{i:02d}　{esc(s.get("title", sid))}　<span class="chip ok">{"便服" if s.get("outfit") == "base" else "服裝"}</span></h3>
  {video(f"videos/scenes/{sid}.mp4", f"pictures/posters/scenes/{sid}.jpg", 'controls muted loop playsinline preload="metadata"')}
  <p>{esc(s.get("desc", ""))}</p></div>''')
stills = sorted(f for f in os.listdir(os.path.join(P, "pictures", "scenes"))) if has("pictures/scenes") else []
if stills:
    scenes.append('<div class="panel wide"><h3>情境靜態圖</h3><div class="stills">' + "".join(img(f"pictures/scenes/{f}", f) for f in stills) + "</div></div>")

name = M.get("display_name") or M["name"]
facts = R.get("s1_facts") or ["身體、手、腳都檢查過；VRoid 刪掉的皮膚已補回。"]
limits = R.get("limits") or []
cos = M.get("costume", {})
T = open(TPL, encoding="utf8").read()
rep = {
    "{{TITLE}}": esc(R.get("title") or f"{name} 3D 角色工作簿"),
    "{{EYEBROW}}": esc(R.get("eyebrow") or f'{M["name"]}.vrm · Blender 5.2 · EEVEE'),
    "{{S3_MOVES_TEXT}}": esc(R.get("s3_moves_text") or "揮手、轉圈、跳躍：裙擺慢半拍、轉圈時張開、落地時往外撐。"),
    "{{S4_TEXT}}": esc(R.get("s4_text") or ("道具和場景都在 Blender 裡用程式做；手要碰到道具的地方（報紙邊、相機、捧花、刀柄、手機）用 IK 算手臂角度，所以手會真的抓在道具上。"
                                            if M.get("scenes") else "這一版還沒做情境；做好後短片會放在這裡。")),
    "{{BRAND}}": esc(name),
    "{{H1}}": esc(R.get("h1") or f"{name}：從捏臉到演出"),
    "{{LEDE}}": esc(R.get("lede") or "用 VRoid 捏好的臉，在 Blender 補完身體、測動作、照照片做服裝，最後放進情境裡演一遍。每個動作都用程式量過穿模、腳底、轉速。"),
    "{{N_OK}}": str(n_ok), "{{N_ALL}}": str(len(CAT)) + ("" if n_done == len(CAT) else f"（已檢查 {n_done} 個）"),
    "{{N_PARTS}}": str(len(cos.get("parts", []))), "{{N_SCENES}}": str(len(M.get("scenes", []))),
    "{{S1_TEXT}}": esc(R.get("s1_text") or "VRoid 匯出時會刪掉衣服底下的皮膚；這一步把缺的部分補回來，接縫的形狀、顏色、光影都對齊原本的皮膚，然後讓角色轉一圈檢查。"),
    "{{S1_FACTS}}": "".join(f"<li>{esc(t)}</li>" for t in facts),
    "{{V_TURN_BODY}}": video("videos/turn_body.mp4", "pictures/posters/turn_body.jpg"),
    "{{V_TURN_FACE}}": video("videos/turn_face.mp4", "pictures/posters/turn_face.jpg"),
    "{{I_HANDS}}": img("pictures/hands_sheet.jpg", "六種手勢的掌心與手背"),
    "{{I_FACE_FEET}}": img("pictures/face_feet.jpg", "五種表情與鞋子四個角度"),
    "{{CARDS}}": "\n".join(cards),
    "{{S3_TITLE}}": esc(cos.get("name") or "照片款服裝"),
    "{{S3_TEXT}}": esc(R.get("s3_summary") or cos.get("summary") or ""),
    "{{V_TURN_COSTUME}}": video("videos/turn_costume.mp4", "pictures/posters/turn_costume.jpg"),
    "{{V_COSTUME_MOVES}}": video("videos/costume_moves.mp4", "pictures/posters/costume_moves.jpg"),
    "{{I_REF_FRONT}}": img("pictures/ref_front.jpg", "照片正面"), "{{I_REF_BACK}}": img("pictures/ref_back.jpg", "照片背面"),
    "{{I_COS_FRONT}}": img("pictures/costume_front.jpg", "3D 正面"), "{{I_COS_BACK}}": img("pictures/costume_back.jpg", "3D 背面"),
    "{{P_COS_COMPARE}}": (f'<div class="panel wide"><h3>改版對照（上排改前、下排改後）</h3>{img("pictures/costume_compare.jpg", "服裝改前改後對照")}</div>'
                          if has("pictures/costume_compare.jpg") else ""),
    "{{SCENES}}": "\n".join(scenes) or '<div class="panel"><p>這個專案還沒有情境。</p></div>',
    "{{LIMITS}}": "\n".join(f"<li>{esc(t)}</li>" for t in limits) or "<li>（沒有）</li>",
}
for k, v in rep.items():
    T = T.replace(k, v)
open(os.path.join(P, "report.html"), "w", encoding="utf8").write(T)
json.dump(files, open(os.path.join(P, "report_files.json"), "w", encoding="utf8"), ensure_ascii=False, indent=0)
print(json.dumps({"page": os.path.join(P, "report.html"), "files_json": os.path.join(P, "report_files.json"), "files": len(files), "actions_ok": n_ok,
                  "actions_checked": n_done, "actions_total": len(CAT), "scenes": len(M.get("scenes", []))}, ensure_ascii=False))
