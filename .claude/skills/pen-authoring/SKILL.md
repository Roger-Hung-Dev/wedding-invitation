---
name: Pen 檔繪製共用基礎
description: 用 Pencil MCP 編修 .pen 設計稿的共用基礎 —— 工具總覽與環境前置條件、execute 的作用域陷阱、Copy 與 descendants 覆寫、元件與變數慣例、多人協作下的定位與驗證。繪製任何 .pen 內容前先遵循；流程圖畫法見 pen-flow-diagram，系統畫面畫法見 pen-screen-drawing。
---

# Pen 檔繪製共用基礎（鐵律）

> 本 skill 是 `.pen` 繪製的**共用權威依據**：環境、作用域、元件、變數、驗證都收斂在此。
> **繪製流程圖**見 [[pen-flow-diagram]]；**重繪系統畫面**見 [[pen-screen-drawing]]；**從 Figma 取素材**見 [[figma-bridge-reading]]；**建立／維護共用元件庫的分類與排版**見 [[pen-shared-component-library]]。

## 1. 工具總覽與環境前置條件

`.pen` 是加密檔，**只能透過 pencil MCP 存取，絕不可用 Read／Grep／Edit**。

pencil MCP（`mcp__pencil-server__*`）目前提供這幾支，**沒有別的**：

| 工具 | 用途 |
| --- | --- |
| `get_app_state` | 取 schema 與畫布概況。四個 flag 都要帶；**沒有 schema 在脈絡中就用不了其他工具** |
| `execute` | **讀寫都走這一支**（見第 2、3 節） |
| `export_nodes` | 匯出 png |
| `get_screenshot` | 看畫布現況 |
| `get_guidelines`／`export_html`／`browser` | 少用 |

> ⚠️ **`get_editor_state`／`batch_get`／`batch_design`／`snapshot_layout` 都已不存在。** 看到任何文件、提示或舊筆記還在用這些名字，一律以本表為準 —— 照著呼叫只會拿到「工具不存在」而不是任何有用的訊息。

**環境**：pencil MCP 由 **Pencil Desktop app** 提供（使用者層級登錄，不進專案 `.mcp.json`）。連不上或回報 transport 未握手時，**直接請使用者處理，不要重試、不要繞路**；同時把不依賴 Pencil 的工作（如 Figma 分析）並行推進，不要空等。

**檔案要不要先開啟**：

- **讀取**（`execute` 的 `Get`／`Print`、`export_nodes`）：實測 `filePath` 可直接指向磁碟上的 `.pen`，**不需要先在 Pencil Desktop 開啟**。
- **繪製**（任何寫入）：仍維持鐵律 —— `.pen` **由使用者手動建立並開啟**，worker 不自建／不自開／不自存。這條與「能不能讀」無關，防的是自建 0-byte 空檔害 Pencil 回收其他已開啟檔的事故；hooks 也會硬擋。

### ⛔ `filePath` 格式：一律用 Windows 原生反斜線，而且「沒報錯」不等於「讀對檔」

```js
filePath: "D:\\SideProject\\xxx\\.claude\\docs\\designs\\進貨作業.pen"   // ✅
filePath: "/D:/SideProject/xxx/.claude/docs/designs/進貨作業.pen"        // ❌ 見下
```

**帶前導斜線的 `/D:/...` 格式會讀到 Pencil 當下的 active 檔，而不是你指定的那一份 —— 而且完全不報錯。** 實測：目標是 `進貨作業.pen`，active 檔是 `庫調單維護.pen`，拿到的是後者的節點。

⚠️ **先前多次用該格式「成功」，只是因為當時 active 檔剛好就是目標檔。**

⛔ **所以「依序試三種格式直到不報錯」是危險的程序** —— 錯的格式不會報錯，它會**安靜地回另一份檔的內容**，於是你會停在第一個「沒出錯」的格式上，然後對著錯的檔工作。要試可以，但**每試一種都必須核對過才算數**。

#### 開工前必做：核對頂層節點（一次呼叫，很便宜）

```js
Get(document,(n,c)=>c.depth===0&&Print(n.id,"|",n.name),{depth:1})
```

