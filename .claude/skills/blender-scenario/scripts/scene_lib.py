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


# ── 多角色同框（2026-10-06 為開場影片 V12 加；只新增函式，上面的既有行為不變）──
# 做法：開 A 角色的 _costume.blend（主命名空間＝A 的 PROJ/WHO），用 add_character() 把 B 角色附加進來，
# 拿到 B 自己的命名空間 ns（ns["ARM"]、ns["ACT"]、ns["pose_frame_at"]… 都是 B 的：體型比例、tune、鞋底取樣點各算各的）。
# 擺位置一律用 pose_frame_at（pose_frame 的腳底鎖定與動作裡的 IK 目標都假設角色在原點面向 -Y，搬到別處會把腳拉直）。

def add_character(proj_dir, blend=None, coll_name=None):
    """把另一個角色專案的角色（身體、服裝、頭髮、碰撞體）附加進目前開著的 .blend，回傳那個角色自己的命名空間。
    已經附加過（<who>_Armature 已存在，例：存好的同框檔）就只建命名空間。附加的物件放在 Cast_<who> 集合。"""
    proj_dir = os.path.abspath(proj_dir)
    man = json.load(open(os.path.join(proj_dir, "project.json"), encoding="utf8"))
    who = man["who"]
    if f"{who}_Armature" not in bpy.data.objects:
        bl = man.get("blend") or {}
        blend = blend or os.path.join(proj_dir, bl.get("costume") or f"{who}_costume.blend")
        if not os.path.exists(blend):
            blend = os.path.join(proj_dir, bl.get("base") or f"{who}.blend")
        with bpy.data.libraries.load(blend, link=False) as (src, dst):
            # 角色物件都以 <who>_ 為前綴；VRM 的頭髮碰撞體叫「J_Bip_… Collider」（另一個角色也有同名的，附加後自動加 .001）
            dst.objects = [n for n in src.objects if n.startswith(who + "_") or " Collider" in n]
        cname = coll_name or f"Cast_{who}"
        c = bpy.data.collections.get(cname) or bpy.data.collections.new(cname)
        if c.name not in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.link(c)
        for o in dst.objects:
            if o is not None and c not in o.users_collection:
                c.objects.link(o)
    ns = {"PROJECT": proj_dir, "REPO": REPO}
    p = os.path.join(SKILLS, "blender-motion-library", "scripts", "blender_env.py")
    exec(compile(open(p, encoding="utf8").read(), p, "exec"), ns)
    ns["use"]("studio", "pose_lib", "actions", "outfit_lib", "costume", "scene_lib")
    return ns


def place_matrix(x=0.0, y=0.0, rz=0.0):
    """角色站位：原點移到 (x, y)、面向轉 rz 度（0＝面向 -Y，+90＝面向 +X）"""
    return Matrix.Translation((x, y, 0.0)) @ Matrix.Rotation(math.radians(rz), 4, "Z")


def plant_feet_at(arm, feet, M):
    """plant_feet 的站位版：腳踝鎖在 M @（rest 腳踝位置 + (dx, dy)），膝蓋方向跟著站位轉"""
    B = arm.data.bones; R3 = M.to_3x3()
    for side, spec in feet.items():
        dx, dy, lift, pitch, yaw, toe = (tuple(spec) + (0.0,) * 6)[:6]
        a0 = B[f"J_Bip_{side}_Foot"].head_local
        sg = 1 if side == "L" else -1
        tgt = M @ Vector((a0.x + dx, a0.y + dy, a0.z + lift))
        pole = R3 @ Vector((sg * FOOT_POLE[0], FOOT_POLE[1], FOOT_POLE[2]))
        for _ in range(3):
            ik_leg(arm, side, tgt, tgt + pole, pitch, yaw, toe)
            err = lift - foot_sole_min(arm, side)
            if abs(err) < 2e-5:
                break
            tgt.z += err


def pose_frame_at(arm, P, x=0.0, y=0.0, rz=0.0, who=None):
    """pose_frame 的「站到場景某處」版。動作 dict 照常寫（角色在原點、面向 -Y）；這裡把 root、feet、ik、palms 換到站位 (x, y, rz)。
    場景自己算好的世界座標 IK（抓道具）放 P["ikw"]、世界方向的掌心放 P["palmsw"]，不再轉換。"""
    M = place_matrix(x, y, rz); R3 = M.to_3x3()
    apply_pose(arm, P)
    r = Vector(P.get("root", (0, 0, 0)))
    arm.location = M @ r
    arm.rotation_euler = (0, 0, math.radians(rz + P.get("rz", 0)))
    feet = P.get("feet")
    if feet:
        plant_feet_at(arm, feet, M)
    if P.get("ground", not feet):
        arm.location.z = r.z - sole_min_z(arm) + P.get("hop", 0.0)
    for item in P.get("ik", []):
        if len(item) > 4:                # 跟著骨頭走的目標：follow_matrix 已含骨架的世界矩陣
            Mf = follow_matrix(arm, item[4])
            item = (item[0],) + tuple(None if p is None else Mf @ Vector(p) for p in item[1:4])
        else:
            item = (item[0],) + tuple(None if p is None else M @ Vector(p) for p in item[1:4])
        ik_arm(arm, *item)
    for item in P.get("ikw", []):
        ik_arm(arm, *item)
    for side, deg in P.get("twist", []):
        twist_forearm(arm, side, deg)
    for item in list(P.get("palms", [])) + [None] + list(P.get("palmsw", [])):
        if item is None:
            R3 = Matrix.Identity(3); continue
        side, tgt = item[0], R3 @ Vector(item[1]); w = item[2] if len(item) > 2 else 1.0
        face_palm(arm, side, tgt, split=item[3] if len(item) > 3 else 0.5, w=w)
    set_face(P.get("face", {}), who)


