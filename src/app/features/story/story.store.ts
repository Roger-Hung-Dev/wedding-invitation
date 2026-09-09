import { Injectable, computed, signal } from '@angular/core'
import { STORY_PAGES, StoryPage } from '../../core/config/wedding-content'

export type StoryTurnDirection = 'next' | 'prev'

/** 書頁的頁碼是兩位數（第 1 頁寫成 01），真書的頁碼不寫總頁數。 */
function formatPageNumber(index: number): string {
  return String(index + 1).padStart(2, '0')
}

/**
 * 交往故事書的翻頁狀態。index 是目前顯示的頁，翻頁一開始就更新成目標頁，
 * outgoingIndex 則留著「正在被翻過去的那一頁」讓畫面畫得出翻頁動畫，翻完才清掉。
 * 翻頁期間不受理新的翻頁請求——連點會讓頁碼與畫面對不上。
 */
@Injectable({ providedIn: 'root' })
export class StoryStore {
  readonly pages: readonly StoryPage[] = STORY_PAGES

  private readonly _index = signal(0)
  readonly index = this._index.asReadonly()

  private readonly _outgoingIndex = signal<number | null>(null)
  readonly outgoingIndex = this._outgoingIndex.asReadonly()

  private readonly _direction = signal<StoryTurnDirection>('next')
  readonly direction = this._direction.asReadonly()

  readonly isTurning = computed(() => this._outgoingIndex() !== null)
  readonly canPrev = computed(() => this._index() > 0)
  readonly canNext = computed(() => this._index() < this.pages.length - 1)

  readonly currentPage = computed(() => this.pages[this._index()])
  readonly currentPageNumber = computed(() => formatPageNumber(this._index()))

  readonly outgoingPage = computed<StoryPage | null>(() => {
    const index = this._outgoingIndex()
    return index === null ? null : this.pages[index]
  })
  readonly outgoingPageNumber = computed(() => {
    const index = this._outgoingIndex()
    return index === null ? '' : formatPageNumber(index)
  })

  /**
   * 開始翻頁。翻頁進行中或已經在邊界（首頁往前、末頁往後）時回傳 false，
   * 呼叫端據此決定要不要啟動「翻完解鎖」的計時器。故事不循環：翻完了就是翻完了。
   */
  startTurn(direction: StoryTurnDirection): boolean {
    if (this.isTurning()) return false

    const from = this._index()
    const to = direction === 'next' ? from + 1 : from - 1
    if (to < 0 || to > this.pages.length - 1) return false

    this._direction.set(direction)
    this._outgoingIndex.set(from)
    this._index.set(to)
    return true
  }

  endTurn(): void {
    this._outgoingIndex.set(null)
  }
}
