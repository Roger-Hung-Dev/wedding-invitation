# 攝影棚：相機、燈光、背景、地板。exec 在 Blender 裡；可重複執行（已存在就更新）。
import bpy, math, os
from mathutils import Vector

sc = bpy.context.scene
O = bpy.data.objects


def get_light(name, kind):
    o = O.get(name)
    if o is None:
        o = bpy.data.objects.new(name, bpy.data.lights.new(name, kind)); sc.collection.objects.link(o)
    return o


def setup_studio(bg=(0.93, 0.89, 0.86)):
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 32
    sc.view_settings.view_transform = "Standard"
    sc.render.film_transparent = False
    sc.render.fps = 24
    w = sc.world or bpy.data.worlds.new("World"); sc.world = w
    w.use_nodes = True
    bgn = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bgn.inputs[0].default_value = (*bg, 1); bgn.inputs[1].default_value = 1.0
    sun = get_light("Sun", "SUN"); sun.data.energy = 2.5
    sun.location = (2, -4, 5); sun.rotation_euler = (math.radians(50), 0, math.radians(20))
    sun.data.angle = math.radians(8)
    fill = get_light("Fill", "AREA"); fill.data.energy = 300; fill.data.size = 3
    fill.location = (-3, -3, 2.5); fill.rotation_euler = (math.radians(60), 0, math.radians(-45))
    rim = get_light("Rim", "AREA"); rim.data.energy = 250; rim.data.size = 2
    rim.location = (1.5, 3.0, 2.6); rim.rotation_euler = (math.radians(-60), 0, math.radians(155))
    cam = O.get("Camera")
    if cam is None:
        cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera")); sc.collection.objects.link(cam)
    sc.camera = cam
    # 地板：大圓盤，顏色比背景略深，接影子
    if "Floor" not in O:
        bpy.ops.mesh.primitive_circle_add(vertices=96, radius=6, fill_type="NGON", location=(0, 0, 0))
        fl = bpy.context.object; fl.name = "Floor"
        m = bpy.data.materials.new("FloorMat"); m.use_nodes = True
        p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        p.inputs["Base Color"].default_value = (bg[0] * 0.92, bg[1] * 0.9, bg[2] * 0.88, 1)
        p.inputs["Roughness"].default_value = 0.9
        fl.data.materials.append(m)
    return cam


def aim(cam, loc, target, lens=50):
    cam.location = loc; cam.data.lens = lens
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def shot(path, res=(600, 900)):
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)


def orbit_views(prefix, target=(0, 0, 0.82), dist=4.2, h=1.0, lens=50, res=(600, 900), angles=(0, 45, 90, 135, 180, 225, 270, 315)):
    """角色面向 -Y；angle 0 = 正面，90 = 從角色左側看"""
    cam = O["Camera"]; out = []
    for a in angles:
        r = math.radians(a)
        aim(cam, (math.sin(r) * dist, -math.cos(r) * dist, h), target, lens)
        p = f"{prefix}_{a:03d}.png"; shot(p, res); out.append(p)
    return out
