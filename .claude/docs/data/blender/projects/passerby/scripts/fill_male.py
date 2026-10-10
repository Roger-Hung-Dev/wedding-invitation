# passerby 專案的補皮膚設定（男性基底 M00）：use("body_fill") 之後再 use("fill_male")，然後 run_fill_male()。
#
# 沿用 groom 專案的 fill_male.py（數值不變）。理由：2026-10-06 實量這個角色的皮膚截面（新娘座標，除以 S=1.0763），
# 腰腹 z 0.98～1.08 的半寬、前緣、後緣和新郎的 SECTIONS 差都在 2 mm 內（兩人都是 VRoid 男性預設身體，只差身高），
# 便服同樣是 VRoid 短袖 T 恤（袖口到 x≈0.29）。所以斜方肌、鎖骨下移、上臂放大倍率、收進 T 恤內側 5 mm 的做法照用；
# T 恤若和新郎的略有差異，clamp_under() 依這件 T 恤實際的網格把補丁收進去，不靠寫死的數字。
# 原始說明（新郎）：
#   body_fill 的截面、斜方肌、鎖骨都是照新娘量的。男性和新娘差在兩處：
#   1. 腰背比較厚：腰後 y≈0.055（新娘 0.025）。照預設做背後會差 2.7 cm，超過吸附距離而留下階梯。
#   2. 肩線比較低（脖子比較長）：照預設做，斜方肌和鎖骨比 VRoid T 恤高出 2～2.5 cm，
#      穿 T 恤時肩膀上方露出一整條皮膚（像露肩上衣）。
#   所以：SECTIONS z 0.98～1.11 照既有皮膚截面；1.14～1.31 參考 T 恤截面往內縮 5 mm 以上；1.31 以上照脖子根部皮膚；
#   斜方肌、鎖骨管往下移約 3 cm、上臂往肩膀的放大倍率降低；
#   clamp_under()：補丁在 T 恤底下的頂點，一律收到 T 恤內側 gap（位移量沿網格平滑，接縫附近不動）。
# 數值都是新娘座標（乘 S＝頭骨高/1.386）。
import bpy, bmesh, math
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

SECTIONS = [
    (0.98, 0.112, -0.095, 0.058), (1.02, 0.104, -0.095, 0.052), (1.05, 0.101, -0.096, 0.050),
    (1.08, 0.104, -0.096, 0.054), (1.11, 0.108, -0.095, 0.058), (1.14, 0.114, -0.094, 0.064),
    (1.17, 0.120, -0.090, 0.070), (1.20, 0.124, -0.083, 0.076), (1.23, 0.124, -0.065, 0.079),
    (1.26, 0.116, -0.048, 0.079), (1.29, 0.095, -0.031, 0.076), (1.31, 0.075, -0.020, 0.072),
    (1.33, 0.052, -0.010, 0.068), (1.36, 0.040, 0.008, 0.066), (1.39, 0.046, 0.022, 0.072),
]
ARM_GROW = [(0.30, 1.0, 0.0), (0.27, 1.0, 0.0), (0.24, 1.01, 0.0), (0.21, 1.03, 0.0), (0.18, 1.06, 0.0),
            (0.15, 1.08, -0.001), (0.125, 1.08, -0.002), (0.105, 1.05, -0.003)]
TRAP = ((0.030, 0.034, 1.310), (0.130, 0.024, 1.270), 0.022, 0.020)      # 斜方肌：起點、終點、半徑
CLAV = ((0.018, -0.040, 1.266), (0.125, 0.000, 1.274), 0.010, 0.013)     # 鎖骨


def build_blocks(name="FillBlocks"):
    if name in O:
        bpy.data.objects.remove(O[name], do_unlink=True)
    bm = bmesh.new()
    _loft(bm, SECTIONS)
    for sx in (1, -1):
        _arm_loft(bm, sx)
        for (p0, p1, r0, r1) in (TRAP, CLAV):
            _tube(bm, V(p0[0] * sx, p0[1], p0[2]), V(p1[0] * sx, p1[1], p1[2]), r0 * S, r1 * S)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob


def clamp_under(ob, cloth_names=("Tee",), gap=0.005, edge=0.012, iters=25):
    """ob 的頂點若在衣服底下卻離衣服內側不到 gap（或跑到外面），往衣服內推到 gap。
    衣服邊緣（領口、袖口、下襬）edge 以內的權重漸減；接縫（離既有皮膚 8 mm 內）不動；位移向量沿網格平滑 iters 次。"""
    gap, edge = gap * S, edge * S
    cloths = [O[f"{WHO}_{n}"] for n in cloth_names if f"{WHO}_{n}" in O]
    data = []
    for c in cloths:
        me = c.data
        bvh = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
        ec = {}
        for p in me.polygons:
            for e in p.edge_keys:
                ec[e] = ec.get(e, 0) + 1
        bnd = sorted({i for e, n in ec.items() if n == 1 for i in e})
        kd = KDTree(max(1, len(bnd)))
        for k, i in enumerate(bnd):
            kd.insert(me.vertices[i].co, k)
        kd.balance()
        data.append((bvh, kd))
    skin = skin_bvh(O[f"{WHO}_Body"])
    me = ob.data; n = len(me.vertices)
    disp = [Vector() for _ in range(n)]; fixed = [False] * n
    for v in me.vertices:
        if skin.find_nearest(v.co)[3] < 0.008 * S:
            fixed[v.index] = True; continue
        for bvh, kd in data:
            loc, nrm, idx, d = bvh.find_nearest(v.co)
            if loc is None or d > 0.06 * S:
                continue
            sd = (v.co - loc).dot(nrm)
            if sd + gap <= 0:
                continue
            db = kd.find(loc)[2]
            w = max(0.0, min(1.0, db / edge)); w = w * w * (3 - 2 * w)
            dv = -nrm * (sd + gap) * w
            if dv.length > disp[v.index].length:
                disp[v.index] = dv
    nb = [[] for _ in range(n)]
    for e in me.edges:
        a, b = e.vertices; nb[a].append(b); nb[b].append(a)
    raw = [d.copy() for d in disp]
    for _ in range(iters):                      # 平滑位移：取鄰居平均，但不能比自己原本需要的少（不然又戳出去）
        new = []
        for i in range(n):
            if fixed[i] or not nb[i]:
                new.append(disp[i]); continue
            avg = sum((disp[j] for j in nb[i]), Vector()) / len(nb[i])
            new.append(avg if avg.length >= raw[i].length else raw[i])
        disp = new
    moved = 0
    for v in me.vertices:
        if disp[v.index].length > 1e-5:
            v.co += disp[v.index]; moved += 1
    me.update()
    return moved


def run_fill_male():
    """run_fill() ＋ 收進 T 恤底下"""
    r = run_fill()
    r["clamped"] = clamp_under(O[f"{WHO}_BodyFill"])
    return r
