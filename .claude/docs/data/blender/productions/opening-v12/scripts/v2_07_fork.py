# ⑦ 新郎拿叉子的手部量測＋近照（2026-10-10 第 5 輪回饋「新郎拿叉子的動作沒有拿到叉子」）：
#   "$BL" -b couple.blend -P prod_cli.py -- --run v2_07_fork [TAG=after] [FKEYS=0.0,0.3,…] [CLOSE=1] [V2_07_R2=1]
# 每個時間點：擺好整幕 → 用變形後的網格量新郎左手每根手指（手指骨權重 > 0.5 的皮膚頂點）到叉柄（柄＋頸，叉子局部的長方體）的最近距離
#   （負＝穿進叉柄）、叉柄被幾根手指包住（≤ 5 mm）、叉子握點到掌心的距離、叉子在不在手上（held／table）
#   → D:\render-work\opening-v12\preview-v2-quick-0507\v2_07\fork_<TAG>\fork.json
# CLOSE=1：手部近照（從叉子外側、拇指側兩個方向，叉子握點正前 0.32 m，70 mm）→ pictures/preview-v2/v2_07_fork_<TAG>.jpg
import bpy, math, os, json, subprocess


def _fl(v, dflt):
    if not v:
        v = dflt
    return [float(x) for x in (v if isinstance(v, list) else str(v).split(","))]

from mathutils import Vector
MODE = "setup"
use("run_prod")
TAG = str(globals().get("TAG", "after"))
SID = "v2_07"
S = SHOTS[SID]; S["build"](); stage(S["set"], cast=True)
KEYS = _fl(globals().get("FKEYS"), "0.0,0.2,0.4,0.7,1.5,2.6,4.9,5.1,5.3")
WORK = os.path.join(r"D:\render-work\opening-v12\preview-v2-quick-0507", SID, "fork_" + TAG); os.makedirs(WORK, exist_ok=True)
A = GR["ARM"]; WHO = GR["WHO"]
BODY = bpy.data.objects[WHO + "_Body"]
FORK = bpy.data.objects["V2_Fork"]
FINGERS = ("Thumb", "Index", "Middle", "Ring", "Little")
gi = {g.index: g.name for g in BODY.vertex_groups}
FV = {f: [] for f in FINGERS}
for v in BODY.data.vertices:
    for g in v.groups:
        n = gi.get(g.group, "")
        if g.weight > 0.5 and n.startswith("J_Bip_L_"):
            for f in FINGERS:
                if f in n:
                    FV[f].append(v.index)
print("V07F finger verts", {f: len(v) for f, v in FV.items()}, flush=True)
HALF = Vector((0.0045, 0.00175, 0.0))          # 叉柄截面半寬（局部 x、y）；長度方向 z −0.065～0.075（柄＋頸）
Z0, Z1 = -0.065, 0.075


def box_dist(p):
    """點（叉子局部）到叉柄長方體的距離（負＝在裡面）"""
    q = Vector((abs(p.x) - HALF.x, abs(p.y) - HALF.y, max(Z0 - p.z, p.z - Z1)))
    out = Vector((max(q.x, 0), max(q.y, 0), max(q.z, 0))).length
    return out + min(max(q.x, q.y, q.z), 0.0)


def measure(t):
    S["frame"](t, cam=False); bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    e = BODY.evaluated_get(dg); m = e.to_mesh(); Mb = BODY.matrix_world
    Mi = FORK.matrix_world.inverted()
    res = {}
    for f, idx in FV.items():
        ds = [box_dist(Mi @ (Mb @ m.vertices[i].co)) for i in idx]
        res[f] = round(min(ds) * 1000, 1) if ds else None
    e.to_mesh_clear()
    pb = A.pose.bones["J_Bip_L_Hand"]; Mh = A.matrix_world @ pb.matrix
    palm = Mh @ GR["_palm_pt"](A, "L", GR["_kof"](A))
    grip = FORK.matrix_world.translation
    held = "held" if (T07_FORK[0] <= t < T07_FORK[1]) else "table"
    return dict(t=t, fingers_mm=res, n_wrap=sum(1 for v in res.values() if v is not None and v <= 5.0),
                palm_to_grip_mm=round((palm - grip).length * 1000, 1), fork=held,
                grip=[round(x, 3) for x in grip])


