// ZEPETO 挑選器（2026-10-12 由 zepeto-body-menu 改名擴充；使用者要求名稱不要只講身體）
// 資料來源都是 zepeto-body 維護的清單腳本（介面契約見各腳本檔頭）：
//   身體 list_bodies.py（舊路徑 D:/render-work/zepeto-body/scripts/ 是轉接）、頭 list_heads.py
// 指令：/zepeto-bodies [demo] [multi]、/zepeto-heads [demo] [multi]
// 工具：pick_body（服裝工作流）、pick_head（身體工作流）。內建問答框（$.ui.ask）只收 2～4 個選項，所以開同一個面板後立刻回傳，
//   使用者按 y 時選擇以使用者訊息送進對話（不在工具裡等：hook 自己等超過 10 秒會被略過）
const PANE = 'zepeto-picker'
const SK = 'D:/SideProject/wedding-invitation/.claude/skills/zepeto-body-generation-workflow/scripts/'
const KEYS = '123456789abcdefghijklmnopqrstuvwxz'   // y 留給「確定」、o 在細節區開預覽圖（列多於 23 個時 o 會被細節區的按鈕蓋過）
const ZH = { groom: '新郎', bride: '新娘' }

// 兩種清單的差別都收在這裡
const KINDS = {
  body: {
    noun: '身體', title: 'ZEPETO 身體', script: SK + 'list_bodies.py', key: 'bodies',
    ok: (x) => x.released, okText: '已出廠', badText: () => '製作中', badHint: '這個身體還在製作中，要等出廠才能用',
    extra: (x) => (x.height_m ? Math.round(x.height_m * 100) + ' cm' : ''), path: (x) => x.blend,
  },
  head: {
    noun: '頭', title: 'ZEPETO 大頭', script: SK + 'list_heads.py', key: 'heads',
    ok: (x) => x.ready, okText: '可用', badText: (x) => (x.status === 'in_progress' ? '製作中' : '未就緒'),
    badHint: '這顆頭還沒做完（或紀錄與檔案對不上），要等大頭端做好才能用',
    extra: (x) => x.version || '', path: (x) => x.blend,
  },
}

const demoOf = (kind) =>
  [['best_man', '伴郎'], ['bridesmaid', '伴娘'], ['father', '爸爸'], ['mother', '媽媽'], ['flower_girl', '花童'],
   ['officiant', '證婚人'], ['guest_a', '賓客 A'], ['guest_b', '賓客 B']].map(([name, zh], i) => ({
    name, zh, demo: true, blend: null, version: 'demo', status: i === 0 ? 'in_progress' : 'released',
    released: i !== 0, ready: i !== 0, height_m: 1.45, preview: null,
  }))

let kind = 'body'
let items = []
let picked = null
let error = null
let onlyOk = false
let multi = false           // 複選：按列切換勾選，y 一次送出全部勾選的
let checked = new Set()

const K = () => KINDS[kind]
const label = (x) => (x.zh || ZH[x.name] || x.name) + ' ' + x.name

async function load($, demo) {
  error = null
  try {
    const r = await $.process.run(['python', '-I', K().script])
    if (r.exitCode !== 0) throw new Error(r.stderr.slice(0, 300))
    items = JSON.parse(r.stdout)[K().key]
  } catch (err) {
    items = []
    error = K().script.split('/').pop() + ' 執行失敗：' + String((err && err.message) || err)
  }
  if (demo) items = [...items, ...demoOf(kind)]
  if (onlyOk) items = items.filter(K().ok)
}

// 送出的訊息格式（服裝、身體工作流照這個解析；改了要先通知 zepeto-clothing-models）：
//   單選：「我選 新郎 groom 身體（body-v8-…）：D:\…\groom\body.blend」（頭：「我選 新郎 groom 頭（legacy）：…\head_rig.blend」）
//   複選：第一行「我選 N 個身體：」（或「N 個頭：」），之後一行一個「- 新郎 groom（版本）：路徑」
function message(list) {
  const n = K().noun
  if (!multi) return '我選 ' + label(list[0]) + ' ' + n + '（' + list[0].version + '）：' + K().path(list[0])
  return ['我選 ' + list.length + ' 個' + n + '：', ...list.map((x) => '- ' + label(x) + '（' + x.version + '）：' + K().path(x))].join('\n')
}

