# Blender 角色資料

```
blender/
├── projects/<專案名稱>/          ← 一個角色一個資料夾（blender-creator 建立）
│   ├── project.json             ← 專案設定：who（物件前綴）、輸入檔、階段狀態、服裝、情境清單、網頁文字與網址
│   ├── source/                  ← 使用者給的 .vroid、匯出的 model.vrm、大頭照、全身正背面照（不進版控）
│   ├── <名稱>.blend             ← 基礎檔：角色＋補好的皮膚＋便服（不進版控）
│   ├── <名稱>_costume.blend     ← 服裝檔：基礎檔＋服裝（不進版控）
│   ├── costume.json             ← 服裝規格（格式見 blender-character-build/references/costume-spec.md）
│   ├── scripts/                 ← 這個專案自己的情境模組、自訂服裝元件
│   ├── qa/                      ← metrics.json（穿模/腳底）、motion.json（轉速）、metrics_first.json、tune.json
│   ├── pictures/                ← 圖片成品：手勢圖、表情與腳、服裝正背面、照片對照、posters/、scenes/
│   ├── videos/                  ← 影片成品：turn_*.mp4、costume_moves.mp4、actions/、scenes/
│   ├── report.html              ← 成果網頁（gen_page.py 產生，本機可直接開）
│   └── report_files.json        ← 發布 Artifact 用的檔案清單
├── zepeto/<名稱>/               ← ZEPETO 黏土風 3D 大頭（AI 生成，與 VRoid 角色是兩回事）；格式見
│                                   zepeto-character-face-generation-workflow skill 的 references/handoff.md
└── library/                     ← 預設資料庫（來自新娘專案）
    ├── actions_catalog.json     ← 動作目錄（30 個預設＋擴充的）
    ├── tune_default.json        ← 碰觸類動作的預設參數
    ├── costumes/                ← 服裝規格預設：pink-ballgown.json（新娘第 3 版）＋它的層次元件 costume_extra_pink_ballgown.py
    ├── textures/                ← 情境用貼圖（報紙）
    ├── previews/                ← 手勢、表情與腳、服裝、30 個動作的預覽圖
    └── props-zepeto/            ← ZEPETO 黏土風道具素材庫（45 樣＋8 場景示意，程式建模、標成 Blender 資產）；
                                    用法見裡面的 README.md（use_props.py 的 place_prop()）
```

- 影格 png（量很大）一律在 `D:\render-work\blender-work\<專案名稱>\`（`blender_env.py` 的 WORK；環境變數 `BLENDER_WORK_ROOT` 可覆寫），不放這裡。
- 範例專案：`projects/bride`（新娘怡安），成果頁 https://claude.ai/artifact/12T6gowAFGaBVvSUAawPfa 。
- 相關子代理：`blender-creator`（建角色 01～03）、`blender-scenario-creator`（情境）、`blender-animation-append`（擴充動作）；一條龍用 `/blender-studio`。
- ZEPETO 大頭：`zepeto-analyze-photo-3d-model`（生成）、`zepeto-avatar-crafter`（後處理）、`zepeto-face-rigger`（可動臉：ARKit 52＋臉部骨架，成品在 `zepeto/<名稱>/rig/`）；一條龍用 `/zepeto-character-face-generation-workflow`。
