/**
 * 婚禮相關的外部連結。
 * 新人未開啟 Google 表單的「提交後可編輯回覆」，故不提供編輯回覆連結，
 * S4 畫面上對應的那一行連結一併移除，不留下點不開的入口。
 */
export const WEDDING_LINKS = {
  /**
   * Google 表單填寫連結（葷食版）。
   * ⚠️ 仍為占位值 —— 新人尚未提供正式表單網址，賓客點擊 CTA 不會開啟任何表單，上線前必須替換。
   */
  rsvpFormUrl: 'https://forms.gle/PLACEHOLDER_RSVP_FORM',
  /**
   * Google 表單填寫連結（素食版，/vegetarian 專用）。
   * ⚠️ 同樣是占位值。兩版用不同表單，回覆才會自然分開統計。
   */
  rsvpFormUrlVegetarian: 'https://forms.gle/PLACEHOLDER_RSVP_FORM_VEG',
  /** 宴客地點地址文字，用於組出 Google 地圖導航連結（帶文字地址即可，不需要經緯度）。 */
  venueAddress: '台中市烏日區高鐵路三段 168 號',
  /**
   * 內嵌地圖的定位字串。名稱與地址一起帶：只帶地址時大頭針旁不會標出飯店名稱，
   * 只帶名稱則怕 Google 對到同名的其他地點。
   */
  venueMapQuery: '臻愛花園飯店 台中市烏日區高鐵路三段168號',
} as const

/**
 * 由地址文字組出 Google 地圖導航連結。
 * 設計澄清後確認只需帶地址文字即可觸發導航，不需經緯度座標。
 */
export function buildGoogleMapsDirectionUrl(address: string): string {
  const encoded = encodeURIComponent(address)
  return `https://www.google.com/maps/dir/?api=1&destination=${encoded}`
}

/**
 * 由定位字串組出可放進 iframe 的 Google 地圖內嵌網址。
 * 走不需 API 金鑰的 output=embed 形式 —— 本站沒有後端可以藏金鑰，也不想為一張地圖綁 Google Cloud 帳單。
 */
export function buildGoogleMapsEmbedUrl(query: string): string {
  const encoded = encodeURIComponent(query)
  return `https://www.google.com/maps?q=${encoded}&z=16&hl=zh-TW&output=embed`
}
