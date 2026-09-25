// V02 極簡扁平：全圖只留灰階＋兩個顏色——藍色＝汽車與停車場、橘色＝機車，一眼就知道看哪裡。
import { FACTS, FONT_SANS, ICONS, G, ANCHOR, flatMap, flatMapMarkers, svgDoc, text, icon, pill, leader, MAP_W, MAP_H } from './lib.mjs';

export const meta = {
  id: 'v02',
  name: '極簡扁平版',
  note: '全圖只有灰階加兩個顏色：藍＝汽車與停車場、橘＝機車。資訊最少、最不花俏。',
};

export default function build() {
  const W = 1200;
  const k = W / MAP_W;
  const headH = 128;
  const H = headH + Math.round(MAP_H * k);
  const C = { blue: '#2563EB', orange: '#F97316', ink: '#18181B', muted: '#71717A' };
  const s = {
    land: '#F4F4F5',
    lot: C.blue,
    apron: C.blue,
    stall: '#FFFFFF',
    stallOpacity: 0.28,
    garden: '#E4E4E7',
    walkway: '#E4E4E7',
    motoLane: '#FED7AA',
    road: '#FFFFFF',
    roadEdge: '#D4D4D8',
    roadLine: '#D4D4D8',
    ramp: '#EAEAEC',
    bldCorridor: '#D4D4D8',
    bldLobby: C.ink,
    bldElev: '#A1A1AA',
    bldPlan: '#D4D4D8',
    chapel: '#E4E4E7',
    bldText: C.muted,
    lobbyText: '#FFFFFF',
    gardenText: C.muted,
    roadText: '#A1A1AA',
    carRoute: C.blue,
    motoRoute: C.orange,
    uturnRoute: '#A1A1AA',
    walkRoute: '#FFFFFF',
  };
  const inv = (px) => px / k;
  let m = flatMap(s, { gardenLabel: false, chapelLabel: false, routeW: 14, casing: '#FFFFFF' });
  // 停車場：大 P＋兩行字
  m += text(250, 262, 'P', { size: 240, fill: '#FFFFFF', weight: 800, family: FONT_SANS });
  m += text(436, 158, '停車場', { size: inv(52), fill: '#FFFFFF', weight: 800, ls: 6 });
  m += text(440, 214, '汽機車約 1,000 位', { size: inv(24), fill: '#DBEAFE', weight: 500 });
  m += text(440, 252, FACTS.bus, { size: inv(24), fill: '#DBEAFE', weight: 500 });
  // 入口
  m += pill(236, 262, '汽車入口', { size: inv(26), bg: '#FFFFFF', fg: C.blue, anchor: 'start', ic: 'ic-car', icColor: C.blue });
  m += pill(930, 560, '機車入口', { size: inv(26), bg: C.orange, fg: '#FFFFFF', anchor: 'end', ic: 'ic-moto', icColor: '#FFFFFF' });
  // 大廳
  const [lx] = ANCHOR.lobby;
  m += leader(lx, G.bldY1 + 4, lx, 446, C.ink, 3);
  m += pill(lx - 20, 472, `大廳搭電梯上 ${FACTS.hall}`, { size: inv(21), bg: C.ink, fg: '#FFFFFF' });

  let body = '';
  body += text(48, 72, '停車場在這裡', { size: 44, fill: C.ink, weight: 800, ls: 2 });
  body += text(50, 108, `${FACTS.hotel}｜${FACTS.addr}`, { size: 20, fill: C.muted });
  // 圖例
  const lg = (x, color, label, dash) =>
    `<line x1="${x}" y1="70" x2="${x + 44}" y2="70" stroke="${color}" stroke-width="8" stroke-linecap="round"${dash ? ` stroke-dasharray="${dash}"` : ''}/>` + text(x + 56, 78, label, { size: 20, fill: C.ink });
  body += lg(740, C.blue, '汽車');
  body += lg(866, C.orange, '機車');
  body += lg(992, '#A1A1AA', '南下迴轉', '10 8');
  body += text(W - 48, 108, FACTS.source, { size: 15, fill: '#A1A1AA', anchor: 'end' });
  body += `<svg x="0" y="${headH}" width="${W}" height="${H - headH}" viewBox="0 0 ${MAP_W} ${MAP_H}">${m}</svg>`;

  return svgDoc({
    w: W,
    h: H,
    title: '臻愛花園飯店停車資訊（極簡扁平版）',
    desc: '藍色區塊是飯店停車場，汽車由左側入口進入；橘色是機車入口，靠高鐵五路一端。',
    defs: ICONS + flatMapMarkers(s, 'm', 3.2, '#FFFFFF'),
    body,
    bg: '#FFFFFF',
  });
}
