import { Injectable, PLATFORM_ID, inject, signal } from '@angular/core'
import { isPlatformBrowser } from '@angular/common'

/**
 * 讀取 prefers-reduced-motion 系統設定，供 TypeScript 端需要跳過交錯延遲、
 * 直接一次性播放的地方使用（如 Hero 入場序列）。樣式層降級一律走 CSS media query，
 * 這個 service 只服務「時序」而非「樣式」的降級需求。
 */
@Injectable({ providedIn: 'root' })
export class ReducedMotionService {
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID))
  private readonly mediaQuery = this.isBrowser ? window.matchMedia('(prefers-reduced-motion: reduce)') : null
  // prerender（Node 環境）沒有 window，先當作使用者沒有要求減少動態，瀏覽器接手後才校正。
  private readonly _prefersReduced = signal(this.mediaQuery?.matches ?? false)
  readonly prefersReduced = this._prefersReduced.asReadonly()

  constructor() {
    this.mediaQuery?.addEventListener('change', (event) => this._prefersReduced.set(event.matches))
  }
}
