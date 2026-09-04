export const meta = {
  name: 'figma-pen-team',
  description: '設計稿產線：每個 job 依自己的 steps（read / draw-flow / draw-screen / draw-scenario / annotate）串成一條鏈，job 之間並行',
  whenToUse: '由 design-lead 在寫出 _jobs.json 後呼叫。args 直接帶 _jobs.json 的內容。每個 job 的 steps 可長可短（1～5 個），job 之間互不等待；draw-scenario 需排在 draw-screen 之後。⚠️ 含 draw-screen 且其後還有 step 的 job，會在 draw-screen 完成後停下來等主控端的比對閘門（design-lead 4.4），要帶 gateCleared 再呼叫一次才會往下走。',
  phases: [
    { title: 'Read', detail: 'figma-reader 讀 Figma、產出分析檔' },
    { title: 'Draw', detail: 'pen-drawer 依分析檔繪製流程骨架／畫面 UI／功能情境' },
    { title: 'Annotate', detail: 'design-question-curator 把設計疑問釘到畫面上' },
  ],
}

// ---------------------------------------------------------------------------
// 設計稿產線（design-lead 團隊）的編排。
//
// 【與舊版 figma-pen-fanout-draw 的差異】
//   舊版：一個 pen 檔一個全能 worker，從讀 Figma 到繪製到標疑問全包。
//   本版：職責拆成三個 worker，階段間靠「分析檔」交接（見 design-handoff-contract）。
//         每個 job 的 steps 可自由組合，長度不同也互不影響。
//
// 【前提】
//   - 所有目標 pen 檔已由使用者在 Pencil Desktop 手動建立並開啟（worker 不自建／自開／自存）。
//   - design-lead 已把 _jobs.json 寫到 .claude/docs/design/{batch}/，本 workflow 的 args 就是它的內容。
//
// 【args 形狀】＝ _jobs.json（見 design-handoff-contract 第三節）
// {
//   batch: 'role-maint-20260726',
//   source: { figmaLink, fileKey, fileName, note },   // 批次預設；job 可自帶 source 整份覆蓋（跨檔批次）
//   jobs: [{ id, screen, penPath, analysisPath, figmaNodeIds, steps }],
//   gateCleared: true | ['job-id', ...]               // 選填，見下方「比對閘門」
// }
//
// 【比對閘門（design-lead 4.4）】
//   draw-screen 之後、其餘 step 之前，主控端要把 Figma 與 pen 的畫面逐項比對色碼與元素組成。
//   這道閘門只有主控端做得了 —— worker 各自只有一半工具（pen-drawer 沒有 figma-bridge，
//   figma-reader 沒有 pencil），而 workflow 自己不能 AskUserQuestion。
//
//   本 script 的作法：job 跑完 draw-screen 後，若其後還有 step 且該 job 未被 gateCleared 放行，
//   就「停在這裡」並回報 gatePending。主控端驗過之後，用「剩下的 steps」＋ gateCleared 再呼叫一次。
//
//   ⛔ 為什麼要做成 script 裡的停點，而不是 skill 裡的一段叮嚀：
//      叮嚀跳過去不會有任何症狀 —— 畫面照樣產出、每個 worker 照樣回報 done，
//      配色與元素組成整批錯時所有自我檢查都是綠燈。實測就是這樣讓 10 張畫面全錯。
// ---------------------------------------------------------------------------

const NODE_LIST = {
  type: 'array',
  description: '本階段產出的節點',
  items: {
    type: 'object',
    additionalProperties: false,
    required: ['name', 'nodeId'],
    properties: {
      name: { type: 'string' },
      nodeId: { type: 'string', description: 'pen 檔內的節點 ID' },
    },
  },
}

const QUESTION_LIST = {
  type: 'array',
  description: '設計疑問，逐項（三要素缺一不可）',
  items: {
    type: 'object',
    additionalProperties: false,
    required: ['no', 'question', 'source', 'impact'],
    properties: {
      no: { type: 'string', description: '題號（與分析檔第 7 節一致）' },
      question: { type: 'string', description: '疑問本身' },
      source: { type: 'string', description: '原文出處（含 Figma node id）' },
      impact: { type: 'string', description: '對 Table Schema / 流程的影響' },
    },
  },
}

const BASE = {
  status: {
    type: 'string',
    enum: ['done', 'partial', 'blocked'],
    description: 'done=完成並自驗過；partial=部分完成；blocked=因缺資訊/環境卡關停下',
  },
  needsDecision: { type: 'array', description: '需要使用者裁決的事項', items: { type: 'string' } },
  notes: { type: 'string', description: '其他補充（卡關原因、缺什麼資訊等）' },
}

