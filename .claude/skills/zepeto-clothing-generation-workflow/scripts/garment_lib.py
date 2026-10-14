# ZEPETO 穿戴物品的共用工具（在背景 Blender 裡用）：從身體長衣服的基本動作＋各種衣物的「配方」。
# 2026-10-14 起新衣服改走「照參考照刻細節＋寫實布料」：細節配方與材質在 garment_detail.py；這裡的黏土風配方與 material() 留給已定案的舊服裝。
# 每套服裝的 outfit.py 只寫「用哪些配方、參數、顏色」，實際的網格操作都在這裡。
#
# 做法（2026-10-11 新郎西裝實測定下）：
#   每件衣服＝複製身體網格 → 先整件往外推出厚度並抹平 → 再用平面切出範圍（切口才平整）→ Solidify 加厚度
#   → 清掉舊權重、Data Transfer（Nearest Face Interpolated、By Name）從身體重抄 → Armature 修改器。
#   小配件（領結、扣子、口袋、鞋帶）是另外捏的小網格，用射線貼到衣服表面，權重一樣從身體抄。
# 換身形（新娘、其他角色）只要用新的 body.blend 重跑，衣服會重新長出來；所有高度都從骨頭或身體網格量，不寫死。
# 座標：角色面向 −Y、左手 +X、Z 朝上，單位 m。
import bpy, bmesh, math
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

sc = bpy.context.scene
O = bpy.data.objects
body = O["Body"]; arm = O["Body_Armature"]; head = O["Head"]
fr = O.get("Face_Rig")


def bone(n):
    return arm.data.bones[n].head_local.copy()


def rest(on=True):
    arm.data.pose_position = "REST" if on else "POSE"
    bpy.context.view_layer.update()


def smooth_step(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


# ════════ 從身體量出來的基準高度（衣服的位置一律從這裡推，不寫死） ════════
def _crotch_z():
    """身體正中線（|x|<1 cm）最低的點＝胯下高度"""
    zs = [v.co.z for v in body.data.vertices if abs(v.co.x) < 0.01 and v.co.z > 0.3]
    return min(zs)


def _head_seam_z():
    """頭模型切口（藏掉胸像底座後，頭最低的那一圈）的高度。肩膀、脖子骨頭怎麼改，這個高度都不跟著動；領子要蓋過它"""
    rest(True)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = head.evaluated_get(dg); me = ev.to_mesh()
    z = min((head.matrix_world @ v.co).z for v in me.vertices)
    ev.to_mesh_clear()
    rest(False)
    return z


A = dict(
    SH_Z=bone("J_Bip_L_UpperArm").z,          # 肩關節高
    WRIST_X=bone("J_Bip_L_Hand").x,           # T 字站姿的手腕 x
    ANKLE_Z=bone("J_Bip_L_Foot").z,
    NECK_Z=bone("J_Bip_C_Neck").z,
    HIP_Z=bone("J_Bip_L_UpperLeg").z,         # 髖關節高
    FOOT_X=bone("J_Bip_L_Foot").x,
    CROTCH=_crotch_z(),
    SEAM=_head_seam_z(),
)
A["COLLAR_TOP"] = max(A["NECK_Z"] + 0.044, A["SEAM"] + 0.018)   # 有領子的上衣：領子上緣在頭切口上方 1.8 cm
A["SLEEVE_X"] = A["WRIST_X"] - 0.035     # 外套袖口：手腕前 3.5 cm（拇指從靠手腕的掌側長出，切更外面會被拇指根撐皺）
A["CUFF_X"] = A["WRIST_X"] - 0.012       # 襯衫袖口：比外套多露 2.3 cm
A["HEM"] = A["HIP_Z"] - 0.045            # 外套下襬：髖關節下 4.5 cm（不要用胯下，舊版身體胯下曾黏到 0.37 m）


def _armpit_z():
    """腋下高度：T 字站姿上臂（離軀幹外側）最低的點。平口禮服的上緣要在這下面，水平切才不會切到手臂"""
    zs = [v.co.z for v in body.data.vertices if 0.20 < abs(v.co.x) < 0.30 and v.co.z > A["HIP_Z"]]
    return min(zs) if zs else A["SH_Z"] - 0.08


A["ARMPIT"] = _armpit_z()


# ════════ 材質 ════════
def lin(c):
    return tuple(((x / 255) ** 2.2) for x in c) + (1,)


def material(name, rgb, rough, sheen=0.0, coat=0.0, metallic=0.0, alpha=1.0):
    """黏土風布料：霧面為主（粗糙度 0.65～0.85，和大頭的 0.75 對齊）；緞面用 Sheen 柔光、皮鞋與飾品用 Coat。rgb 是 sRGB 0～255"""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    p.inputs["Base Color"].default_value = lin(rgb)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metallic
    if sheen:
        p.inputs["Sheen Weight"].default_value = sheen
        p.inputs["Sheen Roughness"].default_value = 0.5
    if coat:
        p.inputs["Coat Weight"].default_value = coat
        p.inputs["Coat Roughness"].default_value = 0.25
    if alpha < 1.0:
        p.inputs["Alpha"].default_value = alpha
    return m


# ════════ 網格基本動作 ════════
def body_copy(name):
    me = body.data.copy(); me.name = name
    o = O.new(name, me); sc.collection.objects.link(o)
    o.matrix_world = body.matrix_world.copy()
    o.data.materials.clear()
    for m in list(o.modifiers):
        o.modifiers.remove(m)
    return o


def open_bm(o):
    bm = bmesh.new(); bm.from_mesh(o.data)
    return bm


def close_bm(o, bm):
    bm.to_mesh(o.data); bm.free()


def cut(bm, co, no):
    """切開並丟掉 no 指向的那一側"""
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co, plane_no=no, clear_outer=True)


