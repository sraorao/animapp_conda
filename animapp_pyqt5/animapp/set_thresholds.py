import cv2
import sys
import numpy as np
from PyQt5.QtWidgets import  * 
from PyQt5.QtCore import QThread, Qt, pyqtSignal, pyqtSlot, QPoint
from PyQt5.QtGui import QImage, QPixmap, QColor, QFont
# from qrangeslider import QRangeSlider
from animapp.qrangeslider import QRangeSlider


leftcorner = (0, 0)
rightcorner = (640, 480)
drawing = False
angle = 0
filename = ""
ratio = 1
stop = False
nframes = 10
currentframe = 0
hue = (0, 35)
sat = (0, 35)
val = (0, 35)

class ThresholdThread(QThread):
    """
    Thread that runs the file selected in the file dialog box. 
    This needs to be updated to make it an event loop at some point.
    """
    changePixmap = pyqtSignal(QImage)
    originalPixmap = pyqtSignal(QImage)

    def run(self):
        """
        This function sends images as signals to the ImageBox
        """
        global leftcorner, rightcorner, drawing, angle, filename, ratio, stop, currentframe, hue, sat, val
        ret = False
        while True:
            if stop: break
            if not filename:
                return # do nothing if no file is selected
            cap = cv2.VideoCapture(filename)
            if filename: cap.set(cv2.CAP_PROP_POS_FRAMES, currentframe) # if reading from file, set current frame to be read, from slider
            ret, firstframe = cap.read()
            h, w, ch = firstframe.shape
            ratio = 640/float(w)
            new_height = int(h * ratio)
            firstframe = cv2.resize(firstframe, (0, 0), fx = ratio, fy = ratio) # resizing affects thresholding of low-res videos
            h, w, ch = firstframe.shape
            bytesPerLine = ch * w
            hsv = cv2.cvtColor(firstframe, cv2.COLOR_BGR2HSV)
            if ret:
                frame = firstframe
                mask = cv2.inRange(hsv, np.array([hue[0], sat[0], val[0]]), np.array([hue[1], sat[1], val[1]]))
                mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)
    
                convertToQtFormat = QImage(mask.data, w, h, bytesPerLine, QImage.Format_RGB888)
                p = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                if abs(angle) > 0: 
                    rotation = cv2.getRotationMatrix2D((w/2, h/2), angle, 1.0)
                    frame = cv2.warpAffine(frame, rotation, (w, h))
                if drawing:
                    cv2.rectangle(frame,leftcorner,rightcorner,(0,255,0), 1)
                convertToQtFormat = QImage(frame.data, w, h, bytesPerLine, QImage.Format_RGB888)
                q = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)   
                self.changePixmap.emit(p)
                self.originalPixmap.emit(q)
                cap.release()

class ImageBox(QLabel):
    """
    Subclassed from QLabel, to handle mouse events. 
    This needs to be updated to make it an event loop at some point.
    """
    mouseposition = pyqtSignal(str)

    def __init__(self, parent=None):
        super(ImageBox, self).__init__(parent)
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor(223, 230, 248))
        self.setPalette(p)
        self.setMouseTracking(True)
        self.lastPoint = QPoint()

    def mousePressEvent(self, event):
        """
        When the left mouse button is pressed, get the corners to draw cropping rectangle
        """
        global drawing, leftcorner, rightcorner
        keepDrawing = False
        if event.button() == Qt.LeftButton:
            leftcorner = (event.x(), event.y())
            rightcorner = leftcorner
            drawing = True

    def mouseMoveEvent(self, event):
        """
        This function sends images as signals to the ImageBox
        """
        global rightcorner, leftcorner
        if event.buttons() == Qt.NoButton:
            drawing = False
        if event.buttons() == Qt.LeftButton:
            rightcorner = (event.x(), event.y())
        updatetext = "Mouse coords: " + str(event.x()) + ":" + str(event.y())
        self.mouseposition.emit(updatetext)

    def mouseReleaseEvent(self, event):
        global rightcorner, drawing
        rightcorner = (event.x(), event.y())

