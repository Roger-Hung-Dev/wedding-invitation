# 動作小片段自我檢驗（第 7.5 步）的總指揮：一般 Python（不是 Blender）。
#   python self_check.py <樣張.blend> <輸出資料夾> <誰> <起秒>-<迄秒>[,<起秒>-<迄秒>…] [--views side,feet] [--step 2] [--body groom,bride]
# 每一段 × 每個角度同時開一個背景 Blender 跑 close_clip.py（固定機位、其他人藏起來），渲完做成：
#   <段>_<角度>_strip.jpg：11 格並排的縮圖條（自己逐格看用）
#   <段>_check.mp4：各角度左右並排的小短片（放確認頁的 videos 給使用者看）
# 印出 SELF_CHECK_OK 和產生的檔案。數字檢查（腳抬幾次、方向來回、兩腳同時離地）在 MCP 裡用 zanim_check.foot_motion 量。
import argparse, glob, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
BL = r"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"

ap = argparse.ArgumentParser()
ap.add_argument("blend"); ap.add_argument("out"); ap.add_argument("who"); ap.add_argument("ranges")
ap.add_argument("--views", default="side,feet"); ap.add_argument("--step", default="2"); ap.add_argument("--body", default="groom,bride"); ap.add_argument("--par", default="2")
a = ap.parse_args()
views = a.views.split(",")
segs = [tuple(float(x) for x in r.split("-")) for r in a.ranges.split(",")]
os.makedirs(a.out, exist_ok=True)
jobs = [(k, t0, t1, v) for k, (t0, t1) in enumerate(segs) for v in views]
running = []
for k, t0, t1, v in jobs:                                  # 一次最多 --par 個背景 Blender（2026-10-13：同時 6 個、三個人都穿衣服時會當掉／只渲出 2 格）
    while len([p for p in running if p.poll() is None]) >= int(a.par):
        running[0].wait(); running = [p for p in running if p.poll() is None]
    d = os.path.join(a.out, f"t{k + 1}")
    log = open(os.path.join(a.out, f"t{k + 1}_{v}.log"), "w")
    running.append(subprocess.Popen([BL, "-b", a.blend, "-P", os.path.join(HERE, "close_clip.py"), "--", d, str(t0), str(t1), a.who, v, a.step, f"BODY={a.body}"],
                                    stdout=log, stderr=subprocess.STDOUT))
for p in running:
    p.wait()
made = []
for k in range(len(segs)):
    seg = f"t{k + 1}"; mp4s = []
    for v in views:
        fs = sorted(glob.glob(os.path.join(a.out, seg, f"{v}_*.jpg")))
        if not fs:
            print("MISSING", seg, v, "（看", os.path.join(a.out, f"{seg}_{v}.log"), "）"); continue
        pick = fs[:: max(1, len(fs) // 11)][:11]
        args = sum((["-i", f] for f in pick), [])
        flt = "".join(f"[{i}]scale=240:240[s{i}];" for i in range(len(pick))) + "".join(f"[s{i}]" for i in range(len(pick))) + f"hstack={len(pick)}"
        strip = os.path.join(a.out, f"{seg}_{v}_strip.jpg")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y"] + args + ["-filter_complex", flt, "-q:v", "3", strip], check=True)
        lst = os.path.join(a.out, f"{seg}_{v}.txt")
        open(lst, "w").write("".join(f"file '{f}'\nduration {int(a.step) / 30:.4f}\n" for f in fs) + f"file '{fs[-1]}'\n")
        mp4 = os.path.join(a.out, f"{seg}_{v}.mp4")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-vf", "scale=360:360,fps=30",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "28", mp4], check=True)
        mp4s.append(mp4); made.append(strip)
    if mp4s:
        out = os.path.join(a.out, f"{seg}_check.mp4")
        ins = sum((["-i", m] for m in mp4s), [])
        flt = "".join(f"[{i}]" for i in range(len(mp4s))) + f"hstack={len(mp4s)}" if len(mp4s) > 1 else "null"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y"] + ins + ["-filter_complex", flt, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "28", out], check=True)
        made.append(out)
print("SELF_CHECK_OK"); [print(" ", m) for m in made]
