# ③ v2_03c 第 4 輪的接觸量測與近照（2026-10-10）：
#   "$BL" -b couple.blend -P prod_cli.py -- --run v2_03c_contact RATE=24 TAG=r6 [TKEYS=…] [STEP=1] [CLOSE=1] [CKEYS=…]
# 1. 每個時間點（TKEYS，或 T0～T1 每 STEP 格）用變形後的網格量：
#    - 新郎雙手：掌心頂點（Body 網格、Hand 權重、掌心那側）到紅毯卷圓柱面的距離（core＝掌心中心 2.5 cm 內；負＝陷進去）
#    - 新娘雙手：掌心頂點到新郎外套（Cos_Jacket／Vest／Shirt）網格的最近距離（帶正負：沿外套法線，負＝穿進去）
#    - 蓬裙（Tulle、Lining、Cascade、Frill、Ruffle、Peplum、BowTails）到新郎（外套、褲子、鞋、身體）的最近距離
#    - 手腕：前臂方向和手掌方向的夾角
#    → D:\render-work\opening-v12\preview-v2\quick\v2_03c_contact_<TAG>\contact.json
# 2. CLOSE：手掌近照（新郎雙手貼卷：側面、斜上；新娘雙手貼背：側面、斜上）× CKEYS → pictures/preview-v2/v2_03c_hands_<TAG>.jpg
import bpy, os, json, math, subprocess
from mathutils import Vector
from mathutils.bvhtree import BVHTree

MODE = "setup"
use("run_prod")
use("shots_v2_s0308")
use("shots_v2_s03carpet")
if globals().get("OVR"):
    _o = OVR if isinstance(OVR, dict) else json.loads(OVR)
    for k_, v_ in _o.items():
        (C3_JOIN if k_ in C3_JOIN else C3)[k_] = v_
SID = "v2_03c"; TAG = str(globals().get("TAG", "r6"))
S_ = SHOTS[SID]; S_["build"](); stage(S_["set"], cast=True)
st_ = V2S["03c"]
OUTW = os.path.join(r"D:\render-work\opening-v12\preview-v2\quick", f"v2_03c_contact_{TAG}"); os.makedirs(OUTW, exist_ok=True)
for o in bpy.data.objects:
    if o.type == "MESH":
        for m in o.modifiers:
            m.show_viewport = m.type == "ARMATURE"
for ns_ in (GR, B):
    mesh_eval(True, ns_["ARM"].name)
SKIRT = [o for o in bpy.data.objects if o.name.startswith("bride_Cos_") and any(k in o.name for k in ("Tulle", "Lining", "Cascade", "Frill", "Ruffle", "Peplum", "BowTails"))]
GMESH = [bpy.data.objects[n] for n in ("groom_Cos_Jacket", "groom_Cos_Pants", "groom_Cos_Shoes", "groom_Body") if n in bpy.data.objects]
BACK = [bpy.data.objects[n] for n in ("groom_Cos_Jacket",) if n in bpy.data.objects]


def ev_pts(obj, idx=None):
    dg = bpy.context.evaluated_depsgraph_get(); e = obj.evaluated_get(dg); me = e.to_mesh(); M = obj.matrix_world
    n0 = len(obj.data.vertices)
    if idx is None:
        out = [M @ me.vertices[i].co for i in range(min(n0, len(me.vertices)))]
    else:
        out = [M @ me.vertices[i].co for i in idx]
    e.to_mesh_clear(); return out


def bvh_of(objs):
    dg = bpy.context.evaluated_depsgraph_get(); trees = []
    for o in objs:
        e = o.evaluated_get(dg); me = e.to_mesh(); M = o.matrix_world
        vs = [M @ v.co for v in me.vertices]; fs = [tuple(p.vertices) for p in me.polygons]
        trees.append(BVHTree.FromPolygons(vs, fs)); e.to_mesh_clear()
    return trees


def wrist(ns, sd):
    A = ns["ARM"]; mw = A.matrix_world
    el = mw @ A.pose.bones[f"J_Bip_{sd}_LowerArm"].head; wr = mw @ A.pose.bones[f"J_Bip_{sd}_Hand"].head; tp = mw @ A.pose.bones[f"J_Bip_{sd}_Hand"].tail
    return round(math.degrees((wr - el).angle(tp - wr)), 1)


def roll_dist(p):
    o = bpy.data.objects["CP_Roll"]; r = o.scale.y; c = o.location
    return math.hypot(p.y - c.y, p.z - c.z) - r