const READ_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['analysisPath', 'status', 'designQuestions', 'measurement', 'needsManualCheck'],
  properties: {
    analysisPath: { type: 'string' },
    screen: { type: 'string' },
    readNodes: { type: 'array', items: { type: 'string' }, description: '讀了哪些 Figma node id' },
    designQuestions: QUESTION_LIST,
    // 隱藏圖層在 Figma API 裡是「不存在」而不是「visible:false」，所以「複本 B 少一塊」
    // 與「設計師忘了畫」在回傳裡長得一模一樣，worker 無從判斷。做成必填欄位，是因為
    // 這是整條鏈上唯一能指出「這裡可能少東西」的線索 —— 而少掉的東西沒有形狀，
    // 不主動列出就永遠不會有人發現（規格會很完整，只是缺一條顯示條件的業務規則）。
    needsManualCheck: {
      type: 'array',
      description: '複本之間有無不一致、判斷可能是隱藏圖層而非缺漏的區塊。只有主控端查得到（要使用者在 Figma 選取該圖層後跑 get_selection）。空陣列代表沒發現，不要拿它當免填欄位',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['screen', 'missingBlock', 'comparedWith'],
        properties: {
          screen: { type: 'string', description: '哪張畫面（含 node id）' },
          missingBlock: { type: 'string', description: '未出現的區塊是什麼' },
          comparedWith: { type: 'string', description: '拿哪張複本比對出來的（含 node id）' },
          impactIfReal: { type: 'string', description: '若真的是缺漏，對資料模型或流程的影響' },
        },
      },
    },
    // 第 9 節的量測留痕。做成必填欄位，是因為「沒量到」若只能靠散文自陳，
    // 就會變成一句「已完成」帶過，而下游拿不到色值時只會自己編一套（實測 10 張畫面全錯）。
    measurement: {
      type: 'object',
      additionalProperties: false,
      required: ['section9Written', 'section90Written', 'section921Written', 'textGroupsFound', 'section922Rows', 'tablesFound', 'tablesWithPerColumnSpec', 'tablesMissingTextWidthMode', 'paletteRowsMissingVariableName', 'formFieldsWithoutSampleValue', 'heightReconciled', 'notMeasured'],
      properties: {
        section9Written: { type: 'boolean', description: '第 9 節（9.1～9.4）是否已寫入分析檔' },
        // 9.0 單獨拉一個欄位，是因為它缺了不會讓下游停工 —— 下游「畫得出來」，
        // 只是照繪製 skill 的示意值補元件，產出多了稿上沒有的 icon／麵包屑，而且不會有任何症狀。
        tablesFound: { type: 'number', description: '該批次畫面上一共有幾張表格（列表表格、明細表、檔案清單…各算一張）' },
        formFieldsWithoutSampleValue: { type: 'array', items: { type: 'string' }, description: '⛔ 第 2.x 表單欄位表中「示意值（逐字）」欄是空的欄位清單（格式「畫面代號／欄位標籤」），空陣列代表全部都填了。⚠️ 畫面上真的是空白的欄位要記成「（空）＋placeholder 逐字」而不是留白 —— 留白與漏量長得一模一樣。實測發生過：一張編輯頁 4 個欄位的值整批沒收（單號／操作者／日期／備註），欄位表的標籤·型態·必填·位置·樣式全都有，唯獨沒有「裡面寫著什麼」，而少了那一欄的欄位表單看毫無異狀，下游只能畫成空框，空框在版面上也完全正常' },
        tablesMissingTextWidthMode: { type: 'array', items: { type: 'string' }, description: '⛔ 第 2.x 各表格中，逐欄規格「缺少『文字寬度模式』（textAutoResize）欄」的表格節名清單，空陣列代表全部都有。實測發生過：4 張表只有第一張填了這一欄，其餘三張整欄消失 —— 每張表單獨看都很完整，要並排才看得出來。缺這一欄的後果是下游把儲存格文字鎖寬，Figma 本來就溢出 padding 的那幾格會變成換行、整列跑版' },
        paletteRowsMissingVariableName: { type: 'number', description: '⛔ 第 9.1 色票表中「對應的 pen 變數名」只寫「待建」而沒有寫出名字的列數，應為 0。「待建」指的是 pen 裡還沒建立這個變數，不是還沒想好名字；沒有名字下游會自己取，於是同一個顏色在不同批次叫不同名字，而每一批單獨看都正常' },
        tablesWithPerColumnSpec: { type: 'number', description: '其中有幾張已用第 2.x 的「表格類欄位」格式逐欄記下寬／儲存格對齊／文字對齊／內距。⛔ 應等於 tablesFound —— 少了就是有表格被記成一句散文（實測發生過：同一份分析檔裡列表表格用表格記、明細表用一句欄位名帶過，下游九欄的寬與對齊全部自配，而且加起來剛好等於表格總寬，沒有任何數字對不上）' },
        textGroupsFound: { type: 'number', description: '所有 TEXT 節點依 fontSize/fontWeight/fontFamily/fills 分群後的群數（本 job 的每張畫面各自分群後取聯集）—— 這是「有幾種文字元素」的機械答案，不是你歸納的。⛔ 只分代表畫面會漏掉「只在其他畫面出現」的元素，而那種漏法在代表畫面上完全看不出來：實測必填星號在列表頁是 enabled:false 所以不出現，只在四個彈窗有，真值 16px/700/Roboto/#0093c1（藍），下游沒依據就畫成 14px/500/紅色' },
        section922Rows: { type: 'number', description: '第 9.2.2 節（逐元素文字規格）實際寫了幾列。⛔ 應等於 textGroupsFound；少了就是有元素沒記錄，下游會一律套預設字級' },
        section921Written: { type: 'boolean', description: '第 9.2.1 節（容器階層樹）是否已寫入，且每個代表畫面各一棵樹、樹末附高度驗算式' },
        heightReconciled: { type: 'boolean', description: '用容器樹算出來的畫面總高是否等於 9.4 記的畫面高度。⛔ 對不上就是還有一層容器沒走到，不要當成捨入誤差 —— 這個算式是全對或全錯，不會差幾 px' },
        heightMismatch: { type: 'array', items: { type: 'string' }, description: '對不上的畫面，逐筆寫「畫面名／算出來多少／9.4 記多少／差幾 px」。空陣列代表全部對得上' },
        section90Written: { type: 'boolean', description: '第 9.0 節（元件組成與呈現方式）五類是否逐項寫齊：頂欄內容／側欄層級與選取態／各按鈕有無 icon／各操作呈現方式（換頁·彈窗·抽屜·就地展開）／列表列操作區形式。設計稿沒有的要寫「無」，留空不算寫齊' },
        measuredItems: { type: 'array', items: { type: 'string' }, description: '已量到的項目（元件組成／色票／骨架／對齊／逐畫面差異）' },
        notMeasured: {
          type: 'array',
          description: '未量到的項目，逐項標明類別 —— 空陣列代表全部量到，不要拿它當免填欄位',
          items: {
            type: 'object',
            additionalProperties: false,
            required: ['item', 'kind', 'reason'],
            properties: {
              item: { type: 'string' },
              kind: { type: 'string', description: 'missing-in-design（缺料，設計稿沒畫，要問設計師）／not-explored（漏量，自己沒展開，再跑一次就有）／unknown（分不出是哪一種）' },
              reason: { type: 'string', description: '找過哪些節點、為什麼判成這一類' },
            },
          },
        },
      },
    },
    ...BASE,
  },
}