async function openMenu($) {
  picked = null
  checked = new Set()
  return $.ui.open({ id: PANE, title: K().title, focus: true, closeOnEscape: true, holdToasts: true, rows: 24 })
}

async function fromTool($, e, k, okFlag) {
  kind = k; onlyOk = !!okFlag; multi = !!e.multi
  await load($, false)
  if (error) return { result: error }
  if (items.length === 0) return { result: '沒有可選的' + K().noun + '。' }
  const r = await openMenu($)
  $.ui.invalidate('ui.render')
  const where = r && r.isPlaced === false ? '（面板在等較寬的終端機：' + r.reason + '）' : ''
  return { result: '已開啟' + K().noun + '選單，共 ' + items.length + ' 個' + where + '。請結束這一輪，等使用者送出「我選 … ' + K().noun + '」的訊息。' }
}

async function fromCommand($, e, k) {
  kind = k; onlyOk = false; multi = /multi/.test(e.args || '')
  await load($, /demo/.test(e.args || ''))
  await openMenu($)
  $.ui.invalidate('ui.render')
  return {}
}

const FORMAT = (n) =>
  '單選：「我選 <中文名> <name> ' + n + '（<version>）：<路徑>」。複選（multi=true）：第一行「我選 N 個' + n +
  '：」，之後每行「- <中文名> <name>（<version>）：<路徑>」。呼叫後結束這一輪，等那則訊息。'

