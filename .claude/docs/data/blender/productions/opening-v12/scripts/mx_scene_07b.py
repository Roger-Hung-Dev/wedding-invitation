# ⑦b 喝酒不開車（9 秒）。2026-10-11 第 3 關第 3 輪回饋：⑦ 拆成兩幕的第二幕——「新郎喝醉臉紅走路不穩，接著搭上計程車離開」。
#   使用者選：⑦b 9 秒、晚上的餐廳門口、計程車我用幾何自己做（右後門能開、輪子會轉）；下載 Drunk Walk、Drunk Idle Variation（打嗝）、
#   Entering Car（原片是從駕駛座那側上車，左右鏡射成從右後門上車：台灣靠右行駛，乘客從靠人行道那側上車）。
# 場景（mx_preview 07b、set_v3）：馬路沿 X，人行道在 y 0～3.2（人行道面＝z 0，馬路低 12 cm），餐廳門面在 y 3.2、門在 x 1.4；
#   計程車停在路邊、車頭朝 −X（靠右停，右側貼著路緣），右後門在 x 0.10～1.00。
# 動作（都是 Mixamo 原樣，只選段、接段、站位）：0～2.55 秒從餐廳門口醉醺醺走到車門前（Drunk Walk 0.85 圈）→ 打一個嗝（Hiccup 0.2～1.4 秒）→
#   上車（Entering Car 鏡射 0～4.45 秒：摸門把、拉開門、低頭鑽進去、坐下、關門）→ 7.7 秒起計程車開走（mx_preview：新郎跟著車移動）。
import math
from mathutils import Quaternion
FINAL = OPT.get("FINAL") == "1"
CAR_SIDE_Y = -0.05                        # 計程車右側車身（靠人行道那側）的 y
SEAT_IN = 0.80                            # Entering Car 原片坐好時骨盆在車身側面往內 0.80 m（起點往前 1.88 m 坐下、1.0 秒摸到 1.08 m 處的門把）
ENTER_XY = (0.55, CAR_SIDE_Y - SEAT_IN + 1.88)   # 上車這段開始時骨盆的位置（往 −y 走進車裡）
T_DRIVE = 7.7                              # 計程車開走


# ════════ 第 2 關的微調（FINAL=1）：換成真實車款 Camry（2026-10-11 使用者從 3D Warehouse 選的 LINE TAXI Camry）════════
# Entering Car 原片是照高車頂的車做的：坐好時骨盆離地 0.84、鑽進門時頭頂 1.30～1.45、車內地板 0.20。
# Camry（set_v3_street 量的，離人行道）：後座座墊 0.33、車頂內側 1.15～1.25、門框上緣約 1.18、地板 0.12 →
#   坐下時骨盆往下 0.39（座墊＋臀部厚 0.12）；鑽進門時上身多往前彎；兩腳用 IK 固定在原片的位置（車內的腳降到 Camry 的地板）
SIT_DROP = 0.39
T_DROP = (5.25, 6.35)                     # 骨盆從開始轉身跨進去到坐好，慢慢往下
T_DUCK = (5.2, 5.6, 5.95, 6.4)            # 鑽進門框時多彎腰
DUCK_DEG = 22.0
FLOOR_IN = 0.20                           # 車內腳踝高（地板 0.12＋腳踝 0.08）；原片車內腳踝約 0.28
CAR_IN_Y = -0.10                          # 腳的 y 小於這個＝在車裡


def leg_ik(T_, R, h, side, target):
    """兩節腿 IK：大腿、小腿轉到腳踝到 target，膝蓋彎的方向沿用現在的（不翻面）；腳掌、腳趾的世界轉向保留原樣"""
    U, L, F = f"J_Bip_{side}_UpperLeg", f"J_Bip_{side}_LowerLeg", f"J_Bip_{side}_Foot"
    keep = {n: R[n] for n in (F, f"J_Bip_{side}_ToeBase") if n in R}
    Hd = T_.fk(R, h)
    A, K0, F0 = Hd[U], Hd[L], Hd[F]
    l1 = (T_.rest_h[L] - T_.rest_h[U]).length; l2 = (T_.rest_h[F] - T_.rest_h[L]).length
    d_ = target - A; dist = max(1e-4, min(d_.length, l1 + l2 - 1e-4)); u = d_.normalized()
    a = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist); hgt = math.sqrt(max(0.0, l1 * l1 - a * a))
    v = (K0 - A) - u * (K0 - A).dot(u)
    if v.length < 1e-6:
        v = Vector((0, 0, 1)).cross(u)
    v.normalize()
    K = A + u * a + v * hgt
    R = rotate_subtree(T_, R, U, (K0 - A).rotation_difference(K - A))
    Hd = T_.fk(R, h)
    R = rotate_subtree(T_, R, L, (Hd[F] - Hd[L]).rotation_difference(A + u * dist - Hd[L]))
    R = dict(R); R.update(keep)
    return R


