# 情境 s1（新郎）：坐在木椅上讀《婚禮日報》，右手抓住頁角把報紙翻過去，最後把報紙放低、轉頭對鏡頭笑。便服。
# 以 blender-scenario 範例 scene_s1.py（新娘）為底：所有世界座標乘上 K（體型比例 BODY_S，新郎約 1.09），
# 椅子、報紙、抓點、手肘方向、鏡頭跟著角色等比例放大，手才構得到報紙兩側。
# exec 在 scene_lib.py 之後。對外：S1_N（格數）、s1_build()、s1_frame(f)、s1_props(f)、s1_cam(i)
import bpy, bmesh, math, os
from mathutils import Vector, Matrix

K = BODY_S                          # 新郎 / 新娘 的體型比例
S1_N = 144                          # 6 秒
PW, PH = 0.28 * K, 0.38 * K         # 單頁寬、高
FOLD = 0.18                         # 跨頁 V 字開口（頁緣往他那邊翹，比例值不用乘 K）
TILT = math.radians(32)             # 報紙上緣往外傾
HIP_Z = 0.53 * K                    # 坐下時髖關節高度（椅面高約 0.50）
CURL = 0.2                          # 翻頁中段往他那邊壓扁的比例（紙面拱起）
Y_LIM = -0.175                      # 翻動頁不能比這更靠近他（世界 y）：量過 T 恤正面在 y≈−0.14（肚子到胸口），留 3.5 公分
REL = 77                            # 右手在這格放開頁角（紙自己翻完），手回到右頁外緣
TOWARD = Vector((0, math.cos(TILT), math.sin(TILT)))     # 報紙局部「往他那邊」的世界方向
TURN_POLE = (-0.4, -0.2, 0.75)      # 翻頁時右手肘朝向（新娘尺寸座標）：往外、往前、偏低；太往內會讓前臂戳進肚子
GRAB_Z = -0.03 * K                  # 右手抓翻動頁自由端的高度（沿紙面，0＝頁面中線；偏下，翻到一半時手才不會擋到下巴）


def kv(x, y, z):
    return Vector((x * K, y * K, z * K))


def paper_center(f):
    low = seg(f, 118, 132)
    return kv(0.0, -0.33 + 0.02 * low, 0.80 - 0.08 * low)      # 胸前偏下；最後放低


def pw(f, x, y_local, zp):
    """報紙局部座標 → 世界：x 橫向（+X＝他的左手邊）、y_local 往他那邊、zp 沿紙面往上"""
    C = paper_center(f)
    y, z = y_local, zp
    return C + Vector((x, y * math.cos(TILT) - z * math.sin(TILT), y * math.sin(TILT) + z * math.cos(TILT)))


def page_xy(side, u):
    """靜止的左右頁：u＝離中縫的距離"""
    sx = 1 if side == "L" else -1
    return sx * u, u * FOLD


TH_R = math.atan2(FOLD, -1.0); TH_L = math.atan2(FOLD, 1.0)


def turn_phase(f):
    return seg(f, 46, 88)


def sheet_xy(f, u, off=0.0):
    """翻動那一張：從右頁（他的右手邊）翻到左頁，自由端慢半拍、紙面捲起"""
    ph = turn_phase(f)
    lag = 0.55 * (u / PW) ** 1.6 * math.sin(math.pi * ph)
    pn = max(0.0, min(1.0, ph - lag * 0.35))
    th = TH_R + (TH_L - TH_R) * pn
    r = u * (1 - 0.06 * math.sin(math.pi * ph))          # 捲起時投影變短一點
    # 翻到一半時紙面拱起：往他那邊的分量壓扁，自由端（和抓著它的右手）不會一路翹到他下巴前面
    cy = 1 - CURL * math.sin(math.pi * ph)
    # off：沿紙面法線偏移（正面、背面兩層各放一邊）；整張再往他那邊浮 3mm 免得和下面那頁打架
    return r * math.cos(th) - math.sin(th) * off * cy, (r * math.sin(th) + math.cos(th) * off) * cy + 0.003


