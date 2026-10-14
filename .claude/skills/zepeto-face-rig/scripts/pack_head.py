# AI 網格路線 ⑥ 之前：整理成交接格式（身體、服裝、動畫三端照舊頭的結構讀頭檔，三端程式不用改）
#   1. AI_Driven → Head；皮膚材質 → ZEPETO_Skin（身體端取膚色、脖子顏色漸層找這個名字）
#   2. 頭髮切成獨立物件 Hair、材質 ZEPETO_Hair（身體端把脖子切口以下藏起來；頭髮跟臉同一網格的話垂到背後的長髮會被一起切掉；
#      頭髮避開肩膀 hairfit 也找 Hair）。頭髮自己一份材質：身體端在 ZEPETO_Skin 上做脖子顏色漸層，共用的話下巴以下的長髮會被染成膚色
#   3. 耳朵切成獨立物件 Ears、材質 ZEPETO_Ears（服裝端找耳垂掛耳環；沒有的話抓「頭最外側的最低點」，長髮會被當成耳朵）
#   4. 嘴唇的面另給 ZEPETO_Lips（身體端量嘴巴位置，例：叉子送到嘴邊）：外觀跟皮膚一樣（同一份材質的複本）
#   切開用 mesh.separate：形態鍵跟著帶過去（頭髮、耳朵的瀏海與鬢角也會跟表情動）；驅動器在骨架步驟才建，所以切完再接骨架
# 用法：blender -b face.blend -P pack_head.py -- <landmarks.json> <輸出 .blend>
import bpy, bmesh, sys, json
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:]
LM = json.load(open(a[0], encoding="utf-8")); OUT = a[1]
ai = bpy.data.objects["AI_Driven"]; me = ai.data
P = np.array([ai.matrix_world @ v.co for v in me.vertices])
N = len(P)
PK = np.array([d.value for d in me.attributes["pocket_k"].data])
SIDE = np.array([d.value for d in me.attributes["lip_side"].data])
skin_mat = me.materials[0]
tex = next(n for n in skin_mat.node_tree.nodes if n.type == 'TEX_IMAGE')
img = tex.image
W, H = img.size
px = np.array(img.pixels[:], np.float32).reshape(H, W, 4)[..., :3]
uvl = me.uv_layers.active.data
COL = np.zeros((N, 3)); cnt = np.zeros(N)
for p in me.polygons:
    for li, vi in zip(p.loop_indices, p.vertices):
        u, v = uvl[li].uv
        COL[vi] += px[min(H - 1, int(v * H)), min(W - 1, int(u * W))]; cnt[vi] += 1
COL /= np.maximum(cnt, 1)[:, None]
ADJ = [[] for _ in range(N)]
for e in me.edges:
    i, j = e.vertices; ADJ[i].append(j); ADJ[j].append(i)
eyes = LM["eyes"]
ez = (eyes["L"]["c"][2] + eyes["R"]["c"][2]) / 2
chin_z = LM["chin_z"]
U = abs(eyes["L"]["c"][0] - eyes["R"]["c"][0])

# ── 頭髮：從頭頂沿網格長出「顏色像頭髮」的區域（同 wrap.py；髮色＝頭頂最高 3%、膚色＝眼睛高度的臉正面）──
HAIR_RGB = np.median(COL[P[:, 2] > np.percentile(P[:, 2], 97)], 0)
sk = (P[:, 1] < 0) & (np.abs(P[:, 2] - ez) < 0.6 * U) & (np.abs(P[:, 0]) < 0.6 * U) & (PK == 0)
SKIN_RGB = np.median(COL[sk], 0)
dh = np.linalg.norm(COL - HAIR_RGB, axis=1); ds = np.linalg.norm(COL - SKIN_RGB, axis=1)
hairlike = (dh < 0.6 * ds) & (PK == 0)
hair = np.zeros(N, bool)
st = [int(np.argmax(P[:, 2]))]; hair[st[0]] = True
while st:
    v = st.pop()
    for u in ADJ[v]:
        if not hair[u] and hairlike[u]:
            hair[u] = True; st.append(u)
for _ in range(2):  # 鬢角髮尾有反光、顏色介於兩者之間：眼睛以下再往外補兩圈
    add = [u for v in np.where(hair)[0] for u in ADJ[v] if not hair[u] and dh[u] < ds[u] and P[u, 2] < ez and PK[u] == 0]
    hair[add] = True
print("[pack] 髮色 %s、膚色 %s、頭髮點 %d" % (np.round(HAIR_RGB, 3), np.round(SKIN_RGB, 3), int(hair.sum())))

