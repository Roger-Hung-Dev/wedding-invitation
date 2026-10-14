// 渲染參數面板（2026-10-12，使用者要求：完整渲染規格要能自訂參數，做成 mod 用在動畫工作流）
// 兩個階段（分工 2026-10-12 和 zepeto-director 對齊、使用者同意）：
//   film   ＝整支片設定：影響構圖與動作，劇本定案後、分鏡展開前由導演端問一次 → <片名>-breakdown/film.json
//   render ＝完整渲染設定：只影響畫質與檔案，所有鏡定案後、完整渲染前由動畫端問 → 呼叫端指定的 render.json
// 指令：/render-settings [film|render] [demo]
// 工具：pick_film_settings、pick_render_settings。和 zepeto-picker 一樣開面板後立刻回傳，
//   使用者按 y 時（有給 out 就先寫檔）把設定以使用者訊息送進對話
// 本機限制（2026-10-12 實測，RTX 2080 SUPER 8 GB）：EEVEE 4K 一格約 9 秒；8K 顯示卡記憶體不夠 → 選單不給 8K
// 剪接端要求（zepeto-director）：影格一律 PNG 序列；透明背景用 RGBA PNG（不用 ProRes）；每鏡另交 H.264 mp4 預覽
const PANE = 'render-settings'
const KEYS = '1234567890abcdefghijklmnqsuwxz'   // o＝開大圖、p＝動態預覽、r＝恢復預設、t＝試渲、v＝專家選項、y＝確定，不給參數用
// 剪接樣式庫（字卡、轉場、配色、字型、版面）：選項、說明、縮圖都從樣式庫來，新增樣式不用改 mod（2026-10-12）
const EDIT_LIB = 'D:/SideProject/wedding-invitation/.claude/docs/data/blender/library/edit-styles-zepeto'
const PREVIEW_TPL = 'D:/render-work/zepeto-anim/edit/preview_template.html'   // build_showcase.py 產生；按 p 時填入目前的值、用瀏覽器打開
const PREVIEW_NOW = 'D:/render-work/zepeto-anim/edit/preview_now.html'
const SHOWCASE = 'https://claude.ai/artifact/VmCmdM4CKkNChZtqij1XQ1'
let EDIT = []                 // 開面板時從 catalog.json 產生
let editCat = null
// 試渲：用背景 Blender 渲樣張場景（坐餐桌喝紅酒、穿西裝）的一格，顯示在右邊（2026-10-12 使用者：參數要先看到效果）
const BLENDER = 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe'
const MANIFEST = 'D:/render-work/zepeto-anim/sample/samples.json'   // 樣張總表：每鏡定案時由 t_sample.register() 登記（樣張檔＋可試渲的畫面）
const FALLBACK = [{ id: 'sit_test', label: '坐餐桌喝紅酒（測試）', kind: 'test', blend: 'D:/render-work/zepeto-anim/sample/sit_sample.blend',
  frames: [{ t: 2.6, label: '拿起杯子' }, { t: 5.1, label: '喝（臉、杯子）' }, { t: 7.7, label: '手快速收回（看動態模糊）' }, { t: 9.5, label: '手擱大腿（靜態）' }] }]
const SAMPLE_PY = 'D:/render-work/zepeto-anim/scripts/sample_render.py'
const TRIAL_DIR = 'D:/render-work/zepeto-anim/sample/trial'
const CMP_PAGE = 'https://claude.ai/artifact/KaC1ZqHyfqnJgbrULR3dq9'

// ── 參數表：opts＝可選值（第一個是預設，除非有 def）、show＝選項怎麼顯示、help＝白話說明、when＝什麼時候調 ──
const FILM = [
  { id: 'aspect', name: '畫面方向', opts: ['16:9', '9:16', '1:1'], show: { '16:9': '橫式 16:9', '9:16': '直式 9:16', '1:1': '方形 1:1' },
    help: '整支片的長寬比。決定鏡頭怎麼擺、角色站在畫面哪裡、字卡留白在哪邊', when: '喜帖網站多半用手機看，可以考慮直式' },
  { id: 'fps', name: '每秒格數', opts: [24, 25, 30, 60], def: 30,
    help: '動作資料是一秒 30 格做、30 格量的', when: '24／25：動作會抽樣，短暫接觸（例：拇指按 3 格）要確認還看得到；60：要補格、重量穿模，渲染時間加倍' },
  { id: 'handles_s', name: '前後多渲', opts: [0, 0.5, 1], def: 0.5, show: { 0: '不多渲', 0.5: '各 0.5 秒', 1: '各 1 秒' },
    help: '每鏡頭尾多做多渲的長度，留給轉場', when: '轉場比較長（例：慢慢溶接）時選 1 秒' },
  { id: 'background', name: '背景', opts: ['scene', 'alpha'], show: { scene: '場景一起渲', alpha: '透明背景' },
    help: '透明背景＝只渲角色和道具，之後在剪接疊到別的畫面上', when: '要換背景或疊實拍照片時選透明' },
  { id: 'occluders', name: '換景遮擋', opts: ['3d', 'post'], show: { '3d': '3D 一起渲', post: '後製另做' },
    help: '換景接縫的柱子（B3→B4）、門框（B5→B6）', when: '3D 一起渲比較自然；後製另做比較好改' },
  { id: 'caption', name: '字卡留白', opts: ['auto', 'left', 'right', 'bottom', 'none'],
    show: { auto: '跟畫面方向（橫＝左 40%、直＝下 30%）', left: '左側 40%', right: '右側 40%', bottom: '下方 30%', none: '不留' },
    help: '畫面留給字卡的區域，角色和道具不放進去', when: '劇本改了字卡位置時' },
]

