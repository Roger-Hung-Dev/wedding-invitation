# ZEPETO 穿戴物品的「細節＋寫實布料」配方（2026-10-14 起所有新衣服都用這套；使用者看過三種質感比較後選寫實布料，並決定所有衣服都改用）。
# 和 garment_lib.py 的分工：garment_lib＝從身體長衣服的基本動作、舊黏土風配方（已定案的舊服裝還在用，不要刪）；
# 這裡＝照參考照刻細節的配方、布料模擬定形、寫實布料材質、給動畫端的交接資料（裙面半徑表、提裙掛點）。
# 做法：
#   形狀要照參考照刻出來（摺、荷葉邊、層次、緞帶都做在模型上），不再簡化成大形。
#   會垂墜的布（外層紗、荷葉邊）先用公式排出大摺，再用布料模擬在「靜止姿勢」垂一次定形、套用成形狀；動畫時不模擬。
#   材質用 fabric()：寫實布料（光澤、透光、薄紗半透明），不用黏土霧面。
# 第一次實做：新娘細節版禮服（library/outfits-zepeto/_drafts/bride-blush-ballgown-v2/outfit.py）。
# 座標同 garment_lib：角色面向 −Y、左手 +X、Z 朝上，單位 m。角度 0＝正前方，往 +X（角色左邊）轉。
import bpy, bmesh, math, random
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import garment_lib as G

A = G.A; O = G.O; sc = G.sc; arm = G.arm; body = G.body
ss = G.smooth_step


# ════════ 小工具 ════════
def bvh_eval(obj):
    """obj 在靜止姿勢、套完修改器後的表面"""
    G.rest(True)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg); me = ev.to_mesh()
    bvh = BVHTree.FromPolygons([obj.matrix_world @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons])
    ev.to_mesh_clear()
    G.rest(False)
    return bvh


def nearest_hit(bvhs, origin, direction):
    """好幾個表面一起打射線，取最先碰到的"""
    best = None
    for b in bvhs:
        h = b.ray_cast(origin, direction)
        if h[0] is not None and (best is None or h[3] < best[3]):
            best = h
    return best


def new_obj(name, bm, role):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = O.new(name, me); sc.collection.objects.link(o)
    o["role"] = role
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def apply_mod(o, name):
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.select_all(action="DESELECT"); o.select_set(True)
    bpy.ops.object.modifier_apply(modifier=name)


def thicken(o, t, offset=-1.0):
    s = o.modifiers.new("Thickness", "SOLIDIFY"); s.thickness = t; s.offset = offset; s.use_even_offset = False   # 「厚度一致」在頭尾重疊的尖角會算爆（2026-10-14 外層紗一個點飛到 6 m 外）
    apply_mod(o, "Thickness")


def subsurf(o, levels=1):
    s = o.modifiers.new("Round", "SUBSURF"); s.levels = levels
    apply_mod(o, "Round")


def copy_weights(o, src):
    """跟著 src 動：抄 src 的頂點群組權重（裙子類是自訂權重，不是身體）"""
    G.rest(True)
    for m in list(o.modifiers):
        o.modifiers.remove(m)
    o.vertex_groups.clear()
    for g in src.vertex_groups:
        o.vertex_groups.new(name=g.name)
    dt = o.modifiers.new("Weights", "DATA_TRANSFER")
    dt.object = src; dt.use_object_transform = True
    dt.use_vert_data = True; dt.data_types_verts = {"VGROUP_WEIGHTS"}
    dt.vert_mapping = "POLYINTERP_NEAREST"
    dt.layers_vgroup_select_src = "ALL"; dt.layers_vgroup_select_dst = "NAME"
    apply_mod(o, "Weights")
    o.parent = arm; o.matrix_parent_inverse = arm.matrix_world.inverted()
    a = o.modifiers.new("Armature", "ARMATURE"); a.object = arm
    G.rest(False)
    return o


def grid_faces(bm, grid, wrap=False):
    rows, n = len(grid), len(grid[0])
    for i in range(rows - 1):
        for j in range(n if wrap else n - 1):
            k = (j + 1) % n
            bm.faces.new((grid[i][j], grid[i][k], grid[i + 1][k], grid[i + 1][j]))


SIM = True       # False＝只用公式排的形狀、不垂（比較或除錯用；outfit.py 可依參數設定）


