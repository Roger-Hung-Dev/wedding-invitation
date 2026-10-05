# 情境共用工具：道具產生、手臂對位（讓手抓到道具上的點）、關鍵格內插、情境渲染迴圈。
# use("studio", "pose_lib", "actions", "outfit_lib", "costume", "scene_lib") 載入（run_scene.py 會做）。
# 座標以預設庫新娘為準；道具位置照角色實際尺寸放（BODY_S＝頭骨高/1.386）。
import bpy, bmesh, math, os, json, time
from mathutils import Vector, Matrix, Euler, Quaternion

SC_COLL = "SceneProps"


def coll():
    c = bpy.data.collections.get(SC_COLL)
    if c is None:
        c = bpy.data.collections.new(SC_COLL); bpy.context.scene.collection.children.link(c)
    return c


def clear_props():
    c = bpy.data.collections.get(SC_COLL)
    if c:
        for o in list(c.objects):
            bpy.data.objects.remove(o, do_unlink=True)


def mat(name, color, shade=None, alpha=None, emit=None):
    m = mtoon(name, color, shade, alpha)
    if emit is not None:
        m.vrm_addon_extension.mtoon1.emissive_factor = emit
    return m


def solid(name, bm, m, smooth=False, parent=None):
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me); coll().objects.link(ob)
    if isinstance(m, (list, tuple)):
        for mm in m: me.materials.append(mm)
    else:
        me.materials.append(m)
    return ob


def box(bm, c, size, rot=None, mi=0):
    r = bmesh.ops.create_cube(bm, size=1.0)
    M = Matrix.Translation(c) @ (rot or Matrix.Identity(4)) @ Matrix.Diagonal((*size, 1))
    bmesh.ops.transform(bm, matrix=M, verts=r["verts"])
    for f in {f for v in r["verts"] for f in v.link_faces}:
        f.material_index = mi
    return r


def cyl(bm, c, r, h, axis="Z", seg=24, r2=None, mi=0, rot=None):
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h)
    R = {"Z": Matrix.Identity(4), "X": Matrix.Rotation(math.pi / 2, 4, "Y"), "Y": Matrix.Rotation(math.pi / 2, 4, "X")}[axis]
    bmesh.ops.transform(bm, matrix=Matrix.Translation(c) @ (rot or Matrix.Identity(4)) @ R, verts=res["verts"])
    for f in {f for v in res["verts"] for f in v.link_faces}:
        f.material_index = mi
    return res


