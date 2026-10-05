# 服裝產生器：讀規格（PROJ/costume.json，格式見 references/costume-spec.md），依元件組出整套服裝。
# use("outfit_lib", "costume") 之後：build_costume() 建全部、wear("costume"|"base") 換裝。
# 預設庫：LIB/costumes/pink-ballgown.json（新娘照片款粉色蓬裙）。所有座標都是新娘座標，乘 S_BODY 換算。
# 規格做不到的部位（西裝、褲子…），在 PROJ/scripts/ 寫 costume_extra_*.py 定義 build_extra(M, spec)，規格的 extra_scripts 列出即可。
# 預設規格自帶的元件放 LIB/costumes/（例：costume_extra_pink_ballgown.py）；use() 先找 PROJ/scripts/，同名時以專案的為準。
import bpy, bmesh, math, json, os
from mathutils import Vector, Matrix

O = bpy.data.objects
A = O[f"{WHO}_Armature"]
S = S_BODY
P = f"{WHO}_Cos_"                       # 服裝物件名稱前綴


def load_spec(path=None):
    path = path or os.path.join(PROJ, MANIFEST.get("costume", {}).get("spec", "costume.json"))
    if not os.path.exists(path):
        path = os.path.join(LIB, "costumes", "pink-ballgown.json")
    return json.load(open(path, encoding="utf8"))


def _c(spec, key, default):
    return tuple(spec.get("colors", {}).get(key, default))


def mats(spec):
    c = lambda k, d: _c(spec, k, d)
    return dict(
        main=mtoon(P + "MainMat", c("main", (0.90, 0.54, 0.56)), c("main_shade", (0.74, 0.38, 0.46))),
        organza=mtoon(P + "OrganzaMat", c("organza", (0.93, 0.60, 0.61)), c("organza_shade", (0.78, 0.44, 0.50)), alpha=spec.get("organza_alpha", 0.9)),
        lining=mtoon(P + "LiningMat", c("lining", (0.86, 0.47, 0.50)), c("lining_shade", (0.70, 0.34, 0.42))),
        tulle=mtoon(P + "TulleMat", c("tulle", (0.93, 0.60, 0.63)), c("tulle_shade", (0.80, 0.48, 0.55)), alpha=spec.get("tulle_alpha", 0.38)),
        sash=mtoon(P + "SashMat", c("sash", (0.92, 0.57, 0.59)), c("sash_shade", (0.76, 0.40, 0.48))),
        bow=mtoon(P + "HairBowMat", c("hair_bow", (0.95, 0.66, 0.68)), c("hair_bow_shade", (0.80, 0.50, 0.56)), alpha=0.8),
        metal=mtoon(P + "MetalMat", c("metal", (0.93, 0.93, 0.95)), c("metal_shade", (0.62, 0.62, 0.70))),
    )


def sv(x, y, z):
    return Vector((x * S, y * S, z * S))


def _new_obj(name, bm, mat, smooth=True):
    name = P + name
    if name in O:
        bpy.data.objects.remove(O[name], do_unlink=True)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me); A.users_collection[0].objects.link(ob)
    me.materials.append(mat)
    return ob


def _weights(ob, groups):
    """groups: [(bone, fn(co)->weight)]"""
    vgs = {b: (ob.vertex_groups.get(b) or ob.vertex_groups.new(name=b)) for b, _ in groups}
    for v in ob.data.vertices:
        for b, fn in groups:
            w = fn(v.co)
            if w > 0:
                vgs[b].add([v.index], w, "REPLACE")
    ob.parent = A
    if not any(m.type == "ARMATURE" for m in ob.modifiers):
        ob.modifiers.new("Armature", "ARMATURE").object = A


def transfer_weights(ob, src):
    for vg in src.vertex_groups:
        if vg.name not in ob.vertex_groups:
            ob.vertex_groups.new(name=vg.name)
    dw = ob.modifiers.new("W", "DATA_TRANSFER"); dw.object = src
    dw.use_vert_data = True; dw.data_types_verts = {"VGROUP_WEIGHTS"}; dw.vert_mapping = "POLYINTERP_NEAREST"
    dw.layers_vgroup_select_src = "ALL"; dw.layers_vgroup_select_dst = "NAME"
    with bpy.context.temp_override(object=ob, active_object=ob):
        bpy.ops.object.modifier_move_to_index(modifier=dw.name, index=0)
        bpy.ops.object.modifier_apply(modifier=dw.name)
    ob.parent = A
    if not any(m.type == "ARMATURE" for m in ob.modifiers):
        ob.modifiers.new("Armature", "ARMATURE").object = A


