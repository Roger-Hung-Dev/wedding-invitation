import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core'

/** 壓印要融入的底色；對應各段落實際的背景色。 */
export type EmbossTone = 'blush' | 'ivory' | 'wine'

/**
 * 段落背景四角的捲草壓印，像實體喜帖的壓紋紙：花紋填的是跟底色相同的顏色，
 * 只靠左上一道陰影、右下一道反光讓人看出凹下去的形狀。
 *
 * 使用端的段落根元素要設 position: relative 與 isolation: isolate —— 本元件以 z-index: -1
 * 壓在段落背景之上、內容之下，沒有 isolation 會一路沉到整頁背景後面而看不見。
 */
@Component({
  selector: 'app-corner-emboss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    'aria-hidden': 'true',
    '[attr.data-top]': 'top()',
    '[attr.data-bottom]': 'bottomTone()',
  },
  template: `
    @for (corner of corners; track corner.pos) {
      <svg [class]="'corner corner--' + corner.pos" viewBox="0 0 136 136" focusable="false">
        <!-- 左右上下的角用 SVG 內部的變換鏡像，而不是對整個 svg 做 CSS transform：
             CSS 濾鏡會跟著元素一起翻面，四個角的光源方向就不一致了。 -->
        <g [attr.transform]="corner.mirror">
          <g fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
            <path d="M16 118 C16 58 58 16 118 16" />
            <path d="M26 92 C26 56 56 26 92 26" />
            <path d="M118 16 c 14 0 20 12 10 18 c -8 5 -16 -4 -10 -9" />
            <path d="M16 118 c 0 14 12 20 18 10 c 5 -8 -4 -16 -9 -10" />
            <path d="M40 40 q 18 -2 30 -18" />
            <path d="M40 40 q -2 18 -18 30" />
          </g>
          <ellipse cx="48" cy="48" rx="6" ry="13" transform="rotate(-45 48 48)" fill="currentColor" />
        </g>
      </svg>
    }
  `,
  styles: `
    :host {
      --top-fill: var(--color-bg-blush);
      --top-shadow: #9e3a634d;
      --top-light: #fffffff2;
      --bottom-fill: var(--top-fill);
      --bottom-shadow: var(--top-shadow);
      --bottom-light: var(--top-light);

      position: absolute;
      inset: 0;
      z-index: -1;
      overflow: hidden;
      pointer-events: none;
    }

    // 陰影色取自各底色本身的深色版本，不用中性灰：灰色壓在粉底上會像髒污而不像紙紋。
    :host([data-top='ivory']) {
      --top-fill: var(--color-bg-ivory);
      --top-shadow: #8a5a454d;
    }

    :host([data-top='wine']) {
      --top-fill: var(--color-text-main);
      --top-shadow: #28000f73;
      --top-light: #ffffff24;
    }

    :host([data-bottom='blush']) {
      --bottom-fill: var(--color-bg-blush);
      --bottom-shadow: #9e3a634d;
      --bottom-light: #fffffff2;
    }

    :host([data-bottom='ivory']) {
      --bottom-fill: var(--color-bg-ivory);
      --bottom-shadow: #8a5a454d;
      --bottom-light: #fffffff2;
    }

    :host([data-bottom='wine']) {
      --bottom-fill: var(--color-text-main);
      --bottom-shadow: #28000f73;
      --bottom-light: #ffffff24;
    }

    // 陰影位移必須是整數 px：Safari（WebKit）會把 drop-shadow 的位移截成整數，
    // 寫 0.9px 會變成 0，陰影正好藏在同色花紋底下，整個壓印就消失了。
    .corner {
      position: absolute;
      width: 118px;
      height: 118px;
      color: var(--top-fill);
      filter: drop-shadow(-1px -1px 0 var(--top-shadow)) drop-shadow(1px 1px 0 var(--top-light));
    }

    .corner--tl {
      top: 0;
      left: 0;
    }

    .corner--tr {
      top: 0;
      right: 0;
    }

    .corner--bl,
    .corner--br {
      bottom: 0;
      color: var(--bottom-fill);
      filter: drop-shadow(-1px -1px 0 var(--bottom-shadow)) drop-shadow(1px 1px 0 var(--bottom-light));
    }

    .corner--bl {
      left: 0;
    }

    .corner--br {
      right: 0;
    }

    @media (min-width: 1024px) {
      .corner {
        width: 150px;
        height: 150px;
      }
    }
  `,
})
export class CornerEmbossComponent {
  /** 上方兩角的底色。 */
  readonly top = input<EmbossTone>('blush')
  /** 下方兩角的底色；段落是上下漸層時才需要另外指定，預設同上方。 */
  readonly bottom = input<EmbossTone | undefined>(undefined)

  protected readonly bottomTone = computed(() => this.bottom() ?? this.top())

  protected readonly corners = [
    { pos: 'tl', mirror: null },
    { pos: 'tr', mirror: 'translate(136 0) scale(-1 1)' },
    { pos: 'bl', mirror: 'translate(0 136) scale(1 -1)' },
    { pos: 'br', mirror: 'translate(136 136) scale(-1 -1)' },
  ] as const
}