**比對回傳的節點 ID 與名稱**（至少 2～3 個已知節點，來源是分析檔第 8 節）。**對不上就停下來**，不要繼續 —— 換格式重試，或用 `get_app_state` 看目前 active 是哪一份，判斷 fallback 落到了哪裡。

> ⛔ **把「No node with id」當成「可能讀錯檔」，不要當成「這個節點不存在」。** 後者會讓你去重建一個其實已經存在的節點。

## 2. 起手式

```js
get_app_state({include_schema:true, include_canvas_design:true,
               include_scripts_and_shaders:false, include_browser:false})
// 接著用 execute（都要帶 filePath）：
GetVariables()                                   // 看既有變數，不要重造
Get(document,(n,c)=>n.reusable&&Print(n.id,"|",n.name),{depth:3})   // 看既有元件
```

**動手前務必先看既有元件與變數。** 專案通常已備好色彩／字型變數與 `C-*` 元件，重造會產生重複資產。

> **讀取一律用 visitor ＋ `Print` 印緊湊的一行一筆，不要 `Get(id)` 整棵傾印**（會爆 context）。深度不夠再針對需要的子樹加深。

### ⚠️ `Get(某節點, ...)` 的第一個參數**不會限制走訪範圍**

實測：傳入某個節點當第一參數，走訪的仍是**整份文件** —— 於是你拿到的是全檔統計，卻以為那是該節點底下的。**數字看起來合理，不會有任何錯誤**，這是最容易誤判的一種。

要只看某個父節點底下的，改用 `c.parentCtx` 過濾：

```js
Get(document,(m,c)=>{
  if(c.parentCtx && c.parentCtx.node && c.parentCtx.node.id===目標id) Print(m.name)
},{depth:30})
```

## 3. `execute` 的作用域陷阱（最常見的失敗）

**每次 `execute` 都是獨立作用域，JS 變數與 helper 函式不跨批次保留。**

```js
// 批次 1
mkCard = (...) => {...}      // 即使不用 const 宣告
s1 = mkSection("列表頁")

// 批次 2
s2 = mkSection("新增")        // ❌ ReferenceError: 'mkSection' is not defined
```

**正確作法**：每個批次**重新定義 helper**，並用**上一批次回傳的節點 ID 字串**來引用既有節點。

```js
const ROOT="PwwtO"                 // 用 ID，不要用變數
const mkSection=(name)=>{...}      // 每批重新定義
```

> 批次回傳的「Created nodes by name」對照表就是你下一批要用的 ID 來源，**務必留存**。

## 4. Copy 與 descendants（做變體的唯一正確方式）

`Copy` 會**重新產生所有子節點的 ID**，所以**不能**先 Copy 再 Update 子節點（ID 已經不同了）。

```js
// ❌ 錯：copied 的子節點 ID 已變，Update 會失敗
const c = Copy("screenA", document, {name:"screenB", x, y})
Update("原本的子節點ID", {content:"新內容"})

// ✅ 對：覆寫寫在 Copy 呼叫裡，key 用「原始節點」的 ID
Copy("screenA", document, {name:"screenB", x, y, descendants:{
  "原始子節點ID": {content:"新內容"},
  "原始ref的ID/元件內子節點ID": {content:"巢狀覆寫"}   // 斜線只用於元件實例巢狀
}})
```

- `descendants` 的 key 用**被複製來源**的節點 ID。
- 元件實例內的節點用 `實例ID/元件內節點ID` 路徑，可任意層數。
- 斜線**只對元件實例有效**，不是一般圖層結構的路徑。

**大量變體用 JS 生成 descendants map**，不要手寫：

```js
const NOI=["kudeD","EwSwc",...]   // 各列「編號」text 的原始 ID
const d={}
DATA.forEach((r,i)=>{ d[NOI[i]]={content:r[0]} })
Copy("screenA", document, {name:"變體", x, y, descendants:d})
```

## 5. 多人協作：檔案會在你工作期間改變

`.pen` 是**即時協作檔**。實際發生過的狀況：

- 開工時只有 5 個元件 → 畫到一半冒出 5 個別人加的畫面 → 再過一會兒**全部被刪掉**。
- `FindEmptySpace` 找到的空位，**在你畫完前可能已被別人佔用**。

**因此**：

