# 動態分鏡（animatic）：比稿縮圖 → 會動的預覽 mp4

`scripts/animatic.py` 給**還沒有正式素材**的比稿稿用：把每張鏡頭卡縮圖裡的圖層拆開，照規劃表的時間軸讓字幕、角色佔位框、圖示動起來，每版輸出一支預覽片。

| | `render_storyboard.py` | `animatic.py` |
| --- | --- | --- |
| 讀什麼 | v2 照片輪播稿（`NN 分鏡列`）→ storyboard.json | 比稿稿（頂層 `V01 …`～`VNN …` 橫帶，卡片 `鏡-Vxx-yy`）的縮圖圖層＋規劃表 |
| 時間軸來源 | 稿上的標註欄 | 規劃表（字幕、角色的 `（起～訖s）`、轉場欄） |
| 角色 | 不合成 | 佔位框（照 storyboard-pen-format §5 的畫法，依規劃表時段出場） |
| 聲音 | 配樂 | 無 |
| 規格 | 稿上 `規格-*`（預設 1080p60） | 固定 1280×720、30fps、H.264、無聲，每支 ≤ 5.8 MB |

⛔ 兩支程式互不相干，**不要為了 animatic 改 render_storyboard.py／build_storyboard.py／fx_notation.py**（它們有逐格回歸驗證）。

---

## 步驟

工作目錄 `WORK` 放系統暫存或專案外（⚠️ C 槽滿時改放 D 槽，例 `D:/render-work/<名稱>/`）。

### 1. 抽取圖層清單（唯讀，結果由系統自動存檔，不要人工謄寫）

`execute` 的 `Print` 輸出太大時，Claude Code 會把結果**存成檔案**並回傳路徑——這正好避開人工謄寫。輸出不夠大時，在最後加一行 `Print("PAD " + "x".repeat(120000))` 逼它存檔，再用 `grep -v '^PAD'` 去掉。

頂層圖層（`extract_raw.txt`，每行一筆 JSON）：

```js
const R = (v) => Math.round(v * 10) / 10;
const TC = {rectangle:"r",ellipse:"e",frame:"f",text:"x",icon:"i",path:"p"};
const cardOf = {}; const verName = {}; const owner = {}; const out = []; const txtAcc = {};
Get(document, (n, c) => {
  const p = c.parentCtx && c.parentCtx.node ? c.parentCtx.node.id : null;
  if (n.enabled === false) return;
  if (c.depth === 0) { verName[n.id] = n.name; if (/^V\d\d /.test(n.name)) out.push(["@", n.name.slice(0,3), n.name]); return; }
  if (verName[p] && n.name.startsWith("鏡-")) { cardOf[n.id] = n.name.slice(2); return; }
  if (cardOf[p] && n.name === "畫面") { cardOf[n.id] = cardOf[p]; return; }
  if (cardOf[p] && n.name === "縮圖內容") {
    owner[n.id] = { card: cardOf[p], d: 0, top: null };
    out.push(["#", cardOf[p], n.id, n.fill, n.width, n.height]); return;
  }
  if (p && owner[p]) {
    const o = owner[p]; const d = o.d + 1; const top = d === 1 ? n.id : o.top;
    owner[n.id] = { card: o.card, d, top };
    if (n.type === "text") (txtAcc[top] = txtAcc[top] || []).push(String(n.content ?? ""));
    if (d === 1) {
      const b = c.bounds;
      const rec = [n.id, TC[n.type] || n.type, R(b.x), R(b.y), R(b.width), R(b.height), n.rotation ? R(n.rotation) : 0, n.opacity !== undefined ? n.opacity : 1, n.name];
      if (n.type === "text") rec.push({ f: n.fontFamily, w: n.fontWeight, s: n.fontSize, c: n.fill, a: n.textAlign, lh: n.lineHeight, ls: n.letterSpacing, st: n.stroke, sw: n.strokeWidth, ef: n.effect, tg: n.textGrowth, tw: n.width, x: n.x, y: n.y });
      out.push(rec);
    }
  }
}, { depth: 30 });
const lines = out.map((r) => {
  if (r[0] === "#" || r[0] === "@") return JSON.stringify(r);
  const t = (txtAcc[r[0]] || []).join("‖");
  if (r[1] === "x") r.splice(9, 0, t); else r.push(t);
  return JSON.stringify(r);
});
Print("BEGIN-EXTRACT"); Print(lines.join("\n")); Print("END-EXTRACT", out.length);
```

