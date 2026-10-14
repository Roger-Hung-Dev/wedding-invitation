---
description: 列出目前這個 repo 已建立的所有 Git worktree。
argument-hint: （不需參數）
---

請列出目前這個 repo 已建立的所有 Git worktree，全程使用繁體中文。

## 步驟

### 1. 取得資料

```bash
git worktree list --porcelain
git branch --list "*-WT"
```

需要每個 worktree 的乾淨程度時，對各個路徑執行
`git -C "{路徑}" status --porcelain`（輸出為空即為乾淨）。

### 2. 用表格回報

| worktree 路徑 | 分支 | 種類 | 有未提交變更 | 推導的來源分支 |
| --- | --- | --- | --- | --- |

- **種類**：主工作區（`git worktree list` 的第一筆）／額外 worktree。
- **推導的來源分支**：分支名以 `-WT` 結尾時，去掉後綴即為來源分支；
  其餘填 `—`。這欄只是推導，不代表 git 記錄了這層關係。
- detached HEAD 的 worktree 在「分支」欄標明 `(detached at {短 hash})`。

### 3. 補充說明

- 若只有主工作區一筆，直接講「目前沒有額外的 worktree」，不要硬湊表格。
- 若 `git worktree list` 出現標示 `prunable` 的項目（目錄已被手動刪掉但記錄還在），
  指出來並建議跑 `git worktree prune`，**但不要自己跑**。
- 表格後面附一句：合併與清理用 `/git-worktree-merge`，新增用 `/git-worktree-create`。
