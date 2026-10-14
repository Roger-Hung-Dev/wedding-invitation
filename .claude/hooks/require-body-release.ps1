<#
.SYNOPSIS
  PreToolUse hook：身體出廠閘門 —— ZEPETO 身體還沒出廠（released）時，擋下所有會用到身體的服裝與動畫工作。

.DESCRIPTION
  使用者 2026-10-12 要求：身體沒完工，服裝和動畫都不能執行。避免在半成品身體上做動畫或服裝，身體一改又全部重來。

  觸發（只擋「會跑 Blender」的動作，只讀檔不擋）：
    - Bash／PowerShell：指令同時含 Blender 執行檔（blender.exe、blender -b、慣用變數 $BL），以及 zepeto-anim 或 zepeto-costume 路徑
      （或 -P 跑的腳本是 suit_build／cuff_probe／outfit_build／b12_*：先 cd 進資料夾再用相對路徑跑的情況；
        outfit_build 是 2026-10-12 服裝改版後的產生器，在 skill zepeto-clothing-generation-workflow 的 scripts/）
    - mcp__blender__execute_blender_code：程式碼含 zepeto-anim 或 zepeto-costume
      （只碰 zepeto-body／body.blend 的放行：身體端自己做身體不擋，使用者 2026-10-12 決定）

  只擋用到的那副身體（使用者 2026-10-12 同意，身體端提案、總監定案）：
    先從指令（或 MCP 程式碼）找出點名了哪幾副身體，三種寫法任一個符合就算：
      (a) build/<人>/body.blend 的路徑
      (b) 服裝輸出 OUT=…/zepeto-costume/<服裝>/<人>
      (c) BODY=<人>（可多個，逗號分開；MCP 程式碼裡寫在註解也算，例：# BODY=groom）
    - 有點名：只核對那幾副。每副都要在 bodies 裡、status 是 released（那副沒寫 status 的舊格式，改看總 status）、sha256 對得上。
    - 沒點名：照舊，看總 status＋全部身體的 sha256。
    ⚠️ 已知漏洞：腳本內部偷開了指令沒點名的身體，這裡看不到。約定：腳本會開哪幾副身體，指令裡就要全部點名（BODY=…）。

  檢查 D:/render-work/zepeto-body/build/RELEASE.json（環境變數 BODY_RELEASE_JSON 可覆寫，測試用）：
    - 檔案不存在、讀不懂 → 擋
    - 沒點名時：總 status 不是 "released" → 擋；bodies 裡任一個 body.blend 目前的 sha256 對不上（或檔案不見）→ 擋
    - 有點名時：點名的身體不在 bodies 裡、它的 status 不是 released、或 sha256 對不上（或檔案不見）→ 擋
  bodies 接受兩種寫法：[{ "name": "...", "path": "...", "sha256": "..." }, ...] 或 { "<名稱>": { "path": ..., "sha256": ..., "status": ... } }。

  身體端的寫法契約：開工時把那副身體的 status 寫 in_progress；出廠檢查全過才寫 released＋sha256＋checks＋handoff。
  總 status 由身體端 body_status.py 維護（全部 released 且 sha 對得上才寫 released）。
  命中則 exit 2 阻擋，stderr 回給模型。
#>

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

try {
    # 明確以 UTF-8 解碼 stdin（本機主控台是 CP950，中文路徑會毀損 JSON）
    $reader = New-Object System.IO.StreamReader([Console]::OpenStandardInput(), (New-Object System.Text.UTF8Encoding($false)))
    $raw = $reader.ReadToEnd()
    if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }
    $raw = $raw.TrimStart([char]0xFEFF)
    $payload = $raw | ConvertFrom-Json
}
catch { exit 0 }  # 輸入解析不了就不擋，避免 hook 自己變成故障點

$tool = [string]$payload.tool_name
$hit = $false
$what = ''

if ($tool -eq 'Bash' -or $tool -eq 'PowerShell') {
    $cmd = [string]$payload.tool_input.command
    if (-not [string]::IsNullOrWhiteSpace($cmd)) {
        $runsBlender = $cmd -match '(?i)blender[^\s"''/\\]*\.exe|(?i)(^|[\s;&|"''/\\])blender(\s+-b\b|\s+--background\b)|\$\{?BL\}?\b'
        # 路徑字樣；或先 cd 進資料夾、用相對路徑跑服裝／動畫腳本（服裝 session 2026-10-12 指出的漏洞）
        $touches = ($cmd -match '(?i)zepeto-anim|zepeto-costume') -or ($cmd -match '(?i)(-P|--python)\s+["'']?[^\s"'']*(suit_build|cuff_probe|outfit_build|b12_)[^\s"'']*\.py')
        if ($runsBlender -and $touches) { $hit = $true; $what = '用 Blender 跑動畫／服裝（zepeto-anim／zepeto-costume）' }
    }
}
elseif ($tool -eq 'mcp__blender__execute_blender_code') {
    $code = [string]$payload.tool_input.code
    # 只碰身體（zepeto-body／body.blend）、不含動畫或服裝路徑的放行：那是身體端自己在做身體（使用者 2026-10-12 決定豁免）
    if ($code -match '(?i)zepeto-anim|zepeto-costume') { $hit = $true; $what = '在 Blender（MCP）裡做動畫／服裝' }
}
if (-not $hit) { exit 0 }

