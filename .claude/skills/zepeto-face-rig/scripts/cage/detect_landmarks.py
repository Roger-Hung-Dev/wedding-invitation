# 找 AI 頭的五官位置（模板包覆的對齊目標）。
#   從貼圖顏色找：先找眼白（只有眼睛有大片白色）→ 從瞳孔沿網格長出「不像皮膚」的整塊＝眼睛範圍；
#   眼睛上方的深色從中間沿網格長出＝眉毛（隔著皮膚的鬢角頭髮長不過去）；
#   鼻子下方「比皮膚紅」的頂點依高度分群：最下面夠寬的一群＝嘴巴、上面那群＝鼻子。
#   （直接用顏色門檻找會把鬢角頭髮當成瞳孔或眉尾；直接量「眼睛到皮膚」會把眼睛圈小、中心偏高）
# 用法：blender.exe -b <AI 頭 .blend> --python detect_landmarks.py -- <輸出 landmarks.json>
#   AI 頭物件名稱：ZEPETO_Head 或 Base_Head（zepeto-avatar-crafter 的 postprocess.py 產生的是 ZEPETO_Head）
import bpy, os, sys, json, math
import numpy as np

out_path = sys.argv[sys.argv.index("--") + 1]
ob = next(o for o in bpy.data.objects if o.name in ("ZEPETO_Head", "Base_Head"))
me = ob.data
N = len(me.vertices)
P = np.array([ob.matrix_world @ v.co for v in me.vertices])
NRM = np.array([v.normal[:] for v in me.vertices])
X, Y, Z = P[:, 0], P[:, 1], P[:, 2]

mat = me.materials[0]
img = next(n.image for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image)
w_img, h_img = img.size
px = np.empty(w_img * h_img * 4, dtype=np.float32)
img.pixels.foreach_get(px)
px = px.reshape(h_img, w_img, 4)
uv = me.uv_layers.active.data
COL = np.zeros((N, 3))
cnt = np.zeros(N)
for poly in me.polygons:
    for li in poly.loop_indices:
        vi = me.loops[li].vertex_index
        u, v = uv[li].uv
        COL[vi] += px[min(h_img - 1, max(0, int(v * h_img))), min(w_img - 1, max(0, int(u * w_img))), :3]
        cnt[vi] += 1
COL /= np.maximum(cnt, 1)[:, None]
LUM = COL @ np.array([0.299, 0.587, 0.114])
RG = COL[:, 0] - COL[:, 1]

FRONT = (NRM[:, 1] < -0.2) & (Y < (Y.min() + Y.max()) / 2)
zc_head = (Z.min() + Z.max()) / 2
H = Z.max() - Z.min()
WINDOW = FRONT & (np.abs(Z - zc_head) < 0.25 * H)
SKIN = FRONT & (LUM > 0.5) & (LUM < 0.92) & (COL.min(1) < 0.75)
SKIN_C = np.median(COL[SKIN], 0)
NOT_SKIN = np.linalg.norm(COL - SKIN_C, axis=1) > 0.22
ADJ = [[] for _ in range(N)]
for e in me.edges:
    a, b = e.vertices
    ADJ[a].append(b)
    ADJ[b].append(a)


def surface_y(x, z):
    i = np.argmin(np.where(FRONT, (X - x) ** 2 + (Z - z) ** 2, np.inf))
    return float(Y[i])


def grow(seeds, allowed):
    seen = set(int(s) for s in seeds)
    stack = list(seen)
    while stack:
        v = stack.pop()
        for u in ADJ[v]:
            if allowed[u] and u not in seen:
                seen.add(u)
                stack.append(u)
    return np.array(sorted(seen))


