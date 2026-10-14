# 分鏡展開檔（導演端寫，或單獨使用時動畫端照同樣格式自己寫）的讀寫。格式和 zepeto-director 約定（2026-10-12）：
#   路徑：.claude/docs/storyboard/<片名>-breakdown/<鏡號小寫>.md；單獨使用的測試情境放 .claude/docs/data/blender/zepeto/anim/_tests/<id>/spec.md
#   二級標題固定、順序不變：## 基本／## 鏡頭／## 角色與動作／## 互動接觸／## 道具與場景／## 字卡時間碼／## 回饋（沒內容寫「（無）」）
#   「基本」是條列（片名、鏡號、秒數、地點、角色、上一鏡、下一鏡、轉場（接上一鏡））
#   「鏡頭」「互動接觸」「字卡時間碼」是固定表頭的表格；時間一律是鏡內秒數（正片第 0 秒起，不含頭尾多做的）
#   「回饋」每輪一個 ### 第 N 輪（YYYY-MM-DD），照輪次往下加
# 用法：python zanim_spec.py <spec.md>   → 印出解析結果（JSON）
# ⚠️ 導演端的 director.py（/zepeto-film-director-workflow）直接 import 這支：parse()、program() 的介面或回傳格式要改，先通知 zepeto-director。
import json, os, re, sys

SECTIONS = ["基本", "鏡頭", "角色與動作", "互動接觸", "道具與場景", "字卡時間碼", "回饋"]
TABLES = {
    "鏡頭": ["起秒", "迄秒", "景別", "機位", "運鏡", "備註"],
    "角色與動作": ["起秒", "迄秒", "角色", "動作", "Mixamo 候選", "備註"],      # 導演端範本（2026-10-12）寫成表格
    "互動接觸": ["起秒", "迄秒", "角色", "部位", "接觸對象", "要求"],
    "字卡時間碼": ["字卡", "標題", "內容", "進場秒", "退場秒"],
}
BASIC_KEYS = ["片名", "鏡號", "秒數", "地點", "角色", "上一鏡", "下一鏡", "轉場（接上一鏡）"]
STORY = r"D:/SideProject/wedding-invitation/.claude/docs/storyboard"


def breakdown_path(film, shot):
    return f"{STORY}/{film}-breakdown/{shot.lower().replace('→', '_')}.md"


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _table(text, head):
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|") or re.match(r"^\|[\s:|-]+\|$", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells == head:
            continue
        rows.append(dict(zip(head, cells + [""] * (len(head) - len(cells)))))
    return rows


def parse(path):
    s = open(path, encoding="utf8").read()
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)               # 範本用 HTML 註解示範寫法，不算內容
    parts = re.split(r"^## (.+?)\s*$", s, flags=re.M)
    sec = {parts[i].strip(): parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}
    missing = [k for k in SECTIONS if k not in sec]
    out = dict(path=path, missing=missing, raw=sec)
    basic = {}
    for line in sec.get("基本", "").splitlines():
        m = re.match(r"^\s*[-*]\s*(.+?)[：:]\s*(.*)$", line)
        if m:
            basic[m.group(1).strip()] = m.group(2).strip()
    out["basic"] = basic
    for k, head in TABLES.items():
        rows = _table(sec.get(k, ""), head)
        for r in rows:
            for c in ("起秒", "迄秒", "進場秒", "退場秒"):
                if c in r:
                    r[c] = _num(r[c])
        out[k] = rows
    fb = sec.get("回饋", "")
    rounds = re.split(r"^### 第\s*(\d+)\s*輪[^\n]*$", fb, flags=re.M)
    out["回饋"] = {int(rounds[i]): rounds[i + 1].strip() for i in range(1, len(rounds) - 1, 2)}
    for r in out["角色與動作"]:
        r["Mixamo 候選"] = [x.strip() for x in re.split(r"[、,，]", r.get("Mixamo 候選", "")) if x.strip()]
    # 道具與場景：條列「場景」「道具」，項目用頓號分開；寫「缺：…」的是素材庫還沒有的
    pr = {}
    for line in sec.get("道具與場景", "").splitlines():
        m = re.match(r"^\s*[-*]\s*(.+?)[：:]\s*(.*)$", line)
        if m:
            pr[m.group(1).strip()] = m.group(2).strip()
    def items(v):
        have, miss = [], []
        for x in re.split(r"[、,，]", v or ""):
            x = x.strip()
            if not x or x.startswith(("（無", "(無")):
                continue
            (miss if x.startswith("缺") else have).append(re.sub(r"^缺[：:]\s*", "", x))
        return have, miss
    out["道具與場景"] = {k: dict(zip(("有", "缺"), items(v))) for k, v in pr.items()}
    return out


def program(specs, clips, handles_s=0.0):
    """字卡時間碼 → render_edit.py 的 program.json。specs：[parse() 結果]；clips：{鏡號: (影片路徑, 鏡內秒數)}。
    handles_s：完整渲染時頭尾多做的秒數（film.json）→ 每段影片跳過開頭 in_s 秒，字卡時間碼照鏡內秒數不用改"""
    shots = []
    for sp in specs:
        sid = sp["basic"].get("鏡號", "")
        src, dur = clips[sid]
        caps = sp["字卡時間碼"]
        c = caps[0] if caps else None
        shots.append(dict(id=sid, label=sid, src=src, dur=dur, in_s=handles_s,
                          cap=[c["標題"], c["內容"]] if c else ["", ""],
                          cue=[c["進場秒"] if c else 0.0, c["退場秒"] if c else None]))
    return {"shots": shots}


def write_standalone(path, basic, camera, actions, contacts, scene="（無）", props="（無）", captions=()):
    """單獨使用（沒有導演端）時，動畫端照導演端範本（storyboard/_breakdown-template.md）的格式寫一份。
    camera／actions／contacts／captions 是 dict 列表（鍵＝表頭；actions 的「Mixamo 候選」可給 list）；scene、props 是頓號分開的字串，缺的寫「缺：…」"""
    def tbl(k, rows):
        h = TABLES[k]
        if not rows:
            return "（無）"
        cell = lambda v: "、".join(v) if isinstance(v, (list, tuple)) else ("" if v is None else str(v))
        return "\n".join(["| " + " | ".join(h) + " |", "| " + " | ".join("---" for _ in h) + " |"] +
                         ["| " + " | ".join(cell(r.get(c)) for c in h) + " |" for r in rows])
    md = ["# " + basic.get("片名", "") + "：" + basic.get("鏡號", "") + "（分鏡展開；動畫端單獨使用時自己寫的）", "",
          "## 基本", "", *[f"- {k}：{basic.get(k, '（無）')}" for k in BASIC_KEYS], "",
          "## 鏡頭", "", tbl("鏡頭", camera), "",
          "## 角色與動作", "", tbl("角色與動作", actions), "",
          "## 互動接觸", "", tbl("互動接觸", contacts), "",
          "## 道具與場景", "", f"- 場景：{scene}", f"- 道具：{props}", "",
          "## 字卡時間碼", "", tbl("字卡時間碼", list(captions)), "",
          "## 回饋", "", "（無）", ""]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf8").write("\n".join(md))
    return path


if __name__ == "__main__":
    print(json.dumps(parse(sys.argv[1]), ensure_ascii=False, indent=1))
