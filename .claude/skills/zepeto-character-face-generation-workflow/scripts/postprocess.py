# ZEPETO 風大頭的後處理（zepeto-avatar-crafter 用；Blender 4.x／5.x 皆可）：
#   1. 清空場景 → 匯入 OBJ → 原點設到幾何中心、移到 (0,0,0)、套用所有變換
#   2. 焊接重疊頂點（0.001）→ 重算法線 → 清掉 OBJ 自帶的自訂法線 → 細分 1 級＋平滑著色
#   3. 新建 ZEPETO_Head_Shader（顏色貼圖接 Base Color、亮澤粗糙度、次表面散射透出血色）
#   4. 三點燈光（左前主光、右前補光、正後輪廓光）＋鏡頭，開檔即鏡頭視角＋材質預覽，存成 .blend
# 用法（背景執行，不影響已開著的 Blender）：
#   blender.exe -b --factory-startup --python postprocess.py -- --obj <OUT>/stylized_face_generated.obj [--blend <OUT>/stylized_face_zepeto.blend]
#   選填：--sss-weight 0.15 --sss-scale 0.05 --sss-radius 1,0.2,0.1 --roughness 0.5
import bpy, os, sys, argparse
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--obj", required=True)
ap.add_argument("--blend", default=None, help="預設：OBJ 同資料夾的 stylized_face_zepeto.blend")
ap.add_argument("--diffuse", default=None, help="預設：<OBJ 主檔名>_diffuse.png")
# 2026-10-14 改亮澤（使用者 2026-10-13 選亮澤；ZEPETO 皮膚光滑有光澤，見 zepeto-face-rig/references/research-zepeto-face.md）：
#   粗糙度 0.75→0.5、次表面散射 0.3→0.15，跟可動臉成品（gloss.py）一致。舊值是 2026-10-11 霧面黏土風定案的（權重 1.0 會把鼻孔、嘴角的小陰影抹平）
ap.add_argument("--sss-weight", type=float, default=0.15)
ap.add_argument("--sss-scale", type=float, default=0.05)  # 0.05～0.1；再大卡通臉會透得像果凍
ap.add_argument("--sss-radius", default="1.0,0.2,0.1")    # 紅光穿透遠大於綠、藍 → 邊緣透出血色（偏暖桃色）
ap.add_argument("--roughness", type=float, default=0.5)        # 不加 Coat 光澤層：整張臉會泛白、眼珠眉毛發灰
opt = ap.parse_args(argv)

OBJ_PATH = os.path.abspath(opt.obj)
WORK_DIR = os.path.dirname(OBJ_PATH)
BASE = os.path.splitext(os.path.basename(OBJ_PATH))[0]
DIFFUSE_PATH = os.path.abspath(opt.diffuse) if opt.diffuse else os.path.join(WORK_DIR, BASE + "_diffuse.png")
BLEND_PATH = os.path.abspath(opt.blend) if opt.blend else os.path.join(WORK_DIR, "stylized_face_zepeto.blend")
SSS_RADIUS = tuple(float(x) for x in opt.sss_radius.split(","))
MERGE_DIST = 0.001

for p in (OBJ_PATH, DIFFUSE_PATH):
    if not os.path.exists(p):
        raise SystemExit(f"[postprocess] 找不到 {p}")


def set_engine_eevee(scene):
    """EEVEE 的識別名稱隨版本不同（4.2～4.5 是 EEVEE_NEXT），依序嘗試"""
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            scene.render.engine = eng
            return eng
        except TypeError:
            continue
    return scene.render.engine


def aim(ob, target=Vector((0.0, 0.0, 0.0))):
    """讓燈光／鏡頭的 −Z 軸對準 target"""
    ob.rotation_euler = (target - ob.location).to_track_quat('-Z', 'Y').to_euler()


def add_area_light(scene, name, loc, energy, size, color):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = energy
    data.size = size
    data.color = color
    ob = bpy.data.objects.new(name, data)
    scene.collection.objects.link(ob)
    ob.location = loc
    aim(ob)
    return ob


scene = bpy.context.scene
view_layer = bpy.context.view_layer
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')

# ── 1. 清空場景、匯入、置中 ──
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
try:
    bpy.data.orphans_purge(do_recursive=True)
except (AttributeError, TypeError):
    pass

bpy.ops.wm.obj_import(filepath=OBJ_PATH, forward_axis='NEGATIVE_Z', up_axis='Y')
head = bpy.context.selected_objects[0]
head.name = "ZEPETO_Head"
bpy.ops.object.select_all(action='DESELECT')
head.select_set(True)
view_layer.objects.active = head

