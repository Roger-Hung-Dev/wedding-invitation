# 第 3 關第 3 輪（2026-10-11）回饋「⑦ 拆成兩幕」的道具與場景（mx_preview 的 SID=07a／07b 才載入：use("set_v3")）。
#   ⑦a 盡情享用美食：沿用 ⑦ 的圓桌晚餐（set_v2 的 build_dinner／build_dinner_items），新娘一個人坐桌子正後方 → 桌上的東西重排、加菜
#     （烤雞大盤、濃湯、沙拉；原有的牛排盤挪到她面前，水果、三盤點心、紅酒瓶、她的酒杯排在周圍；新郎的酒杯、餐巾、畫架收起來）。
#   ⑦b 喝酒不開車：晚上的餐廳門口（人行道、路緣、馬路、餐廳門面、路燈）＋幾何做的卡通計程車（右後門能開、輪子會轉）、新郎臉紅。
# 座標：⑦a 同 ⑦（桌心 V2_07["tc"]）；⑦b 自成一景（集合 Set_Street），x 沿馬路、−y 是鏡頭那側。
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

# ════════ ⑦a：滿桌菜 ════════
# 桌心座標（公尺；新娘在 +y 那側、面向 −y）。她的手平放在 (±0.21, 0.27)，周圍的菜都離手 ≥ 8 cm；她的牛排盤在 (0, 0.17)＝mx_scene_07a 的 PLATE_A
FEAST_LAYOUT = dict(main=(0.0, 0.17), chicken=(0.0, -0.13), fruit=(0.30, 0.02),
                    desserts=[(-0.30, 0.02), (0.0, -0.38), (-0.36, 0.21)], soup=(-0.22, -0.27), salad=(0.22, -0.27),
                    bottle=(-0.36, -0.12), glass=(0.38, -0.16))   # 酒杯：第 7 輪鎖骨放鬆後比讚的手臂往側邊伸、收回時穿過 (0.36, 0.18) 的杯子 → 挪到桌子內側


def _feast_mats():
    return dict(
        china=pmat("V3_China", srgb("#FFFDF8"), rough=0.25, spec=0.6),
        rim=pmat("V3_ChinaRim", PAL["gold"], rough=0.3, spec=0.6, metal=0.8),
        skin=pmat("V3_ChickenSkin", srgb("#B9672C"), rough=0.35, spec=0.6, noise=0.35, coat=0.4),
        skin2=pmat("V3_ChickenDark", srgb("#8C4520"), rough=0.4, spec=0.5, noise=0.3),
        bone=pmat("V3_Bone", srgb("#F3E6CF"), rough=0.6, spec=0.3),
        lettuce=pmat("V3_Lettuce", srgb("#7DB35A"), rough=0.7, spec=0.2, noise=0.15),
        tomato=pmat("V3_Tomato", srgb("#D8402F"), rough=0.25, spec=0.6),
        lemon=pmat("V3_Lemon", srgb("#F2D35B"), rough=0.4, spec=0.4),
        soup=pmat("V3_Soup", srgb("#E9B65A"), rough=0.15, spec=0.7),
        cream=pmat("V3_SoupCream", srgb("#FFF6E3"), rough=0.3, spec=0.5),
        herb=pmat("V3_Herb", srgb("#4E7F3A"), rough=0.6, spec=0.2),
        egg=pmat("V3_Egg", srgb("#FFF8EA"), rough=0.4, spec=0.4),
        yolk=pmat("V3_Yolk", srgb("#F2B33D"), rough=0.4, spec=0.4),
        corn=pmat("V3_Corn", srgb("#F5D062"), rough=0.5, spec=0.3),
    )


def _bowl(bm, r, h, mi=0):
    """碗（外壁＋內壁＋碗腳），回傳液面高度"""
    _lathe(bm, [(0.0, 0.0), (r * 0.45, 0.0), (r * 0.47, 0.008), (r * 0.8, h * 0.45), (r, h), (r * 0.96, h), (r * 0.76, h * 0.45),
                (r * 0.42, 0.012), (0.0, 0.012)], seg=40, mi=mi)
    return h * 0.78