1. 節點讀不到 / 不符預期時，**重新用 `execute` 的 `Get` 讀，不要重建**。
2. 完成一個大區塊後，用 `Get(document,(n,c)=>Print(n.id,n.name,c.bounds.x,c.bounds.y,c.bounds.width,c.bounds.height),{depth:1})` **檢查頂層節點是否重疊**。
3. 發現重疊時，**只移動自己建立的節點**，不要動別人的內容。
4. 別人刪掉的東西，**先問使用者**再決定要不要重建 —— 可能是對方正在自己重做。

## 6. 版面定位

```js
const pos = FindEmptySpace({width:1280, height:991, padding:120, direction:"right", nodeId:"上一張畫面的ID"})
Insert(document, {type:"frame", x:pos.x, y:pos.y, ...})
```

- **一律用 `FindEmptySpace`**，不要自己猜座標。
- 連續畫多張畫面時，用 `nodeId` 指向前一張，讓它們串成一列。
- 元件放上方（慣例 `y:-1400`），畫面放下方、往右往下長。
- **文件根目錄只放**：畫面 frame、`C-*` 元件、主要容器 frame。文字／按鈕／圖示不可直接放根目錄。

## 7. 建構期間掛 placeholder

```js
scr = Insert(document, {..., placeholder:true})
// ... 填內容 ...
Update(scr, {placeholder:false})     // 完成後立刻取消，不要等全部畫完
```

## 8. Schema 地雷（會直接報錯或視覺破版）

| 地雷 | 說明 |
| --- | --- |
| 文字沒有 `fill` | **預設不可見**。每個 text 都要設 `fill` |
| `width:"100%"` / `50vh` / `calc()` | **不支援**，會報錯。用 `fill_container` / `fit_content` / 固定 px |
| `padding` 設在 text 上 | 不支援。用外層 frame 包起來 |
| `alignItems:"stretch"` / `"baseline"` | 不支援 |
| 父 `fit_content` + 全部子 `fill_container` | **循環相依**，會塌成 0。父要給固定寬或改子為 `fit_content` |
| text 要換行卻沒設 `textGrowth` | 不會換行。要換行必須 `fixed-width` 或 `fixed-width-height` + `width` |
| `x`/`y` 設在 flex 子節點 | **被忽略**。要絕對定位得設 `layoutPosition:"absolute"` |
| 用 `id` 指定節點 | 無效，Pencil 一律自動產生 |
| 想放圖片用 `type:"image"` | **沒有 image 節點**。圖片是 `fill`，用 `Generate` 產生 |
| 移除框線傳 `stroke: null` | **不接受**，會報型別錯誤而且**整批 `execute` 回滾**（`strokeAlignment: null` 同樣被擋）。要移除框線傳 **`stroke: []`**（空陣列），它會**連帶清掉 `strokeAlignment`**，不必另外處理 |

> 「整批回滾」的意思是：你在同一次 `execute` 裡做的其他事**也一起沒了**。看到型別錯誤時不要只修那一行就以為其餘已生效，**整批重跑**。

## 9. 遮罩與彈窗

彈窗畫面 = 底畫面 + 遮罩 + 對話框。底畫面通常是既有畫面的 Copy。

```js
pop = Copy("底畫面ID", document, {name:"...-彈窗", x, y})
Insert(pop, {type:"rectangle", name:"遮罩", layoutPosition:"absolute", x:0, y:0,
             width:1280, height:1494, fill:"#02041699"})   // 透明度用 hex alpha
Insert(pop, {type:"frame", name:"彈窗-xxx", layoutPosition:"absolute",
             x:(1280-對話框寬)/2, y:置中y, width:對話框寬, layout:"vertical", ...})
```

- 畫面 frame 若是 `layout:"horizontal"`，遮罩與彈窗**必須 `layoutPosition:"absolute"`**，否則會被排進 flex 流。
- **fill 的透明度只能用 hex alpha**（`#02041699`），沒有獨立的 opacity 欄位可用於 fill。
- 遮罩尺寸要跟畫面一致；改畫面高度時記得一起改。

## 10. 驗證（每個區塊做完就驗，不要等最後）

| 工具 | 用途 | 成本 |
| --- | --- | --- |
| `execute` ＋ `Get` visitor（印 bounds） | 結構／尺寸／溢出檢查 | 低，優先用 |
| `get_screenshot({nodeId})` | 視覺保真度（顏色、字體、對齊） | 高，節制使用 |

