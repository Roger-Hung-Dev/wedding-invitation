# ③ 推紅毯（7.74 秒）。2026-10-10 Mixamo 版第 1 關（骨骼）。
# 站位、鏡頭照現行 v2_03c（shots_v2_s03carpet.py）：鏡頭固定 (6.3, −3.3, 1.75) 看 (0, −1.35, 0.72)、34 mm（從 +X 側面看）；
#   新郎 0 秒骨盆 (0.052, −2.307)、面向 180（+Y，往拱門推）；新娘從新郎左後方跑來，推他左側腰背，最後兩人轉向鏡頭揮手。
# 2026-10-10 使用者改設計：「相遇、交往、求婚、婚禮」改回第一版——平貼在紅地毯上（不要立體文字牆），也不要石頭。
#   字照第一版的規格：霞鶩文楷、字高 0.26 m（婚禮 ×1.25）、香檳奶油色 #F6E7C8、紅毯中線往鏡頭側偏 0.24 m、字順著 +Y 讀；
#   位置重排（第 4 輪的推法照舊公式會疊字）：四個字沿紅毯平均排開，紅毯卷滾過字中心＋0.13 m 那一刻字才出現。
# Mixamo 的推重物動畫手都在離地 0.9～1.0 m，所以紅毯卷要比現行版大（半徑約 0.45 m，第一版是 0.52），手才碰得到。
import math

# 起點比現行版往後 0.8 m（推的路程拉長到約 2.5 m，三個字才排得下不重疊；開場時新郎仍在畫面左側）
BACK = 0.8
# 2026-10-11 第 3 關第 3 輪回饋「紅地毯可以做寬一點，人改踩在沒有字的紅地毯上做一系列動作」：
#   原本紅毯寬 0.95 m、字在 x 0.24，新郎的腳踩到 x 0.45、新娘的蓬裙蓋到 x 0.83 → 人一直踩在字上。
#   紅毯加寬到 1.6 m（x ±0.8；收在拱門柱 ±0.96、柱下玫瑰 x 0.9 之內，卷子滾到拱門前不會撞到）；
#   兩人整組往遠離鏡頭那側（−X）挪 0.35 m，字改排在靠鏡頭那側 x 0.57：新郎的腳最遠到 x 0.10、新娘的蓬裙到 0.47，都不碰字
DX = -0.35
CARPET_W = 1.6                           # 紅毯寬（中心 x 0；紅毯卷一樣寬、軸心固定在 x 0，不再跟著新郎的骨盆左右）
TEXT_X = 0.57                            # 字的中心線（靠鏡頭那側）
G0, G_FACE = (0.052 + DX, -2.307 - BACK), 180.0
CARPET_Y0 = -2.748 - BACK                # 紅毯起點（開場就鋪好的那端）
ROLL_END = 0.02                          # 紅毯卷最後停的位置（拱門前，現行版）
ROLL_R = 0.52                            # 第一版的大小；Mixamo 推的手在離地約 1.0 m，卷子小的話手碰不到
# 四個字：「相遇」開場就在鋪好的紅毯上；其他三個沿卷子滾過的路平均排開（最後一個要在卷子停下時壓不到的地方），卷子滾過字中心＋0.13 m 才出現
WORDS = [("相遇", 0.26), ("交往", 0.26), ("求婚", 0.26), ("婚禮", 0.325)]   # 字高；兩個字順著紅毯長 2×字高


# ════════ 第 2 關「正式版骨骼」的微調（FINAL=1 才套；2026-10-10）════════
FINAL = OPT.get("FINAL") == "1"
ROLL_PATH = []                         # 第 2 關：mod 照「原片的手」算出紅毯卷每格的圓心，post 直接用（手貼上去之後不再回頭改卷子）


def win(t, a, b, c, d):
    def sm(x):
        x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
    if t <= a or t >= d:
        return 0.0
    if t < b:
        return sm((t - a) / max(1e-6, b - a))
    if t <= c:
        return 1.0
    return 1.0 - sm((t - c) / max(1e-6, d - c))


T_RELEASE = 3.3                         # 新郎放手（推動往前衝那段結束）


