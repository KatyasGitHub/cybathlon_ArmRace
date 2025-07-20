# Cybathlon Object‑Detection Pipeline

End‑to‑end workflow for **capturing**, **labelling**, **training** and **running** a YOLOv8 detector that recognises *spheres, cubes and cylinders* from an **ESP32‑CAM** Wi‑Fi stream and returns each object’s **image‑plane centre**.
---

## 0 · Quick Start

```bash
# clone & enter repo
git clone https://github.com/KatyasGitHub/cybathlon_ArmRace.git -b object_classification
cd cybathlon_ArmRace

# create Python env
conda create -n cyba python=3.10 -y   # or use venv
conda activate cyba

pip install torch==2.1.0+cpu torchvision==0.16.0+cpu torchaudio==2.1.0+cpu \
             -f https://download.pytorch.org/whl/torch_stable.html

# install all Python deps
pip install -r requirements.txt
```

> **Note:** PyTorch wheels in `requirements.txt` target CUDA 12.1. If you have a different CUDA version or want CPU‑only, install the matching wheels first, then run `pip install -r requirements.txt --no-deps`.

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

1. Open **`camera/arduino_code/camera/camera.ino`** in the Arduino IDE.
2. Upload. The serial monitor prints:

   ```text
   AP SSID : CybathlonCamera
   AP PASS : BestTeam2025
   SNAPSHOT: http://192.168.4.1/capture.jpg
   STREAM  : http://192.168.4.1/stream
   ```

### 2.2 Automated snapshot grabber — `collect_data.py`

```bash
conda activate cyba   # or any env with requests installed
python camera/collect_data/data_collection.py \
       --ip 192.168.4.1 \
       --out dataset/images_all 
```

Rotate / move the object while the script runs and stop with **Ctrl‑C**.
Aim for **≥ 150 images *per class*** under varied lighting.

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
python computer_vision/dataset_separation.py
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

[//]: # (   ```yaml)

[//]: # (   path: dataset)

[//]: # (   train: images/train)

[//]: # (   val:   images/val)

[//]: # (   nc: 3)

[//]: # (   names: [paralellepiped, cylinder, sphere] )

[//]: # (   ```)
   
   ```yaml
   path: dataset
   train: images/train
   val:   images/val
   nc: 3
   names: [sphere, cube, cylinder] 
   ```
2. Fine‑tune a tiny model:
please enter the computer_vision folder fisrt:
   ```bash
   cd computer_vision/
   ```

   ```bash
   yolo detect train \
        model=yolov8n.pt \
        data=data.yaml \
        epochs=60 \
        imgsz=640 \
        lr0=1e-3
   ```

   Best weights land in `runs/detect/train/weights/best.pt`.

---

## 6 · Real‑Time Inference

### 6.1 Flash streaming firmware

Upload **`camera.ino`** (adds `/stream` MJPEG endpoint and serial LED control).

### 6.2 Run the client

```bash
python computer_vision/gui_stream.py 192.168.4.1   # ESP32‑CAM IP
```

* Tick **Show video** to see the MJPEG stream.  
* In pointer‑only mode an arrow guides the robot gripper; *GRAB!* appears once the target is centred.

---

## 7 · Torch (flash) control

* In the Arduino serial monitor send **`F`** → LED ON, **`O`** → LED OFF.
* Or adapt the firmware to expose `/flash?state=1` and toggle via HTTP.

---
## 8 · Cleaning Up

```bash
conda deactivate        # leave the env
conda env remove -n cyba # optional: delete the env
```

---



