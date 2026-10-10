# 30 種動作：每個函式 t∈[0,1) → 姿勢 dict（含 hands / palms / root / rz / face），頭尾相接可循環。
# exec 在 pose_lib.py 之後。角度慣例見 pose_lib.py。
import math
from mathutils import Vector

ARM = bpy.data.objects[f"{WHO}_Armature"]
# 體型比例：用頭骨高度和預設庫的新娘（1.386 m）相比。IK 目標點都是照新娘量的，換角色時乘上這個比例
BODY_S = ARM.data.bones["J_Bip_C_Head"].head_local.z / 1.386


def bs(x, y, z):
    """新娘座標 → 這個角色的座標（等比例）"""
    return Vector((x * BODY_S, y * BODY_S, z * BODY_S))

# 需要「碰到但不穿過」的姿勢參數，用 check_lib.probe 掃描後定案
TUNE = dict(clap_ux=38, clap_uz=14, clap_fx=62, clap_close=40,
            heart_up=50, heart_ux=0, heart_el=85, heart_fz=0,
            fheart_ux=40, fheart_uz=14, fheart_x=85, fheart_z=32,
            hips_up=52, hips_ux=16, hips_el=66, hips_fz=0,
            bq_ux=22, bq_uz=10, bq_x=68, bq_z=30,
            tilt_ux=-25, tilt_uz=0, tilt_x=40, tilt_z=0,
            think_ux=24, think_uz=18, think_el=132, think_z=32, think_lux=30, think_lfx=72, think_lfz=55,
            look_ux=40, look_uz=30, look_el=118, look_z=40,
            salute_y=62, salute_z=28, salute_el=112,
            kiss_ux=38, kiss_uz=22, kiss_x=128, kiss_z=35,
            shy_el=118, shy_z=30,
            # 鞠躬：男性手貼大腿外側（褲縫）的手腕位置 ±x／y／z、指尖的 x、彎到底時往下滑多少（新娘座標，跟著大腿骨走）、
            #       34° 前彎裡給骨盆（髖關節）的角度；
            # 女性雙手交疊的手腕位置（新娘座標，±x、y、z）、上面那隻手往前多少（gap）、指尖往下多少（dz）
            bowm_x=0.176, bowm_xt=0.134, bowm_y=-0.010, bowm_z=0.851, bowm_slide=0.012, bowm_hip=28,
            bowf_x=0.055, bowf_y=-0.108, bowf_z=0.935, bowf_gap=0.034, bowf_dz=0.03)
import json as _json, os as _os
# 參數依骨架比例調過：先套預設庫（新娘的值），專案自己調過的（qa/tune.json）再覆蓋
for _TF in (_os.path.join(LIB, "tune_default.json"), _os.path.join(QA, "tune.json")):
    if _os.path.exists(_TF):
        TUNE.update(_json.load(open(_TF)))


def lerp(a, b, t):
    return a + (b - a) * t


def seg(t, a, b):
    """t 在 [a,b] 之間的平滑進度 0→1"""
    return ease((t - a) / (b - a))


def bump(t, a, b, c, d):
    """a→b 上升、b→c 停住、c→d 下降的平滑包絡"""
    return seg(t, a, b) * (1 - seg(t, c, d))


def arms_down(P, l_out=0, r_out=0, l_fwd=0, r_fwd=0, l_el=18, r_el=18):
    P["L_UpperArm"] = [("Y", 72 - l_out), ("X", -l_fwd)]; P["R_UpperArm"] = [("Y", -72 + r_out), ("X", -r_fwd)]
    P["L_LowerArm"] = [("Y", 8), ("X", -l_el)]; P["R_LowerArm"] = [("Y", -8), ("X", -r_el)]
    P["L_Hand"] = [("X", -6)]; P["R_Hand"] = [("X", -6)]
    return P


def legs(P, drop, side="both", extra_l=(0, 0, 0), extra_r=(0, 0, 0)):
    th, sh, ft = leg_bend(ARM, drop)
    for s_, ex in (("L", extra_l), ("R", extra_r)):
        P[f"{s_}_UpperLeg"] = P.get(f"{s_}_UpperLeg", []) + [("X", th + ex[0])]
        P[f"{s_}_LowerLeg"] = P.get(f"{s_}_LowerLeg", []) + [("X", sh + ex[1])]
        P[f"{s_}_Foot"] = P.get(f"{s_}_Foot", []) + [("X", ft + ex[2])]
    return P


def breathe(P, t, k=1.0):
    P.setdefault("Spine", []).append(("X", 1.2 * k * s(t)))
    P.setdefault("Head", []).append(("X", 1.0 * k * s(t, 1, 0.3)))
    return P


SMILE = {"Fcl_ALL_Fun": 0.45}

# 腳底鎖定（pose_lib.plant_feet）：兩腳踩在 rest 站姿的位置不動，骨盆移動時膝蓋由腿 IK 自動彎。
# 站姿骨盆下降 3 mm（膝蓋微彎），腿 IK 才有餘裕讓骨盆左右移、骨盆側傾時不會把腿拉直到構不到
PLANT = {"L": (0, 0), "R": (0, 0)}
SOFT_KNEE = 0.003
# 鞠躬的手型依性別：project.json 的 gender（"female"／"male"）優先；沒有就看 body.bust（有胸部＝女性）
BOW_FEMALE = (MANIFEST.get("gender") or ("female" if MANIFEST.get("body", {}).get("bust") else "male")) == "female"


