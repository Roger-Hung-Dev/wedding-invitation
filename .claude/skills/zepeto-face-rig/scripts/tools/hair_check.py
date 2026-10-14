# 頭髮網格體檢（開 head_rig.blend 或接好身體的 body.blend；不存檔）：
#   1. 碎塊：頭髮斷成幾塊、小塊（< 60 點）在哪（AI 的細髮絲碎片會沿脖子排成一條虛線）
#   2. 開口邊：只連一個面的邊串成幾圈、各在哪（分辨「頭髮真的有破口」還是「被身體頂穿」）
#   3. 插進身體（檔裡有 Body 時）：頭髮的點、和頭髮每個面的中心，在身體裡面的各幾個、在哪、多深
#      ——只查點不夠：頭髮的三角形大、肩膀凸，三個角都在外面、面的中間會被身體頂穿（2026-10-14 新娘）
# 用法：blender -b <檔> -P hair_check.py
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from collections import defaultdict
O = bpy.data.objects
hair = O["Hair"]; me = hair.data
P = np.array([hair.matrix_world @ v.co for v in me.vertices])
n = len(P)
par = list(range(n))


def f(x):
    while par[x] != x:
        par[x] = par[par[x]]; x = par[x]
    return x


for e in me.edges:
    a, b = f(e.vertices[0]), f(e.vertices[1])
    if a != b:
        par[a] = b
isl = defaultdict(list)
for i in range(n):
    isl[f(i)].append(i)
sizes = sorted(((len(v), k) for k, v in isl.items()), reverse=True)
small = [(s, k) for s, k in sizes if s < 60]
print("[hair] %d 點、%d 塊；最大幾塊 %s；小於 60 點的 %d 塊" % (n, len(isl), [s for s, _ in sizes[:5]], len(small)))
for s, k in small[:20]:
    Q = P[isl[k]]
    print("[hair]   碎塊 %3d 點 z %.3f～%.3f x %.3f y %.3f" % (s, Q[:, 2].min(), Q[:, 2].max(), Q[:, 0].mean(), Q[:, 1].mean()))
cnt = defaultdict(int)
for p in me.polygons:
    for ek in p.edge_keys:
        cnt[ek] += 1
adj = defaultdict(list)
for (a, b), c in cnt.items():
    if c == 1:
        adj[a].append(b); adj[b].append(a)
seen = set(); loops = []
for v0 in adj:
    if v0 in seen:
        continue
    comp = []; st = [v0]
    while st:
        x = st.pop()
        if x in seen:
            continue
        seen.add(x); comp.append(x); st += adj[x]
    loops.append(comp)
print("[hair] 開口邊 %d 圈（最大幾圈）" % len(loops))
for c in sorted(loops, key=len, reverse=True)[:8]:
    Q = P[c]
    print("[hair]   %4d 點  x %.2f～%.2f  y %.2f～%.2f  z %.2f～%.2f" % (len(c), Q[:, 0].min(), Q[:, 0].max(), Q[:, 1].min(), Q[:, 1].max(), Q[:, 2].min(), Q[:, 2].max()))
body = O.get("Body")
if body:
    dg = bpy.context.evaluated_depsgraph_get()
    be = body.evaluated_get(dg); bm_ = be.to_mesh()
    bvh = BVHTree.FromPolygons([be.matrix_world @ v.co for v in bm_.vertices], [p.vertices[:] for p in bm_.polygons])
    he = hair.evaluated_get(dg); hm = he.to_mesh()
    HP = [he.matrix_world @ v.co for v in hm.vertices]

    def inside(p):
        loc, nn, _, d = bvh.find_nearest(p, 0.2)
        return d if loc is not None and (p - loc).dot(nn) < -0.0005 else None
    iv = [(p, inside(p)) for p in HP]
    iv = [(p, d) for p, d in iv if d is not None]
    fc = [sum((HP[i] for i in poly.vertices), Vector()) / len(poly.vertices) for poly in hm.polygons]
    ifc = [(p, inside(p)) for p in fc]
    ifc = [(p, d) for p, d in ifc if d is not None]
    print("[hair] 插進身體：點 %d、面中心 %d" % (len(iv), len(ifc)))
    for p, d in sorted(iv + ifc, key=lambda x: -x[1])[:10]:
        print("[hair]   (%.3f, %.3f, %.3f) 深 %.1f mm" % (p.x, p.y, p.z, d * 1000))
