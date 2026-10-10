export const meta = {
  name: 'film-scene-review',
  description: '多幕 3D 影片的批次審看（兩關）：第 1 關每一幕出 Mixamo 骨骼動作（skeleton.json）、第 2 關出快速預覽或完整渲染，每一幕交給 blender-scenario-creator → 彙整成一個有回覆框＋Ctrl+V 貼圖的審看網頁（Claude Artifact）讓使用者一次看完、一次給回饋',
  whenToUse: '開場影片這類「一支片有好幾幕 3D 角色情境」的調整期：使用者要「把每一幕都先做出來給我看，我一次告訴你要修哪裡」、或帶著逐幕回饋要求一起修時使用。先跑 stage=skeleton（第 1 關），每一幕骨骼都確認後才跑 stage=preview（第 2 關）。主控端先問齊要哪幾幕、每幕的模式與回饋，args 帶 production、stage 與 scenes。只改單一幕、或只加一個動作，直接呼叫子代理即可，不必走這條。',
  phases: [
    { title: 'Scenes', detail: 'blender-scenario-creator：每一幕一個，不同 group 並行、同 group 依序' },
    { title: 'Review page', detail: '彙整成審看網頁（回覆框＋貼圖）並發布／更新 Claude Artifact' },
  ],
}

// ---------------------------------------------------------------------------
// 【args 形狀】
// {
//   production: 'opening-v12',          // .claude/docs/data/blender/productions/<production>/
//   stage: 'skeleton' | 'preview',      // 第幾關（fast-iteration.md §0.5）。預設 'preview'
//        // skeleton＝第 1 關：每一幕寫 scripts/mx_scene_<幕>.py、跑 mx_skeleton.py 出 skeleton.json，不渲染
//        // preview＝第 2 關：快速預覽（或 mode=full 的完整渲染）。每一幕骨骼都確認後才走這關
//   round: 1,                           // 第幾輪審看（網頁標題、檔名後綴、回饋 doc 的 round 用）
//   scenes: [{
//     id: '03',                         // 幕代號（檔名 sNN_*、檢查圖 v2_NN_check 用）
//     title: '③ 愛情里程碑進度條',
//     mode: 'new' | 'rerender' | 'fix' | 'existing' | 'full',
//        // new＝這一幕還沒有 3D，照設計稿新做快速預覽
//        // rerender＝已有成品，用現行動作庫重渲快速預覽（不改動作）
//        // fix＝照 feedback 修正後重渲快速預覽
//        // existing＝不渲染，直接把 files 放進審看網頁
//        // full＝使用者已確認，做完整品質渲染
//     brief: '…',                       // 這一幕要做什麼（時間軸、角色、動作、鏡頭；以這裡為準，蓋過規劃表）
//     feedback: ['…'],                  // mode=fix：使用者對這一幕的回饋（原話，逐條；網頁回覆框＋對話裡的「第 N 幕：…」）
//     feedbackImages: ['C:/…/x.png'],   // mode=fix：使用者貼的回饋圖（主控端用 Artifact read 存成本機檔後的絕對路徑）
//     files: { video: '…', sheet: '…', skeleton: 'D:/…/skeleton.json' }, // mode=existing：已有的成品（video／sheet 相對 production 資料夾；skeleton 用絕對路徑）
//     group: 'garden',                  // 選填：同 group 的幕依序跑（會改同一支共用程式時用）；不填＝自己一組
//   }],
//   reviewPageUrl: 'https://claude.ai/artifact/…', // 選填：更新既有審看網頁（同一個網址）
//   publish: true,                      // 預設 true
// }
//
// 【為什麼要 group】幾幕若會改同一支共用程式（例：set_v2.py、shots_v2.py），並行會互相覆寫。
// 主控端把會動到同一支檔的幕放同一個 group；不改共用檔的（rerender／existing）各自一組並行。
// 渲染用背景 Blender，每一幕的影格放 D:\render-work 底下自己的資料夾，彼此不會互蓋。
// ---------------------------------------------------------------------------