def soft_back(p, k=0.035):
    """紙面點太靠近身體（世界 y 超過 Y_LIM−k）就沿紙面往外推，平滑逼近 Y_LIM：翻到一半時頁面下角不會戳進肚子"""
    t = Y_LIM - k
    if p.y <= t:
        return p
    y2 = Y_LIM - k * math.exp(-(p.y - t) / k)
    return p - TOWARD * ((p.y - y2) / math.cos(TILT))


def sheet_world(f, u, zp, off=0.0):
    x, y = sheet_xy(f, u, off)
    return soft_back(pw(f, x, y, zp))


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
    clear_props(); set_world((0.93, 0.91, 0.87), (0.62, 0.58, 0.52))      # 暖米色牆、灰褐地板（新郎版偏中性）
    wood = mat("S1_Wood", (0.50, 0.31, 0.17), (0.32, 0.18, 0.10))
    bm = bmesh.new()
    box(bm, kv(0, 0.07, 0.4425), (0.46 * K, 0.42 * K, 0.035 * K))
    for x in (-0.2, 0.2):
        for y in (-0.12, 0.26):
            box(bm, kv(x, y, 0.2125), (0.035 * K, 0.035 * K, 0.425 * K))
        box(bm, kv(x, 0.265, 0.70), (0.035 * K, 0.03 * K, 0.52 * K))
    for z in (0.66, 0.78, 0.90):
        box(bm, kv(0, 0.265, z), (0.40 * K, 0.02 * K, 0.06 * K))
    for y in (-0.12, 0.26):
        box(bm, kv(0, y, 0.12), (0.38 * K, 0.02 * K, 0.025 * K))
    solid("S1_Chair", bm, wood)
    rug = mat("S1_Rug", (0.70, 0.66, 0.60), (0.55, 0.50, 0.46))
    bm = bmesh.new(); cyl(bm, kv(0, 0.0, 0.004), 1.15 * K, 0.008, seg=64); solid("S1_Rug", bm, rug)
    # 小邊桌＋咖啡杯（他的左手邊）
    bm = bmesh.new(); cyl(bm, kv(0.62, 0.15, 0.27), 0.025 * K, 0.54 * K); cyl(bm, kv(0.62, 0.15, 0.55), 0.22 * K, 0.03 * K, seg=40)
    cyl(bm, kv(0.62, 0.15, 0.01), 0.16 * K, 0.02 * K, seg=32); solid("S1_Table", bm, wood)
    cup = mat("S1_Cup", (0.96, 0.95, 0.93), (0.78, 0.76, 0.78))
    bm = bmesh.new(); cyl(bm, kv(0.58, 0.10, 0.61), 0.035 * K, 0.09 * K, seg=24, r2=0.04 * K); solid("S1_Cup", bm, cup)
    # 報紙：外面（鏡頭看到的封面）、裡面（他讀的跨頁）、翻動頁正反面（貼圖用預設庫的《婚禮日報》）
    outer = image_mat("S1_PaperOuter", os.path.join(LIB, "textures", "paper_outer.png"))
    inner = image_mat("S1_PaperInner", os.path.join(LIB, "textures", "paper_inner.png"))
    ta = image_mat("S1_TurnA", os.path.join(LIB, "textures", "paper_turn_a.png"))
    tb = image_mat("S1_TurnB", os.path.join(LIB, "textures", "paper_turn_b.png"))
    _grid("S1_PaperOut", 24, 10, lambda u, v: (u, v), outer)
    _grid("S1_PaperIn", 24, 10, lambda u, v: (1 - u, v), inner)
    _grid("S1_TurnA", 12, 10, lambda u, v: (1 - u, v), ta)
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
            return sheet_world(f, PW * u, -PH / 2 + PH * v, off)
        return fn
    _set(O_["S1_TurnA"], 12, 10, sheet(-0.0008))     # 一開始朝向他的那面
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
    lw = pw(f, PW + 0.012 * K, PW * FOLD + 0.035 * K, -0.03 * K); ltip = pw(f, PW - 0.04 * K, PW * FOLD + 0.02 * K, -0.01 * K)
    # 右手：平常抓右頁外緣；翻頁時抓翻動頁的自由端上角
    rest = pw(f, -PW - 0.012 * K, PW * FOLD + 0.035 * K, -0.03 * K); rest_tip = pw(f, -PW + 0.04 * K, PW * FOLD + 0.02 * K, -0.01 * K)
    # 抓點跟著翻動頁的自由端（u＝0.96）走；REL 那格放手，紙自己翻完，手從放手處回到右頁外緣
    fg = min(f, REL)
    grab = sheet_world(fg, PW * 0.96, GRAB_Z) + TOWARD * 0.035 * K
    # 手掌朝向＝自由端指向中縫的方向，前後 8 格取平均：翻到中段紙面轉得快，手腕才不會一格甩 19 度
    tdir = Vector((0, 0, 0))
    for t in range(-8, 9, 2):
        tt = max(0.0, min(float(REL), fg + t))
        tdir += sheet_world(tt, PW * 0.75, GRAB_Z) - sheet_world(tt, PW * 0.96, GRAB_Z)
    grab_tip = grab + tdir.normalized() * 0.06 * K - TOWARD * 0.015 * K
    g_in = seg(f, 36, 48); g_out = seg(f, REL, REL + 26)
    lift = math.sin(math.pi * g_out) * 0.05 * K
    if f < REL:
        rw = rest.lerp(grab, g_in); rtip = rest_tip.lerp(grab_tip, g_in)
    else:
        rw = grab.lerp(rest, g_out) + Vector((0, 0.0, lift)); rtip = grab_tip.lerp(rest_tip, g_out) + Vector((0, 0.0, lift))
    rpole = kv(-0.4, -0.05, 0.75).lerp(kv(*TURN_POLE), math.sin(math.pi * turn_phase(fg)) * (1 - g_out))
    blink = any(abs(f - b) < 2 for b in (20, 70, 110, 138))
    face = {"Fcl_MTH_Small": 0.25 * (1 - look_cam), "Fcl_ALL_Joy": 0.8 * look_cam, "Fcl_EYE_Close": 1.0 if blink else 0.0}
    return dict(P, root=(0, 0, rz), ground=False, hands=("grip", ("grip", "pinch", g_in * (1 - g_out))),
                ik=[("L", lw, kv(0.42, -0.05, 0.75), ltip), ("R", rw, rpole, rtip)], face=face)


