import cv2
import serial
import time
import threading
import queue
import tkinter as tk
from tkinter import *
from tkinter import ttk
from pathlib import Path
from collections import deque
import numpy as np
from joblib import load
import os
from ultralytics import YOLO
from LivePlot_prediction import LivePlot

# ───── CONFIGURATION ─────
ESP_IP = "192.168.4.1"
URL = f"http://{ESP_IP}/stream"
MODEL = Path("runs/detect/train5/weights/best.pt")
IMG_SZ = 640
CONF = 0.30
THR_PX = 40
PORT = 'COM7'
BAUD = 9600
SAMPLE_RATE = 10
BASELINE_DURATION_SEC = 3
MIN_RETURN_LENGTH = 10
BUFFER = 5
MAX_WINDOW_SIZE = 1000
PLOT_WINDOW_SIZE = 100

# ───── GLOBAL STATE ─────
s1_data = deque(maxlen=MAX_WINDOW_SIZE)
s2_data = deque(maxlen=MAX_WINDOW_SIZE)
baseSig = None
sensor_base = 0
baseline_collected = False
grasping = False
return_count = 0
sample_count = 0
grasp_started = False
grasp_ended = False

data_queue = queue.Queue()

# Load LDA model
model_path = os.path.join(os.path.dirname(__file__), 'lda_model.joblib')
lda_model = load(model_path)

# Live plot setup
live_plot = LivePlot(PLOT_WINDOW_SIZE, SAMPLE_RATE)

# Serial connection
arduino = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)

# ───── Functions ─────
def compute_baseline():
    global baseSig, sensor_base
    baseSig1 = np.mean(list(s1_data)[:BASELINE_DURATION_SEC * SAMPLE_RATE])
    baseSig2 = np.mean(list(s2_data)[:BASELINE_DURATION_SEC * SAMPLE_RATE])
    baseSig = max(baseSig1, baseSig2)
    baseSig = baseSig * 3 if baseSig < 50 else baseSig
    sensor_base = 0 if baseSig1 > baseSig2 else 1
    live_plot.set_baseline(baseSig)

def feature_extraction(s1_window, s2_window):
    max_s1 = max(max(s1_window), 1)
    max_s2 = max(max(s2_window), 1)
    return [max_s1, max_s2, max_s1 / max_s2]

def show_prediction(prediction, root):
    material = 'Soft Material' if prediction == 0 else 'Hard Material'
    result_lbl.config(text=material)

def model_prediction(featureVector, root):
    y_pred = lda_model.predict([featureVector])
    show_prediction(y_pred[0], root)

def read_serial():
    global grasping, return_count, baseline_collected
    trial_start_index = 0
    while True:
        if arduino.in_waiting > 0:
            line = arduino.readline().decode('utf-8').strip()
            if line:
                try:
                    sensor1_str, sensor2_str = line.split(',')
                    sensor1, sensor2 = int(sensor1_str), int(sensor2_str)
                    s1_data.append(sensor1)
                    s2_data.append(sensor2)
                    live_plot.update_data(sensor1, sensor2)
                    if not baseline_collected and len(s1_data) >= BASELINE_DURATION_SEC * SAMPLE_RATE:
                        compute_baseline()
                        baseline_collected = True
                        continue

                    if not baseline_collected:
                        continue

                    currentVal = max(sensor1, sensor2)
                    if not grasping and currentVal > baseSig:
                        grasping = True
                        trial_start_index = len(s1_data) - BUFFER - 1
                        live_plot.add_grasp_start_line(trial_start_index / SAMPLE_RATE)
                    elif grasping:
                        if currentVal < baseSig:
                            return_count += 1
                        else:
                            return_count = 0
                        if return_count >= MIN_RETURN_LENGTH:
                            trial_end_index = len(s1_data) + BUFFER - 1
                            live_plot.add_grasp_end_line(trial_end_index / SAMPLE_RATE)
                            trial_s1 = list(s1_data)[trial_start_index:trial_end_index]
                            trial_s2 = list(s2_data)[trial_start_index:trial_end_index]
                            fv = feature_extraction(trial_s1, trial_s2)
                            data_queue.put(fv)
                            grasping = False
                            return_count = 0
                except ValueError:
                    continue

def detect_loop(target_var: StringVar, show_vid: IntVar, q: queue.Queue):
    model = YOLO(MODEL)
    cap = cv2.VideoCapture(URL)
    if not cap.isOpened():
        q.put("Stream open failed")
        return

    cX, cY = IMG_SZ // 2, IMG_SZ // 2
    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break
        res = model.predict(frame, imgsz=IMG_SZ, conf=CONF, verbose=False)[0]
        tgt = target_var.get().strip().lower()
        found = None
        for b in res.boxes:
            if model.names[int(b.cls[0])].lower() == tgt:
                x1, y1, x2, y2 = map(int, b.xyxy[0])
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                cy -= int(IMG_SZ * 0.04)  # 4 cm offset
                found = (cx, cy)
                if show_vid.get():
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                break
        if show_vid.get():
            if found:
                cv2.arrowedLine(frame, (cX, cY), found, (255, 255, 255), 2, tipLength=.3)
                if abs(found[0] - cX)**2 + abs(found[1] - cY)**2 < THR_PX**2:
                    cv2.putText(frame, "GRAB!", (cX - 60, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
            cv2.imshow("ESP32-YOLO", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                show_vid.set(0)
                cv2.destroyAllWindows()
    cap.release()
    cv2.destroyAllWindows()

# ───── GUI Setup ─────
root = Tk()
root.title("Robotic Hand Controller")
root.configure(bg="black")

font_cfg = ("Arial", 16)
fg_cfg = {"fg": "white", "bg": "black", "font": font_cfg}

Label(root, text="Target:", **fg_cfg).grid(row=0, column=0, padx=6, pady=6)
options = ["cube", "cylinder"]
target = StringVar(value=options[0])
opt_menu = OptionMenu(root, target, *options)
opt_menu.config(**fg_cfg, highlightthickness=0)
opt_menu["menu"].config(bg="black", fg="white", font=font_cfg)
opt_menu.grid(row=0, column=1, padx=6)

show_vid = IntVar(value=1)
Checkbutton(root, text="Show video", variable=show_vid, selectcolor="black", **fg_cfg).grid(row=0, column=2, padx=6)

result_lbl = Label(root, text="", font=("Arial", 24, "bold"), fg="white", bg="black")
result_lbl.grid(row=1, column=0, columnspan=3, pady=10)

def toggle():
    t = threading.Thread(target=detect_loop, args=(target, show_vid, queue.Queue()), daemon=True)
    t.start()
    live_plot.start()

Button(root, text="Start", command=toggle, **fg_cfg).grid(row=2, column=0, columnspan=3, pady=20)

# ───── Background Threads ─────
threading.Thread(target=read_serial, daemon=True).start()

def poll_prediction():
    if not data_queue.empty():
        fv = data_queue.get()
        model_prediction(fv, root)
    root.after(100, poll_prediction)

root.after(100, poll_prediction)
root.mainloop()
