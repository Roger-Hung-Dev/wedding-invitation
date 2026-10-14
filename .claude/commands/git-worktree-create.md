---
description: 以當前分支建立對應的 Git worktree（分支名稱 + -WT）。
argument-hint: （不需參數；可選：指定 worktree 目錄路徑）
---

請以**當前分支**建立一個對應的 Git worktree，全程使用繁體中文。

指定的 worktree 目錄（可為空）：$ARGUMENTS

## 步驟

### 1. 先確認現況並回報

執行並讀取結果：

```bash
git rev-parse --abbrev-ref HEAD
git status --porcelain
git worktree list
```

把下列資訊列給使用者看：

- **當前分支名稱**
- **將建立的 worktree 分支名稱** ＝ 當前分支 + `-WT`
  （例：當前分支 `main` → `main-WT`；`feat/zepeto-outfit` → `feat/zepeto-outfit-WT`）
- **將建立的 worktree 目錄**：
  - 若使用者有傳入路徑，就用那個路徑。
  - 否則預設**建在 repo 根目錄的上一層**（與 repo 資料夾並排，不是放進 repo 裡面）：
    `{repo的上一層}/{repo資料夾名}-{分支名}-WT`，
    其中分支名把 `/` 與其他不適合當路徑的字元換成 `-`。

    範例（repo 在 `D:\SideProject\wedding-invitation`、分支 `main`）：

    ```
    D:\SideProject\
    ├── wedding-invitation\                 ← repo（主工作區）
    └── wedding-invitation-main-WT\         ← 新建的 worktree
    ```

  用 `git rev-parse --show-toplevel` 取得 repo 根目錄，再取它的上一層，
  **不要用當前工作目錄推導** —— 指令可能是在 repo 的子目錄底下執行的。

### 2. 先擋掉這幾種情況（發現就停下來回報，不要硬做）

- 當前是 detached HEAD（`git rev-parse --abbrev-ref HEAD` 回 `HEAD`）。
- 當前分支名稱已經以 `-WT` 結尾 —— 那本身就是一個 worktree 分支，
  再切一層只會讓命名與合併關係亂掉。
- `{分支}-WT` 分支已存在，或該分支已經被某個 worktree 佔用
  （看 `git worktree list` 與 `git branch --list "*-WT"`）。
- 預設目錄已存在且非空。

### 3. 用 `AskUserQuestion` 詢問是否建立

把第 1 步的三項資訊（分支、新分支、目錄）攤出來，讓使用者確認。
使用者說不要就直接結束，不做任何變更。

### 4. 建立

```bash
git worktree add -b "{分支}-WT" "{目錄}" "{分支}"
```

`-b` 會以當前分支為起點建立新分支並簽出到該目錄。

### 5. 回報

建立完成後執行 `git worktree list` 並回報：

- 新 worktree 的**絕對路徑**與分支名稱。
- 提醒使用者：新 worktree 只有**已 commit** 的檔。主工作區裡沒 commit 的檔（多個 session 共用，常有幾十筆）、被 `.gitignore` 排除的檔（`.claude/settings.local.json` 的 MCP 密鑰、`.blend`、參考照片）都不會出現在那裡；要用的話自己複製過去，密鑰檔不要 commit。
- 提醒使用者：主工作區仍停在原分支，兩邊互不影響；
  完成後用 `/git-worktree-merge` 合併回來源分支並清掉這個 worktree。

失敗的話照實回報 git 的原始錯誤訊息，不要自行猜測原因後改用別的做法繞過去。
