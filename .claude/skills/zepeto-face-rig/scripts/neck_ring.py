# 標準脖子接口環（頭端）：在 Head 的脖子上做出一圈 48 點的「接口環」，身體端照抄同樣的座標接上來（合約見
#   references/ai-mesh-route.md「頭身接縫」、research-head-body-seam.md 5.4；2026-10-14 使用者選：環照每顆頭量、先不焊成一塊）。
#   1. 環的高度：zmeasure.measure_cut（從身體端 measure_head 的切口規則改來：先找下巴底，再往下找脖子；2 cm 一格），頭端算好寫進頭檔
#   2. 環那層水平切一刀（取代 pack_head.py 以前「從下巴往下每 0.02 切」：那組高度跟身體切口差 0.0098，切口落在三角面上）
#   3. 後頸墊底皮：AI 把後頸畫成頭髮色的頭（新娘），Head 從環到耳朵下面，後面一大片沒有皮（缺口邊是鋸齒）。
#      從環鋪一片規整的格子皮到「下巴 +0.22」（長髮從下巴 +0.2 以下才往後退）：有臉皮的方向墊在臉皮下面、缺口的方向沿橢圓內插；
#      短髮整圈都有臉皮的頭（攝影師）不鋪。hair_fit 讀 nape_patch_top／nape_patch_ang：這個範圍裡的頭髮不必固定在臉上
#   4. 48 點：從脖子中心往固定角度射線（第 0 點正前方 −Y、俯視逆時針：第 12 點 +X、第 24 點正後 +Y、第 36 點 −X），
#      弧上的交點切開邊長出新點、缺口裡的環點＝墊底皮第 0 層；環那層原本的點焊進角度最近的環點
#   5. 寫進 Head：點屬性 neck_ring（環上 1～48、其他 0）、nape_underlay（墊底皮 1＝墊在臉皮下、2＝缺口）；
#      物件屬性 neck_ring_ver 1、neck_ring_n、neck_ring_z、neck_ring_yc（中心 x＝0）、neck_chin_bottom（下巴底，身體端放頭用）、
#      nape_patch_top、nape_patch_ang
#   6. 環上所有形態鍵位移 0：環往上 FALL 內的表情位移漸變到 0
# 用法：blender -b pack.blend -P neck_ring.py -- <landmarks.json> <輸出 .blend> [<報告 .json>]
import bpy, bmesh, sys, json, math, os
from mathutils.bvhtree import BVHTree
import numpy as np
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
LM = json.load(open(a[0], encoding="utf-8")); OUT = a[1]
REP = a[2] if len(a) > 2 else None
NR = 48          # 環的點數（每 7.5°，正前、正後、左、右都在點上）
STEP = 0.02      # 往上每層間距（頭檔單位）
O = bpy.data.objects
hd = O.get("Head") or O["AI_Driven"]
me = hd.data
mw = hd.matrix_world.copy(); mwi = mw.inverted()
# 合約：環的座標、高度都是 Head 的本地座標（＝頭檔座標）；身體端用 Head.matrix_world 換到世界座標。
#   這裡在世界座標算，所以 Head 本身不能有額外變換（產線做出來的頭都是單位矩陣），不是就停下來
if any(abs(mw[i][j] - (1 if i == j else 0)) > 1e-6 for i in range(4) for j in range(4)):
    raise SystemExit("[ring] Head 的 matrix_world 不是單位矩陣，環的座標會跟本地座標對不上：%s" % mw)
rep = {}


# ── 1. 環的高度：照身體端 measure_head 的規則（量法在 zmeasure.py，neck_slim.py 共用；身體端改規則時兩邊要一起改）──
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zmeasure import measure_cut, fit_ellipse

