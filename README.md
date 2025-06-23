Cybathlon Object‑Detection Pipeline

This project lets you capture images with an ESP32‑CAM, label them, fine‑tune a YOLOv8 model to recognise spheres, cubes and cylinders, and finally run real‑time detection & centre extraction from the live Wi‑Fi stream.

1. Prerequisites

Item

Notes

ESP32‑CAM (Ai‑Thinker or clone)

flashed via Arduino IDE

USB‑TTL adapter

for programming & serial monitor

Python ≥ 3.9 + Conda (recommended)

creates isolated envs

Ultralytics YOLO v8

pip install ultralytics

OpenCV

conda install -c conda-forge opencv

LabelImg

portable zip or source clone

(optional) GPU w/ CUDA

speeds up training & inference

2. Capture a Dataset

Flash the snapshot_server sketch (see firmware/esp32cam_stream.ino). After reset the board exposes a soft-AP:

SSID: CybathlonCamera
PASS: BestTeam2025
URL : http://192.168.4.1/capture.jpg

Automated capture with collect_data.pyWe supply a helper in tools/collect_data.py that pings /capture.jpg at a fixed rate (default 1 FPS) and writes numbered files to dataset/images_all/.

conda activate cyba
python tools/collect_data.py \
       --ip 192.168.4.1 \
       --out dataset/images_all \
       --interval 1          # seconds between frames

Rotate / move the object while the script runs. Stop with Ctrl‑C.

If you prefer manual capture, simply open the URL in a browser and save frames, or use a one‑liner curl loop.

Aim for ≥ 300 images per class with varied lighting.

3. Label the Dataset (YOLO format). Label the Dataset (YOLO format)

Launch LabelImg

labelImg.exe  # or python labelImg.py

Settings → YOLO; Open Dir → dataset/images_all.

Change Save Dir → dataset/labels_all.

Press W, draw a box around the object, type the class (sphere, cube, cylinder) once. LabelImg remembers the word—next boxes need only Enter.

Ctrl+S after each image, D to move forward.

Output: one .txt per image

<class_id> <x_c> <y_c> <w> <h>    # all values 0‑1

4. Split Train / Val (80 / 20)

# tools/split_dataset.py
import random, shutil, pathlib
src_img = pathlib.Path('dataset/images_all')
src_lab = pathlib.Path('dataset/labels_all')
imgs = list(src_img.glob('*.*'))
random.shuffle(imgs)
cut = int(0.8*len(imgs))
for split, batch in [('train',imgs[:cut]), ('val',imgs[cut:])]:
    (pathlib.Path(f'dataset/images/{split}')).mkdir(parents=True, exist_ok=True)
    (pathlib.Path(f'dataset/labels/{split}')).mkdir(parents=True, exist_ok=True)
    for img in batch:
        shutil.copy2(img, f'dataset/images/{split}/{img.name}')
        lab = src_lab / f'{img.stem}.txt'
        shutil.copy2(lab, f'dataset/labels/{split}/{lab.name}')

5. Train YOLOv8

data.yaml:

path: dataset
train: images/train
val:   images/val
nc: 3
names: [cube, cylinder, sphere]

Command (tiny model + 100 epochs):

yolo detect train model=yolov8n.pt data=data.yaml epochs=100 imgsz=640 lr0=1e-3

Best weights saved to runs/detect/train/weights/best.pt.

6. Real‑Time Inference from ESP32‑CAM Stream

Flash stream firmware

Use firmware/esp32cam_stream.ino (adds /stream MJPEG + serial flash control).

Python client

# run: python stream_infer.py 192.168.4.1
import sys, cv2, time, csv
from pathlib import Path
from ultralytics import YOLO

ip   = sys.argv[1]
url  = f'http://{ip}/stream'
model = YOLO('runs/detect/train/weights/best.pt')
cap   = cv2.VideoCapture(url)
log   = csv.writer(open('detections.csv','w',newline=''))
log.writerow(['ts','cls','cx','cy','conf'])
print('press q to quit')
while cap.isOpened():
    ret, frame = cap.read();
    if not ret: break
    res = model.predict(frame, imgsz=640, conf=0.3, verbose=False)[0]
    for b in res.boxes:
        x1,y1,x2,y2 = b.xyxy[0]
        cx, cy = int((x1+x2)/2), int((y1+y2)/2)
        cls = model.names[int(b.cls[0])]
        conf = float(b.conf)
        cv2.rectangle(frame,(int(x1),int(y1)),(int(x2),int(y2)),(0,255,0),2)
        cv2.circle(frame,(cx,cy),4,(0,0,255),-1)
        cv2.putText(frame,f'{cls}:{conf:.2f}',(int(x1),int(y1)-5),0,0.6,(0,255,0),2)
        log.writerow([time.time(),cls,cx,cy,conf])
    cv2.imshow('ESP32‑YOLO',frame)
    if cv2.waitKey(1)&0xFF==ord('q'):break
cap.release();cv2.destroyAllWindows()

Now you have live bounding boxes + CSV log with sub‑pixel centres.

7. Flash (torch) Control

In serial monitor send F to turn LED on, O to turn it off.

Or expose /flash?state=1 in firmware and toggle via HTTP from the client.

Directory Layout

project/
├── firmware/
│   └── esp32cam_stream/
│       └── esp32cam_stream.ino
├── tools/
│   ├── collect_data.py        # grabs /capture.jpg every N s
│   ├── split_dataset.py       # 80 / 20 train/val mover
│   └── …                      # (add extra utilities here)
├── dataset/
│   ├── images_all/            # raw captures from ESP32‑CAM
│   ├── labels_all/            # YOLO txts you draw in LabelImg
│   ├── images/
│   │   ├── train/
│   │   └── val/
│   └── labels/
│       ├── train/
│       └── val/
├── runs/                      # auto‑created by YOLO training
├── stream_infer.py            # real‑time PC client
└── README.md                  # this file

(Feel free to add or rename folders—just keep dataset/images and dataset/labels as YOLO expects.)
