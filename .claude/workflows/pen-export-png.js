export const meta = {
  name: 'pen-export-png',
  description: '唯讀匯出：把指定 .pen 檔的畫面 frame 匯成 png ＋ 版面規格數值，並產出索引，供前端／規格代理用 Read 直接對稿',
  whenToUse: '下游代理（front-end-*-engineer、system-designer 等）需要整批看設計稿實際長相或精確對位時使用 —— 一次量好給全隊共用，比每個代理各自連 pencil 便宜。args 帶 batch／designRoot（絕對路徑）／units（penPath 直接指磁碟路徑即可，唯讀不需先在 Pencil Desktop 開啟）；args.withLayoutSpec 預設 true，會一併讀出 bounds／字級／間距。',
  phases: [
    { title: '匯出', detail: '每檔一個 worker，唯讀盤點 frame、匯出 png、讀版面規格數值' },
    { title: '索引', detail: '彙整成 _index.md（畫面 ↔ 圖檔）與 _layout-spec.md（版面數值）' },
  ],
}

// ---------------------------------------------------------------------------
// 設計稿產線的「下游交付」：.pen → png ＋ 版面規格 ＋ 索引。
//
// 【為什麼要這個】
//   .pen 是加密檔、Read／Grep 讀不了，沒有匯出時下游只能靠中介檔想像視覺。
//   它們只能靠中介檔（.md）想像畫面長相 —— 分析檔擅長記結構與決議，不擅長記視覺
//   （間距、對齊、比例、密度、元件外觀）。實測後果：切版完成後「樣式全都跟設計稿不同」。
//
//   【而且光有圖也不夠】圖能解決「長什麼樣」，解決不了「差幾 px」—— 代理只能目測比例換算，
//   誤差大又慢。實測曾把落差人工誤判成「兩個頁面行為不一致」，實際量測後才發現兩頁完全相同、
//   真正的落差在別處。所以本 workflow 同時產出兩種東西：
//     - png 圖        → 長什麼樣（視覺方向、元件外觀、狀態呈現）
//     - _layout-spec  → 差幾 px（尺寸、間距、字級、色票）
//
// 【為什麼不直接給下游代理 pencil 工具】
//   （2026-08-01 更新：前端工程代理與 system-designer 已配有 pencil 唯讀工具，可自查細節。
//     但批次匯出仍是首選）
//   1. 一次量好給全隊共用，比每個代理各自連 pencil 便宜得多。
//   2. pencil 背後是單一 Desktop 行程，多代理併發會互搶。
//   3. workflow 內的 worker 與其他角色仍然沒有 pencil 工具。
//   → 分工：整批對稿看匯出，單點細節自己查。
//
// 【args 形狀】
// {
//   batch: 'login-20260731',
//   designRoot: 'D:\\SideProject\\xxx\\.claude\\docs\\design',   // 絕對路徑，強烈建議帶
//   outputDir: '...',                                            // 選填，帶了就直接用（覆蓋 designRoot 推導）
//   withLayoutSpec: true,                                        // 選填，預設 true；false＝只出圖不讀數值
//   units: [{ penPath, penName, screenCode?, screenName?, only? }]
// }
//
// 【前置條件】目標 .pen 必須已由使用者在 Pencil Desktop 手動開啟。因此檔案多要分批，
//   不要一次丟 30 個檔 —— 使用者開不了那麼多，只會換來一整排 blocked。
// ---------------------------------------------------------------------------

const CHUNK = 4 // 比其他 fan-out（通常 5）保守：pencil 背後是單一 Desktop 行程，併發過高會互搶

