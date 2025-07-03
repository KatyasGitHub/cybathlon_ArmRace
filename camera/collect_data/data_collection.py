# # save_frames.py
# import requests, pathlib, keyboard, time
#
# ESP_HOST = "http://192.168.4.1"        # ESP32-Cam AP or LAN IP
# OUT_DIR  = pathlib.Path("dataset")     # dataset/sphere/ … square/
# for cls in ("sphere", "square"): (OUT_DIR/cls).mkdir(parents=True, exist_ok=True)
#
# n = 0
# print("[s]=sphere  [q]=square  [ESC]=quit")
# while True:
#     if keyboard.is_pressed('esc'):
#         break
#
#     r = requests.get(f"{ESP_HOST}/capture.jpg", timeout=5)
#     if r.ok:
#         key = keyboard.read_key()
#         if   key.lower() == 's': cls = "sphere"
#         elif key.lower() == 'q': cls = "square"
#         else: continue           # ignore / skip
#         fname = OUT_DIR/cls/f"{int(time.time()*1000)}.jpg"
#         fname.write_bytes(r.content)
#         print(f"saved {fname}")
#         n += 1
#     time.sleep(0.1)              # ~10 fps max polling
# print(f"collected {n} labelled images")


# save_frames.py
import requests
import pathlib
import time
from pynput import keyboard  # 使用 pynput 不需要 root

ESP_HOST = "http://192.168.0.33"       # ⚠️ 这里改成你的摄像头 IP
OUT_DIR  = pathlib.Path("dataset")     # dataset/sphere/ … cube/ … cylinder/

# ⚠️ 创建文件夹
for cls in ("sphere", "cube", "cylinder"):
    (OUT_DIR/cls).mkdir(parents=True, exist_ok=True)

n = 0
shape = None    # 当前要保存的类别
keep_running = True  # 是否继续运行

print("[s]=sphere (球体)  [q]=cube (立方体)  [c]=cylinder (圆柱体)  [ESC]=quit")

# ------------------------------
# 键盘监听函数
# ------------------------------
def on_press(key):
    global shape, keep_running
    try:
        if key.char.lower() == 's':
            print("[s] pressed: 将保存为 sphere (球体)")
            shape = "sphere"
        elif key.char.lower() == 'q':
            print("[q] pressed: 将保存为 cube (立方体)")
            shape = "cube"
        elif key.char.lower() == 'c':
            print("[c] pressed: 将保存为 cylinder (圆柱体)")
            shape = "cylinder"
    except AttributeError:
        if key == keyboard.Key.esc:
            print("[ESC] pressed: 程序即将退出。")
            keep_running = False
            return False  # 停止监听器

# 启动监听器
listener = keyboard.Listener(on_press=on_press)
listener.start()

# ------------------------------
# 主循环
# ------------------------------
while keep_running:
    try:
        r = requests.get(f"{ESP_HOST}/capture.jpg", timeout=5)
        if r.ok and shape:
            fname = OUT_DIR/shape/f"{int(time.time()*1000)}.jpg"
            fname.write_bytes(r.content)
            print(f"saved {fname}")
            n += 1
            shape = None
    except requests.RequestException as e:
        print(f"请求错误 / Request error: {e}")

    time.sleep(0.1)  # ~10 fps max polling

listener.join()
print(f"共采集了 {n} 张标注图片 / Collected {n} labelled images")
