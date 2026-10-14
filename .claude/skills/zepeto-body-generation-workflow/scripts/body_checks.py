# 身體出廠檢查。背景 Blender 開 body.blend 跑，結果寫 <身體資料夾>/checks.json；全部通過才可以出廠（release.py）。
# 用法：blender -b <build>/<名稱>/body.blend -P body_checks.py [-- DIAG=1] [OUT=<checks.json 另存路徑>] [PENV=1] [GEO=1.5]
#   PENV＝穿插量法版本：2（預設，2026-10-14 起）／1（舊量法，只供對照）
# 2026-10-14 量法 v2（手腳研究 research-hands-feet.md 第 0 步）：舊量法把同一處 4～6 mm 擠壓一下算「關節內側」、一下算「插進掌心」、
#   一下量到 0（部位靠「最大權重是哪根骨頭」、同一塊皮膚靠「靜止時 6 mm 內」）。v2：
#   · 部位＝靜止姿勢下離哪一節骨頭最近（不看權重）；
#   · 同一塊皮膚＝沿網格邊走的距離 < GEO × 手指直徑（預設 1.5）；
#   · 指根（手掌↔第一節）、同指相鄰節都算關節內側擠壓（crease）；
#   · 埋住判定＝點往「照骨頭轉動推算的朝外方向」挪 0.2 mm 後，往 6 個方向射線數穿過幾層皮，奇數＝在肉裡（不看面朝哪）。
#     不用網格自己的法線、不用「從哪一面穿出去」：彎曲內側皮膚摺到翻面時這兩樣都會錯，量出 5～9 mm 的假穿插
#     （新郎 v8 握拳 18 點全是這樣；用骨頭位置獨立量，那些點其實在別根手指外面 5 mm）；
#   · 埋在誰裡面＝往外射第一個碰到的皮膚；同一根手指＝crease，深度量到最近沒被埋住的皮膚；別的部位＝量到最近的別的部位表面；
#   · 另外記（參考、還沒定門檻）：buried 埋住的點數、fold 翻面的面數（皮膚摺過頭）、tri_cross 三角形交叉對數（排除同一塊皮膚、分類別）、
#     手與腳的指紋（點座標＋權重的雜湊，同參數要一樣）。
# 2026-10-12 照導演 session 轉使用者的要求加入（手指張開僵 → 身體端把關）。標準：
#   1 bend          四指各節彎 90° 指節厚度保留率 ≥ 0.85、60° ≥ 0.92（且不超過 1.15，不鼓脹）
#   2 interpen      共用 9 個手勢＋四指 90°：不同部位之間（手指對手指、手指對手掌、拇指對手指）最深陷入 ≤ 1 mm
#     crease        同一根手指相鄰兩節在關節內側擠壓（彎超過約 80° 時皮膚往內摺、外面看不到）：≤ 手指半徑 × 0.8
#                   不算進 interpen。2026-10-12 使用者確認為正式標準（經導演 session）。
#   3 weight_trans  每指每關節的權重過渡寬度＝手指直徑的 0.6～1.2 倍
#   4 rest_fingers  靜止姿勢手指（含拇指）方向和 Mixamo 標準差 ≤ 3°
#   5 gestures      共用 9 個手勢都擺得出來、不同部位不穿插（近照另由 hand_probe.py -- GEST=lib 出圖目視）
#   6 retarget      同一格 Mixamo 動作套上後，手指各節方向和 Mixamo 原樣差 ≤ 2°
#   basic           沒綁到的點 0、胯下高度 ≥ 身高 × 0.30（兩腿沒黏住；2026-10-14 前寫死 0.50 m，頭身比改 4.5 後身體變矮，改成比例）
#   uv              （v9 起）有 UV、全部落在 0～1、壓扁的面（UV 面積≈0）≤ 0.5%、各面 UV／實際面積比的離散（第 95／第 5 百分位）≤ 4
#                   → 布紋在全身粗細大致一樣；方向不保證（見 body_build.make_uv）
# 2026-10-14 四肢強化加的（說明、基準數字見 references/limbs.md 第 3 節）：
#   weights         擋：跨指 0、越節 0、每點 ≤ 4 根、總和 1、「動一根看鄰居」≤ 0.3 mm（weight_audit.py）
#   wrist           擋：手掌扭 80° 前臂最細截面 ≥ 0.90、150° ≥ 0.78；只彎手腕時扭轉骨 ≤ 2°；開門片烘焙成關鍵影格後 ≥ 0.85（twist_probe.py）
#                   沒有扭轉骨的身體（TWIST=0、2026-10-14 前出廠的）這項一定不過
#   limbs           參考：手肘、膝、肩、髖、腳踝、腳趾活動範圍；Mixamo 最彎那格；併腳；手指張合（limb_probe.py）。-- LIMBS=0 跳過
#   feet            參考：轉腳踝、翹腳趾時埋住／翻面／壓扁；腳底貼地（sole.ok）；鞋子尺寸（shoe）
#   v2ref           參考：權重統計、四指 0～110° 掃描
#   fingerprint     資訊：手、腳的點座標＋權重雜湊（同參數要一樣、改腳不該動到手）
#   neck_ring       擋（頭有接口環時）：頭環和身體最上圈的縫 ≤ 0.1 mm（靜止、轉頭、低頭、抬頭、張嘴）、法線差 ≤ 1°、張嘴時環動 ≤ 0.1 mm（ring_check.py）
#                   舊頭沒有環：不檢、算通過，脖子看 neck_probe 近照
import bpy, sys, os, math, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, r"D:\SideProject\wedding-invitation\.claude\skills\blender-motion-library\scripts")
import mixamo_retarget as mr

