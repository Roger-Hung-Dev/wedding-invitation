# 四肢第 0 步（references/research-limb-deformation.md 第 0 節）：把 Mixamo 動作庫每一支套到一副身體上，統計各關節實際轉多大。
# 唯讀：開 body.blend 不存檔。拿來決定扭轉骨要幾根、ROM 測試要測幾度、門檻定多少。
# 用法：blender -b <body.blend> -P limb_survey.py -- [OUT=<json>] [RAW=<Mixamo FBX 資料夾>] [ONLY=a,b]
# 量的東西（左右兩邊都算，取較大的）：
#   扭轉：手腕處（前臂→手掌）、手肘處（上臂→前臂）、上臂（肩胛→上臂）、大腿（骨盆→大腿）——mixamo_retarget._twist_about（拆出繞骨頭的扭轉）
#   彎曲：手肘、膝蓋、手腕、腳踝、腳趾——子骨頭方向相對父骨頭、和靜止時差幾度（不含扭轉）；手腕、腳踝另外分方向
#   張指：相鄰兩指第一節在手掌平面上的夾角，減掉靜止時的夾角（只算第一節彎不到約 53° 的影格，彎太多投影方向不穩）
#   站距：待機類片子兩腳踝左右距離
import bpy, sys, os, math, json, glob
from mathutils import Vector
sys.path.insert(0, r"D:\SideProject\wedding-invitation\.claude\skills\blender-motion-library\scripts")
import mixamo_retarget as mr

A = dict(a.split("=", 1) for a in sys.argv[sys.argv.index("--") + 1:] if "=" in a) if "--" in sys.argv else {}
RAW = A.get("RAW", r"D:\render-work\mixamo\raw")
OUT = A.get("OUT", r"D:\render-work\zepeto-body\survey\limb_survey.json")
ONLY = set(A["ONLY"].split(",")) if A.get("ONLY") else None
IDLE = {"standing_idle", "female_idle", "happy_idle", "breathing_idle"}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
arm = bpy.data.objects["Body_Armature"]; tgt = mr.Target(arm)
FN = ("Index", "Middle", "Ring", "Little")


def rest_dir(n):
    t = tgt.rest_t.get(n)
    return (t - tgt.rest_h[n]).normalized()


def delta(R, n):
    return R[n] @ tgt.rest_q[n].inverted()


def bend(R, parent, child):
    """子骨頭相對父骨頭的彎曲（度）＋在父骨頭靜止座標裡的方向變化向量"""
    d_now = delta(R, child) @ rest_dir(child)
    d_par = delta(R, parent).inverted() @ d_now           # 換回父骨頭沒轉時的座標
    d0 = rest_dir(child)
    return math.degrees(d0.angle(d_par)), d_par - d0


def spread(R, side, a, b):
    """兩指第一節在手掌平面（手掌靜止座標、法線＝世界 Z）上的夾角"""
    dh = delta(R, f"J_Bip_{side}_Hand").inverted()
    va = dh @ (delta(R, f"J_Bip_{side}_{a}1") @ rest_dir(f"J_Bip_{side}_{a}1"))
    vb = dh @ (delta(R, f"J_Bip_{side}_{b}1") @ rest_dir(f"J_Bip_{side}_{b}1"))
    va.z = vb.z = 0
    if va.length < 0.6 or vb.length < 0.6:               # 手指彎超過約 53° 時投影太短、方向不穩（會量出 160° 的假張開），不算
        return None
    return math.degrees(va.angle(vb))


def spread_rest(side, a, b):
    va, vb = rest_dir(f"J_Bip_{side}_{a}1").copy(), rest_dir(f"J_Bip_{side}_{b}1").copy()
    va.z = vb.z = 0
    return math.degrees(va.angle(vb))


def pct(xs, q):
    if not xs:
        return None
    s = sorted(xs); return s[min(len(s) - 1, int(q * (len(s) - 1)))]


KEYS = ["tw_wrist", "tw_elbow", "tw_upperarm", "tw_thigh", "bend_elbow", "bend_knee", "bend_wrist", "wrist_flex", "wrist_ext",
        "wrist_side", "bend_ankle", "ankle_up", "ankle_down", "bend_toe", "spread_IM", "spread_MR", "spread_RL", "spread_IL"]
