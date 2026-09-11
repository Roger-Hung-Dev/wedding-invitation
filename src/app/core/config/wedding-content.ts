/**
 * 喜帖全站文案與示意資料。全站沒有後端，所有畫面上看得到的中文／英文字都集中在這一個檔案，
 * 不會散落在各元件的樣板（.html）裡——要改一句話，只需要來這裡找，不必去讀程式碼。
 *
 * 檔案分兩類：
 * 1. WEDDING_CONTENT：會員資料型的內容（新人姓名、日期、場地），本身已有語意明確的欄位名。
 * 2. 依畫面區塊分組的 XXX_TEXT 常數（HERO_TEXT／ABOUT_TEXT／STORY_TEXT／GALLERY_TEXT／INFO_TEXT／
 *    RSVP_TEXT／FOOTER_TEXT／MUSIC_PLAYER_TEXT）：純顯示用的標籤、提示語、按鈕文字，依畫面由上到下的區塊順序排列，
 *    每個區塊對應網站上的一個段落，找文字時比對頁面滾動位置即可定位到對應常數。
 *
 * 姓名、日期、場地為新人提供的正式資料，異動時於此檔一次替換即可。
 */
export const WEDDING_CONTENT = {
  brideGroomEn: 'Roger & Amy',
  brideGroomZh: '洪承孝　✕　李怡安',
  /** 婚期（ISO 日期，不含時間）。 */
  weddingDate: '2026-12-12',
  weddingDateDisplay: '2026 . 12 . 12　SATURDAY',
  /** 不含星期的純日期顯示，S3 宴客資訊區日期大字專用（S1 Hero 才帶 SATURDAY）。 */
  weddingDateOnlyDisplay: '2026 . 12 . 12',
  /** S3 日期大字下方的小字。新人選擇不顯示農曆，僅留星期。 */
  dateSubDisplay: '星期六',
  venueName: '臻愛花園飯店',
  venueHall: '2F　東方明珠',
  /**
   * 頁尾金色圓環內的縮寫。
   * 這裡用半形空白，不是全形 —— 全形空白的寬度等同一個字，
   * 在 20px 字級下會讓 R 與 A 各離 & 二十多 px，圓環裡看起來是散開的三個字母。
   */
  monogram: 'R & A',
  rsvpDeadlineDisplay: '2026 / 11 / 08',
} as const

/**
 * 倒數計時目標時間，即宴席開席時間；歸零後 Hero 的四格倒數會換成致謝句。
 */
export const WEDDING_COUNTDOWN_TARGET_ISO = '2026-12-12T18:00:00+08:00'

export interface WeddingSession {
  readonly id: 'lunch' | 'dinner'
  readonly label: string
  /**
   * 膠囊上時間那一段的完整字串，含「入席」這類說明詞。
   * 賓客真正要知道的是幾點該到，光寫 18:00 會被讀成開席時間而算錯出門時間。
   */
  readonly timeDisplay: string
}

/**
 * 宴席場次。本場婚宴只辦晚宴一場，故僅一筆；S3 的場次切換膠囊會依此只顯示一顆。
 * 日後若加辦午宴，補一筆 id: 'lunch' 即可，切換行為不必改。
 */
export const WEDDING_SESSIONS: readonly WeddingSession[] = [
  { id: 'dinner', label: '晚宴', timeDisplay: '18:00 入席' },
]

export interface GalleryPhoto {
  readonly id: string
  readonly url: string
  readonly alt: string
}

/**
 * 婚紗照 8 張，依拍攝場景由白天外景走到黃昏海邊排序，即畫面上的瀏覽順序。
 * 圖檔為原始檔縮至寬 1000 的網頁版本；手機版頁點指示器在 8 張以內仍清晰，再增量需改為數字式。
 * 路徑不加開頭斜線 —— 網站部署在 GitHub Pages 子路徑下，絕對路徑會在上線後 404。
 */