def build_feast(dc, TC, TOP):
    """⑦a 新加的菜（V3_*，掛在 V2_Table 底下）：烤雞大盤、濃湯、沙拉"""
    rig = bpy.data.objects["V2_Table"]; M = _feast_mats(); L = FEAST_LAYOUT
    random.seed(77)
    # 烤雞：橢圓大盤＋金黃烤雞（身體、兩隻雞腿、翅膀）＋生菜、番茄、檸檬片
    bm = bmesh.new()
    _lathe(bm, [(0.0, 0.0), (0.09, 0.0), (0.095, 0.004), (0.14, 0.010), (0.16, 0.018), (0.158, 0.020), (0.13, 0.013), (0.0, 0.010)], seg=48, mi=0)
    bmesh.ops.scale(bm, vec=(1.0, 0.72, 1.0), verts=bm.verts[:])
    o = mesh_obj("V3_ChickenPlatter", bm, [M["china"]], dc, smooth=True, parent=rig)
    o.location = (L["chicken"][0], L["chicken"][1], TOP + 0.004)
    # 2026-10-11 第 3 關第 5 輪回饋「食物造型是圓形的，看不出是牛排還是雞腿」→ 烤雞重做：側面朝鏡頭（鏡頭在 −y），
    #   胸口在左邊高高鼓起、兩隻雞腿在右後方往上翹、腿骨套白色紙花（最認得出是烤雞的地方），表皮金黃帶深色烤痕；周圍生菜、小番茄、檸檬角、烤馬鈴薯、迷迭香
    bm = MB(); b0 = Vector((0, 0, 0.012))

    def seg_(p0, p1, r0, r1, mi, n=14):                          # 兩點之間的圓錐台（雞腿、骨頭）
        d = p1 - p0
        rot = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
        cyl(bm, (p0 + p1) / 2, r0, d.length, seg=n, r2=r1, mi=mi, rot=rot)
    for k in range(12):                                          # 生菜墊底
        a = 2 * math.pi * k / 12
        ball(bm, b0 + Vector((0.13 * math.cos(a), 0.085 * math.sin(a), 0.004)), (0.034, 0.022, 0.007), mi=2, seg=10)
    ball(bm, b0 + Vector((0.005, 0, 0.058)), (0.092, 0.068, 0.052), mi=0, seg=22)        # 身體（左右長的蛋形）
    ball(bm, b0 + Vector((-0.03, 0, 0.082)), (0.062, 0.058, 0.042), mi=0, seg=18)        # 胸口（左邊高起來）
    # （第 5 輪試過背上加深色烤痕，看起來像破洞，拿掉；金黃色和亮面就夠像烤的）
    for sy in (-1, 1):
        ball(bm, b0 + Vector((0.055, sy * 0.058, 0.05)), (0.05, 0.03, 0.042), mi=0, seg=16)                  # 大腿
        seg_(b0 + Vector((0.07, sy * 0.055, 0.06)), b0 + Vector((0.125, sy * 0.032, 0.112)), 0.027, 0.013, 0)  # 棒棒腿往右上翹
        seg_(b0 + Vector((0.123, sy * 0.033, 0.11)), b0 + Vector((0.148, sy * 0.022, 0.135)), 0.007, 0.006, 3)  # 骨頭
        seg_(b0 + Vector((0.142, sy * 0.024, 0.129)), b0 + Vector((0.162, sy * 0.016, 0.149)), 0.011, 0.015, 6, n=12)  # 白色紙花
        ball(bm, b0 + Vector((-0.05, sy * 0.064, 0.06)), (0.042, 0.018, 0.026), mi=0, seg=12)                # 翅膀
    for k in range(4):                                           # 小番茄
        a = math.radians(205 + 32 * k)
        ball(bm, b0 + Vector((0.135 * math.cos(a), 0.09 * math.sin(a), 0.016)), 0.014, mi=4, seg=12)
    for k in range(3):                                           # 檸檬角
        a = math.radians(-20 + 35 * k)
        cyl(bm, b0 + Vector((0.135 * math.cos(a), 0.09 * math.sin(a), 0.014)), 0.022, 0.012, axis="X", seg=14, mi=5,
            rot=Matrix.Rotation(a, 4, "Z"))
    for k in range(5):                                           # 烤馬鈴薯
        a = math.radians(150 + 20 * k)
        ball(bm, b0 + Vector((0.14 * math.cos(a), 0.095 * math.sin(a), 0.014)), (0.018, 0.015, 0.013), mi=7, seg=10)
    for k in range(3):                                           # 迷迭香
        seg_(b0 + Vector((-0.02 + 0.03 * k, -0.07, 0.03)), b0 + Vector((0.01 + 0.03 * k, -0.105, 0.035)), 0.003, 0.002, 8, n=6)
    M["frill"] = pmat("V3_PaperFrill", srgb("#FFFFFF"), rough=0.7, spec=0.2)
    M["potato"] = pmat("V3_RoastPotato", srgb("#D6A24E"), rough=0.5, spec=0.4, noise=0.3)
    M["rosemary"] = pmat("V3_Rosemary", srgb("#3F6B35"), rough=0.7)
    M["skin"] = pmat("V3_ChickenSkin", srgb("#C9772F"), rough=0.3, spec=0.6, noise=0.35, coat=0.5)
    M["skin2"] = pmat("V3_ChickenDark", srgb("#7E3C14"), rough=0.35, spec=0.5, noise=0.3)
    mesh_obj("V3_Chicken", bm, [M["skin"], M["skin2"], M["lettuce"], M["bone"], M["tomato"], M["lemon"], M["frill"], M["potato"], M["rosemary"]],
             dc, smooth=True, parent=o)
    # 濃湯（玉米濃湯＋奶油漩渦＋香草）
    bm = bmesh.new(); lvl = _bowl(bm, 0.07, 0.05)
    o = mesh_obj("V3_SoupBowl", bm, [M["china"]], dc, smooth=True, parent=rig)
    o.location = (L["soup"][0], L["soup"][1], TOP + 0.004)
    bm = MB()
    cyl(bm, Vector((0, 0, lvl)), 0.064, 0.004, seg=32, mi=0)
    for k in range(5):
        a = k * 1.3; r_ = 0.012 + 0.008 * k
        ball(bm, Vector((r_ * math.cos(a), r_ * math.sin(a), lvl + 0.002)), (0.012, 0.006, 0.002), mi=1, seg=10)
    for k in range(6):
        ball(bm, Vector((random.uniform(-0.03, 0.03), random.uniform(-0.03, 0.03), lvl + 0.003)), 0.003, mi=2, seg=6)
    mesh_obj("V3_Soup", bm, [M["soup"], M["cream"], M["herb"]], dc, smooth=True, parent=o)
    # 沙拉（大碗：生菜、番茄、水煮蛋、玉米）
    bm = bmesh.new(); lvl = _bowl(bm, 0.08, 0.055)
    o = mesh_obj("V3_SaladBowl", bm, [M["china"]], dc, smooth=True, parent=rig)
    o.location = (L["salad"][0], L["salad"][1], TOP + 0.004)
    bm = MB()
    for k in range(16):
        a = random.uniform(0, 2 * math.pi); r_ = random.uniform(0.0, 0.055)
        ball(bm, Vector((r_ * math.cos(a), r_ * math.sin(a), lvl + random.uniform(0.0, 0.02))), (0.028, 0.02, 0.012), mi=0, seg=10)
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.3
        ball(bm, Vector((0.035 * math.cos(a), 0.035 * math.sin(a), lvl + 0.025)), 0.012, mi=1, seg=10)
    for k in range(2):
        a = math.pi * k + 1.0; p = Vector((0.02 * math.cos(a), 0.02 * math.sin(a), lvl + 0.03))
        ball(bm, p, (0.016, 0.011, 0.008), mi=2, seg=12); ball(bm, p + Vector((0, 0, 0.006)), (0.007, 0.007, 0.004), mi=3, seg=8)
    for k in range(10):
        ball(bm, Vector((random.uniform(-0.045, 0.045), random.uniform(-0.045, 0.045), lvl + 0.03)), 0.005, mi=4, seg=6)
    mesh_obj("V3_Salad", bm, [M["lettuce"], M["tomato"], M["egg"], M["yolk"], M["corn"]], dc, smooth=True, parent=o)


def make_neck_shadow(arm, color="#D99A8E", strength=0.55, z0=1.31, z1=1.349, ang=58.0):
    """下巴下的脖子陰影（第 3 關第 8 輪回饋「新娘脖子不明顯，輪廓看不出有脖子」）：卡通材質在前上方的光下脖子和胸口同一個顏色，
    頭髮又擋住脖子兩側，下巴底下沒有影子 → 在脖子前面貼一道彎曲的柔邊膚色陰影（動畫常見的畫法）。
    形狀照新娘脖子量的（scratchpad neck_probe：下巴尖 z 1.351、脖子前緣 y −0.009、脖子軸心 y 0.03 → 半徑約 0.039）：
    繞脖子軸心半徑 0.0405 的圓弧面，左右 ±ang 度、高 z0～z1；上緣（靠下巴）最深、往下和往兩側漸淡。掛在脖子骨頭上"""
    import bmesh as _bm
    B = arm.data.bones["J_Bip_C_Neck"]
    ax0, ax1 = B.head_local, B.tail_local

    def axis_at(z):
        k = (z - ax0.z) / max(1e-6, ax1.z - ax0.z); return ax0.lerp(ax1, k)
    # 脖子表面：身體網格在這一段的頂點，換成「繞軸心的角度、半徑」，每個貼片點用附近頂點的半徑加權平均（第一版用固定半徑 0.0405，
    #   比實際脖子小半毫米，整片藏在皮膚裡）
    body = bpy.data.objects.get(arm.name.replace("_Armature", "_Body"))
    samp = []
    if body:
        Mb = arm.matrix_world.inverted() @ body.matrix_world
        for vv in body.data.vertices:
            p = Mb @ vv.co
            if z0 - 0.012 <= p.z <= z1 + 0.012:
                c = axis_at(p.z); d = Vector((p.x - c.x, p.y - c.y))
                if d.length > 1e-4 and d.y < 0.01:                          # 只要前半圈
                    samp.append((math.atan2(d.x, -d.y), p.z, d.length))

    def radius(th, z):
        wsum = rsum = 0.0
        for t_, z_, r_ in samp:
            w = math.exp(-((t_ - th) / 0.18) ** 2 - ((z_ - z) / 0.006) ** 2)
            wsum += w; rsum += w * r_
        return rsum / wsum if wsum > 1e-6 else 0.043
    nu, nv = 24, 8
    me = bpy.data.meshes.new("V3_NeckShadow")
    bm = _bm.new()
    vs = []
    for j in range(nv + 1):
        v = j / nv; z = z0 + (z1 - z0) * v
        c = axis_at(z)
        row = []
        for i in range(nu + 1):
            u = i / nu; th = math.radians(-ang + 2 * ang * u)
            r = radius(th, z) + float(globals().get("NECKOFF", 0.004))       # 貼在表面外 4 mm（1.5 mm 時被變形的皮膚蓋住）
            p = Vector((c.x + r * math.sin(th), c.y - r * math.cos(th), z))
            row.append((bm.verts.new(p), u, v))
        vs.append(row)
    print("NECKSHADOW samples", len(samp), "radius front %.4f side %.4f" % (radius(0.0, (z0 + z1) / 2), radius(math.radians(ang), (z0 + z1) / 2)), flush=True)
    for j in range(nv):
        for i in range(nu):
            bm.faces.new((vs[j][i][0], vs[j][i + 1][0], vs[j + 1][i + 1][0], vs[j + 1][i][0]))
    bm.to_mesh(me); bm.free()
    attr = me.color_attributes.new("a", "FLOAT_COLOR", "POINT")
    k = 0
    for j in range(nv + 1):
        for i in range(nu + 1):
            u, v = vs[j][i][1], vs[j][i][2]
            side = max(0.0, 1.0 - abs(2 * u - 1) ** 3)
            a = strength * (v ** 1.6) * side
            attr.data[k].color = (a, a, a, 1.0); k += 1
    m = bpy.data.materials.get("V3_NeckShadow") or bpy.data.materials.new("V3_NeckShadow")
    m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "a"
    nt.links.new(at.outputs["Fac"], bs.inputs["Alpha"]); nt.links.new(bs.outputs[0], out.inputs["Surface"])
    bs.inputs["Base Color"].default_value = (*srgb(color), 1); bs.inputs["Roughness"].default_value = 0.8
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    me.materials.append(m)
    o = bpy.data.objects.get("V3_NeckShadow")
    if o:
        bpy.data.objects.remove(o, do_unlink=True)
    o = bpy.data.objects.new("V3_NeckShadow", me); bpy.context.scene.collection.objects.link(o)
    o.visible_shadow = False
    bpy.context.view_layer.update()
    pb = arm.pose.bones["J_Bip_C_Neck"]
    P = arm.matrix_world @ pb.matrix @ B.matrix_local.inverted()      # rest → 現在姿勢
    o.parent = arm; o.parent_type = "BONE"; o.parent_bone = "J_Bip_C_Neck"
    bpy.context.view_layer.update()
    o.matrix_world = P
    return o