def drape(o, colliders, frames=16, pin_fn=None, stiff=18.0, mass=0.10):
    """布料模擬垂一次定形（靜止姿勢、只算 frames 格）→ 套用成形狀 → 被彈飛的點拉回原位 → 抹掉碎皺。
    pin_fn(頂點座標)→0～1，1＝釘住不動。歐根紗硬挺：彎曲剛性調高，才會是大圓摺、不是碎皺"""
    if not SIM:
        return o
    G.rest(True)
    before = [v.co.copy() for v in o.data.vertices]
    vg = o.vertex_groups.new(name="Pin")
    for v in o.data.vertices:
        w = pin_fn(v.co)
        if w > 0:
            vg.add([v.index], w, "REPLACE")
    cols = []
    for c in colliders:
        m = c.modifiers.new("DrapeCollide", "COLLISION"); cols.append((c, m))
        c.collision.thickness_outer = 0.002; c.collision.cloth_friction = 10.0; c.collision.damping = 0.9
    cl = o.modifiers.new("Drape", "CLOTH")
    s = cl.settings
    s.quality = 10; s.mass = mass; s.air_damping = 5.0
    s.tension_stiffness = 40; s.compression_stiffness = 40; s.shear_stiffness = 15; s.bending_stiffness = stiff
    s.tension_damping = 10; s.compression_damping = 10; s.bending_damping = 2.0
    s.vertex_group_mass = "Pin"; s.pin_stiffness = 1.0
    cl.collision_settings.distance_min = 0.002
    cl.collision_settings.use_self_collision = False
    cl.point_cache.frame_start = 1; cl.point_cache.frame_end = frames
    f0 = sc.frame_current
    for f in range(1, frames + 1):
        sc.frame_set(f)
    apply_mod(o, "Drape")
    sc.frame_set(f0)
    for c, m in cols:
        c.modifiers.remove(m)
    pin = o.vertex_groups.get("Pin")              # 套用修改器後舊的群組參照會失效，要重新拿
    if pin:
        o.vertex_groups.remove(pin)
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    bad = {v for v, b in zip(bm.verts, before) if (v.co - b).length > 0.035}      # 模擬爆掉的點
    flung = len(bad)
    for _ in range(30):                           # 用沒爆的鄰點平均補回（直接拉回原位會和旁邊的點脫節、拉成尖刺）
        if not bad:
            break
        fixed = set()
        for v in bad:
            nb = [e.other_vert(v).co for e in v.link_edges if e.other_vert(v) not in bad]
            if nb:
                v.co = sum(nb, Vector()) / len(nb); fixed.add(v)
        bad -= fixed
    inner = [v for v in bm.verts if not v.is_boundary]
    for _ in range(3):
        bmesh.ops.smooth_vert(bm, verts=inner, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bm.to_mesh(o.data); bm.free()
    print("DRAPE", o.name, "flung", flung)
    G.rest(False)
    return o


# ════════ 裙子：好幾層蓬紗（裡面一層不透的襯裙＋外面兩層半透明紗） ════════
def body_sections(zs, n, cy):
    """一次量好幾個高度的身體水平剖面（只建一次 BVH）：{z: [(角度, 半徑)]}，從外往內打射線拿最外層表面"""
    G.rest(True)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg); me = ev.to_mesh()
    bvh = BVHTree.FromPolygons([body.matrix_world @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons])
    ev.to_mesh_clear()
    G.rest(False)
    out = {}
    for z in zs:
        row = []
        for i in range(n):
            a = 2 * math.pi * i / n
            d = Vector((math.sin(a), -math.cos(a), 0))
            hit = bvh.ray_cast(Vector((0, cy, z)) + d * 0.6, -d)
            row.append((a, (hit[0] - Vector((0, cy, z))).length if hit[0] else 0.08))
        out[z] = row
    return out


def tulle_layer(name, role, waist, hem, r_hem, bell=2.2, ease=0.010, folds=(13, 19, 29), fold_amp=0.014,
                gather_amp=0.0025, hem_wave=0.008, seed=1, rows=44, n=200, thick=0.0015, leg_share=0.35):
    """鐘形蓬裙的一層紗：旋轉體＋不規則直摺（幾組不同數量的波疊起來，越往下越明顯）＋腰上一圈細碎抽皺＋下襬微微高低不平"""
    sec, cy = G._section_radius(body, waist, n)
    rnd = random.Random(seed)
    waves = [(k, rnd.uniform(0, 2 * math.pi), rnd.uniform(0.6, 1.0)) for k in folds]
    wsum = sum(w for _, _, w in waves)
    grid_pts = []
    for i in range(rows + 1):
        t = i / rows
        zz = waist + (hem - waist) * t
        shape = 1 - (1 - t) ** bell
        row = []
        for a, r in sec:
            f = sum(w * math.sin(k * a + ph) for k, ph, w in waves) / wsum
            g = math.sin(56 * a + seed)
            rr = (r + ease) * (1 - shape) + r_hem * shape + fold_amp * f * t ** 0.8 + gather_amp * g * (1 - t) ** 3
            z2 = zz + hem_wave * math.sin(7 * a + 2 * seed) * t ** 4
            row.append(Vector((math.sin(a) * rr, cy - math.cos(a) * rr, z2)))
        grid_pts.append(row)
    bm = G._ring_mesh(grid_pts, n)
    o = new_obj(name, bm, role)
    thicken(o, thick)
    G.bind_skirt(o, waist, hem, leg_share)
    return o


