from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets


class QLineEditDrop(QtWidgets.QLineEdit):
    def __init__(self):
        super(QLineEditDrop,self).__init__()

    def dropEvent(self,event):
        print '   '*50
        md = event.mimeData()
        for format in md.formats():
            print '%s == %s'%(format,md.data(format))
        print '   '*50

main_widget = QLineEditDrop()
main_widget.show()