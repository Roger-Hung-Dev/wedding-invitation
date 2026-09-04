import { Injectable, PLATFORM_ID, inject, signal } from '@angular/core'
import { isPlatformBrowser } from '@angular/common'

const DESKTOP_MEDIA_QUERY = '(min-width: 1024px)'

/**
 * 全站唯一的桌機／手機斷點來源。1024px 以上才視為桌機版式，
 * 768～1023px 沿用手機版式讓內容欄流式放大，不做第三套模板。
 */
@Injectable({ providedIn: 'root' })
export class BreakpointService {
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID))
  private readonly mediaQuery = this.isBrowser ? window.matchMedia(DESKTOP_MEDIA_QUERY) : null
  // prerender（Node 環境）沒有 window，一律先當手機版輸出；瀏覽器接手後 constructor 會立刻校正成實際寬度。
  private readonly _isDesktop = signal(this.mediaQuery?.matches ?? false)
  readonly isDesktop = this._isDesktop.asReadonly()

  constructor() {
    this.mediaQuery?.addEventListener('change', (event) => this._isDesktop.set(event.matches))
  }
}
