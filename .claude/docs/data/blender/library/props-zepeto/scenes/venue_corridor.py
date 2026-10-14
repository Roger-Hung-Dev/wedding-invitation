# 婚宴會館①：休息室 → 走廊 → 餐飲區（開場片提案 B 的 B0、B1→B2、B2、B3 同一段連續場景）
# 常數都加檔案前綴（C_／P_／F_）：場景外掛共用 build_props 的命名空間，同名會互相蓋掉
# 座標（三個 venue_* 場景共用）：角色走在 y＝0 往 +X 走，鏡頭在角色右手側 y＝-3、比骨盆高 0.25 m（z≈0.89）、35 mm；
#   牆的正面：走廊 y＝C_WALL_Y（1.52），攝影區、門廳 y＝VENUE_WALL_Y（0.75）。畫面左 40% 留字卡；跟拍構圖（2026-10-12 使用者定）＝兩人整組放在右側 60% 區的中間，
#   也就是兩人中點落在畫面 70% 處：鏡頭 x ≈ 兩人中點 x − 0.62 m（角色在 y≈0、鏡頭 3 m 遠時）。
# 站位（2026-10-12 照動畫端 B0～B3 一鏡到底的走位改：走廊縮短、牆從 y 1.2 移到 0.75；B0～B3 不切換，不能各鏡平移）：
#   新娘走線（導演端 2026-10-13）：新郎 y≈0.1、新娘在遠側 y≈0.55、裙擺半徑 0.32 → 新娘佔 y 0.2～0.9；
#          B0 起點到 B2 新郎停下，y 0.2～0.9 不能有擺設 → 走廊整面牆（連同休息室門）退到 y 1.52，盆栽、餐檯貼新牆。
#   B0     休息室門 x＝0（門寬 0.75、門軸在左 x -0.375、往鏡頭這側開；門裡面是休息室，深 2 m）；新郎出門走約 1.4 m 到 y≈0.1 後往右。
#          門全開（-90°）時門片從門軸伸到 y 0.77，會碰到新娘走線的外緣：新娘經過 x -0.4 附近時門要已經關上或只開一半
#   B1→B2  走廊 x 1～3.8（壁燈、掛畫、盆栽）
#   B1→B2  盆栽 (1.25, 1.32)（縮 0.7 倍，最前緣 y≈1.15）
#   B2     甜點長檯中心 (5.0, 1.295)（1.8×0.35 m，x 4.1～5.9）、檯面高 0.6 m、檯面前緣 y＝1.10、垂幔玫瑰最前緣 y≈1.05（z 0.5 附近）；
#          新郎拿的小蛋糕 (5.614, 1.15, 檯面上 z 0.616)＝托盤前排正中間；新郎停在 (5.61, 0.04)、往前跨一步到 y≈0.45 拿（動畫端 2026-10-13）
#   B2 結尾（動畫端 2026-10-13，鏡內 10.3 秒）：新郎骨盆 (6.82, 0.64)、新娘 (7.50, 0.39)，新娘在前拉著新郎手腕往 +X 走；
#          B2 7.5～10.3 秒兩人走過 x 6.0～7.6、y 0.35～0.75。新娘走 y 0.4～0.7、裙擺 0.32，走線兩側各留 0.35 m → y -0.27～1.37 不放擺設。
#   B3     （2026-10-13 整段往右拉長）走廊在 x 6.4 往後退成泊車區凹處，牆面 y＝C_WALL_Y2（1.9）：
#          代客泊車立牌 (7.604, 1.62)、rz -15（最前緣 y≈1.40，在走線外；2026-10-13 從 8.6 左移：使用者看 B3 說新郎正好擋住立牌）；B3 停點（動畫端 2026-10-13 第 10 版，鏡長 9.4 秒；第 7 版起要看得出面對面）：新娘骨盆 (9.122, 0.472)、新郎 (8.606, 0.816)，
#          鏡頭（導演端要求新郎停穩前從 3 m 拉遠到 3.6 m）(8.195, -3.019, 0.95) 看向 (8.195, 0.581, 0.7)；立牌在兩人左後方（先前新娘 (9.125, 0.472)、(9.052, 0.244)、(8.904, 0.46)；新郎 (8.632, 0.893)、(8.615, 0.795)、(8.494, 0.79)）。
#          走廊盡頭（轉角）從 x 6.9 移到 C_X1＝10.2，攝影區、門廳整段跟著往 +X 平移 3.3 m。
#   B3→B4  前景遮擋柱子（動畫端 2026-10-13）：起步後只剩約 0.9 秒、鏡頭幾乎不動，靜止的柱子掃不過畫面 → 改成最後 0.7 秒從畫面右邊外滑進來，
#          B3 最後一格（9.4 秒）停在 (8.432, -1.719) 擋住兩人中點（第 10 版；先前 (8.436, -1.699)、(8.389, -1.852)、(8.406, -1.874)、(8.487, -1.193)、(8.414, -1.10)），B4 從這裡接（同 B5→B6 的滑入做法）。由動畫端擺，這裡的 instance 只是最後一格的示意。
#          B4 正式版沿用這根柱子，鏡內第 0 格在 (8.68, -2.379)、之後不動（不再另擺一根；舊值 (9.56, -1.60)）。
#          走廊盡頭轉角牆邊另有一根裝飾柱 (10.2, 0.45)
# 休息室門用 instance 擺（關著）；B0 要開門時：append_prop("lounge_door") 轉門片 ZP_lounge_door_leaf 的 rotation_euler.z（0 → -90°）

