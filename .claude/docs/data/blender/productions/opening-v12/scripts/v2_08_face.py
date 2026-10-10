# ⑧ v2_08 新娘臉部近照（2026-10-10 第 4 輪回饋「新娘微笑笑開：嘴巴用大笑Joy 改前（第 5 格）、眼睛張開像微笑改後（第 4 格）」）
#   "$BL" -b couple.blend -P prod_cli.py -- --run v2_08_face [TAG=r4] [FK=6.3,…] [PROBE=1]
# 每格兩列：新娘頭部正前方 0.6 m（70 mm，和 lib_face_before_after.jpg 同取景）／從這一幕的鏡頭位置長焦裁臉；
# 左邊並排參考圖第 4、5 格（新娘列）；每格標出實際套到臉上的形狀鍵 → pictures/preview-v2/v2_08_face_<TAG>.jpg
# PROBE=1：固定 6.9 秒，比較 F08_CANDS 幾組形狀鍵組合（選值用）→ v2_08_face_probe.jpg
import bpy, os, json, subprocess
from mathutils import Vector
MODE = "setup"
use("run_prod")
use("shots_v2_s0308")
TAG = str(globals().get("TAG", "r4"))
SID = "v2_08"
S = SHOTS[SID]; S["build"](); stage(S["set"], cast=True)
WORK = os.path.join(r"D:\render-work\opening-v12\preview-v2\quick", "v2_08_face_" + TAG); os.makedirs(WORK, exist_ok=True)
for o in bpy.data.objects:
    if o.type == "MESH":
        for m in o.modifiers:
            m.show_viewport = False
    if o.name.startswith("G_Petals"):
        o.hide_render = True
REF = os.path.join(PROD, "pictures", "preview-v2", "lib_face_before_after.jpg")
SHOW = ["Fcl_MTH_Joy", "Fcl_MTH_Fun", "Fcl_MTH_A", "Fcl_BRW_Joy", "Fcl_BRW_Fun", "Fcl_EYE_Close", "Fcl_EYE_Surprised", "Fcl_EYE_Joy", "Fcl_ALL_Joy"]
ABBR = dict(Fcl_MTH_Joy="MJoy", Fcl_MTH_Fun="MFun", Fcl_MTH_A="A", Fcl_BRW_Joy="BJoy", Fcl_BRW_Fun="BFun", Fcl_EYE_Close="閉",
            Fcl_EYE_Surprised="眼大", Fcl_EYE_Joy="EJoy", Fcl_ALL_Joy="ALLJoy")


def bw(name):
    A = B["ARM"]; return A.matrix_world @ A.pose.bones[name].head


def head_fwd():
    A = B["ARM"]; pb = A.pose.bones["J_Bip_C_Head"]
    v = (A.matrix_world.to_3x3() @ pb.matrix.to_3x3() @ pb.bone.matrix_local.to_3x3().inverted()) @ Vector((0, -1, 0))
    v.z *= 0.3
    return v.normalized()


def kb():
    return bpy.data.objects["bride_Face"].data.shape_keys.key_blocks


def keys_txt():
    k = kb(); out = []
    for n in SHOW:
        v = k[n].value if n in k else 0.0
        if v > 0.005:
            out.append(f"{ABBR[n]}{v:.2f}")
    return " ".join(out) or "(全 0)"


def shoot(t, cv, p, override=None):
    S["frame"](t, cam=False)
    if override is not None:
        k = kb()
        for n in set(SHOW) | set(override):
            if n in k:
                k[n].value = override.get(n, 0.0)
    bpy.context.view_layer.update()
    hc = bw("J_Bip_C_Head") + Vector((0, 0, 0.07 * B["BODY_S"]))
    if cv:
        CAMP = lerpv(S08["cam0"], S08["cam1"], 1.0)
        look(CAMP, hc, 70.0 * (CAMP - hc).length / 0.6)
    else:
        look(hc + head_fwd() * 0.6 + Vector((0, 0, 0.01)), hc, 70.0)
    sc.camera.data.dof.use_dof = False
    render_still(p, (W, H), 8)
    return keys_txt()