const EXPORT_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['penName', 'status', 'exports'],
  properties: {
    penName: { type: 'string' },
    status: {
      type: 'string',
      enum: ['done', 'partial', 'blocked'],
      description: 'blocked＝檔案沒被 Pencil Desktop 開啟／讀不到，必須請使用者手動開啟後重跑',
    },
    blockedReason: { type: 'string', description: 'status=blocked 時必填，明講卡在哪、要使用者做什麼' },
    exports: {
      type: 'array',
      description: '本檔實際匯出的每一張圖',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['nodeId', 'frameTitle', 'kind', 'filePath'],
        properties: {
          nodeId: { type: 'string', description: '被匯出的 frame 節點 id（＝ png 檔名）' },
          frameTitle: { type: 'string', description: 'frame 在畫布上的標題逐字' },
          kind: {
            type: 'string',
            enum: ['screen', 'flow', 'scenario', 'shared', 'other'],
            description: 'screen=系統畫面 UI／flow=流程圖／scenario=功能情境序列／shared=共用元件或版面／other=其他',
          },
          screenCode: { type: 'string', description: '畫面代號（如 L-01、M-02.1），判讀不出就留空，不要臆造' },
          filePath: { type: 'string', description: 'export_nodes 回傳的絕對路徑' },
          verified: { type: 'boolean', description: '是否已抽驗這張圖不是空白／破圖' },
          note: { type: 'string', description: '異常說明：破圖、內容不完整、疑似 stale、拆分匯出等' },
          layout: {
            type: 'object',
            additionalProperties: false,
            description: '版面規格數值（僅 kind=screen 需要；讓下游能精確對位而不必目測圖片比例）',
            properties: {
              frameSize: { type: 'string', description: 'frame 尺寸，如「1440x960」' },
              elements: {
                type: 'array',
                description: '關鍵容器與元件的數值。只列「下游寫 CSS 會用到」的層級，不要逐一列出每個文字節點',
                items: {
                  type: 'object',
                  additionalProperties: false,
                  required: ['name', 'spec'],
                  properties: {
                    name: { type: 'string', description: '元件／容器名稱，如「登入卡片」「輸入框」「主按鈕」「品牌區」' },
                    spec: {
                      type: 'string',
                      description: '該元件的數值，逐項寫清楚單位。例：「寬 480、高 auto、圓角 14、內距 40、置中」「高 48、圓角 8、內距 12/16、底色 surface」',
                    },
                    typography: { type: 'string', description: '若含文字：字級/字重/色，如「22px / 700 / ink」。無文字則留空' },
                    spacingAfter: { type: 'string', description: '此元件與下一個元件的垂直間距，如「24」。最後一個或不適用則留空' },
                  },
                },
              },
              notes: { type: 'string', description: '版面規律補充：例如「表單欄位之間統一 20、標籤與框之間 8」' },
            },
          },
        },
      },
    },
    skipped: {
      type: 'array',
      description: '本檔中刻意沒匯出的 frame 與原因（例如純畫布輔助、設計疑問標註區）',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['frameTitle', 'reason'],
        properties: {
          frameTitle: { type: 'string' },
          reason: { type: 'string' },
        },
      },
    },
    notes: { type: 'string' },
  },
}

