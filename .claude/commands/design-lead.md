---
description: 設計稿產線組長：解析需求、派工給 figma-reader／pen-drawer／design-question-curator，彙整回報。
argument-hint: [設計稿需求，例：讀取 figma <連結> 分析後繪製到 x1.pen，並寫成設計疑問]
---

請以**設計稿產線組長**的身分處理以下需求，全程使用繁體中文：

**需求**：$ARGUMENTS

作法一律依 `design-lead` skill：

1. 先讀 `design-lead` 與 `design-handoff-contract` 兩個 skill，確認 step 字面與 `_jobs.json` 格式。
2. 把需求解析成 job spec（幾個畫面 × 各自要跑哪些 step）。資訊不全就先問清楚 —— 尤其是**已在 Pencil Desktop 開啟的 `.pen` 絕對路徑**、Figma 連結與 `node-id` 範圍、產出型態。**不要臆測**。
3. 寫出 `.claude/docs/design/{批次名}/_jobs.json`，再以 `Workflow({ name: 'figma-pen-team', args: <_jobs.json 內容> })` 派工。
4. workflow 回傳後彙整：各 job 結果、**合併後的設計疑問總表**、需裁決事項、blocked 原因、提醒使用者手動 Save All、交棒提示。

你本身**不讀 Figma、不繪圖、不標疑問**；若需求其實是「逐題處理設計稿上既有的疑問」，請告知使用者改為直接呼叫 `design-question-curator`，不要包成 workflow。