def cut_sleeves(bm, x):
    """袖口：|x| 超過 x 的手臂部分切掉（左右各一刀）"""
    cut(bm, (x, 0, 0), (1, 0, 0)); cut(bm, (-x, 0, 0), (-1, 0, 0))


def cut_neck(bm, z, r=0.08):
    """只切掉脖子那一圈（|x|<r）高於 z 的部分；T 字站姿時上臂頂端比領口高，不能整個水平面切"""
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, z), plane_no=(0, 0, 1))
    delete_faces(bm, lambda c: c.z > z and abs(c.x) < r)


def delete_faces(bm, pred):
    kill = [f for f in bm.faces if pred(f.calc_center_median())]
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")


def drop_loose(bm, keep_fn):
    """只留中心點符合 keep_fn(中心, 面數) 的連通塊（例如把手、腿切下來的碎塊丟掉）"""
    bm.faces.ensure_lookup_table()
    seen, parts = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack, part = [f], []
        seen.add(f.index)
        while stack:
            g = stack.pop(); part.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index); stack.append(h)
        parts.append(part)
    kill = []
    for part in parts:
        c = sum((f.calc_center_median() for f in part), Vector()) / len(part)
        if not keep_fn(c, len(part)):
            kill += part
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")


def inflate(bm, off_fn, smooth=4):
    """沿法線往外推 off_fn(位置) 公尺，再抹平。一定要在切之前做：反過來做，切口的點抹不到，邊緣會鋸齒"""
    # 切口會留下極細的三角面，加厚度時會被放大成尖刺 → 先合併太近的點、清掉退化面
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.0008)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=0.0008)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.normal_update()
    offs = [(v, v.normal.copy() * off_fn(v.co)) for v in bm.verts]
    for v, d in offs:
        v.co += d
    inner = [v for v in bm.verts if not v.is_boundary]
    for _ in range(smooth):
        bmesh.ops.smooth_vert(bm, verts=inner, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)


def piecewise(pts, z):
    """pts＝[(z, 半寬), ...]，z 由高到低；回傳 z 處的半寬（線性內插）"""
    if z >= pts[0][0]:
        return pts[0][1]
    for (z0, w0), (z1, w1) in zip(pts, pts[1:]):
        if z1 <= z <= z0:
            return w1 + (w0 - w1) * (z - z1) / (z0 - z1)
    return pts[-1][1]


def bisect_polyline(bm, pts):
    """沿 (z, 半寬) 折線的每一段、左右各切一刀（不丟任何一邊），之後依面中心挖洞或上色，切口才平整"""
    for (z0, w0), (z1, w1) in zip(pts, pts[1:]):
        for sg in (1, -1):
            d = Vector((sg * (w1 - w0), 0, z1 - z0))
            n = Vector((d.z, 0, -d.x)).normalized()
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(sg * w0, 0, z0), plane_no=n)


# ════════ 收尾：加厚度、綁骨架 ════════
def transfer_weights(o, drop=()):
    """清掉舊權重 → Data Transfer（Nearest Face Interpolated、By Name）從身體重抄 → Armature。身體在靜止姿勢下抄。
    drop＝骨頭名稱含這些字的群組只留 25%、其餘轉給胸口（例：平口上緣舉手時不要被肩膀、上臂拉走）"""
    rest(True)
    for m in list(o.modifiers):
        o.modifiers.remove(m)
    o.vertex_groups.clear()
    # 只建「骨頭」的頂點群組：身體上的 HAND_DQS（手的保留體積修改器用）、Hide_Under_Outfit 都不是骨頭，不能抄到衣服上
    for g in body.vertex_groups:
        if g.name in arm.data.bones:
            o.vertex_groups.new(name=g.name)
    dt = o.modifiers.new("Weights", "DATA_TRANSFER")
    dt.object = body; dt.use_object_transform = True
    dt.use_vert_data = True; dt.data_types_verts = {"VGROUP_WEIGHTS"}
    dt.vert_mapping = "POLYINTERP_NEAREST"
    dt.layers_vgroup_select_src = "ALL"; dt.layers_vgroup_select_dst = "NAME"
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.select_all(action="DESELECT"); o.select_set(True)
    bpy.ops.object.modifier_apply(modifier="Weights")
    if drop:
        # 不直接刪（只綁手臂的點會變成沒權重、停在 T 字原地）：手臂權重只留 25%，其餘 75% 轉給胸口骨頭
        chest_name = next((n for n in ("J_Bip_C_UpperChest", "J_Bip_C_Chest", "J_Bip_C_Spine") if n in arm.data.bones), None)
        chest = o.vertex_groups.get(chest_name) or o.vertex_groups.new(name=chest_name)
        idx = {g.index for g in o.vertex_groups if any(k in g.name for k in drop)}
        for v in o.data.vertices:
            moved = 0.0
            for ge in v.groups:
                if ge.group in idx:
                    moved += ge.weight * 0.75; ge.weight *= 0.25
            if moved:
                chest.add([v.index], moved, "ADD")
    bpy.ops.object.vertex_group_clean(group_select_mode="ALL", limit=0.01)
    bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
    bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    o.parent = arm; o.matrix_parent_inverse = arm.matrix_world.inverted()
    a = o.modifiers.new("Armature", "ARMATURE"); a.object = arm
    rest(False)


