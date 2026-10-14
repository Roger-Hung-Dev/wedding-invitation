# AI 網格路線：長髮避開身體（厚頭髮版）。從舊路線的 hair_body_fit.py 改來（舊路線已封存：D:/render-work/archive/zepeto-face-rig-old-route-20261014）。
#   AI 生成的長髮是一整塊很厚的鐘形（新娘：1007 點插進肩膀）。做法（2026-10-14，使用者看過側面後定）：
#   - 往後的頭髮「壓縮」：每一束（x 每 0.04）每個高度（z 每 0.03），前緣推到身體背面後方、後緣盡量不動、中間照比例
#     ＝ 前面那層疊到後面那層上，像真實長髮披到背後
#   - 前緣退多少：從支點（下巴 + HF_PIVOT，預設 0.2）直線斜坡到碰到身體的那一格 → 側面看是一條從耳後斜到背上的線
#   - 臉旁細髮絲（pack_head.py 標的 strand）往前避開：本來就垂在肩膀前面
#   - 頭髮跟臉、耳朵相接的那一圈（只算下巴以上）不動，往外 6 圈漸變：不然接縫裂開
#   試過的失敗做法見「壓縮」那段註解；舊路線的坑（法線推出圓包、外推張成翅膀）見 references/cage-pipeline.md 附錄
# 用法：blender -b head_rig.blend --python hair_fit.py -- <身體 .blend> <landmarks.json>
import bpy, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

_a = sys.argv[sys.argv.index("--") + 1:]
body_path = _a[0]
import json as _json
CHIN = _json.load(open(_a[1], encoding="utf-8"))["chin_z"]
MARGIN = 0.03      # 頭髮內層離身體表面至少這麼遠（頭檔單位；新娘 ×0.243 ≈ 0.7 cm）

hair = bpy.data.objects["Hair"]
if hair.get("hairfit_done"):  # 推過一次再跑會推兩次：要重跑就從 rig 步驟開始（rig.blend 重產）
    raise SystemExit("[hairfit] 這個檔已經跑過長髮避開身體了：從 rig 步驟重跑（--steps rig,hairfit,finish）")
thick = sum(abs(m.thickness) for m in hair.modifiers if m.type == 'SOLIDIFY')


IDS = ("objects", "meshes", "armatures", "materials", "images", "node_groups", "actions", "collections", "textures")
_before = {c: set(getattr(bpy.data, c)) for c in IDS}


def drop_body_data():
    """把身體檔帶進來的東西全刪掉（材質、貼圖、零件網格…）；沒刪的會跟著存進頭檔，檔案多 3 MB"""
    for c in IDS:
        coll = getattr(bpy.data, c)
        for d in [d for d in coll if d not in _before[c]]:
            coll.remove(d)


IDLE_FBX = r"D:\render-work\mixamo\raw\female_idle.fbx"   # 待機姿勢（手臂放下）：身體端 neck_probe.py 拍近照也用這個第一格