const DRAW_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['penPath', 'step', 'status', 'drawnNodes', 'hiddenInVariant', 'fidelity', 'coverage', 'fabricated'],
  properties: {
    penPath: { type: 'string' },
    step: { type: 'string', description: 'draw-flow / draw-screen / draw-scenario' },
    drawnNodes: NODE_LIST,
    // 「這張變體關掉了哪些區塊」目前只存在於 .pen 裡，中介檔沒有。
    // 做成必填欄位，是因為它若只能靠散文自陳，就會被一句「已完成」帶過 ——
    // 而下游看到的「這張畫面沒有這塊」與「漏畫了」長得一模一樣，沒有任何東西會報錯。
    hiddenInVariant: {
      type: 'array',
      description: '本輪用 descendants 設成 enabled:false 的畫面區塊（不含 design-question-curator 的疑問標示／徽章）。空陣列代表沒關掉任何區塊，不要拿它當免填欄位',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['name', 'nodeId', 'reason'],
        properties: {
          name: { type: 'string' },
          nodeId: { type: 'string', description: 'pen 檔內的節點 ID' },
          reason: { type: 'string', description: '為什麼這張畫面不顯示它' },
        },
      },
    },
    // 「像不像設計稿」沒有任何一道自動檢查驗得到（自我截圖只驗有沒有破版）。
    // 做成必填欄位，是把「我用了自己配的值」從散文自陳變成填不掉的格子。
    //
    // ⚠️ draw-flow 例外：流程圖有自己的視覺語言（pen-flow-diagram §7 的固定色票），
    //    那些變數本來就不該對到第 9.1 節。實跑過一次 draw-flow 老實把 $canvas-dark／$sec-bg
    //    等 6 個流程圖變數填進 unboundVariables —— 它沒做錯，是欄位問了一個對它不適用的問題。
    //    誤報會訓練人忽略這個欄位，那等於整個機制失效，所以三個欄位都寫明 draw-flow 怎麼填。
    fidelity: {
      type: 'object',
      additionalProperties: false,
      required: ['paletteBound', 'unboundVariables', 'notInSection90'],
      properties: {
        paletteBound: { type: 'boolean', description: '開畫前是否已依分析檔 9.1 跑過 GetVariables/SetVariables，讓用到的變數等於量測色碼。draw-flow 不適用（流程圖用自己的色票），一律填 true 並在 notes 註明「draw-flow 不綁 9.1」' },
        variableDiffs: {
          type: 'array',
          description: '檔案現值與 9.1 不符、但未就地改動而交主控端裁決的變數（改變數會動到全檔既有節點）',
          items: {
            type: 'object', additionalProperties: false,
            required: ['name', 'fileValue', 'measuredValue'],
            properties: { name: { type: 'string' }, fileValue: { type: 'string' }, measuredValue: { type: 'string' } },
          },
        },
        unboundVariables: { type: 'array', items: { type: 'string' }, description: '本輪用到、但在 9.1 指不到對應列的 $變數（＝這幾個是我自己配的）。空陣列代表全部有依據，不要拿它當免填欄位。⛔ draw-flow 一律填空陣列 —— pen-flow-diagram §7 那組流程圖專用色票（canvas-dark／sec-bg／band-sub／note-open／flow-line…）本來就不對到 9.1，填進來是誤報' },
        notInSection90: { type: 'array', items: { type: 'string' }, description: '畫了但 9.0 沒列到的元素（icon／麵包屑／頁籤／通知鈴鐺／更多選單…）。原則上應為空 —— 有東西就要說明為什麼非畫不可。draw-flow 不適用（流程圖畫的是流程不是畫面），一律填空陣列' },
      },
    },
    // 「只畫了一部分」是這條產線最不會被發現的失敗 —— 畫出來的每一張都對，
    // 沒畫的那些不會留下任何空缺。實測一輪：分析檔 9.4 列了 25 張畫面，只畫了 14 張，
    // 而 drawnNodes 有 19 筆、每一筆都正確，沒有任何數字對不上。
    // 比照 annotate 的 inventory，把「應該有幾張」做成填不掉的格子。
    coverage: {
      type: 'object',
      additionalProperties: false,
      required: ['screensInSpec', 'screensDrawn', 'notDrawn'],
      properties: {
        screensInSpec: { type: 'number', description: '分析檔第 9.4 節逐畫面差異列出的畫面總數（實際去數，這是「應該有幾張」）' },
        screensDrawn: { type: 'number', description: '本輪實際畫出來的畫面數' },
        notDrawn: {
          type: 'array',
          description: '9.4 列了但本輪沒畫的畫面，逐筆列出。⛔ 空陣列代表全部畫完，不要拿它當免填欄位；決定不畫是可以的，但必須列出來讓主控端知道',
          items: {
            type: 'object',
            additionalProperties: false,
            required: ['screen', 'reason'],
            properties: {
              screen: { type: 'string', description: '畫面名稱＋分析檔裡的 node id' },
              reason: { type: 'string', description: '為什麼這輪沒畫（工作量／分析檔資料不足／被指示只畫某幾張…）' },
            },
          },
        },
      },
    },
    // 自編的資料比真值更「合理」（連號、遞增、有單位），所以沒有任何檢查會攔它，
    // 看圖的人也不會起疑 —— 真值反而像「稿還沒填完」。實測一次自編 10 列表格資料
    // 並加上稿上沒有的幣別符號，而 worker 早就在 analysisGaps 寫了「本檔自編」，照樣過關。
    // 做成必填欄位，是把「我編了」從散文裡的一行，變成一個要逐筆列出、且原則上必須為空的格子。
    fabricated: {
      type: 'object',
      additionalProperties: false,
      required: ['items', 'addedSymbols'],
      properties: {
        items: {
          type: 'array',
          description: '分析檔沒有、由你生出來的內容，逐筆列出。⛔ 原則上必須是空陣列 —— 缺資料時正確做法是 blocked（見 pen-drawer 3.1.0-A），不是先畫再登記',
          items: {
            type: 'object',
            additionalProperties: false,
            required: ['what', 'where', 'why'],
            properties: {
              what: { type: 'string', description: '生了什麼（例：列表表格 10 列的訂單編號與金額）' },
              where: { type: 'string', description: '畫在哪些節點' },
              why: { type: 'string', description: '為什麼沒有 blocked 而是自己生 —— 這一欄要能說服主控端' },
            },
          },
        },
        addedSymbols: { type: 'array', items: { type: 'string' }, description: '你加上但分析檔逐字值裡沒有的符號或單位（幣別、千分位、單位、標點）。⛔ 應為空。同一張畫面裡符號的有無本身就是設計資訊 —— 實測表格欄位是 3,160、表尾合計才是 NT$ 9,100' },
        modifiedSourceValues: { type: 'array', items: { type: 'string' }, description: '你改動過的「分析檔原有值」，逐筆寫改前→改後與理由。⛔ 應為空 —— 包括為了湊內部一致而改數量、為了對齊而改格式、為了「修正」稿上重複編號' },
      },
    },
    analysisGaps: { type: 'array', items: { type: 'string' }, description: '繪製時發現分析檔缺漏或矛盾之處' },
    ...BASE,
  },
}

