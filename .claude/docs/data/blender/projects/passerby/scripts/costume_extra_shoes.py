# 路人甲黑色綁帶皮鞋＋深色襪子（passerby 專案自訂服裝元件）：costume.json 的 extra_scripts 列出。
# 由 groom 專案的 costume_extra_shoes.py 原樣複製（程式不改）；和新郎的差別全在 costume.json：鞋面、鞋底、鞋帶改黑色，
# 光澤（gloss）改中性灰、輪廓線改黑（新郎是深褐色德比鞋，使用者要求服裝不要重複）。以下是新郎版的原始說明：
#
# 新郎深褐色綁帶皮鞋（德比鞋）＋深色襪子（groom 專案自訂服裝元件）：costume.json 的 extra_scripts 列出。
# 參數在 spec["shoes_leather"]（新娘座標，乘 S）；顏色在 spec["colors"]：shoe／shoe_sole／shoe_lace／socks（各有 _shade）。
#
# 為什麼新做一雙而不是幫 VRoid 球鞋換色：球鞋的白條紋、白色厚鞋底、圓胖鞋頭都畫在網格與貼圖上，換色還是看得出是球鞋。
# 做法：
#   1. 量腳的皮膚（每個 y 站位的左右寬、腳背高度）→ 鞋楦：每站一圈截面＝上半超橢圓鞋面＋下半比鞋面寬一點的鞋底（沿條）。
#      鞋頭比腳尖再長 toe_ext、平面收成杏仁形、微微上翹（toe_spring，腳尖點地時才不會陷地）；
#      後跟是方塊（heel_h），足弓那段鞋底離地（arch_lift）；鞋底、沿條一律深色。
#   2. 鞋口：y_open 以後（往腳跟）截面頂端那一段改成開口，牆頂沿 collar 曲線（後跟高、兩側低、鞋舌前緣高）。
#   3. 鞋帶：鞋背上 4 條橫帶＋兩排鞋眼，貼在鞋面上（射線找表面）。
#   4. 權重從 VRoid 球鞋（<WHO>_Shoes）轉移；鞋底高度和球鞋一樣在 0，所以貼地（pose_lib.sole_points 讀球鞋）照舊。
#   5. 襪子：腳、腳踝、小腿下段的皮膚往外撐 1.5 mm，深色（褲口和鞋口之間走路時露出來的是襪子，不是皮膚）。
# costume.json 的 keep_vroid 不列 Shoes → wear("costume") 會藏起 VRoid 球鞋、wear("base") 再顯示回來。
import bpy, bmesh, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _sh_ss(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def _sh_col(spec, key, d, ds):
    c = spec.get("colors", {})
    return tuple(c.get(key, d)), tuple(c.get(key + "_shade", ds))


def _sh_smooth(vals, passes=2, keep_ends=True):
    for _ in range(passes):
        vals = [vals[0]] + [(a + 2 * b + c) / 4 for a, b, c in zip(vals, vals[1:], vals[2:])] + [vals[-1]]
    return vals


def _sh_foot(sx, p):
    """量一隻腳：回傳每個站位的 (y, cx, a, a_top, zb, zs, zt, zcol, e, t_collar)"""
    m = p.get("margin", 0.004) * S
    body = O[f"{WHO}_Body"]
    pts = [v.co.copy() for v in body.data.vertices if v.co.z < 0.16 * S and v.co.x * sx > 0.015 * S]
    y_ft = min(q.y for q in pts); y_fh = max(q.y for q in pts)
    y_tip = y_ft - p.get("toe_ext", 0.020) * S
    y_heel = y_fh + p.get("heel_ext", 0.008) * S
    toe_y = A.data.bones[f"J_Bip_{'L' if sx > 0 else 'R'}_ToeBase"].head_local.y
    # 鞋口前緣：從腳尖往後掃，腳背皮膚第一次高過 open_z 的位置
    y_open = None
    for k in range(200):
        y = y_ft + (y_fh - y_ft) * k / 199
        sl = [q for q in pts if abs(q.y - y) < 0.006 * S]
        if sl and max(q.z for q in sl) > p.get("open_z", 0.100) * S:
            y_open = y; break
    y_open = y_open if y_open is not None else (y_ft + y_fh) / 2
    L = y_heel - y_tip
    cz = p.get("collar", [[0.0, 0.066], [0.18, 0.058], [0.30, 0.062], [1.0, 0.090]])   # (u＝從後跟到鞋口前緣的比例, z)

    def zcol(y):
        u = (y_heel - y) / max(1e-6, (y_heel - y_open))
        u = max(0.0, min(1.0, u))
        for (u0, z0), (u1, z1) in zip(cz, cz[1:]):
            if u <= u1:
                return (z0 + (z1 - z0) * _sh_ss((u - u0) / (u1 - u0))) * S
        return cz[-1][1] * S

    N = p.get("stations", 44)
    ys = [y_heel + (y_tip - y_heel) * (1 - math.cos(math.pi * i / (N - 1))) / 2 for i in range(N)]
    win = 0.010 * S
    raw = []; slices = []
    for y in ys:
        zc = zcol(y)
        sl = [q for q in pts if abs(q.y - y) < win]
        slices.append(sl)
        low = [q for q in sl if q.z < zc + 0.004 * S] or sl
        if len(low) >= 3:
            x0, x1 = min(q.x for q in low), max(q.x for q in low)
            top = max(q.z for q in sl)
            near = [q for q in sl if abs(q.z - zc) < 0.012 * S]
            at = (max(q.x for q in near) - min(q.x for q in near)) / 2 + m if len(near) >= 3 else None
            raw.append([y, (x0 + x1) / 2, (x1 - x0) / 2 + m, at, top + m])
        else:
            raw.append([y, None, None, None, None])
    # 腳尖以外、腳跟以外：外插（杏仁形鞋頭、圓後跟）
    idx = [i for i, r in enumerate(raw) if r[1] is not None]
    i_first, i_last = idx[0], idx[-1]
    hx, ha, htop = raw[i_first][1], raw[i_first][2], raw[i_first][4]
    tx, ta, ttop = raw[i_last][1], raw[i_last][2], raw[i_last][4]
    for i, r in enumerate(raw):
        y = r[0]
        if i < i_first:                                          # 後跟外
            u = (y - raw[i_first][0]) / max(1e-6, (y_heel - raw[i_first][0]))
            r[1], r[2], r[4] = hx, max(0.004 * S, ha * math.sqrt(max(0.0, 1 - u ** 2))), htop
        elif i > i_last:                                         # 腳尖外：鞋頭
            u = (raw[i_last][0] - y) / max(1e-6, (raw[i_last][0] - y_tip))
            r[1] = tx - p.get("toe_medial", 0.004) * S * sx * u
            r[2] = max(0.003 * S, ta * math.sqrt(max(0.0, 1 - u ** 1.7)))
            r[4] = None
        for j in (3,):
            if r[j] is None:
                r[j] = r[2]
    # 杏仁形：腳趾根部往前，寬度至少照收窄曲線（腳本身太胖時，鞋頭還是看得出收尖）
    cxs = _sh_smooth([r[1] for r in raw], 3)
    As = _sh_smooth([r[2] for r in raw], 2)
    out = []
    sole_h, heel_h = p.get("sole_h", 0.011) * S, p.get("heel_h", 0.026) * S
    heel_len = p.get("heel_len", 0.065) * S
    arch_lift, toe_spring = p.get("arch_lift", 0.006) * S, p.get("toe_spring", 0.007) * S
    tops = []
    for i, r in enumerate(raw):
        y = r[0]
        hf = y_heel - heel_len                                  # 後跟前緣
        # 足弓：後跟前緣往前 1.2 cm 內升到 arch_lift，到腳掌（趾根後 4.5→2 cm）降回 0
        rise = _sh_ss((hf - y) / (0.012 * S))
        fall = _sh_ss((y - (toe_y + 0.020 * S)) / (0.025 * S))
        zb = arch_lift * rise * fall
        zb += toe_spring * _sh_ss((toe_y - 0.02 * S - y) / max(1e-6, (toe_y - 0.02 * S - y_tip))) ** 2
        zs = zb + sole_h + (heel_h - sole_h) * _sh_ss((y - (hf - 0.010 * S)) / (0.010 * S))
        tops.append(r[4])
        out.append([y, cxs[i], As[i], r[3], zb, zs])
    # 鞋面高度：有皮膚的地方照腳背＋余量；鞋頭往前降到鞋底上 toe_h
    toe_h = p.get("toe_h", 0.016) * S
    known = [(i, t) for i, t in enumerate(tops) if t is not None]
    il, tl = known[-1]
    for i in range(len(tops)):
        if tops[i] is None:
            u = (out[il][0] - out[i][0]) / max(1e-6, (out[il][0] - y_tip))
            tops[i] = out[i][5] + toe_h + (tl - out[il][5] - toe_h) * (1 - u ** 1.4)
    tops = _sh_smooth(tops, 2)
    res = []
    mc = p.get("contain_margin", 0.005) * S
    grow = p.get("contain_grow", 1.4)
    for i, ((y, cx, a, at, zb, zs), zt) in enumerate(zip(out, tops)):
        t = _sh_ss((y - (y_open - 0.012 * S)) / (0.012 * S))        # 0＝鞋面（封頂）、1＝鞋口（開口）
        zc = zcol(y)
        e = 2.4 + 0.9 * t
        at = min(at, a)
        # 包住這一站所有腳的皮膚點（＋mc）：封頂的鞋面撐高、撐寬；鞋口的牆撐寬（牆頂、牆底分開算）
        sl = slices[i]
        if sl:
            a0, h0 = a, zt - zs
            if t < 0.999:
                h = max(zt - zs, max(q.z - zs for q in sl) + mc)
                need = a
                for q in sl:
                    dz = max(0.0, q.z - zs)
                    if dz >= h:
                        continue
                    r_ = min(0.95, dz / h)
                    need = max(need, (abs(q.x - cx) + mc) / (1 - r_ ** e) ** (1 / e))
                a = min(need, a0 * grow); zt = zs + h
            if t > 0.001:
                for q in sl:
                    if q.z >= zc:
                        continue
                    s_ = max(0.0, (q.z - zs) / max(1e-6, zc - zs)); d = abs(q.x - cx) + mc
                    if s_ > 0.6:
                        at = max(at, d)
                for q in sl:
                    if q.z >= zc:
                        continue
                    s_ = max(0.0, (q.z - zs) / max(1e-6, zc - zs)); d = abs(q.x - cx) + mc
                    if s_ < 0.95:
                        a = max(a, min(a0 * grow, (d - at * s_ ** 2) / (1 - s_ ** 2)))
                at = min(at, a)
        res.append([y, cx, a, at, zb, zs, zt, zc, e, t])
    # 撐開之後再順一次（只准變大，不然又戳出去）
    for j in (2, 3, 6):
        sm = _sh_smooth([r[j] for r in res], 2)
        for r, v in zip(res, sm):
            r[j] = max(r[j], v)
    return [tuple(r) for r in res], y_open


def _sh_ring(bm, st, p, nu=24, i0=7, nb=6):
    """一圈截面頂點：0..nu 鞋面（右→頂→左），之後是鞋底（左→底→右）。回傳 (verts, kinds)"""
    y, cx, a, at, zb, zs, zt, zc, e, t = st
    w = p.get("welt", 0.0022) * S
    vs, kd = [], []
    for i in range(nu + 1):
        th = math.pi * i / nu
        c, s_ = math.cos(th), math.sin(th)
        # 封頂（鞋面）
        x1 = cx + a * math.copysign(abs(c) ** (2 / e), c); z1 = zs + max(zt - zs, 0.003 * S) * abs(s_) ** (2 / e)
        # 開口（鞋口）：0..i0 右牆、nu-i0..nu 左牆，中間那段橫在牆頂（之後刪掉）
        if i <= i0 or i >= nu - i0:
            sgn = 1 if i <= i0 else -1
            ss = (i if i <= i0 else nu - i) / i0
            x2 = cx + sgn * (a - (a - at) * ss ** 2); z2 = zs + (zc - zs) * ss
        else:
            u = (i - i0) / (nu - 2 * i0)
            x2 = cx + at * (1 - 2 * u); z2 = zc
        vs.append(bm.verts.new((x1 + (x2 - x1) * t, y, z1 + (z2 - z1) * t))); kd.append(0)
    xl, xr = cx - a - w, cx + a + w
    r = min(0.003 * S, (zs - zb) * 0.35)
    for x, z in [(xl, zs), (xl, zb + r)] + [(xl + r + (xr - xl - 2 * r) * k / nb, zb) for k in range(nb + 1)] + [(xr, zb + r), (xr, zs)]:
        vs.append(bm.verts.new((x, y, z))); kd.append(1)
    return vs, kd


def shoes_leather(Ml, Ms, p):
    bm = bmesh.new()
    nu, i0 = 24, 7
    opens = []; kill = []          # ⚠️ 不要用 BMFace.tag 標記：bmesh.ops（例 recalc_face_normals）會改寫 tag，整雙鞋被刪光
    for sx in (1, -1):
        sts, y_open = _sh_foot(sx, p)
        opens.append(y_open)
        rings = [_sh_ring(bm, st, p, nu, i0) for st in sts]
        n = len(rings[0][0])
        for (r0, k0), (r1, k1), s0, s1 in zip(rings, rings[1:], sts, sts[1:]):
            for k in range(n):
                f = bm.faces.new((r0[k], r0[(k + 1) % n], r1[(k + 1) % n], r1[k]))
                sole = k0[k] or k0[(k + 1) % n]
                top_band = i0 <= k < nu - i0
                f.material_index = 1 if sole else 0
                f.smooth = not sole
                if top_band and s0[9] > 0.999 and s1[9] > 0.999:
                    kill.append(f)                               # 鞋口：之後刪
        for rv, kd in (rings[0], rings[-1]):                     # 後跟片、鞋尖封口（後跟片上緣就是鞋口後緣）
            # 鞋面、鞋底各自用一個中心點封口：共用中心的話，鞋底顏色的三角形會拉到鞋面上（後跟頂端一個深色尖角）
            up = [k for k in range(n) if not kd[k]]; lo = [k for k in range(n) if kd[k]]
            for ids, mi in ((up, 0), ([up[-1]] + lo + [up[0]], 1)):   # 鞋底那圈頭尾接回鞋面兩端（沿 zs 的直線）
                c = bm.verts.new(sum((rv[k].co for k in ids), Vector()) / len(ids))
                for a_, b_ in zip(ids, ids[1:] + ids[:1]):
                    f = bm.faces.new((rv[a_], rv[b_], c))
                    f.material_index = mi
                    f.smooth = False
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    name = P + "Shoes"
    if name in O:
        bpy.data.objects.remove(O[name], do_unlink=True)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); A.users_collection[0].objects.link(ob)
    me.materials.append(Ml); me.materials.append(Ms)
    thicken(ob, 0.0012 * S)
    transfer_weights(ob, O[f"{WHO}_Shoes"])
    return ob, opens