RAW = r"D:\render-work\mixamo\raw"
O = bpy.data.objects
arm = O["Body_Armature"]; body = O["Body"]; tgt = mr.Target(arm); B = arm.data.bones
FN = ("Index", "Middle", "Ring", "Little")
DIR = os.path.dirname(bpy.data.filepath)
_bj = os.path.join(DIR, "build.json")
info = json.load(open(_bj, encoding="utf-8")) if os.path.exists(_bj) else {}
FR = 0.0058
DIAG = "DIAG=1" in sys.argv
ARGV = dict(a.split("=", 1) for a in sys.argv[sys.argv.index("--") + 1:] if "=" in a) if "--" in sys.argv else {}
PENV = int(ARGV.get("PENV", "2"))
GEO = float(ARGV.get("GEO", "1.5"))
res = {}

for pb in arm.pose.bones:
    pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
bpy.context.view_layer.update()
R0 = {n: (arm.matrix_world.to_quaternion() @ B[n].matrix_local.to_quaternion()) for n in tgt.keys}
H0 = tgt.rest_h["J_Bip_C_Hips"].copy()
REST_V = [v.co.copy() for v in body.data.vertices]
HD = body.vertex_groups["HAND_DQS"].index if "HAND_DQS" in body.vertex_groups else -1
GNAME = {g.index: g.name.replace("J_Bip_L_", "").replace("J_Bip_R_", "") for g in body.vertex_groups}


def pose(R):
    mr.apply_pose(arm, tgt, R, H0); bpy.context.view_layer.update()


def eval_mesh():
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg); me = ev.to_mesh()
    V = [body.matrix_world @ v.co for v in me.vertices]
    N = [(body.matrix_world.to_3x3() @ v.normal).normalized() for v in me.vertices]
    F = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return V, N, F


def hand_faces(side):
    sg = 1 if side == "L" else -1
    wx = B[f"J_Bip_{side}_Hand"].head_local.x - sg * 0.004
    return [i for i, p in enumerate(body.data.polygons) if all(sg * body.data.vertices[v].co.x > sg * wx for v in p.vertices)]


HF = {"L": hand_faces("L")}


def main_bone(k):
    gs = [g for g in body.data.vertices[k].groups if g.group != HD]
    return GNAME.get(max(gs, key=lambda g: g.weight).group, "?") if gs else "?"


# ── 量法 v2：部位標記（靜止位置）、網格上的距離 ──
import heapq
SEGS = {}                                                   # 部位名 → (頭, 尾)（靜止、物件座標）
for nm in ["Hand"] + [f"{f}{i}" for f in ("Thumb",) + FN for i in (1, 2, 3)]:
    bn = f"J_Bip_L_{nm}"
    if bn in B:
        SEGS[nm] = (B[bn].head_local.copy(), B[bn].tail_local.copy())


def seg_dist(p, a, b):
    d = b - a; t = max(0.0, min(1.0, (p - a).dot(d) / d.length_squared)); return (p - (a + d * t)).length


REGION = {}
def region_of(vi):
    """這個點（靜止姿勢）離哪一節骨頭最近＝屬於哪一區。不看權重：權重一變分類就跳"""
    r = REGION.get(vi)
    if r is None:
        p = REST_V[vi]; r = min(SEGS, key=lambda k: seg_dist(p, *SEGS[k])); REGION[vi] = r
    return r


ADJ = None
def geo_near(vi, radius):
    """沿網格邊走、距離 vi 不超過 radius 的點集合（靜止網格；Dijkstra，有快取）"""
    global ADJ
    if ADJ is None:
        ADJ = [[] for _ in body.data.vertices]
        for e in body.data.edges:
            a, b = e.vertices; L_ = (REST_V[a] - REST_V[b]).length
            ADJ[a].append((b, L_)); ADJ[b].append((a, L_))
    c = GEO_CACHE.get(vi)
    if c is not None:
        return c
    dist = {vi: 0.0}; hq = [(0.0, vi)]
    while hq:
        d, u = heapq.heappop(hq)
        if d > dist.get(u, 1e9):
            continue
        for w, L_ in ADJ[u]:
            nd = d + L_
            if nd <= radius and nd < dist.get(w, 1e9):
                dist[w] = nd; heapq.heappush(hq, (nd, w))
    GEO_CACHE[vi] = set(dist); return GEO_CACHE[vi]


GEO_CACHE = {}
GEO_R = GEO * 2 * FR


def chain_of(r):
    return r.rstrip("123") if r != "Hand" else "Hand"


def category(ra, rb):
    """兩區之間的擠壓算哪一類。同一根手指（含手掌↔第一節的指根）＝crease"""
    fa, fb = chain_of(ra), chain_of(rb)
    if fa == fb or {ra, rb} in ({"Hand", "Index1"}, {"Hand", "Middle1"}, {"Hand", "Ring1"}, {"Hand", "Little1"}, {"Hand", "Thumb1"}):
        return "crease"
    if "Thumb" in fa + fb:
        return "thumb_on_finger"
    if "Hand" in (fa, fb):
        return "tip_in_palm"
    return "finger_finger"


GN_ = {g.index: g.name for g in body.vertex_groups}
VW = {}                                                     # 手的點 → [(骨頭名, 權重)]（不含 HAND_DQS）
for _vi in {v for i in HF["L"] for v in body.data.polygons[i].vertices}:
    VW[_vi] = [(GN_[g.group], g.weight) for g in body.data.vertices[_vi].groups
               if g.weight > 0 and GN_.get(g.group) in arm.pose.bones]
REST_FA = {i: body.data.polygons[i].area for i in HF["L"]}
REST_N = {vi: (body.matrix_world.to_3x3() @ body.data.vertices[vi].normal).normalized() for vi in VW}


def expected_normals():
    """照骨頭轉動推算每點該朝哪（靜止法線 × 各骨頭旋轉，按權重混合）。
    不能用姿勢後網格自己的法線：彎曲內側皮膚摺過去時那裡的法線會翻成朝內，往「外」射的線就整根穿過自己的手指、量到手指厚度（2026-10-14 實測新郎握拳 18 點全是這樣）"""
    rot = {}
    AW = arm.matrix_world
    out = {}
    for vi, ws in VW.items():
        acc = Vector((0, 0, 0)); tot = 0.0
        for nm, w in ws:
            if nm not in rot:
                rot[nm] = (AW @ arm.pose.bones[nm].matrix @ B[nm].matrix_local.inverted() @ AW.inverted()).to_3x3()
            acc += (rot[nm] @ REST_N[vi]) * w; tot += w
        out[vi] = acc.normalized() if tot > 0 else REST_N[vi]
    return out


