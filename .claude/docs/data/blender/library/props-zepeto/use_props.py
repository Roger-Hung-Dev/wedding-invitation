# 把 ZEPETO 黏土風道具素材庫的道具放進目前的 Blender 場景（情境、製作腳本共用）
#   exec(open(r"<本檔路徑>", encoding="utf8").read())   # 或 blender_env 的 use() 搜尋路徑裡加本資料夾
#   place_prop("arch", (0, 0.3, 0))                        # 擺一個實例（輕、可重複擺很多個；材質、形狀跟著素材庫）
#   place_prop("chicken", (0, 0, 0.75), rz=20, parent=bpy.data.collections["Set_Dinner"])
#   col = append_prop("taxi", parent=…)                     # 複製一份可編輯的真物件（要改形狀、拆零件、做動畫時用）
#   list_props()                                            # 列出代號、中文名、用在哪幾幕
# 道具原點都在底部中心、正面朝 -Y；尺寸是真實比例（公尺）。代號與尺寸見 catalog.json。
import bpy, os, json, math

PROPS_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() and __file__.endswith("use_props.py") else \
    r"D:\SideProject\wedding-invitation\.claude\docs\data\blender\library\props-zepeto"
PROPS_BLEND = os.path.join(PROPS_DIR, "zepeto_props.blend")


def list_props():
    cat = json.load(open(os.path.join(PROPS_DIR, "catalog.json"), encoding="utf8"))
    for it in cat["items"]:
        print(it["key"], it["label"], it["scenes"], it.get("size"))
    return cat["items"]


def _load(key, link):
    """載入 ZP_<代號> 集合（同一個檔只載一次）；link=True 是唯讀連結、False 是複製一份進來"""
    name = key if key.startswith("ZP_") else "ZP_" + key
    have = bpy.data.collections.get(name)
    if have is not None and (have.library is not None) == link:
        return have
    if not os.path.exists(PROPS_BLEND):
        raise FileNotFoundError("素材庫還沒建：先跑 build_props.py（見 README.md）→ " + PROPS_BLEND)
    with bpy.data.libraries.load(PROPS_BLEND, link=link) as (src, dst):
        if name not in src.collections:
            raise KeyError("素材庫沒有 %s；可用的：%s" % (name, [c for c in src.collections if c.startswith("ZP_")]))
        dst.collections = [name]
    return dst.collections[0]


def place_prop(key, loc=(0, 0, 0), rz=0.0, scale=1.0, parent=None, link=True, name=None):
    """擺一個集合實例（Empty）；rz 度數；parent＝要放進的集合（預設場景根集合）"""
    col = _load(key, link)
    ob = bpy.data.objects.new(name or ("Prop_" + col.name[3:]), None)
    ob.instance_type = "COLLECTION"; ob.instance_collection = col
    ob.location = loc; ob.rotation_euler = (0, 0, math.radians(rz)); ob.scale = (scale,) * 3 if not hasattr(scale, "__len__") else scale
    (parent or bpy.context.scene.collection).objects.link(ob)
    return ob


def append_prop(key, parent=None):
    """複製一份真物件進場景（可改網格、拆零件、打關鍵影格）；回傳加進去的集合"""
    col = _load(key, link=False)
    (parent or bpy.context.scene.collection).children.link(col)
    return col
