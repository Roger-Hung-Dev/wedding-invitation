# V12 Mixamo 版：每一幕的「骨骼動作」→ JSON（給審看網頁的 3D 骨架播放器）。2026-10-10 新增。
# 流程（使用者 2026-10-10 指定）：第 1 關先審骨骼動作，確認後第 2 關才出低畫質預覽。
# 動作一律是 Mixamo 現成動畫原樣綁到角色骨架（blender-motion-library 的 mixamo_retarget.py）；
# 這裡只決定「用哪一段、從第幾秒開始、站在哪裡、面向哪裡」，動作本身不改。段與段之間 0.3 秒漸變。
#
# 用法（背景 Blender，只讀 couple.blend、不存檔）：
#   BL="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
#   PROD="D:/SideProject/wedding-invitation/.claude/docs/data/blender/productions/opening-v12"
#   "$BL" -b "$PROD/blend/couple.blend" -P "$PROD/scripts/mx_skeleton.py" -- 02 [OUT=D:/render-work/mixamo/review] [FINAL=1]
#   FINAL=1＝第 2 關「正式版骨骼」：有微調（段的 mod）的角色另存一份不套微調的骨架（ghost），網頁畫成灰線對照
# 輸出：<OUT>/s<幕>/skeleton.json（每格每個角色每根骨頭的位置＋這格在用哪一段）
# 幕的組成：② 寫在下面 scene_02；其他幕各自放 mx_scene_<幕>.py（見 SCENES 底下的載入段）。
# 審看網頁樣板：blender-motion-library 的 assets/skeleton_review/viewer.html（規範：fast-iteration.md §0.5）
import bpy, sys, os, json, math
from mathutils import Vector

ML = r"D:\SideProject\wedding-invitation\.claude\skills\blender-motion-library\scripts"
RAW = r"D:\render-work\mixamo\raw"
_g = {"__name__": "mixamo_retarget"}
exec(open(os.path.join(ML, "mixamo_retarget.py"), encoding="utf8").read(), _g)
Target, read_fbx, retarget, Seg, Sequence, mirror_clip, splice_clip = (_g[k] for k in ("Target", "read_fbx", "retarget", "Seg", "Sequence", "mirror_clip", "splice_clip"))
arm_ik, aim_hand, lift_shoulder, rotate_subtree = (_g[k] for k in ("arm_ik", "aim_hand", "lift_shoulder", "rotate_subtree"))   # 套用後的微調
look_at, finger_pose, gesture, breathe, fix_arm_twist = (_g[k] for k in ("look_at", "finger_pose", "gesture", "breathe", "fix_arm_twist"))
# 已經算好的角色：who → 每格 {骨頭: 世界位置}（Vector）。角色層的 mod 可以拿來對準別人（例：新娘的手貼新郎的背、新郎的手到新娘嘴邊）
BUILT = {}
BUILT_R = {}                      # 每格骨頭的世界轉向（別的角色的微調要用，例：⑦ 新娘轉頭後嘴的真實位置）

# 函式庫模式（第 3 關低畫質預覽 mx_preview.py 用）：exec 前在命名空間放 MX_LIB=True、MX_OPT={...}，只載入、不自動輸出 JSON；
#   之後呼叫 build(sid, write=False) 拿每格每個角色的 (R, hips)
if globals().get("MX_LIB"):
    SCENES_WANT = []
    OPT = dict(globals().get("MX_OPT", {}))
else:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    SCENES_WANT = [a for a in argv if "=" not in a] or ["02"]
    OPT = dict(a.split("=", 1) for a in argv if "=" in a)
OUT = OPT.get("OUT", r"D:\render-work\mixamo\review")
FPS = 30

# 角色骨架：新郎、新娘在 couple.blend；其他角色第一次用到時從自己的角色專案附加骨架（只要骨架，不要網格）
EXTRA_ARM = {"passerby": r"D:\SideProject\wedding-invitation\.claude\docs\data\blender\projects\passerby\passerby_costume.blend"}
_TGT = {}
_CLIPS = {}


def tgt(who):
    if who not in _TGT:
        name = who + "_Armature"
        if name not in bpy.data.objects and who in EXTRA_ARM:
            with bpy.data.libraries.load(EXTRA_ARM[who], link=False) as (src, dst):
                dst.objects = [name]
            bpy.context.scene.collection.objects.link(bpy.data.objects[name])
        _TGT[who] = Target(bpy.data.objects[name])
    return _TGT[who]