const ANNOTATE_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['penPath', 'status', 'annotatedQuestions', 'inventory', 'formatCheck'],
  properties: {
    penPath: { type: 'string' },
    annotatedQuestions: QUESTION_LIST,
    // 三邊對帳。做成必填欄位，是因為「漏了幾題」在 .pen 上完全沒有症狀 ——
    // 實測一份稿的對照表 18 題、畫面紅框只有 10 題，從畫面出發的人會拿到一份
    // 看起來很完整的 10 題清單，而少掉的 8 題不會有任何東西提醒他。
    inventory: {
      type: 'object',
      additionalProperties: false,
      required: ['sourceCount', 'cardCount', 'anchoredCount', 'unanchored'],
      properties: {
        sourceCount: { type: 'number', description: '分析檔第 7 節的題數' },
        cardCount: { type: 'number', description: '本檔疑問卡總數（全檔遞迴，含無錨點的）' },
        anchoredCount: { type: 'number', description: '畫面上有紅框的題數' },
        unanchored: { type: 'array', items: { type: 'string' }, description: '沒有畫面錨點、卡放在「不對應特定畫面」段的題號' },
        tableUpdated: { type: 'boolean', description: '頂層「設計疑問對照表」是否已更新為全部題目各一列' },
      },
    },
    // 疑問卡的大綱與換行規則住在 design-question-curator，這裡不重寫一份規則，只要求「交件前實際去數」。
    // 實跑的觀察：大綱 13/13 一次到位（它是結構性的，畫卡就得決定分幾段），
    // 換行則有零星漏網（104 個文字節點裡 4 個用「；」串了完整句）—— 格式細節最容易在寫文字時被略過。
    formatCheck: {
      type: 'object',
      additionalProperties: false,
      required: ['cardTextNodes', 'semicolonJoined', 'multiSentenceNodes'],
      properties: {
        cardTextNodes: { type: 'number', description: '疑問卡內的文字節點總數（實際跑 Get 數，不要憑印象）' },
        semicolonJoined: { type: 'number', description: '用「；」串接完整句子的節點數，應為 0。⚠️ 統計前要先把 Figma node id 剝掉（instance-child id 長這樣 I2198:474061;578:93811;283:15821，本身就含分號）—— 不剝的話每個引用 node id 的出處欄都會被誤判成違規，實測就是這樣先得到一個假的「19 筆違規」' },
        multiSentenceNodes: { type: 'number', description: '同一個節點塞了多個句子卻沒換行的數量（句號／驚嘆號／問號後面還有字），應為 0' },
        outlineUniform: { type: 'boolean', description: '13 張卡的段落組成是否完全一致（標頭／狀態徽章／段-疑問／段-出處／段-影響；未結案時不放決議段）' },
      },
    },
    addedNodes: NODE_LIST,
    layoutAdjusted: { type: 'boolean', description: '是否為了避開重疊而搬動過畫面' },
    ...BASE,
  },
}

const IRONCLAD = [
  '== 鐵律（違反會被 hooks 直接擋下，被擋時不要繞路，照回報格式說明卡在哪）==',
  '- pen 檔由使用者手動建立並開啟：嚴禁 New-Item 自建、嚴禁 Start-Process/code 自開、嚴禁自動存檔。',
  '- 所有 pencil 呼叫都要帶自己的 filePath，禁用「當前開啟檔」。',
  '- 只讀被指派的節點、只畫/只 snapshot 自己的 filePath、只移動自己建立的節點。',
  '- 忠實原則：設計稿矛盾／殘留逐字引用出處回報，不要順手「修正」；設計疑問三要素（疑問、原文出處含 node id、對 Schema/流程的影響）不可省略。',
  '- 完成後不自行存檔，於回報提醒使用者在 Pencil Desktop 手動 Save All。',
].join('\n')

function header(step, job, source) {
  return [
    `【worker 模式】你是被 design-lead 的 workflow 派來執行 step「${step}」的 worker。任務已完整指定，禁止呼叫 AskUserQuestion。`,
    '資料契約以 design-handoff-contract 為唯一真相（step 定義、分析檔格式、誰寫哪一段）。',
    '',
    '== 指派內容 ==',
    `- 批次：${(source && source.batch) || '(未命名)'}`,
    `- 畫面：${job.screen || job.id || '(未命名)'}`,
    `- 分析檔路徑（analysisPath）：${job.analysisPath}`,
    job.penPath ? `- 目標 pen 檔（filePath，絕對路徑）：${job.penPath}` : '',
  ].filter(Boolean).join('\n')
}

