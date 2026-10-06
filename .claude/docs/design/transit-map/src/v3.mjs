// V3 互動切換版：不是圖片，而是網站元件的樣子 —— 分頁切換高鐵／台鐵／捷運／公車，
// 地圖只畫出選中的那條路線（以描線動畫畫出來），右側列出步驟與 Google 地圖步行導航鈕。
import { C, FACTS, MODES, ICONS, EXTRA_ICONS, mapDefs, baseMap } from './tlib.mjs';

export const meta = {
  id: 'v3',
  name: '互動切換版',
  note: '直接做成網站元件：點上方分頁切換交通方式，地圖會用描線動畫畫出那一條路線，旁邊列出步驟和「Google 地圖步行導航」按鈕。放進網站就是現在交通區塊的樣子。',
};

const DEST = '臻愛花園飯店 台中市烏日區高鐵路三段168號';
const ORIGIN = { hsr: '高鐵台中站', tra: '新烏日車站', mrt: '台中捷運 高鐵臺中站', bus: '國際會展中心 公車站' };
const navUrl = (k) =>
  `https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(ORIGIN[k])}&destination=${encodeURIComponent(DEST)}&travelmode=walking`;

export function css() {
  return `
.tx { background: #FDF2F8; border-radius: 28px; padding: 40px 20px 32px; display: flex; flex-direction: column; align-items: center; color: #831843; }
.tx-eyebrow { font-family: 'Cormorant Garamond', Georgia, serif; letter-spacing: 6px; font-size: 14px; color: #CA8A04; }
.tx-title { font-family: 'Tangerine', cursive; font-weight: 700; font-size: 60px; line-height: 1; margin: 6px 0 4px; color: #831843; }
.tx-sub { font-family: 'Noto Serif TC', serif; font-size: 15px; color: #7A5560; margin: 0 0 22px; text-align: center; }
.tx-card { width: 100%; max-width: 1040px; background: #FFFFFF; border-radius: 20px; padding: 20px; box-shadow: 0 8px 28px #8318431F; display: grid; gap: 20px; }
.tx-tabs { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; background: #FDF2F8; padding: 6px; border-radius: 18px; }
.tx-tab { appearance: none; border: 0; background: transparent; border-radius: 14px; padding: 10px 2px 8px; font: inherit; cursor: pointer; color: #7A5560; display: flex; flex-direction: column; align-items: center; gap: 2px; transition: background .25s, color .25s, box-shadow .25s; }
.tx-tab b { font-family: 'Noto Serif TC', serif; font-size: 19px; letter-spacing: 2px; }
.tx-tab small { font-size: 12.5px; letter-spacing: .5px; }
.tx-tab[aria-selected="true"] { background: var(--mc); color: #FFFFFF; box-shadow: 0 4px 12px #8318432E; }
.tx-tab:focus-visible { outline: 3px solid #CA8A04; outline-offset: 2px; }
.tx-map { border-radius: 14px; overflow: hidden; background: #F7E8EE; }
.tx-map svg { display: block; width: 100%; height: auto; }
.tx-map .rt { opacity: 0; transition: opacity .35s; }
.tx-map .rt.on { opacity: 1; }
.tx-map .rt.draw .route-ink[pathLength] { stroke-dasharray: 1; stroke-dashoffset: 1; animation: tx-draw 1.4s ease-out forwards; }
@keyframes tx-draw { to { stroke-dashoffset: 0; } }
@media (prefers-reduced-motion: reduce) { .tx-map .rt.draw .route-ink[pathLength] { animation: none; stroke-dashoffset: 0; } .tx-map .rt, .tx-tab { transition: none; } }
.tx-side { display: flex; flex-direction: column; gap: 14px; min-width: 0; }
.tx-head { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; border-bottom: 1px solid #F0D9E2; padding-bottom: 10px; }
.tx-head h3 { margin: 0; font-family: 'Noto Serif TC', serif; font-size: 22px; letter-spacing: 2px; color: var(--mc); }
.tx-head span { font-size: 15px; color: #7A5560; white-space: nowrap; }
.tx-head span b { font-family: 'Noto Serif TC', serif; font-size: 30px; color: #CA8A04; margin: 0 2px; }
.tx-warn { margin: 0; padding: 10px 14px; border-radius: 12px; background: #FDF2F8; border: 1.5px solid #DB2777; color: #DB2777; font-weight: 700; font-size: 16px; }
.tx-steps { list-style: none; margin: 0; padding: 0; display: grid; gap: 12px; counter-reset: s; }
.tx-steps li { counter-increment: s; display: grid; grid-template-columns: 30px 1fr; gap: 10px; font-size: 17px; line-height: 1.6; color: #831843; }
.tx-steps li::before { content: counter(s); width: 28px; height: 28px; border-radius: 50%; background: var(--mc); color: #FFFFFF; font-weight: 700; font-size: 15px; display: grid; place-items: center; margin-top: 1px; }
.tx-steps li.final::before { content: '★'; background: #CA8A04; }
.tx-nav { margin-top: auto; height: 52px; border-radius: 26px; background: #CA8A04; color: #FFFFFF; display: flex; align-items: center; justify-content: center; gap: 8px; text-decoration: none; font-size: 15px; font-weight: 700; letter-spacing: 1px; }
.tx-nav:focus-visible { outline: 3px solid #831843; outline-offset: 3px; }
.tx-note { margin: 0; font-size: 13px; color: #7A5560; text-align: center; letter-spacing: 1px; }
@media (min-width: 860px) {
  .tx { padding: 64px 40px 48px; }
  .tx-title { font-size: 76px; }
  .tx-card { grid-template-columns: 6fr 5fr; grid-template-areas: "tabs tabs" "map side"; padding: 28px; gap: 24px 32px; }
  .tx-tabs { grid-area: tabs; }
  .tx-map { grid-area: map; border-radius: 18px; }
  .tx-side { grid-area: side; }
  .tx-tab b { font-size: 21px; }
}
`;
}