CHIN, RZ, CB = measure_cut(hd)
# 後頸墊底皮補到這個高度：長髮步驟從下巴 +0.2（hair_fit 的支點）以下才往後退，再多一層；
#   也至少到耳朵最低點 +0.04（新娘只到下巴 +0.22 時，從下往上看耳垂下面那排鋸齒的縫還透出頭髮的黑色）
_ears = bpy.data.objects.get("Ears")
_ear_low = min((_ears.matrix_world @ v.co).z for v in _ears.data.vertices) if _ears and len(_ears.data.vertices) else -9
ZTOP = max(LM["chin_z"] + float(os.environ.get("NR_TOP", "0.22")), _ear_low + 0.04)
print("[ring] 下巴 %.4f、下巴底 %s、環的高度 %.4f（zmeasure.measure_cut）、後頸墊底皮到 %.4f" % (CHIN, "%.4f" % CB if CB is not None else "量不到", RZ, ZTOP))

bm = bmesh.new(); bm.from_mesh(me)
# 標記層一開始就建好：中途新增資料層，之前抓的點參照全部失效
tag = bm.verts.layers.int.new("ring_tag")     # 環點：第 i 點存 i+1
ul = bm.verts.layers.int.new("nape_underlay")      # 後頸墊底皮的點：1
bm.transform(mw)   # 全程在世界座標算（Head 已確認是單位矩陣），最後轉回
sk_layers = list(bm.verts.layers.shape.values())
skin_i = next((i for i, m in enumerate(me.materials) if m and m.name.startswith("ZEPETO_Skin")), 0)
EPS = 2e-5

# ── 2. 環那層水平切一刀 ──
bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, RZ), plane_no=(0, 0, 1), dist=1e-5)
bm.verts.ensure_lookup_table()


def level_pieces(z):
    """這一層的截面：平面上的點和邊串成幾段（每段：有序點列、是否閉合）"""
    vs = [v for v in bm.verts if abs(v.co.z - z) < EPS]
    vset = set(vs)
    adj = {v: [e.other_vert(v) for e in v.link_edges if e.other_vert(v) in vset] for v in vs}
    seen = set(); pieces = []
    for v0 in vs:
        if v0 in seen or not adj[v0]:
            continue
        comp = []; st = [v0]
        while st:
            x = st.pop()
            if x in seen: continue
            seen.add(x); comp.append(x); st += adj[x]
        ends = [x for x in comp if len(adj[x]) == 1]
        start = ends[0] if ends else comp[0]
        order = [start]; prev = None; cur = start
        while True:
            nx = [y for y in adj[cur] if y is not prev and y not in order[-2:]]
            if not nx or (not ends and nx[0] is start): break
            prev, cur = cur, nx[0]
            if cur in order: break
            order.append(cur)
        pieces.append(dict(verts=order, closed=not ends, n=len(comp)))
    return pieces


def ang(x, y, yc):  # 0＝正後（+Y）、+90＝角色左（+X）、±180＝正前
    return math.degrees(math.atan2(x, y - yc))


def wrap(t):
    return (t + 180) % 360 - 180


def ell_r(th, rx, ry):
    """從脖子中心往角度 th 的射線打到橢圓的距離"""
    s, c = math.sin(math.radians(th)), math.cos(math.radians(th))
    return 1 / math.sqrt((s / rx) ** 2 + (c / ry) ** 2)


# ── 3. 環那層：脖子那段（最大的一段）→ 擬合橢圓（整片後頸都用它：脖子最直、最像橢圓）──
ps = level_pieces(RZ)
if not ps:
    raise SystemExit("[ring] 環的高度切不到 Head")
arc_pc = max(ps, key=lambda p: p["n"])
fe = fit_ellipse(np.array([v.co[:2] for v in arc_pc["verts"]]))
if fe is None:
    raise SystemExit("[ring] 環那層的截面擬合不出橢圓")
YC, RX, RY = fe
print("[ring] 環那層：%d 點、%s；擬合橢圓 中心 y %.4f、半寬 %.4f、半厚 %.4f" % (arc_pc["n"], "整圈" if arc_pc["closed"] else "有缺口", YC, RX, RY))
GRID = [180.0 - 7.5 * i for i in range(NR)]   # 環第 i 點的角度（第 0 點正前方）

