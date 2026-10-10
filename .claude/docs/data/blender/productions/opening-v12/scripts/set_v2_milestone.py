# 情境版 ③ v2_03 的道具（2026-10-09）：「愛情里程碑」進度條（第二版取代第一版的押花進度條 G_Bar）。
# 放在 Set_Garden／Set_V2 底下自己的子集合 V2_Milestone，由 shots_v2_s0308.py 開關；既有的 G_Bar、V2_* 不動。
# 造型（規劃表 plan-2 V12-03）：兩根細白立柱撐起棉紙米白細軌道；填色由薰衣草紫漸層到乾燥玫瑰；軌道上 4 個圓形節點
#   「相遇、交往、求婚、婚禮」（0／33／66／100%），「婚禮」最大；最前端是白色小圓把手、乾燥玫瑰粗外框。
#   節點名稱、日期、百分比是 2D 後製，這裡不做。
# 座標：軌道沿 +X、在 y＝MS["y"] 的平面上、高 MS["z"]；節點與把手是朝鏡頭（−Y）的圓片。x0、L 由情境依新郎的走路距離決定（ms_build 的參數）。
import bpy, bmesh, math
from mathutils import Vector, Matrix

MS = dict(y=-0.55, z=0.95, rod=0.011, fill=0.015, node_r=0.046, wed_r=0.078, handle_r=0.040, rim=0.011, post_r=0.016)
MS_OBJ = {}
_RX = Matrix.Rotation(math.radians(90), 4, "X")          # 圓片的軸 +Z → 世界 −Y（朝鏡頭）


def _disc(bm, r, th, mi=0, seg=40, y=0.0):
    cyl(bm, Vector((0.0, y, 0.0)), r, th, axis="Y", seg=seg, mi=mi)


def _grad_mat(name, x0, L):
    """填色：沿世界 x 從薰衣草紫（x0）漸層到乾燥玫瑰（x0＋L）。用世界座標，填色條縮放時漸層不跟著縮"""
    m = pmat(name, PAL["lav"], rough=0.45, spec=0.4, sheen=0.4)
    nt = m.node_tree; bsd = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    geo = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = x0; mr.inputs["From Max"].default_value = x0 + L
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (*PAL["lav"][:3], 1); mix.inputs["B"].default_value = (*PAL["rose"][:3], 1)
    nt.links.new(geo.outputs["Position"], sep.inputs[0]); nt.links.new(sep.outputs["X"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], mix.inputs["Factor"]); nt.links.new(mix.outputs["Result"], bsd.inputs["Base Color"])
    return m


