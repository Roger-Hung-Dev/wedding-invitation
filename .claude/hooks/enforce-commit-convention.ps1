<#
.SYNOPSIS
  PreToolUse hook：git commit 訊息必須符合 Conventional Commits 格式，否則阻擋。

.DESCRIPTION
  規範本身寫在 `git-commit-convention` skill，本 hook 只做「格式守門」——
  規範與判準只有一份，這裡不重述 type 該怎麼選（那是語意判斷，shell script 做不到）。

  === 檢查什麼 ===
  只驗第一行（標題行）是否符合：
      <type>(<scope>)!: <subject>
  其中 type ∈ feat|fix|docs|style|refactor|perf|test|chore|revert，
  scope 與 `!` 皆為選填，冒號後必須有一個半形空格與非空的 subject。

  **刻意不驗**的項目（避免誤擋，也因為它們不是「對或錯」而是「好或不好」）：
    - subject 長度（規範建議 ≤ 50 字，但中英夾雜時字數不是好判準）
    - body／footer 的內容與有無
    - type 選得對不對（refactor 還是 perf？shell script 判斷不了）

  === 什麼情況直接放行（失敗開放）===
    - 命令裡沒有 git commit
    - 沒有 -m／--message，也沒有可解析的 heredoc（例如 --amend --no-edit、或開編輯器寫訊息）
    - --fixup／--squash（訊息由 git 自動產生，格式本來就不同）
    - -F <檔案>（訊息在外部檔案裡，本 hook 不讀檔）
    - 訊息以 Merge／Revert 開頭（git 自動產生的訊息）
    - 任何解析失敗

  失敗開放是刻意的：**誤擋一次合法 commit 的代價，遠大於漏擋一次格式不整的 commit。**
  漏擋的可以事後 rebase 改；誤擋會讓人開始想辦法繞過 hook，那才是真正的損失。

  命中則 exit 2 阻擋，stderr 回給模型。
#>

$ErrorActionPreference = 'Stop'

# 以 UTF-8 輸出，否則 stderr 會依主控台編碼（本機 CP950）輸出，回給模型的中文會變亂碼。
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

try {
    # 明確以 UTF-8 解碼 stdin：[Console]::In 會依主控台編碼解碼，
    # 遇到中文訊息會毀損 JSON，使 hook 靜默失效。
    $reader = New-Object System.IO.StreamReader([Console]::OpenStandardInput(), (New-Object System.Text.UTF8Encoding($false)))
    $raw = $reader.ReadToEnd()
    if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }
    $raw = $raw.TrimStart([char]0xFEFF)   # 容忍 BOM：PS 5.1 的 ConvertFrom-Json 遇 BOM 會丟例外
    $payload = $raw | ConvertFrom-Json
}
catch { exit 0 }

$cmd = ''
if ($payload.tool_input -and $payload.tool_input.command) { $cmd = [string]$payload.tool_input.command }
if ([string]::IsNullOrWhiteSpace($cmd)) { exit 0 }

# --- 只管 git commit ---
if ($cmd -notmatch '(?<![\w-])git\s+(?:-[^\s]+\s+)*commit(?![\w-])') { exit 0 }

# --- 訊息由 git 自動產生的情況，放行 ---
if ($cmd -match '--fixup|--squash') { exit 0 }

# --- 取出訊息第一行 ---
$msg = $null

