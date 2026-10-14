# 走位版共用（2026-10-12，B0、B2 做完後抽出來；B3 起用）：代替品方塊、替身膠囊、側面跟拍鏡頭、鏡與鏡的交接狀態。
# 走位版的規則見 SKILL.md「走位版」：替身只排位置，不做接觸；道具、場景用方塊與平面。
import math, json
import bpy, bmesh
from mathutils import Vector
import zanim as Z
STATE = Z.STATE
FPS = 30
CAP_SHIFT = 0.2            # 字卡留白左邊 40% → 主體（兩人中點）放在畫面 70%：鏡頭往左偏「畫面寬 × 0.2」（整支片的鏡頭規則，和導演端約定）
LENS = 35.0
HFOV = 54.43               # 35 mm 鏡頭、36 mm 感光片的水平視角（度）


def frame_w(dist):
    """dist m 處畫面的寬度（m）"""
    return 2 * dist * math.tan(math.radians(HFOV / 2))


def box(name, size, loc, color=(0.6, 0.6, 0.6, 1), origin="bottom"):
    """灰色方塊代替品。origin：bottom＝原點在底面中心"""
    col = Z.studio_col()
    me = bpy.data.meshes.new(name); sx, sy, sz = size
    z0 = 0 if origin == "bottom" else -sz / 2
    v = [(x * sx / 2, y * sy / 2, z0 + z * sz) for x in (-1, 1) for y in (-1, 1) for z in (0, 1)]
    me.from_pydata(v, [], [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.location = loc
    m = bpy.data.materials.new(name + "_mat"); b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = color; me.materials.append(m)
    return o


def capsule(name="ZA_Bride", height=None, radius=0.14, color=(0.85, 0.72, 0.78, 1), nose=True):
    """替身：膠囊＋朝向標記（鼻子，朝 −Y＝面向角度 0）。身高預設＝新郎（2026-10-12 導演端：新娘先和新郎同身形）"""
    col = Z.studio_col()
    H = height or STATE["measure"]["head_top"]
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=radius)
    for v in bm.verts:
        if v.co.z > 0:
            v.co.z += H - 2 * radius
        v.co.z += radius
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); col.objects.link(o)
    m = bpy.data.materials.new(name + "_mat"); b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = color; me.materials.append(m)
    if nose:
        n_ = box(name + "Nose", (0.06, 0.12, 0.06), (0, 0, 0), (0.5, 0.25, 0.35, 1))
        n_.parent = o; n_.location = (0.0, -(radius + 0.03), H - 0.25)
    return o


SKIRT_R = 0.32             # 新娘禮服 bride-blush-ballgown 草稿（2026-10-12）的裙擺半徑：兩人間距要留夠，不然裙子碰新郎的腿
SKIRT_WAIST_Z = 0.62       # 裙子從腰（約骨盆高）開始


def skirt(parent, r=SKIRT_R, waist_r=0.15, waist_z=SKIRT_WAIST_Z, color=(0.95, 0.78, 0.82, 0.9)):
    """替身加裙擺（錐形）：底部半徑 r、腰圍半徑 waist_r，方便看兩人間距"""
    col = Z.studio_col(); name = parent.name + "Skirt"
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=r, radius2=waist_r, depth=waist_z)
    for v in bm.verts:
        v.co.z += waist_z / 2
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.parent = parent
    m = bpy.data.materials.new(name + "_mat"); b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = color; me.materials.append(m)
    return o


def gap_to_groom(bride_xy, poses, i, r=SKIRT_R):
    """裙擺邊緣到新郎兩腿（膝、腳踝）的最近水平距離（m，負＝裙子碰到腿）"""
    tgt = STATE["tgt"]; R, h = poses[i]; Hd = tgt.fk(R, h)
    pts = [Hd[f"J_Bip_{s}_{b}"] for s in "LR" for b in ("LowerLeg", "Foot")]
    return min((Vector((p.x, p.y)) - Vector((bride_xy[0], bride_xy[1]))).length for p in pts) - r - 0.06   # 腿的半徑約 6 cm


def place_capsule(o, xy, yaw_deg):
    """面向角度：0＝朝 −Y（朝鏡頭）、90＝朝 +X（畫面右邊）、270＝朝 −X"""
    o.location = (xy[0], xy[1], 0); o.rotation_euler = (0, 0, math.radians(yaw_deg))


def yaw_of(fw):
    return math.degrees(math.atan2(fw.x, -fw.y))