def make_skin_shade(arm, name, keep_face, alpha_at, color="#D99A8E", offset=0.0015, subdiv=0, src="_Body", flat_gain=0.0):
    """皮膚上的柔邊陰影層：把身體網格上 keep_face(rest 位置) 為真的那幾片面複製成一層殼，沿法線往外推 offset，
    每個頂點的透明度＝alpha_at(rest 位置)。殼保留身體的頂點群組和骨架修改器 → 跟皮膚一起變形，不會浮起或陷進去
    （第 3 關第 8 輪：先用固定形狀的貼片，皮膚一變形就整片藏進去）
    subdiv：殼先細分幾刀再上透明度。VRoid 胸口的面很大，細線只落在頂點附近、畫出來變成一顆顆點（權重會跟著內插）
    src：從哪個皮膚網格複製。胸口、肩膀露出來的那一大片是 _BodyFill（補回 VRoid 刪掉的皮膚），不是 _Body —— 貼在 _Body 上會藏在補皮底下
    flat_gain > 0：改成平塗（自發光 color × flat_gain，不吃光影），跟 MToon 的平塗陰影同一種質感。
      Principled 版會吃到頭部投下的軟陰影雜訊，脖子變成髒髒的咖啡色。flat_gain 用來抵掉曝光（−0.25 → 2**0.25）"""
    import bmesh as _bm
    body = bpy.data.objects[arm.name.replace("_Armature", src)]
    o = bpy.data.objects.get(name)
    if o:
        bpy.data.objects.remove(o, do_unlink=True)
    o = body.copy(); o.data = body.data.copy(); o.name = name
    for c in body.users_collection:
        c.objects.link(o)
    for m in list(o.modifiers):
        if m.type != "ARMATURE":
            o.modifiers.remove(m)
    for m in o.modifiers:
        m.show_render = True
    bm = _bm.new(); bm.from_mesh(o.data)
    kill = [f for f in bm.faces if not keep_face(f.calc_center_median())]
    _bm.ops.delete(bm, geom=kill, context="FACES")
    if subdiv:
        _bm.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=subdiv, use_grid_fill=True)
    bm.normal_update()
    for v in bm.verts:
        v.co = v.co + v.normal * offset
    bm.to_mesh(o.data); bm.free()
    me = o.data
    me.materials.clear()
    mat = bpy.data.materials.get(name + "Mat") or bpy.data.materials.new(name + "Mat")
    mat.use_nodes = True; nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "shade_a"
    if flat_gain > 0:
        em = nt.nodes.new("ShaderNodeEmission"); tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader")
        em.inputs["Color"].default_value = (*srgb(color), 1); em.inputs["Strength"].default_value = flat_gain
        nt.links.new(at.outputs["Fac"], mx.inputs["Fac"]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs["Surface"])
    else:
        bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
        nt.links.new(at.outputs["Fac"], bs.inputs["Alpha"]); nt.links.new(bs.outputs[0], out.inputs["Surface"])
        bs.inputs["Base Color"].default_value = (*srgb(color), 1); bs.inputs["Roughness"].default_value = 0.8
    try:
        mat.surface_render_method = "BLENDED"
    except Exception:
        pass
    me.materials.append(mat)
    for f in me.polygons:
        f.material_index = 0
    if "shade_a" in me.color_attributes:
        me.color_attributes.remove(me.color_attributes["shade_a"])
    attr = me.color_attributes.new("shade_a", "FLOAT_COLOR", "POINT")
    for i, v in enumerate(me.vertices):
        a = max(0.0, min(1.0, alpha_at(v.co)))
        attr.data[i].color = (a, a, a, 1.0)
    o.visible_shadow = False
    print("SKINSHADE", name, "faces", len(me.polygons), flush=True)
    return o


def ruffle_follow_skin(arm, src="_BodyFill", dst="_Cos_Ruffle", k=1.0):
    """領口荷葉邊改用「最近的補皮頂點」的骨頭權重（第 3 關第 9 輪回饋「圈起來的兩塊是甚麼」）：
    補皮沿領口有一圈鼓起來的捲邊（模型缺陷），原始站姿時藏在荷葉邊底下；荷葉邊主要綁上胸骨、補皮在肩膀綁鎖骨，
    ⑦a 把鎖骨往上放回自然位置後，補皮跟著鎖骨上去、荷葉邊留在原地 → 捲邊露出來，畫成兩道勾狀的陰影線。
    權重照抄後荷葉邊和底下的皮膚一起動，跟原始站姿一樣蓋住捲邊。只改記憶體裡的頂點群組（不存檔）；k＝抄過來的比例"""
    from mathutils import kdtree
    s_o = bpy.data.objects[arm.name.replace("_Armature", src)]
    d_o = bpy.data.objects[arm.name.replace("_Armature", dst)]
    bones = {b.name for b in arm.data.bones}
    kd = kdtree.KDTree(len(s_o.data.vertices))
    for v in s_o.data.vertices:
        kd.insert(v.co, v.index)
    kd.balance()
    s_names = {g.index: g.name for g in s_o.vertex_groups}
    d_names = {g.index: g.name for g in d_o.vertex_groups}
    plan = []
    for v in d_o.data.vertices:
        _, si, _ = kd.find(v.co)
        sw = {s_names[g.group]: g.weight for g in s_o.data.vertices[si].groups if s_names[g.group] in bones}
        dw = {d_names[g.group]: g.weight for g in v.groups if d_names[g.group] in bones}
        tot = sum(sw.values()) or 1.0
        mix = {n: dw.get(n, 0.0) * (1 - k) + sw.get(n, 0.0) / tot * k for n in set(sw) | set(dw)}
        plan.append((v.index, mix))
    for vi, mix in plan:
        for n, wv in mix.items():
            g = d_o.vertex_groups.get(n) or d_o.vertex_groups.new(name=n)
            if wv > 1e-4:
                g.add([vi], wv, "REPLACE")
            else:
                g.remove([vi])
    print("RUFFLEFOLLOW verts", len(plan), flush=True)


