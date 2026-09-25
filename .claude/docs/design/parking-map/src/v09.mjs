// V09 手繪插畫：水彩色塊＋抖動線條＋手寫註解，像新人自己畫給朋友的小地圖。
import { FACTS, FONT_HAND, ICONS, G, ANCHOR, svgDoc, text, icon, polyOf, pathOf, carRoute, motoRoute, uturnPath, yAt, road, roadAngle, MAP_W, MAP_H, LOT_Y } from './lib.mjs';

export const meta = {
  id: 'v09',
  name: '手繪插畫版',
  note: '水彩色塊加抖動線條與手寫註解，像新人親手畫給朋友的小地圖，最有人味。',
};

export default function build() {
  const W = 1200;
  const H = 1080;
  const k = 1100 / MAP_W;
  const C = { paper: '#FBF5EA', ink: '#4A3728', red: '#D1495B', orange: '#E07A1F', blue: '#7FB2DE', green: '#A9CF8F', pink: '#F3B3C3', yellow: '#F6D68A', sand: '#EADCC3' };
  const HF = FONT_HAND;
  const inv = (px) => px / k;

  // 水彩色塊（粗糙濾鏡）＋墨線（另一組粗糙濾鏡，錯開一點點）
  const wash = (pts, fill, op = 0.75) => `<polygon points="${polyOf(pts)}" fill="${fill}" opacity="${op}" filter="url(#v09-wash)"/>`;
  const inkline = (pts, w = 3) => `<polygon points="${polyOf(pts)}" fill="none" stroke="${C.ink}" stroke-width="${w}" stroke-linejoin="round" filter="url(#v09-rough)"/>`;
  const rect = (x0, y0, x1, y1) => [
    [x0, y0],
    [x1, y0],
    [x1, y1],
    [x0, y1],
  ];

  let m = '';
  // 道路
  m += wash(G.rampPoly, C.sand, 0.55) + inkline(G.rampPoly, 2);
  m += wash(G.road5, C.sand, 0.7) + inkline(G.road5, 2.5);
  m += wash(G.roadPoly, C.sand, 0.8) + inkline(G.roadPoly, 3);
  m += `<path d="${pathOf(road)}" fill="none" stroke="${C.ink}" stroke-width="2.5" stroke-dasharray="20 18" opacity="0.5" filter="url(#v09-rough)"/>`;
  // 停車場
  m += wash(G.lot, C.blue, 0.7) + wash(G.apron, C.blue, 0.7) + inkline(G.lot, 3.5);
  // 停車格（手繪短線）
  let stalls = '';
  for (let x = 290; x < 1060; x += 52) stalls += `<path d="M${x} 66 l2 56 M${x + 1} 160 l-2 56"/>`;
  m += `<g stroke="${C.ink}" stroke-width="2.4" opacity="0.4" stroke-linecap="round" filter="url(#v09-rough)">${stalls}</g>`;
  // 綠地、步道、機車道
  m += wash(G.garden, C.green, 0.7) + inkline(G.garden, 2);
  m += wash(G.walkway, '#E9C9A0', 0.6);
  m += wash(G.moto, '#F0B27A', 0.8) + inkline(G.moto, 2.5);
  // 樹
  let trees = '';
  for (let x = 560; x <= 880; x += 64) {
    const y = yAt(road, x) - 96;
    trees += `<circle cx="${x}" cy="${y}" r="17" fill="#7DB36A" opacity="0.8"/><circle cx="${x}" cy="${y}" r="17" fill="none" stroke="${C.ink}" stroke-width="2"/>`;
  }
  m += `<g filter="url(#v09-rough)">${trees}</g>`;
  // 建物
  const B = G.bld;
  m += wash(rect(B.corridor[0], G.bldY0, B.corridor[1], G.bldY1), C.pink, 0.85);
  m += wash(rect(B.lobby[0], G.bldY0, B.lobby[1], G.bldY1), C.red, 0.85);
  m += wash(rect(B.plan[0], G.bldY0, B.plan[1], G.bldY1), C.yellow, 0.85);
  m += inkline(rect(B.corridor[0], G.bldY0, B.plan[1], G.bldY1), 3);
  m += inkline(rect(B.lobby[0], G.bldY0, B.elev[1], G.bldY1), 3);
  m += `<circle cx="${G.chapel.cx}" cy="${G.chapel.cy}" r="${G.chapel.r}" fill="#F7E7A1" filter="url(#v09-wash)"/><circle cx="${G.chapel.cx}" cy="${G.chapel.cy}" r="${G.chapel.r}" fill="none" stroke="${C.ink}" stroke-width="2.5" filter="url(#v09-rough)"/>`;

  // 手寫字：建物、路名
  const hand = (x, y, s, size, o = {}) => text(x, y, s, { size, fill: C.ink, family: HF, ...o });
  m += hand((B.corridor[0] + B.corridor[1]) / 2, 358, '幸福長廊', 30, { anchor: 'middle' });
  m += hand((B.lobby[0] + B.lobby[1]) / 2, 340, '接待', 28, { anchor: 'middle', fill: '#FFFFFF', weight: 700 });
  m += hand((B.lobby[0] + B.lobby[1]) / 2, 374, '大廳', 28, { anchor: 'middle', fill: '#FFFFFF', weight: 700 });
  m += hand((B.plan[0] + B.plan[1]) / 2, 358, '婚禮企劃中心', 26, { anchor: 'middle' });
  m += hand(G.chapel.cx, G.chapel.cy + 9, '教堂', 24, { anchor: 'middle' });
  m += hand(700, yAt(road, 700) + 12, '高 鐵 路 三 段', 34, { anchor: 'middle', rotate: roadAngle(700) });
  m += hand(1236, 150, '高', 30, { anchor: 'middle' }) + hand(1236, 184, '鐵', 30, { anchor: 'middle' }) + hand(1236, 218, '五', 30, { anchor: 'middle' }) + hand(1236, 252, '路', 30, { anchor: 'middle' });
  m += hand(240, yAt(road, 240) + 138, '台74 匝道', 24, { anchor: 'middle', rotate: 28, opacity: 0.8 });

  // 停車場大字
  m += hand(470, 186, 'P', 150, { weight: 700, fill: '#2F6FB0' });
  m += hand(590, 150, '停車場在這！', inv(40), { weight: 700 });
  m += hand(594, 206, '汽機車位約 1000 個・遊覽車也可以', inv(20));

  // 手繪箭頭路線
  const handArrow = (d, color, w = 8, dash = null) =>
    `<path d="${d}" fill="none" stroke="${color}" stroke-width="${w}" stroke-linecap="round" stroke-linejoin="round"${dash ? ` stroke-dasharray="${dash}"` : ''} marker-end="url(#v09-head-${color.slice(1)})" filter="url(#v09-rough)"/>`;
  m += handArrow(pathOf(carRoute()), C.red, 9);
  m += handArrow(pathOf(motoRoute()), C.orange, 9);
  m += handArrow(uturnPath(1030), '#8C6D56', 5, '14 12');
  m += handArrow(
    pathOf([
      [ANCHOR.lobby[0] - 60, 250],
      [ANCHOR.lobby[0] - 10, 268],
      [ANCHOR.lobby[0], LOT_Y - 8],
    ]),
    C.ink,
    4,
    '3 10',
  );

  // 手寫註解（帶小彎箭頭）
  const note = (x, y, lines, color, size = inv(24)) => lines.map((l, i) => hand(x, y + i * size * 1.25, l, size, { fill: color, weight: 700 })).join('');
  const curl = (d, color) => `<path d="${d}" fill="none" stroke="${color}" stroke-width="3.5" stroke-linecap="round" marker-end="url(#v09-head-${color.slice(1)})" filter="url(#v09-rough)"/>`;
  m += note(24, 70, ['汽車從', '這裡進來！'], C.red);
  m += curl('M92 150 C 110 210, 130 250, 162 292', C.red);
  m += note(1060, 450, ['機車', '走這邊～'], C.orange);
  m += curl('M1070 540 C 1060 580, 1040 600, 1012 606', C.orange);
  m += note(400, 440, ['停好車走進大廳，', `搭電梯上 ${FACTS.hall} ♡`], C.ink, inv(22));
  m += hand(1196, 812, '南下的朋友：高鐵五路口迴轉', inv(17), { anchor: 'end', fill: '#8C6D56', weight: 700 });

  // 小插畫：車、機車、愛心
  m += icon('ic-car', 36, 200, 70, C.red);
  m += icon('ic-moto', 1110, 600, 60, C.orange);
  const heart = (x, y, s, c) => `<path d="M${x} ${y + s * 0.35} c${-s * 0.5} ${-s * 0.35} ${-s * 0.62} ${-s * 0.62} ${-s * 0.62} ${-s * 0.82} a${s * 0.31} ${s * 0.31} 0 0 1 ${s * 0.62} ${-s * 0.1} a${s * 0.31} ${s * 0.31} 0 0 1 ${s * 0.62} ${s * 0.1} c0 ${s * 0.2} ${-s * 0.12} ${s * 0.47} ${-s * 0.62} ${s * 0.82}z" fill="${c}" filter="url(#v09-rough)"/>`;
  m += heart(700, 250, 34, C.red) + heart(740, 230, 22, C.pink);

  const mapY = 190;
  const mapH = MAP_H * k;
  let body = '';
  body += hand(W / 2, 96, '來喝喜酒的停車小地圖', 58, { anchor: 'middle', weight: 700 });
  body += `<path d="M330 122 q 60 -12 120 0 t 120 0 t 120 0 t 120 0" fill="none" stroke="${C.red}" stroke-width="4" stroke-linecap="round" filter="url(#v09-rough)"/>`;
  body += hand(W / 2, 166, `${FACTS.hotel}・${FACTS.addr}`, 26, { anchor: 'middle', opacity: 0.8 });
  body += `<clipPath id="v09-clip"><rect x="50" y="${mapY}" width="1100" height="${mapH}" rx="16"/></clipPath>`;
  body += `<g clip-path="url(#v09-clip)"><g transform="translate(50 ${mapY}) scale(${k})">${m}</g></g>`;
  body += `<rect x="46" y="${mapY - 4}" width="1108" height="${mapH + 8}" rx="18" fill="none" stroke="${C.ink}" stroke-width="3" filter="url(#v09-rough)"/>`;
  const fy = mapY + mapH + 64;
  body += hand(80, fy, '① 汽車：高鐵路三段往北開，靠台74 匝道那一頭右轉', 28, { fill: C.red, weight: 700 });
  body += hand(80, fy + 44, '② 機車：靠高鐵五路那一頭右轉，沿機車道進去', 28, { fill: C.orange, weight: 700 });
  body += hand(80, fy + 88, '③ 停好車 → 接待大廳 → 電梯上 2F 東方明珠', 28, { weight: 700 });
  body += text(W - 50, H - 22, FACTS.source, { size: 15, fill: '#9C8672', anchor: 'end' });

  const heads = [C.red, C.orange, '#8C6D56', C.ink]
    .map((c) => `<marker id="v09-head-${c.slice(1)}" viewBox="0 0 12 12" refX="7" refY="6" markerWidth="4" markerHeight="4" orient="auto-start-reverse" overflow="visible"><path d="M1 1 L9 6 L1 11" fill="none" stroke="${c}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></marker>`)
    .join('');

  return svgDoc({
    w: W,
    h: H,
    title: '臻愛花園飯店停車資訊（手繪插畫版）',
    desc: '手繪風停車小地圖：藍色水彩區塊是停車場，汽車由左端入口進入，機車由右端靠高鐵五路的入口進入，停好車走進接待大廳搭電梯上 2F 東方明珠。',
    defs:
      ICONS +
      heads +
      `<filter id="v09-rough" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="2" seed="3" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="5" xChannelSelector="R" yChannelSelector="G"/></filter>` +
      `<filter id="v09-wash" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency="0.018" numOctaves="3" seed="8" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="14" xChannelSelector="R" yChannelSelector="G"/></filter>` +
      `<filter id="v09-paper"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="5"/><feColorMatrix values="0 0 0 0 0.45  0 0 0 0 0.36  0 0 0 0 0.25  0 0 0 0.07 0"/></filter>`,
    body: `<rect width="${W}" height="${H}" filter="url(#v09-paper)"/>` + body,
    bg: C.paper,
  });
}
