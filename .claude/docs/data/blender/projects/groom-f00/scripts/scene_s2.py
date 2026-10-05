# 情境 s2（新郎）：攝影棚。新郎扮攝影師，舉相機對棚內的花台拍兩張（柔光箱閃燈），放下來看螢幕開心一下，再蹲低拍一張。
# 左手托鏡頭、右手食指按快門。西裝。
# 以新娘專案 projects/bride/scripts/scene_s2.py 為底（含相機「舉起↔看螢幕」的平滑過渡修正）：
# 角色座標的位置（相機路徑、手肘方向、蹲低深度）、攝影棚佈景、相機道具、鏡頭全部乘上 K（體型比例 BODY_S），
# 手才構得到相機、佈景和角色的比例也和新娘版一樣。
# exec 在 scene_lib.py 之後。對外：S2_N（格數）、s2_build()、s2_frame(f)、s2_props(f)、s2_cam(i)
import bpy, bmesh, math
from mathutils import Vector, Matrix

K = BODY_S                                    # 新郎 / 新娘 的體型比例
S2_N = 168                                    # 7 秒
S2_RZ = 90                                    # 角色面向 +X（棚內在 +X 那邊）
SCALE_K = Matrix.Scale(K, 4)


def kv(x, y, z):
    return Vector((x * K, y * K, z * K))


def to_w(p):
    """角色座標（面向 -Y，新娘尺寸）→ 世界（乘 K、轉 S2_RZ）"""
    return Matrix.Rotation(math.radians(S2_RZ), 4, "Z") @ kv(*p)


def _k(ob):
    """佈景以新娘尺寸建在世界原點座標系，物件整體放大 K（原點在世界原點，位置跟著等比例外移）"""
    ob.scale = (K, K, K)
    return ob


