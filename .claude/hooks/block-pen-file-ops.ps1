<#
.SYNOPSIS
  PreToolUse hook：擋下任何以 shell 對 .pen 檔做建立／開啟／寫入的動作。

.DESCRIPTION
  病灶：曾用 New-Item 建 0-byte 空 .pen 再 Start-Process 開啟，Pencil Desktop 會把它當成
  可拋棄的暫時「New File」，換文件時連帶把其他已開啟的 pen 檔丟進回收桶（實測造成整份成品遺失）。
  因此 .pen 的建檔／開檔／存檔一律由使用者在 Pencil Desktop 手動負責，agent 只能透過
  mcp__pencil-server__* 繪製。本 hook 把這條原本只寫在提示裡的鐵律，升級成能力邊界。

  掛在 Bash 與 PowerShell 兩個工具上（PreToolUse）。命中則 exit 2 阻擋，stderr 會回給模型。
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
    # 註：不要用 $input 當變數名 —— 那是 PowerShell 的自動變數（管線輸入列舉器）。
    $payload = $raw | ConvertFrom-Json
}
catch { exit 0 }  # 解析不了就不擋，避免 hook 自己變成故障點

$cmd = ''
if ($payload.tool_input -and $payload.tool_input.command) { $cmd = [string]$payload.tool_input.command }
if ([string]::IsNullOrWhiteSpace($cmd)) { exit 0 }

# 不含 .pen 就與本規則無關
if ($cmd -notmatch '(?i)\.pen\b') { exit 0 }

# 建檔／開檔／覆寫類動作（大小寫不敏感）
$patterns = @(
    @{ Rx = '(?i)\bNew-Item\b';                    What = '自建 .pen（New-Item）' }
    @{ Rx = '(?i)\bStart-Process\b';               What = '自開 .pen（Start-Process）' }
    @{ Rx = '(?i)\bInvoke-Item\b|(?i)\bii\b';      What = '自開 .pen（Invoke-Item）' }
    @{ Rx = '(?i)(^|[\s;&|])(start|open|code)\s';  What = '自開 .pen（start／open／code）' }
    @{ Rx = '(?i)\bSet-Content\b|\bOut-File\b|\bAdd-Content\b'; What = '以文字寫入 .pen（.pen 是加密檔，寫入會毀檔）' }
    @{ Rx = '(?i)\bRemove-Item\b|(^|[\s;&|])rm\s'; What = '刪除 .pen' }
)

foreach ($p in $patterns) {
    if ($cmd -match $p.Rx) {
        [Console]::Error.WriteLine(@"
[hook: block-pen-file-ops] 已阻擋：$($p.What)

.pen 的建立、開啟、存檔一律由使用者在 Pencil Desktop 手動負責，agent 不得以 shell 代勞。
理由：以 shell 建立的 0-byte .pen 會被 Pencil 當成可拋棄的暫時「New File」，
      換文件時會連帶把其他已開啟的 pen 檔丟進回收桶（實測造成整份成品遺失）。

正確作法：
  - 要繪製 → 用 mcp__pencil-server__* 並帶上 filePath（檔案須已由使用者開啟）。
  - 檔案還沒建立／未開啟 → 以 status="blocked" 回報，請使用者在 Pencil Desktop
    手動 File → New → Save As 建立並開啟後再重跑。

不要繞路（不要改用其他指令達成同一件事），照回報格式說明卡在哪。
被擋的指令：$cmd
"@)
        exit 2
    }
}

exit 0
