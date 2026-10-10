# 情境版（preview-v2，2026-10-06）新增的道具：② 充氣玩具槌、⑦ 圓桌晚餐（落地長桌巾、餐點、紅酒、椅子、畫架小黑板）、⑤ 路人甲的手機。
# 都放在 Set_Garden 底下自己的子集合（V2_Mallet／V2_Dinner／V2_Phone），由 shots_v2.py 依幕開關；既有的 G_Bar／G_Cam／G_Tea 不動。
# 道具的局部座標照動作庫 held_prop() 的握點慣例（見 actions-catalog.md「道具掛點 held_prop」）：
#   玩具槌：原點＝握點（拳心）、局部 +Z＝槌柄往槌頭、局部 +Y＝槌面朝向（槌頭圓柱的軸）；槌頭中心＝握點 + 0.40 m × Z。
#   紅酒杯：原點＝握點（杯腳中段）、局部 +Z＝杯子往上；杯身中心 +8.5 cm、杯緣 +13.5 cm（半徑 4.2 cm）、杯底 −4.2 cm。
#   叉子：原點＝握點、局部 +Z＝往叉尖；叉尖 +11.5 cm、柄尾 −6.5 cm；食物在叉尖往回 1.8 cm。
#   手機：原點＝中心、局部 +Y＝手機上方、局部 +Z＝背面朝外（螢幕朝 −Z＝朝拿手機的人）。
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

V2 = {}                      # 建好的物件、尺寸


def _lathe(bm, prof, seg=32, axis="Z", mi=0, M=None, caps=True):
    """旋轉體：prof＝[(r, h), …]（由下到上），axis＝旋轉軸；M＝再整個變換；caps＝兩端不在軸上時要不要封口。回傳新頂點"""
    M = M or Matrix.Identity(4)
    Rax = {"Z": Matrix.Identity(4), "Y": Matrix.Rotation(-math.pi / 2, 4, "X"), "X": Matrix.Rotation(math.pi / 2, 4, "Y")}[axis]
    rings = []
    for r, h in prof:
        if r < 1e-6:                                    # 在軸上：只放一個頂點（極點）
            rings.append(bm.verts.new(M @ Rax @ Vector((0.0, 0.0, h))))
            continue
        ring = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            ring.append(bm.verts.new(M @ Rax @ Vector((r * math.cos(a), r * math.sin(a), h))))
        rings.append(ring)
    for ra, rb in zip(rings, rings[1:]):
        pa, pb = not isinstance(ra, list), not isinstance(rb, list)
        if pa and pb:
            continue
        for i in range(seg):
            j = (i + 1) % seg
            vs = (ra, rb[j], rb[i]) if pa else ((ra[i], ra[j], rb) if pb else (ra[i], ra[j], rb[j], rb[i]))
            f = bm.faces.new(vs); f.material_index = mi
    if caps and isinstance(rings[0], list):
        f = bm.faces.new(list(reversed(rings[0]))); f.material_index = mi
    if caps and isinstance(rings[-1], list):
        f = bm.faces.new(rings[-1]); f.material_index = mi
    return rings


def _round_prof(r, half, bev, n=5, bulge=0.0):
    """圓角圓柱的輪廓（沿軸 −half～+half，半徑 r，邊緣圓角 bev；bulge＝中段鼓起，像充氣）"""
    pr = [(0.0, -half)]
    for k in range(n + 1):
        a = math.pi / 2 * k / n
        pr.append((r - bev + bev * math.sin(a), -half + bev - bev * math.cos(a)))
    for k in range(1, 6):
        u = k / 6
        pr.append((r + bulge * math.sin(math.pi * u), -half + bev + (2 * half - 2 * bev) * u))
    for k in range(n + 1):
        a = math.pi / 2 * k / n
        pr.append((r - bev + bev * math.cos(a), half - bev + bev * math.sin(a)))
    pr.append((0.0, half))
    return pr


# ══════════ ② 充氣玩具槌 ══════════
MALLET_LEN = 0.40            # 握點 → 槌頭中心（和動作庫 held_prop 相同）
MALLET_HEAD = dict(r=0.06, len=0.24)     # 槌頭直徑 12 cm、長 24 cm（使用者指定 24×12）


