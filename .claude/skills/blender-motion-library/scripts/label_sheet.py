# python label_sheet.py out.png cols label1=img1 label2=img2 ...
import sys
from PIL import Image, ImageDraw, ImageFont
out, cols = sys.argv[1], int(sys.argv[2])
items = [a.split("=", 1) for a in sys.argv[3:]]
ims = [(l, Image.open(f).convert("RGB")) for l, f in items]
w, h = ims[0][1].size
rows = (len(ims) + cols - 1) // cols
S = Image.new("RGB", (w * cols, h * rows), "white"); d = ImageDraw.Draw(S)
try: font = ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", 18)
except Exception: font = ImageFont.load_default()
for i, (l, im) in enumerate(ims):
    x, y = (i % cols) * w, (i // cols) * h
    S.paste(im, (x, y)); d.text((x + 4, y + 2), l, fill=(160, 30, 30), font=font)
S.save(out)
