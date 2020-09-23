import sys, os, random
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib import animation
from matplotlib.figure import Figure
import ctypes
import serial
import numpy as np
import scipy.io
import random
import serial.tools.list_ports
import math
import time
import glob
matplotlib.use('Qt5Agg')

N = 100

class AppForm(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle('Serial Port Real Time Plotter')
        self.ser = None
        self.create_main_frame()
        self.create_status_bar()
        self.serialport_connected = False
        self.textbox.setText('0.0')
        self.xdata = list(range(-N,0,1))
        self.ydata_ch1 = [0 for i in range(N)]
        self.ydata_ch2 = [0 for i in range(N)]
        self.ydata_ch3 = [0 for i in range(N)]
        self.ydata_ch4 = [0 for i in range(N)]
        self.ydata_ch5 = [0 for i in range(N)]
        self.ydata_ch6 = [0 for i in range(N)]
        self.ydata_ch1_cont = []
        self.ydata_ch2_cont = []
        self.ydata_ch3_cont = []
        self.ydata_ch4_cont = []
        self.ydata_ch5_cont = []
        self.ydata_ch6_cont = []

        os.chdir("./outputs")
        self.setFileName()

        self.ydata_raw = []
        self.axes.clear()
        self.axes.grid(True)
        self.axes.set_xlim([-N,0])
        self.axes.set_ylim([0,1.25])
        self.plot_refs = self.axes.plot(self.xdata, self.ydata_ch1, 'r',self.xdata, self.ydata_ch2, 'g',self.xdata, self.ydata_ch3, 'b',self.xdata,self.ydata_ch4, 'y',self.xdata,self.ydata_ch5, 'k',self.xdata,self.ydata_ch6, 'r')
        #self.axes.legend(['Channel 1','Channel 2','Channel 3','Channel 4'],loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=4)
        self.canvas.draw()

        self.background = self.fig.canvas.copy_from_bbox(self.axes.bbox)

        self.timer = QTimer()
        self.timer.setInterval(10)
        self.timer.timeout.connect(self.update_plot)

        self.timer_send = QTimer()
        self.timer_send.setInterval(100)
        self.timer_send.timeout.connect(self.send_data)

    def setFileName(self):
        self.files= []
        for file in glob.glob("*.mat"):
            self.files.append(file)
        
        i = 0
        while True:
            self.filename = "out_" + time.strftime("%Y-%m-%d_%H-%M-%S") + "_"+ str(i) + ".mat"
            if self.filename not in self.files:
                break
            i += 1

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Window Close', 'Are you sure you want to close the window?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            if self.ser is not None:
                self.ser.close()
            event.accept()
        else:
            event.ignore()
    
    def create_main_frame(self):
        self.main_frame = QWidget()
        
        self.dpi = 100
        self.fig = Figure((10.0, 6.0), dpi=self.dpi,tight_layout=True)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        
        self.axes = self.fig.add_subplot(111)
        #self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)

        self.textbox = QLineEdit()
        self.textbox.setMinimumWidth(100)
        
        self.set_button = QPushButton("&Set")
        self.set_button.clicked.connect(self.set_setpoint)
        
        self.show_ch1 = QCheckBox("Show &Channel1")
        self.show_ch1.setChecked(True)
        self.show_ch2 = QCheckBox("Show &Channel2")
        self.show_ch2.setChecked(True)
        self.show_ch3 = QCheckBox("Show &Channel3")
        self.show_ch3.setChecked(True)
        self.show_ch4 = QCheckBox("Show &Channel4")
        self.show_ch4.setChecked(True)
        self.show_ch5 = QCheckBox("Show &Channel4")
        self.show_ch5.setChecked(True)
        self.show_ch6 = QCheckBox("Show &Channel4")
        self.show_ch6.setChecked(True)
        slider_label = QLabel('Setpoint:')
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 65535)
        self.slider.setValue(0)
        self.slider.setTracking(True)
        self.slider.setTickPosition(QSlider.TicksBothSides)

        hbox = QHBoxLayout()
        
        for w in [  self.textbox, self.set_button,
                    slider_label, self.slider]:
            hbox.addWidget(w)
            hbox.setAlignment(w, Qt.AlignVCenter)
        
        hbox2 = QHBoxLayout()
        for w in [  self.show_ch1, self.show_ch2,self.show_ch3,self.show_ch4]:
            hbox2.addWidget(w)
            hbox2.setAlignment(w, Qt.AlignVCenter)
        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        #vbox.addWidget(self.mpl_toolbar)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox)

        hbox3 = QHBoxLayout()
        self.save_mat_button = QPushButton("&Save .mat")
        self.save_mat_button.clicked.connect(self.save_mat)

        self.start_button = QPushButton("&Start")
        self.start_button.clicked.connect(self.connect)

        hbox3.addWidget(self.start_button)
        hbox3.addWidget(self.save_mat_button)
        hbox3.setAlignment(w, Qt.AlignVCenter)
        vbox.addLayout(hbox3)

        hbox4 = QHBoxLayout()
        self.combo_box_ports = QComboBox()
        self.button_update_ports = QPushButton("&Update Ports")
        self.button_update_ports.clicked.connect(self.update_ports)
        hbox4.addWidget(self.combo_box_ports)
        hbox4.addWidget(self.button_update_ports)
        vbox.addLayout(hbox4)
        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)
        self.info_message('Press Start to start plotting')
    
    def update_ports(self):
        self.info_message('Updating Ports...')
        ports = serial.tools.list_ports.comports()
        self.combo_box_ports.clear()
        for port, desc, hwid in sorted(ports):
            self.combo_box_ports.addItem(str(port) + ": " + str(desc))
        self.success_message('Updated Ports')

    def set_setpoint(self):
        try:
            self.slider.setValue(int(float(self.textbox.text())*65565))
        except:
            self.error_message('Parsing error for set value')

    def create_status_bar(self):
        self.status_text = QLabel("")
        self.statusBar().addWidget(self.status_text, 1)

    def add_actions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def create_action(  self, text, slot=None, shortcut=None, 
                        icon=None, tip=None, checkable=False):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            action.triggered.connect(slot)
        if checkable:
            action.setCheckable(True)
        return action

    def connect(self):
        if 'COM' in str(self.combo_box_ports.currentText()):
            com_port = str(self.combo_box_ports.currentText()).split(':')[0]
        else:
            self.error_message('Select COM Port')
            return

        if self.serialport_connected is False:
            try:
                self.ser = serial.Serial(com_port, 115200,timeout=0.2)
                if self.ser.isOpen() == False:
                    self.ser.open()
                self.success_message('Connected to serial port')
                self.start_button.setText('&Stop')
                self.serialport_connected = True
                self.ydata_ch1 = [-1 for i in range(N)]
                self.ydata_ch2 = [-1 for i in range(N)]
                self.ydata_ch3 = [-1 for i in range(N)]
                self.ydata_ch4 = [-1 for i in range(N)]
                self.ydata_ch5 = [-1 for i in range(N)]
                self.ydata_ch6 = [-1 for i in range(N)]
                self.timer.start()
                self.timer_send.start()
            except:
                self.error_message('Connecting to serial port')
            self.setFileName()
        else:
            try:
                if self.ser.isOpen():
                    self.ser.close()
                self.info_message('Disconnected from serial port')
                self.start_button.setText('&Start')
                self.timer.stop()
                self.timer_send.stop()
                self.serialport_connected = False
            except:
                self.error_message('Disconnecting from serial port')

    def save_mat(self):
        try:
            mat_ch1 = np.array(self.ydata_ch1_cont)
            mat_ch2 = np.array(self.ydata_ch2_cont)
            mat_ch3 = np.array(self.ydata_ch3_cont)
            mat_ch4 = np.array(self.ydata_ch4_cont)
            mat_ch5 = np.array(self.ydata_ch5_cont)
            mat_ch6 = np.array(self.ydata_ch6_cont)
            mat_ch3_raw = np.array(self.ydata_raw)
            print(os.getcwd() + '\\' + self.filename)
            scipy.io.savemat(os.getcwd() + '\\' + self.filename, {'channel1': mat_ch1,'channel2': mat_ch2,'channel3': mat_ch3,'channel4': mat_ch4,'channel5': mat_ch5,'channel6': mat_ch6})
            self.success_message('Saved data to out.mat')
        except Exception as e:
            self.error_message('Saving Data ' + str(e))

    def error_message(self,message):
        self.statusBar().showMessage('ERROR: ' + str(message))
        self.statusBar().setStyleSheet('QStatusBar { background-color : red; }')

    def info_message(self,message):
        self.statusBar().showMessage('INFO: ' + str(message))
        self.statusBar().setStyleSheet('QStatusBar { background-color : yellow; }')

    def success_message(self,message):
        self.statusBar().showMessage('SUCCESS: ' + str(message))
        self.statusBar().setStyleSheet('QStatusBar { background-color : green; }')

    def update_plot(self):
        #ser.flushInput()
        #print('new plot')
        if self.ser.isOpen() == False:
            return
        rawData = self.ser.read(15)
        if len(rawData) != 15:
            return
        # print(time.time())
        start = rawData[0]
        channel1 = int.from_bytes([rawData[1],rawData[2]], byteorder='little', signed=False)*1.25/65536
        channel2 = int.from_bytes([rawData[3],rawData[4]], byteorder='little', signed=False)*1.25/65536
        channel3 = int.from_bytes([rawData[5],rawData[6]], byteorder='little', signed=False)*1.25/65536
        channel4 = int.from_bytes([rawData[7],rawData[8]], byteorder='little', signed=False)*150/65536
        channel5 = int.from_bytes([rawData[9],rawData[10]], byteorder='little', signed=False)*150/65536
        channel6 = int.from_bytes([rawData[11],rawData[12]], byteorder='little', signed=False)*150/65536
        channel3_raw = int.from_bytes([rawData[5],rawData[6]], byteorder='little', signed=False)
        self.ydata_raw.append(channel3_raw)
        end = rawData[13]
        if start != 2 and end != 3:
            print('ERROR: Wrong frame')
            return
        print(int.from_bytes([rawData[1],rawData[2]], byteorder='little', signed=False)*1.25/65536)
        print(int.from_bytes([rawData[3],rawData[4]], byteorder='little', signed=False)*1.25/65536)
        print(int.from_bytes([rawData[5],rawData[6]], byteorder='little', signed=False)*1.25/65536)
        print(int.from_bytes([rawData[7],rawData[8]], byteorder='little', signed=False)*150/65536)
        print(int.from_bytes([rawData[9],rawData[10]], byteorder='little', signed=False)*150/65536)
        print(int.from_bytes([rawData[11],rawData[12]], byteorder='little', signed=False)*150/65536)
        # print(time.time())
        print('----')
        # Drop off the first y element, append a new one.
        self.ydata_ch1 = self.ydata_ch1[1:] + [channel1]
        self.ydata_ch2 = self.ydata_ch2[1:] + [channel2]
        self.ydata_ch3 = self.ydata_ch3[1:] + [channel3]
        self.ydata_ch4 = self.ydata_ch4[1:] + [channel4]
        self.ydata_ch5 = self.ydata_ch5[1:] + [channel5]
        self.ydata_ch6 = self.ydata_ch6[1:] + [channel6]

        self.ydata_ch1_cont = self.ydata_ch1_cont + [channel1]
        self.ydata_ch2_cont = self.ydata_ch2_cont + [channel2]
        self.ydata_ch3_cont = self.ydata_ch3_cont + [channel3]
        self.ydata_ch4_cont = self.ydata_ch4_cont + [channel4]
        self.ydata_ch5_cont = self.ydata_ch5_cont + [channel5]
        self.ydata_ch6_cont = self.ydata_ch6_cont + [channel6]
        #print(time.time())
        if(self.show_ch1.isChecked()):
            self.plot_refs[0].set_visible(True)
            self.plot_refs[0].set_ydata(self.ydata_ch1)
        else:
            self.plot_refs[0].set_visible(False)

        if(self.show_ch2.isChecked()):
            self.plot_refs[1].set_visible(True)
            self.plot_refs[1].set_ydata(self.ydata_ch2)
        else:
            self.plot_refs[1].set_visible(False)

        if(self.show_ch3.isChecked()):
            self.plot_refs[2].set_visible(True)
            self.plot_refs[2].set_ydata(self.ydata_ch3)
        else:
            self.plot_refs[2].set_visible(False)

        if(self.show_ch4.isChecked()):
            self.plot_refs[3].set_visible(True)
            self.plot_refs[3].set_ydata(self.ydata_ch4)
        else:
            self.plot_refs[3].set_visible(False)
            
        if(self.show_ch5.isChecked()):
            self.plot_refs[4].set_visible(True)
            self.plot_refs[4].set_ydata(self.ydata_ch5)
        else:
            self.plot_refs[4].set_visible(False)
            
        if(self.show_ch6.isChecked()):
            self.plot_refs[5].set_visible(True)
            self.plot_refs[5].set_ydata(self.ydata_ch6)
        else:
            self.plot_refs[5].set_visible(False)
            
        self.fig.canvas.restore_region(self.background)
        self.fig.draw_artist(self.plot_refs[0])
        self.fig.draw_artist(self.plot_refs[1])
        self.fig.draw_artist(self.plot_refs[2])
        self.fig.draw_artist(self.plot_refs[3])
        self.fig.draw_artist(self.plot_refs[4])
        self.fig.draw_artist(self.plot_refs[5])
        self.fig.canvas.update()
        #self.fig.canvas.blit()
        self.fig.canvas.flush_events()
        #print(time.time())
        #print('-------')
        #self.ser.reset_input_buffer()

    def send_data(self):
        if self.ser.isOpen() == False:
            return
        data = bytearray(ctypes.c_uint16(self.slider.value()))
        send_array = bytearray(ctypes.c_uint8(2)) + data + bytearray(ctypes.c_uint8(3))
        cs = ctypes.c_uint8(0)
        for byte in data:
            cs = ctypes.c_uint8(cs.value + byte)
        send_array = send_array + cs
        self.ser.write(send_array)

def main():
    app = QApplication(sys.argv)
    form = AppForm()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
