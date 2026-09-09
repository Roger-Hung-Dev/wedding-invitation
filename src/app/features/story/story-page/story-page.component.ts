import { ChangeDetectionStrategy, Component, input, output } from '@angular/core'
import { StoryPage } from '../../../core/config/wedding-content'

/**
 * 書頁的版式：手機是照片與文字同一頁；桌機雙頁展開後拆成左頁只有照片、右頁只有文字。
 */
export type StoryPageVariant = 'single' | 'photo' | 'text'

/** 進場分鏡裡卡內元素各自的延遲（毫秒），文字三行交錯 90ms。 */
const PHOTO_DELAY_MS = 440
const YEAR_DELAY_MS = 600
const TITLE_DELAY_MS = 690
const BODY_DELAY_MS = 780

/**
 * 一頁書頁的內容。同一份版式會被用在三個地方：常駐的目前頁、翻頁時長出來的舊頁、
 * 以及翻頁動畫的正反面，所以做成獨立元件而不是在樣板裡抄三份。
 *
 * animated 只有常駐的目前頁會開啟：翻頁時長出來的那幾份不掛進場動畫的 class，
 * 否則每翻一頁卡內元素就會重播一次 fade-up，翻頁會變得很吵。
 */
@Component({
  selector: 'app-story-page',
  imports: [],
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    '[class.page--single]': "variant() === 'single'",
    '[class.page--photo]': "variant() === 'photo'",
    '[class.page--text]': "variant() === 'text'",
  },
  templateUrl: './story-page.component.html',
  styleUrl: './story-page.component.scss',
})
export class StoryPageComponent {
  readonly page = input.required<StoryPage>()
  readonly variant = input.required<StoryPageVariant>()
  /** 桌機右頁右下角的兩位數頁碼；手機不顯示頁碼，傳 null 即可。 */
  readonly pageNumber = input<string | null>(null)
  readonly animated = input(false)

  /** 照片被點擊（含左右半邊的位置資訊），由外層決定要往前還是往後翻。 */
  readonly photoClick = output<MouseEvent>()

  protected readonly photoDelayMs = PHOTO_DELAY_MS
  protected readonly yearDelayMs = YEAR_DELAY_MS
  protected readonly titleDelayMs = TITLE_DELAY_MS
  protected readonly bodyDelayMs = BODY_DELAY_MS
}
