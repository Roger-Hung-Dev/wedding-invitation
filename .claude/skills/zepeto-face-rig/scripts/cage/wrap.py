# 乙路線第 2 步：把（已對齊的）模板頭變形貼合到 AI 頭的外型上，並把 AI 頭的頭髮切成獨立零件。
#   1. 五官釘子：模板與 AI 頭的對應點（眼睛四邊、嘴角、嘴唇上下緣、鼻尖、下巴、眉心、耳朵、後腦、頭頂）
#      → 用薄板樣條（RBF）算出平滑的位移場，套到模板所有零件（頭、眼球、牙齒、牙齦）。
#   2. 貼表面：臉皮投影到 AI 頭的皮膚上；眼皮、嘴唇、口腔、鼻孔、耳朵不貼（保留模板的結構）；
#      頭髮底下的頭皮只保證縮在頭髮裡面。投影量再沿網格平滑，避免出現摺痕。
#   3. 眼球：不跟著變形（會變橢圓），改成「整顆移到新眼窩、等比例放大到蓋滿眼窩」。
#   4. 頭髮：從 AI 頭的頭頂沿網格長出整片深色區域，切成獨立物件 Hair。
# 用法：blender.exe -b aligned.blend --python wrap.py -- <AI 五官 landmarks.json>
#   輸出 wrapped.blend（Head、Eyes、牙齒牙齦、Hair，AI_Head 隱藏留作參考）與 wrap_report.json
import bpy, bmesh, os, sys, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
# 每張臉的輸出資料夾（環境變數 ZEPETO_RIG_WORK）與模板資料夾（ZEPETO_RIG_TEMPLATE）；run_face_rig.py 會設好
WORK = os.environ.get("ZEPETO_RIG_WORK") or os.getcwd()
TEMPLATE = os.environ.get("ZEPETO_RIG_TEMPLATE") or os.path.normpath(
    os.path.join(_SCRIPTS, "..", "..", "..", "..", "docs", "data", "blender", "zepeto", "templates", "cartoon-head-lucadrech"))
HERE = WORK
ai_lm_path = sys.argv[sys.argv.index("--") + 1]
A = json.load(open(ai_lm_path, encoding="utf-8"))
T0 = json.load(open(os.path.join(TEMPLATE, "template_landmarks.json"), encoding="utf-8"))

ai = bpy.data.objects["AI_Head"]
body = bpy.data.objects["body"]
eyes_obj = bpy.data.objects["pupil"]
inner_parts = [bpy.data.objects[n] for n in ("upper_teeth", "bottom_teeth", "upper_gum", "bottom_gum")]
U_ai = A["U"]


def verts_np(ob):
    return np.array([ob.matrix_world @ v.co for v in ob.data.vertices])


def set_verts(ob, W):
    inv = ob.matrix_world.inverted()
    for v, w in zip(ob.data.vertices, W):
        v.co = inv @ Vector(w)
    ob.data.update()


# ── AI 頭：頂點、顏色、網格鄰接、BVH ──
AP = verts_np(ai)
ame = ai.data
img = next(n.image for m in ame.materials if m for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image)
w_img, h_img = img.size
px = np.empty(w_img * h_img * 4, dtype=np.float32)
img.pixels.foreach_get(px)
px = px.reshape(h_img, w_img, 4)
uvl = ame.uv_layers.active.data
ACOL = np.zeros((len(AP), 3))
cnt = np.zeros(len(AP))
for poly in ame.polygons:
    for li in poly.loop_indices:
        vi = ame.loops[li].vertex_index
        u, v = uvl[li].uv
        ACOL[vi] += px[min(h_img - 1, int(v * h_img)), min(w_img - 1, int(u * w_img)), :3]
        cnt[vi] += 1
ACOL /= np.maximum(cnt, 1)[:, None]
ALUM = ACOL @ np.array([0.299, 0.587, 0.114])
AADJ = [[] for _ in range(len(AP))]
for e in ame.edges:
    a, b = e.vertices
    AADJ[a].append(b)
    AADJ[b].append(a)

# 頭髮：從最高點沿網格長出深色區域
hair = {int(np.argmax(AP[:, 2]))}
# 頭髮的顏色判斷：比較每個點離「髮色」（頭頂最高 3% 的中間值）近，還是離「膚色」（臉正面眼睛高度的中間值）近。
#   （原本用「亮度 < 0.33」：只適合黑髮，淺色或染色頭髮抓不到）
eye_z0 = (A["eyes"]["L"]["c"][2] + A["eyes"]["R"]["c"][2]) / 2
HAIR_RGB = np.median(ACOL[AP[:, 2] > np.percentile(AP[:, 2], 97)], 0)
skin_m = (AP[:, 1] < 0) & (np.abs(AP[:, 2] - eye_z0) < 0.6 * U_ai) & (np.abs(AP[:, 0]) < 0.6 * U_ai)
SKIN_AI = np.median(ACOL[skin_m], 0)
d_hair = np.linalg.norm(ACOL - HAIR_RGB, axis=1)
d_skin = np.linalg.norm(ACOL - SKIN_AI, axis=1)
HAIRLIKE = d_hair < 0.6 * d_skin
print("[wrap] 髮色 %s、膚色 %s" % (np.round(HAIR_RGB, 3), np.round(SKIN_AI, 3)))
stack = list(hair)
while stack:
    v = stack.pop()
    for u in AADJ[v]:
        if u not in hair and HAIRLIKE[u]:
            hair.add(u)
            stack.append(u)
# 再往外補兩圈「緊鄰頭髮、顏色比較接近髮色」的點（新娘耳前鬢髮的尾端有反光、顏色介於髮色膚色之間，
#   沒算成頭髮 → 頭髮被切短，尾端被臉皮蓋住、轉印成一團深色星狀髒斑）
HAIRISH = (d_hair < d_skin) & (AP[:, 2] < eye_z0)  # 只在眼睛高度以下（鬢角）；上面會把靠近瀏海的眉毛收成頭髮，眉毛被切出缺口
for _ in range(2):
    add_ = {u for v in hair for u in AADJ[v] if u not in hair and HAIRISH[u]}
    hair |= add_
HAIR = np.zeros(len(AP), bool)
HAIR[list(hair)] = True
# 多長一圈，讓頭髮邊緣稍微蓋過皮膚
ring = {u for v in hair for u in AADJ[v]}
HAIR_EXT = HAIR.copy()
HAIR_EXT[list(ring)] = True

