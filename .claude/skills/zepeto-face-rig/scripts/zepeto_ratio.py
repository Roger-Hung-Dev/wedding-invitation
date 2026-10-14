# ZEPETO 比例量測（2026-10-14）：量這顆頭離 ZEPETO 官方比例多遠，寫 zepeto_ratio.json（產線在 rig 步驟、接口環之後跑）。
#   只是參考數字、不擋產線；脖子寬有目標範圍（NECK_TARGET），超出時報告標紅。參考值出處見 references/research-zepeto-face.md
#   「ZEPETO 臉特徵表」（預設光頭臉正面、兒童預設，誤差約 ±5%；成人 PRO 另列）與身體端研究（脖子）。
#   量法（座標都是 Head 本地座標＝頭檔座標，臉朝 −Y）：
#   - H（頭頂不含頭髮到下巴）：AI 頭的頭頂被頭髮蓋住量不到 → 用眼睛高度推：ZEPETO 眼睛在下巴往上 40%，H＝(眼睛高度 − 下巴) ÷ 0.40
#     （所以「眼睛高度」這一項不量；換別的推法要一起改參考值）
#   - 頭寬 W：Head 物件（不含頭髮 Hair、耳朵 Ears）下巴往上 0.3H 以上，每 1 cm 一層的左右寬取最大
#   - 下巴往上 5%、10% 的臉寬：那一層（±0.006）Head 上、在脖子中心前面（y < neck_ring_yc）的點的左右寬；
#     只取前半是為了不量到後面的脖子、後頸墊底皮
#   - 眼寬、兩眼間距：eyes.json（找眼珠時量的眼睛開口，[左x, 右x, 高度, 半寬, 半高]）；嘴寬：landmarks.json 嘴角
#   - 脖子寬：接口環（neck_ring 1～48）的左右寬，也就是身體脖子頂端的寬
# 用法：blender -b ring.blend -P zepeto_ratio.py -- <landmarks.json> <eyes.json> <輸出 zepeto_ratio.json>
import bpy, sys, os, json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zmeasure import EYE_FROM_CHIN, head_H, head_width

a = sys.argv[sys.argv.index("--") + 1:]
LM = json.load(open(a[0], encoding="utf-8")); EY = json.load(open(a[1], encoding="utf-8")); OUT = a[2]
NECK_TARGET = (0.35, 0.40, float(os.environ.get("NECK_TARGET", "0.38")))  # 脖子寬 ÷ 頭寬：容許下限、上限、修細目標（2026-10-14 和身體端對齊）
# 參考值：(兒童預設, 成人 PRO 或 None, 說明)
REF = {
    "jaw5":   (0.28, None, "下巴往上 5% 處的臉寬 ÷ H"),
    "jaw10":  (0.39, None, "下巴往上 10% 處的臉寬 ÷ H"),
    "width":  (1 / 1.29, None, "頭寬 ÷ H（ZEPETO 頭高寬比 1.29）"),
    "eye_w":  (0.29, 0.21, "眼寬 ÷ 頭寬"),
    "eye_d":  (0.56, 0.51, "兩眼中心距 ÷ 頭寬"),
    "mouth":  (0.36, None, "嘴寬 ÷ 頭寬"),
}

hd = bpy.data.objects.get("Head") or bpy.data.objects["AI_Driven"]
me = hd.data
co = np.array([v.co[:] for v in me.vertices])
chin = LM["chin_z"]
eL, eR, ez, ehw = EY["eyes"][0], EY["eyes"][1], EY["eyes"][2], EY["eyes"][3]
H = head_H(chin, ez)
yc = hd.get("neck_ring_yc")
if yc is None:  # 沒有接口環的頭：用下巴那層的前後中點
    band = co[np.abs(co[:, 2] - chin) < 0.02]
    yc = float((band[:, 1].min() + band[:, 1].max()) / 2) if len(band) else 0.0


def width_at(z, front=True, half=0.006):
    s = co[(np.abs(co[:, 2] - z) < half) & ((co[:, 1] < yc) if front else True)]
    return float(np.ptp(s[:, 0])) if len(s) > 3 else None


W, Wz = head_width(co, chin, H)  # 0.3H 以上每 1 cm 一層取最大

ring = me.attributes.get("neck_ring")
neck = None
if ring is not None:
    rv = np.array([d.value for d in ring.data])
    if (rv > 0).sum() >= 8:
        neck = float(np.ptp(co[rv > 0][:, 0]))

ml, mr = LM["mouth"]["L"], LM["mouth"]["R"]
val = {
    "jaw5": (width_at(chin + 0.05 * H) or 0) / H,
    "jaw10": (width_at(chin + 0.10 * H) or 0) / H,
    "width": W / H,
    "eye_w": 2 * ehw / W,
    "eye_d": abs(eL - eR) / W,
    "mouth": abs(ml[0] - mr[0]) / W,
}
items = {}
for k, (ref, adult, label) in REF.items():
    v = val[k]
    items[k] = dict(label=label, value=round(v, 3), zepeto=round(ref, 3), zepeto_adult=adult,
                    vs_zepeto=round(v / ref, 2))
nlo, nhi, ntg = NECK_TARGET
items["neck"] = dict(label="脖子寬（接口環左右寬）÷ 頭寬", value=round(neck / W, 3) if neck else None,
                     target=[nlo, nhi], slim_to=ntg,
                     ok=(nlo - 0.005 <= neck / W <= nhi + 0.005) if neck else None)
out = dict(H=round(H, 4), head_w=round(W, 4), head_w_z=round(Wz, 3), neck_w=round(neck, 4) if neck else None,
           chin=round(chin, 4), eye_z=round(ez, 4), neck_yc=round(yc, 4), eye_from_chin=EYE_FROM_CHIN, items=items)
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k, it in items.items():
    if k == "neck":
        print("[zepeto] %-32s %s（目標 %.2f～%.2f）%s" % (it["label"], it["value"], nlo, nhi, "" if it["ok"] else "  ← 超出"))
    else:
        print("[zepeto] %-32s %.3f（ZEPETO %.3f%s，×%.2f）" % (it["label"], it["value"], it["zepeto"],
              "、成人 %.2f" % it["zepeto_adult"] if it["zepeto_adult"] else "", it["vs_zepeto"]))
print("[zepeto] H %.3f（眼睛推算）、頭寬 %.3f（z=%.2f）、脖子寬 %s" % (H, W, Wz, out["neck_w"]))
