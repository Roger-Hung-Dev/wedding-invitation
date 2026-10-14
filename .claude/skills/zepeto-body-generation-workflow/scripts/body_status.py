# 身體的開工／取消／出廠：同時維護兩份紀錄
#   ① 出廠標記 D:/render-work/zepeto-body/build/RELEASE.json（身體出廠閘門 hook require-body-release.ps1 讀這份）
#   ② 產線狀態紀錄 .claude/docs/data/blender/zepeto/pipeline/status/body/<人>.json（格式見 pipeline/README.md，下游開工前比對）
#
# 做身體一律在暫存資料夾 build/<人>.work/（和 build/<人>/ 同一層，檔內相對路徑才不會斷），出廠時才複製到 build/<人>/。
# 所以做到一半時，下游手上的已出廠身體檔一個位元都沒變。
#
# 用法（python -I 執行，輸出 UTF-8）：
#   python -I body_status.py check   <人> [<人> ...]       開工前：頭有沒有更新、身體現在的狀態
#   python -I body_status.py begin   <人> --head <head_rig.blend>
#        開工：狀態紀錄改 in_progress；這個人已經出廠過 → RELEASE.json 的 bodies.<人>.status 與總 status 改 in_progress
#        （閘門 2026-10-12 起逐身體：點名這個人的擋、點名別人的放行、沒點名的看總狀態）
#   python -I body_status.py cancel  <人>                   放棄這次修改：已出廠的身體檔沒被動過 → 兩份紀錄改回 released
#   python -I body_status.py release <人> --changes "這版改了什麼（白話）" [--page 審看頁網址] [--tag 版本代號英文]
#        出廠：build/<人>.work/checks.json 全過且比 body.blend 新 → 舊版封存到 build/_archive/<人>_<版本>/ →
#        暫存資料夾複製到 build/<人>/ → 寫 RELEASE.json 與狀態紀錄（版本加 1、上游記頭的 sha）→ 跑 status_check.py
# 結束碼：0 成功（check：可以開工）；1 有問題（印出原因）。
import argparse, datetime, hashlib, io, json, shutil, subprocess, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]                                          # 專案根目錄
PIPE = ROOT / ".claude" / "docs" / "data" / "blender" / "zepeto" / "pipeline"
BUILD = Path("D:/render-work/zepeto-body/build")
REL = BUILD / "RELEASE.json"
ZH = {"groom": "新郎", "bride": "新娘"}

# 每一版都附的交接說明（這版改了什麼另外接在後面）
HANDOFF_BASE = (
    "骨頭名稱 J_Bip_*（VRoid 同名），T 字靜止姿勢，四指併攏、拇指方向和 Mixamo 一致。"
    "手的部分有第二個 Armature 修改器 Armature_HandVolume（Preserve Volume、頂點群組 HAND_DQS）：服裝抄權重時略過 HAND_DQS，也不要複製這個修改器。"
    "手勢一律用共用 mixamo_retarget.GESTURE 的名稱；骨架帶自訂屬性 thumb_contact、gesture_overrides，Target 會自動讀。"
    "頭掛在 J_Bip_C_Head 骨下，脖子切口以下藏掉；身體有 UV（Smart UV Project：全身布紋粗細一致，島的方向不一致，有方向的布紋請在衣服網格上重新對齊）。"
)


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rjson(p, default=None):
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8-sig")) if p.is_file() else default


def wjson(p, d, indent=2):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8", newline="\n")


def status_path(name):
    return PIPE / "status" / "body" / f"{name}.json"


def heads():
    r = subprocess.run([sys.executable, "-I", str(HERE / "list_heads.py")], capture_output=True)
    return {h["name"]: h for h in json.loads(r.stdout.decode("utf-8"))["heads"]}


def release_all_ok(rel):
    """RELEASE.json 的總狀態：每個登記的身體都是 released 而且檔案指紋對得上，才算 released（hook 照舊只看總狀態＋指紋）"""
    for n, b in rel.get("bodies", {}).items():
        if b.get("status", "released") != "released" or not Path(b["blend"]).is_file() or sha(b["blend"]) != b["sha256"]:
            return False
    return True


def cmd_check(names):
    hs = heads(); bad = False
    for n in names:
        rec = rjson(status_path(n)); h = hs.get(n)
        if not h:
            print(f"[沒有頭] {n}：list_heads.py 找不到這個人的頭，不能做身體"); bad = True; continue
        if not h["ready"]:
            print(f"[頭未就緒] {n}：頭的狀態 {h['status']}，要等大頭端做完"); bad = True; continue
        if not rec:
            print(f"[新身體] {n}：還沒有身體，照常開工（頭 {h['version']}）"); continue
        up = next((u for u in rec.get("upstream", []) if u["kind"] == "head"), None)
        if rec["status"] == "in_progress":
            print(f"[製作中] {n}：上次開工後沒有出廠也沒取消，接著做或先 cancel")
        if not up:
            continue                                            # 還沒出廠過的身體沒有上游紀錄，上面那行已經說明
        if up["sha256"] != h["sha256"]:
            print(f"[頭已更新] {n}：身體 {rec['version']} 用的頭是 {up.get('version')}（{up['sha256'][:12]}），現在是 {h['version']}（{h['sha256'][:12]}）→ 要重做身體")
        else:
            print(f"[一致] {n}：身體 {rec['version']}（{rec['status']}），頭沒變")
    return 1 if bad else 0