function readPrompt(job, source) {
  const nodes = Array.isArray(job.figmaNodeIds) && job.figmaNodeIds.length
    ? job.figmaNodeIds.join(', ')
    : '（未指定 → 以 blocked 回報，不要自行猜範圍）'
  return [
    header('read', job, source),
    `- Figma 來源：${(source && source.figmaLink) || '（未提供 → 以 blocked 回報）'}`,
    (source && source.fileKey)
      ? `- figma-bridge 連線 fileKey（所有呼叫都帶這個，非 URL key）：${source.fileKey}${source.fileName ? `　／檔名：${source.fileName}` : ''}`
      : '- figma-bridge 連線 fileKey：（未提供 → 先跑 list_files；只連著一個檔就用它並在回報寫明，連著多個檔則以 blocked 回報請人指定）',
    `- 要讀的節點（已轉冒號格式）：${nodes}`,
    (source && source.note) ? `- 來源補充：${source.note}` : '',
    '',
    '== 你要做的 ==',
    '0. 先跑 list_files()，確認上面那個 fileKey 真的出現在已連線清單裡（有給檔名就一併核對），之後每一支 figma-bridge 呼叫都帶 fileKey。⛔ 只連著一個檔時，帶錯的 fileKey 不會報錯 —— bridge 會回退到那條唯一連線，你照樣拿到「內容完整、看起來合理，但屬於別的檔」的結果。核對不過就以 blocked 回報，不要因為「反正只連一個、應該就是它」而硬跑；目標檔沒出現在清單裡＝使用者還沒在那個檔開 plugin，連線不是你能建立的。',
    '1. 依 figma-bridge-reading 三鐵律讀取：node-id 轉冒號、先 set_selection 界定範圍再 get_design_context({depth:1})（核對 context[0].name 是否為預期節點）、逐層 depth:1 下探、截圖用 save_screenshots + Read。',
    '2. 整理畫面結構、欄位（逐字）、按鈕、彈窗與狀態、流程走向（含 5.1 情境序列：哪個動作造成畫面怎麼變，前後態各是哪張畫面；畫面上看不出差別的變化不列）、註解原文（逐字，含 node id 與色彩語意）、設計疑問。',
    '3. 量測第 9 節（版面規格與色票）：9.0 元件組成與呈現方式、9.1 色票、9.2 版面骨架、9.3 對齊與排列、9.4 逐畫面差異。方法見 figma-bridge-reading 第 6 節。色值與尺寸一律讀節點屬性（get_node / get_variable_defs），不要看截圖填；截圖只用來定位該量哪個節點。',
    '3-0.【順序不可顛倒】量版面的第一步不是量數字，是把容器階層走出來：從畫面根節點 depth:1 逐層下探，記成一棵樹（誰包誰／每層幾個子節點／每層 gap 與 padding／各層高度），寫進 9.2.1，再回頭填 9.2 的元素數值。⛔ 先量元素再湊階層必然漏層 —— 那些「只是把兩張卡包在一起」的中介容器沒有底色沒有框線、寬度與子節點一樣，唯一的存在證據就是它的 gap。實測漏一層 gap 0 的群組容器，下游把兩張卡當成平行子節點套用了內容區的 gap 24，單這一項就多 24px。',
    '3-0b.【自檢，必做】容器樹走完後用它把畫面總高算一次，與 9.4 記的畫面高度對，填進 measurement.heightReconciled。⛔ 對不上就是還有一層沒走到，不要用「大概是捨入誤差」帶過 —— 這個算式是全對或全錯，不會差幾 px。對不上就把差額逐筆填進 heightMismatch 並回頭找那一層。',
    '3-0d2.【表單欄位的示意值也要逐格記】第 2.x 欄位表必須有「示意值（逐字）」欄，逐畫面各記一次（同一欄位在新增頁是空的、編輯頁有值，兩張要分開記）。畫面上真的空白的記「（空）＋placeholder 逐字」，不要留白。缺的填進 measurement.formFieldsWithoutSampleValue。⛔ 這一項最容易整批漏掉，因為欄位表的標籤·型態·必填·位置·樣式全有時看起來已經很完整，唯獨沒有「裡面寫著什麼」—— 而下游畫出來的空框在版面上也完全正常，不會有任何東西提示你少了東西。',
    '3-0d.【表格逐欄記，不要用散文】畫面上每一張表格（列表表格、明細表、檔案清單…）各用第 2.x 的「表格類欄位」格式記一節：逐欄的寬／儲存格對齊（primaryAxisAlign）／文字對齊（textAlignHorizontal）／儲存格內距。填 measurement.tablesFound 與 tablesWithPerColumnSpec，兩者必須相等。⛔ 欄位清單（含「文字寬度模式」＝ textAutoResize）對每一張表都適用，不是只有第一張 —— 交件前逐表數欄數，缺的填進 measurement.tablesMissingTextWidthMode。⛔ 實測發生過：同一份分析檔裡列表表格用表格格式記得很完整，同一頁的明細表卻只寫成一句「商品圖／商品編號／商品名稱／…」—— 那是個人發揮不是制度，所以第二張表就漏了。下游拿到一串欄位名，九欄的寬與對齊全部自配，而且加起來剛好等於表格總寬，表格不破版、沒有任何數字對不上。⚠️ 「總和對了」只證明這幾個數字加起來等於總寬，與「是不是量到的」無關。',
    '3-0e.【符號先確認是字還是節點】> ≪ ‹ ｜ ～ * 這類符號要記進內容時，先展開一層看它是 TEXT 還是 INSTANCE/VECTOR/LINE。是節點就記進 9.2.1 的容器樹（含尺寸與顏色），⛔ 不要寫進文字內容裡。實測三次都記錯：麵包屑的「>」是 24×24 的 chevron icon（間距因此差 40px）、分頁列的「≪ ‹ › ≫」是 4 顆 icon、頂欄的「｜」是 LINE 節點。記成字元時畫面不會壞也不會報錯，只是間距與形狀永遠對不上。',
    '3-0c.【文字規格用分群量，不要自己分級】把該畫面底下所有 TEXT 節點連同 fontSize/fontWeight/fontFamily/fills 一次抓出來，依這四個屬性分群 —— 群數就是「有幾種文字元素」，寫進 9.2.2，一群一列。填 measurement.textGroupsFound 與 section922Rows，兩者必須相等。⛔ 不要先想「這頁有哪幾級文字」再去量：實測一份稿只記了 5 個「級別」而畫面實際有 13 群，且「字級：頁標題／卡片標題」那一列量的是卡片標題，列表頁頁標題其實是 24px/700，就這樣靜默繼承了別的元素的值。⚠️ 相同文字內容不代表同一種元素（「訂單維護」同頁出現三次、三種規格），數字與中文常是不同字型（Roboto vs Noto Sans TC）—— 分群才分得開。一列只能對應一種元素，出現「A／B」「…類」「各級」就是併了。',
    '3a. 第 9.0 節（元件組成與呈現方式）的量法不是讀屬性，是展開節點樹「逐項清點」（見 figma-bridge-reading 6.6），五類都要寫：①頂欄實際放什麼（選單鈕／麵包屑／搜尋／通知／使用者／登出，逐項列）②側欄幾層、能不能展開、選取態怎麼表示 ③每一種按鈕有沒有 icon、是哪一顆（純文字連結也要標明是純文字）④每個操作的呈現方式（換頁／彈窗／抽屜／就地展開／同頁切分頁籤）⑤列表列操作區的形式（icon 鈕／文字鈕／下拉選單／混合）。⛔ 設計稿沒有的寫「無」，不要留空 —— 下游拿到空白不會停工，它會照繪製 skill 的示意寫法補齊，實測產出被形容成「擅自加了 icon、header 不同、SPA 操作畫面是另一種呈現方式」，而那些東西 worker 一顆都沒有自己發明。',
    '3b. 9.1 色票每一列都要填「對應的 pen 變數名」（下游要照它跑 SetVariables）。查不到對應變數就寫「待建」並在回報說明；⛔ 不要只給色碼 —— .pen 檔本來就有一套 $primary／$bg-page，下游引用得到、不報錯、畫面也不壞，但用的是檔案原本的主題色，跟 Figma 無關。',
    '   ⛔ 描述位置的詞（左／右／置中／靠齊）必須附實測 x 或 y 偏移佐證，只有形容詞沒有數字的一律填「未量到」——「第一個子節點＝在左邊」在 auto-layout 下不成立，實測就是這樣把置中的頁碼群記成「左側」，害下游 13 條分頁列全畫錯。',
    '   ⛔ 量不到就標「未量到」並分清是「缺料」（設計稿沒畫，要問設計師）還是「漏量」（自己沒展開，再跑一次就有），不得以推測值填補；也不得為了看起來一致而統一或四捨五入量到的值（實測同一份稿卡片圓角 0 與 6 並存，兩個都要照原樣記）。',
    '4. 用 Write 建立 analysisPath（依 design-handoff-contract 第二節的格式），填 frontmatter 與第 1～7 節、第 9 節（含 9.0）；第 7 節的「pen 節點 ID」欄與第 8 節留白給下游。既有檔一律插入新段落，不覆蓋別人寫的內容。',
    '5. 第 1～7 節與第 9 節（含 9.0 與 9.2.1 容器階層）都寫完、且容器樹算出來的總高與 9.4 對得上之後，才在 frontmatter 寫 readCompleted: true（這行是下游動筆的守門依據，提早寫等於放行一份沒有色值與版面數值的分析，下游會照樣開畫然後整批畫錯）。',
    '6. Figma 截圖暫存夾任務結束刪掉。',
    '',
    '⛔ 隱藏圖層讀不到，而且是以「不存在」的樣子消失的（不是帶 visible:false 回來）—— 所以「visible 全是 true」不能推論成「沒有隱藏圖層」。因此：同一畫面多個複本之間「區塊有無」的差異一律寫進第 9.4 節逐畫面差異，不要升級成第 7 節設計疑問；措辭用「複本 B 未出現 X 區塊」，不要寫「缺少」或「疑似漏畫」（那是在陳述你無法確認的事）。只有當該區塊的有無會影響資料模型或流程時才升級成疑問，並在影響欄註明「亦可能為隱藏而非缺漏，需人工確認」。判準見 figma-bridge-reading 7.1。',
    '',
    '== 回報要多帶一項 ==',
    '量測涵蓋度：第 9 節五個小節（9.0～9.4）各自「已量／未量到」的項目清單，未量到的逐項標缺料或漏量。不要只寫「已完成」。9.0 要逐類回報寫了什麼，寫「無」的也算已量。',
    '建議人工確認的區塊：複本之間有無不一致、你判斷可能是隱藏圖層而非缺漏的，逐項列出（哪張畫面、少了什麼、對照的是哪張）。只有主控端查得到（要使用者在 Figma 選取該圖層後跑 get_selection），你自己要不到。',
    '',
    IRONCLAD,
  ].filter(Boolean).join('\n')
}