# ── 耳朵：兩側最外側的皮膚（非頭髮）點當起點，在附近長出耳廓；長出來太小（< 40 點）就換下一個起點
#    （新娘左側最外面有一小塊 4 點的膚色碎片：舊產線 wrap.py 和籠子都只抓到它，左耳整個沒切出來）
#    再往周圍包一圈，但只包「往外凸」的部分（比耳廓中心往內不超過 0.4 個耳廓半徑）：全包的話耳後一塊臉皮也進來，
#    服裝端拿耳朵最低點當耳垂掛耳環就會掛錯
ear = np.zeros(N, bool)
for side in (1, -1):
    band = (P[:, 2] > ez - 0.5 * U) & (P[:, 2] < ez + 0.2 * U) & ~hair & (PK == 0) & (np.sign(P[:, 0]) == side)
    order = np.where(band)[0][np.argsort(-side * P[band, 0])]
    seen = np.zeros(N, bool); rim = None
    for aj in order[:400]:
        if seen[aj]:
            continue
        allowed = (~hair & (PK == 0) & (side * P[:, 0] > side * P[aj, 0] - 0.24 * U)
                   & (np.abs(P[:, 1] - P[aj, 1]) < 0.45 * U) & (np.abs(P[:, 2] - P[aj, 2]) < 0.45 * U))
        reg = {int(aj)}; st = [int(aj)]
        while st:
            v = st.pop()
            for u in ADJ[v]:
                if allowed[u] and u not in reg:
                    reg.add(u); st.append(u)
        seen[list(reg)] = True
        if len(reg) >= 40:
            rim = np.array(sorted(reg)); break
    if rim is None:
        print("[pack] %s 耳：找不到（沒有夠大的外凸皮膚）" % ("左" if side > 0 else "右")); continue
    c = P[rim].mean(0); ext = np.linalg.norm(P[rim] - c, axis=1).max()
    near = ~hair & (PK == 0) & (np.linalg.norm(P - c, axis=1) < 1.15 * ext) & (side * P[:, 0] > side * c[0] - 0.4 * ext)
    reg = set(rim.tolist()); st = list(reg)
    while st:
        v = st.pop()
        for u in ADJ[v]:
            if near[u] and u not in reg:
                reg.add(u); st.append(u)
    ear[list(reg)] = True
    print("[pack] %s 耳 %d 點（起點 x=%.3f z=%.3f、最低 z=%.3f）" % ("左" if side > 0 else "右", len(reg), P[rim[0], 0], P[rim[0], 2], P[list(reg), 2].min()))

# ── 臉旁的細髮絲：浮在皮膚外面的薄片 → 沿法線往內射，0.12 內就打到另一層表面（皮膚往內射要穿過整顆頭）
#    （顏色判斷抓不到：AI 把髮絲一半畫成膚色。留在臉上的話：hairfit 把耳垂以下偏離膚色的貼圖改成膚色，髮絲整條變膚色；
#     身體端量脖子粗細會把垂到下巴以下的髮絲算進去，新娘脖子量成 3.1 倍粗）
#    試過用「同一高度左右有間隔」判斷：脖子網格本身就有間隔，脖子皮膚被當成頭髮、套頭髮材質變黑色鋸齒
#    耳朵、臉中間（鼻孔）也是薄的，排除
from mathutils import Vector as _V
from mathutils.bvhtree import BVHTree as _BVH
me.update()
_bv = _BVH.FromPolygons([_V(p) for p in P], [tuple(p_.vertices) for p_ in me.polygons if all(PK[v] == 0 for v in p_.vertices)])
_m3 = ai.matrix_world.to_3x3()
thin_d = np.full(N, 9.0)
for i, v in enumerate(me.vertices):
    if PK[i] or ear[i] or abs(P[i, 0]) < 0.12 or P[i, 2] < chin_z - 0.3:  # 下巴往下 0.3 以下不算（頭髮最下面的髮尾、衣領邊也是薄片，被當細髮絲往前推進胸口）
        continue
    n_ = (_m3 @ v.normal).normalized()
    h_ = _bv.ray_cast(_V(P[i]) - n_ * 1e-4, -n_, 1.0)
    if h_[0] is not None:
        thin_d[i] = h_[3]
strand = thin_d < 0.12
for _ in range(2):  # 往外補兩圈（髮絲的邊、背面）：只補也算薄的點（0.25 內）
    add = [u for v in np.where(strand)[0] for u in ADJ[v] if not strand[u] and thin_d[u] < 0.25 and not ear[u] and PK[u] == 0]
    strand[add] = True
