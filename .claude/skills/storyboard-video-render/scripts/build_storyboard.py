"""raw.json（extract_raw.js 的輸出）→ storyboard.json（schema storyboard/v2），並做完整檢查。

用法：
  python build_storyboard.py RAW.json -o storyboard.json

所有錯誤一次列完，有任何錯誤就不寫出 storyboard.json、exit 1。
錯誤不是給程式「修」的，是給分鏡稿補標註的依據 —— 一律回報，不要在 JSON 裡手動補值。
"""
import argparse
import json
import os
import re
import sys

from fx_notation import (MOTION_LAYOUTS, MOTIONS, PHOTO_COUNT, TITLE_INNER, TRANSITIONS, parse, parse_layout,
                         parse_title_style, strip_note)

# 調色預設（名稱寫在章節標頭「資訊-調色」；數值說明見 references/grading.md）
GRADE_PRESETS = {
    "原色": [],
    "暖褐復古": [{"op": "mul", "v": [1.035, 1.0, 0.93]}, {"op": "sat", "v": 0.88}, {"op": "lin", "a": 0.95, "b": 0.03}],
    "暖褐復古・暗部壓": [{"op": "mul", "v": [1.035, 1.0, 0.93]}, {"op": "sat", "v": 0.88},
                   {"op": "lin", "a": 0.95, "b": 0.03}, {"op": "gamma", "v": 1.08}],
    "明亮通透": [{"op": "lin", "a": 1.03, "b": 0.01}, {"op": "sat", "v": 1.05}],
    "明亮通透・副歌": [{"op": "lin", "a": 1.03, "b": 0.01}, {"op": "sat", "v": 1.14}, {"op": "contrast", "v": 1.06}],
    "金黃暖調": [{"op": "mul", "v": [1.05, 1.015, 0.91]}, {"op": "sat", "v": 1.03}],
    "粉橘夕陽": [{"op": "mul", "v": [1.035, 0.995, 0.985]}, {"op": "contrast", "v": 0.94, "offset": 0.012}],
}

# 編碼預設（可由總覽的「規格-CRF」「規格-位元率上限」覆寫）
VIDEO_DEFAULT = {"codec": "libx264", "preset": "slow", "crf": 16, "maxrate": "20M", "bufsize": "40M",
                 "profile": "high", "level": "4.2"}
AUDIO_DEFAULT = {"codec": "aac", "bitrate": "320k", "rate": 48000}
REQUIRED_SPEC = ["解析度", "影格率", "總長", "配樂", "照片原檔", "字型目錄", "底色"]
NO_CAPTION = {"—", "無", ""}

errors = []


def err(where, msg):
    errors.append(f"[{where}] {msg}")


def check_hash(doc):
    s = json.dumps(doc["payload"], ensure_ascii=False, separators=(",", ":"))
    h = 5381
    for ch in s:
        h = (h * 33 + ord(ch)) & 0xFFFFFFFF
    c = doc["check"]
    if h != c["hash"] or len(s) != c["chars"]:
        sys.exit(f"謄寫核對失敗：raw.json 與 Pencil 印出的內容不一致（字數 {len(s)} vs {c['chars']}，"
                 f"hash {h} vs {c['hash']}）。請重新執行 extract_raw.js，原樣存檔，不要手改。")


def seconds(tc):
    """「1:04」「1:04.5」→ 64.0／64.5"""
    m = re.match(r"^(\d+):(\d{2}(?:\.\d+)?)$", tc.strip())
    return int(m[1]) * 60 + float(m[2]) if m else None


def timecode(where, text):
    parts = re.split(r"\s*[–\-~～]\s*", (text or "").strip())
    if len(parts) == 2:
        a, b = seconds(parts[0]), seconds(parts[1])
        if a is not None and b is not None and b > a:
            return a, b
    err(where, f"時間碼「{text}」格式錯誤，應為「m:ss–m:ss」")
    return None, None


def num(v):
    return int(v) if float(v).is_integer() else float(v)


def value(v):
    """參數表的值：數字／逗號分隔的數字串列／其餘照字串。"""
    v = v.strip()
    if re.fullmatch(r"-?\d+(?:\.\d+)?", v):
        return num(v)
    if re.fullmatch(r"-?\d+(?:\.\d+)?(?:\s*,\s*-?\d+(?:\.\d+)?)+", v):
        return [num(x) for x in v.split(",")]
    return v


