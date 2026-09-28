// 建置前的照片前處理，做兩件事：
//
// 1. 依 src/app/core/config/image-variants.json，把 src/assets 裡的原圖轉成各寬度的 WebP 縮圖，
//    輸出到 .generated/img（angular.json 把它複製成網站的 assets/img）。
// 2. 替 src/assets 裡每一張 jpg 算出內容指紋，寫進 src/app/core/config/photo-versions.generated.json，
//    網頁端把它接在照片網址後面（?v=指紋）。照片內容一變、網址就跟著變，看過網站的手機才會重新下載；
//    沒換的照片網址不變，不會被迫重新下載。
//
// 兩者都不進版控、每次建置重新產生：新人常直接替換 jpg，若要手動更新縮圖或版本號，
// 忘了一次網站就會繼續顯示舊照片。縮圖只在原圖比縮圖新時才重做，本機重跑只處理有變動的檔案。
//
// 原圖比設定的寬度小時不放大，但檔名仍用設定的寬度，網頁端組出的每一個網址都一定有檔案。

import { createHash } from 'node:crypto'
import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs'
import { dirname, join, relative, sep } from 'node:path'
import { fileURLToPath } from 'node:url'
import sharp from 'sharp'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const ASSETS = join(ROOT, 'src', 'assets')
const OUTPUT = join(ROOT, '.generated', 'img')
const CONFIG = join(ROOT, 'src', 'app', 'core', 'config', 'image-variants.json')
const VERSIONS = join(ROOT, 'src', 'app', 'core', 'config', 'photo-versions.generated.json')

// 品質 78：與原圖並排在手機上看不出差別，檔案約為同尺寸 JPEG 的六到八成。
const WEBP_QUALITY = 78

// 指紋取內容雜湊的前 8 碼：全站幾十張照片，8 碼撞在一起的機率可以忽略，網址也不會太長。
const FINGERPRINT_LENGTH = 8

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
const versions = {}

for (const source of listJpgs(ASSETS)) {
  const relativePath = relative(ASSETS, source).split(sep).join('/')
  versions[`assets/${relativePath}`] = createHash('sha1')
    .update(readFileSync(source))
    .digest('hex')
    .slice(0, FINGERPRINT_LENGTH)

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

// 內容沒變就不重寫：ng serve 監看這個檔，每次重寫都會觸發一次重新建置。
const sorted = Object.fromEntries(Object.entries(versions).sort(([a], [b]) => a.localeCompare(b)))
const json = `${JSON.stringify(sorted, null, 2)}\n`
const previous = existsSync(VERSIONS) ? readFileSync(VERSIONS, 'utf8') : ''
if (json !== previous) writeFileSync(VERSIONS, json)

console.log(
  `[image-variants] 縮圖產生 ${made} 張、沿用 ${skipped} 張；照片指紋 ${Object.keys(sorted).length} 張` +
    (json !== previous ? '（已更新）' : '（無變動）'),
)
