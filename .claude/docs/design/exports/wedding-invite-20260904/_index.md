# 設計稿匯出索引｜wedding-invite-20260904

這個資料夾放的是設計檔（`.pen`）匯出的 png 圖，供下游代理直接看視覺。
`.pen` 是加密檔，`Read`／`Grep` 打不開；要看設計稿長什麼樣，就用 `Read` 開下表的**圖檔絕對路徑**。

精確的尺寸、間距、字級、色碼請看同目錄的 [`_layout-spec.md`](./_layout-spec.md)，不必目測圖片比例。

> ⚠️ **警告：圖是設計稿原貌，可能包含已被後續決議推翻的畫法。**
> **欄位、規則、行為一律以 `.md` 分析檔為準，圖只用來看視覺。**
> 圖與分析檔衝突時，**分析檔贏**。

## 圖檔清單

| 畫面代號 | frame 標題 | 類型 | 圖檔絕對路徑 | 來源 pen 檔 |
| --- | --- | --- | --- | --- |
| （未編碼） | 裝置版-單頁全覽 | screen | `D:\SideProject\wedding-invitation\.claude\docs\design\exports\wedding-invite-20260904\lxtQz.png` | web-design |
| （未編碼） | 電腦版-單頁全覽 | screen | `D:\SideProject\wedding-invitation\.claude\docs\design\exports\wedding-invite-20260904\ZQuAX.png` | web-design |
| （未編碼） | 裝置版-S2 燈箱 | screen | `D:\SideProject\wedding-invitation\.claude\docs\design\exports\wedding-invite-20260904\a8sUM.png` | web-design |
| （未編碼） | 裝置版-S6 音樂鈕狀態對照 | shared | `D:\SideProject\wedding-invitation\.claude\docs\design\exports\wedding-invite-20260904\kouQN.png` | web-design |
| （未編碼） | 共用-S7 OG分享圖 | shared | `D:\SideProject\wedding-invitation\.claude\docs\design\exports\wedding-invite-20260904\oB0o5.png` | web-design |
| （未編碼） | 裝置版-S7 LINE卡片模擬 | other | `D:\SideProject\wedding-invitation\.claude\docs\design\exports\wedding-invite-20260904\J0wxV.png` | web-design |

本批次的 frame 都沒有畫面代號，故依 `.pen` 內的排列順序列出（screen → shared → other）。

## ⚠️ 需注意的圖

六張圖全部逐張開圖抽驗過，**沒有空白、破圖或 stale**。下面列的是「內容本身有前提，照著做會出錯」的項目。

| 圖檔 | 需注意什麼 |
| --- | --- |
| `a8sUM.png`（S2 燈箱） | **frame 尺寸 290×560 是示意稿，不是實際裝置寬（單頁為 390）。** 比例可沿用，絕對數值要按 390 等比換算；實作時遮罩應為全視窗滿版。 |
| `kouQN.png`（S6 音樂鈕狀態對照） | 不是一張畫面，是**元件三種狀態並排對照**（按下播放／播放中／已靜音），故歸 `shared`、無版面數值。播放中為 accent-gold 描邊圓框，已靜音為淡化的喇叭斜線 icon。 |
| `J0wxV.png`（S7 LINE 卡片模擬） | **不是本站畫面**，是 LINE 分享時的外部預覽卡片示意（縮圖＋標題＋描述＋網域 `ethan-chloe.wedding`）。用途是設定 OG meta 的 title／description，不要當成要切的頁面。 |
| `oB0o5.png`（S7 OG 分享圖） | 1200×630 的 OG 圖素材規格，直接當 `og:image` 用，不是站內區塊。 |
| `ZQuAX.png`（電腦版單頁） | 2x 匯出為 2880×8100，**逼近工具 8192 的上限**。日後桌機頁再加長就得降 scale 或拆段匯出。 |

## 未匯出

無。本批次只有 `web-design` 一份 `.pen`，全部 6 個頂層 frame 都已匯出。

## 略過的 frame

無略過項目。

---

本次為**唯讀匯出**，未對 `.pen` 做任何修改，因此不需要 Save。