export function register(on) {
  on('session.start', async ($, e, next) => {
    try {
      await $.tool.register({
        name: 'pick_body',
        description: '開啟 ZEPETO 身體選單讓使用者挑（不受 AskUserQuestion 4 個選項的限制）。工具會立刻回傳；使用者按確定後，選擇會以使用者訊息送進對話。' + FORMAT('身體'),
        inputSchema: {
          type: 'object',
          properties: {
            released_only: { type: 'boolean', description: '只列已出廠的（服裝工作流用 true）' },
            multi: { type: 'boolean', description: 'true＝可以勾選多個一次送出；false 或不給＝單選' },
          },
        },
        isDeferred: false,
      })
      await $.tool.register({
        name: 'pick_head',
        description: '開啟 ZEPETO 大頭選單讓使用者挑要做身體的頭（只列每個人的現役版本）。工具會立刻回傳；使用者按確定後，選擇會以使用者訊息送進對話。' + FORMAT('頭'),
        inputSchema: {
          type: 'object',
          properties: {
            ready_only: { type: 'boolean', description: '只列做完、可以用的（身體工作流用 true）' },
            multi: { type: 'boolean', description: 'true＝可以勾選多個一次送出；false 或不給＝單選' },
          },
        },
        isDeferred: false,
      })
      await $.command.register({ name: 'zepeto-bodies', description: '開啟 ZEPETO 身體選單（demo 多 8 個示範、multi 可複選）', argumentHint: '[demo] [multi]' })
      await $.command.register({ name: 'zepeto-heads', description: '開啟 ZEPETO 大頭選單（demo 多 8 個示範、multi 可複選）', argumentHint: '[demo] [multi]' })
    } catch (err) {
      $.ui.toast('zepeto-picker 註冊失敗：' + String((err && err.message) || err))
    }
    return next(e)
  })

  on('command.run', { command: 'zepeto-bodies' }, async ($, e) => fromCommand($, e, 'body'))
  on('command.run', { command: 'zepeto-heads' }, async ($, e) => fromCommand($, e, 'head'))
  on('tool.call', { tool: 'mcp__zepeto-picker__pick_body' }, async ($, e) => fromTool($, e, 'body', e.released_only))
  on('tool.call', { tool: 'mcp__zepeto-picker__pick_head' }, async ($, e) => fromTool($, e, 'head', e.ready_only))

  on('ui.render', { component: 'Pane' }, async ($, e, next) => {
    if (e.requestId !== PANE) return next(e)
    const { Box, Text, Button, Image } = $.ui.resolve(e)
    const redraw = () => $.ui.invalidate('ui.render')
    const k = K()

    const rows = items.map((x, i) =>
      Box({
        key: 'row-' + x.name, flexDirection: 'row', columnGap: 2,
        children: [
          Button({
            key: 'pick-' + x.name,
            label: (multi ? (checked.has(x.name) ? '[x] ' : '[ ] ') : '') + label(x),
            hotkey: KEYS[i], plain: true,
            ...(k.ok(x) ? {} : { dimColor: true }), ...(i === 0 ? { autoFocus: true } : {}),
            onPress: () => {
              picked = x
              if (multi && k.ok(x)) {             // 不能用的不能勾
                if (checked.has(x.name)) checked.delete(x.name)
                else checked.add(x.name)
              }
              redraw()
            },
          }),
          Text({ dimColor: true, children: [k.extra(x)] }),
          Text({ color: k.ok(x) ? 'green' : 'yellow', children: [k.ok(x) ? k.okText : k.badText(x)] }),
          ...(x.demo ? [Text({ dimColor: true, children: ['（示範）'] })] : []),
        ],
      }))

    const detail = picked
      ? [
          Text({ bold: true, children: [label(picked)] }),
          Text({ children: ['版本：' + picked.version] }),
          ...(kind === 'body' ? [Text({ children: ['身高：' + k.extra(picked)] })] : []),
          ...(picked.note ? [Text({ dimColor: true, children: [picked.note] })] : []),
          ...(picked.preview && e.surface === 'terminal'
            ? [
                Image({ key: 'preview', source: { file: picked.preview, format: 'png' }, columns: 24, rows: 12, alt: '（這個終端機不能顯示圖片，按 o 開預覽圖）' }),
                Button({
                  key: 'open-preview', label: '開預覽圖', hotkey: 'o', plain: true,
                  onPress: async () => {
                    try { await $.process.run(['cmd', '/c', 'start', '', picked.preview.replace(/\//g, '\\')]) } catch (err) { $.ui.toast('開不了預覽圖：' + String(err)) }
                  },
                }),
              ]
            : [Text({ dimColor: true, children: [picked.demo ? '（示範項目沒有預覽圖）' : '（沒有預覽圖）'] })]),
          ...(k.ok(picked) ? [] : [Text({ color: 'yellow', children: [k.badHint] })]),
        ]
      : [Text({ dimColor: true, children: [multi ? '按左邊的數字或字母（或上下鍵＋Enter）勾選／取消' : '按左邊的數字或字母（或上下鍵＋Enter）看細節'] })]

    // 確定：單選送 picked；複選送全部勾選的（照清單順序）
    const chosen = multi ? items.filter((x) => checked.has(x.name)) : picked && k.ok(picked) ? [picked] : []
    const confirm = chosen.length
      ? Button({
          key: 'confirm', label: multi ? '確定（' + chosen.length + ' 個）' : '確定用這個', hotkey: 'y', plain: true,
          onPress: async () => {
            const list = chosen
            await $.ui.close({ id: PANE })
            if (list.some((x) => x.demo)) { $.ui.toast('含示範項目，不會送出：\n' + message(list)); return }
            $.prompt.submit({ text: message(list), asUser: true })
          },
        })
      : null

    return Box({
      flexDirection: 'column',
      children: [
        Text({ dimColor: true, children: ['共 ' + items.length + ' 個' + k.noun + (multi ? '（可複選）' : '') + '　Esc 取消'] }),
        ...(error ? [Text({ color: 'red', children: [error] })] : []),
        Box({
          flexDirection: 'row', columnGap: 4,
          children: [
            Box({ flexDirection: 'column', children: rows }),
            Box({ flexDirection: 'column', children: detail }),
          ],
        }),
        ...(confirm ? [Text({ children: [' '] }), confirm] : []),
      ],
    })
  })
}
