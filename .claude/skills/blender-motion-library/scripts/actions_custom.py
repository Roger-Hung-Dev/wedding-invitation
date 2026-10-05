# 擴充動作庫：由 blender-animation-append 新增。actions.py 載入後會把 CUSTOM_ACTIONS 併進 ACTIONS／ACT。
#
# 規則（細節見 references/adding-actions.md）：
#   - 一個動作＝一個函式 t∈[0,1) → 姿勢 dict，頭尾相接（t=0 和 t→1 的姿勢一樣）。
#   - 可直接用 actions.py 的工具：arms_down、legs、breathe、seg、bump、ease、s、bs、TUNE、SMILE。
#   - 手要碰到身體、臉、另一隻手時，用 ik=[(side, 手腕, 手肘方向, 指尖方向)]，座標用 bs(...) 包起來（會依體型縮放）。
#   - 代號用英文小寫、不可和既有 30 個重複；中文名稱是網頁上顯示的名字。
#   - 新增後一定要跑 run_analyse（穿模／腳底／轉速）並通過，才算入庫。
#
# 範例（註解掉，當格式參考）：
#
# def a_bow_deep(t):
#     b = bump(t, 0.1, 0.4, 0.6, 0.9)
#     P = arms_down({}, l_fwd=10 * b, r_fwd=10 * b)
#     P["Spine"] = [("X", 45 * b)]; P["Head"] = [("X", 10 * b)]
#     return dict(P, face={"Fcl_ALL_Fun": 0.5, "Fcl_EYE_Close": 0.7 * b})
#
# CUSTOM_ACTIONS = [("bow_deep", "深鞠躬", a_bow_deep, 72)]

CUSTOM_ACTIONS = []
