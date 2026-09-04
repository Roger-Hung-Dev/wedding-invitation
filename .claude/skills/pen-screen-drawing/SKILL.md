---
name: Pen 系統畫面繪製
description: 依 Figma 設計稿在 .pen 重繪後台系統畫面 UI 的規範 —— 值一律取自分析檔第 9 節、C-* 元件建置、畫面骨架（Navigation＋header＋內容）、表格階層與欄寬量測、表單面板、彈窗與 toast、用 Copy＋descendants 做分頁變體。當任務是「把畫面 UIUX 繪製出來」「重繪系統畫面」而非畫流程摘要時使用。
---

# Pen 系統畫面繪製

> 共用基礎（環境、作用域、Copy、遮罩、驗證）見 [[pen-authoring]]，**先遵循它**。
> 素材與欄寬來源見 [[figma-bridge-reading]]。只要流程摘要時改用 [[pen-flow-diagram]]。

## 0. ⛔ 值的唯一來源是分析檔第 9 節，不是本 skill

**本 skill 給的是「骨架與畫法」** —— 節點階層怎麼搭、該用哪個 `Insert` 參數、`Copy` 怎麼覆寫。
**具體數值與元素組成一律以分析檔第 9 節為準。**

| 這一類東西 | 來源 |
| --- | --- |
| **有哪些元素、怎麼呈現**（按鈕有沒有 icon、頂欄放什麼、操作是換頁還是彈窗） | **第 9.0 節** |
| 顏色（含每個 `$變數` 該等於哪個色碼） | 第 9.1 節 |
| 尺寸（畫面寬、側欄寬、頂欄高、列高、欄寬、圓角、內距、gap、字級） | 第 9.2 節 |
| 對齊與排列（`direction`／`justifyContent`／`alignItems`／`fill_container`） | 第 9.3 節 |
| 各畫面與代表畫面的差異 | 第 9.4 節 |

**本文以下出現的每一個數字與 `$變數名`，一律是佔位示意，不是預設值。**
第 9 節查不到的項目，照 [[pen-drawer]] 3.1 的三級留痕回報，⛔ **不要沿用本文的示意值當答案**。

### 開畫前先把色票寫成變數

第 9.1 節記的是**色碼**，本文的畫法用的是 **`$變數名`** —— 中間那一步要你自己接：

```js
GetVariables()                                   // 先看既有變數，不要重造
SetVariables({                                   // 只補「第 9.1 節有、而檔案裡沒有或值不符」的
  "primary":{type:"color",value:"<9.1 主色>"},
  "nav-bg":{type:"color",value:"<9.1 側欄底>"},
  "table-head":{type:"color",value:"<9.1 表頭底>"}
})
```

⛔ **不接這一步的後果是最難發現的那一種**：`.pen` 檔通常本來就有一套 `$primary`／`$bg-page`，
引用得到、不會報錯、畫面也不會壞 —— 只是整批用的是**檔案原本的主題色，跟 Figma 沒有關係**。
實測 10 張畫面骨架配色全錯，而每一項自我檢查都是綠燈。

**變數現值與第 9.1 節不符時不要就地改掉**：改變數會動到全檔既有節點。
在回報中列出「變數名／檔案現值／9.1 量測值」讓主控端裁決。

> **為什麼要特別寫第 0 節**：舊版把某個專案的後台長相（側欄 220、頂欄 50、畫面 1280、
> 按鈕一律 icon＋label、四顆固定 lucide icon）當成通用規範寫在這裡。實測後果是使用者看到
> 「擅自加了 icon、header 不同、選單底色不同」—— 而 worker 一個字都沒有自己發明，**是規範叫它那樣畫的**。
> **寫死的預設值比沒有預設值更危險**：沒有預設值時它會去查或回報；有預設值時它照抄，而照抄不會有任何症狀。

## 1. 順序：元件 → 主畫面 → 變體 → 彈窗

