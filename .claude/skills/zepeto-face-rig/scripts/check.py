# AI 網格路線 ⑦ 自動檢查（數字）：每個代表表情量四件事，寫 metrics.json。全部 0 才算過。
#   1. teeth_front：牙齒、牙齦、舌頭跑到嘴唇（AI 皮）前面的點數（吐舌頭時舌頭不算）
#   2. pocket_out：口腔袋（第 3 圈以後）穿出臉皮的點數
#   3. holes／backface（含唇緣從外面看到背面）：從嘴巴正面、兩側斜面射一片線（嘴巴附近 0.5×0.36 的範圍），
#      被臉圍住卻什麼都沒打到＝破洞；打到 AI 皮的背面＝從縫裡看到臉皮裡面
#   4. lip_back_bind：嘴唇表面綁到模板「朝嘴裡」三角形的點數（轉移時存的 bind_ny；不是 0 張大嘴會凹凸）
#   「在不在皮前面」：跟附近（xz 平面 0.025 內）皮膚最前面的 y 比（射線在唇縫正上會穿過縫，量不準）
# 用法：blender -b face.blend -P check.py -- <landmarks.json> <輸出 metrics.json>
import bpy, sys, os, json
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

a = sys.argv[sys.argv.index("--") + 1:]
LM = json.load(open(a[0], encoding="utf-8")); OUT = a[1]
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "expr_list.py"), encoding="utf-8").read())
sc = bpy.context.scene
ai = bpy.data.objects["AI_Driven"]
PARTS = [o for o in bpy.data.objects if o.name in ("upper_teeth", "bottom_teeth", "upper_gum", "bottom_gum", "Tongue")]
shp = [o for o in bpy.data.objects if o.type == 'MESH' and o.data.shape_keys]
pt = np.array([d.value for d in ai.data.attributes["pocket_t"].data])
POCKET_ANY = np.zeros(len(pt), bool)
side = np.array([d.value for d in ai.data.attributes["lip_side"].data])
# 口腔袋（含唇緣）的點：從材質與 pocket_t 判斷；唇緣用皮膚材質、pocket_t＝0 → 用面的材質找口腔，唇緣靠「lip_side 有值、在嘴唇後面」不好判，
#   改用轉移時的 WALL 規則：口腔袋所有點在轉移時都有 lip_side（跟原唇縫點同側）且 pocket_t≥0 → 這裡只把 pocket_t>0 當口腔袋，唇緣算皮
POCK = pt > 0
PK = np.array([d.value for d in ai.data.attributes["pocket_k"].data]) if "pocket_k" in ai.data.attributes else (pt > 0).astype(int)
FACE_SKIN = np.array([all(PK[v] == 0 for v in p_.vertices) for p_ in ai.data.polygons])  # 純皮膚的面（唇緣、口腔袋不算）
RIM_FACE = np.array([max(PK[v] for v in p_.vertices) <= 2 and not FACE_SKIN[i] for i, p_ in enumerate(ai.data.polygons)])  # 唇緣（第 1、2 圈）的面
li = [i for i, m in enumerate(ai.data.materials) if m and m.name.startswith("LipInner")]
mc = np.array(LM["mouth"]["center"])
bny = np.array([d.value for d in ai.data.attributes["bind_ny"].data]) if "bind_ny" in ai.data.attributes else None


def set_expr(vals):
    for o in shp:
        for kb in o.data.shape_keys.key_blocks[1:]:
            if kb.name == "jawOpen_smile_corr":
                kb.value = min(vals.get("jawOpen", 0), (vals.get("mouthSmileLeft", 0) + vals.get("mouthSmileRight", 0)) / 2)
            else:
                kb.value = vals.get(kb.name, 0.0)
    bpy.context.view_layer.update()


def world_verts(o, dg):
    ev = o.evaluated_get(dg); me = ev.to_mesh()
    P = np.array([o.matrix_world @ v.co for v in me.vertices]); ev.to_mesh_clear()
    return P


def front_kd(P, mask):
    idx = np.where(mask)[0]
    kd = KDTree(len(idx))
    for j, i in enumerate(idx):
        kd.insert(Vector((P[i, 0], 0.0, P[i, 2])), int(i))
    kd.balance()
    return kd


def n_in_front(Q, P, kd, marg=0.002, r=0.025):
    n = 0
    for q in Q:
        hits = kd.find_range(Vector((q[0], 0.0, q[2])), r)
        if hits and q[1] < min(P[h[1], 1] for h in hits) - marg:
            n += 1
    return n


VIEWS = {"front": Vector((0, -0.75, 0.02)), "34": Vector((0.33, -0.68, 0.04)), "34R": Vector((-0.33, -0.68, 0.04))}


