# 角色＋動作 → GLB（給瀏覽器 three.js 即時預覽、拖時間軸、滑桿微調姿勢），另附 bones.json。
#
# 用法（背景 Blender；只讀 .blend，不存檔，可和 GUI Blender／其他背景 Blender 並行）：
#   BL="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
#   ML="D:/SideProject/wedding-invitation/.claude/skills/blender-motion-library/scripts"
#   P="D:/SideProject/wedding-invitation/.claude/docs/data/blender/projects/groom"
#   "$BL" -b "$P/groom_costume.blend" -P "$ML/bl_cli.py" -- --project "$P" --run export_web_preview \
#         CLIPS=walk_fwd,idle,sneak_hand,bonked OUT=D:/render-work/web-preview/groom
#
# 參數（KEY=值，皆可省略）：
#   CLIPS     clip 清單（逗號分隔）。PRESETS 裡的名稱用預設參數（walk_fwd＝V12 ② 新郎、sneak_hand／bonked＝V12 ② 站位）；
#             其他名稱照動作庫 ACT（actions.py＋actions_custom.py）：循環動作取登記的格數（24fps）換算秒數、單次動作取 fn.dur。
#             也可以直接放真人動作捕捉（不經過動作庫的 walk_fwd 混合加工）：
#               <名稱>=mocap:<BVH>:<起>-<迄>   例 walk_mocap_raw=mocap:35_01:60-324
#             BVH 給檔名（找 library/mocap/<檔名>.bvh）或完整路徑；格號是 BVH 的原始格（含頭尾，CMU 120 fps）。
#             用 mocap_retarget.mocap_action 直接套：保留骨頭扭轉對齊（手臂、腿的彎曲平面）、腳底鎖地不陷地，
#             加上男性骨盆修正（和 actions_custom.posture() 相同：骨盆往後 POSTURE_TILT、上身淨往前 POSTURE_SPINE，
#             在鎖腳之前套到世界旋轉上，腿由鎖腳的 IK 重新對腳）。不套規劃器腳印、時間拉長、腳掌滾動縮小、起步停步混合、KNEE_FIX。
#             MOCAP_POSTURE=false 關掉骨盆修正；MOCAP_ARM_FIX=true 打開手臂平均前後位置修正（預設關）；
#             MOCAP_HEADING（預設 90＝朝 +X）、MOCAP_ORIGIN（預設 [0,0]）。
#   OUT       輸出資料夾（預設 D:/render-work/web-preview/<專案名稱>）
#   NAME      檔名前綴（預設 <專案名稱>）
#   FPS       烘焙格率（預設 30）
#   TEX       貼圖最長邊（預設 1024）            JPEG_Q   JPEG 品質（預設 85；目前匯出器把程式產生的貼圖都存 PNG，用不到）
#   MAXV      每個網格最多幾個頂點，超過就減面（預設 25000；臉、頭髮、身體不減，見 PROTECT）。
#             12000 時外套只剩 2 成，襯衫、背心會從外套穿出來（深色斑點、翻領邊鋸齒）；25000 新郎單檔約 10 MB
#   DROP      不匯出的物件（JSON 清單；預設 ["<WHO>_BodyFill"]：衣服底下的補皮膚，外面看不到）
#   MORPHS    要保留的臉部 shape key（JSON 清單；預設 pose_lib.FACE_KEYS 的 13 個；[] 全拿掉）
#   SPLIT     auto（預設：單檔 > MAXMB 才拆）｜true（一律拆成 <NAME>_model.glb＋<NAME>_anims.glb）｜false
#   MAXMB     單檔上限（預設 14）
#   VERIFY    true（預設）：匯出後重新匯入 GLB，逐 clip 抽格比對骨頭角度，並渲染幾張檢查圖到 WORK/web_preview/
#
# 輸出（OUT）：<NAME>.glb（或 _model.glb＋_anims.glb）、bones.json；驗證結果 verify.json（也印在主控台）。
#
# 做法：
#   1. 逐格 pose_frame（動作庫的姿勢＋IK＋腳底鎖定）→ 讀每根身體骨頭（Root＋J_Bip_*）的 matrix_basis。
#      動作庫的整體位移／轉向寫在骨架「物件」上（arm.location／rz）：併進最上層的 Root 骨頭，物件歸零 → 網頁只要播骨頭動畫就會走。
#   2. 每個 clip 一個 Action（逐格關鍵格、線性內插），放進 NLA → glTF 匯出器 ACTIONS 模式各出一個 animation。
#   3. 網格：拿掉 MToon 描邊（Geometry Nodes）與加厚（Solidify），太密的減面（Decimate），材質換成 Principled（貼圖＋顏色、透明模式照 MToon）。
#   4. 匯出後整理 GLB：動畫只留身體骨頭（rotation 全部、translation 只留有動的骨頭），頭髮／眼睛骨頭的常數軌道拿掉、四元數同半球，未用到的資料壓掉。
import bpy, os, json, math, time, struct
import numpy as np
from mathutils import Vector, Matrix, Quaternion

use("studio", "pose_lib", "actions")
t_start = time.time()
_g = globals()


def _param(k, d):
    v = _g.get(k, d)
    return d if v is None else v


CLIPS = _param("CLIPS", "walk_fwd,idle,sneak_hand,bonked")
if isinstance(CLIPS, str):
    CLIPS = [c.strip() for c in CLIPS.split(",") if c.strip()]
