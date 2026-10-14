export const meta = {
  name: 'zepeto-character-face-generation',
  description: '真人大頭照 → ZEPETO 風 3D 大頭：zepeto-analyze-photo-3d-model（風格分析、Hyper3D 生成、存 OBJ）→ zepeto-avatar-crafter（匯入置中、網格修復、亮澤材質、燈光存 .blend、驗收圖）→ zepeto-face-rigger（AI 網格可動臉：ARKit 52 表情＋控制骨架＋長髮避開身體＋自動檢查）',
  whenToUse: '由 zepeto-character-face-generation-workflow skill（slash command）在找到照片的絕對路徑、問齊名稱之後呼叫，args 帶 { name, photo, outDir, notes, stages, overwrite, material }。生成端回 blocked（Blender 連不上、試用額度用完）時整條停下，不做後處理，回傳 needsUser 給主控端轉告。',
  phases: [
    { title: 'Generate', detail: 'zepeto-analyze-photo-3d-model：五官分析 → 文字生成（最多 3 次）→ 正面／側面／背面檢查 → 匯出 OBJ＋貼圖' },
    { title: 'Craft', detail: 'zepeto-avatar-crafter：背景 Blender 後處理存 .blend（亮澤材質）→ 數值驗收＋四角度驗收圖' },
    { title: 'Rig', detail: 'zepeto-face-rigger：run_face_rig.py（AI 頭當成品、模板當籠子轉移 52 表情、切嘴縫＋口腔袋、材質眼睛、控制骨架、長髮避開身體）→ 看自動檢查報告與預覽圖' },
  ],
}

// ---------------------------------------------------------------------------
// 【args 形狀】（skill 找到照片、問完名稱後組出來）
// {
//   name: 'groom',                                  // 小寫英數與 -，成品資料夾名
//   photo: 'C:/.../images/1.png',                   // 照片的絕對路徑（Alt+V 貼上的圖由 skill 換成暫存檔路徑）
//   outDir: 'D:/SideProject/wedding-invitation/.claude/docs/data/blender/zepeto/groom',  // 絕對路徑
//   notes: '…',                                     // 選填：使用者的補充描述（原話）
//   stages: ['generate', 'craft', 'rig'],           // 選填，預設三段；只重做後處理用 ['craft']、只重做可動臉用 ['rig']
//   overwrite: false,                               // outDir 已有 OBJ 時，使用者同意覆寫才 true
//   material: { sssWeight, sssScale, sssRadius, roughness }  // 選填：使用者另外指定的材質值
// }
// 三段一定依序：後處理吃生成端的 OBJ，可動臉吃後處理的 stylized_face_zepeto.blend（成品 outDir/rig/head_rig.blend）。
// 2026-10-14 可動臉改 AI 網格路線（舊路線：模板當成品，已停用、封存在 D:/render-work/archive/zepeto-face-rig-old-route-20261014）。
// ---------------------------------------------------------------------------

const BASE = {
  status: { type: 'string', enum: ['done', 'partial', 'blocked'], description: 'done＝完成且看過圖；partial＝做出來但有沒解決的問題；blocked＝缺資訊或環境卡住而停下' },
  needsUser: { type: 'array', items: { type: 'string' }, description: '需要使用者動手或決定的事。空陣列代表沒有' },
  notes: { type: 'string', description: '補充（卡關原因、已知問題）' },
}

const GEN_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['status', 'outDir', 'objPath', 'prompt', 'features', 'attempts', 'generationsUsed', 'readbackOk', 'needsUser'],
  properties: {
    outDir: { type: 'string' },
    objPath: { type: 'string', description: 'stylized_face_generated.obj 的絕對路徑；沒產出就空字串' },
    textures: { type: 'array', items: { type: 'string' } },
    features: {
      type: 'array',
      description: '五官分析表',
      items: {
        type: 'object', additionalProperties: false, required: ['part', 'photo', 'stylized'],
        properties: { part: { type: 'string' }, photo: { type: 'string' }, stylized: { type: 'string' } },
      },
    },
    prompt: { type: 'string', description: '最後採用的那次英文描述' },
    attempts: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false, required: ['n', 'passed', 'front', 'side', 'back'],
        properties: {
          n: { type: 'number' },
          passed: { type: 'boolean' },
          front: { type: 'string', description: '正面看到什麼' },
          side: { type: 'string', description: '側面看到什麼' },
          back: { type: 'string', description: '背面看到什麼' },
          problem: { type: 'string', description: '沒過的原因與下一次怎麼改描述' },
        },
      },
    },
    generationsUsed: { type: 'number', description: '實際送出的生成次數（含失敗的）' },
    readbackOk: { type: 'boolean', description: '讀回兩層都通過：readback_ok 為 true，且讀回物件的正面截圖看得到臉' },
    readbackMaxErr: { type: 'number' },
    ...BASE,
  },
}

