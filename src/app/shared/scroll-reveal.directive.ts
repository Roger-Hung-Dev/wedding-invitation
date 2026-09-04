import { isPlatformBrowser } from '@angular/common'
import { AfterViewInit, Directive, ElementRef, OnDestroy, PLATFORM_ID, inject, input } from '@angular/core'
import { ReducedMotionService } from './reduced-motion.service'

/**
 * 捲動進場動畫觸發器。以 IntersectionObserver 觀察「段落」層級的宿主元素，
 * 露出 15% 就加上 is-visible class 播放一次，播完立即 unobserve，
 * 不監聽 scroll 事件以避免逐幀觸發造成掉幀。
 */
@Directive({
  selector: '[appScrollReveal]',
})
export class ScrollRevealDirective implements AfterViewInit, OnDestroy {
  private readonly host = inject(ElementRef<HTMLElement>)
  private readonly reducedMotion = inject(ReducedMotionService)
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID))
  private observer?: IntersectionObserver

  /** 進場後要交錯延遲的子元素選擇器；未提供則只對宿主本身播放。 */
  readonly staggerSelector = input<string | null>(null)
  /** 子元素交錯間隔（毫秒），文字類元素預設 90ms。 */
  readonly staggerMs = input(90)

  ngAfterViewInit(): void {
    const el = this.host.nativeElement

    // prerender（Node 環境）沒有 IntersectionObserver，直接以終態呈現；
    // 反正 anim-ready 旗標（見 main.ts）在伺服器端本來就不會被加上，CSS 那層也會讓內容維持可見，
    // 這裡補 is-visible 只是讓靜態 HTML 的 class 狀態跟瀏覽器接手後一致，不是必要條件。
    if (!this.isBrowser || this.reducedMotion.prefersReduced()) {
      this.reveal(el)
      return
    }

    this.observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            this.reveal(el)
            this.observer?.unobserve(el)
          }
        }
      },
      { threshold: 0.15, rootMargin: '0px 0px -10% 0px' },
    )
    this.observer.observe(el)
  }

  ngOnDestroy(): void {
    this.observer?.disconnect()
  }

  private reveal(el: HTMLElement): void {
    el.classList.add('is-visible')
    const selector = this.staggerSelector()
    if (!selector) return

    // Array.from 而非直接對 NodeList 呼叫 forEach：prerender 用的伺服器端 DOM 實作
    // 回傳的 NodeList 並非完整實作，沒有 forEach 方法。
    const children = Array.from(el.querySelectorAll<HTMLElement>(selector))
    let autoIndex = 0
    children.forEach((child) => {
      // 已手動指定交錯延遲的元素（如桌機相片各自 index * 140ms）不覆寫，只補上 is-visible。
      if (!child.style.transitionDelay) {
        child.style.transitionDelay = `${autoIndex * this.staggerMs()}ms`
        autoIndex++
      }
      child.classList.add('is-visible')
    })
  }
}
