import { ChangeDetectionStrategy, Component, effect, inject, input } from '@angular/core'
import { DietType } from '../../core/config/wedding-content'
import { DietStore } from '../../core/diet.store'
import { HeroComponent } from '../hero/hero.component'
import { AboutComponent } from '../about/about.component'
import { StoryComponent } from '../story/story.component'
import { GalleryComponent } from '../gallery/gallery.component'
import { InfoComponent } from '../info/info.component'
import { RsvpComponent } from '../rsvp/rsvp.component'
import { FooterComponent } from '../footer/footer.component'

/**
 * 喜帖本體：七個區塊依序串接，段與段之間沒有間隙。
 *
 * 兩個宴席版本（葷食／素食）共用這一份畫面，只有桌次引導、出席回覆表單網址
 * 與欄位預告三處不同。差異全部集中在 DietStore，這裡只負責把路由帶來的版本交給它。
 */
@Component({
  selector: 'app-home',
  imports: [HeroComponent, AboutComponent, StoryComponent, GalleryComponent, InfoComponent, RsvpComponent, FooterComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <app-hero />
    <app-about />
    <app-story />
    <app-gallery />
    <app-info />
    <app-rsvp />
    <app-footer />
  `,
})
export class HomeComponent {
  /** 由路由的 withComponentInputBinding 直接餵進來，不必自己讀 ActivatedRoute。 */
  readonly diet = input<DietType>('regular')

  private readonly dietStore = inject(DietStore)

  constructor() {
    effect(() => this.dietStore.setDiet(this.diet()))
  }
}
