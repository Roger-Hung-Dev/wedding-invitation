# 內容替換索引

> 這份文件回答一件事：**要改網站上的某個東西，該去動哪個檔案。**
>
> 網站沒有後端、沒有後台，所有內容都寫在程式碼裡。改完 push 到 `main`，
> GitHub Actions 會自動重新建置並部署，不需要做任何額外設定。

**線上網址**：https://roger-hung-dev.github.io/wedding-invitation/

---

## 0. 改完之後怎麼上線

```bash
git add -A
git commit -m "chore: 更新婚禮實際資訊"
git push
```

推上去之後到 GitHub 的 **Actions** 頁籤，會看到一個正在跑的部署。
跑完（約 2～3 分鐘）重新整理網站即可看到新內容。

⚠️ **瀏覽器可能有快取**，看不到變化時用強制重新整理（`Ctrl + F5`）。

---

## 1. 最常改的：新人資訊與場地

**檔案**：`src/app/core/config/wedding-content.ts`

這是全站文字資訊的集中處，改這一個檔就會同時更新手機版與桌機版。

| 常數名 | 現在的值 | 出現在哪 |
| --- | --- | --- |
| `brideGroomEn` | `Roger & Amy` | 封面大字、頁尾、分享卡 |
| `brideGroomZh` | `洪承孝　✕　李怡安` | 封面英文名下方 |
| `weddingDate` | `2026-12-12` | 程式用的日期（倒數計時的基準） |
| `weddingDateDisplay` | `2026 . 12 . 12　SATURDAY` | 封面顯示用 |
| `weddingDateOnlyDisplay` | `2026 . 12 . 12` | 宴客資訊區的日期大字、頁尾 |
| `dateSubDisplay` | `星期六` | 日期下方的小字（新人選擇不顯示農曆） |
| `venueName` | `臻愛花園酒店` | 宴客資訊區 |
| `venueHall` | `2F　東方明珠` | 宴客資訊區 |
| `seatingGuide` | `入口處設有座位表，男方親友請至 A 區、女方親友請至 B 區` | 宴客資訊區 |
| `monogram` | `R & A` | 頁尾的金色圓環內（⛔ 這個用半形空白）|
| `rsvpDeadlineDisplay` | `2026 / 11 / 08` | 回覆截止日 |

### 1.1 中文姓名裡的空白是全形空白，不是普通空格

`洪承孝　✕　李怡安` 中間用的是**全形空白**（U+3000）。
換成普通半形空格會讓字距變窄、視覺鬆緊跑掉。複製現有的格式改字即可。

同樣情形也出現在 `venueHall`（`2F　東方明珠`）。

⛔ **但 `monogram` 相反，要用半形空白**（`R & A`）—— 它在 20px 字級的小圓環裡，
全形空白會讓 R 與 A 各離 & 二十多 px，看起來是散開的三個字母而不是一組縮寫。

### 1.2 名字變長會影響版面

封面的中文姓名字距很寬（每個字之間有間隔）。
**四個字以上的名字**（例如複姓）會讓那一行變長，在 390px 的手機上可能貼近邊緣。
改完務必在手機上實際看一次。

---

## 2. 倒數計時的目標時間

**檔案**：`src/app/core/config/wedding-content.ts`
**常數**：`WEDDING_COUNTDOWN_TARGET_ISO`

```
'2026-12-12T18:00:00+08:00'
```

這是晚宴開席時間。改時分即可，`+08:00` 是台灣時區，不要拿掉。
倒數歸零後，封面的四格會換成 `HERO_TEXT.countdownOverMessage` 那句話。

---

## 3. 宴席場次（午宴／晚宴）

**檔案**：`src/app/core/config/wedding-content.ts`
**常數**：`WEDDING_SESSIONS`

```ts
{ id: 'dinner', label: '晚宴', timeDisplay: '18:00' },
```

**這場婚宴只辦晚宴一場**，所以只有一筆，畫面上的切換膠囊只有一顆。