# ── 4. 後頸墊底皮（2026-10-14 第 2 版）──
#   AI 把後頸畫成頭髮色的頭（新娘），pack_head 切頭髮時後頸跟著進 Hair，Head 從環到耳朵下面，後面一大片沒有皮，
#   缺口的邊是 AI 三角形的鋸齒（同一層有好幾個缺口邊，左右還不對稱：新娘左 100～113°、右 96～130°）。
#   第 1 版沿缺口的鋸齒邊一格一格縫（只補到下巴）：長髮往後退以後，下巴到耳朵下面那段又露出缺口，鋸齒邊也難縫。
#   → 改成鋪一片規整的格子皮（每 7.5°、每 0.02 一點），從環鋪到 ZTOP、角度涵蓋所有缺口：
#     有臉皮的方向，墊在臉皮下面 INSET（被臉皮蓋住）；沒有臉皮的方向，照兩側臉皮的半徑沿橢圓內插（剛好接上缺口邊）。
#     從外面看，每個方向不是原本的臉皮就是墊底皮，不會有洞；不用縫鋸齒邊。只有環那一層要接成一整圈。
INSET, DA = 0.004, 7.5
bvh = BVHTree.FromBMesh(bm)


def r_skin(th, z, far=1.5):
    """從外面（離脖子中心 far）沿角度 th 往中心射：打到的第一片＝最外面的臉皮；沒打到（缺口）回傳 None"""
    d = Vector((math.sin(math.radians(th)), math.cos(math.radians(th)), 0))
    o = Vector((0, YC, z)) + d * far
    hit = bvh.ray_cast(o, -d, far - 1e-4)
    return None if hit[0] is None else (hit[0] - Vector((0, YC, z))).length


ROWS = [RZ + STEP * k for k in range(0, 60) if RZ + STEP * k <= ZTOP + 1e-6]
ALL = [180.0 - DA * i for i in range(int(360 / DA))]
gapL, gapR = [], []
for z in ROWS:
    for t in ALL:
        if abs(t) < 175 and r_skin(t, z) is None:
            (gapL if t > 0 else gapR).append(t) if t != 0 else None