def body_collider(idle=False):
    with bpy.data.libraries.load(body_path) as (src, dst):
        dst.objects = ["Body", "Body_Armature", "Face_Rig", "Hair"]
    body, arm, rig_b, hair_b = dst.objects
    for o in (body, arm, rig_b, hair_b):  # 都放進場景才會照骨架父子關係重算 matrix_world（沒放進去會是單位矩陣）
        bpy.context.scene.collection.objects.link(o)
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = (1, 0, 0, 0)
    if idle:  # 擺成待機姿勢（手臂放下）：頭髮固定在頭上，所以換算後就是「待機時身體相對於頭在哪」
        import sys as _sys
        _sys.path.insert(0, r"D:\SideProject\wedding-invitation\.claude\skills\blender-motion-library\scripts")
        import mixamo_retarget as _mr
        _tg = _mr.Target(arm)
        _clip = _mr.retarget(_mr.read_fbx(IDLE_FBX), _tg)
        _h0 = _clip["hips"][0].copy(); _h0.x = _h0.y = 0
        _mr.apply_pose(arm, _tg, dict(_clip["R"][0]), _h0)
    bpy.context.view_layer.update()
    # 同一份頭髮在兩邊的 world：頭檔座標 = Mh @ Mb⁻¹ @ 身體座標
    if hair_b is None or rig_b is None:
        raise SystemExit("[hairfit] 身體檔沒有 Face_Rig／Hair，換算不了座標")
    T = hair.matrix_world @ hair_b.matrix_world.inverted()
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    V = [T @ (body.matrix_world @ v.co) for v in me.vertices]
    F = [tuple(p.vertices) for p in me.polygons]
    if idle and len(me.vertices) == len(body.data.vertices):
        # 待機姿勢只拿上臂：整個身體都拿的話，待機動作的頭和上身角度跟 T 字不同、整片後背相對於頭往後移，
        #   新娘第一輪 842 點「在身體裡」、推了 0.28（7 cm），髮型往後張、背面頭髮摺到翻面
        gi = {g.index: g.name for g in body.vertex_groups}
        arm_v = set()
        for v in body.data.vertices:
            if v.groups:
                g = max(v.groups, key=lambda g_: g_.weight)
                if gi.get(g.group, "").endswith("_UpperArm"):
                    arm_v.add(v.index)
        F = [f for f in F if sum(i in arm_v for i in f) * 2 > len(f)]
        print("[hairfit] 待機姿勢的障礙只用上臂：%d 面" % len(F))
    ev.to_mesh_clear()
    for o in (hair_b, rig_b, body, arm):
        bpy.data.objects.remove(o)
    return BVHTree.FromPolygons(V, F), max(v.z for v in V), np.array([v[:] for v in V])


# 身體只用 T 字：手臂放下後的上臂和頭髮碰撞交給動畫端（試過把手臂放下也當障礙，頭髮會整束包住上臂）
cols_z = [body_collider()]
drop_body_data()
# 待機姿勢（手臂放下）的身體當收尾的障礙：預設關（環境變數 HF_IDLE=1 才開，留著做實驗）。
#   起因：身體端 neck_probe 用待機姿勢拍，新娘背面頭髮上一小塊膚色＝左上臂從頭髮後面頂出來。
#   2026-10-14 試過：整個身體 → 842 點在身體裡、推 0.28（7 cm）：待機動作的頭和上身角度跟 T 字不同，整片後背相對頭往後移；
#   只用上臂 → 還是 709 點、推 0.28：手臂放下時上臂整段在長髮裡。兩種都讓背面頭髮摺到翻面、腋下的頭髮變亂。
#   → 長髮垂在上臂外面是結構問題（頭髮固定在頭上、不會跟手臂動），交給動畫端（頭髮骨頭或物理）
import os as _os2
col_idle = None
if _os2.environ.get("HF_IDLE") != "1":
    pass
elif _os2.path.exists(IDLE_FBX):
    try:
        col_idle = body_collider(idle=True)[0]
    except Exception as _e:
        print("[hairfit] 待機姿勢的身體做不出來，收尾只看 T 字：%s" % _e)
    drop_body_data()
else:
    print("[hairfit] 找不到待機動作 %s，收尾只看 T 字" % IDLE_FBX)
