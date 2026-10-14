# 接口環整合驗收：開 body.blend（只讀不存），量頭環與身體最上圈的
#   ① 距離（靜止、轉頭 35°、低頭 25°）② 法線夾角 ③ 張嘴（jawOpen＝1）時頭環動多少。結果印 RINGCHECK {json}
# 用法：blender -b <build>/<人>.work/body.blend -P ring_check.py
# 2026-10-14 接口環（方案 A）整合測試加的。
import bpy, sys, json, math
from mathutils import Vector, Quaternion
sys.path.insert(0, r"D:\SideProject\wedding-invitation\.claude\skills\blender-motion-library\scripts")
import mixamo_retarget as mr
O = bpy.data.objects
hd = O["Head"]; body = O["Body"]; arm = O["Body_Armature"]; tgt = mr.Target(arm)


def ev_mesh(o):
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); return e, e.to_mesh()


def ring_ids(me, limit=None):
    att = me.attributes.get("neck_ring"); out = {}
    n = len(me.vertices) if limit is None else min(limit, len(me.vertices))
    for i in range(n):
        k = att.data[i].value
        if k > 0 and k not in out:
            out[k] = i
    return out


z_ring = float(hd["neck_ring_z"])
M = sum(1 for v in hd.data.vertices if v.co.z >= z_ring - 1e-5)


def snapshot():
    bpy.context.view_layer.update()
    eh, mh = ev_mesh(hd); ih = ring_ids(mh, M)
    hn = {}
    for li, l in enumerate(mh.loops):
        hn.setdefault(l.vertex_index, []).append(Vector(mh.corner_normals[li].vector))
    hp = {k: hd.matrix_world @ mh.vertices[i].co for k, i in ih.items()}
    hnn = {k: (hd.matrix_world.to_3x3() @ sum(hn[i], Vector())).normalized() for k, i in ih.items()}
    eh.to_mesh_clear()
    eb, mb = ev_mesh(body); ib = ring_ids(mb)
    bn = {}
    for li, l in enumerate(mb.loops):
        bn.setdefault(l.vertex_index, []).append(Vector(mb.corner_normals[li].vector))
    bp = {k: body.matrix_world @ mb.vertices[i].co for k, i in ib.items()}
    bnn = {k: (body.matrix_world.to_3x3() @ sum(bn[i], Vector())).normalized() for k, i in ib.items()}
    eb.to_mesh_clear()
    return hp, hnn, bp, bnn


def gaps(hp, bp):
    return max((hp[k] - bp[k]).length for k in range(1, 49)) * 1000


res = {}
for pb in arm.pose.bones:
    pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = (1, 0, 0, 0)
hp, hnn, bp, bnn = snapshot()
res["rest_gap_mm"] = round(gaps(hp, bp), 3)
# 法線夾角只看頭在環上的法線和身體在環上的法線（頭的法線是 seam_normals 抄身體的）
res["normal_diff_max_deg"] = round(max(math.degrees(hnn[k].angle(bnn[k])) for k in range(1, 49)), 2)
res["normal_diff_mean_deg"] = round(sum(math.degrees(hnn[k].angle(bnn[k])) for k in range(1, 49)) / 48, 2)
rest_h = hp
# 轉頭、低頭：只轉頭骨和脖子骨（和 neck_probe 一樣分給脖子 40%、頭 60%）
B = arm.data.bones
R0 = {n: (arm.matrix_world.to_quaternion() @ B[n].matrix_local.to_quaternion()) for n in tgt.keys}
h0 = tgt.rest_h["J_Bip_C_Hips"].copy()
for name, axis, deg in (("turn35", (0, 0, 1), 35), ("down25", (1, 0, 0), 25), ("up25", (1, 0, 0), -25)):
    R = dict(R0)
    for b, w in (("J_Bip_C_Neck", 0.4), ("J_Bip_C_Head", 0.6)):
        R[b] = Quaternion(axis, math.radians(deg * w)) @ R[b]
    mr.apply_pose(arm, tgt, R, h0)
    hp2, _, bp2, _ = snapshot()
    res[f"{name}_gap_mm"] = round(gaps(hp2, bp2), 3)
for pb in arm.pose.bones:
    pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
# 張嘴：關掉表情驅動器、jawOpen＝1
ad = hd.data.shape_keys.animation_data
if ad:
    for fc in ad.drivers:
        fc.mute = True
kb = hd.data.shape_keys.key_blocks
kb["jawOpen"].value = 1.0
hp3, _, bp3, _ = snapshot()
res["jawopen_ring_move_mm"] = round(max((hp3[k] - rest_h[k]).length for k in range(1, 49)) * 1000, 3)
res["jawopen_gap_mm"] = round(gaps(hp3, bp3), 3)
print("RINGCHECK", json.dumps(res, ensure_ascii=False))
