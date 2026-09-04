import { isPlatformBrowser } from '@angular/common'
import { DestroyRef, Injectable, PLATFORM_ID, computed, inject, signal } from '@angular/core'
import { WEDDING_COUNTDOWN_TARGET_ISO } from '../../core/config/wedding-content'
import { calcCountdown } from '../../core/date.util'

/**
 * Hero 倒數計時狀態。以 signal 持有目前時間，每秒更新一次，
 * 婚期已過時 isOver 轉為 true，元件據此切換成「Thank you」文字。
 */
@Injectable({ providedIn: 'root' })
export class HeroStore {
  private readonly destroyRef = inject(DestroyRef)
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID))
  private readonly _now = signal(Date.now())

  readonly countdown = computed(() => calcCountdown(WEDDING_COUNTDOWN_TARGET_ISO, this._now()))

  constructor() {
    // prerender（Node 環境）只需要渲染當下這一刻的合理初始值，不必也不應該啟動計時器，
    // 否則 Node 行程會因為 interval 沒被清掉而卡住，且伺服器算出的秒數渲染完就沒有意義。
    if (!this.isBrowser) return

    const timer = setInterval(() => this._now.set(Date.now()), 1000)
    this.destroyRef.onDestroy(() => clearInterval(timer))
  }
}
