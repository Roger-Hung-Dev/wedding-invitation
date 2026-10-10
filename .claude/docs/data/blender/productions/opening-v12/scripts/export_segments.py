# 段落預覽與抽格（系統 Python）：
#   python export_segments.py 03 05            → videos/segments/03.mp4、05.mp4（1280×720、30fps、無字）
#   python export_segments.py --sheet 03 0.5,1.0,2.2  → D:\render-work\opening-v12\review\03_sheet.jpg（指定秒數的影格拼成一張）
# 影格來源：D:\render-work\opening-v12\shots\<幕>\beauty\0001.png…（cast 層另外出 <幕>_cast.mp4，墊灰底檢查透明）
import os, sys, json, subprocess
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
PROD = os.path.dirname(HERE)
WORK = os.environ.get("OPENING_WORK") or r"D:\render-work\opening-v12"
OUT = os.path.join(PROD, "videos", "segments")
REVIEW = os.path.join(WORK, "review")
FPS = 30
T0 = {"02": 0.5, "08": 5.8, "08c": 8.6}          # 影格 1 對應這一幕的第幾秒（其他幕從 0 開始）


def frames(shot, layer="beauty"):
    d = os.path.join(WORK, "shots", shot, layer)
    return d, sorted(f for f in os.listdir(d) if f.endswith(".png")) if os.path.isdir(d) else []


def export(shot):
    os.makedirs(OUT, exist_ok=True)
    res = {}
    for layer in ("beauty", "cast"):
        d, fs = frames(shot, layer)
        if not fs:
            continue
        name = shot if layer == "beauty" else f"{shot}_cast"
        out = os.path.join(OUT, name + ".mp4")
        vf = "scale=1280:720:flags=lanczos"
        if layer == "cast":                       # 透明層墊中灰，看得出挖空範圍
            vf = "color=c=0x808080:s=1920x1080:r=30[bg];[bg][0:v]overlay=shortest=1,scale=1280:720:flags=lanczos"
            cmd = ["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", os.path.join(d, "%04d.png"),
                   "-filter_complex", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", "-preset", "medium", out]
        else:
            cmd = ["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", os.path.join(d, "%04d.png"),
                   "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", "-preset", "medium", out]
        subprocess.run(cmd, check=True)
        res[name] = dict(frames=len(fs), seconds=round(len(fs) / FPS, 2), mp4=out, mb=round(os.path.getsize(out) / 1e6, 1))
    print(json.dumps(res, ensure_ascii=False))
    return res


def sheet(shot, secs, cols=3, layer="beauty"):
    os.makedirs(REVIEW, exist_ok=True)
    d, fs = frames(shot, layer)
    f_ = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 26)
    tiles = []
    for s in secs:
        i = int(round((s - T0.get(shot, 0.0)) * FPS))
        i = max(0, min(len(fs) - 1, i))
        im = Image.open(os.path.join(d, fs[i])).convert("RGB").resize((960, 540), Image.LANCZOS)
        dr = ImageDraw.Draw(im); dr.rectangle((0, 0, 300, 36), fill=(0, 0, 0)); dr.text((8, 3), f"{shot} {s:.2f}s #{i + 1}", font=f_, fill="white")
        tiles.append(im)
    rows = (len(tiles) + cols - 1) // cols
    out = Image.new("RGB", (cols * 960, rows * 540), "black")
    for k, im in enumerate(tiles):
        out.paste(im, ((k % cols) * 960, (k // cols) * 540))
    p = os.path.join(REVIEW, f"{shot}_sheet.jpg"); out.save(p, quality=85)
    print(p)


def crop(shot, sec, box, out, size=(900, 900)):
    """從某一格裁一塊（box＝成片像素 x0, y0, x1, y1）存成圖片（⑥ 明信片照片用）"""
    d, fs = frames(shot)
    i = int(round((sec - T0.get(shot, 0.0)) * FPS))
    im = Image.open(os.path.join(d, fs[i])).convert("RGB").crop(box).resize(size, Image.LANCZOS)
    im.save(out, quality=92); print(out, fs[i])


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--sheet":
        sheet(a[1], [float(x) for x in a[2].split(",")], layer=a[3] if len(a) > 3 else "beauty")
    elif a and a[0] == "--crop":
        crop(a[1], float(a[2]), tuple(int(x) for x in a[3].split(",")), a[4])
    else:
        for s in a:
            export(s)
