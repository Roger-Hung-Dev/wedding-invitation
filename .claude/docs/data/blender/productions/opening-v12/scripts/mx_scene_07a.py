# ⑦a 盡情享用美食（6 秒）。2026-10-11 第 3 關第 3 輪回饋：原本的 ⑦（12 秒，新郎餵新娘＋乾杯）拆成兩幕——
#   「這一幕總共有兩則提示，一則是『請大家盡情享用美食』，另一則是『喝酒不開車，開車不喝酒』，我想拆成兩幕動畫
#    第一幕：桌上擺著豐盛佳餚，新娘坐著吃的很開心的動作；第二幕：新郎喝醉臉紅走路不穩，接著搭上計程車離開」
#   使用者選 ⑦a 6 秒＋⑦b 9 秒（全片 75 → 78 秒）。⑦a 只有新娘。
# 場景沿用 ⑦ 的圓桌晚餐（桌心 (1.85, −1.25)、桌面 0.733、落地桌巾）；新娘改坐在桌子正後方、正對鏡頭（一個人吃，構圖放中間），
#   桌上加菜（mx_preview 的 07a：烤雞、湯、沙拉、蛋糕、水果、點心；她面前一盤牛排）。
# 做法照 ⑦ 第 3 輪學到的：底是「雙手放桌上靜坐」（Seated Idle With Hands On A Table）＋呼吸，只動做事的手——
#   右手拿叉子：叉一口 → 送進嘴裡（張嘴咬）→ 收回；咬完閉眼笑著嚼、肩膀左右小幅晃（好吃）；
#   左手比讚：手臂用 Mixamo「Sitting Thumbs Up」（左右鏡射成左手）原片的手臂動作，手指用動作庫的 thumbs_up；比讚時看鏡頭；
#   最後低頭看盤子、叉子往盤子伸（準備吃下一口），轉場。
import os
exec(compile(open(os.path.join(PROD_SCRIPTS, "mx_scene_07.py"), encoding="utf8").read(), "mx_scene_07.py", "exec"), globals())   # 共用 ⑦ 的工具
exec(compile(open(os.path.join(PROD_SCRIPTS, "fork_grip.py"), encoding="utf8").read(), "fork_grip.py", "exec"), globals())     # 西餐握叉（第 3 關第 13 輪）
GRIP = {}                                             # solve_grip 的結果（第一次用到時照骨架 rest 算）

B7A = (1.85, -0.684)                                  # 新娘骨盆（桌子正後方，離桌心 0.566 m＝⑦ 原本座位離桌心的距離），面向鏡頭
CAM = Vector((1.85, -3.05, 1.30))                     # 鏡頭（mx_preview 07a 同一組）
CAM_AIM = Vector((1.85, -0.98, 0.95))
PLATE_A = Vector((1.85, -1.08, TABLE_Z))              # 她面前的牛排盤（桌心座標 (0, 0.17)；盤心在骨盆前 40 cm，第一版 35 cm 太近，拿叉子的手只能縮在胸口前）
BITE_A = PLATE_A + Vector((-0.04, 0.02, 0.022))       # 叉的那一口（牛排片，靠她右手那側）
FEAST = Vector((1.85, -1.30, TABLE_Z + 0.10))         # 滿桌菜的中間
# 牛排塊、叉子方向相對新娘右手骨頭。第 3 關第 5 輪回饋「修正動作讓手是真的有拿著叉子」：握法改成照手指算
#   （mx_preview 07a 的 fork_rel：叉柄夾在拇指尖和食指第 2 節之間、柄尾靠虎口），印出的 MXPREVIEW_07A_FORK 值
#   （之前是動作庫 held_prop("fork","R") 的固定位置 (−0.0747, 0.17, 0.0647)，叉柄從手掌底下穿出來）
#   第 3 關第 12 輪改西餐握法（fork_grip，叉柄貼食指下面）後重印；拿筆握法時是 (−0.0415, 0.2037, 0.024)／(−0.2311, 0.9723, 0.0356)
FB_R = Vector((-0.0027, 0.1958, 0.016))
FA_R = Vector((0.0519, 0.9983, -0.027)).normalized()
T_SPEAR_A, T_BITE_A = 1.0, 2.1                        # 叉起那一口、咬下（mx_preview 的道具時間點）
THUMB_CLIP = (0.8, 3.1)                               # Sitting Thumbs Up 原片舉手比讚的那段
T_THUMB = 3.25                                        # 場景裡從幾秒開始比讚（原片 0.8 秒對到這裡）
THUMB_MODE = "hold"                                   # 比讚：hold＝拳頭舉在肩膀前、拇指朝上不晃（/fix-animation）；clip＝原片手臂（舊版）
THUMB_SPOT = (0.30, 0.10, -0.10)                      # 拳頭位置＝左肩往前 30 cm、往左 10 cm、往下 10 cm（胸口高度、身體左前方）；
#   第 1、2 版在肩上 10 cm（下巴高）：手肘在拳頭下方、前臂往上斜，手腕被折 80°
THUMB_WRIST_FIX = False
THUMB_FINGERS = os.environ.get("THUMB_FINGERS", "pose")   # 比讚的手指：pose＝手勢庫 thumbs_up＋拇指對齊；mixamo＝原片動捕的手指（試過：拇指往旁邊歪 45°、四指只彎 135°，原片手指套到 VRoid 會跑掉）
THUMB_FINGER_T = float(os.environ.get("THUMB_FINGER_T", "1.8"))   # 原片取哪一秒的手指（比讚比好、手腕點到中間）


