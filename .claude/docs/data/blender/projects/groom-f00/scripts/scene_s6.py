# 情境 s6（新郎）：宴會廳轉圈跳舞。左右搖擺舞步 → 雙手高舉轉一圈 → 張開手快轉一圈 → 紳士鞠躬（右手按胸口、左手往外展開）。
# 花瓣飄落、鏡頭慢慢繞。西裝。
# 以 blender-scenario 範例 scene_s6.py（＝新娘專案 projects/bride/scripts/scene_s6.py 的底）為底，比照新郎 s2～s5 的做法：
# 佈景、花瓣、鏡頭乘上 K（體型比例 BODY_S），和角色的比例跟新娘版一樣。
# 和範例不同的地方：
#  - 結尾的屈膝禮（提裙）改成紳士鞠躬：上身前傾約 35 度、右手按在左胸口（IK，抓點跟著胸口骨頭走）、左手往外側斜下展開。
#  - 搖擺段的手：範例是一高一低的芭蕾手，新郎改成手肘彎、雙拳在腰前跟著重心左右擺；重心那一側的另一條腿膝蓋微彎、腳跟抬起。
#  - 轉圈時腳步交替踩（範例的裙子蓋住腳，新郎的腳看得到，腳不動整個人原地轉像站在轉盤上）。
#  - 第二圈多轉到正對鏡頭（鏡頭最後停在右前方約 18 度），鞠躬是對著鏡頭鞠。
#  - 西裝沒有裙擺，拿掉 skirt.extra_flare。
#  - 表情不用 Joy（新郎 s5 發現 Joy 在他臉上像打哈欠），用 Fun 加深笑容。
#  - 鏡頭退遠、壓低，雙手舉高到腳底都在畫面裡（範例只拍到膝蓋以上，新郎的舞步要看得到腳）。
#  - 花瓣不從角色身上（半徑 0.55 m 以內）落下，免得穿過頭和身體。
# 除錯：CAMDBG=1~4 換成近照鏡頭（見 s6_cam）。
# exec 在 scene_lib.py 之後。對外：S6_N（格數）、s6_build()、s6_frame(f)、s6_props(f)、s6_cam(i)
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion

K = BODY_S                                    # 新郎 / 新娘 的體型比例
S6_N = 192                                    # 8 秒
PETALS = []
END_YAW = 18.0                                # 第二圈轉完多轉幾度，正對結尾的鏡頭
HIP_Z = ARM.data.bones["J_Bip_C_Hips"].head_local.z


def kv(x, y, z):
    return Vector((x * K, y * K, z * K))


def _k(ob):
    """佈景以新娘尺寸建在世界原點座標系，物件整體放大 K（原點在世界原點，位置跟著等比例外移）"""
    ob.scale = (K, K, K)
    return ob


def s6_build():
    clear_props(); set_world((0.42, 0.29, 0.32), False)          # 宴會廳：深玫瑰色、不顯示棚內地板（自己鋪木地板）
    floor = mat("S6_Floor", (0.62, 0.46, 0.38), (0.46, 0.32, 0.28))
    bm = bmesh.new(); cyl(bm, Vector((0, 0, 0.004)), 4.0, 0.008, seg=96); _k(solid("S6_Floor", bm, floor))
    inlay = mat("S6_Inlay", (0.86, 0.74, 0.58), (0.7, 0.58, 0.45))
    bm = bmesh.new()
    for r in (1.2, 1.28, 2.2):
        for k in range(96):
            a = 2 * math.pi * k / 96
            box(bm, Vector((math.cos(a) * r, math.sin(a) * r, 0.009)), (0.07, 0.025, 0.002), Matrix.Rotation(a + math.pi / 2, 4, "Z"))
    _k(solid("S6_Inlay", bm, inlay))
    gold = mat("S6_Gold", (0.95, 0.80, 0.50), (0.75, 0.58, 0.34)); glow = mat("S6_Glow", (1.0, 0.95, 0.85), (1, 0.95, 0.85))
    glow.vrm_addon_extension.mtoon1.emissive_factor = (1.0, 0.92, 0.75)
    bm = bmesh.new()
    for c in LAMPS:                                               # 左右兩盞立燈
        cyl(bm, Vector((c[0], c[1], 0.8)), 0.03, 1.6, mi=0); cyl(bm, Vector((c[0], c[1], 0.02)), 0.18, 0.04, mi=0)
        ball(bm, Vector((c[0], c[1], 1.7)), 0.16, mi=1, seg=16)
    _k(solid("S6_Lamps", bm, [gold, glow], smooth=True))
    pet = mat("S6_Petal", (0.98, 0.72, 0.76), (0.88, 0.56, 0.62))
    random.seed(21); PETALS.clear()
    bm = bmesh.new()
    while len(PETALS) < 70:
        x, y = random.uniform(-1.8, 1.8), random.uniform(-1.6, 1.6)
        ph, sp, rot = random.uniform(0, 1), random.uniform(0.25, 0.45), random.uniform(0, 6.28)
        if math.hypot(x, y) < 0.55:                               # 不從角色身上落下（飄動幅度 ±0.15）
            continue
        box(bm, Vector((0, 0, 0)), (0.022, 0.016, 0.002))
        PETALS.append((x, y, ph, sp, rot))
    _k(solid("S6_Petals", bm, pet))
    s6_props(0)


