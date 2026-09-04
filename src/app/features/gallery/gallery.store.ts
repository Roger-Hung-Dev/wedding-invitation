import { Injectable, signal } from '@angular/core'
import { GALLERY_PHOTOS, GalleryPhoto } from '../../core/config/wedding-content'

/**
 * 婚紗藝廊狀態：手機輪播的目前頁與燈箱開闔／目前顯示的照片索引。
 */
@Injectable({ providedIn: 'root' })
export class GalleryStore {
  readonly photos: readonly GalleryPhoto[] = GALLERY_PHOTOS

  private readonly _activeIndex = signal(0)
  readonly activeIndex = this._activeIndex.asReadonly()

  private readonly _lightboxIndex = signal<number | null>(null)
  readonly lightboxIndex = this._lightboxIndex.asReadonly()

  setActiveIndex(index: number): void {
    this._activeIndex.set(index)
  }

  openLightbox(index: number): void {
    this._lightboxIndex.set(index)
  }

  closeLightbox(): void {
    this._lightboxIndex.set(null)
  }

  /** 到最後一張時停住，不循環回第一張——燈箱箭頭鈕在邊界要能正確顯示停用態。 */
  showNext(): void {
    this._lightboxIndex.update((i) => (i === null ? i : Math.min(i + 1, this.photos.length - 1)))
  }

  /** 到第一張時停住，不循環回最後一張，理由同 showNext。 */
  showPrev(): void {
    this._lightboxIndex.update((i) => (i === null ? i : Math.max(i - 1, 0)))
  }
}