LIVE_SOLIDIFY = False   # True＝厚度在骨架變形「之後」才加（不套用）。手臂放下時肩膀擠壓，先加厚的內層會從外層戳出成碎片；outfit.py 在 build() 開頭設


def finish(o, mats, thick, rim=True, drop=()):
    """加 Solidify 厚度（往內長，外觀尺寸不變）→ 平滑著色 → 綁骨架"""
    for m in mats:
        o.data.materials.append(m)
    if LIVE_SOLIDIFY:
        for p in o.data.polygons:
            p.use_smooth = True
        transfer_weights(o, drop)
        sol = o.modifiers.new("Thickness", "SOLIDIFY")          # 排在 Armature 後面
        sol.thickness = thick; sol.offset = -1.0; sol.use_rim = rim; sol.use_even_offset = False
        return o
    sol = o.modifiers.new("Thickness", "SOLIDIFY")
    sol.thickness = thick; sol.offset = -1.0; sol.use_rim = rim; sol.use_even_offset = False
    sol.material_offset_rim = 0
    for p in o.data.polygons:
        p.use_smooth = True
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.select_all(action="DESELECT"); o.select_set(True)
    bpy.ops.object.modifier_apply(modifier="Thickness")
    transfer_weights(o, drop)
    return o


def finish_small(name, bm, mat, subsurf=0):
    """小配件：bmesh → 物件 → （選用）細分圓角 → 平滑著色 → 綁骨架"""
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = O.new(name, me); sc.collection.objects.link(o)
    o.data.materials.append(mat)
    if subsurf:
        mod = o.modifiers.new("Round", "SUBSURF"); mod.levels = subsurf
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.select_all(action="DESELECT"); o.select_set(True)
        bpy.ops.object.modifier_apply(modifier="Round")
    for f in o.data.polygons:
        f.use_smooth = True
    transfer_weights(o)
    return o


def surface_front(obj, x, z, normal=False):
    """從正前方打射線到 obj（靜止姿勢、已套修改器）表面，回傳交點（normal=True 時連法線一起回傳）"""
    rest(True)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg); me = ev.to_mesh()
    bvh = BVHTree.FromPolygons([obj.matrix_world @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons])
    ev.to_mesh_clear()
    hit = bvh.ray_cast(Vector((x, -1.0, z)), Vector((0, 1, 0)))
    rest(False)
    return (hit[0], hit[1]) if normal else hit[0]


def blob(bm, c, s, rot_y=0.0, u=20, v=12):
    """扁橢球（領結翼、扣子、珍珠用）"""
    r = bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)
    M = Matrix.Translation(c) @ Matrix.Rotation(rot_y, 4, "Y") @ Matrix.Diagonal((s[0], s[1], s[2], 1))
    bmesh.ops.transform(bm, matrix=M, verts=r["verts"])


# ════════ 配方：上身 ════════
def shirt(name, mat, collar_top=None, cuff_x=None, show=None, collar_thick=0.011):
    """有領襯衫。立領蓋住頭切口。show(中心)→True 的面才保留（只做會露出來的部分，被外套蓋住的不做，動作時才不會從外套底下冒出來）；
    show=None＝整件都做（單穿時）"""
    collar_top = collar_top or A["COLLAR_TOP"]; cuff_x = cuff_x or A["CUFF_X"]
    o = body_copy(name); bm = open_bm(o)
    # 立領：從領子上緣往下 5.5 cm 開始變厚
    inflate(bm, lambda p: 0.005 + collar_thick * smooth_step(collar_top - 0.055, collar_top - 0.03, p.z) * smooth_step(0.085, 0.065, abs(p.x)), smooth=6)
    cut_neck(bm, collar_top)
    cut(bm, (0, 0, A["HIP_Z"] - 0.06), (0, 0, -1))
    cut_sleeves(bm, cuff_x)
    if show:
        delete_faces(bm, lambda c: not show(c))
    drop_loose(bm, lambda c, n: n > 200)
    close_bm(o, bm)
    return finish(o, [mat], 0.004)


def jacket(name, mat, lapel_mat=None, top=None, hem=None, sleeve_x=None, open_pts=None, lapel_pts=None, break_z=None, flare=0.006):
    """西裝外套。open_pts＝前襟開口的 (z, 半寬) 折線（None＝不開口）；lapel_pts＋break_z＝領片範圍（翻折線以上），用 lapel_mat 上色、再外推 3 mm"""
    top = top or A["COLLAR_TOP"] - 0.035; hem = hem or A["HEM"]; sleeve_x = sleeve_x or A["SLEEVE_X"]
    o = body_copy(name); bm = open_bm(o)
    cut(bm, (0, 0, hem - 0.08), (0, 0, -1))              # 先粗切掉腿（省時間），推厚抹平後再精切

    def off(p):
        o_ = 0.016 + flare * smooth_step(0.85, 0.65, p.z)          # 下襬略往外張
        o_ -= 0.004 * smooth_step(top - 0.035, top, p.z)           # 領口收一點
        return o_
    inflate(bm, off, smooth=14)
    cut_neck(bm, top)
    cut(bm, (0, 0, hem), (0, 0, -1))
    cut_sleeves(bm, sleeve_x)
    drop_loose(bm, lambda c, n: abs(c.x) < 0.3 or n > 2000)
    mats = [mat]
    if open_pts:
        bisect_polyline(bm, open_pts)
        if lapel_pts:
            bisect_polyline(bm, lapel_pts)
        delete_faces(bm, lambda c: c.y < 0 and abs(c.x) < piecewise(open_pts, c.z))
    if lapel_pts:
        mats.append(lapel_mat or mat)
        lap_v = set()
        for f in bm.faces:
            c = f.calc_center_median()
            if c.y < 0 and c.z > break_z and abs(c.x) < piecewise(lapel_pts, c.z):
                f.material_index = 1; lap_v.update(f.verts)
        bm.normal_update()
        for v in lap_v:
            v.co += v.normal * 0.003
    close_bm(o, bm)
    return finish(o, mats, 0.007)


