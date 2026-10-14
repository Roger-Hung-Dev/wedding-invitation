# 正式剪接（2026-10-12）：用和展示頁同一份 edit_styles.js，在本機 Chrome 無頭模式逐格截圖，再用 ffmpeg 接成 mp4。
# 所以成品和預覽一模一樣。
# 用法：
#   python render_edit.py --settings <film.json 或設定 json> --program <program.json 或 demo> --out <資料夾>
#                         [--size 1920x1080] [--fps 30] [--from 秒] [--to 秒]
#                         [--audio 配樂檔 --music-from 秒 --audio-at 秒 --fade-out 秒]   → 另出 edit_audio.mp4
#   settings：edit.json（render-settings 面板寫在 film.json 旁邊；舊版是 film.json 的 "edit" 段），或直接是 {caption_style, font, ...}
#   program：{ "shots": [{ id, label, src(影片完整路徑), dur, cap: [標題, 內容], cue: [進場, 退場或 null] }] }；demo＝樣式庫的示範節目
# 結果：<out>/frames/f_00001.png…、<out>/edit.mp4、<out>/edit_info.json（用了哪些設定、幾格、花多久）
import argparse, asyncio, json, os, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_showcase as BS
from cdp_capture import Chrome


async def run(a):
    cat, js, tpl = BS.load()
    BS.check(cat, js)
    st = json.load(open(a.settings, encoding="utf8")) if a.settings else {}
    st = st.get("edit", st)
    settings = {**cat["defaults"], **st}
    prog = BS.local_program(cat) if a.program == "demo" else json.load(open(a.program, encoding="utf8"))
    for s in prog["shots"]:
        if not s["src"].startswith("file:///"):
            s["src"] = "file:///" + s["src"].replace("\\", "/")
    w, h = map(int, a.size.lower().split("x"))
    fr = os.path.join(a.out, "frames"); shutil.rmtree(fr, ignore_errors=True); os.makedirs(fr)
    page = os.path.join(a.out, "_render.html")
    open(page, "w", encoding="utf8").write(BS.page(cat, js, tpl, prog, "render", settings, local=True))
    t0 = time.time()
    async with Chrome(w, h) as c:
        await c.goto(page)
        dur = await c.eval("window.__player.duration")
        a0 = a.t_from or 0.0; a1 = min(a.t_to or dur, dur)
        n = int(round((a1 - a0) * a.fps))
        for i in range(n):
            await c.eval(f"window.__player.seek({a0 + i / a.fps})", await_promise=True)
            await c.shot(os.path.join(fr, f"f_{i + 1:05d}.png"))
    sec = time.time() - t0
    mp4 = os.path.join(a.out, "edit.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(a.fps), "-i", os.path.join(fr, "f_%05d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", mp4], check=True)
    os.remove(page)
    if a.audio:
        mp4 = mix_audio(mp4, a, n / a.fps)
    info = dict(settings=settings, size=[w, h], fps=a.fps, frames=n, from_s=a0, to_s=a1, capture_s=round(sec, 1),
                per_frame_s=round(sec / max(1, n), 3), mp4=mp4,
                audio=dict(file=a.audio, music_from_s=a.music_from, film_at_s=a.audio_at, fade_out_s=a.fade_out) if a.audio else None)
    json.dump(info, open(os.path.join(a.out, "edit_info.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print("EDIT", json.dumps(info, ensure_ascii=False))


def mix_audio(video, a, dur):
    """配樂混進去（2026-10-12 導演端要求）：配樂從 music_from 秒開始取、在片子的 audio_at 秒開始響；
    片子比配樂長就補靜音、比配樂短就截掉；結尾 fade_out 秒淡出。影像不重新編碼。輸出 edit_audio.mp4"""
    out = os.path.join(os.path.dirname(video), "edit_audio.mp4")
    at = max(0.0, a.audio_at); fo = max(0.0, min(a.fade_out, dur))
    flt = f"[1:a]adelay={int(at * 1000)}:all=1,apad,atrim=0:{dur:.3f}" + (f",afade=t=out:st={dur - fo:.3f}:d={fo:.3f}" if fo > 0 else "") + "[a]"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-ss", str(a.music_from), "-i", a.audio,
                    "-filter_complex", flt, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", out], check=True)
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--settings"); p.add_argument("--program", default="demo"); p.add_argument("--out", required=True)
    p.add_argument("--size", default="1920x1080"); p.add_argument("--fps", type=int, default=30)
    p.add_argument("--from", dest="t_from", type=float); p.add_argument("--to", dest="t_to", type=float)
    p.add_argument("--audio", help="配樂檔（mp3／wav／m4a）；不給就沒有聲音")
    p.add_argument("--music-from", dest="music_from", type=float, default=0.0, help="配樂從第幾秒開始取")
    p.add_argument("--audio-at", dest="audio_at", type=float, default=0.0, help="配樂在片子第幾秒開始響")
    p.add_argument("--fade-out", dest="fade_out", type=float, default=1.0, help="結尾淡出幾秒")
    a = p.parse_args(); os.makedirs(a.out, exist_ok=True)
    asyncio.run(run(a))