# 1 站姿待機（腳不動：重心在兩腳間輕輕移動、呼吸、偶爾眨眼）
def a_idle(t):
    w = s(t)                                         # 重心：+1＝偏左腳（+X）
    P = arms_down({}, l_out=1.5 * s(t), r_out=1.5 * s(t))
    breathe(P, t); P["Head"].append(("Z", 3 * s(t, 1, 0.25)))
    P["Hips"] = [("Y", -0.8 * w)]                    # 重心腳那側骨盆略高
    P["Spine"].append(("Y", 1.2 * w))                # 上身反向回正，頭維持在中間
    blink = 1.0 if 0.46 < t < 0.5 else 0.0
    return dict(P, root=(0.006 * BODY_S * w, 0, -SOFT_KNEE * BODY_S), feet=PLANT,
                face={"Fcl_ALL_Fun": 0.3, "Fcl_EYE_Close": blink})


# 2 單手揮手（前臂擺 12°～68°、上臂比前臂早一點把弧線從肩膀帶出來、每揮一下膝蓋沉一次、頭跟著歪；雙腳鎖在地上不滑）
def a_wave(t):
    w = s(t, 3)                                      # 揮動：2 秒揮 3 下（整數圈，頭尾相接）
    lead = s(t, 3, 0.12)                             # 上臂比前臂早一點，弧線從肩膀帶出來
    bob = 0.5 - 0.5 * math.cos(2 * math.pi * 3 * t)  # 膝蓋起伏 0~1
    P = arms_down({}, l_el=24)
    P["R_Shoulder"] = [("Y", 4)]                     # 肩膀微微聳起
    P["R_UpperArm"] = [("Y", 46 + 5 * lead), ("X", -14)]
    P["R_LowerArm"] = [("Y", 40 + 28 * w)]            # 12°～68°（舊版 48±20＝28°～68°）
    P["Spine"] = [("Y", -3 * w)]
    P["Head"] = [("Z", -6), ("X", -2), ("Y", 4 * s(t, 3, 0.2))]
    # 雙腳鎖在地上，骨盆往下沉＝膝蓋彎（不會滑步）
    return dict(P, hands=("relax", "open"), palms=[("R", (0, -1, 0))],
                root=(0, 0, -(SOFT_KNEE + 0.012 * bob) * BODY_S), feet=PLANT, face={"Fcl_ALL_Joy": 1.0})


# 3 雙手揮手（兩手同方向擺、前臂 ±32°、上臂與肩膀跟著帶、每揮一下膝蓋沉一次、頭跟著歪；雙腳鎖在地上不滑）
def a_wave2(t):
    w = s(t, 3); lead = s(t, 3, 0.12); bob = 0.5 - 0.5 * math.cos(2 * math.pi * 3 * t)
    # 兩手同方向擺（像雨刷）：世界軸上左右手的角度同號增減；上臂比前臂早一點（弧線從肩膀帶出來）
    P = {"L_Shoulder": [("Y", -4)], "R_Shoulder": [("Y", 4)],
         "L_UpperArm": [("Y", -46 - 7 * lead), ("X", -10)], "R_UpperArm": [("Y", 46 - 7 * lead), ("X", -10)],
         "L_LowerArm": [("Y", -(40 + 32 * w))], "R_LowerArm": [("Y", 40 - 32 * w)],
         "Spine": [("Y", 3 * w)], "Head": [("Y", -4 * s(t, 3, 0.2)), ("X", -3)]}
    return dict(P, hands=("open", "open"), palms=[("L", (0, -1, 0)), ("R", (0, -1, 0))],
                root=(0, 0, -(SOFT_KNEE + 0.012 * bob) * BODY_S), feet=PLANT, face={"Fcl_ALL_Joy": 1.0, "Fcl_MTH_A": 0.2})


# 合掌工具（拍手、跳舞共用）。合掌要掌心正對貼合，所以用 IK 直接指定手腕與手指方向；
# 拍手手勢 clap_flat：四指伸直併攏（spread +4，正值＝往中指收）、拇指往手背收 45° 再往食指靠 40°，
# 才不會像預設的 open 那樣拇指垂在掌心側、比掌根還突出約 6 mm，兩手一合拇指先撞在一起
HANDS.setdefault("clap_flat", dict(HANDS["open"], Thumb=(-45, 0, 0), thumb_in=40))
_PALM_OFF = {}


def _palm_off():
    """掌心表面到手骨軸的距離（rest 時掌心朝下：手骨頭部高度 − 手掌頂點最低點），每個角色量一次。
    VRoid 的掌根（拇指根）比四指厚約 1.5 cm，合掌時掌根先碰到"""
    if ARM.name not in _PALM_OFF:
        body = bpy.data.objects[f"{WHO}_Body"]; nm = {g.index: g.name for g in body.vertex_groups}
        zs = [(body.matrix_world @ v.co).z for v in body.data.vertices
              if v.groups and nm.get(max(v.groups, key=lambda g: g.weight).group) == "J_Bip_L_Hand"]
        _PALM_OFF[ARM.name] = ARM.data.bones["J_Bip_L_Hand"].head_local.z - min(zs)
    return _PALM_OFF[ARM.name]


def _clap_hands(center, up, ain=7.5, overlap=0.0015):
    """合掌：兩手腕在 center（rest 座標）兩側、掌心正對貼合 → {"L"/"R": (手腕, 指尖點)}。
    up＝手指方向（新娘尺寸）；兩手各往內斜 ain°（掌根和指尖同時碰到，不是只有掌根）；overlap＝互相壓進多少（m）"""
    g = _palm_off() - overlap; out = {}
    for sd, sg in (("L", 1), ("R", -1)):
        w = center + Vector((sg * g, 0, 0))
        inward = math.tan(math.radians(ain)) * Vector(up).length
        out[sd] = (w, w + bs(-sg * inward, up[1], up[2]))
    return out