def raise_neckline(arm, dz=0.018, parts=("_Cos_Ruffle",), z_zero=1.235, z_full=1.29):
    """領口（荷葉邊＋上衣上半＋胸前花瓣）在擺好姿勢後往上提 dz（世界 Z）（第 3 關第 9、10 輪回饋「圈起來的兩塊／還是有兩塊突出來」）：
    ⑦a 手臂往前、肩膀抬高，補皮的胸部上緣跟著上來，從領口上方露出約 1 cm，MToon 在那條弧線畫出兩個勾狀的明暗交界。
    整片荷葉邊往上平移 → 荷葉邊和上衣中間拉開一條縫露出皮膚；上衣、花瓣一起提 → 胸部從上衣裡穿出來（兩塊深粉色橢圓）。
    所以只「拉長」荷葉邊：照 rest 高度漸變，z_full 以上（上緣）全提、z_zero 以下（接上衣的下緣）不動。
    用 Displace（方向 Z、不用貼圖＝平移，頂點群組控制多少）插在骨架修改器正後面"""
    def sstep(a, b, x):
        u = max(0.0, min(1.0, (x - a) / (b - a))); return u * u * (3 - 2 * u)
    for part in parts:
        o = bpy.data.objects.get(arm.name.replace("_Armature", part))
        if not o:
            continue
        g = o.vertex_groups.get("V3_RaiseW") or o.vertex_groups.new(name="V3_RaiseW")
        for v in o.data.vertices:
            g.add([v.index], sstep(z_zero, z_full, v.co.z), "REPLACE")
        md = o.modifiers.get("V3_RaiseUp") or o.modifiers.new("V3_RaiseUp", "DISPLACE")
        md.direction = "Z"; md.space = "GLOBAL"; md.mid_level = 0.0; md.strength = dz; md.vertex_group = "V3_RaiseW"
        want = [m.name for m in o.modifiers].index("Armature") + 1
        while [m.name for m in o.modifiers].index("V3_RaiseUp") > want:
            with bpy.context.temp_override(object=o):
                bpy.ops.object.modifier_move_up(modifier="V3_RaiseUp")
        print("RAISENECK", part, dz, [m.name for m in o.modifiers], flush=True)


def smooth_fill_normals(arm, radius=0.025):
    """補皮 _BodyFill 領口捲邊的明暗修正（第 3 關第 10 輪回饋「還是有兩塊突出來，為什麼修正不掉」）：
    捲邊實際位置（畫面上用 TINTMODE=restpos 反推）：z 1.255～1.28、|x| 0.04～0.15、上衣上緣正上方。
    MToon 照補皮的自訂法線畫明暗 → 不動形狀，只把這一帶的自訂法線換成「周圍 radius 內頂點法線的高斯平均」，照權重和原本的漸變。
    形狀不變 → 底下的 _Body 不會透出來、也不會因為形狀和自訂法線對不上而變斑駁（smooth_fill_ridge 的兩個問題）"""
    from mathutils import kdtree
    fill = bpy.data.objects[arm.name.replace("_Armature", "_BodyFill")]
    me = fill.data

    def sstep(a, b, x):
        u = max(0.0, min(1.0, (x - a) / (b - a))); return u * u * (3 - 2 * u)

    vn = [n.vector.copy() for n in me.vertex_normals]
    kd = kdtree.KDTree(len(me.vertices))
    for v in me.vertices:
        kd.insert(v.co, v.index)
    kd.balance()
    w = {}
    for v in me.vertices:
        p = v.co; ax = abs(p.x)
        if p.y < 0.03 and 0.02 < ax < 0.18 and 1.235 < p.z < 1.30:
            ww = sstep(0.02, 0.04, ax) * (1 - sstep(0.16, 0.18, ax)) * sstep(1.235, 1.252, p.z) * (1 - sstep(1.285, 1.30, p.z))
            if ww > 0:
                w[v.index] = ww
    sm = {}
    for vi, ww in w.items():
        acc = Vector()
        for co, j, d in kd.find_range(me.vertices[vi].co, radius):
            if vn[j].dot(vn[vi]) > 0.0:                         # 不要抓到背面（身體另一側）的頂點
                acc += vn[j] * math.exp(-(d / (radius * 0.5)) ** 2)
        sm[vi] = acc.normalized() if acc.length > 1e-8 else vn[vi]
    old_n = [c.vector.copy() for c in me.corner_normals]
    out = []
    for li, lp in enumerate(me.loops):
        ww = w.get(lp.vertex_index, 0.0)
        n = old_n[li] * (1.0 - ww) + sm[lp.vertex_index] * ww if ww else old_n[li]
        out.append(n.normalized() if n.length > 1e-8 else old_n[li])
    me.normals_split_custom_set(out); me.update()
    print("FILLNORMALS verts", len(w), flush=True)


def smooth_fill_ridge(arm, iters=90, k=0.6, z_lo=1.232, z_hi=1.30):
    """補皮 _BodyFill 鎖骨那道棱的修正（第 3 關第 9 輪回饋「圈起來的兩塊是甚麼？是否為模型設計缺陷」）：
    rest 形狀在 z 1.29～1.31、|x| 0.03～0.14 往前凸，正上方 z 1.32 一下往後退 3 cm 多，肩膀外側那段法線朝下（屋簷）
    → MToon 畫出一道硬的勾狀陰影線。只在記憶體裡改網格資料（不存檔），範圍內做加權的鄰點平均（邊緣漸淡）。
    要在 make_neck_shade 之前呼叫（陰影殼複製的是網格資料）。
    只准往外補、不准往裡縮（每一步沿原本法線往內的分量拿掉）：一般的平均會把凸起削掉、補皮往裡退，底下的 _Body 就透出來。
    **補皮帶自訂法線（custom normals），MToon 照它畫明暗**：只改形狀，自訂法線照舊 → 棱照樣畫出來；形狀變了自訂法線還會歪成斑駁的一塊。
    所以磨完要把範圍內的自訂法線換成磨平後的頂點法線（照權重和原本的漸變，邊緣接得上 _Body）"""
    import bmesh as _bm
    fill = bpy.data.objects[arm.name.replace("_Armature", "_BodyFill")]

    def sstep(a, b, x):
        u = max(0.0, min(1.0, (x - a) / (b - a))); return u * u * (3 - 2 * u)

    me = fill.data
    old_n = [c.vector.copy() for c in me.corner_normals]
    bm = _bm.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    w = {}
    for v in bm.verts:
        p = v.co; ax = abs(p.x)
        if p.y < 0.035 and 0.015 < ax < 0.18 and z_lo < p.z < z_hi and not v.is_boundary:
            ww = sstep(0.015, 0.035, ax) * (1 - sstep(0.16, 0.18, ax)) * sstep(z_lo, z_lo + 0.015, p.z) * (1 - sstep(z_hi - 0.015, z_hi, p.z))
            if ww > 0:
                w[v] = ww
    n0 = {v: v.normal.copy() for v in w}
    for _ in range(iters):
        new = {}
        for v, ww in w.items():
            nb = [e.other_vert(v).co for e in v.link_edges]
            avg = sum(nb, Vector()) / len(nb)
            d = (avg - v.co) * k * ww
            dn = d.dot(n0[v])
            if dn < 0:
                d = d - n0[v] * dn
            new[v] = v.co + d
        for v, c in new.items():
            v.co = c
    wi = {v.index: ww for v, ww in w.items()}
    _mv = max(((v.co - me.vertices[v.index].co).length for v in w), default=0.0)
    print("FILLSMOOTH max move %.4f" % _mv, flush=True)
    bm.normal_update(); bm.to_mesh(me); bm.free(); me.update()
    vn = [n.vector.copy() for n in me.vertex_normals]
    out = []
    for li, lp in enumerate(me.loops):
        ww = wi.get(lp.vertex_index, 0.0)
        n = old_n[li] * (1.0 - ww) + vn[lp.vertex_index] * ww
        out.append(n.normalized() if n.length > 1e-8 else old_n[li])
    me.normals_split_custom_set(out); me.update()
    print("FILLSMOOTH verts", len(w), "loops", len(out), flush=True)


