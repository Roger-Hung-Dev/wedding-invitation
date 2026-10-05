# 情境 s3（新郎）：花園拱門拋捧花。捧花微笑 → 轉身背對 → 數拍子 → 往後上方拋出（捧花轉著飛向鏡頭）→ 轉回來跳起來歡呼。西裝。
# 以新娘專案 projects/bride/scripts/scene_s3.py 為底（含蓄力時捧花只往下 7 cm、上甩弧線往前拱的修正），
# 比照新郎 s2 的做法：角色座標的位置（捧花路徑、抓點、手肘方向、蹲低與跳躍高度）、花園佈景、捧花、鏡頭全部乘上 K（體型比例 BODY_S），
# 手才構得到捧花、佈景和角色的比例也和新娘版一樣。
# exec 在 scene_lib.py 之後。對外：S3_N（格數）、s3_build()、s3_frame(f)、s3_props(f)、s3_cam(i)
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

K = BODY_S                                    # 新郎 / 新娘 的體型比例
S3_N = 168                                    # 7 秒
REL = 100                                     # 放手的那一格
G = 9.8
SCALE_K = Matrix.Scale(K, 4)


def kv(x, y, z):
    return Vector((x * K, y * K, z * K))


def _k(ob):
    """佈景以新娘尺寸建在世界原點座標系，物件整體放大 K（原點在世界原點，位置跟著等比例外移）"""
    ob.scale = (K, K, K)
    return ob


def s3_build():
    clear_props(); set_world((0.78, 0.88, 0.96), False)          # 花園：天空藍、不顯示棚內地板（自己鋪草地）
    grass = mat("S3_Grass", (0.58, 0.74, 0.47), (0.42, 0.58, 0.38))
    bm = bmesh.new(); cyl(bm, Vector((0, 0, 0.003)), 6.0, 0.006, seg=64); _k(solid("S3_Grass", bm, grass))
    stone = mat("S3_Path", (0.86, 0.82, 0.76), (0.7, 0.66, 0.62))
    bm = bmesh.new(); box(bm, Vector((0, -0.6, 0.008)), (1.1, 5.0, 0.01)); _k(solid("S3_Path", bm, stone))
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
    _k(solid("S3_Arch", bm, white))
    bm = bmesh.new()
    for k in range(140):                       # 花沿著拱門
        t = random.random()
        if t < 0.55:
            a = math.pi * random.random(); c = Vector((math.cos(a) * 0.95, 1.2, 2.1 + math.sin(a) * 0.55))
        else:
            sx = random.choice((-1, 1)); c = Vector((sx * 0.95, 1.2, 0.2 + 1.9 * random.random() ** 0.6))
        c += Vector((random.uniform(-0.08, 0.08), random.uniform(-0.08, 0.08), random.uniform(-0.06, 0.06)))
        ball(bm, c, 0.045 + 0.03 * random.random(), mi=random.choice((1, 1, 2, 3, 4, 4)), seg=10)
    _k(solid("S3_ArchFlowers", bm, [white, pk, wh, pe, lf], smooth=True))
    bush = mat("S3_Bush", (0.38, 0.56, 0.33), (0.25, 0.4, 0.26))
    bm = bmesh.new()
    for c in ((-2.0, 1.6, 0.35), (2.1, 1.4, 0.4), (-2.6, 0.2, 0.3), (2.7, -0.2, 0.35), (-1.5, 2.6, 0.5), (1.6, 2.7, 0.55)):
        for _ in range(5):
            ball(bm, Vector(c) + Vector((random.uniform(-0.3, 0.3), random.uniform(-0.2, 0.2), random.uniform(-0.1, 0.15))), 0.3 + 0.12 * random.random(), seg=12)
    _k(solid("S3_Bushes", bm, bush, smooth=True))
    # 捧花（局部座標：花梗沿 +Z，原點在握把中間；新娘尺寸，bq_world 裡整束放大 K，抓點跟著放大）
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


def _count(f):
    """數拍子：60~86 格三下（每下 8.5 格）"""
    return (f > 60) * (f < 86) * (0.5 - 0.5 * math.cos(2 * math.pi * (f - 60) / 8.5))


