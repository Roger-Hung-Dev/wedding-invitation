---
name: Pen 流程圖繪製
description: 把設計稿的畫面流程整理成 .pen 流程圖的規範 —— 分區骨架、步驟卡片、箭頭、註解色彩語意、寬度紀律與 helper 樣板（設計疑問不在流程圖，見 §8）。當任務是「整理畫面流程」「畫流程圖」「把設計稿流程繪製到 pen 檔」而非重繪 UI 時使用。
---

# Pen 流程圖繪製

> 共用基礎（環境、作用域、Copy、驗證）見 [[pen-authoring]]，**先遵循它**。
> 素材來源見 [[figma-bridge-reading]]。要畫的是**真實 UI** 而非流程摘要時，改用 [[pen-screen-drawing]]。

## 1. 這個 skill 解決什麼

把 30+ 張設計稿畫面，收斂成**一張看得完的流程圖**：每個步驟一張卡片（標題＋關鍵欄位／按鈕／狀態），用箭頭串起來，旁邊附上設計稿的原始註解。

**不是**把 Container 截圖貼進去，**也不是**逐張重繪 UI。

## 2. 版面骨架

```
進貨作業-流程圖 (root, 深色畫布, vertical, width 固定)
├─ 主標題帶            fill: $canvas-band (#3065aa)
├─ ① 列表頁            fill: $sec-bg
│   ├─ 區塊標題（色條＋文字）
│   ├─ 步驟列 (horizontal, alignItems:"center")
│   │   卡片 →箭頭→ 卡片 →箭頭→ 卡片
│   └─ 註解（紫／藍／粉）
├─ ② 新增…（可含多個「子流程」，各自 子標題＋步驟列＋註解）
└─ ③④⑤ …
```

> ⛔ **不要再加一個「設計疑問／待討論」分區當最後一區**（舊版骨架有，已廢除，理由見 §8）。

- root `fill:"$canvas-dark"`、`clip:true`、`layout:"vertical"`、`gap:40`、`padding:48`
- 每個分區 `fill:"$sec-bg"`、`cornerRadius:"$r-lg"`、`padding:26`、`gap:18`
- 分區編號用 ①②③ 前綴，方便口頭指涉

## 3. 寬度紀律（實測踩過的坑）

**root 寬度由「最寬的那一列」決定，不要開太寬。**

- 卡片固定 `width:280`、`gap:12`、箭頭 `width:44`
- 一列 N 張卡片的寬度 ＝ `N*280 + (N-1)*44 + (2N-2)*12`
  - 4 張 → 1324｜5 張 → 1672
- **root 寬 1500** 時，分區內可用寬 ≈ 1352 → **一列最多 4 張卡片**
- 超過 4 張就**拆成兩列**（例：「編輯發票」「刪除發票」各一列），不要放寬 root

> **為什麼**：註解是 `width:"fill_container"`，root 開到 2600 會讓註解變成 2400px 寬的單行，一行字太長完全不能讀。**寬度紀律是為了註解的可讀性。**

## 4. 卡片色彩語意

| tone | 標題底色 | 用途 |
| --- | --- | --- |
| （預設） | `$band-sub` `#a7abac` | 一般畫面／步驟 |
| `popup` | `$primary` `#0093c1` | 彈窗、下拉、對話框 |
| `end` | `$table-head` `#00a59b` | 成功結果、流程終點 |
| `err` | `$danger` `#eb4751` | 檢核失敗、錯誤狀態 |

卡片內容行只放**關鍵資訊**：畫面標題、查詢欄位、表格欄位、按鈕、狀態轉換。不要抄整個畫面。

## 5. 註解色彩語意（對應設計稿）

| kind | 底色 | 文字 | 對應設計稿 | 內容要求 |
| --- | --- | --- | --- | --- |
| `purple` | `$note-bg` `#763dd8` | `$note-text` | 紫色便利貼 | **逐字引用**業務規則 |
| `info` | `$info-card` `#f4fbff` | `$text-main` | 淺藍情境說明 | 逐字引用 |
| `open` | `$note-open` `#f8b6a8` | `$text-main` | 粉紅／紅字待討論 | 疑問＋**影響範圍** |

