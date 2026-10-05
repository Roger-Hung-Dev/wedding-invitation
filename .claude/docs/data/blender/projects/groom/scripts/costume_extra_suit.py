# 新郎三件式西裝（groom 專案自訂服裝元件）：costume.json 的 extra_scripts 列出，build_costume() 最後呼叫 build_extra(M, spec)。
# 參數在 spec["suit"]，座標一律是新娘座標（乘 S＝S_BODY 換到這個角色）；顏色在 spec["colors"]（MToon linear 值）。
#
# 做法（規格內建的元件都是禮服用的，西裝全部在這裡做）：
#   1. 西裝褲 Pants：骨盆截面 loft ＋ 兩條腿的直筒管（膝蓋以下取包絡、略收）→ 體素重建合成一塊 → 腰、褲口切平
#   2. 襯衫 Shirt：從身體皮膚撐開 3.5mm（只做軀幹），上緣包到領台頂端；領台 Collar：從脖子中心往外打射線量皮膚＋6mm，
#      前低後高繞一圈（半徑以頂圈為準，底部最多放大 12%，不然碰到肩膀會撐成一圈毛領）；袖口 Cuffs：手腕一小段白管
#   3. 背心 Vest：從皮膚撐開（下襬處加厚、蓋住褲頭），V 領、前下襬兩個尖角、4 顆扣子
#   4. 外套 Jacket：軀幹截面 loft（量身體＋放鬆量，胸口撐寬成直筒）＋兩條袖管 → 體素重建 → 離皮膚不到 9mm 的頂點往外推
#      （這個角色斜方肌很高，不推的話襯衫會從肩膀戳出來）→ 下襬、袖口切平 → 領口：前後兩個斜面，但只切離脖子中心
#      11cm 以內、而且面朝外的部分（⚠️ 無限大的斜面會把整片上胸、肩膀頂端一起切掉）→ 前襟敞開（照片是沒扣的單排扣）；
#      翻領 Lapel（劍領，含缺口）、胸袋、兩個有蓋口袋、袖扣都是貼在外套表面的薄片
#   5. 領結 BowTie：深藍，兩片翅膀＋中間的結
#   權重：都從 _SRC（原始身體）轉移；外套下襬的腿部權重部分移到骨盆，褲子拿掉腳掌權重（走路時褲口不跟腳尖翻）。
import bpy, bmesh, math
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

_SU_SKIN = lambda: [O[n] for n in (f"{WHO}_Body", f"{WHO}_BodyFill") if n in O]


def _su_p(spec):
    return spec.get("suit", {})


def _su_col(spec, key, d, ds):
    c = spec.get("colors", {})
    return tuple(c.get(key, d)), tuple(c.get(key + "_shade", ds))


# ── 量測：用平面切身體皮膚，取截面點 ──
class _SuSection:
    def __init__(self, objs):
        self.bms = []
        for ob in objs:
            bm = bmesh.new(); bm.from_mesh(ob.data); self.bms.append(bm)

    def cut(self, co, no, filt=None):
        pts = []
        for b0 in self.bms:
            bm = b0.copy()
            res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6, plane_co=co, plane_no=no)
            pts += [v.co.copy() for v in res["geom_cut"] if isinstance(v, bmesh.types.BMVert)]
            bm.free()
        return [p for p in pts if filt is None or filt(p)]

    def free(self):
        for b in self.bms:
            b.free()


def _su_ss(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def _su_lerp_tab(tab, z):
    """tab：[(z, 值...)] 依 z 線性內插（z 由小到大）"""
    if z <= tab[0][0]:
        return tab[0][1:]
    for a, b in zip(tab, tab[1:]):
        if z <= b[0]:
            u = (z - a[0]) / (b[0] - a[0])
            return tuple(x + (y - x) * u for x, y in zip(a[1:], b[1:]))
    return tab[-1][1:]


def _su_ring_xy(bm, z, cx, x0, x1, y0, y1, n=48, ex=2.6):
    """水平超橢圓圈：x 從 x0 到 x1、y 從 y0（前）到 y1（後）"""
    cxx = (x0 + x1) / 2; a = (x1 - x0) / 2; cy = (y0 + y1) / 2; b = (y1 - y0) / 2
    out = []
    for k in range(n):
        t = 2 * math.pi * k / n; c, s = math.cos(t), math.sin(t)
        out.append(bm.verts.new((cxx + a * math.copysign(abs(c) ** (2 / ex), c), cy + b * math.copysign(abs(s) ** (2 / ex), s), z)))
    return out


def _su_ring_yz(bm, x, cy, cz, ry, rz, n=32, ex=2.2):
    out = []
    for k in range(n):
        t = 2 * math.pi * k / n; c, s = math.cos(t), math.sin(t)
        out.append(bm.verts.new((x, cy + ry * math.copysign(abs(c) ** (2 / ex), c), cz + rz * math.copysign(abs(s) ** (2 / ex), s))))
    return out


def _su_loft(bm, rings, cap=True):
    n = len(rings[0])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(n):
            bm.faces.new((r0[k], r0[(k + 1) % n], r1[(k + 1) % n], r1[k]))
    if cap:
        bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])


def _su_obj(name, bm, mat):
    name = P + name
    if name in O:
        bpy.data.objects.remove(O[name], do_unlink=True)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); A.users_collection[0].objects.link(ob)
    me.materials.append(mat)
    return ob


def _su_apply_all(ob):
    for md in list(ob.modifiers):
        with bpy.context.temp_override(object=ob, active_object=ob):
            bpy.ops.object.modifier_apply(modifier=md.name)