def make_thumbsup_shape(arm, side="L", name="V3_ThumbsUp", k=1.0):
    """比讚專用的手形（形狀鍵，/fix-animation 比讚第 8 版：使用者「目前的問題應該是建模的細節不像是比讚」）：
    VRoid 的手指是平滑的管子——沒有指節起伏、沒有拇指根部的肌肉、沒有指甲面，握拳比讚時側面看拇指只是一根管子。
    在 rest 空間（左手手指朝 +X、掌心朝 −Z、拇指在 −Y 側）照骨頭位置推頂點：
      ① 四指的指根關節、第二指節在手背側凸起（握拳時就是拳頭上的指節）
      ② 拇指根部（第 1 節）掌心側的肌肉鼓起
      ③ 拇指指尖關節收窄一點（側面看得出關節）、第 2、3 節指腹飽滿
      ④ 拇指尖背面壓平（指甲面）
    只在記憶體裡加形狀鍵（不存檔）；k＝整體強度。回傳形狀鍵"""
    import math as _m
    body = bpy.data.objects[arm.name.replace("_Armature", "_Body")]
    B = arm.data.bones
    me = body.data
    if not me.shape_keys:
        body.shape_key_add(name="Basis", from_mix=False)
    key = me.shape_keys.key_blocks.get(name) or body.shape_key_add(name=name, from_mix=False)
    base = [v.co.copy() for v in me.vertices]
    gn = {g.index: g.name for g in body.vertex_groups}
    g = lambda x, s: _m.exp(-(x / s) ** 2)
    S = "J_Bip_%s_" % side
    UPZ = Vector((0, 0, 1))
    hand_names = tuple(S + f for f in ("Hand", "Thumb", "Index", "Middle", "Ring", "Little"))

    def seg(n):
        return B[n].head_local.copy(), B[n].tail_local.copy()

    def radial(p, a, b):
        ax = (b - a); L = ax.length; ax = ax / L
        al = (p - a).dot(ax)
        r = p - (a + ax * al)
        return ax, al, L, r
    # 拇指的指腹方向：朝食指那邊（+Y）、偏掌心（−Z）；指甲面＝反方向
    pad_dir = Vector((0, 0.7, -0.7)).normalized()
    out = [Vector() for _ in me.vertices]
    for v in me.vertices:
        if not v.groups:
            continue
        own = gn[max(v.groups, key=lambda gg: gg.weight).group]
        if not own.startswith(hand_names):
            continue
        p = base[v.index]; d = Vector()
        # ① 四指指節（手背側 +Z）
        for f in ("Index", "Middle", "Ring", "Little"):
            for jn, amp, sw in ((S + f + "1", 0.0018, 0.006), (S + f + "2", 0.0012, 0.0045), (S + f + "3", 0.0005, 0.003)):
                a, b = seg(jn)
                ax, al, L, r = radial(p, a, b)
                if r.length > 0.02 or abs(al) > 0.012:
                    continue
                dors = r.normalized().dot(UPZ) if r.length > 1e-5 else 0.0
                if dors > 0.2:
                    d += UPZ * (amp * g(al, sw) * min(1.0, (dors - 0.2) / 0.5) * g(r.length, 0.014))
        # 拇指
        t1a, t1b = seg(S + "Thumb1"); t2a, t2b = seg(S + "Thumb2"); t3a, t3b = seg(S + "Thumb3")
        if own.startswith((S + "Thumb", S + "Hand")):
            # ② 拇指根部的肌肉（第 1 節中段的掌心側）
            ax, al, L, r = radial(p, t1a, t1b)
            if 0 <= al <= L and r.length < 0.022 and r.length > 1e-5:
                rn = r.normalized(); pdp = (pad_dir - ax * pad_dir.dot(ax)).normalized()
                facing = rn.dot(pdp)
                if facing > 0:
                    d += rn * (0.0025 * g(al / L - 0.55, 0.3) * facing)
            # ③ 指尖關節收窄、指腹飽滿；④ 指甲面
            for (a, b, nm) in ((t2a, t2b, "2"), (t3a, t3b, "3")):
                ax, al, L, r = radial(p, a, b)
                if al < -0.004 or al > L + 0.008 or r.length < 1e-5 or r.length > 0.016:
                    continue
                rn = r.normalized(); pdp = (pad_dir - ax * pad_dir.dot(ax)).normalized()
                facing = rn.dot(pdp)
                u = al / L
                if facing > 0:                                           # 指腹
                    d += rn * (0.0009 * g(u - 0.5, 0.3) * facing)
                if nm == "3":
                    d -= rn * (0.0007 * g(al, 0.003))                    # 指尖關節（第 3 節頭）收窄
                    if facing < -0.3:                                    # 指甲面壓平（遠端那一半）
                        d -= rn * (0.0008 * max(0.0, min(1.0, (u - 0.3) / 0.5)) * min(1.0, (-facing - 0.3) / 0.5))
        out[v.index] = d * k
    for i, v in enumerate(key.data):
        v.co = base[i] + out[i]
    key.value = 0.0
    mx = max(d.length for d in out)
    print("THUMBSUPSHAPE verts moved", sum(1 for d in out if d.length > 1e-5), "max_mm %.2f" % (mx * 1000), flush=True)
    return key


THUMBS_GLB = r"D:\render-work\assets\thumbsup_hand\thumbs_up_mrsnark.glb"   # Sketchfab「Thumbs up」by Mr. Snark（CC BY，影片要標作者）