has_gap = bool(gapL or gapR) or not arc_pc["closed"]
ULV = []          # 墊底皮的點 ULV[row][col]
TH = []
if has_gap:
    tL = min(150.0, max(gapL, default=DA) + 2 * DA)
    tR = max(-150.0, min(gapR, default=-DA) - 2 * DA)
    TH = [t for t in ALL if tR - 1e-6 <= wrap(t) <= tL + 1e-6]
    TH = sorted({wrap(t) for t in TH}, reverse=True)          # 左 → 正後 → 右
    # 半徑：有臉皮＝臉皮半徑（墊在下面再減 INSET）；缺口＝橢圓＋兩側臉皮跟橢圓的差照角度內插
    nearest = {}
    from mathutils.kdtree import KDTree
    orig = [v for v in bm.verts]
    kd0 = KDTree(len(orig))
    for i, v in enumerate(orig):
        kd0.insert(v.co, i)
    kd0.balance()
    n_under = n_gap = 0
    RES = np.zeros((len(ROWS), len(TH))); KIND = np.zeros((len(ROWS), len(TH)), int); RS = np.zeros_like(RES)
    for k, z in enumerate(ROWS):
        rs = [r_skin(t, z) for t in TH]
        res = [None if r is None else r - ell_r(t, RX, RY) for t, r in zip(TH, rs)]
        known = [i for i, x in enumerate(res) if x is not None]
        for j, t in enumerate(TH):
            if rs[j] is not None:
                RES[k, j] = res[j]; KIND[k, j] = 1; RS[k, j] = rs[j]; n_under += 1
            else:
                lo = max((i for i in known if i < j), default=None); hi = min((i for i in known if i > j), default=None)
                if lo is None and hi is None: rd = 0.0
                elif lo is None: rd = res[hi]
                elif hi is None: rd = res[lo]
                else: rd = res[lo] + (res[hi] - res[lo]) * (j - lo) / (hi - lo)
                RES[k, j] = rd; KIND[k, j] = 2; n_gap += 1
    # 缺口的點上下左右抹順（墊在臉皮下的點不動）：每層照兩側臉皮各自內插，半徑忽大忽小（新娘後頸 0.250～0.279 跳），表面一條一條明暗橫紋
    for _ in range(30):
        P_ = np.pad(RES, 1, mode="edge")
        avg = (P_[:-2, 1:-1] + P_[2:, 1:-1] + P_[1:-1, :-2] + P_[1:-1, 2:]) / 4
        RES = np.where(KIND == 2, RES + 0.6 * (avg - RES), RES)
    for k, z in enumerate(ROWS):
        row = []
        for j, t in enumerate(TH):
            rr = (RS[k, j] - INSET) if KIND[k, j] == 1 else ell_r(t, RX, RY) + RES[k, j]
            co = Vector((rr * math.sin(math.radians(t)), YC + rr * math.cos(math.radians(t)), z))
            v = bm.verts.new(co); v[ul] = int(KIND[k, j])   # 1＝墊在臉皮下、2＝缺口
            src = orig[kd0.find(co)[1]]                 # 形態鍵：照最近的臉皮點的位移（跟著動，不會被蓋住的臉皮穿出來）
            for L in sk_layers:
                v[L] = co + (src[L] - src.co)
            row.append(v)
        ULV.append(row)
    for k in range(len(ROWS) - 1):
        for j in range(len(TH) - 1):
            f = bm.faces.new([ULV[k][j], ULV[k][j + 1], ULV[k + 1][j + 1], ULV[k + 1][j]])
            f.material_index = skin_i; f.smooth = True   # 平面著色每一層明暗不同，看起來一條一條
            f.normal_update()
            c = f.calc_center_median()
            if f.normal.dot(Vector((c.x, c.y - YC, 0))) < 0:
                f.normal_flip()
    print("[ring] 後頸墊底皮：%d 層 × %d 欄（%.1f°～%.1f°），墊在臉皮下 %d 點、缺口 %d 點" % (len(ROWS), len(TH), TH[0], TH[-1], n_under, n_gap))
else:
    print("[ring] 環到 %.3f 整圈都有臉皮，不用墊底皮" % ZTOP)
rep.update(underlay_rows=len(ROWS) if has_gap else 0, underlay_cols=len(TH), ztop=ZTOP)

# ── 5. 48 點的環 ──
ring = {}
arc = arc_pc["verts"]
taken = set()
if not arc_pc["closed"]:
    e0, e1 = arc[0], arc[-1]
    t0, t1 = ang(e0.co.x, e0.co.y, YC), ang(e1.co.x, e1.co.y, YC)
    # 弧的兩端滑到最近的格線角度，當那個環點
    for v, t in ((e0, t0), (e1, t1)):
        gi = min(range(NR), key=lambda i: abs(wrap(GRID[i] - t)))
        rr = math.hypot(v.co.x, v.co.y - YC)
        v.co = Vector((rr * math.sin(math.radians(GRID[gi])), YC + rr * math.cos(math.radians(GRID[gi])), RZ))
        ring[gi] = v; taken.add(gi)
    aL, aR = max(t0, t1), min(t0, t1)
    gL, gR = (GRID[min(taken, key=lambda i: abs(wrap(GRID[i] - aL)))], GRID[min(taken, key=lambda i: abs(wrap(GRID[i] - aR)))])
    # 缺口裡的環點＝墊底皮第 0 層、角度在兩端之間的那些（它們在缺口，不是墊在臉皮下）
    for j, t in enumerate(TH):
        if gR + 1e-6 < t < gL - 1e-6:
            gi = min(range(NR), key=lambda i: abs(wrap(GRID[i] - t)))
            if abs(wrap(GRID[gi] - t)) < 1e-6:
                if ULV[0][j][ul] != 2:
                    print("[ring]   ⚠️ 第 %d 點（%.1f°）在弧的缺口裡卻打到臉皮" % (gi, t))
                ring[gi] = ULV[0][j]; taken.add(gi)