**檢查清單**：

- 版面沒塌（寬高不是 0）
- 內容沒被 `clip` 切掉 → 容器要放得下
- 文字顏色與背景對比足夠
- 對齊與間距一致
- **不要用整份文件截圖驗細節**，會看不清且吃 token；截最小有意義的節點（一個 section，不是整份）

> 有問題**直接改既有節點**，不要刪掉重畫。

⚠️ **這份檢查清單驗的是「有沒有壞」，不是「像不像設計稿」。** 兩者是不同的事：配色與版面整批畫錯時，上面每一項都會通過。**沒壞掉的錯誤最難發現，因為每一道自動檢查都回綠燈** —— 「像不像」要靠主控端拿 Figma 原稿比對（見 [[design-lead]] 4.4）。

### ⚠️ 幾個「傳 null 會整批回滾」的屬性

實測：`stroke: null`、`width: null` 都會讓整個 `execute` 失敗並回滾，**不是把該屬性清掉**。

| 想做的事 | ⛔ 不要 | ✅ 改用 |
| --- | --- | --- |
| 移除框線 | `stroke: null` | `stroke: []` |
| 讓文字回到 hug | `width: null` | 一併移除 `width` 與 `textGrowth` 兩個 key |

⚠️ **`enabled: false` 的節點不要設 `width: "fill_container"`** —— 版面引擎會解析成 0 寬、
把文字折成 0×N，並持續發出「not inside a flexbox layout」警告。改用固定寬（＝父容器可用寬），
視覺一致、零警告，日後把它打開時對齊仍然成立。

### ⚠️ 單獨匯出共用元件時，畫面層額外加的節點不會出現在圖上

看到「元件裡少了某個東西」，先確認**它是不是本來就不在元件內**。

> **實測**：頂欄底部那條 1px 線是**獨立 rectangle 插在各畫面的 `main` 裡**，
> 不在 `C-header` 元件內（當初就是為了避開「inner stroke 被滿版子節點蓋掉」才這樣做的）。
> 單獨匯出 `C-header` 自然掃到 0 點 —— 而在畫面上量是 **1060/1060，一點不缺**。

**驗共用元件要分兩層量**：

| 層 | 匯出什麼 | 驗什麼 |
| --- | --- | --- |
| 元件層 | 元件本身 | 元件內部的結構與尺寸 |
| **畫面層** | 用到它的那張畫面 | **元件與周邊的接縫、畫面層補上的裝飾** |

⛔ **只量元件層會誤報「少了東西」，只量畫面層會漏掉元件內部的偏移。**
（實測那 3px 的內容偏移就只有元件層量得出來 —— 畫面上被文字渲染差異蓋過去了。）

### ⛔ 節點資料正確，畫面上仍可能什麼都沒有（持久性算圖 stale）

⚠️ **這與「被子節點蓋住」不同** —— 那是畫了但被遮住，這是**根本沒畫**。

> **實測**：兩個 `Field` 節點的 `Get` 回傳 **JSON 逐字完全相同**
> （同樣的 `fill: $text-readonly`、`content`、`fontSize: 14`、`fontWeight: "normal"`），
> 各自單獨匯出（脫離遮罩與周邊）之後 —— **一個看得到文字，一個是空白的框。**
> 重複匯出兩次結果一致（`ImageChops.difference` 的 bbox 為 `None`），**所以不是一般的快照過期**。

**判準**：

| 現象 | 是什麼 |
| --- | --- |
| 再匯出一次就出現了 | 一般快照過期，忽略即可 |
| **重複匯出都一樣，而同構節點正常** | **持久性 stale**，要動手修 |

**怎麼確認**（三步，缺一不可）：

1. `Get` 讀回目標節點，確認資料真的在
2. **把它單獨匯出**（不要匯整張畫面）—— 排除遮罩、疊層、裁切的干擾
3. **找一個已知正常的同構節點單獨匯出對照** —— 沒有對照組就分不出「這個壞了」與「這種畫法本來就不顯示」

**修法有階梯，前三階實測都無效，⛔ 不要停在前面就宣告修好**：