# ════════ 上身：斜向放射摺（從腰間布花往右肩方向散開） ════════
def draped_bodice(name, mat, top, hem, knot, folds=7, amp=0.010, thick=0.002):
    """平口上身：從身體複製、往外推出厚度，加從腰間布花往右肩散開的斜摺"""
    o = G.body_copy(name); bm = G.open_bm(o)
    G.cut(bm, (0, 0, hem - 0.08), (0, 0, -1))
    G.cut(bm, (0, 0, top + 0.05), (0, 0, 1))
    G.drop_loose(bm, lambda c, n: abs(c.x) < 0.2 and n > 500)
    G.inflate(bm, lambda p: 0.008, smooth=24)
    G.cut(bm, (0, 0, top), (0, 0, 1))
    G.cut(bm, (0, 0, hem), (0, 0, -1))
    G.drop_loose(bm, lambda c, n: abs(c.x) < 0.2 and n > 500)
    bm.normal_update()
    moves = []
    for v in bm.verts:
        p, nrm = v.co, v.normal
        front = max(0.0, -nrm.y) ** 0.5 + 0.35 * max(0.0, 1 - abs(nrm.y)) ** 2      # 正面最明顯、側面淡一點
        dx, dz = p.x - knot.x, p.z - knot.z
        r = math.hypot(dx, dz); th = math.atan2(dz, dx)
        ridge = (0.5 + 0.5 * math.sin(folds * th + 1.2 * math.sin(2 * th) + 0.6)) ** 2.5
        env = ss(0.02, 0.08, r) * (1 - 0.65 * ss(top - 0.04, top, p.z))
        moves.append((v, nrm * amp * env * front * ridge))
    for v, d in moves:
        v.co += d
    inner = [v for v in bm.verts if not v.is_boundary]
    bmesh.ops.smooth_vert(bm, verts=inner, factor=0.35, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    G.close_bm(o, bm)
    o["role"] = "organza"
    return G.finish(o, [mat], thick, drop=G.NO_ARM)


def ring_bodice(name, mat, top, hem, knot, folds=7, amp=0.013, ease=0.008, thick=0.002, rows=44, n=180):
    """平口上身・乾淨網格版（備用；2026-10-14 新娘禮服試過，使用者選了 draped_bodice 那版的整體感）：每個高度量一圈身體外框，排成一圈圈乾淨的網格（不複製身體網格：身體的網格太亂，往外推會在胸下內凹處交疊成暗痕）。
    內凹只往外填平（上下、左右鄰點取大），像有支撐的硬挺上身；再加從腰間布花往右肩散開的斜摺"""
    cy = G._section_radius(body, (top + hem) / 2, 24)[1]
    zs = [top - (top - hem) * i / rows for i in range(rows + 1)]
    secs = body_sections(zs, n, cy)
    R = [[r + ease for _, r in secs[z]] for z in zs]
    for _ in range(20):                           # 上下方向：凹的地方往外填（只增不減，凸的地方不動 → 身體不會穿出來）
        R = [R[0]] + [[max(R[i][j], (R[i - 1][j] + R[i + 1][j]) / 2) for j in range(n)] for i in range(1, rows)] + [R[-1]]
    for _ in range(4):                            # 左右方向
        R = [[max(row[j], (row[j - 1] + row[(j + 1) % n]) / 2) for j in range(n)] for row in R]
    pts = []
    for i, z in enumerate(zs):
        row = []
        for j in range(n):
            a = 2 * math.pi * j / n
            x0, y0 = math.sin(a) * R[i][j], cy - math.cos(a) * R[i][j]
            front = max(0.0, math.cos(a)) ** 0.5 + 0.35 * max(0.0, 1 - abs(math.cos(a))) ** 2
            dx, dz = x0 - knot.x, z - knot.z
            rk = math.hypot(dx, dz); th = math.atan2(dz, dx)
            ridge = (0.5 + 0.5 * math.sin(folds * th + 1.2 * math.sin(2 * th) + 0.6)) ** 2.5
            env = ss(0.02, 0.08, rk) * (1 - 0.65 * ss(top - 0.04, top, z))
            rr = R[i][j] + amp * env * front * ridge
            row.append(Vector((math.sin(a) * rr, cy - math.cos(a) * rr, z)))
        pts.append(row)
    bm = G._ring_mesh(pts, n)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = O.new(name, me); sc.collection.objects.link(o)
    o["role"] = "organza"
    return G.finish(o, [mat], thick, drop=G.NO_ARM)


# ════════ 平口上緣：往上立起、再往外翻下來的捲邊摺紗（高低不平，兩側後方翹得比較高） ════════
def rolled_neckline(name, mat, on_obj, z, n=180, seed=5):
    sec, cy = G._section_radius(on_obj, z - 0.006, n)
    prof = [(0.0015, -0.030, 0.0), (0.003, -0.012, 0.0), (0.005, 0.008, 0.45), (0.008, 0.024, 0.9),
            (0.014, 0.033, 1.0), (0.022, 0.030, 0.95), (0.030, 0.018, 0.8), (0.034, 0.006, 0.7)]
    def h_of(a):
        bump = sum(math.exp(-((a - c) / 0.45) ** 2) for c in (1.95, 2 * math.pi - 1.95))   # 兩側後方的立起摺
        return 0.012 * math.cos(3 * a + 0.7) + 0.007 * math.cos(5 * a + 2.1) + 0.022 * bump
    rows = []
    for dr, dz, hw in prof:
        row = []
        for a, r in sec:
            h = h_of(a)
            fl = 0.005 * math.cos(7 * a + 1.0) * hw
            rr = r + dr * (1 + 0.8 * hw * max(0.0, h) / 0.02) + fl
            row.append(Vector((math.sin(a) * rr, cy - math.cos(a) * rr, z + dz + h * hw)))
        rows.append(row)
    bm = G._ring_mesh(rows, n)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = O.new(name, me); sc.collection.objects.link(o)
    subsurf(o, 1)
    o["role"] = "organza"
    return G.finish(o, [mat], 0.0018, drop=G.NO_ARM)


# ════════ 前胸斜包摺：從角色右側上緣斜斜往左下包過胸口的一片摺紗（照片正面那道斜摺），下緣捲起 ════════
def wrap_fold(name, mat, on_obj, p0, p1, width=0.032, steps=30, wr=6):
    bvh = bvh_eval(on_obj)
    bm = bmesh.new(); grid = []
    for i in range(steps + 1):
        t = i / steps
        x = p0[0] + (p1[0] - p0[0]) * t
        z = p0[1] + (p1[1] - p0[1]) * t
        w = width * (1.0 - 0.45 * t)
        row = []
        for k in range(wr + 1):
            u = k / wr
            zz = z + (u - 0.5) * w
            hit = bvh.ray_cast(Vector((x, -1.0, zz)), Vector((0, 1, 0)))
            q = hit[0] if hit[0] else Vector((x, -0.08, zz))
            curl = 0.010 * math.sin(math.pi * u) ** 0.7 + 0.006 * max(0.0, 0.3 - u) / 0.3      # 中間鼓起、下緣往外捲
            row.append(bm.verts.new(q + Vector((0, -(0.002 + curl * (1 - 0.5 * t)), 0))))
        grid.append(row)
    grid_faces(bm, grid)
    o = new_obj(name, bm, "organza")
    subsurf(o, 1)
    thicken(o, 0.0016, offset=0.0)
    o.data.materials.append(mat)
    G.transfer_weights(o, drop=G.NO_ARM)
    return o


# ════════ 腰下歐根紗外層：大軟摺、正前方斜開口露出蓬紗，後面比較長 ════════
def peplum(name, mat, waist, skirt, length, open_front=1.1, rolls=7, roll_amp=0.04, seed=3, rows=26, n=170):
    sec, cy = G._section_radius(body, waist, 96)
    sk = bvh_eval(skirt)
    rnd = random.Random(seed)
    ph = [rnd.uniform(0, 2 * math.pi) for _ in range(3)]
    secr = lambda a: min(sec, key=lambda s: abs(math.atan2(math.sin(s[0] - a), math.cos(s[0] - a))))[1]
    bm = bmesh.new(); grid = []
    for i in range(rows + 1):
        t = i / rows
        op = open_front * t ** 0.8                     # 開口越往下越寬＝斜的前緣
        row = []
        for j in range(n):
            a = op / 2 + (2 * math.pi - op) * j / (n - 1)
            back = 0.5 - 0.5 * math.cos(a)             # 0＝正前、1＝正後
            L = length * (0.85 + 0.35 * back)
            roll = 0.5 + 0.5 * math.sin(rolls * a + ph[0] + 0.8 * math.sin(3 * a + ph[1]))
            z = waist - L * t + 0.035 * t ** 2 * roll
            d = Vector((math.sin(a), -math.cos(a), 0))
            far = Vector((0, cy, z)) + d * 1.5
            hit = sk.ray_cast(far, -d)
            rs = (hit[0] - Vector((0, cy, z))).length if hit[0] else secr(a) + 0.02
            rw = secr(a) + 0.014
            rbase = rw + (rs - rw) * ss(0.0, 0.35, t)   # 腰上貼身，往下貼到裙面上
            off = 0.012 + roll_amp * t ** 1.2 * roll
            rr = max(rbase, rs) + off if t > 0.3 else rbase + off * t / 0.3
            row.append(bm.verts.new(Vector((math.sin(a) * rr, cy - math.cos(a) * rr, z))))
        grid.append(row)
    grid_faces(bm, grid)
    o = new_obj(name, bm, "organza")
    o.data.materials.append(mat)
    zt = waist - 0.02
    drape(o, [skirt], pin_fn=lambda c: ss(zt - 0.03, zt + 0.005, c.z))
    thicken(o, 0.0018)
    return copy_weights(o, skirt)


# ════════ 瀑布荷葉邊：沿裙面一圈一圈往下疊，下緣比上緣長很多所以一路起伏 ════════
def cascade(name, mat, skirt, z_top, length, span, center=math.pi, wave_len=0.11, amp=0.045, drop_back=0.03,
            seed=0, rows=16, n=150, colliders=()):
    sk = bvh_eval(skirt)
    cy = G._section_radius(body, A["HIP_Z"] + 0.10, 24)[1]      # 裙子的中心軸（身體前後的中點）
    bm = bmesh.new(); grid = []
    for i in range(rows + 1):
        v = i / rows
        row = []
        for j in range(n):
            u = j / (n - 1)
            a = center + (u - 0.5) * span
            z_att = z_top - drop_back * (0.5 + 0.5 * math.cos(a - center))
            z = z_att - length * v * 0.92
            d = Vector((math.sin(a), -math.cos(a), 0))
            hit = sk.ray_cast(Vector((0, cy, z)) + d * 1.5, -d)
            rs = (hit[0] - Vector((0, cy, z))).length if hit[0] else 0.4
            arc = (a - center) * 0.40
            rip = 0.5 + 0.5 * math.sin(2 * math.pi * arc / wave_len + seed + 0.7 * math.sin(arc * 9 + seed))
            end = ss(0.0, 0.10, u) * ss(1.0, 0.90, u)
            off = 0.010 + (0.008 + amp * rip) * v ** 1.3 * (0.35 + 0.65 * end)
            z += 0.03 * v ** 2 * rip
            rr = rs + off
            row.append(bm.verts.new(Vector((math.sin(a) * rr, cy - math.cos(a) * rr, z))))
        grid.append(row)
    grid_faces(bm, grid)
    o = new_obj(name, bm, "organza")
    o.data.materials.append(mat)
    top = z_top - drop_back
    drape(o, [skirt, *colliders], pin_fn=lambda c: 1.0 if c.z > z_top - drop_back * (0.5 + 0.5 * math.cos(math.atan2(c.x, -c.y) - center)) - 0.012 else 0.0)
    thicken(o, 0.0016)
    return copy_weights(o, skirt)


# ════════ 布花：一條緞帶捲成的玫瑰（外圈花瓣往外翻、邊緣微波浪） ════════
def ribbon_rose(name, mat, on_obj, x, z, size=0.05, turns=2.4, n=150, wr=6, seed=2):
    loc, nrm = G.surface_front(on_obj, x, z, normal=True)
    bm = bmesh.new(); grid = []
    for i in range(n + 1):
        s = i / n
        phi = 2 * math.pi * turns * s
        rho = size * (0.05 + 0.45 * s); h = size * (0.55 - 0.2 * s); tilt = 0.15 + 1.05 * s ** 1.2
        row = []
        for k in range(wr + 1):
            w = k / wr
            rad = rho + w * h * math.sin(tilt)
            hz = w * h * math.cos(tilt) + w ** 2 * 0.07 * size * math.sin(3 * phi + seed)
            row.append(bm.verts.new(Vector((math.cos(phi) * rad, math.sin(phi) * rad, hz))))
        grid.append(row)
    grid_faces(bm, grid)
    rot = Vector((0, 0, 1)).rotation_difference(nrm).to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation(loc + nrm * 0.003) @ rot, verts=bm.verts[:])
    o = new_obj(name, bm, "sash")
    thicken(o, 0.0015, offset=0.0)
    o.data.materials.append(mat)
    G.transfer_weights(o)
    return o


