# 服裝工具：從身體表面複製一塊、沿法線撐開、修邊，掛到骨架。use("outfit_lib") 載入。
# 座標以預設庫新娘為準，乘 S_BODY（頭骨高/1.386）換算到其他角色。
import bpy, bmesh, math
from mathutils import Vector

O = bpy.data.objects


def mtoon(name, base, shade=None, alpha=None, rim=None):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mt = m.vrm_addon_extension.mtoon1
    mt.enabled = True
    mt.pbr_metallic_roughness.base_color_factor = (*base, alpha if alpha else 1.0)
    mt.extensions.vrmc_materials_mtoon.shade_color_factor = shade or tuple(c * 0.8 for c in base)
    if alpha:
        mt.alpha_mode = "BLEND"
    mt.double_sided = True
    return m


def shell_piece(src, name, keep, offset, mat, arm_name=None):
    """src 的表面留 keep(面中心) 為真的面，沿法線推 offset（可以是函式 f(co)），保留權重"""
    if name in O:
        bpy.data.objects.remove(O[name], do_unlink=True)
    A = O[arm_name or f"{WHO}_Armature"]
    me = src.data.copy(); me.name = name
    ob = bpy.data.objects.new(name, me); A.users_collection[0].objects.link(ob); ob.parent = A
    for g in src.vertex_groups:
        if g.name not in ob.vertex_groups:
            ob.vertex_groups.new(name=g.name)
    if me.shape_keys:
        ob.shape_key_clear()
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not keep(f.calc_center_median())], context="FACES")
    bm.normal_update()
    for v in bm.verts:
        v.co += v.normal * (offset(v.co) if callable(offset) else offset)
    for f in bm.faces:
        f.smooth = True; f.material_index = 0
    bm.to_mesh(me); bm.free()
    me.materials.clear(); me.materials.append(mat)
    ob.modifiers.new("Armature", "ARMATURE").object = A
    return ob


def join(objs, name):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    with bpy.context.temp_override(active_object=objs[0], object=objs[0], selected_objects=objs, selected_editable_objects=objs):
        bpy.ops.object.join()
    objs[0].name = name
    return objs[0]


def clean_cut(ob, planes):
    me = ob.data; bm = bmesh.new(); bm.from_mesh(me)
    for co, n in planes:
        co, n = Vector(co), Vector(n).normalized()
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6, plane_co=co, plane_no=n)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if (f.calc_center_median() - co).dot(n) > 0], context="FACES")
    bm.to_mesh(me); bm.free()


def thicken(ob, t=0.002):
    s = ob.modifiers.new("Thick", "SOLIDIFY"); s.thickness = t; s.offset = -1; s.use_rim = True
    return s


def bone_prop(o, arm, bone):
    """道具黏到骨頭上（保持目前世界位置）"""
    bpy.context.view_layer.update(); mw = o.matrix_world.copy()
    o.parent = arm; o.parent_type = "BONE"; o.parent_bone = bone
    bpy.context.view_layer.update(); o.matrix_world = mw
    return o


S_BODY = bpy.data.objects[f"{WHO}_Armature"].data.bones["J_Bip_C_Head"].head_local.z / 1.386


def make_base_top(color=(0.97, 0.92, 0.91), shade=(0.86, 0.76, 0.78), z0=1.03, z1=1.26, top=1.235):
    """便服上衣（平口貼身小可愛）：從身體＋補皮膚表面撐開 4mm。base 服裝＝這件＋VRoid 原本的短褲＋鞋"""
    S = S_BODY
    mat = mtoon(f"{WHO}_BaseTopMat", color, shade=shade)
    keep = lambda c: z0 * S < c.z < z1 * S and abs(c.x) < 0.16 * S
    parts = [shell_piece(O[f"{WHO}_Body"], f"TMP_{WHO}_top1", keep, 0.004 * S, mat)]
    if f"{WHO}_BodyFill" in O:
        parts.append(shell_piece(O[f"{WHO}_BodyFill"], f"TMP_{WHO}_top2", keep, 0.0045 * S, mat))
    top_ob = join(parts, f"{WHO}_BaseTop") if len(parts) > 1 else parts[0]
    top_ob.name = f"{WHO}_BaseTop"
    clean_cut(top_ob, [((0, 0, top * S), (0, 0.25, 1)), ((0, 0, (z0 + 0.025) * S), (0, 0, -1))])
    thicken(top_ob, 0.0025 * S)
    return top_ob