框內文字節點（`extract_nested.txt`，給「框裡的字依時段出現」用）：每筆 `[鏡號, 頂層圖層id, 節點id, 深度, 相對頂層x, 相對頂層y, 寬, 高, 名稱, 內容, 樣式]`，排除 `角色-` 框；相對座標是沿路把每層 `c.bounds.x/y` 加起來（`c.bounds` 是相對父層的局部座標）。

### 2. 匯出圖層 png（唯讀）

```js
Export(ids, "png", "D:/render-work/<名稱>/layers/V01", { scale: 4 })   // 檔名＝<節點id>.png
```

每版匯出：每張卡的 `縮圖內容`（整格，用來驗證）＋它的直屬子節點＋框內文字節點。一版 100～300 個節點約 2～20 秒；一次塞太多版可能被中斷（`interrupted`），分 3 批。

### 3. 字型

稿上英文字型本機多半沒有，從 Google Fonts 的 GitHub 抓到 `WORK/fonts/`（檔名對照見程式的 `FAMILY_FILES`）。中文用系統的 Noto Sans TC／Noto Serif TC 可變字型；英文字型缺字時自動改用 Noto Sans TC。

### 4. 對應報告 → 定位 → 抽格

```
python $SK/animatic.py report --work WORK --plan PLAN.md [V01 …]          # 字幕句 ↔ 縮圖圖層，先看這個
python $SK/animatic.py prep   --work WORK --plan PLAN.md [V01 …] --jobs 14 # 定位＋重組驗證＋抹字（80 格約 9 分鐘）
python $SK/animatic.py still  --work WORK --plan PLAN.md --rules RULES.json V01 3.5 15.2
```

prep 對每格印「重組差異」：把所有圖層依定位疊回去，縮成縮圖尺寸後與整格匯出圖比。幾百個不同像素多半是字邊的次像素差，看 `cache/<版>/<鏡>_rebuild.jpg` 確認；上千就要查。

### 5. 輸出

```
python $SK/animatic.py video --work WORK --plan PLAN.md --rules RULES.json --out OUTDIR --jobs 10 [V01 …]
python $SK/animatic.py index --work WORK --plan PLAN.md --rules RULES.json --out OUTDIR
```

每版先輸出無損中間檔（`WORK/tmp/`），再以 CRF 18 起逐級調高壓到 5.8 MB 內；封面取 ③ 最後一句字幕出現 1.2 秒後。10 版平行約 1～2 分鐘（有 `cam` 鏡頭運動的版本較慢，單版約 5～8 分鐘）。

分批輸出到同一個資料夾時，`index` 加 `--batch N`：保留 index.json 裡其他批的版本、依版號合併，並寫 `batch`／`category` 欄（`category` 取規劃表的「風格類別」，沒有時用 `--category`，例：第一批 `--batch 1 --category 主題扮演`）。

---

## 程式怎麼決定「什麼時候出現」

| 元素 | 規則 |
| --- | --- |
| 字幕（縮圖裡有） | 文字內容對到規劃表的句子 → 照該句時段；一個文字節點含兩句不同時段時依行切開；框裡的字（卡片、對話框）會從框圖抹掉另外疊，框本身從頭就在 |
| 字幕（縮圖沒畫） | 用 PIL 照樣式補畫：優先借同鏡「時段不重疊」的字幕位置與樣式（並以來源字校正字型偏移），否則放安全框底部；沒有借位時依實際畫面檢查對比，不足 3:1 自動改白字或深字 |
| `0% → 99% → 100%` 大標 | 計數：0→99 先快後慢、停在 99 抖兩下、跳 100（時間取動態欄「N s 跳 100」，太晚則取時段結束前 0.6 秒） |
| `3 → 2 → 1` 大標 | 倒數：時段平分給每個數字，照縮圖那個數字的字型重畫 |
| 角色 | 規劃表角色列：位置九宮格、高度百分比、`進場：滑入`；相鄰動作間隔 ≤ 1 秒視為一直在場（框內文字換成下一個動作） |
| 其他圖形 | 整鏡都在；從硬切進入時開頭淡入 0.3 秒（溶接、推移、黑場、閃白進入時由轉場帶入） |
| 轉場 | 照 fx-transition 的時間窗：溶接、推移為交疊型，閃白、黑場、淡出至黑為覆蓋型；標「建議 fx-lab 設計」的用括號前的替代寫法 |

