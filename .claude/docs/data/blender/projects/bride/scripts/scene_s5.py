# 情境 5：氣球牆前自拍。右手舉手機，換三個姿勢各拍一張（螢幕閃白），最後放下手機看照片笑。禮服。
# 新娘專案版（第 3 版禮服）：只改左手垂放點（rest_l）與手貼臉頰時的左手腕位置（cheek），其他照 blender-scenario 的範例。
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

S5_N = 168
SNAPS = (52, 92, 128)


def s5_build():
    clear_props(); set_world((0.97, 0.90, 0.90), (0.56, 0.46, 0.47))
    cols = [mat("S5_BalPink", (0.97, 0.70, 0.74), (0.86, 0.52, 0.6)), mat("S5_BalWhite", (0.98, 0.96, 0.95), (0.84, 0.8, 0.84)),
            mat("S5_BalGold", (0.95, 0.80, 0.52), (0.8, 0.6, 0.38)), mat("S5_BalRose", (0.92, 0.55, 0.62), (0.76, 0.38, 0.48))]
    random.seed(8)
    bm = bmesh.new()
    for k in range(170):                          # 拱形氣球牆
        a = math.pi * random.random()
        r = 1.35 + random.uniform(-0.15, 0.15)
        c = Vector((math.cos(a) * r * 1.15, 0.85 + random.uniform(-0.1, 0.1), 0.15 + math.sin(a) * r * 1.35))
        ball(bm, c, 0.09 + 0.06 * random.random(), mi=random.randrange(4), seg=14)
    for k in range(18):                           # 地上散落的氣球
        c = Vector((random.uniform(-1.6, 1.6), random.uniform(0.3, 1.1), 0.1))
        ball(bm, c, 0.1 + 0.03 * random.random(), mi=random.randrange(4), seg=14)
    solid("S5_Balloons", bm, cols, smooth=True)
    wall = mat("S5_Wall", (0.96, 0.90, 0.88), (0.86, 0.78, 0.78))
    bm = bmesh.new(); box(bm, Vector((0, 1.05, 1.4)), (4.5, 0.05, 2.8)); solid("S5_Wall", bm, wall)
    neon = mat("S5_Neon", (1.0, 0.62, 0.75), (1.0, 0.62, 0.75)); neon.vrm_addon_extension.mtoon1.emissive_factor = (1.0, 0.55, 0.7)
    text_obj("S5_Sign", "Just Married", 0.32, (0, 1.0, 1.95), (math.radians(90), 0, 0), neon, font="C:/Windows/Fonts/segoeprb.ttf", extrude=0.01)
    body = mat("S5_Phone", (0.95, 0.88, 0.86), (0.8, 0.7, 0.7)); scr = mat("S5_Screen", (0.30, 0.34, 0.42), (0.2, 0.22, 0.3))
    bm = bmesh.new()
    box(bm, Vector((0, 0, 0)), (0.074, 0.008, 0.152), mi=0)        # 手機（局部：螢幕朝 +Y、上方 +Z）
    box(bm, Vector((0, 0.0045, 0)), (0.068, 0.001, 0.144), mi=1)
    box(bm, Vector((0.022, -0.005, 0.058)), (0.022, 0.003, 0.022), mi=0)   # 鏡頭模組
    solid("S5_Phone", bm, [body, scr])


def phone_M(f):
    """手機在角色座標：舉起到右前上方、螢幕對著臉；最後放低到胸前看照片"""
    up = seg(f, 8, 30) * (1 - seg(f, 140, 156))
    low = Vector((-0.06, -0.30, 1.12)); hi = Vector((-0.30, -0.46, 1.62))
    p = low.lerp(hi, up)
    face = Vector((0.0, -0.05, 1.45))
    d = (face - p).normalized()                   # 螢幕法線朝臉
    rot = d.to_track_quat("Y", "Z").to_matrix().to_4x4()
    tilt_low = Matrix.Rotation(math.radians(-35 * (1 - up)), 4, "X")
    return Matrix.Translation(p) @ rot @ tilt_low