# 這個指令點名了哪幾副身體
$text = if ($tool -eq 'mcp__blender__execute_blender_code') { $code } else { $cmd }
$named = New-Object System.Collections.Generic.List[string]
foreach ($m in [regex]::Matches($text, '(?i)build[\\/]+([a-z0-9_]+)[\\/]+body\.blend')) { $named.Add($m.Groups[1].Value.ToLowerInvariant()) }
foreach ($m in [regex]::Matches($text, '(?i)zepeto-costume[\\/]+[^\\/\s"'']+[\\/]+([a-z0-9_]+)')) { $named.Add($m.Groups[1].Value.ToLowerInvariant()) }
foreach ($m in [regex]::Matches($text, '(?i)\bBODY=([a-z0-9_,]+)')) { foreach ($n in $m.Groups[1].Value.Split(',')) { if ($n) { $named.Add($n.ToLowerInvariant()) } } }
$named = @($named | Select-Object -Unique)

$relPath = if ($env:BODY_RELEASE_JSON) { $env:BODY_RELEASE_JSON } else { 'D:/render-work/zepeto-body/build/RELEASE.json' }

function Block([string]$why) {
    [Console]::Error.WriteLine(@"
[hook: require-body-release] 已阻擋：$what

原因：$why

身體還沒出廠時，服裝和動畫都不能執行（使用者 2026-10-12 要求）。
出廠紀錄：$relPath
  - 身體端開工時寫 {"status":"in_progress"}，6 項出廠檢查全過才寫 "released"＋每個 body.blend 的 sha256。
  - released 之後身體檔又被改過，sha256 就對不上，也會擋：請身體端重新出廠。

請不要繞過這道閘門。停下來回報使用者（或請主控端轉告身體端），等身體出廠後再繼續。
"@)
    exit 2
}

if (-not (Test-Path -LiteralPath $relPath)) { Block "找不到出廠紀錄 RELEASE.json（身體還沒開始出廠流程）。" }
try {
    $relRaw = [System.IO.File]::ReadAllText($relPath, [System.Text.Encoding]::UTF8).TrimStart([char]0xFEFF)
    $rel = $relRaw | ConvertFrom-Json
}
catch { Block "RELEASE.json 讀不懂（不是合法的 JSON）。" }

$status = [string]$rel.status
if ($named.Count -eq 0 -and $status -ne 'released') {
    $shown = if ([string]::IsNullOrWhiteSpace($status)) { '（沒有寫）' } else { $status }
    Block "身體總狀態是「$shown」，不是 released（有身體還在改）。指令沒有點名用哪副身體，所以照總狀態判斷；只用某副身體的話，請在指令加 BODY=<人>。"
}

# 整理 bodies：陣列或物件都接受
$list = @()
if ($null -eq $rel.bodies) { Block "RELEASE.json 沒有 bodies（無法核對身體檔有沒有被改過）。" }
if ($rel.bodies -is [System.Array]) {
    foreach ($b in $rel.bodies) { $list += [pscustomobject]@{ Name = [string]$b.name; Path = [string]$b.path; Sha = [string]$b.sha256; Status = [string]$b.status } }
}
else {
    foreach ($p in $rel.bodies.PSObject.Properties) {
        $v = $p.Value
        if ($v -is [string]) { $list += [pscustomobject]@{ Name = $p.Name; Path = $p.Name; Sha = $v; Status = '' } }
        else { $list += [pscustomobject]@{ Name = $p.Name; Path = [string]$v.path; Sha = [string]$v.sha256; Status = [string]$v.status } }
    }
}
if ($list.Count -eq 0) { Block "RELEASE.json 的 bodies 是空的。" }
if ($named.Count -gt 0) {
    # 有點名：只核對那幾副；點名的身體不在 bodies 裡就擋
    $sel = @()
    foreach ($n in $named) {
        $b = $list | Where-Object { $_.Name -and $_.Name.ToLowerInvariant() -eq $n } | Select-Object -First 1
        if ($null -eq $b) { Block "指令點名的身體「$n」不在出廠紀錄的 bodies 裡（還沒出廠過，或名字打錯）。" }
        # 這副身體沒寫自己的 status（舊格式）→ 用總 status 判斷（身體端 2026-10-12 驗證抓到：以前直接當 released，總狀態製作中也會放行）
        $st = if (-not [string]::IsNullOrWhiteSpace($b.Status)) { $b.Status } elseif (-not [string]::IsNullOrWhiteSpace($status)) { $status } else { '（沒有寫）' }
        if ($st -ne 'released') { Block "身體「$n」的狀態是「$st」，不是 released（這副身體還在改）。" }
        $sel += $b
    }
    $list = $sel
}

foreach ($b in $list) {
    $label = if ($b.Name) { $b.Name } else { $b.Path }
    if ([string]::IsNullOrWhiteSpace($b.Path) -or [string]::IsNullOrWhiteSpace($b.Sha)) { Block "bodies 裡「$label」缺 path 或 sha256。" }
    if (-not (Test-Path -LiteralPath $b.Path)) { Block "出廠紀錄裡的身體檔不見了：$($b.Path)" }
    $now = (Get-FileHash -LiteralPath $b.Path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($now -ne $b.Sha.ToLowerInvariant()) {
        Block "身體檔「$label」出廠後被改過：sha256 現在是 $($now.Substring(0,12))…，出廠紀錄是 $($b.Sha.Substring(0, [Math]::Min(12, $b.Sha.Length)))…"
    }
}
exit 0