OUT = str(_param("OUT", os.path.join(r"D:\render-work\web-preview", MANIFEST["name"])))
NAME = str(_param("NAME", MANIFEST["name"]))
FPS = int(_param("FPS", 30))
TEX = int(_param("TEX", 1024)); JPEG_Q = int(_param("JPEG_Q", 85))
MAXV = int(_param("MAXV", 25000))
DROP = list(_param("DROP", [f"{WHO}_BodyFill"]))
MORPHS = list(_param("MORPHS", FACE_KEYS))
SPLIT = str(_param("SPLIT", "auto")).lower()
MAXMB = float(_param("MAXMB", 14))
VERIFY = bool(_param("VERIFY", True))
PROTECT = [f"{WHO}_Face", f"{WHO}_Hair", f"{WHO}_HairBack", f"{WHO}_Body"]
os.makedirs(OUT, exist_ok=True)
VDIR = os.path.join(WORK, "web_preview"); os.makedirs(VDIR, exist_ok=True)
sc = bpy.context.scene
sc.render.fps = FPS; sc.render.fps_base = 1.0


def log(*a):
    print("[web]", f"{time.time() - t_start:6.1f}s", *a, flush=True)


# ════════ 1. clip 定義 ════════
# V12 ② 新郎（productions/opening-v12/scripts/shots_v2.py 的 v2_02_setup）：
#   走路 dist=1.5, steps=4, dur=3.2, dirx=+1, start=0.15, end=0.25（出發點改成原點，朝 +X 走）。
#   偷牽手／被敲：新郎站定後新娘右手掌心在他的 (+0.382, +0.218, 0.812)（新娘在他左後方：左右差 0.58 m、前後差 0.28 m），
#   gap 0.12、轉頭 34°、伸左手；這裡把新郎放在原點（回傳的姿勢本來就是「角色在原點、面向 -Y」，站位只用來換算目標點）。
V12_TGT = (0.382, 0.218, 0.812)
PRESETS = {
    "walk_fwd": dict(desc="往前走（V12 ② 新郎：1.5 m、4 步、3.2 秒，朝 +X）",
                     make=lambda: walk_fwd(dist=1.5, steps=4, dur=3.2, dirx=1, start=0.15, end=0.25, origin=(0.0, 0.0)),
                     params=dict(dist=1.5, steps=4, dur=3.2, dirx=1, start=0.15, end=0.25, origin=[0.0, 0.0], style="mocap")),
    "idle": dict(desc="站姿待機（動作庫 idle，循環）", make=lambda: ACT["idle"][1], dur=2.0, loop=True, params={}),
    "sneak_hand": dict(desc="偷牽手（V12 ② 站位）",
                       make=lambda: sneak_hand(target=V12_TGT, me=(0.0, 0.0, 0.0), gap=0.12, look=34.0, dur=1.3, hand="L"),
                       params=dict(target=list(V12_TGT), me=[0, 0, 0], gap=0.12, look=34.0, dur=1.3, hand="L")),
    "bonked": dict(desc="被敲抱頭（接在 sneak_hand 結尾之後）",
                   make=lambda: bonked(target=V12_TGT, me=(0.0, 0.0, 0.0), gap=0.12, look=34.0, sneak_dur=1.3, dur=1.3, hand="L"),
                   params=dict(target=list(V12_TGT), me=[0, 0, 0], gap=0.12, look=34.0, sneak_dur=1.3, dur=1.3, hand="L")),
}


def make_mocap(src, a, b):
    """真人動作捕捉直接套到角色上（見檔頭 mocap:）。回傳 mocap_action 的 fn（fn.dur、fn.contacts＝來源格號的著地區段）"""
    if "mocap_action" not in _g:
        use("mocap_retarget")
    path = src if os.path.isabs(src) and os.path.exists(src) else os.path.join(LIB, "mocap", src if src.endswith(".bvh") else src + ".bvh")
    pt, pe = posture_fix() if (_param("MOCAP_POSTURE", True) and "posture_fix" in _g) else (0.0, 0.0)
    orig = _g["_fix_feet"]

    def fix_feet_with_posture(rig, R_fk, roots, *rest, **kw):
        # 骨盆修正寫進世界旋轉（和 walk_mocap 同做法，不加 POSTURE_MOCAP_LEAN）：骨盆往後 pt；腰以上整體淨往前 pe（posture() 的 Spine +(pt+pe) 扣掉骨盆的 −pt）；
        # 腿、腳的世界旋轉不動，交給鎖腳 IK 重新對腳
        if pt or pe:
            # 轉軸＝角色的左右軸：mocap_action 的世界旋轉已經含行進方向（heading），rest 的 +X 跟著轉 heading
            ax = Quaternion(Vector((0, 0, 1)), math.radians(float(_param("MOCAP_HEADING", 90.0)))) @ Vector((1, 0, 0))
            qh = Quaternion(ax, math.radians(-pt)); qs = Quaternion(ax, math.radians(pe))
            R2 = []
            for R in R_fk:
                R = dict(R); R["Hips"] = qh @ R["Hips"]
                for k in list(R):
                    if k != "Hips" and "Leg" not in k and "Foot" not in k and "ToeBase" not in k:
                        R[k] = qs @ R[k]
                R2.append(R)
            R_fk = R2
        return orig(rig, R_fk, roots, *rest, **kw)
    _g["_fix_feet"] = fix_feet_with_posture
    try:
        fn = mocap_action(path, frames=(a, b), heading=float(_param("MOCAP_HEADING", 90.0)),
                          origin=tuple(_param("MOCAP_ORIGIN", [0.0, 0.0])), foot_fix=True,
                          fix_arm_offset=bool(_param("MOCAP_ARM_FIX", False)))
    finally:
        _g["_fix_feet"] = orig
    fn.posture = (pt, pe)
    return fn


