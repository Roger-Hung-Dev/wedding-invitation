# ZEPETO 動畫共用：穿衣服、量衣服（2026-10-12 由坐餐桌喝紅酒的 t_sit_suit 抽出、改成不限哪一套）。
#   dress()：從已出廠的服裝檔搬衣服進工作場景、改綁這個場景的骨架；身體被蓋住的頂點照服裝檔一樣藏起來（只藏不刪）
#   no_mask：量身體時先不藏（很多量測用完整網格的頂點編號）
#   prop_bvh／depth／depth_tube：量「點在道具／褲管裡面多深」
# 教訓：衣服要一開始就穿（手擱大腿要對褲子表面、靠椅背要量西裝），不要做完動作才穿。
import os, json
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import zanim as Z
STATE = Z.STATE
COSTUME = r"D:/render-work/zepeto-costume"
STATUS = Z.REPO + "/.claude/docs/data/blender/zepeto/pipeline/status/outfit"


def outfit_blend(outfit, body):
    """已出廠服裝的 outfit.blend（狀態紀錄 outfit/<服裝>@<人> 要是 released）"""
    sid = outfit.replace("-", "_") + "@" + body
    st = json.load(open(f"{STATUS}/{sid}.json", encoding="utf8"))
    if st.get("status") != "released":
        raise RuntimeError(f"服裝 {sid} 還沒出廠")
    return st["artifact"]["path"], st


def dress(outfit, body=None):
    """搬衣服進來。回傳 (衣服物件名清單, 藏起來的身體頂點數)"""
    body = body or STATE["body"]
    path, _st = outfit_blend(outfit, body)
    sc = STATE["sc"]; arm = STATE["arm"]; bmesh_obj = Z.L.body_mesh(arm)
    have = STATE.setdefault("outfit_objs", [])
    if have and all(n in sc.objects for n in have):
        return have, None
    with bpy.data.libraries.load(path) as (src, _):
        names = [n for n in src.objects]
    arm_src = None
    with bpy.data.libraries.load(path) as (src, dst):
        dst.objects = names
    col = bpy.data.collections.get(STATE["prefix"] + "outfit") or bpy.data.collections.new(STATE["prefix"] + "outfit")
    if col.name not in sc.collection.children:
        sc.collection.children.link(col)
    src_body, garments = None, []
    for o in dst.objects:
        if o is None:
            continue
        if o.type == "ARMATURE":
            arm_src = o; continue
        if o.type == "MESH" and any(m.type == "ARMATURE" for m in o.modifiers) and o.name.split(".")[0] == bmesh_obj.name.split(".")[0]:
            src_body = o; continue
        if o.type == "MESH" and any(m.type == "ARMATURE" for m in o.modifiers) and "Hide_Under_Outfit" not in o.vertex_groups:
            if o.name.split(".")[0] in {x.name.split(".")[0] for x in sc.objects}:      # 頭、頭髮等身體本來就有的
                continue
            col.objects.link(o); o.parent = arm; garments.append(o.name)
            for m in o.modifiers:
                if m.type == "ARMATURE":
                    m.object = arm
    n_hidden = 0
    if src_body is not None and "Hide_Under_Outfit" in src_body.vertex_groups:
        gi = src_body.vertex_groups["Hide_Under_Outfit"].index
        ids = [v.index for v in src_body.data.vertices if any(g.group == gi and g.weight > 0 for g in v.groups)]
        vg = bmesh_obj.vertex_groups.get("Hide_Under_Outfit") or bmesh_obj.vertex_groups.new(name="Hide_Under_Outfit")
        vg.add(ids, 1.0, "REPLACE")
        m = bmesh_obj.modifiers.get("HideUnderOutfit") or bmesh_obj.modifiers.new("HideUnderOutfit", "MASK")
        m.vertex_group = "Hide_Under_Outfit"; m.invert_vertex_group = True
        n_hidden = len(ids)
    for o in dst.objects:                                 # 這次搬進來、沒放進場景的（骨架、身體、頭的副本）；只動這次載入的，不碰使用者檔案裡的東西
        if o is not None and o.name in bpy.data.objects and not o.users_scene:
            bpy.data.objects.remove(o)
    STATE["outfit_objs"] = garments; STATE["outfit"] = outfit
    return garments, n_hidden


