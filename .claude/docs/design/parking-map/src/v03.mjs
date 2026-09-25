// V03 周邊路網：北方朝上，對照 park1.jpg 的區域圖重畫。
// 重點是「兩條來車路線最後都匯到高鐵五路口，往北進場」，再分汽車／機車兩個入口。
import { FACTS, FONT_SANS, ICONS, svgDoc, text, vtext, arrowMarker, pSign, badge, pill, icon, f1, pathOf, polyOf } from './lib.mjs';

export const meta = {
  id: 'v03',
  name: '周邊路網版（北方朝上）',
  note: '北方朝上、方位與 Google 地圖一致。畫出南下／北上兩條開車路線，以及高鐵站走過來的步行路線。',
};

export default function build() {
  const W = 1200;
  const H = 1330;
  const C = {
    bg: '#F6F2EC',
    road: '#FFFFFF',
    roadEdge: '#DDD5C8',
    viaduct: '#55595F',
    freeway: '#3E8E52',
    zhongshan: '#EFE3AE',
    hotel: '#D9467A',
    lot: '#2563EB',
    moto: '#F59E0B',
    hsr: '#3B82C4',
    ink: '#1F2937',
    muted: '#6B7280',
    south: '#2563EB',
    north: '#16A34A',
    final: '#BE185D',
    walk: '#EA580C',
  };
  const RW = 46; // 一般道路寬

  // ---- 道路中心線 ----
  const r3 = [
    [330, 1120],
    [330, 700],
    [760, 170],
  ]; // 高鐵路二段／三段（下段直、上段斜）
  const r5 = [
    [330, 862],
    [1200, 862],
  ]; // 高鐵五路
  const r3rd = [
    [330, 960],
    [860, 960],
  ]; // 高鐵三路
  const r2 = [
    [330, 1030],
    [600, 1030],
    [600, 1120],
  ]; // 高鐵二路（L 形）
  const zq2 = [
    [860, 862],
    [860, 1120],
  ]; // 站區二路
  const line = (pts, w, color, extra = '') =>
    `<path d="${pathOf(pts)}" fill="none" stroke="${color}" stroke-width="${w}" stroke-linejoin="round" stroke-linecap="butt"${extra}/>`;
  const roadPair = (pts, w = RW) => line(pts, w + 4, C.roadEdge) + line(pts, w, C.road);

  let g = '';
  // 國道一號
  g += `<rect x="40" y="200" width="58" height="960" fill="${C.freeway}"/>`;
  g += vtext(69, 470, '國道一號（中山高）', { size: 26, fill: '#FFFFFF', weight: 700, gap: 32 });
  g += `<path d="M69 214 l-18 26 h11 v22 h14 v-22 h11z" fill="#FFFFFF"/>` + text(69, 300, '台中', { size: 22, fill: '#FFFFFF', anchor: 'middle', weight: 700 });
  g += `<path d="M69 1146 l-18 -26 h11 v-22 h14 v22 h11z" fill="#FFFFFF"/>` + text(69, 1080, '彰化', { size: 22, fill: '#FFFFFF', anchor: 'middle', weight: 700 });
  // 中山路三段
  g += `<rect x="98" y="1120" width="${W - 98}" height="40" fill="${C.zhongshan}"/>`;
  g += text(760, 1149, '中山路三段', { size: 24, fill: '#6B5B2A', anchor: 'middle', weight: 700, ls: 6 });
  // 一般道路
  g += roadPair(r5) + roadPair(r3rd) + roadPair(r2) + roadPair(zq2, 40) + roadPair(r3, 58);
  // 台74 高架（疊在斜段正中央，兩側各露出一條平面道路）
  g += line(
    [
      [342, 685],
      [760, 170],
    ],
    34,
    C.viaduct,
    ' opacity="0.92"',
  );
  g += text(557, 432, '台74 快速道路（高架）', { size: 21, fill: '#FFFFFF', anchor: 'middle', weight: 700, rotate: -51 });
  g += `<g transform="translate(258 722)"><path d="M0 -24 h40 v24 l-20 20 l-20 -20z" fill="#B91C1C"/>${text(20, -4, '74', { size: 20, fill: '#FFFFFF', anchor: 'middle', weight: 800 })}</g>`;

  // 路名
  g += text(1000, 853, '高鐵五路', { size: 22, fill: C.muted, anchor: 'middle', weight: 700, ls: 4 });
  g += text(470, 951, '高鐵三路', { size: 20, fill: C.muted, anchor: 'middle', ls: 4 });
  g += text(470, 1022, '高鐵二路', { size: 20, fill: C.muted, anchor: 'middle', ls: 4 });
  g += vtext(286, 745, '高鐵路三段', { size: 22, fill: C.muted, weight: 700 });
  g += vtext(286, 1000, '高鐵路二段', { size: 20, fill: C.muted });
  g += vtext(890, 1000, '站區二路', { size: 20, fill: C.muted });

  // 高鐵站
  g += `<rect x="920" y="900" width="92" height="190" rx="10" fill="${C.hsr}"/>`;
  g += vtext(966, 942, '台中高鐵站', { size: 26, fill: '#FFFFFF', weight: 700, gap: 30 });
  g += pill(1080, 1068, '捷運高鐵台中站', { size: 18, bg: '#EA580C', fg: '#FFFFFF', rx: 6, h: 32, padX: 10 });
  g += pill(1080, 1104, '新烏日火車站', { size: 18, bg: '#312E81', fg: '#FFFFFF', rx: 6, h: 32, padX: 10 });

  // ---- 飯店基地 ----
  // 斜段東南側邊線：過 (349,715) 往東北
  // 停車場西北角延伸到斜段路邊，那一角就是汽車入口（對應 park2 左端）。
  const lot = [
    [398, 662],
    [590, 426],
    [830, 426],
    [830, 836],
    [452, 836],
    [452, 662],
  ];
  g += `<polygon points="${polyOf(lot)}" fill="${C.lot}"/>`;
  g += `<rect x="372" y="668" width="72" height="146" fill="${C.hotel}"/>`;
  g += vtext(408, 694, '臻愛花園飯店', { size: 21, fill: '#FFFFFF', weight: 700, gap: 22.5 });
  g += `<rect x="362" y="814" width="92" height="22" fill="${C.moto}"/>`;
  g += pSign(690, 532, 58, '#FFFFFF', C.lot, { rx: 16 });
  g += text(660, 690, '飯店停車場', { size: 34, fill: '#FFFFFF', anchor: 'middle', weight: 800, ls: 2 });
  g += text(660, 730, '汽機車位共約 1,000 個', { size: 20, fill: '#DBEAFE', anchor: 'middle' });
  g += text(660, 758, FACTS.bus, { size: 20, fill: '#DBEAFE', anchor: 'middle' });

  // ---- 路線 ----
  const route = (pts, color, w, id, dash = null) =>
    `<path d="${pathOf(pts)}" fill="none" stroke="${color}" stroke-width="${w}" stroke-linejoin="round" stroke-linecap="round"${dash ? ` stroke-dasharray="${dash}"` : ''} marker-end="url(#${id})"/>`;
  // 南下：沿斜段往西南下來 → 高鐵路三段往南 → 高鐵五路口左迴轉
  const southPts = [
    [705, 210],
    [318, 686],
    [318, 862],
  ];
  g += `<path d="${pathOf(southPts)} A12 12 0 0 0 342 862" fill="none" stroke="${C.south}" stroke-width="9" stroke-linejoin="round" stroke-linecap="round" marker-end="url(#v03-south)"/>`;
  // 北上：國道一號 → 中山路三段 → 高鐵二路 → 高鐵路二段往北
  const northPts = [
    [69, 1140],
    [600, 1140],
    [600, 1042],
    [342, 1042],
    [342, 880],
  ];
  g += route(northPts, C.north, 9, 'v03-north');
  // 進場：高鐵五路口往北，機車先右轉、汽車續行到斜段入口
  g += route(
    [
      [342, 850],
      [342, 824],
      [410, 824],
    ],
    C.moto,
    8,
    'v03-moto',
  );
  g += route(
    [
      [342, 850],
      [342, 716],
      [378, 664],
      [436, 650],
      [500, 646],
    ],
    C.final,
    9,
    'v03-final',
  );
  // 步行：高鐵站 → 站區二路往北 → 高鐵五路 → 停車場東南角
  g += route(
    [
      [920, 1000],
      [860, 1000],
      [860, 848],
    ],
    C.walk,
    7,
    'v03-walk',
    '2 12',
  );

  // 入口徽章
  g += badge(476, 604, 22, '汽', C.final, '#FFFFFF', { stroke: '#FFFFFF', sw: 4, size: 22 });
  g += pill(504, 604, '汽車入口', { size: 19, bg: '#FFFFFF', fg: C.final, anchor: 'start', stroke: C.final, sw: 3 });
  g += badge(470, 856 + 6, 22, '機', C.moto, '#FFFFFF', { stroke: '#FFFFFF', sw: 4, size: 22 });

  // 指北針
  g += `<g transform="translate(1120 270)"><circle r="46" fill="#FFFFFF" stroke="${C.roadEdge}" stroke-width="2"/><path d="M0 -36 L12 6 L0 0 L-12 6z" fill="${C.ink}"/><path d="M0 36 L12 -6 L0 0 L-12 -6z" fill="#CBD5E1"/>${text(0, -52, '北', { size: 22, fill: C.ink, anchor: 'middle', weight: 800 })}</g>`;

  // ---- 標題與說明 ----
  let body = '';
  body += text(48, 76, '怎麼開到停車場', { size: 44, fill: C.ink, weight: 800, ls: 2 });
  body += text(50, 114, `${FACTS.hotel}｜${FACTS.addr}｜北方朝上`, { size: 20, fill: C.muted });
  // 說明卡（右上）
  const noteX = 878;
  const note = (y, color, title, l1, l2, dash) =>
    `<line x1="${noteX}" y1="${y - 7}" x2="${noteX + 40}" y2="${y - 7}" stroke="${color}" stroke-width="8" stroke-linecap="round"${dash ? ` stroke-dasharray="${dash}"` : ''}/>` +
    text(noteX + 52, y, title, { size: 21, fill: C.ink, weight: 700 }) +
    text(noteX + 52, y + 28, l1, { size: 17, fill: C.muted }) +
    (l2 ? text(noteX + 52, y + 52, l2, { size: 17, fill: C.muted }) : '');
  body += `<rect x="${noteX - 22}" y="330" width="${W - noteX}" height="430" rx="16" fill="#FFFFFF" stroke="${C.roadEdge}" stroke-width="2"/>`;
  body += note(372, C.south, '南下（台74）', '下「高鐵台中站」交流道，', '往彰化，高鐵五路口左迴轉');
  body += note(462, C.north, '北上（國道1 王田）', '中山路三段→高鐵二路→', '高鐵路二段右轉直行');
  body += note(552, C.final, '進場（兩路線匯合後）', '穿過高鐵五路往北，', '飯店在右手邊');
  body += note(642, C.walk, '步行（高鐵 7 號出口）', '沿站區二路往北約 7 分鐘', '', '2 10');
  body += text(noteX + 52, 722, '156 公車「國際會展中心」站', { size: 17, fill: C.muted });
  body += text(noteX + 52, 744, '下車步行約 1 分鐘', { size: 17, fill: C.muted });

  // 底部：入口與離場
  const fy = 1200;
  body += `<line x1="48" y1="${fy - 22}" x2="${W - 48}" y2="${fy - 22}" stroke="${C.roadEdge}" stroke-width="2"/>`;
  body += badge(72, fy + 12, 20, '汽', C.final, '#FFFFFF', { size: 20 });
  body += text(104, fy + 20, '汽車入口：靠台74 匝道那一端（高鐵路三段轉彎處）', { size: 21, fill: C.ink });
  body += badge(72, fy + 56, 20, '機', C.moto, '#FFFFFF', { size: 20 });
  body += text(104, fy + 64, '機車入口：靠高鐵五路那一端，沿飯店南側進場', { size: 21, fill: C.ink });
  body += text(48, fy + 108, `${FACTS.leave}　｜　${FACTS.source}`, { size: 16, fill: C.muted });

  return svgDoc({
    w: W,
    h: H,
    title: '臻愛花園飯店停車資訊（周邊路網版）',
    desc: '北方朝上的周邊路網。南下與北上兩條路線都在高鐵五路口匯合往北，機車先右轉進飯店南側入口，汽車續行到台74 下方斜段的入口。',
    defs:
      ICONS +
      arrowMarker('v03-south', C.south, 3.4) +
      arrowMarker('v03-north', C.north, 3.4) +
      arrowMarker('v03-final', C.final, 3.4) +
      arrowMarker('v03-moto', C.moto, 3.6) +
      arrowMarker('v03-walk', C.walk, 3.8),
    body: body + g,
    bg: C.bg,
  });
}
