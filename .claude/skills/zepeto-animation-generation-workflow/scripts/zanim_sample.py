# ZEPETO 動畫共用：樣張（2026-10-12 由 t_sample 抽出）。
# 每一鏡定案時：把每格姿勢、道具（位置、顯示／隱藏、透明度）、鏡頭烤成關鍵影格，另存一份獨立的 .blend，
# 再登記進樣張總表 sample/samples.json（render-settings mod 的「試渲鏡頭」「試渲畫面」讀這份；確認頁的短片也用它渲）。
# 不是存回 body.blend，也不是存 GUI 的檔。背景渲：sample_render.py。
import os, json, time
import bpy
from mathutils import Vector
import zanim as Z
STATE = Z.STATE
ROOT = Z.WORK + "/sample"
MANIFEST = ROOT + "/samples.json"
FPS = 30


def _put(act, owner, path, idx, vals, interp="LINEAR"):
    fc = act.fcurve_ensure_for_datablock(owner, path, index=idx)
    fc.keyframe_points.clear(); fc.keyframe_points.add(len(vals))
    co = []
    for i, v in enumerate(vals):
        co += [i + 1, float(v)]
    fc.keyframe_points.foreach_set("co", co)
    for kp in fc.keyframe_points:
        kp.interpolation = interp
    fc.update()


def _action(owner, name):
    ad = owner.animation_data_create()
    act = bpy.data.actions.get(name) or bpy.data.actions.new(name)
    ad.action = act
    return act


def bake(objects=(), alpha=(), camera_fn=None, tag="SAMPLE"):
    """逐格（Z.pose_at，含各鏡的 POSE_HOOKS）記下：骨架 J_Bip_* 的 rotation_quaternion／location、objects 的 matrix_world＋hide_render、
    alpha 的 (物件, 材質節點, 輸入名) 透明度、camera_fn(i)→(位置, 看向的點) 的鏡頭；全部寫成關鍵影格（第 1 格＝0 秒）。
    camera_fn 每格呼叫完會再跑 CAM_HOOKS（例：星星轉向鏡頭）"""
    arm = STATE["arm"]; n = len(STATE["poses"])
    arms = [arm] + [a["state"]["arm"] for k, a in STATE.get("cast", {}).items() if k != "_main"]   # zanim_cast 附加的角色一起烤
    names = [pb.name for pb in arm.pose.bones if pb.name.startswith("J_Bip_")]   # 臉部控制骨頭（驅動器）不碰
    rot = {(a.name, k): [] for a in arms for k in names}; loc = {(a.name, k): [] for a in arms for k in names}
    om = {o.name: [] for o in objects}; oh = {o.name: [] for o in objects}
    av = {(o.name, nd.name, inp): [] for o, nd, inp in alpha}
    cam = []
    for i in range(n):
        Z.pose_at(i / 30)
        if camera_fn:
            l, t = camera_fn(i); cam.append((l, t))
            for hk in Z.CAM_HOOKS:
                hk(l)
        for a in arms:
            for k in names:
                pb = a.pose.bones[k]
                rot[(a.name, k)].append(tuple(pb.rotation_quaternion)); loc[(a.name, k)].append(tuple(pb.location))
        for o in objects:
            om[o.name].append(o.matrix_world.copy()); oh[o.name].append(1.0 if o.hide_render else 0.0)
        for o, nd, inp in alpha:
            av[(o.name, nd.name, inp)].append(nd.inputs[inp].default_value)
    for ai, a in enumerate(arms):
        act = _action(a, tag + "_Body" + ("" if ai == 0 else "_" + a.name))
        for k in names:
            for j in range(4):
                _put(act, a, f'pose.bones["{k}"].rotation_quaternion', j, [q[j] for q in rot[(a.name, k)]])
            if any(Vector(l).length > 1e-6 for l in loc[(a.name, k)]):
                for j in range(3):
                    _put(act, a, f'pose.bones["{k}"].location', j, [l[j] for l in loc[(a.name, k)]])
    for o in objects:
        o.rotation_mode = "QUATERNION"; o.parent = None
        a = _action(o, tag + "_" + o.name)
        parts = [m.decompose() for m in om[o.name]]
        for j in range(3):
            _put(a, o, "location", j, [p[0][j] for p in parts]); _put(a, o, "scale", j, [p[2][j] for p in parts])
        for j in range(4):
            _put(a, o, "rotation_quaternion", j, [p[1][j] for p in parts])
        if len(set(oh[o.name])) > 1:
            _put(a, o, "hide_render", 0, oh[o.name], "CONSTANT")
    for (on, ndn, inp), vals in av.items():
        mat = bpy.data.objects[on].active_material
        a = _action(mat.node_tree, tag + "_" + on + "_alpha")
        _put(a, mat.node_tree, f'nodes["{ndn}"].inputs["{inp}"].default_value', 0, vals)
    sc = STATE["sc"]
    if camera_fn:
        c = sc.camera; c.rotation_mode = "QUATERNION"
        a = _action(c, tag + "_Cam")
        qs = [(Vector(t) - Vector(l)).to_track_quat("-Z", "Y") for l, t in cam]
        for k in range(1, len(qs)):                     # 四元數同半球，內插才不會繞遠路
            if qs[k].dot(qs[k - 1]) < 0:
                qs[k].negate()
        for j in range(3):
            _put(a, c, "location", j, [l[j] for l, _t in cam])
        for j in range(4):
            _put(a, c, "rotation_quaternion", j, [q[j] for q in qs])
        sc["sample_focus_dist"] = sum((Vector(t) - Vector(l)).length for l, t in cam) / len(cam)
    sc.render.fps = FPS; sc.render.fps_base = 1.0
    sc.frame_start, sc.frame_end = 1, n
    return dict(frames=n, bones=len(names), actors=len(arms), objects=len(objects), alpha=len(alpha))