const RENDER = [
  { id: 'preset', name: '預設組合', opts: ['final', 'preview'], show: { final: '正式', preview: '快速預覽（720p、取樣 16、只出 mp4）' },
    help: '快速預覽用來先看效果，正式才出 PNG 影格', when: '第一次渲某鏡、或改了專家選項，先跑快速預覽' },
  { id: 'height', name: '解析度', opts: [720, 1080, 1440, 2160], def: 1080, show: { 720: '720p', 1080: '1080p', 1440: '1440p', 2160: '4K' },
    help: '短邊的像素數（直式時是寬）。本機最高 4K；8K 顯示卡記憶體不夠', when: '要放大或裁切畫面時用 4K' },
  { id: 'samples', name: '取樣數', opts: [16, 32, 64, 128], def: 64,
    help: '越高邊緣越平滑、雜點越少', when: '實測 16 和 64 速度差不多，一般用 64' },
  { id: 'shadow', name: '陰影品質', opts: ['low', 'mid', 'high'], def: 'mid', show: { low: '低', mid: '中', high: '高' },
    help: '陰影邊緣的細緻度（內含陰影解析度、射線數）', when: '手指、杯腳的影子糊掉時選高' },
  { id: 'raytracing', name: '光線追蹤反射', opts: [false, true], show: { false: '關', true: '開' },
    help: '玻璃、地板的反光比較真實，比較慢', when: '有鏡面或玻璃特寫時' },
  { id: 'motion_blur', name: '動態模糊', opts: [false, true], show: { false: '關', true: '開' },
    help: '快速動作有拖影', when: '黏土風通常不開；揮手、轉身很快時可以開' },
  { id: 'dof', name: '景深（背景模糊）', opts: [false, true], show: { false: '關', true: '開' },
    help: '對焦以外的地方模糊；光圈照各鏡分鏡展開的鏡頭設定', when: '特寫要凸顯主角時' },
  { id: 'look', name: '色調', opts: ['Standard', 'AgX', 'Filmic', 'Khronos PBR Neutral'],
    show: { Standard: '標準（目前用的）', AgX: 'AgX（亮部柔、不過曝）', Filmic: 'Filmic（電影感）', 'Khronos PBR Neutral': '中性（顏色最忠實）' },
    help: '整支片的色彩轉換（Blender 的 View Transform）', when: '亮的地方過曝發白、或想要電影感時' },
  { id: 'exposure', name: '曝光', opts: [-1, -0.5, 0, 0.5, 1], def: 0, show: { '-1': '−1（暗）', '-0.5': '−0.5', 0: '0', 0.5: '+0.5', 1: '+1（亮）' },
    help: '在場景原本的曝光上再加減（目前場景是 −0.5）', when: '整體看起來太暗或太亮時' },
  { id: 'mp4_quality', name: 'mp4 預覽品質', opts: ['HIGH', 'MEDIUM'], show: { HIGH: '高', MEDIUM: '中（檔案小）' },
    help: '每鏡另交的 H.264 預覽影片', when: '要傳給別人看、檔案太大時選中' },
  { id: 'jobs', name: '同時跑幾個', opts: [1, 2, 3], show: { 1: '1 個', 2: '2 個', 3: '3 個' },
    help: '背景 Blender 同時渲幾鏡', when: '1080p 可以 2 個；4K 只能 1 個（8 GB 顯示卡）' },
  { id: 'timecode', name: '預覽加時間碼', opts: [true, false], show: { true: '加', false: '不加' },
    help: '只加在 mp4 預覽上，PNG 影格不加', when: '審看時方便說「第幾秒」' },
]

