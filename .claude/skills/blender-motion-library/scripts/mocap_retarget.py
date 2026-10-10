# 真人動作捕捉（BVH）→ VRoid 骨架的重新對應（retarget）＋腳底修正。2026-10-07 試驗版，尚未接進 actions_custom.py。
# exec 在 pose_lib.py／actions.py 之後（要用 ARM、BODY_ORDER、bn、sole_points、HANDS）。
#
# 用法（GUI 或背景 Blender 都可以；BVH 用 Blender 內建匯入器讀，不執行檔案裡的任何東西）：
#     use("studio", "pose_lib", "actions", "mocap_retarget")
#     W = mocap_action(r"D:\render-work\mocap\cmu\35_01.bvh", frames=(60, 324), heading=90, origin=(-1.3, 0.0))
#     pose_frame(ARM, W(t))            # t∈[0,1]：片段開頭到結尾（一次性動作，不循環）
#     W.dur（秒）、W.info（比例、修正量等數字）、W.contacts（每隻腳著地的時間段）
#
# 做法：
#   1. 匯入 BVH（CMU／cgspeed 版：第 1 格是加上去的 T 字站姿、面向 BVH +Z、Y 軸朝上），匯入器把 Y-up 轉成 Blender Z-up。
#      讀完每格每根骨頭的世界旋轉與骨盆位置就把匯入的物件刪掉。
#   2. 旋轉對應：以第 1 格 T 字站姿當來源的基準姿勢（VRoid 的 rest 也是 T 字），
#      來源每格的「世界旋轉變化量」D＝Q(f)·Q(T姿)⁻¹ 套到目標 rest 上；
#      四肢與肩膀另外做「方向對齊」A：把 T 姿裡來源骨頭的方向轉到目標骨頭的方向，所以四肢的絕對方向和真人一樣
#      （兩邊 T 姿的手臂下垂角、腿的外張角不同也不會帶進來）。軀幹、頭不做方向對齊（只套變化量，保留 VRoid 的直立 rest）。
#      整體先繞 Z 轉，讓來源 T 姿面向 −Y（和 VRoid 一樣），再依 heading 把行進方向轉到指定朝向。
#   3. 比例：骨盆位置 × (目標骨盆高 ÷ 來源 T 姿骨盆高)；水平方向再用最小平方法微調（讓著地腳在 FK 下滑最少）。
#   4. 腳底修正：每隻腳依鞋底取樣點判斷著地；著地期間逐格把「兩格都踩在地上的鞋底點」水平固定（腳跟滾到腳尖也不滑），
#      高度貼地；離地期間把偏移量平滑接回下一次著地。腿用兩骨 IK 對到修正後的腳踝，膝蓋方向取真人的膝蓋，
#      腳掌、腳趾維持真人的世界旋轉（保留腳跟著地→放平→墊腳尖的滾動）。腿構不到時骨盆平滑下沉（取前後 0.15 秒最大值再平均）。
#   5. 結果每格存成「骨頭世界旋轉＋骨盆位移」，fn(t) 在格與格之間 slerp，輸出一般的姿勢 dict（每根骨頭一個世界軸旋轉），
#      所以 pose_frame、check_lib、render_actions 都不用改。手指用 walk_relax（BVH 沒有手指資料）。
#   6. 手掌（2026-10-09 修）：方向取手腕→HandIndex1（FingerBase 和手腕同一點、是零向量），手腕彎度只取真人的 WRIST_GAIN、最多 WRIST_MAX。
import bpy, math, os
from mathutils import Vector, Quaternion, Matrix

# VRoid（pose_lib 的 key） ← CMU／cgspeed BVH 骨頭名稱
CMU_MAP = {
    "Hips": "Hips", "Spine": "LowerBack", "Chest": "Spine", "UpperChest": "Spine1", "Neck": "Neck1", "Head": "Head",
    "L_Shoulder": "LeftShoulder", "L_UpperArm": "LeftArm", "L_LowerArm": "LeftForeArm", "L_Hand": "LeftHand",
    "R_Shoulder": "RightShoulder", "R_UpperArm": "RightArm", "R_LowerArm": "RightForeArm", "R_Hand": "RightHand",
    "L_UpperLeg": "LeftUpLeg", "L_LowerLeg": "LeftLeg", "L_Foot": "LeftFoot",
    "R_UpperLeg": "RightUpLeg", "R_LowerLeg": "RightLeg", "R_Foot": "RightFoot",
}
# 腳趾不抄 CMU：CMU 的 toes 雜訊很大（每格 40～70° 的抖動）。改成跟著腳掌，腳掌往上翹到腳尖壓進地板時才往上折（_toe_fix）
# 方向對齊用：(來源骨頭, 來源子關節)、(目標子骨頭)；沒列的只套變化量
# 手掌方向用 HandIndex1（食指根）：CMU（cgspeed 版）的 FingerBase 和 Hand 在同一點（BVH 的 OFFSET 0 0 0），拿它當方向是零向量，
# 2026-10-09 之前就是這樣，算出來的手掌整個往回折（手腕 168～178°，手指指向手肘）
_DIR_SRC = {"L_Shoulder": "LeftArm", "L_UpperArm": "LeftForeArm", "L_LowerArm": "LeftHand", "L_Hand": "LeftHandIndex1",
            "R_Shoulder": "RightArm", "R_UpperArm": "RightForeArm", "R_LowerArm": "RightHand", "R_Hand": "RightHandIndex1",
            "L_UpperLeg": "LeftLeg", "L_LowerLeg": "LeftFoot",
            "R_UpperLeg": "RightLeg", "R_LowerLeg": "RightFoot"}
# 腳掌不做方向對齊：VRoid 的腳踝→腳掌是斜的、CMU 的斜度不同，對齊方向的話著地時腳掌會歪（只有 1～2 個鞋底點碰地）。
# 兩邊的 T 姿腳都平踩在地上，所以腳掌只套「T 姿 → 這一格」的變化量
_DIR_TGT = {"L_Shoulder": "L_UpperArm", "L_UpperArm": "L_LowerArm", "L_LowerArm": "L_Hand", "L_Hand": "L_Middle1",
            "R_Shoulder": "R_UpperArm", "R_UpperArm": "R_LowerArm", "R_LowerArm": "R_Hand", "R_Hand": "R_Middle1",
            "L_UpperLeg": "L_LowerLeg", "L_LowerLeg": "L_Foot",
            "R_UpperLeg": "R_LowerLeg", "R_LowerLeg": "R_Foot"}


# 手臂、腿的鏈：(目標 [上段, 下段, 末端], 來源關節 [上段頭, 下段頭, 末端頭, 末端的子關節],
#               rest 時「往正常方向彎」的轉軸（世界）, 打直時的預設轉軸（世界，要乘上哪根骨頭的旋轉）)
# 轉軸＝上段方向 × 下段方向。VRoid rest（T 字、掌心朝下、面向 −Y）：左手肘往前彎＝−Z、右手肘＝+Z；膝蓋往後彎＝+X。
# 手臂垂下時手肘往前彎的轉軸＝−X（跟著 UpperChest 轉）；腿的預設＝+X（跟著 Hips 轉）。
# 為什麼要這樣：CMU 補上的 T 姿掌心朝向和 VRoid 不同，只套「T 姿 → 這一格」的變化量會把扭轉差帶進來，
# 手肘、膝蓋彎的角度對、方向錯（右手橫在肚子前、膝蓋內靠）。改成用真人的手肘／膝蓋彎曲平面直接定扭轉。
_CHAINS = [
    (("L_UpperArm", "L_LowerArm", "L_Hand", "L_Middle1"), ("LeftArm", "LeftForeArm", "LeftHand", "LeftHandIndex1"),
     Vector((0, 0, -1)), ("UpperChest", Vector((-1, 0, 0)))),
    (("R_UpperArm", "R_LowerArm", "R_Hand", "R_Middle1"), ("RightArm", "RightForeArm", "RightHand", "RightHandIndex1"),
     Vector((0, 0, 1)), ("UpperChest", Vector((-1, 0, 0)))),
    (("L_UpperLeg", "L_LowerLeg", "L_Foot", None), ("LeftUpLeg", "LeftLeg", "LeftFoot", None),
     Vector((1, 0, 0)), ("Hips", Vector((1, 0, 0)))),
    (("R_UpperLeg", "R_LowerLeg", "R_Foot", None), ("RightUpLeg", "RightLeg", "RightFoot", None),
     Vector((1, 0, 0)), ("Hips", Vector((1, 0, 0)))),
]
GROUND_GAP = 0.002                               # 著地時鞋底取樣點離地（公尺）：取樣點每 3 個頂點取 1 個，網格的最低點會再低幾 mm
PIVOT_Z = 0.002                                  # 鎖腳的支點：離地 PIVOT_Z 以內的鞋底點（5 mm 的話會混進正在翹起的點，量到 1.1 mm 的滑步）
SWING_CLEAR = 0.006                              # 擺盪腳最低離地（公尺）
ARM_OUT = 12.0                                   # 手臂往外張的角度（度）：新郎 5° 時前臂近手肘處仍擦進腰側 19 mm，12° 為 0
HINGE_DEFAULT_W = math.sin(math.radians(10))     # 彎曲小於約 10° 時，轉軸漸漸改用預設方向（快打直時真人的轉軸不穩）
WRIST_GAIN = 0.5                                 # 手腕彎度只取真人的一半：CMU 走路時手腕一直量到 25～30°（標記點貼法的固定偏差），整段照抄像手掌往上翹
WRIST_MAX = 30.0                                 # 手腕（手掌相對前臂）最多彎幾度：CMU 手上只有一個標記點，手掌方向雜訊大；超過就往前臂方向收回