| # | 作法 | 實測 |
| --- | --- | --- |
| 1 | `Update` 成相同的值 | ❌ 不觸發重繪 |
| 2 | **`Delete` ＋ 原地 `Insert` 重建** | ❌ **仍是 0 像素** |
| 3 | 換掉 `fill`（改綁別的變數、或直接寫字面色碼） | ❌ 仍是 0 像素 |
| 4 | **在根層建一個暫存 frame ＋ 內容 → `Copy` 進目標位置 → 刪掉暫存** | ✅ **有效** |

⚠️ **第 2 階特別危險**：它是最直覺的修法，做完之後 `Get` 一樣讀得到、
bounding box 尺寸一樣正確（排版量測有跑，只是沒點陣化）—— **看起來每一項都修好了**。

**兩個看似合理、實測都被推翻的假設**（記下來免得再繞一次）：

| 假設 | 推翻它的證據 |
| --- | --- |
| 「新建的變數解析不出來」 | 換成**字面色碼**一樣 0 像素 |
| 「父容器原本是空的，加第一個子節點不會重繪」 | 其他「父容器原本也是空的」節點全部正常 |

**實測到的相關性**（機制不明，只記現象）：**同一個 session 裡第一批 `Insert` 的節點正常，
之後幾批 `Insert` 的壞掉；而 `Update` 既有節點一律正常。**

⛔ **每一階做完都要重新匯出驗證**，用「不透明像素數」與對照組比對 ——
文字節點的像素數在同內容同字級下是**可以逐項相等**的（實測 223×21 的節點兩邊都是 1860）。

⛔ **不要因為 `Get` 讀得到就宣告完成。** 這一類的失敗模式是：
節點清單、屬性、統計數字全部正確，交件報告每一項都是綠的，**只有畫面上少了東西**。

### ⛔ `execute` 的 `filePath` 打錯不會報錯 —— 它會靜默改到「目前開著的那個檔」

實測：帶一個**完全不存在**的路徑（例如 `H:\我的雲端硬碟\x.pen`）呼叫 `execute`，
**回傳 OK、零警告，而操作實際落在當前 active 的 `.pen` 上。**

⚠️ **所以「沒報錯」不等於「操作到對的檔」。** 一批畫錯的節點會安靜地長在另一份設計稿裡，
而那份稿看起來只是「多了一些東西」—— 沒有人會聯想到是路徑打錯。

**開工前先驗一次路徑**：用 `Get` 印出頂層節點名稱，確認就是你要改的那份稿：

```js
Print(Get(document,(n,ctx)=>(ctx.depth<=1 ? n.type+':'+(n.name||'') : undefined)).join(' | '))
```

⛔ 空白新檔會印出 0 個節點 —— **那也是合法結果**，不要把「印不出東西」當成路徑錯了。
判準是「印出來的內容是不是這份稿該有的樣子」，不是「有沒有印出東西」。

### ⚠️ 容器的 `strokeAlignment: "inner"` 會被滿版子節點蓋掉

Pencil 的 inner stroke 畫在**子節點下面**，Figma 的 inside stroke 畫在**子節點上面** —— 兩套渲染順序相反。
所以「容器設 1px inner stroke」這種在 Figma 成立的畫法搬到 pen 之後，**凡是有滿版子節點的區段，那條線就不見了**。

> **實測**：側欄設了 `stroke: $sidebar-border` `strokeWidth: 1` `inner`，
> 但選單項目寬度都是滿版 220 —— 右邊框只有下方沒有項目的空白區看得到，
> 979 列裡只有 413 列畫得出來。**畫面沒破版、沒有警告，就只是少了一條線。**

**要一條看得見的邊框，選一個**：

| 作法 | 什麼時候用 |
| --- | --- |
| **把邊框做成 flex 的一個子項**（容器轉 `horizontal`／`vertical`，內含「內容欄」＋「1px 線」） | **首選，尤其當容器高度隨畫面變動時** |
| 獨立的 1px `rectangle`，**絕對定位＋寫死長度** | 只有在該側長度固定、且不會被別的畫面重用時 |
| 把滿版子節點的尺寸縮掉邊框寬（220 → 219） | 子節點少、且不是 `fill_container` 時 |
| 改 `strokeAlignment: "outer"` | 只有容器外側有空間時才成立，會影響版面總寬 |

