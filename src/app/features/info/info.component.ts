import { ChangeDetectionStrategy, Component, inject } from '@angular/core'
import { CornerEmbossComponent } from '../../shared/corner-emboss/corner-emboss.component'
import { DomSanitizer } from '@angular/platform-browser'
import { IconComponent } from '../../shared/icon/icon.component'
import { ScrollRevealDirective } from '../../shared/scroll-reveal.directive'
import { SectionHeadingComponent } from '../../shared/section-heading/section-heading.component'
import { INFO_TEXT, WEDDING_CONTENT, WEDDING_SESSIONS } from '../../core/config/wedding-content'
import { WEDDING_LINKS, buildGoogleMapsDirectionUrl, buildGoogleMapsEmbedUrl } from '../../core/config/wedding-links'

/**
 * S3 宴客資訊區。地圖為內嵌的 Google 地圖（預設定位在飯店），導航鈕另開分頁前往 Google 地圖。
 */
@Component({
  selector: 'app-info',
  imports: [CornerEmbossComponent, SectionHeadingComponent, IconComponent, ScrollRevealDirective],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './info.component.html',
  styleUrl: './info.component.scss',
})
export class InfoComponent {
  /** 只辦一場時框內就一行；原本的場次切換膠囊已移除——只有一場時它點了不會有任何反應。 */
  protected readonly sessions = WEDDING_SESSIONS
  protected readonly content = WEDDING_CONTENT
  protected readonly text = INFO_TEXT
  protected readonly links = WEDDING_LINKS

  protected readonly mapsUrl = buildGoogleMapsDirectionUrl(WEDDING_LINKS.venueAddress)
  /** iframe 的 src 需先標記為可信任，Angular 才不會把它當成不安全的網址擋掉；網址由本站常數組成，不含使用者輸入。 */
  protected readonly mapEmbedUrl = inject(DomSanitizer).bypassSecurityTrustResourceUrl(
    buildGoogleMapsEmbedUrl(WEDDING_LINKS.venueMapQuery),
  )
}
