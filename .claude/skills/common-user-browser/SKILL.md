---
name: common-user-browser
description: 以 Chrome DevTools MCP 驅動瀏覽器操作與截圖的「通用」流程 —— 啟動/選頁、選單導航、標準截圖（凍結捲動）、Toast 截圖與失敗備案、視覺對稿的 computed style 實測流程、落差修不掉時的元件選型階梯與停損點（何時該自組客製元件）。各站專屬的 URL／選擇器／Toast 機制不寫在本檔，改由「目標應用 profile」提供；截圖輸出路徑與檔名由呼叫端以參數傳入。供前端子代理做 UI/UX 檢視、或依流程文件操作既有網站時使用。
---

# 瀏覽器操作指引（通用）

本技能分兩層，動手前務必先確認齊備：

- **通用方法（本檔 `SKILL.md`）**：所有網站共用的步驟與判斷邏輯。
- **目標應用 profile（另一個檔案）**：某個網站的專屬值（URL、DOM 選擇器、Toast 機制…）。下文以 `{{profile.xxx}}` 表示、執行前由代理從 profile 取值代入。
- **呼叫參數**：由呼叫端（上游流程文件或使用者）當場提供、與網站無關的值。下文以 `<xxx>` 表示。

同資料夾 `profiles/` 只放一個空白樣板：

- `_template.profile.yaml` —— 複製它做新站的 profile（每欄有 [必填]/[選用] 說明）。

**UI 元件庫的慣例 profile 放在對應的 `ui-*` skill 底下**（那些選擇器與機制都是該元件庫的專屬知識）：

| profile | 位置 | 適用 |
| --- | --- | --- |
| `element-plus.profile.yaml` | `ui-element-plus/profiles/` | Vue 3 + Element Plus |
| `bootstrap5.profile.yaml` | `ui-bootstrap5/profiles/` | Vue 3 / Angular + Bootstrap 5 |

前端子代理檢視自己剛做的頁面時，**先看專案裡有哪個 `ui-*` skill，直接取用它的 profile**，多半只需補 `selectors`。

**各站專屬 profile 不放這裡**：由使用本 skill 的專案，在自己的工作目錄用下節「Profile 自動產生（bootstrap）」流程產生 `{站名}.profile.yaml`。

---

## 動手前需要的輸入

| 來源 | 名稱 | 說明 |
|------|------|------|
| profile | `targetUrl` | 目標站台網址（也是啟動後要選取的分頁識別依據 `pageMatch`） |
| profile | `viewport` | 固定視窗尺寸 `{ width, height }` |
| profile | `selectors` | `sidebar` / `activeMenuItem` / `mainContainer` / `scrollPanel` |
| profile | `menuExpand` | 選單展開機制（`containerSelector` / `expandedClass` / `toggleAttr`；無則設 `null`） |
| profile | `toast` | Toast 觸發與偵測（`triggerFn` / `detectSelector` / `dismissSelector`；無則設 `null`） |
| profile | `navigation.policy` | `menu-click-only`（僅可點選單切頁）或 `free`（允許 navigate_page） |
| profile | `launchCommand` | （選用）瀏覽器未連線時的啟動指令 |
| 呼叫參數 | `<outputDir>` | 截圖輸出根目錄 |
| 呼叫參數 | `<filenamePattern>` | 截圖檔名規則（如 `{章節}-{小節}-step{N}`） |

> **profile 欄位不齊時**：缺 `menuExpand`／`toast`／`launchCommand` 皆可省略對應段落；缺 `selectors`／`targetUrl`／`viewport` 則無法執行，須先向使用者索取，或依下節自動產生。

---

## Profile 自動產生（bootstrap）

**觸發時機**：目標站台沒有現成 profile、專案裡也沒有可直接取用的 `ui-*` skill 慣例 profile 時，先跑本節產出一份，再進入「啟動流程」。**選擇器由代理探測 DOM 產生並當場驗證，不需人工逐格填**；只有少數政策/環境欄位需使用者一句話確認。