# 4 拍手（IK 合掌：掌心正對整片貼合、手指朝前上方；雙手最遠張開 40～44 cm、每拍膝蓋沉一次、重心左右移、頭跟著點）
#   不用 FK 前臂往內收：手掌會順著前臂伸出去，從上方看成 V 字，只有指尖碰在一起
def a_clap(t):
    o = 0.5 + 0.5 * s(t, 4)                          # 0＝合掌、1＝張到最開
    sw = s(t, 1)
    # 重心左右移：骨盆側傾、腰椎反向轉回同樣角度 → 上身只平移不旋轉
    P = {"Head": [("Z", 6 * sw), ("X", 3 * s(t, 4, 0.25)), ("Y", 3 * s(t, 1, 0.25))],
         "Hips": [("Y", -1.0 * sw)], "Spine": [("Y", 1.0 * sw)]}
    arms_down(P); breathe(P, t)
    cl = _clap_hands(bs(0, -0.19, 1.03), (0, -0.10, 0.065))      # 胸前合掌，手指朝前上方
    ik = []
    for sd, sg in (("L", 1), ("R", -1)):
        wc, tc = cl[sd]
        wo = bs(sg * 0.175, -0.17, 1.05); to = wo + bs(sg * 0.035, -0.10, 0.065)   # 張開：手指略往外
        ik.append((sd, wc.lerp(wo, o), bs(sg * 0.42, 0.10, 0.85), tc.lerp(to, o), "Chest"))
    # 掌心轉成正對：只轉手腕（split=0），IK 對好的手腕位置才不會被甩開
    return dict(P, hands=("clap_flat", "clap_flat"), ik=ik, palms=[("L", (-1, 0, 0), 1.0, 0.0), ("R", (1, 0, 0), 1.0, 0.0)],
                root=(0.008 * BODY_S * sw, 0, -(SOFT_KNEE + 0.008 * (1 - o)) * BODY_S), feet=PLANT,
                face={"Fcl_ALL_Joy": 1.0, "Fcl_MTH_A": 0.25})


# 5 鞠躬（雙腳原地不動：從髖關節前彎、臀部自然後移，頭跟著低下，停一下再慢慢起身）
#   女性（BOW_FEMALE）：雙手交疊放在小腹前（左手在上），彎腰時手跟著腰一起前彎、留在小腹上
#   男性：雙手併指、掌心朝大腿，貼在大腿外側的褲縫上；彎腰時只沿著褲縫往下滑，不會繞到大腿前面
def a_bow(t):
    b = bump(t, 0.10, 0.36, 0.56, 0.90)               # 下去 0.26、停 0.20、起身 0.34（起身比較慢）
    hb = bump(t, 0.13, 0.38, 0.54, 0.86)              # 頭稍微晚一點低下、早一點抬起
    # 前彎角度（骨盆／腰椎／胸椎）：男性背打直、幾乎全從髖關節彎，肩膀才不會往前跑太多，手構得到大腿外側
    a_hip, a_sp, a_ch = (20, 10, 4) if BOW_FEMALE else (TUNE["bowm_hip"], 34 - TUNE["bowm_hip"] - 2, 2)
    P = {"Hips": [("X", a_hip * b)], "Spine": [("X", a_sp * b)], "Chest": [("X", a_ch * b)],
         "Neck": [("X", 3 * hb)], "Head": [("X", 9 * hb)]}
    face = {"Fcl_ALL_Fun": 0.5, "Fcl_EYE_Close": 0.6 * hb}
    root = (0, 0.045 * BODY_S * b, -(SOFT_KNEE + 0.006 * b) * BODY_S)    # 臀部往後、膝蓋微彎，重心留在腳掌上
    if BOW_FEMALE:
        arms_down(P)
        T = TUNE; x, y, z, g, dz = T["bowf_x"], T["bowf_y"], T["bowf_z"], T["bowf_gap"], T["bowf_dz"]
        # 右手在下、左手疊在上面（往前 g）：兩手幾乎水平、指尖朝對側略往下；手肘往前外開，前臂不壓到腰側。
        # 座標跟著 Spine 走（骨盆＋腰一起前彎時，手留在小腹上）
        ik = [("R", bs(-x, y, z), bs(-0.45, -0.15, 1.0), bs(-x + 0.10, y - 0.005, z - dz), "Spine"),
              ("L", bs(x, y - g, z), bs(0.45, -0.15, 1.0), bs(x - 0.10, y - g - 0.005, z - dz), "Spine")]
        hp = math.radians(30 * b)                    # 掌心朝身體（跟著骨盆＋腰的前彎一起轉）
        palm = (0, math.cos(hp), math.sin(hp))
        return dict(P, hands=("relax", "relax"), ik=ik, palms=[("R", palm), ("L", palm)], root=root, feet=PLANT, face=face)
    arms_down(P)
    T = TUNE; x, xt, y, z = T["bowm_x"], T["bowm_xt"], T["bowm_y"], T["bowm_z"] - T["bowm_slide"] * b
    # 手的 IK 目標寫成 rest 時大腿外側的點，跟著大腿骨走（骨盆後移時大腿往後斜，手也跟著留在褲縫上）。
    # 手腕略在 T 恤／外套下襬外側，指尖往下貼到大腿；手肘朝後
    ik = [(sd, bs(sg * x, y, z), bs(sg * 0.30, 0.30, 1.0), bs(sg * xt, y - 0.006, z - 0.16), f"{sd}_UpperLeg")
          for sd, sg in (("L", 1), ("R", -1))]
    # 掌心朝大腿：只轉手腕（split=0），不轉前臂，IK 對好的手腕位置才不會被甩離褲縫
    return dict(P, hands=("seam", "seam"), ik=ik, palms=[("L", (-1, 0, 0), 1.0, 0.0), ("R", (1, 0, 0), 1.0, 0.0)], root=root, feet=PLANT, face=face)


# 6 點頭
def a_nod(t):
    n = 0.5 - 0.5 * math.cos(2 * math.pi * 2 * t)
    P = arms_down({}); P["Head"] = [("X", 13 * n)]; P["Neck"] = [("X", 4 * n)]; P["Spine"] = [("X", 1.5 * n)]
    return dict(P, face={"Fcl_ALL_Fun": 0.6})


