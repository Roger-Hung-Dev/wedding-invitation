# 背景 Blender 的統一入口（不受 Blender MCP 120 秒限制，可和開著的 GUI Blender 並行）：
#
#   "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b <專案>.blend -P <本檔> -- --project <專案資料夾> --run <腳本名> [KEY=值 ...]
#
# --run：要執行的腳本（依 blender_env.use() 的搜尋順序找，例：run_analyse、render_actions、build_costume、showcase、run_scene）
# KEY=值：設成全域變數給腳本用。值會先試著當 JSON 解讀（數字、true、["a","b"]），失敗就當字串；逗號分隔的字串給 *KEYS 會自動拆成清單。
# 成功時最後印 BL_CLI_DONE，失敗印 BL_CLI_FAIL 和 traceback。
import os, sys, json, traceback

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
try:
    exec(open(os.path.join(os.path.dirname(__file__), "blender_env.py"), encoding="utf8").read())
    argv = sys.argv[sys.argv.index("--") + 1:]
    run = argv[argv.index("--run") + 1]
    for a in argv:
        if "=" in a and not a.startswith("--"):
            k, v = a.split("=", 1)
            try:
                v = json.loads(v)
            except Exception:
                pass
            if k.endswith("KEYS") and not isinstance(v, list):      # KEYS=40 或 KEYS=a,b 都整理成清單
                v = [x for x in str(v).split(",") if x]
            globals()[k] = v
    use(run)
    print("BL_CLI_DONE")
except Exception:
    traceback.print_exc()
    print("BL_CLI_FAIL")