def fork_to_r(T_, R, h, goal, d, w, pole, iters=4):
    """新娘右手的叉子：牛排塊到 goal、叉子方向轉向 d（權重 w）（同 mx_scene_07 的 fork_to，換成右手）"""
    H = "J_Bip_R_Hand"
    Hd = T_.fk(R, h); R0 = R
    fb, fa = GRIP.get("fb", FB_R), GRIP.get("fa", FA_R)
    bite0 = Hd[H] + R[H] @ fb
    want = bite0.lerp(goal, w); target = Hd[H] + (want - bite0)
    for _ in range(iters):
        R = arm_ik(T_, R0, h, "R", target, pole)
        ax = R[H] @ fa
        R = rotate_subtree(T_, R, H, ax.rotation_difference(ax.lerp(d, w).normalized()))
        R = fix_arm_twist(T_, R, h, "R")
        Hd2 = T_.fk(R, h)
        target = target + (want - (Hd2[H] + R[H] @ fb))
    return R


def borrow_arm(T_, R, src, side, w):
    """把另一支動畫（src＝那一格的世界轉向）的整隻手臂動作借過來：上臂 → 前臂 → 手，每一節取「相對上一節」的轉向，
    接到現在的身體上（身體、另一隻手照舊），權重 w。手指之後另外用手勢擺"""
    # （鎖骨不借：原片比讚時鎖骨往前推 30°，第 7 輪回饋「胸口形狀異常」後鎖骨維持 relax_shoulders 放鬆的位置）
    for b in (f"J_Bip_{side}_UpperArm", f"J_Bip_{side}_LowerArm", f"J_Bip_{side}_Hand"):
        p = T_.parent[b]
        want = R[p] @ (src[p].inverted() @ src[b])
        cur = R[b]
        R = rotate_subtree(T_, R, b, cur.slerp(want, w) @ cur.inverted())
    return R


def wiggle(T_, R, h, t, w):
    """好吃的時候肩膀左右小幅晃（胸口繞身體的上方向 ±5°、0.55 秒一下），頭往反方向歪一點"""
    if w <= 0:
        return R
    a = math.radians(5.0) * math.sin(2 * math.pi * (t - 2.3) / 0.55) * w
    R = rotate_subtree(T_, R, "J_Bip_C_Chest", Quaternion(UP, a))
    Hd = T_.fk(R, h)
    lft, fwd = body_axes(Hd)
    return rotate_subtree(T_, R, "J_Bip_C_Head", Quaternion(fwd, -a * 1.2))


def relax_shoulders(T_, R, k=0.7):
    """鎖骨（J_Bip_X_Shoulder）往自然的位置放回 k（第 3 關第 7 輪回饋「胸口有很大一片，形狀有點異常」）：
    Seated Idle 原片的兩邊肩膀往前又往下垂（鎖骨轉 24.5°、兩肩距從站著的 0.21 m 縮到 0.19 m），夾在中間的胸口被擠成一大片。
    相對上胸的轉動往「沒轉」放回 k，底下的手臂跟著；手放桌上的位置之後由 rest_hands 的手臂 IK 再搆"""
    for s_ in "LR":
        n = f"J_Bip_{s_}_Shoulder"; p = T_.parent[n]
        Pw = R[p] @ T_.rest_q[p].inverted()
        L = Pw.inverted() @ (R[n] @ T_.rest_q[n].inverted())
        want = Pw @ L.slerp(Quaternion(), k) @ T_.rest_q[n]
        R = rotate_subtree(T_, R, n, want @ R[n].inverted())
    return R