def vest_front(name, mat, top, v_bottom, hem, half_w=0.13, neck_w=0.060):
    """背心前片（後片被外套整個蓋住，不做）。V 領從 top（半寬 neck_w）收到 v_bottom"""
    o = body_copy(name); bm = open_bm(o)
    cut(bm, (0, 0, hem - 0.08), (0, 0, -1))
    inflate(bm, lambda p: 0.008, smooth=12)
    cut_neck(bm, top)
    cut(bm, (0, 0, hem), (0, 0, -1))
    delete_faces(bm, lambda c: not (c.y < 0.01 and abs(c.x) < half_w))
    drop_loose(bm, lambda c, n: n > 500)
    pts = [(top, neck_w), (v_bottom, 0.004)]
    bisect_polyline(bm, pts)
    delete_faces(bm, lambda c: c.y < 0 and c.z > v_bottom and abs(c.x) < piecewise(pts, c.z))
    close_bm(o, bm)
    return finish(o, [mat], 0.004)


# ════════ 配方：下身 ════════
def trousers(name, mat, waist=0.74, hem=None, flare=0.010):
    """長褲：腰到腳踝上方，褲管下段略寬（直筒）"""
    hem = hem or A["ANKLE_Z"] + 0.045
    o = body_copy(name); bm = open_bm(o)
    cut(bm, (0, 0, waist + 0.08), (0, 0, 1))
    drop_loose(bm, lambda c, n: n > 500)
    inflate(bm, lambda p: 0.008 + flare * smooth_step(0.40, 0.12, p.z), smooth=8)
    cut(bm, (0, 0, waist), (0, 0, 1))
    cut(bm, (0, 0, hem), (0, 0, -1))
    close_bm(o, bm)
    return finish(o, [mat], 0.005)


# ════════ 配方：鞋 ════════
def shoes(name, mat, top=None, toe=0.015):
    """包鞋：腳整個包住、鞋頭往前拉 toe 公尺、鞋底壓平。腳只做到圓圓一塊，鞋子一定要整個包住"""
    top = top or A["ANKLE_Z"] + 0.075
    o = body_copy(name); bm = open_bm(o)
    cut(bm, (0, 0, top), (0, 0, 1))
    drop_loose(bm, lambda c, n: n > 50)
    inflate(bm, lambda p: 0.010 + 0.004 * smooth_step(0.02, -0.005, p.z), smooth=6)
    for v in bm.verts:
        if v.co.y < -0.02:
            v.co.y -= toe * smooth_step(-0.02, -0.07, v.co.y)
        if v.co.z < 0.0:
            v.co.z = max(v.co.z, -0.004)
    close_bm(o, bm)
    return finish(o, [mat], 0.004)


def laces(name, mat, shoe_obj, ys=(-0.048, -0.061, -0.074)):
    """綁帶鞋的鞋帶：每隻鞋腳背上幾條橫向細圓條。褲管蓋到腳背約 y −0.04，鞋帶要排在它前面才看得到"""
    rest(True)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = shoe_obj.evaluated_get(dg); me = ev.to_mesh()
    bvh = BVHTree.FromPolygons([shoe_obj.matrix_world @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons])
    ev.to_mesh_clear()
    rest(False)
    bm = bmesh.new()
    for sx in (1, -1):
        for k, y in enumerate(ys):
            hit = bvh.ray_cast(Vector((sx * A["FOOT_X"], y, 0.5)), Vector((0, 0, -1)))
            if hit[0] is None:
                continue
            g = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.0028, radius2=0.0028, depth=0.024 - 0.004 * k)
            bmesh.ops.transform(bm, matrix=Matrix.Translation(hit[0] + Vector((0, 0, 0.0015))) @ Matrix.Rotation(math.pi / 2, 4, "Y"), verts=g["verts"])
    return finish_small(name, bm, mat)


# ════════ 配方：小配件 ════════
def bowtie(name, mat, on_obj, z=None, wing=(0.033, 0.011, 0.024)):
    """領結：中間一個結＋左右兩翼，貼在 on_obj（通常是襯衫）領口正前方"""
    z = z or A["COLLAR_TOP"] - 0.035
    c = surface_front(on_obj, 0.0, z) + Vector((0, -0.012, 0))
    bm = bmesh.new()
    blob(bm, c, (0.012, 0.010, 0.012))
    blob(bm, c + Vector((wing[0], 0.002, 0)), wing, 0.15)
    blob(bm, c + Vector((-wing[0], 0.002, 0)), wing, -0.15)
    return finish_small(name, bm, mat)


def collar_tips(name, mat, on_obj, z=None):
    """襯衫尖角翻領：領口兩側往外下方斜出的兩個圓角三角片"""
    z = z or A["COLLAR_TOP"] - 0.035
    p = surface_front(on_obj, 0.0, z)
    bm = bmesh.new()
    for sg in (1, -1):
        r = bmesh.ops.create_cone(bm, cap_ends=True, segments=3, radius1=0.022, radius2=0.002, depth=0.052)
        M = (Matrix.Translation(p + Vector((sg * 0.034, -0.007, -0.024))) @ Matrix.Rotation(sg * 0.65, 4, "Y")
             @ Matrix.Rotation(math.pi, 4, "X") @ Matrix.Diagonal((1.0, 0.25, 1.0, 1)))
        bmesh.ops.transform(bm, matrix=M, verts=r["verts"])
    return finish_small(name, bm, mat, subsurf=2)


