/**
 * 婚禮相關的外部連結與待定資料。
 * 三個外部網址（Google 表單、表單編輯回覆、地圖目的地地址）尚未取得正式值，
 * 一律先用占位常數，正式上線前需整批替換，不得自行編造看似真實的網址。
 */
export const WEDDING_LINKS = {
  /** Google 表單填寫連結。目前為占位值，待新人提供正式表單網址後替換。 */
  rsvpFormUrl: 'https://forms.gle/PLACEHOLDER_RSVP_FORM',
  /** Google 表單「編輯回覆」連結。目前為占位值，待表單開啟該選項並提供網址後替換。 */
  rsvpEditUrl: 'https://forms.gle/PLACEHOLDER_RSVP_EDIT',
  /** 宴客地點地址文字，用於組出 Google 地圖導航連結（帶文字地址即可，不需要經緯度）。 */
  venueAddress: '台北市松山區敦化北路二段 158 號',
} as const

/**
 * 由地址文字組出 Google 地圖導航連結。
 * 設計澄清後確認只需帶地址文字即可觸發導航，不需經緯度座標。
 */
export function buildGoogleMapsDirectionUrl(address: string): string {
  const encoded = encodeURIComponent(address)
  return `https://www.google.com/maps/dir/?api=1&destination=${encoded}`
}
