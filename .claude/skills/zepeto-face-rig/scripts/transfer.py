# 第 5 版：轉移表情＋切嘴縫＋自建口腔袋（從唇縫往內長 8 圈：2 圈圓潤唇緣＋6 圈口腔，跟嘴唇相連）＋借模板牙齒舌頭
#   第 4 版借模板口腔：跟 AI 嘴唇接不上、張大時底板折成尖峰、舌頭不跟下顎（診斷見 diag_bind.py、open_series.py）
# 用法：AI_BLEND=<AI 頭 .blend> AI_LM=<landmarks.json> blender -b <籠子 head_arkit.blend> -P transfer.py -- <out.blend> [smooth_iters]
import bpy, bmesh, sys, numpy as np
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
from mathutils import Vector
args = sys.argv[sys.argv.index("--") + 1:]
OUT_BLEND = args[0]
SMOOTH = int(args[1]) if len(args) > 1 else 3
import os as _os0
AI_BLEND = _os0.environ["AI_BLEND"]  # AI 頭（後處理後）
AI_LM = _os0.environ["AI_LM"]  # AI 頭的五官
sc = bpy.context.scene

head = bpy.data.objects["Head"]; hm = head.data
hm.calc_loop_triangles()
tris = np.array([t.vertices[:] for t in hm.loop_triangles], dtype=np.int64)
tri_mat = np.array([hm.polygons[t.polygon_index].material_index for t in hm.loop_triangles])
mat_names = [m.name for m in hm.materials]
LIP = mat_names.index("ZEPETO_Lips"); INNER = mat_names.index("Mouth_Inner")
kbs = hm.shape_keys.key_blocks
def co_of(kb):
    a = np.empty(len(hm.vertices) * 3); kb.data.foreach_get("co", a); return a.reshape(-1, 3)
P0 = co_of(kbs["Basis"])
jaw = np.linalg.norm(co_of(kbs["jawOpen"]) - P0, axis=1)
tri_jaw = jaw[tris].mean(1)
is_mouth_tri = np.isin(tri_mat, [LIP, INNER])
jmax = tri_jaw[is_mouth_tri].max()
lower_tri = is_mouth_tri & (tri_jaw > 0.45 * jmax)
upper_tri = is_mouth_tri & (tri_jaw < 0.2 * jmax)
print("mouth tris", is_mouth_tri.sum(), "upper", upper_tri.sum(), "lower", lower_tri.sum())

def make_bvh(mask):
    idx = np.nonzero(mask)[0]
    return BVHTree.FromPolygons([Vector(p) for p in P0], tris[idx].tolist(), all_triangles=True), idx
bvh_all, idx_all = make_bvh(np.ones(len(tris), bool))
bvh_up, idx_up = make_bvh(upper_tri | ~is_mouth_tri)   # 上唇那側：上唇＋一般皮膚
bvh_lo, idx_lo = make_bvh(lower_tri | ~is_mouth_tri)
# 嘴唇表面的點只綁「朝前」的模板三角形：綁到模板嘴唇內面（朝嘴裡）的點，張嘴時跟旁邊綁到前面的點動法不同 → 凹凸
_tn = np.cross(P0[tris[:, 1]] - P0[tris[:, 0]], P0[tris[:, 2]] - P0[tris[:, 0]])
_tny = _tn[:, 1] / np.maximum(np.linalg.norm(_tn, axis=1), 1e-12)
FRONT_T = _tny < 0.2
bvh_upF, idx_upF = make_bvh((upper_tri | ~is_mouth_tri) & FRONT_T)
bvh_loF, idx_loF = make_bvh((lower_tri | ~is_mouth_tri) & FRONT_T)

with bpy.data.libraries.load(AI_BLEND, link=False) as (src, dst):
    dst.objects = ["ZEPETO_Head"]
ai = dst.objects[0]; ai.name = "AI_Driven"
# 拿掉細分修改器：細分會把凸起的嘴唇往內縮幾毫米，「推到皮後」用的是細分前的形狀 → 牙齒、口腔袋在畫面上跑到嘴唇前面
#   （近照：閉嘴時唇縫上一條灰白牙齒＋一片浮著的粉色長方形）。AI 頭 1.1 萬點，不細分也夠圓
for m_ in list(ai.modifiers):
    if m_.type == 'SUBSURF':
        ai.modifiers.remove(m_)
sc.collection.objects.link(ai)
am = ai.data

# --- 1. 嘴縫：照 AI 畫好的唇線（兩嘴角＋中間的拋物線）切，不再照模板三角形分類（只分到一條細線、其餘亂綁 → 張嘴時碎片）---
import json as _json
LMA = _json.load(open(AI_LM, encoding="utf-8"))
mL, mR, mC = LMA["mouth"]["L"], LMA["mouth"]["R"], LMA["mouth"]["center"]
hw = (mL[0] - mR[0]) / 2
import os as _os
CUT = float(_os.environ.get("MOUTH_CUT", 0.8))  # 嘴縫切到嘴寬的幾成（0.9 時嘴角沒切開、張嘴被上下拉成尖角）
xc = (mL[0] + mR[0]) / 2
zc = mC[2]; zk = (mL[2] + mR[2]) / 2
def z_s(x):
    return zc + (zk - zc) * min(1.0, ((x - xc) / hw) ** 2)
bm = bmesh.new(); bm.from_mesh(am)
def in_box(f, pad=0.1):
    c = f.calc_center_median()
    return c.y < -0.3 and abs(c.x - xc) < hw * 1.25 and abs(c.z - z_s(c.x)) < pad
