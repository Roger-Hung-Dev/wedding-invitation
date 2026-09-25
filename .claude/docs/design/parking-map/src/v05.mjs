// V05 三步驟：把「開到哪 → 從哪進 → 停好後怎麼走」拆成三格，每格只畫那一步需要的東西。手機直式閱讀。
import { FACTS, FONT_SERIF, FONT_SANS, ICONS, G, ANCHOR, flatMap, flatMapMarkers, svgDoc, text, pSign, badge, icon, pill, leader, ornament, arrowMarker, laneNorth, uturnPath, pathOf, yAt, road, laneN, MAP_W, LOT_Y } from './lib.mjs';

export const meta = {
  id: 'v05',
  name: '三步驟圖卡版',
  note: '手機直式。把「開到哪、從哪進、停好後怎麼走」拆成三格，每格只畫那一步需要的東西。',
};

export default function build() {
  const W = 1080;
  const C = { bg: '#FDF2F8', card: '#FFFFFF', wine: '#831843', pink: '#DB2777', gold: '#B7791F', goldSoft: '#E7C873', muted: '#7A5560', border: '#F0D9E2' };
  const s = {
    land: '#F6EEF1',
    lot: C.wine,
    apron: C.wine,
    stall: '#FFFFFF',
    stallOpacity: 0.16,
    garden: '#E1EAD6',
    walkway: '#F0DFCF',
    motoLane: '#EFC6D6',
    road: '#FFFFFF',
    roadEdge: '#E4BFCD',
    roadLine: '#EBCFDA',
    ramp: '#F2E3E9',
    bldCorridor: '#F8D6E3',
    bldLobby: C.pink,
    bldElev: '#E4BFCD',
    bldPlan: '#F5E3CB',
    chapel: '#F1DFA4',
    bldText: C.wine,
    lobbyText: '#FFFFFF',
    gardenText: '#6E8B5C',
    roadText: '#A77E8E',
    carRoute: C.gold,
    motoRoute: C.pink,
    uturnRoute: '#A77E8E',
    walkRoute: C.wine,
  };

  let body = '';
  // 標題
  body += text(W / 2, 92, 'PARKING IN 3 STEPS', { size: 22, fill: C.gold, anchor: 'middle', family: "'Cormorant Garamond','Georgia',serif", ls: 8 });
  body += text(W / 2, 162, '三步驟找到停車場', { size: 56, fill: C.wine, anchor: 'middle', family: FONT_SERIF, weight: 700, ls: 4 });
  body += ornament(W / 2, 196, 170, C.goldSoft);
  body += text(W / 2, 236, `${FACTS.hotel}｜${FACTS.addr}`, { size: 24, fill: C.muted, anchor: 'middle', family: FONT_SERIF });

  /** 一格步驟：標題列＋裁切後的地圖。 */
  const panel = (y, n, title, sub, crop, mapH, content) => {
    const x = 40;
    const w = W - 80;
    const capH = 128;
    const h = capH + mapH + 24;
    let p = `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="28" fill="${C.card}" stroke="${C.border}" stroke-width="2"/>`;
    p += badge(x + 62, y + 64, 34, String(n), C.wine, '#FFFFFF', { family: FONT_SERIF, size: 38 });
    p += text(x + 116, y + 60, title, { size: 38, fill: C.wine, weight: 700, family: FONT_SERIF });
    p += text(x + 118, y + 102, sub, { size: 25, fill: C.muted });
    const mx = x + 24;
    const my = y + capH;
    const mw = w - 48;
    p += `<clipPath id="v05-c${n}"><rect x="${mx}" y="${my}" width="${mw}" height="${mapH}" rx="18"/></clipPath>`;
    p += `<g clip-path="url(#v05-c${n})"><svg x="${mx}" y="${my}" width="${mw}" height="${mapH}" viewBox="${crop.join(' ')}" preserveAspectRatio="xMidYMid slice">${content}</svg></g>`;
    return { svg: p, h };
  };

  let y = 280;
  // ① 開到高鐵路三段往北
  {
    let m = flatMap(s, { routes: false, gardenLabel: false, chapelLabel: false, bldLabels: false, roadLabelX: 700 });
    const approach = laneNorth(1400, 470);
    m += `<path d="${pathOf(approach)}" fill="none" stroke="${C.gold}" stroke-width="16" stroke-linecap="round" marker-end="url(#v05-car)"/>`;
    m += `<path d="${uturnPath(1000)}" fill="none" stroke="${C.pink}" stroke-width="10" stroke-linecap="round" stroke-dasharray="18 12" marker-end="url(#v05-uturn)"/>`;
    m += pill(1150, 560, '北上：直行穿過高鐵五路', { size: 30, bg: C.gold, fg: '#FFFFFF', anchor: 'end' });
    m += pill(1150, 806, '南下：高鐵五路口左迴轉', { size: 30, bg: C.pink, fg: '#FFFFFF', anchor: 'end' });
    m += pill(640, 470, '飯店在右手邊', { size: 34, bg: C.wine, fg: '#FFFFFF' });
    const p = panel(y, 1, '開上高鐵路三段，往北走', '兩個方向來的車，最後都是「往北、飯店在右手邊」', [420, 424, 980, 412], 400, m);
    body += p.svg;
    y += p.h + 32;
  }
  // ② 依車種右轉進場
  {
    let m = flatMap(s, { uturn: false, walk: false, gardenLabel: false, chapelLabel: false, routeW: 16 });
    m += pSign(560, 150, 60, '#FFFFFF', C.wine, { rx: 18 });
    m += text(640, 172, '停車場', { size: 60, fill: '#FFFFFF', weight: 700, family: FONT_SERIF, ls: 6 });
    const [cx, cy] = ANCHOR.carGate;
    m += badge(cx + 4, cy + 20, 36, '汽', C.gold, '#FFFFFF', { stroke: '#FFFFFF', sw: 5, size: 34 });
    m += pill(250, 262, '汽車入口', { size: 32, bg: '#FFFFFF', fg: C.wine, anchor: 'start', stroke: C.gold, sw: 5 });
    const [mx, my] = ANCHOR.motoGate;
    m += badge(mx - 20, my + 30, 36, '機', C.pink, '#FFFFFF', { stroke: '#FFFFFF', sw: 5, size: 34 });
    m += pill(930, 540, '機車入口', { size: 32, bg: '#FFFFFF', fg: C.wine, anchor: 'end', stroke: C.pink, sw: 5 });
    const p = panel(y, 2, '看車種，在對的入口右轉', '往北時先經過機車入口，汽車要再往前開', [0, 20, 1400, 780], 520, m);
    body += p.svg;
    y += p.h + 32;
  }
  // ③ 停好車走到大廳
  {
    let m = flatMap(s, { routes: false, gardenLabel: false, chapelLabel: false, roadLabels: false });
    const lx = ANCHOR.lobby[0];
    const walk = [
      [372, 196],
      [500, 226],
      [lx - 10, 246],
      [lx, LOT_Y - 12],
    ];
    m += `<path d="${pathOf(walk)}" fill="none" stroke="#FFFFFF" stroke-width="12" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="2 20" marker-end="url(#v05-walk)"/>`;
    m += icon('ic-walk', 300, 150, 64, '#FFFFFF');
    m += leader(lx, G.bldY1, lx, 424, C.wine, 4);
    m += pill(lx + 40, 452, `接待大廳 → 搭電梯上 ${FACTS.hall}`, { size: 32, bg: C.wine, fg: '#FFFFFF' });
    const p = panel(y, 3, '停好車，走進接待大廳', `大廳旁有電梯，直上 ${FACTS.hall}`, [236, 130, 800, 353], 420, m);
    body += p.svg;
    y += p.h + 32;
  }
  // 頁尾
  body += `<line x1="80" y1="${y + 10}" x2="${W - 80}" y2="${y + 10}" stroke="${C.border}" stroke-width="2"/>`;
  body += text(W / 2, y + 60, `${FACTS.capacity}（${FACTS.capacityNote}）・${FACTS.bus}`, { size: 26, fill: C.wine, anchor: 'middle', weight: 700 });
  body += text(W / 2, y + 102, FACTS.leave, { size: 21, fill: C.muted, anchor: 'middle' });
  body += text(W / 2, y + 138, FACTS.source, { size: 18, fill: '#A77E8E', anchor: 'middle' });
  const H = y + 180;

  return svgDoc({
    w: W,
    h: H,
    title: '臻愛花園飯店停車資訊（三步驟圖卡版）',
    desc: '第一步：開上高鐵路三段往北，飯店在右手邊。第二步：機車在第一個入口右轉，汽車開到第二個入口右轉。第三步：停好車走進接待大廳，搭電梯上 2F 東方明珠。',
    defs: ICONS + flatMapMarkers(s) + arrowMarker('v05-car', C.gold, 3) + arrowMarker('v05-uturn', C.pink, 3.4) + arrowMarker('v05-walk', '#FFFFFF', 2.6),
    body,
    bg: C.bg,
  });
}