// 三種繪製 step 的差異都收在這裡（字面須與 design-handoff-contract 第一節一致）
const DRAW_KINDS = {
  'draw-flow': { skill: 'pen-flow-diagram', kind: 'flow', desc: '流程骨架' },
  'draw-screen': { skill: 'pen-screen-drawing', kind: 'screen', desc: '完整重繪畫面 UI' },
  'draw-scenario': { skill: 'pen-scenario-sequence', kind: 'scenario', desc: '功能情境序列（說明帶＋前後畫面對照）' },
}

function drawPrompt(step, job, source) {
  const k = DRAW_KINDS[step]
  const isScenario = step === 'draw-scenario'
  return [
    header(step, job, source),
    `- 產出型態：${k.desc}（依 ${k.skill}）`,
    '',
    '== 你要做的 ==',
    '1. Read analysisPath，確認 frontmatter 有 readCompleted: true；沒有就 blocked 回報，不要動筆。分析檔缺你需要的段落也 blocked（請 design-lead 補派 read），不要自行推測補完。',
    step === 'draw-flow' ? '' : '1a. 另外確認第 9 節在，且 9.0（元件組成與呈現方式）、9.1（色票）、9.2.1（容器階層樹）、9.2.2（逐元素文字規格）四者都不是空的 —— 缺任一個都 blocked。⛔ 9.2.2 若只有「字級：頁標題／卡片標題」這種併了多個元素的列，等同缺漏：畫面上每一種文字都要有自己的一列，你不准替沒列到的文字挑一個看起來合理的字級。⛔ 缺 9.2.1 時你只會拿到一張「元素→數值」的平表，而 gap 是掛在容器上的：你不會知道某個 gap 套用在哪兩個東西之間，只能假設同一層的子節點都是平的，於是漏掉的每一層中介容器都會多算一個 gap。⛔ 缺 9.0 時你「畫得出來」，因為繪製 skill 為了給範例帶著示意寫法（按鈕的 icon 槽、頂欄放什麼、操作走換頁），那些示意會變成你的預設答案，產出就是稿上沒有的東西被加了進去。畫得出來不是往下畫的理由。',
    isScenario
      ? '1b.【本 step 特有的前置依存】檢查分析檔第 8 節有無型態為 screen 的節點 —— 那是情境要 Copy 的畫面母版。沒有就 blocked 回報「請先對本畫面跑 draw-screen」，嚴禁自己畫一張新畫面充當母版。另需第 5.1 節「情境序列」；缺了同樣 blocked。'
      : '',
    '2. 用 execute 讀一次頂層 Get(document,(n,c)=>c.depth===0&&Print(n.id,"|",n.name),{depth:1}) 確認 pen 檔已就緒；讀不到、或寫入時回報檔案未開啟，就 blocked 回報「請先在 Pencil Desktop 建立並開啟該檔再重跑」。',
    `3. 載入 ${k.skill}，依其規範繪製到你自己的 filePath。每畫完一區塊就用 execute 的 Get（印 bounds）自驗。`,
    step === 'draw-flow' ? '3a. 【本 step 的 fidelity 怎麼填】你畫的是流程圖，用的是 pen-flow-diagram §7 的流程圖專用色票，那組本來就不對到分析檔 9.1。所以：paletteBound 填 true 並在 notes 註明「draw-flow 不綁 9.1」、unboundVariables 與 notInSection90 一律填空陣列。⛔ 不要把 $canvas-dark／$sec-bg／$band-sub 這類流程圖變數填進 unboundVariables —— 那不是「你自己配的顏色」，是 skill 規定的。' : '',
    step === 'draw-flow' ? '' : '3a. ⛔ 繪製 skill 裡的每一個數字與 $變數名都是佔位示意，不是預設值。skill 給的是骨架與畫法（節點階層怎麼搭、用哪個參數、Copy 怎麼覆寫），值與元素組成一律以第 9 節為準；兩邊看起來衝突時第 9 節贏。9.0 沒列到的元素一律不加（icon／麵包屑／頁籤／通知鈴鐺／「更多」選單都算）—— 多加一個看起來很合理的東西不會破版、不會報錯、自我截圖全綠，只是不像設計稿。',
    step === 'draw-screen' ? '3c. 【覆蓋率】開工前先數一次分析檔第 9.4 節列了幾張畫面，那是「應該有幾張」。畫不完是可以的，但**每一張沒畫的都要列進 coverage.notDrawn 並寫理由**。⛔ 不要默默只畫一部分 —— 畫出來的每一張都會是對的，沒畫的那些不會留下任何空缺，主控端在比對閘門上也看不出來（他比的是「畫了的像不像」，不是「有沒有少畫」）。' : '',
    step === 'draw-flow' ? '' : '3-A.【最高階紅線】分析檔沒有的內容，一格都不准自己生。缺一列表格資料、缺一個欄位值、缺一段文字，都是 blocked，不是「我來補一下」。⛔ 特別是三件事：(1) 不要加分析檔逐字值裡沒有的符號或單位（實測同一張畫面表格欄位是 3,160、表尾合計才是 NT$ 9,100 —— 符號的有無本身就是設計資訊）(2) 不要「修正」稿上的重複或矛盾（兩列編號重複是發現，寫進回報，不是錯誤）(3) 不要為了湊內部一致而改既有值。⚠️ 自編的資料比真值更「合理」（連號、遞增、有單位），所以沒有任何檢查會攔，看圖的人也不會起疑 —— 真值反而像「稿還沒填完」。若仍然生了，逐筆填進 fabricated，那個欄位原則上必須是空的。',
    step === 'draw-flow' ? '' : '3b. 開畫前先把色票綁上：GetVariables() 看現況，再依 9.1 的「對應的 pen 變數名」欄跑 SetVariables 補齊缺的。⚠️ 檔案現值與 9.1 不符時不要就地改掉（改變數會動到全檔既有節點），把「變數名／檔案現值／9.1 量測值」填進回報的 fidelity.variableDiffs 交主控端裁決。不綁的後果是最難發現的那一種：.pen 檔本來就有一套 $primary／$bg-page，你引用得到、不會報錯、畫面也不會壞，只是整批用的是檔案原本的主題色。',
    isScenario
      ? '4. 情境的每一張畫面一律 Copy 母版＋descendants 覆寫「變了的節點」，不重畫；畫面上下排、說明帶在最上；root 的 frame 名稱必須含「功能情境」四字（反導閘門靠它辨識）。要圈變更點用 $primary 藍框，絕不可用紅框 #eb4751（紅框是設計疑問專用語意，誤用會讓後續標註與反導閘門全部誤判）。'
      : '4. 為後續的疑問標註預留版面：畫面排成單一直欄、右側留白給紅框與描述註解，別把版面塞滿。完成後檢查頂層節點不重疊。',
    isScenario
      ? `5. 用 Edit 回填分析檔第 8 節：逐筆寫入節點名稱＋ID，型態一律寫 scenario（不是 screen）—— 情境副本不是疑問標註的對象，型態寫錯會讓 design-question-curator 標到副本去。第 7 節與第 1～6 節都不要動。`
      : `5. 用 Edit 回填分析檔：第 8 節寫入已繪製節點（名稱＋ID＋型態，本 step 為 ${k.kind}）；第 7 節每項疑問補上對應的 pen 節點 ID（找不到對應元素就寫「無對應元素」並在回報說明）。只改這兩處，不要動第 1～6 節。`,
    '6. 用 Copy 做狀態變體時關掉的區塊（descendants 設 enabled:false），每一個都要在第 8 節登記一列，型態 hidden-in-variant，備註寫「為什麼這張不顯示」（格式見契約 8.1）。收工前跑 Get("<畫面ID>",(n,c)=>n.enabled===false&&Print(n.id,n.type,JSON.stringify(n.name))) 確認，並把輸出貼進回報的 hiddenInVariant 欄位。⚠️ 這行會一併列出 design-question-curator 收起的疑問標示（實測 191 個 enabled:false 裡有 182 個是那些）—— 名稱以「疑問標示-」或「徽章-」開頭的不是你的東西，不要登記也不要動。',
    '   為什麼非登記不可：這個資訊目前只存在於 .pen 裡，中介檔完全沒有。下游看到的是「這張畫面沒有這塊」，跟「你漏畫了」長得一模一樣，而且不會有任何東西報錯 —— 最後是規格少寫一條「什麼情況下才顯示」的業務規則，而規格看起來很完整。',
    '',
    IRONCLAD,
  ].filter(Boolean).join('\n')
}

