# 生成端（zepeto-analyze-photo-3d-model）：把 Hyper3D Rodin 匯入的模型匯出成 OBJ＋貼圖，並讀回驗證。
# 在「已開著的 GUI Blender」裡經 MCP execute_blender_code 執行：
#   exec(open(r"<本檔絕對路徑>", encoding="utf-8").read(),
#        {"PARAMS": {"object": "<物件名>", "out_dir": r"<OUT 絕對路徑>", "base": "stylized_face_generated"}})
# 方向：Rodin 匯入時臉已朝 Blender 正面（−Y），**不要轉**；以 forward −Z／up Y 匯出，Y-up 軟體裡臉朝 +Z。
# 讀回驗證有兩層，缺一不可：
#   1. 數字：把剛寫出的 OBJ 用同樣的軸向匯入，逐點比對和原模型重不重合 —— 抓「匯出軸向設錯」。
#   2. 眼睛：讀回的物件留在場景（<base>_readback，原模型隱藏），由生成端用 work_scene.py view front 截圖，
#      要看得到臉 —— 抓「匯出前把模型本身轉錯」（第一次做就是這樣錯的，數字比對抓不到，因為檔案跟著一起轉）。
#   讀回物件由 work_scene.py cleanup 一起刪掉。
import bpy, os, json, shutil
from mathutils import Vector
from mathutils.kdtree import KDTree

P = PARAMS  # noqa: F821 —— 由 exec 的 globals 傳入
obj = bpy.data.objects[P["object"]]
out_dir = P["out_dir"]
base = P.get("base", "stylized_face_generated")
os.makedirs(out_dir, exist_ok=True)

# ── 1. 貼圖：Rodin 的貼圖打包在模型裡，拆成 png 放在 OBJ 旁邊 ──
TAGS = {"texture_diffuse": "diffuse", "texture_normal": "normal",
        "texture_metallic-texture_roughness": "metallic_roughness"}
written = []
for mat in [m for m in obj.data.materials if m]:
    for n in mat.node_tree.nodes:
        if n.type != 'TEX_IMAGE' or not n.image:
            continue
        img = n.image
        key = img.name.split(".")[0]
        tag = TAGS.get(key, key)
        if img.packed_file:
            data = bytes(img.packed_file.data)
            ext = ".png" if data[:8] == b"\x89PNG\r\n\x1a\n" else (".jpg" if data[:2] == b"\xff\xd8" else ".bin")
            path = os.path.join(out_dir, f"{base}_{tag}{ext}")
            with open(path, "wb") as f:
                f.write(data)
            img.filepath = path
            img.unpack(method='REMOVE')
            img.reload()
        else:
            src = bpy.path.abspath(img.filepath)
            ext = os.path.splitext(src)[1] or ".png"
            path = os.path.join(out_dir, f"{base}_{tag}{ext}")
            if os.path.abspath(src) != os.path.abspath(path):
                shutil.copyfile(src, path)
            img.filepath = path
        written.append(os.path.basename(path))

# ── 2. 匯出 OBJ（只匯出這個物件） ──
for o in bpy.context.view_layer.objects:
    o.select_set(False)
obj.hide_set(False)
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
obj_path = os.path.join(out_dir, base + ".obj")
bpy.ops.wm.obj_export(filepath=obj_path, export_selected_objects=True, export_materials=True,
                      export_uv=True, export_normals=True, path_mode='RELATIVE',
                      forward_axis='NEGATIVE_Z', up_axis='Y')

# ── 3. 讀回驗證：每個讀回的點，到原模型最近點的距離 ──
mw = obj.matrix_world
src_pts = [mw @ v.co for v in obj.data.vertices]
kd = KDTree(len(src_pts))
for i, c in enumerate(src_pts):
    kd.insert(c, i)
kd.balance()
before = set(bpy.data.objects.keys())
bpy.ops.wm.obj_import(filepath=obj_path, forward_axis='NEGATIVE_Z', up_axis='Y')
readback = [bpy.data.objects[n] for n in set(bpy.data.objects.keys()) - before]
max_err = None
readback_name = None
if readback:
    rb = readback[0]
    vs = rb.data.vertices
    step = max(1, len(vs) // 800)
    max_err = max(kd.find(rb.matrix_world @ vs[i].co)[2] for i in range(0, len(vs), step))
    rb.name = base + "_readback"
    readback_name = rb.name
    obj.hide_set(True)  # 只留讀回的物件給生成端截正面圖

corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
result = {
    "obj": obj_path,
    "textures": written,
    "verts": len(obj.data.vertices),
    "faces": len(obj.data.polygons),
    "dimensions": [round(max(c[i] for c in corners) - min(c[i] for c in corners), 3) for i in range(3)],
    "readback_object": readback_name,
    "readback_max_err": None if max_err is None else round(max_err, 6),
    "readback_ok": max_err is not None and max_err < 1e-3,
}
print("[export_obj] " + json.dumps(result, ensure_ascii=False))