box = [f for f in bm.faces if in_box(f, 0.06)]
bmesh.ops.subdivide_edges(bm, edges=list({e for f in box for e in f.edges}), cuts=2, use_grid_fill=True)
# 細分區外圍的面只多了點、變成五邊以上的多邊形 → 一變形就自己折出一道摺（嘟嘴時下巴正中一個尖凹窩）→ 拆成三角形
_ng = [f for f in bm.faces if len(f.verts) > 4]
bmesh.ops.triangulate(bm, faces=_ng, quad_method='BEAUTY', ngon_method='BEAUTY')
print("[transfer] 細分區外圍多邊形拆三角 %d 面" % len(_ng))
bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
# 細分出來的點落在原本的平面三角形上，平滑著色後看得出折痕 → 稍微抹圓（區域邊界不動）
sv_ = [v for f in bm.faces if in_box(f, 0.05) for v in f.verts]
sv_ = list({v for v in sv_ if all(in_box(f, 0.07) for f in v.link_faces)})
for _ in range(3):
    bmesh.ops.smooth_vert(bm, verts=sv_, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
# 嘴角的小凹痕（AI 網格本來就有，張嘴一拉就變成往臉頰的折線）→ 嘴角周圍抹平，只動形狀不動貼圖
cv_ = [v for v in bm.verts if v.co.y < -0.3 and min((Vector(mL) - v.co).length, (Vector(mR) - v.co).length) < 0.08]
for _ in range(int(_os.environ.get("CORNER_SMOOTH", 6))):
    bmesh.ops.smooth_vert(bm, verts=cv_, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
print("[transfer] 嘴角抹平 %d 點" % len(cv_))
fcls = {}
for f in bm.faces:
    if in_box(f):
        c = f.calc_center_median()
        fcls[f] = "up" if c.z > z_s(c.x) else "lo"
slit = [e for e in bm.edges if len(e.link_faces) == 2 and abs(e.verts[0].co.x - xc) < hw * CUT and abs(e.verts[1].co.x - xc) < hw * CUT  # 嘴角兩端留一小段不切（切到底會有小凹洞）
        and {fcls.get(e.link_faces[0]), fcls.get(e.link_faces[1])} == {"up", "lo"}]
print("slit edges", len(slit))
bmesh.ops.split_edges(bm, edges=slit)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table(); bm.verts.index_update()
side = {}
lo_faces = {f for f, c in fcls.items() if c == "lo" and f.is_valid}
for v in bm.verts:
    cls = {fcls.get(f) for f in v.link_faces}
    if cls == {"up"}: side[v.index] = "up"
    elif cls == {"lo"}: side[v.index] = "lo"
    elif {"up", "lo"} <= cls: side[v.index] = "mid"  # 嘴縫外側、上下唇交界上的點（沒切開）：取兩側平均，不然隨機綁到上唇或下唇、張嘴時扯出折線
# ── 1b. 嘴縫抹順＋唇內側厚度（2026-10-13 近照：切口沿三角面邊緣是鋸齒、張嘴看到 AI 皮的背面）──
bnd = [e for e in bm.edges if e.is_boundary and side.get(e.verts[0].index) in ("up", "lo") and side.get(e.verts[1].index) in ("up", "lo")]
bv = {v for e in bnd for v in e.verts}
for v in bv:  # 切口的點貼齊唇線
    v.co.z = z_s(v.co.x)
# 唇縫上下兩排點抹順：切口點貼齊弧線後，旁邊的三角面被拉歪變細長，光影出現一排鋸齒白邊
band_ = [v for v in bm.verts if v not in bv and side.get(v.index) in ("up", "lo") and v.co.y < -0.4 and abs(v.co.z - z_s(v.co.x)) < 0.022]
for _ in range(4):
    bmesh.ops.smooth_vert(bm, verts=band_, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
for _ in range(4):  # 沿切口曲線抹順（兩端嘴角不動）
    new_co = {}
    for v in bv:
        nb = [e.other_vert(v) for e in v.link_edges if e in bnd]
        if len(nb) == 2:
            new_co[v] = v.co * 0.5 + (nb[0].co + nb[1].co) * 0.25
    for v, c in new_co.items():
        v.co = c
# ── 1c. 自建口腔袋：唇縫的洞（上唇切口＋下唇切口＋兩端嘴角，一整圈）往內長 8 圈，最後收口 ──
#   第 1、2 圈＝圓潤唇緣（AI 唇縫的顏色）；第 3 圈貼在牙齒前面（照牙弓），往後一路包住牙齒、舌頭；最後幾圈收小、補面封口。
#   每一圈的截面是圓角矩形（超橢圓），寬高照牙齒、牙齦、舌頭量出來，所以牙齒不會穿出口腔
loop_e = [e for e in bm.edges if e.is_boundary and all(side.get(v.index) in ("up", "lo", "mid") and v.co.y < -0.35 and abs(v.co.x - xc) < hw for v in e.verts)]
loop_v = list({v for e in loop_e for v in e.verts})
_deg = {v: sum(1 for e in v.link_edges if e in set(loop_e)) for v in loop_v}
print("[pocket] 唇縫一圈 %d 點、%d 邊；不是 2 條邊的點 %d" % (len(loop_v), len(loop_e), sum(1 for d in _deg.values() if d != 2)))
def _objw(n):
    o_ = bpy.data.objects[n]; return np.array([o_.matrix_world @ v_.co for v_ in o_.data.vertices])
_TG = np.vstack([_objw(n) for n in ("upper_teeth", "bottom_teeth", "upper_gum", "bottom_gum")])
_TT = _objw("Tongue")
_ax = np.array([x for x in np.arange(-0.14, 0.141, 0.02) if (np.abs(_TG[:, 0] - x) < 0.015).any()])
_ay = np.array([_TG[np.abs(_TG[:, 0] - x) < 0.015, 1].min() for x in _ax])
def arch_y(x):  # 牙弓前緣（牙齒＋牙齦最前面），兩端照斜率往外延
    if x < _ax[0]: return _ay[0] + (_ay[0] - _ay[1]) / (_ax[0] - _ax[1]) * (x - _ax[0])
    if x > _ax[-1]: return _ay[-1] + (_ay[-1] - _ay[-2]) / (_ax[-1] - _ax[-2]) * (x - _ax[-1])
    return float(np.interp(x, _ax, _ay))
UPPER_TEETH_DROP = 0.025  # 下面會把上排牙齒、牙齦往下移這麼多
zm0 = float(np.mean([v.co.z for v in loop_v]))
Z_TOP = _objw("upper_gum")[:, 2].max() - UPPER_TEETH_DROP + 0.03   # 上顎
Z_BOT = min(_objw("bottom_gum")[:, 2].min(), _TT[:, 2].min()) - 0.03   # 口腔底
A_W = max(abs(_TG[:, 0]).max() + 0.035, hw * 1.05)                     # 左右半寬
H_UP, H_LO = Z_TOP - zm0, zm0 - Z_BOT
Y_BACK = _TT[:, 1].max() + 0.03
print("[pocket] 截面 半寬 %.3f、上 %.3f、下 %.3f、最深 y %.3f" % (A_W, H_UP, H_LO, Y_BACK))
ux = max(abs(v.co.x - xc) for v in loop_v)
TH = {}
for v in loop_v:
    u = max(-1.0, min(1.0, (v.co.x - xc) / ux))
    s_ = side.get(v.index)
    TH[v] = (np.arccos(u) if s_ == "up" else -np.arccos(u) if s_ == "lo" else (0.0 if u > 0 else np.pi))
def sec_xz(th, scale, n=3.0):
    c, s_ = np.cos(th), np.sin(th)
    x = xc + A_W * scale * np.sign(c) * abs(c) ** (2 / n)
    z = zm0 + (H_UP if s_ > 0 else H_LO) * scale * np.sign(s_) * abs(s_) ** (2 / n)
    return x, z
# 每一圈：("rim", 往後, 往外) 或 ("sec", y 的算法, 截面大小)
# 唇緣第 2 圈：上唇往下、下唇往上收 0.004（往外張 0.006 時，嘴角附近下唇表面比唇縫高，唇緣穿到下唇前面、看得到背面：攝影師）
PROFILE = [("rim", 0.008, 0.0), ("rim", 0.02, float(_os.environ.get("RIM_AWAY", -0.004))),
           ("sec", "arch-0.012", 0.85, "slitx"), ("sec", "arch+0.03", 1.0),
           ("sec", -0.40, 1.0), ("sec", -0.29, 0.95), ("sec", Y_BACK - 0.03, 0.7), ("sec", Y_BACK, 0.3)]
uvl_ = bm.loops.layers.uv.active
UV0 = {}
for v in loop_v:
    for l_ in v.link_loops:
        UV0[v] = l_[uvl_].uv.copy(); break
lipin = bpy.data.materials.new("LipInner")  # 口腔袋材質（名字沿用：其他工具照這個名字找）
bsl = next(n for n in lipin.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
bsl.inputs['Roughness'].default_value = 0.5
_pa = lipin.node_tree.nodes.new("ShaderNodeAttribute"); _pa.attribute_name = "pocket_t"
_pr = lipin.node_tree.nodes.new("ShaderNodeMix"); _pr.data_type = 'RGBA'
_pr.inputs['A'].default_value = (0.42, 0.12, 0.13, 1); _pr.inputs['B'].default_value = (0.1, 0.02, 0.025, 1)  # 越深越暗
lipin.node_tree.links.new(_pa.outputs['Fac'], _pr.inputs['Factor']); lipin.node_tree.links.new(_pr.outputs[2], bsl.inputs['Base Color'])
am.materials.append(lipin)
MAT_P = len(am.materials) - 1
cur_e, cur_map = loop_e, {v: v for v in loop_v}
POCK = {}       # 口腔袋的點 → (原本唇縫的點, 第幾圈)
all_f = []
for k, spec in enumerate(PROFILE, start=1):
    ret = bmesh.ops.extrude_edge_only(bm, edges=cur_e)
    nv_ = [g for g in ret["geom"] if isinstance(g, bmesh.types.BMVert)]
    nf_ = [g for g in ret["geom"] if isinstance(g, bmesh.types.BMFace)]
    ne_ = [g for g in ret["geom"] if isinstance(g, bmesh.types.BMEdge)]
    new_map = {}
    for v in nv_:
        src = next(e.other_vert(v) for e in v.link_edges if e.other_vert(v) in cur_map)
        o = cur_map[src]; new_map[v] = o; POCK[v] = (o, k)
        s_ = side.get(o.index)
        if spec[0] == "rim":
            away = spec[2] * (1 if s_ == "up" else -1 if s_ == "lo" else 0)
            v.co = o.co + Vector((0, spec[1], away))
            # （試過沿皮膚法線往裡捲：閉嘴時上下唇法線都朝前，上下兩片唇緣在縫裡交叉、從前面看得到，已退回；
            #   嘴角下唇往後縮、唇緣跑到前面的問題，改在下面「推到皮後」處理）
        else:
            x, z = sec_xz(TH[o], spec[2])
            if len(spec) > 3 and spec[3] == "slitx":  # 左右寬度跟著嘴縫（不比嘴縫末端寬）：比嘴縫寬的話，會跑到嘴角沒切開那段皮膚正後方，嘴角一動就穿出（攝影師驚訝時）
                x = o.co.x
            if isinstance(spec[1], str):
                y = arch_y(x) + float(spec[1][4:])
            else:
                y = spec[1]
            v.co = Vector((x, max(y, o.co.y + 0.02 * k), z))
    for f in nf_:
        f.material_index = 0 if spec[0] == "rim" else MAT_P
        for l_ in f.loops:
            ov = new_map.get(l_.vert) or cur_map.get(l_.vert)
            if ov in UV0:
                l_[uvl_].uv = UV0[ov]
    all_f += nf_
    cur_e = [e for e in ne_ if e.verts[0] in new_map and e.verts[1] in new_map]
    cur_map = new_map
cap = bmesh.ops.contextual_create(bm, geom=cur_e)["faces"]
cap_t = bmesh.ops.triangulate(bm, faces=cap)["faces"]
for f in cap_t:
    f.material_index = MAT_P
all_f += cap_t
# 面的方向：跟相鄰的皮膚一致（唇縫那條邊，兩邊的面要一個順向、一個逆向走）
ok = bad = 0
for e in loop_e:
    fs = e.link_faces
    if len(fs) != 2: continue
    dirs = []
    for f in fs:
        for l_ in f.loops:
            if l_.edge == e: dirs.append(l_.vert)
    ok += dirs[0] != dirs[1]; bad += dirs[0] == dirs[1]
if bad > ok:
    bmesh.ops.reverse_faces(bm, faces=all_f)
print("[pocket] 長了 %d 圈、%d 面；方向 一致 %d／相反 %d%s" % (len(PROFILE), len(all_f), ok, bad, "（已翻面）" if bad > ok else ""))
bm.verts.index_update()
WALL_SRC = {}
POCK_K = {}
POCK_TH = {}
for v, (o, k) in POCK.items():
    side[v.index] = side.get(o.index)
    WALL_SRC[v.index] = o.index
    POCK_K[v.index] = k
    POCK_TH[v.index] = TH[o]
new_f = all_f
bm.to_mesh(am); bm.free()
am.update()
# AI 皮的背面（張嘴從開口看進去）一律畫成口腔深紅
mt = am.materials[0]; ntm = mt.node_tree
bsm = next(n for n in ntm.nodes if n.type == 'BSDF_PRINCIPLED')
src_sock = bsm.inputs['Base Color'].links[0].from_socket
geo = ntm.nodes.new('ShaderNodeNewGeometry')
mixb = ntm.nodes.new('ShaderNodeMix'); mixb.data_type = 'RGBA'
mixb.inputs['B'].default_value = (0.3, 0.06, 0.07, 1)
ntm.links.new(geo.outputs['Backfacing'], mixb.inputs['Factor']); ntm.links.new(src_sock, mixb.inputs['A'])
ntm.links.new(mixb.outputs[2], bsm.inputs['Base Color'])
nv = len(am.vertices)
sa = am.attributes.new("lip_side", 'INT', 'POINT')  # 除錯：1＝上唇側、2＝下唇側、0＝一般
sa.data.foreach_set("value", [1 if side.get(i) == "up" else 2 if side.get(i) == "lo" else 3 if side.get(i) == "mid" else 0 for i in range(nv)])
V = np.empty(nv * 3); am.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
print("verts", nv, "up", sum(1 for s in side.values() if s == "up"), "lo", sum(1 for s in side.values() if s == "lo"))
PK_I = np.array(sorted(WALL_SRC), dtype=np.int64)
PK_K = np.array([POCK_K[i] for i in PK_I]); PK_TH = np.array([POCK_TH[i] for i in PK_I])
_pt = np.zeros(nv, np.float32); _pt[PK_I] = np.clip((PK_K - 2) / (len(PROFILE) - 2), 0, 1)
am.attributes.new("pocket_t", 'FLOAT', 'POINT').data.foreach_set("value", _pt)
_pkk = np.zeros(nv, np.int32); _pkk[PK_I] = PK_K
am.attributes.new("pocket_k", 'INT', 'POINT').data.foreach_set("value", _pkk)  # 口腔袋第幾圈（0＝不是；1、2＝唇緣）：檢查工具用
# 口腔袋（第 3 圈以後）不能跑到臉皮前面：照附近皮膚最前面的深度往後推
from mathutils.kdtree import KDTree as _KD0
_skin = np.setdiff1d(np.where(V[:, 1] < -0.2)[0], PK_I)
_kd0 = _KD0(len(_skin))
for j, i in enumerate(_skin): _kd0.insert(Vector((V[i, 0], 0.0, V[i, 2])), int(i))
_kd0.balance()
_np0 = 0
for i, k in zip(PK_I, PK_K):
    # 第 3 圈以後：附近 0.03 內皮膚最前面＋0.012；唇緣（第 1、2 圈）：附近 0.012 內＋0.004
    #   （唇緣一律往正後方，嘴角附近下唇往後縮的話唇緣會跑到下唇前面、看得到背面：攝影師嘴角的洋紅小塊）
    r_, m_ = (0.03, 0.012) if k >= 3 else (0.012, 0.004)
    hits = _kd0.find_range(Vector((V[i, 0], 0.0, V[i, 2])), r_)
    if hits:
        fy = min(V[h[1], 1] for h in hits)
        if V[i, 1] < fy + m_:
            V[i, 1] = fy + m_; _np0 += 1
am.vertices.foreach_set("co", V.ravel())
print("[pocket] 口腔袋推到皮後 %d 點" % _np0)

# --- 2. 綁定（嘴巴附近照側別限制）---
tri_idx = np.empty(nv, np.int64); bary = np.empty((nv, 3))
for i, v in enumerate(V):
    s = side.get(i)
    if s in ("up", "mid", "lo") and i not in WALL_SRC:  # 嘴唇表面：只綁朝前的三角形
        bvh, idx = (bvh_upF, idx_upF) if s in ("up", "mid") else (bvh_loF, idx_loF)
    else:
        bvh, idx = (bvh_up, idx_up) if s in ("up", "mid") else (bvh_lo, idx_lo) if s == "lo" else (bvh_all, idx_all)
    loc, nor, ti, d = bvh.find_nearest(Vector(v))
    ti = idx[ti]; tri_idx[i] = ti
    a, b, c = (Vector(P0[j]) for j in tris[ti])
    w = barycentric_transform(loc, a, b, c, Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)))
    bary[i] = (w.x, w.y, w.z)

# 退化三角形（面積 0）算出的重心座標是 NaN → 抹順 40 次會擴散到整張臉、所有表情都壞（2026-10-13 一鍵產線第一次跑）
_bad = ~np.isfinite(bary).all(1)
bary[_bad] = 1 / 3
print("[transfer] 綁到退化三角形 %d 點（改用三角平均）" % int(_bad.sum()))
# 除錯：記下每個點綁到的模板三角形、距離、那個三角形的朝向（diag_bind.py 用）
_bd = np.zeros(nv); _bny = np.zeros(nv)
for i, v in enumerate(V):
    a_, b_, c_ = (P0[j] for j in tris[tri_idx[i]])
    q_ = a_ * bary[i, 0] + b_ * bary[i, 1] + c_ * bary[i, 2]
    _bd[i] = np.linalg.norm(v - q_)
    n_ = np.cross(b_ - a_, c_ - a_); n_ /= max(np.linalg.norm(n_), 1e-12)
    _bny[i] = n_[1]
for nm_, arr_ in (("bind_dist", _bd), ("bind_ny", _bny)):
    at_ = am.attributes.new(nm_, 'FLOAT', 'POINT'); at_.data.foreach_set("value", arr_.astype(np.float32))
at_ = am.attributes.new("bind_tri", 'INT', 'POINT'); at_.data.foreach_set("value", tri_idx.astype(np.int32))
# 嘴角：上下唇兩側的點各再綁一次「對面那側」，越靠近嘴角越往兩者平均靠 → 嘴角不分開（不然張嘴時嘴角留一條細縫，像往臉頰的折線）
tri_b = np.empty(nv, np.int64); bary_b = np.empty((nv, 3)); cw = np.zeros(nv)
for i, v in enumerate(V):
    s_ = side.get(i)
    if s_ not in ("up", "lo", "mid"):
        tri_b[i] = tri_idx[i]; bary_b[i] = bary[i]; continue
    bvh, idx = (bvh_lo, idx_lo) if s_ in ("up", "mid") else (bvh_up, idx_up)
    loc, nor, ti, d = bvh.find_nearest(Vector(v))
    ti = idx[ti]; tri_b[i] = ti
    a, b, c = (Vector(P0[j]) for j in tris[ti])
    w = barycentric_transform(loc, a, b, c, Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)))
    bary_b[i] = (w.x, w.y, w.z)
    t_ = (abs(v[0] - xc) / hw - 0.45) / (CUT - 0.45)
    cw[i] = 0.5 if s_ == "mid" else 0.5 * min(1.0, max(0.0, t_)) ** 1.5  # 嘴寬六成以外開始，到嘴角＝各半