def build_mallet(c):
    lav = pmat("V2_MalletHead", PAL["lav"], rough=0.28, spec=0.55, coat=0.35)
    lav2 = pmat("V2_MalletSeam", srgb("#A68DBA"), rough=0.35, spec=0.5)
    rose = pmat("V2_MalletHandle", PAL["rose"], rough=0.3, spec=0.55, coat=0.3)
    rig = empty("V2_Mallet", c)
    # 握把：柄尾在握點後 4 cm（圓頭）、一路伸進槌頭；三圈充氣的鼓起
    bm = bmesh.new()
    pr = [(0.0, -0.052), (0.012, -0.050), (0.019, -0.044), (0.022, -0.036)]
    for k in range(1, 30):
        z = -0.036 + (MALLET_LEN - 0.03 + 0.036) * k / 29
        pr.append((0.0205 + 0.0025 * abs(math.sin(math.pi * (z + 0.04) / 0.125)), z))
    _lathe(bm, pr, seg=20, mi=0)
    o = mesh_obj("V2_MalletHandle", bm, rose, c, smooth=True, parent=rig)
    # 槌頭：原點在槌頭中心，圓柱軸＝局部 Y（敲中時壓扁用 scale.y）
    head = empty("V2_MalletHeadPivot", c, (0, 0, MALLET_LEN), parent=rig)
    bm = bmesh.new()
    _lathe(bm, _round_prof(MALLET_HEAD["r"], MALLET_HEAD["len"] / 2, 0.028, bulge=0.004), seg=36, axis="Y", mi=0)
    for y in (-0.072, 0.072):                                        # 兩圈熱壓接縫（深一點的薰衣草）
        _lathe(bm, [(MALLET_HEAD["r"] + 0.0035, y - 0.004), (MALLET_HEAD["r"] + 0.0035, y + 0.004)], seg=36, axis="Y", mi=1, caps=False)
    mesh_obj("V2_MalletHeadMesh", bm, [lav, lav2], c, smooth=True, parent=head)
    V2["mallet"] = rig; V2["mallet_head"] = head
    return rig


def mallet_set(M, squash=0.0, show=True):
    """M＝握點的世界矩陣（held_prop('mallet') 的結果）；squash 0～1＝敲中時槌頭壓扁的程度"""
    rig = V2["mallet"]; head = V2["mallet_head"]
    rig.matrix_world = M
    s = squash
    head.scale = (1 + 0.08 * s, 1 - 0.16 * s, 1 + 0.08 * s)
    for o in [rig] + list(rig.children_recursive):
        o.hide_render = not show; o.hide_viewport = not show


# ══════════ ⑤ 路人甲的手機 ══════════
def build_phone(c):
    case = pmat("V2_PhoneCase", srgb("#1E2433"), rough=0.35, spec=0.5)
    scr = pmat("V2_PhoneScreen", srgb("#CFE3F4"), rough=0.15, spec=0.6, emit=2.2)
    lens = pmat("V2_PhoneLens", srgb("#0B0C10"), rough=0.1, spec=0.9)
    rig = empty("V2_Phone", c)
    w, h, t, rr = 0.074, 0.152, 0.008, 0.010
    bm = MB()
    # 圓角長方體：中間一塊＋四角圓柱
    box(bm, Vector((0, 0, 0)), (w - 2 * rr, h, t))
    box(bm, Vector((0, 0, 0)), (w, h - 2 * rr, t))
    for sx in (-1, 1):
        for sy in (-1, 1):
            cyl(bm, Vector((sx * (w / 2 - rr), sy * (h / 2 - rr), 0)), rr, t, seg=12)
    box(bm, Vector((0, 0, -t / 2 - 0.0004)), (w - 0.006, h - 0.008, 0.0008), mi=1)        # 螢幕（朝 −Z）
    box(bm, Vector((-0.018, 0.052, t / 2 + 0.002)), (0.026, 0.034, 0.004), mi=0)          # 背面鏡頭模組
    for dx, dy in ((-0.024, 0.060), (-0.012, 0.060), (-0.024, 0.044)):
        cyl(bm, Vector((dx, dy, t / 2 + 0.0045)), 0.0045, 0.002, seg=12, mi=2)
    mesh_obj("V2_PhoneMesh", bm, [case, scr, lens], c, smooth=False, parent=rig)
    V2["phone"] = rig
    return rig


def phone_set(C, up, fwd, show=True):
    """C＝中心、up＝手機上方、fwd＝背面朝外的方向（世界座標）"""
    y = Vector(up).normalized(); z = Vector(fwd) - y * Vector(fwd).dot(y); z.normalize(); x = y.cross(z)
    M = Matrix((x, y, z)).transposed().to_4x4(); M.translation = Vector(C)
    rig = V2["phone"]; rig.matrix_world = M
    for o in [rig] + list(rig.children_recursive):
        o.hide_render = not show; o.hide_viewport = not show


# ══════════ ⑦ 圓桌晚餐 ══════════
DIN = dict(top=0.73, radius=0.40, seat=0.46)       # 桌面高、半徑、椅面高（和動作庫 V12_TABLE、SEAT_H 相同）
GLASS_D = dict(bowl=0.085, rim=0.135, rim_r=0.042, base=-0.042, fill=0.068)   # fill＝紅酒液面離握點（杯身內 1/3 滿）