cols = [c[0] for c in cols_z]
BV = cols_z[0][2]
me = hair.data
N = len(me.vertices)
Mw = hair.matrix_world
P0 = np.array([Mw @ v.co for v in me.vertices])
EDG = np.array([e.vertices[:] for e in me.edges])
DEG = np.zeros(N)
np.add.at(DEG, EDG[:, 0], 1)
np.add.at(DEG, EDG[:, 1], 1)
DEG = np.maximum(DEG, 1)
# 只動脖子以下：身體最高點（脖子切口）往上一點點開始漸變
z_top = max(c[1] for c in cols_z)  # 身體最高點＝脖子切口
print("[hairfit] 身體最高點（頭檔座標）z=%.3f" % z_top)
import os as _os
Z0 = float(_os.environ.get("HF_Z0", -0.02))     # 從下巴往上（+）／往下（−）多少開始動
RAMP = float(_os.environ.get("HF_RAMP", 0.15))  # 往下多長漸變到全量：越長，往後彎得越緩（側面看頭髮在肩膀高度折一下＝太短）
w_free = np.clip((CHIN + Z0 - P0[:, 2]) / RAMP, 0, 1)
w_free = w_free * w_free * (3 - 2 * w_free)
# 頭髮和臉、耳朵相接的那一圈不動（往外 6 圈漸變）：切開成兩個物件後接縫的點各一份，頭髮這邊動了就裂開
_seam = set()
# 後頸墊底皮（neck_ring.py，2026-10-14）範圍裡的接縫不固定：底下有皮，頭髮整束往後退也不會露出洞。
#   以前固定在臉上的那段頭髮被拉長、留在脖子側面變成黑色鋸齒，細髮絲也被拉住插進身體（新娘 17 點）
_hd = bpy.data.objects.get("Head")
_PT = _hd.get("nape_patch_top") if _hd else None
_PA = tuple(_hd.get("nape_patch_ang")) if _hd and _hd.get("nape_patch_ang") is not None else None
_YC = _hd.get("neck_ring_yc", 0.0) if _hd else 0.0


def _in_patch(p):
    if _PT is None or _PA is None or p[2] > _PT:
        return False
    import math as _m
    t = _m.degrees(_m.atan2(p[0], p[1] - _YC))
    return _PA[1] <= t <= _PA[0]


for _on in ("Head", "Ears"):
    _o = bpy.data.objects.get(_on)
    if _o is None:
        continue
    from mathutils.kdtree import KDTree as _KD
    _q = [_o.matrix_world @ v.co for v in _o.data.vertices]
    _kd = _KD(len(_q))
    for _j, _c in enumerate(_q): _kd.insert(_c, _j)
    _kd.balance()
    for _i, _p in enumerate(P0):
        if _kd.find(Vector(_p))[2] < 1e-5 and _p[2] > CHIN - 0.05:  # 只固定下巴以上：脖子那段接縫在身體裡面（身體端會藏掉臉的脖子），固定住就卡在身體裡
            if _on == "Head" and _in_patch(_p):
                continue
            _seam.add(_i)
_ring = np.full(len(P0), 99)
_ring[list(_seam)] = 0
_fr = list(_seam)
_adj = [[] for _ in range(len(P0))]
for _e in hair.data.edges:
    _a, _b = _e.vertices; _adj[_a].append(_b); _adj[_b].append(_a)
for _d in range(1, 7):
    _nx = []
    for _v in _fr:
        for _u in _adj[_v]:
            if _ring[_u] > _d:
                _ring[_u] = _d; _nx.append(_u)
    _fr = _nx
w_seam = np.clip(_ring / 6.0, 0, 1)
w_free = w_free * w_seam
print("[hairfit] 從下巴 %+.2f 開始、%.2f 漸變；跟臉相接 %d 點不動%s" % (Z0, RAMP, len(_seam),
      "（後頸墊底皮 z ≤ %.3f、%.0f°～%.0f° 裡的接縫不固定）" % (_PT, _PA[0], _PA[1]) if _PT is not None else ""))
need = MARGIN + thick


def violations(P):
    D = np.zeros_like(P)
    bad = np.zeros(len(P), bool)
    for c in cols:
        for i in np.where(P[:, 2] < z_top + 0.2)[0]:
            loc, n, _, d = c.find_nearest(Vector(P[i]), 1.0)
            if loc is None:
                continue
            s = (Vector(P[i]) - loc).dot(n)
            if s < need:
                push = np.array(n) * (need - s)
                if np.linalg.norm(push) > np.linalg.norm(D[i]):
                    D[i] = push
                bad[i] = True
    return D, bad