# 名稱刻意不用 _chain：本檔和 actions_custom.py 會載進同一個命名空間，同名會蓋掉 actions_custom 的 _chain(arm, key)
def _mocap_chain(rig, R, chain, P, pitch=0.0):
    """P：來源關節的世界位置（上段頭、下段頭、末端頭、末端子關節）。改寫 R 裡上段、下段（手臂連手掌）的世界旋轉"""
    (up, lo, end, tip), _, h_rest, (dbone, dvec) = chain
    rq, rh = rig.rest_q, rig.rest_h
    if tip is not None and ARM_OUT:                  # 手臂往外張 ARM_OUT 度（繞胸口的前方軸、以肩膀為中心）：
        fwd = (R["UpperChest"] @ rq["UpperChest"].inverted()) @ Vector((0, -1, 0))   # VRoid 腰臀比 CMU 受試者寬，照抄會擦進腰側
        q = Quaternion(fwd, math.radians(ARM_OUT if up.startswith("L") else -ARM_OUT))
        P = [P[0]] + [(P[0] + q @ (p - P[0])) if p is not None else None for p in P[1:]]
    if tip is not None and pitch:                    # 整條手臂繞肩膀往後轉 pitch 度（扣掉「手相對肩膀」比真人偏前的固定量）
        lat = (R["UpperChest"] @ rq["UpperChest"].inverted()) @ Vector((1, 0, 0))
        q = Quaternion(lat, math.radians(pitch))
        P = [P[0]] + [(P[0] + q @ (p - P[0])) if p is not None else None for p in P[1:]]
    d1 = (P[1] - P[0]).normalized(); d2 = (P[2] - P[1]).normalized()
    n_def = (R[dbone] @ rq[dbone].inverted()) @ dvec
    n = d1.cross(d2) + n_def * HINGE_DEFAULT_W
    # 上段：rest 方向 → d1（最小旋轉），再繞 d1 轉，讓 rest 的轉軸對到 n
    r0 = (rh[lo] - rh[up]).normalized()
    Sw = _qbetween(r0, d1)
    h1 = Sw @ h_rest
    h1 = (h1 - d1 * h1.dot(d1)); nn = (n - d1 * n.dot(d1))
    tw = math.atan2(d1.dot(h1.cross(nn)), h1.dot(nn)) if h1.length > 1e-6 and nn.length > 1e-6 else 0.0
    R[up] = Quaternion(d1, tw) @ Sw @ rq[up]
    # 下段：跟著上段，最小旋轉轉到 d2
    inh = R[up] @ rq[up].inverted() @ rq[lo]
    cur = (inh @ rq[lo].inverted()) @ (rh[end] - rh[lo])
    R[lo] = _qbetween(cur, d2) @ inh
    if tip is not None:                              # 手掌：跟著前臂，最小旋轉轉到真人手掌方向（不另外扭轉）
        inh = R[lo] @ rq[lo].inverted() @ rq[end]
        cur = (inh @ rq[end].inverted()) @ (rh[tip] - rh[end])
        if globals().get("MOCAP_HAND_LEGACY"):       # 只給改前對照用：2026-10-09 之前的算法（FingerBase＝零向量，手掌往回折）
            d3 = (P[3] - P[2]).normalized()
        else:
            d3 = _wrist_dir(d2, P[3] - P[2] if P[3] is not None else None)
        R[end] = _qbetween(cur, d3) @ inh


def _hsrc(n):
    return n.replace("HandIndex1", "FingerBase") if n and globals().get("MOCAP_HAND_LEGACY") else n


def _wrist_dir(fore, hand):
    """手掌方向：真人的手掌方向（前臂方向 fore、手腕→食指根 hand），和前臂的夾角乘 WRIST_GAIN、限制在 WRIST_MAX 以內；資料是零向量就順著前臂"""
    fore = fore.normalized()
    if hand is None or hand.length < 1e-6:
        return fore
    hand = hand.normalized(); a = fore.angle(hand)
    ax = fore.cross(hand)
    if ax.length < 1e-6:                             # 平行或剛好反向：沒有可以收回的平面，順著前臂
        return fore
    return Quaternion(ax.normalized(), min(a * WRIST_GAIN, math.radians(WRIST_MAX))) @ fore


def _slerp(a, b, f):
    """四元數內插，先把 b 的符號對到 a（mathutils 的 slerp 不保證走短路徑；q 和 −q 是同一個旋轉，直接內插會多轉一大圈）"""
    if a.dot(b) < 0:
        b = -b
    return a.slerp(b, f)


def _qbetween(a, b):
    a = a.normalized(); b = b.normalized()
    return a.rotation_difference(b)


def read_bvh(path, ref=1, frames=None):
    """匯入 BVH、讀出 {骨頭: [世界四元數]}、{骨頭: [世界頭部位置]}（第 0 個＝ref 格的 T 姿），讀完刪掉匯入的物件"""
    before = set(bpy.data.objects)
    acts_before = set(bpy.data.actions)
    bpy.ops.import_anim.bvh(filepath=path, global_scale=1.0, frame_start=1, use_fps_scale=False,
                            rotate_mode="NATIVE", axis_forward="-Z", axis_up="Y", update_scene_fps=False,
                            update_scene_duration=False)
    src = [o for o in bpy.data.objects if o not in before][0]
    sc = bpy.context.scene; keep_f = sc.frame_current
    f0, f1 = (int(x) for x in src.animation_data.action.frame_range)
    want = [ref] + list(range(frames[0], frames[1] + 1) if frames else range(f0 + 1, f1 + 1))
    names = [pb.name for pb in src.pose.bones]
    Q = {n: [] for n in names}; H = {n: [] for n in names}
    for f in want:
        sc.frame_set(f)
        for n in names:
            M = src.matrix_world @ src.pose.bones[n].matrix
            Q[n].append(M.to_quaternion()); H[n].append(M.to_translation())
    sc.frame_set(keep_f)
    act = src.animation_data.action
    arm_data = src.data
    bpy.data.objects.remove(src)
    if arm_data.users == 0:
        bpy.data.armatures.remove(arm_data)
    for a in set(bpy.data.actions) - acts_before:
        bpy.data.actions.remove(a)
    return Q, H


