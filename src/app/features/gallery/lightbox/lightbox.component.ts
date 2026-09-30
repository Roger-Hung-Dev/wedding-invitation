import { A11yModule } from '@angular/cdk/a11y'
import { ChangeDetectionStrategy, Component, HostListener, computed, input, output } from '@angular/core'
import { IconComponent } from '../../../shared/icon/icon.component'
import { GalleryPhoto } from '../../../core/config/wedding-content'
import { WebpSrcsetPipe } from '../../../shared/webp-srcset.pipe'

/** 判定為換圖的水平滑動距離。 */
const SWIPE_THRESHOLD_PX = 48

/**
 * 頁面縮放超過這個倍率就視為「正在放大看照片」，單指拖動是在移動畫面看細節，不換圖。
 * 留一點餘裕而不是寫 1：捏回原尺寸時，瀏覽器常停在 1.00x 附近而不是剛好 1。
 */
const ZOOMED_SCALE = 1.05

/**
 * 相簿燈箱本體：全視窗滿版遮罩，左右箭頭鈕／鍵盤左右鍵／滑動手勢三種方式皆可切圖，
 * Esc 關閉，焦點以 cdkTrapFocus 鎖在燈箱內。由 GalleryComponent 透過 CDK Overlay 掛載。
 *
 * 箭頭鈕桌機與手機都顯示——滑動手勢不是人人知道，鍵盤操作又沒有任何視覺提示，
 * 賓客單靠這兩者猜不到怎麼換圖。第一張／最後一張時對應箭頭用 disabled 停用並降低透明度，
 * 不用 display:none 隱藏，否則鍵盤 Tab 的焦點順序會在首末張之間跳動。
 */
@Component({
  selector: 'app-lightbox',
  imports: [IconComponent, A11yModule, WebpSrcsetPipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="lightbox" cdkTrapFocus cdkTrapFocusAutoCapture (click)="onBackdropClick($event)">
      <button type="button" class="lightbox__close" aria-label="關閉燈箱" (click)="close.emit()">
        <app-icon name="x" [size]="24" color="#FFFFFF" />
      </button>

      <button
        type="button"
        class="lightbox__arrow lightbox__arrow--prev"
        aria-label="上一張"
        [attr.aria-disabled]="isFirst() ? 'true' : null"
        [disabled]="isFirst()"
        (click)="prev.emit()"
      >
        <app-icon name="chevron-left" [size]="24" color="#FFFFFF" />
      </button>

      <picture class="webp-picture">
        <source type="image/webp" [attr.srcset]="photo().url | webpSrcset" sizes="(min-width: 760px) 720px, calc(100vw - 40px)" />
        <img
          class="lightbox__image"
          [src]="photo().url"
          [alt]="photo().alt"
          (touchstart)="onTouchStart($event)"
          (touchend)="onTouchEnd($event)"
          (touchcancel)="onTouchCancel()"
        />
      </picture>

      <button
        type="button"
        class="lightbox__arrow lightbox__arrow--next"
        aria-label="下一張"
        [attr.aria-disabled]="isLast() ? 'true' : null"
        [disabled]="isLast()"
        (click)="next.emit()"
      >
        <app-icon name="chevron-right" [size]="24" color="#FFFFFF" />
      </button>

      <p class="lightbox__page" aria-live="polite">{{ index() + 1 }} / {{ total() }}</p>
    </div>
  `,
  styles: `
    .lightbox {
      position: fixed;
      inset: 0;
      z-index: 1000;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--color-overlay-dark);
    }

    .lightbox__close {
      position: absolute;
      top: 16px;
      right: 16px;
      width: 44px;
      height: 44px;
      display: flex;
      align-items: center;
      justify-content: center;
      border: none;
      background: transparent;
      cursor: pointer;
    }

    .lightbox__arrow {
      position: absolute;
      top: 50%;
      transform: translateY(-50%);
      width: 44px;
      height: 44px;
      border-radius: 22px;
      border: none;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--color-overlay-dark);
      cursor: pointer;
      transition: opacity 200ms;

      &:disabled {
        opacity: 0.35;
        cursor: default;
      }

      &:focus-visible {
        outline: 2px solid var(--color-text-invert);
        outline-offset: 2px;
      }
    }

    .lightbox__arrow--prev {
      left: 16px;
    }

    .lightbox__arrow--next {
      right: 16px;
    }

    .lightbox__image {
      width: calc(100% - 40px);
      max-width: 720px;
      max-height: 78vh;
      object-fit: contain;
      border-radius: 12px;
    }

    .lightbox__page {
      position: absolute;
      bottom: 32px;
      left: 0;
      right: 0;
      margin: 0;
      text-align: center;
      font-size: 13px;
      font-weight: 500;
      letter-spacing: 2px;
      color: var(--color-text-invert);
    }
  `,
})
export class LightboxComponent {
  readonly photo = input.required<GalleryPhoto>()
  readonly index = input.required<number>()
  readonly total = input.required<number>()

  readonly close = output<void>()
  readonly next = output<void>()
  readonly prev = output<void>()

  protected readonly isFirst = computed(() => this.index() === 0)
  protected readonly isLast = computed(() => this.index() === this.total() - 1)

  /** 這次單指滑動的起點；null 表示這次手勢不算換圖（雙指捏放、或頁面已放大）。 */
  private swipeStart: { x: number; y: number; id: number } | null = null

  @HostListener('document:keydown', ['$event'])
  onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Escape') this.close.emit()
    if (event.key === 'ArrowRight') this.next.emit()
    if (event.key === 'ArrowLeft') this.prev.emit()
  }

  onBackdropClick(event: MouseEvent): void {
    if (event.target === event.currentTarget) this.close.emit()
  }

  /**
   * 只有「頁面沒放大時的單指橫滑」才換圖。
   * 第二根手指一放上來就是在捏放，整段手勢作廢——放開時先離開的那根手指常帶著橫向位移，
   * 以前會被當成滑動而換到上一張或下一張。放大後的單指拖動是在移動畫面看細節，同樣不換圖。
   */
  onTouchStart(event: TouchEvent): void {
    const zoomed = (window.visualViewport?.scale ?? 1) > ZOOMED_SCALE
    if (event.touches.length > 1 || zoomed) {
      this.swipeStart = null
      return
    }
    const touch = event.changedTouches[0]
    this.swipeStart = { x: touch.clientX, y: touch.clientY, id: touch.identifier }
  }

  onTouchCancel(): void {
    this.swipeStart = null
  }

  onTouchEnd(event: TouchEvent): void {
    const start = this.swipeStart
    const touch = Array.from(event.changedTouches).find((t) => t.identifier === start?.id)
    if (!start || !touch) return
    this.swipeStart = null

    const dx = touch.clientX - start.x
    const dy = touch.clientY - start.y
    if (Math.abs(dx) < SWIPE_THRESHOLD_PX || Math.abs(dx) <= Math.abs(dy)) return
    if (dx > 0) this.prev.emit()
    else this.next.emit()
  }
}
