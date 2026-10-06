// 大眾運輸交通圖共用層：事實文案、周邊路網幾何（北方朝上）、底圖繪製。
// 路網依 src/assets/parkinginformation/park1.jpg（飯店官方交通說明）重畫，與停車圖 V03 同方位。
// 版面語彙（燙金雙框、酒紅標題、玫瑰粉底）沿用停車圖 V01 喜帖雅緻版，SVG 小工具直接取自停車圖的 lib.mjs。
import {
  FONT_SANS,
  FONT_SERIF,
  ICONS,
  f1,
  pathOf,
  text,
  vtext,
  pill,
  badge,
  icon,
  textWidth,
  arrowMarker,
  ornament,
  pSign,
} from '../../parking-map/src/lib.mjs';

export { FONT_SANS, FONT_SERIF, ICONS, f1, pathOf, text, vtext, pill, badge, icon, textWidth, arrowMarker, ornament, pSign };

export const FONT_DISPLAY = "'Cormorant Garamond','Georgia',serif";

export const C = {
  page: '#FFFBF7',
  frame: '#E7C873',
  gold: '#CA8A04',
  wine: '#831843',
  muted: '#7A5560',
  pink: '#DB2777',
  blush: '#F7E8EE',
  border: '#E4BFCD',
  soft: '#F0D9E2',
  road: '#FFFFFF',
  roadEdge: '#E4BFCD',
  mainRoad: '#F6E7BF',
  mainRoadEdge: '#E7C873',
  viaduct: '#9B7484',
  building: '#FBDCE8',
  station: '#7A5560',
  hsr: '#CA8A04',
  tra: '#831843',
  mrt: '#4F7F5B',
  bus: '#DB2777',
};

export const FACTS = {
  hotel: '臻愛花園飯店',
  addr: '台中市烏日區高鐵路三段 168 號',
  hall: '2F 東方明珠',
  exit: '7 號出口',
  exitNote: '計程車排班區',
  finalStep: '走進接待大廳，搭電梯上 2F 東方明珠',
  source: '示意圖・未依比例｜資料來源：臻愛花園飯店交通資訊',
};

/** 四種交通方式。min＝官方資料的「所需步行時間」。 */
export const MODES = [
  {
    key: 'hsr',
    name: '高鐵',
    station: '高鐵台中站',
    min: 7,
    color: C.hsr,
    ic: 'ic-rail',
    steps: ['出月台，下手扶梯到一樓 7 號出口（計程車排班區）', '沿站區二路往北直走，穿過高鐵三路、高鐵五路', '走進飯店停車場，到接待大廳'],
  },
  {
    key: 'tra',
    name: '台鐵',
    station: '新烏日站',
    min: 8,
    color: C.tra,
    ic: 'ic-rail',
    steps: ['出台鐵閘門，往高鐵 3 號出入口', '下手扶梯到一樓 7 號出口（計程車排班區）', '之後同高鐵：沿站區二路往北直走到飯店停車場'],
  },
  {
    key: 'mrt',
    name: '捷運',
    station: '綠線 高鐵臺中站',
    min: 10,
    color: C.mrt,
    ic: 'ic-rail',
    warn: '搭到終點站，不要在前一站「烏日」下車',
    steps: ['綠線搭到終點站「高鐵臺中站」', '下手扶梯到一樓 7 號出口（計程車排班區）', '之後同高鐵：沿站區二路往北直走到飯店停車場'],
  },
  {
    key: 'bus',
    name: '公車',
    station: '156 路 國際會展中心站',
    min: 1,
    color: C.bus,
    ic: 'ic-coach',
    steps: ['156 路在「國際會展中心（高鐵五路）」下車', '往高鐵路三段方向，右轉就到飯店'],
  },
];
export const MODE = Object.fromEntries(MODES.map((m) => [m.key, m]));