def ray_test(dg, nx=90, nz=64):
    """嘴巴附近射一片線：回傳 (破洞數, 看到皮背面數)"""
    res = {}
    for vn, off in VIEWS.items():
        org = Vector(mc) + off
        tgt = Vector(mc)
        fwd = (tgt - org).normalized(); right = fwd.cross(Vector((0, 0, 1))).normalized(); up = right.cross(fwd)
        grid = np.zeros((nz, nx), np.int8)  # 0 空、1 皮正面、2 皮背面、3 口腔袋／嘴內
        for iz in range(nz):
            for ix in range(nx):
                p = tgt + right * ((ix / (nx - 1) - 0.5) * 0.5) + up * ((iz / (nz - 1) - 0.5) * 0.36)
                d = (p - org).normalized()
                hit, loc, nor, fi, ob, _ = sc.ray_cast(dg, org, d)
                if not hit:
                    grid[iz, ix] = 0
                elif ob == ai:
                    m = ob.data.materials[ob.data.polygons[fi].material_index] if fi < len(ob.data.polygons) else None
                    if not FACE_SKIN[fi]:
                        rim_ = RIM_FACE[fi] and nor.dot(d) > 0
                        grid[iz, ix] = 6 if rim_ else 3  # 唇緣、口腔袋；唇緣從外面看到背面＝唇緣跑到嘴唇前面（6）
                    else:
                        grid[iz, ix] = 2 if nor.dot(d) > 0 else 1
                else:
                    grid[iz, ix] = 3
        # 空的格子：從邊界連得到的是臉外背景，連不到的才是破洞
        empty = grid == 0
        seen = np.zeros_like(empty)
        st = [(z, x) for z in range(nz) for x in (0, nx - 1) if empty[z, x]] + [(z, x) for x in range(nx) for z in (0, nz - 1) if empty[z, x]]
        for z, x in st: seen[z, x] = True
        while st:
            z, x = st.pop()
            for dz, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                zz, xx = z + dz, x + dx
                if 0 <= zz < nz and 0 <= xx < nx and empty[zz, xx] and not seen[zz, xx]:
                    seen[zz, xx] = True; st.append((zz, xx))
        # 嘴裡的格子（口腔袋、牙齒、舌頭）：最大一塊＝嘴巴開口；其他不相連、3 格以上的塊＝從臉皮穿出來的
        inner = (grid == 3) | (grid == 6)
        lab = np.zeros(inner.shape, np.int32); sizes = []
        for z0 in range(nz):
            for x0 in range(nx):
                if inner[z0, x0] and not lab[z0, x0]:
                    n_ = len(sizes) + 1; st2 = [(z0, x0)]; lab[z0, x0] = n_; c_ = 0
                    while st2:
                        z, x = st2.pop(); c_ += 1
                        for dz, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            zz, xx = z + dz, x + dx
                            if 0 <= zz < nz and 0 <= xx < nx and inner[zz, xx] and not lab[zz, xx]:
                                lab[zz, xx] = n_; st2.append((zz, xx))
                    sizes.append(c_)
        # 「嘴巴開口」＝最大一塊，或重心落在唇縫帶（上下 0.05、左右嘴寬 1.2 倍內）的塊（微開時唇縫是斷斷續續的細線）
        hw_ = abs(LM["mouth"]["L"][0] - LM["mouth"]["R"][0]) / 2
        biggest = int(np.argmax(sizes)) + 1 if sizes else -1
        def dil(m, r):
            o = m.copy()
            for dz in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    o |= np.roll(np.roll(m, dz, 0), dx, 1)
            return o
        near_open = dil(lab == biggest, 4) if sizes else np.zeros_like(inner)
        stray_lab = set()
        for n_ in range(1, len(sizes) + 1):
            if n_ == biggest or sizes[n_ - 1] < 3:
                continue
            if (near_open & (lab == n_)).any():
                continue  # 貼著開口（4 格內）：開口末端被細皮膚隔開的碎塊（攝影師驚訝時嘴角兩端），不是穿出
            zz_, xx_ = np.nonzero(lab == n_)
            ox = (xx_.mean() / (nx - 1) - 0.5) * 0.5; oz = (zz_.mean() / (nz - 1) - 0.5) * 0.36
            if not (abs(oz) < 0.05 and abs(ox) < 1.2 * hw_):
                stray_lab.add(n_)
        stray = int(sum(sizes[n_ - 1] for n_ in stray_lab))
        # 皮背面：只算被臉圍住的（5×5 範圍內沒有背景）；臉輪廓外那些是臉旁薄髮絲的背面
        nearbg = np.zeros_like(empty)
        for dz in range(-2, 3):
            for dx in range(-2, 3):
                nearbg |= np.roll(np.roll(empty, dz, 0), dx, 1)
        # 而且只算嘴巴附近（左右 1.5 個嘴寬、上下 0.12）：張大嘴時下顎邊緣的薄髮絲（長髮不跟臉動）會露出背面，跟口腔無關
        OX = (np.arange(nx) / (nx - 1) - 0.5) * 0.5; OZ = (np.arange(nz) / (nz - 1) - 0.5) * 0.36
        zone = (np.abs(OZ)[:, None] < 0.12) & (np.abs(OX)[None, :] < 1.5 * hw_)
        near_inner = dil(inner, 3)  # 貼著嘴裡的背面＝唇內側捲進去（塗成口腔色，看起來就是開口邊）
        back_in = int(((grid == 2) & ~nearbg & zone & ~near_inner).sum())
        if back_in < 3:
            back_in = 0  # 1～2 格是射線擦過嘴唇與口腔交界的薄邊（每格約 0.006，放大近拍看不到）；看得到的問題會連成一片
        rim_back = int((grid == 6).sum())
        back_in += rim_back if rim_back >= 3 else 0
        res[vn] = (int((empty & ~seen).sum()), back_in, stray)
        if os.environ.get("CHECK_DBG"):  # 除錯：射線結果存成 .npy（0 空、1 皮正面、2 皮背面、3 嘴內、4 穿出、5 破洞、6 唇緣背面）；Blender 沒有 PIL
            g = grid.copy()
            for n_ in stray_lab:
                g[lab == n_] = 4
            g[empty & ~seen] = 5
            np.save(os.path.join(os.environ["CHECK_DBG"], "%s_%s.npy" % (CUR, vn)), g)
    return res


