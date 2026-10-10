# 手部近照（2026-10-09，⑧ 新郎揮手／新娘比愛心用；② 的手腕近照原本是另一支 v2_hand_close.py，已遺失，要用時以本檔為底重建）：
# ⚠️ 這支在主命名空間執行：模組層級的變數不要用 s、d 這類短名（會蓋掉 pose_lib 的 s() 等函式，heart_head 會壞）。指定幕、秒數，鏡頭貼近角色的手，看手腕、手掌方向、手指（新郎揮手、新娘比愛心這類手勢的回報用）。
#   "$BL" -b couple.blend -P prod_cli.py -- --run v2_s08_hands SHOT=v2_08 RATE=24 TIME_KEYS=6.8,7.3,8.2 [TAG=r2]
#   → pictures/preview-v2/<幕>_hands_<TAG>.jpg：每個秒數一列 × 新郎右手（正面、側面）、新娘雙手（正面、側面）
import bpy, os, json, math, subprocess
from mathutils import Vector

MODE = "setup"
use("run_prod")
use("shots_v2_s0308")
use("shots_v2_s03carpet")
SID = str(globals().get("SHOT", "v2_08")); TAG = str(globals().get("TAG", "r2"))
S = SHOTS[SID]; S["build"](); stage(S["set"], cast=True)
_tk = globals().get("TIME_KEYS") or [6.8, 7.3, 8.2]
KEYS = [float(x) for x in (_tk if isinstance(_tk, list) else str(_tk).split(","))]
OUTW = os.path.join(r"D:\render-work\opening-v12\preview-v2\quick", f"{SID}_hands_{TAG}"); os.makedirs(OUTW, exist_ok=True)
for o in bpy.data.objects:                      # 只渲染：網格修改器關掉視窗評估（擺姿勢快 10 倍以上，畫面不變）
    if o.type == "MESH":
        for m in o.modifiers:
            m.show_viewport = False


def bw(ns, name, end="head"):
    A = ns["ARM"]; pb = A.pose.bones[name]
    return A.matrix_world @ (pb.head if end == "head" else pb.tail)


def facing(ns):
    A = ns["ARM"]; f = A.matrix_world.to_3x3() @ Vector((0, -1, 0)); f.z = 0
    return f.normalized()


for nm_ in ("G_Hedge", "G_Arch", "G_ArchFlowers", "G_FlowerBed", "G_Trees", "G_Petals"):   # 近照的側面鏡頭會被樹籬、拱門柱擋住
    o_ = bpy.data.objects.get(nm_)
    if o_:
        o_.hide_render = True
W_, H_ = 400, 400; tiles = []
for ri, t in enumerate(KEYS):
    S["frame"](t, cam=False); bpy.context.view_layer.update()
    cols = []
    for ns, who, sides in ((GR, "groom", "R"), (B, "bride", "LR")):
        c = sum((bw(ns, f"J_Bip_{sd_}_Hand") for sd_ in sides), Vector()) / len(sides)
        f = facing(ns); left = Vector((-f.y, f.x, 0))
        for lab, dv in (("正面", f), ("側面", left if who == "bride" else -left)):
            look(c + dv * (0.75 if who == "bride" else 0.6) + Vector((0, 0, 0.05)), c, 50.0)
            sc.camera.data.dof.use_dof = False
            p = os.path.join(OUTW, f"_{ri}_{who}_{lab}.jpg"); render_still(p, (W_, H_), 8)
            cols.append((f"{'新郎右手' if who == 'groom' else '新娘雙手'} {lab}", p))
        for sd_ in sides:
            el, wr, mid = bw(ns, f"J_Bip_{sd_}_LowerArm"), bw(ns, f"J_Bip_{sd_}_Hand"), bw(ns, f"J_Bip_{sd_}_Middle1")
            print("HAND", SID, who, t, sd_, "wrist_deg", round(math.degrees((wr - el).angle(mid - wr)), 1), flush=True)
    for ci, (lab, p) in enumerate(cols):
        tiles.append((ci, ri, p, lab))
outp = os.path.join(PROD, "pictures", "preview-v2", f"{SID}_hands_{TAG}.jpg")
lay = dict(W=W_, H=H_, keys=KEYS, tiles=tiles, out=outp, title=f"{SID} hands {TAG}")
lp = os.path.join(OUTW, "_layout.json"); json.dump(lay, open(lp, "w", encoding="utf8"), ensure_ascii=False)
code = ("import json,sys;from PIL import Image,ImageDraw,ImageFont;L=json.load(open(sys.argv[1],encoding='utf8'));W,H=L['W'],L['H'];"
        "nc=max(c for c,r,p,l in L['tiles'])+1;S=Image.new('RGB',(W*nc+90,H*len(L['keys'])+34),'white');d=ImageDraw.Draw(S);f=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',20);"
        "[S.paste(Image.open(p),(90+c*W,34+r*H)) for c,r,p,l in L['tiles']];"
        "[d.text((90+c*W+8,4),l,font=f,fill='black') for c,r,p,l in L['tiles'] if r==0];"
        "[d.text((6,34+i*H+H//2),f'{k:.2f}s',font=f,fill='black') for i,k in enumerate(L['keys'])];S.save(L['out'],quality=86)")
subprocess.run(["python", "-c", code, lp], check=True)
print("HAND_SHEET", outp, flush=True)