def clip_spec(key):
    if "=mocap:" in key or key.startswith("mocap:"):
        name, _, rest = key.partition("=") if "=mocap:" in key else ("", "", key)
        _, src, rng = rest.split(":", 2)
        a, b = (int(x) for x in rng.split("-"))
        name = name or f"mocap_{os.path.splitext(os.path.basename(src))[0]}_{a}_{b}"
        fn = make_mocap(src, a, b)
        return dict(name=name, desc=f"真人動作捕捉直接套用（{os.path.basename(src)} 第 {a}～{b} 格）", fn=fn, dur=fn.dur, loop=False,
                    N=int(round(fn.dur * FPS)) + 1, contacts_src=fn.contacts, src_n=len(fn.R),
                    params=dict(bvh=src, frames=[a, b], heading=float(_param("MOCAP_HEADING", 90.0)),
                                origin=list(_param("MOCAP_ORIGIN", [0.0, 0.0])), posture_tilt=fn.posture[0], posture_spine=fn.posture[1],
                                arm_fix=bool(_param("MOCAP_ARM_FIX", False)), info=fn.info))
    if key in PRESETS:
        p = dict(PRESETS[key]); fn = p["make"]()
    elif key in ACT:
        name, fn, n = ACT[key]
        if hasattr(fn, "real"):
            fn = fn.real()
        p = dict(desc=name, params="動作庫登記版", dur=n / 24.0, loop=True)
    else:
        raise KeyError(f"沒有這個動作：{key}（PRESETS 或動作庫 ACT）")
    if hasattr(fn, "dur") and "loop" not in p:
        p["dur"] = fn.dur; p["loop"] = False
    p.setdefault("loop", False)
    p["fn"] = fn; p["name"] = key
    p["N"] = int(round(p["dur"] * FPS)) + 1          # 含頭尾兩格；循環 clip 最後一格＝第一格
    return p


def posture_metrics(H, hips_q):
    """H：骨頭名 → 世界座標的頭部位置；hips_q：骨盆骨頭相對 rest 的世界旋轉（定角色的前方：rest 的 −Y 跟著轉、取水平分量）。
    回傳骨盆斜度（髖→腰椎 和垂直的夾角，正＝往角色前方倒）與左右膝角度（180＝打直）"""
    fwd = Quaternion(hips_q) @ Vector((0.0, -1.0, 0.0)); fwd.z = 0.0
    v = Vector(H["J_Bip_C_Spine"]) - Vector(H["J_Bip_C_Hips"])
    tilt = math.degrees(v.angle(Vector((0, 0, 1)))) * (1 if v.dot(fwd) >= 0 else -1)
    out = dict(pelvis_tilt_deg=round(tilt, 2))
    for sd in "LR":
        a = Vector(H[f"J_Bip_{sd}_UpperLeg"]); b = Vector(H[f"J_Bip_{sd}_LowerLeg"]); c = Vector(H[f"J_Bip_{sd}_Foot"])
        out[f"knee_{sd}_deg"] = round(math.degrees((a - b).angle(c - b)), 2)
    return out


ROOTS = [b.name for b in ARM.data.bones if b.parent is None]
BODY = [b.name for b in ARM.data.bones if b.name.startswith("J_Bip_")]
EXP = ROOTS + BODY
REST_LOCAL = {n: ARM.data.bones[n].matrix_local.copy() for n in EXP}
REST_POSTURE = posture_metrics({n: REST_LOCAL[n].to_translation() for n in EXP}, (1.0, 0.0, 0.0, 0.0))   # 對照：VRoid rest 的骨盆斜度

# ════════ 2. 逐格取樣 ════════
SAMPLES = {}
REF = {}
_chain_keep = _g.get("_chain")
# 取樣時關掉角色網格的所有修改器（只關視窗評估）：每轉一根骨頭 Blender 就重算一次網格，描邊（GN）＋加厚在 6 萬頂點的西裝上每格要 3 秒多。
# 擺姿勢只用骨頭與原始網格資料（腳底取樣點、頭髮表面 BVH 都讀 mesh.data），結果不變
_mod_vis = [(m, m.show_viewport) for o in bpy.data.objects if o.type == "MESH" and o.parent == ARM for m in o.modifiers]
for m, _v in _mod_vis:
    m.show_viewport = False
for _ck in CLIPS:
    spec = clip_spec(_ck); fn = spec["fn"]; N = spec["N"]; key = spec["name"]
    rows = []; ref = []; moved = set(ROOTS)
    t0 = time.time()
    for i in range(N):
        u = i / (N - 1)
        t = (u % 1.0) if spec["loop"] else min(u, 0.9999)
        pose_frame(ARM, fn(t))
        if _chain_keep is not None and _g.get("_chain") is not _chain_keep:   # mocap_retarget 舊版會蓋掉 actions_custom 的 _chain（見 shots_v2.py）
            _g["_chain"] = _chain_keep
        bpy.context.view_layer.update()
        Mo = ARM.matrix_world.copy()
        fr = {}; rf = {}
        for n in EXP:
            pb = ARM.pose.bones[n]
            Bm = pb.matrix_basis.copy()
            if n in ROOTS:                              # 物件位移／轉向併進 Root：新的 pose 矩陣＝Mo @ 舊的
                L = REST_LOCAL[n]; Bm = L.inverted() @ Mo @ L @ Bm
            loc, q, _s = Bm.decompose()
            if loc.length > 1e-4:
                moved.add(n)
            fr[n] = (tuple(loc), tuple(q))
            W = Mo @ pb.matrix
            rf[n] = (tuple(W.to_translation()), tuple(W.to_3x3().normalized().to_quaternion()))
        rows.append(fr); ref.append(rf)
    SAMPLES[key] = dict(spec=spec, rows=rows, moved=sorted(moved))
    REF[key] = ref
    log("sampled", key, N, "frames", f"{time.time() - t0:.1f}s", "translated bones:", sorted(moved))

reset_pose(ARM); ARM.location = (0, 0, 0); ARM.rotation_euler = (0, 0, 0); set_face({})
for m, _v in _mod_vis:
    m.show_viewport = _v
bpy.context.view_layer.update()

