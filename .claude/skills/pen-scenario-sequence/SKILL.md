---
name: Pen 功能情境繪製
description: 把「一個動作造成的畫面變化」繪成 .pen 功能情境序列的規範 —— 說明帶＋前後畫面由左至右串接、分支情境、以 Copy 母版做狀態變體與衍生畫面、關閉繼承的疑問標註、與設計疑問紅框的語意區隔。當任務是「畫出點某個按鈕後畫面怎麼變」「補功能情境區塊」時使用；單張畫面重繪用 pen-screen-drawing，抽象步驟卡用 pen-flow-diagram。
---

# Pen 功能情境繪製

> 共用基礎（環境、作用域、`Copy`＋`descendants`、驗證）見 [[pen-authoring]]，**先遵循它**。
> 畫面母版怎麼來、toast 與小元素慣例見 [[pen-screen-drawing]]；抽象步驟卡片改用 [[pen-flow-diagram]]。

## 1. 這個 skill 解決什麼

`draw-screen` 畫的是**單一畫面的靜態樣貌**，`draw-flow` 畫的是**抽象步驟卡片**。兩者都答不了「**點了這顆按鈕之後，畫面實際變成什麼樣**」。

功能情境補的就是這一段：**一段說明 ＋ 真實畫面由左至右的變化鏈**。

```
情境① 切換狀態分頁
  說明：點狀態分頁切換列表篩選結果。
  [列表-全部] →點「處理中」→ [列表-處理中] →點「已確認」→ [列表-已確認]
```

**不是**流程摘要（那是 `draw-flow`），**也不是**再重畫一次畫面（畫面一律 `Copy` 母版）。

## 2. 硬前提：必須先有 `draw-screen` 母版

情境裡的每一張畫面都是**母版的副本**，不重畫。開工前檢查分析檔**第 8 節「已繪製節點」**是否有型態為 `screen` 的節點：

- 沒有 → **以 `blocked` 回報**「請先對本畫面跑 `draw-screen`，情境需要可 Copy 的畫面母版」。**不要自己畫一張新的畫面當母版**（會與 `draw-screen` 的產出重複且不同步）。
- 有 → 記下母版節點 ID 與其關鍵子節點 ID（表格列、欄位值、按鈕、分頁列…）。子節點 ID 是覆寫的唯一入口。

> 若母版的子節點 ID 沒有留在分析檔裡，用 `execute`：`Get("<母版ID>",(n,c)=>Print(c.depth,n.id,"|",n.type,"|",n.name),{depth:4})` 重新取，不要靠印象。

## 3. 版面骨架（畫面由左至右，說明帶在最上）

```
功能情境-{畫面名} (root, 深色畫布, vertical)
├─ 主標題帶                      fill: $canvas-band
├─ 情境① {情境名}                 fill: $sec-bg, layout: vertical
│   ├─ 說明帶（固定 width 1100）
│   ├─ 序列列 (horizontal, alignItems:"start")
│   │   [畫面A] →箭頭→ [畫面B] →箭頭→ [畫面C]
│   └─ 變化重點卡（固定 width 1100）
├─ 情境② …
└─ 情境③ …
```

- root：`fill:"$canvas-dark"`、`layout:"vertical"`、`gap:40`、`padding:48`、**寬度不要寫死** —— 讓它被最寬的那個情境撐開（`width` 省略，由內容決定）
- 情境分區：`fill:"$sec-bg"`、`cornerRadius:"$r-lg"`、`padding:26`、`gap:18`、`layout:"vertical"`、`alignItems:"start"`
- 序列列：`layout:"horizontal"`、`gap:24`、`alignItems:"start"`
- 情境編號用 ①②③ 前綴，方便口頭指涉
- **root 的 frame 名稱必須含「功能情境」四字** —— 反導的完整性閘門靠名稱關鍵字遞迴比對（見 [[design-handoff-contract]] §7），名字不對等於這個區塊不存在。

### 寬度紀律（左右排的代價，一定要照做）