日後若加辦午宴，在陣列裡補一筆 `{ id: 'lunch', label: '午宴', timeDisplay: '12:00' }` 即可，
切換行為不用改 —— 預設選中的是陣列第一筆，不是寫死 `'lunch'`。

---

## 4. 圖片替換

### 4.1 圖片已全部換成新人的婚紗照

所有圖片都放在專案裡（`src/assets/`），沒有任何外部圖庫連結。

**原始檔（每張 7～15MB）不進版控** —— `.gitignore` 忽略了
`src/assets/weddingphotos/`、`src/assets/images/dobe-*.jpg`、`map.png` 與未壓縮的音檔。
網站用的是壓縮後的版本（全部圖片加起來約 2.7MB），這幾個目錄才進版控。

要再換圖時的兩種方式：

| 方式 | 怎麼做 | 適合 |
| --- | --- | --- |
| **放進專案**（建議） | 把圖片放到 `src/assets/images/`，常數改成 `'assets/images/檔名.jpg'` | 正式婚紗照，不依賴外部服務 |
| 換成別的網址 | 直接改常數裡的網址 | 暫時替換、測試 |

⚠️ 用第一種方式時，路徑**不要以斜線開頭**（寫 `assets/...` 不要寫 `/assets/...`）。
網站部署在子路徑底下，開頭加斜線會導致上線後圖片 404，**而本機測試完全正常** —— 這種錯最難發現。

### 4.2 各張圖的位置

**檔案**：`src/app/core/config/wedding-content.ts`

| 常數名 | 現在指向 | 用在哪 |
| --- | --- | --- |
| `HERO_IMAGE_URL` | `assets/images/hero-mobile.jpg` | 封面滿版底圖（手機），直式 1200×1600 |
| `HERO_IMAGE_DESKTOP_URL` | `assets/images/hero-desktop.jpg` | 封面滿版底圖（桌機），橫式寬 2400 |
| `GALLERY_PHOTOS` | `assets/gallery/photo-1~8.jpg` | 相簿 8 張，直式寬 1000 |
| `MAP_PREVIEW_IMAGE_URL` | `assets/images/map-preview.jpg` | 地圖預覽（手機） |
| `MAP_PREVIEW_IMAGE_DESKTOP_URL` | 同上（手機桌機共用一張） | 地圖預覽（桌機） |

**相簿張數可以改**：`GALLERY_PHOTOS` 增減項目即可，手機版的頁點指示器會跟著變。
**現在正好 8 張，已經是頁點指示器的上限** —— 再加就會太密，那時要改成數字式指示器（例如 `3 / 12`）。

每一張都有 `alt` 欄位（給讀螢幕軟體與圖片載入失敗時用），換照片時請一併改成符合新照片的描述。

### 4.3 ⚠️ 封面圖要改兩個地方

換封面圖時，除了 `HERO_IMAGE_URL`，還要改：

**檔案**：`src/index.html`（約第 32 行）

```html
<link rel="preload" as="image" href="assets/images/hero-mobile.jpg" fetchpriority="high">
```

這一行是為了讓封面圖搶先載入（首屏速度）。**沒有一起改的話，網站會先下載一張用不到的舊圖，白白浪費行動網路流量。**

### 4.4 地圖圖片

`map-preview.jpg` 是新人提供的 Google 地圖截圖（臻愛花園酒店，高鐵台中站旁）。
原圖近正方形，已裁成 16:9 並保留中央的紅色場地標記。

換圖時記得：**紅色標記要落在圖片中央附近**，因為版面是橫式的，上下會被裁掉。

---

## 5. 外部連結

**檔案**：`src/app/core/config/wedding-links.ts`

| 常數名 | 現在的值 | 狀態 |
| --- | --- | --- |
| `rsvpFormUrl` | `https://forms.gle/PLACEHOLDER_RSVP_FORM` | ⚠️ **還是假網址**（葷食版）|
| `rsvpFormUrlVegetarian` | `https://forms.gle/PLACEHOLDER_RSVP_FORM_VEG` | ⚠️ **還是假網址**（素食版）|
| `venueAddress` | `台中市烏日區高鐵路三段 168 號` | ✅ 已是正式地址 |

