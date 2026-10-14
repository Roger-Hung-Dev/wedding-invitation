# 手指轉移比對：同一格 Mixamo 動作，來源（Mixamo 骨架）與套到我們骨架後，每根手指「往掌心彎多少、往旁邊歪多少」。
# 兩邊數字一樣＝動作本身就這樣；不一樣＝骨架（手指骨頭方向）轉錯。
# 用法：blender -b body.blend -P finger_compare.py -- [CLIP=female_idle.fbx] [F=0]
import bpy, sys, os, math, json
from mathutils import Vector
sys.path.insert(0, r"D:\SideProject\wedding-invitation\.claude\skills\blender-motion-library\scripts")
import mixamo_retarget as mr
A = dict(a.split("=", 1) for a in sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else {}
CLIP = A.get("CLIP", "female_idle.fbx"); F = int(A.get("F", "0"))
arm = bpy.data.objects["Body_Armature"]; tgt = mr.Target(arm)
src = mr.read_fbx(os.path.join(r"D:\render-work\mixamo\raw", CLIP))
if A.get("FIXA"):
    import inspect, textwrap
    code = textwrap.dedent(inspect.getsource(mr.retarget)).replace("D @ A[n].inverted() @ tgt.rest_q[n]", "D @ A[n] @ tgt.rest_q[n]")
    assert "D @ A[n] @ tgt.rest_q[n]" in code
    exec(code, mr.__dict__)
    print("PATCHED retarget: A instead of A^-1")
clip = mr.retarget(src, tgt)
FING = (("Thumb", "Thumb"), ("Index", "Index"), ("Middle", "Middle"), ("Ring", "Ring"), ("Little", "Pinky"))


def frame(P, hand, mid, idx, lit, sg):
    """手的座標系：x＝手腕→中指根（手指方向）、z＝手背法線（掌心朝 −z）、y＝z×x"""
    x = (P[mid] - P[hand]).normalized()
    side = (P[idx] - P[lit])                      # 小指→食指
    z = side.cross(x).normalized() * sg           # 左右手讓 z 都朝手背
    z = (z - x * z.dot(x)).normalized(); y = z.cross(x)
    return x, y, z


def angles(P, chain, fr):
    x, y, z = fr
    a = (P[chain[1]] - P[chain[0]]).normalized(); b = (P[chain[3]] - P[chain[2]]).normalized()
    # 指根節相對手掌：往掌心彎（−z）幾度、往拇指側歪幾度；整根彎曲＝第一節到最後一節的夾角
    base_curl = math.degrees(math.atan2(-a.dot(z), a.dot(x)))
    base_side = math.degrees(math.atan2(a.dot(y), a.dot(x)))
    total = math.degrees(a.angle(b))
    return round(base_curl), round(base_side), round(total)


out = {}
for side, sg, S in (("L", 1, "Left"), ("R", -1, "Right")):
    # 來源
    Hs = src["H"][F]
    Ps = {k: Hs[k] for k in Hs}
    frs = frame(Ps, f"{S}Hand", f"{S}HandMiddle1", f"{S}HandIndex1", f"{S}HandPinky1", sg)
    # 目標
    Rt = clip["R"][F]; Ht = tgt.fk(Rt, clip["hips"][F])
    Pt = dict(Ht)
    for v, _ in FING:
        n3 = f"J_Bip_{side}_{v}3"; Pt[n3 + "_tip"] = tgt.tail(Rt, Ht, n3)
    frt = frame(Pt, f"J_Bip_{side}_Hand", f"J_Bip_{side}_Middle1", f"J_Bip_{side}_Index1", f"J_Bip_{side}_Little1", sg)
    for v, m in FING:
        cs = [f"{S}Hand{m}1", f"{S}Hand{m}2", f"{S}Hand{m}3", f"{S}Hand{m}4"]
        ct = [f"J_Bip_{side}_{v}1", f"J_Bip_{side}_{v}2", f"J_Bip_{side}_{v}3", f"J_Bip_{side}_{v}3_tip"]
        if not all(c in Ps for c in cs):
            continue
        out[f"{side}_{v}"] = dict(mixamo=angles(Ps, cs, frs), ours=angles(Pt, ct, frt))
print("FINGERS (指根往掌心彎°, 指根往拇指側歪°, 整根彎曲°)")
for k, v in out.items():
    print(f"  {k:10s} mixamo={v['mixamo']}  ours={v['ours']}")
# 靜止姿勢的參考（兩邊都是 T 字）
Ps0 = src["rest_h"]; Pt0 = dict(tgt.rest_h)
for v, _ in FING:
    n3 = f"J_Bip_L_{v}3"; Pt0[n3 + "_tip"] = tgt.rest_t[n3]
fr0s = frame(Ps0, "LeftHand", "LeftHandMiddle1", "LeftHandIndex1", "LeftHandPinky1", 1)
fr0t = frame(Pt0, "J_Bip_L_Hand", "J_Bip_L_Middle1", "J_Bip_L_Index1", "J_Bip_L_Little1", 1)
print("REST")
for v, m in FING:
    print(f"  L_{v:7s} mixamo={angles(Ps0, [f'LeftHand{m}{i}' for i in (1, 2, 3, 4)], fr0s)}  ours={angles(Pt0, [f'J_Bip_L_{v}{i}' for i in (1, 2, 3)] + [f'J_Bip_L_{v}3_tip'], fr0t)}")