hair |= strand
# AI 頭底部的衣領（黑色，顏色像頭髮）：下巴往下 0.35 以下、胸口正面那一帶留在臉上——身體端把脖子切口以下藏掉；
#   歸到頭髮的話不會被藏，長髮避開身體時還整條推進胸口
collar = hair & (P[:, 2] < chin_z - 0.35) & (np.abs(P[:, 0]) < 0.4) & (P[:, 1] < 0.0)
hair &= ~collar
print("[pack] 衣領留在臉上 %d 點" % int(collar.sum()))
_sa = me.attributes.get("strand") or me.attributes.new("strand", 'INT', 'POINT')
_sa.data.foreach_set("value", strand.astype(np.int32))  # 給 hair_fit：細髮絲往前避開（垂在肩膀前面）
print("[pack] 臉旁細髮絲 %d 點（薄片：往內 0.12 內打到另一層）" % int(strand.sum()))

# ── 面的分類：多數點是頭髮＝頭髮面；耳朵同理；口腔袋、唇緣一律留在 Head ──
face_cls = []
for p in me.polygons:
    vs = list(p.vertices)
    if (PK[vs] > 0).any():
        face_cls.append(0); continue
    h = hair[vs].mean(); e_ = ear[vs].mean()
    face_cls.append(1 if h > 0.5 else 2 if e_ > 0.5 else 0)
face_cls = np.array(face_cls)
# 黏在耳朵旁的小塊頭髮（攝影師 v2：耳垂下各一顆 71、82 點的黑色水滴，像耳環）→ 改歸耳朵、材質畫成膚色（點屬性 ear_fix）。
#   不能切出來再刪：它本來就是頭的表面，刪掉耳垂下面破一個洞
EAR_ISL_MAX, EAR_NEAR = 200, 0.08
ear_fix = np.zeros(N, bool); n_ear_isl = 0
_ei = np.where(ear)[0]
if len(_ei):
    from mathutils.kdtree import KDTree as _KDT
    _kde = _KDT(len(_ei))
    for j_, i_ in enumerate(_ei):
        _kde.insert(_V(P[i_]), j_)
    _kde.balance()
    _hf = set(np.where(face_cls == 1)[0].tolist())
    _v2f = {}
    for f_ in _hf:
        for v_ in me.polygons[f_].vertices:
            _v2f.setdefault(v_, []).append(f_)
    _seen = set()
    for f0 in _hf:
        if f0 in _seen:
            continue
        comp = [f0]; _seen.add(f0); k_ = 0
        while k_ < len(comp):
            for v_ in me.polygons[comp[k_]].vertices:
                for g_ in _v2f[v_]:
                    if g_ not in _seen:
                        _seen.add(g_); comp.append(g_)
            k_ += 1
        vs_ = np.unique([v_ for f_ in comp for v_ in me.polygons[f_].vertices])
        if len(vs_) < EAR_ISL_MAX and _kde.find(_V(P[vs_].mean(0)))[2] < EAR_NEAR:
            face_cls[comp] = 2; ear_fix[vs_] = True; n_ear_isl += 1
print("[pack] 黏在耳朵旁的小塊頭髮改歸耳朵：%d 塊、%d 點" % (n_ear_isl, int(ear_fix.sum())))
_ef = me.attributes.get("ear_fix") or me.attributes.new("ear_fix", 'FLOAT', 'POINT')
_ef.data.foreach_set("value", ear_fix.astype(np.float32))

# ── 嘴唇的面：唇線上下 0.04 內、嘴寬以內、上下唇兩側的皮膚面 ──
m = LM["mouth"]; xc = (m["L"][0] + m["R"][0]) / 2; hw = (m["L"][0] - m["R"][0]) / 2; zc = m["center"][2]; zk = (m["L"][2] + m["R"][2]) / 2
def z_s(x):
    return zc + (zk - zc) * min(1.0, ((x - xc) / hw) ** 2)
lip_f = []
for p in me.polygons:
    if face_cls[p.index] != 0 or p.material_index != 0:
        continue
    c_ = ai.matrix_world @ p.center
    if c_.y < -0.3 and abs(c_.x - xc) < hw and abs(c_.z - z_s(c_.x)) < 0.04 and all(SIDE[v] in (1, 2, 3) for v in p.vertices):
        lip_f.append(p.index)