// 專家選項：EEVEE 細部（2026-10-12 從 Blender 5.2 讀出的屬性名寫在 bl）
const EXPERT = [
  { id: 'gi_diffuse_bounces', bl: 'eevee.gi_diffuse_bounces', name: '間接光反彈次數', opts: [1, 2, 3, 5], def: 3,
    help: '光在牆壁、地板之間反彈幾次', when: '室內角落死黑時調高' },
  { id: 'use_fast_gi', bl: 'eevee.use_fast_gi', name: '快速全域光', opts: [false, true], show: { false: '關', true: '開' },
    help: '用比較省的算法補環境光', when: '想要柔和的環境光又不想太慢' },
  { id: 'gi_glossy_clamp', bl: 'eevee.gi_glossy_clamp', name: '反光亮點上限', opts: [0, 10, 5, 2], def: 0, show: { 0: '不限', 10: '10', 5: '5', 2: '2（最壓）' },
    help: '限制過亮的小亮點', when: '畫面有閃爍白點時調低' },
  { id: 'shadow_resolution_scale', bl: 'eevee.shadow_resolution_scale', name: '陰影解析度倍率', opts: [1, 0.5, 0.25], show: { 1: '1×（最高）', 0.5: '0.5×', 0.25: '0.25×' },
    help: '蓋過「陰影品質」的解析度部分（Blender 上限 1×）', when: '陰影鋸齒時保持 1×；想省顯示卡記憶體才調低' },
  { id: 'shadow_ray_count', bl: 'eevee.shadow_ray_count', name: '陰影射線數', opts: [1, 2, 4],
    help: '柔和陰影算得多細', when: '陰影有顆粒感時調高' },
  { id: 'shadow_step_count', bl: 'eevee.shadow_step_count', name: '陰影步數', opts: [6, 12, 16],
    help: '柔和陰影的平滑度', when: '陰影有條紋時調高' },
  { id: 'motion_blur_steps', bl: 'eevee.motion_blur_steps', name: '動態模糊步數', opts: [1, 2, 4],
    help: '越多拖影越平滑、越慢', when: '開了動態模糊且拖影有斷層時' },
  { id: 'filter_size', bl: 'render.filter_size', name: '邊緣柔化', opts: [1.5, 1.0, 2.0], show: { 1.5: '1.5（預設）', 1: '1.0（銳利）', 2: '2.0（柔）' },
    help: '像素邊緣混合的範圍', when: '畫面太利或有細碎鋸齒時' },
  { id: 'use_overscan', bl: 'eevee.use_overscan', name: '畫面外延伸', opts: [false, true], show: { false: '關', true: '開' },
    help: '多算一點畫面外的東西', when: '畫面邊緣的反光、陰影不對時' },
  { id: 'png_depth', bl: 'image_settings.color_depth', name: 'PNG 色彩深度', opts: ['8', '16'], show: { 8: '8 bit', 16: '16 bit（要調色時）' },
    help: '影格的色彩精細度；16 bit 檔案大一倍', when: '剪接要調色時選 16' },
]

let stage = 'film'
let vals = {}
let expert = false
let focus = null               // 正在看說明的參數 id
let ctx = {}                   // 呼叫端給的：film、out、shots、current
let shotsOn = new Set()
let trial = null              // { state: 'running'|'done'|'error', file, sec, msg, at }
// 試渲用樣張的哪一格（只影響試渲，不寫進設定）。樣張是坐餐桌喝紅酒；之後各鏡定案後可以換成那一鏡的樣張
let samples = FALLBACK        // 試渲鏡頭清單（開面板時讀總表）
let sampleIdx = 0
let trialIdx = 0
const curSample = () => samples[sampleIdx] || samples[0]
const curFrame = () => (curSample().frames || [])[trialIdx] || { t: 2.6, label: '' }

const DEMO_SHOTS = ['b0', 'b1_b2', 'b2', 'b3', 'b4', 'b5', 'b6']
const defOf = (p) => (p.def !== undefined ? p.def : p.opts[0])
const showOf = (p, v) => (p.show && p.show[String(v)] !== undefined ? p.show[String(v)] : String(v))
const params = () => (stage === 'film' ? [...FILM, ...EDIT] : expert ? [...RENDER, ...EXPERT] : RENDER)
const allParams = () => (stage === 'film' ? [...FILM, ...EDIT] : [...RENDER, ...EXPERT])

// 樣式庫 → 面板參數（id 前面加 e_，寫進 film.json 的 edit 段時用 key）
function editParams(cat) {
  const list = (key, name, kind, items, help) => ({ id: 'e_' + key, key, kind, name, help, when: '按 p 在瀏覽器看動態預覽；所有樣式一起比較看展示頁',
    opts: items.map((x) => x.id), def: cat.defaults[key], show: Object.fromEntries(items.map((x) => [x.id, x.name])),
    desc: Object.fromEntries(items.map((x) => [x.id, (x.desc || '') + (x.when ? '　適合：' + x.when : '')])) })
  const num = (key) => { const n = cat.numbers[key]; return { id: 'e_' + key, key, name: n.name, help: n.desc, when: '按 p 在瀏覽器看動態預覽',
    opts: n.opts, def: cat.defaults[key], show: n.show || Object.fromEntries(n.opts.map((o) => [String(o), o + n.unit])) } }
  return [list('caption_style', '字卡樣式', 'caption', cat.captions, '字卡怎麼進場、退場'), list('font', '字型', 'font', cat.fonts, '字卡的字型'),
    list('palette', '字卡配色', 'palette', cat.palettes, '字卡底色、標題色、內容色'), list('layout', '版面', 'layout', cat.layouts, '字卡放左欄或疊在畫面上'),
    list('transition', '轉場', 'transition', cat.transitions, '鏡與鏡之間怎麼換（換景接縫的柱子、門框在 3D 裡另外做）'),
    num('transition_s'), num('caption_speed'), num('title_size')]
}
const editVals = () => Object.fromEntries(EDIT.map((p) => [p.key, vals[p.id]]))

