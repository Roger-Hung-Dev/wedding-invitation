# 開場影片 V12 的 2D 素材（系統 Python，不在 Blender 裡跑）：
#   python make_assets.py            → 全部重產
#   python make_assets.py photos     → 只做拍立得照片裁切
# 產出 ../assets/photos/*.jpg（拍立得照片區）、../assets/tex/*.png（手機螢幕、郵戳、紙膠帶、押花、明信片、蕾絲、草地）
# 配色照製作說明：薰衣草紫 #B8A1C9、乾燥玫瑰 #D9777F、棉紙米白 #F6EFE6、鼠尾草綠 #8FA58A、墨褐 #4A3B35
import os, sys, math, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
PROD = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PROD, *[".."] * 6))
PHOTO_SRC = os.path.join(REPO, ".claude", "docs", "design", "animation-photo")
OUT_P = os.path.join(PROD, "assets", "photos")
OUT_T = os.path.join(PROD, "assets", "tex")
os.makedirs(OUT_P, exist_ok=True); os.makedirs(OUT_T, exist_ok=True)

LAV = (184, 161, 201); ROSE = (217, 119, 127); PAPER = (246, 239, 230); SAGE = (143, 165, 138); INK = (74, 59, 53)
FONT = "C:/Windows/Fonts/georgiab.ttf"


def hexa(c, a=255):
    return (*c, a)


# ── 1. 拍立得照片：照片區比例 0.852（寬/高），上半身到膝蓋、臉在上 1/3 ──
# 裁切框寫在原圖座標（看過縮圖後定的；臉中心約在框高 24% 處）
PHOTO_CROPS = {
    "groom": ("新郎簡介照.jpg", (1042, 2227, 4480, 6262)),     # 4480×6720，人在畫面中偏右，右邊貼齊原圖
    "bride": ("新娘簡介照.jpg", (539, 1919, 3711, 5646)),      # 4226×6339
}
PHOTO_OUT = (900, 1056)


def photos():
    for key, (fn, box) in PHOTO_CROPS.items():
        im = ImageOps.exif_transpose(Image.open(os.path.join(PHOTO_SRC, fn))).convert("RGB")
        x0, y0, x1, y1 = box
        r = (x1 - x0) / (y1 - y0)
        assert abs(r - PHOTO_OUT[0] / PHOTO_OUT[1]) < 0.01, (key, r)
        c = im.crop(box).resize(PHOTO_OUT, Image.LANCZOS)
        p = os.path.join(OUT_P, f"polaroid_{key}.jpg"); c.save(p, quality=90)
        print("photo", p, c.size)


# ── 2. 手機螢幕（鈴鐺 → 靜音）──
def bell(draw, cx, cy, s, col, width):
    """lucide bell 的簡化畫法：圓頂＋外擴的下緣＋底線＋鈴舌"""
    top = cy - 0.42 * s
    pts = []
    for k in range(0, 181, 6):                      # 圓頂（半圓）
        a = math.radians(180 + k)
        pts.append((cx + 0.30 * s * math.cos(a), cy - 0.08 * s + 0.34 * s * math.sin(a)))
    right = [(cx + 0.30 * s, cy - 0.08 * s), (cx + 0.33 * s, cy + 0.18 * s), (cx + 0.42 * s, cy + 0.28 * s)]
    left = [(cx - 0.42 * s, cy + 0.28 * s), (cx - 0.33 * s, cy + 0.18 * s), (cx - 0.30 * s, cy - 0.08 * s)]
    outline = left + pts + right
    draw.line(outline + [(cx - 0.42 * s, cy + 0.28 * s)], fill=col, width=width, joint="curve")
    draw.arc((cx - 0.10 * s, cy + 0.26 * s, cx + 0.10 * s, cy + 0.46 * s), 0, 180, fill=col, width=width)
    draw.ellipse((cx - 0.05 * s, top - 0.08 * s, cx + 0.05 * s, top + 0.02 * s), fill=col)


