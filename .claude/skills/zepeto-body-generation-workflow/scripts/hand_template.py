# 手的固定模板（手腳研究方案 A 第 1、2 步；2026-10-14 使用者選「照原計畫做 A」）。
# 低面數籠子（前臂半截＋手腕＋手掌＋四指＋拇指，一塊網格）→ 細分 2 次直接用，不經體素、不減面：
#   同一副骨架做出來永遠是同一隻手（身體別處改了也不會變），點數固定。
# 權重寫在籠子的點上（TPL_<骨頭> 點群組），細分時一起內插；body_build 綁完自動權重後再用它蓋掉手的部分。
# 接口：前臂那圈開口（籠子 16 點 → 細分後 64 點），點屬性 hand_ring＝1～64（第 1 點正前方 −Y，從手肘往手看逆時針），
#   身體端照接口環同樣做法（切開 → 拉鍊三角形 → Hermite 過渡）接上。
# 籠子規格（業界做法 [T1][T2][T4]，見 references/research-hands-feet.md 2.2、6.2）：
#   · 手掌一圈 16 點：手背 8 點、手心 8 點，橫向照四根手指的左右邊緣排；最外側兩欄從手腕直走到食指根、小指根（掌緣一條直邊，沒有 L 形轉角）
#   · 手指每圈 4 點（細分後 16 邊）；每個關節 3 圈（關節前、關節、關節後各約半個手指半徑）、每節中段 1 圈、指尖收口
#   · 指縫：指根那排兩根手指之間的面＝指蹼，指蹼深度約 0（使用者不要蹼）
#   · 拇指：從手掌靠手腕的食指側那塊側面擠出 3 節，拇指根肉墊是籠子本身的形狀
import bpy, bmesh, math
from mathutils import Vector, Matrix

FN = ("Index", "Middle", "Ring", "Little")