def nest(flat):
    """{'title.size': '182', 'subtitles.lines.0.text': 'A'} → 巢狀 dict／list"""
    root = {}
    for key, raw in flat.items():
        parts = key.split(".")
        cur = root
        for i, p in enumerate(parts):
            last = i == len(parts) - 1
            nxt = None if last else ([] if parts[i + 1].isdigit() else {})
            if isinstance(cur, list):
                idx = int(p)
                while len(cur) <= idx:
                    cur.append(None)
                if last:
                    cur[idx] = value(raw)
                else:
                    cur[idx] = cur[idx] if cur[idx] is not None else nxt
                    cur = cur[idx]
            else:
                if last:
                    cur[p] = value(raw)
                else:
                    cur = cur.setdefault(p, nxt)
    return root


def photo_names(where, text):
    names = []
    for line in (text or "").splitlines():
        line = re.sub(r"^\s*(左|右|\d+)\s*[:：]", "", strip_note(line)).strip()
        if line:
            names.append(os.path.basename(line.replace("\\", "/")))
    if not names:
        err(where, "素材欄沒有照片")
    return names


def grade_plan(where, text):
    """「明亮通透｜S2-06～S2-13：明亮通透・副歌」→ (基底, [(起, 迄, 預設)])"""
    if not text:
        err(where, "章節標頭缺「資訊-調色」")
        return None, []
    head, *rest = re.split(r"\s*｜\s*", strip_note(text))
    plan = []
    for part in rest:
        for seg in re.split(r"\s*；\s*", part):
            m = re.match(r"^(\S+?)\s*[～~]\s*(\S+?)\s*[:：]\s*(\S+)$", seg)
            if m:
                plan.append((m[1], m[2], m[3]))
            elif seg:
                err(where, f"調色區段「{seg}」格式錯誤，應為「S2-06～S2-13：預設名」")
    for g in [head] + [p[2] for p in plan]:
        if g not in GRADE_PRESETS:
            err(where, f"調色預設「{g}」不存在；可用：{'、'.join(GRADE_PRESETS)}")
    return head, plan


def title_block(kind, row, params_flat):
    """片頭／片尾列 → (style, start, end, 最後一張卡的轉場文字, params)"""
    cards = row["cards"]
    if not cards:
        err(kind, "沒有任何鏡頭卡")
        return None
    styles = set()
    for cd in cards:
        st, e = parse_title_style(cd["rows"].get("版型", ""), kind)
        if e:
            err(cd["id"] or kind, e)
        styles.add(st)
    if len(styles) > 1:
        err(kind, f"同一段{kind}的卡片版型不一致：{styles}")
    s, _ = timecode(cards[0]["id"], cards[0]["timecode"])
    _, e = timecode(cards[-1]["id"], cards[-1]["timecode"])
    for cd in cards[:-1]:
        obj, msg = parse(cd["rows"].get("轉場", ""), TITLE_INNER)
        if msg or obj["type"] != "none":
            err(cd["id"], f"{kind}內部的卡片轉場應寫「無切換」（{kind}樣式自己處理內部過場）")
    return styles.pop(), s, e, cards[-1], nest(params_flat)


