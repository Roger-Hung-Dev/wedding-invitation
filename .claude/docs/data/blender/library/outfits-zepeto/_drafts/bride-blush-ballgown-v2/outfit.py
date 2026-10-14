# 新娘淡粉蓬裙禮服・細節版試做（2026-10-14）：照參考照刻出摺紗、斜向放射摺、腰間緞帶玫瑰與垂尾、
# 腰下歐根紗外層（正前方斜開口）、背後瀑布荷葉邊、三層蓬紗（照照片的蓬度）、背後大蝴蝶結、綁帶球鞋、花形耳環。
# 質感：寫實布料（2026-10-14 使用者從三種比較裡選定）。v1（黏土風）在 ../../bride-blush-ballgown/，已定案、動畫在用；
# 這版等新身形新娘身體出廠、長在新身體上後才換掉 v1（使用者經導演端決定）。
import os, sys, math
import garment_lib as G
import garment_detail as D
from mathutils import Vector

A = G.A
ARGS = dict(a.split("=", 1) for a in sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else {}
D.SIM = ARGS.get("SIM", "1") == "1"                         # 0＝不用布料模擬垂（比較用）

TOP = A["ARMPIT"] - 0.012                                   # 平口上緣：腋下 1.2 cm
WAIST = A["HIP_Z"] + 0.38 * (A["ARMPIT"] - A["HIP_Z"])      # 腰線（腰帶中心）
HEM = 0.022                                                  # 落地裙下襬離地 2.2 cm（新身形腳踝骨頭變高，所以從地面量、不從腳踝量）
R_HEM = 0.72 * WAIST                                         # 照片的蓬度：下襬寬約腰到地高度的 1.5 倍（2026-10-14 試過縮小成 A 字，使用者說質感變差，改回這版；手的位置交給動畫端：走路提裙、停下手放裙子兩側）
KNOT = Vector((0.035, 0, WAIST))                             # 腰間布花：角色左前方（照片在新娘左腰）

M = dict(
    organza=D.fabric("Gown_Organza", (242, 196, 198), "organza"),   # 上身、外層紗、荷葉邊、蝴蝶結（照片的淡粉）
    sash=D.fabric("Gown_Sash", (238, 186, 190), "satin"),          # 腰帶、玫瑰、垂帶，深一階
    tulle=D.fabric("Gown_Tulle", (248, 214, 214), "tulle"),        # 外面兩層紗，淺一階
    lining=D.fabric("Gown_Lining", (244, 202, 204), "lining"),
    shoe=D.fabric("Gown_Shoe", (246, 228, 224), "canvas"),         # 照片裙底露出的淡粉白球鞋
    silver=D.fabric("Gown_Silver", (214, 214, 220), "metal"),
)

EXTRA_CLOSEUPS = [
    ("bow", lambda A, g: Vector((0, 0.10, WAIST - 0.10)), 1.0, (180, 135, -135)),
    ("cascade", lambda A, g: Vector((0, 0.05, WAIST - 0.25)), 1.5, (90, 135, -90)),
    ("knot", lambda A, g: Vector((KNOT.x, -0.1, WAIST - 0.03)), 0.55, (0, 25)),
    ("earring", lambda A, g: g("J_Bip_C_Head") + Vector((0, 0, 0.02)), 0.5, (90, -90)),
]


def covered(c):
    return c.z < TOP - 0.012


def build():
    lining = D.tulle_layer("Gown_Lining", "lining", WAIST - 0.01, HEM + 0.006, R_HEM - 0.02, bell=2.0, folds=(9, 14), fold_amp=0.008, seed=1)
    tulle1 = D.tulle_layer("Gown_Tulle1", "tulle", WAIST - 0.008, HEM + 0.002, R_HEM, bell=2.1, folds=(13, 19, 29), fold_amp=0.016, seed=2)
    tulle2 = D.tulle_layer("Gown_Tulle2", "tulle", WAIST - 0.006, HEM, R_HEM + 0.022, bell=2.2, folds=(11, 17, 23, 31), fold_amp=0.022,
                           hem_wave=0.012, seed=3)
    for o in (lining, tulle1, tulle2):
        o.data.materials.append(M[o["role"]])
    bodice = D.draped_bodice("Gown_Bodice", M["organza"], TOP, WAIST - 0.04, KNOT)
    neck = D.rolled_neckline("Gown_Neckline", M["organza"], bodice, TOP)
    wrap = D.wrap_fold("Gown_Wrap", M["organza"], bodice, (-0.10, TOP - 0.012), (0.045, WAIST + 0.035))
    pep = D.peplum("Gown_Peplum", M["organza"], WAIST + 0.004, tulle2, length=0.30)
    tiers = []
    for k, (zt, ln, span) in enumerate(((WAIST - 0.10, 0.20, 3.4), (WAIST - 0.24, 0.20, 3.0), (WAIST - 0.38, 0.21, 2.6), (WAIST - 0.52, 0.22, 2.2))):
        tiers.append(D.cascade(f"Gown_Cascade{k + 1}", M["organza"], tulle2, zt, ln, span, seed=k * 1.7, colliders=[pep, *tiers],
                               wave_len=0.14, amp=0.055, drop_back=0.07))          # 往後斜著往下、大圓捲（照片側面的瀑布摺）
    sash = G.sash("Gown_Sash", M["sash"], WAIST, width=0.034, ease=0.026); sash["role"] = "sash"
    rose = D.ribbon_rose("Gown_Rose", M["sash"], sash, KNOT.x, KNOT.z, size=0.07, turns=2.8)
    tails = D.ribbon_tails("Gown_RoseTails", M["sash"], [pep, tulle2], KNOT.x, KNOT.z - 0.03, 0.30, weight_src=pep)
    bow = D.ribbon_bow("Gown_BackBow", M["organza"], sash, WAIST, size=0.18, ribbon=0.075)
    btails = D.ribbon_tails("Gown_BowTails", M["organza"], [pep, *tiers, tulle2], 0.0, WAIST - 0.03, 0.42,
                            ends=((-0.09, 0.4), (0.09, 2.1)), width=0.06, back=True, weight_src=tulle2)
    shoes = G.shoes("Gown_Shoes", M["shoe"], toe=0.010); shoes["role"] = "shoe"
    laces = G.laces("Gown_Laces", M["shoe"], shoes); laces["role"] = "shoe"
    ear = G.flower_earrings("Gown_Earrings", M["silver"]); ear["role"] = "silver"
    # 給動畫端：提裙掛點（外層紗＋荷葉邊一起被拉）、裙面半徑表（存在 outfit.blend 的場景屬性，產生器另存成 skirt_radius.json）
    import json
    grips = D.skirt_grips([pep, *tiers], pep, z=A["HIP_Z"] - 0.024)        # 抓點高度：髖關節下 2.4 cm（v3 約 0.60 m，手腕走路時的高度）
    table = D.skirt_radius_table([lining, tulle1, tulle2, pep, *tiers, tails, btails])
    G.sc["gown_handoff"] = json.dumps(dict(grips=grips, skirt_radius=table), ensure_ascii=False)
    # 每次重長都寫回 outfit.json 的 anim_handoff（動畫端從這裡讀；換身體重長後數字自動更新）
    jp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outfit.json")
    meta = json.load(open(jp, encoding="utf-8"))
    ah = meta.setdefault("anim_handoff", {})
    ah["body_blend"] = G.bpy.data.filepath
    ah.setdefault("skirt_radius", {}).update(center=table["center"], rows=table["rows"])
    for side, info in grips.items():
        ah.setdefault("grips", {})[side] = info
    json.dump(meta, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if ARGS.get("OUT"):
        json.dump(dict(grips=grips, skirt_radius=table), open(os.path.join(ARGS["OUT"], "skirt_handoff.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return [lining, tulle1, tulle2, bodice, neck, wrap, pep, *tiers, sash, rose, tails, bow, btails, shoes, laces, ear]