W, H = 300, 300
tiles, labels, vals = [], [], {}
LW = 110
if int(globals().get("PROBE", 0)):
    CANDS = json.loads(os.environ.get("F08_CANDS", "null")) or [
        ["Joy改前(ALL_Joy1)", {"Fcl_ALL_Joy": 1.0}],
        ["MJoy1 BJoy1", {"Fcl_MTH_Joy": 1.0, "Fcl_BRW_Joy": 1.0}],
        ["MJoy1 BFun.4", {"Fcl_MTH_Joy": 1.0, "Fcl_BRW_Fun": 0.4}],
        ["MJoy.8 MFun.3 BJoy.5", {"Fcl_MTH_Joy": 0.8, "Fcl_MTH_Fun": 0.3, "Fcl_BRW_Joy": 0.5}],
        ["MJoy1 BJoy.6 眼大.2", {"Fcl_MTH_Joy": 1.0, "Fcl_BRW_Joy": 0.6, "Fcl_EYE_Surprised": 0.2}],
        ["微笑改後(MFun.72 BFun.29)", {"Fcl_MTH_Fun": 0.72, "Fcl_BRW_Fun": 0.29}],
    ]
    rows = ["正面", "鏡頭"]
    for ri in range(2):
        for ci, (nm, ov) in enumerate(CANDS):
            p = os.path.join(WORK, f"probe_{ri}_{ci}.jpg")
            kv = shoot(6.9, ri, p, ov)
            tiles.append((LW + ci * W, 34 + ri * H, p))
            labels.append((LW + ci * W + 6, 34 + ri * H + 6, nm)); labels.append((LW + ci * W + 6, 34 + ri * H + H - 28, kv))
    outp = os.path.join(PROD, "pictures", "preview-v2", "v2_08_face_probe.jpg"); ncol = len(CANDS); crops = []
    title = "v2_08 新娘表情候選（6.9 秒）"
else:
    FK = [float(x) for x in str(globals().get("FK") or "5.70,6.30,6.90,7.20,7.60,8.40,9.20").split(",")]
    rows = ["正面", "鏡頭"]
    for ri in range(2):
        for ci, t in enumerate(FK):
            p = os.path.join(WORK, f"f_{ri}_{ci}.jpg")
            kv = shoot(t, ri, p)
            vals[f"{rows[ri]} {t:.2f}"] = kv
            x = LW + (ci + 2) * W
            tiles.append((x, 34 + ri * H, p))
            labels.append((x + 6, 34 + ri * H + 6, f"{t:.2f}s")); labels.append((x + 6, 34 + ri * H + H - 28, kv))
    # 參考圖：新娘列第 4 格（微笑 改後）、第 5 格（大笑Joy 改前），原圖 2400×600、每格 300
    crops = [[REF, 900, 300, 1200, 600, LW, 34], [REF, 1200, 300, 1500, 600, LW + W, 34]]
    labels += [(LW + 6, 34 + H + 6, "← 參考：第4格 微笑改後（眼睛）"), (LW + W + 6, 34 + H + 6, "← 參考：第5格 Joy改前（嘴巴）")]
    ncol = len(FK) + 2
    json.dump(vals, open(os.path.join(WORK, "face_keys.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    outp = os.path.join(PROD, "pictures", "preview-v2", f"v2_08_face_{TAG}.jpg")
    title = f"v2_08 新娘臉部 {TAG}：左兩格＝參考圖，其餘＝這一幕實際畫面（MJoy＝張嘴笑嘴型、BJoy／BFun＝眉、閉＝閉眼、眼大＝Fcl_EYE_Surprised）"
lay = dict(W=W, H=H, Wt=LW + ncol * W, Ht=34 + 2 * H, tiles=tiles, labels=labels, rows=rows, out=outp, title=title, crops=crops)
lp = os.path.join(WORK, "_layout.json"); json.dump(lay, open(lp, "w", encoding="utf8"), ensure_ascii=False)
code = ("import json,sys;from PIL import Image,ImageDraw,ImageFont;L=json.load(open(sys.argv[1],encoding='utf8'));W,H=L['W'],L['H'];"
        "S=Image.new('RGB',(L['Wt'],L['Ht']),'white');d=ImageDraw.Draw(S);f=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',17);"
        "[S.paste(Image.open(p),(x,y)) for x,y,p in L['tiles']]\n"
        "[S.paste(Image.open(p).crop((a,b,c,e)),(x,y)) for p,a,b,c,e,x,y in L['crops']]\n"
        "[d.text((x,y),s,font=f,fill='yellow',stroke_width=2,stroke_fill='black') for x,y,s in L['labels']]\n"
        "d.text((L['tiles'][0][0] if not L['crops'] else 110,6),L['title'],font=f,fill='black')\n"
        "[d.text((6,34+i*H+H//2),v,font=f,fill='black') for i,v in enumerate(L['rows'])]\n"
        "S.save(L['out'],quality=88)")
subprocess.run(["python", "-c", code, lp], check=True)
print("F08_DONE", outp, json.dumps(vals, ensure_ascii=False), flush=True)
