# 導演端工具（2026-10-12）：分鏡展開檢查、整支片設定登記、剪接清單。讀分鏡展開檔一律借用動畫端的 zanim_spec.py，不另寫一套。
# 用法（一般 Python，不用 Blender）：
#   python director.py status  <片名>                 → 每一鏡的進度：分鏡展開、檢查結果、動畫狀態紀錄；film／edit 紀錄
#   python director.py lint    <片名> [--shot B2]      → 檢查分鏡展開（格式、時間、轉場名稱、上下鏡銜接），彙整缺件清單；exit 1＝有錯
#   python director.py record  <片名>                 → 把 <片名>-breakdown/film.json、edit.json 登記成 status/film、status/edit（內容沒變不升版）
#   python director.py program <片名> --clips <clips.json> [--out program.json]
#        clips.json：{"B0": ["成片.mp4", 鏡內秒數], …}（動畫端「動畫渲染完成」訊息給的）→ render_edit.py 的 program.json
import argparse, datetime, hashlib, json, re, sys
from pathlib import Path

CLAUDE = Path(__file__).resolve().parents[3]
STORY = CLAUDE / "docs/storyboard"
STATUS = CLAUDE / "docs/data/blender/zepeto/pipeline/status"
STYLES = CLAUDE / "docs/data/blender/library/edit-styles-zepeto/catalog.json"
sys.path.insert(0, str(CLAUDE / "skills/zepeto-animation-generation-workflow/scripts"))
import zanim_spec as S  # noqa: E402

SHOT_SIZES = {"遠景", "全景", "中景", "近景", "特寫"}
NONE = ("（無）", "(無)", "")


def bdir(film):
    return STORY / f"{film}-breakdown"


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")


def shot_key(shot):
    """B1→B2 → b1_b2（狀態紀錄 id、檔名都用這個）"""
    return shot.lower().replace("→", "_").replace(" ", "")


def transitions():
    cat = json.loads(STYLES.read_text(encoding="utf8"))
    return {t["name"] for t in cat["transitions"]} | {t["id"] for t in cat["transitions"]}


def spec_files(film):
    return sorted(p for p in bdir(film).glob("*.md") if not p.name.startswith("_"))


def check(sp, names):
    """單一份分鏡展開的錯誤（會擋）與提醒（不擋）"""
    err, warn = [], []
    b = sp["basic"]
    if sp["missing"]:
        err.append("缺段落：" + "、".join(sp["missing"]))
    for k in S.BASIC_KEYS:
        if k not in b:
            err.append(f"「基本」缺「{k}」")
    dur = S._num(b.get("秒數"))
    if dur is None or dur <= 0:
        err.append(f"「秒數」不是正數：{b.get('秒數')!r}")
    tr = b.get("轉場（接上一鏡）", "")
    if tr not in NONE and tr not in names:
        err.append(f"轉場「{tr}」不在剪接樣式庫（可用：{'、'.join(sorted(n for n in names if not n.isascii()))}）")
    for sec in ("鏡頭", "角色與動作", "互動接觸"):
        for i, r in enumerate(sp[sec], 1):
            a, z = r.get("起秒"), r.get("迄秒")
            if a is None or z is None:
                err.append(f"「{sec}」第 {i} 列起秒／迄秒不是數字")
            elif not (0 <= a < z) or (dur and z > dur + 1e-6):
                err.append(f"「{sec}」第 {i} 列 {a}～{z} 秒超出 0～{dur} 或起訖顛倒")
    for i, r in enumerate(sp["鏡頭"], 1):
        if r.get("景別") not in SHOT_SIZES:
            err.append(f"「鏡頭」第 {i} 列景別「{r.get('景別')}」不是 遠景／全景／中景／近景／特寫")
    if dur and sp["鏡頭"]:
        cov = sorted((r["起秒"], r["迄秒"]) for r in sp["鏡頭"] if r.get("起秒") is not None and r.get("迄秒") is not None)
        t = 0.0
        for a, z in cov:
            if a > t + 1e-6:
                warn.append(f"「鏡頭」{t}～{a} 秒沒有寫到")
            t = max(t, z)
        if t < dur - 1e-6:
            warn.append(f"「鏡頭」{t}～{dur} 秒沒有寫到")
    for i, r in enumerate(sp["字卡時間碼"], 1):
        a, z = r.get("進場秒"), r.get("退場秒")
        if a is None:
            err.append(f"「字卡時間碼」第 {i} 列進場秒不是數字")
        elif z is not None and z <= a:
            err.append(f"「字卡時間碼」第 {i} 列退場 {z} 不晚於進場 {a}")
        elif dur and a >= dur:
            err.append(f"「字卡時間碼」第 {i} 列進場 {a} 秒已經超過這一鏡 {dur} 秒")
    if not sp["角色與動作"]:
        warn.append("「角色與動作」是空的")
    return err, warn