**設計疑問（`open`）要寫清楚三件事**：疑問本身、設計稿原文出處、**對 Table Schema／流程的影響**。只寫「待確認」對後續沒有幫助。

疑問一旦被使用者裁決 → **把該註解從 `open` 改成 `purple`**，內容改寫成決議規則，並註明「原稿為 X，本檔已依決議改為 Y」。

## 6. Helper 樣板（每個 `execute` 重新貼一次）

```js
const ROOT="<root節點ID>"
const mkSection=(name)=>{
  const s=Insert(ROOT,{type:"frame",name,layout:"vertical",gap:18,width:"fill_container",
                       fill:"$sec-bg",cornerRadius:"$r-lg",padding:26})
  const h=Insert(s,{type:"frame",name:"區塊標題",gap:10,alignItems:"center",width:"fill_container"})
  Insert(h,{type:"rectangle",name:"色條",width:5,height:24,fill:"$primary",cornerRadius:"$r-sm"})
  Insert(h,{type:"text",name:"文字",content:name,fill:"$text-white",fontFamily:"$font-tc",fontSize:22,fontWeight:"700"})
  return s
}
const mkRow=(parent,name)=>Insert(parent,{type:"frame",name,gap:12,alignItems:"center"})
const mkCard=(parent,title,lines,tone)=>{
  const c=Insert(parent,{type:"frame",name:"卡-"+title,layout:"vertical",width:280,fill:"$bg-white",
                         cornerRadius:"$r-md",clip:true,stroke:"$card-line",strokeWidth:1,strokeAlignment:"inner"})
  const h=Insert(c,{type:"frame",name:"標題",width:"fill_container",padding:[9,12],alignItems:"center",
                    fill:tone==="popup"?"$primary":(tone==="end"?"$table-head":(tone==="err"?"$danger":"$band-sub"))})
  Insert(h,{type:"text",name:"標題文字",content:title,fill:"$text-white",fontFamily:"$font-tc",fontSize:15,fontWeight:"700"})
  const b=Insert(c,{type:"frame",name:"內容",layout:"vertical",gap:5,padding:[12,14],width:"fill_container"})
  for(const l of lines){Insert(b,{type:"text",name:"行",content:l,fill:"$text-sub",fontFamily:"$font-tc",
                                  fontSize:13,lineHeight:1.5,textGrowth:"fixed-width",width:"fill_container"})}
  return c
}
const mkArrow=(parent,label)=>{
  const a=Insert(parent,{type:"frame",name:"箭頭",layout:"vertical",gap:2,width:44,
                         alignItems:"center",justifyContent:"center"})
  Insert(a,{type:"icon",name:"icon",library:"lucide",icon:"arrow-right",width:26,height:26,fill:"$flow-line"})
  if(label){Insert(a,{type:"text",name:"標籤",content:label,fill:"$flow-line",fontFamily:"$font-tc",
                      fontSize:11,lineHeight:1.3,textAlign:"center",textGrowth:"fixed-width",width:"fill_container"})}
  return a
}
const mkNote=(parent,title,lines,kind)=>{
  const bg=kind==="info"?"$info-card":(kind==="open"?"$note-open":"$note-bg")
  const tc=kind==="purple"?"$note-text":"$text-main"
  const n=Insert(parent,{type:"frame",name:"註解-"+title,layout:"vertical",gap:8,width:"fill_container",
                         fill:bg,cornerRadius:"$r-lg",padding:[18,22]})
  Insert(n,{type:"text",name:"註解標題",content:title,fill:tc,fontFamily:"$font-tc",fontSize:15,
            fontWeight:"700",textGrowth:"fixed-width",width:"fill_container"})
  for(const l of lines){Insert(n,{type:"text",name:"行",content:l,fill:tc,fontFamily:"$font-tc",
                                  fontSize:13,lineHeight:1.6,textGrowth:"fixed-width",width:"fill_container"})}
  return n
}
const mkSubHead=(parent,txt)=>{
  const h=Insert(parent,{type:"frame",name:"子標題-"+txt,gap:8,alignItems:"center",
                         width:"fill_container",padding:[6,0,0,0]})
  Insert(h,{type:"rectangle",name:"點",width:3,height:16,fill:"$flow-line",cornerRadius:"$r-sm"})
  Insert(h,{type:"text",name:"文字",content:txt,fill:"$flow-line",fontFamily:"$font-tc",fontSize:16,fontWeight:"700"})
  return h
}
```

