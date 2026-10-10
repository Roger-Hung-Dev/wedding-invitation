# ⑤ 近照（2026-10-09 第 2 輪回饋用）：
#   "$BL" -b couple.blend -P prod_cli.py -- --run v2_05_close [TAG=after] [G05_LEGACY=1] [SCRATCH_LEGACY=1] [CF_KEYS=…] [CH_KEYS=…]
# 1. 新郎臉部近照（正面略偏鏡頭那側）：看眼睛有沒有瞇、嘴巴是不是閉嘴微笑
# 2. 路人甲右手抱頭近照（右後方、右側、正後方三個角度，其他角色藏起來）：看掌心有沒有貼頭、手腕有沒有折；印前臂 vs 手骨的角度
#   → pictures/preview-v2/v2_05_close_<TAG>.jpg
import bpy, math, os, json, subprocess
from mathutils import Vector
MODE = "setup"
use("run_prod")
TAG = str(globals().get("TAG", "after"))
SID = "v2_05"
S = SHOTS[SID]; S["build"](); stage(S["set"], cast=True)
FK = [float(x) for x in (globals().get("CF_KEYS") or ["0.8", "1.8", "2.8", "5.0", "7.6", "8.4"])]
HK = [float(x) for x in (globals().get("CH_KEYS") or [round(7.1 + 0.15 * i, 2) for i in range(9)])]
# 第 3 輪：先量（要網格變形，所以在關修改器之前）：掌心到頭髮距離、手腕角度（v2_05_hand.py 同一套）
HKEYS = HK
use("v2_05_hand")
HMEAS = {r["t"]: r for r in rows}
WORK = os.path.join(r"D:\render-work\opening-v12\preview-v2-quick-0507", SID, "close_" + TAG); os.makedirs(WORK, exist_ok=True)
for o in bpy.data.objects:
    if o.type == "MESH":
        for m in o.modifiers:
            m.show_viewport = False
PB = V2S["PB"]


def bw(ns, name, end="head"):
    A = ns["ARM"]; pb = A.pose.bones[name]
    return A.matrix_world @ (pb.head if end == "head" else pb.tail)


def fwd(ns):
    l = bw(ns, "J_Bip_L_UpperLeg") - bw(ns, "J_Bip_R_UpperLeg"); l.z = 0; l.normalize()
    return Vector((l.y, -l.x, 0.0))


def head_fwd(ns):
    A = ns["ARM"]; pb = A.pose.bones["J_Bip_C_Head"]
    v = (A.matrix_world.to_3x3() @ pb.matrix.to_3x3() @ pb.bone.matrix_local.to_3x3().inverted()) @ Vector((0, -1, 0))
    v.z *= 0.3
    return v.normalized()


W, H = 320, 320; tiles = []; labels = []
ncol = max(len(FK), len(HK))
# 1. 新郎臉
for ci, t in enumerate(FK):
    S["frame"](t, cam=False); bpy.context.view_layer.update()
    hc = bw(GR, "J_Bip_C_Head") + Vector((0, 0, 0.075))
    f = head_fwd(GR)
    look(hc + f * 0.62 + Vector((0, 0, 0.01)), hc, 70.0); sc.camera.data.dof.use_dof = False
    p = os.path.join(WORK, f"f_{ci}.jpg"); render_still(p, (W, H), 8)
    tiles.append((110 + ci * W, 34, p)); labels.append((110 + ci * W + 6, 40, f"{t:.2f}s 新郎臉"))
# 2. 路人甲右手
show("Cast_groom", False); show("Cast_bride", False)
VIEWS = [("右後方", 135.0), ("右側", 90.0), ("正後方", 180.0)]
for ci, t in enumerate(HK):
    S["frame"](t, cam=False); bpy.context.view_layer.update()
    el, wr, tl = bw(PB, "J_Bip_R_LowerArm"), bw(PB, "J_Bip_R_Hand"), bw(PB, "J_Bip_R_Hand", "tail")
    a = math.degrees((wr - el).angle(tl - wr))
    f = fwd(PB); left = Vector((-f.y, f.x, 0))
    c = bw(PB, "J_Bip_C_Head") + Vector((0, 0, 0.06))
    for ri, (lab, ang) in enumerate(VIEWS):
        r_ = math.radians(ang); d = f * math.cos(r_) - left * math.sin(r_)      # 往角色右邊繞
        look(c + d * 0.85 + Vector((0, 0, 0.18)), c, 50.0); sc.camera.data.dof.use_dof = False
        p = os.path.join(WORK, f"h_{ci}_{ri}.jpg"); render_still(p, (W, H), 8)
        tiles.append((110 + ci * W, 34 + (1 + ri) * H, p))
        m_ = HMEAS.get(t, {})
        labels.append((110 + ci * W + 6, 34 + (1 + ri) * H + 6, f"{t:.2f}s 手腕 {a:.0f}°" if ri == 0 else
                       (f"掌心到頭髮 {m_.get('palm_min_mm', 0):.0f} mm" if ri == 1 else f"掌心中心 {m_.get('palm_c_mm', 0):.0f} mm")))
show("Cast_groom", True); show("Cast_bride", True)
rows = ["新郎 臉", "路人 右後方", "路人 右側", "路人 正後方"]
outp = os.path.join(PROD, "pictures", "preview-v2", f"v2_05_close_{TAG}.jpg")
lay = dict(W=W, H=H, Wt=110 + ncol * W, Ht=34 + len(rows) * H, tiles=tiles, labels=labels, rows=rows, out=outp, title=f"v2_05 {TAG}")
lp = os.path.join(WORK, "_layout.json"); json.dump(lay, open(lp, "w", encoding="utf8"), ensure_ascii=False)
code = ("import json,sys;from PIL import Image,ImageDraw,ImageFont;L=json.load(open(sys.argv[1],encoding='utf8'));W,H=L['W'],L['H'];"
        "S=Image.new('RGB',(L['Wt'],L['Ht']),'white');d=ImageDraw.Draw(S);f=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',20);"
        "[S.paste(Image.open(p),(x,y)) for x,y,p in L['tiles']]\n"
        "[d.text((x,y),s,font=f,fill='yellow',stroke_width=2,stroke_fill='black') for x,y,s in L['labels']]\n"
        "d.text((110,6),L['title'],font=f,fill='black')\n"
        "[d.text((6,34+i*H+H//2),v,font=f,fill='black') for i,v in enumerate(L['rows'])]\n"
        "S.save(L['out'],quality=88)")
subprocess.run(["python", "-c", code, lp], check=True)
print("C05_DONE", outp, flush=True)
