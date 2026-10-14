# AI 網格路線 ② 眼睛自動偵測（第 2 段：找眼珠、量眼睛開口），系統 Python（PIL＋numpy）。
#   輸入 eyes_auto.py 渲的正面貼圖原色圖；輸出 ZEPETO_EYES 格式的五個數字（左眼 x、右眼 x、高度、半寬、半高）。
#   1. 找眼珠：深色、不偏藍的像素（頭髮偏藍：新娘臉旁髮絲把左眼跟整片頭髮連成一塊）→ 侵蝕 2 次（去掉細的眼線、髮絲）
#      → 連通塊 → 不要太扁、夠實心、旁邊有眼白 → 挑左右對稱、同高、同大小、面積大的一對（眉毛太扁先排除）
#   2. 量開口：眼珠中心那幾列，往左右走到「不是眼睛」（眼白＝很亮又不太有顏色、眼珠眼線＝暗）為止
#   3. 高度＝眼白上下範圍的中點；半高＝max(半寬 × 0.6, 眼珠半徑 × 0.9)（ZEPETO 杏仁眼高寬比約 0.64；圓眼要蓋住眼珠）
# 用法：python eyes_find.py <png> <json> [除錯圖]  → 印出一行 JSON：{"eyes": [xL, xR, z, ew, eh], "conf": ...}
import sys, json
import numpy as np
from PIL import Image, ImageDraw


def comps(mask):
    """連通塊（4 鄰），回傳 [像素索引陣列]"""
    H, W = mask.shape
    lab = np.zeros(mask.shape, np.int32)
    out = []
    ys, xs = np.nonzero(mask)
    for y0, x0 in zip(ys, xs):
        if lab[y0, x0]:
            continue
        n = len(out) + 1
        st = [(y0, x0)]; lab[y0, x0] = n; pts = []
        while st:
            y, x = st.pop(); pts.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < H and 0 <= xx < W and mask[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = n; st.append((yy, xx))
        out.append(np.array(pts))
    return out


def erode(m, it):
    for _ in range(it):
        m = m & np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1)
    return m