# 弧上：格線角度的射線跟弧的邊求交點 → 切邊長出新點
arc_set = set(arc)
arc_edges = [e for e in bm.edges if e.verts[0] in arc_set and e.verts[1] in arc_set]
for gi in range(NR):
    if gi in taken: continue
    t = math.radians(GRID[gi]); d = (math.sin(t), math.cos(t))
    best = None
    for e in arc_edges:
        p, q = e.verts[0].co, e.verts[1].co
        ex, ey = q.x - p.x, q.y - p.y
        den = d[0] * (-ey) - d[1] * (-ex)
        if abs(den) < 1e-12: continue
        rx_, ry_ = p.x, p.y - YC
        s = (rx_ * (-ey) - ry_ * (-ex)) / den
        u = (d[0] * ry_ - d[1] * rx_) / den
        if s > 0 and -1e-9 <= u <= 1 + 1e-9 and (best is None or s > best[0]):
            best = (s, e, u)
    if best is None:
        raise SystemExit("[ring] 第 %d 點（%.1f°）的射線打不到脖子" % (gi, GRID[gi]))
    s, e, u = best
    if u < 1e-4: ring[gi] = e.verts[0]; continue
    if u > 1 - 1e-4: ring[gi] = e.verts[1]; continue
    ne, nv = bmesh.utils.edge_split(e, e.verts[0], u)   # 新點的形態鍵、屬性、UV 照兩端內插
    ring[gi] = nv
    arc_edges = [x for x in arc_edges + [ne] if x.is_valid]
if len(ring) != NR:
    raise SystemExit("[ring] 環只有 %d 點：少了 %s" % (len(ring), sorted(set(range(NR)) - set(ring))))
for v in ring.values():
    v.co.z = RZ
# 環那層原本的點併進角度最近的環點（焊接）：相鄰環點之間只剩一條邊
#   用溶點（dissolve_verts）不行：弧上切出來的環點只連兩條邊，溶掉旁邊的點後它也被一起清掉（新娘正面 23 點不見）
for gi, v in ring.items():
    v[tag] = gi + 1
old = [v for v in bm.verts if abs(v.co.z - RZ) < EPS and v[tag] == 0 and v[ul] == 0 and not v.is_boundary]
rv = list(ring.items())
tmap = {}
for v in old:
    t_ = ang(v.co.x, v.co.y, YC)
    tmap[v] = min(rv, key=lambda kv: abs(wrap(GRID[kv[0]] - t_)))[1]
bmesh.ops.weld_verts(bm, targetmap=tmap)
ring = {v[tag] - 1: v for v in bm.verts if v.is_valid and v[tag] > 0}
if len(ring) != NR:
    raise SystemExit("[ring] 焊接之後環剩 %d 點：少了第 %s 點" % (len(ring), sorted(set(range(NR)) - set(ring))))
n_conn = 0
for i in range(NR):
    a2, b2 = ring[i], ring[(i + 1) % NR]
    if any(e.other_vert(a2) is b2 for e in a2.link_edges): continue
    if set(a2.link_faces) & set(b2.link_faces):
        bmesh.ops.connect_verts(bm, verts=[a2, b2])
    else:
        bm.edges.new([a2, b2])   # 弧的端點和缺口第一點：不在同一個面上（墊底皮在臉皮下面），只連一條邊
    n_conn += 1
closed = all(any(e.other_vert(ring[i]) is ring[(i + 1) % NR] for e in ring[i].link_edges) for i in range(NR))
gap = max(abs(v.co.z - RZ) for v in ring.values())
print("[ring] 環 %d 點、%s；併掉 %d 點、補連 %d 條邊；高度誤差 %.2e" % (NR, "整圈連通" if closed else "沒連通", len(old), n_conn, gap))
rep.update(ring_n=NR, ring_closed=closed, ring_z=RZ, ring_yc=YC, chin=CHIN, chin_bottom=CB, ring_z_err=gap)

