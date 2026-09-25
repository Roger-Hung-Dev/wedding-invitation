// V07 捷運路線圖：不畫地形，把「高鐵路三段往北」當成一條主線，入口、停車場、大廳當成站點。
// 只回答「依序會經過什麼、在哪裡轉」，適合不太會看地圖的賓客。
import { FACTS, FONT_SANS, ICONS, svgDoc, text, icon, arrowMarker, pSign } from './lib.mjs';

export const meta = {
  id: 'v07',
  name: '捷運路線圖版',
  note: '不畫地形，把高鐵路三段當成一條主線、入口與大廳當成站點，只回答「依序經過什麼、在哪轉」。',
};

export default function build() {
  const W = 1200;
  const H = 880;
  const C = { bg: '#FAFAF7', ink: '#111827', muted: '#6B7280', road: '#4B5563', car: '#2563EB', moto: '#F97316', walk: '#BE185D', south: '#7C3AED', hub: '#111827' };
  const Y = 600; // 主線高度
  const xFive = 1030;
  const xMoto = 730;
  const xCar = 260;
  const hubY0 = 236;
  const hubY1 = 336;
  let g = '';

  // 南下（對向車道）＋迴轉
  g += `<path d="M110 ${Y + 52} H${xFive + 10} A26 26 0 0 0 ${xFive + 10} ${Y}" fill="none" stroke="${C.south}" stroke-width="8" stroke-dasharray="16 10" stroke-linecap="round" marker-end="url(#v07-south)"/>`;
  g += text(118, Y + 94, '南下車流（從台74 下來）→', { size: 21, fill: C.south, weight: 700 });
  g += text(xFive + 20, Y + 94, '到高鐵五路口左迴轉，回到主線往北', { size: 21, fill: C.south, weight: 700, anchor: 'end' });

  // 主線：高鐵路三段（往北＝往左）
  g += `<line x1="100" y1="${Y}" x2="1160" y2="${Y}" stroke="${C.road}" stroke-width="30" stroke-linecap="round"/>`;
  for (let x = 1120; x > 120; x -= 90) {
    if (Math.abs(x - xFive) < 40 || Math.abs(x - xMoto) < 40 || Math.abs(x - xCar) < 40) continue;
    g += `<path d="M${x + 7} ${Y - 8} L${x - 5} ${Y} L${x + 7} ${Y + 8}" fill="none" stroke="#FFFFFF" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>`;
  }
  g += text(1160, Y + 58, '北上車流', { size: 20, fill: C.muted, anchor: 'end' });
  g += text(100, Y - 34, '往台74 匝道', { size: 20, fill: C.muted });

  // 支線：汽車、機車上行進停車場
  g += `<path d="M${xCar} ${Y} V${hubY1 + 4}" stroke="${C.car}" stroke-width="22" stroke-linecap="round" marker-end="url(#v07-car)"/>`;
  g += `<path d="M${xMoto} ${Y} V${hubY1 + 4}" stroke="${C.moto}" stroke-width="22" stroke-linecap="round" marker-end="url(#v07-moto)"/>`;

  // 站點
  const station = (x, color, r = 22) => `<circle cx="${x}" cy="${Y}" r="${r}" fill="#FFFFFF" stroke="${color}" stroke-width="9"/>`;
  g += station(xFive, C.ink, 24);
  g += station(xMoto, C.moto);
  g += station(xCar, C.car);
  g += text(xFive, Y - 46, '高鐵五路口', { size: 26, fill: C.ink, weight: 800, anchor: 'middle' });
  g += icon('ic-moto', xMoto + 26, Y - 100, 44, C.moto) + text(xMoto + 78, Y - 66, '機車入口', { size: 30, fill: C.moto, weight: 800 });
  g += text(xMoto + 30, Y - 36, '靠高鐵五路那一端', { size: 19, fill: C.muted });
  g += icon('ic-car', xCar + 26, Y - 100, 44, C.car) + text(xCar + 78, Y - 66, '汽車入口', { size: 30, fill: C.car, weight: 800 });
  g += text(xCar + 30, Y - 36, '靠台74 匝道那一端', { size: 19, fill: C.muted });

  // 樞紐：停車場
  g += `<rect x="170" y="${hubY0}" width="680" height="${hubY1 - hubY0}" rx="50" fill="#FFFFFF" stroke="${C.hub}" stroke-width="8"/>`;
  g += pSign(236, (hubY0 + hubY1) / 2, 32, C.hub, '#FFFFFF', { rx: 10 });
  g += text(290, (hubY0 + hubY1) / 2 - 2, '飯店停車場', { size: 34, fill: C.ink, weight: 800 });
  g += text(292, (hubY0 + hubY1) / 2 + 34, `${FACTS.capacity}・${FACTS.bus}`, { size: 19, fill: C.muted });

  // 步行線：停車場 → 接待大廳 → 2F 東方明珠
  const wy = (hubY0 + hubY1) / 2;
  g += `<line x1="854" y1="${wy}" x2="1100" y2="${wy}" stroke="${C.walk}" stroke-width="10" stroke-dasharray="2 16" stroke-linecap="round"/>`;
  g += `<circle cx="960" cy="${wy}" r="20" fill="#FFFFFF" stroke="${C.walk}" stroke-width="8"/>`;
  g += `<circle cx="1110" cy="${wy}" r="32" fill="${C.walk}"/><circle cx="1110" cy="${wy}" r="22" fill="none" stroke="#FFFFFF" stroke-width="4"/>`;
  g += `<path d="M1110 ${wy + 9} c-10 -7 -13 -11 -13 -16 a6.5 6.5 0 0 1 13 -2 a6.5 6.5 0 0 1 13 2 c0 5 -3 9 -13 16z" fill="#FFFFFF"/>`;
  g += text(960, wy + 62, '接待大廳', { size: 24, fill: C.walk, weight: 800, anchor: 'middle' });
  g += text(960, wy + 90, '搭電梯上樓', { size: 18, fill: C.muted, anchor: 'middle' });
  g += text(1110, wy - 50, FACTS.hall, { size: 24, fill: C.walk, weight: 800, anchor: 'middle' });
  g += icon('ic-walk', 880, wy - 64, 36, C.walk);

  // 標題
  let body = '';
  body += text(48, 80, '停車路線圖', { size: 46, fill: C.ink, weight: 800, ls: 3 });
  body += text(50, 120, `${FACTS.hotel}｜${FACTS.addr}｜沿主線由右往左＝往北`, { size: 21, fill: C.muted });
  body += g;
  // 圖例
  const ly = 800;
  const chip = (x, color, label, dash) =>
    `<line x1="${x}" y1="${ly - 7}" x2="${x + 46}" y2="${ly - 7}" stroke="${color}" stroke-width="10" stroke-linecap="round"${dash ? ` stroke-dasharray="${dash}"` : ''}/>` + text(x + 58, ly, label, { size: 20, fill: C.ink });
  body += `<line x1="48" y1="${ly - 48}" x2="${W - 48}" y2="${ly - 48}" stroke="#E5E7EB" stroke-width="2"/>`;
  body += chip(48, C.road, '高鐵路三段（往北）');
  body += chip(318, C.car, '汽車');
  body += chip(452, C.moto, '機車');
  body += chip(586, C.south, '南下迴轉', '14 9');
  body += chip(774, C.walk, '步行', '2 12');
  body += text(W - 48, ly + 44, FACTS.source, { size: 16, fill: '#9CA3AF', anchor: 'end' });
  body += text(48, ly + 44, FACTS.leave, { size: 16, fill: '#9CA3AF' });

  return svgDoc({
    w: W,
    h: H,
    title: '臻愛花園飯店停車資訊（捷運路線圖版）',
    desc: '以路線圖表示：沿高鐵路三段往北，先經過高鐵五路口、再到機車入口、最後是汽車入口，兩個入口都通往飯店停車場，停車後步行到接待大廳搭電梯上 2F 東方明珠。',
    defs: ICONS + arrowMarker('v07-car', C.car, 2.2) + arrowMarker('v07-moto', C.moto, 2.2) + arrowMarker('v07-south', C.south, 3),
    body,
    bg: C.bg,
  });
}