# ════════ 緞帶尾巴：從布花往下垂，貼著外層紗（沒有外層紗的地方貼裙子）、會扭轉、末端剪成燕尾 ════════
def ribbon_tails(name, mat, surfaces, x0, z0, length, ends=((-0.035, 0.0), (0.05, 1.7)), width=0.042, steps=28,
                 back=False, weight_src=None):
    bvhs = [bvh_eval(s) for s in surfaces]
    yd = 1.0 if back else -1.0
    bm = bmesh.new()
    for dx_end, ph in ends:
        rows = []
        for k in range(steps + 1):
            t = k / steps
            zz = z0 - length * t
            xc = x0 + dx_end * t + 0.012 * math.sin(3.0 * t + ph)
            w = width * (0.8 + 0.5 * t)
            tw = 0.9 * math.sin(2.4 * t + ph)
            row = []
            for sgn in (-1, 1):
                x = xc + sgn * w / 2 * math.cos(tw)
                hit = nearest_hit(bvhs, Vector((x, yd * 1.0, zz)), Vector((0, -yd, 0)))
                q = hit[0] if hit else Vector((x, 0, zz))
                lift = 0.006 + 0.004 * t + sgn * w / 2 * math.sin(tw) * 0.5
                row.append(bm.verts.new(q + Vector((0, yd * max(0.003, lift), 0))))
            rows.append(row)
        # 燕尾：最後一排外側兩點往下、中間收上去（多插一個中點）
        a, b = rows[-1]
        mid = bm.verts.new((a.co + b.co) / 2 + Vector((0, 0, width * 0.5)))
        a.co.z -= width * 0.15; b.co.z -= width * 0.15
        for k in range(steps - 1):
            bm.faces.new((rows[k][0], rows[k][1], rows[k + 1][1], rows[k + 1][0]))
        p0, p1 = rows[steps - 1]
        bm.faces.new((p0, mid, a)); bm.faces.new((p0, p1, mid)); bm.faces.new((p1, b, mid))
    o = new_obj(name, bm, "sash")
    subsurf(o, 1)
    thicken(o, 0.0015, offset=0.0)
    o.data.materials.append(mat)
    return copy_weights(o, weight_src or surfaces[0])