# 先把匯入時的軸向轉換吃進網格，再設原點，最後歸零並再套用一次
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
head.location = (0.0, 0.0, 0.0)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# ── 2. 網格修復 ──
verts_before = len(head.data.vertices)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=MERGE_DIST)
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')
verts_after = len(head.data.vertices)

# OBJ 帶進來的自訂法線會蓋過平滑著色與重算的法線，要先清掉
if head.data.has_custom_normals:
    bpy.ops.mesh.customdata_custom_splitnormals_clear()
if hasattr(head.data, "use_auto_smooth"):  # 4.0 匯入 OBJ 會開自動平滑（30°），尖角會出現硬邊
    head.data.use_auto_smooth = False

sub = head.modifiers.new("Subdivision", 'SUBSURF')
sub.levels = 1
sub.render_levels = 1  # 算圖也只細分 1 級，不然預設 2 級會讓面數再翻 4 倍
bpy.ops.object.shade_smooth()

# ── 3. ZEPETO_Head_Shader（2026-10-14 前叫 ZEPETO_Clay_Shader；下游一律用第 1 個材質槽，不認名字）──
mat = bpy.data.materials.new("ZEPETO_Head_Shader")
if bpy.app.version < (5, 0, 0):  # 5.0 起材質一律用節點，再設會跳棄用警告
    mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
bsdf = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')

tex = nodes.new('ShaderNodeTexImage')
tex.image = bpy.data.images.load(DIFFUSE_PATH, check_existing=True)
tex.location = (bsdf.location.x - 400, bsdf.location.y)
links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])

bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = opt.roughness
# 4.0 起沒有「Subsurface Color」，散射顏色取自 Base Color，靠三色通道的散射距離調色
bsdf.inputs['Subsurface Weight'].default_value = opt.sss_weight
bsdf.inputs['Subsurface Radius'].default_value = SSS_RADIUS
bsdf.inputs['Subsurface Scale'].default_value = opt.sss_scale

old_mats = [m for m in head.data.materials if m]
head.data.materials.clear()
head.data.materials.append(mat)
# OBJ 匯入時自帶的材質（含法線貼圖）已沒人用，連同只有它在用的貼圖一起刪掉
for m in old_mats:
    imgs = [n.image for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image]
    bpy.data.materials.remove(m)
    for img in imgs:
        if img.users == 0:
            bpy.data.images.remove(img)

# ── 4. 三點燈光＋鏡頭（臉朝 −Y；「左」指從鏡頭看過去的左邊） ──
add_area_light(scene, "Key_FrontLeft", (-2.6, -2.8, 1.6), 450.0, 2.0, (1.0, 0.96, 0.92))
add_area_light(scene, "Fill_FrontRight", (2.8, -2.6, 0.4), 180.0, 3.0, (0.93, 0.96, 1.0))
add_area_light(scene, "Rim_Back", (0.0, 3.0, 1.8), 500.0, 1.5, (1.0, 1.0, 1.0))

cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 85
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
cam.location = (0.0, -5.6, 0.05)
aim(cam)
scene.camera = cam
scene.render.resolution_x = 1080
scene.render.resolution_y = 1080
engine = set_engine_eevee(scene)

# 打開 .blend 就是從鏡頭看、帶三點燈光的預覽。
# 不設 RENDERED：Blender 開檔時會把它重設回 SOLID（實測）；改用材質預覽＋場景燈光／世界，看到的效果相同
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            space = area.spaces.active
            space.shading.type = 'MATERIAL'
            space.shading.use_scene_lights = True
            space.shading.use_scene_world = True
            space.region_3d.view_perspective = 'CAMERA'

# 貼圖與 .blend 同資料夾時寫成相對路徑（整個資料夾搬走也找得到）
if os.path.dirname(DIFFUSE_PATH) == os.path.dirname(BLEND_PATH):
    tex.image.filepath = "//" + os.path.basename(DIFFUSE_PATH)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH, relative_remap=False)

print("[postprocess] verts %d -> %d (merged %d), faces %d, engine %s, sss %.3f/%s/%.3f, rough %.2f, saved %s"
      % (verts_before, verts_after, verts_before - verts_after, len(head.data.polygons), engine,
         opt.sss_weight, SSS_RADIUS, opt.sss_scale, opt.roughness, BLEND_PATH))