class App(QWidget):
    """
    GUI thread runs here.
    """
    def __init__(self):
        super().__init__()
        self.title = 'PyQt5 Video'
        self.left = 0
        self.top = 0
        self.width = 640
        self.height = 480
        self.initUI()
        self.setMouseTracking(True)

    @pyqtSlot(QImage)
    def setImage(self, image):
        self.label.setPixmap(QPixmap.fromImage(image))

    @pyqtSlot(QImage)
    def setImageOrig(self, image):
        self.colourimage.setPixmap(QPixmap.fromImage(image))

    @pyqtSlot(str)
    def setUpdateLabel(self, string):
        self.label2.setText(string)

    @pyqtSlot()
    def on_click_write(self):
        """
        Writes settings to file settings.yaml
        Just a plain text file for now as does not warrant loading yaml module
        """
        global leftcorner, rightcorner, angle, ratio, currentframe, hue, sat, val
        with open("settings.yaml", "w") as text_file:
            text_file.write(f"leftcorner: {leftcorner}\n")
            text_file.write(f"rightcorner: {rightcorner}\n")
            text_file.write(f"angle: {angle}\n")
            text_file.write(f"hue: {hue}\n")
            text_file.write(f"sat: {sat}\n")
            text_file.write(f"val: {val}\n")
            text_file.write(f"ratio: {ratio}\n")
            text_file.write(f"startframe: {currentframe}\n")

    @pyqtSlot()
    def on_click_load(self, thread):
        """
        Loads video file selected by file dialog 
        """
        global leftcorner, rightcorner, filename, stop
        leftcorner = (0, 0)
        rightcorner = (640, 480)
        self.openFileDialog()
        self.getNFrames()
        self.slidertrack.setMaximum(nframes)
        self.slidertrack.setValue(0)
        stop = True
        try:
            thread.quit()
            thread.wait()
        except:
        	pass
        thread.changePixmap.connect(self.setImage)
        thread.finished.connect(self.on_finished)
        thread.originalPixmap.connect(self.setImageOrig)
        thread.start()
        stop = False

    @pyqtSlot()
    def on_finished(self):
        pass

    @pyqtSlot()
    def on_valuechange_rotate(self):
        global angle
        angle = self.sprotate.value()
        if self.chkclockwise.isChecked():
        	angle = -angle  

    def on_statechange_clockwise(self):
        global angle
        if self.chkclockwise.isChecked():
        	angle = -angle        

    def openFileDialog(self):
        global filename
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);;MP4 Files (*.mp4)", options=options)
        if filename:
            print(filename)

    def getNFrames(self):
        """
        Get total number of frames from the loaded video file
        """
        global nframes
        if filename != "":
            cap = cv2.VideoCapture(filename)
            nframes = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) - 1)

    @pyqtSlot()
    def on_valuechange_rangeslider(self):
        global hue, sat, val
        hue = self.rsh.getRange()
        sat = self.rss.getRange()
        val = self.rsv.getRange()

    def initUI(self):
        global nframes
        th = ThresholdThread(self)
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.resize(700, 500)
        self.setFixedSize(1400, 600)
        # create a label
        self.label2 = QLabel(self)
        self.label2.move(0, 0)
        self.label2.resize(700, 10)

        self.label = ImageBox(self)
        self.label.move(10, 50)
        self.label.resize(640, 480)

        self.colourimage = ImageBox(self)
        self.colourimage.move(10, 50)
        self.colourimage.resize(640, 480)
        self.colourimage.mouseposition.connect(self.setUpdateLabel)
        # hue
        self.rsh = QRangeSlider()
        self.rsh.setMax(180)
        self.rsh.show()
        self.rsh.setRange(0, 35)
        self.rsh.startValueChanged.connect(self.on_valuechange_rangeslider)
        self.rsh.endValueChanged.connect(self.on_valuechange_rangeslider)
        self.rsh.setBackgroundStyle('background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #222, stop:1 #333);')
        self.rsh.setSpanStyle('background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #282, stop:1 #393);')
        # saturation
        self.rss = QRangeSlider()
        self.rss.setMax(255)
        self.rss.show()
        self.rss.setRange(0, 35)
        self.rss.startValueChanged.connect(self.on_valuechange_rangeslider)
        self.rss.endValueChanged.connect(self.on_valuechange_rangeslider)
        self.rss.setBackgroundStyle('background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #222, stop:1 #333);')
        self.rss.setSpanStyle('background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #282, stop:1 #393);')
        # value
        self.rsv = QRangeSlider()
        self.rsv.setMax(255)
        self.rsv.show()
        self.rsv.setRange(0, 35)
        self.rsv.startValueChanged.connect(self.on_valuechange_rangeslider)
        self.rsv.endValueChanged.connect(self.on_valuechange_rangeslider)
        self.rsv.setBackgroundStyle('background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #222, stop:1 #333);')
        self.rsv.setSpanStyle('background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #282, stop:1 #393);')

        self.slidertrack = QSlider(Qt.Horizontal)
        self.slidertrack.setMinimum(0)
        self.slidertrack.setMaximum(nframes)
        self.slidertrack.setValue(0)
        self.slidertrack.setTickPosition(QSlider.TicksBelow)
        self.slidertrack.setTickInterval(5)
        self.slidertrack.valueChanged.connect(self.on_slidertrack_valuechange)
        self.labelh = QLabel(self)
        self.labelh.setText("HUE")
        self.labels = QLabel(self)
        self.labels.setText("SAT")
        self.labelv = QLabel(self)
        self.labelv.setText("VAL")
        vlayout = QVBoxLayout()
        hlayouth = QHBoxLayout()
        vlayout.addLayout(hlayouth)
        hlayouts = QHBoxLayout()
        vlayout.addLayout(hlayouts)
        hlayoutv = QHBoxLayout()
        vlayout.addLayout(hlayoutv)
        hlayouth.addWidget(self.labelh)
        hlayouth.addWidget(self.rsh, stretch=1)
        hlayouts.addWidget(self.labels)
        hlayouts.addWidget(self.rss, stretch=1)
        hlayoutv.addWidget(self.labelv)
        hlayoutv.addWidget(self.rsv, stretch=1)
        vlayout.addWidget(self.slidertrack, stretch=1)
        vlayout.addWidget(self.label2, stretch=1)

        hlayoutim = QHBoxLayout()
        vlayout.addLayout(hlayoutim)
        hlayoutim.addWidget(self.label)
        hlayoutim.addWidget(self.colourimage)

        hlayoutb = QHBoxLayout()
        vlayout.addLayout(hlayoutb)
        self.buttonwrite = QPushButton('Write settings', self)
        self.buttonwrite.setToolTip('Write settings to a file, which will be used by analysis program)')
        hlayoutb.addWidget(self.buttonwrite)
        self.buttonwrite.clicked.connect(self.on_click_write)
        self.labelrotate = QLabel(self)
        self.labelrotate.setText('Rotate image')
        hlayoutb.addWidget(self.labelrotate)
        self.chkclockwise = QCheckBox("Clockwise")
        self.chkclockwise.setCheckState(True)
        self.chkclockwise.setTristate(False)
        hlayoutb.addWidget(self.chkclockwise)
        self.chkclockwise.stateChanged.connect(self.on_statechange_clockwise)
        self.sprotate = QDoubleSpinBox()
        self.sprotate.setRange(0.00, 10.00)
        self.sprotate.setSingleStep(0.10)
        hlayoutb.addWidget(self.sprotate)
        self.sprotate.valueChanged.connect(self.on_valuechange_rotate)
        self.buttonload = QPushButton('Load video', self)
        self.buttonload.setToolTip('Load video file')
        self.buttonload.clicked.connect(lambda: self.on_click_load(th))
        hlayoutb.addWidget(self.buttonload)
        self.setLayout(vlayout)

        self.show()


    def on_slidertrack_valuechange(self):
        global currentframe
        currentframe = self.slidertrack.value()

    def closeEvent(self, event):
    	pass

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == '-h' or sys.argv[1] == '--help':
            print("Animapp - Please run 'threshold' on an exemplar video, and then run 'animapp' on the video(s) of interest")
    else:
        app = QApplication(sys.argv)
        ex = App()
        sys.exit(app.exec_())

if __name__ == '__main__':
    main()
