# 第 3 關「低畫質預覽」（2026-10-10，blender-motion-library references/fast-iteration.md §0.5）：
#   第 2 關確認的正式版骨骼（mx_skeleton.py 的 build，FINAL=1）套到穿服裝的新郎、新娘、路人甲，
#   場景、鏡頭、花瓣用現行 SHOTS[幕] 的 build／frame（cast=False，不跑舊的動作），跟不上新動作的道具由這裡接手
#   （③ 紅毯卷＋平貼字、⑤ 手機、⑦ 叉子／酒杯的時間點）。不跑頭髮、裙擺物理。
#
#   "$BL" -b couple.blend -P prod_cli.py -- --run mx_preview SID=07 [STEP=2] [RES=960,540] [SAMPLES=8] [ENGINE=eevee|workbench]
#        [TAG=r1] [T0=…] [T1=…]（只渲一段）[CLOSE=groom:J_Bip_L_LowerArm[:0.55]]（改拍那根骨頭的近照：影片鏡頭角度放大、正面、側面、背面四張，距離 m）
#        [FACE=groom:3/6,bride:4/6]（表情：平常／開心各用表情樣本頁的幾號；沒給就用舊的瞇眼微笑）
#   STEP＝30 fps 的每幾格渲一張（2＝15 fps）
# 輸出：D:\render-work\mixamo\preview\s<幕>\<TAG>\（影格、preview.mp4），製作資料夾 videos/preview-mx/s<幕>_<TAG>.mp4；結尾印 MXPREVIEW_DONE {json}
import bpy, os, json, time, math, subprocess
from mathutils import Vector, Matrix

MODE = "setup"
use("run_prod")
_SID0 = str(globals().get("SID", "07"))
# 只載這一幕要的：shots_v2_s03carpet 有自己的 _wrap(a)，一律載入會蓋掉動作庫 actions_custom 的 _wrap，⑦ 的「被餵食」直接當掉（2026-10-11）
if _SID0 in ("03", "08"):
    use("shots_v2_s0308")              # ⑧ v2_08（run_prod 沒載入，同 v2_s0308_check.py）
if _SID0 == "03":
    use("shots_v2_s03carpet")          # ③ v2_03c
if _SID0 == "07a":
    use("set_v3")                      # 第 3 關第 3 輪回饋「⑦ 拆成兩幕」：⑦a 滿桌菜
if _SID0 == "07b":
    use("set_v3_street")               # ⑦b 晚上的餐廳門口＋計程車

T_START = time.time()
PROD_SCRIPTS_DIR = os.path.dirname(os.path.abspath(PROD_SCRIPT_SELF)) if "PROD_SCRIPT_SELF" in globals() else os.path.join("D:/SideProject/wedding-invitation/.claude/docs/data/blender/productions/opening-v12", "scripts")
SID = str(globals().get("SID", "07"))
SHOT = {"02": "v2_02", "03": "v2_03c", "05": "v2_05", "07": "v2_07", "07a": "v2_07", "07b": "v3_07b", "08": "v2_08"}[SID]
STEP = int(globals().get("STEP", 2))
TAG = str(globals().get("TAG", "r1"))
RES = tuple(int(x) for x in str(globals().get("RES", "960,540")).split(","))
ENGINE = str(globals().get("ENGINE", "eevee")).lower()
SAMPLES = int(globals().get("SAMPLES", 8))
OUT = os.path.join(r"D:\render-work\mixamo\preview", "s" + SID, TAG); os.makedirs(OUT, exist_ok=True)

S = SHOTS[SHOT]
S["build"](); stage(S["set"], cast=True)
ST0 = S.get("t0", 0.0)
if SID == "07a":                       # ⑦a 只有新娘、⑦b 只有新郎
    show("Cast_groom", False)
elif SID == "07b":
    show("Cast_bride", False)

# ── 正式版骨骼（函式庫模式，FINAL=1）──
MXP = os.path.join(os.path.dirname(os.path.abspath(bpy.data.filepath)), "..", "scripts", "mx_skeleton.py")
MXP = os.path.normpath(MXP) if os.path.exists(os.path.normpath(MXP)) else \
    r"D:\SideProject\wedding-invitation\.claude\docs\data\blender\productions\opening-v12\scripts\mx_skeleton.py"
MX = {"__name__": "mx_lib", "MX_LIB": True, "MX_OPT": {"FINAL": "1"}}
exec(compile(open(MXP, encoding="utf8").read(), MXP, "exec"), MX)
MXOUT, POSES = MX["build"](SID, write=False)
apply_pose = MX["_g"]["apply_pose"]
ARMS = {w: bpy.data.objects[w + "_Armature"] for w in POSES}
TGTS = {w: MX["tgt"](w) for w in POSES}
NFR = min(len(p) for p in POSES.values())
t_build = round(time.time() - T_START, 1)
print("MXPREVIEW_BUILD", SID, SHOT, "chars", list(POSES), "frames30", NFR, "build_s", t_build, flush=True)

# ── 渲染設定 ──
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = RES; sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 88
if ENGINE == "workbench":
    try:
        sc.render.engine = "BLENDER_WORKBENCH"
    except TypeError as e:
        print("ENGINE_FALLBACK", e, flush=True)
    sh = sc.display.shading
    sh.light = "STUDIO"; sh.color_type = "TEXTURE"; sh.show_shadows = False; sh.show_cavity = False
else:
    sc.eevee.taa_render_samples = SAMPLES
for o in bpy.data.objects:                     # 擺姿勢加速（quick_tweak 的做法）：網格修改器只關視窗評估，渲染照常
    if o.type == "MESH":
        for m in o.modifiers:
            m.show_viewport = False


def face(who, keys):
    o = bpy.data.objects.get(who + "_Face")
    if o is None or not o.data.shape_keys:
        return
    kb = o.data.shape_keys.key_blocks
    for k, v in keys.items():
        if k in kb:
            kb[k].value = v


