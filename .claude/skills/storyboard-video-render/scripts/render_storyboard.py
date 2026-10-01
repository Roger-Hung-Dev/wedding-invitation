"""通用分鏡影片產生器：讀 storyboard.json（schema storyboard/v2）逐格合成，交給 ffmpeg 編碼。

用法：
  python render_storyboard.py prep  SB.json                 # 預先把每鏡照片縮圖、調色、做模糊底
  python render_storyboard.py still SB.json 12.0 99.5 ...   # 輸出指定秒數的單格 png（檢查用）
  python render_storyboard.py video SB.json OUT.mp4         # 輸出整支影片
共通選項：--work DIR（快取與抽格的工作目錄，預設為 SB.json 旁的 render-work/）、--jobs N（平行數）

特效實作的對照表（新增特效時要同步改的地方）：
  版型  → render_shot() 的 LAYOUT 分支        運鏡 → motion()、kmax()
  轉場  → overlap_window()／overlap_render()／overlay_tail()／overlay_head()
  片頭  → OPENINGS 註冊表                     片尾 → ENDINGS 註冊表
  調色  → GRADE_OPS
各特效的規格以 .claude/skills/fx-*/SKILL.md 為準。
"""
import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

SB = None
W = H = FPS = 0
DUR = 0.0
WORK = CACHE = PHOTO_DIR = FONT_DIR = ""
BACKDROP = (0, 0, 0)
SHOTS = []
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)


def hex_rgba(s):
    s = s.lstrip("#")
    if len(s) == 6:
        s += "FF"
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4, 6))


def hex_rgb(s):
    return hex_rgba(s)[:3]


def setup(sb_path, work):
    global SB, W, H, FPS, DUR, WORK, CACHE, PHOTO_DIR, FONT_DIR, BACKDROP, SHOTS
    with open(sb_path, encoding="utf-8") as f:
        SB = json.load(f)
    o = SB["output"]
    W, H, FPS, DUR = o["width"], o["height"], o["fps"], float(o["duration"])
    PHOTO_DIR, FONT_DIR = SB["assets"]["photoDir"], SB["assets"]["fontDir"]
    BACKDROP = hex_rgb(SB["palette"]["backdrop"])
    SHOTS = SB["shots"]
    WORK = work or os.path.join(os.path.dirname(os.path.abspath(sb_path)), "render-work")
    CACHE = os.path.join(WORK, "cache")


# ── 調色 ──────────────────────────────────────────────────────────────
# sat 以「調色前的原始亮度」為基準（不是上一步的結果），這是第 1 版婚紗輪播的既定行為，改了會偏色
def grade(img, name):
    ops = SB["grades"][name]
    if not ops:
        return img
    a = np.asarray(img).astype(np.float32) / 255.0
    lum = (a @ LUMA)[..., None]
    for op in ops:
        a = GRADE_OPS[op["op"]](a, lum, op)
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))


GRADE_OPS = {
    "mul": lambda a, lum, op: a * (np.array(op["v"], np.float32) if isinstance(op["v"], list) else op["v"]),
    "lin": lambda a, lum, op: op.get("b", 0.0) + a * op["a"],
    "sat": lambda a, lum, op: lum + (a - lum) * op["v"],
    "contrast": lambda a, lum, op: (a - 0.5) * op["v"] + 0.5 + op.get("offset", 0.0),
    "gamma": lambda a, lum, op: np.clip(a, 0, 1) ** op["v"],
}


def grade_key(name):
    return hashlib.sha1(json.dumps(SB["grades"][name]).encode()).hexdigest()[:8]


# ── 素材 ──────────────────────────────────────────────────────────────
def load_orig(name, need_long):
    """從原始檔讀出長邊至少 need_long 的影像（JPEG draft 只做 2 的冪次縮小，不損細節）。"""
    im = Image.open(os.path.join(PHOTO_DIR, name))
    im.draft("RGB", (need_long, need_long))
    return ImageOps.exif_transpose(im).convert("RGB")


def sharpen(im, percent=None):
    q = SB["quality"]["sharpen"]
    return im.filter(ImageFilter.UnsharpMask(radius=q["radius"], percent=percent or q["percent"],
                                             threshold=q["threshold"]))