def bride_mod():
    B = tgt("bride")
    TC = clip("bride", "sitting_thumbsup", True)       # 左右鏡射：原片右手比讚 → 左手（右手拿著叉子）
    if not GRIP:
        _g = solve_grip(B.rest_h, B.rest_t, B.rest_q)
        GRIP.update(_g); GRIP["fb"], GRIP["fa"] = fork_in_hand(_g, B.rest_h, B.rest_q)
        print("GRIP07A", _g["report"], flush=True)

    def mod(t, R, h):
        R = breathe(B, R, h, t, deg=1.2, phase=0.45)
        R = relax_shoulders(B, R)
        Hd = B.fk(R, h)
        lft, fwd = body_axes(Hd)
        R = lean(B, R, Hd, Hd["J_Bip_C_Head"] + fwd, 6.0 * win(t, 1.55, 1.85, 2.1, 2.45))   # 湊過去咬
        R = wiggle(B, R, h, t, win(t, 2.25, 2.45, 3.1, 3.35))
        Hd = B.fk(R, h)
        mouth0 = mouth_of(B, R, Hd)
        # 頭：看滿桌菜 → 看盤子叉一口 → 叉子過來時看前下方 → 嚼的時候抬頭（閉眼笑）→ 比讚看鏡頭 → 最後看回盤子
        #   （第一版看菜、看盤子低頭 36～48°，開場 1.5 秒都看不到臉 → 看的點抬高、低頭打 0.75 折）
        pt, wl = ramp(t, [(-1, 0.45, FEAST + UP * 0.2), (0.7, 1.35, BITE_A + UP * 0.3), (1.55, 2.1, mouth0 + fwd * 0.35 - UP * 0.10),
                          (2.4, 3.1, CAM + UP * 0.25), (3.4, 5.45, CAM), (5.75, 99, BITE_A + UP * 0.3)])
        if pt is not None:
            R = look_at(B, R, h, pt, w=wl, split=(0.1, 0.2, 0.7), pitch=0.75)
        # 脖子挺直、頭往前補回（第 3 關第 8 輪回饋「新娘脖子不明顯，輪廓看不出有脖子」）：低頭有七成給了脖子骨頭，脖子往前傾 20～34°，
        #   下巴往前下方壓到胸口上；鏡頭又從上往下拍 → 脖子被下巴擋住。真人低頭看盤子多半是頭在脖子上點頭 → 脖子往後 12°、頭往前 12°，
        #   臉的方向不變，下巴離開胸口
        Hd = B.fk(R, h)
        lft_n, _f = body_axes(Hd)
        R = rotate_subtree(B, R, "J_Bip_C_Neck", Quaternion(lft_n, math.radians(-12.0)))
        R = rotate_subtree(B, R, "J_Bip_C_Head", Quaternion(lft_n, math.radians(12.0)))
        R = rest_hands(B, R, h)
        Hd = B.fk(R, h)
        lft, fwd = body_axes(Hd)
        fh, uh, _lh = head_axes(B, R)
        mouth = Hd["J_Bip_C_Head"] + fh * 0.11 + uh * 0.005                  # 嘴前 2.5 cm（同 ⑦ 的 bride_face(t, 0.025, 0.005)；第一版高 1.5 cm，那一口停在鼻子上）
        # 右手：叉子（開場就拿著，叉尖靠在盤緣）→ 0.75～1.2 秒叉一口（叉尖往下）→ 1.9 秒送到嘴前 2.5 cm、停到 2.15（2.1 秒咬下）→ 收回盤邊；
        #   5.5 秒起再往盤子伸（準備吃下一口）
        rest = PLATE_A + Vector((-0.13, 0.04, 0.03))                          # 叉尖靠在盤子右側
        mid = BITE_A.lerp(mouth, 0.5) + UP * 0.10
        back = BITE_A.lerp(mouth, 0.45) + UP * 0.05
        keys = [(0.0, rest), (0.45, rest), (0.8, BITE_A + UP * 0.07), (1.0, BITE_A), (1.2, BITE_A + UP * 0.09), (1.55, mid),
                (1.9, mouth), (2.15, mouth), (2.5, back), (2.95, rest + UP * 0.02), (3.25, rest), (5.45, rest),
                (6.0, BITE_A + UP * 0.05)]
        goal = spline(t, keys)
        sh = Hd["J_Bip_R_UpperArm"]
        d = goal - sh; d.z = 0; d.normalize()
        stab = win(t, 0.75, 0.92, 1.05, 1.2)                                   # 叉的時候叉尖往下
        lean_down = 1.0 - win(t, 0.45, 0.7, 2.7, 3.1)                          # 拿著不吃時叉尖朝前下方、靠在盤緣
        # 放著時叉子往下斜約 35°、叉齒碰到盤面（近照頁回饋「側面的手都很奇怪」：0.45 時只斜 18°，叉子幾乎水平貼在掌下、叉齒懸空）
        d = (d + UP * (0.12 * (1 - stab) - 0.9 * stab - 1.0 * lean_down)).normalized()
        # 放著不吃時叉子斜斜指向盤子中間（第 3 關第 11 輪回饋「叉子變成手指的一部分」）：原本朝前下方＝朝著鏡頭，
        #   從正前方拍縮成一小截直直往下、叉柄被手擋住，看起來像多一根灰色手指 → 往她左邊轉，從鏡頭看叉子斜著橫過畫面
        d = (d + lft * (0.75 * lean_down)).normalized()
        # 送到嘴邊時叉子從前下方朝嘴巴進去（第一版照「肩膀 → 嘴」的水平方向，叉子從臉側邊橫著進去，手跑到耳朵旁、手肘抬到頭高）：
        #   叉子方向＝往她的臉（−前）＋往上＋稍微往左，手就停在下巴前下方 13 cm、手肘朝下
        #   第 4 輪自我審查：往後 0.78 時手腕往回折 100° → 改成比較朝上；第 5 輪握法改成照手指算後再調成幾乎直立（往後 0.15、往上 1.0），手腕彎 85°
        d_m = (-fwd * 0.15 + UP * 1.0 + lft * 0.18).normalized()
        d = d.lerp(d_m, win(t, 1.4, 1.8, 2.2, 2.6)).normalized()
        R = fork_to_r(B, R, h, goal, d, 1.0, -lft * 0.5 - UP * 1.0)           # 手肘往下、稍微往外（第一版 0.7／0.8 手肘翹到肩膀高）
        # （手指照叉子擺放在最後一步，見 return 前）
        # 左手：比讚（原片 0.8～3.1 秒舉手、手腕上下點兩三下 → 場景 3.25～5.55 秒）
        wt = win(t, 3.15, 3.55, 5.25, 5.7)
        if wt > 0 and THUMB_MODE == "hold":
            # /fix-animation「左手比讚的姿勢看不出來在比讚」：原片的手臂往旁邊伸、手腕一直上下點，拇指在朝上和斜 50° 之間晃，
            #   拳頭小小的又一直在動。改成拳頭舉在肩膀前方、臉旁邊：前臂往前（朝鏡頭）、掌心朝身體中線、拇指朝正上方，
            #   只留 ±1.2 cm 的小幅點動（每秒 2 下）。舉起 3.15～3.55、放下 5.25～5.7 照原本的時間
            Hd = B.fk(R, h)
            lft, fwd = body_axes(Hd)
            sh = Hd["J_Bip_L_UpperArm"]
            bob = 0.012 * math.sin(2 * math.pi * 2.0 * max(0.0, t - 3.55)) * win(t, 3.5, 3.7, 5.1, 5.25)
            spot = sh + fwd * THUMB_SPOT[0] + lft * THUMB_SPOT[1] + UP * (THUMB_SPOT[2] + bob)
            Rt = arm_ik(B, R, h, "L", spot, lft * 0.6 - UP * 1.0)              # 手肘往下、稍微往外
            # 手腕保持直的（近照頁回饋「手腕沒有拉到正確角度，看起來是往外凹」：手掌硬轉朝正前方、前臂卻從下往上斜，手腕往手背折 80°）：
            #   手掌順著前臂、只微微往手背 8°；拇指朝上改由手臂的位置決定（拳頭在胸口高度、前臂接近水平往前）
            Hd_t = B.fk(Rt, h)
            fa_t = (Hd_t["J_Bip_L_Hand"] - Hd_t["J_Bip_L_LowerArm"]).normalized()
            Rt = aim_hand(B, Rt, h, "L", (fa_t + UP * 0.14).normalized(), palm=-lft, palm_w=1.0)
            for b_ in ("J_Bip_L_UpperArm", "J_Bip_L_LowerArm", "J_Bip_L_Hand") + tuple(
                    "J_Bip_L_%s%d" % (f_, i_) for f_ in ("Thumb", "Index", "Middle", "Ring", "Little") for i_ in (1, 2, 3)):
                R[b_] = R[b_].slerp(Rt[b_], wt)
        if wt > 0 and THUMB_MODE == "clip":
            tau = min(THUMB_CLIP[1], max(THUMB_CLIP[0], THUMB_CLIP[0] + (t - T_THUMB)))
            R = borrow_arm(B, R, TC["R"][int(round(tau * 30))], "L", wt)
            # 鎖骨不跟原片往前推之後，同樣的上臂轉法手會往側邊打直（像對旁邊的人比讚）→ 上臂繞身體上方向往前轉 22°，手回到肩膀前方、朝鏡頭
            R = rotate_subtree(B, R, "J_Bip_L_UpperArm", Quaternion(UP, math.radians(-22.0) * wt))
        if wt > 0:
            wg = win(t, 3.3, 3.6, 5.2, 5.5)
            if THUMB_FINGERS == "mixamo":
                # 近照頁第 7 版回饋「查一下比讚的動作，放回到目前的角色動作來修正，大拇指還是很奇怪，側面看起來不像手指」：
                #   手指改用 Mixamo「Sitting Thumbs Up」原片（真人動捕）的手指——每一節取「相對上一節」的轉向，接到現在的手上；
                #   原片手腕會點，手指取比讚比好的那一格（THUMB_FINGER_T 秒）固定不動
                src = TC["R"][int(round(THUMB_FINGER_T * 30))]
                for f_ in ("Thumb", "Index", "Middle", "Ring", "Little"):
                    for i_ in (1, 2, 3):
                        b_ = "J_Bip_L_%s%d" % (f_, i_)
                        if b_ not in src:
                            continue
                        p_ = B.parent[b_]
                        want = R[p_] @ (src[p_].inverted() @ src[b_])
                        R = rotate_subtree(B, R, b_, R[b_].slerp(want, wg) @ R[b_].inverted())
            else:
                R = gesture(B, R, "L", "thumbs_up", w=wg)
            # 拇指一直朝上（第 4 輪預覽：原片點讚時手腕會轉，4.3 秒拇指轉成朝旁邊，像搭便車的手勢）：前臂繞自己的軸轉，
            #   讓拇指（垂直於前臂的那個分量）對準上方
            Hd = B.fk(R, h)
            fa = (Hd["J_Bip_L_Hand"] - Hd["J_Bip_L_LowerArm"]).normalized()
            # 扶正的是「四指疊起來的方向」（小指根 → 食指根），不是拇指本身（近照頁第 4 版回饋「大拇指應該與四根手指頭同側方向，
            #   四根手指頭是有角度，大拇指硬生生打直」：拇指被單獨扳成正上方，拳頭卻是斜的）
            v = Hd["J_Bip_L_Index1"] - Hd["J_Bip_L_Little1"]
            vp, up_p = v - fa * v.dot(fa), UP - fa * UP.dot(fa)
            if vp.length > 1e-4 and up_p.length > 1e-4:
                a = math.atan2(fa.dot(vp.cross(up_p)), vp.dot(up_p))
                R = rotate_subtree(B, R, "J_Bip_L_LowerArm", Quaternion(fa, a * wg))
            if THUMB_MODE == "hold" and THUMB_FINGERS == "pose":
                # 前臂轉完拇指還朝前臂方向斜 18°（轉前臂修不到這個方向）→ 只轉拇指根部（拇指根部本來就能往各方向轉），手腕不動，最多 25°
                # 拇指順著四指疊起來的方向（小指根 → 食指根）豎起，跟拳頭同一個角度；只轉拇指根部，最多 60°
                Hd = B.fk(R, h)
                u = (B.tail(R, Hd, "J_Bip_L_Thumb3") - Hd["J_Bip_L_Thumb2"]).normalized()
                stack = (Hd["J_Bip_L_Index1"] - Hd["J_Bip_L_Little1"]).normalized()
                q = u.rotation_difference(stack)
                if q.angle > 1e-4:
                    # 拆成兩段：根部關節轉一半、中間關節（第 2 節）轉另一半（近照頁第 6 版回饋「右側稍微腫大」：根部一次轉 50°，根部皮膚被擠得鼓起來）
                    ang = min(q.angle, math.radians(60.0)) * wg
                    R = rotate_subtree(B, R, "J_Bip_L_Thumb1", Quaternion(q.axis, ang * 0.5))
                    Hd = B.fk(R, h)
                    u = (B.tail(R, Hd, "J_Bip_L_Thumb3") - Hd["J_Bip_L_Thumb2"]).normalized()
                    stack = (Hd["J_Bip_L_Index1"] - Hd["J_Bip_L_Little1"]).normalized()
                    q2 = u.rotation_difference(stack)
                    if q2.angle > 1e-4:
                        R = rotate_subtree(B, R, "J_Bip_L_Thumb2", Quaternion(q2.axis, min(q2.angle, math.radians(35.0)) * wg))
            if THUMB_MODE == "hold" and THUMB_WRIST_FIX:
                # （第 1 版）前臂轉完拇指還斜 25° → 手腕再彎一點把拇指扶正（最多 35°）。第 3 版拿掉：手腕往外折
                Hd = B.fk(R, h)
                u = (B.tail(R, Hd, "J_Bip_L_Thumb3") - Hd["J_Bip_L_Thumb2"]).normalized()
                q = u.rotation_difference(UP)
                ang = min(q.angle, math.radians(35.0))
                if q.angle > 1e-4:
                    R = rotate_subtree(B, R, "J_Bip_L_Hand", Quaternion(q.axis, ang * wg))
        R = table_guard(B, R, h, skip=("R",) if 0.5 < t < 3.0 else ())
        R = lift_off_table(B, R, h, "L", w=1.0 - wt)                       # 左手放桌上時指尖不插進桌面
        # 第 3 關第 13 輪回饋「握叉的角度、握法始終不正確，手指也會穿模」：手指照叉子的位置一根一根彎到剛好碰到叉柄（fork_grip.py）。
        #   一定要在桌面護手之後：護手把手掌轉朝下時手指不跟著轉，放著不吃的那幾段手指被扭直、跟叉子對不上（前幾輪握法看起來不對的主因）
        return apply_grip(B, R, GRIP["acc"])
    return mod