> 原則：**探測到的每個選擇器都要回頁面驗證命中**，驗不過就換候選再試；真的無法確認的欄位一律標 `# 待確認` 並在回報中列出，**不得靜默猜值**。

### 步驟 1：取得無法探測的欄位（問使用者，各一行）

- `targetUrl`：目標網址（或直接用目前分頁的 URL）。
- `navigation.policy`：`menu-click-only`（嚴格模擬使用者、只准點選單）或 `free`（自由切頁）—— 這是政策決定，須由使用者定。
- `viewport`：無指定就用預設 `1920 × 1080`。

### 步驟 2：開啟並載入代表性頁面

連線／選取分頁 → `resize_page`（用步驟 1 的 viewport）→ 確認 `ready`（同「啟動流程」步驟 0–4，但 viewport 用預設值，因為此時尚無 profile）。導航到一個**有側邊選單、且內容會捲動的內頁**，探測結果才完整。

### 步驟 3：探測框架與候選選擇器

`evaluate_script` 執行一次廣掃：

```javascript
() => {
  const sig = el => !el ? null : (el.id ? '#' + el.id
    : '.' + [...el.classList].slice(0, 3).join('.'));
  const framework =
    document.querySelector('.el-menu, .el-main') ? 'element-plus' :
    document.querySelector('[data-bs-target], .collapse, .navbar') ? 'bootstrap' :
    document.querySelector('.ant-menu, .ant-layout') ? 'antd' : 'unknown';
  return {
    framework,
    // 全域 Toast 觸發函數（可覆寫者才能凍結）
    globalToastFns: ['showToast', 'toast', '$message', '$notify']
      .filter(k => typeof window[k] === 'function'),
    sidebar: sig(document.querySelector(
      '.el-aside .el-menu, .el-menu--vertical, #sidebar, .sidebar, nav[role="navigation"]')),
    activeMenuItem: sig(document.querySelector(
      '.el-menu-item.is-active, .nav-link.active, [aria-current="page"], .active')),
    mainContainer: sig(document.querySelector(
      '.el-main, #mainContent, main, .app-main, [role="main"]')),
    // 真正在捲動的容器：內容溢出且 overflowY 可捲，依面積排序取前幾名
    scrollerCandidates: [...document.querySelectorAll('body *')]
      .filter(el => el.scrollHeight > el.clientHeight + 20 &&
                    /(auto|scroll)/.test(getComputedStyle(el).overflowY))
      .sort((a, b) => b.clientHeight * b.clientWidth - a.clientHeight * a.clientWidth)
      .slice(0, 5).map(sig),
    url: location.href, title: document.title,
  };
}
```

由回傳的 `framework` 決定 `menuExpand`／`toast` 走哪套。**若命中的框架剛好有對應的 `ui-*` skill，直接改用它的慣例 profile，不必自己重產一份**：

- `element-plus` → 用 `ui-element-plus/profiles/element-plus.profile.yaml`（`menuExpand: null`、`toast: null`，原因見該檔）。
- `bootstrap` → 用 `ui-bootstrap5/profiles/bootstrap5.profile.yaml`。注意該檔的 `menuExpand` 也是 `null`：Vue／Angular 專案的 collapse 由框架反應式狀態控制，直接加 `.show` class 會被 re-render 蓋掉。**只有在目標站是「不含前端框架的傳統 Bootstrap 頁面」時**，才適用 `.collapse`／`show`／`data-bs-target` 那套；`toast` 視 `globalToastFns` 而定。
- `scrollPanel` 從 `scrollerCandidates` 挑「主內容捲動區」（通常面積最大那個；若只有一個候選就用它，多個則標 `# 待確認`）。

### 步驟 4：逐格驗證候選（關鍵）

把步驟 3 選定的候選填入下面 `sel`，`evaluate_script` 確認每個都命中：