const CRAFT_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['status', 'blendPath', 'mesh', 'material', 'qaImages', 'visualCheck', 'needsUser'],
  properties: {
    blendPath: { type: 'string' },
    mesh: {
      type: 'object', additionalProperties: false,
      required: ['mergedVerts', 'verts', 'faces', 'islands', 'boundaryEdges', 'nonManifoldEdges'],
      properties: {
        mergedVerts: { type: 'number' }, verts: { type: 'number' }, faces: { type: 'number' },
        islands: { type: 'number' }, boundaryEdges: { type: 'number' }, nonManifoldEdges: { type: 'number' },
      },
    },
    material: {
      type: 'object', additionalProperties: false,
      required: ['sssWeight', 'sssRadius', 'sssScale', 'roughness'],
      properties: {
        sssWeight: { type: 'number' }, sssRadius: { type: 'array', items: { type: 'number' } },
        sssScale: { type: 'number' }, roughness: { type: 'number' },
      },
    },
    qaImages: { type: 'array', items: { type: 'string' }, description: 'qa/ 驗收圖的絕對路徑' },
    visualCheck: { type: 'string', description: '四張驗收圖各看到什麼' },
    knownIssues: { type: 'array', items: { type: 'string' } },
    ...BASE,
  },
}

let a = args
if (typeof a === 'string') {
  try { a = JSON.parse(a) } catch (e) { a = null }
}
if (!a || !a.name || !/^[a-z0-9][a-z0-9-]*$/.test(a.name)) {
  log('缺 name，或格式不是小寫英數與 -。請由 zepeto-character-face-generation-workflow skill 問完使用者再呼叫。')
  return { error: 'bad-name', got: a && a.name }
}
const stages = Array.isArray(a.stages) && a.stages.length ? a.stages : ['generate', 'craft', 'rig']
const outDir = a.outDir || `.claude/docs/data/blender/zepeto/${a.name}`
if (stages.includes('generate') && !a.photo) {
  log('缺 photo（照片的絕對路徑）。')
  return { error: 'no-photo' }
}

// ── Generate ──
let gen = null
if (stages.includes('generate')) {
  phase('Generate')
  const genPrompt = [
    '【worker 模式】你是被 zepeto-character-face-generation workflow 派來的 zepeto-analyze-photo-3d-model。任務已完整指定；你沒有 AskUserQuestion，缺什麼就 blocked 並寫進 needsUser。',
    `名稱：${a.name}`,
    `照片：${a.photo}`,
    `成品資料夾 OUT：${outDir}`,
    a.notes ? `使用者的補充描述（原話，優先於照片判讀）：${a.notes}` : '使用者的補充描述：（無）',
    a.overwrite ? 'OUT 已有舊的 OBJ：使用者同意覆寫。' : 'OUT 若已有 stylized_face_generated.obj：使用者沒有同意覆寫 → blocked。',
    '',
    '照你定義裡的流程做：環境 → 風格分析（寫 analysis.md）→ 文字生成（只送文字、不給 bbox_condition、最多 3 次）→ 每次都看正面／側面／背面 → export_obj.py（readback_ok 要是 true，且讀回物件的正面截圖看得到臉）→ work_scene.py cleanup。',
    'attempts 每一次都要列，含沒過的；generationsUsed 照實填（會用掉使用者的免費試用額度）。',
  ].join('\n')
  gen = await agent(genPrompt, { label: `generate:${a.name}`, phase: 'Generate', agentType: 'zepeto-analyze-photo-3d-model', schema: GEN_SCHEMA })
  if (!gen) {
    log('生成端沒有回傳（中止或錯誤），整條停止。')
    return { name: a.name, error: 'generator-died' }
  }
  log(`生成：${gen.status}｜用了 ${gen.generationsUsed} 次｜讀回 ${gen.readbackOk ? '通過' : '沒過'}`)
  if (gen.status === 'blocked' || !gen.objPath || !gen.readbackOk) {
    log('生成端沒有交出可用的 OBJ → 不做後處理。')
    return { name: a.name, outDir, stage: 'generate', generate: gen, needsUser: gen.needsUser || [] }
  }
}

