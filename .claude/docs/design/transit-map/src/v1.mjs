// V1 喜帖雅緻總覽版：與停車圖 V01 同一套版面，上方一張總覽地圖，下方四張交通方式小卡。
import { C, FACTS, MODES, ICONS, EXTRA_ICONS, MAP, FONT_SERIF, text, icon, pill, mapDefs, baseMap, placeMap, header, svgDoc } from './tlib.mjs';

export const meta = {
  id: 'v1',
  name: '喜帖雅緻總覽版',
  note: '和現在的停車圖同一套版面：燙金框、酒紅標題、同樣的四欄說明。一張地圖看完四種走法，最適合直接放在停車圖旁邊。',
};

const CARD_LINES = {
  hsr: ['出月台、下手扶梯，', '從一樓 7 號出口出站，', '沿站區二路往北直走，', '過高鐵三路、高鐵五路，', '就到飯店停車場'],
  tra: ['新烏日站出閘門，', '往高鐵 3 號出入口，', '下手扶梯到 7 號出口，', '之後和高鐵走法相同'],
  mrt: ['綠線搭到終點站', '「高鐵臺中站」，', '下手扶梯到 7 號出口，', '之後和高鐵走法相同'],
  bus: ['156 路在「國際會展', '中心（高鐵五路）」', '下車，往高鐵路三段', '方向右轉就到'],
};

export default function build() {
  const p = 'v1';
  const W = 1200;
  const H = 1640;
  let body = '';
  const hd = header(W, H, 'TRANSIT GUIDE', '大眾運輸交通資訊', `${FACTS.hotel}｜${FACTS.addr}`);
  body += hd.svg;

  const map = placeMap(p, 50, 236, 1100, [0, 0, MAP.w, MAP.h], baseMap(p, { indoor: ['hsr', 'tra', 'mrt'] }));
  body += map.svg;

  // 圖例（疊在地圖右上角的空白處）
  const lx = 50 + 1100 * 0.655;
  const ly = 236 + 22;
  body += `<rect x="${lx}" y="${ly}" width="352" height="134" rx="14" fill="#FFFFFF" opacity="0.94"/>`;
  const leg = (y, color, label, dash) =>
    `<line x1="${lx + 20}" y1="${y - 7}" x2="${lx + 62}" y2="${y - 7}" stroke="${color}" stroke-width="${dash ? 6 : 9}" stroke-linecap="round"${dash ? ' stroke-dasharray="0.1 11"' : ''}/>` +
    text(lx + 76, y, label, { size: 19, fill: C.wine, weight: 700 });
  body += leg(ly + 38, C.gold, '車站走過來（高鐵・台鐵・捷運）');
  body += leg(ly + 76, C.pink, '公車站走過來');
  body += leg(ly + 114, C.muted, '站內走到 7 號出口', true);

  let y = 236 + map.h + 52;
  body += pill(W / 2, y, '高鐵、台鐵、捷運都從一樓「7 號出口」出站，之後走同一條路', {
    size: 22,
    bg: '#FDF2F8',
    fg: C.wine,
    stroke: C.frame,
    sw: 2,
    h: 50,
  });

  // 四張小卡
  y += 52;
  const cw = 260;
  const gap = (1100 - cw * 4) / 3;
  MODES.forEach((m, i) => {
    const x = 50 + i * (cw + gap);
    const cy = y + 34;
    body += `<circle cx="${x + 30}" cy="${cy}" r="28" fill="${m.color}"/>` + icon(m.ic, x + 13, cy - 17, 34, '#FFFFFF');
    body += text(x + 72, cy + 2, m.name, { size: 32, fill: C.wine, weight: 700, family: FONT_SERIF, ls: 2 });
    body += text(x + 72, cy + 30, `步行約 ${m.min} 分鐘`, { size: 19, fill: C.gold, weight: 700 });
    CARD_LINES[m.key].forEach((ln, j) => {
      body += text(x + 4, cy + 80 + j * 32, ln, { size: 20, fill: C.muted });
    });
    if (m.warn) body += text(x + 4, cy + 80 + 4 * 32 + 4, '※ 不要在前一站「烏日」下車', { size: 17, fill: C.pink, weight: 700 });
  });

  // 最後一段
  y += 310;
  body += `<line x1="80" y1="${y}" x2="${W - 80}" y2="${y}" stroke="${C.soft}" stroke-width="2"/>`;
  body += `<circle cx="${W / 2 - 250}" cy="${y + 52}" r="24" fill="${C.pink}"/>` + icon('ic-elev', W / 2 - 266, y + 36, 32, '#FFFFFF');
  body += text(W / 2 - 212, y + 62, `抵達後：${FACTS.finalStep}`, { size: 26, fill: C.wine, weight: 700, family: FONT_SERIF });
  body += text(W / 2, H - 52, FACTS.source, { size: 16, fill: C.muted, anchor: 'middle' });

  return svgDoc({
    w: W,
    h: H,
    title: '臻愛花園飯店大眾運輸交通資訊（喜帖雅緻總覽版）',
    desc: '北方朝上的周邊地圖。高鐵、台鐵、捷運都從高鐵台中站一樓 7 號出口出站，沿站區二路往北，穿過高鐵三路與高鐵五路到飯店停車場，再到接待大廳搭電梯上 2F 東方明珠。公車 156 路在國際會展中心（高鐵五路）下車，往高鐵路三段方向右轉即到。',
    defs: ICONS + EXTRA_ICONS + mapDefs(p),
    body,
  });
}