def lift_off_table(T_, R, h, s_, clear=0.003, w=1.0):
    """手指穿桌面修正（/fix-animation「手指穿模（例：桌面）」）：手放桌上時 rest_hands／table_guard 只管手腕、中指根，
    自然微彎的手指往下垂，指尖插進桌面最深 4.8 cm（TABLECLIP，0～3.2 秒、5.8 秒後左手 529 點）。
    量手指每節的皮膚最低點（骨頭線往下減手指粗細 1 cm）、掌心（手骨頭往下 2.3 cm），低於桌面就把整隻手抬上來（做兩次收斂）"""
    for _ in range(2):
        Hd = T_.fk(R, h)
        pts = [(Hd["J_Bip_%s_Hand" % s_], 0.023), (Hd["J_Bip_%s_Middle1" % s_], 0.012)]
        for f_ in ("Thumb", "Index", "Middle", "Ring", "Little"):
            for i_ in (1, 2, 3):
                n_ = "J_Bip_%s_%s%d" % (s_, f_, i_)
                pts.append((Hd[n_], 0.010)); pts.append((T_.tail(R, Hd, n_), 0.009))
        on = [(p_, r_) for p_, r_ in pts if (Vector((p_.x, p_.y)) - TABLE_C).length < TABLE_R]
        if not on:
            return R
        lack = TABLE_Z + 0.001 + clear - min(p_.z - r_ for p_, r_ in on)
        if lack <= 0:
            return R
        lft, _f = body_axes(Hd)
        sg = 1.0 if s_ == "L" else -1.0
        R = hand_to(T_, R, h, s_, palm_of(Hd, s_) + UP * (lack * w), lft * sg * 0.8 - UP * 0.6, 1.0)
    return R


