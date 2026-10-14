# ⑦ 叉子量測（2026-10-11，第 3 關回饋「新郎拿著食物插進新娘的頭裡面」）：
#   正式場景的叉子掛在新郎左手骨頭上（shots_v2 的 held_fork2 × S["fork_roll"]），量「叉尖、牛排塊相對手骨頭」的固定位置，
#   給 mx_scene_07 的餵食微調用（讓牛排塊到嘴前，不是用猜的 20 cm）。
#   "$BL" -b couple.blend -P prod_cli.py -- --run mx_fork_probe [FWHO=bride FSIDE=R]   → 印 FORK_LOCAL {...}
import bpy, json
from mathutils import Vector, Matrix

MODE = "setup"
use("run_prod")
S = SHOTS["v2_07"]
S["build"](); stage(S["set"], cast=True)
S07 = V2S["07"]
# 2026-10-11 第 3 關第 3 輪（⑦a 新娘自己吃）：FWHO=bride FSIDE=R 量新娘右手（動作庫 held_prop("fork","R") 的預設握法）
WHO = str(globals().get("FWHO", "groom")); SIDE = str(globals().get("FSIDE", "L"))   # 參數名避開 run_prod 已有的 WHO
NS = GR if WHO == "groom" else B
A = NS["ARM"]
bpy.context.view_layer.update()
Mh = A.matrix_world @ A.pose.bones[f"J_Bip_{SIDE}_Hand"].matrix
Mf = (held_fork2() if (WHO, SIDE) == ("groom", "L") else NS["held_prop"]("fork", SIDE)) @ S07["fork_roll"]
Mi = Mh.inverted()
tip = Mi @ (Mf @ Vector((0, 0, 0.115)))
grip = Mi @ (Mf @ Vector((0, 0, 0.0)))
bite = Mi @ (Mf @ S07["bite_rel"]).translation
ax = (Mi.to_3x3() @ (Mf.to_3x3() @ Vector((0, 0, 1)))).normalized()
res = dict(tip=[round(x, 4) for x in tip], grip=[round(x, 4) for x in grip], bite=[round(x, 4) for x in bite], axis=[round(x, 4) for x in ax],
           hand_len=round((A.pose.bones[f"J_Bip_{SIDE}_Middle1"].head - A.pose.bones[f"J_Bip_{SIDE}_Hand"].head).length, 4), who=WHO, side=SIDE)
print("FORK_LOCAL", json.dumps(res), flush=True)