# 立燈位置（新娘尺寸）。範例正後方那盞 (0, 2.6) 在鏡頭繞圈時會從頭頂、肩膀長出來；鏡頭繞 ±20° 時角色背後整片都會掃到，
# 兩側又會和這兩盞疊在一起（算過），所以拿掉，只留左右兩盞
LAMPS = ((-1.7, 1.6), (1.8, 1.5))


def s6_props(f):
    ob = bpy.data.objects["S6_Petals"]; me = ob.data
    base = [Vector(v) for v in ((-0.011, -0.008, -0.001), (-0.011, -0.008, 0.001), (-0.011, 0.008, -0.001), (-0.011, 0.008, 0.001),
                                (0.011, -0.008, -0.001), (0.011, -0.008, 0.001), (0.011, 0.008, -0.001), (0.011, 0.008, 0.001))]
    t = f / 24.0
    for k, (x, y, ph, sp, rot) in enumerate(PETALS):
        z = 2.6 - ((ph * 2.6 + sp * t) % 2.6)
        sx = x + 0.15 * math.sin(t * 1.3 + rot); sy = y + 0.12 * math.cos(t * 1.1 + rot)
        R = Matrix.Rotation(t * 2 + rot, 3, "X") @ Matrix.Rotation(t * 1.4 + rot, 3, "Z")
        for i in range(8):
            me.vertices[k * 8 + i].co = Vector((sx, sy, z)) + R @ base[i]
    me.update()


# ── 時間軸（格）──
#   0~18 站著微笑 → 18~72 左右搖擺 → 70~113 雙手高舉轉第一圈 → 117~151 張開手快轉第二圈（多轉 END_YAW 正對鏡頭）
#   → 146~162 右手從張開直接移到胸口、156~168 鞠躬下去、168~176 停住、176~186 起身 → 186~192 手按心口對鏡頭笑
def s6_rz(f):
    return 360 * seg(f, 70, 113) + (360 + END_YAW) * seg(f, 117, 151)


def _sway(f):
    return math.sin(2 * math.pi * (f - 24) / 48) * seg(f, 18, 30) * (1 - seg(f, 66, 74))


def _bow(f):
    """上身前傾的權重"""
    return seg(f, 156, 168) * (1 - seg(f, 176, 186))


def _hand_on(f):
    """右手按胸口的權重：比上身早一點到，起身後留在胸口到最後（結尾停在「手按心口、對鏡頭笑」）"""
    return seg(f, 146, 162)


# 貼胸口的手掌：手指併攏、微彎（放鬆 3 成＋伸直 7 成）
HANDS["s6_palm"] = dict(Thumb=(2.4, 3.6, 3.0), Index=(2.4, 4.2, 3.0), Middle=(3.6, 5.4, 3.6), Ring=(4.8, 6.6, 4.2), Little=(6.0, 7.8, 4.8), spread=-0.6)