def _body_parts():
    return [O[n] for n in (f"{WHO}_Body", f"{WHO}_BodyFill") if n in O]


# ── 馬甲（從身體表面撐開） ──
def bodice(M, c):
    z0, z1 = c.get("bottom_z", 0.955), c.get("top_z", 1.232)
    keep = lambda co: z0 * S < co.z < (z1 + 0.04) * S and abs(co.x) < 0.17 * S
    parts = [shell_piece(src, f"TMP_{WHO}_b{i}", keep, (c.get("offset", 0.006) + 0.0005 * i) * S, M["main"]) for i, src in enumerate(_body_parts())]
    ob = join(parts, P + "Bodice") if len(parts) > 1 else parts[0]
    ob.name = P + "Bodice"
    clean_cut(ob, [((0, 0, z1 * S), (0, c.get("top_slant", 0.28), 1)), ((0, 0, (z0 + 0.01) * S), (0, 0, -1))])
    thicken(ob, 0.003 * S)
    return ob


def _top_edge(ob, n=120, zmin=1.12):
    me = ob.data; ec = {}
    for p in me.polygons:
        for e in p.edge_keys:
            ec[e] = ec.get(e, 0) + 1
    vs = {i for e, k in ec.items() if k == 1 for i in e}
    pts = [me.vertices[i].co.copy() for i in vs if me.vertices[i].co.z > zmin * S]
    cy = sum(p.y for p in pts) / len(pts)
    out = []
    for k in range(n):
        a = 2 * math.pi * k / n
        d = Vector((math.cos(a), math.sin(a), 0))
        best = max(pts, key=lambda p: Vector((p.x, p.y - cy, 0)).normalized().dot(d))
        out.append((a, best, Vector((best.x, best.y - cy, 0)).normalized()))
    return out


# ── 胸口立體褶邊：幾層波浪布沿馬甲上緣往上、往外翻 ──
def ruffle(M, c, bod):
    edge = _top_edge(bod)
    bm = bmesh.new(); n = len(edge)
    layers = c.get("layers", [[0.045, 0.014, 0.012, 9, 0.0], [0.06, 0.024, 0.02, 6, 0.9], [0.06, 0.03, 0.022, 4, 2.1]])
    for layer, (h, out, amp, waves, ph) in enumerate(layers):
        h, out, amp = h * S, out * S, amp * S
        rows = []
        for j in range(7):
            t = j / 6
            row = []
            for a, p, nrm in edge:
                fr = max(0.0, -math.sin(a))
                front = (0.45 + 0.55 * fr) * (1.0 if layer < len(layers) - 1 or len(layers) < 3 else fr ** 2)
                w = amp * math.sin(waves * a + ph) * t
                row.append(bm.verts.new(p + nrm * (out * t * t + w + 0.002 * S * layer) + Vector((0, 0, h * front * t - 0.004 * S))))
            rows.append(row)
        for r0, r1 in zip(rows, rows[1:]):
            for k in range(n):
                bm.faces.new((r0[k], r0[(k + 1) % n], r1[(k + 1) % n], r1[k]))
    ob = _new_obj("Ruffle", bm, M["organza"])
    thicken(ob, 0.0015 * S)
    transfer_weights(ob, bod)
    return ob


# ── 腰帶、玫瑰結、飄帶 ──
def sash(M, c):
    z0, z1 = c.get("z0", 0.962), c.get("z1", 0.997)
    keep = lambda co: (z0 - 0.01) * S < co.z < (z1 + 0.005) * S and abs(co.x) < 0.17 * S
    ob = shell_piece(O[f"{WHO}_Body"], P + "Sash", keep, c.get("offset", 0.0105) * S, M["sash"])
    clean_cut(ob, [((0, 0, z1 * S), (0, 0, 1)), ((0, 0, z0 * S), (0, 0, -1))])
    thicken(ob, 0.003 * S)
    return ob


def _blob(bm, c, r, rot):
    res = bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=10, radius=1.0)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(c) @ rot @ Matrix.Diagonal((*r, 1)), verts=res["verts"])


