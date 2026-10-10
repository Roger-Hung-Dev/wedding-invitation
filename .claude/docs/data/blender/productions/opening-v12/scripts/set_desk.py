# 「俯拍木桌信紙」景（①、②前段、④、⑥、⑧前段與結尾；③原本的版本也用這個景）。
# 桌面在 z=0；鏡頭從正上方往下拍（畫面上方＝+Y）。尺寸是真實尺寸（公尺）：信紙 0.28×0.19、信封 0.21×0.15、拍立得 0.085×0.126。
# build_desk() 建全部道具；每幕用 desk_layout_*() 擺位置、開關，*_update(t) 做道具動作。
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

LET_W, LET_H = 0.28, 0.19          # 信紙（攤開；對摺後 0.14×0.19）
ENV_W, ENV_H = 0.21, 0.15          # 信封
PL_W, PL_H = 0.085, 0.126          # 拍立得卡；照片區 0.075×0.088（比例 0.852），上緣、左右白邊 0.005，下緣 0.033
PH_W, PH_H = 0.075, 0.088
DESK = {}
RIB_X = 0.024                      # 直向緞帶偏右（不擋螢幕中間的鈴鐺）
RIB_Y = -0.038                     # 手機緞帶十字交叉點（在螢幕下方 1/4，鈴鐺露出來）


