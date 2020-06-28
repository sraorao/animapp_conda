import cv2
import sys
import numpy as np
from PyQt5.QtWidgets import  * 
from PyQt5.QtCore import QThread, Qt, pyqtSignal, pyqtSlot, QPoint
from PyQt5.QtGui import QImage, QPixmap, QColor, QFont
import pandas as pd
import animapp.process_csv as pcsv

filenames = list()
stop = False

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

        global filenames, stop

        with open("settings.yaml", 'r') as text_file:
            settings = text_file.readlines()
            settings = dict([(x.strip().split(':')[0], x.strip().split(':')[1].strip()) for x in settings])
            
            leftcorner = tuple(map(int, settings['leftcorner'].strip('()').split(',')))
            rightcorner = tuple(map(int, settings['rightcorner'].strip('()').split(',')))
            angle = float(settings['angle'])
            hue = tuple(map(int, settings['hue'].strip('()').split(',')))
            sat = tuple(map(int, settings['sat'].strip('()').split(',')))
            val = tuple(map(int, settings['val'].strip('()').split(',')))
            ratio = float(settings['ratio'])
            currentframe = int(settings['startframe'])

        for filename in filenames:
            with open(filename + ".csv", "w") as outputfilename: outputfilename.write("") # initialise output file
            previousx, previousy = 0, 0
            count = 0
            if not filename:
                return # exit if no filename is given
            cap = cv2.VideoCapture(filename)
            if filename: cap.set(cv2.CAP_PROP_POS_FRAMES, currentframe) # if reading from file, set current frame to be read, from slider
            ret, firstframe = cap.read()
            try:
                firstframe = cv2.resize(firstframe, (0, 0), fx = ratio, fy = ratio) # resizing affects thresholding of low-res video
            except:
                print("Not a supported video file, perhaps try converting to a different format using e.g. ffmpeg?")
                return
            init_h, init_w, init_ch = firstframe.shape
            if abs(angle) > 0: 
                rotation = cv2.getRotationMatrix2D((init_w/2, init_h/2), angle, 1.0)
                firstframe = cv2.warpAffine(firstframe, rotation, (init_w, init_h))
            firstframe = firstframe[leftcorner[1]:rightcorner[1], leftcorner[0]:rightcorner[0]]
            h, w, ch = firstframe.shape
            bytesPerLine = ch * w
            
            while ret:
                if stop: break
                ret, frame = cap.read()
                if ret:
    
                    frame = cv2.resize(frame, (0, 0), fx = ratio, fy = ratio)
                    if abs(angle) > 0: 
                        rotation = cv2.getRotationMatrix2D((init_w/2, init_h/2), angle, 1.0)
                        frame = cv2.warpAffine(frame, rotation, (init_w, init_h))
                    frame = frame[leftcorner[1]:rightcorner[1], leftcorner[0]:rightcorner[0]]
                    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                    mask = cv2.inRange(hsv, (hue[0], sat[0], val[0]), (hue[1], sat[1], val[1]))
                    mask_rgb = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)
                    convertToQtFormat = QImage(mask_rgb.data, w, h, bytesPerLine, QImage.Format_RGB888)
                    p = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
                    center = None
                    original = np.copy(frame) 
            
                    # only proceed if at least one contour was found
                    if len(cnts) > 0:
                        # find the largest contour in the mask, then use
                        # it to compute the minimum enclosing circle and
                        # centroid
                        c = max(cnts, key=cv2.contourArea)
                        ((x, y), radius) = cv2.minEnclosingCircle(c)
                        M = cv2.moments(c)
                        if M["m00"] != 0:
                            cX = int(M["m10"] / M["m00"])
                            cY = int(M["m01"] / M["m00"])
                        else:
                            cX, cY = 0, 0
                        center = (cX, cY)
                        bounding_box = cv2.minAreaRect(c)
                        # only proceed if the radius meets a minimum size
                        if radius > 2:
                            # draw the circle and centroid on the frame,
                            # then update the list of tracked points
                            cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
                            previousx = cX
                            previousy = cY
                            with open(filename + ".csv", "a") as outputfilename:
                                outputfilename.write(str(cX) + "," + str(cY) + "," + str(count) + "," + str(bounding_box).replace("(", "").replace(")", "") + "\n")
    
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
                    convertToQtFormat = QImage(frame.data, w, h, bytesPerLine, QImage.Format_RGB888)
                    q = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio) 
                    count += 1  
                    self.changePixmap.emit(p)
                    self.originalPixmap.emit(q)
            cap.release()
            print("done")

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


    @pyqtSlot()
    def on_click_process(self):
        """
        Writes processed results (velocity, rolling velocity) to __processed.csv
        and plot of the path to filename.pdf
        """

        global filenames
        for filename in filenames:
            try:
                original_csv = pd.read_csv(filename + ".csv", names = ['x', 'y', 'frame'], usecols = [0, 1, 2])
                try:
                    filled_csv = pcsv.fill_frames(original_csv)
                    pcsv.calculate_velocity(filled_csv)
                    pcsv.calculate_rolling_velocity(filled_csv)
        
                    print("original:\n", original_csv.head())
                    print("processed:\n", filled_csv.head())
        
                    filled_csv.to_csv(filename + "_processed.csv", index = False, header = False)
                    # filtered_csv = pcsv.filter_by_rolling_velocity(filled_csv, 10)
                    # filtered_csv.to_csv(args.file + args.output + "_filtered.csv", index = False, header = False)
                    plot = filled_csv.plot(x = 'x', y = 'y', legend = False, title = filename).get_figure()
                    plot.savefig(filename + '.pdf')  
                except:
                    print(f"Malformed results file: {filename}, try running analysis again with better thresholds")
            except:
                print(f"Could not find the csv file that corresponds to the video: {filename}. You may need to click on 'Run video' first, before processing.")





    @pyqtSlot()
    def on_click_load(self, thread):
        """
        Loads video file(s) selected by file dialog 
        """

        global stop
        self.openFileDialog()
        stop = True

    @pyqtSlot()
    def on_click_run(self, thread):
        """
        Run video file(s) selected by file dialog 
        """

        global stop
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

    def openFileDialog(self):
        global filenames
        options = QFileDialog.Options()
        filenames, _ = QFileDialog.getOpenFileNames(self,"QFileDialog.getOpenFileName()", "","All Files (*);;MP4 Files (*.mp4)", options=options)
        for each in filenames:
            if each:
                print(each)

    def initUI(self):
        th = ThresholdThread(self)
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.resize(700, 500)
        self.setFixedSize(1400, 600)

        self.label = ImageBox(self)
        self.label.move(10, 50)
        self.label.resize(640, 480)

        self.colourimage = ImageBox(self)
        self.colourimage.move(10, 50)
        self.colourimage.resize(640, 480)

        vlayout = QVBoxLayout()
        hlayoutim = QHBoxLayout()
        vlayout.addLayout(hlayoutim)
        hlayoutim.addWidget(self.label)
        hlayoutim.addWidget(self.colourimage)

        hlayoutb = QHBoxLayout()
        vlayout.addLayout(hlayoutb)

        self.buttonload = QPushButton('Load video', self)
        self.buttonload.setToolTip('Load video file(s)')
        self.buttonload.clicked.connect(lambda: self.on_click_load(th))
        hlayoutb.addWidget(self.buttonload)

        self.buttonrun = QPushButton('Run video', self)
        self.buttonrun.setToolTip('Run video file(s)')
        self.buttonrun.clicked.connect(lambda: self.on_click_run(th))
        hlayoutb.addWidget(self.buttonrun)

        self.buttonprocess = QPushButton('Process results', self)
        self.buttonprocess.setToolTip('Process results csv to calculate distance')
        self.buttonprocess.clicked.connect(self.on_click_process)
        hlayoutb.addWidget(self.buttonprocess)

        self.setLayout(vlayout)

        self.show()


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
