# 量測工具：用平面切網格，取得截面輪廓。
import bpy, bmesh, math
from mathutils import Vector


def section(ob, mats_keep, co, no, region=None):
    """在 ob（rest 座標）上，只留材質名稱含 mats_keep 任一字串的面，沿平面 (co, no) 切出截面點"""
    bm = bmesh.new(); bm.from_mesh(ob.data)
    names = [s.material.name for s in ob.material_slots]
    keep = {i for i, n in enumerate(names) if any(k in n for k in mats_keep)}
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index not in keep], context="FACES")
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6, plane_co=co, plane_no=no)
    pts = [v.co.copy() for v in res["geom_cut"] if isinstance(v, bmesh.types.BMVert)]
    bm.free()
    if region:
        pts = [p for p in pts if region(p)]
    return pts


def ext(pts):
    if not pts:
        return None
    return dict(n=len(pts), x0=min(p.x for p in pts), x1=max(p.x for p in pts), y0=min(p.y for p in pts),
                y1=max(p.y for p in pts), z0=min(p.z for p in pts), z1=max(p.z for p in pts))


def fmt(e):
    return "none" if not e else " ".join(f"{k}={v:.3f}" if isinstance(v, float) else f"{k}={v}" for k, v in e.items())
