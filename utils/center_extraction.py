from ultralytics import YOLO
import cv2, csv
from pathlib import Path

model  = YOLO("runs/detect/train/weights/best.pt")  # trained checkpoint
images = Path("dataset/images/val")                 # folder to test
out_csv = "sphere_centres.csv"

rows = []
for p in sorted(images.glob("*.*")):
    result = model.predict(source=str(p), imgsz=640, conf=0.25, verbose=False)[0]

    for box in result.boxes:          # one row per detected sphere
        # YOLO returns xyxy in pixels; convert to centre
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        conf = float(box.conf)

        rows.append((p.name, cx, cy, conf))

        # (optional) visual check
        img = cv2.imread(str(p))
        cv2.circle(img, (int(cx), int(cy)), 4, (0,255,0), -1)
        cv2.imwrite(f"vis_{p.name}", img)

# save results
with open(out_csv, "w", newline="") as f:
    csv.writer(f).writerows([("filename","cx","cy","conf")] + rows)

print(f"Saved {len(rows)} detections to {out_csv}")