# ── 6. 寫回 Head ──
bm.transform(mwi)
UL_VALS = [v[ul] for v in bm.verts]
bm.to_mesh(me); bm.free(); me.update()
attr = me.attributes.get("neck_ring") or me.attributes.new("neck_ring", 'INT', 'POINT')
vals = [0] * len(me.vertices)
tg = me.attributes.get("ring_tag")
for i, d in enumerate(tg.data):
    vals[i] = d.value
attr.data.foreach_set("value", vals)
for n in ("ring_tag",):
    if me.attributes.get(n): me.attributes.remove(me.attributes[n])
got = sum(1 for x in vals if x)
hd["neck_ring_ver"] = 1; hd["neck_ring_n"] = NR; hd["neck_ring_z"] = RZ; hd["neck_ring_yc"] = YC
# 下巴底（2026-10-14 加，身體端 measure_head 用它放頭）：身體端舊的「比嘴唇退後 0.06」量到的是 V 字下巴的前緣
#   （攝影師 v2 −0.348，真正的下巴底 −0.51）→ 頭被放低 3.7 cm、放大 11%，接口環落在肩膀上
if CB is not None:
    hd["neck_chin_bottom"] = CB
elif "neck_chin_bottom" in hd:
    del hd["neck_chin_bottom"]
if has_gap:   # hair_fit 讀：這個範圍裡的頭髮不必固定在臉上（底下有墊底皮），可以整束往後退
    hd["nape_patch_top"] = ROWS[-1]; hd["nape_patch_ang"] = (TH[0], TH[-1])
print("[ring] 寫入：neck_ring 屬性 %d 點（應為 %d）、neck_ring_z %.4f、neck_ring_yc %.4f、neck_chin_bottom %s" % (
    got, NR, RZ, YC, "%.4f" % CB if CB is not None else "量不到（沒寫）"))
rep.update(ring_marked=got)
# 合約：環上的點在所有形態鍵都不動（身體端照基底座標接，表情動到環就會裂開）。
#   只把環上的點釘回基底不行：新娘 jawOpen 在環上動 0.063（喉嚨跟著下巴往下），旁邊的點照動 → 環那裡折出一道痕。
#   → 環往上 FALL 內，所有形態鍵的位移乘上漸變（環上 0、FALL 以上 1，smoothstep）；環以下（胸像，身體端藏掉）一律 0
#   FALL：新娘試 0.06（張嘴全開時喉嚨折一個角）、0.10（平順，採用）、0.14（下巴底下的動作被壓掉太多、下顎線變直）；環境變數 NR_FALL 可改
FALL = float(os.environ.get("NR_FALL", "0.10"))
mx = 0.0; mx_k = ""
if me.shape_keys:
    base = me.shape_keys.key_blocks[0]
    B_ = np.array([d.co[:] for d in base.data])
    zz = np.array([(mw @ v.co).z for v in me.vertices])
    s_ = np.clip((zz - RZ) / FALL, 0, 1); w_ = s_ * s_ * (3 - 2 * s_)
    ring_i = [i for i, x in enumerate(vals) if x]
    for kb in me.shape_keys.key_blocks[1:]:
        K_ = np.array([d.co[:] for d in kb.data])
        D_ = K_ - B_
        dr = np.linalg.norm(D_[ring_i], axis=1).max() if ring_i else 0.0
        if dr > mx: mx, mx_k = float(dr), kb.name
        kb.data.foreach_set("co", (B_ + D_ * w_[:, None]).ravel())
