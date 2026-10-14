# 新郎深藍灰西裝（2026-10-11 第一版，使用者後來改選米色三件式 groom-beige-3piece；留著當另一款）
# 白色立領襯衫、深藍灰外套＋深色緞面 V 領片＋兩顆黑扣子、深藍灰西裝褲、黑皮鞋、黑領結。
import garment_lib as G

A = G.A
V_BOTTOM = 0.83           # V 領最低點（第一顆扣子上方）
JK_TOP = A["COLLAR_TOP"] - 0.035
LAPEL_W = 0.035

M = dict(
    wool=G.material("Suit_Wool", (52, 60, 78), 0.82, sheen=0.25),         # 深藍灰，不用純黑
    satin=G.material("Suit_Satin", (34, 38, 50), 0.45, sheen=0.4),         # 領片：比本體深一點、帶柔光
    shirt=G.material("Suit_Shirt", (246, 242, 234), 0.7, sheen=0.15),
    tie=G.material("Suit_BowTie", (22, 22, 26), 0.42, sheen=0.5),
    shoe=G.material("Suit_Shoe", (20, 20, 22), 0.35, coat=0.35),
    button=G.material("Suit_Button", (28, 28, 32), 0.3, coat=0.5),
)


def build():
    v_top_half = 0.075 + 0.004
    shirt = G.shirt("Suit_Shirt", M["shirt"],
                    show=lambda c: (c.z > V_BOTTOM - 0.06 and abs(c.x) < 0.10) or abs(c.x) > A["SLEEVE_X"] - 0.03)
    jacket = G.jacket("Suit_Jacket", M["wool"], M["satin"], top=JK_TOP, break_z=V_BOTTOM - 0.06,
                      # 只開 V 領，下面扣起來：折線最後一點的半寬會一路延用到下襬，所以要收成 0，不然整條前襟都被挖開
                      open_pts=[(JK_TOP, v_top_half), (V_BOTTOM, 0.004), (V_BOTTOM - 0.002, 0.0)],
                      lapel_pts=[(JK_TOP, min(v_top_half + LAPEL_W, 0.14)), (V_BOTTOM, 0.004 + LAPEL_W), (V_BOTTOM - 0.06, 0.004 + LAPEL_W)])
    return [
        shirt, jacket,
        G.trousers("Suit_Pants", M["wool"]),
        G.shoes("Suit_Shoes", M["shoe"]),
        G.bowtie("Suit_BowTie", M["tie"], shirt, wing=(0.030, 0.011, 0.022)),
        G.buttons("Suit_Buttons", M["button"], jacket, [V_BOTTOM - 0.025, V_BOTTOM - 0.085], size=(0.009, 0.004, 0.009)),
    ]
