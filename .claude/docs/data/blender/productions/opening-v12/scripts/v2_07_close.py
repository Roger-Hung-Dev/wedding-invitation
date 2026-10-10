# ⑦ 臉部近照（2026-10-09 第 2 輪回饋：被餵後咀嚼、張眼微笑、乾杯與喝酒不大笑）：
#   "$BL" -b couple.blend -P prod_cli.py -- --run v2_07_close [TAG=after] [V2_07_FACE_LEGACY=1] [CF_KEYS=…]
# 新郎、新娘各一列，每格鏡頭放在頭部正前方 0.6 m（70 mm）→ pictures/preview-v2/v2_07_close_<TAG>.jpg
# 每格另外印出實際套到臉上的形狀鍵（Fcl_MTH_A／MTH_Fun／EYE_Close），對照數字和畫面
import bpy, math, os, json, subprocess
from mathutils import Vector
MODE = "setup"
use("run_prod")
TAG = str(globals().get("TAG", "after"))
SID = "v2_07"
S = SHOTS[SID]; S["build"](); stage(S["set"], cast=True)
_ck = globals().get("CF_KEYS") or "2.50,2.90,3.08,3.25,3.45,3.62,4.40,5.40,7.20,7.80,9.60,11.00"
FK = [float(x) for x in (_ck if isinstance(_ck, list) else str(_ck).split(","))]
WORK = os.path.join(r"D:\render-work\opening-v12\preview-v2-quick-0507", SID, "close_" + TAG); os.makedirs(WORK, exist_ok=True)
for o in bpy.data.objects:
    if o.type == "MESH":
        for m in o.modifiers:
            m.show_viewport = False
    if o.name.startswith("G_Petals"):
        o.hide_render = True


def bw(ns, name):
    A = ns["ARM"]; return A.matrix_world @ A.pose.bones[name].head


def head_fwd(ns):
    A = ns["ARM"]; pb = A.pose.bones["J_Bip_C_Head"]
    v = (A.matrix_world.to_3x3() @ pb.matrix.to_3x3() @ pb.bone.matrix_local.to_3x3().inverted()) @ Vector((0, -1, 0))
    v.z *= 0.3
    return v.normalized()


def keys(who):
    kb = bpy.data.objects[f"{who}_Face"].data.shape_keys.key_blocks
    g = lambda k: kb[k].value if k in kb else 0.0
    j = f" Joy{g('Fcl_MTH_Joy'):.1f}" if g('Fcl_MTH_Joy') > 0.01 else ""
    return f"A{g('Fcl_MTH_A'):.2f} Fun{g('Fcl_MTH_Fun'):.2f} 閉{g('Fcl_EYE_Close'):.2f}{j}"


W, H = 300, 300; tiles = []; labels = []; vals = {}
CAMP = Vector(V2_07["cam"])
ROWS = [("groom", GR, 0), ("bride", B, 0), ("groom", GR, 1), ("bride", B, 1)]     # 第 3、4 列：從這一幕實際的鏡頭位置看（長焦裁到臉）
for ri, (who, ns, cv) in enumerate(ROWS):
    for ci, t in enumerate(FK):
        S["frame"](t, cam=False); bpy.context.view_layer.update()
        hc = bw(ns, "J_Bip_C_Head") + Vector((0, 0, 0.07 * ns["BODY_S"]))
        if cv:
            look(CAMP, hc, 36.0 * (CAMP - hc).length / 0.6 * 70.0 / 36.0)
        else:
            f = head_fwd(ns)
            look(hc + f * 0.6 + Vector((0, 0, 0.01)), hc, 70.0)
        sc.camera.data.dof.use_dof = False
        p = os.path.join(WORK, f"f_{who}_{cv}_{ci}.jpg"); render_still(p, (W, H), 8)
        tiles.append((110 + ci * W, 34 + ri * H, p))
        kv = keys(ns["WHO"]); vals[f"{who}{cv} {t:.2f}"] = kv
        labels.append((110 + ci * W + 6, 34 + ri * H + 6, f"{t:.2f}s"))
        labels.append((110 + ci * W + 6, 34 + ri * H + H - 28, kv))
json.dump(vals, open(os.path.join(WORK, "face_keys.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
rows = ["新郎 正面", "新娘 正面", "新郎 鏡頭", "新娘 鏡頭"]
outp = os.path.join(PROD, "pictures", "preview-v2", f"v2_07_close_{TAG}.jpg")
lay = dict(W=W, H=H, Wt=110 + len(FK) * W, Ht=34 + len(rows) * H, tiles=tiles, labels=labels, rows=rows, out=outp,
           title=f"v2_07 臉部近照 {TAG}（A＝張嘴、Fun＝閉嘴微笑、閉＝閉眼）")
lp = os.path.join(WORK, "_layout.json"); json.dump(lay, open(lp, "w", encoding="utf8"), ensure_ascii=False)
code = ("import json,sys;from PIL import Image,ImageDraw,ImageFont;L=json.load(open(sys.argv[1],encoding='utf8'));W,H=L['W'],L['H'];"
        "S=Image.new('RGB',(L['Wt'],L['Ht']),'white');d=ImageDraw.Draw(S);f=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',18);"
        "[S.paste(Image.open(p),(x,y)) for x,y,p in L['tiles']]\n"
        "[d.text((x,y),s,font=f,fill='yellow',stroke_width=2,stroke_fill='black') for x,y,s in L['labels']]\n"
        "d.text((110,6),L['title'],font=f,fill='black')\n"
        "[d.text((6,34+i*H+H//2),v,font=f,fill='black') for i,v in enumerate(L['rows'])]\n"
        "S.save(L['out'],quality=88)")
subprocess.run(["python", "-c", code, lp], check=True)
print("C07_DONE", outp, flush=True)
