# 渲染動作片段（含頭髮擺動物理）→ 影格存在 WORK/actions/<代號>/，數字存 QA/motion.json。
# 可設：RKEYS（清單，預設全部）、OUTFIT（'base' 便服｜'costume' 服裝）、RES、YAW（鏡頭偏角）、SAMPLES。
# 每個動作一次算完（物理要連續）；完成的動作寫進 progress 檔，重跑會跳過（要重渲染就先刪那一行和影格資料夾）。
# 影格轉 mp4 用 blender-report-page 的 export_media.py（系統 Python，不在 Blender 裡）。
import bpy, os, math, time
use("studio", "pose_lib", "actions", "outfit_lib", "costume")
from bl_ext.blender_org.vrm.editor.spring_bone1 import handler as SB

OUTFIT = globals().get("OUTFIT", "base")
ROOT = os.path.join(WORK, "actions_costume" if OUTFIT == "costume" else "actions")
RES = globals().get("RES", (400, 600)); SUB = 2
os.makedirs(ROOT, exist_ok=True)
PROG = os.path.join(ROOT, "progress.txt")
done = set(open(PROG).read().split()) if os.path.exists(PROG) else set()
wear(OUTFIT)

sb = ARM.data.vrm_addon_extension.spring_bone1
for i in reversed(range(len(sb.springs))):
    if "hair" not in sb.springs[i].vrm_name.lower():
        sb.springs.remove(i)
sb.enable_animation = True


def reset_springs():
    for sp in sb.springs:
        for j in sp.joints:
            j.animation_state.initialized_as_tail = False


skirt = None
if OUTFIT == "costume" and "Skirt_Sway" in ARM.data.bones:
    use("skirt_phys")

cam = O["Camera"]; r = math.radians(globals().get("YAW", 25))
k_ = BODY_S                                     # 相機依體型縮放（新娘＝1）：比新娘高的角色，跳躍、舉手時頭和手才不會出畫面
aim(cam, (math.sin(r) * 4.6 * k_, -math.cos(r) * 4.6 * k_, 0.98 * k_), (0, 0, 0.84 * k_), 85)
sc.render.resolution_x, sc.render.resolution_y = RES; sc.render.resolution_percentage = 100
mesh_eval(True)
sc.eevee.taa_render_samples = globals().get("SAMPLES", 16)
keys = globals().get("RKEYS") or [k for k, *_ in ACTIONS]
t0 = time.time()
import json
MF = os.path.join(QA, "motion_costume.json" if OUTFIT == "costume" else "motion.json")
MOT = json.load(open(MF, encoding="utf8")) if os.path.exists(MF) else {}
FING = ("Thumb", "Index", "Middle", "Ring", "Little")


def snap():
    return {pb.name: (ARM.matrix_world @ pb.matrix).to_quaternion() for pb in ARM.pose.bones if pb.name.startswith("J_Bip")}


def diff(a, b):
    body = fing = 0.0
    for k, q in a.items():
        x = q.rotation_difference(b[k]).angle; x = math.degrees(min(x, 2 * math.pi - x))
        if any(f in k for f in FING): fing = max(fing, x)
        else: body = max(body, x)
    return body, fing


for key in keys:
    if key in done:
        continue
    name, fn, n = ACT[key]
    out = os.path.join(ROOT, key); os.makedirs(out, exist_ok=True)
    reset_springs()
    if skirt: skirt.reset()
    warm = max(24, n // 2)                          # 先空跑半輪讓頭髮穩定
    for fi in range(warm + n - 1):
        for s_i in range(SUB):                      # 最後一個子步驟剛好落在第 fi+1 格的整數時間
            tt = ((fi + 1 - warm - 1 + (s_i + 1) / SUB) / n) % 1.0   # 第 fi+1 格＝時間 (fi+1-warm)/n，渲染的第 1 格剛好是 t=0
            pose_frame(ARM, fn(tt))
            if skirt: skirt.step()
            SB.update_pose_bone_rotations(bpy.context, 1.0 / (24 * SUB))
        if fi + 1 >= warm:
            i = fi + 1 - warm
            bpy.context.view_layer.update()
            check_scales(ARM, allow=("Skirt_Sway",) + tuple(pb.name for pb in ARM.pose.bones if pb.name.startswith("J_Sec")))
            cur = snap()
            if i == 0:
                first = cur; vb = []; vf = []
            else:
                b_, f_ = diff(cur, prev); vb.append(b_); vf.append(f_)
            prev = cur
            sc.render.filepath = os.path.join(out, f"{i + 1:04d}.png")
            bpy.ops.render.render(write_still=True)
    b_, f_ = diff(first, prev); vb.append(b_); vf.append(f_)          # 頭尾相接那一格
    acc = [abs(vb[k] - vb[k - 1]) for k in range(1, len(vb))]
    MOT[key] = dict(body_vmax=round(max(vb), 1), body_jerk=round(max(acc), 1), seam=round(vb[-1], 1), finger_vmax=round(max(vf), 1), frames=n)
    json.dump(MOT, open(MF, "w", encoding="utf8"), indent=1)
    with open(PROG, "a") as fp:
        fp.write(key + "\n")
    print(key, round(time.time() - t0, 1))
sb.enable_animation = False
pose_frame(ARM, dict(STAND))
