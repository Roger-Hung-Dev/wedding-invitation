# ZEPETO 黏土風道具素材庫（2026-10-11 建立；第一批＝V12 開場影片 3D 幕 ②③⑤⑦a⑦b⑧ 用到的 26 樣）
#   全部程式建模（不下載素材、不用標註作者）：造型加粗、所有邊角倒圓、粉嫩低彩度配色、霧面黏土材質（粗糙度 0.75、SSS 0.3，同 ZEPETO 大頭）
#   每樣道具一個集合（ZP_<代號>），原點在底部中心、正面朝 -Y；集合都標成 Blender 資產（Asset Browser 可直接拖）
#   另組四個場景示意集合（ZP_Scene_*，用集合實例擺放，示範怎麼組景）
#
#   重建整個素材庫（約 20 秒，背景 Blender）：
#   "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --factory-startup -P build_props.py
#   只試幾樣（不覆寫素材庫，輸出到暫存）：... -P build_props.py -- ONLY=arch,taxi OUT=D:/render-work/zepeto-props/try [NORENDER=1] [SAMPLES=48]
#   只做某個場景外掛（scenes/<key>.py）＋它用到的道具：... -- SCENE=<key> OUT=D:/render-work/zepeto-props/try
#   外部素材：external_items.py 用 ext_item() 登記（檔案在 external/<代號>/source/，匯入後自動換黏土材質、倒圓、置底）
#   場景外掛：scenes/<key>.py 定義 SCENE（格式見 README.md「新增場景」）
#   輸出：OUT/zepeto_props.blend、OUT/blender_assets.cats.txt、OUT/catalog.json、OUT/previews/items/<代號>.jpg、OUT/previews/scenes/<場景>.jpg
#   用法（載入到別的場景）見同資料夾 README.md 與 use_props.py
import bpy, bmesh, math, os, sys, random, time, json, uuid
from mathutils import Vector, Matrix, Euler

ARGS = dict(a.split("=", 1) for a in (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []) if "=" in a)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = ARGS.get("OUT", HERE)
ONLY = [x for x in ARGS.get("ONLY", "").split(",") if x]
SAMPLES = int(ARGS.get("SAMPLES", 48))
NORENDER = ARGS.get("NORENDER", "0") == "1"
FONT_PATH = r"C:/Windows/Fonts/msjhbd.ttc"
T0 = time.time()

# ───────────────────────── 色票 ─────────────────────────
PAL = dict(
    rose="#D9777F", rose_dk="#B85B67", blush="#ECB0AC", cream="#FBF7F0", ivory="#FFFCF7", lav="#B8A1C9", lav_lt="#D9CBE6",
    sage="#8FA58A", euca="#9DB8A0", leaf="#7FB06F", leaf_dk="#5F9455", grass="#A4D08A", hedge="#7DB06A", hedge_dk="#6A9E5C",
    sand="#EAD9BC", stone="#F3EDE2", trunk="#A9785A", blossom="#F4C3CB", butter="#F6D77A",
    carpet="#C94A5C", carpet_dk="#A8364A", gold="#E2B85C", walnut="#8A5A3C", bellow="#4E4252", brass="#E0B860", lens="#2F3A5C",
    phone="#CDB8E0", screen="#3A4470", cloth="#FBF4EA", white="#FFFDF9",
    chicken="#D98A3D", chicken_lt="#E9A657", bone="#FFF5E3", tomato="#E5534B", broc="#6BA857", soup="#F2B45A",
    bowl="#FFF6EA", salad_bowl="#DDEBD3", lettuce="#9CCD6E", cucumber="#BFE09A", corn="#F7D65C",
    wine="#6E2B43", wine_liq="#9C2F4F", label="#FFF4E0", glass="#F2EEFA", silver="#D9DCE6",
    cake="#F7C9D2", macaron_g="#BFE0C4", macaron_y="#F6E7C8", tart="#E2B06B", berry="#6F6BC2", rasp="#E0566B",
    grape="#9B7BC8", orange="#F7A64A", orange_lt="#FFD9A0", straw="#E9545E",
    taxi="#F6C945", taxi_dk="#E3AE2C", tire="#3A3A48", hub="#DADDE4", window="#4A5A84", head="#FFF3C8", tail="#E8455A",
    wall="#F2DCC6", wall_dk="#D9B99E", door="#8C5A43", pane="#FFD9A0", sign="#3F5E4F", navy="#3C4566", pot="#D98C6A",
    walk="#D9D6DE", walk_dk="#C3C0CC", road="#5A5F73", lane="#F6E7A6",
    # 攝影棚（2026-10-11，參考照片 refs/photo_studio；黑色器材依使用者裁決改成柔和的深灰紫）
    gear="#4A4452", steel="#C9CBD3", grip="#8FA3C9", diffuser="#FBFAFC", paper="#F3F5F7",
    studio_floor="#ADA9B2", floor_dk="#A29EA8", wall_st="#E4E1E8", sheer="#F6F3F1", blackout="#4A4552",
    # 婚宴會館（2026-10-12，開場片提案 B：休息室走廊、餐飲區、攝影區、宴會廳門廳）
    hall_wall="#EFDDCB", hall_wall2="#E6DCEB", wainscot="#FFF8EF", trim="#E9D3B4", hall_floor="#E6D2BE", hall_floor2="#DCC4AC",
    runner="#C9B6D6", runner_bd="#F4ECE0", marble="#F6EFE8", marble2="#F1DCDC", lounge="#F5D9C9", pillar="#FBF3E8",
    door_lt="#F4E6D6", cupcake="#F2B8C6", sponge="#E9B97A", frosting="#FBE3EA", valet="#3F6B5E", glow="#FFF1DC",
)


def hexc(h, a=1.0):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (a,)


# ───────────────────────── 材質：ZEPETO 黏土 ─────────────────────────
MATS = {}


def clay(key, hexv=None, rough=0.75, sss=0.3, emit=0.0, alpha=1.0, spec=0.35):
    """霧面黏土：粗糙度 0.75、SSS 權重 0.3、縮放 0.05（同大頭定案值）；SSS 半徑道具用中性 (1,1,1)（大頭的偏紅半徑會讓淺色道具陰影泛粉紅）"""
    name = "ZP_" + key
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    col = hexc(hexv or PAL[key])
    def setin(k, v):
        s = bsdf.inputs.get(k)
        if s is not None:
            s.default_value = v
    setin("Base Color", col); setin("Roughness", rough); setin("Specular IOR Level", spec)
    setin("Subsurface Weight", sss); setin("Subsurface Radius", (1.0, 1.0, 1.0)); setin("Subsurface Scale", 0.05)
    if emit > 0:
        setin("Emission Color", col); setin("Emission Strength", emit)
    if alpha < 1.0:
        setin("Alpha", alpha)
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            m.blend_method = "BLEND"
    m.diffuse_color = col
    MATS[name] = m
    return m


# ───────────────────────── 幾何基本形（回傳暫存 bmesh，局部座標）─────────────────────────
def _mark_flat(bm, axes, min_area=0.0):
    bm.normal_update()
    for f in bm.faces:
        n = f.normal
        flat = any(abs(n[i]) > 0.9999 for i in axes) and f.calc_area() > min_area
        f.smooth = not flat
        if flat:
            for e in f.edges:
                e.smooth = False


def p_box(sx, sy, sz, r=None, seg=4):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz))
    r = min(sx, sy, sz) * 0.2 if r is None else r
    r = min(r, min(sx, sy, sz) * 0.49)
    if r > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=r, offset_type="OFFSET", segments=seg, profile=0.5, affect="EDGES", clamp_overlap=True)
    _mark_flat(bm, (0, 1, 2))
    return bm


def p_cyl(rad, h, r=None, seg=40, rad2=None, bseg=4):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=rad, radius2=rad if rad2 is None else rad2, depth=h)
    r = min(rad, h) * 0.25 if r is None else r
    r = min(r, h * 0.49, min(rad, rad2 or rad) * 0.9)
    if r > 0:
        edges = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) < 1e-6]
        bmesh.ops.bevel(bm, geom=edges, offset=r, offset_type="OFFSET", segments=bseg, profile=0.5, affect="EDGES", clamp_overlap=True)
    _mark_flat(bm, (2,))
    return bm


def p_sphere(rx, ry=None, rz=None, seg=32):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(8, seg // 2), radius=1.0)
    ry = rx if ry is None else ry; rz = rx if rz is None else rz
    for v in bm.verts:
        v.co = Vector((v.co.x * rx, v.co.y * ry, v.co.z * rz))
    for f in bm.faces:
        f.smooth = True
    return bm


def p_lathe(profile, seg=48):
    """繞 Z 軸旋轉成形：profile＝[(半徑, 高)…]，半徑 0 的點收成單點"""
    bm = bmesh.new(); rings = []
    for r, z in profile:
        if r < 1e-6:
            rings.append([bm.verts.new((0, 0, z))])
        else:
            rings.append([bm.verts.new((r * math.cos(2 * math.pi * k / seg), r * math.sin(2 * math.pi * k / seg), z)) for k in range(seg)])
    for a, b in zip(rings, rings[1:]):
        for k in range(seg):
            if len(a) == 1 and len(b) == 1:
                continue
            if len(a) == 1:
                vs = (a[0], b[(k + 1) % seg], b[k])
            elif len(b) == 1:
                vs = (a[k], a[(k + 1) % seg], b[0])
            else:
                vs = (a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k])
            try:
                f = bm.faces.new(vs); f.smooth = True
            except ValueError:
                pass
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return bm


def p_torus(R, r, a0=0.0, a1=2 * math.pi, seg=48, rseg=16):
    bm = bmesh.new(); full = abs(a1 - a0 - 2 * math.pi) < 1e-6
    n = seg if full else seg + 1
    rings = []
    for i in range(n):
        a = a0 + (a1 - a0) * i / seg
        c = Vector((R * math.cos(a), R * math.sin(a), 0)); out = Vector((math.cos(a), math.sin(a), 0))
        rings.append([bm.verts.new(c + out * (r * math.cos(2 * math.pi * j / rseg)) + Vector((0, 0, r * math.sin(2 * math.pi * j / rseg)))) for j in range(rseg)])
    pairs = list(zip(rings, rings[1:])) + ([(rings[-1], rings[0])] if full else [])
    for A, B in pairs:
        for j in range(rseg):
            f = bm.faces.new((A[j], A[(j + 1) % rseg], B[(j + 1) % rseg], B[j])); f.smooth = True
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return bm


def p_tube(pts, rad, rseg=12):
    """沿折線掃出圓管（半徑可給函式 rad(t)），兩端用半球收圓"""
    pts = [Vector(p) for p in pts]; bm = bmesh.new(); rings = []
    rf = rad if callable(rad) else (lambda t: rad)
    prev_n = None
    for i, p in enumerate(pts):
        tg = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        if prev_n is None:
            up = Vector((0, 0, 1)) if abs(tg.z) < 0.9 else Vector((1, 0, 0))
            nrm = (up - tg * up.dot(tg)).normalized()
        else:
            nrm = (prev_n - tg * prev_n.dot(tg)).normalized()
        prev_n = nrm; bin_ = tg.cross(nrm); rr = rf(i / max(1, len(pts) - 1))
        rings.append([bm.verts.new(p + (nrm * math.cos(2 * math.pi * j / rseg) + bin_ * math.sin(2 * math.pi * j / rseg)) * rr) for j in range(rseg)])
    for A, B in zip(rings, rings[1:]):
        for j in range(rseg):
            f = bm.faces.new((A[j], A[(j + 1) % rseg], B[(j + 1) % rseg], B[j])); f.smooth = True
    for ring in (rings[0], rings[-1]):
        f = bm.faces.new(ring); f.smooth = True
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return bm


def M(loc=(0, 0, 0), rot=(0, 0, 0), scale=None):
    m = Matrix.Translation(Vector(loc)) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4()
    if scale is not None:
        s = scale if hasattr(scale, "__len__") else (scale,) * 3
        m = m @ Matrix.Diagonal((s[0], s[1], s[2], 1.0))
    return m