_bad = ~np.isfinite(bary_b).all(1); bary_b[_bad] = 1 / 3
print("[transfer] 嘴角合攏 %d 點" % int((cw > 0.01).sum()))
edges = np.empty(len(am.edges) * 2, np.int64); am.edges.foreach_get("vertices", edges); edges = edges.reshape(-1, 2)
deg = np.bincount(edges.ravel(), minlength=nv).astype(float); deg[deg == 0] = 1
def smooth(D, it):
    for _ in range(it):
        acc = np.zeros_like(D)
        np.add.at(acc, edges[:, 0], D[edges[:, 1]]); np.add.at(acc, edges[:, 1], D[edges[:, 0]])
        D = 0.5 * D + 0.5 * acc / deg[:, None]
    return D
# 長髮不跟臉動：顏色像頭髮、而且離模板臉皮有一段距離（垂在臉外的髮塊）→ 位移權重 0；
#   貼在臉上的細髮絲（畫在皮膚上）照樣跟著動，不然會撕裂
img = next(n.image for n in ai.material_slots[0].material.node_tree.nodes if n.type == 'TEX_IMAGE')
Wi, Hi = img.size; pxa = np.array(img.pixels[:]).reshape(Hi, Wi, 4)[..., :3]
uvl = am.uv_layers.active.data
COL = np.zeros((nv, 3)); cnt = np.zeros(nv)
for poly in am.polygons:
    for li, vi in zip(poly.loop_indices, poly.vertices):
        u, v = uvl[li].uv
        COL[vi] += pxa[min(Hi - 1, int(v * Hi)), min(Wi - 1, int(u * Wi))]; cnt[vi] += 1
