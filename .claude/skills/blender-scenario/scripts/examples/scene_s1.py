# 情境 1：坐在木椅上看報紙，右手翻頁，最後把報紙放低、看鏡頭笑。便服。
# exec 在 scene_lib.py 之後。對外：S1_N（格數）、s1_build()、s1_frame(f)、s1_props(f)、s1_cam(i)
import bpy, bmesh, math
from mathutils import Vector, Matrix

S1_N = 144
PW, PH = 0.28, 0.38                 # 單頁寬、高
FOLD = 0.18                         # 跨頁 V 字開口（頁緣往她那邊翹）
TILT = math.radians(32)             # 報紙上緣往外傾
HIP_Z = 0.53


def _tl(f):
    return f / S1_N


def paper_center(f):
    low = seg(f, 118, 132)
    return Vector((0.0, -0.33 + 0.02 * low, 0.80 - 0.08 * low))      # 坐著時眼睛約在 1.1 公尺，報紙在胸前偏下


def pw(f, x, y_local, zp):
    """報紙局部座標 → 世界：x 橫向（+X＝她的左手邊）、y_local 往她那邊、zp 沿紙面往上"""
    C = paper_center(f)
    y, z = y_local, zp
    return C + Vector((x, y * math.cos(TILT) - z * math.sin(TILT), y * math.sin(TILT) + z * math.cos(TILT)))


def page_xy(side, u):
    """靜止的左右頁：u＝離中縫的距離"""
    sx = 1 if side == "L" else -1
    return sx * u, u * FOLD


TH_R = math.atan2(FOLD, -1.0); TH_L = math.atan2(FOLD, 1.0)


def turn_phase(f):
    return seg(f, 48, 84)


def sheet_xy(f, u, off=0.0):
    """翻動那一張：從右頁（她的右手邊）翻到左頁，自由端慢半拍、紙面捲起"""
    ph = turn_phase(f)
    lag = 0.55 * (u / PW) ** 1.6 * math.sin(math.pi * ph)
    pn = max(0.0, min(1.0, ph - lag * 0.35))
    th = TH_R + (TH_L - TH_R) * pn
    r = u * (1 - 0.06 * math.sin(math.pi * ph))          # 捲起時投影變短一點
    # off：沿紙面法線偏移（正面、背面兩層各放一邊）；整張再往她那邊浮 3mm 免得和下面那頁打架
    return r * math.cos(th) - math.sin(th) * off, r * math.sin(th) + math.cos(th) * off + 0.003


def _grid(name, nx, nz, xfn, m):
    bm = bmesh.new(); uv = bm.loops.layers.uv.new("UVMap"); V = []
    for j in range(nz + 1):
        for i in range(nx + 1):
            V.append(bm.verts.new((0, 0, 0)))
    bm.verts.ensure_lookup_table()
    for j in range(nz):
        for i in range(nx):
            a = j * (nx + 1) + i
            f = bm.faces.new((V[a], V[a + 1], V[a + nx + 2], V[a + nx + 1]))
            for l, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                l[uv].uv = xfn(ii / nx, jj / nz)
    return solid(name, bm, m)


def s1_build():
    clear_props(); set_world((0.95, 0.90, 0.86), (0.66, 0.58, 0.52))
    wood = mat("S1_Wood", (0.56, 0.34, 0.19), (0.36, 0.2, 0.11))
    bm = bmesh.new()
    box(bm, Vector((0, 0.07, 0.4425)), (0.46, 0.42, 0.035))
    for x in (-0.2, 0.2):
        for y in (-0.12, 0.26):
            box(bm, Vector((x, y, 0.2125)), (0.035, 0.035, 0.425))
        box(bm, Vector((x, 0.265, 0.70)), (0.035, 0.03, 0.52))
    for z in (0.66, 0.78, 0.90):
        box(bm, Vector((0, 0.265, z)), (0.40, 0.02, 0.06))
    for y in (-0.12, 0.26):
        box(bm, Vector((0, y, 0.12)), (0.38, 0.02, 0.025))
    solid("S1_Chair", bm, wood)
    rug = mat("S1_Rug", (0.80, 0.66, 0.60), (0.66, 0.5, 0.48))
    bm = bmesh.new(); cyl(bm, Vector((0, 0.0, 0.004)), 1.1, 0.008, seg=64); solid("S1_Rug", bm, rug)
    # 小邊桌＋杯子
    bm = bmesh.new(); cyl(bm, Vector((0.62, 0.15, 0.27)), 0.025, 0.54); cyl(bm, Vector((0.62, 0.15, 0.55)), 0.22, 0.03, seg=40)
    cyl(bm, Vector((0.62, 0.15, 0.01)), 0.16, 0.02, seg=32); solid("S1_Table", bm, wood)
    cup = mat("S1_Cup", (0.96, 0.95, 0.93), (0.78, 0.76, 0.78))
    bm = bmesh.new(); cyl(bm, Vector((0.58, 0.10, 0.61)), 0.035, 0.09, seg=24, r2=0.04); solid("S1_Cup", bm, cup)
    # 報紙：外面（鏡頭看到的封面）、裡面（她讀的跨頁）、翻動頁正反面
    outer = image_mat("S1_PaperOuter", os.path.join(LIB, "textures", "paper_outer.png"))
    inner = image_mat("S1_PaperInner", os.path.join(LIB, "textures", "paper_inner.png"))
    ta = image_mat("S1_TurnA", os.path.join(LIB, "textures", "paper_turn_a.png"))
    tb = image_mat("S1_TurnB", os.path.join(LIB, "textures", "paper_turn_b.png"))
    _grid("S1_PaperOut", 24, 10, lambda u, v: (u, v), outer)
    _grid("S1_PaperIn", 24, 10, lambda u, v: (1 - u, v), inner)
    _grid("S1_TurnA", 12, 10, lambda u, v: (1 - u * 0.5 - 0.5 if False else 1 - u, v), ta)
    _grid("S1_TurnB", 12, 10, lambda u, v: (u, v), tb)
    s1_props(0)


