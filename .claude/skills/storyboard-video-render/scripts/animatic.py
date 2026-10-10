"""動態分鏡（animatic）產生器：比稿 .pen 的縮圖圖層＋規劃表的時間軸 → 每版一支會動的預覽 mp4。

這不是 render_storyboard.py 的替代品：那支讀 v2 照片輪播稿（NN 分鏡列）產正式成片；
這支給「還沒有正式素材」的比稿稿（頂層 `V01 …`～`VNN …` 橫帶、每張卡 `鏡-Vxx-yy`）
先做會動的預覽，讓使用者看節奏與效果。角色用稿上的佔位框、沒有聲音。

用法（工作目錄 WORK 放抽取結果與匯出的圖層，見 references/animatic.md 的步驟 1～2）：
  python animatic.py report --work WORK --plan PLAN.md [V01 …]       # 字幕↔圖層對應報告（先看這個）
  python animatic.py prep   --work WORK --plan PLAN.md [V01 …]       # 圖層定位＋抹字＋重組驗證
  python animatic.py still  --work WORK --plan PLAN.md V01 3.5 15.2  # 指定版本與秒數的單格 png
  python animatic.py video  --work WORK --plan PLAN.md --out DIR [V01 …]
共通選項：--rules RULES.json（逐鏡動態設定；省略時只用通用規則）、--jobs N

WORK 的內容：
  extract_raw.txt     execute 印出的頂層圖層清單（每行一筆 JSON，見 animatic.md）
  extract_nested.txt  框內文字節點清單
  layers/Vxx/<id>.png Export(scale 4) 匯出的圖層與整格縮圖
  fonts/              稿上用到、本機沒有的字型檔
  cache/              prep 產生的定位結果與抹字後的圖層（可刪，重跑 prep 會重建）
"""
import argparse
import json
import math
import os
import random
import re
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

SC = 4                      # Export 倍率（縮圖 480×270 → 1920×1080）
OW, OH, FPS = 1280, 720, 30  # 輸出規格
K = OW / 1920.0             # 1920 座標 → 輸出座标
TH_W, TH_H = 480, 270       # 縮圖尺寸

# ════════════════════════════════════════════════════════════════════════
# 規劃表解析
# ════════════════════════════════════════════════════════════════════════
COLS = ["id", "tc", "sec", "seg", "desc", "subs", "chars", "dyn", "trans", "sfx", "assets"]
RE_WIN = re.compile(r"(\d+(?:\.\d+)?)～(\d+(?:\.\d+)?)s")


def tc_sec(s):
    m, x = s.strip().split(":")
    return int(m) * 60 + float(x)


def strip_paren(s):
    """去掉全形括號內的註記（可巢狀）。"""
    out, depth = [], 0
    for ch in s:
        if ch == "（":
            depth += 1
        elif ch == "）":
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append(ch)
    return "".join(out).strip()


def last_paren(s):
    """回傳句尾最後一組全形括號的內容與括號前的本文。"""
    s = s.strip()
    if not s.endswith("）"):
        return s, ""
    depth = 0
    for i in range(len(s) - 1, -1, -1):
        if s[i] == "）":
            depth += 1
        elif s[i] == "（":
            depth -= 1
            if depth == 0:
                return s[:i].strip(), s[i + 1:-1]
    return s, ""


def parse_subs(cell):
    subs = []
    if strip_paren(cell) in ("—", "", "-"):
        return subs
    for raw in cell.split("<br>"):
        raw = raw.strip()
        if not raw:
            continue
        kind, scene = "sub", False
        # 【場景字】＝文字是場景裡的實體物件（布條、黑板、燈牌）：跟著場景一起被鏡頭推拉平移
        for tag, k, sc in (("【場景字・大標】", "big", True), ("【場景字】", "sub", True),
                           ("【大標】", "big", False), ("【標籤】", "label", False)):
            if raw.startswith(tag):
                kind, scene, raw = k, sc, raw[len(tag):]
                break
        body, note = last_paren(raw)
        m = RE_WIN.search(note)
        if not m:
            raise ValueError(f"字幕沒有時段：{raw}")
        parts = [p.strip() for p in body.split("／")]
        subs.append({"kind": kind, "text": "\n".join(parts), "parts": parts, "scene": scene,
                     "t0": float(m.group(1)), "t1": float(m.group(2)), "note": note})
    return subs


POS9 = {"左上": (0, 0), "中上": (1, 0), "右上": (2, 0), "左": (0, 1), "中": (1, 1), "右": (2, 1),
        "左下": (0, 2), "中下": (1, 2), "右下": (2, 2)}


def parse_chars(cell):
    out = []
    if strip_paren(cell) in ("—", ""):
        return out
    for raw in cell.split("<br>"):
        f = [x.strip() for x in raw.split("｜")]
        if len(f) < 5:
            continue
        who, act, pos, size, win = f[:5]
        opt = {}
        for x in f[5:]:
            if "：" in x:
                k, v = x.split("：", 1)
                opt[k] = v
        if act.startswith("新動作："):
            label_act = strip_paren(act)
        else:
            label_act = strip_paren(act)
        p = pos.split("→")
        m = RE_WIN.search(win)
        enter = ("fade", 0.3)
        if "進場" in opt:
            mm = re.match(r"(直接|淡入|滑入)\s*(\d+(?:\.\d+)?)?s?", opt["進場"])
            if mm:
                enter = ({"直接": "cut", "淡入": "fade", "滑入": "slide"}[mm.group(1)],
                         float(mm.group(2) or 0.3))
        h0 = float(re.search(r"(\d+)", size).group(1)) / 100.0
        # 「高 18%（走近到 32%）」「高 50%（走遠縮到 30%）」：在本段時間內線性變大／變小
        # （「鏡頭推近到」「升空後縮小」是鏡頭造成的，交給規則檔的 cam，不在這裡算）
        mh = re.search(r"走(?:近|遠)(?:縮)?到\s*(\d+)%", size)
        out.append({"who": who, "act": label_act, "from": p[0].strip(), "to": p[-1].strip(),
                    "move": len(p) > 1, "h": h0, "h1": float(mh.group(1)) / 100.0 if mh else h0,
                    "t0": float(m.group(1)), "t1": float(m.group(2)), "enter": enter,
                    "orient": opt.get("朝向", "正面")})
    return out


def parse_trans(cell):
    s = strip_paren(cell)
    if s.startswith("硬切") or s == "":
        return {"type": "cut"}
    m = re.match(r"溶接\s*(\d+(?:\.\d+)?)s", s)
    if m:
        return {"type": "dissolve", "d": float(m.group(1))}
    m = re.match(r"推移\s*([←→])\s*(\d+(?:\.\d+)?)s", s)
    if m:
        return {"type": "push", "dir": -1 if m.group(1) == "←" else 1, "d": float(m.group(2))}
    m = re.match(r"閃白\s*(\d+(?:\.\d+)?)\+(\d+(?:\.\d+)?)s\s*(\d+)%", s)
    if m:
        return {"type": "flash", "pre": float(m.group(1)), "post": float(m.group(2)), "peak": float(m.group(3)) / 100}
    m = re.match(r"黑場\s*(\d+(?:\.\d+)?)\+(\d+(?:\.\d+)?)s", s)
    if m:
        return {"type": "black", "out": float(m.group(1)), "in": float(m.group(2))}
    m = re.match(r"淡出至黑\s*(\d+(?:\.\d+)?)s", s)
    if m:
        return {"type": "fadeout", "d": float(m.group(1))}
    raise ValueError(f"轉場寫法不認得：{cell}")


def parse_plan(path):
    vers, cur = {}, None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        m = re.match(r"^## 版本 (\d+)：(.+)$", line)
        if m:
            cur = f"V{int(m.group(1)):02d}"
            vers[cur] = {"id": cur, "title": m.group(2).strip(), "shots": [], "category": None}
            continue
        m = re.match(r"^- \*\*風格類別\*\*：(.+)$", line)
        if cur and m:
            vers[cur]["category"] = m.group(1).strip()
            continue
        if cur and line.startswith("| " + cur + "-"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) != len(COLS):
                raise ValueError(f"欄數不對（{len(cells)}）：{line[:40]}")
            r = dict(zip(COLS, cells))
            a, b = r["tc"].split("–")
            shot = {"id": r["id"], "t0": tc_sec(a), "t1": tc_sec(b), "seg": r["seg"],
                    "subs": parse_subs(r["subs"]), "chars": parse_chars(r["chars"]),
                    "dyn": r["dyn"], "trans": parse_trans(r["trans"]), "trans_raw": r["trans"],
                    "desc": r["desc"]}
            shot["dur"] = shot["t1"] - shot["t0"]
            if abs(shot["dur"] - float(r["sec"])) > 1e-6:
                raise ValueError(f"{r['id']} 時間碼與秒數不符")
            vers[cur]["shots"].append(shot)
    for v in vers.values():
        sh = v["shots"]
        for a, b in zip(sh, sh[1:]):
            if abs(a["t1"] - b["t0"]) > 1e-6:
                raise ValueError(f"{a['id']}→{b['id']} 時間碼不連續")
        v["total"] = sh[-1]["t1"] if sh else 0
    return vers


# ════════════════════════════════════════════════════════════════════════
# 抽取結果
# ════════════════════════════════════════════════════════════════════════
def load_extract(work):
    cards, ver = {}, None
    for ln in open(os.path.join(work, "extract_raw.txt"), encoding="utf-8"):
        ln = ln.strip()
        if not ln.startswith("["):
            continue
        r = json.loads(ln)
        if r[0] == "@":
            ver = r[1]
            continue
        if r[0] == "#":
            cur = {"id": r[1], "ver": ver, "thumb": r[2], "bg": r[3], "layers": []}
            cards[r[1]] = cur
            continue
        L = {"id": r[0], "type": r[1], "x": r[2], "y": r[3], "w": r[4], "h": r[5], "rot": r[6],
             "op": r[7], "name": r[8], "text": r[9] if len(r) > 9 and isinstance(r[9], str) else "",
             "style": r[10] if r[1] == "x" and len(r) > 10 else None}
        cur["layers"].append(L)
    nested = {}
    p = os.path.join(work, "extract_nested.txt")
    if os.path.exists(p):
        for ln in open(p, encoding="utf-8"):
            if not ln.startswith('["'):
                continue
            r = json.loads(ln)
            nested.setdefault(r[1], []).append({"card": r[0], "top": r[1], "id": r[2], "ox": r[4], "oy": r[5],
                                                "w": r[6], "h": r[7], "name": r[8], "text": r[9], "style": r[10]})
    return cards, nested


def norm(s):
    return re.sub(r"[\s／‖]", "", s or "")


def is_char_box(L):
    return L["name"].startswith("角色-")


def counter_values(text):
    """「0% → 99% → 100%」「3 → 2 → 1」這類大標回傳各值；不是就回傳 None。"""
    if "→" not in text:
        return None
    vals = [v.strip() for v in text.split("→")]
    return vals if all(re.fullmatch(r"\d+%?", v) for v in vals) else None


def match_text(t, subs):
    """文字節點內容 t 對到哪一句字幕。回傳 (句索引, 行索引或 None) 或 None。"""
    nt = norm(t)
    if not nt:
        return None
    for i, s in enumerate(subs):
        if counter_values(s["text"]):
            continue
        if nt == norm(s["text"]):
            return (i, None)
    for i, s in enumerate(subs):
        if counter_values(s["text"]):
            continue
        for j, p in enumerate(s["parts"]):
            if nt == norm(p):
                return (i, j)
    for i, s in enumerate(subs):
        if counter_values(s["text"]):
            continue
        ns = norm(s["text"])
        if len(nt) >= 4 and ((nt in ns and len(nt) >= 0.6 * len(ns)) or (ns in nt and len(ns) >= 0.6 * len(nt))):
            return (i, None)
    return None


NESTED_MIN_SIZE = 12   # 框內文字小於這個字級（縮圖 px）視為介面字（貼文框帳號、按鈕字），不當字幕


def match_counter(t, subs):
    nt = norm(t)
    for i, s in enumerate(subs):
        vals = counter_values(s["text"])
        if vals and nt in vals:
            return i
    return None


def analyse_shot(shot, card, nested):
    """把縮圖圖層分類。回傳 dict：
    roles[layer_id] = {"role": "sub"|"counter"|"static"|"char", "sub": i, "part": j}
    split[layer_id] = [(nested 節點, sub i, part j 或 "counter")]   需要抹字拆出的框
    missing = [句索引]   縮圖裡沒有對應圖層的字幕
    """
    subs = shot["subs"]
    roles, split, used = {}, {}, {}
    for L in card["layers"]:
        if is_char_box(L):
            roles[L["id"]] = {"role": "char"}
            continue
        if L["type"] == "x":
            ci = match_counter(L["text"], subs)
            if ci is not None:
                roles[L["id"]] = {"role": "counter", "sub": ci}
                used.setdefault(ci, []).append(L["id"])
                continue
            m = match_text(L["text"], subs)
            if m:
                roles[L["id"]] = {"role": "sub", "sub": m[0], "part": m[1]}
                used.setdefault(m[0], []).append(L["id"])
                continue
            # 一個文字節點裡放了兩句不同時段的字幕（每行各對一句）→ 之後依行切開
            lines = [ln for ln in L["text"].split("\n") if ln.strip()]
            lm = [match_text(ln, subs) for ln in lines]
            if len(lines) > 1 and all(lm):
                roles[L["id"]] = {"role": "lines", "subs": [x[0] for x in lm]}
                for x in lm:
                    used.setdefault(x[0], []).append(L["id"])
                continue
            roles[L["id"]] = {"role": "static"}
            continue
        kids = [nd for nd in nested.get(L["id"], []) if (nd["style"].get("s") or 0) >= NESTED_MIN_SIZE]
        hits = []
        for nd in kids:
            ci = match_counter(nd["text"], subs)
            if ci is not None:
                hits.append((nd, ci, "counter"))
                continue
            m = match_text(nd["text"], subs)
            if m:
                hits.append((nd, m[0], m[1]))
        if not hits:
            roles[L["id"]] = {"role": "static"}
            continue
        only_one = len({h[1] for h in hits}) == 1 and len(hits) == len(kids) and hits[0][2] != "counter"
        if only_one:
            roles[L["id"]] = {"role": "sub", "sub": hits[0][1], "part": hits[0][2] if len(hits) == 1 else None}
            used.setdefault(hits[0][1], []).append(L["id"])
        else:
            roles[L["id"]] = {"role": "static"}
            split[L["id"]] = hits
            for nd, i, j in hits:
                used.setdefault(i, []).append(nd["id"])
    missing = [i for i in range(len(subs)) if i not in used]
    return {"roles": roles, "split": split, "missing": missing, "used": used}


def cmd_report(args):
    plan = parse_plan(args.plan)
    cards, nested = load_extract(args.work)
    for vid, v in plan.items():
        if args.vers and vid not in args.vers:
            continue
        print(f"=== {vid} {v['title']}  總長 {v['total']:g}s")
        for sh in v["shots"]:
            card = cards.get(sh["id"])
            if not card:
                print(f"  [{sh['id']}] ⛔ 稿上找不到這張卡")
                continue
            a = analyse_shot(sh, card, nested)
            print(f"  [{sh['id']}] {sh['seg']} {sh['dur']:g}s 轉場 {sh['trans']}")
            for i, s in enumerate(sh["subs"]):
                who = a["used"].get(i)
                tag = ",".join(who) if who else "（縮圖沒有，PIL 補畫）"
                print(f"     {s['kind']:5s} {s['t0']:>4}～{s['t1']:<4} {s['text'][:24].replace(chr(10), '⏎'):26s} ← {tag}")
            for lid, hits in a["split"].items():
                print(f"     拆框 {lid}: " + "、".join(f"{h[0]['text'][:8]}→{h[1]}" for h in hits))
            for c in sh["chars"]:
                print(f"     角色 {c['who']} {c['act'][:14]} {c['from']}{'→' + c['to'] if c['move'] else ''} 高{c['h']:.0%} {c['t0']}～{c['t1']} {c['enter']}")


