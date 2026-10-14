---
description: 把指定的 worktree 分支合併回來源分支，確認合併成功後才刪除該 worktree。
argument-hint: [worktree 名稱或分支名稱，可省略]
---

請把指定的 worktree 合併回它的**來源分支**，並在確認合併成功後刪除該 worktree，
全程使用繁體中文。

使用者指定的 worktree：$ARGUMENTS

## 步驟

### 1. 列出並確認要合併哪一個

```bash
git worktree list
git branch --list "*-WT"
```

- 把所有 worktree 列給使用者看（路徑 ＋ 分支名稱）。
- **來源分支的推導方式**：把 worktree 分支名稱結尾的 `-WT` 去掉
  （例：`main-WT` → `main`；`feat/zepeto-outfit-WT` → `feat/zepeto-outfit`）。
- 用 `AskUserQuestion` 請使用者確認：**要把哪個 worktree 合併到哪個來源分支**，
  並把「合併方向」原樣攤出來（`X-WT` → `X`）。
  即使使用者已在參數中指定，仍要確認一次方向 —— 方向反了不會有任何錯誤訊息，
  只會把改動合到錯的分支上。
- **來源分支是 `main` 時**（本專案 push 到 `main` 會觸發 Cloudflare Pages 部署正式喜帖網站）：
  - 確認題裡要明講「這次是**合併回 main**」。
  - 同一次 `AskUserQuestion` 多問一題「**這次要不要部署**」（選項：不部署（推薦）／要部署）。
    答案決定第 3 步的合併訊息。就算使用者之前說過「commit」或「合併」，這題也要問。
- 若推導出的來源分支不存在，停下來回報，不要自行挑一個相近的分支。

### 2. 合併前的檢查（任一項不過就停下來回報，不要自行處理）

- **worktree 內沒有未提交的變更**：`git -C "{worktree路徑}" status --porcelain` 必須為空。
  有的話回報有哪些檔案，請使用者先提交或捨棄。
- **主工作區（要合併進去的那一側）**：本專案的主工作區由多個 session 共用，常有幾十筆別人沒 commit 的檔，所以不要求乾淨，改成：
  - 主工作區**目前就在來源分支上**（`git rev-parse --abbrev-ref HEAD` ＝ 來源分支）才繼續。
    不在的話停下來回報，**不要 checkout 切過去** —— 切分支會讓只存在於目前分支的已 commit 檔從磁碟消失，別的 session 正在用的檔會不見。
  - 主工作區不能有**暫存中**的變更：`git diff --cached --quiet` 要成功。
  - 把 `git status --porcelain` 的筆數告訴使用者（「主工作區有 N 筆未 commit 的檔，合併不會動到它們；若和這次合併改到同一個檔，git 會自己拒絕」）。
- 來源分支存在，且沒有被別的 worktree 佔用。

### 3. 合併

主工作區已經在來源分支上（第 2 步確認過），不用 checkout。依第 1 步的答案擇一：

```bash
# 來源分支是 main、不部署（訊息開頭一定要是 [CF-Pages-Skip]，Cloudflare 只認最開頭）
git merge --no-ff -m "[CF-Pages-Skip] Merge branch '{worktree分支}' into main" -m "依使用者要求不部署。" "{worktree分支}"

# 來源分支是 main、要部署；或來源分支不是 main
git merge --no-ff "{worktree分支}"
```

用 `--no-ff` 保留一筆合併紀錄，之後看得出這段工作是從 worktree 來的。
不部署時一定要 `--no-ff`：快轉合併的話最新一筆是 worktree 上的普通 commit，沒有標記，push 後就會部署。
若 git 因為主工作區有未 commit 的檔會被覆寫而拒絕合併，照實回報那幾個檔，不要自己 stash 或刪除（那是別的 session 的工作）。

**發生衝突就停下來**：回報衝突檔案清單，說明目前停在合併中的狀態，
請使用者決定要解衝突還是 `git merge --abort`。**不要自行解衝突，也不要自行 abort。**

### 4. 確認真的合併回去了（沒過就不准刪）

```bash
git branch --merged "{來源分支}"
```

輸出必須包含 `{worktree分支}`。
另外可用 `git log --oneline "{來源分支}".."{worktree分支}"` 再確認一次 —— 應為空輸出
（代表 worktree 分支上沒有任何 commit 是來源分支還沒有的）。

**這兩項只要有一項不成立，就停止，保留 worktree 並回報原因。**

### 5. 刪除 worktree

```bash
git worktree remove "{worktree路徑}"
git branch -d "{worktree分支}"
```

- `git branch -d`（小寫 d）在分支未完全合併時會自己拒絕，這是最後一道保險，
  **不要因為它失敗就改用 `-D` 強刪**。失敗就停下來回報。
- 若 `git worktree remove` 抱怨目錄有殘留檔案，回報實際訊息交給使用者判斷，
  不要自行加 `--force`。

### 6. 回報

- 合併了哪個分支到哪個分支、產生的合併 commit。
- worktree 目錄與分支是否已刪除。
- 提醒使用者這次合併尚未 push。
- 來源分支是 `main` 時再提醒：push 到 `main` 就會觸發部署。不部署的合併訊息已經帶 `[CF-Pages-Skip]`；push 後可到 `https://api.github.com/repos/Roger-Hung-Dev/wedding-invitation/commits/<sha>/check-runs` 確認沒有「Cloudflare Pages」。push 前若又在合併 commit 之後加了別的 commit，最新那筆也要帶標記，否則會部署。
