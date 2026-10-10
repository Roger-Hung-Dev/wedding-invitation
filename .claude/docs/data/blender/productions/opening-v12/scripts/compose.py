# -*- coding: utf-8 -*-
"""
開場影片 V12「押花情書・紙質手寫風」合成器
3D 影格（D:\\render-work\\opening-v12\\shots）＋ 2D 手寫字幕／大標／手繪元素 ＋ 轉場 → 成品 mp4（無聲）。

依據（衝突時上面優先）：
  1. .claude/docs/storyboard/opening-v12-production.md
  2. productions/opening-v12/compose-handoff.md（影格、72 秒時間軸、分層、track.json、每幕 2D 元素）
  3. .claude/docs/storyboard/wedding-becarefulinfo-show-plan-2.md 版本 12（字幕原文）

用法（系統 Python 3，需要 Pillow＋numpy；不用 Blender）：
  python compose.py prep                       量測快取：③ 進度條推進、⑦ 黑板位置（其他指令缺快取時會自動跑）
  python compose.py check                      列出每段字的墨跡外框、是否在安全框內、字級
  python compose.py still 3.0 17.6 …           成品時間點 → <WORK>/stills/t017.60.png
  python compose.py sheet out.png 3.0 17.6 …   多個時間點拼成一張縮圖表（檢查用）
  python compose.py video [--start S] [--end E] [--out 路徑] [--crf 18] [--jobs N]
  python compose.py web                        成品 → 1280×720 網頁版（目標 ≤ 15 MB）
  python compose.py cover 21.6                 封面 jpg（1920×1080，取成品時間點）

工作目錄 <WORK>＝D:\\render-work\\opening-v12\\compose（字型 fonts/、量測快取 cache/、抽格 stills/）。
字型：霞鶩文楷 LXGW WenKai TC Bold、Pinyon Script（OFL），放 <WORK>/fonts，不裝進系統。
"""
import argparse
import functools
import json
import math
import os
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

# ════════════════════════════════════════════════════════════════════════
# 路徑與規格
# ════════════════════════════════════════════════════════════════════════
W, H, FPS = 1920, 1080, 30
DUR = 72.0
NF = int(round(DUR * FPS))                    # 2160 格
HERE = os.path.dirname(os.path.abspath(__file__))
PROD = os.path.dirname(HERE)                  # productions/opening-v12
SHOTS = os.environ.get("V12_SHOTS", r"D:\render-work\opening-v12\shots")
WORK = os.environ.get("V12_WORK", r"D:\render-work\opening-v12\compose")
FONT_DIR = os.path.join(WORK, "fonts")
CACHE = os.path.join(WORK, "cache")
OUT = os.path.join(PROD, "videos", "opening-v12.mp4")
OUT_WEB = os.path.join(PROD, "videos", "opening-v12-web.mp4")
OUT_COVER = os.path.join(PROD, "videos", "opening-v12.jpg")

# 配色（plan-2 版本 12）
INK = (0x4A, 0x3B, 0x35)        # 墨褐：字色
ROSE = (0xD9, 0x77, 0x7F)       # 乾燥玫瑰：名字
ROSE_EDGE = (0xB2, 0x5B, 0x65)  # 玫瑰字的 1px 深色邊（棉紙底上對比不足時補強字緣）
HALO = (0xFB, 0xF7, 0xF0)       # 墨褐字的 2px 描邊（棉紙白）
PAPER = (0xF8, 0xF2, 0xE9)      # 信紙條
LAV = (0xB8, 0xA1, 0xC9)        # 薰衣草紫：徽章
LAV_EDGE = (0x8C, 0x75, 0xA1)
SHADOW = (0x3C, 0x2E, 0x28)

# 字級（長輩規則：主句 ≥ 72、大標 ≥ 140、標籤 72）
MAIN = 84
BIG = 140
LABEL = 72
PEN = 0.07          # 鋼筆逐字：每字秒數
REVEAL = 0.16       # 單字從開始寫到寫完（與下一字重疊，看起來是連續的筆跡）
FADE_OUT = 0.25     # 字幕在訖點前 0.25 秒淡出，訖點時完全消失
SAFE = (96, 54, 1824, 1026)


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x, p=3):
    x = clamp(x)
    return 1 - (1 - x) ** p


def ease_in(x, p=3):
    x = clamp(x)
    return x ** p


def back_out(x, s=1.7):
    x = clamp(x) - 1
    return 1 + x * x * ((s + 1) * x + s)


def lerp(a, b, w):
    return a + (b - a) * w


# ════════════════════════════════════════════════════════════════════════
# 3D 影格
# ════════════════════════════════════════════════════════════════════════
# 序列 → (第 1 格的本幕秒數, 格數)；影格 n ＝ 本幕秒數 t0 + (n−1)/30（compose-handoff §2）
SEQ = {"01": (0.0, 234), "02a": (0.0, 33), "02": (0.5, 249), "03": (0.0, 264), "04": (0.0, 294),
       "05": (0.0, 294), "06": (0.0, 354), "07": (0.0, 300), "08a": (0.0, 198), "08": (5.8, 108),
       "08c": (8.6, 42)}


def fidx(seq, tl):
    """本幕秒數 → 影格編號（1 起算）。早於第 1 格時停在第 1 格（handoff：頭沒有多渲，切點前停在第 1 格）。"""
    t0, n = SEQ[seq]
    return max(1, min(n, int(math.floor((tl - t0) * FPS + 0.5 + 1e-6)) + 1))


@functools.lru_cache(maxsize=8)
def _png(seq, layer, n):
    return Image.open(os.path.join(SHOTS, seq, layer, "%04d.png" % n)).convert("RGBA")


def shot(seq, tl, layer="beauty"):
    return _png(seq, layer, fidx(seq, tl))


@functools.lru_cache(maxsize=None)
def track(seq):
    with open(os.path.join(SHOTS, seq, "track.json"), encoding="utf-8") as f:
        return json.load(f)


def quad(seq, region, n):
    d = track(seq)
    n = max(1, min(len(d), n))
    return np.array([p[:2] for p in d[str(n)][region]], float)


def homog(src, dst):
    """4 點對 4 點的投影矩陣（src → dst）。"""
    A, b = [], []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); b.append(v)
    h = np.linalg.solve(np.array(A, float), np.array(b, float))
    return np.append(h, 1.0).reshape(3, 3)


def apply_h(Hm, pts):
    pts = np.asarray(pts, float)
    p = np.c_[pts, np.ones(len(pts))] @ Hm.T
    return p[:, :2] / p[:, 2:3]


def T(dx, dy):
    return np.array([[1, 0, dx], [0, 1, dy], [0, 0, 1]], float)


def rect(w, h):
    return np.array([[0, 0], [w, 0], [w, h], [0, h]], float)


# ════════════════════════════════════════════════════════════════════════
# 合成小工具
# ════════════════════════════════════════════════════════════════════════
def mul_alpha(img, a):
    if a >= 0.999:
        return img
    r, g, b, al = img.split()
    lut = [int(v * a + 0.5) for v in range(256)]
    return Image.merge("RGBA", (r, g, b, al.point(lut)))


def paste(base, img, x, y, alpha=1.0):
    """裁掉超出畫面的部分再 alpha 疊上（PIL 的 alpha_composite 不收負座標）。"""
    if img is None or alpha <= 0.001:
        return
    img = mul_alpha(img, alpha)
    x, y = int(round(x)), int(round(y))
    w, h = img.size
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(w, W - x), min(h, H - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    if (sx0, sy0, sx1, sy1) != (0, 0, w, h):
        img = img.crop((sx0, sy0, sx1, sy1))
    base.alpha_composite(img, (x + sx0, y + sy0))


def paste_h(base, img, Hm, alpha=1.0):
    """局部圖（左上原點）經投影矩陣 Hm（局部 → 畫面）貼到畫面；預乘 alpha 再取樣，字邊不會有黑邊。"""
    if img is None or alpha <= 0.001:
        return
    w, h = img.size
    c = apply_h(Hm, rect(w, h))
    x0, y0 = np.floor(c.min(0)).astype(int) - 2
    x1, y1 = np.ceil(c.max(0)).astype(int) + 2
    x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, W), min(y1, H)
    if x1 <= x0 or y1 <= y0:
        return
    M = np.linalg.inv(Hm) @ T(x0, y0)
    M = M / M[2, 2]
    out = img.convert("RGBa").transform((x1 - x0, y1 - y0), Image.PERSPECTIVE, tuple(M.flatten()[:8]),
                                        Image.BICUBIC)
    paste(base, out.convert("RGBA"), x0, y0, alpha)