def new_camera(name="SAMPLE_Cam", lens=35.0):
    sc = STATE["sc"]
    cam = bpy.data.objects.get(name)
    if cam is None:
        cam = bpy.data.objects.new(name, bpy.data.cameras.new(name)); sc.collection.objects.link(cam)
    cam.animation_data_clear()
    cam.data.lens = lens; cam.data.dof.focus_object = None
    sc.camera = cam
    return cam


def follow_camera(offset=(0.0, -3.0, 0.25), aim_z=0.70, smooth=15, partner=None):
    """側面跟拍：鏡頭水平跟著骨盆走（前後 smooth 格平均，不晃）。回傳 camera_fn
    partner(i)→(x, y)：同框的另一個人（例：新娘替身）的位置；有給就跟兩人中點（2026-10-12 導演端第 1 輪：全片構圖對準兩人中點）"""
    arm = STATE["arm"]; n = len(STATE["poses"]); hp = []
    for i in range(n):                                  # 實際擺出來的骨盆位置（原始資料的 hips 和擺出來的不同座標）
        Z.pose_at(i / 30); p = arm.matrix_world @ arm.pose.bones["J_Bip_C_Hips"].head
        if partner is not None:
            q = partner(i)
            if q is not None:
                p = Vector(((p.x + q[0]) / 2, (p.y + q[1]) / 2, p.z))
        hp.append(p)
    sm = [sum((hp[j] for j in range(max(0, i - smooth), min(n, i + smooth + 1))), Vector()) / (min(n, i + smooth + 1) - max(0, i - smooth)) for i in range(n)]
    return lambda i: (Vector((sm[i].x, sm[i].y, aim_z)) + Vector(offset), Vector((sm[i].x, sm[i].y, aim_z)))


def save(sid):
    sc = STATE["sc"]
    path = f"{ROOT}/{sid}.blend"
    os.makedirs(ROOT, exist_ok=True)
    sc.frame_set(1)
    bpy.data.libraries.write(path, {sc}, path_remap="ABSOLUTE", compress=True)
    return path


def register(sid, label, shot, blend, frames, note="", kind="shot"):
    """登記進樣張總表；同一個 id 再登記就覆蓋。frames：[(秒, 說明)]；動得快的那一格說明裡寫「動得快」（試渲動態模糊用）"""
    m = {"schema": 1, "samples": []}
    if os.path.exists(MANIFEST):
        m = json.load(open(MANIFEST, encoding="utf8"))
    m["samples"] = [s for s in m["samples"] if s["id"] != sid]
    m["samples"].append(dict(id=sid, label=label, shot=shot, kind=kind, blend=blend, fps=FPS,
                             frames=[dict(t=t, label=l) for t, l in frames], note=note,
                             updated=time.strftime("%Y-%m-%dT%H:%M:%S")))
    m["samples"].sort(key=lambda s: (s["kind"] != "shot", s["shot"] or "", s["id"]))
    json.dump(m, open(MANIFEST, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    return dict(id=sid, n=len(m["samples"]))


def _bodies():
    """閘門要點名場上所有身體（zanim_cast 附加的也算）"""
    out = [STATE.get("body", "groom")]
    for k, a in STATE.get("cast", {}).items():
        b = a["state"].get("body")
        if k != "_main" and b and b not in out:
            out.append(b)
    return ",".join(out)


def render_clip(sid, t0, t1, out_mp4, size=(960, 540), samples=16):
    """用背景 Blender 從樣張渲一段低畫質短片（確認頁用）。回傳指令（給 Bash 跑，run_in_background）"""
    jobs = f"{ROOT}/_clip_{sid}.json"
    json.dump({"out_dir": os.path.dirname(out_mp4), "jobs": [{"name": os.path.splitext(os.path.basename(out_mp4))[0],
               "clip": [t0, t1], "set": {"resolution": list(size), "samples": samples}}]}, open(jobs, "w", encoding="utf8"))
    bl = r"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"
    return f'"{bl}" -b "{ROOT}/{sid}.blend" -P "{os.path.dirname(os.path.abspath(__file__))}/sample_render.py" -- "{jobs}" BODY={_bodies()}'
