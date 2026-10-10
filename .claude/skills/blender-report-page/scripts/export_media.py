# 把暫存區（WORK）的影格轉成專案裡的成品（系統 Python，需要 ffmpeg 與 Pillow）：
#   python export_media.py --project <PROJ> [--only showcase,actions,actions_costume,scenes,refs]
#
#   WORK/showcase/turn_body|turn_face|turn_costume|costume_moves  → PROJ/videos/<名>.mp4 ＋ PROJ/pictures/posters/<名>.jpg
#   WORK/showcase/hands、expr、feet                               → PROJ/pictures/hands_sheet.jpg、face_feet.jpg
#   WORK/showcase/costume_stills                                  → PROJ/pictures/costume_front.jpg、costume_back.jpg
#   WORK/actions/<代號>（便服）、WORK/actions_costume/<代號>       → PROJ/videos/actions(_costume)/<代號>.mp4 ＋ posters
#   WORK/scenes/<id>                                              → PROJ/videos/scenes/<id>.mp4 ＋ posters
#   PROJ/source/front.*、back.*（使用者的照片）                   → PROJ/pictures/ref_front.jpg、ref_back.jpg（裁成 2:3）
# 只轉「影格比成品新」的；影格數不足（還在渲染）的跳過並列出。最後印一行 JSON 摘要。
import argparse, glob, json, os, subprocess, sys, tempfile
sys.stdout.reconfigure(encoding="utf-8")   # 中文輸出不要變亂碼（Windows 主控台預設 cp950）
from PIL import Image

ap = argparse.ArgumentParser(); ap.add_argument("--project", required=True); ap.add_argument("--only", default="")
a = ap.parse_args()
P = os.path.abspath(a.project); M = json.load(open(os.path.join(P, "project.json"), encoding="utf8"))
# 和 blender_env.py 的 WORK 同一套規則：BLENDER_WORK_ROOT → D 槽 → 系統暫存
WORK_ROOT = os.environ.get("BLENDER_WORK_ROOT") or (
    r"D:\render-work\blender-work" if os.path.isdir("D:\\") else os.path.join(tempfile.gettempdir(), "blender-work"))
WORK = os.path.join(WORK_ROOT, M["name"])
ENC = os.path.join(os.path.dirname(__file__), "..", "..", "blender-motion-library", "scripts", "encode.py")
only = set(x for x in a.only.split(",") if x)
want = lambda k: not only or k in only
done, skipped = [], []


def frames(d):
    return sorted(glob.glob(os.path.join(d, "*.png")))


def enc(src, dst, poster, width=0, expect=0):
    fr = frames(src)
    if not fr or (expect and len(fr) < expect):
        skipped.append(f"{os.path.relpath(src, WORK)}（{len(fr)} 格{f'／需要 {expect}' if expect else ''}）"); return
    os.makedirs(os.path.dirname(dst), exist_ok=True); os.makedirs(os.path.dirname(poster), exist_ok=True)
    if os.path.exists(dst) and os.path.getmtime(dst) > max(os.path.getmtime(f) for f in fr):
        return
    subprocess.run([sys.executable, ENC, src, dst, "1", str(width)], check=True, capture_output=True)
    im = Image.open(fr[len(fr) // 2]).convert("RGB"); im.save(poster, quality=82)
    done.append(os.path.relpath(dst, P).replace("\\", "/"))


def sheet(files, cols, out, size=None):
    ims = [Image.open(f).convert("RGB") for f in files if os.path.exists(f)]
    if not ims:
        return
    w, h = size or ims[0].size
    rows = (len(ims) + cols - 1) // cols
    S = Image.new("RGB", (w * cols, h * rows), (244, 238, 240))
    for i, im in enumerate(ims):
        S.paste(im.resize((w, h)), ((i % cols) * w, (i // cols) * h))
    S.save(out, quality=85); done.append(os.path.relpath(out, P).replace("\\", "/"))


V, PI = os.path.join(P, "videos"), os.path.join(P, "pictures")
SC = os.path.join(WORK, "showcase")
if want("showcase"):
    for n, exp in (("turn_body", 96), ("turn_face", 72), ("turn_costume", 96), ("costume_moves", 180)):
        if os.path.isdir(os.path.join(SC, n)):
            enc(os.path.join(SC, n), os.path.join(V, f"{n}.mp4"), os.path.join(PI, "posters", f"{n}.jpg"), expect=exp)
    hs = [os.path.join(SC, "hands", f"{s}_{h}.png") for s in ("palm", "back") for h in ("relax", "open", "fist", "point", "peace", "grip")]
    if all(os.path.exists(f) for f in hs):
        sheet(hs, 6, os.path.join(PI, "hands_sheet.jpg"))
    ex = [os.path.join(SC, "expr", f"{k}.png") for k in ("joy", "fun", "surp", "wink", "A")]
    ft = [os.path.join(SC, "feet", f"{k}.png") for k in ("f", "q", "s", "b")]
    if all(os.path.exists(f) for f in ex + ft):
        im = Image.new("RGB", (1500, 525), (244, 238, 240))
        for i, f in enumerate(ex): im.paste(Image.open(f).convert("RGB").resize((300, 300)), (i * 300, 0))
        for i, f in enumerate(ft): im.paste(Image.open(f).convert("RGB").resize((300, 225)), (i * 375 + 37, 300))
        im.save(os.path.join(PI, "face_feet.jpg"), quality=85); done.append("pictures/face_feet.jpg")
    for n in ("front", "back"):
        f = os.path.join(SC, "costume_stills", f"{n}.png")
        if os.path.exists(f):
            Image.open(f).convert("RGB").save(os.path.join(PI, f"costume_{n}.jpg"), quality=85); done.append(f"pictures/costume_{n}.jpg")
for kind in ("actions", "actions_costume"):
    if want(kind) and os.path.isdir(os.path.join(WORK, kind)):
        prog = os.path.join(WORK, kind, "progress.txt")
        ok = set(open(prog).read().split()) if os.path.exists(prog) else set()
        for d in sorted(glob.glob(os.path.join(WORK, kind, "*"))):
            k = os.path.basename(d)
            if os.path.isdir(d) and k in ok:
                enc(d, os.path.join(V, kind, f"{k}.mp4"), os.path.join(PI, "posters", kind, f"{k}.jpg"), width=360)
            elif os.path.isdir(d):
                skipped.append(f"{kind}/{k}（還沒渲染完）")
if want("scenes"):
    for s in M.get("scenes", []):
        d = os.path.join(WORK, "scenes", s["id"])
        enc(d, os.path.join(V, "scenes", f"{s['id']}.mp4"), os.path.join(PI, "posters", "scenes", f"{s['id']}.jpg"), expect=s.get("frames", 0))
if want("refs"):
    for n in ("front", "back", "face"):
        src = M.get("sources", {}).get(n)
        if src and os.path.exists(os.path.join(P, src)):
            im = Image.open(os.path.join(P, src)).convert("RGB")
            w, h = im.size
            if n != "face":                               # 全身照裁成 2:3、上下各留一點
                tw = min(w, int(h / 1.5)); x0 = (w - tw) // 2
                im = im.crop((x0, 0, x0 + tw, min(h, int(tw * 1.5))))
            im.thumbnail((420, 630)); im.save(os.path.join(PI, f"ref_{n}.jpg"), quality=84); done.append(f"pictures/ref_{n}.jpg")
print(json.dumps({"exported": done, "skipped": skipped}, ensure_ascii=False))
