# 新郎米色三件式（2026-10-12 使用者給參考照、確認「這樣可以」定案）
# 白襯衫＋尖角翻領、敞開的米色外套＋同色領片＋胸袋與袋蓋、米色 V 領背心＋4 顆深咖啡扣子、米色西裝褲、
# 焦糖棕綁帶皮鞋、海軍藍領結。參考照分析見 refs/analysis.md。
import garment_lib as G

A = G.A
BREAK_Z = 0.86            # 外套領片翻折結束的高度（兩片前襟在這裡最靠近）
VEST_V_BOTTOM = 0.95      # 背心 V 領最低點
VEST_HEM = A["HEM"] + 0.025
JK_TOP = A["COLLAR_TOP"] - 0.035     # 外套領口：露出 3.5 cm 白領子

M = dict(
    wool=G.material("Suit_Wool", (203, 184, 163), 0.82, sheen=0.25),      # 米色（參考照的卡其米）
    lapel=G.material("Suit_Lapel", (212, 194, 174), 0.78, sheen=0.3),      # 領片同布料、亮一階，翻折才看得出來
    shirt=G.material("Suit_Shirt", (246, 244, 240), 0.7, sheen=0.15),
    tie=G.material("Suit_BowTie", (38, 62, 108), 0.45, sheen=0.5),         # 海軍藍
    shoe=G.material("Suit_Shoe", (150, 84, 48), 0.36, coat=0.35),          # 焦糖棕
    lace=G.material("Suit_ShoeLace", (110, 60, 34), 0.6),
    button=G.material("Suit_Button", (82, 60, 44), 0.35, coat=0.4),        # 深咖啡（參考照看不清，自己補的）
)


def build():
    # 襯衫只做會露出來的部分：領口到背心 V 領底、袖口
    shirt = G.shirt("Suit_Shirt", M["shirt"],
                    show=lambda c: (c.z > VEST_V_BOTTOM - 0.04 and abs(c.x) < 0.10) or abs(c.x) > A["SLEEVE_X"] - 0.03)
    vest = G.vest_front("Suit_Vest", M["wool"], top=JK_TOP - 0.01, v_bottom=VEST_V_BOTTOM, hem=VEST_HEM)
    jacket = G.jacket("Suit_Jacket", M["wool"], M["lapel"], top=JK_TOP, break_z=BREAK_Z,
                      open_pts=[(JK_TOP, 0.075), (BREAK_Z, 0.012), (0.72, 0.040), (A["HEM"], 0.070)],   # 敞開：翻折點下面往下襬分開
                      lapel_pts=[(JK_TOP, 0.120), (BREAK_Z, 0.012)])
    pants = G.trousers("Suit_Pants", M["wool"])
    shoes = G.shoes("Suit_Shoes", M["shoe"])
    top, bot = VEST_V_BOTTOM - 0.025, VEST_HEM + 0.05
    return [
        shirt, vest, jacket, pants, shoes,
        G.bowtie("Suit_BowTie", M["tie"], shirt),
        G.collar_tips("Suit_CollarTips", M["shirt"], shirt),
        G.buttons("Suit_Buttons", M["button"], vest, [top + (bot - top) * i / 3 for i in range(4)]),
        G.patches("Suit_Pockets", M["wool"], jacket, [(0.095, 0.665, (0.046, 0.004, 0.016)), (-0.095, 0.665, (0.046, 0.004, 0.016)),
                                                     (0.085, 0.975, (0.034, 0.003, 0.007))]),
        G.laces("Suit_ShoeLaces", M["lace"], shoes),
    ]
