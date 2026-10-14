# ZEPETO 動畫共用：同一個場景放兩個以上的真角色（2026-10-13，B1→B2 正式版起；之前同框的人都用替身膠囊）。
#   add_actor("bride", "bride")：把已出廠的身體附加進工作場景（只讀不存），自己一套骨架、量測、Mixamo 快取、每格姿勢。
#   with as_actor("bride"): ...：區塊內 STATE 的 arm／tgt／poses／measure… 換成這個角色，
#     所以 Z.load_clips、Z.sequence、zanim_fix、zanim_dress.dress、Z.shots 這些只認 STATE 的函式不用改就能用在第二個人身上。
#   pose_at 會順便擺其他角色（POSE_HOOKS 裡的 _cast_hook）：拍照、烤樣張時兩個人都在對的姿勢。
# 注意：
#   - Mixamo 重定向結果跟身體比例有關（新娘比新郎矮），每個角色各自一份快取，不共用 zanim_lib._CL。
#   - 身體出廠閘門只核對點名的身體：MCP 程式與背景渲染的指令要寫 BODY=groom,bride（render_clip 會自動帶）。
#   - 附加進來的物件名稱和主角重複時 Blender 會加 .001；程式一律用骨架物件找它自己的網格，不靠名字。
import bpy
import zanim as Z
STATE = Z.STATE; L = Z.L; mr = Z.mr
SWAP = ("arm", "tgt", "poses", "measure", "body", "outfit_objs", "outfit", "seq", "labels", "segs",
        "head_bvh", "stats", "rows", "lock", "hand_vids", "rad")
_NO = object()


def cast():
    return STATE.setdefault("cast", {})


def add_actor(key, body):
    """附加角色 key（身體 body，要已出廠）。回傳量測"""
    c = cast()
    if key in c:
        return c[key]["state"]["measure"]
    sc = STATE["sc"]; colname = STATE["prefix"] + key
    col = bpy.data.collections.get(colname)
    if col is None or col.name not in [x.name for x in sc.collection.children]:
        with bpy.data.libraries.load(Z.body_blend(body), link=False) as (src, dst):
            dst.objects = [n for n in src.objects if n not in Z.SKIP]
        col = bpy.data.collections.new(colname); sc.collection.children.link(col)
        for o in dst.objects:
            if o is not None:
                col.objects.link(o)
        for o in col.objects:
            if o.name.startswith("WGT"):
                o.hide_render = True; o.hide_viewport = True
    arm = next(o for o in col.objects if o.type == "ARMATURE" and "J_Bip_C_Hips" in o.data.bones)
    tgt = mr.Target(arm)
    st = dict(arm=arm, tgt=tgt, body=body, poses=[])
    c[key] = dict(state=st, clips={}, col=col.name)
    st["measure"] = L.measure(arm, tgt)
    STATE["added"] = STATE.get("added", []) + [o.name for o in col.objects]
    if _cast_hook not in Z.POSE_HOOKS:
        Z.POSE_HOOKS.append(_cast_hook)
    return st["measure"]


def actor(key):
    """角色 key 的狀態（arm、tgt、poses、measure…）"""
    return cast()[key]["state"]


def bodies():
    """場上所有身體（主角＋附加的），給閘門用：BODY=groom,bride"""
    out = [STATE.get("body", "groom")]
    for a in cast().values():
        b = a["state"].get("body")
        if b and b not in out:
            out.append(b)
    return out


class as_actor:
    """區塊內 STATE 換成角色 key 的那一套（離開時存回、主角換回來）"""
    def __init__(self, key):
        self.key = key

    def __enter__(self):
        a = cast()[self.key]
        self.saved = {k: STATE.get(k, _NO) for k in SWAP}
        self.cl = L._CL
        for k in SWAP:
            STATE.pop(k, None)
        STATE.update(a["state"])
        L._CL = a["clips"]
        STATE["_active"] = self.key
        cast()["_main"] = dict(state={k: v for k, v in self.saved.items() if v is not _NO}, clips=self.cl)
        return a["state"]

    def __exit__(self, *e):
        a = cast()[self.key]
        a["state"] = {k: STATE[k] for k in SWAP if k in STATE}
        a["clips"] = L._CL
        for k in SWAP:
            STATE.pop(k, None)
        STATE.update({k: v for k, v in self.saved.items() if v is not _NO})
        L._CL = self.cl
        STATE.pop("_active", None); cast().pop("_main", None)
        return False


def _cast_hook(i):
    """pose_at 的 hook：擺其他角色（正在 as_actor 裡的那個由 pose_at 本身擺）"""
    act = STATE.get("_active")
    for k, a in list(cast().items()):
        if k == act:
            continue
        st = a["state"]; P = st.get("poses")
        if not P:
            continue
        R, h = P[max(0, min(len(P) - 1, i))]
        mr.apply_pose(st["arm"], st["tgt"], R, h)


def hips_world(key, i=None):
    """角色 key 的骨盆世界座標（i 給了就先擺到那一格）"""
    st = actor(key)
    if i is not None:
        Z.pose_at(i / 30)
    arm = st["arm"]
    return arm.matrix_world @ arm.pose.bones["J_Bip_C_Hips"].head