def hips_fw(R):
    tgt = STATE["tgt"]
    fw = (R["J_Bip_C_Hips"] @ tgt.rest_q["J_Bip_C_Hips"].inverted()) @ Vector((0, -1, 0)); fw.z = 0
    return fw.normalized()


def side_follow(holds=(), handles=1.0, offset=(0.0, -3.0, 0.25), aim_z=0.70, ease_s=1.0, shift=CAP_SHIFT, partner=None):
    """側面跟拍（整支片的鏡頭規則）：鏡頭在主體 −Y 3 m、比骨盆高 0.25 m、看向高度 0.70 m、主體放畫面 70%（右側 60% 區的中間）；
    主體＝新郎骨盆；給 partner(i)→(x, y)（新娘位置）就是兩人中點（2026-10-12 導演端第 1 輪：全片都對準兩人中點）；
    holds：[(鏡內起秒, 迄秒)] 鏡頭固定的時段（例：停下演戲），結束後 ease_s 秒內慢慢追上。回傳 camera_fn(i)→(位置, 看向的點)"""
    import zanim_sample as SP
    follow = SP.follow_camera(offset=offset, aim_z=aim_z, partner=partner)
    dx = -frame_w(abs(offset[1])) * shift
    idx = [(int(round((a + handles) * FPS)), int(round((b + handles) * FPS))) for a, b in holds]

    def f(i):
        l, a = follow(i)
        for i0, i1 in idx:
            if i0 <= i <= i1:
                l, a = follow(i0)
            elif i1 < i <= i1 + int(ease_s * FPS):
                l0, a0 = follow(i0); k = (i - i1) / (ease_s * FPS); k = k * k * (3 - 2 * k)
                l, a = l0.lerp(l, k), a0.lerp(a, k)
        return l + Vector((dx, 0, 0)), a + Vector((dx, 0, 0))
    return f


PROPS_PY = r"D:/SideProject/wedding-invitation/.claude/docs/data/blender/library/props-zepeto/use_props.py"
VENUE_OFFSET = r"D:/render-work/zepeto-anim/opening-proposal-b/venue_offset.json"   # B0 量出來的「場景座標 → 動畫座標」平移（休息室門中心）


def props_api():
    g = {"__file__": PROPS_PY}
    exec(open(PROPS_PY, encoding="utf8").read(), g)
    return g


HIDE = ("I_ZP_softbox_light",)   # 場景端已決定拿掉、素材庫還沒重建的東西（2026-10-12 柔光燈 (a)）：載入時先藏起來


def venue(key, offset=(0.0, 0.0, 0.0), hide=HIDE):
    """把素材庫的場景複製一份真物件進工作場景（不是集合實例：裡面的門、蛋糕、柱子等是各自的物件，可以藏、可以打關鍵影格），
    整組平移 offset（場景座標 → 動畫座標）。key：集合名（例 "Scene_VenueCorridor"）。回傳 {物件名: 物件}"""
    old = bpy.data.collections.get("ZP_" + key)           # 上一次清場景後留下的空集合：素材庫載入會沿用它（變成空的）→ 先刪
    if old is not None and not any(old in s.collection.children_recursive for s in bpy.data.scenes):
        bpy.data.collections.remove(old)
    if not STATE.get("_props_reloaded"):                 # 這個 Blender 早先連結過素材庫的話，複製會沿用記憶體裡的舊內容（場景端改版後位置不對）→ 先重讀；
        for lib in bpy.data.libraries:                    # 每個工作場景只重讀一次（第二次會把前一個場景剛複製進來的物件清單弄壞）
            if lib.filepath.replace("\\", "/").endswith("props-zepeto/zepeto_props.blend"):
                lib.reload()
        STATE["_props_reloaded"] = True
    g = props_api(); col = g["append_prop"](key, parent=Z.studio_col())
    off = Vector(offset)
    for o in col.all_objects:
        if o.parent is None:
            o.location = o.location + off
    for o in col.all_objects:
        if o is not None and o.name.startswith(tuple(hide)):
            o.hide_render = o.hide_viewport = True
    return {o.name: o for o in col.all_objects if o is not None}


def end_state(path, t_end, extra=None, handles=1.0):
    """這一鏡最後一格（鏡內 t_end）的新郎骨盆、面向；下一鏡從這裡接（走路相位由各鏡自己算）"""
    i = int(round((t_end + handles) * FPS)); R, h = STATE["poses"][min(i, len(STATE["poses"]) - 1)]
    d = dict(hips=list(h), fw=list(hips_fw(R)), t_end=t_end)
    d.update(extra or {})
    json.dump(d, open(path, "w")); return d


def load_end(path):
    return json.load(open(path))
