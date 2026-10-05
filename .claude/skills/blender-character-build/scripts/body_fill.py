# 補身體：VRoid 匯出時會刪掉衣服底下看不到的皮膚（T 恤款：上胸、肩、整片上背、上臂）。換成露肩的服裝就會看到破洞。
# 做法：用截面 loft 出上半身軀幹＋（女性）胸部橢球＋上臂（沿用既有手臂截面）＋斜方肌＋鎖骨，體素重建合成一塊，
# 修邊後把靠近既有皮膚的頂點吸到皮膚內側（接縫不留縫），接縫法線沿用原皮膚、權重從原始網格轉移、顏色用小漸層貼圖。
#
# 一鍵：run_fill()。座標以預設庫的新娘（頭骨高 1.386 m）量出來，其他角色用 S＝頭骨高/1.386 等比例縮放。
# 換體型差很多的角色（男性、Q 版）時，一定要渲染 fill_check 檢查圖確認，必要時調 SECTIONS。細節見 references/body-fill.md。
import bpy, bmesh, math
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

O = bpy.data.objects
A_ = O[f"{WHO}_Armature"]
S = A_.data.bones["J_Bip_C_Head"].head_local.z / 1.386
BUST = MANIFEST.get("body", {}).get("bust", True)

# (z, 半寬 a, 前 yf, 後 yb) —— 新娘座標，使用時乘 S
SECTIONS = [
    (0.98, 0.112, -0.108, 0.048), (1.02, 0.098, -0.110, 0.034), (1.05, 0.089, -0.113, 0.024),
    (1.08, 0.090, -0.113, 0.025), (1.11, 0.096, -0.112, 0.032), (1.14, 0.104, -0.108, 0.044),
    (1.17, 0.110, -0.100, 0.055), (1.20, 0.114, -0.090, 0.063), (1.23, 0.115, -0.079, 0.068),
    (1.26, 0.110, -0.062, 0.070), (1.29, 0.098, -0.038, 0.068), (1.31, 0.080, -0.026, 0.066),
    (1.33, 0.052, -0.016, 0.063), (1.36, 0.036, -0.019, 0.064), (1.39, 0.040, -0.006, 0.070),
]
EXP = 2.4      # 截面形狀：2 = 橢圓，越大越方


def V(x, y, z):
    return Vector((x * S, y * S, z * S))


def _loft(bm, secs, n=48):
    rings = []
    for z, a, yf, yb in secs:
        z, a, yf, yb = z * S, a * S, yf * S, yb * S
        cy = (yf + yb) / 2; hd = (yb - yf) / 2
        ring = []
        for k in range(n):
            t = 2 * math.pi * k / n
            c, s = math.cos(t), math.sin(t)
            x = a * math.copysign(abs(c) ** (2 / EXP), c)
            y = cy + hd * math.copysign(abs(s) ** (2 / EXP), s)
            ring.append(bm.verts.new((x, y, z)))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(n):
            bm.faces.new((r0[k], r0[(k + 1) % n], r1[(k + 1) % n], r1[k]))
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])


def _ellipsoid(bm, c, r, rot=None):
    res = bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0)
    M = Matrix.Translation(c) @ (rot or Matrix.Identity(4)) @ Matrix.Diagonal((*r, 1))
    bmesh.ops.transform(bm, matrix=M, verts=res["verts"])


def _tube(bm, p0, p1, r0, r1, n=24, rings=10, su=1.0, sv=1.0):
    p0, p1 = Vector(p0), Vector(p1); d = (p1 - p0).normalized()
    u = d.cross(Vector((0, 0, 1))) if abs(d.z) < 0.9 else d.cross(Vector((1, 0, 0)))
    u.normalize(); v = d.cross(u)
    R = []
    for i in range(rings + 1):
        t = i / rings; c = p0.lerp(p1, t); r = r0 + (r1 - r0) * t
        R.append([bm.verts.new(c + (u * su * math.cos(2 * math.pi * k / n) + v * sv * math.sin(2 * math.pi * k / n)) * r) for k in range(n)])
    for a, b in zip(R, R[1:]):
        for k in range(n):
            bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    bm.faces.new(R[0][::-1]); bm.faces.new(R[-1])
    B = Matrix((u * su, v * sv, d)).transposed().to_4x4()   # 球帽跟管子同樣的橢圓截面
    for c, r in ((p0, r0), (p1, r1)):
        _ellipsoid(bm, c, (r, r, r), B)