def s1_cam(i):
    u = ease(i / S1_N)
    # 從他右前方偏高往下拍，才看得到跨頁裡面和翻起來的那張紙；退遠一點讓頭頂到腳都在畫面裡
    if globals().get("CAMDBG"):                           # 除錯用近照：CAMDBG=1 右前方、2 正前方、3 右側，胸口高度拍上半身
        c = int(globals()["CAMDBG"])
        loc = {1: (-1.1, -1.0, 1.1), 2: (0.0, -1.5, 1.05), 3: (-1.5, -0.1, 1.05)}[c]
        aim(bpy.data.objects["Camera"], kv(*loc), kv(-0.05, -0.1, 0.95), 50); return
    loc = kv(-2.15, -1.95, 1.55).lerp(kv(-1.95, -1.72, 1.45), u)
    aim(bpy.data.objects["Camera"], loc, kv(0.05, -0.14, 0.60), 34)


# 給 run_scene.py 用的描述（每個情境模組都要有）
SCENE = dict(id="s1", title="木椅上看報紙", N=S1_N, build=s1_build, frame=s1_frame, props=s1_props, cam=s1_cam,
             desc="坐在木椅上讀《婚禮日報》，右手抓住頁角把報紙翻過去，最後把報紙放低、轉頭對鏡頭笑。翻頁的那張紙會捲起、自由端慢半拍。",
             outfit="base", res=(960, 540), stills=())