def cmd_begin(name, head):
    rel = rjson(REL, {"bodies": {}})
    rec = rjson(status_path(name))
    if rec is None:
        rec = dict(schema=1, kind="body", id=name, version="v0", status="in_progress", updated_at=now(), owner="body",
                   artifact=dict(path=str(BUILD / name / "body.blend").replace("\\", "/"), sha256=""), upstream=[],
                   changes="新身體，製作中")
    rec["status"] = "in_progress"; rec["updated_at"] = now()
    rec.setdefault("notes", {})["work_head"] = str(head).replace("\\", "/")
    wjson(status_path(name), rec)
    if name in rel.get("bodies", {}):
        rel["bodies"][name]["status"] = "in_progress"
        rel["status"] = "in_progress"
        rel["note"] = f"{name} 修改中（{now()}）"
        wjson(REL, rel, 1)
        print(f"閘門已關：{name} 修改期間，點名 {name}（或沒點名身體）的服裝、動畫 Blender 執行會被擋；點名其他身體的照常放行")
    else:
        print(f"{name} 是新身體：不動 RELEASE.json，其他已出廠的身體照常可用")
    (BUILD / f"{name}.work").mkdir(parents=True, exist_ok=True)
    print(f"開工：暫存資料夾 {BUILD / f'{name}.work'}；狀態紀錄 {status_path(name)} → in_progress")
    return 0


def cmd_cancel(name):
    rel = rjson(REL, {"bodies": {}}); rec = rjson(status_path(name))
    b = rel.get("bodies", {}).get(name)
    if b and Path(b["blend"]).is_file() and sha(b["blend"]) == b["sha256"]:
        b["status"] = "released"; rel.pop("note", None)
        if release_all_ok(rel):
            rel["status"] = "released"
        wjson(REL, rel, 1)
        if rec:
            rec["status"] = "released"; rec["updated_at"] = now(); rec.get("notes", {}).pop("work_head", None)
            wjson(status_path(name), rec)
        print(f"已取消：{name} 回到已出廠的 {rec['version'] if rec else ''}（檔案沒被動過）；閘門總狀態 {rel['status']}")
        return 0
    if not b:
        if rec and rec["version"] == "v0":
            status_path(name).unlink()
        print(f"已取消：{name} 是新身體，沒有出廠過；狀態紀錄已移除，暫存資料夾留著")
        return 0
    print(f"不能取消：{name} 已出廠的身體檔指紋對不上（被改過），要重新出廠"); return 1


LABEL = {"length": "腳長", "heel_to_ball": "腳跟到腳掌", "ankle_joint_height": "腳踝關節高", "ball_girth": "腳掌圍", "ball_width": "腳掌寬",
         "ball_height": "腳掌高", "instep_girth": "腳背圍", "instep_width": "腳背寬", "instep_height": "腳背高", "heel_width": "腳跟寬",
         "waist_girth": "鞋楦腰圍", "toe_height": "腳趾高", "toe_girth": "腳趾圍", "arch_height": "足弓高", "ankle_girth": "腳踝圍",
         "min_leg_girth": "最小腿圍", "calf_girth": "小腿最粗圍", "knee_girth": "膝圍", "thigh_girth": "大腿最粗圍", "wrist_girth": "手腕圍",
         "forearm_max_girth": "前臂最粗圍", "upper_arm_girth": "上臂圍", "hand_length": "手長", "hand_breadth": "手寬",
         "ring_girth": "脖子接口圍", "min_girth": "脖子最細圍", "cut_z": "脖子接口高"}


def measure_diff(prev, cur):
    """交接尺寸和上一個出廠版比：變化 ≥ 1 mm 或 ≥ 1% 列一行（研究 3.4）。prev 沒有 → 全部列「新增」"""
    out = []
    for grp in ("foot", "leg", "arm", "neck"):
        p, c = (prev or {}).get(grp, {}), (cur or {}).get(grp, {})
        for k, v in c.items():
            if not isinstance(v, (int, float)):
                continue
            o = p.get(k)
            if not isinstance(o, (int, float)):
                if prev:
                    out.append(f"{LABEL.get(k, k)} 新增 {v} mm")
                continue
            d = v - o
            if abs(d) >= 1.0 or (o and abs(d) / abs(o) >= 0.01):
                out.append(f"{LABEL.get(k, k)} {o} → {v} mm（{d:+.1f}）")
    return out


