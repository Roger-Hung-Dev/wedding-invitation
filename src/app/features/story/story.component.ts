import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  afterNextRender,
  computed,
  inject,
  signal,
  viewChild,
} from '@angular/core'
import { STORY_TEXT } from '../../core/config/wedding-content'
import { webpSrcset } from '../../core/image-variants'
import { BreakpointService } from '../../shared/breakpoint.service'
import { IconComponent } from '../../shared/icon/icon.component'
import { ReducedMotionService } from '../../shared/reduced-motion.service'
import { ScrollRevealDirective } from '../../shared/scroll-reveal.directive'
import { SectionHeadingComponent } from '../../shared/section-heading/section-heading.component'
import { StoryPageComponent } from './story-page/story-page.component'
import { StoryStore, StoryTurnDirection } from './story.store'

/**
 * 桌機雙頁的翻頁時長，與 story.component.scss 的 story-turn-* 動畫時長為同一組數字，
 * 改一邊就要改另一邊，否則畫面已經翻完了卻還鎖著輸入（或反過來，翻到一半就能再點）。
 */
const TURN_DURATION_MS = 900

/**
 * 手機單頁的翻頁時長（掀書角），paintPeel 依這個時長換算每一幀的進度。
 * 摺線要掃過整條對角線，走得比原地翻面遠，短於這個值看起來會像紙被扯走。
 */
const CARD_TURN_DURATION_MS = 900

/** 要求減少動態效果時改成交叉淡入淡出，時長同步縮短。 */
const REDUCED_TURN_DURATION_MS = 200

/**
 * 底層那一半換成新頁的時機，佔整段翻頁的比例。
 *
 * 桌機：必須等於 story.component.scss 的 story-flip-fade 開始淡出的那個百分比（85%），不可以各改各的。
 * 早於它換，紙還沒完全蓋住底層，換頁會被看見；
 * 晚於它換，翻頁層已經開始淡出、露出的還是舊頁，翻完才跳成新頁 —— 那是「翻完後閃一下」。
 *
 * 手機的掀書角整層不透明、把底層整個蓋住，底層何時換都不會被看見，共用同一個值即可。
 */
const BASE_SWAP_RATIO = 0.85

/** 翻頁鈕內箭頭的尺寸，手機 16、桌機 20。 */
const ICON_SIZE_MOBILE = 16
const ICON_SIZE_DESKTOP = 20

/**
 * 故事書離畫面還有多遠就開始預先下載五頁的照片。
 * 賓客往下捲到這一段之前就抓好，第一次翻頁時才不會等照片下載。
 */
const PRELOAD_MARGIN = '800px 0px'

/** 與 story-page 樣板上 source 的 sizes 相同，預先下載的才會是翻頁時實際用到的那個寬度。 */
const PHOTO_SIZES = '(min-width: 1024px) 340px, 278px'

/** 掀起處落在底頁上的陰影寬度，沿摺線的垂直方向量。 */
const PEEL_SHADOW_WIDTH_PX = 48

/** 陰影與紙背暗部的顏色，取書頁文字的深梅色而不是純黑，落在米白紙面上才不會髒。 */
const PEEL_SHADE_RGB = '74, 55, 66'

type PeelPoint = readonly [number, number]

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max)
}

function easeInOutCubic(t: number): number {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2
}

function toPolygon(points: readonly PeelPoint[]): string {
  return `polygon(${points.map(([x, y]) => `${x}px ${y}px`).join(', ')})`
}

/**
 * 畫出掀書角某一刻的形狀。
 *
 * 摺線是 x + y = c 這條 45 度斜線，c 從 0（左上角）走到 w + h（右下角）。
 * 往後翻 c 由大變小：上層舊頁從右下角被掀向左上；往前翻 c 由小變大：前一頁從左上角蓋回右下。
 *
 * 上層只保留摺線左上側；右下側露出底層，並在摺線旁打一道陰影；
 * 被掀起的那一塊沿摺線對折過來畫成紙背 —— 對折就是對摺線做鏡射，(x, y) 映到 (c - y, c - x)。
 * 45 度的摺線讓鏡射只是 x、y 對調再平移，不必處理任意角度的旋轉。
 *
 * 陰影與紙背的深淺乘上 sin(π × 進度)：頭尾兩端紙是平的，不該有陰影，否則開始與結束的瞬間會閃一下。
 */