def buttons(name, mat, on_obj, zs, x=0.0, size=(0.008, 0.004, 0.008)):
    """一排扣子：在 on_obj 正前方 x 處、每個 z 一顆"""
    bm = bmesh.new()
    for z in zs:
        p = surface_front(on_obj, x, z)
        r = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=1.0)
        bmesh.ops.transform(bm, matrix=Matrix.Translation(p + Vector((0, -0.002, 0))) @ Matrix.Diagonal((*size, 1)), verts=r["verts"])
    return finish_small(name, bm, mat)


def patches(name, mat, on_obj, specs):
    """貼在表面的圓角扁方塊（口袋袋蓋、胸袋、名牌…）。specs＝[(x, z, (半寬, 半厚, 半高)), ...]"""
    bm = bmesh.new()
    for x, z, half in specs:
        loc, nrm = surface_front(on_obj, x, z, normal=True)
        before = set(bm.verts)
        bmesh.ops.create_cube(bm, size=2.0)
        new_v = [v for v in bm.verts if v not in before]
        bmesh.ops.bevel(bm, geom=list({e for v in new_v for e in v.link_edges}), offset=0.3, segments=3, affect="EDGES", profile=0.5)
        new_v = [v for v in bm.verts if v not in before]
        rot = Vector((0, -1, 0)).rotation_difference(nrm).to_matrix().to_4x4()
        bmesh.ops.transform(bm, matrix=Matrix.Translation(loc + nrm * half[1]) @ rot @ Matrix.Diagonal((*half, 1)), verts=new_v)
    return finish_small(name, bm, mat)


# ════════ 配方：禮服（平口上身、旋轉體裙子、腰帶、花） ════════
def _section_radius(obj_or_body, z, n=72, cy=None):
    """在高度 z 量水平剖面：從中心往 n 個方向打射線，回傳 [(角度, 半徑)] 與中心 y。角度 0＝正前方（−Y），往 +X（角色左手）轉"""
    rest(True)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj_or_body.evaluated_get(dg); me = ev.to_mesh()
    mw = obj_or_body.matrix_world
    pts = [mw @ v.co for v in me.vertices]
    bvh = BVHTree.FromPolygons(pts, [p.vertices[:] for p in me.polygons])
    ev.to_mesh_clear()
    rest(False)
    if cy is None:
        ys = [p.y for p in pts if abs(p.z - z) < 0.01 and abs(p.x) < 0.04]
        cy = (min(ys) + max(ys)) / 2 if ys else 0.0
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        d = Vector((math.sin(a), -math.cos(a), 0))
        far = Vector((0, cy, z)) + d * 0.6
        hit = bvh.ray_cast(far, -d)          # 從外往內打，拿到最外層表面
        out.append((a, (hit[0] - Vector((0, cy, z))).length if hit[0] else 0.1))
    return out, cy


def _ring_mesh(rows, n, closed_bottom=False):
    """rows＝每一圈 n 個點（由上往下）→ bmesh 管狀面"""
    bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in row] for row in rows]
    for r in range(len(vs) - 1):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((vs[r][i], vs[r][j], vs[r + 1][j], vs[r + 1][i]))
    bm.normal_update()
    return bm


def bind_skirt(o, waist, hem, leg_share=0.55):
    """裙子類（不從腿複製的）自訂權重：上緣全給骨盆，越往下越多分給同側大腿；正前正後兩腿各半。
    走路時裙擺跟著腿前後擺一點，但不會像褲管一樣分成兩條"""
    rest(True)
    for m in list(o.modifiers):
        o.modifiers.remove(m)
    o.vertex_groups.clear()
    names = [n for n in ("J_Bip_C_Hips", "J_Bip_L_UpperLeg", "J_Bip_R_UpperLeg") if n in arm.data.bones]
    hips, gl, gr = (o.vertex_groups.new(name=n) for n in names)
    for v in o.data.vertices:
        c = o.matrix_world @ v.co
        t = smooth_step(waist, hem, c.z) ** 1.3 * leg_share
        side = smooth_step(-0.08, 0.08, c.x)          # +X＝角色左邊
        hips.add([v.index], 1.0 - t, "REPLACE")
        gl.add([v.index], t * side, "REPLACE")
        gr.add([v.index], t * (1 - side), "REPLACE")
    o.parent = arm; o.matrix_parent_inverse = arm.matrix_world.inverted()
    a = o.modifiers.new("Armature", "ARMATURE"); a.object = arm
    rest(False)


NO_ARM = ("Shoulder", "UpperArm", "LowerArm", "Hand")   # 平口上緣：舉手時不被肩膀、上臂拉上去


def strapless_bodice(name, mat, top=None, hem=None):
    """平口上身：從身體複製，上緣切在腋下 top（水平切，手臂在上面不會被切到），下緣到 hem（裙子腰線下一點，被裙子蓋住）"""
    top = top or A["ARMPIT"] - 0.012; hem = hem or A["HIP_Z"] + 0.02
    o = body_copy(name); bm = open_bm(o)
    cut(bm, (0, 0, hem - 0.08), (0, 0, -1))
    cut(bm, (0, 0, top + 0.05), (0, 0, 1))
    drop_loose(bm, lambda c, n: abs(c.x) < 0.2 and n > 500)
    inflate(bm, lambda p: 0.007, smooth=12)
    cut(bm, (0, 0, top), (0, 0, 1))
    cut(bm, (0, 0, hem), (0, 0, -1))
    drop_loose(bm, lambda c, n: abs(c.x) < 0.2 and n > 500)
    close_bm(o, bm)
    return finish(o, [mat], 0.004, drop=NO_ARM)


