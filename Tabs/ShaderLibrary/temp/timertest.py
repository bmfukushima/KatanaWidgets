import time
import numpy
import sys
import sched

from PyQt5.QtWidgets import *


class MainWidget(QWidget):
    def __init__(self, parent=None):
        super(MainWidget, self).__init__(parent)
        self.s = sched.scheduler(time.time, time.sleep)
        self._resize_time = []
        self._average_time = 0.05
        # setup layout
        self.layout = QVBoxLayout(self)

        # setup widgets
        self.test_button = QPushButton("start")
        self.test_button.clicked.connect(self.test)
        self.clear_button = QPushButton("clear")
        self.clear_button.clicked.connect(self.clearResizeTime)
        self.mean_button = QPushButton("mean")
        self.mean_button.clicked.connect(self.getMean)

        # add widgets to layout
        self.layout.addWidget(self.test_button)
        self.layout.addWidget(self.clear_button)
        self.layout.addWidget(self.mean_button)

    def startTimer(self, *args, **kwargs):
        print
        return QWidget.startTimer(self, *args, **kwargs)

    def getMean(self):
        avg_times = numpy.array(self._resize_time[1:-1])
        diff = numpy.diff(avg_times)
        print(avg_times)
        print(diff)
        print(numpy.mean(diff))

    def clearResizeTime(self):
        self._resize_time = []

    def resizeTime(self):
        self._resize_time.append(time.perf_counter())

    def resizeEvent(self, *args, **kwargs):
        '''
        if not event:
            schedule event
        
        set event timer to .05s countdown
        '''
        self.resizeTime()
        try:
            if self._resize_time[-1] - self._resize_time[-2] > self._average_time:
                print()
        except:
            pass
        return QWidget.resizeEvent(self, *args, **kwargs)

'''
def main():
    app = QApplication(sys.argv)
    mw = MainWidget()
    mw.show()
    """Print the latest tutorial from Real Python"""
    #tic = time.perf_counter()
    sys.exit(app.exec_())
    #print (tic)

'''

def main():
    import sched, time
    s = sched.scheduler(time.time, time.sleep)
    def print_time(): print("From print_time"), time.time()

    def print_some_times():
        print(time.time())
        b = s.enter(10000, 1, print_time, ())
        print(b.time)
        print(b)
        s.run()
        print(time.time())


    print_some_times()

if __name__ == "__main__":
    main()