# 單純材質（貼圖直接接到 Base Color）：身體端取膚色時把頭材質裡的貼圖拿掉、改設 Base Color 預設值——
#   眼睛、眨眼的節點串在貼圖後面的話，拿掉貼圖後那串的預設值是白色，身體變成灰白（2026-10-14 試接身體）
#   → 下巴以下（身體端讀的部分）、頭髮、耳朵用單純材質 ZEPETO_Skin；臉上半部（有材質眼睛）叫 ZEPETO_Face
def plain_copy(name):
    pm = skin_mat.copy(); pm.name = name
    nt = pm.node_tree
    bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tx = next(n for n in nt.nodes if n.type == 'TEX_IMAGE')
    for l_ in list(bs.inputs['Base Color'].links):
        nt.links.remove(l_)
    nt.links.new(tx.outputs['Color'], bs.inputs['Base Color'])
    tx.inputs['Vector'].links and nt.links.remove(tx.inputs['Vector'].links[0])  # 貼圖座標直接用 UV（材質眼睛的偏移不要）
    for n in [n for n in nt.nodes if n.type not in ('BSDF_PRINCIPLED', 'TEX_IMAGE', 'OUTPUT_MATERIAL', 'UVMAP')]:
        nt.nodes.remove(n)
    if nt.animation_data:
        nt.animation_data_clear()
    return pm
lips_mat = skin_mat.copy(); lips_mat.name = "ZEPETO_Lips"
me.materials.append(lips_mat); li = len(me.materials) - 1
for f in lip_f:
    me.polygons[f].material_index = li
print("[pack] 嘴唇面 %d" % len(lip_f))
plain = plain_copy("ZEPETO_Skin")
me.materials.append(plain); pi = len(me.materials) - 1
mz_ = LM["mouth"]["center"][2]
n_pl = 0
for p in me.polygons:
    if p.material_index == 0 and (ai.matrix_world @ p.center).z < mz_ - 0.05:
        p.material_index = pi; n_pl += 1
skin_mat.name = "ZEPETO_Face"
print("[pack] 嘴巴以下 %d 面改用單純材質 ZEPETO_Skin" % n_pl)
ai.name = "Head"; me.name = "Head"


def separate(cls_id, name, mat_name):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = ai; ai.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(ai.data); bm.faces.ensure_lookup_table()
    for f in bm.faces:
        f.select = False
    for e in bm.edges:
        e.select = False
    for v in bm.verts:
        v.select = False
    cur = [f for f in bm.faces if FC.get(f.index) == cls_id]
    for f in cur:
        f.select = True
    bmesh.update_edit_mesh(ai.data)
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    new = next(o for o in bpy.context.selected_objects if o is not ai)
    new.name = name; new.data.name = name
    mt = plain_copy(mat_name)
    for s_ in new.material_slots:
        s_.material = mt
    print("[pack] 切出 %s：%d 面、%d 點、形態鍵 %d" % (name, len(new.data.polygons), len(new.data.vertices),
          len(new.data.shape_keys.key_blocks) if new.data.shape_keys else 0))
    return new


