import { ChangeDetectionStrategy, Component } from '@angular/core'
import { IconComponent } from '../../shared/icon/icon.component'
import { ScrollRevealDirective } from '../../shared/scroll-reveal.directive'
import { SectionHeadingComponent } from '../../shared/section-heading/section-heading.component'
import { WEDDING_CONTENT } from '../../core/config/wedding-content'
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

  protected readonly chips = ['姓名', '出席人數', '素食需求', '兒童椅', '喜餅領取', '聯絡電話', '祝福話語']
}