COL /= np.maximum(cnt, 1)[:, None]
hair_rgb = np.median(COL[V[:, 2] > np.percentile(V[:, 2], 97)], 0)
skin_rgb = np.median(COL[(V[:, 1] < -0.3) & (np.abs(V[:, 0]) < 0.15) & (np.abs(V[:, 2] - 0.15) < 0.1)], 0)
hairish = np.linalg.norm(COL - hair_rgb, axis=1) < 0.6 * np.linalg.norm(COL - skin_rgb, axis=1)
dface = np.array([bvh_all.find_nearest(Vector(v))[3] for v in V])
w_move = 1 - hairish * np.clip((dface - 0.03) / 0.05, 0, 1)
w_move = smooth(w_move[:, None], 4)[:, 0]
print("[transfer] 長髮不動 %d 點（髮色 %s）" % (int((w_move < 0.5).sum()), np.round(hair_rgb, 3)))
# 嘴唇範圍權重（嘟嘴往前噘用）：唇線附近、嘴寬以內
_dx = np.abs(V[:, 0] - xc) / (hw * 1.1)
_dz = np.abs(V[:, 2] - np.array([z_s(x) for x in V[:, 0]])) / 0.12
w_lip = np.clip(1 - _dx ** 2, 0, 1) * np.clip(1 - _dz, 0, 1) * (V[:, 1] < -0.4)
w_lip = w_lip * w_lip * (3 - 2 * w_lip)
_zl = np.array([z_s(x) for x in V[:, 0]])
w_chin = np.clip((V[:, 2] - (_zl - 0.15)) / 0.10, 0, 1)  # 唇縫下 0.05 內全量、到下 0.15 淡成 0
w_chin = w_chin * w_chin * (3 - 2 * w_chin)
import os as _os2
LIP_SMOOTH = int(_os2.environ.get("LIP_SMOOTH", 40))  # 12 時張大嘴下唇下方一道橫向折痕、正中一個 V 凹口
_dxs = np.abs(V[:, 0] - xc) / (hw * 1.25)
_dzs = np.abs(V[:, 2] - np.array([z_s(x) for x in V[:, 0]])) / float(_os2.environ.get("LIP_RZ", 0.18))
w_lipS = np.clip(1 - _dxs ** 2, 0, 1) * np.clip(1 - _dzs, 0, 1) * (V[:, 1] < -0.35)
w_lipS = w_lipS * w_lipS * (3 - 2 * w_lipS)
WALL_I = PK_I; WALL_S = np.array([WALL_SRC[i] for i in WALL_I], dtype=np.int64)
# 下顎：模板下排牙齒的每個下顎形態鍵都是剛體轉動（張嘴＝轉 17 度）→ 擬合成 轉動＋平移
def _rigid(A_, B_):
    ca, cb = A_.mean(0), B_.mean(0); H_ = (A_ - ca).T @ (B_ - cb); U_, S_, Vt_ = np.linalg.svd(H_)
    R_ = Vt_.T @ U_.T
    if np.linalg.det(R_) < 0: Vt_[-1] *= -1; R_ = Vt_.T @ U_.T
    return R_, cb - R_ @ ca