def _su_remesh(ob, voxel, iters):
    m = ob.modifiers.new("Remesh", "REMESH"); m.mode = "VOXEL"; m.voxel_size = voxel; m.use_smooth_shade = True
    s = ob.modifiers.new("Smooth", "LAPLACIANSMOOTH"); s.iterations = iters; s.lambda_factor = 0.6; s.use_volume_preserve = True
    _su_apply_all(ob)
    for p in ob.data.polygons:
        p.use_smooth = True


def _su_cut_lines(ob, lines, kill):
    """lines：[(p0, p1)] 世界座標兩點（直線所在平面包含 Y 軸方向）沿線切開；kill(面中心, 面法線) 為真的面刪掉"""
    bm = bmesh.new(); bm.from_mesh(ob.data)
    for p0, p1 in lines:
        p0, p1 = Vector(p0), Vector(p1)
        d = (p1 - p0).normalized(); n = d.cross(Vector((0, 1, 0))).normalized()
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6, plane_co=p0, plane_no=n)
    bm.normal_update()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if kill(f.calc_center_median(), f.normal)], context="FACES")
    bm.to_mesh(ob.data); bm.free()


def _su_smooth_weights(ob, centers, radius, iters=12):
    """腋下一帶的權重沿網格抹平：外套離身體 2～3 cm，轉移權重時腋下頂點有的抓到手臂、有的抓到軀幹，手放下時會摺出直線。
    centers：[(x, y, z)]（rest 座標），radius 以內的頂點參與，權重漸變（中心 1 → 邊緣 0）。"""
    me = ob.data; n = len(me.vertices)
    w_reg = []
    for v in me.vertices:
        d = min((v.co - Vector(c)).length for c in centers)
        w_reg.append(max(0.0, 1 - d / radius))
    idx = [i for i in range(n) if w_reg[i] > 0]
    if not idx:
        return 0
    nb = [[] for _ in range(n)]
    for e in me.edges:
        a, b = e.vertices; nb[a].append(b); nb[b].append(a)
    G = [g.name for g in ob.vertex_groups]
    W = [dict() for _ in range(n)]
    for v in me.vertices:
        for g in v.groups:
            W[v.index][G[g.group]] = g.weight
    for _ in range(iters):
        new = {}
        for i in idx:
            if not nb[i]:
                continue
            acc = {}
            for j in nb[i]:
                for k_, w in W[j].items():
                    acc[k_] = acc.get(k_, 0.0) + w / len(nb[i])
            mix = 0.5 * w_reg[i]
            keys = set(acc) | set(W[i])
            d_ = {k_: W[i].get(k_, 0.0) * (1 - mix) + acc.get(k_, 0.0) * mix for k_ in keys}
            tot = sum(d_.values()) or 1.0
            new[i] = {k_: w / tot for k_, w in d_.items() if w / tot > 1e-4}
        for i, d_ in new.items():
            W[i] = d_
    for i in idx:
        for k_ in G:
            g = ob.vertex_groups[k_]
            w = W[i].get(k_, 0.0)
            if w > 1e-4:
                g.add([i], w, "REPLACE")
            else:
                g.remove([i])
    return len(idx)


def _su_weights(ob, legs_to_hips=None, drop_feet=False):
    """從 _SRC 轉移權重；legs_to_hips(co)→0..1：把腿的權重移到骨盆的比例；drop_feet：腳掌/腳趾權重併回小腿"""
    transfer_weights(ob, O[f"{WHO}_SRC"])
    if not (legs_to_hips or drop_feet):
        return
    vg = {g.name: g for g in ob.vertex_groups}
    hips = vg.get("J_Bip_C_Hips") or ob.vertex_groups.new(name="J_Bip_C_Hips")
    for v in ob.data.vertices:
        gs = {ob.vertex_groups[g.group].name: g.weight for g in v.groups}
        if drop_feet:
            for s_ in ("L", "R"):
                moved = sum(gs.pop(f"J_Bip_{s_}_{b}", 0.0) for b in ("Foot", "ToeBase"))
                if moved > 0:
                    gs[f"J_Bip_{s_}_LowerLeg"] = gs.get(f"J_Bip_{s_}_LowerLeg", 0.0) + moved
        if legs_to_hips:
            f = legs_to_hips(v.co)
            if f > 0:
                for name in list(gs):
                    if any(k in name for k in ("UpperLeg", "LowerLeg")):
                        m_ = gs[name] * f; gs[name] -= m_; gs["J_Bip_C_Hips"] = gs.get("J_Bip_C_Hips", 0.0) + m_
        for name in [g.name for g in ob.vertex_groups]:
            g = vg.get(name) or ob.vertex_groups[name]
            w = gs.get(name, 0.0)
            if w > 1e-4:
                g.add([v.index], w, "REPLACE")
            else:
                g.remove([v.index])


# ── 貼片：在某個表面上鋪一片網格（射線從前方 -Y 或後方 +Y 打過去） ──
def _su_hit(bvh, x, z, side=-1, near=None):
    o = Vector((x, side * 1.0, z)); d = Vector((0, -side, 0))
    loc, n, i, dist = bvh.ray_cast(o, d, 2.0)
    if loc is None:
        return None, None
    if side < 0 and loc.y > 0.0:
        return None, None
    if n.y * side < 0:
        n = -n
    return loc, n


