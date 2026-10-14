# 接身體後拉遠拍側面（右側、右後斜、左側），鏡頭對準脖子、距離 0.9 m。不存檔。
# 用法：blender -b body.blend -P shot_body_side.py -- <輸出檔名前綴>
#   ⚠️ 長髮避開身體一定要看這組：近照只看得到肩膀折角，拉遠才看得到整片頭髮往後張成披風（2026-10-14）
import bpy, sys
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; cam = sc.camera; sc.render.resolution_x = sc.render.resolution_y = 500
arm = bpy.data.objects["Body_Armature"]; hp = arm.matrix_world @ arm.pose.bones["J_Bip_C_Neck"].head
for i, d in enumerate([Vector((1, 0, 0)), Vector((0.7, 0.7, 0)), Vector((-1, 0, 0))]):
    cam.location = hp + d * 0.9 + Vector((0, 0, 0.0)); cam.rotation_euler = (hp - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = out + "_%d.png" % i; bpy.ops.render.render(write_still=True)
