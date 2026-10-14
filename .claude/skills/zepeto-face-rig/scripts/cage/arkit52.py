# 乙路線第 4 步：依網格結構產生 ARKit 52 個表情（形態鍵）。
#   所有包上同一個模板的臉，頂點順序、哪幾圈是眼皮、哪些面是嘴唇都一樣 → 這支程式不寫死任何一張臉的座標，
#   只用「網格結構＋這張臉的五官位置」產生，換一張臉跑一次就有 52 個表情。
#   規則：
#   - 眼皮：眼皮那幾圈繞「這隻眼球的中心」旋轉（在眼球的橢球座標裡轉 → 眼皮沿眼球表面滑，不會穿進去）
#   - 眼珠：轉眼球物件自己的網格（反光點畫在材質上，跟著轉）；看上／看下時上眼皮也跟一點
#   - 下巴：嘴巴線以下的臉、下唇、口腔底、下排牙齒牙齦、舌頭，繞下顎軸轉
#   - 其他（嘴角、嘴唇、眉毛、臉頰、鼻翼）：五官附近平滑權重推拉
#   ARKit 慣例：每個零件各有同名形態鍵（Head 有全部 52 個；Eye_L／Eye_R 有自己那側的 eyeLook；
#   下排牙齒、牙齦、舌頭有 jaw*、tongueOut），表情捕捉時用名稱一起驅動。
#   模板沒有舌頭 → 這裡先做一條（平常躺在口腔底，tongueOut 往前伸出）。
# 用法：blender.exe -b head_v1.blend --python arkit52.py -- <AI 五官 landmarks.json>
#   存成 head_arkit.blend，各形態鍵的最大位移寫到 arkit_report.json
import bpy, os, bmesh, os, sys, json, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
# 每張臉的輸出資料夾（環境變數 ZEPETO_RIG_WORK）與模板資料夾（ZEPETO_RIG_TEMPLATE）；run_face_rig.py 會設好
WORK = os.environ.get("ZEPETO_RIG_WORK") or os.getcwd()
TEMPLATE = os.environ.get("ZEPETO_RIG_TEMPLATE") or os.path.normpath(
    os.path.join(_SCRIPTS, "..", "..", "..", "..", "docs", "data", "blender", "zepeto", "templates", "cartoon-head-lucadrech"))
HERE = WORK
LM = json.load(open(sys.argv[sys.argv.index("--") + 1], encoding="utf-8"))
REP = json.load(open(os.path.join(HERE, "wrap_report.json"), encoding="utf-8"))
U = REP["U"]
sc = bpy.context.scene
head = bpy.data.objects["Head"]
eyes = {"L": bpy.data.objects["Eye_L"], "R": bpy.data.objects["Eye_R"]}
jaw_parts = [bpy.data.objects[n] for n in ("bottom_teeth", "bottom_gum")]

ARKIT_52 = [
    "eyeBlinkLeft", "eyeLookDownLeft", "eyeLookInLeft", "eyeLookOutLeft", "eyeLookUpLeft", "eyeSquintLeft", "eyeWideLeft",
    "eyeBlinkRight", "eyeLookDownRight", "eyeLookInRight", "eyeLookOutRight", "eyeLookUpRight", "eyeSquintRight", "eyeWideRight",
    "jawForward", "jawLeft", "jawRight", "jawOpen",
    "mouthClose", "mouthFunnel", "mouthPucker", "mouthLeft", "mouthRight",
    "mouthSmileLeft", "mouthSmileRight", "mouthFrownLeft", "mouthFrownRight",
    "mouthDimpleLeft", "mouthDimpleRight", "mouthStretchLeft", "mouthStretchRight",
    "mouthRollLower", "mouthRollUpper", "mouthShrugLower", "mouthShrugUpper",
    "mouthPressLeft", "mouthPressRight", "mouthLowerDownLeft", "mouthLowerDownRight",
    "mouthUpperUpLeft", "mouthUpperUpRight",
    "browDownLeft", "browDownRight", "browInnerUp", "browOuterUpLeft", "browOuterUpRight",
    "cheekPuff", "cheekSquintLeft", "cheekSquintRight",
    "noseSneerLeft", "noseSneerRight",
    "tongueOut",
]


