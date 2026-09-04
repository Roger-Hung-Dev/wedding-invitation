import { ChangeDetectionStrategy, Component, HostListener, inject } from '@angular/core'
import { HeroComponent } from './features/hero/hero.component'
import { GalleryComponent } from './features/gallery/gallery.component'
import { InfoComponent } from './features/info/info.component'
import { RsvpComponent } from './features/rsvp/rsvp.component'
import { FooterComponent } from './features/footer/footer.component'
import { MusicPlayerStore } from './features/music-player/music-player.store'
import { ToastContainerComponent } from './shared/toast-container.component'

/**
 * 全站唯一頁面：單頁垂直捲動的五個區塊依序串接，段與段之間沒有間隙。
 */
@Component({
  selector: 'app-root',
  imports: [HeroComponent, GalleryComponent, InfoComponent, RsvpComponent, FooterComponent, ToastContainerComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent {
  private readonly musicPlayerStore = inject(MusicPlayerStore)

  /**
   * 行動瀏覽器禁止無使用者手勢的自動播放，故以「首次點擊頁面任一處」啟動背景音樂。
   * 監聽整份文件而非只在 Hero 內，因為賓客可能先滑動頁面才點擊。
   */
  @HostListener('document:click')
  onFirstInteraction(): void {
    if (this.musicPlayerStore.state() === 'idle') {
      this.musicPlayerStore.play()
    }
  }
}