# 0. 檔案打開時的狀態：所有形態鍵都要是 0（沒接骨頭的表情存成 1 的話，一打開就全開、臉扭成一團；
#    下面量表情時每次都把所有值重設，所以只看表情抓不到這種問題）
rest_on = {o.name: [k.name for k in o.data.shape_keys.key_blocks[1:] if abs(k.value) > 1e-4] for o in shp}
rest_on = {k: v for k, v in rest_on.items() if v}
n_rest = sum(len(v) for v in rest_on.values())
print("[check] 打開檔案時非 0 的形態鍵 %d 個%s" % (n_rest, "：%s" % {k: v[:5] for k, v in rest_on.items()} if n_rest else ""))
out = {"expressions": {}, "rest_nonzero": n_rest}
dg = bpy.context.evaluated_depsgraph_get()
for name, vals in EXPR:
    if any(k.startswith("LOOK") for k in vals):
        continue  # 只改材質，形狀跟原樣一樣
    CUR = name
    set_expr(vals)
    dg = bpy.context.evaluated_depsgraph_get()
    A = world_verts(ai, dg)
    skin = (A[:, 1] < -0.2) & ~POCK
    kd = front_kd(A, skin)
    tf = 0
    for o in PARTS:
        if o.name == "Tongue" and vals.get("tongueOut", 0) > 0:
            continue
        tf += n_in_front(world_verts(o, dg), A, kd)
    po = n_in_front(A[POCK & (pt > 0.15)], A, kd, marg=0.004)
    rt = ray_test(dg)
    holes = sum(v[0] for v in rt.values()); back = sum(v[1] for v in rt.values()); poke = sum(v[2] for v in rt.values())
    out["expressions"][name] = dict(teeth_front=tf, pocket_out=po, poke=poke, holes=holes, backface=back, rays={k: list(v) for k, v in rt.items()})
    print("[check] %-9s 牙齒舌頭在唇前 %3d、口腔袋穿出 點 %3d／畫面 %3d、破洞 %3d、看到皮背面 %3d" % (name, tf, po, poke, holes, back))
if bny is not None:
    lip = (side > 0) & (PK == 0)
    out["lip_back_bind"] = int(((bny > 0.2) & lip & (np.abs(np.array([v.co.z for v in ai.data.vertices]) - mc[2]) < 0.09)).sum())
    print("[check] 嘴唇綁到模板內面 %d 點" % out["lip_back_bind"])
tot = sum(v["teeth_front"] + v["pocket_out"] + v["poke"] + v["holes"] + v["backface"] for v in out["expressions"].values()) + out.get("lip_back_bind", 0)
tot += n_rest
out["total_issues"] = tot
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("[check] 合計問題 %d → %s" % (tot, "通過" if tot == 0 else "要看"))
