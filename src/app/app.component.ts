import { ChangeDetectionStrategy, Component, HostListener, inject } from '@angular/core'
import { HeroComponent } from './features/hero/hero.component'
import { AboutComponent } from './features/about/about.component'
import { StoryComponent } from './features/story/story.component'
import { GalleryComponent } from './features/gallery/gallery.component'
import { InfoComponent } from './features/info/info.component'
import { RsvpComponent } from './features/rsvp/rsvp.component'
import { FooterComponent } from './features/footer/footer.component'
import { MusicPlayerStore } from './features/music-player/music-player.store'
import { ToastContainerComponent } from './shared/toast-container.component'

/**
 * 全站唯一頁面：單頁垂直捲動的七個區塊依序串接，段與段之間沒有間隙。
 */
@Component({
  selector: 'app-root',
  imports: [HeroComponent, AboutComponent, StoryComponent, GalleryComponent, InfoComponent, RsvpComponent, FooterComponent, ToastContainerComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent {
  private readonly musicPlayerStore = inject(MusicPlayerStore)

  /**
   * 行動瀏覽器禁止無使用者手勢的自動播放，故以「首次使用者手勢」啟動背景音樂。
   *
   * ⚠️ 只監聽 click 是不夠的：**手機上滑動頁面不會產生 click**
   * （click 需要按下與放開在同一位置），賓客一進站就往下滑的話，音樂永遠不會開始。
   *
   * 依 HTML 規範，會授予「使用者啟用（user activation）」的是
   * keydown／mousedown／pointerdown／pointerup／touchend —— 其中 **touchend 涵蓋了滑動**，
   * 因為一次滑動的最後仍會送出 touchend。scroll 本身不在清單裡，監聽它沒有用。
   *
   * 四個事件都掛上，先到的那一個生效；play() 內有 idle 判斷，重複觸發不會有副作用。
   */
  @HostListener('document:click')
  @HostListener('document:touchend')
  @HostListener('document:pointerup')
  @HostListener('document:keydown')
  onFirstInteraction(): void {
    if (this.musicPlayerStore.state() === 'idle') {
      this.musicPlayerStore.play()
    }
  }
}