1. **先確認元件存在**（`execute`：`Get(document,(n,c)=>n.reusable&&Print(n.id,"|",n.name),{depth:3})`）。沒有就先建，**單獨一次 `execute`**，才能拿到元件與其子節點的 ID。
2. 畫**第一張完整畫面**（通常是列表頁）。
3. 其他分頁／狀態用 **`Copy` + `descendants`** 做變體，不要重畫。
4. 彈窗畫面 = Copy 底畫面 + 遮罩 + 對話框。

> 元件的子節點 ID 是覆寫的唯一入口，**建完元件的那次回傳一定要留存**。

## 2. 常見的元件切法（不是元件清單）

**這張表講的是「後台系統通常會抽哪幾個元件」，不是「你要建這幾個」。**
實際要建哪些、每個裡面有什麼，看**第 9.0 節**；尺寸看 9.2、顏色看 9.1。
⛔ **第 9.0 節沒說有的東西不要建** —— 最常見的就是「順手在按鈕裡放一個 icon 槽」。

| 元件 | 通常包含 | 覆寫點 |
| --- | --- | --- |
| `C-後台Navigation` | 側欄：標頭＋各功能項＋子項（**幾層、能不能展開，看 9.0**） | 選取態的底色與文字色 |
| `C-header` | 頂欄：**實際放什麼逐項看 9.0**（選單鈕／麵包屑／搜尋／通知／使用者／登出，各站都不同） | 依 9.4 的各畫面差異 |
| `C-button` | 按鈕：label（**icon 槽只有 9.0 明講有才建**） | `label.content`、`fill`（停用色見 9.1） |
| `C-tag` | 狀態標籤（尺寸見 9.2） | `label.content`＋`label.fill`＋外層 `fill` |
| `C-field` | 表單欄位：label＋必填星號＋input-box（**尾端 icon 看 9.0**） | label／value／icon／box 的 fill 與 stroke |

`C-field` 的覆寫組合涵蓋所有變體（**色與尺寸換成 9.1／9.2 的值**）：

```js
mkField=(parent,label,value,o={})=>{
  const dis=!!o.disabled
  return Insert(parent,{type:"ref",ref:FLD,name:"欄-"+label,width:o.width||"fill_container",descendants:{
    [FLDL]:{content:label},
    [FLDSTAR]:{enabled:o.req!==false},                                  // 非必填就關掉星號
    [FLDBOX]:{fill:dis?"$grey-fill":"$bg-white",stroke:dis?"$border-line":"$border-field"},
    [FLDVAL]:{content:value,fill:dis?"$text-placeholder":(o.filled?"$text-main":"$text-placeholder")},
    [FLDICON]:{enabled:!!o.icon,icon:o.icon,fill:"$text-sub"}           // icon 名與有無一律查 9.0，不要給預設
  }})
}
```

## 3. 畫面骨架

⚠️ **這段的前提是「側欄＋頂欄＋內容」這種版型。** 第 9.0 節說不是這樣（例如頂部橫向導覽、
整站單一工作區、或操作走抽屜而不是換頁），就照 9.0 畫，**不要硬套這個骨架**。

```js
scr=Insert(document,{type:"frame",name:"...",x,y,width:<9.2 畫面寬>,height:<9.4 該畫面高>,
                     layout:"horizontal",clip:true,fill:"$bg-page"})
  Insert(scr,{type:"ref",ref:NAV,name:"Navigation",height:"fill_container"})   // 寬度見 9.2
  right=Insert(scr,{type:"frame",name:"右側",layout:"vertical",
                    width:"fill_container",height:"fill_container",fill:"$bg-page"})
    Insert(right,{type:"ref",ref:HDR,name:"Header",width:"fill_container"})    // 高度見 9.2
    cont=Insert(right,{type:"frame",name:"內容",layout:"vertical",
                       width:"fill_container",padding:<9.2 內容區外距>,gap:<9.2 區塊間距>})
```

- 畫面寬取 9.2；**每張畫面的高度各自取 9.4**（各畫面內容長度不同，不要抓一個值套全部）
- Navigation `height:"fill_container"`、Header `width:"fill_container"`（元件本身是固定尺寸，要覆寫）
- 內容區的 `padding` 與 `gap` 取 9.2，不要沿用示意值