### 5.0 網站有兩個版本，網址不同

| 版本 | 網址 | 給誰 |
| --- | --- | --- |
| 葷食（預設）| `https://roger-hung-dev.github.io/wedding-invitation/` | 絕大多數賓客 |
| 素食 | `https://roger-hung-dev.github.io/wedding-invitation/vegetarian` | 吃素的賓客 |

兩版**只差四個地方**：

| 項目 | 葷食版 | 素食版 |
| --- | --- | --- |
| 桌次引導 | 男方 A 區、女方 B 區 | 我們已為您預留蔬食席位 |
| 表單網址 | `rsvpFormUrl` | `rsvpFormUrlVegetarian` |
| 欄位預告 | 姓名／出席人數／**素食需求**／兒童椅／聯絡電話 | 姓名／出席人數／兒童椅／聯絡電話／**蔬食備註** |
| 餐點說明 | 無 | 宴客資訊區多一段「關於今天的餐點」 |

其餘內容完全相同，改一次兩版都會變。

**要改兩版的差異**：`src/app/core/config/wedding-content.ts` 的 `DIET_VARIANTS`。

⛔ **素食版的桌次引導不要寫成「安排於某某區」** —— 實際安排是女方親戚桌全蔬食、
朋友桌葷素混合，蔬食席位是分散的。指定區域會讓賓客到現場找不到那一區。

⚠️ **兩版問的不是同一件事**：葷食版問「素食需求」（你吃不吃素），
素食版問「蔬食備註」（你吃哪一種素——全素／蛋奶素／忌五辛）。
⛔ 素食版不要再問一次是否吃素，那會讓賓客以為自己拿錯連結。

⚠️ 這些標籤要跟**實際的 Google 表單題目**對得上，否則賓客看到預告了卻沒被問。

### 5.1 ⚠️ 表單網址還沒填，這是目前唯一擋著上線的東西

`rsvpFormUrl` 仍是占位值。**賓客按下「填寫出席回覆表單」不會開啟任何表單**，
會停在一個不存在的頁面。拿到 Google 表單網址後改這一行即可，不需要動別的地方。

### 5.2 地址

**不需要經緯度座標** —— 導航連結是用地址文字組出來的，改地址就會自動更新。

⚠️ **地址只有這一個來源**：宴客資訊卡上顯示的地址、與導航按鈕帶的目的地，
兩者都讀 `venueAddress`。改這一個地方，兩處會一起變。

### 5.3 「編輯回覆」連結已經移除

新人沒有開啟 Google 表單的「提交後可編輯回覆」，所以畫面上原本那行
「已經填寫過了？點此修改回覆」連同 `rsvpEditUrl` 常數一起拿掉了 ——
留著會是一個點不開的入口。

**日後想加回來**，要動三個地方：`wedding-links.ts` 補 `rsvpEditUrl`、
`RSVP_TEXT` 補 `editLinkLabel`、`rsvp.component.html` 補那個 `<a>`（樣式在同目錄的 `.scss`）。

---

## 6. 背景音樂（已經有音檔了）

**檔案**：`src/app/features/music-player/music-player.component.ts`（約第 28 行）

```html
<audio #audioEl loop preload="none">
  <source src="assets/audio/wedding-bgm.mp3" type="audio/mpeg">
</audio>
```

音檔在 `src/assets/audio/wedding-bgm.mp3`（2.6MB、約 3 分 48 秒，循環播放）。

⚠️ **換音樂時記得壓縮。** 原始檔通常是 192kbps 以上，一首 4 分鐘的曲子就 5～6MB。
現在的設定是**賓客一進站就開始靜音預載**（見本節下方說明），檔案多大就下載多少。
壓到 **96kbps** 對背景音樂綽綽有餘，同一首曲子從 5.5MB 降到 2.6MB。

**換音樂**：新檔案放進 `src/assets/audio/`，改上面那一行的檔名即可
（路徑開頭**不要加斜線**）。

**幾件要知道的事**：