# ════════ 背後大蝴蝶結：兩個中空的緞帶圈（往外上翹、越往外越寬）＋中間結 ════════
def ribbon_bow(name, mat, on_obj, z, size=0.13, ribbon=0.06, n=60, wr=6):
    p = G.surface_back(on_obj, 0.0, z) + Vector((0, 0.010, 0))
    bm = bmesh.new()
    for sg in (1, -1):
        grid = []
        for i in range(n + 1):
            psi = 2 * math.pi * i / n
            out = 0.5 - 0.5 * math.cos(psi)
            cx = sg * size * out
            cyb = 0.045 * math.sin(psi) * (0.4 + 0.6 * out) + 0.012 * out
            cz = 0.30 * size * out
            W = ribbon * (0.55 + 0.75 * out)
            row = []
            for k in range(wr + 1):
                w = k / wr - 0.5
                row.append(bm.verts.new(p + Vector((cx, cyb + 0.004 * math.sin(math.pi * (w + 0.5)), cz + w * W))))
            grid.append(row)
        grid_faces(bm, grid)
    knot = bmesh.ops.create_uvsphere(bm, u_segments=18, v_segments=10, radius=1.0)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(p + Vector((0, 0.012, 0))) @ Matrix.Diagonal((ribbon * 0.38, 0.016, ribbon * 0.55, 1)), verts=knot["verts"])
    o = new_obj(name, bm, "organza")
    thicken(o, 0.0016, offset=0.0)
    subsurf(o, 1)
    o.data.materials.append(mat)
    G.transfer_weights(o)
    return o