clips = {}
allv = {k: [] for k in KEYS}
stance = {}
files = sorted(glob.glob(os.path.join(RAW, "*.fbx")))
for fp in files:
    name = os.path.splitext(os.path.basename(fp))[0]
    if ONLY and name not in ONLY:
        continue
    try:
        clip = mr.retarget(mr.read_fbx(fp), tgt)
    except Exception as e:
        print("SKIP", name, e); continue
    per = {k: [] for k in KEYS}
    for f in range(clip["n"]):
        R = clip["R"][f]
        for s in "LR":
            J = lambda n: f"J_Bip_{s}_{n}"
            per["tw_wrist"].append(abs(mr._twist_about(tgt, R, J("LowerArm"), J("Hand"))))
            per["tw_elbow"].append(abs(mr._twist_about(tgt, R, J("UpperArm"), J("LowerArm"))))
            per["tw_upperarm"].append(abs(mr._twist_about(tgt, R, J("Shoulder"), J("UpperArm"))))
            per["tw_thigh"].append(abs(mr._twist_about(tgt, R, "J_Bip_C_Hips", J("UpperLeg"))))
            per["bend_elbow"].append(bend(R, J("UpperArm"), J("LowerArm"))[0])
            per["bend_knee"].append(bend(R, J("UpperLeg"), J("LowerLeg"))[0])
            b, dv = bend(R, J("LowerArm"), J("Hand"))
            per["bend_wrist"].append(b)
            # 手腕方向：靜止 T 字掌心朝下（−Z）；往掌心＝屈、往手背＝伸，往拇指／小指側＝側彎
            fl = math.degrees(math.asin(max(-1, min(1, -dv.z))))
            per["wrist_flex"].append(max(0.0, fl)); per["wrist_ext"].append(max(0.0, -fl))
            per["wrist_side"].append(abs(math.degrees(math.asin(max(-1, min(1, dv.y))))))
            b, dv = bend(R, J("LowerLeg"), J("Foot"))
            per["bend_ankle"].append(b)
            # 腳踝：腳背往上＝靠近小腿（+Z 分量），往下＝踮腳
            up = math.degrees(math.asin(max(-1, min(1, dv.z))))
            per["ankle_up"].append(max(0.0, up)); per["ankle_down"].append(max(0.0, -up))
            per["bend_toe"].append(bend(R, J("Foot"), J("ToeBase"))[0])
            for k, a_, b_ in (("spread_IM", "Index", "Middle"), ("spread_MR", "Middle", "Ring"), ("spread_RL", "Ring", "Little"), ("spread_IL", "Index", "Little")):
                sp = spread(R, s, a_, b_)
                if sp is not None:
                    per[k].append(sp - spread_rest(s, a_, b_))
        if name in IDLE:
            Hd = tgt.fk(R, clip["hips"][f])
            stance.setdefault(name, []).append(abs(Hd["J_Bip_L_Foot"].x - Hd["J_Bip_R_Foot"].x))
    clips[name] = {k: dict(max=round(max(v), 1), p95=round(pct(v, 0.95), 1)) if v else dict(max=0.0, p95=0.0) for k, v in per.items()}
    clips[name]["frames"] = clip["n"]
    for k in KEYS:
        allv[k] += per[k]
    print("CLIP", name, clip["n"], {k: clips[name][k]["max"] for k in ("tw_wrist", "tw_elbow", "bend_elbow", "bend_knee", "bend_wrist", "bend_ankle", "spread_IL")})

summary = {}
for k in KEYS:
    v = allv[k] or [0.0]
    top = sorted(clips, key=lambda c: -clips[c][k]["max"])[:3]
    summary[k] = dict(max=round(max(v), 1), p99=round(pct(v, 0.99), 1), p95=round(pct(v, 0.95), 1), p50=round(pct(v, 0.5), 1),
                      top=[(c, clips[c][k]["max"]) for c in top])
st = {k: dict(min=round(min(v) * 100, 1), mean=round(sum(v) / len(v) * 100, 1), max=round(max(v) * 100, 1)) for k, v in stance.items()}
body_stance = round(abs(tgt.rest_h["J_Bip_L_Foot"].x - tgt.rest_h["J_Bip_R_Foot"].x) * 100, 1)
res = dict(body=bpy.data.filepath, clips_n=len(clips), frames=sum(c["frames"] for c in clips.values()), summary=summary,
           stance_cm=st, rest_stance_cm=body_stance, per_clip=clips,
           note="扭轉、彎曲單位度；左右手腳都算；p95＝所有影格的第 95 百分位；站距＝兩腳踝骨頭左右距離（cm）")
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k in KEYS:
    print("SUM", k, summary[k])
print("STANCE", st, "rest", body_stance)
