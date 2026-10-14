# ⑧ 拱門下揮手（幕內 6.0～9.5 秒的 3D 段；播放器 0 秒＝幕內 6.0 秒）。2026-10-10 Mixamo 版第 1 關（骨骼）。
# 站位、鏡頭照現行 v2_08（shots_v2_s0308.py 的 S08）：新郎 (−0.42, ARCH_Y=0.30) 面向 +8°（微微朝新娘）、新娘 (0.40, 0.30) −8°；
# 鏡頭 6.0～6.9 從 (0, −8.4, 1.05) 推到 (0, −7.15, 0.95)（ease-out），看 (0, 0.30, 1.15)、58 mm；角色 6.4 秒才淡入（合成做）。
# 動作：新郎右手揮手＝Mixamo「Waving」（0.53 秒一個來回，重複播）；
#       新娘頭頂比愛心＝Mixamo 沒有：身體用「Female Idle」，手臂用 IK 調成愛心（heart_mod；2026-10-10 第 1 輪回饋後）。
import math
import bpy
from mathutils import Quaternion
ARCH_Y = 0.30


T_IN = 0.0                 # 手從身體兩側舉到頭頂的秒數。2026-10-11 第 3 關回饋「比愛心之前雙手先做了一個倒三角」→ 改 0：第 0 格就比好愛心


def _crown_offset(who):
    """rest 時頭頂（頭髮、臉在中線附近的最高點）相對頭骨頭部的位移，骨架空間（同動作庫 actions_custom._crown 的做法）"""
    arm = bpy.data.objects[who + "_Armature"]; best = None
    for nm in (f"{who}_Hair", f"{who}_Face"):
        o = bpy.data.objects.get(nm)
        if o is None or o.type != "MESH":
            continue
        M = arm.matrix_world.inverted() @ o.matrix_world
        for v in o.data.vertices:
            p = M @ v.co
            if abs(p.x) < 0.03 and (best is None or p.z > best.z):
                best = p.copy()
    return best - arm.data.bones["J_Bip_C_Head"].head_local


def heart_mod():
    """頭頂愛心（照動作庫 heart_head 的規格）：兩手指尖在頭頂最高點正上方相碰（各留 4 mm），手往中線、往下斜 0.25，
    手肘往兩側外張；肩胛跟著抬 15°。目標每格跟著頭走，所以身體晃，愛心也跟著晃。指尖實際位置和目標的差再修兩次（手指本來就彎著）"""
    B = tgt("bride")
    off = _crown_offset("bride")
    up = Vector((0, 0, 1))
    HN = "J_Bip_C_Head"

    def solve(R, h, s_, wrist, hand_dir, w):
        R = arm_ik(B, R, h, s_, wrist, LEFT[0] * SG[s_] + FWD[0] * 0.3)
        H2 = B.fk(R, h)
        cur = (H2[f"J_Bip_{s_}_Middle1"] - H2[f"J_Bip_{s_}_Hand"]).normalized()
        return aim_hand(B, R, h, s_, cur.lerp(hand_dir, w), palm=Vector((0, 0, -1)), palm_w=w)

    SG = {"L": 1.0, "R": -1.0}; LEFT = [None]; FWD = [None]

    def mod(t, R, h):
        w = 1.0 if T_IN <= 0 else max(0.0, min(1.0, t / T_IN)); w = w * w * (3 - 2 * w)
        if w <= 0:
            return R
        Hd = B.fk(R, h)
        left = Hd["J_Bip_L_UpperLeg"] - Hd["J_Bip_R_UpperLeg"]; left.z = 0; left.normalize()
        fwd = Vector((left.y, -left.x, 0)); LEFT[0] = left; FWD[0] = fwd
        crown = Hd[HN] + (R[HN] @ B.rest_q[HN].inverted()) @ off
        C = Vector((crown.x, crown.y, crown.z)) + fwd * 0.02                # 指尖相碰的點：頭頂最高點、稍微往前
        lh = (B.rest_t["J_Bip_L_Middle3"] - B.rest_h["J_Bip_L_Hand"]).length
        for s_ in ("L", "R"):
            sg = SG[s_]
            R = lift_shoulder(B, R, s_, 15.0 * w)
            hand_dir = (left * (-sg) + up * (-0.25)).normalized()
            tip_goal = C + left * (sg * 0.004)
            start = B.fk(R, h)[f"J_Bip_{s_}_Hand"]
            arc = math.sin(math.pi * w)
            goal = tip_goal - hand_dir * lh
            R0 = R
            for _ in range(3):                                                 # 指尖對不準就把手腕目標挪過去再解一次
                wrist = start.lerp(goal, w) + left * (sg * 0.22 * arc) + fwd * (0.10 * arc)
                R = solve(R0, h, s_, wrist, hand_dir, w)
                H2 = B.fk(R, h)
                tip = B.tail(R, H2, f"J_Bip_{s_}_Middle3")
                goal = goal + (tip_goal - tip)
        return R
    return mod