export const GALLERY_PHOTOS: readonly GalleryPhoto[] = [
  {
    id: 'photo-1',
    url: 'assets/gallery/photo-1.jpg',
    alt: '新人牽手走在林蔭道上，新娘身著粉色紗裙',
  },
  {
    id: 'photo-2',
    url: 'assets/gallery/photo-2.jpg',
    alt: '日式老屋前，新郎將身著黑色禮服的新娘抱起',
  },
  {
    id: 'photo-3',
    url: 'assets/gallery/photo-3.jpg',
    alt: '公園草地上相擁而笑的新人特寫',
  },
  {
    id: 'photo-4',
    url: 'assets/gallery/photo-4.jpg',
    alt: '藍天草原上，新人戴著愛心墨鏡舉著「我們結婚了」手牌',
  },
  {
    id: 'photo-5',
    url: 'assets/gallery/photo-5.jpg',
    alt: '黃昏河床上，新娘白紗長裙鋪展、與新郎相望',
  },
  {
    id: 'photo-6',
    url: 'assets/gallery/photo-6.jpg',
    alt: '新娘背影，長頭紗隨風揚起於溪谷之上',
  },
  {
    id: 'photo-7',
    url: 'assets/gallery/photo-7.jpg',
    alt: '海邊夕陽下，新郎輕吻新娘的手，手中捧著粉色花束',
  },
  {
    id: 'photo-8',
    url: 'assets/gallery/photo-8.jpg',
    alt: '沙灘上新郎將新娘橫抱起，兩人相視而笑',
  },
]

/** Hero 滿版底圖。是 LCP 元素，於 index.html 另外 preload（換圖時兩處要一起改）。 */
export const HERO_IMAGE_URL = 'assets/images/hero-mobile.jpg'

export const HERO_IMAGE_DESKTOP_URL = 'assets/images/hero-desktop.jpg'

/**
 * S1 主視覺封面區的固定文案（新人姓名、日期見 WEDDING_CONTENT，這裡只放版面上的標籤字）。
 * 倒數計時四格的英文標籤與婚期已過時顯示的致謝句都在畫面最上方、第一屏可見。
 */
/**
 * 進站開場層的文案。這一層存在的理由是技術性的：行動瀏覽器不允許沒有點擊就播放有聲音樂，
 * 賓客的那一下輕觸就是音樂的啟動許可。文案要讓那個動作看起來是儀式而不是障礙。
 */
/** 宴席類型。葷食是預設版本，素食由 /vegetarian 這個網址進入。 */
export type DietType = 'regular' | 'vegetarian'

/** 蔬食心意區的一則：左側文字、右側線稿插圖。 */
export interface DietNote {
  readonly id: string
  /** 金色小標籤（全大寫英文）。 */
  readonly tag: string
  /** 標籤下方的英文大字，是中文標題的英譯。 */
  readonly headlineEn: string
  readonly title: string
  readonly text: string
  readonly illustrationUrl: string
}

/**
 * 兩種宴席版本之間唯一有差異的內容。除了這裡列出的欄位，兩版完全相同。
 *
 * 注意：實際的分流不是「吃葷／吃素」，而是「女方親戚桌／其他所有人」——
 * 女方親戚整桌全蔬食，拿 /vegetarian；女方朋友與男方賓客都拿預設網址。
 * 這是蔬食心意區的禮金與餐點能寫得這麼直接的前提：讀者範圍與那兩則的對象完全吻合。
 * 分兩個網址而不是在表單裡問，也讓賓客不必自己勾選飲食需求。
 */