def shoes_laces(Mlace, p, shoe, opens):
    """鞋背上 4 條橫帶＋兩排鞋眼（射線從上往下找鞋面）"""
    dg = bpy.context.evaluated_depsgraph_get()
    me = shoe.data
    bvh = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(pl.vertices) for pl in me.polygons])
    bm = bmesh.new()
    n_l = p.get("laces", 4); span = p.get("lace_span", 0.045) * S; half = p.get("lace_w", 0.011) * S
    rr = p.get("lace_r", 0.0016) * S
    for sx, y_open in zip((1, -1), opens):
        # 鞋背中線 x：在 y_open 前方量鞋面最高點
        for li in range(n_l):
            y = y_open - 0.008 * S - span * li / max(1, n_l - 1)
            best = None
            for k in range(41):
                x = sx * (0.04 + 0.08 * k / 40) * S
                hit = bvh.ray_cast(Vector((x, y, 0.3 * S)), Vector((0, 0, -1)), 1.0)
                if hit[0] is not None and (best is None or hit[0].z > best.z):
                    best = hit[0]
            if best is None:
                continue
            cx = best.x
            pts = []
            for sgn in (-1, 1):
                hit = bvh.ray_cast(Vector((cx + sgn * half, y, 0.3 * S)), Vector((0, 0, -1)), 1.0)
                if hit[0] is not None:
                    pts.append(hit[0] + hit[1] * 0.0018 * S)
            if len(pts) != 2:
                continue
            a_, b_ = pts
            d = (b_ - a_); L = d.length; d.normalize()
            up = Vector((0, 0, 1)); side = d.cross(up).normalized()
            # 扁帶：8 段的小方管
            ring = lambda c: [bm.verts.new(c + side * rr * 1.6 * sa + up * rr * 0.6 * ca)
                              for sa, ca in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
            r0 = ring(a_); r1 = ring(b_)
            for k in range(4):
                bm.faces.new((r0[k], r0[(k + 1) % 4], r1[(k + 1) % 4], r1[k]))
            bm.faces.new(r0[::-1]); bm.faces.new(r1)
            for c in (a_, b_):                                    # 鞋眼
                res = bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=rr * 1.5)
                bmesh.ops.translate(bm, verts=res["verts"], vec=c)
    name = P + "ShoeLaces"
    if name in O:
        bpy.data.objects.remove(O[name], do_unlink=True)
    lm = bpy.data.meshes.new(name); bm.to_mesh(lm); bm.free()
    for pl in lm.polygons:
        pl.use_smooth = True
    ob = bpy.data.objects.new(name, lm); A.users_collection[0].objects.link(ob)
    lm.materials.append(Mlace)
    transfer_weights(ob, O[f"{WHO}_Shoes"])
    return ob