const SCENE_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['status', 'sceneId', 'needsUser'],
  properties: {
    sceneId: { type: 'string' },
    status: { type: 'string', enum: ['done', 'partial', 'blocked'], description: 'done＝交付完成且看過圖；partial＝有交付但有沒做完的；blocked＝卡住沒交付' },
    video: { type: 'string', description: 'stage=preview：預覽（或完整）影片，相對 production 資料夾的路徑' },
    skeleton: { type: 'string', description: 'stage=skeleton：skeleton.json 的絕對路徑' },
    segments: { type: 'array', items: { type: 'string' }, description: 'stage=skeleton：每個角色每一段「誰｜開始秒數｜Mixamo 代號 第幾～幾秒｜做什麼」' },
    cover: { type: 'string', description: '封面 jpg（選填）' },
    sheet: { type: 'string', description: '多角度檢查圖 jpg，相對 production 資料夾' },
    timeline: { type: 'array', items: { type: 'string' }, description: '這一幕的時間軸：「秒數｜誰｜做什麼」逐行' },
    numbers: { type: 'array', items: { type: 'string' }, description: '數字檢查：「項目｜門檻｜結果（誰、第幾秒）」逐行' },
    changed: { type: 'array', items: { type: 'string' }, description: '這輪改了什麼（fix／rerender 時列和上一版的差別）' },
    knownIssues: { type: 'array', items: { type: 'string' }, description: '看到但沒修、待使用者決定的' },
    motionSources: { type: 'array', items: { type: 'string' }, description: '用了哪些動作來源（Mixamo 代號＋取用秒數；舊版是真人動作捕捉檔名格號、動作庫代號）' },
    substitutes: { type: 'array', items: { type: 'string' }, description: 'Mixamo 沒有吻合的動作，用哪支代替什麼' },
    tweaks: { type: 'array', items: { type: 'string' }, description: '套用後的微調：哪根骨頭、幾度、為什麼（沒有就空）' },
    needsUser: { type: 'array', items: { type: 'string' } },
    notes: { type: 'string' },
  },
}

const PAGE_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['status', 'artifactUrl', 'pagePath'],
  properties: {
    status: { type: 'string', enum: ['done', 'partial', 'blocked'] },
    artifactUrl: { type: 'string' },
    pagePath: { type: 'string' },
    notes: { type: 'string' },
  },
}

let a = args
if (typeof a === 'string') {
  try { a = JSON.parse(a) } catch (e) { a = null }
}
if (!a || !a.production || !Array.isArray(a.scenes) || !a.scenes.length) {
  log('缺 production 或 scenes。請主控端先問齊要審看哪幾幕。')
  return { error: 'bad-args' }
}
const PROD = `.claude/docs/data/blender/productions/${a.production}`
const round = a.round || 1
const stage = a.stage === 'skeleton' ? 'skeleton' : 'preview'

const MODE_TEXT = {
  preview: {
    new: '這一幕還沒有 3D：照 brief 新做，只交快速預覽。',
    rerender: '已有成品：用「現行動作庫」重渲快速預覽，不改動作設計；回報和舊版相比哪些動作因動作庫更新而改變。若某段明顯僵硬，提出建議但不要大改。',
    fix: '照下面使用者的回饋逐條修正，重渲快速預覽；changed 逐條對應回饋說明怎麼改的，做不到的寫進 knownIssues。',
    full: '使用者已確認這一幕：做完整品質渲染（照製作規格的解析度、取樣、頭髮裙擺物理），舊成品改名加 _old 保留，完整數字檢查後抽格看畫面。',
  },
  skeleton: {
    new: '這一幕還沒有骨骼動作：照 brief 從 Mixamo 動畫挑段落、排時間與站位，寫成 scripts/mx_scene_<幕>.py，出 skeleton.json。',
    fix: '照下面使用者的回饋逐條改 scripts/mx_scene_<幕>.py（換動畫、換段落秒數、站位、面向、開始時間），重出 skeleton.json；changed 逐條對應回饋，做不到的寫進 knownIssues。',
  },
}

