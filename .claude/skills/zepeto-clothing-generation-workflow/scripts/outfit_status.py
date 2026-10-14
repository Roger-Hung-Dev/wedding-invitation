# 服裝的產線狀態紀錄（status/outfit/<服裝>@<人>.json）：開工前比對上游、改之前標製作中、定案後寫 released。
# 格式與規則見 .claude/docs/data/blender/zepeto/pipeline/README.md（由 zepeto-director 維護）。
# id＝素材庫代號把 - 換成 _，再接 @<身體名稱>：groom-beige-3piece ＋ groom → groom_beige_3piece@groom。
#
# 用法（python -I 執行，輸出 UTF-8）：
#   python -I outfit_status.py check   <服裝代號> <身體> [<身體> ...]   開工前：每個身體比對一次，印出結果
#   python -I outfit_status.py begin   <服裝代號> <身體> [<身體> ...]   要改已定案的服裝：紀錄改成 in_progress
#   python -I outfit_status.py release <服裝代號> <身體> --changes "這版改了什麼" [--page 審看頁網址]
#        使用者說可以之後：讀成品 outfit.blend 與當時用的 body.blend 的 sha，寫 released、版本加 1
# 結束碼：check 時 0＝全部可以開工（一致或沒紀錄）、1＝有「上游已更新」或「上游未就緒」、2＝紀錄格式錯誤；其他指令 0＝成功。
import argparse, datetime, hashlib, io, json, subprocess, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
PIPE = Path(__file__).resolve().parents[3] / "docs" / "data" / "blender" / "zepeto" / "pipeline"
STATUS = PIPE / "status"
COSTUME = Path("D:/render-work/zepeto-costume")


def rid(outfit, body):
    return f"{outfit.replace('-', '_')}@{body}"


def path_of(kind, i):
    return STATUS / kind / f"{i}.json"


def load(kind, i):
    p = path_of(kind, i)
    return json.loads(p.read_text(encoding="utf-8-sig")) if p.exists() else None


def save(rec):
    p = path_of(rec["kind"], rec["id"]); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return p


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fp:
        for chunk in iter(lambda: fp.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def cmd_check(a):
    worst = 0
    for b in a.bodies:
        i = rid(a.outfit, b)
        if load("outfit", i) is None:
            body = load("body", b)
            if body is None:
                print(f"[沒有紀錄] outfit/{i}：新的組合，可以開工（身體 {b} 也還沒有狀態紀錄，照出廠閘門判斷）")
            elif body.get("status") != "released":
                print(f"[上游未就緒] outfit/{i}：新的組合，但身體 {b} 是 {body.get('status')}，不能開工")
                worst = max(worst, 1)
            else:
                print(f"[沒有紀錄] outfit/{i}：新的組合，可以開工（身體 {b} {body.get('version')}）")
            continue
        r = subprocess.run([sys.executable, "-I", str(PIPE / "status_check.py"), f"outfit/{i}"], capture_output=True)
        print(r.stdout.decode("utf-8", "replace").rstrip())
        worst = max(worst, r.returncode)
    return worst


def cmd_begin(a):
    for b in a.bodies:
        i = rid(a.outfit, b); rec = load("outfit", i)
        if rec is None:
            print(f"outfit/{i}：還沒有紀錄（新的組合），不用標製作中")
            continue
        rec["status"] = "in_progress"; rec["updated_at"] = now()
        print(f"outfit/{i}：{rec['version']} 改成 in_progress → {save(rec)}")
    return 0


def cmd_release(a):
    i = rid(a.outfit, a.body)
    out = COSTUME / a.outfit / a.body
    blend = out / "outfit.blend"
    info = json.loads((out / "build.json").read_text(encoding="utf-8"))
    body_path = info["body_blend"]
    body_sha = sha256(body_path)
    body_rec = load("body", a.body)
    if body_rec and body_rec.get("artifact", {}).get("sha256") not in (None, body_sha):
        print(f"⚠️ 這次用的 body.blend 和 status/body/{a.body}.json 記的 sha 不一樣：身體可能又改過，先確認再定案")
        return 1
    old = load("outfit", i)
    n = int(str(old["version"]).lstrip("v")) + 1 if old else 1
    rec = {
        "schema": 1, "kind": "outfit", "id": i, "version": f"v{n}", "status": "released",
        "updated_at": now(), "owner": "outfit",
        "artifact": {"path": blend.as_posix(), "sha256": sha256(blend)},
        "upstream": [{"kind": "body", "id": a.body, "version": (body_rec or {}).get("version", "?"), "sha256": body_sha}],
        "changes": a.changes,
    }
    page = a.page or (old or {}).get("page")
    if page:
        rec["page"] = page
    rec["notes"] = {**((old or {}).get("notes") or {}), "outfit_key": a.outfit,
                    "design": f".claude/docs/data/blender/library/outfits-zepeto/{a.outfit}/outfit.py"}
    print(f"outfit/{i}：{(old or {}).get('version', '（新）')} → v{n} released → {save(rec)}")
    return 0


ap = argparse.ArgumentParser()
sub = ap.add_subparsers(dest="cmd", required=True)
p = sub.add_parser("check"); p.add_argument("outfit"); p.add_argument("bodies", nargs="+")
p = sub.add_parser("begin"); p.add_argument("outfit"); p.add_argument("bodies", nargs="+")
p = sub.add_parser("release"); p.add_argument("outfit"); p.add_argument("body"); p.add_argument("--changes", required=True); p.add_argument("--page")
a = ap.parse_args()
sys.exit({"check": cmd_check, "begin": cmd_begin, "release": cmd_release}[a.cmd](a))
