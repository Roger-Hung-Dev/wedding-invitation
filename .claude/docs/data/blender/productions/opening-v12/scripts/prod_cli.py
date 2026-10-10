# 開場影片 V12 的背景 Blender 入口（照 blender-motion-library 的 bl_cli.py；多一個搜尋路徑：本製作的 scripts/）。
#
#   set TEMP=D:\render-work\tmp & set TMP=D:\render-work\tmp
#   "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b <blend> -P prod_cli.py -- --run run_prod MODE=preview SHOT=03 [KEYS=0.5,2.4]
#
# 主命名空間＝新娘專案（PROJ/WHO=bride，她有裙擺物理）；新郎由 prod_env.py 用 scene_lib.add_character() 附加並建自己的命名空間 G。
# KEY=值 會設成全域變數（值先試 JSON）；名稱以 KEYS 結尾的整理成清單。成功最後印 BL_CLI_DONE，失敗印 BL_CLI_FAIL。
import os, sys, json, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, *[".."] * 7))
PROJECT = os.path.join(REPO, ".claude", "docs", "data", "blender", "projects", "bride")
try:
    exec(open(os.path.join(REPO, ".claude", "skills", "blender-motion-library", "scripts", "blender_env.py"), encoding="utf8").read())
    _SEARCH.insert(0, HERE)                     # 本製作的腳本優先（prod_env、set_*、shots_*）
    argv = sys.argv[sys.argv.index("--") + 1:]
    run = argv[argv.index("--run") + 1]
    for a in argv:
        if "=" in a and not a.startswith("--"):
            k, v = a.split("=", 1)
            try:
                v = json.loads(v)
            except Exception:
                pass
            if k.endswith("KEYS") and not isinstance(v, list):
                v = [x for x in str(v).split(",") if x]
            globals()[k] = v
    use(run)
    print("BL_CLI_DONE")
except Exception:
    traceback.print_exc()
    print("BL_CLI_FAIL")