# (a) -m / --message "…" 或 '…'
$m = [regex]::Match($cmd, "(?:^|\s)(?:-m|--message)(?:=|\s+)(?:'([^']*)'|`"((?:[^`"\\]|\\.)*)`")")
if ($m.Success) {
    $msg = if ($m.Groups[1].Success) { $m.Groups[1].Value } else { $m.Groups[2].Value }
}

# (b) heredoc：git commit -F- <<'EOF' … EOF（Git Bash 常用寫法）
if ($null -eq $msg -and $cmd -match '(?:-F|--file)\s*-') {
    $h = [regex]::Match($cmd, "<<-?\s*['`"]?(\w+)['`"]?\s*\r?\n(.*?)\r?\n\1", 'Singleline')
    if ($h.Success) { $msg = $h.Groups[2].Value }
}

# (c) PowerShell here-string：git commit -m @'…'@
if ($null -eq $msg) {
    $p = [regex]::Match($cmd, "(?:-m|--message)\s+@['`"]\s*\r?\n(.*?)\r?\n['`"]@", 'Singleline')
    if ($p.Success) { $msg = $p.Groups[1].Value }
}

# 取不到訊息就放行（開編輯器、--amend --no-edit、-F 外部檔案…都走這裡）
if ([string]::IsNullOrWhiteSpace($msg)) { exit 0 }

$firstLine = ($msg -split "`r?`n" | Where-Object { $_.Trim() -ne '' } | Select-Object -First 1)
if ([string]::IsNullOrWhiteSpace($firstLine)) { exit 0 }
$firstLine = $firstLine.Trim()

# --- git 自動產生的訊息（merge／revert）放行 ---
if ($firstLine -match '^(Merge|Revert)\s') { exit 0 }

# --- 驗格式 ---
# ⚠️ 一律用 -cmatch（區分大小寫）：PowerShell 的 -match 預設**不分大小寫**，
#    用 -match 會讓「Feat(auth): …」通過，而規範明訂 type 必須全小寫。
$types = 'feat|fix|docs|style|refactor|perf|test|chore|revert'
if ($firstLine -cmatch "^($types)(\([^)]+\))?!?: \S") { exit 0 }

# --- 不合格：診斷出「錯在哪」，讓修正一次到位 ---
$hint = ''
if ($firstLine -match '^([A-Za-z]+)(\([^)]*\))?!?:') {
    $bad = $Matches[1]
    if ($bad -cmatch '[A-Z]') {
        $hint = "type「$bad」有大寫 —— type 必須全小寫。"
    } elseif ($bad -match '^(build|ci|improvement|update|add|remove)$') {
        $hint = "「$bad」不在本規範的 type 清單內。建置流程與工具變更請用 chore；新增功能用 feat；修改既有行為視情況用 fix／refactor。"
    } else {
        $hint = "type「$bad」不在允許清單內。"
    }
} elseif ($firstLine -cmatch "^($types)(\([^)]+\))?!?:\S") {
    $hint = '冒號後面少了半形空格 —— 必須是「: 」（冒號＋一個空格）。'
} elseif ($firstLine -cmatch "^($types)(\([^)]+\))?!?:\s*$") {
    $hint = 'subject 是空的 —— 冒號後必須有簡短描述。'
} elseif ($firstLine -notmatch ':') {
    $hint = '整行沒有冒號 —— 缺少「type: 」前綴。'
} else {
    $hint = '第一行不符合「type(scope): subject」的形狀。'
}

[Console]::Error.WriteLine(@"
[hook: enforce-commit-convention] 已阻擋：commit 訊息不符合 Conventional Commits 格式。

你的第一行：
    $firstLine

問題：$hint

正確格式：
    <type>(<scope>): <subject>

    type 必填、全小寫，且必須是下列之一：
      feat     新增或修改新功能
      fix      修復錯誤
      docs     僅修改文件、註解
      style    不影響邏輯的排版修改
      refactor 重構（非新增功能也非修錯）
      perf     效能優化
      test     新增或修改測試
      chore    建置流程、套件依賴、輔助工具
      revert   撤銷先前的 commit

    scope 選填，寫受影響的範圍（auth／api／cart／ui…）。
    冒號後要有一個半形空格。subject 結尾不加句點。

範例：
    feat(auth): 新增使用者 Google 第三方登入功能
    fix(cart): 修正購物車重複點擊導致數量異常的 Bug
    docs(readme): 更新專案安裝與本地執行步驟說明

完整規範（含 type 選用判準、BREAKING CHANGE、切分原則）見 git-commit-convention skill。

⚠️ 被擋的正確反應是**回去挑對 type**，不是把訊息寫得更長或改用其他方式提交。
若你判斷這次確實是規範沒涵蓋的情況，請說明理由並詢問使用者，不要繞過。
"@)
exit 2
