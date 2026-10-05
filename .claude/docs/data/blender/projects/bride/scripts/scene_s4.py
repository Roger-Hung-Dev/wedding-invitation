# 情境 4：切婚禮蛋糕。雙手握刀切下去 → 停住看鏡頭笑 → 拔刀 → 左手比 YA。禮服。
# 新娘專案第 3 版禮服（垂墜貼身＋軟蝴蝶結）：原本桌巾垂到 z≈0.53，整段插進右側內層垂墜約 7.5 cm、外層紗裙約 2.4 cm。
# 改成桌巾只垂 4 cm、桌腳加長接到桌面，整張桌子連蛋糕和刀沿遠離角色的方向移 2 cm（手到刀的距離仍 < 手臂長 94%）。
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

S4_N = 156
S4_RZ = 45                                    # 稍微轉向左前方的桌子
_S4_PUSH = Vector((0.55, -0.40, 0.0)).normalized() * 0.02
TABLE = Vector((0.55, -0.40, 0.0)) + _S4_PUSH; CAKE = Vector((0.42, -0.30, 0.0)) + _S4_PUSH; TOP_Z = 0.76


def s4_build():
    clear_props(); set_world((0.96, 0.92, 0.86), (0.52, 0.45, 0.40))
    cloth = mat("S4_Cloth", (0.97, 0.96, 0.95), (0.82, 0.80, 0.84))
    bm = bmesh.new()
    cyl(bm, TABLE + Vector((0, 0, TOP_Z - 0.015)), 0.32, 0.03, seg=48)
    cyl(bm, TABLE + Vector((0, 0, TOP_Z - 0.025)), 0.33, 0.03, seg=48, r2=0.322)    # 桌巾只垂 4 cm（再長就會碰到蓬裙與垂墜）
    cyl(bm, TABLE + Vector((0, 0, (TOP_Z - 0.03) / 2)), 0.05, TOP_Z - 0.03, seg=16)
    cyl(bm, TABLE + Vector((0, 0, 0.01)), 0.2, 0.02, seg=32)
    solid("S4_Table", bm, cloth)
    icing = mat("S4_Icing", (0.99, 0.97, 0.94), (0.86, 0.82, 0.84))
    rib = mat("S4_CakeRibbon", (0.96, 0.70, 0.72), (0.84, 0.52, 0.58))
    pk = mat("S4_CakeRose", (0.97, 0.66, 0.70), (0.84, 0.48, 0.56)); lf = mat("S4_CakeLeaf", (0.5, 0.66, 0.42), (0.34, 0.48, 0.32))
    bm = bmesh.new(); z = TOP_Z
    for r, h in ((0.16, 0.12), (0.12, 0.11), (0.085, 0.10)):
        cyl(bm, CAKE + Vector((0, 0, z + h / 2)), r, h, seg=48, mi=0)
        cyl(bm, CAKE + Vector((0, 0, z + 0.018)), r + 0.003, 0.02, seg=48, mi=1)
        for k in range(14):                       # 每層頂緣的小珍珠
            a = 2 * math.pi * k / 14
            ball(bm, CAKE + Vector((math.cos(a) * r, math.sin(a) * r, z + h)), 0.009, mi=0, seg=8)
        z += h
    random.seed(4)
    for k in range(9):
        a = 2 * math.pi * k / 9
        ball(bm, CAKE + Vector((math.cos(a) * 0.05, math.sin(a) * 0.05, z + 0.02)), 0.024, mi=2, seg=10)
    for k in range(5):
        ball(bm, CAKE + Vector((random.uniform(-0.05, 0.05), random.uniform(-0.05, 0.05), z + 0.04)), 0.026, mi=2, seg=10)
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.3
        ball(bm, CAKE + Vector((math.cos(a) * 0.075, math.sin(a) * 0.075, z + 0.01)), (0.03, 0.015, 0.008), mi=3, seg=8)
    solid("S4_Cake", bm, [icing, rib, pk, lf], smooth=True)
    steel = mat("S4_Steel", (0.86, 0.87, 0.9), (0.55, 0.57, 0.62)); handle = mat("S4_Handle", (0.98, 0.97, 0.95), (0.82, 0.8, 0.82))
    bm = bmesh.new()
    box(bm, Vector((0, 0, 0.14)), (0.004, 0.036, 0.22), mi=0)             # 刀身（局部：+Z 往刀尖）
    cyl(bm, Vector((0, 0, -0.03)), 0.014, 0.12, mi=1)                      # 握把
    ball(bm, Vector((0, 0.0, 0.035)), (0.03, 0.012, 0.02), mi=2, seg=10)    # 緞帶結
    solid("S4_Knife", bm, [steel, handle, rib], smooth=False)
    s4_props(0)