eyes = {}
EYE_REG = np.zeros(N, bool)  # 兩眼範圍（含睫毛），找眉毛時排除
for side, name in ((1, "L"), (-1, "R")):  # 角色的左＝+X（臉朝 −Y）
    white = WINDOW & (COL.min(1) > 0.78) & (LUM > 0.85) & (np.sign(X) == side)
    if white.sum() >= 3:
        wc = P[white].mean(0)
    else:
        # 眼白只剩細邊（攝影師：整顆深色瞳孔）→ 改找瞳孔：這一側很暗的整塊裡，最低、夠大的那塊
        #   （眉毛、頭髮也是暗的，但都在眼睛上方或外側）
        dark = WINDOW & (LUM < 0.15) & (np.sign(X) == side)
        left, comps = set(np.where(dark)[0].tolist()), []
        while left:
            c = grow([left.pop()], dark)
            left -= set(c.tolist())
            if len(c) >= 5:
                comps.append(c)
        if not comps:
            raise SystemExit(f"[landmarks] 找不到{name}眼（沒有眼白，也沒有深色瞳孔）")
        pupil = min(comps, key=lambda c: Z[c].mean())
        print(f"[landmarks] {name}眼眼白太少（{int(white.sum())} 點），改用瞳孔定位（{len(pupil)} 點）")
        white = np.zeros(N, bool)
        white[pupil] = True
        wc = P[pupil].mean(0)
    seeds = np.where(WINDOW & (LUM < 0.12) & (np.hypot(X - wc[0], Z - wc[2]) < 0.13))[0]
    if len(seeds) < 3:
        seeds = np.where(white)[0]
    region = grow(seeds, FRONT & NOT_SKIN & (np.hypot(X - wc[0], Z - wc[2]) < 0.3))
    EYE_REG[region] = True
    x0, x1, z0, z1 = X[region].min(), X[region].max(), Z[region].min(), Z[region].max()
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    # 虹膜：眼睛範圍裡分三種 —— 眼白（很亮、偏白）、瞳孔（最暗）、虹膜（中間）。量顏色與寬度，給上材質用
    #   （寫死數值時只適合一張臉：換一個眼睛顏色不同的人就不對）
    rl, rc = LUM[region], COL[region]
    white_r = (rc.min(1) > 0.72) & (rl > 0.8)
    pupil_r = rl < np.percentile(rl, 12)
    iris_r = ~white_r & ~pupil_r & (rl < 0.65)
    iris = None
    if iris_r.sum() >= 4:
        ip = region[iris_r | pupil_r]
        iris = dict(color_srgb=[float(v) for v in np.median(rc[iris_r], 0)],
                    radius=float(min(np.ptp(X[ip]), np.ptp(Z[ip])) / 2),
                    pupil_radius=float(np.ptp(X[region[pupil_r]]) / 2) if pupil_r.sum() >= 2 else None)
    ew_, eh_ = (x1 - x0) / 2, (z1 - z0) / 2
    if os.environ.get("ZEPETO_EYES"):  # 試做：手動指定眼睛（量正面正交渲染圖）"xL,xR,z,半寬,半高"——粗眼線畫風自動偵測會抓到眼線
        xl_, xr_, zz_, ew_, eh_ = [float(v) for v in os.environ["ZEPETO_EYES"].split(",")]
        cx, cz = (xl_ if side > 0 else xr_), zz_
        EYE_REG[region] = False  # 自動長出的範圍包到眉毛 → 換成指定的橢圓（放大 1.3 倍含睫毛）
        EYE_REG[FRONT & (((X - cx) / (1.3 * ew_)) ** 2 + ((Z - cz) / (1.6 * eh_)) ** 2 < 1)] = True  # 上下放大 1.6 倍：睫毛往上翹（1.3 倍時睫毛被當成眉毛的起點、找不到眉毛）
        ins = np.where(FRONT & (((X - cx) / ew_) ** 2 + ((Z - cz) / eh_) ** 2 < 0.8))[0]  # 虹膜改從指定的眼睛範圍取（自動範圍抓到藍灰頭髮）
        rl, rc = LUM[ins], COL[ins]
        pupil_r = rl < np.percentile(rl, 12)
        iris_r = ~pupil_r & (rl < 0.55) & (rc.min(1) < 0.6)
        if iris_r.sum() >= 4:
            ip = ins[iris_r | pupil_r]
            iris = dict(color_srgb=[float(v) for v in np.median(rc[iris_r], 0)],
                        radius=float(min(np.ptp(X[ip]), np.ptp(Z[ip])) / 2),
                        pupil_radius=float(np.ptp(X[ins[pupil_r]]) / 2) if pupil_r.sum() >= 2 else None)
            print("[landmarks] %s眼虹膜 %s、半徑 %.3f" % (name, np.round(iris["color_srgb"], 3), iris["radius"]))
    eyes[name] = dict(c=[float(cx), surface_y(cx, cz), float(cz)], ew=float(ew_), eh=float(eh_), n=int(len(region)),
                      iris=iris)