def report(P, tag):
    _, bad = violations(P)
    inside = 0
    for c in cols:
        for i in np.where(P[:, 2] < z_top + 0.2)[0]:
            loc, n, _, _ = c.find_nearest(Vector(P[i]), 1.0)
            if loc is not None and (Vector(P[i]) - loc).dot(n) < 0:
                inside += 1
    print(f"[hairfit] {tag}：插進身體 {inside} 點、太貼（< {need:.3f}）{int(bad.sum())} 點")
    if "strand" in me.attributes and inside:  # 分開看：細髮絲／頭髮、在不在接縫附近
        _st = np.array([d.value for d in me.attributes["strand"].data]).astype(bool)
        ins = np.zeros(len(P), bool)
        for c in cols:
            for i in np.where(P[:, 2] < z_top + 0.2)[0]:
                loc, n, _, _ = c.find_nearest(Vector(P[i]), 1.0)
                if loc is not None and (Vector(P[i]) - loc).dot(n) < 0:
                    ins[i] = True
        _ws = globals().get("w_seam")
        print("[hairfit]   細髮絲 %d、頭髮 %d；其中接縫固定（w_seam<1）%s；高度 z %.2f～%.2f" % (
            int((ins & _st).sum()), int((ins & ~_st).sum()), int((ins & (_ws < 1)).sum()) if _ws is not None else "-",
            P[ins, 2].min(), P[ins, 2].max()))
    return inside, int(bad.sum())


report(P0, "修正前")
# 垂墜：頭髮從碰到肩膀那一點起，往下整段一起前移或後移（披在肩膀前面或後面自然垂下）。
#   試過的失敗做法：
#   - 沿身體法線推、再沿網格平滑：肩膀頂端把側面頭髮頂出一顆圓包（平滑 6～80 次都一樣）。
#   - 身體不含手臂：肩關節那圈開口附近判斷不出裡外，剩 200 點插在肩膀上，收尾沿法線推又變圓包。
#   - 水平往外推：兩側頭髮本來就垂在肩膀正上方，整段要外推 0.4 以上，張成翅膀。
yc = float(np.median(BV[(BV[:, 2] > z_top - 0.8) & (BV[:, 2] < z_top), 1]))  # 軀幹前後的中間
COL_W, MAX_OUT = 0.04, 0.6
BLEND = float(__import__("os").environ.get("HF_BLEND", 0.35))  # 接觸點以上多高內漸變  # 每 COL_W 寬一束；接觸點以上 BLEND 內漸變，不折角


def need_y(P, sgn):
    """每點要往 sgn（−1 前、+1 後）移多少才離身體 need：沿那個方向射線量到身體外緣"""
    out = np.zeros(len(P))
    d = Vector((0, sgn, 0))
    for i in np.where(P[:, 2] < z_top + 0.2)[0]:
        loc, n, _, _ = cols[0].find_nearest(Vector(P[i]), 1.0)
        if loc is None:
            continue
        s_ = (Vector(P[i]) - loc).dot(n)
        if s_ >= need:
            continue
        hit = cols[0].ray_cast(Vector(P[i]) + d * 3.0, -d, 3.0)  # 從那一側外面往回射，第一個碰到的就是外緣
        if hit[0] is None:
            continue
        out[i] = max(0.0, (hit[0].y - P[i][1]) * sgn + need)
    return np.minimum(out, MAX_OUT)


SIDE = np.ones(N)  # 頭髮全部往後：一整束前後兩面一起動（分前後的話厚頭髮會被拆開）
# 臉旁細髮絲（pack_head.py 標的 strand）往前：本來就垂在肩膀前面，往後推要穿過整個身體（試過：最多移 50 cm、240 點卡在身體裡）
if "strand" in me.attributes:
    _st = np.array([d.value for d in me.attributes["strand"].data]).astype(bool)
    SIDE[_st] = -1.0
    print("[hairfit] 臉旁細髮絲 %d 點往前避開" % int(_st.sum()))