def rosette(M, c):
    center = sv(*c.get("center", (0.05, -0.125, 0.985))); k = c.get("scale", 1.6) * S
    bm = bmesh.new()
    face_rot = Matrix.Rotation(math.radians(90), 4, "X")
    for ring, (rad, size, cnt, tilt) in enumerate(((0.030, (0.026, 0.008, 0.018), 7, 35), (0.016, (0.018, 0.007, 0.013), 5, 55))):
        rad *= k; size = tuple(v * k for v in size)
        for i in range(cnt):
            a = 2 * math.pi * i / cnt + ring * 0.4
            p = center + face_rot @ Vector((math.cos(a) * rad, math.sin(a) * rad, 0.006 * S * ring))
            _blob(bm, p, size, face_rot @ Matrix.Rotation(a, 4, "Z") @ Matrix.Rotation(math.radians(tilt), 4, "Y"))
    _blob(bm, center + Vector((0, -0.016 * S, 0)), (0.016 * S, 0.012 * S, 0.016 * S), Matrix.Identity(4))
    ob = _new_obj("Rosette", bm, M["sash"])
    _weights(ob, [("J_Bip_C_Hips", lambda co: 1.0)])
    return ob


def ribbon_tails(M, c):
    top = sv(*c.get("top", (0.05, -0.12, 0.975)))
    bm = bmesh.new()
    for side, (dx, length, sway) in enumerate(((0.012, 0.36, 1), (-0.01, 0.30, -1))):
        rows = []
        for j in range(16):
            t = j / 15
            p = top + sv(dx + 0.03 * t * sway + 0.012 * math.sin(t * 6), -0.012 - 0.06 * math.sin(t * 2.2) - 0.02 * t, -length * t)
            w = (0.022 + 0.008 * t) * S
            tw = 0.6 * math.sin(t * 4 + side)
            u = Vector((math.cos(tw), math.sin(tw) * 0.4, 0)).normalized()
            rows.append([bm.verts.new(p - u * w), bm.verts.new(p + u * w)])
        for r0, r1 in zip(rows, rows[1:]):
            bm.faces.new((r0[0], r0[1], r1[1], r1[0]))
    ob = _new_obj("SashTails", bm, M["sash"])
    thicken(ob, 0.002 * S)
    _weights(ob, [("J_Bip_C_Hips", lambda co: 1.0)])
    return ob


# ── 裙子：旋轉剖面網格（下擺高度可隨角度變、褶數、拖尾） ──
PROFILES = {
    # (t, 半寬 x, 半深 y)：t＝0 腰（z 0.985）到 1 地面（z 0.02），依實際高度取半徑
    "ball": [(0.0, 0.138, 0.118), (0.06, 0.175, 0.150), (0.15, 0.235, 0.205), (0.3, 0.315, 0.28),
             (0.5, 0.40, 0.36), (0.7, 0.465, 0.42), (0.88, 0.51, 0.46), (1.0, 0.535, 0.485)],
    "aline": [(0.0, 0.138, 0.118), (0.08, 0.17, 0.145), (0.2, 0.205, 0.18), (0.5, 0.28, 0.25), (1.0, 0.39, 0.35)],
    "mermaid": [(0.0, 0.138, 0.118), (0.12, 0.172, 0.14), (0.3, 0.165, 0.135), (0.5, 0.14, 0.12), (0.65, 0.15, 0.13),
                (0.85, 0.26, 0.24), (1.0, 0.36, 0.33)],
    "column": [(0.0, 0.138, 0.118), (0.12, 0.17, 0.14), (0.4, 0.165, 0.14), (1.0, 0.18, 0.16)],
}
LENGTH_Z = {"floor": 0.015, "ankle": 0.09, "midi": 0.3, "knee": 0.47, "mini": 0.66}
WAIST_Z = 0.985


def prof_fn(name, grow=1.0, add=0.0):
    pts = PROFILES[name]
    def f(t):
        t = max(0.0, min(1.0, t))
        for (t0, x0, y0), (t1, x1, y1) in zip(pts, pts[1:]):
            if t <= t1:
                u = (t - t0) / (t1 - t0); return (x0 + (x1 - x0) * u) * grow + add, (y0 + (y1 - y0) * u) * grow + add
        return pts[-1][1] * grow + add, pts[-1][2] * grow + add
    return f