def drop_arms(R, h, w, tgt_name="groom"):
    """雙手放下、垂在身體兩側稍微前面一點（放手之後用；w＝權重）"""
    if w <= 0:
        return R
    G = tgt(tgt_name)
    for s_, sg in (("L", 1.0), ("R", -1.0)):
        Hd = G.fk(R, h)
        side = Hd["J_Bip_L_UpperLeg"] - Hd["J_Bip_R_UpperLeg"]; side.z = 0; side.normalize()
        fwd = Vector((side.y, -side.x, 0))
        sh = Hd[f"J_Bip_{s_}_UpperArm"]
        arm = (G.rest_h[f"J_Bip_{s_}_LowerArm"] - G.rest_h[f"J_Bip_{s_}_UpperArm"]).length + (G.rest_h[f"J_Bip_{s_}_Hand"] - G.rest_h[f"J_Bip_{s_}_LowerArm"]).length
        hang = sh + Vector((0, 0, -arm * 0.93)) + fwd * 0.10 + side * (sg * 0.06)
        start = Hd[f"J_Bip_{s_}_Hand"]
        R = arm_ik(G, R, h, s_, start.lerp(hang, w), fwd * -0.3 + side * sg)
        H2 = G.fk(R, h)
        cur = (H2[f"J_Bip_{s_}_Middle1"] - H2[f"J_Bip_{s_}_Hand"]).normalized()
        R = aim_hand(G, R, h, s_, cur.lerp(Vector((0, 0, -1)) + fwd * 0.15, w), palm=(side * -sg), palm_w=w)
    return R


def groom_mod():
    """新郎雙手掌心平貼紅毯卷面（第 4 輪回饋「手的虎口角度是否正確」→ 使用者選「第 2 關把手貼平卷面」）：
    手碰卷子的位置照原片（手掌投影到卷面），掌心朝卷心、手指順著弧面往前往上、拇指自然朝內；手肘往外下方彎"""
    G = tgt("groom"); state = dict(y=-9.0)

    def mod(t, R, h):
        Hd = G.fk(R, h)
        # 1) 卷子的位置（第 3 關回饋「推的時候腳進入到紅地毯裡面」→ 2026-10-11 改）：
        #    a. 照原片的手：手貼在卷子背面（手舉得比卷頂還高時這條會算出「不用往前」，所以只當下限之一）
        #    b. 卷子背面一定在新郎膝蓋、腳尖前面（膝蓋留 8 cm、腳尖留 5 cm）：他往前走，卷子就被推著走
        #    取兩者較大、而且只往前不往後
        Cz = ROLL_R + 0.018
        hy = 0.5 * (Hd["J_Bip_L_Hand"].y + Hd["J_Bip_R_Hand"].y); hz = 0.5 * (Hd["J_Bip_L_Hand"].z + Hd["J_Bip_R_Hand"].z)
        sa = max(-1.0, min(1.0, (hz - Cz) / ROLL_R))
        need = hy + ROLL_R * math.sqrt(1 - sa * sa)
        legs = [(Hd["J_Bip_L_LowerLeg"], 0.08), (Hd["J_Bip_R_LowerLeg"], 0.08),
                (G.tail(R, Hd, "J_Bip_L_ToeBase"), 0.05), (G.tail(R, Hd, "J_Bip_R_ToeBase"), 0.05)]
        for p, m in legs:
            dz = p.z - Cz
            if abs(dz) < ROLL_R + m:
                need = max(need, p.y + math.sqrt(max(0.0, (ROLL_R + m) ** 2 - dz * dz)))
        if t <= T_RELEASE:
            state["y"] = max(state["y"], need)
            ROLL_PATH.append((t, Hd["J_Bip_C_Hips"].x, state["y"]))
            state["y_rel"] = state["y"]
        else:                                    # 放手後：照 post 的同一條減速曲線自己滾到拱門前（手跟著送一小段）
            u = min(1.0, (t - T_RELEASE) / 1.3)
            state["y"] = state["y_rel"] + (ROLL_END - state["y_rel"]) * (1 - (1 - u) ** 2)
        # 2) 手：一路貼著卷子推；放手（3.3 秒）後手繼續貼著往前送，直到手臂伸直構不到（第 3 關回饋「最後推出去時雙手向下壓，
        #    而不是順著往前推」），3.55 秒起掌心離開卷面、3.65 秒起才放下手
        w = win(t, -1, 0, T_RELEASE + 0.25, T_RELEASE + 0.4)
        lift = 0.06 * win(t, T_RELEASE + 0.2, T_RELEASE + 0.4, 99, 100)
        R = drop_arms(R, h, win(t, T_RELEASE + 0.35, T_RELEASE + 0.8, 4.5, 4.85))
        if w <= 0:
            return R
        C = Vector((0, state["y"], ROLL_R + 0.018))
        fwd = Vector((0, 1, 0))
        for s_, sg in (("L", 1.0), ("R", -1.0)):
            H2 = G.fk(R, h)
            palm = (H2[f"J_Bip_{s_}_Hand"] + H2[f"J_Bip_{s_}_Middle1"]) * 0.5
            out = Vector((0, palm.y - C.y, palm.z - C.z)); out.normalize()
            tang = Vector((0, out.z, -out.y))
            if tang.dot(fwd) < 0:
                tang = -tang
            contact = Vector((palm.x, C.y, C.z)) + out * (ROLL_R + 0.012 + lift)   # 掌心貼在卷面外 1.2 cm（手掌厚度）；放手時往外抬
            wrist = contact - tang * 0.055                                      # 手腕在掌心中點後面約 5.5 cm
            start = H2[f"J_Bip_{s_}_Hand"]
            # 2026-10-11 第 3 關自我審查：原本手肘方向寫 (sg, −0.3, −0.6)，但新郎面向 +Y 時左手在 −X，左手肘被指向身體內側
            #   → 兩手肘往內夾、前臂交叉（重疊 8 cm）、上臂扭 −157°。改用身體的左右方向：手肘往外、往下、稍微往後
            lside = H2["J_Bip_L_UpperLeg"] - H2["J_Bip_R_UpperLeg"]; lside.z = 0; lside.normalize()
            R = arm_ik(G, R, h, s_, start.lerp(wrist, w), lside * (sg * 0.6) - fwd * 0.3 + Vector((0, 0, -0.8)))
            H3 = G.fk(R, h)
            cur = (H3[f"J_Bip_{s_}_Middle1"] - H3[f"J_Bip_{s_}_Hand"]).normalized()
            R = aim_hand(G, R, h, s_, cur.lerp(tang, w), palm=(-out), palm_w=w)
            R = gesture(G, R, s_, "flat", w=w)
        return R
    return mod


