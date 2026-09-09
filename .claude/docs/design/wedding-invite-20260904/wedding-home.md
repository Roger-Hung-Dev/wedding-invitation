---
screen: 電子喜帖單頁（Hero／Gallery／Info／RSVP／Footer ＋ 音樂鈕 ＋ 分享卡）
batch: wedding-invite-20260904
figmaLink: （無 —— 本批次沒有 Figma 來源）
figmaNodeIds: []
penPath: D:\SideProject\wedding-invitation\.claude\docs\design\web-design.pen
steps: ["draw-screen"]
readCompleted: true
sourceOfTruth: .claude/docs/data/rfp.md（RFP 文字需求）＋ ui-ux-pro-max 設計系統推薦
---

> ⚠️ **本分析檔不是從 Figma 量測來的。** 本專案沒有 Figma 設計稿，第 9 節的數值是
> `design-lead` 依 RFP ＋ ui-ux-pro-max 推薦的設計系統**訂定**的初稿規格，不是既有稿的量測值。
> 下游（pen-drawer、前端）照它畫／照它做即可；要修改請直接改本檔，它就是這批的唯一真相。
> `readCompleted: true` 在此代表「分析已完成、可以動筆」，不代表「已讀過 Figma」。

## 1. 畫面結構

單頁垂直捲動（single-page scrolling），行動優先。基準寬度 **390px**（iPhone 14/15 邏輯寬）。
由上而下五個區塊，加上一個跨區塊的浮動元件與兩個非頁面產出：

| 順序 | 區塊 | 代號 | 尺寸（mobile） | 說明 |
| --- | --- | --- | --- | --- |
| 1 | 主視覺封面區 Hero | S1 | 390×844 | 滿版婚紗照 ＋ 姓名 ＋ 日期 ＋ 倒數計時 |
| 2 | 婚紗藝廊區 Gallery | S2 | 390×720 | 橫向滑動相簿 ＋ 金句 |
| 3 | 宴客資訊區 Info | S3 | 390×900 | 日期時間、場地、地址、桌次、地圖導航鈕 |
| 4 | 意願調查區 RSVP | S4 | 390×560 | 說明 ＋ 收集欄位預告 ＋ 外連表單 CTA |
| 5 | 結語 Footer | S5 | 390×420 | 致謝 ＋ monogram ＋ 版權 |
| — | 音樂控制鈕 | S6 | 470×260（狀態對照板） | 浮動於畫面右下角，三種狀態並列展示 |
| — | 社群分享預覽 | S7 | 1200×630 ＋ LINE 卡片模擬 | OG 縮圖卡 |
| — | 桌機 Hero 對照 | S8 | 1440×900 | 響應式對照，僅 Hero 一屏 |

**畫布排版**（第二輪已改為連續長頁，現行落點見 §9.5.3）：

⛔ **五個區塊不再是五張獨立畫布。** 第一輪那樣畫，並排看像五個不相干的頁面，
看不出這是一條連續捲動的網頁。現在它們是**長頁裡的五個段落**，段與段之間 gap 0。

```
裝置版-單頁全覽   x=0    y=0   390×3444   ← S1～S5 依序串接，中間無縫
電腦版-單頁全覽   x=560  y=0   1440×4012  ← 桌機五段，版式與手機不同（見 §9.5.2）
輔助那一列       y=4200            ← 燈箱／音樂鈕三態／LINE卡／OG 分享圖
```

**沒有導覽列、沒有側欄、沒有頁籤。** 全站只有一條垂直捲軸，區塊之間不做錨點選單（初稿範圍）。

### 1.1 圖層命名規則（`.pen` 頂層 frame）

前綴標的是**這張圖是給哪個裝置看的**，不是區塊分類：

| 前綴 | 意思 | 有哪些 |
| --- | --- | --- |
| `裝置版-` | 390px 手機基準 | `裝置版-S1 Hero`／`裝置版-S2 Gallery`／`裝置版-S3 Info`／`裝置版-S4 RSVP`／`裝置版-S5 Footer`／`裝置版-S2 燈箱`／`裝置版-S6 音樂鈕狀態對照`／`裝置版-S7 LINE卡片模擬` |
| `電腦版-` | 1440px 桌機基準 | `電腦版-S8 Hero` |
| `共用-` | 不屬於任何裝置，是社群平台的固定規格圖 | `共用-S7 OG分享圖`（1200×630） |

⚠️ **OG 分享圖沒有裝置版／電腦版之分** —— 它是 LINE／Facebook 抓去當縮圖的圖檔，
尺寸由平台規定，不隨螢幕變化，所以獨立用 `共用-`。
新增畫面時沿用這三個前綴，不要再開第四種。

---

## 2. 欄位（逐字）

本站**沒有任何輸入欄位** —— 頁面只展示，資料收集一律在外部 Google 表單。
下表列的是**頁面上會出現的文字內容**與其示意值，供繪製時逐字照抄。

| 區塊 | 標籤／元素 | 型態 | 在第幾列第幾格／佔寬 | 示意值（逐字） | 備註 |
| --- | --- | --- | --- | --- | --- |
| S1 | 引言小字 | 靜態文字 | 第1列・滿寬置中 | `WE ARE GETTING MARRIED` | 全大寫、字距 4 |
| S1 | 英文姓名 | 靜態文字 | 第2列・滿寬置中 | `Ethan & Chloe` | 示意名，待新人提供 → Q1 |
| S1 | 中文姓名 | 靜態文字 | 第3列・滿寬置中 | `陳彥廷　✕　林思妤` | 示意名 → Q1 |
| S1 | 分隔飾線 | 裝飾 | 第4列・寬 72 置中 | （線 ＋ 中央菱形） | — |
| S1 | 婚期 | 靜態文字 | 第5列・滿寬置中 | `2026 . 11 . 14　SATURDAY` | 示意日 → Q1 |
| S1 | 倒數計時・數字 | 動態文字 | 第6列・4 格等寬 | `128` `06` `42` `19` | 4 格：日／時／分／秒 |
| S1 | 倒數計時・標籤 | 靜態文字 | 第6列・各格下方 | `DAYS` `HOURS` `MINS` `SECS` | 10px 字距 2 |
| S1 | 捲動提示 | 靜態文字 ＋ icon | 第7列・滿寬置中 | `SCROLL` | 下方 chevron-down icon |
| S2 | 區塊眉標 | 靜態文字 | 第1列・置中 | `GALLERY` | 字距 5 金色 |
| S2 | 區塊主標 | 靜態文字 | 第2列・置中 | `Our Moments` | Great Vibes 手寫體 |
| S2 | 金句 | 靜態文字 | 第3列・寬 300 置中 | `願我們的故事，`／`從今天起有了共同的名字。` | 兩行，斜體 |
| S2 | 相片卡 | 圖片 | 第4列・主卡 260 置中 | （5 張婚紗照） | 張數待確認 → Q4 |
| S2 | 頁點指示器 | 裝飾 | 第5列・置中 | （5 點，第 1 點為 active 膠囊） | — |
| S2 | 操作提示 | 靜態文字 | 第6列・置中 | `左右滑動瀏覽・點擊放大` | 11px |
| S3 | 區塊眉標 | 靜態文字 | 第1列・置中 | `INFORMATION` | — |
| S3 | 區塊主標 | 靜態文字 | 第2列・置中 | `Wedding Day` | Great Vibes |
| S3 | 場次切換・午宴 | 膠囊按鈕（選中） | 卡內第1列第1格・各佔一半 | `午宴　12:00` | 選中態 |
| S3 | 場次切換・晚宴 | 膠囊按鈕（未選） | 卡內第1列第2格 | `晚宴　18:00` | 是否兩場都辦 → Q3 |
| S3 | 日期大字 | 靜態文字 | 卡內第2列・置中 | `2026 . 11 . 14` | — |
| S3 | 日期副標 | 靜態文字 | 卡內第3列・置中 | `星期六　·　農曆十月初五` | — |
| S3 | 資訊列・宴會地點 | 圖示 ＋ 標籤 ＋ 值 | 卡內第5列・滿寬 | 標籤 `宴會地點` ／ 值 `台北文華東方酒店` | icon `building` |
| S3 | 資訊列・宴會廳 | 同上 | 卡內第6列・滿寬 | 標籤 `宴會廳` ／ 值 `3F　文華廳` | icon `door-open` |
| S3 | 資訊列・地址 | 同上 | 卡內第7列・滿寬 | 標籤 `地址` ／ 值 `台北市松山區敦化北路二段 158 號` | icon `map-pin` |
| S3 | 資訊列・桌次引導 | 同上 | 卡內第8列・滿寬 | 標籤 `桌次引導` ／ 值 `入口處設有座位表，男方親友請至 A 區、女方親友請至 B 區` | icon `users`；值為兩行 |
| S3 | 地圖預覽 | 圖片 | 卡內第9列・滿寬 | （淺色地圖靜態圖，**無圖釘**） | 非互動地圖，僅預覽 |
| S3 | 導航按鈕 | 主按鈕 | 卡內第10列・滿寬 | `開啟 Google 地圖導航` | 左側 icon `navigation` |
| S3 | 入場提醒 | 靜態文字 | 第4列（卡外）・置中 | `※ 宴會廳將於開席前 30 分鐘開放入場` | 11px |
| S4 | 區塊眉標 | 靜態文字 | 第1列・置中 | `R.S.V.P.` | — |
| S4 | 區塊主標 | 靜態文字 | 第2列・置中 | `Will You Join Us?` | Great Vibes |
| S4 | 說明文 | 靜態文字 | 第3列・寬 310 置中 | `您的出席是我們最珍貴的祝福，`／`敬請於 2026 / 10 / 15 前回覆。` | 兩行 |
| S4 | 欄位預告 chips | 標籤群 | 卡內第1列・自動換行 | `姓名`　`出席人數`　`素食需求`　`兒童椅`　`喜餅領取`　`聯絡電話`　`祝福話語` | 7 顆，兩行排列 |
| S4 | 表單 CTA | 主按鈕 | 卡內第2列・滿寬 | `填寫出席回覆表單` | 右側 icon `external-link` |
| S4 | 開啟方式註記 | 靜態文字 | 卡內第3列・置中 | `將另開新視窗前往 Google 表單` | 11px |
| S4 | 修改連結 | 文字連結 | 第5列・置中 | `已經填寫過了？點此修改回覆` | 底線 |
| S5 | 致謝主標 | 靜態文字 | 第1列・置中 | `Thank You` | Great Vibes 42px |
| S5 | 致謝內文 | 靜態文字 | 第2列・寬 300 置中 | `謝謝每一位陪伴我們走到這裡的人，`／`期待與你分享這一天的喜悅。` | 兩行 |
| S5 | Monogram | 裝飾 ＋ 文字 | 第3列・96×96 置中 | `E　&　C` | 圓環內 |
| S5 | 婚期重述 | 靜態文字 | 第4列・置中 | `2026 . 11 . 14` | — |
| S5 | 版權 | 靜態文字 | 第5列・置中 | `© 2026 Ethan & Chloe　·　Made with love` | 10px |
| S6 | 音樂鈕・狀態標籤 | 靜態文字 | 各鈕下方（由左至右） | `按下播放`／`播放中`／`已靜音` | 說明用，非頁面元素。順序以 §4／§9.4 為準 |
| S7 | OG 眉標 | 靜態文字 | OG 圖左側第1列 | `WE ARE GETTING MARRIED` | 字距 4 |
| S7 | OG 姓名 | 靜態文字 | OG 圖左側第2列 | `Ethan & Chloe` | Great Vibes 84px |
| S7 | OG 日期 | 靜態文字 | OG 圖左側第3列 | `2026 . 11 . 14　SATURDAY` | 字距 4 |
| S7 | 分享標題 | 靜態文字 | 卡片第2列 | `We are Getting Married! 陳彥廷 & 林思妤 婚禮邀請函` | 逐字取自 RFP §3 |
| S7 | 分享內文 | 靜態文字 | 卡片第3列 | `誠摯邀請您參與我們的婚禮，點擊查看詳細資訊與回覆出席意願。` | 逐字取自 RFP §3 |
| S7 | 網域 | 靜態文字 | 卡片第4列 | `ethan-chloe.wedding` | 示意網域 |

### 2.0 示意資料

**圖片一律用 `Generate(nodeId, "stock", "<英文 prompt>")` 取 Unsplash 照片**，禁止自行編造 URL。
建議 prompt（逐字，可微調）：

| 用途 | 節點 | prompt |
| --- | --- | --- |
| S1 Hero 底圖 | S1 根 frame 的 fill | `elegant wedding couple portrait, soft warm backlight, outdoor, vertical` |
| S2 相片卡 1 | Gallery 主卡 | `bride and groom holding hands close up, film tone` |
| S2 相片卡 2 | 左側鄰卡 | `wedding dress detail, soft pink flowers` |
| S2 相片卡 3 | 右側鄰卡 | `couple walking in golden hour field, back view` |
| S3 地圖預覽 | 地圖 frame | `city map top view, minimal light style` |
| S7 OG 圖 | S7 大圖區 | `wedding couple horizontal banner, pastel tone, copy space` |
| 電腦版-S8 Hero | S8 根 frame fill | `wedding couple wide landscape shot, soft light, copy space on left` |

---

## 3. 按鈕與互動

| 位置 | 按鈕文字（逐字） | 行為 | 狀態限制 |
| --- | --- | --- | --- |
| S1 右下浮動 | （無文字，唱片 icon） | 切換背景音樂播放／靜音 | 首次需使用者手勢觸發 → Q5 |
| S1 底部 | `SCROLL` ＋ chevron | 點擊平滑捲動至 S2 | 上下浮動微動畫 |
| S2 相片卡 | （無文字） | 點擊放大（燈箱）；左右滑動切換 | 燈箱規格未定 → Q4 |
| S3 場次膠囊 | `午宴　12:00`／`晚宴　18:00` | 切換卡片內顯示的時間資訊 | 若僅一場則不顯示切換 → Q3 |
| S3 主按鈕 | `開啟 Google 地圖導航` | 另開 Google Maps（帶目的地座標） | 無 |
| S4 主按鈕 | `填寫出席回覆表單` | 另開新視窗至 Google 表單 | 外連，不內嵌 → Q2 |
| S4 文字連結 | `已經填寫過了？點此修改回覆` | 另開 Google 表單的編輯回覆連結 | 需表單開啟「編輯回覆」選項 |

**互動元件一律自寫**（Bootstrap 5 只用 CSS，不引其 JS）：輪播、燈箱、場次切換、音訊控制全部走 Angular Signals。

➡️ **動態規格（捲動觸發動畫、Hero 入場序列、視差、持續動畫、reduced-motion 降級）見 §10。**
本站定位是「沉浸式」，那份沉浸感幾乎全部來自動態 —— **只照 §9 的靜態值做，成品會是一份很整齊但很平的網頁。**

---

## 4. 彈窗與狀態

| 元件 | 狀態 | 呈現 |
| --- | --- | --- |
| 音樂鈕 | ① 尚未播放 ② 播放中 ③ 已靜音 | ① 唱片 icon 靜止 ＋ 外圈虛線 ② 唱片旋轉 ＋ 金色外環 ③ 唱片靜止 ＋ 斜線遮罩 icon |
| 相簿燈箱 | 開啟 | 全螢幕遮罩 `$overlay-dark`，中央大圖 ＋ 右上關閉 icon ＋ 底部頁碼 `3 / 5` |
| 倒數計時 | 婚期已過 | 顯示 `Thank you for being with us` 取代四格數字 → Q6 |
| 相片載入中 | 骨架 | 卡片位置顯示 `$border-soft` 底色圓角矩形 |

**初稿只畫音樂鈕三態（S6）與燈箱**。

⛔ **燈箱那張 frame 是 290×560 的「示意稿」，不是實際尺寸。**
實作時燈箱是**全視窗滿版**遮罩（手機 390 寬、桌機 1440 寬），不是一個 290 寬的小視窗。
稿上的絕對數值請按比例換算，比例關係才是規格：

| 項目 | 稿上（290 寬） | 實作（以視窗寬 W 計） |
| --- | --- | --- |
| 遮罩 | 290×560 | **滿版視窗**，fill `$overlay-dark` |
| 大圖 | 250×360，左右各留 20 | 寬 = W − 40（左右各留 20），高依原圖比例，圓角 12 |
| 關閉 icon | 20×20 右上 | 24×24，距上、右各 16（觸控目標至少 44×44） |
| 頁碼 | 底部置中 13px | 同，距底 32 |

⚠️ 這個誤讀風險是真的 —— 匯出時 worker 就特別標註了一次。**不要照 290 這個數字做。**

---

## 5. 流程走向

```
開啟連結（LINE／Messenger 分享卡 S7）
  → S1 Hero（首次點擊任一處 → 背景音樂開始播放）
  → 向下捲動 → S2 Gallery（可左右滑動、點擊放大 → 燈箱 → 關閉回 S2）
  → S3 Info（點「開啟 Google 地圖導航」→ 離站至 Google Maps）
  → S4 RSVP（點「填寫出席回覆表單」→ 離站至 Google 表單）
  → S5 Footer
```

音樂鈕在整個捲動過程中恆常固定於右下角（`position: fixed`），不隨區塊消失。

### 5.1 情境序列

（本批次不跑 `draw-scenario`，此節先留骨架供後續批次使用）

| # | 情境名稱 | 觸發動作 | 前態畫面 | 後態畫面 | 變化重點 |
| --- | --- | --- | --- | --- | --- |
| 1 | 首次進站啟動音樂 | 點擊頁面任一處 | S1・音樂鈕未播放態 | S1・音樂鈕播放中態 | 唱片開始旋轉、金環出現 |
| 2 | 放大相片 | 點擊 S2 主相片卡 | S2 | 裝置版-S2 燈箱 | 全螢幕遮罩 ＋ 大圖 ＋ 頁碼 |
| 3 | 切換宴席場次 | 點擊「晚宴 18:00」 | S3・午宴選中 | S3・晚宴選中 | 膠囊選中態互換、時間字改變 |

---

## 6. 設計稿註解原文

無 —— 本批次沒有 Figma 來源，需求全部來自 `.claude/docs/data/rfp.md`。

---

## 7. 設計疑問

### 7.0 索引表

| # | 疑問摘要（≤ 40 字） | 原文出處 | pen 節點 ID | 狀態 |
| --- | --- | --- | --- | --- |
| Q1 | 新人姓名、婚期、場地全為示意文案，正式內容待提供 | RFP §2 Hero／Info | `wRPvE`（S1-英文姓名）／`Vf6Ql`（S1-中文姓名）／`cNJbF`（S1-婚期）／`M4s8TJ`（S3-資訊列群） | 未處理 |
| Q2 | RSVP 究竟外連還是內嵌？RFP 與 CLAUDE.md 說法不一致 | RFP §2 RSVP vs CLAUDE.md 範圍界線 | `ziuHd`（S4-表單鈕） | 未處理 |
| Q3 | 午宴與晚宴是兩場都辦、還是擇一？ | RFP §2 Info「含午宴／晚宴標記」 | `JKGVq`（S3-場次列） | 未處理 |
| Q4 | 相簿張數未定，且「點擊放大」的燈箱規格未定義 | RFP §2 Gallery | `l6mvHq`（S2-頁點列）／`a8sUM`（S2-燈箱） | 未處理 |
| Q5 | 行動瀏覽器禁止自動播放，音樂啟動時機需確認 | RFP §2 Audio、§4 音樂體驗 | `Ja7lN`（S1-音樂鈕(尚未播放)）／`Ce3LT`（S6-狀態列） | 未處理 |
| Q6 | 婚期當天與之後，倒數計時器顯示什麼？ | RFP §2 Hero「婚禮倒數計時器」 | `bxotT`（S1-倒數群組） | 未處理 |
| Q7 | 是否需要中英雙語切換？ | RFP §2「新人中英文姓名」 | 無對應元素（本稿未畫語言切換鈕；最接近的是 `Vf6Ql` S1-中文姓名） | 未處理 |
| Q8 | 喜餅發放的實際流程未描述，頁面是否要有說明區 | RFP §2 RSVP「喜餅發放紀錄」 | `rCYoZ`（S4-chip-喜餅領取） | 未處理 |
| Q9 | S9 兩段描述的性格描寫是撰稿推測，非新人提供 | 本檔 §13.2 | `Zxwyz`（S9-描述-新郎）／`fNC1M`（S9-描述-新娘）／`NqJZ6`（D9-描述-新郎）／`WH1JL`（D9-描述-新娘） | 未處理（逐題內容見 §13.7） |
| ~~Q10~~ | ~~兩位的單人照尚未提供~~ | 本檔 §13.8 | — | ✅ 已解決（新人已提供，見 §13.8.1） |
| Q11 | S9 是否要顯示英文名 Roger／Amy | 本檔 §13.7 | 無對應元素（本稿未畫英文名；最接近的是 `K52AI`／`me6rS` 手機中文姓名、`DTOGp`／`Q5W16` 桌機中文姓名） | 未處理（逐題內容見 §13.7） |

> ⚠️ **Q9～Q11 的逐題內容寫在 §13.7，不在 §7.1。** 這裡登記索引是為了讓
> `design-question-curator` 取得到題目（它的取題來源是 §7）。

### 7.1 逐題小節

#### Q1 新人姓名、婚期、場地全為示意文案

**疑問**
本稿所有具體內容（`Ethan & Chloe`、`陳彥廷 ✕ 林思妤`、`2026.11.14`、`台北文華東方酒店 3F 文華廳`、地址、座位分區）都是我為了讓版面成立而編的示意值。
正式資料尚未提供。

