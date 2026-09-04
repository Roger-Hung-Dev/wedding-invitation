<#
.SYNOPSIS
  PostToolUse hook：程式碼檔寫入後，掃描註解是否違反 *-coding-standards 的「§8 註解（鐵律）」。

.DESCRIPTION
  === 為什麼需要這個 hook ===
  註解規範已經寫進五份 *-coding-standards（agent 預載），但實測顯示光有規範不夠：

    - 全新乾淨專案（無規格文件可沉浸）實測 22 個檔：`<summary>` 單行率 33%（25/75），
      另有宣告上方堆疊 `//`、`<param>` 只把參數名翻成中文。
    - 實際專案中對代理「口頭提醒」兩次後，違規數不減反增（26 → 39）——
      代理手上攤著滿是 BR-xxx 與圖示的規格文件，規格的體例會直接滲進程式碼；
      提醒是一次性的，沉浸是持續的。
    - 根因不是不服從，是**代理從不驗證自己改完沒有**，憑印象認定已修正。
      工程代理的「自我檢查」清單（agent 檔內）列的是相依方向／DI／nullable／
      信封／密鑰，註解不在其中，而代理收尾時照清單走。

  所以這件事不能靠自覺，要靠機械檢核 —— 與本工作區既有的「不靠模型自制、靠留痕」同源。

  === 刻意只查「機械可判」的項目 ===
  hook 是 script，做不了語意判斷。以下這些**刻意不查**，因為誤報比漏報更糟
  （誤報會訓練代理忽略這個 hook，那等於整個機制失效）：
    - 「註解有沒有複述程式碼」「寫的是為什麼還是做什麼」—— 純語意。
    - 「該寫 `///` 的成員有沒有寫」—— 需要判斷跨層與否，且 §8.1 明訂很多情況不必寫。
    - 「被註解掉的程式碼」—— 與正常的中文說明難以區分。
    - 「多行標籤縮排一層」—— 續行與折行的界線需要讀懂句子。

  查的是七項字面上就能判定對錯的：見下方 $checks。

  === 為什麼是 PostToolUse 而不是 PreToolUse ===
  PreToolUse 要擋下寫入，代理就得在「還沒看到檔案長相」的情況下重寫整份內容，
  容易連正確的部分一起改壞。PostToolUse 讓檔案先落地，再把「第幾行、違反哪一條」
  指出來，代理用 Edit 逐點修即可，這也是它最擅長的操作。
  exit 2 使 stderr 回給模型（PostToolUse 的 exit 2 不撤銷已完成的寫入）。

  === 噪音控制 ===
  不做「一個 session 只提醒一次」—— 每個檔都要各自修，靜音會讓後面的檔全部漏掉。
  改以「沒有違規就完全靜默」控制噪音：乾淨的檔案不會產生任何輸出。
#>

$ErrorActionPreference = 'Stop'

# 以 UTF-8 輸出，否則 stderr 會依主控台編碼（本機 CP950）輸出，回給模型的中文會變亂碼。
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

try {
    # 明確以 UTF-8 解碼 stdin：[Console]::In 會依主控台編碼解碼，
    # 遇到中文路徑會毀損 JSON，使 hook 靜默失效（失敗開放）。
    $reader = New-Object System.IO.StreamReader([Console]::OpenStandardInput(), (New-Object System.Text.UTF8Encoding($false)))
    $raw = $reader.ReadToEnd()
    if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }
    $raw = $raw.TrimStart([char]0xFEFF)   # 容忍 BOM：PS 5.1 的 ConvertFrom-Json 遇 BOM 會丟例外
    $payload = $raw | ConvertFrom-Json
}
catch { exit 0 }

$filePath = ''
if ($payload.tool_input -and $payload.tool_input.file_path) { $filePath = [string]$payload.tool_input.file_path }
if ([string]::IsNullOrWhiteSpace($filePath)) { exit 0 }