# 7 搖頭
def a_shake(t):
    P = arms_down({}); P["Head"] = [("Z", 18 * s(t, 2))]; P["Neck"] = [("Z", 5 * s(t, 2))]
    return dict(P, face={"Fcl_MTH_Small": 0.5, "Fcl_BRW_Sorrow": 0.4})


# 8 蹲下再站起
def a_squat(t):
    b = bump(t, 0.1, 0.42, 0.58, 0.9)
    h = 0.32 * b
    P = {"Spine": [("X", 22 * b)], "Chest": [("X", 6 * b)], "Head": [("X", -16 * b)]}
    arms_down(P, l_fwd=75 * b, r_fwd=75 * b, l_out=10 * b, r_out=10 * b, l_el=18 - 10 * b, r_el=18 - 10 * b)
    legs(P, h)
    P["L_UpperLeg"].insert(0, ("Z", 14 * b)); P["R_UpperLeg"].insert(0, ("Z", -14 * b))   # 膝蓋往外開，大腿才不會互穿
    return dict(P, face={"Fcl_ALL_Fun": 0.4})


# 9 原地踏步
def a_march(t):
    lu, ru = max(0, s(t, 1)), max(0, -s(t, 1))
    P = {"L_UpperLeg": [("X", -45 * lu)], "L_LowerLeg": [("X", 75 * lu)], "L_Foot": [("X", -15 * lu)],
         "R_UpperLeg": [("X", -45 * ru)], "R_LowerLeg": [("X", 75 * ru)], "R_Foot": [("X", -15 * ru)]}
    arms_down(P, l_fwd=25 * s(t, 1, 0.5), r_fwd=-25 * s(t, 1, 0.5), l_el=35, r_el=35)
    P["Spine"] = [("Y", 2 * s(t))]; P["Head"] = [("Y", -2 * s(t))]
    return dict(P, hands=("fist", "fist"), face={"Fcl_ALL_Fun": 0.6})


# 10 原地走路（跑步機式）
def a_walk(t):
    ph = 2 * math.pi * t; sn, cs = math.sin(ph), math.cos(ph)
    P = {"L_UpperLeg": [("X", -24 * sn)], "R_UpperLeg": [("X", 24 * sn)],
         "L_LowerLeg": [("X", 8 + 38 * max(0, cs))], "R_LowerLeg": [("X", 8 + 38 * max(0, -cs))],
         "L_Foot": [("X", -8 * max(0, cs) + 6 * max(0, -sn))], "R_Foot": [("X", -8 * max(0, -cs) + 6 * max(0, sn))]}
    arms_down(P, l_fwd=-18 * sn, r_fwd=18 * sn, l_el=22, r_el=22)
    P["Spine"] = [("Z", 4 * sn), ("X", 3)]; P["Hips"] = [("Z", -4 * sn)]
    return dict(P, face={"Fcl_ALL_Fun": 0.5})


# 11 轉身（轉到背面再轉回來）
def a_turn(t):
    r = 180 * seg(t, 0.08, 0.42) - 180 * seg(t, 0.58, 0.92)
    lead = 25 * (math.sin(math.pi * seg(t, 0.03, 0.42)) - math.sin(math.pi * seg(t, 0.53, 0.92)))
    P = arms_down({}); P["Head"] = [("Z", lead * 0.6)]; P["Spine"] = [("Z", lead * 0.3)]
    step = abs(math.sin(math.pi * seg(t, 0.08, 0.42))) + abs(math.sin(math.pi * seg(t, 0.58, 0.92)))
    legs(P, 0.02 * step)
    # no_stand_fix：原地轉身的腳在地上轉，男性站姿統一層（pose_lib.stand_fix）讓已超標的滑步再多 3～5%，先排除（2026-10-08）
    return dict(P, rz=r, face={"Fcl_ALL_Fun": 0.5}, no_stand_fix=True)


# 12 原地轉一圈
def a_spin(t):
    u = seg(t, 0.12, 0.88)
    sp = math.sin(math.pi * u)
    P = arms_down({}, l_out=40 * sp, r_out=40 * sp, l_el=18 + 20 * sp, r_el=18 + 20 * sp)
    P["Head"] = [("X", -6 * sp)]
    legs(P, 0.03 * sp)
    return dict(P, rz=360 * u, hop=0.015 * sp * sp, face={"Fcl_ALL_Joy": sp}, no_stand_fix=True)   # 同 a_turn，排除站姿統一層


# 13 跳躍
def a_jump(t):
    crouch = bump(t, 0.05, 0.27, 0.27, 0.38) + bump(t, 0.6, 0.7, 0.7, 0.9) * 0.8
    u = max(0.0, min(1.0, (t - 0.33) / 0.3))
    air = 4 * u * (1 - u)                    # 拋物線：起跳、落地速度最大，頂點速度 0
    h = 0.11 * crouch
    P = {"Spine": [("X", 14 * crouch - 4 * air)], "Head": [("X", -8 * crouch)]}
    arm_up = bump(t, 0.2, 0.45, 0.55, 0.85)
    P["L_UpperArm"] = [("Y", 72 - 115 * arm_up), ("X", 25 * crouch * (1 - arm_up))]
    P["R_UpperArm"] = [("Y", -72 + 115 * arm_up), ("X", 25 * crouch * (1 - arm_up))]
    P["L_LowerArm"] = [("X", -15)]; P["R_LowerArm"] = [("X", -15)]
    legs(P, h)
    for s_ in "LR":
        P[f"{s_}_Foot"].append(("X", 25 * air))       # 空中腳尖往下
        P[f"{s_}_LowerLeg"].append(("X", 15 * air))
    return dict(P, hop=0.2 * air, face={"Fcl_ALL_Joy": max(air, 0.3)})


