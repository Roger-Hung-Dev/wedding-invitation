# 參考：國際化 i18n（Transloco）

多國語系分兩層，切換語言時**同步**兩者：

- **應用文案** → 由 **Transloco** 管理（執行期切換），語言檔放 `src/assets/i18n/`。本檔負責這層。
- **UI 元件庫內建文字** → 由元件庫自己的 locale 機制提供（分頁器、日期選擇…），做法各庫不同，見專案選定的 `ui-*` skill。

> 例：`ui-angular-material` 用 `MAT_DATE_LOCALE` 與自訂 `MatPaginatorIntl` 跟隨 Transloco 切換；`ui-bootstrap5` 是純 CSS、不含任何文案，這層不存在。

## 安裝與註冊

```bash
ng add @jsverse/transloco
```

```ts
// src/app/core/transloco-loader.ts
import { HttpClient } from '@angular/common/http'
import { Injectable, inject } from '@angular/core'
import type { Translation, TranslocoLoader } from '@jsverse/transloco'

@Injectable({ providedIn: 'root' })
export class TranslocoHttpLoader implements TranslocoLoader {
  private readonly http = inject(HttpClient)

  getTranslation(lang: string) {
    return this.http.get<Translation>(`/assets/i18n/${lang}.json`)
  }
}
```

```ts
// src/app/app.config.ts（節錄）
import { isDevMode } from '@angular/core'
import { provideTransloco } from '@jsverse/transloco'
import { TranslocoHttpLoader } from './core/transloco-loader'

provideTransloco({
  config: {
    availableLangs: ['zh-TW', 'en'],
    defaultLang: 'zh-TW',
    fallbackLang: 'en',
    reRenderOnLangChange: true, // 執行期切換語言的必要條件
    prodMode: !isDevMode(),
  },
  loader: TranslocoHttpLoader,
})
```

> `reRenderOnLangChange: true` 一定要開，否則切語言後畫面不會更新 —— 這正是我們選 Transloco 而非 `@angular/localize` 的原因。

> 上面的 `zh-TW` / `en` 是**示意**。**支援語言清單與預設語言待專案確認**，未定前先問使用者，不要自行決定要支援哪些語言。

## 語言檔

```jsonc
// src/assets/i18n/zh-TW.json
{
  "common": { "save": "儲存", "cancel": "取消" },
  "task": {
    "title": "任務標題",
    "errors": { "titleRequired": "請輸入標題", "titleTooLong": "最多 50 字" }
  }
}
```

每種語言一個檔，key 結構**必須一致**（`en.json` 同樣的 key 樹）。

## 樣板用法

結構型指令（推薦，一次取得 `t`，整塊共用）：

```html
<ng-container *transloco="let t">
  <h1>{{ t('task.title') }}</h1>
  <button>{{ t('common.save') }}</button>
</ng-container>
```

元件需 `imports: [TranslocoDirective]`。單點翻譯也可用 pipe（`imports: [TranslocoPipe]`）：

```html
<h1>{{ 'task.title' | transloco }}</h1>
```

## TS 用法

```ts
private readonly transloco = inject(TranslocoService)

const message = this.transloco.translate('task.errors.titleRequired')
```

驗證錯誤的 i18n key 就是這樣翻的（schema 裡存 key，見 [form-schema.md](form-schema.md)）。

## 語言切換

```ts
protected switchLang(lang: string): void {
  this.transloco.setActiveLang(lang)
}
```

## 慣例

- 文案**一律**走 `t('...')` / `transloco` pipe，不在樣板寫死字串。
- 訊息 key 以功能 / 領域分群（如 `task.title`、`common.save`）。
- 表單驗證的錯誤訊息也走 i18n key（見 [form-schema.md](form-schema.md)）。
- 若 UI 元件庫也有 locale 機制，新增語言時**兩邊同時加**，並確保切換時同步（見 `ui-*` skill）。
