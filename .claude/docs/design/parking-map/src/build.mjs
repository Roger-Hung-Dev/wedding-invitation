// 產生 10 個停車示意圖版本（../vXX.svg）與比稿頁（../index.html）。
// 用法：node build.mjs            → 全部
//       node build.mjs v01 v03    → 只重產指定版本（比稿頁仍列出全部已存在的版本）
import { writeFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const out = join(here, '..');
const ids = Array.from({ length: 10 }, (_, i) => `v${String(i + 1).padStart(2, '0')}`);
const only = process.argv.slice(2);
// 網站採用 V01（S3 交通資訊區），重產時同步覆寫網站那一份，避免改了原稿、網站還是舊圖。
const SITE_VERSION = 'v01';
const siteAsset = join(here, '../../../../..', 'src/assets/images/parking-map.svg');

const metas = [];
for (const id of ids) {
  const file = join(here, `${id}.mjs`);
  if (!existsSync(file)) continue;
  const mod = await import(`./${id}.mjs`);
  metas.push(mod.meta);
  if (only.length && !only.includes(id)) continue;
  const svg = mod.default();
  writeFileSync(join(out, `${id}.svg`), svg, 'utf8');
  console.log(`wrote ${id}.svg`);
  if (id === SITE_VERSION) {
    writeFileSync(siteAsset, svg, 'utf8');
    console.log(`wrote ${siteAsset}`);
  }
}

const cards = metas
  .map(
    (m) => `    <figure class="card">
      <a href="${m.id}.svg" target="_blank"><img src="${m.id}.svg" alt="${m.name}" loading="lazy"></a>
      <figcaption><b>${m.id.toUpperCase()}　${m.name}</b><span>${m.note}</span></figcaption>
    </figure>`,
  )
  .join('\n');

writeFileSync(
  join(out, 'index.html'),
  `<!doctype html>
<html lang="zh-Hant-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>停車示意圖比稿</title>
<style>
  :root { --bg:#FDF2F8; --ink:#831843; --muted:#7A5560; --card:#fff; --line:#F0D9E2; }
  body { margin:0; background:var(--bg); color:var(--ink); font-family:'Noto Sans TC','PingFang TC','Microsoft JhengHei',sans-serif; }
  header { padding:32px 16px 8px; text-align:center; }
  h1 { font-family:'Noto Serif TC',serif; margin:0 0 8px; font-size:28px; }
  header p { margin:0; color:var(--muted); font-size:15px; }
  main { display:grid; grid-template-columns:repeat(auto-fill,minmax(min(100%,520px),1fr)); gap:24px; padding:24px 16px 48px; max-width:1680px; margin:0 auto; }
  .card { margin:0; background:var(--card); border:1px solid var(--line); border-radius:16px; overflow:hidden; display:flex; flex-direction:column; }
  .card a { display:block; background:#faf7f5; }
  .card img { display:block; width:100%; height:auto; max-height:760px; object-fit:contain; }
  figcaption { padding:14px 16px 18px; display:flex; flex-direction:column; gap:6px; border-top:1px solid var(--line); }
  figcaption b { font-size:17px; }
  figcaption span { color:var(--muted); font-size:14px; line-height:1.6; }
</style>
</head>
<body>
<header>
  <h1>停車示意圖　10 版比稿</h1>
  <p>點圖可開原尺寸 SVG。所有版本內容相同，差別在呈現方式。</p>
</header>
<main>
${cards}
</main>
</body>
</html>
`,
  'utf8',
);
console.log('wrote index.html');