COLK = np.round(P0[:, 0] / COL_W).astype(int) * 2 + (SIDE > 0)
D = np.zeros_like(P0)
# 壓縮（往後的頭髮）：每一束（x 每 0.04）每個高度（z 每 0.03），頭髮前緣推到身體背面後方 need，後緣盡量不動，中間照比例壓縮
#   ＝ 前面那層疊到後面那層上（真實長髮披到背後就是這樣，變薄而不是整片往後移）。
#   前緣要退多少 Δ(z)：每個碰到身體的格子給一條「從支點（下巴 + HF_PIVOT）直線斜坡到那一格」的量，取最大
#   → 側面看前緣是一條從耳後斜到背上的直線，再貼著背往下。左右各 6 束高斯帶動。
#   試過：
#   - 整束平移（前後兩面一起往後）：原本就在背後的那層被推得更遠，整片頭髮往後張成披風（新娘：往後 15 cm）
#   - 碰到身體處全量、往上 BLEND 內淡掉、疊 4 輪：彎折擠在肩膀那一小段，側面折成 V 字
PIVOT = CHIN + float(_os.environ.get("HF_PIVOT", 0.2))
ZB, MIN_T = 0.03, 0.03
back = SIDE > 0
cx_ = np.round(P0[:, 0] / COL_W).astype(int)
cz_ = np.floor(P0[:, 2] / ZB).astype(int)
cells = {}
for i in np.where(back & (P0[:, 2] < PIVOT))[0]:
    cells.setdefault((cx_[i], cz_[i]), []).append(i)
YF, YB, DL = {}, {}, {}
bvh_b = cols[0]
for (kx, kz), idx in cells.items():
    idx = np.array(idx)
    yf, yb = P0[idx, 1].min(), P0[idx, 1].max()
    YF[(kx, kz)], YB[(kx, kz)] = yf, yb
    x_, z_ = kx * COL_W, (kz + 0.5) * ZB
    hit = bvh_b.ray_cast(Vector((x_, 5.0, z_)), Vector((0, -1, 0)), 10.0)  # 從背後往前射：身體背面
    if hit[0] is None:
        continue
    d_ = hit[0].y + need - yf
    if d_ > 0:
        DL[(kx, kz)] = d_
# 前緣要退多少：斜坡（支點 → 那一格）取最大，左右高斯帶動
delta = {}
kxs = sorted({k[0] for k in cells})
for (kx, kz) in cells:
    z_ = (kz + 0.5) * ZB
    best = 0.0
    for (jx, jz), d_ in DL.items():
        if abs(jx - kx) > 6:
            continue
        zj = (jz + 0.5) * ZB
        f = np.clip((PIVOT - z_) / max(PIVOT - zj, 0.05), 0, 1)
        best = max(best, d_ * f * float(np.exp(-((jx - kx) / 3.0) ** 2)))
    delta[(kx, kz)] = best
n_c = 0
for (kx, kz), idx in cells.items():
    dl = delta.get((kx, kz), 0.0)
    if dl <= 0:
        continue
    yf, yb = YF[(kx, kz)], YB[(kx, kz)]
    tf = yf + dl
    tb = max(yb, tf + MIN_T)
    for i in idx:
        t = (P0[i, 1] - yf) / max(yb - yf, 1e-6)
        D[i, 1] = (tf + t * (tb - tf)) - P0[i, 1]
    n_c += 1
w_mv = w_seam * np.clip((PIVOT - P0[:, 2]) / 0.06, 0, 1)
D *= w_mv[:, None]
print("[hairfit] 壓縮 %d 格（支點 z=%.2f）" % (n_c, PIVOT))
# 細髮絲往前：照舊做法（每一點要往前多少，支點斜坡）
if (SIDE < 0).any():
    req = need_y(P0 + D, -1)
    fr_ = np.where(SIDE < 0)[0]
    for i in fr_:
        if req[i] > 0:
            D[i, 1] -= req[i]