class _Rig:
    """目標骨架的 rest 資料與解析式 FK（不碰 Blender 的姿勢，快）"""
    def __init__(self, arm):
        self.arm = arm
        B = arm.data.bones
        self.keys = list(BODY_ORDER)
        self.rest_q = {k: B[bn(k)].matrix_local.to_quaternion() for k in self.keys}
        self.rest_h = {k: B[bn(k)].head_local.copy() for k in self.keys}
        names = {bn(k): k for k in self.keys}
        self.parent = {}
        for k in self.keys:
            p = B[bn(k)].parent
            while p is not None and p.name not in names:
                p = p.parent
            self.parent[k] = names[p.name] if p is not None else None
        for extra in ("L_Middle1", "R_Middle1"):
            self.rest_h[extra] = B[bn(extra)].head_local.copy()

    def fk(self, R, root):
        """R：{key: 世界旋轉}（全部 BODY_ORDER）；root：骨盆位移 → {key: 頭部世界位置}"""
        Hd = {}
        for k in self.keys:
            p = self.parent[k]
            if p is None:
                Hd[k] = self.rest_h[k] + root
            else:
                Hd[k] = Hd[p] + (R[p] @ self.rest_q[p].inverted()) @ (self.rest_h[k] - self.rest_h[p])
        return Hd

    def to_dict(self, R):
        """世界旋轉 → pose_lib 的姿勢 dict（每根骨頭一個世界軸旋轉，照 BODY_ORDER 套）"""
        P = {}
        for k in self.keys:
            p = self.parent[k]
            inh = self.rest_q[k] if p is None else (R[p] @ self.rest_q[p].inverted() @ self.rest_q[k])
            d = R[k] @ inh.inverted()
            ang = d.angle
            if ang > math.pi:
                ang -= 2 * math.pi
            if abs(ang) < 1e-6:
                continue
            ax = d.axis
            P[k] = [((ax.x, ax.y, ax.z), math.degrees(ang))]
        return P


def _gauss(vals, sigma, radius=None):
    """高斯平滑（邊界用最近的值延伸）；radius＝核的半寬（格），預設 3 sigma"""
    n = len(vals); sigma = max(1e-6, sigma); r = int(radius if radius is not None else math.ceil(3 * sigma))
    ker = [math.exp(-0.5 * (k / sigma) ** 2) for k in range(-r, r + 1)]; sk = sum(ker)
    return [sum(ker[k + r] * vals[min(n - 1, max(0, i + k))] for k in range(-r, r + 1)) / sk for i in range(n)]


def _smooth_max(vals, w):
    n = len(vals)
    mx = [max(vals[max(0, i - w):i + w + 1]) for i in range(n)]
    return [sum(mx[max(0, i - w):i + w + 1]) / len(mx[max(0, i - w):i + w + 1]) for i in range(n)]