def petal_neckline(name, mat, on_obj, z=None, lobes=7, height=0.035, flare=0.018, n=96):
    """平口上緣的花瓣褶邊：沿上身上緣一圈往外上方翻開的帶子，上緣做成 lobes 個圓弧花瓣（照片的立體摺紗）"""
    z = z or A["ARMPIT"] - 0.012
    sec, cy = _section_radius(on_obj, z - 0.006, n)
    rows = []
    for k in range(6):
        u = k / 5
        row = []
        for a, r in sec:
            wave = 0.5 + 0.5 * math.cos(lobes * a)
            zz = z - 0.022 + u * (height + 0.012 * wave)
            rr = r + 0.002 + flare * u ** 1.6 * (0.6 + 0.4 * wave)
            row.append(Vector((math.sin(a) * rr, cy - math.cos(a) * rr, zz)))
        rows.append(row)
    bm = _ring_mesh(rows[::-1], n)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = O.new(name, me); sc.collection.objects.link(o)
    return finish(o, [mat], 0.003, drop=NO_ARM)


def lathe_skirt(name, mat, waist, hem, r_hem, bell=2.2, waist_ease=0.012, lobes=0, lobe_amp=0.0, lobe_lift=0.0,
                rows=28, n=96, cy=None, leg_share=0.55):
    """旋轉體裙子（不從腿複製）：上緣貼著身體腰圍 + waist_ease，往下照鐘形 bell 張到 r_hem（越大越早張開＝蓬裙）。
    lobes＞0 時下襬做成波浪花瓣（外層紗、荷葉邊）：半徑起伏 lobe_amp、下襬往上收 lobe_lift"""
    sec, cy0 = _section_radius(body, waist, n)
    cy = cy0 if cy is None else cy
    out = []
    for k in range(rows + 1):
        t = k / rows
        zz = waist + (hem - waist) * t
        shape = 1 - (1 - t) ** bell
        row = []
        for a, r in sec:
            w = 0.5 + 0.5 * math.cos(lobes * a) if lobes else 1.0
            rr = (r + waist_ease) * (1 - shape) + (r_hem + lobe_amp * w * t) * shape
            z2 = zz + (lobe_lift * (1 - w) * t ** 3 if lobes else 0.0)
            row.append(Vector((math.sin(a) * rr, cy - math.cos(a) * rr, z2)))
        out.append(row)
    bm = _ring_mesh(out, n)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = O.new(name, me); sc.collection.objects.link(o)
    o.data.materials.append(mat)
    sol = o.modifiers.new("Thickness", "SOLIDIFY"); sol.thickness = 0.004; sol.offset = -1.0
    mod = o.modifiers.new("Round", "SUBSURF"); mod.levels = 1
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.select_all(action="DESELECT"); o.select_set(True)
    bpy.ops.object.modifier_apply(modifier="Thickness"); bpy.ops.object.modifier_apply(modifier="Round")
    for p in o.data.polygons:
        p.use_smooth = True
    bind_skirt(o, waist, hem, leg_share)
    return o


def sash(name, mat, z, width=0.03, ease=0.016, n=96):
    """腰帶：腰圍外一圈扁帶"""
    sec, cy = _section_radius(body, z, n)
    rows = [[Vector((math.sin(a) * (r + ease), cy - math.cos(a) * (r + ease), z + dz)) for a, r in sec]
            for dz in (width / 2, -width / 2)]
    bm = _ring_mesh(rows, n)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = O.new(name, me); sc.collection.objects.link(o)
    return finish(o, [mat], 0.004)


def rosette(name, mat, on_obj, x, z, size=0.03, petals=7):
    """布花：貼在 on_obj 正前方的一圈扁花瓣＋中心捲（黏土風大形，不做細摺）"""
    loc, nrm = surface_front(on_obj, x, z, normal=True)
    bm = bmesh.new()
    rot = Vector((0, -1, 0)).rotation_difference(nrm).to_matrix().to_4x4()
    base = Matrix.Translation(loc + nrm * size * 0.25) @ rot
    for i in range(petals):
        a = 2 * math.pi * i / petals
        before = set(bm.verts)
        blob(bm, Vector((0, 0, 0)), (size * 0.5, size * 0.22, size * 0.32))
        new_v = [v for v in bm.verts if v not in before]
        M = base @ Matrix.Rotation(a, 4, "Y") @ Matrix.Translation(Vector((size * 0.45, 0, 0))) @ Matrix.Rotation(0.5, 4, "Z")
        bmesh.ops.transform(bm, matrix=M, verts=new_v)
    before = set(bm.verts)
    blob(bm, Vector((0, 0, 0)), (size * 0.35, size * 0.35, size * 0.35))
    bmesh.ops.transform(bm, matrix=base @ Matrix.Translation(Vector((0, -size * 0.15, 0))), verts=[v for v in bm.verts if v not in before])
    return finish_small(name, bm, mat)


