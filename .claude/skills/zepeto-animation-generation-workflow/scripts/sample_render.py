# 樣張渲染（背景 Blender）：照 JSON 規格，用任何渲染參數渲樣張場景 sit_sample.blend 的靜態圖或短片。
# 參數名稱和 render-settings mod 一致（settings＋expert_overrides），比較頁與 mod 的「試渲」共用這支。
# 用法：
#   "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b D:/render-work/zepeto-anim/sample/sit_sample.blend \
#       -P D:/render-work/zepeto-anim/scripts/sample_render.py -- <jobs.json> BODY=groom
# jobs.json：{"out_dir": "...", "jobs": [{"name": "samples_16", "t": 2.6 | "clip": [t0, t1], "set": {...}}]}
#   set 的欄位：resolution [w,h]、samples、shadow(low|mid|high)、raytracing、motion_blur、dof、look、exposure（相對場景原值）、
#     background(scene|alpha)、fps（短片才有意義）、expert {"eevee.xxx": 值, "render.xxx": 值}
# 結果：out_dir/<name>.jpg（透明背景 .png）或 <name>/ 影格＋<name>.mp4；out_dir/results.json 記每個工作的秒數
import bpy, json, sys, os, time, math, subprocess, shutil

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
spec = json.load(open(argv[0], encoding="utf8"))
OUT = spec["out_dir"]; os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene; r = sc.render; e = sc.eevee; cam = sc.camera
BASE_FPS = 30
BASE = dict(res=(r.resolution_x, r.resolution_y), exposure=sc.view_settings.exposure, look=sc.view_settings.view_transform,
            lens=cam.data.lens, sensor_fit=cam.data.sensor_fit)
PORTRAIT_LENS = 1.6                 # 直式鏡頭倍率（2026-10-12 比較 1.0／1.6／2.0 後定）
SHADOW = {"low": (0.5, 1, 4), "mid": (1.0, 1, 6), "high": (1.0, 3, 12)}     # (解析度倍率, 射線數, 步數)
DEFAULT = dict(resolution=[1920, 1080], samples=64, shadow="mid", raytracing=False, motion_blur=False, dof=False,
               look="Standard", exposure=0.0, background="scene", fps=30, expert={})
EXPERT_DEFAULT = {"eevee.gi_diffuse_bounces": 3, "eevee.use_fast_gi": False, "eevee.gi_glossy_clamp": 0.0,
                  "eevee.motion_blur_steps": 1, "render.filter_size": 1.5, "eevee.use_overscan": False}


def setp(path, v):
    obj = {"eevee": e, "render": r, "image_settings": r.image_settings}[path.split(".")[0]]
    setattr(obj, path.split(".", 1)[1], v)


def apply(s):
    s = {**DEFAULT, **s}
    w, h = s["resolution"]; r.resolution_x, r.resolution_y = w, h; r.resolution_percentage = 100
    # 直式：鏡頭照寬度取景會把人裁掉 → 改成固定水平視角（和橫式同寬），上下多看到一點
    cam.data.sensor_fit = "HORIZONTAL" if h > w else BASE["sensor_fit"]
    cam.data.lens = BASE["lens"] * s.get("lens_mul", PORTRAIT_LENS if h > w else 1.0)
    e.taa_render_samples = int(s["samples"])
    a, b, c = SHADOW[s["shadow"]]; e.shadow_resolution_scale = a; e.shadow_ray_count = b; e.shadow_step_count = c
    e.use_raytracing = bool(s["raytracing"])
    r.use_motion_blur = bool(s["motion_blur"])
    cam.data.dof.use_dof = bool(s["dof"])
    if s["dof"]:
        f = sc.get("sample_focus"); fd = sc.get("sample_focus_dist")
        if fd is not None:                                  # 跟拍的樣張：鏡頭到角色的距離固定
            cam.data.dof.focus_distance = fd
        elif f is not None:
            from mathutils import Vector
            cam.data.dof.focus_distance = (Vector(f) - cam.matrix_world.translation).length
        cam.data.dof.aperture_fstop = 0.8          # 樣張故意開大光圈，差別才看得出來
    sc.view_settings.view_transform = s["look"]
    sc.view_settings.exposure = BASE["exposure"] + float(s["exposure"])
    r.film_transparent = s["background"] == "alpha"
    for k, v in {**EXPERT_DEFAULT, **s.get("expert", {})}.items():
        setp(k, v)
    fps = int(s["fps"]); r.fps = fps; r.fps_base = 1.0
    r.frame_map_old, r.frame_map_new = 100, int(round(100 * fps / BASE_FPS))   # 換 fps：照時間內插關鍵影格
    return s


def frame_of(t, fps):
    return 1 + int(round(t * fps))


results = []
for job in spec["jobs"]:
    s = apply(job.get("set", {}))
    t0 = time.time()
    alpha = s["background"] == "alpha"
    if "clip" in job:
        fps = int(s["fps"]); a, b = job["clip"]
        d = os.path.join(OUT, job["name"]); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
        r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGBA" if alpha else "RGB"
        sc.frame_start, sc.frame_end = frame_of(a, fps), frame_of(b, fps)
        r.filepath = os.path.join(d, "f_")
        bpy.ops.render.render(animation=True)
        sec = time.time() - t0
        mp4 = os.path.join(OUT, job["name"] + ".mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-start_number", str(sc.frame_start),
                        "-i", os.path.join(d, "f_%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", mp4], check=True)
        results.append(dict(name=job["name"], sec=round(sec, 1), frames=sc.frame_end - sc.frame_start + 1, file=os.path.basename(mp4)))
    else:
        sc.frame_set(frame_of(job["t"], int(s["fps"])))
        png = alpha or job.get("png", False)          # png：mod 的試渲要 PNG（面板顯示圖片只吃 PNG）
        r.image_settings.file_format = "PNG" if png else "JPEG"
        r.image_settings.color_mode = "RGBA" if alpha else "RGB"
        if not png:
            r.image_settings.quality = 92
        f = os.path.join(OUT, job["name"] + (".png" if png else ".jpg"))
        r.filepath = f
        bpy.ops.render.render(write_still=True)
        results.append(dict(name=job["name"], sec=round(time.time() - t0, 1), file=os.path.basename(f)))
    print("SAMPLE", results[-1], flush=True)
    json.dump(results, open(os.path.join(OUT, "results.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("SAMPLE_DONE", len(results))
