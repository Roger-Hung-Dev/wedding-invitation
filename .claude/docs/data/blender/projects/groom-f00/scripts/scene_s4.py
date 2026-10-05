# 情境 s4（新郎）：切婚禮蛋糕。雙手握刀慢慢切進三層蛋糕 → 停住看鏡頭笑 → 拔刀 → 左手放開、在臉旁比 YA。西裝。
# 以新娘專案 projects/bride/scripts/scene_s4.py 為底，比照新郎 s2、s3 的做法：
# 角色座標的位置（桌子、蛋糕、刀的路徑、抓點、手肘方向、YA 的位置）、佈景、刀、鏡頭全部乘上 K（體型比例 BODY_S），
# 手才構得到刀、佈景和角色的比例也和新娘版一樣。
# 新郎穿西裝褲、沒有蓬裙：桌巾改回範例的長度（垂 22 cm），桌腳一路接到桌面。
# 和範例不同的地方（preview 看圖後改的）：
#  - 握法：範例的手腕就在握把上、手掌順著刀軸，手指沒包住握把（特寫看是張開的手貼在刀柄上）。
#    改成握把橫過掌心（grip_targets）、拳頭包住，握把加長到 19 cm 讓兩個拳頭上下疊著握；刀身加深、握把改香檳金，遠景看得到刀。
#  - 比 YA：預設庫 peace 在新郎手上兩指交叉像「手指槍」，改用本情境的 s4_vsign；手放在臉外側不擋臉。
#  - 鏡頭：退遠、壓低看點，頭頂到鞋子、桌腳都在畫面裡。
# 除錯：CAMDBG=1~8 換成近照鏡頭（見 s4_cam）；YA_W／YA_T／YA_POLE／GC_*／GRIP_* 可從指令列覆寫試參數。
# exec 在 scene_lib.py 之後。對外：S4_N（格數）、s4_build()、s4_frame(f)、s4_props(f)、s4_cam(i)
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

K = BODY_S                                    # 新郎 / 新娘 的體型比例
S4_N = 156                                    # 6.5 秒
S4_RZ = 45                                    # 稍微轉向左前方的桌子
SCALE_K = Matrix.Scale(K, 4)
# 以下是新娘尺寸的座標；佈景物件整體放大 K（原點在世界原點，位置跟著等比例外移）
TABLE = Vector((0.55, -0.40, 0.0)); CAKE = Vector((0.42, -0.30, 0.0)); TOP_Z = 0.76
# 比 YA 的手勢（只在這個情境用）：預設庫的 peace 在新郎的手上，食指和中指往內收、指尖碰在一起，拇指翹在外面，
# 從鏡頭看像「手指槍」。這裡把兩指往外張、拇指往掌心多收一點。
HANDS["s4_vsign"] = dict(Thumb=tuple(globals().get("VS_THUMB", (45, 50, 40))), Index=(0, 2, 2), Middle=(0, 2, 2), Ring=(88, 95, 60), Little=(90, 95, 60),
                         spread=globals().get("VS_SPREAD", -14), spread_mid=-1.0)


def kv(x, y, z):
    return Vector((x * K, y * K, z * K))


def _k(ob):
    ob.scale = (K, K, K)
    return ob


def s4_build():
    clear_props(); set_world((0.96, 0.92, 0.86), (0.52, 0.45, 0.40))     # 暖米色宴會背景、深棕木地板
    cloth = mat("S4_Cloth", (0.97, 0.96, 0.95), (0.82, 0.80, 0.84))
    bm = bmesh.new()
    cyl(bm, TABLE + Vector((0, 0, TOP_Z - 0.015)), 0.32, 0.03, seg=48)
    cyl(bm, TABLE + Vector((0, 0, TOP_Z - 0.12)), 0.33, 0.22, seg=48, r2=0.322)     # 桌巾垂 22 cm（新郎沒有蓬裙，不必縮短）
    cyl(bm, TABLE + Vector((0, 0, (TOP_Z - 0.03) / 2)), 0.05, TOP_Z - 0.03, seg=16)  # 桌腳接到桌面
    cyl(bm, TABLE + Vector((0, 0, 0.01)), 0.2, 0.02, seg=32)
    _k(solid("S4_Table", bm, cloth))
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
    _k(solid("S4_Cake", bm, [icing, rib, pk, lf], smooth=True))
    # 刀身比範例深一點、握把改香檳金：範例的淺銀刀身和白握把在米白背景、白蛋糕前幾乎看不見
    steel = mat("S4_Steel", (0.72, 0.74, 0.80), (0.40, 0.42, 0.49)); handle = mat("S4_Handle", (0.92, 0.82, 0.58), (0.68, 0.57, 0.38))
    bm = bmesh.new()
    box(bm, Vector((0, 0, 0.14)), (0.004, 0.036, 0.22), mi=0)             # 刀身（局部：+Z 往刀尖）
    cyl(bm, Vector((0, 0, -0.065)), 0.014, 0.19, mi=1)                     # 握把（加長到 19 cm：雙拳上下疊著握）
    ball(bm, Vector((0, 0.0, 0.035)), (0.03, 0.012, 0.02), mi=2, seg=10)    # 緞帶結
    solid("S4_Knife", bm, [steel, handle, rib], smooth=False)
    s4_props(0)


