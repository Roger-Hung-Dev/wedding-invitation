# 背景 Blender：樣張（已烤關鍵影格）逐格量禮服。
#   blender -b <sample>.blend -P gown_check.py -- <out.json> [step] BODY=groom,bride
#   1. 新郎（身體＋西裝）離裙子多近／穿進多深
#   2. 新娘手（手掌＋手指）穿進裙子多深
#   3. 裙子穿進場景物件多深（門框、牌子、柱子…；地板不算）
import bpy, sys, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]; STEP = int(argv[1]) if len(argv) > 1 and argv[1].isdigit() else 2
sc = bpy.context.scene
arms = [o for o in sc.objects if o.type == "ARMATURE" and o.name.startswith("Body_Armature")]
groom = next(a for a in arms if any(c.name.startswith("Suit_") for c in a.children))
def _wears(a, pre):
    return any(o.name.startswith(pre) for o in sc.objects if o.type == "MESH" and any(m.type == "ARMATURE" and m.object == a for m in o.modifiers))
bride = next((a for a in arms if a is not groom and _wears(a, "Gown_")), None) or next(a for a in arms if a is not groom)   # 照衣服認人（B4 起有第三個人）
kids = lambda a: [o for o in sc.objects if o.type == "MESH" and any(m.type == "ARMATURE" and m.object == a for m in o.modifiers)]
G_MESH = [o for o in kids(groom) if o.name.startswith(("Body", "Suit_Jacket", "Suit_Pants", "Suit_Shoes"))]
SKIRT = [o for o in kids(bride) if o.name.startswith(("Gown_Skirt", "Gown_Overskirt"))]
B_BODY = next(o for o in kids(bride) if o.name.startswith("Body"))
for m in B_BODY.modifiers:                                  # 衣服底下藏頂點的遮罩會讓頂點編號錯位 → 量手時關掉
    if m.type == "MASK":
        m.show_viewport = m.show_render = False
HAND_VG = {g.index for g in B_BODY.vertex_groups if any(k in g.name for k in ("_Hand", "Index", "Middle", "Ring", "Little", "Thumb"))}
HAND_IDS = [v.index for v in B_BODY.data.vertices if sum(g.weight for g in v.groups if g.group in HAND_VG) > 0.5]
SIDE = {v.index: ("L" if "_L_" in B_BODY.vertex_groups[max(v.groups, key=lambda g: g.weight).group].name else "R") for v in B_BODY.data.vertices if v.index in set(HAND_IDS)}
print("GOWN_CHECK", [o.name for o in SKIRT], len(HAND_IDS), [o.name for o in G_MESH])


def wv(o, dg, ids=None):
    oe = o.evaluated_get(dg); me = oe.to_mesh(); M = o.matrix_world
    V = [M @ me.vertices[i].co for i in ids] if ids is not None else [M @ v.co for v in me.vertices]
    F = [tuple(p.vertices) for p in me.polygons] if ids is None else None
    oe.to_mesh_clear()
    return V, F


def bvh_of(objs, dg):
    V, F = [], []
    for o in objs:
        v, f = wv(o, dg); k = len(V); V += v; F += [tuple(j + k for j in p) for p in f]
    return BVHTree.FromPolygons(V, F), V


def ray_in(b, p, c, far=0.12):
    """p 在裙子裡面多深：從新娘中心軸往外（水平）打一條線，打到裙面＝在裡面，距離就是深度（裙子上下開口，用法線判斷會誤判）"""
    d = p - c; d.z = 0
    if d.length < 1e-4:
        return far
    hit = b.ray_cast(p, d.normalized(), far)[0]
    return (hit - p).length if hit is not None else 0.0


def signed(b, p, far):
    loc, nrm, _i, d = b.find_nearest(p, far)
    if loc is None:
        return far
    return -d if (p - loc).dot(nrm) < 0 else d               # 負＝在裡面


# 場景靜態物件（含集合實例）：只留新娘走線 1.2 m 內、頂端高過 5 cm 的
def _chain(o):
    while o.parent:
        o = o.parent; yield o


def statics(dg):
    out = {}
    for o in sc.objects:
        if o.type != "MESH" and not (o.instance_type == "COLLECTION" and o.instance_collection):
            continue
        if o.hide_render or o in kids(groom) + kids(bride) or any(a in (groom, bride) for a in _chain(o)):
            continue
        parts = [(o, o.matrix_world)] if o.type == "MESH" else [(c, o.matrix_world @ c.matrix_world) for c in o.instance_collection.all_objects if c.type == "MESH"]
        V, F = [], []
        for c, M in parts:
            ce = c.evaluated_get(dg); me = ce.to_mesh(); k = len(V)
            V += [M @ v.co for v in me.vertices]; F += [tuple(j + k for j in p.vertices) for p in me.polygons]; ce.to_mesh_clear()
        if not V or max(v.z for v in V) < 0.05:
            continue
        out[o.name] = (V, F)
    return out