def _su_patch(bvh, name, mat, fn, nu, nv, off, side=-1, thick=0.0012):
    """fn(u, v) → (x, z)；u、v ∈ [0,1]。在 bvh 表面外 off 處鋪 nu×nv 格"""
    bm = bmesh.new(); grid = []
    for j in range(nv + 1):
        row = []
        for i in range(nu + 1):
            x, z = fn(i / nu, j / nv)
            loc, n = _su_hit(bvh, x, z, side)
            if loc is None:
                row.append(None); continue
            row.append(bm.verts.new(loc + n * off))
        grid.append(row)
    for j in range(nv):
        for i in range(nu):
            q = (grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i])
            if all(q):
                bm.faces.new(q if side < 0 else q[::-1])
    ob = _su_obj(name, bm, mat)
    for p in ob.data.polygons:
        p.use_smooth = True
    if thick:
        thicken(ob, thick * S)
    return ob


def _su_button(bm, loc, n, r, flat=0.38):
    res = bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=8, radius=1.0)
    rot = n.to_track_quat("Z", "Y").to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation(loc + n * r * flat * 0.6) @ rot @ Matrix.Diagonal((r, r, r * flat, 1)), verts=res["verts"])


def _su_bvh(ob):
    me = ob.data
    return BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons])


def _su_push_out(ob, clear):
    """離皮膚太近（< clear）的頂點沿皮膚法線推到 clear：襯衫、背心不會從外套戳出來"""
    bvhs = [_su_bvh(o_) for o_ in _SU_SKIN()]
    n_ = 0
    for v in ob.data.vertices:
        best = None
        for b in bvhs:
            loc, nn, i_, d = b.find_nearest(v.co)
            if loc is not None and (best is None or d < best[2]):
                best = (loc, nn, d)
        if best is None:
            continue
        loc, nn, d = best
        sd = (v.co - loc).dot(nn)
        if sd < clear:
            v.co = loc + nn * clear; n_ += 1
    ob.data.update()
    return n_


# ── 1. 西裝褲 ──
def suit_pants(mat, p, sec):
    z_w = p.get("pants_waist", 0.927) * S
    hem_f, hem_b = p.get("pants_hem_front", 0.078) * S, p.get("pants_hem_back", 0.057) * S
    crotch = p.get("crotch", 0.785) * S
    knee = A.data.bones["J_Bip_L_LowerLeg"].head_local.z
    e_hip, e_waist, e_leg = p.get("pants_ease_hip", 0.010) * S, p.get("pants_ease_waist", 0.006) * S, p.get("pants_ease_leg", 0.013) * S
    bm = bmesh.new()
    rings = []
    zs = [z_w + 0.02 * S - i * (z_w + 0.02 * S - (crotch - 0.03 * S)) / 8 for i in range(9)]
    for z in zs:
        pts = sec.cut((0, 0, z), (0, 0, 1), lambda q: abs(q.x) < 0.3 * S)
        e = e_waist + (e_hip - e_waist) * _su_ss((z_w - z) / (0.06 * S))
        x1 = max(abs(q.x) for q in pts) + e
        rings.append(_su_ring_xy(bm, z, 0, -x1, x1, min(q.y for q in pts) - e, max(q.y for q in pts) + e, ex=2.4))
    _su_loft(bm, rings)
    # 腿：每 4cm 量一次（膝蓋以下取包絡，越往下略收）
    taper = p.get("pants_taper", 0.35)
    for sx in (1, -1):
        meas = []
        z = crotch + 0.05 * S
        while z > hem_b - 0.03 * S:
            zz = max(z, 0.10 * S)
            pts = sec.cut((0, 0, zz), (0, 0, 1), lambda q: q.x * sx > 0.004)
            meas.append((z, min(q.x * sx for q in pts), max(q.x * sx for q in pts), min(q.y for q in pts), max(q.y for q in pts)))
            z -= 0.04 * S
        lr = []
        env = None
        for z, xa, xb, ya, yb in meas:
            if z < knee:
                env = (xa, xb, ya, yb) if env is None else (min(env[0], xa), max(env[1], xb), min(env[2], ya), max(env[3], yb))
                k = taper * _su_ss((knee - 0.18 * S - z) / (0.3 * S))          # 小腿以下略收
                xa = env[0] + (xa - env[0]) * k; xb = env[1] + (xb - env[1]) * k
                ya = env[2] + (ya - env[2]) * k; yb = env[3] + (yb - env[3]) * k
            x0, x1 = (xa - e_leg) * sx, (xb + e_leg) * sx
            lr.append(_su_ring_xy(bm, z, 0, min(x0, x1), max(x0, x1), ya - e_leg, yb + e_leg, n=40, ex=2.2))
        _su_loft(bm, lr)
    ob = _su_obj("Pants", bm, mat)
    _su_remesh(ob, p.get("voxel", 0.004) * S, 20)
    tilt = (hem_f - hem_b) / (0.2 * S)
    clean_cut(ob, [((0, 0, z_w), (0, 0, 1)), ((0, 0, (hem_f + hem_b) / 2), (0, -tilt, -1))])
    thicken(ob, 0.002 * S)
    _su_weights(ob, drop_feet=True)
    return ob


# ── 2. 襯衫、領子、袖口 ──
def _su_neck_cy(sec):
    pts = sec.cut((0, 0, 1.36 * S), (0, 0, 1), lambda q: abs(q.x) < 0.07 * S)
    return (min(q.y for q in pts) + max(q.y for q in pts)) / 2