# 原版的耳朵範圍（之後切成獨立物件 Ears）：
#   先從耳朵最外側點沿網格長出外圈耳廓，再以耳廓中心為圓心、把周圍的非頭髮部分全部包進來（耳甲、耳朵前緣）。
#   （只用「離頭側往外凸」的條件長：只切到一條 C 形耳廓，耳甲被頭皮蓋住）
ear_mask = np.zeros(len(AP), bool)
for side in (1, -1):
    am = (np.abs(AP[:, 2] - A["eyes"]["L"]["c"][2]) < 0.25) & ~HAIR
    aj = int(np.argmax(np.where(am, side * AP[:, 0], -np.inf)))
    allowed = (~HAIR & (side * AP[:, 0] > side * AP[aj, 0] - 0.24 * U_ai)
               & (np.abs(AP[:, 1] - AP[aj, 1]) < 0.45 * U_ai) & (np.abs(AP[:, 2] - AP[aj, 2]) < 0.45 * U_ai))
    rim = {aj}
    st = [aj]
    while st:
        v = st.pop()
        for u in AADJ[v]:
            if allowed[u] and u not in rim:
                rim.add(u)
                st.append(u)
    rim = np.array(sorted(rim))
    c_ear = AP[rim].mean(0)
    ext = np.linalg.norm(AP[rim] - c_ear, axis=1).max()
    # 第 4 輪：耳朵上緣在貼圖上偏暗、被當成頭髮 → 範圍內「顏色偏暗但不夠暗到算頭髮」的也包進來
    near_c = (~HAIR | (d_skin < d_hair)) & (np.linalg.norm(AP - c_ear, axis=1) < 1.15 * ext) & (side * AP[:, 0] > 0)
    reg = set(rim.tolist())
    st = list(reg)
    while st:
        v = st.pop()
        for u in AADJ[v]:
            if near_c[u] and u not in reg:
                reg.add(u)
                st.append(u)
    ear_mask[list(reg)] = True

ai_bvh = BVHTree.FromPolygons([tuple(v) for v in AP], [tuple(p.vertices) for p in ame.polygons])

# ── 模板目前（已對齊）的五官：從網格結構重新量 ──
TP = verts_np(body)
tme = body.data
bm = bmesh.new()
bm.from_mesh(tme)
bm.verts.ensure_lookup_table()
TADJ = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]
eye_loops = {}
for k in ("L", "R"):
    eye_loops[k] = np.array(T0["eyes"][k]["loop"])


def ring_dist(seeds, maxd):
    """從 seeds 沿網格走幾步（環數）"""
    dist = np.full(len(TP), 99)
    dist[list(seeds)] = 0
    frontier = list(seeds)
    for d in range(1, maxd + 1):
        nxt = []
        for v in frontier:
            for u in TADJ[v]:
                if dist[u] > d:
                    dist[u] = d
                    nxt.append(u)
        frontier = nxt
    return dist


# ── 眼睛結構：模板的眼皮是一條「隧道」—— 從看得到的眼皮邊緣往頭裡延伸、插進眼球裡（從外面看不到）。
#    網格上的開口是隧道最深處，不是眼皮邊緣。真正的眼皮邊緣＝第一圈整圈都在眼球外面的環。
EP0 = verts_np(eyes_obj)
eme = eyes_obj.data
white_i = [i for i, m_ in enumerate(eme.materials) if m_ and m_.name == "white"]
white_v = np.array(sorted({v for p in eme.polygons if p.material_index in white_i for v in p.vertices}))


def fit_sphere(Q):
    """最小平方法擬合球面：回傳球心、半徑"""
    A_ = np.hstack([2 * Q, np.ones((len(Q), 1))])
    b_ = (Q ** 2).sum(1)
    sol = np.linalg.lstsq(A_, b_, rcond=None)[0]
    c_ = sol[:3]
    return c_, math.sqrt(sol[3] + c_ @ c_)


eye_geo = {}
for k, side in (("L", 1), ("R", -1)):
    wv = white_v[np.sign(EP0[white_v, 0]) == side]
    c0, r0 = fit_sphere(EP0[wv])
    rd = ring_dist(eye_loops[k].tolist(), 16)
    margin = None
    for d in range(1, 16):
        ring_v = np.where(rd == d)[0]
        if len(ring_v) and (np.linalg.norm(TP[ring_v] - c0, axis=1) > r0 + 0.002).all():
            margin = d
            break
    mv = np.where(rd == margin)[0]
    q = TP[mv]
    c_o = q.mean(0)
    _, _, vt = np.linalg.svd(q - c_o)
    n_in = vt[2] if vt[2][1] > 0 else -vt[2]
    a0 = np.linalg.norm(q - c_o, axis=1).max()
    d0 = r0 - np.dot(c0 - c_o, n_in)  # 眼球前端凸出眼皮邊緣平面的距離
    eye_geo[k] = dict(c0=c0, r0=r0, rd=rd, margin=margin, margin_v=mv, cap_ratio=d0 / a0, side=side)
print("[wrap] 眼皮邊緣在第 %d／%d 環；眼球半徑 %.3f；凸出比例 %.2f" % (eye_geo["L"]["margin"], eye_geo["R"]["margin"], eye_geo["L"]["r0"], eye_geo["L"]["cap_ratio"]))

pairs_src, pairs_dst = [], []


def pair(src, dst):
    pairs_src.append(np.asarray(src, float))
    pairs_dst.append(np.asarray(dst, float))


def ai_surface_y(x, z):
    """AI 頭皮膚（非頭髮）在 (x, z) 的正面深度"""
    front = (AP[:, 1] < 0.1) & ~HAIR
    i = np.argmin(np.where(front, (AP[:, 0] - x) ** 2 + (AP[:, 2] - z) ** 2, np.inf))
    return AP[i, 1]


# 眼睛：模板眼皮邊緣（不是隧道底部）的內、外、上、下 → AI 眼睛範圍的四邊
for k in ("L", "R"):
    q = TP[eye_geo[k]["margin_v"]]
    e = A["eyes"][k]
    ex, ez, ew, eh = e["c"][0], e["c"][2], e["ew"], e["eh"]
    side = 1 if k == "L" else -1
    # 整圈都對：每個邊緣點依它在圈上的角度，對到 AI 眼睛橢圓上同角度的點（只對上下左右 4 點時，其餘照模板 → 杏仁眼）
    qc = q.mean(0)
    for p_ in q:
        th = math.atan2((p_[2] - qc[2]) / max(np.ptp(q[:, 2]), 1e-6), (p_[0] - qc[0]) / max(np.ptp(q[:, 0]), 1e-6))
        x, z = ex + ew * math.cos(th), ez + eh * math.sin(th)
        pair(p_, (x, ai_surface_y(x, z), z))

