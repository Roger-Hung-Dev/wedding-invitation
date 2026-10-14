# 嘴唇變形的數字診斷（要轉移時存的 bind_* 屬性）
# 用法：AI_LM=<landmarks.json> blender -b xfer.blend -P diag_bind.py
import bpy, numpy as np, json
ai = bpy.data.objects["AI_Driven"]; me = ai.data; kb = me.shape_keys.key_blocks
B = np.array([k.co[:] for k in kb["Basis"].data]); J = np.array([k.co[:] for k in kb["jawOpen"].data])
D = J - B
side = np.array([d.value for d in me.attributes["lip_side"].data])
bd = np.array([d.value for d in me.attributes["bind_dist"].data])
bny = np.array([d.value for d in me.attributes["bind_ny"].data])
btri = np.array([d.value for d in me.attributes["bind_tri"].data])
li = [i for i, m in enumerate(me.materials) if m and m.name == "LipInner"]
wall = np.zeros(len(B), bool)
for p in me.polygons:
    if p.material_index in li: wall[list(p.vertices)] = True
E = np.array([e.vertices[:] for e in me.edges])
LM = json.load(open(__import__("os").environ["AI_LM"], encoding="utf-8"))
mc = np.array(LM["mouth"]["center"])
lip = (np.abs(B[:, 0] - mc[0]) < 0.17) & (np.abs(B[:, 2] - mc[2]) < 0.09) & (B[:, 1] < -0.4) & ~wall
lo = lip & (side == 2); up = lip & (side == 1)
print("[diag] 嘴唇點 %d（上 %d、下 %d）、內壁點 %d" % (lip.sum(), up.sum(), lo.sum(), wall.sum()))
# 1. 綁定距離與朝向
for nm, m in (("上唇", up), ("下唇", lo)):
    print("[diag] %s 綁定距離：中位 %.3f、最大 %.3f；綁到朝後（口腔內面）的三角形 %d / %d 點" % (nm, np.median(bd[m]), bd[m].max(), int((bny[m] > 0.2).sum()), m.sum()))
# 2. 相鄰兩點綁到朝向相反的三角形（一個朝前、一個朝後）
em = lip[E[:, 0]] & lip[E[:, 1]]
flip = em & (np.sign(bny[E[:, 0]] + 1e-9) != np.sign(bny[E[:, 1]] + 1e-9)) & (np.abs(bny[E[:, 0]] - bny[E[:, 1]]) > 0.6)
print("[diag] 相鄰兩點綁到「一前一後」三角形的邊：%d / %d" % (flip.sum(), em.sum()))
# 3. 位移場的不平順（每點位移和鄰居平均的差）：張嘴量 a 時，凹凸 ∝ a
acc = np.zeros_like(D); deg = np.zeros(len(D))
np.add.at(acc, E[:, 0], D[E[:, 1]]); np.add.at(acc, E[:, 1], D[E[:, 0]]); np.add.at(deg, E[:, 0], 1); np.add.at(deg, E[:, 1], 1)
rough = np.linalg.norm(D - acc / np.maximum(deg, 1)[:, None], axis=1)
mag = np.linalg.norm(D, axis=1)
for nm, m in (("上唇", up), ("下唇", lo)):
    print("[diag] %s 張嘴 1.0：位移中位 %.3f；跟鄰居差（凹凸）中位 %.4f、最大 %.4f" % (nm, np.median(mag[m]), np.median(rough[m]), rough[m].max()))
for a in (0.3, 0.6, 1.0):
    print("[diag]   張嘴 %.1f → 下唇凹凸最大 %.4f（AI 嘴唇厚約 0.04）" % (a, a * rough[lo].max()))
# 4. 綁定距離 vs 位移：同一個模板三角形的點，離得越遠位移應該越不同（下顎是轉動），現在卻完全一樣
same = {}
for i in np.where(lo)[0]:
    same.setdefault(btri[i], []).append(i)
grp = [g for g in same.values() if len(g) >= 4]
spread_d = [np.ptp(bd[g]) for g in grp]; spread_D = [np.ptp(np.linalg.norm(D[g] - D[g].mean(0), axis=1)) for g in grp]
print("[diag] 下唇：%d 組點綁到同一個模板三角形；組內離模板距離差中位 %.3f，但位移幾乎一樣（差中位 %.4f）" % (len(grp), np.median(spread_d), np.median(spread_D)))
# 5. 內壁：張嘴時內壁點和它前緣唇縫點的位移差 → 內壁被扭成斜片
lw = wall & (side == 2); uw = wall & (side == 1)
print("[diag] 內壁 上 %d 下 %d 點；內壁位移 中位 %.3f vs 下唇 %.3f" % (uw.sum(), lw.sum(), np.median(mag[lw]), np.median(mag[lo])))
from mathutils.kdtree import KDTree
kd = KDTree(int(lo.sum())); idx_lo = np.where(lo)[0]
for j, i in enumerate(idx_lo): kd.insert(B[i], j)
kd.balance()
dd = [np.linalg.norm(D[i] - D[idx_lo[kd.find(B[i])[1]]]) for i in np.where(lw)[0]]
print("[diag] 下唇內壁點 vs 最近的下唇點：位移差 中位 %.3f、最大 %.3f（內壁只有 0.07 深）" % (np.median(dd), np.max(dd)))
import bmesh
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
top = np.where(lip)[0][np.argsort(-rough[lip])][:8]
for i in top:
    v = bm.verts[int(i)]
    print("[top] v%d 位置 %s 凹凸 %.4f 側別 %d 邊界點 %s 鄰居 %d 綁距 %.3f" % (i, np.round(B[i], 3), rough[i], side[i], v.is_boundary, len(v.link_edges), bd[i]))
