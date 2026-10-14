# 實驗：嘟嘴形態鍵換成「只有嘴唇往前噘」（不用模板動作），看凹窩還在不在
import bpy, numpy as np, os
me = bpy.data.objects["AI_Driven"].data; kb = me.shape_keys.key_blocks
B = np.array([k.co[:] for k in kb["Basis"].data]); K = np.array([k.co[:] for k in kb["mouthPucker"].data])
mode = os.environ.get("PKMODE", "push")
mz = -0.015
dz = np.abs(B[:, 2] - mz)
w = np.clip(1 - (B[:, 0] / 0.17) ** 2, 0, 1) * np.clip(1 - dz / float(os.environ.get("PKR", 0.12)), 0, 1) * (B[:, 1] < -0.4)
w = w * w * (3 - 2 * w)
D = np.zeros_like(B); D[:, 1] = -0.03 * w
if mode == "mix":  # 模板動作只留唇線附近（窄帶、下唇那側更窄），再加往前噘
    wn = np.clip(1 - (B[:, 0] / 0.17) ** 2, 0, 1) * np.clip(1 - np.where(B[:, 2] < mz, dz / 0.045, dz / 0.07), 0, 1) * (B[:, 1] < -0.4)
    wn = wn * wn * (3 - 2 * wn)
    D = (K - B) * wn[:, None] + D
if mode == "xz":  # 模板動作只取左右收攏（x）＋少量上下，往前噘用自己平滑的推量
    T_ = (K - B) * w[:, None]
    T_[:, 1] = 0; T_[:, 2] *= 0.5
    D = T_ + D * float(os.environ.get("PKF", 1.4))
if mode == "lipsonly":  # 模板動作只留嘴唇帶
    D = (K - B) * w[:, None]
K2 = B + D
for i, k in enumerate(kb["mouthPucker"].data): k.co = K2[i]
print("[pk] mode", mode)
