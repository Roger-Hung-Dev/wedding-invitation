# 情境 s5（新郎）：氣球牆前自拍。右手舉手機，換三個姿勢各拍一張（螢幕閃白）：比 YA 眨眼、手貼臉頰、側臉比小愛心，
# 最後放低手機看照片。西裝。
# 以 blender-scenario 範例 scene_s5.py（＝新娘專案 projects/bride/scripts/scene_s5.py 的底）為底，比照新郎 s2～s4 的做法：
# 角色座標的位置（手機路徑、臉的位置、左手三個姿勢的抓點、手肘方向）、氣球牆佈景、手機、鏡頭全部乘上 K（體型比例 BODY_S），
# 手才構得到手機、佈景和角色的比例也和新娘版一樣。
# 和範例不同的地方（preview 看圖、逐格量測後改的）：
#  - 手機舉高點：範例的位置離肩膀 0.68 m，超出新郎手臂全長 0.473 m，手伸直了手機還飄在手外面 20 cm；搬近到 0.43 m 以內。
#  - 手機殼改深藍灰（範例的淺粉白在白氣球前看不見）；快門時背面閃光燈亮、冒出面向鏡頭的星芒（鏡頭看不到朝臉的螢幕）。
#  - 比 YA：預設庫 peace 在新郎手上像「手指槍」（新郎 s4 發現的），改用本情境的 s5_vsign，掌心朝鏡頭。
#  - 手貼臉頰：範例的位置在新郎臉上變成托下巴，往上移、掌心貼左臉頰；小愛心：從領結前抬到下巴左前方、掌心朝鏡頭。
#  - 左手手勢：範例在權重 0.5 時一格切換手勢（手指會跳一下），改成四種手勢依權重混合（s5_hand）。
#  - 時間軸：姿勢之間改成同一窗口交叉淡入淡出（範例中途手會掉回腰邊）；垂手↔姿勢的淡入淡出拉長。
#  - 左手掌方向用旋轉內插、掌心轉角用定格量好的固定值（範例的作法逐格量到手掌一格甩 169 度）。
#  - 表情：拿掉 Joy（新郎臉上嘴巴張大、眼睛閉起來像打哈欠），改用 Fun 加深笑容。
#  - 鏡頭推近約 0.45 m（畫面下緣在大腿），手勢才看得清楚。
# 除錯：CAMDBG=1~7 換成近照鏡頭（見 s5_cam）；DBG=1 印出手腕目標和手臂長度；DBG_PALM=1 印出掌心轉角；
# REST_L／PEACE／CHEEK／HEART（各兩個點：手腕、指尖，新娘尺寸）、PHONE_HI、HT_*、PALM_*、TW_* 可從指令列覆寫試參數。
# exec 在 scene_lib.py 之後。對外：S5_N（格數）、s5_build()、s5_frame(f)、s5_props(f)、s5_cam(i)
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion

K = BODY_S                                    # 新郎 / 新娘 的體型比例
S5_N = 168                                    # 7 秒
SNAPS = (52, 92, 128)                         # 按快門（螢幕閃白）的格
SCALE_K = Matrix.Scale(K, 4)

# 比 YA 的手勢（只在這個情境用；和新郎 s4 的 s4_vsign 相同）：兩指往外張、拇指往掌心多收
HANDS["s5_vsign"] = dict(Thumb=tuple(globals().get("VS_THUMB", (45, 50, 40))), Index=(0, 2, 2), Middle=(0, 2, 2), Ring=(88, 95, 60), Little=(90, 95, 60),
                         spread=globals().get("VS_SPREAD", -14), spread_mid=-1.0)
# 手貼臉頰：手指併攏微彎（預設 open 五指張開，貼在臉上像抓臉）
HANDS["s5_cheek"] = dict(Thumb=(10, 10, 8), Index=(6, 10, 8), Middle=(8, 12, 8), Ring=(10, 14, 10), Little=(12, 16, 10), spread=-3)
# 小愛心：拇指和食指交叉，其他三指收起
HANDS["s5_heart"] = dict(Thumb=tuple(globals().get("HT_THUMB", (35, 10, 0))), Index=tuple(globals().get("HT_INDEX", (30, 40, 10))),
                         Middle=(85, 95, 60), Ring=(88, 95, 60), Little=(90, 95, 60), spread=globals().get("HT_SPREAD", 8))


