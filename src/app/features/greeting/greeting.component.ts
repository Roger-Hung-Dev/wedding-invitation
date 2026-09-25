import { ChangeDetectionStrategy, Component } from '@angular/core'
import { ScrollRevealDirective } from '../../shared/scroll-reveal.directive'
import { GREETING_TEXT, WEDDING_CONTENT } from '../../core/config/wedding-content'

/**
 * 婚紗藝廊與交通資訊之間的過場：一張照片淡進背景，下方置中一句「好久不見，我們婚禮見」。
 * 不帶段落抬頭、不放任何按鈕 —— 它是兩段之間的一口呼吸，不是一個新的資訊區。
 */
@Component({
  selector: 'app-greeting',
  imports: [ScrollRevealDirective],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './greeting.component.html',
  styleUrl: './greeting.component.scss',
})
export class GreetingComponent {
  protected readonly text = GREETING_TEXT
  /** 寫法與頁尾相同（年 . 月 . 日），由婚期換算，不另外寫死一份日期。 */
  protected readonly dateDisplay = WEDDING_CONTENT.weddingDate.replaceAll('-', ' . ')
}
