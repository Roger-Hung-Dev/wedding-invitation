import { ComponentType, Overlay, OverlayRef } from '@angular/cdk/overlay'
import { ComponentPortal } from '@angular/cdk/portal'
import { ChangeDetectionStrategy, Component, ComponentRef, DestroyRef, ElementRef, afterNextRender, computed, effect, inject, signal, viewChild } from '@angular/core'
import { BreakpointService } from '../../shared/breakpoint.service'
import { ReducedMotionService } from '../../shared/reduced-motion.service'
import { ScrollRevealDirective } from '../../shared/scroll-reveal.directive'
import { SectionHeadingComponent } from '../../shared/section-heading/section-heading.component'
import { GALLERY_TEXT, GalleryPhoto } from '../../core/config/wedding-content'
import { GalleryStore } from './gallery.store'
import { LightboxComponent } from './lightbox/lightbox.component'
import { WebpSrcsetPipe } from '../../shared/webp-srcset.pipe'

/**
 * 自動捲動軌道的版面數值，與 gallery.component.scss 的 $gallery-marquee-card-width／
 * $gallery-marquee-gap 為同一組數字，改樣式時兩邊要一起改，否則接縫會對不齊。
 */
const MARQUEE_CARD_WIDTH_PX = 360
const MARQUEE_GAP_PX = 20

/** 捲動速度，每秒位移的像素。 */
const MARQUEE_SPEED_PX_PER_SEC = 30

/**
 * 相簿離畫面還有多遠時，無論如何都要開始下載（約兩個手機畫面高）。
 * 平常會更早開始（網頁載完、瀏覽器空下來就開始，見 schedulePreload），這一條是給捲得很快的賓客的保底。
 */
const PRELOAD_MARGIN = '1600px 0px'

/** 網頁載入完成後再等多久才開始在背景抓相簿照片，讓封面照先解碼、畫面先穩定。 */
const IDLE_PRELOAD_DELAY_MS = 1200

/** 第一批照片遲遲載不完時（網路很慢），最多等這麼久就接著抓其餘照片，不讓後面的照片永遠卡住。 */
const FIRST_BATCH_TIMEOUT_MS = 4000

/** 手機輪播一開始看得到主卡與右側鄰卡，第一批抓這兩張。 */
const MOBILE_FIRST_BATCH = 2

/** 減少動態效果時的桌機靜態網格，第一列三張。 */
const GRID_FIRST_BATCH = 3

type PreloadStage = 'idle' | 'first' | 'all'
type GalleryLayout = 'track' | 'marquee' | 'grid'

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
  imports: [SectionHeadingComponent, ScrollRevealDirective, WebpSrcsetPipe],
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

  private readonly reducedMotion = inject(ReducedMotionService)
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef)

  /**
   * 相簿照片的下載進度，分兩批：
   * - idle：還沒開始，全部維持 lazy，不跟首屏的封面照搶頻寬。
   * - first：先抓「一進相簿就看得到」的那幾張，並提高優先權。
   * - all：第一批到齊（或等太久）後，其餘照片全部改成 eager 接著抓。
   *
   * 不能一開始就 17 張一起抓：頻寬被平分，每張都一樣慢，畫面會整排空白很久再同時跳出來；
   * 也不能全靠 lazy：自動捲動的照片要等捲進畫面邊緣才下載，會一張一張補上。
   */
  private readonly preloadStage = signal<PreloadStage>('idle')

  /** 第一批的張數，開始預載時依版式與視窗寬度決定。 */
  private firstBatchSize = 0

  /** 第一批已經載入的照片索引（桌機自動捲動有複製份，同一張會觸發兩次，所以用 Set）。 */
  private readonly firstBatchLoaded = new Set<number>()

  private firstBatchTimer: ReturnType<typeof setTimeout> | null = null

  /** 目前實際顯示的版式。另外兩種是 display: none，不能改成 eager，否則會白白多抓一整套照片。 */
  private readonly activeLayout = computed<GalleryLayout>(() => {
    if (!this.breakpoint.isDesktop()) return 'track'
    return this.reducedMotion.prefersReduced() ? 'grid' : 'marquee'
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

    afterNextRender(() => this.schedulePreload())
    this.destroyRef.onDestroy(() => {
      if (this.firstBatchTimer) clearTimeout(this.firstBatchTimer)
    })
  }

  /** 樣板用：某個版式的第 index 張照片現在該不該立刻下載。 */
  protected photoLoading(layout: GalleryLayout, index: number): 'eager' | 'lazy' {
    const stage = this.preloadStage()
    if (stage === 'idle' || layout !== this.activeLayout()) return 'lazy'
    return stage === 'all' || index < this.firstBatchSize ? 'eager' : 'lazy'
  }

  /** 樣板用：第一批提高下載優先權，其餘維持 low，免得跟頁面其他資源搶。 */
  protected photoPriority(index: number): 'high' | 'low' {
    return this.preloadStage() !== 'idle' && index < this.firstBatchSize ? 'high' : 'low'
  }

  /** 樣板用：照片載入完成。第一批到齊就接著抓其餘照片。 */
  protected onPhotoLoad(index: number): void {
    if (this.preloadStage() !== 'first' || index >= this.firstBatchSize) return
    this.firstBatchLoaded.add(index)
    if (this.firstBatchLoaded.size >= this.firstBatchSize) this.loadAll()
  }

  /**
   * 兩個時機擇先觸發：網頁載完、瀏覽器空下來（多數賓客捲到相簿前照片早就好了），
   * 或是相簿已經接近畫面（捲得很快、網頁還沒載完的保底）。
   */
  private schedulePreload(): void {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) this.startPreload()
      },
      { rootMargin: PRELOAD_MARGIN },
    )
    observer.observe(this.host.nativeElement)

    let idleTimer: ReturnType<typeof setTimeout> | null = null
    const onLoad = (): void => {
      idleTimer = setTimeout(() => this.startPreload(), IDLE_PRELOAD_DELAY_MS)
    }
    if (document.readyState === 'complete') onLoad()
    else window.addEventListener('load', onLoad, { once: true })

    this.destroyRef.onDestroy(() => {
      observer.disconnect()
      window.removeEventListener('load', onLoad)
      if (idleTimer) clearTimeout(idleTimer)
    })
  }

  private startPreload(): void {
    if (this.preloadStage() !== 'idle') return
    const total = this.store.photos.length
    const layout = this.activeLayout()
    // 桌機自動捲動一開始看得到的張數 = 視窗寬 ÷ (卡寬 + 間距)，再多抓一張補右緣正要捲進來的那張。
    const visible =
      layout === 'marquee'
        ? Math.ceil(window.innerWidth / (MARQUEE_CARD_WIDTH_PX + MARQUEE_GAP_PX)) + 1
        : layout === 'grid'
          ? GRID_FIRST_BATCH
          : MOBILE_FIRST_BATCH
    this.firstBatchSize = Math.min(total, visible)
    this.preloadStage.set('first')
    this.firstBatchTimer = setTimeout(() => this.loadAll(), FIRST_BATCH_TIMEOUT_MS)
  }

  private loadAll(): void {
    if (this.firstBatchTimer) clearTimeout(this.firstBatchTimer)
    this.firstBatchTimer = null
    this.preloadStage.set('all')
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
