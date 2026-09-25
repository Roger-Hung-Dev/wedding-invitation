import { ChangeDetectionStrategy, Component, input } from '@angular/core'
import { ScrollRevealDirective } from '../scroll-reveal.directive'

/**
 * 各段落共用的「小字眉標 + 花體主標」抬頭，五段內容區共用同一套排版節奏。
 * 眉標可省略；主標是中文時改用 serif 模式（見 titleFont）。
 */
@Component({
  selector: 'app-section-heading',
  imports: [ScrollRevealDirective],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="heading" appScrollReveal [staggerSelector]="'.heading__item'" [staggerMs]="90">
      @if (eyebrow()) {
        <p class="heading__eyebrow heading__item anim-fade-up">{{ eyebrow() }}</p>
      }
      <h2 class="heading__title heading__item anim-fade-up" [class.heading__title--serif]="titleFont() === 'serif'">
        {{ title() }}
      </h2>
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
      margin: 0;
      font-family: var(--font-script);
      font-size: 34px;
      font-weight: 400;
      line-height: 1.2;
      color: var(--color-primary);
    }

    // 間距掛在「眉標後面的主標」上，省略眉標時主標才不會頂著一段空白。
    .heading__eyebrow + .heading__title {
      margin-top: 10px;
    }

    /**
     * 花體字型沒有中文字，中文主標套花體只會掉到系統預設字型，跟全站的中文襯線體對不起來。
     * 字級比花體小一截：花體的字身只佔字框一半左右，中文字卻是滿格，同字級看起來會大很多。
     * 字距加在字尾會讓置中偏左，左側補同寬的內距抵銷。
     */
    .heading__title--serif {
      font-family: var(--font-body);
      font-size: 24px;
      font-weight: 500;
      letter-spacing: 6px;
      padding-left: 6px;
    }

    /**
     * 桌機字級開放給使用端以自訂屬性覆寫：多數段落沿用預設的 14／56，
     * 新人介紹與交往故事書兩段的設計稿訂的是較小的 13／44（那兩段主體是卡片而非抬頭），
     * 由該段自己在 :host 設定這兩個變數，其餘段落不必知道有這回事。
     */
    @media (min-width: 1024px) {
      .heading__eyebrow {
        font-size: var(--section-heading-eyebrow-size, 14px);
        letter-spacing: var(--section-heading-eyebrow-spacing, 6px);
      }

      .heading__eyebrow + .heading__title {
        margin-top: 12px;
      }

      .heading__title {
        font-size: var(--section-heading-title-size, 56px);
      }

      .heading__title--serif {
        font-size: 36px;
        letter-spacing: 10px;
        padding-left: 10px;
      }
    }
  `,
})
export class SectionHeadingComponent {
  /** 主標上方的英文小字；留空就不渲染，主標直接貼齊段落頂端。 */
  readonly eyebrow = input('')
  readonly title = input.required<string>()
  /** script＝花體（英文主標的預設）；serif＝全站中文襯線體，給中文主標用。 */
  readonly titleFont = input<'script' | 'serif'>('script')
}