def supersample(draw_fn, w, h, k=3):
    """在 k 倍畫布上畫（PIL 的線條沒有反鋸齒），再縮回。draw_fn(ImageDraw, k)。"""
    big = Image.new("RGBA", (int(w * k), int(h * k)), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(big), k)
    return big.resize((int(w), int(h)), Image.LANCZOS)


def polyline_cut(pts, frac):
    """折線取前 frac 比例的長度。"""
    pts = np.asarray(pts, float)
    seg = np.hypot(*np.diff(pts, axis=0).T)
    L = seg.sum()
    if frac >= 1:
        return pts
    goal, acc, out = L * max(frac, 0), 0.0, [pts[0]]
    for i, s in enumerate(seg):
        if acc + s >= goal:
            w = (goal - acc) / s if s > 0 else 0
            out.append(pts[i] + (pts[i + 1] - pts[i]) * w)
            return np.array(out)
        out.append(pts[i + 1])
        acc += s
    return np.array(out)


def thick_line(d, pts, width, fill):
    """圓頭圓角的粗線（每個轉折補一個圓）。"""
    pts = [tuple(p) for p in pts]
    if len(pts) >= 2:
        d.line(pts, fill=fill, width=int(round(width)), joint="curve")
    r = width / 2
    for p in (pts[0], pts[-1]) if pts else ():
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=fill)


# ════════════════════════════════════════════════════════════════════════
# 字型與手寫字
# ════════════════════════════════════════════════════════════════════════
FONT_FILES = {"wk": "LXGWWenKaiTC-Bold.ttf", "pinyon": "PinyonScript-Regular.ttf"}


@functools.lru_cache(maxsize=None)
def font(key, size):
    path = os.path.join(FONT_DIR, FONT_FILES[key])
    if not os.path.exists(path):
        raise FileNotFoundError(f"缺字型 {path}（霞鶩文楷 TC Bold／Pinyon Script 放在 <WORK>/fonts）")
    return ImageFont.truetype(path, size)


def line_width(runs, size):
    w = 0.0
    for run in runs:
        f = font(run[2] if len(run) > 2 else "wk", int(round(size * (run[3] if len(run) > 3 else 1.0))))
        w += sum(f.getlength(ch) for ch in run[0])
    return w


class Text:
    """鋼筆手寫字：逐字斜向擦出、墨水微暈（寫下時暈開再收）、2px 棉紙白描邊。

    lines：每行是 str，或 runs 清單 [(文字, 顏色[, 字型鍵, 字級倍率]), …]（名字換玫瑰色、& 用 Pinyon Script）。
    座標在「目標空間」：畫面像素，或某個局部畫布（再經投影貼到信紙上）。cx＝行中心（align=center）或左緣，
    base＝第一行基線，行距＝pitch × size。t0 起寫、每字 speed 秒；t1 前 fade_out 秒淡出。
    """
    F = 0.45  # 擦出邊緣羽化

    def __init__(self, lines, size, t0, t1, cx, base, pitch=1.3, speed=PEN, align="center", color=INK,
                 fade_out=FADE_OUT, fade_in=0.0, reveal=REVEAL, name=""):
        self.t0, self.t1, self.fade_out, self.fade_in, self.reveal = t0, t1, fade_out, fade_in, reveal
        self.size, self.name = size, name
        self.sig = max(1.5, size * 0.04)
        glyphs, k = [], 0
        self.lines_w = []
        for li, line in enumerate(lines):
            runs = [(line, color)] if isinstance(line, str) else line
            wl = line_width(runs, size)
            self.lines_w.append(wl)
            x0 = cx - wl / 2 if align == "center" else (cx if align == "left" else cx - wl)
            by = base + li * pitch * size
            x = x0
            for run in runs:
                txt, col = run[0], run[1]
                f = font(run[2] if len(run) > 2 else "wk", int(round(size * (run[3] if len(run) > 3 else 1.0))))
                for ch in txt:
                    adv = f.getlength(ch)
                    if ch.strip():
                        l, t, r, b = f.getbbox(ch, anchor="ls")
                        pad = 2
                        m = Image.new("L", (r - l + 2 * pad, b - t + 2 * pad), 0)
                        ImageDraw.Draw(m).text((pad - l, pad - t), ch, font=f, fill=255, anchor="ls")
                        glyphs.append(dict(ch=ch, m=m, x=int(round(x + l - pad)), y=int(round(by + t - pad)),
                                           col=col, ts=t0 + k * speed))
                        k += 1
                    x += adv
        self.glyphs = glyphs
        self.t_done = (glyphs[-1]["ts"] if glyphs else t0) + reveal
        self.t_steady = self.t_done + 0.9
        # 畫布範圍（含描邊與暈開的邊）
        mg = int(math.ceil(2 + 3 * self.sig + 3))
        self.ox = min(g["x"] for g in glyphs) - mg
        self.oy = min(g["y"] for g in glyphs) - mg
        self.w = max(g["x"] + g["m"].size[0] for g in glyphs) + mg - self.ox
        self.h = max(g["y"] + g["m"].size[1] for g in glyphs) + mg - self.oy
        for g in glyphs:
            gw, gh = g["m"].size
            big = Image.new("L", (gw + 2 * mg, gh + 2 * mg), 0)
            big.paste(g["m"], (mg, mg))
            rose = g["col"] == ROSE
            sw = 1 if rose else 2                      # 墨褐字 2px 棉紙白描邊；玫瑰字 1px 深玫瑰邊
            g["halo"] = ROSE_EDGE if rose else HALO
            S = big.filter(ImageFilter.MaxFilter(2 * sw + 1)).filter(ImageFilter.GaussianBlur(0.6))
            B = big.filter(ImageFilter.GaussianBlur(self.sig))
            g["A"] = np.asarray(big, np.float32) / 255.0
            g["S"] = np.asarray(S, np.float32) / 255.0
            g["B"] = np.asarray(B, np.float32) / 255.0
            # 擦出座標：在字的墨跡框裡由左上往右下 0→1
            bb = g["m"].getbbox() or (0, 0, gw, gh)
            yy, xx = np.mgrid[0:gh + 2 * mg, 0:gw + 2 * mg].astype(np.float32)
            xn = (xx - (mg + bb[0])) / max(1, bb[2] - bb[0])
            yn = (yy - (mg + bb[1])) / max(1, bb[3] - bb[1])
            g["u"] = np.clip(0.78 * xn + 0.22 * yn, 0, 1)
            g["px"], g["py"] = g["x"] - mg - self.ox, g["y"] - mg - self.oy
            del g["m"]
        self._steady = None

    def ink_box(self):
        """所有字墨跡（不含描邊）的外框，目標空間座標。"""
        xs0 = [self.ox + g["px"] + np.nonzero(g["A"].max(0) > 0.3)[0].min() for g in self.glyphs]
        xs1 = [self.ox + g["px"] + np.nonzero(g["A"].max(0) > 0.3)[0].max() for g in self.glyphs]
        ys0 = [self.oy + g["py"] + np.nonzero(g["A"].max(1) > 0.3)[0].min() for g in self.glyphs]
        ys1 = [self.oy + g["py"] + np.nonzero(g["A"].max(1) > 0.3)[0].max() for g in self.glyphs]
        return min(xs0), min(ys0), max(xs1), max(ys1)

    def _compose(self, t):
        C = np.zeros((self.h, self.w, 3), np.float32)
        A = np.zeros((self.h, self.w), np.float32)

        def over(x, y, a, col):
            hh, ww = a.shape
            Cs, As = C[y:y + hh, x:x + ww], A[y:y + hh, x:x + ww]
            inv = 1.0 - a
            Cs *= inv[..., None]
            Cs += a[..., None] * (np.array(col, np.float32) / 255.0)
            As *= inv
            As += a

        for g in self.glyphs:
            r = (t - g["ts"]) / self.reveal
            if r <= 0:
                break
            wp = 1.0 if r >= 1 else np.clip((r * (1 + self.F) - g["u"]) / self.F, 0, 1)
            age = t - g["ts"] - self.reveal
            bloom = 0.30 * min(r, 1.0) if age < 0 else 0.05 + 0.25 * math.exp(-age / 0.22)
            over(g["px"], g["py"], g["S"] * wp, g["halo"])
            over(g["px"], g["py"], g["B"] * wp * bloom, g["col"])
            over(g["px"], g["py"], g["A"] * wp, g["col"])
        col = C / np.maximum(A, 1e-6)[..., None]
        out = np.dstack([col * 255.0, A[..., None] * 255.0]).clip(0, 255).astype(np.uint8)
        return Image.fromarray(out, "RGBA")

    def alpha(self, t):
        if t < self.t0 or t >= self.t1:
            return 0.0
        a = 1.0
        if self.fade_out > 0:
            a *= clamp((self.t1 - t) / self.fade_out)
        if self.fade_in > 0:
            a *= smooth((t - self.t0) / self.fade_in)
        return a

    def render(self, t):
        """→ (RGBA 圖, 左上 x, 左上 y, 不透明度) 或 None。"""
        a = self.alpha(t)
        if a <= 0:
            return None
        if t >= self.t_steady:
            if self._steady is None:
                self._steady = self._compose(self.t_steady)
            img = self._steady
        else:
            img = self._compose(t)
        return img, self.ox, self.oy, a

    def draw(self, base, t, Hm=None):
        r = self.render(t)
        if r is None:
            return
        img, ox, oy, a = r
        if Hm is None:
            paste(base, img, ox, oy, a)
        else:
            paste_h(base, img, Hm @ T(ox, oy), a)


