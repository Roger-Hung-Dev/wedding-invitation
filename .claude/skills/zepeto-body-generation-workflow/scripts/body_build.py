# ZEPETO 風基礎身體（4.5 頭身）：骨架（VRoid 骨頭名 J_Bip_*＋前臂扭轉骨 J_Adj_*）＋一整塊身體網格（手腳是固定模板）＋接上可動臉。
# 2026-10-11 身體流程第 3～4 步；2026-10-12 v9 搬進 skill zepeto-body-generation-workflow（頭的尺寸每次量、展 UV）。
# 2026-10-14 v10 整合 ZEPETO 研究（references/zepeto-body-v2.md、limbs.md）：4.5 頭身＋官方身形、頭身接口環、手腳固定模板、
#   前臂扭轉骨、權重清理、表面加密、交接尺寸。黏土風時期的做法（5 頭身直管身形、拼裝手、方塊手、一坨腳）已移除，
#   舊程式封存在 D:/render-work/archive/zepeto-body-clay-route-20261014/。
#
# 用法（背景 Blender，開某人的 head_rig.blend 當底；由工作流呼叫，輸出到暫存資料夾，出廠時才複製到 build/<人>）：
#   blender -b <head_rig.blend> -P body_build.py -- OUT=D:/render-work/zepeto-body/build/<人>.work [SKINSRC=face] [QA=rest,close,motion]
#   只量頭不做身體：加 MEASURE_ONLY=1；量錯時用 CHIN=、NECKCUT=（頭檔座標）覆寫
#
# 身體網格做法（順序與理由見 references/limbs.md 1.1）：軀幹、手臂、腿用 Skin 修改器沿骨架長出圓管（細分 SKINSUB 次）→
#   體素重建融成一整塊 → 平滑 → 展 UV → 掛頭、接口環接脖子（fit_neck_ring）→ 手腳固定模板接到前臂、小腿（fit_tpl_rings）→
#   光影抄光滑網格 → 綁骨架（自動權重 → 模板權重 → 扭轉骨權重 → 手部保留體積）→ 頭身權重 → 權重清理 → 存檔前量交接尺寸。
# 座標：角色面向 −Y、左手 +X、Z 朝上，單位 m。H＝頭高（髮頂到下巴）＝0.30 m。
import bpy, bmesh, math, os, sys, json, time
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree

ML = r"D:\SideProject\wedding-invitation\.claude\skills\blender-motion-library\scripts"
sys.path.insert(0, ML)
import mixamo_retarget as mr
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_template
import foot_template

