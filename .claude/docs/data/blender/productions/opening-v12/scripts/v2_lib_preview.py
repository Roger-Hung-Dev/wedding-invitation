# 動作庫預覽圖（單人正面、側面；2026-10-09 wave_arc 入庫用）：新郎（服裝版）站在原點，照動作庫代號擺 N 個時間點
#   "$BL" -b couple.blend -P prod_cli.py -- --run v2_lib_preview ACT_KEY=wave_arc [WHO_=groom] [TS_KEYS=0.1,0.3,…] [OUT=<jpg>]
# → 預設 library/previews/actions/<代號>.jpg（上排正面、下排側面）
import bpy, os, json, math, subprocess
from mathutils import Vector

MODE = "setup"
use("run_prod")
use("shots_v2_s0308")
KEY_ = str(globals().get("ACT_KEY", "wave_arc"))
NS = GR if str(globals().get("WHO_", "groom")) == "groom" else B
_ts = globals().get("TS_KEYS") or [0.08, 0.2, 0.3, 0.42, 0.55, 0.68, 0.92]
TS = [float(x) for x in (_ts if isinstance(_ts, list) else str(_ts).split(","))]
OUT_ = str(globals().get("OUT") or os.path.join(LIB, "previews", "actions", f"{KEY_}.jpg"))
OUTW = os.path.join(r"D:\render-work\opening-v12\preview-v2\quick", f"lib_{KEY_}"); os.makedirs(OUTW, exist_ok=True)
stage("Set_Garden", cast=True)
for o in bpy.data.objects:
    if o.type == "MESH":
        for m in o.modifiers:
            m.show_viewport = False
for nm_ in ("G_Hedge", "G_Arch", "G_ArchFlowers", "G_FlowerBed", "G_Trees", "G_Petals"):
    o_ = bpy.data.objects.get(nm_)
    if o_:
        o_.hide_render = True
show("Cast_bride" if NS is GR else "Cast_groom", False)
A = NS["ARM"]; name, fn, nfr = NS["ACT"][KEY_]
W_, H_ = 300, 420; tiles = []
for ci, t in enumerate(TS):
    P = NS["posture"](dict(fn(t))) if NS is GR else fn(t)
    NS["pose_frame_at"](A, P, 0.0, -1.2, 0.0); bpy.context.view_layer.update()
    c = A.matrix_world @ A.pose.bones["J_Bip_C_Spine"].head; c.x = 0.0; c.z = 1.05
    for ri, (lab, dv) in enumerate((("正面", Vector((0, -1, 0))), ("側面", Vector((-1, 0, 0))))):
        look(c + dv * 3.4 + Vector((0, 0, 0.1)), c, 50.0); sc.camera.data.dof.use_dof = False
        p = os.path.join(OUTW, f"_{ci}_{ri}.jpg"); render_still(p, (W_, H_), 8); tiles.append((ci, ri, p))
lay = dict(W=W_, H=H_, ts=[round(t * nfr / 24.0, 2) for t in TS], tiles=tiles, out=OUT_, title=f"{KEY_}  {name}")
lp = os.path.join(OUTW, "_layout.json"); json.dump(lay, open(lp, "w", encoding="utf8"), ensure_ascii=False)
code = ("import json,sys;from PIL import Image,ImageDraw,ImageFont;L=json.load(open(sys.argv[1],encoding='utf8'));W,H=L['W'],L['H'];"
        "S=Image.new('RGB',(W*len(L['ts']),H*2+34),'white');d=ImageDraw.Draw(S);f=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',18);"
        "[S.paste(Image.open(p),(c*W,34+r*H)) for c,r,p in L['tiles']];"
        "[d.text((c*W+6,6),f'{x:.2f}s',font=f,fill='black') for c,x in enumerate(L['ts'])];S.save(L['out'],quality=86)")
subprocess.run(["python", "-c", code, lp], check=True)
print("LIB_PREVIEW", OUT_, flush=True)
