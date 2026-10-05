# 依規格建服裝（可在背景 Blender 跑）：
#   blender.exe -b <PROJ>/<name>.blend -P bl_cli.py -- --project <PROJ> --run build_costume [SPEC=<json 路徑>] [CHECK=true]
# 1. 規格要露肩卻還沒補皮膚 → 先 run_fill()
# 2. 裙子有開 → 建 Skirt_Sway 骨頭（裙擺擺動用）
# 3. build_costume() → wear("costume") → 存成 PROJ/<name>_costume.blend（基礎檔不動）
# 4. CHECK=true（預設）→ 檢查圖 WORK/check/costume/：0/45/90/180/270 度全身、胸口、後腦、下擺
import bpy, os, math, json
use("studio", "pose_lib", "outfit_lib", "costume", "skirt_phys")
A_ = bpy.data.objects[f"{WHO}_Armature"]
spec = load_spec(globals().get("SPEC"))
reset_pose(A_); A_.location = (0, 0, 0); A_.rotation_mode = "XYZ"; A_.rotation_euler = (0, 0, 0)
log = {}
if spec.get("needs_body_fill") and f"{WHO}_BodyFill" not in bpy.data.objects:
    use("body_fill"); log["fill"] = run_fill()
if spec.get("components", {}).get("skirt", {}).get("enabled"):
    setup_skirt_bone(A_, 0.985 * S_BODY)
parts = build_costume(spec)
wear("costume")
out_blend = os.path.join(PROJ, MANIFEST["blend"]["costume"])
bpy.ops.wm.save_as_mainfile(filepath=out_blend)
MANIFEST.setdefault("costume", {}).update({"parts": parts, "summary": spec.get("summary", ""), "name": spec.get("name", "")})
MANIFEST.setdefault("stages", {})["03"] = "built"
save_manifest()
if globals().get("CHECK", True):
    use("pose_lib")
    apply_pose(A_, dict(STAND))
    cam = bpy.data.objects["Camera"]; sc.camera = cam
    out = os.path.join(WORK, "check", "costume"); os.makedirs(out, exist_ok=True)
    sc.eevee.taa_render_samples = 24
    for a in (0, 45, 90, 180, 270):
        A_.rotation_euler = (0, 0, math.radians(a))
        aim(cam, (0, -4.4 * S_BODY, 0.95 * S_BODY), (0, 0, 0.84 * S_BODY), 85); shot(os.path.join(out, f"c_{a:03d}.png"), (500, 750))
    A_.rotation_euler = (0, 0, 0)
    k = S_BODY
    aim(cam, (0.25 * k, -1.3 * k, 1.35 * k), (0, 0, 1.2 * k), 85); shot(os.path.join(out, "c_bust.png"), (500, 500))
    aim(cam, (0.1 * k, 1.3 * k, 1.4 * k), (0, 0, 1.35 * k), 85); shot(os.path.join(out, "c_headback.png"), (500, 500))
    aim(cam, (0.3 * k, -1.4 * k, 0.35 * k), (0, 0, 0.15 * k), 85); shot(os.path.join(out, "c_hem.png"), (500, 500))
    reset_pose(A_)
print("COSTUME", json.dumps({"blend": out_blend, "parts": parts, **log}, ensure_ascii=False))