async function openPreview($) {
  try {
    const tpl = await $.fs.read(PREVIEW_TPL)
    await $.fs.write(PREVIEW_NOW, tpl.replace('/*SETTINGS*/null', JSON.stringify(editVals())))
    await $.process.run(['cmd', '/c', 'start', '', PREVIEW_NOW.replace(/\//g, '\\')])
  } catch (err) { $.ui.toast('開不了動態預覽（先跑一次樣式庫的 build_showcase.py）：' + String(err)) }
}

function reset() {
  vals = {}
  for (const p of allParams()) vals[p.id] = defOf(p)
  const cur = (ctx.current && (stage === 'film' ? ctx.current : ctx.current.settings || ctx.current)) || {}
  for (const p of allParams()) if (cur[p.id] !== undefined && p.opts.some((o) => String(o) === String(cur[p.id]))) vals[p.id] = cur[p.id]
  if (stage === 'film' && cur.caption_safe) vals.caption = cur.caption_safe.side || 'none'
  const ce = (stage === 'film' && (ctx.currentEdit || cur.edit)) || null      // 剪接設定在 edit.json（舊版寫在 film.json 的 edit 段也認）
  if (ce) for (const p of EDIT) if (ce[p.key] !== undefined && p.opts.some((o) => String(o) === String(ce[p.key]))) vals[p.id] = ce[p.key]
  shotsOn = new Set(ctx.shots || [])
}

function cycle(p) {
  const i = p.opts.findIndex((o) => String(o) === String(vals[p.id]))
  vals[p.id] = p.opts[(i + 1) % p.opts.length]
}

const ASPECT = { '16:9': [16, 9], '9:16': [9, 16], '1:1': [1, 1] }
function sizeOf(aspect, h) {
  const [a, b] = ASPECT[aspect] || ASPECT['16:9']
  const short = h; const long = Math.round((short * Math.max(a, b)) / Math.min(a, b) / 2) * 2
  return a >= b ? [long, short] : [short, long]
}

function captionOf(aspect, c) {
  if (c === 'none') return null
  const side = c === 'auto' ? (aspect === '9:16' ? 'bottom' : 'left') : c
  return { side, ratio: side === 'bottom' ? 0.3 : 0.4 }
}

// 提醒：可能撐不住或要多做事的組合
function warnings() {
  const w = []
  if (stage === 'film') {
    if (vals.fps === 60) w.push('60 fps：動作要補格，補出來的格子要重新量穿模；渲染時間加倍')
    if (vals.fps === 24 || vals.fps === 25) w.push(vals.fps + ' fps：動作從 30 格抽樣，3 格以內的接觸動作要確認還看得到')
    if (vals.background === 'alpha' && vals.occluders === '3d') w.push('透明背景＋遮擋物 3D 一起渲：柱子、門框會留在角色那一層')
    if (ctx.current && ctx.current.version) w.push('會變成第 ' + (ctx.current.version + 1) + ' 版：已開工的鏡頭會顯示「上游已更新」')
  } else {
    const film = ctx.filmSettings || {}
    const preview = vals.preset === 'preview'
    const h = preview ? 720 : vals.height
    if (!preview && h === 2160 && vals.jobs > 1) w.push('4K 同時跑 ' + vals.jobs + ' 個：8 GB 顯示卡很可能不夠，建議 1 個')
    if (!preview && h === 1440 && vals.jobs > 2) w.push('1440p 同時跑 3 個：顯示卡記憶體可能不夠')
    if (vals.motion_blur && !/快/.test(curFrame().label)) w.push('動態模糊要在動得快的畫面才看得出來：試渲畫面換成標「動得快」的那一格')
    if (vals.motion_blur_steps > 1 && !vals.motion_blur) w.push('動態模糊沒開，「動態模糊步數」不會有作用')
    if (film.background === 'alpha') w.push('整支片是透明背景：影格會輸出 RGBA PNG')
    if (ctx.shots && shotsOn.size === 0) w.push('還沒選要渲哪幾鏡')
  }
  return w
}

function result() {
  const at = new Date().toISOString()
  if (stage === 'film') {
    const cur = ctx.current || {}
    return {
      schema: 1, film: ctx.film || cur.film || '', version: (cur.version || 0) + 1,
      aspect: vals.aspect, fps: vals.fps, handles_s: vals.handles_s, background: vals.background, occluders: vals.occluders,
      caption_safe: captionOf(vals.aspect, vals.caption), decided_at: at, notes: cur.notes || '',
    }
  }
  const film = ctx.filmSettings || {}
  const preview = vals.preset === 'preview'
  const h = preview ? 720 : vals.height
  const settings = {}
  for (const p of RENDER) settings[p.id] = vals[p.id]
  const ex = {}
  for (const p of EXPERT) if (String(vals[p.id]) !== String(defOf(p))) ex[p.bl] = vals[p.id]
  return {
    schema: 1, film: ctx.film || film.film || '', film_version: film.version || null, decided_at: at,
    resolution: sizeOf(film.aspect || '16:9', h), fps: film.fps || 30, handles_s: film.handles_s !== undefined ? film.handles_s : 0.5,
    frames: preview ? null : { format: 'PNG', color_mode: film.background === 'alpha' ? 'RGBA' : 'RGB', color_depth: String(vals.png_depth) },
    mp4: { codec: 'H264', quality: preview ? 'MEDIUM' : vals.mp4_quality, timecode: vals.timecode },
    settings: { ...settings, samples: preview ? 16 : vals.samples }, expert_overrides: ex,
    shots: ctx.shots ? ctx.shots.filter((s) => shotsOn.has(s)) : null,
  }
}

// 目前面板的值 → sample_render.py 的 set（名稱一致）
function trialSet() {
  const film = stage === 'film' ? { aspect: vals.aspect, background: vals.background } : ctx.filmSettings || {}
  const preview = stage === 'render' && vals.preset === 'preview'
  const h = stage === 'film' ? 720 : preview ? 720 : vals.height
  const s = { resolution: sizeOf(film.aspect || '16:9', h), background: film.background || 'scene' }
  if (stage === 'film') return Object.assign(s, { samples: 32 })
  Object.assign(s, { samples: preview ? 16 : vals.samples, shadow: vals.shadow, raytracing: vals.raytracing, motion_blur: vals.motion_blur,
    dof: vals.dof, look: vals.look, exposure: vals.exposure, expert: {} })
  for (const p of EXPERT) if (p.bl.startsWith('eevee.') || p.bl.startsWith('render.')) s.expert[p.bl] = vals[p.id]
  return s
}

async function runTrial($) {
  if (trial && trial.state === 'running') return
  const stamp = new Date().toISOString().replace(/[-:T.Z]/g, '').slice(0, 14)
  const set = trialSet()
  const t = curFrame().t; const blend = curSample().blend
  const jobs = TRIAL_DIR + '/jobs_' + stamp + '.json'
  const name = 'trial_' + stamp
  try {
    await $.fs.write(jobs, JSON.stringify({ out_dir: TRIAL_DIR, jobs: [{ name, t, png: true, set }] }))
  } catch (err) { trial = { state: 'error', msg: '寫不進試渲設定：' + String(err) }; $.ui.invalidate('ui.render'); return }
  trial = { state: 'running', at: Date.now(), res: set.resolution.join('×') }
  $.ui.invalidate('ui.render')
  $.process.run([BLENDER, '-b', blend, '-P', SAMPLE_PY, '--', jobs, 'BODY=groom']).then((r) => {
    const m = /SAMPLE \{'name': '[^']+', 'sec': ([0-9.]+)/.exec(r.stdout || '')
    trial = r.exitCode === 0 && m
      ? { state: 'done', file: TRIAL_DIR + '/' + name + '.png', sec: m[1], total: Math.round((Date.now() - trial.at) / 1000), res: trial.res }
      : { state: 'error', msg: '試渲失敗：' + String(r.stderr || r.stdout || '').slice(-300) }
    $.ui.invalidate('ui.render')
  }, (err) => { trial = { state: 'error', msg: '試渲失敗：' + String(err) }; $.ui.invalidate('ui.render') })
}

// 送出的訊息格式（工作流照這個解析）：
//   第一行「渲染參數（整支片設定｜完整渲染設定）：<片名>」，有寫檔時接「已寫入 <路徑>」
//   之後是 ```json 區塊（內容同寫進檔案的）
// 整支片設定拆成兩個檔（2026-10-12 和導演端約定）：film.json＝片子規格（影響動畫，是 anim 紀錄的上游）；
// edit.json＝字卡與轉場（只影響剪接，改了不會讓動畫變「上游已更新」）。整支片設定送出的 JSON 是 { film: …, edit: … }
function editPathOf(filmPath) { return filmPath ? filmPath.replace(/[^/\\]*$/, 'edit.json') : '' }
function sameEdit(ce) { return EDIT.every((p) => String(ce[p.key]) === String(vals[p.id])) }

function message(obj, wrote, specSame) {
  const head = '渲染參數（' + (stage === 'film' ? '整支片設定' : '完整渲染設定') + '）：' + ((obj.film && obj.film.film !== undefined ? obj.film.film : obj.film) || '（未指定片名）')
  return [head + (wrote ? '，已寫入 ' + wrote : ''), ...(specSame ? ['片子規格：未變（沿用 film.json）'] : []), '```json', JSON.stringify(obj, null, 2), '```'].join('\n')
}

async function readJson($, path) {
  if (!path) return null
  try { if (await $.fs.exists(path)) return JSON.parse(await $.fs.read(path)) } catch (err) { $.ui.toast('讀不懂 ' + path + '：' + String(err)) }
  return null
}

async function open($, st, input, demo) {
  stage = st; expert = false; focus = null; trial = null; trialIdx = 0; sampleIdx = 0
  try {
    editCat = JSON.parse(await $.fs.read(EDIT_LIB + '/catalog.json')); EDIT = editParams(editCat)
  } catch (err) { EDIT = []; editCat = null; $.ui.toast('剪接樣式庫讀不懂，這次不顯示字卡與轉場：' + String(err)) }
  try {
    const m = (await $.fs.exists(MANIFEST)) ? JSON.parse(await $.fs.read(MANIFEST)) : null
    samples = m && m.samples && m.samples.length ? m.samples : FALLBACK
  } catch (err) { samples = FALLBACK; $.ui.toast('樣張總表讀不懂，先用內建樣張：' + String(err)) }
  const want = input.shots && input.shots.length ? samples.findIndex((x) => input.shots.includes(x.id)) : samples.findIndex((x) => x.kind === 'shot')
  if (want >= 0) sampleIdx = want
  ctx = {
    film: input.film || '', out: input.out || '',
    shots: input.shots && input.shots.length ? input.shots : demo && st === 'render' ? DEMO_SHOTS : null,
    current: await readJson($, input.current || (st === 'film' ? input.out : '')),
    editOut: st === 'film' ? (input.edit_out || editPathOf(input.out || '')) : '',
    currentEdit: st === 'film' ? await readJson($, input.edit_out || editPathOf(input.out || '')) : null,
    filmSettings: st === 'render' ? await readJson($, input.film_json) : null,
    demo: !!demo,
  }
  reset()
  const r = await $.ui.open({ id: PANE, title: st === 'film' ? '整支片設定' : '完整渲染設定', focus: true, closeOnEscape: true, holdToasts: true, rows: 30 })
  $.ui.invalidate('ui.render')
  return r
}

const FORMAT = '使用者按確定後，會送出一則使用者訊息：第一行「渲染參數（…）：<片名>」（有給 out 時接「，已寫入 <out>」），之後是 ```json 設定```。呼叫後結束這一輪，等那則訊息。'

export function register(on) {
  on('session.start', async ($, e, next) => {
    try {
      await $.tool.register({
        name: 'pick_film_settings',
        description: '開「整支片設定」面板（畫面方向、fps、前後多渲、背景、換景遮擋、字卡留白，加上剪接樣式庫的字卡樣式、字型、配色、版面、轉場；規格寫進 film.json（影響動畫），字卡與轉場寫進同資料夾的 edit.json（只影響剪接）。劇本定案後、分鏡展開前由導演端呼叫一次。' + FORMAT,
        inputSchema: {
          type: 'object',
          properties: {
            film: { type: 'string', description: '片名，例：opening-proposal-b' },
            out: { type: 'string', description: '要寫入的 film.json 完整路徑（片子規格，影響動畫；已存在時會當成目前值、版本 +1）' },
            edit_out: { type: 'string', description: '要寫入的 edit.json 完整路徑（字卡與轉場，只影響剪接）；不給就放在 film.json 同一個資料夾' },
            current: { type: 'string', description: '目前設定檔路徑（不給就用 out）' },
          },
          required: ['film'],
        },
        isDeferred: false,
      })
      await $.tool.register({
        name: 'pick_render_settings',
        description: '開「完整渲染設定」面板（解析度、取樣、陰影、效果、mp4、同時跑幾個、專家選項、要渲哪幾鏡）。所有鏡定案後、完整渲染前由動畫端呼叫。' + FORMAT,
        inputSchema: {
          type: 'object',
          properties: {
            film: { type: 'string', description: '片名' },
            film_json: { type: 'string', description: '整支片設定 film.json 路徑（解析度的長寬比、fps、背景照它）' },
            shots: { type: 'array', items: { type: 'string' }, description: '可以渲的鏡（只給已定案的），例：["b1_b2","b2"]' },
            out: { type: 'string', description: '要寫入的 render.json 完整路徑（可不給，只送訊息）' },
            current: { type: 'string', description: '上次的 render.json，當成預設值' },
          },
          required: ['film', 'film_json'],
        },
        isDeferred: false,
      })
      await $.command.register({ name: 'render-settings', description: '開渲染參數面板（film＝整支片設定、render＝完整渲染設定；demo＝試看，不寫檔不送出）', argumentHint: '[film|render] [demo]' })
    } catch (err) {
      $.ui.toast('render-settings 註冊失敗：' + String((err && err.message) || err))
    }
    return next(e)
  })

  on('command.run', { command: 'render-settings' }, async ($, e) => {
    const a = e.args || ''
    await open($, /render/.test(a) ? 'render' : 'film', {}, true)
    return {}
  })
  on('tool.call', { tool: 'mcp__render-settings__pick_film_settings' }, async ($, e) => {
    const r = await open($, 'film', e, false)
    const where = r && r.isPlaced === false ? '（面板在等較寬的終端機：' + r.reason + '）' : ''
    return { result: '已開啟整支片設定面板' + where + '。請結束這一輪，等使用者送出「渲染參數（整支片設定）…」的訊息。' }
  })
  on('tool.call', { tool: 'mcp__render-settings__pick_render_settings' }, async ($, e) => {
    const r = await open($, 'render', e, false)
    if (!ctx.filmSettings) $.ui.toast('讀不到整支片設定 ' + (e.film_json || '') + '：長寬比、fps 先用 16:9、30')
    const where = r && r.isPlaced === false ? '（面板在等較寬的終端機：' + r.reason + '）' : ''
    return { result: '已開啟完整渲染設定面板' + where + '。請結束這一輪，等使用者送出「渲染參數（完整渲染設定）…」的訊息。' }
  })

  on('ui.render', { component: 'Pane' }, async ($, e, next) => {
    if (e.requestId !== PANE) return next(e)
    const { Box, Text, Button, Image } = $.ui.resolve(e)
    const redraw = () => $.ui.invalidate('ui.render')
    const ps = params()
    let k = 0

    const row = (p, head) => {
      const key = KEYS[k++] || ''
      const changed = String(vals[p.id]) !== String(defOf(p))
      return [
        ...(head ? [Text({ key: 'h-' + p.id, bold: true, children: [head] })] : []),
        Box({
          key: 'row-' + p.id, flexDirection: 'row', columnGap: 1,
          children: [
            Button({
              key: 'p-' + p.id, label: p.name, hotkey: key || undefined, plain: true, ...(k === 1 ? { autoFocus: true } : {}),
              onPress: () => { if (focus === p.id) cycle(p); focus = p.id; redraw() },
            }),
            Text({ color: changed ? 'cyan' : undefined, children: ['：' + showOf(p, vals[p.id])] }),
          ],
        }),
      ]
    }

    const left = []
    ps.forEach((p, i) => left.push(...row(p, stage === 'render' && expert && i === RENDER.length ? '── 專家選項（不懂可以不動）──'
      : stage === 'film' && EDIT.length && i === FILM.length ? '── 字卡與轉場（剪接樣式庫，按 p 看動態預覽）──' : null)))
    {
      left.push(Text({ key: 'trh', bold: true, children: ['── 試渲（只影響試渲，不寫進設定）──'] }))
      const k1 = KEYS[k++] || ''
      left.push(Box({ key: 'row-trial-shot', flexDirection: 'row', columnGap: 1, children: [
        Button({ key: 'p-trialshot', label: '試渲鏡頭', hotkey: k1 || undefined, plain: true,
          onPress: () => { sampleIdx = (sampleIdx + 1) % samples.length; trialIdx = 0; redraw() } }),
        Text({ children: ['：' + curSample().label + (samples.length > 1 ? '（' + (sampleIdx + 1) + '/' + samples.length + '）' : '')] }),
      ] }))
      const k2 = KEYS[k++] || ''
      left.push(Box({ key: 'row-trial-frame', flexDirection: 'row', columnGap: 1, children: [
        Button({ key: 'p-trialframe', label: '試渲畫面', hotkey: k2 || undefined, plain: true,
          onPress: () => { trialIdx = (trialIdx + 1) % Math.max(1, (curSample().frames || []).length); redraw() } }),
        Text({ children: ['：' + curFrame().t + ' 秒 ' + curFrame().label] }),
      ] }))
      if (curSample().note) left.push(Text({ key: 'trn', dimColor: true, children: ['  ' + curSample().note] }))
    }
    if (stage === 'render' && ctx.shots) {
      left.push(Text({ key: 'shh', bold: true, children: ['── 要渲哪幾鏡 ──'] }))
      for (const s of ctx.shots) {
        const key = KEYS[k++] || ''
        left.push(Button({
          key: 's-' + s, label: (shotsOn.has(s) ? '[x] ' : '[ ] ') + s, hotkey: key || undefined, plain: true,
          onPress: () => { shotsOn.has(s) ? shotsOn.delete(s) : shotsOn.add(s); redraw() },
        }))
      }
    }

    const fp = focus && allParams().find((p) => p.id === focus)
    const film = ctx.filmSettings
    const detail = [
      ...(stage === 'render'
        ? [Text({ dimColor: true, children: [film ? '整支片：' + film.aspect + '、' + film.fps + ' fps、' + (film.background === 'alpha' ? '透明背景' : '場景一起渲') : '（沒有整支片設定，先用 16:9、30 fps）'] }),
           Text({ children: ['輸出尺寸：' + sizeOf((film && film.aspect) || '16:9', vals.preset === 'preview' ? 720 : vals.height).join('×')] }),
           Text({ children: [' '] })]
        : []),
      ...(fp
        ? [Text({ bold: true, children: [fp.name] }), Text({ children: [fp.help] }), Text({ dimColor: true, children: ['什麼時候調：' + fp.when] }),
           Text({ dimColor: true, children: ['可選：' + fp.opts.map((o) => showOf(fp, o)).join('／')] }),
           Text({ dimColor: true, children: ['再按一次同一個鍵換下一個值'] }),
           ...(fp.desc ? [Text({ children: [' '] }), Text({ bold: true, children: [showOf(fp, vals[fp.id])] }), Text({ children: [fp.desc[vals[fp.id]] || ''] })] : []),
           ...(fp.kind && e.surface === 'terminal' ? [Image({ key: 'thumb-' + fp.id + '-' + vals[fp.id], source: { file: EDIT_LIB + '/thumbs/' + fp.kind + '_' + vals[fp.id] + '.png', format: 'png' }, columns: 40, rows: 11, alt: '（這個終端機不能顯示縮圖，按 p 看動態預覽）' })] : []),
           ...(fp.key ? [Text({ dimColor: true, children: ['所有樣式一起比較：' + SHOWCASE] })] : [])]
        : [Text({ dimColor: true, children: ['按左邊參數的鍵：第一次看說明，再按一次換值'] })]),
      ...warnings().flatMap((w, i) => [Text({ key: 'w' + i, color: 'yellow', children: ['⚠ ' + w] })]),
      Text({ children: [' '] }),
      ...(trial === null ? [Text({ dimColor: true, children: ['按 t 用目前的值試渲一格樣張（約 20～30 秒）；各選項的差別也可以看比較頁：' + CMP_PAGE] })]
        : trial.state === 'running' ? [Text({ color: 'cyan', children: ['試渲中（' + trial.res + '）…背景 Blender 開檔加渲染約 20～30 秒'] })]
        : trial.state === 'error' ? [Text({ color: 'red', children: [trial.msg] })]
        : [Text({ children: ['試渲完成：' + trial.res + '，渲一格 ' + trial.sec + ' 秒（含開檔共 ' + trial.total + ' 秒）'] }),
           ...(e.surface === 'terminal' ? [Image({ key: 'trial-img', source: { file: trial.file, format: 'png' }, columns: 48, rows: 14, alt: '（這個終端機不能顯示圖片，按 o 開大圖）' })] : []),
           Text({ dimColor: true, children: [trial.file] })]),
    ]

    const bottom = [
      Button({ key: 'reset', label: '恢復預設', hotkey: 'r', plain: true, onPress: () => { reset(); redraw() } }),
      ...(stage === 'film' && EDIT.length ? [Button({ key: 'preview', label: '動態預覽', hotkey: 'p', plain: true, onPress: () => openPreview($) })] : []),
      Button({ key: 'trial', label: trial && trial.state === 'running' ? '試渲中…' : '試渲一格', hotkey: 't', plain: true, onPress: () => runTrial($) }),
      ...(trial && trial.state === 'done'
        ? [Button({ key: 'open', label: '開大圖', hotkey: 'o', plain: true,
            onPress: async () => { try { await $.process.run(['cmd', '/c', 'start', '', trial.file.replace(/\//g, '\\')]) } catch (err) { $.ui.toast('開不了：' + String(err)) } } })]
        : []),
      ...(stage === 'render'
        ? [Button({ key: 'expert', label: expert ? '收起專家選項' : '展開專家選項', hotkey: 'v', plain: true, onPress: () => { expert = !expert; redraw() } })]
        : []),
      Button({
        key: 'confirm', label: '確定', hotkey: 'y', plain: true,
        onPress: async () => {
          const obj = result()
          await $.ui.close({ id: PANE })
          let editObj = null
          if (stage === 'film' && EDIT.length) {
            const ce = ctx.currentEdit || {}
            editObj = { schema: 1, film: obj.film, version: (ce.version || 0) + (sameEdit(ce) ? 0 : 1), ...editVals(), decided_at: obj.decided_at }
          }
          // 規格欄位和現有 film.json 一樣（只改了字卡與轉場）→ 不重寫 film.json：
          // 重寫的話 decided_at 一變 sha 就變，status_check --verify 會判紀錄壞掉、升版又會讓動畫全部變「上游已更新」（2026-10-12 和導演端約定）
          const SPEC = ['aspect', 'fps', 'handles_s', 'background', 'occluders', 'caption_safe']
          const specSame = stage === 'film' && ctx.current && SPEC.every((k) => JSON.stringify(ctx.current[k] ?? null) === JSON.stringify(obj[k] ?? null))
          const filmObj = specSame ? ctx.current : obj
          const sent = editObj ? { film: filmObj, edit: editObj } : obj
          if (ctx.demo) { $.ui.toast('試看模式，不寫檔、不送出：\n' + (specSame ? '片子規格：未變\n' : '') + JSON.stringify(sent)); return }
          let wrote = ''
          if (ctx.out) {
            if (!specSame) {
              try { await $.fs.write(ctx.out, JSON.stringify(obj, null, 2) + '\n'); wrote = ctx.out } catch (err) { $.ui.toast('寫不進 ' + ctx.out + '：' + String(err)) }
            }
            if (editObj && ctx.editOut) {
              try { await $.fs.write(ctx.editOut, JSON.stringify(editObj, null, 2) + '\n'); wrote = (wrote ? wrote + '、' : '') + ctx.editOut } catch (err) { $.ui.toast('寫不進 ' + ctx.editOut + '：' + String(err)) }
            }
          }
          $.prompt.submit({ text: message(sent, wrote, specSame), asUser: true })
        },
      }),
    ]

    return Box({
      flexDirection: 'column',
      children: [
        Text({ dimColor: true, children: [(stage === 'film' ? '整支片設定（劇本定案後問一次）' : '完整渲染設定') + (ctx.film ? '：' + ctx.film : '') + '　改過的值是青色　Esc 取消'] }),
        Box({
          flexDirection: 'row', columnGap: 4,
          children: [Box({ flexDirection: 'column', children: left }), Box({ flexDirection: 'column', children: detail })],
        }),
        Text({ children: [' '] }),
        Box({ flexDirection: 'row', columnGap: 3, children: bottom }),
      ],
    })
  })
}
