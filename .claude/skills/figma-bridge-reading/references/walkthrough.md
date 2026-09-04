# Figma Bridge 讀取走查（實例）

以「後台_採購管理 → 採購作業-進貨作業」為例，完整記錄一次可重現的讀取流程，以及過程中踩到的坑。

---

## 步驟 0：確認檔案與頁面

```
get_metadata()
```

回傳 `fileName`、`currentPageId`、`currentPageName`、`pages[]`。
先確認目前頁面就是要分析的頁面；不是的話，node-id 仍可跨頁選取，但要留意 `currentPage` 會跟著變。

---

## 步驟 1：把 URL 的 node-id 轉成工具格式

使用者給的連結：

```
https://www.figma.com/design/hx4T6.../?node-id=1456-126698&t=...
```

`node-id=1456-126698` → **`1456:126698`**。

---

## 步驟 2：界定選取範圍（最關鍵的一步）

```
set_selection({nodeIds:["1456:126698"]})
→ {"selectedCount":1,"selectedIds":["1456:126698"]}

get_design_context({depth:1})
→ context[0].name === "採購作業-進貨作業"   ✅ 與預期相符
```

### 真實踩坑紀錄

第一次直接呼叫 `get_design_context({depth:3})`（沒有 `set_selection`），拿到 10.8 萬字元的節點樹。內容結構完整、看起來很合理，但那是 **`871:172256`「採購作業-進貨退回作業」** —— 因為 Figma 當下選取的是那個 Section。

整份匯出裡 64 次「進貨」全部是「進貨退回」的脈絡。分析完才發現範圍錯了，等於整輪白做。

**教訓**：`get_design_context` 回傳後，**第一件事是核對 `context[0].name`**。

---

## 步驟 3：逐層下探

`1456:126698` 的 `get_node` 回傳 **8,836,003 字元**，直接超出上限被丟到檔案。

改用逐層 `depth:1`：

```
depth:1 於 1456:126698  →  五個子 SECTION：
  1342:218889  採購管理-進貨-列表頁            (childCount 13)
  1361:286921  採購管理-進貨-新增進貨單        (childCount 27)
  1410:288545  採購管理-進貨-編輯進貨單（處理中）(childCount 7)
  1443:102093  採購管理-進貨-編輯進貨單（已確認）(childCount 12)
  1456:123974  採購管理-進貨-刪除進貨單        (childCount 9)
```

看到 `childCount` 就換該 id 再 `set_selection` + `depth:1`，一層一層往下。

---

## 步驟 4：總覽截圖，先看流程全貌

```
save_screenshots({items:[{
  nodeId:"1456:126698",
  outputPath:"D:\\...\\專案根\\.tmp-figma\\00-overview.png",
  scale:0.09
}]})
→ Read(".tmp-figma/00-overview.png")
```

25626 × 22111 的 Section 在 scale 0.09 下約 2300px 寬，剛好能看清「五個階段由上而下、步驟由左而右」的排列。

### 真實踩坑紀錄

- 先試了 `get_screenshot({scale:0.12})` → base64 **599,137 字元**，爆掉。
- 再試 `save_screenshots` 存到 `C:\Users\...\AppData\Local\Temp\claude\...\scratchpad\` → 被拒：
  `outputPath must be inside the MCP server working directory: D:\SideProject\fubon-stuffmall-sd`
- 最後存到專案內 `.tmp-figma\`，任務結束用 `Remove-Item -Recurse -Force` 刪掉。

---

## 步驟 5：放大讀中文內文

`get_design_context` 把 thead 的子樹截成 `childCount`，欄位名拿不到。對元件單獨截圖：

```
save_screenshots({items:[
  {nodeId:"1361:281320", outputPath:"...\\thead.png",  scale:1.5},   // 表格欄位標題
  {nodeId:"4729:215183", outputPath:"...\\note.png",   scale:1},     // 紫色便利貼
  {nodeId:"1342:218905", outputPath:"...\\dropdown.png", scale:1.2}  // 下拉選項
]})
```

讀出來的結果：

- thead → `進貨單編號 / 資料狀態 / 廠商名稱 / 最後修改日期 / 操作`
- 紫色便利貼 → 完整的「狀態說明」與「刪除按鈕邏輯」business rules
- 下拉選項 → 廠商清單 + 黃色註記「廠商的選項依實際資料顯示」

**這些資訊在節點樹裡完全拿不到，只能讀圖。**

---

## 步驟 6：量測欄位寬度（要重繪畫面時）

從 `get_design_context` 的 `bounds.x` 相減即可得欄寬，比讀圖準：

```
進貨商品表格（總寬 964）：
  商品編號 268..377 → 109
  商品名稱 377..578 → 201
  商品規格 578..678 → 100
  單位     678..737 →  59
  成本價   737..887 → 150
  進貨量   887..1035→ 148
  未稅小計 1035..1148→113
  刪除     1148..1232→ 84
```

> 注意：**規格元件（`table-title-*`）的欄寬可能與實際畫面的 instance 不同**。以實際畫面的 instance 為準，並把差異記下來回報。

---

## 步驟 7：挑出矛盾，不要自行修正

本次分析實際挑出的問題（全部回報給使用者裁決，沒有自行改動）：

1. **規格元件出現「待簽核」狀態**（`1361:281319`，tag `#faedee` / 文字 `#f5693d`），但狀態說明只定義「處理中／已確認」，列表也只有三個分頁。
2. **「全部」分頁的操作按鈕**畫成全部「查看」，與紫色註解「處理中：編輯、刪除」矛盾。
3. **「已確認」分頁**標籤寫 `已確認 (127)`，底部總計卻寫「共22頁 220筆」（那是「全部」的數字）。
4. **進貨量 vs 允收量** 三處敘述互相矛盾：
   - 紫色註記：「允收量⋯（0716 會議決議移除）」
   - 藍色筆記：「所以進貨作業的欄位只留『允收量』」
   - 查看進貨單（已確認）的表格實際顯示「允收量」

使用者裁決後才動手調整。其中 1 被要求「另外抓出來繪製並註記疑問」，2/3 被判定為設計稿畫錯要修正，4 確認為「只保留進貨量」。

---

## 步驟 8：清理

```
Remove-Item -Recurse -Force "<專案根>\.tmp-figma"
```

暫存截圖不進版控、不留在專案裡。