def _polar_ring(pts, n, cy, cz):
    """把截面點（YZ 平面）依角度排序，等角度重新取樣半徑"""
    pol = sorted((math.atan2(p.z - cz, p.y - cy), math.hypot(p.y - cy, p.z - cz)) for p in pts)
    pol = [(a - 2 * math.pi, r) for a, r in pol[-3:]] + pol + [(a + 2 * math.pi, r) for a, r in pol[:3]]
    out = []
    for k in range(n):
        t = -math.pi + 2 * math.pi * k / n
        for (a0, r0), (a1, r1) in zip(pol, pol[1:]):
            if a0 <= t <= a1:
                out.append(r0 + (r1 - r0) * ((t - a0) / (a1 - a0) if a1 > a0 else 0)); break
    return out


ARM_GROW = [(0.30, 1.0, 0.0), (0.27, 1.0, 0.0), (0.24, 1.02, 0.0005), (0.21, 1.05, 0.001), (0.18, 1.09, 0.002),
            (0.15, 1.13, 0.003), (0.125, 1.15, 0.003), (0.105, 1.12, 0.002)]   # (x, 相對 x=0.27 截面的放大倍率, 中心上移)


def section_skin(body, x):
    bm = bmesh.new(); bm.from_mesh(body.data)
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6, plane_co=(x, 0, 0), plane_no=(1, 0, 0))
    pts = [v.co.copy() for v in res["geom_cut"] if isinstance(v, bmesh.types.BMVert) and v.co.z > 1.15 * S]
    bm.free()
    return pts


def _arm_loft(bm, sx, n=32):
    """上臂：從既有手臂 x=0.27 的真實截面出發，往肩膀逐步放大，接縫處形狀完全一致"""
    body = O[f"{WHO}_Body"]
    pts = section_skin(body, 0.27 * S * sx)
    if len(pts) < 8:
        raise RuntimeError("x=0.27 處切不到手臂截面：這個角色的手臂皮膚也被刪了，要改 ARM_GROW 的起點（見 references/body-fill.md）")
    cy = sum(p.y for p in pts) / len(pts); cz = sum(p.z for p in pts) / len(pts)
    base = _polar_ring(pts, n, cy, cz)
    rings = []
    for x, k, dz in ARM_GROW:
        ring = []
        for i, r in enumerate(base):
            t = -math.pi + 2 * math.pi * i / n
            ring.append(bm.verts.new((x * S * sx, cy + math.cos(t) * r * k, cz + dz * S + math.sin(t) * r * k)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for i in range(n):
            bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    bm.faces.new(rings[0]); bm.faces.new(rings[-1][::-1])


def build_blocks(name="FillBlocks"):
    if name in O:
        bpy.data.objects.remove(O[name], do_unlink=True)
    bm = bmesh.new()
    _loft(bm, SECTIONS)
    for sx in (1, -1):
        if BUST:                                                                       # 胸部：略往外、往上翹
            rot = Matrix.Rotation(math.radians(-12 * sx), 4, "Z")
            _ellipsoid(bm, V(0.053 * sx, -0.079, 1.174), tuple(v * S for v in (0.050, 0.039, 0.047)), rot)
        _arm_loft(bm, sx)                                                              # 上臂＋三角肌
        _tube(bm, V(0.030 * sx, 0.032, 1.338), V(0.135 * sx, 0.024, 1.292), 0.024 * S, 0.022 * S)  # 斜方肌
        _tube(bm, V(0.018 * sx, -0.040, 1.300), V(0.125 * sx, 0.000, 1.296), 0.011 * S, 0.015 * S)  # 鎖骨
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob


def remesh(ob, voxel=0.003, smooth_iter=35):
    m = ob.modifiers.new("Remesh", "REMESH"); m.mode = "VOXEL"; m.voxel_size = voxel * S; m.use_smooth_shade = True
    s = ob.modifiers.new("Smooth", "LAPLACIANSMOOTH"); s.iterations = smooth_iter; s.lambda_factor = 0.6; s.use_volume_preserve = True
    bpy.context.view_layer.objects.active = ob
    for md in list(ob.modifiers):
        with bpy.context.temp_override(object=ob, active_object=ob):
            bpy.ops.object.modifier_apply(modifier=md.name)
    return ob


def skin_bvh(body):
    """只拿皮膚材質的面建 BVH（rest 座標）"""
    me = body.data
    names = [s.material.name for s in body.material_slots]
    skin = {i for i, n in enumerate(names) if "SKIN" in n.upper()}
    verts = [v.co.copy() for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons if p.material_index in skin]
    return BVHTree.FromPolygons(verts, polys)


def trim(ob, z_min=1.0, z_max=1.40, x_max=0.255):
    z_min, z_max, x_max = z_min * S, z_max * S, x_max * S
    bm = bmesh.new(); bm.from_mesh(ob.data)
    planes = [((0, 0, z_min), (0, 0, -1)), ((0, 0, z_max), (0, 0, 1)), ((x_max, 0, 0), (1, 0, 0)), ((-x_max, 0, 0), (-1, 0, 0))]
    for co, n in planes:
        co, n = Vector(co), Vector(n)
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6, plane_co=co, plane_no=n)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if (f.calc_center_median() - co).dot(n) > 0], context="FACES")
    bm.to_mesh(ob.data); bm.free()