FC = {i: int(c) for i, c in enumerate(face_cls)}
hair_o = separate(1, "Hair", "ZEPETO_Hair")
# 頭髮背面畫成髮色：AI 生成的頭髮是單層殼，長髮往後推（hair_fit）之後內側露出來，內側的貼圖是雜色（右肩一塊黑白斑駁）
hm_ = hair_o.material_slots[0].material; nt_ = hm_.node_tree
bs_ = next(n for n in nt_.nodes if n.type == 'BSDF_PRINCIPLED')
src_ = bs_.inputs['Base Color'].links[0].from_socket
g_ = nt_.nodes.new('ShaderNodeNewGeometry'); mx_ = nt_.nodes.new('ShaderNodeMix'); mx_.data_type = 'RGBA'
mx_.inputs['B'].default_value = (*(np.array(HAIR_RGB) ** 2.2 * 0.8), 1)
# 頭髮物件上偏亮的貼圖（AI 在頭髮殼內側、原本被脖子擋住的地方畫了膚色；往後推就露出來，右肩一片斑駁）也換成髮色；
#   頭髮本身的反光亮度 < 0.3，不受影響
bw_ = nt_.nodes.new('ShaderNodeRGBToBW'); nt_.links.new(src_, bw_.inputs['Color'])
mr_ = nt_.nodes.new('ShaderNodeMapRange'); mr_.interpolation_type = 'SMOOTHSTEP'
mr_.inputs['From Min'].default_value, mr_.inputs['From Max'].default_value = 0.3, 0.45
nt_.links.new(bw_.outputs[0], mr_.inputs['Value'])
mxf_ = nt_.nodes.new('ShaderNodeMath'); mxf_.operation = 'MAXIMUM'
nt_.links.new(g_.outputs['Backfacing'], mxf_.inputs[0]); nt_.links.new(mr_.outputs['Result'], mxf_.inputs[1])
# 頭髮邊緣幾圈也畫成髮色（點屬性 edge_w，下面 hair_edge_w() 算）：靠近邊緣的貼圖是 AI 的過渡色（棕、灰、淺色雜點），
#   邊緣一露出來就是一圈碎邊（身體端近照：耳朵後緣一圈深色帶雜點、耳垂後方頭髮內側貼脖子一條棕黑毛邊）
at_ = nt_.nodes.new('ShaderNodeAttribute'); at_.attribute_name = "edge_w"; at_.attribute_type = 'GEOMETRY'
mxe_ = nt_.nodes.new('ShaderNodeMath'); mxe_.operation = 'MAXIMUM'
nt_.links.new(mxf_.outputs[0], mxe_.inputs[0]); nt_.links.new(at_.outputs['Fac'], mxe_.inputs[1])
# 比髮色明顯偏暖（紅減藍比髮色多 0.02～0.06，線性色）的貼圖也畫成髮色：頭髮內層有 AI 畫的棕色、暗粉紅過渡色（膚色陰影），
#   亮度不高、上面「偏亮」那條抓不到（身體端近照：右肩高度兩層頭髮中間一塊棕色三角＋粉紅小點）。跟這個人的髮色比，棕髮不會被誤換
sep_ = nt_.nodes.new('ShaderNodeSeparateColor'); nt_.links.new(src_, sep_.inputs[0])
hl_ = np.array(HAIR_RGB) ** 2.2
wm_ = nt_.nodes.new('ShaderNodeMath'); wm_.operation = 'SUBTRACT'
nt_.links.new(sep_.outputs[0], wm_.inputs[0]); nt_.links.new(sep_.outputs[2], wm_.inputs[1])
mrw_ = nt_.nodes.new('ShaderNodeMapRange'); mrw_.interpolation_type = 'SMOOTHSTEP'
mrw_.inputs['From Min'].default_value = float(hl_[0] - hl_[2]) + 0.02; mrw_.inputs['From Max'].default_value = float(hl_[0] - hl_[2]) + 0.06
nt_.links.new(wm_.outputs[0], mrw_.inputs['Value'])
mxw_ = nt_.nodes.new('ShaderNodeMath'); mxw_.operation = 'MAXIMUM'
nt_.links.new(mxe_.outputs[0], mxw_.inputs[0]); nt_.links.new(mrw_.outputs['Result'], mxw_.inputs[1])
nt_.links.new(mxw_.outputs[0], mx_.inputs['Factor']); nt_.links.new(src_, mx_.inputs['A']); nt_.links.new(mx_.outputs[2], bs_.inputs['Base Color'])
# 切掉頭髮後 Head 的面編號變了：重算耳朵的面（照點的位置找回原本的耳朵點）
from mathutils.kdtree import KDTree
kd = KDTree(int(ear.sum()))
for j, i in enumerate(np.where(ear)[0]):
    kd.insert(P[i].tolist(), int(i))
kd.balance()
mw = ai.matrix_world
FC = {}
for p in ai.data.polygons:
    if p.material_index != 0:
        continue
    n_e = 0
    for v in p.vertices:
        co, idx, d = kd.find((mw @ ai.data.vertices[v].co)[:])
        n_e += d < 1e-5
    FC[p.index] = 2 if n_e > len(p.vertices) / 2 else 0
ears_o = separate(2, "Ears", "ZEPETO_Ears")
for o in (hair_o, ears_o):
    o.parent = ai.parent
# 耳朵以下的細碎髮絲碎片刪掉：AI 生成的細髮絲斷成很多小塊（新娘 14 塊、每塊 4～17 點），耳朵以下那 9 塊沿脖子、肩膀兩側
#   排成一條虛線，長髮避開身體時有的被推進身體（身體端近照：斜穿脖子和肩膀的細黑線）。耳朵以上的（臉旁細髮絲）留著
ISL_MAX = 40
ear_low = min((ears_o.matrix_world @ v.co).z for v in ears_o.data.vertices) if ears_o and len(ears_o.data.vertices) else -9
kd_ear = None
if ears_o and len(ears_o.data.vertices):
    from mathutils.kdtree import KDTree as _KD
    kd_ear = _KD(len(ears_o.data.vertices))
    for i_, v_ in enumerate(ears_o.data.vertices):
        kd_ear.insert(ears_o.matrix_world @ v_.co, i_)
    kd_ear.balance()
bmh = bmesh.new(); bmh.from_mesh(hair_o.data); bmh.verts.ensure_lookup_table()
mwh = hair_o.matrix_world
seen_ = set(); kill = []
for v0 in bmh.verts:
    if v0.index in seen_:
        continue
    comp = [v0]; seen_.add(v0.index); k_ = 0
    while k_ < len(comp):
        for e in comp[k_].link_edges:
            u = e.other_vert(comp[k_])
            if u.index not in seen_:
                seen_.add(u.index); comp.append(u)
        k_ += 1
    zmax_ = max((mwh @ v.co).z for v in comp); ymean_ = sum((mwh @ v.co).y for v in comp) / len(comp)
    #   耳朵旁邊、後面的也刪（y 在臉前 −0.3 以後）：耳朵上緣、後緣的黑色碎塊（身體端近照）；臉前面的細髮絲（y < −0.3）留著
    if len(comp) < ISL_MAX and (zmax_ < ear_low or ymean_ > -0.3):
        kill += comp