C_X0, C_X1, C_WH = -3.0, 10.2, 2.8   # C_X1 2026-10-13 從 6.9 拉長（B3 兩人要多走一段）
C_STEP_X, C_WALL_Y2 = 6.4, 1.9        # x 6.4 以後是泊車區凹處（2026-10-13：立牌要放在走線 y 1.37 之外）
C_WALL_Y = 1.52                       # 走廊牆（2026-10-13 從 0.75 退後，門跟著退：新娘 B1→B2 結尾走 y 0.69＋裙擺 0.32＝1.01，餐檯最前緣要 ≥1.05）
DOOR_X, DOOR_W, DOOR_H = 0.0, 0.75, 1.75
TABLE_X, SIGN_X, SIGN_Y, PILLAR_X, PILLAR_Y = 5.0, 7.604, 1.62, 8.432, -1.719
CAKE_X = 5.614                        # 新郎拿的那塊（動畫端 x 4.96＋0.654）：托盤前排正中間
T_Y = C_WALL_Y - 0.225            # 餐檯中心 y（深 0.35、檯面板 0.39，背面離牆 3 cm）
C_VIEW = {}


def _lounge(col):
    """門後的休息室（從門口看得到一點）：暖粉牆、圓鏡、小花瓶，深 2 m"""
    y0, y1, rx = C_WALL_Y + 0.2, C_WALL_Y + 2.2, 1.3
    mb = MB("ZP_venue_lounge_room"); w = clay("lounge", rough=0.9)
    mb.add(p_box(2 * rx, y1 - y0, 0.04, 0.01), clay("hall_floor2", rough=0.8), M((DOOR_X, (y0 + y1) / 2, -0.02)))
    mb.add(p_box(2 * rx + 0.2, 0.2, C_WH, 0.01), w, M((DOOR_X, y1 + 0.1, C_WH / 2)))
    for sx in (-1, 1):
        mb.add(p_box(0.2, y1 - y0, C_WH, 0.01), w, M((DOOR_X + sx * (rx + 0.1), (y0 + y1) / 2, C_WH / 2)))
    mb.add(p_torus(0.32, 0.035, 0, 2 * math.pi, 48, 12), clay("gold", rough=0.4), M((DOOR_X + 0.25, y1 - 0.03, 1.25), (90, 0, 0)))
    mb.add(p_cyl(0.3, 0.02, 0.008, 48), clay("glass"), M((DOOR_X + 0.25, y1 - 0.02, 1.25), (90, 0, 0)))
    mb.add(p_box(0.9, 0.4, 0.55, 0.05), clay("white", rough=0.7), M((DOOR_X + 0.25, y1 - 0.25, 0.275)))   # 梳妝台
    for k in range(5):
        rose(mb, clay("rose" if k % 2 else "blush"), (DOOR_X + 0.55 + 0.05 * math.cos(k * 1.3), y1 - 0.22, 0.62 + 0.03 * (k % 2)), 0.04)
    mb.obj(col)