def bride_mod():
    """新娘雙手貼在新郎背上（第 2 輪起的回饋；第 1 關左手在新郎衝出去時穿進背 17 cm）：
    每格找新郎背面離她掌心最近的點，把手腕挪過去、掌心朝向他、手指朝上；要挪超過 15 cm 才碰得到時就慢慢放開"""
    B = tgt("bride"); DEPTH = 0.12
    SP = ["J_Bip_C_Hips", "J_Bip_C_Spine", "J_Bip_C_Chest", "J_Bip_C_UpperChest", "J_Bip_C_Neck"]

    def back_point(gp, p):
        side = gp["J_Bip_L_UpperLeg"] - gp["J_Bip_R_UpperLeg"]; side.z = 0; side.normalize()
        fwd = Vector((side.y, -side.x, 0))
        u = (gp["J_Bip_C_Neck"] - gp["J_Bip_C_Hips"]).normalized()
        back = -fwd + u * fwd.dot(u); back.normalize()
        best = None
        for a, b in zip(SP, SP[1:]):
            A, Bp = gp[a], gp[b]; ab = Bp - A
            k = max(0.0, min(1.0, (p - A).dot(ab) / max(1e-9, ab.dot(ab))))
            c = A + ab * k
            v = p - c; lat = v - back * v.dot(back)
            if lat.length > 0.15:
                lat = lat.normalized() * 0.15                                   # 背寬一半約 0.15 m
            q = c + back * DEPTH + lat
            if best is None or (q - p).length < (best[0] - p).length:
                best = (q, back, u)
        return best

    def mod(t, R, h):
        w0 = win(t, 1.55, 1.8, 3.0, 3.35)
        if w0 <= 0:
            return R
        gp = BUILT["groom"][min(len(BUILT["groom"]) - 1, int(round(t * 30)))]
        for s_ in ("L", "R"):
            H2 = B.fk(R, h)
            palm = (H2[f"J_Bip_{s_}_Hand"] + H2[f"J_Bip_{s_}_Middle1"]) * 0.5
            q, back, u = back_point(gp, palm)
            move = (q + back * 0.012) - palm
            w = w0 * max(0.0, min(1.0, (0.20 - move.length) / 0.05))           # 要挪 15 cm 以上開始放開、20 cm 完全放開
            if w <= 0:
                continue
            R0, start = R, H2[f"J_Bip_{s_}_Hand"]
            wrist = start + move * w
            for _ in range(3):                                                  # 手轉過之後掌心又會偏一點，再修兩次
                R = arm_ik(B, R0, h, s_, wrist, Vector((0, 0, -1)) + back * 0.3)
                H3 = B.fk(R, h)
                cur = (H3[f"J_Bip_{s_}_Middle1"] - H3[f"J_Bip_{s_}_Hand"]).normalized()
                R = aim_hand(B, R, h, s_, cur.lerp(u, w), palm=(-back), palm_w=w)
                R = gesture(B, R, s_, "flat", w=w)
                H4 = B.fk(R, h)
                p2 = (H4[f"J_Bip_{s_}_Hand"] + H4[f"J_Bip_{s_}_Middle1"]) * 0.5
                q2, back2, _u = back_point(gp, p2)
                wrist = wrist + ((q2 + back2 * 0.012) - p2) * w
        return R
    return mod


