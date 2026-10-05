# 預設禮服 pink-ballgown 的「層次」元件（LIB/costumes/pink-ballgown.json 的 extra_scripts 列出，build_costume() 最後呼叫 build_extra(M, spec)）。
# 來源：新娘專案 projects/bride/scripts/costume_extra_layers.py 第 3 版（2026-10-04 使用者定案）。專案 scripts/ 有同名檔時以專案的為準。
# 參數全在 spec["layers"]，座標是新娘座標（乘 S）。規格的 drape／cascade 已關掉，由本檔取代：
#   1. 襯裙改短、外層紗裙改短，兩層紗的下擺各加一圈荷葉邊 → 下擺看得到一層層的邊
#   2. 歐根紗垂墜兩層（內長外短），下擺往外翻露出深色內面；外層左後腰撐出一大朵波浪
#   3. 各層頂圈收進腰帶底下（不然換成不同顏色後，裙頂會在腰帶上露出一圈）
#   4. 背後右側荷葉瀑布：月牙形一層壓一層、往右下斜、深淺交錯；每層往下只准變寬（不會在下層下擺處往內折）
#   5. 馬甲：上緣翻摺、左上斜向腰中央的大花瓣（射線貼著馬甲表面做，沒有接縫）；pleats（直褶）可選，新娘試過像吊帶所以沒開
#   6. 飄帶推到最外層上面（原本被裙子蓋住）；玫瑰結只對齊腰帶高度以上，下緣花瓣讓垂墜蓋住
#   7. 材質：各層分色、陰影區加大、歐根紗改不透明＋輪廓線。
#      ⚠️ 半透明的歐根紗會和紗裙排序錯亂（所有物件原點都在 0，裡層的紗會畫到外層上面），所以垂墜一律不透明。
#      紗用一般透明（hashed 抖動透明在 24 取樣下顆粒很明顯，試過不用）
#   8. （第 3 版）垂墜貼身：垂墜的間距、褶深、外翻都調小；下擺可改成「往外捲一圈」（roll），側面看得出布的厚度
#      背後瀑布 style="hang"：幾片布從腰帶下緣垂下（頂端收攏、往下散開、直向波浪褶、外層短內層長），取代一層層往外疊的月牙片
#      正面軟蝴蝶結（layers.bow）：兩個圓耳圈＋中間的結＋兩條 V 字剪尾的緞帶，貼著腰帶與垂墜表面；取代規格的 rosette／sash_tails
# 用到 costume.py／outfit_lib.py 的 _new_obj、thicken、skirt_weights、transfer_weights、skirt_mesh、prof_fn、_top_edge、mtoon。
import bpy, bmesh, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

_LX_YC = -0.004 * S_BODY            # 裙子剖面的中心（skirt_mesh 的 ytop）


