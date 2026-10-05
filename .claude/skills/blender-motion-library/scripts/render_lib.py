# 分段渲染：MCP 一次呼叫只有 120 秒，所以每次只算一段，已存在的格子會跳過。exec 在 Blender 裡。
import bpy, os, math, time

sc = bpy.context.scene


def render_seq(out_dir, n, setup, res=(600, 900), budget=95, start=0):
    """setup(i, n) 擺好第 i 格；在 budget 秒內盡量多算，回傳 (已完成格數, 總格數)"""
    os.makedirs(out_dir, exist_ok=True)
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    t0 = time.time()
    for i in range(start, n):
        p = os.path.join(out_dir, f"{i + 1:04d}.png")
        if os.path.exists(p):
            continue
        if time.time() - t0 > budget:
            break
        setup(i, n)
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
    done = sum(1 for i in range(n) if os.path.exists(os.path.join(out_dir, f"{i + 1:04d}.png")))
    return done, n
