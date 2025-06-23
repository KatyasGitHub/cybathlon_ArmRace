# Cybathlon Object‑Detection Pipeline

End‑to‑end workflow for **capturing**, **labelling**, **training** and **running** a YOLOv8 detector that recognises *spheres, cubes and cylinders* from an **ESP32‑CAM** Wi‑Fi stream and returns each object’s **image‑plane centre**.

---

## 1 · Prerequisites

| Component                           | Install / command                        | Purpose                   |
| ----------------------------------- | ---------------------------------------- | ------------------------- |
| **ESP32‑CAM** (Ai‑Thinker or clone) | Arduino IDE (use `CameraWebServer` core) | Image source              |
| USB‑TTL adapter                     | –                                        | Flash & serial monitor    |
| **Python ≥ 3.9**                    | Anaconda/Miniconda recommended           | ML + tooling              |
| Ultralytics YOLO v8                 | `pip install ultralytics`                | Training / inference      |
| OpenCV                              | `conda install -c conda-forge opencv`    | Stream decoding & drawing |
| LabelImg                            | Portable zip or `pip install`            | Bounding‑box labelling    |

---

## 2 · Capture a Dataset

### 2.1 Flash the ESP32‑CAM

1. Open **`camera/arduino_code/esp32cam_stream/esp32cam_stream.ino`** in the Arduino IDE.
2. Fill in SSID/PASS if you prefer STA mode (defaults to soft‑AP).
3. Upload. The serial monitor prints:

   ```text
   AP SSID : CybathlonCamera
   AP PASS : BestTeam2025
   SNAPSHOT: http://192.168.4.1/capture.jpg
   STREAM  : http://192.168.4.1/stream
   ```

### 2.2 Automated snapshot grabber — `collect_data.py`

```bash
conda activate cyba   # or any env with requests installed
python tools/collect_data.py \
       --ip 192.168.4.1 \
       --out dataset/images_all \
       --interval 1            # seconds between frames
```

Rotate / move the object while the script runs and stop with **Ctrl‑C**.
Aim for **≥ 300 images *per class*** under varied lighting.

> Prefer manual capture? Open `/capture.jpg` in a browser and hit **Save As…** repeatedly or use `curl -o img%04d.jpg` in a loop.

---

## 3 · Label the Dataset (YOLO format)

1. **Launch LabelImg**

   ```powershell
   labelImg.exe   # or  python -m labelImg.labelImg
   ```
2. Click **`PascalVOC`** in the left toolbar → switches to **YOLO**.
3. **Open Dir** → `dataset/images_all`
   **Change Save Dir** → `dataset/labels_all`.
4. Press **`W`**, draw a rectangle, type the class name once (`sphere`, `cube`, `cylinder`).
   From now on press **Enter** after each new box.
5. **`Ctrl+S`** to save, **`D`** to advance to the next image.

Each image now has a matching `.txt`:

```
<class_id> <x_center> <y_center> <width> <height>   # all 0–1 relative values
```

---

## 4 · Train / val split (80 / 20)

Run the helper once:

```bash
python tools/split_dataset.py
```

It moves images and labels into:

```
dataset/
├─ images/{train,val}/
└─ labels/{train,val}/
```

---

## 5 · Train YOLOv8

1. Create **`data.yaml`**

   ```yaml
   path: dataset
   train: images/train
   val:   images/val
   nc: 3
   names: [cube, cylinder, sphere]
   ```
2. Fine‑tune a tiny model:

   ```bash
   yolo detect train \
        model=yolov8n.pt \
        data=data.yaml \
        epochs=100 \
        imgsz=640 \
        lr0=1e-3
   ```

   Best weights land in `runs/detect/train/weights/best.pt`.

---

## 6 · Real‑Time Inference

### 6.1 Flash streaming firmware

Upload **`esp32cam_stream.ino`** (adds `/stream` MJPEG endpoint and serial LED control).

### 6.2 Run the client

```bash
python stream_infer.py 192.168.4.1   # ESP32‑CAM IP
```

* Shows live window with boxes + centres.
* Saves every detection to `detections.csv`.

---

## 7 · Torch (flash) control

* In the Arduino serial monitor send **`F`** → LED ON, **`O`** → LED OFF.
* Or adapt the firmware to expose `/flash?state=1` and toggle via HTTP.

---

## 8 · Directory Layout

```
project/
├─ firmware/
│  └─ esp32cam_stream/
│     └─ esp32cam_stream.ino
├─ tools/
│  ├─ collect_data.py      # grabs /capture.jpg every N s
│  ├─ split_dataset.py     # 80 / 20 mover
│  └─ …
├─ dataset/
│  ├─ images_all/          # raw captures
│  ├─ labels_all/          # manual labels
│  ├─ images/{train,val}/
│  └─ labels/{train,val}/
├─ runs/                   # YOLO output
├─ stream_infer.py         # real‑time client
└─ README.md
```