def build_desk():
    coll_clear("Set_Desk")
    c = coll_new("Set_Desk")
    random.seed(3)
    # 木桌：淺橡木＋木紋（波紋＋雜訊）＋木板接縫
    wood = bpy.data.materials.get("D_Wood") or bpy.data.materials.new("D_Wood")
    wood.use_nodes = True; nt = wood.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); bsd = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (3.0, 60.0, 1.0)
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 12.0
    nz.inputs["Roughness"].default_value = 0.62; nz.inputs["Distortion"].default_value = 0.8
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35; ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[0].color = srgb("#9C7552", 1); ramp.color_ramp.elements[1].color = srgb("#C29B73", 1)
    brick = nt.nodes.new("ShaderNodeTexBrick")                       # 木板接縫（每 0.14 m 一塊、每塊明暗略不同）
    brick.inputs["Scale"].default_value = 1.0; brick.inputs["Mortar Size"].default_value = 0.0025
    brick.inputs["Brick Width"].default_value = 1.6; brick.inputs["Row Height"].default_value = 0.14
    brick.inputs["Color1"].default_value = (1, 1, 1, 1); brick.inputs["Color2"].default_value = (0.86, 0.84, 0.82, 1)
    brick.inputs["Mortar"].default_value = srgb("#5A3E2A", 1)
    mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"; mul.inputs["Factor"].default_value = 1.0
    nt.links.new(tc.outputs["Object"], mp.inputs[0]); nt.links.new(mp.outputs[0], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"]); nt.links.new(tc.outputs["Object"], brick.inputs["Vector"])
    nt.links.new(ramp.outputs["Color"], mul.inputs["A"]); nt.links.new(brick.outputs["Color"], mul.inputs["B"])
    nt.links.new(mul.outputs["Result"], bsd.inputs["Base Color"])
    bsd.inputs["Roughness"].default_value = 0.6; bsd.inputs["Specular IOR Level"].default_value = 0.3
    nt.links.new(bsd.outputs[0], out.inputs["Surface"])
    bm = bmesh.new(); box(bm, Vector((0, 0, -0.02)), (1.6, 1.0, 0.04))
    mesh_obj("D_Desk", bm, wood, c)
    paper = pmat("D_Paper", PAL["paper"], rough=0.92, spec=0.15, noise=0.12, bump=0.12, sheen=0.3)
    env_m = pmat("D_Envelope", srgb("#F1E2CC"), rough=0.9, spec=0.15, noise=0.12, bump=0.1)
    env_line = pmat("D_EnvLine", srgb("#DCC7AA"), rough=0.9, spec=0.1)
    wax = pmat("D_Wax", PAL["rose"], rough=0.3, spec=0.6, coat=0.4)
    # 信紙：右半（不動）＋左半（繞中線翻開）；Letter 空物件管位置與旋轉
    let = empty("D_Letter", c)
    bm = bmesh.new(); grid(bm, LET_W / 2, LET_H, 6, 8, c=(LET_W / 4, 0, 0))
    mesh_obj("D_LetterR", bm, paper, c, parent=let)
    hinge = empty("D_LetterHinge", c, parent=let)
    bm = bmesh.new(); grid(bm, LET_W / 2, LET_H, 6, 8, c=(-LET_W / 4, 0, 0))
    mesh_obj("D_LetterL", bm, paper, c, parent=hinge)
    # 信紙上的水彩拱門小畫（②、⑧用；在左半張）
    wc = os.path.join(TEX, "watercolor_arch.png")
    if os.path.exists(wc):
        pm = pmat("D_Painting", (1, 1, 1), rough=0.9, spec=0.1, img=wc, img_alpha=True)
        bm = bmesh.new(); quad(bm, 0.096, 0.072)
        o = mesh_obj("D_Painting", bm, pm, c, parent=let); o.location = (0.0, 0.0, 0.0006)
    # 信封：身體（背面朝上，看得到封口三角蓋）＋折線＋封口蓋（繞上緣翻開）＋蠟封（兩半，裂開）
    env = empty("D_Env", c)
    bm = bmesh.new(); box(bm, Vector((0, 0, 0.0015)), (ENV_W, ENV_H, 0.003))
    mesh_obj("D_EnvBody", bm, env_m, c, parent=env)
    bm = bmesh.new()
    for a, b in (((-ENV_W / 2, -ENV_H / 2), (-0.01, 0.01)), ((ENV_W / 2, -ENV_H / 2), (0.01, 0.01))):   # 下方兩條斜折線
        pa, pb = Vector((*a, 0.0032)), Vector((*b, 0.0032)); v = pb - pa
        box(bm, (pa + pb) / 2, (0.0009, v.length, 0.0002), rot=Matrix.Rotation(math.atan2(-v.x, v.y), 4, "Z"))
    mesh_obj("D_EnvLines", bm, env_line, c, parent=env)
    flap_h = empty("D_FlapHinge", c, (0, ENV_H / 2, 0.0034), parent=env)
    bm = bmesh.new()
    pts = [(-ENV_W / 2, 0), (ENV_W / 2, 0)] + [(0.03 * math.cos(a), -0.088 + 0.012 * math.sin(a)) for a in [math.radians(x) for x in range(0, -181, -30)]]
    vs = [bm.verts.new((x, y, 0.0)) for x, y in pts]
    f = bm.faces.new(vs); bmesh.ops.solidify(bm, geom=[f], thickness=0.0008)
    mesh_obj("D_Flap", bm, env_m, c, parent=flap_h)
    bm = bmesh.new()                                   # 封口蓋的兩條斜邊（看得出蓋子的輪廓）
    for sx in (-1, 1):
        pa, pb = Vector((sx * ENV_W / 2, -0.001, 0.0009)), Vector((sx * 0.03, -0.088, 0.0009)); v = pb - pa
        box(bm, (pa + pb) / 2, (0.0011, v.length, 0.0003), rot=Matrix.Rotation(math.atan2(-v.x, v.y), 4, "Z"))
    mesh_obj("D_FlapLines", bm, env_line, c, parent=flap_h)
    seal_build(c, wax, flap_h, env)
    # 乾燥薰衣草（三枝，麻繩綁）
    lav = pmat("D_Lavender", srgb("#9C84B5"), rough=0.8, spec=0.2, noise=0.2)
    stem = pmat("D_LavStem", srgb("#8C9A78"), rough=0.85)
    twine = pmat("D_Twine", srgb("#C8A77E"), rough=0.9)
    lv = empty("D_LavenderSprig", c)
    bm = MB()
    for k, ang in enumerate((-0.12, 0.0, 0.13)):
        d = Vector((math.sin(ang), math.cos(ang), 0))
        p0 = d * -0.06
        cyl(bm, p0 + d * 0.06 + Vector((0, 0, 0.0018)), 0.0013, 0.13, seg=6, mi=1, rot=d.to_track_quat("Z", "Y").to_matrix().to_4x4())
        for j in range(40):
            u = j / 40
            p = p0 + d * (0.075 + 0.055 * u) + Vector((0, 0, 0.0035))
            sd = Vector((-d.y, d.x, 0)) * (0.0028 * (1 if j % 2 else -1))
            ball(bm, p + sd, (0.0017, 0.0026, 0.0016), mi=0, seg=6)
    ring(bm, Vector((0, -0.03, 0.002)), 0.006, 0.0012, seg=10, mi=2)
    mesh_obj("D_Lavender", bm, [lav, stem, twine], c, smooth=True, parent=lv)
    # 鋼筆（墨褐筆身＋金色筆夾、筆尖）
    body = pmat("D_PenBody", PAL["ink"], rough=0.25, spec=0.7, coat=0.6)
    gold = pmat("D_Gold", PAL["gold"], rough=0.25, spec=0.7, metal=0.9)
    pen = empty("D_Pen", c)
    bm = bmesh.new()
    cyl(bm, Vector((0, 0.0, 0.0068)), 0.0068, 0.1, axis="Y", seg=20, mi=0)
    cyl(bm, Vector((0, 0.058, 0.0068)), 0.0068, 0.016, axis="Y", seg=20, mi=1)
    cyl(bm, Vector((0, -0.062, 0.0068)), 0.0068, 0.024, axis="Y", seg=20, r2=0.0045, mi=0)
    cyl(bm, Vector((0, -0.08, 0.0055)), 0.0035, 0.016, axis="Y", seg=12, r2=0.0008, mi=1)
    box(bm, Vector((0, 0.03, 0.0142)), (0.0025, 0.045, 0.0018), mi=1)
    mesh_obj("D_PenMesh", bm, [body, gold], c, smooth=True, parent=pen)
    # 押花（貼圖片）
    for k, nm_ in enumerate(("pf_lavender", "pf_rose", "pf_white", "pf_blush", "pf_leaf", "pf_rose", "pf_lavender")):
        decal(f"D_PF{k}", os.path.join(TEX, nm_ + ".png"), 0.042 if "leaf" not in nm_ else 0.06, c, loc=(0, 0, -1))
    # 拍立得×2（卡＋顯影照片＋紙膠帶）
    card = pmat("D_PolaCard", srgb("#FCFBF8"), rough=0.4, spec=0.45, noise=0.05)
    for key in ("groom", "bride"):
        e = empty(f"D_Pola_{key}", c)
        bm = bmesh.new(); box(bm, Vector((0, 0, 0.0004)), (PL_W, PL_H, 0.0008))
        mesh_obj(f"D_PolaCard_{key}", bm, card, c, parent=e)
        m = develop_mat(f"D_Photo_{key}", os.path.join(PHOTO, f"polaroid_{key}.jpg"))
        bm = bmesh.new(); quad(bm, PH_W, PH_H)
        o = mesh_obj(f"D_PolaPhoto_{key}", bm, m, c, parent=e); o.location = (0, PL_H / 2 - 0.005 - PH_H / 2, 0.00085)
        t = decal(f"D_Tape_{key}", os.path.join(TEX, "washi_lavender.png" if key == "groom" else "washi_rose.png"), 0.05, c, parent=e)
        t.location = (0, PL_H / 2 - 0.002, 0.0011)
    # 手機（緞帶綁成禮物）
    case = pmat("D_PhoneCase", srgb("#E9DCE8"), rough=0.35, spec=0.6)
    bezel = pmat("D_PhoneBezel", srgb("#2C2628"), rough=0.3, spec=0.6)
    ph = empty("D_Phone", c)
    bm = bmesh.new(); box(bm, Vector((0, 0, 0.004)), (0.066, 0.134, 0.0075), mi=0); box(bm, Vector((0, 0, 0.0079)), (0.062, 0.13, 0.0002), mi=1)
    o = mesh_obj("D_PhoneBody", bm, [case, bezel], c, parent=ph)
    bv = o.modifiers.new("Bevel", "BEVEL"); bv.width = 0.004; bv.segments = 4
    for nm_ in ("phone_bell", "phone_bell_off"):
        m = pmat("D_" + nm_, (1, 1, 1), rough=0.2, spec=0.6, img=os.path.join(TEX, nm_ + ".png"), emit=0.9)
        bm = bmesh.new(); quad(bm, 0.0585, 0.1215)
        o = mesh_obj("D_" + nm_, bm, m, c, parent=ph); o.location = (0, 0, 0.0081)
    rib = pmat("D_Ribbon", PAL["rose"], rough=0.35, spec=0.6, sheen=0.7)
    for k, (w, h, rot) in enumerate(((0.074, 0.016, 0), (0.016, 0.142, 0))):
        cu = bpy.data.curves.get(f"D_RibbonBand{k}") or bpy.data.curves.new(f"D_RibbonBand{k}", "CURVE")
        cu.dimensions = "3D"; cu.splines.clear(); cu.extrude = 0.0065; cu.resolution_u = 4
        sp = cu.splines.new("POLY")
        # 繞手機一圈（在手機的橫截面上，比機身大一點）
        if k == 0:
            yb = RIB_Y
            loop = [(-0.035, yb, 0.0085), (0.035, yb, 0.0085), (0.035, yb, -0.0005), (-0.035, yb, -0.0005), (-0.035, yb, 0.0085)]
        else:
            xb = RIB_X
            loop = [(xb, -0.069, 0.0085), (xb, 0.069, 0.0085), (xb, 0.069, -0.0005), (xb, -0.069, -0.0005), (xb, -0.069, 0.0085)]
        sp.points.add(len(loop) - 1)
        for p_, q in zip(sp.points, loop):
            p_.co = (*q, 1); p_.tilt = math.pi / 2
        cu.bevel_factor_mapping_start = "SPLINE"; cu.bevel_factor_mapping_end = "SPLINE"
        cu.materials.clear(); cu.materials.append(rib)
        if f"D_RibbonBand{k}" in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[f"D_RibbonBand{k}"], do_unlink=True)
        o = bpy.data.objects.new(f"D_RibbonBand{k}", cu); c.objects.link(o); o.parent = ph
        o.rotation_euler = (0, 0, 0) if k == 0 else (0, 0, 0)
    bm = bmesh.new()                                    # 蝴蝶結：兩個環＋兩條尾巴（在緞帶十字交叉點）
    for sx in (-1, 1):
        ball(bm, Vector((sx * 0.013, 0.003, 0.011)), (0.013, 0.008, 0.0035), seg=12)
        p0 = Vector((0, 0, 0.0095)); p1 = Vector((sx * 0.012, -0.03, 0.0088)); v = p1 - p0
        box(bm, (p0 + p1) / 2, (0.008, v.length, 0.0008), rot=Matrix.Rotation(math.atan2(-v.x, v.y), 4, "Z"))
    ball(bm, Vector((0, 0.0, 0.0115)), (0.0055, 0.006, 0.0035), seg=10)
    o = mesh_obj("D_Bow", bm, rib, c, smooth=True, parent=ph); o.location = (RIB_X, RIB_Y, 0)
    DESK["bow_s"] = 0.75
    # 明信片（IG 風卡面＋顯影照片＋郵戳）＋橡皮章
    face = pmat("D_PostcardFace", (1, 1, 1), rough=0.6, spec=0.3, img=os.path.join(TEX, "postcard_face.png"))
    pc = empty("D_Postcard", c)
    bm = bmesh.new(); box(bm, Vector((0, 0, 0.0004)), (0.15, 0.1, 0.0008), mi=1); quad(bm, 0.15, 0.1, (0, 0, 0.00082), mi=0)
    mesh_obj("D_PostcardCard", bm, [face, card], c, parent=pc)
    ph_img = os.path.join(TEX, "postcard_photo.jpg")
    m = develop_mat("D_PostcardPhoto", ph_img if os.path.exists(ph_img) else os.path.join(PHOTO, "polaroid_bride.jpg"))
    bm = bmesh.new(); quad(bm, 0.082, 0.082)
    o = mesh_obj("D_PostcardPhoto", bm, m, c, parent=pc); o.location = (-0.15 / 2 + 0.004 + 0.041, 0.1 / 2 - 0.004 - 0.041, 0.00095)
    pm_ = decal("D_Postmark", os.path.join(TEX, "postmark.png"), 0.07, c, parent=pc)
    pm_.location = (0.036, -0.026, 0.0011); pm_.rotation_euler = (0, 0, math.radians(-12))
    rub = pmat("D_StampWood", srgb("#A9784F"), rough=0.5, noise=0.3); ink = pmat("D_StampInk", srgb("#B05460"), rough=0.6)
    st = empty("D_Stamp", c)
    bm = bmesh.new(); box(bm, Vector((0, 0, 0.012)), (0.034, 0.034, 0.016), mi=0); box(bm, Vector((0, 0, 0.002)), (0.032, 0.032, 0.004), mi=1)
    cyl(bm, Vector((0, 0, 0.032)), 0.006, 0.025, seg=12, mi=0); ball(bm, Vector((0, 0, 0.05)), 0.013, seg=14, mi=0)
    mesh_obj("D_StampMesh", bm, [rub, ink], c, smooth=True, parent=st)
    # 倒數用的押花瓣（⑧）：一堆小花瓣，每格改位置拼成 3、2、1
    pmats = [pmat("D_PetalRose", (1, 1, 1), rough=0.7, img=os.path.join(TEX, "petal_rose.png"), img_alpha=True),
             pmat("D_PetalLav", (1, 1, 1), rough=0.7, img=os.path.join(TEX, "petal_lav.png"), img_alpha=True),
             pmat("D_PetalBlush", (1, 1, 1), rough=0.7, img=os.path.join(TEX, "petal_blush.png"), img_alpha=True)]
    bm = bmesh.new()
    for i in range(N_CD):
        quad(bm, 0.016, 0.011, (0, 0, -1 - i * 0.001), mi=i % 3)
    mesh_obj("D_CountPetals", bm, pmats, c)
    # 燈：左上方的大面積柔光（窗光）＋暖色天光
    lt = bpy.data.objects.get("D_Window")
    if lt is None:
        lt = bpy.data.objects.new("D_Window", bpy.data.lights.new("D_Window", "AREA"))
    if lt.name not in c.objects:
        c.objects.link(lt)
    lt.data.shape = "RECTANGLE"; lt.data.size = 0.9; lt.data.size_y = 0.6; lt.data.energy = 11.5; lt.data.color = (1.0, 0.95, 0.88)
    try:
        lt.data.use_shadow_jitter = True
    except Exception:
        pass
    lt.location = (-0.55, 0.5, 0.75)
    lt.rotation_euler = (Vector((0.05, -0.02, 0)) - lt.location).to_track_quat("-Z", "Y").to_euler()
    DESK["built"] = True
    digit_targets()


