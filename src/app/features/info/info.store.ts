import { Injectable, signal } from '@angular/core'
import { WEDDING_SESSIONS, WeddingSession } from '../../core/config/wedding-content'

/**
 * 宴客場次切換狀態。設計初稿假設午宴／晚宴兩場都辦，此處先照初稿實作兩顆可切換膠囊。
 */
@Injectable({ providedIn: 'root' })
export class InfoStore {
  readonly sessions: readonly WeddingSession[] = WEDDING_SESSIONS

  private readonly _selectedId = signal<WeddingSession['id']>('lunch')
  readonly selectedId = this._selectedId.asReadonly()

  select(id: WeddingSession['id']): void {
    this._selectedId.set(id)
  }
}
