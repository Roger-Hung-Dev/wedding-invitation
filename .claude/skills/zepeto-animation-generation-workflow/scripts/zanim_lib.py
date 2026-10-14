# ZEPETO 動畫共用工具（2026-10-12 由 B1→B2 的 b12_lib 搬來，內容沒改）：找骨架、自動量角色、讀 Mixamo、鞋底取樣點、滑步／腳底量測。
# 換角色時不寫死任何尺寸：全部從輸入 .blend 的骨架與網格量出來。
import bpy, os, sys, math
from mathutils import Vector, Quaternion, Matrix

ML = r"D:\SideProject\wedding-invitation\.claude\skills\blender-motion-library\scripts"
if ML not in sys.path:
    sys.path.insert(0, ML)
import mixamo_retarget as mr

RAW = r"D:\render-work\mixamo\raw"
FPS = 30
_CL = {}
_SOLE = {}


def find_arm(scene=None):
    objs = (scene or bpy.context.scene).objects
    return next(o for o in objs if o.type == "ARMATURE" and "J_Bip_C_Hips" in o.data.bones)


def body_mesh(arm):
    """綁在骨架上、頂點最多的網格＝身體"""
    ms = [o for o in bpy.data.objects if o.type == "MESH" and any(m.type == "ARMATURE" and m.object == arm for m in o.modifiers)]
    return max(ms, key=lambda o: len(o.data.vertices))


def head_mesh(arm):
    """頭：骨架底下（含 Face_Rig 子物件）名稱以 Head 開頭的網格"""
    for o in arm.children_recursive:
        if o.type == "MESH" and o.name.split(".")[0] == "Head":
            return o
    return None


def clip(tgt, name):
    if name not in _CL:
        _CL[name] = mr.retarget(mr.read_fbx(os.path.join(RAW, name + ".fbx")), tgt)
    return _CL[name]


def _bbox_world(o):
    vl = (o.users_scene[0] if o.users_scene else bpy.context.scene).view_layers[0]
    vl.update(); dg = vl.depsgraph
    oe = o.evaluated_get(dg); me = oe.to_mesh()
    mw = o.matrix_world
    P = [mw @ v.co for v in me.vertices]
    oe.to_mesh_clear()
    lo = Vector((min(p.x for p in P), min(p.y for p in P), min(p.z for p in P)))
    hi = Vector((max(p.x for p in P), max(p.y for p in P), max(p.z for p in P)))
    return lo, hi


def sole_points(arm, body=None):
    """鞋底取樣點：rest 時離地 ≤ 1.2 cm 的身體頂點，記成所屬腳骨（Foot／ToeBase）的局部座標"""
    if arm.name in _SOLE:
        return _SOLE[arm.name]
    body = body or body_mesh(arm)
    names = {g.index: g.name for g in body.vertex_groups}
    zmin = min(v.co.z for v in body.data.vertices)
    pts = []
    for v in body.data.vertices:
        if v.co.z > zmin + 0.012 or not v.groups:
            continue
        g = max(v.groups, key=lambda g: g.weight); b = names[g.group]
        if not (b.endswith("Foot") or b.endswith("ToeBase")):
            continue
        pts.append((b, arm.data.bones[b].matrix_local.inverted() @ (body.matrix_world @ v.co)))
    _SOLE[arm.name] = pts[::2]
    return _SOLE[arm.name]


def measure(arm, tgt):
    """自動量測（換角色重跑一次就好）：髖高、腿長、腳長、腳底高度、肩寬、頭寬、手臂長…（m）"""
    B = arm.data.bones
    h = lambda n: B[n].head_local
    body = body_mesh(arm)
    lo, hi = _bbox_world(body)
    M = dict(height_body_top=round(hi.z, 4), sole_z=round(lo.z, 4))
    hd = head_mesh(arm)
    if hd:
        hlo, hhi = _bbox_world(hd)
        M.update(head_w=round(hhi.x - hlo.x, 4), head_d=round(hhi.y - hlo.y, 4), head_top=round(hhi.z, 4), head_bottom=round(hlo.z, 4))
    M["hip_h"] = round(tgt.hip_h, 4)
    thigh = (h("J_Bip_L_LowerLeg") - h("J_Bip_L_UpperLeg")).length
    shin = (h("J_Bip_L_Foot") - h("J_Bip_L_LowerLeg")).length
    M.update(thigh=round(thigh, 4), shin=round(shin, 4), ankle_h=round(h("J_Bip_L_Foot").z - lo.z, 4),
             leg=round(tgt.hip_h - lo.z, 4))
    sp = sole_points(arm, body)
    ys = [(B[b].matrix_local @ co).y for b, co in sp if "_L_" in b]
    M["foot_len"] = round(max(ys) - min(ys), 4) if ys else None
    M["sole_pts"] = len(sp)
    M["shoulder_joint_w"] = round((h("J_Bip_L_UpperArm") - h("J_Bip_R_UpperArm")).length, 4)
    # 肩外緣寬：肩關節高度 ±2 cm 的身體頂點、排除手臂（|x| 超過上臂起點 6 cm 的不算）
    sz = h("J_Bip_L_UpperArm").z; ax = h("J_Bip_L_UpperArm").x
    xs = [abs((body.matrix_world @ v.co).x) for v in body.data.vertices if abs(v.co.z - sz) < 0.02 and abs(v.co.x) < ax + 0.03]
    M["shoulder_outer_w"] = round(2 * max(xs), 4) if xs else None
    M["upper_arm"] = round((h("J_Bip_L_LowerArm") - h("J_Bip_L_UpperArm")).length, 4)
    M["fore_arm"] = round((h("J_Bip_L_Hand") - h("J_Bip_L_LowerArm")).length, 4)
    M["head_pivot_z"] = round(h("J_Bip_C_Head").z, 4)
    return M


# ── 每格量測 ──
def soles(tgt, R, hips, pts):
    """用骨架 FK（不碰網格）算鞋底點的世界座標"""
    Hd = tgt.fk(R, hips)
    out = {"L": [], "R": []}
    for b, co in pts:
        Mb = Matrix.Translation(Hd[b]) @ R[b].to_matrix().to_4x4()
        out["L" if "_L_" in b else "R"].append(Mb @ co)
    return out


def contact_stats(seq_poses, tgt, pts, z_on=0.005):
    """seq_poses：每格 (R, hips) → 每格每腳：最低點高度、著地點平均水平位移（mm/格）"""
    prev = None; rows = []
    for i, (R, hp) in enumerate(seq_poses):
        cur = soles(tgt, R, hp, pts)
        row = dict(i=i, lowL=min(p.z for p in cur["L"]), lowR=min(p.z for p in cur["R"]))
        for s in "LR":
            row["slide" + s] = None
            if prev is not None:
                idx = [k for k, (a, b) in enumerate(zip(prev[s], cur[s])) if a.z <= z_on and b.z <= z_on]
                if len(idx) >= 3:
                    dx = sum(cur[s][k].x - prev[s][k].x for k in idx) / len(idx)
                    dy = sum(cur[s][k].y - prev[s][k].y for k in idx) / len(idx)
                    row["slide" + s] = math.hypot(dx, dy) * 1000
        rows.append(row); prev = cur
    return rows
