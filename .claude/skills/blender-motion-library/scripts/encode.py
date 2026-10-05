# PNG 序列 → mp4（H.264、24fps、yuv420p）。用法：python encode.py <png資料夾> <輸出.mp4> [loops] [寬]
# loops：重複幾次（短的循環動作播起來比較好看）；寬：縮放到這個寬度（高度等比、取偶數）
import subprocess, sys, os, glob

src, dst = sys.argv[1], sys.argv[2]
loops = int(sys.argv[3]) if len(sys.argv) > 3 else 1
width = int(sys.argv[4]) if len(sys.argv) > 4 else 0
frames = sorted(glob.glob(os.path.join(src, "*.png")))
lst = dst + ".txt"
with open(lst, "w") as f:
    for _ in range(loops):
        for p in frames:
            f.write(f"file '{os.path.abspath(p)}'\nduration {1/24:.6f}\n")
vf = f"scale={width}:-2:flags=lanczos," if width else ""
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
       "-vf", vf + "format=yuv420p", "-r", "24", "-c:v", "libx264", "-crf", "23", "-preset", "slow",
       "-movflags", "+faststart", dst]
subprocess.run(cmd, check=True)
os.remove(lst)
print(dst, len(frames) * loops, "frames", os.path.getsize(dst) // 1024, "KB")