export const DIET_VARIANTS = {
  regular: {
    /** 出席回覆表單會收集的欄位預告。 */
    fieldChips: ['姓名', '出席人數', '素食需求', '兒童椅', '聯絡電話'] as readonly string[],
    /** 禮金與餐點兩則心意只對女方親戚桌說，葷食版不渲染整個蔬食心意區。 */
    dietNotes: [] as readonly DietNote[],
  },
  vegetarian: {
    /**
     * 素食版問的不是「吃不吃素」而是「吃哪一種素」——
     * 賓客是從素食專屬連結進來的，再問一次是否素食會讓人以為自己拿錯連結；
     * 但蔬食分全素、蛋奶素、忌五辛，光知道「這位吃素」不夠備餐。
     */
    fieldChips: ['姓名', '出席人數', '兒童椅', '聯絡電話', '蔬食備註'] as readonly string[],
    /**
     * 蔬食心意區的兩則，順序即畫面由上到下。
     *
     * 禮金排第一：這一版的連結只發給女方親戚桌，對象與讀者完全吻合，
     * 不會讓其他賓客看到後困惑自己該不該包。
     * 刻意不寫「現場不設禮金桌」—— 那要現場真的沒有那張桌子才成立，
     * 賓客到場看到桌子會覺得跟喜帖說的不一樣，反而更猶豫。
     *
     * 餐點站在「收到這個連結的吃素賓客」的角度寫：他要知道的是「有我的餐」，
     * 而不是整場的葷素分佈。英文大字放中文標題的英譯而不是開席時間——
     * 時間在宴客資訊區已經寫過，這裡重複一次反而像是另一個場次。
     */
    dietNotes: [
      {
        id: 'gift',
        tag: 'GIFT',
        headlineEn: 'YOUR PRESENCE',
        title: '不收禮金',
        text: '女方親友席不收禮金，敬請入座，您的到來就是我們最珍貴的祝福',
        illustrationUrl: 'assets/images/diet-note-gift.png',
      },
      {
        id: 'dinner',
        tag: 'DINNER',
        headlineEn: 'PLANT-BASED FEAST',
        title: '蔬食盛宴',
        text: '女方親友席宴請蔬食料理，由飯店主廚特別設計，期待與您共享蔬食盛宴',
        illustrationUrl: 'assets/images/diet-note-dinner.png',
      },
    ] as readonly DietNote[],
  },
} as const

/**
 * 蔬食心意區（只在 /vegetarian 出現）的抬頭。兩則內容本身在 DIET_VARIANTS.vegetarian.dietNotes。
 */
export const DIET_NOTES_TEXT = {
  eyebrow: 'WITH LOVE',
  title: 'A Little Note',
} as const

export const INTRO_GATE_TEXT = {
  /** 姓名上方的弧形標題，讓賓客一眼知道收到的是什麼。 */
  title: '婚禮邀請函',
  /** 提示文字，動詞開頭讓賓客知道要做什麼。 */
  action: '輕觸開啟',
  /** 螢幕報讀軟體會唸出來的按鈕說明（畫面上不顯示）。 */
  ariaLabel: '婚禮邀請函，輕觸開啟，並開始播放背景音樂',
} as const

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
 * S9 新人介紹區文案。引言與收尾句在手機刻意斷成兩行、桌機不斷行，兩種版本各自維護
 * （作法同 GALLERY_TEXT.quote），不要合併成一句再靠程式斷行。
 */
export const ABOUT_TEXT = {
  eyebrow: 'ABOUT US',
  title: 'The Two of Us',
  intro: {
    /** 桌機單行不斷行。 */
    full: '在遇見彼此之前，我們各自過著很不一樣的日子。',
    /** 手機刻意斷成兩行，順序即畫面順序。 */
    lines: ['在遇見彼此之前，', '我們各自過著很不一樣的日子。'] as readonly string[],
  },
  /** 兩張人物卡中間的連結符號，兩側各有一條金色細線。 */
  connector: '&',
  outro: {
    full: '一個把日子過成邏輯，一個把日子過成溫度，從 2026 . 12 . 12 起，我們一起過。',
    lines: [
      '一個把日子過成邏輯，一個把日子過成溫度，',
      '從 2026 . 12 . 12 起，我們一起過。',
    ] as readonly string[],
  },
} as const

export interface AboutProfile {
  readonly id: 'groom' | 'bride'
  /** 卡片最上方的英文角色標籤。 */
  readonly role: string
  readonly name: string
  /** 姓名下方的職業膠囊。 */
  readonly occupation: string
  readonly description: string
  readonly photoUrl: string
  readonly photoAlt: string
}