def phone_screens():
    W, H = 540, 1110
    for name, off in (("phone_bell", False), ("phone_bell_off", True)):
        im = Image.new("RGB", (W, H))
        dr = ImageDraw.Draw(im)
        for y in range(H):                           # 薰衣草→棉紙米白的直向漸層
            t = y / H
            dr.line([(0, y), (W, y)], fill=tuple(int(LAV[i] * (1 - t) + PAPER[i] * t) for i in range(3)))
        dr.rounded_rectangle((W * 0.5 - 60, 36, W * 0.5 + 60, 62), 13, fill=(40, 34, 38))   # 瀏海
        f = ImageFont.truetype(FONT, 64)
        dr.text((W / 2, 200), "12:12", font=f, fill=INK, anchor="mm")
        col = INK if not off else ROSE
        bell(dr, W / 2, H * 0.52, 300, col, 22)
        if off:
            dr.line([(W / 2 - 150, H * 0.52 - 160), (W / 2 + 150, H * 0.52 + 160)], fill=PAPER, width=46)
            dr.line([(W / 2 - 150, H * 0.52 - 160), (W / 2 + 150, H * 0.52 + 160)], fill=ROSE, width=22)
        p = os.path.join(OUT_T, name + ".png"); im.save(p); print("tex", p)


