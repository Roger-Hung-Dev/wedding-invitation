# AI 網格的「材質眼睛」——
#   1. 閉眼：材質眼皮從上往下蓋（邊緣漸變），下緣一條「◡」閉眼線；網格的眨眼鍵改名不用
#      眼皮顏色＝眼睛內側、下方幾點的膚色中間值（上方是 AI 畫的眼影，會偏橘）
#   2. 轉眼球：眼睛範圍裡的貼圖座標平移（虹膜是畫在貼圖上的），由 LOOK_<L|R>_X／_Z 兩個數值控制
#   3. 頭髮：另存一張貼圖，偏藍灰的髮色換成黑髮（保留明暗；咖啡色眉毛不動）
# 用法：blender -b xfer.blend -P eyes_shader.py -- <landmarks.json> <out.blend> [髮色 r,g,b]
import bpy, sys, os, json
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

a = sys.argv[sys.argv.index("--") + 1:]
LM = json.load(open(a[0], encoding="utf-8"))
OUT = a[1]
HAIR_T = np.array([float(v) for v in a[2].split(",")]) if len(a) > 2 else np.array([0.075, 0.068, 0.072])
ai = bpy.data.objects["AI_Driven"]
me = ai.data
for side in ("Left", "Right"):
    kb = me.shape_keys.key_blocks.get("eyeBlink" + side)
    if kb:
        kb.name = "eyeBlink%s_geo" % side
mat = ai.material_slots[0].material
nt = mat.node_tree
N, L = nt.nodes, nt.links
bsdf = next(n for n in N if n.type == "BSDF_PRINCIPLED")
tex = next(n for n in N if n.type == "TEX_IMAGE")

# ── 3. 黑髮貼圖 ──
img = tex.image
W, H = img.size
px = np.array(img.pixels[:], np.float32).reshape(H, W, 4)
uv = me.uv_layers.active.data
V = np.array([v.co[:] for v in me.vertices])
v2uv = {}
for poly in me.polygons:
    for li, vi in zip(poly.loop_indices, poly.vertices):
        v2uv[vi] = uv[li].uv[:]


def col_at_verts(idx):
    return np.array([px[int(v2uv[i][1] * (H - 1)), int(v2uv[i][0] * (W - 1)), :3] for i in idx])


top = np.where(V[:, 2] > np.percentile(V[:, 2], 97))[0]
hair_rgb = np.median(col_at_verts(top), 0)
C = px[..., :3]
skin_rgb = np.median(col_at_verts(np.where((V[:, 1] < -0.3) & (np.abs(V[:, 0]) < 0.15) & (np.abs(V[:, 2] - 0.15) < 0.1))[0]), 0)
dh = np.linalg.norm(C - hair_rgb, axis=2)
ds = np.linalg.norm(C - skin_rgb, axis=2)
w = np.clip((0.75 * ds - dh) / (0.25 * ds + 1e-6), 0, 1) * np.clip((C[..., 2] - C[..., 0] - 0.0) / 0.04, 0, 1)  # 像頭髮、而且偏藍（眉毛偏咖啡不動）
# 臉正面（眼睛、眉毛、臉上細髮絲）不碰：眼珠、眉毛也是深色，會被當成頭髮改掉、整張臉發灰
face_zone = (np.abs(V[:, 0]) < 0.33) & (V[:, 2] > -0.25) & (V[:, 2] < 0.5) & (V[:, 1] < -0.3)
keep = np.zeros((H, W), bool)
yy, xx = np.mgrid[0:H, 0:W]
for poly in me.polygons:
    if not all(face_zone[v] for v in poly.vertices):
        continue
    T_ = [np.array(uv[li].uv) * (W, H) for li in poly.loop_indices]
    x0, y0 = np.floor(np.min(T_, 0)).astype(int) - 1
    x1, y1 = np.ceil(np.max(T_, 0)).astype(int) + 2
    if x1 - x0 > 0.05 * W or y1 - y0 > 0.05 * H:
        continue  # 口腔袋、唇緣的面跨了上下唇兩塊貼圖，包圍框會蓋到半張貼圖（頭髮就不轉黑）
    keep[max(y0, 0):min(y1, H), max(x0, 0):min(x1, W)] = True  # 包圍框就好（512 貼圖、面很小）