def _glass_prof():
    """紅酒杯外形（握點在原點、Z 往上）：杯底 → 杯腳 → 杯身（最寬在杯身中心略下）→ 杯緣"""
    b = GLASS_D["base"]
    return [(0.0, b), (0.036, b), (0.036, b + 0.003), (0.010, b + 0.006), (0.0042, b + 0.012), (0.0040, 0.020),
            (0.0045, 0.030), (0.012, 0.034), (0.026, 0.042), (0.038, 0.056), (0.045, 0.074), (0.046, 0.088),
            (0.0445, 0.106), (0.0430, 0.122), (GLASS_D["rim_r"], GLASS_D["rim"])]


def _wine_prof():
    """杯身內側的液體（封閉的旋轉體，比杯壁內縮 1.5 mm）：之後每格用水平面切出液面"""
    pr = [(0.0, 0.0335)]
    for r, h in _glass_prof()[7:]:
        pr.append((max(0.0, r - 0.0015), h))
    pr.append((0.0, GLASS_D["rim"]))
    return pr


def build_dinner(c, center):
    """圓桌晚餐：center＝桌心 (x, y)。回傳 dict（物件、桌上道具的世界座標）"""
    cx, cy = center
    TOP, R = DIN["top"], DIN["radius"]
    random.seed(12)
    M = dict(
        cloth=pmat("V2_Cloth", srgb("#FBF6EE"), rough=0.88, spec=0.2, noise=0.10, sheen=0.4),
        band=pmat("V2_ClothBand", PAL["lav"], rough=0.6, spec=0.3, sheen=0.5),
        nap=pmat("V2_Napkin", PAL["sage"], rough=0.85, spec=0.2, noise=0.12),
        ring=pmat("V2_NapRing", PAL["gold"], rough=0.3, spec=0.6, metal=0.8),
        china=pmat("V2_China", srgb("#FFFDF8"), rough=0.25, spec=0.6),
        rim=pmat("V2_ChinaRim", PAL["gold"], rough=0.3, spec=0.6, metal=0.8),
        wood=pmat("V2_ChairWood", PAL["white"], rough=0.55, spec=0.3),
        cushion=pmat("V2_Cushion", PAL["blush"], rough=0.8, spec=0.2, sheen=0.5),
        oak=bpy.data.materials.get("G_Oak") or pmat("G_Oak", srgb("#C79B6C"), rough=0.6, noise=0.25),
        board=pmat("V2_Chalk", srgb("#2F3D35"), rough=0.9, spec=0.1, noise=0.25),
        bottle=pmat("V2_Bottle", srgb("#24331F"), rough=0.12, spec=0.8, coat=0.6),
        foil=pmat("V2_Foil", srgb("#7A1E2C"), rough=0.35, spec=0.6, metal=0.5),
        label=pmat("V2_Label", PAL["paper"], rough=0.8, spec=0.2, noise=0.15),
        labr=pmat("V2_LabelRose", PAL["rose"], rough=0.7, spec=0.2),
        glass=pmat("V2_Glass", srgb("#F4F8FA"), rough=0.04, spec=1.0, alpha=0.22),
        wine=pmat("V2_Wine", srgb("#6E1424"), rough=0.08, spec=0.8, alpha=0.92),
        steak=pmat("V2_Steak", srgb("#7A4A33"), rough=0.6, spec=0.3, noise=0.35),
        steak_in=pmat("V2_SteakIn", srgb("#C46A5E"), rough=0.6, spec=0.3),
        sauce=pmat("V2_Sauce", srgb("#5A2E22"), rough=0.2, spec=0.6),
        green=pmat("V2_Greens", srgb("#6F9A5B"), rough=0.7, spec=0.2),
        carrot=pmat("V2_Carrot", srgb("#E39A4E"), rough=0.6, spec=0.3),
        potato=pmat("V2_Potato", srgb("#E8C987"), rough=0.6, spec=0.3, noise=0.25),
        cake=pmat("V2_Cake", srgb("#F6E7C8"), rough=0.6, spec=0.3),
        cream=pmat("V2_Cream", srgb("#FFF8EA"), rough=0.45, spec=0.4),
        berry=pmat("V2_Berry", srgb("#C2364A"), rough=0.3, spec=0.6),
        macl=pmat("V2_MacLav", PAL["lav"], rough=0.6), macr=pmat("V2_MacRose", PAL["blush"], rough=0.6),
        macs=pmat("V2_MacSage", srgb("#B9CDB2"), rough=0.6),
        grape=pmat("V2_Grape", srgb("#6C3A62"), rough=0.25, spec=0.6),
        grape2=pmat("V2_GrapeG", srgb("#A9C46A"), rough=0.25, spec=0.6),
        orange=pmat("V2_Orange", srgb("#F2A03D"), rough=0.4, spec=0.5),
        kiwi=pmat("V2_Kiwi", srgb("#8DB14A"), rough=0.4, spec=0.4),
        silver=pmat("V2_Silver", srgb("#D8D8DC"), rough=0.2, spec=0.8, metal=1.0),
        candle=pmat("V2_Candle", PAL["cream"], rough=0.6, spec=0.3),
    )
    rig = empty("V2_Table", c, (cx, cy, 0.0))
    # 桌面（被桌巾蓋住，只是撐著）
    bm = MB(); cyl(bm, Vector((0, 0, TOP - 0.02)), R, 0.03, seg=48); cyl(bm, Vector((0, 0, TOP / 2)), 0.05, TOP - 0.04, seg=12)
    mesh_obj("V2_TableTop", bm, M["china"], c, parent=rig)
    # 落地長桌巾：桌面圓片 → 繞過桌緣 → 往下垂到地面、下襬微微外擴＋垂褶（越往下褶越深），地上積一點
    bm = bmesh.new()
    seg = 128; NF = 22
    rows = []
    prof = [(0.0, TOP + 0.004)]
    for k in range(1, 9):
        prof.append((R * k / 8, TOP + 0.004))
    for k in range(1, 7):                                   # 桌緣圓角
        a = math.pi / 2 * k / 6
        prof.append((R + 0.012 * math.sin(a), TOP + 0.004 - 0.012 * (1 - math.cos(a))))
    for k in range(1, 25):                                  # 垂下
        u = k / 24
        prof.append((R + 0.012 + 0.05 * u ** 1.6, TOP - 0.008 - (TOP - 0.008 - 0.004) * u))
    prof.append((R + 0.085, 0.003))
    pole = bm.verts.new((0.0, 0.0, TOP + 0.004))
    for j, (r0, z) in enumerate(prof[1:]):
        ring = []
        drop = max(0.0, (TOP - 0.01 - z) / (TOP - 0.01)) if r0 > R else 0.0
        for i in range(seg):
            a = 2 * math.pi * i / seg
            fold = 0.016 * drop ** 0.8 * math.sin(NF * a + 0.6 * math.sin(3 * a))
            rr = r0 + fold
            ring.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), z)))
        rows.append(ring)
    for i in range(seg):
        bm.faces.new((pole, rows[0][i], rows[0][(i + 1) % seg]))
    for ra, rb in zip(rows, rows[1:]):
        for i in range(seg):
            bm.faces.new((ra[i], rb[i], rb[(i + 1) % seg], ra[(i + 1) % seg]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh_obj("V2_Tablecloth", bm, M["cloth"], c, smooth=True, parent=rig)
    # 桌巾上的薰衣草緞帶（桌緣下 9 cm 繞一圈，像垂飾的腰帶）
    bm = bmesh.new()
    pr = []
    for z, dr in ((TOP - 0.075, 0.0), (TOP - 0.100, 0.0)):
        u = (TOP - 0.008 - z) / (TOP - 0.012)
        pr.append((R + 0.012 + 0.05 * u ** 1.6 + 0.004, z))
    _lathe(bm, list(reversed(pr)), seg=128, caps=False)
    mesh_obj("V2_ClothBand", bm, M["band"], c, smooth=True, parent=rig)
    S = {}

    def W(p):
        return Vector((cx + p[0], cy + p[1], p[2] if len(p) > 2 else TOP))

    def plate(name, p, r, foot=0.006):
        bm = bmesh.new()
        _lathe(bm, [(0.0, 0.0), (r * 0.55, 0.0), (r * 0.6, 0.004), (r * 0.62, 0.006), (r * 0.9, 0.010), (r, 0.014), (r * 0.99, 0.016),
                    (r * 0.88, 0.0125), (r * 0.6, 0.0085), (0.0, 0.0085)], seg=48)
        o = mesh_obj(name, bm, M["china"], c, smooth=True, parent=rig)
        o.location = (p[0], p[1], TOP + 0.004)
        bm = bmesh.new(); _lathe(bm, [(r * 0.955, 0.0148), (r * 0.985, 0.0158)], seg=48, caps=False)
        mesh_obj(name + "Rim", bm, M["rim"], c, smooth=True, parent=o)
        return o
    V2["din_mats"] = M
    V2["din_center"] = Vector((cx, cy, 0.0))
    V2["din_W"] = W
    V2["din_plate"] = plate
    return rig, M, W, plate


def build_dinner_items(c, layout):
    """桌上的東西（位置由 shots_v2 依座位算好傳進來，桌心座標）：layout＝dict(main, desserts[], fruit, bottle, napkins[], board, chairs[])"""
    rig = bpy.data.objects["V2_Table"]; M = V2["din_mats"]; plate = V2["din_plate"]; TOP = DIN["top"]
    random.seed(31)
    # 主餐大盤：牛排切片＋烤蔬菜＋醬汁
    p = layout["main"]
    o = plate("V2_MainPlate", p, 0.150)
    bm = MB(); base = Vector((0, 0, 0.0085))
    for k in range(5):                                         # 五片牛排斜切，排成一列
        a = math.radians(-35); d = Vector((math.cos(a), math.sin(a), 0))
        q = base + d * (-0.05 + 0.025 * k) + Vector((0.01, 0.02, 0.012))
        rot = Matrix.Rotation(a, 4, "Z") @ Matrix.Rotation(math.radians(18), 4, "Y")
        box(bm, q, (0.020, 0.062, 0.022), rot=rot, mi=0)
        box(bm, q + rot.to_3x3() @ Vector((0.0105, 0, 0)), (0.0012, 0.054, 0.016), rot=rot, mi=1)
    ball(bm, base + Vector((-0.03, -0.055, 0.0)), (0.05, 0.03, 0.004), mi=2, seg=14)      # 醬汁
    for k in range(6):                                          # 烤蔬菜
        q = base + Vector((-0.07 + random.uniform(-0.015, 0.015), -0.02 + 0.016 * k, 0.012))
        ball(bm, q, random.uniform(0.010, 0.014), mi=3 + k % 3, seg=10)
    for k in range(3):                                          # 一小把綠葉
        ball(bm, base + Vector((0.055 + 0.012 * k, -0.06 + 0.01 * k, 0.012)), (0.018, 0.012, 0.008), mi=3, seg=10)
    mesh_obj("V2_Steak", bm, [M["steak"], M["steak_in"], M["sauce"], M["green"], M["carrot"], M["potato"]], c, smooth=True, parent=o)
    # 點心小盤（三盤：小蛋糕、馬卡龍、莓果塔）
    kinds = ["cake", "mac", "tart"]
    for i, q in enumerate(layout["desserts"]):
        o = plate(f"V2_Dessert{i}", q, 0.075)
        bm = MB(); b0 = Vector((0, 0, 0.0085)); kind = kinds[i % 3]
        if kind == "cake":
            cyl(bm, b0 + Vector((0, 0, 0.02)), 0.028, 0.04, seg=24, mi=0)
            cyl(bm, b0 + Vector((0, 0, 0.042)), 0.029, 0.006, seg=24, mi=1)
            ball(bm, b0 + Vector((0, 0, 0.052)), 0.010, mi=2, seg=10)
            mats = [M["cake"], M["cream"], M["berry"]]
        elif kind == "mac":
            for k in range(3):
                a = 2 * math.pi * k / 3 + 0.4; q2 = b0 + Vector((0.026 * math.cos(a), 0.026 * math.sin(a), 0.006))
                for dz, r_, mi_ in ((0.0, 0.017, k), (0.007, 0.0145, 3), (0.014, 0.017, k)):
                    cyl(bm, q2 + Vector((0, 0, dz)), r_, 0.0065, seg=16, mi=mi_)
            mats = [M["macl"], M["macr"], M["macs"], M["cream"]]
        else:
            cyl(bm, b0 + Vector((0, 0, 0.008)), 0.032, 0.016, seg=24, r2=0.035, mi=0)
            cyl(bm, b0 + Vector((0, 0, 0.0165)), 0.029, 0.003, seg=24, mi=1)
            for k in range(7):
                a = 2 * math.pi * k / 7; ball(bm, b0 + Vector((0.017 * math.cos(a), 0.017 * math.sin(a), 0.021)), 0.008, mi=2, seg=10)
            ball(bm, b0 + Vector((0, 0, 0.021)), 0.009, mi=3, seg=10)
            mats = [M["potato"], M["cream"], M["berry"], M["grape"]]
        mesh_obj(f"V2_DessertFood{i}", bm, mats, c, smooth=True, parent=o)
    # 水果盤：葡萄兩串、柳橙片、奇異果片、草莓
    q = layout["fruit"]
    o = plate("V2_FruitPlate", q, 0.09)
    bm = MB(); b0 = Vector((0, 0, 0.0085))
    for g, (gx, gy, mi_) in enumerate(((-0.035, 0.02, 0), (0.025, 0.035, 1))):
        for k in range(14):
            lay = k // 5
            a = 2 * math.pi * (k % 5) / 5 + lay
            r_ = 0.016 - 0.004 * lay
            ball(bm, b0 + Vector((gx + r_ * math.cos(a), gy + r_ * math.sin(a), 0.010 + 0.013 * lay)), 0.0095, mi=mi_, seg=10)
    for k in range(4):
        a = math.radians(-110 + 24 * k); r_ = 0.06
        rot = Matrix.Rotation(a, 4, "Z") @ Matrix.Rotation(math.radians(70), 4, "X")
        cyl(bm, b0 + Vector((r_ * math.cos(a), r_ * math.sin(a), 0.02)), 0.022, 0.006, seg=18, mi=2 if k % 2 == 0 else 3, rot=rot)
    for k in range(3):
        cyl(bm, b0 + Vector((0.045 - 0.02 * k, -0.035 - 0.005 * k, 0.012)), 0.013, 0.024, seg=10, r2=0.003, mi=4)
    mesh_obj("V2_Fruit", bm, [M["grape"], M["grape2"], M["orange"], M["kiwi"], M["berry"]], c, smooth=True, parent=o)
    # 紅酒瓶（左前方）
    q = layout["bottle"]
    bm = bmesh.new()
    _lathe(bm, [(0.0, 0.0), (0.036, 0.0), (0.037, 0.004), (0.037, 0.19), (0.034, 0.21), (0.022, 0.235), (0.0135, 0.255),
                (0.0135, 0.30), (0.0145, 0.302), (0.0145, 0.306), (0.0, 0.306)], seg=36, mi=0)
    o = mesh_obj("V2_WineBottle", bm, [M["bottle"]], c, smooth=True, parent=rig)
    o.location = (q[0], q[1], TOP + 0.004)
    bm = bmesh.new(); _lathe(bm, [(0.0145, 0.258), (0.0150, 0.307), (0.0, 0.3075)], seg=24, mi=0)
    mesh_obj("V2_BottleFoil", bm, M["foil"], c, smooth=True, parent=o)
    bm = bmesh.new()
    rings = _lathe(bm, [(0.0375, 0.07), (0.0375, 0.15)], seg=36, mi=0, caps=False)
    mesh_obj("V2_BottleLabel", bm, M["label"], c, smooth=True, parent=o)
    bm = bmesh.new(); _lathe(bm, [(0.0378, 0.125), (0.0378, 0.135)], seg=36, mi=0, caps=False)
    mesh_obj("V2_BottleLabelBand", bm, M["labr"], c, smooth=True, parent=o)
    # 餐巾（摺成長方形、套金色餐巾環）
    for i, (q, rz) in enumerate(layout["napkins"]):
        bm = MB()
        box(bm, Vector((0, 0, 0.007)), (0.055, 0.15, 0.014))
        for dy in (-0.05, 0.05):
            box(bm, Vector((0, dy, 0.016)), (0.054, 0.004, 0.004))
        cyl(bm, Vector((0, 0, 0.008)), 0.017, 0.022, axis="Y", seg=18, mi=1)
        o = mesh_obj(f"V2_Napkin{i}", bm, [M["nap"], M["ring"]], c, smooth=False, parent=rig)
        o.location = (q[0], q[1], TOP + 0.004); o.rotation_euler = (0, 0, math.radians(rz))
    # 小蠟燭杯（桌心後方，矮的，不擋臉）
    if layout.get("candle"):
        q = layout["candle"]
        bm = MB(); cyl(bm, Vector((0, 0, 0.022)), 0.022, 0.044, seg=20, mi=0)
        o = mesh_obj("V2_Candle", bm, [M["candle"]], c, smooth=True, parent=rig)
        o.location = (q[0], q[1], TOP + 0.004)


def build_glass(c, name):
    """紅酒杯（含酒）：杯子 name、液體 name+'Wine'（液面每格用 wine_level 切成水平）"""
    M = V2["din_mats"]
    bm = bmesh.new(); _lathe(bm, _glass_prof(), seg=36)
    g = mesh_obj(name, bm, M["glass"], c, smooth=True)
    bm = bmesh.new(); _lathe(bm, _wine_prof(), seg=36)
    base = bpy.data.meshes.new(name + "WineBase"); bm.to_mesh(base); bm.free()
    w = mesh_obj(name + "Wine", bmesh.new(), M["wine"], c, smooth=True)
    V2.setdefault("wine_base", {})[name] = base
    # 杯身內的液體體積（直立、液面在 fill 時），之後傾斜時照體積找液面高度
    V2.setdefault("wine_vol", {})[name] = _wine_cut(base, Matrix.Identity(4), GLASS_D["fill"], vol_only=True)
    return g, w


def _wine_cut(base, Mw, z_level, vol_only=False, out=None):
    """把液體旋轉體換到世界（Mw），切掉水平面 z_level 以上，補上液面 → 體積（vol_only）或寫進 out 網格"""
    bm = bmesh.new(); bm.from_mesh(base)
    bmesh.ops.transform(bm, matrix=Mw, verts=bm.verts[:])
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    res = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, z_level), plane_no=(0, 0, 1), clear_outer=True)
    cut_edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    if cut_edges:
        try:
            bmesh.ops.holes_fill(bm, edges=cut_edges, sides=0)
        except Exception:
            pass
    if vol_only:
        v = bm.calc_volume(signed=False); bm.free(); return v
    if out is not None:
        bm.to_mesh(out); out.update()
    bm.free()