def static_text(s, size, color=INK):
    """寫好的靜態字（計數數字用）。"""
    tx = Text([[(s, color)]], size, -10, 1e9, 0, 0, align="left", fade_out=0)
    img, ox, oy, _ = tx.render(100.0)
    return img, ox, oy, tx


# ════════════════════════════════════════════════════════════════════════
# 2D 手繪元素
# ════════════════════════════════════════════════════════════════════════
class Strip:
    """半透明信紙條（花園幕的字幕底）：毛邊、紙纖維、柔和投影；淡入時往下滑 12px。"""

    def __init__(self, box, t_in, t_out, seed=1, alpha=0.9):
        self.t_in, self.t_out = t_in, t_out
        x0, y0, x1, y1 = box
        w, h = x1 - x0, y1 - y0
        mg = 30
        k = 2
        rng = np.random.default_rng(seed)
        # 毛邊：沿四邊取點，外推 ±2.5px 的平滑雜訊
        pts = []

        def noise(n, amp):
            v = np.zeros(n)
            for f in (3, 7, 17, 41):
                v += np.sin(np.linspace(0, f * math.pi * 2, n) + rng.uniform(0, 6.3)) * amp / f ** 0.6
            return v + rng.normal(0, amp * 0.25, n)

        for (ax, ay), (bx, by), (nx, ny) in [((0, 0), (w, 0), (0, -1)), ((w, 0), (w, h), (1, 0)),
                                             ((w, h), (0, h), (0, 1)), ((0, h), (0, 0), (-1, 0))]:
            n = int(max(abs(bx - ax), abs(by - ay)) / 5) + 2
            nz = noise(n, 2.6)
            for i in range(n - 1):
                s = i / (n - 1)
                pts.append(((mg + ax + (bx - ax) * s + nx * nz[i]) * k, (mg + ay + (by - ay) * s + ny * nz[i]) * k))
        msk = Image.new("L", ((w + 2 * mg) * k, (h + 2 * mg) * k), 0)
        ImageDraw.Draw(msk).polygon(pts, fill=255)
        msk = msk.resize((w + 2 * mg, h + 2 * mg), Image.LANCZOS)
        fib = rng.normal(0, 1, (h + 2 * mg, w + 2 * mg)).astype(np.float32)
        fib = np.asarray(Image.fromarray(((fib * 18) + 128).clip(0, 255).astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(0.8)), np.float32) - 128
        base = np.array(PAPER, np.float32)[None, None, :] + fib[..., None] * 0.35
        a = np.asarray(msk, np.float32) / 255.0
        paper = np.dstack([base, a[..., None] * 255 * alpha]).clip(0, 255).astype(np.uint8)
        paper = Image.fromarray(paper, "RGBA")
        sh = Image.new("RGBA", paper.size, SHADOW + (0,))
        sa = msk.filter(ImageFilter.GaussianBlur(9)).point(lambda v: int(v * 0.24))
        sh.putalpha(sa)
        out = Image.new("RGBA", paper.size, (0, 0, 0, 0))
        out.alpha_composite(sh, (0, 6))
        out.alpha_composite(paper)
        self.img, self.x, self.y = out, x0 - mg, y0 - mg

    def draw(self, base, t):
        if t < self.t_in or t > self.t_out:
            return
        a = smooth((t - self.t_in) / 0.3) * smooth((self.t_out - t) / 0.3)
        dy = -12 * (1 - ease_out((t - self.t_in) / 0.35))
        paste(base, self.img, self.x, self.y + dy, a)


class Counter:
    """③ 大標的百分比：跟著 3D 進度條數上去（量測值），2.2s 停在 99%（顫動），2.64s 跳 100%（彈一下、轉玫瑰色）。"""

    def __init__(self, table, x_left, base, size, t0, t1, t99=2.2, jump=2.64, fade_out=0.15):
        self.table, self.x, self.base, self.size = table, x_left, base, size
        self.t0, self.t1, self.t99, self.jump, self.fade_out = t0, t1, t99, jump, fade_out
        self.cache = {}

    def value(self, tl):
        if tl >= self.jump:
            return 100
        n = fidx("03", tl)
        return int(self.table.get(str(n), 99))

    def draw(self, base, tl):
        if tl < self.t0 or tl >= self.t1:
            return
        v = self.value(tl)
        key = (v, v == 100)
        if key not in self.cache:
            self.cache[key] = static_text(f"{v}%", self.size, ROSE if v == 100 else INK)[:3]
        img, ox, oy = self.cache[key]
        a = smooth((tl - self.t0) / 0.2) * clamp((self.t1 - tl) / self.fade_out)
        dx = dy = 0.0
        if self.t99 <= tl < self.jump:                  # 第 10 朵卡住顫動：數字跟著抖
            dx = 2.5 * math.sin(2 * math.pi * 13 * tl)
            dy = 1.0 * math.sin(2 * math.pi * 9 * tl)
        x, y = self.x + ox + dx, self.base + oy + dy
        if tl >= self.jump:                             # 100% 彈出
            s = 1 + 0.22 * (1 - ease_out((tl - self.jump) / 0.3))
            if s > 1.001:
                w, h = img.size
                cx, cy = x + w / 2, y + h * 0.62
                img = img.resize((int(w * s), int(h * s)), Image.BICUBIC)
                x, y = cx - img.size[0] / 2, cy - img.size[1] * 0.62
        paste(base, img, x, y, a)


class Brackets:
    """⑤ 觀景窗括線：畫面四角手繪的 L 形括線（墨褐＋棉紙白暈邊），t0 起 0.4 秒畫出。"""

    def __init__(self, t0, inset=72, arm=130, width=7):
        self.t0, self.width = t0, width
        rng = np.random.default_rng(5)
        self.corners = []
        for (cx, cy), (dx, dy) in [((inset, inset), (1, 1)), ((W - inset, inset), (-1, 1)),
                                   ((W - inset, H - inset), (-1, -1)), ((inset, H - inset), (1, -1))]:
            pts = []
            for i in range(13):                      # 橫臂：端點 → 角
                s = 1 - i / 12
                pts.append((cx + dx * arm * s, cy + rng.normal(0, 0.8) * (0.3 + s)))
            for i in range(1, 13):                   # 直臂：角 → 端點
                s = i / 12
                pts.append((cx + rng.normal(0, 0.8) * (0.3 + s), cy + dy * arm * s))
            pts = np.array(pts)
            x0, y0 = pts.min(0) - 16
            self.corners.append((pts - [x0, y0], int(x0), int(y0), int(arm + 34)))
        self.full = None

    def _corner(self, pts, size, frac):
        pp = polyline_cut(pts, frac)

        def dr(d, k):
            q = pp * k
            thick_line(d, q, (self.width + 6) * k, HALO + (215,))
            thick_line(d, q, self.width * k, INK + (255,))
        return supersample(dr, size, size)

    def draw(self, base, tl):
        p = ease_out((tl - self.t0) / 0.4)
        if p <= 0:
            return
        if p >= 1 and self.full is None:
            self.full = [self._corner(pts, s, 1.0) for pts, _, _, s in self.corners]
        for i, (pts, x0, y0, s) in enumerate(self.corners):
            img = self.full[i] if p >= 1 else self._corner(pts, s, p)
            paste(base, img, x0, y0)