def pose_blend_at(arm, PA, PB, w, x=0.0, y=0.0, rz=0.0, who=None, place_b=None):
    """兩個姿勢之間淡入淡出（換動作時用，免得一格跳過去）：各擺一次、骨頭四元數 slerp、骨架位置與表情線性內插。
    place_b＝(x, y, rz)：PB 用不同的站位（例：PA 是自帶世界座標的 walk_fwd，站位給 (0, 0, 0)；PB 是走完接的 idle）"""
    pa, pb = (x, y, rz), tuple(place_b) if place_b is not None else (x, y, rz)
    if w <= 1e-4:
        return pose_frame_at(arm, PA, *pa, who)
    if w >= 1 - 1e-4:
        return pose_frame_at(arm, PB, *pb, who)
    snap = []
    for P, pl in ((PA, pa), (PB, pb)):
        pose_frame_at(arm, P, *pl, who); bpy.context.view_layer.update()
        snap.append(({pb.name: pb.rotation_quaternion.copy() for pb in arm.pose.bones},
                     arm.location.copy(), arm.rotation_euler.z))
    (qa, la, za), (qb, lb, zb) = snap
    for pb in arm.pose.bones:
        pb.rotation_quaternion = qa[pb.name].slerp(qb[pb.name], w)
    arm.location = la.lerp(lb, w); arm.rotation_euler.z = za + (zb - za) * w
    fa, fb = PA.get("face", {}), PB.get("face", {})
    set_face({k: fa.get(k, 0.0) * (1 - w) + fb.get(k, 0.0) * w for k in set(fa) | set(fb)}, who)


def physics_setup(arms, keep="hair"):
    """頭髮物理準備（多個骨架）：只留名稱含 keep 的 spring（VRoid 衣服的 spring 會拉動藏起來的 T 恤骨頭），重設狀態"""
    for A in arms:
        sb = A.data.vrm_addon_extension.spring_bone1
        for i in reversed(range(len(sb.springs))):
            if keep not in sb.springs[i].vrm_name.lower():
                sb.springs.remove(i)
        sb.enable_animation = True
        for sp in sb.springs:
            for j in sp.joints:
                j.animation_state.initialized_as_tail = False


def render_cast(out_dir, n, pose_fn, cam_fn, arms, skirts=(), prop_fn=None, fps=24, res=(960, 540), warm=24, sub=2,
                stills=(), still_dir=None, still_prefix="", skip_existing=True, on_frame=None):
    """多個角色同框的渲染迴圈（頭髮＋裙擺物理）。
    pose_fn(f)：擺好所有角色在第 f 格（浮點；物理子步驟會傳小數）的姿勢；arms＝要跑頭髮物理的骨架；
    skirts＝各角色 skirt_phys 的 SkirtSpring；影格存 out_dir/0001.png…；skip_existing＝已存在的影格不重算
    （物理照樣逐格模擬，所以中斷後接著跑的結果和一次跑完一樣）。on_frame(i) 在每格渲染前呼叫（例：輸出 2D 追蹤點）。回傳秒數"""
    from bl_ext.blender_org.vrm.editor.spring_bone1 import handler as SB
    os.makedirs(out_dir, exist_ok=True)
    physics_setup(arms)
    for k in skirts:
        k.reset()
    sc_ = bpy.context.scene
    sc_.render.resolution_x, sc_.render.resolution_y = res; sc_.render.resolution_percentage = 100
    dt = 1.0 / (fps * sub)
    t0 = time.time()
    for w in range(warm):                # 停在第 0 格空跑，讓頭髮、裙擺穩定
        for s_i in range(sub):
            pose_fn(0.0)
            for k in skirts: k.step()
            SB.update_pose_bone_rotations(bpy.context, dt)
    for i in range(n):
        for s_i in range(sub):
            tt = i - 1 + (s_i + 1) / sub if i > 0 else 0.0
            pose_fn(max(0.0, tt))
            if prop_fn: prop_fn(max(0.0, tt))
            for k in skirts: k.step()
            SB.update_pose_bone_rotations(bpy.context, dt)
        bpy.context.view_layer.update()
        cam_fn(i)
        if on_frame: on_frame(i)
        path = os.path.join(out_dir, f"{i + 1:04d}.png")
        if not (skip_existing and os.path.exists(path)):
            sc_.render.filepath = path
            bpy.ops.render.render(write_still=True)
        if i in stills and still_dir:
            import shutil
            os.makedirs(still_dir, exist_ok=True)
            shutil.copy2(path, os.path.join(still_dir, f"{still_prefix}{i + 1:04d}.png"))
    for A in arms:
        A.data.vrm_addon_extension.spring_bone1.enable_animation = False
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