f0, f1 = sc.frame_start, sc.frame_end
hips = []
for f in range(f0, f1 + 1, 10):
    sc.frame_set(f); hips.append((bride.matrix_world @ bride.pose.bones["J_Bip_C_Hips"].head).to_2d())
dg = bpy.context.evaluated_depsgraph_get()
st = {}
for nm, (V, F) in statics(dg).items():
    lo = Vector((min(v.x for v in V), min(v.y for v in V))); hi = Vector((max(v.x for v in V), max(v.y for v in V)))
    if any(lo.x - 1.2 < h.x < hi.x + 1.2 and lo.y - 1.2 < h.y < hi.y + 1.2 for h in hips):
        st[nm] = BVHTree.FromPolygons([v for v in V], F)
MOVING = [nm for nm in st if bpy.data.objects[nm].animation_data and bpy.data.objects[nm].animation_data.action]
print("STATICS", list(st), "MOVING", MOVING)

GOWN = [o for o in kids(bride) if o.name.startswith(("Gown_Skirt", "Gown_Overskirt", "Gown_Sash", "Gown_Bodice"))]
_cache = {}
def _one(o):
    def f(dg):
        k = (o.name, sc.frame_current)
        if k not in _cache:
            _cache.clear(); _cache[k] = bvh_of([o], dg)[0]
        return _cache[k]
    return f
GB = [(o.name, _one(o)) for o in GOWN]
WHO = {"L": "", "R": ""}
GIN = {}
R = dict(groom_gap=(9, 0), groom_in=(0, 0), hand={"L": (0, 0), "R": (0, 0)}, hand_frames=[], scene={})
for f in range(f0, f1 + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); t = round((f - f0) / sc.render.fps, 2)
    sk, SV = bvh_of(SKIRT, dg)
    cb = bride.matrix_world @ bride.pose.bones["J_Bip_C_Hips"].head; cb = Vector((cb.x, cb.y, 0))
    for o in G_MESH:
        V, _ = wv(o, dg)
        for p in V[::2]:
            loc, _n, _i, d = sk.find_nearest(p, 0.6)
            if loc is not None and d < R["groom_gap"][0]:
                R["groom_gap"] = (d, t)
            s = ray_in(sk, Vector((p.x, p.y, p.z)), Vector((cb.x, cb.y, p.z)))
            if s > R["groom_in"][0]:
                R["groom_in"] = (s, t, o.name, round(p.z, 2))
            if s > 0.01:
                GIN.setdefault(t, [0, "", 0])
                if 1000 * s > GIN[t][0]:
                    GIN[t] = [round(1000 * s, 1), o.name, round(p.z, 2)]
    HV, _ = wv(B_BODY, dg, HAND_IDS)
    worst = {"L": 0, "R": 0}
    for gb in GB:
        for vi, p in zip(HAND_IDS, HV):
            s = ray_in(gb[1](dg), p, Vector((cb.x, cb.y, p.z)))
            if s > worst[SIDE[vi]]:
                worst[SIDE[vi]] = s; WHO[SIDE[vi]] = gb[0]
    for k in "LR":
        if worst[k] > R["hand"][k][0]:
            R["hand"][k] = (worst[k], t, WHO[k])
    if max(worst.values()) > 0.003:
        R["hand_frames"].append((t, round(1000 * worst["L"], 1), round(1000 * worst["R"], 1)))
    if MOVING:                                            # 會動的（門片）每格重算
        cur = statics(dg)
        for nm in MOVING:
            if nm in cur:
                st[nm] = BVHTree.FromPolygons(*cur[nm])
    for nm, b in st.items():
        d = max(-signed(b, p, 0.1) for p in SV[::3] if p.z > 0.04)
        if d > R["scene"].get(nm, (-1, 0))[0]:
            R["scene"][nm] = (d, t)
mm = lambda v: round(1000 * v, 1)
out = dict(step=STEP, groom_gap_mm=(mm(R["groom_gap"][0]), R["groom_gap"][1]), groom_in_mm=(mm(R["groom_in"][0]),) + tuple(R["groom_in"][1:]), groom_in_frames=sorted(GIN.items()),
           hand_in_mm={k: (mm(v[0]),) + tuple(v[1:]) for k, v in R["hand"].items()},
           hand_frames=R["hand_frames"], scene_in_mm={k: (mm(v[0]), v[1]) for k, v in sorted(R["scene"].items(), key=lambda x: -x[1][0])[:8]})
json.dump(out, open(OUT, "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("GOWN_DONE", json.dumps(out)[:600])