_bt_o = bpy.data.objects["bottom_teeth"]; _bmw = _bt_o.matrix_world
_bkb = _bt_o.data.shape_keys.key_blocks
_B0 = np.array([_bmw @ k.co for k in _bkb["Basis"].data])
JAW = {k.name: _rigid(_B0, np.array([_bmw @ q.co for q in k.data])) for k in _bkb if k.name != "Basis"}
print("[pocket] 下顎形態鍵：%s" % list(JAW))
# 口腔袋每一圈：前兩圈（唇緣）照抄嘴唇；越深越照下顎（下半部）或不動（上半部＝頭骨）
WD = np.select([PK_K <= 2, PK_K == 3, PK_K == 4], [0.0, 0.35, 0.75], 1.0)
_lw = np.clip(0.5 - 0.7 * np.sin(PK_TH), 0, 1); LOWER = _lw * _lw * (3 - 2 * _lw)
NPUSH = [0]
ai.shape_key_add(name="Basis", from_mix=False)
for kb in kbs:
    if kb.name == "Basis": continue
    dP = co_of(kb) - P0
    if not np.any(np.abs(dP) > 1e-7): continue
    Da = (dP[tris[tri_idx]] * bary[:, :, None]).sum(1)
    Db = (dP[tris[tri_b]] * bary_b[:, :, None]).sum(1)
    D = smooth(Da * (1 - cw[:, None]) + Db * cw[:, None], SMOOTH) * w_move[:, None]
    # 嘴唇一帶多抹順：AI 嘴唇細分過、比模板密很多，同一個模板三角形底下的點位移一樣 → 平平一塊、到三角形邊界才轉折＝波浪
    #   （上下唇已切開，抹順不會互相混到；位移跟張嘴量成正比，所以小開口看不出來、開大才明顯）
    D = D * (1 - w_lipS[:, None]) + smooth(D, LIP_SMOOTH) * w_lipS[:, None]
    if kb.name.startswith("brow"):
        D *= float(_os2.environ.get("BROW_GAIN", 1.6))  # 眉毛：模板動作傳過來被平滑削弱，生氣、難過幾乎看不出來
    if kb.name in ("mouthPucker", "mouthFunnel"):
        # 嘟嘴：模板動作只取「往中間收」（左右＋一半上下），往前噘改用自己平滑的推量。
        #   試過：模板原樣 → 下巴正中壓出一個尖凹窩（模板下唇下緣的動作，抹順、只動嘴唇範圍都消不掉）；
        #   模板只留唇線窄帶 → 嘴唇擠成尖嘴。實驗在 pk_test.py
        Tm = D * w_lip[:, None]
        Tm[:, 1] = 0; Tm[:, 2] *= 0.5
        D = Tm
        D[:, 1] -= (0.042 if kb.name == "mouthPucker" else 0.028) * w_lip
        D = smooth(D, 3)
    # 口腔袋：唇緣照抄嘴唇；深處下半部照下顎轉動、上半部不動（自己另外綁定時，張嘴越大跟嘴唇差越多 → 扭成斜片插進牙齒）
    Dp = D[WALL_S].copy()
    if kb.name in JAW:
        R_, t_ = JAW[kb.name]; P_ = V[WALL_I]
        Dj = (P_ @ R_.T + t_ - P_) * LOWER[:, None]
    else:
        Dj = np.zeros_like(Dp)
    D[WALL_I] = Dp * (1 - WD[:, None]) + Dj * WD[:, None]
    # 這個表情下，口腔袋（第 3 圈以後）不能跑到臉皮前面：嘴角往內收時（驚訝、嘟嘴），寬嘴的人口腔袋側牆會從嘴角旁邊穿出
    #   （攝影師：驚訝時嘴角外一塊粉紅）。量法同靜止時：附近皮膚點（xz 0.03 內）最前面的 y
    if kb.name.startswith(("mouth", "jaw", "cheek")):
        PK_ = V + D
        kd_e = _KD0(len(_skin))
        for j, i in enumerate(_skin): kd_e.insert(Vector((PK_[i, 0], 0.0, PK_[i, 2])), int(i))
        kd_e.balance()
        for i, k_ in zip(WALL_I, PK_K):
            if k_ < 3: continue
            hits = kd_e.find_range(Vector((PK_[i, 0], 0.0, PK_[i, 2])), 0.03)
            if hits:
                fy = min(PK_[h[1], 1] for h in hits)
                if PK_[i, 1] < fy + 0.012:
                    D[i, 1] += fy + 0.012 - PK_[i, 1]; NPUSH[0] += 1
    if not np.isfinite(D).all():
        raise SystemExit("[transfer] %s 有無效數字（NaN）：%d 點" % (kb.name, int((~np.isfinite(D)).any(1).sum())))
    _nk = ai.shape_key_add(name=kb.name, from_mix=False)
    _nk.data.foreach_set("co", (V + D).ravel())
    _nk.value = 0.0  # 明確歸零（存檔後留在 1 的話，沒接骨頭的表情會一直開著）