def cover(im, w, h):
    s = max(w / im.width, h / im.height)
    r = im.resize((math.ceil(im.width * s), math.ceil(im.height * s)), Image.LANCZOS)
    x, y = (r.width - w) // 2, (r.height - h) // 2
    return r.crop((x, y, x + w, y + h))


def blur_bg(im, w, h):
    """模糊底：同一張照片放大鋪滿、模糊、以底色 40% 壓暗。"""
    small = cover(im, w // 4, h // 4).filter(ImageFilter.GaussianBlur(9))
    big = small.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(6))
    return Image.blend(big, Image.new("RGB", (w, h), BACKDROP), 0.40)


def akey(kind, name, gname, size=""):
    return f"{kind}_{os.path.splitext(name)[0]}_{grade_key(gname)}_{size}"


def cache_path(key):
    return os.path.join(CACHE, key + ".png")


def split_geometry():
    seam = 2
    left = (W - seam) // 2
    return [(0, left), (left + seam, left + seam + left)]


def grid_geometry(n):
    """回顧格：n 張 2:3 直式並排一列，外距 32、間距 16，垂直置中。"""
    margin, gap = 32, 16
    tw = (W - 2 * margin - (n - 1) * gap) // n
    th = round(tw * 1.5)
    if th > H - 2 * margin:
        th = H - 2 * margin
        tw = round(th / 1.5)
    x0 = (W - (n * tw + (n - 1) * gap)) // 2
    return tw, th, [x0 + (tw + gap) * j for j in range(n)], (H - th) // 2


def prep_one(job):
    kind, name, gname, size = job
    out = cache_path(akey(kind, name, gname, size))
    if os.path.exists(out):
        return out
    if kind == "pt":  # 直式照片，高度＝size（最大倍率時的顯示高）
        h = int(size)
        im = load_orig(name, h * 2)
        im = im.resize((round(h * im.width / im.height), h), Image.LANCZOS)
        im = sharpen(grade(im, gname))
    elif kind == "ld":  # 橫式滿版，鋪滿畫面再乘最大倍率（size＝倍率×100）
        k = int(size) / 100
        im = load_orig(name, round(W * k * 2))
        s = max(W / im.width, H / im.height) * k
        im = sharpen(grade(im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS), gname))
    elif kind == "bg":  # 模糊底，size＝寬
        im = blur_bg(grade(load_orig(name, 1000), gname), int(size), H)
    elif kind == "tile":  # 回顧格單格，size＝寬x高
        tw, th = (int(v) for v in size.split("x"))
        im = sharpen(grade(cover(load_orig(name, 1400), tw, th), gname), SB["quality"].get("tileSharpenPercent", 60))
    else:
        raise ValueError(f"未知素材種類 {kind}")
    im.save(out)
    return out


def shot_assets(sh):
    lay, photos, g, k = sh["layout"], sh["photos"], sh["grade"], kmax(sh["motion"])
    if lay == "A":
        return [("pt", photos[0], g, round(H * k)), ("bg", photos[0], g, str(W))]
    if lay == "B":
        half = split_geometry()[0][1]
        return [j for p in photos for j in (("pt", p, g, round(H * k)), ("bg", p, g, str(half)))]
    if lay == "H":
        return [("ld", photos[0], g, round(k * 100))]
    if lay == "C":
        tw, th, _, _ = grid_geometry(len(photos))
        return [("tile", p, g, f"{tw}x{th}") for p in photos]
    raise ValueError(f"{sh['id']}：未知版型 {lay}")


def prep_jobs():
    jobs = set()
    for sh in SHOTS:
        jobs |= set(shot_assets(sh))
    jobs |= set(OPENINGS[SB["opening"]["style"]]["assets"](SB["opening"]["params"]))
    jobs |= set(ENDINGS[SB["ending"]["style"]]["assets"](SB["ending"]["params"]))
    return sorted(jobs, key=str)


_cache = {}