def knife_M(f):
    """刀：握把中心 H，刀尖方向 d（往蛋糕下切）。0~24 舉在蛋糕上方、24~60 切下、84~104 拔起。
    路徑在新娘尺寸算，最後整把刀放大 K（抓點跟著放大）"""
    cut = seg(f, 24, 60) * (1 - seg(f, 84, 104))
    tip_hi = CAKE + Vector((-0.10, 0.05, TOP_Z + 0.16)); tip_lo = CAKE + Vector((-0.10, 0.05, TOP_Z + 0.03))
    tip = tip_hi.lerp(tip_lo, cut)
    d = Vector((0.25, -0.2, -1.0)).normalized()
    H = tip - d * 0.25
    rot = d.to_track_quat("Z", "X").to_matrix().to_4x4()
    return Matrix.Translation(H * K) @ rot @ SCALE_K


def s4_props(f):
    bpy.data.objects["S4_Knife"].matrix_world = knife_M(f)


# 握刀的手勢（只在這個情境用）：預設庫的 grip 彎得不夠，拳頭包不住握把
HANDS["s4_grip"] = dict(Thumb=(22, 30, 25), Index=tuple(globals().get("GC_I", (62, 70, 45))), Middle=tuple(globals().get("GC_M", (66, 72, 48))),
                        Ring=(68, 74, 50), Little=(70, 76, 50), spread=-2)
_BN = ARM.data.bones
SHOULDER = {s_: _BN[f"J_Bip_{s_}_UpperArm"].head_local.copy() for s_ in "LR"}   # 骨架空間（未轉 rz）
SPINE_H = _BN["J_Bip_C_Spine"].head_local.copy()
ARM_L = {s_: ((_BN[f"J_Bip_{s_}_LowerArm"].head_local - _BN[f"J_Bip_{s_}_UpperArm"].head_local).length,
              (_BN[f"J_Bip_{s_}_Hand"].head_local - _BN[f"J_Bip_{s_}_LowerArm"].head_local).length) for s_ in "LR"}
GRIP_C = {"R": globals().get("GC_R", -0.035), "L": globals().get("GC_L", -0.11)}   # 拳頭中心在握把上的位置（刀的局部 z，新娘尺寸）
GRIP_LEN = globals().get("GRIP_LEN", 0.065)   # 手腕到握把（沿手掌方向，新娘尺寸）
GRIP_OFF = globals().get("GRIP_OFF", 0.03)    # 手骨中心到握把中心（沿掌心法線）


def shoulder_w(M, side, spine_x):
    """肩膀的世界座標（估算）：骨架靜止位置 → 繞 Spine 先轉 X 再轉 Z 4 度（和 s4_frame 的 Spine 一樣）→ 轉 rz"""
    R = Matrix.Rotation(math.radians(4), 3, "Z") @ Matrix.Rotation(math.radians(spine_x), 3, "X")
    return M @ (SPINE_H + R @ (SHOULDER[side] - SPINE_H))


def elbow_est(S, W, pole, side):
    """照 ik_arm 的算法估手肘位置"""
    L1, L2 = ARM_L[side]
    v = W - S; d = max(1e-4, min(v.length, (L1 + L2) * 0.999)); dr = v.normalized()
    ang = math.acos(max(-1.0, min(1.0, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d))))
    pp = pole - S; pp = pp - dr * pp.dot(dr)
    pp.normalize()
    return S + dr * math.cos(ang) * L1 + pp * math.sin(ang) * L1


def grip_targets(Kn, S, pole, side):
    """握把橫過掌心、拳頭包住：手掌方向 h 垂直於刀軸 a，掌心法線 n 垂直於兩者、讓食指→小指的方向朝刀尖（拇指在握把末端那側）。
    h 取「前臂方向」在垂直刀軸平面上的投影（手腕打直）：轉掌心（palms）是繞手掌軸、以手肘為支點轉前臂，
    手掌軸和前臂不平行時手腕會被帶離目標（第一版取肩膀→握把的方向，左手腕偏了 1～2 cm）。
    手肘位置依 IK 的算法估，迭代三次。回傳手腕、指尖方向點、掌心法線"""
    a = (Kn.to_3x3() @ Vector((0, 0, 1))).normalized()
    P = Kn @ Vector((0, 0, GRIP_C[side]))
    v = P - S
    for _ in range(4):
        h = (v - a * v.dot(a)).normalized()
        n = (h.cross(a) if side == "R" else a.cross(h)).normalized()
        w = P - h * (GRIP_LEN * K) - n * (GRIP_OFF * K)
        v = w - elbow_est(S, w, pole, side)
    return w, w + h * 0.1, n


