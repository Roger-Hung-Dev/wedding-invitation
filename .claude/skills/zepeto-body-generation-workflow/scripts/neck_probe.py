# 脖子接口近照診斷：開 body.blend（只讀不存），拍頭和身體接縫的多角度近照，含低頭、抬頭、轉頭。
# 用法：blender -b <build>/<人>/body.blend -P neck_probe.py -- OUT=<資料夾> [DIST=0.55]
# ⚠️ 直接開原檔（不存檔就不會動到）；複製到別的資料夾再開，頭的貼圖相對路徑會斷（耳環變洋紅色）
# 2026-10-12 使用者看新娘禮服說「頭和身體的銜接處好像沒做好」→ 加這支，專看接縫：顏色、縫線、形狀斷層。
import bpy, sys, os, math
from mathutils import Vector, Quaternion
sys.path.insert(0, r"D:\SideProject\wedding-invitation\.claude\skills\blender-motion-library\scripts")
import mixamo_retarget as mr
A = dict(a.split("=", 1) for a in sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else {}
OUT = A["OUT"]; os.makedirs(OUT, exist_ok=True)
DIST = float(A.get("DIST", "0.55"))
sc = bpy.context.scene; O = bpy.data.objects
arm = O["Body_Armature"]; cam = O["Camera"]; tgt = mr.Target(arm)
clip = mr.retarget(mr.read_fbx(r"D:\render-work\mixamo\raw\female_idle.fbx"), tgt)
R0, h0 = dict(clip["R"][0]), clip["hips"][0].copy(); h0.x = h0.y = 0
cam.data.type = "PERSP"; cam.data.lens = 50
sc.render.resolution_x = sc.render.resolution_y = 640


def pose(pitch=0.0, yaw=0.0):
    R = dict(R0)
    for b, w in (("J_Bip_C_Neck", 0.4), ("J_Bip_C_Head", 0.6)):        # 低頭／抬頭、轉頭分給脖子和頭
        q = Quaternion((1, 0, 0), math.radians(pitch * w)) @ Quaternion((0, 0, 1), math.radians(yaw * w))
        R[b] = q @ R[b]
    mr.apply_pose(arm, tgt, R, h0); bpy.context.view_layer.update()


def shot(name, angle, up=0.0):
    hb = arm.pose.bones["J_Bip_C_Head"]
    c = arm.matrix_world @ hb.head + Vector((0, 0, -0.035))   # 對準脖子接口（頭骨根部往下 3.5 cm）
    r = math.radians(angle)
    cam.location = c + Vector((-math.sin(r) * DIST, -math.cos(r) * DIST, up))
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(OUT, name + ".png"); bpy.ops.render.render(write_still=True)


pose()
for a, n in ((0, "front"), (45, "front_r"), (90, "side_r"), (-90, "side_l"), (180, "back")):
    shot("neck_" + n, a)
shot("neck_below", 0, up=-0.18)                                   # 從下往上看下巴底
pose(pitch=25)                                                    # 低頭（+x 轉：臉往下）
shot("neck_down_front", 0); shot("neck_down_side", 90)
pose(pitch=-25)                                                   # 抬頭
shot("neck_up_front", 0); shot("neck_up_side", 90)
pose(yaw=35)
shot("neck_turn", 0)
print("NECK_PROBE done", OUT)
