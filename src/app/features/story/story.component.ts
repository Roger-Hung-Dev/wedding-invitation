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
 * 翻頁動畫時長，與 story.component.scss 的 story-turn-*／story-page-* 動畫時長為同一組數字，
 * 改一邊就要改另一邊，否則畫面已經翻完了卻還鎖著輸入（或反過來，翻到一半就能再點）。
 */
const TURN_DURATION_MS = 600

/** 要求減少動態效果時改成交叉淡入淡出，時長同步縮短。 */
const REDUCED_TURN_DURATION_MS = 200

/** 翻頁鈕內箭頭的尺寸，手機 16、桌機 20。 */
const ICON_SIZE_MOBILE = 16
const ICON_SIZE_DESKTOP = 20

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

  /** 頁點列對報讀器隱藏，改由這一句視覺隱藏的文字報出目前頁次。 */
  protected readonly pageStatus = computed(() =>
    this.text.pageStatus
      .replace('{{current}}', String(this.store.index() + 1))
      .replace('{{total}}', String(this.store.pages.length)),
  )

  protected readonly iconSize = computed(() =>
    this.breakpoint.isDesktop() ? ICON_SIZE_DESKTOP : ICON_SIZE_MOBILE,
  )

  constructor() {
    this.destroyRef.onDestroy(() => this.clearTimer())
  }

  protected turn(direction: StoryTurnDirection): void {
    if (!this.store.startTurn(direction)) return

    this.clearTimer()
    const duration = this.reducedMotion.prefersReduced() ? REDUCED_TURN_DURATION_MS : TURN_DURATION_MS
    this.turnTimer = setTimeout(() => {
      this.turnTimer = null
      this.store.endTurn()
    }, duration)
  }

  /**
   * 照片本身也是翻頁區：點左半往前翻、點右半往後翻。
   * 手機上大目標比小按鈕好按；鍵盤與報讀器走的是翻頁鈕那條路，這裡只服務滑鼠與觸控。
   */
  protected onPhotoClick(event: MouseEvent): void {
    const bounds = (event.currentTarget as HTMLElement).getBoundingClientRect()
    this.turn(event.clientX - bounds.left < bounds.width / 2 ? 'prev' : 'next')
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
  }
}