def snap_to_skin(ob, bvh, near=0.005, far=0.022, inset=0.001):
    """頂點離既有皮膚 near 以內：整個吸到皮膚內側 inset；near~far 之間漸變；更遠不動"""
    near, far, inset = near * S, far * S, inset * S
    n = 0
    for v in ob.data.vertices:
        loc, nrm, idx, d = bvh.find_nearest(v.co)
        if loc is None or d > far:
            continue
        w = 1.0 if d <= near else 1 - (d - near) / (far - near)
        w = w * w * (3 - 2 * w)
        v.co = v.co.lerp(loc - nrm * inset, w); n += 1
    return n


def delete_dark_band(z_from=0.98, x_max=0.25):
    """VRoid 皮膚貼圖在衣服邊緣畫了黑色內衣帶；補皮膚後會露出來，把那些面刪掉（下面有補丁墊著）"""
    body = O[f"{WHO}_Body"]; me = body.data
    img = body.material_slots[0].material.vrm_addon_extension.mtoon1.pbr_metallic_roughness.base_color_texture.index.source
    if img is None:
        return 0
    W, H = img.size; px = img.pixels[:]
    def tex(uv):
        x = int((uv[0] % 1) * W); y = int((uv[1] % 1) * H); i = (y * W + x) * 4; return px[i:i + 3]
    bm = bmesh.new(); bm.from_mesh(me); uvl = bm.loops.layers.uv.active
    kill = [f for f in bm.faces if f.calc_center_median().z > z_from * S and abs(f.calc_center_median().x) < x_max * S
            and any(sum(tex(l[uvl].uv)) < 0.6 for l in f.loops)]
    bmesh.ops.delete(bm, geom=kill, context="FACES"); bm.to_mesh(me); bm.free()
    return len(kill)


def sample_skin_colors():
    """從身體皮膚貼圖取三個區域的平均色（軀幹、手臂、脖子），補丁用漸層貼圖對齊接縫兩邊的顏色"""
    body = O[f"{WHO}_Body"]; me = body.data; uvl = me.uv_layers.active.data
    img = body.material_slots[0].material.vrm_addon_extension.mtoon1.pbr_metallic_roughness.base_color_texture.index.source
    if img is None:
        return (0.98, 0.917, 0.866), (0.976, 0.902, 0.848), (0.974, 0.892, 0.835)
    W, H = img.size; px = img.pixels[:]
    def avg(cond):
        acc = [0.0, 0.0, 0.0]; n = 0
        for p in me.polygons:
            if cond(p.center):
                for li in p.loop_indices:
                    u, v = uvl[li].uv; i = (int((v % 1) * H) * W + int((u % 1) * W)) * 4; c = px[i:i + 3]
                    if sum(c) > 0.6:
                        acc = [a + b for a, b in zip(acc, c)]; n += 1
        return tuple(a / max(1, n) for a in acc)
    torso = avg(lambda c: abs(c.x) < 0.08 * S and 0.95 * S < c.z < 1.07 * S)
    arm = avg(lambda c: 0.26 * S < abs(c.x) < 0.30 * S and c.z > 1.15 * S)
    neck = avg(lambda c: abs(c.x) < 0.08 * S and 1.3 * S < c.z < 1.36 * S)
    return torso, arm, neck


def _apply(ob, md):
    with bpy.context.temp_override(object=ob, active_object=ob):
        bpy.ops.object.modifier_apply(modifier=md.name)


