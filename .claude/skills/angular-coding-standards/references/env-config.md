# 參考：環境變數與建置

Angular 沒有 Vite 那種 `import.meta.env`，走的是**建置期檔案替換**（file replacements）：不同環境用不同的 `environment.ts`，由 CLI 在 build 時抽換。

## 環境設定檔

```ts
// src/environments/environment.ts —— 開發（預設）
export const environment = {
  production: false,
  apiBaseUrl: 'http://localhost:8080/api',
} as const
```

```ts
// src/environments/environment.prod.ts —— 正式
export const environment = {
  production: true,
  apiBaseUrl: '/api',
} as const
```

> **兩個檔案的欄位必須完全一致**，否則抽換後會出現 undefined。新增欄位時兩邊同時加。

## 註冊檔案替換

```jsonc
// angular.json（節錄）
{
  "configurations": {
    "production": {
      "fileReplacements": [
        {
          "replace": "src/environments/environment.ts",
          "with": "src/environments/environment.prod.ts"
        }
      ]
    }
  }
}
```

## 集中讀取

程式碼**不直接 import `environment`**，統一經 `core/config/env.ts` 轉一手 —— 之後要改來源（如改讀 runtime config）只需動一個檔：

```ts
// src/app/core/config/env.ts
import { environment } from '../../../environments/environment'

export const env = {
  apiBaseUrl: environment.apiBaseUrl,
  isProduction: environment.production,
} as const
```

## 鐵律

- **API 位址不寫死在程式碼**，一律走 `env.apiBaseUrl`。
- **密鑰不放 `environment.ts`** —— 它會被打包進前端 bundle，任何人都看得到。前端需要的機敏設定一律由後端在 runtime 提供。
- 新增環境（如 staging）時：加一個 `environment.staging.ts` + `angular.json` 的對應 configuration，不要用 if/else 在程式碼裡分支。

## 常用指令

> **專案初始化時待確定**（未定前不要自行假設，先問使用者）：套件管理器（npm / pnpm 擇一）、Node 版本、ESLint / Prettier / husky + lint-staged 的**具體設定檔**內容。

| 指令 | 用途 |
| --- | --- |
| `ng serve` | 開發伺服器（預設 `http://localhost:4200`） |
| `ng build` | 正式建置（預設套用 production configuration） |
| `ng test` | 跑測試（見 `angular-testing`） |
| `ng lint` | ESLint 檢查 |
| `ng generate component features/task/task-list` | 產生元件骨架（產完仍要依本規範調整，如加 `OnPush`） |