# ════════ 3. Action（每個 clip 一個，放進 NLA） ════════
ad = ARM.animation_data_create()
ad.action = None
ACTS = {}
for tr in list(ad.nla_tracks):
    ad.nla_tracks.remove(tr)
for key, S in SAMPLES.items():
    act = bpy.data.actions.new(key); act.use_fake_user = True; ACTS[key] = act
    ad.action = act
    rows = S["rows"]; N = len(rows)
    for n in EXP:
        pb = ARM.pose.bones[n]; pb.rotation_mode = "QUATERNION"
        qs = []; prev = None
        for fr in rows:
            q = Quaternion(fr[n][1])
            if prev is not None and q.dot(prev) < 0:
                q.negate()
            qs.append(q); prev = q
        chans = [(f'pose.bones["{n}"].rotation_quaternion', i, [q[i] for q in qs]) for i in range(4)]
        if n in S["moved"]:
            chans += [(f'pose.bones["{n}"].location', i, [fr[n][0][i] for fr in rows]) for i in range(3)]
        for path, idx, vals in chans:
            fc = act.fcurve_ensure_for_datablock(ARM, path, index=idx, group_name=n)
            fc.keyframe_points.clear()
            fc.keyframe_points.add(N)
            co = [0.0] * (2 * N)
            co[0::2] = [float(f) for f in range(N)]; co[1::2] = vals
            fc.keyframe_points.foreach_set("co", co)
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
            fc.update()
    ad.action = None
    trk = ad.nla_tracks.new(); trk.name = key
    trk.strips.new(key, 0, act)
    trk.mute = True
log("actions", list(SAMPLES))

# ════════ 4. 網格與材質 ════════
for n in DROP:
    if n in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[n])
MESHES = [o for o in bpy.data.objects if o.type == "MESH" and o.parent == ARM and not o.hide_render]
mesh_info = []
for o in MESHES:
    for m in list(o.modifiers):
        if m.type in ("NODES", "SOLIDIFY"):
            o.modifiers.remove(m)
    nv = len(o.data.vertices)
    if o.data.shape_keys:
        keep = set(MORPHS)
        for kb in list(o.data.shape_keys.key_blocks)[1:]:
            if kb.name not in keep:
                o.shape_key_remove(kb)
        if len(o.data.shape_keys.key_blocks) == 1:
            o.shape_key_remove(o.data.shape_keys.key_blocks[0])
    ratio = 1.0
    if o.name not in PROTECT and not o.data.shape_keys and nv > MAXV:
        # 減面直接套用到網格（不留修改器）：匯出器烘動畫時每一格都會重算整個網格，留著修改器 4 個 clip 要十幾分鐘
        ratio = MAXV / nv
        d = o.modifiers.new("WebDecimate", "DECIMATE"); d.decimate_type = "COLLAPSE"; d.ratio = ratio
        try:
            o.modifiers.move(len(o.modifiers) - 1, 0)
        except Exception:
            pass
        with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o], selected_editable_objects=[o]):
            bpy.ops.object.modifier_apply(modifier=d.name)
    mesh_info.append(dict(name=o.name, verts=nv, verts_out=len(o.data.vertices), decimate=round(ratio, 3)))
# 檔案裡其他舊 action（之前做動作測試留下的）不匯出：ACTIONS 模式會把骨架能用的 action 全部匯出
_mine = set(ACTS.values())
for a in list(bpy.data.actions):
    if a not in _mine:
        bpy.data.actions.remove(a)
for key, act in ACTS.items():
    act.name = key                                       # 同名的舊 action 刪掉之後，新的（可能叫 idle.001）改回原名

_img_cache = {}


def web_image(img):
    if img is None:
        return None, False
    if img.name in _img_cache:
        return _img_cache[img.name]
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32); img.pixels.foreach_get(px)
    a = px[3::4]; has_alpha = bool((a < 0.98).any())
    s = min(1.0, TEX / max(w, h))
    if s < 1.0:
        tmp = img.copy(); tmp.scale(max(1, int(w * s)), max(1, int(h * s)))
        w, h = tmp.size; px = np.empty(w * h * 4, dtype=np.float32); tmp.pixels.foreach_get(px)
        bpy.data.images.remove(tmp)
    ni = bpy.data.images.new("W" + img.name.strip("_"), w, h, alpha=has_alpha)
    ni.colorspace_settings.name = img.colorspace_settings.name
    ni.pixels.foreach_set(px)
    ni.file_format = "PNG" if has_alpha else "JPEG"
    ni.pack()
    _img_cache[img.name] = (ni, has_alpha)
    return ni, has_alpha


def _sock(node, ident):
    return next(s for s in node.inputs if s.identifier == ident)


_mat_cache = {}
MAT_INFO = []