def asset(kind, name, gname, size=""):
    key = akey(kind, name, gname, size)
    if key not in _cache:
        if len(_cache) > 24:
            _cache.pop(next(iter(_cache)))
        im = Image.open(cache_path(key)).convert("RGB")
        im.load()
        _cache[key] = im
    return _cache[key]


# ── 幾何：子像素定位＋邊緣半透明過渡（運鏡時照片邊緣不會一格跳 1 px）────────
PAD = 2
_padded = {}


def padded(src):
    """四周各補 2 px（複製邊緣像素，避免取樣時滲入黑邊）＋對應的覆蓋遮罩。"""
    key = id(src)
    if key not in _padded:
        if len(_padded) > 24:
            _padded.pop(next(iter(_padded)))
        a = np.pad(np.asarray(src), ((PAD, PAD), (PAD, PAD), (0, 0)), mode="edge")
        m = np.zeros(a.shape[:2], np.uint8)
        m[PAD:-PAD, PAD:-PAD] = 255
        _padded[key] = (Image.fromarray(a), Image.fromarray(m), src)
    return _padded[key][:2]


def place_sub(canvas, src, x0, y0, s, clip=None):
    """把 src 以縮放 s（≤1）貼到畫面座標 (x0, y0)，位置可為小數。"""
    clip = clip or (0, 0, W, H)
    dw, dh = src.width * s, src.height * s
    L, T = max(clip[0], math.floor(x0) - 1), max(clip[1], math.floor(y0) - 1)
    R, B = min(clip[2], math.ceil(x0 + dw) + 1), min(clip[3], math.ceil(y0 + dh) + 1)
    if R <= L or B <= T:
        return
    rgb, mask = padded(src)
    a = 1 / s
    data = (a, 0, (L - x0) * a + PAD, 0, a, (T - y0) * a + PAD)
    size = (R - L, B - T)
    im = rgb.transform(size, Image.AFFINE, data, resample=Image.BICUBIC)
    m = mask.transform(size, Image.AFFINE, data, resample=Image.BILINEAR)
    canvas.paste(im, (L, T), m)


def place_center(canvas, src, cx, cy, s, clip=None, snap=False):
    x0, y0 = cx - src.width * s / 2, cy - src.height * s / 2
    if snap:  # 靜止鏡頭對齊整數像素，避免內插造成的輕微模糊
        x0, y0 = round(x0), round(y0)
    place_sub(canvas, src, x0, y0, s, clip)


def lerp(a, b, p):
    return a + (b - a) * p


def ease(p):
    p = min(1.0, max(0.0, p))
    return p * p * (3 - 2 * p)


# ── 運鏡 ──────────────────────────────────────────────────────────────
def kmax(m):
    """本鏡內的最大放大倍率；照片一次縮到這個尺寸，逐格只做 ≤1 的縮小。"""
    t = m["type"]
    if t == "zoom":
        return max(m["from"], m["to"])
    if t == "pan":
        return m["scale"]
    if t == "split-counter":
        return max(m["left"] + m["right"])
    if t in ("still", "split-late", "stagger"):
        return 1.0
    raise ValueError(f"未知運鏡 {t}")


def motion(m, p):
    """回傳（縮放倍率, 水平位移 px）；p 為本鏡進度 0→1（轉場交疊時可略超出）。"""
    q = ease(p) if m.get("ease") else p
    if m["type"] == "zoom":
        return lerp(m["from"], m["to"], q), 0
    if m["type"] == "pan":
        d = 1 if m["dir"] == "right" else -1
        return m["scale"], d * lerp(-m["distance"] / 2, m["distance"] / 2, q)
    return 1.0, 0