def scene():
    groom = dict(segs=[
        S("groom", "push_start", 1.0, 3.8, label="慢慢推、越推越吃力（Start To Push A Heavy Object 1.0～3.8 秒）"),
        S("groom", "push_heavy", 2.0, 3.1, label="推動了往前衝（Pushing Heavy Object 2.0～3.1 秒）"),
        S("groom", "push_heavy", 5.8, 7.4, label="停下、站直（Pushing Heavy Object 5.8～7.4 秒）"),
        S("groom", "turn_right_90", 0.8, 2.0, add=True, label="右轉面向鏡頭（Quick 90 Degree Right Turn，只取腳步和轉向）"),
        S("groom", "waving_both_hands", 0.2, 3.0, label="雙手揮手（Waving With Both Hands）"),
    ], anchor=(0.0, G0, G_FACE), mod=groom_mod() if FINAL else None)
    bride = dict(segs=[
        # 2026-10-10 第 1 輪回饋「應該是跑步過來急停」→ 下載 Female Run Forward（使用者同意）；一步週期 0.63 秒、約 4.4 m/s。
        # 0.52 秒才起跑（之前在畫面外停著），跑完急停的時間點和上一版一樣（約 1.75 秒），推背的接觸不變
        # 2026-10-11 第 3 關自我審查：接段時急停會提前 0.3 秒和跑步重疊，跑步「結束前 0.3 秒」那格跟急停第一格是相反的腳步（差 23 cm），
        #   混出伸直的腿＋蹲低的骨盆 → 腳尖陷進地板 15 cm、骨盆 0.07 秒掉 16 cm。跑步多跑半步（1.47 圈，結束前 0.3 秒＝第 18 格，
        #   和急停第一格差 2.5 cm）、提早 0.28 秒起跑，急停、推人的時間都不變（tools/phase_match.py）
        S("bride", "female_run", loops=1.47, at=0.24, label="跑過來（Female Run Forward）"),
        S("bride", "run_fast_stop", 0.0, None, label="跑步急停（Fast Stop From Full Run）"),
        # 2026-10-10 第 2 輪回饋「新娘提早恢復站姿，新郎還在推」、第 3 輪「新娘沒有真的推出去，只有在原地」→
        #   推到新郎推不動那段結束（停在 1.3 秒那一格等），2.5 秒新郎推動時接著播同一支的 1.3～2.4 秒：邊推邊跟著往前走幾步，再放手
        S("bride", "push_heavy", 0.5, 1.3, label="雙手推新郎的背（Pushing Heavy Object 0.5～1.3 秒）"),
        S("bride", "push_heavy", 1.3, 2.4, at=2.5, label="推著他往前走（Pushing Heavy Object 1.3～2.4 秒）"),
        S("bride", "push_heavy", 6.9, 7.6, label="放手站直（Pushing Heavy Object 6.9～7.6 秒）"),
        S("bride", "turn_right_90", 0.8, 2.0, at=4.3, add=True, label="右轉面向鏡頭（Quick 90 Degree Right Turn，只取腳步和轉向）"),
        S("bride", "waving_both_hands", 0.2, 3.0, label="雙手揮手（Waving With Both Hands）"),
    ], anchor=("end:1", (0.13 + DX, -2.54 - BACK), 160.0), mod=bride_mod() if FINAL else None)   # 2026-10-10 第 1 輪回饋「手沒碰到背」：contact_fit.py 找的站位（推的 1.8～2.4 秒雙掌離背面 ≤ 5.5 cm）
    cam = dict(pos=[6.3, -3.3, 1.75], aim=[0.0, -1.35, 0.72], lens=34.0, sensor=36.0, aspect=16 / 9)
    return dict(id="03", title="③ 推紅毯", dur=7.74, chars=dict(groom=groom, bride=bride), props=garden_props(), cam=cam,
                skirt=dict(who="bride", r_floor=0.70, r_waist=0.16, h_waist=0.98), post=post,
                note="紅色圓柱是紅毯卷（跟著新郎的手往前滾，放手後自己滾到停），金色字是平貼在紅毯上的四個階段，卷子滾過才出現。"
                     "段與段之間 0.3 秒漸變，動作本身沒有改。",
                decide=DECIDE_FINAL if FINAL else ["字照你說的改回平貼在紅地毯上、拿掉石頭。四個字的位置重排：「相遇」開場就在鋪好的那段，「交往」1.7 秒、「求婚」3.5 秒、「婚禮」3.8 秒在卷子滾過時出現，字和字之間約 10 cm 不重疊。",
                        "推的路程拉長：新郎起點比現行版往後 0.8 m，卷子從約 −2.5 推到拱門前（y 0.02），三個字才排得下。開場時新郎在畫面左側。",
                        "紅毯卷改大：半徑 0.52 m（第一版的大小；現行版 0.30）。Mixamo 推重物時手在離地約 1.0 m，卷子小手會碰不到。",
                        "節奏照 Mixamo：0～2.5 秒越推越吃力（身體越壓越低，代替「推不動」）、2.5 秒推動往前衝、3.3 秒放手、卷子自己滾到拱門前 4.6 秒停；5.5 秒轉向鏡頭揮手。現行版是 3.05 秒推動。",
                        "新娘跑過來（照你第 1 輪的回饋改）：前段換成 Mixamo「Female Run Forward」，跑一步就接「跑步急停」，1.75 秒停下。",
                        "新娘推新郎的背：站在新郎正後方，1.5 秒開始推；2.5 秒新郎推動時，她接著同一支動畫邊推邊往前走約 0.3 m（照你第 3 輪的回饋改），3.3 秒才放手站直。1.8～3.0 秒右手離他的背 ±4 cm 內，之後新郎衝得比她快、手慢慢分開。",
                        "2.7～3.0 秒新郎推動時身體會往她左手那側扭，她的左手會穿進他背後最多約 17 cm（約 0.3 秒）；調站位也只能減到 15 cm。這要靠「手跟著貼在背上」的微調，放到下一關「正式版骨骼」處理。",
                        "新娘站在新郎正後方、兩人骨盆只差約 0.5 m：她的蓬裙範圍（圓錐）會蓋到新郎的腳，第 2 關要處理（現行版是推的時候把裙子往另一側壓扁）。",
                        "揮手換成 Mixamo「雙手揮手」：手舉過頭左右揮（現行版是在臉旁水平劃弧）。新郎轉完面向 78°，正對鏡頭是 71°。"])