**出處**
RFP §2 主視覺封面區、宴客資訊區。

**影響**
中文姓名字數會改變 S1 第 3 列的寬度；飯店與廳別名稱過長時 S3 資訊列會換行、卡片高度隨之改變。
所以正式文案進來時要重新確認 S3 主卡高度。

#### Q2 RSVP 究竟外連還是內嵌

**疑問**
RFP 寫「內嵌或跳轉至線上出席表單」，兩種都可以。
但專案的 `CLAUDE.md` 範圍界線明確寫「出席統計走**外部 Google 表單連結**，頁面上只放一個連到 Google 表單的按鈕或連結」。

**出處**
RFP §2 意願調查區；`CLAUDE.md`「範圍界線」。

**影響**
初稿依 `CLAUDE.md` 畫成**外連按鈕**（S4 只有一顆 CTA，沒有輸入欄位）。
若改成 iframe 內嵌，S4 高度會從 560 增加到約 1200，而且要處理 iframe 在 iOS 上的捲動巢狀問題。
這是版面等級的差異，不是樣式差異，所以要先定案。

#### Q3 午宴與晚宴是兩場都辦、還是擇一

**疑問**
RFP 只寫「含午宴／晚宴標記」，沒說是兩場都辦、還是只是要標出這一場屬於哪一種。

**出處**
RFP §2 宴客資訊區。

**影響**
初稿畫成**兩顆可切換的膠囊**（午宴選中、晚宴未選）。
若實際只有一場，那兩顆膠囊要換成一顆靜態徽章，S3 主卡少約 20px。
若兩場都辦，還要確認賓客怎麼知道自己該去哪一場 —— 可能需要在 RSVP 表單多一題。

#### Q4 相簿張數與燈箱規格

**疑問**
婚紗照要放幾張？
「點擊放大」之後是全螢幕燈箱、還是原地放大？
燈箱內能不能左右換圖、有沒有頁碼、怎麼關閉？

**出處**
RFP §2 婚紗藝廊區。

**影響**
初稿假設 **5 張**、全螢幕燈箱、有頁碼與右上關閉鈕（畫在 `S2-燈箱`）。
張數影響頁點指示器的寬度；張數超過 8 時頁點會太密，要改成 `3 / 12` 這種數字式指示器。

#### Q5 音樂的啟動時機

> ✅ **第十七輪補充：「首次手勢」不等於「首次點擊」。**
>
> 初版只監聽 `document:click`，實測回報**手機一進站就往下滑時音樂永遠不會開始** ——
> 因為**滑動不會產生 click**（click 要求按下與放開在同一位置）。
>
> 依 HTML 規範，授予「使用者啟用（user activation）」的輸入事件是
> `keydown`／`mousedown`／`pointerdown`／`pointerup`／`touchend`。
> 其中 **`touchend` 涵蓋滑動** —— 一次滑動的最後仍會送出 `touchend`。
> ⛔ **`scroll` 不在清單裡，監聽它沒有用。**
>
> 現行實作四個事件都監聽（click／touchend／pointerup／keydown），先到的生效。
>
> ⚠️ **`play()` 被拒時必須退回 `idle`**：留在 `playing` 會讓音樂鈕顯示「播放中」
> 卻沒有聲音，賓客只會以為音量壞了，不知道要再點一次。
>
> ⛔ **完全不需任何手勢的自動播放做不到** —— 這是瀏覽器規範層級的限制，
> 不是設定問題，也沒有繞道。唯一能自動播放的是**靜音**媒體，但那對背景音樂沒有意義。


**疑問**
行動版 Safari 與 Chrome 都禁止沒有使用者手勢的自動播放，所以「一進站就有音樂」在技術上做不到。
RFP §4 也要求「避免音量突然播放造成賓客困擾」。

**出處**
RFP §2 音樂控制區、§4 設計與品質規範。

**影響**
初稿採：**進站時為「尚未播放」態**（唱片靜止 ＋ 外圈虛線提示），賓客首次點擊頁面任一處才開始播放。
這代表音樂鈕需要**三種狀態**而不是兩種（RFP 只提到「開關／靜音」兩種）。
若不接受這個折衷，就只能改成「必須手動按鈕才播」，那第三態仍然存在，只是提示方式不同。

#### Q6 倒數計時歸零之後

**疑問**
婚禮當天以及之後再打開頁面，四格數字要顯示什麼？

**出處**
RFP §2 主視覺封面區。

**影響**
留 `00 00 00 00` 會顯得像壞掉。
初稿建議婚期當天起改顯示一行文字 `Thank you for being with us` 取代四格。
這需要一段判斷邏輯，也影響 S1 第 6 列的高度（四格 76px vs 單行 32px）。

#### Q7 是否需要中英雙語切換

**疑問**
RFP 只在姓名那一項提到「中英文」，沒有說整站要雙語。

**出處**
RFP §2「新人中英文姓名」。

**影響**
初稿理解為：**整站中文為主，英文只用於裝飾性的標題與眉標**（`GALLERY`、`Our Moments`），不做語言切換。
若真的要雙語切換，要加 Transloco 與一顆語言切換鈕，而右上角目前沒有留位置給它。

#### Q8 喜餅發放的流程未描述

**疑問**
RFP 把「喜餅發放紀錄」列為表單欄位，但沒說賓客要怎麼領、什麼時候領、宴客當天領還是另外寄送。

**出處**
RFP §2 意願調查區。

**影響**
初稿只在 S4 的欄位預告 chips 放了一顆 `喜餅領取`，頁面上**沒有**任何說明文字。
若賓客需要知道領取方式（例如「當天於簽到處領取」），S3 或 S4 要多一段說明，約 60px 高。

---

## 8. 已繪製節點

（由 `pen-drawer` 於 `draw-screen` 後回填；批次 `wedding-invite-20260904`，繪於 `web-design.pen`）

| 節點名稱 | pen 節點 ID | 型態 |
| --- | --- | --- |
| 裝置版-S1 Hero | `p1rjjJ` | screen |
| 裝置版-S2 Gallery | `kJsg4` | screen |
| 裝置版-S3 Info | `PqZZU` | screen |
| 裝置版-S4 RSVP | `QjV72` | screen |
| 裝置版-S5 Footer | `PdMsp` | screen |
| 裝置版-S6 音樂鈕狀態對照 | `kouQN` | screen |
| 裝置版-S2 燈箱 | `a8sUM` | screen |
| 裝置版-S7 LINE卡片模擬 | `J0wxV` | screen |
| 共用-S7 OG分享圖 | `oB0o5` | screen |
| 電腦版-段1 Hero（原 `電腦版-S8 Hero`，第二輪 Move 進長頁並改名） | `HlNtS` | screen |

**第二輪追加（桌機長頁）**：

| 節點名稱 | pen 節點 ID | 型態 |
| --- | --- | --- |
| 電腦版-單頁全覽 | `ZQuAX` | screen |
| 電腦版-段1 Hero | `HlNtS` | screen |
| 電腦版-段2 Gallery | `O1WPh` | screen |
| 電腦版-段3 Info | `jtA2m` | screen |
| 電腦版-段4 RSVP | `l73sy` | screen |
| 電腦版-段5 Footer | `QGIVK` | screen |

**第五輪追加（新人介紹區 S9 About）**：

| 節點名稱 | pen 節點 ID | 型態 |
| --- | --- | --- |
| 裝置版-S9 About | `k9CXWE` | screen |
| 電腦版-段1.5 About | `tgAQJ` | screen |

段內主要子節點（供後續標註對位）：

`k9CXWE`（手機）：眉標 `beFvC`／主標 `f9Z7WP`／金線 `JJAQK`／引言 `AojCh`／
人物卡-新郎 `E3FIFU`（照片 `yqhn4`／文字欄 `r5FDL`／角色標籤 `C8TK1W`／姓名 `K52AI`／
職業 chip `HuS42`／描述 `Zxwyz`）／中央連結列 `MjkCn`（線左 `Xlxj4`／`&` `EtGCI`／線右 `SD11B`）／
人物卡-新娘 `kiwh5`（文字欄 `SNM8M`／角色標籤 `RuZNL`／姓名 `me6rS`／職業 chip `u4Wug`／
描述 `fNC1M`／照片 `cGGmE`）／收尾句 `HD5v0`。

`tgAQJ`（桌機）：眉標 `kmnA7`／主標 `SsZxO`／金線 `af7fk`／引言 `Z4AaHl`／
兩人列 `JFctj`（新郎欄 `A1ITBb`：照片 `X4k7HR`／文字欄 `qZGQJ`／角色標籤 `cFtTy`／姓名 `DTOGp`／
職業 chip `Mi2pq`／描述 `NqJZ6`；中央分隔 `mi3QY`：線上 `XcOFN`／`&` `mcheO`／線下 `td2zK`；
新娘欄 `v5aeal`：文字欄 `h7n3c8`／角色標籤 `fQZem`／姓名 `Q5W16`／職業 chip `N4wPyL`／
描述 `WH1JL`／照片 `EldLJ`）／收尾句 `c06DK`。

⚠️ **桌機兩張照片的節點 ID 於第七輪換過**（`ZSHt0` → `X4k7HR`、`N3db55` → `EldLJ`）。
原因見 §13.8：為了讓手機／桌機用同一張佔位圖，改以 `Copy` 手機照片節點再刪除原節點，
`Copy` 會重新產生 ID。⛔ 引用舊 ID 會拿到「No node with id」。

**第五輪沒有 `hidden-in-variant`** —— 兩段皆新建，未使用 `Copy` 做變體，
`Get("k9CXWE"/"tgAQJ", n=>n.enabled===false)` 皆為 0 筆。

**第七輪追加（交往故事書 S10 Story）**：

| 節點名稱 | pen 節點 ID | 型態 |
| --- | --- | --- |
| 裝置版-S10 Story | `wbUtn` | screen |
| 電腦版-段1.6 Story | `fAw6F` | screen |

段內主要子節點（供後續標註對位）：

`wbUtn`（手機，**第十一輪改版後**）：眉標 `Z0bur`／主標 `fZuLh`／金線 `B2VPE`／
**書本（書皮）`shoHW`**（342×414，`$book-wood`，pad 12）→ 內頁 `RK3GT`（318×390，`$surface`，圓角 8）：
照片 `NxfTr`（278×208）／年份標籤 `vhusd`／段落標題 `k5xK5`／故事文字 `v9XAif`／
控制列 `u3yQw3`（翻頁鈕-上一頁(停用) `VbtbV`／頁點列 `By7TO`（active `X9XQB`）／翻頁鈕-下一頁 `Z4ql9V`）／
操作提示 `LI4rq`。

**第十二輪（立體感）新增兩個節點**：桌機內頁上緣暗線 `dkEAp`（`OSper` 下，絕對定位）、
手機內頁上緣暗線 `F3w0xR`（`RK3GT` 下，絕對定位）。

**第十三輪（書皮四邊分色）改為十個節點**（全部絕對定位）：

| 邊／線 | 桌機（`OSper` 下） | 手機 |
| --- | --- | --- |
| 書皮-上 `#BD9B79` | `qb22u` | `CJo2Q`（`shoHW` 下）|
| 書皮-左 `#B18961` | `yDZao` | `J2Lkkx` |
| 書皮-右 `#956F4A` | `XiOAh` | `lE7mW` |
| 書皮-下 `#7D5D3E` | `JL7ci` | `B09TC` |
| 內頁上緣暗線 `#00000020` | `dkEAp` | `F3w0xR`（`RK3GT` 下）|
| 內頁下緣反光 `#FFFFFF66` | `MqPf0` | `ocZfh`（`RK3GT` 下）|

⚠️ **書本 frame 自身已無 `fill`**（第十二輪的漸層已用 `fill: []` 清除），
書皮完全由上表四條邊構成。frame 上只剩 `stroke 1px #CAAF94` inner（外緣高光）、
外圓角 20、`clip: true` 與外投影。⛔ 手機 `shoHW` 的 `clip` 是第十三輪補的 ——
沒有它，四條方角的邊會戳出圓角外。

⚠️ **第十一輪：`shoHW` 與 `RK3GT` 的角色變了（ID 沒變）** —— `shoHW` 由「書頁卡組」變成**木色書皮本體**，
`RK3GT` 由「書頁卡」變成**內頁**，兩者都已改名。頁緣節點 `Beky5`（含 `Q4ijr`/`RvYSE`/`G9oPx`）**已刪除**。

⚠️ **第九輪刪除了四個節點**：卡內的點擊區 `nKXHk`／`c1KcAO` 與疊在照片上的箭頭 `Yj218`／`wSq5F`。
翻頁鈕改放在書頁卡下方的控制列（§14.3.2 已全面改寫），原本的頁點列 `By7TO` 被 `Move` 進控制列，
**ID 沒變、父容器變了**。⛔ 引用那四個舊 ID 會拿到「No node with id」。

`fAw6F`（桌機，**第十一輪改版後**）：眉標 `a6M8NC`／主標 `SeEnO`／金線 `dnRdn`／
書本列 `u3HAX`（1192）（翻頁鈕-上一頁(停用) `dTiVp`／
**書本 `OSper`**（1000×580，`$book-wood`，pad 12，外圓角 20）：
左頁 `E0qLqu`（488×556，`$surface`，圓角 `[8,0,0,8]`，照片 `vwrx1` 440×508）／
右頁 `bvCVJ`（488×556，`$surface`，圓角 `[0,8,8,0]`，**靠上對齊**）：年份標籤 `GuQyq`／段落標題 `JXYQE`／
故事文字 `joM75`／**頁碼列 `Z9Y4i`（頁碼 `uHQYU`）**；
書脊暗部-左 `Uh5q5`／書脊暗部-右 `j1mYSi`／書脊 `MnAfx`／
翻頁鈕-下一頁 `wbqUy`）／頁點列 `AIhWQ`（active `yU47P`）／操作提示 `YrnWO`。

⚠️ **第十一輪刪除了三個節點**：`書本組 biIYs`（外包層）與頁緣 `UCytP`／`Zs3oB`（含各自三條線）。
`OSper` 從書本組的子節點**改回書本列的直接子節點**（ID 沒變），並升格為木色書皮本體。

⚠️ **沒有「內頁」容器** —— 白色內頁是由左頁／右頁各自的 `$surface` 底色與半邊圓角拼成的
（左 `[8,0,0,8]`、右 `[0,8,8,0]`），不是一層包住兩頁的白框。原因見下方「算圖 stale」那則。
書脊三件是 `OSper` 的絕對定位子節點，座標已含書皮的 12 偏移（`x=444`／`500`／`500`，`y=12`，高 556）。

⚠️ **桌機左頁的節點 ID 於第八輪換過**（原滿版照片 `EhFK5` 已刪除）。左頁改為
「`E0qLqu` 左頁 frame（pad 24）＋ `vwrx1` 照片 402×472」兩層，理由見 §14.4.1 的修正紀錄。
⛔ 引用 `EhFK5` 會拿到「No node with id」。

**第七輪沒有 `hidden-in-variant`** —— 只畫第 1 頁的靜態畫面，未用 `Copy` 做五個頁面狀態。
翻頁鈕的停用態是以 `opacity: 0.3` 表現，**不是 `enabled: false`**（那會讓節點整個不顯示）。

**第二輪段內主要子節點（供後續標註對位）**：
`O1WPh` 相片列 `We3zu`／相片卡 `AXsVx`,`ycZaK`,`OQZIM`／頁點列 `TdXtY`；
`jtA2m` 分欄容器 `L0BMm`／主卡 `FJGe2`／場次列 `jVRYN`／資訊列群 `AgYWk`／地圖 `Y5g0jZ`／導航鈕 `PFuce`；
`l73sy` chips 列 `bnACO`（chip-喜餅領取 `TqXOl`）／表單鈕 `h7si45`／修改連結 `GLMiS`；
`QGIVK` monogram `xTgxQ`。

**第二輪也沒有 `hidden-in-variant`** —— 未使用 `Copy` 做變體，五段皆新建或 Move。

**本輪沒有 `hidden-in-variant`** —— 本批次未使用 `Copy` 做狀態變體，全檔 `enabled:false` 節點數為 0（已用
`Get(document,(n)=>n.enabled===false&&...)` 確認）。

**S7 OG 圖本體已於比對閘門補繪**（`design-lead` 手繪，落點 x=550 y=1000）。
`pen-drawer` 當輪未畫是正確的判斷 —— 當時 §2 只有 LINE 卡片那三行的逐字值，OG 圖的三段沒有值。
逐字值已補進 §2（`WE ARE GETTING MARRIED`／`Ethan & Chloe`／`2026 . 11 . 14　SATURDAY`），該張已補齊。

⚠️ **OG 圖的截圖目前會是空白**，那是 Pencil 對「非 active 文件上新建節點」的算圖快照限制
（見 `pen-authoring`），不是沒畫。節點資料已核對：14 個子節點齊全、文字逐字正確、圖片 fill 已套用。
使用者在 Pencil Desktop 開啟時會正常顯示。

### 8.1 畫布座標（實際落點）

| 節點 | x | y | w | h |
| --- | --- | --- | --- | --- |
| 裝置版-S1 Hero | 0 | 0 | 390 | 844 |
| 裝置版-S2 Gallery | 470 | 0 | 390 | 720 |
| 裝置版-S3 Info | 940 | 0 | 390 | 900 |
| 裝置版-S4 RSVP | 1410 | 0 | 390 | 560 |
| 裝置版-S5 Footer | 1880 | 0 | 390 | 420 |
| 裝置版-S6 音樂鈕狀態對照 | 0 | 1000 | 470 | 260 |
| 裝置版-S2 燈箱 | 0 | 1400 | 290 | 560 |
| 裝置版-S7 LINE卡片模擬 | 550 | 1680 | 343 | 330 |
| 電腦版-S8 Hero | 1830 | 1000 | 1440 | 900 |

**第九輪後的實際頂層落點**（S10 加寬加高後；輔助那一列維持 y=5900，未再移動）：

| 節點 | x | y | w | h |
| --- | --- | --- | --- | --- |
| 裝置版-單頁全覽 `lxtQz` | 0 | 0 | 390 | **5002** |
| 電腦版-單頁全覽 `ZQuAX` | 560 | 0 | 1440 | **5756** |
| 裝置版-S2 燈箱 `a8sUM` | 0 | **5900** | 290 | 560 |
| 裝置版-S6 音樂鈕狀態對照 `kouQN` | 380 | **5900** | 470 | 260 |
| 裝置版-S7 LINE卡片模擬 `J0wxV` | 950 | **5900** | 343 | 330 |
| 共用-S7 OG分享圖 `oB0o5` | 1400 | **5900** | 1200 | 630 |

> **輔助那一列的移動史**：4200 → 5000（第七輪，S10 插入）→ 5900（第八輪）。第九輪未再移動，
> 但**與桌機長頁底部的間隔已縮到 144**（第七、八輪都是 204）—— 再加一段就得再移一次。

桌機長頁 5756 ＝ 4012（第二輪實測）＋ 772（S9）＋ **972**（S10）。第十一輪未變。
手機長頁 5002 ＝ 3444 ＋ 820（S9）＋ **738**（S10，第十一輪由 732 加高 6 —— 書皮 12×2 減去原頁緣 6）。
**兩者皆為實測值。**

⚠️ **§13.9 桌機表列的段高與畫布現況有兩處對不上，那是 §13.9 沿用了未修正前的估值**：
段2 Gallery 實高 **942**（表列 980）、段3 Info 實高 **970**（表列 940）。兩者互相抵銷，
所以總高只差在 S9 那一項。§13.9 的表已於本輪一併校正為實測值。

⚠️ **S2-燈箱的座標與 §4／§9.2.1 寫的不同。** 原文寫「放在 S2 右側 x=+410」（＝ x 880），但 §1 的畫布排版
把 S3 排在 x=940，燈箱寬 290 會壓到 S3（880+290 = 1170 > 940）。本檔改放 x=0 / y=1400（S6 下方），
未動任何其他畫面。這是**畫布擺放**的調整，不影響畫面內容。

---

## 9. 版面規格與色票

> ⚠️ 本節是**訂定值**（設計系統推薦 ＋ 我依 RFP 排的版面），不是 Figma 量測值。

### 9.0 元件組成與呈現方式

| 項目 | 實際內容 | 依據 |
| --- | --- | --- |
| ① 頂欄實際放什麼 | **無頂欄。** 沒有選單鈕、沒有麵包屑、沒有搜尋、沒有通知、沒有使用者、沒有登出。全站無導覽列 | RFP §2「一頁式垂直串聯」 |
| ② 側欄 | **無側欄。** 零層 | 同上 |
| ③ 每種按鈕有沒有 icon | S3 導航鈕：**有**，左側 `navigation`（箭頭指標）16px；S4 表單鈕：**有**，右側 `external-link` 16px；S3 場次膠囊：**無 icon**，純文字；S4 修改連結：**純文字連結**，有底線無 icon；S1 SCROLL：文字下方 `chevron-down` 14px；S3 四條資訊列：各有 20px icon（`building`／`door-open`／`map-pin`／`users`）；音樂鈕：`disc` 24px（靜音態疊 `slash`）；燈箱關閉：`x` 20px。**以上以外一律無 icon，不要自行增補** | 本檔 §3 |
| ④ 每個操作的呈現方式 | 相片放大＝**全螢幕燈箱**（不是換頁、不是抽屜）；場次切換＝**就地切換卡內文字**（不換頁、不彈窗）；地圖導航＝**離站另開分頁**；RSVP＝**離站另開分頁**；SCROLL＝**同頁平滑捲動** | 本檔 §3、§5 |
| ⑤ 列表列的操作區形式 | **無列表、無表格。** 全站沒有任何表格 | — |
| ⑥ 圖片來源（本案專屬） | 一律 `Generate(id, "stock", prompt)`，見 §2.0。**禁止手寫 url** | pencil 指南 |
| ⑦ 裝飾元素清單（本案專屬） | 只有四種：S1／S8 的「線＋菱形」飾線、S5 的 monogram 圓環、S2 的頁點指示器、S2／S3 的金色細線。**S5 沒有飾線。不要自行加花草、緞帶、邊框紋樣、地圖圖釘** | 本檔 §2、§9.2.1 |

