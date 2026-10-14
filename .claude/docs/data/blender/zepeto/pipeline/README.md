# ZEPETO 角色產線：分工表與狀態紀錄

交接不靠「傳訊息給某個 session」，靠這個資料夾：

- **分工表**（本檔第 1 節）：誰負責什麼。換人、改 session 名稱只改這張表，不改工作流。由總協調（zepeto-director）維護。
- **狀態紀錄**（`status/`）：每樣產物現在是哪一版、照上游哪一版做的。各負責的 session 出新版時只改**自己那幾個檔**。
- **檢查工具** `status_check.py`：開工前比對上游，列出「照的是舊版、要重跑」的產物。

原則：

- **以紀錄為主（pull）**：不管下游 session 有沒有開著、叫什麼名字，下次開工跑 `status_check.py` 一定會發現上游變了。
- **訊息只當加分（push）**：出新版後，照分工表找目前開著的負責 session 傳訊息；找不到就跳過，在回報裡寫「已留紀錄，未通知到 ○○」。

## 1. 分工表

| 角色 key | 負責項目 | 目前 session | 入口 | 產出（狀態紀錄的 kind） | 上游 |
| --- | --- | --- | --- | --- | --- |
| `head` | 大頭：照片 → 可動臉 | character | `/zepeto-character-face-generation-workflow` | `head/<人>` | 無 |
| `body` | 身體：比例、骨架、手、權重、出廠 | zepeto-body | `/zepeto-body-generation-workflow` | `body/<人>` | `head/<人>` |
| `outfit` | 穿戴物品：每套衣服 × 每個身體 | zepeto-clothing-models | `/zepeto-clothing-generation-workflow` | `outfit/<服裝>@<人>` | `body/<人>` |
| `anim` | 動畫：每段動作 | zepeto-animation | `/zepeto-animation-generation-workflow`（交接格式見該 skill 的 `references/handoff.md`） | `anim/<段落>` | `body/<人>`、`outfit/<服裝>@<人>`、`film/<片名>`、用到的道具 |
| `props` | 場景與道具素材庫 | zepeto-scense | `/zepeto-scenes-generation-workflow` | 不寫紀錄（見第 5 節） | 無 |
| `director` | 總協調：分鏡、裁決轉達、剪接（2026-10-12 使用者決定；剪接程式與樣式庫由 zepeto-animation 維護）、維護本表 | zepeto-director | `/zepeto-film-director-workflow`（劇本子代理 `film-director`、分鏡展開 workflow `zepeto-shot-breakdown`、工具 `director.py`） | `film/<片名>`（片子規格 film.json，動畫的上游）、`edit/<片名>`（字卡與轉場 edit.json，只有剪接讀） | `edit` 的上游是 `film/<片名>` |

先後順序：大頭 → 身體 → 身體出廠 → 服裝和動畫並行 → 正式渲染。動畫的正式版要等服裝定案。

## 2. 狀態紀錄放哪

```
status/
  head/groom.json
  body/groom.json
  outfit/groom_beige_3piece@groom.json
  anim/b1_b2.json
  film/<片名>.json
  edit/<片名>.json
```

- `film` 和 `edit` 分開，是為了「只改字卡、轉場」時不讓每一鏡動畫被標成要重做。規格沒變時，面板不會重寫 film.json，`film` 紀錄也不升版。

- **一樣產物一個檔**。每個 session 只寫自己 kind 底下的檔，不會互相覆蓋。
- 檔名就是 `id`：只用小寫英數、底線；服裝固定寫成 `<服裝>@<人>`，`<服裝>` 用素材庫 `outfits-zepeto/` 的代號、把 `-` 換成 `_`（例 `groom-beige-3piece` → `groom_beige_3piece@groom`）。
- 存成 UTF-8（不加 BOM）、JSON 縮排 2 格。

## 3. 欄位

```json
{
  "schema": 1,
  "kind": "outfit",
  "id": "groom_beige_3piece@groom",
  "version": "v2",
  "status": "released",
  "updated_at": "2026-10-12T10:30:00+08:00",
  "owner": "outfit",
  "artifact": {
    "path": "D:/render-work/zepeto-costume/groom-beige-3piece/groom/outfit.blend",
    "sha256": "…"
  },
  "upstream": [
    { "kind": "body", "id": "groom", "version": "v8", "sha256": "052080afd1fa…" }
  ],
  "changes": "米色三件式；使用者 2026-10-12 定案",
  "page": "https://claude.ai/artifact/…"
}
```