def surface_back(obj, x, z, normal=False):
    """同 surface_front，但從正後方（+Y）打過去"""
    rest(True)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg); me = ev.to_mesh()
    bvh = BVHTree.FromPolygons([obj.matrix_world @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons])
    ev.to_mesh_clear()
    hit = bvh.ray_cast(Vector((x, 1.0, z)), Vector((0, -1, 0)))
    rest(False)
    return (hit[0], hit[1]) if normal else hit[0]


def bind_rigid(o, bone_name):
    """整個物件只跟一根骨頭（耳環→頭）。頭不是身體網格，不能從身體抄權重"""
    for m in list(o.modifiers):
        o.modifiers.remove(m)
    o.vertex_groups.clear()
    g = o.vertex_groups.new(name=bone_name)
    g.add([v.index for v in o.data.vertices], 1.0, "REPLACE")
    o.parent = arm; o.matrix_parent_inverse = arm.matrix_world.inverted()
    a = o.modifiers.new("Armature", "ARMATURE"); a.object = arm


def back_bow(name, mat, on_obj, z, size=0.07, tail=0.22, drape_obj=None):
    """背後大蝴蝶結：貼在 on_obj（腰帶）正後方。左右兩個往外上翹的大圈＋中間結＋兩條往下垂的長尾巴。
    drape_obj（通常是外層裙）給了的話，尾巴沿著它的背面表面往下貼（裙子往外張，直直垂會埋進裙子裡）"""
    p = surface_back(on_obj, 0.0, z) + Vector((0, size * 0.18, 0))
    bm = bmesh.new()
    blob(bm, p + Vector((0, size * 0.05, 0)), (size * 0.22, size * 0.20, size * 0.26))                 # 結
    for sg in (1, -1):
        blob(bm, p + Vector((sg * size * 0.55, size * 0.06, size * 0.12)), (size * 0.55, size * 0.18, size * 0.36), sg * 0.35)   # 圈
    bow = finish_small(name, bm, mat, subsurf=1)
    if not drape_obj:
        return bow
    # 尾巴：沿 drape_obj 背面一條條往下取點，做成有厚度的帶子，下端略往外撇
    rest(True)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = drape_obj.evaluated_get(dg); me = ev.to_mesh()
    bvh = BVHTree.FromPolygons([drape_obj.matrix_world @ v.co for v in me.vertices], [q.vertices[:] for q in me.polygons])
    ev.to_mesh_clear()
    rest(False)
    tb = bmesh.new()
    steps = 14; w = size * 0.42
    for sg in (1, -1):
        rows = []
        for k in range(steps + 1):
            t = k / steps
            zz = z - size * 0.15 - tail * t
            xc = sg * (size * 0.22 + size * 0.45 * t)
            row = []
            for dx in (-w / 2, w / 2):
                hit = bvh.ray_cast(Vector((xc + dx * (1 + 0.4 * t), 1.0, zz)), Vector((0, -1, 0)))
                q = hit[0] if hit[0] else Vector((xc + dx, p.y, zz))
                row.append(tb.verts.new(q + Vector((0, 0.006, 0))))
            rows.append(row)
        for k in range(steps):
            tb.faces.new((rows[k][0], rows[k][1], rows[k + 1][1], rows[k + 1][0]))
    me = bpy.data.meshes.new(name + "Tails"); tb.to_mesh(me); tb.free()
    o = O.new(name + "Tails", me); sc.collection.objects.link(o)
    o.data.materials.append(mat)
    sol = o.modifiers.new("Thickness", "SOLIDIFY"); sol.thickness = 0.005; sol.offset = 1.0
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.select_all(action="DESELECT"); o.select_set(True)
    bpy.ops.object.modifier_apply(modifier="Thickness")
    for f in o.data.polygons:
        f.use_smooth = True
    # 尾巴跟著外層裙動：直接抄它的權重（裙子是自訂權重，不是身體）
    o.parent = arm; o.matrix_parent_inverse = arm.matrix_world.inverted()
    for g in drape_obj.vertex_groups:
        o.vertex_groups.new(name=g.name)
    dt = o.modifiers.new("Weights", "DATA_TRANSFER")
    dt.object = drape_obj; dt.use_object_transform = True
    dt.use_vert_data = True; dt.data_types_verts = {"VGROUP_WEIGHTS"}
    dt.vert_mapping = "POLYINTERP_NEAREST"
    dt.layers_vgroup_select_src = "ALL"; dt.layers_vgroup_select_dst = "NAME"
    rest(True)
    bpy.ops.object.modifier_apply(modifier="Weights")
    rest(False)
    am = o.modifiers.new("Armature", "ARMATURE"); am.object = arm
    return [bow, o]


