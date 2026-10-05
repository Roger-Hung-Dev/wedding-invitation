# 裙擺擺動：自製的 Skirt_Sway 骨頭（腰部固定、下擺跟著身體慢半拍，彈簧＋阻尼）。
# setup_skirt_bone() 只需執行一次（build_costume.py 會做）；use("skirt_phys") 會建立全域的 skirt 物件。
import bpy, math
from mathutils import Vector, Matrix, Quaternion


def setup_skirt_bone(arm, waist_z=0.985):
    if "Skirt_Sway" in arm.data.bones:
        return
    bpy.context.view_layer.objects.active = arm
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    arm.select_set(True)
    with bpy.context.temp_override(active_object=arm, object=arm, selected_objects=[arm]):
        bpy.ops.object.mode_set(mode="EDIT")
        eb = arm.data.edit_bones.new("Skirt_Sway")
        eb.head = (0, 0, waist_z); eb.tail = (0, 0, waist_z - 0.3)
        eb.parent = arm.data.edit_bones["J_Bip_C_Hips"]
        bpy.ops.object.mode_set(mode="OBJECT")


class SkirtSpring:
    def __init__(self, arm, length=0.95, k=0.035, drag=0.07, max_deg=16, lean_gain=3.0):
        self.arm, self.L, self.k, self.drag, self.max, self.lean_gain = arm, length, k, drag, math.radians(max_deg), lean_gain
        self.reset()

    def reset(self):
        self.p = self.q = None
        self.extra_flare = 0.0          # 轉圈時由情境設定，把裙擺撐開

    def step(self):
        A = self.arm; pb = A.pose.bones["Skirt_Sway"]
        bpy.context.view_layer.update()
        mw = A.matrix_world @ pb.parent.matrix @ (pb.parent.bone.matrix_local.inverted() @ pb.bone.matrix_local)
        head = mw.to_translation(); rest = (mw.to_quaternion() @ Vector((0, 1, 0))).normalized()
        target = head + rest * self.L
        chest = A.matrix_world @ A.pose.bones["J_Bip_C_UpperChest"].head
        hips = A.matrix_world @ A.pose.bones["J_Bip_C_Hips"].head
        target -= Vector((chest.x - hips.x, chest.y - hips.y, 0.0)) * self.lean_gain
        if self.p is None:
            self.p = target.copy(); self.q = target.copy()
        nxt = self.p + (self.p - self.q) * (1 - self.drag) + (target - self.p) * self.k
        d = nxt - head; ln = max(1e-6, d.length); dn = d / ln
        if rest.angle(dn) > self.max:
            axis = rest.cross(dn).normalized(); dn = (Quaternion(axis, self.max) @ rest).normalized()
        stretch = max(0.88, min(1.10, ln / self.L))
        nxt = head + dn * (stretch * self.L)
        self.q, self.p = self.p, nxt
        inv = A.matrix_world.to_quaternion().inverted()
        rot = (inv @ rest).rotation_difference(inv @ dn)
        pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1); pb.location = (0, 0, 0)
        bpy.context.view_layer.update()
        m = pb.matrix.copy(); h = m.to_translation()
        pb.matrix = Matrix.Translation(h) @ rot.to_matrix().to_4x4() @ Matrix.Translation(-h) @ m
        pb.location = (0, 0, 0); pb.rotation_quaternion.normalize()
        flare = 1 + (1 - stretch) * 1.2 + self.extra_flare
        pb.scale = (flare, stretch, flare)


skirt = SkirtSpring(bpy.data.objects[f"{WHO}_Armature"])
