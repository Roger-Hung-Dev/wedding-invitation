import { ChangeDetectionStrategy, Component, inject } from '@angular/core'
import { IconComponent } from '../../shared/icon/icon.component'
import { ScrollRevealDirective } from '../../shared/scroll-reveal.directive'
import { SectionHeadingComponent } from '../../shared/section-heading/section-heading.component'
import { INFO_TEXT, MAP_PREVIEW_IMAGE_DESKTOP_URL, MAP_PREVIEW_IMAGE_URL, WEDDING_CONTENT } from '../../core/config/wedding-content'
import { WEDDING_LINKS, buildGoogleMapsDirectionUrl } from '../../core/config/wedding-links'
import { InfoStore } from './info.store'
import { DietStore } from '../../core/diet.store'

/**
 * S3 宴客資訊區。地圖預覽為非互動靜態圖，導航鈕另開分頁前往 Google 地圖。
 */
@Component({
  selector: 'app-info',
  imports: [SectionHeadingComponent, IconComponent, ScrollRevealDirective],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './info.component.html',
  styleUrl: './info.component.scss',
})
export class InfoComponent {
  protected readonly store = inject(InfoStore)
  /** 桌次引導兩版不同：素食席位通常集中安排。 */
  protected readonly diet = inject(DietStore)
  protected readonly content = WEDDING_CONTENT
  protected readonly text = INFO_TEXT
  protected readonly links = WEDDING_LINKS

  protected readonly mapsUrl = buildGoogleMapsDirectionUrl(WEDDING_LINKS.venueAddress)
  protected readonly mapImageUrl = MAP_PREVIEW_IMAGE_URL
  protected readonly mapImageDesktopUrl = MAP_PREVIEW_IMAGE_DESKTOP_URL
}
