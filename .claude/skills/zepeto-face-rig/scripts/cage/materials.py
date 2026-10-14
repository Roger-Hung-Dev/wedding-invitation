# 乙路線第 3 步：上材質，並和原本的 AI 頭並排渲染比對。
#   1. 皮膚：把 AI 頭的顏色（皮膚、眉毛）烘焙轉印到新臉的貼圖座標上，套黏土材質（同 postprocess.py 定案值）。
#   2. 嘴巴：嘴唇＝帶粉的膚色；口腔內部（嘴唇材質中不朝前、比嘴唇深的面）＝深紅。
#   3. 眼睛：虹膜＋瞳孔沿視線方向放大（貼著眼球表面），虹膜改成深棕色、眼白微亮。
#   4. 牙齒白、牙齦粉紅；頭髮沿用 AI 頭的黏土材質。
#   5. 三點燈光＋鏡頭，存成 head_v1.blend；渲正面／斜側／側面，新頭與 AI 頭各一張。
# 用法：blender.exe -b wrapped.blend --python materials.py -- <輸出資料夾>
import bpy, bmesh, os, sys, json, math
import numpy as np
from mathutils import Vector

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
# 每張臉的輸出資料夾（環境變數 ZEPETO_RIG_WORK）與模板資料夾（ZEPETO_RIG_TEMPLATE）；run_face_rig.py 會設好
WORK = os.environ.get("ZEPETO_RIG_WORK") or os.getcwd()
TEMPLATE = os.environ.get("ZEPETO_RIG_TEMPLATE") or os.path.normpath(
    os.path.join(_SCRIPTS, "..", "..", "..", "..", "docs", "data", "blender", "zepeto", "templates", "cartoon-head-lucadrech"))
HERE = WORK
out = sys.argv[sys.argv.index("--") + 1]
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
head, eyes, hair, ai = (bpy.data.objects[n] for n in ("Head", "Eyes", "Hair", "AI_Head"))
ears = bpy.data.objects["Ears"]  # 原版 AI 頭切下來的耳朵
bust = bpy.data.objects.get("Bust")  # 原版的肩頸底座（AI 頭底部不是脖子時才有）
extra = [bust] if bust else []
teeth = [bpy.data.objects[n] for n in ("upper_teeth", "bottom_teeth")]
gums = [bpy.data.objects[n] for n in ("upper_gum", "bottom_gum")]
CLAY = dict(rough=0.75, sss=0.3, radius=(1.0, 0.2, 0.1), scale=0.05)


def principled(name, color, rough=0.5, sss=0.0, image=None):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (*color, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = 0.0
    b.inputs['Subsurface Weight'].default_value = sss
    b.inputs['Subsurface Radius'].default_value = CLAY["radius"]
    b.inputs['Subsurface Scale'].default_value = CLAY["scale"]
    if image is not None:
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = image
        t.location = (b.location.x - 400, b.location.y)
        nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    return m


# ── 1. 烘焙：AI 頭的顏色 → 新臉的貼圖 ──
#   Blender 烘焙會先把整張圖清成黑色，射線沒打到 AI 頭的地方就是純黑（模板脖子比 AI 細，耳後、下巴底下會漏）。
#   所以烘兩次：近距離（準）＋遠距離（補漏），兩次都沒打到的填膚色。頭髮是深灰、不是純黑，不會被誤判。
SKIN_RGB = (0.93, 0.79, 0.70)
try:
    sc.render.engine = 'CYCLES'
except TypeError:
    pass
sc.cycles.device = 'CPU'
sc.cycles.samples = 1
ai.hide_set(False)
ai.hide_render = False
for o in bpy.context.view_layer.objects:
    o.select_set(False)
ai.select_set(True)
head.select_set(True)
bpy.context.view_layer.objects.active = head
SIZE = 2048
passes = []
for extrusion, max_dist in ((0.06, 0.5), (0.35, 1.2)):
    im = bpy.data.images.new(f"bake_{extrusion}", SIZE, SIZE)
    for m in head.data.materials:
        n = m.node_tree.nodes.new('ShaderNodeTexImage')
        n.image = im
        m.node_tree.nodes.active = n
    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, use_selected_to_active=True,
                        cage_extrusion=extrusion, max_ray_distance=max_dist, margin=16)
    px = np.empty(SIZE * SIZE * 4, np.float32)
    im.pixels.foreach_get(px)
    passes.append(px.reshape(-1, 4))
    for m in head.data.materials:
        for n in [n for n in m.node_tree.nodes if n.type == 'TEX_IMAGE']:
            m.node_tree.nodes.remove(n)
near, far = passes
miss_near = near[:, :3].max(1) < 0.02
comb = near.copy()
comb[miss_near] = far[miss_near]
miss_both = comb[:, :3].max(1) < 0.02
comb[miss_both, :3] = SKIN_RGB
comb[:, 3] = 1.0


REP = json.load(open(os.path.join(HERE, "wrap_report.json"), encoding="utf-8"))
hme = head.data
UVD = hme.uv_layers.active.data