```javascript
() => {
  const sel = {
    sidebar: '<候選>', activeMenuItem: '<候選>',
    mainContainer: '<候選>', scrollPanel: '<候選>',
  };
  const out = {};
  for (const [k, s] of Object.entries(sel)) {
    if (!s) { out[k] = 'EMPTY'; continue; }
    try {
      const n = document.querySelectorAll(s).length;
      out[k] = { selector: s, count: n, ok: n >= 1 };
    } catch { out[k] = { selector: s, error: 'INVALID_SELECTOR' }; }
  }
  return out;
}
```

任何 `ok:false`／`EMPTY`／`INVALID_SELECTOR` → 換候選重試步驟 3–4；仍找不到就把該格留空並標 `# 待確認`。

### 步驟 5：Toast 探測（選用）

- `globalToastFns` 非空 → 取第一個當 `toast.triggerFn`（如 `window.showToast`），`freezeExpr` 先假設 `duration=0`。
- `detectSelector` 依框架給候選（Bootstrap `.alert, .toast.show`／Element Plus `.el-message`）。**但要真正確認需觸發一次 Toast 才看得到 DOM**；若當下不便觸發，`detectSelector` 照框架填、整個 `toast` 區塊標 `# 待確認（需觸發一次驗證）`。
- 無全域函數且非必要 → `toast: null`。

### 步驟 6：寫檔並回報

以 `_template.profile.yaml` 為骨架，填入已驗證欄位，寫到 `profiles/{站名}.profile.yaml`。回報時**分兩類列清楚**：

- ✅ 已自動填入並驗證命中：`selectors.*` 等。
- ⚠️ 待使用者確認：標了 `# 待確認` 的欄位（如 policy、多候選的 scrollPanel、未觸發驗證的 toast）。

使用者確認後即定案；此後除非目標站改版，profile 不需再動。

---

## 工具對照

| 用途 | 工具 |
|------|------|
| 列出分頁 | `mcp__chrome-devtools__list_pages` |
| 選取分頁 | `mcp__chrome-devtools__select_page` |
| 固定視窗尺寸 | `mcp__chrome-devtools__resize_page` |
| 頁面快照（取得 UID） | `mcp__chrome-devtools__take_snapshot` |
| 點擊元素 | `mcp__chrome-devtools__click` |
| 執行 JS | `mcp__chrome-devtools__evaluate_script` |
| 截圖存檔 | `mcp__chrome-devtools__take_screenshot` |
| 等待條件 | `mcp__chrome-devtools__wait_for` |

---

## 啟動流程

每個工作階段開始時執行一次（連續多份工作時只需一次）：

**步驟 0（確認/啟動瀏覽器）**：呼叫 `list_pages` 確認目標瀏覽器是否已就緒。

- **若清單中已有符合 `{{profile.targetUrl}}` 的分頁**：記錄其 `pageId`，直接跳至步驟 2。
- **若連線失敗或清單為空，且 profile 有 `launchCommand`**：以 `Bash` 執行 `{{profile.launchCommand}}` 啟動瀏覽器，等待數秒後重新 `list_pages`。
  - 出現符合分頁 → 續步驟 2。
  - 仍為空 → 提示使用者「瀏覽器已啟動，請在新視窗登入／開啟目標站台後告知繼續」，等待確認。
- **若無 `launchCommand` 又連不上**：提示使用者手動開啟目標站台後再繼續。

**步驟 2**：`select_page(pageId)` 選取該分頁為後續操作目標。

**步驟 3**：`resize_page(width={{profile.viewport.width}}, height={{profile.viewport.height}})` 固定視窗尺寸，確保所有截圖尺寸一致。

**步驟 4**：`evaluate_script` 確認頁面已完全載入：

```javascript
() => ({
  title: document.title,
  ready: document.readyState === 'complete',
  size: `${window.innerWidth}x${window.innerHeight}`
})
```

回傳 `ready: true` 才繼續。

---

## 頁面間導航規則

依 `{{profile.navigation.policy}}` 決定：

### policy = `menu-click-only`（嚴格：僅可點選單）

**禁止**使用 `navigate_page` 跳轉至任何頁面專屬路由。所有頁面切換一律透過**點擊左側選單**完成：

