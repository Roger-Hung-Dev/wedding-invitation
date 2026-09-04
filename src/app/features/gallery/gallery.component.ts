import { ComponentType, Overlay, OverlayRef } from '@angular/cdk/overlay'
import { ComponentPortal } from '@angular/cdk/portal'
import { ChangeDetectionStrategy, Component, ComponentRef, DestroyRef, ElementRef, computed, effect, inject, viewChild } from '@angular/core'
import { BreakpointService } from '../../shared/breakpoint.service'
import { ScrollRevealDirective } from '../../shared/scroll-reveal.directive'
import { SectionHeadingComponent } from '../../shared/section-heading/section-heading.component'
import { GALLERY_TEXT, GalleryPhoto } from '../../core/config/wedding-content'
import { GalleryStore } from './gallery.store'
import { LightboxComponent } from './lightbox/lightbox.component'

export interface MarqueeItem {
  readonly key: string
  readonly photo: GalleryPhoto
  /** 對應 store.photos 的原始索引，複製份也要指回原始索引，開燈箱才不會開錯張。 */
  readonly originalIndex: number
  /** 複製份不接受鍵盤焦點、對螢幕報讀軟體隱藏，避免同一張照片在無障礙樹裡被唸兩次。 */
  readonly isDuplicate: boolean
}

/**
 * S2 婚紗藝廊區。手機為橫向滑動輪播（scroll-snap，僅可見主卡與左右鄰卡邊緣）。
 * 桌機預設為無縫自動橫向捲動（CSS animation，滑鼠停留或鍵盤聚焦時暫停）；
 * 使用者要求減少動態效果時，改用靜態 3＋2 兩列展示（見 gallery.component.scss 的
 * prefers-reduced-motion 覆寫），確保五張照片仍然全部一次看得到，不會因為捲動停用
 * 而永遠只看得到當下那幾張。兩種版式皆可點擊照片開啟燈箱。
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
  protected readonly text = GALLERY_TEXT
  private readonly overlay = inject(Overlay)
  private readonly destroyRef = inject(DestroyRef)

  private readonly track = viewChild<ElementRef<HTMLElement>>('track')

  /**
   * 桌機自動捲動軌道：把照片序列複製一份接在後面做成 10 張，動畫跑完第一份的寬度就重置，
   * 視覺上看不出接縫。複製份的 originalIndex 指回 0～4，點擊才會開對照片。
   */
  protected readonly marqueeItems = computed<MarqueeItem[]>(() => {
    const photos = this.store.photos
    return [...photos, ...photos].map((photo, i) => ({
      key: `${photo.id}-${i < photos.length ? 'a' : 'b'}`,
      photo,
      originalIndex: i % photos.length,
      isDuplicate: i >= photos.length,
    }))
  })

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
