# 跑一個情境模組（背景 Blender，開 <name>_costume.blend；便服情境也用這個檔，wear("base") 會換回便服）：
#   blender.exe -b <PROJ>/<name>_costume.blend -P bl_cli.py -- --project <PROJ> --run run_scene SCENE=<模組名> MODE=preview|full [KEYS=0,40,80]
#
# 情境模組（放 PROJ/scripts/scene_<id>.py，或用預設庫 examples/scene_s1~s6.py）要定義
#   SCENE = dict(id, title, N, build, frame, props, cam, outfit='costume'|'base', res=(960,540), stills=(格數,...))
# MODE=preview：只渲染幾格（KEYS 或 0、¼、½、¾、最後一格）到 WORK/check/<id>/，640×360、不跑物理 —— 先看構圖和動作對不對
# MODE=full：整段渲染（含頭髮、裙擺物理）到 WORK/scenes/<id>/；完成後用 export_media.py 轉成 PROJ/videos/scenes/<id>.mp4
import bpy, os, json
use("studio", "pose_lib", "actions", "outfit_lib", "costume", "scene_lib")
_name = globals().get("SCENE")
if not isinstance(_name, str):
    raise RuntimeError("要指定 SCENE=<情境模組名>（例：scene_s3，或專案 scripts/ 裡的 scene_xxx）")
use(_name)
sc_ = globals()["SCENE"]                        # 模組 exec 後 SCENE 換成它自己的 dict
ARM.rotation_mode = "XYZ"
sc_["build"](); sc.camera = O["Camera"]; sc.eevee.taa_render_samples = 24
wear(sc_.get("outfit", "costume"))
MODE = globals().get("MODE", "preview")
if MODE == "preview":
    out = os.path.join(WORK, "check", sc_["id"]); os.makedirs(out, exist_ok=True)
    mesh_eval(True)
    N = sc_["N"]
    keys = [int(x) for x in (globals().get("KEYS") or [0, N // 4, N // 2, 3 * N // 4, N - 1])]
    for k in keys:
        pose_frame(ARM, sc_["frame"](k)); sc_["props"](k); bpy.context.view_layer.update(); sc_["cam"](k)
        shot(os.path.join(out, f"f{k:04d}.png"), (640, 360))
    print("PREVIEW", out, keys)
else:
    t = render_scene(sc_["id"], sc_["N"], sc_["frame"], sc_["cam"], res=tuple(sc_.get("res", (960, 540))),
                     outfit=sc_.get("outfit", "costume"), prop_fn=sc_["props"], stills=tuple(sc_.get("stills", ())))
    entry = {"id": sc_["id"], "title": sc_.get("title", sc_["id"]), "outfit": sc_.get("outfit", "costume"),
             "frames": sc_["N"], "desc": sc_.get("desc", ""), "module": _name}
    # 渲染要跑十幾分鐘，期間其他並行的情境可能已改過 project.json → 寫入前重讀，只更新自己這一筆
    MANIFEST.clear(); MANIFEST.update(json.load(open(_mf, encoding="utf8")))
    scenes = MANIFEST.setdefault("scenes", [])
    old = next((s for s in scenes if s.get("id") == sc_["id"]), None)
    if old is None:
        scenes.append(entry)                    # 新情境排最後
    else:
        old.update(entry)                       # 既有情境：原位更新，保留其他欄位
    save_manifest()
    print("FULL", sc_["id"], t)