def sm(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


# ── 表情（2026-10-11 第 3 關回饋「不要瞇瞇眼、要開口笑、不要長方形的笑、表情要隨動作變換」）──
#   FACE=groom:<平常>/<開心>,bride:<平常>/<開心>（號碼＝表情樣本頁的 1～7，tools/face_samples.py 的 COMBOS）
#   每格先把 Fcl_ 形狀鍵歸零，再照 MOOD 的時間軸在「平常」「開心」之間 0.3 秒漸變；另外每 2.6～4.2 秒眨一次眼（0.16 秒）
FACE_COMBOS = {
    1: {"Fcl_ALL_Joy": 0.6},
    2: {"Fcl_MTH_Joy": 0.8, "Fcl_BRW_Joy": 0.8},
    3: {"Fcl_MTH_Fun": 1.0, "Fcl_BRW_Fun": 0.5},
    4: {"Fcl_MTH_Fun": 0.8, "Fcl_MTH_A": 0.3, "Fcl_BRW_Fun": 0.5},
    5: {"Fcl_MTH_Fun": 0.7, "Fcl_MTH_A": 0.5, "Fcl_BRW_Joy": 0.5, "Fcl_EYE_Spread": 0.15},
    6: {"Fcl_MTH_Fun": 0.6, "Fcl_MTH_A": 0.75, "Fcl_MTH_Large": 0.2, "Fcl_BRW_Joy": 0.7, "Fcl_EYE_Spread": 0.2},
    7: {"Fcl_MTH_Fun": 0.7, "Fcl_MTH_A": 0.4, "Fcl_EYE_Fun": 0.35, "Fcl_BRW_Fun": 0.5},
}
# 2026-10-11 使用者裁決（表情樣本頁 Version 3）：新郎嘴巴 平常 3 號、開心 5 號，眼睛 A3（張大）、眉毛 B3（笑眉）兩種都用；
#   新娘 平常 3 號、開心 6 號。FACE= 參數可以覆寫（測其他組合用）
G_EYE_BRW = {"Fcl_EYE_Spread": 0.5, "Fcl_BRW_Joy": 0.4}
FACE_PICK = {"groom": ({"Fcl_MTH_Fun": 1.0, **G_EYE_BRW}, {"Fcl_MTH_Fun": 0.7, "Fcl_MTH_A": 0.5, **G_EYE_BRW}),
             "bride": (FACE_COMBOS[3], FACE_COMBOS[6])}
for _part in str(globals().get("FACE", "")).split(","):
    if ":" in _part:
        _w, _v = _part.split(":"); _a, _b = _v.split("/")
        FACE_PICK[_w.strip()] = (FACE_COMBOS[int(_a)], FACE_COMBOS[int(_b)])
# 每幕「開心」的時段（幕內秒數；其餘是平常）。照劇情：② 跳舞起、③ 新娘一路開心／新郎推出去後、⑤ 比 YA 時（看到路人甲後收起來）、
#   ⑦ 新娘咬下後與碰杯舉杯、新郎餵食後與碰杯舉杯、結尾兩人、⑧ 揮手比愛心整段
MOOD = {
    "02": {"groom": [(-1, 99)], "bride": [(-1, 99)]},                    # 第 3 關第 3 輪起整幕都在跳舞
    "03": {"groom": [(3.3, 99)], "bride": [(0.0, 99)]},
    "05": {"groom": [(-1, 2.6)], "bride": [(-1, 2.75)]},
    "07": {"groom": [(1.9, 4.4), (6.45, 8.6), (10.5, 99)], "bride": [(2.3, 4.4), (6.45, 8.6), (10.6, 99)]},
    "07a": {"bride": [(2.2, 99)]},                                       # 咬下之後一路開心（嚼、比讚）
    "07b": {"groom": [(-1, 99)]},                                        # 喝醉傻笑
    "08": {"groom": [(-1, 99)], "bride": [(-1, 99)]},
}


def mood_w(t, spans, ramp=0.3):
    w = 0.0
    for a, b in spans:
        w = max(w, sm((t - a) / ramp + 1.0) if t < a else (1.0 if t <= b else 1.0 - sm((t - b) / ramp)))
    return w


def blink(t, who):
    import random
    rnd = random.Random(sum(map(ord, who)) * 100 + sum(ord(ch) * (k + 1) for k, ch in enumerate(SID)))   # 固定種子：每次重渲（15／30 fps）眨眼時間都一樣（幕號可以是 07a）
    tb = rnd.uniform(0.6, 1.8)
    while tb < t + 1.0:
        if tb - 0.08 <= t <= tb + 0.08:
            return 1.0 - abs(t - tb) / 0.08
        tb += rnd.uniform(2.6, 4.2)
    return 0.0


# 個別時段多加的表情（2026-10-11）：⑦ 新娘 2.1 秒湊過去咬那一口時張嘴
#   ⑦a 新娘 1.72～2.15 秒張嘴咬、2.2～3.3 秒閉眼笑著嚼（嘴巴 0.32 秒一開一合）
EXTRA_FACE = {"07": {"bride": [((1.75, 1.92, 2.1, 2.28), {"Fcl_MTH_A": 0.55})]},
              "07a": {"bride": [((1.62, 1.8, 2.02, 2.16), {"Fcl_MTH_A": 0.6, "Fcl_MTH_Fun": 0.2}),
                                ((2.15, 2.35, 3.05, 3.3), {"Fcl_EYE_Joy": 1.0, "Fcl_EYE_Spread": 0.0, "Fcl_MTH_Fun": 0.8,
                                                           "Fcl_MTH_A": lambda t: 0.06 + 0.16 * max(0.0, math.sin(2 * math.pi * (t - 2.2) / 0.32)),
                                                           "Fcl_MTH_Large": 0.0})]},
              # ⑦b 新郎喝醉：整段笑眼（瞇成彎的）、笑眉；2.45～2.8 秒打嗝時嘴巴 O 型、眼睛睜開
              #   （第一版用「半閉眼＋垂眉」近照像在瞪人生氣 → 改成開心的醉）
              "07b": {"groom": [((-1, -1, 99, 99), {"Fcl_EYE_Spread": 0.0, "Fcl_EYE_Joy": 0.42, "Fcl_BRW_Joy": 0.6}),
                                ((2.42, 2.5, 2.66, 2.85), {"Fcl_MTH_O": 0.65, "Fcl_MTH_Fun": 0.0, "Fcl_MTH_A": 0.0, "Fcl_EYE_Joy": 0.0,
                                                           "Fcl_EYE_Surprised": 0.35})]}}


def face_frame(t):
    for who, (calm, joy) in FACE_PICK.items():
        o = bpy.data.objects.get(who + "_Face")
        if o is None or not o.data.shape_keys:
            continue
        kb = o.data.shape_keys.key_blocks
        for k in kb:
            if k.name.startswith("Fcl_"):
                k.value = 0.0
        w = mood_w(t, MOOD.get(SID, {}).get(who, []))
        mix = {}
        for k, v in calm.items():
            mix[k] = mix.get(k, 0.0) + v * (1 - w)
        for k, v in joy.items():
            mix[k] = mix.get(k, 0.0) + v * w
        for (a_, b_, c_, d_), keys in EXTRA_FACE.get(SID, {}).get(who, []):
            we = sm((t - a_) / max(1e-6, b_ - a_)) if t < b_ else (1.0 if t <= c_ else 1.0 - sm((t - c_) / max(1e-6, d_ - c_)))
            if t > a_ and we > 0:
                for k, v in keys.items():                         # 值可以是 fn(t)（例：嚼東西時嘴巴一開一合）
                    mix[k] = mix.get(k, 0.0) * (1 - we) + (v(t) if callable(v) else v) * we
        bl = blink(t, who)
        for k, v in mix.items():
            if k in kb:
                kb[k].value = v * (1 - bl) if k.startswith("Fcl_EYE_") else v
        if bl > 0 and "Fcl_EYE_Close" in kb:
            kb["Fcl_EYE_Close"].value = bl


if not FACE_PICK:
    print("MXPREVIEW_WARN 沒給 FACE=…，表情用舊的（會瞇眼）", flush=True)


# ── 眼珠自動看人（2026-10-11 使用者：「要自動看他在看的人，新娘一起做」）──
#   每格算出要看的點，扣掉頭已經轉過去的角度，剩下的由眼珠（J_Adj_L/R_FaceEye）補：左右最多 25°、上下最多 12°（骨頭只轉 0.22 倍，見 EYE_GAIN）
#   （上下轉時眼皮不會跟著動，轉多了像在瞪人）。換目標時 0.2 秒漸變。目標："bride"／"groom"／"passerby"＝那個人的臉、
#   "cam"＝影片鏡頭、(x, y, z)＝固定點；沒列的時段眼珠朝正前方（跟著頭）
OC_LENS = (-2.05, -2.35, 1.31)
GAZE = {
    "02": {"groom": [(-1, 99, "cam")], "bride": [(-1, 99, "cam")]},      # 整幕跳舞、看鏡頭（第 3 關第 3 輪起拿掉走出來和轉身）
    "03": {"bride": [(-1, 3.4, "groom"), (4.6, 99, "cam")]},              # 推完、揮手時看鏡頭
    "05": {"groom": [(-1, 2.4, OC_LENS), (2.4, 99, "passerby")], "bride": [(-1, 2.55, OC_LENS), (2.55, 99, "passerby")]},
    # ⑦ 和 mx_scene_07 的轉頭計畫一致（2026-10-11 第 2 輪回饋後第三次重做）：看盤子、看杯子、看前方時眼珠跟著頭（不列也可以，列了更準）
    "07": {"groom": [(-1, 0.25, "bride"), (0.5, 1.1, (1.740, -1.098, 0.752)), (1.4, 4.35, "bride"), (4.6, 5.3, (1.62, -1.02, 0.875)),
                     (5.55, 6.85, "bride"), (7.15, 8.55, "cam"), (8.85, 10.4, (1.85, -1.25, 1.18)), (10.65, 99, "cam")],
           "bride": [(-1, 1.05, "groom"), (2.45, 4.35, "groom"), (4.6, 5.35, (2.08, -1.02, 0.875)), (5.6, 6.85, "groom"),
                     (7.15, 8.55, "cam"), (8.85, 10.4, (1.85, -1.25, 1.18)), (10.65, 99, "groom")]},
    "08": {"groom": [(-1, 99, "cam")], "bride": [(-1, 99, "cam")]},
    "07a": {"bride": [(3.4, 5.45, "cam")]},                              # 比讚時看鏡頭；其餘眼珠跟著頭（看菜、看盤子、閉眼嚼）
}
# 2026-10-11 第 3 關第 2 輪回饋「⑧ 眼神要面對鏡頭」：眼珠斜到眼角——VRoid 眼珠骨頭的轉軸在眼球後面約 6 cm（tools/eye_pivot.py：
#   骨頭頭部在虹膜後 5.8 cm），骨頭轉 10° 虹膜就移 1 cm，看起來像斜看 50°。真眼球半徑約 1.3 cm → 骨頭只轉「要看的角度 × 0.22」。
#   要看的角度最多左右 25°、上下 12°（再多就要靠轉頭）
EYE_YAW, EYE_PITCH, GAZE_RAMP, EYE_GAIN = 25.0, 12.0, 0.2, 0.22


def gaze_frame(t):
    import math
    from mathutils import Quaternion
    spans_all = {} if str(globals().get("NOGAZE", "")) == "1" else GAZE.get(SID, {})    # NOGAZE=1：眼珠不轉（比對用）
    todo = []
    for who, spans in spans_all.items():
        arm = bpy.data.objects.get(who + "_Armature")
        if arm is None or "J_Adj_L_FaceEye" not in arm.pose.bones:
            continue
        for nm in ("J_Adj_L_FaceEye", "J_Adj_R_FaceEye"):
            arm.pose.bones[nm].matrix_basis = Matrix.Identity(4)
        todo.append((who, arm, spans))
    if not todo:
        return
    bpy.context.view_layer.update()

    def face_pt(w):
        a = bpy.data.objects.get(w + "_Armature")
        return a.matrix_world @ a.pose.bones["J_Bip_C_Head"].head + Vector((0, 0, 0.06))

    for who, arm, spans in todo:
        A = arm.matrix_world.to_3x3(); Ai = A.inverted()
        hb = arm.data.bones["J_Bip_C_Head"]
        Rd = (arm.matrix_world @ arm.pose.bones["J_Bip_C_Head"].matrix).to_3x3() @ (arm.matrix_world @ hb.matrix_local).to_3x3().inverted()
        fwd = (Rd @ (A @ Vector((0, -1, 0)))).normalized()     # 角色 rest 面向 −Y、左手邊 +X
        up = (Rd @ (A @ Vector((0, 0, 1)))).normalized()
        lft = (Rd @ (A @ Vector((1, 0, 0)))).normalized()
        yaw = pitch = wsum = 0.0
        for a, b, tg in spans:
            w = (sm((t - a) / GAZE_RAMP + 1.0) if t < a else (1.0 if t <= b else 1.0 - sm((t - b) / GAZE_RAMP)))
            if w <= 0:
                continue
            p = face_pt(tg) if isinstance(tg, str) and tg != "cam" else (sc.camera.matrix_world.translation.copy() if tg == "cam" else Vector(tg))
            e = arm.matrix_world @ arm.pose.bones["J_Adj_L_FaceEye"].matrix.translation.lerp(arm.pose.bones["J_Adj_R_FaceEye"].matrix.translation, 0.5)
            d = p - e
            off = math.degrees(fwd.angle(d)) if d.length > 1e-6 else 0.0
            w *= 1.0 - sm((off - 40.0) / 25.0)                 # 對方轉到頭看不到的角度（離頭的正前方 40～65°）時眼珠漸漸回正，不卡在眼角斜眼看
            if w <= 0:
                continue
            y_ = math.degrees(math.atan2(d.dot(lft), max(1e-4, d.dot(fwd))))
            p_ = math.degrees(math.atan2(d.dot(up), math.hypot(d.dot(lft), max(1e-4, d.dot(fwd)))))
            yaw += w * max(-EYE_YAW, min(EYE_YAW, y_)); pitch += w * max(-EYE_PITCH, min(EYE_PITCH, p_)); wsum += w
        if wsum > 1.0:
            yaw /= wsum; pitch /= wsum
        if abs(yaw) < 0.05 and abs(pitch) < 0.05:
            continue
        q = Quaternion(Ai @ up, math.radians(yaw * EYE_GAIN)) @ Quaternion(Ai @ lft, math.radians(-pitch * EYE_GAIN))   # 往上看＝繞左手邊軸轉負角度
        for nm in ("J_Adj_L_FaceEye", "J_Adj_R_FaceEye"):
            pb = arm.pose.bones[nm]; M = pb.matrix.copy(); tr = M.translation.copy()
            pb.matrix = Matrix.Translation(tr) @ q.to_matrix().to_4x4() @ Matrix.Translation(-tr) @ M
    bpy.context.view_layer.update()


# ── 各幕的道具與表情（跟不上新動作的部分）──
if SID == "03":
    # 紅毯：重建成沒有文字牆的版本（使用者 2026-10-10：改回第一版平貼字、不要石頭），字照正式版骨骼的位置與出現秒數
    col = bpy.data.collections.get("V2_Carpet")
    roll_p = next(p for p in MXOUT["props"] if p.get("name") == "紅毯卷")
    flat_p = next(p for p in MXOUT["props"] if p.get("name", "").startswith("紅毯（"))
    words = [p for p in MXOUT["props"] if p.get("kind") == "text"]
    ROLL_R = roll_p["r"]; Y0 = flat_p["min"][1]
    # 紅毯寬照 mx_scene_03（第 3 關第 3 輪回饋「紅地毯做寬一點，人踩在沒有字的紅地毯上」：0.95 → 1.6 m）
    CP.update(x=0.5 * (flat_p["min"][0] + flat_p["max"][0]), w=flat_p["max"][0] - flat_p["min"][0])
    cp_build(col, Y0, ())
    gold = pmat("CP_Text", srgb("#F6E7C8"), rough=0.5, spec=0.3, emit=0.15)
    fnt = _font(); TXT = []
    for i, w in enumerate(words):
        cu = bpy.data.curves.new(f"MX_Txt{i}", "FONT")
        cu.body = w["text"]; cu.size = w["size"]; cu.align_x = "CENTER"; cu.align_y = "CENTER"; cu.extrude = 0.0008
        if fnt:
            cu.font = fnt
        ob = bpy.data.objects.new(f"MX_Txt{i}", cu); col.objects.link(ob)
        cu.materials.append(gold)
        ob.location = (w["c"][0], w["c"][1], CP["z0"] + CP["th"] + 0.003)
        ob.rotation_euler = (0, 0, math.radians(90))
        TXT.append((ob, w["on"]))
    RP = roll_p["path"]; y_start = RP[0][2]

    def roll_y(t):
        for a, b in zip(RP, RP[1:]):
            if a[0] <= t <= b[0]:
                return a[2] + (b[2] - a[2]) * (t - a[0]) / max(1e-6, b[0] - a[0])
        return RP[0][2] if t < RP[0][0] else RP[-1][2]

    def scene_frame(t):
        S["frame"](ST0 + t, props=False, cast=False, cam=True)
        garden_parts(()); v2_parts(("V2_Carpet",)); petals_update(t, v2_03c_petals)
        y = roll_y(t)
        cp_update(y, ROLL_R, -(y - y_start) / ROLL_R, 0.0)
        for ob, on in TXT:
            ob.hide_render = t < on; ob.hide_viewport = t < on
        skirt_squash(t)
        if FACE_PICK:
            face_frame(t)
        else:
            for w in ("groom", "bride"):
                face(w, {"Fcl_ALL_Joy": 0.5})

elif SID == "05":
    S05 = V2S["05"]
    cp = bpy.data.collections.get("Cast_passerby")

    def scene_frame(t):
        S["frame"](ST0 + t, props=True, cast=False, cam=True)
        if cp:                                                        # 舊版 3.76 秒才出現；新版 1.0 秒起就在畫面外走進來
            cp.hide_render = False; cp.hide_viewport = False
        # 手機：舉手機拍照、鞠躬前在右手（walk_in_photo 的握法），摸頭起換到左手（舊版 oops_bow 的握法）
        M = S05["hand_m"]("R") @ S05["relR"] if t < 6.35 else S05["hand_m"]("L") @ S05["relL"]
        phone_set(M.translation, M.col[1].to_3d(), M.col[2].to_3d())
        sc.camera.data.dof.use_dof = False                            # 第 3 關回饋「畫面一開始很糊」：拿掉開場從老相機拉焦到新人（全片都清楚）
        if FACE_PICK:
            face_frame(t)
        else:
            face("groom", {"Fcl_ALL_Joy": 0.6}); face("bride", {"Fcl_ALL_Joy": 0.55})

elif SID == "07":
    S07 = V2S["07"]
    # 叉子、酒杯照新的時間軸（2026-10-11 第 3 關第 2 輪後重做的 ⑦：mx_scene_07 的 T_FORK／T_SPEAR／T_PUT／T_GLASS_*）；
    #   放在桌上的位置在主迴圈前照新動作重算（07_props_from_pose），拿起、放下那一格不會瞬移
    S07.update(t_fork=0.4, t_put=3.4, t_spear=1.0, t_glass_g=5.3, t_glass_b=5.4)
    for nm, seat in (("V2_ChairG", 0.595), ("V2_ChairB", 0.595)):                     # 椅子調高：坐姿骨盆（mx_scene_07 的 SEAT 0.675）往下 8 cm
        o = bpy.data.objects.get(nm)
        if o:
            o.scale.z = o.scale.z * (seat / 0.46)

    def scene_frame(t):
        S["frame"](ST0 + t, props=True, cast=False, cam=True)
        bite = bpy.data.objects.get("V2_ForkBite")
        if bite and t >= 2.15:                                         # 新版 2.0～2.2 秒餵進嘴裡
            bite.hide_render = True
        if FACE_PICK:
            face_frame(t)
        else:
            b07_joy_keys(t)
            face("groom", {"Fcl_ALL_Joy": 0.5})

elif SID == "07a":
    # ⑦a（第 3 關第 3 輪回饋「⑦ 拆成兩幕」的第一幕）：⑦ 的晚餐桌，新娘一個人坐桌子正後方；桌上重排＋加菜（set_v3），叉子一直在她右手
    S07 = V2S["07"]; TCv = Vector((S07["TC"].x, S07["TC"].y, 0.0)); TOP7 = DIN["top"]
    build_feast(bpy.data.collections["V2_DinnerSet"], TCv, TOP7)
    GLASS_7A = feast_layout(TCv, TOP7) + Vector((0, 0, 0.042))                 # 杯子原點＝杯腳握點（桌上 4.2 cm，同 ⑦）
    ch = bpy.data.objects.get("V2_ChairB")
    if ch:                                                                     # 椅子搬到她的座位（mx_scene_07a 的 B7A，面向鏡頭）、調高同 ⑦
        ch.location = (1.85, -0.684, 0.0); ch.rotation_euler = (0, 0, 0); ch.scale.z = ch.scale.z * (0.595 / 0.46)
    CAM_7A, AIM_7A, LENS_7A = Vector((1.85, -3.05, 1.30)), Vector((1.85, -0.98, 0.95)), 50.0   # 同 mx_scene_07a 的 CAM／CAM_AIM
    T_SPEAR_7A, T_BITE_7A = 1.0, 2.1
    S7A = dict(bite_at=None, rel=None)
    # 玻璃杯、酒用平滑的半透明（第 3 關第 5 輪回饋「酒杯變碎玻璃」：預設的抖動透明在 8 取樣下顆粒很粗）
    for mn in ("V2_Glass", "V2_Wine"):
        m_ = bpy.data.materials.get(mn)
        if m_:
            try:
                m_.surface_render_method = "BLENDED"
            except Exception:
                pass

    def fork_rel():
        """叉子握法照手指算（第 3 關第 5 輪回饋「修正動作讓手是真的有拿著叉子」：原本照手骨頭掛固定位置，叉柄從手掌底下穿出來）：
        像拿筆一樣，叉柄夾在拇指尖和食指第 2 節之間，柄尾靠在虎口（拇指根、食指根中間）；叉子的平面朝掌心。回傳相對手骨頭的矩陣"""
        A = ARMS["bride"]; mw = A.matrix_world; pb = A.pose.bones
        P = lambda n: mw @ pb[n].head
        nrm = (P("J_Bip_R_Index1") - P("J_Bip_R_Little1")).cross(P("J_Bip_R_Middle1") - P("J_Bip_R_Hand")).normalized()
        if str(globals().get("FORKGRIP", "solved")) == "solved":
            # 第 3 關第 13 輪回饋「握叉的角度、握法始終不正確，手指也會穿模」：叉子先放在手的 rest 空間、手指照它彎（fork_grip.py，
            #   和 mx_scene_07a 同一個求解）→ 叉子相對手骨頭＝手骨頭 rest 矩陣的反矩陣 × 叉子的 rest 矩陣
            _fg = {}
            exec(compile(open(os.path.join(PROD_SCRIPTS_DIR, "fork_grip.py"), encoding="utf8").read(), "fork_grip.py", "exec"), _fg)
            Bn = A.data.bones
            g = _fg["solve_grip"]({b.name: b.head_local.copy() for b in Bn}, {b.name: b.tail_local.copy() for b in Bn},
                                  {b.name: b.matrix_local.to_quaternion() for b in Bn})
            S7A["grip"] = _fg; S7A["grip_g"] = g
            return Bn["J_Bip_R_Hand"].matrix_local.inverted() @ g["Fr"]
        if str(globals().get("FORKGRIP", "solved")) == "index":
            # 第 3 關第 12 輪回饋「手沒有握著叉子，叉子穿過手像是手指的一部分」：改成西餐握法（手勢 fork_grip）——
            #   叉柄貼在食指下面、順著食指往前，叉尖伸出食指尖外 4 cm、柄尾壓在掌心；中指到小指彎起來包在叉柄下、拇指夾在側面
            curl = (mw @ pb["J_Bip_R_Middle3"].tail) - P("J_Bip_R_Middle1")
            palm = nrm if nrm.dot(curl) > 0 else -nrm                                  # 手指彎過去的那一側＝掌心
            i0, i1 = P("J_Bip_R_Index1"), mw @ pb["J_Bip_R_Index3"].tail
            zi = (i1 - i0).normalized()
            palm = (palm - zi * palm.dot(zi)).normalized()
            # 叉柄往掌心斜 22°：完全順著食指的話，柄尾 6.5 cm 會從手背靠手腕那裡穿出來；斜過去柄尾壓在掌心
            z = (zi - palm * float(globals().get("FORKTILT", 0.4))).normalized()
            palm = (palm - z * palm.dot(z)).normalized()
            grip = i0.lerp(i1, 0.25) + palm * 0.011
            y = palm; x = y.cross(z)
            Mf = Matrix((x, y, z)).transposed().to_4x4(); Mf.translation = grip
            return (mw @ pb["J_Bip_R_Hand"].matrix).inverted() @ Mf
        pinch = ((mw @ pb["J_Bip_R_Thumb3"].tail) + P("J_Bip_R_Index2")) * 0.5
        web = (P("J_Bip_R_Thumb1") + P("J_Bip_R_Index1")) * 0.5
        z = (pinch - web).normalized()
        y = (nrm - z * nrm.dot(z)).normalized(); x = y.cross(z)
        Mf = Matrix((x, y, z)).transposed().to_4x4(); Mf.translation = pinch
        return (mw @ pb["J_Bip_R_Hand"].matrix).inverted() @ Mf

    TABLE_TOP_7A = 0.734                     # 桌巾頂面（mx_scene_07a 的圓桌 z1）

    def table_clip_check(t):
        """手指穿桌面檢查（/fix-animation「手指穿模（例：桌面）」）：兩隻手（手骨頭＋手指）的皮膚頂點自己蒙皮，
        數在桌面圓裡又低於桌面的點、最深幾 mm。印 TABLECLIP"""
        body = bpy.data.objects["bride_Body"]; A = ARMS["bride"]
        if "tclip_idx" not in S7A:
            gn = {g.index: g.name for g in body.vertex_groups}
            pre = tuple("J_Bip_%s_%s" % (s_, f_) for s_ in ("L", "R") for f_ in ("Hand", "Thumb", "Index", "Middle", "Ring", "Little"))
            S7A["tclip_idx"] = [(v.co.copy(), [(gn[g.group], g.weight) for g in v.groups if gn[g.group] in A.pose.bones],
                                 gn[max(v.groups, key=lambda g: g.weight).group])
                                for v in body.data.vertices if v.groups and gn[max(v.groups, key=lambda g: g.weight).group].startswith(pre)]
        defm = {}; n_in = 0; deep = 0.0; who = {}
        tc = Vector((1.85, -1.25))
        for co, ws, own in S7A["tclip_idx"]:
            p = Vector(); tw = 0.0
            for n, w in ws:
                if n not in defm:
                    defm[n] = A.matrix_world @ A.pose.bones[n].matrix @ A.data.bones[n].matrix_local.inverted()
                p += (defm[n] @ co) * w; tw += w
            p /= max(tw, 1e-6)
            if (Vector((p.x, p.y)) - tc).length < 0.485 and p.z < TABLE_TOP_7A:
                n_in += 1; deep = max(deep, TABLE_TOP_7A - p.z); who[own] = who.get(own, 0) + 1
        print("TABLECLIP t %.2f below_table %d deepest_mm %.1f %s" % (t, n_in, deep * 1000,
              ",".join("%s:%d" % (k.replace("J_Bip_", ""), v) for k, v in sorted(who.items(), key=lambda kv: -kv[1])[:4])), flush=True)

    def thumb_probe(t):
        """比讚檢查（/fix-animation「左手比讚的姿勢看不出來在比讚」）：拇指朝上幾度、從鏡頭看拇指剩多長（1＝完全側面、0＝正對鏡頭縮成一點）、
        四指彎了多少（第 1 節到第 3 節方向夾角）、拇指尖比拳頭頂高幾 cm。印 THUMBPROBE"""
        A = ARMS["bride"]; mw = A.matrix_world; pb = A.pose.bones
        W = lambda v: mw @ v
        th0, th1 = W(pb["J_Bip_L_Thumb2"].head), W(pb["J_Bip_L_Thumb3"].tail)
        u = (th1 - th0).normalized()
        cam = bpy.context.scene.camera.matrix_world.translation
        view = (th0 - cam).normalized()
        up_deg = math.degrees(u.angle(Vector((0, 0, 1))))
        vis = math.sin(u.angle(view))
        def bend(f):
            a = (pb["J_Bip_L_%s1" % f].tail - pb["J_Bip_L_%s1" % f].head).normalized()
            b = (pb["J_Bip_L_%s3" % f].tail - pb["J_Bip_L_%s3" % f].head).normalized()
            return math.degrees(a.angle(b))
        fist_top = max(W(pb["J_Bip_L_%s%d" % (f, i)].head).z for f in ("Index", "Middle", "Ring", "Little") for i in (1, 2, 3))
        # 手腕角度（/fix-animation「手腕沒有拉到正確角度，看起來是往外凹」）：手掌（手腕→中指根）相對前臂的夾角，
        #   拆成往掌心／手背（屈伸，正＝往掌心）和往拇指側／小指側（偏，正＝往拇指側）
        fa = (W(pb["J_Bip_L_Hand"].head) - W(pb["J_Bip_L_LowerArm"].head)).normalized()
        hd = (W(pb["J_Bip_L_Middle1"].head) - W(pb["J_Bip_L_Hand"].head)).normalized()
        across = (W(pb["J_Bip_L_Index1"].head) - W(pb["J_Bip_L_Little1"].head)); across = (across - fa * across.dot(fa)).normalized()
        palm_n = fa.cross(across).normalized()                       # 左手：前臂方向 × 往拇指側 → 掌心或手背，下面用手指彎的方向定號
        tipc = W(pb["J_Bip_L_Middle3"].tail) - W(pb["J_Bip_L_Middle1"].head)
        if palm_n.dot(tipc) < 0:
            palm_n = -palm_n
        flex = math.degrees(math.atan2(hd.dot(palm_n), hd.dot(fa)))
        dev = math.degrees(math.atan2(hd.dot(across), hd.dot(fa)))
        print("WRIST t %.2f total %.0f flex(+palm) %.0f dev(+thumb) %.0f" % (t, math.degrees(fa.angle(hd)), flex, dev), flush=True)
        stack = (W(pb["J_Bip_L_Index1"].head) - W(pb["J_Bip_L_Little1"].head)).normalized()
        print("THUMBPROBE t %.2f thumb_up_deg %.0f visible %.2f thumb_above_fist_cm %.1f bend I/M/R/L %.0f/%.0f/%.0f/%.0f | thumb_vs_fingers %.0f fist_tilt %.0f" % (
            t, up_deg, vis, (th1.z - fist_top) * 100, bend("Index"), bend("Middle"), bend("Ring"), bend("Little"),
            math.degrees(u.angle(stack)), math.degrees(stack.angle(Vector((0, 0, 1))))), flush=True)

    def fork_clip_check(t, Mf):
        """穿模檢查（第 3 關第 13 輪回饋「手指也會穿模」）：右手（手骨頭、手指）的皮膚頂點換到叉子座標，數有幾個在叉子裡面
        （叉柄 9×3.5 mm、叉頭寬 2.2 cm，各外加 0.3 mm）、最近的離叉子幾 mm。印 FORKCLIP"""
        # 預覽為了快把身體的骨架修改器關掉（show_viewport），評估網格是沒擺姿勢的 → 自己用骨頭做蒙皮（權重 × 骨頭變形）
        body = bpy.data.objects["bride_Body"]; A = ARMS["bride"]
        if "clip_idx" not in S7A:
            gn = {g.index: g.name for g in body.vertex_groups}
            pre = ("J_Bip_R_Hand", "J_Bip_R_Thumb", "J_Bip_R_Index", "J_Bip_R_Middle", "J_Bip_R_Ring", "J_Bip_R_Little")
            S7A["clip_idx"] = [(v.co.copy(), [(gn[g.group], g.weight) for g in v.groups if gn[g.group] in A.pose.bones])
                               for v in body.data.vertices if v.groups and gn[max(v.groups, key=lambda g: g.weight).group].startswith(pre)]
        Mi = Mf.inverted() @ A.matrix_world
        defm = {}
        inside = 0; near = 1e9
        for co, ws in S7A["clip_idx"]:
            p = Vector(); tw = 0.0
            for n, w in ws:
                if n not in defm:
                    defm[n] = A.pose.bones[n].matrix @ A.data.bones[n].matrix_local.inverted()
                p += (defm[n] @ co) * w; tw += w
            if tw <= 0:
                continue
            p = Mi @ (p / tw)
            if -0.066 <= p.z <= 0.116:
                hw = 0.0045 if p.z < 0.075 else 0.011
                dx, dy = abs(p.x) - hw, abs(p.y) - 0.00175
                if dx < 0.0003 and dy < 0.0003:
                    inside += 1
                    if inside <= 3 and t < 0.01:
                        print("FORKCLIP_V z %.4f x %.4f y %.4f bone %s" % (p.z, p.x, p.y, max(ws, key=lambda nw: nw[1])[0]), flush=True)
                near = min(near, max(dx, dy))
        _pb = A.pose.bones
        def _ang(a_, b_):
            u = (_pb[a_].tail - _pb[a_].head).normalized(); v = (_pb[b_].tail - _pb[b_].head).normalized()
            return math.degrees(u.angle(v))
        print("FORKCLIP t %.2f inside %d nearest_mm %.1f | bend hand-mid1 %.0f mid1-mid3 %.0f hand-idx1 %.0f" % (
            t, inside, near * 1000, _ang("J_Bip_R_Hand", "J_Bip_R_Middle1"), _ang("J_Bip_R_Middle1", "J_Bip_R_Middle3"),
            _ang("J_Bip_R_Hand", "J_Bip_R_Index1")), flush=True)

    def fork_m():
        A = ARMS["bride"]
        return (A.matrix_world @ A.pose.bones["J_Bip_R_Hand"].matrix) @ S7A["rel"]

    def scene_frame(t):
        S["frame"](ST0 + t, props=True, cast=False, cam=True)
        bpy.context.view_layer.update()
        # 比讚時拇指縮短加粗（/fix-animation「大拇指變得纖細又長，不像大拇指」：VRoid 拇指骨頭本來就細長，比讚時豎起來高出拳頭 5.6 cm）：
        #   第 2 節（骨頭 Y＝長度方向）長 THUMBSC[0]、粗 THUMBSC[1]，第 3 節跟著；照比讚的時段漸變（只在記憶體裡）
        _sc = [float(x) for x in str(globals().get("THUMBSC", "1,1")).split(",")]
        _w = max(0.0, min(1.0, (t - 3.3) / 0.3)) * max(0.0, min(1.0, (5.5 - t) / 0.3))
        _pbt = ARMS["bride"].pose.bones["J_Bip_L_Thumb2"]
        _pbt.scale = (1 + (_sc[1] - 1) * _w, 1 + (_sc[0] - 1) * _w, 1 + (_sc[1] - 1) * _w)
        if S7A.get("tu_key") is not None:
            S7A["tu_key"].value = _w
        if S7A.get("thumbs_hand"):                                   # 比讚比好時（權重過半）換成比讚手，前後是原本的手
            _on = _w > 0.5
            S7A["thumbs_hand"][0].hide_render = not _on
            S7A["thumbs_hand"][1].show_render = S7A["thumbs_hand"][1].show_viewport = _on
            _cr = bpy.data.objects.get("V3_ThumbCrease")
            if _cr:
                _cr.hide_render = _on
        bpy.context.view_layer.update()
        Mf = fork_m()
        bpy.data.objects["V2_Fork"].matrix_world = Mf
        if str(globals().get("FORKCLIP", "1")) == "1":
            fork_clip_check(t, Mf)
        if str(globals().get("THUMBPROBE", "")) == "1":
            thumb_probe(t)
        if str(globals().get("TABLECLIP", "1")) == "1":
            table_clip_check(t)
        bite = bpy.data.objects["V2_ForkBite"]
        if t < T_SPEAR_7A:
            bite.matrix_world = Matrix.Translation(S7A["bite_at"]); bite.hide_render = False
        elif t < T_BITE_7A + 0.03:
            bite.matrix_world = Mf @ S07["bite_rel"]; bite.hide_render = False
        else:
            bite.hide_render = True                                            # 2.1 秒咬下（吃掉）
        Mg = Matrix.Translation(GLASS_7A)
        bpy.data.objects["V2_Wine_bride"].matrix_world = Mg; wine_level("V2_Wine_bride", Mg)
        for nm in ("V2_Wine_groom", "V2_Wine_groomWine"):                   # 新郎的杯子和杯裡的酒（酒是分開的物件；之前只藏杯子，酒浮在空中還跟著新郎的手走）
            o = bpy.data.objects.get(nm)
            if o:
                o.hide_render = True; o.hide_viewport = True
        if globals().get("CAMOVR"):                                            # 檢查用：CAMOVR=x,y,z:x,y,z:鏡頭
            _c, _a, _l = str(CAMOVR).split(":")
            look(Vector([float(v) for v in _c.split(",")]), Vector([float(v) for v in _a.split(",")]), float(_l)).data.dof.use_dof = False
        else:
            look(CAM_7A, AIM_7A, LENS_7A).data.dof.use_dof = False
        face_frame(t)

elif SID == "07b":
    # ⑦b（⑦ 拆成兩幕的第二幕）：晚上的餐廳門口（set_v3_street）。車門角度跟著新郎的右手（4.05～4.85 秒拉開）、6.85～7.45 秒關上；
    #   7.7 秒起計程車往 −X 開走（3 m/s² 加速），新郎坐在車裡跟著移動；臉頰醉紅（make_blush，主迴圈前貼上）
    CAM_7B, AIM_7B, LENS_7B = Vector((6.2, 1.45, 1.95)), Vector((0.35, 0.75, 0.9)), 32.0   # 車尾後方的人行道邊、往後拉高（第一版太近，車尾擠在左邊）
    T_DRIVE_7B = 7.7
    CAMOVR = str(globals().get("CAMOVR", ""))
    S7B = dict(door={}, base=ARMS["groom"].location.copy())

    def door_at(t):
        if t < 4.05 or t > 7.45:
            return 0.0
        mx = S7B["door_max"]
        if t < 4.85:
            ks = sorted(S7B["door"])
            return next((S7B["door"][k] for k in ks if k >= round(t * 30)), mx)
        if t < 6.85:
            return mx
        return mx * (1.0 - sm((t - 6.85) / 0.6))

    def scene_frame(t):
        S["frame"](ST0 + t, props=True, cast=False, cam=True)
        dx = -0.5 * 3.0 * max(0.0, t - T_DRIVE_7B) ** 2                           # 3 m/s² 起步，到 9 秒開出 2.5 m
        taxi_set(door_at(t), dx)
        ARMS["groom"].location = S7B["base"] + Vector((dx, 0, 0))
        if CAMOVR:                                                             # 檢查用：CAMOVR=x,y,z:x,y,z:鏡頭（例：從車門正對面拍上車）
            _c, _a, _l = CAMOVR.split(":")
            look(Vector([float(v) for v in _c.split(",")]), Vector([float(v) for v in _a.split(",")]), float(_l)).data.dof.use_dof = False
        else:
            look(CAM_7B, AIM_7B, LENS_7B).data.dof.use_dof = False
        face_frame(t)

elif SID == "08":
    def scene_frame(t):
        S["frame"](ST0 + t, props=True, cast=False, cam=True)
        if FACE_PICK:
            face_frame(t)
        else:
            b08_face_keys(ST0 + t)
            face("groom", {"Fcl_ALL_Joy": 0.6})

else:   # 02
    def scene_frame(t):
        S["frame"](ST0 + t, props=True, cast=False, cam=True)
        if FACE_PICK:
            face_frame(t)
        else:
            w = 0.35 + 0.45 * sm((t - 4.0) / 0.4)                      # 跳舞起張嘴笑（同現行 ② 的 MTH_Joy＋BRW_Joy）
            for who in ("groom", "bride"):
                face(who, {"Fcl_MTH_Joy": w, "Fcl_BRW_Joy": w})


def pose_at(i):
    for w, arm in ARMS.items():
        R, h = POSES[w][min(i, len(POSES[w]) - 1)]
        apply_pose(arm, TGTS[w], R, h)


if SID == "07b":                       # ⑦b 車門開的角度＝新郎右手（握門把）繞門軸轉到的角度（只增不減，最多 80°）；臉頰醉紅
    _hx, _hy = TAXI["hinge"]; _mx = 0.0
    for _i in range(int(4.05 * 30), int(4.85 * 30) + 1):
        pose_at(_i); bpy.context.view_layer.update()
        _pb = ARMS["groom"].pose.bones; _mw = ARMS["groom"].matrix_world
        _g = (_mw @ _pb["J_Bip_R_Hand"].head + _mw @ _pb["J_Bip_R_Middle1"].head) * 0.5
        _mx = max(_mx, min(80.0, math.degrees(math.atan2(_g.y - _hy, _g.x - _hx))))
        S7B["door"][_i] = _mx
    S7B["door_max"] = _mx
    pose_at(0); bpy.context.view_layer.update()
    make_blush(ARMS["groom"], "groom_Face")
    print("MXPREVIEW_07B door_max", round(_mx, 1), flush=True)

if SID == "07a":                       # ⑦a 叉的那一口原本在盤上的位置＝叉起那一格叉子上的位置（拿起時不會瞬移）
    pose_at(0); bpy.context.view_layer.update()
    S7A["rel"] = fork_rel()
    if str(globals().get("THUMBCREASE", "1")) == "1":               # /fix-animation「大拇指面對鏡頭的指節不清楚」：拇指兩個關節畫摺痕線（只畫面向鏡頭那一側）
        _ck = {"color": "#FF0000", "half": 0.003} if str(globals().get("CREASEDEBUG", "")) == "1" else {}
        make_thumb_crease(ARMS["bride"], int(round(4.4 * 30)), pose_at, CAM_7A, **_ck); pose_at(0); bpy.context.view_layer.update()
    if str(globals().get("THUMBSHAPE", "0")) != "0":                 # 試做（效果不明顯，預設關）：比讚專用手形（形狀鍵，set_v3.make_thumbsup_shape）：比讚時才啟用
        S7A["tu_key"] = make_thumbsup_shape(ARMS["bride"], k=float(globals().get("THUMBSHAPE", "2.2")))
    if str(globals().get("THUMBNAIL", "0")) == "1":                 # 試做（只有背面看得到，預設關）：拇指指甲輪廓（set_v3.make_thumb_nail）
        make_thumb_nail(ARMS["bride"])
    if str(globals().get("BODYOUTLINE", "1")) != "0":                # 預設開（/fix-animation「手指輪廓不太明顯，指節不清楚」）：身體沒有描邊、只有臉有 → 臉的 MToon 描邊抄一份給身體
        #   身體皮膚材質的描邊粗細本來就有（0.8 mm，同臉），只是模式是 none；臉是 worldCoordinates → 打開（只在記憶體裡）
        _bo = bpy.data.objects["bride_Body"]
        for _s in _bo.material_slots:
            if _s.material and "SKIN" in _s.material.name:
                _mt = _s.material.vrm_addon_extension.mtoon1.extensions.vrmc_materials_mtoon
                _mt.outline_width_mode = "worldCoordinates"
                if str(globals().get("BODYOUTLINE", "1")) not in ("1", ""):     # 給數字＝改描邊粗細（m）
                    _mt.outline_width_factor = float(globals().get("BODYOUTLINE"))
        bpy.context.view_layer.update()
        print("BODYOUTLINE", [(m.name, m.show_render) for m in _bo.modifiers], flush=True)
    if str(globals().get("THUMBSHAND", "1")) == "1":               # 比讚第 9 版：比讚時換上 Sketchfab 的比讚手（set_v3.load_thumbs_hand）
        _bo = bpy.data.objects["bride_Body"]
        _th = load_thumbs_hand(ARMS["bride"], int(round(4.4 * 30)), pose_at); pose_at(0); bpy.context.view_layer.update()
        _skin = next(s_.material for s_ in _bo.material_slots if s_.material and "SKIN" in s_.material.name)
        _th.data.materials.clear(); _th.data.materials.append(_skin)
        # 膚色對齊小臂（近照頁第 8 版回饋「側面的手的膚色與小臂落差」）：GLB 沒有 UV，套新娘的皮膚材質只讀到貼圖角落的顏色 →
        #   新手每個點的 UV 都設成「新娘左手腕附近那個頂點」的 UV，亮面、陰影色都跟手腕同一個位置
        _gn0 = {g.index: g.name for g in _bo.vertex_groups}
        _uvl = _bo.data.uv_layers.active
        _wh = ARMS["bride"].data.bones["J_Bip_L_Hand"].head_local
        _cand = [v for v in _bo.data.vertices if v.groups and _gn0[max(v.groups, key=lambda g: g.weight).group] == "J_Bip_L_LowerArm"]
        _wv = min(_cand, key=lambda v: (v.co - _wh).length)
        _wuv = next(_uvl.data[li].uv.copy() for li, lp in enumerate(_bo.data.loops) if lp.vertex_index == _wv.index)
        _tuv = _th.data.uv_layers.new(name=_uvl.name)
        for _d in _tuv.data:
            _d.uv = _wuv
        print("THUMBSHAND uv from wrist vertex", _wv.index, [round(c, 4) for c in _wuv], flush=True)
        _om = next((m for m in _bo.modifiers if m.type == "NODES" and "Outline" in m.name), None)
        if _om:                                                       # 描邊照身體（MToon 描邊修改器抄過去）
            with bpy.context.temp_override(object=_bo, active_object=_bo, selected_objects=[_bo, _th], selected_editable_objects=[_bo, _th]):
                bpy.ops.object.modifier_copy_to_selected(modifier=_om.name)
        # 藏原本的左手：左手（手骨頭、手指）頂點的群組＋Mask（反向），插在骨架修改器後面
        _gn = {g.index: g.name for g in _bo.vertex_groups}
        _hg = _bo.vertex_groups.get("V3_LHandHide") or _bo.vertex_groups.new(name="V3_LHandHide")
        _pre = tuple("J_Bip_L_" + f_ for f_ in ("Hand", "Thumb", "Index", "Middle", "Ring", "Little"))
        _hg.add([v.index for v in _bo.data.vertices if v.groups and _gn[max(v.groups, key=lambda g: g.weight).group].startswith(_pre)], 1.0, "REPLACE")
        _mk = _bo.modifiers.new("V3_LHandMask", "MASK"); _mk.vertex_group = "V3_LHandHide"; _mk.invert_vertex_group = True
        while [m.name for m in _bo.modifiers].index("V3_LHandMask") > [m.name for m in _bo.modifiers].index("Armature") + 1:
            with bpy.context.temp_override(object=_bo):
                bpy.ops.object.modifier_move_up(modifier="V3_LHandMask")
        _mk.show_render = _mk.show_viewport = False; _th.hide_render = True
        S7A["thumbs_hand"] = (_th, _mk)
        print("THUMBSHAND mods", [m.name for m in _bo.modifiers], "hand mods", [m.name for m in _th.modifiers], flush=True)
    if str(globals().get("RUFFLEFOLLOW", "0")) == "1":             # 第 3 關第 9 輪回饋「圈起來的兩塊」：荷葉邊跟著底下的皮膚動，蓋住補皮的捲邊
        ruffle_follow_skin(ARMS["bride"])
    if float(globals().get("NECKUP", 0.018)) > 0:                  # 第 3 關第 10 輪回饋「還是有兩塊突出來」：領口往上提，蓋住補皮的胸部上緣（set_v3.raise_neckline）
        raise_neckline(ARMS["bride"], float(globals().get("NECKUP", 0.018)))
    if str(globals().get("FILLNORMALS", "0")) == "1":              # 第 3 關第 10 輪回饋「還是有兩塊突出來」：補皮領口捲邊的自訂法線換成平順的
        smooth_fill_normals(ARMS["bride"])
    if str(globals().get("FILLSMOOTH", "0")) == "1":               # 第 3 關第 9 輪回饋「圈起來的兩塊」：補皮鎖骨那道棱磨平（要在陰影殼、項鍊之前）
        smooth_fill_ridge(ARMS["bride"])
    if str(globals().get("NECKSHADOW", "1")) == "1":               # 第 3 關第 8 輪回饋「脖子不明顯」：脖子陰影＋鎖骨線（set_v3.make_neck_shade）
        _ns = make_neck_shade(ARMS["bride"], **({"strength": 1.0, "clav": 1.0} if str(globals().get("NECKDEBUG", "")) == "1" else {}))
        if str(globals().get("NECKDEBUG", "")) == "1":
            for _o in _ns:
                _bs = next(n for n in _o.data.materials[0].node_tree.nodes if n.type in ("BSDF_PRINCIPLED", "EMISSION"))
                _bs.inputs["Base Color" if _bs.type == "BSDF_PRINCIPLED" else "Color"].default_value = (1, 0, 0, 1)
        if str(globals().get("NECKLACE", "1")) == "1":                # 珍珠項鍊（第 3 關第 9 輪使用者「加上項鍊」）
            make_necklace_skin(ARMS["bride"])
        if str(globals().get("CLAVICLE", "")) == "1":                 # 試做：鎖骨線
            make_clavicles(ARMS["bride"])
    if str(globals().get("CSMOOTH", "")) not in ("", "0"):           # 試做：補皮擺姿勢後的摺痕（肩膀前面一道棱）用 Corrective Smooth 撫平
        _cs = bpy.data.objects["bride_BodyFill"].modifiers.new("V3_CSmooth", "CORRECTIVE_SMOOTH")
        _cs.factor = float(globals().get("CSMOOTH")); _cs.iterations = int(globals().get("CSITER", 10))
        _cs.smooth_type = "LENGTH_WEIGHTED"; _cs.rest_source = "ORCO"; _cs.use_only_smooth = False; _cs.use_pin_boundary = True
    if str(globals().get("RESTPOSE", "")) == "1":                   # 除錯：新娘站回原始姿勢（看形狀是模型本身還是擺姿勢擠出來的）
        ARMS["bride"].data.pose_position = "REST"
    for _nm in str(globals().get("NOSHADOWOBJ", "")).split(","):     # 除錯：指定物件不投影
        if _nm and bpy.data.objects.get(_nm):
            bpy.data.objects[_nm].visible_shadow = False
    for _nm in str(globals().get("HIDEOBJ", "")).split(","):         # 除錯：藏起指定物件（逗號分隔）
        if _nm and bpy.data.objects.get(_nm):
            bpy.data.objects[_nm].hide_render = True
    for _nm in str(globals().get("TINTOBJ", "")).split(","):         # 除錯：指定物件改成純藍平塗，看畫面上哪塊是它
        _o = bpy.data.objects.get(_nm) if _nm else None
        if _o:
            _m = bpy.data.materials.new("DBG_Tint"); _m.use_nodes = True; _t = _m.node_tree
            for _n in list(_t.nodes):
                _t.nodes.remove(_n)
            _e = _t.nodes.new("ShaderNodeEmission"); _e.inputs["Color"].default_value = (0.0, 0.25, 1.0, 1)
            if str(globals().get("TINTMODE", "")) == "restpos":        # rest 座標編成顏色（R＝(x+0.2)/0.4、G＝(z−1.15)/0.25、B＝(y+0.15)/0.3，線性），從畫面反推位置
                _me = _o.data
                if "rest_p" in _me.attributes:
                    _me.attributes.remove(_me.attributes["rest_p"])
                _ra = _me.attributes.new("rest_p", "FLOAT_VECTOR", "POINT")
                _ra.data.foreach_set("vector", [c for v in _me.vertices for c in ((v.co.x + 0.2) / 0.4, (v.co.z - 1.15) / 0.25, (v.co.y + 0.15) / 0.3)])
                _at = _t.nodes.new("ShaderNodeAttribute"); _at.attribute_name = "rest_p"
                _t.links.new(_at.outputs["Vector"], _e.inputs["Color"])
            if str(globals().get("TINTMODE", "")) == "normal":         # 法線當顏色：表面凹凸不平會變成一塊塊色斑
                _g = _t.nodes.new("ShaderNodeNewGeometry"); _v = _t.nodes.new("ShaderNodeVectorMath"); _v.operation = "MULTIPLY_ADD"
                _v.inputs[1].default_value = (0.5, 0.5, 0.5); _v.inputs[2].default_value = (0.5, 0.5, 0.5)
                _t.links.new(_g.outputs["Normal"], _v.inputs[0]); _t.links.new(_v.outputs[0], _e.inputs["Color"])
            _t.links.new(_e.outputs[0], _t.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
            for _i in range(len(_o.material_slots)):
                _o.material_slots[_i].material = _m
    if str(globals().get("NECKGRID", "")) == "1":                     # 除錯：皮膚上畫 rest 座標格線（紅＝z 每 1 cm、z 1.30 加粗；藍＝x 每 2 cm），看畫面位置對應模型哪裡
        def _keep_all(p):
            return 1.22 <= p.z <= 1.37 and abs(p.x) < 0.12 and p.y < 0.04

        def _line(v, step, w):
            d = abs(v / step - round(v / step)) * step
            return 1.0 if d < w else 0.0
        for _src in ("_Body", "_BodyFill"):
            make_skin_shade(ARMS["bride"], "V3_GridZ" + _src, _keep_all, lambda p: max(_line(p.z, 0.01, 0.0007), 1.0 if abs(p.z - 1.30) < 0.0016 else 0.0),
                            color="#FF0000", offset=0.0018, subdiv=4, src=_src)
            make_skin_shade(ARMS["bride"], "V3_GridX" + _src, _keep_all, lambda p: _line(p.x, 0.02, 0.0007), color="#0040FF", offset=0.0021, subdiv=4, src=_src)
        _bf = bpy.data.objects["bride_BodyFill"]
        print("NECKGRID fill", [m.type for m in _bf.modifiers], len(_bf.vertex_groups), "mw_identity", _bf.matrix_world == Matrix.Identity(4), "parent", _bf.parent and _bf.parent.name, flush=True)
        print("NECKGRID objs", [o.name for o in bpy.data.objects if o.name.startswith("bride_") and o.type == "MESH" and not o.hide_render], flush=True)

    _fb = (S7A["rel"] @ S07["bite_rel"]).translation; _fa = (S7A["rel"].to_3x3() @ Vector((0, 0, 1))).normalized()
    print("MXPREVIEW_07A_FORK bite_in_hand", [round(v, 4) for v in _fb], "axis_in_hand", [round(v, 4) for v in _fa], flush=True)
    pose_at(int(round(T_SPEAR_7A * 30))); bpy.context.view_layer.update()
    S7A["bite_at"] = (fork_m() @ S07["bite_rel"]).translation.copy()
    print("MXPREVIEW_07A_PROPS bite_at", [round(x, 3) for x in S7A["bite_at"]], "glass", [round(x, 3) for x in GLASS_7A], flush=True)

if SID == "07":
    # ⑦ 道具放在桌上的位置照新動作算（正式場景的 fork_lie、bite_at、fork_put、glass_g／glass_b 是照舊動作那一格的手算的，
    #   新動作的手不在那裡，拿起、放下時道具會瞬移）：拿起叉子那一格手上的叉子＝桌上的叉子；叉起那一格叉子上的位置＝盤上的牛排塊；
    #   放下那一格手上的叉子＝之後桌上的叉子；拿起酒杯那一格手上的杯子位置＝桌上的杯子（杯子直立，只取位置）
    def _pose_t(t):
        pose_at(int(round(t * 30))); bpy.context.view_layer.update()
    _pose_t(S07["t_fork"]); S07["fork_lie"] = held_fork2() @ S07["fork_roll"]
    _pose_t(S07["t_spear"]); S07["bite_at"] = (held_fork2() @ S07["fork_roll"] @ S07["bite_rel"]).translation.copy()
    _pose_t(S07["t_put"]); S07["fork_put"] = held_fork2() @ S07["fork_roll"]
    _pose_t(S07["t_glass_g"]); S07["glass_g"] = GR["held_prop"]("glass", "L").translation.copy()
    _pose_t(S07["t_glass_b"]); S07["glass_b"] = B["held_prop"]("glass", "R").translation.copy()
    print("MXPREVIEW_07_PROPS fork_lie", [round(x, 3) for x in S07["fork_lie"].translation], "bite_at", [round(x, 3) for x in S07["bite_at"]],
          "fork_put", [round(x, 3) for x in S07["fork_put"].translation], "glass_g", [round(x, 3) for x in S07["glass_g"]],
          "glass_b", [round(x, 3) for x in S07["glass_b"]], flush=True)


# ── 近照模式（CLOSE=角色:骨頭[:距離]）：鏡頭改成對著那根骨頭，從角色正面、外側、背面各拍一張，不出影片 ──
CLOSE = str(globals().get("CLOSE", ""))
if CLOSE:
    c_who, c_bone = CLOSE.split(":")[:2]
    c_dist = float(CLOSE.split(":")[2]) if CLOSE.count(":") >= 2 else 0.55
    OUT = os.path.join(OUT, "close_" + c_who + "_" + c_bone); os.makedirs(OUT, exist_ok=True)
    sc.render.resolution_x = sc.render.resolution_y = 640


def close_shots(t, k):
    arm = ARMS[c_who]; mw = arm.matrix_world; pb = arm.pose.bones
    p = mw @ pb[c_bone].head
    cam0 = sc.camera.matrix_world.translation.copy()                  # 這一幕的影片鏡頭位置（scene_frame 每格會重設）
    cm = look(cam0, p, 50.0 * (cam0 - p).length / c_dist); cm.data.dof.use_dof = False   # 同影片的角度、放大到同樣的取景
    sc.render.filepath = os.path.join(OUT, f"{t:05.2f}_main.jpg")
    bpy.ops.render.render(write_still=True)
    lft = (mw @ pb["J_Bip_L_UpperArm"].head - mw @ pb["J_Bip_R_UpperArm"].head); lft.z = 0; lft.normalize()
    up = Vector((0, 0, 1)); fwd = lft.cross(up).normalized()
    out = lft if "_L_" in c_bone else (-lft if "_R_" in c_bone else lft)
    for nm, d in (("front", fwd), ("side", out), ("back", -fwd)):
        cm = look(p + d * c_dist + up * 0.05, p, 50.0); cm.data.dof.use_dof = False
        sc.render.filepath = os.path.join(OUT, f"{t:05.2f}_{nm}.jpg")
        bpy.ops.render.render(write_still=True)


# ── 花園各幕的打光（2026-10-11 第 3 關第 6 輪：使用者問「新娘的手特別白、看不出身體輪廓」→ 比了 6 種打光，使用者選 E、花園的幕都改）──
#   原因：只有一盞太陽從鏡頭後方往前照，加上卡通材質（MToon）只有亮面／陰影兩色 → 面向鏡頭的皮膚整片在亮面、沒有立體感；
#   皮膚又接近最亮（手臂 246, 232, 218）。E＝曝光 −0.25、太陽稍微偏左、背景光 0.55 → 0.5、角色背後一盞輪廓光往鏡頭照（3.0）。
#   ③ 的鏡頭從側面（+X）拍：太陽方向不動（改了會變逆光），輪廓光改朝 ③ 的鏡頭。命令列給的 SUNDIR／EXPO… 會蓋掉這裡
LIGHT_E = {"02": dict(EXPO=-0.25, SUNDIR="0.6,0.55,-0.6", WORLDS=0.5, RIM=3.0),
           "03": dict(EXPO=-0.25, WORLDS=0.5, RIM=3.0, RIMDIR="0.85,-0.35,-0.35"),
           "05": dict(EXPO=-0.25, SUNDIR="0.6,0.55,-0.6", WORLDS=0.5, RIM=3.0),
           "07a": dict(EXPO=-0.25, SUNDIR="0.6,0.55,-0.6", WORLDS=0.5, RIM=3.0),
           "08": dict(EXPO=-0.25, SUNDIR="0.6,0.55,-0.6", WORLDS=0.5, RIM=3.0)}
if str(globals().get("LIGHT", "E")) == "E":                 # LIGHT=old：舊打光（比對用）
    for _k, _v in LIGHT_E.get(SID, {}).items():
        if not globals().get(_k):
            globals()[_k] = _v

# ── 檢查用：試不同打光（SUNDIR=x,y,z 太陽光前進的方向、SUNE=強度、WORLDS=背景強度、EXPO=曝光）──
if globals().get("SUNDIR") or globals().get("SUNE") or globals().get("WORLDS") or globals().get("EXPO"):
    _sun = next((o for o in bpy.data.objects if o.type == "LIGHT" and o.data.type == "SUN" and not o.hide_render), None)
    if _sun and globals().get("SUNDIR"):
        _d = Vector([float(v) for v in str(SUNDIR).split(",")]).normalized()
        _sun.rotation_euler = _d.to_track_quat("-Z", "Y").to_euler()
    if _sun and globals().get("SUNE"):
        _sun.data.energy = float(SUNE)
    if globals().get("WORLDS"):
        _bg = next(n for n in sc.world.node_tree.nodes if n.type == "BACKGROUND"); _bg.inputs[1].default_value = float(WORLDS)
    if globals().get("EXPO"):
        sc.view_settings.exposure = float(EXPO)
if globals().get("RIM"):                                    # 輪廓光：角色背後一盞太陽光往鏡頭方向照（RIMDIR 可指定方向）
    _ld = bpy.data.lights.get("MX_Rim") or bpy.data.lights.new("MX_Rim", "SUN")
    _ld.energy = float(RIM); _ld.color = (1.0, 0.97, 0.92)
    _ro = bpy.data.objects.get("MX_Rim") or bpy.data.objects.new("MX_Rim", _ld)
    if _ro.name not in sc.collection.objects:
        sc.collection.objects.link(_ro)
    _rd = Vector([float(v) for v in str(globals().get("RIMDIR", "-0.25,-0.9,-0.35")).split(",")]).normalized()
    _ro.rotation_euler = _rd.to_track_quat("-Z", "Y").to_euler()

# ── 檢查用：LIGHTINFO=1 印出這一幕的燈光、背景、色彩設定（第 3 關第 6 輪使用者問「新娘的手特別白、看不出身體輪廓，是燈光太亮？」）──
if str(globals().get("LIGHTINFO", "")) == "1":
    for o in bpy.data.objects:
        if o.type == "LIGHT" and not o.hide_render and all(not c.hide_render for c in o.users_collection):
            d = o.matrix_world.to_3x3() @ Vector((0, 0, -1))
            print("LIGHTINFO", o.name, o.data.type, "energy", round(o.data.energy, 2), "color", tuple(round(c, 2) for c in o.data.color),
                  "loc", tuple(round(v, 2) for v in o.matrix_world.translation), "dir", tuple(round(v, 2) for v in d), flush=True)
    w = sc.world; bg = next((n for n in w.node_tree.nodes if n.type == "BACKGROUND"), None) if w and w.use_nodes else None
    print("LIGHTINFO world", tuple(round(c, 3) for c in bg.inputs[0].default_value[:3]) if bg else None, "strength", bg.inputs[1].default_value if bg else None,
          "| view", sc.view_settings.view_transform, "look", sc.view_settings.look, "exposure", sc.view_settings.exposure, "gamma", sc.view_settings.gamma, flush=True)
    for nm in ("bride_Body", "bride_BodyFill"):
        o = bpy.data.objects.get(nm)
        if o:
            for m in o.data.materials:
                if m and m.use_nodes:
                    grp = [n.node_tree.name for n in m.node_tree.nodes if n.type == "GROUP" and n.node_tree]
                    print("LIGHTINFO mat", nm, m.name, "groups", grp[:3], flush=True)

# ── 主迴圈 ──
i0 = int(round(float(globals().get("T0", 0.0)) * 30)); i1 = min(NFR - 1, int(round(float(globals().get("T1", 99.0)) * 30)))
t_r = time.time(); k = 0
for i in range(i0, i1 + 1, STEP):
    t = i / 30.0
    pose_at(i)
    bpy.context.view_layer.update()
    scene_frame(t)
    bpy.context.view_layer.update()
    gaze_frame(t)
    k += 1
    if CLOSE:
        close_shots(t, k)
        continue
    sc.render.filepath = os.path.join(OUT, f"{k:04d}.jpg")
    bpy.ops.render.render(write_still=True)
    if k % 20 == 0:
        print("MXPREVIEW_PROGRESS", SID, k, round(t, 2), round((time.time() - t_r) / k, 2), "s/frame", flush=True)
t_loop = round(time.time() - t_r, 1)

if CLOSE:
    print("MXPREVIEW_DONE", json.dumps(dict(sid=SID, close=CLOSE, frames=k, out=OUT, total_s=round(time.time() - T_START, 1)), ensure_ascii=False), flush=True)
else:
    fps_out = 30 // STEP
    mp4 = os.path.join(OUT, "preview.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(fps_out), "-i", os.path.join(OUT, "%04d.jpg"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-preset", "veryfast", mp4], check=False)
    vid_dir = r"D:\SideProject\wedding-invitation\.claude\docs\data\blender\productions\opening-v12\videos\preview-mx"
    os.makedirs(vid_dir, exist_ok=True)
    dst = os.path.join(vid_dir, f"s{SID}_{TAG}.mp4")
    if os.path.exists(mp4):
        import shutil
        shutil.copyfile(mp4, dst)
    res = dict(sid=SID, shot=SHOT, tag=TAG, frames=k, fps=fps_out, res=list(RES), engine=ENGINE, samples=SAMPLES,
               build_s=t_build, loop_s=t_loop, per_frame_s=round(t_loop / max(1, k), 2), video=dst, total_s=round(time.time() - T_START, 1))
    print("MXPREVIEW_DONE", json.dumps(res, ensure_ascii=False), flush=True)