## 7. 需要的變數（不存在就先 SetVariables）

⚠️ **這些是流程圖自己的視覺語言（卡片、色帶、註解），不是產品的配色** —— 所以這裡可以有固定值，
與 [[pen-screen-drawing]] 第 0 節「值一律取自分析檔第 9 節」不衝突：那條管的是**重繪產品畫面**。
⛔ 反過來也成立：**畫產品畫面時不要沿用這裡的色票**。


**這份清單分兩群，來源不同，不要混著建。**

### 7.1 流程圖自己的（固定值，與設計稿無關）

```js
SetVariables({
  "canvas-dark":{type:"color",value:"#22242a"},   // 畫布底
  "sec-bg"     :{type:"color",value:"#3a3a3a"},   // 分區底
  "band-sub"   :{type:"color",value:"#a7abac"},   // 子標題帶
  "note-open"  :{type:"color",value:"#f8b6a8"},   // 未決註解
  "note-bg"    :{type:"color",value:"#763dd8"},   // 註解便利貼
  "note-text"  :{type:"color",value:"#eeeeff"}
})
```

### 7.2 有分析檔第 9.1 節就取它的量測值（**不要用本文的示意值**）

`primary`／`table-head`／`danger`／`card-line`／`info-card`／`flow-line`／`canvas-band`／`font-tc`／`r-*`

這幾個**在產品畫面上也會用到**，流程圖沿用同一組才不會出現「流程圖的主色與畫面的主色不一樣」。
先 `GetVariables()` 看有沒有，沒有就依 9.1 建；**分析檔沒有第 9 節時（例如只跑 `draw-flow` 的 job）才用你判斷合理的值，並在回報標明是自配的**。

> ⚠️ **這一節原本是一份混在一起的清單，實跑就分岔了**：worker 把 `card-line` 建成 `#dfe4e5`（9.1 的量測值）而不是本文原本寫死的 `#e3e6e7`，`canvas-band` 也取了 9.1 的藍帶 `#3065aa` —— 兩個都是對的判斷。
> 但 `band-sub` 照本文建成 `#a7abac`，而該份設計稿的灰帶其實是 `#494a57`，於是**藍帶對得上設計稿、灰帶對不上**。
> ⛔ **不要據此把 `band-sub` 改成 `#494a57`** —— 分岔的原因是清單沒分群，不是某個值填錯。分群之後 `band-sub` 明確屬於「流程圖自己的」，`#a7abac` 就是正確答案。

## 8. 分區的內容組織

每個分區依序：**子標題（若有多條子流程）→ 步驟列 → 該分區的註解**。

- 主線先畫，子流程與分支情境跟在後面
- 子流程用 `mkSubHead` 標示（例：「子流程：新增進貨商品」「分支情境（CTA）」）
- 註解緊跟在它所解釋的步驟列後面，不要全部堆到最後

### ⛔ 不要建「設計疑問／待討論」分區

**流程圖裡不設疑問彙總分區。** 設計疑問的家在**系統畫面旁邊**（見 [[design-question-curator]] 用法 A），完整清單則由「設計疑問對照表」承接。

**為什麼改掉**：疑問卡集中掛在流程圖底下時，**看畫面的人不會翻過去**。實測一份 `.pen` 有 18 張疑問卡全在流程圖的疑問分區、畫面上只有 10 題有紅框 —— 從畫面出發的人會以為只有 10 題，**而少掉的 8 題不會有任何症狀**。

流程步驟旁該解釋什麼就照 §5 用 `open` 註解寫（那是**這個步驟**的待討論點，緊跟在它解釋的步驟列後面）；但**不要把全稿的疑問彙整成一個分區**。真正要被逐題結案追蹤的疑問，一律以畫面旁的疑問卡為準。

## 9. 驗證

畫完一個分區就 `get_screenshot({nodeId:"<該分區ID>"})`，確認：

- 卡片沒被切掉、註解沒有超長單行
- 一列卡片沒有超出分區寬度（超出就拆列）
- 色彩語意正確（彈窗藍、終點綠、錯誤紅、疑問粉）

**不要截整份文件驗細節**，看不清楚。