def clip(who, name, mirror=False):
    key = (who, name, mirror)
    if key not in _CLIPS:
        if ("src", name) not in _CLIPS:
            _CLIPS[("src", name)] = read_fbx(os.path.join(RAW, name + ".fbx"))
        c = retarget(_CLIPS[("src", name)], tgt(who))
        _CLIPS[key] = mirror_clip(c, tgt(who)) if mirror else c
    return _CLIPS[key]


def S(who, name, a=0.0, b=None, at=None, label="", loops=None, face=None, hold=0.0, seat=None, mirror=False, mod=None, add=False, spans=None, pin=False):
    """一段：Mixamo 動畫 name 的第 a～b 秒（None＝到結尾）；loops＝循環幾次（走路）；face＝開頭面向（度，0＝面向鏡頭；None＝接前一段）；
    hold＝播完停在最後一格幾秒；seat＝這段第一格的骨盆高度要對到幾公尺（坐姿動畫配合椅面，整段上下平移，動作不變）；
    mirror＝左右鏡射（等同 Mixamo 的 Mirror 選項，例：右手拿杯改左手）；mod＝套用後的微調 fn(段內秒數, R, hips) → R；
    add＝只取這段的轉向、腳步（身體和手臂沿用前後段；轉身用，見 mixamo_retarget 的 Seg.add）；
    spans＝先把原片剪接成新的一支再取 a～b 秒（[(a, b[, 漸變秒數]), …]，見 mixamo_retarget 的 splice_clip；例：剪掉不要的段落接成循環）；
    pin＝剪接後扣掉累積的水平位移（原地舞步接成循環才不會漂）"""
    c = clip(who, name, mirror)
    if spans:
        key = (who, name, mirror, tuple(tuple(s) for s in spans), pin)
        if key not in _CLIPS:
            _CLIPS[key] = splice_clip(c, spans, pin=pin)
        c = _CLIPS[key]
    fa = int(round(a * c["fps"])); fb = c["n"] - 1 if b is None else min(c["n"] - 1, int(round(b * c["fps"])))
    dz = 0.0 if seat is None else seat - c["hips"][fa].z
    return Seg(c, fa, fb, hold=hold, name=label or name, at=at, loops=loops, face=face, dz=dz, mod=mod, add=add)


# ════════ 各幕的組成 ════════
# 每個角色：segs（照順序）、anchor＝(場景秒數, 骨盆水平位置 xy, 面向 yaw 度)：整條平移／轉向讓那一刻站在那裡。
# yaw：0＝面向鏡頭（−Y）、90＝面向 +X、−90＝面向 −X。
def garden_props():
    """花園拱門景（② ③ ⑤ ⑧ 共用）：樹籬、拱門柱（0.075 m 見方，set_garden.py:10–12、124–126）、拱門頂、小徑、樹籬後走道"""
    return [
        dict(kind="box", name="樹籬牆（左）", min=[-7.0, 0.12, 0.0], max=[-1.12, 0.47, 1.7], color="#5F8457"),
        dict(kind="box", name="樹籬牆（右）", min=[1.12, 0.12, 0.0], max=[7.0, 0.47, 1.7], color="#5F8457"),
        dict(kind="box", name="拱門左前柱", min=[-1.0375, 0.0825, 0.0], max=[-0.9625, 0.1575, 2.0], color="#FFFDF9"),
        dict(kind="box", name="拱門左後柱", min=[-1.0375, 0.4425, 0.0], max=[-0.9625, 0.5175, 2.0], color="#FFFDF9"),
        dict(kind="box", name="拱門右前柱", min=[0.9625, 0.0825, 0.0], max=[1.0375, 0.1575, 2.0], color="#FFFDF9"),
        dict(kind="box", name="拱門右後柱", min=[0.9625, 0.4425, 0.0], max=[1.0375, 0.5175, 2.0], color="#FFFDF9"),
        dict(kind="box", name="拱門頂", min=[-1.05, 0.10, 2.0], max=[1.05, 0.50, 2.62], color="#FFFDF9", opacity=0.35),
        dict(kind="box", name="小徑", min=[-0.575, -6.0, 0.0], max=[0.575, 0.47, 0.005], color="#E4D6BF"),
        dict(kind="box", name="樹籬後走道", min=[-7.0, 0.47, 0.0], max=[7.0, 1.6, 0.004], color="#E4D6BF", opacity=0.6),
    ]


