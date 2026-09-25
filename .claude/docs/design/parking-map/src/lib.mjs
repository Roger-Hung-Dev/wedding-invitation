// 停車示意圖共用層：事實文案、場地幾何、SVG 小工具、圖示。
// 幾何以 park2.jpg（飯店近景）為準，方位與原圖相同：高鐵路三段在下方、停車場在建物後方（上方）。
// 由右往左行駛＝往北，飯店在右手邊；park1.jpg 的「至高鐵五路左迴轉，目標即在您的右手邊」即此方向。

export const FONT_SANS = "'Noto Sans TC','PingFang TC','Microsoft JhengHei','Heiti TC',sans-serif";
export const FONT_SERIF = "'Noto Serif TC','Songti TC','PMingLiU',serif";
export const FONT_HAND = "'DFKai-SB','BiauKai','Kaiti TC','STKaiti',serif";

export const FACTS = {
  hotel: '臻愛花園飯店',
  branch: '台中烏日高鐵店',
  addr: '台中市烏日區高鐵路三段 168 號',
  hall: '2F 東方明珠',
  lotName: '飯店停車場',
  capacity: '汽機車位共約 1,000 個',
  capacityNote: '含詮營停車場',
  bus: '可停遊覽車',
  carIndoorOutdoor: '汽車位：室內、室外都有',
  carIn: '汽車入口',
  motoIn: '機車入口',
  lobby: '接待大廳',
  road3: '高鐵路三段',
  road5: '高鐵五路',
  ramp: '台74 匝道',
  southbound: '南下（台74 下「高鐵台中站」）：往彰化方向，到高鐵五路左迴轉',
  northbound: '北上（國道1 王田交流道）：高鐵路二段直行接三段，穿過高鐵五路',
  leave: '離場：橋下迴轉可達彰化、台74、高鐵站，不易塞車；右轉易塞車',
  gmap: 'Google Map 搜尋「臻愛花園飯店-台中烏日高鐵店」',
  source: '示意圖・未依比例｜資料來源：臻愛花園飯店交通資訊',
};

// ---------- 幾何小工具 ----------

