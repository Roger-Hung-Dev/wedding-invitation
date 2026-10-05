# 展示用渲染（背景 Blender）：影格存 WORK/showcase/<項目>/，之後用 export_media.py 轉成 PROJ/videos、PROJ/pictures。
#   MODE=base    （開 <name>.blend）        → turn_body（全身 360°）、turn_face（臉 360°＋眨眼）、hands（6 手勢 × 掌心/手背）、
#                                            expr（5 表情）、feet（4 角度）
#   MODE=costume（開 <name>_costume.blend）→ turn_costume（服裝 360°）、costume_stills（正面/背面）、costume_moves（揮手→轉圈→跳躍，含頭髮與裙擺物理）
# 可設 ONLY=["turn_body", ...] 只做其中幾項；已存在的影格會跳過（render_seq）。
import bpy, os, math
use("studio", "pose_lib", "actions", "outfit_lib", "costume", "render_lib")
MODE = globals().get("MODE", "base")
ONLY = set(globals().get("ONLY") or [])
k = BODY_S
cam = O["Camera"]; sc.camera = cam
OUT = os.path.join(WORK, "showcase"); os.makedirs(OUT, exist_ok=True)
want = lambda n: not ONLY or n in ONLY
wear("costume" if MODE == "costume" else "base")
mesh_eval(True); sc.eevee.taa_render_samples = 24
ARM.rotation_mode = "XYZ"


def turntable(name, n, cam_loc, target, lens, res, face_fn=None):
    aim(cam, cam_loc, target, lens)
    def setup(i, n_):
        ARM.rotation_euler = (0, 0, 2 * math.pi * i / n_)
        if face_fn: set_face(face_fn(i / n_))
    render_seq(os.path.join(OUT, name), n, setup, res=res, budget=1e9)
    ARM.rotation_euler = (0, 0, 0)


pose_frame(ARM, dict(STAND, ground=True)); set_face({"Fcl_ALL_Fun": 0.35})
if MODE == "base":
    if want("turn_body"):
        turntable("turn_body", 96, (0, -4.4 * k, 0.95 * k), (0, 0, 0.82 * k), 85, (600, 900))
    if want("turn_face"):
        turntable("turn_face", 72, (0, -1.2 * k, 1.46 * k), (0, 0, 1.43 * k), 85, (540, 540),
                  face_fn=lambda t: {"Fcl_ALL_Fun": 0.35, "Fcl_EYE_Close": 1.0 if 0.30 < t < 0.33 else 0.0})
    if want("hands"):                                  # 左手 6 種手勢：前臂轉成掌心朝鏡頭
        d = os.path.join(OUT, "hands"); os.makedirs(d, exist_ok=True)
        O[f"{WHO}_Hair"].hide_render = True
        for h in ("relax", "open", "fist", "point", "peace", "grip"):
            reset_pose(ARM); ARM.location = (0, 0, 0); hand_pose(ARM, "L", h); hand_pose(ARM, "R", "relax")
            rot_world(ARM, "J_Bip_L_LowerArm", "X", -90); bpy.context.view_layer.update()
            hp = ARM.matrix_world @ ARM.pose.bones["J_Bip_L_Middle1"].head
            aim(cam, (hp.x, hp.y - 0.42 * k, hp.z + 0.02), tuple(hp), 85); shot(os.path.join(d, f"palm_{h}.png"), (360, 360))
            aim(cam, (hp.x, hp.y + 0.42 * k, hp.z + 0.02), tuple(hp), 85); shot(os.path.join(d, f"back_{h}.png"), (360, 360))
        O[f"{WHO}_Hair"].hide_render = False
        pose_frame(ARM, dict(STAND, ground=True))
    if want("expr"):
        d = os.path.join(OUT, "expr"); os.makedirs(d, exist_ok=True)
        for nm, vals in (("joy", {"Fcl_ALL_Joy": 1}), ("fun", {"Fcl_ALL_Fun": 1}), ("surp", {"Fcl_ALL_Surprised": 1}),
                         ("wink", {"Fcl_EYE_Close_R": 1, "Fcl_ALL_Fun": 0.5}), ("A", {"Fcl_MTH_A": 1, "Fcl_ALL_Fun": 0.4})):
            set_face(vals); aim(cam, (0, -0.75 * k, 1.47 * k), (0, 0, 1.45 * k), 85); shot(os.path.join(d, f"{nm}.png"), (300, 300))
        set_face({"Fcl_ALL_Fun": 0.35})
    if want("feet"):
        d = os.path.join(OUT, "feet"); os.makedirs(d, exist_ok=True)
        for nm, (l, t) in {"f": ((0.0, -0.75, 0.25), (0, 0, 0.08)), "q": ((0.5, -0.55, 0.25), (0, 0, 0.08)),
                           "s": ((0.75, 0, 0.22), (0, 0, 0.08)), "b": ((-0.3, 0.7, 0.25), (0, 0, 0.08))}.items():
            aim(cam, tuple(v * k for v in l), tuple(v * k for v in t), 85); shot(os.path.join(d, f"{nm}.png"), (400, 300))