/**
 * S9 兩張人物卡的內容。順序即畫面順序（新郎在上／左，新娘在下／右）。
 *
 * 待替換：description 裡的性格描寫是撰稿推測，不是新人提供的事實，上線前必須由新人確認或改寫。
 * 職業與姓名是新人提供的事實，性格描寫不是——喜帖是公開的，寫錯個性比空著更糟。
 * 兩段描述請維持 42～48 字，字數跑掉兩張卡會不等高、中央的 & 會失去對稱。
 *
 * 照片為新人提供的真實單人照（4480×6720 原始檔上下各裁 374px 置中後縮至 600×800）。
 * 路徑不加開頭斜線 —— 網站部署在 GitHub Pages 子路徑下，絕對路徑會在上線後 404。
 */
export const ABOUT_PROFILES: readonly AboutProfile[] = [
  {
    id: 'groom',
    role: 'GROOM',
    name: '洪承孝',
    occupation: '軟體工程師',
    description:
      '靠一行行程式碼過日子，習慣把複雜的問題拆開來、一個一個解決。話不多，但答應的事情一定做到。',
    photoUrl: 'assets/images/groom.jpg',
    photoAlt: '新郎洪承孝身著米色西裝，於公園綠蔭前回眸',
  },
  {
    id: 'bride',
    role: 'BRIDE',
    name: '李怡安',
    occupation: '服務業',
    description:
      '在餐飲業裡練就一身照顧人的本事，記得誰不吃什麼、誰想多要一點醬。她相信好好吃一頓飯，能讓人重新有力氣。',
    photoUrl: 'assets/images/bride.jpg',
    photoAlt: '新娘李怡安身著白紗、手持捧花，於海邊夕陽下回眸',
  },
]

/**
 * S10 交往故事書區的固定文案（五頁故事內容見 STORY_PAGES）。
 * 翻頁鈕與頁碼的無障礙標籤都在這裡，畫面上不會直接顯示這幾句，但螢幕報讀器會唸出來。
 */
export const STORY_TEXT = {
  eyebrow: 'OUR STORY',
  title: 'How We Met',
  /**
   * 書頁卡下方的操作提示。手機可以左右滑，桌機沒有觸控只能點箭頭，所以兩句分開。
   * 手機把「滑動」放前面：那是主要的操作方式，箭頭是備援。
   */
  hint: '左右滑動或點箭頭翻頁',
  hintDesktop: '點兩側箭頭翻頁',
  prevLabel: '上一頁',
  nextLabel: '下一頁',
  /** 書本區的無障礙名稱，鍵盤使用者聚焦到書本時報讀器會唸出來。 */
  bookLabel: '交往故事書，可用左右方向鍵翻頁',
  /** 視覺隱藏的頁碼狀態句，{{current}}／{{total}} 會被換成實際頁碼。 */
  pageStatus: '第 {{current}} 頁，共 {{total}} 頁',
} as const

export interface StoryPage {
  readonly id: string
  /** 照片下方的年份標籤，例如「2019 秋」。 */
  readonly year: string
  readonly title: string
  readonly body: string
  readonly photoUrl: string
  readonly photoAlt: string
}

/**
 * S10 交往故事書的五頁內容，順序即翻頁順序。
 *
 * 待替換（一）：這五段故事沒有一句是真的，全部是為了把版面做出來而寫的示範文案，上線前必須整批替換。
 * 季節、地點、對話、繞半座城市送宵夜、搬三次家等細節全是編的——
 * 這是全站最不能留著假內容的地方，賓客會當真。
 *
 * 待替換（二）：photoUrl 目前全部是佔位圖，借用婚紗藝廊的照片，但婚紗照與「2019 秋」的時間軸對不上，
 * 正式應換成交往期間的生活照。五張需維持同一色調傾向（暖調、柔和），
 * 否則翻頁時每頁色溫跳動會很明顯。
 *
 * body 每段維持 58～64 字：手機一行約 21.4 字、桌機約 23.1 字，皆排成 3 行；
 * 超過 64 字手機會變成 4 行、撐爆固定高度的書頁卡。
 */