def s2_build():
    clear_props(); set_world((0.90, 0.90, 0.92), (0.50, 0.50, 0.53))   # 攝影棚淺灰背景、灰地板
    paper = mat("S2_Backdrop", (0.66, 0.71, 0.78), (0.50, 0.55, 0.64))
    bm = bmesh.new(); rows = []
    for j in range(13):                       # 無縫背景紙：牆面往下彎到地面
        a = math.pi / 2 * j / 12
        x = 2.55 - 0.5 * (1 - math.cos(a)); z = 0.5 - 0.5 * math.sin(a)
        rows.append([bm.verts.new((x, y, z)) for y in (-1.6, 1.6)])
    rows.insert(0, [bm.verts.new((2.55, y, 2.6)) for y in (-1.6, 1.6)])
    rows.append([bm.verts.new((1.3, y, 0.001)) for y in (-1.6, 1.6)])
    for r0, r1 in zip(rows, rows[1:]):
        bm.faces.new((r0[0], r0[1], r1[1], r1[0]))
    _k(solid("S2_Backdrop", bm, paper, smooth=True))
    white = mat("S2_White", (0.95, 0.94, 0.93), (0.78, 0.76, 0.78))
    bm = bmesh.new(); cyl(bm, Vector((1.95, 0, 0.36)), 0.17, 0.72, seg=32); cyl(bm, Vector((1.95, 0, 0.73)), 0.21, 0.03, seg=32)
    _k(solid("S2_Pedestal", bm, white))
    vase = mat("S2_Vase", (0.80, 0.86, 0.90), (0.62, 0.68, 0.76))
    bm = bmesh.new(); cyl(bm, Vector((1.95, 0, 0.86)), 0.06, 0.22, seg=24, r2=0.045); _k(solid("S2_Vase", bm, vase))
    pk = mat("S2_Rose", (0.96, 0.68, 0.70), (0.84, 0.5, 0.56)); wh = mat("S2_RoseW", (0.98, 0.95, 0.92), (0.82, 0.78, 0.8))
    lf = mat("S2_Leaf", (0.45, 0.62, 0.38), (0.3, 0.45, 0.3))
    bm = bmesh.new()
    import random; random.seed(5)
    for i in range(22):
        a = random.random() * 2 * math.pi; r = random.random() * 0.12
        ball(bm, Vector((1.95 + math.cos(a) * r, math.sin(a) * r, 1.02 + 0.08 * random.random() - r * 0.4)), 0.032 + 0.012 * random.random(), mi=i % 3, seg=12)
    _k(solid("S2_Flowers", bm, [pk, wh, lf], smooth=True))
    # 兩盞柔光箱（閃燈）
    black = mat("S2_Black", (0.12, 0.12, 0.13), (0.06, 0.06, 0.07))
    flash = mat("S2_Flash", (1.0, 1.0, 1.0), (1.0, 1.0, 1.0))
    for k, (xx, y) in enumerate(((2.05, -1.5), (1.55, 1.25))):
        bm = bmesh.new()
        c = Vector((xx, y, 1.65)); aimd = (Vector((1.95, 0, 1.0)) - c).normalized()
        rot = aimd.to_track_quat("-Z", "Y").to_matrix().to_4x4()
        box(bm, c, (0.55, 0.55, 0.32), rot, mi=0)
        box(bm, c + aimd * 0.165, (0.5, 0.5, 0.01), rot, mi=1)
        for t in range(3):                    # 腳架
            a = 2 * math.pi * t / 3
            p0 = Vector((xx + math.cos(a) * 0.35, y + math.sin(a) * 0.35, 0)); p1 = Vector((xx, y, 0.9))
            d = p1 - p0; cyl(bm, (p0 + p1) / 2, 0.012, d.length, rot=d.to_track_quat("Z", "Y").to_matrix().to_4x4(), mi=0)
        cyl(bm, Vector((xx, y, 1.2)), 0.015, 0.8, mi=0)
        _k(solid(f"S2_Softbox{k}", bm, [black, flash]))
    # 相機（局部：-Y 是鏡頭方向；整台在 cam_matrix 裡放大 K，抓點跟著放大）
    cam_m = mat("S2_CamBody", (0.13, 0.13, 0.14), (0.07, 0.07, 0.08)); ring = mat("S2_CamRing", (0.75, 0.75, 0.78), (0.5, 0.5, 0.55))
    glass = mat("S2_Glass", (0.25, 0.32, 0.42), (0.12, 0.16, 0.24)); screen = mat("S2_Screen", (0.55, 0.75, 0.9), (0.4, 0.55, 0.7))
    bm = bmesh.new()
    box(bm, Vector((0, 0, 0)), (0.135, 0.075, 0.09), mi=0)              # 機身
    box(bm, Vector((0, 0, 0.055)), (0.05, 0.05, 0.03), mi=0)            # 觀景窗突起
    box(bm, Vector((-0.055, -0.01, -0.005)), (0.03, 0.095, 0.085), mi=0)  # 右手握把
    cyl(bm, Vector((0.005, -0.075, -0.005)), 0.036, 0.08, axis="Y", mi=0)
    cyl(bm, Vector((0.005, -0.112, -0.005)), 0.038, 0.012, axis="Y", mi=1)
    cyl(bm, Vector((0.005, -0.119, -0.005)), 0.03, 0.004, axis="Y", mi=2)
    box(bm, Vector((0.005, 0.039, 0.0)), (0.09, 0.003, 0.06), mi=3)     # 背面螢幕
    box(bm, Vector((-0.05, 0.0, 0.05)), (0.012, 0.012, 0.006), mi=1)    # 快門鈕
    solid("S2_Camera", bm, [cam_m, ring, glass, screen])
    fl = bpy.data.objects.get("S2_FlashLight")
    if fl is None:
        fl = bpy.data.objects.new("S2_FlashLight", bpy.data.lights.new("S2_FlashLight", "POINT")); coll().objects.link(fl)
    fl.location = kv(1.4, 0, 1.6); fl.data.energy = 0.0; fl.data.color = (1, 0.98, 0.95)


SHOTS = (58, 74, 152)                         # 按快門的格（閃燈在 +2 格最亮）


def flash_amt(f):
    return max([max(0.0, 1 - abs(f - (k + 2)) / 3.0) for k in SHOTS])


CHEST = (0.01, -0.27, 1.12, 55.0)            # 胸前，螢幕朝上（x, y, z, pitch 度）
EYE = (-0.032, -0.135, 1.435, 0.0)            # 舉到右眼前
LOOK = (0.01, -0.24, 1.17, 55.0)              # 放下來看螢幕
CAM_KEYS = [(0, CHEST), (24, CHEST), (46, EYE), (80, EYE), (100, LOOK), (124, LOOK), (142, EYE), (S2_N, EYE)]


def cam_pose(f):
    """相機在角色座標（新娘尺寸）的位置、朝向（yaw, pitch, roll 度）。
    0~24 胸前、24~46 舉到眼前、80~100 放下看螢幕、124~142 蹲低再舉。
    新娘版用 up/look 兩個權重再在 up 0.6→0.4 切換路徑，切換只花 2 格，逐格量到第 89→90、133→134 格雙手一格移動 10 cm；
    改成關鍵格平滑內插（停住的姿勢和新娘版完全相同，只換中間的路徑）"""
    v = keys_interp(CAM_KEYS, f)
    p = Vector(v[:3]); pitch = v[3]
    up = seg(f, 24, 46) * (1 - seg(f, 80, 100)) + seg(f, 124, 142)
    # 舉起／放下的途中相機背面離胸口近，途中往前推 6 cm（舉到眼前、放在胸前時不變）
    p = p + Vector((0, -0.06, 0)) * (4 * up * (1 - up))
    return p, 0.0, pitch, 0.0


