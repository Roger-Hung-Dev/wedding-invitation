# 外部素材登記（build_props.py 會讀這個檔；在 build_props 的命名空間執行，可以直接用 ext_item、PAL）
# 一個下載的模型一行 ext_item()。檔案放 external/<代號>/source/<檔名>（source/ 不進版控，clone 後照 source.page 重新下載）
#
# ext_item("cake", "結婚蛋糕（三層）", "（未用）", "wedding_cake.glb", cat="party:派對",
#          source=dict(site="Poly Pizza", page="https://poly.pizza/m/<id>", title="Wedding Cake", author="<作者>", license="CC BY 3.0", downloaded="2026-10-12"),
#          size=0.45, fit="height", rz=0, colors={"Frosting": "cream", "Berry": "straw"})
#
# 參數：size＋fit（max／height／width）把模型縮到真實尺寸（公尺）；rz 轉到正面朝 -Y；
#       colors 用「原材質名的片段 → 色票名（PAL）或 #hex」指定顏色，沒指定的自動取原色再粉嫩化（sat、light 可調）；
#       bevel＝倒圓寬度（模型最長邊的比例，預設 0.04；造型細碎的調小）；keep＝只留名稱含這些字的網格
# license 是 CC BY 開頭的，ATTRIBUTION.md 也要加一列。
