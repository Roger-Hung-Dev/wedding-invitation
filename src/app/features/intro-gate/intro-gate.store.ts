import { Injectable, signal } from '@angular/core'

/**
 * 開場層的狀態。
 *
 * 為什麼需要這一層：行動瀏覽器（尤其 iOS）不允許沒有「點擊或輕觸」就播放有聲音樂。
 * 滑動不算，靜音預播之後再解除靜音也會被立刻暫停（實機實測）。
 * 所以改為進站先請賓客輕觸一下：那一下同時是音樂的啟動許可，也是進場的儀式。
 *
 * 這個狀態也決定 Hero 的入場動畫何時開始 —— 賓客點開之後才播。
 * 不要在開場層還蓋著的時候就播完，那 2.4 秒的入場序列會白白浪費。
 */
@Injectable({ providedIn: 'root' })
export class IntroGateStore {
  private readonly _entered = signal(false)

  /** 賓客是否已經輕觸進入。false 時開場層蓋在最上層。 */
  readonly entered = this._entered.asReadonly()

  enter(): void {
    this._entered.set(true)
  }
}
