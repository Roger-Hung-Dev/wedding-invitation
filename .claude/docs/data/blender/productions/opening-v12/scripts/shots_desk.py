# 桌面幕：①、②前段（02a）、④、⑥、⑧前段（08a）與結尾（08c）。全部俯拍、沒有角色。
# 時間一律是「這一幕開始後的秒數」。字幕、大標、名字、帳號、愛心虛線都在合成階段疊 2D（鋼筆逐字寫出）；
# 每幕的 track() 回傳要疊字的區域在成片上的像素座標（鏡頭會慢推，合成要跟著）。
import bpy, math, random
from mathutils import Vector, Matrix

_dbuilt = {"desk": False}


def need_desk():
    if not _dbuilt["desk"]:
        build_desk(); _dbuilt["desk"] = True
    desk_world()
    desk_hide_all()


def corners_of(name, w, h, z=0.0):
    """物件局部座標裡 w×h 矩形的四角 → 成片像素"""
    o = bpy.data.objects[name]; bpy.context.view_layer.update()
    M = o.matrix_world
    return [screen_px(M @ Vector((x, y, z))) for x, y in ((-w / 2, h / 2), (w / 2, h / 2), (w / 2, -h / 2), (-w / 2, -h / 2))]


def pf_fall(k, t, t0, t1, end, rz0=0.0, rz1=40.0, h=0.07):
    """押花從鏡頭前飄下來，停在 end"""
    u = lin01(t, t0, t1)
    e = ease(u)
    x = end[0] + 0.03 * math.sin(6 * u) * (1 - e); y = end[1] + 0.02 * (1 - e)
    z = end[2] + h * (1 - e) ** 1.5
    pf_set(k, x, y, rz0 + (rz1 - rz0) * e, z=z, on=t >= t0)


# ══════════ ① 0:00–0:07（7 秒）蠟封裂開 → 封口蓋掀起 → 信紙抽出、攤平 → 押花飄落 ══════════
LET1 = (0.012, -0.006, 1.5)          # 信紙最後的位置與角度


def s01_props(t):
    for n in ("D_Letter", "D_Env", "D_LavenderSprig", "D_Pen"):
        show_tree(n)
    bpy.data.objects["D_Painting"].hide_render = True
    O = bpy.data.objects
    O["D_SealWhole"].hide_render = True
    # 信封：開頭在正中，0.45～0.95 秒滑到左上角（大半出畫）
    ue = seg01(t, 0.45, 0.95)
    ex, ey, erz = -0.004 + (-0.15 + 0.004) * ue, 0.004 + (0.095 - 0.004) * ue, -3 - 10 * ue
    place("D_Env", ex, ey, erz)
    # 蠟封裂開（0～0.18）：下半往下移一點、轉一點
    uc = seg01(t, 0.04, 0.18)
    O["D_SealBot"].location = (0.0, -0.0016 * uc, 0.0034); O["D_SealBot"].rotation_euler = (0, 0, math.radians(-4 * uc))
    # 封口蓋掀開（0.10～0.40）：繞上緣轉 180°，平躺在信封上方
    O["D_FlapHinge"].rotation_euler = (-math.radians(179.5 * seg01(t, 0.10, 0.40)), 0, 0)
    # 信紙：對摺著藏在信封裡（轉 90°）→ 0.30～0.62 往上抽出、抬起 → 0.55～0.85 移到畫面中央、轉正、攤開
    Me = Matrix.Translation((ex, ey, 0)) @ Matrix.Rotation(math.radians(erz), 4, "Z")
    out = seg01(t, 0.30, 0.62)
    p_in = Me @ Vector((0.0, -0.002 + 0.17 * out, 0.0012 + 0.012 * out))
    mv = seg01(t, 0.55, 0.85)
    p = p_in.lerp(Vector((LET1[0], LET1[1], 0.0042)), mv)
    p.z += 0.01 * math.sin(math.pi * mv)
    rz = (erz + 90) * (1 - mv) + LET1[2] * mv
    letter_set(1 - seg01(t, 0.60, 0.88), p.x, p.y, rz, p.z)
    place("D_LavenderSprig", -0.14, -0.072, 38)
    place("D_Pen", 0.14, -0.068, -36)
    pf_set(4, -0.165, 0.062, 20, z=0.0005)
    pf_set(3, 0.155, 0.088, 10, z=0.0005, s=0.8)
    pf_set(0, 0.168, -0.01, -30, z=0.0005, s=0.7)
    pf_fall(1, t, 1.5, 2.6, (0.112, 0.066, 0.0055), rz0=-30, rz1=25)      # 一片押花從上方飄落，停在信紙右上角