# ── 右手按胸口：IK 目標跟著胸口骨頭走 ──
# 座標是新郎 rest 姿勢（面向 -Y）量的：背心/外套正面在胸口高度約 y = -0.15（射線量）。手腕放在中線偏右、手掌往左上斜貼在左胸，
# 掌面離外套約 8 mm（掃參數量的；手腕再往前 1.5 cm 就變成手浮在胸前 3 cm）。
# 手肘方向：往外側垂下（範例式）時前臂斜斜穿過外套右前襟（前臂和外套身體重疊 221 個三角形）；改成往前、略低於腋下
# （「手按心口」的姿勢），前臂就在外套前面，只剩袖子貼著前襟（45 個，衣服互貼）。
# 彎腰後胸口位置要等擺好身體、貼地之後才知道，所以用 _Lazy：ik_arm 讀座標（Vector(...)）那一刻才換算。
CHEST_BONE = "J_Bip_C_UpperChest"
R_WRIST = Vector(globals().get("R_WRIST", (-0.04, -0.185, 1.20)))
R_TIP = Vector(globals().get("R_TIP", (0.07, -0.19, 1.24)))
R_POLE = Vector(globals().get("R_POLE", (-0.30, -0.45, 1.10)))
R_TWIST = globals().get("R_TWIST", 0.0)
R_ROLL = globals().get("R_ROLL", 0.0)          # 掌心朝胸口之後再多轉幾度（微調用）
BULGE = 0.10 * K                              # 手從身側移到胸口的路上往前拱，免得穿過外套


class _Lazy:
    """延後算的世界座標：ik_arm 在擺好身體、貼地之後才用 Vector() 讀它，那時才呼叫 fn 算"""
    def __init__(self, fn):
        self.fn = fn

    def __iter__(self):
        return iter(self.fn())

    def __len__(self):
        return 3


def _chest_M():
    """胸口骨頭從 rest 到這一格的變換（世界座標）：rest 姿勢的點 → 這一格的點"""
    pb = ARM.pose.bones[CHEST_BONE]; b = ARM.data.bones[CHEST_BONE]
    return ARM.matrix_world @ pb.matrix @ b.matrix_local.inverted()


def _cur(bone, end="head"):
    pb = ARM.pose.bones[bone]
    return ARM.matrix_world @ (pb.head if end == "head" else pb.tail)


def _r_hand_ik(w):
    """權重 w=0 時目標＝這一格 FK 的手腕/手肘/手掌（IK 不改任何東西），w=1 時按在胸口；中間往前拱"""
    def wrist():
        M = _chest_M()
        return _cur("J_Bip_R_Hand").lerp(M @ R_WRIST, w) + M.to_3x3() @ Vector((0, -BULGE, 0)) * math.sin(math.pi * w)

    def pole():
        # 手肘方向用「從肩膀看出去的方向」轉過去：直接內插點的話，R_POLE 比手肘遠得多，權重一點點手肘就甩 27 度（量過）
        S = _cur("J_Bip_R_UpperArm")
        d0 = (_cur("J_Bip_R_LowerArm") - S).normalized(); d1 = (_chest_M() @ R_POLE - S).normalized()
        return S + (Quaternion().slerp(d0.rotation_difference(d1), w) @ d0) * 0.3

    def tip():                                # ik_arm 最後才讀（上臂、前臂已對好）：手掌方向從現在的方向轉到按胸口的方向
        _roll_forearm(w)
        # 不能直接內插「點」：手掌只有 6 cm 長，目標點從垂手的指尖往胸口移，權重一點點就讓手掌一格甩 50 度（量過）
        M = _chest_M(); h = _cur("J_Bip_R_Hand")
        d0 = (_cur("J_Bip_R_Hand", "tail") - h).normalized(); d1 = (M @ R_TIP - M @ R_WRIST).normalized()
        return h + (Quaternion().slerp(d0.rotation_difference(d1), w) @ d0) * 0.1
    return ("R", _Lazy(wrist), _Lazy(pole), _Lazy(tip))


