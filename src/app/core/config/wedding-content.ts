/**
 * 喜帖全站文案與示意資料。全站沒有後端，所有畫面上看得到的中文／英文字都集中在這一個檔案，
 * 不會散落在各元件的樣板（.html）裡——要改一句話，只需要來這裡找，不必去讀程式碼。
 *
 * 檔案分兩類：
 * 1. WEDDING_CONTENT：會員資料型的內容（新人姓名、日期、場地），本身已有語意明確的欄位名。
 * 2. 依畫面區塊分組的 XXX_TEXT 常數（HERO_TEXT／GALLERY_TEXT／INFO_TEXT／RSVP_TEXT／FOOTER_TEXT／
 *    MUSIC_PLAYER_TEXT）：純顯示用的標籤、提示語、按鈕文字，依畫面由上到下的區塊順序排列，
 *    每個區塊對應網站上的一個段落，找文字時比對頁面滾動位置即可定位到對應常數。
 *
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

/**
 * S1 主視覺封面區的固定文案（新人姓名、日期見 WEDDING_CONTENT，這裡只放版面上的標籤字）。
 * 倒數計時四格的英文標籤與婚期已過時顯示的致謝句都在畫面最上方、第一屏可見。
 */
export const HERO_TEXT = {
  /** 姓名上方的小字眉標，全大寫、字距展開。 */
  eyebrow: 'WE ARE GETTING MARRIED',
  /** 倒數計時四格下方各自的英文標籤，順序固定為天／時／分／秒。 */
  countdownLabels: {
    days: 'DAYS',
    hours: 'HOURS',
    minutes: 'MINS',
    seconds: 'SECS',
  },
  /** 婚期當天起、四格倒數消失後顯示的一句話。 */
  countdownOverMessage: 'Thank you for being with us',
  /** 畫面最下方「往下滑」提示的文字。 */
  scrollHint: 'SCROLL',
} as const

/**
 * S2 婚紗藝廊區文案。金句與操作提示在手機／桌機顯示不同的斷句或措辭，是設計刻意決定的，
 * 不是同一句話自動換行，兩種版本都要各自維護，不要合併成一句再用程式斷行。
 */
export const GALLERY_TEXT = {
  /** 區塊眉標（小字、金色）。 */
  eyebrow: 'GALLERY',
  /** 區塊主標（花體字）。 */
  title: 'Our Moments',
  quote: {
    /** 桌機顯示一整行。 */
    full: '願我們的故事，從今天起有了共同的名字。',
    /** 手機刻意斷成兩行顯示，順序即畫面順序。 */
    lines: ['願我們的故事，', '從今天起有了共同的名字。'] as readonly string[],
  },
  hint: {
    /** 手機版操作提示：因為手機有左右滑動手勢，文字要提到「滑動」。 */
    mobile: '左右滑動瀏覽・點擊放大',
    /** 桌機版操作提示：桌機三張並排無滑動手勢，只提「點擊放大」。 */
    desktop: '點擊放大檢視',
  },
} as const

/**
 * S3 宴客資訊區文案。地址、場地名稱等實際資料在 WEDDING_CONTENT／WEDDING_LINKS，
 * 這裡只放資訊列的標籤字、按鈕文字與提醒句。
 */
export const INFO_TEXT = {
  eyebrow: 'INFORMATION',
  title: 'Wedding Day',
  /** 卡片內四條資訊列各自的標籤字，順序固定：宴會地點／宴會廳／地址／桌次引導。 */
  rowLabels: {
    venue: '宴會地點',
    hall: '宴會廳',
    address: '地址',
    seating: '桌次引導',
  },
  /** 地圖圖片的無障礙替代文字（螢幕報讀器會唸出來，畫面上不會直接顯示）。 */
  mapImageAlt: '宴會地點位置示意地圖',
  /** 導航按鈕文字。 */
  navButtonLabel: '開啟 Google 地圖導航',
  /** 卡片外、入場相關的提醒句。 */
  reminder: '※ 宴會廳將於開席前 30 分鐘開放入場',
} as const

/**
 * S4 意願調查區文案。說明文第二行嵌著 RSVP 截止日，該日期唯一的來源是
 * WEDDING_CONTENT.rsvpDeadlineDisplay，這裡用 {{deadline}} 佔位字串標記插入位置，
 * 不要把日期字面值再寫死一次，否則以後改期限會漏改這裡。
 */
export const RSVP_TEXT = {
  eyebrow: 'R.S.V.P.',
  title: 'Will You Join Us?',
  /** 說明文兩行，第二行的 {{deadline}} 會被換成 WEDDING_CONTENT.rsvpDeadlineDisplay。 */
  introLines: ['您的出席是我們最珍貴的祝福，', '敬請於 {{deadline}} 前回覆。'] as readonly string[],
  /** 表單會收集的七個欄位預告，畫面上以 chip 呈現，順序即畫面順序。 */
  fieldChips: ['姓名', '出席人數', '素食需求', '兒童椅', '喜餅領取', '聯絡電話', '祝福話語'] as readonly string[],
  /** 主要 CTA 按鈕文字。 */
  ctaLabel: '填寫出席回覆表單',
  /** CTA 按鈕下方的小字註記。 */
  ctaNote: '將另開新視窗前往 Google 表單',
  /** 已回覆賓客可點擊修改回覆的連結文字。 */
  editLinkLabel: '已經填寫過了？點此修改回覆',
} as const

/**
 * S5 結語區文案。內文與版權同樣是手機兩行、桌機同一行顯示（純 CSS 控制斷行，
 * 文字本身沒有分成兩種版本），monogram／婚期見 WEDDING_CONTENT。
 */
export const FOOTER_TEXT = {
  /** 花體主標。 */
  title: 'Thank You',
  /** 致謝內文，手機兩行、桌機同一行顯示（見上方說明）。 */
  bodyLines: ['謝謝每一位陪伴我們走到這裡的人，', '期待與你分享這一天的喜悅。'] as readonly string[],
  copyright: '© 2026 Ethan & Chloe　·　Made with love',
} as const

/**
 * 浮動音樂鈕三種狀態各自的無障礙標籤（螢幕報讀器會唸出來，畫面上不會直接顯示文字）。
 */
export const MUSIC_PLAYER_TEXT = {
  ariaLabelIdle: '播放背景音樂',
  ariaLabelPlaying: '靜音背景音樂',
  ariaLabelMuted: '取消靜音並播放背景音樂',
} as const
