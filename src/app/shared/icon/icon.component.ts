import { ChangeDetectionStrategy, Component, input } from '@angular/core'

export type IconName =
  | 'chevron-down'
  | 'chevron-left'
  | 'chevron-right'
  | 'disc'
  | 'volume-x'
  | 'x'
  | 'navigation'
  | 'external-link'
  | 'building'
  | 'door-open'
  | 'map-pin'
  | 'users'
  | 'leaf'
  | 'heart'

/**
 * 全站唯一的圖示來源，手刻線性圖示（stroke-based，24×24 viewBox），
 * 不引入任何第三方圖示套件。畫面上只會用到分析檔列出的這幾種，不自行增補。
 */
@Component({
  selector: 'app-icon',
  imports: [],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <svg
      [attr.width]="size()"
      [attr.height]="size()"
      viewBox="0 0 24 24"
      fill="none"
      [attr.stroke]="color() || 'currentColor'"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
    >
      @switch (name()) {
        @case ('chevron-down') {
          <polyline points="6 9 12 15 18 9" />
        }
        @case ('chevron-left') {
          <polyline points="15 6 9 12 15 18" />
        }
        @case ('chevron-right') {
          <polyline points="9 6 15 12 9 18" />
        }
        @case ('disc') {
          <circle cx="12" cy="12" r="9" />
          <circle cx="12" cy="12" r="2.5" />
        }
        @case ('volume-x') {
          <polygon points="8 5 3 9 3 15 8 19 15 19 15 5 8 5" fill="currentColor" stroke="none" />
          <line x1="17" y1="9" x2="23" y2="15" />
          <line x1="23" y1="9" x2="17" y2="15" />
        }
        @case ('x') {
          <line x1="5" y1="5" x2="19" y2="19" />
          <line x1="19" y1="5" x2="5" y2="19" />
        }
        @case ('navigation') {
          <polygon points="12 2 19 21 12 17 5 21 12 2" />
        }
        @case ('external-link') {
          <path d="M14 4h6v6" />
          <path d="M20 4 10 14" />
          <path d="M18 13v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h6" />
        }
        @case ('building') {
          <rect x="5" y="3" width="14" height="18" rx="1" />
          <line x1="9" y1="7" x2="9" y2="7.01" />
          <line x1="15" y1="7" x2="15" y2="7.01" />
          <line x1="9" y1="11" x2="9" y2="11.01" />
          <line x1="15" y1="11" x2="15" y2="11.01" />
          <line x1="9" y1="15" x2="15" y2="15" />
        }
        @case ('door-open') {
          <path d="M4 20h5V4l-5 1z" />
          <path d="M9 4h9v16h-9" />
          <line x1="14" y1="12" x2="14" y2="12.01" />
        }
        @case ('map-pin') {
          <path d="M12 21s7-6.4 7-12a7 7 0 0 0-14 0c0 5.6 7 12 7 12z" />
          <circle cx="12" cy="9" r="2.4" />
        }
        @case ('users') {
          <path d="M14 19v-1.5a3.5 3.5 0 0 0-3.5-3.5h-4A3.5 3.5 0 0 0 3 17.5V19" />
          <circle cx="8.5" cy="8" r="3" />
          <path d="M21 19v-1.5a3.5 3.5 0 0 0-2.5-3.36" />
          <path d="M15.5 4.6a3 3 0 0 1 0 5.8" />
        }
        @case ('leaf') {
          <path d="M4 20c0-8 5-13 16-14 0 11-5 15-11 15a5 5 0 0 1-5-1Z" />
          <path d="M9 15c1.8-3 4.2-5.2 7-6.4" />
        }
        @case ('heart') {
          <path d="M12 20.4s-7.5-4.6-7.5-10a4.3 4.3 0 0 1 7.5-2.6 4.3 4.3 0 0 1 7.5 2.6c0 5.4-7.5 10-7.5 10Z" />
        }
      }
    </svg>
  `,
})
export class IconComponent {
  readonly name = input.required<IconName>()
  readonly size = input(20)
  readonly color = input<string | null>(null)
}
