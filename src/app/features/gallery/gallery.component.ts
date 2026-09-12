import { ComponentType, Overlay, OverlayRef } from '@angular/cdk/overlay'
import { ComponentPortal } from '@angular/cdk/portal'
import { ChangeDetectionStrategy, Component, ComponentRef, DestroyRef, ElementRef, afterNextRender, computed, effect, inject, signal, viewChild } from '@angular/core'
import { BreakpointService } from '../../shared/breakpoint.service'
import { ScrollRevealDirective } from '../../shared/scroll-reveal.directive'
import { SectionHeadingComponent } from '../../shared/section-heading/section-heading.component'
import { GALLERY_TEXT, GalleryPhoto } from '../../core/config/wedding-content'
import { GalleryStore } from './gallery.store'
import { LightboxComponent } from './lightbox/lightbox.component'

/**
 * 自動捲動軌道的版面數值，與 gallery.component.scss 的 $gallery-marquee-card-width／
 * $gallery-marquee-gap 為同一組數字，改樣式時兩邊要一起改，否則接縫會對不齊。
 */
const MARQUEE_CARD_WIDTH_PX = 360
const MARQUEE_GAP_PX = 20

/** 捲動速度，每秒位移的像素。 */
const MARQUEE_SPEED_PX_PER_SEC = 30

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
 * 桌機預設為無縫自動橫向捲動（CSS animation，滑鼠停留、鍵盤走訪或燈箱開著時暫停），
 * 捲動距離與時長依實際照片張數算出，增減照片不必改樣式；
 * 使用者要求減少動態效果時，改用每列三張的靜態網格（見 gallery.component.scss 的
 * prefers-reduced-motion 覆寫），確保所有照片仍然一次看得到，不會因為捲動停用
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
   * 焦點是不是「使用者按 Tab 走進來」的。
   *
   * 不能用 CSS 的 :focus-within 或 :has(:focus-visible) —— 那兩個偽類分不出
   * 「使用者按 Tab 進來」與「程式把焦點還原回去」。滑鼠點一張照片會讓那顆 button 取得焦點，
   * 關掉燈箱時 CDK 又把焦點還原回它，輪播就卡在暫停，要再點一次別處才會動。
   * （:focus-visible 也擋不住，實測還原焦點時 Chrome 仍判定它是 focus-visible。）
   *
   * 所以改追蹤「進入焦點前的最後一次互動是不是 Tab」：滑鼠點擊與關閉燈箱的焦點還原
   * 都不算，只有鍵盤走訪會讓輪播停下來。
   */
  private readonly keyboardFocused = signal(false)

  /** 進入焦點前的最後一次互動是不是按 Tab。純旗標，不需要觸發變更偵測。 */
  private lastInputWasTab = false

  /** 燈箱開著時背景不該繼續跑；鍵盤走訪時要能停下來（WCAG 2.2.2）。滑鼠停留那一路留在 CSS。 */
  protected readonly marqueePaused = computed(
    () => this.store.lightboxIndex() !== null || this.keyboardFocused(),
  )

  /**
   * 桌機自動捲動軌道：把照片序列複製一份接在後面，動畫跑完第一份的寬度就重置，
   * 視覺上看不出接縫。複製份的 originalIndex 指回原始索引，點擊才會開對照片。
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

  /**
   * 自動捲動一份序列要位移的距離，即「張數 × (卡寬 + 卡間距)」——
   * 位移到這個距離時，複製份的第一張正好落在原始第一張的起始位置，重置回 0 才沒有接縫。
   * 必須依實際張數算，寫死會在增減照片後跑到一半就跳回開頭（看起來像閃一下重播）。
   */
  protected readonly marqueeShift = computed(
    () => `${this.store.photos.length * (MARQUEE_CARD_WIDTH_PX + MARQUEE_GAP_PX)}px`,
  )

  /** 播放時長由位移距離與固定速度推得，照片增減時捲動快慢維持一致。 */
  protected readonly marqueeDuration = computed(
    () =>
      `${Math.round(
        (this.store.photos.length * (MARQUEE_CARD_WIDTH_PX + MARQUEE_GAP_PX)) / MARQUEE_SPEED_PX_PER_SEC,
      )}s`,
  )

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
    // 直接掛在 document 上而不是用樣板的事件綁定：這兩個只是更新一個旗標，
    // 走 Angular 的事件綁定會讓每一次按鍵都跑一輪變更偵測。
    afterNextRender(() => {
      const onKeydown = (event: KeyboardEvent) => {
        if (event.key === 'Tab') this.lastInputWasTab = true
      }
      const onPointerDown = () => {
        this.lastInputWasTab = false
      }
      document.addEventListener('keydown', onKeydown, true)
      document.addEventListener('pointerdown', onPointerDown, true)
      this.destroyRef.onDestroy(() => {
        document.removeEventListener('keydown', onKeydown, true)
        document.removeEventListener('pointerdown', onPointerDown, true)
      })
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

  /** 焦點走進相片區。只有這一步之前剛按過 Tab 才算鍵盤走訪。 */
  onMarqueeFocusIn(): void {
    this.keyboardFocused.set(this.lastInputWasTab)
  }

  onMarqueeFocusOut(): void {
    this.keyboardFocused.set(false)
  }

  onTrackScroll(): void {
    const el = this.track()?.nativeElement
    if (!el) return
    const cardWidth = el.scrollWidth / this.store.photos.length
    const index = Math.round(el.scrollLeft / cardWidth)
    this.store.setActiveIndex(Math.min(Math.max(index, 0), this.store.photos.length - 1))
  }
}
