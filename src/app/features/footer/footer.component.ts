import { ChangeDetectionStrategy, Component } from '@angular/core'
import { ScrollRevealDirective } from '../../shared/scroll-reveal.directive'
import { FOOTER_TEXT, WEDDING_CONTENT } from '../../core/config/wedding-content'

/**
 * S5 結語區。全站最後一段，monogram 圓環描邊動畫時長最慢，做為整份喜帖的收尾。
 */
@Component({
  selector: 'app-footer',
  imports: [ScrollRevealDirective],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './footer.component.html',
  styleUrl: './footer.component.scss',
})
export class FooterComponent {
  protected readonly content = WEDDING_CONTENT
  protected readonly text = FOOTER_TEXT
  protected readonly weddingDateDisplay = WEDDING_CONTENT.weddingDate.replaceAll('-', ' . ')
}
