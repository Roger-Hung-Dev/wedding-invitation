# 情境版 ③ v2_03c 的道具（2026-10-09 第 3 幕改版；2026-10-10 第 4 輪改）：沿小徑鋪向拱門的紅毯卷、立體文字牆 ×4。
# 放在 Set_Garden／Set_V2 底下自己的子集合 V2_Carpet，由 shots_v2_s03carpet.py 開關；既有的 V2_*、G_* 不動。
# 高度：鋪開的紅毯墊高 z0（小徑的踏腳石比草地高，第 2 輪看到石頭從紅毯裡透出來）。
# 座標：紅毯沿 +Y（小徑往拱門），寬 CP["w"]、中心線 x＝CP["x"]；紅毯卷的軸沿 X。
#   捲著的部分＝圓柱（半徑隨鋪開的長度變小，面積守恆：r² = r0² − 厚度×鋪開長度／π）；鋪開的部分＝貼地的薄片，從起點到紅毯卷著地點。
# 第 4 輪（使用者回饋 1、2）：
#   - 拿掉卡住紅毯卷的石頭、拿掉毯上平貼的四個字。
#   - 改成立體文字牆（cp_walls）：暖白牆板＋金框＋底座＋頂上兩朵玫瑰，正面是有厚度的玫瑰色字（霞鶩文楷 Bold、擠出 1.4 cm），
#     牆板四周一圈小燈泡。平常不亮（字是霧面玫瑰色、燈泡灰白）；cp_light(i, 0～1) 亮燈：字發光、燈泡發光、前方一盞小點光。
#     「婚禮」那面比較大，字下方多一行「2026.12.12」。
import bpy, bmesh, math, os
from mathutils import Vector, Matrix

CP = dict(x=0.0, w=0.95, th=0.012, z0=0.018)
CP_OBJ = {}
CARPET_FONT = (r"D:\render-work\opening-v12\compose\fonts\LXGWWenKaiTC-Bold.ttf", "C:/Windows/Fonts/kaiu.ttf")
# 文字牆尺寸（公尺）：W 牆板寬、H 牆板高、D 牆板厚、size 字級（字身高）、sub 小字字級
WALL = dict(small=dict(W=0.74, H=0.50, D=0.06, size=0.29, sub=0.0),
            big=dict(W=0.86, H=0.66, D=0.07, size=0.30, sub=0.085))
WALL_LIT = dict(txt_emit=1.6, bulb_emit=6.0, light_w=1.2)


def _font():
    for p in CARPET_FONT:
        if os.path.exists(p):
            return bpy.data.fonts.load(p, check_existing=True)
    return None


def cp_build(c, y0, walls=()):
    """y0：鋪開的紅毯起點（y）；walls：[dict(text, sub, pos=(x, y), rz, kind='small'|'big')]"""
    coll_clear(c.name)
    CP_OBJ.clear(); CP_OBJ.update(y0=y0)
    red = pmat("CP_Red", srgb("#B23A48"), rough=0.85, spec=0.15, noise=0.18, sheen=0.5)
    edge = pmat("CP_Edge", srgb("#C9A45C"), rough=0.5, spec=0.4)
    inner = pmat("CP_Inner", srgb("#8E2A36"), rough=0.9, spec=0.1)
    w = CP["w"]
    # 鋪開的紅毯（原點在起點；scale.y＝鋪到哪裡）＋兩側金邊
    bm = bmesh.new()
    box(bm, Vector((0.0, 0.5, CP["th"] / 2)), (w, 1.0, CP["th"]), mi=0)
    for sx in (-1, 1):
        box(bm, Vector((sx * (w / 2 - 0.035), 0.5, CP["th"] + 0.0006)), (0.03, 1.0, 0.0012), mi=1)
    o = mesh_obj("CP_Flat", bm, [red, edge], c)
    o.location = (CP["x"], y0, CP["z0"]); CP_OBJ["flat"] = o
    # 紅毯卷：單位半徑的圓柱（軸沿 X），外層紅、兩端露出深色的捲層，一條金邊斜紋讓滾動看得出來
    bm = bmesh.new()
    cyl(bm, Vector((0, 0, 0)), 1.0, w, axis="X", seg=40, mi=0)
    for sx in (-1, 1):
        cyl(bm, Vector((sx * (w / 2 + 0.002), 0, 0)), 0.86, 0.004, axis="X", seg=40, mi=1)
    box(bm, Vector((0, 0, 1.0)), (w + 0.004, 0.10, 0.03), mi=2)               # 捲口（外層的尾端），跟著滾
    roll = mesh_obj("CP_Roll", bm, [red, inner, edge], c, smooth=False)
    CP_OBJ["roll"] = roll
    CP_OBJ["walls"] = [cp_wall(c, i, wd) for i, wd in enumerate(walls)]
    cp_update(y0 + 0.3, 0.25, 0.0, 0.0)