# ════════════════════════════════════════════════════════════════════════
# prep：圖層定位（座標初值＋模板比對）、重組驗證、框內抹字
# ════════════════════════════════════════════════════════════════════════
def hex_rgba(s):
    s = (s or "#000000").lstrip("#")
    if len(s) == 6:
        s += "FF"
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4, 6))


def bg_image(fill, w, h):
    """縮圖內容的底色（純色或放射漸層）。"""
    if isinstance(fill, str):
        return Image.new("RGBA", (w, h), hex_rgba(fill))
    if isinstance(fill, dict) and fill.get("gradientType") == "radial":
        cs = fill["colors"]
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2).clip(0, 1)
        c0 = np.array(hex_rgba(cs[0]["color"]), np.float32)
        c1 = np.array(hex_rgba(cs[-1]["color"]), np.float32)
        a = (c0 * (1 - r[..., None]) + c1 * r[..., None]).astype(np.uint8)
        return Image.fromarray(a, "RGBA")
    return Image.new("RGBA", (w, h), (0, 0, 0, 255))


def f32(im):
    return np.asarray(im.convert("RGBA"), np.float32) / 255.0


CAP = 0.15


def _err(C, F, L, x, y):
    """把 L 疊在 C 的 (x,y)，回傳「誤差減少量」的負值（越小越好）。
    用減少量而不是疊上後的誤差：深色字疊在深色天空上誤差也很小，但不會讓誤差變小。
    每個像素的誤差封頂 CAP：之後才疊上的圖層會遮住一部分，避免遮擋處主導結果。"""
    Hc, Wc = C.shape[:2]
    h, w = L.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(Wc, x + w), min(Hc, y + h)
    if x1 - x0 < 1 or y1 - y0 < 1:
        return 9.0
    l = L[y0 - y:y1 - y, x0 - x:x1 - x]
    a = l[..., 3:4]
    m = a[..., 0] > 0.01
    if m.sum() < 4:
        return 9.0
    c = C[y0:y1, x0:x1, :3]
    f = F[y0:y1, x0:x1, :3]
    pred = l[..., :3] * a + c * (1 - a)
    da = np.minimum(np.abs(pred - f).sum(-1)[m], CAP)
    db = np.minimum(np.abs(c - f).sum(-1)[m], CAP)
    return float((da - db).sum()) / (h * w)


def _after_err(C, F, L, x, y):
    Hc, Wc = C.shape[:2]
    h, w = L.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(Wc, x + w), min(Hc, y + h)
    if x1 - x0 < 1 or y1 - y0 < 1:
        return 9.0
    l = L[y0 - y:y1 - y, x0 - x:x1 - x]
    a = l[..., 3:4]
    m = a[..., 0] > 0.15
    if m.sum() < 4:
        return 0.0
    pred = l[..., :3] * a + C[y0:y1, x0:x1, :3] * (1 - a)
    return float(np.minimum(np.abs(pred - F[y0:y1, x0:x1, :3]).sum(-1)[m], CAP).mean())


def search(C, F, L, xr, yr, step=1, keep=1, ex=None):
    """ex＝預期位置；分數相同時取離預期近的（圖層與底色同色、疊了沒差時）。"""
    res = []
    for y in range(yr[0], yr[1] + 1, step):
        for x in range(xr[0], xr[1] + 1, step):
            e = _err(C, F, L, x, y)
            if ex is not None:
                e += 1e-7 * math.hypot(x - ex[0], y - ex[1])
            res.append((e, x, y))
    res.sort()
    return res[:keep] if keep > 1 else res[0]


