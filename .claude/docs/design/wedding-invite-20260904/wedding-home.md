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

段內主要子節點（供後續標註對位）：
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
