# 新娘淡粉平口蓬裙禮服（2026-10-12 使用者給兩張參考照：正面、側面）
# 平口上身＋花瓣摺紗上緣、腰帶＋布花＋背後大蝴蝶結、到膝上的波浪外層紗、落地蓬蓬紗裙、淡粉休閒鞋（照片裙底露出的白粉色球鞋）、銀色花形耳環（2026-10-12 使用者要求補上蝴蝶結與耳環）。
# 參考照分析見 refs/analysis.md。新娘身體還沒出廠：第一版在新郎身體上試版型。
import garment_lib as G
from mathutils import Vector

A = G.A
TOP = A["ARMPIT"] - 0.012                                   # 平口上緣：腋下 1.2 cm
WAIST = A["HIP_Z"] + 0.38 * (A["ARMPIT"] - A["HIP_Z"])      # 腰線（腰帶中心）：髖關節到腋下的 38%
SKIRT_HEM = A["ANKLE_Z"] + 0.012                            # 落地裙：只露鞋尖，走路時不拖地穿地板
SKIRT_R = 0.32                                              # 裙擺半徑：照片更蓬，但挽手臂、並肩走會撞到新郎，先收
OVER_HEM = A["HIP_Z"] - 0.26                     # 外層紗垂到膝上（照片兩側垂得更長）

M = dict(
    satin=G.material("Gown_Satin", (240, 192, 194), 0.6, sheen=0.45),     # 上身與外層紗（照片的淡粉，略帶光澤）
    tulle=G.material("Gown_Tulle", (246, 206, 206), 0.75, sheen=0.6),     # 裙子的紗，比上身淺一階
    sash=G.material("Gown_Sash", (236, 184, 188), 0.55, sheen=0.5),
    shoe=G.material("Gown_Shoe", (244, 222, 218), 0.6),
    silver=G.material("Gown_Silver", (214, 214, 220), 0.28, metallic=1.0),     # 照片的銀色花形耳環
)

# 這套特有的近照：背後蝴蝶結、耳環
EXTRA_CLOSEUPS = [
    ("bow", lambda A, g: Vector((0, 0.05, WAIST - 0.06)), 0.9, (180, 135, -135)),
    ("earring", lambda A, g: g("J_Bip_C_Head") + Vector((0, 0, 0.02)), 0.5, (90, -90, 45)),
]


def covered(c):
    """平口：上緣以下整個藏（腿在蓬裙裡看不到，藏起來走路時才不會從裙子戳出來）；手臂、肩膀、脖子露出"""
    return c.z < TOP - 0.012


def build():
    bodice = G.strapless_bodice("Gown_Bodice", M["satin"], top=TOP, hem=WAIST - 0.04)
    skirt = G.lathe_skirt("Gown_Skirt", M["tulle"], WAIST - 0.01, SKIRT_HEM, SKIRT_R, bell=2.2, waist_ease=0.010,
                          lobes=11, lobe_amp=0.012)             # 下襬小波浪，紗才不像硬筒
    over = G.lathe_skirt("Gown_Overskirt", M["satin"], WAIST, OVER_HEM, 0.285, bell=3.0, waist_ease=0.018,
                         lobes=3, lobe_amp=0.03, lobe_lift=0.16, leg_share=0.4)    # 3 片大垂片＝照片兩側往下垂的大摺
    sash = G.sash("Gown_Sash", M["sash"], WAIST, width=0.032, ease=0.024)
    return [
        bodice, skirt, over, sash,
        G.petal_neckline("Gown_Neckline", M["satin"], bodice, z=TOP, lobes=5, height=0.05, flare=0.03),
        G.rosette("Gown_Rose", M["sash"], sash, x=0.035, z=WAIST, size=0.045),
        G.shoes("Gown_Shoes", M["shoe"], toe=0.010),
        *G.back_bow("Gown_BackBow", M["satin"], sash, z=WAIST, size=0.12, tail=0.26, drape_obj=over),      # 側面照背後的大蝴蝶結
        G.flower_earrings("Gown_Earrings", M["silver"]),
    ]