DIRS = [Vector(d) for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]


def crossings(t, q, d):
    k = 0; o = q
    for _ in range(64):
        h = t.ray_cast(o, d)
        if h[0] is None:
            break
        k += 1; o = h[0] + d * 1e-6
    return k


def inside(t, q):
    """q 在全身網格裡面嗎：往 6 個方向射到底、數穿過幾層皮，奇數＝裡面，多數決。
    只數層數、不看面朝哪：摺到翻面的皮膚是多兩層、奇偶不變，不會像「從哪一面穿出去」那樣被騙"""
    odd = 0
    for i, d in enumerate(DIRS):
        odd += crossings(t, q, d) % 2
        if odd >= 4 or odd + (5 - i) < 4:
            break
    return odd >= 4


def penetration_v2(side):
    """手的網格陷進自己另一部分多深 → {類別: 最深 mm}，外加 tri_cross（排除同一塊皮膚後相交的三角形對數，分類別）、fold（翻面的面數）。
    陷入判定：點沿「推算的朝外方向」往外 0.2 mm 還在全身網格裡面（inside）＝這點埋在別的部位裡；
    埋在誰裡面＝往外射第一個碰到的皮膚屬於哪一區；同一根手指（crease）的深度＝離最近沒被埋住的皮膚，
    別的部位的深度＝離那個部位的表面。
    2026-10-14 前用「沿法線射、先碰到從裡面出來的面」判定：彎曲內側皮膚摺到翻面時會誤判，量出 5～9 mm 的假穿插"""
    V, N, F = eval_mesh()
    NE = expected_normals()
    fs = [F[i] for i in HF[side]]
    t = BVHTree.FromPolygons(V, fs)
    tall = BVHTree.FromPolygons(V, F)
    hv = sorted({v for f in fs for v in f})
    ins = {vi for vi in hv if inside(tall, V[vi] + NE[vi] * 2e-4)}
    # 深度＝離最近「沒被埋住」的皮膚多遠（埋住的點彼此很近，不能拿來當表面；也不必再排除「同一塊皮膚」）
    efs = [i for i, f in enumerate(fs) if not any(k in ins for k in f)]
    te = BVHTree.FromPolygons(V, [fs[i] for i in efs])
    out = {}
    for vi in sorted(ins):
        ra = region_of(vi); n = NE[vi]
        # 埋在誰裡面：往外射，第一個碰到的皮膚就是把它包住的那一塊
        h = t.ray_cast(V[vi] + n * 2e-4, n, 0.03)
        rc = region_of(fs[h[2]][0]) if h[0] is not None else ra
        cat = category(ra, rc)
        if cat == "crease":             # 自己關節摺進去：深度＝離最近沒被埋住的皮膚
            g = te.find_nearest(V[vi], 0.03)
            d = g[3] if g[0] is not None else None
        else:                           # 埋進別的部位：深度＝離最近的「別的部位」表面
            # 不能只找射線碰到的那一區：指尖埋進手掌時射線會整個穿過手掌、碰到小指根，量成 7 mm 的手指對手指
            ds = [(dist, r) for loc, nor, fi, dist in t.find_nearest_range(V[vi], 0.015)
                  if category(ra, r := region_of(fs[fi][0])) != "crease"]
            if not ds:
                continue
            d, rc = min(ds)
            cat = category(ra, rc)
        if d is None:
            continue
        dm = round(d * 1000, 2)
        if dm > out.get(cat, 0.0):
            out[cat] = dm
            WORST[cat] = (dm, vi, ra, rc, tuple(round(c, 4) for c in REST_V[vi]))
    out["buried"] = len(ins)
    tri = {}
    for a, b in t.overlap(t):
        if a < b and not (set(fs[a]) & set(fs[b])):
            if not any(k in geo_near(fs[a][0], GEO_R) for k in fs[b]):
                c = category(region_of(fs[a][0]), region_of(fs[b][0]))
                tri[c] = tri.get(c, 0) + 1
    out["tri_cross"] = tri
    fold = 0
    for f in fs:
        a, b, c = V[f[0]], V[f[1]], V[f[2]]
        fn = (b - a).cross(c - a)
        if fn.length > 1e-12 and fn.dot(sum((NE[k] for k in f), Vector((0, 0, 0)))) < 0:
            fold += 1
    out["fold"] = fold
    sq = 0
    for i, f in zip(HF[side], fs):
        a = sum(((V[f[k]] - V[f[0]]).cross(V[f[k + 1]] - V[f[0]]).length for k in range(1, len(f) - 1))) / 2
        if REST_FA[i] > 1e-12 and a / REST_FA[i] < 0.3:
            sq += 1
    out["squash"] = sq
    if DIAG:
        print("DIAGW", {k: v for k, v in WORST.items()})
    WORST.clear()
    return out


WORST = {}


