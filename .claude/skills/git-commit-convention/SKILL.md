---
name: git-commit-convention
description: Git commit 訊息規範（Conventional Commits／約定式提交）—— type(scope)!: subject ＋ body ＋ footer 的格式、9 種 type 的選用判準、BREAKING CHANGE 標註、以及「一個 commit 一件事」的切分原則。任何要執行 git commit 的時候使用：工程代理開發完成後自行提交、或使用者要求「幫我 commit」時都適用。
---

# Git Commit 訊息規範（Conventional Commits）

本規範用於維持 commit 紀錄的清晰，並讓自動化版本日誌（Changelog）得以生成。**所有 commit 一律遵守。**

---

## 1. 訊息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

| 欄位 | 必填 | 說明 |
| --- | :---: | --- |
| **type** | ✅ | 本次提交的類別（全小寫，見下方清單） |
| **scope** | ⬜ | 受影響的範圍、模組或元件（例：`auth`、`api`、`cart`、`ui`） |
| **subject** | ✅ | 簡短描述，**建議不超過 50 個字，結尾不加句點** |
| **body** | ⬜ | 詳細說明。解釋**「為什麼」這樣做**，而非「怎麼做」 |
| **footer** | ⬜ | 關閉 Issue、或標註重大變更（Breaking Change） |

**格式細節**：

- `type` 與 `subject` 之間是 **`: `（冒號＋一個半形空格）**。
- `scope` 有就寫在 `type` 後的括號裡；沒有就整組省略（`feat: 新增…`）。
- **標題、body、footer 之間各空一行。**
- subject 用祈使／描述語氣即可，中文英文皆可。

---

## 2. Type 類別

依 commit 的**實際內容**嚴格選擇：

| Type | 用於 |
| --- | --- |
| 🚀 **feat** | 新增或修改新功能（Feature） |
| 🐛 **fix** | 修復錯誤（Bug） |
| 📝 **docs** | 僅修改文件、註解或說明文件（Documentation） |
| 🎨 **style** | 不影響程式碼邏輯的排版修改（空白、格式化、漏分號等） |
| 🔨 **refactor** | 程式碼重構（既非新增功能也非修復錯誤） |
| ⚡ **perf** | 提升效能、優化速度的程式碼修改（Performance） |
| 🧪 **test** | 新增或修改測試案例（Test） |
| 🔧 **chore** | 建置流程、外部套件或輔助工具的變更（更新 `.gitignore`、修改套件依賴等） |
| ⏪️ **revert** | 撤銷先前的某個 commit |

### 容易選錯的幾組

- **`feat` vs `fix`**：判準是「這個行為**本來就該這樣**，只是壞了」→ `fix`；「這是**新的**行為」→ `feat`。
- **`refactor` vs `perf`**：`refactor` 不改變外部行為也不以效能為目的；**以效能為目的**才是 `perf`。
- **`style` vs `refactor`**：`style` 只動排版空白，**刪掉之後程式碼的 AST 不變**；一旦動到結構就是 `refactor`。
- **`chore` vs `build`／`ci`**：本規範**沒有** `build`／`ci` 兩型，建置流程與工具變更一律歸 `chore`。
- **改文件裡的程式碼範例** → `docs`（改的是文件，不是程式）。

---

## 3. 重大變更（Breaking Change）

調整了不相容舊版本的 API 或架構時，**在 footer 用 `BREAKING CHANGE:` 開頭說明**：

```
refactor(api): 重構使用者資料回傳結構

BREAKING CHANGE: 調整了 /user/profile API 的回傳欄位，將 userId 欄位更名為 id。
```

亦可在 `type`／`scope` 後加 `!` 標示（`refactor(api)!: …`），但 **footer 的說明不可省** —— `!` 只標示「有」，不說明「是什麼」。

---

## 4. 範例

### 單行

```bash
git commit -m "feat(auth): 新增使用者 Google 第三方登入功能"
git commit -m "fix(cart): 修正購物車重複點擊導致數量異常的 Bug"
git commit -m "docs(readme): 更新專案安裝與本地執行步驟說明"
git commit -m "style(ui): 修正導覽列按鈕的間距微調"
```

### 含 body 與 footer

```bash
git commit -m "feat(api): 串接綠界金流付款 API

- 支援信用卡與網路 ATM 轉帳
- 新增金流回應的雜湊值（Hash）驗證機制

Closes #123"
```

> **多行訊息的寫法**：`-m` 帶多行字串即可（如上）。在 Git Bash 用 heredoc（`git commit -F- <<'EOF' … EOF`）也可以，**格式規範完全相同**。

---

## 5. 切分原則 —— 一個 commit 一件事

格式對了，但把五件不相干的事塞進同一個 commit，紀錄一樣沒有用。

- **一個 commit 只有一個 `type` 說得通** —— 若你發現「這個 commit 既是 feat 又是 fix 又是 chore」，那就是三個 commit。
- **能一句話說完 subject** —— 需要用「並且」「順便」「另外」串起來，就是該拆了。
- **順手修的東西單獨提** —— 開發過程中修掉的錯字、格式、無關的小 bug，拆成自己的 `style`／`fix`／`chore`，不要夾帶。
- **body 寫「為什麼」** —— 「怎麼做」看 diff 就知道了；**當初為什麼這樣決定、當時考慮過什麼**，只有 commit 訊息留得住。

---

## 6. 提交前確認

1. **`git status` 與 `git diff --stat`** —— 確認這次要提交的範圍就是你以為的範圍，沒有夾帶不相干的檔案。
2. **選對 `type`** —— 對照第 2 節，尤其注意「容易選錯的幾組」。
3. **`scope` 用專案既有的詞彙** —— 先看 `git log --oneline -20` 看看這個 repo 慣用哪些 scope，沿用它，不要自己另創一套。
4. **有破壞性變更就寫 footer** —— 漏寫的代價是下游升級時毫無預警。

> **本規範由 `enforce-commit-convention` hook 強制** —— `git commit -m` 的訊息不符格式時會被擋下並說明原因。被擋不是重寫得更長，而是**回到第 2 節挑對 type**。

---

## 7. 與其他慣例的關係

- **`Co-Authored-By:` 等既有 footer**：與本規範不衝突，照原本的慣例放在 footer 區即可（與 `Closes #123`、`BREAKING CHANGE:` 併存）。
- **專案若已有自己的 commit 慣例**（看 `git log`）：以專案既有慣例為準，本 skill 是預設值不是覆蓋令。發現衝突就回報，不要自行切換。
