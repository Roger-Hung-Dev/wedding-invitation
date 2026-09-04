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

  unmute(): void {
    this._state.set('playing')
  }
}