## 4. 表格（嚴格階層）

**表格 → 列 → 儲存格 → 內容**。儲存格**必須是 frame**，內容不可直接塞進列。

```js
mkTable=(parent,cols,heads)=>{
  const t=Insert(parent,{type:"frame",name:"表格",layout:"vertical",width:"fill_container",
                         stroke:"$border-line",strokeWidth:1,strokeAlignment:"inner",
                         cornerRadius:"$r-sm",clip:true})
  const h=Insert(t,{type:"frame",name:"thead",width:"fill_container",fill:"$table-head"})
  heads.forEach((x,i)=>{
    const c=Insert(h,{type:"frame",name:"th-"+x,width:cols[i],height:<9.2 表頭高>,
                      justifyContent:"center",alignItems:"center",padding:<9.2 表頭內距>,
                      stroke:"$border-line",strokeWidth:{right:i<heads.length-1?1:0},strokeAlignment:"inner"})
    Insert(c,{type:"text",name:"label",content:x,fill:"$text-white",fontFamily:"$font-tc",
              fontSize:<9.2 表頭字級>,fontWeight:<9.2 表頭字重>})
  })
  return t
}
const mkCell=(row,w,last,align)=>Insert(row,{type:"frame",name:"td",width:w,height:<9.2 資料列高>,
  justifyContent:align||"start",alignItems:"center",padding:<9.2 儲存格內距>,
  stroke:"$border-line",strokeWidth:{right:last?0:1},strokeAlignment:"inner"})
```

**欄寬取第 9.2 節**（`figma-reader` 已用 `bounds.x` 相減量好），不要目測也不要自己分配。
各欄寬總和要等於表格總寬（總寬同樣取 9.2）。

對齊取第 9.3 節。常見是文字左對齊、數字與金額右對齊（`justifyContent:"end"`）、狀態／日期／操作置中，
但**這是常見不是預設**：9.3 有寫就照 9.3，標「未量到」才用常見值並在回報標明。

## 5. 表單面板

```js
mkPanel=(title,btnLabel,btnOn)=>{
  const c=Insert(cont,{type:"frame",name:"面板-"+title,layout:"vertical",width:"fill_container",
                       fill:"$bg-white",stroke:"$border-line",strokeWidth:1,strokeAlignment:"inner",
                       cornerRadius:"$r-md"})
  const h=Insert(c,{type:"frame",name:"面板標題",width:"fill_container",padding:<9.2 面板標題內距>,
                    justifyContent:"space_between",alignItems:"center",
                    stroke:"$border-line",strokeWidth:{bottom:1},strokeAlignment:"inner"})
  Insert(h,{type:"text",name:"title",content:title,fill:"$text-main",fontFamily:"$font-tc",
            fontSize:<9.2 面板標題字級>,fontWeight:<9.2 面板標題字重>})
  if(btnLabel){Insert(h,{type:"ref",ref:BTN,name:"btn-"+btnLabel,
    fill:btnOn?"$primary":"$grey-fill",
    descendants:{[BTNL]:{content:btnLabel,fill:btnOn?"$text-white":"$text-placeholder"}}})}
  return Insert(c,{type:"frame",name:"面板內容",layout:"vertical",width:"fill_container",
                   padding:<9.2 面板內距>,gap:<9.2 欄位間距>})
}
```

- 面板標題列右側放該區塊的操作按鈕（可 disabled）
- 兩欄表單：`Insert(base,{type:"frame",gap:<9.2 欄位間距>,width:"fill_container"})` 內放兩個 `width:"fill_container"` 的 field
- 單欄跨滿：自己一列，field `width:"fill_container"`
- **空狀態**要畫：置中的 `$text-placeholder` 提示文字（逐字抄設計稿）

## 6. 分頁／狀態變體用 Copy

先把第一張畫面各列的關鍵子節點 ID 收成陣列，再用 JS 組 descendants：

