import { ChangeDetectionStrategy, Component } from '@angular/core'
import { DEAR_FRIENDS_TEXT } from '../../core/config/wedding-content'
import { ScrollRevealDirective } from '../../shared/scroll-reveal.directive'
import { WebpSrcsetPipe } from '../../shared/webp-srcset.pipe'

/**
 * 婚紗藝廊與 greeting 之間的「致親友」：一張照片，給家人朋友的一段話直接寫在照片的天空上。
 * 延續 greeting 的作法（照片邊緣淡進背景、不帶段落抬頭），差別在字寫在照片裡而不是照片下方。
 */
@Component({
  selector: 'app-dear-friends',
  imports: [ScrollRevealDirective, WebpSrcsetPipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './dear-friends.component.html',
  styleUrl: './dear-friends.component.scss',
})
export class DearFriendsComponent {
  protected readonly text = DEAR_FRIENDS_TEXT
}
