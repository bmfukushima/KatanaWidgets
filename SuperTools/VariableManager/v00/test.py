#from PyQt5 import QtGui, QtWidgets, QtCore
import sys

from Utils import AbstractUserBooleanWidget

from Settings import CANCEL_GIF, ACCEPT_COLOR_RGBA, ACCEPT_HOVER_COLOR_RGBA, ACCEPT_GIF,\
    CANCEL_COLOR_RGBA, MAYBE_COLOR_RGBA, MAYBE_HOVER_COLOR_RGBA
from PyQt5.QtCore import Qt, QByteArray, QSettings, QTimer, pyqtSlot, QSize
from PyQt5.QtWidgets import (
    QWidget, QApplication, QLabel, QSizePolicy, QVBoxLayout, QAction, QPushButton,
    QHBoxLayout, QTextEdit, QPlainTextEdit, QGroupBox, QTreeWidget, QTreeWidgetItem,
    QAbstractItemView
)

from ItemTypes import PATTERN_ITEM, BLOCK_ITEM
from PyQt5.QtGui import QMovie, QCursor
# test update...

class MainWidget(QTreeWidget):
    def __init__(self, parent=None):
        super(MainWidget, self).__init__(parent)
        for x in range(10):
            #item = QTreeWidgetItem(self)
            item = TempItem(self)
            item.setText(0, str(x))
            item.setFlags(
                item.flags()
                | Qt.ItemIsEditable
            )
            self.addTopLevelItem(item)
        bitem = TempItem(item)
        aitem = TempItem()
        aitem.setText(0, 'aklfjlasfjk')
        item.insertChild(item.childCount(), aitem)
        self.itemChanged.connect(self.test)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)

    def dragEnterEvent(self, event, *args, **kwargs):
        #print('drag enter?')
        return QTreeWidget.dragEnterEvent(self, event, *args, **kwargs)

    def dropEvent(self, event, *args, **kwargs):

        item_dropped_on = self.itemAt(event.pos())
        dropped_item = self.currentItem()

        print(self.dropIndicatorPosition())
        
        return_val = super(MainWidget, self).dropEvent(event, *args, **kwargs)
        item_dropped_on.setExpanded(True)

        return return_val
        #print(item_dropped_on.text(0), dropped_item.text(0))
        
        mimedata = event.mimeData()
        #for format in mimedata.formats():
            #print(format, mimedata.data(format))

        '''
        print(event.source)
        print (event)
        for x in dir(event):
            print (x)
        print ('drop event')
        '''
        return QTreeWidget.dropEvent(self, event, *args, **kwargs)

    def test(self):
        print (self.currentItem().text(0))
        print ('test')


class TempItem(QTreeWidgetItem):
    def __init__(self, parent=None):
        super(TempItem, self).__init__(parent)

    def setExpanded(self, value):
        return QTreeWidgetItem.setExpanded(self, value)

app = QApplication(sys.argv)

w = MainWidget()
w.show()
w.move(QCursor.pos())
sys.exit(app.exec_())