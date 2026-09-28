import IMAGE_VARIANTS from './config/image-variants.json'

/**
 * 照片的 WebP 縮圖版本放在 assets/img/ 底下，與原圖同路徑、檔名後面加上寬度：
 * assets/weddingphotos/photo-1.jpg → assets/img/weddingphotos/photo-1-640.webp。
 *
 * 縮圖不進版控，是建置時由 tools/generate-image-variants.mjs 依 image-variants.json 從原圖產生的，
 * 所以替換原圖後縮圖一定跟著更新。這裡與產生腳本讀同一份設定，兩邊的寬度清單不會對不上。
 */
const VARIANT_ROOT = 'assets/img/'
const ASSET_ROOT = 'assets/'

const RULES = Object.entries(IMAGE_VARIANTS as Record<string, number[]>)

function widthsFor(relativePath: string): number[] | null {
  for (const [key, widths] of RULES) {
    const matched = key.endsWith('/') ? relativePath.startsWith(key) : relativePath === key
    if (matched) return widths
  }
  return null
}

/**
 * 由原圖網址組出 WebP 版本的 srcset；沒有設定縮圖的照片回傳 null，只用原圖。
 * 原圖網址上的 ?v= 版本號原樣帶到縮圖上：縮圖同樣沿用固定檔名，換照片時也要靠版本號讓手機重新下載。
 */
export function webpSrcset(url: string): string | null {
  const [path, query] = url.split('?')
  if (!path.startsWith(ASSET_ROOT) || !path.endsWith('.jpg')) return null

  const relative = path.slice(ASSET_ROOT.length)
  const widths = widthsFor(relative)
  if (!widths) return null

  const base = VARIANT_ROOT + relative.slice(0, -'.jpg'.length)
  const suffix = query ? `?${query}` : ''
  return widths.map((width) => `${base}-${width}.webp${suffix} ${width}w`).join(', ')
}