def load_thumbs_hand(arm, frame, pose_fn, side="L", fist_extra=0.024):
    """比讚時換上的手（比讚第 9 版，使用者選 Sketchfab #3「Thumbs up」by Mr. Snark：VRoid 的手太簡單，調姿勢、塑形都做不出拇指）。
    GLB 的手：手腕切面在 +X、拳頭朝 −X、拇指朝 +Z、掌心朝 −Y（glb_probe 量的：切面中心 (0.059, 0.001, 0.049)、手腕到拳頭前端 12.3 cm）。
    在 frame 那一格把它對到新娘的手：拳頭方向＝手腕→中指根、拇指方向＝四指疊起來的方向（小指根→食指根）、
    大小＝新娘手腕到拳頭前端（手腕→中指根＋fist_extra）÷ 12.3 cm；左右手不同就鏡射。掛在手骨頭上跟著動。
    材質、描邊、藏原本的手在 mx_preview 做。回傳物件"""
    import bmesh as _bm
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=THUMBS_GLB)
    new = [o for o in bpy.data.objects if o not in before]
    mo = [o for o in new if o.type == "MESH"][0]
    mo.data = mo.data.copy()
    me = mo.data
    M0 = mo.matrix_world.copy()
    for v in me.vertices:                                                # 先把匯入的層層父物件變換烘進頂點（世界座標）
        v.co = M0 @ v.co
    mo.parent = None; mo.matrix_world = Matrix.Identity(4)
    for o in new:
        if o is not mo:
            bpy.data.objects.remove(o, do_unlink=True)
    cut_c = Vector((0.0591, 0.001, 0.049))
    # 拿掉手腕切面那片平的圓（近照頁第 9 版回饋「還是有一點斷層，可以看到手部材質的直線」：描邊沿著切面邊緣畫出一圈線）
    bm = _bm.new(); bm.from_mesh(me)
    cap = [f for f in bm.faces if f.normal.x > 0.9 and f.calc_center_median().x > cut_c.x - 0.002]
    _bm.ops.delete(bm, geom=cap, context="FACES_ONLY")
    bm.to_mesh(me); bm.free()
    a_g, t_g = Vector((-1, 0, 0)), Vector((0, 0, 1))
    palm_g = Vector((0, -1, 0))
    L_g = 0.1231
    pose_fn(frame); bpy.context.view_layer.update()
    mw = arm.matrix_world; pb = arm.pose.bones; S = "J_Bip_%s_" % side
    W = lambda n: mw @ pb[S + n].head
    wrist = W("Hand"); a_b = (W("Middle1") - wrist)
    L_b = a_b.length + fist_extra; a_b.normalize()
    t_b = (W("Index1") - W("Little1")); t_b = (t_b - a_b * t_b.dot(a_b)).normalized()
    tipc = (mw @ pb[S + "Middle3"].tail) - W("Middle1")
    n_b = a_b.cross(t_b)
    palm_b = n_b if n_b.dot(tipc) > 0 else -n_b
    n_g = a_g.cross(t_g)
    mirror = (n_g.dot(palm_g) > 0) != (n_b.dot(palm_b) > 0)
    if mirror:                                                           # 左右手不同：沿 n 軸鏡射（頂點 Y 反過來、法線翻面）
        bm = _bm.new(); bm.from_mesh(me)
        for v in bm.verts:
            v.co.y = 2 * cut_c.y - v.co.y
        _bm.ops.reverse_faces(bm, faces=list(bm.faces))
        bm.to_mesh(me); bm.free()
    s = L_b / L_g
    Rg = Matrix((a_g, t_g, a_g.cross(t_g))).transposed()
    Rb = Matrix((a_b, t_b, a_b.cross(t_b))).transposed()
    rot = (Rb @ Rg.inverted()).to_4x4()
    Mw = Matrix.Translation(wrist) @ rot @ Matrix.Scale(s, 4) @ Matrix.Translation(-cut_c)
    for v in me.vertices:
        v.co = Mw @ v.co
    # 手腕收細（第 9 版自我審查：GLB 的手腕切面縮放後約是新娘手腕的 1.7 倍粗，側面看手腕突然變寬）：
    #   量新娘 rest 手腕那一圈在「拇指方向／掌心方向」的半寬，量 GLB 切面同兩個方向的半寬，
    #   切面那裡縮到一樣、往拳頭 taper 公分內漸變回原本
    B = arm.data.bones
    body = bpy.data.objects[arm.name.replace("_Armature", "_Body")]
    ra = (B[S + "Hand"].tail_local - B[S + "Hand"].head_local).normalized()
    rt = B[S + "Index1"].head_local - B[S + "Little1"].head_local; rt = (rt - ra * rt.dot(ra)).normalized()
    rn = ra.cross(rt)
    h0 = B[S + "Hand"].head_local
    ring = [v.co - h0 for v in body.data.vertices if abs((v.co - h0).dot(ra)) < 0.004 and (v.co - h0 - ra * (v.co - h0).dot(ra)).length < 0.04]
    # 上下左右各自對齊（第 9 版回饋「下邊緣與小手臂沒有修成一直線」：手骨頭不在手腕正中間、偏手背，對稱縮放時手掌側縮過頭）
    bt1, bt0 = max(p.dot(rt) for p in ring), min(p.dot(rt) for p in ring)
    bn1, bn0 = max(p.dot(rn) for p in ring), min(p.dot(rn) for p in ring)
    nb_ = a_b.cross(t_b)
    cutv = [v.co - wrist for v in me.vertices if abs((v.co - wrist).dot(a_b)) < 0.003]
    gt1, gt0 = max(p.dot(t_b) for p in cutv), min(p.dot(t_b) for p in cutv)
    gn1, gn0 = max(p.dot(nb_) for p in cutv), min(p.dot(nb_) for p in cutv)
    taper, tuck = 0.035, 0.008

    def sst(x):
        u = max(0.0, min(1.0, x)); return u * u * (3 - 2 * u)

    def remap(c, g0, g1, b0, b1, w):
        # 切面上的 [g0, g1] 對到新娘手腕的 [b0, b1]，往拳頭漸變回原本
        u = (c - g0) / max(1e-6, g1 - g0)
        cb = b0 + (b1 - b0) * u
        return cb + (c - cb) * w
    for v in me.vertices:
        p = v.co - wrist; d = p.dot(a_b)
        w = sst(d / taper)
        ct, cn_ = p.dot(t_b), p.dot(nb_)
        ct2, cn2 = remap(ct, gt0, gt1, bt0, bt1, w), remap(cn_, gn0, gn1, bn0, bn1, w)
        if d < 0.004:                                                     # 手腕末端往小臂裡伸 8 mm、縮 4%，接縫藏進小臂皮膚
            k_ = 1.0 - max(0.0, (0.004 - d) / 0.004)
            d -= tuck * (1 - k_); ct2 *= 1 - 0.04 * (1 - k_); cn2 *= 1 - 0.04 * (1 - k_)
        v.co = wrist + a_b * d + t_b * ct2 + nb_ * cn2
    bt, bn, gt, gn_ = (bt1 - bt0) / 2, (bn1 - bn0) / 2, (gt1 - gt0) / 2, (gn1 - gn0) / 2
    kt, kn = bt / gt, bn / gn_
    print("THUMBSHAND wrist bride %.1f×%.1f mm, glb %.1f×%.1f mm → ×%.2f ×%.2f" % (bt * 2000, bn * 2000, gt * 2000, gn_ * 2000, kt, kn), flush=True)
    me.update()
    # 掛在手骨頭上（保持現在的世界位置）
    Pb = mw @ pb[S + "Hand"].matrix
    mo.parent = arm; mo.parent_type = "BONE"; mo.parent_bone = S + "Hand"
    bpy.context.view_layer.update()
    mo.matrix_world = Matrix.Identity(4)
    mo.name = "V3_ThumbsHand"
    for f in me.polygons:
        f.use_smooth = True
    print("THUMBSHAND scale %.3f mirror %s L_b %.3f verts %d" % (s, mirror, L_b, len(me.vertices)), flush=True)
    return mo


def make_thumb_nail(arm, side="L", color="#4A1C24", gain=2 ** 0.25, line=0.13, k=1.0):
    """拇指指甲的輪廓（比讚第 8 版）：卡通角色靠指甲讓人認出「這是手指」。在拇指第 3 節遠端的指甲面（指腹的反面）
    畫一個橢圓細框（沿手指長 A、寬 Bw），用 make_skin_shade 貼在皮膚上。rest 空間：拇指指腹朝 +Y／−Z"""
    import math as _m
    B = arm.data.bones
    S = "J_Bip_%s_" % side
    a, b = B[S + "Thumb3"].head_local.copy(), B[S + "Thumb3"].tail_local.copy()
    ax = (b - a); L = ax.length; ax = ax / L
    pad = Vector((0, 0.7, -0.7)); pad = (pad - ax * pad.dot(ax)).normalized()
    nail = -pad; sidev = ax.cross(nail).normalized()
    c_al, A, Bw = L * 0.75, 0.0062 * k, 0.0042 * k                   # 指甲中心在第 3 節 75% 處、長 1.24 cm、寬 0.84 cm

    def keep(p):
        al = (p - a).dot(ax)
        r = p - (a + ax * al)
        return -0.003 < al < L + 0.012 and r.length < 0.016 and (r.length < 1e-5 or r.normalized().dot(nail) > -0.2)

    def alpha(p):
        al = (p - a).dot(ax)
        r = p - (a + ax * al)
        if r.length < 1e-5 or r.normalized().dot(nail) < 0.15:
            return 0.0
        rn = r.normalized()
        lat = _m.atan2(rn.dot(sidev), rn.dot(nail)) * r.length
        e = ((al - c_al) / A) ** 2 + (lat / Bw) ** 2
        return max(0.0, 1.0 - abs(_m.sqrt(e) - 1.0) / line)
    return make_skin_shade(arm, "V3_ThumbNail", keep, alpha, color=color, subdiv=3, offset=0.0012, flat_gain=gain)


def make_thumb_crease(arm, frame, pose_fn, cam_pos, side="L", color="#4A1C24", strength=1.0, half=0.0009, gain=2 ** 0.25):
    """拇指關節摺痕線（/fix-animation「大拇指面對鏡頭的指節不清楚」）：VRoid 手指網格沒有關節摺痕，身體描邊只畫外輪廓，
    面向鏡頭的拇指是一整片平的。在拇指第 2 節頭（根部關節）、第 3 節頭（指尖關節）各畫一條細線（寬 2×half），
    只畫在 frame 那一格面向鏡頭的那一側（比讚的姿勢固定，這一格代表整段）。用 make_skin_shade 貼在皮膚上、跟著骨頭動。
    pose_fn(frame)＝把角色擺到那一格（mx_preview 的 pose_at）"""
    def sstep(a, b, x):
        u = max(0.0, min(1.0, (x - a) / (b - a))); return u * u * (3 - 2 * u)

    B = arm.data.bones
    joints = []
    for jb, db in (("J_Bip_%s_Thumb2" % side, "J_Bip_%s_Thumb2" % side), ("J_Bip_%s_Thumb3" % side, "J_Bip_%s_Thumb3" % side)):
        J = B[jb].head_local.copy(); a = (B[jb].tail_local - B[jb].head_local).normalized()
        joints.append((J, a, db))
    pose_fn(frame); bpy.context.view_layer.update()
    mw = arm.matrix_world
    D = {db: arm.pose.bones[db].matrix @ B[db].matrix_local.inverted() for _J, _a, db in joints}
    cam = Vector(cam_pos)                       # 影片鏡頭的位置（建場景時 scene.camera 還不是這一幕的鏡頭 → 方向全錯，第一版只剩一個小點）

    def keep(p):
        for J, a, _db in joints:
            al = (p - J).dot(a)
            if abs(al) < 0.006 and (p - J - a * al).length < 0.016:
                return True
        return False

    def alpha(p):
        best = 0.0
        for J, a, db in joints:
            al = (p - J).dot(a)
            line = max(0.0, 1.0 - abs(al) / half)
            if line <= 0:
                continue
            rad = p - J - a * al
            if rad.length < 1e-5 or rad.length > 0.016:
                continue
            rp = (D[db].to_3x3() @ rad.normalized()).normalized()
            pw = mw @ (D[db] @ p)
            facing = rp.dot((cam - pw).normalized())
            best = max(best, strength * line * (1.0 if half > 0.002 else sstep(0.35, 0.6, facing)))      # 只留面向鏡頭的中間一段（像摺痕，不是一整圈戒指）；除錯（粗線）不篩方向
        return best
    return make_skin_shade(arm, "V3_ThumbCrease", keep, alpha, color=color, subdiv=3, offset=0.0012, flat_gain=gain)   # 0.6 mm 時根部那條中間沉進皮膚