- 手機瀏覽器**禁止網頁自動播放聲音**，所以設計成「賓客首次點擊頁面任一處才開始播」。這是瀏覽器的限制，不是可以繞過的設定
- 音檔建議壓到 **3MB 以內**，賓客多半用行動網路開啟
- 版權：婚禮網站是公開的，用有授權的音樂

---

## 7. 各區塊的顯示文字

**全部都在同一個檔**：`src/app/core/config/wedding-content.ts`

依畫面由上到下拆成六組具名常數，找的時候照著畫面位置找就對了：

| 常數名 | 管哪一段畫面 | 裡面有什麼 |
| --- | --- | --- |
| `HERO_TEXT` | 封面 | `WE ARE GETTING MARRIED` 眉標、倒數四格的英文標籤、`SCROLL` 提示、婚期過後要顯示的那句話 |
| `GALLERY_TEXT` | 相簿 | `GALLERY` 眉標、`Our Moments` 主標、金句、滑動提示 |
| `INFO_TEXT` | 宴客資訊 | `INFORMATION` 眉標、`Wedding Day` 主標、四條資訊列的標籤、導航按鈕文字、入場提醒、地圖的無障礙描述 |
| `RSVP_TEXT` | 意願調查 | `R.S.V.P.` 眉標、`Will You Join Us?` 主標、說明文、五顆欄位 chips、CTA 按鈕 |
| `FOOTER_TEXT` | 頁尾 | `Thank You` 主標、致謝內文、版權 |
| `MUSIC_PLAYER_TEXT` | 音樂鈕 | 三種狀態的無障礙標籤（畫面上看不到，螢幕報讀軟體會唸） |

另外 `WEDDING_CONTENT` 放的是**資料**（姓名、日期、場地），見第 1 節。
分工是：`WEDDING_CONTENT` ＝ 會變的事實，`*_TEXT` ＝ 畫面上的說法。

### 7.1 手機兩行、桌機一行的那幾句

相簿金句與頁尾致謝詞在手機上刻意斷成兩行（螢幕窄），桌機是一整句。
**這個斷點是設計決定的，不是自動換行。**

- `GALLERY_TEXT.quote` 同時有 `full`（桌機一整句）與 `lines`（手機兩行）**兩種形式**
  → 改的時候**兩個都要改**，否則換台裝置看會看到舊句子
- `FOOTER_TEXT.bodyLines`、`RSVP_TEXT.introLines` 是**單一份陣列**，兩個裝置共用
  （斷行交給 CSS 處理）→ 改一處即可

### 7.2 回覆截止日只有一個來源

`RSVP_TEXT.introLines` 第二行寫的是 `敬請於 {{deadline}} 前回覆。`，
那個 `{{deadline}}` 會自動換成 `WEDDING_CONTENT.rsvpDeadlineDisplay`。

⛔ **不要把日期直接打進說明文**，否則改了 `rsvpDeadlineDisplay` 這裡不會跟著變。

### 7.3 畫面檔（`.html`）裡已經沒有中文文案了

重構後所有使用者看得到的文字都在常數檔。
`gallery.component.html` 裡還剩一段中文，那是**寫給工程師看的註解**（解釋為什麼手機與桌機版式要同時放在 DOM 裡），不是畫面文字。

---

## 8. 分享到 LINE／Facebook 時顯示的縮圖卡

**檔案**：`src/index.html`（第 10～23 行）

| 標籤 | 現在的值 | 說明 |
| --- | --- | --- |
| `og:title` | `We are Getting Married! 洪承孝 & 李怡安 婚禮邀請函` | 卡片標題 |
| `og:description` | `2026 . 12 . 12 星期六　臻愛花園酒店　⋯` | 卡片內文 |
| `og:image` | `https://roger-hung-dev.github.io/wedding-invitation/assets/images/og-share.jpg` | 卡片縮圖 |
| `twitter:title` / `twitter:description` / `twitter:image` | 同上 | 給 X（Twitter）用，**要跟上面同步改** |

**縮圖檔案**：`src/assets/images/og-share.jpg`（1200×630）
現在是**封面婚紗照裁切的純照片**，上面沒有文字。
換圖時直接覆蓋這個檔案即可，網址不用改。

