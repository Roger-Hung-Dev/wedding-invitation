# Head 脖子截面分析（開 pack.blend／ring.blend／head_rig.blend；只在記憶體切、不存檔）：
#   1. 某一個高度切開：截面串成幾段、閉不閉合（閉合＝那一圈都有皮）、範圍；擬合橢圓（x 對稱）
#   2. 一段高度範圍，每 0.02 一層：每側「開口邊界點」的角度（缺口邊在哪、同一層有好幾個＝鋸齒）
#   3. 後頸墊底皮（nape_underlay 屬性）每一層：後面的半徑（應該平順，不要忽大忽小）、哪些點墊在臉皮下（u）哪些在缺口（.）
#   角度：從脖子中心看，0＝正後（+Y）、+90＝角色左（+X）、±180＝正前
# 用法：blender -b <檔> -P neck_section.py -- <切的高度> [<層的起點> <層的終點>]
#   例：-- -0.28 -0.28 0.06
import bpy, bmesh, sys, math
import numpy as np
a = sys.argv[sys.argv.index("--") + 1:]
Z = float(a[0])
Z0, Z1 = (float(a[1]), float(a[2])) if len(a) > 2 else (None, None)
h = bpy.data.objects["Head"]
base = bmesh.new(); base.from_mesh(h.data); base.transform(h.matrix_world)


def pieces(bm_, z, faces=None):
    geom = (bm_.verts[:] + bm_.edges[:] + bm_.faces[:]) if faces is None else \
        list({v for f in faces for v in f.verts}) + list({e for f in faces for e in f.edges}) + faces
    res = bmesh.ops.bisect_plane(bm_, geom=geom, plane_co=(0, 0, z), plane_no=(0, 0, 1), dist=1e-5)
    ce = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    adj = {}
    for e in ce:
        x, y = e.verts
        adj.setdefault(x, []).append(y); adj.setdefault(y, []).append(x)
    seen = set(); out = []
    for v in adj:
        if v in seen:
            continue
        comp = []; st = [v]
        while st:
            q = st.pop()
            if q in seen:
                continue
            seen.add(q); comp.append(q); st += adj[q]
        out.append((comp, sum(1 for q in comp if len(adj[q]) == 1)))
    return out


b1 = base.copy()
ps = pieces(b1, Z)
YC = 0.0
if ps:
    big = max(ps, key=lambda p: len(p[0]))
    Pb = np.array([v.co[:2] for v in big[0]])
    M = np.c_[Pb[:, 0] ** 2, Pb[:, 1] ** 2, Pb[:, 1]]
    A_, B_, C_ = np.linalg.lstsq(M, np.ones(len(Pb)), rcond=None)[0]
    if A_ > 0 and B_ > 0:
        YC = -C_ / (2 * B_); k = 1 + B_ * YC * YC
        print("[sec] z %.3f 擬合橢圓：中心 y %.4f、半寬 %.4f、半厚 %.4f" % (Z, YC, math.sqrt(k / A_), math.sqrt(k / B_)) if k > 0 else "[sec] 擬合失敗")
    else:
        YC = float((Pb[:, 1].max() + Pb[:, 1].min()) / 2)
        print("[sec] z %.3f 擬合不出橢圓（截面不像脖子），中心用範圍中點 y %.4f" % (Z, YC))
for comp, ends in sorted(ps, key=lambda p: -len(p[0])):
    Q = np.array([v.co[:] for v in comp])
    print("[sec]   一段 %d 點、%s；x %.3f～%.3f、y %.3f～%.3f" % (len(comp), "閉合" if ends == 0 else "開口 %d 端" % ends, Q[:, 0].min(), Q[:, 0].max(), Q[:, 1].min(), Q[:, 1].max()))
b1.free()
if Z0 is not None:
    print("[sec] 每層開口邊界點的角度（只切中心往前 0.35 以後的面，避開臉和嘴）")
    z = Z0
    while z <= Z1 + 1e-6:
        b2 = base.copy()
        faces = [f for f in b2.faces if f.calc_center_median().y > YC - 0.35]
        pieces(b2, z, faces)
        L, R = [], []
        for v in b2.verts:
            if abs(v.co.z - z) < 2e-5 and v.is_boundary and v.co.y > YC - 0.35:
                t = math.degrees(math.atan2(v.co.x, v.co.y - YC))
                (L if v.co.x > 0 else R).append(round(t))
        print("[sec]   z %+.3f  左 %s  右 %s" % (z, sorted(L, reverse=True), sorted(R)))
        b2.free(); z += 0.02
ua = h.data.attributes.get("nape_underlay")
if ua:
    yc = h.get("neck_ring_yc", YC)
    rows = {}
    for v in h.data.vertices:
        kk = ua.data[v.index].value
        if kk:
            w = h.matrix_world @ v.co
            rows.setdefault(round(w.z, 3), []).append((math.degrees(math.atan2(w.x, w.y - yc)), math.hypot(w.x, w.y - yc), kk))
    print("[sec] 後頸墊底皮 %d 層（u＝墊在臉皮下、.＝缺口）" % len(rows))
    for z in sorted(rows):
        R_ = sorted(rows[z], key=lambda x: -x[0])
        back = min(R_, key=lambda x: abs(x[0]))
        print("[sec]   z %+.3f 正後半徑 %.3f  %s" % (z, back[1], "".join("u" if q == 1 else "." for _, _, q in R_)))
