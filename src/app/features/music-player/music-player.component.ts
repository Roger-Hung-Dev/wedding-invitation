import { isPlatformBrowser } from '@angular/common'
import { ChangeDetectionStrategy, Component, ElementRef, HostListener, PLATFORM_ID, afterNextRender, effect, inject, signal, viewChild } from '@angular/core'
import { IconComponent } from '../../shared/icon/icon.component'
import { MUSIC_PLAYER_TEXT } from '../../core/config/wedding-content'
import { MusicPlayerStore } from './music-player.store'

/**
 * 浮動於畫面右下角的音樂控制鈕，position: fixed 橫跨全頁，
 * 獨立成 feature 而不掛在 Hero 底下，因為它不隨任何區塊捲走。
 */
@Component({
  selector: 'app-music-player',
  imports: [IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <button
      type="button"
      class="music-btn"
      [class.music-btn--idle]="store.state() === 'idle'"
      [class.music-btn--playing]="store.state() === 'playing'"
      [class.music-btn--muted]="store.state() === 'muted'"
      [attr.aria-label]="store.state() === 'muted' ? text.ariaLabelMuted : store.state() === 'playing' ? text.ariaLabelPlaying : text.ariaLabelIdle"
      (click)="toggle()"
    >
      <span class="music-btn__disc" [class.anim-disc-spin]="store.state() === 'playing'">
        <app-icon [name]="store.state() === 'muted' ? 'volume-x' : 'disc'" [size]="24" />
      </span>
    </button>
    @if (debug()) {
      <pre class="music-debug">{{ debugText() }}</pre>
    }
    <!--
      ⚠️ 背景音樂用 <audio>，而且 preload 一定要是 auto。
      iOS 要求 play() 在使用者手勢的同步呼叫中完成 —— 若音檔尚未載入，
      play() 得先等下載，那一等就脫離了手勢的時間窗，於是被拒。
      preload="auto" 讓音檔在進站後就備好，手勢一到就能立刻出聲。

      ⛔ 不要改用隱藏的 <video> 來繞自動播放限制：實測 iOS 上 video 會「在播、
      不靜音、時間也在走」，但**聽不到聲音** —— 視覺上被藏起來的 video 不會實際輸出音訊。
      診斷面板顯示一切正常卻沒聲音，就是踩到這一點。
    -->
    <audio #audioEl loop preload="auto">
      <source src="assets/audio/wedding-bgm.mp3" type="audio/mpeg">
    </audio>
  `,
  styles: `
    :host {
      display: inline-flex;
    }

    // ⛔ 不要用 display: none 或 visibility: hidden 藏這個 video ——
    // 部分瀏覽器會把「不可見的媒體」視為可回收而停止播放。
    // 縮到 1px、透明、移出點擊範圍，是既看不見又確保會播的作法。
    // 只在網址帶 ?debug 時出現，用於在真實手機上回報播放狀態（本機無法遠端偵錯）
    .music-debug {
      position: fixed;
      left: 8px;
      right: 8px;
      bottom: 8px;
      z-index: 99;
      margin: 0;
      padding: 10px 12px;
      border-radius: 10px;
      background: #000000D9;
      color: #fff;
      font-size: 12px;
      line-height: 1.6;
      white-space: pre-wrap;
      pointer-events: none;
    }

    .music-media {
      position: fixed;
      left: 0;
      bottom: 0;
      width: 1px;
      height: 1px;
      opacity: 0;
      pointer-events: none;
    }

    .music-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 56px;
      height: 56px;
      border-radius: 28px;
      background: var(--color-surface);
      border: 1px solid transparent;
      box-shadow: 0 4px 16px var(--shadow-rose);
      color: var(--color-primary);
      cursor: pointer;
      transition: border-color 200ms, opacity 200ms;
    }

    .music-btn--idle {
      border-color: #E7C87380;
    }

    .music-btn--playing {
      border-width: 2px;
      border-color: var(--color-accent-gold);
    }

    .music-btn--muted {
      border-color: var(--color-border-pill);
      color: var(--color-text-muted);
      opacity: 0.75;
    }

    .music-btn__disc {
      display: inline-flex;
    }
  `,
})
export class MusicPlayerComponent {
  protected readonly store = inject(MusicPlayerStore)
  protected readonly text = MUSIC_PLAYER_TEXT
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID))
  private readonly audioEl = viewChild.required<ElementRef<HTMLAudioElement>>('audioEl')

  /**
   * 診斷面板：只在網址帶 ?debug 時顯示。
   * 自動播放的行為在每台手機、每種瀏覽器設定下都不同，而這些狀態在開發機上重現不出來 ——
   * 讓使用者開一次 ?debug 把畫面截給我，比猜十次有效。
   */
  protected readonly debug = signal(false)
  protected readonly debugText = signal('')
  private readonly debugLog: string[] = []

  constructor() {
    // ⛔ 這裡不做「靜音預播」：實測 <audio> 即使靜音也不准自動播放
    // （NotAllowedError: the user didn't interact with the document first）。
    // 能做的是 preload="auto" 讓音檔先備好，手勢一到就能立刻播 —— 見樣板的說明。
    afterNextRender(() => {
      if (!this.isBrowser) return
      if (new URLSearchParams(location.search).has('debug')) {
        this.debug.set(true)
        this.note('面板啟動')
        setInterval(() => this.note(''), 1000)
      }
    })

    // 用 effect 統一連動實際的 <audio>，避免多處各自呼叫 audio API。
    // prerender（Node 環境）的 <audio> 是精簡 DOM 實作，沒有真正的 play()/pause()，故整段跳過。
    effect(() => {
      if (!this.isBrowser) return
      const audio = this.audioEl().nativeElement
      const state = this.store.state()
      if (state === 'playing') {
        audio.play().catch(() => {
          // 被拒的兩種情況：瀏覽器判定手勢不足，或音檔載入失敗。
          // 都要退回 idle —— 留在 playing 會讓鈕顯示「播放中」卻沒有聲音。
          this.store.resetToIdle()
        })
      } else if (state === 'muted') {
        // 使用者主動關掉：真的暫停，不要只是靜音空跑，那會白白耗流量與電力
        audio.pause()
      }
      // state === 'idle' 時什麼都不做 —— 靜音預播要繼續跑著等待解除靜音
    })
  }

  /**
   * 首次使用者手勢：嘗試把靜音預播轉成有聲。
   *
   * ⚠️ **滑動無法啟動「有聲自動播放」** —— Chrome 的 Autoplay Policy 要求的是
   * click 或 tap，`touchend` 給的 user activation 不足以通過那一關（實測確認）。
   * 但**解除一個已在播放的媒體的靜音**走的不是同一條規則，滑動有機會成功。
   * 所以這裡監聽 touchend／pointerup（涵蓋滑動）與 click／keydown（涵蓋點擊）。
   *
   * 失敗就轉回靜音、狀態留在 idle，賓客仍可點右下角的音樂鈕 —— 沒有任何損失。
   */
  @HostListener('document:touchend', ['$event'])
  @HostListener('document:pointerup', ['$event'])
  @HostListener('document:click', ['$event'])
  @HostListener('document:keydown', ['$event'])
  onFirstGesture(event?: Event): void {
    if (!this.isBrowser || this.store.state() !== 'idle') return
    const audio = this.audioEl().nativeElement
    this.note(`手勢 ${event?.type ?? '?'} ready=${audio.readyState}`)
    // ⚠️ play() 必須在這個同步呼叫堆疊裡發出 —— iOS 只認「手勢當下」發出的播放請求，
    // 先做任何 await 或 setTimeout 都會脫離時間窗而被拒。
    audio.play().then(
      () => {
        this.store.play()
        this.note('播放 → 成功')
      },
      (e: DOMException) => this.note(`播放 → 被拒 ${e.name}`),
    )
  }

  /** 把一行診斷訊息加進面板（只在 ?debug 時看得到）。 */
  private note(line: string): void {
    if (!this.debug()) return
    if (line) this.debugLog.push(line)
    const audio = this.audioEl().nativeElement
    this.debugText.set(
      [
        `狀態=${this.store.state()}  標籤=${audio.tagName}`,
        `paused=${audio.paused} t=${audio.currentTime.toFixed(1)} ready=${audio.readyState} vol=${audio.volume}`,
        ...this.debugLog.slice(-6),
      ].join(String.fromCharCode(10)),
    )
  }

  toggle(): void {
    if (this.store.state() === 'idle') {
      this.store.play()
    } else if (this.store.state() === 'muted') {
      this.store.unmute()
    } else {
      this.store.mute()
    }
  }
}