def web_material(m):
    if m.name in _mat_cache:
        return _mat_cache[m.name]
    e = m.vrm_addon_extension.mtoon1
    pbr = e.pbr_metallic_roughness; ext = e.extensions.vrmc_materials_mtoon
    src = pbr.base_color_texture.index.source if e.enabled else None
    img, has_alpha = web_image(src)
    mode = e.alpha_mode if e.enabled else "OPAQUE"
    if mode == "MASK" and img is not None and not has_alpha:
        mode = "OPAQUE"                                  # 貼圖沒有透明的地方：當不透明（貼圖可以存 JPEG）
    nm = bpy.data.materials.new("W_" + m.name.replace(" (Instance)", ""))
    nm.use_nodes = True
    nt = nm.node_tree; N_ = nt.nodes; L_ = nt.links
    bsdf = next(n for n in N_ if n.type == "BSDF_PRINCIPLED")
    _sock(bsdf, "Metallic").default_value = 0.0
    _sock(bsdf, "Roughness").default_value = 0.85
    fac = tuple(pbr.base_color_factor) if e.enabled else (0.8, 0.8, 0.8, 1.0)
    if img is not None:
        tx = N_.new("ShaderNodeTexImage"); tx.image = img; tx.location = (-600, 200)
        L_.new(tx.outputs["Color"], _sock(bsdf, "Base Color"))
        if mode == "MASK":
            r = N_.new("ShaderNodeMath"); r.operation = "ROUND"; r.location = (-300, 0)
            L_.new(tx.outputs["Alpha"], r.inputs[0]); L_.new(r.outputs[0], _sock(bsdf, "Alpha"))
        elif mode == "BLEND":
            L_.new(tx.outputs["Alpha"], _sock(bsdf, "Alpha"))
    else:
        _sock(bsdf, "Base Color").default_value = fac
        if mode != "OPAQUE":
            _sock(bsdf, "Alpha").default_value = fac[3]
    try:
        nm.surface_render_method = "BLENDED" if mode == "BLEND" else "DITHERED"
    except Exception:
        pass
    nm.use_backface_culling = not e.double_sided
    info = dict(name=nm.name, source=m.name, alpha=mode, double_sided=bool(e.double_sided),
                base_color=[round(x, 4) for x in fac], texture=(img.name if img else None),
                texture_format=(img.file_format if img else None), texture_size=(list(img.size) if img else None),
                shade_color=[round(x, 4) for x in ext.shade_color_factor] if e.enabled else None)
    MAT_INFO.append(info)
    _mat_cache[m.name] = nm
    return nm


for o in MESHES:
    for sl in o.material_slots:
        if sl.material:
            sl.material = web_material(sl.material)
log("meshes", [(x["name"], x["verts"], x["decimate"]) for x in mesh_info])

# ════════ 5. 匯出 ════════
COMMON = dict(export_format="GLB", use_selection=True, export_apply=False, export_yup=True, export_optimize_disable_viewport=True,
              export_image_format="AUTO", export_jpeg_quality=JPEG_Q, export_image_quality=JPEG_Q,
              export_materials="EXPORT", export_skins=True, export_def_bones=False, export_leaf_bone=False,
              export_morph=True, export_morph_normal=False, export_morph_animation=False,
              export_animation_mode="ACTIONS", export_force_sampling=True, export_frame_range=False,
              export_anim_slide_to_zero=True, export_optimize_animation_size=True, export_reset_pose_bones=True,
              export_rest_position_armature=True, export_cameras=False, export_lights=False, export_extras=False,
              export_tangents=False)


def do_export(path, meshes=True, anims=True):
    bpy.ops.object.select_all(action="DESELECT")
    ARM.select_set(True); bpy.context.view_layer.objects.active = ARM
    if meshes:
        for o in MESHES:
            o.select_set(True)
    kw = dict(COMMON); kw["export_animations"] = anims
    if not anims:
        kw.pop("export_animation_mode")
    bpy.ops.export_scene.gltf(filepath=path, **kw)


# ── GLB 整理：只留身體骨頭的動畫軌道、四元數同半球、壓掉沒用到的資料 ──
def read_glb(p):
    data = open(p, "rb").read()
    off = 12; js = None; bn_ = b""
    while off < len(data):
        ln, ty = struct.unpack_from("<II", data, off); ch = data[off + 8: off + 8 + ln]
        if ty == 0x4E4F534A: js = json.loads(ch.decode("utf8"))
        elif ty == 0x004E4942: bn_ = ch
        off += 8 + ln
    return js, bytearray(bn_)


def write_glb(p, js, bn_):
    jb = json.dumps(js, separators=(",", ":"), ensure_ascii=False).encode("utf8")
    jb += b" " * ((4 - len(jb) % 4) % 4)
    bn_ = bytes(bn_) + b"\0" * ((4 - len(bn_) % 4) % 4)
    total = 12 + 8 + len(jb) + (8 + len(bn_) if bn_ else 0)
    with open(p, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(jb), 0x4E4F534A)); f.write(jb)
        if bn_:
            f.write(struct.pack("<II", len(bn_), 0x004E4942)); f.write(bn_)