### 9.1 色票

| 用途 | 色碼 | 對應的 pen 變數名 | 來源 |
| --- | --- | --- | --- |
| 頁面主底（粉調） | `#FDF2F8` | `$bg-blush`（待建） | ui-ux-pro-max background |
| 頁面次底（象牙） | `#FFFBF7` | `$bg-ivory`（待建） | 本檔訂定 |
| 卡片／浮動元件底 | `#FFFFFF` | `$surface`（待建） | 本檔訂定 |
| 主色（強調、RSVP 主按鈕、頁點 active） | `#DB2777` | `$primary`（待建） | ui-ux-pro-max primary |
| 主色淺（次要強調、hover） | `#F472B6` | `$primary-soft`（待建） | ui-ux-pro-max secondary |
| CTA 金（地圖導航鈕、眉標） | `#CA8A04` | `$accent-gold`（待建） | ui-ux-pro-max CTA |
| 金色淺（飾線、monogram 圓環） | `#E7C873` | `$gold-soft`（待建） | 本檔訂定 |
| 主要文字／S5 底色 | `#831843` | `$text-main`（待建） | ui-ux-pro-max text |
| 次要文字（說明、標籤） | `#7A5560` | `$text-muted`（待建） | 本檔訂定（對 `#FDF2F8` 對比 4.6:1） |
| 反白文字（Hero、S5） | `#FFFFFF` | `$text-invert`（待建） | 本檔訂定 |
| 反白次要文字 | `#FFFFFFCC` | `$text-invert-muted`（待建） | 本檔訂定 |
| 卡片與分隔框線 | `#F0D9E2` | `$border-soft`（待建） | 本檔訂定 |
| 未選膠囊框線 | `#E4BFCD` | `$border-pill`（待建） | 本檔訂定 |
| 燈箱／Hero 遮罩 | `#00000073` | `$overlay-dark`（待建） | 本檔訂定（45% 黑） |
| 玻璃卡（倒數計時格） | `#FFFFFF26` | `$glass-fill`（待建） | 本檔訂定（15% 白） |
| 玻璃卡框線 | `#FFFFFF4D` | `$glass-border`（待建） | 本檔訂定（30% 白） |
| 卡片陰影色 | `#8318431F` | `$shadow-rose` | 本檔訂定（主文字色 12% 透明） |
| S3 資訊列 icon | `#CA8A04` | `$accent-gold` | 閘門補訂（與區塊眉標同色） |
| 按鈕內 icon（S3 導航／S4 external-link） | `#FFFFFF` | `$text-invert` | 閘門補訂（＝同一顆按鈕的文字色） |
| S1 SCROLL chevron | `#FFFFFFCC` | `$text-invert-muted` | 閘門補訂（＝SCROLL 文字色） |
| 燈箱關閉 icon | `#FFFFFF` | `$text-invert` | 閘門補訂 |
| S4 chip 底色 | `#FDF2F8` | `$bg-blush` | 閘門補訂（白卡片上需要底色才看得見 chip） |
| Hero 遮罩漸層（S1，上→下） | `#00000000` → `#0000008C` | （不設變數，直接寫字面值） | 閘門補訂。⚠️ 這裡**不使用** `$overlay-dark`——該變數是燈箱專用的均勻 45% 黑 |
| Hero 遮罩漸層（S8，左→右） | `#000000D9` → `#00000073`(50%) → `#00000026` | （同上，字面值） | 閘門補訂。`rotation: 180` ＝ 左暗右亮 |
| 音樂鈕外圈（尚未播放態） | `#E7C87380` | （字面值，＝`$gold-soft` 50% alpha） | 閘門補訂 |
| **故事書書皮（S10 專用）** | `#A67C52` | `$book-wood` ✅ **已建於 `.pen`（第十一輪）** | 第十一輪新增，見 §14.4.2 ① |

⚠️ **`$book-wood` 是全站唯一的棕色，且只准用在 S10 的書皮。**

> ⚠️ **第十二輪之後，`.pen` 裡已經沒有任何節點引用 `$book-wood`** ——
> 書皮改成四邊分色（`#BD9B79`／`#B18961`／`#956F4A`／`#7D5D3E`，見 §14.4.2 ①-A）之後，四個值都是字面色碼。
> 變數保留著當**基色的文件紀錄**（漸層的兩端就是它上下各偏移 12% 明度算出來的），
> ⛔ 但不要以為「改這個變數就能改書皮顏色」——**改它不會有任何效果**，要改的是那兩個字面值。

> ⛔ **色票寫在本節不等於變數存在於 `.pen`。** 第十一輪繪製時 `$book-wood` 只登記在這張表、
> 檔案裡並沒有這個變數 —— 而 `fill: "$book-wood"` **沒有報錯、沒有警告，直接被填成黑色 `#000000`**。
> 是因為順手 `Print` 了一次 `GetVariables()` 才發現書皮是黑的。
> **本節新增色票時，繪製的第一步一定是 `GetVariables()` 確認、缺的用 `SetVariables()` 補**
> （見 [[pen-screen-drawing]] §0）。⚠️ 補完變數之後**要重新 `Update` 一次那個 `fill`** ——
> 已經落地的 `#000000` 不會因為變數後來建好就自己變回來。
它不是主題色的一員 —— 加它是為了讓書從象牙色背景裡分離出來（原本白書配象牙底幾乎融在一起）。
⛔ 不要把它擴散到其他段落的邊框、按鈕或文字。

### 9.2 版面骨架

| 元素 | 量測值 | 說明 |
| --- | --- | --- |
| 基準畫布寬 | 390 | mobile-first |
| 頁面左右安全邊距 | 24 | 內容最大寬 = 342 |
| 卡片圓角 | 20 | S3／S4 主卡 |
| 相片卡圓角 | 16 | S2 |
| 按鈕高 | 52（S3 導航）／54（S4 表單） | — |
| 按鈕圓角 | 26／27（＝全圓角膠囊） | — |
| 按鈕內距 | `[0, 24]` | 文字置中 |
| 膠囊（場次）高 | 40，圓角 20，內距 `[0,20]` | — |
| chips 高 | 30，圓角 15，內距 `[0,14]`，gap 8 | — |
| 音樂鈕 | 56×56 圓，圓角 28 | 距畫面右 16、下 24 |
| 倒數計時格 | 68×80，圓角 14，gap 12 | 4 格總寬 = 68×4+12×3 = 308 |
| 卡片陰影 | `y=8 blur=28 color=$shadow-rose` | — |
| 浮動鈕陰影 | `y=4 blur=16 color=$shadow-rose` | — |

#### 9.2.1 容器階層

```
S1 Hero 390×844   fill=stock 圖 + 疊一層 $overlay-dark 漸層（上 0% → 下 55%）
└ 內容欄 342×fit  layout=vertical alignItems=center  pad [120,24,0,24]  gap 0
  ├ 眉標 "WE ARE GETTING MARRIED"  h=16
  ├ (spacer 20)
  ├ 英文姓名 "Ethan & Chloe"       h=72
  ├ (spacer 8)
  ├ 中文姓名 "陳彥廷 ✕ 林思妤"      h=26
  ├ (spacer 28)
  ├ 飾線群組 80×12  layout=horizontal alignItems=center gap 8   ← 28+8+8+8+28 = 80（原寫 72，算錯）
  │ ├ 線 28×1 ／ 菱形 8×8（旋轉 45°，可用 polygon） ／ 線 28×1
  ├ (spacer 28)
  ├ 婚期 "2026 . 11 . 14　SATURDAY" h=22
  ├ (spacer 40)
  └ 倒數群組 308×80  layout=horizontal gap 12
    └ 格×4 68×80  layout=vertical alignItems=center justifyContent=center gap 4
      ├ 數字 h=34
      └ 標籤 h=12
高度驗算：120+16+20+72+8+26+28+12+28+22+40+80 = 472（內容底 y=472；實測文字高略小，餘量落在底部留白）
浮動於底：SCROLL 群組 y=760（文字 h=12 + gap 6 + chevron 14）；音樂鈕 y=764 x=318

S2 Gallery 390×720  fill=$bg-ivory  layout=vertical alignItems=center pad [64,0]  gap 0
├ 眉標 "GALLERY" h=14
├ (spacer 10)
├ 主標 "Our Moments" h=46
├ (spacer 12)
├ 金線 40×1
├ (spacer 20)
├ 金句 300×52（兩行）
├ (spacer 32)
├ 輪播列 390×340  layout=horizontal alignItems=center gap 12  pad [0,21]  clip
│ ├ 鄰卡左 44×300  radius 16 opacity 0.55（只露出右半）
│ ├ 主卡 260×340  radius 16 shadow
│ └ 鄰卡右 44×300  radius 16 opacity 0.55
├ (spacer 24)
├ 頁點列 fit×8 layout=horizontal gap 6：active 膠囊 20×8 radius 4 $primary ＋ 4 顆 8×8 圓 $border-pill
├ (spacer 16)
└ 提示 "左右滑動瀏覽・點擊放大" h=14
高度驗算：64+14+10+46+12+1+20+52+32+340+24+8+16+14 = 653（餘 67 為底部留白）

S2-燈箱 290×560（獨立 frame，畫布座標 x=0 y=1400 —— 原訂「S2 右側 x=+410」會壓到排在 x=940 的 S3，已改）
└ 遮罩 fill=$overlay-dark
  ├ 關閉 icon 20×20  右上 pad 16
  ├ 大圖 250×360  radius 12  置中
  └ 頁碼 "3 / 5"  底部 pad 32

S3 Info 390×900  fill=$bg-blush  layout=vertical alignItems=center pad [64,24]  gap 0
├ 眉標 "INFORMATION" h=14
├ (spacer 10)
├ 主標 "Wedding Day" h=46
├ (spacer 24)
├ 主卡 342×670  radius 20  fill=$surface  shadow  pad 24  layout=vertical gap 0 alignItems=center
│   （原訂 600 是算錯：驗算式把每條資訊列算成 20，但同一棵樹寫的組成是「標籤 14 ＋ gap 3 ＋ 值 20」＝37，
│    且「地址」實際換 2 行、「桌次引導」實際換 3 行。資訊列群實排 222 而非 154，故主卡 670。
│    S3 整屏 856 < 900，畫面高不變。）
│ ├ 場次列 294×40 layout=horizontal gap 8：膠囊×2 各 143×40
│ ├ (spacer 24)
│ ├ 日期大字 h=38
│ ├ (spacer 6)
│ ├ 日期副標 h=18
│ ├ (spacer 20)
│ ├ 虛線 294×1（用 1px 矩形 fill=$border-soft 代替虛線）
│ ├ (spacer 20)
│ ├ 資訊列群 294×fit layout=vertical gap 18
│ │ └ 資訊列 294×fit layout=horizontal gap 12 alignItems=start
│ │   ├ icon 20×20
│ │   └ 文字欄 262×fit layout=vertical gap 3：標籤 h=14 ／ 值 h=20（桌次那列 h=40 兩行）
│ ├ (spacer 22)
│ ├ 地圖預覽 294×120 radius 12
│ ├ (spacer 16)
│ └ 導航鈕 294×52 radius 26 fill=$accent-gold layout=horizontal alignItems=center justifyContent=center gap 8
├ (spacer 16)
└ 入場提醒 h=14
高度驗算：64+14+10+46+24+670+16+14 = 858（餘 42 為底部留白）
主卡內驗算：24+40+24+38+6+18+20+1+20+**222**+22+120+16+52+24 = 647，加上文字實測餘量 ≒ 670
資訊列群 222 ＝ 宴會地點 37 ＋18＋ 宴會廳 37 ＋18＋ 地址 57（2行）＋18＋ 桌次引導 77（3行）

S4 RSVP 390×560  fill=$bg-ivory→$bg-blush 垂直漸層  layout=vertical alignItems=center pad [64,24] gap 0
├ 眉標 "R.S.V.P." h=14
├ (spacer 10)
├ 主標 "Will You Join Us?" h=46
├ (spacer 16)
├ 說明文 310×48（兩行）
├ (spacer 24)
├ 卡片 342×236 radius 20 fill=$surface shadow pad 24 layout=vertical alignItems=center gap 0
│   （內容加總 216，底部刻意多留 20 的呼吸空間 —— 這是設定值不是漏算）
│   （chips 兩列容器寬用 fit_content：第一行四顆實測 296，比 294 多 2px，固定寬會被裁）
│ ├ chips 群 294×68 layout=horizontal gap 8（自動換行成兩行，行距 8）
│ ├ (spacer 20)
│ ├ 表單鈕 294×54 radius 27 fill=$primary layout=horizontal alignItems=center justifyContent=center gap 8
│ ├ (spacer 12)
│ └ 註記 h=14
├ (spacer 20)
└ 修改連結 h=16
高度驗算：64+14+10+46+16+48+24+236+20+16 = 494（餘 66 為底部留白）

S5 Footer 390×420  fill=$text-main  layout=vertical alignItems=center pad [64,24] gap 0
├ 主標 "Thank You" fill=$text-invert h=54
├ (spacer 18)
├ 內文 300×46（兩行）fill=$text-invert-muted
├ (spacer 32)
├ monogram 96×96 圓 stroke 1 $gold-soft，內文字 "E　&　C" fill=$gold-soft
├ (spacer 24)
├ 婚期 h=18 fill=$text-invert-muted
├ (spacer 12)
└ 版權 h=12 fill=$text-invert-muted opacity 0.7
高度驗算：64+54+18+46+32+96+24+18+12+12 = 376（餘 44）

S6 音樂鈕狀態對照 470×260  fill=$bg-ivory  pad 32  layout=vertical gap 20
├ 標題 "音樂控制鈕 — 三種狀態" h=20
└ 狀態列 406×fit layout=horizontal gap 40 justifyContent=center
  └ 狀態組 ×3 layout=vertical alignItems=center gap 12
    ├ 鈕 56×56 圓（見 §4 三態畫法）
    └ 標籤 h=14

S7 社群分享預覽 1200×630（OG 圖本體）
└ 圖 fill=stock，左側疊文字群 pad [0,80]：眉標 ／ 姓名 Great Vibes 84 ／ 日期
另附「LINE 卡片模擬」343×330 獨立 frame，放在 S7 下方 y=+680：
└ 卡片 fill=$surface radius 12 stroke $border-soft
  ├ 縮圖 343×172（同 OG 圖縮小）
  └ 文字區 pad 12 layout=vertical gap 4：標題 h=20（單行截斷）／ 內文 h=32（兩行）／ 網域 h=14

S8 桌機 Hero 1440×900  fill=stock 圖 ＋ 左側 $overlay-dark 漸層（左 60% → 右 0%）
└ 內容欄 520×fit  絕對定位 x=120 y=250  layout=vertical alignItems=start gap 0
  ├ 眉標 h=18 ／ (spacer 24) ／ 英文姓名 Great Vibes 96 h=120
  ├ (spacer 12) ／ 中文姓名 h=32 ／ (spacer 32)
  ├ 飾線 96×12（靠左）／ (spacer 32)
  ├ 婚期 h=26 ／ (spacer 48)
  └ 倒數群組 4 格 84×96 gap 16（總寬 384）
音樂鈕 x=1352 y=812
```

#### 9.2.2 逐元素文字規格

字型只用兩套：`Great Vibes`（手寫標題）與 `Cormorant Infant`（其餘全部）。
中文由 `Cormorant Infant` 的系統中文後援顯示；**中文絕對不要套 Great Vibes**（該字型沒有中文字符，會變豆腐字）。

| 文字元素 | 字級 | 字重 | 字型 | 字距 | 顏色 |
| --- | --- | --- | --- | --- | --- |
| S1 眉標 WE ARE GETTING MARRIED | 11 | 500 | Cormorant Infant | 4 | `$text-invert-muted` |
| S1 英文姓名 | 56 | 400 | Great Vibes | 0 | `$text-invert` |
| S1 中文姓名 | 18 | 400 | Cormorant Infant | 6 | `$text-invert` |
| S1 婚期 | 16 | 500 | Cormorant Infant | 3 | `$text-invert` |
| S1 倒數數字 | 26 | 600 | Cormorant Infant | 0 | `$text-invert` |
| S1 倒數標籤 | 10 | 500 | Cormorant Infant | 2 | `$text-invert-muted` |
| S1 SCROLL | 10 | 500 | Cormorant Infant | 3 | `$text-invert-muted` |
| 區塊眉標（GALLERY／INFORMATION／R.S.V.P.） | 11 | 600 | Cormorant Infant | 5 | `$accent-gold` |
| 區塊主標（Our Moments／Wedding Day／Will You Join Us?） | 34 | 400 | Great Vibes | 0 | `$primary` |
| S2 金句 | 16 | 400（italic） | Cormorant Infant | 0 | `$text-muted` |
| S2 操作提示 | 11 | 400 | Cormorant Infant | 1 | `$text-muted` |
| S2-燈箱 頁碼 | 13 | 500 | Cormorant Infant | 2 | `$text-invert` |
| S3 場次膠囊（選中） | 14 | 600 | Cormorant Infant | 1 | `$text-invert` |
| S3 場次膠囊（未選） | 14 | 500 | Cormorant Infant | 1 | `$text-muted` |
| S3 日期大字 | 30 | 600 | Cormorant Infant | 2 | `$text-main` |
| S3 日期副標 | 13 | 400 | Cormorant Infant | 1 | `$text-muted` |
| S3 資訊列標籤 | 11 | 600 | Cormorant Infant | 2 | `$text-muted` |
| S3 資訊列值 | 15 | 500 | Cormorant Infant | 0 | `$text-main` |
| S3 導航鈕文字 | 15 | 600 | Cormorant Infant | 1 | `$text-invert` |
| S3 入場提醒 | 11 | 400 | Cormorant Infant | 0 | `$text-muted` |
| S4 說明文 | 14 | 400 | Cormorant Infant | 0 | `$text-muted` |
| S4 chips 文字 | 12 | 500 | Cormorant Infant | 0 | `$primary` |
| S4 表單鈕文字 | 15 | 600 | Cormorant Infant | 1 | `$text-invert` |
| S4 註記 | 11 | 400 | Cormorant Infant | 0 | `$text-muted` |
| S4 修改連結 | 12 | 500（底線） | Cormorant Infant | 0 | `$text-muted` |
| S5 Thank You | 42 | 400 | Great Vibes | 0 | `$text-invert` |
| S5 內文 | 14 | 400 | Cormorant Infant | 0 | `$text-invert-muted` |
| S5 monogram | 20 | 500 | Cormorant Infant | 2 | `$gold-soft` |
| S5 婚期 | 13 | 500 | Cormorant Infant | 3 | `$text-invert-muted` |
| S5 版權 | 10 | 400 | Cormorant Infant | 1 | `$text-invert-muted` |
| S6 標題 | 15 | 600 | Cormorant Infant | 0 | `$text-main` |
| S6 狀態標籤 | 12 | 500 | Cormorant Infant | 0 | `$text-muted` |
| S7 OG 姓名 | 84 | 400 | Great Vibes | 0 | `$text-invert` |
| S7 OG 眉標／日期 | 20／22 | 500 | Cormorant Infant | 4 | `$text-invert-muted`／`$text-invert` |
| S7 LINE 卡標題 | 14 | 600 | Cormorant Infant | 0 | `$text-main` |
| S7 LINE 卡內文 | 12 | 400 | Cormorant Infant | 0 | `$text-muted` |
| S7 LINE 卡網域 | 11 | 400 | Cormorant Infant | 0 | `$text-muted` |
| S8 眉標 | 13 | 500 | Cormorant Infant | 4 | `$text-invert-muted` |
| S8 英文姓名 | 96 | 400 | Great Vibes | 0 | `$text-invert` |
| S8 中文姓名 | 26 | 400 | Cormorant Infant | 8 | `$text-invert` |
| S8 婚期 | 20 | 500 | Cormorant Infant | 4 | `$text-invert` |
| S8 倒數數字／標籤 | 34／12 | 600／500 | Cormorant Infant | 0／2 | `$text-invert`／`$text-invert-muted` |

行高一律 `lineHeight: 1.4`，唯 Great Vibes 標題用 `1.2`，倒數數字用 `1.0`。

### 9.3 對齊與排列

| 容器 | direction | justifyContent | alignItems | gap | 寬度 |
| --- | --- | --- | --- | --- | --- |
| S1／S2／S3／S4／S5 內容欄 | vertical | start | center | 0（用 spacer 控制） | 342 或 fill_container |
| S1 倒數群組 | horizontal | center | start | 12 | 308（fit_content） |
| S1 倒數單格 | vertical | center | center | 4 | 68 |
| S2 輪播列 | horizontal | center | center | 12 | fill_container（超出裁切） |
| S2 頁點列 | horizontal | center | center | 6 | fit_content |
| S3 場次列 | horizontal | center | center | 8 | 294 |
| S3 資訊列 | horizontal | start | **start**（icon 對齊第一行） | 12 | 294 |
| S3／S4 按鈕 | horizontal | center | center | 8 | 294 |
| S4 chips 群 | horizontal | center | center | 8（換行行距 8） | 294 |
| S6 狀態列 | horizontal | center | start | 40 | fit_content |
| S8 內容欄 | vertical | start | **start** | 0 | 520 |

