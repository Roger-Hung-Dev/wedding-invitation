import { ChangeDetectionStrategy, Component } from '@angular/core'
import { ScrollRevealDirective } from '../../shared/scroll-reveal.directive'
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
 * 手機與平板是直式的水彩 C 版，桌機換成橫式的水彩橫幅 L17，兩張帖讀同一份資料。
 *
 * 這一區只負責「這是一張帖」，所以不放地圖，也不放任何按鈕；「怎麼去」交給 S3 交通資訊區。
 */
@Component({
  selector: 'app-invitation',
  imports: [ScrollRevealDirective],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './invitation.component.html',
  styleUrl: './invitation.component.scss',
})
export class InvitationComponent {
  protected readonly content = WEDDING_CONTENT
  protected readonly text = INVITATION_TEXT
  protected readonly parents = WEDDING_PARENTS
  protected readonly photoUrl = INVITATION_PHOTO_URL
  protected readonly address = WEDDING_LINKS.venueAddress

  /**
   * 日期下方那一行，例如「星期六 · 晚宴 18:00 入席」。
   * 字距靠 CSS 的 letter-spacing 拉開，不在字串裡塞空白 —— 那會讓資料變成排版的一部分。
   *
   * 本場只有晚宴一場，取第一筆即可；日後加辦午宴時這裡要改成逐場列出，
   * 否則帖面只會顯示其中一場。
   */
  protected readonly dateSubDisplay =
    `${WEDDING_CONTENT.dateSubDisplay} · ${WEDDING_SESSIONS[0].label} ${WEDDING_SESSIONS[0].timeDisplay}`
}