/** 額外圖示（停車圖的 ICONS 之外）。 */
export const EXTRA_ICONS = `
<symbol id="ic-rail" viewBox="0 0 48 48"><rect x="10" y="5" width="28" height="30" rx="7" fill="none" stroke="currentColor" stroke-width="3.6"/><path d="M10 20h28" stroke="currentColor" stroke-width="3.2"/><circle cx="17.5" cy="28" r="2.6" fill="currentColor"/><circle cx="30.5" cy="28" r="2.6" fill="currentColor"/><path d="M16 43l4.5-8M32 43l-4.5-8" stroke="currentColor" stroke-width="3.4" stroke-linecap="round"/></symbol>
<symbol id="ic-coach" viewBox="0 0 48 48"><rect x="9" y="5" width="30" height="33" rx="6" fill="none" stroke="currentColor" stroke-width="3.6"/><path d="M9 23h30" stroke="currentColor" stroke-width="3.2"/><circle cx="16" cy="30.5" r="2.6" fill="currentColor"/><circle cx="32" cy="30.5" r="2.6" fill="currentColor"/><path d="M15 38v5M33 38v5" stroke="currentColor" stroke-width="4" stroke-linecap="round"/></symbol>
<symbol id="ic-escalator" viewBox="0 0 48 48"><path d="M6 40h9l18-24h9" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/><circle cx="20" cy="12" r="3.6" fill="currentColor"/><path d="M20 17v9" stroke="currentColor" stroke-width="4" stroke-linecap="round"/></symbol>
<symbol id="ic-door" viewBox="0 0 48 48"><rect x="10" y="5" width="28" height="38" rx="3" fill="none" stroke="currentColor" stroke-width="4"/><circle cx="31" cy="25" r="2.6" fill="currentColor"/></symbol>
`;

// ---------- 周邊路網幾何（地圖座標 1000 × 750，北方朝上） ----------

export const MAP = { w: 1000, h: 750 };

const DIAG_A = [140, 230]; // 高鐵路三段轉彎處（台74 匝道下）
const APEX = [380, 10];
const slope = (APEX[1] - DIAG_A[1]) / (APEX[0] - DIAG_A[0]); // 斜段斜率（負）
/** 停車場西北緣：與斜段平行、往內縮。 */
const lotEdgeY = (x) => DIAG_A[1] + 49 + slope * (x - DIAG_A[0]);
const lotEdgeX = (y) => DIAG_A[0] + (y - DIAG_A[1] - 49) / slope;

export const GEO = {
  r3: [[140, 780], DIAG_A, APEX], // 高鐵路二段／三段（下段直、上段斜）
  rightDiag: [APEX, [850, 300]],
  r5: [[140, 400], [1010, 400]], // 高鐵五路
  r3rd: [[140, 480], [1010, 480]], // 高鐵三路
  r2: [[140, 560], [420, 560], [420, 780]], // 高鐵二路
  zq2: [[600, 146], [600, 780]], // 站區二路
  zq1: [[730, 400], [730, 780]], // 站區一路
  east: [[850, 300], [850, 780]], // 高鐵東路
  jg: [[730, 560], [1010, 560]], // 建國北路
  zs: [[-10, 670], [1010, 670]], // 中山路三段
  lot: [
    [165, 372],
    [165, lotEdgeY(165)],
    [lotEdgeX(170), 170],
    [580, 170],
    [580, 372],
  ],
  bld: { x0: 165, x1: 250, y0: 262, y1: 372 },
  lobby: [250, 318],
  station: { x0: 616, x1: 714, y0: 494, y1: 650 },
  exit7: [616, 626],
  busStop: [330, 388],
  chipTra: [590, 718],
  chipMrt: [770, 718],
};

/** 路線（地圖座標）。 */
export const ROUTE = {
  walk: [
    [612, 626],
    [600, 626],
    [600, 318],
    [266, 318],
  ],
  bus: [
    [314, 388],
    [162, 388],
    [162, 338],
  ],
  indoor: {
    hsr: [
      [702, 548],
      [702, 626],
      [638, 626],
    ],
    tra: [
      [590, 702],
      [612, 664],
      [614, 648],
    ],
    mrt: [
      [770, 702],
      [704, 654],
      [638, 640],
    ],
  },
};

// ---------- 繪製 ----------

const roadStroke = (pts, w, color) =>
  `<path d="${pathOf(pts)}" fill="none" stroke="${color}" stroke-width="${w}" stroke-linejoin="round" stroke-linecap="butt"/>`;