def _lx_ss(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def _lx_pt(a, r, z):
    return Vector((math.cos(a) * r, _LX_YC + math.sin(a) * r, z))


def _lx_polar(co):
    return math.atan2(co.y - _LX_YC, co.x), math.hypot(co.x, co.y - _LX_YC)


def _lx_prof_r(prof, a, z):
    rx, ry = prof_fn(prof)((WAIST_Z * S - z) / ((WAIST_Z - 0.02) * S))
    rx, ry = rx * S, ry * S
    return 1.0 / math.sqrt((math.cos(a) / rx) ** 2 + (math.sin(a) / ry) ** 2)


class _LxEnv:
    """柱座標包絡：每個角度格、每個高度格記最外半徑。新層照它往外推，就不會和裡層互穿"""

    def __init__(self, objs, nb=120, dz=0.005):
        self.nb, self.dz = nb, dz * S
        self.nz = int(1.5 * S / self.dz) + 2
        self.g = [[None] * self.nz for _ in range(nb)]
        for ob in objs:
            self.add(ob)

    def add(self, ob):
        return self.add_points([v.co for v in ob.data.vertices])

    def add_points(self, cos):
        nb, nz, dz = self.nb, self.nz, self.dz
        g = [[None] * nz for _ in range(nb)]
        for co in cos:
            a, r = _lx_polar(co)
            b = int(round(a / (2 * math.pi) * nb)) % nb; iz = int(round(co.z / dz))
            if 0 <= iz < nz and (g[b][iz] is None or r > g[b][iz]):
                g[b][iz] = r
        for b in range(nb):
            col = g[b]; idx = [i for i, r in enumerate(col) if r is not None]
            for i0, i1 in zip(idx, idx[1:]):                         # 同一角度上，相鄰兩列之間是直線
                for i in range(i0 + 1, i1):
                    u = (i - i0) / (i1 - i0); col[i] = col[i0] * (1 - u) + col[i1] * u
            G = self.g[b]
            for i, r in enumerate(col):
                if r is not None and (G[i] is None or r > G[i]):
                    G[i] = r
        return self

    def fill(self, max_gap=20):
        """角度方向的空格用左右兩邊內插（身體、腰帶這種頂點分布不均的網格，有些角度格會沒有點）"""
        nb = self.nb
        for i in range(self.nz):
            have = [b for b in range(nb) if self.g[b][i] is not None]
            if len(have) < 2:
                continue
            for b0, b1 in zip(have, have[1:] + [have[0] + nb]):
                gap = b1 - b0
                if 1 < gap <= max_gap:
                    r0, r1 = self.g[b0][i], self.g[b1 % nb][i]
                    for b in range(b0 + 1, b1):
                        self.g[b % nb][i] = r0 + (r1 - r0) * (b - b0) / gap
        return self

    def r(self, a, z, spread=1):
        fb = (a % (2 * math.pi)) / (2 * math.pi) * self.nb
        b0 = int(math.floor(fb)); fz = z / self.dz; i0 = int(math.floor(fz)); w = fz - i0
        if not (0 <= i0 < self.nz - 1):
            return None
        best = None
        for b in range(b0 - spread, b0 + 2 + spread):
            col = self.g[b % self.nb]
            r0, r1 = col[i0], col[i0 + 1]
            if r0 is None and r1 is None:
                continue
            r = r1 if r0 is None else r0 if r1 is None else r0 * (1 - w) + r1 * w
            best = r if best is None or r > best else best
        return best


def _lx_mat(spec, key, dflt, dshade, alpha=None):
    col = spec.get("colors", {})
    name = P + "".join(p.capitalize() for p in key.split("_")) + "Mat"
    return mtoon(name, tuple(col.get(key, dflt)), tuple(col.get(key + "_shade", dshade)), alpha=alpha)


def _lx_curl_rows(bm, rows, angles, curl, n=3, scales=None, roll=None):
    """下擺往外、往上捲（外翻），回傳新增的列；scales＝每個點的外翻比例（瀑布兩端收成 0）
    roll＝[半徑, 度數]：改成往下、往外捲一圈（像捲邊的布管），側面看得出布的厚度"""
    hem = rows[-1]; out = []; scales = scales or [1.0] * len(hem)
    if roll:
        rr, deg = roll[0] * S, math.radians(roll[1])
        for c in range(1, n + 1):
            ph = deg * c / n; row = []
            for v, a, k in zip(hem, angles, scales):
                d = Vector((math.cos(a), math.sin(a), 0)) * rr * (1 - math.cos(ph)) - Vector((0, 0, rr * math.sin(ph)))
                row.append(bm.verts.new(v.co + d * max(0.15, k)))
            out.append(row)
        return out
    co, cu = curl[0] * S, curl[1] * S
    for c in range(1, n + 1):
        s = c / n; row = []
        for v, a, k in zip(hem, angles, scales):
            row.append(bm.verts.new(v.co + (Vector((math.cos(a), math.sin(a), 0)) * co * math.sin(s * math.pi / 2) + Vector((0, 0, cu * s * s))) * max(0.15, k)))
        out.append(row)
    return out


# ── 1. 歐根紗垂墜（整圈；下擺高度隨角度變；只往外起伏，不會鑽進裡層） ──
def _lx_peplum(name, mats, env, c, prof):
    hi, lo, ang = c["high_z"] * S, c["low_z"] * S, math.radians(c["high_angle"])
    hw = c.get("hem_wave", [0.0, 0, 0.0])                                      # [振幅, 個數, 相位]：下擺上下起伏（正面看得到波浪邊）
    hem = lambda a: hi * (0.5 + 0.5 * math.cos(a - ang)) + lo * (0.5 - 0.5 * math.cos(a - ang)) + hw[0] * S * math.sin(hw[1] * a + hw[2])
    top = c.get("top_z", 0.978) * S
    N, R = c.get("N", 160), c.get("R", 18)
    folds, amp, ph, gap, margin = c["folds"], c["fold_amp"], c.get("fold_ph", 0.0), c["gap"], c["margin"] * S
    bm = bmesh.new(); rows = []; angles = [2 * math.pi * k / N for k in range(N)]
    for j in range(R + 1):
        t = j / R; row = []
        for a in angles:
            z = top + (hem(a) - top) * t
            re = env.r(a, z)
            re = re if re is not None else _lx_prof_r(prof, a, z)
            f = gap + amp * t ** 1.2 * (0.5 + 0.5 * math.sin(folds * a + ph))
            for ad, wd, amt, p in c.get("bumps", []):
                d = math.atan2(math.sin(a - math.radians(ad)), math.cos(a - math.radians(ad)))
                f += amt * math.exp(-(d / math.radians(wd)) ** 2) * t ** p
            row.append(bm.verts.new(_lx_pt(a, re * (1 + f) + margin, z)))
        rows.append(row)
    rows += _lx_curl_rows(bm, rows, angles, c.get("curl", (0.025, 0.012)), n=c.get("curl_n", 3), roll=c.get("roll"))
    for j, (r0, r1) in enumerate(zip(rows, rows[1:])):
        for k in range(N):
            bm.faces.new((r0[k], r0[(k + 1) % N], r1[(k + 1) % N], r1[k])).material_index = 1 if j >= R else 0
    ob = _new_obj(name, bm, mats[0]); ob.data.materials.append(mats[1])
    skirt_weights(ob); thicken(ob, c.get("thick", 0.0015) * S)
    return ob


# ── 2. 腰部收進腰帶底下 ──
def _lx_cinch(layers, sash_env, body_env, c):
    """layers 由內到外。頂圈收到腰帶內側（最外層離腰帶 3 mm，往內每層再收 step），往下到 z_lo 之前漸漸放開；腰帶以下不准比身體還裡面"""
    n = len(layers); zl = c.get("z_lo", 0.86) * S; step = c.get("step", 0.0015) * S
    zref = c.get("z_ref", 0.98) * S; zsash = c.get("sash_bottom", 0.962) * S
    nb = 120
    for i, ob in enumerate(layers):
        off = 0.003 * S + step * (n - 1 - i)
        me = ob.data; ztop = max(v.co.z for v in me.vertices)
        top = {}
        for v in me.vertices:
            if v.co.z > ztop - 0.004 * S:
                a, r = _lx_polar(v.co); b = int(round(a / (2 * math.pi) * nb)) % nb
                top[b] = max(top.get(b, 0.0), r)
        for v in me.vertices:
            if v.co.z < zl:
                continue
            a, r = _lx_polar(v.co); b = int(round(a / (2 * math.pi) * nb)) % nb
            rt = top.get(b) or top.get((b + 1) % nb) or top.get((b - 1) % nb) or r
            sr = sash_env.r(a, zref)
            s = min(1.0, (sr - off) / rt) if sr else 1.0
            w = _lx_ss((v.co.z - zl) / max(1e-6, ztop - zl))
            r2 = r * (1 - (1 - s) * w)
            if v.co.z < zsash:
                br = body_env.r(a, v.co.z)
                if br:
                    r2 = max(r2, br + (0.004 + 0.0015 * i) * S)
            v.co = _lx_pt(a, r2, v.co.z)
        me.update()


# ── 3. 紗裙：外層改短（下擺前高後低） ──
def _lx_shorten(ob, front, back):
    zt = max(v.co.z for v in ob.data.vertices); old = min(v.co.z for v in ob.data.vertices)
    for v in ob.data.vertices:
        a, _ = _lx_polar(v.co)
        hz = ((front + back) / 2 - (front - back) / 2 * math.sin(a)) * S       # sin<0 是正面
        v.co.z = zt + (v.co.z - zt) * (zt - hz) / (zt - old)
    ob.data.update()


def _lx_frill(name, mat, env, c, z_clamp):
    """下擺荷葉邊：一圈細密波浪的紗，掛在某層紗的下擺"""
    N, R = c.get("N", 200), 6
    top_fn = lambda a: c["top"][0] * S * 0.5 + c["top"][1] * S * 0.5 - (c["top"][0] - c["top"][1]) * S * 0.5 * math.sin(a)
    bot_fn = lambda a: c["bottom"][0] * S * 0.5 + c["bottom"][1] * S * 0.5 - (c["bottom"][0] - c["bottom"][1]) * S * 0.5 * math.sin(a)
    bm = bmesh.new(); rows = []
    for j in range(R + 1):
        t = j / R; row = []
        for k in range(N):
            a = 2 * math.pi * k / N
            z = top_fn(a) + (bot_fn(a) - top_fn(a)) * t - c.get("scallop", 0.0) * S * (0.5 + 0.5 * math.sin(c.get("scallop_n", 24) * a)) * t
            re = env.r(a, max(z, z_clamp(a))) or env.r(a, z_clamp(a) + 0.01 * S) or _lx_prof_r("ball", a, z)
            r = re * (1 + c.get("gap", 0.01)) + c.get("margin", 0.004) * S + c.get("flare", 0.02) * S * t ** 1.5 \
                + c.get("wave", 0.012) * S * (0.5 + 0.5 * math.sin(c.get("waves", 36) * a)) * t
            row.append(bm.verts.new(_lx_pt(a, r, z)))
        rows.append(row)
    for r0, r1 in zip(rows, rows[1:]):
        for k in range(N):
            bm.faces.new((r0[k], r0[(k + 1) % N], r1[(k + 1) % N], r1[k]))
    ob = _new_obj(name, bm, mat); skirt_weights(ob); thicken(ob, 0.001 * S)
    return ob


# ── 4. 背後荷葉瀑布 ──
def _lx_cascade(mats, env, c, prof):
    bm = bmesh.new(); K, R = c.get("K", 30), c.get("R", 8)
    for i in range(c["tiers"]):
        zt = (c["z0"] - c["dz"] * i) * S; L = (c["len"] + c["len_step"] * i) * S
        ac = math.radians(c["a0"] + c["a_step"] * i); half = math.radians(c["half"] + c["half_step"] * i)
        g = c["gap"] + c["gap_step"] * i
        angles = [ac + (k / K - 0.5) * 2 * half for k in range(K + 1)]
        rows = []
        for j in range(R + 1):
            t = j / R; row = []
            for k, a in enumerate(angles):
                u = k / K
                Lu = L * (c.get("end_len", 0.5) + (1 - c.get("end_len", 0.5)) * math.sin(math.pi * u))   # 兩端短、中間長
                z = zt - Lu * t - c["wave_z"] * S * (0.5 + 0.5 * math.sin(u * math.pi * 4 + i)) * t
                re = env.r(a, z)
                re = re if re is not None else _lx_prof_r(prof, a, z)
                r = re * (1 + g) + c["margin"] * S + c["flare"] * S * t ** 1.5 \
                    + c["wave_r"] * S * (0.5 + 0.5 * math.sin(u * math.pi * 6 + 1.7 * i)) * t
                if rows:                                                          # 往下只准變寬：硬挺的布直接垂過下面那層的下擺，不往內折
                    r = max(r, _lx_polar(rows[-1][k].co)[1])
                row.append(bm.verts.new(_lx_pt(a, r, z)))
            rows.append(row)
        rows += _lx_curl_rows(bm, rows, angles, c.get("curl", (0.02, 0.01)), n=2,
                              scales=[math.sin(math.pi * k / K) ** c.get("end_taper", 0.6) for k in range(K + 1)])
        for j, (r0, r1) in enumerate(zip(rows, rows[1:])):
            for k in range(K):
                bm.faces.new((r0[k], r0[k + 1], r1[k + 1], r1[k])).material_index = 2 if j >= R else (i % 2)
    ob = _new_obj("Cascade", bm, mats[0]); ob.data.materials.append(mats[1]); ob.data.materials.append(mats[2])
    skirt_weights(ob); thicken(ob, 0.0015 * S)
    return ob


def _lx_cascade_hang(mats, env, c, prof):
    """背後垂墜（貼身版，style="hang"）：幾片布從腰帶下緣垂下，頂端收攏、往下散開，順著外層裙子往下掉。
    每片：直向波浪褶（兩側貼著下面那層、中間鼓起，越往下越深）、下擺月牙形（褶鼓起處稍長）、下擺捲邊。
    panels 由內到外（內層長、外層短）。半徑＝max(外層裙子＋margin＋stack×層數＋褶, 前幾片＋cover)：
    自己的形狀照外層裙子算，只有碰到前幾片時才蓋過去，褶不會一片一片累加往外撐。
    角度：top＝[起, 迄] 頂端收攏在腰帶下的範圍、span＝[起, 迄] 下擺散開的範圍（90＝正後、180＝角色右）"""
    K, R = c.get("K", 36), c.get("R", 22)
    zt = c.get("top_z", 0.958) * S; m = c.get("margin", 0.004) * S
    st, cov = c.get("stack", 0.003) * S, c.get("cover", 0.003) * S
    penv = _LxEnv([]); bm = bmesh.new()
    for pi, pc in enumerate(c["panels"]):
        t0, t1 = (math.radians(v) for v in pc["top"]); b0, b1 = (math.radians(v) for v in pc["span"])
        lo = pc["low_z"] * S; s0, s1 = pc["side_z"][0] * S, pc["side_z"][1] * S; sk = pc.get("skew", 0.5)
        nf, fa, wz = pc.get("folds", 3), pc.get("fold_amp", 0.03) * S, pc.get("wave_z", 0.02) * S

        def zhem(u, lo=lo, s0=s0, s1=s1, sk=sk):
            if u <= sk:
                return s0 + (lo - s0) * math.sin(math.pi / 2 * u / sk)
            return s1 + (lo - s1) * math.sin(math.pi / 2 * (1 - u) / (1 - sk))
        rows = []; angs = []
        for j in range(R + 1):
            t = j / R; e = t ** 0.6; a0, a1 = t0 + (b0 - t0) * e, t1 + (b1 - t1) * e; row = []; angs = []
            for kk in range(K + 1):
                u = kk / K; a = a0 + (a1 - a0) * u
                fl = 0.5 - 0.5 * math.cos(2 * math.pi * nf * u)
                z = zt + (zhem(u) - zt) * t - wz * fl * t ** 1.5
                re = env.r(a, z); re = re if re is not None else _lx_prof_r(prof, a, z)
                r = re + m + st * pi + fa * fl * t ** 0.8
                rp = penv.r(a, z)
                if rp is not None:
                    r = max(r, rp + cov)
                row.append(bm.verts.new(_lx_pt(a, r, z))); angs.append(a)
            rows.append(row)
        sc = [math.sin(math.pi * kk / K) ** c.get("end_taper", 0.5) for kk in range(K + 1)]
        rows += _lx_curl_rows(bm, rows, angs, c.get("curl", (0.01, 0.006)), n=c.get("curl_n", 4), scales=sc, roll=c.get("roll"))
        for j, (r0, r1) in enumerate(zip(rows, rows[1:])):
            for kk in range(K):
                bm.faces.new((r0[kk], r0[kk + 1], r1[kk + 1], r1[kk])).material_index = 2 if j >= R else pc.get("color", pi % 2)
        penv.add_points([v.co for row in rows for v in row])
    ob = _new_obj("Cascade", bm, mats[0]); ob.data.materials.append(mats[1]); ob.data.materials.append(mats[2])
    skirt_weights(ob); thicken(ob, c.get("thick", 0.0015) * S)
    return ob


# ── 5. 馬甲上的布片：在正面投影上定形狀，射線打到馬甲表面，沿法線推出去 ──
def _lx_band(name, mat, bod, bvh, ptfn, nu, nv, offfn):
    bm = bmesh.new(); grid = []
    for i in range(nu + 1):
        row = []
        for j in range(nv + 1):
            u, v = i / nu, j / nv; x, z = ptfn(u, v)
            loc, nrm, _, _ = bvh.ray_cast(Vector((x, -0.6 * S, z)), Vector((0, 1, 0)))
            if loc is None:
                row.append(None); continue
            if nrm.y > 0:
                nrm = -nrm
            nrm = (nrm + Vector((0, -1.0, 0))).normalized()
            row.append(bm.verts.new(loc + nrm * offfn(u, v)))
        grid.append(row)
    for i in range(nu):
        for j in range(nv):
            q = (grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1])
            if all(q):
                bm.faces.new(q)
    ob = _new_obj(name, bm, mat); thicken(ob, 0.0015 * S); transfer_weights(ob, bod)
    return ob