def render_shot(i, t):
    sh = SHOTS[i]
    s, e, lay, photos, g, m = sh["start"], sh["end"], sh["layout"], sh["photos"], sh["grade"], sh["motion"]
    p = (t - s) / (e - s)
    km = kmax(m)
    still = m["type"] == "still"
    if lay == "A":
        c = asset("bg", photos[0], g, str(W)).copy()
        k, dx = motion(m, p)
        place_center(c, asset("pt", photos[0], g, round(H * km)), W / 2 + dx, H / 2, k / km, snap=still)
    elif lay == "H":
        c = Image.new("RGB", (W, H))
        k, dx = motion(m, p)
        place_center(c, asset("ld", photos[0], g, round(km * 100)), W / 2 + dx, H / 2, k / km, snap=still)
    elif lay == "B":
        c = Image.new("RGB", (W, H), BACKDROP)
        q = ease(p) if m.get("ease") else p
        if m["type"] == "split-counter":
            ks = [lerp(*m["left"], q), lerp(*m["right"], q)]
        else:
            ks = [motion(m, p)[0]] * 2
        late = m["type"] == "split-late"
        for j, (x0, x1) in enumerate(split_geometry()):
            half = asset("bg", photos[j], g, str(x1 - x0)).copy()
            src = asset("pt", photos[j], g, round(H * km))
            place_center(half, src, (x1 - x0) / 2, H / 2, ks[j] / km, clip=(0, 0, x1 - x0, H), snap=late or still)
            if late and j == 1:  # 右格晚進
                a = ease((t - s - m["delay"]) / m["fade"])
                half = Image.blend(Image.new("RGB", half.size, BACKDROP), half, a)
            c.paste(half, (x0, 0))
    elif lay == "C":  # n 張直式並排一列；stagger 時由左至右依序淡入
        c = Image.new("RGB", (W, H), BACKDROP)
        tw, th, xs, y = grid_geometry(len(photos))
        for j, name in enumerate(photos):
            a = ease((t - s - m["interval"] * j) / m["fade"]) if m["type"] == "stagger" else 1.0
            if a <= 0:
                continue
            region = c.crop((xs[j], y, xs[j] + tw, y + th))
            c.paste(Image.blend(region, asset("tile", name, g, f"{tw}x{th}"), a), (xs[j], y))
    else:
        raise ValueError(f"{sh['id']}：未知版型 {lay}")
    return c


# ── 文字（Pencil 的字距＝每字後加固定 px，PIL 沒有，逐字排）──────────────
def font(name, size, wght=None):
    f = ImageFont.truetype(os.path.join(FONT_DIR, name), size)
    if wght is not None:
        f.set_variation_by_axes([wght])
    return f


def text_width(txt, f, ls):
    return sum(f.getlength(ch) for ch in txt) + ls * (len(txt) - 1)


def draw_text(layer, spec):
    """spec：text／font／size／wght／tracking／color／boxTop／boxH，水平用 x（左緣）或 cx（中心）。
    文字以字型 ascent+descent 在 Pencil 文字框內垂直置中。"""
    f = font(spec["font"], spec["size"], spec.get("wght"))
    ls = spec.get("tracking", 0)
    x = spec["x"] if "x" in spec else spec["cx"] - text_width(spec["text"], f, ls) / 2
    asc, desc = f.getmetrics()
    y = spec["boxTop"] + (spec["boxH"] - (asc + desc)) / 2
    d = ImageDraw.Draw(layer)
    fill = hex_rgba(spec["color"])
    for ch in spec["text"]:
        d.text((x, y), ch, font=f, fill=fill)
        x += f.getlength(ch) + ls


_layers = {}


def layer(key, painter):
    """以 key 快取一張全畫面 RGBA 圖層；painter(L) 負責畫內容。"""
    if key not in _layers:
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        painter(L)
        _layers[key] = L
    return _layers[key]


def text_layer(key, *specs):
    return layer(key, lambda L: [draw_text(L, s) for s in specs])


def over(base, lay, alpha=1.0):
    if alpha <= 0:
        return base
    if alpha < 1:
        a = lay.getchannel("A").point(lambda v: int(v * alpha))
        lay = lay.copy()
        lay.putalpha(a)
    out = base.convert("RGBA")
    out.alpha_composite(lay)
    return out.convert("RGB")


def black():
    return Image.new("RGB", (W, H))


# ── 片頭：focus-pull（對焦轉移）────────────────────────────────────────
def op_focus_pull_assets(P):
    return [("ld", P["photo"], P["grade"], round(P["scale"][0] * 100))]