def find(png, meta, dbg=None):
    im = np.asarray(Image.open(png).convert("RGB"), float) / 255
    H, W = im.shape[:2]
    lum = im @ np.array([0.299, 0.587, 0.114])
    mx, mn = im.max(2), im.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    px_per = W / meta["size"]
    def to_w(px, py):  # 像素 → 世界 (x, z)
        return meta["cx"] + (px - W / 2) / px_per, meta["cz"] - (py - H / 2) / px_per
    # 搜尋範圍：頭的上半中段、中間 70% 寬
    r0, r1 = int(0.25 * H), int(0.6 * H)  # 頭頂往下 25%～60%（攝影師的眼睛在 50% 附近，0.5 會切掉下半）
    c0, c1 = int(0.15 * W), int(0.85 * W)
    dark = np.zeros((H, W), bool)
    blu = im[..., 2] - im[..., 0]
    dark[r0:r1, c0:c1] = (lum[r0:r1, c0:c1] < 0.32) & (blu[r0:r1, c0:c1] < 0.04)
    core = erode(dark, 2)
    cand = []
    for pts in comps(core):
        if len(pts) < 60:
            continue
        y_, x_ = pts[:, 0], pts[:, 1]
        h, w = np.ptp(y_) + 1, np.ptp(x_) + 1
        r = max(h, w) / 2
        fill = len(pts) / (np.pi * r * r)
        if 0.5 < w / h < 2.3 and fill > 0.2 and len(pts) > (0.018 * W) ** 2:  # 眼珠連著眼線不太實心（新娘 0.27）；太小的是眼尾、髮絲碎點
            # 旁邊要有眼白（左右各 2.2 個半徑內，顏色很淡又夠亮的比例）：眼睛 0.04～0.15，臉旁深色髮絲、下巴陰影是 0
            cx_, cy_, rr = x_.mean(), y_.mean(), np.sqrt(len(pts) / np.pi)
            yy = np.clip(np.arange(int(cy_ - rr), int(cy_ + rr)), 0, H - 1)
            xx = np.clip(np.arange(int(cx_ - 2.2 * rr), int(cx_ + 2.2 * rr)), 0, W - 1)
            wf = ((sat < 0.15) & (lum > 0.55))[np.ix_(yy, xx)].mean()
            if wf > 0.025:
                cand.append(dict(cx=cx_, cy=cy_, r=rr + 3, n=len(pts), white=round(float(wf), 3)))
    best, bs = None, 1e9
    for i in range(len(cand)):
        for j in range(len(cand)):
            a, b = cand[i], cand[j]
            if a["cx"] >= b["cx"]:
                continue
            mid = (a["cx"] + b["cx"]) / 2
            sym = abs(mid - W / 2) / W
            dz = abs(a["cy"] - b["cy"]) / H
            dr = abs(a["r"] - b["r"]) / max(a["r"], b["r"])
            gap = (b["cx"] - a["cx"]) / W
            if gap < 0.08 or gap > 0.45:
                continue
            s = sym * 4 + dz * 6 + dr - 0.3 * np.log(min(a["n"], b["n"]))
            if s < bs:
                bs, best = s, (a, b)
    if best is None:
        return None
    eyes = []
    blu_ = im[..., 2] - im[..., 0]
    eyeish = (sat < 0.15) | ((lum < 0.55) & (blu_ < 0.04))  # 眼白（顏色很淡；皮膚彩度約 0.3，陰影裡的眼白偏灰、不夠亮）或眼珠眼線（暗到中等、不偏藍＝不是頭髮）
    for e in best:
        rows = range(int(e["cy"] - 0.3 * e["r"]), int(e["cy"] + 0.3 * e["r"]) + 1)
        L, R = [], []
        for y in rows:
            for sgn, acc in ((-1, L), (1, R)):
                x, gap_ = int(e["cx"]), 0
                while 0 < x < W - 1 and gap_ <= 3:
                    x += sgn
                    gap_ = 0 if eyeish[y, x] else gap_ + 1
                acc.append(x - sgn * 4)
        xl, xr = np.median(L), np.median(R)
        eyes.append(dict(cx=(xl + xr) / 2, cy=e["cy"], hw=(xr - xl) / 2, r=e["r"]))
    # 高度：眼白上下範圍的中點（眼珠連著上眼線，重心偏高約 0.015 → 閉眼時下面露出一片眼白）
    for e in eyes:
        x0, x1 = int(e["cx"] - 0.9 * e["hw"]), int(e["cx"] + 0.9 * e["hw"])
        y0, y1 = int(e["cy"] - 2 * e["hw"]), int(e["cy"] + 2 * e["hw"])
        wm = (sat[y0:y1, x0:x1] < 0.15) & (lum[y0:y1, x0:x1] > 0.55)
        ys = np.nonzero(wm.any(1))[0]
        if len(ys) > 3:
            e["cy"] = y0 + (ys.min() + ys.max()) / 2
    (xa, za), (xb, zb) = to_w(eyes[0]["cx"], eyes[0]["cy"]), to_w(eyes[1]["cx"], eyes[1]["cy"])
    ew = 0.9 * (eyes[0]["hw"] + eyes[1]["hw"]) / 2 / px_per  # ×0.9：往左右走時連眼尾、眼頭的眼線一起算進去了（不扣的話程式眼白蓋過眼線、蓋到臉旁髮絲）
    # 畫面左＝角色右（-x）、畫面右＝角色左（+x）
    iris_r = (eyes[0]["r"] + eyes[1]["r"]) / 2 / px_per
    # 半高：ZEPETO 杏仁眼＝0.6 倍半寬；但至少要蓋住眼珠（0.9 倍眼珠半徑）——圓眼的頭（攝影師舊描述 large round eyes）
    #   只用 0.6 倍的話，睜眼時上下露出 AI 原本的黑眼珠邊、閉眼時蓋不滿、留一道 AI 畫的粗眼線弧
    eh = max(0.6 * ew, 0.9 * iris_r)
    res = dict(eyes=[float(round(v, 4)) for v in (xb, xa, (za + zb) / 2, ew, eh)],
               iris_r=round(iris_r, 4), score=round(bs, 4), n_cand=len(cand))
    if dbg:
        img = Image.open(png).convert("RGB"); d = ImageDraw.Draw(img)
        for c in cand:
            d.ellipse((c["cx"] - c["r"], c["cy"] - c["r"], c["cx"] + c["r"], c["cy"] + c["r"]), outline=(255, 255, 0))
        for e in eyes:
            d.ellipse((e["cx"] - e["hw"], e["cy"] - 0.6 * e["hw"], e["cx"] + e["hw"], e["cy"] + 0.6 * e["hw"]), outline=(0, 255, 0), width=2)
        img.crop((c0, r0, c1, r1)).save(dbg)
    return res


if __name__ == "__main__":
    r = find(sys.argv[1], json.load(open(sys.argv[2])), sys.argv[3] if len(sys.argv) > 3 else None)
    print(json.dumps(r))


def find_seam(png, meta, mL, mR, k=5):
    """唇縫高度：嘴巴中段每一欄找「比上下 k 像素都暗」最多的那一列（細線），取中位數。
    閉嘴微笑的唇縫是往下彎的 U 形，中間比嘴角低（攝影師低 0.037）；只用「紅色帶的中間高度」會切在上唇上緣、
    一張嘴整片下唇連皮膚像板子掉下來。回傳 (中央高度, 整條線[(x, z)], 信心＝細線平均有多暗)"""
    im = np.asarray(Image.open(png).convert("RGB"), float) / 255
    H, W = im.shape[:2]
    lum = im @ np.array([0.299, 0.587, 0.114])
    px = W / meta["size"]
    to_px = lambda x, z: (W / 2 + (x - meta["cx"]) * px, H / 2 - (z - meta["cz"]) * px)
    zk = (mL[2] + mR[2]) / 2; xc = (mL[0] + mR[0]) / 2; hw = (mL[0] - mR[0]) / 2
    y0, y1 = int(to_px(0, zk + 0.03)[1]), int(to_px(0, zk - 0.09)[1])
    line = []
    for x in np.linspace(xc - 0.85 * hw, xc + 0.85 * hw, 35):
        col = int(round(to_px(x, 0)[0]))
        lc = lum[:, col - 1:col + 2].mean(1)
        ys = np.arange(y0, y1)
        r = lc[ys] - 0.5 * (lc[ys - k] + lc[ys + k])
        y = ys[np.argmin(r)]
        line.append((float(x), float(meta["cz"] - (y - H / 2) / px), float(r.min())))
    line = np.array(line)
    cen = np.abs(line[:, 0] - xc) < 0.4 * hw
    return float(np.median(line[cen, 1])), line[:, :2].tolist(), float(-np.median(line[cen, 2]))