def _wind(f):
    return seg(f, 84, 92) * (1 - seg(f, 92, 100))


def body_drop(f):
    """骨盆下降量（新娘尺寸，公尺）：數拍子屈膝、轉身、蓄力微蹲、起跳前下蹲"""
    turning = math.sin(math.pi * seg(f, 30, 58)) + math.sin(math.pi * seg(f, 112, 140))
    return (0.05 * _count(f) + 0.03 * turning + 0.06 * seg(f, 140, 144) * (1 - seg(f, 144, 146)) + 0.05 * _wind(f))


def bq_local(f):
    """捧花握把在角色座標（面向 -Y，新娘尺寸）的位置、往後仰角。拋的時候往後上方甩"""
    chest = Vector((0.0, -0.24, 1.0))
    wind = _wind(f)
    throw = seg(f, 90, 100)
    # 新娘版的修正：蓄力時只往下 7 cm、往外 2 cm（再配合 s3_frame 的微蹲＋上身前傾），手構得到
    p = chest + Vector((0, -0.02, -0.07)) * wind
    # 數拍子時捧花跟著身體一起上下（新娘版捧花停在原地、只有身體蹲，看起來像手在抽動）；蓄力的微蹲已含在上面的 -7 cm
    p = p + Vector((0, 0, -(body_drop(f) - 0.05 * wind))) * (1 - throw)
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
        return char_M(f) @ Matrix.Translation(p * K) @ Matrix.Rotation(math.radians(tilt), 4, "X") @ SCALE_K
    p0, tilt0 = bq_local(REL)
    M0 = char_M(REL)
    # 往他背後（＝鏡頭那邊）、往上拋。範例 (0, 2.4, 3.2) 在新郎的鏡頭裡最高點會被畫面上緣切掉（第 108～112 格）；
    # 改成飛低一點、更往鏡頭衝（最高點約在畫面 89% 高度，第 120 格前後從畫面左下飛出）
    v = M0.to_3x3() @ Vector((0, 3.0, 2.6))
    dt = (f - REL) / 24.0
    pos = M0 @ (p0 * K) + (v * dt + Vector((0, 0, -0.5 * G * dt * dt))) * K
    spin = Matrix.Rotation(dt * 9.0, 4, "X")
    return Matrix.Translation(pos) @ (M0.to_3x3().to_4x4() @ Matrix.Rotation(math.radians(tilt0), 4, "X")) @ spin @ SCALE_K


def s3_props(f):
    bpy.data.objects["S3_Bouquet"].matrix_world = bq_world(f)


# 放手後雙手放低的位置（新娘尺寸、左手；右手鏡像）。新娘版是張開的手放在腰前、指尖朝上，新郎做起來像「投降」；
# 改成雙手握拳收在胸口下方兩側、前臂直立、手肘朝下（「Yes!」的興奮姿勢），等轉回正面再舉起來歡呼
LOW = globals().get("LOW", (0.20, -0.13, 1.00))
LOW_POLE = (0.42, 0.02, 0.70)                     # 握拳時手肘朝向：外側、略往後、偏低
UP_POLE = (0.5, 0.1, 1.0)                         # 舉手時手肘朝向（範例原值）