def _ear_lobes():
    """兩邊耳垂的位置。有獨立的 Ears 物件（可動臉產線的頭）就用它每邊最低的點；
    沒有才退回「頭網格左右最外側那一圈的最低點」（長髮會蓋過耳朵、被當成最外側，所以 Ears 優先）"""
    src = O.get("Ears") or head
    rest(True)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = src.evaluated_get(dg); me = ev.to_mesh()
    pts = [src.matrix_world @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    rest(False)
    if src is not head:
        return {sg: min((p for p in pts if p.x * sg > 0), key=lambda p: p.z) for sg in (1, -1)}
    zmin = min(p.z for p in pts); zmax = max(p.z for p in pts)
    band = [p for p in pts if zmin + 0.15 * (zmax - zmin) < p.z < zmin + 0.6 * (zmax - zmin)]
    out = {}
    for sg in (1, -1):
        side = [p for p in band if p.x * sg > 0]
        xm = max(abs(p.x) for p in side)
        ear = [p for p in side if abs(p.x) > xm - 0.012]
        out[sg] = min(ear, key=lambda p: p.z)
    return out


def flower_earrings(name, mat, center_mat=None, size=0.016, drop=0.010, petals=5):
    """花形耳環：耳垂下方一朵朝外的扁花（petals 瓣）＋中心珠。尺寸刻意放大，遠景才看得到。只跟頭骨頭"""
    lobes = _ear_lobes()
    bm = bmesh.new()
    for sg, lobe in lobes.items():
        c = lobe + Vector((sg * 0.004, 0, -drop))
        base = Matrix.Translation(c) @ Matrix.Rotation(sg * math.pi / 2, 4, "Z")     # 花面朝外（±X）
        for i in range(petals):
            a = 2 * math.pi * i / petals
            before = set(bm.verts)
            blob(bm, Vector((0, 0, 0)), (size * 0.32, size * 0.10, size * 0.55), u=12, v=8)
            new_v = [v for v in bm.verts if v not in before]
            bmesh.ops.transform(bm, matrix=base @ Matrix.Rotation(a, 4, "Y") @ Matrix.Translation(Vector((0, 0, size * 0.5))), verts=new_v)
        blob(bm, c + Vector((sg * size * 0.12, 0, 0)), (size * 0.22, size * 0.22, size * 0.22), u=12, v=8)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = O.new(name, me); sc.collection.objects.link(o)
    o.data.materials.append(mat)
    for f in o.data.polygons:
        f.use_smooth = True
    hb = next(n for n in ("J_Bip_C_Head", "mixamorig:Head", "Head") if n in arm.data.bones)
    bind_rigid(o, hb)
    return o


def smooth_weights(objs, repeat=8, factor=0.5):
    """把衣服的權重抹勻：權重在肩膀上方變化太急，手臂放下時布會折成碎片。抹勻後再 normalize"""
    import numpy as np
    for o in objs:
        me = o.data; n = len(me.vertices); G_ = len(o.vertex_groups)
        W = np.zeros((n, G_))
        for v in me.vertices:
            for ge in v.groups:
                W[v.index, ge.group] = ge.weight
        e = np.array([ed.vertices[:] for ed in me.edges])
        deg = np.bincount(e.ravel(), minlength=n).astype(float)[:, None]
        for _ in range(repeat):                                   # 背景模式不能用 vertex_group_smooth 運算子（poll 失敗），自己算鄰點平均
            acc = np.zeros_like(W)
            np.add.at(acc, e[:, 0], W[e[:, 1]]); np.add.at(acc, e[:, 1], W[e[:, 0]])
            W = (1 - factor) * W + factor * np.where(deg > 0, acc / np.maximum(deg, 1), W)
        for gi, g in enumerate(o.vertex_groups):
            col = W[:, gi]
            idx = np.nonzero(col > 0.001)[0]
            g.remove(list(range(n)))
            for i in idx:
                g.add([int(i)], float(col[i]), "REPLACE")
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.select_all(action="DESELECT"); o.select_set(True)
        bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
        bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    return objs


def corrective_smooth(objs, iterations=8):
    """骨架變形後再做一次「修正平滑」：手臂從 T 字放下時，肩膀上方推厚過的布會擠成皺摺碎片，這個修改器把它抹平
    （只抹變形造成的差異，靜止形狀不變）。2026-10-12 攝影師身體肩膀出現碎摺後加的，選用"""
    for o in objs:
        if o.type != "MESH" or not o.modifiers.get("Armature"):
            continue
        cs = o.modifiers.new("FixFolds", "CORRECTIVE_SMOOTH")
        cs.rest_source = "ORCO"; cs.iterations = iterations; cs.smooth_type = "LENGTH_WEIGHTED"
        if o.modifiers.get("Thickness"):                          # 要在加厚之前抹
            o.modifiers.move(len(o.modifiers) - 1, list(o.modifiers).index(o.modifiers["Thickness"]))
    return objs


# ════════ 藏身體 ════════
def default_covered(c, sleeve_x=None, pant_hem=None, shoe_top=None):
    """全身套裝（長袖上衣＋長褲＋包鞋）的預設：手腕以外、脖子以上、褲管與鞋子之間的腳踝露出，其餘藏"""
    sleeve_x = sleeve_x or A["SLEEVE_X"]; pant_hem = pant_hem or A["ANKLE_Z"] + 0.045; shoe_top = shoe_top or A["ANKLE_Z"] + 0.075
    if abs(c.x) > sleeve_x - 0.02:
        return False
    if c.z > A["NECK_Z"] - 0.005 and abs(c.x) < 0.08:
        return False
    if c.z < shoe_top - 0.025:
        return True
    if c.z < pant_hem + 0.02:
        return False
    return True


def hide_body(covered):
    """身體被衣服整個蓋住的部分用 Mask 修改器藏起來（只藏不刪，身體網格不動）→ 動作時身體不會從衣服底下戳出來。
    covered(位置)→True＝藏。露出皮膚的款式（短袖、平口禮服、短裙）要自己寫 covered，不能用 default_covered"""
    vg = body.vertex_groups.get("Hide_Under_Outfit") or body.vertex_groups.new(name="Hide_Under_Outfit")
    ids = [v.index for v in body.data.vertices if covered(v.co)]
    vg.add(ids, 1.0, "REPLACE")
    m = body.modifiers.get("HideUnderOutfit") or body.modifiers.new("HideUnderOutfit", "MASK")
    m.vertex_group = "Hide_Under_Outfit"; m.invert_vertex_group = True
    return len(ids)