export function html() {
  const p = 'v3';
  const map = baseMap(p, { routes: ['walk', 'bus'], indoor: ['hsr', 'tra', 'mrt'], wrap: true, labelScale: 1.1 });
  const svg = `<svg viewBox="140 150 740 600" role="img" aria-label="臻愛花園飯店周邊地圖，標出選取的交通方式路線"><defs>${ICONS}${EXTRA_ICONS}${mapDefs(p, 1.2)}</defs>${map}</svg>`;
  const tabs = MODES.map(
    (m, i) =>
      `<button class="tx-tab" type="button" role="tab" id="tx-tab-${m.key}" aria-selected="${i === 0}" data-mode="${m.key}" style="--mc:${m.color}"><b>${m.name}</b><small>步行 ${m.min} 分</small></button>`,
  ).join('');
  return `<section class="tx" id="tx">
  <div class="tx-eyebrow">DIRECTIONS</div>
  <div class="tx-title">By Train &amp; Bus</div>
  <p class="tx-sub">搭高鐵、台鐵、捷運或公車來的賓客，請選您搭的交通方式</p>
  <div class="tx-card">
    <div class="tx-tabs" role="tablist" aria-label="交通方式">${tabs}</div>
    <div class="tx-map">${svg}</div>
    <div class="tx-side" role="tabpanel" aria-live="polite">
      <div class="tx-head"><h3 id="tx-name"></h3><span>步行約<b id="tx-min"></b>分鐘</span></div>
      <p class="tx-warn" id="tx-warn" hidden></p>
      <ol class="tx-steps" id="tx-steps"></ol>
      <a class="tx-nav" id="tx-nav" target="_blank" rel="noopener" href="#">開啟 Google 地圖步行導航</a>
    </div>
  </div>
  <p class="tx-note">${FACTS.source}</p>
</section>`;
}

export function js() {
  const data = Object.fromEntries(
    MODES.map((m) => [
      m.key,
      {
        name: `${m.name}｜${m.station}`,
        min: m.min,
        color: m.color,
        warn: m.warn || '',
        steps: m.steps,
        nav: navUrl(m.key),
        show: m.key === 'bus' ? ['bus'] : ['walk', `in-${m.key}`],
      },
    ]),
  );
  return `
(() => {
  const DATA = ${JSON.stringify(data)};
  const FINAL = ${JSON.stringify(FACTS.finalStep)};
  const root = document.getElementById('tx');
  if (!root) return;
  root.querySelectorAll('.route-ink:not([stroke-dasharray])').forEach((el) => el.setAttribute('pathLength', '1'));
  const $ = (id) => document.getElementById(id);
  const tabs = [...root.querySelectorAll('.tx-tab')];
  function select(key, focus) {
    const d = DATA[key];
    tabs.forEach((t) => { const on = t.dataset.mode === key; t.setAttribute('aria-selected', String(on)); t.tabIndex = on ? 0 : -1; if (on && focus) t.focus(); });
    root.querySelector('.tx-card').style.setProperty('--mc', d.color);
    $('tx-name').textContent = d.name;
    $('tx-min').textContent = d.min;
    $('tx-warn').textContent = d.warn;
    $('tx-warn').hidden = !d.warn;
    $('tx-steps').innerHTML = '';
    [...d.steps, FINAL].forEach((s, i, a) => { const li = document.createElement('li'); li.textContent = s; if (i === a.length - 1) li.className = 'final'; $('tx-steps').appendChild(li); });
    $('tx-nav').href = d.nav;
    root.querySelectorAll('.rt').forEach((g) => {
      const on = d.show.some((k) => g.classList.contains('rt-' + k));
      g.classList.toggle('on', on);
      g.classList.remove('draw');
      if (on) { void g.getBoundingClientRect(); g.classList.add('draw'); }
    });
  }
  tabs.forEach((t, i) => {
    t.addEventListener('click', () => select(t.dataset.mode));
    t.addEventListener('keydown', (e) => {
      const n = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
      if (!n) return;
      e.preventDefault();
      select(tabs[(i + n + tabs.length) % tabs.length].dataset.mode, true);
    });
  });
  select('hsr');
})();
`;
}
