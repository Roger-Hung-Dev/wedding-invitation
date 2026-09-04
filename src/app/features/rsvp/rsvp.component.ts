import { ChangeDetectionStrategy, Component, computed } from '@angular/core'
import { IconComponent } from '../../shared/icon/icon.component'
import { ScrollRevealDirective } from '../../shared/scroll-reveal.directive'
import { SectionHeadingComponent } from '../../shared/section-heading/section-heading.component'
import { RSVP_TEXT, WEDDING_CONTENT } from '../../core/config/wedding-content'
import { WEDDING_LINKS } from '../../core/config/wedding-links'

/**
 * S4 意願調查區。全站沒有內嵌表單，一律外連 Google 表單，符合專案範圍界線。
 */
@Component({
  selector: 'app-rsvp',
  imports: [SectionHeadingComponent, IconComponent, ScrollRevealDirective],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './rsvp.component.html',
  styleUrl: './rsvp.component.scss',
})
export class RsvpComponent {
  protected readonly content = WEDDING_CONTENT
  protected readonly links = WEDDING_LINKS
  protected readonly text = RSVP_TEXT

  /** 說明文第二行的 {{deadline}} 佔位字串換成截止日，日期只有 WEDDING_CONTENT.rsvpDeadlineDisplay 這一個來源。 */
  protected readonly introLines = computed(() =>
    this.text.introLines.map((line) => line.replace('{{deadline}}', this.content.rsvpDeadlineDisplay)),
  )
}
