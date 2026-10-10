# ③ v2_03c 肩頸診斷與近照（2026-10-10 第 4 輪，由 v2_s08_shoulder.py 複製改成「新郎或新娘」都能量；⑧ 那支不動）：
#   "$BL" -b couple.blend -P prod_cli.py -- --run v2_03c_shoulder RATE=24 WHO_=groom|bride TAG=r6 REF_T=… T0=… T1=… STEP=0.2 [CLOSE=1]
# 量法同下（v2_s08_shoulder 原說明）。REF_T＝轉身時雙手垂下的站姿（揮手前），作為「待機」比較基準。
# ⚠️ 在主命名空間執行：模組層級變數不要用 s、d 這類短名（會蓋掉 pose_lib 的 s()）。
#   "$BL" -b couple.blend -P prod_cli.py -- --run v2_s08_shoulder SHOT=v2_08 RATE=24 [TAG=r4] [DIAG=1] [CLOSE=1] [T0=6.4 T1=9.4 STEP=0.2] [REF_T=5.4]
# 1. DIAG：每 STEP 秒量新郎（揮的那隻手＝右）
#    - 骨頭長度與縮放：每根姿勢骨（head→tail）和 rest 長度比、matrix 的縮放（IK 拉伸、mocap 轉位改骨長都會在這裡露出來）
#    - 肩胛骨（R_Shoulder）相對 rest 往上抬幾度、上臂抬到水平以上幾度、上臂往外張（冠狀面）與往前（矢狀面）
#    - 網格（變形後）：肩頂高度（外套在肩膀那一帶的最高點）、脖子露出長度（頭骨 − 肩頂）、肩寬（兩側外套最外點）、
#      上臂中段粗細（外套頂點到上臂骨軸的平均距離）；和 REF_T（待機）比較的百分比
#    → D:\render-work\opening-v12\preview-v2\quick\<幕>_shoulder_<TAG>\diag.json
# 2. CLOSE：新郎肩頸近照（正面、斜前 45°、背面）每 STEP 秒一列 → pictures/preview-v2/<幕>_shoulder_<TAG>.jpg
import bpy, os, json, math, subprocess
from mathutils import Vector

MODE = "setup"
use("run_prod")
use("shots_v2_s0308")
use("shots_v2_s03carpet")
SID = str(globals().get("SHOT", "v2_03c")); TAG = str(globals().get("TAG", "r4"))
S_ = SHOTS[SID]; S_["build"](); stage(S_["set"], cast=True)
T0_ = float(globals().get("T0", 6.4)); T1_ = float(globals().get("T1", 9.4)); STEP_ = float(globals().get("STEP", 0.2))
REF_T = float(globals().get("REF_T", 5.4))
OUTW = os.path.join(r"D:\render-work\opening-v12\preview-v2\quick", f"{SID}_shoulder_{globals().get('WHO_', 'groom')}_{TAG}"); os.makedirs(OUTW, exist_ok=True)
NS_ = GR if str(globals().get("WHO_", "groom")) == "groom" else B
GA = NS_["ARM"]; GW = NS_["WHO"]
OTHER_ = "Cast_bride" if NS_ is GR else "Cast_groom"
TIMES = [round(T0_ + i * STEP_, 3) for i in range(int(round((T1_ - T0_) / STEP_)) + 1)]


def gbw(name, end="head"):
    pb = GA.pose.bones[name]
    return GA.matrix_world @ (pb.head if end == "head" else pb.tail)


def facing():
    f = GA.matrix_world.to_3x3() @ Vector((0, -1, 0)); f.z = 0
    return f.normalized()


def mesh_pts(obj):
    """變形後的頂點（世界座標）；有 Solidify 時只取前 len(原網格) 個（對應原頂點）"""
    dg = bpy.context.evaluated_depsgraph_get(); ev = obj.evaluated_get(dg); me = ev.to_mesh()
    n0 = len(obj.data.vertices); M = obj.matrix_world
    pts = [M @ me.vertices[i].co for i in range(min(n0, len(me.vertices)))]
    ev.to_mesh_clear()
    return pts


