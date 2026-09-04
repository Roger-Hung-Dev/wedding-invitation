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

  showNext(): void {
    this._lightboxIndex.update((i) => (i === null ? i : (i + 1) % this.photos.length))
  }

  showPrev(): void {
    this._lightboxIndex.update((i) => (i === null ? i : (i - 1 + this.photos.length) % this.photos.length))
  }
}