```
步驟 1：take_snapshot 取得目前頁面 DOM 快照
步驟 2：找到父選單項目 UID，呼叫 click 展開
步驟 3：找到目標子選單項目 UID，呼叫 click
步驟 4：evaluate_script 確認頁面已切換（標題、active class）
步驟 5：evaluate_script 確認父選單已展開（有 {{profile.menuExpand.expandedClass}}）、目標項目有 active class
步驟 6：確認導覽列狀態正確後，再進行任何截圖
```

**唯一允許 navigate_page 的時機**：頁面錯誤需重置時，回到 `{{profile.navigation.resetUrl}}` 重新進入。

### policy = `free`

允許以 `navigate_page` 直接切換頁面；截圖前仍請以 `evaluate_script` 確認目標頁已載入。

---

## 截圖存檔流程

截圖分三步驟：**JS 前處理 → CDP 截圖存檔 → JS 還原**。由 `take_screenshot(filePath)` 直接寫入磁碟，無需本機 server。

### 標準截圖

**步驟 A：evaluate_script 前處理**（展開選單、凍結捲動）

下方選擇器以 `{{profile.*}}` 代入；若 profile 未提供 `menuExpand`，略過展開選單那段。

```javascript
async () => {
  await new Promise(r => setTimeout(r, 1000)); // 等待 DOM 穩定

  // 強制展開目前頁面對應的父選單（僅在 profile 有 menuExpand 時執行）
  const activeLink = document.querySelector('{{profile.selectors.activeMenuItem}}');
  if (activeLink) {
    const col = activeLink.closest('{{profile.menuExpand.containerSelector}}');
    if (col && !col.classList.contains('{{profile.menuExpand.expandedClass}}')) {
      col.classList.add('{{profile.menuExpand.expandedClass}}');
      const toggle = document.querySelector(`[{{profile.menuExpand.toggleAttr}}="#${col.id}"]`);
      if (toggle) toggle.setAttribute('aria-expanded', 'true');
      await new Promise(r => setTimeout(r, 300));
    }
  }

  // 視窗層級捲動：只對主容器套 translateY，fixed 元素不動
  const scrollY = window.scrollY;
  const mainContent = document.querySelector('{{profile.selectors.mainContainer}}');
  if (scrollY > 0 && mainContent) {
    mainContent.style.transform = `translateY(-${scrollY}px)`;
    window.scrollTo(0, 0);
    await new Promise(r => setTimeout(r, 200));
  }

  // 面板層級捲動：對可捲動面板的子元素套 translateY
  const panel = document.querySelector('{{profile.selectors.scrollPanel}}');
  const panelScrollTop = panel?.scrollTop ?? 0;
  if (panelScrollTop > 0 && panel) {
    Array.from(panel.children).forEach(c => {
      c.style.transform = `translateY(-${panelScrollTop}px)`;
    });
    panel.style.overflow = 'visible';
    panel.scrollTop = 0;
    await new Promise(r => setTimeout(r, 200));
  }

  // 儲存狀態供還原使用
  window.__ssState = { scrollY, panelScrollTop };
  return `ready: scrollY=${scrollY} panelScrollTop=${panelScrollTop}`;
}
```

**步驟 B：take_screenshot 存檔**

```
filePath: "<outputDir>/<filenamePattern>.png"
```

**步驟 C：evaluate_script 還原**

```javascript
() => {
  const s = window.__ssState || {};

  if (s.scrollY > 0) {
    const mc = document.querySelector('{{profile.selectors.mainContainer}}');
    if (mc) mc.style.transform = '';
    window.scrollTo(0, s.scrollY);
  }

  if (s.panelScrollTop > 0) {
    const panel = document.querySelector('{{profile.selectors.scrollPanel}}');
    if (panel) {
      Array.from(panel.children).forEach(c => { c.style.transform = ''; });
      panel.style.overflow = '';
      panel.scrollTop = s.panelScrollTop;
    }
  }

  delete window.__ssState;
  return 'restored';
}
```

---

### Toast 截圖策略（僅在 profile 有 `toast` 時適用）