def ms_build(c, x0, L, gap):
    """x0：0% 的位置；L：0→100% 的長度；gap：99% 時把手停在「婚禮」節點前多遠（把手不疊在節點上）"""
    coll_clear(c.name)
    MS_OBJ.clear(); MS_OBJ.update(x0=x0, L=L, gap=gap)
    y, z = MS["y"], MS["z"]
    white = pmat("MS_White", PAL["white"], rough=0.5, spec=0.3)
    paper = pmat("MS_Paper", PAL["paper"], rough=0.8, spec=0.2, noise=0.12)
    node_off = pmat("MS_NodeOff", srgb("#EFE5D8"), rough=0.7, spec=0.25)
    rose = pmat("MS_Rose", PAL["rose"], rough=0.45, spec=0.4, emit=0.15)
    rim_c = pmat("MS_Rim", srgb("#E2D3C2"), rough=0.6, spec=0.25)
    # 軌道（米白細管）＋兩根立柱（白、細）＋柱頂小圓帽
    xa, xb = x0 - 0.10, x0 + L + 0.12
    bm = bmesh.new()
    cyl(bm, Vector(((xa + xb) / 2, y, z)), MS["rod"], xb - xa, axis="X", seg=16, mi=1)
    for x in (xa, xb):
        cyl(bm, Vector((x, y + 0.004, z / 2)), MS["post_r"], z + 0.03, seg=16)
        ball(bm, Vector((x, y + 0.004, z + 0.02)), MS["post_r"] * 1.35, seg=12)
        cyl(bm, Vector((x, y + 0.004, 0.006)), MS["post_r"] * 2.6, 0.012, seg=20)          # 底座小圓盤
    MS_OBJ["track"] = mesh_obj("MS_Track", bm, [white, paper], c, smooth=True)
    # 填色（原點在 0%，scale.x＝填到哪裡）
    bm = bmesh.new(); cyl(bm, Vector((0.5, 0.0, 0.0)), MS["fill"], 1.0, axis="X", seg=16)
    f = mesh_obj("MS_Fill", bm, _grad_mat("MS_Grad", x0, L), c, smooth=True)
    f.location = (x0, y - 0.002, z); MS_OBJ["fill"] = f
    # 4 個節點：米白圓片＋淡外框；亮起＝前面一片乾燥玫瑰圓片從 0 長到滿
    nodes = []
    for i, fr in enumerate((0.0, 1 / 3, 2 / 3, 1.0)):
        r = MS["wed_r"] if i == 3 else MS["node_r"]
        e = empty(f"MS_Node{i}", c, (x0 + L * fr, y - 0.004, z))
        bm = bmesh.new(); _disc(bm, r, 0.014, mi=0); _disc(bm, r + 0.007, 0.010, mi=1, y=0.004)
        mesh_obj(f"MS_Node{i}_Base", bm, [node_off, rim_c], c, smooth=True, parent=e)
        bm = bmesh.new(); _disc(bm, r * 0.86, 0.006, y=-0.011)
        lit = mesh_obj(f"MS_Node{i}_Lit", bm, rose, c, smooth=True, parent=e)
        nodes.append((e, lit, r))
    MS_OBJ["nodes"] = nodes
    # 把手：白色小圓、乾燥玫瑰粗外框（朝鏡頭；在軌道前面一點）
    h = empty("MS_Handle", c, (x0, y - 0.03, z))
    bm = bmesh.new(); _disc(bm, MS["handle_r"], 0.022, mi=0)
    ring(bm, (0, 0, 0), MS["handle_r"], MS["rim"], Mrot=_RX, seg=28, mi=1)
    mesh_obj("MS_Handle_Mesh", bm, [white, pmat("MS_HandleRim", PAL["rose"], rough=0.4, spec=0.45)], c, smooth=True, parent=h)
    MS_OBJ["handle"] = h
    # 「婚禮」亮起時往外擴散的兩圈白色光環（自發光、淡出）
    halos = []
    for k in range(2):
        m = pmat(f"MS_Halo{k}", PAL["white"], rough=0.3, emit=1.6, alpha=1.0)
        bm = bmesh.new(); ring(bm, (0, 0, 0), 1.0, 0.035, Mrot=_RX, seg=40)
        o = mesh_obj(f"MS_Halo{k}", bm, m, c, smooth=True)
        o.location = (x0 + L, y - 0.03, z); o.visible_shadow = False
        halos.append((o, m))
    MS_OBJ["halos"] = halos
    # 拖曳緞帶（把手 → 垂下 → 肩上 → 肩前的拳頭 → 前面的拳頭），和第一版 G_TowRibbon 同做法
    cu = bpy.data.curves.get("MS_Tow") or bpy.data.curves.new("MS_Tow", "CURVE")
    cu.dimensions = "3D"; cu.extrude = 0.018; cu.bevel_depth = 0.0; cu.resolution_u = 10
    cu.splines.clear(); sp = cu.splines.new("BEZIER"); sp.bezier_points.add(4)
    for bp in sp.bezier_points:
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    if "MS_Tow" in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects["MS_Tow"], do_unlink=True)
    tow = bpy.data.objects.new("MS_Tow", cu); c.objects.link(tow)
    cu.materials.clear(); cu.materials.append(pmat("MS_Ribbon", PAL["rose"], rough=0.35, spec=0.6, sheen=0.6))
    MS_OBJ["tow"] = tow
    ms_update(0.0, (0, 0, 0, 0), 0.0, ())


def ms_handle_x(p):
    """進度 p → 把手 x：0～99% 走到「婚禮」前 gap 的地方，99～100% 走完最後的 gap"""
    x0, L, g = MS_OBJ["x0"], MS_OBJ["L"], MS_OBJ["gap"]
    if p <= 0.99:
        return x0 + (L - g) * p / 0.99
    return x0 + (L - g) + g * (p - 0.99) / 0.01


def ms_update(p, lit, shake, halos):
    """p：進度 0～1；lit：4 個節點亮起的程度 0～1；shake：把手顫動（公尺，x 方向）；halos：[(擴散進度 0～1)]×2"""
    hx = ms_handle_x(p) + shake
    MS_OBJ["fill"].scale = (max(0.001, hx - MS_OBJ["x0"]), 1, 1)
    MS_OBJ["handle"].location.x = hx
    for (e, o, r), w in zip(MS_OBJ["nodes"], lit):
        s = max(0.001, w); o.scale = (s, 1, s)
        if w > 0:                                           # 亮起時節點輕輕彈一下（1→1.18→1）
            b = 1.0 + 0.18 * math.sin(math.pi * min(1.0, w))
            e.scale = (b, 1, b)
        else:
            e.scale = (1, 1, 1)
    for k, (o, m) in enumerate(MS_OBJ["halos"]):
        u = halos[k] if k < len(halos) else 0.0
        o.hide_render = not (0.0 < u < 1.0)
        R = MS["wed_r"] * (1.2 + 3.8 * u)
        o.scale = (R, R, R)
        set_alpha(m, (1 - u) ** 1.5)
    return Vector((hx, MS["y"] - 0.05, MS["z"]))


def ms_tow(pts):
    sp = bpy.data.curves["MS_Tow"].splines[0]
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = p
