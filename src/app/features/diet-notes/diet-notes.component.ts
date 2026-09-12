import { ChangeDetectionStrategy, Component, inject } from '@angular/core'
import { CornerEmbossComponent } from '../../shared/corner-emboss/corner-emboss.component'
import { ScrollRevealDirective } from '../../shared/scroll-reveal.directive'
import { SectionHeadingComponent } from '../../shared/section-heading/section-heading.component'
import { DIET_NOTES_TEXT } from '../../core/config/wedding-content'
import { DietStore } from '../../core/diet.store'

/**
 * S3.5 蔬食心意區：只在 /vegetarian 出現，排在宴客資訊與出席回覆之間。
 * 禮金與餐點原本是宴客資訊卡裡的兩列，抽成獨立一段，才放得下線稿插圖、讀起來像一封短信而不是規則條目。
 * 要不要渲染由首頁依 DietStore 決定，這裡不再判斷版本。
 */
@Component({
  selector: 'app-diet-notes',
  imports: [CornerEmbossComponent, SectionHeadingComponent, ScrollRevealDirective],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './diet-notes.component.html',
  styleUrl: './diet-notes.component.scss',
})
export class DietNotesComponent {
  protected readonly diet = inject(DietStore)
  protected readonly text = DIET_NOTES_TEXT
}