function buildPrompt(unit, outputDir, withLayoutSpec) {
  return [
    '【worker 模式｜唯讀匯出】你是被 workflow 派來處理「一個」pen 檔的 pen-drawer worker。禁止 AskUserQuestion、禁止 figma-bridge。',
    '★★ 本任務『零寫入設計稿』：只讀取、只匯出圖檔。`execute` 只准用 Get／Print 這類唯讀函式，絕對不得 Insert／Update／Copy／Replace／Move／Delete／SetVariables。唯一的寫入行為是 export_nodes 產生 png 檔。★★',
    '',
    '== 目標 ==',
    '把本檔的畫面 frame 匯出成 png，讓下游代理（前端工程、規格撰寫）能用 Read 直接看到設計稿實際長相。',
    withLayoutSpec
      ? '★ 本次**額外要讀版面規格數值**（bounds／字級／間距）：下游光看圖只能目測比例，拿到數值才能精確對位。'
      : '',
    '',
    '== 指派檔 ==',
    `- 目標 pen 檔：${unit.penPath}`,
    `- 檔名：${unit.penName}`,
    unit.screenCode ? `- 預期畫面代號：${unit.screenCode} ${unit.screenName || ''}` : '',
    `- 圖檔輸出目錄：${outputDir}`,
    unit.only ? `- ★ 只匯出這些：${unit.only}（其餘 frame 一律 skip）` : '',
    '',
    '== 步驟 ==',
    '1. 盤點本檔頂層 frame，取得每個 frame 的 nodeId 與標題逐字。用 `execute` 搭配 Get 的 visitor，一行一筆印出來：',
    '   ```js',
    '   Get(document,(n,c)=>c.depth===0&&Print(n.id,"|",n.name,"|",Math.round(c.bounds.width)+"x"+Math.round(c.bounds.height)),{depth:1})',
    '   ```',
    '   - `filePath` 可直接指向磁碟上的 .pen，**讀取不需要先在 Pencil Desktop 開啟**（已實測）。',
    '   - 讀不到檔／回傳空 → **不要重試繞路**，直接 status=blocked，blockedReason 寫「請在 Pencil Desktop 手動開啟此檔後重跑」。',
    '     （讀不到就是讀不到，重試只是燒 token。注意唯讀查詢不需要該檔先在 Pencil Desktop 開啟。）',
    '   - ⚠️ 若讀回的內容明顯不是這個檔該有的東西，可能是 filePath 格式不合當前環境導致**靜默 fallback 到目前 active 的編輯器** —— 先核對檔名／頂層節點名稱再繼續，不要接著匯出別份檔的內容。',
    '2. 判讀每個 frame 的 kind：screen（系統畫面 UI）／flow（流程圖）／scenario（功能情境序列）／shared（共用元件、版面框架）／other。',
    '   - 依標題逐字判讀，判讀不出就填 other，**不要臆造 screenCode**。',
    '3. 用 `export_nodes({ filePath, outputDir, nodeIds, format: "png" })` 匯出。',
    '   - 匯出檔名是 node id（工具行為，不可改），所以你回報的 nodeId ↔ frameTitle 對應是下游唯一的線索，**必須精確**。',
    '   - 純畫布輔助（分區色條、標題帶）、設計疑問標註區這類非畫面內容 → 放進 skipped，不要匯出。',
    '   - ⚠️ **「wrong .pen file」是一句共用的誤導訊息**，至少四種原因都會回它，照字面去查檔案路徑只會白費工夫：',
    '     ① `outputDir` 用了反斜線 → **一律改用正斜線**（`D:/.../exports/batch`）。',
    '     ② `filePath` 格式 → **一律用 Windows 原生反斜線 `D:\\...`**（`export_nodes` 只吃這種）。',
    '        ⛔ 不要「依序試到不報錯為止」：`/D:/...` 前導斜線格式**不會報錯，而是靜默讀成目前 active 的那份 .pen**，',
    '        於是你會停在第一個「沒出錯」的格式上、對著別份檔匯圖。每換一種格式都要重新核對頂層節點才算數。',
    '     ③ **一次傳太多 nodeIds** → 一次帶多個沒錯，但**每批 ≤3～5 個**；實測 12～13 個會失敗。',
    '     ④ 節點太大，2x 匯出後超過 8192px 上限 → 見下一點。',
    '   - ⚠️ **尺寸上限的處理（不要硬匯）**：若某個 frame 尺寸過大（2x 匯出後任一邊超過 8192px，例如把 8 個情境並排／堆疊的「功能情境」父框），',
    '     **改為逐一匯出其子 frame**（一個情境一張），並在該筆 note 與 notes 說明拆分方式，確保內容無遺漏。',
    '     降 scale（2 → 1 → 0.5）是備案而非首選 —— 縮圖會讓中文字糊掉，而下游正是要靠它看視覺；真要補一張俯瞰全貌的縮圖，**必須在 note 註明「文字不可讀，細節看子 frame」**。',
    '4. **抽驗**：部分環境的 Pencil 有 render stale 問題（截圖空白、bounds 偏移、problems 誤報）。',
    '   - 匯出後用 `Read` 打開至少 2 張（少於 3 張就全開）確認不是空白／破圖，把結果填進 verified 與 note。',
    '   - 沒開來看的那些，`verified` 一律填 false 並在 note 註明「未逐張開圖抽驗」。**不要因為「應該沒問題」就填 true。**',
    '   - 發現破圖 → 該張 verified=false 並在 note 說明，status 填 partial。',
    withLayoutSpec
      ? [
          '5. **讀版面規格數值**（只對 `kind=screen` 的 frame 做，其餘略過）：用 `execute` 讀該 frame 的子樹，取出下游寫 CSS 會用到的數值，填進該筆的 `layout`。',
          '   - 用 visitor ＋ Print 印緊湊的一行一筆，**不要 `Get(id)` 整棵傾印**（會爆 context）。建議：',
          '     ```js',
          '     Get("<frameId>",(n,c)=>c.depth<=3&&Print(c.depth,n.type,n.name,Math.round(c.bounds.x)+","+Math.round(c.bounds.y),Math.round(c.bounds.width)+"x"+Math.round(c.bounds.height),n.fontSize||"",n.fontWeight||"",n.fill||"",n.cornerRadius||"",n.padding||"",n.gap||""),{resolveVariables:true})',
          '     ```',
          '   - 深度不夠再逐段加深，只針對需要的子樹（例如卡片、表格列）再 Get 一次。',
          '   - 要的是：**容器與元件層級**的寬高、圓角、內距、元件之間的垂直間距、字級／字重／色。',
          '   - **不要逐一列出每個文字節點**。下游要的是「輸入框高 48、圓角 8、欄位之間間距 20」這種可直接寫成 CSS 的規律，不是節點傾印 —— 傾印既爆 token 又沒人讀得完。',
          '   - 一個畫面抓 8～15 個關鍵元件就夠（卡片、品牌區、欄位、標籤、按鈕、註記區…）。抓不完不要硬湊。',
          '   - 若發現版面有明顯規律（例如所有表單欄位間距一致），寫進 `layout.notes`，那比逐項列舉更有用。',
          '   - 設計 token（色票、圓角階、字型）若讀得到變數表，一併整理進 `layout.notes` —— 下游可直接當 CSS 變數用；多個畫面共用同一組元件規格時，寫成「共用」而不要逐畫面重複列。',
          '   - ⚠️ **部分環境的 Pencil 有 bounds 偏移的已知問題**。數值以 `Get` 讀回的實際值為準；若某個值明顯不合理（例如負數、或與相鄰元素矛盾），在 `notes` 標註存疑，**不要自己修正成「看起來合理」的數字**。',
          '6. 依 schema 結構化回報。',
        ].join('\n')
      : '5. 依 schema 結構化回報。',
    '',
    '== 鐵律 ==',
    '- 全程唯讀設計稿；不新增／不刪除／不移動任何節點；不存檔（不要嘗試 Save）。',
    '- 所有 pencil 呼叫都要帶自己的 filePath（多 worker 共用單一 pencil-server，禁用「當前開啟檔」）。',
    '- 忠實回報：匯不出來就說匯不出來，破圖就標破圖，沒抽驗就說沒抽驗，數值存疑就標存疑。',
    '  **下游會直接拿這些圖與數值當切版依據，謊報比沒有更糟。**',
  ].filter(Boolean).join('\n')
}