/** 所有版本共用的箭頭 marker（以 prefix 隔開 id，避免同頁多張 SVG 互相干擾）。 */
export function mapDefs(p, scale = 1) {
  return (
    arrowMarker(`${p}-a-walk`, C.gold, 3.6 * scale, '#FFFFFF') +
    arrowMarker(`${p}-a-bus`, C.pink, 3.6 * scale, '#FFFFFF') +
    arrowMarker(`${p}-a-hsr`, C.hsr, 4.4 * scale) +
    arrowMarker(`${p}-a-tra`, C.tra, 4.4 * scale) +
    arrowMarker(`${p}-a-mrt`, C.mrt, 4.4 * scale)
  );
}

/** 路線線條：白色外框＋色線＋箭頭。 */
export function routeLine(pts, color, marker, o = {}) {
  const { w = 9, dash = null, casing = true, cls = '', id = '' } = o;
  const d = pathOf(pts);
  const attrs = `${cls ? ` class="${cls}"` : ''}${id ? ` id="${id}"` : ''}`;
  return `<g${attrs}>${casing ? `<path d="${d}" fill="none" stroke="#FFFFFF" stroke-width="${w + 7}" stroke-linejoin="round" stroke-linecap="round"/>` : ''}<path class="route-ink" d="${d}" fill="none" stroke="${color}" stroke-width="${w}" stroke-linejoin="round" stroke-linecap="round"${dash ? ` stroke-dasharray="${dash}"` : ''} marker-end="url(#${marker})"/></g>`;
}

/**
 * 周邊底圖。回傳地圖座標下的 SVG 片段，呼叫端以巢狀 <svg viewBox> 裁切與縮放。
 * opt.routes：要畫的戶外路線（'walk'／'bus'）；opt.indoor：要畫的站內路線（'hsr'／'tra'／'mrt'）。
 * opt.wrap：每條路線外包 class，給互動版切換用。
 */