U = abs(eyes["L"]["c"][0] - eyes["R"]["c"][0])
ez = (eyes["L"]["c"][2] + eyes["R"]["c"][2]) / 2
eh_avg = (eyes["L"]["eh"] + eyes["R"]["eh"]) / 2

brows = {}
HAIR_C = np.median(COL[Z > np.percentile(Z, 97)], 0)  # 髮色＝頭頂最高 3% 的中間值（同 wrap.py）
for side, name in ((1, "L"), (-1, "R")):
    e = eyes[name]
    top = e["c"][2] + e["eh"]
    near = FRONT & (np.abs(NRM[:, 0]) < 0.7) & (Z > top) & (Z < top + 0.6 * U) & (np.abs(X - e["c"][0]) < 2.0 * e["ew"])
    # 眼睛範圍（含睫毛）不算：睫毛比眉毛黑時會從睫毛長起，翹起的睫毛碰到臉側長髮就一路長進頭髮（新娘：眉毛量成 0.3 高）
    near &= ~EYE_REG
    col_ = near & (np.abs(X - e["c"][0]) < 0.5 * e["ew"]) & (Z < top + 0.35 * U)
    # 起點＝這一欄最暗的一成；門檻不寫死（咖啡色眉毛比黑眉亮，LUM < 0.2 抓不到）
    s_thr = max(0.2, np.percentile(LUM[col_], 10) + 0.05) if col_.any() else 0.2
    seeds = np.where(col_ & (LUM < s_thr))[0]
    if len(seeds):  # 只取眼睛上方第一段暗色（最低那段）；欄位往上會碰到髮際（新娘：起點混到頭髮，眉色被算成介於兩者之間）
        # 最低那段要「夠密」（0.03 高度內 ≥ 6 點）：零星的睫毛尖會被當成最低點、只留 1～2 點（攝影師：找不到眉毛）
        zs_ = np.sort(Z[seeds])
        z_lo = next((z for z in zs_ if ((zs_ >= z) & (zs_ < z + 0.03)).sum() >= 6), zs_[0])
        seeds = seeds[(Z[seeds] >= z_lo) & (Z[seeds] < z_lo + 0.06)]
    if len(seeds) < 3:
        raise SystemExit(f"[landmarks] 找不到{name}眉毛")
    allowed_b = near & (LUM < max(0.3, np.median(LUM[seeds]) + 0.12))
    # 眉毛顏色和髮色明顯不同（新娘：咖啡色眉、黑髮）→ 像頭髮的不算，否則會從眉尾長進髮際；同色（新郎）就不分
    bc = np.median(COL[seeds], 0)
    print("[landmarks] %s眉色 %s、髮色 %s、相差 %.3f" % (name, np.round(bc, 3), np.round(HAIR_C, 3), np.linalg.norm(bc - HAIR_C)))
    if np.linalg.norm(bc - HAIR_C) > 0.15:
        allowed_b &= ~(np.linalg.norm(COL - HAIR_C, axis=1) < np.linalg.norm(COL - bc, axis=1))
    m = grow(seeds, allowed_b)
    bx, bz = X[m], Z[m]
    inner_x = bx[np.argmin(np.abs(bx))]
    outer_x = bx[np.argmax(np.abs(bx))]
    inner_z = bz[np.abs(bx - inner_x) < 0.03].mean()
    outer_z = bz[np.abs(bx - outer_x) < 0.03].mean()
    brows[name] = dict(inner=[float(inner_x), surface_y(inner_x, inner_z), float(inner_z)],
                       outer=[float(outer_x), surface_y(outer_x, outer_z), float(outer_z)],
                       center=[float(bx.mean()), surface_y(bx.mean(), bz.mean()), float(bz.mean())],
                       half_len=float(abs(outer_x - inner_x) / 2), thick=float(bz.max() - bz.min()),
                       bottom=float(bz.min()), top=float(bz.max()), color_srgb=[float(v) for v in bc])

