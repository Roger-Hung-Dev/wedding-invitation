# 修細脖子（2026-10-14，rig 步驟：pack_head.py 之後、neck_ring.py 之前）：AI 頭的脖子比 ZEPETO 粗
#   （新娘 52%，ZEPETO 官方 33～34%），身體脖子照接口環做、會跟著粗。目標和身體端對齊：脖子寬 ÷ 頭寬 38%，
#   超過 40% 才修（research-zepeto-face.md「2026-10-14 更正」）。
#   做法：只往脖子中心軸縮，臉不動。
#   1. 環的高度、下巴用 zmeasure.measure_cut（和 neck_ring.py 同一套規則）；環那層擬合橢圓（中心 y、半寬、半厚）
#   2. 縮放倍數＝目標寬 ÷ 環那層現在的左右寬；左右、前後同比例縮（身體端建議：官方只有正面圖，保持現在的形狀）
#   3. 每一點的權重＝「離脖子多遠」×「高度」：
#      - 用環那層的橢圓量（ρ＝1 在脖子表面上）：ρ ≤ 1.12 全縮、1.6 以外不動 → 下巴、下顎、臉頰離脖子遠，不會動；
#        喉嚨往下巴底面那段漸變
#      - 高度：環往下 0.03 到下巴底全縮；環往下 0.10 以下不動（胸像身體會藏；長髮下半段不被拉）；
#        往上：前面（喉嚨）下巴底往上 0.25 漸變到 0；後面（後頸）全縮到耳朵最低點、再往上 0.12 漸變到 0，左右照方向內插。
#        後面只縮到下巴底的話，脖子長的頭（攝影師 v2：環到後腦 0.3）環上面一段沒縮到，從側面、背面看在接口處掐一圈
#   4. Head、Hair 用同一個公式（交界上兩邊各一份的點位置一樣 → 一起動，不會裂開）；Head 的口腔袋不動；耳朵不動
#   5. 形態鍵：每個鍵加同樣的位移（表情的位移量不變）
# 用法：blender -b pack.blend -P neck_slim.py -- <landmarks.json> <eyes.json> <輸出 .blend> <報告 .json>
#   環境變數 NECK_TARGET（預設 0.38）、NECK_MAX（預設 0.40：超過才修）
import bpy, sys, os, json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zmeasure import measure_cut, fit_ellipse, head_H, head_width, section_xy

a = sys.argv[sys.argv.index("--") + 1:]
LM = json.load(open(a[0], encoding="utf-8")); EY = json.load(open(a[1], encoding="utf-8")); OUT, REP = a[2], a[3]
TARGET = float(os.environ.get("NECK_TARGET", "0.38"))
NMAX = float(os.environ.get("NECK_MAX", "0.40"))
R_FULL, R_ZERO = 1.12, 1.6          # 離脖子多遠（橢圓 ρ）：全縮、不動
Z_BELOW_FULL, Z_BELOW_ZERO = 0.03, 0.10   # 環往下：全縮到這裡、這裡以下不動
Z_ABOVE = 0.25                       # 前面：下巴底往上漸變到 0
Z_BACK_FADE = 0.12                   # 後面：耳朵最低點往上漸變到 0
O = bpy.data.objects
hd = O["Head"]
mw = hd.matrix_world
if any(abs(mw[i][j] - (1 if i == j else 0)) > 1e-6 for i in range(4) for j in range(4)):
    raise SystemExit("[slim] Head 的 matrix_world 不是單位矩陣")


def co_of(o):
    c = np.empty(len(o.data.vertices) * 3); o.data.vertices.foreach_get("co", c)
    return c.reshape(-1, 3)


C = co_of(hd)
chinL = LM["chin_z"]
H = head_H(chinL, EY["eyes"][2])
W, _ = head_width(C, chinL, H)
CHIN, RZ, CB = measure_cut(hd)
ZF = CB if CB is not None else CHIN  # 全縮到這個高度（下巴底；V 字臉的「下巴」量到的是下巴前緣，比下巴底高很多）
_ears = O.get("Ears")
EAR_LOW = min((_ears.matrix_world @ v.co).z for v in _ears.data.vertices) if _ears and len(_ears.data.vertices) else None
ZB = max(ZF, EAR_LOW) if EAR_LOW is not None else ZF   # 後頸全縮到耳朵最低點（不低於前面）
band = section_xy(hd, RZ)  # 環那層的截面（和 neck_ring.py 一樣真的切一刀）
if len(band) < 8:
    raise SystemExit("[slim] 環的高度切不到 Head")
cur = float(np.ptp(band[:, 0]))
fe = fit_ellipse(band)
if fe is None:
    raise SystemExit("[slim] 環那層擬合不出橢圓")
YC, RX, RY = fe
ratio = cur / W
rep = dict(head_w=round(W, 4), ring_z=round(RZ, 4), chin=round(CHIN, 4), chin_bottom=None if CB is None else round(CB, 4), back_full_to=round(ZB, 4),
           width_before=round(cur, 4), ratio_before=round(ratio, 3), target=TARGET, max=NMAX, yc=round(YC, 4), rx=round(RX, 4), ry=round(RY, 4))