# （不做舊做法的收尾「沿身體法線推」：肩膀頂端會頂出圓包）
# 移動量沿頭髮網格抹順 20 次（只動下巴以下）：一束一束的差異在背後會折出皺褶
for _ in range(20):
    acc = np.zeros_like(D)
    np.add.at(acc, EDG[:, 0], D[EDG[:, 1]]); np.add.at(acc, EDG[:, 1], D[EDG[:, 0]])
    D = D + (acc / DEG[:, None] - D) * (0.5 * w_mv)[:, None]
# 收尾：壓縮完還插在身體裡的往後頭髮點，各自沿 +Y 推到身體外緣＋need，推量往網格旁邊抹開（不留尖角），最多 3 輪。
#   壓縮是每束（x 每 0.04）從那一束的中線量身體背面；肩膀斜，束的外側背面比中線更後面 → 那幾點推不夠
#   （新娘 4.5 頭身身體：後背靠肩膀兩點插進 3～4 mm，背面看頭髮上一小塊膚色破洞）
def _push_req(p, cs):
    """p 在哪個身體裡面（或面中心）：從背後往前射到那個身體的背面，回傳要往後推多少（取最大）；都不在裡面回傳 0"""
    best = 0.0
    for c in cs:
        loc, n, _, _ = c.find_nearest(Vector(p), 1.0)
        if loc is None or (Vector(p) - loc).dot(n) >= 0:
            continue
        hit = c.ray_cast(Vector(p) + Vector((0, 3.0, 0)), Vector((0, -1, 0)), 3.0)
        if hit[0] is not None:
            best = max(best, hit[0].y - p[1] + need)
    return best


CS = [cols[0]] + ([col_idle] if col_idle is not None else [])
for _round in range(4):
    Pc = P0 + D
    req = np.zeros(N); n_v = n_f = 0
    for i in np.where((Pc[:, 2] < z_top + 0.2) & (SIDE > 0) & (w_mv > 0))[0]:
        r_ = _push_req(Pc[i], CS)
        if r_ > 0:
            req[i] = r_; n_v += 1
    # 面中心也要查：頭髮的三角形大、肩膀凸，三個角都在身體外面，面的中間卻被身體頂穿
    for poly in me.polygons:
        vs = list(poly.vertices)
        if not all(SIDE[v] > 0 and w_mv[v] > 0 for v in vs):
            continue
        c = Pc[vs].mean(0)
        if c[2] >= z_top + 0.2:
            continue
        r_ = _push_req(c, CS)
        if r_ > 0:
            n_f += 1
            for v in vs:
                req[v] = max(req[v], r_)
    if n_v == 0 and n_f == 0:
        break
    Rq = req.copy()
    for _ in range(8):  # 推量往旁邊擴散、逐圈減弱
        acc = np.zeros(N); cnt_ = np.zeros(N)
        np.add.at(acc, EDG[:, 0], Rq[EDG[:, 1]]); np.add.at(acc, EDG[:, 1], Rq[EDG[:, 0]])
        np.add.at(cnt_, EDG[:, 0], 1); np.add.at(cnt_, EDG[:, 1], 1)
        Rq = np.maximum(Rq, 0.75 * acc / np.maximum(cnt_, 1))
    D[:, 1] += Rq * (w_mv > 0) * (SIDE > 0)
    print("[hairfit] 收尾第 %d 輪（T 字%s）：%d 點、%d 個面中心還在身體裡，往後推最多 %.3f" % (
        _round + 1, "＋待機" if col_idle is not None else "", n_v, n_f, req.max()))
inside, close = report(P0 + D, "修正後")
mv = np.linalg.norm(D, axis=1)
print("[hairfit] 移動 %d 點、最多 %.3f（約 %.1f cm）" % ((mv > 1e-4).sum(), mv.max(), mv.max() * 0.243 * 100))
Inv = Mw.inverted().to_3x3()
DL = np.array([Inv @ Vector(d) for d in D])
if me.shape_keys:
    for kb in me.shape_keys.key_blocks:
        for i, v in enumerate(kb.data):
            v.co = v.co + Vector(DL[i])