def bottom_gradient(g):
    def paint(L):
        n = g["height"]
        a = np.zeros((H, W), np.uint8)
        a[H - n:, :] = np.linspace(0, round(g["alpha"] * 255), n).astype(np.uint8)[:, None]
        L.paste(Image.new("RGBA", (W, H), hex_rgb(g["color"]) + (0,)))
        L.putalpha(Image.fromarray(a))
    return layer("op-gradient", paint)


def op_focus_pull(t, P, dur, out):
    s0, s1, s2 = P["scale"]
    hold, fe = P["focusStart"], P["focusEnd"]
    src = asset("ld", P["photo"], P["grade"], round(s0 * 100))
    if t < hold:
        k, blur, bright = s0, P["blur"], P["brightness"]
    elif t < fe:
        q = ease((t - hold) / (fe - hold))
        k, blur, bright = lerp(s0, s1, q), lerp(P["blur"], 0, q), lerp(P["brightness"], 1.0, q)
    else:
        k, blur, bright = lerp(s1, s2, (t - fe) / (dur - fe)), 0, 1.0
    s = k / s0
    c = Image.new("RGB", (W, H))
    place_sub(c, src, W / 2 - src.width * s / 2, 0, s)  # 以畫面上緣中點為縮放基準
    if blur > 0.3:  # Pencil 的模糊半徑＝2σ；半解析度上做 σ/2 等效全解析度 σ
        small = c.resize((W // 2, H // 2), Image.BILINEAR).filter(ImageFilter.GaussianBlur(blur / 4))
        c = small.resize((W, H), Image.BICUBIC)
    if bright < 1:
        c = Image.blend(black(), c, bright)
    c = over(c, bottom_gradient(P["gradient"]))
    T = P["title"]
    if T["in"] <= t < fe:
        L = text_layer("op-title", T)
        if t < hold:
            c = over(c, L, ease((t - T["in"]) / T["fade"]))
        else:  # 大字糊掉、放大、淡出
            q = ease((t - hold) / (fe - hold))
            sc = lerp(1.0, T["exitScale"], q)
            box = T.get("exitBox") or L.getbbox()
            crop = L.crop(tuple(box))
            big = crop.resize((round(crop.width * sc), round(crop.height * sc)), Image.BICUBIC)
            if q > 0.01:
                big = big.filter(ImageFilter.GaussianBlur(lerp(0, T["exitBlur"] / 2, q)))
            cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            lay.alpha_composite(big, (round(cx - big.width / 2), round(cy - big.height / 2)))
            c = over(c, lay, 1 - q)
    S = P["subtitles"]
    if t >= S["in"]:
        c = over(c, text_layer("op-subtitles", *S["lines"]), ease((t - S["in"]) / S["fade"]))
    if t < P["fadeIn"]:  # 自黑場淡入
        c = Image.blend(black(), c, ease(t / P["fadeIn"]))
    if out["type"] == "black" and t >= dur - out["out"]:  # 淡出至黑，黑場溶接進第 1 章
        c = Image.blend(c, black(), (t - (dur - out["out"])) / out["out"])
    return c


OPENINGS = {"focus-pull": {"assets": op_focus_pull_assets, "render": op_focus_pull}}


# ── 片尾：photo-thanks-monogram（左照右字 → 字標）────────────────────────
def ed_ptm_assets(P):
    ph = P["photo"]
    return [("pt", ph["name"], ph["grade"], round(H * ph["push"][1]))]


def ed_thanks_layer(T):
    def paint(L):
        draw_text(L, T)
        o = T["ornament"]
        d = ImageDraw.Draw(L)
        cx, cy, col = T["cx"], o["y"], hex_rgba(o["color"])
        d.rectangle((cx - o["outer"], cy, cx - o["inner"], cy), fill=col)
        d.rectangle((cx + o["inner"], cy, cx + o["outer"], cy), fill=col)
        r = o["diamond"]
        d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], outline=col)
    return layer("ed-thanks", paint)