def suit_shirt(mat, p, sec):
    zc = p.get("collar_z", 1.333) * S; ncy = _su_neck_cy(sec)
    keep = lambda co: 0.86 * S < co.z < zc + 0.06 * S and abs(co.x) < 0.17 * S
    parts = [shell_piece(src, f"TMP_{WHO}_sh{i}", keep, (0.0035 + 0.0004 * i) * S, mat) for i, src in enumerate(_SU_SKIN())]
    ob = join(parts, P + "Shirt") if len(parts) > 1 else parts[0]
    ob.name = P + "Shirt"
    zt_, sf, sb = p.get("shirt_top", [1.3636, 0.66, 0.41])
    clean_cut(ob, [((0, ncy, zt_ * S), (0, -sf, 1)), ((0, ncy, zt_ * S), (0, -sb, 1)), ((0, 0, 0.87 * S), (0, 0, -1))])
    thicken(ob, 0.002 * S)
    return ob


def suit_collar(mat, p, sec):
    """領台：繞脖子一圈的帶子（前低後高）。半徑＝從脖子中心往外打射線量到的皮膚距離＋off，所以脖子根部前面（上胸）也包得住"""
    ncy = _su_neck_cy(sec)
    bvhs = [_su_bvh(o_) for o_ in _SU_SKIN()]
    zb = [v * S for v in p.get("collar_bottom", [1.302, 1.327, 1.345])]     # 前、側、後
    zt = [v * S for v in p.get("collar_top", [1.318, 1.363, 1.381])]
    off = p.get("collar_off", 0.006) * S
    gap = math.radians(p.get("collar_gap_deg", 10))
    def zf(tab, sn):
        f, sd, b = tab
        return sd + sn * (b - sd) if sn >= 0 else sd + sn * (sd - f)
    N, R = 72, 6
    ths = [-math.pi / 2 + gap + (2 * math.pi - 2 * gap) * i / N for i in range(N + 1)]
    rr = []
    for th in ths:
        sn = math.sin(th); d = Vector((math.cos(th), sn, 0)); col = []
        for j in range(R + 1):
            z = zf(zb, sn) + (zf(zt, sn) - zf(zb, sn)) * j / R
            o = Vector((0, ncy, z)); best = None
            for b in bvhs:
                loc, n_, i_, dist = b.ray_cast(o, d, 0.25)
                if loc is not None and (best is None or dist > best):
                    best = dist
            col.append((z, best))
        rr.append(col)
    for j in range(R + 1):                                     # 沒打到的補鄰居、再沿圓周平滑一次
        vals = [c[j][1] for c in rr]
        known = [v for v in vals if v is not None]
        fill = sum(known) / len(known) if known else 0.05 * S
        vals = [v if v is not None else fill for v in vals]
        sm = [vals[0]] + [(vals[i - 1] + 2 * vals[i] + vals[i + 1]) / 4 for i in range(1, len(vals) - 1)] + [vals[-1]]
        for i, c in enumerate(rr):
            c[j] = (c[j][0], sm[i])
    for c in rr:                                               # 以頂圈（脖子）半徑為準，往下最多放大 12%：底部碰到肩膀、上胸的大半徑不准把領子撐開
        rt = c[R][1]
        for j in range(R + 1):
            c[j] = (c[j][0], min(c[j][1], rt * (1 + 0.12 * (1 - j / R))))
    bm = bmesh.new(); grid = []
    for th, col in zip(ths, rr):
        d = Vector((math.cos(th), math.sin(th), 0))
        grid.append([bm.verts.new(Vector((0, ncy, z)) + d * (r + off)) for z, r in col])
    for a, b in zip(grid, grid[1:]):
        for j in range(R):
            bm.faces.new((a[j], b[j], b[j + 1], a[j + 1]))
    ob = _su_obj("Collar", bm, mat)
    for pl in ob.data.polygons:
        pl.use_smooth = True
    thicken(ob, 0.0018 * S)
    _su_weights(ob)
    return ob


def suit_collar_points(mat, p, shirt):
    """領尖：領結兩側往外下方的兩個小三角，貼在襯衫上"""
    bvhs = [_su_bvh(ob_) for ob_ in _SU_SKIN()]
    bm = bmesh.new()
    for sx in (1, -1):
        vs = []
        for x, z in p.get("collar_points", [[0.006, 1.312], [0.036, 1.306], [0.015, 1.283]]):
            hits = [h for h in (_su_hit(b, x * S * sx, z * S) for b in bvhs) if h[0] is not None]
            if not hits:
                break
            loc, nn = min(hits, key=lambda h: h[0].y)
            vs.append(bm.verts.new(loc + nn * p.get("collar_point_off", 0.0085) * S))
        if len(vs) == 3:
            bm.faces.new(vs if sx > 0 else vs[::-1])
    ob = _su_obj("CollarPoints", bm, mat)
    thicken(ob, 0.0015 * S)
    _su_weights(ob)
    return ob


def suit_cuffs(mat, p, sec):
    x0, x1 = p.get("cuff_x0", 0.49) * S, p.get("cuff_x1", 0.520) * S
    e = p.get("cuff_ease", 0.006) * S
    bm = bmesh.new()
    for sx in (1, -1):
        rings = []
        for i in range(5):
            x = x0 + (x1 - x0) * i / 4
            pts = sec.cut((x * sx, 0, 0), (1, 0, 0), lambda q: q.z > 1.2 * S)
            ya, yb = min(q.y for q in pts), max(q.y for q in pts); za, zb = min(q.z for q in pts), max(q.z for q in pts)
            rings.append(_su_ring_yz(bm, x * sx, (ya + yb) / 2, (za + zb) / 2, (yb - ya) / 2 + e, (zb - za) / 2 + e))
        _su_loft(bm, rings, cap=False)
    ob = _su_obj("Cuffs", bm, mat)
    for pl in ob.data.polygons:
        pl.use_smooth = True
    thicken(ob, 0.0015 * S)
    _su_weights(ob)
    return ob