def mocap_action(path, frames, heading=90.0, origin=(0.0, 0.0), src_fps=120.0, ref=1, arm=None,
                 stance_v=0.5, reach=0.995, foot_fix=True, fix_arm_offset=True, smile=0.45, hands=("walk_relax", "walk_relax")):
    """frames：BVH 的格號範圍（含頭尾）；heading：行進方向（度，和 rz 同慣例：90＝往 +X）；origin：第一格骨盆的世界 (x, y)"""
    arm = arm or ARM
    rig = _Rig(arm)
    Q, H = read_bvh(path, ref=ref, frames=frames)
    N = len(Q["Hips"]) - 1                           # 第 0 個是 T 姿
    # ── 1. 整體朝向：來源 T 姿的左手方向轉到 +X（面向 −Y）
    left = H["LeftUpLeg"][0] - H["RightUpLeg"][0]; left.z = 0
    Rg = Quaternion((0, 0, 1), math.atan2(left.cross(Vector((1, 0, 0))).z, left.dot(Vector((1, 0, 0)))))   # 只繞 Z
    # 行進方向（片段頭尾骨盆位移）→ heading
    trav = Rg @ (H["Hips"][N] - H["Hips"][1]); trav.z = 0
    if heading is None:                              # 原地動作（揮手等，2026-10-09 加）：不看行進方向，改成讓片段裡平均的骨盆朝向面向 −Y
        lm = sum((Rg @ (H["LeftUpLeg"][i] - H["RightUpLeg"][i]) for i in range(1, N + 1)), Vector()); lm.z = 0
        Hh = Quaternion((0, 0, 1), math.atan2(lm.cross(Vector((1, 0, 0))).z, lm.dot(Vector((1, 0, 0)))))
    else:
        hr = math.radians(heading); want = Vector((math.sin(hr), -math.cos(hr), 0))
        Hh = Quaternion((0, 0, 1), math.atan2(trav.cross(want).z, trav.dot(want)))
    C = Hh @ Rg
    # ── 2. 方向對齊
    A = {}
    for k, s in CMU_MAP.items():
        if k in _DIR_SRC and _DIR_SRC[k] in H:
            sd = Rg @ (H[_DIR_SRC[k]][0] - H[s][0])
            td = rig.rest_h[_DIR_TGT[k]] - rig.rest_h[k]
            A[k] = _qbetween(td, sd)                   # 目標 rest 方向 → 來源 T 姿方向
        else:
            A[k] = Quaternion()
    # ── 3. 比例
    # 比例用腿長（T 姿的髖關節離地高度）：VRoid 的 Hips 骨頭頭部比髖關節高，用骨盆高度算會高估腿長，腳會浮起、著地腳被拖著走
    leg_t = 0.5 * (rig.rest_h["L_UpperLeg"].z + rig.rest_h["R_UpperLeg"].z)
    foot_s = min(min(H["LeftToeBase"][0].z, H["RightToeBase"][0].z), min(H["LeftFoot"][0].z, H["RightFoot"][0].z))
    leg_s = 0.5 * (H["LeftUpLeg"][0].z + H["RightUpLeg"][0].z) - foot_s
    s_v = leg_t / leg_s
    hips_src = [C @ H["Hips"][i] for i in range(1, N + 1)]
    R_fk = []
    for i in range(1, N + 1):
        R = {}
        for k, s in CMU_MAP.items():
            D = (Rg @ Q[s][i]) @ (Rg @ Q[s][0]).inverted()
            R[k] = (Hh @ D) @ A[k].inverted() @ rig.rest_q[k]
        for chain in _CHAINS:                             # 手臂、腿：對準方向＋對齊彎曲平面（取代上面的結果）
            _mocap_chain(rig, R, chain, [(C @ H[_hsrc(n)][i]) if n and _hsrc(n) in H else None for n in chain[1]])
        for sd in "LR":                                   # 腳趾跟著腳掌（相對 rest 不轉）
            R[f"{sd}_ToeBase"] = R[f"{sd}_Foot"] @ rig.rest_q[f"{sd}_Foot"].inverted() @ rig.rest_q[f"{sd}_ToeBase"]
        R_fk.append(R)
    arm_pitch = _arm_pitch_fix(rig, R_fk, H, C, s_v, hips_src, build_root_v=None) if fix_arm_offset else {"L": 0.0, "R": 0.0}
    if any(arm_pitch.values()):
        for i in range(1, N + 1):
            for chain in _CHAINS[:2]:
                sd = chain[0][0][0]
                _mocap_chain(rig, R_fk[i - 1], chain, [(C @ H[_hsrc(n)][i]) if n and _hsrc(n) in H else None for n in chain[1]], pitch=arm_pitch[sd])
    sole = {"L": [], "R": []}
    for b, co in sole_points(arm):
        sd = "L" if "_L_" in b else "R"
        key = next(k for k in rig.keys if bn(k) == b) if any(bn(k) == b for k in rig.keys) else None
        if key:
            sole[sd].append((key, co))

    def sole_pts(R, Hd, sd, off=Vector()):
        out = []
        for key, co in sole[sd]:
            M = Matrix.Translation(Hd[key] + off) @ R[key].to_matrix().to_4x4()
            out.append(M @ co)
        return out

    def build_root(sh):
        p0 = hips_src[0]
        z0 = (C @ H["Hips"][0]).z                       # 骨盆高度：rest 高度 ＋ (來源和 T 姿的高度差) × 比例
        return [Vector((origin[0] + (p.x - p0.x) * sh, origin[1] + (p.y - p0.y) * sh, rig.rest_h["Hips"].z + (p.z - z0) * s_v))
                - rig.rest_h["Hips"] for p in hips_src]

    # 著地判斷用來源的真人資料（和目標體型無關）：腳踝或腳掌（ToeBase 頭）任一個水平速度 < stance_v（m/s，換算成目標尺度）
    contact = {}
    for sd, ank, toe in (("L", "LeftFoot", "LeftToeBase"), ("R", "RightFoot", "RightToeBase")):
        c = []
        for i in range(1, N + 1):
            j = max(1, i - 1); k = min(N, i + 1)
            va = ((H[ank][k] - H[ank][j]).xy.length) * s_v * src_fps / max(1, k - j)
            vt = ((H[toe][k] - H[toe][j]).xy.length) * s_v * src_fps / max(1, k - j)
            c.append(min(va, vt) < stance_v)
        runs = []; i = 0
        while i < N:
            if c[i]:
                j = i
                while j + 1 < N and c[j + 1]:
                    j += 1
                if j - i + 1 >= int(0.08 * src_fps) or i == 0 or j == N - 1:
                    runs.append((i, j))
                i = j + 1
            else:
                i += 1
        merged = []                                   # 間隔 < 0.12 秒的著地段合併（同一次著地被速度雜訊切開）
        for r in runs:
            if merged and r[0] - merged[-1][1] <= int(0.12 * src_fps):
                merged[-1] = (merged[-1][0], r[1])
            else:
                merged.append(r)
        contact[sd] = merged
    # 水平比例：最小平方法，讓著地腳在 FK 下的鞋底最低點水平移動最少（限制在垂直比例的 ±20%）
    roots = build_root(s_v)
    Hd0 = [rig.fk(R_fk[i], roots[i]) for i in range(N)]
    low = {sd: [min(sole_pts(R_fk[i], Hd0[i], sd), key=lambda v: v.z) for i in range(N)] for sd in "LR"}
    st_z = [low[sd][i].z for sd in "LR" for (a, b) in contact[sd] for i in range(a, b + 1)]
    dz0 = -sorted(st_z)[len(st_z) // 2] if st_z else 0.0
    num = den = 0.0
    for sd in "LR":
        for (a, b) in contact[sd]:
            for i in range(a + 1, b + 1):
                dh = (hips_src[i] - hips_src[i - 1]); dh.z = 0
                dr = (low[sd][i] - low[sd][i - 1]) - dh * s_v; dr.z = 0
                num += dh.dot(dr); den += dh.dot(dh)
    s_h = -num / den if den > 1e-9 else s_v
    s_h_ls = s_h
    s_h = s_v      # 2026-10-08：水平比例＝腿長比例。最小平方估計會把「腳跟滾到腳掌、最低點往前移」當成滑步而低估（只留作參考）
    roots = build_root(s_h)
    for r in roots:
        r.z += dz0
    info = dict(frames=N, src_fps=src_fps, s_vertical=round(s_v, 4), s_horizontal=round(s_h, 4),
                s_horizontal_lsq=round(s_h_ls, 4), dz=round(dz0, 4),
                arm_pitch_deg={k: round(v, 2) for k, v in arm_pitch.items()})

    R_out = R_fk
    contacts = {"L": [], "R": []}
    if foot_fix:
        R_out, roots, contacts, extra = _fix_feet(rig, R_fk, roots, sole, sole_pts, contact, reach, src_fps)
        info.update(extra)
    dur = (N - 1) / src_fps
    face_base = {"Fcl_ALL_Fun": smile}

    def fn(t):
        x = max(0.0, min(1.0, t)) * (N - 1); i = min(int(x), N - 2); f = x - i
        R = {k: _slerp(R_out[i][k], R_out[i + 1][k], f) for k in rig.keys}
        root = roots[i].lerp(roots[i + 1], f)
        P = rig.to_dict(R)
        blink = 1.0 if abs(t - 0.62) < 0.012 else 0.0
        return dict(P, hands=hands, root=(root.x, root.y, root.z), rz=0.0, ground=False,
                    face=dict(face_base, Fcl_EYE_Close=blink))

    fn.dur = dur; fn.info = info; fn.contacts = contacts; fn.rig = rig
    fn.R = R_out; fn.roots = roots; fn.R_fk = R_fk; fn.contact_src = contact
    fn.pos = lambda t: tuple(roots[int(round(max(0, min(1, t)) * (N - 1)))].xy + rig.rest_h["Hips"].xy)
    return fn


def _fix_feet(rig, R_fk, roots, sole, sole_pts, contact, reach, fps):
    N = len(R_fk)
    Hd = [rig.fk(R_fk[i], roots[i]) for i in range(N)]
    pts = {sd: [sole_pts(R_fk[i], Hd[i], sd) for i in range(N)] for sd in "LR"}
    # 每隻腳的偏移量 O(f)：著地時逐格固定踩地的鞋底點、高度貼地；離地時平滑接回
    O = {}
    drift = {}
    for sd in "LR":
        off = [None] * N; runs = contact[sd]; dmax = 0.0
        for (a, b) in runs:
            o = Vector((0, 0, GROUND_GAP - min(p.z for p in pts[sd][a])))
            off[a] = o.copy()
            for i in range(a + 1, b + 1):
                prev = [p + off[i - 1] for p in pts[sd][i - 1]]
                cur_z = GROUND_GAP - min(p.z for p in pts[sd][i])
                cur = [p + Vector((off[i - 1].x, off[i - 1].y, cur_z)) for p in pts[sd][i]]
                S = [m for m in range(len(cur)) if prev[m].z <= GROUND_GAP + PIVOT_Z and cur[m].z <= GROUND_GAP + PIVOT_Z]
                if len(S) < 3:
                    S = sorted(range(len(cur)), key=lambda m: cur[m].z)[:3]
                dx = sum(prev[m].x - cur[m].x for m in S) / len(S)
                dy = sum(prev[m].y - cur[m].y for m in S) / len(S)
                off[i] = Vector((off[i - 1].x + dx, off[i - 1].y + dy, cur_z))
            dmax = max(dmax, off[b].xy.length)
        # 離地：前一段結尾 → 下一段開頭，用 smoothstep 接；片段開頭／結尾在空中的部分沿用最近的值
        known = [i for i in range(N) if off[i] is not None]
        if not known:
            off = [Vector() for _ in range(N)]
        else:
            for i in range(N):
                if off[i] is not None:
                    continue
                a = max((k for k in known if k < i), default=None); b = min((k for k in known if k > i), default=None)
                if a is None:
                    off[i] = off[b].copy()
                elif b is None:
                    off[i] = off[a].copy()
                else:
                    u = (i - a) / (b - a); e = u * u * (3 - 2 * u)
                    off[i] = off[a].lerp(off[b], e)
        # 擺盪腳離地至少 SWING_CLEAR，只在著地前／離地後 0.05 秒內降到 0：VRoid 的腳在擺盪末段會貼著地面（< 5 mm）往前移，
        # 會被當成「踩在地上滑」。需要往上抬的量取前後 0.05 秒的最大值再平均（平滑），只往上加
        if known:
            fade = max(1, int(0.05 * fps)); bounds = [x for r in runs for x in r]
            def clear(i):
                d = min((abs(i - x) for x in bounds), default=fade)
                return GROUND_GAP + (SWING_CLEAR - GROUND_GAP) * min(1.0, d / fade)
            lift = [0.0 if any(a <= i <= b for a, b in runs) else max(0.0, clear(i) - (min(p.z for p in pts[sd][i]) + off[i].z))
                    for i in range(N)]
            if any(lift):
                lift = _smooth_max(lift, max(1, int(0.05 * fps)))
                for i in range(N):
                    if not any(a <= i <= b for a, b in runs):
                        off[i] = off[i] + Vector((0, 0, lift[i]))
        O[sd] = off; drift[sd] = round(dmax * 1000, 1)
    # 骨盆下沉：腿構不到就整體往下
    L = {}
    for sd in "LR":
        ul, ll, ft = f"{sd}_UpperLeg", f"{sd}_LowerLeg", f"{sd}_Foot"
        L[sd] = ((rig.rest_h[ll] - rig.rest_h[ul]).length, (rig.rest_h[ft] - rig.rest_h[ll]).length)
    need = []
    for i in range(N):
        req = 0.0
        for sd in "LR":
            hip = Hd[i][f"{sd}_UpperLeg"]; ank = Hd[i][f"{sd}_Foot"] + O[sd][i]
            Rmax = (L[sd][0] + L[sd][1]) * reach
            v = ank - hip; hz = v.xy.length
            if v.length > Rmax:
                req = max(req, (-v.z) - math.sqrt(max(Rmax * Rmax - hz * hz, 0.0)))
            # 回推：v.z 是負的（腳在下面）；需要骨盆再降 req
        need.append(max(0.0, req))
    w = max(1, int(0.15 * fps))
    drop = _smooth_max(need, w) if any(need) else [0.0] * N
    roots = [r - Vector((0, 0, d)) for r, d in zip(roots, drop)]
    # 腿 IK
    R_out = []; toe_ang = {"L": [], "R": []}
    for i in range(N):
        R = dict(R_fk[i]); Hn = rig.fk(R, roots[i])
        for sd in "LR":
            ul, ll, ft = f"{sd}_UpperLeg", f"{sd}_LowerLeg", f"{sd}_Foot"
            L1, L2 = L[sd]
            S = Hn[ul]; W = Hd[i][ft] + O[sd][i]
            knee_fk = Hd[i][ll] + O[sd][i]
            v = W - S; d = max(1e-4, min(v.length, (L1 + L2) * 0.9999)); dr = v.normalized()
            a = math.acos(max(-1.0, min(1.0, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d))))
            pp = knee_fk - S; pp = pp - dr * pp.dot(dr)
            if pp.length < 1e-6:
                pp = Vector((0, -1, 0))
            pp.normalize()
            E = S + dr * math.cos(a) * L1 + pp * math.sin(a) * L1
            # 大腿：FK 方向 → 新方向（最小旋轉，保留扭轉）
            cur_t = (R[ul] @ rig.rest_q[ul].inverted()) @ (rig.rest_h[ll] - rig.rest_h[ul])
            R[ul] = _qbetween(cur_t, E - S) @ R[ul]
            cur_s = (R[ll] @ rig.rest_q[ll].inverted()) @ (rig.rest_h[ft] - rig.rest_h[ll])
            R[ll] = _qbetween(cur_s, (S + dr * d) - E) @ R[ll]
            toe_ang[sd].append(_toe_fix(rig, R, sd, roots[i], sole, sole_pts, O[sd][i] + Hd[i][ft] - rig.fk(R, roots[i])[ft]))
        R_out.append(R)
    # 腳趾折角在時間上平滑（取前後 0.06 秒最大值再平均）：離地那一格不會一下子彈回來
    w = max(1, int(0.06 * fps))
    for sd in "LR":
        mag = _smooth_max([abs(a) for a in toe_ang[sd]], w)
        sg = 1 if sum(toe_ang[sd]) >= 0 else -1
        tb = f"{sd}_ToeBase"; ft = f"{sd}_Foot"
        for i in range(N):
            R = R_out[i]
            ax = (R[ft] @ rig.rest_q[ft].inverted()) @ Vector((1, 0, 0))
            R[tb] = Quaternion(ax, sg * mag[i]) @ R[tb]
    extra = dict(pelvis_drop_max_mm=round(max(drop) * 1000, 1), stance_drift_mm=drift,
                 contacts={sd: [(round(a / fps, 3), round(b / fps, 3)) for a, b in contact[sd]] for sd in "LR"})
    return R_out, roots, {sd: contact[sd] for sd in "LR"}, extra