CAM8 = Vector((0.0, -7.15, 1.0))         # 推近之後的鏡頭（6.9 秒起）


def wave_mod():
    """新郎揮手（2026-10-11 第 3 關第 2 輪回饋「新郎揮手動作方向不搭」：Mixamo「Waving」的手在臉旁往內擺，擺到額頭前面像敬禮，
    掌心也沒朝鏡頭）→ 右手舉在頭的外側：手肘在肩膀外 12 cm、低 12 cm，前臂往上；整隻前臂繞手肘左右擺 ±18°（0.8 秒一個來回），
    擺動的面正對鏡頭、掌心朝鏡頭、手指併攏微彎；頭和眼睛看鏡頭。左手、身體照原片"""
    G = tgt("groom"); up = Vector((0, 0, 1))

    def mod(t, R, h):
        Hd = G.fk(R, h)
        S_ = Hd["J_Bip_R_UpperArm"]
        fwd = CAM8 - S_; fwd.z = 0; fwd.normalize()
        rgt = fwd.cross(up).normalized()                                       # 面向鏡頭時他的右手邊
        lift = min(1.0, t / 0.35); lift = lift * lift * (3 - 2 * lift)          # 開頭 0.35 秒從原片的手接過來（角色 0.4 秒才淡入）
        E = S_ + rgt * 0.12 - up * 0.12 + fwd * 0.06
        fl = (G.rest_h["J_Bip_R_Hand"] - G.rest_h["J_Bip_R_LowerArm"]).length
        a = math.radians(18.0) * math.sin(2 * math.pi * t / 0.8)
        fa = (Quaternion(fwd, -a) @ (up * 0.98 + rgt * 0.02 + fwd * 0.08)).normalized()   # 繞「朝鏡頭的軸」轉：在正對鏡頭的面上、以直立為中心左右擺
        wrist = E + fa * fl
        cur = Hd["J_Bip_R_Hand"]
        R = arm_ik(G, R, h, "R", cur.lerp(wrist, lift), rgt * 0.7 - up * 0.6 - fwd * 0.2)
        flap = Quaternion(fwd, -0.35 * a)                                         # 手掌比前臂慢一點點跟著擺（像真的在揮）
        R = aim_hand(G, R, h, "R", (flap @ fa).normalized(), palm=fwd, palm_w=lift)
        R = gesture(G, R, "R", "relaxed", w=lift)
        R = look_at(G, R, h, CAM8, split=(0.0, 0.3, 0.7))
        return R
    return mod


def bride_look():
    B = tgt("bride")

    def mod(t, R, h):
        return look_at(B, R, h, CAM8, split=(0.0, 0.0, 1.0))                   # 只轉脖子（手比愛心接在上胸，轉腰會把愛心帶歪）
    return mod