print("[pocket] 口腔袋逐表情推到皮後 %d 點次" % NPUSH[0])
# 靜止座標（材質眼睛、眼皮用）：黏在皮膚上跟著變形，睜大眼、瞇眼時眼睛範圍一起動
ra = am.attributes.new("rest", 'FLOAT_VECTOR', 'POINT')
ra.data.foreach_set("vector", V.ravel())
# --- 3. 牙齒、牙齦、舌頭照用模板的（口腔袋改自建，見 1c）---
# 口腔袋往後縮一點，避免從 AI 嘴唇表面穿出
keep = {ai.name, "upper_teeth", "bottom_teeth", "upper_gum", "bottom_gum", "Tongue", "Eye_L", "Eye_R"}
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name not in keep:
        bpy.data.objects.remove(o)
for n in ("Eye_L", "Eye_R"):
    bpy.data.objects[n].hide_render = True
# 口腔袋不能戳到 AI 嘴唇前面（模板嘴唇比 AI 靠前，口腔袋前緣從上唇前面穿出來＝上唇下緣的粉紅碎片）
#   每一點量到 AI 皮（未張嘴）的正面深度，超出的往後推到皮後 0.015；每個形態鍵推同樣的量
# 上排牙齒、牙齦往下一點：AI 上唇比模板厚，張嘴時上排牙被上唇整排擋住
for n in ("upper_teeth", "upper_gum"):
    o = bpy.data.objects.get(n)
    if o:
        for kb in (o.data.shape_keys.key_blocks if o.data.shape_keys else [None]):
            for v in (kb.data if kb else o.data.vertices):
                v.co.z -= 0.025 / max(o.matrix_world.to_scale().z, 1e-6)
        if o.data.shape_keys:
            for v, kv in zip(o.data.vertices, o.data.shape_keys.key_blocks[0].data):
                v.co = kv.co