def s3_frame(f):
    P = {}
    rz = s3_rz(f)
    count = _count(f)
    wind = _wind(f)
    jump_u = max(0.0, min(1.0, (f - 144) / 12.0)); air = 4 * jump_u * (1 - jump_u)
    legs(P, body_drop(f) * K)
    P["Spine"] = [("X", 3 * count + 8 * wind - 6 * seg(f, 92, 100) * (1 - seg(f, 106, 116)))]
    P["Head"] = [("X", 4 * count - 12 * seg(f, 94, 102) * (1 - seg(f, 108, 118))), ("Y", 5 * s(f / 40))]
    arms_down(P)
    M = char_M(f)
    # 握捧花：抓點在捧花局部座標（bq_world 已含 K）；放手後停在放手那一格的位置
    Mb = bq_world(min(f, REL))
    g_lw = Mb @ Vector((0.03, -0.035, -0.02)); g_rw = Mb @ Vector((-0.03, -0.035, -0.02))
    g_lt = Mb @ Vector((-0.01, -0.03, 0.04)); g_rt = Mb @ Vector((0.01, -0.03, 0.04))
    if f <= REL:
        ik = [("L", g_lw, M @ kv(0.4, -0.1, 0.8), g_lt), ("R", g_rw, M @ kv(-0.4, -0.1, 0.8), g_rt)]
        hands = ("grip", "grip")
    else:
        # 放手後：雙手往上張開再放下（握拳），最後跳起來歡呼
        up = 1 - seg(f, 106, 124); cheer = seg(f, 140, 148)
        k = max(up, cheer)
        lw = M @ kv(0.22, -0.02 + 0.03 * up, 1.25 + 0.5 * k); rw = M @ kv(-0.22, -0.02 + 0.03 * up, 1.25 + 0.5 * k)
        lw2 = M @ kv(LOW[0], LOW[1], LOW[2]); rw2 = M @ kv(-LOW[0], LOW[1], LOW[2])
        lw = lw2.lerp(lw, k); rw = rw2.lerp(rw, k)
        tip = M.to_3x3() @ kv(0.0, -0.03 * (1 - k), 0.15)          # 手掌朝上（握拳時拳頭略往前）
        lt, rt = lw + tip, rw + tip
        # 範例在第 102 格從握把一格跳到張開的位置（手腕移動約 20 cm）→ 放手後 6 格內平滑分開（手肘朝向也一起過渡）
        rel = seg(f, REL, REL + 6)
        lw = g_lw.lerp(lw, rel); rw = g_rw.lerp(rw, rel); lt = g_lt.lerp(lt, rel); rt = g_rt.lerp(rt, rel)
        pole = Vector((0.4, -0.1, 0.8)).lerp(Vector(LOW_POLE).lerp(Vector(UP_POLE), k), rel)
        ik = [("L", lw, M @ kv(pole.x, pole.y, pole.z), lt),
              ("R", rw, M @ kv(-pole.x, pole.y, pole.z), rt)]
        if rel < 1:
            g = ("grip", "open", round(rel, 2))
        else:
            g = ("open", "fist", round(1 - k, 2))                  # 舉高張開、放低握拳（內插，不會一格跳換）
        hands = (g, g)
    face = {"Fcl_ALL_Fun": 0.6, "Fcl_ALL_Joy": seg(f, 136, 146), "Fcl_MTH_O": 0.5 * seg(f, 98, 104) * (1 - seg(f, 112, 120))}
    return dict(P, rz=rz, ground=True, hop=0.12 * K * air, hands=hands, ik=ik, face=face)


def s3_cam(i):
    if globals().get("CAMDBG"):                           # 除錯用近照：1 正前方、2 右前方、3 背後、4 左側，看手抓捧花、手肘、臉
        c = int(globals()["CAMDBG"])
        loc = {1: (0.0, -1.7, 1.3), 2: (1.2, -1.2, 1.35), 3: (0.0, 1.7, 1.4), 4: (-1.7, 0.0, 1.3)}[c]
        aim(bpy.data.objects["Camera"], kv(*loc), kv(0.0, 0.0, 1.15), 40); return
    u = ease(i / S3_N)
    # 新郎比新娘高，新娘版的鏡頭會切到腳：退遠、壓低看點，頭頂（含跳起來舉手）到鞋子都在畫面裡
    loc = kv(0.7, -4.6, 1.45).lerp(kv(0.4, -4.1, 1.4), u)
    aim(bpy.data.objects["Camera"], loc, kv(0.0, 0.3, 1.10), 33)


# 給 run_scene.py 用的描述（每個情境模組都要有）
SCENE = dict(id="s3", title="花園拋捧花", N=S3_N, build=s3_build, frame=s3_frame, props=s3_props, cam=s3_cam,
             desc="捧花微笑 → 轉身背對 → 數拍子 → 往後上方拋出，捧花轉著飛向鏡頭 → 轉回來跳起來歡呼。",
             outfit="costume", res=(960, 540), stills=())