# 14 歡呼（雙手高舉）
def a_cheer(t):
    u = 0.5 + 0.5 * s(t, 2, -0.25)
    P = {"L_UpperArm": [("Y", -58 - 12 * u)], "R_UpperArm": [("Y", 58 + 12 * u)],
         "L_LowerArm": [("Y", -12 * (1 - u))], "R_LowerArm": [("Y", 12 * (1 - u))],
         "Spine": [("X", -3)], "Head": [("X", -6)]}
    legs(P, 0.03 * (1 - u))
    return dict(P, hands=("open", "open"), palms=[("L", (0, -1, 0)), ("R", (0, -1, 0))],
                hop=0.035 * u * u, face={"Fcl_ALL_Joy": 1.0})


# 15 頭上比大愛心
def a_heart(t):
    T = TUNE
    P = {"L_UpperArm": [("Y", -T["heart_up"]), ("X", -T["heart_ux"])], "R_UpperArm": [("Y", T["heart_up"]), ("X", -T["heart_ux"])],
         "L_LowerArm": [("Y", -T["heart_el"]), ("Z", T["heart_fz"])], "R_LowerArm": [("Y", T["heart_el"]), ("Z", -T["heart_fz"])],
         "Spine": [("Y", 4 * s(t))], "Head": [("Y", 6 * s(t))]}
    return dict(P, hands=("relax", "relax"), face={"Fcl_ALL_Joy": 1.0})


# 16 胸前比小愛心
def a_fheart(t):
    T = TUNE
    P = {"L_UpperArm": [("Y", 72), ("X", -T["fheart_ux"]), ("Z", -T["fheart_uz"])], "R_UpperArm": [("Y", -72), ("X", -T["fheart_ux"]), ("Z", T["fheart_uz"])],
         "L_LowerArm": [("X", -T["fheart_x"]), ("Z", -T["fheart_z"])], "R_LowerArm": [("X", -T["fheart_x"]), ("Z", T["fheart_z"])],
         "Head": [("Y", 8 * s(t))], "Spine": [("Y", 3 * s(t))]}
    return dict(P, hands=("pinch", "pinch"), palms=[("L", (-0.6, -0.8, 0)), ("R", (0.6, -0.8, 0))], face={"Fcl_ALL_Fun": 0.8})


# 17 飛吻
def a_kiss(t):
    # IK 沿路徑走：垂手 → 嘴邊 → 往前上方送出 → 回到垂手（每段都平滑起停）
    rest = (bs(-0.19, -0.05, 0.86), bs(-0.2, -0.08, 0.72))
    mouth = (bs(-0.04, -0.185, 1.30), bs(0.0, -0.118, 1.38))
    send = (bs(-0.19, -0.34, 1.37), bs(-0.23, -0.5, 1.43))      # 留在手臂構得到的範圍內，免得伸直後手肘突然彎回
    a, b, c = seg(t, 0.04, 0.28), seg(t, 0.38, 0.58), seg(t, 0.64, 1.0)
    w = rest[0].lerp(mouth[0], a).lerp(send[0], b).lerp(rest[0], c)
    tip = rest[1].lerp(mouth[1], a).lerp(send[1], b).lerp(rest[1], c)
    k = a * (1 - b); o = b * (1 - c)
    P = arms_down({})
    P["Head"] = [("X", 6 * k - 4 * o), ("Y", 6 * o)]
    face = {"Fcl_MTH_U": 0.8 * k, "Fcl_EYE_Close": 0.9 * k, "Fcl_ALL_Joy": o}
    return dict(P, hands=("relax", ("relax", "open", o)), twist=[("R", 38 * o)],
                ik=[("R", w, bs(-0.45, 0.05, 0.9))], face=face)       # 手掌不另外對準（避免翻面），順著前臂


# 18 比 YA
def a_peace(t):
    P = arms_down({})
    P["R_UpperArm"] = [("Y", -72), ("X", -32), ("Z", 22)]
    P["R_LowerArm"] = [("X", -122), ("Z", 30)]
    P["Head"] = [("Y", -8 + 3 * s(t, 2))]; P["Spine"] = [("Y", -3)]
    legs(P, 0.012 * (0.5 + 0.5 * s(t, 2)))
    # palms 轉完掌心法線 ≈ -0.96 Y（朝鏡頭）。V 字看不出來時先查 pose_lib 的 peace 手勢 spread 正負號，不是掌心方向
    return dict(P, hands=("relax", "peace"), palms=[("R", (0, -1, 0))],
                face={"Fcl_ALL_Joy": 0.6, "Fcl_EYE_Close_R": 1.0})


# 19 指向前方
def a_point(t):
    u = 0.5 + 0.5 * s(t, 2)
    P = arms_down({})
    P["R_UpperArm"] = [("Y", -72), ("X", -80 - 6 * u)]
    P["R_LowerArm"] = [("X", -6)]
    P["Spine"] = [("X", 3), ("Z", 5)]; P["Head"] = [("Z", -3)]
    return dict(P, hands=("relax", "point"), palms=[("R", (-1, 0, 0))], face={"Fcl_ALL_Fun": 0.8})


# 20 雙手叉腰
def a_hips(t):
    T = TUNE
    # 下半身和軀幹不動（手搭在腰上，軀幹一動手就會滑開或壓進去），只有頭和脖子輕輕歪、轉，讓它不呆板
    P = {"L_UpperArm": [("Y", T["hips_up"]), ("X", T["hips_ux"])], "R_UpperArm": [("Y", -T["hips_up"]), ("X", T["hips_ux"])],
         "L_LowerArm": [("Y", T["hips_el"]), ("Z", T["hips_fz"])], "R_LowerArm": [("Y", -T["hips_el"]), ("Z", -T["hips_fz"])],
         "Neck": [("Y", 1.5 * s(t))], "Head": [("Y", 5 * s(t)), ("Z", 4 * s(t, 1, 0.25)), ("X", 1.5 * s(t, 2))]}
    blink = 1.0 if 0.70 < t < 0.74 else 0.0
    return dict(P, hands=("relax", "relax"), palms=[("L", (-1, 0, 0)), ("R", (1, 0, 0))], root=(0, 0, -SOFT_KNEE * BODY_S), feet=PLANT,
                face={"Fcl_ALL_Fun": 0.7, "Fcl_EYE_Close": blink})