# ── 3. 背心 ──
def suit_vest(mat, p, sec):
    hem_side, hem_pt, notch = p.get("vest_hem_side", 0.886) * S, p.get("vest_hem_point", 0.843) * S, p.get("vest_notch", 0.870) * S
    pt_x = p.get("vest_point_x", 0.02) * S
    vb, vw, vt = p.get("vest_v_bottom", 1.138) * S, p.get("vest_v_w", 0.051) * S, p.get("vest_v_top", 1.326) * S
    top = p.get("vest_top", 1.322) * S
    def off(co):
        return (p.get("vest_off", 0.008) + p.get("vest_off_hem", 0.009) * _su_ss((0.96 * S - co.z) / (0.08 * S))) * S
    vx = p.get("vest_x", 0.155) * S                    # 背心左右範圍：太寬會包到上臂（男性肩膀寬），舉手時從外套露出
    ah = p.get("vest_armhole")                         # [中心 x, 中心 z, 半寬, 半高]：袖孔橢圓（男性上臂根部被補丁包進來，手放下會變成短袖）
    def keep(co):
        if not (hem_pt - 0.02 * S < co.z < top + 0.05 * S and abs(co.x) < vx):
            return False
        return not (ah and ((abs(co.x) - ah[0] * S) / (ah[2] * S)) ** 2 + ((co.z - ah[1] * S) / (ah[3] * S)) ** 2 < 1)
    parts = [shell_piece(src, f"TMP_{WHO}_v{i}", keep, (lambda co, i=i: off(co) + 0.0005 * i * S), mat) for i, src in enumerate(_SU_SKIN())]
    ob = join(parts, P + "Vest") if len(parts) > 1 else parts[0]
    ob.name = P + "Vest"
    clean_cut(ob, [((0, 0, top), (0, 0.6, 1))])
    side_x = 0.17 * S
    def hem_z(x):
        ax = abs(x)
        if ax < pt_x:
            return notch + (hem_pt - notch) * ax / pt_x
        return hem_pt + (hem_side - hem_pt) * min(1.0, (ax - pt_x) / (side_x - pt_x))
    def v_w(z):
        return vw * (z - vb) / (vt - vb)
    lines = []
    for sx in (1, -1):
        lines += [((0, 0, notch), (sx * pt_x, 0, hem_pt)), ((sx * pt_x, 0, hem_pt), (sx * side_x, 0, hem_side)),
                  ((0, 0, vb), (sx * vw, 0, vt))]
    lines.append(((-1, 0, hem_side), (1, 0, hem_side)))
    def kill(c, n):
        front = c.y < p.get("vest_front_y", -0.02) * S     # 前後分界：男性脖子前緣比較後面，預設值會讓 V 領在喉嚨前留一圈
        if front and c.z < hem_z(c.x):
            return True
        if not front and c.z < hem_side:
            return True
        if front and c.z > vb and abs(c.x) < v_w(c.z):
            return True
        return False
    _su_cut_lines(ob, lines, kill)
    thicken(ob, 0.0025 * S)
    # 扣子
    bvh = _su_bvh(ob); bm = bmesh.new()
    for z in p.get("vest_buttons", [1.106, 1.037, 0.968, 0.900]):
        loc, n = _su_hit(bvh, 0.0, z * S)
        if loc is not None:
            _su_button(bm, loc + n * 0.0025 * S, n, 0.0062 * S)
    btn = _su_obj("VestButtons", bm, M_SU["button"])
    for pl in btn.data.polygons:
        pl.use_smooth = True
    _su_weights(btn)
    return ob