Toast 存活時間短（2–4 秒）。策略分五步，**凍結邏輯與觸發操作嚴格分離**，避免重複觸發出現兩個 Toast。

> **重要**：觸發按鈕的 click 只能發生一次，統一由步驟 B 的 `click` 工具執行，evaluate_script 中絕對不得再呼叫 `.click()`。

**步驟 A：evaluate_script 掛 Hook（只凍結，不觸發）**

多數 App 的 Toast 為自訂全域函數，透過覆寫它、強制不自動消失來凍結。函數名與凍結方式見 profile。

> **⚠️ 注意簽名**：`{{profile.toast.triggerFn}}` 的參數簽名為 `{{profile.toast.signature}}`。若 duration 藏在 options 物件裡，需用 `Object.assign` 合併覆寫，直接傳 `0` 通常無效。

```javascript
() => {
  const fn = {{profile.toast.triggerFn}};
  if (fn) {
    const orig = fn;
    // 依 profile.toast.freezeExpr 覆寫，使 Toast 不自動消失
    {{profile.toast.triggerFn}} = function(message, type, options) {
      orig(message, type, Object.assign({}, options || {}, { duration: 0 }));
    };
    window.__toastHooked = true;
    window.__origToast = orig;
  }
  return 'hook ready';
}
```

**步驟 B：click 工具點擊觸發元素（唯一觸發點）**

`take_snapshot` 取得 UID，再以 `click(uid)` 點擊按鈕。

**步驟 C：evaluate_script 等待 Toast 出現**

> **⚠️ 偵測選擇器**：Toast 的 DOM 樣子見 profile 的 `detectSelector`（不一定是 Bootstrap 的 `.toast`）。

```javascript
async () => {
  await new Promise(resolve => {
    const obs = new MutationObserver(() => {
      if (document.querySelector('{{profile.toast.detectSelector}}')) {
        obs.disconnect();
        resolve();
      }
    });
    obs.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] });
    setTimeout(() => { obs.disconnect(); resolve(); }, 3000);
  });
  await new Promise(r => setTimeout(r, 400)); // 等待淡入動畫
  return 'toast visible';
}
```

**步驟 D：take_screenshot 存檔**

```
filePath: "<outputDir>/<filenamePattern>-toast.png"
```

**步驟 E：evaluate_script 驗證截圖內容後還原**

> **截圖後必須驗證**：確認頁面上真的有 Toast 元素，若無則標記失敗，不得靜默略過。

```javascript
() => {
  const toastEl = document.querySelector('{{profile.toast.detectSelector}}');
  const verified = !!toastEl;
  const toastText = toastEl?.textContent?.trim() || '';

  // 還原觸發函數
  if (window.__toastHooked) {
    if (window.__origToast) {
      {{profile.toast.triggerFn}} = window.__origToast;
      delete window.__origToast;
    }
    // 關閉畫面上殘留的 Toast
    document.querySelectorAll('{{profile.toast.dismissSelector}}').forEach(el => el.remove());
    delete window.__toastHooked;
  }

  return verified ? `toast captured: "${toastText}"` : 'TOAST_MISSING: no toast element found';
}
```

若回傳 `TOAST_MISSING`，**必須在回報中標注該截圖失敗，不得假裝成功**。

**若 Toast 仍無法捕捉**：描述改為「操作成功後，畫面**短暫**顯示 Toast 訊息」，以操作後結果畫面替代，**不得聲稱截圖包含 Toast**。

---

## 截圖時機對照

| 時機 | 使用方法 |
|------|---------|
| 頁面初始載入後 | 標準截圖（A→B→C） |
| 填寫表單欄位後 | 標準截圖（自動處理面板捲動） |
| Modal / 彈窗開啟後 | 標準截圖 |
| Toast 通知出現時 | Toast 截圖策略 |
| 操作完成後 | 標準截圖 |

---

## 視覺對稿：computed style 實測（不是看，是量）

截圖只能回答「看起來像不像」。**要回答「差幾 px」，兩側都必須是量出來的** —— 這一節是強制流程，不是建議。