export function baseMap(p, opt = {}) {
  const { routes = ['walk', 'bus'], indoor = [], compass = true, wrap = false, lobbyPill = true, labelScale = 1, nearLabels = false } = opt;
  const L = (n) => n * labelScale;
  let g = `<rect x="-200" y="-200" width="1400" height="1200" fill="${C.blush}"/>`;

  // 道路：先畫全部外緣，再畫全部路面，路口才會融成一片。
  const minor = [
    [GEO.rightDiag, 24],
    [GEO.east, 24],
    [GEO.jg, 24],
    [GEO.zq1, 24],
    [GEO.r2, 22],
    [GEO.r3rd, 26],
    [GEO.zq2, 24],
    [GEO.r5, 30],
    [GEO.r3, 40],
  ];
  g += minor.map(([pts, w]) => roadStroke(pts, w + 5, C.roadEdge)).join('');
  g += roadStroke(GEO.zs, 45, C.mainRoadEdge);
  g += minor.map(([pts, w]) => roadStroke(pts, w, C.road)).join('');
  g += roadStroke(GEO.zs, 40, C.mainRoad);

  // 台74 高架：貼在斜段外側（西北側）。
  const n = [-0.676, -0.737];
  const vA = [DIAG_A[0] + n[0] * 26, DIAG_A[1] + n[1] * 26 + 30];
  const vB = [APEX[0] + n[0] * 26 + 20, APEX[1] + n[1] * 26 - 18];
  g += `<path d="${pathOf([vA, vB])}" stroke="${C.viaduct}" stroke-width="20" stroke-linecap="butt"/>`;
  const mid = [(vA[0] + vB[0]) / 2, (vA[1] + vB[1]) / 2];
  g += text(mid[0] - 4, mid[1] + 5, '台74 快速道路（高架）', { size: L(13), fill: '#FFFFFF', anchor: 'middle', weight: 700, rotate: -42.5, ls: 1 });
  // 台74 盾牌
  g += `<g transform="translate(96 262)"><path d="M-17 -15h34v14c0 9-8 15-17 19-9-4-17-10-17-19z" fill="${C.wine}"/>${text(0, 4, '74', { size: 15, fill: '#FFFFFF', anchor: 'middle', weight: 800 })}</g>`;

  // 停車場與建物
  g += `<polygon points="${GEO.lot.map((q) => q.join(',')).join(' ')}" fill="${C.wine}"/>`;
  g += pSign(326, 222, 24, '#FFFFFF', C.wine, { family: FONT_SANS });
  g += text(362, 232, '飯店停車場', { size: L(26), fill: '#FFFFFF', weight: 700, family: FONT_SERIF, ls: 2 });
  g += text(363, 258, '汽機車位約 1,000 個', { size: L(14), fill: '#F6D3E1' });
  const b = GEO.bld;
  g += `<rect x="${b.x0}" y="${b.y0}" width="${b.x1 - b.x0}" height="${b.y1 - b.y0}" fill="${C.building}" stroke="${C.border}" stroke-width="2"/>`;
  g += vtext((b.x0 + b.x1) / 2, b.y0 + 22, '臻愛花園飯店', { size: L(15), fill: C.wine, weight: 700, family: FONT_SERIF, gap: 16.5 });

  // 高鐵站
  const s = GEO.station;
  g += `<rect x="${s.x0}" y="${s.y0}" width="${s.x1 - s.x0}" height="${s.y1 - s.y0}" rx="8" fill="${C.station}"/>`;
  g += vtext((s.x0 + s.x1) / 2 - 6, s.y0 + 26, '高鐵台中站', { size: L(20), fill: '#FFFFFF', weight: 700, gap: 22 });

  // 斑馬線（步行路線穿越高鐵三路、高鐵五路的地方）
  const zebra = (cy, h) => {
    let z = '';
    for (let x = 589; x <= 609; x += 6) z += `<rect x="${x}" y="${cy - h / 2}" width="3.2" height="${h}" fill="${C.border}"/>`;
    return z;
  };
  g += zebra(480, 22) + zebra(400, 26);

  // 路名
  g += vtext(140, 266, '高鐵路三段', { size: L(16), fill: C.muted, weight: 700, gap: 19 });
  g += vtext(140, 594, '高鐵路二段', { size: L(14), fill: C.muted, gap: 16 });
  g += text(815, 406, '高鐵五路', { size: L(17), fill: C.muted, weight: 700, anchor: 'middle', ls: 4 });
  g += text(460, 485.5, '高鐵三路', { size: L(15), fill: C.muted, anchor: 'middle', ls: 4 });
  g += text(300, 565, '高鐵二路', { size: L(14), fill: C.muted, anchor: 'middle', ls: 3 });
  g += vtext(600, 196, '站區二路', { size: L(15), fill: C.muted, weight: 700, gap: 17 });
  g += vtext(730, 585, '站區一路', { size: L(14), fill: C.muted, gap: 16 });
  g += vtext(850, 322, '高鐵東路', { size: L(14), fill: C.muted, gap: 16 });
  g += text(905, 565, '建國北路', { size: L(14), fill: C.muted, anchor: 'middle', ls: 3 });
  // 裁切成飯店近景時，原本的路名落在框外，這裡在飯店旁補一組。
  if (nearLabels) g += text(470, 406, '高鐵五路', { size: L(17), fill: C.muted, weight: 700, anchor: 'middle', ls: 4 });
  g += text(300, 677, '中山路三段', { size: L(19), fill: C.wine, weight: 700, anchor: 'middle', ls: 6 });

  // 台鐵／捷運車站標籤（與高鐵共構，在高鐵站南側）
  g += pill(GEO.chipTra[0], GEO.chipTra[1], '台鐵 新烏日站', { size: L(15), bg: C.tra, fg: '#FFFFFF', ic: 'ic-rail', rx: 8, h: L(30) });
  g += pill(GEO.chipMrt[0], GEO.chipMrt[1], '捷運 高鐵臺中站', { size: L(15), bg: C.mrt, fg: '#FFFFFF', ic: 'ic-rail', rx: 8, h: L(30) });

  // 指北針
  if (compass) {
    g += `<g transform="translate(944 214)"><circle r="26" fill="#FFFFFF" stroke="${C.border}" stroke-width="2"/><path d="M0 -19 L7 4 L0 0 L-7 4z" fill="${C.wine}"/><path d="M0 19 L7 -4 L0 0 L-7 -4z" fill="${C.border}"/>${text(0, -32, '北', { size: 15, fill: C.wine, anchor: 'middle', weight: 800 })}</g>`;
  }

  // 路線
  const wrapG = (key, inner) => (wrap ? `<g class="rt rt-${key}">${inner}</g>` : inner);
  for (const k of indoor) {
    g += wrapG(`in-${k}`, routeLine(ROUTE.indoor[k], MODE[k].color, `${p}-a-${k}`, { w: 5, dash: '0.1 10', casing: false }));
  }
  if (routes.includes('walk')) g += wrapG('walk', routeLine(ROUTE.walk, C.gold, `${p}-a-walk`));
  if (routes.includes('bus')) g += wrapG('bus', routeLine(ROUTE.bus, C.pink, `${p}-a-bus`));

  // 7 號出口
  const [ex, ey] = GEO.exit7;
  g += badge(ex, ey, 14, '7', C.gold, '#FFFFFF', { stroke: '#FFFFFF', sw: 3, size: 17 });
  g += text(582, 610, '7 號出口', { size: L(17), fill: C.wine, weight: 700, anchor: 'end' });
  g += text(582, 630, FACTS.exitNote, { size: L(13), fill: C.muted, anchor: 'end' });

  // 公車站
  const [bx, by] = GEO.busStop;
  g += `<circle cx="${bx}" cy="${by}" r="15" fill="${C.pink}" stroke="#FFFFFF" stroke-width="3"/>` + icon('ic-coach', bx - 9, by - 9.5, 18, '#FFFFFF');
  g += pill(bx + 6, 441, '156 國際會展中心站', { size: L(13), bg: '#FFFFFF', fg: C.pink, stroke: C.pink, sw: 2, h: L(26), rx: 6 });

  // 接待大廳
  if (lobbyPill) {
    g += pill(420, 352, '接待大廳 → 電梯上 2F', { size: L(14), bg: '#FFFFFF', fg: C.wine, ic: 'ic-elev', icColor: C.pink, h: L(28) });
  }
  return g;
}

