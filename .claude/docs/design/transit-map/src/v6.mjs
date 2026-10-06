// V6 長輩轉傳直式版：1080×1920（LINE／限時動態比例），上半張地圖、下半四列大字，存成圖片就能直接轉傳。
import { C, FACTS, MODES, ICONS, EXTRA_ICONS, FONT_SERIF, FONT_DISPLAY, text, icon, mapDefs, baseMap, placeMap, svgDoc, ornament } from './tlib.mjs';

export const meta = {
  id: 'v6',
  name: '長輩轉傳直式版',
  note: '1080×1920 直式（LINE／限時動態比例）。上半張地圖，下半四列大字，一列一種交通方式。存成圖片就能直接傳給長輩。',
};

const LINES = {
  hsr: '7 號出口出站，沿站區二路往北直走',
  tra: '出閘門往高鐵 3 號口，再到 7 號出口',
  mrt: '坐到終點站，不要在「烏日」下車',
  bus: '156 路國際會展中心站下車，右轉就到',
};

export default function build() {
  const p = 'v6';
  const W = 1080;
  const H = 1920;
  let body = `<rect x="16" y="16" width="${W - 32}" height="${H - 32}" fill="none" stroke="${C.frame}" stroke-width="2"/><rect x="24" y="24" width="${W - 48}" height="${H - 48}" fill="none" stroke="${C.frame}" stroke-width="1"/>`;
  body += text(W / 2, 96, 'HOW TO GET THERE', { size: 28, fill: C.gold, anchor: 'middle', family: FONT_DISPLAY, ls: 10 });
  body += text(W / 2, 186, '搭車來會場', { size: 80, fill: C.wine, anchor: 'middle', family: FONT_SERIF, weight: 700, ls: 10 });
  body += ornament(W / 2, 226, 180, C.frame);
  body += text(W / 2, 278, `${FACTS.hotel}・2F 東方明珠`, { size: 36, fill: C.muted, anchor: 'middle', family: FONT_SERIF });

  const map = placeMap(p, 44, 316, W - 88, [150, 160, 720, 570], baseMap(p, { indoor: ['tra', 'mrt'], labelScale: 1.15 }), 24);
  body += map.svg;

  let y = 316 + map.h + 34;
  const rowH = 140;
  MODES.forEach((m, i) => {
    const ry = y + i * rowH;
    if (i > 0) body += `<line x1="70" y1="${ry - 14}" x2="${W - 70}" y2="${ry - 14}" stroke="${C.soft}" stroke-width="2"/>`;
    body += `<circle cx="104" cy="${ry + 46}" r="46" fill="${m.color}"/>` + icon(m.ic, 76, ry + 18, 56, '#FFFFFF');
    body += text(176, ry + 62, m.name, { size: 56, fill: m.color, weight: 700, family: FONT_SERIF, ls: 4 });
    body += text(W - 70, ry + 62, `步行 ${m.min} 分`, { size: 46, fill: C.wine, weight: 700, anchor: 'end' });
    body += text(176, ry + 116, LINES[m.key], { size: 36, fill: m.key === 'mrt' ? C.pink : C.muted, weight: m.key === 'mrt' ? 700 : 400 });
  });

  y += rowH * 4 + 10;
  body += `<rect x="60" y="${y}" width="${W - 120}" height="84" rx="42" fill="${C.pink}"/>`;
  body += icon('ic-elev', 104, y + 18, 48, '#FFFFFF');
  body += text(W / 2 + 26, y + 56, '到飯店後：接待大廳搭電梯上 2F', { size: 38, fill: '#FFFFFF', weight: 700, anchor: 'middle' });
  body += text(W / 2, H - 46, FACTS.source, { size: 20, fill: C.muted, anchor: 'middle' });

  return svgDoc({
    w: W,
    h: H,
    title: '臻愛花園飯店大眾運輸交通資訊（長輩轉傳直式版）',
    desc: '直式圖卡：上方周邊地圖，下方四列分別是高鐵、台鐵、捷運、公車的走法與步行時間。',
    defs: ICONS + EXTRA_ICONS + mapDefs(p, 1.3),
    body,
  });
}