縮圖畫的是某一格的**最後狀態**，動態欄寫的「3.8 秒滑入」「6.3 秒人影擋鏡」要靠規則檔指定（見下）。

## 規則檔（RULES.json）

```jsonc
{
  "V01": {
    "sub_in": {"fx": "bounce"}, "big_in": {...}, "label_in": {...}, "countdown_in": {...},   // 本版預設進場
    "sub_style": {...}, "sub_default_box": [x, y, w, null],                                    // 補畫字幕預設
    "notes": "做出…／簡化…",                                                                    // 寫進 index.json
    "shots": {
      "V01-03": {
        "layers": [ {"match": "名稱正規式 或 id:a,b", "nth": 0, "hide": true, "unfade": true,
                     "show": [起, 訖], "in": {...}, "out": {...}, "loop": [...], "reveal": {...},
                     "move": {...}, "follow": "新郎", "pivot": [x, y], "stagger": 秒, "counter_seq": true} ],
        "subs":   [ {"match": "字幕正規式", "in": {...}, "slot": ["圖層id"], "box": [x, y, w, h], "style": {...}, "show": [起, 訖]} ],
        "counter": {"layer": false, "box": [x, y, w], "style": {...}, "jump": 秒, "b": 秒, "in": {...}},
        "extras": [ {"text": "…", "box": [...], "style": {...}, "show": [...], "in": {...}},
                    {"kind": "arc", "center": [x, y], "r_out": r, "inner": 0.72, "a0": 0, "sweep": 60, "color": "#…", "glow": 14, "z_after": "圖層名"} ],
        "frame_shake": [[秒, 幅度px, 長度]], "bob": [幅度px, 週期], "flash": [[秒, 長度, 峰值]]
      }
    }
  }
}
```

### 第二批（V11～V25）新增的寫法

全部是「規則檔有寫才啟用」，沒寫的鏡走原本的路徑（第一批 250 格逐像素回歸驗證過）。