# 21 伸懶腰
def a_stretch(t):
    up = bump(t, 0.03, 0.3, 0.8, 0.98)
    side = math.sin(2 * math.pi * seg(t, 0.3, 0.8)) * bump(t, 0.28, 0.4, 0.7, 0.82)
    P = {"L_UpperArm": [("Y", 72 - 150 * up)], "R_UpperArm": [("Y", -72 + 150 * up)],
         "L_LowerArm": [("Y", -10 * up), ("X", -18 * (1 - up))], "R_LowerArm": [("Y", 10 * up), ("X", -18 * (1 - up))],
         "Spine": [("X", -6 * up), ("Y", 14 * side)], "Chest": [("Y", 6 * side)], "Head": [("X", -10 * up)]}
    return dict(P, hands=("relax", "relax"), face={"Fcl_EYE_Close": up, "Fcl_MTH_O": 0.5 * up})


# 22 手遮眉遠眺
def a_lookout(t):
    look = s(t, 1)
    T = TUNE
    P = arms_down({})
    P["R_UpperArm"] = [("Y", -72), ("X", -T["look_ux"]), ("Z", T["look_uz"])]
    P["R_LowerArm"] = [("X", -T["look_el"]), ("Z", T["look_z"])]
    P["R_Hand"] = [("Y", 20)]
    P["Head"] = [("Z", 28 * look), ("X", -4)]; P["Spine"] = [("Z", 8 * look)]
    return dict(P, hands=("relax", "flat"), twist=[("R", -120)], face={"Fcl_MTH_Small": 0.3})


# 23 捧花
def a_bouquet(t):
    T = TUNE
    P = {"L_UpperArm": [("Y", 72), ("X", -T["bq_ux"]), ("Z", -T["bq_uz"])], "R_UpperArm": [("Y", -72), ("X", -T["bq_ux"]), ("Z", T["bq_uz"])],
         "L_LowerArm": [("X", -T["bq_x"]), ("Z", -T["bq_z"])], "R_LowerArm": [("X", -T["bq_x"]), ("Z", T["bq_z"])],
         "Spine": [("Y", 0.8 * s(t))], "Head": [("Y", 5 * s(t)), ("X", 3)], "Hips": [("Y", -0.8 * s(t))]}
    # 腳不動：重心在兩腳間輕輕左右移，骨盆側傾、腰椎反向轉回同樣角度 → 上身只平移不旋轉。
    # （手臂是世界軸 FK，上身一旋轉，左右手的相對姿勢就會變、手指互相壓進去；不轉就維持合握的樣子）
    return dict(P, hands=("grip", "grip"), palms=[("L", (-1, 0, 0.6)), ("R", (1, 0, 0.6))],
                root=(0.005 * BODY_S * s(t), 0, -SOFT_KNEE * BODY_S), feet=PLANT, face={"Fcl_ALL_Fun": 0.6})


# 24 害羞摀臉
def a_shy(t):
    c = bump(t, 0.05, 0.3, 0.7, 0.95)
    P = arms_down({})
    P["L_UpperArm"] = [("Y", 72), ("X", -30 * c), ("Z", -22 * c)]
    P["R_UpperArm"] = [("Y", -72), ("X", -30 * c), ("Z", 22 * c)]
    P["L_LowerArm"] = [("X", -18 - (TUNE["shy_el"] - 18) * c), ("Z", -TUNE["shy_z"] * c)]
    P["R_LowerArm"] = [("X", -18 - (TUNE["shy_el"] - 18) * c), ("Z", TUNE["shy_z"] * c)]
    P["Head"] = [("X", 10 * c), ("Z", 10 * c * s(t, 2))]; P["Spine"] = [("X", 5 * c)]
    return dict(P, hands=("relax", "relax"), twist=[("L", -84 * c), ("R", 84 * c)],
                face={"Fcl_EYE_Close": c, "Fcl_ALL_Joy": 0.5 * c})


# 25 思考（手托下巴）
def a_think(t):
    sw = s(t)
    P = {"Head": [("Y", 8 + 3 * sw), ("X", -5)], "Spine": [("Y", 2 * sw)]}
    arms_down(P)
    # 右手：手腕在胸前、食指點下巴；左手：托住右手肘
    ik = [("R", bs(-0.02, -0.20, 1.26), bs(-0.15, -0.5, 0.95), bs(0.0, -0.09, 1.365)),
          ("L", bs(-0.10, -0.19, 1.075), bs(0.3, -0.25, 0.95), bs(-0.2, -0.17, 1.085))]
    return dict(P, hands=("relax", "point"), ik=ik, face={"Fcl_MTH_Small": 0.4, "Fcl_BRW_Sorrow": 0.3})


# 26 歪頭
def a_tilt(t):
    tl = math.sin(math.pi * 2 * t)
    P = {"Head": [("Y", 16 * tl)], "Neck": [("Y", 4 * tl)], "Spine": [("Y", -3 * tl)]}
    arms_down(P)
    # 雙手背在身後：手腕在腰後 5 公分、手指朝中間
    ik = [("L", bs(0.075, 0.165, 0.935), bs(0.35, 0.25, 1.0), bs(0.005, 0.19, 0.905)),
          ("R", bs(-0.075, 0.145, 0.925), bs(-0.35, 0.25, 1.0), bs(-0.005, 0.155, 0.895))]   # 左手疊在右手外側
    return dict(P, hands=("relax", "relax"), ik=ik, face={"Fcl_ALL_Fun": 0.8})