function paintPeel(el: HTMLElement, direction: StoryTurnDirection, progress: number): void {
  const top = el.querySelector<HTMLElement>('.story__peel-top')
  const shadow = el.querySelector<HTMLElement>('.story__peel-shadow')
  const flap = el.querySelector<HTMLElement>('.story__peel-flap')
  if (!top || !shadow || !flap) return

  const w = el.clientWidth
  const h = el.clientHeight
  const eased = easeInOutCubic(progress)
  const c = (w + h) * (direction === 'next' ? 1 - eased : eased)

  const foldStart: PeelPoint = [Math.min(c, w), clamp(c - w, 0, h)]
  const foldEnd: PeelPoint = [clamp(c - h, 0, w), Math.min(c, h)]
  const kept: PeelPoint[] = [[0, 0], [Math.min(c, w), 0], foldStart, foldEnd, [0, Math.min(c, h)]]
  const lifted: PeelPoint[] = [foldStart, [w, clamp(c - w, 0, h)], [w, h], [clamp(c - h, 0, w), h], foldEnd]
  const back = lifted.map(([x, y]): PeelPoint => [c - y, c - x])

  // 135deg 漸層的 0 點在左上角，任一點在漸層上的位置是 (x + y) / √2，摺線因此落在 c / √2。
  const fold = c / Math.SQRT2
  const depth = Math.sin(Math.PI * progress)

  top.style.clipPath = toPolygon(kept)
  shadow.style.clipPath = toPolygon(lifted)
  shadow.style.background = `linear-gradient(135deg, rgba(${PEEL_SHADE_RGB}, ${0.32 * depth}) ${fold}px, rgba(${PEEL_SHADE_RGB}, 0) ${fold + PEEL_SHADOW_WIDTH_PX}px)`
  flap.style.clipPath = toPolygon(back)
  flap.style.background = `linear-gradient(135deg, #fdfaf7 ${fold - 160}px, #f5eee8 ${fold - 48}px, rgba(${PEEL_SHADE_RGB}, ${0.18 * depth}) ${fold}px), #f5eee8`
}

/**
 * 判定為翻頁的水平滑動距離。
 * 太小會把「想垂直捲動時手指的橫向偏移」誤判成翻頁，太大則要刻意用力滑才翻得動。
 */
const SWIPE_THRESHOLD_PX = 40

/**
 * 滑完之後多久之內不受理照片點擊。
 *
 * 手指在照片上滑動放開時，瀏覽器仍然會補一個 click，那會讓「點照片翻頁」跟著觸發，
 * 一次滑動翻兩頁。用時間戳擋掉，不用旗標——旗標在「滑動起點不在照片上、click 沒來」
 * 的情況會留到下一次點擊，變成第一次點沒反應。
 */
const SWIPE_CLICK_GUARD_MS = 400

/**
 * 雙指放大超過這個倍率就視為「正在放大看」，滑動改成移動畫面、不再翻頁。
 * 留一點餘裕而不是寫 1：放大後捏回原尺寸時，瀏覽器常停在 1.00x 附近而不是剛好 1。
 */
const ZOOMED_SCALE = 1.05

/**
 * S10 交往故事書。手機是單頁的紀念冊、桌機是雙頁展開，兩種版式都固定渲染在 DOM 中、
 * 只用 CSS 切換顯示（理由同 S2 婚紗藝廊：用 @if 依斷點抽換節點會讓已經播過的進場動畫套不上新節點）。
 *
 * 目前這一頁的內容是常駐節點、不隨翻頁重建，翻頁時才另外長出一層「正在翻過去的舊頁」——
 * 這樣進場動畫只會在第一次進入視野時播一次，翻頁不會把卡內元素的 fade-up 重播一遍。
 */