$norm = $filePath.Trim().Replace('/', '\')
$lower = $norm.ToLowerInvariant()

# --- 只認程式碼檔；產生物與相依目錄一律略過 ---
$ext = [System.IO.Path]::GetExtension($lower)
if ($ext -ne '.cs' -and $ext -ne '.ts') { exit 0 }
if ($lower -match '\\(node_modules|bin|obj|dist|build|\.git)\\') { exit 0 }
if ($lower -match '\.(d|min|designer|g|generated)\.(ts|cs)$') { exit 0 }   # 產生的檔不歸代理管

if (-not (Test-Path -LiteralPath $norm)) { exit 0 }
try {
    $lines = [System.IO.File]::ReadAllLines($norm, [System.Text.Encoding]::UTF8)
}
catch { exit 0 }
if ($lines.Count -eq 0) { exit 0 }

$isCs = ($ext -eq '.cs')
$findings = New-Object System.Collections.ArrayList

function Add-Finding([int]$lineNo, [string]$rule, [string]$detail) {
    [void]$findings.Add([pscustomobject]@{ Line = $lineNo; Rule = $rule; Detail = $detail })
}

# 圖示偵測：
#   - [\uD800-\uDBFF] 是 UTF-16 高代理項，代表 astral 平面字元（絕大多數 emoji）
#   - BMP 區的常見圖示：雜項符號、印刷符號、雜項技術符號
#   刻意不含 U+2190-U+21FF（箭頭）—— 「→」在中文說明裡是正常用字，規範也沒禁。
#   中文全形標點在 U+3000-U+303F，不在範圍內，不會誤判。
$iconPattern = '[\uD800-\uDBFF\u2600-\u27BF\u2B00-\u2BFF\u2300-\u23FF\u2705\u274C\u26A0\u26D4]'

# 規格章節與編號引用：§ 或 BR-／VR-／IR-／OI- 後接數字
$specRefPattern = '(\u00A7|\b(BR|VR|IR|OI)-\d)'

for ($i = 0; $i -lt $lines.Count; $i++) {
    $line = $lines[$i]
    $lineNo = $i + 1
    $trimmed = $line.TrimStart()

    $isDocComment = $isCs -and $trimmed.StartsWith('///')
    $isJsDoc = (-not $isCs) -and ($trimmed.StartsWith('*') -or $trimmed.StartsWith('/**'))
    $isLineComment = $trimmed -match '^//(?!/)' -or ($isCs -eq $false -and $trimmed.StartsWith('//'))
    $isAnyComment = $isDocComment -or $isJsDoc -or $isLineComment

    if (-not $isAnyComment) { continue }

    # --- 規則 1：註解中的圖示／表情符號（§8.2 格式：純文字）---
    if ($line -match $iconPattern) {
        Add-Finding $lineNo '禁止圖示' '註解只用純文字。圖示沒有一致定義、無法搜尋，要強調就把話講清楚。'
    }

    # --- 規則 2：引用規格章節或編號（§8.2 格式）---
    if ($line -match $specRefPattern) {
        Add-Finding $lineNo '禁止引用規格編號' '規格會改版、章節會位移，引用很快指向錯的地方。要講的重點直接寫成一句話。'
    }

    # --- 規則 3：單行 <summary>（§8.1 排版：一律三行式）---
    if ($isDocComment -and $line -match '<summary>.*</summary>') {
        Add-Finding $lineNo '<summary> 須三行式' '開始標籤、內容、結束標籤各一行，即使內容只有一句也一樣。'
    }

    # --- 規則 4：空標籤（§8.1：要嘛寫滿、要嘛整段不寫）---
    if ($isDocComment -and $line -match '<(param[^>]*|returns|response[^>]*|exception[^>]*)>\s*</(param|returns|response|exception)>') {
        Add-Finding $lineNo '禁止空標籤' '空殼標籤是噪音。寫不出內容就整段 /// 不要寫，不要留著佔位。'
    }
    if ($isJsDoc -and $line -match '^\s*\*\s*@(param|returns|throws)\s+\S+\s*$') {
        Add-Finding $lineNo '禁止空標籤' '@param／@returns 後面沒有說明是噪音。要嘛寫滿、要嘛整段不寫。'
    }

    # --- 規則 5：@param 帶型別大括號（僅 TS；型別由 TS 負責，寫兩份會走鐘）---
    if ($isJsDoc -and $line -match '@param\s*\{') {
        Add-Finding $lineNo '@param 不帶型別' '型別由 TypeScript 負責。寫 `@param userId 說明`，不要寫 `@param {string} userId`。'
    }

    # --- 規則 6：裸 TODO／HACK（§8.2：一律附原因與解除條件）---
    if ($isLineComment -and $line -match '(TODO|HACK|FIXME)') {
        $after = ($line -replace '^.*?(TODO|HACK|FIXME)\s*:?\s*', '').Trim()
        if ($after.Length -lt 10) {
            Add-Finding $lineNo '裸 TODO' 'TODO／HACK 一律附上原因與解除條件，不得只留一個標記。'
        }
    }

    # --- 規則 7：分隔線橫幅（§8.2 禁止）---
    if ($isLineComment -and $line -match '(=|-|\*|#){6,}') {
        Add-Finding $lineNo '禁止分隔線橫幅' '需要分區代表該拆方法或拆類別了。'
    }
}

# --- 規則 8：宣告上方堆疊 `//`（§8.0 明令禁止）---
# 判定條件刻意收緊，避免把「方法內部的區域變數宣告」誤判成成員宣告：
#   C#  ：後接行以存取修飾詞或屬性 `[` 開頭 —— 這兩者不會出現在方法內部。
#   TS  ：後接行以 export／class／interface／function／裝飾器開頭 —— 頂層宣告才算。
# 「1 行 //」不算堆疊（§8.0 談的是「堆一疊」），只抓連續 2 行以上，把誤報壓到最低。
$run = 0
$runStart = 0
for ($i = 0; $i -lt $lines.Count; $i++) {
    $trimmed = $lines[$i].TrimStart()
    $isPlainComment = ($trimmed -match '^//') -and (-not $trimmed.StartsWith('///'))

    if ($isPlainComment) {
        if ($run -eq 0) { $runStart = $i + 1 }
        $run++
        continue
    }

    if ($run -ge 2) {
        $decl = $false
        if ($isCs) {
            $decl = $trimmed -match '^(public|private|protected|internal)\s' -or $trimmed -match '^\['
        }
        else {
            $decl = $trimmed -match '^(export|class|interface|abstract\s+class|function|async\s+function)\s' -or $trimmed -match '^@[A-Z]'
        }
        if ($decl) {
            $kind = if ($isCs) { '/// XML 文件註解' } else { '/** */ JSDoc' }
            Add-Finding $runStart '宣告上方禁止堆疊 //' "說明一個成員是文件註解的工作。改用 $kind —— 堆疊 // 會讓 IDE tooltip、Swagger、文件產生器全部讀不到。這條與長度無關。"
        }
    }
    $run = 0
}

if ($findings.Count -eq 0) { exit 0 }

$sorted = $findings | Sort-Object Line
$detail = ($sorted | ForEach-Object { "  第 {0} 行 [{1}] {2}" -f $_.Line, $_.Rule, $_.Detail }) -join "`n"
$ruleList = ($sorted | Select-Object -ExpandProperty Rule -Unique) -join '、'
$standards = if ($isCs) { 'net-webapi-coding-standards' } else { 'express-／nestjs-／angular-／vue3-coding-standards（依專案技術棧）' }

[Console]::Error.WriteLine(@"
[hook: check-comment-standards] $filePath 的註解有 $($findings.Count) 處違反規範（$ruleList）：

$detail

**請立刻用 Edit 修正這些行，不要留到收尾。** 規則出處：$standards 的「§8 註解（鐵律）」。

提醒兩件事：
1. **改完要實際再看一次那幾行**，不要憑印象認定已修正 —— 這是這類違規最常見的復發原因。
2. 本 hook 只查「字面上就能判定」的項目。**沒被點名不等於這個檔的註解就合規** ——
   「複述程式碼」「該寫 /// 卻沒寫」「寫的是做什麼而非為什麼」這些要靠你自己對照規範。
"@)
exit 2