def penetration(side):
    """手的網格陷進自己另一部分多深 → {類別: 最深 mm}。
    每個頂點沿法線往外射：先碰到「從裡面出來」的面＝這點在另一塊肉裡面；陷入深度＝離那塊肉表面最近的距離。
    排除靜止姿勢下 6 mm 內的面（同一塊表面）。類別：crease（同一根手指相鄰節）、thumb_on_finger、tip_in_palm、finger_finger"""
    V, N, F = eval_mesh()
    fs = [F[i] for i in HF[side]]
    t = BVHTree.FromPolygons(V, fs)
    out = {}
    for vi in sorted({v for f in fs for v in f}):
        p, n = V[vi], N[vi]
        hit = t.ray_cast(p + n * 1e-5, n, 0.012)
        if hit[0] is None or hit[1].dot(n) <= 0:
            continue
        if min((REST_V[k] - REST_V[vi]).length for k in fs[hit[2]]) < 0.006:
            continue
        d = None; fbest = None
        for loc, nor, fi, dist in t.find_nearest_range(p, 0.015):
            if min((REST_V[k] - REST_V[vi]).length for k in fs[fi]) >= 0.006 and (d is None or dist < d):
                d, fbest = dist, fi
        if d is None:
            continue
        a_, b_ = main_bone(vi), main_bone(fs[fbest][0])
        fa, fb = a_.rstrip("123"), b_.rstrip("123")
        cat = ("crease" if fa == fb and fa != "Hand" else
               "thumb_on_finger" if "Thumb" in (fa + fb) else
               "tip_in_palm" if "Hand" in (fa, fb) else "finger_finger")
        out[cat] = max(out.get(cat, 0.0), round(d * 1000, 2))
    return out


def thickness(side, f, i):
    V, N, F = eval_mesh()
    t = BVHTree.FromPolygons(V, F)
    pa = arm.pose.bones[f"J_Bip_{side}_{f}{i}"]; pc = arm.pose.bones[f"J_Bip_{side}_{f}{i + 1}"]
    P = arm.matrix_world @ pc.head
    up = lambda pb: (arm.matrix_world.to_3x3() @ pb.matrix.to_3x3() @ B[pb.name].matrix_local.to_3x3().inverted() @ Vector((0, 0, 1))).normalized()
    b = (up(pa) + up(pc)).normalized(); tot = 0.0
    for s_ in (1, -1):
        h = t.ray_cast(P, b * s_, 0.05)
        if h[0] is None:
            return None
        tot += h[3]
    return tot


# 1 bend
pose(R0)
base = {(f, i): thickness("L", f, i) for f in FN for i in (1, 2)}
bend = {}
for ang in (60, 90):
    pose(mr.finger_pose(tgt, R0, "L", {f: (ang, ang, ang) for f in FN}))
    bend[ang] = {f"{f}{i}": round(thickness("L", f, i) / base[(f, i)], 3) for f in FN for i in (1, 2)}
lo60, lo90 = min(bend[60].values()), min(bend[90].values())
hi = max(max(bend[60].values()), max(bend[90].values()))
res["bend"] = dict(pass_=lo90 >= 0.85 and lo60 >= 0.92 and hi <= 1.15, value=dict(min_60=lo60, min_90=lo90, max=hi, detail=bend))

# 2 / 5 interpen, crease, gestures
names = ["rest"] + list(mr.GESTURE) + ["curl90"]
pen = {}
for n in names:
    if n == "rest":
        pose(R0)
    elif n == "curl90":
        pose(mr.finger_pose(tgt, R0, "L", {f: (90, 90, 90) for f in FN}))
    else:
        pose(mr.gesture(tgt, R0, "L", n))
    pen[n] = penetration_v2("L") if PENV == 2 else penetration("L")
    if n == "curl90":                     # 只彎四指、拇指留在靜止位置：四指撞到拇指是測試本身的安排（真人也做不到），不算
        pen[n].pop("thumb_on_finger", None)
        if isinstance(pen[n].get("tri_cross"), dict):
            pen[n]["tri_cross"].pop("thumb_on_finger", None)
    if DIAG:
        print("DIAG", n, pen[n])
cross_v = {n: max([v for c, v in pen[n].items() if c not in ("crease", "tri_cross", "fold", "buried", "squash")], default=0.0) for n in names}
tri_v = {n: pen[n].get("tri_cross", 0) for n in names}
fold_v = {n: pen[n].get("fold", 0) for n in names}
crease_v = {n: pen[n].get("crease", 0.0) for n in names}
CREASE_MAX = round(FR * 1000 * 0.8, 2)   # 手指半徑 × 0.8（使用者 2026-10-12 確認；crease 不算進 interpen）
res["interpen"] = dict(pass_=all(v <= 1.0 for v in cross_v.values()), value=dict(unit="不同部位之間最深陷入 mm（≤ 1）", **cross_v))
res["crease"] = dict(pass_=all(v <= CREASE_MAX for v in crease_v.values()),
                     value=dict(unit=f"同一根手指關節內側擠壓最深 mm（≤ {CREASE_MAX}）", **crease_v))
res["interpen"]["value"]["tri_cross"] = tri_v                    # 量法 v2 加的參考數字（還沒定門檻）
res["interpen"]["value"]["fold"] = dict(faces=len(HF["L"]), **fold_v)   # 翻面的面數（彎曲內側皮膚摺過頭；參考，還沒定門檻）
res["interpen"]["value"]["squash"] = {n: pen[n].get("squash", 0) for n in names}   # 面積壓到靜止 30% 以下的面數（參考）
res["interpen"]["value"]["buried"] = {n: pen[n].get("buried", 0) for n in names}   # 埋在肉裡的點數（參考）
res["interpen"]["value"]["method"] = f"v{PENV}" + (f"（同一塊皮膚＝網格距離 < {GEO} × 手指直徑）" if PENV == 2 else "")
res["gestures"] = dict(pass_=all(cross_v[g] <= 1.0 for g in mr.GESTURE),
                       value=dict(names=list(mr.GESTURE), note="近照由 hand_probe.py -- GEST=lib 出圖，需目視"))

# 3 weight transition
gi = {g.name: g.index for g in body.vertex_groups}
wt = {}
for f in FN:
    h1 = B[f"J_Bip_L_{f}1"].head_local; t3 = B[f"J_Bip_L_{f}3"].tail_local; d = t3 - h1; L = d.length
    rows = []
    for v in body.data.vertices:
        t = (v.co - h1).dot(d) / d.length_squared
        if -0.05 < t < 1.05 and ((v.co - h1) - d * t).length < FR * 1.3:
            w = {g.group: g.weight for g in v.groups}
            rows.append((t * L, [w.get(gi[f"J_Bip_L_{f}{i}"], 0.0) for i in (1, 2, 3)]))
    for ch in (1, 2):
        lo = [s for s, w in rows if w[ch] >= 0.1]; hi_ = [s for s, w in rows if w[ch] >= 0.9]
        wt[f"{f}{ch}"] = round((min(hi_) - min(lo)) / (2 * FR), 2) if lo and hi_ else None