def cmd_release(name, changes, page, tag):
    work = BUILD / f"{name}.work"; wb = work / "body.blend"; ck = work / "checks.json"; bj = work / "build.json"
    if not wb.is_file():
        print(f"沒有 {wb}"); return 1
    if not ck.is_file() or ck.stat().st_mtime < wb.stat().st_mtime:
        print("checks.json 不存在或比 body.blend 舊：存檔後要重跑 body_checks.py"); return 1
    checks = rjson(ck); fail = [k for k, v in checks.items() if not v.get("pass")]
    if fail:
        print(f"出廠檢查沒過：{fail}"); return 1
    build = rjson(bj, {}); hd = build.get("head", {})
    hs = heads(); h = next((x for x in hs.values() if x["sha256"] == hd.get("sha256")), None)
    rec = rjson(status_path(name)) or {}
    old_v = int(str(rec.get("version", "v0")).lstrip("v") or 0); ver = f"v{old_v + 1}"
    rel = rjson(REL, {"bodies": {}})
    dest = BUILD / name
    if dest.is_dir() and (dest / "body.blend").is_file():                # 舊版封存
        arc = BUILD / "_archive" / f"{name}_{rec.get('version', 'old')}"
        if not arc.exists():
            shutil.copytree(dest, arc)
        shutil.rmtree(dest)
    shutil.copytree(work, dest)
    blend = dest / "body.blend"; s = sha(blend)
    assert s == sha(wb), "複製後指紋不一致"
    stamp = datetime.date.today().strftime("%Y%m%d")
    release_version = f"body-{ver}-{tag + '-' if tag else ''}{stamp}"
    meas = build.get("measure")
    prev_meas = (rel.get("bodies", {}).get(name) or {}).get("measure")
    mdiff = measure_diff(prev_meas, meas) if meas and "error" not in meas else []
    if mdiff:
        changes = changes + "；交接尺寸變化（≥1 mm 或 ≥1%）：" + "、".join(mdiff[:15]) + ("…" if len(mdiff) > 15 else "")
    rel.setdefault("bodies", {})[name] = dict(
        path=str(blend), blend=str(blend), sha256=s, status="released", version=release_version, released_at=now(),
        head=dict(path=hd.get("path"), sha256=hd.get("sha256"), version=h["version"] if h else None),
        checks=checks, handoff=HANDOFF_BASE + f"這版（{ver}）：{changes}", measure=meas, measure_changes=mdiff)
    rel["version"] = release_version; rel["released_at"] = now(); rel.pop("note", None)
    rel["status"] = "released" if release_all_ok(rel) else "in_progress"
    rel["checks"] = checks; rel["handoff"] = rel["bodies"][name]["handoff"]     # 舊欄位（只有一個身體時的讀法）
    wjson(REL, rel, 1)
    n_pass = len(checks)
    new = dict(schema=1, kind="body", id=name, version=ver, status="released", updated_at=now(), owner="body",
               artifact=dict(path=str(blend).replace("\\", "/"), sha256=s),
               upstream=[dict(kind="head", id=h["name"] if h else name, version=h["version"] if h else "unknown", sha256=hd.get("sha256"))],
               changes=changes)
    if page:
        new["page"] = page
    new["notes"] = dict(release_version=release_version, checks=f"{n_pass} 項全過；完整數字在 {REL}", head_path=hd.get("path"))
    wjson(status_path(name), new)
    print(f"已出廠：{name} {ver}（{release_version}） sha {s[:12]}；閘門總狀態 {rel['status']}")
    print("下游比對：")
    r = subprocess.run([sys.executable, "-I", str(PIPE / "status_check.py")], capture_output=True)
    print(r.stdout.decode("utf-8", "replace"))
    return 0


ap = argparse.ArgumentParser()
ap.add_argument("cmd", choices=["check", "begin", "cancel", "release"])
ap.add_argument("names", nargs="+")
ap.add_argument("--head"); ap.add_argument("--changes"); ap.add_argument("--page"); ap.add_argument("--tag", default="")
a = ap.parse_args()
if a.cmd == "check":
    sys.exit(cmd_check(a.names))
if len(a.names) != 1:
    sys.exit("begin／cancel／release 一次一個人")
if a.cmd == "begin":
    if not a.head:
        sys.exit("begin 要給 --head")
    sys.exit(cmd_begin(a.names[0], a.head))
if a.cmd == "cancel":
    sys.exit(cmd_cancel(a.names[0]))
if not a.changes:
    sys.exit("release 要給 --changes")
sys.exit(cmd_release(a.names[0], a.changes, a.page, a.tag))