### 9.4 逐畫面差異

| 畫面 | 與基準的差異 |
| --- | --- |
| 裝置版-S2 燈箱 | 獨立 frame，非頁面區塊；底為 `$overlay-dark`，圖片為 S2 主卡同一張 |
| S6 | 展示板，不是頁面內容。實際音樂鈕固定在畫面右下 `right:16 bottom:24` |
| S7 | OG 圖 1200×630 為社群平台規格，不隨頁面縮放；LINE 卡片模擬寬 343 |
| S8 | 桌機 1440 寬。內容改**靠左**（不是置中），字級全面放大約 1.7 倍，遮罩改為左→右漸層 |

音樂鈕三態畫法：

| 狀態 | 畫法 |
| --- | --- |
| 尚未播放 | 56×56 圓 `$surface`，外圈 1px 虛線示意用 `$gold-soft` 實線 opacity 0.5；內 `disc` icon 24 色 `$primary` |
| 播放中 | 同上，外圈改 2px 實線 `$accent-gold`；icon 色 `$primary` |
| 已靜音 | 同上，外圈 1px `$border-pill`；icon 改 `volume-x` 24 色 `$text-muted`，整體 opacity 0.75 |

---

## 9.5 連續長頁與桌機版式（第二輪追加）

### 9.5.0 為什麼要改成長頁

第一輪把五個區塊畫成五張獨立畫布（高度 844／720／900／560／420），並排看像五個不相干的頁面，
**看不出這是一條連續捲動的網頁**。第二輪改成兩條完整長頁，區塊只是長頁裡的一段，不再是獨立稿件。

### 9.5.1 手機長頁（已完成）

`裝置版-單頁全覽`　390×3444　`layout=vertical gap=0 alignItems=start`

由上而下五段，段與段之間**沒有間隙**（gap 0）：

```
裝置版-S1 Hero      390×844   （y 0    ～ 844）
裝置版-S2 Gallery   390×720   （y 844  ～ 1564）
裝置版-S3 Info      390×900   （y 1564 ～ 2464）
裝置版-S4 RSVP      390×560   （y 2464 ～ 3024）
裝置版-S5 Footer    390×420   （y 3024 ～ 3444）
高度驗算：844+720+900+560+420 = 3444 ✓
```

音樂鈕留在 S1 內（x=318 y=764），**代表的是 `position: fixed` 的第一屏落點**，
不是只在 Hero 出現 —— 實作時它固定在視窗右下 `right:16 bottom:24`，整條長頁都看得到。

### 9.5.2 桌機長頁（本輪要畫）

`電腦版-單頁全覽`　1440×3700　`layout=vertical gap=0 alignItems=start`

**通用規則**（五段共用，不要逐段各訂一套）：

| 項目 | 值 |
| --- | --- |
| 畫布寬 | 1440 |
| 內容欄寬 | 1120，水平置中（左右各留 160） |
| 區塊上下內距 | 上 96 ／ 下 96（Hero 除外，Hero 是滿版圖） |
| 色票 | **與手機版完全相同**，一個都不新增（用 §9.1 既有的 pen 變數） |
| 字型 | 同 §9.2.2：Great Vibes 只用於英文主標，其餘 Cormorant Infant |
| 圓角 | 卡片 24（手機是 20）／相片 20（手機 16）／按鈕全圓角 |
| 音樂鈕 | 56×56，固定在 x=1352 y=812（＝第一屏右下），只畫在 Hero 段 |

**桌機字級**（手機值 → 桌機值；沒列到的一律沿用手機值）：

| 元素 | 手機 | 桌機 |
| --- | --- | --- |
| 區塊眉標 | 11 | 14（字距 6） |
| 區塊主標（Great Vibes） | 34 | 56 |
| 金句 | 16 | 20 |
| 資訊列標籤 | 11 | 13 |
| 資訊列值 | 15 | 18 |
| 日期大字 | 30 | 40 |
| 按鈕文字 | 15 | 17 |
| chips 文字 | 12 | 14 |
| 說明文 | 14 | 17 |
| Footer 主標（Great Vibes） | 42 | 64 |
| Footer 內文 | 14 | 17 |

#### 段 1：Hero　1440×900　（已存在，`電腦版-S8 Hero`，直接 Move 進長頁當第一段）

不要重畫。底圖與遮罩已調校過（遮罩 `rotation:180`，左暗右亮，見 §9.1）。

#### 段 2：Gallery　1440×880

⛔ **桌機沒有「左右滑動」** —— 三張相片並排全部看得見，不是輪播。所以：

```
Gallery 1440×880  fill=$bg-ivory  layout=vertical alignItems=center pad [96,160]
├ 眉標 "GALLERY"                h=18
├ (spacer 12)
├ 主標 "Our Moments"            h=68
├ (spacer 16)
├ 金線 64×1  fill=$gold-soft
├ (spacer 24)
├ 金句 "願我們的故事，從今天起有了共同的名字。"  單行置中  h=28
│   （⛔ 桌機版是**一行**，不是手機版的兩行）
├ (spacer 48)
├ 相片區 1440×480（滿版出血，超出內容欄 1120）  overflow=hidden
│ └ 跑馬帶  layout=horizontal gap 20  ← 由右往左自動捲動，詳見 §12
│    └ 相片卡 ×5  360×480  radius 20  shadow（＋複製一份接在後面做無縫循環）
│  ⛔ **桌機是自動捲動，不是靜態排列。** 五張都要 Generate。
│  ⛔ 相片區**刻意做成滿版出血**（左右不留 160 內距），
│     讓照片從畫面邊緣進出，捲動才有「延伸出去」的感覺；
│     若沿用 1120 內容欄寬，照片會在畫面中間憑空出現與消失。
│  ⚠️ `prefers-reduced-motion` 時改為靜態 3＋2 兩列，見 §12.4。
├ (spacer 32)
├ ⛔ **桌機不畫頁點列**
│   頁點是「你在第幾張」的指示器，而桌機五張全部並排看得見，沒有「第幾張」這回事。
│   實作時桌機隱藏，手機保留。
└ 提示 "點擊放大檢視"  h=18
    ⛔ 文字與手機版不同 —— 桌機沒有滑動手勢，不可寫「左右滑動瀏覽」
高度驗算：96+18+12+68+16+1+24+28+48+480+32+18+96 = 937 → **段 2 高度定為 942**
（單列 480；頁點列與其前的 spacer 已移除。942 是設計檔與前端實作的共同實測值 ——
  前端 942、設計檔 fit_content 量到 935，取前端值對齊，差 7px 屬文字渲染誤差）
⚠️ `prefers-reduced-motion` 的 3＋2 降級版式相片區是 980 高，該情境下段 2 會撐到約 1480 ——
   那是使用者主動開啟減少動態時才會出現的版面，**不是預設值**，長頁總高以預設的 4050 為準。
```

#### 段 3：Info　1440×820

⛔ **桌機改成左右分欄** —— 手機是資訊卡在上、地圖在下的直式堆疊，桌機把地圖挪到右邊：

```
Info 1440×820  fill=$bg-blush  layout=vertical alignItems=center pad [96,160]
├ 眉標 "INFORMATION"   h=18
├ (spacer 12)
├ 主標 "Wedding Day"   h=68
├ (spacer 48)
├ 分欄容器 1120×fit  layout=horizontal gap 40  alignItems=start
│ ├ 左欄：主卡 540×fit  radius 24 fill=$surface shadow pad 40  layout=vertical alignItems=center gap 0
│ │  ├ 場次列 460×48  layout=horizontal gap 12（膠囊各 224×48 radius 24）
│ │  ├ (spacer 28) ／ 日期大字 h=50 ／ (spacer 8) ／ 日期副標 h=24
│ │  ├ (spacer 24) ／ 分隔線 460×1 fill=$border-soft ／ (spacer 24)
│ │  └ 資訊列群 460×fit  layout=vertical gap 24
│ │     └ 資訊列 layout=horizontal gap 16 alignItems=start
│ │        ├ icon 24×24  fill=$accent-gold
│ │        └ 文字欄 420×fit  layout=vertical gap 4：標籤 h=18 ／ 值 h=26
│ │           ⚠️ 欄寬 420。實測 18px 下：地址 267 寬**單行**；
│ │              **桌次引導 472 寬會溢出 52px → 該列的值必須換兩行**
│ │              （作法：值的文字節點設 `textGrowth:"fixed-width"` ＋ `width:"fill_container"`）
│ │              ⛔ 不要為了排版改文案、也不要單獨縮那一列的字級
│ └ 右欄 540×fit  layout=vertical gap 20
│    ├ 地圖預覽 540×400  radius 24（Generate，prompt 同 §2.0 地圖那列）
│    └ 導航鈕 540×60  radius 30  fill=$accent-gold  icon `navigation` 18 ＋ 文字
├ (spacer 24)
└ 入場提醒 "※ 宴會廳將於開席前 30 分鐘開放入場"  h=18  置中
高度驗算：96+18+12+68+48+左欄實高+24+18+96
左欄實高 ＝ 40+48+28+50+8+24+24+1+24+(26+... 四列各 48 ＋ 3×24 gap ＝ 264)+40 ≈ 551
實測（桌次引導換兩行後）：主卡 582，段 3 內容高 961 → **段 3 高度定為 970**
```

#### 段 4：RSVP　1440×620

```
RSVP 1440×620  fill=垂直漸層 $bg-ivory→$bg-blush  layout=vertical alignItems=center pad [96,160]
├ 眉標 "R.S.V.P."          h=18
├ (spacer 12)
├ 主標 "Will You Join Us?" h=68
├ (spacer 20)
├ 說明文「您的出席是我們最珍貴的祝福，敬請於 2026 / 10 / 15 前回覆。」單行置中 h=24
│   （⛔ 桌機版一行，不是手機版的兩行）
├ (spacer 40)
├ chips 列 fit×36  layout=horizontal gap 12  justifyContent=center
│   ⛔ **桌機七顆排一行**（不換行）。chip 高 36 radius 18 pad [0,18] fill=$bg-blush 文字 $primary
├ (spacer 40)
├ 表單鈕 360×60  radius 30  fill=$primary  文字 ＋ 右側 icon `external-link` 18
├ (spacer 16)
├ 註記 "將另開新視窗前往 Google 表單"  h=18
├ (spacer 24)
└ 修改連結 "已經填寫過了？點此修改回覆"  h=20（底線）
高度驗算：96+18+12+68+20+24+40+36+40+60+16+18+24+20+96 = 588 → 段 4 高度 620 ✓（底部餘 32）
```

#### 段 5：Footer　1440×480

```
Footer 1440×480  fill=$text-main  layout=vertical alignItems=center pad [96,160]
├ 主標 "Thank You"  Great Vibes 64  fill=$text-invert  h=80
├ (spacer 24)
├ 內文「謝謝每一位陪伴我們走到這裡的人，期待與你分享這一天的喜悅。」單行 h=24  fill=$text-invert-muted
├ (spacer 40)
├ monogram 120×120 圓 stroke 1 $gold-soft，內文字 "E　&　C" 24px fill=$gold-soft
├ (spacer 32)
├ 婚期 "2026 . 11 . 14"  h=22  fill=$text-invert-muted
├ (spacer 16)
└ 版權  h=16  fill=$text-invert-muted opacity 0.7
高度驗算：96+80+24+24+40+120+32+22+16+16+96 = 566 → **段 5 高度改為 580**
```

#### 桌機長頁總高

| 段 | 高 |
| --- | --- |
| Hero | 900 |
| Gallery | 942 |
| Info | 970 |
| RSVP | 620 |
| Footer | 580 |
| **合計** | **4012** |

`電腦版-單頁全覽` 五段相加 900+942+970+620+580 = **4012**（設計檔實測值）。

### 9.5.3 畫布落點（第二輪重排後）

| 節點 | x | y | w | h |
| --- | --- | --- | --- | --- |
| `裝置版-單頁全覽` | 0 | 0 | 390 | 3444 |
| `電腦版-單頁全覽` | 560 | 0 | 1440 | 4012 |
| `裝置版-S2 燈箱` | 0 | 3700 | 290 | 560 |
| `裝置版-S6 音樂鈕狀態對照` | 380 | 3700 | 470 | 260 |
| `裝置版-S7 LINE卡片模擬` | 950 | 3700 | 343 | 330 |
| `共用-S7 OG分享圖` | 1400 | 3700 | 1200 | 630 |

✅ 輔助那一列在 y=4200，與桌機長頁（y 0～4012）不重疊。

#### 9.5.3-A 實際落點（第二輪繪製後實測）

| 節點 | id | x | y | w | h |
| --- | --- | --- | --- | --- | --- |
| `裝置版-單頁全覽` | `lxtQz` | 0 | 0 | 390 | 3444 |
| `電腦版-單頁全覽` | `ZQuAX` | 560 | 0 | 1440 | **4020** |
| `裝置版-S2 燈箱` | `a8sUM` | 0 | 4200 | 290 | 560 |
| `裝置版-S6 音樂鈕狀態對照` | `kouQN` | 380 | 4200 | 470 | 260 |
| `裝置版-S7 LINE卡片模擬` | `J0wxV` | 950 | 4200 | 343 | 330 |
| `共用-S7 OG分享圖` | `oB0o5` | 1400 | 4200 | 1200 | 630 |

桌機長頁段落（相對長頁的 y）：

| 段 | id | y | h | 內容實高（含上下 padding） | 底部餘白 |
| --- | --- | --- | --- | --- | --- |
| 段1 Hero | `HlNtS` | 0 | 900 | —（滿版圖，未改） | — |
| 段2 Gallery | `O1WPh` | 900 | 980 | 963 | 17 |
| 段3 Info | `jtA2m` | 1880 | 940 | 934 | 6 |
| 段4 RSVP | `l73sy` | 2820 | 620 | 583 | 37 |
| 段5 Footer | `QGIVK` | 3440 | 580 | 557 | 23 |
| **合計** | | | **4020** | | |

⚠️ 高度合計與 §9.5.2 總表的 4020 **完全相符**（段高是分析檔訂定的固定值，內容實高小於段高的差額落在底部留白）。

⚠️ **實測發現的規格落差（未自行修正，待裁決）**：§9.5.2 段 3 註記「460 的欄寬比手機的 262 寬得多，
**地址與桌次引導在桌機版都是單行**」。實測 18px 字級下：
「台北市松山區敦化北路二段 158 號」＝ 267px（< 文字欄 420，單行成立 ✓）；
「入口處設有座位表，男方親友請至 A 區、女方親友請至 B 區」＝ **472px（> 420，溢出 52px）**，
以主卡 540 ＋ padding 40 計算會**超出白卡右緣 12px**。本輪照分析檔畫成單行未動，詳見 pen-drawer 回報。

---

## 10. 動態規格（捲動動畫與持續動畫）

> **為什麼要有這一節**：`CLAUDE.md` 把本站定位成「沉浸式」，而沉浸感幾乎全部來自動態。
> 第一版規格只寫了靜態版面，前端只能自己編一套動畫 —— 做完才發現方向不對的返工成本，
> 比任何一個色值或間距都貴。**這一節就是把「沉浸式」這個形容詞展開成可執行的值。**
>
> 定調：**克制、緩慢、單向。** 這是喜帖不是產品官網，動畫要像布幔被風掀起，
> 不要像簡報換頁。⛔ 沒有彈跳（bounce）、沒有旋轉入場、沒有翻牌、沒有彩帶特效。

### 10.1 動畫語彙庫（⛔ 全站只有這四種，不要再發明第五種）

| 代號 | 動作 | 起始值 → 結束值 | 用在哪 |
| --- | --- | --- | --- |
| `fade-up` | 淡入 ＋ 由下輕推 | `opacity 0 → 1`，`translateY 24px → 0` | 所有文字、按鈕、卡片 |
| `fade-in` | 純淡入 | `opacity 0 → 1` | 遮罩、分隔線、頁點、細節裝飾 |
| `reveal-mask` | 遮罩由下往上揭開 | `clip-path: inset(100% 0 0 0) → inset(0 0 0 0)` | **只用於相片**（Gallery 三張／輪播主卡） |
| `line-grow` | 線條由中心向兩側展開 | `transform: scaleX(0) → scaleX(1)`，`transform-origin: center` | 飾線、金線、分隔線 |

**桌機的位移量放大**：`fade-up` 在 ≥1024px 用 `translateY 32px`（手機 24px）。
理由是桌機視野大，24px 的位移在 1440 寬的畫面上幾乎看不出來。

### 10.2 節奏參數（全站統一，不要逐段各訂一套）

| 參數 | 值 | 說明 |
| --- | --- | --- |
| 文字類時長 | `700ms` | `fade-up`／`fade-in` |
| 圖片類時長 | `900ms` | `reveal-mask`／相片的 `fade-in` |
| 線條時長 | `600ms` | `line-grow` |
| 緩動 | `cubic-bezier(0.22, 1, 0.36, 1)` | 快起慢收。**收尾慢＝優雅**，這是整體調性的關鍵，不要換成 `ease` 或 `linear` |
| 交錯間隔 | `90ms` | 同一段內元素依序進場 |
| 相片交錯 | `140ms` | 桌機 Gallery 三張並排時，間隔拉大比較有節奏 |

### 10.3 觸發規則

用 `IntersectionObserver`，**不要監聽 scroll 事件**（每幀觸發，會掉幀）。

| 參數 | 值 | 理由 |
| --- | --- | --- |
| `threshold` | `0.15` | 露出 15% 就開始，不要等整段進來才動 |
| `rootMargin` | `0px 0px -10% 0px` | 底部縮 10%，讓元素進到視野**內**一點才觸發，避免貼著邊緣就播完 |
| 播放次數 | **只播一次**，播完 `unobserve` | ⛔ 不要來回播。往回捲又重播一次，賓客會覺得頁面在閃 |

**觀察的是「段落」不是「每個元素」** —— 一段觸發後，段內元素靠 `transition-delay` 交錯，
這樣只需要 5 個 observer 而不是幾十個。

### 10.4 逐段分鏡

延遲欄是**相對於該段觸發時刻**的累積值（＝前一個的延遲 ＋ 90ms，圖片段用 140ms）。

#### 段 1 Hero —— ⛔ 這一段不是捲動觸發，是「進站入場」

頁面載入完成即播放（不等捲動）。這是賓客看到的第一個畫面，是整份喜帖的第一印象。

| 順序 | 元素 | 動作 | 延遲 | 時長 |
| --- | --- | --- | --- | --- |
| 1 | 底圖 | `fade-in` ＋ `scale 1.06 → 1` | 0 | **1400ms**（比其他都慢，緩緩推近） |
| 2 | 遮罩漸層 | `fade-in` | 200 | 800 |
| 3 | 眉標 `WE ARE GETTING MARRIED` | `fade-up` | 500 | 700 |
| 4 | 英文姓名 | `fade-up` | 640 | 900（主角，慢一點） |
| 5 | 中文姓名 | `fade-up` | 780 | 700 |
| 6 | 飾線群組 | `line-grow` | 900 | 600 |
| 7 | 婚期 | `fade-up` | 1000 | 700 |
| 8 | 倒數四格 | `fade-up`，**四格再交錯 60ms** | 1120 | 700 |
| 9 | SCROLL 群組 | `fade-in` | 1500 | 700 |
| 10 | 音樂鈕 | `fade-in` ＋ `scale 0.8 → 1` | 1700 | 500 |

入場總長約 **2.4 秒**。⛔ 不要再拉長 —— 超過 3 秒賓客會以為頁面卡住。

#### 段 2 Gallery

| 順序 | 元素 | 動作 | 延遲 |
| --- | --- | --- | --- |
| 1 | 眉標 `GALLERY` | `fade-up` | 0 |
| 2 | 主標 `Our Moments` | `fade-up` | 90 |
| 3 | 金線 | `line-grow` | 180 |
| 4 | 金句 | `fade-up` | 270 |
| 5 | 相片 | `reveal-mask`，**桌機三張各交錯 140ms**；手機只揭主卡 | 400 |
| 6 | 頁點列 | `fade-in` | 700 |
| 7 | 操作提示 | `fade-in` | 790 |

#### 段 3 Info

| 順序 | 元素 | 動作 | 延遲 |
| --- | --- | --- | --- |
| 1 | 眉標 `INFORMATION` | `fade-up` | 0 |
| 2 | 主標 `Wedding Day` | `fade-up` | 90 |
| 3 | 主卡（整張一起） | `fade-up` | 220 |
| 4 | 卡內四條資訊列 | `fade-up`，**各交錯 90ms** | 400 |
| 5 | 地圖預覽 | `fade-in` | 760 |
| 6 | 導航鈕 | `fade-up` | 850 |
| 7 | 入場提醒 | `fade-in` | 940 |

⚠️ 桌機是左右分欄：**左卡與右欄同時觸發**，不要讓右欄等左卡整段播完（會顯得拖沓）。
右欄的地圖延遲 220、導航鈕 310。

#### 段 4 RSVP

| 順序 | 元素 | 動作 | 延遲 |
| --- | --- | --- | --- |
| 1 | 眉標 `R.S.V.P.` | `fade-up` | 0 |
| 2 | 主標 `Will You Join Us?` | `fade-up` | 90 |
| 3 | 說明文 | `fade-up` | 180 |
| 4 | 卡片 | `fade-up` | 300 |
| 5 | 七顆 chips | `fade-up`，**各交錯 50ms**（快一點，七顆用 90 太久） | 420 |
| 6 | 表單鈕 | `fade-up` ＋ `scale 0.96 → 1` | 780 |
| 7 | 註記／修改連結 | `fade-in` | 880 |