vals = [v for v in wt.values() if v is not None]
res["weight_trans"] = dict(pass_=len(vals) == len(wt) and all(0.6 <= v <= 1.2 for v in vals), value=wt)

# 4 rest fingers vs Mixamo（retarget 方向對齊的角度＝兩副骨架 rest 方向差）
src = mr.read_fbx(os.path.join(RAW, "female_idle.fbx"))
rh = src["rest_h"]; lv = rh["LeftUpLeg"] - rh["RightUpLeg"]; lv.z = 0
Rg = mr.Quaternion((0, 0, 1), -mr._yaw_of(lv))
rf = {}
for n in tgt.keys:
    if n in mr._ALIGN and any(k in n for k in FN + ("Thumb",)):
        tn, sn = mr._ALIGN[n]; s0 = mr.MAP[n]
        if sn in rh:
            sd = Rg @ (rh[sn] - rh[s0]); td = (tgt.rest_h[tn] if tn else tgt.rest_t[n]) - tgt.rest_h[n]
            rf[n.replace("J_Bip_", "")] = round(math.degrees(td.angle(sd)), 1)
res["rest_fingers"] = dict(pass_=max(rf.values()) <= 3.0, value=dict(max_deg=max(rf.values()), detail=rf))

# 6 retarget：同一格 Mixamo 動作，手指各節方向（手掌方向對齊後）和來源一樣
clip = mr.retarget(src, tgt)
F_ = 0
Hs = src["H"][F_]; Rt = clip["R"][F_]; Ht = tgt.fk(Rt, clip["hips"][F_])
worst = 0.0
for side, S in (("L", "Left"), ("R", "Right")):
    ha = (Hs[f"{S}HandMiddle1"] - Hs[f"{S}Hand"]).normalized(); hb = (Ht[f"J_Bip_{side}_Middle1"] - Ht[f"J_Bip_{side}_Hand"]).normalized()
    q = hb.rotation_difference(ha)
    for f, m in (("Thumb", "Thumb"), ("Index", "Index"), ("Middle", "Middle"), ("Ring", "Ring"), ("Little", "Pinky")):
        for i in (1, 2):
            a = (Hs[f"{S}Hand{m}{i + 1}"] - Hs[f"{S}Hand{m}{i}"]).normalized()
            b = (Ht[f"J_Bip_{side}_{f}{i + 1}"] - Ht[f"J_Bip_{side}_{f}{i}"]).normalized()
            worst = max(worst, math.degrees((q @ b).angle(a)))
res["retarget"] = dict(pass_=worst <= 2.0, value=dict(max_deg=round(worst, 2), clip="female_idle", frame=F_))

# basic
unw = sum(1 for v in body.data.vertices if not any(g.weight > 1e-4 for g in v.groups))
cz = info.get("crotch_z")
tall = info.get("T", 1.5)
res["basic"] = dict(pass_=unw == 0 and (cz or 0) >= 0.30 * tall, value=dict(unweighted=unw, crotch_z=cz, crotch_ratio=round((cz or 0) / tall, 3)))

# uv
me = body.data
if not me.uv_layers:
    res["uv"] = dict(pass_=False, value=dict(note="沒有 UV"))
else:
    uvd = me.uv_layers.active.data
    ratios, flat, outside = [], 0, 0
    for p in me.polygons:
        uv = [uvd[li].uv for li in p.loop_indices]
        outside += any(not (-1e-4 <= c.x <= 1.0001 and -1e-4 <= c.y <= 1.0001) for c in uv)
        a = 0.0
        for i in range(1, len(uv) - 1):
            a += abs((uv[i].x - uv[0].x) * (uv[i + 1].y - uv[0].y) - (uv[i + 1].x - uv[0].x) * (uv[i].y - uv[0].y)) / 2
        if a < 1e-12:
            flat += 1
        elif p.area > 1e-12:
            ratios.append(a / p.area)
    ratios.sort()
    spread = ratios[int(len(ratios) * 0.95)] / ratios[int(len(ratios) * 0.05)] if ratios else 999
    n = len(me.polygons)
    res["uv"] = dict(pass_=outside == 0 and flat / n <= 0.005 and spread <= 4.0,
                     value=dict(outside=outside, flat_pct=round(flat / n * 100, 3), density_spread=round(spread, 2)))

# 量法 v2 參考指標（手腳研究第 0 步；還沒定門檻、不擋出廠，重量現有版本後再定）
# 權重：每點骨頭數、總和、跨指污染（第 2、3 節的點吃到別根手指的骨頭）
nb_max, sums, contam = 0, [], 0
for vi, ws in VW.items():
    ws = [(nm, w) for nm, w in ws if w > 1e-4]
    nb_max = max(nb_max, len(ws)); tot = sum(w for _, w in ws)
    sums.append(tot)
    r = region_of(vi)
    if r[-1:] in ("2", "3"):
        own = chain_of(r)
        contam += any(w > 0.01 and chain_of(nm.replace("J_Bip_L_", "")) not in (own,) for nm, w in ws)
wref = dict(bones_max=nb_max, sum_min=round(min(sums), 3), sum_max=round(max(sums), 3), cross_finger=contam, verts=len(VW),
            note="總和不是 1 不影響變形（Blender 骨架變形會自己除以總和）；匯出到別的引擎前才要正規化")


