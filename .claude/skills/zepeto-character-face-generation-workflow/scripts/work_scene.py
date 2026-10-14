# 生成端（zepeto-analyze-photo-3d-model）在「使用者開著的 GUI Blender」裡作業用的工作場景工具。
# 一律在獨立的 ZEPETO_WORK 場景裡做，做完整個刪掉並切回原場景 —— 不動使用者原本開著的檔案內容、不存檔。
# 經 MCP execute_blender_code 執行：
#   exec(open(r"<本檔絕對路徑>", encoding="utf-8").read(), {"PARAMS": {"action": "...", ...}})
# action：
#   open                        建立／切到 ZEPETO_WORK，在這個場景開 Hyper3D Rodin＋免費試用金鑰
#   isolate  object=<名稱>      只顯示這個物件（同場景其他網格隱藏），材質預覽
#   view     object=<名稱> dir=front|side|back|34   視角對準物件（臉朝 −Y），之後再呼叫 get_viewport_screenshot
#   info     object=<名稱>      印出尺寸，深度（y）大於高度（z）多半是後腦長出東西（例：馬尾）
#   cleanup                     刪掉 ZEPETO_WORK 與裡面的物件／網格／材質／貼圖，切回原場景
import bpy, json
from mathutils import Vector

P = PARAMS  # noqa: F821 —— 由 exec 的 globals 傳入
WORK = "ZEPETO_WORK"
act = P["action"]
out = {"action": act}


def view3d_areas():
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            yield area


if act == "open":
    win = bpy.context.window
    if win.scene.name != WORK:
        prev = win.scene.name
        ws = bpy.data.scenes.get(WORK) or bpy.data.scenes.new(WORK)
        ws["zepeto_prev_scene"] = prev
        win.scene = ws
    ws = win.scene
    # Hyper3D 的開關與金鑰是「場景」屬性，要在切過來之後設
    ws.blendermcp_use_hyper3d = True
    ws.blendermcp_hyper3d_mode = 'MAIN_SITE'
    bpy.ops.blendermcp.set_hyper3d_free_trial_api_key()
    out.update(scene=ws.name, prev_scene=ws.get("zepeto_prev_scene"), blender=bpy.app.version_string,
               file=bpy.data.filepath or "(未存檔)", key_set=bool(ws.blendermcp_hyper3d_api_key))

elif act == "isolate":
    ws = bpy.data.scenes[WORK]
    keep = bpy.data.objects[P["object"]]
    for o in ws.objects:
        o.hide_set(o != keep and o.type == 'MESH')
    for area in view3d_areas():
        area.spaces.active.shading.type = 'MATERIAL'
    out.update(shown=keep.name)

elif act == "view":
    ob = bpy.data.objects[P["object"]]
    corners = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    center = sum(corners, Vector()) / 8
    size = max(ob.dimensions)
    # 視線方向：臉朝 −Y，所以「看臉」是朝 +Y 看
    dirs = {"front": (0, 1, 0), "back": (0, -1, 0), "side": (-1, 0, 0), "34": (-0.7, 1, 0.1)}
    d = Vector(dirs[P.get("dir", "front")]).normalized()
    for area in view3d_areas():
        r3 = area.spaces.active.region_3d
        r3.view_perspective = 'PERSP'
        r3.view_location = center
        r3.view_distance = size * 1.9
        r3.view_rotation = d.to_track_quat('-Z', 'Y')
    out.update(object=ob.name, dir=P.get("dir", "front"))

elif act == "info":
    ob = bpy.data.objects[P["object"]]
    # 用世界座標的外框量（物件本身帶旋轉時 ob.dimensions 是物件自己的軸，會量錯）
    corners = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    dx, dy, dz = (max(c[i] for c in corners) - min(c[i] for c in corners) for i in range(3))
    out.update(object=ob.name, dimensions=[round(dx, 3), round(dy, 3), round(dz, 3)],
               verts=len(ob.data.vertices), faces=len(ob.data.polygons),
               depth_over_height=round(dy / dz, 3) if dz else None)

elif act == "cleanup":
    ws = bpy.data.scenes.get(WORK)
    if ws:
        prev = ws.get("zepeto_prev_scene")
        meshes = {o.data for o in ws.objects if o.type == 'MESH'}
        mats = {m for me in meshes for m in me.materials if m}
        imgs = {n.image for m in mats for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image}
        for o in list(ws.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        for me in meshes:
            if me.users == 0:
                bpy.data.meshes.remove(me)
        for m in mats:
            if m.users == 0:
                bpy.data.materials.remove(m)
        for im in imgs:
            if im.users == 0:
                bpy.data.images.remove(im)
        if bpy.context.window.scene == ws:
            others = [s for s in bpy.data.scenes if s != ws]
            back = bpy.data.scenes.get(prev) if prev else None
            bpy.context.window.scene = back or (others[0] if others else bpy.data.scenes.new("Scene"))
        bpy.data.scenes.remove(ws)
        out.update(removed=True, back_to=prev)
    else:
        out.update(removed=False)

print("[work_scene] " + json.dumps(out, ensure_ascii=False))