class CutOut:
    """⑤ 手繪剪紙人形：從右側滑入擋住鏡頭，鋼筆在它身上畫 ✕，再滑出（6.3～7.8s）。"""

    def __init__(self, t_in=6.3, cx=1340, top=330):
        self.t_in = t_in
        self.t_s1, self.t_s2, self.ts_len = 6.78, 7.06, 0.24     # 兩筆 ✕ 的開始與長度
        self.t_out0, self.t_out1 = 7.42, 7.8
        cw, ch = 640, 900
        mg = 40
        k = 3
        rng = np.random.default_rng(9)
        # 人形輪廓（頭、脖子、圓肩身體），毛邊
        msk = Image.new("L", ((cw + 2 * mg) * k, (ch + 2 * mg) * k), 0)
        d = ImageDraw.Draw(msk)
        ox = mg * k
        d.ellipse([ox + 212 * k, ox + 40 * k, ox + 428 * k, ox + 256 * k], fill=255)       # 頭
        d.rectangle([ox + 282 * k, ox + 230 * k, ox + 358 * k, ox + 320 * k], fill=255)    # 脖子
        d.rounded_rectangle([ox + 60 * k, ox + 300 * k, ox + 580 * k, ox + (ch + 200) * k], radius=170 * k,
                            fill=255)                                                    # 身體
        msk = msk.resize((cw + 2 * mg, ch + 2 * mg), Image.LANCZOS)
        a = np.asarray(msk, np.float32) / 255.0
        nz = np.asarray(Image.fromarray((rng.normal(128, 40, a.shape)).clip(0, 255).astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(1.2)), np.float32) / 255.0
        edge = np.clip((a - 0.5) * 2.2 + (nz - 0.5) * 0.9, 0, 1) * (a > 0.02)   # 毛邊
        paper_col = np.array((0xF3, 0xEA, 0xDC), np.float32)
        fib = (np.asarray(Image.fromarray(rng.normal(128, 30, a.shape).clip(0, 255).astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(0.7)), np.float32) - 128) * 0.12
        rim = np.asarray(Image.fromarray((edge * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(7)),
                         np.float32) / 255.0
        shade = (edge - rim).clip(0, 1)[..., None] * np.array((-38, -42, -46), np.float32)  # 邊緣一圈略深
        col = (paper_col[None, None] + fib[..., None] + shade).clip(0, 255)
        sil = Image.fromarray(np.dstack([col, edge[..., None] * 255]).astype(np.uint8), "RGBA")
        sh = Image.new("RGBA", sil.size, SHADOW + (0,))
        sh.putalpha(Image.fromarray((edge * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(16)).point(
            lambda v: int(v * 0.38)))
        body = Image.new("RGBA", (sil.size[0] + 30, sil.size[1] + 30), (0, 0, 0, 0))
        body.alpha_composite(sh, (18, 14))
        body.alpha_composite(sil)
        self.body = body
        self.x0, self.y0 = cx - cw / 2 - mg, top - 40 - mg
        # ✕ 兩筆（局部座標，含邊距）
        o = mg
        self.strokes = [(np.array([o + 205, o + 430.0]), np.array([o + 440, o + 700.0])),
                        (np.array([o + 440, o + 430.0]), np.array([o + 205, o + 700.0]))]
        self.stroke_imgs = []
        for p0, p1 in self.strokes:
            def dr(dd, kk, p0=p0, p1=p1):
                n = 24
                pts = []
                nrm = np.array([-(p1 - p0)[1], (p1 - p0)[0]]) / np.hypot(*(p1 - p0))
                for i in range(n + 1):
                    s = i / n
                    pts.append((p0 + (p1 - p0) * s + nrm * 9 * math.sin(math.pi * s)) * kk)
                thick_line(dd, pts, 19 * kk, INK + (255,))
            self.stroke_imgs.append(supersample(dr, *body.size))
        bh, bw = body.size[1], body.size[0]
        yy, xx = np.mgrid[0:bh, 0:bw].astype(np.float32)
        self.proj = []
        for p0, p1 in self.strokes:
            v = (p1 - p0) / np.hypot(*(p1 - p0))
            self.proj.append(((xx - p0[0]) * v[0] + (yy - p0[1]) * v[1]) / np.hypot(*(p1 - p0)))
        self.pen = self._pen()

    def _pen(self):
        """鋼筆（筆尖朝左下）。回傳 (圖, 筆尖在圖中的位置)。"""
        L, Wd = 300, 44

        def dr(d, k):
            d.rounded_rectangle([0, 0, Wd * k, 225 * k], radius=20 * k, fill=(0x3E, 0x2E, 0x28, 255))
            d.rectangle([6 * k, 18 * k, 12 * k, 200 * k], fill=(0x6A, 0x55, 0x4C, 255))       # 反光
            d.rectangle([0, 180 * k, Wd * k, 196 * k], fill=(0xC9, 0xA4, 0x5C, 255))           # 金環
            d.rounded_rectangle([5 * k, 222 * k, (Wd - 5) * k, 252 * k], radius=6 * k, fill=(0x2E, 0x22, 0x1E, 255))
            d.polygon([(7 * k, 250 * k), ((Wd - 7) * k, 250 * k), (Wd / 2 * k, L * k)], fill=(0xD8, 0xB4, 0x6A, 255))
            d.line([(Wd / 2 * k, 262 * k), (Wd / 2 * k, (L - 8) * k)], fill=(0x8A, 0x6A, 0x30, 255), width=2 * k)
        img = supersample(dr, Wd, L)
        ang = -38.0                                   # 逆時針為正：負值＝筆身往右上
        rot = img.rotate(ang, resample=Image.BICUBIC, expand=True)
        # 筆尖 (Wd/2, L) 繞中心旋轉後的位置
        cx, cy = Wd / 2, L / 2
        a = math.radians(ang)
        tx, ty = Wd / 2 - cx, L - cy
        nx = tx * math.cos(a) + ty * math.sin(a)
        ny = -tx * math.sin(a) + ty * math.cos(a)
        return rot, (rot.size[0] / 2 + nx, rot.size[1] / 2 + ny)

    def draw(self, base, tl):
        if tl < self.t_in or tl > self.t_out1:
            return
        span = W - self.x0 + 60
        if tl < self.t_out0:
            off = span * (1 - ease_out((tl - self.t_in) / 0.42))
        else:
            off = span * ease_in((tl - self.t_out0) / (self.t_out1 - self.t_out0))
        layer = self.body.copy()
        tip = None
        for i, t_s in enumerate((self.t_s1, self.t_s2)):
            p = (tl - t_s) / self.ts_len
            if p <= 0:
                continue
            img = self.stroke_imgs[i]
            if p < 1:
                m = np.clip((p * 1.06 - self.proj[i]) / 0.06 + 1, 0, 1)
                a = (np.asarray(img.getchannel("A"), np.float32) * m).astype(np.uint8)
                img = img.copy()
                img.putalpha(Image.fromarray(a))
                p0, p1 = self.strokes[i]
                nrm = np.array([-(p1 - p0)[1], (p1 - p0)[0]]) / np.hypot(*(p1 - p0))
                tip = p0 + (p1 - p0) * p + nrm * 9 * math.sin(math.pi * p)
            layer.alpha_composite(img)
        # 鋼筆：第一筆前 0.1 秒出現、第二筆後 0.1 秒離開；兩筆之間移到第二筆起點
        pen_a = smooth((tl - (self.t_s1 - 0.12)) / 0.1) * smooth((self.t_s2 + self.ts_len + 0.12 - tl) / 0.1)
        if pen_a > 0:
            if tip is None:
                if tl < self.t_s1:
                    tip = self.strokes[0][0]
                elif tl < self.t_s2:
                    w = smooth((tl - self.t_s1 - self.ts_len) / (self.t_s2 - self.t_s1 - self.ts_len))
                    tip = self.strokes[0][1] + (self.strokes[1][0] - self.strokes[0][1]) * w
                else:
                    tip = self.strokes[1][1]
            pimg, (px, py) = self.pen
            tmp = Image.new("RGBA", layer.size, (0, 0, 0, 0))
            paste_local(tmp, pimg, tip[0] - px, tip[1] - py, pen_a)
            layer.alpha_composite(tmp)
        paste(base, layer, self.x0 + off, self.y0)


def paste_local(dst, img, x, y, alpha=1.0):
    """貼到任意大小的圖上（paste() 是貼到 1920×1080 畫面）。"""
    img = mul_alpha(img, alpha)
    x, y = int(round(x)), int(round(y))
    w, h = img.size
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(w, dst.size[0] - x), min(h, dst.size[1] - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    dst.alpha_composite(img.crop((sx0, sy0, sx1, sy1)), (x + sx0, y + sy0))


class HeartLine:
    """④ 兩張照片之間的手繪愛心虛線：虛線從兩張照片邊緣往中間畫（0.45s），中間一顆愛心彈出。
    座標在參考格（④ 第 175 格）的畫面空間，逐格用 groom_photo 的投影對到目前畫面（跟著鏡頭慢推）。"""

    def __init__(self, S, E, t0, t1):
        self.S, self.E, self.t0, self.t1 = np.array(S, float), np.array(E, float), t0, t1
        self.M = (self.S + self.E) / 2
        self.hw = 58     # 愛心半寬
        hp = []
        for i in range(73):
            th = i / 72 * 2 * math.pi
            x = 16 * math.sin(th) ** 3
            y = -(13 * math.cos(th) - 5 * math.cos(2 * th) - 2 * math.cos(3 * th) - math.cos(4 * th))
            hp.append((x, y + 1.5))
        self.heart = np.array(hp) * (self.hw / 16.0)

    def _half(self, a, b):
        n = 40
        out = []
        for i in range(n + 1):
            s = i / n
            p = a + (b - a) * s
            p = p + np.array([0, -9 * math.sin(math.pi * s)])         # 微微上拱的手繪弧
            out.append(p)
        return np.array(out)

    def draw(self, base, tl, Hm):
        p = ease_out((tl - self.t0) / 0.45, 2)
        if p <= 0 or tl >= self.t1:
            return
        fa = clamp((self.t1 - tl) / FADE_OUT)
        hs = back_out((tl - self.t0 - 0.35) / 0.3) if tl > self.t0 + 0.35 else 0.0
        halves = [self._half(self.S, self.M - [self.hw + 14, 0]), self._half(self.E, self.M + [self.hw + 14, 0])]
        heart = self.M + self.heart * max(hs, 0.0)
        allp = np.vstack(halves + [self.M + self.heart * 1.2])
        sp = apply_h(Hm, allp)
        x0, y0 = np.floor(sp.min(0)).astype(int) - 12
        x1, y1 = np.ceil(sp.max(0)).astype(int) + 12

        def dr(d, k):
            for hv in halves:
                pts = apply_h(Hm, polyline_cut(hv, p)) - [x0, y0]
                seg = np.hypot(*np.diff(pts, axis=0).T)
                cum = np.r_[0, np.cumsum(seg)]
                dash, gap = 20, 13
                s = 0.0
                while s < cum[-1]:
                    e = min(s + dash, cum[-1])
                    q = [np.interp(v, cum, pts[:, 0]) for v in np.linspace(s, e, 6)], \
                        [np.interp(v, cum, pts[:, 1]) for v in np.linspace(s, e, 6)]
                    thick_line(d, [(qx * k, qy * k) for qx, qy in zip(*q)], 6.5 * k, ROSE + (255,))
                    s += dash + gap
            if hs > 0.01:
                hp = apply_h(Hm, heart) - [x0, y0]
                d.polygon([(x * k, y * k) for x, y in hp], fill=ROSE + (255,))
                d.line([(x * k, y * k) for x, y in hp] + [(hp[0][0] * k, hp[0][1] * k)], fill=ROSE_EDGE + (255,),
                       width=int(3 * k), joint="curve")
        img = supersample(dr, x1 - x0, y1 - y0)
        paste(base, img, x0, y0, fa)


class Badge:
    """⑦【標籤】溫馨提醒：薰衣草紫膠囊＋警示三角，72px。黏在黑板上方（跟著鏡頭推近一起放大），4.3s 彈出。"""

    def __init__(self, t0, t1):
        self.t0, self.t1 = t0, t1
        k = 2
        f = font("wk", LABEL * k)
        txt = "溫馨提醒"
        tw = f.getlength(txt)
        ih = int(LABEL * 0.86 * k)                       # 圖示高
        padx, gap, hgt = 40 * k, 18 * k, int(LABEL * 1.5 * k)
        wid = int(padx * 2 + ih + gap + tw)
        img = Image.new("RGBA", (wid + 24 * k, hgt + 24 * k), (0, 0, 0, 0))
        sh = Image.new("L", img.size, 0)
        ImageDraw.Draw(sh).rounded_rectangle([12 * k, 16 * k, 12 * k + wid, 16 * k + hgt], radius=hgt // 2, fill=90)
        sh = sh.filter(ImageFilter.GaussianBlur(7 * k))
        shl = Image.new("RGBA", img.size, SHADOW + (0,))
        shl.putalpha(sh)
        img.alpha_composite(shl)
        d = ImageDraw.Draw(img)
        bx, by = 12 * k, 10 * k
        d.rounded_rectangle([bx, by, bx + wid, by + hgt], radius=hgt // 2, fill=LAV + (255,),
                            outline=LAV_EDGE + (255,), width=3 * k)
        # 警示三角（圓角）＋驚嘆號
        tx0, ty0 = bx + padx, by + (hgt - ih) / 2
        tri = [(tx0 + ih / 2, ty0 + 4 * k), (tx0 + ih - 2 * k, ty0 + ih - 4 * k), (tx0 + 2 * k, ty0 + ih - 4 * k)]
        thick_line(d, tri + [tri[0]], 7 * k, INK + (255,))
        d.rounded_rectangle([tx0 + ih / 2 - 3.5 * k, ty0 + ih * 0.33, tx0 + ih / 2 + 3.5 * k, ty0 + ih * 0.66],
                            radius=3 * k, fill=INK + (255,))
        d.ellipse([tx0 + ih / 2 - 4.5 * k, ty0 + ih * 0.73, tx0 + ih / 2 + 4.5 * k, ty0 + ih * 0.73 + 9 * k],
                  fill=INK + (255,))
        d.text((tx0 + ih + gap, by + hgt / 2), txt, font=f, fill=INK + (255,), anchor="lm")
        self.img2 = img
        self.size1 = (img.size[0] / k, img.size[1] / k)
        self.pill_cy = (by + hgt / 2) / k             # 膠囊中心在圖中的 y（1x）

    def draw(self, base, tl, board, board_final):
        if tl < self.t0 or tl >= self.t1:
            return
        bx0, by0, bx1, by1 = board
        s = (bx1 - bx0) / (board_final[2] - board_final[0])
        pop = 0.75 + 0.25 * back_out((tl - self.t0) / 0.35)
        a = smooth((tl - self.t0) / 0.25) * clamp((self.t1 - tl) / FADE_OUT)
        sc = s * pop
        w, h = max(2, int(self.size1[0] * sc)), max(2, int(self.size1[1] * sc))
        img = self.img2.resize((w, h), Image.LANCZOS)
        cx = (bx0 + bx1) / 2
        cy = by0 + 10 * s                                # 膠囊中心壓在黑板內框上緣
        paste(base, img, cx - w / 2, cy - self.pill_cy * sc, a)


# ════════════════════════════════════════════════════════════════════════
# 量測快取（③ 進度條、⑦ 黑板）
# ════════════════════════════════════════════════════════════════════════
def measure_progress():
    """③ 進度條粉紅填色的右端（每格），換成 0→99 的計數值。2.2s（第 67 格）＝99%。"""
    ends = {}
    for n in range(1, 68):
        im = np.asarray(_png("03", "beauty", n).convert("RGB"))[645:658, 240:1000].astype(int)
        r, g, b = im[..., 0], im[..., 1], im[..., 2]
        m = ((r > 185) & (r - g > 55) & (b < 175)).mean(0) > 0.5
        idx = np.nonzero(m)[0]
        end = None
        if len(idx):
            end = idx[0]
            for i in idx[1:]:
                if i - end <= 4:
                    end = i
                else:
                    break
            end += 240
        ends[n] = end
    e0, e64 = ends[1], ends[64]
    tab, run = {}, 0.0
    for n in range(1, 68):
        if n <= 64:
            p = 0.97 * clamp((ends[n] - e0) / (e64 - e0)) if ends[n] is not None else run
        else:
            p = lerp(0.97, 1.0, (n - 64) / 3)
        run = max(run, p)
        tab[str(n)] = int(round(99 * run))
    return {"ends": {str(k): (int(v) if v is not None else None) for k, v in ends.items()}, "table": tab}


def measure_board():
    """⑦ 黑板內框（深綠）每格的外框；4.0～5.0s 鏡頭推近，之後不動。"""
    out = {}
    for n in range(118, 153):
        a = np.asarray(_png("07", "beauty", n).convert("RGB")).astype(int)
        r, g, b = a[..., 0], a[..., 1], a[..., 2]
        m = (abs(r - 54) < 12) & (abs(g - 68) < 12) & (abs(b - 59) < 12) & (g - r >= 7) & (g - r <= 22) & \
            (b - r >= 0) & (b - r <= 12)
        cc, rc = m.sum(0), m.sum(1)
        cx = np.nonzero(cc > cc.max() * 0.3)[0]
        ry = np.nonzero(rc > rc.max() * 0.3)[0]
        out[str(n)] = [int(cx.min()), int(ry.min()), int(cx.max()), int(ry.max())]
    return out


@functools.lru_cache(maxsize=None)
def measures():
    p = os.path.join(CACHE, "measures.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    os.makedirs(CACHE, exist_ok=True)
    d = {"progress": measure_progress(), "board": measure_board()}
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    return d


def board_at(n):
    b = measures()["board"]
    n = max(118, min(152, n))
    return b[str(n)]


# ════════════════════════════════════════════════════════════════════════
# 各幕的 2D 元素（每個工作行程第一次用到時建一次）
# ════════════════════════════════════════════════════════════════════════
# ① 信紙局部畫布：letter_text_area 在第 60 格（已攤平）的邊長
S1_REF = 60
# ④ 參考格（5.8s）：說明字、愛心虛線用 groom_photo 的投影跟著鏡頭
S4_REF = 175
# ⑥ 明信片右半的橫線（track 的 postcard_right_half 位置有偏差，改用第 229 格實測的第 2 條橫線，
#   再用 postcard_right_half 的逐格投影跟著鏡頭）
S6_REF = 229
S6_LINE = ((1484.0, 362.6), (1748.0, 348.9))

E = {}


def build():
    if E:
        return E
    # ── ① ──
    q = quad("01", "letter_text_area", S1_REF)
    lw, lh = np.hypot(*(q[1] - q[0])), np.hypot(*(q[3] - q[0]))
    E["s1_rect"] = rect(lw, lh)
    cx, cy = lw / 2, lh / 2
    E["s1"] = [
        # 規劃表 0.8s 起寫；但 track.json 第 25～26 格與畫面不符（信紙還在滑入），0.8s 寫的第一筆會落在信封和桌面上，
        # 改 0.87s 起寫（第一筆出現在第 28 格＝0.90s，信紙已攤平）
        Text(["各位貴賓請注意！"], 96, 0.87, 3.3, cx, cy + 0.36 * 96, name="①-1"),
        Text(["婚禮開始前，", "請先讀完以下幾則小叮嚀…"], 92, 3.3, 6.8, cx, cy - 0.7 * 92 + 0.36 * 92, pitch=1.4,
             name="①-2"),
    ]
    # ── ② 上方半透明信紙條 ──
    E["s2_strip"] = Strip((510, 54, 1410, 302), 0.55, 7.85, seed=2)
    E["s2"] = [
        Text(["為了讓大家擁有", "最佳的觀禮體驗"], MAIN, 0.8, 4.0, 960, 156, name="②-1"),
        Text(["請花 1 分鐘，", "讀完今日的幸福守則"], MAIN, 4.0, 7.8, 960, 156, name="②-2"),
    ]
    # ── ③ 左上信紙條（避開新郎的頭與兩人舉高的手） ──
    s3cx = 608
    E["s3_strip"] = Strip((96, 50, 1120, 290), 0.1, 7.85, seed=3)
    small = "幸福花開中…"
    ws = line_width([(small, INK)], MAIN)
    wb = line_width([("100%", INK)], 150)
    gap = 44
    left = s3cx - (ws + gap + wb) / 2
    base = 205
    E["s3_row"] = Text([small], MAIN, 0.3, 2.95, left + ws, base, align="right", fade_out=0.15, name="③-1")
    E["s3_cnt"] = Counter(measures()["progress"]["table"], left + ws + gap, base, 150, 0.3, 2.95)
    E["s3_wel"] = Text([[("歡迎來到 ", INK), ("洪承孝", ROSE), (" ", INK), ("&", ROSE), (" ", INK),
                         ("李怡安", ROSE)], "的婚禮派對！"], 80, 2.9, 7.8, s3cx, 150, pitch=1.25,
                       name="③-2")
    # ── ④ 拍立得白邊寫名字（局部畫布＝白邊在參考格的邊長）＋說明字 ──
    E["s4_names"] = []
    for region, name, t0 in (("groom_name_border", "洪承孝", 0.6), ("bride_name_border", "李怡安", 0.9)):
        qn = quad("04", region, S4_REF)
        bw, bh = np.hypot(*(qn[1] - qn[0])), np.hypot(*(qn[3] - qn[0]))
        E["s4_names"].append((region, rect(bw, bh),
                              Text([[(name, ROSE)]], BIG, t0, 8.8, bw / 2, bh / 2 + 0.36 * BIG, speed=0.12,
                                   reveal=0.22, name="④名")))
    gb, bb = quad("04", "groom_name_border", S4_REF), quad("04", "bride_name_border", S4_REF)
    lcx, rcx = gb[:, 0].mean(), bb[:, 0].mean()
    sub_base = 916
    E["s4_subs"] = [
        Text(["負責把新娘寵上天"], MAIN, 1.0, 5.8, lcx, sub_base, name="④-左"),
        Text(["負責監督新郎減肥"], MAIN, 3.0, 5.8, rcx, sub_base, name="④-右"),
        Text(["兩位主角已準備就緒！"], MAIN, 5.8, 8.8, (lcx + rcx) / 2, sub_base, name="④-下"),
    ]
    gp, bp = quad("04", "groom_photo", S4_REF), quad("04", "bride_photo", S4_REF)
    E["s4_heart"] = HeartLine((gp[1] + gp[2]) / 2 + [10, 0], (bp[0] + bp[3]) / 2 - [10, 0], 5.8, 8.8)
    # ── ⑤ 上半部偏左 ──
    E["s5_strip"] = Strip((250, 54, 1270, 302), 0.2, 8.85, seed=5)
    E["s5"] = [
        Text(["現場已重金聘請", "專業攝錄影團隊全程記錄"], MAIN, 0.4, 3.6, 760, 156, name="⑤-1"),
        Text(["拍照時請留在座位", "或留意身後的鏡頭"], MAIN, 3.6, 6.3, 760, 156, name="⑤-2"),
        Text(["請勿遮擋雙師的", "大砲鏡頭哦～"], MAIN, 6.3, 8.8, 760, 156, name="⑤-3"),
    ]
    E["s5_br"] = Brackets(3.6)
    E["s5_cut"] = CutOut()
    # ── ⑥ 手機下緣以下（信紙上，墨褐字） ──
    c6 = 1010
    E["s6"] = [
        Text(["手機請轉為", "靜音或震動模式"], MAIN, 0.3, 3.3, c6, 888, name="⑥-1"),
        Text(["今日歡迎拍爆新人！"], MAIN, 3.3, 5.8, c6, 945, name="⑥-2"),
        Text(["合照或側拍請標記：", "@[新人IG帳號]"], MAIN, 5.8, 10.8, c6, 888, name="⑥-3"),
    ]
    (ax, ay), (bx_, by_) = S6_LINE
    th = math.atan2(by_ - ay, bx_ - ax)
    ln = math.hypot(bx_ - ax, by_ - ay)
    acct = "@[新人IG帳號]"
    asz = 46
    while line_width([(acct, INK)], asz) > ln - 14 and asz > 30:
        asz -= 1
    E["s6_acct_size"] = asz
    # 局部畫布：x 沿橫線、y 往下；基線在 y=0（橫線上方 2px）
    ex, ey = np.array([math.cos(th), math.sin(th)]), np.array([-math.sin(th), math.cos(th)])
    A = np.array([[ex[0], ey[0], ax + ey[0] * -2], [ex[1], ey[1], ay + ey[1] * -2], [0, 0, 1]])
    E["s6_acct_A"] = A
    E["s6_acct"] = Text([acct], asz, 5.8, 1e9, 6, 0, align="left", speed=0.09, fade_out=0, name="⑥帳號")
    # ── ⑦ 下方字幕條（上方是兩人的臉，放不下）＋溫馨提醒徽章 ──
    E["s7_strip"] = Strip((480, 782, 1440, 1030), 0.3, 4.05, seed=7)
    E["s7"] = [Text(["請大家放開胃口，", "盡情享用美食與美酒！"], MAIN, 0.5, 4.0, 960, 883, name="⑦-1")]
    E["s7_badge"] = Badge(4.3, 9.8)
    # ── ⑧ ──
    E["s8_a"] = Text(["信讀完了！", "請準備好雙手與熱情…"], 76, 0.2, 3.2, 830, 640, pitch=1.34, name="⑧-1")
    E["s8_strip"] = Strip((480, 54, 1440, 302), 6.0, 9.65, seed=8)
    E["s8_b"] = Text(["讓我們用最熱烈的掌聲", "歡迎新人登場！"], MAIN, 6.2, 9.6, 960, 156, name="⑧-2")
    return E


# ════════════════════════════════════════════════════════════════════════
# 各幕：3D 底圖＋2D
# ════════════════════════════════════════════════════════════════════════
def scaled(img, s):
    """以畫面中心放大 s 倍（s ≥ 1）。"""
    if s <= 1.0005:
        return img
    w, h = int(round(W * s)), int(round(H * s))
    big = img.resize((w, h), Image.BICUBIC)
    x0, y0 = (w - W) // 2, (h - H) // 2
    return big.crop((x0, y0, x0 + W, y0 + H))


def blend(a, b, w):
    if w <= 0:
        return a
    if w >= 1:
        return b
    return Image.blend(a, b, w)


# ② 前段桌面 → 花園的幕內溶接：02a 從 0.867s 起小畫已滿版且不再動，構圖與 02 的 100% 完全對齊
#   （handoff 建議 0.55～0.95s、02 由 107% 縮回 100%；實測那樣會讓拱門錯位成兩個，改成對齊的直接溶接）
S2_DA, S2_DB = 0.85, 1.06
# ⑧ 前段桌面 → 花園：08a 6.5s 小畫滿版，但取景比 08 開頭近（拱門寬 38% vs 25%），
#   溶接時把小畫繼續放大 1.0→1.3（鏡頭穿過小畫），花園照原樣淡入；花園 → 結尾桌面
S8_DA, S8_DB = 6.40, 6.62
S8_ZOOM = 1.30
S8_CA, S8_CB = 6.4, 6.9      # 角色淡入（set → beauty）
S8_EA, S8_EB = 8.8, 9.0


def scene1(tl):
    e = build()
    base = shot("01", tl).copy()
    q = quad("01", "letter_text_area", fidx("01", tl))
    Hm = homog(e["s1_rect"], q)
    for tx in e["s1"]:
        tx.draw(base, tl, Hm)
    return base


def scene2(tl):
    e = build()
    if tl < S2_DA:
        base = shot("02a", tl).copy()
    elif tl >= S2_DB:
        base = shot("02", tl).copy()
    else:
        w = smooth((tl - S2_DA) / (S2_DB - S2_DA))
        base = blend(shot("02a", tl), shot("02", tl), w)
    e["s2_strip"].draw(base, tl)
    for tx in e["s2"]:
        tx.draw(base, tl)
    return base


def scene3(tl):
    e = build()
    base = shot("03", tl).copy()
    e["s3_strip"].draw(base, tl)
    e["s3_row"].draw(base, tl)
    e["s3_cnt"].draw(base, tl)
    e["s3_wel"].draw(base, tl)
    return base


def scene4(tl):
    e = build()
    n = fidx("04", tl)
    base = shot("04", tl).copy()
    for region, rc, tx in e["s4_names"]:
        tx.draw(base, tl, homog(rc, quad("04", region, n)))
    Href = homog(quad("04", "groom_photo", S4_REF), quad("04", "groom_photo", max(n, 25)))
    e["s4_heart"].draw(base, tl, Href)
    for tx in e["s4_subs"]:
        tx.draw(base, tl, Href)
    return base


def scene5(tl):
    e = build()
    base = shot("05", tl).copy()
    e["s5_cut"].draw(base, tl)
    e["s5_br"].draw(base, tl)
    e["s5_strip"].draw(base, tl)
    for tx in e["s5"]:
        tx.draw(base, tl)
    return base


def scene6(tl):
    e = build()
    n = fidx("06", tl)
    base = shot("06", tl).copy()
    if tl >= 5.8:
        Ht = homog(quad("06", "postcard_right_half", S6_REF), quad("06", "postcard_right_half", max(n, 125)))
        e["s6_acct"].draw(base, tl, Ht @ e["s6_acct_A"])
    for tx in e["s6"]:
        tx.draw(base, tl)
    return base


def scene7(tl):
    e = build()
    n = fidx("07", tl)
    base = shot("07", tl).copy()
    e["s7_strip"].draw(base, tl)
    for tx in e["s7"]:
        tx.draw(base, tl)
    e["s7_badge"].draw(base, tl, board_at(n), board_at(152))
    return base


def scene8_garden(tl):
    a = (tl - S8_CA) / (S8_CB - S8_CA)
    if a <= 0:
        return shot("08", tl, "set")
    if a >= 1:
        return shot("08", tl)
    return Image.blend(shot("08", tl, "set"), shot("08", tl), clamp(a))


def scene8(tl):
    e = build()
    if tl < S8_DA:
        base = shot("08a", tl).copy()
    elif tl < S8_DB:
        w = smooth((tl - S8_DA) / (S8_DB - S8_DA))
        base = blend(scaled(shot("08a", tl), lerp(1.0, S8_ZOOM, w)), scene8_garden(tl), w).copy()
    elif tl < S8_EA:
        base = scene8_garden(tl).copy()
    elif tl < S8_EB:
        base = blend(scene8_garden(tl), shot("08c", tl), smooth((tl - S8_EA) / (S8_EB - S8_EA))).copy()
    else:
        base = shot("08c", tl).copy()
    e["s8_a"].draw(base, tl)
    e["s8_strip"].draw(base, tl)
    e["s8_b"].draw(base, tl)
    return base


# 幕：(起點, 長度, 函式)
SCENES = [(0, 7, scene1), (7, 8, scene2), (15, 8, scene3), (23, 9, scene4), (32, 9, scene5),
          (41, 11, scene6), (52, 10, scene7), (62, 10, scene8)]
# 幕與幕之間（寫在前一幕）：推移 ← 0.8s、溶接 0.8s、黑場 0.5+0.8s
TRANS = {7: ("push", 0.8), 15: ("dissolve", 0.8), 23: ("dissolve", 0.8), 32: ("push", 0.8),
         41: ("push", 0.8), 52: ("push", 0.8), 62: ("black", 0.5, 0.8)}
END_FADE = (71.3, DUR - 1.0 / FPS)   # ⑧ 9.3s 起淡出，最後一格全黑


def scene_img(k, t):
    st, du, fn = SCENES[k]
    return fn(t - st)


def frame(t):
    """成品時間 t（秒）→ RGB 圖。"""
    k = max(i for i, s in enumerate(SCENES) if s[0] <= t + 1e-9)
    st, du, _ = SCENES[k]
    img = None
    for B, tr in TRANS.items():
        if tr[0] in ("push", "dissolve") and B - tr[1] / 2 <= t < B + tr[1] / 2:
            ka = [i for i, s in enumerate(SCENES) if s[0] + s[1] == B][0]
            a, b = scene_img(ka, t), scene_img(ka + 1, t)
            p = smooth((t - (B - tr[1] / 2)) / tr[1])
            if tr[0] == "dissolve":
                img = Image.blend(a, b, p)
            else:                                      # 推移 ←：本幕往左推出、下一幕從右推入
                off = int(round(p * W))
                img = Image.new("RGBA", (W, H))
                if off < W:
                    img.paste(a.crop((off, 0, W, H)), (0, 0))
                if off > 0:
                    img.paste(b.crop((0, 0, off, H)), (W - off, 0))
            break
    if img is None:
        img = scene_img(k, t)
    mul = 1.0
    bo, bi = TRANS[62][1], TRANS[62][2]
    if 62 - bo <= t < 62:
        mul = (62 - t) / bo                           # 黑場：⑦ 最後 0.5s 線性到黑
    elif 62 <= t < 62 + bi:
        mul = smooth((t - 62) / bi)                   # ⑧ 前 0.8s smoothstep 從黑淡入
    if t >= END_FADE[0]:
        mul *= clamp((END_FADE[1] - t) / (END_FADE[1] - END_FADE[0]))
    img = img.convert("RGB")
    if mul < 0.999:
        img = Image.eval(img, lambda v: int(v * mul + 0.5)) if mul > 0 else Image.new("RGB", (W, H))
    return img


def render_index(i):
    return frame(i / FPS).tobytes()


# ════════════════════════════════════════════════════════════════════════
# 檢查：字幕框是否在安全框內
# ════════════════════════════════════════════════════════════════════════
def check_layout():
    e = build()
    rows = []

    def chk(name, box):
        x0, y0, x1, y1 = box
        ok = x0 >= SAFE[0] and y0 >= SAFE[1] and x1 <= SAFE[2] and y1 <= SAFE[3]
        rows.append((name, [int(v) for v in box], "OK" if ok else "超出安全框"))

    def screen_box(tx, Hm=None):
        b = tx.ink_box()
        if Hm is None:
            return b
        c = apply_h(Hm, [[b[0], b[1]], [b[2], b[1]], [b[2], b[3]], [b[0], b[3]]])
        return (*c.min(0), *c.max(0))

    q1 = quad("01", "letter_text_area", 100)
    for tx in e["s1"]:
        chk(tx.name, screen_box(tx, homog(e["s1_rect"], q1)))
    for tx in e["s2"] + [e["s3_row"], e["s3_wel"]] + e["s5"] + e["s6"] + e["s7"] + [e["s8_a"], e["s8_b"]]:
        chk(tx.name, screen_box(tx))
    for region, rc, tx in e["s4_names"]:
        chk(tx.name + region[:5], screen_box(tx, homog(rc, quad("04", region, 260))))
    Href = homog(quad("04", "groom_photo", S4_REF), quad("04", "groom_photo", 260))
    for tx in e["s4_subs"]:
        chk(tx.name, screen_box(tx, Href))
    for r in rows:
        print("  %-10s ink %-24s %s" % r)
    sizes = {tx.name: tx.size for tx in e["s1"] + e["s2"] + e["s5"] + e["s6"] + e["s7"] + [e["s8_a"], e["s8_b"]]}
    print("  字級：", sizes, "｜③ 主句", MAIN, "計數 150｜④ 名字", BIG, "說明", MAIN, "｜⑥ 明信片帳號",
          e["s6_acct_size"], "（裝飾，字幕另有 84px）｜⑦ 標籤", LABEL)
    for tx in e["s1"] + e["s2"] + e["s5"] + e["s6"] + e["s7"] + [e["s8_a"], e["s8_b"], e["s3_wel"]]:
        if max(tx.lines_w) / tx.size > 16.5:
            print("  ⚠ 一行超過 16 字寬：", tx.name)
    return rows


# ════════════════════════════════════════════════════════════════════════
# 指令
# ════════════════════════════════════════════════════════════════════════
# ffmpeg 8 由 rgb24 轉出的影格沒帶 primaries／transfer，-color_primaries 等選項會被蓋成 unknown；
# 用 h264_metadata 直接把 BT.709 寫進 SPS（不重新編碼）
BT709_BSF = "h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0"


def ffmpeg_cmd(out, crf, preset="slow"):
    return ["ffmpeg", "-v", "error", "-y",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
            "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-profile:v", "high", "-level", "4.2",
            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-bsf:v", BT709_BSF,
            "-an", "-movflags", "+faststart", out]


def _init():
    build()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["prep", "still", "sheet", "video", "web", "cover", "check"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=DUR)
    ap.add_argument("--out", default=None)
    ap.add_argument("--crf", type=float, default=18)
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    a = ap.parse_args()
    os.makedirs(WORK, exist_ok=True)
    if a.cmd == "prep":
        if os.path.exists(os.path.join(CACHE, "measures.json")):
            os.remove(os.path.join(CACHE, "measures.json"))
        measures.cache_clear()
        m = measures()
        print("③ 計數表（格→%）：", {k: v for k, v in m["progress"]["table"].items() if int(k) % 6 == 1})
        print("⑦ 黑板：", m["board"]["118"], "→", m["board"]["152"])
    elif a.cmd == "check":
        check_layout()
    elif a.cmd == "still":
        od = os.path.join(WORK, "stills")
        os.makedirs(od, exist_ok=True)
        for s in a.args:
            p = os.path.join(od, "t%06.2f.png" % float(s))
            frame(float(s)).save(p)
            print("still", p, flush=True)
    elif a.cmd == "sheet":
        out, ts = a.args[0], [float(x) for x in a.args[1:]]
        cols = 2 if len(ts) > 1 else 1
        rows = (len(ts) + cols - 1) // cols
        sheet = Image.new("RGB", (960 * cols, 540 * rows))
        for i, t in enumerate(ts):
            im = frame(t).resize((960, 540), Image.LANCZOS)
            ImageDraw.Draw(im).text((8, 6), "%.2fs" % t, fill=(255, 0, 0))
            sheet.paste(im, ((i % cols) * 960, (i // cols) * 540))
        sheet.save(out)
        print("sheet", out)
    elif a.cmd == "video":
        out = a.out or OUT
        os.makedirs(os.path.dirname(out), exist_ok=True)
        frames = range(int(round(a.start * FPS)), int(round(a.end * FPS)))
        n = len(frames)
        ff = subprocess.Popen(ffmpeg_cmd(out, a.crf), stdin=subprocess.PIPE)
        with Pool(a.jobs, initializer=_init) as pool:
            for k, buf in enumerate(pool.imap(render_index, frames, chunksize=4)):
                ff.stdin.write(buf)
                if k % 150 == 0:
                    print(f"frame {k}/{n}", flush=True)
        ff.stdin.close()
        ff.wait()
        print("done", ff.returncode, out, os.path.getsize(out) if os.path.exists(out) else -1, flush=True)
    elif a.cmd == "web":
        src, out = a.args[0] if a.args else OUT, a.out or OUT_WEB
        target_mb = 14.0
        kbps = int(target_mb * 8 * 1024 / DUR)             # 檔案上限 15 MB，留 1 MB 餘裕
        common = ["-vf", "scale=1280:720:flags=lanczos", "-c:v", "libx264", "-preset", "slow",
                  "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p", "-b:v", f"{kbps}k",
                  "-maxrate", f"{int(kbps * 1.8)}k", "-bufsize", f"{int(kbps * 3)}k",
                  "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-an"]
        tag = ["-bsf:v", BT709_BSF]
        log = os.path.join(WORK, "x264web")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src] + common +
                       ["-pass", "1", "-passlogfile", log, "-f", "mp4", os.devnull], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src] + common +
                       ["-pass", "2", "-passlogfile", log] + tag + ["-movflags", "+faststart", out], check=True)
        print("web", out, os.path.getsize(out))
    elif a.cmd == "cover":
        t = float(a.args[0]) if a.args else 21.6
        out = a.out or OUT_COVER
        frame(t).save(out, quality=92, subsampling=0)
        print("cover", out, os.path.getsize(out))


if __name__ == "__main__":
    main()
