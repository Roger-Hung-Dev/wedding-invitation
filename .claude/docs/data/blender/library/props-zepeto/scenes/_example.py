# 場景外掛範本（底線開頭的檔案 build_props.py 不會讀；複製成 scenes/<key>.py 再改）
# 在 build_props 的命名空間執行，可以直接用：instance()、MB、clay()、p_box／p_cyl／p_sphere／p_lathe／p_tube、M()、light()、PAL
#
# 試做：blender -b --factory-startup -P build_props.py -- SCENE=<key> OUT=D:/render-work/zepeto-props/try
#       （只建這個場景用到的道具＋算單品預覽＋算場景示意，不覆寫素材庫）


def _build(col, cols):
    """col＝這個場景的集合；cols[代號]＝道具集合。地面、牆這種只屬於這個場景的東西直接用 MB 建"""
    MB("ZP_example_ground").add(p_cyl(6, 0.1, 0.04, 64), clay("grass"), M((0, 0, -0.05))).obj(col)
    instance(col, cols["arch"], (0, 1.0, 0))                    # instance(集合, 道具, 位置, rz 度數, 縮放)
    instance(col, cols["hedge"], (-2.7, 1.0, 0))
    instance(col, cols["hedge"], (2.7, 1.0, 0))
    instance(col, cols["table"], (0, -0.8, 0))
    instance(col, cols["chicken"], (0, -0.8, 0.75))             # 桌面高 0.75 m


def _lights():
    """night=True 時才會呼叫：白天的燈已經關掉，回傳自己打的燈（算完會自動關掉）"""
    return [light("POINT", "ZP_ExampleLamp", (1.0, -0.5, 2.6), (0, 0, 0), 120, "#FFD39A", size=0.2)]


SCENE = dict(
    key="example",                         # 檔名同名；預覽圖 previews/scenes/example.jpg、集合 ZP_Scene_Example
    label="場景示意：範例",
    scenes="（未用）",                      # 用在哪部影片的哪幾幕
    group="garden",                         # 展示頁放在哪個分類那一段；新分類寫 "beach:海邊"
    props=["arch", "hedge", "table", "chicken"],   # 用到的道具代號（SCENE= 試做時只建這些）
    camera=((3.0, -6.0, 1.8), (0, 0, 0.9), 35),    # (鏡頭位置, 看的點, 焦距 mm)
    night=False, sky="#A9CFF0",             # 夜景：night=True、sky="#1E2748"、lights=_lights
    lights=None,
    build=_build,
)