# 嘴：嘴角、嘴唇正中上下緣（AI 是一條細線 → 嘴唇變薄）
lips_idx = [i for i, m in enumerate(tme.materials) if m and m.name == "lips"]
ez_t = TP[np.concatenate([eye_loops["L"], eye_loops["R"]]), 2].mean()
lipv = np.array(sorted({v for p in tme.polygons if p.material_index in lips_idx for v in p.vertices}))
lipv = lipv[(TP[lipv, 2] < ez_t - 0.1) & (TP[lipv, 1] < TP[:, 1].min() + 0.5)]
L_ = TP[lipv]
kl, kr = L_[np.argmax(L_[:, 0])], L_[np.argmin(L_[:, 0])]
mid = L_[np.abs(L_[:, 0]) < 0.01]
front_mid = mid[mid[:, 1] < mid[:, 1].min() + 0.06]
lip_top, lip_bot = front_mid[np.argmax(front_mid[:, 2])], front_mid[np.argmin(front_mid[:, 2])]
m = A["mouth"]
mz = m["center"][2]
# 第 4 輪：嘴巴中心的高度改用「正中最紅的點」（U 形微笑的底）。
#   landmarks 的 center 是整條紅色帶的中間值，只比嘴角低 0.01 → 微笑弧線幾乎是平的
ARG = ACOL[:, 0] - ACOL[:, 1]
band_m = ~HAIR & (np.abs(AP[:, 0] - m["center"][0]) < 0.05 * U_ai) & (np.abs(AP[:, 2] - mz) < 0.1 * U_ai) & (AP[:, 1] < m["center"][1] + 0.1 * U_ai)
if band_m.sum() > 3:
    mz = float(AP[band_m][np.argmax(ARG[band_m]), 2])
print("[wrap] 嘴巴中心高度 %.3f（嘴角 %.3f／%.3f）" % (mz, m["L"][2], m["R"][2]))
# 第 4 輪：嘴角往上、往外一點（找五官時嘴角取的是紅色帶最外側，比原版實際上揚的嘴角尖低）
CORNER_UP, CORNER_OUT = 0.035 * U_ai, 0.015 * U_ai
pair(kl, np.array(m["L"]) + np.array([CORNER_OUT, 0, CORNER_UP]))
pair(kr, np.array(m["R"]) + np.array([-CORNER_OUT, 0, CORNER_UP]))
lip_half = 0.05 * U_ai
pair(lip_top, (0.0, ai_surface_y(0.0, mz + lip_half), mz + lip_half))
pair(lip_bot, (0.0, ai_surface_y(0.0, mz - lip_half), mz - lip_half))
# 嘴巴縫在兩側半寬處：沿 AI 那條上揚的微笑弧線（通過兩嘴角與正中的拋物線）→ 帶過來原版天生的微笑
t_hw = (kl[0] - kr[0]) / 2
a_hw = (m["L"][0] - m["R"][0]) / 2
a_par = ((m["L"][2] + m["R"][2]) / 2 - mz) / (a_hw ** 2)
for fr in (-0.75, -0.5, -0.25, 0.25, 0.5, 0.75):  # 第 2 輪：多釘 4 點，嘴型完整沿原版微笑弧線
    near_ = L_[(np.abs(L_[:, 0] - fr * t_hw) < 0.12 * t_hw) & (L_[:, 1] < L_[:, 1].min() + 0.06)]
    if len(near_) < 2:
        continue
    zmid = (near_[:, 2].max() + near_[:, 2].min()) / 2
    src = near_[np.argmin(np.abs(near_[:, 2] - zmid))]
    x = fr * a_hw
    z = mz + a_par * x * x
    pair(src, (x, ai_surface_y(x, z), z))

# 脖子：模板脖子比 AI 短又細 → 脖子底部前後左右 4 點對到 AI 脖子底部
t_low = TP[:, 2].min()
tb = TP[TP[:, 2] < t_low + 0.02]
# AI 頭最底下不一定是脖子（新娘：底部是寬的肩頸底座＋長髮髮尾，脖子釘到 ±0.69、整個下半臉被撐寬）
#   → 量底部到下巴之間每個高度的皮膚（非頭髮）寬度，取「從底部往上第一個不超過最細處 1.15 倍」的高度當脖子底部；
#     底部本來就是脖子（新郎）時選到的就是底部，和原本一樣
t_w = np.ptp(tb[:, 0])
a_low = AP[:, 2].min()
skin_ai = ~HAIR
levels = []
for z_ in np.arange(a_low, A["chin_z"], 0.01):
    sl = skin_ai & (np.abs(AP[:, 2] - (z_ + 0.015)) < 0.015)
    if sl.sum() >= 8:
        levels.append((z_, np.ptp(AP[sl, 0])))
w_min = min(w for _, w in levels)
neck_z = next(z for z, w in levels if w <= 1.15 * w_min)
ab = AP[skin_ai & (AP[:, 2] >= neck_z) & (AP[:, 2] < neck_z + 0.03)]
print("[wrap] 脖子底部 z=%.3f（AI 最低 %.3f）、寬 %.3f（模板 %.3f）" % (neck_z, a_low, np.ptp(ab[:, 0]), t_w))
for ax_, sgn in ((0, 1), (0, -1), (1, 1), (1, -1)):
    ts = tb[np.argmax(sgn * tb[:, ax_])]
    as_ = ab[np.argmax(sgn * ab[:, ax_])]
    pair(ts, as_ + np.array([0, 0, 0.02]))

# 鼻尖：AI 鼻子是小鼓包 → 取正中、眼睛與嘴巴之間最往前的皮膚點
mask = (np.abs(AP[:, 0]) < 0.03) & (AP[:, 2] < A["eyes"]["L"]["c"][2] - 0.1) & (AP[:, 2] > mz + 0.05) & ~HAIR
ai_nose = AP[mask][np.argmin(AP[mask][:, 1])]
mask = (np.abs(TP[:, 0]) < 0.01) & (TP[:, 2] < ez_t - 0.1) & (TP[:, 2] > lip_top[2] + 0.02)
t_nose = TP[mask][np.argmin(TP[mask][:, 1])]
pair(t_nose, ai_nose)