red_thr = np.percentile(RG[SKIN], 90)
m = FRONT & (RG > red_thr) & (np.abs(X) < 0.8 * U) & (Z < ez - 1.2 * eh_avg) & (Z > ez - 6.0 * eh_avg)
idx = np.where(m)[0][np.argsort(Z[m])]
if len(idx) < 6:
    raise SystemExit("[landmarks] 找不到嘴巴（比皮膚紅的橫帶）")
groups, cur = [], [idx[0]]
for a, b in zip(idx[:-1], idx[1:]):
    if Z[b] - Z[a] > 0.035:
        groups.append(cur)
        cur = []
    cur.append(b)
groups.append(cur)
groups = [np.array(g) for g in groups if len(g) >= 6]
for g in groups:
    print("[landmarks] 紅色群 z=%.3f 寬 %.3f（%.2fU） 點數 %d 中線點 %d" % (Z[g].mean(), X[g].max() - X[g].min(), (X[g].max() - X[g].min()) / U, len(g), int((np.abs(X[g]) < 0.05 * U).sum())))
mouth_g = next(g for g in groups if X[g].max() - X[g].min() > 0.35 * U)
# 腮紅明顯時（ZEPETO 風描述），兩頰的粉紅和嘴連成一群 → 嘴角被抓到臉頰外側。
#   用正中線上的紅點定嘴巴高度，只留同高度附近、臉中段的點
cen = mouth_g[np.abs(X[mouth_g]) < 0.1 * U]
if len(cen) >= 3 and X[mouth_g].max() - X[mouth_g].min() > 0.9 * U:
    mz0 = float(np.median(Z[cen]))
    mouth_g = mouth_g[(np.abs(Z[mouth_g] - mz0) < 0.06) & (np.abs(X[mouth_g]) < 0.5 * U)]
    print("[landmarks] 嘴和腮紅連在一起：只留嘴巴高度 %.3f 附近 %d 點" % (mz0, len(mouth_g)))
upper = [g for g in groups if Z[g].mean() > Z[mouth_g].mean() + 0.03 and not np.isin(mouth_g, g).any()]
mz = float(np.median(Z[mouth_g]))
kl_i = mouth_g[np.argmax(X[mouth_g])]
kr_i = mouth_g[np.argmin(X[mouth_g])]
mouth = dict(center=[float(X[mouth_g].mean()), surface_y(float(X[mouth_g].mean()), mz), mz],
             L=[float(v) for v in P[kl_i]], R=[float(v) for v in P[kr_i]], half_w=float((X[kl_i] - X[kr_i]) / 2))
nose_z = float(Z[upper[0]].mean()) if upper else (ez + mz) / 2
LM = dict(U=float(U), eyes=eyes, brows=brows, mouth=mouth, nose=[0.0, surface_y(0.0, nose_z), nose_z],
          chin_z=float(mz - 0.6 * (ez - mz)), source=bpy.data.filepath,
          note="座標是 AI 頭的世界座標（臉朝 −Y、角色的左＝+X）")
os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(LM, f, ensure_ascii=False, indent=1)
print("[landmarks] U=%.3f 眼 L%s R%s 嘴角 L%s R%s 鼻 z=%.3f → %s" % (
    U, np.round(eyes["L"]["c"], 3), np.round(eyes["R"]["c"], 3), np.round(mouth["L"], 3), np.round(mouth["R"], 3), nose_z, out_path))