def scene_02():
    # ② 花園拱門：兩人在拱門下面向鏡頭一起跳舞，從轉場進來跳到下一次轉場（9 秒；第 3 關第 3 輪前是走出來、停下、轉身再跳）
    # 鏡頭 (0, −5.95, 0.95) 看 (0, 0.96, 1.13)、58 mm；停點同第 5 輪（相距 0.95 m，跳舞時蓬裙不碰新郎）
    # 2026-10-11 第 3 關第 2 輪回饋「跳舞改成 Mixamo 的 Booty Hip Hop Dance」「把鞠躬拿掉，直接讓跳舞繼續到轉場」→
    #   下載 booty_hiphop（使用者同意，4.93 秒，4.2 秒起跳剛好跳到 9.1 秒）；查爾斯頓、鞠躬拿掉
    # 2026-10-11 第 3 關第 3 輪回饋「移除進場與最後敬禮畫面，轉場到這個畫面之後就開始跳舞到下一次轉場前」→
    #   走出來、停下、轉身都拿掉，0 秒就在拱門下面向鏡頭跳；「敬禮」＝原片 2.4～4.4 秒左手橫在胸前、一邊往前走 1.3 m 那段，剪掉。
    #   剩下的原地舞步（0～2.07 秒舉手、手放頭後＋4.33～4.87 秒雙手往外甩回起始姿勢；原片頭尾本來就接得起來）接成循環跳滿 9 秒。
    #   剪接點 2.07 ↔ 4.33 是兩邊姿勢最像的格子（tools/loop_probe.py：差 10.7 cm），漸變 0.3 秒；每圈往前、往右累積約 13 cm、7 cm，pin 平均扣掉
    #   （不扣的話 9 秒漂 40 cm，新娘的裙子會碰到右邊拱門柱）；站位＝第 3 輪起跳那一刻的位置
    DANCE = "booty_hiphop"
    LOOP = [(0.0, 2.22)] + [(4.18, 4.9, 0.3), (0.0, 2.22, 0.034)] * 3 + [(4.18, 4.9, 0.3)]   # 4.9 → 0 是原片自己的循環接點，只給 1 格
    lab = "跳舞（Booty Hip Hop Dance，剪掉手放胸前往前走那段，循環跳到轉場）"
    groom = dict(segs=[S("groom", DANCE, spans=LOOP, pin=True, label=lab)], anchor=(0.0, (-0.365, 0.749), 0.0))
    bride = dict(segs=[S("bride", DANCE, spans=LOOP, pin=True, label=lab)], anchor=(0.0, (0.53, 0.98), 0.0))
    props = garden_props()
    cam = dict(pos=[0.0, -5.95, 0.95], aim=[0.0, 0.96, 1.13], lens=58.0, sensor=36.0, aspect=16 / 9)
    return dict(id="02", title="② 新郎新娘一起跳舞", dur=9.0, chars=dict(groom=groom, bride=bride), props=props, cam=cam,
                skirt=dict(who="bride", r_floor=0.70, r_waist=0.16, h_waist=0.98),
                note="整幕只有跳舞：Booty Hip Hop Dance 剪掉手放胸前那段、接成循環；剪接處 0.3 秒漸變，面向鏡頭。",
                decide=["第 3 關第 3 輪回饋後：拿掉走出來、停下、轉身，0 秒就在拱門下跳；原片 2.4～4.4 秒「左手橫在胸前、一邊往前走」那段（你說的敬禮）剪掉，"
                        "剩下的原地舞步循環跳到 9 秒。新娘踢腿、蹲低時腿收在蓬裙裡（裙下護腳）。"] if OPT.get("FINAL") == "1" else ["總長約 9.1 秒（Mixamo 原片的節奏，沒有壓縮）。",
                        "查爾斯頓只用原片前 3 秒：後面原片會整圈轉身，這幕放不下。",
                        "鞠躬（Quick Formal Bow）幅度偏小，不滿意可以換深一點的。",
                        "新娘踢腿時腿會不會踢出蓬裙（圓錐），請在 4.2～7.2 秒看；真正的穿模第 2 關才量。"])


SCENES = {"02": scene_02}

