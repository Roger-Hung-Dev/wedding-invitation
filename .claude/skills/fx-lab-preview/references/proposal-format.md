# 特效提案檔格式

路徑：`.claude/docs/fx-lab/{分類}-{id}.md`，分類用 `motion`／`transition`／`opening`／`ending`。例：`.claude/docs/fx-lab/transition-glow-dissolve.md`。

```markdown
---
id: glow-dissolve
category: transition          # motion | transition | opening | ending
name: 光暈溶接
status: 待裁決                 # 待裁決 | 修訂中 | 否決 | 已入庫
artifact: https://claude.ai/...
created: 2026-10-02
decided:                      # 裁決日期
---

## 使用者原始描述
> （原文照抄，不要改寫）

## 提案

| 項目 | 內容 |
| --- | --- |
| 分鏡寫法 | `光暈溶接 0.8s 120%` |
| 圖示 | lucide `sun` |
| JSON | `{"type":"glow-dissolve","duration":0.8,"bloom":1.2}` |
| 型態 | 交疊型（以切點為中心前後各半） |
| 適用版型 | A、H |
| 演算法 | …（工程師照著能實作的程度） |
| 使用時機 | … |
| 已知坑 | … |

## 版本

| 版本 | 參數 | 差異 |
| --- | --- | --- |
| A | 0.8s、bloom 1.2 | 短促，像閃光燈 |
| B | 1.5s、bloom 1.1 | 柔和，適合抒情段 |

## 與產生器的差距
- （預覽做得到但 Pillow 要換做法的地方；做不到而改成近似的地方）

## 裁決紀錄
| 日期 | 使用者決定 | 處理 |
| --- | --- | --- |
| 2026-10-02 | 採用 B，詞彙改「柔光溶接」 | 已重新發布預覽 |
```
