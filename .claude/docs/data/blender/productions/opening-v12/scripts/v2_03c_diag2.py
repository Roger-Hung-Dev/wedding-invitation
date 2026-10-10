# ③ v2_03c 候選真人片段的腳步（2026-10-10 第 4 輪：找步幅小的推重物片段）
import math, json, os
MODE = "setup"
use("run_prod")
use("shots_v2_s0308")
use("shots_v2_s03carpet")
if "mocap_action" not in GR:
    GR["use"]("mocap_retarget")
for path, n in [(p.rsplit(":", 1)[0], int(p.rsplit(":", 1)[1])) for p in str(globals().get("CANDS")).split(";")]:
    F = GR["mocap_action"](path, frames=(2, n), heading=180.0, origin=(0.0, 0.0), foot_fix=False, fix_arm_offset=False, stance_v=0.25)
    rows = []
    for s in "LR":
        for a, b in F.contact_src[s]:
            m = (a + b) // 2; p = F.rig.fk(F.R_fk[m], F.roots[m])[f"{s}_Foot"]
            rows.append((a / 120, b / 120, s, round(p.x, 3), round(p.y, 3)))
    rows.sort()
    print("STEPS", os.path.basename(path), json.dumps([(round(a, 2), round(b, 2), s, x, y) for a, b, s, x, y in rows]), flush=True)
    for t in [i * 0.5 for i in range(int(len(F.R_fk) / 60))]:
        i = int(t * 120); H = F.rig.fk(F.R_fk[i], F.roots[i])
        print("FK", os.path.basename(path), t, [round(v, 2) for v in H["Hips"]], [round(v, 2) for v in H["L_Hand"]], [round(v, 2) for v in H["R_Hand"]], flush=True)
