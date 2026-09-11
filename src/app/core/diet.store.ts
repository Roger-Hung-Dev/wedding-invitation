import { Injectable, computed, signal } from '@angular/core'
import { DIET_VARIANTS, DietType } from './config/wedding-content'
import { WEDDING_LINKS } from './config/wedding-links'

/**
 * 目前這一份喜帖是哪個宴席版本。由路由在進站時設定一次，之後不再變動。
 *
 * 放在 core 而不是某個 feature 底下，因為首頁、蔬食心意區與出席回覆區都要讀它 ——
 * 掛在其中一邊會讓另一邊反向相依。
 */
@Injectable({ providedIn: 'root' })
export class DietStore {
  private readonly _diet = signal<DietType>('regular')

  readonly diet = this._diet.asReadonly()

  /** 出席回覆表單會收集的欄位預告。 */
  readonly fieldChips = computed(() => DIET_VARIANTS[this._diet()].fieldChips)

  /** 蔬食心意區的禮金與餐點兩則。葷食版為空陣列，首頁據此決定要不要渲染整個區塊。 */
  readonly dietNotes = computed(() => DIET_VARIANTS[this._diet()].dietNotes)

  /** 出席回覆表單網址。兩版分開，回覆才會自然分開統計。 */
  readonly rsvpFormUrl = computed(() =>
    this._diet() === 'vegetarian' ? WEDDING_LINKS.rsvpFormUrlVegetarian : WEDDING_LINKS.rsvpFormUrl,
  )

  setDiet(diet: DietType): void {
    this._diet.set(diet)
  }
}
