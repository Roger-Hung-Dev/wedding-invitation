# V12 Mixamo 版：每一幕的「骨骼動作」→ JSON（給審看網頁的 3D 骨架播放器）。2026-10-10 新增。
# 流程（使用者 2026-10-10 指定）：第 1 關先審骨骼動作，確認後第 2 關才出低畫質預覽。
# 動作一律是 Mixamo 現成動畫原樣綁到角色骨架（blender-motion-library 的 mixamo_retarget.py）；
# 這裡只決定「用哪一段、從第幾秒開始、站在哪裡、面向哪裡」，動作本身不改。段與段之間 0.3 秒漸變。
#
# 用法（背景 Blender，只讀 couple.blend、不存檔）：
#   BL="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
#   PROD="D:/SideProject/wedding-invitation/.claude/docs/data/blender/productions/opening-v12"
#   "$BL" -b "$PROD/blend/couple.blend" -P "$PROD/scripts/mx_skeleton.py" -- 02 [OUT=D:/render-work/mixamo/review]
# 輸出：<OUT>/s<幕>/skeleton.json（每格每個角色每根骨頭的位置＋這格在用哪一段）
# 幕的組成：② 寫在下面 scene_02；其他幕各自放 mx_scene_<幕>.py（見 SCENES 底下的載入段）。
# 審看網頁樣板：blender-motion-library 的 assets/skeleton_review/viewer.html（規範：fast-iteration.md §0.5）
import bpy, sys, os, json, math
from mathutils import Vector

ML = r"D:\SideProject\wedding-invitation\.claude\skills\blender-motion-library\scripts"
RAW = r"D:\render-work\mixamo\raw"
_g = {"__name__": "mixamo_retarget"}
exec(open(os.path.join(ML, "mixamo_retarget.py"), encoding="utf8").read(), _g)
Target, read_fbx, retarget, Seg, Sequence = (_g[k] for k in ("Target", "read_fbx", "retarget", "Seg", "Sequence"))

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SCENES_WANT = [a for a in argv if "=" not in a] or ["02"]
OPT = dict(a.split("=", 1) for a in argv if "=" in a)
OUT = OPT.get("OUT", r"D:\render-work\mixamo\review")
FPS = 30

ARM = {"groom": bpy.data.objects["groom_Armature"], "bride": bpy.data.objects["bride_Armature"]}
TGT = {k: Target(a) for k, a in ARM.items()}
_CLIPS = {}


def clip(who, name):
    key = (who, name)
    if key not in _CLIPS:
        if ("src", name) not in _CLIPS:
            _CLIPS[("src", name)] = read_fbx(os.path.join(RAW, name + ".fbx"))
        _CLIPS[key] = retarget(_CLIPS[("src", name)], TGT[who])
    return _CLIPS[key]


def S(who, name, a=0.0, b=None, at=None, label="", loops=None, face=None):
    """一段：Mixamo 動畫 name 的第 a～b 秒（None＝到結尾）；loops＝循環幾次（走路）；face＝開頭面向（度，0＝面向鏡頭；None＝接前一段）"""
    c = clip(who, name)
    fa = int(round(a * c["fps"])); fb = c["n"] - 1 if b is None else min(c["n"] - 1, int(round(b * c["fps"])))
    return Seg(c, fa, fb, name=label or name, at=at, loops=loops, face=face)


