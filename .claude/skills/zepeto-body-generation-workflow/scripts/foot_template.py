# 腳的固定模板（手腳研究方案 A 第 4 步）。
# 2026-10-14 v2：照 ZEPETO 官方基本身體重做（研究頁 https://claude.ai/artifact/Cuefy2mtUSjs87pzmnpBS8；使用者：「與該風格不符合」「還有腳趾雕刻」）。
#   v1（13.6 cm、一塊趾塊壓四道淺溝）太短、腳尖收成一點、看不出腳趾。官方的腳：
#   · 腳長≈身高 17%，小腿站在腳的後 3 成，腳背是一條很長很緩的斜線，腳尖圓厚，腳跟圓、往後凸出小腿約 5%
#   · 五根分開雕的圓腳趾：上面、前面有分界，大拇趾最大（約 1.5 倍寬）、往小趾一根比一根小、短、矮，排成弧線；沒有趾甲
#   · 一根腳趾骨（官方 _toes，我們 ToeBase），五根一起彎
# 做法同 hand_template：低面數籠子 → 細分 2 次直接用，不經體素、不減面，同一副骨架永遠是同一隻腳。
# 籠子：
#   · 腳＝一條橫的管子（腳跟 → 腳趾根 9 圈），每圈 22 點：腳背 10（內 → 外，照五根腳趾的左右邊排）、外側 1、腳底 10（外 → 內）、內側 1
#   · 腳跟那圈用 9×2 格子封口；腳趾根那圈不封，五根腳趾從那裡擠出來（每根 3 圈＋收口；最內、最外那根多帶一個側邊點），腳趾之間留一條很窄的縫
#   · 小腿 3 圈從上面接到腳背後段挖的洞（第 2、3 圈之間、腳背第 1～8 欄）
# 權重寫在籠子點（TPL_<骨頭>），細分時內插；body_build 綁完自動權重後蓋回。
# 接口：小腿那圈開口（16 → 64 點），點屬性 foot_ring 1～64、foot_tpl＝1。
import bpy, bmesh, math
from mathutils import Vector

# 五根腳趾（內 → 外）：(寬 ×u, 長 ×大拇趾長, 高 ×大拇趾高)
TOES = ((1.45, 1.00, 1.00), (1.00, 0.96, 0.88), (0.95, 0.86, 0.80), (0.88, 0.74, 0.73), (0.80, 0.62, 0.66))