# 舌頭的下顎形態鍵改成跟下顎一起剛體轉動（模板的舌頭張嘴只往下 0.018、牙齒 0.059 → 張大時舌頭停在上排牙齒高度）
_tg0 = bpy.data.objects.get("Tongue")
if _tg0 and _tg0.data.shape_keys:
    _tmw = _tg0.matrix_world; _tinv = _tmw.inverted()
    _tk = _tg0.data.shape_keys.key_blocks
    _T0 = np.array([_tmw @ k.co for k in _tk["Basis"].data])
    for jn, (R_, t_) in JAW.items():
        kj = _tk.get(jn) or _tg0.shape_key_add(name=jn, from_mix=False)
        TJ = _T0 @ R_.T + t_
        for q, p_ in zip(kj.data, TJ):
            q.co = _tinv @ Vector(p_)
    print("[pocket] 舌頭跟下顎剛體轉動：%s" % list(JAW))
# 舌頭：吐舌頭時壓扁一點、舌尖往下垂（模板的舌頭伸出來像一顆膠囊）
_tg = bpy.data.objects.get("Tongue")
if _tg and _tg.data.shape_keys and "tongueOut" in _tg.data.shape_keys.key_blocks:
    _kb = _tg.data.shape_keys.key_blocks
    TB = np.array([v.co[:] for v in _kb["Basis"].data]); TK = np.array([v.co[:] for v in _kb["tongueOut"].data])
    TK = TB + (TK - TB) * np.array([1.0, float(_os2.environ.get("TONGUE_LEN", 0.75)), 0.85])  # 伸出長度（1＝模板原樣，斜側看像一片懸空的圓盤伸出臉外）
    fwd = np.clip(TB[:, 1] - TK[:, 1], 0, None)  # 往前伸了多少（臉朝 −Y）
    zc = np.median(TK[fwd > 0.5 * fwd.max(), 2]) if (fwd > 0).any() else TK[:, 2].mean()
    w_ = fwd / max(fwd.max(), 1e-6)
    TK[:, 2] = TK[:, 2] + (zc + 0.7 * (TK[:, 2] - zc) - TK[:, 2]) * w_ - 0.05 * fwd * w_  # 舌尖稍微下垂（0.12 時舌尖穿出下唇前面、下唇上一個 V 形缺口；（0.25 時垂到下唇前面、懸在下巴上
    TK[:, 0] = TK[:, 0] * (1 + 0.12 * w_)  # 舌尖稍微變寬變扁
    # 舌溝：舌面中央壓一道淺溝；舌根（沒伸出來的那段）收窄
    _tg.data.update()
    TN = np.array([v.normal[:] for v in _tg.data.vertices])
    hwid = max(np.ptp(TK[:, 0]) / 2, 1e-3)
    xm = np.median(TK[:, 0])
    top = TN[:, 2] > 0.4
    wg = w_ * np.clip((0.85 - w_) / 0.25, 0, 1)  # 舌尖前淡掉：舌尖很薄，壓下去上表面穿到下表面底下、折出 V 形
    TK[:, 2] -= 0.012 * top * np.clip(1 - ((TK[:, 0] - xm) / (0.4 * hwid)) ** 2, 0, 1) * wg  # 0.007 時畫面上看不出舌溝
    TK[:, 0] = xm + (TK[:, 0] - xm) * (1 - 0.12 * (1 - w_) * (fwd.max() > 0))
    _kb["tongueOut"].data.foreach_set("co", TK.ravel())
    print("[transfer] 舌頭壓扁、舌尖下垂（最多往前 %.3f）" % fwd.max())