function annotatePrompt(job, source) {
  return [
    header('annotate', job, source),
    '',
    '== 你要做的（用法 A：annotate，一次性標註）==',
    '1. Read analysisPath，取第 7 節疑問清單（含 pen 節點 ID 欄）。缺 readCompleted: true 就 blocked；第 7 節為空就回報 done 並註明「本畫面無設計疑問」，不要硬生出疑問。',
    '2. 用 execute 讀一次頂層確認 pen 檔就緒。',
    '3. 逐項標到畫面上：紅色外框（#eb4751 框線、加粗、透明填色）框住對應元素，左上角加編號徽章（題號與第 7 節一致），並把疑問卡放在「該畫面右側」（紅框指向什麼／原稿依據含 node id／對 Schema 與流程的影響）。⛔ 卡貼著它所指的畫面，不集中到流程圖底下 —— 集中的後果實測過：18 張卡全在流程圖疑問分區、畫面上只有 10 題有紅框，從畫面出發的人會以為只有 10 題，另外 8 題安靜地不見。對應欄位是「無對應元素」或屬純示意稿殘留的提醒性項目，不畫紅框與徽章，卡改放畫面區最後的「不對應特定畫面」段並在回報說明。',
    '3b. 維護頂層的「設計疑問對照表」（沒有就建）：每一題各一列，欄位為 題號／一句摘要／紅框在哪張畫面（無錨點寫「—」）／卡在哪。不放狀態徽章（狀態只在卡上，兩處各一份必定走鐘）。這張表是唯一的完整清單，resolve 的對帳與反導閘門都以它為母體 —— 漏列一題，那題就從此不存在。',
    '4. 檢查版面：紅框與註解很吃空間，確認未與其他畫面或流程區塊重疊；有重疊就把畫面往外挪、重新排位，並用 execute 的 Get（印 bounds）／截圖驗證無破版。',
    '5. 用 Edit 回填分析檔：第 7 節狀態欄改為「未處理」（已標註但尚未結案），第 8 節追加新增的標註節點。其他段落不動。',
    '6. 交件前跑一次卡片格式統計並填進 formatCheck（大綱與換行規則見 design-question-curator，這裡不重複規則、只要求你實際去數）。⚠️ 數「；」之前先把 Figma node id 剝掉再判 —— instance-child id 本身就含分號（I2198:474061;578:93811;283:15821），不剝的話每個寫了出處的欄位都會被誤判成違規。⛔ 不要憑印象填 0。',
    '',
    IRONCLAD,
  ].join('\n')
}

// --- step 對映表（字面須與 design-handoff-contract 第一節一致）---
const STEPS = {
  'read': (job, source) =>
    agent(readPrompt(job, source), {
      label: `read:${job.screen || job.id}`, phase: 'Read',
      agentType: 'figma-reader', schema: READ_SCHEMA,
    }),
  'draw-flow': (job, source) =>
    agent(drawPrompt('draw-flow', job, source), {
      label: `flow:${job.screen || job.id}`, phase: 'Draw',
      agentType: 'pen-drawer', schema: DRAW_SCHEMA,
    }),
  'draw-screen': (job, source) =>
    agent(drawPrompt('draw-screen', job, source), {
      label: `screen:${job.screen || job.id}`, phase: 'Draw',
      agentType: 'pen-drawer', schema: DRAW_SCHEMA,
    }),
  'draw-scenario': (job, source) =>
    agent(drawPrompt('draw-scenario', job, source), {
      label: `scenario:${job.screen || job.id}`, phase: 'Draw',
      agentType: 'pen-drawer', schema: DRAW_SCHEMA,
    }),
  'annotate': (job, source) =>
    agent(annotatePrompt(job, source), {
      label: `annotate:${job.screen || job.id}`, phase: 'Annotate',
      agentType: 'design-question-curator', schema: ANNOTATE_SCHEMA,
    }),
}

// --- 解析 args（可能以物件或字串化 JSON 抵達）---
let a = args
if (typeof a === 'string') {
  try { a = JSON.parse(a) } catch (e) { a = null }
}

const source = Object.assign({ batch: a && a.batch }, (a && a.source) || {})
const jobs = (a && Array.isArray(a.jobs)) ? a.jobs : []

