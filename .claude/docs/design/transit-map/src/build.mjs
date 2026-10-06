// 產生所有版本的 SVG（寫到上一層資料夾），並可輸出 png 預覽。
// 用法：node build.mjs [png 輸出資料夾]
import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const outDir = join(here, '..');
const pngDir = process.argv[2];
const ids = (process.env.ONLY || 'v1,v2,v4,v5,v6').split(',');
// 網站採用 V1（S3 交通資訊區，停車圖下方），重產時同步覆寫網站那一份，避免改了原稿、網站還是舊圖。
const SITE_VERSION = 'v1';
const siteAsset = join(here, '../../../../..', 'src/assets/images/transit-map.svg');

for (const id of ids) {
  const mod = await import(`./${id}.mjs`);
  const svg = mod.default();
  writeFileSync(join(outDir, `${id}.svg`), svg);
  console.log(`${id}.svg  ${(svg.length / 1024).toFixed(1)} KB`);
  if (id === SITE_VERSION) {
    writeFileSync(siteAsset, svg);
    console.log(`wrote ${siteAsset}`);
  }
  if (pngDir) {
    mkdirSync(pngDir, { recursive: true });
    const { default: sharp } = await import('sharp');
    await sharp(Buffer.from(svg)).resize(1000).png().toFile(join(pngDir, `${id}.png`));
  }
}
