import { Injectable, signal } from '@angular/core'

export type MusicPlayerState = 'idle' | 'playing' | 'muted'

/**
 * 音樂鈕狀態。行動瀏覽器禁止無使用者手勢的自動播放，
 * 進站時固定為 idle（尚未播放），首次使用者手勢才轉為 playing。
 */
@Injectable({ providedIn: 'root' })
export class MusicPlayerStore {
  private readonly _state = signal<MusicPlayerState>('idle')
  readonly state = this._state.asReadonly()

  play(): void {
    this._state.set('playing')
  }

  mute(): void {
    this._state.set('muted')
  }

  /**
   * 瀏覽器拒絕播放時退回未播放狀態。
   * ⛔ 不要省略這一步 —— 狀態留在 playing 的話，畫面上的鈕會顯示「播放中」
   * 而實際上沒有聲音，賓客只會覺得音量壞了，不知道要再點一次。
   */
  resetToIdle(): void {
    this._state.set('idle')
  }

  unmute(): void {
    this._state.set('playing')
  }
}