def _toe_fix(rig, R, sd, root, sole, sole_pts, off):
    """算出腳趾要往上折多少（弧度），腳趾的鞋底點才不低於地面（腳掌墊起、腳尖撐地時）。off：讓 FK 腳踝對到 IK 腳踝的位移（IK 後應接近 0）"""
    tb = f"{sd}_ToeBase"; ft = f"{sd}_Foot"
    Hd = rig.fk(R, root)
    toe_pts = [(k, co) for k, co in sole[sd] if k == tb]
    if not toe_pts:
        return 0.0
    def lowest(Rt):
        return min((Matrix.Translation(Hd[tb] + off) @ Rt.to_matrix().to_4x4() @ co).z for _, co in toe_pts)
    z0 = lowest(R[tb])
    if z0 >= 0.0:
        return 0.0
    ax = (R[ft] @ rig.rest_q[ft].inverted()) @ Vector((1, 0, 0))
    lo, hi = 0.0, math.radians(60)
    for sgn in (1, -1):                          # 找哪個方向是往上折
        if lowest(Quaternion(ax, sgn * math.radians(5)) @ R[tb]) > z0:
            break
    for _ in range(20):
        mid = 0.5 * (lo + hi)
        if lowest(Quaternion(ax, sgn * mid) @ R[tb]) < 0.0:
            lo = mid
        else:
            hi = mid
    return sgn * hi                              # 角度（弧度）；由呼叫端平滑後再套


def _arm_pitch_fix(rig, R_fk, H, C, s_v, hips_src, build_root_v=None):
    """手腕相對肩膀、沿行進方向的平均前後位置：目標 − 真人（換算成目標尺度）→ 手臂要往後轉的角度（度）。
    VRoid 和 CMU 的軀幹比例、rest 前傾不同，照抄方向後手平均偏前 4～6 cm，手臂看起來一直停在腰前"""
    N = len(R_fk); out = {}
    tr = (hips_src[-1] - hips_src[0]); tr.z = 0; tr.normalize()
    for sd, sh, hd in (("L", "LeftArm", "LeftHand"), ("R", "RightArm", "RightHand")):
        dsum = 0.0; L = 0.0
        for i in range(N):
            Hd = rig.fk(R_fk[i], Vector())
            tgt = (Hd[f"{sd}_Hand"] - Hd[f"{sd}_UpperArm"]).dot(tr)
            src = (C @ (H[hd][i + 1] - H[sh][i + 1])).dot(tr) * s_v
            dsum += tgt - src; L += (Hd[f"{sd}_Hand"] - Hd[f"{sd}_UpperArm"]).length
        d = dsum / N; L /= N
        out[sd] = math.degrees(math.asin(max(-0.5, min(0.5, d / L)))) if abs(d) > 0.01 else 0.0
    return out



# ════════════════════════ 混合式走路（walk_fwd(style="mocap") 用） ════════════════════════
# 腳印位置與著地時間沿用 walk_fwd 的規劃器（呼叫參數、fn.pos、fn.landings 和舊版完全相同）；
# 姿態依「步態相位」取自真人的一個完整步態週期（左腳跟著地 → 下一次左腳跟著地），時間照規劃器的步伐拉長縮短；
# 起步、停步兩步是混合：權重 w 0→1→0，w=0 時就是舊版（proc）的姿勢，所以接 idle、turn_exit 的頭尾站姿和以前一樣。
# 腳：著地期間鎖地（腳跟著地後 HEEL_PIVOT_S 秒內以腳跟最低點為單一支點，之後用離地 PIVOT_Z 內的鞋底點），
#     著地那一刻腳踝對到舊版的落腳位置；擺盪期間把偏移量平滑接過去；腿用兩骨 IK、膝蓋方向取真人的。
MOCAP_WALK_BVH = os.path.join(LIB, "mocap", "35_01.bvh") if "LIB" in globals() else None
MOCAP_WALK_FRAMES = (60, 324)                    # CMU 35_01 的第 60～324 格（2.2 秒，約 4 步）
# KNEE_FIX（actions_custom 的全域開關，預設關）：開啟＝骨盆高度改成「支撐腳都構得到的最高位置」＋後腳跟自動抬起（腿變直，
# 但 2026-10-08 第 3 輪量到 V12 參數小腿轉速 16.7～18.5°/格、速度突變 11～13.6，還沒過門檻）；關閉＝舊做法（規劃器的骨盆高度）
KNEE_R_STAND = 0.999   # 站著（權重 0）時支撐腿最多伸到腿長的幾成（≈ 膝蓋 175°）
KNEE_R_WALK = 0.996    # 走路中支撐腿（≈ 170°，真人支撐中段約 165～175°）
KNEE_R_SWING = 0.993   # （2026-10-08 第 3 輪起不用：擺盪腳不決定骨盆高度）
KNEE_FADE_S = 0.12     # 支撐腳參與骨盆高度的淡入淡出（秒）
KNEE_LOWPASS_S = 0.15  # 骨盆高度低通的半寬（秒）
KNEE_R_PUSH = 0.995    # 抬腳跟那段：腿伸到這麼長還構不到就抬腳跟
HEEL_RISE_MAX = 40.0   # 自動抬腳跟最多幾度
HEEL_PIVOT_S = 0.0     # 腳跟著地後以腳跟最低點為單一支點的秒數。2026-10-08 試過 0.10：著地下一格滑 3～4.5 mm（比支點集合法的 1.2 mm 差），所以關掉
WALK_GAP = 0.0005      # 著地時鞋底最低點離地（公尺）：用下面的完整鞋底點，所以不必像 GROUND_GAP 留 2 mm；留越多，腳跟放平時離地 2～5 mm 的點轉動帶出的水平位移越大
FOOT_SMOOTH_S_KNEE = 0.11   # KNEE_FIX 開啟時的腳掌平滑（骨盆抬高後 V12 參數滑步 1.11 mm）
FOOT_SMOOTH_S = 0.09   # 腳掌旋轉的時間平滑半寬（秒）。0.07 時新郎加了骨盆修正後 V12 參數滑步 1.15 mm
ROLL_POW = 1.5         # 腳掌滾動縮小量＝(步幅／真人步幅)^ROLL_POW（V12 的 0.5 m 步幅＝0.56 倍）
KNEE_FWD = 0.15        # 膝蓋方向往前加的量（公尺，路徑座標的 −Y）
WALK_PIVOT_Z = 0.005   # 鎖腳支點：兩格都離地 5 mm 內的點（和 check_lib 的滑步量法同一個條件）
PALM_IN = 1.0                                    # 掌心轉向身體內側的比例
_CYCLE = {}


