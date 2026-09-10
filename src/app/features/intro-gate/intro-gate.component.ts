import { isPlatformBrowser } from '@angular/common'
import { ChangeDetectionStrategy, Component, PLATFORM_ID, effect, inject } from '@angular/core'
import { HERO_IMAGE_DESKTOP_URL, HERO_IMAGE_URL, INTRO_GATE_TEXT, WEDDING_CONTENT } from '../../core/config/wedding-content'
import { MusicPlayerStore } from '../music-player/music-player.store'
import { IntroGateStore } from './intro-gate.store'

/**
 * 進站開場層：蓋滿畫面，賓客輕觸一下才進入喜帖本體。
 *
 * 這一層不是為了視覺效果才加的，是行動瀏覽器逼出來的：
 * 沒有點擊或輕觸就不准播放有聲音樂，滑動不算，靜音預播後解除靜音也會被立刻暫停。
 * 既然一定要有一次點擊，就把它做成進場的儀式，而不是一顆孤零零的播放鈕。
 *
 * 整層本身就是按鈕（而不是在中間放一顆小鈕），賓客點畫面任何地方都能進入。
 */
@Component({
  selector: 'app-intro-gate',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (!store.entered()) {
      <button type="button" class="gate" [attr.aria-label]="text.ariaLabel" (click)="enter()">
        <img class="gate__bg gate__bg--mobile" [src]="heroImageUrl" alt="" aria-hidden="true" />
        <img class="gate__bg gate__bg--desktop" [src]="heroImageDesktopUrl" alt="" aria-hidden="true" />
        <span class="gate__veil" aria-hidden="true"></span>

        <span class="gate__content">
          <span class="gate__title" aria-hidden="true">
            <svg viewBox="0 0 220 46" width="220" height="46">
              <path id="gateTitleArc" d="M 12 46 Q 110 -8 208 46" fill="none" />
              <text>
                <textPath href="#gateTitleArc" startOffset="50%" text-anchor="middle">{{ text.title }}</textPath>
              </text>
            </svg>
          </span>

          <span class="gate__name-en">{{ content.brideGroomEn }}</span>
          <span class="gate__name-zh">{{ content.brideGroomZh }}</span>

          <span class="gate__divider" aria-hidden="true">
            <span class="gate__divider-line"></span>
            <span class="gate__divider-diamond"></span>
            <span class="gate__divider-line"></span>
          </span>

          <span class="gate__action">{{ text.action }}</span>
        </span>
      </button>
    }
  `,
  styles: `
    .gate {
      position: fixed;
      inset: 0;
      z-index: 100;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0;
      border: none;
      background: var(--color-gate-backdrop);
      cursor: pointer;
      animation: gate-in 600ms var(--ease-elegant) both;
    }

    /*
      背景用封面同一張圖，點開後與 Hero 銜接不會有換圖的斷裂感。
      用 img 而不是 CSS 的 background-image：樣式表裡的 url() 得寫成絕對路徑，
      而這個網站部署在子路徑下，絕對路徑上線就會 404（本機卻完全正常）。
      走 img 就能沿用與 Hero 相同的常數，換圖時也不會漏掉這一層。
    */
    .gate__bg {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .gate__bg--desktop {
      display: none;
    }

    /*
      遮罩壓暗照片、讓文字讀得清楚，但照片必須看得出是誰 ——
      這一層是喜帖的第一眼，蓋成一片色塊就失去意義了。
      用黑色而不是酒紅：酒紅疊在照片上會把膚色與白紗都染成紫紅。
    */
    .gate__veil {
      position: absolute;
      inset: 0;
      background: linear-gradient(180deg, #00000073 0%, #000000b3 100%);
    }

    /*
      整組文字往上：底圖的人物在畫面中央偏下，文字若也置中就會壓在臉上。
      用 transform 而不是改 flex 對齊，是因為它不影響佈局計算，
      子元素各自的進場動畫也不受影響。

      這一層垂直置中，所以位移不能單獨算 —— 內容的總高一變，整組就會自己跑掉一半。
      手機的 -137 是兩件事疊起來的：

      1. 飾線與它上面兩行往下 20（.gate__action 的 margin 56 → 36）。內容因此變矮 20，
         置中後整組往回彈 10，所以位移只需給 10 → -110。
      2. 上方加了弧形標題（高 46 + margin 8 = 54）。新元素加在上方時，內容頂端上移 27，
         但標題以下的元素相對頂端又往下 54，淨往下 27 —— 要抵銷得往上補 27 → -137。

      ⚠️ 補償方向很容易搞反：加在上方的元素要往「上」補，不是往下。
      改動任一項的通則是：位移 = -120 + (action 少掉的 margin)/2 − (上方新增的高度)/2。
      桌機的排版不同（字級大、action 的 margin 是 52、標題也放大），數值另外算。
    */
    .gate__content {
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 0 24px;
      text-align: center;
      transform: translateY(-137px);
    }

    /*
      弧形標題。CSS 排不出弧形文字，逐字旋轉又會讓中文字歪掉，
      所以走 SVG 的 textPath —— 字形保持完整，只是整個字順著曲線轉。

      SVG 的佈局高度固定在 46，字靠 overflow: visible 溢出框外，
      所以調弧度（path 的控制點）不會動到下面的排版。
      弧線兩端越陡，最外側的字被轉得越多 —— 目前的弧度下「函」會比其他字略低，
      這是選定的樣式，不是沒對齊。
    */
    .gate__title {
      display: block;
      line-height: 0;
      margin-bottom: 8px;
      animation: gate-rise 900ms var(--ease-elegant) 80ms both;
    }

    .gate__title svg {
      display: block;
      overflow: visible;
    }

    .gate__title text {
      font-size: 13px;
      font-weight: 500;
      letter-spacing: 5px;
      fill: var(--color-text-invert);
    }

    .gate__name-en {
      font-family: var(--font-script);
      font-size: 52px;
      line-height: 1.2;
      color: var(--color-text-invert);
      animation: gate-rise 900ms var(--ease-elegant) 200ms both;
    }

    .gate__name-zh {
      margin-top: 10px;
      font-size: 17px;
      font-weight: 400;
      letter-spacing: 6px;
      line-height: 1.4;
      color: var(--color-text-invert);
      animation: gate-rise 900ms var(--ease-elegant) 340ms both;
    }

    .gate__divider {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 28px;
      animation: gate-rise 900ms var(--ease-elegant) 480ms both;
    }

    .gate__divider-line {
      width: 28px;
      height: 1px;
      background: var(--color-gold-soft);
    }

    .gate__divider-diamond {
      width: 8px;
      height: 8px;
      background: var(--color-gold-soft);
      transform: rotate(45deg);
    }

    /*
      這行字是整層唯一要賓客做的事，所以給它緩慢的呼吸感把視線帶過去。
      節奏刻意訂得比全站其他動畫慢，讀起來像等待而不是催促。
    */
    .gate__action {
      margin-top: 36px;
      font-size: 13px;
      font-weight: 500;
      letter-spacing: 5px;
      color: var(--color-gold-soft);
      /* 底圖亮處（天空、白紗）會吃掉金色字，加一層暗影確保任何一張封面都讀得到 */
      text-shadow: 0 1px 6px #00000099;
      animation:
        gate-rise 900ms var(--ease-elegant) 640ms both,
        gate-breathe 2600ms ease-in-out 1500ms infinite;
    }

    @keyframes gate-in {
      from {
        opacity: 0;
      }
      to {
        opacity: 1;
      }
    }

    @keyframes gate-rise {
      from {
        opacity: 0;
        transform: translateY(16px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    @keyframes gate-breathe {
      0%,
      100% {
        opacity: 0.72;
      }
      50% {
        opacity: 1;
      }
    }

    @media (min-width: 1024px) {
      .gate__bg--mobile {
        display: none;
      }

      .gate__bg--desktop {
        display: block;
      }

      /*
        桌機不套用手機那 10px 的下讓，但同樣要抵銷弧形標題撐出來的高度。
        標題等比放大到 254×53（＝220×15/13，讓字看起來是 15px，與 .gate__action 同級），
        所以補償是 -120 − (53+8)/2 ≈ -150。
      */
      .gate__content {
        transform: translateY(-150px);
      }

      .gate__title svg {
        width: 254px;
        height: 53px;
      }

      .gate__name-en {
        font-size: 88px;
      }

      .gate__name-zh {
        margin-top: 14px;
        font-size: 24px;
        letter-spacing: 8px;
      }

      .gate__action {
        margin-top: 52px;
        font-size: 15px;
      }
    }

    /*
      減少動態時只留淡入：脈動與位移都拿掉，但提示文字要維持完全不透明，
      否則它會停在呼吸動畫的半透明起點，變成一行看不清楚的字。
    */
    @media (prefers-reduced-motion: reduce) {
      .gate,
      .gate__name-en,
      .gate__name-zh,
      .gate__divider,
      .gate__action {
        animation: none;
        opacity: 1;
        transform: none;
      }
    }
  `,
})
export class IntroGateComponent {
  protected readonly store = inject(IntroGateStore)
  protected readonly content = WEDDING_CONTENT
  protected readonly text = INTRO_GATE_TEXT
  private readonly musicPlayerStore = inject(MusicPlayerStore)
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID))

  constructor() {
    // 開場層蓋著的時候鎖住整頁捲動。它雖然是 fixed 蓋滿畫面，
    // 但手指滑過去仍會捲到背後的內容 —— 賓客會看到一頁在開場層底下偷偷移動。
    effect(() => {
      if (!this.isBrowser) return
      // 兩個都要鎖：真正的捲動容器是 <html>，只鎖 <body> 擋不住（實測仍會捲動）
      const value = this.store.entered() ? '' : 'hidden'
      document.documentElement.style.overflow = value
      document.body.style.overflow = value
    })
  }

  /** 與 Hero 共用同一組底圖常數，換封面時不會漏掉開場層這一張。 */
  protected readonly heroImageUrl = HERO_IMAGE_URL
  protected readonly heroImageDesktopUrl = HERO_IMAGE_DESKTOP_URL

  /**
   * 這一下點擊是整個流程的關鍵：它同時是音樂的播放許可與 Hero 入場的起跑訊號。
   * 音樂要在這裡直接啟動，不能延後到動畫結束 —— 瀏覽器只認手勢當下發出的播放請求。
   */
  enter(): void {
    this.musicPlayerStore.play()
    this.store.enter()
  }
}
