# 角色匯入與整理（在開著的 GUI Blender 裡、透過 Blender MCP 執行；背景 Blender 匯入 VRM 會失敗）。
#
# ⚠️ 開新檔和匯入一定要分成兩次 MCP 呼叫：read_homefile 之後同一次呼叫裡 bpy.context.window 是 None，
#    VRM 匯入器（底層是 glTF 匯入）會在 `bpy.context.window.scene = ...` 這行炸掉。
#
#   呼叫 1：new_empty_file()
#   呼叫 2：import_vrm(); organize(); save_base()
import bpy, os, math


def new_empty_file():
    bpy.ops.wm.read_homefile(use_empty=True)


def import_vrm(path=None):
    path = path or os.path.join(PROJ, MANIFEST["sources"]["vrm"])
    win = bpy.context.window_manager.windows[0]
    with bpy.context.temp_override(window=win, screen=win.screen):
        r = bpy.ops.import_scene.vrm(filepath=path)
    if "FINISHED" not in r:
        raise RuntimeError(f"VRM 匯入失敗：{r}")
    # 匯入失敗留下的空骨架（沒有子物件）清掉
    for o in list(bpy.data.objects):
        if o.type == "ARMATURE" and not o.children:
            bpy.data.objects.remove(o, do_unlink=True)
    return r


KEYWORDS = [("Body_00_SKIN", "Body"), ("HairBack", "HairBack"), ("Tops", "Tee"), ("Bottoms", "Shorts"),
            ("Shoes", "Shoes"), ("Onepiece", "Onepiece"), ("Accessory", "Accessory"), ("Socks", "Socks")]


def organize():
    """改名成 <WHO>_Armature / _Body / _Face / _Hair；身體依材質拆開（皮膚、後髮、上衣、下身、鞋…）；留一份原始身體 _SRC"""
    O = bpy.data.objects
    arms = [o for o in O if o.type == "ARMATURE" and o.children]
    if len(arms) != 1:
        raise RuntimeError(f"預期 1 個有子物件的骨架，實際 {len(arms)} 個：{[a.name for a in arms]}")
    A = arms[0]; A.name = f"{WHO}_Armature"; A.rotation_mode = "XYZ"
    for n in ("Body", "Face", "Hair"):
        if n in O:
            O[n].name = f"{WHO}_{n}"
    body = O[f"{WHO}_Body"]
    if f"{WHO}_SRC" not in O:
        src = body.copy(); src.data = body.data.copy(); src.name = f"{WHO}_SRC"
        body.users_collection[0].objects.link(src); src.hide_render = True; src.hide_viewport = True
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = body; body.select_set(True)
    with bpy.context.temp_override(active_object=body, object=body, selected_objects=[body], selected_editable_objects=[body]):
        bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.separate(type="MATERIAL"); bpy.ops.object.mode_set(mode="OBJECT")
    renamed = {}
    for o in [o for o in O if o.name.startswith(f"{WHO}_Body")]:
        used = {p.material_index for p in o.data.polygons}
        mats = [o.material_slots[i].material.name for i in used]
        label = next((lab for key, lab in KEYWORDS if any(key in m for m in mats)), None) or f"Part{len(renamed)}"
        o.name = f"__tmp_{WHO}_{label}"; renamed[label] = mats
    for o in list(O):
        if o.name.startswith("__tmp_"):
            o.name = o.name[6:]
    # 身體皮膚的 MToon 輪廓線關掉：補皮膚的接縫會被輪廓線描出來（臉、頭髮保留）
    skin = O[f"{WHO}_Body"].material_slots[0].material
    skin.vrm_addon_extension.mtoon1.extensions.vrmc_materials_mtoon.outline_width_mode = "none"
    return renamed


def skin_holes():
    """列出身體皮膚的破洞（開放邊界環）：z 範圍、x 範圍。上半身有大洞＝VRoid 刪掉了衣服底下的皮膚，要跑 body_fill"""
    import bmesh
    from collections import defaultdict
    body = bpy.data.objects[f"{WHO}_Body"]
    bm = bmesh.new(); bm.from_mesh(body.data)
    adj = defaultdict(list)
    for e in bm.edges:
        if len(e.link_faces) == 1:
            a, b = e.verts; adj[a.index].append(b.index); adj[b.index].append(a.index)
    bm.verts.ensure_lookup_table()
    seen, loops = set(), []
    for s in adj:
        if s in seen:
            continue
        st, comp = [s], []
        while st:
            x = st.pop()
            if x in seen:
                continue
            seen.add(x); comp.append(x); st += adj[x]
        P = [bm.verts[i].co for i in comp]
        loops.append(dict(n=len(comp), x=(round(min(p.x for p in P), 3), round(max(p.x for p in P), 3)),
                          z=(round(min(p.z for p in P), 3), round(max(p.z for p in P), 3))))
    bm.free()
    return sorted(loops, key=lambda l: -l["n"])


def save_base():
    use("studio")
    setup_studio()
    path = os.path.join(PROJ, MANIFEST["blend"]["base"])
    bpy.ops.wm.save_as_mainfile(filepath=path)
    return path
