# Blender 端共用的開機檔：每支在 Blender 裡跑的腳本，第一件事都是 exec 這個檔。
#
# 在 Blender MCP（GUI）裡：
#     PROJECT = r"D:\SideProject\wedding-invitation\.claude\docs\data\blender\projects\bride"
#     exec(open(r"D:\SideProject\wedding-invitation\.claude\skills\blender-motion-library\scripts\blender_env.py", encoding="utf8").read())
#     use("studio", "pose_lib", "actions")
#
# 在背景 Blender（blender.exe -b x.blend -P some_cli.py -- --project <路徑> ...）：
#     CLI 腳本自己 exec 這個檔，PROJECT 從 --project 參數或環境變數 BLENDER_PROJECT 取得。
#
# 提供的全域變數：
#   REPO   專案 repo 根目錄            SKILLS  .claude/skills
#   PROJ   這個角色專案的資料夾         MANIFEST  PROJ/project.json 的內容
#   WHO    物件名稱前綴（例：bride → bride_Armature、bride_Body）
#   WORK   系統暫存的工作資料夾（影格 png、檢查圖；不進 repo）
#   QA     PROJ/qa（量測結果、調好的參數）  PICS  PROJ/pictures   VIDS  PROJ/videos
#   LIB    .claude/docs/data/blender/library（預設資料庫）
#   use(*names)  依名稱載入各 skill 的 scripts/<name>.py（找不到就報錯）
import os, sys, json, tempfile

_here = globals().get("__file__")
if _here and os.path.basename(_here) == "blender_env.py":
    REPO = os.path.abspath(os.path.join(os.path.dirname(_here), "..", "..", "..", ".."))
else:
    REPO = globals().get("REPO") or os.environ.get("WEDDING_REPO") or r"D:\SideProject\wedding-invitation"
SKILLS = os.path.join(REPO, ".claude", "skills")
LIB = os.path.join(REPO, ".claude", "docs", "data", "blender", "library")
_SEARCH = [os.path.join(SKILLS, n, "scripts") for n in
           ("blender-motion-library", "blender-character-build", "blender-scenario", "blender-report-page")]


def _arg(flag):
    if "--" in sys.argv:
        a = sys.argv[sys.argv.index("--") + 1:]
        if flag in a and a.index(flag) + 1 < len(a):
            return a[a.index(flag) + 1]
    return None


PROJ = globals().get("PROJECT") or _arg("--project") or os.environ.get("BLENDER_PROJECT")
if not PROJ:
    raise RuntimeError("沒有指定角色專案：先設 PROJECT = r'<.claude/docs/data/blender/projects/名稱>'，或 CLI 加 --project")
PROJ = os.path.abspath(PROJ)
_mf = os.path.join(PROJ, "project.json")
if not os.path.exists(_mf):
    raise RuntimeError(f"找不到 {_mf}：專案要先用 blender-character-build 的 new_project.py 建立")
MANIFEST = json.load(open(_mf, encoding="utf8"))
WHO = MANIFEST["who"]
WORK = os.path.join(tempfile.gettempdir(), "blender-work", MANIFEST["name"])
QA = os.path.join(PROJ, "qa"); PICS = os.path.join(PROJ, "pictures"); VIDS = os.path.join(PROJ, "videos")
for _d in (WORK, QA, PICS, VIDS):
    os.makedirs(_d, exist_ok=True)
D = WORK                      # 舊腳本的工作資料夾變數，統一指到暫存區


def find_script(name):
    fn = name if name.endswith(".py") else name + ".py"
    for d in [os.path.join(PROJ, "scripts")] + _SEARCH:      # 專案自己的 scripts/ 優先（例：自訂服裝、情境）
        p = os.path.join(d, fn)
        if os.path.exists(p):
            return p
    for d in (os.path.join(SKILLS, "blender-scenario", "scripts", "examples"),
              os.path.join(LIB, "costumes")):                 # 預設服裝規格的自訂元件（例：costume_extra_pink_ballgown）
        p = os.path.join(d, fn)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(f"找不到腳本 {fn}（找過：專案 scripts/、各 blender skill 的 scripts/、library/costumes/）")


def use(*names):
    g = globals()
    for n in names:
        p = find_script(n)
        exec(compile(open(p, encoding="utf8").read(), p, "exec"), g)


def save_manifest():
    json.dump(MANIFEST, open(_mf, "w", encoding="utf8"), ensure_ascii=False, indent=2)