def upper_set(obj, side):
    """原網格裡權重以 <side>_UpperArm 為主的頂點索引"""
    g = obj.vertex_groups.get(f"J_Bip_{side}_UpperArm")
    if g is None:
        return []
    out = []
    for v in obj.data.vertices:
        ws = {obj.vertex_groups[e.group].name: e.weight for e in v.groups}
        if ws.get(g.name, 0) >= 0.5:
            out.append(v.index)
    return out


def diag_frame(t, objs, ups):
    S_["frame"](t, props=False, cam=False); bpy.context.view_layer.update()
    r = dict(t=t)
    # 骨長、縮放
    worst = (0.0, None); scl = (0.0, None)
    for pb in GA.pose.bones:
        if not pb.name.startswith("J_Bip_"):
            continue
        L0 = pb.bone.length
        if L0 < 1e-4:
            continue
        L = (pb.tail - pb.head).length
        e = abs(L / L0 - 1)
        if e > worst[0]:
            worst = (e, pb.name)
        sv = pb.matrix.to_scale(); es = max(abs(x - 1) for x in sv)
        if es > scl[0]:
            scl = (es, pb.name)
    r["bone_len_err_pct"] = (round(worst[0] * 100, 3), worst[1]); r["bone_scale_err_pct"] = (round(scl[0] * 100, 3), scl[1])
    f = facing(); lat = Vector((f.y, -f.x, 0))      # 角色的右手邊（世界）
    for sd, sg in (("R", 1), ("L", -1)):
        sh = gbw(f"J_Bip_{sd}_Shoulder", "tail") - gbw(f"J_Bip_{sd}_Shoulder")
        sh0 = GA.matrix_world.to_3x3() @ (GA.data.bones[f"J_Bip_{sd}_Shoulder"].tail_local - GA.data.bones[f"J_Bip_{sd}_Shoulder"].head_local)
        el = lambda v: math.degrees(math.asin(max(-1, min(1, v.normalized().z))))
        r[f"shoulder_up_{sd}"] = round(el(sh) - el(sh0), 1)
        ua = gbw(f"J_Bip_{sd}_LowerArm") - gbw(f"J_Bip_{sd}_UpperArm")
        r[f"uparm_elev_{sd}"] = round(el(ua), 1)                                      # 上臂高於水平幾度（負＝低於）
        r[f"uparm_out_{sd}"] = round(math.degrees(math.atan2(ua.dot(lat * sg), -ua.z)), 1)   # 冠狀面：從垂下往外張幾度
        r[f"uparm_fwd_{sd}"] = round(math.degrees(math.atan2(ua.dot(f), math.hypot(ua.dot(lat), ua.z))), 1)
    # 網格
    head_z = gbw("J_Bip_C_Head").z
    neck = gbw("J_Bip_C_Neck"); allp = []
    for o in objs:
        allp += mesh_pts(o)
    for sd, sg in (("R", 1), ("L", -1)):
        band = [p for p in allp if 0.07 <= (p - neck).dot(lat * sg) <= 0.15 and abs((p - neck).dot(f)) < 0.12 and p.z < head_z]
        r[f"shoulder_top_z_{sd}"] = round(max(p.z for p in band), 4) if band else None
        r[f"neck_len_{sd}_cm"] = round((head_z - r[f"shoulder_top_z_{sd}"]) * 100, 2) if band else None
    near = [p for p in allp if abs(p.z - (neck.z - 0.12)) < 0.03]
    r["shoulder_w_cm"] = round((max((p - neck).dot(lat) for p in near) - min((p - neck).dot(lat) for p in near)) * 100, 2) if near else None
    for sd in "RL":
        a_ = gbw(f"J_Bip_{sd}_UpperArm"); b_ = gbw(f"J_Bip_{sd}_LowerArm"); ax = (b_ - a_); Lb = ax.length; ax.normalize()
        rs = []
        for o, idx in ups[sd]:
            P = mesh_pts(o)
            for i in idx:
                if i < len(P):
                    v = P[i] - a_; u = v.dot(ax) / Lb
                    if 0.35 <= u <= 0.65:
                        rs.append((v - ax * v.dot(ax)).length)
        r[f"uparm_r_{sd}_cm"] = round(sum(rs) / len(rs) * 100, 2) if rs else None
    return r


