import { ChangeDetectionStrategy, Component, input } from '@angular/core'
import { ScrollRevealDirective } from '../scroll-reveal.directive'

/**
 * 各段落共用的「小字眉標 + 花體主標」抬頭，五段內容區共用同一套排版節奏。
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

    .heading__title {
      margin: 10px 0 0;
      font-family: var(--font-script);
      font-size: 34px;
      font-weight: 400;
      line-height: 1.2;
      color: var(--color-primary);
    }

    // 桌機字級開放給使用端以自訂屬性覆寫：多數段落沿用預設的 14／56，
    // 新人介紹與交往故事書兩段的設計稿訂的是較小的 13／44（那兩段主體是卡片而非抬頭），
    // 由該段自己在 :host 設定這兩個變數，其餘段落不必知道有這回事。
    @media (min-width: 1024px) {
      .heading__eyebrow {
        font-size: var(--section-heading-eyebrow-size, 14px);
        letter-spacing: var(--section-heading-eyebrow-spacing, 6px);
      }

      .heading__title {
        margin-top: 12px;
        font-size: var(--section-heading-title-size, 56px);
      }
    }
  `,
})
export class SectionHeadingComponent {
  readonly eyebrow = input.required<string>()
  readonly title = input.required<string>()
}
