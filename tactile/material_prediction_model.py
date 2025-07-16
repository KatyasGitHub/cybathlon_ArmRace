import serial
import time
import numpy as np
from collections import deque
import matplotlib.pyplot as plt
from joblib import load
import tkinter as tk
import threading
from LivePlot_prediction import LivePlot
import os

# === CONFIGURATION ===
SAMPLE_RATE = 10  # Hz
BASELINE_DURATION_SEC = 3
MIN_RETURN_LENGTH = 10  # samples
buffer = 5 # samples
MAX_WINDOW_SIZE = 1000  # for deque
PORT = 'COM7'  # <-- Update as needed
BAUD = 9600
window_size = 100  # samples for plotting window

# === GLOBAL STATE ===
s1_data = deque(maxlen=MAX_WINDOW_SIZE)
s2_data = deque(maxlen=MAX_WINDOW_SIZE)
time_buffer = deque(maxlen=window_size)
baseSig = None
sensor_base = 0
baseline_collected = False
grasping = False
return_count = 0
trial_start_index = 0
sample_count = 0
grasp_started = False
grasp_ended = False
trial_start_time = 0
trial_end_time = 0

#load lda model 
script_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(script_dir, 'lda_model.joblib')
lda_model = load(model_path)

# === PLOT SETUP ===
live_plot = LivePlot(window_size,SAMPLE_RATE)

# === SERIAL SETUP ===
arduino = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)  # Wait for serial connection to establish

# === FUNCTIONS ===
def compute_baseline():
    global baseSig, sensor_base
    baseSig1 = np.mean(list(s1_data)[:BASELINE_DURATION_SEC * SAMPLE_RATE])
    baseSig2 = np.mean(list(s2_data)[:BASELINE_DURATION_SEC * SAMPLE_RATE])
    baseSig = max(baseSig1, baseSig2)

    if baseSig < 10:
        baseSig = 50
    elif baseSig < 50:
        baseSig *= 3

    sensor_base = 0 if baseSig1 > baseSig2 else 1
    print(f"Baseline computed: {baseSig:.2f} from Sensor {sensor_base + 1}")
    live_plot.set_baseline(baseSig)

def feature_extraction(s1_window, s2_window):
    max_s1 = max(max(s1_window), 1)
    max_s2 = max(max(s2_window), 1)
    ratio = max_s1 / max_s2
    return [max_s1, max_s2, ratio]

def show_prediction(prediction):
    material = 'Soft Material' if prediction == 0 else 'Hard Material'
    root = tk.Tk()
    root.overrideredirect(True)
    root.configure(bg='white')
    text_box = tk.Label(root, text=material, font=("Helvetica", 28, "bold"), bg='white')
    text_box.pack(padx=40, pady=30)
    root.after(2000, root.destroy)
    root.mainloop()

def model_prediction(featureVector):
    global lda_model
    y_pred = lda_model.predict([featureVector])
    print(f"Prediction: {y_pred[0]}")
    show_prediction(y_pred[0])

def read_serial():
    global grasping, trial_start_index, return_count, baseline_collected
    global grasp_started, grasp_ended, trial_start_time, trial_end_time, sample_count
    while True:
        if arduino.in_waiting > 0:
            line = arduino.readline().decode('utf-8').strip()
            if line:
                try:
                    sensor1_str, sensor2_str = line.split(',')
                    sensor1 = int(sensor1_str)
                    sensor2 = int(sensor2_str)

                    s1_data.append(sensor1)
                    s2_data.append(sensor2)
                    sample_count += 1

                    live_plot.update_data(sensor1, sensor2)

                    if not baseline_collected and len(s1_data) >= BASELINE_DURATION_SEC * SAMPLE_RATE:
                        compute_baseline()
                        baseline_collected = True
                        continue

                    if not baseline_collected:
                        continue

                    currentVal = s1_data[-1] if s1_data[-1]>s2_data[-1] else s2_data[-1]

                    if not grasping:
                        if currentVal > baseSig:
                            grasping = True
                            trial_start_index = len(s1_data) - buffer - 1
                            trial_start_time = trial_start_index / SAMPLE_RATE
                            grasp_started = True
                            grasp_ended = False
                            live_plot.add_grasp_start_line(trial_start_time)
                            print("Grasp started")
                            return_count = 0
                    else:
                        if currentVal < baseSig:
                            return_count += 1
                        else:
                            return_count = 0

                        if return_count >= MIN_RETURN_LENGTH:
                            trial_end_index = len(s1_data) + buffer - 1
                            trial_end_time = trial_end_index / SAMPLE_RATE
                            grasp_started = False
                            grasp_ended = True
                            live_plot.add_grasp_end_line(trial_end_time)
                            print("Grasp ended")

                            
                            trial_s1 = list(s1_data)[trial_start_index :trial_end_index]
                            trial_s2 = list(s2_data)[trial_start_index :trial_end_index]

                            featureVector = feature_extraction(trial_s1, trial_s2)
                            model_prediction(featureVector)

                            grasping = False
                            return_count = 0
                except ValueError:
                    continue
          #  time.sleep(1 / SAMPLE_RATE)

# === INIT BUFFERS FOR PLOTTING ===
force1_buffer = deque(maxlen=window_size)
force2_buffer = deque(maxlen=window_size)

# === START SERIAL THREAD ===
serial_thread = threading.Thread(target=read_serial, daemon=True)
serial_thread.start()

live_plot.start()

# === KEEP ALIVE LOOP ===
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    arduino.close()
    print("Serial connection closed.")



#training model, loaded from memory during use
# featureFile = loadmat('featureVector.mat')
# features = featureFile['featureVector'].squeeze() 
# labelFile = loadmat('material_vector.mat')
# labels = labelFile['material_vector'].squeeze() 
# # Create the LDA model with shrinkage (equivalent to Gamma = 0.5)
# lda_model = LinearDiscriminantAnalysis(solver='lsqr', shrinkage=0.5)
# # Train it
# lda_model.fit(features, labels)
# dump(lda_model, 'lda_model.joblib')