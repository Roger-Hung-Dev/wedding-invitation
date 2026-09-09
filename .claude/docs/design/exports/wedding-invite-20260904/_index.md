# 設計稿匯出索引：wedding-invite-20260904

這個目錄放的是設計檔 `web-design.pen` 匯出的 png 圖，一張圖 = 設計稿上的一個 frame。
`.pen` 是加密檔，`Read`／`Grep` 都打不開，所以下游代理要看設計稿長相時，**就是讀這些 png**。

**怎麼用**：在下表找到你要的畫面代號，用 `Read` 開它的「圖檔絕對路徑」即可（`Read` 支援圖片）。
精確的尺寸、間距、字級、色票請搭配同目錄的 `_layout-spec.md`，不要用目測比例。

> ⚠️ **警告：圖是設計稿原貌，可能包含已被後續決議推翻的畫法。**
> **欄位、規則、行為一律以 `.md` 分析檔為準，圖只用來看視覺。**
> 圖與分析檔衝突時，**分析檔贏**。

## 段落順序注意

「裝置版-單頁全覽」的實際段落順序是
**S1 Hero → S9 About → S10 Story → S2 Gallery → S3 Info → S4 RSVP → S5 Footer**。
也就是 **S 編號不等於畫面順序**（S9／S10 是後補的段落，實際排在 S2 之前）。
排版時請以這個實際順序為準，不要照編號排。電腦版的段落順序同理（段1 → 段1.5 → 段1.6 → 段2 → 段3 → 段4 → 段5）。

## 圖檔清單

| 畫面代號 | frame 標題 | 類型 | 圖檔絕對路徑 | 來源 pen 檔 |
| --- | --- | --- | --- | --- |
| D1 | 電腦版-段1 Hero | screen | `D:\SideProject\wedding-invitation\.claude\docs\design\exports\wedding-invite-20260904\HlNtS.png` | web-design |
| D1.5 | 電腦版-段1.5 About | screen | `D:\SideProject\wedding-invitation\.claude\docs\design\exports\wedding-invite-20260904\tgAQJ.png` | web-design |
| D1.6 | 電腦版-段1.6 Story | screen | `D:\SideProject\wedding-invitation\.claude\docs\design\exports\wedding-invite-20260904\fAw6F.png` | web-design |
| D2 | 電腦版-段2 Gallery | screen | `D:\SideProject\wedding-invitation\.claude\docs\design\exports\wedding-invite-20260904\O1WPh.png` | web-design |
| D3 | 電腦版-段3 Info | screen | `D:\SideProject\wedding-invitation\.claude\docs\design\exports\wedding-invite-20260904\jtA2m.png` | web-design |
| D4 | 電腦版-段4 RSVP | screen | `D:\SideProject\wedding-invitation\.claude\docs\design\exports\wedding-invite-20260904\l73sy.png` | web-design |
| D5 | 電腦版-段5 Footer | screen | `D:\SideProject\wedding-invitation\.claude\docs\design\exports\wedding-invite-20260904\QGIVK.png` | web-design |
| S1 | 裝置版-S1 Hero | screen | `D:\SideProject\wedding-invitation\.claude\docs\design\exports\wedding-invite-20260904\p1rjjJ.png` | web-design |
| S2 | 裝置版-S2 Gallery | screen | `D:\SideProject\wedding-invitation\.claude\docs\design\exports\wedding-invite-20260904\kJsg4.png` | web-design |
| S2 | 裝置版-S2 燈箱（相簿點圖後的狀態） | screen | `D:\SideProject\wedding-invitation\.claude\docs\design\exports\wedding-invite-20260904\a8sUM.png` | web-design |
| S3 | 裝置版-S3 Info | screen | `D:\SideProject\wedding-invitation\.claude\docs\design\exports\wedding-invite-20260904\PqZZU.png` | web-design |
| S4 | 裝置版-S4 RSVP | screen | `D:\SideProject\wedding-invitation\.claude\docs\design\exports\wedding-invite-20260904\QjV72.png` | web-design |
| S5 | 裝置版-S5 Footer | screen | `D:\SideProject\wedding-invitation\.claude\docs\design\exports\wedding-invite-20260904\PdMsp.png` | web-design |
| S6 | 裝置版-S6 音樂鈕狀態對照 | shared | `D:\SideProject\wedding-invitation\.claude\docs\design\exports\wedding-invite-20260904\kouQN.png` | web-design |
| S7 | 裝置版-S7 LINE卡片模擬 | shared | `D:\SideProject\wedding-invitation\.claude\docs\design\exports\wedding-invite-20260904\J0wxV.png` | web-design |
| S7 | 共用-S7 OG分享圖 | shared | `D:\SideProject\wedding-invitation\.claude\docs\design\exports\wedding-invite-20260904\oB0o5.png` | web-design |
| S9 | 裝置版-S9 About | screen | `D:\SideProject\wedding-invitation\.claude\docs\design\exports\wedding-invite-20260904\k9CXWE.png` | web-design |
| S10 | 裝置版-S10 Story | screen | `D:\SideProject\wedding-invitation\.claude\docs\design\exports\wedding-invite-20260904\wbUtn.png` | web-design |