def _set(ob, nx, nz, fn):
    me = ob.data
    for j in range(nz + 1):
        for i in range(nx + 1):
            me.vertices[j * (nx + 1) + i].co = fn(i / nx, j / nz)
    me.update()


def s1_props(f):
    O_ = bpy.data.objects
    def spread(off):
        def fn(u, v):
            x = -PW + 2 * PW * u
            xx, yy = page_xy("L" if x >= 0 else "R", abs(x))
            return pw(f, xx, yy + off, -PH / 2 + PH * v)
        return fn
    _set(O_["S1_PaperOut"], 24, 10, spread(-0.0015))
    _set(O_["S1_PaperIn"], 24, 10, spread(0.0))
    def sheet(off):
        def fn(u, v):
            x, y = sheet_xy(f, PW * u, off)
            return pw(f, x, y, -PH / 2 + PH * v)
        return fn
    _set(O_["S1_TurnA"], 12, 10, sheet(-0.0008))     # 一開始朝向她的那面
    _set(O_["S1_TurnB"], 12, 10, sheet(0.0008))


def s1_frame(f):
    P = {}
    rz = seat_legs(P, HIP_Z)
    look_cam = seg(f, 120, 134)
    turn = turn_phase(f)
    P["Spine"] = [("X", -3 + 2 * look_cam)]
    P["Head"] = [("X", 14 * (1 - look_cam) + 1.5 * s(f / 48)), ("Z", -6 + 12 * turn - 26 * look_cam), ("Y", 4 * look_cam)]
    arms_down(P)
    # 左手：抓左頁外緣
    lw = pw(f, PW + 0.012, PW * FOLD + 0.035, -0.03); ltip = pw(f, PW - 0.04, PW * FOLD + 0.02, -0.01)
    # 右手：平常抓右頁外緣；翻頁時抓翻動頁的自由端上角
    rest = pw(f, -PW - 0.012, PW * FOLD + 0.035, -0.03); rest_tip = pw(f, -PW + 0.04, PW * FOLD + 0.02, -0.01)
    sx, sy = sheet_xy(f, PW * 0.96); grab = pw(f, sx, sy + 0.035, 0.07); gx2, gy2 = sheet_xy(f, PW * 0.75); grab_tip = pw(f, gx2, gy2 + 0.02, 0.07)
    g_in = seg(f, 36, 48); g_out = seg(f, 86, 104)
    lift = math.sin(math.pi * g_out) * 0.06
    if f < 86:
        rw = rest.lerp(grab, g_in); rtip = rest_tip.lerp(grab_tip, g_in)
    else:
        rw = grab.lerp(rest, g_out) + Vector((0, 0.02, lift)); rtip = grab_tip.lerp(rest_tip, g_out) + Vector((0, 0.02, lift))
    rpole = Vector((-0.4, -0.05, 0.75)).lerp(Vector((-0.15, -0.35, 0.7)), math.sin(math.pi * turn))
    blink = any(abs(f - b) < 2 for b in (20, 70, 110, 138))
    face = {"Fcl_MTH_Small": 0.25 * (1 - look_cam), "Fcl_ALL_Joy": 0.8 * look_cam, "Fcl_EYE_Close": 1.0 if blink else 0.0}
    return dict(P, root=(0, 0, rz), ground=False, hands=("grip", ("grip", "pinch", g_in * (1 - g_out))),
                ik=[("L", lw, (0.42, -0.05, 0.75), ltip), ("R", rw, rpole, rtip)], face=face)


def s1_cam(i):
    u = ease(i / S1_N)
    # 從她右前方偏高往下拍，才看得到跨頁裡面和翻起來的那張紙
    loc = Vector((-1.75, -1.55, 1.55)).lerp(Vector((-1.5, -1.3, 1.45)), u)
    aim(bpy.data.objects["Camera"], loc, (0.05, -0.18, 0.74), 40)


# 給 run_scene.py 用的描述（每個情境模組都要有）
SCENE = dict(id="s1", title="木椅上看報紙", N=S1_N, build=s1_build, frame=s1_frame, props=s1_props, cam=s1_cam,
             desc="坐在木椅上讀《婚禮日報》，右手抓住頁角把報紙翻過去，最後把報紙放低、轉頭對鏡頭笑。翻頁的那張紙會捲起、自由端慢半拍。",
             outfit="base", res=(960, 540), stills=())