# 27 招手（過來過來）
def a_beckon(t):
    u = 0.5 + 0.35 * s(t, 2)
    P = arms_down({})
    P["R_UpperArm"] = [("Y", -72), ("X", -45), ("Z", 8)]
    P["R_LowerArm"] = [("X", -55 - 15 * u)]
    P["Head"] = [("Y", -5)]
    return dict(P, hands=("relax", ("open", "grip", u)), twist=[("R", 91)], face={"Fcl_ALL_Fun": 0.7})


# 28 敬禮
def a_salute(t):
    u = bump(t, 0.05, 0.4, 0.68, 0.97)
    T = TUNE
    P = arms_down({})
    P["R_UpperArm"] = [("Y", -72 + T["salute_y"] * u), ("Z", T["salute_z"] * u)]
    P["R_LowerArm"] = [("Y", T["salute_el"] * u), ("X", -18 * (1 - u))]
    P["R_Hand"] = [("Y", 8 * u)]
    P["Head"] = [("X", -3 * u)]
    return dict(P, hands=("relax", ("relax", "flat", u)), twist=[("R", 148 * u)],
                face={"Fcl_ALL_Fun": 0.3 + 0.4 * u})


# 29 跳舞擺動（左右踏步 step-touch：右腳往右踏 → 左腳併過去點地 → 左腳往左踏 → 右腳併回來，一拍一步）
def _step(t, a, b, x0, x1, h):
    """一隻腳在 [a,b] 之間抬起 → 移到新位置 → 放下。回傳 (dx, 離地高度, 抬起比例 0~1)。
    水平移動只在中段（腳已離地 2 cm 以上）發生，所以腳是「抬起、放下」，不是在地上拖"""
    u = min(1.0, max(0.0, (t - a) / (b - a)))
    up = 0.5 - 0.5 * math.cos(2 * math.pi * u)        # 起落速度都是 0，膝蓋不會一格突然彎
    return x0 + (x1 - x0) * ease((u - 0.2) / 0.6), h * up, up


# 跳舞的上半身：每拍一個定格，拍與拍之間用梯形速度曲線移過去、手勢跟著換。
# 定格點對齊整數格（48 格裡的第 10／22／34／46 格，膝蓋最低點 0.22／0.47／0.72／0.97 的前一點），
# 渲染出來才有一格是合掌真正貼緊的（落在兩格之間的話，前後兩格都差 2～4 mm）
_DK = (10 / 48, 22 / 48, 34 / 48, 46 / 48)


def _trap(u, r=0.25):
    """梯形速度：前 r 加速、中段等速、後 r 減速。最高速＝平均的 1/(1-r) 倍（smoothstep 是 1.5 倍），兩端速度 0（定格）"""
    u = max(0.0, min(1.0, u)); c = 1 / (2 * r * (1 - r))
    if u < r:
        return c * u * u
    if u > 1 - r:
        return 1 - c * (1 - u) ** 2
    return (u - r / 2) / (1 - r)


def _dance_arm(name, sd, sg):
    """一隻手在某個定格的 (手腕, 手肘方向點, 指尖點, 掌心方向)，rest 座標（跟著 Chest 走）。位移以右手寫，左手 x 取負號。
    掌心：指、比 YA 朝前；合掌、胸前拳頭朝中間（兩者接近，換拍時手掌不必大翻）"""
    S = ARM.data.bones[f"J_Bip_{sd}_UpperArm"].head_local
    def off(x, y, z): return S + bs(-sg * x, y, z)
    if name == "pt":                                          # 往斜上方指（手腕在肩上 16 cm；再高的話換拍時前臂轉速會超過 15°/格）
        w = off(-0.18, -0.18, 0.16); return w, off(-0.10, 0.15, -0.30), w + (w - S).normalized() * 0.11 * BODY_S, (0, -1, 0)
    if name == "ch":                                          # 拳頭收在胸前、指節朝上
        w = off(0.0, -0.225, -0.19); return w, off(-0.25, 0.05, -0.25), w + bs(-sg * 0.02, -0.05, 0.10), (-sg, 0, 0)
    if name == "pc":                                          # 臉旁比 YA
        w = off(-0.10, -0.17, 0.07); return w, off(-0.25, 0.10, -0.20), w + bs(sg * 0.02, -0.02, 0.10), (0, -1, 0)
    w, tip = _clap_hands(bs(0.0, -0.27, 1.28), (0, -0.04, 0.11))[sd]     # 下巴前合掌
    return w, off(-0.30, 0.0, -0.20), tip, (-sg, 0, 0)


# 每拍定格：(右手, 左手, 右手勢, 左手勢, 頭 (Z 轉向, X 抬低頭, Y 歪頭))
_DANCE_KEYS = [("pt", "ch", "point", "fist", (-18, -6, -3)),        # 第 1 拍：右腳往右踏，右手往右上指、頭轉右看上去
               ("cl", "cl", "clap_flat", "clap_flat", (-3, 0, 5)),  # 第 2 拍：左腳併過來，雙手在下巴前拍一下
               ("ch", "pt", "fist", "point", (18, -6, 3)),          # 第 3 拍：左腳往左踏，左手往左上指、頭轉左
               ("pc", "pc", "peace", "peace", (0, 0, 7))]           # 第 4 拍：右腳併回來，雙手臉旁比 YA、歪頭