class no_mask:
    """量身體時先不藏衣服底下的頂點：很多量測用完整網格的頂點編號"""
    def __enter__(self):
        self.m = Z.L.body_mesh(STATE["arm"]).modifiers.get("HideUnderOutfit")
        if self.m:
            self.m.show_viewport = False
        STATE["sc"].view_layers[0].update()

    def __exit__(self, *a):
        if self.m:
            self.m.show_viewport = True


def world_verts(o, dg):
    oe = o.evaluated_get(dg); me = oe.to_mesh(); M = o.matrix_world
    V = [M @ v.co for v in me.vertices]; F = [tuple(p.vertices) for p in me.polygons]
    oe.to_mesh_clear()
    return V, F


def prop_bvh(o, dg):
    """o 和底下所有網格（含集合實例：素材庫道具是空物件＋集合）合成一個 BVH（世界座標）"""
    V, F = [], []
    parts = [(c, c.matrix_world) for c in [o] + list(o.children_recursive) if c.type == "MESH"]
    if o.instance_type == "COLLECTION" and o.instance_collection:
        parts += [(c, o.matrix_world @ c.matrix_world) for c in o.instance_collection.all_objects if c.type == "MESH"]
    for c, M in parts:
        oe = c.evaluated_get(dg); me = oe.to_mesh(); k = len(V)
        V += [M @ v.co for v in me.vertices]; F += [tuple(j + k for j in p.vertices) for p in me.polygons]
        oe.to_mesh_clear()
    return BVHTree.FromPolygons(V, F)


def depth(bvh, p, far=0.05):
    """點在網格裡面多深（m，正＝在裡面）；用最近面的法線判斷，太遠就當外面"""
    loc, nrm, _i, d = bvh.find_nearest(p, far)
    if loc is None:
        return -far
    return d if (p - loc).dot(nrm) < 0 else -d


def depth_tube(bvh, p, far=0.03):
    """同 depth，但再要求往上、往下兩條射線都打到（褲管、袖子是兩頭開口的管子：只看法線會把管子外面的點誤判成在裡面）"""
    d = depth(bvh, p, far)
    if d <= 0:
        return d
    up = bvh.ray_cast(p, Vector((0, 0, 1)), 0.2)[0]; dn = bvh.ray_cast(p, Vector((0, 0, -1)), 0.2)[0]
    return d if (up is not None and dn is not None) else -0.0001


def outfit_vs_props(props, step=6, outer=None, times=None):
    """逐格量：衣服最外層的頂點穿進每個道具多深（m，正＝穿進去）。props：{名稱: 物件}（靜止的道具）。
    回傳 {(衣服, 道具): (最深, 第幾格)}。會動的道具（杯子、手機）用各鏡自己的距離場量"""
    sc = STATE["sc"]; dg = sc.view_layers[0].depsgraph
    outer = outer or [n for n in STATE.get("outfit_objs", []) if any(k in n for k in ("Jacket", "Pants", "Shoes", "Dress", "Skirt", "Coat"))]
    bvhs = {k: prop_bvh(o, dg) for k, o in props.items()}
    n = len(STATE["poses"])
    frames = [int(round(t * 30)) for t in times] if times else list(range(0, n, step))
    worst = {}
    for i in frames:
        Z.pose_at(i / 30)
        for on in outer:
            V, _ = world_verts(sc.objects[on], dg)
            for pk, b in bvhs.items():
                d = max(depth(b, p) for p in V[::3])
                if (on, pk) not in worst or d > worst[(on, pk)][0]:
                    worst[(on, pk)] = (d, i)
    return {f"{a}→{b}": (round(1000 * v, 1), round(i / 30, 2)) for (a, b), (v, i) in worst.items()}