def wine_level(name, Mw):
    """杯子的世界矩陣 Mw（握點）→ 液面保持水平、體積不變（二分法找液面高度）"""
    base = V2["wine_base"][name]; vol = V2["wine_vol"][name]
    zs = [(Mw @ v.co).z for v in base.vertices]
    lo, hi = min(zs), max(zs)
    for _ in range(14):
        mid = (lo + hi) / 2
        if _wine_cut(base, Mw, mid, vol_only=True) < vol:
            lo = mid
        else:
            hi = mid
    w = bpy.data.objects[name + "Wine"]
    w.matrix_world = Matrix.Identity(4)
    _wine_cut(base, Mw, (lo + hi) / 2, out=w.data)
    w.data.polygons.foreach_set("use_smooth", [True] * len(w.data.polygons))
    if not w.data.materials:
        w.data.materials.append(V2["din_mats"]["wine"])


def build_fork(c, name):
    """叉子（原點＝握點、+Z＝叉尖；叉尖 +11.5、柄尾 −6.5 cm）＋叉上的一口牛排"""
    M = V2["din_mats"]
    bm = MB()
    box(bm, Vector((0, 0, -0.015)), (0.009, 0.0035, 0.10))                 # 柄
    box(bm, Vector((0, 0, 0.055)), (0.007, 0.003, 0.04))                   # 頸
    box(bm, Vector((0, 0, 0.081)), (0.022, 0.003, 0.012))                  # 叉根
    for k in range(4):
        box(bm, Vector((-0.0083 + 0.0055 * k, 0, 0.100)), (0.0022, 0.0025, 0.03))
    o = mesh_obj(name, bm, M["silver"], c, smooth=False)
    bm = MB()
    box(bm, Vector((0, 0, 0.0)), (0.020, 0.020, 0.018), rot=Matrix.Rotation(0.3, 4, "Z"))
    box(bm, Vector((0.0, 0.0102, 0.0)), (0.017, 0.001, 0.014), rot=Matrix.Rotation(0.3, 4, "Z"), mi=1)
    b = mesh_obj(name + "Bite", bm, [M["steak"], M["steak_in"]], c, smooth=True)
    return o, b