def skirt_mesh(name, mat, prof, hem_z=lambda a: 0.02, folds=0, fold_amp=0.0, fold_ph=0.0, train=0.0,
               N=128, R=18, scale=1.0, top_z=WAIST_Z, ytop=-0.004):
    """新娘座標建網格再整體乘 S。prof(t) 依實際高度（腰→地面）取半徑"""
    bm = bmesh.new(); rows = []
    for j in range(R + 1):
        t = j / R
        row = []
        for k in range(N):
            a = 2 * math.pi * k / N
            z = top_z + (hem_z(a) - top_z) * t
            rx, ry = prof((top_z - z) / (top_z - 0.02))
            back = max(0.0, math.sin(a)) ** 2                                    # 角色面向 -Y，sin>0 是背面
            f = 1 + fold_amp * (t ** 1.3) * math.sin(folds * a + fold_ph) + train * back * t ** 2
            row.append(bm.verts.new(sv(math.cos(a) * rx * f * scale, ytop + math.sin(a) * ry * f * scale + train * 0.25 * back * t ** 2, z)))
        rows.append(row)
    for r0, r1 in zip(rows, rows[1:]):
        for k in range(N):
            bm.faces.new((r0[k], r0[(k + 1) % N], r1[(k + 1) % N], r1[k]))
    return _new_obj(name, bm, mat)


def skirt_weights(ob, waist=WAIST_Z):
    w0 = waist * S
    def wh(co): return max(0.0, 1.0 - max(0.0, min(1.0, (w0 - co.z) / (w0 * 0.85))) ** 1.3)
    def ws(co): return 1.0 - wh(co)
    _weights(ob, [("J_Bip_C_Hips", wh)] + ([("Skirt_Sway", ws)] if "Skirt_Sway" in A.data.bones else []))


def skirts(M, c):
    prof = c.get("profile", "ball"); hz = LENGTH_Z.get(c.get("length", "floor"), c.get("hem_z", 0.015))
    out = []
    if c.get("lining", True):
        out.append(skirt_mesh("Lining", M["lining"], prof_fn(prof), hem_z=lambda a: hz, folds=12, fold_amp=0.025, scale=0.985))
    for i in range(c.get("tulle_layers", 2)):
        tl = skirt_mesh(f"Tulle{i + 1}", M["tulle"], prof_fn(prof), hem_z=lambda a, i=i: max(0.004, hz - 0.004 * (i + 1)),
                        folds=17 + 6 * i, fold_amp=0.05 + 0.01 * i, fold_ph=0.3 + 0.8 * i, train=c.get("train", 0.2) * (0.6 + 0.4 * i), scale=1.02 + 0.03 * i)
        thicken(tl, 0.0015 * S); out.append(tl)
    for ob in out:
        skirt_weights(ob)
    return out


def drape(M, c, prof):
    hi, lo, ang = c.get("high_z", 0.78), c.get("low_z", 0.38), math.radians(c.get("high_angle", -60))
    def hem(a):
        k = 0.5 + 0.5 * math.cos(a - ang)                          # -60°＝左前（+X、-Y）
        return hi * k + lo * (1 - k)
    ob = skirt_mesh("Drape", M["organza"], prof_fn(prof, 1.07, 0.012), hem_z=hem, folds=c.get("folds", 7), fold_amp=0.07, fold_ph=0.5, R=14)
    skirt_weights(ob); thicken(ob, 0.0015 * S)
    return ob


def back_cascade(M, c, prof):
    """背後一側的荷葉瀑布：一層層往下的波浪布片（side：right＝-X 側）"""
    sgn = -1 if c.get("side", "right") == "right" else 1
    pf = prof_fn(prof)
    bm = bmesh.new()
    for tier in range(c.get("tiers", 5)):
        z0 = 0.93 - tier * 0.12
        rows = []
        for j in range(5):
            t = j / 4
            row = []
            for k in range(25):
                u = k / 24
                a = math.radians(70 + 70 * u)
                rx, ry = pf((WAIST_Z - (z0 - 0.09 * t)) / 0.965)
                rr = 1.10 + 0.06 * t + 0.05 * math.sin(u * math.pi * 6 + tier) * t
                row.append(bm.verts.new(sv(sgn * (abs(math.cos(a)) * rx * rr + 0.02), math.sin(a) * ry * rr + 0.01, z0 - 0.10 * t)))
            rows.append(row)
        for r0, r1 in zip(rows, rows[1:]):
            for k in range(24):
                bm.faces.new((r0[k], r0[k + 1], r1[k + 1], r1[k]))
    ob = _new_obj("Cascade", bm, M["organza"])
    thicken(ob, 0.0015 * S); skirt_weights(ob)
    return ob


