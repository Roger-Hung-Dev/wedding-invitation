// V06 汽機車分流：汽車一張、機車一張，各自只亮自己的路線，另一個入口打叉提醒「不是這裡」。
import { FACTS, FONT_SANS, ICONS, G, ANCHOR, flatMap, flatMapMarkers, svgDoc, text, icon, pill, badge, MAP_W } from './lib.mjs';

export const meta = {
  id: 'v06',
  name: '汽機車分流版',
  note: '汽車一張圖、機車一張圖，各自只亮自己的路線；另一個入口打叉，提醒不要轉錯。',
};

export default function build() {
  const W = 1200;
  const C = { bg: '#F7F5F2', ink: '#1F2937', muted: '#6B7280', car: '#1D4ED8', carTint: '#EFF4FF', moto: '#EA580C', motoTint: '#FFF4EC' };
  const base = {
    land: '#EEEAE4',
    stall: '#FFFFFF',
    stallOpacity: 0.25,
    garden: '#E3E7DA',
    walkway: '#E9E1D4',
    road: '#FFFFFF',
    roadEdge: '#DAD3C8',
    roadLine: '#DAD3C8',
    ramp: '#E8E3DB',
    bldCorridor: '#DDD6CC',
    bldLobby: '#9CA3AF',
    bldElev: '#C9C1B6',
    bldPlan: '#DDD6CC',
    chapel: '#E8E1CF',
    bldText: '#6B6259',
    lobbyText: '#FFFFFF',
    gardenText: '#8A9A7A',
    roadText: '#A8A094',
    uturnRoute: '#A8A094',
    walkRoute: '#FFFFFF',
  };
  const crop = [0, 24, MAP_W, 770];
  const mapW = W - 80;
  const k = mapW / crop[2];
  const mapH = Math.round(crop[3] * k);

  /** 一張分流圖：mode = 'car' | 'moto'。 */
  const panel = (y, mode) => {
    const isCar = mode === 'car';
    const theme = isCar ? C.car : C.moto;
    const tint = isCar ? C.carTint : C.motoTint;
    const s = {
      ...base,
      lot: theme,
      apron: theme,
      motoLane: isCar ? '#DAD3C8' : '#FDBA8C',
      carRoute: C.car,
      motoRoute: C.moto,
    };
    const inv = (px) => px / k;
    let m = flatMap(s, { carOn: isCar, motoOn: !isCar, uturn: true, walk: true, gardenLabel: false, chapelLabel: false, routeW: 15, casing: '#FFFFFF', markerPrefix: mode });
    m += text(420, 175, 'P', { size: 150, fill: '#FFFFFF', weight: 800 });
    m += text(530, 150, '停車場', { size: inv(40), fill: '#FFFFFF', weight: 800, ls: 4 });
    m += text(532, 205, `${FACTS.capacity}・${FACTS.bus}`, { size: inv(19), fill: '#FFFFFF', opacity: 0.85 });
    // 自己的入口：亮色標籤；別人的入口：灰色打叉
    const [cx, cy] = ANCHOR.carGate;
    const [mx, my] = ANCHOR.motoGate;
    const cross = (x, y) => `<g><circle cx="${x}" cy="${y}" r="30" fill="#FFFFFF" stroke="#9CA3AF" stroke-width="5"/><path d="M${x - 12} ${y - 12} L${x + 12} ${y + 12} M${x + 12} ${y - 12} L${x - 12} ${y + 12}" stroke="#6B7280" stroke-width="7" stroke-linecap="round"/></g>`;
    if (isCar) {
      m += pill(236, 262, '汽車入口', { size: inv(26), bg: '#FFFFFF', fg: C.car, anchor: 'start', ic: 'ic-car', icColor: C.car });
      m += cross(mx - 20, my + 30);
      m += pill(915, 560, '這是機車入口，汽車繼續往前', { size: inv(18), bg: '#FFFFFF', fg: '#4B5563', anchor: 'end', stroke: '#D1D5DB', sw: 3 });
    } else {
      m += pill(930, 560, '機車入口', { size: inv(26), bg: C.moto, fg: '#FFFFFF', anchor: 'end', ic: 'ic-moto', icColor: '#FFFFFF' });
      m += cross(cx + 4, cy + 20);
      m += pill(236, 262, '這是汽車入口', { size: inv(18), bg: '#FFFFFF', fg: '#4B5563', anchor: 'start', stroke: '#D1D5DB', sw: 3 });
    }
    m += pill(ANCHOR.lobby[0] - 10, 472, `接待大廳 → 電梯上 ${FACTS.hall}`, { size: inv(19), bg: '#374151', fg: '#FFFFFF' });

    const hH = 150;
    const h = hH + mapH + 40;
    let p = `<rect x="24" y="${y}" width="${W - 48}" height="${h}" rx="28" fill="${tint}"/>`;
    p += `<circle cx="96" cy="${y + 76}" r="44" fill="${theme}"/>` + icon(isCar ? 'ic-car' : 'ic-moto', 64, y + 44, 64, '#FFFFFF');
    p += text(160, y + 72, isCar ? '開車的賓客' : '騎機車的賓客', { size: 42, fill: theme, weight: 800, ls: 2 });
    p += text(162, y + 116, isCar ? '高鐵路三段往北，經過機車入口後繼續往前，在靠台74 匝道那一端右轉' : '高鐵路三段往北，在靠高鐵五路那一端右轉，沿機車道進停車場', { size: 22, fill: C.ink });
    p += `<clipPath id="v06-${mode}"><rect x="40" y="${y + hH}" width="${mapW}" height="${mapH}" rx="20"/></clipPath>`;
    p += `<g clip-path="url(#v06-${mode})"><svg x="40" y="${y + hH}" width="${mapW}" height="${mapH}" viewBox="${crop.join(' ')}">${m}</svg></g>`;
    return { svg: p, h, s };
  };

  let body = '';
  body += text(48, 80, '汽車、機車，入口不一樣', { size: 44, fill: C.ink, weight: 800, ls: 2 });
  body += text(50, 120, `${FACTS.hotel}｜${FACTS.addr}`, { size: 21, fill: C.muted });
  let y = 158;
  const pc = panel(y, 'car');
  body += pc.svg;
  y += pc.h + 28;
  const pm = panel(y, 'moto');
  body += pm.svg;
  y += pm.h + 26;
  body += text(W / 2, y + 12, `南下車流請於高鐵五路口左迴轉（灰色虛線）　｜　${FACTS.source}`, { size: 18, fill: C.muted, anchor: 'middle' });
  const H = y + 44;

  return svgDoc({
    w: W,
    h: H,
    title: '臻愛花園飯店停車資訊（汽機車分流版）',
    desc: '上圖給開車賓客：高鐵路三段往北，經過機車入口後繼續往前，在靠台74 匝道一端右轉。下圖給騎機車賓客：在靠高鐵五路一端的機車入口右轉。',
    defs: ICONS + flatMapMarkers(pc.s, 'car', 3.2, '#FFFFFF') + flatMapMarkers(pm.s, 'moto', 3.2, '#FFFFFF'),
    body,
    bg: C.bg,
  });
}
