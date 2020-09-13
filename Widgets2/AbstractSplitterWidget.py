from PyQt5.QtWidgets import QSplitter, qApp
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor

from Utils2.colors import(
    GRID_COLOR,
    GRID_HOVER_COLOR
)


class AbstractSplitterWidget(QSplitter):
    """
    Splitter widget that has advanced functionality.  This serves as a base
    class for everything that will be used through this library.

    Attributes:
        isFullScreen (bool): If this is in full screen mode.  Full screen mode
            allows the user to press a hotkey to make a widget take up the
            entire space of this splitter.  The default hotkey for this is ~ but can be
            set with the setFullScreenHotkey() call.

        # not used... but I set them up anyways lol
        currentIndex (int): The current index
        currentWidget (widget): The current widget

    Class Attributes:
        HANDLE_WIDTH: Default size of the handle
        FULLSCREEN_HOTKEY: Default hotkey for toggling full screen mode
    """
    HANDLE_WIDTH = 10
    FULLSCREEN_HOTKEY = 96

    def __init__(self, parent=None, orientation=Qt.Vertical):
        super(AbstractSplitterWidget, self).__init__(parent)

        self._current_index = None
        self._current_widget = None
        self._is_fullscreen = False
        self._fullscreen_hotkey = AbstractSplitterWidget.FULLSCREEN_HOTKEY
        self.setOrientation(orientation)

        style_sheet = """
                QSplitter::handle {
                    border: 1px double rgba%s;
                }
                QSplitter::handle:hover {
                    border: 2px double rgba%s;
                }
        """ % (repr(GRID_COLOR), repr(GRID_HOVER_COLOR))

        self.setStyleSheet(style_sheet)
        self.setHandleWidth(AbstractSplitterWidget.HANDLE_WIDTH)

    def __displayAllWidgets(self, value):
        """
        Hides/shows all of the widgets in this splitter.  This is a utility function
        for toggling inbetween full screen modes.

        Args:
            value (bool): If True this will show all the widgets, if False,
                this will hide everythign.
        """
        for index in range(self.count()):
            widget = self.widget(index)
            if value:
                widget.show()
            else:
                widget.hide()

    @staticmethod
    def getIndexOfWidget(widget):
        """
        Recursive function to find the index of this widget's parent widget
        that is a child of the main splitter, and then return that widgets index
        under the main splitter.

        Args:
            widget (QWidget): Widget to set searching from, this is set
                to the current widget under the cursor
        Returns (int, widget):
            if returns None, then bypass everything.
        """
        print(widget)
        if widget.parent():
            if isinstance(widget.parent(), AbstractSplitterWidget):
                return widget.parent().indexOf(widget), widget
            else:
                return AbstractSplitterWidget.getIndexOfWidget(widget.parent())
        else:
            return None, None

    def toggleFullScreenView(self):
        """
        Toggles between the full view of either the parameters
        or the creation portion of this widget.  This is to help
        to try and provide more screen real estate to this widget
        which already does not have enough
        """
        # toggle attrs
        self.setIsFullScreen(not self.isFullScreen())

    def keyPressEvent(self, event):
        if event.key() == self.fullScreenHotkey():
            self.toggleFullScreenView()
            event.ignore()
            return
        elif event.key() == Qt.Key_Escape:
            if self.isFullScreen() is True:
                self.setIsFullScreen(False)
        return QSplitter.keyPressEvent(self, event)

    """ PROPERTIES """
    def isFullScreen(self):
        return self._is_fullscreen

    def setIsFullScreen(self, is_fullscreen):
        """
        Sets the widget that the mouse is currently over to take up
        all of the space inside of the splitter by hiding the rest of the
        widgets.
        """
        print('==================')
        # get attrs
        #pos1 = QCursor.pos()
        widget = qApp.widgetAt(QCursor.pos())
        current_index, current_widget = self.getIndexOfWidget(widget)
        current_splitter = current_widget.parent()
        try:
            print(self.objectName(), widget.text(), current_index, current_widget)
        except:
            pass
        # enter full screen
        if is_fullscreen is True:
            current_splitter.__displayAllWidgets(False)
            current_widget.show()
        # exit full screen
        else:
            current_splitter.__displayAllWidgets(True)

        # set attrs
        self.setCurrentIndex(current_index)
        self.setCurrentWidget(current_widget)
        self._is_fullscreen = is_fullscreen

    def fullScreenHotkey(self):
        return self._fullscreen_hotkey

    def setFullScreenHotkey(self, fullscreen_hotkey):
        self._fullscreen_hotkey = fullscreen_hotkey

    def getCurrentWidget(self):
        return self._current_widget

    def setCurrentWidget(self, widget):
        self._current_widget = widget

    def getCurrentIndex(self):
        return self._current_index

    def setCurrentIndex(self, current_index):
        self._current_index = current_index


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QLabel
    from PyQt5.QtGui import QCursor
    app = QApplication(sys.argv)

    main_splitter = AbstractSplitterWidget()
    main_splitter.setObjectName("main")
    main_splitter.addWidget(QLabel('a'))
    main_splitter.addWidget(QLabel('b'))
    main_splitter.addWidget(QLabel('c'))

    splitter1 = AbstractSplitterWidget(orientation=Qt.Horizontal)
    splitter1.setObjectName("embed")
    for x in range(3):
        l = QLabel(str(x))
        splitter1.addWidget(l)

    main_splitter.addWidget(splitter1)
    main_splitter.show()
    main_splitter.move(QCursor.pos())
    sys.exit(app.exec_())