def post(out):
    """照新郎雙手的位置算紅毯卷的路徑（手貼在卷子背面、卷子只往前不往後），放手後減速滾到停；再放紅毯與平貼字"""
    fps = out["fps"]; g = out["chars"]["groom"]; b = g["bones"]
    iL, iR, iH = b.index("J_Bip_L_Hand"), b.index("J_Bip_R_Hand"), b.index("J_Bip_C_Hips")
    labels = g["labels"]
    rush_end = max(i for i, l in enumerate(labels) if l.startswith("推動了")) / fps
    path = []; y_max = -9.0; x = 0.0
    if ROLL_PATH:                                         # 第 2 關：照原片的手算好的（手貼上去之後不回頭改卷子）
        rush_end = T_RELEASE
        for k, (t_, x_, y_) in enumerate(ROLL_PATH):
            if t_ <= rush_end and k % 3 == 0:
                path.append([round(t_, 3), 0.0, round(y_, 3), ROLL_R + 0.018]); x = 0.0
    for i, fr in enumerate(g["frames"] if not ROLL_PATH else []):
        t = i / fps
        if t > rush_end:
            break
        hy = 0.5 * (fr["p"][iL][1] + fr["p"][iR][1]); hz = 0.5 * (fr["p"][iL][2] + fr["p"][iR][2]); x = 0.0
        sa = max(-1.0, min(1.0, (hz - 0.018 - ROLL_R) / ROLL_R))          # 手貼在卷子背面：離圓心水平距離 r·cos a
        y_max = max(y_max, hy + ROLL_R * math.sqrt(1 - sa * sa))
        if i % 3 == 0:
            path.append([round(t, 3), round(x, 3), round(y_max, 3), ROLL_R + 0.018])
    t0, y0 = path[-1][0], path[-1][2]
    T_STOP = 1.3                                          # 放手後自己滾到拱門前停（現行版停在 y 0.02），減速曲線 1−(1−u)²
    for k in range(1, 14):
        u = k / 13; tt = t0 + T_STOP * u
        path.append([round(tt, 3), round(x, 3), round(y0 + (ROLL_END - y0) * (1 - (1 - u) ** 2), 3), ROLL_R + 0.018])
    y_end = path[-1][2]
    out["props"] += [
        dict(kind="box", name="紅毯（鋪開的範圍）", min=[-CARPET_W / 2, CARPET_Y0, 0.0], max=[CARPET_W / 2, y_end - ROLL_R, 0.012], color="#B23A48", opacity=0.55),
        dict(kind="cyl", axis="x", name="紅毯卷", c=[x, path[0][2], ROLL_R + 0.018], r=ROLL_R, len=CARPET_W, color="#B23A48", opacity=0.5, path=path),
    ]
    def y_at(t):
        for a_, b_ in zip(path, path[1:]):
            if a_[0] <= t <= b_[0]:
                return a_[2] + (b_[2] - a_[2]) * (t - a_[0]) / max(1e-6, b_[0] - a_[0])
        return path[-1][2]
    placed = []
    y_lo, y_hi = path[0][2] + 0.05, y_end - ROLL_R - 0.03        # 卷子滾過、而且最後不會壓到的範圍
    rest = WORDS[1:]; need = sum(2 * z for _, z in rest); gap = max(0.0, (y_hi - y_lo - need) / (len(rest) - 1))
    spots = [(WORDS[0][0], 0.5 * (CARPET_Y0 + path[0][2] - ROLL_R), WORDS[0][1])]     # 開場就鋪好的那段的正中間
    y = y_lo
    for word, z in rest:
        spots.append((word, y + z, z)); y += 2 * z + gap
    for word, wy, z in spots:
        on = next((p[0] for p in path if p[2] >= wy + 0.13), 0.0) if wy > path[0][2] else 0.0
        placed.append((word, round(wy, 2), on))
        out["props"].append(dict(kind="text", name=word, text=word, c=[TEXT_X, wy, 0.015], size=z, rot=90, color="#C9A45C", on=on))
    out["word_gap"] = round(gap, 3)
    out["roll"] = dict(release=round(rush_end, 2), stop=round(path[-1][0], 2), y_start=path[0][2], y_end=round(y_end, 2), words=placed)