#### 段 5 Footer

| 順序 | 元素 | 動作 | 延遲 |
| --- | --- | --- | --- |
| 1 | `Thank You` | `fade-up`，時長 **1000ms**（收尾，最慢的一個） | 0 |
| 2 | 內文 | `fade-up` | 200 |
| 3 | monogram 圓環 | `fade-in` ＋ 圓環 `stroke-dashoffset` 描繪一圈 **1200ms** | 400 |
| 4 | 婚期 | `fade-in` | 700 |
| 5 | 版權 | `fade-in` | 800 |

### 10.5 視差（Parallax）

**只有 Hero 底圖做視差，其他一律不做。**

| 項目 | 規格 |
| --- | --- |
| 對象 | Hero 底圖（`裝置版-S1 Hero`／`電腦版-段1 Hero` 的底圖 rectangle） |
| 行為 | 頁面下捲時，底圖 `translateY = scrollY × 0.3`（＝比頁面慢，製造深度） |
| 上限 | 位移不超過 `120px`，超過就固定（避免圖底部露出空白） |
| 啟用條件 | **只在 ≥1024px 啟用。手機關閉** |

⛔ **手機為什麼關**：兩個原因，都不是效能潔癖 ——
(1) 行動裝置捲動時 `scroll` 事件節流不穩，視差容易抖動；
(2) 手機視野小，圖與文字的相對位移更容易誘發暈眩。

### 10.6 持續性動畫（不是進場，是一直在動的）

| 元素 | 動畫 | 規格 |
| --- | --- | --- |
| 音樂鈕（**播放中**態） | 唱片旋轉 | `rotate 0 → 360deg`，`8s`，`linear`，`infinite` |
| 音樂鈕（尚未播放／已靜音） | **不轉** | 靜止。⛔ 靜音了還在轉會讓人以為聲音還開著 |
| SCROLL 提示 | 上下浮動 | `translateY 0 → 6px → 0`，`2s`，`ease-in-out`，`infinite` |
| 倒數計時的秒數 | **不做任何動畫** | ⛔ 每秒閃一下會變成整頁最吵的東西，正好蓋掉「優雅」 |

### 10.7 `prefers-reduced-motion` 降級（⛔ 必做，不是加分項）

使用者在系統設定開了「減少動態效果」時：

| 原本 | 降級後 |
| --- | --- |
| `fade-up` | **只保留 `opacity 0 → 1`，時長縮到 `200ms`**，位移取消 |
| `reveal-mask` | 改為 `fade-in` `200ms` |
| `line-grow` | 直接顯示，無動畫 |
| Hero 入場序列 | 全部同時淡入，總長 `300ms`，不做交錯 |
| 視差 | **關閉** |
| 唱片旋轉 | **停止**，改為靜態 ＋ 金色外環表示播放中 |
| SCROLL 浮動 | **停止** |

實作方式：`@media (prefers-reduced-motion: reduce)` 一個區塊統一覆寫，
**不要在 TypeScript 裡逐個判斷** —— 漏一個沒有任何症狀，而受影響的正是對動態敏感的使用者。

### 10.8 效能鐵律

1. **只動 `transform`／`opacity`／`clip-path`。** ⛔ 禁止動 `height`／`top`／`margin`／`width` —— 那些會觸發 layout，整頁重排。
2. `will-change: transform, opacity` **只在元素即將進場時加上，播完就移除**。整頁常駐會吃掉大量記憶體。
3. 視差用 `requestAnimationFrame` 節流，**不要在 `scroll` handler 裡直接改樣式**。
4. Hero 底圖是 LCP 元素 —— **不可以 lazy load，要 preload**。入場的 `scale 1.06 → 1` 不影響 LCP 判定（transform 不算內容變化）。
5. 動畫一律走 CSS `transition`／`animation`，**不要引入動畫函式庫**（GSAP、Framer Motion 等）—— 這四種語彙 CSS 完全做得到，引函式庫只是多背一個相依。

### 10.9 這一節沒有回答的事（前端要自己決定的）

| 項目 | 說明 |
| --- | --- |
| 燈箱開闔動畫 | 建議遮罩 `fade-in 200ms` ＋ 大圖 `scale 0.96 → 1`，關閉反向。**但這是建議不是規格**，因為它屬於互動回饋不是進場動畫 |
| 場次膠囊切換 | 建議 `background-color` ＋ `color` `transition 200ms`。同上，屬互動回饋 |
| 按鈕 hover | 桌機 hover 用 `background-color` 加深 `200ms`。⛔ **不要用 `scale` 放大**（會推動周圍版面） |

---

## 11. 燈箱的換圖操作（第三輪修正）

> **起因**：使用者實測桌機版時發現 —— 首頁只露出 3 張照片，打開燈箱後
> 「只能用鍵盤左右移動切畫面才知道第 4 張、第 5 張」。

### 11.1 這是兩個缺陷疊在一起

| # | 缺陷 | 根源 |
| --- | --- | --- |
| 1 | 桌機首頁只露 3 張，賓客不知道還有 5 張 | §9.5.2 我只畫三張並排，而 `GALLERY_PHOTOS` 有 5 張。**更糟的是我還以「三張全看得見」為由拿掉了頁點列**，連「還有更多」的暗示都一併消滅 |
| 2 | 燈箱在桌機沒有可點的換圖控制 | 我當初指示「不加箭頭 icon 以維持視覺乾淨」。**那個判斷只在有滑動手勢的手機上成立** —— 桌機用滑鼠，只剩鍵盤方向鍵，而鍵盤操作沒有任何視覺提示，賓客猜不到 |

⛔ **教訓**：「維持視覺乾淨」不能凌駕「使用者找不到功能」。
一個沒有人發現得了的功能，等於不存在。

缺陷 1 的處置見 §9.5.2（已改為 3＋2 兩列，五張全露）。以下是缺陷 2。

### 11.2 燈箱必須有可見的換圖控制

| 項目 | 規格 |
| --- | --- |
| 左右箭頭鈕 | 44×44 圓形，半透明底 `#00000073`，內含 `chevron-left`／`chevron-right` icon 24，色 `$text-invert` |
| 位置 | 垂直置中，距畫面左／右各 16 |
| 桌機 | **必須顯示** |
| 手機 | **也顯示**（滑動手勢並非人人知道，且單手持握時點按比滑動穩） |
| 首張／末張 | 對應方向的箭頭 `opacity: 0.35` 且不可點（不要整顆消失 —— 消失會造成版面跳動，也讓人以為壞了） |
| 頁碼 | 維持底部置中 `3 / 5`，**這是「總共幾張」的唯一告知**，不可省略 |
| 觸控目標 | 至少 44×44（箭頭鈕本身即符合） |

### 11.3 鍵盤與手勢一併保留

新增箭頭鈕**不取代**既有操作，三種並存：

- 滑鼠：點箭頭鈕
- 鍵盤：左右方向鍵、`Esc` 關閉（既有，不動）
- 觸控：左右滑動（既有，不動）

### 11.4 無障礙

| 元素 | 要求 |
| --- | --- |
| 箭頭鈕 | `aria-label`：`上一張`／`下一張`；停用時 `aria-disabled="true"` |
| 頁碼 | `aria-live="polite"`，換圖時讓螢幕報讀軟體唸出「第幾張／共幾張」 |
| 焦點 | 箭頭鈕要在 focus trap 內，且有可見的 focus 樣式 |

⛔ **停用態不要用 `display:none`** —— 焦點順序會在首張與末張之間跳動，鍵盤使用者會迷路。

---

## 12. 桌機相簿：自動橫向捲動（第四輪）

> 取代 §9.5.2 原本的「三張並排」與第三輪一度採用的「3＋2 兩列」。
> **手機版不受影響**，維持 `scroll-snap` 輪播 ＋ 頁點列。

### 12.1 動作

| 項目 | 規格 |
| --- | --- |
| 方向 | 由右往左（照片自右側進入、向左移出） |
| 速度 | 約 **30px／秒**。一輪（5×360 ＋ 5×20 ＝ 1900px）約 63 秒 |
| 循環 | **無縫**。序列複製一份接在後面，`translateX` 位移滿一份寬度（1900px）即重置 |
| 卡片 | 360×480、radius 20、shadow —— 與原規格相同 |
| 容器 | **滿版 1440 出血**（不套 160 內距），`overflow: hidden` |
| 實作 | CSS `@keyframes` ＋ `transform: translateX()` |

⛔ **只動 `transform`。** 不要動 `left`／`margin`／`scrollLeft`，那些會觸發 layout 導致整頁重排。
⛔ **不要用 JS 每幀改位置。**

**為什麼要滿版出血**：照片若限制在 1120 的內容欄裡，會在畫面中間憑空出現與消失，
看起來像破圖而不是捲動。從畫面邊緣進出才有「延伸出去」的感覺。

### 12.2 速度為什麼訂這麼慢

30px／秒 ＝ 一張 360 寬的照片要 12 秒才完整通過。
這是刻意的 —— **捲動本身不是重點，照片才是**。
捲太快會讓人覺得被催促，與全站「克制、緩慢」的調性（§10）衝突。

實作後以實際觀感微調，但**不要超過 60px／秒**。

### 12.3 暫停機制（兩種，都必須有）

| 觸發 | 規格 |
| --- | --- |
| 滑鼠停留 | 游標進入相片區任一處即 `animation-play-state: paused`，離開恢復 |
| **鍵盤焦點** | 相片區內任一元素獲得焦點時同樣暫停（`:focus-within`） |

⚠️ **暫停要原地停住**，不是回到起點、也不是跳一下。

#### ⛔ 為什麼鍵盤焦點暫停是硬性要求，不是加分項

WCAG 2.2.2（Pause, Stop, Hide）規定：**任何自動移動超過 5 秒的內容，必須提供暫停機制。**

`hover` 只服務滑鼠使用者。鍵盤操作者與螢幕報讀軟體的使用者**停不下來**，
而移動中的內容對他們而言等於無法操作。

每張相片卡本身要能被 `Tab` 聚焦 —— 它本來就可點擊放大，本來就該是可聚焦的按鈕。

### 12.4 `prefers-reduced-motion`：改為靜態 3＋2 兩列

```
相片區 1120×980  layout=vertical gap 20  alignItems=center
├ 第一列 1120×480  gap 20  justifyContent=center  →  相片卡 ×3  360×480
└ 第二列  740×480  gap 20  justifyContent=center  →  相片卡 ×2  360×480
```

此情境下相片區改回內容欄寬 1120（不出血），段 2 高度約 1480。

⛔ **降級不能只是「停住不動」。**
停住的話賓客只看得到當下停在畫面上的那幾張，**其餘永遠看不到**。
必須換成一次能看完五張的靜態排列 —— 這是這條降級的整個重點。

### 12.5 點擊放大

- 點任一張相片卡 → 開燈箱，**從被點的那一張開始**（不是從第一張）
- ⚠️ **複製出來的第二份也要能點，且要對應正確的原始索引** ——
  點複製份的第 2 張要開原始的第 2 張，不是第 7 張
- 燈箱內的左右切換見 §11.2

### 12.6 這一節取代了什麼

| 輪次 | 桌機相簿版式 | 為什麼換掉 |
| --- | --- | --- |
| 第二輪 | 三張並排（靜態） | 只露 3 張，賓客不知道有 5 張（見 §11.1 缺陷 1） |
| 第三輪 | 3＋2 兩列（靜態） | 使用者提出自動捲動更能呈現照片，且不受張數限制 |
| **第四輪（現行）** | **自動橫向捲動** | — |

⚠️ 3＋2 的版式**沒有被廢棄**，它成為 `prefers-reduced-motion` 的降級版式（§12.4）。

**自動捲動的附帶好處**：照片張數變動時版面不會崩 ——
§4 的 Q4（相簿張數未定）在桌機這一側因此不再是阻礙，加到 12 張也只是循環變長。
手機版仍受頁點列數量限制，那一題對手機仍然成立。

---

## 13. 新人介紹區 About（第五輪追加）

> **這一段要解決什麼**：賓客名單裡有一半的人只認識新郎或只認識新娘。
> 目前的喜帖從 Hero 直接跳到婚紗照，看完仍不知道另一位是什麼樣的人。
> 這一段補上「兩位各自是誰」，讓賓客在看照片之前先認識人。

### 13.1 代號與插入位置

**代號 `S9 About`。** ⚠️ 代號數字與畫面順序不一致，這是刻意的：

- `S6`／`S7`／`S8` 已被音樂鈕狀態板、分享卡、桌機 Hero 佔用，那三個**不是頁面段落**
- 既有的 `S1`～`S5` 已寫進前端元件名、`.pen` 圖層名與本檔多處，重新編號的連帶修改遠大於收益

**畫面順序**：`S1 Hero` → **`S9 About`** → `S2 Gallery` → `S3 Info` → `S4 RSVP` → `S5 Footer`。

放在 Hero 之後、Gallery 之前的理由：**先認識人，再看照片。** 反過來的話，
賓客會先看完八張不知道是誰的婚紗照，介紹反而變成事後補充。

### 13.2 文案（逐字，繪製時照抄）

> ⚠️ **職業是新人提供的事實；性格描寫是撰稿推測**，見 §13.7 的待確認清單。

| 元素 | 逐字內容 |
| --- | --- |
| 眉標 | `ABOUT US` |
| 主標 | `The Two of Us` |
| 引言（手機兩行／桌機一行） | `在遇見彼此之前，`／`我們各自過著很不一樣的日子。` |
| 新郎・角色標籤 | `GROOM` |
| 新郎・姓名 | `洪承孝` |
| 新郎・職業 chip | `軟體工程師` |
| 新郎・描述 | `靠一行行程式碼過日子，習慣把複雜的問題拆開來、一個一個解決。話不多，但答應的事情一定做到。` |
| 新娘・角色標籤 | `BRIDE` |
| 新娘・姓名 | `李怡安` |
| 新娘・職業 chip | `服務業` |
| 新娘・描述 | `在餐飲業裡練就一身照顧人的本事，記得誰不吃什麼、誰想多要一點醬。她相信好好吃一頓飯，能讓人重新有力氣。` |
| 中央連結符號 | `&` |
| 收尾句（手機兩行／桌機一行） | `一個把日子過成邏輯，一個把日子過成溫度，`／`從 2026 . 12 . 12 起，我們一起過。` |

**字數紀律**：兩段描述都控制在 **42～48 字**，兩張卡的文字高度才會一致。
改文案時務必維持這個字數區間，否則兩張卡會不等高、中央的 `&` 會失去對稱。

### 13.3 版面骨架（手機 390×820）

底色 `$bg-blush`。夾在 S1（深色滿版圖）與 S2（`$bg-ivory`）之間，
三段依「深 → 粉 → 象牙」推進，段與段的邊界看得出來但不突兀。

```
S9 About 390×820   fill=$bg-blush  layout=vertical alignItems=center  pad [64,24]
├ 眉標 "ABOUT US"                     h=16
├ (spacer 10)
├ 主標 "The Two of Us"                h=41
├ (spacer 12)
├ 金線 40×1                            $gold-soft
├ (spacer 20)
├ 引言（寬 300，2 行）                  h=45
├ (spacer 36)
├ 人物卡-新郎 342×176                  ← 照片左・文字右
├ (spacer 20)
├ 中央連結列 342×12                     ← 線 100 ＋ "&" ＋ 線 100
├ (spacer 20)
├ 人物卡-新娘 342×176                  ← 文字左・照片右（與新郎鏡像）
├ (spacer 32)
└ 收尾句（寬 310，2 行）                h=39
```

內容實高 656 ＋ 上下 padding 128 ＝ **784**，段高取 **820**（底部餘白 36）。

#### 13.3.1 人物卡（342×176）

`layout=horizontal, gap=16, alignItems=start`

| 子元素 | 尺寸 | 說明 |
| --- | --- | --- |
| 照片 | 132×176，圓角 16 | 3:4 直式，陰影 `y=8 blur=28 $shadow-rose` |
| 文字欄 | 194×fit，`layout=vertical` | 342 − 132 − 16 = 194 |

文字欄內部（gap 0，用 spacer 控制）：

```
角色標籤 GROOM / BRIDE     h=14
(spacer 6)
姓名 洪承孝 / 李怡安        h=31    ← 與 chip 同屬一個 fit-content 容器
(spacer 6)
職業 chip                  h=26   圓角 13，padding [0,12]，fill=$bg-ivory，
                                  框線 1px $border-pill
(spacer 12)
描述文字（寬 194，4 行）     h=84   lineHeight 1.6
```

文字欄合計 177 ≈ 照片高 176，兩者視覺齊平。

⚠️ **姓名與職業 chip 靠同一側對齊，跟著整張卡的鏡像方向走**：

| | 對齊 | 貼齊的基準 |
| --- | --- | --- |
| 新郎卡 | 靠左 | chip 左緣 ＝ 姓名**第一個字**的左側 |
| 新娘卡 | 靠右 | chip 右緣 ＝ 姓名**最後一個字**的右側 |

兩者仍包在同一個容器裡（`flex-direction: column`），只是 `align-items`
依卡片方向取 `flex-start` 或 `flex-end`。

> ⚠️ **驗收要量「文字的墨水範圍」，不是元素盒子。** 姓名有 2px 字距，
> 元素盒子的邊緣不等於字的邊緣。用 `Range.selectNodeContents()` 取
> `getBoundingClientRect()` 才量得到真正的字緣 —— 實測手機與桌機、新郎與新娘
> 四種組合的差距皆為 0。
>
> ⛔ **不要「憑字距推算」再補負 margin**：本輪一度加了 `margin-right: -2px`
> 想補償尾部字距，實測反而超出 2px —— 該瀏覽器的墨水範圍本來就不含尾部字距。
> 先量，不要先算。

⚠️ **新娘卡是鏡像不是複製**：子元素順序改為「文字欄 → 照片」，
且文字欄內所有文字 `textAlign` 改為 `right`。角色標籤與 chip 也要靠右對齊
（`alignItems: flex-end`）。⛔ 不要只把照片搬到右邊卻留著左對齊的文字，
那會在版面正中央留下一條參差的邊。

#### 13.3.2 中央連結列（342×12）

`layout=horizontal, gap=8, justifyContent=center, alignItems=center`

| 子元素 | 尺寸 | 顏色 |
| --- | --- | --- |
| 線-左 | 100×1 | `$gold-soft` |
| 文字 `&` | fit | `$gold-soft`，20px／400／Great Vibes |
| 線-右 | 100×1 | `$gold-soft` |

這是 §9.0 ⑦ 裝飾元素清單的**第五種**，一併登記進去（原本四種：飾線、monogram 圓環、頁點、金色細線）。

### 13.4 版面骨架（桌機 1440×800）

底色同手機 `$bg-blush`。`pad [96,160]`，內容寬 1120。

```
S9 About 1440×772   layout=vertical alignItems=center  pad [96,160]
├ 眉標 "ABOUT US"                     h=18   （13px／600／字距 5）
├ (spacer 12)
├ 主標 "The Two of Us"                h=53   （44px Great Vibes）
├ (spacer 14)
├ 金線 64×1
├ (spacer 24)
├ 引言（單行，不斷行）                  h=28   （20px italic）
├ (spacer 56)
├ 兩人列 1120×300                      ← 見下表
├ (spacer 48)
└ 收尾句（單行，不斷行）                h=28
```

內容實高 **580** ＋ 上下 padding 192 ＝ **772**，段高即 **772**（無餘白，上下留白對稱各 96）。

> ⚠️ **修正紀錄**：本節初稿誤寫「內容實高 608、段高 800」——
> 骨架列逐項加總實際是 `18+12+53+14+1+24+28+56+300+48+28 = 582`，
> 且收尾句 17px 單行實高是 26 不是 28，故為 580。
> 段高若留在 800，上留白 96／下留白 124，整段會明顯偏上。**段高以 772 為準。**

#### 13.4.1 兩人列（1120×300）

`layout=horizontal, gap=0, alignItems=center`

| 子元素 | 寬 | 內容 |
| --- | --- | --- |
| 新郎欄 | 520 | 照片 220×300（圓角 20）＋ gap 24 ＋ 文字欄 276 |
| 中央分隔 | 80 | 垂直線 1×200（`$gold-soft`）上下各留 50，中央疊 `&` |
| 新娘欄 | 520 | 文字欄 276 ＋ gap 24 ＋ 照片 220×300（鏡像，文字右對齊） |

⚠️ **桌機照片與手機一樣要有陰影** `y=8 blur=28 $shadow-rose`（初稿漏寫，兩版必須一致）。

520 × 2 ＋ 80 ＝ 1120，與內容寬完全吻合。

桌機文字欄（276 寬）內部：

```
角色標籤        h=18   （12px／600／字距 3）
(spacer 8)
姓名           h=36   （26px／500／字距 2）
(spacer 8)
職業 chip      h=28   （13px／500）
(spacer 14)
描述（3 行）    h=78   （15px，lineHeight 1.7）
```

合計 189，垂直置中於 300 高的欄內（上下各餘 55.5）。

> ⚠️ **修正紀錄**：初稿寫「4 行 h=102」，實測 276 寬在 15px 下一行放得比預期多，
> 42～48 字的描述只排成 3 行。兩欄同樣是 3 行、等高，視覺無問題。

