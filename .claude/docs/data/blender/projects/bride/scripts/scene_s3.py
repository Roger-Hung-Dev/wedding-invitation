# 情境 3：花園拱門拋捧花。捧花微笑 → 轉身背對 → 數拍子 → 往後上方拋出（捧花飛向鏡頭）→ 轉回來開心跳。禮服。
# 新娘專案版（第 3 版禮服）：只改蓄力／上甩的捧花路徑（bq_local）與放手後雙手放低的位置，其他照 blender-scenario 的範例。
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

S3_N = 168
REL = 100                                     # 放手的那一格
G = 9.8


def s3_build():
    clear_props(); set_world((0.78, 0.88, 0.96), False)
    grass = mat("S3_Grass", (0.58, 0.74, 0.47), (0.42, 0.58, 0.38))
    bm = bmesh.new(); cyl(bm, Vector((0, 0, 0.003)), 6.0, 0.006, seg=64); solid("S3_Grass", bm, grass)
    stone = mat("S3_Path", (0.86, 0.82, 0.76), (0.7, 0.66, 0.62))
    bm = bmesh.new(); box(bm, Vector((0, -0.6, 0.008)), (1.1, 5.0, 0.01)); solid("S3_Path", bm, stone)
    white = mat("S3_ArchWood", (0.95, 0.94, 0.92), (0.78, 0.76, 0.78))
    pk = mat("S3_FlPink", (0.97, 0.70, 0.72), (0.84, 0.52, 0.58)); wh = mat("S3_FlWhite", (0.99, 0.96, 0.93), (0.82, 0.78, 0.8))
    pe = mat("S3_FlPeach", (0.99, 0.80, 0.68), (0.86, 0.62, 0.55)); lf = mat("S3_Leaf", (0.42, 0.62, 0.36), (0.28, 0.44, 0.28))
    random.seed(11)
    bm = bmesh.new()
    for sx in (-1, 1):
        cyl(bm, Vector((sx * 0.95, 1.2, 1.05)), 0.035, 2.1, mi=0)
    for k in range(25):                        # 拱頂
        a = math.pi * k / 24
        cyl(bm, Vector((math.cos(a) * 0.95, 1.2, 2.1 + math.sin(a) * 0.55)), 0.035, 0.14, mi=0,
            rot=Matrix.Rotation(a, 4, "Y"))
    solid("S3_Arch", bm, white)
    bm = bmesh.new()
    for k in range(140):                       # 花沿著拱門
        t = random.random()
        if t < 0.55:
            a = math.pi * random.random(); c = Vector((math.cos(a) * 0.95, 1.2, 2.1 + math.sin(a) * 0.55))
        else:
            sx = random.choice((-1, 1)); c = Vector((sx * 0.95, 1.2, 0.2 + 1.9 * random.random() ** 0.6))
        c += Vector((random.uniform(-0.08, 0.08), random.uniform(-0.08, 0.08), random.uniform(-0.06, 0.06)))
        ball(bm, c, 0.045 + 0.03 * random.random(), mi=random.choice((1, 1, 2, 3, 4, 4)), seg=10)
    solid("S3_ArchFlowers", bm, [white, pk, wh, pe, lf], smooth=True)
    bush = mat("S3_Bush", (0.38, 0.56, 0.33), (0.25, 0.4, 0.26))
    bm = bmesh.new()
    for c in ((-2.0, 1.6, 0.35), (2.1, 1.4, 0.4), (-2.6, 0.2, 0.3), (2.7, -0.2, 0.35), (-1.5, 2.6, 0.5), (1.6, 2.7, 0.55)):
        for _ in range(5):
            ball(bm, Vector(c) + Vector((random.uniform(-0.3, 0.3), random.uniform(-0.2, 0.2), random.uniform(-0.1, 0.15))), 0.3 + 0.12 * random.random(), seg=12)
    solid("S3_Bushes", bm, bush, smooth=True)
    # 捧花（局部座標：花梗沿 +Z，原點在握把中間）
    rib = mat("S3_Ribbon", (0.97, 0.78, 0.78), (0.85, 0.6, 0.64)); stem = mat("S3_Stem", (0.48, 0.62, 0.38), (0.32, 0.45, 0.3))
    bm = bmesh.new()
    cyl(bm, Vector((0, 0, 0.0)), 0.022, 0.16, mi=0)
    cyl(bm, Vector((0, 0, 0.01)), 0.026, 0.07, mi=1)
    for k in range(19):
        a = 2.4 * k; r = 0.022 * math.sqrt(k)
        ball(bm, Vector((math.cos(a) * r, math.sin(a) * r, 0.13 - r * 0.6)), 0.033, mi=2 + k % 3, seg=12)
    for k in range(8):
        a = 2 * math.pi * k / 8
        ball(bm, Vector((math.cos(a) * 0.1, math.sin(a) * 0.1, 0.09)), (0.04, 0.02, 0.012), mi=5, seg=8)
    solid("S3_Bouquet", bm, [stem, rib, pk, wh, pe, lf], smooth=True)
    s3_props(0)


def bq_local(f):
    """捧花握把在角色座標（面向 -Y）的位置、往後仰角。拋的時候往後上方甩"""
    chest = Vector((0.0, -0.24, 1.0))
    wind = seg(f, 84, 92) * (1 - seg(f, 92, 100))
    throw = seg(f, 90, 100)
    # 第 3 版禮服：原本蓄力時往下 20 cm、往身體 4 cm，捧花和雙手會插進蝴蝶結、緞帶尾和垂墜（而且超出手臂長度，手會離開捧花）；
    # 改成往下 7 cm、往外 2 cm，再配合 s3_frame 裡的微蹲＋上身前傾，手構得到
    p = chest + Vector((0, -0.02, -0.07)) * wind
    top = Vector((0.0, 0.06, 1.62))            # 手臂伸得到的最高點
    # 往上甩的途中直線會穿過胸口和臉，弧線往前拱 18 cm
    p = p.lerp(top, throw) + Vector((0, -0.18, 0)) * math.sin(math.pi * throw)
    tilt = 20 * wind - 40 * throw              # Rx 負值＝花朝後仰
    return p, tilt


