# 情境 6：宴會廳轉圈跳舞。左右搖擺舞步 → 雙手高舉轉一圈 → 再快轉一圈（裙擺張開）→ 屈膝禮。花瓣飄落、鏡頭慢慢繞。禮服。
# 新娘專案版（第 3 版禮服）：只改搖擺段手臂的最低角度，其他照 blender-scenario 的範例。
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

S6_N = 192
PETALS = []


def s6_build():
    clear_props(); set_world((0.42, 0.29, 0.32), False)
    floor = mat("S6_Floor", (0.62, 0.46, 0.38), (0.46, 0.32, 0.28))
    bm = bmesh.new(); cyl(bm, Vector((0, 0, 0.004)), 4.0, 0.008, seg=96); solid("S6_Floor", bm, floor)
    inlay = mat("S6_Inlay", (0.86, 0.74, 0.58), (0.7, 0.58, 0.45))
    bm = bmesh.new()
    for r in (1.2, 1.28, 2.2):
        for k in range(96):
            a = 2 * math.pi * k / 96
            box(bm, Vector((math.cos(a) * r, math.sin(a) * r, 0.009)), (0.07, 0.025, 0.002), Matrix.Rotation(a + math.pi / 2, 4, "Z"))
    solid("S6_Inlay", bm, inlay)
    gold = mat("S6_Gold", (0.95, 0.80, 0.50), (0.75, 0.58, 0.34)); glow = mat("S6_Glow", (1.0, 0.95, 0.85), (1, 0.95, 0.85))
    glow.vrm_addon_extension.mtoon1.emissive_factor = (1.0, 0.92, 0.75)
    bm = bmesh.new()
    for c in ((-1.7, 1.6), (1.8, 1.5), (0.0, 2.6)):    # 三盞立燈
        cyl(bm, Vector((c[0], c[1], 0.8)), 0.03, 1.6, mi=0); cyl(bm, Vector((c[0], c[1], 0.02)), 0.18, 0.04, mi=0)
        ball(bm, Vector((c[0], c[1], 1.7)), 0.16, mi=1, seg=16)
    solid("S6_Lamps", bm, [gold, glow], smooth=True)
    pet = mat("S6_Petal", (0.98, 0.72, 0.76), (0.88, 0.56, 0.62))
    random.seed(21); PETALS.clear()
    bm = bmesh.new()
    for k in range(70):
        box(bm, Vector((0, 0, 0)), (0.022, 0.016, 0.002))
        PETALS.append((random.uniform(-1.8, 1.8), random.uniform(-1.6, 1.6), random.uniform(0, 1), random.uniform(0.25, 0.45), random.uniform(0, 6.28)))
    solid("S6_Petals", bm, pet)
    s6_props(0)


def s6_props(f):
    ob = bpy.data.objects["S6_Petals"]; me = ob.data
    base = [Vector(v) for v in ((-0.011, -0.008, -0.001), (-0.011, -0.008, 0.001), (-0.011, 0.008, -0.001), (-0.011, 0.008, 0.001),
                                (0.011, -0.008, -0.001), (0.011, -0.008, 0.001), (0.011, 0.008, -0.001), (0.011, 0.008, 0.001))]
    t = f / 24.0
    for k, (x, y, ph, sp, rot) in enumerate(PETALS):
        z = 2.6 - ((ph * 2.6 + sp * t) % 2.6)
        sx = x + 0.15 * math.sin(t * 1.3 + rot); sy = y + 0.12 * math.cos(t * 1.1 + rot)
        R = Matrix.Rotation(t * 2 + rot, 3, "X") @ Matrix.Rotation(t * 1.4 + rot, 3, "Z")
        for i in range(8):
            me.vertices[k * 8 + i].co = Vector((sx, sy, z)) + R @ base[i]
    me.update()
    sk = globals().get("skirt")
    if sk is not None:
        sk.extra_flare = spin_speed(f) * 0.35


def s6_rz(f):
    return 360 * seg(f, 72, 114) + 360 * seg(f, 120, 148)


def spin_speed(f):
    """轉圈角速度（0~1），用來把裙擺撐開"""
    return min(1.0, abs(s6_rz(f + 1) - s6_rz(f - 1)) / 2 / 14.0)


def s6_frame(f):
    P = {}
    sway = math.sin(2 * math.pi * (f - 24) / 48) * seg(f, 18, 30) * (1 - seg(f, 66, 74))
    spin1 = math.sin(math.pi * seg(f, 68, 118)); spin2 = math.sin(math.pi * seg(f, 118, 152))
    bow = seg(f, 156, 172) * (1 - seg(f, 184, 192))
    legs(P, 0.03 * abs(sway) + 0.04 * spin2 + 0.08 * bow, extra_r=(20 * bow, 16 * bow, 8 * bow))
    P["Hips"] = [("Y", 6 * sway)]
    P["Spine"] = [("Y", -7 * sway), ("X", 8 * bow)]
    P["Head"] = [("Y", 8 * sway + 5 * bow), ("X", -6 * spin1 + 10 * bow)]
    # 手臂：搖擺時一高一低的芭蕾手、第一圈雙手高舉、第二圈往兩側張開、最後提裙
    # 第 3 版禮服：搖擺到最低的那隻手會被慢半拍的裙擺垂墜蹭到（第 36、58～62 格，約 3～8 mm），搖擺段手臂整體往外多抬 6°
    lift = 6 * seg(f, 18, 30) * (1 - seg(f, 66, 74))      # 只在搖擺段（和 sway 同一段時間），之後的轉圈、行禮與原版相同
    la = (72 - lift - 95 * (0.5 + 0.5 * sway) * seg(f, 18, 30), 15, 0, 25, 0)
    ra = (72 - lift - 40 * (0.5 - 0.5 * sway) * seg(f, 18, 30), 15, 0, 25, 0)
    up = spin1; out = spin2
    def mix(a, b, w): return tuple(x + (y - x) * w for x, y in zip(a, b))
    la = mix(la, (-60, 5, 10, 30, 0), up); ra = mix(ra, (-60, 5, 10, 30, 0), up)
    la = mix(la, (15, 10, 0, 15, 0), out); ra = mix(ra, (15, 10, 0, 15, 0), out)
    la = mix(la, (52, 8, 0, 20, 0), bow); ra = mix(ra, (52, 8, 0, 20, 0), bow)
    arm_pose(P, "L", la); arm_pose(P, "R", ra)
    face = {"Fcl_ALL_Fun": 0.6, "Fcl_ALL_Joy": max(spin1, spin2), "Fcl_EYE_Close": 0.7 * bow}
    return dict(P, rz=s6_rz(f), root=(0.10 * sway, 0, 0), ground=True,
                hands=(("relax", "pinch", bow), ("relax", "pinch", bow)), face=face)


def s6_cam(i):
    a = math.radians(-18 + 36 * ease(i / S6_N))
    r = 3.3
    aim(bpy.data.objects["Camera"], (math.sin(a) * r, -math.cos(a) * r, 1.35), (0, 0, 0.95), 40)


# 給 run_scene.py 用的描述（每個情境模組都要有）
SCENE = dict(id="s6", title="宴會廳轉圈", N=S6_N, build=s6_build, frame=s6_frame, props=s6_props, cam=s6_cam,
             desc="左右搖擺的舞步，雙手高舉轉一圈、再張開手快轉一圈（裙擺撐開），最後屈膝行禮。花瓣飄落、鏡頭慢慢繞。",
             outfit="costume", res=(960, 540), stills=())