def ed_monogram_layer(M):
    def paint(L):
        D, st = M["ring"]["diameter"], M["ring"]["stroke"]
        cx, cy = W / 2, H / 2
        # 細圓框：以 4 倍解析度畫再縮回，邊緣才平滑
        big = Image.new("RGBA", (D * 4, D * 4), (0, 0, 0, 0))
        inset = st * 4 / 2
        ImageDraw.Draw(big).ellipse((inset, inset, D * 4 - inset, D * 4 - inset),
                                    outline=hex_rgba(M["ring"]["color"]), width=round(st * 4))
        L.alpha_composite(big.resize((D, D), Image.LANCZOS), (int(cx - D / 2), int(cy - D / 2)))
        draw_text(L, M["text"])
    return layer("ed-monogram", paint)


def ed_card(t, P):
    ph = P["photo"]
    c = Image.new("RGB", (W, H), BACKDROP)
    k0, k1 = ph["push"]
    k = lerp(k0, k1, min(1.0, t / ph["pushDur"]))
    pw = ph["panelWidth"]
    panel = Image.new("RGB", (pw, H))
    place_center(panel, asset("pt", ph["name"], ph["grade"], round(H * k1)), pw / 2, H / 2, k / k1, clip=(0, 0, pw, H))
    dm = ph["dim"]
    dark = dm["from"] if t < dm["at"] else lerp(dm["from"], dm["to"], min(1.0, (t - dm["at"]) / dm["dur"]))
    panel = Image.blend(panel, Image.new("RGB", panel.size, BACKDROP), dark)
    c.paste(panel, (0, 0))
    dv = P["divider"]
    line = Image.new("RGB", (dv["width"], H), hex_rgb(dv["color"]))
    c.paste(Image.blend(Image.new("RGB", (dv["width"], H), BACKDROP), line, dv["alpha"]), (pw, 0))
    T = P["thanks"]
    if t >= T["in"]:
        c = over(c, ed_thanks_layer(T), ease((t - T["in"]) / T["fade"]))
    for j, ln in enumerate(P["lines"]):
        if t >= ln["in"]:
            c = over(c, text_layer(f"ed-line{j}", ln), ease((t - ln["in"]) / ln["fade"]))
    return c


def ed_photo_thanks_monogram(t, P, dur, prev_out):
    M = P["monogram"]
    logo = over(Image.new("RGB", (W, H), hex_rgb(M["bg"])), ed_monogram_layer(M))
    if t < M["in"]:
        c = ed_card(t, P)
    elif t < M["in"] + M["dissolve"]:  # 溶接 → 深色底字標
        c = Image.blend(ed_card(t, P), logo, ease((t - M["in"]) / M["dissolve"]))
    else:
        c = logo
    if prev_out["type"] == "black" and t < prev_out["in"]:  # 自黑場淡入
        c = Image.blend(black(), c, ease(t / prev_out["in"]))
    if t >= dur - P["fadeOut"]:  # 最後淡出至全黑
        c = Image.blend(c, black(), (t - (dur - P["fadeOut"])) / P["fadeOut"])
    return c


ENDINGS = {"photo-thanks-monogram": {"assets": ed_ptm_assets, "render": ed_photo_thanks_monogram}}


# ── 轉場 ──────────────────────────────────────────────────────────────
# 交疊型（dissolve／push）：以切點為中心，前後各半；回傳兩鏡合成的整格
# 覆蓋型（black／flash）：疊在單鏡畫面上，切點前改本鏡尾、切點後改下一鏡頭
def overlap_window(tr):
    if tr["type"] in ("dissolve", "push"):
        return tr["duration"] / 2
    return None


def overlap_render(i, t, cut, tr):
    half = tr["duration"] / 2
    q = ease((t - (cut - half)) / tr["duration"])
    if tr["type"] == "dissolve":
        return Image.blend(render_shot(i, t), render_shot(i + 1, t), q)
    d = 1 if tr["dir"] == "right" else -1  # push：箭頭＝畫面移動方向
    c = black()
    c.paste(render_shot(i, t), (round(d * q * W), 0))
    c.paste(render_shot(i + 1, t), (round(d * (q - 1) * W), 0))
    return c


def overlay_tail(c, t, e, tr):
    if tr["type"] == "black" and t >= e - tr["out"]:
        return Image.blend(c, black(), (t - (e - tr["out"])) / tr["out"])
    if tr["type"] == "flash" and t >= e - tr["pre"]:
        return Image.blend(c, Image.new("RGB", (W, H), (255, 255, 255)), tr["peak"] * (t - (e - tr["pre"])) / tr["pre"])
    return c


