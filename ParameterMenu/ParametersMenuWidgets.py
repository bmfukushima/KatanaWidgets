from PyQt5.QtWidgets import (
    QLabel, QMenu
)

from PyQt5.QtGui import QPixmap

from Utils2.settings import BEBOP_ON_JPG, BEBOP_OFF_JPG

from .NodeShapeAttributesWidget import NodeShapeAttrsTab


class ParametersMenuButton(QLabel):
    """
    Button that will be displayed on all parameter widgets in the top
    for the form widget.  This will open a new drop down menu with
    new options available specifically for this library.

    Attributes:
        menu (ParametersMenu): The menu that will be displayed when the
            user clicks on the button.
        is_pressed (bool): if the button is currently pressed or not
        is_selected (bool): determines if the button is currently selected or not
            This is slightly different than pressed.  As pressed is only when the user
            actually clicks on the button.  Is select can exist on a hover as well.
        node (Node): Current node that this button interacts with

        SIZE (int): size of pixmap
        OFFSET (int): how far to offset in the X coord from the other widgets in the bar
    """
    SIZE = 15
    OFFSET = SIZE * 0.5

    def __init__(self, parent=None, node=None):
        super(ParametersMenuButton, self).__init__(parent)
        # set up attrs
        self.setNode(node)
        self.setIsPressed(False)
        self.__setPixmap(BEBOP_OFF_JPG)
        self.setContentsMargins(
            ParametersMenuButton.OFFSET, 0, ParametersMenuButton.OFFSET, 0)

        # create custom menu
        self.menu = ParametersMenu(self)

        # set style sheet to mimic katana =\
        self.setStyleSheet("""
            QLabel::hover{background-color: rgb(80, 80, 80)};
            QLabel[_is_pressed=true]{background-color: rgb(80, 80, 80)};
        """)

    """ EVENTS """
    def enterEvent(self, event):
        self.setIsSelected(True)
        return QLabel.enterEvent(self, event)

    def leaveEvent(self, event):
        if not self.isPressed():
            self.setIsSelected(False)
        return QLabel.leaveEvent(self, event)

    def __setPixmap(self, pixmap):
        pixmap = QPixmap(pixmap)
        pixmap = pixmap.scaledToHeight(ParametersMenuButton.SIZE)
        self.setPixmap(pixmap)

    def isSelected(self):
        return self._is_selected

    def setIsSelected(self, is_selected):
        # set property
        self._is_selected = is_selected

        # set pixmap
        if is_selected:
            self.__setPixmap(BEBOP_ON_JPG)
        else:
            self.__setPixmap(BEBOP_OFF_JPG)

        # update style sheet
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def isPressed(self):
        return self._is_pressed

    def setIsPressed(self, is_pressed):
        self._is_pressed = is_pressed

    def mousePressEvent(self, event):
        self.setIsPressed(True)
        pos = self.parent().mapToGlobal(self.geometry().bottomLeft())
        self.menu.popup(pos)
        return QLabel.mousePressEvent(self, event)

    """ PROPERTIES """
    def getNode(self):
        return self._node

    def setNode(self, node):
        self._node = node


class ParametersMenu(QMenu):
    """
    Drop down menu that is displayed when the user clicks on the bebop menu
    """
    def __init__(self, parent=None):
        super(ParametersMenu, self).__init__(parent)
        self.addAction('Toggle Node Shape Adjust', self.toggleNodeShapeWidget)

    def toggleNodeShapeWidget(self):
        """
        Toggles between dispalying and hidnig the shape nodes adjustment
        widget.
        """
        form_widget = self.parent().parent()

        # create widget if it doesnt exist
        if not hasattr(form_widget, 'node_shape_attrs_widget'):
            node_shape_attrs_widget = NodeShapeAttrsTab(form_widget, self.parent().getNode())
            form_widget.node_shape_attrs_widget = node_shape_attrs_widget
            form_widget.layout().insertWidget(1, node_shape_attrs_widget)

        # toggle display on node shape attrs widget
        if form_widget.node_shape_attrs_widget.isVisible():
            form_widget.node_shape_attrs_widget.hide()
        else:
            form_widget.node_shape_attrs_widget.show()
            form_widget.node_shape_attrs_widget.update()

    def test(self):
        print (self.parent().getNode())

    def closeEvent(self, event):
        self.parent().setIsPressed(False)
        self.parent().setIsSelected(False)
        return QMenu.closeEvent(self, event)


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QCursor

    app = QApplication(sys.argv)

    mw = ParametersMenuButton()
    mw.setStyleSheet("""
        QLabel::hover{background-color: rgb(128,255,128)};
    """)
    mw.show()
    mw.move(QCursor().pos())
    sys.exit(app.exec_())