const STAGE_TEXT = {
  preview: [
    '這是第 2 關「低畫質預覽」：這一幕的骨骼動作使用者已在第 1 關確認過，動作段落、秒數、站位照 scripts/mx_scene_<幕>.py（② 在 mx_skeleton.py 的 scene_02），不要另外改；只處理套上服裝後才看得到的問題（穿模、接觸點、裙擺、臉被擋）。',
    '規範：blender-motion-library 的 references/fast-iteration.md（§0 Mixamo 原樣套用、可微調但不破壞動作結構；§0.5 兩關審看；§1 快速預覽 ≤ 960×540、不跑頭髮裙擺物理；§2 多角度檢查圖；§3 一次收齊常見問題）。§5 是這條批次審看的交付格式。',
  ],
  skeleton: [
    '這是第 1 關「骨骼動作」：只出 skeleton.json 給 3D 骨架播放器，不渲染、不做服裝或網格檢查。',
    '規範：blender-motion-library 的 references/fast-iteration.md §0（Mixamo 現成動畫原樣套用：只決定用哪一支、取哪幾秒、何時開始、站位與面向，0.3 秒漸變；劇情不改，沒有吻合的挑最接近的）與 §0.5（兩關審看）。',
    `Mixamo 檔案在 D:\\render-work\\mixamo\\raw\\（manifest.json 有每個檔的名稱與用在哪幾幕）。需要還沒下載的動畫：不要找別的來源，寫進 needsUser（下載要主控端問使用者）。`,
    `程式：${PROD}/scripts/mx_skeleton.py（檔頭有用法；scene_02 是寫法範例）。這一幕的組成寫在你自己的 ${PROD}/scripts/mx_scene_<幕>.py，定義 scene()，回傳和 scene_02 同形狀的 dict（chars 的 segs／anchor、props、cam、skirt、dur）；不要改 mx_skeleton.py 與 mixamo_retarget.py。`,
    '寫完自己檢查：每一段的骨架有沒有面向對、兩人有沒有重疊、新娘的腿有沒有踢出蓬裙範圍、道具位置對不對（可以讀 skeleton.json 算距離）。看得出的問題寫進 knownIssues。',
  ],
}

function scenePrompt(s) {
  const imgs = s.mode === 'fix' && s.feedbackImages && s.feedbackImages.length ? s.feedbackImages : []
  return [
    `【worker 模式】你是被 film-scene-review workflow 派來的 blender-scenario-creator。禁止呼叫 AskUserQuestion，問題寫進 needsUser。不 commit、不動任何 .pen 檔。`,
    `製作資料夾：${PROD}/（先讀 README.md、design.md）。這一輪是第 ${round} 輪批次審看。`,
    `幕：${s.id}　${s.title || ''}`,
    `關卡：${stage}。模式：${s.mode}。${(MODE_TEXT[stage] || {})[s.mode] || ''}`,
    ...STAGE_TEXT[stage],
    s.brief ? `這一幕的內容（以這裡為準，蓋過規劃表）：\n${s.brief}` : '',
    s.mode === 'fix' && s.feedback && s.feedback.length ? `使用者回饋（原話）：\n${s.feedback.map((f, i) => `${i + 1}. ${f}`).join('\n')}` : '',
    imgs.length ? `使用者貼的回饋圖（先用 Read 逐張看，圈起來的地方就是要改的）：\n${imgs.map((p, i) => `${i + 1}. ${p}`).join('\n')}` : '',
    '',
    stage === 'skeleton'
      ? `交付：D:\\render-work\\mixamo\\review\\s${s.id}\\skeleton.json（mx_skeleton.py 的預設輸出）；回報 skeleton（絕對路徑）、segments、motionSources、substitutes。`
      : `交付：影片 videos/preview-v2/s${s.id}_*_${s.mode === 'full' ? 'full' : 'quick'}.mp4、檢查圖 pictures/preview-v2/v2_${s.id}_check.jpg（路徑相對製作資料夾）。數字檢查每輪都跑。微調寫進 tweaks。`,
    s.group ? `同一個 group「${s.group}」的其他幕會在你之後依序跑，可以改共用程式，但不要動別幕的設定。` : '你和其他幕並行：不要修改會被別幕共用的程式（例 set_v2.py、shots_v2.py、mx_skeleton.py）；非改不可就把這一幕的邏輯放到自己的新檔，或停下來寫進 needsUser。影格放 D:\\render-work 底下這一幕自己的資料夾。',
  ].filter(Boolean).join('\n').replace(/<幕>/g, s.id)
}

