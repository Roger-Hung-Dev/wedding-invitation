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
      font-size: 14px;
      font-weight: 600;
      letter-spacing: 5px;
      color: var(--color-accent-gold);
    }

    .heading__title {
      margin: 10px 0 0;
      font-family: var(--font-script);
      font-size: 34px;
      // 用 Tangerine 本身的粗體字重（index.html 有載入 700），不是瀏覽器硬描的假粗體。
      font-weight: 700;
      line-height: 1.2;
      color: var(--color-primary);
    }

    /**
     * 各段抬頭的字級一律相同（手機 14／34、桌機 18／56），不開放個別段落覆寫：
     * 曾經讓蔬食心意區自己縮小，結果相鄰兩段一大一小，看起來像排錯。頁尾的抬頭也比照這組數值。
     */
    @media (min-width: 1024px) {
      .heading__eyebrow {
        font-size: 18px;
        letter-spacing: 6px;
      }

      .heading__title {
        margin-top: 12px;
        font-size: 56px;
      }
    }
  `,
})
export class SectionHeadingComponent {
  readonly eyebrow = input.required<string>()
  readonly title = input.required<string>()
}