```js
const NOI=[...], TAGR=[...], VEN=[...], ACT=[...], DELB=[...], DELL=[...]
const setRow=(d,i,no,st,vendor,act,delKind)=>{
  d[NOI[i]]={content:no}
  d[TAGR[i]]={fill:st==="已確認"?"$tag-done-bg":"$grey-fill"}
  d[TAGR[i]+"/"+TAGL]={content:st,fill:st==="已確認"?"$table-head":"$text-main"}   // 元件實例巢狀
  d[VEN[i]]={content:vendor}
  d[ACT[i]]={content:act}
  d[DELB[i]]={stroke:delKind==="off"?"$border-field":"$danger"}
  d[DELL[i]]={fill:delKind==="off"?"$text-placeholder":"$danger"}
}
const d={}; setTabs(d,"proc"); DATA.forEach((r,i)=>setRow(d,i,...r))
Copy("第一張畫面ID", document, {name:"...-處理中", x, y, descendants:d})
```

分頁的選中／未選中樣式取第 9.1 節（各站配色不同；常見是選中＝白底＋深色粗體字、未選中＝灰底淺字）。

## 7. 小元素：形式看 9.0，值看 9.1／9.2

**下表列的是這類元素「通常由哪些部分組成」，用來提醒你該去 9.0 查什麼，不是照著畫的規格。**

| 元素 | 要去查的東西 |
| --- | --- |
| 列內小按鈕 | 9.0：是文字鈕、icon 鈕，還是 icon＋文字？9.1／9.2：主要／危險／停用三態的填色邊框與高度圓角內距 |
| 分頁列 | 9.0：實際有哪幾個部件（首頁／末頁鈕不是每站都有）、筆數文案逐字。9.3：整列置中還是靠右（⛔ 這一格實測錯過 —— 看形容詞會反） |
| Checkbox | 9.2：尺寸與圓角。9.1：勾選態底色與勾號顏色 |
| **圖示按鈕** | **9.0：這裡到底有沒有 icon、是哪一顆。** ⛔ 不要套一組「編輯＝`square-pen`、刪除＝`trash-2`」的預設 —— 設計稿用別套圖庫、或那裡根本是純文字連結時，這樣畫就是自己加了東西 |
| 捲軸提示、合計區、麵包屑、頁籤 | 9.0：這站有沒有這個東西。**沒列在 9.0 的一律不要自己加** |

## 8. 保真度原則

- **筆數、日期、金額、公司名都照設計稿抄**，不要自己編。
- **元素組成也照設計稿**：設計稿沒有的 icon、麵包屑、頁籤、通知鈴鐺一律不加。
  > 「多加一個看起來很合理的東西」在自我檢查裡完全看不出來 —— 畫面不會壞，只是不像。
- 設計稿的錯誤（筆數對不上、按鈕不一致）**先回報使用者裁決**，不要自行修正；裁決後在 pen 檔註明差異。
- 設計稿是示意圖，數據**內部一致性**比像素完美重要（例：分頁標籤寫 127 筆，總計就該是「共13頁 127筆」）。

## 9. 驗證

畫完一張就 `get_screenshot({nodeId:"<右側欄ID>"})` —— 截右側欄比截整張畫面看得清楚。

- 底部 CTA 有沒有被 `clip` 切掉（內容高度 > 畫面高度）
- 表格欄寬總和是否等於表格寬
- disabled 狀態的視覺是否與 enabled 有區別
- 縮圖看起來像被切掉時，**先截該子節點確認**，不要急著改高度（常是縮圖錯覺）
- **本輪用到的每一個 `$變數`，都要能在第 9.1 節指到一列**；指不到的逐項列進回報（那就是「我自己配的」）

⚠️ **以上驗的都是「有沒有壞」，不是「像不像設計稿」。** 配色與元素組成整批錯時，這裡每一項都是綠燈。
「像不像」由主控端的比對閘門負責（見 [[design-lead]] 4.4），**那道閘門過了才可以進下一個 step**。