def _build(col, cols):
    venue_floor(col, "ZP_venue_corridor_floor", C_X0, C_X1, "wood", y1=C_WALL_Y2 + 0.05)
    rt = MB("ZP_venue_corridor_return")
    for x, ya, yb, sx in ((C_X1, VENUE_WALL_Y, C_WALL_Y2, -1), (C_STEP_X, C_WALL_Y, C_WALL_Y2, 1)):   # 側牆：轉角（面朝 -X）、凹處起點（面朝 +X）
        rt.add(p_box(0.2, yb + 0.2 - ya, C_WH, 0.008), clay("hall_wall", rough=0.9), M((x - sx * 0.1, (ya + yb + 0.2) / 2, C_WH / 2)))
        rt.add(p_box(0.03, yb - ya, 0.9, 0.008), clay("wainscot", rough=0.8), M((x + sx * 0.015, (ya + yb) / 2, 0.45)))
        rt.add(p_box(0.05, yb - ya, 0.05, 0.015), clay("trim"), M((x + sx * 0.025, (ya + yb) / 2, 0.92)))
    rt.obj(col)
    venue_runner(col, "ZP_venue_corridor_runner", C_X0, C_X1, y=0.15, w=1.7)
    venue_wall(col, "ZP_venue_corridor_wall", C_X0, C_STEP_X, C_WH, gaps=[(DOOR_X - DOOR_W / 2, DOOR_X + DOOR_W / 2, DOOR_H)], y=C_WALL_Y)
    venue_wall(col, "ZP_venue_corridor_wall2", C_STEP_X, C_X1, C_WH, y=C_WALL_Y2)
    _lounge(col)
    C_VIEW["door"] = instance(col, cols["lounge_door"], (DOOR_X, C_WALL_Y, 0))
    # 開門版（只在 B0 示意圖用）：共用門的網格，門片轉 -70°
    C_VIEW["door_open"] = posed_copy(col, cols["lounge_door"], (DOOR_X, C_WALL_Y, 0), {"leaf": -70})
    deco = MB("ZP_venue_corridor_deco")
    for x in (-2.0, 1.2, 3.0):
        venue_sconce(deco, x, y=C_WALL_Y)
    for x in (7.3, 9.6):
        venue_sconce(deco, x, y=C_WALL_Y2)
    venue_frame(deco, 8.1, 1.5, 0.6, 0.76, "rose", y=C_WALL_Y2)
    venue_frame(deco, -1.1, 1.45, 0.62, 0.78, "blush", y=C_WALL_Y)
    venue_frame(deco, 2.1, 1.45, 0.7, 0.86, "rose", y=C_WALL_Y)
    venue_frame(deco, 3.6, 1.45, 0.5, 0.64, "lav", y=C_WALL_Y)
    # B2 甜點區：檯面上方的花環（掛在牆上）
    for k in range(13):
        t = k / 12; x = TABLE_X - 0.95 + 1.9 * t; z = 1.75 - 0.18 * math.sin(math.pi * t)
        deco.add(p_sphere(0.06, 0.04, 0.06, 14), clay(["blush", "cream", "rose"][k % 3]), M((x, C_WALL_Y - 0.05, z)))
    # 兩層蛋糕架＋前面一個小托盤（新郎拿托盤上的）
    gd = clay("gold", rough=0.4); TZ = 0.6
    deco.add(p_cyl(0.008, 0.36, 0.003, 12), gd, M((TABLE_X, T_Y + 0.02, TZ + 0.18)))
    for z, r in ((TZ + 0.02, 0.17), (TZ + 0.22, 0.11)):
        deco.add(p_lathe([(0, 0), (r, 0), (r + 0.01, 0.015), (r - 0.005, 0.02), (0, 0.012)], 48), clay("white", rough=0.6), M((TABLE_X, T_Y + 0.02, z)))
    deco.add(p_box(0.32, 0.18, 0.016, 0.006), clay("white", rough=0.6), M((CAKE_X, T_Y - 0.105, TZ + 0.008)))   # 托盤前緣＝檯面前緣
    deco.add(p_sphere(0.012), gd, M((TABLE_X, T_Y + 0.02, TZ + 0.37)))
    for k in range(5):                                                     # 小花瓶
        rose(deco, clay("blush" if k % 2 else "ivory"), (TABLE_X + 0.68 + 0.05 * math.cos(k * 1.3), T_Y + 0.08 + 0.05 * math.sin(k * 1.3), TZ + 0.19), 0.035)
    deco.add(p_lathe([(0, 0), (0.05, 0), (0.06, 0.05), (0.035, 0.15), (0.045, 0.17), (0, 0.16)], 32), clay("lav_lt"), M((TABLE_X + 0.68, T_Y + 0.08, TZ)))
    deco.obj(col)
    instance(col, cols["buffet_table"], (TABLE_X, T_Y, 0))
    for k in range(6):
        a = 2 * math.pi * k / 6
        instance(col, cols["mini_cake"], (TABLE_X + 0.12 * math.cos(a), T_Y + 0.02 + 0.12 * math.sin(a), TZ + 0.035))
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.5
        instance(col, cols["mini_cake"], (TABLE_X + 0.06 * math.cos(a), T_Y + 0.02 + 0.06 * math.sin(a), TZ + 0.235))
    for i in range(3):
        for j in range(2):
            instance(col, cols["mini_cake"], (CAKE_X - 0.1 + i * 0.1, T_Y - 0.145 + j * 0.08, TZ + 0.016))   # 前排離檯面前緣 5 cm
    instance(col, cols["dessert"], (TABLE_X - 0.32, T_Y + 0.02, TZ), 0, 0.75)
    instance(col, cols["fruit"], (TABLE_X + 0.36, T_Y, TZ), 0, 0.75)
    instance(col, cols["planter"], (1.25, C_WALL_Y - 0.2, 0), 0, 0.7)
    instance(col, cols["valet_sign"], (SIGN_X, SIGN_Y, 0), -15)
    instance(col, cols["pillar"], (PILLAR_X, PILLAR_Y, 0))
    instance(col, cols["pillar"], (C_X1, VENUE_WALL_Y - 0.3, 0))