⛔ **絕對定位節點的 `fill_container` 不生效**（schema 明寫 absolute 時 fallback），所以「absolute rectangle ＋ `height: fill_container`」這條路**走不通** ——
高度會被固定住，而同一個元件常常在不同畫面有不同高度（實測側欄有 979／2133／2181／650／917 **五種**，寫死任何一個都只有一張對）。

⛔ **父 `fit_content` ＋ 子 `fill_container` 是循環相依**，pencil 會警告並塌成 0。
用 flex 子項這條路時，**要先把元件定義的那一軸改成固定值**（實測側欄定義高固定 566），
instance 端各自的 `height: fill_container` 完全不用動，畫面照樣撐得開。

> **實測可行的形狀**（側欄）：
> ```
> C-後台Navigation 220×566   layout: horizontal
> ├ 側欄內容欄 219×566        layout: vertical   ← 原本的子節點整批 Move 進來
> └ line-側欄右緣 1×566       fill: $sidebar-border, height: fill_container
> ```
> 好處是**不必逐一改那些 `fill_container` 子節點**（它們自動變成 219），日後新增項目也不會漏掉。

⛔ **改用其他作法之後，把容器上那個沒作用的 `stroke`／`strokeWidth` 刪掉**（`stroke: []`）。
留著的話，下一個人 `Get` 到「有設 stroke」就會以為線已經畫好了。

⚠️ **驗法一律取像素**：匯出後看邊框那一行／那一列的色碼，數它出現幾列。
`Get` 查得到 `stroke` 屬性設對了，但**查不出它有沒有被蓋住**。

### ⚠️ `ctx.bounds` 不能用來比較「不同深度的兩個節點」的相對位置

`ctx.bounds` 有系統性偏移（已知 y +50；實測也見過 x 偏移），**而且偏移量隨節點深度不同**。
所以拿它去算「A 相對於 B 差多少」——尤其 A 是淺層的絕對定位節點、B 是深層的 layout 子節點——**會得到一組看起來合理但完全錯誤的數字**。

實測：用 `ctx.bounds` 比對 8 個紅框與其目標，算出 **8 組全部錯位**（Δx 一律 244 左右）；
改用版面算式重算，實際只有 **4 組**錯位，另外 4 組是對的。**先錯判了一半。**

**要比較相對位置就用版面算式**（把 padding／gap／各節點高度加起來），那些值本身是可靠的：

```
表格 y = 50(header) + 24(內容區 pad) + 44(頁標題) + 24(gap) + 216(查詢卡) + 0(群組 gap) + 24(表格卡 pad) = 382
```

⛔ **`ctx.bounds` 適合的用途只有「同一層節點之間的重疊檢查」與「單一節點的寬高」**，
跨層的座標比較一律改用算式，或改用「把兩者放進同一個父節點再比」。

### ⚠️ 在非 active 檔上新 `Insert` 的節點，截圖會是一片空白

資料**寫得進去**、`Get` **讀得到**，就是截圖空白，且首個子節點的 `bounds` 有固定 **+50** 偏移。這不是你畫壞了。

**已驗證的繞法**：

> **先在根層建好 → `Copy` 到目標位置 → 截圖驗證 → 刪掉暫存節點。**
> `Copy` 出來的節點一切正常。

⚠️ **同源問題：`ctx.bounds` 的 y 有系統性偏移（多／少 50px 不等），會誤報內容被 `clip` 切掉。** 看到 clipped 警告時，先用截圖與自洽算式（子節點高度加總 vs 容器高度）複核，**不要盡信 bounds** —— 照著它去「修」一個沒壞的版面，只會把真的弄壞。

> 這與第 3 節「`execute` 的回傳是呼叫過程中的中間狀態」是不同的兩件事，但處理原則一樣：**改完要驗，一律拆成兩次 `execute`**。

## 11. 忠實原則

- 設計稿原註（紫色／藍色便利貼）**逐字引用**，不要改寫或摘要。
- 設計稿的矛盾／錯誤**先回報使用者裁決**，不要自行「順手修正」。
- 使用者裁決後才動手，並在 pen 檔內**記錄「原稿為 X，本檔已依決議改為 Y」**，讓後續讀者知道差異來源。