def build_chair(c, name, place, back=0.30):
    """白色木頭花園椅：place＝(x, y, rz)（角色站位，椅面在臀部正下方偏後）；椅背在角色後方"""
    M = V2["din_mats"]
    x, y, rz = place
    rig = empty(name, c, (x, y, 0.0)); rig.rotation_euler = (0, 0, math.radians(rz))
    S = DIN["seat"]
    bm = MB()
    oy = 0.05                                                    # 椅面中心在臀部後方 5 cm（角色座標 +Y＝後方）
    box(bm, Vector((0, oy, S - 0.036)), (0.42, 0.40, 0.04))        # 椅面（上面再放 1.6 cm 坐墊，坐墊頂＝動作庫的椅面高 SEAT_H）
    for sx in (-1, 1):
        for sy in (-1, 1):
            h = S - 0.04 if sy < 0 else 0.95
            box(bm, Vector((sx * 0.18, oy + sy * 0.17, h / 2)), (0.035, 0.035, h))     # 前腳／後腳（後腳一路到椅背頂）
        box(bm, Vector((sx * 0.18, oy, 0.16)), (0.025, 0.34, 0.025))                    # 側橫撐
    for z in (0.62, 0.78, 0.92):                                                     # 椅背橫條
        box(bm, Vector((0, oy + 0.17, z)), (0.36, 0.022, 0.05 if z > 0.9 else 0.035))
    for sx in (-0.09, 0.0, 0.09):                                                     # 椅背直條
        box(bm, Vector((sx, oy + 0.17, 0.77)), (0.022, 0.018, 0.30))
    mesh_obj(name + "Frame", bm, M["wood"], c, smooth=False, parent=rig)
    bm = MB(); box(bm, Vector((0, oy, S - 0.008)), (0.38, 0.36, 0.016))
    mesh_obj(name + "Cushion", bm, M["cushion"], c, smooth=False, parent=rig)
    return rig