w = w * ~keep
lum = C @ np.array([0.2126, 0.7152, 0.0722], np.float32)
lum_h = float(hair_rgb @ np.array([0.2126, 0.7152, 0.0722]))
newc = HAIR_T[None, None, :] * (lum / max(lum_h, 1e-3))[..., None]
px[..., :3] = C * (1 - w[..., None]) + newc * w[..., None]
img2 = bpy.data.images.new("diffuse_blackhair", W, H)
img2.pixels.foreach_set(px.ravel())
img2.filepath_raw = os.path.join(os.path.dirname(OUT), "diffuse_blackhair.png")
img2.file_format = 'PNG'
img2.save()
tex.image = img2
print("[eyes] 頭髮換黑：%d 像素（原髮色 %s）" % (int((w > 0.5).sum()), np.round(hair_rgb, 3)))

# ── 共用節點小工具 ──
def node(t, **kw):
    n = N.new(t)
    for k, v in kw.items():
        setattr(n, k, v)
    return n


def math(op, a_, b_=None, clamp=False):
    n = node("ShaderNodeMath", operation=op, use_clamp=clamp)
    for i, x in enumerate((a_, b_)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            n.inputs[i].default_value = x
        else:
            L.new(x, n.inputs[i])
    return n.outputs[0]


def smooth(x, lo, hi):
    """lo→0、hi→1 的平滑階梯"""
    n = node("ShaderNodeMapRange", interpolation_type='SMOOTHSTEP')
    n.inputs["From Min"].default_value, n.inputs["From Max"].default_value = lo, hi
    L.new(x, n.inputs["Value"])
    return n.outputs["Result"]


def val(name, v=0.0):
    n = node("ShaderNodeValue", name=name, label=name)
    n.outputs[0].default_value = v
    return n.outputs[0]


tc = node("ShaderNodeAttribute", attribute_name="rest")  # 靜止座標：黏在皮膚上（物件座標不跟著變形）
sep = node("ShaderNodeSeparateXYZ")
L.new(tc.outputs["Vector"], sep.inputs[0])
X, Z = sep.outputs[0], sep.outputs[2]

# ── 2. 眼珠：AI 的貼圖是零碎拼貼，平移貼圖座標會跳到別塊 → 眼睛範圍裡改畫程式眼珠（眼白＋虹膜＋瞳孔＋反光），
#    虹膜中心由 LOOK_<L|R>_X／_Z 移動；眼睛外圍（眼線、睫毛）照 AI 原圖
kd = KDTree(len(V))
for i, p in enumerate(V):
    kd.insert(Vector(p), i)
kd.balance()
EYE_MIX = []
for key in ("L", "R"):
    e = LM["eyes"][key]
    cx, cy, cz = e["c"]
    ew, eh = e["ew"], e["eh"]
    ir = e.get("iris") or {}
    icol = np.array([float(c) for c in os.environ.get("IRIS_RGB", "0.26,0.15,0.1").split(",")]) ** 2.2  # 虹膜顏色（sRGB；新娘照片是深棕，AI 貼圖量到的偏灰）
    lx, lz = val("LOOK_%s_X" % key), val("LOOK_%s_Z" % key)
    icx = math("ADD", cx, math("MULTIPLY", lx, 0.35 * ew))
    icz = math("ADD", cz, math("MULTIPLY", lz, 0.3 * eh))
    ddx = math("SUBTRACT", X, icx)
    ddz = math("SUBTRACT", Z, icz)
    d = math("SQRT", math("ADD", math("MULTIPLY", ddx, ddx), math("MULTIPLY", ddz, ddz)))
    R_I = 0.85 * eh
    iris_m = math("SUBTRACT", 1.0, smooth(d, R_I - 0.004, R_I + 0.004))
    pup_m = math("SUBTRACT", 1.0, smooth(d, 0.45 * R_I - 0.003, 0.45 * R_I + 0.003))
    hx = math("SUBTRACT", X, math("ADD", icx, -0.35 * R_I))
    hz = math("SUBTRACT", Z, math("ADD", icz, 0.4 * R_I))
    hd = math("SQRT", math("ADD", math("MULTIPLY", hx, hx), math("MULTIPLY", hz, hz)))
    hl = math("SUBTRACT", 1.0, smooth(hd, 0.2 * R_I, 0.26 * R_I))
    rad = math("DIVIDE", d, R_I)  # 虹膜外圈深一點
    ring = smooth(rad, 0.6, 1.0)
    # 杏仁形眼睛（AI 畫的是杏仁眼、眼尾微翹；橢圓會跟眼線對不上）
    sgo = 1 if key == "L" else -1  # 眼尾方向
    edx = math("DIVIDE", math("SUBTRACT", X, cx), 0.97 * ew)
    edz = math("DIVIDE", math("SUBTRACT", Z, cz), eh)
    q = math("MAXIMUM", math("SUBTRACT", 1.0, math("MULTIPLY", edx, edx)), 0.0)
    up = math("ADD", math("MULTIPLY", math("POWER", q, 0.55), 0.95), math("MULTIPLY", edx, 0.18 * sgo))
    lo = math("MULTIPLY", math("POWER", q, 0.8), -0.8)
    eye_m = math("MULTIPLY", smooth(math("SUBTRACT", up, edz), 0.0, 0.08), smooth(math("SUBTRACT", edz, lo), 0.0, 0.08))
    eye_m = math("MULTIPLY", eye_m, smooth(q, 0.0, 0.05))
    shade = smooth(math("SUBTRACT", edz, math("SUBTRACT", up, 0.45)), 0.0, 0.45)  # 眼白上方被眼皮投影
    c_white = node("ShaderNodeMix", data_type="RGBA")
    c_white.inputs["A"].default_value = (0.85, 0.85, 0.86, 1)
    c_white.inputs["B"].default_value = (0.55, 0.52, 0.53, 1)
    L.new(shade, c_white.inputs["Factor"])
    c_iris = node("ShaderNodeMix", data_type="RGBA")
    c_iris.inputs["A"].default_value = (*(icol * 1.3).clip(0, 1), 1)
    c_iris.inputs["B"].default_value = (*(icol * 0.5), 1)
    L.new(ring, c_iris.inputs["Factor"])
    c1 = node("ShaderNodeMix", data_type="RGBA")
    L.new(iris_m, c1.inputs["Factor"]); L.new(c_white.outputs[2], c1.inputs["A"]); L.new(c_iris.outputs[2], c1.inputs["B"])
    c2 = node("ShaderNodeMix", data_type="RGBA")
    L.new(pup_m, c2.inputs["Factor"]); L.new(c1.outputs[2], c2.inputs["A"]); c2.inputs["B"].default_value = (0.004, 0.003, 0.003, 1)
    c3 = node("ShaderNodeMix", data_type="RGBA")
    L.new(math("MULTIPLY", hl, iris_m), c3.inputs["Factor"]); L.new(c2.outputs[2], c3.inputs["A"]); c3.inputs["B"].default_value = (1, 1, 1, 1)
    EYE_MIX.append((eye_m, c3.outputs[2]))

# ── 1. 材質眼皮 ──（閉眼時網格不動 → 用物件座標，比較平滑；靜止座標逐三角面直線內插，細線會變鋸齒）
tco = node("ShaderNodeTexCoord")
sepo = node("ShaderNodeSeparateXYZ")
L.new(tco.outputs["Object"], sepo.inputs[0])
X, Z = sepo.outputs[0], sepo.outputs[2]
color = bsdf.inputs["Base Color"].links[0].from_socket
for m_, c_ in EYE_MIX:
    mm = node("ShaderNodeMix", data_type="RGBA")
    L.new(m_, mm.inputs["Factor"]); L.new(color, mm.inputs["A"]); L.new(c_, mm.inputs["B"])
    color = mm.outputs[2]
for key, side in (("L", "Left"), ("R", "Right")):
    e = LM["eyes"][key]
    cx, cy, cz = e["c"]
    ew, eh = e["ew"] * 1.25, e["eh"] * 1.35
    sgn = 1 if key == "L" else -1
    pts = [(cx - sgn * 1.5 * e["ew"], cz - 0.2 * e["eh"]), (cx - sgn * 0.8 * e["ew"], cz - 1.9 * e["eh"]), (cx, cz - 2.0 * e["eh"])]
    samp = []
    for x_, z_ in pts:
        for _, i, _ in kd.find_n(Vector((x_, cy, z_)), 6):
            samp.append(px[int(v2uv[i][1] * (H - 1)), int(v2uv[i][0] * (W - 1)), :3])
    sk = np.median(samp, 0) ** 2.2
    b = val("BLINK_" + side)
    dx_ = math("DIVIDE", math("SUBTRACT", X, cx), ew)
    dz_ = math("DIVIDE", math("SUBTRACT", Z, cz), eh)
    r2 = math("ADD", math("MULTIPLY", dx_, dx_), math("MULTIPLY", dz_, dz_))
    inside = math("SUBTRACT", 1.0, smooth(r2, 0.8, 1.05))
    lid = math("SUBTRACT", math("SUBTRACT", 1.0, math("MULTIPLY", b, 1.35)),
               math("MULTIPLY", math("MULTIPLY", b, 0.35), math("SUBTRACT", 1.0, math("MULTIPLY", dx_, dx_))))
    cover = math("MULTIPLY", inside, smooth(math("SUBTRACT", dz_, lid), -0.06, 0.06))
    cover = math("MULTIPLY", cover, smooth(b, 0.0, 0.08))
    dist = math("ABSOLUTE", math("SUBTRACT", dz_, lid))
    thick = math("MULTIPLY", 0.07, math("SUBTRACT", 1.0, math("MULTIPLY", dx_, dx_)))
    line = math("MULTIPLY", math("SUBTRACT", 1.0, smooth(math("DIVIDE", dist, math("MAXIMUM", thick, 0.001)), 0.3, 1.2)), math("SUBTRACT", 1.0, smooth(r2, 0.85, 0.98)))
    line = math("MULTIPLY", line, math("MINIMUM", math("MULTIPLY", b, 2.0), 1.0))
    m1 = node("ShaderNodeMix", data_type="RGBA")
    m1.inputs["B"].default_value = (*sk, 1)
    L.new(cover, m1.inputs["Factor"])
    L.new(color, m1.inputs["A"])
    m2 = node("ShaderNodeMix", data_type="RGBA")
    m2.inputs["B"].default_value = (0.02, 0.015, 0.015, 1)
    L.new(line, m2.inputs["Factor"])
    L.new(m1.outputs[2], m2.inputs["A"])
    color = m2.outputs[2]
    print("[eyes] %s眼皮膚色 %s" % (key, np.round(sk, 3)))
# ── 4. 嘴角笑紋：AI 畫在貼圖上的嘴角深色短線，張嘴一拉就變成往臉頰的長折線 → 張得越開越淡（JAW_OPEN 由 jawOpen 推）──
tcr = node("ShaderNodeAttribute", attribute_name="rest")
sepr = node("ShaderNodeSeparateXYZ")
L.new(tcr.outputs["Vector"], sepr.inputs[0])
RX, RZ = sepr.outputs[0], sepr.outputs[2]
jaw = val("JAW_OPEN")
skin_m = np.median(col_at_verts(np.where((V[:, 1] < -0.3) & (np.abs(V[:, 0] - LM["mouth"]["L"][0]) < 0.08) & (np.abs(V[:, 2] - LM["mouth"]["L"][2] - 0.06) < 0.03))[0]), 0) ** 2.2
cm_tot = None
for k in ("L", "R"):
    mx_, _, mz_ = LM["mouth"][k]
    ddx = math("SUBTRACT", RX, mx_)
    ddz = math("SUBTRACT", RZ, mz_)
    dd = math("SQRT", math("ADD", math("MULTIPLY", ddx, ddx), math("MULTIPLY", ddz, ddz)))
    mk = math("SUBTRACT", 1.0, smooth(dd, 0.03, 0.07))
    cm_tot = mk if cm_tot is None else math("MAXIMUM", cm_tot, mk)
bw = node("ShaderNodeRGBToBW")
L.new(color, bw.inputs["Color"])
darkish = math("SUBTRACT", 1.0, smooth(bw.outputs[0], 0.25, 0.45))  # 只淡化偏暗的筆畫，膚色不變
fade = math("MULTIPLY", math("MULTIPLY", cm_tot, darkish), smooth(jaw, 0.05, 0.4))
mf = node("ShaderNodeMix", data_type="RGBA")
mf.inputs["B"].default_value = (*skin_m, 1)
L.new(fade, mf.inputs["Factor"]); L.new(color, mf.inputs["A"])
color = mf.outputs[2]
L.new(color, bsdf.inputs["Base Color"])
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("[eyes] 存檔", OUT)