| 位置 | 寫法 | 用途 |
| --- | --- | --- |
| 規劃表 | `【場景字】`／`【場景字・大標】` | 解析成 `scene: true` 的字幕：跟著場景被鏡頭推拉平移；版本預設進場另設 `scene_in`／`scene_big_in` |
| 規劃表 | `- **風格類別**：浪漫` | `index --batch N` 時寫進 `category` |
| 規劃表 | 角色大小 `高 18%（走近到 32%）`／`（走遠縮到 30%）` | 角色框在該段時間內線性變大／變小（「鏡頭推近到」「升空後縮小」不算，交給 `cam`） |
| 版本 | `"pair": true` | 同時段寫在同一格位置的兩人並排（新郎左、新娘右）；從兩側走到同一格時終點也並排 |
| 版本／鏡 | `"qfps": 12` | 場景、角色框以每秒 12 格抽格（字幕不抽格），黏土定格感 |
| 鏡 | `"cam": {"keys": [[秒, cx, cy, 倍率, "lin"?], …], "ext": [左, 上, 右, 下], "char_key": i, "chars": "world"\|"screen"}` | 3D 場景幕的鏡頭推拉平移（2D 代替）。`(cx, cy)`＝畫面中心對準的縮圖座標；`ext`＝鏡頭要移到縮圖沒畫的地方時延伸的範圍（用縮圖邊緣的顏色帶補）；角色框以第 `char_key` 個關鍵格的鏡頭為準擺在規劃表寫的位置 |
| 鏡 | `"char_boxes": {"新郎": [x, y, w, h]}` | 角色框放進指定位置（拍立得、窗戶、漫畫格、泡泡裡） |
| 鏡 | `"color_spread": {"t", "d", "center", "map": [暗→亮色], "mix"}` | 黑白→彩色擴散的替代：灰階換成暖色漸層，飽和的粉紅保留 |
| 鏡 | `"iris": {"t": 0, "d": 0.4}` | 圓形虹膜打開（老電影開場） |
| 圖層規則 | `"screen": true`／`"front": true` | 不跟鏡頭動（黑邊、觀景窗框、日期戳）／畫在角色框前面（桌面、窗框）。字幕預設不跟鏡頭動，`subs` 規則 `"world": true` 可改 |
| 圖層規則 | `"anchor": {"who": "新娘", "dx", "dy", "ay": "bottom"}` | 黏在角色框上（新娘框下的禮服粉條、頭上的手繪皇冠） |
| 圖層規則 | `"within": [x0, y0, x1, y1]` | 只套到外框中心在範圍內的同名圖層（各漫畫格自己的網點）。⚠️ 整張大小的 path（外框 0,0,480,270）分不出來，改用 `id:` |
| 圖層規則 | `"noclean": true` | 框裡的字保留在原圖（天燈上的數字），不拆出來另外疊 |
| 圖層規則 | `"counter_seq": true, "seq_n": 10` | 逐格亮起的總格數（縮圖只畫 9 格、第 10 格到 100% 才補時） |
| `subs` 規則 | `"hide"`／`"front"`／`"out"`／`"move"` | 不補畫（字已用物件畫出）／畫在角色框前／出場方式／跟著物件移動（字寫在游進來的海龜殼上） |
| `counter` | `"slot": "圖層id"` | 縮圖寫成「99% → 100%」的文字圖層：借它的位置與字型跑計數，原圖層不畫 |
| `counter` | `"slots": ["id", "id", [x, y, w]], "keep": true, "out": {…}` | 倒數每個數字畫在自己的位置（燈泡數字板、氣球、天燈），可累積不消失、可設飛走 |
| `counter` | `"none": true` | 數字已在物件上，不另外畫 |
| `extras` | `{"kind": "rect", "box", "fill", "stroke", "sw", "r", "shape": "ellipse", "text", "style"}` | 縮圖沒畫、規劃表寫了的物件用簡化色塊代替（看板、計程車、桌面、海灘球） |
| `extras` | `{"kind": "copy", "id", "card"?, "dx", "dy", "clean"?}` | 複製縮圖圖層（可取同版別張卡；`clean` 用抹掉字的版本） |
| `extras` | `{"kind": "scene", "card": "V12-02", "exclude": "字幕\|…"}` | 借別張卡的整個場景（規劃表寫「同 ②」、縮圖沒畫的段落） |
| `extras` | `{"kind": "confetti", "origin", "region", "n", "colors", "g", "shape", "aspect", "burst", "seed"}` | 紙花、糖珠、花瓣、氣球（`g` 負值往上飄） |
| 進場 | `blur`（`r0`）／`squash`（`w0`）／`beat`（逐字放大回彈）／`type` 加 `cf`（逐字淡入） | 燭光模糊淡入、黏土壓扁回彈、歌舞節拍跳字、星光逐字亮起 |
| 循環 | `jitter`（`amp`、`period`） | 蠟筆線條每 0.08 秒抖動 |
| 顯現 | `reveal.dir: "iris"` | 從中心往外的圓形顯現（橢圓相框打開） |

- 新種類的 `extras`（rect／copy／scene／confetti）預設畫在所有字幕下面一層；要蓋過字幕或指定層次用 `z`／`z_after`。
- 補畫圖示（🔔🔕🚕📷✦✕✓♥♔✿✋）用 Windows 內建的 `Segoe UI Symbol`（單色），字型表已登記。
- 分批時另開工作目錄（例 `WORK/b2/`），`index --batch 2` 會保留 index.json 裡其他批的版本，依版號合併。