PALM_YA = tuple(globals().get("PALM_YA", (0.1, -1.0, 0.0)))
PALM_CHEEK = tuple(globals().get("PALM_CHEEK", (-1.0, 0.3, 0.0)))
PALM_HEART = tuple(globals().get("PALM_HEART", (-0.2, -1.0, 0.0)))
# 三個定格姿勢的掌心轉角（度，繞手掌軸）：用 DBG_PALM=1 在定格格（52、92、128）量到「掌心朝 PALM_* 要轉幾度」。
# 改了左手的位置（PEACE／CHEEK／HEART）或手肘方向（LPOLE）就要重量
TW_YA, TW_CHEEK, TW_HEART = globals().get("TW_YA", 90.36), globals().get("TW_CHEEK", -0.74), globals().get("TW_HEART", 76.55)
FUN2, JOY2 = globals().get("FUN2", 0.3), globals().get("JOY2", 0.0)
FUNL, JOYL = globals().get("FUNL", 0.4), globals().get("JOYL", 0.0)


def kv(x, y, z):
    return Vector((x * K, y * K, z * K))


def _k(ob):
    """佈景以新娘尺寸建在世界原點座標系，物件整體放大 K（原點在世界原點，位置跟著等比例外移）"""
    ob.scale = (K, K, K)
    return ob


def s5_build():
    clear_props(); set_world((0.97, 0.90, 0.90), (0.56, 0.46, 0.47))   # 淡粉背景、玫瑰灰地板
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
    _k(solid("S5_Balloons", bm, cols, smooth=True))
    wall = mat("S5_Wall", (0.96, 0.90, 0.88), (0.86, 0.78, 0.78))
    bm = bmesh.new(); box(bm, Vector((0, 1.05, 1.4)), (4.5, 0.05, 2.8)); _k(solid("S5_Wall", bm, wall))
    neon = mat("S5_Neon", (1.0, 0.62, 0.75), (1.0, 0.62, 0.75)); neon.vrm_addon_extension.mtoon1.emissive_factor = (1.0, 0.55, 0.7)
    _k(text_obj("S5_Sign", "Just Married", 0.32, kv(0, 1.0, 1.95), (math.radians(90), 0, 0), neon, font="C:/Windows/Fonts/segoeprb.ttf", extrude=0.01))
    # 深藍灰手機殼：範例的淺粉白在白氣球前看不見
    body = mat("S5_Phone", (0.20, 0.23, 0.32), (0.11, 0.12, 0.18)); scr = mat("S5_Screen", (0.30, 0.34, 0.42), (0.2, 0.22, 0.3))
    bm = bmesh.new()
    box(bm, Vector((0, 0, 0)), (0.074, 0.008, 0.152), mi=0)        # 手機（局部：螢幕朝 +Y、上方 +Z；整支在 phone_M 裡放大 K）
    box(bm, Vector((0, 0.0045, 0)), (0.068, 0.001, 0.144), mi=1)
    box(bm, Vector((0.022, -0.005, 0.058)), (0.022, 0.003, 0.022), mi=0)   # 鏡頭模組
    box(bm, Vector((0.022, -0.0068, 0.040)), (0.008, 0.002, 0.008), mi=2)  # 背面閃光燈（快門時亮）
    led = mat("S5_LED", (0.40, 0.40, 0.42), (0.25, 0.25, 0.27))   # 平常深灰，快門時發白光
    solid("S5_Phone", bm, [body, scr, led])
    # 快門閃光的星芒（局部 XZ 平面、面向 -Y；每格轉向鏡頭）：螢幕朝臉、鏡頭只看得到手機背面，光靠螢幕發光看不出「閃白」。
    # 試過在手機前放點光源照臉：MToon 臉幾乎不變亮，握手機的手反而被照紅，所以改用看得到的星芒
    core = mat("S5_BurstCore", (1.0, 1.0, 1.0), (1.0, 1.0, 1.0), emit=(1.0, 1.0, 1.0))
    ray = mat("S5_BurstRay", (1.0, 0.86, 0.45), (1.0, 0.86, 0.45), emit=(1.0, 0.82, 0.4))
    bm = bmesh.new()
    ball(bm, Vector((0, 0, 0)), (0.016, 0.004, 0.016), mi=0, seg=16)
    for k in range(8):
        a = math.pi / 4 * k; ln = 0.075 if k % 2 == 0 else 0.042
        R = Matrix.Rotation(-a, 4, "Y")
        box(bm, R @ Vector((ln / 2, 0.002, 0)), (ln, 0.002, 0.007 if k % 2 == 0 else 0.005), rot=R, mi=1)
    solid("S5_Burst", bm, [core, ray])
    s5_props(0)