CT = {5126: ("f", 4), 5123: ("H", 2), 5125: ("I", 4), 5121: ("B", 1), 5122: ("h", 2), 5120: ("b", 1)}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def tidy_glb(p, keep_trans):
    js, bn_ = read_glb(p)
    nodes = js.get("nodes", [])
    body = set(EXP)
    stats = dict(dropped=0, kept=0, flipped=0)
    for an in js.get("animations", []):
        ch2 = []; smap = {}; sm2 = []
        for ch in an["channels"]:
            nd = ch["target"].get("node"); pth = ch["target"]["path"]
            nm = nodes[nd]["name"] if nd is not None else ""
            ok = nm in body and (pth == "rotation" or (pth == "translation" and nm in keep_trans))
            if not ok:
                stats["dropped"] += 1; continue
            si = ch["sampler"]
            if si not in smap:
                smap[si] = len(sm2); sm2.append(an["samplers"][si])
            ch2.append(dict(ch, sampler=smap[si])); stats["kept"] += 1
        an["channels"] = ch2; an["samplers"] = sm2
        for ch in ch2:                                   # 四元數同半球（相鄰兩格內插不會繞遠路）
            if ch["target"]["path"] != "rotation":
                continue
            acc = js["accessors"][sm2[ch["sampler"]]["output"]]
            if acc.get("componentType") != 5126:
                continue
            bv = js["bufferViews"][acc["bufferView"]]
            o0 = bv.get("byteOffset", 0) + acc.get("byteOffset", 0); st = bv.get("byteStride", 16)
            prev = None
            for k in range(acc["count"]):
                q = list(struct.unpack_from("<4f", bn_, o0 + k * st))
                if prev is not None and sum(a * b for a, b in zip(q, prev)) < 0:
                    q = [-x for x in q]; struct.pack_into("<4f", bn_, o0 + k * st, *q); stats["flipped"] += 1
                prev = q
    js["animations"] = [a for a in js.get("animations", []) if a["channels"]]
    if not js["animations"]:
        js.pop("animations")
    # 壓掉沒用到的 accessor／bufferView
    used = set()
    for me in js.get("meshes", []):
        for pr in me["primitives"]:
            used |= set(pr["attributes"].values())
            if "indices" in pr: used.add(pr["indices"])
            for tg in pr.get("targets", []): used |= set(tg.values())
    for sk in js.get("skins", []):
        if "inverseBindMatrices" in sk: used.add(sk["inverseBindMatrices"])
    for an in js.get("animations", []):
        for s_ in an["samplers"]: used |= {s_["input"], s_["output"]}
    amap = {}; acc2 = []
    for i, a in enumerate(js.get("accessors", [])):
        if i in used:
            amap[i] = len(acc2); acc2.append(a)
    for me in js.get("meshes", []):
        for pr in me["primitives"]:
            pr["attributes"] = {k: amap[v] for k, v in pr["attributes"].items()}
            if "indices" in pr: pr["indices"] = amap[pr["indices"]]
            if "targets" in pr: pr["targets"] = [{k: amap[v] for k, v in tg.items()} for tg in pr["targets"]]
    for sk in js.get("skins", []):
        if "inverseBindMatrices" in sk: sk["inverseBindMatrices"] = amap[sk["inverseBindMatrices"]]
    for an in js.get("animations", []):
        for s_ in an["samplers"]: s_["input"] = amap[s_["input"]]; s_["output"] = amap[s_["output"]]
    js["accessors"] = acc2
    refs = []
    for a in acc2:
        if "bufferView" in a: refs.append((a, "bufferView"))
        if "sparse" in a:
            refs.append((a["sparse"]["indices"], "bufferView")); refs.append((a["sparse"]["values"], "bufferView"))
    for im in js.get("images", []):
        if "bufferView" in im: refs.append((im, "bufferView"))
    order = sorted({o_[k] for o_, k in refs})
    nb = bytearray(); bmap = {}; bv2 = []
    for i in order:
        bv = js["bufferViews"][i]
        nb += b"\0" * ((4 - len(nb) % 4) % 4)
        o0 = bv.get("byteOffset", 0); ln = bv["byteLength"]
        nbv = dict(bv, byteOffset=len(nb)); nb += bn_[o0:o0 + ln]
        bmap[i] = len(bv2); bv2.append(nbv)
    for o_, k in refs:
        o_[k] = bmap[o_[k]]
    js["bufferViews"] = bv2
    js["buffers"] = [dict(byteLength=len(nb))] if nb else []
    write_glb(p, js, nb)
    return js, stats


keep_trans = set()
for S in SAMPLES.values():
    keep_trans |= set(S["moved"])
files = []
one = os.path.join(OUT, NAME + ".glb")
for f in (one, os.path.join(OUT, NAME + "_model.glb"), os.path.join(OUT, NAME + "_anims.glb")):
    if os.path.exists(f):
        os.remove(f)
do_export(one)
js_one, st = tidy_glb(one, keep_trans)
mb = os.path.getsize(one) / 1e6
log("glb", one, f"{mb:.2f} MB", st)
if SPLIT == "true" or (SPLIT == "auto" and mb > MAXMB):
    os.remove(one)
    pm = os.path.join(OUT, NAME + "_model.glb"); pa = os.path.join(OUT, NAME + "_anims.glb")
    do_export(pm, meshes=True, anims=False); js_model, _ = tidy_glb(pm, keep_trans)
    do_export(pa, meshes=False, anims=True); js_anim, st = tidy_glb(pa, keep_trans)
    files = [pm, pa]; js_ref = js_model
    log("split", [(f, round(os.path.getsize(f) / 1e6, 2)) for f in files])
else:
    files = [one]; js_ref = js_one

# 貼圖實際格式照 GLB 裡寫的（匯出器對程式產生的貼圖一律存 PNG；10 張 1024 以下合計約 1 MB，不必另轉 JPEG）
_mime = {im.get("name"): im.get("mimeType") for im in js_ref.get("images", [])}
for mi in MAT_INFO:
    if mi["texture"]:
        mi["texture_format"] = _mime.get(mi["texture"], mi["texture_format"])

# ════════ 6. bones.json ════════
def to_gl(v):
    return [round(v[0], 5), round(v[2], 5), round(-v[1], 5)]


nidx = {n["name"]: i for i, n in enumerate(js_ref.get("nodes", []))}
bones = []
for n in EXP:
    b = ARM.data.bones[n]
    hd = b.head_local; tl = b.tail_local; d = (tl - hd).normalized()
    gn = js_ref["nodes"][nidx[n]] if n in nidx else {}
    bones.append(dict(name=n, parent=b.parent.name if b.parent else None,
                      head=to_gl(hd), tail=to_gl(tl), dir=to_gl(d), length=round((tl - hd).length, 5),
                      dir_blender=[round(x, 5) for x in d],
                      gltf_rest_rotation=gn.get("rotation", [0, 0, 0, 1]), gltf_rest_translation=gn.get("translation", [0, 0, 0]),
                      animated_translation=n in keep_trans))