def rest_hands(T_, R, h):
    """雙手平放桌上、收在身前（同 mx_scene_07，但兩手左右各 21 cm：她面前的牛排盤半徑 15 cm，手要放在盤子兩側）"""
    Hd = T_.fk(R, h)
    lft, fwd = body_axes(Hd)
    hp = Hd["J_Bip_C_Hips"]
    for s_, sg in (("L", 1.0), ("R", -1.0)):
        spot = Vector((hp.x, hp.y, 0)) + fwd * 0.30 + lft * (sg * 0.21); spot.z = TABLE_Z + 0.02
        for _ in range(2):
            R = hand_to(T_, R, h, s_, spot, lft * (sg * 0.8) - UP * 0.6, 1.0)
            H2 = T_.fk(R, h)
            R = aim_hand(T_, R, h, s_, (fwd * 0.92 - lft * (sg * 0.3) - UP * 0.12).normalized(), palm=-UP, palm_w=1.0)
        R = gesture(T_, R, s_, "relaxed", w=1.0)
    return R


def post(out):
    """第 2 關網頁：椅子調高到坐姿骨盆下方"""
    for p in out["props"]:
        if p.get("name", "").startswith("新娘椅"):
            p["max"][2] = SEAT - 0.08; p["name"] = "新娘椅（椅面調高到 %.2f）" % (SEAT - 0.08)