if kill:
    bmesh.ops.delete(bmh, geom=kill, context='VERTS')
    bmh.to_mesh(hair_o.data); hair_o.data.update()
bmh.free()
print("[pack] 耳朵以下的細碎髮絲碎片（< %d 點）刪掉 %d 點" % (ISL_MAX, len(kill)))

# ── 耳朵調回膚色（2026-10-14）：AI 可能把耳朵內側、耳後那片皮膚畫成偏紅（攝影師 v2：耳朵紅−綠 0.32、臉頰 0.20），
#    側面、背面看像耳朵發紅。關掉透光幾乎沒差 → 是貼圖畫的，不是材質。
#    材質裡做（不改貼圖檔）：比這張臉的膚色明顯偏紅的地方，往膚色混回去最多 EAR_TONE（保留明暗、留一點粉）。
#    Ears 整個物件都做；Head 只做耳朵附近（點屬性 ear_zone：離耳朵 0.06 內 1、0.18 外 0）→ 嘴唇、腮紅不受影響
EAR_TONE = 0.7
EAR_RED_LO, EAR_RED_HI = 0.04, 0.14      # 比膚色多紅（線性色的紅−綠）這麼多開始混、混到最多
def _skin_ref():
    tx_ = next(n for n in skin_mat.node_tree.nodes if n.type == 'TEX_IMAGE')
    W_, H_ = tx_.image.size
    px_ = np.array(tx_.image.pixels[:], np.float32).reshape(H_, W_, 4)[..., :3]
    uvd = me.uv_layers.active.data; cols = []
    for p_ in me.polygons:
        if p_.material_index != 0 or (ai.matrix_world @ p_.center).y > -0.2:
            continue
        for li_ in p_.loop_indices:
            u_, v_ = uvd[li_].uv
            cols.append(px_[min(H_ - 1, int(v_ * H_)), min(W_ - 1, int(u_ * W_))])
    return np.median(np.array(cols), 0) ** 2.2   # 貼圖是 sRGB → 跟材質節點裡一樣用線性色比
SKIN_LIN = _skin_ref()
SKIN_LUM = float(SKIN_LIN @ np.array([0.2126, 0.7152, 0.0722]))


def add_ear_tone(mat, gate_attr=None, force_attr=None):
    nt = mat.node_tree
    bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    src = bs.inputs['Base Color'].links[0].from_socket
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(src, sep.inputs[0])
    rg = nt.nodes.new('ShaderNodeMath'); rg.operation = 'SUBTRACT'
    nt.links.new(sep.outputs[0], rg.inputs[0]); nt.links.new(sep.outputs[1], rg.inputs[1])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.interpolation_type = 'SMOOTHSTEP'
    r0 = float(SKIN_LIN[0] - SKIN_LIN[1])
    mr.inputs['From Min'].default_value, mr.inputs['From Max'].default_value = r0 + EAR_RED_LO, r0 + EAR_RED_HI
    mr.inputs['To Max'].default_value = EAR_TONE
    nt.links.new(rg.outputs[0], mr.inputs['Value'])
    fac = mr.outputs['Result']
    if gate_attr:
        at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = gate_attr; at.attribute_type = 'GEOMETRY'
        mu = nt.nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'
        nt.links.new(fac, mu.inputs[0]); nt.links.new(at.outputs['Fac'], mu.inputs[1]); fac = mu.outputs[0]
    if force_attr:   # 改歸耳朵的黑色碎塊：整個畫成膚色（亮度用膚色的，不是黑色的）
        fa = nt.nodes.new('ShaderNodeAttribute'); fa.attribute_name = force_attr; fa.attribute_type = 'GEOMETRY'
        mxa = nt.nodes.new('ShaderNodeMath'); mxa.operation = 'MAXIMUM'
        nt.links.new(fac, mxa.inputs[0]); nt.links.new(fa.outputs['Fac'], mxa.inputs[1]); fac = mxa.outputs[0]
    bw = nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(src, bw.inputs['Color'])
    if force_attr:
        lmix = nt.nodes.new('ShaderNodeMix'); lmix.data_type = 'FLOAT'
        nt.links.new(fa.outputs['Fac'], lmix.inputs['Factor']); nt.links.new(bw.outputs[0], lmix.inputs['A'])
        lmix.inputs['B'].default_value = SKIN_LUM * 0.95
        lum_out = lmix.outputs['Result']
    else:
        lum_out = bw.outputs[0]
    sc = nt.nodes.new('ShaderNodeVectorMath'); sc.operation = 'SCALE'
    sc.inputs[0].default_value = tuple(float(c) / SKIN_LUM for c in SKIN_LIN)
    nt.links.new(lum_out, sc.inputs['Scale'])     # 膚色 × 這一點的亮度：保留耳朵的明暗
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    nt.links.new(fac, mx.inputs['Factor']); nt.links.new(src, mx.inputs['A']); nt.links.new(sc.outputs[0], mx.inputs['B'])
    nt.links.new(mx.outputs[2], bs.inputs['Base Color'])