def phone_M(f):
    """手機在角色座標：舉起到右前上方、螢幕對著臉；最後放低到胸前看照片。
    路徑在新娘尺寸算再乘 K，最後整支手機放大 K（抓點跟著放大）"""
    up = seg(f, 8, 30) * (1 - seg(f, 140, 156))
    # 舉高點：範例的 (-0.30, -0.46, 1.62) 離肩膀 0.68 m，比新郎手臂全長 0.473 m 還遠 20 cm（手伸直、手機飄在手外面）；
    # 搬到肩膀起算 0.43 m 以內（手肘留一點彎；換姿勢時 Spine 轉動會讓肩膀移 2～3 cm）
    low = kv(-0.06, -0.30, 1.12); hi = kv(*globals().get("PHONE_HI", (-0.265, -0.24, 1.53)))
    p = low.lerp(hi, up)
    face = kv(0.0, -0.05, 1.45)
    d = (face - p).normalized()                   # 螢幕法線朝臉
    rot = d.to_track_quat("Y", "Z").to_matrix().to_4x4()
    tilt_low = Matrix.Rotation(math.radians(-35 * (1 - up)), 4, "X")
    return Matrix.Translation(p) @ rot @ tilt_low @ SCALE_K


_LPALM = {}


def _palm_angle(side, target):
    """掌心轉到 target 方向要繞手掌軸轉幾度（和 pose_lib.face_palm 同一套量法），只量不轉"""
    bpy.context.view_layer.update()
    n, axis = palm_normal(ARM, side)
    a = n - axis * n.dot(axis); b = target - axis * target.dot(axis)
    if a.length < 1e-4 or b.length < 1e-4:
        return None
    a.normalize(); b.normalize()
    return math.degrees(math.atan2(axis.dot(a.cross(b)), a.dot(b)))


def _apply_twist(side, ang):
    """和 face_palm 同一套轉法：繞手掌軸，前臂、手腕各轉一半"""
    if abs(ang) < 1e-3:
        return
    bpy.context.view_layer.update()
    n, axis = palm_normal(ARM, side)
    for bone, part in ((f"J_Bip_{side}_LowerArm", 0.5), (f"J_Bip_{side}_Hand", 0.5)):
        pb = ARM.pose.bones[bone]
        m = pb.matrix.copy(); h = m.to_translation()
        pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(ang * part), 4, axis) @ Matrix.Translation(-h) @ m
        pb.scale = (1, 1, 1); pb.location = (0, 0, 0); pb.rotation_quaternion.normalize()
        bpy.context.view_layer.update()


