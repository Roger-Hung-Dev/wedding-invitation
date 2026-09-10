import { ChangeDetectionStrategy, Component, DestroyRef, computed, inject } from '@angular/core'
import { STORY_TEXT } from '../../core/config/wedding-content'
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
 * 手機單頁的翻頁時長，對應 scss 的 story-card-flip-*。
 * 比桌機短：紙在原地翻，視覺移動距離比桌機那張橫跨書脊的紙小得多，用 900ms 會拖。
 */
const CARD_TURN_DURATION_MS = 800

/** 要求減少動態效果時改成交叉淡入淡出，時長同步縮短。 */
const REDUCED_TURN_DURATION_MS = 200

/**
 * 底層那一半換成新頁的時機，佔整段翻頁的比例。
 *
 * 桌機：必須等於 story.component.scss 的 story-flip-fade 開始淡出的那個百分比（85%），不可以各改各的。
 * 早於它換，紙還沒完全蓋住底層，換頁會被看見；
 * 晚於它換，翻頁層已經開始淡出、露出的還是舊頁，翻完才跳成新頁 —— 那是「翻完後閃一下」。
 *
 * 手機沒有淡出那一段，紙直接翻到底再移除，這個比例代表「紙已經轉得夠開、幾乎蓋滿底層」，
 * 同樣是換頁不會被看見的時機，所以共用同一個值。
 */
const BASE_SWAP_RATIO = 0.85

/** 翻頁鈕內箭頭的尺寸，手機 16、桌機 20。 */
const ICON_SIZE_MOBILE = 16
const ICON_SIZE_DESKTOP = 20

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
  private turnTimer: ReturnType<typeof setTimeout> | null = null
  private swapTimer: ReturnType<typeof setTimeout> | null = null

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

  constructor() {
    this.destroyRef.onDestroy(() => this.clearTimer())
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

    const duration = this.breakpoint.isDesktop() ? TURN_DURATION_MS : CARD_TURN_DURATION_MS
    const swapDelay = Math.round(duration * BASE_SWAP_RATIO)

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
   * 鍵盤與報讀器走的是翻頁鈕那條路，所以按鈕不能因為有了手勢就拿掉。
   */
  protected onSwipeStart(event: PointerEvent): void {
    if (event.pointerType !== 'touch' || !event.isPrimary) {
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

  private clearTimer(): void {
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
