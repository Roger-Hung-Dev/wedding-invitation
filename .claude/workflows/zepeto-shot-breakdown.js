export const meta = {
  name: 'zepeto-shot-breakdown',
  description: 'ZEPETO 開場片的分鏡展開：劇本定案、整支片設定選好後，每一鏡一個子代理照範本寫分鏡展開檔（鏡頭、角色與動作、互動接觸、道具與場景、字卡時間碼），不確定的用 ask-panel 問使用者 → 最後一個子代理檢查整支片銜接、彙整缺件清單',
  whenToUse: '由 /zepeto-film-director-workflow 在第 ⑤ 步呼叫（主控端先開 pick_body 問出場角色）。args 帶 film、date、cast、shots（每鏡 mode：new／revise／backfill）。只改一鏡的小地方時主控端直接改檔即可，不必走這條。',
  phases: [
    { title: 'Shots', detail: '每一鏡一個子代理寫分鏡展開檔並跑 director.py lint' },
    { title: 'Continuity', detail: '整支片銜接檢查、修小問題、彙整缺件清單' },
  ],
}

// 【args 形狀】
// {
//   film: 'opening-proposal-b',          // 片名：劇本 storyboard/<film>-script.md、分鏡展開 storyboard/<film>-breakdown/
//   date: '2026-10-12',                  // 回饋輪次標題用的日期（腳本裡不能取現在時間）
//   cast: [{ name: 'groom', zh: '新郎', body: '<body.blend 路徑或「未出廠」>' }],
//   shots: [{
//     id: 'B2',                          // 鏡號；經過段寫 'B1→B2'
//     mode: 'new' | 'revise' | 'backfill',
//        // new＝新寫；revise＝照 feedback 改（回饋段加一輪）；backfill＝動畫已定案、補寫分鏡展開（照 final.json 與確認頁寫實際值，不問使用者）
//     feedback: ['…'],                   // revise：使用者原話，逐條
//     round: 1,                          // revise：第幾輪
//     note: '…',                         // 主控端補充（選填）
//   }],
// }

const ROOT = 'D:/SideProject/wedding-invitation/.claude'
const GUIDE = `${ROOT}/skills/zepeto-film-director-workflow/references/breakdown-guide.md`
const LINT = `python ${ROOT}/skills/zepeto-film-director-workflow/scripts/director.py lint`

const SHOT_SCHEMA = {
  type: 'object',
  properties: {
    shot: { type: 'string' },
    path: { type: 'string' },
    seconds: { type: 'number' },
    lint_ok: { type: 'boolean', description: 'director.py lint --shot 最後一次是否 exit 0' },
    missing: { type: 'array', items: { type: 'string' }, description: '「缺：」的項目（道具、場景、服裝）' },
    asked: { type: 'array', items: { type: 'string' }, description: '問了使用者什麼、答案是什麼' },
    unanswered: { type: 'array', items: { type: 'string' }, description: '使用者沒回、暫用推薦的' },
    continuity: { type: 'array', items: { type: 'string' }, description: '和上一鏡／下一鏡銜接要注意或有疑慮的地方' },
    notes: { type: 'string' },
  },
  required: ['shot', 'path', 'lint_ok', 'missing', 'asked', 'unanswered', 'continuity'],
}

const FILM_SCHEMA = {
  type: 'object',
  properties: {
    lint_ok: { type: 'boolean' },
    total_s: { type: 'number' },
    fixes: { type: 'array', items: { type: 'string' }, description: '直接修掉的銜接問題（哪一份、改了什麼）' },
    issues: { type: 'array', items: { type: 'string' }, description: '要使用者或主控端決定的問題' },
    missing: {
      type: 'array',
      items: {
        type: 'object',
        properties: { kind: { type: 'string', description: '場景／道具／服裝' }, item: { type: 'string' }, shots: { type: 'array', items: { type: 'string' } }, owner: { type: 'string', description: 'zepeto-scense／zepeto-clothing-models' } },
        required: ['kind', 'item', 'shots', 'owner'],
      },
    },
    order: { type: 'array', items: { type: 'string' }, description: '照上一鏡／下一鏡排出的播放順序' },
  },
  required: ['lint_ok', 'total_s', 'fixes', 'issues', 'missing', 'order'],
}

const film = args.film
const shots = args.shots || []
const castText = (args.cast || []).map((c) => `${c.zh} ${c.name}（${c.body}）`).join('、') || '（主控端沒給，照劇本）'

