# save_frames.py
import requests, pathlib, keyboard, time

ESP_HOST = "http://192.168.0.33"        # ESP32-Cam AP or LAN IP
# # ESP_HOST = "http://192.168.0.33"       # ⚠️ Change this to your camera’s IP address. | ⚠️ 这里改成你的摄像头 IP
OUT_DIR  = pathlib.Path("dataset")     # dataset/sphere/ … square/
for cls in ("sphere", "square"): (OUT_DIR/cls).mkdir(parents=True, exist_ok=True)

n = 0
print("[s]=sphere  [q]=square  [ESC]=quit")
while True:
    if keyboard.is_pressed('esc'):
        break

    r = requests.get(f"{ESP_HOST}/capture.jpg", timeout=15)
    if r.ok:
        key = keyboard.read_key()
        if   key.lower() == 's': cls = "sphere"
        elif key.lower() == 'q': cls = "square"
        else: continue           # ignore / skip
        fname = OUT_DIR/cls/f"{int(time.time()*1000)}.jpg"
        fname.write_bytes(r.content)
        print(f"saved {fname}")
        n += 1
    time.sleep(0.1)              # ~10 fps max polling
print(f"collected {n} labelled images")
