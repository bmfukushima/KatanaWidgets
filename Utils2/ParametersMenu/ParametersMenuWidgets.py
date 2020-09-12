from PyQt5.QtWidgets import (
    QLabel, QMenu, QApplication
)

from PyQt5.QtCore import QPoint

from PyQt5.QtGui import QPixmap

from Utils2.settings import BEBOP_ON_JPG, BEBOP_OFF_JPG


class ParametersMenuButton(QLabel):
    """
    Button that will be displayed on all parameter widgets in the top
    for the form widget.  This will open a new drop down menu with
    new options available specifically for this library.

    Attributes:
        menu (ParametersMenu): The menu that will be displayed when the
            user clicks on the button.
        is_pressed (bool): if the button is currently pressed or not
        node (Node): Current node that this button interacts with
    """
    SIZE = 20

    def __init__(self, parent=None, node=None):
        super(ParametersMenuButton, self).__init__(parent)
        # set up attrs
        self.setNode(node)
        self.setIsPressed(False)
        self.__setPixmap(BEBOP_OFF_JPG)

        # create custom menu
        self.menu = ParametersMenu(self)

    """ EVENTS """
    def enterEvent(self, event):
        self.__setPixmap(BEBOP_ON_JPG)
        return QLabel.enterEvent(self, event)

    def leaveEvent(self, event):
        self.__setPixmap(BEBOP_OFF_JPG)
        return QLabel.leaveEvent(self, event)

    def __setPixmap(self, pixmap):
        pixmap = QPixmap(pixmap)
        pixmap = pixmap.scaledToHeight(ParametersMenuButton.SIZE)
        self.setPixmap(pixmap)

    def isPressed(self):
        return self._is_pressed

    def setIsPressed(self, is_pressed):
        self._is_pressed = is_pressed
        if is_pressed:
            self.__setPixmap(BEBOP_ON_JPG)
        else:
            self.__setPixmap(BEBOP_OFF_JPG)

    def mousePressEvent(self, event):
        self.setIsPressed(True)
        pos = self.parent().mapToGlobal(self.pos())
        pos = QPoint(pos.x(), pos.y() + ParametersMenuButton.SIZE)
        self.menu.popup(pos)
        return QLabel.mousePressEvent(self, event)

    """ PROPERTIES """
    def getNode(self):
        return self._node

    def setNode(self, node):
        self._node = node


class ParametersMenu(QMenu):
    def __init__(self, parent=None):
        super(ParametersMenu, self).__init__(parent)
        self.addAction('test', self.test)
        self.addAction('test', self.test)
        self.addAction('test', self.test)

    def test(self):
        print (self.parent().getNode())

    def closeEvent(self, event):
        self.parent().setIsPressed(False)
        return QMenu.closeEvent(self, event)