# ── 4. 外套 ──
def suit_jacket(mat, p, sec):
    z_hem = p.get("jacket_hem", 0.767) * S
    ex_ = p.get("jacket_ease_side", 0.028) * S; ef = p.get("jacket_ease_front", 0.030) * S; eb = p.get("jacket_ease_back", 0.022) * S
    chest_min = p.get("jacket_chest_min", 0.152) * S; waist_min = p.get("jacket_waist_min", 0.146) * S
    z_arm = 1.225 * S                          # 腋下（T 姿勢手臂下緣以下才量得到純軀幹）
    zs = []
    z = z_hem - 0.03 * S
    while z < z_arm:
        zs.append(z); z += 0.03 * S
    zs.append(z_arm)
    secs = []
    for z in zs:
        pts = sec.cut((0, 0, z), (0, 0, 1), lambda q: abs(q.x) < 0.3 * S)
        a = max(abs(q.x) for q in pts) + ex_
        lo = waist_min + (chest_min - waist_min) * _su_ss((z - 1.04 * S) / (0.12 * S))   # 胸口撐寬、腰身微收
        secs.append([z, max(a, lo), min(q.y for q in pts) - ef, max(q.y for q in pts) + eb])
    for _ in range(2):                         # 1-2-1 平滑
        secs = [secs[0]] + [[s1[0]] + [(s0[k] + 2 * s1[k] + s2[k]) / 4 for k in (1, 2, 3)] for s0, s1, s2 in zip(secs, secs[1:], secs[2:])] + [secs[-1]]
    # 腋下以上：收到脖子（領子）
    ncy = _su_neck_cy(sec)
    nk = sec.cut((0, 0, 1.36 * S), (0, 0, 1), lambda q: abs(q.x) < 0.07 * S)
    ncy = (min(q.y for q in nk) + max(q.y for q in nk)) / 2
    na, nb = max(abs(q.x) for q in nk), (max(q.y for q in nk) - min(q.y for q in nk)) / 2
    ce = p.get("jacket_collar_ease", 0.020) * S
    up = []
    for zb_ in p.get("jacket_up_z", [1.25, 1.28, 1.31, 1.34, 1.37, 1.42]):
        z = zb_ * S
        pts = sec.cut((0, 0, z), (0, 0, 1), lambda q: abs(q.x) < p.get("jacket_up_xlim", 0.124) * S)
        if len(pts) < 6:
            up.append((z,) + up[-1][1:]); continue
        up.append((z, max(abs(q.x) for q in pts) + ce, min(q.y for q in pts) - ce, max(q.y for q in pts) + ce))
    bm = bmesh.new()
    rings = [_su_ring_xy(bm, z, 0, -a, a, yf, yb, n=56, ex=p.get("jacket_ex", 2.8)) for z, a, yf, yb in secs]
    rings += [_su_ring_xy(bm, z, 0, -a, a, yf, yb, n=56, ex=2.4) for z, a, yf, yb in up]
    _su_loft(bm, rings)
    # 袖管：沿 T 姿勢手臂，截面量出來＋放鬆量；肩膀那頭放大（墊肩）
    es = p.get("sleeve_ease", 0.014) * S; x_end = p.get("sleeve_end", 0.507) * S
    for sx in (1, -1):
        rr = []
        xs = [0.18 * S + (x_end + 0.02 * S - 0.18 * S) * i / 12 for i in range(13)]
        meas = []
        for x in xs:
            pts = sec.cut((x * sx, 0, 0), (1, 0, 0), lambda q: q.z > 1.17 * S)
            ya, yb = min(q.y for q in pts), max(q.y for q in pts); za, zb = min(q.z for q in pts), max(q.z for q in pts)
            meas.append((x, (ya + yb) / 2, (za + zb) / 2, (yb - ya) / 2, (zb - za) / 2))
        x0, cy0, cz0, ry0, rz0 = meas[0]
        # 靠脖子那段不墊高（斜方肌上方要讓外套領口躺下去），墊肩只在肩點
        grow = p.get("shoulder_grow", [[0.06, 1.12, 0.0, 0.0], [0.10, 1.15, 0.003, 0.5], [0.14, 1.15, 0.006, 1.0]])
        pad = p.get("shoulder_pad", 0.008) * S
        for x, k, dz, pk in grow:
            rr.append(_su_ring_yz(bm, x * S * sx, cy0, cz0 + dz * S + pad * 0.5 * pk, ry0 * k + es, rz0 * k + es + pad * 0.5 * pk))
        pad = p.get("shoulder_pad", 0.008) * S
        for x, cy, cz, ry, rz in meas:
            k_ = 1 - _su_ss((x - 0.22 * S) / (0.10 * S))
            rr.append(_su_ring_yz(bm, x * sx, cy, cz + pad * 0.5 * k_, max(ry, 0.026 * S) + es, max(rz, 0.024 * S) + es + pad * 0.5 * k_))
        _su_loft(bm, rr)
    ob = _su_obj("Jacket", bm, mat)
    _su_remesh(ob, p.get("voxel", 0.004) * S, p.get("jacket_smooth", 22))
    print("jacket push-out", _su_push_out(ob, p.get("jacket_clear", 0.009) * S))
    if p.get("jacket_smooth_after", 0):                 # 推開後再順一次：推開會在腋下、肩膀留下小凹痕，輪廓線會把凹痕描成深色碎線
        s2 = ob.modifiers.new("Smooth2", "LAPLACIANSMOOTH"); s2.iterations = p["jacket_smooth_after"]
        s2.lambda_factor = 0.5; s2.use_volume_preserve = True
        _su_apply_all(ob)
    # 切：下襬、袖口、領口（後高前低）
    clean_cut(ob, [((0, 0, z_hem), (0, 0, -1)), ((x_end, 0, 0), (1, 0, 0)), ((-x_end, 0, 0), (-1, 0, 0)),
                   ((0, 0, p.get("jacket_top_max", 1.378) * S), (0, 0, 1))])          # loft 頂端封口（在頭裡）一律切掉
    # 領口：前、後兩個斜面，但只切脖子周圍（離脖子中心 jacket_collar_r 以內）——無限大的斜面會把胸口、肩膀的外套一起切掉
    z_col, kf, kb = p.get("jacket_collar", [1.348, 0.5, 0.3])
    z_col *= S; Rc = p.get("jacket_collar_r", 0.11) * S
    planes = [(Vector((0, ncy, z_col)), Vector((0, -kf, 1)).normalized()), (Vector((0, ncy, z_col)), Vector((0, -kb, 1)).normalized())]
    bm = bmesh.new(); bm.from_mesh(ob.data)
    for co, n in planes:
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6, plane_co=co, plane_no=n)
    bm.normal_update()
    nz_max = p.get("jacket_collar_nz", 0.8)            # 面朝上的（肩膀頂端）不切，只切朝外的領口那圈
    def _above(f):
        c = f.calc_center_median()
        r_ = math.hypot(c.x, c.y - ncy)
        if r_ >= Rc or not any((c - co).dot(n) > 0 for co, n in planes):
            return False
        return r_ < p.get("jacket_collar_r_inner", 0.085) * S or abs(f.normal.z) < nz_max
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if _above(f)], context="FACES")
    bm.to_mesh(ob.data); bm.free()
    # 前襟敞開：開口半寬 w(z)，下擺往外圓弧
    z_brk, w_hem = p.get("break_z", 1.056) * S, p.get("open_w_hem", 0.064) * S
    tab = sorted((z * S, w * S) for z, w in p.get("open_w", [[1.056, 0.0284], [1.212, 0.0303], [1.303, 0.044], [1.6, 0.044]]))
    w_brk = _su_lerp_tab(tab, z_brk)[0]
    def w_of(z):
        if z >= z_brk:
            return _su_lerp_tab(tab, z)[0]
        u = (z_brk - z) / (z_brk - z_hem); return w_brk + (w_hem - w_brk) * u * u
    zz = sorted(set([z for z, _ in tab if z > z_brk] + [z_brk - (z_brk - z_hem) * i / 6 for i in range(7)]), reverse=True)
    pts = [(w_of(z), z) for z in zz]
    lines = []
    for sx in (1, -1):
        lines += [((sx * a0, 0, b0), (sx * a1, 0, b1)) for (a0, b0), (a1, b1) in zip(pts, pts[1:])]
    oy = p.get("open_y", -0.03) * S                  # 前襟開口只刪 y < oy 的面（男性脖子前緣比較後面，預設 -0.03 會在喉嚨前留一條布帶）
    _su_cut_lines(ob, lines, lambda c, n: c.y < oy and abs(c.x) < w_of(c.z) and c.z > z_hem - 0.01 * S)
    jb = _su_bvh(ob)
    thicken(ob, 0.003 * S)
    _su_weights(ob, legs_to_hips=lambda co: 0.75 * _su_ss((0.90 * S - co.z) / (0.08 * S)))
    ap = p.get("armpit_smooth")                        # [x, y, z, 半徑, 次數]（新娘座標）
    if ap:
        cs = [(sx * ap[0] * S, ap[1] * S, ap[2] * S) for sx in (1, -1)]
        print("armpit smooth", _su_smooth_weights(ob, cs, ap[3] * S, int(ap[4])))
    return ob, jb, w_of


