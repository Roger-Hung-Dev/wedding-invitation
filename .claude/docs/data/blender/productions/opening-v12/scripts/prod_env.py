# 開場影片 V12 的共用環境（use("prod_env") 載入；run_prod.py 會做）。
#   路徑、影格率、配色（sRGB 十六進位 → Blender 線性色）、材質工具、兩個角色（新娘＝主命名空間、新郎＝G）、
#   時間軸（動作段＋換動作淡入淡出）、集合開關（場景／角色）、分層渲染、2D 追蹤點（給合成疊手寫字）。
import bpy, bmesh, math, os, json, random, time
from mathutils import Vector, Matrix, Euler, Quaternion
from bpy_extras.object_utils import world_to_camera_view

use("studio", "pose_lib", "actions", "outfit_lib", "costume", "scene_lib", "skirt_phys")

PROD = os.path.dirname(os.path.dirname(find_script("prod_env")))
ASSET = os.path.join(PROD, "assets"); TEX = os.path.join(ASSET, "tex"); PHOTO = os.path.join(ASSET, "photos")
BLEND_DIR = os.path.join(PROD, "blend"); PREVIEW_DIR = os.path.join(PROD, "pictures", "preview")
PWORK = os.environ.get("OPENING_WORK") or r"D:\render-work\opening-v12"      # 影格與中間檔一律放 D 槽
for _d in (BLEND_DIR, PREVIEW_DIR, PWORK):
    os.makedirs(_d, exist_ok=True)
GROOM_PROJ = os.path.join(os.path.dirname(PROJ), "groom")
FPS = 30
RES_FULL = (1920, 1080)
sc = bpy.context.scene
SHOTS = {}          # 各幕登記在這裡（shots_desk.py、shots_garden.py）：id → dict(set, dur, build, frame, stills, cast, actors, track)


def srgb(h, a=None):
    """'#B8A1C9' → 線性 RGB（Blender 的顏色欄位是線性值）"""
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)
    return c if a is None else (*c, a)


PAL = dict(lav=srgb("#B8A1C9"), rose=srgb("#D9777F"), paper=srgb("#F6EFE6"), sage=srgb("#8FA58A"), ink=srgb("#4A3B35"),
           blush=srgb("#ECB0AC"), cream=srgb("#FBF7F0"), white=srgb("#FFFDF9"), oak=srgb("#B98A5E"), gold=srgb("#C9A45C"),
           leaf=srgb("#7E9A78"), hedge=srgb("#6E8F62"), sky=srgb("#DCE9F2"))


# ── 材質（場景道具用 Principled；角色維持 MToon）──
def pmat(name, color, rough=0.75, spec=0.35, img=None, img_alpha=False, emit=0.0, alpha=None, metal=0.0,
         uv=None, bump=0.0, noise=0.0, sss=0.0, coat=0.0, sheen=0.0):
    """img：貼圖路徑（img_alpha＝用圖的透明度）；noise：紙張纖維般的細微明暗；bump：細微凹凸；uv＝(縮放 x, y)"""
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); bs_ = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bs_.outputs[0], out.inputs["Surface"])
    I = bs_.inputs
    I["Roughness"].default_value = rough
    if "Specular IOR Level" in I: I["Specular IOR Level"].default_value = spec
    I["Metallic"].default_value = metal
    col_sock = I["Base Color"]
    col_sock.default_value = (*color[:3], 1)
    tc = None
    if img or noise or bump:
        tc = nt.nodes.new("ShaderNodeTexCoord")
    if img:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(img, check_existing=True)
        tex.extension = "CLIP" if img_alpha else "REPEAT"
        src = tc.outputs["UV"]
        if uv:
            mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (uv[0], uv[1], 1)
            nt.links.new(src, mp.inputs[0]); src = mp.outputs[0]
        nt.links.new(src, tex.inputs[0])
        nt.links.new(tex.outputs["Color"], col_sock)
        if img_alpha:
            nt.links.new(tex.outputs["Alpha"], I["Alpha"])
        m["tex_node"] = tex.name
    if noise:
        nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 180.0; nz.inputs["Detail"].default_value = 8.0
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = noise
        src_col = col_sock.links[0].from_socket if col_sock.is_linked else None
        if src_col:
            nt.links.new(src_col, mix.inputs["A"])
        else:
            mix.inputs["A"].default_value = (*color[:3], 1)
        rr = nt.nodes.new("ShaderNodeMapRange"); rr.inputs["From Min"].default_value = 0.3; rr.inputs["From Max"].default_value = 0.7
        rr.inputs["To Min"].default_value = 0.88; rr.inputs["To Max"].default_value = 1.0
        nt.links.new(nz.outputs["Fac"], rr.inputs["Value"])
        nt.links.new(rr.outputs["Result"], mix.inputs["B"])
        nt.links.new(mix.outputs["Result"], col_sock)
    if bump:
        nz2 = nt.nodes.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 420.0; nz2.inputs["Detail"].default_value = 6.0
        nt.links.new(tc.outputs["Object"], nz2.inputs["Vector"])
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.0004
        nt.links.new(nz2.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], I["Normal"])
    if emit:
        I["Emission Color"].default_value = (*color[:3], 1)
        if img: nt.links.new(nt.nodes[m["tex_node"]].outputs["Color"], I["Emission Color"])
        I["Emission Strength"].default_value = emit
    if alpha is not None:
        I["Alpha"].default_value = alpha
    if sss and "Subsurface Weight" in I:
        I["Subsurface Weight"].default_value = sss
    if coat and "Coat Weight" in I:
        I["Coat Weight"].default_value = coat
    if sheen and "Sheen Weight" in I:
        I["Sheen Weight"].default_value = sheen
    if img_alpha or alpha is not None:
        try:
            m.surface_render_method = "DITHERED"
        except Exception:
            pass
    try:
        m.use_transparent_shadow = True
    except Exception:
        pass
    return m