def cam_matrix(f, drop):
    p, yaw, pitch, roll = cam_pose(f)
    M = Matrix.Translation(Vector((0, 0, -drop)) + p * K) @ Matrix.Rotation(math.radians(pitch), 4, "X") @ SCALE_K
    return Matrix.Rotation(math.radians(S2_RZ), 4, "Z") @ M


def s2_drop(f):
    return 0.17 * K * seg(f, 120, 138)


def s2_props(f):
    O_ = bpy.data.objects
    O_["S2_Camera"].matrix_world = cam_matrix(f, s2_drop(f))
    a = flash_amt(f)
    O_["S2_FlashLight"].data.energy = 900 * a
    bpy.data.materials["S2_Flash"].vrm_addon_extension.mtoon1.emissive_factor = (a, a, a)


def s2_frame(f):
    drop = s2_drop(f)
    P = {}
    legs(P, drop, extra_l=(0, 0, 0), extra_r=(-8 * seg(f, 120, 138), 0, 0))
    up = seg(f, 24, 46) * (1 - seg(f, 80, 100)) + seg(f, 124, 142)
    look = seg(f, 82, 100) * (1 - seg(f, 124, 140))
    happy = seg(f, 100, 110) * (1 - seg(f, 122, 130))
    P["Spine"] = [("X", 6 * look + 4 * up), ("Y", 3 * happy * s(f / 12))]
    P["Head"] = [("X", 22 * look - 4 * up + 6 * (1 - up) * (1 - look)), ("Z", -4 * up), ("Y", 6 * happy)]
    arms_down(P)
    M = cam_matrix(f, drop)
    # 抓點在相機局部座標（M 已含 K）：右手握把＋食指在快門上方，左手掌托在鏡頭下面
    grip_w = M @ Vector((-0.072, -0.005, -0.03)); grip_tip = M @ Vector((-0.06, -0.05, 0.035))
    lens_w = M @ Vector((0.03, -0.06, -0.075)); lens_tip = M @ Vector((-0.01, -0.09, -0.04))
    press = max([max(0.0, 1 - abs(f - k) / 3.0) for k in SHOTS])
    face = {"Fcl_ALL_Fun": 0.5 * (1 - up), "Fcl_EYE_Close_L": 0.9 * up, "Fcl_ALL_Joy": happy, "Fcl_MTH_Small": 0.3 * up}
    # 右手食指：平常微彎搭在快門上（新娘版 1.0＝伸直，新郎的手比較大，伸直時指尖會翹到相機上方），按快門時再往下彎
    fr, fp = globals().get("FING", (0.45, 0.15))
    # 右手肘往下、略往前收（攝影師夾肘）：新娘版往外張的手肘，舉到眼前時手肘彎很深，皮膚會從西裝袖子的手肘戳出來（袖子只離皮膚 1.4 cm）
    rpole = globals().get("RPOLE", (-0.25, -0.2, 0.6))
    return dict(P, rz=S2_RZ, root=(0, 0, 0), ground=True,
                hands=("grip", ("grip", "point", fr - (fr - fp) * press)),
                ik=[("R", grip_w, to_w(rpole), grip_tip), ("L", lens_w, to_w((0.35, -0.2, 0.85)), lens_tip)], face=face)


def s2_cam(i):
    if globals().get("CAMDBG"):                           # 除錯用近照：1 他正前方、2 右前方、3 左側、4 主鏡頭同方向拉近，看手抓相機、手肘、臉
        c = int(globals()["CAMDBG"])
        loc = {1: (1.2, 0.0, 1.35), 2: (0.85, -0.85, 1.35), 3: (0.25, 1.15, 1.35), 4: (0.12, -1.6, 1.4)}[c]
        z = 1.3 - 0.17 * seg(i, 120, 138)
        aim(bpy.data.objects["Camera"], kv(*loc), kv(0.12, 0.0, z), 45); return
    u = ease(i / S2_N)
    # 新郎比新娘高，新娘版的鏡頭會切到腳：退遠、壓低看點、焦距 34，頭頂到鞋子都在畫面裡
    loc = kv(0.3, -3.85, 1.35).lerp(kv(0.38, -3.45, 1.3), u)
    aim(bpy.data.objects["Camera"], loc, kv(0.85, 0.0, 0.88), 34)


# 給 run_scene.py 用的描述（每個情境模組都要有）
SCENE = dict(id="s2", title="攝影棚當攝影師", N=S2_N, build=s2_build, frame=s2_frame, props=s2_props, cam=s2_cam,
             desc="舉相機對棚內的花台拍兩張（柔光箱閃燈），放下來看螢幕開心一下，再蹲低拍一張。左手托鏡頭、右手食指按快門。",
             outfit="costume", res=(960, 540), stills=())