YA_POLE = tuple(globals().get("YA_POLE", (0.45, -0.25, 0.85)))   # 比 YA 時左手肘朝向


def s4_frame(f):
    P = {}
    M = Matrix.Rotation(math.radians(S4_RZ), 4, "Z")
    Kn = knife_M(f)
    happy = seg(f, 60, 72)
    yeah = seg(f, 104, 120)
    spine_x = 6 + 4 * seg(f, 24, 60) * (1 - seg(f, 84, 104))
    P["Spine"] = [("X", spine_x), ("Z", 4)]
    P["Head"] = [("X", 18 * (1 - happy) * (1 - yeah) + 2), ("Z", -22 * happy * (1 - yeah) - 10 * yeah), ("Y", -6 * yeah)]
    arms_down(P)
    # 抓點由刀的矩陣算（Kn 已含 K）：右拳握握把下段（靠刀身）、左拳疊在右拳上方
    r_pole = M @ kv(-0.45, -0.1, 0.85); l_pole_knife = M @ kv(0.45, -0.25, 0.85)
    rw, rt, rn = grip_targets(Kn, shoulder_w(M, "R", spine_x), r_pole, "R")
    lw_knife, lt_knife, ln = grip_targets(Kn, shoulder_w(M, "L", spine_x), l_pole_knife, "L")
    # 左手放開刀，在臉旁比 YA（放在臉的外側，不擋臉；掌心朝前）
    yw, yt = globals().get("YA_W", (0.19, -0.08, 1.34)), globals().get("YA_T", (0.21, -0.10, 1.54))
    lw_yeah = M @ kv(*yw); lt_yeah = M @ kv(*yt)
    lw = lw_knife.lerp(lw_yeah, yeah); lt = lt_knife.lerp(lt_yeah, yeah)
    face = {"Fcl_ALL_Fun": 0.4 * (1 - happy), "Fcl_ALL_Joy": max(happy * (1 - yeah) * 0.9, 0.0),
            "Fcl_EYE_Close_R": yeah, "Fcl_MTH_Fun": 0.6 * yeah}
    return dict(P, rz=S4_RZ, ground=True, hands=(("s4_grip", "s4_vsign", yeah), "s4_grip"),
                ik=[("R", rw, r_pole, rt), ("L", lw, l_pole_knife.lerp(M @ kv(*YA_POLE), yeah), lt)],
                palms=[("R", rn, 1.0), ("L", ln, 1 - yeah)], face=face)


def s4_cam(i):
    if globals().get("CAMDBG"):                           # 除錯用近照：1 主鏡頭方向拉近、2 他正前方（蛋糕後上方）、3 他左側，看手抓刀、手肘、YA、臉
        c = int(globals()["CAMDBG"])
        if c >= 7:                                        # 7、8：左手肘特寫（左前方、左後方），看比 YA 時皮膚有沒有戳出袖子
            e = ARM.matrix_world @ ARM.pose.bones["J_Bip_L_LowerArm"].head
            off = {7: (0.75, -0.55, 0.1), 8: (0.35, 0.8, 0.1)}[c]
            aim(bpy.data.objects["Camera"], e + Vector(off), e, 50); return
        if c >= 4:                                        # 4、5、6：握把特寫（主鏡頭方向、他正前方、他左後上方）
            h = knife_M(i).translation
            off = {4: (-0.15, -0.6, 0.15), 5: (0.45, -0.45, 0.2), 6: (0.2, 0.5, 0.35)}[c]
            aim(bpy.data.objects["Camera"], h + Vector(off), h, 50); return
        loc, tgt = {1: ((-0.15, -1.75, 1.4), (0.15, -0.15, 1.2)), 2: ((1.05, -1.05, 1.45), (0.1, -0.1, 1.2)),
                    3: ((1.2, 0.6, 1.45), (0.1, -0.1, 1.25))}[c]
        aim(bpy.data.objects["Camera"], kv(*loc), kv(*tgt), 40); return
    u = ease(i / S4_N)
    # 新郎比新娘高，範例的鏡頭會切到腳：退遠、壓低看點、焦距 34，頭頂到鞋子都在畫面裡
    loc = kv(-0.45, -3.65, 1.42).lerp(kv(-0.3, -3.25, 1.38), u)
    aim(bpy.data.objects["Camera"], loc, kv(0.25, -0.2, 0.84), 34)


# 給 run_scene.py 用的描述（每個情境模組都要有）
SCENE = dict(id="s4", title="切婚禮蛋糕", N=S4_N, build=s4_build, frame=s4_frame, props=s4_props, cam=s4_cam,
             desc="雙手握刀慢慢切進三層蛋糕，停住看鏡頭笑，拔刀後左手放開、在臉旁比 YA。",
             outfit="costume", res=(960, 540), stills=())
