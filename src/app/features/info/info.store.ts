import { Injectable, signal } from '@angular/core'
import { WEDDING_SESSIONS, WeddingSession } from '../../core/config/wedding-content'

/**
 * 宴客場次切換狀態。預設選中的是設定檔裡的第一場，不寫死場次 id ——
 * 本場婚宴只辦晚宴，寫死 'lunch' 會讓唯一那顆膠囊沒有選中樣式。
 */
@Injectable({ providedIn: 'root' })
export class InfoStore {
  readonly sessions: readonly WeddingSession[] = WEDDING_SESSIONS

  private readonly _selectedId = signal<WeddingSession['id']>(WEDDING_SESSIONS[0].id)
  readonly selectedId = this._selectedId.asReadonly()

  select(id: WeddingSession['id']): void {
    this._selectedId.set(id)
  }
}