def _txt(c, name, body, size, mat, fnt, extrude):
    cu = bpy.data.curves.get(name) or bpy.data.curves.new(name, "FONT")
    cu.body = body; cu.size = size; cu.align_x = "CENTER"; cu.align_y = "CENTER"
    cu.extrude = extrude; cu.bevel_depth = min(0.003, extrude * 0.3); cu.bevel_resolution = 1
    if fnt:
        cu.font = fnt
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
    ob = bpy.data.objects.new(name, cu); c.objects.link(ob)
    cu.materials.clear(); cu.materials.append(mat)
    return ob


def cp_wall(c, i, wd):
    """一面立體文字牆（局部座標：正面朝 −Y，底部在 z=0；rz 轉到面向鏡頭）"""
    k = WALL[wd.get("kind", "small")]; W, H, D = k["W"], k["H"], k["D"]
    root = bpy.data.objects.get(f"CP_Wall{i}") or bpy.data.objects.new(f"CP_Wall{i}", None)
    if root.name not in c.objects:
        c.objects.link(root)
    root.location = (wd["pos"][0], wd["pos"][1], 0.0); root.rotation_euler = (0, 0, math.radians(wd["rz"]))
    cream = pmat("CPW_Board", srgb("#F6EFE6"), rough=0.8, spec=0.2, noise=0.12)
    base_m = pmat("CPW_Base", srgb("#FBF7F0"), rough=0.7, spec=0.25)
    gold = pmat("CPW_Gold", srgb("#C9A45C"), rough=0.35, spec=0.6, metal=0.6)
    rose = pmat("CPW_Rose", srgb("#D9777F"), rough=0.7, spec=0.25)
    leaf = pmat("CPW_Leaf", srgb("#8FA58A"), rough=0.8, spec=0.2)
    lift = wd.get("lift", 0.0)                                       # 牆板墊高（兩根立柱撐起來；前三面一面比一面高，從鏡頭看像往右上的階梯）
    bm = bmesh.new()
    box(bm, Vector((0, 0, 0.04)), (W + 0.08, D + 0.08, 0.08), mi=1)                       # 底座
    if lift > 0:
        for sx in (-1, 1):
            box(bm, Vector((sx * (W / 2 - 0.07), 0, 0.08 + lift / 2)), (0.045, 0.045, lift), mi=1)
    hb = 0.08 + lift
    box(bm, Vector((0, 0, hb + H / 2)), (W, D, H), mi=0)                                  # 牆板
    fy = -D / 2 - 0.006
    for zc, sz in ((hb + 0.0125, (W, 0.012, 0.025)), (hb + H - 0.0125, (W, 0.012, 0.025))):
        box(bm, Vector((0, fy, zc)), sz, mi=2)                                            # 金框上下
    for sx in (-1, 1):
        box(bm, Vector((sx * (W / 2 - 0.0125), fy, hb + H / 2)), (0.025, 0.012, H), mi=2)  # 金框左右
    box(bm, Vector((0, 0, hb + H + 0.012)), (W + 0.03, D + 0.02, 0.024), mi=2)             # 頂蓋（金）
    for sx in (-1, 1):                                                                    # 頂上兩角各一朵玫瑰＋兩片葉
        ball(bm, Vector((sx * (W / 2 - 0.02), -0.005, hb + H + 0.055)), 0.042, mi=3, seg=12)
        for dx in (-0.045, 0.045):
            box(bm, Vector((sx * (W / 2 - 0.02) + dx, -0.004, hb + H + 0.035)), (0.05, 0.012, 0.022),
                rot=Matrix.Rotation(math.radians(25 if dx > 0 else -25), 4, "Y"), mi=4)
    mesh_obj(f"CP_Wall{i}_Body", bm, [cream, base_m, gold, rose, leaf], c, smooth=True, parent=root)
    # 字（每面牆自己的材質，亮燈時改發光強度）
    tm = pmat(f"CPW_Txt{i}", srgb("#8E5E66"), rough=0.6, spec=0.3, emit=0.0001)            # 不亮：灰玫瑰；亮：發出亮玫瑰紅
    fnt = _font()
    sub = wd.get("sub")
    tz = hb + H * (0.56 if sub else 0.5)
    t = _txt(c, f"CP_Wall{i}_Txt", wd["text"], k["size"], tm, fnt, 0.014)
    t.parent = root; t.location = (0, -D / 2 - 0.016, tz); t.rotation_euler = (math.radians(90), 0, 0)
    objs = dict(root=root, txt_mat=tm)
    if sub:
        s_ = _txt(c, f"CP_Wall{i}_Sub", sub, k["sub"], tm, fnt, 0.008)
        s_.parent = root; s_.location = (0, -D / 2 - 0.012, hb + H * 0.17); s_.rotation_euler = (math.radians(90), 0, 0)
    # 一圈小燈泡（金框上）
    bmat = pmat(f"CPW_Bulb{i}", srgb("#E4DCCD"), rough=0.3, spec=0.5, emit=0.0001)
    bm = bmesh.new(); r_b = 0.011 if wd.get("kind") != "big" else 0.013
    nx = 7 if wd.get("kind") != "big" else 9; nz = 4 if wd.get("kind") != "big" else 5
    for j in range(nx):
        x = -W / 2 + 0.035 + (W - 0.07) * j / (nx - 1)
        for zc in (hb + 0.0125, hb + H - 0.0125):
            ball(bm, Vector((x, fy - 0.012, zc)), r_b, seg=8)
    for j in range(1, nz - 1):
        z = hb + 0.0125 + (H - 0.025) * j / (nz - 1)
        for sx in (-1, 1):
            ball(bm, Vector((sx * (W / 2 - 0.0125), fy - 0.012, z)), r_b, seg=8)
    mesh_obj(f"CP_Wall{i}_Bulbs", bm, [bmat], c, smooth=True, parent=root)
    objs["bulb_mat"] = bmat
    # 前方小範圍點光（亮燈時打亮牆板與地面一小塊）
    ln = f"CP_Wall{i}_Lamp"
    lo = bpy.data.objects.get(ln) or bpy.data.objects.new(ln, bpy.data.lights.get(ln) or bpy.data.lights.new(ln, "POINT"))
    if lo.name not in c.objects:
        c.objects.link(lo)
    lo.parent = root; lo.location = (0, -0.32, tz + 0.05)
    lo.data.color = (1.0, 0.82, 0.68); lo.data.shadow_soft_size = 0.08; lo.data.energy = 0.0
    try:
        lo.data.use_custom_distance = True; lo.data.cutoff_distance = 1.2
    except Exception:
        pass
    objs["lamp"] = lo; objs["kind"] = wd.get("kind", "small")
    return objs


def _emit(mat, strength, color=None):
    bs_ = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bs_.inputs["Emission Strength"].default_value = strength
    if color is not None:
        bs_.inputs["Emission Color"].default_value = (*color[:3], 1)


def cp_light(i, lvl):
    """第 i 面牆亮燈程度 0～1"""
    o = CP_OBJ["walls"][i]; L = WALL_LIT
    _emit(o["txt_mat"], L["txt_emit"] * lvl, srgb("#F0485F"))
    _emit(o["bulb_mat"], L["bulb_emit"] * lvl, srgb("#FFE3A6"))
    o["lamp"].data.energy = L["light_w"] * lvl * (1.6 if o["kind"] == "big" else 1.0)


def cp_update(y_contact, r, angle, hop):
    """y_contact：紅毯卷著地點（＝鋪到哪裡）；r：紅毯卷半徑；angle：滾了幾度（弧度）；hop：抬高"""
    O = CP_OBJ
    O["flat"].scale = (1, max(0.001, y_contact - O["y0"]), 1)
    ro = O["roll"]
    ro.location = (CP["x"], y_contact, r + hop + CP["z0"])
    ro.rotation_euler = (angle, 0, 0)
    ro.scale = (1, r, r)
