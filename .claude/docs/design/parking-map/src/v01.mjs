// V01 喜帖雅緻：沿用喜帖網站色票（酒紅／玫瑰／燙金），停車場用最深的酒紅壓出重點。
import { FACTS, FONT_SERIF, FONT_SANS, ICONS, G, ANCHOR, flatMap, flatMapMarkers, svgDoc, text, pSign, badge, icon, pill, leader, ornament, textWidth, MAP_W, MAP_H } from './lib.mjs';

export const meta = {
  id: 'v01',
  name: '喜帖雅緻版',
  note: '沿用喜帖網站的酒紅、玫瑰粉與燙金色票，停車場用最深的酒紅標出，放進網站不會跳色。',
};

export default function build() {
  const W = 1200;
  const H = 1110;
  const k = 1100 / MAP_W;
  const C = { bg: '#FFFBF7', wine: '#831843', pink: '#DB2777', gold: '#CA8A04', goldSoft: '#E7C873', muted: '#7A5560', border: '#F0D9E2' };
  const s = {
    land: '#F7E8EE',
    lot: C.wine,
    apron: C.wine,
    stall: '#FFFFFF',
    stallOpacity: 0.16,
    garden: '#DDE7D3',
    walkway: '#F0DDCB',
    motoLane: '#E9C4D4',
    road: '#FFFFFF',
    roadEdge: '#E4BFCD',
    roadLine: '#EBCFDA',
    ramp: '#F2E1E8',
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
    font: FONT_SANS,
  };

  const inv = (px) => px / k; // 畫面像素 → 地圖座標
  let m = flatMap(s, { gardenLabel: false, chapelLabel: false, routeW: 13 });

  // 停車場主標
  // 三行都要壓在步行虛線起點（y≈228）之上，否則第三行會被虛線穿過。
  m += pSign(470, 142, 58, '#FFFFFF', C.wine, { rx: 18 });
  m += text(548, 124, '飯店停車場', { size: inv(44), fill: '#FFFFFF', weight: 700, family: FONT_SERIF, ls: 4 });
  m += text(550, 170, `${FACTS.capacity}・${FACTS.bus}`, { size: inv(22), fill: '#F9D9E6', family: FONT_SANS });
  m += pill(548, 206, FACTS.carIndoorOutdoor, { size: inv(19), bg: C.goldSoft, fg: C.wine, anchor: 'start', ic: 'ic-car', icColor: C.wine });

  // ① 汽車入口
  const [cx, cy] = ANCHOR.carGate;
  m += badge(cx + 4, cy + 20, 30, '1', C.gold, '#FFFFFF', { stroke: '#FFFFFF', sw: 5 });
  m += pill(236, 262, '汽車入口', { size: inv(24), bg: '#FFFFFF', fg: C.wine, anchor: 'start', stroke: C.gold, sw: 4, ic: 'ic-car', icColor: C.gold });

  // ② 機車入口
  const [mx, my] = ANCHOR.motoGate;
  m += badge(mx - 20, my + 30, 30, '2', C.pink, '#FFFFFF', { stroke: '#FFFFFF', sw: 5 });
  m += pill(930, 560, '機車入口', { size: inv(24), bg: '#FFFFFF', fg: C.wine, anchor: 'end', stroke: C.pink, sw: 4, ic: 'ic-moto', icColor: C.pink });

  // ③ 接待大廳 → 2F
  const [lx, ly] = ANCHOR.lobby;
  m += leader(lx, G.bldY1 + 4, lx, 446, C.wine, 3);
  const lobbyLabel = `接待大廳 → 電梯上 ${FACTS.hall}`;
  const lobbyW = textWidth(lobbyLabel, inv(21)) + inv(21) * 1.24;
  m += pill(lx - 30, 470, lobbyLabel, { size: inv(21), bg: C.wine, fg: '#FFFFFF', anchor: 'middle' });
  m += badge(lx - 30 - lobbyW / 2 - 38, 470, 30, '3', C.goldSoft, C.wine, { stroke: '#FFFFFF', sw: 5 });

  // 南下迴轉提示
  m += text(1236, 815, '南下於此左迴轉', { size: inv(19), fill: C.muted, anchor: 'end', family: FONT_SANS });

  const mapY = 222;
  const mapH = MAP_H * k;
  let body = '';
  // 外框雙線
  body += `<rect x="18" y="18" width="${W - 36}" height="${H - 36}" fill="none" stroke="${C.goldSoft}" stroke-width="2"/>`;
  body += `<rect x="26" y="26" width="${W - 52}" height="${H - 52}" fill="none" stroke="${C.goldSoft}" stroke-width="1"/>`;
  // 標題
  body += text(W / 2, 86, 'PARKING GUIDE', { size: 20, fill: C.gold, anchor: 'middle', family: "'Cormorant Garamond','Georgia',serif", ls: 8 });
  body += text(W / 2, 148, '賓客停車資訊', { size: 50, fill: C.wine, anchor: 'middle', family: FONT_SERIF, weight: 700, ls: 6 });
  body += ornament(W / 2, 176, 150, C.goldSoft);
  body += text(W / 2, 208, `${FACTS.hotel}｜${FACTS.addr}`, { size: 21, fill: C.muted, anchor: 'middle', family: FONT_SERIF });
  // 地圖
  body += `<clipPath id="v01-clip"><rect x="50" y="${mapY}" width="1100" height="${mapH}" rx="22"/></clipPath>`;
  body += `<g clip-path="url(#v01-clip)"><g transform="translate(50 ${mapY}) scale(${k})">${m}</g></g>`;
  body += `<rect x="50" y="${mapY}" width="1100" height="${mapH}" rx="22" fill="none" stroke="${C.border}" stroke-width="2"/>`;

  // 下方三欄說明
  const y0 = mapY + mapH + 34;
  const cols = [
    { n: '1', c: C.gold, fc: '#FFFFFF', t: '汽車入口', l1: '高鐵路三段往北開，', l2: '靠台74 匝道那一端右轉' },
    { n: '2', c: C.pink, fc: '#FFFFFF', t: '機車入口', l1: '靠高鐵五路那一端，', l2: '沿機車道進停車場' },
    { n: '3', c: C.goldSoft, fc: C.wine, t: '接待大廳', l1: '停好車走進大廳，', l2: `搭電梯上 ${FACTS.hall}` },
  ];
  cols.forEach((c, i) => {
    const x = 70 + i * 360;
    body += badge(x + 26, y0 + 26, 26, c.n, c.c, c.fc);
    body += text(x + 66, y0 + 37, c.t, { size: 30, fill: C.wine, weight: 700, family: FONT_SERIF });
    body += text(x + 66, y0 + 80, c.l1, { size: 22, fill: C.muted });
    body += text(x + 66, y0 + 112, c.l2, { size: 22, fill: C.muted });
  });
  body += `<line x1="70" y1="${y0 + 142}" x2="${W - 70}" y2="${y0 + 142}" stroke="${C.border}" stroke-width="1.5"/>`;
  body += text(W / 2, y0 + 176, `南下車流請於高鐵五路口左迴轉，飯店即在右手邊　｜　${FACTS.source}`, { size: 17, fill: '#A77E8E', anchor: 'middle' });

  return svgDoc({
    w: W,
    h: H,
    title: '臻愛花園飯店停車資訊（喜帖雅緻版）',
    desc: '飯店停車場位於建物後方，汽車位有室內也有室外，汽車由高鐵路三段靠台74 匝道一端進入，機車由靠高鐵五路一端進入，停好車由接待大廳搭電梯上 2F 東方明珠。',
    defs: ICONS + flatMapMarkers(s),
    body,
    bg: C.bg,
  });
}
