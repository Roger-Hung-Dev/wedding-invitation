# 開場影片 V12：新郎耳朵縮小＋新娘口紅（2026-10-11 使用者裁決：耳朵 E1、口紅 L2 玫瑰紅；樣本 https://claude.ai/artifact/XYkXELfobRcceABKn38NDH）
#   "$BL" -b blend/couple.blend -P scripts/face_fix_v12.py -- [check]
#   先把 couple.blend 備份到 D:\render-work\backup\，再寫入、存檔；加 check 只檢查不改。
#
# 1) 新郎耳朵：當初 VRoid 調了「耳朵往外張」，耳朵外緣離頭側 3.6 cm（招風耳）→ 臉網格加形狀鍵 Ear_Small（值 1）：
#    頭骨 rest 空間（y 朝上、x 左右）裡高 1～9.5 cm、|x| 超過 0.084（頭側面）的部分，突出距離 × 0.6（剩 2.1 cm），邊緣 0.8 cm／1 cm 漸變。
#    要還原：Ear_Small 的值設 0。只有 Fcl_ 開頭的表情鍵會被各幕程式改，這個鍵不會被動到。
# 2) 新娘口紅：VRoid 的嘴唇沒有模型，只在皮膚貼圖 _04 上畫一條嘴巴線（x 448～576、y 773）→ 複製成 _04_lip_rose，
#    在線上下畫上唇（厚 20 px、中間唇峰薄 28%）與下唇（厚 30 px），邊緣 6 px 漸層，玫瑰紅 (0.78, 0.25, 0.35) 不透明度 0.62；
#    打包進 .blend，換到新娘臉皮膚材質裡用到 _04 的節點。要還原：節點的 image 換回 _04。
import bpy, os, sys, shutil, time
import numpy as np
from mathutils import Vector

CHECK = "check" in (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
EAR = dict(x0=0.084, y_lo=0.010, y_hi=0.095, lat=0.6, size=1.0)
LIP = dict(cx=512, cy=773, half=70.0, up=20.0, low=30.0, feather=6.0, color=(0.78, 0.25, 0.35), opacity=0.62)


def sm(a, b, x):
    u = max(0.0, min(1.0, (x - a) / (b - a))); return u * u * (3 - 2 * u)


def ear_small(who="groom", name="Ear_Small"):
    arm = bpy.data.objects[who + "_Armature"]; face = bpy.data.objects[who + "_Face"]
    hb = arm.data.bones["J_Bip_C_Head"]
    M = (arm.matrix_world @ hb.matrix_local).inverted() @ face.matrix_world; Mi = M.inverted()
    if not face.data.shape_keys:
        face.shape_key_add(name="Basis")
    kbs = face.data.shape_keys.key_blocks
    if name in kbs:
        face.shape_key_remove(kbs[name])
    basis = face.data.shape_keys.reference_key
    P = [M @ d.co for d in basis.data]
    k = face.shape_key_add(name=name, from_mix=False)
    x0, lo, hi = EAR["x0"], EAR["y_lo"], EAR["y_hi"]
    moved = 0
    for side in (1, -1):
        idx = [i for i, p in enumerate(P) if p.x * side > x0 - 0.008 and lo - 0.01 < p.y < hi + 0.01]
        ear = [i for i in idx if P[i].x * side > x0 and lo < P[i].y < hi]
        c = sum((P[i] for i in ear), Vector()) / max(1, len(ear))
        for i in idx:
            p = P[i]
            w = sm(x0 - 0.008, x0, p.x * side) * sm(lo - 0.01, lo, p.y) * (1 - sm(hi, hi + 0.01, p.y))
            if w <= 0:
                continue
            q = p.copy(); d = p.x * side - x0
            if d > 0:
                q.x = side * (x0 + d * EAR["lat"])
            q.y = c.y + (q.y - c.y) * EAR["size"]; q.z = c.z + (q.z - c.z) * EAR["size"]
            k.data[i].co = Mi @ p.lerp(q, w); moved += 1
    k.value = 1.0
    print("EAR_SMALL", who, "verts moved", moved, flush=True)


def lip_alpha(W, H):
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    dx = (xs - LIP["cx"]) / LIP["half"]
    inside = np.clip(1 - dx * dx, 0, 1)
    up = LIP["up"] * inside ** 0.7 * (1 - 0.28 * np.exp(-((xs - LIP["cx"]) / 7.0) ** 2))
    low = LIP["low"] * inside ** 0.6
    dy = ys - LIP["cy"]; t = np.where(dy < 0, up, low); d = np.abs(dy)
    a = np.clip((t - d) / LIP["feather"] + 0.5, 0, 1) * (t > 0.5)
    a *= 0.75 + 0.25 * np.clip(1 - d / np.maximum(t, 1e-3), 0, 1)
    return a[::-1].copy()                                   # 影像座標（左上原點）→ Blender 像素（左下原點）


def lipstick(who="bride", name="_04_lip_rose"):
    face = bpy.data.objects[who + "_Face"]
    mat = next(m for m in face.data.materials if m and "Face_00_SKIN" in m.name)
    users = [o.name for o in bpy.data.objects if o.type == "MESH" and any(m == mat for m in o.data.materials)]
    assert users == [face.name], users                     # 只有新娘的臉用這個材質，才不會連新郎一起擦到
    nodes = [n for n in mat.node_tree.nodes if n.type == "TEX_IMAGE" and n.image and n.image.name in ("_04", name)]
    base = bpy.data.images["_04"]
    W, H = base.size
    px = np.array(base.pixels[:], dtype=np.float32).reshape(H, W, 4)
    a = (lip_alpha(W, H) * LIP["opacity"])[..., None]
    out = px.copy(); out[..., :3] = px[..., :3] * (1 - a) + np.array(LIP["color"], dtype=np.float32) * a
    im = bpy.data.images.get(name) or bpy.data.images.new(name, W, H, alpha=True)
    im.colorspace_settings.name = base.colorspace_settings.name
    im.pixels.foreach_set(out.ravel()); im.update(); im.pack()
    for n in nodes:
        n.image = im
    print("LIPSTICK", who, mat.name, "nodes", len(nodes), "lip px", int((a[..., 0] > 0.05).sum()), flush=True)


def report():
    g = bpy.data.objects["groom_Face"].data.shape_keys.key_blocks
    print("CHECK ear key", "Ear_Small" in g, g["Ear_Small"].value if "Ear_Small" in g else None)
    mat = next(m for m in bpy.data.objects["bride_Face"].data.materials if m and "Face_00_SKIN" in m.name)
    print("CHECK lip nodes", [n.image.name for n in mat.node_tree.nodes if n.type == "TEX_IMAGE" and n.image and n.image.name.startswith("_04")],
          "packed", bool(bpy.data.images.get("_04_lip_rose") and bpy.data.images["_04_lip_rose"].packed_file))


if CHECK:
    report()
else:
    src = bpy.data.filepath
    bdir = r"D:\render-work\backup"; os.makedirs(bdir, exist_ok=True)
    dst = os.path.join(bdir, "couple_%s_before_face_fix.blend" % time.strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(src, dst)
    print("BACKUP", dst, os.path.getsize(dst), flush=True)
    ear_small("groom")
    lipstick("bride")
    bpy.ops.wm.save_mainfile()
    print("SAVED", src, flush=True)
    report()
