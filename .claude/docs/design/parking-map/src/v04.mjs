// V04 立體鳥瞰：把共用平面圖投影成斜俯視，建物拉出高度、停車場擺上車子，入口用浮空大頭針標示。
import { FACTS, FONT_SANS, ICONS, G, ANCHOR, road, roadTop, laneN, yAt, svgDoc, text, f1, arrowMarker, carRoute, motoRoute, walkToLobby, icon } from './lib.mjs';

export const meta = {
  id: 'v04',
  name: '立體鳥瞰版',
  note: '斜俯視的立體模型：建物有高度、停車場停滿車，入口用浮在空中的大頭針標示，最有「現場感」。',
};

const A = (10 * Math.PI) / 180;
const Q = 0.68;
let K = 0.78;
let OX = 0;
let OY = 0;

/** 地圖座標 → 畫面座標（z 往上）。 */
function P(x, y, z = 0) {
  const X = x * Math.cos(A) - y * Math.sin(A);
  const Y = x * Math.sin(A) + y * Math.cos(A);
  return [OX + K * X, OY + K * Q * Y - K * z];
}
const poly = (pts, z = 0) => pts.map(([x, y]) => P(x, y, z).map(f1).join(',')).join(' ');
const pathP = (pts, z = 0) => 'M' + pts.map(([x, y]) => P(x, y, z).map(f1).join(' ')).join(' L');

function shade(hex, f) {
  const n = parseInt(hex.slice(1), 16);
  const c = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map((v) => Math.max(0, Math.min(255, Math.round(v * f))));
  return '#' + c.map((v) => v.toString(16).padStart(2, '0')).join('');
}

function inside(pt, pts) {
  let c = false;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [xi, yi] = pts[i];
    const [xj, yj] = pts[j];
    if (yi > pt[1] !== yj > pt[1] && pt[0] < ((xj - xi) * (pt[1] - yi)) / (yj - yi) + xi) c = !c;
  }
  return c;
}

/** 擠出多邊形：只畫面向觀看者的側面，最後蓋頂面。 */
function extrude(pts, h, color, z0 = 0) {
  let s = '';
  const faces = [];
  for (let i = 0; i < pts.length; i++) {
    const p = pts[i];
    const q = pts[(i + 1) % pts.length];
    const dx = q[0] - p[0];
    const dy = q[1] - p[1];
    const len = Math.hypot(dx, dy);
    let n = [dy / len, -dx / len];
    const mid = [(p[0] + q[0]) / 2 + n[0] * 0.5, (p[1] + q[1]) / 2 + n[1] * 0.5];
    if (inside(mid, pts)) n = [-n[0], -n[1]];
    const facing = n[0] * Math.sin(A) + n[1] * Math.cos(A);
    if (facing <= 0) continue;
    const light = n[0] > 0 ? 0.78 : 0.9;
    faces.push({ d: `${poly([p, q], z0)} ${poly([q, p], z0 + h)}`, fill: shade(color, light), depth: (p[1] + q[1]) / 2 });
  }
  faces.sort((a, b) => a.depth - b.depth);
  for (const f of faces) s += `<polygon points="${f.d}" fill="${f.fill}" stroke="${shade(color, 0.7)}" stroke-width="0.8" stroke-linejoin="round"/>`;
  s += `<polygon points="${poly(pts, z0 + h)}" fill="${color}" stroke="${shade(color, 0.8)}" stroke-width="1" stroke-linejoin="round"/>`;
  return s;
}

const rectPts = (x0, y0, x1, y1) => [
  [x0, y0],
  [x1, y0],
  [x1, y1],
  [x0, y1],
];
const circlePts = (cx, cy, r, n = 28) => Array.from({ length: n }, (_, i) => [cx + r * Math.cos((i / n) * 2 * Math.PI), cy + r * Math.sin((i / n) * 2 * Math.PI)]);

/** 浮空大頭針：尖端落在 (sx, sy)，頭部高 hh。 */
function pinAt(sx, sy, hh, r, color, inner) {
  const t = `M${f1(sx)} ${f1(sy)} L${f1(sx - r * 0.62)} ${f1(sy - hh + r * 0.55)} A${r} ${r} 0 1 1 ${f1(sx + r * 0.62)} ${f1(sy - hh + r * 0.55)} Z`;
  return `<ellipse cx="${f1(sx)}" cy="${f1(sy)}" rx="${f1(r * 0.55)}" ry="${f1(r * 0.2)}" fill="#000" opacity="0.18"/><path d="${t}" fill="${color}" stroke="#FFFFFF" stroke-width="4" filter="url(#v04-shadow)"/>${inner(sx, sy - hh)}`;
}

