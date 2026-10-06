// V2 路線圖匯流版：把高鐵／台鐵／捷運畫成三條路線，在 7 號出口匯成一條三色緞帶，
// 沿途的路口當成「站」，公車線在接待大廳併入，終點是 2F 東方明珠。下方附對照地圖。
import { C, FACTS, MODE, ICONS, EXTRA_ICONS, FONT_SERIF, text, icon, mapDefs, baseMap, placeMap, header, svgDoc, pSign } from './tlib.mjs';

export const meta = {
  id: 'v2',
  name: '路線圖匯流版',
  note: '像捷運路線圖：三條車站線在「7 號出口」匯成一條緞帶，沿途路口當成站名，一路往下讀到 2F 東方明珠。下方附對照地圖。',
};

export default function build() {
  const p = 'v2';
  const W = 1200;
  let body = '';
  const H = 1450 + 22 + 733 + 96;
  const hd = header(W, H, 'ROUTE MAP', '搭車來的路線圖', `${FACTS.hotel}｜${FACTS.addr}`);
  body += hd.svg;

  const SW = 13; // 線寬
  const rows = [
    { m: MODE.hsr, y: 330, x: 612, sub: '出月台，下手扶梯到一樓' },
    { m: MODE.tra, y: 450, x: 600, sub: '出閘門，往高鐵 3 號出入口，下手扶梯' },
    { m: MODE.mrt, y: 570, x: 588, sub: '綠線終點站，不要在前一站「烏日」下車' },
  ];
  const yMerge = 690;
  const yLobby = 1215;
  const yEnd = 1340;
  const r = 40;

  // 三條來源線
  for (const row of rows) {
    const { m, y, x } = row;
    body += `<path d="M96 ${y} H${x - r} A${r} ${r} 0 0 1 ${x} ${y + r} V${yEnd}" fill="none" stroke="${m.color}" stroke-width="${SW}"/>`;
    body += `<circle cx="96" cy="${y}" r="15" fill="#FFFFFF" stroke="${m.color}" stroke-width="7"/>`;
    body += text(80, y - 30, m.name, { size: 32, fill: m.color, weight: 700, family: FONT_SERIF, ls: 2 });
    body += text(160, y - 30, m.station, { size: 24, fill: C.wine, weight: 700 });
    body += text(132, y + 40, row.sub, { size: 20, fill: C.muted });
    body += text(1120, y + 9, `約 ${m.min} 分鐘`, { size: 26, fill: m.color, weight: 700, anchor: 'end' });
    body += `<line x1="646" y1="${y}" x2="${1120 - 132}" y2="${y}" stroke="${m.color}" stroke-width="2" stroke-dasharray="2 8" stroke-linecap="round" opacity="0.6"/>`;
  }
  body += text(1120, 278, '步行時間', { size: 18, fill: C.muted, anchor: 'end', ls: 2 });

  // 公車線（在接待大廳併入，之後多一條粉色）
  const bus = MODE.bus;
  body += `<path d="M96 ${yLobby} H580" fill="none" stroke="${bus.color}" stroke-width="${SW}"/>`;
  body += `<path d="M624 ${yLobby} V${yEnd}" fill="none" stroke="${bus.color}" stroke-width="${SW}"/>`;
  body += `<circle cx="96" cy="${yLobby}" r="15" fill="#FFFFFF" stroke="${bus.color}" stroke-width="7"/>`;
  body += text(80, yLobby - 30, bus.name, { size: 32, fill: bus.color, weight: 700, family: FONT_SERIF, ls: 2 });
  body += text(160, yLobby - 30, '156 路「國際會展中心」', { size: 24, fill: C.wine, weight: 700 });
  body += text(132, yLobby + 42, '高鐵五路上下車，往高鐵路三段右轉', { size: 20, fill: C.muted });
  body += text(132, yLobby + 70, `步行約 ${bus.min} 分鐘`, { size: 20, fill: bus.color, weight: 700 });

  // 站點
  const stop = (y, h = 24, x0 = 574, x1 = 626) =>
    `<rect x="${x0}" y="${y - h / 2}" width="${x1 - x0}" height="${h}" rx="${h / 2}" fill="#FFFFFF" stroke="${C.wine}" stroke-width="4"/>`;
  const label = (y, title, sub, o = {}) =>
    text(668, y + 4, title, { size: o.size || 28, fill: C.wine, weight: 700, family: o.serif ? FONT_SERIF : undefined }) +
    (sub ? text(668, y + 36, sub, { size: 20, fill: C.muted }) : '');

  body += stop(yMerge, 32);
  body += label(yMerge, '1F　7 號出口', '計程車排班區・三種車都從這裡出站', { size: 32, serif: true });

  const stops = [
    { y: 800, t: '沿站區二路往北直走', s: '一路直走，不用轉彎' },
    { y: 900, t: '穿過高鐵三路', s: '第一個路口，直走過馬路', zebra: true },
    { y: 1000, t: '穿過高鐵五路', s: '第二個路口，過了就是飯店', zebra: true },
    { y: 1100, t: '走進飯店停車場', s: '停車場在左手邊，往建物走', park: true },
  ];
  for (const st of stops) {
    body += stop(st.y);
    body += label(st.y, st.t, st.s);
    if (st.zebra) {
      let z = '';
      for (let i = 0; i < 5; i++) z += `<rect x="${1040 + i * 12}" y="${st.y - 18}" width="7" height="36" rx="2" fill="${C.border}"/>`;
      body += z;
    }
    if (st.park) body += pSign(1066, st.y + 2, 20, C.wine, '#FFFFFF');
  }
  body += stop(yLobby, 32, 574, 638);
  body += label(yLobby, '接待大廳', '公車來的賓客也走到這裡', { size: 32, serif: true });

  // 終點
  body += `<circle cx="606" cy="${yEnd}" r="36" fill="#FFFFFF" stroke="${C.gold}" stroke-width="9"/><circle cx="606" cy="${yEnd}" r="15" fill="${C.gold}"/>`;
  body += icon('ic-elev', 668, yEnd - 24, 44, C.pink);
  body += text(724, yEnd + 12, '搭電梯上 2F　東方明珠', { size: 36, fill: C.wine, weight: 700, family: FONT_SERIF, ls: 2 });

  // 左側步行時間括號
  body += `<path d="M548 ${yMerge + 12} h-14 V${1100} h14" fill="none" stroke="${C.frame}" stroke-width="3"/>`;
  body += text(512, 885, '出站後', { size: 22, fill: C.muted, anchor: 'end' });
  body += text(512, 921, '同一條路', { size: 26, fill: C.gold, anchor: 'end', weight: 700 });

  // 對照地圖
  const my = 1450;
  body += `<line x1="80" y1="${my - 46}" x2="${W - 80}" y2="${my - 46}" stroke="${C.soft}" stroke-width="2"/>`;
  body += text(W / 2, my - 4, 'ON THE MAP　對照地圖', { size: 20, fill: C.gold, anchor: 'middle', family: "'Cormorant Garamond','Noto Serif TC',serif", ls: 5 });
  const map = placeMap(p, 50, my + 22, 1100, [100, 150, 900, 600], baseMap(p, { indoor: ['hsr', 'tra', 'mrt'], compass: true }));
  body += map.svg;
  body += text(W / 2, H - 52, FACTS.source, { size: 16, fill: C.muted, anchor: 'middle' });

  return svgDoc({
    w: W,
    h: H,
    title: '臻愛花園飯店大眾運輸路線圖（路線圖匯流版）',
    desc: '高鐵、台鐵、捷運三條路線在高鐵台中站一樓 7 號出口匯合，沿站區二路往北，穿過高鐵三路、高鐵五路，進飯店停車場到接待大廳；公車 156 路由國際會展中心站併入；終點搭電梯上 2F 東方明珠。',
    defs: ICONS + EXTRA_ICONS + mapDefs(p),
    body,
  });
}