#### 13.4.2 中央分隔的 `&`

垂直線是**兩段**不是一段：上段 1×90、下段 1×90，中間留 120 給 `&`（28px Great Vibes `$gold-soft`）。
⛔ 不要畫成一整條線再把 `&` 疊上去 —— 線會從文字中間穿過去。

### 13.5 逐元素文字規格（併入 §9.2.2）

| 文字元素 | 字級 | 字重 | 字型 | 字距 | 顏色 |
| --- | --- | --- | --- | --- | --- |
| S9 眉標 `ABOUT US` | 11（桌機 **14**） | 600 | Cormorant Infant | 5（桌機 6） | `$accent-gold` |
| S9 主標 `The Two of Us` | 34（桌機 **56**） | 400 | Great Vibes | 0 | `$primary` |

⚠️ **S9／S10 的抬頭沿用全站 `section-heading` 的預設值（桌機 14／56／字距 6），⛔ 不另訂。**
初稿訂 13／44，實作後同一頁往下滑會看到主標從 44 跳到 56（Gallery／Info／RSVP 都是 56）——
**一段特例換來的是整頁的不一致**，不值得。
| S9 引言 | 16（桌機 20） | 400（italic） | Cormorant Infant | 0 | `$text-muted` |
| S9 角色標籤 `GROOM`／`BRIDE` | 10（桌機 12） | 600 | Cormorant Infant | 3 | `$accent-gold` |
| S9 姓名 | 22（桌機 26） | 500 | Cormorant Infant | 2 | `$text-main` |
| S9 職業 chip 文字 | 12（桌機 13） | 500 | Cormorant Infant | 0 | `$primary` |
| S9 描述 | 13（桌機 15） | 400 | Cormorant Infant | 0 | `$text-muted` |
| S9 中央 `&` | 20（桌機 28） | 400 | Great Vibes | 0 | `$gold-soft` |
| S9 收尾句 | 14（桌機 17） | 400（italic） | Cormorant Infant | 0 | `$text-muted` |

⚠️ 描述的 `lineHeight` 是 **1.6（桌機 1.7）**，不是全站慣用的 1.4 ——
這是本段唯一一處例外。理由：這兩段是全站最長的連續中文，1.4 在 13px 下會擠成一團。

### 13.6 動態規格（併入 §10）

#### 13.6.1 ⚠️ 這一段新增了第五種動畫語彙

§10.1 原本明訂「全站只有四種，不要再發明第五種」。本段**受控地新增第五種**，
並把適用範圍鎖死在 S9：

| 代號 | 動作 | 起始值 → 結束值 | 只用在哪 |
| --- | --- | --- | --- |
| `fade-side` | 淡入 ＋ 由外側向中央推 | `opacity 0 → 1`，新郎 `translateX -32px → 0`、新娘 `translateX +32px → 0` | **只有 S9 的兩張人物卡**。⛔ 其他段落一律不得使用 |

**為什麼非要第五種**：這一段的敘事是「兩個原本各過各的人，向中央的 `&` 靠攏」。
`fade-up`（由下往上）表達的是「浮現」，表達不出「從兩邊走向彼此」——
而這正是整段唯一想說的事。桌機位移量放大到 `48px`（同 §10.1 的桌機放大原則）。

#### 13.6.2 分鏡（段 1.5 About，捲動觸發）

觸發規則沿用 §10.3（`threshold 0.15`、`rootMargin 0 0 -10% 0`、只播一次）。

| 順序 | 元素 | 動作 | 延遲 | 時長 |
| --- | --- | --- | --- | --- |
| 1 | 眉標 `ABOUT US` | `fade-up` | 0 | 700 |
| 2 | 主標 `The Two of Us` | `fade-up` | 90 | 700 |
| 3 | 金線 | `line-grow` | 180 | 600 |
| 4 | 引言 | `fade-up` | 270 | 700 |
| 5 | **新郎照片** | `reveal-mask` | 420 | 900 |
| 6 | 新郎文字欄 | `fade-side`（左→右） | 520 | 700 |
| 7 | 中央連結列 | `line-grow` ＋ `&` 用 `fade-in` | 760 | 600 |
| 8 | **新娘照片** | `reveal-mask` | 860 | 900 |
| 9 | 新娘文字欄 | `fade-side`（右→左） | 960 | 700 |
| 10 | 收尾句 | `fade-up` | 1200 | 700 |

**節奏設計**：新郎（420ms）→ 中央 `&`（760ms）→ 新娘（860ms）是刻意的先後，
讓賓客的視線照「他 → 兩人 → 她」走一遍，而不是兩張卡同時冒出來。
整段約 **1.9 秒**跑完。

#### 13.6.3 `prefers-reduced-motion` 降級

依 §10.7，`fade-side` 與 `reveal-mask` 一律降為**無位移的純 `fade-in`（300ms）**，
交錯延遲全部歸零、同時顯示。⛔ 版面不需要改成別的排列（不像 §12.4 的相簿要換版式），
因為這一段靜止時本來就全部可見。

### 13.7 待確認（新的設計疑問）

| 編號 | 問題 | 現況 | 影響 |
| --- | --- | --- | --- |
| **Q9** | 兩段描述的**性格描寫是撰稿推測**，不是新人提供的事實 | 「話不多，但答應的事情一定做到」「記得誰不吃什麼」皆為推測 | ⛔ **上線前必須由新人確認或改寫**。喜帖是公開的，寫錯個性比空著更糟 |
| ~~**Q10**~~ | ~~兩位的單人照尚未提供~~ | ✅ **已解決** —— 新人已提供兩張單人照，見 §13.8 | — |
| **Q11** | 英文名 `Roger`／`Amy` 是否要出現在這一段 | 現行版面只放中文名 | Hero 已有 `Roger & Amy`，這裡重複可能冗贅；若要加，放在中文名下方 14px `$text-muted` |

**對應的 pen 節點 ID**（`pen-drawer` 第五輪回填，供 `design-question-curator` 釘紅框用）：

| 編號 | 手機 `k9CXWE` | 桌機 `tgAQJ` |
| --- | --- | --- |
| Q9（性格描寫為推測） | `Zxwyz`（描述-新郎）／`fNC1M`（描述-新娘） | `NqJZ6`（描述-新郎）／`WH1JL`（描述-新娘） |
| ~~Q10~~（單人照未提供，已解決） | `yqhn4`（照片-新郎）／`cGGmE`（照片-新娘） | `X4k7HR`（照片-新郎）／`EldLJ`（照片-新娘） |
| Q11（英文名是否加入） | 無對應元素（本稿未畫英文名；最接近的是 `K52AI`／`me6rS` 中文姓名） | 無對應元素（最接近的是 `DTOGp`／`Q5W16`） |

✅ Q9～Q11 已於第六輪由 `design-lead` 補進 §7.0 索引表，`design-question-curator` 取題不會漏。

### 13.8 圖片來源

⚠️ **設計稿與實作用的是不同來源，這不是矛盾**：

- **`.pen` 設計稿**：依 §9.0 ⑥ 一律 `Generate(id, "stock", prompt)`，⛔ 禁止手寫 url。
  設計稿的圖只是版式佔位，說明「這裡放一張 3:4 直式人像」。
- **前端實作**：用新人提供的真實單人照（下表），⛔ 不要去抓設計稿裡的 stock 圖網址。

| 節點 | 設計稿的 stock prompt |
| --- | --- |
| 新郎照片 | `asian man beige suit portrait outdoor` |
| 新娘照片 | `asian bride white gown portrait beach` |

> ⚠️ **prompt 已於第六輪改短**（原為 `portrait of an asian groom in a light beige suit, soft natural
> daylight, warm film tone, vertical 3:4` 與同格式的新娘版）。Unsplash 的 stock 查詢是**關鍵字比對**，
> 長句 prompt 的命中率低：初稿 prompt 抓到的四張裡有兩張不是人像（灰西裝全身橋景、塑膠紗布藝術照）。
> 短關鍵字重抓後四張都是單人像。⛔ **不要改回長 prompt。**
>
> ⚠️ **`Generate` 之後在同一次 `execute` 裡截圖會拍到空白**（實測兩次）。`Get` 讀得到 fill 的 url，
> 只是畫面還沒點陣化。分成兩次 `execute` 就正常。⛔ 不要把它當成生成失敗而重抓。

**第七輪：四張佔位圖已統一成同兩個人。** 桌機的兩張改成與手機同一張圖
（新郎 `X4k7HR`、新娘 `EldLJ`），理由是這份稿要手機／桌機並排給人看，
四個不同的人會被誤讀成「版式不一致」而不是佔位圖。

⚠️ **統一的作法是 `Copy` 手機的照片節點再刪掉原節點，不是複製 fill。**
第一次試的是 `Update(dst,{fill: 來源的fill, metadata: 來源的metadata})` ——
**`fill` 進去了，`metadata` 沒有**：呼叫回 OK、零警告，讀回來仍是舊值
（再試 `metadata:{}` 也一樣不動）。結果是節點掛著 A 的圖、B 的攝影師署名，
而**畫面上完全看不出來**。`metadata` 目前無法用 `Update` 寫入，要連署名一起搬就只能 `Copy` 節點。

> ⛔ **順帶留痕一個判讀錯誤**：`pen-drawer` 第五輪回報時說「桌機新郎那張是合照」，
> **那是誤判** —— 它是單人全身照，我把橋上的欄杆看成了第二個人。
> 起因是拿**整段的縮圖**在判斷單張照片的內容。
> **判讀圖片內容一律 `TakeScreenshot` 該張照片節點本身**，不要用整段截圖縮圖去看；
> 縮圖只能用來看版面有沒有破，看不出畫面裡有幾個人。
> （該張最後還是換掉了，但理由是「灰西裝全身橋景不符 §13.8.1 的米色西裝」，不是合照。）

#### 13.8.1 實作用的真實照片（新人提供）

| 用途 | 檔案 | 說明 |
| --- | --- | --- |
| 新郎 | `assets/images/groom.jpg` | 米色西裝、公園回眸，暖綠背景 |
| 新娘 | `assets/images/bride.jpg` | 白紗海邊夕陽、手持捧花回眸，粉調背景 |

兩張原始檔皆為 4480×6720（**2:3**，不是人物卡的 3:4），已**上下各裁 374px 置中**
後縮至 600×800 —— 置中裁而非從單邊裁，是因為單邊裁會把人物頭部推到畫面過上緣。
原始檔（`dobe-5329.jpg`／`dobe-5557.jpg`）逾 6MB，不進版控。

⚠️ **兩張的背景色調不同**（新郎偏綠、新娘偏粉）。並排時色溫不一致，
但兩張都是柔和暖調、且中間有金線分隔，實測可接受。若之後覺得突兀，
解法是統一套一層極淡的暖色濾鏡，⛔ 不要改成單色去背 —— 那會與全站的實景照調性衝突。

### 13.9 對既有畫布落點的影響

⚠️ **插入 S9 會把後續段落整段下推，長頁總高改變，輔助那一列必須跟著下移**，
否則會與長頁重疊。

| 節點 | 原 y／h | 新 y／h |
| --- | --- | --- |
| `裝置版-單頁全覽` | 0／3444 | 0／**4264**（＋820） |
| `電腦版-單頁全覽` | 0／**4012**（§9.5.3-A 表列 4020 有誤，實測 4012） | 0／**4784**（＋772）✅ 已實測 |
| 輔助那一列（燈箱／音樂鈕／LINE 卡／OG 圖） | y=4200 | y=**5000** |

手機長頁段落新落點（相對長頁）：

| 段 | y | h |
| --- | --- | --- |
| S1 Hero | 0 | 844 |
| **S9 About** | **844** | **820** |
| S2 Gallery | 1664 | 720 |
| S3 Info | 2384 | 900 |
| S4 RSVP | 3284 | 560 |
| S5 Footer | 3844 | 420 |
| **合計** | | **4264** |

桌機長頁段落新落點：

| 段 | y | h |
| --- | --- | --- |
| 段1 Hero | 0 | 900 |
| **段1.5 About** | **900** | **772** |
| 段2 Gallery | 1672 | 942 |
| 段3 Info | 2614 | 970 |
| 段4 RSVP | 3584 | 620 |
| 段5 Footer | 4204 | 580 |
| **合計** | | **4784** |

> 本表已於第六輪改為**畫布實測值**（`pen-drawer` 回填）。初稿表列的 Gallery 980／Info 940
> 是第二輪繪製前的估值，與實際繪出的 942／970 不同；段1.5 的 800 已依 §13.4 修正紀錄改為 772。

> 長頁是 `layout: vertical` 的自動排列，插入新 frame 後後續段落會自己往下推，
> **不需要逐段手動改 y**；要手動改的只有輔助那一列的頂層座標。

---

## 14. 交往故事書 Story（第七輪追加）

> **這一段要解決什麼**：S9 About 講的是「兩位各自是誰」，這一段講「他們怎麼走到一起」。
> 形式上刻意做成**可翻頁的紀念冊**，讓賓客用手把故事一頁一頁翻過去 ——
> 這是全站唯一需要賓客動手、而且動手才看得完的段落。

### 14.1 代號與插入位置

**代號 `S10 Story`。** 沿用 §13.1 的編號策略（代號數字 ≠ 畫面順序，理由同前）。

**畫面順序**：`S1 Hero` → `S9 About` → **`S10 Story`** → `S2 Gallery` → `S3 Info` → `S4 RSVP` → `S5 Footer`。

放在 About 之後、Gallery 之前的理由：**認識人 → 知道他們的故事 → 看婚紗照**，
情感是遞進的。故事若放在婚紗照之後，會變成看完美美的照片再回頭補敘述，節奏是斷的。

### 14.2 ⚠️ 這一段推翻了 §10.1 的一條禁令，這裡說明為什麼

§10.1 明訂「⛔ 沒有彈跳、沒有旋轉入場、**沒有翻牌**、沒有彩帶特效」。
翻頁在形式上就是翻牌，本段**明確地違反那一條**。這不是疏忽，是有條件的例外：

**那條禁令的對象是「進場動畫」——元素首次出現的方式。** 原文脈絡是
「動畫要像布幔被風掀起，不要像簡報換頁」，禁的是**自己動起來搶注意力**的入場特效。

**翻頁不是進場，是使用者主動操作的直接回饋。** 賓客按了「下一頁」，
畫面必須表現出「這一頁被翻過去了」，否則點擊與結果之間沒有因果感，
會變成「內容突然換掉」而不是「我翻了一頁」。而這一段的形式就是一本書 ——
書被翻開時本來就會翻頁。

**例外的界線（⛔ 三條都不得放寬）**：

1. **只在使用者點擊或按鍵時觸發**，⛔ 不得自動輪播、不得捲動觸發翻頁
2. **只有 `S10` 能用**，其他段落一律不得出現翻頁或任何 3D 旋轉
3. **`prefers-reduced-motion` 必須降級**（§14.7），3D 旋轉對前庭敏感的人是實質不適

### 14.3 版面骨架（手機 390×720）

底色 `$bg-ivory`。前一段 S9 是 `$bg-blush`，這裡回到象牙色做出區隔。

手機螢幕放不下雙頁，**一律單頁**：一次一張圖配一段故事。

```
S10 Story 390×808   fill=$bg-ivory  layout=vertical alignItems=center  pad [64,24]
├ 眉標 "OUR STORY"                    h=16
├ (spacer 10)
├ 主標 "How We Met"                   h=41
├ (spacer 12)
├ 金線 40×1                            $gold-soft
├ (spacer 20)
├ 書頁卡組 342×484                     ← 木色書皮 12 ＋ 內頁 318×460，見 §14.3.1
├ (spacer 20)
├ 控制列 204×40                         ← 翻頁鈕 ＋ 頁點 ＋ 翻頁鈕，見 §14.3.2
├ (spacer 20)
└ 操作提示 "點兩側箭頭翻頁"              h=16
```

逐項加總 `16+10+41+12+1+20+484+20+40+20+16 = 680`，＋上下 padding 128 ＝ **段高 808**（無餘白）。

⚠️ 808 仍在手機一屏（844）之內 —— 這是這一段高度的上限：翻頁書若一頁看不完、
還要捲動才讀得到文字，翻頁的意義就消失了。⛔ 加高任何元素前先確認總高不超過 844。

#### 14.3.1 書頁卡（342×414，含 12 書皮）

外圈 12px `$book-wood` 書皮，內頁 318×390（`fill=$surface`，圓角 8），
卡片外圓角 16，陰影 `y=10 blur=32 $shadow-rose`。內頁 `pad 20`（內容寬 **278**）。

⚠️ **第十一輪改動**：原本是「336 卡片 ＋ 右側 6 頁緣」，頁緣已廢止（§14.4.2 ③），
改為四邊 12 的木色書皮往內吃，卡片組總寬維持 **342** 不變、高度變為 **414**。

```
照片 278×278（圓角 12）      ← 1:1 正方形，理由見 §14.3.4
(spacer 18)
年份標籤 "2019 秋"           h=16
(spacer 8)
段落標題                     h=26
(spacer 8)
故事文字（寬 278，3 行）      h=66   lineHeight 1.7
```

內頁內容 420 ＋ padding 40 ＝ 460，＋ 書皮上下 24 ＝ 卡片組高 **484**。

⚠️ **278 寬一行約 21.4 字，3 行的上限降為 64 字**（原本 296 寬時是 66）——
字數紀律的上限跟著收為 **58～64**，見下方修正紀錄。

⚠️ **故事文字一律控制在 58～64 字（＝手機 3 行、桌機 3 行）。**
書頁高度固定是為了讓五頁翻起來版面不上下抽動，字數紀律就是維持它的手段。

> ⚠️ **第九輪收緊（原本 52～62）**：桌機右頁從 354 加寬到 404 之後，一行從 23.6 字變成
> **26.9 字**，52 字在桌機只排得出 **2 行**，書頁高度就會跳動 —— 正是這條紀律要防的事。
> 用程式跑過整個區間：**兩版都保證 3 行的範圍是 54～68 字**，取中段 **58～66** 留緩衝
> （54 字在桌機是 2.007 行，只差 0.007 就掉到 2 行，太危險）。

> ⚠️ **修正紀錄（第七輪繪製後）**：初稿寫「4 行 h=89、卡高 431」與「52～62 字」是**互相矛盾**的 ——
> 手機欄寬 302、字級 13，一行約放 23 個中文字，4 行需要約 **92 字**，52～62 字只排得出 3 行。
> `pen-drawer` 照初稿畫出來，卡片下緣空了 46px。
> **以字數紀律為準、行數與卡高跟著算**：3 行 h=66、卡高 408、段高 700。
> （這裡提到的 52～62 是**當時**的紀律值，第九輪桌機加寬後已再收緊為 **58～66**。）

#### 14.3.3 ⛔ 訂「字數 → 容器高」時，中間那一步一定要寫出來

本檔已經在**兩個不同段落**踩到同一個錯（§13.4.1 桌機描述 4 行 vs 實際 3 行、
§14.3.1 書頁卡 4 行 vs 實際 3 行）。兩次都是同一個原因：
**推導鏈中間的「一行放得下幾個字」沒有被寫下來，於是每次都用猜的。**

推導鏈是四步，⛔ 規格裡四步都要出現，不能只寫頭尾：

```
字數紀律  →  一行字數  →  行數  →  容器高
（訂的）    （算的←漏了）  （算的）  （訂的）
```

**中文一行字數的估法**：`欄寬 ÷ 字級 ≈ 一行字數`（中文是全形，一字約等於一個字級的寬）。

| 出現位置 | 欄寬 | 字級 | 一行字數 | 依據 |
| --- | --- | --- | --- | --- |
| S9 人物描述（手機） | 194 | 13 | ≈ 15 | 42～48 字 → **4 行**（48 ÷ 15 ＝ 3.2）|
| S9 人物描述（桌機） | 276 | 15 | ≈ 18 | 42～48 字 → 3 行 |
| S10 故事文字（手機） | 296 | 13 | ≈ 22.8 | 58～66 字 → 3 行 |
| S10 故事文字（桌機） | 404 | 15 | ≈ 26.9 | 58～66 字 → 3 行 |

行高換算：`行數 × 字級 × lineHeight`，四捨五入到整數。

⚠️ **這個估法只對純中文成立。** 夾雜英數字時一行放得下更多，實際行數會少於估值 ——
估出來的容器高只會偏大（留白多），不會爆版，所以偏保守是安全的方向。

⚠️ **固定高度的容器是刻意的選擇，不是偷懶。** 內容排不滿時，差額是一個確定的數字
（46px），不是「感覺有點空」—— 這讓錯誤可被計算、被回報。代價是必須把上面四步算對。

#### 14.3.4 照片框的比例：直式照片放橫式框會被裁掉一半

**症狀**：使用者回報「故事書的照片有截半的問題」。

**量測**（照片原圖 1000×1500，即 1:1.5 直式；`object-fit: cover`）：

| 框 | 比例 | 原圖看得到 | 垂直裁掉 |
| --- | --- | --- | --- |
| 手機初稿 278×208 | 1:0.75（橫式）| **50%** | **50%** |
| 手機現行 278×278 | 1:1（正方）| 67% | 33% |
| 桌機現行 440×508 | 1:1.15 | 77% | 23% |

初稿把手機的照片框訂成 4:3 橫式，而故事照多是直式 —— **正好裁掉一半**，
實際畫面上只看得到背景（樹、屋頂），人物全被切在框外。

**手機改為 1:1**。正方形是直式與橫式都吃得下的折衷；
再直一點（3:4）雖然裁切更少，但段高會超過手機一屏 844，翻頁書一頁看不完就失去意義。