# 下巴：正中、嘴巴下方最往前的點 → AI 同樣定義
def chin_pt(P, mzz, extra_mask=None):
    mk = (np.abs(P[:, 0]) < 0.02) & (P[:, 2] < mzz - 0.12) & (P[:, 2] > mzz - 0.45)
    if extra_mask is not None:
        mk &= extra_mask
    cand = P[mk]
    return cand[np.argmin(cand[:, 1])]


_ac = chin_pt(AP, mz, ~HAIR)
if os.environ.get("ZEPETO_CONTOUR"):  # （試做・ZEPETO）嘴巴到下巴＝眼睛到下巴的 28%（AI 頭 39%，下半臉偏長）
    _cz = (mz - 0.28 * eye_z0) / 0.72
    print("[wrap] ZEPETO 下巴：z %.3f → %.3f" % (_ac[2], _cz))
    _ac = np.array([_ac[0], _ac[1] + 0.03, _cz])
pair(chin_pt(TP, lip_bot[2]), _ac)

# 眉心與兩眉中點：模板眉骨上（眼窩上方 1.6 個眼高）的表面點 → AI 眉毛位置
for k in ("L", "R"):
    q = TP[eye_loops[k]]
    tx, tz = q[:, 0].mean(), q[:, 2].max() + 0.6 * (q[:, 2].max() - q[:, 2].min())
    i = np.argmin(np.where(TP[:, 1] < TP[:, 1].min() + 0.5, (TP[:, 0] - tx) ** 2 + (TP[:, 2] - tz) ** 2, np.inf))
    b = A["brows"][k]["center"]
    pair(TP[i], (b[0], ai_surface_y(b[0], b[2]), b[2]))

# 耳朵：左右最外側的點（耳朵高度附近）→ AI 同樣的點
ear_tips = []
for side in (1, -1):
    tm = (np.abs(TP[:, 2] - ez_t) < 0.25)
    ti = int(np.argmax(np.where(tm, side * TP[:, 0], -np.inf)))
    am = (np.abs(AP[:, 2] - A["eyes"]["L"]["c"][2]) < 0.25) & ~HAIR
    aj = np.argmax(np.where(am, side * AP[:, 0], -np.inf))
    pair(TP[ti], AP[aj])
    ear_tips.append(ti)
    # （試過再釘耳朵頂端、底端：AI 頭上用範圍找耳朵會抓到頭髮邊緣與臉頰，耳朵變尖、往外翹，已拿掉）

# 後腦與頭頂：放在 AI 頭髮的內側（頭髮厚度留 0.12U）
hair_in = 0.12 * U_ai
t_back = TP[np.argmax(TP[:, 1])]
a_back_z = t_back[2]
hb = AP[(np.abs(AP[:, 0]) < 0.05) & (np.abs(AP[:, 2] - a_back_z) < 0.05)]
pair(t_back, (0.0, hb[:, 1].max() - hair_in, a_back_z))
t_top = TP[np.argmax(TP[:, 2])]
ht = AP[(np.abs(AP[:, 0]) < 0.05) & (np.abs(AP[:, 1] - t_top[1]) < 0.08)]
pair(t_top, (0.0, t_top[1], ht[:, 2].max() - hair_in))

# （試做・ZEPETO）下顎輪廓釘到 ZEPETO 比例：AI 頭頭髮底下的臉皮和包子臉一樣寬，V 臉只是兩側細髮絲畫出來的
#   → 模板正面輪廓（每個高度、每一側最外的點）釘到 ZEPETO 預設臉量到的全寬（H＝頭頂到下巴；眼睛在下巴往上 40%）
if os.environ.get("ZEPETO_CONTOUR"):
    a_chin_pt = _ac
    H_z = (eye_z0 - a_chin_pt[2]) / 0.40
    t_chin = chin_pt(TP, lip_bot[2])
    ZW = [(0.05, 0.28), (0.10, 0.39), (0.15, 0.45), (0.22, 0.534), (0.30, 0.63)]
    for f, wf in ZW:
        z_a = a_chin_pt[2] + f * H_z            # AI 座標的高度
        z_t = t_chin[2] + (z_a - a_chin_pt[2])  # 模板上同樣離下巴的高度
        band = (np.abs(TP[:, 2] - z_t) < 0.015) & (TP[:, 1] < t_chin[1] + 0.45)
        for side in (1, -1):
            cand = np.where(band & (np.sign(TP[:, 0]) == side))[0]
            if not len(cand):
                continue
            j = cand[np.argmax(side * TP[cand, 0])]
            pair(TP[j], (side * wf * H_z / 2, TP[j][1] + (a_chin_pt[1] - t_chin[1]), z_a))
    # 下巴底下：從下巴尖往後收成一個轉角（模板是一道斜坡直接接到脖子＝雙下巴）
    for xo in (0.0, 0.1, -0.1):
        zt = t_chin[2] - 0.12
        cand = np.where((TP[:, 1] < t_chin[1] + 0.3) & (TP[:, 2] < t_chin[2]))[0]  # 模板網格稀：取最近的頂點
        if len(cand):
            j = cand[np.argmin(np.hypot(TP[cand, 0] - xo, TP[cand, 2] - zt) + 0.3 * (TP[cand, 1] - t_chin[1]))]
            pair(TP[j], (xo, a_chin_pt[1] + 0.24, a_chin_pt[2] - 0.02))
            print("[wrap] ZEPETO 下巴底下 x=%.1f：%s → %s" % (xo, np.round(TP[j], 3), np.round((xo, a_chin_pt[1] + 0.24, a_chin_pt[2] - 0.08), 3)))
    print("[wrap] ZEPETO 下顎：H=%.3f、AI 下巴 z=%.3f、釘 %d 組" % (H_z, a_chin_pt[2], 2 * len(ZW)))
SRC = np.array(pairs_src)
DST = np.array(pairs_dst)
# 同一個模板頂點被當成兩根釘子、卻要去兩個不同目標 → 薄板樣條無解，只能折衷（誤差會變大）→ 去掉重複的
_, uniq = np.unique(np.round(SRC, 6), axis=0, return_index=True)
if len(uniq) < len(SRC):
    print("[wrap] 去掉重複的釘子 %d 根" % (len(SRC) - len(uniq)))
    keep = np.sort(uniq)
    SRC, DST = SRC[keep], DST[keep]