// ── Scenes ──
phase('Scenes')
const groups = {}
for (const s of a.scenes) {
  const g = s.group || `__${s.id}`
  ;(groups[g] = groups[g] || []).push(s)
}
const groupResults = await parallel(Object.values(groups).map((list) => async () => {
  const out = []
  for (const s of list) {
    if (s.mode === 'existing') {
      out.push({ sceneId: s.id, status: 'done', video: (s.files && s.files.video) || '', sheet: (s.files && s.files.sheet) || '', skeleton: (s.files && s.files.skeleton) || '', needsUser: [], notes: '沿用既有成品' })
      continue
    }
    const r = await agent(scenePrompt(s), { label: `scene:${s.id}:${stage}:${s.mode}`, phase: 'Scenes', agentType: 'blender-scenario-creator', schema: SCENE_SCHEMA })
    if (!r) { log(`第 ${s.id} 幕沒有回傳，網頁上標「未完成」`); out.push({ sceneId: s.id, status: 'blocked', video: '', needsUser: ['子代理中止，需要重跑'] }); continue }
    log(`第 ${s.id} 幕：${r.status}${r.knownIssues && r.knownIssues.length ? `｜待決定 ${r.knownIssues.length} 項` : ''}`)
    out.push(r)
  }
  return out
}))
const results = groupResults.filter(Boolean).flat()
const byId = Object.fromEntries(results.map((r) => [r.sceneId, r]))
const ordered = a.scenes.map((s) => ({ ...(byId[s.id] || { sceneId: s.id, status: 'blocked', video: '' }), title: s.title || s.id, mode: s.mode }))

if (a.publish === false) return { round, stage, scenes: ordered }

