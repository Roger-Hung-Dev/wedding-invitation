# 攝影師黑色便服（2026-10-12 導演端分鏡 opening-proposal-b B4 要的：黑色上衣加長褲，蹲著拍照）
# 寬鬆黑色圓領長袖上衣（蓋過褲頭）、黑色長褲、深灰休閒鞋。2026-10-12 攝影師身體 v1 出廠後改穿在攝影師身上。
import garment_lib as G

A = G.A

M = dict(
    top=G.material("Photog_Top", (28, 28, 30), 0.85, sheen=0.3),        # 黑色棉質，sheen 讓暗部還看得出布料
    pants=G.material("Photog_Pants", (40, 40, 44), 0.8, sheen=0.2),     # 比上衣淺一點，上下分得開
    shoe=G.material("Photog_Shoe", (70, 70, 74), 0.6),
)


def build():
    G.LIVE_SOLIDIFY = True       # 攝影師身體肩膀在手臂放下時會擠出碎片：厚度改在變形之後才加
    # 上衣用外套配方不開襟＝寬鬆套頭衫；下襬蓋過褲頭，蹲下時腰後不露肉
    # 領口拉到頭切口上 2.8 cm：攝影師脖子接口有一條細線，身體端與使用者說好用衣領蓋住
    # 2026-10-12 改用貼身襯衫配方（外套配方推厚 1.6 cm，攝影師肩膀在手臂放下時會擠出一條摺）：高領、紮進褲子
    top = G.shirt("Photog_Top", M["top"], collar_top=A["COLLAR_TOP"] + 0.010, collar_thick=0.006)
    pants = G.trousers("Photog_Pants", M["pants"], flare=0.006)
    shoes = G.shoes("Photog_Shoes", M["shoe"], toe=0.012)
    return G.corrective_smooth([top, pants, shoes], iterations=30)     # 手臂放下時肩膀上的小摺抹平
