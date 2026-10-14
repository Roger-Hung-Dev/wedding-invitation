# 動作小片段自我檢驗（第 7.5 步）的數字：在 MCP 裡、用目前 STATE 的姿勢量（不用渲圖，很快）。
#   foot_motion(a_s, b_s)：鏡內 a_s～b_s 秒，每隻腳抬起幾次、最高抬多少、移動方向來回幾次（碎步）、兩腳同時離地幾格、站著的腳滑多少
#   body_jitter(a_s, b_s)：骨盆高度起伏、面向每格變化的方向來回次數（身體抖、微蹲）
# 2026-10-13 使用者：改完動作後先用小短片自己檢驗再交（B3 新郎轉身雙腳小碎步那次起）。
import zanim as Z
STATE = Z.STATE; L = Z.L
FPS = 30
HANDLES = 1.0
LIFT = 0.006                                            # 鞋底最低點高過 6 mm 算離地


def _idx(t):
    return int(round((t + HANDLES) * FPS))


def foot_motion(a_s, b_s, poses=None, tgt=None, arm=None):
    """回傳 {L/R: {lifts: [離地的鏡內秒…], max_lift_mm, reversals, path_mm, slide_max_mm}, both_off_frames}。
    標準（2026-10-13 B3 定的）：站著轉身每隻腳只抬 1 次、reversals 0、both_off_frames 0、站著的腳 slide ≤ 1 mm／格"""
    poses = poses or STATE["poses"]; tgt = tgt or STATE["tgt"]; arm = arm or STATE["arm"]
    pts = L.sole_points(arm); a, b = _idx(a_s), min(len(poses) - 1, _idx(b_s))
    low = {s: [] for s in "LR"}; ank = {s: [] for s in "LR"}
    for i in range(a, b + 1):
        R, h = poses[i]; so = L.soles(tgt, R, h, pts); Hd = tgt.fk(R, h)
        for s in "LR":
            low[s].append(min(p.z for p in so[s])); ank[s].append(Hd[f"J_Bip_{s}_Foot"].copy())
    out = {}
    for s in "LR":
        V = [(ank[s][k + 1] - ank[s][k]).xy for k in range(len(ank[s]) - 1)]
        rev = sum(1 for k in range(len(V) - 1) if V[k].length > 0.001 and V[k + 1].length > 0.001 and V[k].dot(V[k + 1]) < 0)
        lifts, up = [], False
        for k, z in enumerate(low[s]):
            if z > LIFT and not up:
                lifts.append(round((a + k) / FPS - HANDLES, 2))
            up = z > LIFT
        slide = [V[k].length * 1000 for k in range(len(V)) if low[s][k] <= LIFT and low[s][k + 1] <= LIFT]
        out[s] = dict(lifts=lifts, max_lift_mm=round(1000 * max(low[s])), reversals=rev,
                      path_mm=round(sum(v.length for v in V) * 1000), slide_max_mm=round(max(slide), 1) if slide else 0.0)
    out["both_off_frames"] = sum(1 for k in range(len(low["L"])) if low["L"][k] > LIFT and low["R"][k] > LIFT)
    return out


def body_jitter(a_s, b_s, poses=None, tgt=None):
    """骨盆高度最高－最低（mm）、面向（度）每格變化的方向來回次數（> 0.2° 才算）"""
    import math
    from mathutils import Vector
    poses = poses or STATE["poses"]; tgt = tgt or STATE["tgt"]; a, b = _idx(a_s), min(len(poses) - 1, _idx(b_s))
    zs = [poses[i][1].z for i in range(a, b + 1)]
    def yaw(R):
        v = (R["J_Bip_C_Hips"] @ tgt.rest_q["J_Bip_C_Hips"].inverted()) @ Vector((0, -1, 0))
        return math.degrees(math.atan2(v.x, -v.y))
    ys = [yaw(poses[i][0]) for i in range(a, b + 1)]
    d = [(ys[k + 1] - ys[k] + 180) % 360 - 180 for k in range(len(ys) - 1)]
    rev = sum(1 for k in range(len(d) - 1) if abs(d[k]) > 0.2 and abs(d[k + 1]) > 0.2 and d[k] * d[k + 1] < 0)
    return dict(hips_range_mm=round(1000 * (max(zs) - min(zs)), 1), yaw_from=round(ys[0], 1), yaw_to=round(ys[-1], 1), yaw_reversals=rev)