def seal_build(c, wax, flap_h, env):
    """蠟封：不規則圓餅＋R&A 浮雕；沿一條鋸齒線切成兩半（上半黏在封口蓋、下半留在信封上）"""
    bm = bmesh.new()
    rnd = random.Random(8)
    n = 28
    top = [bm.verts.new(((0.019 + rnd.uniform(-0.0012, 0.0012)) * math.cos(2 * math.pi * k / n),
                         (0.019 + rnd.uniform(-0.0012, 0.0012)) * math.sin(2 * math.pi * k / n), 0.0035)) for k in range(n)]
    f = bm.faces.new(top)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]:
        v.co.z = 0.0
    # 浮雕字
    cu = bpy.data.curves.new("D_SealTxt", "FONT"); cu.body = "R&A"; cu.size = 0.017; cu.align_x = "CENTER"; cu.align_y = "CENTER"
    cu.extrude = 0.0006
    try:
        cu.font = bpy.data.fonts.load(font_path("FRSCRIPT.TTF"), check_existing=True)
    except Exception:
        pass
    tmp = bpy.data.objects.new("D_SealTxtTmp", cu); bpy.context.scene.collection.objects.link(tmp)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); me = tmp.evaluated_get(dg).to_mesh()
    tb = bmesh.new(); tb.from_mesh(me)
    bmesh.ops.translate(tb, vec=Vector((0, 0, 0.0039)), verts=tb.verts[:])
    tme = bpy.data.meshes.new("D_SealTxtMesh"); tb.to_mesh(tme); tb.free()
    tmp.evaluated_get(dg).to_mesh_clear(); bpy.data.objects.remove(tmp, do_unlink=True)
    bm.from_mesh(tme); bpy.data.meshes.remove(tme)
    whole = bpy.data.meshes.new("D_SealWholeMesh"); bm.to_mesh(whole)
    for half, sgn, parent in (("Top", 1, flap_h), ("Bot", -1, env)):
        hb = bmesh.new(); hb.from_mesh(whole)
        # 裂線：沿 y≈0 的鋸齒
        for k in range(6):
            x0 = -0.024 + k * 0.008
            ycut = 0.0015 * (1 if k % 2 else -1)
            bmesh.ops.bisect_plane(hb, geom=hb.verts[:] + hb.edges[:] + hb.faces[:], plane_co=Vector((x0, ycut, 0)), plane_no=Vector((0, 1, 0)))
        bmesh.ops.delete(hb, geom=[f_ for f_ in hb.faces if f_.calc_center_median().y * sgn < 0], context="FACES")
        o = mesh_obj(f"D_Seal{half}", hb, wax, c, smooth=False)
        o.parent = parent
        if half == "Top":                      # 封口蓋的鉸鏈在信封上緣；蠟封在蓋子尖端（信封中央）
            o.location = (0, -ENV_H / 2, 0.0)
        else:
            o.location = (0, 0, 0.0034)
    bm.free()
    o = bpy.data.objects.new("D_SealWhole", whole); c.objects.link(o); o.data.materials.append(wax); o.parent = env
    o.location = (0, 0, 0.0034)


