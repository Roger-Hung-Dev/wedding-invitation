# ⑦ 道具量測（2026-10-11，第 3 關第 2 輪回饋「⑦ 太多動作不是正常人類的動作」→ 重做時要知道道具的真實位置與握法）：
#   正式場景的叉子、酒杯在 shots_v2 是掛在手骨頭上（held_fork2、held_prop("glass")），開場的擺放位置（fork_lie、glass_g／glass_b、bite_at）
#   是照舊動作算的。印出這些位置，以及舊版（使用者看過、覺得比較像人）拿杯、舉杯、喝時手骨頭的方向，給 mx_scene_07 用。
#   "$BL" -b couple.blend -P prod_cli.py -- --run mx_prop_probe   → 印 PROP07 {...}
import bpy, json
from mathutils import Vector, Matrix

MODE = "setup"
use("run_prod")
S = SHOTS["v2_07"]
S["build"](); stage(S["set"], cast=True)
S07 = V2S["07"]
r = lambda v: [round(x, 4) for x in v]
out = dict(fork_lie=dict(p=r(S07["fork_lie"].translation), z=r(S07["fork_lie"].col[2].to_3d()), y=r(S07["fork_lie"].col[1].to_3d())),
           bite_at=r(S07["bite_at"]), glass_g=r(S07["glass_g"]), glass_b=r(S07["glass_b"]),
           fork_put=dict(p=r(S07["fork_put"].translation), z=r(S07["fork_put"].col[2].to_3d())),
           t=dict(fork=S07["t_fork"], spear=S07["t_spear"], put=S07["t_put"], glass_g=S07["t_glass_g"], glass_b=S07["t_glass_b"]))
# 舊版各時間點：手骨頭三軸、前臂方向、握點、杯子軸（世界座標）
for who, ns, side, actor in (("groom", GR, "L", S07["AG"]), ("bride", B, "R", S07["AB"])):
    A = ns["ARM"]; rows = []
    for t in (5.6, 6.0, 6.7, 7.6, 9.5, 10.3):
        actor.pose(t); bpy.context.view_layer.update()
        pb = A.pose.bones
        M = A.matrix_world @ pb[f"J_Bip_{side}_Hand"].matrix; R3 = M.to_3x3().normalized()
        fa = (A.matrix_world @ pb[f"J_Bip_{side}_Hand"].head - A.matrix_world @ pb[f"J_Bip_{side}_LowerArm"].head).normalized()
        el = A.matrix_world @ pb[f"J_Bip_{side}_LowerArm"].head
        sh = A.matrix_world @ pb[f"J_Bip_{side}_UpperArm"].head
        G = ns["held_prop"]("glass", side)
        rows.append(dict(t=t, X=r(R3.col[0]), Y=r(R3.col[1]), Z=r(R3.col[2]), forearm=r(fa), elbow=r(el), shoulder=r(sh),
                         grip=r(G.translation), axis=r(G.col[2].to_3d()), hips=r(A.matrix_world @ pb["J_Bip_C_Hips"].head)))
    out[who] = rows
print("PROP07", json.dumps(out), flush=True)
