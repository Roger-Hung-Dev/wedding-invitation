# 開場影片 V12 的工作入口（由 prod_cli.py 執行）。MODE：
#   couple   開 bride_costume.blend → 附加新郎 → 存 blend/couple.blend（只需做一次；之後都開這個檔）
#   info     印兩個角色的尺寸、EEVEE 設定（檢查用）
#   preview  SHOT=03 [KEYS=秒,秒] [RES=960,540] [SAMPLES=16]：渲染代表格到 pictures/preview/<shot>_<秒>.jpg（不跑物理）
#   full     SHOT=03 [RES=1920,1080] [LAYERS=beauty,cast]：整段渲染到 D:\render-work\opening-v12\shots\<shot>\<layer>\（第二階段）
#   save     建好兩個景、存 blend/opening_v12_sets.blend（給人開檔看）
import bpy, os, json, time, math

MODE = globals().get("MODE", "preview")
if MODE == "couple":
    pass
use("prod_env")

if MODE == "couple":
    cast_collections()
    for nm_ in ("Sun", "Fill", "Rim", "Floor"):
        o = bpy.data.objects.get(nm_)
        if o:
            bpy.data.objects.remove(o, do_unlink=True)
    wear("costume"); G["wear"]("costume")
    for im in bpy.data.images:
        if not im.packed_file and im.filepath and not os.path.exists(bpy.path.abspath(im.filepath)):
            print("MISSING_IMAGE", im.name, im.filepath)
    p = os.path.join(BLEND_DIR, "couple.blend")
    bpy.ops.wm.save_as_mainfile(filepath=p, relative_remap=True)
    print("SAVED", p)

if globals().get("RATE"):                  # 2026-10-06 情境版預覽（preview-v2）：RATE=24 改影格率（預設 30＝正式版）
    FPS = int(globals()["RATE"])
use("set_desk", "set_garden", "shots_desk", "shots_garden", "set_v2", "shots_v2")
render_setup()

if MODE == "info":
    for k, ns in CAST.items():
        A = ns["ARM"]
        print("CAST", k, "BODY_S", round(ns["BODY_S"], 3), "head_z", round(A.data.bones["J_Bip_C_Head"].head_local.z, 3),
              "shoulder_w", round(A.data.bones["J_Bip_L_UpperArm"].head_local.x * 2, 3))
    print("EEVEE", [p.identifier for p in sc.eevee.bl_rna.properties][:80])

elif MODE == "preview" or (MODE == "couple" and globals().get("SHOT")):      # couple 加 SHOT＝存檔後順便預覽
    res = tuple(int(x) for x in str(globals().get("RES", "960,540")).split(","))
    samples = int(globals().get("SAMPLES", 16))
    for o in (ARM, G["ARM"]):
        mesh_eval(False, o.name)
    for sid in str(globals().get("SHOT", "03")).split(","):        # SHOT=02,03,05 一次跑好幾幕
        S = SHOTS[sid]
        keys = [float(k) for k in (globals().get("KEYS") or S.get("stills", [0.0]))]
        S["build"]()
        stage(S["set"], cast=S.get("cast", False))
        t_all = time.time()
        for t in keys:
            t0 = time.time()
            S["frame"](t)
            bpy.context.view_layer.update()
            tp = time.time() - t0
            pdir = globals().get("PDIR") or PREVIEW_DIR             # PDIR＝預覽圖另存的資料夾（preview-v2 用）
            os.makedirs(pdir, exist_ok=True)
            path = os.path.join(pdir, f"{sid}_{t:05.2f}s.jpg")
            render_still(path, res, samples)
            print("PREVIEW", path, "pose", round(tp, 2), "total", round(time.time() - t0, 2), flush=True)
        print("PREVIEW_DONE", sid, round(time.time() - t_all, 1), flush=True)