// 比對閘門的放行名單：true ＝ 整批放行；陣列 ＝ 只放行列到的 job id。
const gateRaw = a && a.gateCleared
const gateClearedAll = gateRaw === true
const gateClearedIds = Array.isArray(gateRaw) ? gateRaw : []
const isGateCleared = (job) => gateClearedAll || gateClearedIds.includes(job.id) || gateClearedIds.includes(job.screen)

if (!jobs.length) {
  log('args.jobs 為空。請先由 design-lead 解析需求並寫出 _jobs.json。')
  return { error: 'no-jobs', results: [] }
}

// --- 派工前檢核：不合法的 job 直接剔除，並明講剔除原因（不靜默略過）---
const valid = []
for (const job of jobs) {
  const steps = Array.isArray(job.steps) ? job.steps : []
  const unknown = steps.filter((s) => !STEPS[s])
  if (unknown.length) {
    log(`SKIP ${job.id || job.screen}：未知的 step ${unknown.join(', ')}（合法值：${Object.keys(STEPS).join(', ')}；resolve 不是 step，走直呼 design-question-curator）`)
    continue
  }
  if (!steps.length) {
    log(`SKIP ${job.id || job.screen}：steps 為空`)
    continue
  }
  if (!job.analysisPath) {
    log(`SKIP ${job.id || job.screen}：缺 analysisPath（分析檔是各階段的交接點，不可省略）`)
    continue
  }
  const needsPen = steps.some((s) => s.startsWith('draw') || s === 'annotate')
  if (needsPen && !job.penPath) {
    log(`SKIP ${job.id || job.screen}：steps 含繪製／標註卻沒有 penPath`)
    continue
  }
  // draw-scenario 是唯一有順序約束的 step：情境要 Copy draw-screen 畫出來的畫面母版。
  if (steps.includes('draw-scenario')) {
    const si = steps.indexOf('draw-screen')
    const ci = steps.indexOf('draw-scenario')
    if (si > ci) {
      log(`SKIP ${job.id || job.screen}：draw-scenario 必須排在 draw-screen 之後（情境要 Copy 畫面母版，不重畫）`)
      continue
    }
    if (si === -1) {
      log(`NOTE ${job.id || job.screen}：本 job 含 draw-scenario 但無 draw-screen，將沿用既有母版（worker 會檢查分析檔第 8 節有無型態 screen 的節點，缺了會 blocked）`)
    }
  }
  if (!steps.includes('read') && steps.some((s) => s.startsWith('draw') || s === 'annotate')) {
    // 沒有 read 階段時，分析檔必須是既有的 —— 這裡無法讀檔驗證，交由 worker 開工時檢核 readCompleted。
    log(`NOTE ${job.id || job.screen}：本 job 未含 read，將沿用既有分析檔 ${job.analysisPath}（worker 會檢查 readCompleted，缺了會 blocked）`)
  }
  valid.push(job)
}

if (!valid.length) {
  log('沒有任何合法 job，全部被剔除。')
  return { error: 'no-valid-jobs', requested: jobs.length, results: [] }
}

log(`派工 ${valid.length}/${jobs.length} 個 job；job 之間並行，job 內部依 steps 依序執行`)
if (gateClearedAll) {
  log('gateCleared: true → 本次略過 draw-screen 後的比對閘門（主控端已驗過）')
} else if (gateClearedIds.length) {
  log(`gateCleared: ${gateClearedIds.join(', ')} → 這幾個 job 略過比對閘門，其餘照擋`)
}

// --- 每個 job 走自己的鏈：job 間並行、job 內序列（steps 長度可不同）---
const results = await parallel(valid.map((job) => async () => {
  const outputs = {}
  // job 自帶 source 時「整份覆蓋」批次層的（不逐欄合併）——見 design-handoff-contract 3.1：
  // 逐欄合併會讓「只覆寫 fileKey、卻沿用批次 figmaLink」這種指向兩個檔的半套組合成立，而且看起來完全正常。
  const jobSource = job.source
    ? Object.assign({ batch: source.batch }, job.source)
    : source
  if (job.source) {
    log(`${job.id || job.screen} 使用自己的 Figma 來源：${job.source.fileName || '(未命名)'}（fileKey ${job.source.fileKey || '未提供'}）`)
  }
  let gatePending = null
  for (let i = 0; i < job.steps.length; i++) {
    const step = job.steps[i]
    const r = await STEPS[step](job, jobSource)
    outputs[step] = r
    if (!r) {
      log(`${job.id || job.screen} 的 step「${step}」沒有回傳（worker 中止），該 job 停止後續 step`)
      break
    }
    if (r.status === 'blocked') {
      log(`${job.id || job.screen} 的 step「${step}」blocked：${r.notes || '(未說明)'} → 該 job 停止後續 step`)
      break
    }
    // --- 比對閘門：draw-screen 完成後、其餘 step 之前 ---
    const remaining = job.steps.slice(i + 1)
    if (step === 'draw-screen' && remaining.length && !isGateCleared(job)) {
      gatePending = remaining
      log(`GATE ${job.id || job.screen}：draw-screen 已完成，停在比對閘門（未放行）。剩下的 step：${remaining.join(', ')}`)
      break
    }
  }
  return {
    id: job.id, screen: job.screen, penPath: job.penPath,
    analysisPath: job.analysisPath, steps: job.steps, outputs,
    gatePending,
  }
}))

const done = results.filter(Boolean)
const blocked = done.filter((r) => Object.values(r.outputs).some((o) => o && o.status === 'blocked'))
const pending = done.filter((r) => r.gatePending && r.gatePending.length)
log(`完成 ${done.length}/${valid.length} 個 job；其中 ${blocked.length} 個中途 blocked、${pending.length} 個停在比對閘門`)

if (pending.length) {
  log('=== 停在比對閘門的 job（design-lead 4.4）===')
  log('先驗一張再放行其餘：把 Figma 代表畫面（save_screenshots）與 pen 畫面（export_nodes）逐項比對')
  log('　　色碼（頂部橫幅／側欄各層／表頭／主要按鈕／卡片框線）＋ 元素組成（有沒有多出稿上沒有的 icon／麵包屑／頁籤）')
  log('不符就退回重畫，不要放行。驗過之後改用「剩下的 steps」再呼叫一次本 workflow，並帶 gateCleared：')
  for (const r of pending) {
    log(`　- ${r.id || r.screen}：steps 改成 [${r.gatePending.map((x) => `'${x}'`).join(', ')}]`)
  }
  log(`　- gateCleared: ${JSON.stringify(pending.map((r) => r.id || r.screen))}　（或整批驗過就寫 true）`)
}

return {
  batch: source.batch,
  requested: jobs.length,
  dispatched: valid.length,
  returned: done.length,
  blocked: blocked.length,
  gatePending: pending.map((r) => ({ id: r.id || r.screen, penPath: r.penPath, remainingSteps: r.gatePending })),
  results: done,
}