def _cycle(arm, path=None, frames=None):
    """真人步態週期（快取）：{R: [每格世界旋轉], osc: [骨盆相對等速直線的偏移], phiR: 右腳跟著地的相位}，面向 −Y"""
    path = path or MOCAP_WALK_BVH; frames = frames or MOCAP_WALK_FRAMES
    key = (arm.name, path, tuple(frames))
    if key in _CYCLE:
        return _CYCLE[key]
    M = mocap_action(path, frames, heading=0.0, origin=(0.0, 0.0), arm=arm, foot_fix=False)
    hs = {sd: [a for a, b in M.contact_src[sd] if a > 0] for sd in "LR"}
    a, b = hs["L"][0], hs["L"][1]
    r = [x for x in hs["R"] if a < x < b][0]
    R = [dict(M.R_fk[i]) for i in range(a, b + 1)]
    n = b - a
    for k in R[0]:                                # 頭尾相接：最後一格和第一格的差平均分到整個週期
        d = R[0][k] @ R[n][k].inverted()
        for i in range(n + 1):
            R[i][k] = _slerp(Quaternion(), d, i / n) @ R[i][k]
    rq, rh = M.rig.rest_q, M.rig.rest_h
    # 手掌：順著前臂（CMU 的手部資料不可靠），再繞前臂轉到掌心朝身體內側（和舊版垂手相同）。
    # 手肘照彎曲平面對齊後前臂沒有旋前、掌心朝前，和舊版一混就翻面；角度沿時間展開成連續（接近 ±180° 時不會正負對調）
    for sd, sg in (("L", 1), ("R", -1)):
        la, hd = f"{sd}_LowerArm", f"{sd}_Hand"; prev = None; angs = []
        for Ri in R:
            Ri[hd] = Ri[la] @ rq[la].inverted() @ rq[hd]
            ax = ((Ri[la] @ rq[la].inverted()) @ (rh[hd] - rh[la])).normalized()
            pn = (Ri[hd] @ rq[hd].inverted()) @ Vector((0, 0, -1))
            tg = (Ri["UpperChest"] @ rq["UpperChest"].inverted()) @ Vector((-sg, 0, 0))
            pn = pn - ax * pn.dot(ax); tg = tg - ax * tg.dot(ax)
            ang = math.atan2(ax.dot(pn.cross(tg)), pn.dot(tg)) if pn.length > 1e-6 and tg.length > 1e-6 else (prev or 0.0)
            if prev is not None:
                while ang - prev > math.pi:
                    ang -= 2 * math.pi
                while ang - prev < -math.pi:
                    ang += 2 * math.pi
            prev = ang; angs.append((ax, ang))
        for Ri, (ax, ang) in zip(R, angs):
            ang *= PALM_IN
            Ri[la] = Quaternion(ax, ang * 0.5) @ Ri[la]; Ri[hd] = Quaternion(ax, ang) @ Ri[hd]
    hips = [M.roots[i] + M.rig.rest_h["Hips"] for i in range(a, b + 1)]
    osc = [hips[i] - hips[0].lerp(hips[n], i / n) for i in range(n + 1)]
    mz = sum(o.z for o in osc) / len(osc)
    for o in osc:
        o.z -= mz
    span = (hips[n] - hips[0]); span.z = 0
    _CYCLE[key] = dict(R=R, osc=osc, n=n, phiR=(r - a) / n, info=M.info, step=span.length / 2)
    return _CYCLE[key]


def _cyc_sample(C, phi):
    phi %= 1.0; x = phi * C["n"]; i = min(int(x), C["n"] - 1); f = x - i
    R = {k: _slerp(C["R"][i][k], C["R"][i + 1][k], f) for k in C["R"][i]}
    return R, C["osc"][i].lerp(C["osc"][i + 1], f)


_WSOLE = {}


def _walk_sole(arm, rig):
    """完整鞋底點：鞋子 rest 時 z < 4 cm、主要權重在 Foot／ToeBase 的頂點（含鞋頭前緣；pose_lib.sole_points 只取 z < 1.2 cm、
    每 3 點取 1，腳尖撐地時鞋頭前緣會變成最低點而量不到，陷地 1 cm），記成骨頭局部座標"""
    if arm.name in _WSOLE:
        return _WSOLE[arm.name]
    sh = bpy.data.objects[f"{arm.name[:-len('_Armature')]}_Shoes"]; names = {g.index: g.name for g in sh.vertex_groups}
    keys = {bn(k): k for k in rig.keys}; out = {"L": [], "R": []}
    for v in sh.data.vertices:
        if v.co.z > 0.04 or not v.groups:
            continue
        g = max(v.groups, key=lambda g: g.weight); b = names[g.group]
        if b in keys and ("Foot" in b or "ToeBase" in b):
            out["L" if "_L_" in b else "R"].append((keys[b], arm.data.bones[b].matrix_local.inverted() @ v.co))
    _WSOLE[arm.name] = out
    return out