/** 以巢狀 svg 放置一塊地圖（含圓角裁切）。 */
export function placeMap(p, x, y, w, vb, inner, rx = 22) {
  const h = (w * vb[3]) / vb[2];
  return {
    h,
    svg: `<clipPath id="${p}-clip"><rect x="${f1(x)}" y="${f1(y)}" width="${f1(w)}" height="${f1(h)}" rx="${rx}"/></clipPath><g clip-path="url(#${p}-clip)"><svg x="${f1(x)}" y="${f1(y)}" width="${f1(w)}" height="${f1(h)}" viewBox="${vb.join(' ')}" preserveAspectRatio="xMidYMid slice">${inner}</svg></g>`,
  };
}

/** 喜帖雅緻版的標題區（燙金雙框、英文 eyebrow、宋體大標、菱形飾線、地址）。 */
export function header(W, H, eyebrow, title, sub, o = {}) {
  const { top = 0, titleSize = 50, eyebrowSize = 20, subSize = 21 } = o;
  let s = `<rect x="18" y="18" width="${W - 36}" height="${H - 36}" fill="none" stroke="${C.frame}" stroke-width="2"/><rect x="26" y="26" width="${W - 52}" height="${H - 52}" fill="none" stroke="${C.frame}" stroke-width="1"/>`;
  s += text(W / 2, top + 86, eyebrow, { size: eyebrowSize, fill: C.gold, anchor: 'middle', family: FONT_DISPLAY, ls: 8 });
  s += text(W / 2, top + 86 + titleSize * 1.24, title, { size: titleSize, fill: C.wine, anchor: 'middle', family: FONT_SERIF, weight: 700, ls: 6 });
  const oy = top + 86 + titleSize * 1.24 + 28;
  s += ornament(W / 2, oy, 150, C.frame);
  s += text(W / 2, oy + 32 + (subSize - 21), sub, { size: subSize, fill: C.muted, anchor: 'middle', family: FONT_SERIF });
  return { svg: s, bottom: oy + 32 + (subSize - 21) };
}

export function svgDoc({ w, h, title, desc, defs = '', body, bg = C.page }) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" role="img" aria-label="${title}">
<title>${title}</title>
<desc>${desc}</desc>
<defs>${defs}</defs>
<rect width="${w}" height="${h}" fill="${bg}"/>
${body}
</svg>
`;
}
