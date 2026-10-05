export const meta = {
  name: 'blender-character-studio',
  description: '3D 角色工作室：blender-creator 建角色（01 身體／02 動作測試／03 照片款服裝）→ blender-scenario-creator 逐一做情境 → 產生成果網頁並發布成 Claude Artifact',
  whenToUse: '由 blender-studio skill 在問完使用者（聯集參數）之後呼叫，args 帶整份參數。blender-creator 回 blocked（例：還沒匯出 VRM、Blender 沒開）時整條停下，不做情境也不發布，回傳 needsUser 給主控端轉問。只想改服裝、只加動作，不要走這條，直接呼叫對應子代理。',
  phases: [
    { title: 'Build', detail: 'blender-creator：建專案、01 身體完成度、02 動作測試、03 服裝' },
    { title: 'Scenarios', detail: 'blender-scenario-creator：每段情境一次，依序執行（共用同一個專案檔）' },
    { title: 'Report', detail: '轉檔、產生五章網頁、發布或更新 Claude Artifact' },
  ],
}

// ---------------------------------------------------------------------------
// 【args 形狀】（blender-studio skill 問完使用者後組出來的聯集參數）
// {
//   project: 'bride',                         // 專案名稱（小寫英數與 -），blender-creator 建的資料夾名，情境直接沿用
//   vroid: 'D:/.../bride.vroid',              // 臉部模型，只收 .vroid（resume 時可省略）
//   vrm: 'D:/.../bride.vrm',                  // 選填：使用者已用 VRoid Studio F8 匯出的 VRM
//   facePhoto, frontPhoto, backPhoto,         // 真人大頭照、全身正面、全身背面（路徑）
//   description: '…',                         // 角色與服裝描述（原話）
//   costumeNotes: '…',                        // 選填：服裝的額外要求
//   bust: 'yes' | 'no',                       // 選填
//   stages: ['01','02','03'],                 // 選填，預設全部
//   resume: false,                            // true＝專案已存在，從沒完成的階段接著做
//   scenarios: [{ id, title, description, output: 'video'|'picture'|'both', outfit: 'costume'|'base', seconds }],
//   publish: true,                            // 最後發布 Artifact（預設 true）
//   artifactUrl: 'https://claude.ai/artifact/…' // 選填：更新既有網頁
// }
//
// 【為什麼情境是一段一段依序跑】情境共用同一個專案檔與 project.json（每段完成會登記 scenes），
// 並行會互相覆寫登記表；渲染也吃同一張顯示卡，並行不會比較快。
// ---------------------------------------------------------------------------

const BASE = {
  status: { type: 'string', enum: ['done', 'partial', 'blocked'], description: 'done＝完成且看過圖；partial＝部分完成；blocked＝缺資訊或環境卡住而停下' },
  needsUser: { type: 'array', items: { type: 'string' }, description: '需要使用者動手或決定的事（例：請在 VRoid Studio 按 F8 匯出 VRM 存到 X）。空陣列代表沒有' },
  notes: { type: 'string', description: '補充（卡關原因、已知問題）' },
}

const CREATOR_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['status', 'project', 'projectPath', 'who', 'stages', 'actions', 'outputs', 'needsUser'],
  properties: {
    project: { type: 'string' },
    projectPath: { type: 'string', description: 'PROJ 的絕對路徑' },
    who: { type: 'string', description: '物件名稱前綴' },
    stages: {
      type: 'object', additionalProperties: false, required: ['s01', 's02', 's03'],
      properties: {
        s01: { type: 'string', description: 'done / partial / skip / blocked' },
        s02: { type: 'string' },
        s03: { type: 'string' },
      },
    },
    actions: {
      type: 'object', additionalProperties: false, required: ['passed', 'total', 'failed'],
      properties: {
        passed: { type: 'number' }, total: { type: 'number' },
        failed: { type: 'array', items: { type: 'string' }, description: '沒通過的動作：「代號：哪一項 數字」。空陣列代表全過' },
      },
    },
    bodyFill: { type: 'string', description: '補了哪些部位、檢查圖看到什麼' },
    costume: { type: 'string', description: '服裝主要設定、和照片比對結果、做不到的' },
    outputs: { type: 'array', items: { type: 'string' }, description: 'PROJ/videos、pictures 新增的檔案（相對 PROJ）' },
    ...BASE,
  },
}

