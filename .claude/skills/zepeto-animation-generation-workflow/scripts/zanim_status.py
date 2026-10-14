# 動畫的產線狀態紀錄（status/anim/<id>.json）：開工、定案、上游清單。格式見 pipeline/README.md；比對上游用 status_check.py。
# 用法（一般 Python，不用 Blender）：
#   python zanim_status.py check <id>
#   python zanim_status.py start <id> [--changes 這次要做什麼]
#   python zanim_status.py release <id> --artifact <final.json> --changes "…" --page <網址> \
#          --body groom --outfit groom-beige-3piece --film opening-proposal-b --prop phone_zp --notes '{"shot": "B2", "duration_s": 4.2}'
# 也可以在 Blender 裡 import 呼叫 start()／release()。
import argparse, datetime, hashlib, json, os, subprocess, sys

PIPE = r"D:/SideProject/wedding-invitation/.claude/docs/data/blender/zepeto/pipeline"
PROPS_BLEND = r"D:/SideProject/wedding-invitation/.claude/docs/data/blender/library/props-zepeto/zepeto_props.blend"
STORY = r"D:/SideProject/wedding-invitation/.claude/docs/storyboard"


def now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def path_of(sid):
    return f"{PIPE}/status/anim/{sid}.json"


def load(sid):
    p = path_of(sid)
    return json.load(open(p, encoding="utf8")) if os.path.exists(p) else None


def save(r):
    p = path_of(r["id"]); os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(r, open(p, "w", encoding="utf8"), ensure_ascii=False, indent=2)
    return p


def check(sid):
    """跑 status_check.py，回傳 (結果第一行, 全文)"""
    r = subprocess.run([sys.executable, "-I", f"{PIPE}/status_check.py", f"anim/{sid}"], capture_output=True, text=True, encoding="utf8")
    out = (r.stdout or "") + (r.stderr or "")
    return out.strip().split("\n")[0] if out.strip() else "", out


def _rec(kind, rid):
    p = f"{PIPE}/status/{kind}/{rid}.json"
    return json.load(open(p, encoding="utf8")) if os.path.exists(p) else None


def upstream(body=None, outfits=(), film=None, props=()):
    """照當下的上游紀錄組 upstream 清單（記版號＋sha）。film 用 status/film/<片名>.json（導演端寫）"""
    ups = []
    for kind, rid in ([("body", body)] if body else []) + [("outfit", o.replace("-", "_") + ("" if "@" in o else "@" + (body or ""))) for o in outfits] \
            + ([("film", film)] if film else []):
        r = _rec(kind, rid)
        if r is None:
            ups.append(dict(kind=kind, id=rid, version=None, sha256=None, note="找不到紀錄"))
        else:
            ups.append(dict(kind=kind, id=rid, version=r["version"], sha256=r["artifact"]["sha256"]))
    if props:
        sh = sha256(PROPS_BLEND) if os.path.exists(PROPS_BLEND) else None
        ups += [dict(kind="prop", id=k, sha256=sh) for k in props]
    return ups


def start(sid, changes=""):
    """開工：紀錄改成 in_progress（artifact 先不動）；第一次做的鏡建一筆新的"""
    r = load(sid) or dict(schema=1, kind="anim", id=sid, version="v0", artifact=dict(path="", sha256=""), upstream=[], changes="", owner="anim")
    r.update(status="in_progress", updated_at=now(), owner="anim")
    if changes:
        r.setdefault("notes", {})["in_progress"] = changes
    return save(r)


def release(sid, artifact, changes, page="", ups=None, notes=None, version=None):
    """定案：新版號（沒給就 +1）、artifact sha、upstream、changes"""
    r = load(sid) or dict(schema=1, kind="anim", id=sid, version="v0")
    v = version or "v%d" % (int(str(r.get("version", "v0")).lstrip("v") or 0) + 1)
    n = dict(r.get("notes", {})); n.pop("in_progress", None); n.update(notes or {})
    r.update(schema=1, kind="anim", id=sid, version=v, status="released", updated_at=now(), owner="anim",
             artifact=dict(path=artifact.replace("\\", "/"), sha256=sha256(artifact)), upstream=ups if ups is not None else r.get("upstream", []),
             changes=changes, notes=n)
    if page:
        r["page"] = page
    return save(r), v


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("cmd", choices=["check", "start", "release"]); a.add_argument("id")
    a.add_argument("--artifact"); a.add_argument("--changes", default=""); a.add_argument("--page", default="")
    a.add_argument("--body"); a.add_argument("--outfit", action="append", default=[]); a.add_argument("--film"); a.add_argument("--prop", action="append", default=[])
    a.add_argument("--notes", default="{}"); a.add_argument("--version")
    x = a.parse_args()
    if x.cmd == "check":
        print(check(x.id)[1])
    elif x.cmd == "start":
        print("開工：", start(x.id, x.changes))
    else:
        p, v = release(x.id, x.artifact, x.changes, x.page, upstream(x.body, x.outfit, x.film, x.prop), json.loads(x.notes), x.version)
        print("定案：", p, v)