# ───────────────────────── 組合器：一個物件可放多種材質 ─────────────────────────
class MB:
    def __init__(self, name):
        self.name = name; self.bm = bmesh.new(); self.mats = []

    def add(self, src, mat, m=None):
        m = m or Matrix(); mi = self._mi(mat)
        vmap = [self.bm.verts.new(m @ v.co) for v in src.verts]
        for f in src.faces:
            try:
                nf = self.bm.faces.new([vmap[v.index] for v in f.verts])
            except ValueError:
                continue
            nf.smooth = f.smooth; nf.material_index = mi
        self.bm.edges.ensure_lookup_table()
        for e in src.edges:
            if not e.smooth:
                ne = self.bm.edges.get((vmap[e.verts[0].index], vmap[e.verts[1].index]))
                if ne:
                    ne.smooth = False
        src.free()
        return self

    def add_mesh(self, src, mats):
        """整個 bmesh 加進來，面的 material_index 對到 mats（外部素材用；src 已在最終座標）"""
        vmap = [self.bm.verts.new(v.co) for v in src.verts]
        idx = [self._mi(m) for m in mats]
        for f in src.faces:
            try:
                nf = self.bm.faces.new([vmap[v.index] for v in f.verts])
            except ValueError:
                continue
            nf.smooth = f.smooth; nf.material_index = idx[min(f.material_index, len(idx) - 1)]
        src.free()
        return self

    def _mi(self, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def obj(self, col, loc=(0, 0, 0)):
        me = bpy.data.meshes.new(self.name)
        if len(self.bm.verts) and self.mats and any(m.blend_method != "OPAQUE" if hasattr(m, "blend_method") else False for m in self.mats):
            pass
        bmesh.ops.recalc_face_normals(self.bm, faces=list(self.bm.faces))
        self.bm.to_mesh(me); self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(self.name, me); ob.location = loc
        col.objects.link(ob)
        return ob


def text_obj(col, body, size, mat, loc=(0, 0, 0), rot=(0, 0, 0), extrude=0.004, name="ZP_Text", font=None):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = body
    try:
        cu.font = bpy.data.fonts.load(font or FONT_PATH, check_existing=True)
    except Exception as e:
        print("FONT_FAIL", e)
    cu.size = size; cu.extrude = extrude; cu.bevel_depth = extrude * 0.3; cu.bevel_resolution = 3
    cu.align_x = "CENTER"; cu.align_y = "CENTER"
    ob = bpy.data.objects.new(name, cu); ob.data.materials.append(mat)
    ob.location = loc; ob.rotation_euler = [math.radians(a) for a in rot]
    col.objects.link(ob)
    return ob


# ───────────────────────── 小零件 ─────────────────────────
def rose(mb, mat, c, r, rnd=None, tilt=(0, 0, 0)):
    """黏土玫瑰：壓扁的花球＋頂上捲 2.5 圈的花瓣管＋外圈 5 片花瓣"""
    rot = M(c, tilt)
    mb.add(p_sphere(r, r, r * 0.82, 20), mat, rot)
    pts = []
    for i in range(46):
        t = i / 45; a = t * 2.5 * 2 * math.pi; rr = r * 0.78 * (1 - t) + r * 0.08
        z = math.sqrt(max(0.0, r * r - rr * rr)) * 0.82 + r * 0.06
        pts.append((rr * math.cos(a), rr * math.sin(a), z))
    mb.add(p_tube(pts, lambda t: r * (0.16 - 0.06 * t), 8), mat, rot)
    for k in range(5):
        a = 2 * math.pi * k / 5 + (rnd.random() if rnd else 0)
        mb.add(p_sphere(r * 0.62, r * 0.42, r * 0.22, 14), mat,
               rot @ M((r * 0.62 * math.cos(a), r * 0.62 * math.sin(a), -r * 0.18), (0, 62, math.degrees(a))))


def leaf(mb, mat, c, L, yaw=0.0, pitch=0.0, roll=0.0):
    mb.add(p_sphere(L * 0.5, L * 0.22, L * 0.06, 14), mat, M(c, (roll, pitch, yaw)) @ M((L * 0.45, 0, 0)))


def daisy(mb, mat_p, mat_c, c, r, n=5):
    mb.add(p_sphere(r * 0.38, r * 0.38, r * 0.25, 12), mat_c, M(c))
    for k in range(n):
        a = 2 * math.pi * k / n
        mb.add(p_sphere(r * 0.5, r * 0.3, r * 0.12, 12), mat_p, M(c) @ M((r * 0.55 * math.cos(a), r * 0.55 * math.sin(a), -r * 0.05), (0, 0, math.degrees(a))))


def lavender_spike(mb, c, h, rnd):
    mb.add(p_tube([(c[0], c[1], c[2]), (c[0], c[1], c[2] + h)], 0.006, 6), clay("sage"))
    for i in range(7):
        z = c[2] + h * (0.55 + 0.065 * i); s = 0.022 * (1 - i * 0.08)
        mb.add(p_sphere(s, s, s * 1.3, 10), clay("lav"), M((c[0] + rnd.uniform(-0.004, 0.004), c[1], z)))


# ───────────────────────── 道具（每個回傳集合）─────────────────────────
ITEMS = {}   # 代號 → (中文名, 幕, builder)
CATALOGS = {"garden": ("ZEPETO_Props/Garden", "花園"), "carpet": ("ZEPETO_Props/Carpet", "紅毯"), "dinner": ("ZEPETO_Props/Dinner", "晚餐桌"),
            "street": ("ZEPETO_Props/Street", "夜晚街景"), "scenes": ("ZEPETO_Props/Scenes", "場景示意")}


ITEM_CAT = {}  # 代號 → 分類 key（新道具用 @item(..., cat="beach:海邊")；V12 第一批的分類寫在 CAT_OF）


def item(key, label, scenes, cat=None):
    def deco(fn):
        ITEMS[key] = (label, scenes, fn)
        if cat:
            ITEM_CAT[key] = add_catalog(cat)
        return fn
    return deco


def add_catalog(cat):
    """'beach:海邊' → 登記 Asset Browser 分類 ZEPETO_Props/Beach（中文名＝海邊），回傳 key"""
    ck, _, cn = cat.partition(":")
    if ck not in CATALOGS:
        CATALOGS[ck] = ("ZEPETO_Props/" + ck.replace("_", " ").title().replace(" ", ""), cn or ck)
    return ck


def cat_of(k):
    return CAT_OF.get(k) or ITEM_CAT.get(k) or add_catalog("misc:其他")


@item("arch", "白色花拱門（玫瑰＋尤加利垂枝）", "②③⑤⑧")
def b_arch(col):
    rnd = random.Random(7); mb = MB("ZP_arch_frame"); w = clay("white", rough=0.7)
    for x in (-1.0, 1.0):
        for y in (-0.18, 0.18):
            mb.add(p_box(0.13, 0.13, 2.0, 0.045), w, M((x, y, 1.0)))
            mb.add(p_box(0.2, 0.2, 0.08, 0.03), w, M((x, y, 0.04)))
        for z in (0.45, 0.9, 1.35, 1.8):
            mb.add(p_cyl(0.025, 0.36, 0.01, 16), w, M((x, 0, z), (90, 0, 0)))
    for y in (-0.18, 0.18):
        mb.add(p_torus(1.0, 0.065, 0, math.pi, 40, 14), w, M((0, y, 2.0), (90, 0, 0)))
    for k in range(1, 10):
        a = math.pi * k / 10
        mb.add(p_cyl(0.028, 0.36, 0.01, 16), w, M((math.cos(a), 0, 2.0 + math.sin(a)), (90, 0, 0)))
    mb.obj(col)
    fl = MB("ZP_arch_flowers"); cols = [clay("rose"), clay("blush"), clay("cream"), clay("lav")]
    g1, g2 = clay("sage"), clay("euca")
    # 左上一大叢（沿拱 95°～175°）、右柱下方一叢、右上點綴
    spots = [(math.radians(rnd.uniform(95, 178)), None) for _ in range(44)] + [(math.radians(rnd.uniform(10, 40)), None) for _ in range(8)]
    for a, _ in spots:
        base = Vector((math.cos(a), -0.24 + rnd.uniform(-0.05, 0.06), 2.0 + math.sin(a)))
        out = Vector((math.cos(a), 0, math.sin(a))) * rnd.uniform(-0.05, 0.08)
        rose(fl, rnd.choice(cols), base + out, rnd.uniform(0.09, 0.13), rnd, (rnd.uniform(70, 110), 0, rnd.uniform(-30, 30)))
        if rnd.random() < 0.8:
            leaf(fl, g1, base + Vector((0, 0.03, 0)), rnd.uniform(0.12, 0.18), rnd.uniform(0, 360), rnd.uniform(-30, 30))
    for z in [rnd.uniform(1.2, 1.95) for _ in range(9)]:            # 左柱往下
        rose(fl, rnd.choice(cols), Vector((-1.0 + rnd.uniform(-0.08, 0.08), -0.25, z)), rnd.uniform(0.07, 0.1), rnd, (90, 0, rnd.uniform(-20, 20)))
        leaf(fl, g1, Vector((-1.0, -0.22, z - 0.05)), 0.15, rnd.uniform(0, 360), rnd.uniform(-40, 40))
    for z in [rnd.uniform(0.15, 0.7) for _ in range(9)]:            # 右柱下方
        rose(fl, rnd.choice(cols), Vector((1.0 + rnd.uniform(-0.12, 0.12), -0.25, z)), rnd.uniform(0.07, 0.1), rnd, (90, 0, rnd.uniform(-20, 20)))
        leaf(fl, g1, Vector((1.0, -0.22, z - 0.05)), 0.15, rnd.uniform(0, 360), rnd.uniform(-40, 40))
    for i in range(16):                                               # 尤加利垂枝
        a = math.radians(rnd.uniform(100, 175) if i < 12 else rnd.uniform(15, 50))
        top = Vector((math.cos(a), -0.2, 2.0 + math.sin(a))); L = rnd.uniform(0.4, 0.9)
        pts = [top + Vector((0.04 * math.sin(t * 6), 0, -L * t)) for t in [j / 12 for j in range(13)]]
        fl.add(p_tube(pts, 0.008, 6), g2)
        for j in range(1, 13, 1):
            p = pts[j]; s = 0.035 * (1 - j / 20)
            for sd in (-1, 1):
                fl.add(p_sphere(s, s * 0.9, s * 0.18, 12), g2, M(p + Vector((sd * s * 0.9, -0.01, 0)), (90, 0, 0)))
    fl.obj(col)


@item("hedge", "樹籬牆（圓角方塊＋小花點）", "②③⑤⑦a⑧")
def b_hedge(col):
    rnd = random.Random(3); mb = MB("ZP_hedge")
    mb.add(p_box(3.0, 0.6, 1.45, 0.24), clay("hedge"), M((0, 0, 0.725)))
    mb.add(p_box(3.06, 0.66, 0.22, 0.1), clay("hedge_dk"), M((0, 0, 0.11)))
    for _ in range(26):
        x = rnd.uniform(-1.35, 1.35); z = rnd.uniform(0.35, 1.3)
        daisy(mb, rnd.choice([clay("cream"), clay("blush")]), clay("butter"), (x, -0.305, z), 0.035)
    mb.obj(col)


@item("tree", "背景樹（綠樹、粉花樹）", "②③⑤⑧")
def b_tree(col):
    for i, (x, c) in enumerate(((-0.9, "leaf"), (0.9, "blossom"))):
        mb = MB("ZP_tree_%d" % i)
        mb.add(p_lathe([(0, 0), (0.13, 0), (0.12, 0.05), (0.085, 0.3), (0.075, 1.2), (0, 1.2)], 24), clay("trunk"), M((x, 0, 0)))
        for (dx, dy, dz, r) in ((0, 0, 1.75, 0.7), (0.38, 0.05, 1.45, 0.48), (-0.4, -0.02, 1.5, 0.5), (0.05, -0.1, 2.25, 0.42)):
            mb.add(p_sphere(r, r, r * 0.92, 28), clay(c), M((x + dx, dy, dz)))
        mb.obj(col)


@item("ground", "草地＋沙色小徑＋踏腳石", "②③⑤⑧")
def b_ground(col):
    mb = MB("ZP_ground")
    mb.add(p_cyl(2.2, 0.12, 0.05, 64), clay("grass"), M((0, 0, 0.06)))
    mb.add(p_box(1.0, 4.0, 0.03, 0.012), clay("sand"), M((0, 0, 0.125)))
    for i in range(7):
        mb.add(p_cyl(0.2, 0.035, 0.015, 28), clay("stone"), M((0.08 * (-1) ** i, -1.6 + i * 0.53, 0.145), scale=(1.25, 0.85, 1)))
    mb.obj(col)


@item("flowerbed", "花圃（矮灌木、雛菊、薰衣草）", "②③⑤⑧")
def b_flowerbed(col):
    rnd = random.Random(11); mb = MB("ZP_flowerbed")
    mb.add(p_box(1.8, 0.5, 0.18, 0.08), clay("hedge_dk"), M((0, 0, 0.09)))
    for i in range(7):
        x = -0.78 + i * 0.26
        mb.add(p_sphere(0.16, 0.15, 0.14, 20), clay("leaf"), M((x, 0.05, 0.22)))
    for _ in range(14):
        daisy(mb, rnd.choice([clay("cream"), clay("blush"), clay("rose")]), clay("butter"), (rnd.uniform(-0.85, 0.85), rnd.uniform(-0.2, -0.05), rnd.uniform(0.25, 0.36)), 0.045)
    for _ in range(9):
        lavender_spike(mb, (rnd.uniform(-0.8, 0.8), rnd.uniform(-0.05, 0.15), 0.2), rnd.uniform(0.32, 0.45), rnd)
    mb.obj(col)


@item("petals", "飄落花瓣", "②③⑤⑧")
def b_petals(col):
    rnd = random.Random(5); mb = MB("ZP_petals")
    for i in range(40):
        a = i * 2.4; rr = 0.05 + 0.3 * math.sqrt(i / 40)
        c = (rr * math.cos(a), rr * math.sin(a) * 0.5, 0.06 + rnd.uniform(0, 0.45))
        mb.add(p_sphere(0.032, 0.024, 0.007, 14), rnd.choice([clay("rose"), clay("blush"), clay("lav")]),
               M(c, (rnd.uniform(-60, 60), rnd.uniform(-60, 60), rnd.uniform(0, 360))))
    mb.obj(col)


@item("carpet", "紅毯（鋪開、四個平貼字）", "③")
def b_carpet(col):
    mb = MB("ZP_carpet")
    mb.add(p_box(1.6, 4.0, 0.03, 0.014), clay("carpet"), M((0, 0, 0.015)))
    for x in (-0.68, 0.68):
        mb.add(p_box(0.05, 3.9, 0.012, 0.005), clay("gold", rough=0.5), M((x, 0, 0.034)))
    mb.obj(col)
    for i, w in enumerate(("相遇", "交往", "求婚", "婚禮")):
        text_obj(col, w, 0.34, clay("label"), (0, -1.45 + i * 0.95, 0.033), (0, 0, 90), 0.005, "ZP_carpet_txt%d" % i)


@item("roll", "紅毯卷（推動用）", "③")
def b_roll(col):
    mb = MB("ZP_roll")
    mb.add(p_cyl(0.52, 1.6, 0.06, 56), clay("carpet"), M((0, 0, 0.52), (0, 90, 0)))
    for sd in (-1, 1):                                              # 兩端的捲層：平面螺旋
        pts = []
        for i in range(160):
            t = i / 159; a = t * 4.5 * 2 * math.pi; rr = 0.07 + 0.4 * t
            pts.append((sd * 0.805, rr * math.cos(a), 0.52 + rr * math.sin(a)))
        mb.add(p_tube(pts, 0.018, 8), clay("carpet_dk"))
        mb.add(p_cyl(0.06, 0.02, 0.008, 24), clay("carpet_dk"), M((sd * 0.8, 0, 0.52), (0, 90, 0)))
    mb.add(p_box(1.6, 0.7, 0.03, 0.014), clay("carpet"), M((0, -0.42, 0.015)))
    for x in (-0.68, 0.68):
        mb.add(p_box(0.05, 0.66, 0.012, 0.005), clay("gold", rough=0.5), M((x, -0.44, 0.034)))
    mb.obj(col)


@item("oldcam", "木製老相機＋三腳架（紅燈）", "⑤")
def b_oldcam(col):
    mb = MB("ZP_oldcam"); wood = clay("walnut"); br = clay("brass", rough=0.45)
    for k in range(3):
        a = math.radians(90 + 120 * k)
        mb.add(p_tube([(0, 0, 1.02), (0.42 * math.cos(a), 0.42 * math.sin(a), 0.02)], 0.032, 12), clay("trunk"))
        mb.add(p_sphere(0.045, 0.045, 0.03, 14), clay("bellow"), M((0.42 * math.cos(a), 0.42 * math.sin(a), 0.02)))
    mb.add(p_cyl(0.11, 0.06, 0.02, 28), br, M((0, 0, 1.05)))
    mb.add(p_box(0.36, 0.34, 0.34, 0.06), wood, M((0, 0.06, 1.25)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                mb.add(p_sphere(0.028), br, M((sx * 0.165, 0.06 + sy * 0.155, 1.25 + sz * 0.155)))
    for i in range(5):                                              # 皮腔：往前越來越小
        s = 0.3 - i * 0.03
        mb.add(p_box(s, 0.06, s, 0.025), clay("bellow") if i % 2 == 0 else clay("lav", "#5E5064"), M((0, -0.14 - i * 0.055, 1.25)))
    mb.add(p_cyl(0.085, 0.14, 0.02, 32), br, M((0, -0.47, 1.25), (90, 0, 0)))
    mb.add(p_cyl(0.07, 0.03, 0.01, 32), clay("lens", rough=0.3), M((0, -0.545, 1.25), (90, 0, 0)))
    mb.add(p_box(0.42, 0.06, 0.4, 0.05), clay("bellow", "#2E2A33"), M((0, 0.26, 1.22)))
    mb.add(p_box(0.12, 0.05, 0.08, 0.02), br, M((0, 0.06, 1.455)))
    mb.add(p_sphere(0.035), clay("tail", "#FF4A4A", rough=0.4, emit=3.0), M((0, 0.06, 1.52)))
    mb.obj(col)


@item("bouquet", "捧花（19 朵玫瑰＋緞帶蝴蝶結）", "⑤")
def b_bouquet(col):
    rnd = random.Random(21); mb = MB("ZP_bouquet"); cols = [clay("rose"), clay("blush"), clay("cream"), clay("lav")]
    cz = 0.33
    for i in range(19):
        y = 1 - (i + 0.5) / 19 * 0.75; rr = math.sqrt(1 - y * y); a = i * 2.39996
        d = Vector((rr * math.cos(a), rr * math.sin(a), y))
        c = Vector((0, 0, cz)) + d * 0.12
        rose(mb, rnd.choice(cols), c, 0.045, rnd, (math.degrees(math.acos(max(-1, min(1, d.z)))) * 0.9, 0, 0))
    for k in range(10):
        a = 2 * math.pi * k / 10
        leaf(mb, clay("sage"), (0.11 * math.cos(a), 0.11 * math.sin(a), cz - 0.02), 0.09, math.degrees(a), 25)
    mb.add(p_cyl(0.035, 0.24, 0.012, 20), clay("leaf_dk"), M((0, 0, 0.14)))
    mb.add(p_cyl(0.042, 0.09, 0.015, 24), clay("rose"), M((0, 0, 0.2)))
    for sd in (-1, 1):
        mb.add(p_sphere(0.042, 0.016, 0.026, 20), clay("rose"), M((sd * 0.045, -0.05, 0.205), (0, sd * -25, 0)))
        mb.add(p_box(0.025, 0.012, 0.12, 0.006), clay("rose"), M((sd * 0.03, -0.05, 0.12), (0, sd * 18, 0)))
    mb.add(p_sphere(0.022), clay("rose_dk"), M((0, -0.05, 0.2)))
    mb.obj(col)


PHONE_ZP = 0.125 / 0.155    # ZEPETO 角色手長 11.4 cm，手機縮到約手長 1.1 倍（高 12.5 cm）才握得住


def phone_mb(name, s=1.0):
    mb = MB(name)
    mb.add(p_box(0.078, 0.014, 0.155, 0.014), clay("phone"), M((0, 0, 0.0775)))
    mb.add(p_box(0.066, 0.004, 0.138, 0.01), clay("screen", rough=0.35, emit=0.6), M((0, -0.007, 0.0775)))
    mb.add(p_box(0.03, 0.006, 0.03, 0.008), clay("lav"), M((-0.017, 0.009, 0.128)))
    if s != 1.0:
        bmesh.ops.scale(mb.bm, vec=(s, s, s), verts=list(mb.bm.verts))      # 原點在底部中心，等比縮放不會離地
    return mb


@item("phone", "手機（路人甲拍照用）", "⑤")
def b_phone(col):
    phone_mb("ZP_phone").obj(col)


@item("phone_zp", "手機・ZEPETO 角色用（縮小版、素色螢幕）", "提案B B1", cat="daily:日常小物")
def b_phone_zp(col):
    phone_mb("ZP_phone_zp", PHONE_ZP).obj(col)


@item("phone_mute", "手機・靜音畫面（鈴鐺打叉＋靜音開關）", "提案B B1", cat="daily:日常小物")
def b_phone_mute(col):
    phone_mute_mb("ZP_phone_mute").obj(col)


@item("phone_mute_zp", "手機・靜音畫面・ZEPETO 角色用（縮小版）", "提案B B1", cat="daily:日常小物")
def b_phone_mute_zp(col):
    phone_mute_mb("ZP_phone_mute_zp", PHONE_ZP).obj(col)


def phone_mute_mb(name, s=1.0):
    """同 phone 外型；螢幕上是凸起的鈴鐺打叉圖示（壓扁的旋轉體），左側面有橘色靜音撥桿；握持點約在下半段 z≈0.05×s"""
    mb = MB(name)
    mb.add(p_box(0.078, 0.014, 0.155, 0.014), clay("phone"), M((0, 0, 0.0775)))
    mb.add(p_box(0.066, 0.004, 0.138, 0.01), clay("screen_m", "#4B5687", rough=0.35, emit=0.6), M((0, -0.007, 0.0775)))
    mb.add(p_box(0.03, 0.006, 0.03, 0.008), clay("lav"), M((-0.017, 0.009, 0.128)))
    def pill(half, rad, th, mat, loc):                                         # 貼在螢幕上的薄膠囊：中段方塊＋兩端圓片
        mb.add(p_box(2 * half, th, 2 * rad, th * 0.3), mat, M(loc))
        for sx in (-half, half):
            mb.add(p_cyl(rad, th, th * 0.3, 32), mat, M((loc[0] + sx, loc[1], loc[2]), (90, 0, 0)))
    pill(0.0068, 0.0032, 0.003, clay("island", "#262A3E", rough=0.4), (0, -0.009, 0.139))
    bell = [(0, 0), (0.0195, 0), (0.0212, 0.0012), (0.0212, 0.0028), (0.0195, 0.0045), (0.0172, 0.0075),
            (0.016, 0.012), (0.0155, 0.018), (0.0148, 0.023), (0.013, 0.027), (0.0102, 0.0305), (0.0062, 0.0325), (0, 0.0332)]
    icon = clay("ivory")
    mb.add(p_lathe(bell, 64), icon, M((0, -0.011, 0.072), scale=(1, 0.13, 1)))
    mb.add(p_sphere(0.0032, 0.0016, 0.0032, 16), icon, M((0, -0.0105, 0.1065)))
    mb.add(p_sphere(0.0055, 0.0018, 0.0042, 16), icon, M((0, -0.0105, 0.069)))
    mb.add(p_box(0.0062, 0.004, 0.064, 0.0028), clay("rose"), M((0, -0.0128, 0.088), (0, 45, 0)))
    pill(0.0085, 0.0065, 0.003, clay("rose"), (0, -0.0095, 0.042))
    mb.add(p_sphere(0.0052, 0.002, 0.0052, 16), icon, M((-0.0085, -0.0112, 0.042)))
    mb.add(p_box(0.004, 0.007, 0.011, 0.0018), clay("orange"), M((-0.0405, 0, 0.122)))
    if s != 1.0:
        bmesh.ops.scale(mb.bm, vec=(s, s, s), verts=list(mb.bm.verts))
    return mb


@item("table", "圓桌＋落地桌巾（薰衣草緞帶）", "⑦a")
def b_table(col):
    mb = MB("ZP_table")
    prof = [(0, 0.75), (0.38, 0.75), (0.43, 0.742), (0.455, 0.715), (0.465, 0.66), (0.48, 0.4), (0.5, 0.12), (0.52, 0.02), (0.51, 0.0), (0, 0.0)]
    mb.add(p_lathe(prof, 64), clay("cloth"))
    mb.add(p_torus(0.468, 0.016, 0, 2 * math.pi, 64, 10), clay("lav"), M((0, 0, 0.64)))
    for k in range(8):                                              # 垂褶：一圈小凸起
        a = 2 * math.pi * (k + 0.5) / 8
        mb.add(p_tube([(0.47 * math.cos(a), 0.47 * math.sin(a), 0.6), (0.515 * math.cos(a), 0.515 * math.sin(a), 0.05)], 0.02, 10), clay("cloth"))
    mb.add(p_sphere(0.03, 0.02, 0.03), clay("lav"), M((0, -0.47, 0.64)))
    mb.obj(col)


@item("chair", "白色花園椅（腮紅粉坐墊）", "⑦a")
def b_chair(col):
    mb = MB("ZP_chair"); w = clay("white", rough=0.7)
    mb.add(p_box(0.46, 0.44, 0.06, 0.025), w, M((0, 0, 0.43)))
    mb.add(p_box(0.4, 0.38, 0.06, 0.03), clay("blush"), M((0, -0.01, 0.48)))
    for x in (-0.19, 0.19):
        for y in (-0.18, 0.18):
            mb.add(p_lathe([(0, 0), (0.028, 0), (0.032, 0.02), (0.024, 0.4), (0, 0.4)], 20), w, M((x, y, 0)))
    for x in (-0.19, 0.19):
        mb.add(p_box(0.045, 0.045, 0.52, 0.018), w, M((x, 0.19, 0.71)))
    mb.add(p_box(0.46, 0.06, 0.1, 0.03), w, M((0, 0.19, 0.98)))
    for x in (-0.09, 0, 0.09):
        mb.add(p_cyl(0.017, 0.45, 0.008, 14), w, M((x, 0.19, 0.71)))
    mb.obj(col)


@item("chair_zp", "白色花園椅・ZEPETO 角色用（矮胖版、腮紅粉坐墊）", "坐餐桌喝紅酒測試")
def b_chair_zp(col):
    """ZEPETO 新郎坐著時屁股離地約 19 cm、大腿短（2026-10-12 坐餐桌測試量的）：椅墊頂 0.19 m、座面 30×26 cm、
    椅背頂 0.51 m（到背中段）；腳、椅背立柱比原版粗，黏土玩具感。不是等比縮小 chair（等比縮到 0.38 倍像矮凳、腳太細）"""
    mb = MB("ZP_chair_zp"); w = clay("white", rough=0.7)
    mb.add(p_box(0.30, 0.26, 0.04, 0.018), w, M((0, 0, 0.135)))                     # 座板（頂 0.155）
    mb.add(p_box(0.27, 0.23, 0.04, 0.02), clay("blush"), M((0, -0.008, 0.17)))       # 坐墊（頂 0.19）
    for x in (-0.12, 0.12):
        for y in (-0.10, 0.10):
            mb.add(p_lathe([(0, 0), (0.024, 0), (0.027, 0.012), (0.021, 0.12), (0, 0.12)], 20), w, M((x, y, 0)))
    for x in (-0.12, 0.12):
        mb.add(p_box(0.036, 0.036, 0.34, 0.016), w, M((x, 0.11, 0.32)))             # 椅背立柱
    mb.add(p_box(0.31, 0.05, 0.075, 0.024), w, M((0, 0.11, 0.49)))                  # 椅背頂板（頂 0.53）
    for x in (-0.055, 0.0, 0.055):
        mb.add(p_cyl(0.012, 0.29, 0.006, 14), w, M((x, 0.11, 0.31)))                 # 直條
    mb.obj(col)


def plate(mb, r, z=0.0, mat=None):
    mb.add(p_lathe([(0, z), (r * 0.6, z), (r * 0.72, z + 0.006), (r, z + 0.018), (r * 1.0, z + 0.024), (r * 0.94, z + 0.024), (r * 0.7, z + 0.012), (0, z + 0.012)], 48), mat or clay("bowl"))


def bowl(mb, r, h, mat):
    mb.add(p_lathe([(0, 0), (r * 0.45, 0), (r * 0.5, 0.012), (r * 0.85, h * 0.45), (r, h), (r * 0.92, h), (r * 0.8, h * 0.5), (r * 0.42, h * 0.2), (0, h * 0.18)], 48), mat)


@item("chicken", "烤雞（雞腿紙花、配菜）", "⑦a")
def b_chicken(col):
    rnd = random.Random(31); mb = MB("ZP_chicken")
    plate(mb, 0.21)
    mb.add(p_sphere(0.12, 0.09, 0.075, 32), clay("chicken", rough=0.5), M((0, 0.01, 0.085)))
    mb.add(p_sphere(0.07, 0.06, 0.04, 24), clay("chicken_lt", rough=0.5), M((-0.02, 0.0, 0.135)))
    for sd in (-1, 1):
        mb.add(p_sphere(0.065, 0.04, 0.038, 24), clay("chicken", rough=0.5), M((sd * 0.07, -0.07, 0.07), (0, 0, sd * 35)))
        tip = Vector((sd * 0.13, -0.135, 0.085))
        mb.add(p_tube([(sd * 0.1, -0.1, 0.075), tip], 0.011, 10), clay("bone"))
        mb.add(p_cyl(0.022, 0.04, 0.006, 16), clay("white"), M(tip + Vector((sd * 0.012, -0.012, 0.004)), (90, 0, sd * -45)))
    for _ in range(7):
        a = rnd.uniform(0, 2 * math.pi)
        mb.add(p_sphere(0.019), clay("tomato", rough=0.5), M((0.17 * math.cos(a), 0.17 * math.sin(a), 0.035)))
    for _ in range(5):
        a = rnd.uniform(0, 2 * math.pi); c = Vector((0.165 * math.cos(a), 0.165 * math.sin(a), 0.03))
        mb.add(p_cyl(0.008, 0.03, 0.003, 10), clay("cucumber"), M(c))
        for k in range(4):
            mb.add(p_sphere(0.014), clay("broc"), M(c + Vector((0.01 * math.cos(k * 1.6), 0.01 * math.sin(k * 1.6), 0.025))))
    mb.obj(col)


@item("soup", "濃湯（奶油螺旋＋麵包丁）", "⑦a")
def b_soup(col):
    rnd = random.Random(41); mb = MB("ZP_soup")
    plate(mb, 0.12)
    bowl(mb, 0.085, 0.055, clay("bowl"))
    mb.add(p_cyl(0.074, 0.006, 0.002, 40), clay("soup", rough=0.5), M((0, 0, 0.06)))
    mb.add(p_tube([(0.035 * (1 - i / 30) * math.cos(i * 0.5), 0.035 * (1 - i / 30) * math.sin(i * 0.5), 0.0645) for i in range(31)], 0.0035, 6), clay("cream"))
    for _ in range(5):
        mb.add(p_box(0.012, 0.012, 0.01, 0.003), clay("chicken_lt"), M((rnd.uniform(-0.045, 0.045), rnd.uniform(-0.045, 0.045), 0.067), (0, 0, rnd.uniform(0, 90))))
    for _ in range(6):
        mb.add(p_sphere(0.004), clay("broc"), M((rnd.uniform(-0.04, 0.04), rnd.uniform(-0.04, 0.04), 0.065)))
    mb.obj(col)


@item("salad", "沙拉（生菜、番茄、小黃瓜、玉米）", "⑦a")
def b_salad(col):
    rnd = random.Random(51); mb = MB("ZP_salad")
    bowl(mb, 0.12, 0.07, clay("salad_bowl"))
    for _ in range(16):
        mb.add(p_sphere(0.04, 0.03, 0.012, 16), clay("lettuce"), M((rnd.uniform(-0.07, 0.07), rnd.uniform(-0.07, 0.07), rnd.uniform(0.065, 0.085)), (rnd.uniform(-40, 40), rnd.uniform(-40, 40), rnd.uniform(0, 360))))
    for _ in range(5):
        mb.add(p_sphere(0.017), clay("tomato", rough=0.5), M((rnd.uniform(-0.06, 0.06), rnd.uniform(-0.06, 0.06), 0.095)))
    for _ in range(4):
        mb.add(p_cyl(0.017, 0.007, 0.003, 20), clay("cucumber"), M((rnd.uniform(-0.06, 0.06), rnd.uniform(-0.06, 0.06), 0.095), (rnd.uniform(-30, 30), 0, 0)))
    for _ in range(10):
        mb.add(p_sphere(0.006), clay("corn"), M((rnd.uniform(-0.06, 0.06), rnd.uniform(-0.06, 0.06), 0.097)))
    mb.obj(col)


@item("bottle", "紅酒瓶", "⑦a")
def b_bottle(col):
    mb = MB("ZP_bottle")
    mb.add(p_lathe([(0, 0), (0.042, 0), (0.048, 0.008), (0.048, 0.2), (0.042, 0.23), (0.02, 0.26), (0.017, 0.29), (0.017, 0.33), (0, 0.33)], 40), clay("wine", rough=0.4))
    mb.add(p_cyl(0.0195, 0.05, 0.006, 24), clay("gold", rough=0.45), M((0, 0, 0.31)))
    mb.add(p_cyl(0.0495, 0.09, 0.004, 40), clay("label"), M((0, 0, 0.12)))
    rose(mb, clay("rose"), Vector((0, -0.05, 0.125)), 0.014, None, (90, 0, 0))
    mb.obj(col)


@item("wineglass", "紅酒杯（半透明＋紅酒）", "⑦a")
def b_glass(col):
    mb = MB("ZP_wineglass")
    prof = [(0, 0), (0.038, 0), (0.04, 0.006), (0.006, 0.012), (0.006, 0.09), (0.03, 0.105), (0.045, 0.14), (0.04, 0.19), (0.037, 0.19), (0.041, 0.14), (0.028, 0.11), (0, 0.105)]
    mb.add(p_lathe(prof, 40), clay("glass", rough=0.25, sss=0.0, alpha=0.35))
    mb.add(p_lathe([(0, 0.108), (0.026, 0.112), (0.038, 0.135), (0.039, 0.145), (0, 0.145)], 40), clay("wine_liq", rough=0.3, sss=0.1))
    mb.obj(col)


@item("fork", "叉子", "⑦a")
def b_fork(col):
    mb = MB("ZP_fork"); s = clay("silver", rough=0.35, sss=0.0)
    mb.add(p_box(0.024, 0.11, 0.008, 0.0039), s, M((0, -0.055, 0.004)))
    mb.add(p_box(0.012, 0.03, 0.007, 0.0034), s, M((0, 0.014, 0.0045)))
    mb.add(p_box(0.032, 0.022, 0.007, 0.0034), s, M((0, 0.038, 0.006)))
    for i in range(4):
        mb.add(p_box(0.006, 0.04, 0.006, 0.0029), s, M((-0.012 + i * 0.008, 0.066, 0.007)))
    mb.obj(col)


@item("dessert", "甜點盤（小蛋糕、馬卡龍、莓果塔）", "⑦a")
def b_dessert(col):
    rnd = random.Random(61); mb = MB("ZP_dessert")
    plate(mb, 0.15, 0, clay("blush", "#FBE6EA"))
    mb.add(p_cyl(0.04, 0.045, 0.012, 32), clay("cake"), M((-0.05, 0.03, 0.035)))
    for k in range(10):
        a = 2 * math.pi * k / 10
        mb.add(p_sphere(0.009), clay("cream"), M((-0.05 + 0.032 * math.cos(a), 0.03 + 0.032 * math.sin(a), 0.06)))
    mb.add(p_lathe([(0, 0), (0.014, 0), (0.017, 0.012), (0.01, 0.026), (0, 0.03)], 20), clay("straw", rough=0.5), M((-0.05, 0.03, 0.058)))
    for i, c in enumerate(("lav", "macaron_g", "macaron_y")):
        p = Vector((0.06, -0.035 + i * 0.045, 0.012))
        for dz in (0, 0.019):
            mb.add(p_sphere(0.021, 0.021, 0.0085, 24), clay(c), M(p + Vector((0, 0, dz + 0.006))))
        mb.add(p_cyl(0.018, 0.006, 0.002, 24), clay("cream"), M(p + Vector((0, 0, 0.0155))))
    mb.add(p_lathe([(0, 0), (0.033, 0), (0.04, 0.008), (0.042, 0.022), (0.036, 0.022), (0, 0.016)], 32), clay("tart"), M((-0.045, -0.06, 0.012)))
    mb.add(p_cyl(0.034, 0.006, 0.002, 32), clay("cream", "#FFF1C9"), M((-0.045, -0.06, 0.032)))
    for _ in range(9):
        mb.add(p_sphere(0.008), clay(rnd.choice(["berry", "rasp"]), rough=0.5), M((-0.045 + rnd.uniform(-0.022, 0.022), -0.06 + rnd.uniform(-0.022, 0.022), 0.04)))
    mb.obj(col)


@item("fruit", "水果盤（葡萄、柳橙、草莓）", "⑦a")
def b_fruit(col):
    rnd = random.Random(71); mb = MB("ZP_fruit")
    plate(mb, 0.14)
    for layer, n in enumerate((7, 4, 1)):
        for k in range(n):
            a = 2 * math.pi * k / max(1, n); rr = 0.03 - layer * 0.013
            mb.add(p_sphere(0.016), clay("grape", rough=0.5), M((-0.04 + rr * math.cos(a), 0.03 + rr * math.sin(a), 0.03 + layer * 0.022)))
    mb.add(p_tube([(-0.04, 0.03, 0.08), (-0.035, 0.035, 0.1)], 0.003, 6), clay("trunk"))
    for i in range(3):
        mb.add(p_cyl(0.035, 0.01, 0.003, 32), clay("orange"), M((0.05 + i * 0.012, -0.03 + i * 0.01, 0.02 + i * 0.006), (60, 0, 20)))
        mb.add(p_cyl(0.028, 0.0105, 0.002, 32), clay("orange_lt"), M((0.05 + i * 0.012, -0.03 + i * 0.01, 0.02 + i * 0.006), (60, 0, 20)))
    for k in range(4):
        p = Vector((-0.02 + k * 0.03, -0.075 + rnd.uniform(-0.01, 0.01), 0.012))
        mb.add(p_lathe([(0, 0), (0.012, 0.004), (0.016, 0.018), (0.014, 0.028), (0, 0.03)], 20), clay("straw", rough=0.5), M(p, (180 - 70, 0, rnd.uniform(-40, 40)), None) @ M((0, 0, -0.03)))
        mb.add(p_sphere(0.012, 0.012, 0.004, 12), clay("leaf"), M(p + Vector((0, 0.028, 0.012)), (70, 0, 0)))
    mb.obj(col)


@item("taxi", "卡通計程車（玩具比例、TAXI 頂燈）", "⑦b")
def b_taxi(col):
    mb = MB("ZP_taxi"); y = clay("taxi", rough=0.6)
    mb.add(p_box(2.0, 1.0, 0.5, 0.2), y, M((0, 0, 0.5)))
    mb.add(p_box(1.15, 0.88, 0.45, 0.18), y, M((-0.12, 0, 0.92)))
    for sy in (-1, 1):                                              # 側窗兩片
        for x in (-0.4, 0.12):
            mb.add(p_box(0.42, 0.04, 0.27, 0.06), clay("window", rough=0.3), M((x, sy * 0.43, 0.94)))
        for i in range(10):                                         # 方格帶
            mb.add(p_box(0.09, 0.02, 0.045, 0.008), clay("tire") if i % 2 == 0 else clay("white"), M((-0.6 + i * 0.12, sy * 0.505, 0.6)))
    mb.add(p_box(0.04, 0.72, 0.28, 0.06), clay("window", rough=0.3), M((0.455, 0, 0.94)))
    mb.add(p_box(0.04, 0.72, 0.26, 0.06), clay("window", rough=0.3), M((-0.695, 0, 0.94)))
    for x in (-0.62, 0.62):
        for sy in (-1, 1):
            mb.add(p_cyl(0.27, 0.2, 0.08, 40), clay("tire"), M((x, sy * 0.45, 0.27), (90, 0, 0)))
            mb.add(p_cyl(0.13, 0.04, 0.02, 32), clay("hub"), M((x, sy * 0.56, 0.27), (90, 0, 0)))
    for sy in (-1, 1):
        mb.add(p_sphere(0.075, 0.075, 0.06, 24), clay("head", emit=2.0), M((1.0, sy * 0.3, 0.58), (0, 90, 0)))
        mb.add(p_box(0.04, 0.18, 0.1, 0.03), clay("tail", emit=2.0), M((-1.0, sy * 0.33, 0.6)))
    for x in (1.02, -1.02):
        mb.add(p_box(0.1, 0.96, 0.12, 0.05), clay("hub"), M((x, 0, 0.32)))
    mb.add(p_box(0.32, 0.16, 0.13, 0.05), clay("white", emit=0.4), M((-0.12, 0, 1.2)))
    mb.obj(col)
    for sd, rz in ((-1, 0), (1, 180)):
        text_obj(col, "TAXI", 0.075, clay("tire"), (-0.12, sd * 0.082, 1.2), (90, 0, rz), 0.004, "ZP_taxi_txt")


@item("facade", "餐廳門面（雨棚、暖光窗、招牌）", "⑦b")
def b_facade(col):
    mb = MB("ZP_facade")
    mb.add(p_box(3.2, 0.3, 2.9, 0.06), clay("wall"), M((0, 0.15, 1.45)))
    mb.add(p_box(3.24, 0.34, 0.3, 0.05), clay("wall_dk"), M((0, 0.15, 0.15)))
    mb.add(p_box(0.95, 0.08, 2.05, 0.04), clay("white"), M((0, -0.02, 1.03)))
    mb.add(p_box(0.82, 0.08, 1.95, 0.04), clay("door"), M((0, -0.04, 1.0)))
    mb.add(p_box(0.5, 0.04, 0.9, 0.06), clay("pane", emit=0.8), M((0, -0.085, 1.3)))
    mb.add(p_sphere(0.03), clay("gold", rough=0.4), M((0.3, -0.1, 1.0)))
    for x in (-1.0, 1.0):
        mb.add(p_box(0.8, 0.08, 1.0, 0.04), clay("white"), M((x, -0.02, 1.35)))
        mb.add(p_box(0.7, 0.04, 0.9, 0.05), clay("pane", emit=0.8), M((x, -0.05, 1.35)))
        mb.add(p_box(0.02, 0.05, 0.9, 0.008), clay("white"), M((x, -0.07, 1.35)))
        for i in range(6):                                          # 條紋雨棚
            mb.add(p_box(0.15, 0.42, 0.04, 0.018), clay("rose") if i % 2 == 0 else clay("cream"), M((x - 0.375 + i * 0.15, -0.2, 2.02), (-28, 0, 0)))
        for i in range(6):
            mb.add(p_sphere(0.075, 0.03, 0.055, 16), clay("rose") if i % 2 == 0 else clay("cream"), M((x - 0.375 + i * 0.15, -0.39, 1.9)))
        mb.add(p_box(0.82, 0.2, 0.12, 0.05), clay("white"), M((x, -0.1, 0.78)))
        for i in range(4):
            mb.add(p_sphere(0.07), clay("hedge"), M((x - 0.3 + i * 0.2, -0.12, 0.88)))
            daisy(mb, clay("blush"), clay("butter"), (x - 0.3 + i * 0.2, -0.19, 0.92), 0.03)
    mb.add(p_box(1.3, 0.08, 0.34, 0.05), clay("sign"), M((0, -0.02, 2.52)))
    for x in (-0.6, 0.6):
        mb.add(p_sphere(0.06), clay("pane", emit=4.0), M((x, -0.12, 2.25)))
        mb.add(p_box(0.04, 0.12, 0.04, 0.015), clay("navy"), M((x, -0.06, 2.3)))
    mb.obj(col)
    text_obj(col, "BISTRO", 0.2, clay("label", emit=0.5), (0, -0.065, 2.52), (90, 0, 0), 0.006, "ZP_facade_txt")


@item("lamp", "路燈", "⑦b")
def b_lamp(col):
    mb = MB("ZP_lamp")
    mb.add(p_cyl(0.14, 0.16, 0.05, 32), clay("navy"), M((0, 0, 0.08)))
    mb.add(p_cyl(0.045, 2.7, 0.015, 24), clay("navy"), M((0, 0, 1.5)))
    mb.add(p_torus(0.25, 0.045, 0, math.pi / 2, 16, 14), clay("navy"), M((0.25, 0, 2.85), (90, 0, 180)))
    mb.add(p_lathe([(0, 0.0), (0.06, 0.0), (0.16, -0.1), (0.15, -0.13), (0, -0.12)], 32), clay("navy"), M((0.5, 0, 3.1)))
    mb.add(p_sphere(0.09, 0.09, 0.06, 24), clay("pane", emit=6.0), M((0.5, 0, 2.98)))
    mb.add(p_sphere(0.05), clay("navy"), M((0, 0, 2.86)))
    mb.obj(col)


@item("planter", "盆栽（圓灌木、高灌木）", "⑦b")
def b_planter(col):
    for i, (x, tall) in enumerate(((-0.35, False), (0.35, True))):
        mb = MB("ZP_planter_%d" % i)
        mb.add(p_lathe([(0, 0), (0.15, 0), (0.17, 0.02), (0.2, 0.3), (0.23, 0.32), (0.23, 0.36), (0.19, 0.36), (0, 0.33)], 40), clay("pot"), M((x, 0, 0)))
        if tall:
            for j, (dz, r) in enumerate(((0.55, 0.19), (0.82, 0.16), (1.04, 0.12))):
                mb.add(p_sphere(r), clay("hedge"), M((x, 0, dz)))
        else:
            for (dx, dy, dz, r) in ((0, 0, 0.55, 0.24), (0.12, -0.06, 0.48, 0.15), (-0.13, -0.04, 0.5, 0.15)):
                mb.add(p_sphere(r), clay("leaf"), M((x + dx, dy, dz)))
        mb.obj(col)


@item("street", "人行道＋馬路（方磚、車道線）", "⑦b")
def b_street(col):
    mb = MB("ZP_street")
    for i in range(6):
        for j in range(3):
            mb.add(p_box(0.48, 0.48, 0.12, 0.03), clay("walk") if (i + j) % 2 == 0 else clay("walk_dk"), M((-1.25 + i * 0.5, 0.5 + j * 0.5, 0.06)))
    mb.add(p_box(3.0, 0.16, 0.14, 0.05), clay("white", "#EDEBF2"), M((0, 0.17, 0.07)))
    mb.add(p_box(3.0, 2.0, 0.04, 0.015), clay("road"), M((0, -0.92, 0.02)))
    for i in range(4):
        mb.add(p_box(0.45, 0.07, 0.012, 0.006), clay("lane", emit=0.2), M((-1.2 + i * 0.8, -1.3, 0.042)))
    mb.obj(col)


# ── 攝影棚（refs/photo_studio/analysis.md）──
def cstand(mb, h=2.0, base_r=0.55):
    """C 型燈架：三支往下彎的腳（高度錯開）＋套環＋伸縮立柱（兩個關節、藍色握把）＋頂上夾頭；回傳頂端高度"""
    st = clay("steel", rough=0.45); gr = clay("gear")
    for k in range(3):
        a = 2 * math.pi * k / 3 - math.pi / 2; d = Vector((math.cos(a), math.sin(a), 0)); zc = 0.42 - 0.07 * k
        p0, c1, p2 = Vector((0, 0, zc)), d * 0.42 + Vector((0, 0, zc)), d * base_r + Vector((0, 0, 0.035))
        pts = [(1 - t) ** 2 * p0 + 2 * (1 - t) * t * c1 + t * t * p2 for t in [i / 12 for i in range(13)]]
        mb.add(p_tube(pts, 0.022, 10), st)
        mb.add(p_sphere(0.045, 0.045, 0.03, 14), gr, M(p2 - Vector((0, 0, 0.005))))
    mb.add(p_cyl(0.05, 0.32, 0.015, 24), gr, M((0, 0, 0.34)))
    mb.add(p_cyl(0.032, 0.75, 0.01, 20), st, M((0, 0, 0.85)))
    mb.add(p_cyl(0.046, 0.09, 0.015, 20), gr, M((0, 0, 1.22)))
    mb.add(p_cyl(0.038, 0.14, 0.012, 20), clay("grip"), M((0, 0, 1.05)))
    mb.add(p_cyl(0.027, h * 0.8 - 1.22, 0.008, 20), st, M((0, 0, (1.22 + h * 0.8) / 2)))
    mb.add(p_cyl(0.042, 0.08, 0.012, 20), gr, M((0, 0, h * 0.8)))
    mb.add(p_cyl(0.022, h * 0.2, 0.006, 16), st, M((0, 0, h * 0.9)))
    mb.add(p_cyl(0.05, 0.11, 0.015, 20), gr, M((0, 0, h), (0, 90, 0)))
    mb.add(p_sphere(0.03), gr, M((0.075, 0, h)))
    return h


def light_head(mb, top, w=0.24, d=0.34, hgt=0.24):
    """燈頭：U 型支架＋圓角燈身（正面朝 -Y）"""
    gr = clay("gear")
    mb.add(p_box(w + 0.08, 0.05, 0.04, 0.015), gr, M((0, 0.04, top + 0.03)))
    for sx in (-1, 1):
        mb.add(p_box(0.03, 0.05, 0.16, 0.012), gr, M((sx * (w / 2 + 0.03), 0.04, top + 0.11)))
    mb.add(p_box(w, d, hgt, 0.06), gr, M((0, 0.04, top + 0.17)))
    mb.add(p_cyl(0.06, 0.06, 0.02, 24), clay("steel", rough=0.45), M((0, 0.04 + d / 2 + 0.02, top + 0.17), (90, 0, 0)))
    return Vector((0, 0.04 - d / 2, top + 0.17))                       # 燈頭正面中心（接燈罩的地方）


@item("c_stand", "C 型燈架（空架）", "（未用）", cat="studio:攝影棚")
def b_c_stand(col):
    mb = MB("ZP_c_stand"); cstand(mb, 2.0); mb.obj(col)


@item("softbox_light", "八角深口柔光罩燈（含燈架）", "（未用）", cat="studio:攝影棚")
def b_softbox_light(col):
    mb = MB("ZP_softbox_light")
    top = cstand(mb, 2.0); front = light_head(mb, top)
    shell = [(0.1, 0), (0.16, 0.02), (0.38, 0.25), (0.55, 0.5), (0.62, 0.66), (0.63, 0.69), (0.6, 0.69), (0.535, 0.52), (0.36, 0.27), (0.15, 0.05), (0.1, 0.04)]
    Ms = M(front, (105, 0, 0)) @ M((0, 0, 0), (0, 0, 22.5))            # 開口朝 -Y、往下 15°；八邊形的平邊朝下
    mb.add(p_lathe(shell, 8), clay("gear"), Ms)
    mb.add(p_lathe([(0, 0.655), (0.6, 0.655), (0.6, 0.668), (0, 0.668)], 8), clay("diffuser", emit=0.35), Ms)
    mb.add(p_cyl(0.11, 0.05, 0.015, 8), clay("steel", rough=0.45), Ms @ M((0, 0, 0.01), (0, 0, 22.5)))
    mb.obj(col)


@item("beauty_dish_light", "雷達罩燈（白色柔光布套、含燈架）", "（未用）", cat="studio:攝影棚")
def b_beauty_dish_light(col):
    mb = MB("ZP_beauty_dish_light")
    top = cstand(mb, 1.9); front = light_head(mb, top, 0.2, 0.28, 0.2)
    Md = M(front, (100, 0, 0))
    mb.add(p_lathe([(0.06, 0), (0.12, 0.01), (0.22, 0.07), (0.27, 0.16), (0.285, 0.22), (0.28, 0.235), (0.265, 0.22), (0.25, 0.16),
                    (0.2, 0.08), (0.1, 0.03), (0.06, 0.025)], 48), clay("gear"), Md)
    mb.add(p_lathe([(0, 0.275), (0.15, 0.266), (0.24, 0.248), (0.29, 0.226), (0.297, 0.212), (0.287, 0.2), (0, 0.2)], 48), clay("diffuser", emit=0.25), Md)
    mb.add(p_torus(0.291, 0.012, 0, 2 * math.pi, 48, 10), clay("steel", rough=0.45), Md @ M((0, 0, 0.214)))
    mb.obj(col)


@item("video_camera", "攝影機（三腳架、油壓雲台搖桿、頂上監看螢幕）", "（未用）", cat="studio:攝影棚")
def b_video_camera(col):
    """refs/photo_studio/ref_2.png 左前方那台＋右邊那台的遮光斗；鏡頭朝 -Y、攝影師站 +Y 那側（看得到監看螢幕）"""
    mb = MB("ZP_video_camera"); gr = clay("gear"); st = clay("steel", rough=0.45)
    top, foot_r = 1.12, 0.46
    for k in range(3):                                                   # 三腳架：上粗下細兩節＋腳墊＋中段支撐桿
        a = 2 * math.pi * k / 3 + math.pi / 2; d = Vector((math.cos(a), math.sin(a), 0))
        p0 = d * 0.065 + Vector((0, 0, top)); p1 = d * foot_r
        mid = p0.lerp(p1, 0.55)
        mb.add(p_tube([p0, mid], 0.024, 12), gr)
        mb.add(p_tube([mid, p1 + Vector((0, 0, 0.03))], 0.017, 12), st)
        mb.add(p_cyl(0.03, 0.05, 0.012, 16), clay("grip"), M(mid))
        mb.add(p_sphere(0.035, 0.035, 0.025, 14), gr, M(p1 + Vector((0, 0, 0.02))))
        f = (top - 0.42) / top; sp = p0.lerp(p1, f)
        mb.add(p_tube([(0, 0, 0.42), (sp.x, sp.y, sp.z)], 0.011, 8), st)
    mb.add(p_cyl(0.026, top - 0.42, 0.008, 16), st, M((0, 0, (top + 0.42) / 2)))   # 中柱
    mb.add(p_cyl(0.04, 0.05, 0.015, 16), gr, M((0, 0, 0.42)))
    mb.add(p_cyl(0.085, 0.05, 0.018, 24), gr, M((0, 0, top + 0.02)))              # 腳架頂盤
    mb.add(p_box(0.13, 0.15, 0.12, 0.03), gr, M((0, 0, top + 0.1)))               # 油壓雲台
    mb.add(p_cyl(0.035, 0.16, 0.012, 16), gr, M((0.085, 0, top + 0.1), (0, 90, 0)))
    pb0 = Vector((0.03, 0.08, top + 0.1)); pb1 = Vector((0.2, 0.62, top - 0.18))    # 搖桿斜向後下方
    mb.add(p_tube([pb0, pb1], 0.014, 10), st)
    mb.add(p_tube([pb1.lerp(pb0, 0.22), pb1], 0.024, 12), gr)
    mb.add(p_box(0.11, 0.26, 0.03, 0.01), gr, M((0, -0.01, top + 0.175)))          # 快拆板
    cz = top + 0.27                                                                  # 機身中心高
    mb.add(p_box(0.16, 0.24, 0.16, 0.035), gr, M((0, 0, cz)))                      # 機身
    mb.add(p_box(0.13, 0.06, 0.1, 0.02), clay("steel", "#8E8A98", rough=0.5), M((0, 0.15, cz - 0.01)))   # 電池
    mb.add(p_cyl(0.052, 0.05, 0.012, 32), gr, M((0, -0.145, cz), (90, 0, 0)))      # 鏡頭接環
    mb.add(p_cyl(0.047, 0.15, 0.012, 32), gr, M((0, -0.235, cz), (90, 0, 0)))      # 鏡頭
    for yy in (-0.2, -0.26):
        mb.add(p_cyl(0.051, 0.025, 0.008, 32), clay("grip"), M((0, yy, cz), (90, 0, 0)))   # 對焦環
    mb.add(p_cyl(0.04, 0.008, 0.003, 32), clay("lens", rough=0.25), M((0, -0.312, cz), (90, 0, 0)))
    for sz in (-1, 1):                                                               # 方形遮光斗（右邊那台）
        mb.add(p_box(0.22, 0.12, 0.014, 0.006), gr, M((0, -0.37, cz + sz * 0.085)))
    for sx in (-1, 1):
        mb.add(p_box(0.014, 0.12, 0.17, 0.006), gr, M((sx * 0.105, -0.37, cz)))
    for yy in (-0.07, 0.07):                                                         # 頂上提把
        mb.add(p_box(0.025, 0.025, 0.05, 0.008), gr, M((0, yy, cz + 0.1)))
    mb.add(p_box(0.035, 0.2, 0.03, 0.012), gr, M((0, 0, cz + 0.135)))
    mb.add(p_tube([(0, -0.06, cz + 0.15), (0, -0.05, cz + 0.2)], 0.012, 8), gr)    # 監看螢幕支臂
    Mm = M((0, -0.04, cz + 0.27), (-12, 0, 0))                                      # 螢幕往後仰，畫面朝攝影師（+Y）
    mb.add(p_box(0.22, 0.025, 0.14, 0.012), gr, Mm)
    mb.add(p_box(0.195, 0.004, 0.115, 0.004), clay("screen", rough=0.35, emit=0.6), Mm @ M((0, 0.013, 0)))
    mb.obj(col)


@item("studio_backdrop", "白色背景紙卷（無縫彎弧＋捲軸、掛鉤）", "（未用）", cat="studio:攝影棚")
def b_studio_backdrop(col):
    W, H, R, L = 2.72, 2.88, 0.6, 2.3                                    # 寬、垂下高度、底部彎弧半徑、鋪到地上的長度
    prof = [(0.0, H - i * (H - R) / 10) for i in range(11)]
    prof += [(-R + R * math.cos(math.radians(t)), R - R * math.sin(math.radians(t))) for t in range(6, 91, 6)]
    prof += [(-R - (L - R) * i / 8, 0.0) for i in range(1, 9)]
    bm = bmesh.new(); xs = [-W / 2 + W * j / 6 for j in range(7)]
    rows = [[bm.verts.new((x, y, z + 0.004)) for x in xs] for (y, z) in prof]
    for A, B in zip(rows, rows[1:]):
        for j in range(6):
            f = bm.faces.new((A[j], A[j + 1], B[j + 1], B[j])); f.smooth = True
    me = bpy.data.meshes.new("ZP_backdrop_paper"); bm.to_mesh(me); bm.free(); me.materials.append(clay("paper", rough=0.85))
    ob = bpy.data.objects.new("ZP_backdrop_paper", me); col.objects.link(ob)
    so = ob.modifiers.new("ZP_Thick", "SOLIDIFY"); so.thickness = 0.008; so.offset = 1.0
    mb = MB("ZP_backdrop_rig"); gr = clay("gear"); st = clay("steel", rough=0.45)
    mb.add(p_cyl(0.075, W + 0.06, 0.02, 32), clay("paper", rough=0.85), M((0, 0.075, H + 0.04), (0, 90, 0)))
    mb.add(p_cyl(0.1, W + 0.02, 0.025, 32), clay("blackout"), M((0, -0.05, H + 0.2), (0, 90, 0)))
    mb.add(p_cyl(0.018, W + 0.5, 0.006, 16), st, M((0, 0.01, H + 0.12), (0, 90, 0)))
    for sx in (-1, 1):
        mb.add(p_box(0.06, 0.3, 0.42, 0.02), gr, M((sx * (W / 2 + 0.2), 0.05, H + 0.12)))
        mb.add(p_box(0.12, 0.06, 0.6, 0.02), gr, M((sx * (W / 2 + 0.2), 0.22, H + 0.12)))
    mb.obj(col)


# ── 婚宴會館（開場片提案 B，2026-10-12；場景外掛 scenes/venue_*.py）──
# 比例照 ZEPETO 新郎身體（body-v8）：身高 1.50 m、骨盆 0.64 m、肩 1.10 m、手肘約 0.8 m、手長 11.4 cm。
#   建築（門、柱、牆）接近真人尺寸（門高 2.1 m）；手會碰到的家具與小物照 ZEPETO 的腿長、手長縮
#   （餐檯面 0.6 m、蛋糕直徑 4.5 cm、鑰匙 7 cm、相機寬 10.5 cm）。
# 門類道具的原點在牆的正面（y＝0）、門洞底部中心；門片是獨立物件、原點在門軸，append_prop 後轉 rotation_euler.z 就能開門。
def door_casing(mb, w, h, mat, trim, depth=0.2, cw=0.1, ct=0.04):
    """門洞的框：正面一圈飾條（寬 cw、凸出 ct）＋包住牆厚 depth 的門側板＋頂上一條線板；門洞 x∈[-w/2, w/2]、z∈[0, h]"""
    for sx in (-1, 1):
        mb.add(p_box(cw, ct, h + cw, 0.012), mat, M((sx * (w / 2 + cw / 2), -ct / 2, (h + cw) / 2)))
        mb.add(p_box(0.03, depth, h, 0.008), mat, M((sx * (w / 2 + 0.015), depth / 2, h / 2)))
    mb.add(p_box(w + 2 * cw + 0.04, ct + 0.01, cw, 0.012), mat, M((0, -(ct + 0.01) / 2, h + cw / 2)))
    mb.add(p_box(w, depth, 0.03, 0.008), mat, M((0, depth / 2, h + 0.015)))
    mb.add(p_box(w + 2 * cw + 0.1, ct + 0.03, 0.035, 0.012), trim, M((0, -(ct + 0.03) / 2, h + cw + 0.0175)))


def text_at(col, body, size, mat, Mw, extrude=0.003, name="ZP_Text", font=None):
    """文字放在任意矩陣 Mw（文字本身朝 -Y 的版本再乘上 Mw）"""
    ob = text_obj(col, body, size, mat, (0, 0, 0), (0, 0, 0), extrude, name, font)
    ob.matrix_world = Mw @ M((0, 0, 0), (90, 0, 0))
    return ob


@item("lounge_door", "休息室門（單扇、往外推開、含門框與門把）", "提案B B0", cat="venue:婚宴會館")
def b_lounge_door(col):
    """門洞 0.75×1.75 m（照 ZEPETO 比例縮：新郎 1.48 m，真實 2.1 m 的門會讓角色顯得太小；2026-10-12 動畫端 B0 走位定的），
    門框包住 0.2 m 牆厚。鏡頭看過去門軸在左（x＝-0.375）、門把在右，高 0.8 m。
    門片 ZP_lounge_door_leaf 原點在門軸：rotation_euler.z 從 0 轉到 -90° 是往鏡頭這側（-Y）全開；新郎在門裡用右手推門把那側，
    門往左邊打開，兩人出門後往右走不會撞到門片"""
    W, H = 0.75, 1.75
    fr = MB("ZP_lounge_door_frame"); door_casing(fr, W, H, clay("white", rough=0.7), clay("trim")); fr.obj(col)
    lf = MB("ZP_lounge_door_leaf"); g = clay("gold", rough=0.4); wh = clay("white", rough=0.7)
    lw, t, y0 = W - 0.012, 0.05, 0.005                                     # 門片寬、厚、正面離牆面
    cx = 0.006 + lw / 2
    lf.add(p_box(lw, t, H - 0.012, 0.012), clay("door_lt"), M((cx, y0 + t / 2, (H - 0.012) / 2 + 0.004)))
    for z0, z1 in ((0.13, 0.6), (0.82, 1.62)):                             # 兩面各兩塊凸起門板
        for yy in (y0 - 0.004, y0 + t + 0.004):
            lf.add(p_box(lw - 0.18, 0.012, z1 - z0, 0.006), wh, M((cx, yy, (z0 + z1) / 2)))
    hx = 0.006 + lw - 0.08
    for sd, yy in ((-1, y0), (1, y0 + t)):                                 # 兩面都有拉桿門把（桿子朝門軸那側）
        lf.add(p_cyl(0.028, 0.012, 0.004, 24), g, M((hx, yy + sd * 0.006, 0.8), (90, 0, 0)))
        lf.add(p_tube([(hx, yy + sd * 0.01, 0.8), (hx, yy + sd * 0.05, 0.8), (hx - 0.1, yy + sd * 0.055, 0.8)], 0.011, 12), g)
    lf.add(p_box(0.27, 0.012, 0.09, 0.006), g, M((cx, y0 - 0.012, 1.25)))      # 正面名牌
    leaf = lf.obj(col, loc=(-W / 2, 0.0, 0.0))
    txt = text_obj(col, "Lounge", 0.052, clay("door"), (cx, y0 - 0.0195, 1.25), (90, 0, 0), 0.002, "ZP_lounge_door_txt")
    txt.parent = leaf                                                      # 名牌字跟著門片轉


@item("ballroom_doors", "宴會廳雙開大門（往內自動開、門後暖白強光）", "提案B B6", cat="venue:婚宴會館")
def b_ballroom_doors(col):
    """門洞 1.7×2.2 m（照休息室門同比例縮，約真實尺寸的 0.83 倍），門框包住 0.2 m 牆厚。左右門片各一個物件、原點在門軸（門片背面那條邊）：
    ZP_ballroom_door_L 的 rotation_euler.z 從 0 → +90° 往內（+Y）全開；ZP_ballroom_door_R 從 0 → -90°。
    門後是 1.6 m 深的發光通道 ZP_ballroom_doors_glow：背板材質 ZP_glow_back（Emission Strength 預設 6，可打關鍵影格做強光漸亮）。
    發光材質在 EEVEE 照不太亮外面的角色，要打光的話在通道裡加一盞朝 -Y 的面光（場景外掛 venue_foyer 有示範）"""
    W, H, T = 1.7, 2.2, 0.06
    wh = clay("white", rough=0.7); gd = clay("gold", rough=0.4)
    fr = MB("ZP_ballroom_doors_frame"); door_casing(fr, W, H, wh, gd, cw=0.15, ct=0.06)
    fr.add(p_box(W + 0.52, 0.12, 0.12, 0.03), wh, M((0, -0.06, H + 0.15 + 0.1)))          # 頂上檐口
    fr.add(p_box(0.85, 0.08, 0.3, 0.11), wh, M((0, -0.05, H + 0.15 + 0.31)))               # 中間飾板
    fr.add(p_sphere(0.08, 0.03, 0.08, 24), gd, M((0, -0.1, H + 0.15 + 0.31)))              # 金色徽章
    for sx in (-1, 1):
        rose(fr, clay("blush"), (sx * 0.18, -0.1, H + 0.15 + 0.31), 0.045, None, (90, 0, 0))
    fr.obj(col)
    for sd, nm in ((-1, "L"), (1, "R")):
        lf = MB("ZP_ballroom_door_" + nm); lw = W / 2 - 0.008; cx = -sd * (lw / 2 + 0.004)
        lf.add(p_box(lw, T, H - 0.01, 0.015), clay("door_lt"), M((cx, -T / 2, (H - 0.01) / 2 + 0.005)))
        for z0, z1 in ((0.17, 0.85), (1.02, 2.05)):                                           # 正面兩塊門板＋金色邊線
            zc, ph, pw = (z0 + z1) / 2, z1 - z0, lw - 0.2
            lf.add(p_box(pw, 0.012, ph, 0.006), wh, M((cx, -T - 0.004, zc)))
            for dx in (-1, 1):
                lf.add(p_box(0.016, 0.01, ph - 0.06, 0.004), gd, M((cx + dx * (pw / 2 - 0.04), -T - 0.012, zc)))
            for dz in (-1, 1):
                lf.add(p_box(pw - 0.06, 0.01, 0.016, 0.004), gd, M((cx, -T - 0.012, zc + dz * (ph / 2 - 0.04))))
        hx = -sd * (lw - 0.07)                                                             # 靠中縫的直立長把手
        lf.add(p_cyl(0.017, 0.52, 0.007, 16), gd, M((hx, -T - 0.055, 0.9)))
        for dz in (-0.22, 0.22):
            lf.add(p_tube([(hx, -T, 0.9 + dz), (hx, -T - 0.055, 0.9 + dz)], 0.01, 10), gd)
        lf.obj(col, loc=(sd * W / 2, 0.1, 0.0))                                           # 門片正面 y＝0.04、背面（門軸）y＝0.10
    gl = MB("ZP_ballroom_doors_glow"); D0, D1 = 0.2, 1.8
    side = clay("glow_side", PAL["glow"], emit=2.0)
    gl.add(p_box(W + 0.2, 0.05, H + 0.35, 0.01), clay("glow_back", PAL["glow"], emit=6.0), M((0, D1, (H + 0.35) / 2)))
    for sx in (-1, 1):
        gl.add(p_box(0.05, D1 - D0, H + 0.35, 0.01), side, M((sx * (W / 2 + 0.06), (D0 + D1) / 2, (H + 0.35) / 2)))
    gl.add(p_box(W + 0.2, D1 - D0, 0.05, 0.01), side, M((0, (D0 + D1) / 2, H + 0.35)))
    gl.add(p_box(W + 0.2, D1 - D0, 0.04, 0.01), clay("glow_floor", "#F7E6CF", emit=1.2), M((0, (D0 + D1) / 2, -0.02)))
    gl.obj(col)


@item("pillar", "圓柱（米白＋金色線板；前景遮擋用）", "提案B B3→B4", cat="venue:婚宴會館")
def b_pillar(col):
    """高 3.0 m（鏡頭 3 m 側拍時上下都出畫，從鏡頭前掃過就整片遮住）；柱身直徑 0.5 m、表面一圈直條紋，柱座與柱頭 0.66 m 見方"""
    mb = MB("ZP_pillar"); w = clay("pillar", rough=0.7); gd = clay("gold", rough=0.4)
    mb.add(p_box(0.66, 0.66, 0.16, 0.03), w, M((0, 0, 0.08)))
    mb.add(p_lathe([(0, 0.16), (0.31, 0.16), (0.31, 0.2), (0.28, 0.23), (0.26, 0.26), (0, 0.26)], 48), w)
    mb.add(p_cyl(0.25, 2.5, 0.02, 48), w, M((0, 0, 1.51)))
    for k in range(16):                                                    # 直條紋
        a = 2 * math.pi * k / 16
        mb.add(p_cyl(0.022, 2.2, 0.01, 12), w, M((0.245 * math.cos(a), 0.245 * math.sin(a), 1.51)))
    for z in (0.32, 2.7):
        mb.add(p_torus(0.262, 0.02, 0, 2 * math.pi, 48, 10), gd, M((0, 0, z)))
    mb.add(p_lathe([(0, 2.74), (0.26, 2.74), (0.28, 2.78), (0.31, 2.82), (0.31, 2.86), (0, 2.86)], 48), w)
    mb.add(p_box(0.66, 0.66, 0.14, 0.03), w, M((0, 0, 2.93)))
    mb.obj(col)


@item("door_frame", "門框（獨立的門洞框；前景遮擋用）", "提案B B5→B6", cat="venue:婚宴會館")
def b_door_frame(col):
    """門洞 1.7×2.1 m（照休息室門同比例縮）；兩側門柱 0.32 m 寬、0.3 m 深，連頂上橫楣總高 2.6 m，正面朝 -Y。
    當前景遮擋時只讓一側門柱掃過鏡頭（另一側離 2.0 m，鏡頭停下時在畫面外）"""
    mb = MB("ZP_door_frame"); w = clay("pillar", rough=0.7); gd = clay("gold", rough=0.4)
    W, H, jw, jd = 1.7, 2.1, 0.32, 0.3
    for sx in (-1, 1):
        x = sx * (W / 2 + jw / 2)
        mb.add(p_box(jw + 0.08, jd + 0.08, 0.18, 0.03), w, M((x, 0, 0.09)))
        mb.add(p_box(jw, jd, H, 0.03), w, M((x, 0, H / 2)))
        mb.add(p_box(0.11, 0.012, H - 0.45, 0.005), clay("trim"), M((x, -jd / 2 - 0.003, H / 2 + 0.05)))   # 正面凹框
        mb.add(p_box(0.02, 0.01, H - 0.55, 0.004), gd, M((x, -jd / 2 - 0.01, H / 2 + 0.05)))
    mb.add(p_box(W + 2 * jw + 0.1, jd + 0.08, 0.32, 0.04), w, M((0, 0, H + 0.16)))
    mb.add(p_box(W + 2 * jw + 0.2, jd + 0.14, 0.12, 0.04), w, M((0, 0, H + 0.38)))
    mb.add(p_box(W + 2 * jw, 0.012, 0.035, 0.006), gd, M((0, -jd / 2 - 0.046, H + 0.16)))
    mb.obj(col)


@item("buffet_table", "自助餐長檯（落地桌巾、薰衣草垂幔）", "提案B B2", cat="venue:婚宴會館")
def b_buffet_table(col):
    """1.8×0.35 m、檯面高 0.60 m（真人餐檯 0.76 m 照 ZEPETO 腿長縮；角色手肘約 0.8 m，站著伸手就拿得到）。
    2026-10-12 從 2.4×0.65 縮成 1.8×0.45；2026-10-13 再縮深到 0.35、垂幔與玫瑰貼近桌邊（最多凸出檯面前緣 3 cm），
    讓新娘裙擺（走 y 0.69、半徑 0.32）過得去。
    客人那側（垂幔）朝 -Y；不是素材庫的圓桌 table"""
    L, D, Hh = 1.8, 0.35, 0.6
    mb = MB("ZP_buffet_table"); cl = clay("cloth"); lav = clay("lav")
    mb.add(p_box(L + 0.04, D + 0.04, 0.05, 0.02), cl, M((0, 0, Hh - 0.025)))
    mb.add(p_box(L - 0.04, D - 0.04, Hh - 0.04, 0.02), cl, M((0, 0, (Hh - 0.04) / 2)))
    n = 12
    for i in range(n):                                                     # 正面、背面的布褶（下面略寬）
        x = -L / 2 + (i + 0.5) * L / n
        for sy in (-1, 1):
            mb.add(p_cyl(0.085, Hh - 0.04, 0.02, 20, rad2=0.07), cl, M((x, sy * (D / 2 - 0.05), (Hh - 0.04) / 2)))
    for j in range(3):                                                     # 側面布褶
        y = -D / 2 + (j + 0.5) * D / 3
        for sx in (-1, 1):
            mb.add(p_cyl(0.085, Hh - 0.04, 0.02, 20, rad2=0.07), cl, M((sx * (L / 2 - 0.05), y, (Hh - 0.04) / 2)))
    k = 3; sw = L / k
    for i in range(k):                                                     # 正面三段垂幔＋接點的玫瑰
        x = -L / 2 + (i + 0.5) * sw
        mb.add(p_torus(sw / 2, 0.028, math.pi, 2 * math.pi, 24, 10), lav, M((x, -D / 2 - 0.02, Hh - 0.04), (90, 0, 0), (1, 1, 0.45)))
    for i in range(k + 1):
        x = -L / 2 + i * sw
        rose(mb, clay("blush"), (x * 0.985, -D / 2 - 0.035, Hh - 0.045), 0.035, None, (90, 0, 0))
    mb.obj(col)


@item("mini_cake", "單塊小蛋糕（杯子蛋糕・ZEPETO 手拿大小）", "提案B B2", cat="dinner:晚餐桌")
def b_mini_cake(col):
    """紙杯直徑 4.3 cm、全高 6.4 cm（ZEPETO 手長 11.4 cm）：拇指和食指、中指捏紙杯兩側（z 0.5～2.2 cm）；一口塞進嘴"""
    mb = MB("ZP_mini_cake")
    bm = p_lathe([(0, 0), (0.0165, 0), (0.0175, 0.002), (0.0215, 0.022), (0.0205, 0.0228), (0, 0.022)], 64)
    for v in bm.verts:                                                     # 紙杯的直條摺痕
        if 0.0015 < v.co.z < 0.0225:
            a = math.atan2(v.co.y, v.co.x); s = 1 + 0.045 * math.cos(16 * a)
            v.co.x *= s; v.co.y *= s
    mb.add(bm, clay("cupcake"))
    mb.add(p_sphere(0.0205, 0.0205, 0.009, 32), clay("sponge"), M((0, 0, 0.0225)))
    mb.add(p_lathe([(0, 0.022), (0.0215, 0.024), (0.0225, 0.03), (0.0175, 0.0355), (0.0185, 0.039), (0.0135, 0.045),
                    (0.014, 0.0475), (0.0075, 0.0525), (0, 0.0545)], 48), clay("frosting"))
    mb.add(p_lathe([(0, 0), (0.0065, 0.002), (0.0085, 0.006), (0.006, 0.011), (0, 0.0125)], 24), clay("straw", rough=0.5), M((0, 0, 0.051)))
    for k in range(3):
        a = 2 * math.pi * k / 3
        mb.add(p_sphere(0.004, 0.002, 0.0012, 10), clay("leaf"), M((0.003 * math.cos(a), 0.003 * math.sin(a), 0.0635), (0, 0, math.degrees(a))))
    rnd = random.Random(5)
    for _ in range(9):                                                     # 糖珠
        a = rnd.uniform(0, 2 * math.pi); z = rnd.uniform(0.03, 0.046); r = 0.0215 - (z - 0.024) * 0.55
        mb.add(p_sphere(0.0016), clay(rnd.choice(["lav", "butter", "macaron_g"])), M((r * math.cos(a), r * math.sin(a), z)))
    mb.obj(col)


@item("valet_sign", "代客泊車 A 字立牌（P 圖示、車子圖示）", "提案B B3", cat="venue:婚宴會館")
def b_valet_sign(col):
    """高 0.9 m、寬 0.52 m（ZEPETO 角色腰到胸口高）；兩片牌面往後靠成 A 字，正面朝 -Y。牌面是固定圖示（VALET／P／車／PARKING），不用換字"""
    tl, Lp, Wd = 11.0, 0.915, 0.52
    wood = clay("trunk"); face = clay("valet"); wh = clay("white", rough=0.7)
    mb = MB("ZP_valet_sign")
    for sd in (-1, 1):                                                     # sd＝-1 正面那片（朝 -Y）、+1 背面那片
        Mp = M((0, sd * Lp / 2 * math.sin(math.radians(tl)), Lp / 2 * math.cos(math.radians(tl))), (sd * tl, 0, 0))
        mb.add(p_box(Wd, 0.03, Lp, 0.014), wood, Mp)
        mb.add(p_box(Wd - 0.07, 0.036, Lp - 0.1, 0.01), face, Mp)
        if sd < 0:
            Mf = lambda x, z, ry=0.0: Mp @ M((x, -0.022, z), (0, ry, 0))
            mb.add(p_box(0.38, 0.008, 0.095, 0.03), wh, Mf(0, 0.31))
            mb.add(p_cyl(0.125, 0.008, 0.003, 48), wh, Mp @ M((0, -0.022, 0.08), (90, 0, 0)))
            mb.add(p_box(0.21, 0.008, 0.055, 0.022), wh, Mf(0, -0.17))                          # 小車
            mb.add(p_box(0.12, 0.008, 0.06, 0.022), wh, Mf(-0.01, -0.125))
            for x in (-0.06, 0.06):
                mb.add(p_cyl(0.022, 0.012, 0.004, 24), face, Mp @ M((x, -0.025, -0.2), (90, 0, 0)))
                mb.add(p_cyl(0.013, 0.014, 0.004, 24), wh, Mp @ M((x, -0.027, -0.2), (90, 0, 0)))
            front = Mp
    mb.add(p_box(0.08, 0.06, 0.04, 0.015), clay("gear"), M((0, 0, Lp * math.cos(math.radians(tl)) - 0.01)))   # 頂上鉸鏈
    for sx in (-1, 1):                                                     # 兩側防滑繩
        mb.add(p_tube([(sx * (Wd / 2 - 0.03), -0.11, 0.3), (sx * (Wd / 2 - 0.03), 0.11, 0.3)], 0.005, 8), clay("gear"))
    mb.obj(col)
    text_at(col, "VALET", 0.072, face, front @ M((0, -0.027, 0.31)), 0.003, "ZP_valet_txt1")
    text_at(col, "P", 0.2, face, front @ M((0, -0.027, 0.085)), 0.004, "ZP_valet_txt2")
    text_at(col, "PARKING", 0.062, wh, front @ M((0, -0.023, -0.31)), 0.003, "ZP_valet_txt3")


@item("car_key", "車鑰匙（圓鑰匙圈＋一支遙控鑰匙；縮小版）", "提案B B3", cat="daily:日常小物")
def b_car_key(col):
    """全長 7.3 cm（ZEPETO 手長 11.4 cm）：鑰匙圈在最上面（圓心 z＝6.2 cm，拇指食指捏這裡），
    中間是遙控握柄（2.2×2.8 cm），金屬鑰匙齒往下垂；正面（按鈕）朝 -Y"""
    mb = MB("ZP_car_key"); st = clay("steel", rough=0.35); bk = clay("gear")
    mb.add(p_box(0.0085, 0.0028, 0.022, 0.0012), st, M((0, 0, 0.011)))                    # 鑰匙齒
    for z in (0.005, 0.0105, 0.016):
        mb.add(p_box(0.004, 0.0028, 0.0032, 0.0008), st, M((0.0045, 0, z)))
    mb.add(p_box(0.022, 0.0095, 0.028, 0.0045), bk, M((0, 0, 0.0355)))                    # 遙控握柄
    for z, c in ((0.0405, "rose"), (0.0315, "lav_lt")):
        mb.add(p_cyl(0.0045, 0.002, 0.0008, 20), clay(c), M((0, -0.0048, z), (90, 0, 0)))
    mb.add(p_torus(0.0035, 0.0012, 0, 2 * math.pi, 20, 8), st, M((0, 0, 0.0515), (0, 90, 0)))   # 連接小環
    mb.add(p_torus(0.0098, 0.0013, 0, 2 * math.pi, 40, 8), st, M((0, 0, 0.0618), (90, 0, 0)))  # 鑰匙圈（朝鏡頭）
    mb.obj(col)


@item("dslr", "手持單眼相機（攝影師用；ZEPETO 手的大小）", "提案B B4", cat="studio:攝影棚")
def b_dslr(col):
    """機身寬 10.5 cm（真人單眼 14 cm 照 ZEPETO 手長縮）；鏡頭朝 -Y，觀景窗和螢幕在 +Y（攝影師那側）。
    握把在 -X（攝影師的右手），快門在握把頂；左手托鏡頭（鏡頭中心高 3.6 cm、往前伸 2～9 cm）"""
    mb = MB("ZP_dslr"); gr = clay("gear"); dk = clay("grip_dk", "#3A3542"); st = clay("steel", rough=0.45)
    mb.add(p_box(0.105, 0.05, 0.066, 0.012), gr, M((0, 0, 0.033)))
    mb.add(p_box(0.03, 0.062, 0.07, 0.013), dk, M((-0.039, -0.006, 0.035)))              # 握把
    mb.add(p_box(0.046, 0.046, 0.03, 0.012), gr, M((0.004, 0.002, 0.075)))               # 觀景窗那塊凸起
    mb.add(p_box(0.026, 0.014, 0.018, 0.006), dk, M((0.004, 0.03, 0.074)))               # 眼罩
    mb.add(p_cyl(0.029, 0.012, 0.004, 40), st, M((0.006, -0.031, 0.036), (90, 0, 0)))    # 卡口
    mb.add(p_cyl(0.027, 0.055, 0.006, 40), gr, M((0.006, -0.064, 0.036), (90, 0, 0)))    # 鏡頭
    for yy in (-0.055, -0.078):
        mb.add(p_cyl(0.0285, 0.012, 0.003, 40), dk, M((0.006, yy, 0.036), (90, 0, 0)))   # 對焦環、變焦環
    mb.add(p_cyl(0.021, 0.004, 0.0015, 40), clay("lens", rough=0.2), M((0.006, -0.092, 0.036), (90, 0, 0)))
    mb.add(p_cyl(0.011, 0.008, 0.003, 24), dk, M((0.034, 0.004, 0.07)))                  # 轉盤
    mb.add(p_cyl(0.0055, 0.005, 0.002, 16), clay("rose"), M((-0.04, -0.016, 0.072)))     # 快門
    mb.add(p_box(0.062, 0.004, 0.042, 0.004), clay("screen", rough=0.35, emit=0.6), M((0.008, 0.026, 0.031)))   # 背面螢幕
    for sx in (-1, 1):
        mb.add(p_torus(0.005, 0.0015, 0, 2 * math.pi, 16, 6), st, M((sx * 0.054, 0.0, 0.058), (0, 90, 0)))   # 背帶扣
    mb.obj(col)


@item("photo_backdrop", "婚禮拍照背板（花牆＋新人名字 Roger & Amy）", "提案B B5", cat="venue:婚宴會館")
def b_photo_backdrop(col):
    """2.4 m 寬、2.3 m 高的花牆，正面朝 -Y；名牌（白底金色手寫 Roger & Amy）在 1.55～2.05 m，ZEPETO 兩人（1.5 m）站在前面也擋不到。
    背後兩支 L 型腳架往後 0.45 m"""
    rnd = random.Random(23); mb = MB("ZP_photo_backdrop"); wh = clay("white", rough=0.7)
    W, H0, H1 = 2.4, 0.12, 2.3
    mb.add(p_box(W, 0.08, H1 - H0, 0.03), clay("hedge_dk"), M((0, 0.04, (H0 + H1) / 2)))
    for sx in (-1, 1):                                                     # 白色外框＋腳架
        mb.add(p_box(0.08, 0.12, H1 - H0 + 0.08, 0.03), wh, M((sx * (W / 2 + 0.02), 0.04, (H0 + H1) / 2)))
        mb.add(p_box(0.08, 0.08, H0, 0.02), wh, M((sx * (W / 2 - 0.15), 0.04, H0 / 2)))
        mb.add(p_box(0.09, 0.5, 0.06, 0.025), wh, M((sx * (W / 2 - 0.15), 0.22, 0.03)))
    for z in (H0 - 0.02, H1 + 0.02):
        mb.add(p_box(W + 0.12, 0.12, 0.08, 0.03), wh, M((0, 0.04, z)))
    PZ, PW, PH = 1.8, 1.06, 0.5                                            # 名牌中心高、寬、高
    cols_ = ["blush"] * 4 + ["cream"] * 3 + ["ivory"] * 2 + ["rose", "lav_lt", "butter"]
    nx, nz = 22, 20
    for i in range(nx):
        for j in range(nz):
            x = -W / 2 + (i + 0.5) * W / nx + rnd.uniform(-0.02, 0.02); z = H0 + (j + 0.5) * (H1 - H0) / nz + rnd.uniform(-0.02, 0.02)
            if abs(x) < PW / 2 + 0.02 and abs(z - PZ) < PH / 2 + 0.02:
                continue
            r = rnd.uniform(0.052, 0.07)
            mb.add(p_sphere(r, r * 0.7, r, 14), clay(rnd.choice(cols_)), M((x, -0.01, z)))
    for _ in range(26):                                                    # 散在花牆上的大玫瑰
        x = rnd.uniform(-W / 2 + 0.1, W / 2 - 0.1); z = rnd.uniform(H0 + 0.1, H1 - 0.1)
        if abs(x) < PW / 2 + 0.08 and abs(z - PZ) < PH / 2 + 0.08:
            continue
        rose(mb, clay(rnd.choice(["rose", "blush", "ivory"])), (x, -0.06, z), 0.075, rnd, (90, 0, rnd.uniform(-20, 20)))
    for _ in range(40):
        leaf(mb, clay(rnd.choice(["euca", "sage"])), (rnd.uniform(-W / 2 + 0.05, W / 2 - 0.05), -0.05, rnd.uniform(H0 + 0.05, H1 - 0.05)),
             0.09, rnd.uniform(0, 360), 0, 90)
    mb.add(p_box(PW + 0.06, 0.03, PH + 0.06, 0.12), clay("gold", rough=0.4), M((0, -0.085, PZ)))   # 名牌：金邊＋白底
    mb.add(p_box(PW, 0.04, PH, 0.11), wh, M((0, -0.1, PZ)))
    mb.obj(col)
    text_obj(col, "Roger & Amy", 0.15, clay("gold", rough=0.4), (0, -0.124, PZ + 0.02), (90, 0, 0), 0.004, "ZP_backdrop_txt",
             font=r"C:/Windows/Fonts/segoescb.ttf")


# ── 婚宴會館的牆、地板、燈（scenes/venue_*.py 共用）──
# 三個場景共用一個世界座標：角色走在 y＝0 往 +X，鏡頭在 y＝-3（右手側 3 m），牆的正面在 y＝VENUE_WALL_Y。
# 走廊 x -3.0～10.2 → 攝影區 10.2～14.8 → 門框 → 門廳 14.8～19.6（2026-10-13 B3 拉長，攝影區、門廳 +3.3 m）；三個場景一起擺在原點就接成一條連續的會館。
VENUE_WALL_Y = 0.75     # 攝影區、門廳的牆（2026-10-12 從 1.2 改成 0.75）；走廊另用 C_WALL_Y＝1.55（2026-10-13 讓出新娘走線，見 venue_corridor.py）


def venue_wall(col, name, x0, x1, h=3.0, gaps=(), upper="hall_wall", y=VENUE_WALL_Y, t=0.2):
    """朝 -Y 的一面牆：上半牆＋腰板（0～0.9 m，凸起方格）＋扶手線板＋踢腳板＋頂上線板。gaps＝[(門洞左 x, 右 x, 門洞高)…] 留洞，
    洞旁的線板會讓開門框（0.12 m）"""
    mb = MB(name); up = clay(upper, rough=0.9); wn = clay("wainscot", rough=0.8); tr = clay("trim")
    spans, cur, prev_gap = [], x0, False
    for g0, g1, gh in sorted(gaps):
        if g0 > cur:
            spans.append((cur, g0, prev_gap, True))
        mb.add(p_box(g1 - g0, t, h - gh, 0.008), up, M(((g0 + g1) / 2, y + t / 2, (gh + h) / 2)))
        cur, prev_gap = g1, True
    if cur < x1:
        spans.append((cur, x1, prev_gap, False))
    for a, b, ga, gb in spans:
        L, cx = b - a, (a + b) / 2
        mb.add(p_box(L, t, h, 0.008), up, M((cx, y + t / 2, h / 2)))
        a2, b2 = a + (0.14 if ga else 0), b - (0.14 if gb else 0)          # 線板讓開門框
        if b2 - a2 < 0.1:
            continue
        L2, c2 = b2 - a2, (a2 + b2) / 2
        mb.add(p_box(L2, 0.03, 0.9, 0.008), wn, M((c2, y - 0.015, 0.45)))
        n = max(1, int(L2 / 0.9))
        for i in range(n if L2 > 0.5 else 0):
            mb.add(p_box(L2 / n - 0.2, 0.02, 0.5, 0.01), wn, M((a2 + (i + 0.5) * L2 / n, y - 0.04, 0.47)))
        mb.add(p_box(L2, 0.05, 0.05, 0.015), tr, M((c2, y - 0.025, 0.92)))
        mb.add(p_box(L2, 0.04, 0.12, 0.01), tr, M((c2, y - 0.02, 0.06)))
        mb.add(p_box(L, 0.08, 0.1, 0.02), wn, M((cx, y - 0.04, h - 0.05)))
    return mb.obj(col)


def venue_floor(col, name, x0, x1, kind="wood", y0=-3.8, y1=VENUE_WALL_Y + 0.05):
    """地板：wood＝沿 X 的長木條（兩色交錯）；marble＝0.6 m 方格（米白／淡粉交錯）"""
    mb = MB(name)
    if kind == "wood":
        n = int((y1 - y0) / 0.2)
        for i in range(n):
            mb.add(p_box(x1 - x0, (y1 - y0) / n - 0.006, 0.04, 0.006), clay("hall_floor" if i % 2 == 0 else "hall_floor2", rough=0.8),
                   M(((x0 + x1) / 2, y0 + (i + 0.5) * (y1 - y0) / n, -0.02)))
    else:
        nx, ny = max(1, round((x1 - x0) / 0.6)), max(1, round((y1 - y0) / 0.6))
        for i in range(nx):
            for j in range(ny):
                mb.add(p_box((x1 - x0) / nx - 0.008, (y1 - y0) / ny - 0.008, 0.04, 0.008), clay("marble" if (i + j) % 2 == 0 else "marble2", rough=0.55),
                       M((x0 + (i + 0.5) * (x1 - x0) / nx, y0 + (j + 0.5) * (y1 - y0) / ny, -0.02)))
    return mb.obj(col)


def venue_runner(col, name, x0, x1, y=0.1, w=1.6, color="runner"):
    mb = MB(name)
    mb.add(p_box(x1 - x0, w, 0.016, 0.006), clay("runner_bd", rough=0.9), M(((x0 + x1) / 2, y, 0.008)))
    mb.add(p_box(x1 - x0, w - 0.16, 0.02, 0.006), clay(color, rough=0.9), M(((x0 + x1) / 2, y, 0.01)))
    return mb.obj(col)


def venue_sconce(mb, x, z=1.6, y=VENUE_WALL_Y):
    """壁燈：金色底座＋彎臂＋米白燈罩（微發光）"""
    gd = clay("gold", rough=0.4)
    mb.add(p_box(0.1, 0.02, 0.18, 0.03), gd, M((x, y - 0.01, z - 0.08)))
    mb.add(p_tube([(x, y - 0.02, z - 0.1), (x, y - 0.12, z - 0.08), (x, y - 0.15, z)], 0.012, 10), gd)
    mb.add(p_lathe([(0, 0), (0.055, 0), (0.085, 0.13), (0, 0.13)], 32), clay("glow_shade", "#FFF3DF", emit=1.5), M((x, y - 0.15, z)))


def venue_frame(mb, x, z, w, h, art="blush", y=VENUE_WALL_Y):
    """掛畫：金框＋粉嫩色塊（畫的是圓滾滾的花）"""
    mb.add(p_box(w, 0.04, h, 0.02), clay("gold", rough=0.4), M((x, y - 0.02, z)))
    mb.add(p_box(w - 0.1, 0.03, h - 0.1, 0.01), clay("ivory"), M((x, y - 0.035, z)))
    for k, (dx, dz, r, c) in enumerate(((0, 0.02, 0.09, art), (-0.09, -0.06, 0.06, "lav_lt"), (0.09, -0.07, 0.055, "butter"))):
        mb.add(p_sphere(r * w / 0.6, 0.012, r * w / 0.6, 20), clay(c), M((x + dx * w / 0.6, y - 0.052, z + dz * h / 0.75)))


def venue_lights(x0, x1, y=-0.3, z=3.1, energy=150):
    """室內：天花板一排柔光＋鏡頭那側一大片補光（夜景模式時才打，見 render_plugin）"""
    n = max(1, round((x1 - x0) / 3.0)); out = []
    for i in range(n):
        out.append(light("AREA", "ZP_VenueCeil", (x0 + (i + 0.5) * (x1 - x0) / n, y, z), (0, 0, 0), energy, "#FFF4E8", size=2.6))
    out.append(light("AREA", "ZP_VenueFill", ((x0 + x1) / 2, -7.0, 2.0), (80, 0, 0), 18 * (x1 - x0), "#F3F0FF", size=8.0))
    return out


def posed_copy(col, src, offset, rots):
    """把道具集合 src 的物件複製一份（共用網格）擺到 offset，名稱含 rots 的 key 的物件轉 rz 度（開門示意用）；預設不算圖，回傳物件清單"""
    out, made = [], {}
    for o in sorted(src.objects, key=lambda o: o.parent is not None):
        c = bpy.data.objects.new(o.name + "_posed", o.data)
        if o.parent is not None and o.parent.name in made:
            c.parent = made[o.parent.name]; c.location = o.location; c.rotation_euler = o.rotation_euler
        else:
            c.location = Vector(o.location) + Vector(offset)
            rz = next((v for k, v in rots.items() if k in o.name), 0.0)
            c.rotation_euler = (0, 0, math.radians(rz))
        c.hide_render = True; c.hide_viewport = True; col.objects.link(c); made[o.name] = c; out.append(c)   # 視窗也藏：擺場景時不會看到重疊的門
    return out


def venue_context(col, x0, x1, kind="wood", upper="hall_wall", y=VENUE_WALL_Y):
    """示意圖用：隔壁場景的簡化牆與地板（場景外掛的 context 呼叫，不進素材庫）；y＝那段牆的位置（走廊是 C_WALL_Y）"""
    venue_floor(col, "ZP_ctx_floor", x0, x1, kind, y1=y + 0.05)
    venue_wall(col, "ZP_ctx_wall", x0, x1, 2.8, upper=upper, y=y)


def scale_figure(col, loc, rz=0.0, name="ZP_ScaleFig"):
    """ZEPETO 角色比例的灰色人形（身高 1.50 m、骨盆 0.64 m、大頭）：只出現在場景示意圖，不屬於場景"""
    mb = MB(name); g = clay("scalefig", "#B9B2C6", rough=0.8)
    for sx in (-1, 1):
        mb.add(p_cyl(0.07, 0.62, 0.03, 16, rad2=0.06), g, M((sx * 0.075, 0, 0.31)))
        mb.add(p_tube([(sx * 0.17, 0, 1.06), (sx * 0.23, 0, 0.62)], 0.045, 10), g)
    mb.add(p_sphere(0.18, 0.13, 0.3, 24), g, M((0, 0, 0.86)))
    mb.add(p_sphere(0.19, 0.18, 0.18, 24), g, M((0, 0, 1.32)))
    ob = mb.obj(col, loc); ob.rotation_euler = (0, 0, math.radians(rz))
    return ob


# ───────────────────────── 場景、燈光、算圖 ─────────────────────────
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    try:
        sc.render.engine = "BLENDER_EEVEE"
    except TypeError:
        sc.render.engine = "BLENDER_EEVEE_NEXT"
    try:
        sc.eevee.taa_render_samples = SAMPLES
        sc.eevee.use_raytracing = True
        sc.eevee.use_shadows = True
    except Exception as e:
        print("EEVEE_OPT", e)
    sc.view_settings.view_transform = "AgX"
    looks = [i.identifier for i in sc.view_settings.bl_rna.properties["look"].enum_items] if False else None
    for lk in ("AgX - Medium High Contrast", "Medium High Contrast"):
        try:
            sc.view_settings.look = lk; break
        except TypeError:
            pass
    sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 90
    return sc


def world(color, strength):
    w = bpy.data.worlds.new("ZP_World"); w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = hexc(color); bg.inputs[1].default_value = strength
    bpy.context.scene.world = w


def light(kind, name, loc, rot, energy, color="#FFF8F0", size=None, angle=None):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = hexc(color)[:3]
    if angle is not None:
        ld.angle = math.radians(angle)
    if size is not None:
        if kind == "AREA":
            ld.size = size
        else:
            ld.shadow_soft_size = size
    ob = bpy.data.objects.new(name, ld); ob.location = loc; ob.rotation_euler = [math.radians(a) for a in rot]
    bpy.context.scene.collection.objects.link(ob)
    return ob


def day_lights():
    world("#F3EEF6", 0.55)
    light("SUN", "ZP_Sun", (0, 0, 10), (48, 0, -32), 3.6, "#FFF6EC", angle=22)
    light("SUN", "ZP_Rim", (0, 0, 10), (-55, 0, 150), 0.9, "#E8E4FF", angle=30)


def cyclorama(col):
    """無縫背景：地板往後彎成牆（單位尺寸，之後依道具大小縮放）"""
    bm = bmesh.new(); prof = []
    for i in range(12):
        prof.append((-12 + i * 1.2, 0.0))
    for i in range(13):
        a = math.radians(90 * i / 12); prof.append((1.5 + 2.5 * math.sin(a), 2.5 * (1 - math.cos(a))))
    prof.append((4.0, 12.0))
    rows = [[bm.verts.new((x, y, z)) for x in (-14, -7, 0, 7, 14)] for (y, z) in prof]
    for A, B in zip(rows, rows[1:]):
        for k in range(4):
            f = bm.faces.new((A[k], A[k + 1], B[k + 1], B[k])); f.smooth = True
    me = bpy.data.meshes.new("ZP_Cyc"); bm.to_mesh(me); bm.free()
    me.materials.append(clay("cyc", "#E6DCEB", rough=0.9, sss=0.0))
    ob = bpy.data.objects.new("ZP_Cyc", me); col.objects.link(ob)
    return ob


def coll_bbox(cols):
    bpy.context.view_layer.update()
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for c in cols:
        for o in c.all_objects:
            if o.type not in ("MESH", "FONT"):
                continue
            for p in o.bound_box:
                w = o.matrix_world @ Vector(p)
                lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    return lo, hi


def camera(name, loc, target, lens=50.0):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    ob = bpy.data.objects.new(name, cd); bpy.context.scene.collection.objects.link(ob)
    ob.location = loc; ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = ob
    return ob


def frame_bbox(lo, hi, az=-30.0, el=18.0, lens=50.0, margin=1.12, aspect=1.0):
    c = (lo + hi) / 2; R = (hi - lo).length / 2
    fov = 2 * math.atan(18.0 / lens) * min(1.0, aspect)
    d = R / math.sin(fov / 2) * margin
    a, e = math.radians(az), math.radians(el)
    v = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    return c + v * d, c, R


def render(path, res):
    sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.render.filepath = path; os.makedirs(os.path.dirname(path), exist_ok=True)
    t = time.time(); bpy.ops.render.render(write_still=True)
    print("RENDERED", path, round(time.time() - t, 1), flush=True)


def show_only(vl, keep):
    for lc in vl.layer_collection.children:
        lc.exclude = lc.name not in keep


def instance(col_parent, src, loc, rz=0.0, scale=1.0):
    ob = bpy.data.objects.new("I_" + src.name, None); ob.instance_type = "COLLECTION"; ob.instance_collection = src
    ob.location = loc; ob.rotation_euler = (0, 0, math.radians(rz)); ob.scale = (scale,) * 3
    col_parent.objects.link(ob)
    return ob


def main():
    if (ONLY or ONLY_SCENE) and "OUT" not in ARGS:
        raise SystemExit("ONLY=／SCENE= 試做時要給 OUT=（別覆寫素材庫）")
    if ONLY_SCENE:
        if ONLY_SCENE not in PLUGINS:
            raise SystemExit("沒有場景外掛 scenes/%s.py；有的：%s" % (ONLY_SCENE, list(PLUGINS)))
        ONLY[:] = [k for k in PLUGINS[ONLY_SCENE]["props"] if k in ITEMS]
    sc = reset(); vl = bpy.context.view_layer
    keys = ONLY or list(ITEMS)
    cols = {}
    for k in ITEMS:
        if ONLY and k not in ONLY:
            continue
        c = bpy.data.collections.new("ZP_" + k); sc.collection.children.link(c)
        t = time.time(); ITEMS[k][2](c); cols[k] = c
        print("BUILT", k, len(c.all_objects), round(time.time() - t, 2), flush=True)
    stage = bpy.data.collections.new("ZP_Stage"); sc.collection.children.link(stage)
    cyc = cyclorama(stage)
    day_lights()
    manifest = []
    # ── 單品：3/4 視角 ──
    for k in keys:
        if k not in cols:
            continue
        show_only(vl, {"ZP_" + k, "ZP_Stage"})
        lo, hi = coll_bbox([cols[k]])
        az = -32.0; el = 42.0 if (hi - lo).z < 0.12 * max((hi - lo).x, (hi - lo).y) or k == "petals" else 20.0   # 扁平的東西從高一點拍
        loc, tgt, R = frame_bbox(lo, hi, az=az, el=el)
        cyc.scale = (max(R, 0.15),) * 3; cyc.location = (0, (lo.y + hi.y) / 2 + R * 0.6, 0)
        cam = camera("ZP_Cam_" + k, loc, tgt)
        manifest.append(dict(key=k, label=ITEMS[k][0], scenes=ITEMS[k][1], size=[round(x, 3) for x in (hi - lo)], img="previews/items/%s.jpg" % k, collection="ZP_" + k, catalog=cat_of(k), **({"source": EXT_SRC[k]} if k in EXT_SRC else {})))
        if not NORENDER:
            render(os.path.join(OUT, "previews", "items", k + ".jpg"), (900, 900))
    # ── 場景示意 ──
    if not ONLY:
        build_scenes(sc, vl, cols, cyc, manifest)
    for key, S in PLUGINS.items():
        if (ONLY_SCENE and key != ONLY_SCENE) or (ONLY and not ONLY_SCENE):
            continue
        render_plugin(S, sc, vl, cols, manifest)
    show_only(vl, set(c.name for c in sc.collection.children))
    mark_assets(cols, manifest)
    os.makedirs(OUT, exist_ok=True)
    json.dump(dict(built=time.strftime("%Y-%m-%d"), blend="zepeto_props.blend", catalogs={k: v[1] for k, v in CATALOGS.items()}, items=manifest), open(os.path.join(OUT, "catalog.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "zepeto_props.blend"))
    print("ZP_DONE", round(time.time() - T0, 1), flush=True)


# ───────────────────────── 資產標記（Asset Browser）─────────────────────────
CAT_OF = {**{k: "garden" for k in ("arch", "hedge", "tree", "ground", "flowerbed", "petals", "oldcam", "bouquet", "phone")},
          **{k: "carpet" for k in ("carpet", "roll")},
          **{k: "dinner" for k in ("table", "chair", "chicken", "soup", "salad", "bottle", "wineglass", "fork", "dessert", "fruit")},
          **{k: "street" for k in ("taxi", "facade", "lamp", "planter", "street")}}


def mark_assets(cols, manifest):
    """每個道具集合、場景示意集合標成資產：分類、說明、標籤、預覽圖（用算好的 jpg）；分類檔 blender_assets.cats.txt 和 .blend 放一起"""
    ids = {k: str(uuid.uuid5(uuid.NAMESPACE_URL, "zepeto-props/" + k)) for k in CATALOGS}   # 固定 UUID：重建後分類不會變
    lines = ["# Blender 資產分類（build_props.py 產生，別手改）", "VERSION 1", ""]
    lines += ["%s:%s:%s" % (ids[k], path, simple) for k, (path, simple) in CATALOGS.items()]
    open(os.path.join(OUT, "blender_assets.cats.txt"), "w", encoding="utf8").write("\n".join(lines) + "\n")
    for m in manifest:
        c = bpy.data.collections.get(m["collection"])
        if c is None:
            continue
        c.asset_mark()
        ad = c.asset_data; ad.catalog_id = ids.get(m["catalog"] or "scenes"); ad.description = m["label"] + "（用在 " + m["scenes"] + "）"
        for t in ("ZEPETO", "黏土風") + (("V12",) if any(ch in m["scenes"] for ch in "②③⑤⑦⑧") else ()):
            ad.tags.new(t, skip_if_exists=True)
        jpg = os.path.join(OUT, m["img"])
        if os.path.exists(jpg):
            try:
                with bpy.context.temp_override(id=c):
                    bpy.ops.ed.lib_id_load_custom_preview(filepath=jpg)
            except Exception as e:
                print("PREVIEW_FAIL", m["key"], e, flush=True)


def build_scenes(sc, vl, cols, cyc, manifest):
    rnd = random.Random(99)
    sc.world = None; world("#A9CFF0", 0.75)                            # 場景示意用淡藍天空
    # A. 花園拱門（②⑤⑧ 的視角）
    A = bpy.data.collections.new("ZP_Scene_Garden"); sc.collection.children.link(A)
    big = MB("ZP_bigground"); big.add(p_cyl(14, 0.1, 0.04, 96), clay("grass"), M((0, 0, -0.05))); big.add(p_box(1.1, 14, 0.03, 0.012), clay("sand"), M((0, -6.7, 0.012))); big.obj(A)
    instance(A, cols["arch"], (0, 0.3, 0))
    for sd in (-1, 1):
        for i in range(3):
            instance(A, cols["hedge"], (sd * (2.65 + i * 3.0), 0.3, 0))
            instance(A, cols["flowerbed"], (sd * (2.2 + i * 1.85), -0.35, 0))
    for i in range(14):
        x = rnd.choice([-1, 1]) * rnd.uniform(2.3, 9); y = rnd.uniform(2.5, 9)
        t = instance(A, cols["tree"], (x, y, 0), rnd.uniform(0, 360), rnd.uniform(0.9, 1.4))
    for i in range(7):
        instance(A, cols["petals"], (rnd.uniform(-1.5, 1.5), rnd.uniform(-1.5, 0), rnd.uniform(0.6, 2.2)), rnd.uniform(0, 360), 1.2)
    instance(A, cols["oldcam"], (-2.0, -2.6, 0), -25)
    instance(A, cols["bouquet"], (0.45, -0.2, 0.0), 0, 1.0)
    show_only(vl, {"ZP_Scene_Garden"})
    camera("ZP_Cam_Garden", (0.6, -7.2, 1.6), (-0.2, 0.3, 1.25), 32)
    if not NORENDER:
        render(os.path.join(OUT, "previews", "scenes", "garden.jpg"), (1600, 900))
    manifest.append(dict(key="scene_garden", label="場景示意：花園拱門（②⑤⑧）", scenes="②⑤⑧", img="previews/scenes/garden.jpg", collection="ZP_Scene_Garden", catalog="scenes", group="garden"))
    # B. ③ 紅毯（側面平視）：同一個花園，紅毯沿 X 鋪向拱門
    B = bpy.data.collections.new("ZP_Scene_Carpet"); sc.collection.children.link(B)
    instance(B, cols["carpet"], (-2.6, -0.9, 0.0), -90)
    instance(B, cols["roll"], (-0.35, -0.9, 0.0), -90)
    show_only(vl, {"ZP_Scene_Garden", "ZP_Scene_Carpet"})
    for o in A.objects:                                              # ③ 不放老相機、捧花
        if o.name.startswith("I_ZP_oldcam") or o.name.startswith("I_ZP_bouquet"):
            o.hide_render = True
    camera("ZP_Cam_Carpet", (-2.4, -7.6, 1.5), (-1.6, -0.4, 0.9), 32)
    if not NORENDER:
        render(os.path.join(OUT, "previews", "scenes", "carpet.jpg"), (1600, 900))
    manifest.append(dict(key="scene_carpet", label="場景示意：③ 推紅毯", scenes="③", img="previews/scenes/carpet.jpg", collection="ZP_Scene_Carpet", catalog="scenes", group="carpet"))
    for o in A.objects:
        o.hide_render = False
    # C. ⑦a 晚餐桌
    C = bpy.data.collections.new("ZP_Scene_Dinner"); sc.collection.children.link(C)
    g = MB("ZP_dinner_ground"); g.add(p_cyl(4.5, 0.1, 0.04, 72), clay("grass"), M((0, 0, -0.05))); g.obj(C)
    instance(C, cols["hedge"], (0, 1.5, 0)); instance(C, cols["hedge"], (-3.0, 1.5, 0)); instance(C, cols["hedge"], (3.0, 1.5, 0))
    instance(C, cols["table"], (0, 0, 0)); instance(C, cols["chair"], (0, 0.62, 0))
    T = 0.75
    for k, (x, y, rz) in dict(chicken=(0.0, 0.02, 0), soup=(-0.25, -0.17, 0), salad=(0.24, -0.1, 0), dessert=(-0.2, 0.2, 0), fruit=(0.22, 0.22, 0),
                              bottle=(-0.34, 0.04, 0), wineglass=(0.33, -0.25, 0), fork=(0.08, -0.3, 75)).items():
        instance(C, cols[k], (x, y, T), rz)
    instance(C, cols["flowerbed"], (-1.7, 1.0, 0)); instance(C, cols["flowerbed"], (1.7, 1.0, 0))
    show_only(vl, {"ZP_Scene_Dinner"})
    camera("ZP_Cam_Dinner", (0.15, -2.5, 1.75), (0.0, 0.05, 0.8), 40)
    if not NORENDER:
        render(os.path.join(OUT, "previews", "scenes", "dinner.jpg"), (1600, 900))
    manifest.append(dict(key="scene_dinner", label="場景示意：⑦a 晚餐桌", scenes="⑦a", img="previews/scenes/dinner.jpg", collection="ZP_Scene_Dinner", catalog="scenes", group="dinner"))
    # D. ⑦b 夜晚街景
    D = bpy.data.collections.new("ZP_Scene_Street"); sc.collection.children.link(D)
    for i in range(-1, 2):
        instance(D, cols["street"], (i * 3.0, 0, 0))
    instance(D, cols["facade"], (0, 1.55, 0)); instance(D, cols["facade"], (3.2, 1.55, 0)); instance(D, cols["facade"], (-3.2, 1.55, 0))
    instance(D, cols["lamp"], (1.7, 0.45, 0), 90 + 180); instance(D, cols["lamp"], (-2.3, 0.45, 0), 90 + 180)
    instance(D, cols["planter"], (-0.95, 1.15, 0)); instance(D, cols["planter"], (0.95, 1.15, 0), 180)
    instance(D, cols["taxi"], (-0.4, -0.75, 0), 0)
    show_only(vl, {"ZP_Scene_Street"})
    for o in bpy.data.objects:
        if o.type == "LIGHT":
            o.hide_render = True
    sc.world = None; world("#1E2748", 0.35)
    night = [light("SUN", "ZP_Moon", (0, 0, 10), (50, 0, 30), 0.35, "#AFC2FF", angle=10)]
    for x in (1.2, -2.8):
        night.append(light("POINT", "ZP_LampPt", (x, 0.45, 2.9), (0, 0, 0), 120, "#FFD39A", size=0.2))
    for x in (-1.0, 0, 1.0, 2.2, -2.2):
        night.append(light("AREA", "ZP_Window", (x, 1.0, 1.4), (90, 0, 0), 15, "#FFC98A", size=0.9))
    night.append(light("AREA", "ZP_Fill", (-1.5, -4, 3), (60, 0, -20), 60, "#9FB3FF", size=4))
    camera("ZP_Cam_Street", (-3.6, -5.2, 1.9), (-0.2, 0.2, 0.95), 32)
    if not NORENDER:
        render(os.path.join(OUT, "previews", "scenes", "street.jpg"), (1600, 900))
    manifest.append(dict(key="scene_street", label="場景示意：⑦b 夜晚餐廳門口", scenes="⑦b", img="previews/scenes/street.jpg", collection="ZP_Scene_Street", catalog="scenes", group="street"))
    for o in night:
        o.hide_render = True
    for o in bpy.data.objects:
        if o.type == "LIGHT" and o not in night:
            o.hide_render = False


# ───────────────────────── 外部素材：匯入 → 黏土化 ─────────────────────────
EXT_SRC = {}   # 代號 → 來源（site、page、author、license、file），寫進 catalog.json；CC BY 的另外登記在 ATTRIBUTION.md


def _srgb(c):
    return tuple(12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055 for x in c[:3])


def _lin(c):
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c[:3])


def _mat_color(m):
    """原材質的代表色（線性）：有貼圖取貼圖平均色，否則取 Base Color"""
    if m is None or not m.use_nodes:
        return tuple(m.diffuse_color[:3]) if m else (0.8, 0.8, 0.8)
    for n in m.node_tree.nodes:
        if n.type == "TEX_IMAGE" and n.image is not None and n.image.size[0] > 0:
            px = n.image.pixels[:]; ch = n.image.channels; step = max(1, len(px) // ch // 4000) * ch
            acc = [0.0, 0.0, 0.0]; cnt = 0
            for i in range(0, len(px) - ch + 1, step):
                if ch < 4 or px[i + 3] > 0.5:
                    acc[0] += px[i]; acc[1] += px[i + 1]; acc[2] += px[i + 2]; cnt += 1
            if cnt:
                avg = tuple(a / cnt for a in acc)
                return avg if n.image.colorspace_settings.name.lower().startswith(("linear", "non")) else _lin(avg)
    b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    return tuple(b.inputs["Base Color"].default_value[:3]) if b else tuple(m.diffuse_color[:3])


def _pastel(lin, sat=0.65, light=0.2):
    import colorsys
    h, s_, v = colorsys.rgb_to_hsv(*_srgb(lin))
    r, g, b = colorsys.hsv_to_rgb(h, s_ * sat, v + (1 - v) * light)
    return "#%02X%02X%02X" % tuple(int(max(0, min(1, x)) * 255 + 0.5) for x in (r, g, b))


def import_external(col, path, key, size=None, fit="max", rz=0.0, colors=None, bevel=0.04, sat=0.65, light=0.2, keep=None):
    """匯入 glb／gltf／obj／fbx → 只留網格、烘進世界座標、合成一個物件 → 轉 rz 讓正面朝 -Y → 縮放（fit：max／height／width）
    → 原點移到底部中心 → 每個原材質換成粉嫩化的黏土色（colors={'材質名片段': 色票名或 #hex} 可指定）→ 倒圓（Bevel，角度限制）"""
    ext = os.path.splitext(path)[1].lower(); before = set(bpy.data.objects)
    if ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=path)
    elif ext == ".obj":
        bpy.ops.wm.obj_import(filepath=path)
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=path)
    else:
        raise ValueError("不支援的格式 " + ext + "（先轉成 glb）")
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH" and (keep is None or any(k in o.name for k in keep))]
    mb = MB("ZP_" + key); R = Matrix.Rotation(math.radians(rz), 4, "Z")
    for o in meshes:
        me = o.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh() if o.modifiers else o.data
        bm = bmesh.new(); bm.from_mesh(me); bm.transform(R @ o.matrix_world)
        mats = []
        for i, slot in enumerate(o.material_slots or [None]):
            m = slot.material if slot else None
            pick = next((v for k_, v in (colors or {}).items() if m is not None and k_.lower() in m.name.lower()), None)
            hexv = (PAL.get(pick, pick) if pick else _pastel(_mat_color(m), sat, light))
            mats.append(clay("ext_%s_%d_%s" % (key, i, hexv.lstrip("#")), hexv))
        for f in bm.faces:
            f.smooth = True
        mb.add_mesh(bm, mats)
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    bmesh.ops.remove_doubles(mb.bm, verts=list(mb.bm.verts), dist=1e-5)
    # glTF 會把面切成三角形：同一平面的三角形先合回整面，倒圓的寬度才不會被細長三角形夾到幾乎為零
    bmesh.ops.dissolve_limit(mb.bm, angle_limit=math.radians(1.0), verts=list(mb.bm.verts), edges=list(mb.bm.edges), delimit={"MATERIAL"})
    lo = Vector([min(v.co[i] for v in mb.bm.verts) for i in range(3)]); hi = Vector([max(v.co[i] for v in mb.bm.verts) for i in range(3)])
    dim = hi - lo; ref = {"max": max(dim), "height": dim.z, "width": dim.x}[fit]
    k = (size / ref) if (size and ref > 0) else 1.0
    base = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    for v in mb.bm.verts:
        v.co = (v.co - base) * k
    ob = mb.obj(col)
    if bevel > 0:
        bv = ob.modifiers.new("ZP_Round", "BEVEL"); bv.width = bevel * max(dim) * k; bv.segments = 4; bv.profile = 0.5
        bv.limit_method = "ANGLE"; bv.angle_limit = math.radians(30); bv.harden_normals = True
    return ob


def ext_item(key, label, scenes, file, cat=None, source=None, **kw):
    """登記一個外部素材道具：file 相對於 external/<代號>/source/；檔案不在（例如剛 clone、source/ 不進版控）就跳過並提醒"""
    path = os.path.join(globals().get("EXT_ROOT", HERE), "external", key, "source", file)
    if not os.path.exists(path):
        print("EXT_MISSING", key, path, "（重新下載：見 catalog／ATTRIBUTION 的來源網址）", flush=True)
        return
    EXT_SRC[key] = dict(source or {}, file=file)
    item(key, label, scenes, cat)(lambda col: import_external(col, path, key, **kw))


# ───────────────────────── 場景外掛（scenes/<key>.py）─────────────────────────
PLUGINS = {}
ONLY_SCENE = ARGS.get("SCENE", "")


def render_plugin(S, sc, vl, cols, manifest):
    """S＝場景外掛的 SCENE：build(col, cols) 擺景（instance(col, cols[代號], 位置, rz, 縮放)）；night=True 時關掉白天燈、
    換夜空（sky）、呼叫 lights() 自己打燈；camera＝(位置, 看的點, 焦距)"""
    key = S["key"]; col = bpy.data.collections.new("ZP_Scene_" + key.title().replace("_", "")); sc.collection.children.link(col)
    missing = [p for p in S.get("props", []) if p not in cols]
    if missing:
        print("SCENE_MISSING_PROPS", key, missing, flush=True)
    S["build"](col, cols)
    figs = None
    if S.get("figures") or S.get("context"):                               # 只出現在示意圖、算完就刪：灰色比例人形、隔壁場景的牆與地板
        figs = bpy.data.collections.new("ZP_PreviewOnly"); sc.collection.children.link(figs)
        for f in S.get("figures") or []:
            scale_figure(figs, (f[0], f[1], 0.0), f[2] if len(f) > 2 else 0.0)
        if S.get("context"):
            S["context"](figs)
    show_only(vl, {col.name} | ({figs.name} if figs else set()))
    day = [o for o in bpy.data.objects if o.type == "LIGHT" and not o.hide_render]
    if S.get("night"):
        for o in day:
            o.hide_render = True
    world(S.get("sky", "#1E2748" if S.get("night") else "#A9CFF0"), S.get("sky_strength", 0.35 if S.get("night") else 0.75))
    extra = list(S["lights"]() or []) if S.get("lights") else []
    loc, tgt, lens = S["camera"]
    camera("ZP_Cam_Scene_" + key, loc, tgt, lens)
    img = "previews/scenes/%s.jpg" % key
    if not NORENDER:
        render(os.path.join(OUT, img), tuple(S.get("res", (1600, 900))))
    grp = add_catalog(S["group"]) if S.get("group") else "scenes"
    manifest.append(dict(key="scene_" + key, label=S["label"], scenes=S.get("scenes", ""), img=img, collection=col.name, catalog="scenes", group=grp))
    for v in S.get("views") or []:                                          # 額外視角：(後綴, 說明, (位置, 看的點, 焦距)[, pose(開/關)])
        suf, lab, (vloc, vtgt, vlens) = v[0], v[1], v[2]
        if len(v) > 3:
            v[3](True)
        camera("ZP_Cam_Scene_%s_%s" % (key, suf), vloc, vtgt, vlens)
        vimg = "previews/scenes/%s__%s.jpg" % (key, suf)
        if not NORENDER:
            render(os.path.join(OUT, vimg), tuple(S.get("res", (1600, 900))))
        if len(v) > 3:
            v[3](False)
        manifest.append(dict(key="scene_%s__%s" % (key, suf), label=lab, scenes=S.get("scenes", ""), img=vimg, collection="", catalog="scenes", group=grp, view_of="scene_" + key))
    for o in extra:
        o.hide_render = True
    for o in day:
        o.hide_render = False
    if figs:
        for o in list(figs.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(figs)


def _load_plugins():
    """讀 external_items.py 與 scenes/*.py（底線開頭的是範本，不讀）；EXTRA_DIR=<資料夾> 另外讀那裡的同名檔（試做、測試用，不進素材庫）"""
    for root in [HERE] + ([ARGS["EXTRA_DIR"]] if ARGS.get("EXTRA_DIR") else []):
        p = os.path.join(root, "external_items.py")
        if os.path.exists(p):
            g = globals(); g["EXT_ROOT"] = root
            exec(compile(open(p, encoding="utf8").read(), p, "exec"), g)
        sd = os.path.join(root, "scenes")
        for f in sorted(os.listdir(sd)) if os.path.isdir(sd) else []:
            if f.endswith(".py") and not f.startswith("_"):
                g = globals(); g.pop("SCENE", None)
                exec(compile(open(os.path.join(sd, f), encoding="utf8").read(), os.path.join(sd, f), "exec"), g)
                if "SCENE" in g:
                    S_ = g.pop("SCENE"); PLUGINS[S_["key"]] = S_
    globals()["EXT_ROOT"] = HERE


_load_plugins()
main()