def s01_frame(t, props=True, cast=True, cam=True):
    if props:
        s01_props(t)
    if cam:
        desk_cam(0.372 - 0.012 * lin01(t, 0, 7.8), (0.004, 0.0))           # 7 秒慢推 100→103%


def s01_track():
    return {"letter_text_area": corners_of("D_Letter", LET_W * 0.86, LET_H * 0.7, 0.001)}


SHOTS["01"] = dict(set="Set_Desk", cast=False, t0=0.0, dur=7.0, tail=0.8, build=need_desk, frame=s01_frame, track=s01_track,
                   stills=[0.0, 0.35, 0.7, 3.0])


# ══════════ ②前段（0～1.1 秒）：信紙上的水彩拱門小畫，鏡頭往下「掉進」畫裡 ══════════
def s02a_frame(t, props=True, cast=True, cam=True):
    if props:
        for n in ("D_Letter", "D_LavenderSprig", "D_Pen"):
            show_tree(n)
        letter_set(0.0, 0.0, 0.0, 0.0, 0.0)
        o = bpy.data.objects["D_Painting"]; o.hide_render = False; o.location = (0.0, 0.004, 0.0006)
        place("D_LavenderSprig", -0.15, -0.075, 38); place("D_Pen", 0.15, -0.07, -36)
        pf_set(2, -0.115, 0.07, 15, z=0.0006, s=0.8); pf_set(5, 0.12, -0.065, -20, z=0.0006, s=0.8)
    if cam:
        u = lin01(t, 0.0, 0.85) ** 2.2                                    # 越推越快
        w = 0.36 * (1 - u) + 0.084 * u                                   # 最後畫面寬＝小畫有顏料的範圍（約原畫面的 93%）
        desk_cam(w, (0.0, 0.004))


SHOTS["02a"] = dict(set="Set_Desk", cast=False, t0=0.0, dur=1.1, tail=0.0, build=need_desk, frame=s02a_frame, stills=[0.0, 0.6, 0.85])


# ══════════ ④ 0:23–0:32（9 秒）兩張拍立得滑入、紙膠帶貼上、照片顯影 ══════════
P4 = {"groom": (-0.073, 0.021, 4.0, -0.32, 22), "bride": (0.073, 0.021, -3.0, 0.32, -20)}   # 最後 x, y, 角度；起點 x、起始角度


def s04_props(t):
    show_tree("D_Letter"); bpy.data.objects["D_Painting"].hide_render = True
    letter_set(0.0, 0.0, 0.0, 0.0, 0.0)
    for k, key in enumerate(("groom", "bride")):
        x1, y1, r1, x0, r0 = P4[key]
        u = seg01(t, 0.0 + 0.08 * k, 0.5 + 0.08 * k)
        show_tree(f"D_Pola_{key}")
        place(f"D_Pola_{key}", x0 + (x1 - x0) * u, y1 + 0.01 * (1 - u), r0 + (r1 - r0) * u, 0.0008 + 0.006 * math.sin(math.pi * u))
        tape = bpy.data.objects[f"D_Tape_{key}"]                       # 紙膠帶「撕—貼」：0.45～0.62 秒拉長、壓下
        ut = seg01(t, 0.45 + 0.06 * k, 0.62 + 0.06 * k)
        tape.hide_render = ut <= 0.0
        tape.scale = (max(0.01, ut), 1, 1); tape.location.z = 0.0011 + 0.004 * (1 - ut)
        tape.rotation_euler = (0, 0, math.radians(-6 if k == 0 else 7))
        set_develop(bpy.data.materials[f"D_Photo_{key}"], lin01(t, 0.6 + 0.1 * k, 1.6 + 0.1 * k))
    pf_set(2, 0.0, 0.07, 15, z=0.0006, s=0.75)
    pf_set(0, -0.142, 0.068, -25, z=0.0006, s=0.8)
    pf_set(3, 0.145, 0.07, 30, z=0.0006, s=0.8)
    pf_set(4, -0.15, -0.07, 120, z=0.0006, s=0.8)
    pf_set(6, 0.152, -0.072, -40, z=0.0006, s=0.65)