一列 N 張畫面的寬度 ＝ `N*1280 + (N-1)*(150+24*2)`（畫面 1280、箭頭 150、gap 24）：
2 張 ≈ 2758｜3 張 ≈ 4236｜4 張 ≈ 5714。

**說明帶與變化重點卡一律固定 `width:1100`，絕對不可用 `width:"fill_container"`。**
它們若跟著序列列變寬，文字會被拉成 4000px 的單行、完全不能讀 —— 這正是 [[pen-flow-diagram]] §3 寬度紀律要防的事。左右排能成立，靠的就是「畫面橫著長、文字不跟著長」。

**一列最多 4 張畫面。** 更長的鏈拆成兩個情境（例：「切換分頁」與「篩選後查看」各自成境）。

## 4. 說明帶

每個情境最上面一條說明帶（`width:1100`），**四行以內**：

| 行 | 內容 | 必要性 |
| --- | --- | --- |
| 標題 | `情境① {情境名}` | 必要 |
| 說明 | 一句話講完「做什麼動作、畫面怎麼變」 | 必要 |
| 觸發 | 前置條件（例「已有查詢結果」「單據狀態＝草稿」） | 有條件才寫 |
| 依據 | 設計稿註解出處（含 node id），**逐字引用** | 有依據才寫 |

說明文字一律 `textGrowth:"fixed-width"`＋`width:"fill_container"`（在固定 1100 的說明帶**之內**填滿，不是跟著序列列變寬）。

## 5. 動作箭頭

`arrow-right`（水平鏈）＋ 動作標籤，箭頭容器 `width:150`。

標籤寫**使用者的實際操作**，逐字用畫面上的按鈕文字：「點『查詢』」「點『刪除』」「勾選 3 筆後點『批次過帳』」。不要寫「執行查詢動作」這種抽象描述。

## 6. 分支情境

一個動作有多種結果（確認／取消、成功／檢核失敗）時，**在分岔點右側放一個垂直的分支容器**，每條分支自己一列：

```
[前態] →點「刪除」→ [確認彈窗] ─┬─ →點「確認」→ [刪除成功]
                                └─ →點「取消」→ [回列表-全部]
```

實作：分支容器 `layout:"vertical"`、`gap:24`、`alignItems:"start"`，內含 N 個 `horizontal` 列，每列 ＝ 箭頭 ＋ 畫面。

- **主線（happy path）放第一條**，例外／取消放後面。
- 分支標籤要能一眼分辨走哪條：`→點「確認」`、`→點「取消」`、`→檢核失敗`。
- 分支超過 3 條 → 拆成兩個情境，不要無限往下長。
- 分支資訊從哪來：分析檔 §5.1 的情境序列；`.pen` 既有流程圖的箭頭標籤（`draw-flow` 畫的「確認」「取消」「切換分頁」等）是最可靠的來源。

## 7. 衍生畫面（沒有母版的後態）

分支的後態常常**沒有畫面稿**（設計稿只在流程圖放了一張卡，例如「刪除成功：該列消失＋跳 toast」）。此時：

1. `Copy` **最接近的母版**，用 `descendants` 覆寫成該狀態（關掉一列、改分頁列筆數、依 [[pen-screen-drawing]] §7 的慣例加 toast…）。
2. 節點名稱**前綴 `衍生-`**（例：`情境②-後態-衍生-刪除成功`）。
3. 說明帶或該分支的標籤上**明寫「衍生畫面（非原稿）」**。
4. 在回報的 `analysisGaps` 列出「哪些畫面是衍生的、依據哪段註解造的」。

**衍生畫面不是設計依據。** 它是為了讓情境鏈看得完整而合成的示意；後續反導、寫規格、做 schema 時，一律以原稿母版與註解原文為準。造之前先確認註解真的講了那個結果（逐字引用），**沒有依據就不要造** —— 改用一張文字說明卡帶過，並在 `analysisGaps` 說明缺畫面稿。

## 8. 關閉從母版繼承的疑問標註（必做）

若 `annotate` 已經跑過，母版上會有紅框與編號徽章，**`Copy` 會把它們一起帶進情境副本** —— 於是情境區塊裡出現紅框，正好違反 §9 的語意區隔（讀者會以為情境本身有未決疑問，反導閘門掃關鍵字時也可能誤命中）。

