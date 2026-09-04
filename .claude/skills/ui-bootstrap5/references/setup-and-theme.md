# 參考：Bootstrap 5 引入與主題

**只引 CSS/SCSS，不引 Bootstrap 的 JS**（理由見 SKILL.md 的鐵律）。`package.json` 只需要 `bootstrap` 這個套件，不需要 `@popperjs/core`（那是 Bootstrap JS 的相依，我們不用）。

## 按需引入 + 變數覆寫

引入 Bootstrap 的 **SCSS 原始碼**（不是編譯好的 `bootstrap.min.css`），才能覆寫變數並挑模組。順序是硬性的：

```scss
// src/assets/styles/main.scss

// 1. functions 先載入（變數運算需要它）
@import 'bootstrap/scss/functions';

// 2. 覆寫變數 —— 必須在 variables 之前
//    Bootstrap 的變數都標 !default，晚設就無效
$primary: #0d6efd;      // 佔位色，實際依設計稿調整
$border-radius: 0.5rem;

// 3. 變數、maps、mixins、root
@import 'bootstrap/scss/variables';
@import 'bootstrap/scss/variables-dark';
@import 'bootstrap/scss/maps';
@import 'bootstrap/scss/mixins';
@import 'bootstrap/scss/root';

// 4. 按需挑模組 —— 用得到才引
@import 'bootstrap/scss/reboot';
@import 'bootstrap/scss/grid';
@import 'bootstrap/scss/buttons';
@import 'bootstrap/scss/forms';
@import 'bootstrap/scss/modal';
@import 'bootstrap/scss/dropdown';
@import 'bootstrap/scss/toast';

// 5. utility API —— 要用 .mt-3 / .d-flex 這類 class 就必須引，且 api 一定放最後
@import 'bootstrap/scss/utilities';
@import 'bootstrap/scss/utilities/api';
```

> **注意順序的三個雷**：變數覆寫必須在 `variables` **之前**；`utilities/api` 必須在所有模組**之後**；`functions` 必須在覆寫**之前**（否則 `shade-color()` 這類函式無法使用）。

## 簡易替代（開發快、bundle 較大）

不需要客製主題時，整包吃下來即可：

```scss
@use 'bootstrap/scss/bootstrap' with (
  $primary: #0d6efd,
);
```

> Dart Sass 已將 `@import` 標為 deprecated，但 Bootstrap 5 官方的按需引入路徑目前仍以 `@import` 為準（`@use` 無法在中途插入變數覆寫）。若建置時出現 deprecation 警告屬預期，可暫時忽略；不要為了消警告而改動上面的順序。

## 自訂樣式

- 間距、字級、色彩優先用 utility class（`.mt-3`、`.fs-5`、`.text-muted`），少寫自訂 CSS。
- 真的需要自訂時：Vue 放 `<style scoped>`；Angular 放元件自己的樣式檔（預設即元件範圍）。
- 需要新增自己的 utility class 時，用 Bootstrap 的 utility API（在 `@import 'bootstrap/scss/utilities'` 之後、`utilities/api` 之前 `map-merge` 進 `$utilities`），不要硬刻。