def ball(bm, c, r, mi=0, seg=16):
    res = bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(6, seg // 2), radius=1.0)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(c) @ Matrix.Diagonal((*(r if isinstance(r, (tuple, list)) else (r, r, r)), 1)), verts=res["verts"])
    for f in {f for v in res["verts"] for f in v.link_faces}:
        f.material_index = mi
    return res


def text_obj(name, body, size, loc, rot, m, font="C:/Windows/Fonts/msjhbd.ttc", extrude=0.0):
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
    cu = bpy.data.curves.new(name, "FONT"); cu.body = body; cu.size = size; cu.align_x = "CENTER"; cu.align_y = "CENTER"
    cu.extrude = extrude
    try:
        cu.font = bpy.data.fonts.load(font, check_existing=True)
    except Exception:
        pass
    ob = bpy.data.objects.new(name, cu); coll().objects.link(ob)
    ob.location = loc; ob.rotation_euler = rot; cu.materials.append(m)
    return ob


def image_mat(name, path):
    """一般 Principled＋圖片（報紙、海報用）"""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission"); tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(tex.outputs["Color"], em.inputs["Color"]); em.inputs["Strength"].default_value = 0.95
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


# ── 手臂參數化：一隻手 5 個角度 ──
def arm_pose(P, side, v, twist=0.0):
    """v = (ua_y, ua_x, ua_z, fa_x, fa_z)：上臂 Y（垂下＝72）、往前抬 X、往內 Z；前臂往前彎 X、往內 Z。右手自動鏡像"""
    sg = 1 if side == "L" else -1
    P[f"{side}_UpperArm"] = [("Y", sg * v[0]), ("X", -v[1]), ("Z", -sg * v[2])]
    P[f"{side}_LowerArm"] = [("X", -v[3]), ("Z", -sg * v[4])]
    if twist:
        P.setdefault("twist", []).append((side, twist))
    return P


DOWN = (72, 0, 0, 18, 0)


def nm(f, x0, step=10.0, iters=70):
    n = len(x0)
    pts = [list(x0)] + [[x0[j] + (step if j == i else 0) for j in range(n)] for i in range(n)]
    vals = [f(p) for p in pts]
    for _ in range(iters):
        o = sorted(range(n + 1), key=lambda i: vals[i]); pts = [pts[i] for i in o]; vals = [vals[i] for i in o]
        cen = [sum(p[j] for p in pts[:-1]) / n for j in range(n)]
        xr = [cen[j] + (cen[j] - pts[-1][j]) for j in range(n)]; fr = f(xr)
        if fr < vals[0]:
            xe = [cen[j] + 2 * (cen[j] - pts[-1][j]) for j in range(n)]; fe = f(xe)
            pts[-1], vals[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < vals[-2]:
            pts[-1], vals[-1] = xr, fr
        else:
            xc = [cen[j] + 0.5 * (pts[-1][j] - cen[j]) for j in range(n)]; fc = f(xc)
            if fc < vals[-1]:
                pts[-1], vals[-1] = xc, fc
            else:
                pts = [pts[0]] + [[pts[0][j] + 0.5 * (p[j] - pts[0][j]) for j in range(n)] for p in pts[1:]]
                vals = [vals[0]] + [f(p) for p in pts[1:]]
    i = min(range(n + 1), key=lambda i: vals[i])
    return pts[i], vals[i]


def bone_pt(bone, end="head", off=None):
    pb = ARM.pose.bones[bone]; mw = ARM.matrix_world
    if off is not None:
        return mw @ pb.matrix @ Vector(off)
    return mw @ (pb.head if end == "head" else pb.tail)


def fit_arm(base_fn, side, targets, x0=DOWN, twist=0.0, iters=70, reg=0.0):
    """base_fn(v) → 完整姿勢 dict（含這隻手的 arm_pose）；targets = [(bone, end, (x,y,z), 權重)]"""
    def cost(v):
        pose_frame(ARM, base_fn(v)); bpy.context.view_layer.update()
        c = sum((tg[3] if len(tg) > 3 else 1.0) * (bone_pt(tg[0], tg[1]) - Vector(tg[2])).length_squared for tg in targets)
        return c + reg * sum((a - b) ** 2 for a, b in zip(v, x0)) * 1e-6
    best, val = nm(cost, list(x0), iters=iters)
    pose_frame(ARM, base_fn(best)); bpy.context.view_layer.update()
    err = [round((bone_pt(tg[0], tg[1]) - Vector(tg[2])).length * 1000, 1) for tg in targets]
    return [round(b, 2) for b in best], err


def keys_interp(keys, t):
    """keys = [(t, vector)]，平滑內插（smoothstep），t 超出範圍取端點"""
    if t <= keys[0][0]:
        return list(keys[0][1])
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1:
            u = ease((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
            return [x + (y - x) * u for x, y in zip(a, b)]
    return list(keys[-1][1])


def seat_legs(P, hip_z_target, side_spread=4):
    """坐姿：大腿往前、小腿垂直、腳掌踩地。回傳 root z（整體要下降多少）"""
    B = ARM.data.bones
    hip0 = B["J_Bip_L_UpperLeg"].head_local; knee0 = B["J_Bip_L_LowerLeg"].head_local; ank0 = B["J_Bip_L_Foot"].head_local
    L1 = (knee0 - hip0).length; L2 = (ank0 - knee0).length
    knee_z = ank0.z + L2
    s_ = max(-1.0, min(1.0, (hip_z_target - knee_z) / L1))
    a = math.degrees(math.asin(s_))                  # 大腿往下斜的角度
    for sd, sg in (("L", 1), ("R", -1)):
        P[f"{sd}_UpperLeg"] = [("X", -(90 - a)), ("Z", sg * side_spread)]
        P[f"{sd}_LowerLeg"] = [("X", 90 - a)]
        P[f"{sd}_Foot"] = [("X", 0)]
    return hip_z_target - hip0.z


# ── 情境渲染迴圈（頭髮＋裙擺物理）──
def render_scene(name, n, frame_fn, cam_fn, res=(960, 540), outfit="costume", warm=24, sub=2, prop_fn=None, budget=None, stills=()):
    from bl_ext.blender_org.vrm.editor.spring_bone1 import handler as SB
    """影格存 WORK/scenes/<name>/；stills 列出的格數另外複製一份到 PROJ/pictures/scenes/<name>_<格>.png"""
    out = os.path.join(WORK, "scenes", name); os.makedirs(out, exist_ok=True)
    wear(outfit)
    sb = ARM.data.vrm_addon_extension.spring_bone1
    for i in reversed(range(len(sb.springs))):
        if "hair" not in sb.springs[i].vrm_name.lower():
            sb.springs.remove(i)
    sb.enable_animation = True
    for sp in sb.springs:
        for j in sp.joints:
            j.animation_state.initialized_as_tail = False
    skirt = None
    if outfit == "costume" and "Skirt_Sway" in ARM.data.bones:
        use("skirt_phys")
        skirt = globals()["skirt"]; skirt.reset()
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    mesh_eval(True)
    t0 = time.time()
    # 開頭先停在第 0 格空跑 warm 格，讓頭髮、裙擺穩定
    for w in range(warm):
        for s_i in range(sub):
            pose_frame(ARM, frame_fn(0))
            if skirt: skirt.step()
            SB.update_pose_bone_rotations(bpy.context, 1.0 / (24 * sub))
    for i in range(n):
        for s_i in range(sub):
            tt = i - 1 + (s_i + 1) / sub if i > 0 else 0
            pose_frame(ARM, frame_fn(max(0.0, tt)))
            if prop_fn: prop_fn(max(0.0, tt))
            if skirt: skirt.step()
            SB.update_pose_bone_rotations(bpy.context, 1.0 / (24 * sub))
        bpy.context.view_layer.update()
        cam_fn(i)
        sc.render.filepath = os.path.join(out, f"{i + 1:04d}.png")
        bpy.ops.render.render(write_still=True)
        if i in stills:
            import shutil
            d = os.path.join(PICS, "scenes"); os.makedirs(d, exist_ok=True)
            shutil.copy2(sc.render.filepath, os.path.join(d, f"{name}_{i + 1:04d}.png"))
    sb.enable_animation = False
    return round(time.time() - t0, 1)


def set_world(bg, floor=None):
    """每個情境自己的背景色；floor=None 時保留攝影棚地板、給顏色就換地板色、False 就藏起來"""
    w = bpy.context.scene.world
    n = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    n.inputs[0].default_value = (*bg, 1)
    fl = bpy.data.objects.get("Floor")
    if fl:
        fl.hide_render = floor is False
        if floor:
            p = next(x for x in fl.data.materials[0].node_tree.nodes if x.type == "BSDF_PRINCIPLED")
            p.inputs["Base Color"].default_value = (*floor, 1)