# ── 3. Tag 郵戳（墨水章，RGBA）──
def postmark():
    S = 900
    im = Image.new("RGBA", (S * 2, S), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    ink = hexa((176, 84, 96), 235)
    cx, cy, R = S * 0.5, S * 0.5, S * 0.42
    dr.ellipse((cx - R, cy - R, cx + R, cy + R), outline=ink, width=22)
    dr.ellipse((cx - R * 0.80, cy - R * 0.80, cx + R * 0.80, cy + R * 0.80), outline=ink, width=10)
    # 中間的「標籤」圖示（行李吊牌）
    tw, th = R * 0.62, R * 0.40
    poly = [(cx - tw * 0.5, cy - th * 0.5 + 10), (cx + tw * 0.25, cy - th * 0.5 + 10), (cx + tw * 0.55, cy + 10),
            (cx + tw * 0.25, cy + th * 0.5 + 10), (cx - tw * 0.5, cy + th * 0.5 + 10)]
    dr.line(poly + [poly[0]], fill=ink, width=18, joint="curve")
    dr.ellipse((cx + tw * 0.12 - 16, cy + 10 - 16, cx + tw * 0.12 + 16, cy + 10 + 16), outline=ink, width=9)
    f = ImageFont.truetype(FONT, 76)
    dr.text((cx, cy - R * 0.56), "TAG US", font=f, fill=ink, anchor="mm")
    f2 = ImageFont.truetype(FONT, 60)
    dr.text((cx, cy + R * 0.58), "2026.12.12", font=f2, fill=ink, anchor="mm")
    # 往右延伸的波浪消印線
    for k in range(5):
        y0 = cy - R * 0.5 + k * R * 0.25
        pts = [(cx + R * 1.05 + x, y0 + 16 * math.sin(x / 38.0)) for x in range(0, int(S * 0.9), 6)]
        dr.line(pts, fill=ink, width=12)
    # 墨水斑駁：隨機挖掉一些、外圍濺幾點
    random.seed(4)
    mask = Image.new("L", im.size, 255); md = ImageDraw.Draw(mask)
    for _ in range(900):
        x, y, r = random.uniform(0, S * 2), random.uniform(0, S), random.uniform(2, 9)
        md.ellipse((x - r, y - r, x + r, y + r), fill=random.randint(0, 150))
    a = im.split()[3]
    a = Image.composite(a, Image.new("L", im.size, 0), mask.filter(ImageFilter.GaussianBlur(1.2)))
    im.putalpha(a)
    dr = ImageDraw.Draw(im)
    for _ in range(14):
        ang = random.uniform(0, 2 * math.pi); d = random.uniform(R * 1.05, R * 1.3); r = random.uniform(4, 13)
        x, y = cx + d * math.cos(ang), cy + d * math.sin(ang)
        dr.ellipse((x - r, y - r, x + r, y + r), fill=ink)
    p = os.path.join(OUT_T, "postmark.png"); im.save(p); print("tex", p)


# ── 4. 紙膠帶（半透明、兩端鋸齒撕邊）──
def washi(name, base, dots=None, stripes=None):
    W, H = 1024, 256
    im = Image.new("RGBA", (W, H), hexa(base, 215))
    dr = ImageDraw.Draw(im)
    if dots:
        for y in range(18, H, 44):
            for x in range((y // 44) % 2 * 22 + 12, W, 44):
                dr.ellipse((x - 7, y - 7, x + 7, y + 7), fill=hexa(dots, 230))
    if stripes:
        for x in range(-H, W, 36):
            dr.line([(x, H), (x + H, 0)], fill=hexa(stripes, 160), width=8)
    a = im.split()[3]; ad = ImageDraw.Draw(a)
    random.seed(len(name))
    for side in (0, 1):                               # 撕邊：兩端各一排三角缺口
        x = 0 if side == 0 else W
        pts = [(x, 0)]
        for y in range(0, H + 1, 16):
            pts.append((x + (1 if side == 0 else -1) * random.uniform(4, 22), y))
        pts.append((x, H))
        ad.polygon(pts, fill=0)
    im.putalpha(a)
    p = os.path.join(OUT_T, name + ".png"); im.save(p); print("tex", p)


# ── 5. 押花（扁平花朵、葉、單片花瓣，RGBA）──
def petal_shape(dr, cx, cy, ang, L, W, col, vein=None):
    pts = []
    for k in range(0, 361, 10):
        t = math.radians(k)
        # 花瓣：一端尖、一端圓
        r = L * 0.5 * (1 + math.cos(t)) ** 0.9 if k < 360 else 0
        x = L * 0.5 * (1 - math.cos(t)); y = W * 0.5 * math.sin(t) * (0.6 + 0.4 * math.sin(t / 2))
        ca, sa = math.cos(ang), math.sin(ang)
        pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    dr.polygon(pts, fill=col)
    if vein:
        dr.line([(cx, cy), (cx + L * 0.85 * math.cos(ang), cy + L * 0.85 * math.sin(ang))], fill=vein, width=max(2, int(W * 0.05)))


def flower(name, n, col, center, vein, S=512, L=0.46, W=0.30, seed=1):
    random.seed(seed)
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    c = S / 2
    for k in range(n):
        a = 2 * math.pi * k / n + random.uniform(-0.12, 0.12)
        cc = tuple(max(0, min(255, int(v * random.uniform(0.9, 1.05)))) for v in col)
        petal_shape(dr, c, c, a, S * L * random.uniform(0.9, 1.05), S * W, hexa(cc, 225), hexa(vein, 120))
    dr.ellipse((c - S * 0.07, c - S * 0.07, c + S * 0.07, c + S * 0.07), fill=hexa(center, 240))
    for k in range(10):
        a = random.uniform(0, 2 * math.pi); d = random.uniform(0, S * 0.05)
        dr.ellipse((c + d * math.cos(a) - 5, c + d * math.sin(a) - 5, c + d * math.cos(a) + 5, c + d * math.sin(a) + 5), fill=hexa(INK, 160))
    im = im.filter(ImageFilter.GaussianBlur(0.8))
    p = os.path.join(OUT_T, name + ".png"); im.save(p); print("tex", p)


def leaf_sprig(name, col, S=512, seed=3):
    random.seed(seed)
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    dr.line([(S * 0.5, S * 0.95), (S * 0.5, S * 0.08)], fill=hexa((110, 128, 100), 230), width=7)
    for k in range(7):
        y = S * (0.82 - 0.11 * k)
        for sd in (-1, 1):
            a = math.radians(-90 + sd * (50 - k * 3))
            petal_shape(dr, S * 0.5, y, a, S * (0.26 - 0.015 * k), S * 0.13, hexa(col, 225), hexa((100, 120, 95), 140))
    p = os.path.join(OUT_T, name + ".png"); im.save(p); print("tex", p)


def single_petal(name, col, S=256, seed=5):
    random.seed(seed)
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    petal_shape(dr, S * 0.12, S * 0.5, 0, S * 0.8, S * 0.52, hexa(col, 230), hexa(tuple(int(v * 0.8) for v in col), 120))
    im = im.filter(ImageFilter.GaussianBlur(0.6))
    p = os.path.join(OUT_T, name + ".png"); im.save(p); print("tex", p)


# ── 6. IG 風明信片的卡面（照片另外貼一片，才能做顯影；不放官方商標）──
def postcard_face():
    W, H = 1500, 1000
    im = Image.new("RGB", (W, H), (252, 249, 244)); dr = ImageDraw.Draw(im)
    # 左側照片槽（照片物件會蓋在這裡）
    dr.rectangle((60, 60, 60 + 820, 60 + 820), fill=(236, 230, 222))
    # 照片下方的通用圖示列：愛心、對話框、紙飛機（線條、墨褐）
    y = 935
    hx = 100
    dr.line([(hx, y + 12), (hx - 26, y - 12), (hx - 16, y - 30), (hx, y - 20), (hx + 16, y - 30), (hx + 26, y - 12), (hx, y + 12)], fill=INK, width=7, joint="curve")
    dr.ellipse((170, y - 30, 226, y + 22), outline=INK, width=7); dr.line([(180, y + 14), (172, y + 30), (194, y + 20)], fill=INK, width=7)
    dr.line([(266, y - 4), (318, y - 28), (300, y + 26), (288, y + 2), (266, y - 4)], fill=INK, width=7, joint="curve")
    # 右側：頭像圓＋名字橫線（留白給合成階段手寫帳號）＋淡淡的橫格線
    dr.ellipse((940, 80, 1040, 180), fill=LAV)
    dr.rounded_rectangle((1065, 112, 1330, 146), 17, fill=(232, 224, 214))
    for k in range(5):
        yy = 330 + k * 110
        dr.line([(940, yy), (1440, yy)], fill=(225, 214, 204), width=4)
    # 郵票框（右上角）
    dr.rectangle((1330, 200, 1440, 320), outline=ROSE, width=6)
    for k in range(9):
        dr.ellipse((1330 + k * 13 - 4, 196, 1330 + k * 13 + 4, 204), fill=(252, 249, 244))
    p = os.path.join(OUT_T, "postcard_face.png"); im.save(p); print("tex", p)


# ── 7. 蕾絲桌巾邊（RGBA，橫向重複）──
def lace():
    W, H = 1024, 256
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    white = (250, 247, 242, 255)
    dr.rectangle((0, 0, W, H * 0.45), fill=white)
    n = 8; w = W / n
    for k in range(n):
        cx = w * (k + 0.5)
        dr.ellipse((cx - w * 0.5, H * 0.2, cx + w * 0.5, H * 0.95), fill=white)          # 扇形下緣
        dr.ellipse((cx - w * 0.22, H * 0.42, cx + w * 0.22, H * 0.78), fill=(0, 0, 0, 0))  # 中間的洞
        for j in range(6):
            a = math.pi * (j + 0.5) / 6
            x, y = cx + w * 0.36 * math.cos(a), H * 0.6 + H * 0.26 * math.sin(a)
            dr.ellipse((x - 7, y - 7, x + 7, y + 7), fill=(0, 0, 0, 0))
        for j in range(3):
            x = cx - w * 0.3 + j * w * 0.3
            dr.ellipse((x - 9, H * 0.18 - 9, x + 9, H * 0.18 + 9), fill=(0, 0, 0, 0))
    p = os.path.join(OUT_T, "lace.png"); im.save(p); print("tex", p)


# ── 8. 草地（柔和的斑駁綠，給草地材質當底色）──
def grass():
    S = 1024
    random.seed(9)
    base = Image.new("RGB", (S, S), (150, 184, 128)); dr = ImageDraw.Draw(base)
    for _ in range(2600):
        x, y = random.uniform(0, S), random.uniform(0, S); r = random.uniform(10, 46)
        t = random.random()
        col = (int(130 + 40 * t), int(168 + 30 * t), int(112 + 26 * t))
        dr.ellipse((x - r, y - r, x + r, y + r), fill=col)
    base = base.filter(ImageFilter.GaussianBlur(10))
    dr = ImageDraw.Draw(base)
    for _ in range(9000):                              # 細草葉
        x, y = random.uniform(0, S), random.uniform(0, S); L = random.uniform(6, 16); a = random.uniform(-0.4, 0.4)
        col = (int(120 + 50 * random.random()), int(160 + 40 * random.random()), int(100 + 30 * random.random()))
        dr.line([(x, y), (x + L * math.sin(a), y - L * math.cos(a))], fill=col, width=2)
    base = base.filter(ImageFilter.GaussianBlur(0.7))
    # 讓它可以無縫重複：和左右、上下翻轉的版本交叉淡化
    p = os.path.join(OUT_T, "grass.png"); base.save(p); print("tex", p)


# ── 9. 水彩拱門小畫（②、⑧ 信紙上；先跑 run_prod MODE=painting 產生 garden_for_painting.png）──
def watercolor():
    src = os.path.join(OUT_T, "garden_for_painting.png")
    im = Image.open(src).convert("RGB").resize((1200, 900), Image.LANCZOS)
    flat = im
    for _ in range(3):                                         # 色塊化：中值濾波＋減色
        flat = flat.filter(ImageFilter.MedianFilter(7))
    flat = flat.quantize(colors=28, method=Image.Quantize.MEDIANCUT).convert("RGB")
    flat = flat.filter(ImageFilter.GaussianBlur(2.2))
    wash = Image.blend(flat, Image.new("RGB", flat.size, PAPER), 0.22)          # 水彩的淡
    edges = flat.convert("L").filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(1.0))
    edges = edges.point(lambda v: 255 - min(255, int(v * 2.2)))
    ink = Image.merge("RGB", [edges] * 3)
    from PIL import ImageChops
    out = ImageChops.multiply(wash, Image.blend(ink, Image.new("RGB", ink.size, (255, 255, 255)), 0.45))
    random.seed(12)                                            # 紙紋：細小的明暗斑點
    noise = Image.effect_noise(out.size, 26).filter(ImageFilter.GaussianBlur(1.2)).point(lambda v: 225 + (v - 128) // 6)
    out = ImageChops.multiply(out, Image.merge("RGB", [noise] * 3))
    # 不規則的水彩邊（透明度）＋外圈留白
    W, H = 1280, 960
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    paper = Image.new("RGBA", (W, H), hexa(PAPER)); card.alpha_composite(paper)
    mask = Image.new("L", out.size, 0); md = ImageDraw.Draw(mask)
    pts = []
    for k in range(120):
        a = 2 * math.pi * k / 120
        rx, ry = 560 + random.uniform(-14, 10), 420 + random.uniform(-14, 10)
        x = 600 + rx * math.copysign(abs(math.cos(a)) ** 0.25, math.cos(a)); y = 450 + ry * math.copysign(abs(math.sin(a)) ** 0.25, math.sin(a))
        pts.append((x, y))
    md.polygon(pts, fill=255); mask = mask.filter(ImageFilter.GaussianBlur(5))
    layer = out.convert("RGBA"); layer.putalpha(mask)
    card.alpha_composite(layer, (40, 30))
    # 卡片外緣也做一點毛邊
    a = Image.new("L", (W, H), 0); ad = ImageDraw.Draw(a)
    ad.rectangle((6, 6, W - 6, H - 6), fill=255)
    for _ in range(500):
        x, y = random.choice((random.uniform(0, W), random.choice((random.uniform(0, 9), random.uniform(H - 9, H))))), 0
        x, y = (random.uniform(0, W), random.choice((random.uniform(0, 9), random.uniform(H - 9, H)))) if random.random() < 0.5 else \
               (random.choice((random.uniform(0, 9), random.uniform(W - 9, W))), random.uniform(0, H))
        ad.ellipse((x - 5, y - 5, x + 5, y + 5), fill=0)
    card.putalpha(Image.composite(card.split()[3], Image.new("L", (W, H), 0), a))
    p = os.path.join(OUT_T, "watercolor_arch.png"); card.save(p); print("tex", p)


# ── 10. 明信片照片（用花園同框的預覽圖；正式版可換使用者指定的照片）──
def postcard_photo(src=None):
    src = src or os.path.join(PROD, "pictures", "preview", "08_08.00s.jpg")
    im = Image.open(src).convert("RGB")
    w, h = im.size; s = min(w, h)
    c = im.crop(((w - s) // 2, 0, (w + s) // 2, s)).resize((900, 900), Image.LANCZOS)
    p = os.path.join(OUT_T, "postcard_photo.jpg"); c.save(p, quality=90); print("tex", p)


if __name__ == "__main__":
    if sys.argv[1:2] == ["watercolor"]:
        watercolor(); sys.exit()
    if sys.argv[1:2] == ["postcard_photo"]:
        postcard_photo(*sys.argv[2:3]); sys.exit()
    only = sys.argv[1:] or ["photos", "phone", "postmark", "washi", "flowers", "postcard", "lace", "grass"]
    if "photos" in only: photos()
    if "phone" in only: phone_screens()
    if "postmark" in only: postmark()
    if "washi" in only:
        washi("washi_lavender", LAV, dots=(250, 246, 240)); washi("washi_sage", SAGE, stripes=(236, 240, 228))
        washi("washi_rose", (232, 170, 172), dots=(252, 244, 240))
    if "flowers" in only:
        flower("pf_lavender", 5, LAV, (240, 214, 120), (140, 110, 160), seed=1)
        flower("pf_rose", 6, ROSE, (245, 220, 150), (170, 80, 90), seed=2)
        flower("pf_white", 5, (247, 240, 232), (240, 200, 110), (200, 185, 170), L=0.42, W=0.34, seed=6)
        flower("pf_blush", 8, (236, 176, 172), (235, 205, 140), (190, 120, 120), L=0.44, W=0.22, seed=8)
        leaf_sprig("pf_leaf", SAGE)
        single_petal("petal_rose", ROSE, seed=11); single_petal("petal_lav", LAV, seed=12)
        single_petal("petal_blush", (236, 176, 172), seed=13); single_petal("petal_sage", SAGE, seed=14)
    if "postcard" in only: postcard_face()
    if "lace" in only: lace()
    if "grass" in only: grass()
