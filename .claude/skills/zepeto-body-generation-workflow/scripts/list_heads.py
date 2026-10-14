# 列出可以拿來做身體的 ZEPETO 大頭（給身體工作流與選單外掛 zepeto-picker 用）。輸出 UTF-8 JSON 到 stdout。
# 用法：python -I list_heads.py [--ready]      --ready：只列可以用的（成品齊全、沒在製作中）
# 介面契約（同 list_bodies.py）：呼叫端只依賴輸出欄位；頭的存放方式之後改了由本腳本吸收。
#
# 規則（2026-10-12 使用者定）：每個人只留一個「現役版本」＝ zepeto/<人>/rig/head_rig.blend；重做時舊版改名封存
#   （例 head_rig_20261012.blend），本腳本只認 head_rig.blend，封存檔、中間檔（aligned／wrapped／head_arkit／head_v1）一律不列。
# 新郎的頭是產線建好前手動做的，放在專案根目錄 stylized_face_rig/（CLAUDE.md：不搬），這裡登記成 groom。
# 輸出：{"heads":[{name, zh, blend, version, status, ready, sha256, sha_ok, preview, legacy, note}]}
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]                     # 專案根目錄
ZEP = ROOT / ".claude" / "docs" / "data" / "blender" / "zepeto"
STATUS = ZEP / "pipeline" / "status" / "head"
LEGACY = {"groom": ROOT / "stylized_face_rig"}                 # 名稱 → 舊位置的資料夾（裡面直接是 head_rig.blend、preview/）
SKIP = {"templates", "pipeline"}
ZH = {"groom": "新郎", "bride": "新娘"}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def entry(name, rig, legacy):
    blend = rig / "head_rig.blend"
    if not blend.is_file():
        return None
    pv = rig / "preview" / "mat_front_new.png"
    complete = legacy or (rig / "preview" / "sheet_keys.png").is_file()     # 可動臉端最後才出 sheet_keys.png
    st = STATUS / f"{name}.json"
    rec = json.loads(st.read_text(encoding="utf-8-sig")) if st.is_file() else None
    cur = sha(blend)
    status = rec["status"] if rec else ("released" if complete else "in_progress")
    note = None if rec else "大頭端還沒寫狀態紀錄，版本與狀態是依檔案推定的"
    return dict(name=name, zh=ZH.get(name, name), blend=str(blend).replace("\\", "/"),
                version=rec["version"] if rec else "legacy" if legacy else "unrecorded",
                status=status, ready=complete and status == "released" and (rec is None or rec["artifact"]["sha256"] == cur),
                sha256=cur, sha_ok=(rec["artifact"]["sha256"] == cur) if rec else None,
                preview=str(pv).replace("\\", "/") if pv.is_file() else None, legacy=legacy, note=note)


heads = {}
for d in sorted(p for p in ZEP.iterdir() if p.is_dir() and p.name not in SKIP):
    e = entry(d.name, d / "rig", False)
    if e:
        heads[d.name] = e
for name, d in LEGACY.items():
    if name not in heads:                                       # 產線版做出來之後就以產線版為準
        e = entry(name, d, True)
        if e:
            heads[name] = e
out = list(heads.values())
if "--ready" in sys.argv:
    out = [h for h in out if h["ready"]]
sys.stdout.reconfigure(encoding="utf-8")
print(json.dumps({"heads": out}, ensure_ascii=False, indent=1))
