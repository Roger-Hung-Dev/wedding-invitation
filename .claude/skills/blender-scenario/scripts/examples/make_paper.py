# 報紙版面（情境 1 的貼圖範例）：python make_paper.py <輸出資料夾>
# outer（封面＋封底，鏡頭看到的那面）、inner（她在讀的跨頁）、turn_a / turn_b（翻動那張的正反面）
from PIL import Image, ImageDraw, ImageFont
import random, sys, os
OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
os.makedirs(OUT, exist_ok=True)
W, H = 1120, 760          # 跨頁（兩頁），每頁 560
BG = (238, 233, 222); INK = (40, 36, 34); GRAY = (150, 145, 138); PINK = (226, 160, 165)
F = lambda s, b=True: ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc" if b else "C:/Windows/Fonts/msjh.ttc", s)
SER = lambda s: ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", s)
random.seed(3)


def columns(d, x0, y0, x1, y1, cols=3, gap=14):
    cw = (x1 - x0 - gap * (cols - 1)) / cols
    for c in range(cols):
        cx = x0 + c * (cw + gap); y = y0
        while y < y1:
            ln = cw * (0.55 + 0.45 * random.random()) if random.random() < 0.12 else cw
            d.line([(cx, y), (cx + ln, y)], fill=GRAY, width=3); y += 9


def page(d, x, title=None, sub=None, photo=None, small=False):
    if title:
        d.text((x + 280, 70 if not small else 40), title, font=F(54 if not small else 36), fill=INK, anchor="mm")
    if sub:
        d.text((x + 280, 120 if not small else 78), sub, font=F(22, False), fill=GRAY, anchor="mm")
    y = 150 if not small else 100
    if photo:
        d.rectangle([x + 40, y, x + 520, y + 220], fill=photo); y += 236
        d.text((x + 280, y - 128), "♥" if photo == PINK else "", font=ImageFont.truetype("C:/Windows/Fonts/seguisym.ttf", 80), fill=(255, 255, 255), anchor="mm")
    columns(d, x + 40, y, x + 520, H - 40)


def outer():
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    # 右半是封面（鏡頭從她正前方看，封面在右側＝她的左手邊翻開後朝外）
    x = 560
    d.text((x + 280, 62), "婚禮日報", font=F(72), fill=INK, anchor="mm")
    d.text((x + 280, 112), "THE WEDDING DAILY  ·  2026.12.12", font=SER(20), fill=GRAY, anchor="mm")
    d.line([(x + 30, 134), (x + 530, 134)], fill=INK, width=3)
    d.text((x + 280, 178), "怡安 & 承孝  婚禮今日登場", font=F(38), fill=(170, 60, 70), anchor="mm")
    d.rectangle([x + 40, 210, x + 520, 430], fill=PINK)
    d.text((x + 280, 320), "♥", font=ImageFont.truetype("C:/Windows/Fonts/seguisym.ttf", 110), fill=(255, 255, 255), anchor="mm")
    columns(d, x + 40, 450, x + 520, H - 40)
    page(d, 0, "生活", "LIFESTYLE", photo=(200, 190, 175), small=True)
    im.save(os.path.join(OUT, "paper_outer.png"))


def inner():
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    page(d, 0, "新娘試穿禮服", "粉紅歐根紗蓬裙亮相", photo=PINK)
    page(d, 560, "攝影棚直擊", "STUDIO REPORT", photo=(190, 200, 210))
    im.save(os.path.join(OUT, "paper_inner.png"))


def turn():
    a = Image.new("RGB", (560, H), BG); d = ImageDraw.Draw(a); page(d, 0, "婚宴菜單", "MENU", photo=(215, 200, 170)); a.save(os.path.join(OUT, "paper_turn_a.png"))
    b = Image.new("RGB", (560, H), BG); d = ImageDraw.Draw(b); page(d, 0, "賓客留言", "GUEST BOOK", photo=(210, 185, 200)); b.save(os.path.join(OUT, "paper_turn_b.png"))


outer(); inner(); turn(); print("ok")
