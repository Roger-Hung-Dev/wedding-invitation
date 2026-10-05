# 讓手碰到指定位置：用 Nelder-Mead 調 TUNE 參數，使指定骨頭端點靠近目標點。結果寫進 QA/tune.json。
# 先設 FITS = [(動作代號, t, [參數...], [(骨頭, 'head'|'tail', (x,y,z), 權重), ...]), ...]，ITERS（預設 60）。
# 能用 IK（pose_lib.ik_arm / 姿勢的 ik 欄）就優先用 IK；這支只用在「參數化的 FK 姿勢」要微調時。
import bpy, os, json, math
use("studio", "pose_lib", "actions")
from mathutils import Vector
TF = os.path.join(QA, "tune.json")
saved = json.load(open(TF)) if os.path.exists(TF) else {}
TUNE.update(saved)
mesh_eval(False)


def cost(key, t, params, x, targets):
    for p, v in zip(params, x):
        TUNE[p] = v
    pose_frame(ARM, ACT[key][1](t)); bpy.context.view_layer.update()
    mw = ARM.matrix_world; c = 0.0
    for tg in targets:
        bone, end, tgt = tg[:3]; w = tg[3] if len(tg) > 3 else 1.0
        pb = ARM.pose.bones[bone]
        c += w * ((mw @ (pb.head if end == "head" else pb.tail)) - Vector(tgt)).length_squared
    return c


def nelder_mead(f, x0, step=8.0, iters=60):
    n = len(x0)
    pts = [list(x0)] + [[x0[j] + (step if j == i else 0) for j in range(n)] for i in range(n)]
    vals = [f(p) for p in pts]
    for _ in range(iters):
        order = sorted(range(n + 1), key=lambda i: vals[i]); pts = [pts[i] for i in order]; vals = [vals[i] for i in order]
        cen = [sum(p[j] for p in pts[:-1]) / n for j in range(n)]
        xr = [cen[j] + (cen[j] - pts[-1][j]) for j in range(n)]; fr = f(xr)
        if fr < vals[0]:
            xe = [cen[j] + 2 * (cen[j] - pts[-1][j]) for j in range(n)]; fe = f(xe)
            pts[-1], vals[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < vals[-2]:
            pts[-1], vals[-1] = xr, fr
        else:
            xc = [cen[j] + 0.5 * (pts[-1][j] - cen[j]) for j in range(n)]; fc = f(xc)
            if fc < vals[-1]:
                pts[-1], vals[-1] = xc, fc
            else:
                pts = [pts[0]] + [[pts[0][j] + 0.5 * (p[j] - pts[0][j]) for j in range(n)] for p in pts[1:]]
                vals = [vals[0]] + [f(p) for p in pts[1:]]
    i = min(range(n + 1), key=lambda i: vals[i])
    return pts[i], vals[i]


out = []
for key, t, params, targets in FITS:
    x0 = [TUNE[p] for p in params]
    best, v = nelder_mead(lambda x: cost(key, t, params, x, targets), x0, iters=globals().get("ITERS", 60))
    for p, val in zip(params, best):
        saved[p] = round(val, 1); TUNE[p] = round(val, 1)
    errs = []
    cost(key, t, params, best, targets)
    for tg in targets:
        pb = ARM.pose.bones[tg[0]]; errs.append(round(((ARM.matrix_world @ (pb.head if tg[1] == "head" else pb.tail)) - Vector(tg[2])).length * 1000, 1))
    out.append((key, {p: round(val, 1) for p, val in zip(params, best)}, errs))
json.dump(saved, open(TF, "w"), indent=1)
mesh_eval(True); pose_frame(ARM, dict(STAND))
for o in out:
    print(o[0], o[1], "err mm per target", o[2])