# ════════ 提裙掛點（給動畫端：走路時手捏住胯側的外層紗往上提，裙子跟著被拉起來） ════════
def skirt_grips(objs, ref_obj, z, angle_deg=72, radius=0.15, up=0.10):
    """在 ref_obj（外層紗）左右胯側各做一個抓點，objs 裡每件都加 Hook 修改器（排在 Armature 後面）：
      SkirtGrip_L／R＝Hook 的目標空物件，父物件是骨架「物件」（不是骨頭），靜止時在抓點上。
      SkirtGripAnchor_L／R＝掛在骨盆骨頭上、跟著身體走的錨點，標出「裙面上的抓點現在在哪」。
    動畫端每格：SkirtGrip.location = grip_rest + 骨架物件旋轉的反矩陣 @ (手指捏住的世界座標 − 錨點的世界座標)。
    （Hook 加的是「相對靜止時」的位移；掛點如果直接放到手指的絕對位置，裙子已經跟身體走過一次，會被再拉一次）
    權重：抓點水平 radius 內（6 cm 內全吃、往外漸弱），往上 up 內漸弱（腰不動），往下一路到裙襬都跟著提"""
    G.rest(True)
    cy = G._section_radius(body, A["HIP_Z"] + 0.10, 24)[1]
    bvh = bvh_eval(ref_obj)
    G.rest(True)
    hips = next(n for n in ("J_Bip_C_Hips", "mixamorig:Hips") if n in arm.data.bones)
    made = {}
    for side, sg in (("L", 1), ("R", -1)):
        a = math.radians(angle_deg) * sg
        d = Vector((math.sin(a), -math.cos(a), 0))
        hit = bvh.ray_cast(Vector((0, cy, z)) + d * 1.5, -d)
        g = hit[0]
        rg = math.hypot(g.x, g.y - cy)
        emp = O.new(f"SkirtGrip_{side}", None); sc.collection.objects.link(emp)
        emp.empty_display_type = "SPHERE"; emp.empty_display_size = 0.02; emp.hide_render = True
        emp.parent = arm; emp.matrix_parent_inverse = arm.matrix_world.inverted(); emp.location = g
        emp["grip_rest"] = list(g)
        anc = O.new(f"SkirtGripAnchor_{side}", None); sc.collection.objects.link(anc)
        anc.empty_display_type = "PLAIN_AXES"; anc.empty_display_size = 0.015; anc.hide_render = True
        anc.parent = arm; anc.parent_type = "BONE"; anc.parent_bone = hips
        bpy.context.view_layer.update()
        anc.matrix_world = Matrix.Translation(g)
        bpy.context.view_layer.update()
        for o in objs:
            vg = o.vertex_groups.get(f"grip_{side}") or o.vertex_groups.new(name=f"grip_{side}")
            for v in o.data.vertices:
                c = o.matrix_world @ v.co
                av = math.atan2(c.x, -(c.y - cy))
                da = abs(math.atan2(math.sin(av - a), math.cos(av - a)))
                dh = da * rg
                fv = 1 - ss(0.0, up, c.z - z) if c.z > z else 1.0
                w = (1 - ss(0.4 * radius, radius, dh)) * fv
                if w > 0.001:
                    vg.add([v.index], w, "REPLACE")
            hm = o.modifiers.new(f"Grip_{side}", "HOOK")
            hm.object = emp; hm.vertex_group = vg.name; hm.falloff_type = "NONE"; hm.strength = 1.0
            hm.center = o.matrix_world.inverted() @ g
            hm.matrix_inverse = (o.matrix_world.inverted() @ emp.matrix_world).inverted()
        made[side] = dict(grip_rest=[round(c, 4) for c in g], empty=emp.name, anchor=anc.name, anchor_bone=hips)
    G.rest(False)
    return made


