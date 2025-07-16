from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import numpy as np
import sys

class LivePlot:
    def __init__(self, window_size, sample_rate, display_seconds=10):
        self.sample_rate = sample_rate
        self.window_size = window_size
        self.display_seconds = display_seconds

        self.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        self.win = pg.GraphicsLayoutWidget(show=True, title="Live Sensor Plot")
        self.win.setBackground('k')

        self.plot = self.win.addPlot(title="Sensor Signals")
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.plot.setYRange(0, 1000)
        self.plot.addLegend()
        self.plot.setLabel('left', 'Force')
        self.plot.setLabel('bottom', 'Time (Seconds)')

        self.curve1 = self.plot.plot(pen=pg.mkPen('cyan', width=2), name='Sensor 1')
        self.curve2 = self.plot.plot(pen=pg.mkPen('magenta', width=2), name='Sensor 2')

        # Baseline line (horizontal)
        self.baseline_line = pg.InfiniteLine(angle=0, pen=pg.mkPen('blue', style=QtCore.Qt.DashLine))
        self.plot.addItem(self.baseline_line, ignoreBounds=True)

        # Lists to hold multiple grasp start/end vertical lines
        self.grasp_start_lines = []
        self.grasp_end_lines = []

        # Data buffers
        self.data1 = np.zeros(window_size)
        self.data2 = np.zeros(window_size)
        self.time_array = np.zeros(window_size)
        self.time_counter = 0  # running index in samples

        self.baseline = 0

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(50)

    def update_data(self, val1, val2):
        self.data1 = np.roll(self.data1, -1)
        self.data2 = np.roll(self.data2, -1)
        self.time_array = np.roll(self.time_array, -1)

        self.data1[-1] = val1
        self.data2[-1] = val2
        self.time_array[-1] = self.time_counter / self.sample_rate
        self.time_counter += 1

    def add_grasp_start_line(self, time_sec):
        line = pg.InfiniteLine(pos=time_sec, angle=90, pen=pg.mkPen('green', style=QtCore.Qt.DashLine))
        self.plot.addItem(line, ignoreBounds=True)
        self.grasp_start_lines.append(line)

    def add_grasp_end_line(self, time_sec):
        line = pg.InfiniteLine(pos=time_sec, angle=90, pen=pg.mkPen('red', style=QtCore.Qt.DashLine))
        self.plot.addItem(line, ignoreBounds=True)
        self.grasp_end_lines.append(line)

    def update_plot(self):
        num_points = int(self.display_seconds * self.sample_rate)

        if len(self.time_array) < num_points:
            x = self.time_array
            y1 = self.data1
            y2 = self.data2
        else:
            x = self.time_array[-num_points:]
            y1 = self.data1[-num_points:]
            y2 = self.data2[-num_points:]

        self.curve1.setData(x, y1)
        self.curve2.setData(x, y2)

        self.baseline_line.setPos(self.baseline)

        # Always show full window even if little data
        current_time = self.time_counter / self.sample_rate
        start_time = max(0, current_time - self.display_seconds)
        self.plot.setXRange(start_time, start_time + self.display_seconds, padding=0)
        self.plot.setYRange(0, 1000)

    def set_baseline(self, value):
        self.baseline = value

    def start(self):
        self.win.show()
        self.app.exec_()
