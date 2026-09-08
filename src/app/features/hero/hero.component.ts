import { ChangeDetectionStrategy, Component, ElementRef, afterNextRender, inject, signal, viewChild } from '@angular/core'
import { BreakpointService } from '../../shared/breakpoint.service'
import { ReducedMotionService } from '../../shared/reduced-motion.service'
import { HERO_IMAGE_DESKTOP_URL, HERO_IMAGE_URL, HERO_TEXT, WEDDING_CONTENT } from '../../core/config/wedding-content'
import { padTwoDigits } from '../../core/date.util'
import { HeroStore } from './hero.store'
import { MusicPlayerComponent } from '../music-player/music-player.component'

/**
 * S1 主視覺封面區。是進站第一印象，入場動畫在頁面載入完成即播放，
 * 不像其他段落等待捲動觸發；底圖只在桌機（≥1024px）啟用視差。
 */
@Component({
  selector: 'app-hero',
  imports: [MusicPlayerComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './hero.component.html',
  styleUrl: './hero.component.scss',
})
export class HeroComponent {
  protected readonly store = inject(HeroStore)
  protected readonly breakpoint = inject(BreakpointService)
  private readonly reducedMotion = inject(ReducedMotionService)

  protected readonly heroImageUrl = HERO_IMAGE_URL
  protected readonly heroImageDesktopUrl = HERO_IMAGE_DESKTOP_URL
  protected readonly content = WEDDING_CONTENT
  protected readonly text = HERO_TEXT
  protected readonly padTwoDigits = padTwoDigits

  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef)
  private readonly bgImage = viewChild.required<ElementRef<HTMLElement>>('heroBg')

  /** Hero 入場序列不等捲動觸發，載入後立刻切成 true 播放一次；各元素的交錯延遲寫在樣板與樣式表。 */
  protected readonly loaded = signal(false)

  constructor() {
    afterNextRender(() => {
      requestAnimationFrame(() => this.loaded.set(true))
      this.bindParallax()
    })
  }

  /**
   * 捲到下一個區塊。取的是宿主元素 <app-hero> 的下一個兄弟（也就是 <app-gallery>）——
   * 不能取 section.hero 的兄弟，那個 section 是元件內唯一的子元素，往下找不到東西。
   */
  scrollToNext(): void {
    const next = this.host.nativeElement.nextElementSibling
    next?.scrollIntoView({ behavior: this.reducedMotion.prefersReduced() ? 'auto' : 'smooth' })
  }

  /**
   * 只在桌機啟用底圖視差，位移量夾在 120px 內。
   * 行動裝置的 scroll 節流不穩定容易抖動、且小螢幕更易誘發暈眩，因此手機關閉。
   */
  private bindParallax(): void {
    if (!this.breakpoint.isDesktop() || this.reducedMotion.prefersReduced()) return

    let ticking = false
    window.addEventListener(
      'scroll',
      () => {
        if (ticking) return
        ticking = true
        requestAnimationFrame(() => {
          const offset = Math.min(window.scrollY * 0.3, 120)
          this.bgImage().nativeElement.style.transform = `translateY(${offset}px)`
          ticking = false
        })
      },
      { passive: true },
    )
  }
}