def _ss(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def build(L, s, sg, HL, FR, TR, fa_ring=0.60, opt=None):
    """→ 細分好（已套用）的網格物件 HandTpl_<s>，世界座標＝骨架 rest 座標。
    L＝bones_layout() 的 {骨頭: (頭, 尾, 父)}；sg＝+1 左手、−1 右手"""
    o = dict(PT=0.105, PB=0.85, KT=0.78, FW=1.12, FH=0.95, KN=0.18, CR=0.08, TH=0.95, SHR=0.906, P1=0.30, P2=0.42, TB=0.70, TP=1.0, T0=0.04, TY=-0.03, TZ=-0.04, JW=0.15, TJ=0.95, KPB=0.95, KB=0.65, TWB=0.25, TW1=0.6, DAR=0.20, PBC=0.6)
    o.update(opt or {})
    J = lambda n: L[f"J_Bip_{s}_{n}"]
    a1, a2 = J("LowerArm")[0], J("Hand")[0]
    U = Vector((sg, 0, 0)); Y = Vector((0, 1, 0)); Z = Vector((0, 0, 1))
    at = lambda u, v, w: a2 + U * u + Y * v + Z * w          # 手的座標：u 沿手、v 橫向（−＝食指側）、w 往手背
    bm = bmesh.new()
    dl = bm.verts.layers.deform.verify()
    W = {}                                                     # 籠子點 → {骨頭: 權重}
    bone = lambda n: f"J_Bip_{s}_{n}"

    def V(p, w):
        v = bm.verts.new(p); W[v] = dict(w); return v

    def F(vs):                                                 # 面的方向最後統一重算（recalc_face_normals）
        return bm.faces.new(vs)

    # ── 手掌橫向欄位（指根那排）──
    roots = [J(f"{f}1")[0] for f in FN]
    PT = o["PT"] * HL; PB = o["PB"]
    a_f = FR * o["FW"] / 0.92                                 # 手指籠子半寬（細分後縮成約 0.92 倍）
    cols = []
    for r in roots:
        cols += [r.y - a2.y - a_f, r.y - a2.y + a_f]
    vmid = sum(cols) / len(cols)
    Ku = [(roots[c // 2].x - a2.x) * sg for c in range(8)]     # 每欄指根在手上的 u（中指、無名指比食指、小指前 1.7 mm）
    K0 = min(Ku)

    # ── 前臂兩圈（橢圓、16 點），半徑＝身體 Skin 半徑 × 體素平滑後的收縮率（實測 0.906），和身體在接口處一樣粗 ──
    fa = (a2 - a1).length
    def skin_r(f):                                             # 身體 Skin 的前臂節點（body_build.skin_body）：0.25 (.032,.029)、0.70 (.025,.021)
        t = (f - 0.25) / 0.45; return (0.032 + (0.025 - 0.032) * t) * o["SHR"], (0.029 + (0.021 - 0.029) * t) * o["SHR"]
    def ell_ring(u, ry, rz, wts):
        k = 1 / 0.975                                          # 16 點一圈細分後的極限曲線約縮 0.975
        top = [V(at(u, -ry * k * math.cos((c + 0.5) * math.pi / 8), rz * k * math.sin((c + 0.5) * math.pi / 8)), wts) for c in range(8)]
        bot = [V(at(u, -ry * k * math.cos((c + 0.5) * math.pi / 8), -rz * k * math.sin((c + 0.5) * math.pi / 8)), wts) for c in range(8)]
        return top, bot
    LA = {bone("LowerArm"): 1.0}
    u0 = -(1 - fa_ring) * fa
    ry0, rz0 = skin_r(fa_ring)
    st = [ell_ring(u0, ry0, rz0, LA)]
    st.append(ell_ring(u0 * 0.45, 0.0215, 0.0175, LA))       # 前臂下段：往手腕變寬扁
    # ── 手腕、手掌（上下兩排）──
    def palm_ring(u_of, wk, tk_top, tk_bot, wts_of):
        top, bot = [], []
        for c in range(8):
            v = vmid + (cols[c] - vmid) * wk
            x2 = ((cols[c] - vmid) / (cols[-1] - vmid)) ** 2
            arch = o["DAR"] * PT * (1 - x2)                    # 手背中間拱起
            u = u_of(c)
            top.append(V(at(u, v, tk_top * PT + arch), wts_of(c, True)))
            # 手心兩側變薄（PBC）：彎起來的小指、食指指尖才不會插進手心（舊手是橢球，兩側本來就薄；2026-10-14 平板手心量到 4.5～5 mm）
            bot.append(V(at(u, v, -tk_bot * PT * PB * (1 - o["PBC"] * x2)), wts_of(c, False)))
        return top, bot
    HAND = {bone("Hand"): 1.0}
    wk = lambda u: 0.70 + 0.30 * u / K0                        # 掌緣直線：寬度隨 u 線性變（手腕 0.70 → 指根 1.0）
    uW = -0.004
    st.append(palm_ring(lambda c: uW, wk(uW) * 0.98, 0.95, 1.0, lambda c, t: {bone("LowerArm"): 0.5, bone("Hand"): 0.5}))
    for uf in (o["T0"], o["P1"], o["P2"]):                     # T0 → P1 那塊側面是拇指根（只包住拇指掌骨那段，不從手腕開始）
        u = uf * HL
        st.append(palm_ring(lambda c, u=u: u, wk(u), 1.0, 1.0, lambda c, t: HAND))
    # 拇指根那塊的手心兩角往內、往上收（TY、TZ 負＝收）：拇指掌指關節離手掌邊緣只有約 7 mm，不收的話靜止時拇指內側就穿進手掌
    #   （2026-10-14 實測：往外推 30 對面互相穿過、不動 17 對、收 3／4 成＋拇指關節 0.95 倍粗 → 0）
    for k_ in (3, 4):
        st[k_][1][0].co += Y * (-o["TY"] * HL) + Z * (-o["TZ"] * HL)
    uKp = K0 - 0.6 * FR
    st.append(palm_ring(lambda c: Ku[c] - 0.6 * FR, wk(uKp), 0.98, o["KPB"],
                        lambda c, t: {bone("Hand"): 1.0 - o["JW"], bone(f"{FN[c // 2]}1"): o["JW"]}))

    def k_w(c, t):                                             # 指根那排：手掌一半、該欄那根手指第一節一半（指縫兩邊的點各屬兩側的手指）
        return {bone("Hand"): 0.5, bone(f"{FN[c // 2]}1"): 0.5}
    kt = o["KT"]
    top, bot = [], []
    for c in range(8):
        v = vmid + (cols[c] - vmid) * 1.0
        top.append(V(at(Ku[c], v, kt * PT), k_w(c, True)))
        x2 = ((cols[c] - vmid) / (cols[-1] - vmid)) ** 2
        bot.append(V(at(Ku[c], v, -o["KB"] * PT * PB * (1 - o["PBC"] * x2)), k_w(c, False)))   # 手心那面指根處比手背薄：彎下來的指尖才不會插進掌心
    st.append((top, bot))

    # 站點串成管子（16 點一圈：手背 0→7、手心 7→0）
    def loop(stn):
        t, b = stn; return t + list(reversed(b))
    loops = [loop(x) for x in st]
    thumb_base = None
    for i in range(len(loops) - 1):
        A, Bq = loops[i], loops[i + 1]
        for k in range(16):
            q = [A[k], A[(k + 1) % 16], Bq[(k + 1) % 16], Bq[k]]
            if i == 3 and k == 15:                             # T0 → P1 之間、食指側那塊側面：拇指從這裡擠出
                thumb_base = [A[0], Bq[0], Bq[15], A[15]]; continue   # [手腕手背, 手掌手背, 手掌手心, 手腕手心]
            F(q)
    # 指根那排的端面：手指的底（擠出去）＋指縫（指蹼）
    tK, bK = st[-1]
    for c in (1, 3, 5):
        F([tK[c], tK[c + 1], bK[c + 1], bK[c]])

    # ── 手指 ──
    def ring_at(center, hw, hh, kn, cr, wts):
        return [V(center + Y * (-hw) + Z * hh * (1 + kn), wts), V(center + Y * hw + Z * hh * (1 + kn), wts),
                V(center + Y * hw - Z * hh * (1 - cr), wts), V(center + Y * (-hw) - Z * hh * (1 - cr), wts)]

    def bridge(r0, r1):
        for k in range(4):
            F([r0[k], r1[k], r1[(k + 1) % 4], r0[(k + 1) % 4]])

    for fi, f in enumerate(FN):
        segs = [J(f"{f}{i}") for i in (1, 2, 3)]
        lens = [(t - h).length for h, t, _ in segs]
        Lt = sum(lens)
        d = (segs[0][1] - segs[0][0]).normalized()
        p0 = segs[0][0]
        rr = lambda sd: FR * (1.0 - 0.07 * min(3.0, sd / Lt * 3.0)) if sd < Lt else FR * 0.80
        J1, J2 = lens[0], lens[0] + lens[1]
        b1, b2, b3 = bone(f"{f}1"), bone(f"{f}2"), bone(f"{f}3")
        h = FR * 0.5
        jw = o["JW"]
        stations = [(h, 0, 0, {b1: 1.0 - jw, bone("Hand"): jw}),
                    (J1 * 0.55, 0, 0, {b1: 1.0}),
                    (J1 - h, 0, 0, {b1: 1.0 - jw, b2: jw}), (J1, 1, 1, {b1: 0.5, b2: 0.5}), (J1 + h, 0, 0, {b2: 1.0 - jw, b1: jw}),
                    (J1 + lens[1] * 0.5, 0, 0, {b2: 1.0}),
                    (J2 - h, 0, 0, {b2: 1.0 - jw, b3: jw}), (J2, 1, 1, {b2: 0.5, b3: 0.5}), (J2 + h, 0, 0, {b3: 1.0 - jw, b2: jw}),
                    (J2 + lens[2] * 0.45, 0, 0, {b3: 1.0}),
                    (Lt - 0.45 * FR * 0.80, 0, 0, {b3: 1.0})]
        prev = [tK[2 * fi], tK[2 * fi + 1], bK[2 * fi + 1], bK[2 * fi]]
        for sd, knk, crs, wts in stations:
            r = rr(sd)
            hw, hh = r * o["FW"] / 0.92, r * o["FH"] / 0.92
            ring = ring_at(p0 + d * sd, hw, hh, o["KN"] * knk, o["CR"] * crs, wts)
            bridge(prev, ring); prev = ring
        F(prev)                                                 # 指尖收口

    # ── 拇指：從食指側那塊側面擠出來 ──
    tb = thumb_base
    segs = [J(f"Thumb{i}") for i in (1, 2, 3)]
    lens = [(t - h).length for h, t, _ in segs]
    Lt = sum(lens); d = (segs[0][1] - segs[0][0]).normalized(); p0 = segs[0][0]
    bc = sum((v.co for v in tb), Vector()) / 4
    e_len = (tb[1].co + tb[2].co - tb[0].co - tb[3].co).normalized()
    e_thk = (tb[0].co + tb[1].co - tb[2].co - tb[3].co).normalized()
    nb = e_thk.cross(e_len).normalized()
    if nb.dot(d) < 0:
        nb = -nb
    q = nb.rotation_difference(d)
    E1, E2 = q @ e_len, q @ e_thk
    sgn = [((v.co - bc).dot(e_len) > 0) * 2 - 1 for v in tb], [((v.co - bc).dot(e_thk) > 0) * 2 - 1 for v in tb]
    for v in tb:                                                # 拇指根那塊：手掌、拇指第一節分著走（拇指根肉墊跟著拇指動）
        W[v] = {k: w * (1 - o["TWB"]) for k, w in W[v].items()}; W[v][bone("Thumb1")] = W[v].get(bone("Thumb1"), 0) + o["TWB"]
    T1, T2, T3 = bone("Thumb1"), bone("Thumb2"), bone("Thumb3")
    J1, J2 = lens[0], lens[0] + lens[1]
    h = TR * 0.5
    tj = o["TJ"]
    trr = lambda sd: (TR * (o["TP"] - (o["TP"] - tj) * sd / J1) if sd < J1 else TR * (tj - (tj - 0.93) * (sd - J1) / lens[1]) if sd < J2 else TR * 0.93 - TR * 0.13 * (sd - J2) / lens[2])
    # 拇指第一節（掌骨）包在手掌的肉墊裡：從側面那塊直接收到掌指關節前，看得到的拇指從掌指關節才開始
    #   （2026-10-14 第一版從第一節中段就是一根圓管，看起來像從手腕插出一根棒子）
    # 拇指根第一圈也只部分跟拇指第一節走（TW1）：拇指往食指收時，整塊肉墊跟著甩會壓進食指根（2026-10-14 relaxed 量到 11.8 mm）
    stations = [(J1 * o["TB"], 0, 0, {T1: o["TW1"], bone("Hand"): 1 - o["TW1"]}),
                (J1 - h, 0, 0, {T1: 1.0 - o["JW"], T2: o["JW"]}), (J1, 1, 1, {T1: 0.5, T2: 0.5}), (J1 + h, 0, 0, {T2: 1.0 - o["JW"], T1: o["JW"]}),
                (J1 + lens[1] * 0.5, 0, 0, {T2: 1.0}),
                (J2 - h, 0, 0, {T2: 1.0 - o["JW"], T3: o["JW"]}), (J2, 1, 1, {T2: 0.5, T3: 0.5}), (J2 + h, 0, 0, {T3: 1.0 - o["JW"], T2: o["JW"]}),
                (J2 + lens[2] * 0.45, 0, 0, {T3: 1.0}), (Lt - 0.45 * TR * 0.8, 0, 0, {T3: 1.0})]
    prev = tb
    for sd, knk, crs, wts in stations:
        r = trr(sd) * o["TH"]
        c = p0 + d * sd
        ring = [V(c + E1 * (sgn[0][k] * r / 0.92) + E2 * (sgn[1][k] * r / 0.92 * (1 + (o["KN"] * knk if sgn[1][k] > 0 else -o["CR"] * crs))), wts) for k in range(4)]
        for k in range(4):
            F([prev[k], ring[k], ring[(k + 1) % 4], prev[(k + 1) % 4]])
        prev = ring
    F(prev)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(f"HandTpl_{s}")
    bm.to_mesh(me)
    ob = bpy.data.objects.new(f"HandTpl_{s}", me)
    bpy.context.scene.collection.objects.link(ob)
    # 籠子權重 → 點群組 TPL_<骨頭>（細分時一起內插）
    idx = {v: i for i, v in enumerate(bm.verts)}
    groups = {}
    for v, ws in W.items():
        tot = sum(ws.values())
        for b, w in ws.items():
            g = groups.get(b) or ob.vertex_groups.new(name="TPL_" + b); groups[b] = g
            g.add([idx[v]], w / tot, "REPLACE")
    bm.free()
    sub = ob.modifiers.new("Sub", "SUBSURF"); sub.levels = 2; sub.render_levels = 2; sub.boundary_smooth = "ALL"
    bpy.ops.object.select_all(action="DESELECT"); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=sub.name)
    # 前臂開口那圈 → hand_ring 1～N（第 1 點最接近正前方 −Y，從手肘往手看逆時針）；全部點 hand_tpl＝1
    me = ob.data
    bnd = set()
    ec = {}
    for p in me.polygons:
        for e in p.edge_keys:
            ec[e] = ec.get(e, 0) + 1
    for (a, b), n in ec.items():
        if n == 1:
            bnd.update((a, b))
    cy, cz = a2.y, a2.z
    ang = lambda co: math.atan2(co.z - cz, -(co.y - cy)) * sg % (2 * math.pi)
    ring = sorted(bnd, key=lambda i: ang(me.vertices[i].co))
    at_r = me.attributes.new("hand_ring", "INT", "POINT")
    at_t = me.attributes.new("hand_tpl", "INT", "POINT")
    for i in range(len(me.vertices)):
        at_t.data[i].value = 1
    for k, i in enumerate(ring):
        at_r.data[i].value = k + 1
    for p in me.polygons:
        p.use_smooth = True
    return ob