1. 從分析檔第 8 節取型態為 **`annotation`** 的節點 ID（紅框、編號徽章、疑問卡）。
2. `Copy` 時以 `descendants` 關掉：`d[標註節點ID] = { enabled: false }`。
3. 第 8 節**沒有** `annotation` 節點可查時，先用 `execute`：`Get("<母版ID>",(n,c)=>/疑問/.test(n.name)&&Print(n.id,"|",n.name),{depth:2})` **從 `.pen` 實地找**（標註節點通常是母版的直接子節點，命名含「疑問」）；找到就關掉並在回報說明來源。真的找不到才照原樣 Copy，並在 `analysisGaps` 明講。**不要靠猜刪除節點。**

> **順序建議**：同批次要同時跑 `annotate` 與 `draw-scenario` 時，把 `draw-scenario` 排在 `annotate` **之前**，情境副本就天生乾淨。

## 9. 變更點標示（與設計疑問紅框的語意區隔）

要圈出「哪裡變了」時，用 **`$primary` 藍框**：`stroke:"$primary"`、`strokeWidth:2`、`fill` 透明、右上角一枚 `$primary` 底的「變更」小標籤。

> **絕不可用 `#eb4751` 紅框。** 紅框在本產線是 `design-question-curator` 的**設計疑問**專用語意（見 [[design-handoff-contract]] §6）。情境用紅框會讓後續的疑問標註與反導的閘門判讀全部誤判。

變更點多於 3 處時不要框滿畫面，改用 §3 的**變化重點卡**條列（`$info-card` 底、逐條寫「欄位 → 變化」）。

## 10. 每一格都必須可獨立匯出，並逐格登記節點 ID（必做）

下游的規格線**要逐格內嵌**這些畫面（見 [[design-handoff-contract]] §8）。整條序列寬 4000～6000px，整張匯出後縮到文件欄寬，文字會小到讀不到 —— 所以規格線需要的是「每一格各一張」。

因此：

1. **每一格（前態／中繼／後態／各分支後態）都是序列列底下自己的一個 frame**，不要把多格塞進同一個容器、也不要用純座標的 `group` 湊。
2. **回填分析檔第 8 節時，root 與每一格都要各登記一列**（型態一律 `scenario`），縮排或前綴標出從屬關係：

   ```
   | 情境N {情境名}                        | <rootID>  | scenario |
   | ─ 情境N-前態-{狀態}                    | <id>      | scenario |
   | ─ 情境N-中繼-{彈窗名}                  | <id>      | scenario |
   | ─ 情境N-後態-{結果}                    | <id>      | scenario |
   | ─ 情境N-後態-衍生-{分支結果}            | <id>      | scenario |
   ```

3. 命名照 `情境N-{前態|中繼|後態}-{說明}`（衍生畫面依 §7 加 `衍生-`），讓下游看名字就知道是哪一格。

> **為什麼這條是設計線的責任**：只登記 root 的話，規格線只有兩條路 —— 匯出整條序列（產出讀不到的圖），或自己進 `.pen` 逐層找節點（把設計線的責任推給規格線）。兩者都不該發生，而且**兩者都不會報錯**，只會在交付時才被人發現規格裡有一大塊看不清的圖。

## 11. 情境的副本不是疑問標註的對象

`design-question-curator` 的紅框釘在**母版畫面**上（分析檔第 7 節的 `pen 節點 ID` 指的是母版的子節點）。情境區塊裡的副本**不標疑問**。

回填分析檔第 8 節時，情境副本的型態一律寫 **`scenario`**，與母版的 `screen` 區分開，讓下游看得出哪些節點不該被標註。

## 12. Helper 樣板（每個 `execute` 重新貼一次）

