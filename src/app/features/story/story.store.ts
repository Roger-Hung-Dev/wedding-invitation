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

  /**
   * 翻過來的那張紙是否已經蓋住底層該換頁的那一半。
   * 由元件在動畫進行到淡出起點時設起來，見 story.component.ts 的 BASE_SWAP_RATIO。
   */
  private readonly _covered = signal(false)

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

  /*
    以下三個是「桌機雙頁底層該顯示哪一頁」。翻頁一開始 index 就跳到目標頁，
    但真實的書翻頁時只有一半會馬上換：

    | 方向 | 左半（照片）           | 右半（文字）           |
    | 往後 | 被翻過來的紙背面蓋上 → 留舊頁 | 紙離開後露出 → 換新頁     |
    | 往前 | 紙離開後露出 → 換新頁     | 被翻過來的紙背面蓋上 → 留舊頁 |

    兩邊都直接換成新頁的話，會看到「還沒翻，另外半邊就先變成下一張」。

    ⛔ 但「留舊頁」不能留到翻頁結束。翻頁層在最後 15% 會淡出、由底層接手
    （見 story.component.scss 的 story-flip-fade），底層那時還是舊頁的話，
    淡出就會露出舊頁、等翻頁結束才跳成新頁 —— 那是「翻完後閃一下」。
    所以要在紙蓋住、而且還沒開始淡出的那一刻換，也就是 _covered 被設起來的時候。
  */

  /**
   * 手機單頁的底層。翻頁時留著舊頁，等翻過來的紙蓋上了才換。
   *
   * 手機是一整張紙原地翻面（正面舊頁、背面新頁），紙轉動時兩側會露出底層。
   * 底層若直接換成新頁，畫面會變成「新頁｜正在翻的舊頁｜新頁」三段；留著舊頁，
   * 看起來才是同一張紙在翻。
   */
  readonly cardPage = computed(() => {
    const outgoing = this._outgoingIndex()
    return outgoing !== null && !this._covered() ? this.pages[outgoing] : this.currentPage()
  })

  /** 左頁（照片）。往後翻時要留著舊頁，等翻過來的紙蓋上了才換。 */
  readonly spreadPhotoPage = computed(() => {
    const outgoing = this._outgoingIndex()
    return outgoing !== null && this._direction() === 'next' && !this._covered()
      ? this.pages[outgoing]
      : this.currentPage()
  })

  /** 右頁（文字）。往前翻時要留著舊頁，理由同上。 */
  readonly spreadTextPage = computed(() => {
    const outgoing = this._outgoingIndex()
    return outgoing !== null && this._direction() === 'prev' && !this._covered()
      ? this.pages[outgoing]
      : this.currentPage()
  })

  /** 右頁的頁碼要跟著右頁的內容走，否則翻到一半會出現「舊內容配新頁碼」。 */
  readonly spreadTextPageNumber = computed(() => {
    const outgoing = this._outgoingIndex()
    return outgoing !== null && this._direction() === 'prev' && !this._covered()
      ? formatPageNumber(outgoing)
      : this.currentPageNumber()
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
    this._covered.set(false)
    this._outgoingIndex.set(from)
    this._index.set(to)
    return true
  }

  /** 紙已經蓋住底層該換頁的那一半，可以換了。 */
  markCovered(): void {
    this._covered.set(true)
  }

  endTurn(): void {
    this._outgoingIndex.set(null)
    this._covered.set(false)
  }
}