def _lx_bodice_folds(mat, c):
    bod = O.get(P + "Bodice")
    if bod is None:
        return []
    dg = bpy.context.evaluated_depsgraph_get(); bvh = BVHTree.FromObject(bod, dg)
    edge = _top_edge(bod)
    front = sorted(((p.x, p.z) for a, p, n in edge if math.sin(a) < -0.2), key=lambda q: q[0])

    def ztop(x):
        for (x0, z0), (x1, z1) in zip(front, front[1:]):
            if x0 <= x <= x1:
                return z0 + (z1 - z0) * (x - x0) / max(1e-6, x1 - x0)
        return front[0][1] if x < front[0][0] else front[-1][1]
    out = []
    cf = c.get("cuff")
    if cf:                                    # 上緣翻摺：沿領口往下一條寬帶，下緣翹起
        x0, x1, h, lift = cf["x0"] * S, cf["x1"] * S, cf["h"] * S, cf["lift"] * S
        out.append(_lx_band("Cuff", mat, bod, bvh,
                            lambda u, v: (x0 + (x1 - x0) * u, ztop(x0 + (x1 - x0) * u) - 0.006 * S - v * h * (1 + 0.22 * math.sin(3 * math.pi * u + 0.7))),
                            40, 6, lambda u, v: 0.0035 * S + lift * v ** 1.6))
    dg_ = c.get("diagonal")
    if dg_:                                   # 斜向大花瓣：左上（角色左邊腋下）→ 腰中央，左上那一側翹起
        p0, p1 = Vector(dg_["p0"]) * S, Vector(dg_["p1"]) * S
        d = (p1 - p0).normalized(); perp = Vector((-d.y, d.x))
        if perp.y < 0:
            perp = -perp
        w0, w1, lift = dg_["w0"] * S, dg_["w1"] * S, dg_["lift"] * S

        def pt(u, v):
            q = p0 + (p1 - p0) * u + perp * (v - 0.5) * (w0 + (w1 - w0) * u)
            return q.x, min(q.y, ztop(q.x) - 0.012 * S)
        out.append(_lx_band("Petal", mat, bod, bvh, pt, 30, 8,
                            lambda u, v: 0.0035 * S + lift * v ** 1.5 * (1 - u) ** 0.6))
    for i, pl in enumerate(c.get("pleats", [])):     # 直褶：細長條，一側翹起
        xc, w, zb, lift, slant = pl["x"] * S, pl["w"] * S, pl["z_bottom"] * S, pl["lift"] * S, pl.get("slant", 0.0) * S
        out.append(_lx_band(f"Pleat{i + 1}", mat, bod, bvh,
                            lambda u, v, xc=xc, w=w, zb=zb, slant=slant: (xc + (v - 0.5) * w + slant * u, (ztop(xc) - 0.05 * S) + (zb - (ztop(xc) - 0.05 * S)) * u),
                            24, 3, lambda u, v, lift=lift: 0.003 * S + lift * v * math.sin(math.pi * u) ** 0.5))
    return out