/** Catmull-Rom 取樣，回傳密集折線點。 */
function sampleSpline(ctrl, perSeg = 40) {
  const out = [];
  for (let i = 0; i < ctrl.length - 1; i++) {
    const p0 = ctrl[i - 1] || ctrl[i];
    const p1 = ctrl[i];
    const p2 = ctrl[i + 1];
    const p3 = ctrl[i + 2] || p2;
    for (let s = 0; s < perSeg; s++) {
      const t = s / perSeg;
      const t2 = t * t;
      const t3 = t2 * t;
      const f = (k) =>
        0.5 *
        (2 * p1[k] +
          (-p0[k] + p2[k]) * t +
          (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2 +
          (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3);
      out.push([f(0), f(1)]);
    }
  }
  out.push(ctrl[ctrl.length - 1]);
  return out;
}

/** 折線平移：d 為正時往行進方向左側（畫面上方，飯店那一側）。 */
export function offsetLine(pts, d) {
  return pts.map((p, i) => {
    const a = pts[Math.max(0, i - 1)];
    const b = pts[Math.min(pts.length - 1, i + 1)];
    const dx = b[0] - a[0];
    const dy = b[1] - a[1];
    const len = Math.hypot(dx, dy);
    return [p[0] + (d * dy) / len, p[1] - (d * dx) / len];
  });
}

/** x 單調遞增的折線上，求某 x 的 y。 */
export function yAt(pts, x) {
  for (let i = 0; i < pts.length - 1; i++) {
    const [x0, y0] = pts[i];
    const [x1, y1] = pts[i + 1];
    if (x >= x0 && x <= x1) return y0 + ((y1 - y0) * (x - x0)) / (x1 - x0);
  }
  return x < pts[0][0] ? pts[0][1] : pts[pts.length - 1][1];
}

/** 折線第一次跨過某 y 的 x。 */
export function xAtY(pts, y) {
  for (let i = 0; i < pts.length - 1; i++) {
    const [x0, y0] = pts[i];
    const [x1, y1] = pts[i + 1];
    if ((y - y0) * (y - y1) <= 0 && y0 !== y1) return x0 + ((x1 - x0) * (y - y0)) / (y1 - y0);
  }
  return null;
}

/** 道路中心線在 x 處的角度（度）。 */
export function roadAngle(x) {
  const a = yAt(road, x - 10);
  const b = yAt(road, x + 10);
  return f1((Math.atan2(b - a, 20) * 180) / Math.PI);
}

export const between = (pts, x0, x1) => pts.filter((p) => p[0] >= x0 && p[0] <= x1);
export const f1 = (n) => Math.round(n * 10) / 10;
export const pathOf = (pts) => 'M' + pts.map((p) => `${f1(p[0])} ${f1(p[1])}`).join(' L');
export const polyOf = (pts) => pts.map((p) => `${f1(p[0])},${f1(p[1])}`).join(' ');
export const lerp = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];

// ---------- 場地幾何（地圖座標 1400 × 820） ----------

export const MAP_W = 1400;
export const MAP_H = 820;
export const ROAD_HALF = 60;

const ROAD_CTRL = [
  [-160, 240],
  [40, 380],
  [300, 540],
  [600, 640],
  [920, 700],
  [1220, 724],
  [1560, 734],
];

export const road = sampleSpline(ROAD_CTRL);
export const roadTop = offsetLine(road, ROAD_HALF);
export const roadBot = offsetLine(road, -ROAD_HALF);
export const laneN = offsetLine(road, ROAD_HALF / 2); // 往北車道（往左、靠飯店側）
export const laneS = offsetLine(road, -ROAD_HALF / 2); // 往南車道（往右）
const walkOuter = offsetLine(road, ROAD_HALF + 26);

export const LOT_Y = 300; // 停車場下緣＝建物上緣
export const BLD_Y1 = 392; // 建物下緣
const lotBLx = xAtY(roadTop, LOT_Y);

export const G = {};

/** 汽車入口：停車場左下角直接接到高鐵路三段。 */
G.carGateX0 = lotBLx;
G.carGateX1 = 270;
G.lot = [
  [lotBLx, LOT_Y],
  [lotBLx + 190, 36],
  [1150, 36],
  [1070, LOT_Y],
];
G.apron = [
  [lotBLx, LOT_Y],
  [G.carGateX1, LOT_Y],
  [G.carGateX1, yAt(roadTop, G.carGateX1)],
  ...between(roadTop, lotBLx, G.carGateX1).reverse(),
];

G.bld = {
  corridor: [G.carGateX1, 590],
  lobby: [590, 700],
  elev: [700, 732],
  plan: [732, 975],
};
G.bldY0 = LOT_Y;
G.bldY1 = BLD_Y1;

// 機車道：由路邊斜向右上接進停車場右下角（park2 的咖啡色斜帶）。
G.motoTop = [1002, 1068];
G.motoBot = [932, 998];
G.moto = [
  [G.motoTop[0], LOT_Y],
  [G.motoTop[1], LOT_Y],
  [G.motoBot[1], yAt(roadTop, G.motoBot[1])],
  [G.motoBot[0], yAt(roadTop, G.motoBot[0])],
];
export const motoLeftX = (y) => {
  const b = [G.motoBot[0], yAt(roadTop, G.motoBot[0])];
  const t = [G.motoTop[0], LOT_Y];
  return b[0] + ((t[0] - b[0]) * (b[1] - y)) / (b[1] - t[1]);
};

G.walkway = [
  [G.carGateX1, yAt(walkOuter, G.carGateX1)],
  ...between(walkOuter, G.carGateX1, G.motoBot[0] + 4),
  ...between(roadTop, G.carGateX1, G.motoBot[0] + 4).reverse(),
  [G.carGateX1, yAt(roadTop, G.carGateX1)],
];
G.garden = [
  [G.carGateX1, BLD_Y1],
  [motoLeftX(BLD_Y1), BLD_Y1],
  ...between(walkOuter, G.carGateX1, motoLeftX(yAt(walkOuter, G.motoBot[0]))).reverse(),
  [G.carGateX1, yAt(walkOuter, G.carGateX1)],
];
G.chapel = { cx: 880, cy: 478, r: 40 };

// 高鐵五路：由上方接到高鐵路三段的 T 字路口。
G.road5X = [1206, 1266];
G.road5 = [
  [G.road5X[0], -10],
  [G.road5X[1], -10],
  [G.road5X[1], yAt(roadTop, G.road5X[1]) + 4],
  [G.road5X[0], yAt(roadTop, G.road5X[0]) + 4],
];

// 台74 匝道：在路的另一側（畫面下方）、左段並行，於中段併入。
const rampCtrl = [
  [-160, 380],
  [60, 520],
  [300, 650],
  [520, 716],
  [760, 742],
];
export const ramp = sampleSpline(rampCtrl);
G.rampHalf = 30;

/** 道路外框多邊形（上緣正向＋下緣反向）。 */
G.roadPoly = [...roadTop, ...roadBot.slice().reverse()];
const rampTaper = (sign) =>
  ramp.map((p, i) => {
    const t = Math.min(1, (ramp.length - 1 - i) / (ramp.length * 0.35));
    return offsetLine(ramp, sign * G.rampHalf * t)[i];
  });
G.rampPoly = [...rampTaper(1), ...rampTaper(-1).reverse()];

// ---------- 路線 ----------

/** 往北車道上，由 xStart 往左開到 xEnd（回傳由右至左的點）。 */
export function laneNorth(xStart, xEnd) {
  return between(laneN, xEnd, xStart).reverse();
}

/** 汽車路線：往北車道 → 在汽車入口右轉進停車場。 */
export function carRoute(xStart = 1380) {
  const turnX = (G.carGateX0 + G.carGateX1) / 2 + 40;
  const pts = laneNorth(xStart, turnX + 40);
  pts.push([turnX, yAt(laneN, turnX) - 6]);
  pts.push([turnX - 10, LOT_Y - 40]);
  pts.push([turnX + 10, LOT_Y - 110]);
  return pts;
}

/** 機車路線：往北車道 → 在機車入口右轉，沿機車道進停車場。 */
export function motoRoute(xStart = 1380) {
  const mid0 = (G.motoBot[0] + G.motoBot[1]) / 2;
  const mid1 = (G.motoTop[0] + G.motoTop[1]) / 2;
  const pts = laneNorth(xStart, mid0 + 44);
  pts.push([mid0 + 6, yAt(laneN, mid0) - 6]);
  pts.push([mid0 + (mid1 - mid0) * 0.35, yAt(roadTop, mid0) - (yAt(roadTop, mid0) - LOT_Y) * 0.35]);
  pts.push([mid1, LOT_Y - 10]);
  pts.push([mid1 + 18, LOT_Y - 70]);
  return pts;
}

/** 南下車流：往南車道到高鐵五路口左迴轉，回到往北車道。 */
export function uturnPath(xFrom = 1040) {
  const cx = (G.road5X[0] + G.road5X[1]) / 2;
  const a = [cx, yAt(laneS, cx)];
  const b = [cx, yAt(laneN, cx)];
  const r = (a[1] - b[1]) / 2;
  const start = between(laneS, xFrom, cx - 2);
  return `${pathOf(start)} L${f1(a[0])} ${f1(a[1])} A${f1(r)} ${f1(r)} 0 0 0 ${f1(b[0])} ${f1(b[1])} L${f1(b[0] - 50)} ${f1(yAt(laneN, b[0] - 50))}`;
}

/** 停車場走到接待大廳的步行線（由停車場往下進大廳）。 */
export function walkToLobby() {
  const x = (G.bld.lobby[0] + G.bld.lobby[1]) / 2;
  return [
    [x, LOT_Y - 72],
    [x, LOT_Y - 12],
  ];
}

// ---------- SVG 小工具 ----------

export function svgDoc({ w, h, title, desc, defs = '', body, bg }) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" role="img" aria-labelledby="t d">
<title id="t">${title}</title>
<desc id="d">${desc}</desc>
<defs>${defs}</defs>
${bg ? `<rect width="${w}" height="${h}" fill="${bg}"/>` : ''}
${body}
</svg>
`;
}

export function text(x, y, s, o = {}) {
  const {
    size = 24,
    fill = '#222',
    weight = 400,
    anchor = 'start',
    family = FONT_SANS,
    ls = 0,
    rotate = 0,
    stroke = null,
    sw = 0,
    opacity = 1,
    italic = false,
    baseline = null,
  } = o;
  const tr = rotate ? ` transform="rotate(${rotate} ${f1(x)} ${f1(y)})"` : '';
  const st = stroke ? ` stroke="${stroke}" stroke-width="${sw}" paint-order="stroke" stroke-linejoin="round"` : '';
  const bl = baseline ? ` dominant-baseline="${baseline}"` : '';
  return `<text x="${f1(x)}" y="${f1(y)}" font-family="${family}" font-size="${size}" font-weight="${weight}" fill="${fill}" text-anchor="${anchor}"${ls ? ` letter-spacing="${ls}"` : ''}${italic ? ' font-style="italic"' : ''}${opacity !== 1 ? ` opacity="${opacity}"` : ''}${st}${bl}${tr}>${s}</text>`;
}

/** 直排文字（逐字往下排）。 */
export function vtext(x, y, s, o = {}) {
  const size = o.size || 24;
  const gap = o.gap ?? size * 1.08;
  return [...s].map((ch, i) => text(x, y + i * gap, ch, { ...o, anchor: 'middle' })).join('');
}

export function arrowMarker(id, color, size = 4, outline = null) {
  const st = outline ? ` stroke="${outline}" stroke-width="1.1" stroke-linejoin="round"` : '';
  return `<marker id="${id}" viewBox="-1.5 -1.5 13 13" refX="5" refY="5" markerWidth="${size * 1.3}" markerHeight="${size * 1.3}" orient="auto-start-reverse" overflow="visible"><path d="M0 0 L10 5 L0 10 L2.5 5 Z" fill="${color}"${st}/></marker>`;
}

/** 停車格線（在停車場多邊形內畫斜向格線，營造「這裡是停車場」的樣子）。 */
export function stallLines(color, opacity = 0.5, sw = 3) {
  const rows = [
    { y0: 70, y1: 130 },
    { y0: 150, y1: 210 },
  ];
  let s = '';
  for (const r of rows) {
    const xs = G.lot[1][0] + 30;
    for (let x = xs; x < 1080; x += 46) {
      s += `<line x1="${x}" y1="${r.y0}" x2="${x}" y2="${r.y1}"/>`;
    }
    s += `<line x1="${xs}" y1="${r.y1}" x2="1080" y2="${r.y1}"/>`;
  }
  return `<g stroke="${color}" stroke-width="${sw}" opacity="${opacity}" stroke-linecap="round">${s}</g>`;
}

/** 粗估字串寬度：CJK 全形算 1em，其餘算 0.58em。 */
export function textWidth(str, size) {
  let w = 0;
  for (const ch of str) w += (ch.codePointAt(0) > 0x2e80 ? 1 : 0.58) * size;
  return w;
}

/** 膠囊標籤。x 依 anchor 定位，y 為中線。可帶前置圖示（symbol id）。 */
export function pill(x, y, label, o = {}) {
  const {
    size = 28,
    fg = '#fff',
    bg = '#333',
    stroke = null,
    sw = 0,
    anchor = 'middle',
    weight = 700,
    family = FONT_SANS,
    ic = null,
    icColor = fg,
    h = size * 1.75,
    padX = size * 0.62,
    rx = null,
    shadow = null,
  } = o;
  const icW = ic ? size * 1.25 : 0;
  const w = textWidth(label, size) + icW + padX * 2;
  const x0 = anchor === 'middle' ? x - w / 2 : anchor === 'end' ? x - w : x;
  const r = rx ?? h / 2;
  let g = `<g${shadow ? ` filter="url(#${shadow})"` : ''}><rect x="${f1(x0)}" y="${f1(y - h / 2)}" width="${f1(w)}" height="${f1(h)}" rx="${f1(r)}" fill="${bg}"${stroke ? ` stroke="${stroke}" stroke-width="${sw}"` : ''}/></g>`;
  if (ic) g += icon(ic, x0 + padX - size * 0.05, y - size * 0.55, size * 1.1, icColor);
  g += text(x0 + padX + icW, y + size * 0.36, label, { size, fill: fg, weight, family });
  return g;
}

export const leader = (x1, y1, x2, y2, color, sw = 3, dash = null) =>
  `<line x1="${f1(x1)}" y1="${f1(y1)}" x2="${f1(x2)}" y2="${f1(y2)}" stroke="${color}" stroke-width="${sw}"${dash ? ` stroke-dasharray="${dash}"` : ''} stroke-linecap="round"/>`;

/** 標題下的細線＋菱形飾線（取自喜帖的飾線語彙）。 */
export function ornament(cx, y, half, color) {
  return `<g><line x1="${f1(cx - half)}" y1="${y}" x2="${f1(cx - 12)}" y2="${y}" stroke="${color}" stroke-width="1.6"/><line x1="${f1(cx + 12)}" y1="${y}" x2="${f1(cx + half)}" y2="${y}" stroke="${color}" stroke-width="1.6"/><rect x="${f1(cx - 5)}" y="${f1(y - 5)}" width="10" height="10" fill="${color}" transform="rotate(45 ${f1(cx)} ${y})"/></g>`;
}

// ---------- 圖示（以 48×48 為基準，currentColor 著色） ----------

export const ICONS = `
<symbol id="ic-car" viewBox="0 0 48 48"><path fill="currentColor" d="M5 34v-6.5c0-2 1.3-3.4 3.2-3.8l4.6-1 4.6-6.3c1-1.3 2.4-2 4-2h9.3c1.6 0 3 .7 4 1.9l5 6.4 3.3.8c1.8.5 3 2 3 3.9V34c0 .8-.6 1.4-1.4 1.4H6.4C5.6 35.4 5 34.8 5 34z"/><path fill="#fff" opacity=".85" d="M18.4 22.3l3.3-4.6c.3-.4.8-.7 1.3-.7h4v5.3zm11.1 0V17h3.3c.5 0 1 .2 1.3.6l3.6 4.7z"/><circle cx="14" cy="35.5" r="5.2" fill="currentColor" stroke="#fff" stroke-width="2.2"/><circle cx="35" cy="35.5" r="5.2" fill="currentColor" stroke="#fff" stroke-width="2.2"/></symbol>
<symbol id="ic-moto" viewBox="0 0 48 48"><circle cx="11" cy="35" r="6" fill="none" stroke="currentColor" stroke-width="3.4"/><circle cx="38" cy="35" r="6" fill="none" stroke="currentColor" stroke-width="3.4"/><path fill="currentColor" d="M6 29.5c0-4.4 3.3-7.5 8-7.5h9.5c1.5 0 2.6 1 2.9 2.4l.9 4.1h6.4l-3.2-13.3h-3.9V12h5.8c.9 0 1.7.6 1.9 1.5l4.9 19.6c.2.8-.4 1.6-1.3 1.6H17.2c-.7-3-3.3-5.2-6.4-5.2z"/><path d="M29.5 11.5h6" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></symbol>
<symbol id="ic-walk" viewBox="0 0 48 48"><circle cx="26" cy="8" r="4.4" fill="currentColor"/><path d="M24 15l-5.5 8.5 3 1.5 L25 20.5l1.8 9-6 13.5 3.6 1.3 5.8-12.5 4.6 12.8 3.6-1.2-5.3-15-1.6-7.9 4 4.3 5.3 1.2.8-3.3-4.3-1-5.3-6.3c-.9-1-2.2-1.5-3.6-1.3z" fill="currentColor"/><path d="M17.5 24l-2.8 8" stroke="currentColor" stroke-width="3.2" stroke-linecap="round"/></symbol>
<symbol id="ic-pin" viewBox="0 0 48 48"><path fill="currentColor" d="M24 3c-8.3 0-15 6.5-15 14.6C9 29 24 45 24 45s15-16 15-27.4C39 9.5 32.3 3 24 3z"/><circle cx="24" cy="17.5" r="5.6" fill="#fff"/></symbol>
<symbol id="ic-elev" viewBox="0 0 48 48"><rect x="8" y="5" width="32" height="38" rx="4" fill="none" stroke="currentColor" stroke-width="3.4"/><path d="M24 10l-6 7h12z M24 38l-6-7h12z" fill="currentColor"/></symbol>
<symbol id="ic-bus" viewBox="0 0 48 48"><rect x="8" y="6" width="32" height="32" rx="6" fill="currentColor"/><rect x="12" y="11" width="24" height="12" rx="2" fill="#fff" opacity=".9"/><circle cx="15" cy="31" r="2.6" fill="#fff"/><circle cx="33" cy="31" r="2.6" fill="#fff"/><rect x="11" y="37" width="6" height="6" rx="1.5" fill="currentColor"/><rect x="31" y="37" width="6" height="6" rx="1.5" fill="currentColor"/></symbol>
<symbol id="ic-train" viewBox="0 0 48 48"><path fill="currentColor" d="M14 4h20c4.4 0 8 3.6 8 8v18c0 3.9-3.1 7-7 7H13c-3.9 0-7-3.1-7-7V12c0-4.4 3.6-8 8-8z"/><rect x="11" y="10" width="26" height="11" rx="2.5" fill="#fff" opacity=".9"/><circle cx="15" cy="29" r="2.6" fill="#fff"/><circle cx="33" cy="29" r="2.6" fill="#fff"/><path d="M13 44l5-7h12l5 7" stroke="currentColor" stroke-width="3.2" fill="none" stroke-linecap="round"/></symbol>
<symbol id="ic-uturn" viewBox="0 0 48 48"><path d="M34 44V20a10 10 0 0 0-20 0v6" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round"/><path d="M5 23l9 11 9-11z" fill="currentColor"/></symbol>
`;

export function icon(id, x, y, size, color) {
  return `<use href="#${id}" x="${f1(x)}" y="${f1(y)}" width="${size}" height="${size}" style="color:${color}" color="${color}"/>`;
}

/** 圓底 P 標誌。 */
export function pSign(cx, cy, r, bg, fg, o = {}) {
  const { rx = r * 0.28, stroke = null, sw = 0, family = FONT_SANS } = o;
  return `<g><rect x="${f1(cx - r)}" y="${f1(cy - r)}" width="${f1(2 * r)}" height="${f1(2 * r)}" rx="${f1(rx)}" fill="${bg}"${stroke ? ` stroke="${stroke}" stroke-width="${sw}"` : ''}/>${text(cx, cy + r * 0.52, 'P', { size: r * 1.5, fill: fg, weight: 800, anchor: 'middle', family })}</g>`;
}

/** 圓形編號徽章。 */
export function badge(cx, cy, r, n, bg, fg, o = {}) {
  const { stroke = null, sw = 0, family = FONT_SANS, size = r * 1.15 } = o;
  return `<g><circle cx="${f1(cx)}" cy="${f1(cy)}" r="${f1(r)}" fill="${bg}"${stroke ? ` stroke="${stroke}" stroke-width="${sw}"` : ''}/>${text(cx, cy + size * 0.36, n, { size, fill: fg, weight: 800, anchor: 'middle', family })}</g>`;
}

// ---------- 平面底圖（多版本共用，以樣式物件換皮） ----------

/**
 * 回傳地圖座標系內的 SVG 片段。
 * s：色彩樣式；o：顯示開關（routes、labels、dim 等）。
 */
export function flatMap(s, o = {}) {
  const {
    routes = true,
    carOn = true,
    motoOn = true,
    uturn = true,
    walk = true,
    labels = true,
    chapelLabel = true,
    gardenLabel = true,
    bldLabels = true,
    roadLabels = true,
    roadLabelX = 760,
    rampOn = true,
    stalls = true,
    lotLabel = true,
    routeW = 12,
    markerPrefix = 'm',
    casing = null,
    routeGroupAttr = '',
  } = o;
  const cased = (d, w) => (casing ? `<path d="${d}" fill="none" stroke="${casing}" stroke-width="${w + 8}" stroke-linecap="round" stroke-linejoin="round"/>` : '');
  const F = s.font || FONT_SANS;
  let g = '';
  // 基地與外圍
  g += `<rect x="-200" y="-200" width="${MAP_W + 400}" height="${MAP_H + 400}" fill="${s.land}"/>`;
  // 高鐵五路
  g += `<polygon points="${polyOf(G.road5)}" fill="${s.road}"${s.roadEdge ? ` stroke="${s.roadEdge}" stroke-width="2"` : ''}/>`;
  // 台74 匝道
  if (rampOn) {
    g += `<polygon points="${polyOf(G.rampPoly)}" fill="${s.ramp}"${s.roadEdge ? ` stroke="${s.roadEdge}" stroke-width="2"` : ''}/>`;
  }
  // 停車場
  g += `<polygon points="${polyOf(G.lot)}" fill="${s.lot}"${s.lotStroke ? ` stroke="${s.lotStroke}" stroke-width="${s.lotStrokeW || 4}" stroke-linejoin="round"${s.lotDash ? ` stroke-dasharray="${s.lotDash}"` : ''}` : ''}/>`;
  g += `<polygon points="${polyOf(G.apron)}" fill="${s.apron || s.lot}"/>`;
  if (stalls && s.stall) g += stallLines(s.stall, s.stallOpacity ?? 0.5, s.stallW ?? 3);
  // 花園、步道、機車道
  g += `<polygon points="${polyOf(G.garden)}" fill="${s.garden}"/>`;
  g += `<polygon points="${polyOf(G.walkway)}" fill="${s.walkway}"/>`;
  g += `<polygon points="${polyOf(G.moto)}" fill="${s.motoLane}"/>`;
  // 高鐵路三段
  g += `<polygon points="${polyOf(G.roadPoly)}" fill="${s.road}"${s.roadEdge ? ` stroke="${s.roadEdge}" stroke-width="2"` : ''}/>`;
  if (s.roadLine) {
    g += `<path d="${pathOf(road)}" fill="none" stroke="${s.roadLine}" stroke-width="3" stroke-dasharray="22 16"/>`;
  }
  // 建物
  const B = G.bld;
  const rect = (x0, x1, fill) => `<rect x="${x0}" y="${G.bldY0}" width="${x1 - x0}" height="${G.bldY1 - G.bldY0}" fill="${fill}"${s.bldStroke ? ` stroke="${s.bldStroke}" stroke-width="2"` : ''}/>`;
  g += rect(...B.corridor, s.bldCorridor);
  g += rect(...B.lobby, s.bldLobby);
  g += rect(...B.elev, s.bldElev);
  g += rect(...B.plan, s.bldPlan);
  g += `<circle cx="${G.chapel.cx}" cy="${G.chapel.cy}" r="${G.chapel.r}" fill="${s.chapel}"/>`;

  if (labels) {
    const bt = s.bldText;
    const cy = (G.bldY0 + G.bldY1) / 2 + 9;
    if (bldLabels) g += text((B.corridor[0] + B.corridor[1]) / 2, cy, '幸福長廊', { size: 26, fill: bt, anchor: 'middle', family: F, ls: 4 });
    if (bldLabels) g += text((B.lobby[0] + B.lobby[1]) / 2, cy - 14, '接待', { size: 26, fill: s.lobbyText || bt, anchor: 'middle', family: F, weight: 700 });
    if (bldLabels) g += text((B.lobby[0] + B.lobby[1]) / 2, cy + 18, '大廳', { size: 26, fill: s.lobbyText || bt, anchor: 'middle', family: F, weight: 700 });
    if (bldLabels) g += text((B.plan[0] + B.plan[1]) / 2, cy, '婚禮企劃中心', { size: 24, fill: bt, anchor: 'middle', family: F });
    if (chapelLabel && bldLabels) g += text(G.chapel.cx, G.chapel.cy + 8, '教堂', { size: 22, fill: s.chapelText || bt, anchor: 'middle', family: F });
    if (gardenLabel) g += text(560, 520, '花 園 綠 地', { size: 26, fill: s.gardenText, anchor: 'middle', family: F, ls: 6, opacity: 0.9 });
    // 路名
    if (roadLabels) g += text(roadLabelX, yAt(road, roadLabelX) + 11, '高 鐵 路 三 段', { size: 30, fill: s.roadText, anchor: 'middle', family: F, weight: 700, rotate: roadAngle(roadLabelX) });
    if (roadLabels) g += vtext((G.road5X[0] + G.road5X[1]) / 2, 110, '高鐵五路', { size: 28, fill: s.roadText, family: F, weight: 700 });
    if (rampOn && roadLabels) g += text(250, yAt(ramp, 250) + 8, '台74 匝道', { size: 22, fill: s.rampText || s.roadText, anchor: 'middle', family: F, rotate: 29 });
  }

  if (routes) {
    if (walk) {
      const w = walkToLobby();
      g += `<path d="${pathOf(w)}" fill="none" stroke="${s.walkRoute}" stroke-width="7" stroke-dasharray="2 14" stroke-linecap="round" marker-end="url(#${markerPrefix}-walk)"/>`;
    }
    if (uturn) {
      g += `<path d="${uturnPath()}" fill="none" stroke="${s.uturnRoute}" stroke-width="${routeW * 0.7}" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="18 12" marker-end="url(#${markerPrefix}-uturn)"/>`;
    }
    let main = '';
    if (motoOn) {
      main += cased(pathOf(motoRoute()), routeW);
      main += `<path d="${pathOf(motoRoute())}" fill="none" stroke="${s.motoRoute}" stroke-width="${routeW}" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#${markerPrefix}-moto)"/>`;
    }
    if (carOn) {
      main += cased(pathOf(carRoute()), routeW);
      main += `<path d="${pathOf(carRoute())}" fill="none" stroke="${s.carRoute}" stroke-width="${routeW}" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#${markerPrefix}-car)"/>`;
    }
    g += routeGroupAttr ? `<g ${routeGroupAttr}>${main}</g>` : main;
  }
  return g;
}

export function flatMapMarkers(s, prefix = 'm', size = 3.2, outline = null) {
  return (
    arrowMarker(`${prefix}-car`, s.carRoute, size, outline) +
    arrowMarker(`${prefix}-moto`, s.motoRoute, size, outline) +
    arrowMarker(`${prefix}-uturn`, s.uturnRoute, size * 1.2) +
    arrowMarker(`${prefix}-walk`, s.walkRoute, size * 0.9)
  );
}

/** 地圖錨點：各版本放標籤／徽章的位置（地圖座標）。 */
export const ANCHOR = {
  lotCenter: [640, 150],
  carGate: [(G.carGateX0 + G.carGateX1) / 2 + 30, yAt(roadTop, (G.carGateX0 + G.carGateX1) / 2 + 30) - 50],
  motoGate: [(G.motoBot[0] + G.motoBot[1]) / 2 + 20, yAt(roadTop, G.motoBot[1]) - 70],
  lobby: [(G.bld.lobby[0] + G.bld.lobby[1]) / 2, (G.bldY0 + G.bldY1) / 2],
  uturn: [(G.road5X[0] + G.road5X[1]) / 2, yAt(road, (G.road5X[0] + G.road5X[1]) / 2)],
};