def s5_props(f):
    # s5_props 在 pose_frame 之後呼叫（run_scene 的 preview 與 render_scene 都是），左手掌心在這裡轉
    if _LPALM.get("f") == f:
        if globals().get("DBG_PALM") and _LPALM["tgt"] is not None:
            print(f"PALM f{f} measured={_palm_angle('L', _LPALM['tgt'])} applied={_LPALM['deg']:.2f}")
        _apply_twist("L", _LPALM["deg"])
    bpy.data.objects["S5_Phone"].matrix_world = phone_M(f)
    fl = max([max(0.0, 1 - abs(f - k) / 2.5) for k in SNAPS])
    e = 0.15 + 0.85 * fl
    bpy.data.materials["S5_Screen"].vrm_addon_extension.mtoon1.emissive_factor = (e, e, e)
    bpy.data.materials["S5_LED"].vrm_addon_extension.mtoon1.emissive_factor = (fl, fl, fl * 0.95)
    M = phone_M(f)
    B = bpy.data.objects["S5_Burst"]
    if fl < 0.02:
        B.hide_render = True; B.scale = (0.001, 0.001, 0.001)
    else:
        pos = M @ Vector((0.022, -0.02, 0.040))                     # 背面閃光燈外面一點
        cam = CAM_A.lerp(CAM_B, ease(f / S5_N))
        rot = (cam - pos).normalized().to_track_quat("-Y", "Z").to_matrix().to_4x4()
        sz = K * (0.5 + 1.1 * fl)                                  # 最大約 18 cm 寬：960×540 成片裡才看得出來
        B.hide_render = False
        B.matrix_world = Matrix.Translation(pos) @ rot @ Matrix.Scale(sz, 4)


_FK = ("Thumb", "Index", "Middle", "Ring", "Little")


def s5_hand(ws):
    """四種手勢依權重混合（權重量化到 0.05，混合結果登記成 HANDS 的一筆，hand_pose 才能快取）"""
    tot = sum(ws.values()) or 1.0
    q = {k: round(v / tot * 20) / 20 for k, v in ws.items() if v > 1e-3}
    name = "s5_mix_" + "_".join(f"{k}{v:.2f}" for k, v in sorted(q.items()))
    if name not in HANDS:
        d = {}
        for fk in _FK:
            d[fk] = tuple(sum(HANDS[k][fk][j] * w for k, w in q.items()) for j in range(3))
        d["spread"] = sum(HANDS[k].get("spread", 0) * w for k, w in q.items())
        d["spread_mid"] = sum(HANDS[k].get("spread_mid", 0) * w for k, w in q.items())
        HANDS[name] = d
    return name


def _pt(name, dflt):
    v = globals().get(name, dflt)
    return kv(*v[0]), kv(*v[1])