def make_neck_shade(arm, strength=0.8, clav=0.45, color="#F0B9B5", gain=2 ** 0.25):
    """脖子陰影＋鎖骨線（第 3 關第 8 輪回饋「新娘脖子不明顯，輪廓看不出有脖子，胸口一大片空」），用 make_skin_shade 貼在皮膚上。
    動畫角色的畫法：下巴下整段脖子在陰影裡、下緣在脖子底切清楚 → 一眼看出「這裡是脖子、下面才是胸口」；鎖骨兩道淡線把胸口分出結構。
    胸口、肩膀、脖子大半是補皮 _BodyFill（不是 _Body），兩個都貼一層，回傳 [殼, …]。
    補皮 rest（fill_probe 量的）：衣服上緣 z 1.25、脖子底的凹處 z 1.30（x=0 往後凹到 y −0.027）、鎖骨頭在 x ±0.02 z 1.30 往前凸、
    下巴尖 z 1.351、脖子前面 z 1.31～1.35 半寬約 0.045。
    （前幾版只貼 _Body：胸口那片藏在補皮底下，只剩下巴下一條和荷葉邊上兩個點）
    顏色＝她身上 MToon 原本的粉色陰影：畫面上量到 (222,171,168)，Standard 色彩、曝光 −0.25 → 自發光 #F0B9B5 × 2**0.25。
    _Body 那層只留下巴正下方一條（|x|<0.03，畫面上只有那裡的 _Body 在補皮前面；_Body 的面很大，0.016 會漏掉面、中間變一條亮的），
    其他地方兩層疊在一起會打架出條紋。整片同一個深淺（兩側加深會和 MToon 自己的陰影疊出深色直條）"""
    def sstep(a, b, x):
        u = max(0.0, min(1.0, (x - a) / (b - a))); return u * u * (3 - 2 * u)

    def keep(p):
        return 1.285 <= p.z <= 1.358 and abs(p.x) < 0.125 and p.y < 0.03

    def alpha(p):
        ax = abs(p.x)
        hw = 0.044 + max(0.0, 1.315 - p.z) * 1.0                                      # 脖子半寬（往下到脖子底張開）
        z_edge = 1.306 + 6.0 * min(ax, hw) ** 2                                       # 下緣：中間最低、兩側往上彎（U 形）
        neck = (1.0 - sstep(hw - 0.006, hw + 0.002, ax)) * sstep(z_edge - 0.0015, z_edge + 0.0015, p.z)
        u = max(0.0, min(1.0, (ax - 0.022) / 0.08))                                  # 鎖骨：脖子底往肩膀微微往上、中段略下彎
        zc = 1.300 + 0.015 * u - 0.003 * math.sin(math.pi * u)
        cl = max(0.0, 1.0 - abs(p.z - zc) / 0.0028) * sstep(0.022, 0.034, ax) * (1.0 - sstep(0.085, 0.105, ax))
        return max(strength * neck, clav * cl)
    return [make_skin_shade(arm, "V3_NeckShade", lambda p: keep(p) and abs(p.x) < 0.03, alpha, color=color, subdiv=4, flat_gain=gain),
            make_skin_shade(arm, "V3_NeckShadeFill", keep, alpha, color=color, subdiv=2, src="_BodyFill", offset=0.0012, flat_gain=gain)]


def _surface_sampler(arm, zlo, zhi, center=(0.0, 0.03)):
    """身體網格（rest）在 zlo～zhi 這段的前半圈頂點 → fn(角度, z) 回傳離 center（俯視）的表面半徑"""
    body = bpy.data.objects.get(arm.name.replace("_Armature", "_Body"))
    Mb = arm.matrix_world.inverted() @ body.matrix_world
    samp = []
    for vv in body.data.vertices:
        p = Mb @ vv.co
        if zlo <= p.z <= zhi:
            d = Vector((p.x - center[0], p.y - center[1]))
            if d.length > 1e-4 and d.y < 0.015:
                samp.append((math.atan2(d.x, -d.y), p.z, d.length))

    def radius(th, z):
        best = 0.0; wsum = rsum = 0.0
        for t_, z_, r_ in samp:
            w = math.exp(-((t_ - th) / 0.12) ** 2 - ((z_ - z) / 0.005) ** 2)
            wsum += w; rsum += w * r_
        return rsum / wsum if wsum > 1e-6 else 0.06
    return radius


def _bone_attach(o, arm, bone):
    B = arm.data.bones[bone]; pb = arm.pose.bones[bone]
    bpy.context.view_layer.update()
    P = arm.matrix_world @ pb.matrix @ B.matrix_local.inverted()
    o.parent = arm; o.parent_type = "BONE"; o.parent_bone = bone
    bpy.context.view_layer.update()
    o.matrix_world = P


