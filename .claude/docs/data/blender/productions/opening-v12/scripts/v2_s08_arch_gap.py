# ⑧ 新郎揮手的手離拱門（G_Arch、G_ArchFlowers）多近（2026-10-09 wave_arc）：每格量右手（手掌＋手指頂點）到拱門網格的最近距離
#   "$BL" -b couple.blend -P prod_cli.py -- --run v2_s08_arch_gap RATE=24
import bpy, math
from mathutils.bvhtree import BVHTree
MODE = "setup"
use("run_prod")
use("shots_v2_s0308")
S_ = SHOTS["v2_08"]; S_["build"](); stage(S_["set"], cast=True)
GA = GR["ARM"]; dg = bpy.context.evaluated_depsgraph_get()
trees = []
for nm in ("G_Arch", "G_ArchFlowers"):
    o = bpy.data.objects.get(nm)
    if o is not None and o.type == "MESH":
        trees.append((nm, BVHTree.FromObject(o, dg, deform=True)))
    elif o is not None:
        for ch in o.children_recursive:
            if ch.type == "MESH":
                trees.append((ch.name, BVHTree.FromObject(ch, dg, deform=True)))
print("ARCH_OBJS", [n for n, _ in trees][:12], len(trees), flush=True)
body = bpy.data.objects[GR["WHO"] + "_Body"]
gi = {g.index for g in body.vertex_groups if g.name.startswith("J_Bip_R_") and any(k in g.name for k in ("Hand", "Thumb", "Index", "Middle", "Ring", "Little"))}
idx = [v.index for v in body.data.vertices if any(e.group in gi and e.weight > 0.3 for e in v.groups)]
mesh_eval(True, GA.name)
best = (9, None, None)
for i in range(int(3.1 * 24) + 1):
    t = 6.4 + i / 24
    S_["frame"](t, props=False, cam=False); bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg); me = ev.to_mesh(); M = body.matrix_world
    pts = [M @ me.vertices[j].co for j in idx[::3]]; ev.to_mesh_clear()
    for nm, tr in trees:
        for p in pts:
            r = tr.find_nearest(p)
            if r[0] is not None and r[3] < best[0]:
                best = (r[3], t, nm)
    if i % 12 == 0:
        print("GAP_SO_FAR", round(t, 2), round(best[0] * 100, 1), "cm", best[1], best[2], flush=True)
print("ARCH_GAP_MIN_CM", round(best[0] * 100, 2), "at", best[1], best[2], flush=True)