def s5_frame(f):
    P = {}
    Mp = phone_M(f)
    # 範例的淡出、淡入窗口錯開（64~74 淡出、70~82 淡入），中間三個權重加起來不到 1，左手會先掉回腰邊再抬上去；
    # 改成前一個淡出和下一個淡入用同一個窗口（兩者相加恆為 1），手直接從一個姿勢移到下一個
    x12 = seg(f, 66, 80); x23 = seg(f, 104, 116)
    # 垂手↔姿勢的淡入淡出比範例長（YA 淡入 14→22 格、小愛心淡出 10→20 格）：前臂從朝下翻到朝上約 150 度，
    # 範例的長度逐格量到前臂每格 17～22 度
    p1 = seg(f, 26, 48) * (1 - x12)                  # 姿勢 1：歪頭＋臉旁比 YA＋眨眼
    p2 = x12 * (1 - x23)                             # 姿勢 2：手貼臉頰
    p3 = x23 * (1 - seg(f, 134, 154))                # 姿勢 3：轉頭側臉、左手比小愛心
    look = seg(f, 146, 158)
    P["Head"] = [("Y", -12 * p1 + 10 * p2), ("Z", -8 * p1 + 6 * p2 - 18 * p3 - 6 * (1 - look) * (p1 + p2 + p3 < 0.1)), ("X", -6 * (p1 + p2) + 18 * look)]
    P["Spine"] = [("Y", -4 * p1 + 4 * p2), ("Z", -6 * p3)]
    arms_down(P)
    # 右手握手機：抓點在手機局部座標（Mp 已含 K）
    rw = Mp @ Vector((0.0, -0.012, -0.085)); rt = Mp @ Vector((0.0, -0.015, 0.03))
    # 左手四個位置（手腕、指尖；新娘尺寸，乘 K）
    rest_l = _pt("REST_L", ((0.16, -0.16, 0.9), (0.14, -0.2, 0.8)))
    peace = _pt("PEACE", ((0.10, -0.11, 1.34), (0.09, -0.13, 1.52)))
    # 手貼臉頰：範例的位置在新郎臉上變成托下巴（新郎脖子短、臉比較高），往上移、掌心貼左臉頰、手指朝上
    cheek = _pt("CHEEK", ((0.12, -0.10, 1.30), (0.08, -0.09, 1.43)))
    # 小愛心：範例的位置壓在領結前面（從鏡頭看像拳頭），抬到下巴左前方
    heart = _pt("HEART", ((0.11, -0.21, 1.33), (0.09, -0.25, 1.43)))
    w0 = max(0.0, 1 - p1 - p2 - p3)
    lw = rest_l[0] * w0 + peace[0] * p1 + cheek[0] * p2 + heart[0] * p3
    # 手掌方向（手腕→指尖）用旋轉內插：範例直接內插指尖點，垂手（朝下）↔比 YA（朝上）途中這個向量幾乎縮成零，
    # 方向在兩三格內急轉，逐格量到手掌一格轉 43 度。同一時間只有兩個權重不是 0，取這兩個做 slerp（經過朝前轉上去）
    pts = sorted(((w0, rest_l), (p1, peace), (p2, cheek), (p3, heart)), key=lambda x: -x[0])[:2]
    (wa, A), (wb, Bp) = pts
    da, db = A[1] - A[0], Bp[1] - Bp[0]
    t = wb / max(1e-6, wa + wb)
    qd = da.normalized().rotation_difference(db.normalized())
    d = Quaternion().slerp(qd, t) @ da.normalized()
    lt = lw + d * (da.length * (1 - t) + db.length * t)
    # 換姿勢途中手會掃過領結、外套翻領，途中往前拱（姿勢定住時不變）：垂放↔姿勢 6 cm、姿勢↔姿勢 3 cm
    wr = min(1.0, w0)
    arc = kv(0.0, -0.06, 0.0) * (4 * wr * (1 - wr)) + kv(0.0, -0.03, 0.0) * (4 * x12 * (1 - x12) + 4 * x23 * (1 - x23))
    lw = lw + arc; lt = lt + arc
    hand_l = s5_hand({"relax": w0, "s5_vsign": p1, "s5_cheek": p2, "s5_heart": p3})
    # 掌心方向（世界）：YA 朝鏡頭、手貼臉頰朝臉、小愛心朝鏡頭偏右；依權重混合、淡入淡出
    palm = (Vector(PALM_YA) * p1 + Vector(PALM_CHEEK) * p2 + Vector(PALM_HEART) * p3)
    # 表情：範例的 Fun 0.5＋Joy 0.6／0.8 在新郎臉上嘴巴張大、眼睛閉起來，像打哈欠；改成用 Fun 加深笑容
    face = {"Fcl_ALL_Fun": min(1.0, 0.5 + FUN2 * p2 + FUNL * look), "Fcl_EYE_Close_R": p1,
            "Fcl_ALL_Joy": JOY2 * p2 + JOYL * look, "Fcl_MTH_U": 0.5 * p3}
    lpole = kv(*globals().get("LPOLE", (0.45, -0.1, 0.9)))
    _DBG_T["R"] = rw; _DBG_T["L"] = lw
    # 掌心不用 pose_frame 的 palms（每格量「轉到目標方向要幾度」再乘權重）：
    #  - YA 淡入時要轉的角度會跨過 ±180，palms 第 38 格挑了另一圈，手掌一格甩 169 度；
    #  - 手臂抬起途中手指一度幾乎正對鏡頭，要轉的角度每格變 60～70 度，就算不翻面也一格轉 40 度。
    # 改成三個定格姿勢各量一次轉角（TW_*，DBG_PALM=1 會印出量到的值），每格轉「定格轉角 × 權重」，
    # 由 s5_props 在 pose_frame 之後轉（_apply_twist）。定格時和 palms 的結果相同，淡入淡出時均勻地轉過去
    _LPALM.clear()
    _LPALM.update(f=f, deg=TW_YA * p1 + TW_CHEEK * p2 + TW_HEART * p3,
                  tgt=palm.normalized() if palm.length > 1e-4 else None)
    return dict(P, ground=True, hands=(hand_l, "grip"),
                ik=[("R", rw, kv(-0.5, -0.1, 1.1), rt), ("L", lw, lpole, lt)], face=face)