# ── ⑧ 倒數：押花瓣拼成 3、2、1 ──
N_CD = 96
CD = {}


def digit_targets():
    """用字型的字形取樣：每個數字取 N_CD 個點（最遠點取樣，分佈均勻）"""
    for d in "321":
        cu = bpy.data.curves.new("D_Dig" + d, "FONT"); cu.body = d; cu.size = 0.17; cu.align_x = "CENTER"; cu.align_y = "CENTER"
        try:
            cu.font = bpy.data.fonts.load(font_path("georgiab.ttf"), check_existing=True)
        except Exception:
            pass
        ob = bpy.data.objects.new("D_DigTmp", cu); bpy.context.scene.collection.objects.link(ob)
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get(); me = ob.evaluated_get(dg).to_mesh()
        tris = []
        me.calc_loop_triangles()
        for tri in me.loop_triangles:
            a, b, c_ = (me.vertices[i].co.copy() for i in tri.vertices)
            tris.append((a, b, c_, ((b - a).cross(c_ - a)).length / 2))
        tot = sum(t[3] for t in tris)
        rnd = random.Random(ord(d))
        cand = []
        for _ in range(1500):
            r_ = rnd.uniform(0, tot)
            for a, b, c_, ar in tris:
                r_ -= ar
                if r_ <= 0:
                    u, v = rnd.random(), rnd.random()
                    if u + v > 1:
                        u, v = 1 - u, 1 - v
                    cand.append(a + (b - a) * u + (c_ - a) * v)
                    break
        pts = [cand[0]]
        dist = [(p - pts[0]).length for p in cand]
        while len(pts) < N_CD:
            i = max(range(len(cand)), key=lambda k: dist[k])
            pts.append(cand[i])
            dist = [min(dd, (p - cand[i]).length) for dd, p in zip(dist, cand)]
        ob.evaluated_get(dg).to_mesh_clear(); bpy.data.objects.remove(ob, do_unlink=True)
        CD[d] = pts