// ── Craft ──
let craft = null
if (stages.includes('craft')) {
  phase('Craft')
  const m = a.material || {}
  const overrides = [
    m.sssWeight != null ? `--sss-weight ${m.sssWeight}` : '',
    m.sssScale != null ? `--sss-scale ${m.sssScale}` : '',
    m.sssRadius ? `--sss-radius ${[].concat(m.sssRadius).join(',')}` : '',
    m.roughness != null ? `--roughness ${m.roughness}` : '',
  ].filter(Boolean).join(' ')
  const craftPrompt = [
    '【worker 模式】你是被 zepeto-character-face-generation workflow 派來的 zepeto-avatar-crafter。任務已完整指定；你沒有 AskUserQuestion，缺什麼就 blocked 並寫進 needsUser。',
    `名稱：${a.name}`,
    `資料夾 OUT：${outDir}`,
    gen ? `生成端剛交出：${gen.objPath}（${gen.generationsUsed} 次生成、讀回比對通過）` : '這次只重做後處理：OUT 裡的 OBJ 是之前生成的。',
    overrides ? `材質改用使用者指定的值（postprocess.py 參數）：${overrides}` : '材質用預設值（亮澤：權重 0.15、半徑 1,0.2,0.1、縮放 0.05、粗糙度 0.5）。',
    '',
    '照你定義裡的流程做：postprocess.py → verify.py → 讀數值 → 四張驗收圖每張都用 Read 看。',
  ].join('\n')
  craft = await agent(craftPrompt, { label: `craft:${a.name}`, phase: 'Craft', agentType: 'zepeto-avatar-crafter', schema: CRAFT_SCHEMA })
  if (!craft) {
    log('後處理端沒有回傳（中止或錯誤）。')
    return { name: a.name, outDir, generate: gen, error: 'crafter-died' }
  }
  log(`後處理：${craft.status}｜合併 ${craft.mesh.mergedVerts} 個頂點｜破洞邊 ${craft.mesh.boundaryEdges}｜${craft.blendPath}`)
  if (craft.status === 'blocked') {
    log('後處理端沒有交出 .blend → 不做可動臉。')
    return { name: a.name, outDir, generate: gen, craft, needsUser: craft.needsUser || [] }
  }
}

// ── Rig ──
const RIG_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['status', 'blendPath', 'checks', 'faceJsonChanges', 'likeness', 'previews', 'needsUser'],
  properties: {
    blendPath: { type: 'string', description: 'head_rig.blend 的絕對路徑' },
    checks: {
      type: 'object', additionalProperties: false, required: ['totalIssues', 'restNonzero', 'rigOk', 'ringOk', 'hairInside', 'eyesSource'],
      properties: {
        totalIssues: { type: 'number', description: 'check/summary.json 的 total_issues（應為 0）' },
        restNonzero: { type: 'number', description: '打開檔案時非 0 的形態鍵（應為 0）' },
        rigOk: { type: 'boolean', description: '控制骨頭拉到底全部通過' },
        ringOk: { type: 'boolean', description: '脖子接口環做好了：summary.json 的 neck_ring.ring_closed 是 true、ring_marked 是 48（身體端照它接，不是的話接不上）' },
        hairInside: { type: 'number', description: '長髮避開身體後還插進身體的點數（應為 0）；沒跑（body: none）填 -1' },
        eyesSource: { type: 'string', description: 'auto（自動偵測）或 manual（face.json 手動填）' },
      },
    },
    faceJsonChanges: { type: 'string', description: '改了 face.json 的哪些值、為什麼；沒改寫「沒改」' },
    likeness: { type: 'string', description: '成品和 AI 原頭比（mat_*_ai 對 mat_*_new）：哪裡一樣、哪裡不一樣' },
    previews: { type: 'array', items: { type: 'string' }, description: '看過的圖絕對路徑＋各看到什麼' },
    knownIssues: { type: 'array', items: { type: 'string' } },
    ...BASE,
  },
}
let rig = null
if (stages.includes('rig')) {
  phase('Rig')
  const rigPrompt = [
    '【worker 模式】你是被 zepeto-character-face-generation workflow 派來的 zepeto-face-rigger。任務已完整指定；你沒有 AskUserQuestion，缺什麼就 blocked 並寫進 needsUser。',
    `名稱：${a.name}`,
    `資料夾 OUT：${outDir}（輸入 OUT/stylized_face_zepeto.blend，成品 OUT/rig/head_rig.blend）`,
    craft ? `後處理端剛交出：${craft.blendPath}` : '這次只重做可動臉：OUT 裡的 stylized_face_zepeto.blend 是之前做好的。',
    '',
    '照你定義裡的流程做：先讀 OUT/analysis.md（髮色、眼睛顏色）→ run_face_rig.py --work OUT/rig（約 5 分鐘，用 run_in_background）→ 讀 check/summary.json → 報告與預覽圖每張都用 Read 看（含耳朵 check/ear.png、後頸 check/nape.png） → 自動偵測不準就改 face.json 重跑（最多 2 輪）。',
    '不要改產線程式，程式問題寫進 knownIssues；不要寫狀態紀錄（主控端在使用者看過後寫）。',
  ].join('\n')
  rig = await agent(rigPrompt, { label: `rig:${a.name}`, phase: 'Rig', agentType: 'zepeto-face-rigger', schema: RIG_SCHEMA })
  if (!rig) {
    log('可動臉端沒有回傳（中止或錯誤）。')
    return { name: a.name, outDir, generate: gen, craft, error: 'rigger-died' }
  }
  log(`可動臉：${rig.status}｜問題 ${rig.checks.totalIssues}｜骨架 ${rig.checks.rigOk ? '通過' : '有問題'}｜接口環 ${rig.checks.ringOk ? '通過' : '有問題'}｜長髮插進身體 ${rig.checks.hairInside}｜${rig.blendPath}`)
}

return {
  name: a.name,
  outDir,
  generate: gen,
  craft,
  rig,
  needsUser: [...((gen && gen.needsUser) || []), ...((craft && craft.needsUser) || []), ...((rig && rig.needsUser) || [])],
}