elif MODE == "full":
    sid = str(globals().get("SHOT"))
    S = SHOTS[sid]
    res = tuple(int(x) for x in str(globals().get("RES", "1920,1080")).split(","))
    samples = int(globals().get("SAMPLES", 32))
    layers = [x for x in str(globals().get("LAYERS", "beauty")).split(",") if x]
    S["build"]()
    stage(S["set"], cast=S.get("cast", False))
    for o in (ARM, G["ARM"]):
        mesh_eval(False, o.name)                               # 擺姿勢時不重算網格變形（渲染用的是 show_render，不受影響）
    n = int(round(S["dur"] * FPS)) + int(S.get("tail", 0) * FPS)
    if globals().get("N"):                                     # 測試用：只算前 N 格（估時間）
        n = min(n, int(globals()["N"]))
    sc.eevee.taa_render_samples = samples
    sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "RGBA"
    # 一次物理模擬、每格依序渲染每一層（第一層走 render_cast 的主迴圈，其餘層在 on_frame 裡切換後各渲染一次）
    root = os.path.join(globals().get("OUT") or PWORK, "shots" if not globals().get("N") else "timing", sid)   # OUT＝影格根目錄（preview-v2 用）
    primary, extra = layers[0], layers[1:]
    layer_mode(primary)
    actors = S.get("actors", [])
    tracks = {}
    T0 = S.get("t0", 0.0)
    fqa = FootQA(actors, t0=T0, skip=S.get("qa_skip", ())) if actors else None

    def pose_fn(f):
        S["frame"](T0 + f / FPS, props=True, cast=True, cam=False)

    def cam_fn(i):
        S["frame"](T0 + i / FPS, props=False, cast=False, cam=True)

    def on_frame(i):
        if S.get("track"):
            tracks[i + 1] = S["track"]()
        if fqa:
            fqa.record(i)
        for lay in extra:
            p = os.path.join(root, lay, f"{i + 1:04d}.png")
            if not os.path.exists(p):
                os.makedirs(os.path.dirname(p), exist_ok=True)
                layer_mode(lay); sc.render.filepath = p; bpy.ops.render.render(write_still=True)
        layer_mode(primary)

    out = os.path.join(root, primary)
    if actors:
        sk = skirts_of(actors) if S.get("skirt", True) else []         # skirt=False：這一幕不跑裙擺物理（⑦ 坐姿把裙子收小）
        t = render_cast(out, n, pose_fn, cam_fn, arms_of(actors), skirts=sk, fps=FPS, res=res, on_frame=on_frame)
    else:
        os.makedirs(out, exist_ok=True); t0 = time.time()
        sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
        for i in range(n):
            S["frame"](T0 + i / FPS); on_frame(i)
            p = os.path.join(out, f"{i + 1:04d}.png")
            if not os.path.exists(p):
                sc.render.filepath = p; bpy.ops.render.render(write_still=True)
        t = round(time.time() - t0, 1)
    if tracks:
        track_dump(os.path.join(root, "track.json"), tracks)
    if fqa:
        q = fqa.summary(); track_dump(os.path.join(root, "qa_feet.json"), q); print("QA_FEET", sid, json.dumps(q, ensure_ascii=False), flush=True)
    print("FULL", sid, layers, n, "frames", t, "s", round(t / max(1, n), 2), "s/frame", flush=True)
    layer_mode("beauty")

elif MODE == "painting":
    # ② 開頭的鏡頭位置拍一張空拱門（4:3，水平視角和 16:9 成片相同）→ make_assets.py watercolor 轉成信紙上的水彩小畫
    SHOTS["02"]["build"](); stage("Set_Garden", cast=False); garden_parts(())
    petals_update(0.0, lambda i, rnd: None)
    look((0, -6.4, 1.05), (0, 0.8, 1.22), 36); cam_obj().data.sensor_fit = "HORIZONTAL"
    render_still(os.path.join(TEX, "garden_for_painting.png"), (1600, 1200), 32, fmt="PNG")
    cam_obj().data.sensor_fit = "AUTO"
    print("PAINTING_SRC_DONE")

elif MODE == "save":
    for sid in ("01", "03"):
        SHOTS[sid]["build"]()
    stage("Set_Garden", cast=True)
    p = os.path.join(BLEND_DIR, "opening_v12_sets.blend")
    bpy.ops.wm.save_as_mainfile(filepath=p, copy=True, relative_remap=True)
    print("SAVED", p)
