import { ChangeDetectionStrategy, Component, inject } from '@angular/core'
import { ABOUT_PROFILES, ABOUT_TEXT } from '../../core/config/wedding-content'
import { BreakpointService } from '../../shared/breakpoint.service'
import { ScrollRevealDirective } from '../../shared/scroll-reveal.directive'
import { SectionHeadingComponent } from '../../shared/section-heading/section-heading.component'

/**
 * 進場分鏡裡新郎卡與新娘卡的間隔（毫秒）。照片與文字欄各自的延遲都由這個間隔推出來，
 * 讓視線照「他 → 兩人 → 她」的順序走一遍，而不是兩張卡同時冒出來。
 */
const CARD_SEQUENCE_GAP_MS = 440

/** 第一張卡的照片與文字欄延遲，第二張各自加上 CARD_SEQUENCE_GAP_MS。 */
const CARD_PHOTO_DELAY_MS = 420
const CARD_TEXT_DELAY_MS = 520

/**
 * S9 新人介紹區。兩張人物卡在手機是上下堆疊、桌機是左右並排，中央都有一組金線加 & 的連結列。
 * 新娘卡是新郎卡的鏡像（照片與文字欄對調、文字改靠右），不是單純把照片搬到另一邊——
 * 只搬照片會在版面正中央留下一條參差的邊。
 * 進場時兩張卡分別由外側往中央推（fade-side），表達「兩個原本各過各的人向彼此靠攏」。
 */
@Component({
  selector: 'app-about',
  imports: [SectionHeadingComponent, ScrollRevealDirective],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './about.component.html',
  styleUrl: './about.component.scss',
})
export class AboutComponent {
  protected readonly breakpoint = inject(BreakpointService)
  protected readonly text = ABOUT_TEXT
  protected readonly profiles = ABOUT_PROFILES

  protected photoDelayMs(index: number): number {
    return CARD_PHOTO_DELAY_MS + index * CARD_SEQUENCE_GAP_MS
  }

  protected textDelayMs(index: number): number {
    return CARD_TEXT_DELAY_MS + index * CARD_SEQUENCE_GAP_MS
  }
}