def suit_lapels(mat, p, jb, w_of):
    """劍領：翻領（開口邊往外的三角，下端在 break、上端到缺口）＋上領（缺口以上，繞到脖子側）"""
    z_brk, z_n = p.get("break_z", 1.056) * S, p.get("notch_z", 1.258) * S
    lw = p.get("lapel_w", 0.055) * S; cw = p.get("collar_w", 0.028) * S
    z_top = p.get("lapel_top", 1.300) * S
    out = []
    for sx in (1, -1):
        def lapel(u, v, sx=sx):
            z = z_brk + (z_n - z_brk) * v
            w = w_of(z) + 0.0015 * S
            width = lw * v ** 0.9 + 0.003 * S
            z += 0.016 * S * v ** 3 * u                 # 外角往上翹（缺口的下緣）
            return sx * (w + width * u), z
        out.append(_su_patch(jb, f"Lapel{'L' if sx > 0 else 'R'}", mat, lapel, 4, 14, 0.0028 * S))
        def upper(u, v, sx=sx):
            z = z_n + 0.012 * S + (z_top - z_n - 0.012 * S) * v
            w = w_of(z) + 0.0015 * S
            return sx * (w + (cw * (1 - 0.35 * v)) * u + 0.004 * S * v), z
        out.append(_su_patch(jb, f"UpperCollar{'L' if sx > 0 else 'R'}", mat, upper, 3, 6, 0.0026 * S))
    for o in out:
        _su_weights(o)
    return out


def suit_pockets(mat, p, jb):
    out = []
    cx, cz = p.get("chest_pocket", [0.106, 1.177]); w, h = p.get("chest_pocket_size", [0.062, 0.014])
    out.append(_su_patch(jb, "ChestPocket", mat, lambda u, v: ((cx - w / 2 + w * u) * S, (cz - h / 2 + h * v + 0.006 * (u - 0.5)) * S), 4, 1, 0.0018 * S))
    fx, fz = p.get("flap_pocket", [0.115, 0.945]); fw, fh = p.get("flap_pocket_size", [0.062, 0.022])
    for sx in (1, -1):
        out.append(_su_patch(jb, f"Flap{'L' if sx > 0 else 'R'}", mat,
                             lambda u, v, sx=sx: (sx * (fx - fw / 2 + fw * u) * S, (fz - fh / 2 + fh * v) * S), 5, 2, 0.002 * S))
    for o in out:
        _su_weights(o)
    return out


def suit_jacket_buttons(p, jb, w_of):
    bm = bmesh.new()
    z_brk = p.get("break_z", 1.056) * S
    loc, n = _su_hit(jb, -(w_of(z_brk) + 0.016 * S), z_brk - 0.004 * S)      # 外套前襟一顆（穿的人右手邊）
    if loc is not None:
        _su_button(bm, loc + n * 0.003 * S, n, 0.0072 * S)
    x_end = p.get("sleeve_end", 0.507) * S
    for sx in (1, -1):                                                        # 袖扣 4 顆（袖子後側）
        for i in range(4):
            x = (x_end - 0.016 * S - 0.0115 * S * i) * sx
            o = Vector((x, 1.0, A.data.bones["J_Bip_L_Hand"].head_local.z - 0.006 * S)); d = Vector((0, -1, 0))
            loc, nn, idx, dist = jb.ray_cast(o, d, 2.0)
            if loc is None:
                continue
            if nn.y < 0:
                nn = -nn
            _su_button(bm, loc + nn * 0.0028 * S, nn, 0.0036 * S)
    ob = _su_obj("JacketButtons", bm, M_SU["button"])
    for pl in ob.data.polygons:
        pl.use_smooth = True
    _su_weights(ob)
    return ob


