/**
 * 喜帖靜態文案與示意資料。全站沒有後端，內容一律寫死在此。
 * 姓名、日期、場地皆為設計階段標註的示意值，正式資料到位後於此檔一次替換即可。
 */
export const WEDDING_CONTENT = {
  brideGroomEn: 'Ethan & Chloe',
  brideGroomZh: '陳彥廷　✕　林思妤',
  /** 婚期（ISO 日期，不含時間）。 */
  weddingDate: '2026-11-14',
  weddingDateDisplay: '2026 . 11 . 14　SATURDAY',
  /** 不含星期的純日期顯示，S3 宴客資訊區日期大字專用（S1 Hero 才帶 SATURDAY）。 */
  weddingDateOnlyDisplay: '2026 . 11 . 14',
  lunarDateDisplay: '星期六　·　農曆十月初五',
  venueName: '台北文華東方酒店',
  venueHall: '3F　文華廳',
  seatingGuide: '入口處設有座位表，男方親友請至 A 區、女方親友請至 B 區',
  monogram: 'E　&　C',
  rsvpDeadlineDisplay: '2026 / 10 / 15',
} as const

/**
 * 倒數計時目標時間。婚期只定到日期，時分未定，先取當天午宴開席時間 12:00 為暫定值。
 * 正式時間確認後只需改這裡的字面時分。
 */
export const WEDDING_COUNTDOWN_TARGET_ISO = '2026-11-14T12:00:00+08:00'

export interface WeddingSession {
  readonly id: 'lunch' | 'dinner'
  readonly label: string
  readonly timeDisplay: string
}

export const WEDDING_SESSIONS: readonly WeddingSession[] = [
  { id: 'lunch', label: '午宴', timeDisplay: '12:00' },
  { id: 'dinner', label: '晚宴', timeDisplay: '18:00' },
]

export interface GalleryPhoto {
  readonly id: string
  readonly url: string
  readonly alt: string
}

/**
 * 婚紗照。目前沿用 Unsplash 示意圖，張數依設計初稿假設為 5 張。
 */
export const GALLERY_PHOTOS: readonly GalleryPhoto[] = [
  {
    id: 'photo-1',
    url: 'https://images.unsplash.com/photo-1465495976277-4387d4b0b4c6?auto=format&fit=crop&w=800&q=80',
    alt: '新人牽手特寫，底片色調',
  },
  {
    id: 'photo-2',
    url: 'https://images.unsplash.com/photo-1519225421980-715cb0215aed?auto=format&fit=crop&w=800&q=80',
    alt: '婚紗細節與粉色花束',
  },
  {
    id: 'photo-3',
    url: 'https://images.unsplash.com/photo-1606216794074-735e91aa2c92?auto=format&fit=crop&w=800&q=80',
    alt: '新人於金色夕陽下漫步的背影',
  },
  {
    id: 'photo-4',
    url: 'https://images.unsplash.com/photo-1522673607200-164d1b6ce486?auto=format&fit=crop&w=800&q=80',
    alt: '婚禮儀式現場',
  },
  {
    id: 'photo-5',
    url: 'https://images.unsplash.com/photo-1544078751-58fee2d8a03b?auto=format&fit=crop&w=800&q=80',
    alt: '新娘微笑肖像',
  },
]

/** Hero 滿版底圖。是 LCP 元素，於 index.html 另外 preload。 */
export const HERO_IMAGE_URL =
  'https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=1200&q=80'

export const HERO_IMAGE_DESKTOP_URL =
  'https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=2400&q=80'

/** S3 地圖預覽圖，沿用設計稿上手機版與桌機版節點各自的 Unsplash 圖檔。 */
export const MAP_PREVIEW_IMAGE_URL =
  'https://images.unsplash.com/photo-1645708313906-c4e2cd0b4daa?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080'

export const MAP_PREVIEW_IMAGE_DESKTOP_URL =
  'https://images.unsplash.com/photo-1736117703382-8ed6a338c3b9?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080'