def section_area(VF, f, i):
    """第 i 節和第 i+1 節之間那個關節（i=1 近端指節 PIP、i=2 遠端指節 DIP）的截面積：
    用兩節方向的角平分面切這兩節的面，交點繞關節中心排角度、算多邊形面積（離中心 2.2 倍半徑內；
    放太寬會切到彎回來的指尖，2026-10-14 試 4 倍半徑在 80° 量出 1.7 倍的假鼓脹）"""
    V, F = VF
    pa = arm.pose.bones[f"J_Bip_L_{f}{i}"]; pc = arm.pose.bones[f"J_Bip_L_{f}{i + 1}"]
    AW = arm.matrix_world
    c = AW @ pc.head
    da = (AW @ pa.tail - AW @ pa.head).normalized(); dc = (AW @ pc.tail - AW @ pc.head).normalized()
    nrm = (da + dc).normalized()
    pts = []
    for fi in HF["L"]:
        poly = F[fi]
        if region_of(poly[0]) not in (f"{f}{i}", f"{f}{i + 1}"):
            continue
        for k in range(len(poly)):
            a, b = V[poly[k]], V[poly[(k + 1) % len(poly)]]
            sa, sb = (a - c).dot(nrm), (b - c).dot(nrm)
            if (sa > 0) != (sb > 0):
                q = a + (b - a) * (sa / (sa - sb))
                if (q - c).length < 2.2 * FR:
                    pts.append(q)
    if len(pts) < 6:
        return None
    u = (pts[0] - c); u = (u - nrm * u.dot(nrm)).normalized(); w_ = nrm.cross(u)
    pp = sorted(((math.atan2((q - c).dot(w_), (q - c).dot(u)), (q - c).dot(u), (q - c).dot(w_)) for q in pts))
    return abs(sum(pp[k][1] * pp[(k + 1) % len(pp)][2] - pp[(k + 1) % len(pp)][1] * pp[k][2] for k in range(len(pp)))) / 2


pose(R0)
_V, _N, _F = eval_mesh()
A0 = {(f, i): section_area((_V, _F), f, i) for f in FN for i in (1, 2)}
sweep = {}; first = {}
for ang in range(0, 111, 10):
    pose(mr.finger_pose(tgt, R0, "L", {f: (ang, ang, ang) for f in FN}))
    pv = penetration_v2("L")
    pv.pop("thumb_on_finger", None)
    if isinstance(pv.get("tri_cross"), dict):
        pv["tri_cross"].pop("thumb_on_finger", None)
    _V, _N, _F = eval_mesh()
    ar = [a / A0[k] for k in A0 if A0[k] and (a := section_area((_V, _F), *k))]
    row = dict(cross=max([v for c, v in pv.items() if c not in ("crease", "tri_cross", "fold", "buried", "squash")], default=0.0),
               crease=pv.get("crease", 0.0), tri=sum(pv["tri_cross"].values()), fold=pv["fold"], squash=pv["squash"],
               area_min=round(min(ar), 3) if ar else None, area_max=round(max(ar), 3) if ar else None)
    sweep[ang] = row
    for k, bad in (("cross", row["cross"] > 1.0), ("crease", row["crease"] > CREASE_MAX), ("tri", row["tri"] > 0),
                   ("area", row["area_min"] is not None and (row["area_min"] < 0.85 or row["area_max"] > 1.10))):
        if bad and k not in first:
            first[k] = ang
    if DIAG:
        print("SWEEP", ang, row)
res["v2ref"] = dict(pass_=True, value=dict(weights=wref, sweep=sweep, first_over_deg=first,
                                           note="四指一起彎 0～110°（拇指留在靜止）；first_over_deg＝從幾度開始超標（cross＞1 mm、crease＞半徑×0.8、tri＞0、截面積比不在 0.85～1.10）；參考，還沒定門檻"))

# 腳（手腳研究 F1～F9 的一部分；2026-10-14 腳模板試做時加，參考、不擋出廠，重量幾副身體後再定門檻）
#   F3／F4 轉腳踝、翹腳趾時埋住的點數、最深（離最近沒被埋住的皮膚）、翻面、壓扁；F5 靜止時腳底貼地；F8 鞋子要量的尺寸
_fa = body.data.attributes.get("foot_tpl")
FV = [v.index for v in body.data.vertices if v.co.x > 0 and ((_fa.data[v.index].value != 0) if _fa else v.co.z < 0.10)]
_fvs = set(FV)
FF = [i for i, p in enumerate(body.data.polygons) if all(k in _fvs for k in p.vertices)]
FVW = {vi: [(GN_[g.group], g.weight) for g in body.data.vertices[vi].groups if g.weight > 0 and GN_.get(g.group) in arm.pose.bones] for vi in FV}
FREST_N = {vi: (body.matrix_world.to_3x3() @ body.data.vertices[vi].normal).normalized() for vi in FV}
FREST_A = {i: body.data.polygons[i].area for i in FF}


def foot_metrics():
    V, N, F = eval_mesh()
    AW = arm.matrix_world; rot = {}; NE = {}
    for vi, ws in FVW.items():
        acc = Vector((0, 0, 0)); tot = 0.0
        for nm, w in ws:
            if nm not in rot:
                rot[nm] = (AW @ arm.pose.bones[nm].matrix @ B[nm].matrix_local.inverted() @ AW.inverted()).to_3x3()
            acc += (rot[nm] @ FREST_N[vi]) * w; tot += w
        NE[vi] = acc.normalized() if tot > 0 else FREST_N[vi]
    tall = BVHTree.FromPolygons(V, F)
    ins = {vi for vi in FV if inside(tall, V[vi] + NE[vi] * 2e-4)}
    fs = [F[i] for i in FF]
    efs = [f for f in fs if not any(k in ins for k in f)]
    te = BVHTree.FromPolygons(V, efs) if efs else None
    deep = 0.0
    for vi in ins:
        h = te.find_nearest(V[vi], 0.03) if te else (None,)
        if h[0] is not None:
            deep = max(deep, h[3])
    fold = sq = 0
    for i, f in zip(FF, fs):
        a, b, c = V[f[0]], V[f[1]], V[f[2]]
        fn = (b - a).cross(c - a)
        if fn.length > 1e-12 and fn.dot(sum((NE[k] for k in f), Vector((0, 0, 0)))) < 0:
            fold += 1
        ar = sum(((V[f[k]] - V[f[0]]).cross(V[f[k + 1]] - V[f[0]]).length for k in range(1, len(f) - 1))) / 2
        if FREST_A[i] > 1e-12 and ar / FREST_A[i] < 0.3:
            sq += 1
    return dict(buried=len(ins), deepest_mm=round(deep * 1000, 2), fold=fold, squash=sq, faces=len(FF))