def build(raw):
    P = raw["payload"]
    spec = P["spec"]
    for k in REQUIRED_SPEC:
        if not spec.get(k):
            err("00 總覽", f"缺「規格-{k}」")
    if errors:
        return None
    m = re.match(r"^(\d+)\s*[×xX]\s*(\d+)$", spec["解析度"].strip())
    if not m:
        err("規格-解析度", f"「{spec['解析度']}」應為「1920×1080」")
    w, h = (int(m[1]), int(m[2])) if m else (0, 0)
    fps = re.match(r"^(\d+)", spec["影格率"].strip())
    dur = seconds(spec["總長"].strip())
    if not fps or dur is None:
        err("00 總覽", "「規格-影格率」應為數字、「規格-總長」應為 m:ss")
        return None
    video = dict(VIDEO_DEFAULT)
    if spec.get("CRF"):
        video["crf"] = int(spec["CRF"])
    if spec.get("位元率上限"):
        video["maxrate"] = spec["位元率上限"].strip()
        video["bufsize"] = f"{int(re.match(r'\d+', video['maxrate'])[0]) * 2}M"

    rows = sorted(P["rows"], key=lambda r: int(r["name"][:2]))
    op_rows = [r for r in rows if r["name"].startswith("10 ")]
    ed_rows = [r for r in rows if "片尾" in r["name"]]
    body = [r for r in rows if r not in op_rows + ed_rows]
    if len(op_rows) != 1 or len(ed_rows) != 1 or rows[-1] is not ed_rows[0]:
        err("分鏡列", "必須剛好各有一列「10 分鏡列・片頭」與「NN 分鏡列・片尾」，且片尾是編號最大的一列")
        return None

    op = title_block("片頭", op_rows[0], P["openingParams"])
    ed = title_block("片尾", ed_rows[0], P["endingParams"])
    if not op or not ed:
        return None
    op_out, msg = parse(op[3]["rows"].get("轉場", ""), TRANSITIONS)
    if msg or op_out["type"] != "black":
        err(op[3]["id"], "片頭最後一張卡的轉場必須是「黑場 a+bs」")
    ed_last, msg = parse(ed[3]["rows"].get("轉場", ""), TITLE_INNER)
    if msg or ed_last["type"] != "fade-to-black":
        err(ed[3]["id"], "片尾最後一張卡的轉場必須是「淡出至黑 Ns」")
    else:
        ed[4]["fadeOut"] = ed_last["duration"]

    shots, seen = [], set()
    for row in body:
        base, plan = grade_plan(row["name"], row["header"].get("調色"))
        for cd in row["cards"]:
            sid = cd["id"]
            where = sid or cd["frame"]
            if sid in seen:
                err(where, "鏡號重複")
            seen.add(sid)
            if cd["frame"] != f"鏡-{sid}":
                err(where, f"卡片名「{cd['frame']}」與鏡號不一致")
            s, e = timecode(where, cd["timecode"])
            r = cd["rows"]
            for key in ("版型", "運鏡", "轉場", "字卡", "素材"):
                if key not in r:
                    err(where, f"缺「列-{key}」")
            lay, msg = parse_layout(r.get("版型", ""))
            if msg:
                err(where, msg)
            mo, msg = parse(r.get("運鏡", ""), MOTIONS)
            if msg:
                err(where, "運鏡" + msg)
            tr, msg = parse(r.get("轉場", ""), TRANSITIONS)
            if msg:
                err(where, "轉場" + msg)
            if strip_note(r.get("字卡", "")) not in NO_CAPTION:
                err(where, f"字卡「{r['字卡']}」：渲染器尚未支援正片字卡，請改寫「—（無）」或先擴充渲染器")
            photos = photo_names(where, r.get("素材"))
            if s is not None and cd["seconds"]:
                pill = re.match(r"^(\d+(?:\.\d+)?)", cd["seconds"].strip())
                if not pill or abs(float(pill[1]) - (e - s)) > 1e-6:
                    err(where, f"秒數膠囊「{cd['seconds']}」與時間碼 {cd['timecode']} 不符")
            if lay and mo and lay not in MOTION_LAYOUTS[mo["type"]]:
                err(where, f"版型 {lay} 不能搭配運鏡 {mo['type']}")
            if lay:
                lo, hi = PHOTO_COUNT[lay]
                if not lo <= len(photos) <= hi:
                    err(where, f"版型 {lay} 需要 {lo}～{hi} 張照片，素材欄有 {len(photos)} 張")
            g = base
            for a, b, name in plan:
                if a <= sid <= b:
                    g = name
            shots.append({"id": sid, "start": num(s) if s is not None else s, "end": num(e) if e is not None else e,
                          "chapter": row["chapter"], "grade": g, "layout": lay, "photos": photos,
                          "motion": mo, "out": tr})

    sb = {
        "schema": "storyboard/v2",
        "title": "",
        "source": {"pen": "", "note": "由 build_storyboard.py 自 raw.json 產生；不要手改，改分鏡稿後重新抽取"},
        "output": {"width": w, "height": h, "fps": int(fps[1]), "duration": num(dur), "video": video, "audio": AUDIO_DEFAULT},
        "audio": {"file": spec["配樂"].strip()},
        "assets": {"photoDir": spec["照片原檔"].strip(), "fontDir": spec["字型目錄"].strip()},
        "palette": {"backdrop": spec["底色"].strip()},
        "quality": {"sharpen": {"radius": 1.2, "percent": 70, "threshold": 2}, "tileSharpenPercent": 60},
        "grades": GRADE_PRESETS,
        "opening": {"style": op[0], "start": num(op[1]), "end": num(op[2]), "out": op_out, "params": op[4]},
        "shots": shots,
        "ending": {"style": ed[0], "start": num(ed[1]), "end": num(ed[2]), "params": ed[4]},
    }
    validate(sb)
    return sb