ARGS = dict(a.split("=", 1) for a in sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else {}
N = float(ARGS.get("N", "4.5"))   # 頭身比（含頭髮）：2026-10-11 使用者選 5；2026-10-14 看 ZEPETO 研究試做後改 4.5（舊值 5＝新郎 v8、新娘 v3）
OUT = ARGS.get("OUT", r"D:\render-work\zepeto-body\build\groom")
QA = ARGS.get("QA", "rest,close,motion").split(",")
VOXEL = float(ARGS.get("VOXEL", "0.003"))    # 體素格子（m）：手腳是固定模板、不進體素，軀幹四肢最細處（前臂、小腿接口、脖子）半徑都 > 25 mm，3 mm 足夠
#   （黏土風時期手指也進體素，要 1.2 mm 才不會把指縫填平）
# 軀幹左右寬度倍率：照 ZEPETO 官方預設身體，腋下軀幹寬＝下巴到腳底的 0.21 → 0.92（2026-10-14 使用者「照 ZEPETO」；黏土風時期 1.10）
BW = float(ARGS.get("BW", "0.92"))
BD = float(ARGS.get("BD", "0.96"))        # 軀幹前後厚度倍率（黏土風時期 1.05）
LW = float(ARGS.get("LW", "1.05"))        # 上臂、大腿粗細倍率
NECKFIT = ARGS.get("NECKFIT", "1") == "1"   # v3 起：脖子粗細貼合頭的脖子（0＝舊做法，新郎 v8／攝影師 v1）；頭有接口環時不用
WRF = float(ARGS.get("WRF", "1.0"))             # 手腕粗細倍率（0.92 時手指自動權重跟著變、關節內側擠壓超標）
RINGGAP = float(ARGS.get("RINGGAP", "0.012"))   # 接口環：身體脖子從環下多少公尺切開、重做過渡帶
RINGK = int(ARGS.get("RINGK", "3"))               # 接口環：過渡帶中間幾圈
RINGEVALTOL = float(ARGS.get("RINGEVALTOL", "0.003"))   # 頭環細分後的位置和原始位置最多差多少（m）才算正常
HEADWELD = ARGS.get("HEADWELD", "1") == "1"     # 把頭縫到身體上（見 weld_head）
SEAMFIX = ARGS.get("SEAMFIX", "1") == "1"       # v3 起：接縫處頭的法線抄身體（見 seam_normals）
SEAMSPAN = float(ARGS.get("SEAMSPAN", "0.6"))     # 法線漸淡的範圍：切口往上到下巴底的幾成
NECKBLEND = ARGS.get("NECKBLEND", "1") == "1"   # v3 起：頭那一小段脖子的顏色漸層到身體膚色（只改身體檔裡的頭材質）
SKINSRC = ARGS.get("SKINSRC", "neck")      # 膚色取色區域：neck（預設）／face（見 skin_material）
# 手、腳都是固定模板（hand_template.py、foot_template.py；手腳研究方案 A，2026-10-14 使用者看過說可以、整合進工作流）
FARING = float(ARGS.get("FARING", "0.60"))      # 手模板接口環在前臂的位置（手肘 0 → 手腕 1）
ARMGAP = float(ARGS.get("ARMGAP", "0.012"))     # 身體前臂從接口環往手肘多少公尺切開、重做過渡帶
ARMK = int(ARGS.get("ARMK", "3"))               # 過渡帶中間幾圈
DECIM = float(ARGS.get("DECIMATE", "1"))         # 減面比例；1＝不減面（2026-10-14：細長三角形 27% → 0.3%，面數約 11 萬，形狀差 < 0.2 cm）
FLRING = float(ARGS.get("FLRING", "0.70"))      # 腳模板接口環在小腿的位置（膝蓋 0 → 腳踝 1）
LEGGAP = float(ARGS.get("LEGGAP", "0.012"))     # 身體小腿從接口環往膝蓋多少公尺切開
LEGK = int(ARGS.get("LEGK", "3"))
FOOTL = float(ARGS.get("FOOTL", "0.17"))        # 腳模板的腳長 ÷ 身高（ZEPETO 官方基本身體量的；2026-10-14 使用者選「照官方約 17%」）
ANKH = float(ARGS.get("ANKH", "0.362"))         # 腳踝關節高度 ÷ 腳長（官方 0.362，約身高 6.2%；2026-10-14 使用者選「一起抬到約 6%」）
LEGC = 0.004                                    # 小腿中心的 y（Skin 腳踝節點往後 4 mm）
SKINSUB = int(ARGS.get("SKINSUB", "4"))           # Skin 修改器後細分幾次（Skin 每節是 4 角方框：2 次＝16 邊形管，表面一條條直紋；4 次＝64 邊形）
TWIST = ARGS.get("TWIST", "1") == "1"            # 前臂扭轉輔助骨（見 add_twist_bones；2026-10-14 起預設開）
HALFJ = ARGS.get("HALFJ", "0") == "1"            # 手肘、膝蓋的半轉輔助骨（見 add_half_bones）；2026-10-14 使用者看比較圖選「維持現狀」（不加），開關留著對照
HALFB = float(ARGS.get("HALFB", "1.0"))          # 半轉骨帶的半寬 ÷ 該處肢體半徑
HANDDEF = ARGS.get("HANDDEF", "dqs")               # 手的變形方式：dqs（現行：一般變形＋手部保留體積）／lbs（只有一般變形）／cs（一般變形＋修正平滑），比較用
JOINTCS = ARGS.get("JOINTCS", "0") == "1"         # 手肘、膝蓋那一段加修正平滑（Corrective Smooth）；同上，使用者選維持現狀（不加）
JCSW = float(ARGS.get("JCSW", "1.6"))             # 修正平滑帶的半寬 ÷ 該處肢體半徑
JCSF = float(ARGS.get("JCSF", "0.5")); JCSN = int(ARGS.get("JCSN", "10"))           # 修正平滑的強度、次數
WEIGHTCLEAN = ARGS.get("WEIGHTCLEAN", "1") == "1"   # 權重清理（見 clean_weights；2026-10-14 起預設開）
MIDBAND = float(ARGS.get("MIDBAND", "0.02"))        # 四肢的點吃到另一側骨頭的權重：離正中線 MIDBAND×0.5 起漸減、×2 清光（胯下、軀幹中線本來就要左右混）
WCMODE = ARGS.get("WCMODE", "limb")                     # limb＝四肢點清另一側（漸減）＋遠骨頭；norm＝只做碎權重、4 根、正規化
SMOOTHNRM = ARGS.get("SMOOTHNRM", "1") == "1"  # 減面後的光影抄減面前的光滑網格（見 smooth_normals；2026-10-14 起預設開）
RAW = r"D:\render-work\mixamo\raw"
os.makedirs(OUT, exist_ok=True)
T0 = time.time()

sc = bpy.context.scene
O = bpy.data.objects
H = 0.30


CHIN_SRC = [None]     # 這次的下巴從哪來（寫進 build.json 的 head.chin_source）


def measure_head():
    """從開著的 head_rig.blend 量出接身體要用的五個數（頭檔座標）。
    v9 前寫死成新郎頭的值；新娘頭（產線做的）脖子轉軸高 24 cm、胸像是另一個物件 Bust，寫死就會接歪。
    → top 髮頂、chin 下巴、pivot 頭骨轉軸（Face_Rig 的 head 骨）、mouth 嘴巴中心（嘴唇材質面的中心）、cut 脖子切口（以下藏掉）"""
    hd = O["Head"]; me = hd.data; mw = hd.matrix_world
    fr = O["Face_Rig"]
    pivot = fr.matrix_world @ fr.data.bones["head"].head_local
    top = max((o.matrix_world @ Vector(c)).z for o in fr.children if o.type == "MESH" and o.name != "Bust" for c in o.bound_box)
    lips = next((i for i, m in enumerate(me.materials) if m and m.name.startswith("ZEPETO_Lips")), None)
    pts = [mw @ me.vertices[v].co for p in me.polygons if p.material_index == lips for v in p.vertices]
    c = sum(pts, Vector()) / len(pts)
    mouth = Vector((c.x, min(p.y for p in pts), c.z))     # 嘴唇最前緣（叉尖要送到這裡）
    # 正中線剖面（|x|<5 cm、只看臉前半）：每 2 cm 一格，記最前面的 y；正中線上點很稀，空格跳過
    BIN = 0.02
    front = {}
    for v in me.vertices:
        w = mw @ v.co
        if abs(w.x) < 0.05 and w.y < 0:
            k_ = round(w.z / BIN)
            front[k_] = min(front.get(k_, 9.0), w.y)
    mk = round(mouth.z / BIN)
    f0 = min(front[k_] for k_ in front if mk - 2 <= k_ <= mk + 1)
    chin = None
    if hd.get("neck_chin_bottom") is not None:
        # 2026-10-14 起（使用者：「修，用頭檔的下巴底」）：頭端把下巴底寫進 Head 屬性 neck_chin_bottom（頭檔座標，和 neck_ring_z 同一套）＝
        #   正中線前緣從下巴「跳回喉嚨」的地方（zmeasure.measure_cut 的第三個回傳值）。放頭的高度、頭的縮放都照它算。
        #   舊規則（下面）碰到又長又直的 V 字下巴會量太高：攝影師 v2 量到 −0.348、下巴底其實 −0.51 → 頭低 3.7 cm、大 11%、接口環落在肩膀上
        chin = float(hd["neck_chin_bottom"]); CHIN_SRC[0] = "head neck_chin_bottom"
    else:
        # 舊頭：嘴巴以下，正中線最前緣往後退 6 cm（頭檔單位）的高度（線性內插；要連兩格都退才算，避開單點雜訊）。量到的是下巴前緣，比下巴底高
        ks = sorted((k_ for k_ in front if k_ < mk), reverse=True)
        for a, b, c2 in zip(ks, ks[1:], ks[2:]):
            ra, rb, rc = front[a] - f0, front[b] - f0, front[c2] - f0
            if ra < 0.06 <= rb and rc >= 0.06:
                chin = (a + (b - a) * (0.06 - ra) / (rb - ra)) * BIN; break
        if chin is None:
            raise SystemExit("量不到下巴：頭模型的正中線剖面和預期不同，請人工檢查（可用 NECKCUT／CHIN 參數覆寫）")
        CHIN_SRC[0] = "rule（前緣往後退 6 cm）"
    if "CHIN" in ARGS:
        chin = float(ARGS["CHIN"]); CHIN_SRC[0] = "CHIN 參數"
    # 切口：下巴底下（下巴往下 6 cm 起算），正中線最前緣不再往後退（相鄰兩格差 < 3.5 cm）的第一格＝下巴底面結束、脖子開始。
    # 太靠近下巴，Mask 切線會切過下巴底面、露出鋸齒（新娘頭測試時發生：原本用「頭高 ×0.084」，新娘頭的下巴底比較長）。
    # 新郎頭量出來 −0.70（和 v8 寫死的值一樣）。不低於頭網格底 +1 cm。
    zmin = min((mw @ Vector(b)).z for b in hd.bound_box)
    below = sorted((k_ for k_ in front if k_ * BIN <= chin - 0.06), reverse=True)
    cut = None
    for a, b in zip(below, below[1:]):
        if front[b] - front[a] < 0.035:
            cut = b * BIN; break
    if cut is None:
        cut = chin - 0.084 * (top - chin)
    cut = max(cut, zmin + 0.01)
    # 切口處頭的脖子截面（頭檔單位）：身體脖子要比它粗才蓋得住切口鋸齒（攝影師頭的脖子比新郎粗 18%，切口一圈露在外面）
    sec = [mw @ v.co for v in me.vertices if abs((mw @ v.co).z - cut) < 0.012]
    neck_rx = max(abs(w.x) for w in sec) if sec else 0.0
    neck_ry = (max(w.y for w in sec) - min(w.y for w in sec)) / 2 if sec else 0.0
    neck_yc = (max(w.y for w in sec) + min(w.y for w in sec)) / 2 if sec else 0.1
    out = dict(top=top, chin=chin, pivot=pivot, mouth=mouth, cut=cut, neck_rx=neck_rx, neck_ry=neck_ry, neck_yc=neck_yc)
    ring = read_neck_ring(hd, cut, neck_yc)
    if ring:
        out.update(ring)
    return out


def ring_dir(i, n=48):
    """接口環第 i 點（0 起算）的水平方向。合約（research-head-body-seam.md 5.4）：第 0 點＝正前方（−Y），
    從上往下看逆時針 −Y → +X（第 12 點）→ +Y（第 24 點）→ −X（第 36 點）"""
    a = 2 * math.pi * i / n
    return Vector((math.sin(a), -math.cos(a), 0.0))


def read_neck_ring(hd, cut, neck_yc):
    """頭和身體的接口環（2026-10-14 使用者選方案 A：兩個物件、接縫點對點重合）。
    頭檔有 neck_ring_ver：讀 Head 的點屬性 neck_ring（1～48）與 neck_ring_z（頭檔座標）。
    沒有、但參數 RINGTEST=1：在舊頭的表面、切口高度用射線取 48 點當假環（只給身體端開發測試，頭不改）。
    回傳 dict(ring_local=[48 個 Head 本地座標], cut=環高度, neck_rx/ry/yc＝環的寬厚中心, ring_src)；都沒有回傳 None"""
    me = hd.data; mw = hd.matrix_world; mi = mw.inverted()
    pts = None; src = None; z = cut
    if "neck_ring_ver" in hd:
        att = me.attributes.get("neck_ring")
        if att is None:
            raise SystemExit("頭檔有 neck_ring_ver 卻沒有點屬性 neck_ring")
        idx = {d.value: i for i, d in enumerate(att.data) if d.value > 0}
        if sorted(idx) != list(range(1, 49)):
            raise SystemExit(f"接口環點數不對：{len(idx)}（要 1～48 各一點）")
        pts = [mw @ me.vertices[idx[k]].co for k in range(1, 49)]
        z = float(hd.get("neck_ring_z", sum(p.z for p in pts) / 48))
        src = f"head v{int(hd['neck_ring_ver'])}"
    elif ARGS.get("RINGTEST") == "1":
        from mathutils.bvhtree import BVHTree as _BVH
        tree = _BVH.FromPolygons([mw @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
        c = Vector((0.0, neck_yc, cut)); pts = []
        for i in range(48):
            hit = tree.ray_cast(c, ring_dir(i), 2.0)
            if hit[0] is None:
                raise SystemExit(f"假環第 {i} 點射不到頭的表面（脖子有洞？）")
            pts.append(hit[0])
        src = "RINGTEST（舊頭表面取樣）"
    if not pts:
        return None
    rx = max(abs(p.x) for p in pts); ys = [p.y for p in pts]
    return dict(ring_local=[mi @ p for p in pts], ring_file=[p.copy() for p in pts], cut=z, neck_rx=rx, neck_ry=(max(ys) - min(ys)) / 2,
                neck_yc=(max(ys) + min(ys)) / 2, ring_src=src)


HM = measure_head()
HEAD_FILE_H = HM["top"] - HM["chin"]
S = H / HEAD_FILE_H
PIVOT_FILE = HM["pivot"]
CHIN_FILE = HM["chin"]
MOUTH_FILE = HM["mouth"]
RING = "ring_local" in HM
print("HEAD", {k_: (tuple(round(x, 4) for x in v) if hasattr(v, "x") else round(v, 4)) for k_, v in HM.items() if k_ not in ("ring_local", "ring_file", "ring_src")}, "RING", HM.get("ring_src"), "CHIN", CHIN_SRC[0])
if "MEASURE_ONLY" in ARGS:
    sys.exit(0)

k = max(0.0, min(1.0, (N - 3.5) / 1.5))
T = N * H; CHIN = T - H; B = (N - 1) * H
P = {}
P["hip_j"] = B * float(ARGS.get("LEGR", "0.615"))   # 髖關節高度 ÷ 下巴到腳底；ZEPETO 官方預設胯下在 0.55 → 髖關節約 0.615
P["hip_x"] = float(ARGS.get("HIPX", "0.066"))            # 兩腿骨頭離中線（v2 前是 0.16H×1.1＝0.053：大腿圓管重疊，體素重建後兩腿黏到離地 0.37 m，服裝 session 回報）
P["hips"] = P["hip_j"] + 0.05 * H
P["ankle"] = 0.075 * H
P["knee"] = P["ankle"] + (P["hip_j"] - P["ankle"]) * 0.5
# 2026-10-14 ZEPETO 腳掌研究（https://claude.ai/artifact/Cuefy2mtUSjs87pzmnpBS8）：官方腳長≈身高 17%、腳踝關節≈腳長 0.362（身高 6.2%，
#   和 Mixamo 標準骨架差不多）；我們原本腳踝骨在身高 1.7%，轉腳踝是繞著腳底轉。膝蓋用舊算法、位置不變（官方膝 25.5%、我們 24.7%）
P["foot_len"] = FOOTL * T
P["ankle"] = ANKH * P["foot_len"]
P["heel_y"] = LEGC + 0.165 * P["foot_len"]          # 官方小腿中心在離腳跟 16.5% 腳長的地方
P["sh_z"] = CHIN - float(ARGS.get("SHDROP", "0.085")) * B   # 肩關節高度（v3 前 0.05B：肩膀跟脖子根一樣高，使用者說「聳肩」→ 降 4 cm）
# 下巴改用頭檔的下巴底（neck_chin_bottom）時，肩膀跟著往上補 SHUP×H：舊規則量到的是下巴前緣、比下巴底高，
#   新娘頭差 0.0306 頭檔單位＝身體 8 mm（0.0267H）。不補的話下巴底放到同一個高度後，接口環→肩線那段脖子會長 8 mm；
#   使用者 2026-10-14 選「身體那段脖子先不動，維持 0.14H」，所以補回去，新娘的脖子長度和改之前一樣
SHUP = float(ARGS.get("SHUP", "0.0267" if str(CHIN_SRC[0]).startswith("head") else "0"))
P["sh_z"] += SHUP * H
P["sh_x"] = 0.40 * H * (1 + 0.08 * k)
P["ua"] = 0.205 * B
P["fa"] = 0.195 * B
P["hand"] = 0.38 * H
P["pivot_z"] = CHIN + (PIVOT_FILE.z - CHIN_FILE) * S
P["neck_z"] = P["sh_z"] + 0.03 * H
HL = P["hand"]
WR_A, WR_B = float(ARGS.get("WRA", "0.014")), float(ARGS.get("WRB", "0.023"))   # 手腕兩軸半徑（Skin 的兩軸：這樣是左右寬、上下扁；反過來手腕會變窄變厚）
THUMB_CURL = float(ARGS.get("THUMBC", "30"))   # 拇指靜止方向：往掌心幾度
THUMB_SIDE = float(ARGS.get("THUMBS", "30"))   # 往拇指側張幾度
SH_BACK = 0.008                           # 肩關節往後（v3 前 0：肩膀在胸口正中，看起來含胸）
NECK_CUT_FILE = float(ARGS["NECKCUT"]) if "NECKCUT" in ARGS else HM["cut"]   # 頭檔座標這個高度以下是往外撐開的胸像底座，藏掉（新郎頭量出來約 −0.70）
NECK_CUT_Z = CHIN + (NECK_CUT_FILE - CHIN_FILE) * S
# 脖子粗細倍率：切口處頭的脖子截面（換成身體公尺）÷ 新郎頭的值（0.0537、0.0458；身體脖子半徑 0.061／0.069 是照新郎頭調的）。
# 只會變粗不會變細（≥1）：新郎頭、新娘頭＝1，攝影師頭≈1.18
NF = max(1.0, HM["neck_rx"] * S / 0.0537, HM["neck_ry"] * S / 0.0458)
# 手指：(名稱, 指根在手掌寬度上的位置（×手長，−＝拇指側）, 長度（×手長）, 休息姿勢往外張的角度°)
FINGERS = (("Index", -0.185, 0.44, 0.0), ("Middle", -0.06, 0.48, 0.0), ("Ring", 0.065, 0.45, 0.0), ("Little", 0.185, 0.36, 0.0))
# v8：靜止姿勢四指併攏平行（和 Mixamo 標準一樣）。v5～v7 張成 −8／0／8／16°，動畫一往靜止姿勢混就變耙子形（導演 session 轉使用者）
FR = 0.0058          # 手指半徑（m）；hand_template 照這個做手指
TR = 0.0078          # 拇指半徑


def bones_layout():
    """→ {骨頭: (頭, 尾, 父)}（rest＝T 字、掌心朝下）"""
    L = {}
    hz, sz = P["hips"], P["sh_z"]
    top = sz - 0.04 * H
    L["J_Bip_C_Hips"] = (Vector((0, 0, hz)), Vector((0, 0, hz + 0.1 * H)), None)
    zs = [hz + (top - hz) * f for f in (0.15, 0.45, 0.75)]
    L["J_Bip_C_Spine"] = (Vector((0, 0, zs[0])), Vector((0, 0, zs[1])), "J_Bip_C_Hips")
    L["J_Bip_C_Chest"] = (Vector((0, 0, zs[1])), Vector((0, 0, zs[2])), "J_Bip_C_Spine")
    L["J_Bip_C_UpperChest"] = (Vector((0, 0, zs[2])), Vector((0, 0, P["neck_z"])), "J_Bip_C_Chest")
    L["J_Bip_C_Neck"] = (Vector((0, 0, P["neck_z"])), Vector((0, 0, P["pivot_z"])), "J_Bip_C_UpperChest")
    L["J_Bip_C_Head"] = (Vector((0, 0, P["pivot_z"])), Vector((0, 0, P["pivot_z"] + 0.5 * H)), "J_Bip_C_Neck")
    for s, sg in (("L", 1), ("R", -1)):
        X = lambda x: Vector((sg * x, 0, 0))
        sh0 = Vector((sg * 0.07 * H, 0, sz))
        a0 = Vector((sg * P["sh_x"], SH_BACK, sz)); a1 = a0 + X(P["ua"]); a2 = a1 + X(P["fa"])   # 肩關節略在胸口中心後面
        L[f"J_Bip_{s}_Shoulder"] = (sh0, a0, "J_Bip_C_UpperChest")
        L[f"J_Bip_{s}_UpperArm"] = (a0, a1, f"J_Bip_{s}_Shoulder")
        L[f"J_Bip_{s}_LowerArm"] = (a1, a2, f"J_Bip_{s}_UpperArm")
        m1 = a2 + Vector((sg * 0.50 * HL, -0.055 * HL, 0))
        L[f"J_Bip_{s}_Hand"] = (a2, m1, f"J_Bip_{s}_LowerArm")
        if TWIST:
            # 前臂扭轉輔助骨：前臂的葉子骨（底下不掛骨頭），頭在前臂 1/3、2/3，方向和前臂一樣（roll 0，自己的 Y 軸＝前臂長軸）。
            #   名字 J_Adj_ 開頭：套動作（mixamo_retarget 只動 MAP 裡的骨頭）、動畫端烘焙（只收 J_Bip_）、bind() 挑手部 DQS 骨頭（看 Hand／Thumb…字串）都不會碰到
            fd = a2 - a1
            for k_, f_ in ((1, 1 / 3), (2, 2 / 3)):
                h_ = a1 + fd * f_
                L[f"J_Adj_{s}_LowerArmTwist{k_}"] = (h_, h_ + fd * 0.25, f"J_Bip_{s}_LowerArm")
        for fn, dy, ln, spread in FINGERS:
            b0 = a2 + Vector((sg * (0.50 - 0.12 * abs(dy)) * HL, dy * HL, 0))
            r = math.radians(spread)
            d = Vector((sg * math.cos(r), math.sin(r), 0))         # 張開：往 ±Y 轉（左右手對稱）
            p = b0; par = f"J_Bip_{s}_Hand"
            for i, f in enumerate((0.42, 0.32, 0.26), 1):
                q = p + d * (ln * HL * f)
                L[f"J_Bip_{s}_{fn}{i}"] = (p.copy(), q, par); par = f"J_Bip_{s}_{fn}{i}"; p = q
        # 拇指：從靠近手腕的手掌側邊長出來，往外張得比較開，虎口才凹得深（v6 前從手掌中段長出、和食指之間一大片膜）
        t0 = a2 + Vector((sg * 0.10 * HL, -0.16 * HL, -0.035 * HL))
        # 拇指方向照 Mixamo 標準骨架的靜止姿勢：往掌心 30°、往拇指側 30°（v6 張到 58°，共用手勢的拇指收不回來：握拳、比讚拇指直直伸出）
        d = Vector((sg * 0.7746, -0.4472, -0.4472))      # v8：直接用 Mixamo 標準骨架的拇指方向（female_idle.fbx 的 rest 量的），出廠檢查要求差 ≤ 3°
        p = t0; par = f"J_Bip_{s}_Hand"
        for i, f in enumerate((0.40, 0.32, 0.28), 1):
            q = p + d * (0.50 * HL * f)
            L[f"J_Bip_{s}_Thumb{i}"] = (p.copy(), q, par); par = f"J_Bip_{s}_Thumb{i}"; p = q
        h0 = Vector((sg * P["hip_x"], 0, P["hip_j"])); kn = Vector((sg * P["hip_x"], -0.01 * H, P["knee"]))
        an = Vector((sg * P["hip_x"], 0.0, P["ankle"]))
        FLn = P["foot_len"]; tip = P["heel_y"] - FLn         # 腳趾關節在離腳尖 31% 腳長、高 7.8% 腳長（官方）
        toe = Vector((sg * P["hip_x"], tip + 0.311 * FLn, 0.078 * FLn)); toe_t = Vector((sg * P["hip_x"], tip + 0.06 * FLn, 0.078 * FLn))
        if HALFJ:
            # 半轉輔助骨：上一節的葉子骨，頭在關節、方向同下一節，約束抄下一節本地轉動的 50%（見 add_half_bones）
            L[f"J_Adj_{s}_ElbowHalf"] = (a1.copy(), a1 + (a2 - a1) * 0.25, f"J_Bip_{s}_UpperArm")
            L[f"J_Adj_{s}_KneeHalf"] = (kn.copy(), kn + (an - kn) * 0.25, f"J_Bip_{s}_UpperLeg")
        L[f"J_Bip_{s}_UpperLeg"] = (h0, kn, "J_Bip_C_Hips")
        L[f"J_Bip_{s}_LowerLeg"] = (kn, an, f"J_Bip_{s}_UpperLeg")
        L[f"J_Bip_{s}_Foot"] = (an, toe, f"J_Bip_{s}_LowerLeg")
        L[f"J_Bip_{s}_ToeBase"] = (toe, toe_t, f"J_Bip_{s}_Foot")
    return L


def build_armature(L):
    ad = bpy.data.armatures.new("Body_Armature"); arm = O.new("Body_Armature", ad); sc.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    for n, (h, t, par) in L.items():
        eb = ad.edit_bones.new(n); eb.head = h; eb.tail = t; eb.roll = 0.0
    for n, (h, t, par) in L.items():
        if par:
            ad.edit_bones[n].parent = ad.edit_bones[par]
    bpy.ops.object.mode_set(mode="OBJECT")
    ad.display_type = "STICK"
    if TWIST:
        add_twist_bones(arm)
    if HALFJ:
        add_half_bones(arm)
    # 共用手勢的拇指壓到手指時離骨頭多遠＝手指半徑＋拇指尖半徑＋0.5 mm（mixamo_retarget.Target 讀這個屬性；沒設是 VRoid 的 12 mm）。
    #   手模板實測 0.0175（2026-10-14；黏土風拼裝手是 0.0155，模板用 0.0155 時比 YA 拇指陷 1.7 mm）
    arm["thumb_contact"] = float(ARGS.get("THC", "0.0175"))
    # 這副身體專用的手勢微調（mixamo_retarget.gesture 會優先用）：共用 thumbs_up 的四指彎太深、指尖壓進掌心 → 四指彎度 ×0.8
    #   （手模板；0.9 時比讚指尖陷 1.3 mm）。不要改共用手勢：會動到 V12 已審過的幕
    tuf = float(ARGS.get("TUF", "0.8"))
    _tu = mr.GESTURE["thumbs_up"]
    arm["gesture_overrides"] = json.dumps({"thumbs_up": {"curl": {f: ([round(a * tuf, 1) for a in v] if f != "Thumb" else list(v))
                                                                   for f, v in _tu["curl"].items()}}}, ensure_ascii=False)
    return arm


# ════════ 身體網格 ════════
def skin_body(L):
    """軀幹＋手臂（到手腕）＋腿（到腳踝）：Skin 修改器的骨架點與半徑。手、腳是固定模板，fit_tpl_rings 從前臂、小腿接上"""
    hj, sz = P["hip_j"], P["sh_z"]
    tl = sz - hj
    V = []; E = []; R = []

    def add(p, rx, ry=None):
        V.append(Vector(p)); R.append((rx, ry if ry is not None else rx)); return len(V) - 1

    def edge(a, b):
        E.append((a, b))
    # 站直的 S 形：臀往後、腰在中間、胸口往前挺（v3 前是直筒，使用者說「駝背」）
    c0 = add((0, 0.014, hj + 0.015), 0.118 * BW, 0.086 * BD)       # 臀
    c1 = add((0, 0.006, hj + 0.40 * tl), 0.100 * BW, 0.074 * BD)    # 腰
    c2 = add((0, -0.012, hj + 0.70 * tl), 0.122 * BW, 0.086 * BD)   # 胸
    c3 = add((0, 0.002, sz - 0.015), 0.110 * BW, 0.068 * BD)        # 肩線（肩關節高度；往上到脖子是斜的）
    if RING:
        # 接口環（2026-10-14）：脖子管只做到環上方 4 mm（之後 fit_neck_ring 從環下 12 mm 切掉、重做過渡帶接到環），不伸進頭裡
        hx, hy = HM["neck_rx"] * S, HM["neck_ry"] * S
        hyc = (HM["neck_yc"] - PIVOT_FILE.y) * S
        nk = 1.19 / (1.013 if SKINSUB >= 4 else 1.0)       # Skin 細分 4 次身體粗約 1.3%，係數跟著縮（2026-10-14）
        c4 = add((0, hyc, NECK_CUT_Z), hx * nk, hy * nk)
        c4b = add((0, hyc, NECK_CUT_Z + 0.03), hx * nk, hy * nk)   # 再往上 3 cm：體素＋平滑會把管口收圓，要讓切口處還是完整的管（這段之後會被切掉）
        c5 = None
    elif NECKFIT:
        # v3（2026-10-12 新娘禮服露肩，使用者說「頭和身體的銜接處沒做好」）：切口處身體脖子和頭的脖子一樣粗、同一個中心，
        # 往下（c3 肩線）才變粗。舊做法固定半徑＋往後偏 1.3 cm，比頭的脖子粗一圈，接口像台階
        hx, hy = HM["neck_rx"] * S, HM["neck_ry"] * S
        hyc = (HM["neck_yc"] - PIVOT_FILE.y) * S
        c4 = add((0, hyc, NECK_CUT_Z - 0.004), hx * float(ARGS.get("NECKOVER", "1.12" if HEADWELD else "1.24")), hy * float(ARGS.get("NECKOVER", "1.12" if HEADWELD else "1.24")))     # 切口處：Skin 半徑 ×1.24（體素重建＋平滑會縮約 11%），成品比頭的脖子大約 2%，剛好蓋住切線
        c4b = add((0, hyc, NECK_CUT_Z + 0.012), hx * 0.90, hy * 0.90)    # 切口以上縮進頭裡
        c5 = add((0, hyc * 0.5, P["pivot_z"] + 0.015), hx * 0.75, hy * 0.75)
    else:
        c4 = add((0, 0.013, NECK_CUT_Z - 0.008), 0.061 * NF, 0.069 * NF)          # 脖子：頭在 NECK_CUT_Z 以下藏掉；切口處身體比頭略粗，把鋸齒邊埋進去
        c4b = add((0, 0.010, NECK_CUT_Z + 0.014), 0.050 * NF, 0.056 * NF)         # 切口以上縮進頭裡
        c5 = add((0, 0.006, P["pivot_z"] + 0.015), 0.044 * NF, 0.046 * NF)
    chain = [(c0, c1), (c1, c2), (c2, c3), (c3, c4)] + ([] if c4b is None else [(c4, c4b)]) + ([] if c5 is None else [(c4b, c5)])   # 肩線直接收到切口（中間多一節會在脖子底擠出一圈台階）
    for a, b in chain:
        edge(a, b)
    for s, sg in (("L", 1), ("R", -1)):
        g = lambda n: L[f"J_Bip_{s}_{n}"]
        a0, a1, a2 = g("UpperArm")[0], g("LowerArm")[0], g("Hand")[0]
        # ZEPETO 的手臂（2026-10-14 使用者選「手腳加形狀」）：從三角肌往手肘漸細、前臂靠手肘那段有肌肉、手腕細
        #   （黏土風時期只有 5 個點、中間直線內插，像一樣粗的管子）
        sh = add(a0 + Vector((-sg * 0.005, 0, -0.008)), 0.046 * LW)            # 三角肌
        u1 = add(a0.lerp(a1, 0.35), 0.040 * LW, 0.038 * LW)
        u2 = add(a0.lerp(a1, 0.75), 0.034, 0.032)                             # 手肘上方收細
        el = add(a1, 0.030, 0.029)
        f1 = add(a1.lerp(a2, 0.25), 0.032, 0.029)                             # 前臂肌肉
        f2 = add(a1.lerp(a2, 0.70), 0.025, 0.021)
        wr = add(a2 - Vector((sg * 0.006, 0, 0)), WR_A * WRF, WR_B * WRF)      # 手腕
        chain_a = (c3, sh, u1, u2, el, f1, f2, wr)
        for a, b in zip(chain_a, chain_a[1:]):
            edge(a, b)
        h0, kn, an, toe = g("UpperLeg")[0], g("LowerLeg")[0], g("Foot")[0], g("ToeBase")[0]
        # ZEPETO 的腿：大腿根最粗、往膝蓋收；膝蓋上方收細、膝蓋微凸；小腿肚在小腿上三分之一、往後鼓；腳踝細
        #   （官方預設身體正面量：大腿根寬 0.10、膝 0.075、腳踝 0.05，單位＝下巴到腳底）
        hp = add(h0 + Vector((sg * 0.010, 0.004, -0.01)), 0.068 * LW, 0.070 * LW)
        t1 = add(h0.lerp(kn, 0.30), 0.058 * LW, 0.060 * LW)                  # 大腿上段
        t2 = add(h0.lerp(kn, 0.65) + Vector((0, -0.003, 0)), 0.048, 0.050)  # 大腿前側略鼓
        t3 = add(h0.lerp(kn, 0.90), 0.040, 0.041)                            # 膝蓋上方收細
        kv = add(kn + Vector((0, -0.003, 0)), 0.040, 0.041)                  # 膝蓋
        s1 = add(kn.lerp(an, 0.30) + Vector((0, 0.009, 0)), 0.039, 0.044)   # 小腿肚（往後鼓）
        s2 = add(kn.lerp(an, 0.65) + Vector((0, 0.004, 0)), 0.031, 0.031)
        av = add(an + Vector((0, 0.004, 0.006)), 0.025, 0.026)               # 腳踝細
        chain_l = (c0, hp, t1, t2, t3, kv, s1, s2, av)
        for a, b in zip(chain_l, chain_l[1:]):
            edge(a, b)
    me = bpy.data.meshes.new("SkinBody"); me.from_pydata([tuple(v) for v in V], E, []); me.update()
    o = O.new("SkinBody", me); sc.collection.objects.link(o)
    mod = o.modifiers.new("Skin", "SKIN"); mod.branch_smoothing = 0.6; mod.use_smooth_shade = True
    sv = me.skin_vertices[0].data
    for i, (rx, ry) in enumerate(R):
        sv[i].radius = (rx, ry)
    sv[c0].use_root = True
    sub = o.modifiers.new("Sub", "SUBSURF"); sub.levels = SKINSUB; sub.render_levels = SKINSUB
    return o


def capsule_bm(bm, p0, p1, r0, r1):
    d = p1 - p0; Lg = d.length
    M = Matrix.Translation((p0 + p1) / 2) @ Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4()
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=r0, radius2=r1, depth=Lg)
    vs = list(g["verts"])
    for r, z in ((r0, -Lg / 2), (r1, Lg / 2)):
        s_ = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=r)
        bmesh.ops.translate(bm, verts=s_["verts"], vec=(0, 0, z)); vs += s_["verts"]
    bmesh.ops.transform(bm, matrix=M, verts=vs)


def ellip_bm(bm, c, semi, rot=None):
    g = bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=1.0)
    M = Matrix.Translation(c) @ (rot or Matrix()) @ Matrix.Diagonal((*semi, 1))
    bmesh.ops.transform(bm, matrix=M, verts=g["verts"])