if ears_o and len(ears_o.data.vertices) and kd_ear is not None:
    add_ear_tone(ears_o.material_slots[0].material, force_attr="ear_fix")
    hz = np.array([kd_ear.find(ai.matrix_world @ v.co)[2] for v in me.vertices])
    w_ear = 1 - np.clip((hz - 0.06) / 0.12, 0, 1)   # 離耳朵 0.06 內全做、0.18 外不做（0.04～0.12 時耳後下半那片紅沒蓋到）
    w_ear = w_ear * w_ear * (3 - 2 * w_ear)
    at_ = me.attributes.get("ear_zone") or me.attributes.new("ear_zone", 'FLOAT', 'POINT')
    at_.data.foreach_set("value", w_ear.astype(np.float32))
    for m_ in (skin_mat, plain):
        add_ear_tone(m_, "ear_zone")
    print("[pack] 耳朵調回膚色：膚色（線性）%s；Ears 整個、Head 耳朵附近 %d 點（ear_zone）" % (np.round(SKIN_LIN, 3), int((w_ear > 0).sum())))


# 頭髮和臉皮（Head、Ears）的交界抹順：頭髮是沿 AI 三角形切出來的，交界一排鋸齒，上色後是一排深色三角
#   （使用者 2026-10-14 圈出耳朵前面的鬢角、耳垂下方）。交界上的點兩邊各一份（切成不同物件），兩份一起移才不會裂開；
#   往內 3 圈跟著移一點（不然三角形摺起來）；開口邊上、但不在頭髮交界的點不動（Head 跟 Ears 的交界會裂開）；
#   形態鍵保留原本的位移（基底和每個形態鍵加同一個位移）。
#   只抹耳朵頂端到下巴往下 0.12、兩側（|x| > 0.6 個眼距；下巴以下、後腦不論左右）的交界：額頭瀏海的髮尖不動
#   （新娘只抹眼睛以下時，鬢角上半段還留幾個三角；只算兩側時，脖子旁邊夾在脖子和長髮之間的那片頭髮被排除，留一條鋸齒毛邊）
SEAM_IT = 12