def sleeve(arm, name, side, r0, r1, r2, x_end_extra, mat, start_back=0.0):
    """程序式袖子（西裝、襯衫）：沿上臂→前臂→手腕的管子，權重分給 UpperArm/LowerArm。r0 肩、r1 手肘、r2 袖口半徑"""
    if name in O:
        bpy.data.objects.remove(O[name], do_unlink=True)
    B = arm.data.bones
    sh, el, wr = (B[f"J_Bip_{side}_{n}"].head_local.copy() for n in ("UpperArm", "LowerArm", "Hand"))
    sgn = 1 if wr.x > 0 else -1
    x0 = sh.x - sgn * start_back; x1 = el.x; x2 = wr.x + sgn * x_end_extra
    bm = bmesh.new(); N = 20; rings = []; weights = []
    for i in range(25):
        x = x0 + (x2 - x0) * i / 24
        t = (x - x0) / (x2 - x0)
        tx = (x - x0) / (x1 - x0) if abs(x - x0) < abs(x1 - x0) else 1 + (x - x1) / (x2 - x1)
        r = r0 + (r1 - r0) * min(1, tx) if tx <= 1 else r1 + (r2 - r1) * (tx - 1)
        zc = sh.z + (wr.z - sh.z) * t; yc = sh.y + (wr.y - sh.y) * t
        rings.append([bm.verts.new((x, yc + math.cos(2 * math.pi * k / N) * r, zc + math.sin(2 * math.pi * k / N) * r)) for k in range(N)])
        wl = min(1, max(0, ((x - x1) * sgn + 0.03) / 0.06))
        weights.append((1 - wl, wl))
    for a_, b_ in zip(rings, rings[1:]):
        for k in range(N):
            bm.faces.new((a_[k], a_[(k + 1) % N], b_[(k + 1) % N], b_[k]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me); arm.users_collection[0].objects.link(ob); ob.parent = arm
    me.materials.append(mat)
    gu = ob.vertex_groups.new(name=f"J_Bip_{side}_UpperArm"); gl = ob.vertex_groups.new(name=f"J_Bip_{side}_LowerArm")
    for i, (wu, wl) in enumerate(weights):
        idx = list(range(i * N, (i + 1) * N))
        if wu > 0: gu.add(idx, wu, "REPLACE")
        if wl > 0: gl.add(idx, wl, "REPLACE")
    ob.modifiers.new("Armature", "ARMATURE").object = arm
    return ob


def v_cut(ob, w0, z0, w1, z1, gap=None, lapel=None, hem=0.0):
    """沿兩條斜線切出前襟 V 字開口（西裝外套）；lapel＝翻領寬度（換第 2 個材質）。參數為新娘座標，自動乘 S_BODY"""
    S = S_BODY
    w0, z0, w1, z1 = w0 * S, z0 * S, w1 * S, z1 * S
    gap = gap * S if gap else None; lapel = lapel * S if lapel else None; hem *= S
    me = ob.data; bm = bmesh.new(); bm.from_mesh(me)
    d = Vector((w1 - w0, 0, z1 - z0)).normalized()
    planes = []
    for sx in (1, -1):
        p0 = Vector((sx * w0, 0, z0)); n = Vector((sx * d.z, 0, -d.x)).normalized()
        if n.x * sx < 0:
            n = -n
        planes.append((p0, n))
    cuts = list(planes)
    if lapel:
        cuts += [(p0 + n * lapel, n) for p0, n in planes]
    if gap:
        cuts += [(Vector((sx * gap, 0, 0)), Vector((sx, 0, 0))) for sx in (1, -1)]
    for p0, n in cuts:
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-5, plane_co=p0, plane_no=n)
    kill, lap = [], []
    for f in bm.faces:
        c = f.calc_center_median()
        if c.y > -0.005:
            continue
        if c.z > z0:
            side = planes[0] if c.x >= 0 else planes[1]
            sd = (c - side[0]).dot(side[1])
            if sd < 0:
                kill.append(f)
            elif lapel and sd < lapel:
                lap.append(f)
        elif gap and abs(c.x) < gap and c.z > hem:
            kill.append(f)
    for f in lap:
        f.material_index = 1
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bm.to_mesh(me); bm.free()


def pinch(ob, zc=1.0, amt=0.07, width=0.07):
    """在高度 zc 附近往內收（腰身）"""
    S = S_BODY; zc *= S; width *= S
    for v in ob.data.vertices:
        k = 1 - amt * math.exp(-((v.co.z - zc) / width) ** 2)
        v.co.x *= k; v.co.y = (v.co.y + 0.005 * S) * k - 0.005 * S
