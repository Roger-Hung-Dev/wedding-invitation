# 頭的共用量法（Blender 裡 import）：接口環高度、頭寬、H、環那層的橢圓。
#   neck_ring.py、neck_slim.py、zepeto_ratio.py 都從這裡拿，量法只有一份（改了三支一起變）。
import numpy as np
from mathutils import Vector


def measure_cut(hd):
    """接口環的高度：從身體端 body_build.py measure_head 的切口規則改來（2026-10-14）。
    回傳 (下巴高度, 環的高度, 下巴底)：正中線（|x| < 0.05）每 2 cm 一格的最前面 y；下巴＝比嘴巴最前面退後 0.06 的那格（內插）；
    下巴底＝從嘴巴往下第一次「一格就往後退 > 0.06」的地方（下巴底面轉進脖子）；
    環＝下巴底往下 0.03 以下（量不到下巴底時：下巴往下 0.06 以下）第一個「往後退不到 0.035」的格子。
    改「從下巴底往下找」的原因：V 字臉的下巴比嘴唇後縮很多（攝影師 v2），「比嘴唇退後 0.06」量到的是下巴前緣（−0.35），
    舊規則把環放在 −0.44＝還在下巴上（下巴底 −0.51）；新娘兩種規則都是 −0.28。身體端讀頭檔的 neck_ring_z，不用跟著改"""
    me, mw = hd.data, hd.matrix_world
    lips = next((i for i, m in enumerate(me.materials) if m and m.name.startswith("ZEPETO_Lips")), None)
    pts = [mw @ me.vertices[v].co for p in me.polygons if p.material_index == lips for v in p.vertices]
    c = sum(pts, Vector()) / len(pts)
    mouth = Vector((c.x, min(p.y for p in pts), c.z))
    BIN = 0.02
    front = {}
    for v in me.vertices:
        w = mw @ v.co
        if abs(w.x) < 0.05 and w.y < 0:
            k_ = round(w.z / BIN)
            front[k_] = min(front.get(k_, 9.0), w.y)
    mk = round(mouth.z / BIN)
    f0 = min(front[k_] for k_ in front if mk - 2 <= k_ <= mk + 1)
    ks = sorted((k_ for k_ in front if k_ < mk), reverse=True)
    chin = None
    for a_, b_, c_ in zip(ks, ks[1:], ks[2:]):
        ra, rb, rc = front[a_] - f0, front[b_] - f0, front[c_] - f0
        if ra < 0.06 <= rb and rc >= 0.06:
            chin = (a_ + (b_ - a_) * (0.06 - ra) / (rb - ra)) * BIN; break
    if chin is None:
        raise SystemExit("[measure] 量不到下巴（正中線剖面跟預期不同）")
    top = max((mw @ Vector(cc)).z for cc in hd.bound_box)
    zmin = min((mw @ Vector(cc)).z for cc in hd.bound_box)
    cb = None
    for a_, b_ in zip(ks, ks[1:]):
        if b_ == a_ - 1 and front[b_] - front[a_] > 0.06:
            cb = (a_ + b_) / 2 * BIN; break
    below = sorted((k_ for k_ in front if k_ * BIN <= (cb - 0.03 if cb is not None else chin - 0.06)), reverse=True)
    cut = None
    for a_, b_ in zip(below, below[1:]):
        if front[b_] - front[a_] < 0.035:
            cut = b_ * BIN; break
    if cut is None:
        cut = chin - 0.084 * (top - chin)
    return chin, max(cut, zmin + 0.01), cb


def section_xy(o, z):
    """o 在高度 z 水平切一刀的截面點（世界座標的 x, y）：網格三角形大，用「高度 ±幾 mm 內的點」會量少（新娘 0.29 vs 實際 0.40）"""
    import bmesh
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, z), plane_no=(0, 0, 1), dist=1e-5)
    P = np.array([v.co[:2] for v in bm.verts if abs(v.co.z - z) < 2e-5])
    bm.free()
    return P


EYE_FROM_CHIN = 0.40  # ZEPETO 眼睛在下巴往上 40%（research-zepeto-face.md）：AI 頭頂被頭髮蓋住，H 用眼睛推


def head_H(chin, eye_z):
    """H＝頭頂（不含頭髮）到下巴，用眼睛高度推"""
    return (eye_z - chin) / EYE_FROM_CHIN


def head_width(co, chin, H):
    """頭寬：Head 的點（不含頭髮、耳朵）下巴往上 0.3H 以上，每 1 cm 一層的左右寬取最大 → (寬, 那層高度)"""
    zs = np.arange(chin + 0.3 * H, co[:, 2].max(), 0.01)
    layers = [(float(np.ptp(co[(co[:, 2] >= z) & (co[:, 2] < z + 0.01)][:, 0])), float(z)) for z in zs
              if ((co[:, 2] >= z) & (co[:, 2] < z + 0.01)).sum() > 10]
    return max(layers) if layers else (None, None)


def fit_ellipse(P):
    """x 對稱的橢圓 x²/rx² + (y−yc)²/ry² = 1：解 A x² + B y² + C y = 1 → (yc, rx, ry)；擬合不出回 None"""
    M = np.c_[P[:, 0] ** 2, P[:, 1] ** 2, P[:, 1]]
    A, B, C = np.linalg.lstsq(M, np.ones(len(P)), rcond=None)[0]
    if A <= 0 or B <= 0:
        return None
    yc = -C / (2 * B)
    k = 1 + B * yc * yc
    if k <= 0:
        return None
    return yc, (k / A) ** 0.5, (k / B) ** 0.5