export default function build() {
  const W = 1200;
  let H = 1000;
  const C = {
    sky0: '#EEF3F8',
    sky1: '#F8F5EF',
    land: '#E9E3D5',
    slab: '#CFC5B1',
    road: '#FBFAF7',
    roadEdge: '#D6CCBA',
    lot: '#5C6470',
    stall: '#FFFFFF',
    garden: '#A9D18E',
    walkway: '#EADAB9',
    moto: '#E3A465',
    corridor: '#F6C4D5',
    lobby: '#F472B6',
    elev: '#C4B5FD',
    plan: '#FBE2B6',
    chapel: '#FDF1B8',
    ink: '#1F2937',
    muted: '#6B7280',
    car: '#2563EB',
    motoRoute: '#F97316',
    pink: '#DB2777',
  };

  // 讓整塊地板置中：先算投影範圍再定位。
  const GX0 = -10;
  const GX1 = 1320;
  const ground = rectPts(GX0, 0, GX1, 830);
  K = 1;
  OX = 0;
  OY = 0;
  let pr = ground.map(([x, y]) => P(x, y));
  const spanX = Math.max(...pr.map((p) => p[0])) - Math.min(...pr.map((p) => p[0]));
  K = (W - 60) / spanX;
  pr = ground.map(([x, y]) => P(x, y));
  const minX = Math.min(...pr.map((p) => p[0]));
  const minY = Math.min(...pr.map((p) => p[1]));
  OX = 30 - minX;
  OY = 318 - minY;
  const maxY = Math.max(...ground.map(([x, y]) => P(x, y)[1]));
  H = Math.round(maxY + 26 * K + 96);

  let g = '';
  // 地板（帶厚度）
  g += extrude(ground, 26, C.land, -26);
  // 道路
  const road5 = G.road5.map(([x, y]) => [x, Math.max(y, 0)]);
  g += `<polygon points="${poly(road5)}" fill="${C.road}" stroke="${C.roadEdge}" stroke-width="1.5"/>`;
  g += `<polygon points="${poly(G.rampPoly.map(([x, y]) => [Math.max(x, GX0), y]))}" fill="#F1EEE7" stroke="${C.roadEdge}" stroke-width="1.5"/>`;
  const clampX = (pts) => pts.filter(([x]) => x >= GX0 && x <= GX1);
  const roadPoly = [...clampX(roadTop), ...clampX(G.roadPoly.slice(roadTop.length))];
  g += `<polygon points="${poly(roadPoly)}" fill="${C.road}" stroke="${C.roadEdge}" stroke-width="1.5"/>`;
  g += `<path d="${pathP(clampX(road))}" fill="none" stroke="#D9D2C3" stroke-width="2.5" stroke-dasharray="16 12"/>`;
  // 停車場
  g += `<polygon points="${poly(G.lot)}" fill="${C.lot}"/>`;
  g += `<polygon points="${poly(G.apron)}" fill="${C.lot}"/>`;
  let stalls = '';
  const rows = [
    [60, 120],
    [168, 228],
  ];
  for (const [y0, y1] of rows) {
    for (let x = 250; x <= 1090; x += 42) stalls += `<path d="${pathP([
      [x, y0],
      [x, y1],
    ])}"/>`;
  }
  g += `<g stroke="${C.stall}" stroke-width="1.6" opacity="0.65">${stalls}</g>`;
  // 綠地、步道、機車道
  g += `<polygon points="${poly(G.garden)}" fill="${C.garden}"/>`;
  g += `<polygon points="${poly(G.walkway)}" fill="${C.walkway}"/>`;
  g += `<polygon points="${poly(G.moto)}" fill="${C.moto}"/>`;

  // 路線（貼地）
  const routeLine = (pts, color, id) =>
    `<path d="${pathP(pts)}" fill="none" stroke="#FFFFFF" stroke-width="15" stroke-linecap="round" stroke-linejoin="round"/><path d="${pathP(pts)}" fill="none" stroke="${color}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#${id})"/>`;
  g += routeLine(motoRoute(GX1), C.motoRoute, 'v04-moto');
  g += routeLine(carRoute(GX1), C.car, 'v04-car');

  // 停好的車（小方塊，後排先畫）
  const palette = ['#F8FAFC', '#94A3B8', '#1F2937', '#DC2626', '#F8FAFC', '#64748B', '#E5E7EB', '#1E3A8A'];
  let cars = '';
  let seed = 7;
  const rnd = () => ((seed = (seed * 9301 + 49297) % 233280) / 233280);
  for (const [y0] of rows) {
    for (let x = 250; x < 1090; x += 42) {
      if (rnd() < 0.3) continue;
      const c = palette[Math.floor(rnd() * palette.length)];
      cars += extrude(rectPts(x + 7, y0 + 8, x + 35, y0 + 52), 12, c);
      cars += `<polygon points="${poly(rectPts(x + 10, y0 + 20, x + 32, y0 + 38), 12.2)}" fill="#0F172A" opacity="0.35"/>`;
    }
  }
  g += cars;

  // 樹（沿步道）
  const trees = [];
  for (let x = 320; x <= 880; x += 70) trees.push([x, yAt(roadTop, x) - 46]);
  trees.push([760, 440], [420, 450]);
  trees.sort((a, b) => a[1] - b[1]);
  const treeSvg = trees
    .map(([x, y]) => {
      const [sx, sy] = P(x, y);
      return `<ellipse cx="${f1(sx)}" cy="${f1(sy)}" rx="13" ry="5" fill="#000" opacity="0.15"/><rect x="${f1(sx - 2)}" y="${f1(sy - 16)}" width="4" height="16" fill="#8B5E3C"/><circle cx="${f1(sx)}" cy="${f1(sy - 26)}" r="15" fill="#5EA64B"/><circle cx="${f1(sx - 4)}" cy="${f1(sy - 30)}" r="7" fill="#7FC36A"/>`;
    })
    .join('');

  // 建物
  const B = G.bld;
  let bld = '';
  bld += extrude(rectPts(B.corridor[0], G.bldY0, B.corridor[1], G.bldY1), 58, C.corridor);
  bld += extrude(rectPts(B.lobby[0], G.bldY0, B.lobby[1], G.bldY1), 100, C.lobby);
  bld += extrude(rectPts(B.elev[0], G.bldY0, B.elev[1], G.bldY1), 116, C.elev);
  bld += extrude(rectPts(B.plan[0], G.bldY0, B.plan[1], G.bldY1), 72, C.plan);
  // 窗帶
  const winBand = (x0, x1, z) => `<path d="${pathP(
    [
      [x0 + 14, G.bldY1],
      [x1 - 14, G.bldY1],
    ],
    z,
  )}" stroke="#FFFFFF" stroke-width="5" opacity="0.7" stroke-linecap="round"/>`;
  bld += winBand(...B.corridor, 30) + winBand(...B.plan, 40) + winBand(...B.lobby, 34) + winBand(...B.lobby, 72);
  // 教堂
  bld += extrude(circlePts(G.chapel.cx, G.chapel.cy, 34), 46, C.chapel);
  const [tx, ty] = P(G.chapel.cx, G.chapel.cy, 46);
  bld += `<path d="M${f1(tx - 25)} ${f1(ty)} L${f1(tx)} ${f1(ty - 40)} L${f1(tx + 25)} ${f1(ty)} Z" fill="#E9B949"/>`;

  g += bld + treeSvg;

  // 建物與路名標籤
  const lab = (x, y, z, s, o = {}) => {
    const [sx, sy] = P(x, y, z);
    return text(sx, sy, s, { size: 19, fill: C.ink, anchor: 'middle', weight: 700, stroke: '#FFFFFF', sw: 5, ...o });
  };
  g += lab((B.corridor[0] + B.corridor[1]) / 2, G.bldY1, 26, '幸福長廊', { size: 18 });
  g += lab((B.plan[0] + B.plan[1]) / 2, G.bldY1, 26, '婚禮企劃中心', { size: 18 });
  g += lab(G.chapel.cx, G.chapel.cy + 40, 0, '教堂', { size: 16, fill: C.muted });
  const [r3x, r3y] = P(760, yAt(road, 760));
  g += text(r3x, r3y + 18, '高 鐵 路 三 段', { size: 22, fill: '#9A8F7C', anchor: 'middle', weight: 700, rotate: 13 });
  const [r5x, r5y] = P(1236, 90);
  g += text(r5x, r5y, '高鐵五路', { size: 20, fill: '#9A8F7C', anchor: 'middle', weight: 700, rotate: 70 });
  const [rpx, rpy] = P(200, 620);
  g += text(rpx, rpy, '台74 匝道', { size: 18, fill: '#9A8F7C', anchor: 'middle', rotate: 38 });

  // 浮空大頭針＋說明卡。上排三張卡片用細線連到針頭，避免卡片互相壓到。
  const cardW = (title, sub) => Math.max(title.length * 26, sub.length * 17) + 36;
  const card = (x0, y, title, sub, color) => {
    const w = cardW(title, sub);
    return `<g filter="url(#v04-shadow)"><rect x="${f1(x0)}" y="${f1(y - 34)}" width="${f1(w)}" height="78" rx="14" fill="#FFFFFF"/></g><rect x="${f1(x0)}" y="${f1(y - 34)}" width="8" height="78" rx="4" fill="${color}"/>${text(x0 + 22, y - 2, title, { size: 26, fill: color, weight: 800 })}${text(x0 + 22, y + 30, sub, { size: 17, fill: C.muted })}`;
  };
  const cardY = 190;
  const topCard = (x0, head, title, sub, color) => {
    const w = cardW(title, sub);
    const lx = Math.min(Math.max(head[0], x0 + 24), x0 + w - 24);
    return `<path d="M${f1(lx)} ${cardY + 44} L${f1(head[0])} ${f1(head[1])}" stroke="${color}" stroke-width="2.5" stroke-dasharray="4 5" fill="none"/>` + card(x0, cardY, title, sub, color);
  };
  let pins = '';
  // P
  const [lpx, lpy] = P(930, 120);
  pins += pinAt(lpx, lpy, 140, 50, C.car, (x, y) => text(x, y + 22, 'P', { size: 64, fill: '#FFFFFF', weight: 800, anchor: 'middle' }));
  // 汽車入口
  const [cgx, cgy] = P(ANCHOR.carGate[0] - 10, ANCHOR.carGate[1] + 40);
  pins += pinAt(cgx, cgy, 104, 34, C.car, (x, y) => icon('ic-car', x - 22, y - 22, 44, '#FFFFFF'));
  // 機車入口
  const [mgx, mgy] = P(ANCHOR.motoGate[0], ANCHOR.motoGate[1] + 40);
  pins += pinAt(mgx, mgy, 104, 34, C.motoRoute, (x, y) => icon('ic-moto', x - 22, y - 22, 44, '#FFFFFF'));
  pins += card(mgx + 44, mgy - 120, '機車入口', '靠高鐵五路那一端', C.motoRoute);
  // 大廳
  const [lbx, lby] = P(ANCHOR.lobby[0], G.bldY0 + 30, 100);
  pins += pinAt(lbx, lby, 84, 30, C.pink, (x, y) => `<path d="M${f1(x)} ${f1(y + 10)} c-14 -10 -18 -16 -18 -22 a9 9 0 0 1 18 -3 a9 9 0 0 1 18 3 c0 6 -4 12 -18 22z" fill="#FFFFFF"/>`);
  // 上排卡片
  pins += topCard(40, [cgx, cgy - 104 - 34], '汽車入口', '靠台74 匝道那一端', C.car);
  pins += topCard(330, [lbx, lby - 84 - 30], '接待大廳', `搭電梯上 ${FACTS.hall}`, C.pink);
  pins += topCard(W - 40 - cardW('飯店停車場', '汽機車位共約 1,000 個・可停遊覽車'), [lpx, lpy - 140 - 50], '飯店停車場', '汽機車位共約 1,000 個・可停遊覽車', C.car);

  let body = '';
  body += `<defs><linearGradient id="v04-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${C.sky0}"/><stop offset="1" stop-color="${C.sky1}"/></linearGradient></defs>`;
  body += `<rect width="${W}" height="${H}" fill="url(#v04-sky)"/>`;
  body += text(48, 76, '停車場在飯店後方', { size: 42, fill: C.ink, weight: 800, ls: 2 });
  body += text(50, 114, `${FACTS.hotel}｜${FACTS.addr}`, { size: 20, fill: C.muted });
  body += g + pins;
  // 圖例
  const ly = H - 44;
  body += `<line x1="48" y1="${ly - 6}" x2="92" y2="${ly - 6}" stroke="${C.car}" stroke-width="8" stroke-linecap="round"/>` + text(104, ly, '汽車進場', { size: 19, fill: C.ink });
  body += `<line x1="220" y1="${ly - 6}" x2="264" y2="${ly - 6}" stroke="${C.motoRoute}" stroke-width="8" stroke-linecap="round"/>` + text(276, ly, '機車進場', { size: 19, fill: C.ink });
  body += text(400, ly, '南下車流請於高鐵五路口左迴轉　｜　' + FACTS.source, { size: 16, fill: C.muted });

  return svgDoc({
    w: W,
    h: H,
    title: '臻愛花園飯店停車資訊（立體鳥瞰版）',
    desc: '斜俯視立體圖：停車場位於飯店建物後方，汽車入口在左端、機車入口在右端靠高鐵五路，接待大廳可搭電梯上 2F 東方明珠。',
    defs:
      ICONS +
      arrowMarker('v04-car', C.car, 3.2, '#FFFFFF') +
      arrowMarker('v04-moto', C.motoRoute, 3.2, '#FFFFFF') +
      `<filter id="v04-shadow" x="-20%" y="-20%" width="140%" height="160%"><feDropShadow dx="0" dy="4" stdDeviation="5" flood-color="#1F2937" flood-opacity="0.22"/></filter>`,
    body,
  });
}
