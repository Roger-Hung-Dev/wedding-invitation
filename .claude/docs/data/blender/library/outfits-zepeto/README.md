# ZEPETO 穿戴物品素材庫

衣服、配件、鞋子。每套服裝一個資料夾，用 `/zepeto-clothing-generation-workflow` 新增或修改。
2026-10-14 起新衣服照參考照刻細節＋寫實布料（配方在 skill 的 `scripts/garment_detail.py`）；下表標「黏土風」的是之前定案的舊款，之後要照新做法重做。

```
outfits-zepeto/
├── catalog.json            # 總目錄：每套的代號、名稱、狀態、適用身體、審看頁網址
├── _drafts/<代號>-v2/       # 已定案、下游在用的一套要大改時，在這裡試做（不蓋掉下游正在用的 outfit.blend）；換版時機先問導演端
└── <服裝代號>/
    ├── outfit.py           # 用哪些配方、參數、顏色（配方在 skill 的 scripts/garment_detail.py、garment_lib.py）
    ├── outfit.json         # 名稱、狀態、物品清單、已知問題、要使用者決定的事、審看頁網址；大蓬裙另有 anim_handoff（給動畫端）
    ├── refs/               # 參考照片（不進版控）＋ analysis.md（進版控）
    └── previews/<身體>/     # 小預覽圖（寬 360，進版控）
```

- 產出的 `.blend` 和檢查圖在 `D:/render-work/zepeto-costume/<服裝代號>/<身體名稱>/`（不在 repo）：`outfit.blend`、`build.json`、各角度 png。
- 身體只用**已出廠**的：`python -I D:/render-work/zepeto-body/scripts/list_bodies.py --released`。
- 衣服是照身體重新長出來的，所以身體出廠新版本後重跑一次就好；不手改 `.blend`。

| 代號 | 名稱 | 狀態 | 身體 |
| --- | --- | --- | --- |
| `groom-beige-3piece` | 新郎米色三件式 | 已定案（2026-10-12） | groom |
| `groom-navy-tux` | 新郎深藍灰西裝 | 備用款 | groom |
| `photographer-black-casual` | 攝影師黑色便服 | 已定案（2026-10-12，黏土風） | photographer |
| `bride-blush-ballgown` | 新娘淡粉平口蓬裙禮服 v1 | 已定案（2026-10-13，黏土風；開場片 B 在用） | bride（v3） |
| `_drafts/bride-blush-ballgown-v2` | 新娘淡粉禮服・細節版 | 使用者說可以（2026-10-14）；等新身形新娘身體出廠、長上去後才換掉 v1 | bride（試做在 v3） |