clips = []
for key, S in SAMPLES.items():
    sp = S["spec"]; rows = S["rows"]; N = len(rows)
    r0 = REF[key][0][ROOTS[0]][0]; r1 = REF[key][-1][ROOTS[0]][0]
    h0 = REF[key][0]["J_Bip_C_Hips"][0]; h1 = REF[key][-1]["J_Bip_C_Hips"][0]
    pm = {str(f): posture_metrics({n: REF[key][f][n][0] for n in EXP},
                                      Quaternion(REF[key][f]["J_Bip_C_Hips"][1]) @ REST_LOCAL["J_Bip_C_Hips"].to_3x3().normalized().to_quaternion().inverted()) for f in sorted({0, (N - 1) // 2, N - 1})}
    _rq = REST_LOCAL["J_Bip_C_Hips"].to_3x3().normalized().to_quaternion().inverted()
    allm = [posture_metrics({n: REF[key][f][n][0] for n in EXP}, Quaternion(REF[key][f]["J_Bip_C_Hips"][1]) @ _rq) for f in range(N)]
    tl = [m_["pelvis_tilt_deg"] for m_ in allm]
    pm["range"] = dict(pelvis_tilt_min=min(tl), pelvis_tilt_max=max(tl), pelvis_tilt_mean=round(sum(tl) / N, 2),
                       knee_L_min=min(m_["knee_L_deg"] for m_ in allm), knee_R_min=min(m_["knee_R_deg"] for m_ in allm))
    if sp.get("contacts_src"):                         # 真人動作：照著地區段分支撐期中段／擺盪
        sn = sp["src_n"]; fr = lambda i: int(round(i / (sn - 1) * (N - 1)))
        gait = {}
        for sd in "LR":
            runs = sp["contacts_src"][sd]
            st = []
            for a_, b_ in runs:
                if a_ == 0 or b_ >= sn - 1:
                    continue                           # 片段頭尾被切掉的著地段不算「中段」
                f_ = fr((a_ + b_) / 2); st.append(dict(frame=f_, knee_deg=allm[f_][f"knee_{sd}_deg"]))
            on = set()
            for a_, b_ in runs:
                on |= set(range(fr(a_), fr(b_) + 1))
            sw = [f_ for f_ in range(N) if f_ not in on]
            swing = None
            if sw:
                fmin = min(sw, key=lambda f_: allm[f_][f"knee_{sd}_deg"])
                swing = dict(frame=fmin, knee_min_deg=allm[fmin][f"knee_{sd}_deg"])
            gait[sd] = dict(contacts_frames=[[fr(a_), fr(b_)] for a_, b_ in runs], stance_mid=st, swing=swing)
        pm["gait"] = gait
    clips.append(dict(name=key, desc=sp["desc"], frames=N, fps=FPS, duration=round((N - 1) / FPS, 4), loop=sp["loop"],
                      params=sp.get("params"), hips_start=to_gl(h0), hips_end=to_gl(h1), posture=pm))
meta = dict(
    project=MANIFEST["name"], who=WHO, outfit="costume" if any(o.name.startswith(f"{WHO}_Cos_") for o in MESHES) else "base",
    generated=time.strftime("%Y-%m-%d %H:%M:%S"), script=".claude/skills/blender-motion-library/scripts/export_web_preview.py",
    files=[dict(file=os.path.basename(f), bytes=os.path.getsize(f)) for f in files],
    coords=("glTF：Y 朝上、公尺。角色 rest 時面向 +Z、角色的左手在 +X。Blender (x, y, z) → glTF (x, z, -y)。"
            "head／tail／dir 是 rest（T 字站姿）時的世界座標；dir＝頭→尾的單位向量。"),
    root_motion=f"整體位移與轉向烘在 {ROOTS[0]} 骨頭（translation＋rotation）；骨架節點本身不動。",
    channels="每根身體骨頭有 rotation；translation 只有 animated_translation=true 的骨頭。頭髮（J_Sec_*）、眼睛（J_Adj_*）沒有動畫軌道。",
    rest_posture=REST_POSTURE, stand_fix=dict(STAND_FIX=_g.get("STAND_FIX"), KNEE_FIX=_g.get("KNEE_FIX")),
    bones=bones, clips=clips, materials=MAT_INFO, meshes=mesh_info,
    morph_targets=[k for k in MORPHS if k in (bpy.data.objects.get(f"{WHO}_Face").data.shape_keys.key_blocks.keys()
                                             if bpy.data.objects.get(f"{WHO}_Face") and bpy.data.objects[f"{WHO}_Face"].data.shape_keys else [])],
)
json.dump(meta, open(os.path.join(OUT, "bones.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
log("bones.json", len(bones), "bones", [(c["name"], c["frames"], c["duration"]) for c in clips])

# ════════ 7. 驗證：重新匯入 GLB，逐 clip 抽格比對 ════════
if VERIFY:
    def _qang(a, b):
        """兩個四元數的夾角（度），用 Python 雙精度算（mathutils 是單精度，0.04° 以下會變 0）"""
        aw, ax, ay, az = (float(x) for x in a); bw, bx, by, bz = (float(x) for x in b)
        w = aw * bw + ax * bx + ay * by + az * bz                    # conj(a)*b 的 w
        x = aw * bx - ax * bw - ay * bz + az * by
        y = aw * by + ax * bz - ay * bw - az * bx
        z = aw * bz - ax * by + ay * bx - az * bw
        return math.degrees(2.0 * math.atan2(math.sqrt(x * x + y * y + z * z), abs(w)))

    REF_KEEP = REF; ROOT0 = ROOTS[0]; REST_W = {n: (tuple(REST_LOCAL[n].to_translation()),
                                                   tuple(REST_LOCAL[n].to_3x3().normalized().to_quaternion())) for n in EXP}
    FILES = files
    bpy.ops.wm.read_homefile(use_empty=True)
    s2 = bpy.context.scene; s2.render.fps = FPS; s2.render.fps_base = 1.0
    for f in FILES:
        bpy.ops.import_scene.gltf(filepath=f)
    arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    # 拆檔時有兩副骨架：比對用帶動畫的那副（動作檔）；檢查圖也用它（動作檔沒有網格時圖裡看不到人，只看比對數字）
    A2 = next((o for o in arms if o.animation_data and o.animation_data.nla_tracks), arms[0])
    acts = {a.name: a for a in bpy.data.actions}
    res = {}
    for key in REF_KEEP:
        act = acts.get(key) or next((a for n_, a in acts.items() if n_.startswith(key)), None)
        if act is None:
            res[key] = "找不到 action"; continue
        ad2 = A2.animation_data_create()
        for tr in ad2.nla_tracks:
            tr.mute = True
        ad2.action = act
        if act.slots and ad2.action_slot is None:
            ad2.action_slot = act.slots[0]
        N = len(REF_KEEP[key]); out = []
        for f in sorted({0, (N - 1) // 2, N - 1, (N - 1) // 3}):
            s2.frame_set(f); bpy.context.view_layer.update()
            worst = (0.0, ""); pos = 0.0; mag = 0.0
            for n in EXP:
                if n not in A2.pose.bones:
                    continue
                pb = A2.pose.bones[n]
                W = A2.matrix_world @ pb.matrix
                Wr = A2.matrix_world @ pb.bone.matrix_local
                q_new = W.to_3x3().normalized().to_quaternion() @ Wr.to_3x3().normalized().to_quaternion().inverted()
                h_ref, qr = REF_KEEP[key][f][n]
                q_ref = Quaternion(qr) @ Quaternion(REST_W[n][1]).inverted()
                ang = _qang(q_new, q_ref)                      # 匯入後 vs 原本：這根骨頭（相對 rest）的世界旋轉差
                mag = max(mag, _qang(q_ref, (1.0, 0.0, 0.0, 0.0)))   # 對照：原本的姿勢離 rest 轉了多少
                if ang > worst[0] or not worst[1]:
                    worst = (ang, n)
                pos = max(pos, (W.to_translation() - Vector(h_ref)).length)
            Hn = {n: tuple(A2.matrix_world @ A2.pose.bones[n].head) for n in EXP if n in A2.pose.bones}
            _hb = A2.pose.bones["J_Bip_C_Hips"]
            qroot = (A2.matrix_world @ _hb.matrix).to_3x3().normalized().to_quaternion() @                 (A2.matrix_world @ _hb.bone.matrix_local).to_3x3().normalized().to_quaternion().inverted()
            out.append(dict(frame=f, max_angle_deg=round(worst[0], 5), bone=worst[1], max_pos_mm=round(pos * 1000, 3),
                            pose_max_rot_from_rest_deg=round(mag, 1),
                            posture_original=posture_metrics({n: REF_KEEP[key][f][n][0] for n in EXP},
                                                             Quaternion(REF_KEEP[key][f]["J_Bip_C_Hips"][1]) @ Quaternion(REST_W["J_Bip_C_Hips"][1]).inverted()),
                            posture_reimport=posture_metrics(Hn, qroot)))
        res[key] = out
    log("verify", json.dumps(res, ensure_ascii=False))
    # 檢查圖：重新匯入的模型（Principled 材質）在幾個格子的樣子
    imgs = []
    try:
        cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); s2.collection.objects.link(cam); s2.camera = cam
        sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")); s2.collection.objects.link(sun)
        sun.data.energy = 3.0; sun.rotation_euler = (math.radians(50), 0, math.radians(25))
        w = bpy.data.worlds.new("W"); s2.world = w; w.use_nodes = True
        bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND"); bg.inputs[0].default_value = (0.9, 0.88, 0.86, 1); bg.inputs[1].default_value = 1.0
        s2.view_settings.view_transform = "Standard"
        try:
            s2.render.engine = "BLENDER_EEVEE"
        except TypeError:
            pass
        s2.render.resolution_x, s2.render.resolution_y = 600, 800
        def shot(tag, key, f, eye, at, lens):
            act = acts.get(key) or next((a for n_, a in acts.items() if n_.startswith(key)), None)
            A2.animation_data.action = act
            if act and act.slots and A2.animation_data.action_slot is None:
                A2.animation_data.action_slot = act.slots[0]
            s2.frame_set(f)
            cam.location = eye; d = Vector(at) - Vector(eye)
            cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler(); cam.data.lens = lens
            p = os.path.join(VDIR, f"reimport_{tag}.png"); s2.render.filepath = p
            bpy.ops.render.render(write_still=True); imgs.append(p)
        if "idle" in REF_KEEP:
            shot("idle_front", "idle", 0, (0.0, -4.2, 1.0), (0.0, 0.0, 0.9), 50)
            shot("face", "idle", 0, (0.0, -1.1, 1.55), (0.0, 0.0, 1.52), 70)
        if "walk_fwd" in REF_KEEP:
            Nw = len(REF_KEEP["walk_fwd"]); hx = REF_KEEP["walk_fwd"][Nw // 2]["J_Bip_C_Hips"][0]
            shot("walk_mid", "walk_fwd", Nw // 2, (hx[0] + 2.2, -3.4, 1.0), (hx[0], 0.0, 0.9), 50)
        for k_ in [k for k in REF_KEEP if "mocap" in k]:
            Nw = len(REF_KEEP[k_]); hx = REF_KEEP[k_][Nw // 2]["J_Bip_C_Hips"][0]
            shot(k_ + "_mid", k_, Nw // 2, (hx[0] + 2.2, hx[1] - 3.4, 1.0), (hx[0], hx[1], 0.9), 50)
        for k_ in ("sneak_hand", "bonked"):
            if k_ in REF_KEEP:
                shot(k_ + "_end", k_, len(REF_KEEP[k_]) - 1, (1.2, -3.8, 1.1), (0.0, 0.0, 0.95), 50)
    except Exception as ex:
        log("render check failed", repr(ex))
    json.dump(dict(compare=res, images=imgs), open(os.path.join(OUT, "verify.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
log("done", [(os.path.basename(f), round(os.path.getsize(f) / 1e6, 2)) for f in files])