def seam_smooth():
    from mathutils.kdtree import KDTree
    objs = [o for o in (ai, hair_o, ears_o) if o]
    bms = {}
    for o in objs:
        b_ = bmesh.new(); b_.from_mesh(o.data); b_.verts.ensure_lookup_table(); bms[o.name] = b_
    mwo = {o.name: o.matrix_world.copy() for o in objs}
    skin = [(o.name, v.index, mwo[o.name] @ v.co) for o in objs if o is not hair_o for v in bms[o.name].verts if v.is_boundary]
    kd_ = KDTree(len(skin))
    for i, (_, _, p) in enumerate(skin):
        kd_.insert(p, i)
    kd_.balance()
    hb = bms[hair_o.name]
    ear_top = max((ears_o.matrix_world @ v.co).z for v in ears_o.data.vertices) if ears_o else ez
    seam = {}
    for v in hb.verts:
        if not v.is_boundary:
            continue
        p = mwo[hair_o.name] @ v.co
        if p.z > ear_top or p.z < chin_z - 0.12 or (abs(p.x) < 0.6 * U and p.z > chin_z and p.y < -0.1):   # 下巴往下 0.12 以下是胸像（身體端藏掉），抹那裡只會把肩膀上的頭髮拉歪（新娘移 0.12）；
            # 不抹的只有臉前面中間（額頭瀏海）—— 後腦中間要抹：短髮的後髮際線露在外面（攝影師 v2 後頸一排深色鋸齒）
            continue
        hits = kd_.find_range(p, 1e-5)
        if hits:
            seam[v.index] = [(skin[i][0], skin[i][1]) for _, i, _ in hits]
    nb = {i: [] for i in seam}
    for e in hb.edges:
        if e.is_boundary:
            a_, b2 = e.verts[0].index, e.verts[1].index
            if a_ in seam and b2 in seam:
                nb[a_].append(b2); nb[b2].append(a_)
    mov = [i for i in seam if len(nb[i]) == 2]   # 鏈的兩端、分岔點不動
    X0 = {i: mwo[hair_o.name] @ hb.verts[i].co for i in seam}
    X = dict(X0)
    for _ in range(SEAM_IT):
        Xn = dict(X)
        for i in mov:
            a_, b2 = nb[i]
            Xn[i] = X[i] * 0.5 + (X[a_] + X[b2]) * 0.25
        X = Xn
    dW = {i: X[i] - X0[i] for i in mov}
    per = {o.name: {} for o in objs}
    for i, d in dW.items():
        per[hair_o.name][i] = d
        for on, vi in seam[i]:
            per[on][vi] = d
    mx = 0.0
    if dW:
        iw = max(dW, key=lambda i: dW[i].length)
        print("[pack]   交界抹順移最多的點：%s 移 %.3f" % (tuple(round(c, 3) for c in X0[iw]), dW[iw].length))
    for o in objs:
        b_ = bms[o.name]; dd = dict(per[o.name])
        frontier = set(dd)
        for f in (0.6, 0.35, 0.15):
            acc = {}
            for vi in frontier:
                for e in b_.verts[vi].link_edges:
                    u = e.other_vert(b_.verts[vi])
                    if u.index in dd or u.is_boundary:
                        continue
                    acc.setdefault(u.index, []).append(dd[vi])
            new = {u: sum(ds, Vector()) / len(ds) * f for u, ds in acc.items()}
            dd.update(new); frontier = set(new)
        inv = mwo[o.name].inverted().to_3x3()
        layers = list(b_.verts.layers.shape.values())
        for vi, d in dd.items():
            dl = inv @ d
            v = b_.verts[vi]
            v.co += dl
            for L in layers:
                v[L] = v[L] + dl
            mx = max(mx, d.length)
        b_.to_mesh(o.data); o.data.update(); b_.free()
    print("[pack] 頭髮和臉皮交界抹順：%d 點（z %.3f～%.3f、兩側），最多移 %.3f" % (len(mov), chin_z - 0.12, ear_top, mx))


from mathutils import Vector
seam_smooth()


def hair_edge_w():
    """頭髮開口邊（只連一個面的邊）往內 3 圈的點屬性 edge_w（1、1、0.6、0.3）：材質照這個把邊緣畫成髮色。
    範圍同交界抹順：耳朵頂端以下、兩側；下巴以下不論左右（額頭瀏海的髮尖不動）"""
    from collections import defaultdict
    mh = hair_o.data; n_ = len(mh.vertices)
    cnt_ = defaultdict(int)
    for p in mh.polygons:
        for ek in p.edge_keys:
            cnt_[ek] += 1
    adj_ = [[] for _ in range(n_)]
    for e in mh.edges:
        a_, b_ = e.vertices; adj_[a_].append(b_); adj_[b_].append(a_)
    ring_ = np.full(n_, 99)
    fr_ = list({v for ek, c in cnt_.items() if c == 1 for v in ek})
    ring_[fr_] = 0
    for d in range(1, 4):
        nx_ = []
        for v in fr_:
            for u in adj_[v]:
                if ring_[u] > d:
                    ring_[u] = d; nx_.append(u)
        fr_ = nx_
    Pw = np.array([hair_o.matrix_world @ v.co for v in mh.vertices])
    ear_top = max((ears_o.matrix_world @ v.co).z for v in ears_o.data.vertices) if ears_o else ez
    region = (Pw[:, 2] < ear_top + 0.05) & ((np.abs(Pw[:, 0]) > 0.6 * U) | (Pw[:, 2] < chin_z) | (Pw[:, 1] > -0.1))  # 後腦中間也畫（短髮後髮際線）
    w = np.select([ring_ <= 1, ring_ == 2, ring_ == 3], [1.0, 0.6, 0.3], 0.0) * region
    at = mh.attributes.get("edge_w") or mh.attributes.new("edge_w", 'FLOAT', 'POINT')
    at.data.foreach_set("value", w.astype(np.float32))
    print("[pack] 頭髮邊緣畫成髮色：%d 點（耳朵頂端以下、兩側；下巴以下全部）" % int((w > 0).sum()))


hair_edge_w()
# 脖子的水平邊改由 neck_ring.py 切（從接口環往上每 0.02；2026-10-14 前在這裡從下巴往下切，高度跟身體切口差約 1 cm 的一半）
print("[pack] Head 剩 %d 面" % len(ai.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