# 其他幕各自一支 mx_scene_<幕>.py（定義 scene()，回傳和 scene_02 同形狀的 dict；可直接用 S、math、Vector）。
# 幕分開放，並行製作時不必改這支共用檔。
PROD_SCRIPTS = r"D:\SideProject\wedding-invitation\.claude\docs\data\blender\productions\opening-v12\scripts"
def load_scene(_sid):
    """載入第 _sid 幕的 mx_scene_<幕>.py（函式庫模式要先呼叫，再 build）"""
    _p = os.path.join(PROD_SCRIPTS, "mx_scene_%s.py" % _sid)
    if os.path.exists(_p):
        _sg = dict(globals())
        exec(compile(open(_p, encoding="utf8").read(), _p, "exec"), _sg)
        SCENES[_sid] = _sg["scene"]


for _sid in SCENES_WANT:
    load_scene(_sid)


# ════════ 輸出 ════════
def skirt_guard(T_, plist, sk, margin=0.05, win_=5):
    """裙下護腳（2026-10-11 第 3 關自我審查：② 新娘跳查爾斯頓踢腿，鞋子和小腿從蓬裙正面戳出來）：
    蓬裙是硬殼（預覽不跑物理），當成圓錐——地面半徑 r_floor、腰高 h_waist 時 r_waist，中心跟著骨盆。
    每格找出那隻腿要往「站直」（大腿、小腿、腳照骨盆的方向直直往下）收多少（k，0～1），膝蓋、腳踝、腳尖才都在裙面內 margin；
    k 前後各 win_ 格取最大再平均（不會一格一格抖），再套回去。只動腿，踢腿的節奏還在、只是踢在裙子裡。回傳每格的 k（左右取大）"""
    import math as _m
    hn = "J_Bip_C_Hips"

    def inside_ok(Hd, h, side):
        for b in (f"J_Bip_{side}_LowerLeg", f"J_Bip_{side}_Foot"):
            p_ = Hd[b]
            if p_.z < sk["h_waist"]:
                r = sk["r_floor"] + (sk["r_waist"] - sk["r_floor"]) * max(0.0, p_.z) / sk["h_waist"]
                if _m.hypot(p_.x - h.x, p_.y - h.y) > r - margin:
                    return False
        return True

    def blend(R, side, k):
        R = dict(R)
        dh = R[hn] @ T_.rest_q[hn].inverted()
        for b in (f"J_Bip_{side}_UpperLeg", f"J_Bip_{side}_LowerLeg", f"J_Bip_{side}_Foot", f"J_Bip_{side}_ToeBase"):
            if b in R:
                R[b] = R[b].slerp(dh @ T_.rest_q[b], k)
        return R

    K = {"L": [], "R": []}
    for R, h in plist:
        for side in "LR":
            if inside_ok(T_.fk(R, h), h, side):
                K[side].append(0.0); continue
            lo, hi = 0.0, 1.0
            for _ in range(10):
                mid = 0.5 * (lo + hi)
                if inside_ok(T_.fk(blend(R, side, mid), h), h, side):
                    hi = mid
                else:
                    lo = mid
            K[side].append(min(1.0, hi + 0.03))
    n_ = len(plist); out_k = []
    for side in "LR":
        k = K[side]
        dil = [max(k[max(0, i - win_):i + win_ + 1]) for i in range(n_)]
        K[side] = [sum(dil[max(0, i - win_):i + win_ + 1]) / len(dil[max(0, i - win_):i + win_ + 1]) for i in range(n_)]
    for i in range(n_):
        R, h = plist[i]
        for side in "LR":
            if K[side][i] > 1e-3:
                R = blend(R, side, K[side][i])
        plist[i] = (R, h)
        out_k.append(max(K["L"][i], K["R"][i]))
    return out_k