def s04_frame(t, props=True, cast=True, cam=True):
    if props:
        s04_props(t)
    if cam:
        desk_cam(0.345 - 0.01 * lin01(t, 0, 9.8), (0.0, 0.002))


def s04_track():
    d = {}
    for key in ("groom", "bride"):
        o = f"D_Pola_{key}"
        d[f"{key}_name_border"] = corners_of(o, PL_W - 0.01, 0.028, 0.001)        # 下緣白邊（寫名字）
        bpy.context.view_layer.update()
        M = bpy.data.objects[o].matrix_world
        d[f"{key}_name_border"] = [screen_px(M @ Vector((x, y - (PL_H / 2 - 0.0165), 0.001))) for x, y in
                                   ((-0.0375, 0.014), (0.0375, 0.014), (0.0375, -0.014), (-0.0375, -0.014))]
        d[f"{key}_photo"] = corners_of(f"D_PolaPhoto_{key}", PH_W, PH_H, 0.0)
    return d


SHOTS["04"] = dict(set="Set_Desk", cast=False, t0=0.0, dur=9.0, tail=0.8, build=need_desk, frame=s04_frame, track=s04_track,
                   stills=[0.3, 1.0, 3.0])


# ══════════ ⑥ 0:41–0:52（11 秒）緞帶綁手機、靜音震動 → 明信片滑入顯影 → 郵戳蓋下 ══════════
def s06_props(t):
    show_tree("D_Letter"); bpy.data.objects["D_Painting"].hide_render = True
    letter_set(0.0, 0.0, 0.0, 0.0, 0.0)
    O = bpy.data.objects
    show_tree("D_Phone")
    sh = 0.0
    if 0.65 <= t < 1.2:                                                 # 震動 3 下
        sh = 2.5 * math.sin(2 * math.pi * 6 * (t - 0.65)) * (1 - lin01(t, 0.65, 1.2))
    place("D_Phone", -0.095 + 0.0008 * math.sin(2 * math.pi * 12 * t) * (sh != 0), 0.022, -6 + sh)
    O["D_phone_bell"].hide_render = t >= 0.6; O["D_phone_bell_off"].hide_render = t < 0.6
    for k, (a, b) in enumerate(((0.0, 0.35), (0.15, 0.5))):            # 緞帶自己繞一圈
        cu = O[f"D_RibbonBand{k}"].data
        f = seg01(t, a, b)
        O[f"D_RibbonBand{k}"].hide_render = f <= 0.001
        cu.bevel_factor_start = 0.0; cu.bevel_factor_end = max(0.001, f)
    ub = seg01(t, 0.45, 0.6)
    bow = O["D_Bow"]; bow.hide_render = ub <= 0
    s_ = DESK.get("bow_s", 1.0) * ub * (1 + 0.25 * math.sin(math.pi * ub))
    bow.scale = (max(0.01, s_),) * 3
    # 明信片（3.3 秒從右邊滑入）
    up = seg01(t, 3.3, 3.8)
    show_tree("D_Postcard", t >= 3.25)
    place("D_Postcard", 0.36 + (0.078 - 0.36) * up, 0.026 + 0.01 * (1 - up), 12 * (1 - up) + 3, 0.0008 + 0.005 * math.sin(math.pi * up))
    set_develop(bpy.data.materials["D_PostcardPhoto"], lin01(t, 3.7, 4.7))
    # 郵戳：橡皮章 6.6 秒從上方落下、7.0 秒蓋下、7.4 秒抬起離開；墨印在蓋下那一刻出現
    st = O["D_Stamp"]
    down = seg01(t, 6.6, 6.95); upst = seg01(t, 7.05, 7.45)
    hz = 0.18 * (1 - down) + 0.18 * upst
    show_tree("D_Stamp", 6.55 <= t < 7.5)
    pc = O["D_Postcard"]; bpy.context.view_layer.update()
    pm = O["D_Postmark"]
    target = pc.matrix_world @ Vector((0.036, -0.026, 0.0))
    st.location = (target.x + 0.03 * (1 - down) + 0.05 * upst, target.y - 0.02 * (1 - down) - 0.03 * upst, target.z + 0.0012 + hz)
    st.rotation_euler = (0, 0, math.radians(-12))
    pm.hide_render = t < 6.97
    if t >= 6.97:
        set_alpha(pm.data.materials[0], min(1.0, (t - 6.97) / 0.06))
    for k, (x, y, r, s) in enumerate(((-0.16, 0.075, 20, 0.7), (0.155, -0.08, -30, 0.7), (-0.015, -0.07, 60, 0.6))):
        pf_set((0, 4, 3)[k], x, y, r, z=0.0006, s=s)