// --- 解析 args（可能以物件或字串化 JSON 抵達）---
let a = args
if (typeof a === 'string') {
  try { a = JSON.parse(a) } catch (e) { a = null }
}

const units = a && Array.isArray(a.units) ? a.units : []
if (!units.length) {
  log('args.units 為空，沒有東西可以匯出。')
  return { error: 'no-units', reports: [] }
}

const batch = (a && a.batch) || 'exports'
const withLayoutSpec = !(a && a.withLayoutSpec === false) // 預設開啟

// 輸出目錄：優先用呼叫端給的 outputDir，其次由 designRoot 推導。
// designRoot 一律由呼叫端（design-lead）以絕對路徑傳入 —— workflow script 沒有檔案系統存取，
// 推導不出專案根；相對路徑則會隨 worker 的工作目錄而異。
let outputDir = a && a.outputDir
if (!outputDir) {
  const root = (a && a.designRoot) || '.claude/docs/design'
  if (!a || !a.designRoot) {
    log('⚠️ args 未帶 designRoot（絕對路徑），退回相對路徑 .claude/docs/design —— 請 design-lead 補傳絕對路徑，否則 export_nodes 的輸出位置不可靠。')
  }
  const sep = root.includes('\\') ? '\\' : '/'
  outputDir = `${root}${sep}exports${sep}${batch}`
}

phase('匯出')
log(`pen → png 匯出：${units.length} 檔，輸出至 ${outputDir}（CHUNK=${CHUNK}｜版面規格 ${withLayoutSpec ? '開' : '關'}）`)

const reports = []
for (let i = 0; i < units.length; i += CHUNK) {
  const slice = units.slice(i, i + CHUNK)
  log(`chunk: ${slice.map((u) => u.penName).join(' / ')}`)
  const part = await parallel(
    slice.map((unit, j) => () =>
      agent(buildPrompt(unit, outputDir, withLayoutSpec), {
        label: `export:${unit.penName || 'unit-' + (i + j + 1)}`,
        phase: '匯出',
        agentType: 'pen-drawer',
        schema: EXPORT_SCHEMA,
      }),
    ),
  )
  reports.push(...part)
}

const done = reports.filter(Boolean)
const blocked = done.filter((r) => r.status === 'blocked')
const allExports = done.flatMap((r) => (r.exports || []).map((e) => ({ ...e, penName: r.penName })))

log(`匯出完成：${done.length}/${units.length} 檔，共 ${allExports.length} 張圖，blocked ${blocked.length} 檔`)

// --- 索引：下游代理的入口 ---
// export_nodes 用 node id 當檔名（工具行為，不可改），匯出結果是 ol9L5.png 這種。
// 沒有索引，下游代理只看到一堆亂碼檔名。索引不是裝飾，是入口。
phase('索引')