export const STORY_PAGES: readonly StoryPage[] = [
  {
    id: 'story-1',
    year: '2019 10月',
    title: '初次見面',
    body: '那年秋天，在朋友的一場聚會上第一次見到彼此。那天散場之後才發現，我們是聊到最後才離開的兩個人，連要回家的方向都一樣。',
    photoUrl: 'assets/gallery/photo-1.jpg',
    photoAlt: '新人牽手走在林蔭道上，新娘身著粉色紗裙',
  },
  {
    id: 'story-2',
    year: '2020 3月',
    title: '熟悉起來',
    body: '開始習慣生活裡有對方的日常。她下班傳訊息說今天很累，他就把宵夜送到樓下，說剛好順路——其實那天他整整繞了半座城市才到。',
    photoUrl: 'assets/gallery/photo-2.jpg',
    photoAlt: '日式老屋前，新郎將身著黑色禮服的新娘抱起',
  },
  {
    id: 'story-3',
    year: '2020 7月',
    title: '在一起',
    body: '其實那天沒有誰正式開口說什麼。只是某一天散步回家的路上，牽起來的手就沒有再放開；後來想想，那條路我們一走就走了好多年。',
    photoUrl: 'assets/gallery/photo-3.jpg',
    photoAlt: '公園草地上相擁而笑的新人特寫',
  },
  {
    id: 'story-4',
    year: '2021 – 2025',
    title: '一起走過的日子',
    body: '我們一起搬過三次家，一起吵過架也一起道過歉。日子說不上轟轟烈烈，但每一天都比前一天更確定一點，確定要一直這樣走下去。',
    photoUrl: 'assets/gallery/photo-4.jpg',
    photoAlt: '藍天草原上，新人戴著愛心墨鏡舉著「我們結婚了」手牌',
  },
  {
    id: 'story-5',
    year: '2026 3月',
    title: '他問，她說好',
    body: '就在第一次見面的那家店門口，他單膝跪下。她一邊哭一邊點頭，然後說了一句：你怎麼這麼慢。那天整間店的人全都站起來鼓掌。',
    photoUrl: 'assets/gallery/photo-5.jpg',
    photoAlt: '黃昏河床上，新娘白紗長裙鋪展、與新郎相望',
  },
]

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
  /** 卡片內資訊列各自的標籤字，順序固定：宴會地點／宴會廳／地址。 */
  rowLabels: {
    venue: '宴會地點',
    hall: '宴會廳',
    address: '地址',
  },
  /** 內嵌地圖的無障礙標題（螢幕報讀器會唸出來，畫面上不會直接顯示）。 */
  mapFrameTitle: '臻愛花園飯店位置地圖',
  /** 導航按鈕文字。 */
  navButtonLabel: '開啟 Google 地圖導航',
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
  /**
   * 表單會收集的欄位預告，畫面上以 chip 呈現，順序即畫面順序。
   * 這幾顆必須與實際 Google 表單的題目對得上，否則賓客會看到預告了卻沒被問的欄位。
   */
  fieldChips: ['姓名', '出席人數', '素食需求', '兒童椅', '聯絡電話'] as readonly string[],
  /** 主要 CTA 按鈕文字。 */
  ctaLabel: '填寫出席回覆表單',
  /** CTA 按鈕下方的小字註記。 */
  ctaNote: '將另開新視窗前往 Google 表單',
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
  copyright: '© 2026 Roger & Amy　·　Made with love',
} as const

/**
 * 浮動音樂鈕三種狀態各自的無障礙標籤（螢幕報讀器會唸出來，畫面上不會直接顯示文字）。
 */
export const MUSIC_PLAYER_TEXT = {
  ariaLabelIdle: '播放背景音樂',
  ariaLabelPlaying: '靜音背景音樂',
  ariaLabelMuted: '取消靜音並播放背景音樂',
} as const
