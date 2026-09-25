import { ChangeDetectionStrategy, Component, inject } from '@angular/core'
import { DomSanitizer } from '@angular/platform-browser'
import { IconComponent } from '../../shared/icon/icon.component'
import { ScrollRevealDirective } from '../../shared/scroll-reveal.directive'
import { SectionHeadingComponent } from '../../shared/section-heading/section-heading.component'
import { INFO_TEXT } from '../../core/config/wedding-content'
import { WEDDING_LINKS, buildGoogleMapsDirectionUrl, buildGoogleMapsEmbedUrl } from '../../core/config/wedding-links'

/**
 * S3 交通資訊區：停車示意圖（點圖另開原尺寸）與內嵌 Google 地圖（預設定位在飯店）加導航鈕，
 * 手機上下疊、桌機左右併排。
 * 日期、場地、宴會廳與地址由婚禮邀請函區呈現，這一段不重複。
 */
@Component({
  selector: 'app-info',
  imports: [SectionHeadingComponent, IconComponent, ScrollRevealDirective],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './info.component.html',
  styleUrl: './info.component.scss',
})
export class InfoComponent {
  protected readonly text = INFO_TEXT

  protected readonly mapsUrl = buildGoogleMapsDirectionUrl(WEDDING_LINKS.venueAddress)
  /** iframe 的 src 需先標記為可信任，Angular 才不會把它當成不安全的網址擋掉；網址由本站常數組成，不含使用者輸入。 */
  protected readonly mapEmbedUrl = inject(DomSanitizer).bypassSecurityTrustResourceUrl(
    buildGoogleMapsEmbedUrl(WEDDING_LINKS.venueMapQuery),
  )
}