# ── 5b. 正面軟蝴蝶結：兩個圓耳圈＋中間的結＋兩條緞帶尾，全部貼著腰帶／垂墜表面算位置 ──
def _lx_surf(env, x, z, y0=-0.13):
    """正面 (x, z) 落在包絡表面上的 (角度, 半徑)"""
    y = y0 * S
    for _ in range(5):
        a = math.atan2(y - _LX_YC, x)
        r = env.r(a, z) or _lx_prof_r("ball", a, min(z, WAIST_Z * S))
        y = _LX_YC - math.sqrt(max(r * r - x * x, 1e-8))
    return math.atan2(y - _LX_YC, x), r


def _lx_bow(mat, env, c, sash=None):
    """耳圈：一條緞帶繞成扁圈（前半鼓起、後半貼著腰帶），靠結那端捏窄、外端變寬，外端兩角往內收成圓弧、邊緣微微內扣（軟的布）。
    結：半圈布包住耳圈根部，有幾道細皺。緞帶尾：從結後面垂下、跟著垂墜表面往外鼓，邊緣稍微翻起、尾端 V 字剪口。
    座標：center＝[x, z]（+x＝角色左手邊），長度單位公尺（新娘座標）"""
    xc, zc = c["center"][0] * S, c["center"][1] * S; m = c.get("margin", 0.004) * S

    def put(x, z, d, dy=0.0):                          # 表面上 (x, z) 那一點，沿半徑往外 d、再往正前方 dy
        a, r = _lx_surf(env, x, z)                     # 耳圈和結的鼓起用 dy：沿半徑鼓會讓前後兩股左右錯開、角露出來
        return _lx_pt(a, r + d, z) + Vector((0, -dy, 0))
    bm = bmesh.new()
    for lp in c["loops"]:
        sx, L, D = lp["side"], lp["len"] * S, lp["depth"] * S
        hw0, hw1 = lp["hw"][0] * S, lp["hw"][1] * S; tau = math.radians(lp.get("tilt", 15)); rnd = lp.get("round", 1.0)
        x0 = lp.get("root", 0.008) * S; droop = lp.get("droop", 0.0) * S
        NU, NV = 40, 8; grid = []
        for i in range(NU):
            th = 2 * math.pi * i / NU; e = math.sin(th / 2)
            X = x0 + (L - x0) * (1 - math.cos(th)) / 2
            hw = hw0 + (hw1 - hw0) * e ** 0.8
            cap = rnd * hw1                                # 外端橢圓收邊（round＝收邊長度／最大半寬）：寬度順順收圓，邊緣不會折返出尖角
            q = min(1.0, max(0.0, (X - (L - cap)) / max(1e-6, cap)))
            hw *= max(0.18, math.sqrt(1 - q * q))
            row = []
            for j in range(NV + 1):
                v = -1 + 2 * j / NV
                Zl = v * hw - droop * e ** 2
                dep = D * (0.5 + 0.5 * math.sin(th)) * (1 - 0.35 * v * v) + 0.0012 * S * math.sin(3 * math.pi * v) * (1 - e)
                xw = xc + sx * (X * math.cos(tau) - Zl * math.sin(tau))
                zw = zc + X * math.sin(tau) + Zl * math.cos(tau)
                row.append(bm.verts.new(put(xw, zw, m, dep)))
            grid.append(row)
        for i in range(NU):
            for j in range(NV):
                bm.faces.new((grid[i][j], grid[(i + 1) % NU][j], grid[(i + 1) % NU][j + 1], grid[i][j + 1]))
    k = c["knot"]; kw, ry, rz = k["w"] * S, k["ry"] * S, k["rz"] * S; kd = k.get("base", 0.011) * S
    NF, NW = 16, 8; grid = []
    for i in range(NF + 1):
        ph = math.radians(-115 + 230 * i / NF); row = []
        for j in range(NW + 1):
            w = -1 + 2 * j / NW
            x = xc + w * kw * (1 + 0.12 * math.cos(ph))
            z = zc + rz * math.sin(ph) * (1 - 0.12 * w * w)
            d = kd + ry * math.cos(ph) * (1 - 0.18 * w * w) + 0.0013 * S * math.sin(2.5 * math.pi * w + ph)
            row.append(bm.verts.new(put(x, z, m, d)))
        grid.append(row)
    for i in range(NF):
        for j in range(NW):
            bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    ob = _new_obj("Bow", bm, mat); thicken(ob, 0.0015 * S)
    if sash is not None:
        transfer_weights(ob, sash)                    # 結和耳圈跟著腰帶動
    else:
        _weights(ob, [("J_Bip_C_Hips", lambda co: 1.0)])
    bm = bmesh.new()
    for tl in c.get("tails", []):
        sx, Lt = tl["side"], tl["len"] * S; w0, w1 = tl["w"][0] * S, tl["w"][1] * S
        sp, tw0, vc = tl.get("spread", 0.04) * S, tl.get("twist", 0.5), tl.get("vcut", 0.02) * S
        z0 = zc + tl.get("start", -0.004) * S; NT, NV = 24, 6; grid = []
        for i in range(NT + 1):
            t = i / NT
            xcen = xc + sx * (0.004 * S + sp * t ** 1.1 + tl.get("sway", 0.008) * S * math.sin(math.pi * t * 1.6))
            w = w0 + (w1 - w0) * t; tw = tw0 * math.sin(math.pi * t * 1.2 + tl.get("phase", 0.0))
            row = []
            for j in range(NV + 1):
                v = -1 + 2 * j / NV
                x = xcen + v * w * math.cos(tw)
                z = z0 - Lt * t + vc * (1 - abs(v)) * _lx_ss((t - 0.86) / 0.14)
                d = m + 0.003 * S + w * abs(math.sin(tw)) + v * w * math.sin(tw)
                row.append(bm.verts.new(put(x, z, d)))
            grid.append(row)
        for i in range(NT):
            for j in range(NV):
                bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    tails = _new_obj("BowTails", bm, mat); thicken(tails, 0.0015 * S); skirt_weights(tails)
    return ob, tails