def smooth01(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def band(v, full_lo, full_hi, zero_lo, zero_hi):
    """一維權重：[full_lo, full_hi] 為 1，往外平滑降到 zero_lo／zero_hi 為 0"""
    w = np.ones_like(v)
    lo, hi = v < full_lo, v > full_hi
    w[lo] = 1 - smooth01((full_lo - v[lo]) / max(full_lo - zero_lo, 1e-6))
    w[hi] = 1 - smooth01((v[hi] - full_hi) / max(zero_hi - full_hi, 1e-6))
    return w


def world_verts(ob):
    return np.array([ob.matrix_world @ v.co for v in ob.data.vertices])


# ── Head 的頂點、法線、網格結構 ──
me = head.data
P = world_verts(head)  # Head 物件沒有變換，世界＝局部
N = len(P)
NRM = np.array([v.normal[:] for v in me.vertices])
X, Y, Z = P[:, 0], P[:, 1], P[:, 2]
mat_i = {m.name: i for i, m in enumerate(me.materials)}
lip_v = np.array(sorted({v for p in me.polygons if p.material_index == mat_i["ZEPETO_Lips"] for v in p.vertices}))
inner_v = np.array(sorted({v for p in me.polygons if p.material_index == mat_i["Mouth_Inner"] for v in p.vertices}))
IS_LIP = np.zeros(N, bool)
IS_LIP[lip_v] = True
IS_INNER = np.zeros(N, bool)
IS_INNER[inner_v] = True

# 嘴：嘴角＝嘴唇最左右；嘴巴線＝通過兩嘴角與正中縫的拋物線
front_lip = lip_v[Y[lip_v] < Y[lip_v].min() + 0.08]
kl, kr = front_lip[np.argmax(X[front_lip])], front_lip[np.argmin(X[front_lip])]
K = {"L": P[kl], "R": P[kr]}
mid = front_lip[np.abs(X[front_lip]) < 0.02]
slit_c0 = float(np.median(Z[mid]))
k_half = (K["L"][0] - K["R"][0]) / 2
mouth_y = float(Y[front_lip].min())
# 上唇／下唇：看網格連接，不看高度。
#   模板的上下唇在嘴巴中段是分開的（中間一道縫、沒有面相連），只在兩邊嘴角和口腔最深處接在一起。
#   → 從上唇正中最高點出發，沿「嘴唇＋口腔前緣」往外長、不經過嘴角與口腔深處，長得到的就是上唇。
#   （用理想拋物線分：上唇內側中間幾點落在線下，張嘴時被當下唇拉下來，開口變倒 V；
#     用「高度上最大的空隙」找縫：嘴唇上的頂點本來就稀疏，最大空隙常在嘴唇中間，不在縫上）
ADJ = [[] for _ in range(N)]
for e in me.edges:
    a, b = e.vertices
    ADJ[a].append(b)
    ADJ[b].append(a)
EDG = np.array([e.vertices[:] for e in me.edges])
DEG = np.maximum(np.bincount(EDG.ravel(), minlength=N), 1).astype(float)


def smooth_disp(D, free, iters=14):
    """位移場沿網格平滑：free 的頂點反覆取鄰居平均，其餘固定"""
    D = D.copy()
    for _ in range(iters):
        acc = np.zeros_like(D)
        np.add.at(acc, EDG[:, 0], D[EDG[:, 1]])
        np.add.at(acc, EDG[:, 1], D[EDG[:, 0]])
        D[free] = 0.5 * D[free] + 0.5 * (acc / DEG[:, None])[free]
    return D


mx_ = (K["L"][0] + K["R"][0]) / 2
cand = (IS_LIP | IS_INNER) & (Y < mouth_y + 0.3 * U) & (np.abs(X - mx_) < 0.85 * k_half)
seed = int(mid[np.argmax(Z[mid])])
upper_set = {seed}
stack = [seed]
while stack:
    v = stack.pop()
    for u in ADJ[v]:
        if cand[u] and u not in upper_set:
            upper_set.add(u)
            stack.append(u)
UP_LIP = np.zeros(N, bool)
UP_LIP[list(upper_set)] = True
lower_front = cand & ~UP_LIP
if UP_LIP.sum() < 10 or lower_front.sum() < 10:
    raise SystemExit(f"[arkit] 上下唇沒分開：上 {UP_LIP.sum()}、下 {lower_front.sum()}（嘴巴中段可能沒有縫）")
cm = np.abs(X - mx_) < 0.15 * k_half
slit_c = float((Z[UP_LIP & cm].min() + Z[lower_front & cm].max()) / 2)
a_par = ((K["L"][2] + K["R"][2]) / 2 - slit_c) / (k_half ** 2)
slit_z = slit_c + a_par * (X - mx_) ** 2  # 皮膚與嘴角用的嘴巴線高度
UPPER = Z > slit_z
UPPER[cand] = UP_LIP[cand]  # 嘴巴中段的嘴唇與口腔前緣：照連接關係
MC = np.array([0.0, mouth_y, slit_c])
mw = k_half

# 眼睛
eye = {}
for k in ("L", "R"):
    eo = eyes[k]
    er = REP["eye_rings"][k]
    rd = np.full(N, 99)
    for v, d in er["rd"].items():
        rd[int(v)] = d
    eye[k] = dict(c=np.array(eo.location), radii=np.array(eo.scale), q=eo.rotation_quaternion.copy(), rd=rd, m=er["margin"])

U_eye = abs(eye["L"]["c"][0] - eye["R"]["c"][0])

SH = {name: {} for name in ARKIT_52}  # 形態鍵 → {物件名: 位移陣列}
CORR_KEY = "jawOpen_smile_corr"


def add(name, obj_name, D):
    if isinstance(D, tuple):  # 眼球的旋轉指令（"rot", 軸, 角度），不和位移相加
        SH[name][obj_name] = D
    else:
        SH[name][obj_name] = SH[name].get(obj_name, 0) + D


# ── 眼皮：在眼球的單位球座標裡繞局部 X 軸旋轉 ──
def lid_rotate(k, angle_up, angle_low, verts_mask=None):
    """上眼皮轉 angle_up（正＝往下蓋）、下眼皮轉 angle_low（正＝往上）。回傳 Head 的位移"""
    g = eye[k]
    Rm = np.array(g["q"].to_matrix())
    loc = ((P - g["c"]) @ Rm) / g["radii"]  # 眼球局部單位球座標（−Y 是視線）
    d = g["rd"] - g["m"]
    w_ring = np.select([d <= 0, d == 1, d == 2, d == 3, d == 4, d == 5, d == 6], [1.0, 1.0, 0.95, 0.78, 0.52, 0.27, 0.08], 0.0)  # 多兩圈、漸變較緩，減少閉眼時的弧形摺痕
    vert = smooth01(np.abs(loc[:, 2]) / 0.35)  # 眼角（上下交界）少動
    # 眉毛保護：上眼皮的影響往上最多到眉毛下緣（第一版沒擋，眨眼時眉毛被拉成一團黑）
    brow_bottom = LM["brows"][k]["bottom"]
    guard = 1 - smooth01((Z - (brow_bottom - 0.05 * U)) / (0.04 * U))
    up_w = w_ring * vert * (loc[:, 2] > 0) * guard
    lo_w = w_ring * vert * (loc[:, 2] <= 0)
    D = np.zeros((N, 3))
    for w_, ang in ((up_w, angle_up), (lo_w, -angle_low)):
        sel = w_ > 0
        if not sel.any() or ang == 0:
            continue
        th = ang * w_[sel]  # 正角＝往下（−Z）轉：視線方向的點 (0, −cos a, sin a) 轉成仰角 a − th
        c_, s_ = np.cos(th), np.sin(th)
        y0, z0 = loc[sel, 1], loc[sel, 2]
        y1 = c_ * y0 - s_ * z0
        z1 = s_ * y0 + c_ * z0
        nl = loc[sel].copy()
        nl[:, 1], nl[:, 2] = y1, z1
        D[sel] += (nl * g["radii"]) @ Rm.T + g["c"] - P[sel]
    # 眼皮外圈（第 2～7 圈）的位移做平滑，去掉閉眼時眼角往外上的摺痕；眼皮邊緣兩圈不動
    # 只平滑上眼皮那側、第 3～7 圈，眉毛保護區不動（第一次試：眉毛被平滑拉下來、瞇眼時下眼皮反摺）
    #   用漸變混合，不用硬切（硬切 z>0.1 時眼頭出現台階）
    Ds = smooth_disp(D, (d >= 3) & (d <= 7))
    blend = smooth01((loc[:, 2] + 0.05) / 0.3) * guard
    return D + (Ds - D) * blend[:, None]


def lid_angles(k):
    """上、下眼皮邊緣正中在眼球單位球上的仰角（弧度）"""
    g = eye[k]
    Rm = np.array(g["q"].to_matrix())
    rim = np.where(g["rd"] == g["m"])[0]
    loc = ((P[rim] - g["c"]) @ Rm) / g["radii"]
    up = rim[np.argmax(loc[:, 2])]
    lo = rim[np.argmin(loc[:, 2])]
    el = lambda v: math.atan2(((P[v] - g["c"]) @ Rm / g["radii"])[2], -((P[v] - g["c"]) @ Rm / g["radii"])[1])
    return el(up), el(lo)


for k, nm in (("L", "Left"), ("R", "Right")):
    a_up, a_lo = lid_angles(k)
    meet = a_lo + 0.3 * (a_up - a_lo)  # 上下眼皮在偏下 30% 處相遇
    over = 0.06 * (a_up - a_lo)  # 上眼皮多蓋過相遇點一點，下眼皮也多上來一點，閉到底不露眼珠
    add(f"eyeBlink{nm}", "Head", lid_rotate(k, a_up - meet + over, meet - a_lo + 0.5 * over))
    add(f"eyeSquint{nm}", "Head", lid_rotate(k, 0.12 * (a_up - a_lo), 0.4 * (a_up - a_lo)))
    add(f"eyeWide{nm}", "Head", lid_rotate(k, -0.22 * (a_up - a_lo), -0.08 * (a_up - a_lo)))
    # 眼珠轉動：上下 22°、內外 28°；看上／下時上眼皮跟 35%
    #   局部 X 軸轉 θ：視線 (0,−1,0) → z＝−sin θ（θ 負＝往上看）；局部 Z 軸轉 θ：x＝sin θ（左眼往內＝往 −X）
    #   眼皮角度正＝往下蓋，所以看上（θ 負）時眼皮角度也是負的（往上收）
    side = 1 if k == "L" else -1
    for key, axis, ang, lid in (("Up", 'X', -22, 0.35), ("Down", 'X', 22, 0.35), ("In", 'Z', -28 * side, 0), ("Out", 'Z', 28 * side, 0)):
        add(f"eyeLook{key}{nm}", f"Eye_{k}", ("rot", axis, math.radians(ang)))
        if lid:
            add(f"eyeLook{key}{nm}", "Head", lid_rotate(k, math.radians(ang) * lid, 0.0))


# ── 上眼皮邊緣的立體眼線（Lash_L／Lash_R）──
#   畫在眼皮上的眼線只蓋住中段，閉眼時兩側眼角的接縫露出一道淺色弧線，中段的眼線又被壓扁成一團。
#   → 沿上眼皮邊緣（眼頭到眼尾）做一條兩端漸細的扁管，跟著上眼皮同樣的轉法動：睜眼時疊在原本眼線上，閉眼時是一條乾淨的「︶」。
LASH_UP = {}  # 眼 → {形態鍵: 上眼皮角度}
for k, nm in (("L", "Left"), ("R", "Right")):
    a_up, a_lo = lid_angles(k)
    meet = a_lo + 0.3 * (a_up - a_lo)
    over = 0.06 * (a_up - a_lo)
    LASH_UP[k] = {f"eyeBlink{nm}": a_up - meet + over, f"eyeSquint{nm}": 0.12 * (a_up - a_lo),
                  f"eyeWide{nm}": -0.22 * (a_up - a_lo),
                  f"eyeLookUp{nm}": math.radians(-22) * 0.35, f"eyeLookDown{nm}": math.radians(22) * 0.35}


def lash_tube(k):
    g = eye[k]
    Rm = np.array(g["q"].to_matrix())
    rim = np.where(g["rd"] == g["m"])[0]
    loc = ((P[rim] - g["c"]) @ Rm) / g["radii"]
    sel = loc[:, 2] > 0.0  # 上半圈（含 -0.12 時眼尾會勾回下半圈，閉眼時豎起一截）
    pts, lc = P[rim][sel], loc[sel]
    order = np.argsort(lc[:, 0])
    pts = pts[order]
    keep = smooth01(np.abs(lc[order][:, 2]) / 0.35) > 0.45  # 眼角那段眼皮幾乎不動、會被皮膚蓋住只露出尖端 → 去掉
    pts = pts[np.argmax(keep):len(keep) - np.argmax(keep[::-1])]
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    S_N = 48
    tt = np.linspace(0, seg[-1], S_N)
    C = np.stack([np.interp(tt, seg, pts[:, i]) for i in range(3)], 1)
    for _ in range(3):  # 輕微平滑，去掉網格的折角
        C[1:-1] = 0.5 * C[1:-1] + 0.25 * (C[:-2] + C[2:])
    r0 = 0.045 * g["radii"][2]
    ZL = bool(os.environ.get("ZEPETO_LINER"))
    if ZL:  # （試做・ZEPETO）眼線加粗、越往眼尾越粗，眼尾往外上方延伸一截（上揚眼線）
        if abs(C[0, 0]) > abs(C[-1, 0]):
            C = C[::-1].copy()  # 眼尾放最後
        t_end = C[-1] - C[-4]
        t_end /= np.linalg.norm(t_end)
        wdir = t_end * 0.75 + np.array([0, 0, 0.55])
        wdir /= np.linalg.norm(wdir)
        L_w = 0.45 * seg[-1]
        C = np.vstack([C, [C[-1] + wdir * L_w * j / 8 for j in range(1, 9)]])
        S_N = len(C)
    verts, rings = [], 10
    for i in range(S_N):
        t = C[min(i + 1, S_N - 1)] - C[max(i - 1, 0)]
        t /= np.linalg.norm(t)
        n = C[i] - g["c"]
        n -= t * (n @ t)
        n /= np.linalg.norm(n)
        b = np.cross(t, n)
        if b @ (Rm[:, 2]) < 0:
            b = -b  # b 朝眼皮那邊（眼球局部 +Z）
        s = i / (S_N - 1)
        r = r0 * math.sin(math.pi * s) ** 0.6 if not ZL else r0 * 2.0 * min(1, s / 0.15) ** 0.6 * min(1, (1 - s) / 0.12) * (0.7 + 0.6 * s)  # 兩端收到 0：眼尾那截不太跟眼皮動，閉眼時會翹出一個小黑點
        ctr = C[i] + b * 0.3 * r + n * 0.4 * r  # 貼著眼皮邊緣（0.9r 時睜眼浮在眼皮上方、有一條縫），往外一點不被皮膚蓋住
        for j in range(rings):
            ang = 2 * math.pi * j / rings
            verts.append(ctr + b * r * math.cos(ang) + n * 0.45 * r * math.sin(ang))
    faces = [(i * rings + j, i * rings + (j + 1) % rings, (i + 1) * rings + (j + 1) % rings, (i + 1) * rings + j)
             for i in range(S_N - 1) for j in range(rings)]
    faces += [tuple(range(rings))[::-1], tuple((S_N - 1) * rings + j for j in range(rings))]
    me_ = bpy.data.meshes.new(f"Lash_{k}")
    me_.from_pydata([tuple(v) for v in verts], [], faces)
    for poly in me_.polygons:
        poly.use_smooth = True
    ml = bpy.data.materials.get("Lash") or bpy.data.materials.new("Lash")
    bs = next(nd for nd in ml.node_tree.nodes if nd.type == 'BSDF_PRINCIPLED')
    bs.inputs['Base Color'].default_value = (0.006, 0.004, 0.004, 1)
    bs.inputs['Roughness'].default_value = 0.95
    if 'Specular IOR Level' in bs.inputs:
        bs.inputs['Specular IOR Level'].default_value = 0.0
    me_.materials.append(ml)
    old = bpy.data.objects.get(f"Lash_{k}")
    if old:
        bpy.data.objects.remove(old)
    ob = bpy.data.objects.new(f"Lash_{k}", me_)
    sc.collection.objects.link(ob)
    # 每個管段跟著它中心點那個位置的上眼皮轉（眼角少動，與 lid_rotate 的 vert 權重相同）
    V_ = np.array(verts)
    lc_all = ((V_ - g["c"]) @ Rm) / g["radii"]
    ctr_loc = ((C - g["c"]) @ Rm) / g["radii"]
    w_seg = np.repeat(smooth01(np.abs(ctr_loc[:, 2]) / 0.35) * (ctr_loc[:, 2] > -0.05), rings)
    for key, ang in LASH_UP[k].items():
        th = ang * w_seg
        c_, s_ = np.cos(th), np.sin(th)
        nl = lc_all.copy()
        nl[:, 1] = c_ * lc_all[:, 1] - s_ * lc_all[:, 2]
        nl[:, 2] = s_ * lc_all[:, 1] + c_ * lc_all[:, 2]
        add(key, ob.name, (nl * g["radii"]) @ Rm.T + g["c"] - V_)
    return ob


LASH = {k: lash_tube(k) for k in ("L", "R")}


# ── 一般推拉的權重工具 ──
def ellw(c, rx, rz, inner=0.3, depth=0.5):
    d = np.sqrt(((X - c[0]) / rx) ** 2 + ((Z - c[2]) / rz) ** 2)
    w = 1 - smooth01((d - inner) / (1 - inner))
    w[Y > c[1] + depth * U] = 0
    return w


def V(dx=0.0, dy=0.0, dz=0.0):
    return np.array([dx, dy, dz]) * U


NOT_LID = np.ones(N)
for k in ("L", "R"):
    NOT_LID *= smooth01((eye[k]["rd"] - eye[k]["m"] - 2) / 3.0)  # 眼皮不給嘴巴、臉頰、眉毛的推拉動到
NOT_INNER = (~IS_INNER).astype(float)

# ── 眉毛（位置取自 AI 頭的五官：包覆後兩者同一個座標） ──
for k, nm, side in (("L", "Left", 1), ("R", "Right", -1)):
    b = LM["brows"][k]
    e = eye[k]
    eye_top = e["c"][2] + e["radii"][2] * 0.8
    hl = b["half_len"]

    def brow_w(xc, full, zero):
        return (band(X, xc - full, xc + full, xc - zero, xc + zero)
                * band(Z, b["bottom"], b["top"], eye_top + 0.02 * U, b["top"] + 0.45 * U)
                * (Y < e["c"][1] + 0.3 * U) * NOT_LID)

    inner_ness = smooth01(1 - np.abs(X - b["inner"][0]) / (2 * hl + 1e-6))
    add(f"browDown{nm}", "Head", (brow_w(b["center"][0], 1.05 * hl, 1.6 * hl) * (0.7 + 0.3 * inner_ness))[:, None] * V(dx=-side * 0.03, dz=-0.08))
    add(f"browOuterUp{nm}", "Head", brow_w(b["outer"][0], 0.6 * hl, 1.8 * hl)[:, None] * V(dz=0.10))
    add("browInnerUp", "Head", brow_w(b["inner"][0], 0.6 * hl, 1.8 * hl)[:, None] * V(dz=0.12))

# ── 嘴角、嘴唇 ──
# 唇緣曲線（給倒三角笑）：每個 x 位置上唇最低點、下唇最高點的高度
_bx = np.linspace(MC[0] - 1.6 * mw, MC[0] + 1.6 * mw, 41)
_ul = IS_LIP & UPPER
_ll = IS_LIP & ~UPPER
_ue, _le = [], []
for _x in _bx:
    _m = np.abs(X - _x) < 0.06 * mw
    _ue.append(Z[_m & _ul].min() if (_m & _ul).any() else np.nan)
    _le.append(Z[_m & _ll].max() if (_m & _ll).any() else np.nan)
_ue, _le = np.array(_ue), np.array(_le)
_ok_u, _ok_l = ~np.isnan(_ue), ~np.isnan(_le)
UP_EDGE = np.interp(X, _bx[_ok_u], _ue[_ok_u])
LO_EDGE = np.interp(X, _bx[_ok_l], _le[_ok_l])
SMILE_LINE = np.interp(MC[0], _bx[_ok_u], _ue[_ok_u]) + 0.05 * U
LO_CORNER = smooth01((np.abs(X - MC[0]) - 0.3 * mw) / (0.7 * mw))
for k, nm, side in (("L", "Left", 1), ("R", "Right", -1)):
    Kp = K[k]
    wk = (ellw(Kp, mw * 0.95, mw * 0.8, inner=0.15) * NOT_LID)[:, None]
    cheek = (ellw(Kp + V(dx=side * 0.12, dz=0.24), 0.26 * U, 0.22 * U, inner=0.2) * NOT_LID * NOT_INNER)[:, None]
    # 上唇（靠上排牙齒那條）保持水平、只有最邊邊的嘴角往上翹；整塊往上提時上唇被拉成斜線，笑的角度太大（使用者看開心笑、大笑後的回饋）
    ax_s = np.abs(X - MC[0])
    #   倒三角笑「▽」：上唇下緣拉成一條水平線（中間比原本高 0.05U、露出上排牙齒），下唇的嘴角那端也拉到同一條線、中間不動 → 下唇成 V
    #   （上唇整塊照嘴角往上提：上唇被拉成斜線、笑的角度太大；上唇整條等量抬：原本的唇形是拱形「⌒」，抬了還是拱形）
    #   左右兩個形態鍵各負責一半（w_half），兩邊都開時剛好是完整的 ▽
    up_lip = UPPER & (IS_LIP | IS_INNER) & (Y < mouth_y + 0.3 * U) & (ax_s < 1.6 * mw)
    lo_lip = ~UPPER & (IS_LIP | IS_INNER) & (Y < mouth_y + 0.3 * U) & (ax_s < 1.6 * mw)
    w_half = smooth01(np.clip(side * (X - MC[0]) / (2 * mw) + 0.5, 0, 1))
    up_fall = 1 - smooth01((ax_s - 1.1 * mw) / (0.5 * mw))
    Ds = wk * V(dx=side * 0.13, dy=0.05)
    Ds += np.where(up_lip | lo_lip, 0.0, 1.0)[:, None] * wk * V(dz=0.08)  # 嘴唇以外（臉頰、笑紋）照嘴角往上提
    Ds[:, 2] += (up_lip * w_half * up_fall) * (SMILE_LINE - UP_EDGE)
    Ds[:, 2] += (lo_lip * w_half * up_fall * LO_CORNER) * (SMILE_LINE - LO_EDGE)
    Ds[:, 2] -= (lo_lip * w_half * (1 - LO_CORNER)) * 0.03 * U  # 下唇中間再往下一點，倒三角開口大一點（使用者回饋）
    # 皮膚上的位移沿網格平滑（嘴唇不動）：拉動範圍邊界太硬時，從鼻翼到嘴角折出一道很深的法令紋，大笑看起來恐怖（使用者回饋）
    skin_s = ~IS_LIP & ~IS_INNER & (np.abs(X - MC[0]) < 2.6 * mw) & (Z > slit_c - 0.6 * U) & (Z < slit_c + 0.7 * U)
    Ds = smooth_disp(Ds + cheek * V(dz=0.045, dy=-0.01), skin_s, iters=16)
    add(f"mouthSmile{nm}", "Head", Ds)
    add(f"mouthFrown{nm}", "Head", wk * V(dx=side * 0.015, dz=-0.10))
    add(f"mouthDimple{nm}", "Head", wk * V(dx=side * 0.10, dy=0.13))
    add(f"mouthStretch{nm}", "Head", wk * V(dx=side * 0.17, dz=-0.07))
    half = MC + np.array([side * mw * 0.5, 0, 0])
    w_side = ellw(half, mw * 0.95, 0.3 * U, inner=0.35)
    Dp = np.zeros((N, 3))
    Dp[:, 2] = w_side * 0.9 * (slit_z - Z) * (IS_LIP | IS_INNER)
    Dp[:, 1] = w_side * 0.05 * U * (IS_LIP | IS_INNER)  # 嘴唇壓扁並往內收
    Dp[:, 0] = w_side * side * 0.04 * U
    add(f"mouthPress{nm}", "Head", Dp)
    add(f"mouthUpperUp{nm}", "Head", (ellw(half + V(dz=0.06), mw * 0.75, 0.16 * U) * UPPER * NOT_INNER)[:, None] * V(dz=0.07))
    add(f"mouthLowerDown{nm}", "Head", (ellw(half + V(dz=-0.06), mw * 0.75, 0.18 * U) * (~UPPER) * NOT_INNER)[:, None] * V(dz=-0.08))
    # 鼻翼、臉頰
    add(f"noseSneer{nm}", "Head", (ellw(MC + V(dx=side * 0.12, dz=0.30), 0.14 * U, 0.14 * U, inner=0.2) * NOT_LID)[:, None] * V(dy=-0.02, dz=0.11))
    e = eye[k]
    # 臉頰上推：範圍收小、不碰到嘴角（原本一路延伸到嘴角，單獨開嘴巴也會變笑，疊在大笑上摺痕更深），幅度也降一點
    add(f"cheekSquint{nm}", "Head", (ellw(e["c"] + np.array([0, 0, -e["radii"][2] * 1.5]), e["radii"][0] * 1.3, e["radii"][2] * 0.8, inner=0.3)
                                    * smooth01((e["rd"] - e["m"] - 1) / 3.0) * smooth01((Z - slit_c - 0.15 * U) / (0.25 * U)))[:, None] * V(dy=-0.04, dz=0.13))

w_mouth = ellw(MC, mw * 1.25, mw * 0.8, inner=0.25)
w_mouth_all = w_mouth * NOT_LID
add("mouthLeft", "Head", ellw(MC, mw * 1.45, mw * 0.85, inner=0.3)[:, None] * V(dx=0.13))
add("mouthRight", "Head", ellw(MC, mw * 1.45, mw * 0.85, inner=0.3)[:, None] * V(dx=-0.13))
D = np.zeros((N, 3)); D[:, 0] = -0.28 * (X - MC[0]) * w_mouth_all; D[:, 1] = -0.07 * U * w_mouth_all; D[:, 2] = 0.12 * (Z - slit_c) * w_mouth_all
add("mouthFunnel", "Head", D)
D = np.zeros((N, 3)); D[:, 0] = -0.5 * (X - MC[0]) * w_mouth_all; D[:, 1] = -0.12 * U * w_mouth_all; D[:, 2] = -0.12 * (Z - slit_c) * w_mouth_all
add("mouthPucker", "Head", D)
w_up = (ellw(MC + V(dz=0.07), mw * 1.05, 0.14 * U) * UPPER)[:, None]
w_lo = (ellw(MC + V(dz=-0.07), mw * 1.05, 0.14 * U) * (~UPPER))[:, None]
add("mouthRollUpper", "Head", w_up * V(dy=0.05, dz=-0.09))  # 往後太多（0.13）會縮到牙齒後面、露牙
add("mouthRollLower", "Head", w_lo * V(dy=0.05, dz=0.09))
add("mouthShrugUpper", "Head", w_up * V(dy=-0.05, dz=0.05) + w_lo * V(dy=-0.03, dz=0.05))  # 上唇往前上嘟、下唇跟著上來，不露牙
add("mouthShrugLower", "Head", (ellw(MC + V(dz=-0.16), mw * 1.15, 0.26 * U) * (~UPPER))[:, None] * V(dy=-0.04, dz=0.11))

# 鼓臉頰：嘴角外上方兩團沿法線往外
for side in (1, -1):
    c = MC + V(dx=side * (mw / U + 0.22), dz=0.15)
    add("cheekPuff", "Head", (ellw(c, 0.3 * U, 0.3 * U, inner=0.2) * NOT_LID * NOT_INNER)[:, None] * (NRM * 0.12 * U + V(dx=side * 0.02)))

# ── 下巴：嘴巴線以下、下巴以上（脖子不動），繞耳朵前方的下顎軸轉 ──
chin_z = REP["ai_chin_z"]
throat_far = Y.max()
w_jaw = smooth01((slit_z - Z - 0.005 * U) / (0.14 * U))
w_jaw *= 1 - smooth01((chin_z - 0.12 * U - Z) / (0.3 * U))  # 下巴以下（脖子）漸漸不動
w_jaw *= 1 - smooth01((np.abs(X) - 0.62 * U) / (0.3 * U))   # 往耳朵方向漸漸不動
w_jaw[(Y > mouth_y + 0.95 * U) & ~IS_INNER] = 0              # 後腦、頸後不動
inner_floor = IS_INNER & ~UPPER
w_jaw[inner_floor] = np.maximum(w_jaw[inner_floor], 1 - smooth01((Y[inner_floor] - (mouth_y + 0.45 * U)) / (0.35 * U)))  # 口腔底，越靠喉嚨越不動
w_jaw[IS_INNER & UPPER] = 0                                   # 上顎不動
# 下唇與嘴唇內側整片跟著下巴（第一版下唇剛好在嘴巴線上、權重近 0，嘴打不開）；只有嘴角漸變，避免撕裂
corner_fall = 1 - smooth01((np.abs(X) - 0.65 * mw) / (0.45 * mw))
low_lip = (IS_LIP | (IS_INNER & (Y < mouth_y + 0.25 * U))) & ~UPPER
w_jaw[low_lip] = np.maximum(w_jaw[low_lip], corner_fall[low_lip])
# 嘴角：上下唇在嘴角是同一圈點，兩邊跟下巴的比例要在嘴角接起來 —— 下唇從中間 1 降到嘴角 0.5、上唇從中間 0 升到嘴角 0.5，
#   嘴角外的臉頰再從 0.5 漸漸到 0（嘴角完全不動時，嘴角那段嘴唇被拉成兩條往上翹的「角」，口紅看起來劃到嘴角外面）
ax_ = np.abs(X - MC[0])
to_corner = smooth01((ax_ - 0.45 * mw) / (0.55 * mw))  # 0＝中段、1＝AI 嘴角；嘴角外（到嘴唇尖端）上下唇一起動、不張開（到尖端才會合時，新郎的開口裂到嘴角外，露出嘴唇內側）
lip_tip = ax_[IS_LIP & (np.abs(Z - slit_c) < 0.2 * U)].max()  # 嘴唇尖端（模板嘴唇可能比 AI 嘴角再往外一點）
outside = 1 - smooth01((ax_ - lip_tip) / (0.4 * mw))  # 嘴唇尖端往外到臉頰漸漸不動（從固定 1.05 倍嘴寬起算時，新郎的嘴唇尖端留在原地、嘴角外多兩塊粉紅）
print("[arkit] 嘴唇尖端 %.3f（嘴寬一半 %.3f）" % (lip_tip, mw))
lip_band = (IS_LIP | (IS_INNER & (Y < mouth_y + 0.25 * U))) & (ax_ < 1.6 * mw)
skin_band = ~IS_LIP & ~IS_INNER & (np.abs(Z - slit_c) < 0.16 * U) & (ax_ > 0.9 * mw) & (Y < mouth_y + 0.3 * U)
lip_band &= ax_ <= lip_tip + 0.01 * U
CORNER_JAW = 0.85  # 嘴角會合點跟下巴動的比例（0.5 以下時嘴角那段比旁邊的嘴唇高、拉成往上翹的「角」，口紅看起來劃到嘴角外；大笑時嘴角因此往下掉，由修正形態鍵 jawOpen_smile_corr 抬回來）
w_low_lip = (1 - (1 - CORNER_JAW) * to_corner) * outside
w_up_lip = CORNER_JAW * to_corner * outside
w_jaw[lip_band & ~UPPER] = w_low_lip[lip_band & ~UPPER]
w_jaw[lip_band & UPPER & ~(IS_INNER & (Y > mouth_y + 0.1 * U))] = w_up_lip[lip_band & UPPER & ~(IS_INNER & (Y > mouth_y + 0.1 * U))]
# 嘴巴內壁在嘴角附近也照同一套比例（下面的內壁整片跟下巴、上面的不動時，嘴角的內壁被撐開露出一塊）
near_c = IS_INNER & (ax_ > 0.45 * mw) & (Y < mouth_y + 0.45 * U)
in_lo = near_c & ~UPPER
in_up = near_c & UPPER & (Y < mouth_y + 0.3 * U)
w_jaw[in_lo] = np.minimum(w_jaw[in_lo], w_low_lip[in_lo])
w_jaw[in_up] = np.maximum(w_jaw[in_up], w_up_lip[in_up])
sv = 1 - smooth01((np.abs(Z - slit_c) - 0.03 * U) / (0.13 * U))
w_jaw[skin_band] = np.maximum(w_jaw[skin_band], (CORNER_JAW * outside * sv)[skin_band])
PIVOT = np.array([0.0, mouth_y + 0.9 * U, slit_c + 0.12 * U])


def jaw_delta(Pts, w, ang=0.0, shift=(0, 0, 0), yaw=0.0):
    """繞下顎軸（X 軸，過 PIVOT）往下轉 ang、再左右轉 yaw、平移 shift；乘上權重"""
    rel = Pts - PIVOT
    c_, s_ = math.cos(ang), math.sin(ang)
    y1 = rel[:, 1] * c_ - rel[:, 2] * s_
    z1 = rel[:, 1] * s_ + rel[:, 2] * c_
    rot = np.stack([rel[:, 0], y1, z1], 1)
    if yaw:
        cy, sy = math.cos(yaw), math.sin(yaw)
        rot = np.stack([rot[:, 0] * cy - rot[:, 1] * sy, rot[:, 0] * sy + rot[:, 1] * cy, rot[:, 2]], 1)
    return (rot + PIVOT + np.array(shift) * U - Pts) * w[:, None]


JAW_OPEN = math.radians(17)
jaw_variants = {"jawOpen": dict(ang=JAW_OPEN), "jawForward": dict(shift=(0, -0.09, 0)),
                "jawLeft": dict(shift=(0.1, 0, 0), yaw=math.radians(4)), "jawRight": dict(shift=(-0.1, 0, 0), yaw=math.radians(-4))}
for name, kw in jaw_variants.items():
    add(name, "Head", jaw_delta(P, w_jaw, **kw))
    for jp in jaw_parts:
        Wp = world_verts(jp)
        add(name, jp.name, jaw_delta(Wp, np.ones(len(Wp)), **kw))
# 張嘴時嘴角往中間收（真人張大嘴時嘴巴會變窄）：嘴角外那段閉著的嘴唇停在原本寬度時，下唇口紅從開口的角斜斜連到原本的唇尖、
#   看起來劃到嘴角外（驚訝、張嘴都有）
pull_x = smooth01((ax_ - 0.3 * mw) / (0.7 * mw)) * (1 - smooth01((ax_ - lip_tip - 0.3 * mw) / (0.5 * mw)))
pull_z = 1 - smooth01((np.abs(Z - slit_c) - 0.05 * U) / (0.2 * U))
pull = pull_x * pull_z * (Y < mouth_y + 0.3 * U)
D_in = np.zeros((N, 3))
D_in[:, 0] = -(X - MC[0]) * 0.22 * pull
add("jawOpen", "Head", D_in)
# 大笑修正（不是 ARKit 的鍵）：張嘴時上唇在嘴角那段跟著往下，疊上微笑（上唇拉平）後兩端還是往下垂 → 把那段抬回來。
#   控制骨架用 min(張嘴, 微笑) 推它：只張嘴、只微笑都不受影響；表情捕捉直接送 52 個值時不會有這個修正
#   下唇靠近嘴角那段也抬回來（中間不動、越靠嘴角越多），嘴角回到笑線上；只抬上唇時，嘴角被撐成一條垂直的邊、倒三角變梯形
corr_zone = (np.abs(Z - slit_c) < 0.3 * U) & (Y < mouth_y + 0.3 * U)
corr_w = np.where(UPPER, smooth01((ax_ - 0.2 * mw) / (0.3 * mw)), to_corner ** 2) * corr_zone
SH[CORR_KEY] = {}
add(CORR_KEY, "Head", -jaw_delta(P, w_jaw * corr_w, ang=JAW_OPEN))
# mouthClose：和 jawOpen 一起用時嘴唇合上 → 把 jawOpen 對嘴唇（下唇＋口腔內緣）的位移抵掉，上唇稍微往下
lip_zone = (IS_LIP | (IS_INNER & (Y < mouth_y + 0.15 * U))).astype(float)
# 嘴唇下方的皮膚也漸進地抵銷（只抵銷嘴唇時，嘴唇正下方那圈皮膚被拉長；唇色有轉印到那圈，會拉成一大片粉紅、像張大嘴）
low_lip_z = Z[IS_LIP & ~UPPER].min()
below = ~UPPER & ~IS_LIP & ~IS_INNER & (Z < low_lip_z + 0.02 * U)
fall_v = 1 - smooth01((low_lip_z - Z) / (0.35 * U))
fall_h = 1 - smooth01((np.abs(X - MC[0]) - 0.8 * mw) / (0.5 * mw))
lip_zone = np.maximum(lip_zone, below * fall_v * fall_h)
# 上唇在嘴角附近也跟著張嘴動、張嘴還有嘴角往中間收 → 都要抵銷（只抵銷下唇的下巴轉動時，閉嘴控制器的兩邊嘴角擠出缺口）
D = -jaw_delta(P, w_jaw, ang=JAW_OPEN) * lip_zone[:, None]
D -= D_in * lip_zone[:, None]
D += (w_up[:, 0] * IS_LIP)[:, None] * V(dz=-0.03)
add("mouthClose", "Head", D)

# ── 舌頭：口腔底一條扁長的圓，跟著下巴；tongueOut 往前伸出嘴外 ──
tongue = bpy.data.objects.get("Tongue")
if tongue is None:
    bt = world_verts(jaw_parts[0])
    t_c = np.array([0.0, bt[:, 1].max() + 0.12 * U, bt[:, 2].min() + 0.02 * U])
    bmt = bmesh.new()
    bmesh.ops.create_uvsphere(bmt, u_segments=24, v_segments=12, radius=1.0)
    tme = bpy.data.meshes.new("Tongue")
    bmt.to_mesh(tme)
    bmt.free()
    for p in tme.polygons:
        p.use_smooth = True
    mt = bpy.data.materials.get("Tongue") or bpy.data.materials.new("Tongue")
    bsdf = next(n for n in mt.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = (0.78, 0.33, 0.36, 1)
    bsdf.inputs['Roughness'].default_value = 0.45
    tme.materials.append(mt)
    tongue = bpy.data.objects.new("Tongue", tme)
    sc.collection.objects.link(tongue)
    S = np.array([0.42 * mw, 0.30 * U, 0.07 * U])
    for v in tme.vertices:
        v.co = Vector(np.array(v.co) * S + t_c)
TW = world_verts(tongue)
for name, kw in jaw_variants.items():
    add(name, "Tongue", jaw_delta(TW, np.ones(len(TW)), **kw))
front_w = smooth01((TW[:, 1].max() - TW[:, 1]) / (TW[:, 1].max() - TW[:, 1].min()))  # 舌尖動最多
# 吐舌頭的終點用「控制器張嘴 0.45 時」下唇的位置算 —— 舌尖從上下唇之間出來、搭在下唇上，不從下唇正面穿出
#   （原本水平往前伸 0.62U：張嘴時下唇轉下去，開口在舌頭上方，舌頭從下唇正面穿出來，還被拉成細長的錐子）
TONGUE_JAW = 0.45  # 和 face_rig.py 的 CTRL_Tongue 帶動的張嘴量一致
lip_c = np.where(IS_LIP & ~UPPER & (np.abs(X - MC[0]) < 0.25 * mw))[0]
LJ = P[lip_c] + jaw_delta(P[lip_c], w_jaw[lip_c], ang=JAW_OPEN * TONGUE_JAW)
lip_top, lip_front = LJ[:, 2].max(), LJ[:, 1].min()
tip = TW[np.argmin(TW[:, 1])]
tipJ = tip + jaw_delta(tip[None], np.ones(1), ang=JAW_OPEN * TONGUE_JAW)[0]
t_half = 0.07 * U  # 舌頭半厚（上面建舌頭時的 S[2]）
target = np.array([tip[0], lip_front - 0.16 * U, lip_top + 0.6 * t_half])
fw = smooth01(front_w / 0.6)  # 前 4 成整塊一起移（只拉舌尖會變錐子）
D = fw[:, None] * (target - tipJ)
D[:, 0] += (TW[:, 0] - tip[0]) * 0.2 * fw  # 舌尖稍微變寬
add("tongueOut", "Tongue", D)
print("[arkit] 吐舌 下唇頂 z=%.3f 前緣 y=%.3f 舌尖目標 %s" % (lip_top, lip_front, np.round(target, 3)))

# ── 寫進形態鍵 ──
def ensure_basis(ob):
    if ob.data.shape_keys is None:
        ob.shape_key_add(name="Basis", from_mix=False)
    return ob.data.shape_keys.key_blocks


report = {}
objs = {"Head": head, "Eye_L": eyes["L"], "Eye_R": eyes["R"], "Tongue": tongue}
objs.update({f"Lash_{k}": LASH[k] for k in ("L", "R")})
objs.update({jp.name: jp for jp in jaw_parts})
for ob in objs.values():
    ensure_basis(ob)
for k in ARKIT_52:  # Head 一律有完整 52 個（做不到的保持零位移）
    if k not in head.data.shape_keys.key_blocks:
        head.shape_key_add(name=k, from_mix=False)
for name, per_obj in SH.items():
    for oname, D in per_obj.items():
        ob = objs[oname]
        kbs = ensure_basis(ob)
        kb = kbs.get(name) or ob.shape_key_add(name=name, from_mix=False)
        base = np.array([v.co[:] for v in kbs["Basis"].data])
        if isinstance(D, tuple) and D[0] == "rot":  # 眼球：在物件局部座標裡繞局部軸轉
            R = np.array(Matrix.Rotation(D[2], 3, D[1]))
            new = base @ R.T
        else:
            inv = np.array(ob.matrix_world.inverted().to_3x3())
            new = base + D @ inv.T
        kb.data.foreach_set("co", new.astype(np.float32).ravel())
        kb.value = 0.0
        mx = float(np.linalg.norm((new - base) @ np.array(ob.matrix_world.to_3x3()).T, axis=1).max())
        report.setdefault(name, {})[oname] = round(mx / U, 4)
empty = [k for k in ARKIT_52 if not report.get(k)]
json.dump(dict(report=report, empty=empty), open(os.path.join(HERE, "arkit_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "head_arkit.blend"))
print("[arkit] 有變形 %d 個、空白 %d 個 %s" % (52 - len(empty), len(empty), empty))
print("[arkit] 嘴角 L%s R%s 縫 z=%.3f 下顎軸 %s" % (np.round(K["L"], 3), np.round(K["R"], 3), slit_c, np.round(PIVOT, 3)))