_DBG_T = {}
CAM_A = kv(0.42, -2.85, 1.5); CAM_B = kv(0.25, -2.5, 1.48); CAM_T = kv(-0.05, 0.2, 1.32)


def _dbg_reach(i):
    """除錯（DBG=1）：印出手腕目標離實際手腕多遠、肩膀到目標多遠、手臂全長（看 IK 目標有沒有超出手臂長度）"""
    mw = ARM.matrix_world; pb = ARM.pose.bones; B = ARM.data.bones
    for s_ in "RL":
        S = mw @ pb[f"J_Bip_{s_}_UpperArm"].head; Wr = mw @ pb[f"J_Bip_{s_}_Hand"].head
        L = (B[f"J_Bip_{s_}_LowerArm"].head_local - B[f"J_Bip_{s_}_UpperArm"].head_local).length + \
            (B[f"J_Bip_{s_}_Hand"].head_local - B[f"J_Bip_{s_}_LowerArm"].head_local).length
        T = _DBG_T[s_]
        print(f"REACH f{i} {s_} shoulder={tuple(round(x, 3) for x in S)} target={tuple(round(x, 3) for x in T)} "
              f"dist={(T - S).length:.3f} arm={L:.3f} err={(Wr - T).length * 100:.1f}cm")
    print(f"REACH f{i} K={K:.4f} head={tuple(round(x, 3) for x in mw @ pb['J_Bip_C_Head'].head)}")


def s5_cam(i):
    if globals().get("DBG"):
        _dbg_reach(i)
    if globals().get("CAMDBG"):                   # 除錯用近照：1 主鏡頭方向拉近看臉和左手、2 他左前方、3 他右側看手機和右手、4 他正前方半身、5 左手特寫、6 右手特寫
        c = int(globals()["CAMDBG"])
        if c == 7:                                # 7：主鏡頭同一個位置、長焦拉近到頭和左手（觀眾實際看到的角度）
            u = ease(i / S5_N)
            loc = CAM_A.lerp(CAM_B, u)
            h = ARM.matrix_world @ ARM.pose.bones["J_Bip_C_Head"].head
            aim(bpy.data.objects["Camera"], loc, h + Vector((0.0, 0.0, -0.02)), 120); return
        if c >= 5:
            h = ARM.matrix_world @ ARM.pose.bones[f"J_Bip_{'L' if c == 5 else 'R'}_Hand"].head
            off = Vector((0.45, -3.3, 0.1)).normalized() * 0.55 if c == 5 else Vector((-0.5, -0.6, 0.2)).normalized() * 0.5
            aim(bpy.data.objects["Camera"], h + off, h + Vector((0, 0, 0.04)), 50); return
        loc, tgt, lens = {1: ((0.2, -1.6, 1.5), (0.0, 0.0, 1.38), 45), 2: ((0.95, -1.0, 1.5), (0.05, -0.1, 1.36), 45),
                          3: ((-1.25, -0.55, 1.55), (-0.12, -0.25, 1.42), 45), 4: ((0.0, -1.9, 1.3), (0.0, 0.0, 1.15), 40)}[c]
        aim(bpy.data.objects["Camera"], kv(*loc), kv(*tgt), lens); return
    u = ease(i / S5_N)
    # 比範例推近約 0.45 m（畫面下緣在大腿）：範例的距離下角色只佔畫面三分之一高，左手的手勢看不清楚
    loc = CAM_A.lerp(CAM_B, u)
    aim(bpy.data.objects["Camera"], loc, CAM_T, 36)


# 給 run_scene.py 用的描述（每個情境模組都要有）
SCENE = dict(id="s5", title="氣球牆前自拍", N=S5_N, build=s5_build, frame=s5_frame, props=s5_props, cam=s5_cam,
             desc="右手舉手機，換三個姿勢各拍一張（螢幕閃白）：比 YA 眨眼、手貼臉頰、側臉比小愛心，最後放低手機看照片。",
             outfit="costume", res=(960, 540), stills=())