def measure(t):
    S_["frame"](t, cam=False); bpy.context.view_layer.update()
    r = dict(t=round(t, 3), fix=st_.get("last_hands"))
    if st_["w_g"](t) > 0.5:
        for sd in "LR":
            G = palm_geo(GR, sd); P = ev_pts(bpy.data.objects["groom_Body"], G["idx"])
            core = [roll_dist(P[i]) for i in G["core"]]; allp = [roll_dist(p) for p in P]
            r["g_palm_" + sd] = dict(core_mm=(round(min(core) * 1000, 1), round(max(core) * 1000, 1)), all_mm=(round(min(allp) * 1000, 1), round(max(allp) * 1000, 1)),
                                     wrist=wrist(GR, sd))
    if st_["w_b_on"](t) > 0.5 and t < C3["t100"] + 0.70:
        tr = bvh_of(BACK)
        for sd in "LR":
            G = palm_geo(B, sd); P = ev_pts(bpy.data.objects["bride_Body"], G["idx"])
            ds = []
            for p in P:
                best = None
                for T in tr:
                    loc, nrm, _, dd = T.find_nearest(p)
                    if loc is not None and (best is None or dd < best[0]):
                        best = (dd, loc, nrm)
                if best:
                    sgn = 1 if (p - best[1]).dot(best[2]) >= 0 else -1
                    ds.append(sgn * best[0])
            core = [ds[i] for i in G["core"] if i < len(ds)]
            r["b_palm_" + sd] = dict(core_mm=(round(min(core) * 1000, 1), round(max(core) * 1000, 1)) if core else None,
                                     all_mm=(round(min(ds) * 1000, 1), round(max(ds) * 1000, 1)) if ds else None, wrist=wrist(B, sd))
    if t >= st_["FB"].joins["start_t"] + 0.2:
        trg = bvh_of(GMESH); best = 9.0; who = None
        for o in SKIRT:
            pts = ev_pts(o)[::3]
            for p in pts:
                for gi, T in enumerate(trg):
                    loc, nrm, _, dd = T.find_nearest(p, best)
                    if loc is not None and dd < best:
                        best = dd; who = (o.name, GMESH[gi].name, [round(x, 3) for x in p])
        r["skirt_groom_mm"] = round(best * 1000, 1); r["skirt_pair"] = who
    return r


if int(globals().get("MEAS", 1)):
    if globals().get("TKEYS"):
        TS = [float(x) for x in TKEYS]
    else:
        T0 = float(globals().get("T0", 0.0)); T1 = float(globals().get("T1", C3["dur"])); stp = int(globals().get("STEP", 2))
        TS = [T0 + i * stp / FPS for i in range(int((T1 - T0) * FPS / stp) + 1)]
    rows = []
    for t in TS:
        r = measure(t); rows.append(r); print("CT", json.dumps(r, ensure_ascii=False), flush=True)
    json.dump(rows, open(os.path.join(OUTW, "contact.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)

if int(globals().get("CLOSE", 0)):
    for o in bpy.data.objects:
        if o.type == "MESH":
            for m in o.modifiers:
                m.show_viewport = False
    for nm_ in ("G_Hedge", "G_Arch", "G_ArchFlowers", "G_FlowerBed", "G_Trees", "G_Petals"):
        o_ = bpy.data.objects.get(nm_)
        if o_:
            o_.hide_render = True
    CK = [float(x) for x in (globals().get("CKEYS") or [0.3, 1.5, 2.3, 2.85, 3.05, 3.6])]
    W_, H_ = 320, 260; tiles = []; labs = ["新郎手 側面", "新郎手 斜上", "新娘手 後方", "新娘手 上方"]
    for ci, t in enumerate(CK):
        S_["frame"](t, cam=False); bpy.context.view_layer.update()
        A = GR["ARM"]; mw = A.matrix_world
        gc = (mw @ A.pose.bones["J_Bip_L_Hand"].head + mw @ A.pose.bones["J_Bip_R_Hand"].head) / 2
        BA = B["ARM"]; bc = (BA.matrix_world @ BA.pose.bones["J_Bip_L_Hand"].head + BA.matrix_world @ BA.pose.bones["J_Bip_R_Hand"].head) / 2
        views = [(gc, Vector((1.0, 0.0, 0.15))), (gc, Vector((0.55, -0.55, 0.6))), (bc, Vector((-0.35, -1.0, 0.45))), (bc, Vector((-0.2, 0.25, 1.0)))]   # 新娘在新郎左邊（遠側）：從她後方、正上方看
        for ri, (cc, dv) in enumerate(views):
            look(cc + dv.normalized() * 0.9, cc, 50.0); sc.camera.data.dof.use_dof = False
            p = os.path.join(OUTW, f"_h_{ci}_{ri}.jpg"); render_still(p, (W_, H_), 8); tiles.append((ci, ri, p))
    outp = os.path.join(PROD, "pictures", "preview-v2", f"v2_03c_hands_{TAG}.jpg")
    lay = dict(W=W_, H=H_, keys=CK, views=labs, tiles=tiles, out=outp, title=f"v2_03c hands {TAG}")
    lp = os.path.join(OUTW, "_layout.json"); json.dump(lay, open(lp, "w", encoding="utf8"), ensure_ascii=False)
    code = ("import json,sys;from PIL import Image,ImageDraw,ImageFont;L=json.load(open(sys.argv[1],encoding='utf8'));W,H=L['W'],L['H'];"
            "S=Image.new('RGB',(W*len(L['keys'])+130,H*len(L['views'])+34),'white');d=ImageDraw.Draw(S);f=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',20);"
            "[S.paste(Image.open(p),(130+c*W,34+r*H)) for c,r,p in L['tiles']];"
            "[d.text((130+i*W+8,4),f'{k:.2f}s',font=f,fill='black') for i,k in enumerate(L['keys'])];"
            "[d.text((6,34+i*H+H//2),v,font=f,fill='black') for i,v in enumerate(L['views'])];d.text((6,4),L['title'],font=f,fill='black');S.save(L['out'],quality=86)")
    subprocess.run(["python", "-c", code, lp], check=True)
    print("CT_SHEET", outp, flush=True)
print("CT_DONE", flush=True)