def validate(sb):
    shots = sb["shots"]
    if any(s["start"] is None for s in shots):
        return
    # 時間軸首尾相接
    cur = sb["opening"]["end"]
    if sb["opening"]["start"] != 0:
        err("片頭", "片頭必須從 0:00 開始")
    for s in shots:
        if abs(s["start"] - cur) > 1e-6:
            err(s["id"], f"時間碼不連續：上一段結束於 {cur}，本鏡從 {s['start']} 開始")
        cur = s["end"]
    if abs(sb["ending"]["start"] - cur) > 1e-6:
        err("片尾", f"片尾開始 {sb['ending']['start']} 與最後一鏡結束 {cur} 不相接")
    if abs(sb["ending"]["end"] - sb["output"]["duration"]) > 1e-6:
        err("片尾", f"片尾結束 {sb['ending']['end']} ≠ 規格總長 {sb['output']['duration']}")
    # 轉場長度不可超過相鄰兩鏡的一半以上
    for i, s in enumerate(shots):
        tr = s["out"]
        if not tr:
            continue
        nxt = shots[i + 1] if i + 1 < len(shots) else None
        if tr["type"] in ("dissolve", "push"):
            if not nxt:
                err(s["id"], "最後一鏡只能接「黑場」進片尾")
            elif tr["duration"] / 2 > min(s["end"] - s["start"], nxt["end"] - nxt["start"]) / 2:
                err(s["id"], f"轉場 {tr['duration']}s 超過相鄰鏡頭長度")
        if nxt is None and tr["type"] != "black":
            err(s["id"], "最後一鏡的轉場必須是「黑場」")
        if tr["type"] == "black" and nxt and nxt["chapter"] == s["chapter"]:
            err(s["id"], "黑場只用在章節交界，章內請改用溶接或硬切")
    # 檔案存在
    a = sb["assets"]
    for s in shots:
        for p in s["photos"]:
            if not os.path.isfile(os.path.join(a["photoDir"], p)):
                err(s["id"], f"照片原檔不存在：{os.path.join(a['photoDir'], p)}")
    if not os.path.isfile(sb["audio"]["file"]):
        err("規格-配樂", f"配樂檔不存在：{sb['audio']['file']}")
    fonts = set(re.findall(r'"font":\s*"([^"]+)"', json.dumps(sb, ensure_ascii=False)))
    for f in fonts:
        if not os.path.isfile(os.path.join(a["fontDir"], f)):
            err("字型", f"字型檔不存在：{os.path.join(a['fontDir'], f)}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("raw")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--pen", default="", help="來源分鏡稿路徑（只記錄在 source.pen）")
    ap.add_argument("--title", default="")
    a = ap.parse_args()
    with open(a.raw, encoding="utf-8") as f:
        raw = json.load(f)
    check_hash(raw)
    sb = build(raw)
    if errors:
        print(f"分鏡稿有 {len(errors)} 個問題，未產出 storyboard.json：", file=sys.stderr)
        for e in errors:
            print("  " + e, file=sys.stderr)
        sys.exit(1)
    sb["source"]["pen"], sb["title"] = a.pen, a.title
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(sb, f, ensure_ascii=False, indent=1)
    print(f"ok：{len(sb['shots'])} 鏡，{sb['output']['duration']} 秒 → {a.out}")


if __name__ == "__main__":
    main()