def knife_M(f):
    """刀：握把中心 H，刀尖方向 d（往蛋糕下切）。0~24 舉在蛋糕上方、24~60 切下、80~100 拔起"""
    cut = seg(f, 24, 60) * (1 - seg(f, 84, 104))
    tip_hi = CAKE + Vector((-0.10, 0.05, TOP_Z + 0.16)); tip_lo = CAKE + Vector((-0.10, 0.05, TOP_Z + 0.03))
    tip = tip_hi.lerp(tip_lo, cut)
    d = Vector((0.25, -0.2, -1.0)).normalized()
    H = tip - d * 0.25
    rot = d.to_track_quat("Z", "X").to_matrix().to_4x4()
    return Matrix.Translation(H) @ rot


def s4_props(f):
    bpy.data.objects["S4_Knife"].matrix_world = knife_M(f)


def s4_frame(f):
    P = {}
    M = Matrix.Rotation(math.radians(S4_RZ), 4, "Z")
    K = knife_M(f)
    happy = seg(f, 60, 72)
    yeah = seg(f, 104, 120)
    P["Spine"] = [("X", 6 + 4 * seg(f, 24, 60) * (1 - seg(f, 84, 104))), ("Z", 4)]
    P["Head"] = [("X", 18 * (1 - happy) * (1 - yeah) + 2), ("Z", -22 * happy * (1 - yeah) - 10 * yeah), ("Y", -6 * yeah)]
    arms_down(P)
    rw = K @ Vector((0.0, 0.0, -0.06)); rt = K @ Vector((0, 0, 0.06))
    lw_knife = K @ Vector((0.0, -0.025, -0.005)); lt_knife = K @ Vector((0.0, -0.04, 0.09))
    # 左手放開刀，在臉旁比 YA
    lw_yeah = M @ Vector((0.13, -0.12, 1.33)); lt_yeah = M @ Vector((0.12, -0.15, 1.52))
    lw = lw_knife.lerp(lw_yeah, yeah); lt = lt_knife.lerp(lt_yeah, yeah)
    face = {"Fcl_ALL_Fun": 0.4 * (1 - happy), "Fcl_ALL_Joy": max(happy * (1 - yeah) * 0.9, 0.0), "Fcl_EYE_Close_L": yeah * 0.0,
            "Fcl_EYE_Close_R": yeah, "Fcl_MTH_Fun": 0.6 * yeah}
    return dict(P, rz=S4_RZ, ground=True, hands=(("grip", "peace", yeah), "grip"),
                ik=[("R", rw, M @ Vector((-0.45, -0.1, 0.85)), rt), ("L", lw, M @ Vector((0.45, -0.25, 0.85)), lt)], face=face)


def s4_cam(i):
    u = ease(i / S4_N)
    loc = Vector((-0.35, -3.3, 1.5)).lerp(Vector((-0.2, -2.9, 1.45)), u)
    aim(bpy.data.objects["Camera"], loc, (0.22, -0.2, 1.0), 36)


# 給 run_scene.py 用的描述（每個情境模組都要有）
SCENE = dict(id="s4", title="切婚禮蛋糕", N=S4_N, build=s4_build, frame=s4_frame, props=s4_props, cam=s4_cam,
             desc="雙手握刀慢慢切進三層蛋糕，停住看鏡頭笑，拔刀後左手放開、在臉旁比 YA。",
             outfit="costume", res=(960, 540), stills=())