def build(L, s, sg, fl_ring=0.70, foot_len=0.23, heel_y=0.042, legc=0.004, opt=None):
    o = dict(SHR_X=0.92, SHR_Y=0.91, BALLW=0.385, TOEL=0.13, TOEH=0.13, GAP=0.05, ARCH=0.04, MED=0.53, TW=1.06)
    o.update(opt or {})
    J = lambda n: L[f"J_Bip_{s}_{n}"]
    kn, an = J("LowerLeg")[0], J("Foot")[0]
    FL = foot_len; tip = heel_y - FL
    Y = lambda sf: tip + sf * FL                               # 離腳尖 sf 個腳長的 y
    hx = an.x; LAT = sg                                        # 外側＝+x（左腳）／−x（右腳）
    bone = lambda n: f"J_Bip_{s}_{n}"
    LL, FT, TB = bone("LowerLeg"), bone("Foot"), bone("ToeBase")
    bm = bmesh.new()
    W = {}

    def V(p, w):
        v = bm.verts.new(p); W[v] = dict(w); return v

    def F(vs):
        return bm.faces.new(vs)

    # 腳背 10 欄的位置（0＝內側邊、1＝外側邊）：腳趾那段照五根腳趾的左右邊排、中間留窄縫；往腳跟漸變成平均分布
    tw = [t[0] for t in TOES]; tot = sum(tw) + 4 * o["GAP"]
    lay_toe, x_ = [], 0.0
    for i, w in enumerate(tw):
        lay_toe += [x_ / tot, (x_ + w) / tot]; x_ += w + o["GAP"]
    lay_even = [c / 9 for c in range(10)]

    def layout(sf):
        b = max(0.0, min(1.0, (0.52 - sf) / (0.52 - 0.36)))  # 離腳尖 36% 以前全用腳趾排法、52% 以後平均
        return [lay_even[c] + (lay_toe[c] - lay_even[c]) * b for c in range(10)]

    toe_h = [o["TOEH"] * t[2] for t in TOES]
    # 站點：(離腳尖幾成, 寬 ÷腳長, 腳背高 ÷腳長（None＝照腳趾高）, 腳底外側高 ÷腳長, 足弓 ÷腳長, 權重)；腳底 0＝貼地（2026-10-14 原本 0.004 L，整隻腳浮 1 mm、腳跟浮 3 mm）
    ST = [
        (0.985, 0.20, 0.22, 0.045, 0.0, {FT: 1.0}),                       # 腳跟後緣（之後封口）
        (0.93, 0.25, 0.30, 0.0, 0.0, {FT: 0.6, LL: 0.4}),               # ── 小腿接在這圈和下一圈之間（腳背第 1～8 欄挖洞）
        (0.62, 0.29, 0.29, 0.0, o["ARCH"], {FT: 0.7, LL: 0.3}),
        (0.52, 0.32, 0.25, 0.0, o["ARCH"], {FT: 1.0}),
        (0.42, 0.355, 0.205, 0.0, o["ARCH"] * 0.6, {FT: 1.0}),
        (0.36, o["BALLW"] - 0.005, 0.185, 0.0, o["ARCH"] * 0.2, {FT: 0.85, TB: 0.15}),  # 腳掌（最寬）
        (0.30, o["BALLW"], 0.168, 0.0, 0.0, {FT: 0.5, TB: 0.5}),          # 腳趾關節（離腳尖 31%）
        (0.21, o["BALLW"], 0.150, 0.0, 0.0, {TB: 0.8, FT: 0.2}),
        (o["TOEL"], o["BALLW"], None, 0.0, 0.0, {TB: 0.85, FT: 0.15}),    # 腳趾根（五根腳趾從這圈擠出）
    ]
    loops = []
    for sf, wf, top, bot, arch, w in ST:
        y = Y(sf); Wd = wf * FL; lay = layout(sf)
        xmed = hx - LAT * Wd * o["MED"]
        X = lambda c: xmed + LAT * lay[c] * Wd
        # 小腿和腳之間的過渡權重只給上半圈：腳底、腳跟下半 100% 跟腳走（不然轉腳踝時腳底會被小腿拖著）
        wl_ = (lambda z, ht: w if z > 0.45 * ht else {FT: 1.0}) if LL in w else (lambda z, ht: w)
        if top is None:
            th = [toe_h[c // 2] * FL for c in range(10)]
        else:
            th = [top * FL * (1 - 0.12 * (2 * (c / 9) - 1) ** 2 - 0.14 * (c / 9)) for c in range(10)]   # 中間拱、外側略低
        ht = max(th)
        tops = [V(Vector((X(c), y, th[c])), wl_(th[c], ht)) for c in range(10)]
        lat = V(Vector((X(9) + LAT * 0.003, y, 0.45 * th[9])), wl_(0.45 * th[9], ht))
        zb = lambda c: bot * FL + arch * FL * max(0.0, 1 - c / 4.5) ** 2   # 內側足弓抬高
        bots = [V(Vector((X(c), y, zb(c))), wl_(0, ht)) for c in range(9, -1, -1)]
        med = V(Vector((X(0) - LAT * 0.003, y, max(0.45 * th[0], zb(0) + 0.004))), wl_(0, ht))
        loops.append(tops + [lat] + bots + [med])              # 10＋1＋10＋1＝22
    n = 22
    HOLE = (1, range(1, 8))                                    # 第 1、2 圈之間、腳背第 1～8 欄（面 1～7）
    for i in range(len(loops) - 1):
        A, Bq = loops[i], loops[i + 1]
        for k in range(n):
            if i == HOLE[0] and k in HOLE[1]:
                continue
            F([A[k], A[(k + 1) % n], Bq[(k + 1) % n], Bq[k]])

    # 腳跟封口：9×2 格子（上排＝腳背 10 點、下排＝腳底 10 點、中排＝內側點＋8 個新點＋外側點），往後推圓
    R = loops[0]
    top = R[0:10]; bot = [R[20 - c] for c in range(10)]; med, lat = R[21], R[10]
    mid = [med]
    for c in range(1, 9):
        p = (top[c].co + bot[c].co) / 2 + Vector((0, 0.06 * FL * math.sin(math.pi * c / 9), 0))
        mid.append(V(p, {FT: 1.0}))
    mid.append(lat)
    for c in range(9):
        F([top[c], top[c + 1], mid[c + 1], mid[c]])
        F([mid[c], mid[c + 1], bot[c + 1], bot[c]])

    # ── 腳趾：從腳趾根那圈擠出五根，腳趾之間的窄縫封起來 ──
    Rt = loops[-1]
    T_ = lambda c: Rt[c]; B_ = lambda c: Rt[20 - c]
    for i in range(4):                                         # 腳趾之間的縫
        F([T_(2 * i + 1), T_(2 * i + 2), B_(2 * i + 2), B_(2 * i + 1)])
    y0 = Y(o["TOEL"])
    for i, (wu, lf, hf) in enumerate(TOES):
        poly = [T_(2 * i), T_(2 * i + 1)] + ([Rt[10]] if i == 4 else []) + [B_(2 * i + 1), B_(2 * i)] + ([Rt[21]] if i == 0 else [])
        xc = (T_(2 * i).co.x + T_(2 * i + 1).co.x) / 2
        zb0 = min(v.co.z for v in poly); zt0 = max(v.co.z for v in poly)
        ln = o["TOEL"] * FL * lf
        prev = poly
        # (沿腳趾幾成, 寬度比, 頂高比, 底高 ÷腳長)：前段頂往下收、底往上翹，腳尖圓
        # 寬度比略大於 1：細分會把每根腳趾收圓、收窄，不放寬的話腳趾之間會裂出看得到地板的縫（2026-10-14 第一版像耙子）
        for t, ws, hs, zbf in ((0.33, o["TW"], 0.97, 0.0), (0.66, o["TW"] * 0.98, 0.90, 0.006), (0.92, o["TW"] * 0.86, 0.76, 0.026)):
            zt = zt0 * hs; zb_ = zbf * FL
            ring = [V(Vector((xc + (v.co.x - xc) * ws, y0 - t * ln, zb_ + (v.co.z - zb0) / max(1e-6, zt0 - zb0) * (zt - zb_))), {TB: 1.0}) for v in poly]
            for kk in range(len(poly)):
                F([prev[kk], prev[(kk + 1) % len(poly)], ring[(kk + 1) % len(poly)], ring[kk]])
            prev = ring
        F(prev)                                                 # 腳趾尖收口

    # ── 小腿：開口那圈（16 點，接口環）→ 腳踝最細處 → 往腳背張開 → 接腳背的洞 ──
    A, Bq = loops[HOLE[0]], loops[HOLE[0] + 1]
    hole = [A[c] for c in range(1, 9)] + [Bq[c] for c in range(8, 0, -1)]
    hc = sum((v.co for v in hole), Vector()) / 16
    ang = lambda p: math.atan2(p.y - hc.y, (p.x - hc.x) * LAT) % (2 * math.pi)
    hole.sort(key=lambda v: ang(v.co))
    zr = kn.z + (an.z - kn.z) * fl_ring

    def skin_r(f):                                              # 身體 Skin 的小腿節點（body_build.skin_body）：0.65 (.031,.031)、腳踝 (.025,.026)
        t = (f - 0.65) / 0.35; return (0.031 + (0.025 - 0.031) * t) * o["SHR_X"], (0.031 + (0.026 - 0.031) * t) * o["SHR_Y"]
    # 小腿每圈 16 點平均分角度（不能照洞口的角度：洞口前後長、左右窄，角度擠在前後兩邊，細分後小腿左右只剩 15 mm 寬，2026-10-14 實測）；
    #   起始角對齊洞口，第 k 點接洞口第 k 點
    a_h = [ang(v.co) for v in hole]
    a0 = math.atan2(sum(math.sin(a_h[i] - 2 * math.pi * i / 16) for i in range(16)), sum(math.cos(a_h[i] - 2 * math.pi * i / 16) for i in range(16)))
    angs = [a0 + 2 * math.pi * i / 16 for i in range(16)]
    rings = []
    k = 1 / 0.975
    for z, (rx, ry), cy, w in ((zr, skin_r(fl_ring), legc, {LL: 1.0}),
                               (0.50 * FL, (0.0255, 0.0265), legc, {LL: 1.0}),          # 腳踝最細（官方：高 0.5 腳長、前後 0.23 腳長）
                               (0.40 * FL, (0.026, 0.030), legc - 0.004, {LL: 0.85, FT: 0.15})):   # 往前張開接腳背
        rings.append([V(Vector((hx + LAT * rx * k * math.cos(a), cy + ry * k * math.sin(a), z)), w) for a in angs])
    rings.append(hole)
    for i in range(len(rings) - 1):
        A_, B_q = rings[i], rings[i + 1]
        for kk in range(16):
            F([A_[kk], A_[(kk + 1) % 16], B_q[(kk + 1) % 16], B_q[kk]])

    loose = [v for v in bm.verts if not v.link_faces]
    for v in loose:
        W.pop(v, None)
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(f"FootTpl_{s}"); bm.to_mesh(me)
    ob = bpy.data.objects.new(f"FootTpl_{s}", me); bpy.context.scene.collection.objects.link(ob)
    idx = {v: i for i, v in enumerate(bm.verts)}
    groups = {}
    for v, ws in W.items():
        tot_ = sum(ws.values())
        for b, w in ws.items():
            g = groups.get(b) or ob.vertex_groups.new(name="TPL_" + b); groups[b] = g
            g.add([idx[v]], w / tot_, "REPLACE")
    bm.free()
    sub = ob.modifiers.new("Sub", "SUBSURF"); sub.levels = 2; sub.render_levels = 2; sub.boundary_smooth = "ALL"
    bpy.ops.object.select_all(action="DESELECT"); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=sub.name)
    me = ob.data
    # 開口那圈 → foot_ring 1～N；全部點 foot_tpl＝1
    ec = {}
    for p in me.polygons:
        for e in p.edge_keys:
            ec[e] = ec.get(e, 0) + 1
    bnd = {a for (a, b), c in ec.items() if c == 1} | {b for (a, b), c in ec.items() if c == 1}
    a2 = lambda co: math.atan2(co.y - legc, (co.x - hx) * LAT) % (2 * math.pi)
    ring = sorted(bnd, key=lambda i: a2(me.vertices[i].co))
    at_r = me.attributes.new("foot_ring", "INT", "POINT"); at_t = me.attributes.new("foot_tpl", "INT", "POINT")
    for i in range(len(me.vertices)):
        at_t.data[i].value = 1
    for kk, i in enumerate(ring):
        at_r.data[i].value = kk + 1
    for p in me.polygons:
        p.use_smooth = True
    return ob