| 對稿的兩側 | 強制作法 | 明令禁止 |
| --- | --- | --- |
| **設計稿側** | 先查既有的 `_layout-spec.md`（`.claude/docs/design/exports/{批次}/`）；不夠再查 `.pen`（有 pencil 唯讀工具的話）；都沒有才對 png 逐像素取樣 | 目測圖片比例換算 |
| **實作側** | `evaluate_script` 跑 `getComputedStyle` 一次遍歷所有文字節點，輸出 `font-size`／`font-weight`／`line-height`／`color`；**修正後再量一次確認生效** | **讀 CSS 原始碼推論**、只截圖目視 |

### 為什麼禁止讀原始碼推論

**你看到的原始碼不等於瀏覽器最後套用的值。** 元件庫的內層選擇器、`!important` 的優先序、scoped style 邊界、載入順序 —— 任何一個都會讓推論失準。

> **實測案例**：某站全站的表單輸入框文字吃元件庫預設 16px（設計稿要求 13px），全域樣式只覆寫了浮動 label、**從沒覆寫欄位本身的文字節點**。代理靠讀 CSS 推論，**連跑兩輪對稿都回報「已對齊」**，使用者仍看得出字不對；第三輪改用 `getComputedStyle` 才在幾分鐘內抓到真因。
>
> 注意這是**流程缺陷不是資料來源缺陷** —— 設計稿明明白白寫著 13px，就算當時代理讀得到 `.pen` 也一樣發現不了，因為沒人量過實作側。

### 元件庫預設值的系統性風險

元件庫（Angular Material MDC 是最典型的，但 Bootstrap、Element Plus 同樣會）把樣式散在多層 class 上，**覆寫了 A 不代表 B 也被覆寫**。新增全域覆寫時，**同一組概念的相關 class 要一起檢查**，只改一個就會留缺口 —— 而這類缺口**只有 computed style 看得見**。

例（Material：欄位文字）：`.mat-mdc-input-element`（含 `textarea`）＋ `.mat-mdc-select-value-text` ＋ `::placeholder` 要一起處理。各元件庫的實際 class 名以專案配的 `ui-*` skill 為準。

### 對稿的五條判準

1. **規則、欄位、行為以 `.md` 分析檔為準**；`.pen` 與匯出圖只用來看視覺數值。設計稿記錄的是當初畫法，分析檔記錄的是最新決議，**衝突時分析檔贏**。
2. **設計稿沒標的東西不是落差。** 寫「設計稿未標，比照全站既有慣例」，**不要補一個推測值再宣稱已對齊**。
3. **共用元件層與畫面層的規格衝突 → 回報等裁決**，不要自己選邊。（這條講的是**規格**衝突：兩份來源對同一個元件講了不同的話。設計稿與元件庫的**架構**分歧是另一回事，見下一節，那個你有職權自己判。）
4. **改共用元件／全域樣式前先回報影響面** —— 那會波及全站，不是單一畫面的授權範圍。改完**抽驗至少 4 個不同型態的畫面**（列表頁 ×2、表單頁、另一端別各一），確認沒把原本正確的地方改壞。
5. 落差一律用既有 design token 修；沒有對應 token 就**說明後新增**，不在元件裡寫 magic number。

---

## 落差修不掉時：元件選型階梯與停損點

上一節處理的是「量出落差 → 改樣式 → 再量」。但有一種落差**不管改幾次樣式都不會收斂** —— 設計稿要的結構跟元件庫那顆元件的規範架構根本不同。這一節是為了讓你及早認出它，並且知道自己有權處理。

### 「不混用元件庫」≠「一律用現成元件湊」

專案 CLAUDE.md 與 `ui-*` skill 都會寫「只配這一套，不要混用其他元件庫」。**這句話禁止的是「引入第三方元件庫」（PrimeNG、Ng-Zorro、Ant Design、Vuetify…），這條沒有例外。它從來不是說「所有 UI 都必須用現成元件湊出來」。**

