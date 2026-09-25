import { ChangeDetectionStrategy, Component, input } from '@angular/core'
import { ScrollRevealDirective } from '../scroll-reveal.directive'

/**
 * 各段落共用的「英文小字眉標 + 中文主標」抬頭，所有內容段落共用同一套排版節奏。
 */
@Component({
  selector: 'app-section-heading',
  imports: [ScrollRevealDirective],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="heading" appScrollReveal [staggerSelector]="'.heading__item'" [staggerMs]="90">
      <p class="heading__eyebrow heading__item anim-fade-up">{{ eyebrow() }}</p>
      <h2 class="heading__title heading__item anim-fade-up">{{ title() }}</h2>
    </div>
  `,
  styles: `
    .heading {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
    }

    .heading__eyebrow {
      margin: 0;
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 5px;
      color: var(--color-accent-gold);
    }

    /**
     * 主標是中文，用全站的中文襯線體；花體字型沒有中文字，套上去只會掉到系統預設字型。
     * 字距加在字尾會讓置中偏左，左側補同寬的內距抵銷。
     */
    .heading__title {
      margin: 10px 0 0;
      padding-left: 6px;
      font-family: var(--font-body);
      font-size: 24px;
      font-weight: 500;
      letter-spacing: 6px;
      line-height: 1.3;
      color: var(--color-primary);
    }

    /**
     * 桌機字級開放給使用端以自訂屬性覆寫：多數段落沿用預設的 14／36，
     * 蔬食心意區主體只有兩則，自己在 :host 把這兩個變數調小，其餘段落不必知道有這回事。
     */
    @media (min-width: 1024px) {
      .heading__eyebrow {
        font-size: var(--section-heading-eyebrow-size, 14px);
        letter-spacing: var(--section-heading-eyebrow-spacing, 6px);
      }

      .heading__title {
        margin-top: 12px;
        padding-left: 10px;
        font-size: var(--section-heading-title-size, 36px);
        letter-spacing: 10px;
      }
    }
  `,
})
export class SectionHeadingComponent {
  readonly eyebrow = input.required<string>()
  readonly title = input.required<string>()
}