def build_easel(c, loc, rz, board=(0.44, 0.34), bottom=0.80):
    """畫架＋空白小黑板（粉筆字之後 2D 疊）：loc＝畫架腳中心 (x, y)、rz＝黑板面朝向（0＝面向 −Y）"""
    M = V2["din_mats"]
    rig = empty("V2_Easel", c, (loc[0], loc[1], 0.0)); rig.rotation_euler = (0, 0, math.radians(rz))
    bw, bh = board
    top = bottom + bh
    bm = MB()
    for sx in (-1, 1):                                            # 前面兩支腳（往上收）
        p0 = Vector((sx * 0.30, -0.10, 0.0)); p1 = Vector((sx * 0.07, 0.0, top + 0.10)); v = p1 - p0
        box(bm, (p0 + p1) / 2, (0.03, 0.03, v.length), rot=v.to_track_quat("Z", "Y").to_matrix().to_4x4())
    p0 = Vector((0, 0.42, 0.0)); p1 = Vector((0, 0.02, top + 0.05)); v = p1 - p0                       # 後腳
    box(bm, (p0 + p1) / 2, (0.03, 0.03, v.length), rot=v.to_track_quat("Z", "Y").to_matrix().to_4x4())
    box(bm, Vector((0, -0.085, bottom - 0.02)), (0.56, 0.06, 0.025))                                      # 托板
    mesh_obj("V2_EaselLegs", bm, M["oak"], c, parent=rig)
    tilt = math.radians(-8)
    bd = empty("V2_Board", c, (0, -0.09, bottom), parent=rig); bd.rotation_euler = (tilt, 0, 0)
    bm = MB()
    box(bm, Vector((0, 0, bh / 2)), (bw, 0.014, bh), mi=0)
    for z in (0.0, bh):
        box(bm, Vector((0, -0.004, z)), (bw + 0.03, 0.022, 0.026), mi=1)
    for x in (-bw / 2 - 0.004, bw / 2 + 0.004):
        box(bm, Vector((x, -0.004, bh / 2)), (0.026, 0.022, bh + 0.026), mi=1)
    mesh_obj("V2_BoardPanel", bm, [M["board"], M["oak"]], c, parent=bd)
    return rig, bd