# ── 1. 薄板樣條位移場 ──
def tps_fit(S, D):
    n = len(S)
    K = np.linalg.norm(S[:, None, :] - S[None, :, :], axis=2)
    Pm = np.hstack([np.ones((n, 1)), S])
    Mat = np.zeros((n + 4, n + 4))
    Mat[:n, :n] = K + 1e-6 * np.eye(n)
    Mat[:n, n:] = Pm
    Mat[n:, :n] = Pm.T
    rhs = np.zeros((n + 4, 3))
    rhs[:n] = D - S
    return np.linalg.solve(Mat, rhs)


def tps_eval(coef, S, X):
    n = len(S)
    K = np.linalg.norm(X[:, None, :] - S[None, :, :], axis=2)
    return K @ coef[:n] + np.hstack([np.ones((len(X), 1)), X]) @ coef[n:]


coef = tps_fit(SRC, DST)
TPw = TP + tps_eval(coef, SRC, TP)
for ob in inner_parts:
    W = verts_np(ob)
    set_verts(ob, W + tps_eval(coef, SRC, W))

# ── 2. 貼表面 ──
margin_max = max(eye_geo["L"]["margin"], eye_geo["R"]["margin"])
lid = np.minimum(eye_geo["L"]["rd"], eye_geo["R"]["rd"]) - margin_max  # 眼皮邊緣＝0，隧道是負的
lipd = ring_dist(lipv.tolist(), 5)
eard = ring_dist(ear_tips, 10)
# 隧道與眼皮邊緣、嘴唇本身、耳朵 2 環內＝0，再 2 環漸變到 1（第 1 輪：原本耳朵 7 環、嘴唇外 1 環都不貼，留太多模板形狀）
w_keep = np.clip(np.minimum.reduce([lid, lipd]) / 2.0, 0, 1)
# 第 3 輪：耳朵不再保留模板形狀（模板是有皺摺的寫實耳，原版是簡單的大圓弧耳）→ 整隻貼到原版耳朵表面
EAR_V = eard <= 9
TN = np.array([v.normal[:] for v in tme.vertices])  # 模板原本的頂點法線：口腔、鼻孔內部是朝內的
fit = np.zeros_like(TPw)
fit_w = np.zeros(len(TPw))
under_hair = set()
for i, p in enumerate(TPw):
    hit = ai_bvh.find_nearest(Vector(p))
    if hit[0] is None:
        continue
    q, n_, idx, dist = hit
    q = np.array(q)
    if EAR_V[i]:  # 耳朵另外處理（縮進原版耳朵裡，見下）
        continue
    # 鼻子（第 4 輪）：模板鼻子比原版尖，朝向差很多 → 範圍內不看朝向、整片貼到原版圓鼻；鼻孔深處（離表面遠）保留
    #   （只把朝向門檻放寬到 0 時，側面看鼻尖還是尖的）
    if np.linalg.norm(TPw[i] - ai_nose) < 0.35 * U_ai and dist < 0.12 * U_ai:
        fit[i] = q - p
        fit_w[i] = 1.0
        continue
    if np.dot(TN[i], np.array(n_)) < 0.4:  # 朝向跟 AI 表面不同（內部的面）→ 不貼
        continue
    face_verts = ame.polygons[idx].vertices
    on_hair = HAIR_EXT[list(face_verts)].any()
    if on_hair:
        # 頭髮底下：只把「穿出頭髮、或離頭髮表面不到 0.03U」的頭皮推回去。
        # （整片往內壓到 hair_in 會在瀏海分線處壓出一道凹痕）
        depth = np.dot(p - q, np.array(n_))
        # 只記「真的被頭髮蓋住、又不是朝正前方」的頭皮（給上材質塗髮色）；多長的一圈與額頭在瀏海縫隙看得到，要留膚色
        if HAIR[list(face_verts)].all() and TN[i][1] > -0.3:
            under_hair.add(i)
        if depth > -0.06 * U_ai:  # 第 2 輪：0.03／0.05 時頭頂分線處還會露出頭皮
            fit[i] = q - np.array(n_) * 0.09 * U_ai - p
            fit_w[i] = min(1.0, w_keep[i] + 0.5)
    elif os.environ.get("ZEPETO_CONTOUR") and p[2] < mz - 0.02 and w_keep[i] > 0.5:
        continue  # （試做・ZEPETO）下半臉兩側照下顎控制點的形狀，不貼 AI 那層寬臉皮
    elif dist < 0.6 * U_ai:  # 第 1 輪：0.25U 時下顎、兩頰外側、脖子離太遠沒貼到
        fit[i] = q - p
        fit_w[i] = w_keep[i]
# 內部結構（口腔、鼻孔、耳朵背面）離 AI 表面太遠 → 不貼
# 投影量沿網格平滑 4 次，避免摺痕
D = fit * fit_w[:, None]
for _ in range(4):
    D = 0.5 * D + 0.5 * np.array([D[nb].mean(0) if nb else D[i] for i, nb in enumerate(TADJ)])
TPf = TPw + D
# 耳朵：直接用原版 AI 頭的耳朵（下面切成獨立物件 Ears）；模板自己的耳朵縮向耳根、藏進原版耳朵裡。
#   試過：第 2 輪整隻放大＋上移（形狀還是模板的寫實耳）、第 3 輪整隻貼到最近表面（大多貼到頭側，變一塊扁鼓包）
#   模板耳朵整片推到原版表面內側 0.1U（只縮向耳根時，殘留的一條會露在原版耳朵前面、遮住耳根）
#   另外：新頭的頭皮落在原版耳朵底下的，也推進去 0.05U（和切下來的耳朵疊在同一個表面會互相閃爍）
ear_w = np.zeros(len(TPf))
for ti in ear_tips:
    rd_e = ring_dist([ti], 10)
    ear_w = np.maximum(ear_w, np.clip((10 - rd_e) / 3.0, 0, 1))
for i in range(len(TPf)):
    q, n_, fi, _ = ai_bvh.find_nearest(Vector(TPf[i]))
    if q is None:
        continue
    under_ear = ear_mask[list(ame.polygons[fi].vertices)].any()  # all 時耳窩邊上幾點沒推進去，從耳窩穿出一小塊白
    if ear_w[i] > 0:
        tgt = np.array(q) - np.array(n_) * 0.1 * U_ai
        TPf[i] = TPf[i] + ear_w[i] * (tgt - TPf[i])
    elif under_ear:
        TPf[i] = np.array(q) - np.array(n_) * 0.1 * U_ai
