"""分鏡卡標註文字 → storyboard.json 特效物件的解析註冊表。

每一條規則對應 fx-* skill 裡的一個特效條目；新增特效時：
  1. 在對應的 fx-* SKILL.md 加條目（詞彙、寫法、JSON）
  2. 在這裡加一條 (正規式, 建構函式, 寫法範例)
  3. 在 render_storyboard.py 實作 JSON 的 type
三處的「寫法」與「JSON 欄位」必須一字不差。
"""
import re

NUM = r"(\d+(?:\.\d+)?)"
ARROW = r"(→|←)"


def strip_note(text):
    """去掉全形括號說明與前後空白；說明不參與解析。"""
    return re.sub(r"（[^）]*）", "", text or "").strip()


def _ease(m, group):
    return {"ease": True} if m.group(group) else {}


def _dir(arrow):
    return "right" if arrow == "→" else "left"


# ── 運鏡 ──────────────────────────────────────────────────────────────
MOTIONS = [
    (rf"^(?:慢推|慢拉|微推|微拉)\s*{NUM}\s*→\s*{NUM}\s*%(\s*緩動)?$",
     lambda m: {"type": "zoom", "from": float(m[1]) / 100, "to": float(m[2]) / 100, **_ease(m, 3)},
     "慢推 100→108%／慢拉 115→100%／微推 100→103%（可加「緩動」）"),
    (r"^靜止$", lambda m: {"type": "still"}, "靜止"),
    (rf"^平移\s*{ARROW}\s*{NUM}\s*px\s*@\s*{NUM}\s*%(\s*緩動)?$",
     lambda m: {"type": "pan", "dir": _dir(m[1]), "distance": float(m[2]), "scale": float(m[3]) / 100, **_ease(m, 4)},
     "平移 → 90px @105%"),
    (rf"^分割一推一拉\s*左\s*{NUM}\s*→\s*{NUM}\s*%\s*右\s*{NUM}\s*→\s*{NUM}\s*%$",
     lambda m: {"type": "split-counter", "left": [float(m[1]) / 100, float(m[2]) / 100],
                "right": [float(m[3]) / 100, float(m[4]) / 100]},
     "分割一推一拉 左100→106% 右106→100%"),
    (rf"^分割右格晚進\s*延遲\s*{NUM}\s*s\s*淡入\s*{NUM}\s*s$",
     lambda m: {"type": "split-late", "delay": float(m[1]), "fade": float(m[2])},
     "分割右格晚進 延遲0.2s 淡入0.3s"),
    (rf"^多格依序進場\s*間隔\s*{NUM}\s*s\s*淡入\s*{NUM}\s*s$",
     lambda m: {"type": "stagger", "interval": float(m[1]), "fade": float(m[2])},
     "多格依序進場 間隔0.3s 淡入0.4s"),
]

# ── 轉場（寫在「本鏡 → 下一鏡」）──────────────────────────────────────
TRANSITIONS = [
    (r"^硬切$", lambda m: {"type": "cut"}, "硬切"),
    (rf"^溶接\s*{NUM}\s*s$", lambda m: {"type": "dissolve", "duration": float(m[1])}, "溶接 0.8s"),
    (rf"^推移\s*{ARROW}\s*{NUM}\s*s$", lambda m: {"type": "push", "dir": _dir(m[1]), "duration": float(m[2])},
     "推移 → 0.6s"),
    (rf"^閃白\s*{NUM}\s*\+\s*{NUM}\s*s\s*{NUM}\s*%$",
     lambda m: {"type": "flash", "pre": float(m[1]), "post": float(m[2]), "peak": float(m[3]) / 100},
     "閃白 0.08+0.22s 85%"),
    (rf"^黑場\s*{NUM}\s*\+\s*{NUM}\s*s$", lambda m: {"type": "black", "out": float(m[1]), "in": float(m[2])},
     "黑場 0.5+1.5s"),
]

# 片頭片尾卡內部專用（不進 shots）
TITLE_INNER = [
    (r"^無切換$", lambda m: {"type": "none"}, "無切換"),
    (rf"^淡出至黑\s*{NUM}\s*s$", lambda m: {"type": "fade-to-black", "duration": float(m[1])}, "淡出至黑 1s"),
]

LAYOUTS = {"A": "直式置中＋模糊底", "H": "橫式滿版", "B": "分割畫面", "C": "回顧格"}
OPENING_STYLES = {"對焦轉移": "focus-pull"}
ENDING_STYLES = {"左照右字": "photo-thanks-monogram"}

# 版型與運鏡的相容表（不在表內的組合一律報錯）
MOTION_LAYOUTS = {
    "zoom": {"A", "H", "B"}, "still": {"A", "H", "B", "C"}, "pan": {"A", "H"},
    "split-counter": {"B"}, "split-late": {"B"}, "stagger": {"C"},
}
PHOTO_COUNT = {"A": (1, 1), "H": (1, 1), "B": (2, 2), "C": (2, 6)}


def parse(text, table):
    """回傳 (物件, None) 或 (None, 錯誤訊息)。"""
    t = strip_note(text)
    for pattern, build, _ in table:
        m = re.match(pattern, t)
        if m:
            return build(m), None
    allowed = "、".join(f"「{ex}」" for _, _, ex in table)
    return None, f"「{text}」不符合任何寫法；可用寫法：{allowed}"


def parse_layout(text):
    t = strip_note(text)
    m = re.match(r"^([AHBC])\b", t)
    if m:
        return m[1], None
    return None, f"「{text}」不是有效版型；開頭須為 A／H／B／C（{'、'.join(f'{k} {v}' for k, v in LAYOUTS.items())}）"


def parse_title_style(text, kind):
    """kind＝片頭／片尾；寫法「片頭：對焦轉移」。"""
    styles = OPENING_STYLES if kind == "片頭" else ENDING_STYLES
    m = re.match(rf"^{kind}\s*[:：]\s*(\S+)$", strip_note(text))
    if m and m[1] in styles:
        return styles[m[1]], None
    return None, f"「{text}」不是有效的{kind}樣式；寫法「{kind}：{'／'.join(styles)}」"
