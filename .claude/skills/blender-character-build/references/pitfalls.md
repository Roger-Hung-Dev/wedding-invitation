# 常見坑（都實際踩過）

| 症狀 | 原因 | 解法 |
| --- | --- | --- |
| 匯入 VRM 報 `'NoneType' object has no attribute 'scene'` | 和 `read_homefile` 在同一次 MCP 呼叫，或在背景 Blender 匯入 | 開新檔、匯入分兩次呼叫；只在 GUI 匯入，並用 `temp_override(window=…)`（`character_setup.import_vrm` 已處理） |
| 匯入後多出空的 `Armature`、`Armature.001` | 失敗的匯入留下的 | `import_vrm` 會清掉沒有子物件的骨架 |
| 骨架 `rotation_euler` 改了沒反應 | VRM 骨架預設 `rotation_mode = QUATERNION` | `organize()` 已改成 XYZ |
| 補皮膚的接縫看得到一條線 | MToon 輪廓線在網格切口描線；接縫法線差 13° | 皮膚材質輪廓線關掉（`outline_width_mode = "none"`）；`finish()` 轉移接縫法線 |
| 補丁上有雜訊斑點 | 複製的皮膚材質帶法線貼圖，補丁 UV 不對應 | `fill_material` 拿掉 `normal_texture` |
| 改材質後輪廓線又跑回來 | VRM add-on 依材質設定自動補 outline 修改器 | 改材質的 `outline_width_mode`，不要只關修改器 |
| 補丁接縫一圈黑帶 | 皮膚貼圖畫了內衣帶 | `delete_dark_band()` |
| 背面看起來粉紅一片、有怪亮塊 | MToon 背光面陰影色是粉色、背光燈造成硬邊亮塊 | 判斷背面時轉角色 180°，用正面燈光拍 |
| 地板一片死白 | Principled 地板的鏡面反射＋太陽光 | 地板 Roughness 1、Specular 0、顏色調暗（studio.py 已處理） |
| 換便服後鞋子還是服裝的顏色 | 鞋子材質被換成服裝版 | `wear("base")` 會找回原本名稱含 Shoes 的材質 |
| MCP 回「No data received」 | 呼叫超過 120 秒（Blender 其實還在跑） | 長工作改背景 Blender（bl_cli）；確認用檔案或進度檔，不要重送同一個指令 |
| 長時間渲染後 Blender 當掉 | 連續幾百格 | 以動作／段落為單位存進度，重跑接續；請使用者重開 Blender 後從 .blend 繼續 |
| GUI 匯入時 Blender 有未存的別的檔 | 使用者正在用 | 先回報，不要直接 `read_homefile` |
| 照片上的人比角色胖瘦、高矮不同 | VRoid 捏的是臉，身體是 VRoid 預設 | 服裝照輪廓做，不要為了貼合照片去改身體；差異寫進回報 |