# ════════ 裙面半徑表（給動畫端擺手）：高度 → 正面、側面、背面離身體中心的距離 ════════
def skirt_radius_table(objs, step=0.05):
    G.rest(True)
    dg = bpy.context.evaluated_depsgraph_get()
    vs, fs = [], []
    for o in objs:
        ev = o.evaluated_get(dg); me = ev.to_mesh(); k = len(vs)
        vs += [o.matrix_world @ v.co for v in me.vertices]; fs += [[k + i for i in p.vertices] for p in me.polygons]
        ev.to_mesh_clear()
    bvh = BVHTree.FromPolygons(vs, fs)
    hp = arm.matrix_world @ arm.data.bones[next(n for n in ("J_Bip_C_Hips", "mixamorig:Hips") if n in arm.data.bones)].head_local
    top = max(v.z for v in vs)
    rows = []
    z = 0.0
    while z <= top + 1e-6:
        r = []
        for deg in (0, 90, -90, 180):
            a = math.radians(deg); d = Vector((math.sin(a), -math.cos(a), 0))
            h = bvh.ray_cast(Vector((hp.x, hp.y, z)) + d * 1.5, -d)
            r.append((h[0] - Vector((hp.x, hp.y, z))).length if h[0] else 0.0)
        rows.append([round(z, 3), round(r[0], 3), round((r[1] + r[2]) / 2, 3), round(r[3], 3)])
        z += step
    G.rest(False)
    return dict(center=[round(hp.x, 4), round(hp.y, 4)], rows=rows)


