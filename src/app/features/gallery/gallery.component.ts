import { ComponentType, Overlay, OverlayRef } from '@angular/cdk/overlay'
import { ComponentPortal } from '@angular/cdk/portal'
import { ChangeDetectionStrategy, Component, ComponentRef, DestroyRef, ElementRef, computed, effect, inject, viewChild } from '@angular/core'
import { BreakpointService } from '../../shared/breakpoint.service'
import { ScrollRevealDirective } from '../../shared/scroll-reveal.directive'
import { SectionHeadingComponent } from '../../shared/section-heading/section-heading.component'
import { GalleryStore } from './gallery.store'
import { LightboxComponent } from './lightbox/lightbox.component'

/**
 * S2 婚紗藝廊區。手機為橫向滑動輪播（scroll-snap，僅可見主卡與左右鄰卡邊緣），
 * 桌機改為三張並排靜態展示、無滑動手勢。兩種版式皆可點擊照片開啟燈箱。
 */
@Component({
  selector: 'app-gallery',
  imports: [SectionHeadingComponent, ScrollRevealDirective],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './gallery.component.html',
  styleUrl: './gallery.component.scss',
})
export class GalleryComponent {
  protected readonly store = inject(GalleryStore)
  protected readonly breakpoint = inject(BreakpointService)
  private readonly overlay = inject(Overlay)
  private readonly destroyRef = inject(DestroyRef)

  private readonly track = viewChild<ElementRef<HTMLElement>>('track')

  /** 桌機並排展示只取前 3 張（分析檔桌機分鏡明訂三張並排，不是輪播）。 */
  protected readonly desktopPhotos = computed(() => this.store.photos.slice(0, 3))

  private overlayRef: OverlayRef | null = null
  private lightboxRef: ComponentRef<LightboxComponent> | null = null

  constructor() {
    // 燈箱開闔與換圖全交給這個 effect 統一處理，避免在多個互動入口各自呼叫 Overlay API。
    // 注意：effect() 內不得再呼叫 effect()，換圖時的 input 更新直接在同一個 effect 裡做，不額外開一個。
    effect(() => {
      const index = this.store.lightboxIndex()
      if (index === null) {
        this.overlayRef?.dispose()
        this.overlayRef = null
        this.lightboxRef = null
        return
      }

      if (!this.lightboxRef) {
        this.lightboxRef = this.openOverlay()
      }
      this.lightboxRef.setInput('photo', this.store.photos[index])
      this.lightboxRef.setInput('index', index)
      this.lightboxRef.setInput('total', this.store.photos.length)
    })
    this.destroyRef.onDestroy(() => this.overlayRef?.dispose())
  }

  private openOverlay(): ComponentRef<LightboxComponent> {
    this.overlayRef = this.overlay.create({
      hasBackdrop: false,
      scrollStrategy: this.overlay.scrollStrategies.block(),
      positionStrategy: this.overlay.position().global().centerHorizontally().centerVertically(),
    })

    const portal = new ComponentPortal(LightboxComponent as ComponentType<LightboxComponent>)
    const componentRef = this.overlayRef.attach(portal)

    componentRef.instance.close.subscribe(() => this.store.closeLightbox())
    componentRef.instance.next.subscribe(() => this.store.showNext())
    componentRef.instance.prev.subscribe(() => this.store.showPrev())

    return componentRef
  }

  onTrackScroll(): void {
    const el = this.track()?.nativeElement
    if (!el) return
    const cardWidth = el.scrollWidth / this.store.photos.length
    const index = Math.round(el.scrollLeft / cardWidth)
    this.store.setActiveIndex(Math.min(Math.max(index, 0), this.store.photos.length - 1))
  }
}
