# 「花園拱門」景（②③⑤⑦⑧ 共用）。build_garden() 建全部；子集合依幕開關：
#   G_Base 拱門、樹籬牆、草地、小徑、花圃、樹、天空（每幕都開）
#   G_Bar  ③ 押花進度條（長木框＋10 朵會開的花＋緞帶填色＋把手＋拖在新郎肩上的緞帶）
#   G_Cam  ⑤ 木製老相機＋三腳架＋紅燈
#   G_Tea  ⑦ 下午茶高腳桌（蕾絲桌巾、兩層點心架、司康、馬卡龍、茶壺）＋小黑板（場景字）＋香檳杯×2
# 座標：鏡頭預設往 +Y 看；拱門中心 (0, 0.30)，柱子 x=±1.0；樹籬牆在拱門兩側（y 0.12～0.47）。
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

ARCH_Y = 0.30
POST_X = 1.0
HEDGE_Y0, HEDGE_Y1 = 0.12, 0.47
BAR_X0, BAR_X1, BAR_Y, BAR_Z = -5.45, -2.25, -0.60, 0.86      # ③ 進度條：左右端、所在平面 y、花的高度
N_BUDS = 10


def ellip(bm, M, radii, seg=8, mi=0):
    """變換矩陣 M 下的橢球（radii＝三軸半徑）；bm 是 MB 時走快速路徑"""
    if isinstance(bm, MB):
        return bm.ellip(M, radii, seg, mi)
    res = bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(4, seg * 2 // 3), radius=1.0)
    bmesh.ops.transform(bm, matrix=M @ Matrix.Diagonal((*radii, 1)), verts=res["verts"])
    for f in {f for v in res["verts"] for f in v.link_faces}:
        f.material_index = mi


def ring(bm, c, R, r, Mrot=None, seg=16, mi=0):
    """圓環（用小圓柱接成）：中心 c、半徑 R、管徑 r；Mrot 決定環所在的平面（預設 xy 平面）"""
    Mrot = Mrot or Matrix.Identity(4)
    pts = [Vector(c) + (Mrot @ Vector((R * math.cos(2 * math.pi * k / seg), R * math.sin(2 * math.pi * k / seg), 0))) for k in range(seg)]
    for a, b in zip(pts, pts[1:] + pts[:1]):
        v = b - a
        cyl(bm, (a + b) / 2, r, v.length * 1.1, seg=6, mi=mi, rot=v.to_track_quat("Z", "Y").to_matrix().to_4x4())


def facing(n, up=(0, 0, 1)):
    """局部 +Z 朝向 n 的旋轉矩陣（4×4）"""
    return Vector(n).normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()


def rose(bm, M, r, mi, mi_core=None, seg=7):
    """玫瑰：花心＋三層花瓣；M 的局部 +Z＝花朝向"""
    mi_core = mi if mi_core is None else mi_core
    ellip(bm, M @ Matrix.Translation((0, 0, 0.18 * r)), (0.32 * r, 0.32 * r, 0.36 * r), seg, mi_core)
    for n_, th, L, w, ph in ((4, 22, 0.55, 0.42, 0.0), (5, 48, 0.70, 0.58, 0.3), (6, 74, 0.82, 0.66, 0.1)):
        for k in range(n_):
            phi = 2 * math.pi * (k + ph) / n_
            Mp = M @ Matrix.Rotation(phi, 4, "Z") @ Matrix.Translation((0.12 * r, 0, 0)) @ Matrix.Rotation(math.radians(th), 4, "Y") \
                @ Matrix.Translation((0, 0, L * r * 0.5))
            ellip(bm, Mp, (w * r * 0.5, w * r * 0.32, L * r * 0.5), seg, mi)


def leaf_sprig(bm, base, direction, length, mi_stem, mi_leaf, side=(1, 0, 0), n=7, leaf_r=0.026, droop=0.35):
    """尤加利：彎垂的細莖＋成對的圓葉"""
    d = Vector(direction).normalized(); sd = Vector(side).normalized()
    pts = []
    for k in range(n + 1):
        u = k / n
        pts.append(Vector(base) + d * length * u + Vector((0, 0, -droop * length * u * u)))
    for a, b in zip(pts, pts[1:]):
        mid = (a + b) / 2; v = b - a
        cyl(bm, mid, 0.0035, v.length, mi=mi_stem, seg=5, rot=v.to_track_quat("Z", "Y").to_matrix().to_4x4())
    for k in range(1, n + 1):
        p = pts[k]; v = (pts[k] - pts[k - 1]).normalized()
        nrm = v.cross(sd).normalized()
        if nrm.y > 0:
            nrm = -nrm
        for s_ in (-1, 1):
            c = p + sd * s_ * leaf_r * 0.9
            rr = leaf_r * (1.15 - 0.4 * k / n)
            ellip(bm, Matrix.Translation(c) @ facing(nrm + sd * s_ * 0.4), (rr, rr, rr * 0.12), 8, mi_leaf)


def arc_pt(u, y):
    """拱門上緣的橢圓弧：u 0→1 由左柱頂到右柱頂"""
    a = math.pi * (1 - u)
    return Vector((POST_X * math.cos(a), y, 2.0 + 0.62 * math.sin(a)))


def build_garden():
    coll_clear("Set_Garden")
    root = coll_new("Set_Garden")
    base = coll_new("G_Base", root)
    random.seed(21)
    M = {k: pmat("G_" + k, c, rough=r, spec=s) for k, c, r, s in (
        ("white", PAL["white"], 0.55, 0.3), ("rose", PAL["rose"], 0.6, 0.3), ("blush", PAL["blush"], 0.6, 0.3),
        ("cream", PAL["cream"], 0.6, 0.3), ("lav", PAL["lav"], 0.6, 0.3), ("core", srgb("#C2606A"), 0.6, 0.3),
        ("euc", srgb("#93AE98"), 0.7, 0.25), ("euc2", srgb("#7F9C88"), 0.7, 0.25), ("stem", srgb("#6E8466"), 0.8, 0.2),
        ("h1", srgb("#5F8457"), 0.9, 0.15), ("h2", srgb("#6E9563"), 0.9, 0.15), ("h3", srgb("#557A50"), 0.9, 0.15),
        ("sand", srgb("#E4D6BF"), 0.95, 0.1), ("stone", srgb("#EFE8DC"), 0.85, 0.2), ("trunk", srgb("#8A6A50"), 0.9, 0.1),
        ("t1", srgb("#86A877"), 0.9, 0.1), ("t2", srgb("#9DB98A"), 0.9, 0.1), ("bloom", srgb("#F2C7C9"), 0.9, 0.1))}
    grass = pmat("G_Lawn", (1, 1, 1), rough=1.0, spec=0.1, img=os.path.join(TEX, "grass.png"), uv=(1, 1))
    # 草地（每 2.5 m 重複一次貼圖）
    bm = bmesh.new(); f = quad(bm, 80, 80)
    lay = bm.loops.layers.uv.verify()
    for lp in f.loops:
        lp[lay].uv = (lp[lay].uv[0] * 32, lp[lay].uv[1] * 32)
    mesh_obj("G_Lawn", bm, grass, base)
    # 小徑：沙色路面＋踏腳石，穿過拱門往後延伸
    bm = MB(); box(bm, Vector((0, -2.5, 0.004)), (1.15, 14.0, 0.008), mi=0)
    for k in range(26):
        y = -8.8 + k * 0.52 + random.uniform(-0.05, 0.05)
        cyl(bm, Vector((random.uniform(-0.18, 0.18), y, 0.012)), random.uniform(0.17, 0.24), 0.012, seg=9, mi=1,
            rot=Matrix.Rotation(random.uniform(0, 3), 4, "Z") @ Matrix.Diagonal((1.0, random.uniform(0.6, 0.85), 1, 1)))
    mesh_obj("G_Path", bm, [M["sand"], M["stone"]], base)
    # 天空穹頂（漸層自發光；不擋陽光、不投影）
    sky = bpy.data.materials.get("G_Sky") or bpy.data.materials.new("G_Sky")
    sky.use_nodes = True; nt = sky.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.0; mr.inputs["From Max"].default_value = 30.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = srgb("#F7EFE4", 1); ramp.color_ramp.elements[1].color = srgb("#BCD5E8", 1)
    ramp.color_ramp.elements.new(0.25).color = srgb("#E3EBEF", 1)
    nt.links.new(tc.outputs["Object"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
    em.inputs["Strength"].default_value = 1.0; nt.links.new(em.outputs[0], out.inputs["Surface"])
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=90.0)
    o = mesh_obj("G_Sky", bm, sky, base, smooth=True)
    o.visible_shadow = False
    # 拱門（白色木作：四根柱、前後兩道橢圓弧、頂上與側面的格柵）
    bm = MB()
    for sx in (-1, 1):
        for y in (ARCH_Y - 0.18, ARCH_Y + 0.18):
            box(bm, Vector((sx * POST_X, y, 1.0)), (0.075, 0.075, 2.0))
        for z in [0.35 + 0.26 * k for k in range(7)]:
            box(bm, Vector((sx * POST_X, ARCH_Y, z)), (0.035, 0.36, 0.03))
        box(bm, Vector((sx * POST_X, ARCH_Y, 0.04)), (0.14, 0.5, 0.08))
    NA = 30
    for y in (ARCH_Y - 0.18, ARCH_Y + 0.18):
        for k in range(NA):
            a, b = arc_pt(k / NA, y), arc_pt((k + 1) / NA, y)
            v = b - a
            box(bm, (a + b) / 2, (0.075, 0.075, v.length + 0.02), rot=v.to_track_quat("Z", "Y").to_matrix().to_4x4())
    for k in range(1, NA, 2):
        p = arc_pt(k / NA, ARCH_Y)
        box(bm, p, (0.03, 0.36, 0.03))
    mesh_obj("G_Arch", bm, M["white"], base)
    # 拱門上的花：左上方一大束往頂端延伸、右柱下方一叢、其他地方點綴；尤加利垂下來
    bm = MB()
    mats = [M["rose"], M["blush"], M["cream"], M["lav"], M["core"], M["stem"], M["euc"], M["euc2"]]

    def add_rose(p, r, n=None):
        n = n or Vector((random.uniform(-0.3, 0.3), -1.0, random.uniform(-0.1, 0.4)))
        c = random.choice((0, 0, 0, 1, 1, 2, 2, 3))
        rose(bm, Matrix.Translation(p) @ facing(n), r, c, mi_core=4 if c == 0 else c)

    for k in range(70):                                  # 左上方的花束：沿弧 0.05～0.55
        u = random.betavariate(2.0, 3.2) * 0.62
        y = ARCH_Y + random.uniform(-0.25, 0.25)
        p = arc_pt(u, y) + Vector((random.uniform(-0.05, 0.05), 0, random.uniform(-0.04, 0.06)))
        add_rose(p, random.uniform(0.045, 0.075), n=(p - Vector((0, ARCH_Y + 0.6, 1.6))))
    for k in range(34):                                  # 左柱往下延伸
        z = 2.0 - random.betavariate(1.2, 2.5) * 1.3
        p = Vector((-POST_X + random.uniform(-0.08, 0.1), ARCH_Y + random.uniform(-0.26, 0.2), z))
        add_rose(p, random.uniform(0.04, 0.065))
    for k in range(40):                                  # 右柱下方一叢
        z = random.betavariate(1.5, 2.2) * 1.2 + 0.1
        p = Vector((POST_X + random.uniform(-0.1, 0.12), ARCH_Y + random.uniform(-0.28, 0.2), z))
        add_rose(p, random.uniform(0.045, 0.075))
    for k in range(14):                                  # 右上方點綴
        u = random.uniform(0.66, 0.95)
        add_rose(arc_pt(u, ARCH_Y - 0.2 + random.uniform(-0.05, 0.05)), random.uniform(0.035, 0.05))
    for k in range(38):                                  # 尤加利：從花束垂下
        u = random.uniform(0.0, 0.7) if k < 26 else random.uniform(0.7, 1.0)
        p = arc_pt(u, ARCH_Y + random.uniform(-0.24, 0.0))
        d = Vector((random.uniform(-0.6, 0.6), random.uniform(-0.5, -0.1), random.uniform(-1.0, -0.2)))
        leaf_sprig(bm, p, d, random.uniform(0.25, 0.5), 5, random.choice((6, 7)), side=(1, 0, 0.3))
    for k in range(18):
        sx = -1 if k < 10 else 1
        z = random.uniform(0.2, 1.9) if sx < 0 else random.uniform(0.1, 1.1)
        p = Vector((sx * POST_X, ARCH_Y - 0.2, z))
        d = Vector((random.uniform(-0.5, 0.5), -0.3, random.uniform(-0.8, 0.5)))
        leaf_sprig(bm, p, d, random.uniform(0.2, 0.38), 5, random.choice((6, 7)), side=(0, 0, 1), droop=0.2)
    mesh_obj("G_ArchFlowers", bm, mats, base, smooth=True)
    # 樹籬牆（拱門兩側）：一顆顆圓葉團堆出來
    bm = MB()
    for sx in (-1, 1):
        x = 1.12
        while x < 7.0:
            for z in (0.2, 0.55, 0.9, 1.22, 1.48):
                for y in (HEDGE_Y0 + 0.1, HEDGE_Y1 - 0.1):
                    r = random.uniform(0.17, 0.23)
                    ball(bm, Vector((sx * (x + random.uniform(-0.04, 0.04)), y + random.uniform(-0.03, 0.03), z + random.uniform(-0.04, 0.04))), r,
                         mi=random.randint(0, 2), seg=10)
            x += 0.2
    mesh_obj("G_Hedge", bm, [M["h1"], M["h2"], M["h3"]], base, smooth=True)
    # 花圃：樹籬前一排低矮花叢（粉、白、薰衣草穗）
    bm = MB()
    for sx in (-1, 1):
        x = 1.25
        while x < 6.8:
            c = Vector((sx * x, HEDGE_Y0 - 0.12, 0.1))
            for _ in range(3):
                ball(bm, c + Vector((random.uniform(-0.1, 0.1), random.uniform(-0.06, 0.06), random.uniform(0, 0.08))), random.uniform(0.1, 0.15), mi=0, seg=8)
            for _ in range(7):
                p = c + Vector((random.uniform(-0.18, 0.18), random.uniform(-0.12, 0.05), random.uniform(0.12, 0.26)))
                kind = random.random()
                if kind < 0.35:                          # 薰衣草穗
                    for j in range(5):
                        ellip(bm, Matrix.Translation(p + Vector((0, 0, 0.022 * j))), (0.012, 0.012, 0.016), 6, 3)
                else:
                    ellip(bm, Matrix.Translation(p), (0.03, 0.03, 0.022), 7, 1 if kind < 0.7 else 2)
            x += 0.32
    mesh_obj("G_FlowerBed", bm, [M["h2"], M["blush"], M["cream"], M["lav"]], base, smooth=True)
    # 背景的樹（樹籬後方）
    bm = MB()
    for k in range(34):
        x = random.uniform(-15, 15); y = random.uniform(2.8, 11.0)
        if abs(x) < 3.6:                                  # 拱門正後方留空，從拱門看出去是深遠的草地
            x = math.copysign(3.6 + random.uniform(0, 2.5), x if x else 1)
        if k >= 26:                                       # 遠景樹林
            x = random.uniform(-6, 6); y = random.uniform(15, 19)
        h = random.uniform(2.6, 4.6)
        cyl(bm, Vector((x, y, h * 0.35)), 0.08, h * 0.7, mi=0, seg=7)
        crown = random.choice((1, 1, 2, 3))
        for _ in range(7):
            ball(bm, Vector((x + random.uniform(-0.7, 0.7), y + random.uniform(-0.5, 0.5), h * 0.75 + random.uniform(-0.3, 0.6))),
                 random.uniform(0.55, 0.95), mi=crown, seg=10)
    mesh_obj("G_Trees", bm, [M["trunk"], M["t1"], M["t2"], M["bloom"]], base, smooth=True)
    # 太陽（暖白、左前上方）＋天光
    sun = bpy.data.objects.get("G_Sun")
    if sun is None:
        sun = bpy.data.objects.new("G_Sun", bpy.data.lights.new("G_Sun", "SUN"))
    if sun.name not in base.objects:
        base.objects.link(sun)
    sun.data.energy = 3.2; sun.data.color = (1.0, 0.96, 0.9); sun.data.angle = math.radians(5)
    try:
        sun.data.use_shadow_jitter = True
    except Exception:
        pass
    sun.rotation_euler = (math.radians(52), 0, math.radians(-32))
    build_bar(coll_new("G_Bar", root))
    build_oldcam(coll_new("G_Cam", root))
    build_tea(coll_new("G_Tea", root))
    build_petals(coll_new("G_Petals", root))
    garden_parts(())


def garden_parts(on):
    for n in ("G_Bar", "G_Cam", "G_Tea"):
        show(n, n in on)


def garden_world():
    world_env(srgb("#E4ECF0"), 0.55)


# ── ③ 押花進度條 ──
BUDS = []           # [(花的空物件, [(花瓣物件, 層, 角度)], 花心物件)]


BUD_SCALE = 0.72                    # 花的大小（2.1 m 的框、間距約 0.2 m → 盛開直徑約 0.19 m）


def bud_x(i):
    """第 i 朵花在把手走到 10%×(i+1)−1% 的位置：99% 時把手剛好停在第 10 朵（半開），每一朵都是把手經過時開"""
    x0 = BAR_X0 + 0.05; x1 = BAR_X1 - 0.05
    return x0 + (x1 - x0) * (0.1 * (i + 1) - 0.01)


def build_bar(c):
    BUDS.clear()
    oak = pmat("G_Oak", srgb("#C79B6C"), rough=0.6, spec=0.3, noise=0.25)
    paper = pmat("G_BarPaper", PAL["paper"], rough=0.9, spec=0.2, noise=0.15, bump=0.08)
    rib = pmat("G_Ribbon", PAL["rose"], rough=0.35, spec=0.6, sheen=0.6)
    L = BAR_X1 - BAR_X0; cx = (BAR_X0 + BAR_X1) / 2
    z0, z1 = BAR_Z - 0.23, BAR_Z + 0.21
    bm = MB()
    box(bm, Vector((cx, BAR_Y + 0.05, (z0 + z1) / 2)), (L, 0.02, z1 - z0), mi=1)                 # 背板（棉紙）
    for z in (z0, z1):
        box(bm, Vector((cx, BAR_Y, z)), (L + 0.1, 0.1, 0.05))                                     # 上下框
    for x in (BAR_X0, BAR_X1):
        box(bm, Vector((x, BAR_Y, (z0 + z1) / 2)), (0.05, 0.1, z1 - z0 + 0.05))                  # 左右框
    for x in (BAR_X0 + 0.45, BAR_X1 - 0.45):                                                      # 兩組 A 字腳
        for sy in (-1, 1):
            p0 = Vector((x, BAR_Y + sy * 0.22, 0.0)); p1 = Vector((x, BAR_Y + sy * 0.02, z0))
            v = p1 - p0
            box(bm, (p0 + p1) / 2, (0.045, 0.045, v.length), rot=v.to_track_quat("Z", "Y").to_matrix().to_4x4())
        box(bm, Vector((x, BAR_Y, 0.28)), (0.035, 0.42, 0.035))
    box(bm, Vector((cx, BAR_Y - 0.035, z0 + 0.07)), (L - 0.08, 0.012, 0.025))                      # 緞帶滑軌
    mesh_obj("G_BarFrame", bm, [oak, paper], c)
    # 填色緞帶（原點在左端，scale.x＝進度）
    bm = bmesh.new(); box(bm, Vector((0.5, 0, 0)), (1.0, 0.01, 0.07))
    fill = mesh_obj("G_BarFill", bm, rib, c)
    fill.location = (BAR_X0 + 0.05, BAR_Y - 0.045, z0 + 0.07)
    # 把手（木頭小牌＋緞帶環）
    bm = bmesh.new(); box(bm, Vector((0, 0, 0)), (0.05, 0.035, 0.085)); cyl(bm, Vector((0, -0.025, 0.0)), 0.016, 0.01, axis="Y", mi=1)
    h = mesh_obj("G_BarHandle", bm, [oak, rib], c)
    # 拖在新郎肩上的緞帶（曲線，每格改控制點）
    cu = bpy.data.curves.get("G_TowRibbon") or bpy.data.curves.new("G_TowRibbon", "CURVE")
    cu.dimensions = "3D"; cu.extrude = 0.018; cu.bevel_depth = 0.0; cu.resolution_u = 10
    cu.splines.clear(); sp = cu.splines.new("BEZIER"); sp.bezier_points.add(4)
    for bp in sp.bezier_points:
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    if "G_TowRibbon" in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects["G_TowRibbon"], do_unlink=True)
    tow = bpy.data.objects.new("G_TowRibbon", cu); c.objects.link(tow)
    cu.materials.clear(); cu.materials.append(rib)
    # 10 朵花：玫瑰色、薰衣草、腮紅粉輪流；花瓣是獨立物件，每格轉角度做開花
    cols = [pmat("G_BudRose", PAL["rose"], rough=0.6), pmat("G_BudLav", PAL["lav"], rough=0.6), pmat("G_BudBlush", PAL["blush"], rough=0.6)]
    sepal = pmat("G_Sepal", srgb("#7E9A6E"), rough=0.8); stamen = pmat("G_Stamen", srgb("#E9C46A"), rough=0.7)
    for i in range(N_BUDS):
        e = empty(f"G_Bud{i}", c, (bud_x(i), BAR_Y - 0.02, BAR_Z))
        e.rotation_euler = (math.radians(90), 0, 0)                  # 局部 +Z → 世界 -Y（朝鏡頭）
        bm = bmesh.new()
        for k in range(5):                                            # 花萼（固定）
            Mp = Matrix.Rotation(2 * math.pi * k / 5, 4, "Z") @ Matrix.Rotation(math.radians(70), 4, "Y") @ Matrix.Translation((0, 0, 0.035 * BUD_SCALE))
            ellip(bm, Mp, (0.02 * BUD_SCALE, 0.006, 0.04 * BUD_SCALE), 6)
        cyl(bm, Vector((0, 0, -0.03)), 0.006, 0.06, seg=6)
        mesh_obj(f"G_Bud{i}_Sepal", bm, sepal, c, smooth=True, parent=e)
        pets = []
        m = cols[i % 3]
        for layer, (n_, L_, w_) in enumerate(((8, 0.13 * BUD_SCALE, 0.11 * BUD_SCALE), (6, 0.095 * BUD_SCALE, 0.09 * BUD_SCALE))):
            for k in range(n_):
                bm = bmesh.new()
                ellip(bm, Matrix.Translation((0, 0, L_ * 0.5)), (w_ * 0.5, w_ * 0.16, L_ * 0.5), 8)
                bmesh.ops.transform(bm, matrix=Matrix.Translation((0, 0, 0)), verts=bm.verts[:])
                # 花瓣中段往內凹一點（杯狀）
                for v in bm.verts:
                    v.co.y += 0.25 * (v.co.x / (w_ * 0.5)) ** 2 * w_ * 0.25
                po = mesh_obj(f"G_Bud{i}_P{layer}_{k}", bm, m, c, smooth=True, parent=e)
                pets.append((po, layer, 2 * math.pi * (k + 0.5 * layer) / n_))
        bm = bmesh.new(); ball(bm, Vector((0, 0, 0.016 * BUD_SCALE)), 0.028 * BUD_SCALE, seg=12)
        core = mesh_obj(f"G_Bud{i}_Core", bm, stamen, c, smooth=True, parent=e)
        BUDS.append((e, pets, core))
    bar_update(0.0, 0.0)


def bloom_set(i, b, shake=0.0):
    """第 i 朵開到 b（0＝花苞、1＝盛開）；shake＝顫動的角度"""
    e, pets, core = BUDS[i]
    for po, layer, phi in pets:
        th0, th1 = (8, 78) if layer == 0 else (4, 52)
        th = th0 + (th1 - th0) * b + shake
        r0 = 0.004 + 0.008 * b
        s = 0.55 + 0.45 * b
        po.matrix_parent_inverse = Matrix.Identity(4)
        po.matrix_basis = Matrix.Rotation(phi, 4, "Z") @ Matrix.Translation((r0, 0, 0.004 * layer)) @ Matrix.Rotation(math.radians(th), 4, "Y") @ Matrix.Diagonal((s, s, s, 1))
    core.scale = (0.4 + 0.6 * b,) * 3


def bar_update(p, t, last_hold=None, shake=0.0):
    """進度 p（0～1）：填色緞帶與把手跟著走；把手經過哪一朵、那一朵就開（把手在花的正中＝半開）。
    last_hold＝第 10 朵卡住時固定的開度（None＝照把手位置）"""
    x0 = BAR_X0 + 0.05; x1 = BAR_X1 - 0.05
    hx = x0 + (x1 - x0) * p
    W = 0.6 * (x1 - x0) / N_BUDS                         # 從花苞到盛開，把手要走的距離
    for i in range(N_BUDS):
        b = max(0.0, min(1.0, (hx - bud_x(i)) / W + 0.5))
        if i == N_BUDS - 1 and last_hold is not None:
            b = last_hold
        bloom_set(i, ease(b), shake if i == N_BUDS - 1 else 0.0)
    O = bpy.data.objects
    O["G_BarFill"].scale = (max(0.001, hx - x0), 1, 1)
    O["G_BarHandle"].location = (hx, BAR_Y - 0.06, BAR_Z - 0.16)
    return Vector((hx, BAR_Y - 0.085, BAR_Z - 0.16))


def tow_update(pts):
    """拖曳緞帶的 5 個控制點（世界座標）：把手 → 垂下 → 肩上 → 肩前的拳頭 → 前面的拳頭（動作庫 ribbon_points 的順序反過來）"""
    sp = bpy.data.curves["G_TowRibbon"].splines[0]
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = p


# ── ⑤ 木製老相機＋三腳架 ──
def build_oldcam(c):
    walnut = pmat("G_Walnut", srgb("#7A5236"), rough=0.5, spec=0.4, noise=0.3)
    leather = pmat("G_Bellows", srgb("#3A2E2A"), rough=0.7, spec=0.2)
    brass = pmat("G_Brass", srgb("#C9A45C"), rough=0.3, spec=0.6, metal=0.9)
    glass = pmat("G_LensGlass", srgb("#1E2228"), rough=0.08, spec=0.9)
    red = pmat("G_RedLamp", srgb("#FF3B30"), rough=0.3, emit=10.0)
    rig = empty("G_OldCam", c, (-2.05, -2.35, 0.0))
    bm = MB()
    for k in range(3):                                           # 三腳架
        a = 2 * math.pi * k / 3 + 0.5
        p0 = Vector((0.42 * math.cos(a), 0.42 * math.sin(a), 0.0)); p1 = Vector((0.05 * math.cos(a), 0.05 * math.sin(a), 1.12))
        v = p1 - p0
        box(bm, (p0 + p1) / 2, (0.035, 0.035, v.length), rot=v.to_track_quat("Z", "Y").to_matrix().to_4x4())
    cyl(bm, Vector((0, 0, 1.14)), 0.09, 0.04, seg=16)
    mesh_obj("G_Tripod", bm, walnut, c, parent=rig)
    head = empty("G_OldCamHead", c, (0, 0, 1.16), parent=rig)       # 機身：局部 -Y＝鏡頭朝向
    cloth = pmat("G_FocusCloth", srgb("#1A1716"), rough=0.95, spec=0.05)
    bm = MB()
    box(bm, Vector((0, 0.08, 0.15)), (0.26, 0.2, 0.28), mi=0)                 # 後半機身（胡桃木）
    for sx in (-1, 1):                                                           # 黃銅包角
        for sz in (0.015, 0.285):
            box(bm, Vector((sx * 0.13, 0.08, sz)), (0.02, 0.21, 0.02), mi=2)
    box(bm, Vector((0, -0.03, 0.01)), (0.24, 0.42, 0.02), mi=0)                 # 底座軌道
    for k in range(8):                                                           # 皮腔：一折一折、越往前越小
        s_ = 1 - 0.045 * k
        box(bm, Vector((0, -0.035 - 0.026 * k, 0.15)), (0.22 * s_ + 0.012 * (k % 2), 0.026, 0.24 * s_ + 0.012 * (k % 2)), mi=1)
    box(bm, Vector((0, -0.25, 0.15)), (0.2, 0.025, 0.22), mi=0)                 # 前板
    cyl(bm, Vector((0, -0.3, 0.15)), 0.055, 0.08, axis="Y", seg=24, mi=2)        # 黃銅鏡筒
    cyl(bm, Vector((0, -0.35, 0.15)), 0.062, 0.03, axis="Y", seg=24, mi=2)       # 鏡頭遮光罩
    cyl(bm, Vector((0, -0.366, 0.15)), 0.048, 0.004, axis="Y", seg=24, mi=3)
    box(bm, Vector((0, 0.08, 0.298)), (0.12, 0.08, 0.012), mi=2)                # 頂上的黃銅片
    mesh_obj("G_OldCamBody", bm, [walnut, leather, brass, glass], c, smooth=False, parent=head)
    bm = MB()                                                                     # 背後的黑色對焦遮光布（只蓋機背、往下垂一點，側面露出胡桃木）
    box(bm, Vector((0, 0.195, 0.2)), (0.27, 0.035, 0.24))
    box(bm, Vector((0, 0.17, 0.302)), (0.27, 0.08, 0.02))
    box(bm, Vector((0, 0.225, 0.04)), (0.25, 0.025, 0.14), rot=Matrix.Rotation(math.radians(-10), 4, "X"))
    mesh_obj("G_OldCamCloth", bm, cloth, c, smooth=False, parent=head)
    bm = bmesh.new(); ball(bm, Vector((0.08, -0.25, 0.29)), 0.022, seg=12)
    mesh_obj("G_OldCamLamp", bm, red, c, smooth=True, parent=head)
    lamp = bpy.data.objects.get("G_RedLight")
    if lamp is None:
        lamp = bpy.data.objects.new("G_RedLight", bpy.data.lights.new("G_RedLight", "POINT"))
    if lamp.name not in c.objects:
        c.objects.link(lamp)
    lamp.parent = head; lamp.location = (0.08, -0.27, 0.285); lamp.data.color = (1, 0.25, 0.2); lamp.data.shadow_soft_size = 0.01
    lamp.data.energy = 2.0
    # 新娘的捧花（⑤ bouquet 動作用；局部 +Z＝花朝向，原點在握把中間）
    rib = bpy.data.materials.get("G_Ribbon") or pmat("G_Ribbon", PAL["rose"], rough=0.35, spec=0.6, sheen=0.6)
    stem = pmat("G_BqStem", srgb("#7E9A6E"), rough=0.8)
    fl = [bpy.data.materials["G_" + k] for k in ("rose", "blush", "cream", "lav")] + [bpy.data.materials["G_euc"]]
    bm = MB()
    cyl(bm, Vector((0, 0, 0)), 0.02, 0.16, mi=0, seg=10)
    cyl(bm, Vector((0, 0, 0.01)), 0.024, 0.06, mi=1, seg=12)
    random.seed(5)
    for k in range(13):
        a = 2.4 * k; r = 0.03 * math.sqrt(k)
        n = Vector((math.cos(a) * r * 4, math.sin(a) * r * 4, 1.0))
        rose(bm, Matrix.Translation((math.cos(a) * r, math.sin(a) * r, 0.12 - r * 0.5)) @ facing(n), 0.045, 2 + k % 4, seg=6)
    for k in range(9):
        a = 2 * math.pi * k / 9
        leaf_sprig(bm, Vector((math.cos(a) * 0.07, math.sin(a) * 0.07, 0.1)), (math.cos(a), math.sin(a), 0.2), 0.12, 0, 6, side=(-math.sin(a), math.cos(a), 0), n=4, droop=0.5)
    mesh_obj("G_Bouquet", bm, [stem, rib] + fl, c, smooth=True)


def oldcam_aim(target):
    """機身的鏡頭（局部 -Y）對準 target"""
    head = bpy.data.objects["G_OldCamHead"]
    bpy.context.view_layer.update()
    d = Vector(target) - (head.matrix_world @ Vector((0, -0.3, 0.15)))
    head.rotation_euler = (math.atan2(-d.z, Vector((d.x, d.y)).length), 0, math.atan2(d.x, -d.y))


def oldcam_lamp(t):
    """REC 紅燈：每 0.5 秒閃一次（亮 0.3 秒）"""
    on = (t % 0.5) < 0.3
    bpy.data.objects["G_RedLight"].data.energy = 2.0 if on else 0.0
    m = bpy.data.materials["G_RedLamp"]
    next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Emission Strength"].default_value = 10.0 if on else 0.3


# ── ⑦ 下午茶高腳桌 ──
TEA_C = Vector((0.08, -0.62, 0.0))
TEA_TOP = 0.98
BOARD_W, BOARD_H = 0.30, 0.23
BOARD_LOC = (0.0, -0.165, TEA_TOP + 0.005)          # 桌子局部座標（桌面前緣正中；兩側留給杯子和點心）


def build_tea(c):
    white = pmat("G_TeaWhite", PAL["white"], rough=0.5, spec=0.4)
    gold = pmat("G_TeaGold", PAL["gold"], rough=0.3, spec=0.6, metal=0.8)
    lace = pmat("G_Lace", (1, 1, 1), rough=0.8, spec=0.2, img=os.path.join(TEX, "lace.png"), img_alpha=True, uv=(9, 1))
    cloth = pmat("G_Cloth", srgb("#FBF8F2"), rough=0.85, spec=0.2, noise=0.1)
    scone = pmat("G_Scone", srgb("#D7A66A"), rough=0.8, spec=0.2, noise=0.35)
    cream = pmat("G_Cream", srgb("#FFF8EA"), rough=0.5)
    jam = pmat("G_Jam", srgb("#B8424E"), rough=0.3, spec=0.6)
    mac = [pmat("G_Mac" + k, v, rough=0.6) for k, v in (("Lav", PAL["lav"]), ("Rose", PAL["blush"]), ("Sage", srgb("#B9CDB2")), ("Cream", srgb("#F6E7C8")))]
    pot = pmat("G_Teapot", srgb("#F3D9DA"), rough=0.35, spec=0.6)
    board = pmat("G_Chalk", srgb("#2F3D35"), rough=0.9, spec=0.1, noise=0.25)
    oak = bpy.data.materials.get("G_Oak") or pmat("G_Oak", srgb("#C79B6C"), rough=0.6, noise=0.25)
    chalk = pmat("G_ChalkText", srgb("#F4F1E8"), rough=0.9, spec=0.1, noise=0.35)
    rig = empty("G_Tea", c, TEA_C)
    bm = MB()
    cyl(bm, Vector((0, 0, TEA_TOP - 0.015)), 0.32, 0.03, seg=48, mi=0)              # 桌面
    cyl(bm, Vector((0, 0, TEA_TOP * 0.5)), 0.025, TEA_TOP - 0.03, seg=12, mi=1)       # 細柱
    for k in range(3):                                                                # 三腳底座（佔地小，裙擺不會穿過）
        a = 2 * math.pi * k / 3 + math.pi / 2
        box(bm, Vector((0.1 * math.cos(a), 0.1 * math.sin(a), 0.02)), (0.2, 0.03, 0.025), mi=1, rot=Matrix.Rotation(a, 4, "Z"))
    mesh_obj("G_TeaTable", bm, [white, gold], c, smooth=True, parent=rig)
    bm = bmesh.new(); cyl(bm, Vector((0, 0, TEA_TOP + 0.002)), 0.335, 0.004, seg=64)
    mesh_obj("G_TeaCloth", bm, cloth, c, smooth=True, parent=rig)
    bm = bmesh.new()                                                                  # 蕾絲垂邊（12 cm）
    res = bmesh.ops.create_cone(bm, cap_ends=False, segments=96, radius1=0.355, radius2=0.336, depth=0.12)
    bmesh.ops.translate(bm, vec=Vector((0, 0, TEA_TOP - 0.058)), verts=res["verts"])
    lay = bm.loops.layers.uv.verify()
    for f in bm.faces:
        for lp in f.loops:
            co = lp.vert.co
            lp[lay].uv = ((math.atan2(co.y, co.x) / (2 * math.pi)) % 1.0, (co.z - (TEA_TOP - 0.118)) / 0.12)
    mesh_obj("G_TeaLace", bm, lace, c, smooth=True, parent=rig)
    # 兩層點心架（左前）：下層司康、上層馬卡龍
    st = Vector((-0.06, 0.15, TEA_TOP))                                              # 點心架：後方偏左
    bm = MB()
    cyl(bm, st + Vector((0, 0, 0.18)), 0.006, 0.36, seg=8, mi=1)
    cyl(bm, st + Vector((0, 0, 0.02)), 0.13, 0.008, seg=40, mi=0)
    cyl(bm, st + Vector((0, 0, 0.21)), 0.09, 0.008, seg=40, mi=0)
    ball(bm, st + Vector((0, 0, 0.37)), 0.015, mi=1, seg=10)
    mesh_obj("G_Stand", bm, [white, gold], c, smooth=True, parent=rig)
    bm = MB()
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4
        p = st + Vector((0.075 * math.cos(a), 0.075 * math.sin(a), 0.048))
        cyl(bm, p, 0.03, 0.04, seg=14, mi=0, r2=0.026)
        ball(bm, p + Vector((0, 0, 0.026)), (0.018, 0.018, 0.01), mi=1, seg=10)
        ball(bm, p + Vector((0.004, 0, 0.034)), (0.008, 0.008, 0.005), mi=2, seg=8)
    mesh_obj("G_Scones", bm, [scone, cream, jam], c, smooth=True, parent=rig)
    bm = MB()
    for k in range(6):
        a = 2 * math.pi * k / 6
        p = st + Vector((0.055 * math.cos(a), 0.055 * math.sin(a), 0.235))
        for dz, r_, mi_ in ((0.0, 0.019, k % 4), (0.008, 0.016, 4), (0.016, 0.019, k % 4)):
            cyl(bm, p + Vector((0, 0, dz)), r_, 0.007, seg=16, mi=mi_)
    mesh_obj("G_Macarons", bm, mac + [cream], c, smooth=True, parent=rig)
    # 手上要拿的一顆司康、一顆馬卡龍（品嚐用；每格跟著手走）
    bm = bmesh.new(); cyl(bm, Vector((0, 0, 0)), 0.03, 0.04, seg=14, mi=0, r2=0.026); ball(bm, Vector((0, 0, 0.026)), (0.018, 0.018, 0.01), mi=1, seg=10)
    mesh_obj("G_HandScone", bm, [scone, cream], c, smooth=True)
    bm = MB()
    for dz, r_, mi_ in ((0.0, 0.019, 0), (0.008, 0.016, 1), (0.016, 0.019, 0)):
        cyl(bm, Vector((0, 0, dz)), r_, 0.007, seg=16, mi=mi_)
    mesh_obj("G_HandMacaron", bm, [mac[1], cream], c, smooth=True)
    # 茶壺（右前）
    tp = Vector((0.11, 0.17, TEA_TOP))                                               # 茶壺：後方偏右
    bm = MB()
    ball(bm, tp + Vector((0, 0, 0.075)), (0.085, 0.085, 0.07), seg=20)
    cyl(bm, tp + Vector((0, 0, 0.147)), 0.035, 0.02, seg=16)
    ball(bm, tp + Vector((0, 0, 0.165)), 0.012, seg=10, mi=1)
    sp_ = Vector((0.1, 0, 0.1))
    cyl(bm, tp + sp_, 0.012, 0.09, seg=10, r2=0.007, rot=Matrix.Rotation(math.radians(-50), 4, "Y"))
    ring(bm, tp + Vector((-0.1, 0, 0.08)), 0.035, 0.007, Matrix.Rotation(math.radians(90), 4, "X"), seg=14)   # 把手
    mesh_obj("G_Teapot", bm, [pot, gold], c, smooth=True, parent=rig)
    # 手寫小黑板（桌面後方，正對鏡頭、往後仰 8°）
    bd = empty("G_Board", c, BOARD_LOC, parent=rig)                    # 桌面右前方、往後仰 10°：推近時前面沒有東西擋字
    bd.rotation_euler = (math.radians(-10), 0, 0)
    bm = MB()
    BW, BH = BOARD_W, BOARD_H
    box(bm, Vector((0, 0, BH / 2 + 0.01)), (BW, 0.012, BH), mi=0)
    for z in (0.01, BH + 0.01):
        box(bm, Vector((0, -0.004, z)), (BW + 0.02, 0.02, 0.022), mi=1)
    for x in (-BW / 2 - 0.004, BW / 2 + 0.004):
        box(bm, Vector((x, -0.004, BH / 2 + 0.01)), (0.022, 0.02, BH + 0.02), mi=1)
    mesh_obj("G_BoardPanel", bm, [board, oak], c, parent=bd)
    for k, line in enumerate(("喝酒不開車", "開車不喝酒")):
        for j, ch in enumerate(line):
            o = text_obj(f"G_Chalk_{k}_{j}", ch, 0.054, (-0.114 + j * 0.057, -0.0075, 0.178 - k * 0.075), (math.radians(90), 0, 0), chalk,
                         font=font_path("kaiu.ttf"))
            o.parent = bd
            for coll_ in list(o.users_collection):
                coll_.objects.unlink(o)
            c.objects.link(o)
    # 粉筆小計程車（右下角）：車身輪廓、車窗、車頂燈、兩個輪子
    bm = MB()
    S_ = 0.75
    segs = (((0.0, 0.0), (0.07, 0.0)), ((0.0, 0.0), (0.0, 0.022)), ((0.07, 0.0), (0.07, 0.022)), ((0.0, 0.022), (0.016, 0.042)),
            ((0.016, 0.042), (0.054, 0.042)), ((0.054, 0.042), (0.07, 0.022)), ((0.0, 0.022), (0.07, 0.022)), ((0.035, 0.022), (0.035, 0.042)),
            ((0.027, 0.042), (0.027, 0.05)), ((0.027, 0.05), (0.043, 0.05)), ((0.043, 0.05), (0.043, 0.042)))
    ox, oz = BOARD_W / 2 - 0.075, 0.03
    for a, b in segs:
        pa = Vector((ox + a[0] * S_, -0.0075, oz + a[1] * S_)); pb = Vector((ox + b[0] * S_, -0.0075, oz + b[1] * S_)); v = pb - pa
        box(bm, (pa + pb) / 2, (0.0028, 0.002, v.length + 0.0025), rot=v.to_track_quat("Z", "Y").to_matrix().to_4x4())
    for wx in (0.016, 0.054):
        ring(bm, Vector((ox + wx * S_, -0.0075, oz)), 0.0075, 0.0013, Matrix.Rotation(math.radians(90), 4, "X"), seg=12)
    mesh_obj("G_ChalkTaxi", bm, chalk, c, parent=bd)
    # 香檳杯（新郎、新娘各一；每格跟著手走）
    glass = pmat("G_Glass", srgb("#F4F8FA"), rough=0.05, spec=1.0, alpha=0.28)
    fizz = pmat("G_Champagne", srgb("#E9C877"), rough=0.1, spec=0.8, alpha=0.75)
    for who_ in ("groom", "bride"):
        bm = bmesh.new()
        cyl(bm, Vector((0, 0, 0.0)), 0.032, 0.004, seg=20, mi=0)          # 杯腳底座
        cyl(bm, Vector((0, 0, 0.045)), 0.004, 0.09, seg=8, mi=0)           # 杯梗
        cyl(bm, Vector((0, 0, 0.14)), 0.028, 0.1, seg=20, mi=0, r2=0.033)   # 杯身
        cyl(bm, Vector((0, 0, 0.125)), 0.025, 0.065, seg=20, mi=1, r2=0.028)
        mesh_obj(f"G_Flute_{who_}", bm, [glass, fizz], c, smooth=True)


def chalk_reveal(t0, t, per=0.12):
    """粉筆字一個字一個字出現（兩行接著寫）；t0＝開始寫的秒數"""
    k = 0
    for line in range(2):
        for j in range(5):
            o = bpy.data.objects.get(f"G_Chalk_{line}_{j}")
            if o:
                show_t = t0 + k * per
                o.hide_render = t < show_t
                o.scale = (1, 1, 1)
            k += 1
    taxi = bpy.data.objects.get("G_ChalkTaxi")
    if taxi:
        taxi.hide_render = t < t0 + 10 * per + 0.3


# ── 花瓣（飄落、迸出）──
PET = {}


def build_petals(c, n=220):
    mats = [pmat("G_Petal" + k, (1, 1, 1), rough=0.6, spec=0.2, img=os.path.join(TEX, f"petal_{k.lower()}.png"), img_alpha=True)
            for k in ("Rose", "Blush", "Lav")]
    bm = bmesh.new()
    for i in range(n):
        quad(bm, 0.07, 0.05, (0, 0, -50 - i * 0.01), mi=i % 3)
    o = mesh_obj("G_Petals", bm, mats, c)
    o.visible_shadow = False
    PET.clear(); PET["n"] = n


def petals_update(t, emit):
    """emit(i) → None（不出現）或 (出現秒數, 起點, 初速)。花瓣以終端速度慢慢飄落、左右擺、翻轉"""
    o = bpy.data.objects["G_Petals"]; me = o.data
    rnd = random.Random(7)
    co = []
    for i in range(PET["n"]):
        spin = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized()
        w = rnd.uniform(2.0, 5.0); ph = rnd.uniform(0, 6.28); sz = rnd.uniform(0.7, 1.2)
        e = emit(i, rnd)
        corners = [Vector((-0.035, -0.025, 0)), Vector((0.035, -0.025, 0)), Vector((0.035, 0.025, 0)), Vector((-0.035, 0.025, 0))]
        if e is None or t < e[0]:
            co += [(0, 0, -50)] * 4
            continue
        t0, p0, v0 = e
        dt = t - t0
        drag = 1.6                                       # 空氣阻力：初速很快衰減，之後以 0.6 m/s 落下
        vt = Vector((0, 0, -0.6))
        p = Vector(p0) + (Vector(v0) - vt) * (1 - math.exp(-drag * dt)) / drag + vt * dt
        p += Vector((0.06 * math.sin(w * dt + ph), 0.04 * math.cos(0.7 * w * dt + ph), 0))
        if p.z < 0.003:
            p.z = 0.003
        R = Matrix.Rotation(dt * w + ph, 3, spin)
        if p.z <= 0.0031:
            R = Matrix.Rotation(ph, 3, "Z")
        co += [tuple(p + R @ (c_ * sz)) for c_ in corners]
    flat = [x for v in co for x in v]
    me.vertices.foreach_set("co", flat); me.update()
