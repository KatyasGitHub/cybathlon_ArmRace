# run:  python esp32_stream_yolo.py  192.168.4.123
import sys, cv2, time, csv
from pathlib import Path
from ultralytics import YOLO

ESP_IP   = sys.argv[1]              # pass ESP32 IP as first CLI arg
URL      = f"http://{ESP_IP}:81/stream"
MODEL    = "runs/detect/train/weights/best.pt"   # your 3-class checkpoint
SAVE_DIR = Path("detections")
SAVE_DIR.mkdir(exist_ok=True)

model  = YOLO(MODEL)
cap    = cv2.VideoCapture(URL)

fourcc = cv2.VideoWriter_fourcc(*'XVID')
log    = open(SAVE_DIR / "detections.csv", "w", newline="")
csv.writer(log).writerow(["ts","cls","cx","cy","conf"])

print("Press  q  to quit")
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("⚠️  lost stream"); break

    # YOLO inference
    result = model.predict(frame, imgsz=640, conf=0.30, verbose=False)[0]
    for box in result.boxes:
        cls_id = int(box.cls[0])
        name   = model.names[cls_id]      # cube / cylinder / sphere
        x1,y1,x2,y2 = box.xyxy[0]
        cx, cy = int((x1+x2)/2), int((y1+y2)/2)
        conf   = float(box.conf)

        # draw
        cv2.rectangle(frame, (int(x1),int(y1)), (int(x2),int(y2)), (0,255,0), 2)
        cv2.circle(frame, (cx,cy), 4, (0,0,255), -1)
        cv2.putText(frame, f"{name}:{conf:.2f}", (int(x1),int(y1)-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

        csv.writer(log).writerow([time.time(), name, cx, cy, conf])

    cv2.imshow("ESP32-YOLO", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

log.close()
cap.release()
cv2.destroyAllWindows()