> 💡 想要像設計稿那樣**在縮圖上疊姓名與日期**的話，那需要另外做一張圖
> （網頁的字型排版沒辦法直接輸出成圖片）。純照片版的好處是永遠不會有錯字。

### 8.1 三個容易踩的坑

1. **`og:image` 必須是完整網址**（`https://` 開頭）。改成 `assets/...` 這種相對路徑的話，
   社群平台的爬蟲抓不到，分享出去就沒有縮圖。
2. **改了縮圖但 LINE 還是顯示舊圖** —— 那是平台的快取。
   Facebook 可用 [分享偵錯工具](https://developers.facebook.com/tools/debug/) 強制重新抓取；
   LINE 沒有官方工具，通常等一段時間才會更新。
3. **`og:image:width` / `og:image:height` 要跟實際圖片尺寸一致**（現在是 1200×630）。
   換成不同尺寸的圖時要一起改，否則某些平台會裁切錯誤。

### 8.2 換網域的話要改四個地方

如果之後改用自訂網域（例如 `ethan-chloe.wedding`）：

| 要改什麼 | 在哪 |
| --- | --- |
| `og:url`、`og:image`、`twitter:image` | `src/index.html` |
| `baseHref` | `angular.json` 的 `production` 設定，改成 `"/"` |
| `CNAME` 檔 | 在 `public/` 新增，內容就是網域名 |
| GitHub 設定 | repo 的 Settings → Pages → Custom domain |

⚠️ **`baseHref` 忘了改是最容易犯的錯**：網站會整頁空白，而本機測試完全正常。

---

## 9. 顏色與字型（要動視覺再看這節）

| 要改什麼 | 檔案 |
| --- | --- |
| 全站 17 個顏色 | `src/styles/_tokens.scss` |
| 字型載入（Great Vibes、Cormorant Infant） | `src/index.html` 的 Google Fonts 連結 |
| 動畫的時長與位移 | `src/styles/_animations.scss` |

⛔ **英文花體字（Great Vibes）不能套在中文上** —— 那套字型沒有中文字符，會變成方塊豆腐字。
所有中文一律用 Cormorant Infant（會自動退回系統的中文襯線字）。

改顏色時**改變數就好**，全站會一起變。不要在個別元件裡寫死色碼。

---

## 10. 上線前檢查清單

給賓客之前逐項確認：

- [x] 新人姓名、婚期、飯店、廳別、地址、桌次引導都換成正式資訊
- [x] 倒數計時的目標時分改成實際開席時間（12/12 晚上 6 點）
- [x] 宴席場次確認是一場還是兩場（只辦晚宴）
- [x] 婚紗照換成真的照片（8 張，含 `alt` 描述）
- [x] 封面圖改了，**`index.html` 的 preload 那一行也一起改了**
- [x] 地圖圖片換成場地實際位置
- [x] 「編輯回覆」連結（表單沒開這功能，那一行已移除）
- [x] 背景音樂音檔放上去
- [x] 分享卡縮圖換成新人的照片
- [ ] ⚠️ **Google 表單網址填上，實際點一次確認會開啟正確的表單** ← 還沒
- [ ] 在手機上實際聽一次背景音樂
- [ ] 用手機把網址傳給自己，確認分享縮圖有出現
- [ ] **在真的手機上開一次**，不要只在電腦的縮小視窗裡看

---

## 11. 這份文件沒有涵蓋的

**版面結構的調整**（區塊順序、增減區塊、改版式）不在這份索引裡 ——
那需要動元件與樣式，屬於開發工作。設計規格在
`.claude/docs/design/wedding-invite-20260904/wedding-home.md`，
那份文件是設計的唯一真相，包含版面數值、色票、逐元素字級與動畫規格。

**設計階段的未決事項**記在同一份文件的第 7 節。
其中「姓名」「午晚宴幾場」「相簿張數」「喜餅怎麼領」已由新人拍板（見上面各節），
剩下「要不要中英雙語」等仍未決。