print("[slim] 頭寬 %.4f、下巴底 %s、環的高度 %.4f、環那層寬 %.4f → 脖子 ÷ 頭寬 %.3f（目標 %.2f，超過 %.2f 才修）；橢圓 中心 y %.4f 半寬 %.4f 半厚 %.4f" % (
    W, "%.4f" % CB if CB is not None else "量不到", RZ, cur, ratio, TARGET, NMAX, YC, RX, RY))


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# 防呆：量到的不像脖子就停（不要照縮）。攝影師 v2：嘴巴、下巴偵測錯 → 環的高度落在下顎，寬度比 0.79、
#   照縮成 0.48 倍，下半張臉被壓扁。脖子實際最粗的是攝影師 v1 約 0.59
if ratio > 0.70 or RZ > chinL - 0.02:
    raise SystemExit("[slim] 量到的不像脖子（環的高度 %.3f、下巴 %.3f、寬度比 %.2f）：多半是嘴巴或下巴偵測錯，"
                     "看 check/eyes_detect.png、landmarks.json，必要時填 face.json 的 mouth_manual／eyes_manual 從 eyes 重跑" % (RZ, chinL, ratio))
if ratio <= NMAX + 1e-4:
    rep.update(slimmed=False, scale=1.0)
    print("[slim] 不用修")
else:
    s = TARGET * W / cur
    rep.update(slimmed=True, scale=round(s, 4), objects={})
    # 後頸每一層自己的「脖子表面」：Head 在脖子中心後面的點，每 0.02 一層最外圈的 ρ（環那層＝1）。
    #   後頸越往上越粗的頭（攝影師 v2），只用環那層當尺，上面那段 ρ 超過 1.12、縮不滿 → 側面背面看像漏斗、接口處掐一圈。
    #   用每層自己的尺 → 整段後頸同比例縮（原本上粗下細的樣子保留）。後頸不在 Head 上的頭（新娘：畫成髮色、分給頭髮）那幾層沒有點 → 尺＝1（照舊）
    rho_h = np.sqrt((C[:, 0] / RX) ** 2 + ((C[:, 1] - YC) / RY) ** 2)
    back_h = C[:, 1] > YC
    LV = np.arange(RZ, ZB + Z_BACK_FADE + 0.02, 0.02)
    REF = []
    for zl in LV:
        sel = back_h & (np.abs(C[:, 2] - zl) < 0.01)
        REF.append(max(1.0, float(rho_h[sel].max())) if sel.sum() >= 3 else 1.0)
    REF = np.array(REF)
    rep["back_ref"] = [round(v, 3) for v in REF]
    print("[slim] 後頸每層的尺（環那層＝1，往上每 0.02）：%s" % np.round(REF, 2).tolist())
    for name in ("Head", "Hair"):
        o = O.get(name)
        if o is None or o.type != 'MESH':
            continue
        if any(abs(o.matrix_world[i][j] - (1 if i == j else 0)) > 1e-6 for i in range(4) for j in range(4)):
            raise SystemExit("[slim] %s 的 matrix_world 不是單位矩陣" % name)
        P = co_of(o)
        rho = np.sqrt((P[:, 0] / RX) ** 2 + ((P[:, 1] - YC) / RY) ** 2)
        z = P[:, 2]
        tb = smooth(0.0, 0.6, (P[:, 1] - YC) / RY)   # 0＝脖子中心往前（喉嚨、下顎那側），1＝後頸
        rho = rho * (1 - tb) + rho / np.interp(z, LV, REF) * tb
        wr = 1 - smooth(R_FULL, R_ZERO, rho)
        below = smooth(RZ - Z_BELOW_ZERO, RZ - Z_BELOW_FULL, z)
        wz_f = np.where(z < RZ - Z_BELOW_FULL, below, np.where(z > ZF, 1 - smooth(ZF, ZF + Z_ABOVE, z), 1.0))
        wz_b = np.where(z < RZ - Z_BELOW_FULL, below, np.where(z > ZB, 1 - smooth(ZB, ZB + Z_BACK_FADE, z), 1.0))
        wz = wz_f * (1 - tb) + np.maximum(wz_f, wz_b) * tb
        w = wr * wz
        at = o.data.attributes
        for k in ("pocket_k", "pocket_t"):  # 口腔袋不動
            if k in at:
                v = np.array([d.value for d in at[k].data]); w[v > 0] = 0
        f = 1 - w * (1 - s)
        N = P.copy(); N[:, 0] = P[:, 0] * f; N[:, 1] = YC + (P[:, 1] - YC) * f
        D = N - P
        o.data.vertices.foreach_set("co", N.ravel())
        if o.data.shape_keys:
            for kb in o.data.shape_keys.key_blocks:
                kc = np.empty(len(P) * 3); kb.data.foreach_get("co", kc)
                kb.data.foreach_set("co", (kc.reshape(-1, 3) + D).ravel())
        o.data.update()
        mv = np.linalg.norm(D, axis=1)
        rep["objects"][name] = dict(moved=int((mv > 1e-5).sum()), max_move=round(float(mv.max()), 4))
        print("[slim] %s：動了 %d 點、最多 %.4f" % (name, (mv > 1e-5).sum(), mv.max()))
    after = float(np.ptp(section_xy(hd, RZ)[:, 0]))
    rep.update(width_after=round(after, 4), ratio_after=round(after / W, 3))
    print("[slim] 縮放 %.3f：環那層寬 %.4f → %.4f（脖子 ÷ 頭寬 %.3f → %.3f）" % (s, cur, after, ratio, after / W))
json.dump(rep, open(REP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
