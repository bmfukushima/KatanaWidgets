import sys
import os

from PyQt5.QtWidgets import QLineEdit, QFileSystemModel, QApplication, QCompleter

from PyQt5.QtCore import Qt, QEvent, QDir

from PyQt5.QtGui import QCursor

from Widgets2.AbstractSuperToolEditor import iParameter

from Utils2 import getMainWidget

from .Settings import PUBLISH_DIR


class PublishDirWidget(QLineEdit, iParameter):
    def __init__(self, parent=None):
        super(PublishDirWidget, self).__init__(parent=parent)
        self.main_widget = getMainWidget(self)

        # setup model
        self.model = QFileSystemModel()
        filters = self.model.filter()
        self.model.setFilter(filters | QDir.Hidden)

        # setup completer
        self.completer = QCompleter(self.model, self)
        self.setCompleter(self.completer)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)

        self.autoCompleteList = []

        # set default values
        # TODO Set up default publish dir paths
        param = self.main_widget.node.getParameter(self.getLocation())
        publish_dir = PUBLISH_DIR
        if param:
            value = param.getValue(0)
            if  value != '':
                publish_dir = value
        self.setText(publish_dir)

        # setup signals
        self.editingFinished.connect(self.test)

    """ UTILS """
    def test(self):
        print('test')

    def next_completion(self):
        row = self.completer.currentRow()

        # if does not exist reset
        if not self.completer.setCurrentRow(row + 1):
            self.completer.setCurrentRow(0)

        # if initializing
        if self.completer.popup().currentIndex().row() == -1:
            self.completer.setCurrentRow(0)

        index = self.completer.currentIndex()
        self.completer.popup().setCurrentIndex(index)

    def previous_completion(self):
        row = self.completer.currentRow()
        numRows = self.completer.completionCount()

        # if wrapping
        if not self.completer.setCurrentRow(row - 1):
            self.completer.setCurrentRow(numRows - 1)
        # if initializing
        if self.completer.popup().currentIndex().row() == -1:
            self.completer.setCurrentRow(numRows - 1)

        index = self.completer.currentIndex()
        self.completer.popup().setCurrentIndex(index)

    def checkDirectory(self):
        directory = str(self.text())
        if os.path.isdir(directory):
            self.model.setRootPath(str(self.text()))

    def event(self, event, *args, **kwargs):
        if (event.type() == QEvent.KeyPress) and (event.key() == Qt.Key_Return):
            #self.main_widget.populateList()
            return True

        if (event.type() == QEvent.KeyPress) and (event.key() == Qt.Key_Tab):
            self.next_completion()
            return True

        if (event.type() == QEvent.KeyPress) and (event.key() == 16777218):
            self.previous_completion()
            return True

        # I think this is the / key... lol
        if (event.type() == QEvent.KeyRelease) and event.key() == 47:
            self.checkDirectory()
            self.completer.popup().show()

        return QLineEdit.event(self, event, *args, **kwargs)

# app = QApplication(sys.argv)
# w = PublishDirWidget()
# w.show()
# w.move(QCursor.pos())
# sys.exit(app.exec_())