# ════════ 各幕的組成 ════════
# 每個角色：segs（照順序）、anchor＝(場景秒數, 骨盆水平位置 xy, 面向 yaw 度)：整條平移／轉向讓那一刻站在那裡。
# yaw：0＝面向鏡頭（−Y）、90＝面向 +X、−90＝面向 −X。
def scene_02():
    # ② 花園拱門：兩人從樹籬後的走道走出來、停下、轉向鏡頭、一起跳查爾斯頓、一起鞠躬（9 秒）
    # 鏡頭 (0, −5.95, 0.95) 看 (0, 0.96, 1.13)、58 mm；停點同第 5 輪（相距 0.95 m，跳舞時蓬裙不碰新郎）
    T_DANCE = 4.2; T_BOW = 6.9
    groom = dict(segs=[
        S("groom", "male_standard_walk", loops=1.3, label="走路（Male Standard Walk）"),
        S("groom", "male_stop_walk", 0, 2.0, label="停下（Walking To Standing Idle）"),
        S("groom", "turn_right_90", 0.7, 2.2, label="右轉 90°（Quick 90 Degree Right Turn）"),
        S("groom", "swing_charleston", 0, 3.0, at=T_DANCE, face=0.0, label="查爾斯頓（Dance Swing Charleston 0～3 秒）"),
        S("groom", "bow_formal", 0, 2.2, at=T_BOW, face=0.0, label="鞠躬（Quick Formal Bow）"),
    ], anchor=("end:1", (-0.45, 0.80), 90.0))
    bride = dict(segs=[
        S("bride", "female_walk", loops=1.6, label="走路（Female Normal Walk）"),
        S("bride", "female_stop_walk", 0, None, label="停下（Female Stop Walking）"),
        S("bride", "turn_left_90", 0, None, label="左轉 90°（Turning 90 Degrees Left）"),
        S("bride", "swing_charleston", 0, 3.0, at=T_DANCE, face=0.0, label="查爾斯頓（Dance Swing Charleston 0～3 秒）"),
        S("bride", "bow_formal", 0, 2.2, at=T_BOW, face=0.0, label="鞠躬（Quick Formal Bow）"),
    ], anchor=("end:1", (0.50, 1.08), -90.0))
    props = [
        dict(kind="box", name="樹籬牆（左）", min=[-7.0, 0.12, 0.0], max=[-1.12, 0.47, 1.7], color="#5F8457"),
        dict(kind="box", name="樹籬牆（右）", min=[1.12, 0.12, 0.0], max=[7.0, 0.47, 1.7], color="#5F8457"),
        dict(kind="box", name="拱門左前柱", min=[-1.05, 0.10, 0.0], max=[-0.95, 0.14, 2.0], color="#FFFDF9"),
        dict(kind="box", name="拱門左後柱", min=[-1.05, 0.46, 0.0], max=[-0.95, 0.50, 2.0], color="#FFFDF9"),
        dict(kind="box", name="拱門右前柱", min=[0.95, 0.10, 0.0], max=[1.05, 0.14, 2.0], color="#FFFDF9"),
        dict(kind="box", name="拱門右後柱", min=[0.95, 0.46, 0.0], max=[1.05, 0.50, 2.0], color="#FFFDF9"),
        dict(kind="box", name="拱門頂", min=[-1.05, 0.10, 2.0], max=[1.05, 0.50, 2.62], color="#FFFDF9", opacity=0.35),
        dict(kind="box", name="小徑", min=[-0.575, -6.0, 0.0], max=[0.575, 0.47, 0.005], color="#E4D6BF"),
        dict(kind="box", name="樹籬後走道", min=[-7.0, 0.47, 0.0], max=[7.0, 1.6, 0.004], color="#E4D6BF", opacity=0.6),
    ]
    cam = dict(pos=[0.0, -5.95, 0.95], aim=[0.0, 0.96, 1.13], lens=58.0, sensor=36.0, aspect=16 / 9)
    return dict(id="02", title="② 新郎新娘一起跳舞", dur=9.0, chars=dict(groom=groom, bride=bride), props=props, cam=cam,
                skirt=dict(who="bride", r_floor=0.70, r_waist=0.16, h_waist=0.98))


SCENES = {"02": scene_02}

# 其他幕各自一支 mx_scene_<幕>.py（定義 scene()，回傳和 scene_02 同形狀的 dict；可直接用 S、math、Vector）。
# 幕分開放，並行製作時不必改這支共用檔。
PROD_SCRIPTS = r"D:\SideProject\wedding-invitation\.claude\docs\data\blender\productions\opening-v12\scripts"
for _sid in SCENES_WANT:
    _p = os.path.join(PROD_SCRIPTS, "mx_scene_%s.py" % _sid)
    if os.path.exists(_p):
        _sg = dict(globals())
        exec(compile(open(_p, encoding="utf8").read(), _p, "exec"), _sg)
        SCENES[_sid] = _sg["scene"]


# ════════ 輸出 ════════
def build(sid):
    sc = SCENES[sid]()
    out = dict(id=sc["id"], title=sc["title"], dur=sc["dur"], fps=FPS, props=sc["props"], cam=sc["cam"], skirt=sc.get("skirt"),
               chars={}, source="Mixamo（原樣綁到角色骨架，只選段落與站位）")
    for who, spec in sc["chars"].items():
        tgt = TGT[who]
        seq = Sequence(tgt, spec["segs"], blend=0.3)
        ta, xy, yaw = spec["anchor"]
        if isinstance(ta, str) and ta.startswith("end:"):      # 第 k 段結束的那一刻
            k = int(ta[4:]); ta = seq.T[k][0] + spec["segs"][k].dur
        seq.place(ta, xy, yaw)
        bones = tgt.keys
        parents = [tgt.parent[n] for n in bones]
        tips = ["J_Bip_C_Head"] + [n for n in bones if n.endswith("3") or n.endswith("ToeBase")]
        frames = []; labels = []
        N = int(round(sc["dur"] * FPS)) + 1
        for i in range(N):
            t = i / FPS
            R, hips, _y = seq.at(t)
            Hd = tgt.fk(R, hips)
            pos = [[round(c, 4) for c in Hd[n]] for n in bones]
            tip = [[round(c, 4) for c in tgt.tail(R, Hd, n)] for n in tips]
            frames.append(dict(p=pos, t=tip))
            labels.append(seq.which(t))
        segs = [dict(start=round(seq.T[i][0], 3), dur=round(s.dur, 3), name=s.name) for i, s in enumerate(spec["segs"])]
        out["chars"][who] = dict(bones=bones, parents=parents, tips=tips, frames=frames, labels=labels, segs=segs,
                                 seq_dur=round(seq.dur, 3), anchor=dict(t=round(ta, 3), xy=list(xy), yaw=yaw))
        print("[mx]", sid, who, "segments:", [(round(seq.T[i][0], 2), round(s.dur, 2), s.name) for i, s in enumerate(spec["segs"])], flush=True)
    d = os.path.join(OUT, "s" + sid); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "skeleton.json"), "w", encoding="utf8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print("[mx] wrote", os.path.join(d, "skeleton.json"), os.path.getsize(os.path.join(d, "skeleton.json")), "bytes", flush=True)


for sid in SCENES_WANT:
    build(sid)