def raster(face_idx, fn):
    """把每個面在貼圖座標上的像素交給 fn(列, 欄, 三角形三頂點, 重心座標)處理（三角形重心座標判斷）"""
    for fi in face_idx:
        poly = hme.polygons[fi]
        lis = list(poly.loop_indices)
        uvs = [np.array(UVD[li].uv) * SIZE for li in lis]
        vids = [hme.loops[li].vertex_index for li in lis]
        for t in range(1, len(uvs) - 1):
            a, b, c = uvs[0], uvs[t], uvs[t + 1]
            x0, y0 = np.floor(np.minimum.reduce([a, b, c])).astype(int) - 2
            x1, y1 = np.ceil(np.maximum.reduce([a, b, c])).astype(int) + 2
            xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, SIZE)), np.arange(max(y0, 0), min(y1, SIZE)))
            pts = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
            e1, e2, d = b - a, c - a, pts - a
            den = e1[0] * e2[1] - e2[0] * e1[1]
            if abs(den) < 1e-9:
                continue
            l1 = (d[:, 0] * e2[1] - e2[0] * d[:, 1]) / den
            l2 = (e1[0] * d[:, 1] - d[:, 0] * e1[1]) / den
            l0 = 1 - l1 - l2
            inside = (l0 >= -0.03) & (l1 >= -0.03) & (l2 >= -0.03)
            fn(ys.ravel()[inside], xs.ravel()[inside], (vids[0], vids[t], vids[t + 1]),
               np.stack([l0[inside], l1[inside], l2[inside]], 1).clip(0, 1))