- 座標：`box`、`center` 是縮圖座標（480×270）；`dist`、`move`、`pivot`、`origin` 是 1920 座標；時間一律從本鏡開頭算。
- `in.fx`：`fade`／`pop`（0→110→100%）／`slide`（`from`＋`dist`）／`drop`（由上彈落）／`scale`（`s0`）／`slam`（大→小砸下）／`flip`（垂直翻牌）／`flipx`（水平翻開）／`wipe`（左→右顯現）／`type`（逐字，`rate`）／`bounce`（單字彈跳）／`burst`（從 `origin` 噴出）；皆可加 `delay`。
- `loop.fx`：`blink`（`period`、`min`、`duty`）／`glow`／`pulse`／`float`／`hfloat`／`sway`／`spin`（`dps`，`from`～`until` 之間轉，之後停住）／`drift`／`fall`（重力）／`shake`（`times`）／`steps`（階梯位移）／`gauge`（指針跟百分比轉，配 `pivot`）；`zphase` 讓同規則的多個圖層錯開相位。
- `reveal`：`dir` = `l2r`／`r2l`／`b2t`／`t2b`／`cw`；時間型（`a`、`b`）、跟百分比（`counter: true`）、循環掃描（`period`，可 `shrink`）；可加 `steps`。
- `counter_seq: true`：命中的多個圖層依百分比逐格亮（LED 方塊、航線虛線）。
- `move.ease: "counter"`：位移跟著百分比走（小飛機沿航線）。

## 已知坑

- **匯出圖會裁到筆畫或外擴到陰影，而且不一定對稱**：不能直接用節點 x、y 擺。prep 以「疊上後整體誤差減少最多」的位置為準（不能用「疊上後誤差最小」：深色字疊在深色天空也幾乎沒誤差）；每像素誤差封頂，避免被後面圖層遮住的部分主導；粗搜要用區塊平均縮小，跳格取樣會讓像素字型找錯位置。
- **圖層的 opacity 會烤進匯出圖**（0.3 → alpha 77）：字幕、計數要以完整不透明度出現時，用 `unfade` 除回來。
- **Pencil 單獨匯出「帶陰影的弧形 ellipse」角度會錯**（V07-03 儀表粉紅段）：用 `hide` 藏掉，改用 `extras` 的 `arc` 照節點參數重畫。查參數用 `Get("節點id")`。
- **唯讀守門 hook 比對不分大小寫**：JS 裡出現 `.replace(`、`.delete(` 也會被擋，改用 split／join。
- `execute` 整份文件走訪偶爾回 `interrupted`，重試或改用 `Get(id)` 查單一節點。
- C 槽滿時 `Export` 會報 `ENOSPC`：輸出路徑一律放 D 槽。
- **匯出圖比外框大很多時 prep 會跑很久**：漫畫放射背景外框 1920×1080，匯出卻是 4800×4800，定位要搜幾十萬個位置（V24-01／V24-08 單張跑了一個多小時）。prep 的 `place.json` 是全部跑完才寫，所以別等它：另開一次 prep 只跑其他版本先檢查。
- 匯出的 `Export` 每個檔都會印一行，整批會塞爆上下文：script 最後加 `Print("PAD …")` 讓結果存檔，只 grep 摘要。
- 匯出 id 不必手抄：匯出 script 在 Pencil 裡用同一套走訪規則自己收集（頂層圖層＋縮圖內容＋框內文字）。
- 對應報告裡「（縮圖沒有，PIL 補畫）」的字幕會借同鏡時段不重疊的字幕位置；借到的位置不合（例：借到看板上的場景字、借到窄小的名牌框）時用 `subs` 規則的 `box` 指定。

## 限制（回報時要講清楚）

- 角色是佔位框，不是 3D 角色；沒有配樂與音效。
- 縮圖沒畫的元素（例：動態欄寫「手機往左滑出」但縮圖只畫了後段的貼文框）做不出來，只能讓縮圖裡有的元素照時段出現。
- 大頭照用的是稿上的圓形照片（去背版還沒做）。
- 標「建議 fx-lab 設計」的轉場與特效（像素溶解、VHS 雜訊跳接、新聞色塊擦除、翻頁、3D 角色像素化）先用替代寫法。