# ── 2.5（試做・ZEPETO）臉型照 AI 頭的「看得到的輪廓」：
#   a. 跑到 AI 表面外面的臉皮貼回表面（下巴底下的斜坡＝雙下巴、兩頰外凸）；嘴唇、眼皮不動
#   b. 正面看，每個高度的臉寬不超過 AI 皮膚（非頭髮）的寬度：AI 的 V 臉一部分是兩側髮絲框出來的，
#      頭髮底下的臉皮比較寬 → 模板照貼就變包子臉
if os.environ.get("ZEPETO_CONTOUR"):
    ear_y_ai = AP[ear_mask, 1].min() if ear_mask.any() else -0.2
    sk = ~HAIR & (AP[:, 1] < ear_y_ai)
    a_chin = AP[sk & (np.abs(AP[:, 0]) < 0.05) & (AP[:, 1] < -0.3)][:, 2].min()
    zs_ = np.arange(a_chin - 0.02, eye_z0 + 0.01, 0.01)
    S_ = np.array([np.abs(AP[sk & (np.abs(AP[:, 2] - z) < 0.015), 0]).max() if (sk & (np.abs(AP[:, 2] - z) < 0.015)).any() else np.nan for z in zs_])
    ok_ = ~np.isnan(S_)
    zs_, S_ = zs_[ok_], S_[ok_]
    keep_lid = np.minimum.reduce([lid, lipd]) <= 1  # 眼皮、嘴唇本身
    front_t = TPf[:, 1] < ear_y_ai + 0.05
    D2 = np.zeros_like(TPf)
    n_out = n_clamp = 0
    for i in np.where(front_t & (TPf[:, 2] > a_chin - 0.35) & (TPf[:, 2] < eye_z0) & ~keep_lid & ~(ear_w > 0))[0]:
        p = TPf[i]
        q, n_, fi, _ = ai_bvh.find_nearest(Vector(p))
        if q is not None:
            s_ = np.dot(p - np.array(q), np.array(n_))
            if s_ > 0.005:
                D2[i] = np.array(q) - p
                n_out += 1
        if a_chin < p[2] < eye_z0:
            lim = np.interp(p[2], zs_, S_) + 0.01
            x_ = p[0] + D2[i][0]
            if abs(x_) > lim:
                D2[i][0] = np.sign(x_) * lim - p[0]
                n_clamp += 1
    for _ in range(6):  # 沿網格抹順，邊界不起皺
        D2 = 0.5 * D2 + 0.5 * np.array([D2[nb].mean(0) if nb else D2[i] for i, nb in enumerate(TADJ)])
    D2[keep_lid] = 0
    TPf = TPf + D2
    print("[wrap] ZEPETO 輪廓：貼回表面 %d 點、臉寬夾住 %d 點；AI 下巴 z=%.3f；臉寬 %s" % (n_out, n_clamp, a_chin, np.round(S_[::5], 2)))
set_verts(body, TPf)

# ── 3. 眼球：照搬模板「眼皮邊緣 ↔ 眼球」的相對關係 ──
#   眼皮邊緣那一圈變寬幾倍、變高幾倍，眼球就跟著寬幾倍、高幾倍（深度取兩者平均），一起移到新位置。
#   （試過「從開口反推球半徑」：模板眼角包在眼球外側，開口量起來偏大，眼球被放到 0.3 穿出臉皮。）
#   隧道若跑出眼球外，推回眼球裡藏好。
EP = verts_np(eyes_obj)
new_eye = EP.copy()
eye_info = {}
for k in ("L", "R"):
    g = eye_geo[k]
    sel = np.sign(EP[:, 0]) == g["side"]
    q_old, q_new = TP[g["margin_v"]], TPf[g["margin_v"]]
    c_old, c_new = q_old.mean(0), q_new.mean(0)
    sx = np.ptp(q_new[:, 0]) / np.ptp(q_old[:, 0])
    sz = np.ptp(q_new[:, 2]) / np.ptp(q_old[:, 2])
    S = np.diag([sx, (sx + sz) / 2, sz])
    new_eye[sel] = c_new + (EP[sel] - c_old) @ S
    c0_new = c_new + (g["c0"] - c_old) @ S
    tunnel = np.where(g["rd"] < g["margin"])[0]
    u = (TPf[tunnel] - c0_new) @ np.linalg.inv(S)
    du = np.linalg.norm(u, axis=1)
    out_ = du > g["r0"] * 0.97
    u[out_] = u[out_] / du[out_, None] * g["r0"] * 0.97
    TPf[tunnel] = c0_new + u @ S
    eye_info[k] = dict(center=c0_new.round(4).tolist(), scale=[round(float(sx), 3), round(float(sz), 3)], tunnel_fixed=int(out_.sum()),
                       radii=[round(float(g["r0"] * s_), 4) for s_ in (sx, (sx + sz) / 2, sz)])
set_verts(eyes_obj, new_eye)
set_verts(body, TPf)

# ── 4. 頭髮切成獨立物件 ──
hb_ = bmesh.new()
hb_.from_mesh(ame)
hb_.transform(ai.matrix_world)
hb_.verts.ensure_lookup_table()
# 面的頂點過半是頭髮就算頭髮（補掉瀏海上零星的小洞）
# 只切真正是頭髮的面（第 3 輪：多切一圈時那圈是皮膚、帶膚色，頭髮邊緣會留下一條條淺色碎片）
bmesh.ops.delete(hb_, geom=[f for f in hb_.faces if sum(HAIR[v.index] for v in f.verts) * 2 < len(f.verts)], context='FACES')
hair_me = bpy.data.meshes.new("Hair")
hb_.to_mesh(hair_me)
hb_.free()
hair_obj = bpy.data.objects.new("Hair", hair_me)
bpy.context.scene.collection.objects.link(hair_obj)
for mat in ame.materials:
    hair_me.materials.append(mat)
for p in hair_me.polygons:
    p.use_smooth = True
# 頭髮下緣：切口是沿三角形切的，鋸齒狀 → 邊緣那一圈沿著邊緣方向平滑幾次（只動邊緣點）
hb2 = bmesh.new()
hb2.from_mesh(hair_me)
edge_v = [v for v in hb2.verts if v.is_boundary]
for _ in range(8):
    newpos = {}
    for v in edge_v:
        nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
        if len(nb) == 2:
            newpos[v] = v.co * 0.5 + (nb[0].co + nb[1].co) * 0.25
    for v, c in newpos.items():
        v.co = c
