import { A11yModule } from '@angular/cdk/a11y'
import { ChangeDetectionStrategy, Component, HostListener, input, output } from '@angular/core'
import { IconComponent } from '../../../shared/icon/icon.component'
import { GalleryPhoto } from '../../../core/config/wedding-content'

/**
 * 相簿燈箱本體：全視窗滿版遮罩，鍵盤左右鍵／滑動切圖、Esc 關閉，
 * 焦點以 cdkTrapFocus 鎖在燈箱內。由 GalleryComponent 透過 CDK Overlay 掛載。
 *
 * 換圖方式未於設計稿定義，本站採「滑動手勢 + 鍵盤左右鍵」、不加額外箭頭 icon 以維持視覺乾淨，
 * 屬工程假設而非既定規格。
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

      <img
        class="lightbox__image"
        [src]="photo().url"
        [alt]="photo().alt"
        (touchstart)="onTouchStart($event)"
        (touchend)="onTouchEnd($event)"
      />

      <p class="lightbox__page">{{ index() + 1 }} / {{ total() }}</p>
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