def socks(Msock, p):
    top = p.get("sock_top", 0.26) * S
    keep = lambda c: c.z < top and abs(c.x) > 0.012 * S
    ob = shell_piece(O[f"{WHO}_Body"], P + "Socks", keep, p.get("sock_off", 0.0015) * S, Msock)
    return ob


def _sh_gloss(m, p):
    e = m.vrm_addon_extension.mtoon1.extensions.vrmc_materials_mtoon
    g = p.get("gloss", {"color": [0.30, 0.19, 0.12], "power": 4.0, "lift": 0.0, "mix": 0.6})
    e.parametric_rim_color_factor = tuple(g["color"]); e.parametric_rim_fresnel_power_factor = g["power"]
    e.parametric_rim_lift_factor = g["lift"]; e.rim_lighting_mix_factor = g["mix"]


def _sh_outline(m, p):
    ol = p.get("outline")
    if not ol:
        return
    e = m.vrm_addon_extension.mtoon1.extensions.vrmc_materials_mtoon
    ids = [i.identifier for i in e.bl_rna.properties["outline_width_mode"].enum_items]
    e.outline_width_mode = next((i for i in ids if i.lower().startswith("world")), ids[-1])
    e.outline_color_factor = tuple(ol["color"]); e.outline_lighting_mix_factor = ol.get("mix", 0.5)
    e.outline_width_factor = ol["width"] * S


def build_extra(M, spec):
    p = spec.get("shoes_leather", {})
    mk = lambda name, key, d, ds: mtoon(P + name, *_sh_col(spec, key, d, ds))
    Ml = mk("ShoeLeatherMat", "shoe", (0.13, 0.045, 0.018), (0.055, 0.018, 0.008))
    Ms = mk("ShoeSoleMat", "shoe_sole", (0.022, 0.013, 0.009), (0.011, 0.007, 0.005))
    Mlace = mk("ShoeLaceMat", "shoe_lace", (0.035, 0.018, 0.010), (0.018, 0.009, 0.005))
    Msock = mk("SocksMat", "socks", (0.035, 0.030, 0.028), (0.018, 0.015, 0.014))
    _sh_gloss(Ml, p)
    for m in (Ml, Ms):
        _sh_outline(m, p)
    shoe, opens = shoes_leather(Ml, Ms, p)
    shoes_laces(Mlace, p, shoe, opens)
    socks(Msock, p)
