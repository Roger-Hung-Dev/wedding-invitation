---
name: blender-studio
description: 3D 角色工作室的入口（/blender-studio）：向使用者一次問齊「建角色＋做情境」的聯集參數（專案名稱、VRoid .vroid 檔、真人大頭照與全身正背面照、描述、服裝要求、要做的階段、情境描述與產出），呼叫 blender-character-studio workflow（blender-creator → blender-scenario-creator → 發布 Claude Artifact），再彙整結果與待辦。使用者說「用我的 VRoid 檔做一個 3D 角色並演情境」「跑一整套角色工作室」時使用。只改服裝、只加動作、只做情境時不要走這裡，直接呼叫對應子代理。
---

# 3D 角色工作室（入口）

你是主控端。workflow 裡的子代理不能問使用者，所以**所有要問的都在這裡問完**，再一次派工。

## 1. 先看使用者已經給了什麼

從使用者的訊息裡找出下表各項，已給的不要再問。路徑一律轉成 Windows 絕對路徑。

| 參數 | 屬於 | 必要 | 怎麼問 |
| --- | --- | --- | --- |
| `project` 專案名稱 | 共用（情境直接沿用） | ✅ | 小寫英數與 -。可用角色名轉（新娘 → bride）。已存在的專案名 → 問要「繼續（resume）」還是換名字 |
| `vroid` 臉部模型 | blender-creator | ✅（resume 免） | 只收 `.vroid`。先 Glob 常見位置（`D:\SideProject\VRoid-MCP-lab\saves\*.vroid`、`.claude\docs\design\**\*.vroid`）把找到的當選項 |
| `vrm` 已匯出的 VRM | blender-creator | 選填 | 不主動問；但要提醒：VRoid MCP 不能匯出，**請先在 VRoid Studio 開 .vroid → F8 → VRM 1.0，存在 .vroid 旁邊同檔名**，否則 workflow 第一步就會停下 |
| `facePhoto`、`frontPhoto`、`backPhoto` | blender-creator | 建議 | Glob `.claude\docs\design\animation-photo\*.jpg` 等當選項；沒有正背面照服裝只能照描述做 |
| `description` 角色與服裝描述 | blender-creator | ✅ | 原話；性別若看不出來順便問（影響補皮膚的胸部） |
| `costumeNotes` 服裝額外要求 | blender-creator | 選填 | 「照片之外有沒有要改的？」 |
| `stages` 要做的階段 | blender-creator | 預設全部 | 01 身體／02 動作測試（最久，約 1 小時）／03 服裝 |
| `scenarios` 情境 | blender-scenario-creator | 選填 | 每段：描述（原話）、產出 video/picture/both、便服或服裝、長度。可以 0 段 |
| `publish` 發布網頁 | workflow | 預設是 | 已有網頁要更新就帶 `artifactUrl` |

## 2. 一次問完

- 用 **AskUserQuestion**，一次最多 4 題；可列舉的（.vroid 候選、照片候選、階段、產出型態、服裝）給選項，使用者也能選 Other 自己打。
- 自由文字（描述、情境內容）如果使用者訊息裡沒有，就在同一輪用一般訊息請他補，不要拆成很多輪。
- 問完把整理好的參數表貼給使用者看一眼（不用再等確認，除非有矛盾）。

## 3. 派工

```
Workflow({ name: 'blender-character-studio', args: {
  project, vroid, vrm, facePhoto, frontPhoto, backPhoto, description, costumeNotes, bust,
  stages: ['01','02','03'], resume: false,
  scenarios: [{ id, title, description, output, outfit, seconds }],
  publish: true, artifactUrl
}})
```

開跑前提醒使用者：**Blender 要開著**（MCP for Blender 外掛啟動）、全套大約 1.5～3 小時（動作渲染最久），期間不要關 Blender。

## 4. 回來之後

- `needsUser` 有東西（最常見：還沒匯出 VRM、Blender 沒開）→ 原樣轉告使用者，說明做完之後用 `resume: true` 再跑一次就會接著做。
- 成功 → 回報：網頁連結（提醒只有本人看得到）、01／02（通過幾個）／03 各一句、每段情境一句、已知問題、檔案在 `.claude/docs/data/blender/projects/<project>/`。
- 動作沒全過、情境有已知問題 → 照實講，不要說「都完成了」。

## 5. 不走 workflow 的情況

| 使用者要的 | 直接呼叫 |
| --- | --- |
| 改某個角色的服裝（描述或新照片） | `blender-creator`（mode revise-costume） |
| 幫既有角色做新情境 | `blender-scenario-creator` |
| 動作庫加新動作 | `blender-animation-append` |
| 只想看成品網頁 | 照 `blender-report-page` 重產並發布 |