# 眼睛高度以下的頭髮邊緣（鬢角、後腦下緣）再做 Taubin 平滑（一正一負交替，邊緣不會往內縮）；瀏海尖端不動
z_eye_ = (A["eyes"]["L"]["c"][2] + A["eyes"]["R"]["c"][2]) / 2
low_v = [v for v in edge_v if v.co.z < z_eye_ - 0.2 * U_ai]
for it in range(40):
    lam = 0.5 if it % 2 == 0 else -0.53
    newpos = {}
    for v in low_v:
        nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
        if len(nb) == 2:
            newpos[v] = v.co + lam * ((nb[0].co + nb[1].co) * 0.5 - v.co)
    for v, c in newpos.items():
        v.co = c
# 上面那步只能磨掉小鋸齒；AI 頭這一帶的三角形大，切口沿三角形走、凹口有一整個三角形深（新娘耳前鬢髮）
#   → 眼睛高度以下的邊緣，沿邊線用較寬的範圍（前後各 4 點、高斯權重）取平均，再把往內一圈的點往鄰點平均放鬆，避免三角形摺起來
low_set = set(low_v)
for _ in range(3):
    newpos = {}
    for v in low_v:
        acc, wsum = v.co * 1.0, 1.0
        for direction in (0, 1):
            prev, cur = v, None
            nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
            if len(nb) != 2:
                break
            cur = nb[direction]
            for k in range(1, 5):
                w_ = math.exp(-(k * k) / 8.0)
                acc += cur.co * w_
                wsum += w_
                nxt = [e.other_vert(cur) for e in cur.link_edges if e.is_boundary and e.other_vert(cur) is not prev]
                if not nxt:
                    break
                prev, cur = cur, nxt[0]
        newpos[v] = acc / wsum
    for v, c in newpos.items():
        v.co = c
inner_ = {e.other_vert(v) for v in low_v for e in v.link_edges} - low_set
for _ in range(4):
    newpos = {v: v.co * 0.5 + sum((e.other_vert(v).co for e in v.link_edges), v.co * 0) / max(1, len(v.link_edges)) * 0.5 for v in inner_ if not v.is_boundary}
    for v, c in newpos.items():
        v.co = c
hb2.to_mesh(hair_me)
hb2.free()
# 臉皮凸出到頭髮外面的點推回頭髮底下 0.04U（新娘耳前的鬢髮：頭髮模型是完整的，但模板臉皮蓋在外面，
#   看起來鬢髮被切短，臉皮還轉印到頭髮的顏色變成一團星狀髒斑）。眼睛、嘴唇、耳朵不動；瀏海後面的額頭本來就在頭髮裡面
hv_ = [tuple(v.co) for v in hair_me.vertices]
hbvh = BVHTree.FromPolygons(hv_, [tuple(p_.vertices) for p_ in hair_me.polygons])
TPh = verts_np(body)
dsp = np.zeros_like(TPh)
for _pass in range(2):
    for i in range(len(TPh)):
        if EAR_V[i] or lid[i] <= 3 or lipd[i] <= 3 or TPh[i][2] > eye_z0:  # 只處理眼睛高度以下（鬢角）
            continue
        q, n_, _, dist = hbvh.find_nearest(Vector(TPh[i] + dsp[i]))
        if q is None or dist > 0.2 * U_ai:
            continue
        q, n_ = np.array(q), np.array(n_)
        if np.dot(TPh[i] + dsp[i] - q, n_) > -0.02 * U_ai:
            dsp[i] = q - n_ * 0.04 * U_ai - TPh[i]
    if _pass == 0:
        for _ in range(3):
            dsp = 0.5 * dsp + 0.5 * np.array([dsp[nb].mean(0) if nb else dsp[i] for i, nb in enumerate(TADJ)])
n_push = int((np.linalg.norm(dsp, axis=1) > 1e-4).sum())
set_verts(body, TPh + dsp)
print("[wrap] 臉皮凸出頭髮外推回 %d 點" % n_push)
# 頭髮只是一層殼，邊緣看起來像紙 → 往內加一點厚度
sol = hair_obj.modifiers.new("Thickness", 'SOLIDIFY')
sol.thickness = 0.03 * U_ai
sol.offset = -1.0

# ── 5. 耳朵切成獨立物件（範圍 ear_mask 在前面算好） ──
eb_ = bmesh.new()
eb_.from_mesh(ame)
eb_.transform(ai.matrix_world)
bmesh.ops.delete(eb_, geom=[f for f in eb_.faces if not all(ear_mask[v.index] for v in f.verts)], context='FACES')
ears_me = bpy.data.meshes.new("Ears")
eb_.to_mesh(ears_me)
eb_.free()
eb2 = bmesh.new()
eb2.from_mesh(ears_me)
edge_v = [v for v in eb2.verts if v.is_boundary]
for it in range(24):  # 耳朵前緣的切口是沿三角形切的、鋸齒狀 → 邊緣沿邊平滑（一般平滑 4 次還看得到一段段直線 → Taubin 24 次）
    lam = 0.5 if it % 2 == 0 else -0.53
    newpos = {}
    for v in edge_v:
        nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
        if len(nb) == 2:
            newpos[v] = v.co + lam * ((nb[0].co + nb[1].co) * 0.5 - v.co)
    for v, c in newpos.items():
        v.co = c
eb2.to_mesh(ears_me)
eb2.free()
ears_obj = bpy.data.objects.new("Ears", ears_me)
bpy.context.scene.collection.objects.link(ears_obj)
for mat in ame.materials:
    ears_me.materials.append(mat)
for p in ears_me.polygons:
    p.use_smooth = True
print("[wrap] 原版耳朵切下 %d 點" % int(ear_mask.sum()))

