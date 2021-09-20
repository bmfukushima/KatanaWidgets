from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from cgwidgets.utils import centerWidgetOnCursor, setAsAlwaysOnTop

class QLineEditDrop(QtWidgets.QLineEdit):
    def __init__(self):
        super(QLineEditDrop, self).__init__()
        self.setAcceptDrops(True)

    def dragEnterEvent(self,event):
        event.accept()
        return QtWidgets.QLineEdit.dragEnterEvent(self, event)
        
    def dropEvent(self, event):
        md = event.mimeData()
        for format in md.formats():
            print("{format} == {data}".format(format=format, data=md.data(format)))
        QtWidgets.QLineEdit.dropEvent(self, event)
main_widget = QLineEditDrop()
setAsAlwaysOnTop(main_widget)
main_widget.show()
centerWidgetOnCursor(main_widget)