def develop_mat(name, photo, white=None):
    """拍立得／明信片照片的「由白顯影」：值節點 develop 0→1（0＝一片白、1＝彩色照片），每格改 m['dev'] 對應的節點"""
    m = pmat(name, (1, 1, 1), rough=0.35, spec=0.5, img=photo)
    nt = m.node_tree
    tex = nt.nodes[m["tex_node"]]; bsd = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    val = nt.nodes.new("ShaderNodeValue"); val.name = "develop"; val.outputs[0].default_value = 1.0
    # 顯影：先出現淡淡的冷色輪廓，再慢慢上色（白 → 淡灰藍 → 彩色）
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (*(white or srgb("#FBFAF6")), 1)
    nt.links.new(tex.outputs["Color"], mix.inputs["B"])
    curve = nt.nodes.new("ShaderNodeMapRange"); curve.interpolation_type = "SMOOTHSTEP"
    nt.links.new(val.outputs[0], curve.inputs["Value"]); nt.links.new(curve.outputs["Result"], mix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], bsd.inputs["Base Color"])
    return m


def set_develop(m, v):
    m.node_tree.nodes["develop"].outputs[0].default_value = max(0.0, min(1.0, v))


def set_alpha(m, a):
    bsd = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    if bsd.inputs["Alpha"].is_linked:
        # 有貼圖透明度時，乘一個係數
        nt = m.node_tree
        mul = nt.nodes.get("alpha_mul")
        if mul is None:
            mul = nt.nodes.new("ShaderNodeMath"); mul.name = "alpha_mul"; mul.operation = "MULTIPLY"
            src = bsd.inputs["Alpha"].links[0].from_socket
            nt.links.new(src, mul.inputs[0]); nt.links.new(mul.outputs[0], bsd.inputs["Alpha"])
        mul.inputs[1].default_value = a
    else:
        bsd.inputs["Alpha"].default_value = a
    try:
        m.surface_render_method = "DITHERED"
    except Exception:
        pass