def scene():
    bride = dict(segs=[
        S("bride", "seated_table_idle", 0, None, loops=1.5, seat=SEAT, label="坐著、雙手放桌上（Seated Idle With Hands On A Table）"),
    ], anchor=(0.0, B7A, 0.0), mod=bride_mod() if FINAL else None)
    x, y = B7A
    props = [
        dict(kind="cyl", name="圓桌＋落地桌巾", c=[1.85, -1.25], r=0.485, z0=0.0, z1=0.734, color="#FBF6EE", opacity=0.4),
        dict(kind="box", name="新娘椅（椅面 0.46）", min=[x - 0.21, y - 0.17, 0.0], max=[x + 0.21, y + 0.25, 0.46], color="#ECB0AC", opacity=0.5),
        dict(kind="cyl", name="她的牛排盤", c=[PLATE_A.x, PLATE_A.y], r=0.15, z0=0.734, z1=0.752, color="#FFFDF8", opacity=0.8),
        dict(kind="cyl", name="烤雞大盤", c=[1.87, -1.37], r=0.15, z0=0.734, z1=0.86, color="#C98A4B", opacity=0.6),
    ]
    cam = dict(pos=list(CAM), aim=list(CAM_AIM), lens=50.0, sensor=36.0, aspect=16 / 9)
    return dict(id="07a", title="⑦a 盡情享用美食", dur=6.0, chars=dict(bride=bride), props=props, cam=cam, skirt=None, post=post,
                note="新娘一個人坐在圓桌正後方（白色圓柱是落地桌巾）。底是「雙手放桌上靜坐」，只有拿叉子的右手、比讚的左手在動。",
                decide=DECIDE_FINAL if FINAL else DECIDE_G1)