# ── 6. 肩頸底座（只有 AI 頭底部不是脖子時才有，例：新娘）：脖子底部以下的皮膚切成獨立物件 Bust ──
#   模板脖子只到脖子底部（上面的釘子），底下沒東西 → 正面直接看到長髮內側一片黑
if neck_z > a_low + 0.05:
    bb_ = bmesh.new()
    bb_.from_mesh(ame)
    bb_.transform(ai.matrix_world)
    bb_.verts.ensure_lookup_table()
    # 切在脖子底部，切口上緣每一點貼到模板脖子底端那一圈上（兩者嚴密接合）
    #   試過：剛好切在脖子底部 → 中間一圈黑縫（像頸鍊）；往上多切一段重疊、往內縮 → 脖子、底座、脖子底端三層交錯，一條淺色帶加褐色印子
    bmesh.ops.delete(bb_, geom=[f for f in bb_.faces if not all((not HAIR[v.index]) and v.co.z < neck_z + 0.03 for v in f.verts)], context='FACES')
    # 先把模板脖子底端那幾圈貼回原版表面（最底圈 1、往上兩圈 0.66／0.33）：模板脖子底端比原版表面凸出，
    #   只把底座切口拉上去貼時，側面看接縫處斜出一道凸邊
    bme_t = bmesh.new()
    bme_t.from_mesh(body.data)
    bme_t.verts.ensure_lookup_table()
    r0 = {v.index for v in bme_t.verts if v.is_boundary and v.co.z < neck_z + 0.12}
    rings_ = [r0]
    seen_ = set(r0)
    for _ in range(2):
        nxt = {e.other_vert(bme_t.verts[i]).index for i in rings_[-1] for e in bme_t.verts[i].link_edges} - seen_
        rings_.append(nxt)
        seen_ |= nxt
    TPn = verts_np(body)
    for w_r, ring_i in zip((1.0, 0.66, 0.33), rings_):
        for i in ring_i:
            hit = ai_bvh.find_nearest(Vector(TPn[i]))
            if hit[0] is not None:
                TPn[i] = TPn[i] + w_r * (np.array(hit[0]) - TPn[i])
    set_verts(body, TPn)
    bme_t.free()
    bme_t = bmesh.new()
    bme_t.from_mesh(body.data)
    ring_t = []
    for e in bme_t.edges:
        if e.is_boundary and all(v.co.z < neck_z + 0.12 for v in e.verts):
            ring_t.append((np.array(e.verts[0].co), np.array(e.verts[1].co)))
    bme_t.free()
    if ring_t:
        RA = np.array([a_ for a_, _ in ring_t])
        RB = np.array([b_ for _, b_ in ring_t])
        AB = RB - RA
        L2 = np.maximum((AB * AB).sum(1), 1e-12)
        top_v = [v for v in bb_.verts if v.is_boundary and v.co.z > neck_z - 0.06]
        for v in top_v:
            p_ = np.array(v.co)
            t_ = np.clip(((p_ - RA) * AB).sum(1) / L2, 0, 1)
            q_ = RA + AB * t_[:, None]
            v.co = Vector(q_[np.argmin(((q_ - p_) ** 2).sum(1))])
        print("[wrap] 肩頸底座切口 %d 點貼到脖子底端（%d 段邊）" % (len(top_v), len(ring_t)))
        # 脖子後面原版是長髮（不算皮膚），底座在後面缺一塊、脖子底端懸空，側面看得到缺口
        #   → 底端那圈「附近沒有底座切口」的邊往下補一圈裙邊，貼著原版表面（往內 0.005U）藏到頭髮底下
        snapped = np.array([np.array(v.co) for v in top_v]) if top_v else np.zeros((0, 3))
        skirt_v = {}

        def sv_(p_, down):
            key = (tuple(np.round(p_, 5)), down)
            if key not in skirt_v:
                if down:
                    q0 = p_ + np.array([0, 0, -0.35 * U_ai])
                    hit = ai_bvh.find_nearest(Vector(q0))
                    q0 = np.array(hit[0]) - np.array(hit[1]) * 0.005 * U_ai if hit[0] is not None else q0
                    skirt_v[key] = bb_.verts.new(Vector(q0))
                else:
                    skirt_v[key] = bb_.verts.new(Vector(p_))
            return skirt_v[key]

        n_sk = 0
        for a_, b_ in ring_t:
            mid = (a_ + b_) / 2
            if len(snapped) and np.sqrt(((snapped - mid) ** 2).sum(1)).min() < 0.03:
                continue
            try:
                bb_.faces.new((sv_(a_, False), sv_(b_, False), sv_(b_, True), sv_(a_, True)))
                n_sk += 1
            except ValueError:
                pass
        print("[wrap] 脖子後面補裙邊 %d 段" % n_sk)
    bust_me = bpy.data.meshes.new("Bust")
    bb_.to_mesh(bust_me)
    bb_.free()
    bust_obj = bpy.data.objects.new("Bust", bust_me)
    bpy.context.scene.collection.objects.link(bust_obj)
    for mat in ame.materials:
        bust_me.materials.append(mat)
    for p in bust_me.polygons:
        p.use_smooth = True
    print("[wrap] 肩頸底座切下 %d 面（脖子底部 z=%.3f 以下）" % (len(bust_me.polygons), neck_z))

body.name = "Head"
eyes_obj.name = "Eyes"
ai.hide_set(True)
ai.hide_render = True

rep = dict(pairs=len(SRC), hair_verts=int(HAIR.sum()), fit_moved=int((fit_w > 0).sum()), eyes=eye_info,
           ear_verts=[int(i) for i in np.where(eard <= 9)[0]], hair_rgb=[float(v) for v in HAIR_RGB],
           under_hair=sorted(int(i) for i in under_hair),
           eye_rings={k: dict(margin=int(eye_geo[k]["margin"]),
                              rd={int(i): int(eye_geo[k]["rd"][i]) for i in np.where(eye_geo[k]["rd"] <= eye_geo[k]["margin"] + 4)[0]})
                      for k in ("L", "R")},
           ai_chin_z=float(A["chin_z"]), ai_mouth_z=float(A["mouth"]["center"][2]),
           ai_eye_z=float((A["eyes"]["L"]["c"][2] + A["eyes"]["R"]["c"][2]) / 2), U=float(U_ai),
           max_fit=float(np.linalg.norm(D, axis=1).max()), pairs_err=float(np.linalg.norm(TPw[[int(np.argmin(np.linalg.norm(TP - s_, axis=1))) for s_ in SRC]] - DST, axis=1).max()))
_err = np.linalg.norm(TPw[[int(np.argmin(np.linalg.norm(TP - s_, axis=1))) for s_ in SRC]] - DST, axis=1)
for i in np.argsort(-_err)[:3]:
    if _err[i] > 1e-3:
        print("[wrap] 沒釘到位：模板 %s → 目標 %s，差 %.3f" % (np.round(SRC[i], 3), np.round(DST[i], 3), _err[i]))
json.dump(rep, open(os.path.join(HERE, "wrap_report.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "wrapped.blend"))
print("[wrap] 釘子 %d 組（誤差 %.1e）、貼表面 %d 點（最大 %.3f）、頭髮 %d 點、眼球半徑 L%s R%s" % (
    rep["pairs"], rep["pairs_err"], rep["fit_moved"], rep["max_fit"], rep["hair_verts"], rep["eyes"]["L"]["radii"], rep["eyes"]["R"]["radii"]))