# ── 髮飾蝴蝶結、耳環 ──
def _torus(bm, R, r, M_, nu=24, nv=10):
    rings = []
    for i in range(nu):
        a = 2 * math.pi * i / nu
        ring = []
        for j in range(nv):
            b = 2 * math.pi * j / nv
            ring.append(bm.verts.new(M_ @ Vector(((R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a), r * math.sin(b)))))
        rings.append(ring)
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((rings[i][j], rings[(i + 1) % nu][j], rings[(i + 1) % nu][(j + 1) % nv], rings[i][(j + 1) % nv]))


def hair_bow(M, c):
    zc = c.get("z", 1.50) * S
    hv = [v.co for v in O[f"{WHO}_Hair"].data.vertices if abs(v.co.x) < 0.03 * S and abs(v.co.z - zc) < 0.02 * S]
    ctr = Vector((0.0, max(v.y for v in hv) + 0.012 * S, zc))           # 頭髮背面外 1 公分
    k = c.get("scale", 1.0) * S
    bm = bmesh.new()
    for sx in (1, -1):
        M_ = (Matrix.Translation(ctr + Vector((0.045 * sx, 0.006, 0.004)) * k) @ Matrix.Rotation(math.radians(90), 4, "X")
              @ Matrix.Rotation(math.radians(12 * sx), 4, "Z") @ Matrix.Diagonal((1.25 * k, 0.75 * k, 0.35 * k, 1)))
        _torus(bm, 0.032, 0.011, M_)
        rows = []
        for j in range(8):
            t = j / 7
            p = ctr + Vector((0.012 * sx + 0.03 * t * sx, 0.012 + 0.01 * t, -0.012 - 0.10 * t)) * k
            rows.append([bm.verts.new(p + Vector((-0.012 * k, 0, 0))), bm.verts.new(p + Vector((0.012 * k, 0, 0)))])
        for r0, r1 in zip(rows, rows[1:]):
            bm.faces.new((r0[0], r0[1], r1[1], r1[0]))
    _blob(bm, ctr + Vector((0, 0.01, 0)) * k, (0.014 * k, 0.010 * k, 0.016 * k), Matrix.Identity(4))
    ob = _new_obj("HairBow", bm, M["bow"])
    _weights(ob, [("J_Bip_C_Head", lambda co: 1.0)])
    return ob


def earrings(M, c):
    face = O[f"{WHO}_Face"].data
    bm = bmesh.new()
    for sx in (1, -1):
        ear = [v.co for v in face.vertices if v.co.x * sx > 0.07 * S and 1.38 * S < v.co.z < 1.47 * S]
        if not ear:
            continue
        lobe = min(ear, key=lambda v: v.z)
        ctr = Vector((lobe.x + 0.004 * S * sx, lobe.y, lobe.z - 0.012 * S))
        _blob(bm, ctr + Vector((0, 0, 0.008 * S)), (0.003 * S,) * 3, Matrix.Identity(4))
        if c.get("style", "flower") == "flower":
            for i in range(5):
                a = 2 * math.pi * i / 5
                _blob(bm, ctr + Vector((0, math.cos(a) * 0.006, math.sin(a) * 0.006)) * S, (0.0018 * S, 0.005 * S, 0.0028 * S), Matrix.Rotation(a, 4, "X"))
        _blob(bm, ctr + Vector((0, 0, -0.013 * S)), (0.0035 * S, 0.0035 * S, 0.0045 * S), Matrix.Identity(4))   # 垂墜珍珠
    ob = _new_obj("Earrings", bm, M["metal"])
    _weights(ob, [("J_Bip_C_Head", lambda co: 1.0)])
    return ob


