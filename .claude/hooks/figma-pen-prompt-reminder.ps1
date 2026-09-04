<#
.SYNOPSIS
  UserPromptSubmit hook：使用者提到 Figma 卻沒給 .pen 路徑時，注入一句前提提醒。

.DESCRIPTION
  這是「提示」不是「阻擋」—— hook 是 shell script，做不了語意判斷，真正的需求解析
  仍由 design-lead skill 負責。本 hook 只補一件機械上可判定的事：設計稿產線的硬前提
  （.pen 須由使用者先在 Pencil Desktop 手動建立並開啟）很容易在對話裡被略過，
  在這裡先講一次，可省掉一輪來回。

  exit 0 且 stdout 有內容 → 內容會被當成額外 context 加進本回合。
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

$prompt = ''
if ($payload.prompt) { $prompt = [string]$payload.prompt }
if ([string]::IsNullOrWhiteSpace($prompt)) { exit 0 }

$mentionsFigma = $prompt -match '(?i)figma'
$mentionsPen   = $prompt -match '(?i)\.pen\b'

if ($mentionsFigma -and -not $mentionsPen) {
    Write-Output @'
[hook 提醒｜設計稿產線] 使用者提到 Figma 但未指定 .pen 檔路徑。若這是設計稿繪製需求，開工前請先確認：
1. 目標 .pen 的絕對路徑，且已由使用者在 Pencil Desktop 手動建立並開啟（worker 不自建／不自開／不自存）。
2. 要讀的 Figma node-id 範圍（記得轉冒號格式）與 figma-bridge 的 fileKey。
3. 產出型態（流程骨架／畫面 UI／要不要標設計疑問）。
派工方式見 design-lead skill；若只是單純詢問或與設計稿產線無關，忽略本提醒即可。
'@
}

exit 0
