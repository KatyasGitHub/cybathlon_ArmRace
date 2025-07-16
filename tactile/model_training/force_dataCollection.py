# Force data collection script
# arduino must be running, data is read in from serial port
# data collection initialized when script is started and ends with keyboard interupt, data is saved to csv

import serial
import time
import csv
from live_plot import LivePlot
import threading

# Initialize serial port
arduino = serial.Serial(port='COM7', baudrate=9600, timeout=1)
time.sleep(2)  # Wait for Arduino to reset

s1_data = []
s2_data = []

plot = LivePlot(window_size=200)

def read_serial():
    global s1_data, s2_data
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

                    plot.update_data(sensor1, sensor2)

                except ValueError:
                    continue  # skip malformed line

# Run serial reading in separate thread
serial_thread = threading.Thread(target=read_serial, daemon=True)
serial_thread.start()

try:
    plot.start()  # This blocks until window is closed
except KeyboardInterrupt:
    print("Keyboard interrupt detected")

print("\nSaving to CSV...")

# Save data to CSV
with open("sensor_output.csv", mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Sensor1", "Sensor2"])
    for val1, val2 in zip(s1_data, s2_data):
        writer.writerow([val1, val2])

print("Data saved to 'sensor_output.csv'")