def foot_rot(R, ang_foot=0.0, ang_toe=0.0):
    """腳踝往上翹（ang_foot 負）／往下壓（正）、腳趾往上翹（ang_toe 負）：繞世界 X 軸轉（腳朝 −Y）"""
    R = dict(R)
    qf = mr.Quaternion((1, 0, 0), math.radians(ang_foot)); qt = mr.Quaternion((1, 0, 0), math.radians(ang_toe))
    for s in "LR":
        R[f"J_Bip_{s}_Foot"] = qf @ R[f"J_Bip_{s}_Foot"]
        R[f"J_Bip_{s}_ToeBase"] = qt @ qf @ R[f"J_Bip_{s}_ToeBase"]
    return R


fpose = {}
for nm, af, at in (("rest", 0, 0), ("ankle_up30", -30, 0), ("ankle_down50", 50, 0), ("toes_up70", 0, -70), ("toes_up40", 0, -40)):
    pose(foot_rot(R0, af, at)); fpose[nm] = foot_metrics()
    if DIAG:
        print("FOOT", nm, fpose[nm])
pose(R0)
_V = [body.matrix_world @ v.co for v in body.data.vertices]
an_ = B["J_Bip_L_Foot"].head_local; toe_ = B["J_Bip_L_ToeBase"].head_local
fp_ = [_V[i] for i in FV if _V[i].z < max(0.07, an_.z)]
heel = [p.z for p in fp_ if p.y > an_.y]
ball = [p.z for p in fp_ if toe_.y - 0.01 < p.y < toe_.y + 0.015]
_ay0, _ay1 = toe_.y + 0.25 * (an_.y - toe_.y), toe_.y + 0.75 * (an_.y - toe_.y)        # 足弓＝腳趾關節和腳踝之間的中段、內側
_mx = min([p.x for p in fp_ if _ay0 < p.y < _ay1 and p.z < 0.03] or [an_.x])
_mw = max([p.x for p in fp_ if _ay0 < p.y < _ay1 and p.z < 0.03] or [an_.x]) - _mx
arch = [p.z for p in fp_ if p.x < _mx + 0.2 * _mw and _ay0 < p.y < _ay1 and p.z < 0.02]   # 內側邊兩成寬的那條（只量左腳，內側＝x 小）
sole = dict(heel_min_mm=round(min(heel) * 1000, 2) if heel else None, ball_min_mm=round(min(ball) * 1000, 2) if ball else None,
            lowest_mm=round(min(p.z for p in fp_) * 1000, 2) if fp_ else None, arch_mm=round(min(arch) * 1000, 2) if arch else None)
sole["ok"] = bool(heel and ball and arch) and sole["heel_min_mm"] <= 2 and sole["ball_min_mm"] <= 2 and sole["lowest_mm"] >= -1 and sole["arch_mm"] >= 3
w_at = lambda y0, dy: [p.x for p in fp_ if abs(p.y - y0) < dy and p.z < 0.04]
_hy = max(p.y for p in fp_) if fp_ else 0.0
bw = w_at(toe_.y + 0.004, 0.004); hw = w_at(an_.y + 0.5 * (_hy - an_.y), 0.004)          # 腳掌（腳趾關節）、腳跟（腳踝到腳跟中間）
shoe = dict(length_mm=round((max(p.y for p in fp_) - min(p.y for p in fp_)) * 1000, 1) if fp_ else None,
            ball_width_mm=round((max(bw) - min(bw)) * 1000, 1) if bw else None, heel_width_mm=round((max(hw) - min(hw)) * 1000, 1) if hw else None,
            instep_mm=round(max([p.z for p in fp_ if abs(p.y - (toe_.y + 0.6 * (an_.y - toe_.y))) < 0.004 and p.z < an_.z] or [0]) * 1000, 1))
res["feet"] = dict(pass_=True, value=dict(poses=fpose, sole=sole, shoe=shoe, template=bool(_fa),
                                          note="參考、不擋出廠：埋住點數／最深（mm）／翻面／壓扁在轉腳踝、翹腳趾時；sole.ok＝腳跟、前腳掌離地 ≤ 2 mm、沒有低於地面 1 mm、足弓 ≥ 3 mm；shoe＝鞋子尺寸"))

# weights（2026-10-14，references/research-limb-deformation.md 第 4 節；scripts/weight_audit.py）：
#   跨指、越節＝0；每點 ≤ 4 根、總和 1；「動一根看鄰居」（轉一根手指／大腿／上臂，量不該跟著動的點）≤ 0.3 mm
#   參考不擋：左右（離正中線 4 cm 外吃到另一側）、遠骨頭、碎權重（連續清理一定會留一些 < 0.01 的）
import importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import weight_audit
importlib.reload(weight_audit)
_wa = weight_audit.audit(body, arm)
pose(R0)
res["weights"] = dict(pass_=_wa["G1_cross_finger"] == 0 and _wa["G2_skip_joint"] == 0 and _wa["G4_over4"] == 0 and _wa["G5_sum_off"] == 0
                      and all(v <= 0.3 for v in _wa["G7_drag_mm"].values()), value=_wa)

