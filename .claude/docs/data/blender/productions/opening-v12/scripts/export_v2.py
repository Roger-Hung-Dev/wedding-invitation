# 情境版預覽（preview-v2）的成品輸出（系統 Python）：影格 → mp4、封面 jpg、抽格總覽圖。
#   python export_v2.py v2_02 --name s02_hammer --cover 5.3 --sheet 1.0,2.6,4.2,4.7,5.0,5.3,5.6,6.0,6.6,7.0,7.4,7.9
# 影格：D:\render-work\opening-v12\preview-v2\shots\<幕>\beauty\0001.png…（run_prod MODE=full RATE=24 OUT=…）
# 成品：productions/opening-v12/videos/preview-v2/<name>.mp4、<name>_cover.jpg、<name>_sheet.jpg
# 總覽圖每格標秒數，畫面最上緣 22% 畫一條紅線（字幕條的下緣，之後 2D 疊字幕）
import os, sys, json, subprocess, argparse
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
PROD = os.path.dirname(HERE)
WORK = os.environ.get("PREVIEW_V2_WORK") or r"D:\render-work\opening-v12\preview-v2"
OUT = os.path.join(PROD, "videos", "preview-v2")

ap = argparse.ArgumentParser()
ap.add_argument("shot"); ap.add_argument("--name", required=True)
ap.add_argument("--fps", type=int, default=24); ap.add_argument("--cover", type=float, default=0.0)
ap.add_argument("--sheet", default=""); ap.add_argument("--cols", type=int, default=4)
a = ap.parse_args()

d = os.path.join(WORK, "shots", a.shot, "beauty")
fs = sorted(f for f in os.listdir(d) if f.endswith(".png"))
os.makedirs(OUT, exist_ok=True)
mp4 = os.path.join(OUT, a.name + ".mp4")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(a.fps), "-i", os.path.join(d, "%04d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", "-movflags", "+faststart", mp4], check=True)


def frame_at(t):
    i = max(0, min(len(fs) - 1, int(round(t * a.fps))))
    return Image.open(os.path.join(d, fs[i])).convert("RGB"), i


im, i = frame_at(a.cover)
cover = os.path.join(OUT, a.name + "_cover.jpg"); im.save(cover, quality=90)
res = dict(mp4=mp4, frames=len(fs), seconds=round(len(fs) / a.fps, 2), mb=round(os.path.getsize(mp4) / 1e6, 1), cover=cover)
if a.sheet:
    secs = [float(x) for x in a.sheet.split(",")]
    W, H = 640, 360
    font = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 22)
    rows = (len(secs) + a.cols - 1) // a.cols
    sheet = Image.new("RGB", (a.cols * W, rows * H), "black")
    for k, t in enumerate(secs):
        im, i = frame_at(t)
        im = im.resize((W, H), Image.LANCZOS); dr = ImageDraw.Draw(im)
        dr.line((0, int(H * 0.22), W, int(H * 0.22)), fill=(230, 60, 60), width=1)
        dr.rectangle((0, 0, 150, 30), fill=(0, 0, 0)); dr.text((8, 2), f"{t:.2f}s #{i + 1}", font=font, fill="white")
        sheet.paste(im, ((k % a.cols) * W, (k // a.cols) * H))
    p = os.path.join(OUT, a.name + "_sheet.jpg"); sheet.save(p, quality=85); res["sheet"] = p
print(json.dumps(res, ensure_ascii=False))