def scene():
    groom = dict(segs=[
        S("groom", "waving_one_hand", loops=7.0, label="右手揮手（Waving，0.53 秒一個來回、重複播）"),
    ], anchor=(0.0, (-0.42, ARCH_Y), 8.0), mod=wave_mod() if OPT.get("FINAL") == "1" else None)
    # 2026-10-10 第 1 輪回饋「新娘要比愛心，這裡停頓很奇怪」→ 使用者選「站立待機＋我調手臂」：
    #   身體用 Mixamo「Female Idle」（自然的呼吸、重心晃動），手臂用 IK 調成頭頂愛心（mod），跟著身體微微動，不會整個停住
    bride = dict(segs=[
        S("bride", "female_idle", 0.0, 4.0, mod=heart_mod(), label="頭頂比愛心（身體：Female Idle；手臂：我調的愛心）"),
    ], anchor=(0.0, (0.40, ARCH_Y), -8.0), mod=bride_look() if OPT.get("FINAL") == "1" else None)
    cam = dict(pos=[0.0, -7.15, 0.95], aim=[0.0, ARCH_Y, 1.15], lens=58.0, sensor=36.0, aspect=16 / 9)
    return dict(id="08", title="⑧ 拱門下揮手（幕內 6.0～9.5 秒）", dur=3.5, chars=dict(groom=groom, bride=bride),
                props=garden_props(), cam=cam, skirt=dict(who="bride", r_floor=0.70, r_waist=0.16, h_waist=0.98),
                note="播放器的 0 秒＝這一幕的 6.0 秒（3D 段 6.0～9.5）。角色 6.4 秒才淡入，所以開頭 0.4 秒在影片裡看不到。"
                     "「影片鏡頭」是推近之後（6.9 秒起）的位置。",
                decide=DECIDE_FINAL if OPT.get("FINAL") == "1" else ["新郎的揮手換成 Mixamo「Waving」：手在臉旁、比肩略高（1.5 m），0.53 秒一個來回。手腕左右只移動約 7 cm，主要是手掌在擺；你第 3 輪要的是整隻手水平擺 26 cm。要照原片，還是第 2 關把擺幅加大？",
                        "新娘頭頂比愛心（照你第 1 輪的回饋改）：Mixamo 沒有比愛心的動畫，所以身體用「Female Idle」的自然呼吸、晃動，手臂是我調的——指尖在頭頂正上方相碰、手肘往兩側外張，跟著身體一起微微動，不會整個停住。"
                        "0～0.7 秒手從身體兩側舉上去（0.4 秒才淡入，大半看不到）；之後指尖在頭頂相碰（兩手各留 4 mm）。手指的彎法第 2 關再細修。",
                        "Female Idle 本身晃得很小（骨盆 3 秒只動約 1 cm），愛心跟著身體動的幅度也很小。如果看起來還是像停住，可以換成晃動比較明顯的「Happy Idle」（要再下載，會先問你）。",
                        "新郎揮手的手離拱門左柱約 28 cm（手在 x −0.67，柱在 −0.95），不會掃到柱子；柱上垂下的花葉第 2 關再看。"])


DECIDE_FINAL = [
    "【第 2 關的微調，灰線是 Mixamo 原樣】新娘頭頂比愛心：身體照 Female Idle，手臂用 IK 舉到頭頂、指尖相碰（兩手各留 4 mm）、手肘往兩側外張、肩胛抬 15°。第 3 關回饋「比愛心之前雙手先做了一個倒三角」後改成第 0 秒就已經比好（不再有舉上去的過程）。灰線是 Female Idle 原本雙手垂下的樣子。",
    "新郎揮手（第 3 關第 2 輪回饋「揮手動作方向不搭」）：原片的手在臉旁往內擺、擺到額頭前像敬禮 → 右手舉在頭的外側（手肘在肩膀外 12 cm），"
    "前臂繞手肘左右擺 ±18°、0.8 秒一個來回，擺動的面正對鏡頭、掌心朝鏡頭。灰線是 Mixamo 原樣。",
    "眼神（第 2 輪回饋「眼神要面對鏡頭」）：兩人的頭轉向鏡頭（新娘只轉脖子，愛心不歪），眼珠也看鏡頭。",
]