const SCENARIO_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['status', 'sceneId', 'title', 'outputs', 'checkedFrames', 'needsUser'],
  properties: {
    sceneId: { type: 'string' },
    title: { type: 'string' },
    breakdown: { type: 'string', description: '拆解表：秒數、動作、道具、鏡頭' },
    previewRounds: { type: 'number', description: 'preview 修了幾輪' },
    checkedFrames: { type: 'array', items: { type: 'string' }, description: '看過的影格與看到什麼（至少 6 格）' },
    outputs: { type: 'array', items: { type: 'string' }, description: 'PROJ/videos/scenes、pictures/scenes 的成品（相對 PROJ）' },
    knownIssues: { type: 'array', items: { type: 'string' } },
    ...BASE,
  },
}

const REPORT_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['status', 'artifactUrl', 'pagePath', 'filesPublished', 'needsUser'],
  properties: {
    artifactUrl: { type: 'string' },
    pagePath: { type: 'string' },
    filesPublished: { type: 'number' },
    actionsShownPassed: { type: 'string', description: '網頁上顯示的動作通過數（例 30/30）' },
    skippedMedia: { type: 'array', items: { type: 'string' }, description: 'export_media 跳過的（還沒渲染完）' },
    ...BASE,
  },
}

let a = args
if (typeof a === 'string') {
  try { a = JSON.parse(a) } catch (e) { a = null }
}
if (!a || !a.project) {
  log('缺 project（專案名稱）。請由 blender-studio skill 問完使用者再呼叫。')
  return { error: 'no-project' }
}
if (!a.resume && !a.vroid) {
  log('缺 vroid（臉部模型 .vroid 路徑）。新專案一定要有。')
  return { error: 'no-vroid' }
}
if (a.vroid && !/\.vroid$/i.test(a.vroid)) {
  log(`臉部模型只接受 .vroid，收到「${a.vroid}」。`)
  return { error: 'not-vroid', got: a.vroid }
}
const stages = Array.isArray(a.stages) && a.stages.length ? a.stages : ['01', '02', '03']
const scenarios = Array.isArray(a.scenarios) ? a.scenarios.filter((s) => s && s.description) : []
const ROOT = '.claude/docs/data/blender/projects'

// ── Build ──
phase('Build')
const creatorPrompt = [
  `【worker 模式】你是被 blender-character-studio workflow 派來的 blender-creator。任務已完整指定，禁止呼叫 AskUserQuestion，缺什麼就 blocked 並寫進 needsUser。`,
  `模式：${a.resume ? 'resume（專案已存在，從 project.json 的 stages 沒完成的地方接著做）' : 'build'}`,
  `專案名稱：${a.project}（資料夾 ${ROOT}/${a.project}/）`,
  a.vroid ? `臉部模型（.vroid）：${a.vroid}` : '',
  a.vrm ? `使用者已匯出的 VRM：${a.vrm}` : '',
  a.facePhoto ? `真人大頭照：${a.facePhoto}` : '真人大頭照：（未提供）',
  a.frontPhoto ? `真人全身正面照：${a.frontPhoto}` : '真人全身正面照：（未提供 → 服裝只能照描述做，report.limits 要寫明）',
  a.backPhoto ? `真人全身背面照：${a.backPhoto}` : '真人全身背面照：（未提供）',
  a.bust ? `體型：bust=${a.bust}` : '',
  `使用者描述（原話）：${a.description || '（無）'}`,
  a.costumeNotes ? `服裝額外要求（原話）：${a.costumeNotes}` : '',
  `要做的階段：${stages.join('、')}`,
  '',
  '照 blender-character-build 的 references/pipeline.md 逐步做；每一步用 Read 看檢查圖。',
  '02 的第一輪結果要另存 qa/metrics_first.json；03 完成後跑 showcase MODE=costume 與 export_media（showcase、actions、refs）。',
  'project.json 的 report.s1_text／s1_facts／s3_summary／limits 要依這個角色實際做的事寫好（網頁會直接讀）。',
  '回傳的 outputs 用相對 PROJ 的路徑；actions.failed 逐一列沒通過的動作。',
].filter(Boolean).join('\n')

const built = await agent(creatorPrompt, { label: `creator:${a.project}`, phase: 'Build', agentType: 'blender-creator', schema: CREATOR_SCHEMA })
if (!built) {
  log('blender-creator 沒有回傳（中止或錯誤），整條停止。')
  return { project: a.project, error: 'creator-died' }
}
log(`建角色：${built.status}｜01 ${built.stages.s01}｜02 動作 ${built.actions.passed}/${built.actions.total}｜03 ${built.stages.s03}`)
if (built.status === 'blocked') {
  log('blender-creator blocked → 不做情境、不發布。需要使用者處理：')
  for (const n of built.needsUser) log(`　- ${n}`)
  return { project: a.project, stage: 'build', creator: built, needsUser: built.needsUser }
}
const projectName = built.project || a.project