# ── 鞋子換色：貼圖黑→指定色、白→白 ──
def recolor_shoes(color):
    sh = O.get(f"{WHO}_Shoes")
    if sh is None:
        return None
    m = sh.material_slots[0].material
    src = m.vrm_addon_extension.mtoon1.pbr_metallic_roughness.base_color_texture.index.source
    name = f"{WHO}_Cos_ShoesTex"
    img = bpy.data.images.get(name)
    if img is None:
        img = src.copy(); img.name = name
    px = list(src.pixels[:])
    for i in range(0, len(px), 4):
        k = min(1.0, (0.3 * px[i] + 0.59 * px[i + 1] + 0.11 * px[i + 2]) * 1.15)
        for ch in range(3):
            px[i + ch] = color[ch] * (1 - k) + 1.0 * k
    img.pixels = px; img.pack()
    nm = bpy.data.materials.get(P + "ShoesMat") or m.copy(); nm.name = P + "ShoesMat"
    nt = nm.vrm_addon_extension.mtoon1
    nt.pbr_metallic_roughness.base_color_texture.index.source = img
    nt.extensions.vrmc_materials_mtoon.shade_multiply_texture.index.source = img
    return nm


def clear_costume():
    for o in [o for o in O if o.name.startswith(P)]:
        bpy.data.objects.remove(o, do_unlink=True)


def build_costume(spec=None):
    """依規格重建整套服裝；回傳建出的元件清單（物件名稱）"""
    spec = spec or load_spec()
    clear_costume()
    M = mats(spec); comp = spec.get("components", {})
    on = lambda k: comp.get(k, {}).get("enabled", False)
    prof = comp.get("skirt", {}).get("profile", "ball")
    if on("bodice"):
        bod = bodice(M, comp["bodice"])
        if on("ruffle"): ruffle(M, comp["ruffle"], bod)
    if on("sash"): sash(M, comp["sash"])
    if on("rosette"): rosette(M, comp["rosette"])
    if on("sash_tails"): ribbon_tails(M, comp["sash_tails"])
    if on("skirt"): skirts(M, comp["skirt"])
    if on("drape"): drape(M, comp["drape"], prof)
    if on("cascade"): back_cascade(M, comp["cascade"], prof)
    if on("hair_bow"): hair_bow(M, comp["hair_bow"])
    if on("earrings"): earrings(M, comp["earrings"])
    shoes = comp.get("shoes", {})
    if shoes.get("recolor"):
        recolor_shoes(shoes["recolor"])
    for mod in spec.get("extra_scripts", []):                 # 專案自訂元件（PROJ/scripts/<mod>.py 定義 build_extra(M, spec)）
        use(mod); globals()["build_extra"](M, spec)
    return sorted(o.name for o in O if o.name.startswith(P))


def wear(outfit):
    """'costume'：顯示服裝、藏便服；'base'：顯示便服（MANIFEST.base_parts，預設小可愛＋短褲）"""
    cos = outfit == "costume"
    base_parts = MANIFEST.get("base_parts") or ([f"{WHO}_BaseTop", f"{WHO}_Shorts"] if f"{WHO}_BaseTop" in O else [f"{WHO}_Tee", f"{WHO}_Shorts"])
    keep = set(load_spec().get("keep_vroid", ["Shoes"])) if cos else set()
    for o in O:
        if o.name.startswith(P):
            o.hide_render = o.hide_viewport = not cos
    for n in (f"{WHO}_Tee", f"{WHO}_Shorts", f"{WHO}_BaseTop", f"{WHO}_Onepiece", f"{WHO}_Socks"):
        if n in O:
            show = (n in base_parts) if not cos else (n.split("_", 1)[1] in keep)
            O[n].hide_render = O[n].hide_viewport = not show
    sh = O.get(f"{WHO}_Shoes")
    if sh:
        # keep_vroid 沒列 Shoes＝服裝自己做了鞋（<WHO>_Cos_* 物件）：穿服裝時藏起 VRoid 的鞋；便服一律顯示。
        # 貼地用的鞋底取樣點讀的是網格資料（pose_lib.sole_points），藏起來不影響。
        sh.hide_render = sh.hide_viewport = cos and "Shoes" not in keep
        cmat = bpy.data.materials.get(P + "ShoesMat")
        # 排除 VRM add-on 自動建的輪廓線材質「MToon Outline (…Shoes…)」：它沒有貼圖，套上去鞋子會變成一片暗紅
        orig = next((m for m in bpy.data.materials if "Shoes" in m.name and not m.name.startswith(P)
                     and not m.name.startswith("MToon Outline")), None)
        if (cos and cmat) or orig:
            sh.material_slots[0].material = cmat if (cos and cmat) else orig
