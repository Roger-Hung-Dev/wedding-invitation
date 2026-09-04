<#
.SYNOPSIS
  PreToolUse hook：pen-drawer／design-question-curator 動筆前，先確認上游分析已完成。

.DESCRIPTION
  設計稿產線（design-lead 團隊）的階段順序是 read → draw-* → annotate，階段間靠
  .claude/docs/design/{批次}/{畫面}.md 這份分析檔交接。跳過 read 直接繪製，畫出來的東西
  沒有依據 —— 這正是「leader 分析錯需求」最可能造成的實害。

  判斷方式（刻意做成「只擋派工過的檔」，不影響直呼）：
    1. 取 mcp__pencil-server__execute 的 filePath。
    2. 看 code 是不是寫入 —— 現行 pencil API 把讀與寫都收在 execute 一支裡，
       純唯讀（只有 Get／Print）一律放行，否則「查一下節點 ID」也會被擋。
    3. 掃 .claude/docs/design/*/_jobs.json，找 penPath 與之相符的 job。
       - 找不到 → 放行（＝使用者直呼 design-question-curator 之類的情境，本來就沒有分析檔）。
    4. 找到 → 檢查該 job 的 analysisPath 是否存在、且含 "readCompleted: true"。
       - 否 → exit 2 阻擋。

  命中則 exit 2 阻擋，stderr 會回給模型。

  ⚠️ 這支 hook 的 matcher 曾經綁在 mcp__pencil-server__batch_design 上，而該工具已不存在 ——
  於是它有一段時間永遠不會觸發，閘門是死的且沒有任何症狀。改工具名時 settings.json 的
  matcher 與本檔的判斷邏輯必須一起改。
#>

$ErrorActionPreference = 'Stop'

# 以 UTF-8 輸出，否則 stderr／stdout 會依主控台編碼（本機 CP950）輸出，
# 回給模型的中文說明會變亂碼、失去指引作用。
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

try {
    # 明確以 UTF-8 解碼 stdin：[Console]::In 會依主控台編碼（本機常為 CP950）解碼，
    # 遇到中文 pen 檔名會毀損 JSON，使 hook 靜默失效（失敗開放）。
    $reader = New-Object System.IO.StreamReader([Console]::OpenStandardInput(), (New-Object System.Text.UTF8Encoding($false)))
    $raw = $reader.ReadToEnd()
    if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }
    $raw = $raw.TrimStart([char]0xFEFF)   # 容忍 BOM：PS 5.1 的 ConvertFrom-Json 遇 BOM 會丟例外
    $payload = $raw | ConvertFrom-Json
}
catch { exit 0 }

$filePath = ''
if ($payload.tool_input -and $payload.tool_input.filePath) { $filePath = [string]$payload.tool_input.filePath }
if ([string]::IsNullOrWhiteSpace($filePath)) { exit 0 }  # 沒帶 filePath 是另一條規則的事（agent 提示已要求必帶）

# 唯讀放行：execute 同時承載讀與寫，只有含寫入函式的呼叫才算「動筆」。
# 判斷保守 —— 取不到 code 時視為寫入（寧可多擋一次，也不要放過一次未分析就動筆）。
$code = ''
if ($payload.tool_input -and $payload.tool_input.code) { $code = [string]$payload.tool_input.code }
if (-not [string]::IsNullOrWhiteSpace($code)) {
    if ($code -notmatch '(?m)\b(Insert|Update|Copy|Replace|Move|Delete|SetVariables|Generate)\s*\(') { exit 0 }
}

$projectDir = $env:CLAUDE_PROJECT_DIR
if ([string]::IsNullOrWhiteSpace($projectDir) -and $payload.cwd) { $projectDir = [string]$payload.cwd }
if ([string]::IsNullOrWhiteSpace($projectDir)) { exit 0 }

$designDir = Join-Path $projectDir '.claude\docs\design'
if (-not (Test-Path $designDir)) { exit 0 }  # 這個專案沒用產線，放行

# 正規化路徑以便比對（去尾斜線、統一分隔符與大小寫）
function Normalize-Path {
    param([string]$P)
    if ([string]::IsNullOrWhiteSpace($P)) { return '' }
    return ($P.Trim().Replace('/', '\').TrimEnd('\')).ToLowerInvariant()
}
$target = Normalize-Path $filePath

$jobsFiles = @(Get-ChildItem -Path $designDir -Recurse -Filter '_jobs.json' -File -ErrorAction SilentlyContinue)
foreach ($jf in $jobsFiles) {
    try { $spec = (Get-Content $jf.FullName -Raw -Encoding UTF8) | ConvertFrom-Json } catch { continue }
    if (-not $spec.jobs) { continue }

    foreach ($job in $spec.jobs) {
        # 注意括號：`Normalize-Path $x -ne $y` 會被當成「呼叫函式並傳入 -ne 參數」，
        # 回傳字串恆為真值，導致每個 job 都被 continue 掉。函式呼叫必須先用括號收斂成值。
        if ((Normalize-Path ([string]$job.penPath)) -ne $target) { continue }

        # 找到對應 job —— 這個 pen 檔是產線派工過的，必須有完成的分析檔才准動筆
        $analysisPath = [string]$job.analysisPath
        if ([string]::IsNullOrWhiteSpace($analysisPath)) {
            [Console]::Error.WriteLine("[hook: require-analysis-before-draw] 已阻擋：$($jf.FullName) 中對應此 pen 檔的 job 沒有 analysisPath。分析檔是各階段的交接點，請 design-lead 補上後再重跑。")
            exit 2
        }

        $full = if ([System.IO.Path]::IsPathRooted($analysisPath)) { $analysisPath } else { Join-Path $projectDir $analysisPath }

        if (-not (Test-Path $full -PathType Leaf)) {
            [Console]::Error.WriteLine(@"
[hook: require-analysis-before-draw] 已阻擋：尚未分析就要動筆。

pen 檔：$filePath
本批次派工清單：$($jf.FullName)
應有的分析檔：$full （不存在）

設計稿產線的階段順序是 read → draw-* → annotate，階段間靠分析檔交接。
請先跑 step "read"（figma-reader）產出分析檔，或由 design-lead 指定既有的 analysisPath。
現在該做的是以 status="blocked" 回報，不要自行推測補完欄位、也不要繞路。
"@)
            exit 2
        }

        $content = ''
        try { $content = Get-Content $full -Raw -Encoding UTF8 } catch {}
        if ($content -notmatch '(?im)^\s*readCompleted\s*:\s*true\s*$') {
            [Console]::Error.WriteLine(@"
[hook: require-analysis-before-draw] 已阻擋：分析檔存在但尚未標記完成。

pen 檔：$filePath
分析檔：$full
缺少：frontmatter 的 readCompleted: true

這一行由 figma-reader 在第 1～7 節與第 9 節都寫完後才寫入，是下游動筆的守門依據。
缺它代表上游分析未完成（可能中途卡關）。請以 status="blocked" 回報，
說明分析檔未完成，由 design-lead 決定補跑 read 或改指定其他 analysisPath。
"@)
            exit 2
        }

        exit 0  # 分析檔齊備，放行
    }
}

exit 0  # 這個 pen 檔不在任何派工清單內（直呼模式），放行
