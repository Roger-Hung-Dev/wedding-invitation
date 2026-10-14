# 列出現有的 ZEPETO 身體（給服裝、動畫工作流挑選用）。輸出 JSON 到 stdout。
# 2026-10-12 起本檔在 skill zepeto-body-generation-workflow/scripts/；D:/render-work/zepeto-body/scripts/list_bodies.py 只是轉接到這裡。
# 用法：python -I list_bodies.py [--released]      --released：只列可以拿去用的（已出廠且檔案指紋對得上）
# 介面契約（2026-10-12 和 zepeto-clothing-models 約定）：呼叫端只依賴本腳本的輸出欄位，不直接解析 RELEASE.json；
#   RELEASE.json 內部格式之後若改（例如每個身體各自一個出廠狀態），由本腳本吸收，輸出欄位不變。
# 輸出：{"bodies":[{name, blend, version, released, status, sha256, sha_ok, preview, preview_tpose, handoff, height_m, released_at}], "release_file":...}
import hashlib, json, os, sys

BUILD = r"D:\render-work\zepeto-body\build"
REL = os.path.join(BUILD, "RELEASE.json")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


rel = json.load(open(REL, encoding="utf-8")) if os.path.exists(REL) else {}
rb = rel.get("bodies", {})
out = []
for name in sorted(os.listdir(BUILD)):
    blend = os.path.join(BUILD, name, "body.blend")
    if not os.path.isfile(blend):            # 只算 build/<名稱>/body.blend；groom_v3 之類的舊快照資料夾沒有 body.blend 就略過
        continue
    if name not in rb and ("_" in name or "." in name):   # 沒登記在出廠標記、名稱帶底線的是舊版快照；<人>.work 是製作中的暫存
        continue
    r = rb.get(name, {})
    st = r.get("status", rel.get("status", "unreleased")) if r else "unreleased"
    cur = sha(blend)
    ok = bool(r) and r.get("sha256") == cur
    bj = os.path.join(BUILD, name, "build.json")
    b = json.load(open(bj, encoding="utf-8")) if os.path.exists(bj) else {}
    pv = lambda f: (lambda p: p if os.path.exists(p) else None)(os.path.join(BUILD, name, f))
    out.append(dict(name=name, blend=blend, version=r.get("version", rel.get("version")) if r else None,
                    released=st == "released" and ok, status=st, sha256=cur, sha_ok=ok,
                    preview=pv("idle_0.png"), preview_tpose=pv("rest_0.png"),
                    handoff=r.get("handoff", rel.get("handoff")) if r else None,
                    height_m=b.get("T"), head=r.get("head") if r else None, released_at=r.get("released_at", rel.get("released_at")) if r else None))
if "--released" in sys.argv:
    out = [x for x in out if x["released"]]
sys.stdout.reconfigure(encoding="utf-8")   # Windows 主控台預設 cp950，handoff 裡的 − 等字元會炸
print(json.dumps({"release_file": REL, "bodies": out}, ensure_ascii=False, indent=1))
