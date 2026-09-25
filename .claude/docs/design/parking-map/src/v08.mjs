// V08 夜間版：晚宴 18:00 入席、12 月天黑得早，賓客抵達時是晚上。深色底配發光的入口與停車場外框。
import { FACTS, FONT_SERIF, FONT_SANS, ICONS, G, ANCHOR, flatMap, flatMapMarkers, svgDoc, text, pill, badge, icon, leader, polyOf, MAP_W, MAP_H } from './lib.mjs';

export const meta = {
  id: 'v08',
  name: '夜間版',
  note: '晚宴 18:00 入席、12 月天黑得早，賓客抵達時是晚上。深色底配發光的入口與停車場外框，跟開場畫面的夜色同調。',
};

export default function build() {
  const W = 1200;
  const H = 1060;
  const k = 1100 / MAP_W;
  const C = { ivory: '#F6EFE3', muted: '#9FB0BF', gold: '#FFD166', goldSoft: '#E7C873', pink: '#FF8FB8', sky0: '#0D141B', sky1: '#1E2A33' };
  const s = {
    land: '#17212A',
    lot: '#22303C',
    apron: '#22303C',
    stall: C.goldSoft,
    stallOpacity: 0.32,
    stallW: 2.5,
    garden: '#1B3128',
    walkway: '#2A3440',
    motoLane: '#4A2E40',
    road: '#2C3A46',
    roadEdge: '#3C4E5D',
    roadLine: '#71879A',
    ramp: '#25313C',
    bldCorridor: '#3A2C39',
    bldLobby: C.goldSoft,
    bldElev: '#4A3B57',
    bldPlan: '#35313F',
    chapel: '#3D3B2B',
    bldText: '#D9CCD6',
    lobbyText: '#1E2A33',
    gardenText: '#6E9A80',
    roadText: '#8FA3B5',
    carRoute: C.gold,
    motoRoute: C.pink,
    uturnRoute: '#8FA3B5',
    walkRoute: '#FFFFFF',
  };
  const inv = (px) => px / k;

  let m = flatMap(s, { gardenLabel: false, chapelLabel: false, routeW: 12, routeGroupAttr: 'filter="url(#v08-glow)"' });
  // 停車場發光外框與大 P
  m += `<polygon points="${polyOf(G.lot)}" fill="none" stroke="${C.goldSoft}" stroke-width="5" stroke-linejoin="round" filter="url(#v08-glow)"/>`;
  m += `<g filter="url(#v08-glow)">${text(300, 240, 'P', { size: 210, fill: C.gold, weight: 800 })}</g>`;
  m += text(460, 150, '飯店停車場', { size: inv(42), fill: C.ivory, weight: 700, family: FONT_SERIF, ls: 4 });
  m += text(462, 206, `${FACTS.capacity}・${FACTS.bus}`, { size: inv(20), fill: C.muted });
  // 入口信標
  const beacon = (x, y, color, label, ic, anchor, lx, ly) =>
    `<circle cx="${x}" cy="${y}" r="58" fill="${color}" opacity="0.12"/><circle cx="${x}" cy="${y}" r="40" fill="${color}" opacity="0.22"/><g filter="url(#v08-glow)"><circle cx="${x}" cy="${y}" r="26" fill="${color}"/></g>` +
    icon(ic, x - 18, y - 18, 36, '#1E2A33') +
    pill(lx, ly, label, { size: inv(24), bg: '#0F171E', fg: color, anchor, stroke: color, sw: 3 });
  const [cx, cy] = ANCHOR.carGate;
  const [mx, my] = ANCHOR.motoGate;
  m += beacon(cx + 4, cy + 22, C.gold, '汽車入口', 'ic-car', 'start', 236, 262);
  m += beacon(mx - 20, my + 30, C.pink, '機車入口', 'ic-moto', 'end', 925, 560);
  // 大廳
  const [lx] = ANCHOR.lobby;
  m += `<rect x="${G.bld.lobby[0]}" y="${G.bldY0}" width="${G.bld.lobby[1] - G.bld.lobby[0]}" height="${G.bldY1 - G.bldY0}" fill="${C.goldSoft}" filter="url(#v08-glow)" opacity="0.8"/>`;
  m += text(lx, 340, '接待', { size: 26, fill: '#1E2A33', anchor: 'middle', weight: 800 }) + text(lx, 372, '大廳', { size: 26, fill: '#1E2A33', anchor: 'middle', weight: 800 });
  m += leader(lx, G.bldY1 + 4, lx, 446, C.goldSoft, 3);
  m += pill(lx - 20, 472, `接待大廳 → 電梯上 ${FACTS.hall}`, { size: inv(20), bg: '#0F171E', fg: C.ivory, stroke: C.goldSoft, sw: 2 });

  // 星空與月亮
  let sky = '';
  let seed = 11;
  const rnd = () => ((seed = (seed * 9301 + 49297) % 233280) / 233280);
  for (let i = 0; i < 60; i++) {
    const x = rnd() * W;
    const y = rnd() * 180;
    const r = rnd() * 1.6 + 0.4;
    sky += `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${r.toFixed(2)}" fill="#FFFFFF" opacity="${(0.3 + rnd() * 0.6).toFixed(2)}"/>`;
  }
  sky += `<g transform="translate(1086 86)"><circle r="34" fill="#F6E7B8" filter="url(#v08-glow)"/><circle cx="14" cy="-8" r="30" fill="${C.sky0}"/></g>`;

  const mapY = 212;
  const mapH = MAP_H * k;
  let body = '';
  body += `<defs><linearGradient id="v08-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${C.sky0}"/><stop offset="1" stop-color="${C.sky1}"/></linearGradient></defs>`;
  body += `<rect width="${W}" height="${H}" fill="url(#v08-sky)"/>` + sky;
  body += text(60, 94, '夜間抵達・停車指引', { size: 46, fill: C.ivory, weight: 700, family: FONT_SERIF, ls: 4 });
  body += text(62, 140, '晚宴 18:00 入席，抵達時天色已暗——出發前先記住兩個入口的位置', { size: 22, fill: C.muted });
  body += text(62, 176, `${FACTS.hotel}｜${FACTS.addr}`, { size: 19, fill: '#7C8E9E' });
  body += `<clipPath id="v08-clip"><rect x="50" y="${mapY}" width="1100" height="${mapH}" rx="24"/></clipPath>`;
  body += `<g clip-path="url(#v08-clip)"><g transform="translate(50 ${mapY}) scale(${k})">${m}</g></g>`;
  body += `<rect x="50" y="${mapY}" width="1100" height="${mapH}" rx="24" fill="none" stroke="#2E3D4A" stroke-width="2"/>`;
  // 頁尾
  const fy = mapY + mapH + 60;
  const item = (x, color, ic, t, d) => `<circle cx="${x + 24}" cy="${fy - 8}" r="24" fill="${color}"/>` + icon(ic, x + 8, fy - 24, 32, '#1E2A33') + text(x + 62, fy - 2, t, { size: 26, fill: color, weight: 700 }) + text(x + 62, fy + 34, d, { size: 19, fill: C.muted });
  body += item(60, C.gold, 'ic-car', '汽車入口', '高鐵路三段往北，靠台74 匝道那一端');
  body += item(440, C.pink, 'ic-moto', '機車入口', '靠高鐵五路那一端，沿機車道進場');
  body += item(820, C.ivory, 'ic-walk', '停好之後', `大廳搭電梯上 ${FACTS.hall}`);
  body += text(W / 2, H - 28, `南下車流請於高鐵五路口左迴轉　｜　${FACTS.source}`, { size: 16, fill: '#6B7D8C', anchor: 'middle' });

  return svgDoc({
    w: W,
    h: H,
    title: '臻愛花園飯店停車資訊（夜間版）',
    desc: '深色夜間版停車示意圖：飯店停車場在建物後方，汽車入口靠台74 匝道一端，機車入口靠高鐵五路一端，停好車由接待大廳搭電梯上 2F 東方明珠。',
    defs:
      ICONS +
      flatMapMarkers(s) +
      `<filter id="v08-glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur in="SourceGraphic" stdDeviation="7" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>`,
    body,
  });
}