def groom_mod():
    G = tgt("groom")

    def sm_(x):
        x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

    def mod(t, R, h):
        drop = SIT_DROP * sm_((t - T_DROP[0]) / (T_DROP[1] - T_DROP[0]))
        duck = win_(t, *T_DUCK)
        if drop <= 1e-4 and duck <= 1e-4:
            return R
        Hd0 = G.fk(R, h)
        feet = {s_: Hd0[f"J_Bip_{s_}_Foot"].copy() for s_ in "LR"}
        h.z -= drop                                            # h 是骨盆位置（Vector），直接改（build 拿同一個物件算 fk）
        if duck > 0:
            lft = Hd0["J_Bip_L_UpperLeg"] - Hd0["J_Bip_R_UpperLeg"]; lft.z = 0; lft.normalize()
            R = rotate_subtree(G, R, "J_Bip_C_Spine", Quaternion(lft, math.radians(DUCK_DEG * duck)))   # 繞身體左右軸往前彎
        for s_ in "LR":
            p = feet[s_]
            inside = sm_((CAR_IN_Y - p.y) / 0.15)              # 腳在車裡（y 越小越裡面）
            z = p.z + (min(p.z, FLOOR_IN) - p.z) * inside
            R = leg_ik(G, R, h, s_, Vector((p.x, p.y, z)))
        return R
    return mod


def win_(t, a, b, c, d):
    if t <= a or t >= d:
        return 0.0
    x = (t - a) / max(1e-6, b - a) if t < b else (1.0 if t <= c else 1.0 - (t - c) / max(1e-6, d - c))
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def scene():
    groom = dict(segs=[
        S("groom", "drunk_walk", 0, None, loops=0.85, label="醉醺醺走出來（Drunk Walk）"),
        S("groom", "drunk_hiccup", 0.2, 1.4, label="停下來打嗝（Drunk Idle Variation Hiccup）"),
        S("groom", "entering_car", 0.0, 4.45, mirror=True, label="開門坐進計程車、關門（Entering Car，鏡射成右後門）"),
    ], anchor=("end:1", ENTER_XY, 0.0), mod=groom_mod() if FINAL else None)
    x0, y0 = ENTER_XY
    props = [
        dict(kind="box", name="人行道（面＝z 0）", min=[-6.0, 0.0, -0.12], max=[6.0, 3.2, 0.0], color="#B9B2A8", opacity=0.5),
        dict(kind="box", name="餐廳門面", min=[-6.0, 3.2, 0.0], max=[6.0, 3.5, 3.2], color="#8C6A52", opacity=0.35),
        dict(kind="box", name="計程車（車頭朝 −X）", min=[-2.2, CAR_SIDE_Y - 1.95, -0.12], max=[2.2, CAR_SIDE_Y, 1.66], color="#F2C230", opacity=0.35),
    ]
    cam = dict(pos=[-3.6, 3.0, 1.55], aim=[0.9, 0.6, 0.95], lens=30.0, sensor=36.0, aspect=16 / 9)
    return dict(id="07b", title="⑦b 喝酒不開車", dur=9.0, chars=dict(groom=groom), props=props, cam=cam, skirt=None,
                note="新郎一個人：從餐廳門口醉醺醺走到計程車旁、打嗝、開右後門坐進去關門，計程車開走。動作是 Mixamo 原樣。",
                decide=DECIDE)


DECIDE = [
    "【⑦ 拆成兩幕的第二幕，9 秒】晚上的餐廳門口。新郎從門口醉醺醺走到計程車旁（Mixamo「Drunk Walk」，身體左右晃、腳步歪）→ 停下來打一個嗝 →"
    "開右後門坐進去、關門（Mixamo「Entering Car」左右鏡射：原片是從駕駛座上車，改成從靠人行道的右後門上車）→ 7.7 秒計程車開走。",
    "計程車是我用幾何做的卡通黃色計程車（車頂 TAXI 燈），車門、座位的位置照新郎實際摸門把、坐下的位置做。新郎臉頰畫上醉紅。",
]
