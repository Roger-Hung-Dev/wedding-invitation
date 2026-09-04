import { A11yModule } from '@angular/cdk/a11y'
import { ChangeDetectionStrategy, Component, HostListener, computed, input, output } from '@angular/core'
import { IconComponent } from '../../../shared/icon/icon.component'
import { GalleryPhoto } from '../../../core/config/wedding-content'

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
  imports: [IconComponent, A11yModule],
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

      <img
        class="lightbox__image"
        [src]="photo().url"
        [alt]="photo().alt"
        (touchstart)="onTouchStart($event)"
        (touchend)="onTouchEnd($event)"
      />

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

  private touchStartX = 0

  @HostListener('document:keydown', ['$event'])
  onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Escape') this.close.emit()
    if (event.key === 'ArrowRight') this.next.emit()
    if (event.key === 'ArrowLeft') this.prev.emit()
  }

  onBackdropClick(event: MouseEvent): void {
    if (event.target === event.currentTarget) this.close.emit()
  }

  onTouchStart(event: TouchEvent): void {
    this.touchStartX = event.changedTouches[0].clientX
  }

  onTouchEnd(event: TouchEvent): void {
    const deltaX = event.changedTouches[0].clientX - this.touchStartX
    const swipeThreshold = 48
    if (deltaX > swipeThreshold) this.prev.emit()
    else if (deltaX < -swipeThreshold) this.next.emit()
  }
}