// ── Scenarios ──
const sceneResults = []
if (scenarios.length) {
  phase('Scenarios')
  const hasCostume = built.stages.s03 === 'done' || built.stages.s03 === 'partial'
  for (let i = 0; i < scenarios.length; i++) {
    const s = scenarios[i]
    const sid = s.id || `sc${i + 1}`
    const outfit = s.outfit || (hasCostume ? 'costume' : 'base')
    const prompt = [
      `【worker 模式】你是被 blender-character-studio workflow 派來的 blender-scenario-creator。禁止呼叫 AskUserQuestion，問題寫進 needsUser。`,
      `專案：${projectName}（${built.projectPath || `${ROOT}/${projectName}`}），角色前綴 ${built.who}。這個專案剛由 blender-creator 建好：01 ${built.stages.s01}、03 ${built.stages.s03}。`,
      `情境 id：${sid}（情境模組存成 PROJ/scripts/scene_${sid}.py）`,
      s.title ? `標題：${s.title}` : '',
      `情境描述（原話）：${s.description}`,
      `產出：${s.output || 'video'}　服裝：${outfit}　長度：${s.seconds ? `${s.seconds} 秒` : '6～8 秒'}`,
      outfit === 'costume' && !hasCostume ? '⚠️ 這個專案沒有完成服裝 → 改用便服（base），並在 notes 說明' : '',
      '',
      '照 blender-scenario 的流程：拆解 → 複製最像的範例 → preview（最多 5 輪）→ full → export_media --only scenes → 抽至少 6 格看。',
    ].filter(Boolean).join('\n')
    const r = await agent(prompt, { label: `scene:${sid}`, phase: 'Scenarios', agentType: 'blender-scenario-creator', schema: SCENARIO_SCHEMA })
    if (!r) {
      log(`情境 ${sid} 沒有回傳，跳過，繼續下一段`)
      sceneResults.push({ sceneId: sid, status: 'died' })
      continue
    }
    log(`情境 ${sid}「${r.title}」：${r.status}${r.knownIssues && r.knownIssues.length ? `（已知問題 ${r.knownIssues.length} 項）` : ''}`)
    sceneResults.push(r)
  }
}

// ── Report ──
if (a.publish === false) {
  log('publish=false → 不發布網頁')
  return { project: projectName, creator: built, scenarios: sceneResults }
}
phase('Report')
const reportPrompt = [
  `【worker 模式】你是 blender-character-studio workflow 的最後一步：把專案成果做成 Claude Artifact 網頁。禁止呼叫 AskUserQuestion。`,
  `先載入 blender-report-page skill，照它的步驟做：export_media.py → 檢查／補寫 project.json 的 report 文字 → gen_page.py → 用瀏覽器看一次 PROJ/report.html → Artifact 發布 → 網址寫回 project.json.report.artifact_url。`,
  `專案：${projectName}（${built.projectPath || `${ROOT}/${projectName}`}）`,
  a.artifactUrl ? `更新既有網頁（publish 帶 url）：${a.artifactUrl}` : '這是第一次發布：帶 icon（sparkle）與一句 description；若 project.json.report.artifact_url 已有網址就改成更新它。',
  '',
  '== blender-creator 的回報（網頁文字依據；數字以 qa/*.json 為準，不要手抄）==',
  JSON.stringify({ stages: built.stages, actions: built.actions, bodyFill: built.bodyFill, costume: built.costume, notes: built.notes }, null, 1),
  '',
  '== 情境的回報 ==',
  JSON.stringify(sceneResults.map((r) => ({ id: r.sceneId, title: r.title, status: r.status, knownIssues: r.knownIssues })), null, 1),
  '',
  'report.limits 要包含：沒通過的動作、情境的已知問題、做不到的服裝細節（有就寫，沒有不要編）。網頁有使用者的真人照片，Artifact 保持私人。',
].join('\n')
const rep = await agent(reportPrompt, { label: `report:${projectName}`, phase: 'Report', agentType: 'general-purpose', schema: REPORT_SCHEMA })
if (rep) log(`網頁：${rep.status}｜${rep.artifactUrl}｜發布 ${rep.filesPublished} 個檔`)

return {
  project: projectName,
  projectPath: built.projectPath,
  creator: built,
  scenarios: sceneResults,
  report: rep,
  needsUser: [...(built.needsUser || []), ...sceneResults.flatMap((r) => r.needsUser || []), ...((rep && rep.needsUser) || [])],
}
