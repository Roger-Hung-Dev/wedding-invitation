import { ChangeDetectionStrategy, Component } from '@angular/core'
import { ScrollRevealDirective } from '../../shared/scroll-reveal.directive'
import { WebpSrcsetPipe } from '../../shared/webp-srcset.pipe'
import {
  INVITATION_PHOTO_URL,
  INVITATION_TEXT,
  WEDDING_CONTENT,
  WEDDING_PARENTS,
  WEDDING_SESSIONS,
} from '../../core/config/wedding-content'
import { WEDDING_LINKS } from '../../core/config/wedding-links'

/**
 * S1.5 正式邀請函區。緊接在封面之後，是整份喜帖唯一由雙方家長具名的一面，
 * 等同紙本喜帖的帖面：一眼看完就知道是誰邀、哪天、在哪。
 * 手機與平板是直式帖、桌機是橫式帖（比稿「電子喜帖帖面排版」手機 1／電腦 6），兩張帖讀同一份資料。
 *
 * 這一區只負責「這是一張帖」，所以不放地圖，也不放任何按鈕；「怎麼去」交給 S3 交通資訊區。
 */
@Component({
  selector: 'app-invitation',
  imports: [ScrollRevealDirective, WebpSrcsetPipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './invitation.component.html',
  styleUrl: './invitation.component.scss',
})
export class InvitationComponent {
  protected readonly content = WEDDING_CONTENT
  protected readonly text = INVITATION_TEXT
  protected readonly parents = WEDDING_PARENTS
  protected readonly photoUrl = INVITATION_PHOTO_URL
  /**
   * 地址拆成「台中市烏日區」與「高鐵路三段 168 號」兩段，每段各自不斷行。
   * 手機帖的字級放大後地址放不進一行，讓瀏覽器自由換行會斷成「…三段 168」／「號」；
   * 拆段後只會在行政區之後換行。找不到「區／鄉／鎮」時整串當一段。
   */
  protected readonly addressParts = splitAfterDistrict(WEDDING_LINKS.venueAddress)

  /**
   * 日期下方那一行，例如「星期六 · 晚宴 18:00」＋「恭請準時入席」，拆成兩段的理由同地址：
   * 窄手機放不下一行時，只在兩段之間換行，不會把「恭請準時入席」拆散。
   * 字距靠 CSS 的 letter-spacing 拉開，不在字串裡塞空白 —— 那會讓資料變成排版的一部分。
   *
   * 本場只有晚宴一場，取第一筆即可；日後加辦午宴時這裡要改成逐場列出，
   * 否則帖面只會顯示其中一場。
   */
  protected readonly dateSubParts = splitDateSub(
    WEDDING_CONTENT.dateSubDisplay,
    WEDDING_SESSIONS[0].label,
    WEDDING_SESSIONS[0].timeDisplay,
  )
}

function splitAfterDistrict(address: string): string[] {
  const match = /^(.*?[區鄉鎮])(.+)$/.exec(address)
  return match ? [match[1], match[2]] : [address]
}

/** timeDisplay 是「18:00 恭請準時入席」：時間接在前段，後面的敬語自成一段。 */
function splitDateSub(weekday: string, sessionLabel: string, timeDisplay: string): string[] {
  const [time, ...courtesy] = timeDisplay.split(' ')
  const lead = `${weekday} · ${sessionLabel} ${time}`
  return courtesy.length > 0 ? [lead, courtesy.join(' ')] : [lead]
}