def lint(film, only=None):
    names = transitions()
    specs, shots, errors, warns = {}, [], [], []
    miss = {}
    for p in spec_files(film):
        sp = S.parse(str(p))
        sid = sp["basic"].get("鏡號", p.stem)
        specs[sid] = sp
    for sid, sp in specs.items():
        if only and sid != only:
            continue
        e, w = check(sp, names)
        exp = shot_key(sid) + ".md"
        if Path(sp["path"]).name != exp:
            e.append(f"檔名應為 {exp}")
        for side, other_key in (("上一鏡", "下一鏡"), ("下一鏡", "上一鏡")):
            o = sp["basic"].get(side, "（無）")
            if o in NONE:
                continue
            if o not in specs:
                w.append(f"{side} {o} 還沒有分鏡展開")
            elif specs[o]["basic"].get(other_key) != sid:
                e.append(f"{side}是 {o}，但 {o} 的{other_key}寫「{specs[o]['basic'].get(other_key)}」")
        for kind, v in sp["道具與場景"].items():
            for x in v.get("缺", []):
                miss.setdefault(kind, {}).setdefault(x, []).append(sid)
        shots.append(dict(shot=sid, path=sp["path"], seconds=S._num(sp["basic"].get("秒數")),
                          errors=e, warnings=w, feedback_rounds=sorted(sp["回饋"])))
        errors += [f"{sid}：{x}" for x in e]
        warns += [f"{sid}：{x}" for x in w]
    total = sum(s["seconds"] or 0 for s in shots)
    return dict(film=film, ok=not errors, total_s=round(total, 2), shots=shots, errors=errors, warnings=warns,
                missing={k: [dict(item=i, shots=v) for i, v in d.items()] for k, d in miss.items()})


def order(film):
    """照「上一鏡／下一鏡」排出播放順序（從沒有上一鏡的那份開始）"""
    specs = {S.parse(str(p))["basic"].get("鏡號"): S.parse(str(p)) for p in spec_files(film)}
    heads = [k for k, v in specs.items() if v["basic"].get("上一鏡", "（無）") in NONE]
    seq, cur = [], heads[0] if heads else None
    while cur in specs and cur not in seq:
        seq.append(cur)
        cur = specs[cur]["basic"].get("下一鏡")
    return [specs[k] for k in seq], [k for k in specs if k not in seq]


def write_record(kind, film, artifact, upstream, changes, notes):
    path = STATUS / kind / f"{film}.json"
    sha = sha256(artifact)
    old = json.loads(path.read_text(encoding="utf8")) if path.exists() else None
    if old and old["artifact"]["sha256"] == sha and old.get("upstream") == upstream:
        return path, old["version"], False
    data = json.loads(Path(artifact).read_text(encoding="utf8"))
    ver = data.get("version")
    ver = (f"v{ver}" if isinstance(ver, int) else ver) or (f"v{int(old['version'][1:]) + 1}" if old else "v1")
    rec = dict(schema=1, kind=kind, id=film, version=ver, status="released", updated_at=now(), owner="director",
               artifact=dict(path=str(artifact).replace("\\", "/"), sha256=sha), upstream=upstream,
               changes=changes, page=None, notes=notes)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    return path, ver, True


def record(film):
    d = bdir(film)
    film_json, edit_json = d / "film.json", d / "edit.json"
    out = {}
    if film_json.exists():
        p, v, new = write_record("film", film, film_json, [], "整支片規格（render-settings 面板；影響動畫）",
                                 dict(film=film, fields="aspect、fps、handles_s、background、occluders、caption_safe"))
        out["film"] = dict(path=str(p), version=v, updated=new)
    if edit_json.exists():
        fr = json.loads((STATUS / "film" / f"{film}.json").read_text(encoding="utf8")) if film_json.exists() else None
        up = [dict(kind="film", id=film, version=fr["version"], sha256=fr["artifact"]["sha256"])] if fr else []
        p, v, new = write_record("edit", film, edit_json, up, "字卡與轉場（render-settings 面板；只影響剪接）",
                                 dict(film=film))
        out["edit"] = dict(path=str(p), version=v, updated=new)
    return out


def status(film):
    r = lint(film)
    for s in r["shots"]:
        a = STATUS / "anim" / f"{shot_key(s['shot'])}.json"
        rec = json.loads(a.read_text(encoding="utf8")) if a.exists() else None
        s["anim"] = f"{rec['version']} {rec['status']}" if rec else "未開工"
        s["lint"] = "OK" if not s["errors"] else f"{len(s['errors'])} 個錯"
        for k in ("errors", "warnings", "path"):
            s.pop(k)
    recs = {k: (json.loads((STATUS / k / f"{film}.json").read_text(encoding="utf8"))["version"]
                if (STATUS / k / f"{film}.json").exists() else "未登記") for k in ("film", "edit")}
    return dict(film=film, script=str(STORY / f"{film}-script.md"), records=recs, total_s=r["total_s"],
                shots=r["shots"], missing=r["missing"])


def program(film, clips_path):
    film_json = bdir(film) / "film.json"
    handles = json.loads(film_json.read_text(encoding="utf8")).get("handles_s", 0.0) if film_json.exists() else 0.0
    clips = {k: tuple(v) for k, v in json.loads(Path(clips_path).read_text(encoding="utf8")).items()}
    seq, orphan = order(film)
    lack = [sp["basic"]["鏡號"] for sp in seq if sp["basic"]["鏡號"] not in clips]
    if lack:
        sys.exit("clips.json 缺這幾鏡的成片：" + "、".join(lack))
    if orphan:
        print("⚠ 這幾份沒接進上下鏡的順序、不會進剪接：" + "、".join(orphan), file=sys.stderr)
    prog = S.program(seq, clips, handles)
    prog["caption_hold"] = "until_next"   # 退場秒空白的字卡跨鏡留到下一張進場（使用者 2026-10-12 決定的全片規則）
    return prog


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["status", "lint", "record", "program"])
    ap.add_argument("film")
    ap.add_argument("--shot")
    ap.add_argument("--clips")
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.cmd == "lint":
        r = lint(a.film, a.shot)
    elif a.cmd == "status":
        r = status(a.film)
    elif a.cmd == "record":
        r = record(a.film)
    else:
        if not a.clips:
            sys.exit("program 要給 --clips")
        r = program(a.film, a.clips)
        if a.out:
            Path(a.out).write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(r, ensure_ascii=False, indent=1))
    if a.cmd == "lint" and not r["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