else:
    if want("turn_costume"):
        turntable("turn_costume", 96, (0, -4.6 * k, 0.95 * k), (0, 0, 0.84 * k), 80, (600, 900))
    if want("costume_stills"):
        d = os.path.join(OUT, "costume_stills"); os.makedirs(d, exist_ok=True)
        aim(cam, (0, -3.6 * k, 0.9 * k), (0, 0, 0.86 * k), 62); shot(os.path.join(d, "front.png"), (420, 630))
        ARM.rotation_euler = (0, 0, math.radians(200)); shot(os.path.join(d, "back.png"), (420, 630)); ARM.rotation_euler = (0, 0, 0)
    if want("costume_moves"):
        from bl_ext.blender_org.vrm.editor.spring_bone1 import handler as SB
        use("skirt_phys")
        seq = [("wave", 48), ("spin", 72), ("jump", 60)]
        sb = ARM.data.vrm_addon_extension.spring_bone1
        for i in reversed(range(len(sb.springs))):
            if "hair" not in sb.springs[i].vrm_name.lower():
                sb.springs.remove(i)
        sb.enable_animation = True
        for sp in sb.springs:
            for j in sp.joints:
                j.animation_state.initialized_as_tail = False
        has_skirt = "Skirt_Sway" in ARM.data.bones      # 沒有裙子的服裝（西裝等）沒有裙擺骨頭，不跑裙擺物理
        skirt.reset()
        total = sum(n for _, n in seq)
        def fn_at(g):
            g = g % total
            for key, n in seq:
                if g < n:
                    return ACT[key][1](g / n)
                g -= n
        d = os.path.join(OUT, "costume_moves"); os.makedirs(d, exist_ok=True)
        r = math.radians(25); aim(cam, (math.sin(r) * 4.8 * k, -math.cos(r) * 4.8 * k, 1.0 * k), (0, 0, 0.86 * k), 80)
        sc.render.resolution_x, sc.render.resolution_y = 480, 720; sc.eevee.taa_render_samples = 16
        for fi in range(24 + total):
            for s_i in range(2):
                g = fi - 24 + (s_i + 1) / 2 - 1
                pose_frame(ARM, fn_at(max(0.0, g)) if g >= 0 else dict(STAND))
                if has_skirt:
                    skirt.step()
                SB.update_pose_bone_rotations(bpy.context, 1 / 48)
            if fi >= 24:
                p = os.path.join(d, f"{fi - 23:04d}.png")
                if not os.path.exists(p):
                    bpy.context.view_layer.update(); sc.render.filepath = p; bpy.ops.render.render(write_still=True)
        sb.enable_animation = False
print("SHOWCASE", MODE, sorted(os.listdir(OUT)))