def countdown_update(t, center, t_start=3.2):
    """3.2 秒起每秒一個數字：0.25 秒聚成數字、停 0.55 秒、0.2 秒散開，下一秒換下一個；之前與之後花瓣散在信紙四周"""
    o = bpy.data.objects["D_CountPetals"]; me = o.data
    rnd = random.Random(5)
    co = []
    for i in range(N_CD):
        home = Vector((rnd.uniform(-0.15, 0.15), rnd.uniform(-0.09, 0.09), 0))
        if home.length < 0.06:
            home *= 0.06 / max(home.length, 1e-4) * 1.6
        spin = rnd.uniform(0, 6.28)
        k = int((t - t_start) // 1.0)
        ph = (t - t_start) - k
        if 0 <= k < 3:
            tgt = CD["321"[k]][i]
            if ph < 0.25:
                prev = home if k == 0 else home * 0.6
                w = ease(ph / 0.25)
            elif ph < 0.8:
                w = 1.0
            else:
                w = 1 - ease((ph - 0.8) / 0.2)
            p = home.lerp(tgt, w)
            lift = 0.012 * math.sin(math.pi * min(1, ph / 0.25)) if ph < 0.25 else 0.0
        else:
            p = home; lift = 0.0; w = 0
        p = Vector(center) + p + Vector((0, 0, 0.0007 + 0.00002 * i + lift))
        R = Matrix.Rotation(spin + 2.0 * w, 3, "Z")
        for cx_, cy_ in ((-0.008, -0.0055), (0.008, -0.0055), (0.008, 0.0055), (-0.008, 0.0055)):
            co.append(tuple(p + R @ Vector((cx_, cy_, 0))))
    me.vertices.foreach_set("co", [x for v in co for x in v]); me.update()


# ── 共用：擺位置與開關 ──
DESK_OBJS = ("D_Letter", "D_Env", "D_LavenderSprig", "D_Pen", "D_Pola_groom", "D_Pola_bride", "D_Phone", "D_Postcard", "D_Stamp")


def desk_hide_all():
    for o in bpy.data.collections["Set_Desk"].all_objects:
        if o.name not in ("D_Desk", "D_Window"):
            o.hide_render = True


def show_tree(name, on=True):
    o = bpy.data.objects.get(name)
    if not o:
        return
    o.hide_render = not on
    for ch in o.children_recursive:
        ch.hide_render = not on


def place(name, x, y, rz=0.0, z=0.0):
    o = bpy.data.objects[name]
    o.location = (x, y, z); o.rotation_euler = (0, 0, math.radians(rz))


def desk_world():
    world_env(srgb("#F3E9DD"), 0.36)


def desk_cam(width, center=(0.0, 0.0), roll=0.0, lens=50):
    """正上方往下拍：畫面寬 width 公尺、中心 center；畫面上方＝+Y"""
    h = width * lens / 36.0
    c = cam_obj()
    c.location = (center[0], center[1], h); c.rotation_euler = (0, 0, math.radians(roll))
    c.data.lens = lens; c.data.sensor_width = 36; c.data.clip_start = 0.005; c.data.clip_end = 20; c.data.dof.use_dof = False
    return c


def letter_set(fold, x=0.0, y=0.0, rz=0.0, z=0.0):
    """fold：0＝攤平、1＝左半蓋在右半上（對摺）。(x, y) 一律是「看得到的那張紙」的中心：對摺時往右半張的中心補位移"""
    off = Matrix.Rotation(math.radians(rz), 3, "Z") @ Vector((-LET_W / 4 * fold, 0, 0))
    place("D_Letter", x + off.x, y + off.y, rz, z)
    h = bpy.data.objects["D_LetterHinge"]
    h.rotation_euler = (0, -math.radians(180 * fold * 0.995), 0)
    h.location = (0, 0, 0.0004 + 0.0006 * math.sin(math.pi * fold))


def pf_set(k, x, y, rz=0.0, z=0.0006, s=1.0, on=True):
    o = bpy.data.objects[f"D_PF{k}"]
    o.location = (x, y, z); o.rotation_euler = (0, 0, math.radians(rz)); o.scale = (s, s, s); o.hide_render = not on