- **元件庫官方隨附的底層工具箱，算這一套的一部分。** 用它自組客製元件**仍在「只用這一套」之內，不算違規**。哪些套件算數，見專案配的那個 `ui-*` skill（各庫不同，該 skill 有寫）。
- 這是實測過最常見的誤讀。代理讀成最嚴格的那個解釋（指令模糊時保守是對的，錯在指令），於是遇到架構分歧時反覆用 CSS 硬凹，把招式試完才敢說做不到，還把「要不要自組」當成必須上呈的事。

### 選型階梯

1. **先找對應的現成元件** —— 這仍然是預設路徑，沒有改變。
2. 落差是**色值、尺寸、間距、圓角、字級** → 用 CSS／design token 覆寫解決（回上一節的量測流程）。
3. 落差是 **DOM 結構或行為模型** → **判定為架構分歧，不要硬凹 CSS**。典型徵兆：設計稿是單槽位、元件是雙槽位；設計稿沒有某個元件庫規範強制存在的部件；要關掉的東西是該元件庫設計規範的一部分。
4. **停損點：同一個落差試過 2 種 CSS／樣板解法仍無法對齊，即停止嘗試**，改判為架構分歧。

> **「還沒試完所有 CSS 招式」不等於「還不能說做不到」。** CSS 招式是無窮的，沒有停損點的話這種情境永遠不會收斂。第 3 步已判定為架構分歧時，連 2 次都不用試。

### 自組客製元件的驗收條件（不是加分項）

- 用元件庫官方底層工具箱搭建，**不得引入第三方元件庫**。
- 放共用元件目錄（如 `shared/ui/`），命名與寫法比照該目錄既有元件。
- **表單類元件必須讓既有呼叫端一行都不用改**（Angular：實作 `ControlValueAccessor`；Vue：維持 `v-model` 契約）。若某種寫法會逼呼叫端改，換一種寫法。
- **a11y 與鍵盤操作對齊被取代的原元件**（focus 管理、方向鍵、Esc、`aria-*`）—— 這是自組最容易漏的部分，元件庫本來幫你做掉的東西現在要自己補，且**要明確回報補了哪些、哪些沒補**，不要只說「已完成」。
- 補單元測試。
- 用上一節的量測流程**驗到零落差**，不接受目視判定。

### 職權與回報

- 判斷某需求無法用現成元件達成時，**自組是你的職權範圍**，不需要等使用者裁決才敢提出。
- 但**實作前先回報範圍與影響面**：波及幾個 feature、幾個呼叫點、要不要改呼叫端、既有行為會不會變。範圍確認後再動手。
- 若自組會取代**全站共用**的元件，先在單一畫面試點驗證，再推其餘 feature（與上一節判準 4 同源）。

### 另一條路：回頭修設計稿

若團隊決定「UI 一律以元件庫慣例為準」，正確做法是**回頭修設計稿**讓兩邊只剩一個真相，而不是讓實作長期背著一筆對不齊的帳。**發現架構分歧時，這個選項要跟「自組」一起提出**由使用者裁決 —— 不要預設只能改實作。

---

## 截圖失敗備案

若 `take_screenshot` 回傳錯誤，**不得省略截圖**，改為保留佔位符（Markdown 情境）並在最終回報中列出：

```markdown
![步驟 N 截圖](screenshots/{檔名}.png)
<!-- TODO: 待補截圖 -->
```

在最終回報中列出所有失敗截圖，讓使用者得知需要手動補充。

---

## 遇到問題時

- **找不到元素**：先用 `take_snapshot` 取得 DOM 快照，從快照中確認 UID 或 selector。
- **操作無回應（連續 3 次失敗）**：記錄問題，跳過該步驟，繼續下一個，最後在回報中列出。
- **Modal/Dialog 阻擋**：用 `evaluate_script` 執行 `document.querySelector('{{profile.toast.dismissSelector}}')?.click()`（或 profile 指定的關閉選擇器）關閉後繼續。
- **瀏覽器未連線**：若 profile 有 `launchCommand` 則重跑啟動流程；否則提示使用者手動開啟目標站台後重試。
