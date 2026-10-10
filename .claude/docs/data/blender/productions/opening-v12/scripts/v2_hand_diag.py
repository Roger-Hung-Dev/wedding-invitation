# 手腕診斷（2026-10-09）：mocap_action 套出來的手腕彎曲角（前臂骨頭方向 vs 手骨方向），逐格；也量 CMU 原始資料的手腕角
#   "$BL" -b couple.blend -P prod_cli.py -- --run v2_hand_diag
import bpy, math, os, json
from mathutils import Vector
MODE = "setup"
use("run_prod")
lib = os.path.join(LIB, "mocap")
out = {}
for who, ns in (("groom", GR), ("bride", B)):
    if "mocap_action" not in ns:
        ns["use"]("mocap_retarget")
    for name, fr, fps in (("35_01", (60, 324), 120.0), ("16_33", (2, 236), 120.0), ("143_25", (255, 385), 60.0), ("82_08", (900, 1250), 120.0), ("16_57", (2, 300), 120.0)):
        if fr is None:
            continue
        F = ns["mocap_action"](os.path.join(lib, name + ".bvh"), frames=fr, heading=90.0 if name != "143_25" else None, origin=(0, 0),
                               foot_fix=False, fix_arm_offset=False, src_fps=fps)
        rig = F.rig; rq = rig.rest_q
        Y = Vector((0, 1, 0)); res = {}
        for sd in "LR":
            a = []
            for R in F.R_fk:
                fa = R[f"{sd}_LowerArm"] @ Y; hd = R[f"{sd}_Hand"] @ Y
                a.append(math.degrees(fa.angle(hd)))
            res[sd] = dict(max=round(max(a), 1), mean=round(sum(a) / len(a), 1), n_over60=sum(1 for x in a if x > 60),
                           at=[round(a[i], 0) for i in range(0, len(a), max(1, len(a) // 12))])
        out[f"{who}/{name}"] = res
        print(who, name, json.dumps(res))
# CMU 原始
Q, H = GR["read_bvh"](os.path.join(lib, "16_33.bvh"), frames=(2, 236))
for sd, s in (("L", "Left"), ("R", "Right")):
    a = [math.degrees((H[s + "Hand"][i] - H[s + "ForeArm"][i]).angle(H[s + "HandIndex1"][i] - H[s + "Hand"][i])) for i in range(len(H["Hips"]))]
    print("raw16_33", sd, round(max(a), 1), [round(a[i]) for i in range(0, len(a), 20)])
    print("names", [n for n in H if "Hand" in n or "Finger" in n or "Thumb" in n])
json.dump(out, open(r"D:\render-work\tmp\hand_fix\diag.json", "w"), indent=1)