def build(sid, write=True):
    """算一幕：write＝輸出 skeleton.json；回傳 (out, poses)：poses[who]＝每格（30 fps）(R, hips)"""
    if sid not in SCENES:
        load_scene(sid)
    sc = SCENES[sid]()
    poses = {}
    out = dict(id=sc["id"], title=sc["title"], dur=sc["dur"], fps=FPS, props=sc["props"], cam=sc["cam"], skirt=sc.get("skirt"),
               chars={}, source="Mixamo（原樣綁到角色骨架，只選段落與站位）",
               note=sc.get("note", ""), decide=sc.get("decide", []))   # 網頁側欄：這幕的說明、需要使用者決定的事
    for who, spec in sc["chars"].items():
        T_ = tgt(who)
        seq = Sequence(T_, spec["segs"], blend=0.3)
        ta, xy, yaw = spec["anchor"]
        if isinstance(ta, str) and ta.startswith("end:"):      # 第 k 段結束的那一刻
            k = int(ta[4:]); ta = seq.T[k][0] + spec["segs"][k].dur
        seq.place(ta, xy, yaw)
        bones = T_.keys
        parents = [T_.parent[n] for n in bones]
        tips = ["J_Bip_C_Head"] + [n for n in bones if n.endswith("3") or n.endswith("ToeBase")]
        frames = []; labels = []
        N = int(round(sc["dur"] * FPS)) + 1
        cmod = spec.get("mod")                 # 角色層的微調（第 2 關）：fn(場景秒數, R, hips) → R，世界座標
        BUILT[who] = []; BUILT_R[who] = []; poses[who] = []
        for i in range(N):
            t = i / FPS
            R, hips, _y = seq.at(t)
            if cmod is not None:
                R = cmod(t, R, hips)
            Hd = T_.fk(R, hips)
            BUILT[who].append(Hd); BUILT_R[who].append(R); poses[who].append((R, hips))
            pos = [[round(c, 4) for c in Hd[n]] for n in bones]
            tip = [[round(c, 4) for c in T_.tail(R, Hd, n)] for n in tips]
            frames.append(dict(p=pos, t=tip))
            labels.append(seq.which(t))
        sk = sc.get("skirt")
        if OPT.get("FINAL") == "1" and sk and sk.get("who") == who:          # 第 2 關：裙下護腳（腳不從硬殼蓬裙戳出來）
            kk = skirt_guard(T_, poses[who], sk)
            moved = [i for i, k in enumerate(kk) if k > 0.01]
            for i in moved:
                R, hips = poses[who][i]; Hd = T_.fk(R, hips); BUILT[who][i] = Hd
                frames[i] = dict(p=[[round(c, 4) for c in Hd[n]] for n in bones], t=[[round(c, 4) for c in T_.tail(R, Hd, n)] for n in tips])
            if moved:
                print("[mx] skirt_guard", sid, who, "frames", len(moved), "max k %.2f" % max(kk), flush=True)
                out.setdefault("guard", {})[who] = [[round(i / FPS, 3), round(kk[i], 3)] for i in range(0, len(kk), 3) if kk[i] > 0.01]
        segs = [dict(start=round(seq.T[i][0], 3), dur=round(s.dur, 3), name=s.name) for i, s in enumerate(spec["segs"])]
        out["chars"][who] = dict(bones=bones, parents=parents, tips=tips, frames=frames, labels=labels, segs=segs,
                                 seq_dur=round(seq.dur, 3), anchor=dict(t=round(ta, 3), xy=list(xy), yaw=yaw))
        # 第 2 關「正式版骨骼」（FINAL=1）：另存一份不套微調（mod）的骨架，網頁畫成灰線對照 Mixamo 原樣
        if OPT.get("FINAL") == "1" and (cmod is not None or any(getattr(s, "mod", None) for s in spec["segs"])):
            keep = [s.mod for s in spec["segs"]]
            for s in spec["segs"]:
                s.mod = None
            seq.place(ta, xy, yaw)
            ghost = []
            for i in range(N):
                R, hips, _y = seq.at(i / FPS)
                Hd = T_.fk(R, hips)
                ghost.append([[round(c, 3) for c in Hd[n]] for n in bones])
            for s, m in zip(spec["segs"], keep):
                s.mod = m
            seq.place(ta, xy, yaw)
            out["chars"][who]["ghost"] = ghost
        print("[mx]", sid, who, "segments:", [(round(seq.T[i][0], 2), round(s.dur, 2), s.name) for i, s in enumerate(spec["segs"])], flush=True)
    if sc.get("post"):                     # 幕自己的後處理：例如照手的位置算紅毯卷的路徑（out["chars"][who]["frames"] 已算好）
        sc["post"](out)
    if not write:
        return out, poses
    d = os.path.join(OUT, "s" + sid); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "skeleton.json"), "w", encoding="utf8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print("[mx] wrote", os.path.join(d, "skeleton.json"), os.path.getsize(os.path.join(d, "skeleton.json")), "bytes", flush=True)
    return out, poses


for sid in SCENES_WANT:
    build(sid)
