import { isPlatformBrowser } from '@angular/common'
import { ChangeDetectionStrategy, Component, ElementRef, PLATFORM_ID, effect, inject, viewChild } from '@angular/core'
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
    <audio #audioEl loop preload="none">
      <!-- 實際婚禮背景音樂檔尚未取得，先留空來源；有正式音檔後補上 src 即可 -->
    </audio>
  `,
  styles: `
    :host {
      display: inline-flex;
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

  constructor() {
    // 音樂狀態也可能由「首次點擊頁面任一處」（app root 的全域手勢）觸發，
    // 用 effect 統一在這裡連動實際的 <audio> 播放／暫停，避免兩處各自呼叫 audio API。
    // prerender（Node 環境）的 <audio> 是精簡 DOM 實作，沒有真正的 play()/pause()，故整段跳過。
    effect(() => {
      if (!this.isBrowser) return
      const audio = this.audioEl().nativeElement
      if (this.store.state() === 'playing') {
        audio.play().catch(() => {
          // 沒有實際音檔可播放時 play() 會 reject，仍維持狀態切換的互動回饋
        })
      } else {
        audio.pause()
      }
    })
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
