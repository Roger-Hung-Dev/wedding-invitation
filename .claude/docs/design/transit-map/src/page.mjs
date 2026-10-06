// 組出比稿頁（Claude Artifact 用）：五張靜態 SVG 直接內嵌（才吃得到網頁字型），V3 是可操作的元件。
// 用法：先跑 build.mjs 產生 SVG，再跑 node page.mjs，輸出 ../index.html。
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import * as v3 from './v3.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const out = join(here, '..');
const order = ['v1', 'v2', 'v3', 'v4', 'v5', 'v6'];
const metas = {};
for (const id of order) metas[id] = (await import(`./${id}.mjs`)).meta;

const WIDE = { v1: '820px', v2: '820px', v4: '820px', v5: '520px', v6: '480px' };
const TAGS = {
  v1: '1200 寬・與停車圖同版面',
  v2: '1200 寬・路線圖',
  v3: '網頁元件・可點',
  v4: '1200 寬・2×2 分格',
  v5: '1080 寬・手機長圖',
  v6: '1080×1920・LINE 轉傳',
};

const sections = order
  .map((id, i) => {
    const m = metas[id];
    const n = `V${i + 1}`;
    const art =
      id === 'v3'
        ? `<div class="live">${v3.html()}</div>`
        : `<div class="sheet" style="max-width:${WIDE[id]}">${readFileSync(join(out, `${id}.svg`), 'utf8')}</div>`;
    return `<section class="ver" id="${id}">
  <header class="ver-head"><span class="ver-no">${n}</span><div class="ver-text"><h2>${m.name}</h2><p>${m.note}</p></div><span class="ver-tag">${TAGS[id]}</span></header>
  ${art}
</section>`;
  })
  .join('\n');

const nav = order.map((id, i) => `<a href="#${id}">V${i + 1}　${metas[id].name}</a>`).join('');

const html = `<title>喜帖交通資訊比稿</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500&family=Tangerine:wght@700&family=Noto+Serif+TC:wght@400;700&family=Noto+Sans+TC:wght@400;700&display=swap">
<style>
/* 版面：單欄比稿長頁，每版一段；配色沿用喜帖網站（單一淺色世界，刻意不做深色模式，因為各版本身就是固定配色的成品圖） */
:root {
  color-scheme: light;
  --bg: #FDF2F8;
  --paper: #FFFBF7;
  --ink: #831843;
  --muted: #7A5560;
  --gold: #CA8A04;
  --line: #F0D9E2;
  --font-serif: 'Noto Serif TC', 'Songti TC', 'PMingLiU', serif;
  --font-sans: 'Noto Sans TC', 'PingFang TC', 'Microsoft JhengHei', sans-serif;
  --font-display: 'Cormorant Garamond', Georgia, serif;
}
html { scroll-behavior: smooth; }
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
body { background: var(--bg); color: var(--ink); font-family: var(--font-sans); padding-inline: 16px; padding-block: 0 64px; }
.top { max-width: 1040px; margin: 0 auto; padding-block: 40px 8px; text-align: center; }
.eyebrow { font-family: var(--font-display); letter-spacing: 8px; color: var(--gold); font-size: 15px; }
h1 { font-family: var(--font-serif); font-size: clamp(26px, 5vw, 38px); letter-spacing: 3px; margin: 8px 0 12px; text-wrap: balance; }
.lede { color: var(--muted); font-size: 15px; line-height: 1.8; max-width: 62ch; margin: 0 auto; }
.facts { max-width: 760px; margin: 24px auto 0; text-align: left; background: var(--paper); border: 1px solid var(--line); border-radius: 16px; padding: 16px 20px; font-size: 14.5px; line-height: 1.75; color: var(--muted); }
.facts b { color: var(--ink); }
.facts ul { margin: 6px 0 0; padding-left: 1.2em; }
nav { position: sticky; top: env(safe-area-inset-top, 0px); z-index: 5; display: flex; gap: 8px; overflow-x: auto; max-width: 1040px; margin: 24px auto 0; padding: 10px 2px; background: var(--bg); scrollbar-width: none; }
nav a { flex: none; text-decoration: none; color: var(--ink); background: var(--paper); border: 1px solid var(--line); border-radius: 999px; padding: 7px 14px; font-size: 14px; }
nav a:hover, nav a:focus-visible { border-color: var(--gold); outline: none; }
.ver { max-width: 1040px; margin: 40px auto 0; scroll-margin-top: 70px; }
.ver-head { display: grid; grid-template-columns: auto 1fr auto; align-items: start; gap: 14px; margin-bottom: 16px; }
.ver-no { font-family: var(--font-display); font-size: 34px; line-height: 1; color: var(--gold); }
.ver-text { min-width: 0; }
.ver-text h2 { font-family: var(--font-serif); font-size: 22px; letter-spacing: 2px; margin: 2px 0 6px; }
.ver-text p { margin: 0; color: var(--muted); font-size: 14.5px; line-height: 1.75; max-width: 64ch; }
.ver-tag { font-size: 12.5px; color: var(--muted); border: 1px solid var(--line); border-radius: 999px; padding: 4px 10px; white-space: nowrap; background: var(--paper); }
@media (max-width: 640px) { .ver-head { grid-template-columns: auto 1fr; } .ver-tag { grid-column: 2; justify-self: start; } }
.sheet { margin: 0 auto; border-radius: 6px; overflow: hidden; box-shadow: 0 8px 28px #8318431F; background: #FFFBF7; }
.sheet svg { display: block; width: 100%; height: auto; }
.live { border-radius: 28px; box-shadow: 0 8px 28px #8318431F; }
${v3.css()}
</style>

<div class="top">
  <div class="eyebrow">TRANSIT GUIDE</div>
  <h1>大眾運輸交通資訊　6 版比稿</h1>
  <p class="lede">接在現有停車圖旁邊的「搭車來怎麼走」。六版內容完全相同，差在呈現方式；配色、燙金框與標題字沿用停車圖 V01 喜帖雅緻版。V3 可以直接點分頁試試看。</p>
  <div class="facts">
    <b>所有版本共用的內容</b>（照飯店官方交通說明，地圖為示意、未依比例）
    <ul>
      <li><b>高鐵</b>：高鐵台中站出月台，下手扶梯到一樓 7 號出口（計程車排班區），沿站區二路往北直走，穿過高鐵三路、高鐵五路就到飯店停車場。步行約 7 分鐘。</li>
      <li><b>台鐵</b>：新烏日站出台鐵閘門，往高鐵 3 號出入口，下手扶梯到 7 號出口，之後同高鐵。步行約 8 分鐘。</li>
      <li><b>捷運</b>：綠線搭到終點站「高鐵臺中站」（前一站「烏日」不是轉乘站），下手扶梯到 7 號出口，之後同高鐵。步行約 10 分鐘。</li>
      <li><b>公車</b>：156 路「國際會展中心（高鐵五路）」下車，往高鐵路三段方向右轉即到。步行約 1 分鐘。</li>
      <li><b>最後一段</b>：走進接待大廳，搭電梯上 2F 東方明珠。</li>
    </ul>
  </div>
</div>
<nav aria-label="版本">${nav}</nav>
${sections}
<script>${v3.js()}</script>
`;

writeFileSync(join(out, 'index.html'), html);
console.log(`index.html  ${(html.length / 1024).toFixed(1)} KB`);
