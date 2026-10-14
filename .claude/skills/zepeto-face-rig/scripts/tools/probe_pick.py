# 從身體端 neck_probe.py 的某一張近照，指定像素打射線：打到哪個物件、位置、那個面的骨頭權重（哪個部位）。不存檔。
# 用法：blender -b body.blend -P probe_pick.py -- ANGLE=180 PIX=56,448;58,440 [UP=0] [DIST=0.55]
#   ANGLE：0＝front、45＝front_r、90＝side_r、−90＝side_l、180＝back（同 neck_probe.py 的 shot）；像素以 640×640 的原圖為準
#   執行時讀身體端 neck_probe.py 的設定段（擺待機姿勢、鏡頭），只截到開拍之前——那支改了這支會跟著變
#   2026-10-14：背面頭髮上一小塊膚色，查出是 J_Bip_L_UpperArm（手臂放下時上臂從長髮後面頂出來），不是頭髮破洞
import bpy, sys, os, math
from mathutils import Vector
NP = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..",
                                   "zepeto-body-generation-workflow", "scripts", "neck_probe.py"))
A0 = dict(x.split("=", 1) for x in sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else {}
src = open(NP, encoding="utf-8").read()
setup = src[:src.index("\npose()\n")]          # 只要擺姿勢、鏡頭的設定段，不拍照
sys.argv = sys.argv[:sys.argv.index("--") + 1] + ["OUT=" + os.environ.get("TEMP", ".")] + [k + "=" + v for k, v in A0.items() if k == "DIST"]
g = {"__name__": "__probe__", "__file__": NP}
exec(compile(setup, NP, "exec"), g)
g["pose"]()
sc, arm, cam, DIST = g["sc"], g["arm"], g["cam"], g["DIST"]
ang = math.radians(float(A0.get("ANGLE", "180"))); up = float(A0.get("UP", "0"))
hb = arm.pose.bones["J_Bip_C_Head"]
c = arm.matrix_world @ hb.head + Vector((0, 0, -0.035))
cam.location = c + Vector((-math.sin(ang) * DIST, -math.cos(ang) * DIST, up))
cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
mw = cam.matrix_world
tr, br, bl, tl = [mw @ v for v in cam.data.view_frame(scene=sc)]
RES = sc.render.resolution_x
for s in A0.get("PIX", "320,320").split(";"):
    px, py = (int(x) for x in s.split(","))
    u, v = px / RES, 1 - py / RES
    lo = bl + (br - bl) * u; hi = tl + (tr - tl) * u
    d = ((lo + (hi - lo) * v) - mw.translation).normalized()
    hit, loc, nor, idx, ob, M = sc.ray_cast(dg, mw.translation, d)
    info = ""
    if hit and ob.type == 'MESH' and ob.vertex_groups:
        me = ob.data
        if idx < len(me.polygons):
            acc = {}
            for vi in me.polygons[idx].vertices:
                for gg in me.vertices[vi].groups:
                    nm = ob.vertex_groups[gg.group].name; acc[nm] = acc.get(nm, 0) + gg.weight
            info = "權重 " + str(sorted(((k, round(w_, 2)) for k, w_ in acc.items()), key=lambda x: -x[1])[:3])
    print("[pick] (%d,%d) → %s %s %s" % (px, py, ob.name if hit else "（沒打到）", tuple(round(x, 3) for x in loc) if hit else "", info))