// 有沒有真的讀到版面數值 —— 用實際資料判斷，不是看 withLayoutSpec 旗標。
// （開了旗標但 worker 全部 blocked／沒有 screen 型 frame 時，不該憑空要求它寫一份空的 _layout-spec。）
const hasLayout = allExports.some((e) => e.layout && (e.layout.frameSize || (e.layout.elements || []).length))

if (allExports.length) {
  const indexPrompt = [
    '【worker 模式｜寫索引】你只做一件事：把下面的匯出結果寫成 markdown 索引檔。禁止 AskUserQuestion、禁止呼叫任何 pencil 工具。',
    '',
    `用 Write 寫到：${outputDir}\\_index.md`,
    '',
    '== 這份索引的用途（寫的時候放在心上）==',
    '下游的前端工程代理／system-designer **讀不了加密的 .pen（Read／Grep 無效）**，整批對稿時看的就是這些 png。',
    '這份索引是它們的入口 —— 它們要能從「我要做 M-02.1 新增商品」一眼找到對應圖檔的絕對路徑。',
    '',
    '== 格式要求 ==',
    '1. 開頭寫一段簡短說明：這些圖是什麼、怎麼用（用 Read 開圖檔絕對路徑），以及**警告：圖是設計稿原貌，可能包含已被後續決議推翻的畫法；欄位、規則、行為一律以 .md 分析檔為準，圖只用來看視覺**。這句警告不可省略、不可弱化。',
    '2. 主表格：畫面代號｜frame 標題｜類型｜圖檔絕對路徑｜來源 pen 檔。依畫面代號排序（英數順序），代號空白的排最後。',
    '3. 若有 verified=false 或有 note 的項目，另起一節「⚠️ 需注意的圖」列出來，寫明問題（破圖／疑似 stale／內容不完整／未抽驗／拆分匯出）。',
    '4. 若有 blocked 的檔，另起一節「未匯出」列出檔名與原因，並寫明「請在 Pencil Desktop 開啟後重跑本 workflow」。',
    '5. 若有 skipped 的 frame，用一節簡短帶過即可，不用逐條列。',
    hasLayout
      ? [
          '',
          `**另外再寫第二份檔案**：${outputDir}\\_layout-spec.md —— 版面規格數值（資料在各筆 exports[].layout，只有 kind=screen 才有）。`,
          '格式要求：',
          'a. 開頭說明用途：**這是給前端代理精確對位用的數值，不用再目測圖片比例**；並註明設計稿基準寬度（看 frameSize）。同時放一句指路：視覺長相看 `_index.md` 的圖，兩份搭配使用。',
          'b. 每個畫面一節，標題用「畫面代號 frame 標題」。節內先寫 frameSize，再用表格列出各元件：元件／尺寸與樣式／字級字重色／與下一元素間距。',
          'c. 該畫面的 `layout.notes`（版面規律、設計 token）放在該節**開頭**，不要埋在表格後面 —— 規律比逐項數值更有用。多個畫面共用同一組元件規格時，抽成「共用元件規格」一節，不要逐畫面重複列。',
          'd. 若某個數值被 worker 標為存疑（bounds 偏移風險），在該列標 ⚠️ 並**保留原值**，不要自行修正成看起來合理的數字。',
          'e. 結尾提醒：**數值是設計稿的靜態量測，實作時 RWD 斷點、元件庫預設值可能需要調整；有衝突時以能正常運作為優先**。',
        ].join('\n')
      : '',
    '',
    '== 資料 ==',
    '```json',
    JSON.stringify({ batch, outputDir, reports: done }, null, 2),
    '```',
    '',
    hasLayout
      ? '寫完回報：兩份檔案的路徑、收錄幾張圖、幾個畫面有版面數值、其中幾張圖有問題。'
      : '寫完回報：索引檔路徑、收錄幾張圖、其中幾張有問題。',
  ].filter(Boolean).join('\n')

  await agent(indexPrompt, {
    label: hasLayout ? 'index:_index.md ＋ _layout-spec.md' : 'index:_index.md',
    phase: '索引',
    agentType: 'pen-drawer',
  })
} else {
  log('沒有任何圖成功匯出，略過索引。')
}

return {
  batch,
  outputDir,
  indexPath: allExports.length ? `${outputDir}\\_index.md` : null,
  layoutSpecPath: hasLayout ? `${outputDir}\\_layout-spec.md` : null,
  requested: units.length,
  returned: done.length,
  exported: allExports.length,
  blocked: blocked.map((r) => ({ penName: r.penName, reason: r.blockedReason })),
  needsAttention: allExports.filter((e) => e.verified === false || e.note),
  reports: done,
}
