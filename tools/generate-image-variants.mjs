// 依 src/app/core/config/image-variants.json，把 src/assets 裡的原圖轉成各寬度的 WebP 縮圖，
// 輸出到 .generated/img（angular.json 把它複製成網站的 assets/img）。
//
// 縮圖不進版控、每次建置重新產生：新人常直接替換 jpg，縮圖若要手動更新，
// 忘了一次網站就會繼續顯示舊照片的縮圖。原圖比縮圖新才重做，本機重跑只處理有變動的檔案。
//
// 原圖比設定的寬度小時不放大，但檔名仍用設定的寬度，網頁端組出的每一個網址都一定有檔案。

import { existsSync, mkdirSync, readFileSync, readdirSync, statSync } from 'node:fs'
import { dirname, join, relative, sep } from 'node:path'
import { fileURLToPath } from 'node:url'
import sharp from 'sharp'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const ASSETS = join(ROOT, 'src', 'assets')
const OUTPUT = join(ROOT, '.generated', 'img')
const CONFIG = join(ROOT, 'src', 'app', 'core', 'config', 'image-variants.json')

// 品質 78：與原圖並排在手機上看不出差別，檔案約為同尺寸 JPEG 的六到八成。
const WEBP_QUALITY = 78

const rules = Object.entries(JSON.parse(readFileSync(CONFIG, 'utf8')))

function widthsFor(relativePath) {
  for (const [key, widths] of rules) {
    const matched = key.endsWith('/') ? relativePath.startsWith(key) : relativePath === key
    if (matched) return widths
  }
  return null
}

function listJpgs(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = join(dir, entry.name)
    if (entry.isDirectory()) return listJpgs(full)
    return entry.name.toLowerCase().endsWith('.jpg') ? [full] : []
  })
}

let made = 0
let skipped = 0

for (const source of listJpgs(ASSETS)) {
  const relativePath = relative(ASSETS, source).split(sep).join('/')
  const widths = widthsFor(relativePath)
  if (!widths) continue

  const sourceTime = statSync(source).mtimeMs
  for (const width of widths) {
    const target = join(OUTPUT, relativePath.replace(/\.jpg$/i, `-${width}.webp`))
    if (existsSync(target) && statSync(target).mtimeMs >= sourceTime) {
      skipped++
      continue
    }
    mkdirSync(dirname(target), { recursive: true })
    await sharp(source)
      .rotate()
      .resize({ width, withoutEnlargement: true })
      .webp({ quality: WEBP_QUALITY, effort: 5 })
      .toFile(target)
    made++
  }
}

console.log(`[image-variants] 產生 ${made} 張、沿用 ${skipped} 張 → ${relative(ROOT, OUTPUT)}`)