# ── 大量小零件的網格（玫瑰花瓣、樹籬葉團…）──
# ⚠️ 不要把幾千個 bmesh.ops.create_* 疊進同一個 bmesh：每個運算都會掃整張網格，時間變成平方級（花園景曾因此跑超過 10 分鐘）。
# MB 先把頂點、面放在 Python 清單，最後 from_pydata 一次建好。box/cyl/ball 的呼叫方式和 scene_lib 一樣（第一個參數傳 MB 就走這條）。
class MB:
    def __init__(self):
        self.v, self.f, self.mi = [], [], []

    def _add(self, verts, faces, mi):
        b = len(self.v)
        self.v += [tuple(p) for p in verts]
        for fc in faces:
            self.f.append(tuple(b + i for i in fc)); self.mi.append(mi)

    def ellip(self, M, radii=(1, 1, 1), seg=8, mi=0):
        u = seg; v = max(4, seg * 2 // 3)
        M = M @ Matrix.Diagonal((*radii, 1))
        vs = [M @ Vector((0, 0, -1))]
        for j in range(1, v):
            th = math.pi * j / v - math.pi / 2
            for i in range(u):
                ph = 2 * math.pi * i / u
                vs.append(M @ Vector((math.cos(th) * math.cos(ph), math.cos(th) * math.sin(ph), math.sin(th))))
        vs.append(M @ Vector((0, 0, 1)))
        top = len(vs) - 1
        R = lambda j, i: 1 + (j - 1) * u + (i % u)
        fs = [(0, R(1, i + 1), R(1, i)) for i in range(u)]
        fs += [(R(j, i), R(j, i + 1), R(j + 1, i + 1), R(j + 1, i)) for j in range(1, v - 1) for i in range(u)]
        fs += [(R(v - 1, i), R(v - 1, i + 1), top) for i in range(u)]
        self._add(vs, fs, mi)

    def ball(self, c, r, mi=0, seg=16):
        r = r if isinstance(r, (tuple, list)) else (r, r, r)
        self.ellip(Matrix.Translation(c), r, seg, mi)

    def cyl(self, c, r, h, axis="Z", seg=24, r2=None, mi=0, rot=None):
        r2 = r if r2 is None else r2
        Rax = {"Z": Matrix.Identity(4), "X": Matrix.Rotation(math.pi / 2, 4, "Y"), "Y": Matrix.Rotation(math.pi / 2, 4, "X")}[axis]
        M = Matrix.Translation(c) @ (rot or Matrix.Identity(4)) @ Rax
        vs = [M @ Vector((r * math.cos(2 * math.pi * i / seg), r * math.sin(2 * math.pi * i / seg), -h / 2)) for i in range(seg)]
        vs += [M @ Vector((r2 * math.cos(2 * math.pi * i / seg), r2 * math.sin(2 * math.pi * i / seg), h / 2)) for i in range(seg)]
        fs = [(i, (i + 1) % seg, seg + (i + 1) % seg, seg + i) for i in range(seg)]
        fs += [tuple(range(seg - 1, -1, -1)), tuple(range(seg, 2 * seg))]
        self._add(vs, fs, mi)

    def box(self, c, size, rot=None, mi=0):
        M = Matrix.Translation(c) @ (rot or Matrix.Identity(4)) @ Matrix.Diagonal((*size, 1))
        vs = [M @ Vector((x * 0.5, y * 0.5, z * 0.5)) for z in (-1, 1) for y in (-1, 1) for x in (-1, 1)]
        fs = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
        self._add(vs, fs, mi)

    def to_mesh(self, name):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        me.polygons.foreach_set("material_index", self.mi)
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bm.to_mesh(me); bm.free()
        return me


_bm_box, _bm_cyl, _bm_ball = box, cyl, ball


def box(bm, c, size, rot=None, mi=0):
    return bm.box(c, size, rot, mi) if isinstance(bm, MB) else _bm_box(bm, c, size, rot, mi)


def cyl(bm, c, r, h, axis="Z", seg=24, r2=None, mi=0, rot=None):
    return bm.cyl(c, r, h, axis, seg, r2, mi, rot) if isinstance(bm, MB) else _bm_cyl(bm, c, r, h, axis, seg, r2, mi, rot)


def ball(bm, c, r, mi=0, seg=16):
    return bm.ball(c, r, mi, seg) if isinstance(bm, MB) else _bm_ball(bm, c, r, mi, seg)


# ── 物件工具 ──
def coll_new(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or sc.collection).children.link(c)
    return c


def coll_clear(name):
    c = bpy.data.collections.get(name)
    if c:
        for o in list(c.all_objects):
            bpy.data.objects.remove(o, do_unlink=True)
        for ch in list(c.children):
            bpy.data.collections.remove(ch)


def mesh_obj(name, bm, mats, coll, smooth=False, parent=None):
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
    if isinstance(bm, MB):
        me = bm.to_mesh(name)
    else:
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.polygons.foreach_set("use_smooth", [smooth] * len(me.polygons))
    ob = bpy.data.objects.new(name, me); coll.objects.link(ob)
    for mm in (mats if isinstance(mats, (list, tuple)) else [mats]):
        me.materials.append(mm)
    if parent:
        ob.parent = parent
    return ob


def empty(name, coll, loc=(0, 0, 0), parent=None):
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
    e = bpy.data.objects.new(name, None); coll.objects.link(e); e.location = loc
    e.empty_display_size = 0.05
    if parent:
        e.parent = parent
    return e


def quad(bm, w, h, c=(0, 0, 0), mi=0, uv=True):
    """xy 平面上的矩形（法線 +Z），UV 0~1"""
    x, y, z = c
    vs = [bm.verts.new((x - w / 2, y - h / 2, z)), bm.verts.new((x + w / 2, y - h / 2, z)),
          bm.verts.new((x + w / 2, y + h / 2, z)), bm.verts.new((x - w / 2, y + h / 2, z))]
    f = bm.faces.new(vs); f.material_index = mi
    if uv:
        lay = bm.loops.layers.uv.verify()
        for lp, (u, v) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            lp[lay].uv = (u, v)
    return f


def grid(bm, w, h, nx, ny, c=(0, 0, 0), mi=0):
    """細分的矩形（可變形的紙）：回傳頂點二維陣列 [j][i]"""
    lay = bm.loops.layers.uv.verify()
    V = [[bm.verts.new((c[0] - w / 2 + w * i / nx, c[1] - h / 2 + h * j / ny, c[2])) for i in range(nx + 1)] for j in range(ny + 1)]
    for j in range(ny):
        for i in range(nx):
            f = bm.faces.new((V[j][i], V[j][i + 1], V[j + 1][i + 1], V[j + 1][i])); f.material_index = mi
            for lp, (a, b) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                lp[lay].uv = (a / nx, b / ny)
    return V


def decal(name, img, w, coll, loc=(0, 0, 0), rz=0.0, h=None, parent=None, rough=0.8):
    """透明貼圖片（押花、郵戳、紙膠帶）：寬 w（高依圖片比例），平放"""
    im = bpy.data.images.load(img, check_existing=True)
    h = h or w * im.size[1] / max(1, im.size[0])
    m = pmat("M_" + name, (1, 1, 1), rough=rough, spec=0.2, img=img, img_alpha=True)
    bm = bmesh.new(); quad(bm, w, h)
    ob = mesh_obj(name, bm, m, coll, parent=parent)
    ob.location = loc; ob.rotation_euler = (0, 0, math.radians(rz))
    return ob


def font_path(name):
    return os.path.join("C:/Windows/Fonts", name)


# ── 角色 ──
G = add_character(GROOM_PROJ)                       # 新郎的命名空間；新娘就是主命名空間（ARM、ACT…）
CAST = {"bride": globals(), "groom": G}


def cast_collections():
    """新娘的物件原本在場景根集合：搬進 Cast_bride，和 Cast_groom 一樣可以整組開關"""
    cb = coll_new("Cast_bride")
    for o in list(sc.collection.objects):
        if o.name.startswith("bride_"):
            cb.objects.link(o); sc.collection.objects.unlink(o)
    return cb


def show(coll_name, on=True):
    c = bpy.data.collections.get(coll_name)
    if c:
        c.hide_render = not on; c.hide_viewport = not on


def stage(set_name, cast=True):
    """這一幕要用哪個景：只開那個景的集合；cast＝要不要角色"""
    for n in ("Set_Desk", "Set_Garden"):
        show(n, n == set_name)
    for n in ("Cast_bride", "Cast_groom"):
        show(n, cast)


def act_pose(ns, spec, tl):
    """spec：動作庫代號（循環播放）、(代號, 起始相位)、或函式 fn(tl)→P；tl＝這段開始後的秒數"""
    if callable(spec):
        return spec(tl)
    if isinstance(spec, tuple):
        key, ph = spec
    else:
        key, ph = spec, 0.0
    name, fn, n = ns["ACT"][key]
    return fn(((tl / (n / 24.0)) + ph) % 1.0)


def timeline(ns, segs, t, blend=0.3):
    """segs＝[(起秒, 訖秒, spec), …]（首尾相接）。換段時前一段淡出 blend 秒 → 回傳 (PA, PB, w)"""
    i = 0
    for i, (t0, t1, spec) in enumerate(segs):
        if t < t1:
            break
    t0, t1, spec = segs[i]
    P = act_pose(ns, spec, max(0.0, t - t0))
    if i > 0 and t - t0 < blend:
        p0, p1, pspec = segs[i - 1]
        return act_pose(ns, pspec, t - p0), P, ease((t - t0) / blend)
    return P, None, 1.0


class Actor:
    """一個角色在一幕裡的演出：segs＝動作時間軸、place(t)→(x, y, rz)、mod(t, P)→P（加道具 IK、表情…）"""

    def __init__(self, ns, segs, place, mod=None, blend=0.3):
        self.ns, self.segs, self.place, self.mod, self.blend = ns, segs, place, mod, blend

    def pose(self, t):
        PA, PB, w = timeline(self.ns, self.segs, t, self.blend)
        if self.mod:
            PA = self.mod(t, dict(PA))
            PB = self.mod(t, dict(PB)) if PB is not None else None
        # 自己帶世界站位的動作（walk_fwd／pull_walk：工廠參數 origin、dirx 已給位置朝向）在 dict 裡放 "abs": True，站位用 (0, 0, 0)；
        # 其他動作用 place(t)。換段淡入淡出時兩段各用自己的站位
        pl = tuple(self.place(t))
        pa = (0.0, 0.0, 0.0) if PA.get("abs") else pl
        ns = self.ns
        if PB is None:
            ns["pose_frame_at"](ns["ARM"], PA, *pa)
        else:
            pb = (0.0, 0.0, 0.0) if PB.get("abs") else pl
            ns["pose_blend_at"](ns["ARM"], PA, PB, w, *pa, place_b=pb)


def walk_seg(W):
    """walk_fwd／pull_walk 的工廠函式 → 時間軸用的 spec（tl＝這段開始後的秒數；走完停在最後一格）"""
    return lambda tl: dict(W(min(1.0, max(0.0, tl / W.dur))), abs=True)


class FootQA:
    """每格記錄每個角色兩隻腳的鞋底取樣點（世界座標），算著地腳的滑步：離地 5 mm 內的點、相鄰兩格的水平位移。
    skip＝[(起秒, 訖秒)] 不算（例：原地轉身）"""

    def __init__(self, actors, t0=0.0, skip=()):
        self.actors = actors; self.t0 = t0; self.skip = list(skip); self.prev = {}; self.rows = {}

    def record(self, i):
        t = self.t0 + i / FPS
        bpy.context.view_layer.update()
        for a in self.actors:
            ns = a.ns; A = ns["ARM"]; mw = A.matrix_world; who = ns["WHO"]
            for side in "LR":
                pts = [mw @ A.pose.bones[b].matrix @ co for b, co in ns["sole_points"](A, who) if f"_{side}_" in b]
                key = (who, side); pv = self.prev.get(key)
                row = self.rows.setdefault(key, dict(max_step=0.0, total=0.0, at=None))
                if pv is not None and len(pv) == len(pts) and not any(a_ <= t <= b_ for a_, b_ in self.skip):
                    d = [(Vector((p.x - q.x, p.y - q.y))).length for p, q in zip(pts, pv) if p.z < 0.005 and q.z < 0.005]
                    if d:
                        step = min(d)                    # 著地點（最不動的那個點）的位移＝滑步
                        row["total"] += step
                        if step > row["max_step"]:
                            row["max_step"], row["at"] = step, round(t, 2)
                self.prev[key] = pts

    def summary(self):
        return {f"{w}_{s}": dict(max_step_mm=round(r["max_step"] * 1000, 2), total_mm=round(r["total"] * 1000, 1), at_s=r["at"])
                for (w, s), r in self.rows.items()}


def arms_of(actors):
    return [a.ns["ARM"] for a in actors]


def skirts_of(actors):
    out = []
    for a in actors:
        if "Skirt_Sway" in a.ns["ARM"].data.bones:
            if "skirt" not in a.ns:
                a.ns["use"]("skirt_phys")
            out.append(a.ns["skirt"])
    return out


def hand_frame(ns, side):
    """手的世界座標框架：(手腕, 指尖方向, 掌心法線, 指節橫軸)。拿東西時物體的軸大致沿指節橫軸"""
    A = ns["ARM"]; bpy.context.view_layer.update()
    pb = A.pose.bones[f"J_Bip_{side}_Hand"]
    M = A.matrix_world @ pb.matrix
    n, ax = ns["palm_normal"](A, side)
    R = A.matrix_world.to_3x3()
    fd = (R @ ax).normalized(); pn = (R @ n).normalized()
    return M.translation.copy(), fd, pn, fd.cross(pn).normalized()


def grip_matrix(ns, side, along=0.07, out=0.025, up=(0, 0, 1)):
    """握在手裡的道具矩陣：原點在掌心前方，局部 +Z＝指節橫軸（取朝 up 那一頭），局部 +Y＝掌心朝向"""
    w, fd, pn, kn = hand_frame(ns, side)
    if kn.dot(Vector(up)) < 0:
        kn = -kn
    p = w + fd * along + pn * out
    y = pn - kn * pn.dot(kn); y.normalize(); x = y.cross(kn)
    M = Matrix((x, y, kn)).transposed().to_4x4(); M.translation = p
    return M


def bone_world(ns, bone, off=(0, 0, 0)):
    A = ns["ARM"]; pb = A.pose.bones[bone]
    return A.matrix_world @ pb.matrix @ Vector(off)


# ── 鏡頭、渲染、分層、追蹤點 ──
def cam_obj():
    c = bpy.data.objects.get("Camera")
    if c is None:
        c = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera")); sc.collection.objects.link(c)
    sc.camera = c
    return c


def look(loc, target, lens=35, roll=0.0, dof=None, fstop=2.8):
    c = cam_obj()
    aim(c, loc, target, lens)
    if roll:
        c.rotation_euler = (c.rotation_euler.to_matrix() @ Matrix.Rotation(math.radians(roll), 3, "Z")).to_euler()
    c.data.sensor_width = 36; c.data.clip_start = 0.005; c.data.clip_end = 200
    c.data.dof.use_dof = dof is not None
    if dof is not None:
        c.data.dof.focus_distance = dof; c.data.dof.aperture_fstop = fstop
    return c


def lerpv(a, b, u):
    return Vector(a).lerp(Vector(b), u)


def render_still(path, res=(960, 540), samples=16, fmt="JPEG"):
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = fmt
    if fmt == "JPEG":
        sc.render.image_settings.quality = 90
    sc.eevee.taa_render_samples = samples
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def layer_mode(mode):
    """分層渲染：'beauty'＝整幅；'cast'＝只有角色（場景挖空成透明，遮擋照算）；'set'＝只有場景（角色關掉）"""
    vl = bpy.context.view_layer
    sc.render.film_transparent = mode == "cast"

    def rec(lc, on):                     # holdout 不會自動傳給子集合，要每一層都設
        lc.holdout = on
        for ch in lc.children:
            rec(ch, on)
    for lc in vl.layer_collection.children:
        if lc.name.startswith("Set_"):
            rec(lc, mode == "cast")
        if lc.name.startswith("Cast_"):
            lc.exclude = mode == "set"


def screen_px(p, res=RES_FULL):
    """世界座標 → 成片像素（左上角為原點）；z<0 表示在鏡頭後面"""
    v = world_to_camera_view(sc, sc.camera, Vector(p))
    return [round(v.x * res[0], 1), round((1 - v.y) * res[1], 1), round(v.z, 3)]


def track_dump(path, frames):
    json.dump(frames, open(path, "w", encoding="utf8"), ensure_ascii=False, indent=1)


def seg01(t, a, b):
    return ease((t - a) / (b - a)) if b > a else float(t >= a)


def lin01(t, a, b):
    return max(0.0, min(1.0, (t - a) / (b - a)))


def world_env(color, strength=1.0):
    w = sc.world or bpy.data.worlds.new("World"); sc.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (*color[:3], 1); bg.inputs[1].default_value = strength


def render_setup(samples=16):
    sc.render.engine = "BLENDER_EEVEE"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.render.fps = FPS
    sc.eevee.taa_render_samples = samples
    for nm_ in ("Sun", "Fill", "Rim", "Floor"):             # 攝影棚的燈和地板不用（每個景自己打光）
        o = bpy.data.objects.get(nm_)
        if o:
            o.hide_render = True; o.hide_viewport = True