# ══════════ ② 敲中時的小星星（3D，2026-10-07 使用者要求）══════════
STAR_N = 4


def build_stars(c):
    """4 顆圓胖的五角星（外半徑 4.5 cm、內半徑 2.1 cm、厚 1.4 cm、邊緣圓一點）：暖黃×2、乾燥玫瑰×2，微微自發光（逆光也看得出來）。
    局部 +Z＝星星正面（每格轉向鏡頭）"""
    cols = [pmat("V2_StarYellow", srgb("#F3C64B"), rough=0.35, spec=0.5, emit=0.8, coat=0.4),
            pmat("V2_StarRose", PAL["rose"], rough=0.35, spec=0.5, emit=0.6, coat=0.4)]
    for i in range(STAR_N):
        bm = bmesh.new()
        ro, ri, th = 0.045, 0.021, 0.014
        top = bm.verts.new((0, 0, th * 0.75)); bot = bm.verts.new((0, 0, -th * 0.75))
        ring = []
        for k in range(10):
            a = math.pi / 2 + math.pi * k / 5
            r = ro if k % 2 == 0 else ri
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), 0.0)))
        for k in range(10):
            bm.faces.new((top, ring[k], ring[(k + 1) % 10]))
            bm.faces.new((bot, ring[(k + 1) % 10], ring[k]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        o = mesh_obj(f"V2_Star{i}", bm, cols[i % 2], c, smooth=False)
        o.hide_render = True
    V2["stars"] = [bpy.data.objects[f"V2_Star{i}"] for i in range(STAR_N)]


def stars_update(t, a, b, ctr, cam_loc):
    """a～b 秒：從 ctr（新郎頭頂上方）冒出來（0.15 秒放大、半徑 6→16 cm）→ 在頭頂上方繞一圈（約 1.15 秒，深度方向壓扁成橢圓）→
    最後 0.25 秒縮小消失；每顆星正面朝鏡頭、自己慢慢轉"""
    for i, o in enumerate(V2.get("stars", [])):
        if not (a <= t <= b):
            o.hide_render = True; o.hide_viewport = True; continue
        s = t - a
        pop = ease(min(1.0, s / 0.15)); fade = 1.0 - ease(max(0.0, (t - (b - 0.25)) / 0.25))
        sc_ = max(0.001, pop * fade * (0.95 + 0.12 * math.sin(7.0 * s + i)))
        th = 2 * math.pi * i / STAR_N + 2 * math.pi * s / 1.15
        r = 0.06 + 0.10 * pop
        p = Vector(ctr) + Vector((r * math.cos(th), 0.55 * r * math.sin(th), 0.025 * math.sin(2 * th + i) + 0.02 * pop))
        n = (Vector(cam_loc) - p).normalized()
        R = n.to_track_quat("Z", "Y").to_matrix().to_4x4() @ Matrix.Rotation(1.8 * s * (1 if i % 2 else -1) + i * 0.6, 4, "Z")
        o.matrix_world = Matrix.Translation(p) @ R @ Matrix.Diagonal((sc_, sc_, sc_, 1.0))
        o.hide_render = False; o.hide_viewport = False