# ── 6. 推到最外層上面 ──
def _lx_push_vertices(ob, env, margin):
    for v in ob.data.vertices:
        a, r = _lx_polar(v.co); re = env.r(a, v.co.z)
        if re is not None and r < re + margin:
            v.co = _lx_pt(a, re + margin, v.co.z)
    ob.data.update()


def _lx_push_object(ob, env, margin, z_min=0.0):
    """整個物件往正前方平移，直到 z_min 以上的點都在包絡外（下面的部分讓它被垂墜蓋住）"""
    for _ in range(4):
        need = 0.0
        for v in ob.data.vertices:
            a, r = _lx_polar(v.co); re = env.r(a, v.co.z)
            if re is not None and math.sin(a) < -0.3 and v.co.z > z_min:
                need = max(need, (re + margin - r) / max(0.3, -math.sin(a)))
        if need <= 1e-4:
            break
        for v in ob.data.vertices:
            v.co.y -= need
    ob.data.update()


# ── 7. 材質 ──
def _lx_materials(L):
    mats = [m for m in bpy.data.materials if m.name.startswith(P) and m.name.endswith("Mat")]
    sh = L.get("shading", {})
    for m in mats:
        if m.name in (P + "MetalMat", P + "ShoesMat"):
            continue
        e = m.vrm_addon_extension.mtoon1.extensions.vrmc_materials_mtoon
        if "shift" in sh: e.shading_shift_factor = sh["shift"]
        if "toony" in sh: e.shading_toony_factor = sh["toony"]
    for n in L.get("opaque", []):
        m = bpy.data.materials.get(P + n)
        if m:
            mt = m.vrm_addon_extension.mtoon1; mt.alpha_mode = "OPAQUE"
            col = list(mt.pbr_metallic_roughness.base_color_factor); col[3] = 1.0; mt.pbr_metallic_roughness.base_color_factor = col
    for n in L.get("hashed", []):
        m = bpy.data.materials.get(P + n)
        if m:
            m.vrm_addon_extension.mtoon1.alpha_mode_blend_method_hashed = True
    ol = L.get("outline")
    if ol:
        e0 = bpy.data.materials[P + "MainMat"].vrm_addon_extension.mtoon1.extensions.vrmc_materials_mtoon
        ids = [i.identifier for i in e0.bl_rna.properties["outline_width_mode"].enum_items]
        mode = next((i for i in ids if i.lower().startswith("world")), ids[-1])
        for n in ol["materials"]:
            m = bpy.data.materials.get(P + n)
            if not m:
                continue
            e = m.vrm_addon_extension.mtoon1.extensions.vrmc_materials_mtoon
            e.outline_color_factor = tuple(ol["color"]); e.outline_lighting_mix_factor = ol.get("mix", 0.5)
            e.outline_width_factor = ol["width"] * S; e.outline_width_mode = mode