def overlay_head(c, t, s, tr):
    if tr["type"] == "black" and t < s + tr["in"]:
        return Image.blend(black(), c, ease((t - s) / tr["in"]))
    if tr["type"] == "flash" and t < s + tr["post"]:
        return Image.blend(c, Image.new("RGB", (W, H), (255, 255, 255)), tr["peak"] * (1 - (t - s) / tr["post"]))
    return c


# ── 時間軸合成 ───────────────────────────────────────────────────────
def frame(t):
    op, ed = SB["opening"], SB["ending"]
    if t < op["end"]:
        return OPENINGS[op["style"]]["render"](t - op["start"], op["params"], op["end"] - op["start"], op["out"])
    if t >= ed["start"]:
        return ENDINGS[ed["style"]]["render"](t - ed["start"], ed["params"], ed["end"] - ed["start"], SHOTS[-1]["out"])
    i = next(j for j, sh in enumerate(SHOTS) if sh["start"] <= t < sh["end"])
    s, e, out = SHOTS[i]["start"], SHOTS[i]["end"], SHOTS[i]["out"]
    prev = SHOTS[i - 1]["out"] if i > 0 else op["out"]
    half = overlap_window(out)
    if half is not None and i + 1 < len(SHOTS) and t >= e - half:
        return overlap_render(i, t, e, out)
    half = overlap_window(prev)
    if half is not None and i > 0 and t < s + half:
        return overlap_render(i - 1, t, s, prev)
    c = render_shot(i, t)
    c = overlay_tail(c, t, e, out)
    return overlay_head(c, t, s, prev)


def render_index(n):
    return frame(n / FPS).tobytes()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prep", "still", "video"])
    ap.add_argument("storyboard")
    ap.add_argument("args", nargs="*")
    ap.add_argument("--work")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    ap.add_argument("--start", type=float, default=0.0, help="video：只輸出片段（預覽用）的起點秒數")
    ap.add_argument("--end", type=float, help="video：片段終點秒數，預設為全長")
    a = ap.parse_args()
    setup(a.storyboard, a.work)
    os.makedirs(CACHE, exist_ok=True)
    init = (setup, (a.storyboard, a.work))
    if a.cmd == "prep":
        jobs = prep_jobs()
        with Pool(a.jobs, *init) as pool:
            for k, _ in enumerate(pool.imap_unordered(prep_one, jobs), 1):
                print(f"prep {k}/{len(jobs)}", flush=True)
    elif a.cmd == "still":
        outdir = os.path.join(WORK, "stills")
        os.makedirs(outdir, exist_ok=True)
        for ts in a.args:
            path = os.path.join(outdir, f"t{float(ts):07.2f}.png")
            frame(float(ts)).save(path)
            print("still", path, flush=True)
    elif a.cmd == "video":
        out = a.args[0]
        v, au = SB["output"]["video"], SB["output"]["audio"]
        start, end = a.start, a.end if a.end is not None else DUR
        frames = range(round(start * FPS), round(end * FPS))
        n = len(frames)
        ff = subprocess.Popen([
            "ffmpeg", "-v", "error", "-y",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-ss", str(start), "-i", SB["audio"]["file"],
            "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
            "-c:v", v["codec"], "-preset", v["preset"], "-crf", str(v["crf"]),
            "-maxrate", v["maxrate"], "-bufsize", v["bufsize"],
            "-profile:v", v["profile"], "-level", v["level"],
            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
            "-c:a", au["codec"], "-b:a", au["bitrate"], "-ar", str(au["rate"]),
            "-t", str(end - start), "-movflags", "+faststart", out,
        ], stdin=subprocess.PIPE)
        with Pool(a.jobs, *init) as pool:
            for k, buf in enumerate(pool.imap(render_index, frames, chunksize=6)):
                ff.stdin.write(buf)
                if k % 300 == 0:
                    print(f"frame {k}/{n}", flush=True)
        ff.stdin.close()
        ff.wait()
        print("done", ff.returncode, flush=True)


if __name__ == "__main__":
    main()