def walk_mocap(proc, arm, rz, origin, arms="swing", sr=120.0, reach=0.995):
    """proc：同參數的舊版 walk_fwd（style='proc'）。回傳介面和舊版相同的 fn(t)。
    內部都在「路徑座標」算（面向 −Y、出發點在原點、物件不旋轉），最後才轉到世界（origin、rz）"""
    G = proc.gait; plan = G.steps; dur = proc.dur
    rig = _Rig(arm); C = _cycle(arm); phiR = C["phiR"]
    pt_, pe_ = posture_fix() if "posture_fix" in globals() else (0.0, 0.0)
    rq, rh = rig.rest_q, rig.rest_h
    # 相位：每一步腳跟著地＝左 0／右 phiR，中間線性；頭尾用相鄰那一段的斜率外插
    pts = []; ph = 0.0 if plan[0]["side"] == "L" else phiR
    for j, st in enumerate(plan):
        if j:
            ph += phiR if st["side"] == "R" else (1 - phiR)
        pts.append((st["t1"], ph))

    def phase(t):
        if len(pts) == 1:
            return pts[0][1]
        if t <= pts[0][0]:
            (t0, p0), (t1, p1) = pts[0], pts[1]
        elif t >= pts[-1][0]:
            (t0, p0), (t1, p1) = pts[-2], pts[-1]
        else:
            k = max(j for j in range(len(pts) - 1) if pts[j][0] <= t)
            (t0, p0), (t1, p1) = pts[k], pts[k + 1]
        return p0 + (p1 - p0) * (t - t0) / (t1 - t0)
    f0, fl = plan[0], plan[-1]

    def weight(t):                                   # 第一步腳跟抬起 → 著地淡入；最後一步腳跟抬起 → 腳掌放平淡出
        return seg(t, f0["t0"] - f0["hoff"], f0["t1"]) * (1 - seg(t, fl["t0"] - fl["hoff"], fl["t1"] + fl["hon"]))
    # 著地期間（照規劃器）：腳跟著地 t1 → 下一次腳尖離地 t0；最前面站著、最後一步之後也算著地
    stance = {}
    for sd in "LR":
        iv = []; start = 0.0
        for st in plan:
            if st["side"] == sd:
                iv.append((start, st["t0"])); start = st["t1"]
        iv.append((start, 1.0)); stance[sd] = iv
    late = {sd: [(st["t0"] - st["hoff"], st["t0"]) for st in plan if st["side"] == sd] for sd in "LR"}   # 支撐期最後一段（抬腳跟）
    N = int(round(dur * sr)) + 1
    T = [i / (N - 1) for i in range(N)]
    step_len = max(st["u1"] for st in plan) / max(1, len(plan) - 1)       # 步幅＝dist／(steps−1)
    roll = min(1.0, step_len / C["step"]) ** ROLL_POW          # 腳掌滾動照步幅縮小：步幅比真人短時，整段真人腳掌滾動會讓著地那格滑 2 mm
    sole = _walk_sole(arm, rig)

    def spts(R, Hd, sd, off=Vector()):
        return [Matrix.Translation(Hd[k] + off) @ R[k].to_matrix().to_4x4() @ co for k, co in sole[sd]]
    Rb = []; roots = []; Ap = []
    for t in T:
        P = proc(t); w = weight(t)
        Rp = {k: _fk(arm, P, k).to_quaternion() @ rq[k] for k in rig.keys}
        z = P["root"][2]; up = G.u_p(t)
        rp = Vector((0.0, -up, z - w * G.bob(t)))    # 骨盆位移（路徑座標）；扣掉舊版的起伏，改用真人的
        Rm, osc = _cyc_sample(C, phase(t))
        if pt_ or pe_:                               # 站姿骨盆修正（actions_custom.posture_fix）：真人週期也一樣
            qh = Quaternion(Vector((1, 0, 0)), math.radians(-pt_)); qs = Quaternion(Vector((1, 0, 0)), math.radians(pe_ + globals().get("POSTURE_MOCAP_LEAN", 0.0)))
            Rm = dict(Rm); Rm["Hips"] = qh @ Rm["Hips"]
            for k in Rm:                             # 腰以上（世界旋轉）整體往前 pe_，繞腰椎頭轉
                if k not in ("Hips",) and "Leg" not in k and "Foot" not in k and "ToeBase" not in k:
                    Rm[k] = qs @ Rm[k]
        R = {k: _slerp(Rp[k], Rm[k], w * (roll if ("Foot" in k or "ToeBase" in k) else 1.0)) for k in rig.keys}
        if arms == "skirt":                          # 提裙：手臂用舊版（pose_frame 再用 IK 捏裙子）
            for k in rig.keys:
                if "Shoulder" in k or "Arm" in k or k.endswith("_Hand"):
                    R[k] = Rp[k]
        Rb.append(R); roots.append(rp + osc * w)
        Ap.append({k: (_fk(arm, P, k) @ rh[k]) + Vector((0.0, -up, z)) for k in ("L_Foot", "R_Foot")})
    fw = max(1, int((FOOT_SMOOTH_S_KNEE if globals().get("KNEE_FIX") else FOOT_SMOOTH_S) * sr))             # 腳掌、腳趾的世界旋轉在前後 FOOT_SMOOTH_S 秒內平均：腳跟著地後腳掌放平那一下太快，
    for k in ("L_Foot", "R_Foot", "L_ToeBase", "R_ToeBase"):   # 離地 2～5 mm 的鞋底點跟著轉，會量到 1 mm 以上的滑步
        src = [Rb[i][k] for i in range(N)]
        for i in range(N):
            q = src[i].copy(); acc = Vector((q.w, q.x, q.y, q.z)); cnt = 1
            for j in range(max(0, i - fw), min(N, i + fw + 1)):
                if j != i:
                    r_ = src[j] if src[j].dot(q) >= 0 else -src[j]
                    acc += Vector((r_.w, r_.x, r_.y, r_.z)); cnt += 1
            Rb[i][k] = Quaternion(acc / cnt).normalized()
    Hd = [rig.fk(Rb[i], roots[i]) for i in range(N)]
    pts_ = {sd: [spts(Rb[i], Hd[i], sd) for i in range(N)] for sd in "LR"}
    O = {}; STN = {}
    for sd in "LR":
        off = [None] * N; ft = f"{sd}_Foot"; rngs = []
        for (ta, tb) in stance[sd]:
            a = int(round(ta * (N - 1))); b = min(N - 1, int(round(tb * (N - 1))))
            if b < a:
                continue
            rngs.append((a, b))
            o = Ap[a][ft] - Hd[a][ft]; o.z = WALK_GAP - min(p.z for p in pts_[sd][a])
            off[a] = o
            piv = min(range(len(pts_[sd][a])), key=lambda m: pts_[sd][a][m].z) if a > 0 else None
            for i in range(a + 1, b + 1):
                prev = [p + off[i - 1] for p in pts_[sd][i - 1]]
                cz = WALK_GAP - min(p.z for p in pts_[sd][i])
                cur = [p + Vector((off[i - 1].x, off[i - 1].y, cz)) for p in pts_[sd][i]]
                if piv is not None and (T[i] - T[a]) * dur <= HEEL_PIVOT_S:
                    S = [piv]                         # 腳跟剛著地：腳跟最低點當單一支點
                else:
                    S = [m for m in range(len(cur)) if prev[m].z <= WALK_PIVOT_Z and cur[m].z <= WALK_PIVOT_Z]
                    if len(S) < 3:
                        S = sorted(range(len(cur)), key=lambda m: cur[m].z)[:3]
                dx = sum(prev[m].x - cur[m].x for m in S) / len(S); dy = sum(prev[m].y - cur[m].y for m in S) / len(S)
                off[i] = Vector((off[i - 1].x + dx, off[i - 1].y + dy, cz))
        known = [i for i in range(N) if off[i] is not None]
        for i in range(N):
            if off[i] is not None:
                continue
            a = max((k for k in known if k < i), default=None); b = min((k for k in known if k > i), default=None)
            if a is None or b is None:
                off[i] = (off[b] if a is None else off[a]).copy()
            else:
                u = (i - a) / (b - a); off[i] = off[a].lerp(off[b], u * u * (3 - 2 * u))
        inst = [any(a <= i <= b for a, b in rngs) for i in range(N)]
        STN[sd] = inst
        bset = [x for r_ in rngs for x in r_]
        fade = max(1, int(0.05 * sr)); lift = []
        for i in range(N):
            if inst[i]:
                lift.append(0.0); continue
            d = min((abs(i - x) for x in bset), default=fade)
            cl = WALK_GAP + (SWING_CLEAR - WALK_GAP) * min(1.0, d / fade)
            lift.append(max(0.0, cl - (min(p.z for p in pts_[sd][i]) + off[i].z)))
        if any(lift):
            lift = _smooth_max(lift, fade)
            for i in range(N):
                if not inst[i]:
                    off[i] = off[i] + Vector((0, 0, lift[i]))
        O[sd] = off
    # 骨盆下沉（腿構不到）—— 舊做法（KNEE_FIX 關閉時）：沿用規劃器的骨盆高度，只在腿構不到時往下沉
    L = {sd: ((rh[f"{sd}_LowerLeg"] - rh[f"{sd}_UpperLeg"]).length, (rh[f"{sd}_Foot"] - rh[f"{sd}_LowerLeg"]).length) for sd in "LR"}
    if not globals().get("KNEE_FIX"):
        need = []
        for i in range(N):
            req = 0.0
            for sd in "LR":
                v = (Hd[i][f"{sd}_Foot"] + O[sd][i]) - Hd[i][f"{sd}_UpperLeg"]; Rm_ = (L[sd][0] + L[sd][1]) * reach
                if v.length > Rm_:
                    req = max(req, (-v.z) - math.sqrt(max(Rm_ * Rm_ - v.xy.length ** 2, 0.0)))
            need.append(max(0.0, req))
        drop = _smooth_max(need, max(1, int(0.15 * sr))) if any(need) else [0.0] * N
        roots = [r - Vector((0, 0, d)) for r, d in zip(roots, drop)]
    else:
        # 骨盆高度（2026-10-08 改）：每一格取「兩腳都構得到」的最高位置。支撐腳的腿最多伸到 KNEE_R_STAND（站著，膝蓋約 175°）～
        # KNEE_R_WALK（走路中，約 170°），擺盪腳 KNEE_R_SWING；上限是 rest 站直的高度。前後 0.15 秒取最低再平均（平滑、一定構得到）。
        # 舊版沿用規劃器的骨盆下沉（腿只伸到 97.5%＝膝蓋彎 26°，站定也一樣）：使用者說「新郎姿勢很像半蹲進場」「站定位後腳也不打直」
        L = {sd: ((rh[f"{sd}_LowerLeg"] - rh[f"{sd}_UpperLeg"]).length, (rh[f"{sd}_Foot"] - rh[f"{sd}_LowerLeg"]).length) for sd in "LR"}
        # 每隻腳參與的權重 cw（0～1）：支撐期＝1、擺盪期與抬腳跟那段＝0，前後 KNEE_FADE_S 秒平均（換腳那一格不會突然換人壓骨盆）
        cw = {}
        for sd in "LR":
            raw = [1.0 if (STN[sd][i] and not (any(a_ <= T[i] <= b_ for a_, b_ in late[sd]) and weight(T[i]) > 0.05)) else 0.0
                   for i in range(N)]
            cw[sd] = _gauss(raw, KNEE_FADE_S * sr / 4.0)            # 高斯淡入淡出（直線坡度的轉折會變成速度突變）
        dz = []
        for i in range(N):
            w = weight(T[i]); cap = -roots[i].z; best = cap               # 不高過 rest（root z ≤ 0）
            for sd in "LR":
                c_ = cw[sd][i]
                if c_ <= 1e-6:
                    continue
                r_ = KNEE_R_STAND * (1 - w) + KNEE_R_WALK * w
                Rr = (L[sd][0] + L[sd][1]) * r_
                hip = Hd[i][f"{sd}_UpperLeg"]; W_ = Hd[i][f"{sd}_Foot"] + O[sd][i]
                h2 = Rr * Rr - (W_ - hip).xy.length ** 2
                best = min(best, c_ * ((W_.z + math.sqrt(max(h2, 0.0))) - hip.z) + (1 - c_) * cap)
            dz.append(best)
        # 低通：先取前後 win 格的最低值，再用支撐寬度不超過 win 的高斯平滑 → 結果一定不高於每一格的上限（腿構得到），
        # 而且曲線平滑、上下加速度有限（舊做法「取最低再平均」是一段段折線，換腳那幾格大腿、小腿的速度突變 7～10）
        win = max(1, int(KNEE_LOWPASS_S * sr))
        mn = [min(dz[max(0, i - win):i + win + 1]) for i in range(N)]
        dzs = _gauss(mn, win / 2.5, radius=win)
        roots = [r + Vector((0, 0, d)) for r, d in zip(roots, dzs)]
        # 後腳跟自動抬起：抬腳跟那段腿構不到時，繞腳掌最低點把腳跟往上抬到構得到（最多 HEEL_RISE_MAX），角度時間上平滑
        Hd2 = [rig.fk(Rb[i], roots[i]) for i in range(N)]
        for sd in "LR":
            ft = f"{sd}_Foot"; Rr = (L[sd][0] + L[sd][1]) * KNEE_R_PUSH; th = [0.0] * N; piv = [None] * N
            for i in range(N):
                if not any(a_ <= T[i] <= b_ for a_, b_ in late[sd]):
                    continue
                hip = Hd2[i][f"{sd}_UpperLeg"]; W_ = Hd[i][ft] + O[sd][i]
                if (W_ - hip).length <= Rr:
                    continue
                pv = Hd[i][f"{sd}_ToeBase"] + O[sd][i]           # 支點＝腳趾關節：腳趾（朝向不變）留在地上不滑，腳掌、腳跟抬起
                ax = (Rb[i][ft] @ rq[ft].inverted()) @ Vector((1, 0, 0))
                lo, hi = 0.0, math.radians(HEEL_RISE_MAX)
                for sgn in (1, -1):                          # 哪個方向是腳跟往上
                    q = Quaternion(ax, sgn * math.radians(5))
                    if (pv + q @ (W_ - pv)).z > W_.z:
                        break
                for _ in range(24):
                    m = 0.5 * (lo + hi); q = Quaternion(ax, sgn * m)
                    if (pv + q @ (W_ - pv) - hip).length > Rr:
                        lo = m
                    else:
                        hi = m
                th[i] = sgn * hi; piv[i] = (pv, ax)
            mag = _smooth_max([abs(x) for x in th], max(1, int(0.05 * sr)))
            for i in range(N):
                if mag[i] < 1e-6:
                    continue
                j = i if piv[i] else min((k for k in range(N) if piv[k]), key=lambda k: abs(k - i))
                pv, ax = piv[j]; sgn_ = 1 if th[j] >= 0 else -1
                if piv[i] is None:                           # 平滑後延伸出來的格：支點用這一格自己的腳趾關節
                    pv = Hd[i][f"{sd}_ToeBase"] + O[sd][i]
                    ax = (Rb[i][ft] @ rq[ft].inverted()) @ Vector((1, 0, 0))
                q = Quaternion(ax, sgn_ * mag[i]); W_ = Hd[i][ft] + O[sd][i]
                Wn = pv + q @ (W_ - pv)
                O[sd][i] = O[sd][i] + (Wn - W_)
                Rb[i][ft] = q @ Rb[i][ft]
    # 腿 IK ＋ 腳趾
    R_out = []; toe = {"L": [], "R": []}
    for i in range(N):
        R = dict(Rb[i]); Hn = rig.fk(R, roots[i])
        for sd in "LR":
            ul, ll, ft = f"{sd}_UpperLeg", f"{sd}_LowerLeg", f"{sd}_Foot"
            L1, L2 = L[sd]; S = Hn[ul]; W = Hd[i][ft] + O[sd][i]; kfk = Hd[i][ll] + O[sd][i]
            v = W - S; d = max(1e-4, min(v.length, (L1 + L2) * 0.9999)); dr = v.normalized()
            al = math.acos(max(-1.0, min(1.0, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d))))
            pp = (kfk - S) + Vector((0, -KNEE_FWD, 0))     # 膝蓋方向：真人膝蓋＋固定往前一點（腿快打直時真人膝蓋幾乎在髖—踝連線上，方向不穩，大腿會一格扭轉 20°）
            pp = pp - dr * pp.dot(dr)
            if pp.length < 1e-6:
                pp = Vector((0, -1, 0))
            pp.normalize(); E = S + dr * math.cos(al) * L1 + pp * math.sin(al) * L1
            cur = (R[ul] @ rq[ul].inverted()) @ (rh[ll] - rh[ul]); R[ul] = _qbetween(cur, E - S) @ R[ul]
            cur = (R[ll] @ rq[ll].inverted()) @ (rh[ft] - rh[ll]); R[ll] = _qbetween(cur, (S + dr * d) - E) @ R[ll]
            toe[sd].append(_toe_fix(rig, R, sd, roots[i], sole, spts, O[sd][i] + Hd[i][ft] - rig.fk(R, roots[i])[ft]))
        R_out.append(R)
    wv = max(1, int(0.06 * sr))
    for sd in "LR":
        mag = _smooth_max([abs(x) for x in toe[sd]], wv); sg = 1 if sum(toe[sd]) >= 0 else -1
        for i in range(N):
            R = R_out[i]; ax = (R[f"{sd}_Foot"] @ rq[f"{sd}_Foot"].inverted()) @ Vector((1, 0, 0))
            R[f"{sd}_ToeBase"] = Quaternion(ax, sg * mag[i]) @ R[f"{sd}_ToeBase"]
    r = math.radians(rz); c, sn = math.cos(r), math.sin(r)

    def world_root(v):
        return (origin[0] + c * v.x - sn * v.y, origin[1] + sn * v.x + c * v.y, v.z)

    def fn(t):
        x = max(0.0, min(1.0, t)) * (N - 1); i = min(int(x), N - 2); f = x - i
        R = {k: _slerp(R_out[i][k], R_out[i + 1][k], f) for k in rig.keys}
        P0 = proc(t)
        out = rig.to_dict(R)
        out.update(hands=P0["hands"], root=world_root(roots[i].lerp(roots[i + 1], f)), rz=rz, ground=False, face=P0["face"])
        if "ik" in P0:
            out["ik"] = P0["ik"]
        return out

    fn.gait = G; fn.dur = dur; fn.pos = proc.pos; fn.landings = proc.landings; fn.style = "mocap"
    fn.proc = proc; fn.weight = weight; fn.cycle_info = C["info"]; fn.roll = roll
    return fn