def apply_all(o):
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True); bpy.context.view_layer.objects.active = o
    for m in list(o.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)


def build_mesh(L):
    body = skin_body(L); apply_all(body)
    body.name = "Body"; body.data.name = "Body"
    rm = body.modifiers.new("Remesh", "REMESH"); rm.mode = "VOXEL"; rm.voxel_size = VOXEL; rm.adaptivity = 0.0
    sm = body.modifiers.new("Smooth", "LAPLACIANSMOOTH"); sm.iterations = 4; sm.lambda_factor = 0.6; sm.use_volume_preserve = True
    apply_all(body)
    n_before = len(body.data.polygons)
    HIRES[:] = [body.data.copy()]                       # 減面前的光滑網格（smooth_normals 抄它的法線）
    dc = body.modifiers.new("Decimate", "DECIMATE"); dc.ratio = DECIM
    apply_all(body)
    for f in body.data.polygons:
        f.use_smooth = True
    make_uv(body)
    return body, n_before


HIRES = []


def smooth_normals(body):
    """減面留下的「面感」（大三角面一塊塊的明暗）：身體每個點的法線改抄減面前那個光滑網格（DataTransfer 自訂法線，套用後就固定在網格上，
    跟著骨架變形一起轉）。形狀一點都不變，只有光影變平滑。手腳模板與過渡帶本來就光滑，不動。
    2026-10-14 手腳換成平滑模板後，身體的面感和模板的平滑在接口形成一條線（使用者先前也看到胸口、肩膀的面感）"""
    if not HIRES:
        return None
    src = O.new("_HiRes", HIRES[0]); sc.collection.objects.link(src); src.matrix_world = body.matrix_world
    atts = [a for a in (body.data.attributes.get(n) for n in ("hand_tpl", "foot_tpl")) if a]
    ids = [v.index for v in body.data.vertices if all(a.data[v.index].value == 0 for a in atts)]
    vg = body.vertex_groups.new(name="_SMOOTH_NRM"); vg.add(ids, 1.0, "REPLACE")
    # 手腳接口的過渡帶：身體那端 100% 抄、往模板那端漸變到 0（只抄身體那段的話，過渡帶頂端會留一條淡線）
    for it in LIMB_ITEMS:
        P, ax = it["P"], it["axis"]
        for v in body.data.vertices:
            if any(a.data[v.index].value == 2 for a in atts) and (v.co - P).length < 0.12:
                t = min(1.0, max(0.0, ((v.co - P).dot(ax) + it["gap"]) / it["gap"]))     # 0＝切口、1＝模板環
                if 1 - t > 1e-3:
                    vg.add([v.index], 1 - t, "REPLACE")
    dt = body.modifiers.new("SmoothNrm", "DATA_TRANSFER")
    dt.object = src; dt.use_loop_data = True; dt.data_types_loops = {"CUSTOM_NORMAL"}
    dt.loop_mapping = "POLYINTERP_NEAREST"; dt.vertex_group = vg.name; dt.mix_factor = 1.0
    bpy.ops.object.select_all(action="DESELECT"); body.select_set(True); bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier=dt.name)
    g = body.vertex_groups.get("_SMOOTH_NRM")                # 套用修改器後舊的參照會失效，要重新用名字找
    if g:
        body.vertex_groups.remove(g)
    me = src.data; O.remove(src, do_unlink=True); bpy.data.meshes.remove(me); HIRES.clear()
    return len(ids)