def smooth01(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


# 每個頂點「保留轉印顏色」的權重：臉的正面 1；側面、脖子、耳朵、後腦 0（統一膚色），中間平滑過渡。
# （AI 頭只有正面的顏色可信；側面和脖子是模板比 AI 細、轉印時從遠處補來的，顏色不均）
PV = np.array([v.co[:] for v in hme.vertices])
NV = np.array([v.normal[:] for v in hme.vertices])
U_ = REP["U"]
w_keep_col = smooth01((-NV[:, 1] - 0.15) / 0.35) * smooth01((PV[:, 2] - (REP["ai_chin_z"] - 0.3 * U_)) / (0.25 * U_))
w_keep_col[list(REP["ear_verts"])] = 0.0
eye_c = {k: np.array(REP["eyes"][k]["center"]) for k in ("L", "R")}
# 眼線濃度（每個頂點一個值，面內平滑內插 → 邊緣不會是鋸齒）：
#   上眼皮：眼皮邊緣 1、往外一圈 0.55、兩圈 0；下眼皮：邊緣 0.3（淡淡的陰影）
lash_w = np.zeros(len(PV))
for k in ("L", "R"):
    er = REP["eye_rings"][k]
    m_ = er["margin"]
    for vid, d in er["rd"].items():
        vid = int(vid)
        if d <= m_ + 2:
            w_keep_col[vid] = 0.0  # 眼皮內緣：轉印到的是原本畫的眼白 → 蓋膚色
        upper = PV[vid, 2] > eye_c[k][2] - 0.01
        base = {m_ - 1: 0.8, m_: 0.8, m_ + 1: 0.0}.get(d, 0.0)  # 第 2 輪再收細（原版的眼線很細）；閉眼時這圈會轉到正面
        lash_w[vid] = base if upper else base * 0.3
img3 = comb.reshape(SIZE, SIZE, 4)
# 統一膚色＝臉正面皮膚（權重 1、亮的）在貼圖上的中間值
sample = []
uv_of_v = {}
for l in hme.loops:
    uv_of_v.setdefault(l.vertex_index, UVD[l.index].uv[:])
for v in np.where(w_keep_col > 0.99)[0]:
    if int(v) not in uv_of_v:  # 沒有連在任何面上的孤立頂點
        continue
    u, vv = uv_of_v[int(v)]
    c = img3[min(SIZE - 1, int(vv * SIZE)), min(SIZE - 1, int(u * SIZE)), :3]
    if c.mean() > 0.6:
        sample.append(c)
skin_tone = np.median(np.array(sample), 0) if sample else np.array(SKIN_RGB)
orig = img3.copy()


def blend_fn(rr, cc, tri, bary):
    w = bary @ w_keep_col[list(tri)]
    img3[rr, cc, :3] = orig[rr, cc, :3] * w[:, None] + skin_tone * (1 - w[:, None])


raster(range(len(hme.polygons)), blend_fn)
# 頭髮底下的頭皮塗成髮色：萬一從頭髮縫隙（例：頭頂分線）露出來，看到的是暗色不是膚色
HAIR_RGB = np.array(REP.get("hair_rgb", [0.16, 0.16, 0.18]))  # AI 頭量到的髮色（wrap.py）
if os.environ.get("ZEPETO_HAIR"):  # （試做）照片是黑髮，AI 頭偏藍灰
    HAIR_RGB = np.array([float(v) for v in os.environ["ZEPETO_HAIR"].split(",")])
uh = np.zeros(len(PV))
uh[REP.get("under_hair", [])] = 1.0
uh_faces = [p.index for p in hme.polygons if any(uh[v] > 0 for v in p.vertices)]


def hair_fn(rr, cc, tri, bary):
    w = smooth01(bary @ uh[list(tri)])
    img3[rr, cc, :3] = img3[rr, cc, :3] * (1 - w[:, None]) + HAIR_RGB * w[:, None]


raster(uh_faces, hair_fn)
# 頭髮邊緣與眉毛的雜色
#   原版 AI 貼圖在髮際、瀏海下緣、眉毛下緣本來就有一圈橘褐陰影與顆粒；轉印過來被放大成「鬢角網狀雜點、橘邊」。
#   - 離頭髮很近的皮膚：沿「膚色 → 髮色」那條線看深淺，淺的一律換成乾淨膚色、深的換成髮色（去雜點）
#   - 眉毛一帶：顏色投影到「膚色 → 髮色」線上（保留深淺漸層、去掉橘色）
from mathutils import kdtree
hv = [hair.matrix_world @ v.co for v in hair.data.vertices]
kd = kdtree.KDTree(len(hv))
for i_, c_ in enumerate(hv):
    kd.insert(c_, i_)
kd.balance()
hdist = np.array([kd.find(Vector(p_))[2] for p_ in PV])
band_w = 1 - smooth01((hdist - 0.03 * U_) / (0.09 * U_))
LMJ = json.load(open(os.path.join(HERE, "landmarks.json"), encoding="utf-8"))
brow_w = np.zeros(len(PV))
for k in ("L", "R"):
    b_ = LMJ["brows"][k]
    wx = 1 - smooth01((np.abs(PV[:, 0] - b_["center"][0]) - b_["half_len"] * 1.4) / (0.08 * U_))
    wz = (1 - smooth01((PV[:, 2] - b_["top"] - 0.05 * U_) / (0.06 * U_))) * (1 - smooth01((b_["bottom"] - 0.08 * U_ - PV[:, 2]) / (0.06 * U_)))
    brow_w = np.maximum(brow_w, wx * wz * (NV[:, 1] < -0.3))
band_w *= 1 - brow_w
band_w[uh > 0] = 0.0  # 頭髮底下的頭皮維持髮色（頭頂分線露出來時是暗的）
for k in ("L", "R"):  # 眼皮一帶不動（眼線另外畫）
    for vid, d in REP["eye_rings"][k]["rd"].items():
        band_w[int(vid)] = 0.0
DSH = HAIR_RGB - skin_tone
DD = float(DSH @ DSH)
# 眉毛的顏色線：用量到的眉色（新娘是咖啡色眉、黑髮；投影到髮色線上會被染成灰黑）；舊的 landmarks 沒有眉色就用髮色
BROW_RGB = np.mean([LMJ["brows"][k].get("color_srgb", HAIR_RGB) for k in ("L", "R")], 0)
DSB = BROW_RGB - skin_tone
DB = float(DSB @ DSB)
clean_faces = [p.index for p in hme.polygons if any(band_w[v] > 0.01 or brow_w[v] > 0.01 for v in p.vertices)]


BWI = np.zeros((SIZE, SIZE), np.float32)  # 每個像素的「頭髮邊緣」權重
BRI = np.zeros((SIZE, SIZE), np.float32)  # 每個像素的「眉毛」權重


def weight_fn(rr, cc, tri, bary):
    BWI[rr, cc] = np.maximum(BWI[rr, cc], bary @ band_w[list(tri)])
    BRI[rr, cc] = np.maximum(BRI[rr, cc], bary @ brow_w[list(tri)])


raster(clean_faces, weight_fn)
c_ = img3[:, :, :3]
t_ = np.clip(((c_ - skin_tone) @ DSH) / DD, 0, 1)
# 深色區先縮 R 像素再脹回來：細細一圈（瀏海尖端外的黑邊、鬢角顆粒）消失，大片（瀏海縫隙底下的頭皮）留著
#   （第一次試：頭髮外一律換膚色 → 頭頂瀏海縫隙露出一塊膚色；深的留著 → 瀏海尖端外一圈鋸齒黑邊）
R_ = 6
dark = t_ > 0.5


def shift_all(a, op):
    out = a.copy()
    for dy in range(-R_, R_ + 1):
        for dx in range(-R_, R_ + 1):
            out = op(out, np.roll(np.roll(a, dy, 0), dx, 1))
    return out


dark_open = shift_all(shift_all(dark, np.logical_and), np.logical_or)
tb_ = np.clip(((c_ - skin_tone) @ DSB) / DB, 0, 1)
proj = skin_tone + tb_[..., None] * DSB
snap = np.where(dark_open[..., None], HAIR_RGB, skin_tone)
tgt = c_ * (1 - BRI[..., None]) + proj * BRI[..., None]
img3[:, :, :3] = tgt * (1 - BWI[..., None]) + snap * BWI[..., None]


print("[mat] 清頭髮邊緣與眉毛雜色，面 %d" % len(clean_faces))
# AI 嘴角外的口紅色還原成膚色（新娘：口紅畫到嘴角外的皮膚上，笑的時候跟著臉頰往上提，看起來嘴角往上劃一道粉紅）
mth = LMJ["mouth"]
mcx, mcz, mhw = mth["center"][0], mth["center"][2], mth["half_w"]
old_lip_i = next((i for i, m in enumerate(hme.materials) if m and m.name == "lips"), None)
lipf = np.array([p.material_index == old_lip_i for p in hme.polygons])
lip_v = np.zeros(len(PV), bool)
for p in hme.polygons:
    if lipf[p.index] and abs(p.center.x - mcx) < 0.5 * mhw and abs(p.center.z - mcz) < 0.15 * U_ and p.normal.y < -0.3:
        lip_v[list(p.vertices)] = True
LIP_RGB = None
if lip_v.any():
    smp = [img3[min(SIZE - 1, int(uv_of_v[int(v)][1] * SIZE)), min(SIZE - 1, int(uv_of_v[int(v)][0] * SIZE)), :3] for v in np.where(lip_v)[0] if int(v) in uv_of_v]
    LIP_RGB = np.median(np.array(smp), 0)
if LIP_RGB is not None and np.linalg.norm(LIP_RGB - skin_tone) > 0.04:
    axm = np.abs(PV[:, 0] - mcx)
    corner_w = smooth01((axm - 0.95 * mhw) / (0.2 * mhw)) * (1 - smooth01((axm - 1.9 * mhw) / (0.3 * mhw)))         * (1 - smooth01((np.abs(PV[:, 2] - mcz) - 0.12 * U_) / (0.1 * U_))) * (NV[:, 1] < 0.2)
    DL = LIP_RGB - skin_tone
    DLL = float(DL @ DL)
    cw_faces = [p.index for p in hme.polygons if any(corner_w[v] > 0.01 for v in p.vertices)]

    def unlip_fn(rr, cc, tri, bary):
        c_ = img3[rr, cc, :3]
        t_ = np.clip(((c_ - skin_tone) @ DL) / DLL, 0, 1)
        w_ = (bary @ corner_w[list(tri)])[:, None]
        img3[rr, cc, :3] = c_ - (t_[:, None] * DL) * w_

    raster(cw_faces, unlip_fn)
    print("[mat] 嘴角外口紅還原膚色：唇色 %s、面 %d" % (np.round(LIP_RGB, 3), len(cw_faces)))
# 上眼皮的眼線（ZEPETO 風的深色上睫毛線）＋下眼皮淡陰影
LASH = np.array([0.09, 0.06, 0.05])
lash_faces = [p.index for p in hme.polygons if any(lash_w[v] > 0 for v in p.vertices)]


def lash_fn(rr, cc, tri, bary):
    w = smooth01((bary @ lash_w[list(tri)] - 0.15) / 0.5)  # 內插後再壓一次對比：邊緣俐落但不鋸齒
    img3[rr, cc, :3] = img3[rr, cc, :3] * (1 - w[:, None]) + LASH * w[:, None]


raster(lash_faces, lash_fn)
print("[mat] 統一膚色 %s、眼線面 %d" % (np.round(skin_tone, 3), len(lash_faces)))
bake_img = bpy.data.images.new("Head_color", SIZE, SIZE)
bake_img.pixels.foreach_set(comb.ravel())
bake_img.filepath_raw = os.path.join(HERE, "head_color.png")
bake_img.file_format = 'PNG'
bake_img.save()
print("[mat] 烘焙：近距離漏 %d 像素，遠距離補完後仍漏 %d（填膚色）" % (int(miss_near.sum()), int(miss_both.sum())))
ai.hide_set(True)
ai.hide_render = True

# ── 皮膚／嘴唇／口腔材質 ──
#   materials.clear() 會把每個面的材質編號清成 0，所以先記下哪些面原本是 lips
me = head.data
P = np.array([v.co[:] for v in me.vertices])
old_lips = next(i for i, m in enumerate(me.materials) if m.name == "lips")
lip_face_idx = [p.index for p in me.polygons if p.material_index == old_lips]
mat_skin = principled("ZEPETO_Skin", SKIN_RGB, CLAY["rough"], CLAY["sss"], image=bake_img)
# 嘴唇：轉印來的膚色再乘一層淡粉紅（單色淡粉打光後會接近白色，看起來像露出牙齒）
mat_lips = principled("ZEPETO_Lips", SKIN_RGB, 0.6, CLAY["sss"], image=bake_img)
nt = mat_lips.node_tree
tex = next(n for n in nt.nodes if n.type == 'TEX_IMAGE')
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
mix = nt.nodes.new('ShaderNodeMix')
mix.data_type = 'RGBA'
mix.blend_type = 'MULTIPLY'
mix.inputs['Factor'].default_value = 1.0
mix.inputs['B'].default_value = (1.0, 0.90, 0.88, 1.0)  # 第 4 輪調淡：原版嘴唇幾乎是膚色，只有一條粉紅線
nt.links.new(tex.outputs['Color'], mix.inputs['A'])
nt.links.new(mix.outputs['Result'], bsdf.inputs['Base Color'])
mat_inner = principled("Mouth_Inner", (0.45, 0.16, 0.16), 0.6, 0.1)  # 第 4 輪：太暗時上下唇的縫是一條深灰線，原版是柔和的紅線
me.materials.clear()
for m in (mat_skin, mat_lips, mat_inner):
    me.materials.append(m)
for p in me.polygons:
    p.material_index = 0
eye_z = json.load(open(os.path.join(HERE, "wrap_report.json"), encoding="utf-8"))["eyes"]["L"]["center"][2]
# 嘴巴的面：眼睛下方、臉的中間（耳道在模板裡也是 lips 材質，要排除）；眼窩隧道裡的 lips 面維持皮膚
mouth_faces = [me.polygons[i] for i in lip_face_idx
               if me.polygons[i].center.z < eye_z - 0.15 and abs(me.polygons[i].center.x) < 0.35]
lips_front_y = min(p.center.y for p in mouth_faces)
mz_ = float(np.median([p.center.z for p in mouth_faces if p.center.y < lips_front_y + 0.03]))
cavity = Vector((0.0, lips_front_y + 0.2, mz_))  # 嘴巴裡面深處的一點
n_in, n_lip = 0, 0
for p in mouth_faces:
    if p.normal.dot((cavity - p.center).normalized()) > 0.1:
        p.material_index = 2  # 面朝向嘴巴裡面 → 口腔內部
        n_in += 1
    else:
        p.material_index = 1
        n_lip += 1
# 口腔袋：模板的口腔內部是皮膚材質。從喉嚨最深處的開口出發，沿相連的面往外長、碰到嘴唇就停 → 整片是口腔
bmq = bmesh.new()
bmq.from_mesh(me)
bmq.faces.ensure_lookup_table()
bnd = [e for e in bmq.edges if e.is_boundary]
adj_b = {}
for e in bnd:
    a, b = e.verts[0].index, e.verts[1].index
    adj_b.setdefault(a, []).append(b)
    adj_b.setdefault(b, []).append(a)
loops_b, seen_b = [], set()
for s in adj_b:
    if s in seen_b:
        continue
    comp, st = [], [s]
    seen_b.add(s)
    while st:
        v = st.pop()
        comp.append(v)
        for u in adj_b[v]:
            if u not in seen_b:
                seen_b.add(u)
                st.append(u)
    loops_b.append(comp)
cands = [l for l in loops_b if abs(P[l][:, 0].mean()) < 0.05 and P[l][:, 1].mean() > lips_front_y + 0.15]
throat = min(cands, key=lambda l: abs(P[l][:, 2].mean() - (mz_ - 0.12)))
lips_set = set(lip_face_idx)
bag = set()
st = []
bmq.verts.ensure_lookup_table()
for v in throat:
    for f in bmq.verts[v].link_faces:
        if f.index not in lips_set and f.index not in bag:
            bag.add(f.index)
            st.append(f.index)
while st:
    f = bmq.faces[st.pop()]
    for e in f.edges:
        for g in e.link_faces:
            if g.index not in bag and g.index not in lips_set:
                bag.add(g.index)
                st.append(g.index)
bmq.free()
if len(bag) > len(me.polygons) * 0.4:
    raise SystemExit(f"[mat] 口腔長太大（{len(bag)} 面），嘴唇沒有把口腔和臉隔開")
for i in bag:
    me.polygons[i].material_index = 2
n_in += len(bag)

# ── 3. 眼睛：換成自己做的乾淨眼球，虹膜、瞳孔、反光點用材質畫 ──
#   （硬撐大模板的寫實眼球：眼白被擠出放射狀紋路、瞳孔像凹進去的鏡頭、反光點被虹膜擋住）
#   每隻眼一個物件：網格是半徑 1 的球、物件縮放＝眼球三軸半徑（同包覆時算的橢球），原點在眼球中心、
#   物件的 −Y 是視線 → 之後眼珠轉動只要轉物件（或做成形態鍵）。材質用「物件座標」畫，所以跟著眼球轉。
# 虹膜大小與顏色：從 AI 頭的眼睛量（landmarks.json 的 eyes.*.iris），換算規則用第一張臉（新郎）手調結果反推：
#   大小＝量到的虹膜半徑 ÷ 眼球橫向半徑 × 0.9（眼皮會蓋掉一圈）；瞳孔＝虹膜 × 0.55（瞳孔用量的不可靠：虹膜上半很暗會被當瞳孔）
#   顏色＝量到的中間值（sRGB→線性）當上方深色、×3.2 當下方淺色（上深下淺的漸層；太暗時黑瞳孔看不出來）
#   量不到時用新郎的手調值。（第 3 輪：原版虹膜約佔眼寬 6 成、兩側看得到眼白；0.70 時眼白幾乎沒了）
IRIS_R, PUPIL_R = 0.55, 0.30
IRIS_TOP, IRIS_BOT = (0.05, 0.038, 0.033), (0.165, 0.12, 0.10)
_lm = json.load(open(os.path.join(HERE, "landmarks.json"), encoding="utf-8"))
_ir = [(_lm["eyes"][k]["iris"], REP["eyes"][k]["radii"][0]) for k in ("L", "R") if _lm["eyes"][k].get("iris")]
if _ir:
    IRIS_R = float(np.clip(np.mean([i["radius"] / rx for i, rx in _ir]) * 0.9, 0.4, 0.75))
    PUPIL_R = IRIS_R * 0.55
    lin = np.mean([np.array(i["color_srgb"]) ** 2.2 for i, _ in _ir], 0)
    IRIS_TOP = tuple(float(v) for v in lin)
    IRIS_BOT = tuple(float(v) for v in np.clip(lin * 3.2, 0, 0.6))
print("[mat] 虹膜 半徑 %.2f、瞳孔 %.2f、上 %s 下 %s" % (IRIS_R, PUPIL_R, np.round(IRIS_TOP, 3), np.round(IRIS_BOT, 3)))
HL = ((-0.22, 0.26, 0.095), (0.20, -0.17, 0.04))  # 反光點（x, z, 半徑）：畫面左上大、右下小（第 2 輪縮小，原版較柔和）


def eye_material():
    m = bpy.data.materials.get("ZEPETO_Eye") or bpy.data.materials.new("ZEPETO_Eye")
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type not in ('BSDF_PRINCIPLED', 'OUTPUT_MATERIAL'):
            nt.nodes.remove(n)
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    # 霧面＋低反射：0.12 時三盞長方形面光源會在眼球上倒映成白色長方形；亮點只用材質畫的兩個圓點
    b.inputs['Roughness'].default_value = 0.55
    b.inputs['Specular IOR Level'].default_value = 0.15
    b.inputs['Subsurface Weight'].default_value = 0.0
    N = nt.nodes.new
    tc = N('ShaderNodeTexCoord')
    sep = N('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])

    def math(op, a, b_=None):
        n = N('ShaderNodeMath')
        n.operation = op
        for i, v in enumerate((a, b_)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                nt.links.new(v, n.inputs[i])
        return n.outputs[0]

    def dist(cx, cz):  # 物件座標 (x, z) 到 (cx, cz) 的距離
        dx, dz = math('SUBTRACT', sep.outputs['X'], cx), math('SUBTRACT', sep.outputs['Z'], cz)
        return math('SQRT', math('ADD', math('MULTIPLY', dx, dx), math('MULTIPLY', dz, dz)))

    def inside(d, r, soft=0.012):  # 圓內 1、圓外 0，邊緣 soft 寬的平滑過渡（不鋸齒）
        mr = N('ShaderNodeMapRange')
        mr.interpolation_type = 'SMOOTHSTEP'
        nt.links.new(d, mr.inputs['Value'])
        mr.inputs['From Min'].default_value = r - soft
        mr.inputs['From Max'].default_value = r
        mr.inputs['To Min'].default_value = 1.0
        mr.inputs['To Max'].default_value = 0.0
        return mr.outputs['Result']

    def mix(fac, a, b_):
        n = N('ShaderNodeMix')
        n.data_type = 'RGBA'
        nt.links.new(fac, n.inputs['Factor'])
        for slot, v in (('A', a), ('B', b_)):
            if isinstance(v, tuple):
                n.inputs[slot].default_value = (*v, 1.0)
            else:
                nt.links.new(v, n.inputs[slot])
        return n.outputs['Result']

    d0 = dist(0.0, 0.0)
    front = inside(sep.outputs['Y'], 0.0, 0.05)  # 只有前半顆（−Y）畫虹膜
    # 虹膜：上深下淺的漸層，外圈一道更深的邊
    grad = N('ShaderNodeMapRange')
    nt.links.new(sep.outputs['Z'], grad.inputs['Value'])
    grad.inputs['From Min'].default_value, grad.inputs['From Max'].default_value = IRIS_R, -IRIS_R
    iris_col = mix(grad.outputs['Result'], IRIS_TOP, IRIS_BOT)  # 上深下淺（數值見上方 IRIS_TOP／IRIS_BOT）
    rim = math('SUBTRACT', 1.0, inside(d0, IRIS_R - 0.06, 0.06))
    iris_col = mix(rim, iris_col, (0.03, 0.015, 0.01))
    col = mix(math('MULTIPLY', inside(d0, IRIS_R), front), (0.95, 0.95, 0.95), iris_col)
    col = mix(math('MULTIPLY', inside(d0, PUPIL_R, 0.02), front), col, (0.01, 0.008, 0.006))
    hl = None
    for hx, hz, hr in HL:
        s = math('MULTIPLY', inside(dist(hx, hz), hr, 0.015), front)
        hl = s if hl is None else math('MAXIMUM', hl, s)
    col = mix(hl, col, (1.0, 1.0, 1.0))
    nt.links.new(col, b.inputs['Base Color'])
    b.inputs['Emission Color'].default_value = (1, 1, 1, 1)
    nt.links.new(math('MULTIPLY', hl, 3.0), b.inputs['Emission Strength'])
    return m


mat_eye = eye_material()
new_eyes = []
for k in ("L", "R"):
    info = REP["eyes"][k]
    bme = bmesh.new()
    bmesh.ops.create_uvsphere(bme, u_segments=48, v_segments=24, radius=1.0)
    eme = bpy.data.meshes.new(f"Eye_{k}")
    bme.to_mesh(eme)
    bme.free()
    for p in eme.polygons:
        p.use_smooth = True
    eme.materials.append(mat_eye)
    eo = bpy.data.objects.new(f"Eye_{k}", eme)
    sc.collection.objects.link(eo)
    eo.location = info["center"]
    eo.scale = info["radii"]
    # 視線（物件 −Y）對準原版 AI 頭這隻眼的中心（landmarks.json）。
    #   一律朝 −Y 會像斜視；對準眼皮那一圈的平均中心也不行 —— 那圈不對稱、中心偏外，兩眼瞳孔往外眼角飄
    lm_eye = json.load(open(os.path.join(HERE, "landmarks.json"), encoding="utf-8"))["eyes"][k]["c"]
    gaze = Vector(lm_eye) - Vector(info["center"])
    eo.rotation_mode = 'QUATERNION'
    eo.rotation_quaternion = Vector((0, -1, 0)).rotation_difference(gaze.normalized())
    new_eyes.append(eo)
bpy.data.objects.remove(eyes, do_unlink=True)  # 模板原本的寫實眼球不用了
eyes = None

# ── 4. 牙齒、牙齦、頭髮 ──
mat_teeth = principled("Teeth", (0.95, 0.93, 0.88), 0.35)
mat_gum = principled("Gums", (0.82, 0.42, 0.45), 0.5, 0.2)
for o in teeth:
    o.data.materials.clear()
    o.data.materials.append(mat_teeth)
for o in gums:
    o.data.materials.clear()
    o.data.materials.append(mat_gum)
# 頭髮、耳朵不再共用 AI 頭的材質
#   頭髮：保留貼圖的明暗，但顏色統一成髮色（瀏海尖端的切口帶到皮膚、橘褐色，會變成一圈髒邊）
#   耳朵：切口外圈漸變成臉的統一膚色（原本耳朵偏粉橘、旁邊的臉是統一膚色，接縫看得出一塊）
src_m = hair.data.materials[0]


def tex_bsdf(m):
    nt_ = m.node_tree
    return nt_, next(n for n in nt_.nodes if n.type == 'TEX_IMAGE'), next(n for n in nt_.nodes if n.type == 'BSDF_PRINCIPLED')


hm = src_m.copy()
hm.name = "ZEPETO_Hair"
nt_, tx, bs = tex_bsdf(hm)
# 貼圖讀出的數值是 sRGB 編碼，材質節點裡的顏色是線性 → 要先換算（沒換算時頭髮變淺、耳朵接縫變白）
HAIR_LIN = np.power(HAIR_RGB, 2.2)
SKIN_LIN = np.power(skin_tone, 2.2)
lumH = float(np.dot(HAIR_LIN, (0.2126, 0.7152, 0.0722)))
bw = nt_.nodes.new('ShaderNodeRGBToBW')
mr = nt_.nodes.new('ShaderNodeMapRange')
mr.clamp = True
mr.inputs['From Min'].default_value, mr.inputs['From Max'].default_value = lumH * 0.75, lumH * 1.2
mr.inputs['To Min'].default_value, mr.inputs['To Max'].default_value = 0.75, 1.2
mx = nt_.nodes.new('ShaderNodeMix')
mx.data_type = 'RGBA'
mx.blend_type = 'MULTIPLY'
mx.inputs['Factor'].default_value = 1.0
mx.inputs[6].default_value = (*HAIR_LIN, 1.0)
nt_.links.new(tx.outputs['Color'], bw.inputs['Color'])
nt_.links.new(bw.outputs['Val'], mr.inputs['Value'])
nt_.links.new(mr.outputs['Result'], mx.inputs[7])
nt_.links.new(mx.outputs[2], bs.inputs['Base Color'])
for i_ in range(len(hair.data.materials)):
    hair.data.materials[i_] = hm

em = src_m.copy()
em.name = "ZEPETO_Ears"
nt_, tx, bs = tex_bsdf(em)
eme = ears.data
ring = np.full(len(eme.vertices), 99)
bm_e = bmesh.new()
bm_e.from_mesh(eme)
front = [v.index for v in bm_e.verts if v.is_boundary]
bm_e.verts.ensure_lookup_table()
for v in front:
    ring[v] = 0
for d_ in range(1, 6):
    for v in np.where(ring == d_ - 1)[0]:
        for e in bm_e.verts[int(v)].link_edges:
            o_ = e.other_vert(bm_e.verts[int(v)]).index
            if ring[o_] > d_:
                ring[o_] = d_
bm_e.free()
ew = 1 - smooth01(ring / 5.0)
ca = eme.color_attributes.get("ear_edge") or eme.color_attributes.new("ear_edge", 'FLOAT_COLOR', 'POINT')
ca.data.foreach_set("color", np.repeat(ew, 4).astype(np.float32) * np.tile([1, 1, 1, 0], len(ew)) + np.tile([0, 0, 0, 1], len(ew)))
vc = nt_.nodes.new('ShaderNodeVertexColor')
vc.layer_name = "ear_edge"
mx = nt_.nodes.new('ShaderNodeMix')
mx.data_type = 'RGBA'
mx.blend_type = 'MIX'
nt_.links.new(vc.outputs['Color'], mx.inputs['Factor'])
nt_.links.new(tx.outputs['Color'], mx.inputs[6])
mx.inputs[7].default_value = (*SKIN_LIN, 1.0)
nt_.links.new(mx.outputs[2], bs.inputs['Base Color'])
for i_ in range(len(eme.materials)):
    eme.materials[i_] = em
if bust:  # 肩頸底座：原版貼圖；上緣（接脖子那圈）往下 6 環漸變成臉的統一膚色（脖子是統一膚色、原版底座偏橘還畫了陰影，接縫看得出一條帶）
    bm_m = src_m.copy()
    bm_m.name = "ZEPETO_Bust"
    nt_, tx, bs = tex_bsdf(bm_m)
    bme_ = bust.data
    bmb = bmesh.new()
    bmb.from_mesh(bme_)
    bmb.verts.ensure_lookup_table()
    zb = np.array([v.co.z for v in bmb.verts])
    ring_b = np.full(len(bmb.verts), 99)
    top_b = [v.index for v in bmb.verts if v.is_boundary and v.co.z > np.percentile(zb, 60)]
    ring_b[top_b] = 0
    for d_ in range(1, 7):
        for v in np.where(ring_b == d_ - 1)[0]:
            for e in bmb.verts[int(v)].link_edges:
                o_ = e.other_vert(bmb.verts[int(v)]).index
                if ring_b[o_] > d_:
                    ring_b[o_] = d_
    bmb.free()
    bw_ = 1 - smooth01(ring_b / 6.0)
    ca = bme_.color_attributes.get("bust_edge") or bme_.color_attributes.new("bust_edge", 'FLOAT_COLOR', 'POINT')
    ca.data.foreach_set("color", (np.repeat(bw_, 4) * np.tile([1, 1, 1, 0], len(bw_)) + np.tile([0, 0, 0, 1], len(bw_))).astype(np.float32))
    vc = nt_.nodes.new('ShaderNodeVertexColor')
    vc.layer_name = "bust_edge"
    mx = nt_.nodes.new('ShaderNodeMix')
    mx.data_type = 'RGBA'
    mx.blend_type = 'MIX'
    nt_.links.new(vc.outputs['Color'], mx.inputs['Factor'])
    nt_.links.new(tx.outputs['Color'], mx.inputs[6])
    mx.inputs[7].default_value = (*SKIN_LIN, 1.0)
    nt_.links.new(mx.outputs[2], bs.inputs['Base Color'])
    for i_ in range(len(bme_.materials)):
        bme_.materials[i_] = bm_m
print("[mat] 頭髮單一髮色（亮度 %.3f）、耳朵切口漸變 %d 點" % (lumH, int((ew > 0.01).sum())))
for o in [head, hair, ears] + extra + new_eyes + teeth + gums:
    for p in o.data.polygons:
        p.use_smooth = True
for o in [head, hair, ears] + extra:
    if not any(m.type == 'SUBSURF' for m in o.modifiers):
        s = o.modifiers.new("Subdivision", 'SUBSURF')
        s.levels = s.render_levels = 1

# ── 5. 燈光、鏡頭、存檔、渲染 ──
for o in list(bpy.data.objects):
    if o.type in ('LIGHT', 'CAMERA'):
        bpy.data.objects.remove(o, do_unlink=True)


def aim(ob, target=Vector((0.0, 0.0, -0.05))):
    ob.rotation_euler = (target - ob.location).to_track_quat('-Z', 'Y').to_euler()


for name, loc, e, size, col in (("Key_FrontLeft", (-2.6, -2.8, 1.6), 450, 2.0, (1.0, 0.96, 0.92)),
                                ("Fill_FrontRight", (2.8, -2.6, 0.4), 180, 3.0, (0.93, 0.96, 1.0)),
                                ("Rim_Back", (0.0, 3.0, 1.8), 500, 1.5, (1, 1, 1))):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy, ld.size, ld.color = e, size, col
    lo = bpy.data.objects.new(name, ld)
    sc.collection.objects.link(lo)
    lo.location = loc
    aim(lo)
cd = bpy.data.cameras.new("Camera")
cd.lens = 85
cam = bpy.data.objects.new("Camera", cd)
sc.collection.objects.link(cam)
sc.camera = cam
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        sc.render.engine = eng
        break
    except TypeError:
        pass
sc.eevee.taa_render_samples = 32
try:
    sc.eevee.use_raytracing = True  # 眼窩、嘴角這類凹處有接觸陰影，下眼皮和眼白的交界才不會太生硬
except AttributeError:
    pass
sc.render.resolution_x = sc.render.resolution_y = 720
sc.render.film_transparent = False
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "head_v1.blend"))

new_objs = [head, hair, ears] + extra + new_eyes + teeth + gums
# 籠子用（AI 網格路線，CAGE_ONLY）不渲驗收圖
for name, loc in (() if os.environ.get("CAGE_ONLY") else (("front", (0.0, -5.6, 0.0)), ("34", (3.9, -3.9, 0.2)), ("side", (5.6, 0.0, 0.0)))):
    cam.location = Vector(loc)
    aim(cam)
    for which, show in (("new", new_objs), ("ai", [ai])):
        for o in new_objs + [ai]:
            o.hide_render = o not in show
        sc.render.filepath = os.path.join(out, f"mat_{name}_{which}.png")
        bpy.ops.render.render(write_still=True)
print("[mat] 嘴唇面 %d、口腔面 %d、烘焙貼圖 %s" % (n_lip, n_in, bake_img.filepath_raw))