⚠️ **桌機的 23% 沒有再改善的空間** —— 左頁的比例由書本高度（580）決定，
要讓框更直就得加高書本，而桌機段高已經 972、一屏是 900。

##### ⚠️ 換正式照片時的建議

這一段的照片框**接近正方形**（手機 1:1、桌機 1:1.15）。
挑照片時**優先選橫式或正方構圖**，主體置中；直式人像照放進來一定會裁掉上下。
⛔ 不要改用 `object-fit: contain` 來閃避 —— 直式照片放進正方框會左右留白，
書頁會出現兩條空白邊，比裁切更難看。

#### 14.3.2 控制列（204×40，⛔ 翻頁鈕不得疊在照片上）

> ⚠️ **第九輪改寫。** 初稿把翻頁鈕疊在照片左右兩側 —— 實際看是**擋住照片**，
> 而照片是這一段的主體。已改為把鈕移到書頁卡**下方**，與頁點列同一排。

手機 390 寬扣掉書頁卡 342，左右只剩各 24，**放不下卡片兩側的按鈕**。
硬要放就得把書頁縮到 286 以下，照片與文字都會跟著縮水，代價比收益大。
所以改成把「左 → 頁點 → 右」放在同一列：既沒有蓋住照片，也保留了「左右翻頁」的語意。

```
┌──────────────────┐
│                  │
│     書 頁 卡      │
│                  │
└──────────────────┘
   ◀   ● ○ ○ ○ ○   ▶
```

`layout=horizontal, gap=24, justifyContent=center, alignItems=center`

| 子元素 | 尺寸 | 說明 |
| --- | --- | --- |
| 翻頁鈕-左 | 40×40 圓角 20 | `fill=$surface`，陰影 `y=4 blur=16 $shadow-rose`，內含 16px `chevron-left`（`$text-main`）|
| 頁點列 | 76×8 | 5 顆，作法同 §9.2.1 的 S2 頁點（active 20×8 圓角 4 `$primary`，其餘 8×8 圓 `$border-pill`，gap 6）|
| 翻頁鈕-右 | 40×40 | 同左，`chevron-right` |

橫向加總 `40+24+76+24+40 = 204`，落在書頁卡寬 336 之內、置中。

**照片本身也是翻頁觸控區**：點照片左半往前翻、右半往後翻。
這是**前端行為，設計稿不畫任何節點** —— 手機上大目標比小按鈕好按，
但畫成透明矩形只會讓看稿的人以為那裡有東西。
⛔ 故事書的照片**不開燈箱**（與 S2 相簿不同），所以點擊不會有其他語意衝突。

**鈕底改用 `$surface`（純白）不再是半透明** —— 鈕已經離開照片、落在 `$bg-ivory` 底上，
半透明白在淺色底上會糊掉；改純白加陰影才浮得起來。

⛔ **首頁的「上一頁」與末頁的「下一頁」是停用態**，不循環回頭。
理由同 §11 燈箱：邊界要看得出來，賓客才知道故事翻完了。

**停用態的畫法**：⛔ **不要對整顆鈕套 `opacity`**，改成**鈕底維持不變、只讓箭頭本身變淡**
（icon 改 `$text-muted` 且 `opacity 0.4`）。整顆變淡會讓鈕在某些背景上直接消失，
「讓賓客看出邊界」的目的反而落空 —— 這是初稿把鈕疊在深色照片上時實測到的（70% 白乘 0.3 只剩 21%）。

### 14.4 版面骨架（桌機 1440×972）

底色同手機 `$bg-ivory`。`pad [96,120]`，內容寬 1200。

桌機做**雙頁展開**：左頁照片、右頁文字、中央書脊。

```
S10 Story 1440×972   layout=vertical alignItems=center  pad [96,120]
├ 眉標 "OUR STORY"                    h=18   （13px／600／字距 5）
├ (spacer 12)
├ 主標 "How We Met"                   h=53   （44px Great Vibes）
├ (spacer 14)
├ 金線 64×1
├ (spacer 24)
├ 書本列 1192×580                      ← 見 §14.4.1
├ (spacer 29)
├ 頁點列 h=10
├ (spacer 18)
└ 操作提示 "點兩側箭頭翻頁"             h=21   （15px）
```

逐項加總 `18+12+53+14+1+24+580+29+10+18+21 = 780`，＋上下 padding 192 ＝ **段高 972**（無餘白）。

> ⚠️ **第九輪加寬。** 初稿書本 900×520 在 1440 的畫面上偏小，書本兩側各有一大片空白。
> 左右 padding 由 160 縮到 **120**（內容寬 1120 → 1200），書本放大到 **1000×580**（面積增加 24%）。
> 這是這一段的主體，值得把版面讓給它。

#### 14.4.1 書本列（1192×580）

`layout=horizontal, gap=0, alignItems=center, justifyContent=center`

| 子元素 | 寬 | 說明 |
| --- | --- | --- |
| 翻頁鈕-左 | 56 | 56×56 圓，`fill=$surface`，陰影 `y=4 blur=16 $shadow-rose`，內含 20px `chevron-left` |
| （間隔） | 40 | |
| 書本 | 1000 | 木色書皮 12 ＋ 左頁 488 ＋ 右頁 488，見 §14.4.2 ① |
| （間隔） | 40 | |
| 翻頁鈕-右 | 56 | 同左，`chevron-right` |

**桌機的翻頁鈕一樣有停用態**，畫法同 §14.3.2（只讓 icon 變淡，不對整顆鈕套 `opacity`）——
邊界表現是元件層級的規則，兩版一致。

**桌機頁點列**：列高 10，顆粒比手機放大 —— active 為 `25×10` 圓角 5（`$primary`），
其餘 4 顆為 `10×10` 圓（`$border-pill`）。⛔ 不要沿用手機的 20×8／8×8，
那會填不滿 10 的列高，且桌機視野下顆粒過小。

**手機與桌機的操作提示都是「點兩側箭頭翻頁」。**

> ⚠️ **第十四輪統一**：本節原本寫「桌機用『點兩側箭頭翻頁』，手機用『點左右兩側翻頁』」，
> 但 §14.3.2 在第九輪已把手機的鈕從照片兩側移到卡片下方 —— 手機也是按箭頭，
> 「點左右兩側」那句已經不準。兩版統一用同一句。

橫向加總 `56+40+1000+40+56 = 1192`，落在內容寬 1200 之內（左右各餘 4）。

**書本（1000×580）**：外圈 12px `$book-wood` 書皮 ＋ 內頁 976×556（`fill=$surface`，圓角 8），
書本外圓角 20，陰影 `y=16 blur=48 $shadow-rose`。詳見 §14.4.2 ①。

| 頁 | 寬 | 內容 |
| --- | --- | --- |
| 左頁 | 488 | `pad 24`，內含照片 **440×508**（圓角 12），四周留白 24 |
| 右頁 | 488 | `padding [24,48,48,48]`（內容寬 **392**），文字**靠上對齊**，底部另有頁碼 |

⚠️ **單頁從 500 縮為 488** —— 書皮往內吃掉 12×2，書本總寬維持 1000 不變。

**書脊**：見 §14.4.2 —— 第九輪已從「一條 1px 細線」改為「細線 ＋ 兩側凹陷陰影」。

#### 14.4.2 ⛔ 書的造型：三個讓它像書而不是白卡片的元素

> **第九輪追加。** 初稿的「書」實際上只是一張白底圓角矩形加一條中線 ——
> 少了實體書最關鍵的三個視覺線索。這一節把它們補上。
> 判準很簡單：**遮住文字之後，這個形狀還看得出是一本攤開的書嗎？**

##### ① 木色書皮（第十一輪追加）

> ⚠️ **這一項推翻了本節原本的禁令。** 初稿寫「⛔ 不要加深色硬殼書皮邊框，
> 全站是粉白金淺色調，深色框會突兀」—— 那個判斷下得太早：只顧著配色和諧，
> 沒顧到更基本的「書要看得出是一本書」。
> 實際畫出來後，**白色書本（`#FFFFFF`）落在象牙色背景（`#FFFBF7`）上幾乎融為一體**，
> 只靠陰影撐分離。木色與現有的金色（`#CA8A04`／`#E7C873`）同屬暖色家族，不會打架。

書本外圈一圈 **12px 的實心 `$book-wood`（`#A67C52`）**，像精裝相本的硬殼包著內頁。

| 項目 | 值 |
| --- | --- |
| 書皮寬度 | 12（四邊等寬）|
| 書皮顏色 | `$book-wood` `#A67C52` |
| 書本外圓角 | 20（不變）|
| 內頁圓角 | 8（比外圓角小，才像被包在裡面）|

⚠️ **書皮往內吃，書本總尺寸不變** —— 桌機仍是 1000×580、手機卡組仍是 342。
⛔ 不要往外擴：桌機書本列只剩 8px 餘裕，外擴會爆版。

##### ①-A 書皮要有立體感（第十三輪改寫）

> ⚠️ **第十二輪的做法是錯的，這一節整段重寫。**
> 當時的規格是「整個木框套一個上亮下暗的漸層」——
> 使用者實看後的回饋是「**邊框還是平面的感覺**」，而且 `pen-drawer` 早就回報過徵兆：
> 「桌機比手機弱，因為同樣的漸層攤在 12px 寬的框上、桌機高 580，變化較平緩」。
>
> **問題不在寬度，在手法。** 一個框之所以看起來立體，靠的是**四條邊各自不同的明暗**，
> 不是整個框一個漸層。早期軟體的按鈕邊框只有 2px，靠左上亮、右下暗就有明顯浮凸感。
> 整框同色的漸層，讀起來就是「一張貼上去的色紙」。

**統一假設光從正上方偏左來。** 四邊分色，明暗差要看得出來：

| 邊 | 顏色 | 為什麼 |
| --- | --- | --- |
| **上邊** | `#BD9B79` | 朝上，正對光源，最亮 |
| **左邊** | `#B18961` | 側面偏受光 |
| **右邊** | `#956F4A` | 側面背光 |
| **下邊** | `#7D5D3E` | 朝下，完全背光，最暗 |

基色仍是 `#A67C52`（`$book-wood`），四個值是它的明度 ±12%／±5%。

**實作結構**：⛔ 書皮不再是「一個 frame 塗一個漸層」，改為**四個獨立矩形**拼成的框
（角落歸上下邊所有，桌機以 1000×580 為例）：

| 節點 | x | y | w | h |
| --- | --- | --- | --- | --- |
| 書皮-上 | 0 | 0 | 1000 | 12 |
| 書皮-下 | 0 | 568 | 1000 | 12 |
| 書皮-左 | 0 | 12 | 12 | 556 |
| 書皮-右 | 988 | 12 | 12 | 556 |

手機（342×414）同樣四條：上 `0,0,342,12`／下 `0,402,342,12`／左 `0,12,12,390`／右 `330,12,12,390`。

⚠️ **書本 frame 本身的 fill 要拿掉**（原本是漸層），改由這四條邊構成書皮，
中間留給內頁。書本外圓角 20 仍保留在書本 frame 上。

> ✅ **實作註記（第十三輪繪製）**
>
> 1. **清除 fill 用 `fill: []`**（同 `stroke: []` 的作法），⛔ 不要傳 `null` —— 會整批回滾。
> 2. **書本 frame 一定要 `clip: true`**：四條邊是方角矩形，沒有 clip 會戳出外圓角 20 之外。
>    桌機本來就有，**手機 `shoHW` 是這輪才補上的**。
> 3. ⛔ **這十個矩形踩到算圖 stale，一定要用 `Copy` 的方式建**（見 ①-B 下方那則的同類問題）：
>    直接 `Insert` 進書本 frame 的話，`Get` 讀得到、raw 屬性全對，**但畫面上整個書皮不見**
>    （書本變成沒有邊框的白塊）。實測 `Move` 觸發重繪**無效**；
>    有效的是 `pen-authoring` §10 第 4 階 —— **根層建暫存 frame ＋ 素材 → `Copy` 進目標 → 刪暫存**。
>    ⚠️ 因為要 `Copy`，這批節點的 ID 與第一次 `Insert` 時不同，§8 記的是 `Copy` 之後的 ID。

##### ①-A2 再加兩道，立體感才完整

| # | 手法 | 規格 | 作用 |
| --- | --- | --- | --- |
| 5 | **外緣高光** | 書本 frame `stroke 1px #CAAF94`，`strokeAlignment: inner`（原為 `#D4B48C`，改亮一階）| 框的最外緣一線反光 |
| 6 | **內緣反光** | 內頁**下緣**一條 1px `#FFFFFF66`，左右各內縮 8 | 凹陷處底部的反射光 |

加上原有的**內緣上方暗線**（2px `#00000020`，左右各內縮 8），內緣就形成
「上暗下亮」——**與外框的「上亮下暗」剛好相反**，這正是「凹進去」的視覺定義。

⛔ **兩者的方向絕對不能一致**：外框上亮下暗＝凸起，內緣上暗下亮＝凹陷。
方向做反或做成一樣，立體感會直接抵消掉。

⚠️ **手機六項全做，數值與桌機完全一致，⛔ 不要按比例縮小** ——
光影的厚度感不隨尺寸縮放，縮小後只會全部消失。

##### ①-A3 若這樣還是平

先**加寬書皮 12 → 16**（四邊分色的效果會更明顯），再檢討其他。
⚠️ 加寬會連動：手機內容寬 278 → 270，一行 20.8 字，**字數上限從 64 降為 62**。
⛔ 不要用「提高明暗差」來救 —— 對比再拉大就會變成四條顏色不同的色塊，
而不是一個有厚度的框。

##### ①-B ⛔ 立體感不要做過頭

| ⛔ 不要做 | 為什麼 |
| --- | --- |
| 木紋貼圖或材質紋理 | 全站沒有任何材質貼圖，一塊木紋會變成整頁最搶眼的東西 |
| 四角加金屬包角 | 那是古董書的語彙，與粉白金的婚禮調性不合 |
| 書本整體傾斜或旋轉 | 這一段還要疊翻頁動畫，靜態就傾斜會讓翻頁的軸心很難理解 |
| 多層堆疊模擬「好幾本書」 | 這是一本紀念冊，不是書堆 |

> ⚠️ **實作註記（第十一輪繪製）：⛔ 不要為白色內頁另外包一層 frame。**
> 直覺的畫法是「書皮 frame → 內頁 frame（976×556 白底圓角 8）→ 左頁＋右頁」，
> 實測**那層新建的內頁 frame 會發生算圖 stale**：它自己的白底畫得出來，
> **但它的子節點一個都沒有被合成** —— 而同樣那些子節點單獨截圖全都正常。
> 重複截圖結果一致（不是快照過期），`Get` 讀得到、bounds 也正確。
>
> **改用的作法**：白色內頁由**左頁與右頁各自的 `$surface` 底色 ＋ 半邊圓角**拼成
> （左 `[8,0,0,8]`、右 `[0,8,8,0]`），兩頁直接放在書皮 frame 裡。視覺完全相同、少一層節點。
> 手機因為只有一頁，一層內頁 frame 就夠（`RK3GT` 是既有節點、非新建，沒有這個問題）。
>
> ⚠️ **判準**：`Get` 讀得到 ≠ 畫得出來。新增容器層之後**一定要截圖看**，
> 不能只看 bounds 與節點清單 —— 那三項在這個失敗模式下全部是綠的。

⚠️ **書皮取代了原本的「頁緣厚度」三條線**（見下方 ② 的修正紀錄）。

##### ② 書脊凹陷（⛔ 最關鍵，沒有這個就不是書）

> ✅ **實作註記（第九輪繪製）**：漸層的方向參數是 **`rotation: 270`**（pen 的角度是逆時針、
> `0°` 朝上，所以 `270°` ＝ 由左至右）。已用「暫時把 alpha 拉到 `FF` 再截圖」的方式驗證過方向正確：
> 中央最暗、往兩側淡出。⛔ 不要照抄本檔既有的 `rotation: 180` —— 那是**由上至下**，
> 用在這裡會變成上暗下亮的橫向漸層（§9.1 把 S8 那顆註記為「左→右」是錯的，該節點實際是上→下）。

真實的書攤開時，紙張向書縫彎曲，**靠近書脊的地方會暗下去**。這是大腦判斷「這是一本書」最主要的線索，比任何邊框都有效。

| 元素 | 規格 |
| --- | --- |
| 左側暗部 | **56×556**，`y=12`，貼齊左頁右緣。線性漸層（左→右）`#83184300` → `#83184326` |
| 中央線 | **1×556**，`y=12`，`$border-soft`，位於書本正中央 |
| 右側暗部 | **56×556**，`y=12`，貼齊右頁左緣。線性漸層（左→右）`#83184326` → `#83184300` |

⚠️ **高度是 556 不是 580、起點 y=12** —— 書脊必須**貼齊內頁範圍**，
⛔ 不可以從 y=0 畫滿 580，那會讓書縫爬到上下的木色書皮上。
書縫是紙張彎曲造成的，硬殼不會凹。（手機是單頁，不做書脊。）

`#831843` 是 `$text-main`，`26` ＝ 15% alpha。**15% 是上限，⛔ 不要再調深** ——
超過就會變成「兩頁中間有一條黑帶」，而不是「紙張彎進去」。

##### ⚠️ 漸層方向是 `rotation: 270`，不是 180

pen 的漸層角度是**逆時針、`0°` 朝上**，所以「由左至右」是 **`270`**。
本檔既有的三顆漸層（S1／S4／S8）都是 `rotation: 180`（＝由上至下），
**照抄的話書脊會變成上暗下亮的橫向漸層 —— 而且不會報錯，只會安靜地畫錯。**

驗證低對比漸層方向的手法：**把 alpha 暫時拉到 `FF` 截圖看方向，確認後再還原**。
15% 的漸層在縮圖上幾乎看不見，肉眼無法確認方向對不對。

##### ⚠️ 這組值的由來與調整方向（第九輪實測）

初稿訂 32 寬／10%，`pen-drawer` 實測「看不出有凹陷」——
10% 的 `#831843` 疊在白底上最暗處是 `rgb(243,232,236)`，對純白只差約 5～8% 亮度，
而且這個差值還被攤在 32px 上慢慢變化。

**要加強時優先加寬，不要先加深** —— 兩個參數的失敗模式不同：

| 調整 | 效果 | 風險 |
| --- | --- | --- |
| 提高 alpha | 最暗點更暗 | ⚠️ 這才是變成「黑帶」的原因，15% 的上限要守住 |
| 加寬 | 暗的範圍變大、最暗點不變 | 幾乎沒有風險 —— 只會讓彎曲看起來更緩、更像厚紙 |

真書的書縫陰影本來就是**寬而淺**的，不是窄而深的。不夠明顯時可再加寬到 56。

##### ~~③ 頁緣厚度~~（第十一輪廢止）

> ⛔ **這一項已刪除。** 原本在書本左右外側各疊三條淺粉細線模擬紙緣，
> 加了木色書皮之後它的功能被完全取代 —— 而且淺粉細線疊在木色外緣會很怪。
>
> **連帶回復的兩件事**：
> 1. `書本組` 那一層外包 frame 不再需要，書本直接就是 1000×580
> 2. 書本列的間隔從 36 **改回 40**：`56+40+1000+40+56 = 1192`，仍在內容寬 1200 內
>
> 手機的右側頁緣 6 也一併移除，書頁卡組回到單層 342 寬。

##### ③ 落在桌面的陰影

書本陰影從 `y=12 blur=40` 加重為 **`y=16 blur=48`**（`$shadow-rose`）。
書比卡片厚，陰影要更沉一點才有重量感。

##### 手機版的書感（單頁也要看得出是書）

手機是單頁，靠**木色書皮**做出「這是一本書」，現行值：

- 卡片組 **342×414**：木色書皮 12（四邊）＋ 內頁 318×390（`$surface`，圓角 8）
- 照片 **278×208**（4:3），故事文字寬 278
- 卡片外圓角 16，陰影 `y=10 blur=32 $shadow-rose`
- 立體感六項（四邊分色／外緣高光／內緣上暗線／內緣下亮線／投影）**與桌機數值完全一致**，見 §14.4.2 ①-A

⛔ **手機不要做書脊凹陷** —— 單頁沒有書縫，硬加會變成一條沒有來由的暗帶。

> ⚠️ **第十一輪改寫**：原本是「書頁卡 336 ＋ 右側頁緣 6 三條線」，
> 頁緣已隨 ③ 一併廢止，改由木色書皮承擔邊界與厚度感。

##### ⛔ 不要做的兩件事

1. **不要畫翻頁的捲角（page curl）。** 靜態設計稿上的捲角是假的動作，看久了只覺得那一角破了。
2. **不要用書本插圖或裝飾花邊。** §9.0 ⑦ 的裝飾元素清單是封閉的，書的造型靠上面幾個結構元素就夠。

> ⚠️ **原本的第 1 條「不要加深色硬殼書皮邊框」已於第十一輪整條刪除** ——
> 它被 §14.4.2 ① 推翻了（白書配象牙底幾乎融為一體，木色書皮是解法不是禁忌）。
> ⛔ 不要因為在別處看到那句話就把書皮擋掉。
> 立體感做過頭的禁令另見 §14.4.2 ①-B。

> ⚠️ **修正紀錄（第七輪繪製後）**：初稿是「左頁照片滿版、只有左側倒角」，
> 實際畫出來**書脊完全看不見** —— 左頁滿版深色照片與右頁白底的交界本身就是一條強烈分界，
> 1px 的 `$border-soft`（`#F0D9E2`）壓在上面被吃掉，反而真的把書切成了兩張卡片。
> 改為**左頁照片四周留白 24**：書脊兩側都是白色，細線才有對比可言，
> 而且有白邊的頁面本來就更像實體相冊。