else:
    for i, v in enumerate(me.vertices):
        v.co = v.co + Vector(DL[i])
me.update()


def skin_patch():
    """頭髮往後披，露出耳垂以下、下巴後面的臉皮：AI 頭在那裡畫的是頭髮的黑色（還有偏綠的色斑），
    轉印進 head_color.png 後原本被頭髮蓋住 → 身體端近照看到幾片黑色碎塊。把那一帶偏離膚色的貼圖改成膚色。
    改的是外部圖檔 head_color.png（身體檔也直接讀它）；重跑 materials 會重產，所以每次 hairfit 都重做一次。"""
    hd = bpy.data.objects["Head"]
    ears = bpy.data.objects.get("Ears")
    z_cut = min((ears.matrix_world @ v.co).z for v in ears.data.vertices) + 0.05 if ears else z_top + 0.4
    img = next(n.image for n in hd.material_slots[0].material.node_tree.nodes if n.type == 'TEX_IMAGE')
    SKIN_SLOTS = {i for i, s_ in enumerate(hd.material_slots) if s_.material and s_.material.name.startswith(("ZEPETO_Face", "ZEPETO_Skin"))} or {0}
    Wd, Ht = img.size
    px = np.array(img.pixels[:], np.float32).reshape(Ht, Wd, 4)
    hm = hd.data
    uv = hm.uv_layers.active.data
    HMw = hd.matrix_world
    mask = np.zeros((Ht, Wd), bool)
    yy, xx = np.mgrid[0:Ht, 0:Wd]
    for poly in hm.polygons:
        if poly.material_index not in SKIN_SLOTS or max((HMw @ hm.vertices[v].co).z for v in poly.vertices) > z_cut:
            continue
        T = [np.array(uv[li].uv) * (Wd, Ht) for li in poly.loop_indices]
        for k in range(1, len(T) - 1):  # 扇形切三角形、逐一塗進遮罩
            a, b, c = T[0], T[k], T[k + 1]
            x0, y0 = np.floor(np.minimum(np.minimum(a, b), c)).astype(int) - 1
            x1, y1 = np.ceil(np.maximum(np.maximum(a, b), c)).astype(int) + 2
            x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, Wd), min(y1, Ht)
            if x1 <= x0 or y1 <= y0:
                continue
            X, Y = xx[y0:y1, x0:x1] + 0.5, yy[y0:y1, x0:x1] + 0.5
            d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(d) < 1e-9:
                continue
            l1 = ((b[1] - c[1]) * (X - c[0]) + (c[0] - b[0]) * (Y - c[1])) / d
            l2 = ((c[1] - a[1]) * (X - c[0]) + (a[0] - c[0]) * (Y - c[1])) / d
            e_ = 1.5 / max(np.linalg.norm(b - a), np.linalg.norm(c - b), 1)  # 往外多塗一點，接縫不留黑邊
            mask[y0:y1, x0:x1] |= (l1 > -e_) & (l2 > -e_) & (1 - l1 - l2 > -e_)
    C = px[mask, :3]
    lum = C @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    ref = np.median(C[lum > np.percentile(lum, 40)], 0)  # 那一帶的膚色
    dist = np.linalg.norm(C - ref, axis=1)
    w = np.clip((dist - 0.06) / 0.1, 0, 1)[:, None]
    px[mask, :3] = C * (1 - w) + ref * w
    if not (w > 0.5).any():  # 已經改過：不重存（重存會換掉檔案，打包前出廠的身體檔直接讀這張）
        print("[hairfit] 耳垂以下的臉皮：已是膚色，head_color.png 不動")
        return
    img.pixels.foreach_set(px.ravel())
    img.save()
    print("[hairfit] 耳垂以下的臉皮：%d 個貼圖點改成膚色（膚色 %s）" % (int((w[:, 0] > 0.5).sum()), np.round(ref, 3)))


skin_patch()
hair["hairfit_done"] = 1
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
if inside:
    print("[hairfit] 警告：還有頭髮在身體裡面")