def s06_frame(t, props=True, cast=True, cam=True):
    if props:
        s06_props(t)
    if cam:
        desk_cam(0.365 - 0.01 * lin01(t, 0, 11.8), (0.0, 0.0))


def s06_track():
    return {"postcard_right_half": corners_of("D_Postcard", 0.06, 0.07, 0.001), "phone_screen": corners_of("D_Phone", 0.0585, 0.1215, 0.0082)}


SHOTS["06"] = dict(set="Set_Desk", cast=False, t0=0.0, dur=11.0, tail=0.8, build=need_desk, frame=s06_frame, track=s06_track,
                   stills=[0.3, 1.0, 4.2, 7.2])


# ══════════ ⑧前段 0～6.6 秒：押花瓣拼成 3、2、1 → 6.0 秒拱門小畫被風吹起，鏡頭穿過去 ══════════
def s08a_props(t):
    show_tree("D_Letter"); show_tree("D_Env")
    letter_set(0.0, 0.0, 0.0, 0.0, 0.0)
    O = bpy.data.objects
    O["D_SealWhole"].hide_render = True
    place("D_Env", -0.205, -0.112, 14)                                   # 左下角的空信封（封口蓋開著，大半在畫面外）
    O["D_FlapHinge"].rotation_euler = (-math.radians(179.5), 0, 0)
    pt = O["D_Painting"]; pt.hide_render = False
    lift = seg01(t, 6.0, 6.5)
    pt.location = (0.095 - 0.095 * lift, -0.058 + 0.058 * lift, 0.0006 + 0.045 * lift ** 1.6)   # 飛到鏡頭前、滿版
    pt.rotation_euler = (math.radians(-10 * math.sin(math.pi * lift)), math.radians(8 * math.sin(math.pi * lift)), math.radians(-6 + 6 * lift))
    O["D_CountPetals"].hide_render = False
    countdown_update(t, (0.0, 0.012, 0.0))
    pf_set(4, -0.15, 0.07, 30, z=0.0006, s=0.8); pf_set(2, 0.15, 0.075, -10, z=0.0006, s=0.7)


def s08a_frame(t, props=True, cast=True, cam=True):
    if props:
        s08a_props(t)
    if cam:
        u = seg01(t, 6.0, 6.55)
        desk_cam(0.37 * (1 - u) + 0.10 * u, (0.0, 0.0))


SHOTS["08a"] = dict(set="Set_Desk", cast=False, t0=0.0, dur=6.6, tail=0.0, build=need_desk, frame=s08a_frame, stills=[1.0, 3.6, 4.6, 6.3])


# ══════════ ⑧結尾 9.0～10.0 秒：信封自己闔上、蠟封重新印上 R&A（同時淡出至黑） ══════════
def s08c_props(t):
    show_tree("D_Env"); show_tree("D_LavenderSprig"); show_tree("D_Pen")
    O = bpy.data.objects
    place("D_Env", 0.0, 0.0, -3)
    place("D_LavenderSprig", -0.135, -0.07, 38); place("D_Pen", 0.135, -0.07, -36)
    O["D_FlapHinge"].rotation_euler = (-math.radians(179.5 * (1 - seg01(t, 9.05, 9.45))), 0, 0)
    O["D_SealTop"].hide_render = True; O["D_SealBot"].hide_render = True
    sw = O["D_SealWhole"]; us = seg01(t, 9.45, 9.65)
    sw.hide_render = t < 9.45
    sw.scale = (1.25 - 0.25 * us,) * 3; sw.location = (0, 0, 0.0034 + 0.01 * (1 - us))


def s08c_frame(t, props=True, cast=True, cam=True):
    if props:
        s08c_props(t)
    if cam:
        desk_cam(0.34, (0.0, 0.0))


SHOTS["08c"] = dict(set="Set_Desk", cast=False, t0=8.6, dur=1.4, tail=0.0, build=need_desk, frame=s08c_frame, stills=[9.2, 9.8])