if int(globals().get("DIAG", 1)):
    for o in bpy.data.objects:
        if o.type == "MESH":
            for m in o.modifiers:
                m.show_viewport = m.type in ("ARMATURE",)
    mesh_eval(True, GA.name)
    objs = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith(GW + "_") and ("Cos" in o.name or o.name.endswith("_Body"))
            and not o.hide_render]
    print("SH_OBJS", [o.name for o in objs], flush=True)
    jacket = ([o for o in objs if "Cos" in o.name] or objs) if GW == GR["WHO"] else [o for o in objs if o.name.endswith("_Body")]   # 新娘手臂是裸的：量身體網格
    ups = {sd: [(o, upper_set(o, sd)) for o in jacket] for sd in "RL"}
    print("SH_UPS", {sd: [(o.name, len(i)) for o, i in v] for sd, v in ups.items()}, flush=True)
    ref = diag_frame(REF_T, objs, ups); rows = []
    print("SH_REF", json.dumps(ref, ensure_ascii=False), flush=True)
    for t in TIMES:
        r = diag_frame(t, objs, ups)
        for k in ("neck_len_R_cm", "shoulder_w_cm", "uparm_r_R_cm", "uparm_r_L_cm"):
            if r.get(k) and ref.get(k):
                r[k + "_vs_ref_pct"] = round((r[k] / ref[k] - 1) * 100, 1)
        rows.append(r); print("SH", json.dumps(r, ensure_ascii=False), flush=True)
    json.dump(dict(ref=ref, rows=rows), open(os.path.join(OUTW, "diag.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    mesh_eval(False, GA.name)

if int(globals().get("CLOSE", 0)):
    for o in bpy.data.objects:
        if o.type == "MESH":
            for m in o.modifiers:
                m.show_viewport = False
    for nm_ in ("G_Hedge", "G_Arch", "G_ArchFlowers", "G_FlowerBed", "G_Trees", "G_Petals"):
        o_ = bpy.data.objects.get(nm_)
        if o_:
            o_.hide_render = True
    show(OTHER_, False)
    W_, H_ = 300, 300; tiles = []
    VIEWS = [("正面", 0.0), ("斜前45°", -45.0), ("背面", 180.0)]
    for ri, t in enumerate(TIMES):
        S_["frame"](t, props=False, cam=False); bpy.context.view_layer.update()
        c = (gbw("J_Bip_C_Neck") + gbw("J_Bip_R_UpperArm")) / 2 + Vector((0, 0, 0.02)); f = facing(); lat = Vector((f.y, -f.x, 0))
        for ci, (lab, a) in enumerate(VIEWS):
            rr = math.radians(a); dv = f * math.cos(rr) + lat * math.sin(rr)
            look(c + dv * 1.0 + Vector((0, 0, 0.05)), c, 50.0)
            sc.camera.data.dof.use_dof = False
            p = os.path.join(OUTW, f"_c_{ri}_{ci}.jpg"); render_still(p, (W_, H_), 8)
            tiles.append((ci, ri, p, lab))
    show(OTHER_, True)
    # 每列 3 張，秒數多時折成兩大欄
    half = (len(TIMES) + 1) // 2
    lay = dict(W=W_, H=H_, keys=TIMES, tiles=tiles, half=half, out=os.path.join(PROD, "pictures", "preview-v2", f"{SID}_shoulder_{GW}_{TAG}.jpg"))
    lp = os.path.join(OUTW, "_layout.json"); json.dump(lay, open(lp, "w", encoding="utf8"), ensure_ascii=False)
    code = ("import json,sys;from PIL import Image,ImageDraw,ImageFont;L=json.load(open(sys.argv[1],encoding='utf8'));W,H,h=L['W'],L['H'],L['half'];"
            "S=Image.new('RGB',((W*3+80)*2,H*h+34),'white');d=ImageDraw.Draw(S);f=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',20);\n"
            "for c,r,p,l in L['tiles']:\n"
            " X=(r//h)*(W*3+80);Y=34+(r%h)*H;S.paste(Image.open(p),(X+80+c*W,Y))\n"
            " if c==0: d.text((X+6,Y+H//2),f\"{L['keys'][r]:.1f}s\",font=f,fill='black')\n"
            " if r%h==0: d.text((X+80+c*W+8,4),l,font=f,fill='black')\n"
            "S.save(L['out'],quality=86)")
    subprocess.run(["python", "-c", code, lp], check=True)
    print("SH_SHEET", lay["out"], flush=True)
print("SH_DONE", flush=True)