def finish(ob, near=0.008, far=0.03):
    """接縫法線沿用既有皮膚、從原始網格（_SRC）轉移骨架權重、加骨架修改器"""
    body = O[f"{WHO}_Body"]; src = O[f"{WHO}_SRC"]
    near, far = near * S, far * S
    for md in list(ob.modifiers):
        ob.modifiers.remove(md)
    bvh = skin_bvh(body)
    g = ob.vertex_groups.get("seam_w") or ob.vertex_groups.new(name="seam_w")
    for v in ob.data.vertices:
        d = bvh.find_nearest(v.co)[3]
        w = 1.0 if d <= near else max(0.0, 1 - (d - near) / (far - near))
        g.add([v.index], w * w * (3 - 2 * w), "REPLACE")
    dt = ob.modifiers.new("SeamNormals", "DATA_TRANSFER"); dt.object = body
    dt.use_loop_data = True; dt.data_types_loops = {"CUSTOM_NORMAL"}; dt.loop_mapping = "POLYINTERP_NEAREST"
    dt.vertex_group = "seam_w"
    _apply(ob, dt)
    for vg in list(ob.vertex_groups):
        if vg.name != "seam_w":
            ob.vertex_groups.remove(vg)
    for vg in src.vertex_groups:
        if vg.name not in ob.vertex_groups:
            ob.vertex_groups.new(name=vg.name)
    dw = ob.modifiers.new("Weights", "DATA_TRANSFER"); dw.object = src
    dw.use_vert_data = True; dw.data_types_verts = {"VGROUP_WEIGHTS"}; dw.vert_mapping = "POLYINTERP_NEAREST"
    dw.layers_vgroup_select_src = "ALL"; dw.layers_vgroup_select_dst = "NAME"
    _apply(ob, dw)
    ob.modifiers.new("Armature", "ARMATURE").object = A_
    return ob


def fill_material(ob, colors=None):
    """複製身體皮膚材質，底色/陰影貼圖換成小漸層圖：u＝往手臂、v＝往脖子。法線貼圖拿掉（補丁的 UV 不對應它），輪廓線關掉"""
    body = O[f"{WHO}_Body"]; skin = body.material_slots[0].material
    torso, arm, neck = colors or sample_skin_colors()
    name = f"{WHO}_SkinFill"
    m = bpy.data.materials.get(name) or skin.copy(); m.name = name
    N = 16
    img = bpy.data.images.get(name + "_grad") or bpy.data.images.new(name + "_grad", N, N)
    px = []
    for j in range(N):
        v = j / (N - 1)
        for i in range(N):
            u = i / (N - 1)
            px += [torso[k] * (1 - u) * (1 - v) + arm[k] * u * (1 - v) + neck[k] * v for k in range(3)] + [1.0]
    img.pixels = px; img.pack()
    mt = m.vrm_addon_extension.mtoon1
    mt.pbr_metallic_roughness.base_color_texture.index.source = img
    mt.extensions.vrmc_materials_mtoon.shade_multiply_texture.index.source = img
    mt.normal_texture.index.source = None
    mt.extensions.vrmc_materials_mtoon.outline_width_mode = "none"
    ob.data.materials.clear(); ob.data.materials.append(m)
    uvl = (ob.data.uv_layers.active or ob.data.uv_layers.new(name="UVMap")).data
    def sm(a, b, x):
        t = max(0.0, min(1.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)
    for p in ob.data.polygons:
        for li in p.loop_indices:
            co = ob.data.vertices[ob.data.loops[li].vertex_index].co
            u = sm(0.13 * S, 0.21 * S, abs(co.x)); v = sm(1.29 * S, 1.34 * S, co.z) * (1 - u)
            uvl[li].uv = (0.5 / N + u * (N - 1) / N, 0.5 / N + v * (N - 1) / N)
    return m


def run_fill():
    """一鍵補皮膚。回傳 dict（補丁頂點數、吸附數、刪掉的黑帶面數）"""
    name = f"{WHO}_BodyFill"
    if name in O:
        bpy.data.objects.remove(O[name], do_unlink=True)
    band = delete_dark_band()
    body = O[f"{WHO}_Body"]
    ob = build_blocks(); remesh(ob)
    bvh = skin_bvh(body); trim(ob); snapped = snap_to_skin(ob, bvh)
    ob.name = name
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.parent = A_
    finish(ob); fill_material(ob)
    return dict(verts=len(ob.data.vertices), snapped=snapped, band_faces_removed=band, scale=round(S, 4), bust=BUST)