def make_uv(body):
    """v9：展 UV（體素重建後原本沒有 UV，衣服只能純色）。Smart UV Project：每塊島的比例一致（布紋粗細全身一樣），
    島的方向不保證一致——服裝要做有方向的布紋（人字紋、條紋）時，在衣服自己的網格上重新對齊方向。"""
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True); bpy.context.view_layer.objects.active = body
    if not body.data.uv_layers:
        body.data.uv_layers.new(name="UVMap")
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.003, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")


def crotch_z(body):
    """胯下高度：正中線（|x|<1 cm）上最低的點。兩腿黏住的話這個值會掉到很低"""
    zs = [v.co.z for v in body.data.vertices if abs(v.co.x) < 0.01 and v.co.z < P["hip_j"] + 0.1]
    return min(zs) if zs else None


def skin_material():
    """複製頭的皮膚材質（透光、粗糙度照頭），貼圖換成頭的平均膚色（取色區域見 SKINSRC）"""
    head = O["Head"]
    src = next(m for m in head.data.materials if m and m.name.startswith("ZEPETO_Skin"))
    me = head.data; uvl = me.uv_layers.active
    img = next(n.image for n in src.node_tree.nodes if n.type == "TEX_IMAGE" and n.image)
    W, Hh = img.size; px = img.pixels[:]
    cols = []
    skin_i = next(i for i, m in enumerate(me.materials) if m is src)
    # 取色區域（參數 SKINSRC）：neck＝切口以下的脖子（預設；新郎 v8 用這個）；
    # face＝臉的下半部（下巴到嘴之間、正面、避開耳朵與嘴唇）——新娘頭的脖子貼圖比臉深，使用者 2026-10-12 要「白一點、貼近臉的顏色」
    if SKINSRC == "face":
        zlo = CHIN_FILE + 0.25 * (MOUTH_FILE.z - CHIN_FILE); zhi = MOUTH_FILE.z
        pick = lambda co, p: p.material_index == skin_i and zlo < co.z < zhi and co.y < PIVOT_FILE.y - 0.25 and abs(co.x) < 0.35
    else:
        pick = lambda co, p: co.z < NECK_CUT_FILE
    for p in me.polygons:
        for li in p.loop_indices:
            if pick(me.vertices[me.loops[li].vertex_index].co, p):
                u, w = uvl.data[li].uv
                x = int((u % 1) * (W - 1)); y = int((w % 1) * (Hh - 1)); i = (y * W + x) * 4
                cols.append(px[i:i + 3])
    srgb = [sum(c[j] for c in cols) / len(cols) for j in range(3)]
    lin = [((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92 for c in srgb]
    global SKIN_LIN
    SKIN_LIN = lin
    m = src.copy(); m.name = "ZEPETO_Skin_Body"
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    for n in [n for n in nt.nodes if n.type == "TEX_IMAGE"]:
        nt.nodes.remove(n)
    bsdf.inputs["Base Color"].default_value = (*lin, 1)
    return m, srgb


def blend_head_neck(lin):
    """頭模型自己的那一小段脖子（下巴底到切口）顏色漸層到身體膚色：切口處＝身體色、往上到下巴底＝頭原本的貼圖。
    只改這個 body.blend 裡的頭材質（頭檔不動）。用物件座標 Z（＝頭檔座標）"""
    hd = O["Head"]
    m = next(m for m in hd.data.materials if m and m.name.startswith("ZEPETO_Skin"))
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    base = bsdf.inputs["Base Color"]
    if not base.links:
        return False
    src = base.links[0].from_socket
    tc = nt.nodes.new("ShaderNodeTexCoord"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    mr_ = nt.nodes.new("ShaderNodeMapRange"); mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"; mix.blend_type = "MIX"
    nt.links.new(tc.outputs["Object"], sp.inputs[0]); nt.links.new(sp.outputs["Z"], mr_.inputs["Value"])
    top_z = CHIN_FILE - 0.25 * (CHIN_FILE - NECK_CUT_FILE)            # 下巴底往下四分之一以上保持頭原本的顏色
    mr_.inputs["From Min"].default_value = NECK_CUT_FILE; mr_.inputs["From Max"].default_value = top_z
    mr_.inputs["To Min"].default_value = 1.0; mr_.inputs["To Max"].default_value = 0.0
    nt.links.new(mr_.outputs["Result"], mix.inputs["Factor"])
    nt.links.new(src, mix.inputs["A"]); mix.inputs["B"].default_value = (*lin, 1)
    nt.links.new(mix.outputs["Result"], base)
    return True


def seam_normals(body):
    """接縫的光影：頭的脖子靠近切口那一段，法線改抄身體表面（DataTransfer 自訂法線，切口處 100%、往上漸淡），
    兩塊網格在接口的明暗就連起來，不會出現一圈細線。2026-10-12 使用者圈出新娘 v3 脖子接口還有一圈線。只改 body.blend 裡的頭副本"""
    hd = O["Head"]
    vg = hd.vertex_groups.new(name="SEAM_NRM")
    span = (CHIN_FILE - NECK_CUT_FILE) * SEAMSPAN
    for v in hd.data.vertices:
        w = 1.0 - (v.co.z - NECK_CUT_FILE) / span
        if v.co.z >= NECK_CUT_FILE - 0.01 and w > 0:
            vg.add([v.index], min(1.0, w), "REPLACE")
    dt = hd.modifiers.new("SeamNormals", "DATA_TRANSFER")
    dt.object = body; dt.use_loop_data = True; dt.data_types_loops = {"CUSTOM_NORMAL"}
    dt.loop_mapping = "POLYINTERP_NEAREST"; dt.vertex_group = "SEAM_NRM"; dt.mix_factor = 1.0
    return True


def fit_neck_ring(body):
    """身體脖子頂端接到頭的接口環（方案 A）：環下 RINGGAP 切掉上半截 → 切口（點數不固定）拉鍊式三角形接到 48 點 →
    往上 RINGK 圈過渡，形狀用三次 Hermite（底端沿身體表面斜率、頂端沿頭表面斜率），最上面那圈的座標＝頭環的世界座標。
    身體最上面那圈標點屬性 neck_ring＝1～48（和頭同一個順序）。在 attach_head 之後、bind 之前呼叫"""
    from mathutils.bvhtree import BVHTree as _BVH
    bpy.context.view_layer.update()                          # attach_head 剛設好 Face_Rig 的位置，Head 的 matrix_world 要更新後才對
    hd = O["Head"]; hmw = hd.matrix_world
    top = head_ring_world(hd)
    chk = [(p - PIVOT_FILE) * S + Vector((0, 0, P["pivot_z"])) for p in HM["ring_file"]]   # 和 attach_head 一樣的換算，兩種算法要一致
    dev = max((a - b).length for a, b in zip(top, chk))
    if dev > RINGEVALTOL:
        raise SystemExit(f"接口環座標換算不一致：差 {dev * 1000:.2f} mm（Head 掛在 Face_Rig 底下有額外變換？）")
    zr = sum(p.z for p in top) / len(top)
    zc = zr - RINGGAP
    cen = sum(top, Vector()) / len(top); cen.z = 0
    reach = max((Vector((p.x, p.y, 0)) - cen).length for p in top) * 2.2
    bm = bmesh.new(); bm.from_mesh(body.data)
    lay = bm.verts.layers.int.get("neck_ring") or bm.verts.layers.int.new("neck_ring")   # 先建：之後再加圖層會讓手上的點參照全部失效
    near = lambda v: (Vector((v.co.x, v.co.y, 0)) - cen).length < reach
    n_above0 = sum(1 for v in bm.verts if v.co.z > zc and near(v))
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, zc), plane_no=(0, 0, 1))
    print("RINGDBG bisect: above", n_above0, "cut verts", sum(1 for e in res["geom_cut"] if isinstance(e, bmesh.types.BMVert)), "reach", round(reach, 3), "cen", tuple(round(c, 3) for c in cen))
    kill = [f for f in bm.faces if all(v.co.z > zc - 1e-6 and near(v) for v in f.verts) and any(v.co.z > zc + 1e-6 for v in f.verts)]
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    ang = lambda co: math.atan2(co.x - cen.x, -(co.y - cen.y)) % (2 * math.pi)
    bnd = [v for v in bm.verts if abs(v.co.z - zc) < 1e-5 and near(v) and any(e.is_boundary for e in v.link_edges)]
    bnd.sort(key=lambda v: ang(v.co))
    if len(bnd) < 12:
        zs = [v.co.z for v in bm.verts if near(v)]
        print("RINGDBG zr", round(zr, 4), "zc", round(zc, 4), "body top near neck", round(max(zs), 4) if zs else None,
              "ring", [tuple(round(c, 3) for c in p) for p in top[::6]])
        raise SystemExit(f"脖子切口只找到 {len(bnd)} 個邊界點")
    # 身體表面（切掉前的）與頭表面，用來估兩端的斜率
    def tree_of(o):
        dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); m = e.to_mesh()
        t = _BVH.FromPolygons([o.matrix_world @ v.co for v in m.vertices], [tuple(p.vertices) for p in m.polygons]); e.to_mesh_clear(); return t
    btree = tree_of(body); htree = tree_of(hd)
    def surf(tree, z, d, fallback):
        h = tree.ray_cast(Vector((cen.x, cen.y, z)), d, 1.0)
        return h[0] if h[0] is not None else fallback
    # 切口邊界在第 i 個角度的位置（沿多邊形內插）
    def boundary_at(a):
        n = len(bnd)
        for j in range(n):
            a0, a1 = ang(bnd[j].co), ang(bnd[(j + 1) % n].co)
            span = (a1 - a0) % (2 * math.pi)
            if span == 0:
                continue
            t = ((a - a0) % (2 * math.pi)) / span
            if t <= 1.0:
                return bnd[j].co.lerp(bnd[(j + 1) % n].co, t)
        return bnd[0].co.copy()
    N = len(top); K = RINGK
    rings = []
    for i in range(N):
        d = ring_dir(i)
        b0 = boundary_at(2 * math.pi * i / N); h0 = top[i]
        bl = surf(btree, zc - 0.008, d, b0 - Vector((0, 0, 0.008)))          # 身體表面再往下 8 mm
        hu = surf(htree, zr + 0.008, d, h0 + Vector((0, 0, 0.008)))          # 頭表面再往上 8 mm
        L_ = (h0 - b0).length
        tb = (b0 - bl).normalized() * L_; th = (hu - h0).normalized() * L_
        col = []
        for k in range(1, K + 2):
            t = k / (K + 1)
            h00, h10, h01, h11 = 2*t**3 - 3*t**2 + 1, t**3 - 2*t**2 + t, -2*t**3 + 3*t**2, t**3 - t**2
            col.append(h0.copy() if k == K + 1 else b0 * h00 + tb * h10 + h0 * h01 + th * h11)
        rings.append(col)
    rv = [[bm.verts.new(rings[i][k]) for i in range(N)] for k in range(K + 1)]
    for i, v in enumerate(rv[-1]):
        v[lay] = i + 1
    # 拉鍊：切口邊界（n 點）↔ 第一圈（N 點），照角度合併成三角形
    n = len(bnd); ia = ib = 0; tri = []
    A = [(ang(v.co), v) for v in bnd]; Bv = [(2 * math.pi * i / N, rv[0][i]) for i in range(N)]
    while ia < n or ib < N:
        a_next = A[(ia + 1) % n][0] + (2 * math.pi if ia + 1 >= n else 0) if ia < n else 1e9
        b_next = Bv[(ib + 1) % N][0] + (2 * math.pi if ib + 1 >= N else 0) if ib < N else 1e9
        if a_next <= b_next:
            tri.append((A[ia % n][1], A[(ia + 1) % n][1], Bv[ib % N][1])); ia += 1
        else:
            tri.append((A[ia % n][1], Bv[(ib + 1) % N][1], Bv[ib % N][1])); ib += 1
    for t_ in tri:
        if len(set(t_)) == 3:
            try:
                bm.faces.new(t_)
            except ValueError:
                pass
    for k in range(K):
        for i in range(N):
            j = (i + 1) % N
            bm.faces.new((rv[k][i], rv[k][j], rv[k + 1][j], rv[k + 1][i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(body.data); bm.free(); body.data.update()
    for f in body.data.polygons:
        f.use_smooth = True
    make_uv(body)
    return dict(boundary_n=n, ring_n=N, rings=K + 1, gap_mm=round(RINGGAP * 1000, 1))


def head_ring_world(hd):
    """頭環 48 點的世界座標。真的接口環（頭檔有 neck_ring 屬性）：取 Head **算完修改器之後**的位置——
    Head 有 Mask（藏胸像）＋Subdivision，細分會把開口邊緣的點挪一點，身體要對齊的是看得到的那圈。
    Mask 會把點的編號壓緊，但細分輸出裡「原本的點」排在最前面、屬性值照舊，所以照 neck_ring 屬性找、只看前 M 個點。
    RINGTEST 假環（頭沒有那些點）：直接用取樣位置"""
    if "neck_ring_ver" not in hd:
        return [hd.matrix_world @ p for p in HM["ring_local"]]
    M = sum(1 for v in hd.data.vertices if v.co.z >= NECK_CUT_FILE - 1e-5)
    dg = bpy.context.evaluated_depsgraph_get(); ev = hd.evaluated_get(dg); m = ev.to_mesh()
    att = m.attributes.get("neck_ring")
    pos = {}
    for i in range(min(M, len(m.vertices))):
        k = att.data[i].value if att else 0
        if k > 0 and k not in pos:
            pos[k] = hd.matrix_world @ m.vertices[i].co
    ev.to_mesh_clear()
    if sorted(pos) != list(range(1, 49)):
        raise SystemExit(f"細分後找不到完整的頭環（{len(pos)} 點）：修改器順序或屬性有變？")
    return [pos[k] for k in range(1, 49)]


def ring_report(body):
    """接口環驗收：身體最上面那圈和頭環逐點的距離、身體那圈頭骨權重"""
    bpy.context.view_layer.update()
    hd = O["Head"]; top = head_ring_world(hd)
    att = body.data.attributes.get("neck_ring")
    idx = {d.value: i for i, d in enumerate(att.data) if d.value > 0}
    gaps = [((body.matrix_world @ body.data.vertices[idx[k + 1]].co) - top[k]).length for k in range(len(top))]
    hg = body.vertex_groups.get("J_Bip_C_Head")
    ws = [next((g.weight for g in body.data.vertices[idx[k + 1]].groups if hg and g.group == hg.index), 0.0) for k in range(len(top))]
    return dict(ring_n=len(idx), ring_gap_max_mm=round(max(gaps) * 1000, 3), ring_weight_head_min=round(min(ws), 3), ring_src=HM.get("ring_src"))


def weld_head(body):
    """把頭縫到身體上（2026-10-13 使用者：「身體和頭始終無法完美接合」→ 業界做法：接口的點位置、法線一致）。
    不合併成同一個物件（頭有 54 個表情形態鍵＋臉部骨架驅動器，合併會斷），改成：
      ① 頭的切口邊緣那圈點（和被藏掉的點相連的那圈）貼到身體脖子表面上，往上第二圈貼一半，所有表情形態鍵一起平移；
      ② 身體脖子在切口附近 100% 跟頭骨走（和頭一起剛體轉），往下 2.3 cm 漸變回自動權重，轉頭時接口不會裂開；
      ③ 頭靠近切口那段的法線抄身體（seam_normals）。
    身體脖子在切口處比頭略細（NECKOVER 1.12），頭的邊緣是往內貼到身體上，而不是身體從頭裡穿出來"""
    from mathutils.bvhtree import BVHTree as _BVH
    hd = O["Head"]; me = hd.data
    dg = bpy.context.evaluated_depsgraph_get()
    eb = body.evaluated_get(dg); bme = eb.to_mesh()
    tree = _BVH.FromPolygons([body.matrix_world @ v.co for v in bme.vertices], [tuple(p.vertices) for p in bme.polygons])
    eb.to_mesh_clear()
    keep = [v.co.z >= NECK_CUT_FILE for v in me.vertices]
    nb = [[] for _ in me.vertices]
    for e in me.edges:
        a, b = e.vertices; nb[a].append(b); nb[b].append(a)
    ring1 = [i for i in range(len(me.vertices)) if keep[i] and any(not keep[j] for j in nb[i])]
    r1 = set(ring1)
    ring2 = [i for i in {j for i in ring1 for j in nb[i]} if keep[i] and i not in r1]
    r2 = set(ring2)
    ring3 = [i for i in {j for i in ring2 for j in nb[i]} if keep[i] and i not in r1 and i not in r2]
    mw = hd.matrix_world; mi = mw.inverted()
    delta = {}
    for idxs, f in (() if RING else ((ring1, 1.0), (ring2, 0.6), (ring3, 0.25))):   # 有接口環：頭不動（身體已經接到環上）         # 往上三圈漸淡，接口不會折出一道棱
        for i in idxs:
            w = mw @ me.vertices[i].co
            hit = tree.find_nearest(w)
            if hit[0] is not None and hit[3] < 0.03:
                delta[i] = (mi @ hit[0] - me.vertices[i].co) * f
    keys = me.shape_keys.key_blocks if me.shape_keys else []
    for i, d in delta.items():
        me.vertices[i].co += d
        for kb in keys:
            kb.data[i].co += d
    me.update()
    # 身體權重：切口往下 1.2 cm 以上 100% 頭骨，往下到 3.5 cm 漸變
    gi = {g.name: g.index for g in body.vertex_groups}
    hg = body.vertex_groups["J_Bip_C_Head"] if "J_Bip_C_Head" in gi else body.vertex_groups.new(name="J_Bip_C_Head")
    hi = hg.index; z1, z0 = NECK_CUT_Z - 0.012, NECK_CUT_Z - 0.035
    n_rw = 0
    for v in body.data.vertices:
        if v.co.z < z0:
            continue
        t = 1.0 if v.co.z >= z1 else (v.co.z - z0) / (z1 - z0)
        for g in v.groups:
            if g.group != hi and body.vertex_groups[g.group].name.startswith("J_Bip"):
                body.vertex_groups[g.group].add([v.index], g.weight * (1 - t), "REPLACE")
        cur = next((g.weight for g in v.groups if g.group == hi), 0.0)
        hg.add([v.index], cur * (1 - t) + t, "REPLACE"); n_rw += 1
    return dict(ring1=len(ring1), ring2=len(ring2), ring3=len(ring3), snapped=len(delta), ring1_snapped=sum(1 for i in ring1 if i in delta), max_gap_mm=round(max((d.length * S * 1000 for d in delta.values()), default=0), 2), body_reweighted=n_rw)


LIMB_ITEMS = []      # fit_tpl_rings 記下每個接口（tpl_weights 要用切口位置）


def fit_tpl_rings(body):
    """手、腳的固定模板接到身體（方案 A，做法同脖子接口環）：模板（hand_template／foot_template，同一副骨架永遠一樣）→
    身體在接口環往身體那側 GAP 處切開、刪掉模板那一側 → 切口（點數不固定）拉鍊三角形接到過渡帶第一圈 →
    K 圈 Hermite 過渡（兩端斜率沿身體、模板表面）→ 最後一圈直接接模板的 64 點開口。
    點屬性 hand_tpl／foot_tpl：1＝模板、2＝過渡帶（綁骨架後 tpl_weights 依這個改權重）。在 fit_neck_ring 之後、bind 之前呼叫"""
    from mathutils.bvhtree import BVHTree as _BVH
    items = []
    opt = {k[4:]: float(v) for k, v in ARGS.items() if k.startswith("TPL_")}      # 模板參數覆寫（試做用），例：TPL_TW1=0.6
    if SKINSUB >= 4:                                  # 接口半徑係數是照「Skin 細分 2 次＋體素＋平滑」量的；細分 4 次身體粗約 1.3%（2026-10-14 實測）
        opt.setdefault("SHR", 0.906 * 1.013)
    for s, sg in (("L", 1), ("R", -1)):
        a1, a2 = L[f"J_Bip_{s}_LowerArm"][0], L[f"J_Bip_{s}_Hand"][0]
        items.append(dict(s=s, kind="hand", bone=f"J_Bip_{s}_LowerArm", gap=ARMGAP, K=ARMK, near=0.08,
                          P=Vector((a1.x + (a2.x - a1.x) * FARING, a2.y, a2.z)), axis=Vector((sg, 0, 0)),
                          e1=Vector((0, -1, 0)), e2=Vector((0, 0, 1)),
                          obj=hand_template.build(L, s, sg, HL, FR, TR, fa_ring=FARING, opt=opt)))
    opt = {k[5:]: float(v) for k, v in ARGS.items() if k.startswith("FTPL_")}     # 腳模板參數覆寫，例：FTPL_ARCH=0.03
    if SKINSUB >= 4:
        opt.setdefault("SHR_X", 0.92 * 1.013); opt.setdefault("SHR_Y", 0.91 * 1.013)
    for s, sg in (("L", 1), ("R", -1)):
        kn, an = L[f"J_Bip_{s}_LowerLeg"][0], L[f"J_Bip_{s}_Foot"][0]
        items.append(dict(s=s, kind="foot", bone=f"J_Bip_{s}_LowerLeg", gap=LEGGAP, K=LEGK, near=0.07,
                          P=Vector((an.x, LEGC, kn.z + (an.z - kn.z) * FLRING)), axis=Vector((0, 0, -1)),
                          e1=Vector((sg, 0, 0)), e2=Vector((0, 1, 0)),
                          obj=foot_template.build(L, s, sg, fl_ring=FLRING, foot_len=globals()["P"]["foot_len"], heel_y=globals()["P"]["heel_y"], legc=LEGC, opt=opt)))

    def tree_of(o):
        me = o.data
        return _BVH.FromPolygons([o.matrix_world @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    btree = tree_of(body)
    for it in items:
        it["tree"] = tree_of(it["obj"])
    bm = bmesh.new(); bm.from_mesh(body.data)
    for it in items:
        P, ax = it["P"], it["axis"]; pc = P - ax * it["gap"]
        rad = lambda co: ((co - P) - ax * (co - P).dot(ax)).length
        dd = lambda co: (co - pc).dot(ax)
        # 只切這隻手／腳附近：腳的切面是水平的，切全身會連另一隻腳一起切，另一隻再切一次就多出一圈重複的切口點（2026-10-14 右腳接縫一圈虛線）
        loc = lambda co: rad(co) < it["near"] and abs(dd(co)) < 0.05      # near 不能放大：兩腿中心只差 13 cm，1.5 倍會切到另一條腿內側
        gv = [v for v in bm.verts if loc(v.co)]; gvs = set(gv)
        bmesh.ops.bisect_plane(bm, geom=gv + [e for e in bm.edges if all(v in gvs for v in e.verts)]
                               + [f for f in bm.faces if all(v in gvs for v in f.verts)], plane_co=pc, plane_no=ax)
        kill = [f for f in bm.faces if all(dd(v.co) > -1e-6 and rad(v.co) < it["near"] for v in f.verts) and any(dd(v.co) > 1e-6 for v in f.verts)]
        bmesh.ops.delete(bm, geom=kill, context="FACES")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(body.data); bm.free(); body.data.update()
    # 模板併進身體（點群組 TPL_*、點屬性 *_ring／*_tpl 跟著過來）
    bpy.ops.object.select_all(action="DESELECT")
    for it in items:
        it["obj"].select_set(True)
    body.select_set(True); bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    # 模板沒有材質：併進來會多一個空的材質欄位、模板的面都指到它（渲染變白，2026-10-14 實測）→ 全部指回膚色、刪掉空欄位
    for p in body.data.polygons:
        p.material_index = 0
    while len(body.data.materials) > 1:
        body.data.materials.pop(index=len(body.data.materials) - 1)
    bm = bmesh.new(); bm.from_mesh(body.data)
    out = {}
    for it in items:
        lr = bm.verts.layers.int.get(f"{it['kind']}_ring"); lt = bm.verts.layers.int.get(f"{it['kind']}_tpl")
        lts = [bm.verts.layers.int.get(n) for n in ("hand_tpl", "foot_tpl") if bm.verts.layers.int.get(n)]
        P, ax, e1, e2 = it["P"], it["axis"], it["e1"], it["e2"]; pc = P - ax * it["gap"]
        ang = lambda co: math.atan2((co - P).dot(e2), (co - P).dot(e1)) % (2 * math.pi)
        rad = lambda co: ((co - P) - ax * (co - P).dot(ax)).length
        bnd = [v for v in bm.verts if abs((v.co - pc).dot(ax)) < 1e-5 and rad(v.co) < it["near"] and all(v[l] == 0 for l in lts)
               and any(e.is_boundary for e in v.link_edges)]
        bnd.sort(key=lambda v: ang(v.co))
        ring = sorted([v for v in bm.verts if v[lr] > 0 and (v.co - P).length < 0.1], key=lambda v: ang(v.co))
        if len(bnd) < 12 or len(ring) < 12:
            raise SystemExit(f"模板接口：{it['kind']} {it['s']} 切口 {len(bnd)} 點、模板環 {len(ring)} 點")
        Ar = [ang(v.co) for v in ring]

        def boundary_at(a):
            n = len(bnd)
            for j in range(n):
                a0, a1_ = ang(bnd[j].co), ang(bnd[(j + 1) % n].co)
                span = (a1_ - a0) % (2 * math.pi)
                if span == 0:
                    continue
                t = ((a - a0) % (2 * math.pi)) / span
                if t <= 1.0:
                    return bnd[j].co.lerp(bnd[(j + 1) % n].co, t)
            return bnd[0].co.copy()
        N = len(ring); K = it["K"]
        cols = []
        for i, v in enumerate(ring):
            h0 = v.co.copy(); d = ((h0 - P) - ax * (h0 - P).dot(ax)).normalized()
            b0 = boundary_at(Ar[i])
            hb = btree.ray_cast(P - ax * (it["gap"] + 0.008), d, 0.1)
            bl = hb[0] if hb[0] is not None else b0 - ax * 0.008
            ht = it["tree"].ray_cast(P + ax * 0.008, d, 0.1)
            hu = ht[0] if ht[0] is not None else h0 + ax * 0.008
            L_ = (h0 - b0).length
            tb = (b0 - bl).normalized() * L_; th = (hu - h0).normalized() * L_
            col = []
            for k in range(1, K + 1):
                t = k / (K + 1)
                h00, h10, h01, h11 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t, -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
                col.append(b0 * h00 + tb * h10 + h0 * h01 + th * h11)
            cols.append(col)
        rv = [[bm.verts.new(cols[i][k]) for i in range(N)] for k in range(K)]
        for row in rv:
            for v in row:
                v[lt] = 2
        rv.append(ring)
        n = len(bnd); ia = ib = 0
        A = [(ang(v.co), v) for v in bnd]; Bv = [(Ar[i], rv[0][i]) for i in range(N)]
        tri = []
        while ia < n or ib < N:
            a_next = A[(ia + 1) % n][0] + (2 * math.pi if ia + 1 >= n else 0) if ia < n else 1e9
            b_next = Bv[(ib + 1) % N][0] + (2 * math.pi if ib + 1 >= N else 0) if ib < N else 1e9
            if a_next <= b_next:
                tri.append((A[ia % n][1], A[(ia + 1) % n][1], Bv[ib % N][1])); ia += 1
            else:
                tri.append((A[ia % n][1], Bv[(ib + 1) % N][1], Bv[ib % N][1])); ib += 1
        for t_ in tri:
            if len(set(t_)) == 3:
                try:
                    bm.faces.new(t_)
                except ValueError:
                    pass
        for k in range(K):
            for i in range(N):
                j = (i + 1) % N
                bm.faces.new((rv[k][i], rv[k][j], rv[k + 1][j], rv[k + 1][i]))
        out[f"{it['kind']}_{it['s']}"] = dict(boundary_n=n, ring_n=N, rings=K, gap_mm=round(it["gap"] * 1000, 1),
                                              ring_at=[round(c, 4) for c in P])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(body.data); bm.free(); body.data.update()
    for f in body.data.polygons:
        f.use_smooth = True
    make_uv(body)
    for kind in ("hand", "foot"):
        a = body.data.attributes.get(f"{kind}_tpl")
        if a:
            out[f"{kind}_tpl_verts"] = sum(1 for d in a.data if d.value == 1)
    LIMB_ITEMS[:] = [{k: v for k, v in it.items() if k not in ("obj", "tree")} for it in items]
    return out


def tpl_weights(body):
    """綁完自動權重後：模板的點改用籠子內插的權重（TPL_* 點群組）；過渡帶 100% 前臂／小腿；
    身體切口往身體那側 1 cm 內 100% 前臂／小腿、到 2.5 cm 漸變回自動權重（接縫兩側不受手腳骨頭影響，研究 J3）"""
    me = body.data
    names = {g.index: g.name for g in body.vertex_groups}
    tv, trv = [], {}
    tpl_att = [me.attributes.get(n) for n in ("hand_tpl", "foot_tpl") if me.attributes.get(n)]
    for kind in ("hand", "foot"):
        its = [it for it in LIMB_ITEMS if it["kind"] == kind]
        att = me.attributes.get(f"{kind}_tpl")
        if not its or att is None:
            continue
        for i, d in enumerate(att.data):
            if d.value == 1:
                tv.append(i)
            elif d.value == 2:                                 # 過渡帶：屬於最近的那個接口（左右分開）
                trv[i] = min(its, key=lambda it: (me.vertices[i].co - it["P"]).length)["bone"]
    saved = {i: [(names[g.group][4:], g.weight) for g in me.vertices[i].groups if names[g.group].startswith("TPL_")] for i in tv}
    for g in [g for g in body.vertex_groups if g.name.startswith("J_Bip")]:
        g.remove(tv + list(trv))
    G = {g.name: g for g in body.vertex_groups}

    def grp(n):
        if n not in G:
            G[n] = body.vertex_groups.new(name=n)
        return G[n]
    for i, ws in saved.items():
        for n, w in ws:
            if w > 1e-4:
                grp(n).add([i], w, "REPLACE")
    for i, b in trv.items():
        grp(b).add([i], 1.0, "REPLACE")
    nrw = 0
    names = {g.index: g.name for g in body.vertex_groups}
    for it in LIMB_ITEMS:
        P, ax = it["P"], it["axis"]; pc = P - ax * it["gap"]
        la = grp(it["bone"])
        for v in me.vertices:
            dd = -(v.co - pc).dot(ax)                          # 往身體那側多遠
            if dd < -1e-6 or dd > 0.025 or any(a.data[v.index].value != 0 for a in tpl_att):
                continue
            if ((v.co - P) - ax * (v.co - P).dot(ax)).length > it["near"]:
                continue
            t = 1.0 if dd <= 0.010 else (0.025 - dd) / 0.015
            for g in v.groups:
                n = names.get(g.group, "")
                if n.startswith("J_Bip") and n != la.name:
                    body.vertex_groups[g.group].add([v.index], g.weight * (1 - t), "REPLACE")
            cur = next((g.weight for g in v.groups if g.group == la.index), 0.0)
            la.add([v.index], cur * (1 - t) + t, "REPLACE"); nrw += 1
    for g in [g for g in body.vertex_groups if g.name.startswith("TPL_")]:
        body.vertex_groups.remove(g)
    return nrw


def attach_head(arm):
    for n in ("AI_Head", "Bust", "Camera", "Fill_FrontRight", "Key_FrontLeft", "Rim_Back"):   # Bust：產線做的頭胸像是獨立物件（新郎頭的胸像在 Head 裡，用下面的 Mask 藏）
        if n in O:
            O.remove(O[n], do_unlink=True)
    if "WGT_circle" in O:
        O["WGT_circle"].hide_render = True; O["WGT_circle"].hide_viewport = True
    hd = O["Head"]                                       # 藏掉胸像底座：Mask 修改器（不刪點，形態鍵與原檔都不動）
    vg = hd.vertex_groups.new(name="BODY_KEEP")
    vg.add([v.index for v in hd.data.vertices if v.co.z >= NECK_CUT_FILE - (1e-5 if RING else 0.0)], 1.0, "REPLACE")   # 有環：環上的點一定保留
    mk = hd.modifiers.new("HideBust", "MASK"); mk.vertex_group = "BODY_KEEP"
    while hd.modifiers[0] != mk:
        bpy.ops.object.select_all(action="DESELECT"); bpy.context.view_layer.objects.active = hd
        bpy.ops.object.modifier_move_up(modifier=mk.name)
    fr = O["Face_Rig"]
    fr.parent = arm; fr.parent_type = "BONE"; fr.parent_bone = "J_Bip_C_Head"
    bpy.context.view_layer.update()
    fr.matrix_world = Matrix.Translation(Vector((0, 0, P["pivot_z"])) - PIVOT_FILE * S) @ Matrix.Scale(S, 4)
    return fr


def add_twist_bones(arm):
    """前臂扭轉輔助骨的約束（references/research-limb-deformation.md 1.5）：每根一個 Transformation 約束，
    讀手掌的本地轉動、用前臂的軸拆（LOCAL_OWNER_ORIENT），只取繞前臂長軸的扭轉（SWING_TWIST_Y，手腕彎多少不算），乘上 1/3、2/3 寫到自己的 Y 軸。
    扭轉量只在約束結果裡：動畫端每格把所有骨頭歸零（旋轉 (1,0,0,0)）、只對 J_Bip_ 打關鍵影格，都不影響（2026-10-14 和動畫端約定）"""
    for s in "LR":
        for k_, f_ in ((1, 1 / 3), (2, 2 / 3)):
            pb = arm.pose.bones[f"J_Adj_{s}_LowerArmTwist{k_}"]
            pb.rotation_mode = "QUATERNION"
            c = pb.constraints.new("TRANSFORM"); c.name = "TwistFromHand"
            c.target = arm; c.subtarget = f"J_Bip_{s}_Hand"
            # 讀手掌的本地轉動，但用「扭轉骨自己（＝前臂）的軸」來拆扭轉：手掌骨頭方向和前臂差約 6°，用手掌自己的軸拆，
            #   手腕只往掌心彎 70° 扭轉骨也會跟著轉 3～6°（2026-10-14 實測；標準 ≤ 2°）
            c.target_space = "LOCAL_OWNER_ORIENT"; c.owner_space = "LOCAL"
            c.map_from = "ROTATION"; c.from_rotation_mode = "SWING_TWIST_Y"
            c.from_min_y_rot = -math.pi; c.from_max_y_rot = math.pi
            c.map_to = "ROTATION"; c.map_to_x_from = "X"; c.map_to_y_from = "Y"; c.map_to_z_from = "Z"
            c.to_min_y_rot = -math.pi * f_; c.to_max_y_rot = math.pi * f_
            c.mix_mode_rot = "REPLACE"


def twist_weights(body):
    """前臂權重沿長度分給扭轉骨（手肘 t＝0、手腕 t＝1）：0～1/3 前臂→扭轉 1、1/3～2/3 扭轉 1→扭轉 2、2/3 以後全給扭轉 2。
    上臂、手掌的權重不動；手模板那段前臂也照同一條規則分，接口環兩側同位置的權重一樣"""
    G = {g.name: g for g in body.vertex_groups}
    n = 0
    for s, sg in (("L", 1), ("R", -1)):
        a1, a2 = L[f"J_Bip_{s}_LowerArm"][0], L[f"J_Bip_{s}_LowerArm"][1]
        la = G.get(f"J_Bip_{s}_LowerArm")
        if la is None:
            continue
        t1 = G.get(f"J_Adj_{s}_LowerArmTwist1") or body.vertex_groups.new(name=f"J_Adj_{s}_LowerArmTwist1")
        t2 = G.get(f"J_Adj_{s}_LowerArmTwist2") or body.vertex_groups.new(name=f"J_Adj_{s}_LowerArmTwist2")
        d = a2 - a1
        for v in body.data.vertices:
            if v.co.x * sg <= 0:
                continue
            w = next((g.weight for g in v.groups if g.group == la.index), 0.0)
            if w <= 0:
                continue
            t = (v.co - a1).dot(d) / d.length_squared
            if t <= 0:
                continue
            t = min(1.0, t)
            if t < 1 / 3:
                wl, w1, w2 = w * (1 - 3 * t), w * 3 * t, 0.0
            elif t < 2 / 3:
                wl, w1, w2 = 0.0, w * (2 - 3 * t), w * (3 * t - 1)
            else:
                wl, w1, w2 = 0.0, 0.0, w
            if wl > 1e-6:
                la.add([v.index], wl, "REPLACE")
            else:
                la.remove([v.index])
            if w1 > 1e-6:
                t1.add([v.index], w1, "REPLACE")
            if w2 > 1e-6:
                t2.add([v.index], w2, "REPLACE")
            n += 1
    return n


def add_half_bones(arm):
    """手肘、膝蓋的半轉輔助骨（references/research-limb-deformation.md 5.5 第 3 項）：每根一個 Copy Rotation 約束，
    抄下一節（LowerArm／LowerLeg）相對上一節的本地轉動、影響 0.5 → 關節中間那圈皮膚只轉一半，不會像一般變形那樣兩邊平均而塌扁
    （2026-10-14 實測：手肘彎 90° 截面只剩 0.71、120° 0.50）。扭轉量只在約束結果裡，動畫端每格歸零不受影響"""
    for s in "LR":
        for nm, src in (("ElbowHalf", "LowerArm"), ("KneeHalf", "LowerLeg")):
            pb = arm.pose.bones[f"J_Adj_{s}_{nm}"]
            pb.rotation_mode = "QUATERNION"
            c = pb.constraints.new("COPY_ROTATION"); c.name = "HalfOf" + src
            c.target = arm; c.subtarget = f"J_Bip_{s}_{src}"
            c.target_space = "LOCAL"; c.owner_space = "LOCAL"; c.mix_mode = "REPLACE"; c.influence = 0.5


def half_weights(body):
    """關節帶的權重分給半轉骨：沿肢體軸離關節 s（上一節為負），帶半寬 b＝HALFB × 該處肢體半徑（點到骨頭線的距離），
    半轉骨權重 h＝cos²(π/2 · |s|/b)（關節中心 1、帶邊 0），原本的權重乘 (1−h)"""
    G = {g.name: g for g in body.vertex_groups}
    bones = {b.name for b in O["Body_Armature"].data.bones if b.use_deform}
    n = 0
    for s, sg in (("L", 1), ("R", -1)):
        for nm, up, lo in (("ElbowHalf", "UpperArm", "LowerArm"), ("KneeHalf", "UpperLeg", "LowerLeg")):
            hn = f"J_Adj_{s}_{nm}"
            hg = G.get(hn) or body.vertex_groups.new(name=hn); G[hn] = hg
            a, j = L[f"J_Bip_{s}_{up}"][0], L[f"J_Bip_{s}_{lo}"][0]
            e = L[f"J_Bip_{s}_{lo}"][1]
            du = (j - a).normalized(); dl = (e - j).normalized()
            ax = (du + dl).normalized()
            limb = (up, lo, "LowerArmTwist")
            for v in body.data.vertices:
                if v.co.x * sg <= 0 and nm == "ElbowHalf":
                    continue
                if (v.co.x - j.x) * sg < -0.08 and nm == "KneeHalf":
                    continue
                p = v.co - j
                sd_ = p.dot(ax)
                r = (p - ax * sd_).length
                if r > 0.12:
                    continue
                gs = [(body.vertex_groups[g.group].name, g.weight) for g in v.groups if body.vertex_groups[g.group].name in bones]
                if not any(any(k in gn for k in limb) and f"_{s}_" in gn for gn, _ in gs):
                    continue
                b = HALFB * max(r, 0.01)
                if abs(sd_) >= b:
                    continue
                h = math.cos(math.pi / 2 * abs(sd_) / b) ** 2
                for gn, w in gs:
                    G[gn].add([v.index], w * (1 - h), "REPLACE")
                hg.add([v.index], h, "REPLACE"); n += 1
    return n


def joint_cs(body):
    """手肘、膝蓋那一段的修正平滑（references/research-limb-deformation.md 2.2、5.5 第 2 項）：骨架變形之後把關節內側被擠出來的凹口抹圓，
    再把靜止時的形狀細節加回去（Corrective Smooth，靜止來源 ORCO、依邊長加權）。只作用在關節帶（點群組 JOINT_CS，中心 1、帶邊漸變到 0）"""
    vg = body.vertex_groups.new(name="JOINT_CS")
    for s, sg in (("L", 1), ("R", -1)):
        for up, lo in (("UpperArm", "LowerArm"), ("UpperLeg", "LowerLeg")):
            a, j = L[f"J_Bip_{s}_{up}"][0], L[f"J_Bip_{s}_{lo}"][0]; e = L[f"J_Bip_{s}_{lo}"][1]
            ax = ((j - a).normalized() + (e - j).normalized()).normalized()
            for v in body.data.vertices:
                if (v.co.x - j.x) * sg < -0.06:
                    continue
                p = v.co - j; sd_ = p.dot(ax); r = (p - ax * sd_).length
                if r > 0.10:
                    continue
                b = JCSW * max(r, 0.01)
                if abs(sd_) < b:
                    vg.add([v.index], math.cos(math.pi / 2 * abs(sd_) / b) ** 2, "REPLACE")
    cs = body.modifiers.new("JointSmooth", "CORRECTIVE_SMOOTH")
    cs.rest_source = "ORCO"; cs.smooth_type = "LENGTH_WEIGHTED"; cs.factor = JCSF; cs.iterations = JCSN
    cs.vertex_group = "JOINT_CS"; cs.use_only_smooth = False


def clean_weights(body, arm):
    """權重清理（references/research-limb-deformation.md 第 4 節）。在 weld_head 之後呼叫（脖子頂 100% 頭骨那段已經寫好）。
    2026-10-14 實測（_tplF3.work）：自動權重的軀幹、腿左右互吃 3,470 點（只轉左大腿 30°，右邊的點被拖 12.5 mm）、
    每點最多 7 根骨頭、總和不是 1 的點 3.9 萬、碎權重 6 千多筆；手腳模板本身是乾淨的。
      ① 四肢上的點（離它最近的骨頭是手臂、腿、手腳）：另一側（L↔R）骨頭的權重從正中線往外漸減，MIDBAND×0.5 起、MIDBAND×2 清光；
         軀幹上的點不動（胯下、肚子中線本來就要左右混）
      ② 四肢上的點（離它最近的骨頭是手臂、腿、手腳）：清掉離它很遠的骨頭（> max(2.5×最近距離, 最近距離＋4 cm)）
      ③ 每點最多 4 根、碎權重（< 0.01）清掉、總和 1——用連續的做法（見下面註解）；只動會變形的骨頭群組，HAND_DQS 這類遮罩群組不動
    服裝的 transfer_weights 也做 ③，身體先做完，兩邊就一致"""
    B = arm.data.bones
    deform = {b.name for b in B if b.use_deform and (b.name.startswith("J_Bip") or b.name.startswith("J_Adj_"))}
    seg = {n: (B[n].head_local.copy(), B[n].tail_local.copy()) for n in deform}
    LIMB = ("UpperArm", "LowerArm", "Hand", "Thumb", "Index", "Middle", "Ring", "Little", "UpperLeg", "LowerLeg", "Foot", "ToeBase")
    gname = {g.index: g.name for g in body.vertex_groups}
    G = {g.name: g for g in body.vertex_groups}

    def sd(p, a, b):
        d = b - a; t = max(0.0, min(1.0, (p - a).dot(d) / d.length_squared)); return (p - (a + d * t)).length
    side_rm = far_rm = 0
    for v in body.data.vertices:
        ws = [(gname[g.group], g.weight) for g in v.groups if gname.get(g.group) in deform and g.weight > 0]
        if len(ws) < 2:
            continue
        p = v.co
        dist = {n: sd(p, *seg[n]) for n in seg}
        near = min(dist, key=dist.get); dmin = dist[near]
        limb = any(k in near for k in LIMB)
        sided = "_L_" in near or "_R_" in near                # 四肢＋鎖骨（Shoulder）：鎖骨不算四肢，但左鎖骨的權重會延伸到右肩頸（2026-10-14 實測 195 點）
        if not sided or WCMODE == "norm":
            continue                                        # 軀幹上的點（胯下、肚子中線）左右骨頭本來就該混，不動
        for n, w in ws:
            other = ("_L_" in n and p.x < 0) or ("_R_" in n and p.x > 0)
            if other:
                # 四肢上的點吃到另一側骨頭：從正中線往外漸減到 0，不一刀切
                #   （2026-10-14 第一版在 ±2 cm 一刀切掉，大腿一扭，下腹、胯下就皺出一條摺痕）
                t = max(0.0, min(1.0, (abs(p.x) - MIDBAND * 0.5) / (MIDBAND * 1.5)))
                f = t * t * (3 - 2 * t)
                if f >= 0.999:
                    G[n].remove([v.index])
                else:
                    G[n].add([v.index], w * (1 - f), "REPLACE")
                side_rm += 1
            elif limb and any(k in n for k in LIMB) and dist[n] > max(2.5 * dmin, dmin + 0.04):
                G[n].remove([v.index]); far_rm += 1
    # ③ 連續版：超過 4 根時每根都減掉第 5 大的值 → 正規化 → 每根再減 0.01（小於的變 0）→ 正規化。
    #   不用 Blender 的 vertex_group_clean／limit_total：那兩個是「剛好超過門檻就留、沒超過就砍」，自動權重在下腹、胯下有很多很小的
    #   骨頭影響，相鄰兩點一留一砍，大腿一扭皮膚就皺出凹凸（2026-10-14 實測：變形差異的粗糙度 5.5 → 連續版 0.34）
    gname = {g.index: g.name for g in body.vertex_groups}
    n4 = 0
    for v in body.data.vertices:
        ws = sorted([(gname[g.group], g.weight) for g in v.groups if gname.get(g.group) in deform and g.weight > 0], key=lambda x: -x[1])
        if not ws:
            continue
        if len(ws) > 4:
            th = ws[4][1]; ws = [(n, w - th) for n, w in ws]; n4 += 1
        t0 = sum(w for _, w in ws if w > 0)
        ws = [(n, w / t0) for n, w in ws if w > 0]
        ws2 = [(n, w - 0.01) for n, w in ws if w > 0.01] or ws[:1]
        t = sum(w for _, w in ws2)
        keep = {n for n, _ in ws2}
        for g in list(v.groups):
            n = gname.get(g.group)
            if n in deform and n not in keep:
                G[n].remove([v.index])
        for n, w in ws2:
            G[n].add([v.index], w / t, "REPLACE")
    return dict(side_removed=side_rm, far_removed=far_rm, over4=n4)


def bind(body, arm):
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active = arm
    tw_bones = [b for b in arm.data.bones if b.name.startswith("J_Adj_")]
    for b in tw_bones:                                    # 自動權重先不分給扭轉骨（手腳研究 [W9] 同一招），之後照前臂長度分
        b.use_deform = False
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    tpl_weights(body)
    for b in tw_bones:
        b.use_deform = True
    if any("Twist" in b.name for b in tw_bones):
        twist_weights(body)
    if any("Half" in b.name for b in tw_bones):
        half_weights(body)
    # v8：手的部分疊一層「保留體積」變形（dual quaternion），手指彎到底不塌；只作用在手掌手指、往手腕淡出，身體其他地方不變
    hand_bones = {g.index for g in body.vertex_groups if any(k in g.name for k in ("_Hand", "Thumb", "Index", "Middle", "Ring", "Little"))}
    hv = body.vertex_groups.new(name="HAND_DQS")
    for v in body.data.vertices:
        w = min(1.0, sum(g.weight for g in v.groups if g.group in hand_bones))
        if w > 1e-3:
            hv.add([v.index], w, "REPLACE")
    m0 = next(m for m in body.modifiers if m.type == "ARMATURE")
    if HANDDEF == "dqs":
        m1 = body.modifiers.new("Armature_HandVolume", "ARMATURE"); m1.object = arm
        m1.use_deform_preserve_volume = True; m1.use_multi_modifier = True; m1.vertex_group = "HAND_DQS"
    elif HANDDEF == "cs":                                  # 比較用：手改用一般變形＋修正平滑（研究 2.5）
        cs = body.modifiers.new("HandSmooth", "CORRECTIVE_SMOOTH")
        cs.rest_source = "ORCO"; cs.smooth_type = "LENGTH_WEIGHTED"; cs.factor = 0.5; cs.iterations = 8; cs.vertex_group = "HAND_DQS"
    if JOINTCS:
        joint_cs(body)
    groups = {g.index: g.name for g in body.vertex_groups}
    unweighted = sum(1 for v in body.data.vertices if not any(g.weight > 1e-4 for g in v.groups))
    return len(groups), unweighted


# ════════ 攝影棚 ════════
def studio():
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 24
    sc.view_settings.view_transform = "Standard"; sc.view_settings.exposure = -0.5
    w = sc.world or bpy.data.worlds.new("World"); sc.world = w
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (0.93, 0.91, 0.89, 1); bg.inputs[1].default_value = 1.0

    def light(name, kind, loc, rot, e, size=None):
        o = O.new(name, bpy.data.lights.new(name, kind)); sc.collection.objects.link(o)
        o.location = loc; o.rotation_euler = [math.radians(a) for a in rot]; o.data.energy = e
        if size:
            o.data.size = size
        return o
    light("Sun", "SUN", (2, -4, 5), (50, 0, 20), 2.5).data.angle = math.radians(8)
    light("Fill", "AREA", (-3, -3, 2.5), (60, 0, -45), 250, 3)
    light("Rim", "AREA", (1.5, 3.0, 2.6), (-60, 0, 155), 200, 2)
    me = bpy.data.meshes.new("Floor"); bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=64, radius=6); bm.to_mesh(me); bm.free()
    fl = O.new("Floor", me); sc.collection.objects.link(fl)
    m = bpy.data.materials.new("FloorMat")
    p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    p.inputs["Base Color"].default_value = (0.55, 0.52, 0.50, 1); p.inputs["Roughness"].default_value = 0.9
    me.materials.append(m)
    cam = O.new("Camera", bpy.data.cameras.new("Camera")); sc.collection.objects.link(cam); sc.camera = cam
    return cam


def aim(cam, loc, target, lens=50, ortho=None):
    cam.location = loc
    if ortho:
        cam.data.type = "ORTHO"; cam.data.ortho_scale = ortho
    else:
        cam.data.type = "PERSP"; cam.data.lens = lens
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


def shot(path, res=(640, 640)):
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"; sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def views(cam, prefix, target, dist, angles, lens=50, res=(640, 640), ortho=None, h_off=0.0):
    """angle：0＝正面、45＝角色右前方、90＝角色右側、180＝背面、−45＝左前方；'top'＝正上方、'under'＝正下方"""
    out = []
    for a in angles:
        if a == "top":
            aim(cam, Vector(target) + Vector((0, -0.001, dist)), target, lens, ortho)
        elif a == "under":
            aim(cam, Vector(target) + Vector((0, -0.001, -dist)), target, lens, ortho)
        else:
            r = math.radians(a)
            aim(cam, Vector(target) + Vector((-math.sin(r) * dist, -math.cos(r) * dist, h_off)), target, lens, ortho)
        p = f"{prefix}_{a}.png"; shot(p, res); out.append(os.path.basename(p))
    return out


# ════════ 主流程 ════════
L = bones_layout()
arm = build_armature(L)
body, n_raw = build_mesh(L)
mat, skin_srgb = skin_material()
body.data.materials.clear(); body.data.materials.append(mat)
fr = attach_head(arm)
RINGFIT = fit_neck_ring(body) if RING else None
print("RINGFIT", RINGFIT)
LIMBFIT = fit_tpl_rings(body)
print("LIMBFIT", LIMBFIT)
SMOOTHED = smooth_normals(body) if SMOOTHNRM else None
NECK_BLENDED = blend_head_neck(SKIN_LIN) if NECKBLEND else False
n_groups, n_unweighted = bind(body, arm)
WELD = weld_head(body) if HEADWELD else None
WCLEAN = clean_weights(body, arm) if WEIGHTCLEAN else None
print("WCLEAN", WCLEAN)
RINGREP = ring_report(body) if RING else None
print("RINGREP", RINGREP)
print("WELD", WELD)
SEAM_FIXED = seam_normals(body) if SEAMFIX else False
tgt = mr.Target(arm)
cam = studio()
bpy.context.view_layer.update()
cz = crotch_z(body)
_sec = [v.co for v in body.data.vertices if abs(v.co.z - (NECK_CUT_Z - 0.004)) < 0.003]
NECK_SEC = dict(body_rx=round(max(abs(c.x) for c in _sec), 4), body_ry=round((max(c.y for c in _sec) - min(c.y for c in _sec)) / 2, 4),
                body_yc=round((max(c.y for c in _sec) + min(c.y for c in _sec)) / 2, 4),
                head_rx=round(HM["neck_rx"] * S, 4), head_ry=round(HM["neck_ry"] * S, 4), head_yc=round((HM["neck_yc"] - PIVOT_FILE.y) * S, 4)) if _sec else {}
print("NECKSEC", NECK_SEC)
import hashlib
info = dict(head=dict(path=bpy.data.filepath.replace("\\", "/"), sha256=hashlib.sha256(open(bpy.data.filepath, "rb").read()).hexdigest(),
                      measured={k_: (list(round(x, 4) for x in v) if hasattr(v, "x") else round(v, 4)) for k_, v in HM.items() if k_ not in ("ring_local", "ring_file", "ring_src")}, cut_used=round(NECK_CUT_FILE, 4), neck_factor=round(NF, 3),
                      chin_source=CHIN_SRC[0], shoulder_up=round(SHUP, 4)),
            uv_layers=[u.name for u in body.data.uv_layers], skin_source=SKINSRC, neck_fit=NECKFIT, neck_blend=NECK_BLENDED, seam_normals=SEAM_FIXED, head_weld=WELD, neck_ring=dict(fit=RINGFIT, check=RINGREP) if RING else None, neck_section=NECK_SEC,
            N=N, H=H, T=T, voxel=VOXEL, BW=BW, BD=BD, LW=LW, crotch_z=round(cz, 3) if cz else None, faces_after_remesh=n_raw, faces=len(body.data.polygons), verts=len(body.data.vertices),
            vertex_groups=n_groups, unweighted_verts=n_unweighted, skin_srgb=[round(c, 3) for c in skin_srgb], limb_templates=LIMBFIT, smooth_normals=SMOOTHED, weight_clean=WCLEAN,
            params={k_: round(v, 4) for k_, v in P.items()}, build_sec=round(time.time() - T0, 1))
print("BUILT", json.dumps(info, ensure_ascii=False))
# v3 起：頭的貼圖打包進 body.blend。以前讀頭資料夾的外部圖檔（絕對路徑），大頭端改了圖，已出廠的身體外觀就跟著變、指紋卻不變
try:
    bpy.ops.file.pack_all()
except Exception as e:
    print("PACK failed", e)
info["packed_images"] = sum(1 for im in bpy.data.images if im.packed_file)
# 交接尺寸（body_measure.py；2026-10-14）：T 字靜止量，寫進 build.json 的 measure，出廠時 body_status.py 複製到 RELEASE.json 並列出和上一版的差
try:
    _mp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "body_measure.py")
    _mn = {"__name__": "body_measure_embed", "MEASURE_EMBED": True}
    exec(compile(open(_mp, encoding="utf-8").read(), _mp, "exec"), _mn)
    info["measure"] = _mn["res"]
except Exception as e:
    info["measure"] = dict(error=str(e)[:200])
    print("MEASURE failed", e)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "body.blend"))

idle = mr.retarget(mr.read_fbx(os.path.join(RAW, "female_idle.fbx")), tgt)


def pose_from_clip(clip, f, ref=None):
    ref = f if ref is None else ref
    mr.apply_pose(arm, tgt, clip["R"][f], clip["hips"][f])
    y = clip["yaw"][ref]; h = clip["hips"][ref]
    arm.rotation_euler = (0, 0, -y)
    arm.location = -(Matrix.Rotation(-y, 4, "Z") @ Vector((h.x, h.y, 0)))
    bpy.context.view_layer.update()


def rest_pose():
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
    arm.location = (0, 0, 0); arm.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()


imgs = {}
if "rest" in QA:
    rest_pose()
    imgs["rest"] = views(cam, os.path.join(OUT, "rest"), (0, 0, 0.78), 6, (0, 45, 90, 180), ortho=1.75, res=(560, 640))
    pose_from_clip(idle, 0)
    imgs["idle"] = views(cam, os.path.join(OUT, "idle"), (0, 0, 0.78), 6, (0, 45, 90, 180), ortho=1.75, res=(560, 640))
    # UV 檢查：暫時換成棋盤格材質拍正面、背面——格子全身大小一致＝布紋粗細一致；格子方向會因島而轉，屬已知
    ck = bpy.data.materials.new("QA_UVChecker"); nt = ck.node_tree
    tx = nt.nodes.new("ShaderNodeTexImage")
    im = bpy.data.images.new("QA_UVGrid", 1024, 1024); im.generated_type = "COLOR_GRID"; tx.image = im
    nt.links.new(tx.outputs["Color"], next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"])
    body.data.materials[0] = ck
    imgs["uv"] = views(cam, os.path.join(OUT, "uv"), (0, 0, 0.78), 6, (0, 180), ortho=1.75, res=(560, 640))
    body.data.materials[0] = mat
    bpy.data.materials.remove(ck); bpy.data.images.remove(im)
if "close" in QA:
    rest_pose()
    g = lambda n: arm.matrix_world @ arm.pose.bones[n].head
    hc = g("J_Bip_L_Hand") + Vector((0.05, -0.005, 0))
    imgs["hand"] = views(cam, os.path.join(OUT, "hand"), hc, 0.32, ("top", "under", 0, 180))
    nk = Vector((0, 0, P["sh_z"] + 0.02))
    imgs["neck"] = views(cam, os.path.join(OUT, "neck"), nk, 0.55, (0, 45, 90, 180), h_off=0.05)
    pose_from_clip(idle, 0)
    ft = g("J_Bip_L_Foot")
    imgs["feet"] = views(cam, os.path.join(OUT, "feet"), Vector((0, ft.y - 0.03, 0.12)), 0.75, (0, 45, 90), h_off=0.15)
if "motion" in QA:
    tests = (("walk", "male_standard_walk.fbx", "mid"), ("wave_both", "waving_both_hands.fbx", "top"),
             ("sit", "sitting_idle.fbx", 0), ("thumbs", "sitting_thumbsup.fbx", "top"))
    for key, fbx, which in tests:
        clip = mr.retarget(mr.read_fbx(os.path.join(RAW, fbx)), tgt)
        if which == "mid":
            f = clip["n"] // 3
        elif which == "top":
            best = (-1e9, 0)
            for f_ in range(0, clip["n"], 2):
                pose_from_clip(clip, f_, 0)
                z = max((arm.matrix_world @ arm.pose.bones[f"J_Bip_{s}_Hand"].head).z for s in ("L", "R"))
                if z > best[0]:
                    best = (z, f_)
            f = best[1]
        else:
            f = which
        pose_from_clip(clip, f, 0)
        c = arm.matrix_world @ arm.pose.bones["J_Bip_C_Spine"].head
        imgs[key] = views(cam, os.path.join(OUT, f"motion_{key}"), c + Vector((0, 0, 0.12)), 2.6, (0, 45, 90), res=(560, 640))
    # 手到嘴邊：右手握叉子（共用手勢 fork_grip），叉尖送到嘴唇。v7 前沒有叉子、手背擋在嘴前，看起來像摀嘴（服裝 session 指出）
    R, hips = dict(idle["R"][0]), idle["hips"][0].copy(); hips.x = hips.y = 0
    mr.apply_pose(arm, tgt, R, hips); arm.location = (0, 0, 0); arm.rotation_euler = (0, 0, 0); bpy.context.view_layer.update()
    mouth = fr.matrix_world @ MOUTH_FILE
    appr = Vector((0.30, 0.85, 0.35)).normalized()             # 叉子從右前下方往嘴巴送（角色右手在 −X）
    palm = Vector((0.45, 0.0, -0.9)).normalized()              # 掌心朝下、朝身體中線
    FORK = 0.09                                                 # 食指根到叉尖（m）
    tip_goal = mouth - appr * 0.004
    wrist = tip_goal - appr * (FORK + 0.5 * HL)
    for _ in range(4):
        R2 = mr.arm_ik(tgt, R, hips, "R", wrist, Vector((-0.5, -0.15, -0.85)))
        R2 = mr.aim_hand(tgt, R2, hips, "R", appr, palm=palm)
        R2 = mr.gesture(tgt, R2, "R", "fork_grip")
        mr.apply_pose(arm, tgt, R2, hips); bpy.context.view_layer.update()
        i0 = arm.matrix_world @ arm.pose.bones["J_Bip_R_Index1"].head
        i3 = arm.matrix_world @ arm.pose.bones["J_Bip_R_Index3"].tail
        fd = (i3 - i0).normalized(); tip = i0 + fd * FORK
        wrist = wrist + (tip_goal - tip)
    fork_gap = (tip_goal - tip).length
    me = bpy.data.meshes.new("QA_Fork"); bm = bmesh.new()
    capsule_bm(bm, i0 - fd * 0.03, tip - fd * 0.025, 0.0028, 0.0024)
    ellip_bm(bm, tip - fd * 0.012, (0.006, 0.006, 0.0015), fd.to_track_quat("Y", "Z").to_matrix().to_4x4())
    bm.to_mesh(me); bm.free()
    fk = O.new("QA_Fork", me); sc.collection.objects.link(fk)
    fm = bpy.data.materials.new("QA_ForkMat"); fp = next(n for n in fm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    fp.inputs["Base Color"].default_value = (0.75, 0.75, 0.78, 1); fp.inputs["Metallic"].default_value = 1.0; fp.inputs["Roughness"].default_value = 0.3
    me.materials.append(fm)
    hp = arm.matrix_world @ arm.pose.bones["J_Bip_C_Head"].head
    imgs["mouth"] = views(cam, os.path.join(OUT, "motion_mouth"), hp + Vector((-0.05, 0, -0.1)), 1.0, (0, 45, 90))
    info["fork_tip_gap_cm"] = round(fork_gap * 100, 2)
    O.remove(fk, do_unlink=True)
    # 比 YA（左手）
    R3 = mr.gesture(tgt, R, "L", "peace")
    sh = tgt.fk(R3, hips)["J_Bip_L_UpperArm"]
    R3 = mr.arm_ik(tgt, R3, hips, "L", sh + Vector((0.10, -0.16, 0.12)), Vector((0.6, 0.2, -0.8)))
    R3 = mr.aim_hand(tgt, R3, hips, "L", Vector((0.15, 0.0, 1.0)), palm=Vector((0, 1, 0)))
    mr.apply_pose(arm, tgt, R3, hips); bpy.context.view_layer.update()
    hd = arm.matrix_world @ arm.pose.bones["J_Bip_L_Hand"].head
    imgs["ya"] = views(cam, os.path.join(OUT, "motion_ya"), hd + Vector((0, 0, 0.05)), 0.5, (0, 30, -30))

info["imgs"] = imgs
info["args"] = {k: v for k, v in ARGS.items() if k != "OUT"}   # 這次給的參數（其餘用預設）；要重做同一副身體照抄這些
info["total_sec"] = round(time.time() - T0, 1)
json.dump(info, open(os.path.join(OUT, "build.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("DONE", info["total_sec"])
