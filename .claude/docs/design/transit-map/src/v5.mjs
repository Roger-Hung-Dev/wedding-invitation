// V5 步驟圖卡版（手機直式 1080 寬）：把「出站 → 沿站區二路往北 → 穿過停車場 → 上 2F」拆成四張卡，
// 每張只畫那一步需要的東西；公車另外一張卡。字級以長輩在手機上看得清楚為準。
import { C, FACTS, MODE, ICONS, EXTRA_ICONS, FONT_SERIF, text, icon, badge, pill, mapDefs, baseMap, placeMap, svgDoc, ornament, FONT_DISPLAY } from './tlib.mjs';

export const meta = {
  id: 'v5',
  name: '手機步驟圖卡版',
  note: '手機直式長圖。把搭車來的路拆成四步，每一步只畫那一步要看的東西（車站剖面、站區二路、停車場），字最大、最適合長輩一步一步照著走。',
};

export default function build() {
  const W = 1080;
  let defs = ICONS + EXTRA_ICONS;
  let body = '';
  const X = 40;
  const CW = W - 80;

  // 標題
  body += text(W / 2, 110, 'STEP BY STEP', { size: 26, fill: C.gold, anchor: 'middle', family: FONT_DISPLAY, ls: 10 });
  body += text(W / 2, 192, '搭車來，跟著四步走', { size: 64, fill: C.wine, anchor: 'middle', family: FONT_SERIF, weight: 700, ls: 6 });
  body += ornament(W / 2, 232, 170, C.frame);
  body += text(W / 2, 282, `${FACTS.hotel}｜高鐵・台鐵・捷運都這樣走`, { size: 28, fill: C.muted, anchor: 'middle', family: FONT_SERIF });

  // 步行時間列
  let y = 330;
  body += text(W / 2, y + 8, '出站後步行時間', { size: 22, fill: C.muted, anchor: 'middle', ls: 2 });
  const chips = ['hsr', 'tra', 'mrt', 'bus'];
  const chipW = 228;
  chips.forEach((k, i) => {
    const m = MODE[k];
    const cx = X + chipW / 2 + i * (chipW + (CW - chipW * 4) / 3);
    body += `<rect x="${cx - chipW / 2}" y="${y + 30}" width="${chipW}" height="76" rx="38" fill="#FFFFFF" stroke="${m.color}" stroke-width="3"/>`;
    body += text(cx - 54, y + 80, m.name, { size: 30, fill: m.color, weight: 700, anchor: 'middle', family: FONT_SERIF });
    body += text(cx + 46, y + 81, `${m.min} 分`, { size: 32, fill: C.wine, weight: 700, anchor: 'middle' });
  });
  y += 150;

  const card = (y0, h, n, title, color = C.gold) =>
    `<rect x="${X}" y="${y0}" width="${CW}" height="${h}" rx="30" fill="#FFFFFF" stroke="${C.soft}" stroke-width="2"/>` +
    (n ? badge(X + 76, y0 + 74, 36, n, color, '#FFFFFF', { size: 40, family: FONT_SERIF }) : '') +
    text(X + (n ? 132 : 52), y0 + 90, title, { size: 46, fill: C.wine, weight: 700, family: FONT_SERIF, ls: 2 });

  // ---- 第 1 步：車站剖面 ----
  {
    const h = 800;
    body += card(y, h, '1', '先到一樓「7 號出口」');
    const fx = X + 40;
    const fw = CW - 80;
    const f2 = y + 140;
    const f1y = y + 470;
    body += `<rect x="${fx}" y="${f2}" width="${fw}" height="130" rx="18" fill="${C.blush}"/>`;
    body += `<rect x="${fx}" y="${f1y}" width="${fw}" height="120" rx="18" fill="#FBF3E2"/>`;
    body += text(fx + 22, f2 + 44, '2F', { size: 34, fill: C.gold, weight: 700, family: FONT_SERIF });
    body += text(fx + 22, f1y + 44, '1F', { size: 34, fill: C.gold, weight: 700, family: FONT_SERIF });
    const srcs = [
      { m: MODE.hsr, x: fx + 210, label: '高鐵 月台' },
      { m: MODE.tra, x: fx + 470, label: '台鐵 新烏日站' },
      { m: MODE.mrt, x: fx + 740, label: '捷運 高鐵臺中站' },
    ];
    const esc = [fx + fw / 2 + 60, f2 + 190];
    for (const s of srcs) {
      body += `<path d="M${s.x} ${f2 + 92} Q${s.x} ${esc[1] - 20} ${esc[0]} ${esc[1] - 14}" fill="none" stroke="${s.m.color}" stroke-width="7" stroke-linecap="round" stroke-dasharray="0.1 14"/>`;
      body += pill(s.x, f2 + 66, s.label, { size: 26, bg: s.m.color, fg: '#FFFFFF', ic: 'ic-rail', h: 52 });
    }
    body += text(srcs[1].x, f2 + 118, '出閘門 → 往高鐵 3 號出入口', { size: 20, fill: C.tra, anchor: 'middle', weight: 700 });
    body += `<circle cx="${esc[0]}" cy="${esc[1] + 20}" r="44" fill="#FFFFFF" stroke="${C.gold}" stroke-width="4"/>` + icon('ic-escalator', esc[0] - 30, esc[1] - 10, 60, C.gold);
    body += text(esc[0] + 62, esc[1] + 30, '下手扶梯', { size: 30, fill: C.wine, weight: 700 });
    body += `<path d="M${esc[0]} ${esc[1] + 66} V${f1y + 60} H${fx + 430}" fill="none" stroke="${C.gold}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#v5-a-walk)"/>`;
    body += `<circle cx="${fx + 130}" cy="${f1y + 62}" r="34" fill="${C.gold}"/>` + text(fx + 130, f1y + 77, '7', { size: 40, fill: '#FFFFFF', weight: 800, anchor: 'middle' });
    body += text(fx + 182, f1y + 60, '7 號出口', { size: 42, fill: C.wine, weight: 700, family: FONT_SERIF });
    body += text(fx + 182, f1y + 96, FACTS.exitNote, { size: 26, fill: C.muted });
    const rows = [
      [MODE.hsr, '出月台，下手扶梯'],
      [MODE.tra, '出台鐵閘門，往高鐵 3 號出入口，再下手扶梯'],
      [MODE.mrt, '搭到終點站，不要在前一站「烏日」下車'],
    ];
    rows.forEach(([m, s], i) => {
      const ry = f1y + 170 + i * 50;
      body += pill(fx + 4, ry - 10, m.name, { size: 24, bg: m.color, fg: '#FFFFFF', anchor: 'start', h: 40 });
      body += text(fx + 92, ry, s, { size: 28, fill: m.key === 'mrt' ? C.pink : C.wine, weight: m.key === 'mrt' ? 700 : 400 });
    });
    y += h + 32;
  }

  // ---- 第 2 步：站區二路 ----
  {
    const VB = [420, 262, 340, 410];
    const mw = 500;
    const s = mw / VB[2];
    const mh = VB[3] * s;
    const h = 150 + mh + 40;
    body += card(y, h, '2', '沿站區二路往北直走');
    const mx = X + 36;
    const my = y + 140;
    defs += mapDefs('v5s2', 1.1);
    body += placeMap('v5s2', mx, my, mw, VB, baseMap('v5s2', { routes: ['walk'], compass: false, lobbyPill: false }), 18).svg;
    const at = (px, py) => [mx + (px - VB[0]) * s, my + (py - VB[1]) * s];
    const marks = [
      [616 + 34, 650, '1'],
      [600 + 34, 480, '2'],
      [600 + 34, 400, '3'],
      [552, 290, '4'],
    ];
    for (const [px, py, n] of marks) {
      const [bx, by] = at(px, py);
      body += badge(bx, by, 22, n, C.wine, '#FFFFFF', { stroke: '#FFFFFF', sw: 4, size: 26 });
    }
    const tx = X + 580;
    const items = [
      ['出 7 號出口', '計程車排班區'],
      ['穿過高鐵三路', '第一個路口，直走'],
      ['穿過高鐵五路', '第二個路口，直走'],
      ['左手邊就是停車場', '飯店停車場'],
    ];
    items.forEach(([t, sub], i) => {
      const iy = my + 50 + i * 120;
      body += badge(tx + 22, iy - 12, 22, String(i + 1), C.wine, '#FFFFFF', { size: 26 });
      body += text(tx + 58, iy, t, { size: 34, fill: C.wine, weight: 700 });
      body += text(tx + 58, iy + 40, sub, { size: 25, fill: C.muted });
    });
    y += h + 32;
  }

  // ---- 第 3 步：停車場到接待大廳 ----
  {
    const VB = [150, 158, 470, 240];
    const mw = CW - 72;
    const mh = (VB[3] * mw) / VB[2];
    const h = 150 + mh + 100;
    body += card(y, h, '3', '穿過停車場，到接待大廳');
    defs += mapDefs('v5s3', 1.1);
    body += placeMap('v5s3', X + 36, y + 140, mw, VB, baseMap('v5s3', { routes: ['walk'], compass: false }), 18).svg;
    body += text(X + 52, y + 140 + mh + 62, '沿著金色路線穿過停車場，走到飯店的接待大廳', { size: 30, fill: C.wine });
    y += h + 32;
  }

  // ---- 第 4 步：上 2F ----
  {
    const h = 250;
    body += card(y, h, '4', '搭電梯上 2F');
    body += `<circle cx="${X + 120}" cy="${y + 172}" r="50" fill="${C.pink}"/>` + icon('ic-elev', X + 90, y + 142, 60, '#FFFFFF');
    body += text(X + 200, y + 200, '2F', { size: 80, fill: C.gold, weight: 700, family: FONT_SERIF });
    body += text(X + 330, y + 196, '東方明珠', { size: 64, fill: C.wine, weight: 700, family: FONT_SERIF, ls: 8 });
    y += h + 56;
  }

  // ---- 公車 ----
  {
    const VB = [96, 196, 450, 276];
    const mw = CW - 72;
    const mh = (VB[3] * mw) / VB[2];
    const h = 150 + mh + 200;
    body += `<rect x="${X}" y="${y}" width="${CW}" height="${h}" rx="30" fill="#FFFFFF" stroke="${C.pink}" stroke-width="3"/>`;
    body += `<circle cx="${X + 76}" cy="${y + 74}" r="36" fill="${C.pink}"/>` + icon('ic-coach', X + 52, y + 50, 48, '#FFFFFF');
    body += text(X + 132, y + 90, '搭公車的賓客', { size: 46, fill: C.pink, weight: 700, family: FONT_SERIF, ls: 2 });
    body += text(X + CW - 40, y + 88, `步行約 ${MODE.bus.min} 分鐘`, { size: 28, fill: C.wine, weight: 700, anchor: 'end' });
    defs += mapDefs('v5bus', 1.1);
    body += placeMap('v5bus', X + 36, y + 140, mw, VB, baseMap('v5bus', { routes: ['bus'], compass: false, lobbyPill: false, nearLabels: true }), 18).svg;
    const lines = ['156 路在「國際會展中心（高鐵五路）」下車', '往高鐵路三段方向，右轉就到飯店', '走進飯店，搭電梯上 2F 東方明珠'];
    lines.forEach((s, i) => {
      const ly = y + 140 + mh + 62 + i * 50;
      body += badge(X + 66, ly - 10, 18, String(i + 1), C.pink, '#FFFFFF', { size: 22 });
      body += text(X + 98, ly, s, { size: 30, fill: C.wine });
    });
    y += h;
  }

  y += 70;
  body += text(W / 2, y, FACTS.source, { size: 20, fill: C.muted, anchor: 'middle' });
  const H = y + 60;
  const frame = `<rect x="16" y="16" width="${W - 32}" height="${H - 32}" fill="none" stroke="${C.frame}" stroke-width="2"/><rect x="24" y="24" width="${W - 48}" height="${H - 48}" fill="none" stroke="${C.frame}" stroke-width="1"/>`;
  defs += mapDefs('v5', 1.4);

  return svgDoc({
    w: W,
    h: H,
    title: '臻愛花園飯店大眾運輸交通資訊（手機步驟圖卡版）',
    desc: '四步驟：一、高鐵、台鐵、捷運都下手扶梯到一樓 7 號出口；二、沿站區二路往北，穿過高鐵三路與高鐵五路；三、穿過飯店停車場到接待大廳；四、搭電梯上 2F 東方明珠。公車 156 路在國際會展中心（高鐵五路）下車，往高鐵路三段方向右轉即到。',
    defs,
    body: frame + body,
  });
}