@Component({
  selector: 'app-story',
  imports: [SectionHeadingComponent, ScrollRevealDirective, IconComponent, StoryPageComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './story.component.html',
  styleUrl: './story.component.scss',
})
export class StoryComponent {
  protected readonly store = inject(StoryStore)
  protected readonly breakpoint = inject(BreakpointService)
  protected readonly reducedMotion = inject(ReducedMotionService)
  protected readonly text = STORY_TEXT

  private readonly destroyRef = inject(DestroyRef)
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef)
  private turnTimer: ReturnType<typeof setTimeout> | null = null
  private swapTimer: ReturnType<typeof setTimeout> | null = null
  private peelFrame: number | null = null

  /** 手機掀書角的那一層，只在翻頁期間存在。 */
  private readonly peelRef = viewChild<ElementRef<HTMLElement>>('peel')

  /** 頁點列對報讀器隱藏，改由這一句視覺隱藏的文字報出目前頁次。 */
  protected readonly pageStatus = computed(() =>
    this.text.pageStatus
      .replace('{{current}}', String(this.store.index() + 1))
      .replace('{{total}}', String(this.store.pages.length)),
  )

  protected readonly iconSize = computed(() =>
    this.breakpoint.isDesktop() ? ICON_SIZE_DESKTOP : ICON_SIZE_MOBILE,
  )

  /** 桌機沒有觸控，提示裡不要寫「滑動」。 */
  protected readonly hint = computed(() =>
    this.breakpoint.isDesktop() ? this.text.hintDesktop : this.text.hint,
  )

  private swipeStart: { x: number; y: number; id: number } | null = null
  private lastSwipeAt = 0

  /** 賓客目前是否用雙指把頁面放大了。放大時書上的水平滑動要讓給瀏覽器移動畫面。 */
  protected readonly pageZoomed = signal(false)

  constructor() {
    this.destroyRef.onDestroy(() => this.clearTimer())
    afterNextRender(() => {
      this.preloadPhotosWhenNear()
      this.trackPinchZoom()
    })
  }

  protected turn(direction: StoryTurnDirection): void {
    if (!this.store.startTurn(direction)) return

    this.clearTimer()

    if (this.reducedMotion.prefersReduced()) {
      // 降級版是整份舊跨頁疊上來淡出，底層全程被蓋住，不需要等時機。
      this.store.markCovered()
      this.turnTimer = setTimeout(() => {
        this.turnTimer = null
        this.store.endTurn()
      }, REDUCED_TURN_DURATION_MS)
      return
    }

    const isDesktop = this.breakpoint.isDesktop()
    const duration = isDesktop ? TURN_DURATION_MS : CARD_TURN_DURATION_MS
    const swapDelay = Math.round(duration * BASE_SWAP_RATIO)

    if (!isDesktop) this.startPeel(direction, duration)

    /*
      收尾的計時器排在換頁完成之後才起算，不是兩個各自從現在數起。

      兩個獨立的 setTimeout 在主執行緒忙碌時會各自延遲不同的量，換底層那個一旦被推遲到
      接近、甚至晚於移除翻頁層的時刻，紙一撤底層還是舊頁 —— 畫面就會殘留前一張才跳到
      下一張。巢狀之後順序與間隔都固定，不受延遲影響。
    */
    this.swapTimer = setTimeout(() => {
      this.swapTimer = null
      this.store.markCovered()

      this.turnTimer = setTimeout(() => {
        this.turnTimer = null
        this.store.endTurn()
      }, duration - swapDelay)
    }, swapDelay)
  }

  /**
   * 照片本身也是翻頁區：點左半往前翻、點右半往後翻。
   * 手機上大目標比小按鈕好按；鍵盤與報讀器走的是翻頁鈕那條路，這裡只服務滑鼠與觸控。
   */
  protected onPhotoClick(event: MouseEvent): void {
    if (Date.now() - this.lastSwipeAt < SWIPE_CLICK_GUARD_MS) return

    const bounds = (event.currentTarget as HTMLElement).getBoundingClientRect()
    this.turn(event.clientX - bounds.left < bounds.width / 2 ? 'prev' : 'next')
  }

  /**
   * 觸控滑動翻頁。一本書在手機上，直覺是用手滑而不是點小箭頭。
   *
   * 只收 touch：滑鼠拖曳在桌機是選取文字的動作，把它也當成翻頁會讓人選不到字。
   * 頁面放大時也不收：那時的水平滑動是在移動畫面找字，翻掉會讓人找不到剛才看的那一段。
   * 鍵盤與報讀器走的是翻頁鈕那條路，所以按鈕不能因為有了手勢就拿掉。
   */
  protected onSwipeStart(event: PointerEvent): void {
    if (event.pointerType !== 'touch' || !event.isPrimary || this.pageZoomed()) {
      this.swipeStart = null
      return
    }
    this.swipeStart = { x: event.clientX, y: event.clientY, id: event.pointerId }
  }

  protected onSwipeEnd(event: PointerEvent): void {
    const start = this.swipeStart
    this.swipeStart = null
    if (!start || event.pointerId !== start.id) return

    const dx = event.clientX - start.x
    const dy = event.clientY - start.y
    // 垂直位移較大時當成捲動頁面，不翻頁 —— 賓客往下讀的動作不該把書翻掉。
    if (Math.abs(dx) < SWIPE_THRESHOLD_PX || Math.abs(dx) <= Math.abs(dy)) return

    this.lastSwipeAt = Date.now()
    this.turn(dx < 0 ? 'next' : 'prev')
  }

  protected onKeydown(event: KeyboardEvent): void {
    if (event.key === 'ArrowLeft') {
      event.preventDefault()
      this.turn('prev')
      return
    }
    if (event.key === 'ArrowRight') {
      event.preventDefault()
      this.turn('next')
    }
  }

  /**
   * 逐幀畫手機的掀書角。進度以翻頁開始的時間計算，不以翻頁層出現的那一幀起算，
   * 動畫才會與收尾計時器同時結束；翻頁層還沒渲染出來的前一兩幀直接略過。
   */
  private startPeel(direction: StoryTurnDirection, duration: number): void {
    const startedAt = performance.now()
    const step = (now: number): void => {
      const progress = clamp((now - startedAt) / duration, 0, 1)
      const el = this.peelRef()?.nativeElement
      if (el) paintPeel(el, direction, progress)
      this.peelFrame = progress < 1 ? requestAnimationFrame(step) : null
    }
    this.peelFrame = requestAnimationFrame(step)
  }

  /**
   * 跟著雙指縮放更新 pageZoomed。visualViewport 的 scale 是瀏覽器的縮放倍率，
   * 捏放時會觸發 resize；不支援的瀏覽器就維持「沒放大」，行為與加這段之前相同。
   */
  private trackPinchZoom(): void {
    const viewport = window.visualViewport
    if (!viewport) return

    const update = (): void => this.pageZoomed.set(viewport.scale > ZOOMED_SCALE)
    viewport.addEventListener('resize', update)
    this.destroyRef.onDestroy(() => viewport.removeEventListener('resize', update))
    update()
  }

  /**
   * 故事書接近畫面時，先把五頁的照片都抓下來。
   * 常駐的那一頁是延遲載入，其他四頁要等翻過去才會開始下載；手機網路一慢，
   * 掀開書角時底下那頁還在下載，就會露出一片白。預先抓好之後，翻頁都是從快取取圖。
   */
  private preloadPhotosWhenNear(): void {
    const observer = new IntersectionObserver(
      (entries) => {
        if (!entries.some((entry) => entry.isIntersecting)) return
        observer.disconnect()
        for (const page of this.store.pages) {
          const img = new Image()
          img.sizes = PHOTO_SIZES
          img.srcset = webpSrcset(page.photoUrl) ?? ''
          img.src = page.photoUrl
          img.decode().catch(() => undefined)
        }
      },
      { rootMargin: PRELOAD_MARGIN },
    )
    observer.observe(this.host.nativeElement)
    this.destroyRef.onDestroy(() => observer.disconnect())
  }

  private clearTimer(): void {
    if (this.peelFrame !== null) {
      cancelAnimationFrame(this.peelFrame)
      this.peelFrame = null
    }
    if (this.turnTimer !== null) {
      clearTimeout(this.turnTimer)
      this.turnTimer = null
    }
    if (this.swapTimer !== null) {
      clearTimeout(this.swapTimer)
      this.swapTimer = null
    }
  }
}
