# 婚宴會館③：宴會廳大門前的門廳（開場片提案 B 的 B6）
# 常數都加檔案前綴（C_／P_／F_）：場景外掛共用 build_props 的命名空間，同名會互相蓋掉
# 座標同 venue_corridor（角色走 y＝0 往 +X、鏡頭 y＝-3、牆面 y＝0.75）；接在攝影區（x 14.8）之後。
# 2026-10-12 跟著走廊縮短整段往 -X 平移 3.3 m、牆往 -Y 平移 0.45 m。
# 2026-10-13 走廊 B3 拉長，整段往 +X 平移 3.3 m（說明與程式裡的 x 都已是平移後的值；y 不變）。
# 站位（建議值）：
#   B5→B6  前景遮擋門框：中心 x＝15.81、y＝-1.5，左邊門柱在 x 14.8 掃過鏡頭；右邊門柱在 x 16.82，
#          鏡頭停在 x≈15.8 時剛好在畫面外
#   B6     宴會廳雙開大門中心 x＝16.4（門洞 1.7×2.2 m）；兩人停在門正前方：新郎 (16.75, 0)、新娘 (16.05, 0)，間距 0.7 m（動畫端實測），轉身面向大門。
#          前景門框 door_frame (15.81, -1.5) 原位不動，只在兩人停下、鏡頭拉遠到 4.5 m 時當框住兩人的前景。
#   B5→B6  換景（使用者 2026-10-12 決定）：另擺一根 pillar 在鏡頭前約 1.3 m 擋住畫面，由動畫端每一鏡自己擺（不放進本場景）：
#          開頭在 (15.39, -1.94)（鏡頭前約 0.9 m，擋住兩人中點），0～0.9 秒往左滑到 (14.99, -1.94) 剛好出畫，之後隱藏。
#          要滑是因為兩人 1.2 秒就停、停下後鏡頭又拉遠到 4.5 m，靜止的柱子出不了畫還會重新入鏡。位置跟鏡頭算，以最新回報為準
#          門後是發光通道，另打一盞朝 -Y 的暖白面光；門片往內開：append_prop("ballroom_doors") 轉
#          ZP_ballroom_door_L（0 → +90°）、ZP_ballroom_door_R（0 → -90°），2.9 秒開始
# ⚠️ 側面跟拍（3 m、35 mm）只拍得到牆上約 1.8 m 以下；大門整扇入鏡要把鏡頭拉遠到約 4.5 m，或改用約 24 mm

F_X0, F_X1, F_WH = 14.8, 19.6, 3.0
DX, DW, DH = 16.4, 1.7, 2.2
F_VIEW = {}


def _build(col, cols):
    venue_floor(col, "ZP_venue_foyer_floor", F_X0, F_X1, "marble")
    venue_wall(col, "ZP_venue_foyer_wall", F_X0, F_X1, F_WH, gaps=[(DX - DW / 2, DX + DW / 2, DH)])
    rug = MB("ZP_venue_foyer_rug")                                          # 門前的地毯
    rug.add(p_box(2.4, 1.9, 0.016, 0.01), clay("runner_bd", rough=0.9), M((DX, -0.25, 0.008)))
    rug.add(p_box(2.2, 1.7, 0.02, 0.01), clay("carpet", rough=0.9), M((DX, -0.25, 0.01)))
    rug.obj(col)
    deco = MB("ZP_venue_foyer_deco")
    for x in (DX - 1.45, DX + 1.45):                                          # 兩側花柱：白色台座＋花球
        deco.add(p_lathe([(0, 0), (0.2, 0), (0.2, 0.06), (0.13, 0.12), (0.1, 0.7), (0.16, 0.76), (0.16, 0.8), (0, 0.8)], 40), clay("white", rough=0.7), M((x, VENUE_WALL_Y - 0.35, 0)))
        rnd = random.Random(int(x * 10))
        for k in range(14):
            a = rnd.uniform(0, 2 * math.pi); r = rnd.uniform(0, 0.18)
            rose(deco, clay(rnd.choice(["blush", "ivory", "rose"])), (x + r * math.cos(a), VENUE_WALL_Y - 0.35 + r * math.sin(a), 0.9 + rnd.uniform(0, 0.16)), 0.06, rnd)
        for k in range(8):
            leaf(deco, clay("euca"), (x, VENUE_WALL_Y - 0.35, 0.88), 0.16, 45 * k, -20)
        venue_sconce(deco, x + (0.75 if x > DX else -0.75))
    deco.obj(col)
    F_VIEW["doors"] = instance(col, cols["ballroom_doors"], (DX, VENUE_WALL_Y, 0))
    F_VIEW["doors_open"] = posed_copy(col, cols["ballroom_doors"], (DX, VENUE_WALL_Y, 0), {"door_L": 75, "door_R": -75})
    instance(col, cols["door_frame"], (15.81, -1.5, 0))


def _open(on):
    F_VIEW["doors"].hide_render = on
    for o in F_VIEW["doors_open"]:
        o.hide_render = not on


def _lights():
    out = venue_lights(F_X0, F_X1)
    out.append(light("AREA", "ZP_BallroomGlow", (DX, VENUE_WALL_Y + 1.4, 1.2), (-90, 0, 0), 450, "#FFE9CC", size=1.6))
    return out


SCENE = dict(
    key="venue_foyer",
    label="場景示意：婚宴會館③宴會廳大門前的門廳（提案 B：B6；灰色人形＝ZEPETO 角色比例）",
    scenes="提案B B6",
    group="venue:婚宴會館",
    props=["ballroom_doors", "door_frame"],
    camera=((16.6, -7.0, 2.2), (16.6, 0.3, 1.1), 22),
    context=lambda c: venue_context(c, F_X0 - 4.0, F_X0, "marble", "hall_wall2"),
    night=True, sky="#F6EEE6", sky_strength=0.45,
    lights=_lights,
    figures=[(16.75, 0.0), (16.05, 0.0)],
    views=[
        ("b6_wipe", "B6 開頭：門框從鏡頭前掃過", ((14.95, -3.0, 0.89), (14.95, 0.0, 0.70), 35)),
        ("b6", "B6：兩人停在大門前（側面跟拍 3 m、35 mm：門的上半部出畫）", ((DX - 0.62, -3.0, 0.89), (DX - 0.62, 0.0, 0.70), 35)),
        ("b6_back", "B6 2.9 秒後：繞到兩人背後，大門往內打開、門後強光", ((DX, -2.0, 1.15), (DX, VENUE_WALL_Y, 1.25), 35), _open),
    ],
    build=_build,
)