def make_necklace_skin(arm, r_pearl=0.0042, half_w=0.05, z_front=1.288, z_side=1.322, src="_BodyFill"):
    """珍珠項鍊（貼皮膚版）：沿脖子底繞前半圈，每顆珍珠放在身體網格「那個位置最前面的頂點」外面（沿頂點法線推出珠子半徑），
    珠子的頂點照那個身體頂點的權重綁到骨架 → 跟皮膚一起動。前面中間一顆水滴形大珍珠。
    （第一版用「猜表面形狀」的取樣，抓到手臂的頂點，珠子飄到肩膀外；第二版貼在 _Body，但脖子底、胸口露出來的是補皮 _BodyFill，
    珠子藏在補皮底下只露出幾顆。第 3 關第 9 輪使用者要「加上項鍊」：改貼補皮、珠子 4.2 mm、繞在脖子底（前 z 1.288、兩側 z 1.322））"""
    import bmesh as _bm
    body = bpy.data.objects[arm.name.replace("_Armature", src)]
    bv = body.data.vertices
    cand = [v for v in bv if 1.26 <= v.co.z <= 1.35 and abs(v.co.x) < half_w + 0.02 and v.co.y < 0.04]

    def surf(x, z):
        near = [v for v in cand if abs(v.co.x - x) < 0.006 and abs(v.co.z - z) < 0.006]
        if not near:
            near = sorted(cand, key=lambda v: (v.co.x - x) ** 2 + (v.co.z - z) ** 2)[:3]
        v = min(near, key=lambda v: v.co.y)                          # 最前面（−Y）
        return v
    path = []
    for k in range(161):
        s = -1 + 2 * k / 160
        path.append((half_w * s, z_front + (z_side - z_front) * s * s))
    pts = []
    for x, z in path:
        v = surf(x, z); n = v.normal.normalized()
        pts.append((v.co + n * (r_pearl + 0.0006), v))
    # 每個取樣點各自抓最近的皮膚頂點，抓到的點忽前忽後 → 珠子一團一團、中間有空隙。先把路徑順平（移動平均 3 次），再照弧長等距放
    sm = [p for p, _ in pts]
    for _ in range(3):
        sm = [sum(sm[max(0, i - 7):i + 8], Vector()) / len(sm[max(0, i - 7):i + 8]) for i in range(len(sm))]
    cum = [0.0]
    for a, b in zip(sm, sm[1:]):
        cum.append(cum[-1] + (b - a).length)
    step = 2 * r_pearl * 1.08; placed = []; i = 0; s_ = 0.0
    while s_ <= cum[-1]:
        while i < len(cum) - 2 and cum[i + 1] < s_:
            i += 1
        t = (s_ - cum[i]) / max(1e-9, cum[i + 1] - cum[i])
        placed.append((sm[i].lerp(sm[i + 1], t), pts[i][1]))
        s_ += step
    mid = min(pts, key=lambda pv: abs(pv[0].x))
    drop = (mid[0] + mid[1].normal.normalized() * 0.003 + Vector((0, 0, -0.011)), mid[1])
    me = bpy.data.meshes.new("V3_Necklace"); bm = _bm.new()
    owners = []
    for i, (p, v) in enumerate(placed + [drop]):
        big = i == len(placed)
        M = Matrix.Translation(p) @ (Matrix.Diagonal((1.0, 1.0, 1.35, 1.0)) if big else Matrix.Identity(4))
        before = len(bm.verts)
        _bm.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.0062 if big else r_pearl, matrix=M)
        owners += [v.index] * (len(bm.verts) - before)
    bm.to_mesh(me); bm.free()
    for f in me.polygons:
        f.use_smooth = True
    me.materials.append(pmat("V3_Pearl", srgb("#F8F3EA"), rough=0.18, spec=0.8, coat=0.8, sheen=0.3))
    o = bpy.data.objects.get("V3_Necklace")
    if o:
        bpy.data.objects.remove(o, do_unlink=True)
    o = bpy.data.objects.new("V3_Necklace", me)
    for c in body.users_collection:
        c.objects.link(o)
    o.matrix_world = body.matrix_world.copy()
    gname = {g.index: g.name for g in body.vertex_groups}
    for vi_new, vi_body in enumerate(owners):
        for ge in bv[vi_body].groups:
            nm = gname[ge.group]
            g = o.vertex_groups.get(nm) or o.vertex_groups.new(name=nm)
            g.add([vi_new], ge.weight, "REPLACE")
    md = o.modifiers.new("Armature", "ARMATURE"); md.object = arm
    o.parent = body.parent
    o.visible_shadow = False                         # 珍珠投在皮膚上的細碎陰影，低取樣下變成一塊斑駁的雜點
    print("NECKLACE pearls", len(placed), flush=True)
    return o


def make_necklace(arm, r_pearl=0.0034):
    """珍珠項鍊（第 3 關第 8 輪「胸口一大片空」的試做，和耳環同款）：沿脖子底繞前半圈，兩側 z 1.30、前面垂到 z 1.262，
    珠子貼在皮膚外（照身體網格的表面）；前面中間多一顆水滴形的大珍珠。掛在上胸骨頭"""
    import bmesh as _bm
    radius = _surface_sampler(arm, 1.24, 1.32)
    pts = []
    for k in range(121):
        th = math.radians(-82 + 164 * k / 120)
        z = 1.300 - 0.038 * math.cos(th) ** 2
        r = radius(th, z) + r_pearl + 0.0008
        pts.append(Vector((r * math.sin(th), 0.03 - r * math.cos(th), z)))
    bm = _bm.new()
    acc = 0.0; last = pts[0]; placed = [pts[0]]
    for p in pts[1:]:
        acc += (p - last).length; last = p
        if acc >= 2 * r_pearl * 1.08:
            placed.append(p); acc = 0.0
    for p in placed:
        _bm.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=r_pearl, matrix=Matrix.Translation(p))
    front = Vector((0, 0.03 - radius(0.0, 1.262) - 0.007, 1.262 - 0.012))
    m_ = Matrix.Translation(front) @ Matrix.Diagonal((1.0, 1.0, 1.35, 1.0))
    _bm.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.0062, matrix=m_)
    me = bpy.data.meshes.new("V3_Necklace"); bm.to_mesh(me); bm.free()
    for f in me.polygons:
        f.use_smooth = True
    me.materials.append(pmat("V3_Pearl", srgb("#F8F3EA"), rough=0.18, spec=0.8, coat=0.8, sheen=0.3))
    o = bpy.data.objects.get("V3_Necklace")
    if o:
        bpy.data.objects.remove(o, do_unlink=True)
    o = bpy.data.objects.new("V3_Necklace", me); bpy.context.scene.collection.objects.link(o)
    _bone_attach(o, arm, "J_Bip_C_UpperChest")
    return o


def make_clavicles(arm, color="#D99A8E", strength=0.5):
    """鎖骨線（試做）：胸口兩側從脖子底（x ±0.018、z 1.288）往肩膀（x ±0.085、z 1.298）兩道淡淡的陰影，寬 6 mm、兩端漸淡。掛在上胸骨頭"""
    import bmesh as _bm
    radius = _surface_sampler(arm, 1.26, 1.32)
    me = bpy.data.meshes.new("V3_Clavicles"); bm = _bm.new(); alph = []
    for sg in (-1, 1):
        rows = []
        for k in range(17):
            u = k / 16
            x = sg * (0.018 + 0.067 * u); z = 1.288 + 0.010 * u + 0.006 * math.sin(math.pi * u)
            row = []
            for w in (-0.003, 0.003):
                zz = z + w
                th = math.atan2(x, 0.03 + 0.05)
                # 用 x 反推角度：在這個高度找表面
                r = radius(math.atan2(x, max(0.02, 0.03 - (-0.03))), zz)
                th = math.asin(max(-0.99, min(0.99, x / max(r, 1e-3))))
                r = radius(th, zz) + 0.003
                row.append(bm.verts.new((r * math.sin(th), 0.03 - r * math.cos(th), zz)))
            rows.append(row); alph.append(strength * math.sin(math.pi * u) ** 0.8)
        for k in range(16):
            bm.faces.new((rows[k][0], rows[k + 1][0], rows[k + 1][1], rows[k][1]))
    bm.to_mesh(me); bm.free()
    attr = me.color_attributes.new("a", "FLOAT_COLOR", "POINT")
    for i in range(len(attr.data)):
        a = alph[i // 2]; attr.data[i].color = (a, a, a, 1.0)
    m = bpy.data.materials.get("V3_NeckShadow")
    me.materials.append(m)
    o = bpy.data.objects.get("V3_Clavicles")
    if o:
        bpy.data.objects.remove(o, do_unlink=True)
    o = bpy.data.objects.new("V3_Clavicles", me); bpy.context.scene.collection.objects.link(o)
    o.visible_shadow = False
    _bone_attach(o, arm, "J_Bip_C_UpperChest")
    return o


def feast_layout(TC, TOP):
    """原有的桌上東西挪到 ⑦a 的位置；新郎那份收起來"""
    L = FEAST_LAYOUT
    place = {"V2_MainPlate": L["main"], "V2_FruitPlate": L["fruit"], "V2_WineBottle": L["bottle"]}
    for i, q in enumerate(L["desserts"]):
        place[f"V2_Dessert{i}"] = q
    for nm, q in place.items():
        o = bpy.data.objects.get(nm)
        if o:
            o.location = (q[0], q[1], o.location.z)
    for nm in ("V2_Wine_groom", "V2_Napkin0", "V2_Candle", "V2_ChairG"):
        o = bpy.data.objects.get(nm)
        if o:
            for oo in [o] + list(o.children_recursive):
                oo.hide_render = True; oo.hide_viewport = True
    e = bpy.data.objects.get("V2_Easel")
    if e:
        for oo in [e] + list(e.children_recursive):
            oo.hide_render = True; oo.hide_viewport = True
    return Vector((TC[0] + L["glass"][0], TC[1] + L["glass"][1], TOP))