（代號依英數自然順序排；`S2`／`S7` 各有兩筆是因為同一段落另有衍生狀態或素材。沒有代號的項目：無。）

## ⚠️ 需注意的圖

### 全部 18 張都是「拆分匯出」或獨立 frame，沒有一張整頁俯瞰圖

兩張頂層全覽 frame 都超過 2x 匯出的 8192px 上限，所以改成逐段匯出（詳見最後一節）。
**沒有整頁縮圖**——縮到可容納的比例後中文字會糊到不可讀，反而誤導。
要看整頁節奏請依上面的段落順序把各段依序讀過。

### 未抽驗的圖（`verified=false`，共 14 張）

匯出後只開了 4 張圖確認內容完整，其餘 14 張沒有逐張開圖，**不保證沒有空白破圖**。
使用時如果讀到明顯空白或內容不完整，回報請求重匯。

| 畫面代號 | 圖檔 | 狀況 |
| --- | --- | --- |
| D1 | `HlNtS.png` | 未抽驗；「電腦版-單頁全覽」(ZQuAX) 第 1 段，拆分匯出 |
| D1.5 | `tgAQJ.png` | 未抽驗；第 2 段，對應手機版 S9 About |
| D1.6 | `fAw6F.png` | 未抽驗；第 3 段，對應手機版 S10 Story |
| D3 | `jtA2m.png` | 未抽驗；第 5 段。手機版的單張主卡在電腦版改為左右分欄 |
| D4 | `l73sy.png` | 未抽驗；第 6 段。表單鈕為外連 Google 表單的膠囊鈕（360x60、圓角 30） |
| S2 | `kJsg4.png` | 未抽驗；「裝置版-單頁全覽」(lxtQz) 第 4 段 |
| S2 燈箱 | `a8sUM.png` | 未抽驗；頂層獨立 frame，不在單頁全覽內，是 S2 Gallery 的衍生狀態；**只畫燈箱本體，不含全螢幕遮罩** |
| S3 | `PqZZU.png` | 未抽驗；第 5 段 |
| S4 | `QjV72.png` | 未抽驗；第 6 段。出席回覆走外部 Google 表單連結，卡內為外連按鈕 |
| S5 | `PdMsp.png` | 未抽驗；第 7 段（深酒紅底、反白文字） |
| S7 LINE | `J0wxV.png` | 未抽驗；**這是喜帖連結在 LINE 裡的分享預覽外觀模擬**（343x330：縮圖 343x172 ＋ 文字區 343x101、內距 12、gap 4），屬 OG meta 標籤的呈現效果示意，**不是本站要切的畫面** |
| S7 OG | `oB0o5.png` | 未抽驗；1200x630 社群分享縮圖素材（底圖＋遮罩漸層＋600x240 內容欄，內容欄絕對定位 y=190），供 `og:image` 使用，**不是頁面畫面** |
| S9 | `k9CXWE.png` | 未抽驗；第 2 段（實際排序在 S2 Gallery 之前） |
| S10 | `wbUtn.png` | 未抽驗；第 3 段 |

### 已抽驗確認內容完整的 4 張

| 畫面代號 | 圖檔 | 確認到的內容 |
| --- | --- | --- |
| S1 | `p1rjjJ.png` | 滿版婚紗照＋漸層遮罩、英文花體主名、中文姓名、倒數四格玻璃卡、SCROLL 提示、右下音樂鈕 |
| S6 | `kouQN.png` | 三種音樂鈕狀態並列（按下播放＝白底細金框、播放中＝粗金框、已靜音＝淡粉底靜音喇叭 icon），每個鈕下方有中文狀態標籤。**這是元件狀態對照表、不是系統畫面** |
| D2 | `O1WPh.png` | GALLERY 眉標＋桃紅花體主標 Our Moments＋金線＋中文金句，下方為滿版自動橫向捲動的相片跑馬帶（卡片圓角、右側刻意切邊表示可續捲），底部「點擊放大檢視」提示 |
| D5 | `QGIVK.png` | 深酒紅底、白色花體 Thank You、中文謝詞、金色圓框 monogram「E & C」、婚期 2026 . 11 . 14、底部版權列 |

## 未匯出

無。本批次唯一的來源檔 `web-design` 匯出狀態為 `done`。

## 已略過的 frame

兩張頂層全覽 frame 因超過匯出尺寸上限而略過，改以逐段匯出取代，**內容無遺漏**：

- **裝置版-單頁全覽**（390x4996，2x 後 9992px > 8192 上限）→ 拆成 7 段：`p1rjjJ`／`k9CXWE`／`wbUtn`／`kJsg4`／`PqZZU`／`QjV72`／`PdMsp`
- **電腦版-單頁全覽**（1440x5756，2x 後 11512px > 8192 上限）→ 拆成 7 段：`HlNtS`／`tgAQJ`／`fAw6F`／`O1WPh`／`jtA2m`／`l73sy`／`QGIVK`

---

**匯出說明**：本輪全程唯讀，未對設計稿做任何寫入（沒有 Insert／Update／Copy／Delete／SetVariables，也沒有存檔）。
頂層節點名稱已核對為喜帖相關內容，確認沒有讀錯 `.pen` 檔。