function shotPrompt(s) {
  const head = [
    `你是分鏡子代理，負責片「${film}」的 ${s.id} 這一鏡。全程繁體中文。`,
    `先讀寫法指南 ${GUIDE}（照它做），再讀範本 ${ROOT}/docs/storyboard/_breakdown-template.md 與劇本 ${ROOT}/docs/storyboard/${film}-script.md。`,
    `整支片設定：${ROOT}/docs/storyboard/${film}-breakdown/film.json、edit.json。出場角色（已確認）：${castText}。`,
    `這次一起寫的鏡：${shots.map((x) => x.id).join('、')}（別的鏡由其他子代理同時寫，你只寫自己這份）。`,
  ]
  const mode = {
    new: `模式 new：新寫這一鏡的分鏡展開。`,
    revise: `模式 revise：讀現有的分鏡展開檔，照下面的回饋修改，並在「回饋」段最後加「### 第 ${s.round || 1} 輪（${args.date}）」把回饋原話逐條記下、每條後面寫怎麼改的。舊的輪次不刪。\n回饋：\n${(s.feedback || []).map((f) => '- ' + f).join('\n')}`,
    backfill: `模式 backfill：這一鏡動畫已經定案，補寫分鏡展開讓剪接用。照 ${ROOT}/docs/data/blender/zepeto/pipeline/status/anim/ 底下這一鏡的紀錄、它指向的 final.json 與確認頁寫「實際做出來的」秒數、動作、接觸與字卡進場時間。不問使用者；不知道的寫進回報 notes。`,
  }[s.mode || 'new']
  const tail = [
    s.note ? `主控端補充：${s.note}` : '',
    `寫完跑 ${LINT} ${film} --shot "${s.id}"，exit 0 才算完成（「上一鏡／下一鏡還沒有分鏡展開」的提醒可以忽略）。`,
    `最後回傳結構化結果：path 寫檔案完整路徑；missing 列「缺：」的項目；continuity 寫和前後鏡銜接要注意的地方（例：上一鏡結尾新郎站在畫面右側、面向左）。`,
  ]
  return [...head, mode, ...tail].filter(Boolean).join('\n\n')
}

phase('Shots')
log(`分鏡展開：${shots.map((s) => `${s.id}（${s.mode || 'new'}）`).join('、')}`)
const done = (await parallel(shots.map((s) => () =>
  agent(shotPrompt(s), { label: `breakdown:${s.id}`, phase: 'Shots', schema: SHOT_SCHEMA })))).filter(Boolean)
const lost = shots.filter((s) => !done.find((d) => d.shot === s.id)).map((s) => s.id)
if (lost.length) log(`沒有完成的鏡：${lost.join('、')}`)

// 銜接檢查要同時看所有鏡的檔案與各鏡回報，所以等全部寫完
phase('Continuity')
const report = done.map((d) => `- ${d.shot}：${d.path}；lint ${d.lint_ok ? 'OK' : '未過'}；銜接注意：${d.continuity.join('；') || '無'}`).join('\n')
const filmCheck = await agent([
  `你是分鏡子代理的總檢查，負責片「${film}」整支片的銜接。全程繁體中文。先讀 ${GUIDE}。`,
  `各鏡已寫好（劇本：${ROOT}/docs/storyboard/${film}-script.md）：\n${report}`,
  `1. 跑 ${LINT} ${film}，有錯就修到 exit 0（只改分鏡展開檔，不改劇本）。`,
  `2. 逐一看相鄰兩鏡：上一鏡結尾和下一鏡開頭的角色位置、面向、手上拿的東西、機位與運鏡是否接得上；劇本指定的遮擋接縫（例：柱子、門框）兩邊是否都寫到；字卡進場有沒有配合動作。`,
  `   明確的小問題（秒數錯、上下鏡寫錯、漏寫手上的道具）直接改，記進 fixes；要改劇情或需要使用者決定的，記進 issues，不要自己決定。`,
  `3. 彙整缺件清單：場景、道具交給 zepeto-scense，服裝交給 zepeto-clothing-models；同一樣東西多鏡要用就合併成一筆。`,
  `4. order 寫照上一鏡／下一鏡排出的播放順序；total_s 寫加總秒數。`,
  `不碰 3D 與動畫產線檔案，不 commit。`,
].join('\n\n'), { label: 'continuity', phase: 'Continuity', schema: FILM_SCHEMA })

return { film, shots: done, lost, film_check: filmCheck }