from mathutils.bvhtree import BVHTree as _BT
afaces = [tuple(p_.vertices) for p_ in am.polygons]
akb = {k.name: k for k in am.shape_keys.key_blocks}
def _arr(kbx):
    a_ = np.empty(len(kbx.data) * 3); kbx.data.foreach_get("co", a_); return a_.reshape(-1, 3)
ABASE = _arr(akb["Basis"])
from mathutils.kdtree import KDTree as _KD
KDS = {}
WALLV = np.zeros(len(am.vertices), bool)
WALLV[PK_I] = True  # 口腔袋（含唇緣）不算皮
def _front_y(name, x, z, r=0.025):
    """AI 皮（這個表情）在 (x,z) 附近最前面的深度。射線在唇縫正上會從上下唇的接縫穿過去、打不到皮 → 改用附近頂點"""
    if name not in KDS:
        AK = _arr(akb[name]) if name in akb else ABASE
        fr_ = np.where((AK[:, 1] < -0.2) & ~WALLV)[0]  # 唇內壁不算皮：張嘴開口處只剩內壁點，會把舌頭壓成一個平面
        kd_ = _KD(len(fr_))
        for j, i in enumerate(fr_):
            kd_.insert(Vector((AK[i, 0], 0.0, AK[i, 2])), int(i))
        kd_.balance()
        KDS[name] = (kd_, AK)
    kd_, AK = KDS[name]
    hits = kd_.find_range(Vector((x, 0.0, z)), r)
    return min(AK[i, 1] for _, i, _ in hits) if hits else None
BTS = {}
def _bt(name):
    if name not in BTS:
        AK = _arr(akb[name]) if name in akb else ABASE
        BTS[name] = _BT.FromPolygons([Vector(p_) for p_ in AK], afaces)
    return BTS[name]
np_tot, pmax = 0, 0.0
# 口腔袋、牙齒、牙齦、舌頭：每個表情下都不能跑到 AI 皮前面（模板嘴唇比 AI 靠前；上排牙齒、牙齦本來沒有形態鍵，
#   微笑時 AI 嘴角往後拉、固定的牙齒就從嘴唇前面穿出來）→ 缺的形態鍵補上，超出的推到皮後 MARG
MARG = {"upper_teeth": 0.012, "bottom_teeth": 0.012, "upper_gum": 0.015, "bottom_gum": 0.015, "Tongue": 0.012}
for on_, marg in MARG.items():
    o_ = bpy.data.objects.get(on_)
    if not o_:
        continue
    me_ = o_.data
    if not me_.shape_keys:
        o_.shape_key_add(name="Basis", from_mix=False)
    okb = me_.shape_keys.key_blocks
    def _push(CK, kname):
        bt = _bt(kname)
        dlt = np.zeros(len(CK))
        for i, p_ in enumerate(CK):
            fy = _front_y(kname, p_[0], p_[2])
            if fy is not None and p_[1] < fy + marg:
                dlt[i] = fy + marg - p_[1]
        return dlt
    # 先推基準形狀，所有形態鍵一起推同樣的量（相對形態鍵：只推基準的話，開表情會被拉回原位）
    OB = _arr(okb["Basis"])
    bd = _push(OB, "Basis")
    for k_ in okb:
        a_ = _arr(k_); a_[:, 1] += bd; k_.data.foreach_set("co", a_.ravel())
    np_tot += int((bd > 0).sum()); pmax = max(pmax, bd.max())
    OB = _arr(okb["Basis"])
    for kname in [k for k in akb if k != "Basis"]:
        if not np.any(np.abs(_arr(akb[kname]) - ABASE) > 1e-6):
            continue
        if on_ == "Tongue" and kname == "tongueOut":
            continue  # 吐舌頭本來就要伸到嘴唇前面（推回去會在舌尖壓出 V 形缺口）
        kbo = okb.get(kname)
        CK = _arr(kbo) if kbo else OB.copy()
        dlt = _push(CK, kname)
        if not dlt.any():
            continue
        if kbo is None:
            kbo = o_.shape_key_add(name=kname, from_mix=False)
            kbo.value = 0.0  # 新增的鍵預設值可能不是 0 → 檢查報「打開時非 0 的形態鍵」（攝影師 v2：上排牙齒 mouthRollLower）
        CK[:, 1] += dlt
        kbo.data.foreach_set("co", CK.ravel())
        np_tot += int((dlt > 0).sum()); pmax = max(pmax, dlt.max())
    for v, kv in zip(me_.vertices, okb[0].data):
        v.co = kv.co
print("[transfer] 口腔零件推到皮後（逐表情）%d 點次、最多 %.3f" % (np_tot, pmax))
# 牙齦粉紅、唇內側深紅（淡色時看起來像一條白邊、斜側看得到碎片）
for n in ("upper_gum", "bottom_gum"):
    o = bpy.data.objects.get(n)
    if o:
        gm = bpy.data.materials.new("Gum_Pink"); b_ = next(x for x in gm.node_tree.nodes if x.type == 'BSDF_PRINCIPLED')
        b_.inputs['Base Color'].default_value = (0.13, 0.025, 0.025, 1); b_.inputs['Roughness'].default_value = 0.95
        if 'Specular IOR Level' in b_.inputs: b_.inputs['Specular IOR Level'].default_value = 0.1  # 跟口腔同色：牙齦是直邊扁帶，亮粉色時張嘴像一塊長方形
        o.data.materials.clear(); o.data.materials.append(gm)
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
print("SAVED", OUT_BLEND)