def a_dance(t):
    # 腳：步幅 24 cm、抬腳 5.5 cm、每拍下沉 3 cm；上半身：指 → 合掌 → 指 → 比 YA（_DANCE_KEYS）
    k = BODY_S; d = 0.24 * k; h = 0.055 * k            # 步幅、抬腳高度
    # 每隻腳的位置（相對 rest 站姿，往角色左邊為正）：一開始兩腳都在左邊（+d/2）
    if t < 0.5:
        rx, rl, ru = _step(t, 0.02, 0.21, d / 2, -d / 2, h)      # 第 1 拍：右腳往右踏
        lx, ll, lu = _step(t, 0.29, 0.48, d / 2, -d / 2, h)      # 第 2 拍：左腳併過去
    else:
        lx, ll, lu = _step(t, 0.52, 0.71, -d / 2, d / 2, h)      # 第 3 拍：左腳往左踏
        rx, rl, ru = _step(t, 0.79, 0.98, -d / 2, d / 2, h)      # 第 4 拍：右腳併回來
    w = 1 - 2 * seg(t, 0.14, 0.31) + 2 * seg(t, 0.64, 0.81)      # 重心：+1 在左腳、-1 在右腳（腳放下才開始換，換到一半另一腳才抬）
    bnc = 0.5 + 0.5 * math.cos(2 * math.pi * 4 * (t - 0.22))      # 每拍踩下時膝蓋往下沉
    # 上半身：現在在哪兩個定格之間（循環：第 4 拍 → 下一圈第 1 拍）
    tt = t if t >= _DK[0] else t + 1
    i = max(j for j in range(4) if _DK[j] <= tt)
    a, b = _DANCE_KEYS[i], _DANCE_KEYS[(i + 1) % 4]
    t0, t1 = _DK[i], _DK[(i + 1) % 4] + (1 if i == 3 else 0)
    u = _trap((tt - t0) / (t1 - t0))
    hd = [a[4][j] + (b[4][j] - a[4][j]) * u for j in range(3)]
    P = {"Hips": [("Y", -6 * w)], "Spine": [("Y", 8 * w)], "Chest": [("Y", 2.5 * w)],
         "Head": [("Z", hd[0]), ("X", hd[1] + 4 * bnc), ("Y", hd[2])]}
    arms_down(P)
    ik, palms, hands = [], [], {}
    for sd, sg, ai, gi in (("R", -1, 0, 2), ("L", 1, 1, 3)):
        ka, kb = _dance_arm(a[ai], sd, sg), _dance_arm(b[ai], sd, sg)
        ik.append((sd, ka[0].lerp(kb[0], u), ka[1].lerp(kb[1], u), ka[2].lerp(kb[2], u), "Chest"))
        hands[sd] = a[gi] if a[gi] == b[gi] else (a[gi], b[gi], round(u, 2))
        sp = (0.0 if a[ai] == "cl" else 0.5) * (1 - u) + (0.0 if b[ai] == "cl" else 0.5) * u   # 合掌時只轉手腕
        palms.append((sd, tuple(Vector(ka[3]).lerp(Vector(kb[3]), u).normalized()), 1.0, sp))
    feet = {"L": (lx, 0, ll, 12 * lu), "R": (rx, 0, rl, 12 * ru)}
    return dict(P, hands=(hands["L"], hands["R"]), ik=ik, palms=palms, root=(0.75 * d / 2 * w, 0, -(0.012 + 0.030 * bnc) * k),
                feet=feet, face={"Fcl_ALL_Joy": 1.0})


# 30 屈膝禮
def a_curtsy(t):
    b = bump(t, 0.1, 0.4, 0.6, 0.9)
    h = 0.09 * b
    P = {"Spine": [("X", 8 * b)], "Head": [("X", 10 * b), ("Y", 5 * b)]}
    P["L_UpperArm"] = [("Y", 72 - 22 * b), ("X", -10 * b)]; P["R_UpperArm"] = [("Y", -72 + 22 * b), ("X", -10 * b)]
    P["L_LowerArm"] = [("Y", 8), ("X", -18 - 8 * b)]; P["R_LowerArm"] = [("Y", -8), ("X", -18 - 8 * b)]
    legs(P, h, extra_r=(22 * b, 18 * b, 10 * b))
    return dict(P, hands=(("relax", "pinch", b), ("relax", "pinch", b)), face={"Fcl_ALL_Fun": 0.4 + 0.4 * b})


ACTIONS = [
    ("idle", "站姿待機", a_idle, 48), ("wave", "單手揮手", a_wave, 48), ("wave2", "雙手揮手", a_wave2, 48),
    ("clap", "拍手", a_clap, 48), ("bow", "鞠躬", a_bow, 72), ("nod", "點頭", a_nod, 48),
    ("shake", "搖頭", a_shake, 48), ("squat", "蹲下站起", a_squat, 72), ("march", "原地踏步", a_march, 48),
    ("walk", "原地走路", a_walk, 48), ("turn", "轉身", a_turn, 72), ("spin", "轉一圈", a_spin, 72),
    ("jump", "跳躍", a_jump, 60), ("cheer", "歡呼", a_cheer, 48), ("heart", "頭上比愛心", a_heart, 48),
    ("fheart", "胸前比心", a_fheart, 48), ("kiss", "飛吻", a_kiss, 84), ("peace", "比YA", a_peace, 48),
    ("point", "指向前方", a_point, 48), ("hips", "雙手叉腰", a_hips, 48), ("stretch", "伸懶腰", a_stretch, 96),
    ("lookout", "手遮眉遠眺", a_lookout, 72), ("bouquet", "捧花", a_bouquet, 48), ("shy", "害羞摀臉", a_shy, 72),
    ("think", "思考", a_think, 48), ("tilt", "歪頭", a_tilt, 48), ("beckon", "招手", a_beckon, 48),
    ("salute", "敬禮", a_salute, 84), ("dance", "跳舞擺動", a_dance, 48), ("curtsy", "屈膝禮", a_curtsy, 72),
]
ACT = {k: (name, fn, n) for k, name, fn, n in ACTIONS}
DEFAULT_KEYS = [k for k, *_ in ACTIONS]          # 預設庫的 30 個動作

# 擴充動作（blender-animation-append 加的）放在 actions_custom.py，載入後併進同一張表
try:
    use("actions_custom")
    for _k, _name, _fn, _n in CUSTOM_ACTIONS:
        if _k in ACT:
            raise RuntimeError(f"擴充動作代號 {_k} 和既有動作重複")
        ACTIONS.append((_k, _name, _fn, _n)); ACT[_k] = (_name, _fn, _n)
except FileNotFoundError:
    pass