def _roll_forearm(w):
    """手掌對準手掌方向（tip）之前，先把右前臂繞自己的軸轉到掌心朝胸口。
    不轉的話，掌心朝下的手要往內折 40 度去貼胸口，變成手腕側彎、手掌插進袖口（量到手和右袖重疊 98 個三角形）；
    掌心先朝胸口，接下來對準 tip 的那一下就是「手腕往掌心彎」。繞前臂自己的軸轉，手腕位置不變"""
    bpy.context.view_layer.update()
    la = ARM.pose.bones["J_Bip_R_LowerArm"]
    axis = la.matrix.to_3x3().col[1].normalized()
    n, _ = palm_normal(ARM, "R")
    pc = ARM.pose.bones[CHEST_BONE]; bc = ARM.data.bones[CHEST_BONE]
    want = (pc.matrix @ bc.matrix_local.inverted()).to_3x3() @ Vector((0, 1, 0))   # 胸口的「往身體裡」方向（骨架空間）
    a = n - axis * n.dot(axis); b = want - axis * want.dot(axis)
    if a.length < 1e-4 or b.length < 1e-4:
        return
    a.normalize(); b.normalize()
    ang = math.atan2(axis.dot(a.cross(b)), a.dot(b)) + math.radians(R_ROLL)
    if globals().get("DBG_ROLL"):
        print(f"ROLL w={w:.2f} ang={math.degrees(ang):.1f}")
    m = la.matrix.copy(); h = m.to_translation()
    la.matrix = Matrix.Translation(h) @ Matrix.Rotation(ang * w, 4, axis) @ Matrix.Translation(-h) @ m
    la.scale = (1, 1, 1); la.location = (0, 0, 0)
    bpy.context.view_layer.update()


# ── 手臂關鍵姿勢（arm_pose 的 5 個角度：上臂垂下 Y、往前 X、往內 Z、前臂往前彎 X、往內 Z；右手自動鏡像）──
GROOVE = tuple(globals().get("GROOVE", (70, 12, 0, 70, 15)))   # 搖擺：手肘彎、雙拳在腰前
UP = (-60, 5, 10, 30, 0)                      # 第一圈：雙手高舉（範例原值）
OUT = (15, 10, 0, 15, 0)                      # 第二圈：往兩側張開（範例原值）
BOW_SP = globals().get("BOW_SP", 28)       # 鞠躬時腰往前彎幾度（胸口再加 10）
FLOURISH = tuple(globals().get("FLOURISH", (38, -12, 0, 12, 0)))   # 鞠躬時左手往外側斜下展開
# 範例是「基本姿勢 → 舉高 → 回基本姿勢 → 張開」，新郎的基本姿勢是手肘彎的搖擺手，兩圈之間手會先收回腰前；
# 改成關鍵格內插，舉高直接放到兩側張開
S6_ARM_KEYS = [(0, DOWN), (18, DOWN), (30, GROOVE), (66, GROOVE), (84, UP), (106, UP), (122, OUT), (146, OUT), (156, DOWN)]
L_KEYS = S6_ARM_KEYS + [(168, FLOURISH), (176, FLOURISH), (186, DOWN)]
R_KEYS = S6_ARM_KEYS                             # 鞠躬時右手 FK 垂著，IK 把它帶到胸口
SWING = globals().get("SWING", 12)
FIST_KEYS = [(0, [0.0]), (18, [0.0]), (30, [0.7]), (58, [0.7]), (66, [0.0])]   # 搖擺時鬆鬆握拳（66 格前放開，接著才張開手）
OPEN_KEYS = [(0, [0.0]), (66, [0.0]), (80, [1.0]), (146, [1.0]), (150, [0.0])]   # 舉高、張開時手掌張開（150 格收回，右手接著按胸口）