DECIDE_FINAL = [
    "【第 3 關第 3 輪回饋「紅地毯做寬一點，人踩在沒有字的紅地毯上」】紅毯從 0.95 m 加寬到 1.6 m（兩端離拱門柱、柱下玫瑰還有 10 cm 以上，卷子滾到拱門前不會撞到）；"
    "兩人整組往遠離鏡頭那側挪 35 cm，字改排在靠鏡頭那側。新郎的腳最遠踩到 x 0.10、字從 0.44 開始，整段動作都踩在沒有字的那半邊。",
    "【第 2 關的微調，灰線是 Mixamo 原樣】新郎的手平貼紅毯卷（照你第 4 輪的回饋）：0～3.3 秒雙手掌心轉成貼著卷面（離卷面約 1.2 cm＝手掌厚度）、手指順著弧面往前往上、手指伸平，手肘往外下方彎；手碰卷子的位置照原片。",
    "放手（照你第 2 關的兩次回饋、第 3 關「最後推出去時雙手向下壓」）：3.3 秒推出去後雙手繼續貼著卷子往前送，直到手臂伸直構不到（約 3.55 秒），掌心才離開卷面，3.65 秒起雙手放下、垂在身體兩側稍前面；4.5～4.85 秒接回原片。",
    "卷子的位置（第 3 關回饋「推的時候腳進入到紅地毯裡面」）：原本照手的高度反推，手舉得比卷頂還高時卷子會停住、新郎走進卷子裡；改成卷子背面一定在新郎膝蓋前 8 cm、腳尖前 5 cm，他往前走卷子就被推著走。",
    "新娘的手貼在新郎背上：1.55～3.35 秒每一格找新郎背面離她掌心最近的點，把手腕挪過去、掌心朝向他、手指朝上伸平；新郎衝出去、她的手要伸超過 15 cm 才碰得到時就慢慢放開（20 cm 完全放開）。第 1 關左手穿進他背 17 cm 的問題由這項處理。",
    "紅毯卷的路線照原片的手來算（和第 1 關一樣），手貼上去之後卷子不跟著改。",
]