def s5_props(f):
    bpy.data.objects["S5_Phone"].matrix_world = phone_M(f)
    fl = max([max(0.0, 1 - abs(f - k) / 2.5) for k in SNAPS])
    e = 0.15 + 0.85 * fl
    bpy.data.materials["S5_Screen"].vrm_addon_extension.mtoon1.emissive_factor = (e, e, e)


def s5_frame(f):
    P = {}
    Mp = phone_M(f)
    p1 = seg(f, 30, 44) * (1 - seg(f, 64, 74))       # 姿勢 1：歪頭＋臉旁比 YA＋眨眼
    p2 = seg(f, 70, 82) * (1 - seg(f, 104, 112))     # 姿勢 2：手背貼臉頰的花朵手
    p3 = seg(f, 108, 118) * (1 - seg(f, 138, 148))   # 姿勢 3：轉頭側臉、左手比小愛心
    look = seg(f, 146, 158)
    P["Head"] = [("Y", -12 * p1 + 10 * p2), ("Z", -8 * p1 + 6 * p2 - 18 * p3 - 6 * (1 - look) * (p1 + p2 + p3 < 0.1)), ("X", -6 * (p1 + p2) + 18 * look)]
    P["Spine"] = [("Y", -4 * p1 + 4 * p2), ("Z", -6 * p3)]
    arms_down(P)
    rw = Mp @ Vector((0.0, -0.012, -0.085)); rt = Mp @ Vector((0.0, -0.015, 0.03))
    # 第 3 版禮服：原本的垂放點 (0.16,-0.16,0.9) 會讓手指陷進垂墜和紗裙約 1.5 cm；往外上移、指尖順著裙面朝外下方，間隙約 9 mm
    rest_l = (Vector((0.20, -0.20, 0.94)), Vector((0.24, -0.24, 0.85)))
    peace = (Vector((0.10, -0.11, 1.34)), Vector((0.09, -0.13, 1.52)))
    # 第 3 版禮服：原本手腕 (0.10,-0.09,1.30) 會壓在胸口褶邊上約 8 mm；手腕往前外移、指尖仍在臉頰（離臉約 3 mm）
    cheek = (Vector((0.12, -0.13, 1.31)), Vector((0.05, -0.1, 1.42)))
    heart = (Vector((0.07, -0.22, 1.25)), Vector((0.04, -0.26, 1.36)))
    lw = rest_l[0] * (1 - p1 - p2 - p3) + peace[0] * p1 + cheek[0] * p2 + heart[0] * p3
    lt = rest_l[1] * (1 - p1 - p2 - p3) + peace[1] * p1 + cheek[1] * p2 + heart[1] * p3
    # 第 3 版禮服：換姿勢途中手會掃過胸口褶邊，途中往前拱 6 cm（姿勢定住時不變）
    wr = max(0.0, min(1.0, 1 - p1 - p2 - p3)); arc = Vector((0.0, -0.06, 0.0)) * (4 * wr * (1 - wr))
    lw = lw + arc; lt = lt + arc
    hand_l = "relax" if p1 + p2 + p3 < 0.5 else ("peace" if p1 > 0.5 else ("open" if p2 > 0.5 else "pinch"))
    face = {"Fcl_ALL_Fun": 0.5, "Fcl_EYE_Close_R": p1, "Fcl_ALL_Joy": 0.6 * p2 + 0.8 * look, "Fcl_MTH_U": 0.5 * p3}
    return dict(P, ground=True, hands=(hand_l, "grip"),
                ik=[("R", rw, (-0.5, -0.1, 1.1), rt), ("L", lw, (0.45, -0.1, 0.9), lt)], face=face)


def s5_cam(i):
    u = ease(i / S5_N)
    loc = Vector((0.45, -3.3, 1.5)).lerp(Vector((0.25, -2.9, 1.48)), u)
    aim(bpy.data.objects["Camera"], loc, (-0.05, 0.2, 1.3), 36)


# 給 run_scene.py 用的描述（每個情境模組都要有）
SCENE = dict(id="s5", title="氣球牆前自拍", N=S5_N, build=s5_build, frame=s5_frame, props=s5_props, cam=s5_cam,
             desc="右手舉手機，換三個姿勢各拍一張（螢幕閃白）：比 YA 眨眼、手貼臉頰、側臉比小愛心，最後放低手機看照片。",
             outfit="costume", res=(960, 540), stills=())