# wrist（2026-10-14，research-limb-deformation.md 1.8；scripts/twist_probe.py）：手掌繞前臂扭 80°、150° 前臂最細截面積比 ≥ 0.90、0.78；
#   只彎手腕（往掌心 70°、往手背 60°、側彎）時扭轉骨轉角 ≤ 2°；開門片（手腕扭 105°）照動畫端做法烘焙成關鍵影格後再量，約束照樣生效（≥ 0.85）
_tp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "twist_probe.py")
_ns = {"__name__": "twist_probe_embed", "TWIST_EMBED": True}
exec(compile(open(_tp, encoding="utf-8").read(), _tp, "exec"), _ns)
_tw = _ns["res"]
pose(R0)
_bake = _tw.get("BAKE_open_door", {})
_w4 = max([d for v in _tw["W4_twist_bones_when_bending_deg"].values() for d in v] or [0.0])
res["wrist"] = dict(pass_=bool(_tw["twist_bones"]) and (_tw["W1_twist_min_area"][80] or 0) >= 0.90 and (_tw["W1_twist_min_area"][150] or 0) >= 0.78
                    and _w4 <= 2.0 and (_bake.get("forearm_min_area") or 0) >= 0.85,
                    value=dict(twist_bones=_tw["twist_bones"], twist_min_area=_tw["W1_twist_min_area"], bend_wrist_area=_tw["W3_bend_wrist_area"],
                               twist_bones_when_bending_max_deg=_w4, flex60_twist90=_tw["W5_flex60_twist90"], open_door=_tw["W8_mixamo"].get("open_door"),
                               baked_open_door=_bake))

# limbs（2026-10-14，research-limb-deformation.md 第 3、5、6 節；scripts/limb_probe.py）：參考、不擋出廠（門檻等使用者看過再定）
#   ROM：手肘、膝、肩、髖、腳踝、腳趾逐角度（截面積比、摺進去深度、不同部位互穿、翻面）；MIX：Mixamo 跪姿、蹲、坐、喝東西、弓步最彎那格；
#   STANCE：靜止兩腿間距、併腳要內收幾度、待機片左右腿互穿；SPREAD：手指張開、併攏、只張一根、捏食指尖／小指尖
if ARGV.get("LIMBS", "1") == "1":
    _lp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "limb_probe.py")
    _ln = {"__name__": "limb_probe_embed", "LIMB_EMBED": True}
    exec(compile(open(_lp, encoding="utf-8").read(), _lp, "exec"), _ln)
    pose(R0)
    _lr = _ln["res"]
    _rom = {k: {str(r["deg"]): {kk: r.get(kk) for kk in ("area", "crease_mm", "cross_mm", "fold")} for r in v} for k, v in _lr.get("rom", {}).items()}
    res["limbs"] = dict(pass_=True, value=dict(rom=_rom, mixamo=_lr.get("mix"), stance=_lr.get("stance"), spread=_lr.get("spread"),
                                               note="參考：一般變形在手肘、膝蓋彎超過約 75° 會塌（90° 截面約 0.7）；跪、蹲、坐時手放在腿上的穿插歸動畫端（接觸對位）"))

# 指紋（資訊，不擋）：手、腳的點座標（0.01 mm）＋權重（0.001）雜湊；同樣參數做兩次要一樣，改腳不該動到手的指紋
import hashlib
def fingerprint(sel):
    h = hashlib.sha256(); n = 0
    for v in body.data.vertices:
        if sel(v.co):
            n += 1
            h.update(("%.5f,%.5f,%.5f;" % tuple(v.co)).encode())
            for g in sorted(v.groups, key=lambda g: g.group):
                if g.weight > 1e-4:
                    h.update(("%s:%.3f;" % (body.vertex_groups[g.group].name, g.weight)).encode())
    return dict(verts=n, sha=h.hexdigest()[:16])
wx = B["J_Bip_L_Hand"].head_local.x - 0.004
ank = B["J_Bip_L_Foot"].head_local.z + 0.01
res["fingerprint"] = dict(pass_=True, value=dict(hand_L=fingerprint(lambda c: c.x > wx), hand_R=fingerprint(lambda c: c.x < -wx),
                                                 foot_L=fingerprint(lambda c: c.z < ank and c.x > 0), foot_R=fingerprint(lambda c: c.z < ank and c.x < 0),
                                                 note="資訊用，不擋出廠"))

# neck_ring（2026-10-14 整合進出廠檢查；scripts/ring_check.py，接口環合約見 zepeto-face-rig/references/research-head-body-seam.md 5.4）：
#   頭有接口環時擋：頭環和身體最上圈的距離（靜止、轉頭 35°、低頭／抬頭 25°、張嘴）≤ 0.1 mm、法線差 ≤ 1°、張嘴時環動 ≤ 0.1 mm。
#   舊頭（沒有 neck_ring_ver）不檢，脖子接口看 neck_probe 近照。放最後：ring_check 會擺姿勢、關表情驅動器、張嘴
_hd = O.get("Head")
if _hd is not None and "neck_ring_ver" in _hd.keys():
    _rp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ring_check.py")
    _rn = {"__name__": "ring_check_embed"}
    exec(compile(open(_rp, encoding="utf-8").read(), _rp, "exec"), _rn)
    _rc = dict(_rn["res"], ring=True)
    _gap = max(_rc[k] for k in ("rest_gap_mm", "turn35_gap_mm", "down25_gap_mm", "up25_gap_mm", "jawopen_gap_mm"))
    res["neck_ring"] = dict(pass_=_gap <= 0.1 and _rc["normal_diff_max_deg"] <= 1.0 and _rc["jawopen_ring_move_mm"] <= 0.1, value=_rc)
else:
    res["neck_ring"] = dict(pass_=True, value=dict(ring=False, note="頭沒有接口環（舊頭），不檢；脖子接口看 neck_probe 近照"))

out = {k: {"pass": v["pass_"], "value": v["value"]} for k, v in res.items()}
json.dump(out, open(ARGV.get("OUT", os.path.join(DIR, "checks.json")), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("CHECKS", json.dumps({k: (v["pass"], {kk: vv for kk, vv in v["value"].items() if kk != "detail"}) for k, v in out.items()}, ensure_ascii=False))