// ── Review page ──
phase('Review page')
const ML_ASSETS = '.claude/skills/blender-motion-library/assets'
const FEEDBACK_RULES = [
  '回饋功能（使用者規定，兩關都要有；細節 blender-motion-library 的 references/fast-iteration.md §0.5）：',
  '- 寫網頁前先載入 artifact-capabilities skill（讀 db.d.ts、assets.d.ts）。發布帶 capabilities: {db: {}, assets: {}}；更新既有網頁時同樣帶上。',
  `- 每一幕一個回覆框：打字自動存到 db 的 doc review/${stage === 'skeleton' ? 'skel' : 'prev'}-<幕>，形狀 {scene, stage: "${stage}", round: ${round}, text, images: [{id, t, kind}], updatedAt}。`,
  '- Ctrl+V 貼圖、拖曳圖片：用 assets.upload 上傳，db 只存 id；縮圖用 "/_blob/"+id 顯示，可放大、可拿掉。claude.use 回傳 null 時退回瀏覽器本機草稿並提示「在 claude.ai 開這頁才能同步」。',
  '- 頁面要寫明：「寫完就好，Claude 讀得到，不用貼回對話」。',
]
const pagePrompt = stage === 'skeleton' ? [
  `【worker 模式】你是 film-scene-review workflow 的最後一步：把各幕的骨骼動作做成一個「骨骼審看」網頁並發布成 Claude Artifact。禁止呼叫 AskUserQuestion。`,
  `樣板：${ML_ASSETS}/skeleton_review/viewer.html（3D 骨架播放器＋回覆框＋Ctrl+V 貼圖＋在畫面上圈，回饋功能已做好）。複製到你系統提示列出的 scratchpad 目錄底下的 skel-review/index.html（沒有 scratchpad 才放 ${PROD}/videos/review-skeleton/），只改 <title>、ROUND（= ${round}）、SCENES（每一幕的 id、label、ready；status 不是 done 的幕 ready=false）。`,
  '每一幕的 skeleton.json 複製到同資料夾的 s<幕>/skeleton.json，用 Artifact 的 files 一起發布（發布路徑 s<幕>/skeleton.json）。',
  a.reviewPageUrl ? `更新既有網頁（publish 帶 url）：${a.reviewPageUrl}。先用 Artifact read 讀現有版本再改；之前已發布的幕若這輪沒重做，files 不要傳 null，留著。` : '第一次發布：帶 icon（motion）、一句 description、capabilities: {db: {}, assets: {}}。',
  '發布前先用本機 http 伺服器開來看一次（播放、切幕、時間軸），確認骨架有畫出來。',
  ...FEEDBACK_RULES,
  '',
  '== 各幕回報 ==',
  JSON.stringify(ordered, null, 1),
].join('\n') : [
  `【worker 模式】你是 film-scene-review workflow 的最後一步：把各幕成果做成一個「批次審看」網頁並發布成 Claude Artifact。禁止呼叫 AskUserQuestion。`,
  '寫網頁前先載入 artifact-design skill。網頁原始檔存成 ' + `${PROD}/videos/preview-v2/review_round${round}.html；影片與圖片用 Artifact 的 files 一起發布（發布路徑就用檔名）。`,
  a.reviewPageUrl ? `更新既有網頁（publish 帶 url）：${a.reviewPageUrl}。先用 Artifact read 讀現有版本再改。` : '第一次發布：帶 icon（film）與一句 description。',
  '',
  '版面：每一幕一張卡，依幕順序：標題、模式（新做／重渲／修正／完整）、影片（controls muted loop playsinline）、時間軸表、數字檢查表、這輪改了什麼、套用後的微調、「待你決定」清單。',
  '每張卡最後放這一幕的回覆框＋貼圖區（見下面的回饋功能），讓使用者看完一次回饋；也註明可以在對話裡用「第 N 幕：…」告訴 Claude。',
  '頁首寫：第幾輪、這是快速預覽（低解析、頭髮裙擺不飄，只看動作）或完整品質、整支片哪些幕還沒有 3D。',
  'status=blocked 的幕顯示「這一幕這輪沒做出來」與原因，不要放壞掉的影片。',
  ...FEEDBACK_RULES,
  '',
  '== 各幕回報 ==',
  JSON.stringify(ordered, null, 1),
].join('\n')
const page = await agent(pagePrompt, { label: `review-page:${stage}:r${round}`, phase: 'Review page', agentType: 'general-purpose', schema: PAGE_SCHEMA })
if (page) log(`審看網頁：${page.status}｜${page.artifactUrl}`)

return {
  round,
  stage,
  scenes: ordered,
  page,
  // 主控端讀回饋：ArtifactData list（url＝page.artifactUrl、collection「review」）；圖片用 Artifact read（path＝圖片 id）存成本機檔
  feedbackDocs: ordered.map((r) => `review/${stage === 'skeleton' ? 'skel' : 'prev'}-${r.sceneId}`),
  needsUser: ordered.flatMap((r) => (r.needsUser || []).map((n) => `第 ${r.sceneId} 幕：${n}`)),
}