# ════════ 材質：寫實布料 ════════
def _nodes(m):
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    return nt, out


def _real_bsdf(nt, rgb, rough, sheen, coat, translucent, metallic=0.0):
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Base Color"].default_value = G.lin(rgb)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Sheen Weight"].default_value = sheen; p.inputs["Sheen Roughness"].default_value = 0.35
    p.inputs["Coat Weight"].default_value = coat; p.inputs["Coat Roughness"].default_value = 0.15
    sh = p.outputs[0]
    if translucent:
        tr = nt.nodes.new("ShaderNodeBsdfTranslucent"); tr.inputs["Color"].default_value = G.lin(rgb)
        mx = nt.nodes.new("ShaderNodeMixShader"); mx.inputs[0].default_value = translucent
        nt.links.new(sh, mx.inputs[1]); nt.links.new(tr.outputs[0], mx.inputs[2]); sh = mx.outputs[0]
    return sh


def _with_alpha(nt, out, sh, alpha):
    """alpha：None＝不透明；數字＝固定；(正面, 斜面)＝薄紗正看較透、斜看較密"""
    if alpha is None:
        nt.links.new(sh, out.inputs["Surface"]); return
    tp = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    if isinstance(alpha, tuple):
        lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["To Min"].default_value = alpha[0]; mr.inputs["To Max"].default_value = alpha[1]
        pw = nt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 1.5
        nt.links.new(lw.outputs["Facing"], pw.inputs[0]); nt.links.new(pw.outputs[0], mr.inputs["Value"])
        nt.links.new(mr.outputs[0], mx.inputs[0])
    else:
        mx.inputs[0].default_value = alpha
    nt.links.new(tp.outputs[0], mx.inputs[1]); nt.links.new(sh, mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])


# 布料種類 → 粗糙度、光澤（sheen）、亮漆（coat）、透光、透明度、金屬。✔＝新娘細節版禮服實測、使用者看過；其餘是起始值，第一次用要看近照調
FABRIC = dict(
    organza=dict(rough=0.30, sheen=0.55, coat=0.25, translucent=0.25, alpha=0.94),          # ✔ 歐根紗：硬挺、有亮面、微透
    satin=dict(rough=0.32, sheen=0.55, coat=0.20, translucent=0.15, alpha=None),            # ✔ 緞帶、腰帶
    tulle=dict(rough=0.55, sheen=0.90, coat=0.0, translucent=0.30, alpha=(0.30, 0.85)),     # ✔ 薄紗：正看透、斜看密
    lining=dict(rough=0.50, sheen=0.45, coat=0.0, translucent=0.10, alpha=None),            # ✔ 襯裙
    canvas=dict(rough=0.60, sheen=0.20, coat=0.0, translucent=0.0, alpha=None),             # ✔ 帆布鞋
    metal=dict(rough=0.28, sheen=0.0, coat=0.0, translucent=0.0, alpha=None, metallic=1.0), # ✔ 銀飾
    wool=dict(rough=0.78, sheen=0.30, coat=0.0, translucent=0.0, alpha=None),               # 西裝毛料
    cotton=dict(rough=0.70, sheen=0.20, coat=0.0, translucent=0.05, alpha=None),            # 襯衫、T 恤
    knit=dict(rough=0.85, sheen=0.35, coat=0.0, translucent=0.0, alpha=None),               # 針織
    denim=dict(rough=0.80, sheen=0.10, coat=0.0, translucent=0.0, alpha=None),              # 牛仔布
    leather=dict(rough=0.40, sheen=0.0, coat=0.35, translucent=0.0, alpha=None),            # 皮鞋、皮帶
    pearl=dict(rough=0.25, sheen=0.0, coat=0.50, translucent=0.0, alpha=None),              # 扣子、珍珠
)


def fabric(name, rgb, kind, **override):
    """寫實布料材質。rgb 是 sRGB 0～255（色相照參考照）；kind 查 FABRIC；override 可蓋掉個別值（例：alpha=0.9）"""
    p = dict(FABRIC[kind]); p.update(override)
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt, out = _nodes(m)
    _with_alpha(nt, out, _real_bsdf(nt, rgb, p["rough"], p["sheen"], p["coat"], p["translucent"], p.get("metallic", 0.0)), p["alpha"])
    try:
        m.surface_render_method = "DITHERED"          # EEVEE：半透明一層層疊起來才排得對
    except Exception:
        pass
    try:
        m.use_transparent_shadow = True
    except Exception:
        pass
    return m