def s6_frame(f):
    P = {}
    sway = _sway(f)
    spin1 = bump(f, 70, 78, 107, 113); spin2 = bump(f, 117, 124, 145, 151)
    spin = max(spin1, spin2)
    bow = _bow(f); hon = _hand_on(f)
    opn = keys_interp(OPEN_KEYS, f)[0]; fst = keys_interp(FIST_KEYS, f)[0]
    # 腿：搖擺時重心那一側站直、另一條腿膝蓋微彎腳跟抬起；轉圈時兩腳交替踩；鞠躬時髖微彎
    wl = max(0.0, -sway); wr = max(0.0, sway)
    st = math.sin(2 * math.pi * (f - 70) / 14) * spin
    wl += max(0.0, st) * 0.9; wr += max(0.0, -st) * 0.9
    legs(P, 0.02 * abs(sway) + 0.03 * spin2, extra_l=(-8 * wl + 4 * bow, 16 * wl, -8 * wl - 4 * bow),
         extra_r=(-8 * wr + 4 * bow, 16 * wr, -8 * wr - 4 * bow))
    P["Hips"] = [("Y", 6 * sway)]
    for sd in ("L", "R"):                                        # 骨盆側傾時腳掌跟著斜，轉回來讓鞋底平貼
        P[f"{sd}_Foot"].append(("Y", -6 * sway))
    P["Spine"] = [("Y", -7 * sway), ("X", BOW_SP * bow)]
    P["Chest"] = [("X", 10 * bow)]
    P["Head"] = [("Y", 6 * sway), ("X", -6 * spin1 + 10 * bow)]
    la = list(keys_interp(L_KEYS, f)); ra = list(keys_interp(R_KEYS, f))
    la[4] -= SWING * sway; ra[4] += SWING * sway                 # 搖擺：雙拳跟著重心左右擺
    arm_pose(P, "L", la); arm_pose(P, "R", ra)
    ik = [_r_hand_ik(hon)] if hon > 1e-3 else []
    tw = [("R", R_TWIST * hon)] if R_TWIST and hon > 1e-3 else []
    if fst > 1e-3:
        gl = gr = ("relax", "fist", round(fst, 2))
    else:
        gl = ("relax", "open", round(max(opn, bow), 2))
        # 右手從張開（146 格 opn=1）直接收成貼胸口的手掌，不經過放鬆手（兩種手勢內插只能兩兩接，這樣才不會跳）
        gr = ("relax", "open", round(opn, 2)) if hon < 1e-3 else ("open", "s6_palm", round(hon, 2))
    face = {"Fcl_ALL_Fun": 0.55 + 0.35 * max(opn, seg(f, 180, 188)), "Fcl_EYE_Close": 0.55 * bow}
    # root x：骨盆側傾 6° 時兩腳會往反方向擺 HIP_Z·sin6°（約 10 cm），整個人往同方向平移抵掉，踩地的腳才不會滑
    # （範例的 0.10*sway 就是這個值）。預設庫鞠躬的 root y 往後 3.5 cm 會讓腳往後滑，這裡不用
    return dict(P, rz=s6_rz(f), root=(HIP_Z * math.sin(math.radians(6 * sway)), 0, 0), ground=True,
                hands=(gl, gr), ik=ik, twist=tw, face=face)


def s6_cam(i):
    if globals().get("CAMDBG"):                   # 除錯用近照：1 正前方上半身、2 右前方、3 左側、4 主鏡頭方向拉近；5~7 右手特寫（左前方、正上方、左側）
        c = int(globals()["CAMDBG"])
        if c >= 5:
            h = ARM.matrix_world @ ARM.pose.bones["J_Bip_R_Hand"].tail
            off = {5: Vector((0.25, -0.45, 0.05)), 6: Vector((0.05, -0.25, 0.45)), 7: Vector((0.5, -0.05, 0.0))}[c]
            aim(bpy.data.objects["Camera"], h + off, h, 50); return
        h = ARM.matrix_world @ ARM.pose.bones["J_Bip_C_Chest"].head
        off = {1: Vector((0.0, -1.3, 0.15)), 2: Vector((-0.8, -1.0, 0.2)), 3: Vector((1.2, -0.2, 0.15)), 4: None}[c]
        if off is None:
            a = math.radians(-20 + 40 * ease(i / S6_N))
            off = Vector((math.sin(a), -math.cos(a), 0.1)).normalized() * 1.6
        aim(bpy.data.objects["Camera"], h + off, h, 45); return
    # 鏡頭繞圈 -20° → +20°（範例 -18° → +18°）；退遠、壓低，雙手舉高到腳底都在畫面裡
    a = math.radians(-20 + 40 * ease(i / S6_N))
    r = 3.9 * K
    aim(bpy.data.objects["Camera"], (math.sin(a) * r, -math.cos(a) * r, 1.15 * K), (0, 0, 0.92 * K), 38)


# 給 run_scene.py 用的描述（每個情境模組都要有）
SCENE = dict(id="s6", title="宴會廳轉圈", N=S6_N, build=s6_build, frame=s6_frame, props=s6_props, cam=s6_cam,
             desc="左右搖擺的舞步，雙手高舉轉一圈、再張開手快轉一圈，最後右手按胸口、左手展開，對鏡頭紳士鞠躬。花瓣飄落、鏡頭慢慢繞。",
             outfit="costume", res=(960, 540), stills=())