def build_extra(M, spec):
    L = spec.get("layers", {})
    comp = spec.get("components", {}); prof = comp.get("skirt", {}).get("profile", "ball")
    hz = LENGTH_Z.get(comp.get("skirt", {}).get("length", "floor"), 0.015)
    mk = lambda k, d, s, al=None: _lx_mat(spec, k, d, s, al)
    hem_mat = mk("hem_under", (0.80, 0.50, 0.57), (0.62, 0.33, 0.42))

    # 1. 襯裙改短（透過紗看得到它的下擺）、外層紗改短
    if L.get("lining_hem"):
        lin = skirt_mesh("Lining", M["lining"], prof_fn(prof), hem_z=lambda a: L["lining_hem"], folds=12, fold_amp=0.025, scale=0.985)
        skirt_weights(lin)
    skirts_ = [O[P + n] for n in ("Lining", "Tulle1", "Tulle2", "Tulle3") if P + n in O]
    tulles = [o for o in skirts_ if "Tulle" in o.name]
    if L.get("tulle_outer_hem") and len(tulles) >= 2:
        _lx_shorten(tulles[-1], *L["tulle_outer_hem"])

    # 2. 歐根紗垂墜（由內到外）
    env = _LxEnv(skirts_)
    peps = []
    for i, pc in enumerate(L.get("peplum", [])):
        mat = mk(pc["color"], (0.93, 0.70, 0.74), (0.74, 0.42, 0.50))
        ob = _lx_peplum(pc.get("name", f"Peplum{i + 1}"), (mat, hem_mat), env, pc, prof)
        env.add(ob); peps.append(ob)

    # 3. 腰部收進腰帶底下
    if L.get("waist_cinch") and P + "Sash" in O:
        body = [O[n] for n in (f"{WHO}_Body", f"{WHO}_BodyFill") if n in O]
        _lx_cinch(skirts_ + peps, _LxEnv([O[P + "Sash"]]).fill(), _LxEnv(body).fill(), L["waist_cinch"])

    # 4. 背後荷葉瀑布（在垂墜外面）
    outer = _LxEnv(tulles + peps)
    if L.get("cascade"):
        cc = L["cascade"]
        cm = (mk("cascade_a", (0.97, 0.84, 0.88), (0.78, 0.48, 0.55)), mk("cascade_b", (0.92, 0.68, 0.73), (0.70, 0.40, 0.48)), hem_mat)
        (_lx_cascade_hang if cc.get("style") == "hang" else _lx_cascade)(cm, outer, cc, prof)

    # 5. 紗裙下擺的荷葉邊
    th = mk("tulle_hem", (0.98, 0.90, 0.93), (0.84, 0.70, 0.77), spec.get("tulle_hem_alpha", 0.55))
    for i, fc in enumerate(L.get("frills", [])):
        t_ob = O.get(P + fc["on"])
        if not t_ob:
            continue
        e1 = _LxEnv([t_ob]); zmin = {}
        for v in t_ob.data.vertices:
            a, _ = _lx_polar(v.co); b = int(round(a / (2 * math.pi) * 60)) % 60
            zmin[b] = min(zmin.get(b, 9.0), v.co.z)
        zc = lambda a, zmin=zmin: zmin.get(int(round(a / (2 * math.pi) * 60)) % 60, 0.0) + 0.004 * S
        _lx_frill(f"Frill{i + 1}", th, e1, fc, zc)

    # 6. 飄帶、玫瑰結放到最外層上面
    if P + "SashTails" in O:
        _lx_push_vertices(O[P + "SashTails"], outer, L.get("tails_margin", 0.008) * S)
    if P + "Rosette" in O:
        _lx_push_object(O[P + "Rosette"], outer, 0.006 * S, L.get("rosette_z_min", 0.955) * S)

    # 7. 馬甲布片
    if L.get("bodice_folds"):
        _lx_bodice_folds(mk("petal", (0.97, 0.80, 0.82), (0.74, 0.45, 0.52)), L["bodice_folds"])

    # 7b. 正面軟蝴蝶結（貼著腰帶、馬甲、垂墜的表面）
    if L.get("bow"):
        surf = [O[P + n] for n in ("Sash", "Bodice", "Petal", "Cuff") if P + n in O] + tulles + peps
        _lx_bow(M["sash"], _LxEnv(surf).fill(), L["bow"], O.get(P + "Sash"))

    # 8. 材質（輪廓線最後設：外掛會替「已經用到這個材質」的物件加輪廓線修改器）
    _lx_materials(L)