T07_FORK = V2S["07"].get("fork_held", (T07["fork_pick"], T07["pick"][0] + 0.45))
CK = _fl(globals().get("CKEYS"), "0.0,0.2,0.4,0.7,1.5,2.6,4.9,5.1,5.3")
rows = [measure(t) for t in sorted(set(KEYS) | set(CK))]
for r in rows:
    print("V07F", json.dumps(r, ensure_ascii=False), flush=True)
json.dump(rows, open(os.path.join(WORK, "fork.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)

if int(globals().get("CLOSE", 1)):
    for o in bpy.data.objects:
        if o.type == "MESH":
            for md in o.modifiers:
                md.show_viewport = False
        if o.name.startswith("G_Petals"):
            o.hide_render = True
    W, H = 300, 300; tiles = []; labels = []
    for ci, t in enumerate(CK):
        S["frame"](t, cam=False); bpy.context.view_layer.update()
        Mf = FORK.matrix_world; g = Mf.translation
        z = Mf.col[2].to_3d().normalized(); y = Mf.col[1].to_3d().normalized(); x = Mf.col[0].to_3d().normalized()
        r = next(rr for rr in rows if abs(rr["t"] - t) < 1e-6)
        Ah = A.matrix_world @ A.pose.bones["J_Bip_L_Hand"].matrix; pn = (Ah.to_3x3() @ Vector((1, 0, 0))).normalized()   # 左手掌心方向
        th_ = (Ah.to_3x3() @ Vector((0, 0, 1))).normalized()                                                   # 拇指那側
        for ri, d in enumerate((-pn + Vector((0, 0, 0.6)), th_ + Vector((0, 0, 0.4)))):
            d = d.normalized()
            look(g + d * 0.50, g, 50.0); sc.camera.data.dof.use_dof = False
            p = os.path.join(WORK, f"c_{ri}_{ci}.jpg"); render_still(p, (W, H), 8)
            tiles.append((110 + ci * W, 34 + ri * H, p))
            labels.append((110 + ci * W + 6, 34 + ri * H + 6, f"{t:.2f}s {r['fork']}"))
            fm = r["fingers_mm"]
            labels.append((110 + ci * W + 6, 34 + ri * H + H - 50, f"拇{fm['Thumb']} 食{fm['Index']} 中{fm['Middle']}"))
            labels.append((110 + ci * W + 6, 34 + ri * H + H - 26, f"無{fm['Ring']} 小{fm['Little']} mm"))
    outp = os.path.join(PROD, "pictures", "preview-v2", f"v2_07_fork_{TAG}.jpg")
    lay = dict(W=W, H=H, Wt=110 + len(CK) * W, Ht=34 + 2 * H, tiles=tiles, labels=labels, rows=["手背上方", "拇指側"], out=outp,
               title=f"v2_07 新郎左手拿叉子 {TAG}（數字＝各手指到叉柄最近距離，負＝穿進去）")
    lp = os.path.join(WORK, "_layout.json"); json.dump(lay, open(lp, "w", encoding="utf8"), ensure_ascii=False)
    code = ("import json,sys;from PIL import Image,ImageDraw,ImageFont;L=json.load(open(sys.argv[1],encoding='utf8'));W,H=L['W'],L['H'];"
            "S=Image.new('RGB',(L['Wt'],L['Ht']),'white');d=ImageDraw.Draw(S);f=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',18);"
            "[S.paste(Image.open(p),(x,y)) for x,y,p in L['tiles']]\n"
            "[d.text((x,y),s,font=f,fill='yellow',stroke_width=2,stroke_fill='black') for x,y,s in L['labels']]\n"
            "d.text((110,6),L['title'],font=f,fill='black')\n"
            "[d.text((6,34+i*H+H//2),v,font=f,fill='black') for i,v in enumerate(L['rows'])]\n"
            "S.save(L['out'],quality=88)")
    subprocess.run(["python", "-c", code, lp], check=True)
    print("V07F_CLOSE", outp, flush=True)
print("V07F_DONE", TAG, flush=True)