def _door_pose(on):
    C_VIEW["door"].hide_render = on
    for o in C_VIEW["door_open"]:
        o.hide_render = not on


def _lights():
    out = venue_lights(C_X0, C_X1)
    out.append(light("POINT", "ZP_LoungeLamp", (DOOR_X, C_WALL_Y + 1.3, 2.2), (0, 0, 0), 90, "#FFD9B8", size=0.4))
    return out


def _cam(cx, z=0.89, aim_z=0.70, y=-3.0, lens=35):
    return ((cx, y, z), (cx, 0.0, aim_z), lens)


SCENE = dict(
    key="venue_corridor",
    label="場景示意：婚宴會館①休息室 → 走廊 → 甜點區（提案 B：B0～B3；灰色人形＝ZEPETO 角色比例，不屬於場景）",
    scenes="提案B B0～B3",
    group="venue:婚宴會館",
    props=["lounge_door", "buffet_table", "mini_cake", "dessert", "fruit", "planter", "valet_sign", "pillar"],
    camera=((3.6, -10.0, 2.4), (3.6, 0.3, 0.95), 22),
    context=lambda c: venue_context(c, C_X1, C_X1 + 4.0, "marble", "hall_wall2"),
    night=True, sky="#F6EEE6", sky_strength=0.45,
    lights=_lights,
    figures=[(0.15, 0.1), (2.4, 0.1), (2.85, 0.55), (5.61, 0.45), (4.63, 0.69), (8.606, 0.816), (9.122, 0.472)],   # 後兩個＝B3 停點
    views=[
        ("b0", "B0：休息室門正前方 3.5 m（門開 70° 的樣子）", ((DOOR_X - 0.72, C_WALL_Y - 3.5, 0.89), (DOOR_X - 0.72, C_WALL_Y, 0.85), 35), _door_pose),
        ("b1b2", "B1→B2：走廊側面跟拍（角色在 x 2.4）", _cam(2.4 - 0.62)),
        ("b2", "B2：甜點長檯（新郎跨到 y 0.45 拿蛋糕、新娘在他左後方；兩人中點在畫面 70%）", _cam(5.12 - 0.62)),
        ("b3", "B3：兩人停在泊車立牌右前方（新郎 8.606、新娘 9.122；動畫端的鏡頭）", ((8.195, -3.019, 0.95), (8.195, 0.581, 0.7), 35)),
        ("b3_end", "B3 最後一格：柱子從右邊滑進來、擋住兩人中點", ((8.195, -3.019, 0.95), (8.195, 0.581, 0.7), 35)),
    ],
    build=_build,
)
