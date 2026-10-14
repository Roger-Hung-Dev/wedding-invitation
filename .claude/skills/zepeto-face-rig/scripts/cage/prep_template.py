# 乙路線第 1 步之一：整理模板頭並找出它的五官位置。
#   模板：LucaDrech「Cartoon Stylized Character Face Head Base Mesh」（CC BY 4.0，見
#   .claude/docs/data/blender/zepeto/templates/cartoon-head-lucadrech/ATTRIBUTION.md）
#   1. 刪掉作者放在頭旁邊展示用的複製零件（名稱 .001）與燈光，套用所有變換。
#   2. 從佈線找五官：眼窩＝頭網格上兩個圓形開口；嘴角＝嘴唇材質左右最遠的點；
#      鼻尖＝臉正中最往前凸的點；下巴＝嘴巴下方、正中最低的臉表面。
#   3. 另存成 template_clean.blend，五官位置寫到 template_landmarks.json。
# 用法（模板是下載的檔案，關掉自動執行）：
#   blender.exe -b --disable-autoexec <模板.blend> --python prep_template.py
import bpy, bmesh, os, json
import numpy as np

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
# 每張臉的輸出資料夾（環境變數 ZEPETO_RIG_WORK）與模板資料夾（ZEPETO_RIG_TEMPLATE）；run_face_rig.py 會設好
WORK = os.environ.get("ZEPETO_RIG_WORK") or os.getcwd()
TEMPLATE = os.environ.get("ZEPETO_RIG_TEMPLATE") or os.path.normpath(
    os.path.join(_SCRIPTS, "..", "..", "..", "..", "docs", "data", "blender", "zepeto", "templates", "cartoon-head-lucadrech"))
HERE = WORK

for o in list(bpy.data.objects):
    if o.name.endswith(".001") or o.type != 'MESH':
        bpy.data.objects.remove(o, do_unlink=True)
for o in bpy.data.objects:
    o.select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects["body"]
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

body = bpy.data.objects["body"]
me = body.data
P = np.array([v.co[:] for v in me.vertices])
bm = bmesh.new()
bm.from_mesh(me)
bm.verts.ensure_lookup_table()

# ── 開口：邊界邊連成的環 ──
bnd = [e for e in bm.edges if e.is_boundary]
adj = {}
for e in bnd:
    a, b = e.verts[0].index, e.verts[1].index
    adj.setdefault(a, []).append(b)
    adj.setdefault(b, []).append(a)
loops, seen = [], set()
for s in adj:
    if s in seen:
        continue
    comp, stack = [], [s]
    seen.add(s)
    while stack:
        v = stack.pop()
        comp.append(v)
        for u in adj[v]:
            if u not in seen:
                seen.add(u)
                stack.append(u)
    loops.append(np.array(comp))
loop_info = [(l, P[l].mean(0)) for l in loops]
print("[tmpl] 開口", [(len(l), np.round(c, 3).tolist()) for l, c in loop_info])

# 眼窩：在臉前面（y 小）、高度在上半、左右各一的開口
face_front_y = P[:, 1].min()
eye_loops = sorted([lc for lc in loop_info if lc[1][1] < face_front_y + 0.4 and abs(lc[1][0]) > 0.1], key=lambda lc: lc[1][0])
if len(eye_loops) != 2:
    raise SystemExit(f"[tmpl] 眼窩開口不是兩個：{len(eye_loops)}")
eyes = {}
for name, (l, c) in zip(("R", "L"), eye_loops):  # x 小的是角色右眼（臉朝 −Y，角色的左＝+X）
    q = P[l]
    eyes[name] = dict(c=c.tolist(), ew=float((q[:, 0].max() - q[:, 0].min()) / 2), eh=float((q[:, 2].max() - q[:, 2].min()) / 2),
                      loop=l.tolist())

# 嘴角：嘴唇材質的頂點左右最遠（作者把眼窩內側也上了 lips 材質，所以只看眼睛下方）
ez0 = (eyes["L"]["c"][2] + eyes["R"]["c"][2]) / 2
lips_idx = [i for i, m in enumerate(me.materials) if m and m.name == "lips"]
lip_verts = sorted({v for p in me.polygons if p.material_index in lips_idx for v in p.vertices})
LV = P[lip_verts]
front_lips = LV[(LV[:, 1] < face_front_y + 0.35) & (LV[:, 2] < ez0 - 0.15)]
kl = front_lips[np.argmax(front_lips[:, 0])]
kr = front_lips[np.argmin(front_lips[:, 0])]
mouth = dict(L=kl.tolist(), R=kr.tolist(), center=((kl + kr) / 2).tolist(), half_w=float((kl[0] - kr[0]) / 2))
print("[tmpl] 嘴唇頂點", len(lip_verts), "前面的", len(front_lips), "嘴角", np.round(kl, 3), np.round(kr, 3), "眼高 z", round(float((eyes["L"]["c"][2] + eyes["R"]["c"][2]) / 2), 3))

# 鼻尖：|x| 很小、高度在眼睛與嘴巴之間、最往前的點
ez = (eyes["L"]["c"][2] + eyes["R"]["c"][2]) / 2
mzc = mouth["center"][2]
mid = (np.abs(P[:, 0]) < 0.02) & (P[:, 2] < ez) & (P[:, 2] > mzc)
nose = P[mid][np.argmin(P[mid][:, 1])].tolist()

# 下巴：嘴巴下方、正中、臉表面最低的點（脖子前面那個轉折以上）
chin_c = (np.abs(P[:, 0]) < 0.02) & (P[:, 2] < mzc - 0.05) & (P[:, 1] < face_front_y + 0.35)
chin = P[chin_c][np.argmin(P[chin_c][:, 2] - 0.0 * P[chin_c][:, 1])].tolist()

U = float(abs(eyes["L"]["c"][0] - eyes["R"]["c"][0]))
LM = dict(U=U, eyes=eyes, mouth=mouth, nose=nose, chin=chin,
          head_top=P[np.argmax(P[:, 2])].tolist(), back=P[np.argmax(P[:, 1])].tolist(),
          note="模板 body 網格的座標（已套用變換；臉朝 −Y、角色的左＝+X）")
with open(os.path.join(TEMPLATE, "template_landmarks.json"), "w", encoding="utf-8") as f:
    json.dump(LM, f, ensure_ascii=False, indent=1)
bm.free()

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(TEMPLATE, "template_clean.blend"))
print("[tmpl] 物件", [o.name for o in bpy.data.objects])
print("[tmpl] U=%.3f 眼 L%s R%s 眼寬高 L(%.3f,%.3f) 嘴角 L%s R%s 鼻尖 %s 下巴 %s" % (
    U, np.round(eyes["L"]["c"], 3), np.round(eyes["R"]["c"], 3), eyes["L"]["ew"], eyes["L"]["eh"],
    np.round(kl, 3), np.round(kr, 3), np.round(nose, 3), np.round(chin, 3)))