DECIDE_G1 = [
    "【第 1 關（第 3 關第 3 輪回饋「⑦ 拆成兩幕」的第一幕）】新娘坐在桌子正後方、正對鏡頭，底是 Mixamo「Seated Idle With Hands On A Table」（雙手放桌上靜坐）。",
    "比讚用 Mixamo「Sitting Thumbs Up」（你同意下載的），左右鏡射成左手（右手拿著叉子）；第 2 關只借它的手臂動作。",
]

DECIDE_FINAL = [
    "【⑦ 拆成兩幕的第一幕，6 秒】桌上擺滿菜（烤雞、湯、沙拉、蛋糕、水果、點心），新娘面前一盤牛排。底是「雙手放桌上靜坐」＋呼吸，只有做事的手在動。",
    "右手拿叉子：0.75～1.2 秒在盤上叉一口 → 1.9 秒送到嘴前、張嘴咬（2.1 秒）→ 收回盤邊；咬的時候上身往前湊 6°。",
    "咬完閉眼笑著嚼（2.3～3.3 秒），肩膀左右小幅晃、頭往反方向歪一點，表示好吃。",
    "3.25～5.55 秒左手比讚、看鏡頭：手臂是 Mixamo「Sitting Thumbs Up」原片的動作（鏡射成左手），手指改用握拳＋拇指伸直。",
    "最後低頭看盤子、叉子往盤子伸，準備吃下一口時轉場。",
]
