<#
.SYNOPSIS
  PreToolUse hook（掛在 storyboard-video-renderer 子代理的 frontmatter）：讓該子代理對 .pen 只能讀、不能寫。

.DESCRIPTION
  storyboard-video-renderer 只需要用 extract_raw.js 唯讀抽取分鏡標註。pencil 的 execute 一支工具
  同時承載讀與寫，工具層級無法只給「讀」，所以在這裡檢查程式碼內容：
    - tool_input.input（新送出的程式碼）
    - tool_input.edits[].replace（修補失敗程式碼時帶入的新片段）
  任何一處出現寫入函式（Insert／Update／Copy／Replace／Move／Delete／SetVariables／Generate）就 exit 2 阻擋。

  ⚠️ 判斷保守：取不到任何程式碼時放行（例如只帶 editId 的錯誤呼叫），因為那種呼叫本身不會執行新程式。
#>

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

try {
    $reader = New-Object System.IO.StreamReader([Console]::OpenStandardInput(), (New-Object System.Text.UTF8Encoding($false)))
    $raw = $reader.ReadToEnd()
    if ([string]::IsNullOrWhiteSpace($raw)) { exit 0 }
    $payload = $raw.TrimStart([char]0xFEFF) | ConvertFrom-Json
}
catch { exit 0 }

$parts = @()
if ($payload.tool_input) {
    if ($payload.tool_input.input) { $parts += [string]$payload.tool_input.input }
    if ($payload.tool_input.code) { $parts += [string]$payload.tool_input.code }
    if ($payload.tool_input.edits) { foreach ($e in $payload.tool_input.edits) { if ($e.replace) { $parts += [string]$e.replace } } }
}
$code = $parts -join "`n"
if ([string]::IsNullOrWhiteSpace($code)) { exit 0 }

if ($code -match '(?m)\b(Insert|Update|Copy|Replace|Move|Delete|SetVariables|Generate)\s*\(') {
    [Console]::Error.WriteLine(@"
[hook: pen-readonly-guard] 已阻擋：storyboard-video-renderer 對分鏡稿只能唯讀。

偵測到寫入函式：$($Matches[1])(...)
你的工作是讀稿產影片，不是改稿。分鏡稿有缺漏或寫法錯誤時，請以 blocked 回報錯誤清單，
由使用者或 storyboard-artist 修改分鏡稿後再重跑。
"@)
    exit 2
}
exit 0