print("[ring] 環上的點原本在形態鍵的最大位移 %.2e（%s）；環往上 %.2f 內所有形態鍵的位移漸變到 0（環上 0）" % (mx, mx_k or "-", FALL))
rep.update(ring_shape_disp_before=mx, ring_shape_disp_key=mx_k, shape_fall=FALL)
# 墊底皮：rest 屬性＝自己的座標（材質眼睛用 rest；墊底皮用 ZEPETO_Skin，沒有眼睛節點，只是不留 0）
ulv = [i for i, x in enumerate(UL_VALS) if x]
if "rest" in me.attributes and ulv:
    r_ = me.attributes["rest"]
    if r_.data_type == 'FLOAT_VECTOR':
        for i in ulv:
            r_.data[i].vector = me.vertices[i].co
# 墊底皮的貼圖座標：一律指到「脖子側面皮膚的中間色」那一點（第 1 版指脖子正面一點，比旁邊亮，身體端看到一塊亮色矩形）
uvl = me.uv_layers.active
if uvl and ulv:
    ulset = set(ulv)
    img = next((n.image for n in me.materials[skin_i].node_tree.nodes if n.type == 'TEX_IMAGE' and n.image), None)
    if img:
        W_, H_ = img.size
        px = np.array(img.pixels[:], np.float32).reshape(H_, W_, 4)[..., :3]
        cand = []   # 環到下巴、側面（90～150°）、皮膚材質、不是墊底皮
        for p in me.polygons:
            if p.material_index != skin_i: continue
            for li, vi in zip(p.loop_indices, p.vertices):
                if vi in ulset: continue
                w = mw @ me.vertices[vi].co
                if RZ < w.z < CHIN and 90 < abs(ang(w.x, w.y, YC)) < 150:
                    u, v_ = uvl.data[li].uv
                    cand.append((px[min(H_ - 1, int(v_ * H_)), min(W_ - 1, int(u * W_))], uvl.data[li].uv.copy()))
        if cand:
            C_ = np.array([c[0] for c in cand]); med = np.median(C_, 0)
            best = cand[int(np.argmin(np.linalg.norm(C_ - med, axis=1)))][1]
            n_uv = 0
            for p in me.polygons:
                if all(v in ulset for v in p.vertices):
                    for li in p.loop_indices:
                        uvl.data[li].uv = best; n_uv += 1
            print("[ring] 墊底皮的貼圖座標 %d 個角指到脖子側面的中間色 %s（取 %d 個角）" % (n_uv, np.round(med, 3), len(cand)))
# ── 7. 整塊在環以下的頭髮刪掉：AI 在胸像底部畫的深色衣領被切頭髮時當成頭髮（攝影師 v2：背後兩塊 143、101 點）。
#   胸像（Head 環以下）身體端會藏，這些卻是 Hair、藏不到 → 從肩膀上露出黑色碎片、插進身體。
#   長髮一定連著頭（新娘整片頭髮一塊、跨過環），不會整塊在環以下
_hair = bpy.data.objects.get("Hair")
if _hair is not None and len(_hair.data.vertices):
    bh = bmesh.new(); bh.from_mesh(_hair.data); bh.verts.ensure_lookup_table()
    hw_ = _hair.matrix_world
    seen_, drop_, nisl = set(), [], 0
    for v0 in bh.verts:
        if v0.index in seen_: continue
        isl_, st_ = [], [v0]; seen_.add(v0.index)
        while st_:
            x_ = st_.pop(); isl_.append(x_)
            for e_ in x_.link_edges:
                u_ = e_.other_vert(x_)
                if u_.index not in seen_:
                    seen_.add(u_.index); st_.append(u_)
        if max((hw_ @ x_.co).z for x_ in isl_) < RZ - 0.005:
            drop_ += isl_; nisl += 1
    if drop_:
        bmesh.ops.delete(bh, geom=drop_, context='VERTS')
        bh.to_mesh(_hair.data); _hair.data.update()
    bh.free()
    rep["hair_below_ring_dropped"] = [nisl, len(drop_)]
    print("[ring] 整塊在環以下的頭髮：刪掉 %d 塊、%d 點" % (nisl, len(drop_)))
if REP:
    json.dump(rep, open(REP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