| 欄位 | 必填 | 說明 |
| --- | --- | --- |
| `schema` | ✅ | 固定 `1`。格式改版才加 |
| `kind`、`id` | ✅ | 要和檔案位置一致（`status/<kind>/<id>.json`） |
| `version` | ✅ | 給人看的版號，例 `v8`。每出一版就加 1 |
| `status` | ✅ | `in_progress`（做到一半，下游不要用）／`released`（可以用）／`retired`（停用，下游要換） |
| `updated_at` | ✅ | ISO 8601，含時區 |
| `owner` | ✅ | 分工表的角色 key（不是 session 名稱） |
| `artifact.path`、`artifact.sha256` | ✅ | 成品檔與它的 sha256。**下游比對靠的是 sha，不是版號** |
| `upstream` | ✅ | 這版是照哪些上游做的。每筆記當時讀到的 `kind`、`id`、`version`、`sha256`。沒有上游寫 `[]` |
| `changes` | ✅ | 這版改了什麼，一兩句白話。下游要重跑時，工具會把這句秀給使用者 |
| `page` | | 審看頁網址 |
| `notes` | | 其他（例：身體記出廠檢查摘要、用的是哪顆頭） |

各角色額外要記的東西放 `notes`，例如身體可以放 `{"release_version": "body-v8-fingers-20261012", "checks": "8 項全過"}`。完整的出廠檢查數字留在身體自己的 `RELEASE.json`，這裡不重抄。

## 4. 什麼時候寫、什麼時候讀

**負責的 session（寫）**

1. 開工改某樣產物時，先把它的紀錄改成 `in_progress`（`artifact` 先不動）。
2. 做完、使用者說可以，才寫 `released`：新的 `version`、`artifact.sha256`、`upstream`（當時用的上游 sha）、`changes`。
3. 跑 `python status_check.py` 看有哪些下游因此變成「要重跑」，照分工表通知開著的 session。

**下游的 session（讀）**

開工第一步：

```bash
python "D:/SideProject/wedding-invitation/.claude/docs/data/blender/zepeto/pipeline/status_check.py" outfit/groom_beige_3piece@groom
```

- 結果是「一致」→ 照常開工。
- 結果是「上游已更新」→ 停下來告訴使用者：哪個上游、從哪版變成哪版、上游的 `changes`，問要不要重跑。
- 結果是「上游還沒出廠」（`in_progress`）→ 不開工，回報使用者。

不帶參數會列出全部產物的狀態；加 `--verify` 會再算一次每個成品檔的 sha256，抓「檔案被改了、紀錄沒更新」的情況。

## 5. 和其他機制的關係

- **身體出廠閘門 hook（`require-body-release.ps1`）照舊讀 `RELEASE.json`**，這次不改。之後身體端把出廠標記拆成每個身體各自一個狀態時，再和 hook 的維護者（zepeto-animation）一起改成讀 `status/body/*.json`。
- **道具素材庫不寫狀態紀錄**：道具很少改、尺寸會寫進 `catalog.json`。動畫用到的道具在自己的 `upstream` 記 `{"kind": "prop", "id": "phone_mute_zp", "sha256": "<.blend 的 sha>"}` 即可；工具找不到 `status/prop/` 時只顯示「不追蹤」，不擋。
- 新郎的頭是產線建好前手動做的 `stylized_face_rig/head_rig.blend`。身體紀錄已用 sha `065b90ee7f39…`、version `legacy` 指向它。大頭端補 `status/head/groom.json` 時**一定要用同一個 sha**，不然新郎身體會被誤判成「上游已更新」。補上之前，`body/groom` 會一直顯示「上游 head/groom：找不到紀錄」，這是預期的。
- 大頭：使用者已定「每個人只留一個現役版本，舊版自動封存」。舊版那筆紀錄改 `retired` 或直接被新版覆蓋都可以，但新版的 `sha256` 一定要變。