def s3_rz(f):
    return 180 * seg(f, 30, 58) + 180 * seg(f, 112, 140)


def char_M(f):
    return Matrix.Rotation(math.radians(s3_rz(f)), 4, "Z")


def bq_world(f):
    if f <= REL:
        p, tilt = bq_local(f)
        return char_M(f) @ Matrix.Translation(p) @ Matrix.Rotation(math.radians(tilt), 4, "X")
    p0, tilt0 = bq_local(REL)
    M0 = char_M(REL)
    v = M0.to_3x3() @ Vector((0, 2.4, 3.2))             # 往她背後（＝鏡頭那邊）、往上拋
    dt = (f - REL) / 24.0
    pos = M0 @ p0 + v * dt + Vector((0, 0, -0.5 * G * dt * dt))
    spin = Matrix.Rotation(dt * 9.0, 4, "X")
    return Matrix.Translation(pos) @ (M0.to_3x3().to_4x4() @ Matrix.Rotation(math.radians(tilt0), 4, "X")) @ spin


def s3_props(f):
    bpy.data.objects["S3_Bouquet"].matrix_world = bq_world(f)


def s3_frame(f):
    P = {}
    rz = s3_rz(f)
    count = (f > 60) * (f < 86) * (0.5 - 0.5 * math.cos(2 * math.pi * (f - 60) / 8.5))
    turning = math.sin(math.pi * seg(f, 30, 58)) + math.sin(math.pi * seg(f, 112, 140))
    jump_u = max(0.0, min(1.0, (f - 144) / 12.0)); air = 4 * jump_u * (1 - jump_u)
    wind = seg(f, 84, 92) * (1 - seg(f, 92, 100))   # 蓄力：微蹲＋上身前傾，讓手構得到放低的捧花（第 3 版禮服修正）
    legs(P, 0.05 * count + 0.03 * turning + 0.06 * seg(f, 140, 144) * (1 - seg(f, 144, 146)) + 0.05 * wind)
    P["Spine"] = [("X", 3 * count + 8 * wind - 6 * seg(f, 92, 100) * (1 - seg(f, 106, 116)))]
    P["Head"] = [("X", -12 * seg(f, 94, 102) * (1 - seg(f, 108, 118))), ("Y", 5 * s(f / 40))]
    arms_down(P)
    M = char_M(f)
    if f <= REL + 2:
        Mb = bq_world(min(f, REL))
        lw = Mb @ Vector((0.03, -0.035, -0.02)); rw = Mb @ Vector((-0.03, -0.035, -0.02))
        lt = Mb @ Vector((-0.01, -0.03, 0.04)); rt = Mb @ Vector((0.01, -0.03, 0.04))
        ik = [("L", lw, M @ Vector((0.4, -0.1, 0.8)), lt), ("R", rw, M @ Vector((-0.4, -0.1, 0.8)), rt)]
        hands = ("grip", "grip")
    else:
        # 放手後：雙手往上張開再放下，最後跳起來歡呼
        up = 1 - seg(f, 104, 124); cheer = seg(f, 140, 148)
        k = max(up, cheer)
        lw = M @ Vector((0.22, -0.02 + 0.03 * up, 1.25 + 0.5 * k)); rw = M @ Vector((-0.22, -0.02 + 0.03 * up, 1.25 + 0.5 * k))
        # 第 3 版禮服：原本放低的位置 (±0.15,-0.12,0.88) 前臂會陷進垂墜和紗裙約 2 cm（轉回正面時看得到），往外上移到裙面外
        lw2 = M @ Vector((0.20, -0.20, 0.94)); rw2 = M @ Vector((-0.20, -0.20, 0.94))
        lw = lw2.lerp(lw, k); rw = rw2.lerp(rw, k)
        ik = [("L", lw, M @ Vector((0.5, 0.1, 1.0)), lw + M.to_3x3() @ Vector((0.0, 0, 0.15))),
              ("R", rw, M @ Vector((-0.5, 0.1, 1.0)), rw + M.to_3x3() @ Vector((0.0, 0, 0.15)))]
        hands = ("open", "open")
    face = {"Fcl_ALL_Fun": 0.6, "Fcl_ALL_Joy": seg(f, 136, 146), "Fcl_MTH_O": 0.5 * seg(f, 98, 104) * (1 - seg(f, 112, 120))}
    return dict(P, rz=rz, ground=True, hop=0.12 * air, hands=hands, ik=ik, face=face)


def s3_cam(i):
    u = ease(i / S3_N)
    loc = Vector((0.7, -4.6, 1.55)).lerp(Vector((0.4, -4.1, 1.5)), u)
    aim(bpy.data.objects["Camera"], loc, (0.0, 0.3, 1.25), 32)


# 給 run_scene.py 用的描述（每個情境模組都要有）
SCENE = dict(id="s3", title="花園拋捧花", N=S3_N, build=s3_build, frame=s3_frame, props=s3_props, cam=s3_cam,
             desc="捧花微笑 → 轉身背對 → 數拍子 → 往後上方拋出，捧花轉著飛向鏡頭 → 轉回來跳起來歡呼。",
             outfit="costume", res=(960, 540), stills=())
