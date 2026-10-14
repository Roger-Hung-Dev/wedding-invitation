# 攝影棚（參考照片 refs/photo_studio/ref_1.png，分析見 refs/photo_studio/analysis.md）
# 使用者要求：照照片的攝影棚做，拿掉中間 4 張椅子和梯子。房間（地板、三面牆、天花板、窗簾）只屬於這個場景，直接在這裡建。
# 座標：背景紙垂下的那一面在 y＝0.35、往鏡頭（-Y）鋪到 y≈-1.95；鏡頭在 y＝-6.2、28 mm（背景紙寬 2.72 m 約佔畫面 1/3，兩盞燈整支入鏡，同照片）

RX0, RX1, RY0, RY1, RZ = -3.1, 2.95, -7.8, 0.75, 3.4                    # 房間內緣：左牆、右牆、前（鏡頭後）、後牆、天花板


def _curtain(mb, mat, x, y0, y1, z0, z1, side):
    """窗簾：一排直立的圓角長條，前後錯開做出布褶；side＝貼哪面牆（-1 左牆、+1 右牆）"""
    n = max(2, int((y1 - y0) / 0.16))
    for i in range(n):
        y = y0 + (i + 0.5) * (y1 - y0) / n
        mb.add(p_box(0.09, (y1 - y0) / n * 1.15, z1 - z0, 0.04), mat, M((x - side * (0.06 + 0.035 * (i % 2)), y, (z0 + z1) / 2)))
    mb.add(p_cyl(0.02, y1 - y0 + 0.3, 0.006, 12), clay("steel", rough=0.45), M((x - side * 0.08, (y0 + y1) / 2, z1 + 0.05), (90, 0, 0)))


def _build(col, cols):
    room = MB("ZP_studio_room")
    nx = int((RX1 - RX0) / 0.2)
    for i in range(nx):                                                  # 灰色長條木地板（兩色交錯）
        x = RX0 + (i + 0.5) * (RX1 - RX0) / nx
        room.add(p_box((RX1 - RX0) / nx - 0.006, RY1 - RY0, 0.04, 0.006), clay("studio_floor" if i % 2 == 0 else "floor_dk", rough=0.8), M((x, (RY0 + RY1) / 2, -0.02)))
    w = clay("wall_st", rough=0.9)
    room.add(p_box(RX1 - RX0 + 0.4, 0.2, RZ, 0.03), w, M(((RX0 + RX1) / 2, RY1 + 0.1, RZ / 2)))          # 後牆
    room.add(p_box(0.2, RY1 - RY0, RZ, 0.03), w, M((RX0 - 0.1, (RY0 + RY1) / 2, RZ / 2)))                 # 左牆
    room.add(p_box(0.2, RY1 - RY0, RZ, 0.03), w, M((RX1 + 0.1, (RY0 + RY1) / 2, RZ / 2)))                 # 右牆
    room.add(p_box(RX1 - RX0 + 0.4, RY1 - RY0, 0.2, 0.03), w, M(((RX0 + RX1) / 2, (RY0 + RY1) / 2, RZ + 0.1)))  # 天花板
    for x, side in ((RX0, -1), (RX1, 1)):                               # 踢腳板
        room.add(p_box(0.04, RY1 - RY0, 0.1, 0.015), clay("floor_dk"), M((x - side * 0.02, (RY0 + RY1) / 2, 0.05)))
    _curtain(room, clay("sheer", rough=0.9), RX0, -1.9, 0.35, 0.55, 2.95, -1)        # 左牆白紗窗簾
    _curtain(room, clay("blackout"), RX0, -3.5, -2.6, 0.75, 2.95, -1)               # 左牆前段黑色遮光簾
    _curtain(room, clay("blackout"), RX1, -0.6, 0.35, 1.55, 2.75, 1)                # 右牆後上方黑色窗簾
    room.obj(col)
    instance(col, cols["studio_backdrop"], (0, 0.35, 0))
    instance(col, cols["softbox_light"], (-1.85, -2.0, 0), 128.0)        # 左前方（背景紙前緣），朝向背景紙中央偏後：鏡頭看到的大多是外殼
    instance(col, cols["beauty_dish_light"], (1.6, -1.9, 0), -112.0)     # 右前方，朝向中央
    instance(col, cols["c_stand"], (2.3, -0.6, 0), 25.0)                 # 右後方靠牆兩支空架
    instance(col, cols["c_stand"], (2.55, -0.3, 0), -40.0)
    # 2026-10-11 第二張參考照片（ref_2）：加兩台立在地上的攝影機，在棚前方左右兩側、鏡頭朝背景紙中央拍
    instance(col, cols["video_camera"], (-1.15, -3.4, 0), 162.3)
    instance(col, cols["video_camera"], (1.15, -3.2, 0), -161.3)


def _lights():
    """室內：天花板一大片柔光（照片整體光線平均、陰影很淡）"""
    return [light("AREA", "ZP_StudioCeiling", (0, -1.8, RZ - 0.05), (0, 0, 0), 320, "#FFF8F2", size=5.0),
            light("AREA", "ZP_StudioFill", (0, -5.6, 2.2), (75, 0, 0), 110, "#F3F0FF", size=3.0)]


SCENE = dict(
    key="photo_studio",
    label="場景示意：攝影棚（參考照片，拿掉椅子與梯子；加兩台攝影機）",
    scenes="（未用）",
    group="studio:攝影棚",
    props=["studio_backdrop", "softbox_light", "beauty_dish_light", "c_stand", "video_camera"],
    camera=((0.0, -6.2, 1.5), (0.0, 0.2, 1.38), 28),
    night=False, sky="#EEEAF0", sky_strength=0.3,
    lights=_lights,
    build=_build,
)