```js
const ROOT = "<root節點ID>"
const TEXTW = 1100                       // 說明帶／變化重點卡固定寬 —— 不可改成 fill_container

const mkScenario = (no, title) =>
  Insert(ROOT, { type:"frame", name:`情境${no} ${title}`, layout:"vertical", gap:18,
                 alignItems:"start", fill:"$sec-bg", cornerRadius:"$r-lg", padding:26 })

const mkDesc = (parent, no, title, lines) => {
  const n = Insert(parent, { type:"frame", name:"說明帶", layout:"vertical", gap:8, width:TEXTW,
                             fill:"$info-card", cornerRadius:"$r-lg", padding:[18,22] })
  Insert(n, { type:"text", name:"標題", content:`情境${no} ${title}`, fill:"$text-main",
              fontFamily:"$font-tc", fontSize:18, fontWeight:"700",
              textGrowth:"fixed-width", width:"fill_container" })
  for (const l of lines) {
    Insert(n, { type:"text", name:"行", content:l, fill:"$text-main", fontFamily:"$font-tc",
                fontSize:13, lineHeight:1.6, textGrowth:"fixed-width", width:"fill_container" })
  }
  return n
}

const mkRow    = (parent, name) => Insert(parent, { type:"frame", name, gap:24, alignItems:"start" })
const mkBranch = (parent)       => Insert(parent, { type:"frame", name:"分支", layout:"vertical",
                                                    gap:24, alignItems:"start" })

const mkArrow = (parent, label) => {
  const a = Insert(parent, { type:"frame", name:"動作箭頭", layout:"vertical", gap:4, width:150,
                             alignItems:"center", justifyContent:"center", padding:[120,0,0,0] })
  Insert(a, { type:"icon", name:"icon", library:"lucide", icon:"arrow-right",
              width:30, height:30, fill:"$flow-line" })
  if (label) {
    Insert(a, { type:"text", name:"標籤", content:label, fill:"$flow-line", fontFamily:"$font-tc",
                fontSize:13, fontWeight:"700", lineHeight:1.4, textAlign:"center",
                textGrowth:"fixed-width", width:"fill_container" })
  }
  return a
}

const mkDelta = (parent, lines) => {
  const n = Insert(parent, { type:"frame", name:"變化重點", layout:"vertical", gap:6, width:TEXTW,
                             fill:"$info-card", cornerRadius:"$r-lg", padding:[16,20] })
  Insert(n, { type:"text", name:"標題", content:"變化重點", fill:"$text-main", fontFamily:"$font-tc",
              fontSize:14, fontWeight:"700", textGrowth:"fixed-width", width:"fill_container" })
  for (const l of lines) {
    Insert(n, { type:"text", name:"行", content:"・" + l, fill:"$text-sub", fontFamily:"$font-tc",
                fontSize:13, lineHeight:1.6, textGrowth:"fixed-width", width:"fill_container" })
  }
  return n
}

// 關閉母版繼承的疑問標註（§8）：ANNOS = 分析檔第 8 節型態 annotation 的節點 ID
const hideAnnos = (d, ANNOS) => { for (const id of ANNOS) d[id] = { enabled:false }; return d }
```

`Copy` 用法：`Copy(母版ID, 序列列ID, { name:"情境①-前態-…", descendants: hideAnnos({}, ANNOS) })`

## 13. 驗證

畫完一個情境就 `get_screenshot({ nodeId:"<該情境分區ID>" })`：

- 每一段畫面**確實不一樣**（最常見的失誤是 `descendants` 沒生效，兩張長得一模一樣）
- 說明帶與變化重點卡**沒有被拉寬**（維持 1100，文字沒變超長單行）
- 情境副本上**沒有紅框**（母版繼承的已關掉）
- 分支的每條線都接得到畫面，標籤分得出走哪條
- 畫面沒有被 `clip` 切掉；前後態的數字內部一致
- **逐格節點都登記了**（§10）：交件前實際去數 —— 這個情境畫了幾格，第 8 節就該有幾列 `scenario` 子節點；數字對不上就是漏登，不要憑印象認定已寫

最後用 `execute` 的 `Get(document,(n,c)=>Print(n.name,c.bounds.x,c.bounds.y,c.bounds.width,c.bounds.height),{depth:1})` 確認情境 root 沒有與「系統畫面」「操作流程」區塊重疊；重疊時**只移動自己建立的節點**。