# ── 5. 領結 ──
def suit_bowtie(mat, p, sec):
    zc = p.get("bowtie_z", 1.300) * S
    W, H, D = p.get("bowtie_w", 0.044) * S, p.get("bowtie_h", 0.015) * S, p.get("bowtie_d", 0.007) * S
    yf = min(min(q.y for q in sec.cut((0, 0, zc + dz * H), (0, 0, 1), lambda q: abs(q.x) < W)) for dz in (-1, 0, 1))
    c = Vector((0, yf - p.get("bowtie_gap", 0.017) * S, zc))
    bm = bmesh.new()
    for sx in (1, -1):
        rings = []
        N = 10
        for i in range(N + 1):
            u = i / N
            x = sx * (0.004 * S + u * W)
            h = H * (0.42 + 0.58 * math.sin(min(1.0, u * 1.25) * math.pi / 2)) * (1 - 0.35 * max(0.0, u - 0.85) / 0.15)
            dd = D * (0.7 + 0.3 * math.sin(u * math.pi))
            ring = []
            for k in range(16):
                t = 2 * math.pi * k / 16
                zz = h * math.sin(t); dip = -0.0025 * S * math.sin(u * math.pi) * (1 if zz > 0 else -1)    # 上下緣中間微凹（蝴蝶結形）
                ring.append(bm.verts.new(c + Vector((x, dd * math.cos(t) + 0.004 * S * u * u, zz + dip))))
            rings.append(ring)
        _su_loft(bm, rings)
    res = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=1.0)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(c + Vector((0, -0.002 * S, 0))) @ Matrix.Diagonal((0.0075 * S, 0.0075 * S, H * 0.62, 1)), verts=res["verts"])
    ob = _su_obj("BowTie", bm, mat)
    for pl in ob.data.polygons:
        pl.use_smooth = True
    ob.parent = A
    for b, w in (("J_Bip_C_Neck", 0.6), ("J_Bip_C_UpperChest", 0.4)):
        g = ob.vertex_groups.new(name=b); g.add(list(range(len(ob.data.vertices))), w, "REPLACE")
    ob.modifiers.new("Armature", "ARMATURE").object = A
    return ob


def _su_outline(spec, names):
    ol = spec.get("suit", {}).get("outline")
    if not ol:
        return
    for n in names:
        m = bpy.data.materials.get(P + n)
        if not m:
            continue
        e = m.vrm_addon_extension.mtoon1.extensions.vrmc_materials_mtoon
        ids = [i.identifier for i in e.bl_rna.properties["outline_width_mode"].enum_items]
        mode = next((i for i in ids if i.lower().startswith("world")), ids[-1])
        e.outline_color_factor = tuple(ol["color"]); e.outline_lighting_mix_factor = ol.get("mix", 0.5)
        e.outline_width_factor = ol["width"] * S; e.outline_width_mode = mode


def _su_collar_outline(p):
    """襯衫領子、領尖單獨一個材質，加淺灰輪廓線：白領尖疊在白襯衫上，沒有輪廓線就完全分不出來"""
    ol = p.get("collar_outline")
    m = bpy.data.materials.get(P + "CollarMat")
    if not ol or not m:
        return
    e = m.vrm_addon_extension.mtoon1.extensions.vrmc_materials_mtoon
    ids = [i.identifier for i in e.bl_rna.properties["outline_width_mode"].enum_items]
    e.outline_width_mode = next((i for i in ids if i.lower().startswith("world")), ids[-1])
    e.outline_color_factor = tuple(ol["color"]); e.outline_lighting_mix_factor = ol.get("mix", 0.5)
    e.outline_width_factor = ol["width"] * S


def build_extra(M, spec):
    global M_SU
    p = _su_p(spec)
    mk = lambda name, key, d, ds: mtoon(P + name, *_su_col(spec, key, d, ds))
    M_SU = dict(
        jacket=mk("JacketMat", "suit", (0.68, 0.535, 0.40), (0.41, 0.29, 0.21)),
        lapel=mk("LapelMat", "lapel", (0.70, 0.56, 0.42), (0.43, 0.31, 0.23)),
        vest=mk("VestMat", "vest", (0.66, 0.52, 0.39), (0.40, 0.28, 0.20)),
        pants=mk("PantsMat", "pants", (0.66, 0.52, 0.39), (0.40, 0.28, 0.20)),
        pocket=mk("PocketMat", "pocket", (0.60, 0.46, 0.34), (0.36, 0.25, 0.18)),
        shirt=mk("ShirtMat", "shirt", (0.93, 0.93, 0.93), (0.70, 0.72, 0.80)),
        bowtie=mk("BowTieMat", "bowtie", (0.012, 0.03, 0.097), (0.005, 0.012, 0.045)),
        button=mk("ButtonMat", "button", (0.06, 0.04, 0.028), (0.03, 0.02, 0.014)),
        collar=mk("CollarMat", "collar", (0.98, 0.98, 0.98), (0.78, 0.80, 0.86)),   # 領子比襯衫亮：白領尖疊在白襯衫上才分得出來
    )
    _su_collar_outline(p)
    sec = _SuSection(_SU_SKIN())
    try:
        suit_pants(M_SU["pants"], p, sec)
        sh = suit_shirt(M_SU["shirt"], p, sec)
        suit_collar(M_SU["collar"], p, sec)
        suit_collar_points(M_SU["collar"], p, sh)
        suit_cuffs(M_SU["shirt"], p, sec)
        suit_vest(M_SU["vest"], p, sec)
        jk, jb, w_of = suit_jacket(M_SU["jacket"], p, sec)
        suit_lapels(M_SU["lapel"], p, jb, w_of)
        suit_pockets(M_SU["pocket"], p, jb)
        suit_jacket_buttons(p, jb, w_of)
        suit_bowtie(M_SU["bowtie"], p, sec)
    finally:
        sec.free()
    _su_outline(spec, ["JacketMat", "LapelMat", "VestMat", "PantsMat", "PocketMat"])
