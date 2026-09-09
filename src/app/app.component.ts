import { ChangeDetectionStrategy, Component } from '@angular/core'
import { HeroComponent } from './features/hero/hero.component'
import { AboutComponent } from './features/about/about.component'
import { StoryComponent } from './features/story/story.component'
import { GalleryComponent } from './features/gallery/gallery.component'
import { InfoComponent } from './features/info/info.component'
import { RsvpComponent } from './features/rsvp/rsvp.component'
import { FooterComponent } from './features/footer/footer.component'
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
export class AppComponent {}
