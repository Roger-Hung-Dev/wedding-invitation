"""ZEPETO 產線狀態紀錄檢查：比對每樣產物記的上游 sha 和上游目前的 sha。

用法：
  python status_check.py                       列出全部產物
  python status_check.py outfit/groom_suit@groom   只看這一樣（開工前用）
  python status_check.py --verify              再算一次每個成品檔的 sha256

結束碼：0 一致；1 有產物要重跑、上游未出廠或檔案對不上；2 紀錄格式錯誤。
格式說明見同資料夾 README.md。
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "status"
REQUIRED = ("schema", "kind", "id", "version", "status", "updated_at", "owner", "artifact", "upstream", "changes")
STATUSES = ("in_progress", "released", "retired")
UNTRACKED = ("prop",)   # 不寫狀態紀錄的 kind：只顯示、不擋


def load_all():
    recs, errors = {}, []
    if not ROOT.exists():
        return recs, errors
    for f in sorted(ROOT.glob("*/*.json")):
        key = f"{f.parent.name}/{f.stem}"
        try:
            r = json.loads(f.read_text(encoding="utf-8-sig"))
        except Exception as e:
            errors.append(f"{key}：讀不懂（{e}）")
            continue
        miss = [k for k in REQUIRED if k not in r]
        if miss:
            errors.append(f"{key}：缺欄位 {', '.join(miss)}")
        if r.get("kind") != f.parent.name or r.get("id") != f.stem:
            errors.append(f"{key}：kind／id 和檔案位置不一致（{r.get('kind')}/{r.get('id')}）")
        if r.get("status") not in STATUSES:
            errors.append(f"{key}：status 必須是 {'／'.join(STATUSES)}")
        recs[key] = r
    return recs, errors


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fp:
        for chunk in iter(lambda: fp.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check(key, r, recs, verify):
    """回傳 (狀態字, 說明行list)。狀態字：ok／stale／blocked／broken／wip。"""
    lines, state = [], "ok"
    if r.get("status") == "in_progress":
        return "wip", ["製作中（下游不要用）"]
    if r.get("status") == "retired":
        return "ok", ["已停用"]
    art = r.get("artifact") or {}
    if verify:
        p = art.get("path")
        if not p or not Path(p).exists():
            state = "broken"; lines.append(f"成品檔不見：{p}")
        elif sha256(p) != art.get("sha256"):
            state = "broken"; lines.append("成品檔被改過、紀錄沒更新（sha256 對不上）")
    for up in r.get("upstream") or []:
        ukey = f"{up.get('kind')}/{up.get('id')}"
        u = recs.get(ukey)
        if u is None:
            if up.get("kind") in UNTRACKED:
                lines.append(f"上游 {ukey}：不追蹤")
            else:
                state = "blocked" if state == "ok" else state
                lines.append(f"上游 {ukey}：找不到紀錄")
            continue
        if u.get("status") == "in_progress":
            state = "blocked" if state == "ok" else state
            lines.append(f"上游 {ukey}：還沒出廠（製作中）")
        elif u.get("status") == "retired":
            state = "stale" if state in ("ok",) else state
            lines.append(f"上游 {ukey}：已停用，要換新的上游")
        elif (u.get("artifact") or {}).get("sha256") != up.get("sha256"):
            state = "stale" if state in ("ok", "blocked") else state
            lines.append(f"上游 {ukey}：已更新 {up.get('version')} → {u.get('version')}，要重跑。上游這版改了：{u.get('changes')}")
    return state, lines


LABEL = {"ok": "一致", "stale": "上游已更新", "blocked": "上游未就緒", "broken": "檔案對不上", "wip": "製作中"}


def main(argv):
    verify = "--verify" in argv
    targets = [a for a in argv if not a.startswith("--")]
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    recs, errors = load_all()
    for e in errors:
        print(f"[格式錯誤] {e}")
    if errors:
        return 2
    keys = targets or sorted(recs)
    bad = False
    for key in keys:
        r = recs.get(key)
        if r is None:
            print(f"[找不到] {key}：沒有狀態紀錄（status/{key}.json）")
            bad = True
            continue
        state, lines = check(key, r, recs, verify)
        bad |= state in ("stale", "blocked", "broken")
        print(f"[{LABEL[state]}] {key}  {r.get('version')}（{r.get('status')}，{r.get('updated_at')}）")
        for ln in lines:
            print(f"    - {ln}")
    if not keys:
        print("還沒有任何狀態紀錄。")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
