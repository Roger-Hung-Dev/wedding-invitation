// V10 手機直式資訊卡：1080×1920（限時動態／LINE 圖片的比例）。上半張圖、下半五列大字重點，存成圖就能直接轉傳。
import { FACTS, FONT_SERIF, FONT_SANS, ICONS, G, ANCHOR, flatMap, flatMapMarkers, svgDoc, text, pSign, badge, icon, pill, leader, ornament, MAP_W } from './lib.mjs';

export const meta = {
  id: 'v10',
  name: '手機直式資訊卡版',
  note: '1080×1920 直式（LINE／限時動態比例）。上半張圖、下半五列大字重點，存成圖片就能直接轉傳給長輩。',
};

export default function build() {
  const W = 1080;
  const C = { bg: '#FDF2F8', wine: '#831843', pink: '#DB2777', gold: '#B7791F', goldSoft: '#E7C873', muted: '#7A5560', border: '#F0D9E2' };
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
    walkRoute: '#FFFFFF',
  };

  // 地圖卡
  const crop = [10, 30, 1290, 740];
  const cardX = 40;
  const cardY = 268;
  const mapW = W - 2 * cardX - 40;
  const k = mapW / crop[2];
  const mapH = Math.round(crop[3] * k);
  const inv = (px) => px / k;
  let m = flatMap(s, { gardenLabel: false, chapelLabel: false, bldLabels: false, routeW: 16 });
  m += pSign(430, 150, 66, '#FFFFFF', C.wine, { rx: 18 });
  m += text(520, 176, '停車場', { size: inv(58), fill: '#FFFFFF', weight: 700, family: FONT_SERIF, ls: 6 });
  const [cx, cy] = ANCHOR.carGate;
  const [mx, my] = ANCHOR.motoGate;
  const [lx, ly] = ANCHOR.lobby;
  m += badge(cx + 4, cy + 20, 40, '1', C.gold, '#FFFFFF', { stroke: '#FFFFFF', sw: 6, size: 44 });
  m += badge(mx - 20, my + 30, 40, '2', C.pink, '#FFFFFF', { stroke: '#FFFFFF', sw: 6, size: 44 });
  m += badge(lx, ly, 40, '3', C.goldSoft, C.wine, { stroke: '#FFFFFF', sw: 6, size: 44 });
  m += pill(260, 258, '汽車', { size: inv(30), bg: '#FFFFFF', fg: C.wine, anchor: 'start', stroke: C.gold, sw: 5, ic: 'ic-car', icColor: C.gold });
  m += pill(930, 556, '機車', { size: inv(30), bg: '#FFFFFF', fg: C.wine, anchor: 'end', stroke: C.pink, sw: 5, ic: 'ic-moto', icColor: C.pink });

  let body = '';
  body += text(W / 2, 96, 'PARKING', { size: 26, fill: C.gold, anchor: 'middle', family: "'Cormorant Garamond','Georgia',serif", ls: 12 });
  body += text(W / 2, 176, '賓客停車指南', { size: 72, fill: C.wine, anchor: 'middle', family: FONT_SERIF, weight: 700, ls: 6 });
  body += ornament(W / 2, 214, 190, C.goldSoft);
  body += text(W / 2, 250, `${FACTS.hotel}｜${FACTS.addr}`, { size: 26, fill: C.muted, anchor: 'middle', family: FONT_SERIF });
  const cardH = mapH + 40;
  body += `<rect x="${cardX}" y="${cardY + 12}" width="${W - 2 * cardX}" height="${cardH}" rx="32" fill="#FFFFFF" stroke="${C.border}" stroke-width="2"/>`;
  body += `<clipPath id="v10-clip"><rect x="${cardX + 20}" y="${cardY + 32}" width="${mapW}" height="${mapH}" rx="20"/></clipPath>`;
  body += `<g clip-path="url(#v10-clip)"><svg x="${cardX + 20}" y="${cardY + 32}" width="${mapW}" height="${mapH}" viewBox="${crop.join(' ')}">${m}</svg></g>`;

  // 五列重點
  let y = cardY + cardH + 44;
  const rowH = 172;
  const row = (marker, title, l1, l2) => {
    let r = `<rect x="${cardX}" y="${y}" width="${W - 2 * cardX}" height="${rowH - 20}" rx="28" fill="#FFFFFF" stroke="${C.border}" stroke-width="2"/>`;
    r += marker(cardX + 78, y + (rowH - 20) / 2);
    r += text(cardX + 150, y + 58, title, { size: 42, fill: C.wine, weight: 700, family: FONT_SERIF });
    r += text(cardX + 152, y + 104, l1, { size: 31, fill: C.muted });
    if (l2) r += text(cardX + 152, y + 140, l2, { size: 31, fill: C.muted });
    y += rowH;
    return r;
  };
  const circleIcon = (bg, ic, fg, n) => (x, cy2) =>
    `<circle cx="${x}" cy="${cy2}" r="46" fill="${bg}"/>` + (ic ? icon(ic, x - 28, cy2 - 28, 56, fg) : '') + (n ? text(x, cy2 + 16, n, { size: 46, fill: fg, weight: 800, anchor: 'middle' }) : '');
  body += row((x, cy2) => pSign(x, cy2, 46, C.wine, '#FFFFFF', { rx: 14 }), '停在哪裡', '飯店後方的停車場', `${FACTS.capacity}・${FACTS.bus}`);
  body += row(circleIcon(C.gold, 'ic-car', '#FFFFFF'), '① 汽車入口', '高鐵路三段往北開，', '靠台74 匝道那一端右轉');
  body += row(circleIcon(C.pink, 'ic-moto', '#FFFFFF'), '② 機車入口', '靠高鐵五路那一端右轉，', '沿機車道進停車場');
  body += row(circleIcon(C.goldSoft, 'ic-walk', C.wine), '③ 停好之後', '走進接待大廳，', `搭電梯上 ${FACTS.hall}`);
  body += row(circleIcon('#EADBE1', 'ic-uturn', C.wine), '南下的賓客', '在高鐵五路口左迴轉，', '飯店就在右手邊');

  y += 10;
  body += text(W / 2, y + 30, FACTS.gmap, { size: 27, fill: C.wine, anchor: 'middle', weight: 700 });
  body += text(W / 2, y + 76, FACTS.source, { size: 21, fill: '#A77E8E', anchor: 'middle' });
  const H = Math.max(1920, y + 120);

  return svgDoc({
    w: W,
    h: H,
    title: '臻愛花園飯店停車資訊（手機直式資訊卡版）',
    desc: '直式資訊卡：上半為停車示意圖，下半列出停車場位置與車位數、汽車入口、機車入口、停好後前往 2F 東方明珠的方式，以及南下車流的迴轉位置。',
    defs: ICONS + flatMapMarkers(s),
    body,
    bg: C.bg,
  });
}