def boxdown(a, q):
    h, w = a.shape[0] // q * q, a.shape[1] // q * q
    if h == 0 or w == 0:
        return a[::q, ::q]
    return a[:h, :w].reshape(h // q, q, w // q, q, a.shape[2]).mean((1, 3))


def locate(C, F, L, bx, by, bw, bh):
    """在 F 裡找 L 的位置。bx..bh 是節點外框（1920 座標）。
    匯出圖會裁到筆畫（文字、弧形）或外擴（陰影、模糊），而且不一定對稱，所以兩種都涵蓋後搜尋。"""
    h, w = L.shape[:2]
    m = 2 if abs(w - bw) <= 2 and abs(h - bh) <= 2 else 6

    def rng(b, bs, s):
        return (int(math.floor(b - max(0, s - bs))) - m, int(math.ceil(b + max(0, bs - s))) + m)

    xr, yr = rng(bx, bw, w), rng(by, bh, h)
    # 預期位置：外擴時對稱、裁切時置中
    ex = (bx + (bw - w) / 2, by + (bh - h) / 2)
    if (xr[1] - xr[0]) * (yr[1] - yr[0]) > 300 and min(h, w) >= 8:
        # 粗搜：區塊平均縮小 4 倍（不能跳格取樣，細筆畫會失真），取前 3 名再細搜
        q = 4
        Cs, Fs, Ls = boxdown(C, q), boxdown(F, q), boxdown(L, q)
        cands = search(Cs, Fs, Ls, (xr[0] // q, xr[1] // q + 1), (yr[0] // q, yr[1] // q + 1), keep=3,
                       ex=(ex[0] / q, ex[1] / q))
        best = (9e9, 0, 0)
        for _, x, y in cands:
            r = search(C, F, L, (x * q - q, x * q + q), (y * q - q, y * q + q), ex=ex)
            best = min(best, r)
        e, x, y = best
    else:
        e, x, y = search(C, F, L, xr, yr, ex=ex)
    return x, y, _after_err(C, F, L, x, y)


def over_np(C, L, x, y, mult=1.0):
    Hc, Wc = C.shape[:2]
    h, w = L.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(Wc, x + w), min(Hc, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    l = L[y0 - y:y1 - y, x0 - x:x1 - x]
    a = l[..., 3:4] * mult
    C[y0:y1, x0:x1, :3] = l[..., :3] * a + C[y0:y1, x0:x1, :3] * (1 - a)


def inpaint(P, mask):
    """把 P（RGBA float，未預乘）在 mask 處補成周圍的顏色（列、欄線性內插的平均，再平滑幾次）。"""
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return P
    pad = 6
    y0, y1 = max(0, ys.min() - pad), min(P.shape[0], ys.max() + pad + 1)
    x0, x1 = max(0, xs.min() - pad), min(P.shape[1], xs.max() + pad + 1)
    sub = P[y0:y1, x0:x1].copy()
    m = mask[y0:y1, x0:x1]
    pm = sub.copy()
    pm[..., :3] *= pm[..., 3:4]          # 預乘，讓透明底維持透明
    acc = np.zeros_like(pm)
    cnt = np.zeros(m.shape, np.float32)
    for axis in (0, 1):
        arr = pm if axis == 1 else pm.transpose(1, 0, 2)
        mm = m if axis == 1 else m.T
        out = arr.copy()
        ok = np.zeros(mm.shape, bool)
        for i in range(arr.shape[0]):
            known = np.nonzero(~mm[i])[0]
            hole = np.nonzero(mm[i])[0]
            if len(hole) == 0 or len(known) < 2:
                continue
            for ch in range(4):
                out[i, hole, ch] = np.interp(hole, known, arr[i, known, ch])
            ok[i, hole] = True
        if axis == 0:
            out, ok = out.transpose(1, 0, 2), ok.T
        acc[ok] += out[ok]
        cnt[ok] += 1
    fill = np.where(cnt[..., None] > 0, acc / np.maximum(cnt, 1)[..., None], pm)
    res = np.where(m[..., None], fill, pm)
    for _ in range(4):   # 輕微平滑補洞處
        blur = res.copy()
        blur[1:-1, 1:-1] = (res[:-2, 1:-1] + res[2:, 1:-1] + res[1:-1, :-2] + res[1:-1, 2:] + res[1:-1, 1:-1]) / 5
        res = np.where(m[..., None], blur, res)
    a = res[..., 3:4]
    res[..., :3] = np.where(a > 1e-4, res[..., :3] / np.maximum(a, 1e-4), 0)
    P = P.copy()
    P[y0:y1, x0:x1] = res.clip(0, 1)
    return P


def dilate(mask, r):
    m = mask.copy()
    for _ in range(r):
        n = m.copy()
        n[1:] |= m[:-1]
        n[:-1] |= m[1:]
        n[:, 1:] |= m[:, :-1]
        n[:, :-1] |= m[:, 1:]
        m = n
    return m


def prep_card(work, card, nested, plan_shot, big_skip=False):
    ver = card["ver"]
    ldir = os.path.join(work, "layers", ver)
    cdir = os.path.join(work, "cache", ver)
    os.makedirs(cdir, exist_ok=True)
    F = f32(Image.open(os.path.join(ldir, card["thumb"] + ".png")))
    Hh, Ww = F.shape[:2]
    C = f32(bg_image(card["bg"], Ww, Hh))
    place, worst = {}, []
    for L in card["layers"]:
        im = f32(Image.open(os.path.join(ldir, L["id"] + ".png")))
        bw_, bh_ = L["w"] * SC, L["h"] * SC
        if big_skip and im.shape[0] * im.shape[1] > 4 * bw_ * bh_:
            # 匯出圖比外框大很多（4800×4800 的放射背景）：搜尋要幾十萬個位置，直接置中在外框中心
            x = int(round(L["x"] * SC + (bw_ - im.shape[1]) / 2))
            y = int(round(L["y"] * SC + (bh_ - im.shape[0]) / 2))
            e = _after_err(C, F, im, x, y)
        else:
            x, y, e = locate(C, F, im, L["x"] * SC, L["y"] * SC, L["w"] * SC, L["h"] * SC)
        over_np(C, im, x, y)
        place[L["id"]] = [x, y, im.shape[1], im.shape[0], round(e, 4)]
        worst.append((e, L["id"], L["name"]))
    # 驗證：縮成縮圖尺寸再比（次像素反鋸齒差異會平均掉，擺錯位置才會留下）
    def box4(a):
        h4, w4 = a.shape[0] // 4 * 4, a.shape[1] // 4 * 4
        return a[:h4, :w4, :3].reshape(h4 // 4, 4, w4 // 4, 4, 3).mean((1, 3))
    diff = np.abs(box4(C) - box4(F)).sum(-1)
    stat = {"mean": float(diff.mean()), "p99": float(np.percentile(diff, 99)), "bad_px": int((diff > 0.25).sum())}
    # 框內字幕：在框圖裡定位、抹掉，另存乾淨版
    a = analyse_shot(plan_shot, card, nested) if plan_shot else {"split": {}}
    nest_place = {}
    for pid, hits in a["split"].items():
        P = f32(Image.open(os.path.join(ldir, pid + ".png")))
        px, py = place[pid][:2]
        L = next(l for l in card["layers"] if l["id"] == pid)
        mask = np.zeros(P.shape[:2], bool)
        for nd, i, j in hits:
            N = f32(Image.open(os.path.join(ldir, nd["id"] + ".png")))
            bx, by = (L["x"] + nd["ox"]) * SC - px, (L["y"] + nd["oy"]) * SC - py
            # 在框圖本身裡找（不受其他圖層遮擋）
            Pz = P.copy()
            Pz[..., :3] *= Pz[..., 3:4]
            x, y, e = locate(Pz, Pz, N, bx, by, nd["w"] * SC, nd["h"] * SC)
            nest_place[nd["id"]] = [px + x, py + y, N.shape[1], N.shape[0], round(e, 4)]
            nm = np.zeros(P.shape[:2], bool)
            h, w = N.shape[:2]
            ys0, xs0 = max(0, y), max(0, x)
            ys1, xs1 = min(P.shape[0], y + h), min(P.shape[1], x + w)
            if ys1 > ys0 and xs1 > xs0:
                nm[ys0:ys1, xs0:xs1] = N[ys0 - y:ys1 - y, xs0 - x:xs1 - x, 3] > 0.03
            mask |= dilate(nm, 3)
        Pc = inpaint(P, mask)
        Image.fromarray((Pc * 255).round().astype(np.uint8), "RGBA").save(os.path.join(cdir, pid + "_clean.png"))
    # 重組圖（驗證用）
    Image.fromarray((C * 255).round().astype(np.uint8), "RGBA").convert("RGB").resize((960, 540)).save(
        os.path.join(cdir, card["id"] + "_rebuild.jpg"), quality=85)
    worst.sort(reverse=True)
    return {"place": place, "nested": nest_place, "stat": stat, "worst": [w[:3] for w in worst[:3]]}


def _prep_one(a):
    work, card, nested, shot, big_skip = a
    return card["id"], prep_card(work, card, nested, shot, big_skip)


def cmd_prep(args):
    plan = parse_plan(args.plan)
    cards, nested = load_extract(args.work)
    shots = {s["id"]: s for v in plan.values() for s in v["shots"]}
    todo = [c for c in cards.values() if not args.vers or c["ver"] in args.vers]
    jobs = [(args.work, c, nested, shots.get(c["id"]), args.big_skip) for c in todo]
    res = {}
    with Pool(args.jobs) as pool:
        for cid, r in pool.imap_unordered(_prep_one, jobs):
            res[cid] = r
            st = r["stat"]
            flag = "  ⚠ 請看 cache/<版>/<鏡>_rebuild.jpg" if st["bad_px"] > 20 else ""
            print(f"{cid}: 重組差異（縮圖尺寸）平均 {st['mean']:.4f}  p99 {st['p99']:.3f}  明顯不同像素 {st['bad_px']}/129600{flag}", flush=True)
    for ver in sorted({c["ver"] for c in todo}):
        p = os.path.join(args.work, "cache", ver, "place.json")
        old = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
        old.update({cid: r for cid, r in res.items() if cid.startswith(ver)})
        json.dump(old, open(p, "w", encoding="utf-8"), ensure_ascii=False)


# ════════════════════════════════════════════════════════════════════════
# 字型與排字（PIL 補畫：縮圖沒畫到的字幕、計數數字、倒數數字、角色框）
# ════════════════════════════════════════════════════════════════════════
FONT_DIRS = []
SYS_FONTS = [r"C:/Windows/Fonts", os.path.expandvars(r"%LOCALAPPDATA%/Microsoft/Windows/Fonts")]
FAMILY_FILES = {   # family → [(檔名, 字重或 None＝可變字型)]
    "Noto Sans TC": [("NotoSansTC-VF.ttf", None)],
    "Noto Serif TC": [("NotoSerifTC-VF.ttf", None)],
    "Poppins": [("Poppins-Bold.ttf", 700)],
    "Barlow Condensed": [("BarlowCondensed-SemiBold.ttf", 600), ("BarlowCondensed-Bold.ttf", 700)],
    "Press Start 2P": [("PressStart2P-Regular.ttf", 400)],
    "DotGothic16": [("DotGothic16-Regular.ttf", 400)],
    "Limelight": [("Limelight-Regular.ttf", 400)],
    "VT323": [("VT323-Regular.ttf", 400)],
    "Huninn": [("Huninn-Regular.ttf", 400)],
    "Bungee": [("Bungee-Regular.ttf", 400)],
    "Iansui": [("Iansui-Regular.ttf", 400)],
    "Oswald": [("Oswald[wght].ttf", None)],
    "Orbitron": [("Orbitron[wght].ttf", None)],
    "Inter": [("Inter[opsz,wght].ttf", None)],
    "Fredoka": [("Fredoka[wdth,wght].ttf", None)],
    # 第二批（V11～V25）
    "LXGW WenKai TC": [("LXGWWenKaiTC-Bold.ttf", 700)],
    "Courier Prime": [("CourierPrime-Regular.ttf", 400), ("CourierPrime-Bold.ttf", 700)],
    "Chewy": [("Chewy-Regular.ttf", 400)],
    "Baloo 2": [("Baloo2[wght].ttf", None)],
    "Bangers": [("Bangers-Regular.ttf", 400)],
    "Special Elite": [("SpecialElite-Regular.ttf", 400)],
    "Sniglet": [("Sniglet-Regular.ttf", 400), ("Sniglet-ExtraBold.ttf", 800)],
    "Patrick Hand": [("PatrickHand-Regular.ttf", 400)],
    "Gochi Hand": [("GochiHand-Regular.ttf", 400)],
    "Cormorant Garamond": [("CormorantGaramond[wght].ttf", None)],
    "Cinzel": [("Cinzel[wght].ttf", None)],
    "Caveat": [("Caveat[wght].ttf", None)],
    "Segoe UI Symbol": [("seguisym.ttf", 400)],   # 補畫圖示用：🔔🔕🚕📷✦✕✓★♡♪（Windows 內建、單色）
}
FALLBACK = "Noto Sans TC"
_font_cache, _cmap_cache = {}, {}


def find_font_file(name):
    for d in FONT_DIRS + SYS_FONTS:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    return None


def wnum(w):
    if w in (None, "normal", "regular"):
        return 400
    if w == "bold":
        return 700
    try:
        return int(w)
    except Exception:
        return 400


def get_font(family, weight, size):
    """回傳 (ImageFont, 檔案路徑)；找不到字型時改用 Noto Sans TC。"""
    size = max(1, int(round(size)))
    w = wnum(weight)
    key = (family, w, size)
    if key in _font_cache:
        return _font_cache[key]
    cands = FAMILY_FILES.get(family) or FAMILY_FILES[FALLBACK]
    best = min(cands, key=lambda c: 0 if c[1] is None else abs(c[1] - w))
    path = find_font_file(best[0])
    if not path:
        if family != FALLBACK:
            print(f"⚠ 找不到字型 {family}（{best[0]}），改用 {FALLBACK}", file=sys.stderr)
            r = get_font(FALLBACK, weight, size)
            _font_cache[key] = r
            return r
        raise FileNotFoundError(best[0])
    f = ImageFont.truetype(path, size)
    if best[1] is None:
        try:
            axes = f.get_variation_axes()
            vals = []
            for ax in axes:
                nm = ax.get("name", b"")
                nm = nm.decode() if isinstance(nm, bytes) else str(nm)
                nm = nm.lower()
                if "weight" in nm or nm == "wght":
                    vals.append(max(ax["minimum"], min(ax["maximum"], w)))
                elif "optical" in nm or nm == "opsz":
                    vals.append(max(ax["minimum"], min(ax["maximum"], 14)))
                else:
                    vals.append(ax.get("default", ax["minimum"]))
            f.set_variation_by_axes(vals)
        except Exception as e:
            print(f"⚠ 可變字型設定失敗 {path}: {e}", file=sys.stderr)
    _font_cache[key] = (f, path)
    return _font_cache[key]


def has_glyph(path, ch):
    if path not in _cmap_cache:
        from fontTools.ttLib import TTFont
        _cmap_cache[path] = set(TTFont(path, lazy=True).getBestCmap().keys())
    return ord(ch) in _cmap_cache[path]


def shadow_spec(ef):
    if not ef:
        return None
    for e in (ef if isinstance(ef, list) else [ef]):
        if e.get("type") == "shadow" and e.get("shadowType", "outer") == "outer":
            o = e.get("offset") or {}
            return {"color": hex_rgba(e.get("color", "#00000080")), "blur": float(e.get("blur", 0) or 0),
                    "dx": float(o.get("x", 0)), "dy": float(o.get("y", 0))}
    return None


def render_text(text, style, box, k=SC * K):
    """依 Pencil 文字節點的樣式排字。box＝(x, y, w) 縮圖座標（文字框左上與寬）。
    回傳 dict：img（RGBA）、x、y（輸出座標左上）、glyphs（每字外框，img 內座標）、ink（輸出座標墨跡框）。"""
    fam, wt = style.get("f") or FALLBACK, style.get("w")
    fs = float(style.get("s") or 21) * k
    font, fpath = get_font(fam, wt, fs)
    fb, fbpath = get_font(FALLBACK, wt, fs)
    asc, desc = font.getmetrics()
    lh = style.get("lh")
    lineH = fs * lh if lh else (asc + desc)
    ls = float(style.get("ls") or 0) * k
    color = hex_rgba(style.get("c") or "#FFFFFF")
    align = style.get("a") or "left"
    lines = text.split("\n")
    bx, by, bw = box[0] * k, box[1] * k, (box[2] if box[2] else 0) * k
    laid = []
    for i, ln in enumerate(lines):
        items, x = [], 0.0
        for ch in ln:
            f, p = (font, fpath) if (ch == " " or has_glyph(fpath, ch)) else (fb, fbpath)
            adv = f.getlength(ch)
            items.append((ch, f, x, adv))
            x += adv + ls
        wline = x - ls if items else 0
        if align == "center" and bw:
            x0 = bx + (bw - wline) / 2
        elif align == "right" and bw:
            x0 = bx + bw - wline
        else:
            x0 = bx
        base = by + i * lineH + (lineH - (asc + desc)) / 2 + asc
        laid.append((items, x0, base))
    sh = shadow_spec(style.get("ef"))
    pad = int(fs * 0.6) + (int(sh["blur"] * k + abs(sh["dx"]) * k + abs(sh["dy"]) * k) + 4 if sh else 0)
    minx = min((x0 for _, x0, _ in laid), default=bx) - pad
    maxx = max((x0 + (it[-1][2] + it[-1][3] if it else 0) for it, x0, _ in laid), default=bx) + pad
    miny = by - pad
    maxy = by + len(lines) * lineH + pad
    W, H = int(math.ceil(maxx - minx)), int(math.ceil(maxy - miny))
    mask = Image.new("L", (max(1, W), max(1, H)), 0)
    d = ImageDraw.Draw(mask)
    glyphs = []
    for items, x0, base in laid:
        for ch, f, x, adv in items:
            gx, gy = x0 + x - minx, base - miny
            if ch.strip():
                d.text((gx, gy), ch, font=f, fill=255, anchor="ls")
                bb = f.getbbox(ch, anchor="ls")
                glyphs.append((int(gx + bb[0]), int(gy + bb[1]), int(math.ceil(gx + bb[2])), int(math.ceil(gy + bb[3]))))
    img = Image.new("RGBA", mask.size, color[:3] + (0,))
    a = np.asarray(mask, np.float32) * (color[3] / 255.0)
    img.putalpha(Image.fromarray(a.astype(np.uint8)))
    if sh:
        sm = mask
        if sh["blur"] > 0:
            sm = mask.filter(ImageFilter.GaussianBlur(sh["blur"] * k / 2))
        sa = np.asarray(sm, np.float32) * (sh["color"][3] / 255.0)
        simg = Image.new("RGBA", mask.size, sh["color"][:3] + (0,))
        simg.putalpha(Image.fromarray(sa.astype(np.uint8)))
        canvas = Image.new("RGBA", mask.size, (0, 0, 0, 0))
        canvas.alpha_composite(simg, (int(round(sh["dx"] * k)), int(round(sh["dy"] * k))))
        canvas.alpha_composite(img)
        img = canvas
    bb = mask.getbbox() or (0, 0, 1, 1)
    return {"img": img, "x": int(round(minx)), "y": int(round(miny)), "glyphs": glyphs,
            "ink": (minx + bb[0], miny + bb[1], minx + bb[2], miny + bb[3])}


def ink_box(img, x, y, thr=80):
    a = np.asarray(img.getchannel("A")) > thr
    ys, xs = np.nonzero(a)
    if len(ys) == 0:
        return None
    return (x + xs.min(), y + ys.min(), x + xs.max() + 1, y + ys.max() + 1)


def line_bands(img):
    """文字圖的各行上下界（以列空白切，太近的合併）。"""
    a = np.asarray(img.getchannel("A")) > 40
    rows = a.any(1)
    bands, y, H = [], 0, a.shape[0]
    while y < H:
        if rows[y]:
            y0 = y
            while y < H and rows[y]:
                y += 1
            bands.append([y0, y])
        y += 1
    if not bands:
        return []
    gap = max(3, int(0.25 * max(b[1] - b[0] for b in bands)))
    merged = [bands[0]]
    for b in bands[1:]:
        if b[0] - merged[-1][1] <= gap:
            merged[-1][1] = b[1]
        else:
            merged.append(b)
    hmax = max(b[1] - b[0] for b in merged)
    return [tuple(b) for b in merged if b[1] - b[0] >= 0.3 * hmax]


def luminance(rgb):
    def ch(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb[:3]
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast_color(thumb, box, color):
    """補畫字幕落在縮圖的哪個底色上；對比不足（< 3:1）就改成白字或深字。"""
    x0, y0 = max(0, int(box[0])), max(0, int(box[1]))
    x1, y1 = min(TH_W, int(box[0] + box[2])), min(TH_H, int(box[1] + box[3]))
    if x1 <= x0 or y1 <= y0:
        return color
    reg = np.asarray(thumb.crop((x0, y0, x1, y1)), np.float32).reshape(-1, 3)
    bgc = np.median(reg, 0)
    lb = luminance(bgc)
    lt = luminance(hex_rgba(color))
    ratio = (max(lb, lt) + 0.05) / (min(lb, lt) + 0.05)
    if ratio >= 3:
        return color
    return "#FFFFFF" if lb < 0.35 else "#2A2A2A"


def text_segments(img, text, style):
    """把一張文字圖切成逐字外框（逐字打字、單字彈跳用）。先以列空白切行，再依字寬比例切字。"""
    a = np.asarray(img.getchannel("A")) > 40
    rows = a.any(1)
    bands, y = [], 0
    H = a.shape[0]
    while y < H:
        if rows[y]:
            y0 = y
            while y < H and rows[y]:
                y += 1
            bands.append([y0, y])
        y += 1
    if not bands:
        return []
    # 合併太近的列（同一行字的上下部件）
    gap = max(3, int(0.25 * (bands[0][1] - bands[0][0])))
    merged = [bands[0]]
    for b in bands[1:]:
        if b[0] - merged[-1][1] <= gap:
            merged[-1][1] = b[1]
        else:
            merged.append(b)
    hmax = max(b[1] - b[0] for b in merged)
    merged = [b for b in merged if b[1] - b[0] >= 0.3 * hmax]
    lines = [ln for ln in text.split("\n") if ln.strip()]
    st = style or {}
    font, fpath = get_font(st.get("f") or FALLBACK, st.get("w"), 40)
    fb, _ = get_font(FALLBACK, st.get("w"), 40)

    def adv(ch):
        return (font if has_glyph(fpath, ch) or ch == " " else fb).getlength(ch)

    if len(merged) != len(lines):
        lines = ["".join(lines)] if len(merged) == 1 else lines
    segs = []
    if len(merged) == len(lines):
        pairs = list(zip(merged, lines))
    else:   # 對不上時整段平均分到各行
        allc = "".join(lines)
        n = len(merged)
        per = max(1, math.ceil(len(allc) / n))
        pairs = [(merged[i], allc[i * per:(i + 1) * per]) for i in range(n)]
    for (y0, y1), ln in pairs:
        cols = np.nonzero(a[y0:y1].any(0))[0]
        if len(cols) == 0 or not ln:
            continue
        x0, x1 = cols.min(), cols.max() + 1
        ws = [adv(c) for c in ln]
        tot = sum(ws) or 1
        acc = 0
        starts = []
        for c, w in zip(ln, ws):
            if c.strip():
                starts.append(x0 + (x1 - x0) * acc / tot)
            acc += w
        # 每段延伸到下一段開頭（空白分給前一個字），整行無縫，窄字不會落在空隙裡被漏畫
        for k, sx0 in enumerate(starts):
            sx1 = starts[k + 1] if k + 1 < len(starts) else x1
            segs.append((int(sx0) if k else int(x0), y0, int(math.ceil(sx1)), y1))
    return segs


# ════════════════════════════════════════════════════════════════════════
# 動態（時間軸）
# ════════════════════════════════════════════════════════════════════════
def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def smooth(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ease_out(x, p=3):
    x = clamp01(x)
    return 1 - (1 - x) ** p


def back_out(x):
    """0→1.1→1 的彈出。"""
    x = clamp01(x)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def bounce_out(x):
    x = clamp01(x)
    n1, d1 = 7.5625, 2.75
    if x < 1 / d1:
        return n1 * x * x
    if x < 2 / d1:
        x -= 1.5 / d1
        return n1 * x * x + 0.75
    if x < 2.5 / d1:
        x -= 2.25 / d1
        return n1 * x * x + 0.9375
    x -= 2.625 / d1
    return n1 * x * x + 0.984375


class Item:
    """畫面上的一個元素。座標一律是輸出像素；動態參數裡的距離是 1920 座標（乘 K）。"""
    def __init__(self, img, x, y, a=0.0, b=1e9, z=0.0, name="", kind="layer"):
        self.img, self.x, self.y = img, x, y
        self.a, self.b, self.z = a, b, z
        self.name, self.kind = name, kind
        self.fin = None          # 進場 dict
        self.fout = None         # 出場 dict
        self.loops = []
        self.reveal = None       # {"dir":…, "a":…, "b":…} 或 {"dir":…, "counter":True}
        self.move = None         # {"from":[dx,dy], "a":…, "b":…, "ease":…}
        self.segs = None
        self.style = None
        self.text = ""
        self.follow = None
        self.frames = None       # 依時間換圖（計數、倒數）：callable(t) → (img, x, y, extra)
        self.static = False
        self.screen = False      # True＝疊在畫面上、不跟鏡頭推拉平移（字幕）；False＝場景裡的東西
        self.front = False       # True＝畫在角色框前面（桌面、窗框）

    def visible_at(self, t):
        pre = 0
        return self.a - pre <= t <= self.b + (self.fout or {}).get("after", 0)


def seg_draw(canvas, img, segs, x, y, t, it):
    """逐字：type＝依序出現；bounce＝依序上彈落定。"""
    fin = it.fin
    n = len(segs)
    if n == 0:
        paste(canvas, img, x, y)
        return
    rate = fin.get("rate") or min(0.07, max(0.025, 0.5 * (it.b - it.a) / n))
    for i, (x0, y0, x1, y1) in enumerate(segs):
        ts = it.a + i * rate
        if t < ts:
            continue
        piece = img.crop((x0, y0, x1, y1))
        dy = 0
        if fin["fx"] == "bounce":
            p = (t - ts) / 0.32
            if p < 1:
                dy = -fin.get("dist", 24) * K * math.sin(math.pi * clamp01(p)) * (1 - 0.3 * p)
                piece = mul_alpha(piece, clamp01(p * 4))
        elif fin["fx"] == "beat":    # 逐字放大 130% 回彈（歌舞節拍跳字）
            p = (t - ts) / fin.get("cd", 0.3)
            if p < 1:
                s0 = fin.get("s0", 1.3)
                pw, ph = piece.size
                piece, ox, oy = transform(piece, s0 + (1 - s0) * back_out(p))
                piece = mul_alpha(piece, clamp01(p * 3))
                paste(canvas, piece, x + x0 + ox, int(round(y + y0 + oy)))
                continue
        elif fin.get("cf"):          # 逐字淡入（星光由暗到亮）
            piece = mul_alpha(piece, clamp01((t - ts) / fin["cf"]))
        paste(canvas, piece, x + x0, int(round(y + y0 + dy)))


def mul_alpha(img, m):
    if m >= 0.999:
        return img
    if m <= 0.001:
        return None
    a = img.getchannel("A").point(lambda v: int(v * m))
    out = img.copy()
    out.putalpha(a)
    return out


def paste(canvas, img, x, y):
    if img is None:
        return
    W, H = canvas.size
    w, h = img.size
    x, y = int(round(x)), int(round(y))
    if x >= W or y >= H or x + w <= 0 or y + h <= 0:
        return
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(w, W - x), min(h, H - y)
    if sx0 or sy0 or sx1 != w or sy1 != h:
        img = img.crop((sx0, sy0, sx1, sy1))
    canvas.alpha_composite(img, (x + sx0, y + sy0))


def transform(img, scale=1.0, sy=None, rot=0.0, sx=None):
    """以圖中心縮放／旋轉，回傳新圖與左上角位移。sx／sy 是額外的單軸倍率（翻開、翻牌）。"""
    w, h = img.size
    syy = scale if sy is None else scale * sy
    sx = scale if sx is None else scale * sx
    if abs(sx - 1) > 1e-3 or abs(syy - 1) > 1e-3:
        nw, nh = max(1, int(round(w * sx))), max(1, int(round(h * syy)))
        img = img.resize((nw, nh), Image.BILINEAR)
    if abs(rot) > 0.05:
        img = img.rotate(rot, resample=Image.BICUBIC, expand=True)
    nw, nh = img.size
    return img, (w - nw) / 2, (h - nh) / 2


def item_state(it, t, ctx):
    """回傳 (alpha, dx, dy, scale, sy, rot, reveal_frac, sx)；不可見回傳 None。"""
    if t < it.a or t > it.b:
        return None
    if getattr(it, "cidx", None) is not None:   # 依百分比逐格亮起
        if ctx.get("counter_frac", 0.0) < (it.cidx + 1) / it.cn - 1e-6:
            return None
    al, dx, dy, sc, sy, rot, sxx = 1.0, 0.0, 0.0, 1.0, None, 0.0, None
    fin = it.fin
    if fin and fin.get("fx") not in (None, "none", "type", "bounce", "beat"):
        d = fin.get("d", 0.3)
        ta = it.a + fin.get("delay", 0)
        if t < ta:
            return None
        p = (t - ta) / d if d > 0 else 1
        fx = fin["fx"]
        if p < 1:
            if fx == "fade":
                al *= smooth(p)
            elif fx == "pop":
                sc *= max(0.01, back_out(p))
                al *= clamp01(p * 3)
            elif fx == "slide":
                dist = fin.get("dist", 80) * K
                vx, vy = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}[fin.get("from", "down")]
                e = 1 - ease_out(p)
                dx += vx * dist * e
                dy += vy * dist * e
                al *= smooth(p * 1.5)
            elif fx == "drop":
                dist = fin.get("dist", 160) * K
                dy -= dist * (1 - bounce_out(p))
                al *= clamp01(p * 4)
            elif fx == "scale":
                s0 = fin.get("s0", 0.9)
                sc *= s0 + (1 - s0) * ease_out(p)
                al *= smooth(p)
            elif fx == "slam":
                s0 = fin.get("s0", 1.6)
                sc *= s0 + (1 - s0) * ease_out(p, 2)
                al *= clamp01(p * 3)
            elif fx == "flip":
                sy = max(0.02, ease_out(p))
                al *= clamp01(p * 3)
            elif fx == "flipx":
                sxx = max(0.02, ease_out(p))
                al *= clamp01(p * 3)
            elif fx == "wipe":
                pass
            elif fx == "blur":       # 模糊淡入（模糊量在 draw_item 依進度套）
                al *= smooth(p)
            elif fx == "squash":     # 黏土：先扁寬再回彈到原尺寸
                sy = max(0.05, back_out(p))
                sxx = 1 + fin.get("w0", 0.25) * (1 - ease_out(p))
                al *= clamp01(p * 4)
            elif fx == "burst":
                ox, oy = fin["origin"]
                e = 1 - ease_out(p)
                dx += (ox * K - it.x - it.img.width / 2) * e
                dy += (oy * K - it.y - it.img.height / 2) * e
                al *= clamp01(p * 4)
    fout = it.fout
    if fout and fout.get("fx") != "none" and it.b < ctx["dur"] + 5:
        d = fout.get("d", 0.2)
        p = (it.b - t) / d if d > 0 else 1
        if p < 1:
            if fout.get("fx") == "slide":
                dist = fout.get("dist", 80) * K
                vx, vy = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}[fout.get("to", "down")]
                dx += vx * dist * (1 - p)
                dy += vy * dist * (1 - p)
            al *= smooth(p)
    lt = t - it.a
    for lp in it.loops:
        fx = lp["fx"]
        if fx == "spin":   # 旋轉在 from～until 之間進行，之後停在當時的角度
            t0_ = lp.get("from", it.a)
            te = min(t, lp.get("until", 1e9))
            if te > t0_:
                rot -= lp.get("dps", 360) * (te - t0_)
            continue
        if "from" in lp and t < lp["from"]:
            continue
        if "until" in lp and t > lp["until"]:
            continue
        per = lp.get("period", 1.0)
        ph = lp.get("phase", 0) + it.z * lp.get("zphase", 0)
        if fx == "blink":
            mn = lp.get("min", 0.3)
            on = ((t / per + ph) % 1.0) < lp.get("duty", 0.5)
            al *= 1.0 if on else mn
        elif fx == "glow":
            mn = lp.get("min", 0.4)
            al *= mn + (1 - mn) * (0.5 + 0.5 * math.cos(2 * math.pi * (t / per + ph)))
        elif fx == "pulse":
            sc *= 1 + lp.get("amp", 0.05) * math.sin(2 * math.pi * (t / per + ph))
        elif fx == "float":
            dy += lp.get("amp", 6) * K * math.sin(2 * math.pi * (t / per + ph))
        elif fx == "hfloat":
            dx += lp.get("amp", 6) * K * math.sin(2 * math.pi * (t / per + ph))
        elif fx == "sway":
            rot += lp.get("deg", 8) * math.sin(2 * math.pi * (t / per + ph))
        elif fx == "drift":
            dx += lp.get("vx", 0) * K * lt
            dy += lp.get("vy", 0) * K * lt
        elif fx == "fall":   # 重力落下（紙花）
            g = lp.get("g", 300)
            dy += 0.5 * g * K * max(0, lt - lp.get("after", 0)) ** 2
        elif fx == "shake":
            for ts in lp.get("times", []):
                if ts <= t < ts + lp.get("d", 0.3):
                    q = 1 - (t - ts) / lp.get("d", 0.3)
                    amp = lp.get("amp", 8) * K * q
                    dx += amp * math.sin(t * 90)
                    dy += amp * 0.5 * math.cos(t * 70)
        elif fx == "jitter":  # 蠟筆線條抖動：每 period 秒換一個隨機小位移
            n = int(t / per)
            r1 = math.sin(n * 12.9898 + it.z * 78.233) * 43758.5453
            r2 = math.sin(n * 39.3468 + it.z * 11.135) * 24634.6345
            amp = lp.get("amp", 2) * K
            dx += amp * (2 * (r1 - math.floor(r1)) - 1)
            dy += amp * (2 * (r2 - math.floor(r2)) - 1)
        elif fx == "steps":   # 階梯式位移（像素雲）
            n = int(t / per)
            dx += lp.get("vx", 0) * K * n
            dy += lp.get("vy", 0) * K * n
        elif fx == "gauge":   # 指針：依百分比從 deg0 轉到 deg1（逆時針為正）
            f = ctx.get("counter_frac", 1.0)
            rot += lp.get("deg0", 180) + (lp.get("deg1", 0) - lp.get("deg0", 180)) * f
    if it.move:
        mv = it.move
        p = clamp01((t - mv["a"]) / max(1e-6, mv["b"] - mv["a"]))
        if mv.get("ease") == "counter":
            e = ctx.get("counter_frac", 1.0) if t < mv["b"] else 1.0
        else:
            e = {"lin": p, "out": ease_out(p), "in": p ** 2.2, "smooth": smooth(p)}[mv.get("ease", "smooth")]
        fx_, fy_ = mv.get("from", [0, 0])
        tx_, ty_ = mv.get("to", [0, 0])
        dx += (fx_ + (tx_ - fx_) * e) * K
        dy += (fy_ + (ty_ - fy_) * e) * K
    if it.follow:
        st = ctx["chars"].get(it.follow, {}).get("state")
        if st is None:
            return None
        al *= st[0]
        dx += st[1]
        dy += st[2]
    an = getattr(it, "anchor", None)
    if an:   # 黏在角色框上（框的左上或左下＋位移，縮圖座標），例：新娘框下緣的禮服粉標示
        c = ctx["chars"].get(an["who"])
        if c is None:
            return None
        cal, cx_, cy_, cw_, ch_, _ = c["box"]
        al *= cal
        dx += (cx_ + an.get("dx", 0)) * SC * K - it.x
        dy += (cy_ + (ch_ if an.get("ay") == "bottom" else 0) + an.get("dy", 0)) * SC * K - it.y
    frac = None
    if it.reveal:
        rv = it.reveal
        if rv.get("counter"):
            frac = ctx.get("counter_frac", 1.0) if t < ctx.get("counter_end", 1e9) else 1.0
        elif rv.get("period"):   # 循環掃描（倒數環、膠卷扇形）
            ra = rv.get("a", 0)
            if rv.get("until") is not None and t >= rv["until"]:
                frac = 1.0
            else:
                frac = ((t - ra) % rv["period"]) / rv["period"] if t >= ra else 1.0
                if rv.get("shrink"):
                    frac = 1 - frac
        else:
            frac = ease_out((t - rv["a"]) / max(1e-6, rv["b"] - rv["a"]), rv.get("p", 2)) if t < rv["b"] else 1.0
            if t < rv["a"]:
                frac = 0.0
        if "steps" in rv and frac is not None:
            frac = math.floor(frac * rv["steps"] + 1e-6) / rv["steps"]
    elif fin and fin.get("fx") == "wipe":
        d = fin.get("d", 0.5)
        frac = clamp01((t - it.a - fin.get("delay", 0)) / d)
    if al <= 0.003:
        return None
    return al, dx, dy, sc, sy, rot, frac, sxx


def apply_reveal(img, frac, direction):
    if frac is None or frac >= 0.999:
        return img
    if frac <= 0.001:
        return None
    w, h = img.size
    a = np.asarray(img.getchannel("A")).copy()
    if direction == "l2r":
        a[:, int(w * frac):] = 0
    elif direction == "r2l":
        a[:, :int(w * (1 - frac))] = 0
    elif direction == "b2t":
        a[:int(h * (1 - frac)), :] = 0
    elif direction == "t2b":
        a[int(h * frac):, :] = 0
    elif direction == "cw":     # 從 12 點鐘方向順時針
        yy, xx = np.mgrid[0:h, 0:w]
        ang = (np.degrees(np.arctan2(xx - w / 2, -(yy - h / 2))) + 360) % 360
        a[ang > 360 * frac] = 0
    elif direction == "iris":   # 從中心往外的圓形（虹膜打開）
        yy, xx = np.mgrid[0:h, 0:w]
        a[np.hypot(xx - w / 2, yy - h / 2) > frac * math.hypot(w, h) / 2] = 0
    out = img.copy()
    out.putalpha(Image.fromarray(a))
    return out


def draw_item(canvas, it, t, ctx, off=(0, 0)):
    """off＝畫到「世界畫布」（比畫面大、四周有延伸區）時，縮圖原點在畫布上的位置。"""
    if it.frames:
        r = it.frames(t)
        if r is None:
            return
        img, x, y = r
    else:
        img, x, y = it.img, it.x, it.y
    stt = item_state(it, t, ctx)
    if stt is None:
        return
    al, dx, dy, sc, sy, rot, frac, sxx = stt
    if off != (0, 0):
        dx, dy = dx + off[0], dy + off[1]
    if it.fin and it.fin.get("fx") in ("type", "bounce", "beat") and it.segs is not None:
        im = mul_alpha(img, al)
        if im is not None:
            seg_draw(canvas, im, it.segs, x + dx, y + dy, t, it)
        return
    if it.fin and it.fin.get("fx") == "blur":
        pb = (t - it.a - it.fin.get("delay", 0)) / it.fin.get("d", 0.6)
        if 0 <= pb < 1:
            r_ = it.fin.get("r0", 8) * K * (1 - smooth(pb))
            if r_ > 0.3:
                pad_ = int(r_ * 3) + 2
                big = Image.new("RGBA", (img.width + 2 * pad_, img.height + 2 * pad_), (0, 0, 0, 0))
                big.paste(img, (pad_, pad_))
                img, x, y = big.filter(ImageFilter.GaussianBlur(r_)), x - pad_, y - pad_
    if frac is not None:
        img = apply_reveal(img, frac, (it.reveal or {}).get("dir", "l2r"))
        if img is None:
            return
    if sc != 1.0 or sy is not None or sxx is not None or rot:
        piv = getattr(it, "pivot", None)
        img2, ox, oy = transform(img, sc, sy, rot, sxx)
        if piv and rot:
            # 繞指定點旋轉：先算圖中心相對 pivot 的位移
            cx, cy = x + img.width / 2, y + img.height / 2
            px, py = piv[0] * K, piv[1] * K
            r_ = math.radians(-rot)
            vx, vy = cx - px, cy - py
            ncx = px + vx * math.cos(r_) - vy * math.sin(r_)
            ncy = py + vx * math.sin(r_) + vy * math.cos(r_)
            ox += ncx - cx
            oy += ncy - cy
        img, x, y = img2, x + ox, y + oy
    img = mul_alpha(img, al)
    paste(canvas, img, x + dx, y + dy)


# ════════════════════════════════════════════════════════════════════════
# 每一鏡的元素建構
# ════════════════════════════════════════════════════════════════════════
def load_layer(work, ver, lid, clean=False, unfade_op=None):
    p = os.path.join(work, "cache", ver, lid + "_clean.png") if clean else os.path.join(work, "layers", ver, lid + ".png")
    im = Image.open(p).convert("RGBA")
    if unfade_op and unfade_op < 0.999:
        a = np.asarray(im.getchannel("A"), np.float32) / unfade_op
        im.putalpha(Image.fromarray(a.clip(0, 255).astype(np.uint8)))
    return im


def to_out(im, x, y):
    """1920 座標的圖與位置 → 輸出尺寸。"""
    w, h = max(1, int(round(im.width * K))), max(1, int(round(im.height * K)))
    return im.resize((w, h), Image.LANCZOS), int(round(x * K)), int(round(y * K))


def rule_match(rule, L):
    m = rule.get("match")
    if not m:
        return False
    if m.startswith("id:"):
        return L["id"] in m[3:].split(",")
    if re.search(m, L["name"]) is None:
        return False
    if "within" in rule and "x" in L:   # 只套用到外框中心落在 [x0, y0, x1, y1]（縮圖座標）裡的圖層
        x0, y0, x1, y1 = rule["within"]
        cx, cy = L["x"] + L["w"] / 2, L["y"] + L["h"] / 2
        return x0 <= cx <= x1 and y0 <= cy <= y1
    return True


def apply_rule(it, r, ctx):
    if "show" in r:
        it.a, it.b = r["show"][0], r["show"][1]
        it.static = False
        if it.fin is None and it.a > 0.01:
            it.fin = {"fx": "fade", "d": 0.3}
        if it.fout is None and it.b < ctx["dur"] - 0.01:
            it.fout = {"fx": "fade", "d": 0.25}
    if "in" in r:
        it.fin = dict(r["in"])
        it.static = False
    if "out" in r:
        it.fout = dict(r["out"])
    if "loop" in r:
        it.loops = it.loops + [dict(x) for x in r["loop"]]
        it.static = False
    if "reveal" in r:
        it.reveal = dict(r["reveal"])
        it.static = False
    if "move" in r:
        it.move = dict(r["move"])
        it.static = False
    if "follow" in r:
        it.follow = r["follow"]
        it.static = False
    if "anchor" in r:
        it.anchor = r["anchor"]
        it.static = False
    if "pivot" in r:
        it.pivot = r["pivot"]
    if "screen" in r:
        it.screen = bool(r["screen"])
    if r.get("front"):
        it.front = True
    if r.get("static_fade") is False and it.fin and it.fin.get("auto"):
        it.fin = None


def box_of(card, nested_by_id, lid):
    for L in card["layers"]:
        if L["id"] == lid:
            return (L["x"], L["y"], L["w"], L["h"])
    nd = nested_by_id.get(lid)
    if nd:
        P = next(l for l in card["layers"] if l["id"] == nd["top"])
        return (P["x"] + nd["ox"], P["y"] + nd["oy"], nd["w"], nd["h"])
    return None


def style_of(card, nested, nested_by_id, lid):
    for L in card["layers"]:
        if L["id"] == lid:
            if L["style"]:
                return L["style"]
            kids = [n for n in nested.get(lid, []) if (n["style"].get("s") or 0) >= NESTED_MIN_SIZE]
            return kids[0]["style"] if kids else None
    nd = nested_by_id.get(lid)
    return nd["style"] if nd else None


def union(boxes):
    x0 = min(b[0] for b in boxes)
    y0 = min(b[1] for b in boxes)
    x1 = max(b[0] + b[2] for b in boxes)
    y1 = max(b[1] + b[3] for b in boxes)
    return (x0, y0, x1 - x0, y1 - y0)


def char_color(work, ver, card):
    for L in card["layers"]:
        if is_char_box(L):
            im = np.asarray(Image.open(os.path.join(work, "layers", ver, L["id"] + ".png")).convert("RGBA"))
            h = im.shape[0]
            col = im[h // 2, :8]
            i = int(np.argmax(col[:, 3] * (np.abs(col[:, :3].astype(int) - 255).sum(1) + 1)))
            return tuple(int(v) for v in col[i, :3]) + (255,)
    return (120, 120, 120, 255)


_box_cache = {}


def char_box_img(label, w, h, color):
    """角色佔位框（照縮圖畫法）：白 70% 底、1px 主色框、圓角 6、框內 11/700 字。先以 1920 座標畫再縮。"""
    key = (label, round(w, 2), round(h, 2), color)
    if key in _box_cache:
        return _box_cache[key]
    s = SC
    W, H = int(round(w * s)), int(round(h * s))
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=6 * s, fill=(255, 255, 255, 179), outline=color, width=s)
    font, _ = get_font("Noto Sans TC", 700, 11 * s)
    # 折行：英數單字不拆、中文逐字（與縮圖的排法一致）
    maxw = W - 2 * 3 * s
    lines, cur = [], ""
    for tok in re.findall(r"[A-Za-z0-9]+|\s|.", label):
        if tok == " " and not cur:
            continue
        if font.getlength(cur + tok) > maxw and cur.strip():
            lines.append(cur.rstrip())
            cur = tok.strip()
            while font.getlength(cur) > maxw and len(cur) > 1:   # 單字本身太長才拆
                k = len(cur)
                while k > 1 and font.getlength(cur[:k]) > maxw:
                    k -= 1
                lines.append(cur[:k])
                cur = cur[k:]
        else:
            cur += tok
    if cur:
        lines.append(cur)
    asc, desc = font.getmetrics()
    lh = asc + desc
    y = (H - lh * len(lines)) / 2
    for ln in lines:
        lw = font.getlength(ln)
        d.text(((W - lw) / 2, y + asc), ln, font=font, fill=(0x33, 0x29, 0x2C, 255), anchor="ls")
        y += lh
    out = im.resize((max(1, int(round(W * K))), max(1, int(round(H * K)))), Image.LANCZOS)
    _box_cache[key] = out
    return out


def char_geom(pos, hfrac):
    col, row = POS9.get(pos, (0, 2))
    h = TH_H * hfrac
    w = h * 0.35
    x = [24, TH_W / 2 - w / 2, TH_W - 24 - w][col]
    y = [0, (TH_H - h) / 2, TH_H - h][row]
    return x, y, w, h


def pair_x(pos, w, side, gap=6):
    """兩人寫在同一格位置時並排：整組放在單人框會在的位置，新郎在左（side<0）、新娘在右。"""
    col = POS9.get(pos, (0, 2))[0]
    bx = [24, TH_W / 2 - w - gap / 2, TH_W - 24 - 2 * w - gap][col]
    return bx if side < 0 else bx + w + gap


def build_chars(shot, color, dur, pair=False, boxes=None):
    """回傳每個角色的出場區段：[{segs:[…], a, b, enter}]。間隔 ≤ 1 秒的相鄰動作視為連續在場。
    pair＝True 時，同一時段寫在同一格位置的兩個角色並排（縮圖就是這樣畫的），不然兩個框會疊在一起；
    兩人從不同位置走到同一格時，終點也並排（pair_to）。
    boxes＝{"新郎": [x, y, w, h]}：角色框改放在指定位置（拍立得、窗戶、漫畫格裡），不照九宮格。"""
    if pair:
        cs = shot["chars"]
        for c in cs:
            c["pair"] = c["pair_to"] = 0
        for i, c1 in enumerate(cs):
            for c2 in cs[i + 1:]:
                if c1["who"] == c2["who"] or min(c1["t1"], c2["t1"]) - max(c1["t0"], c2["t0"]) <= 0.05:
                    continue
                left = c1 if c1["who"] == "新郎" or c2["who"] == "新娘" else c2
                if c1["from"] == c2["from"] and c1["to"] == c2["to"]:
                    for c in (c1, c2):
                        c["pair"] = -1 if c is left else 1
                elif c1["to"] == c2["to"]:
                    for c in (c1, c2):
                        c["pair_to"] = -1 if c is left else 1
    for c in shot["chars"]:
        if boxes and c["who"] in boxes:
            c["box"] = boxes[c["who"]]
    by = {}
    for c in shot["chars"]:
        by.setdefault(c["who"], []).append(c)
    spans = {}
    for who, segs in by.items():
        segs.sort(key=lambda c: c["t0"])
        out = []
        for s in segs:
            if out and s["t0"] - out[-1]["b"] <= 1.0:
                out[-1]["segs"].append(s)
                out[-1]["b"] = max(out[-1]["b"], s["t1"])
            else:
                out.append({"segs": [s], "a": s["t0"], "b": s["t1"], "enter": s["enter"]})
        for sp in out:
            if dur - sp["b"] <= 0.35:
                sp["b"] = dur + 1.0
        spans[who] = out
    return spans


def char_state(spans, who, t, base_xy=None):
    """回傳 (alpha, x, y, w, h, label) 輸出座標；不在場回傳 None。"""
    for sp in spans.get(who, []):
        if not (sp["a"] <= t <= sp["b"]):
            continue
        segs = sp["segs"]
        cur = segs[0]
        for s in segs:
            if s["t0"] <= t:
                cur = s
        hh = cur["h"]
        if cur.get("h1", hh) != hh:   # 走近／走遠：高度在本段時間內線性變化
            hh = hh + (cur["h1"] - hh) * clamp01((t - cur["t0"]) / max(1e-6, cur["t1"] - cur["t0"]))
        x0, y0, w, h = char_geom(cur["from"], hh)
        if cur.get("pair"):
            x0 = pair_x(cur["from"], w, cur["pair"])
        if cur.get("box"):
            x0, y0, w, h = cur["box"]
            x, y = x0, y0
        elif cur["move"]:
            x1, y1, _, _ = char_geom(cur["to"], hh)
            if cur.get("pair") or cur.get("pair_to"):
                x1 = pair_x(cur["to"], w, cur.get("pair") or cur["pair_to"])
            p = smooth((t - cur["t0"]) / max(1e-6, cur["t1"] - cur["t0"]))
            x, y = x0 + (x1 - x0) * p, y0 + (y1 - y0) * p
        else:
            x, y = x0, y0
        al = 1.0
        kind, d = sp["enter"]
        p = (t - sp["a"]) / d if d > 0 else 1
        if p < 1:
            if kind == "fade":
                al *= smooth(p)
            elif kind == "slide":
                col = POS9.get(segs[0]["from"], (0, 2))[0]
                off = [-(x + w + 4), 0, TH_W - x + 4][col]
                offy = (TH_H - y) if col == 1 else 0
                e = 1 - ease_out(p)
                x += off * e
                y += offy * e
        q = (sp["b"] - t) / 0.3
        if q < 1:
            al *= smooth(q)
        label = f"{who} {cur['act']}" + (f" →{cur['to']}" if cur["move"] else "")
        return al, x, y, w, h, label
    return None


def counter_value(t, a, b, jump, vals):
    """0→99 先快後慢、停在 99（抖兩下）、jump 時跳到最後值。回傳 (字串, 抖動, 進度比例)。"""
    last = vals[-1]
    pct = last.endswith("%")
    lastn = int(last.rstrip("%"))
    t99 = jump - 0.8
    if t < a:
        v = 0
    elif t < t99:
        v = int(round((lastn - 1) * ease_out((t - a) / max(1e-6, t99 - a), 2.2)))
    elif t < jump:
        v = lastn - 1
    else:
        v = lastn
    jit = 0.0
    if t99 <= t < jump:
        q = (t - t99) / 0.8
        if q < 0.25 or 0.5 <= q < 0.75:
            jit = math.sin(q * math.pi * 16) * 5
    s = f"{v}%" if pct else str(v)
    return s, jit, v / float(lastn)


def default_sub_style(cards, nested, ver, analyses):
    """該版最常見的字幕樣式（給沒有可借位置的補畫字幕用）。"""
    cnt = {}
    for cid, (card, a, shot) in analyses.items():
        if card["ver"] != ver:
            continue
        for L in card["layers"]:
            r = a["roles"].get(L["id"], {})
            if r.get("role") == "sub" and L["style"] and shot["subs"][r["sub"]]["kind"] == "sub" \
                    and (L["style"].get("s") or 0) >= 18:   # 卡片上的小介紹字不算字幕樣式
                st = L["style"]
                k = json.dumps({x: st.get(x) for x in ("f", "w", "s", "c", "lh", "ef")}, sort_keys=True)
                cnt[k] = cnt.get(k, 0) + 1
    if not cnt:
        return {"f": FALLBACK, "w": "700", "s": 21, "c": "#FFFFFF", "lh": 1.3}
    st = json.loads(max(cnt, key=cnt.get))
    st["a"] = "center"
    return st


def pick_rules(rules, ver, sid):
    vr = (rules or {}).get(ver, {})
    return vr, vr.get("shots", {}).get(sid, {})


def calib(ref_img, rx, ry, rendered):
    """PIL 排字與 Pencil 匯出圖的偏移校正（以墨跡框比較：水平中心、上緣）。"""
    rb = ink_box(ref_img, rx, ry)
    mb = rendered["ink"]
    if not rb:
        return 0, 0
    return ((rb[0] + rb[2]) / 2 - (mb[0] + mb[2]) / 2), (rb[1] - mb[1])


def arc_img(ex):
    """照 Pencil ellipse 的參數畫環形扇區（縮圖座標）：center、r_out、inner（內徑比）、a0、sweep（逆時針度數）、color、glow。"""
    s = SC
    cx, cy = ex["center"]
    ro = ex["r_out"]
    ri = ro * ex.get("inner", 0.72)
    pad = int(ex.get("glow", 0) * 2 + 4)
    W = int((2 * ro + 2 * pad) * s)
    mask = Image.new("L", (W, W), 0)
    d = ImageDraw.Draw(mask)
    c = W / 2
    a0, a1 = ex.get("a0", 0), ex.get("a0", 0) + ex["sweep"]
    d.pieslice([c - ro * s, c - ro * s, c + ro * s, c + ro * s], -a1, -a0, fill=255)
    d.ellipse([c - ri * s, c - ri * s, c + ri * s, c + ri * s], fill=0)
    col = hex_rgba(ex["color"])
    out = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    if ex.get("glow"):
        g = mask.filter(ImageFilter.GaussianBlur(ex["glow"] * s / 2))
        gi = Image.new("RGBA", (W, W), col[:3] + (0,))
        gi.putalpha(g)
        out.alpha_composite(gi)
    body = Image.new("RGBA", (W, W), col[:3] + (0,))
    body.putalpha(Image.fromarray((np.asarray(mask, np.float32) * col[3] / 255).astype(np.uint8)))
    out.alpha_composite(body)
    return to_out(out, (cx - ro - pad) * s, (cy - ro - pad) * s)


def build_shot(work, ver, shot, card, nested, place, rules, dstyle, prev_trans, color):
    vr, sr = pick_rules(rules, ver, shot["id"])
    dur = shot["dur"]
    ctx = {"dur": dur}
    a = analyse_shot(shot, card, nested)
    nested_by_id = {n["id"]: n for lst in nested.values() for n in lst}
    pl = place.get(card["id"])
    if pl is None:
        raise RuntimeError(f"{card['id']} 沒有定位結果，請先跑 prep")
    entering_cut = prev_trans is None or prev_trans["type"] == "cut"
    thumb_img = Image.open(os.path.join(work, "layers", ver, card["thumb"] + ".png")).convert("RGB").resize((TH_W, TH_H))
    items = []
    z = 0
    sub_items = {}       # 句索引 → [Item]
    counter_ref = {}     # 句索引 → (ref_img, x, y, style, box)
    subs = shot["subs"]
    layer_rules = sr.get("layers", [])

    def new_static(img, x, y, name):
        it = Item(img, x, y, 0, dur + 5, z, name)
        it.static = True
        if entering_cut and not sr.get("no_static_fade"):
            it.fin = {"fx": "fade", "d": 0.3, "auto": True}
        return it

    def sub_fx(i):
        s = subs[i]
        for rr in sr.get("subs", []):
            if re.search(rr["match"], s["text"]) and "in" in rr:
                return dict(rr["in"])
        key = {"sub": "sub_in", "big": "big_in", "label": "label_in"}[s["kind"]]
        if s.get("scene"):   # 場景字：可另設預設進場（寫在物件上、布條滾落…）
            skey = "scene_big_in" if s["kind"] == "big" else "scene_in"
            if skey in vr:
                return dict(vr[skey])
        if key in vr:
            return dict(vr[key])
        return {"fx": "fade", "d": 0.3} if s["kind"] == "sub" else {"fx": "pop", "d": 0.35}

    def make_sub_item(img, x, y, i, name, text, style, lid=None):
        s = subs[i]
        it = Item(img, x, y, s["t0"], s["t1"], z, name, "sub")
        it._lid = lid
        it.fin = sub_fx(i)
        it.fout = {"fx": "fade", "d": 0.2}
        it.text, it.style = text, style
        it.screen = not s.get("scene")
        if it.fin.get("fx") in ("type", "bounce", "beat"):
            it.segs = text_segments(img, text, style)
        for rr in sr.get("subs", []):
            if re.search(rr["match"], s["text"]):
                if "loop" in rr:
                    it.loops += [dict(q) for q in rr["loop"]]
                if "show" in rr:
                    it.a, it.b = rr["show"]
                if "world" in rr:
                    it.screen = not rr["world"]
                if rr.get("front"):
                    it.front = True
                if "out" in rr:
                    it.fout = dict(rr["out"])
                if "move" in rr:
                    it.move = dict(rr["move"])
        sub_items.setdefault(i, []).append(it)
        return it

    rule_hits = {}
    cr_all = sr.get("counter", {})
    z_names = {}
    # 計數／倒數借縮圖上的文字圖層當位置與字型（縮圖寫成「99% → 100%」或每個數字各一個物件時）
    cslot = cr_all.get("slot")
    cslots = [q for q in cr_all.get("slots", []) if isinstance(q, str)]
    ci_first = next((i for i, s in enumerate(subs) if counter_values(s["text"])), None)
    slot_refs = {}
    for L in card["layers"]:
        z += 1
        z_names[L["name"]] = z
        role = a["roles"].get(L["id"], {"role": "static"})
        if role["role"] == "char":
            continue
        if ci_first is not None and (L["id"] == cslot or L["id"] in cslots):
            x, y, w, h = pl["place"][L["id"]][:4]
            img, ox, oy = to_out(load_layer(work, ver, L["id"], False, L["op"]), x, y)
            rec = (img, ox, oy, L["style"], (L["x"], L["y"], L["w"]), L["text"], z)
            if L["id"] == cslot:
                counter_ref[ci_first] = rec
            else:
                slot_refs[L["id"]] = rec
            continue
        if role["role"] == "counter" and cr_all.get("layer") is False:
            role = {"role": "static"}
        rl = []
        for k_, r in enumerate(layer_rules):
            if rule_match(r, L):
                idx = rule_hits.get(k_, 0)
                rule_hits[k_] = idx + 1
                if "nth" in r and r["nth"] != idx:
                    continue
                rl.append(r)
        if any(r.get("hide") for r in rl):
            continue
        x, y, w, h = pl["place"][L["id"]][:4]
        unf = L["op"] if (role["role"] in ("sub", "counter", "lines") or any(r.get("unfade") for r in rl)) else None
        noclean = any(r.get("noclean") for r in rl)   # 框裡的字保留在原圖上（不拆出來另外疊）
        clean = L["id"] in a["split"] and not noclean
        raw = load_layer(work, ver, L["id"], clean, unf)
        img, ox, oy = to_out(raw, x, y)
        if role["role"] == "counter":
            counter_ref[role["sub"]] = (img, ox, oy, L["style"], (L["x"], L["y"], L["w"]), L["text"], z)
            continue
        if role["role"] == "lines":
            # 依行切開，每行各自照自己那句的時段
            bands = line_bands(img)
            lines = [ln for ln in L["text"].split("\n") if ln.strip()]
            if len(bands) == len(lines):
                for (y0, y1), ln, si in zip(bands, lines, role["subs"]):
                    p0, p1 = max(0, y0 - 3), min(img.height, y1 + 3)
                    it = make_sub_item(img.crop((0, p0, img.width, p1)), ox, oy + p0, si, L["name"], ln, L["style"], L["id"])
                    for r in rl:
                        apply_rule(it, r, ctx)
                    items.append(it)
                continue
            role = {"role": "sub", "sub": role["subs"][0]}
            subs[role["sub"]]["t1"] = max(subs[q]["t1"] for q in a["roles"][L["id"]]["subs"])
        if role["role"] == "sub":
            st = style_of(card, nested, nested_by_id, L["id"])
            text = L["text"].replace("‖", "\n") if L["type"] != "x" else L["text"]
            it = make_sub_item(img, ox, oy, role["sub"], L["name"], text, st, L["id"])
        else:
            it = new_static(img, ox, oy, L["name"])
        for r in rl:
            apply_rule(it, r, ctx)
        items.append(it)
        # 框內拆出的字
        for nd, si, part in ([] if noclean else a["split"].get(L["id"], [])):
            z += 0.01
            nx, ny = pl["nested"][nd["id"]][:2]
            nraw = load_layer(work, ver, nd["id"], False, None)
            nimg, nox, noy = to_out(nraw, nx, ny)
            if part == "counter":
                counter_ref[si] = (nimg, nox, noy, nd["style"], (L["x"] + nd["ox"], L["y"] + nd["oy"], nd["w"]), nd["text"], z)
                continue
            nit = make_sub_item(nimg, nox, noy, si, nd["name"], nd["text"], nd["style"], nd["id"])
            for r in [r for r in layer_rules if rule_match(r, {"id": nd["id"], "name": nd["name"]})]:
                apply_rule(nit, r, ctx)
            items.append(nit)

    # ── 縮圖沒有的字幕：借同鏡、時段不重疊的字幕位置，否則用預設位置 ──
    z_sub = z + 1
    for i in a["missing"]:
        s = subs[i]
        if counter_values(s["text"]):
            continue
        rr = next((r for r in sr.get("subs", []) if re.search(r["match"], s["text"])), {})
        if rr.get("hide"):   # 字已經用別的方式畫在畫面上（例：一個個黏土字物件），不補畫
            continue
        box, style, ref = None, None, None
        if "slot" in rr:
            ids = rr["slot"]
            box = union([box_of(card, nested_by_id, q) for q in ids])
            style = style_of(card, nested, nested_by_id, ids[0])
            ref = ids[0]
        elif "box" in rr:
            box = tuple(rr["box"])
        else:
            best = None
            for j, s2 in enumerate(subs):
                if j == i or j not in a["used"] or counter_values(s2["text"]):
                    continue
                if s2["kind"] != s["kind"] and not (s["kind"] == "sub" and s2["kind"] == "sub"):
                    continue
                ov = min(s["t1"], s2["t1"]) - max(s["t0"], s2["t0"])
                if ov > 0.05:
                    continue
                ids = a["used"][j]
                st = style_of(card, nested, nested_by_id, ids[0])
                if st is None or (s["kind"] == "sub" and (st.get("s") or 0) < 16):
                    continue
                gap = max(s2["t0"] - s["t1"], s["t0"] - s2["t1"])
                if best is None or gap < best[0]:
                    best = (gap, ids, st)
            if best:
                box = union([box_of(card, nested_by_id, q) for q in best[1]])
                style = best[2]
                ref = best[1][0]
        if style is None:
            style = dict(dstyle)
        style = dict(style)
        style.update(rr.get("style", {}))
        if box is None:
            nl = len(s["parts"])
            lh = style.get("lh") or 1.45
            bh = nl * style.get("s", 21) * lh
            db = vr.get("sub_default_box", [40, None, 400, None])
            box = (db[0], (db[1] if db[1] is not None else 255 - bh), db[2], bh)
        if not style.get("a"):
            style["a"] = "left" if ref else "center"   # Pencil 文字預設靠左；沒有借位時才置中
        # 某一行比框還寬時縮小字級（最多到 75%），不讓字超出借來的位置
        font, fpath_ = get_font(style.get("f") or FALLBACK, style.get("w"), (style.get("s") or 21) * SC * K)
        fbk, _ = get_font(FALLBACK, style.get("w"), (style.get("s") or 21) * SC * K)
        wmax = max(sum((font if has_glyph(fpath_, ch) or ch == " " else fbk).getlength(ch) for ch in p_) for p_ in s["parts"])
        bw_out = box[2] * SC * K
        if bw_out and wmax > bw_out * 1.02:
            style["s"] = (style.get("s") or 21) * max(0.75, bw_out / wmax)
        # 垂直置中在借來的框裡
        nl = len(s["parts"])
        font, _ = get_font(style.get("f") or FALLBACK, style.get("w"), (style.get("s") or 21) * SC * K)
        lhp = (style.get("lh") or ((sum(font.getmetrics())) / ((style.get("s") or 21) * SC * K)))
        bh_new = nl * (style.get("s") or 21) * lhp
        by = box[1] + (box[3] - bh_new) / 2
        r = render_text(s["text"], style, (box[0], by, box[2]))
        dx = dy = 0
        refit = next((it2 for lst in sub_items.values() for it2 in lst if getattr(it2, "_lid", None) == ref), None) if ref else None
        if ref and not rr.get("style"):
            # 借位字幕：把來源字用同樣方法排一次，與它的匯出圖比較，校正字型度量造成的偏移
            rb = box_of(card, nested_by_id, ref)
            if refit is not None and rb and refit.text:
                rr2 = render_text(refit.text, style, (rb[0], rb[1], rb[2]))
                dx, dy = calib(refit.img, refit.x, refit.y, rr2)
                if abs(dx) > 40 or abs(dy) > 30:
                    dx = dy = 0
        it = make_sub_item(r["img"], r["x"] + int(round(dx)), r["y"] + int(round(dy)), i, f"補畫字幕{i}", s["text"], style)
        if ref is None and "c" not in rr.get("style", {}):
            it._contrast = (s["text"], style, (box[0], by, box[2]))   # 建好整鏡後再依實際畫面檢查對比
        it.glyphs = r["glyphs"]
        if it.fin.get("fx") in ("type", "bounce"):
            it.segs = r["glyphs"]
        # 借位時放在來源字幕的圖層順序（上面的覆蓋層，例如 LED 點陣網點，才會一樣蓋到）
        it.z = refit.z + 0.001 if refit is not None else z_sub
        items.append(it)

    # ── 計數（③ 的 0→99→100）與倒數（⑧ 的 3→2→1）──
    for i, s in enumerate(subs):
        vals = counter_values(s["text"])
        if not vals:
            continue
        cr = sr.get("counter", {})
        if cr.get("none"):   # 數字已經烤在物件上（天燈上的字），不另外畫
            continue
        ref = counter_ref.get(i)
        if cr.get("layer") is False:
            ref = None
        zc = z_sub + 0.5
        if ref:
            rimg, rx, ry, rstyle, rbox, rtext, zc = ref
            zc += 0.005
            style = dict(rstyle or dstyle)
            box = rbox
        else:
            style = dict(dstyle)
            box = None
        style.update(cr.get("style", {}))
        if "box" in cr:
            box = tuple(cr["box"])
        if box is None:
            box = (0, 110, 480)
        if not style.get("a"):
            style["a"] = "center"
        countdown = int(vals[0].rstrip("%")) > int(vals[-1].rstrip("%"))
        # 校正：把縮圖上的那個數字用同樣方法排一次，與匯出圖比較
        dx = dy = 0
        if ref and "box" not in cr:
            rr_ = render_text(rtext, style, box)
            dx, dy = calib(rimg, rx, ry, rr_)
        cache = {}

        def rend(txt, style=style, box=box, cache=cache, dx=dx, dy=dy):
            if txt not in cache:
                r = render_text(txt, style, box)
                cache[txt] = (r["img"], r["x"] + int(round(dx)), r["y"] + int(round(dy)))
            return cache[txt]

        c_screen = not s.get("scene") if "world" not in cr else not cr["world"]

        def slot_render(slot, v, style=style):
            """每個數字畫在自己的位置（燈泡數字、氣球、天燈各一個）。slot＝圖層 id 或 [x, y, w]。"""
            if isinstance(slot, str):
                rimg_, rx_, ry_, rstyle_, rbox_, rtext_, _ = slot_refs[slot]
                st = dict(rstyle_ or style)
                st.update(cr.get("slot_style", {}))
                st["a"] = st.get("a") or "center"
                ddx, ddy = calib(rimg_, rx_, ry_, render_text(rtext_, st, rbox_))
                r_ = render_text(v, st, rbox_)
                return r_["img"], r_["x"] + int(round(ddx)), r_["y"] + int(round(ddy))
            # 自訂位置：沿用同一組裡第一個圖層數字的字型與排字校正
            ref_ = next((q for q in cr.get("slots", []) if isinstance(q, str) and q in slot_refs), None)
            if ref_:
                rimg_, rx_, ry_, rstyle_, rbox_, rtext_, _ = slot_refs[ref_]
                st = dict(rstyle_ or style)
                st.update(cr.get("slot_style", {}))
                st["a"] = st.get("a") or "center"
                ddx, ddy = calib(rimg_, rx_, ry_, render_text(rtext_, st, rbox_))
                r_ = render_text(v, st, tuple(slot[:3]))
                return r_["img"], r_["x"] + int(round(ddx)), r_["y"] + int(round(ddy))
            r_ = render_text(v, style, tuple(slot[:3]))
            return r_["img"], r_["x"], r_["y"]

        if countdown:
            n = len(vals)
            step = (s["t1"] - s["t0"]) / n
            cin = dict(cr.get("in") or vr.get("countdown_in") or {"fx": "slam", "d": 0.25})
            slots = cr.get("slots")
            for k_, v in enumerate(vals):
                img, x, y = slot_render(slots[k_], v) if slots and k_ < len(slots) else rend(v)
                it = Item(img, x, y, s["t0"] + k_ * step, s["t0"] + (k_ + 1) * step if k_ < n - 1 else s["t1"], zc,
                          f"倒數{v}", "count")
                it.fin = dict(cin)
                it.fout = {"fx": "fade", "d": 0.12} if k_ < n - 1 else {"fx": "fade", "d": 0.25}
                if "out" in cr:     # 例：數字氣球升空後飛走
                    it.fout = dict(cr["out"])
                if cr.get("keep"):   # 數字留在原地不消失（氣球、燈泡數字一個個累積）
                    it.b, it.fout = (s["t1"] if not cr.get("keep_end") else cr["keep_end"]), {"fx": "fade", "d": 0.25}
                it.screen = c_screen
                for lp in cr.get("loop", []):
                    it.loops.append(dict(lp))
                items.append(it)
        else:
            jump = cr.get("jump")
            if jump is None:
                m = re.search(r"(\d+(?:\.\d+)?)s\s*(?:瞬間)?跳\s*100", shot["dyn"])
                jump = float(m.group(1)) if m else s["t1"] - 0.6
                if not (s["t0"] + 1.0 <= jump <= s["t1"] - 0.3):
                    jump = s["t1"] - 0.6
            a_, b_ = s["t0"], cr.get("b", s["t1"])
            ctx["counter"] = (a_, b_, jump, vals)

            def frames(t, a_=a_, b_=b_, jump=jump, vals=vals, rend=rend):
                txt, jit, _ = counter_value(t, a_, b_, jump, vals)
                img, x, y = rend(txt)
                return img, x + jit * K, y

            it = Item(None, 0, 0, a_, b_, zc, "計數", "count")
            it.frames = frames
            it.fin = dict(cr.get("in") or {"fx": "fade", "d": 0.25})
            it.fout = {"fx": "fade", "d": 0.25}
            it.screen = c_screen
            items.append(it)
    # 額外補畫的元素（規則 extras）：規劃表寫了、縮圖沒畫的字；或匯出有誤的圖層改照參數畫
    # 新種類的補畫物件（rect／copy／scene／confetti）預設放在所有字幕之下，字才不會被看板、紙花蓋住
    z_under = min([it.z for it in items if it.kind in ("sub", "count")] or [z_sub]) - 0.05
    for ex in sr.get("extras", []):
        z_def = z_under if ex.get("kind") in ("rect", "copy", "scene", "confetti") else z_sub
        zx = z_names.get(ex["z_after"], z_sub) + 0.5 if "z_after" in ex else ex.get("z", z_def)
        if ex.get("kind") == "confetti":
            # 紙花／彩帶／糖珠／花瓣：從 origin 噴出到 region 裡的隨機位置，再受重力飄落（seed 固定，每次相同）
            rng = random.Random(ex.get("seed", 1))
            ox_, oy_ = ex.get("origin", [240, 135])
            rg = ex.get("region", [0, 0, 480, 200])
            t0_, t1_ = ex.get("show", [0, dur + 5])
            cols = ex.get("colors", ["#FF6F91", "#FFD45C", "#7CC08B", "#5BC0EB", "#B28DFF"])
            for k_ in range(ex.get("n", 12)):
                sz = ex.get("size", 5) * (0.7 + 0.6 * rng.random())
                part = {"kind": "rect", "shape": ex.get("shape", "rect"), "r": 1, "fill": rng.choice(cols),
                        "box": [rg[0] + rng.random() * rg[2], rg[1] + rng.random() * rg[3], sz, sz * ex.get("aspect", 0.6)]}
                img, x, y = rect_img(part, dstyle)
                it = Item(img, x, y, t0_ + k_ * ex.get("stagger", 0.0), t1_, zx, "confetti")
                d_ = ex.get("d", 0.5)
                it.fin = {"fx": "burst", "origin": [ox_ * SC, oy_ * SC], "d": d_} if ex.get("burst", True) else {"fx": "fade", "d": 0.2}
                it.fout = {"fx": "fade", "d": 0.3} if t1_ < dur - 0.01 else None
                it.loops = [{"fx": "fall", "g": ex.get("g", 160), "after": d_ if ex.get("burst", True) else 0},
                            {"fx": "sway", "deg": ex.get("sway", 40), "period": 0.6 + rng.random(), "phase": rng.random()}]
                if ex.get("hfloat"):
                    it.loops.append({"fx": "hfloat", "amp": ex["hfloat"], "period": 1.5 + rng.random(), "phase": rng.random()})
                it.screen = bool(ex.get("screen", False))
                it.front = bool(ex.get("front", False))
                items.append(it)
            continue
        if ex.get("kind") == "arc":
            img, x, y = arc_img(ex)
            it = Item(img, x, y, ex.get("show", [0, dur + 5])[0], ex.get("show", [0, dur + 5])[1], zx, "arc")
            if entering_cut:
                it.fin = {"fx": "fade", "d": 0.3}
            items.append(it)
            continue
        if ex.get("kind") in ("rect", "copy", "scene"):
            # rect＝縮圖沒畫、規劃表寫了的物件，用簡化色塊代替（看板、燈牌、桌面、計程車）；
            # copy＝複製縮圖圖層到別處（card 可指定別張卡）；scene＝借別張卡的整個場景（規劃表寫「同 ②」的）
            if ex["kind"] == "rect":
                img, x, y = rect_img(ex, dstyle)
            elif ex["kind"] == "scene":
                img, x, y = scene_img(work, ver, ex, place)
            else:
                px_, py_ = place[ex.get("card", card["id"])]["place"][ex["id"]][:2]
                img, x, y = to_out(load_layer(work, ver, ex["id"], bool(ex.get("clean")), None), px_ + ex.get("dx", 0) * SC,
                                   py_ + ex.get("dy", 0) * SC)
                if ex.get("scale"):
                    img, ox_, oy_ = transform(img, ex["scale"])
                    x, y = x + ox_, y + oy_
            sh_ = ex.get("show", [0, dur + 5])
            it = Item(img, x, y, sh_[0], sh_[1], zx, ex.get("name", ex["kind"]))
            it.fin = dict(ex["in"]) if "in" in ex else ({"fx": "fade", "d": 0.3} if sh_[0] > 0.01 or entering_cut else None)
            it.fout = dict(ex["out"]) if "out" in ex else ({"fx": "fade", "d": 0.2} if sh_[1] < dur - 0.01 else None)
        else:
            r = render_text(ex["text"], dict(dstyle, **ex.get("style", {})), tuple(ex["box"][:3]))
            it = Item(r["img"], r["x"], r["y"], ex.get("show", [0, dur + 5])[0], ex.get("show", [0, dur + 5])[1], zx, ex["text"])
            it.fin = dict(ex.get("in", {"fx": "fade", "d": 0.3}))
            it.fout = {"fx": "fade", "d": 0.2}
            if "out" in ex:
                it.fout = dict(ex["out"])
            if it.fin.get("fx") in ("type", "bounce", "beat"):
                it.segs = r["glyphs"]
        it.loops = [dict(q) for q in ex.get("loop", [])]
        if "reveal" in ex:
            it.reveal = dict(ex["reveal"])
        if "move" in ex:
            it.move = dict(ex["move"])
        if "pivot" in ex:
            it.pivot = ex["pivot"]
        if "anchor" in ex:
            it.anchor = ex["anchor"]
        it.screen = bool(ex.get("screen", False))
        it.front = bool(ex.get("front", False))
        items.append(it)
    # stagger：同一條規則命中多個圖層時，依序延遲進場；counter_seq：依百分比逐格亮起
    for r in layer_rules:
        if "stagger" in r or r.get("counter_seq"):
            hit = [it for it in items if r.get("match") and not r["match"].startswith("id:") and re.search(r["match"], it.name or "")]
            for k_, it in enumerate(hit):
                if "stagger" in r:
                    if it.fin is None:
                        it.fin = {"fx": "fade", "d": 0.3}
                    it.fin = dict(it.fin)
                    it.fin["delay"] = it.fin.get("delay", 0) + k_ * r["stagger"]
                if r.get("counter_seq"):
                    it.cidx, it.cn = k_, r.get("seq_n", len(hit))
                    it.static = False
    if "counter" in ctx:
        ctx["counter_end"] = ctx["counter"][1]
    # 字幕結束點離鏡尾 ≤ 0.35 秒、而且接下來不是硬切：留到鏡尾由轉場帶走
    # （否則淡黑／溶接時字先消失、底下的框還在，會閃一下空框）
    if shot["trans"]["type"] != "cut":
        for it in items:
            if it.kind in ("sub", "count") and it.frames is None and dur - 0.35 <= it.b < dur:
                it.b, it.fout = dur + 5, None
    items.sort(key=lambda it: it.z)
    spans = build_chars(shot, color, dur, pair=sr.get("pair", vr.get("pair", False)), boxes=sr.get("char_boxes"))
    bg = bg_image(card["bg"], OW, OH)
    S = {"items": items, "spans": spans, "bg": bg, "ctx": ctx, "color": color, "shot": shot, "card": card,
         "rules": sr, "frame_shake": sr.get("frame_shake", []), "bob": sr.get("bob"), "flash": sr.get("flash", [])}
    # 第二批新增（規則檔沒寫就不啟用，第一批的輸出不受影響）
    if sr.get("cam"):
        S["cam"] = prep_cam(sr["cam"], work, ver, card)
    q = sr.get("qfps", vr.get("qfps"))
    if q:
        S["qfps"] = q
    for k_ in ("color_spread", "iris"):
        if k_ in sr:
            S[k_] = sr[k_]
    fix_contrast(S)
    return S


# ════════════════════════════════════════════════════════════════════════
# 鏡頭（3D 場景幕的推拉平移）、抽格、整格效果
# ════════════════════════════════════════════════════════════════════════
def prep_cam(cam, work, ver, card):
    """cam＝{"keys": [[秒, cx, cy, 倍率], …], "ext": [左, 上, 右, 下], "chars": "world"|"screen", "char_key": i}
    keys 的 (cx, cy) 是「畫面中心對準縮圖上的哪一點」（縮圖座標，可以超出 0～480／0～270 落到延伸區）。
    ext＝縮圖四周要延伸多少（縮圖 px）：鏡頭移到縮圖沒畫的地方時，延伸區用縮圖邊緣的顏色帶補滿。"""
    ext = cam.get("ext", [0, 0, 0, 0])
    l, t, r, b = [int(round(e * SC * K)) for e in ext]
    Wd, Hd = OW + l + r, OH + t + b
    bg = np.asarray(bg_image(card["bg"], OW, OH).convert("RGB"), np.float32)
    if l or t or r or b:
        th = np.asarray(Image.open(os.path.join(work, "layers", ver, card["thumb"] + ".png")).convert("RGB")
                        .resize((OW, OH), Image.BILINEAR), np.float32)
        Wa = np.zeros((Hd, Wd, 3), np.float32)
        Wa[t:t + OH, l:l + OW] = th
        st = 24

        def runmed(v, k=81):
            """沿著帶子方向的寬窗中位數：碰到縮圖邊緣的小物件（喇叭、角色框）不會被拉成一條長紋。"""
            from numpy.lib.stride_tricks import sliding_window_view
            pad = np.pad(v, ((k // 2, k // 2), (0, 0)), mode="edge")
            return np.median(sliding_window_view(pad, k, axis=0), axis=-1)

        if l:
            Wa[t:t + OH, :l] = runmed(np.median(th[:, :st], 1))[:, None, :]
        if r:
            Wa[t:t + OH, l + OW:] = runmed(np.median(th[:, -st:], 1))[:, None, :]
        if t:
            Wa[:t, :] = runmed(np.median(Wa[t:t + st, :], 0))[None, :, :]
        if b:
            Wa[t + OH:, :] = runmed(np.median(Wa[t + OH - st:t + OH, :], 0))[None, :, :]
        band = Image.fromarray(Wa.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4))
        Wa = np.asarray(band, np.float32).copy()
        Wa[t:t + OH, l:l + OW] = bg      # 縮圖範圍內照常由底色＋圖層組成
        wbg = Image.fromarray(Wa.clip(0, 255).astype(np.uint8)).convert("RGBA")
    else:
        wbg = Image.fromarray(bg.astype(np.uint8)).convert("RGBA")
    keys = cam.get("keys") or [[0, TH_W / 2, TH_H / 2, 1.0]]
    fill = tuple(int(v) for v in np.asarray(wbg.convert("RGB"))[Hd // 2, Wd // 2]) + (255,)
    return {"keys": keys, "wbg": wbg, "off": (l, t), "chars": cam.get("chars", "world"),
            "char_key": cam.get("char_key", 0), "fill": fill}


def cam_state(cam, t):
    keys = cam["keys"]
    if t <= keys[0][0]:
        k = keys[0]
        return k[1], k[2], k[3]
    if t >= keys[-1][0]:
        k = keys[-1]
        return k[1], k[2], k[3]
    for a_, b_ in zip(keys, keys[1:]):
        if a_[0] <= t <= b_[0]:
            p = (t - a_[0]) / max(1e-6, b_[0] - a_[0])
            e = p if (len(b_) > 4 and b_[4] == "lin") else smooth(p)
            return tuple(a_[i] + (b_[i] - a_[i]) * e for i in (1, 2, 3))
    k = keys[-1]
    return k[1], k[2], k[3]


def apply_cam(world, cam, t):
    cx, cy, s = cam_state(cam, t)
    l, tp = cam["off"]
    wx, wy = cx * SC * K + l, cy * SC * K + tp
    return world.transform((OW, OH), Image.AFFINE, (1 / s, 0, wx - OW / 2 / s, 0, 1 / s, wy - OH / 2 / s),
                           resample=Image.BICUBIC, fillcolor=cam["fill"])


def char_to_world(cam, x, y, w, h):
    """角色框（縮圖座標、以畫面為準）→ 世界畫布座標：以 char_key 那一刻的鏡頭為準，那一刻角色正好在規劃表寫的位置。"""
    k = cam["keys"][min(cam["char_key"], len(cam["keys"]) - 1)]
    cx, cy, s = k[1], k[2], k[3]
    return (x - TH_W / 2) / s + cx, (y - TH_H / 2) / s + cy, w / s, h / s


def color_spread_fx(img, cs, t):
    """黑白→彩色擴散（V14-08）：縮圖本身是黑白＋粉紅；t 之後從 center 以圓形擴散，
    把灰階換成漸層映射的暖色（map 由暗到亮），飽和的粉紅保留原色。"""
    if t < cs["t"]:
        return img
    p = smooth((t - cs["t"]) / cs.get("d", 0.8))
    a = np.asarray(img.convert("RGB"), np.float32) / 255.0
    lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
    stops = [np.array(hex_rgba(c)[:3], np.float32) / 255.0 for c in cs["map"]]
    xs = np.linspace(0, 1, len(stops))
    mapped = np.stack([np.interp(lum, xs, [s_[i] for s_ in stops]) for i in range(3)], -1)
    sat = a.max(-1) - a.min(-1)
    keep = np.clip((sat - 0.12) / 0.15, 0, 1)[..., None]
    mix = cs.get("mix", 0.85)
    col = a * (1 - mix) + mapped * mix
    col = col * (1 - keep) + a * keep
    cx, cy = cs["center"][0] * SC * K, cs["center"][1] * SC * K
    yy, xx = np.mgrid[0:OH, 0:OW]
    rmax = math.hypot(max(cx, OW - cx), max(cy, OH - cy)) + 80
    m = np.clip((p * rmax - np.hypot(xx - cx, yy - cy)) / 80.0, 0, 1)[..., None]
    out = a * (1 - m) + col * m
    return Image.fromarray((out * 255).clip(0, 255).astype(np.uint8)).convert("RGBA")


def iris_fx(img, ir, t):
    """圓形虹膜打開（老電影開場）：t～t+d 之間圓形由中心放大，圓外是黑色。"""
    t0, d = ir.get("t", 0), ir.get("d", 0.4)
    if t >= t0 + d:
        return img
    p = smooth((t - t0) / d) if t >= t0 else 0.0
    cx, cy = ir.get("center", [TH_W / 2, TH_H / 2])
    cx, cy = cx * SC * K, cy * SC * K
    rmax = math.hypot(max(cx, OW - cx), max(cy, OH - cy))
    yy, xx = np.mgrid[0:OH, 0:OW]
    m = np.clip((p * rmax - np.hypot(xx - cx, yy - cy)) / 3.0, 0, 1)
    out = Image.new("RGBA", img.size, (0, 0, 0, 255))
    out.paste(img, (0, 0), Image.fromarray((m * 255).astype(np.uint8)))
    return out


_ALL_CARDS = {}   # Version 建立時填入（scene 借別張卡的圖層用）


def scene_img(work, ver, ex, place):
    """把別張卡（同一版）的圖層照定位疊成一張場景圖；不含角色框，exclude 正規式排除字幕等圖層。"""
    cid = ex["card"]
    c2 = _ALL_CARDS[cid]
    pl2 = place[cid]["place"]
    canvas = bg_image(c2["bg"], TH_W * SC, TH_H * SC)
    exc = re.compile(ex["exclude"]) if ex.get("exclude") else None
    for L in c2["layers"]:
        if is_char_box(L) or (exc and exc.search(L["name"])):
            continue
        im = Image.open(os.path.join(work, "layers", ver, L["id"] + ".png")).convert("RGBA")
        paste(canvas, im, pl2[L["id"]][0], pl2[L["id"]][1])
    return canvas.resize((OW, OH), Image.LANCZOS), 0, 0


def rect_img(ex, dstyle):
    """簡化物件：圓角矩形或橢圓（fill／stroke／sw／r），可帶置中文字（text＋style）。box＝縮圖座標 [x, y, w, h]。"""
    x, y, w, h = ex["box"]
    s = SC
    sw = ex.get("sw", 0)
    pad = int(math.ceil(sw * s)) + 2 + int(math.ceil(ex.get("blur", 0) * s * 3))
    W, H = max(1, int(round(w * s))), max(1, int(round(h * s)))
    im = Image.new("RGBA", (W + 2 * pad, H + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    box = [pad, pad, pad + W - 1, pad + H - 1]
    fill = hex_rgba(ex["fill"]) if ex.get("fill") else None
    outline = hex_rgba(ex["stroke"]) if ex.get("stroke") else None
    if ex.get("shape") == "ellipse":
        d.ellipse(box, fill=fill, outline=outline, width=max(1, int(round(sw * s))) if outline else 0)
    else:
        d.rounded_rectangle(box, radius=ex.get("r", 6) * s, fill=fill, outline=outline,
                            width=max(1, int(round(sw * s))) if outline else 0)
    if ex.get("blur"):   # 柔邊（光暈、陽光、暖光）
        im = im.filter(ImageFilter.GaussianBlur(ex["blur"] * s))
    out, ox, oy = to_out(im, x * s - pad, y * s - pad)
    if ex.get("text"):
        st = dict(dstyle, **ex.get("style", {}))
        st["a"] = st.get("a") or "center"
        fs = float(st.get("s") or 21)
        nl = len(ex["text"].split("\n"))
        lh = st.get("lh") or 1.25
        by = y + (h - nl * fs * lh) / 2 + ex.get("ty", 0)
        r = render_text(ex["text"], st, (x, by, w))
        paste(out, r["img"], r["x"] - ox, r["y"] - oy)
    return out, ox, oy


def fix_contrast(S):
    """補畫字幕（沒有借位的）：渲染它出現時段中點的實際畫面（不含它自己），在字的範圍取樣底色；
    對比不足 3:1 就改成白字或深字。縮圖是最後狀態，不能拿縮圖判斷（例如大標框要晚一點才出現）。"""
    for it in S["items"]:
        if not getattr(it, "_contrast", None):
            continue
        text, style, box = it._contrast
        if S.get("cam") and not it.screen:
            continue   # 跟著鏡頭動的場景字：座標在世界畫布上，不能拿畫面去比；顏色照規則檔
        tm = (it.a + it.b) / 2
        others = [o for o in S["items"] if o is not it and not getattr(o, "_contrast", None)]
        S2 = dict(S, items=others)
        frame = render_shot(S2, tm).convert("RGB")
        ib = ink_box(it.img, it.x, it.y)
        if not ib:
            continue
        cb = (max(0, int(ib[0])), max(0, int(ib[1])), min(OW, int(ib[2])), min(OH, int(ib[3])))
        if cb[2] <= cb[0] or cb[3] <= cb[1]:
            continue
        reg = np.asarray(frame.crop(cb), np.float32).reshape(-1, 3)
        if len(reg) == 0:
            continue
        lb = luminance(np.median(reg, 0))
        lt = luminance(hex_rgba(style.get("c") or "#FFFFFF"))
        if (max(lb, lt) + 0.05) / (min(lb, lt) + 0.05) >= 3:
            continue
        style = dict(style, c="#FFFFFF" if lb < 0.35 else "#2A2A2A")
        r = render_text(text, style, box)
        it.img, it.style, it.x, it.y = r["img"], style, r["x"], r["y"]
        if it.segs is not None:
            it.segs = r["glyphs"]
        it._contrast = None


def shot_ctx(S, t):
    ctx = dict(S["ctx"])
    if "counter" in ctx:
        a_, b_, jump, vals = ctx["counter"]
        ctx["counter_frac"] = counter_value(t, a_, b_, jump, vals)[2] if t >= a_ else 0.0
    return ctx


def render_shot(S, t):
    if S.get("cam") or S.get("qfps") or S.get("color_spread") or S.get("iris"):
        return render_shot_world(S, t)
    ctx = shot_ctx(S, t)
    # 角色狀態（給 follow 用）
    chars = {}
    for who in S["spans"]:
        st = char_state(S["spans"], who, t)
        if st:
            al, x, y, w, h, label = st
            # 位移：相對該角色在本鏡第一段起點的位置
            sp0 = S["spans"][who][0]["segs"][0]
            bx, by, _, _ = char_geom(sp0["from"], sp0["h"])
            chars[who] = {"state": (al, (x - bx) * SC * K, (y - by) * SC * K), "box": st}
    ctx["chars"] = chars
    canvas = S["bg"].copy()
    for it in S["items"]:
        if not it.front:
            draw_item(canvas, it, t, ctx)
    for who, c in chars.items():
        al, x, y, w, h, label = c["box"]
        im = char_box_img(label, w, h, S["color"])
        paste(canvas, mul_alpha(im, al), x * SC * K, y * SC * K)
    for it in S["items"]:
        if it.front:
            draw_item(canvas, it, t, ctx)
    return post_fx(S, canvas, t)


def render_shot_world(S, t):
    """有鏡頭運動／抽格／整格效果的鏡：場景（圖層、場景字、角色框）先畫在世界畫布上、套鏡頭，
    再疊不跟鏡頭動的字幕。qfps＝場景以每秒 N 格抽格（字幕不抽格）。"""
    q = S.get("qfps")
    tw = math.floor(t * q + 1e-6) / q if q else t
    ctx_w, ctx_s = shot_ctx(S, tw), shot_ctx(S, t)
    cam = S.get("cam")
    world = cam["wbg"].copy() if cam else S["bg"].copy()
    off = cam["off"] if cam else (0, 0)
    in_world = cam is None or cam["chars"] == "world"
    chars = {}
    for who in S["spans"]:
        st = char_state(S["spans"], who, tw)
        if not st:
            continue
        al, x, y, w, h, label = st
        sp0 = S["spans"][who][0]["segs"][0]
        bx, by, _, _ = char_geom(sp0["from"], sp0["h"])
        if cam and in_world:
            x, y, w, h = char_to_world(cam, x, y, w, h)
            bx, by, _, _ = char_to_world(cam, bx, by, 0, 0)
        chars[who] = {"state": (al, (x - bx) * SC * K, (y - by) * SC * K), "box": (al, x, y, w, h, label)}
    ctx_w["chars"] = ctx_s["chars"] = chars

    def put_chars(canvas, o):
        for who, c in chars.items():
            al, x, y, w, h, label = c["box"]
            im = char_box_img(label, w, h, S["color"])
            paste(canvas, mul_alpha(im, al), x * SC * K + o[0], y * SC * K + o[1])

    for it in S["items"]:
        if not it.screen and not it.front:
            draw_item(world, it, tw, ctx_w, off)
    if in_world:
        put_chars(world, off)
    for it in S["items"]:
        if not it.screen and it.front:
            draw_item(world, it, tw, ctx_w, off)
    canvas = apply_cam(world, cam, tw) if cam else world
    if not in_world:
        put_chars(canvas, (0, 0))
    if S.get("color_spread"):
        canvas = color_spread_fx(canvas, S["color_spread"], t)
    for it in S["items"]:
        if it.screen:
            draw_item(canvas, it, t, ctx_s)
    if S.get("iris"):
        canvas = iris_fx(canvas, S["iris"], t)
    return post_fx(S, canvas, t)


def post_fx(S, canvas, t):
    # 整格上下晃（車廂）
    if S.get("bob"):
        amp, per = S["bob"]
        oy = int(round(amp * K * math.sin(2 * math.pi * t / per)))
        if oy:
            sh = S["bg"].copy()
            sh.paste(canvas, (0, oy))
            canvas = sh
    # 整格閃白（出隧道白光等）
    for ts, d, peak in S.get("flash", []):
        if ts <= t < ts + d:
            canvas = Image.blend(canvas, Image.new("RGBA", canvas.size, (255, 255, 255, 255)), peak * (1 - (t - ts) / d))
    # 整格震動
    for fs in S["frame_shake"]:
        ts, amp, d = fs
        if ts <= t < ts + d:
            q = 1 - (t - ts) / d
            ox = int(round(amp * K * q * math.sin(t * 95)))
            oy = int(round(amp * K * q * 0.6 * math.cos(t * 77)))
            sh = S["bg"].copy()
            sh.paste(canvas, (ox, oy))
            canvas = sh
    return canvas


# ════════════════════════════════════════════════════════════════════════
# 整版：轉場、角落標示
# ════════════════════════════════════════════════════════════════════════
LABEL_FONT = None


def corner_label(text, align):
    f, _ = get_font("Noto Sans TC", 500, 17)
    w = int(f.getlength(text)) + 16
    im = Image.new("RGBA", (w, 28), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, 27], radius=8, fill=(0, 0, 0, 70))
    d.text((8, 21), text, font=f, fill=(255, 255, 255, 170), anchor="ls")
    return im


class Version:
    def __init__(self, work, vid, plan_v, cards, nested, rules):
        self.vid, self.plan = vid, plan_v
        self.shots = plan_v["shots"]
        _ALL_CARDS.update(cards)
        place = json.load(open(os.path.join(work, "cache", vid, "place.json"), encoding="utf-8"))
        analyses = {s["id"]: (cards[s["id"]], analyse_shot(s, cards[s["id"]], nested), s) for s in self.shots}
        dstyle = default_sub_style(cards, nested, vid, analyses)
        vr = (rules or {}).get(vid, {})
        dstyle.update(vr.get("sub_style", {}))
        color = char_color(work, vid, cards[self.shots[0]["id"]])
        self.S = []
        prev = None
        for s in self.shots:
            self.S.append(build_shot(work, vid, s, cards[s["id"]], nested, place, rules, dstyle, prev, color))
            prev = s["trans"]
        self.total = plan_v["total"]
        self.labels = [corner_label(f"{s['id']}  {s['seg']}", "l") for s in self.shots]
        self.wm = corner_label("動態分鏡預覽・非成品", "r")

    def shot_at(self, T):
        for i, s in enumerate(self.shots):
            if T < s["t1"] or i == len(self.shots) - 1:
                return i
        return len(self.shots) - 1

    def frame(self, T):
        i = self.shot_at(T)
        s = self.shots[i]
        cur = None
        out = None
        # 交疊型轉場（溶接、推移）
        if i + 1 < len(self.shots) and s["trans"]["type"] in ("dissolve", "push") and T > s["t1"] - s["trans"]["d"] / 2:
            A_, B_, tr, c = i, i + 1, s["trans"], s["t1"]
        elif i > 0 and self.shots[i - 1]["trans"]["type"] in ("dissolve", "push") and T < s["t0"] + self.shots[i - 1]["trans"]["d"] / 2:
            A_, B_, tr, c = i - 1, i, self.shots[i - 1]["trans"], s["t0"]
        else:
            A_ = None
        if A_ is not None:
            d = tr["d"]
            p = clamp01((T - (c - d / 2)) / d)
            fa = render_shot(self.S[A_], T - self.shots[A_]["t0"])
            fb = render_shot(self.S[B_], T - self.shots[B_]["t0"])
            if tr["type"] == "dissolve":
                out = Image.blend(fa, fb, smooth(p))
            else:
                off = int(round(smooth(p) * OW))
                out = Image.new("RGBA", (OW, OH), (0, 0, 0, 255))
                if tr["dir"] < 0:    # ←：本鏡往左推出、下一鏡從右推入
                    out.paste(fa, (-off, 0))
                    out.paste(fb, (OW - off, 0))
                else:
                    out.paste(fa, (off, 0))
                    out.paste(fb, (off - OW, 0))
        else:
            out = render_shot(self.S[i], T - s["t0"])
        # 覆蓋型轉場
        white = black = 0.0
        tr = s["trans"]
        if tr["type"] == "flash" and s["t1"] - tr["pre"] <= T < s["t1"]:
            white = tr["peak"] * (T - (s["t1"] - tr["pre"])) / tr["pre"]
        if i > 0:
            pt = self.shots[i - 1]["trans"]
            if pt["type"] == "flash" and s["t0"] <= T < s["t0"] + pt["post"]:
                white = pt["peak"] * (1 - (T - s["t0"]) / pt["post"])
            if pt["type"] == "black" and T < s["t0"] + pt["in"]:
                black = max(black, 1 - smooth((T - s["t0"]) / pt["in"]))
        if tr["type"] == "black" and T > s["t1"] - tr["out"]:
            black = max(black, (T - (s["t1"] - tr["out"])) / tr["out"])
        if tr["type"] == "fadeout" and T > s["t1"] - tr["d"]:
            black = max(black, (T - (s["t1"] - tr["d"])) / tr["d"])
        if white > 0:
            out = Image.blend(out, Image.new("RGBA", out.size, (255, 255, 255, 255)), clamp01(white))
        if black > 0:
            out = Image.blend(out, Image.new("RGBA", out.size, (0, 0, 0, 255)), clamp01(black))
        out = out.copy()
        paste(out, self.labels[i], 14, 12)
        paste(out, self.wm, OW - self.wm.width - 14, OH - self.wm.height - 12)
        return out


def load_rules(path):
    if not path:
        return {}
    return json.load(open(path, encoding="utf-8"))


def setup_fonts(args):
    FONT_DIRS[:] = [os.path.join(args.work, "fonts")]


def cmd_still(args):
    setup_fonts(args)
    plan = parse_plan(args.plan)
    cards, nested = load_extract(args.work)
    rules = load_rules(args.rules)
    vid = args.vers[0]
    V = Version(args.work, vid, plan[vid], cards, nested, rules)
    od = os.path.join(args.work, "stills")
    os.makedirs(od, exist_ok=True)
    for T in args.times:
        p = os.path.join(od, f"{vid}_{T:06.2f}.png")
        V.frame(T).convert("RGB").save(p)
        print(p)


def _render_version(a):
    work, plan_path, rules_path, vid, outdir, tmpdir = a
    FONT_DIRS[:] = [os.path.join(work, "fonts")]
    plan = parse_plan(plan_path)
    cards, nested = load_extract(work)
    rules = load_rules(rules_path)
    V = Version(work, vid, plan[vid], cards, nested, rules)
    n = int(round(V.total * FPS))
    inter = os.path.join(tmpdir, f"{vid}_lossless.mkv")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "ultrafast", "-qp", "0", "-pix_fmt", "yuv444p", inter]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(n):
        T = f / FPS
        pr.stdin.write(V.frame(T).convert("RGB").tobytes())
    pr.stdin.close()
    pr.wait()
    # 正式編碼：CRF 由低往高找，控制在 5.8 MB 以內
    out = os.path.join(outdir, f"{vid}.mp4")
    for crf in (18, 20, 22, 24, 26, 28, 30, 32):
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", inter, "-c:v", "libx264", "-preset", "slow", "-tune", "animation",
               "-crf", str(crf), "-pix_fmt", "yuv420p", "-profile:v", "high", "-r", str(FPS), "-movflags", "+faststart",
               "-an", out]
        subprocess.run(cmd, check=True)
        if os.path.getsize(out) <= 5.8 * 1024 * 1024:
            break
    # 封面：③ 歡迎字出現 1 秒後
    sh = next((s for s in V.shots if s["seg"] == "③"), V.shots[len(V.shots) // 2])
    last = max((x for x in sh["subs"] if not counter_values(x["text"])), key=lambda x: x["t0"], default=None)
    tl = min(sh["dur"] - 0.6, (last["t0"] + 1.2) if last else sh["dur"] / 2)
    V.frame(sh["t0"] + tl).convert("RGB").save(os.path.join(outdir, f"{vid}.jpg"), quality=88)
    return vid, crf, os.path.getsize(out), V.total, sh["id"], round(tl, 2)


def cmd_video(args):
    plan = parse_plan(args.plan)
    vers = args.vers or list(plan.keys())
    os.makedirs(args.out, exist_ok=True)
    tmp = os.path.join(args.work, "tmp")
    os.makedirs(tmp, exist_ok=True)
    jobs = [(args.work, args.plan, args.rules, v, args.out, tmp) for v in vers]
    res = []
    with Pool(min(args.jobs, len(jobs))) as pool:
        for r in pool.imap_unordered(_render_version, jobs):
            print(f"{r[0]}: CRF {r[1]}  {r[2] / 1024 / 1024:.2f} MB  {r[3]:g}s  封面 {r[4]} +{r[5]}s", flush=True)
            res.append(r)
    return res


COMMON_NOTE = "動態分鏡預覽：角色是規劃表時段出場的佔位框（框內寫動作），沒有聲音；畫面元素取自比稿縮圖。"


def cmd_index(args):
    """依成品資料夾裡的 Vxx.mp4／Vxx.jpg 寫 index.json（notes 取自規則檔各版的 notes）。"""
    plan = parse_plan(args.plan)
    rules = load_rules(args.rules)
    out = []
    for vid, v in plan.items():
        f = os.path.join(args.out, f"{vid}.mp4")
        if not os.path.exists(f):
            continue
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f],
                                   capture_output=True, text=True).stdout.strip() or 0)
        note = (rules.get(vid, {}) or {}).get("notes", "")
        e = {"id": vid, "title": v["title"], "seconds": round(dur, 2), "file": f"{vid}.mp4",
             "poster": f"{vid}.jpg", "notes": (COMMON_NOTE + note) if note else COMMON_NOTE}
        if args.batch is not None:
            e["batch"] = args.batch
            e["category"] = v.get("category") or args.category
        out.append(e)
    p = os.path.join(args.out, "index.json")
    if args.batch is not None and os.path.exists(p):
        # 分批：保留 index.json 裡不屬於這份規劃表的版本，依版號排序合併
        ids = {e["id"] for e in out}
        out = sorted([e for e in json.load(open(p, encoding="utf-8")) if e["id"] not in ids] + out,
                     key=lambda e: e["id"])
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(p, len(out), "版")


# ════════════════════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["report", "prep", "still", "video", "index"])
    ap.add_argument("rest", nargs="*")
    ap.add_argument("--work", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--rules")
    ap.add_argument("--out")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    ap.add_argument("--batch", type=int, help="index：第幾批（指定時合併既有 index.json，並寫 batch／category 欄）")
    ap.add_argument("--category", help="index：規劃表沒寫「風格類別」時的類別")
    ap.add_argument("--big-skip", action="store_true",
                    help="prep：匯出圖比外框大 4 倍以上的圖層不搜尋、直接置中（避免放射背景這類圖層跑一小時）")
    args = ap.parse_args()
    if args.cmd == "still":
        args.vers = [args.rest[0]]
        args.times = [float(x) for x in args.rest[1:]]
    else:
        args.vers = args.rest
    if args.cmd in ("video", "index") and not args.out:
        ap.error(f"{args.cmd} 需要 --out")
    {"report": cmd_report, "prep": cmd_prep, "still": cmd_still, "video": cmd_video, "index": cmd_index}[args.cmd](args)


if __name__ == "__main__":
    main()
