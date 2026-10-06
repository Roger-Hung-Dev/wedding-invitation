// V4 四格分流版：高鐵／台鐵／捷運／公車各一張卡，地圖只亮自己那條路線（含站內走到 7 號出口的那一段），
// 讓賓客只看跟自己有關的那一格。
import { C, FACTS, MODES, ICONS, EXTRA_ICONS, FONT_SERIF, text, icon, badge, pill, mapDefs, baseMap, placeMap, header, svgDoc } from './tlib.mjs';

export const meta = {
  id: 'v4',
  name: '四格分流版',
  note: '四種交通方式各一格，每格的地圖只亮自己那條路線，連站內怎麼走到 7 號出口都畫出來。賓客只要找到自己那一格。',
};

const STEPS = {
  hsr: ['出月台，下手扶梯到一樓 7 號出口', '沿站區二路往北，過高鐵三路、高鐵五路', '走進飯店停車場，到接待大廳'],
  tra: ['出台鐵閘門，往高鐵 3 號出入口', '下手扶梯到一樓 7 號出口', '之後同高鐵：沿站區二路往北直走'],
  mrt: ['搭到終點站，不要在前一站「烏日」下車', '下手扶梯到一樓 7 號出口', '之後同高鐵：沿站區二路往北直走'],
  bus: ['在「國際會展中心（高鐵五路）」下車', '往高鐵路三段方向，右轉就到飯店', '走進飯店，到接待大廳'],
};

export default function build() {
  const W = 1200;
  const H = 1934;
  let body = '';
  let defs = ICONS + EXTRA_ICONS;
  const hd = header(W, H, 'TRANSIT GUIDE', '搭車來怎麼走', `${FACTS.hotel}｜找到您搭的那一格就好`);
  body += hd.svg;

  const CW = 540;
  const CH = 700;
  const VB = [158, 168, 700, 584];
  const VB_BUS = [100, 186, 540, 450];
  const top = 262;
  MODES.forEach((m, i) => {
    const x = 50 + (i % 2) * (CW + 20);
    const y = top + Math.floor(i / 2) * (CH + 24);
    const p = `v4${m.key}`;
    defs += mapDefs(p, 1.2);
    body += `<rect x="${x}" y="${y}" width="${CW}" height="${CH}" rx="24" fill="#FFFFFF" stroke="${C.soft}" stroke-width="2"/>`;
    // 卡頭
    body += `<circle cx="${x + 52}" cy="${y + 58}" r="30" fill="${m.color}"/>` + icon(m.ic, x + 34, y + 40, 36, '#FFFFFF');
    body += text(x + 98, y + 56, m.name, { size: 36, fill: m.color, weight: 700, family: FONT_SERIF, ls: 3 });
    body += text(x + 99, y + 88, m.station, { size: 20, fill: C.muted });
    body += text(x + CW - 30, y + 44, '步行約', { size: 18, fill: C.muted, anchor: 'end' });
    body += text(x + CW - 78, y + 96, String(m.min), { size: 58, fill: C.gold, weight: 700, anchor: 'end', family: FONT_SERIF });
    body += text(x + CW - 30, y + 94, '分鐘', { size: 20, fill: C.gold, weight: 700, anchor: 'end' });

    // 地圖
    const rail = m.key !== 'bus';
    const inner = baseMap(p, {
      routes: rail ? ['walk'] : ['bus'],
      indoor: rail ? [m.key] : [],
      compass: false,
      labelScale: 1.15,
    });
    const map = placeMap(p, x + 20, y + 118, CW - 40, rail ? VB : VB_BUS, inner, 16);
    body += map.svg;

    // 步驟
    const sy = y + 118 + map.h + 46;
    STEPS[m.key].forEach((s, j) => {
      body += badge(x + 38, sy + j * 40 - 7, 13, String(j + 1), m.color, '#FFFFFF', { size: 16 });
      const warn = m.key === 'mrt' && j === 0;
      body += text(x + 62, sy + j * 40, s, { size: 21, fill: warn ? C.pink : C.wine, weight: warn ? 700 : 400 });
    });
  });

  const fy = top + 2 * CH + 24 + 48;
  body += `<line x1="80" y1="${fy}" x2="${W - 80}" y2="${fy}" stroke="${C.soft}" stroke-width="2"/>`;
  body += `<circle cx="${W / 2 - 290}" cy="${fy + 50}" r="24" fill="${C.pink}"/>` + icon('ic-elev', W / 2 - 306, fy + 34, 32, '#FFFFFF');
  body += text(W / 2 - 252, fy + 60, '四條路線的終點都一樣：接待大廳搭電梯上 2F 東方明珠', { size: 24, fill: C.wine, weight: 700, family: FONT_SERIF });
  body += text(W / 2, H - 52, FACTS.source, { size: 16, fill: C.muted, anchor: 'middle' });

  return svgDoc({
    w: W,
    h: H,
    title: '臻愛花園飯店大眾運輸交通資訊（四格分流版）',
    desc: '四格分別說明高鐵、台鐵、捷運、公車的走法，每格地圖只標出該交通方式的路線。',
    defs,
    body,
  });
}