右頁文字（404 寬，垂直置中於 484 高的內容區）：

```
年份標籤        h=20   （14px／600／字距 3）
(spacer 10)
段落標題        h=39   （28px／500／字距 1）
(spacer 14)
故事文字（3 行） h=92   （17px，lineHeight 1.8）
```

合計 175，**靠上對齊**。

⚠️ **右頁上內距是 24 不是 48**（`padding [24,48,48,48]`）——
左頁照片是 `pad 24`、頂端落在 y=36；右頁若四邊都用 48，文字頂端會落在 y=60，**比照片低 24**。
上內距改 24 才真的齊平，而左右內距維持 48，內容寬仍是 392，行數不受影響。

> ⚠️ **第十一輪改為靠上（原本垂直置中）＋ 字級加大。**
> 匯出 png 實看後發現右頁「很空」—— 不是留白多，是**文字浮在正中間一小塊**，
> 上下各一大片白，看起來像沒排滿而不是刻意的留白。
> 真書的一頁文字是**從頂端排下來**的，留白自然落在下方。
> 字級同時從 15／24／13 加大到 **17／28／14**（1440 螢幕上 15px 偏小），
> 392 寬在 17px 下一行 23.1 字，58～64 字仍是 3 行。

**右頁底部另有頁碼**：靠右下，距右緣 48、距底 32，內容為兩位數頁碼（第 1 頁是 `01`）。
14px／400／字距 2／`$text-muted`。這是真書都有的元素，同時讓下方的留白有個視覺錨點，
不再是一片無所依附的白。⛔ 不要做成「1 / 5」——書的頁碼不寫總頁數。

> ⚠️ 初稿的「5 行 h=128」同樣是誤算（桌機欄寬 354、字級 15，一行約 23.6 字，
> 當時的 52～62 字排成 3 行；第九輪加寬到 404 後已改為 58～66）。桌機右頁是**垂直置中**的，字少只是留白多一點、視覺仍平衡，
> 所以桌機沒有手機那個空洞問題 —— 但數字仍須修正以免下游照著做。

### 14.5 示範文案（⚠️ 全部是虛構的，上線前必須整批替換）

> ⛔ **這五段故事沒有一句是真的。** 新人尚未提供交往經過，這裡是為了把版面做出來
> 而寫的示範文案。細節（季節、地點、對話、養貓、搬家）全是編的。見 §14.8 的 Q12。

| 頁 | 年份標籤 | 段落標題 | 故事文字 |
| --- | --- | --- | --- |
| 1 | `2019 10月` | `初次見面` | `那年秋天，在朋友的一場聚會上第一次見到彼此。那天散場之後才發現，我們是聊到最後才離開的兩個人，連要回家的方向都一樣。` |
| 2 | `2020 3月` | `熟悉起來` | `開始習慣生活裡有對方的日常。她下班傳訊息說今天很累，他就把宵夜送到樓下，說剛好順路——其實那天他整整繞了半座城市才到。` |
| 3 | `2020 7月` | `在一起` | `其實那天沒有誰正式開口說什麼。只是某一天散步回家的路上，牽起來的手就沒有再放開；後來想想，那條路我們一走就走了好多年。` |
| 4 | `2021 – 2025` | `一起走過的日子` | `我們一起搬過三次家，一起吵過架也一起道過歉。日子說不上轟轟烈烈，但每一天都比前一天更確定一點，確定要一直這樣走下去。` |
| 5 | `2026 3月` | `他問，她說好` | `就在第一次見面的那家店門口，他單膝跪下。她一邊哭一邊點頭，然後說了一句：你怎麼這麼慢。那天整間店的人全都站起來鼓掌。` |

**字數紀律**：每段 **58～64 字**（手機 3 行、桌機 3 行）。五頁現為 58～59 字，皆以程式驗過行數。

> ⚠️ **第十一輪上限再收（原本 58～66）**：手機加木色書皮後內容寬從 296 縮為 278，
> 一行從 22.8 字變成 21.4 字，**65 字以上會排成 4 行**、撐爆固定卡高。
> 現有五頁 58～59 字仍安全，但改文案時上限是 **64**。
改文案時務必維持這個區間，否則書頁高度會跳動、翻頁時版面上下抽動。

> ⚠️ **第七輪把五段都補長了。** 初稿最短的一段只有 44 字（第 1 頁），
> 在固定高度的書頁卡裡只排 2 行，卡片下緣會空一大塊。示範文案本身雖然要換掉，
> 但**設計稿必須呈現真實文案的長度**，否則使用者看到的版面留白是假的。

### 14.6 逐元素文字規格（併入 §9.2.2）

| 文字元素 | 字級 | 字重 | 字型 | 字距 | 顏色 |
| --- | --- | --- | --- | --- | --- |
| S10 眉標 `OUR STORY` | 11（桌機 **14**） | 600 | Cormorant Infant | 5（桌機 6） | `$accent-gold` |
| S10 主標 `How We Met` | 34（桌機 **56**） | 400 | Great Vibes | 0 | `$primary` |
| S10 年份標籤 | 11（桌機 **14**） | 600 | Cormorant Infant | 3 | `$accent-gold` |
| S10 段落標題 | 18（桌機 **28**） | 500 | Cormorant Infant | 0（桌機 1） | `$text-main` |
| S10 故事文字 | 13（桌機 **17**） | 400 | Cormorant Infant | 0 | `$text-muted` |
| S10 頁碼（桌機專用） | — （桌機 14） | 400 | Cormorant Infant | 2 | `$text-muted` |
| S10 操作提示 | 11（桌機 15） | 400 | Cormorant Infant | 1 | `$text-muted` |

故事文字 `lineHeight`：**手機 1.7、桌機 1.8**（同 §13.5 的理由，長段中文用 1.4 會擠）。

> ⚠️ **第十四輪釐清**：§14.6 原本只寫 1.7，但 §14.4 骨架的 `h=92` 是用 1.8 算的
> （17 × 1.8 × 3 ＝ 91.8）。兩者不可能同時成立 —— **以骨架高度為準**，
> 因為那是容器尺寸的來源；桌機 1.8、手機維持 1.7（手機 h=66 ＝ 13 × 1.7 × 3）。

### 14.7 動態規格（併入 §10）

#### 14.7.1 第六種動畫語彙 `page-turn`

| 代號 | 動作 | 值 | 只用在哪 |
| --- | --- | --- | --- |
| `page-turn` | 頁面沿書脊翻過去 | 見下表 | **只有 S10 的翻頁**。⛔ 其他段落不得使用 |

| 裝置 | 作法 |
| --- | --- |
| 桌機 | 容器 `perspective: 2000px`。右頁 `transform-origin: left center`，`rotateY(0) → -180deg`；翻頁過程中新頁在下層等待。往回翻則是左頁 `transform-origin: right center`，`rotateY(0) → 180deg` |
| 手機 | 沒有書脊，改為整頁替換：舊頁 `transform-origin: left center` 從 `rotateY(0)` 轉到 `-90deg` 並淡出，新頁同時從 `rotateY(90deg)` 轉回 `0`。容器 `perspective: 1200px` |

- **時長 900ms**，緩動沿用全站的 `cubic-bezier(0.22, 1, 0.36, 1)`
- ⛔ **不要超過 1200ms** —— 翻五頁就是五次等待，太慢會讓人不想翻完

> ⚠️ **第十五輪調慢（原本 600ms、上限 800ms）**：使用者實際翻過之後的回饋是
> **「600 毫秒太快」**。初稿的 600 與「不要超過 800」都是我憑感覺訂的，沒有依據；
> 實際翻起來，翻頁是這一段的主要樂趣，太快會讓那個動作一閃就過去、感覺不到「翻」。
> 上限一併放寬到 1200。
- 翻頁進行中鎖住輸入，避免連點造成頁碼與畫面不同步

##### ⛔ 翻頁元素在動畫尾聲必須淡出（第十六輪追加）

**症狀**：翻頁進行到中後段時，翻起來的那一頁**比它最終該在的位置往外偏一點、也大一點**，
於是吃掉木框內緣與部分頁面內距；動畫結束元素移除後才「跳」回正確位置。
使用者看到的是「翻完之後先閃一個版面不太對的畫面，然後才變正常」。

**量測**（1920 螢幕、900ms 動畫、左頁照片規格為距書本左緣 36、寬 440）：

| 動畫進度 | 翻頁層照片左緣 | 寬 | 偏差 |
| --- | --- | --- | --- |
| 514ms（57%）| 30 | 446 | −6／+6 |
| 580ms（64%）| 33 | 443 | −3／+3 |
| 653ms（73%）| 35 | 441 | −1／+1 |
| 725ms（81%）| 36 | 440 | 對齊 |

**原因**：3D 透視。旋轉中的平面尚未回到 `z=0`，其投影比最終位置略大略偏 ——
與 §14.7.1 的溢出同源，但**這一個裁切救不了**：偏移發生在內頁範圍**之內**，
不是溢出到書皮外。

⛔ **不要用「把翻頁元素做小一點來補償」** —— 偏移量隨動畫進度變化（6px → 0），
固定的補償值只會讓別的時間點錯得更多。

**解法：收尾段把透視拉平。** 翻頁到 **40% 之後，`perspective` 從 2000px 逐漸拉遠到 40000px**
（趨近正射投影）。透視放大是偏移的成因，透視拉遠偏移就趨近於零。

- 前 40% 保留完整透視 —— 那是頁面真正在轉、看得出深度的階段
- 40% 之後頁面已接近攤平，拉平透視在視覺上看不出來
- ⛔ 這**不是**「把元素做小一點來補償」：沒有任何固定的尺寸修正，
  而是把造成偏移的透視本身撤掉，所以不會有「某個角度剛好對、其他角度更錯」的問題

實測修正後（1920、900ms、規格左緣 36／寬 440）：45% 之後每一幀都在 **±0.7px** 內
（45% 時 35.8／440.6，57% 之後 35.9～36／440.0～440.1）。45% 之前頁面仍明顯擺動，
讀起來是動作而不是版面。

> ⚠️ **「最後 15% 淡出」單獨用是無效的，不要只做那一項。**
> 初版規格只寫淡出，實測發現**偏移在 83% 就已自行收斂到 0**，而淡出 85% 才開始 ——
> 淡的是一個位置已經正確的東西。要靠淡出遮住 57% 那一幀，淡出得從 55% 起算（45% 的區間），
> 遠超過「不要超過 25%」的上限，翻頁的實體感會整個消失。
> **淡出仍然保留**（收尾更柔和），但真正解決偏移的是上面的透視拉平。

##### ⛔ 淡出動畫不可以掛在翻頁元素上（第十六輪實測）

把 `opacity` 動畫掛在 `.story__flip`（帶 `transform-style: preserve-3d` 的那一層）會讓瀏覽器
**把整個 3D 內容壓平**，`backface-visibility: hidden` 隨之失效 ——
正面轉過去之後仍然畫得出來、還蓋在背面上，**後半段看到的會是舊頁反過來的鏡像文字**。

**淡出要掛在裁切層**（`transform-style: flat` 的那一層）。
視覺結果相同，而且完全不碰 3D。

⚠️ 這個問題**只查幾何數值查不出來** —— 位置全對，錯的是「畫出來的是哪一面」。
驗證方式是 `document.elementFromPoint` 命中的元素屬於正面還是背面，或直接截圖看有沒有鏡像字。

##### 手機版：偏移存在但不處理（第十六輪裁決）

手機同一成因的偏移**小一個數量級**：最後一個偏離 1px 以上的影格在 46%（寬少 1px），
照片 278 寬的左右各約 1px，合計約 2px。且收斂過程中頁面寬度每幀都在明顯變化
（256 → 278），讀起來是「頁面正轉回來」，沒有桌機那種「已經停住但版面不對」的階段。

**判定在可察覺門檻之下，不做。** 要做的話是同一招（收尾拉平透視）套在 `.story__card-inner`，
但那個元素是常駐的、不是每次翻頁重建，得多加一個 class 開關 —— 為 2px 增加一組狀態不划算。

##### ⛔ 翻頁元素必須被內頁裁切（第十五輪追加）

**症狀**：翻頁進行到中段時，翻起來的那一頁（白色）會**蓋住上下的木色書皮** ——
書本上緣有一半變成白的，右下角還露出一道斜邊；翻完元素移除才恢復正常。
使用者看到的是「中間先白一塊，然後才融合回去」的閃爍。

**原因**：3D 透視。頁面繞垂直軸旋轉時，離觀察者近的一側會被放大，
**上下邊會超出原本的 556 高度**，溢出到書皮上。這不是尺寸算錯 ——
翻頁元素的 `top: 12px / height: 556px` 完全正確，是旋轉後的投影變大了。

**解法**：在書皮內側加一層**只負責裁切**的容器（`overflow: hidden`），翻頁元素放進去。

⚠️ **那一層 ⛔ 不可以設 `transform-style: preserve-3d`** ——
`overflow: hidden` 與 `preserve-3d` 同時存在會壓平 3D，翻頁會變成平面滑動。
3D 上下文留在翻頁元素自己身上，裁切交給沒有 3D 的父層，兩者才不打架。

⛔ **不要改用「把翻頁元素做矮一點」來閃避** —— 那只是讓溢出量小到某個角度看不出來，
換一個 `perspective` 值或螢幕尺寸就會再跑出來。

⚠️ **手機版同樣要檢查** —— 手機是整頁替換（`rotateY ±90deg`），
同樣有透視放大，書頁卡的木色書皮一樣會被蓋到。
- **手機往回翻是往前翻的鏡像**：舊頁 `transform-origin: right center` 從 `rotateY(0)` 轉到 `+90deg` 並淡出，新頁從 `rotateY(-90deg)` 轉回 `0`（初稿只寫了往前翻，第十四輪補齊）

#### 14.7.2 進場分鏡（段落本身，捲動觸發）

翻頁是操作回饋；**段落第一次進入視野時仍然照全站規則做進場**，觸發規則沿用 §10.3。

| 順序 | 元素 | 動作 | 延遲 | 時長 |
| --- | --- | --- | --- | --- |
| 1 | 眉標 `OUR STORY` | `fade-up` | 0 | 700 |
| 2 | 主標 `How We Met` | `fade-up` | 90 | 700 |
| 3 | 金線 | `line-grow` | 180 | 600 |
| 4 | 書本／書頁卡 | `fade-up` | 300 | 700 |
| 5 | 卡內照片 | `reveal-mask` | 440 | 900 |
| 6 | 卡內文字（年份／標題／故事） | `fade-up`，各交錯 90ms | 600 | 700 |
| 7 | 翻頁鈕、頁點列、操作提示 | `fade-in` | 900 | 700 |

⛔ **進場動畫只在第一次進入視野時播一次。** 之後翻頁只走 `page-turn`，
⛔ 不要每翻一頁就把卡內元素重播一次 `fade-up` —— 那會讓翻頁變得很吵。

#### 14.7.3 `prefers-reduced-motion` 降級（⛔ 必做）

3D 旋轉對前庭敏感的人是實質不適，不是美感偏好。

| 項目 | 降級後 |
| --- | --- |
| `page-turn` | **完全移除 3D**，改為 200ms 的交叉淡入淡出 |
| 進場分鏡 | 依 §10.7 降為無位移的 `fade-in`，交錯歸零。**時長 200ms** |

> ⚠️ **第十四輪更正**：本節原寫進場降級為 300ms，但全站既有的降級規則
> （`_animations.scss`）寫死 **200ms**，Gallery／Info／RSVP 都跑這條。
> 為一段改成 300 會讓同一頁出現兩種降級節奏，**以全站既有值 200 為準**。

⛔ 版面不需要改成別的排列（不像 §12.4 的相簿），翻頁功能本身照常運作。

### 14.7.4 無障礙（⛔ 這一段是全站互動最多的，不能只做滑鼠）

| 項目 | 要求 |
| --- | --- |
| 翻頁鈕 | 真正的 `<button>`，`aria-label` 為「上一頁」／「下一頁」（⛔ 不是「chevron」） |
| 鍵盤 | 左右方向鍵翻頁（焦點在書本區內時），作法同 §11.3 燈箱 |
| 邊界 | 首頁的上一頁、末頁的下一頁設 `disabled`，⛔ 不要只做視覺變淡卻仍可點 |
| 換頁通知 | 書頁內容區加 `aria-live="polite"`，翻頁後報讀器會唸出新頁 |
| 頁碼 | 頁點列對報讀器隱藏（`aria-hidden`），另以視覺隱藏文字提供「第 3 頁，共 5 頁」 |

### 14.8 待確認（新的設計疑問）

| 編號 | 問題 | 現況 | 影響 |
| --- | --- | --- | --- |
| **Q12** | **五段故事全是虛構的示範文案** | 新人尚未提供交往經過 | ⛔ **上線前必須整批替換**。這是全站最不能留著假內容的地方 —— 賓客會當真 |
| **Q13** | 每頁的**照片尚未指定** | 設計稿用 stock 佔位 | 五頁需要五張「有時間感」的照片（交往期間的生活照，不是婚紗照）。若只能用婚紗照，故事的時間軸會失去說服力 |
| **Q14** | 頁數固定 5 頁，**頁點列在超過 6 頁時會太密** | 現為 5 顆點 | 同 §12.6 相簿的老問題。超過 6 頁要改成「3 / 8」數字式 |

**對應的 pen 節點 ID**（`pen-drawer` 第七輪回填，供 `design-question-curator` 釘紅框用）：

| 編號 | 手機 `wbUtn` | 桌機 `fAw6F` |
| --- | --- | --- |
| Q12（五段故事全是虛構） | `v9XAif`（故事文字）／`k5xK5`（段落標題）／`vhusd`（年份標籤） | `joM75`（故事文字）／`JXYQE`（段落標題）／`GuQyq`（年份標籤） |
| Q13（每頁照片未指定） | `NxfTr`（照片-第1頁） | `vwrx1`（左頁照片） |
| Q14（頁點列超過 6 頁會太密） | `By7TO`（頁點列） | `AIhWQ`（頁點列） |

⚠️ **Q12～Q14 目前只登記在 §14.8，尚未進 §7.0 索引表。** `design-question-curator` 的取題來源是 §7，
不補進去這三題不會被標註（第五輪的 Q9～Q11 也是這樣，後來由 `design-lead` 補上）。

⚠️ **設計稿只畫了第 1 頁**，所以 Q12 的紅框只釘得到第 1 頁的文案節點；
另外四頁的假文案**在 `.pen` 上沒有對應元素**，只存在於 §14.5 的表格。
下游若只看設計稿，會以為只有一段假文案要換。

### 14.9 圖片來源

設計稿階段依 §9.0 ⑥ 用 `Generate(id, "stock", prompt)`。
**prompt 一律寫短（4～6 個關鍵字）**，理由見 §13.8 的實測結論。

| 頁 | stock prompt |
| --- | --- |
| 1 初次見面 | `friends gathering cafe warm evening` |
| 2 熟悉起來 | `couple night street city lights` |
| 3 在一起 | `couple holding hands walking sunset` |
| 4 一起走過的日子 | `young couple home cozy daily life` |
| 5 他問，她說好 | `marriage proposal ring outdoor` |

⚠️ **五張要用同一個色調傾向**（暖調、柔和），否則翻頁時每頁色溫跳動會很明顯 ——
這比單張圖好不好看重要得多。

### 14.10 對既有畫布落點的影響

| 節點 | 現 y／h | 新 y／h |
| --- | --- | --- |
| `裝置版-單頁全覽` | 0／4264 | 0／**5002**（＋738） |
| `電腦版-單頁全覽` | 0／4784 | 0／**5756**（＋972） |
| 輔助那一列（4 個 frame） | y=5000 | y=**5900**（距桌機長頁底 144）|

> ⚠️ **第九輪數字**（書本加寬 ＋ 手機控制列外移後）：手機段 700 → **732**、桌機段 912 → **972**。

⚠️ **輔助那一列一定要移**：桌機長頁會長到 5696，5000 那條線會被壓在長頁裡。

手機長頁段落新落點：

| 段 | y | h |
| --- | --- | --- |
| S1 Hero | 0 | 844 |
| S9 About | 844 | 820 |
| **S10 Story** | **1664** | **738** |
| S2 Gallery | 2402 | 720 |
| S3 Info | 3122 | 900 |
| S4 RSVP | 4022 | 560 |
| S5 Footer | 4582 | 420 |
| **合計** | | **5002** |

桌機長頁段落新落點（以第六輪實測值為基礎）：

| 段 | y | h |
| --- | --- | --- |
| 段1 Hero | 0 | 900 |
| 段1.5 About | 900 | 772 |
| **段1.6 Story** | **1672** | **972** |
| 段2 Gallery | 2644 | 942 |
| 段3 Info | 3586 | 970 |
| 段4 RSVP | 4556 | 620 |
| 段5 Footer | 5176 | 580 |
| **合計** | | **5756** |

> ✅ **本節兩張表已於第十一輪修正後重新逐列實測核對，畫布與表列完全相同**（手機七段、桌機七段的
> y 與 h 全部吻合，總高 **5002／5756** 也吻合）。輔助那一列在 y=5900，與桌機長頁底部（5756）相距 **144**。
>
> ⚠️ **144 是目前最小的一次間隔**（第七輪 204、第八輪 204）。再加一段或再加高，
> 輔助那一列就得再往下移一次 —— 它已經移過兩次（4200 → 5000 → 5900）。
