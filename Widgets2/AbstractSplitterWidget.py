from PyQt5.QtWidgets import QSplitter, qApp
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor

from Utils2.colors import(
    GRID_COLOR,
    GRID_HOVER_COLOR
)

from Utils2 import getWidgetAncestor


class AbstractSplitterWidget(QSplitter):
    """
    Splitter widget that has advanced functionality.  This serves as a base
    class for everything that will be used through this library.

    Attributes:
        isSoloView (bool): If this is in full screen mode.  Full screen mode
            allows the user to press a hotkey to make a widget take up the
            entire space of this splitter.  The default hotkey for this is ~ but can be
            set with the setSoloViewHotkey() call.

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
        self._is_solo_view = False
        self._solo_view_hotkey = AbstractSplitterWidget.FULLSCREEN_HOTKEY
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
        if widget.parent():
            if isinstance(widget.parent(), AbstractSplitterWidget):
                return widget.parent().indexOf(widget), widget
            else:
                return AbstractSplitterWidget.getIndexOfWidget(widget.parent())
        else:
            return None, None

    def toggleSoloViewView(self):
        """
        Toggles between the full view of either the parameters
        or the creation portion of this widget.  This is to help
        to try and provide more screen real estate to this widget
        which already does not have enough
        """
        # toggle attrs
        self.setIsSoloView(not self.isSoloView())

    def keyPressEvent(self, event):
        if event.key() == self.soloViewHotkey():
            #self.toggleSoloViewView()
            self.setIsSoloView(True)
            event.ignore()
            return
        elif event.key() == Qt.Key_Escape:
            self.setIsSoloView(False)
        return QSplitter.keyPressEvent(self, event)

    """ PROPERTIES """
    def isSoloView(self):
        return self._is_solo_view

    def setIsSoloView(self, is_solo_view, widget=None):
        """
        Sets the widget that the mouse is currently over to take up
        all of the space inside of the splitter by hiding the rest of the
        widgets.
        """

        # get the current splitter
        if not widget:
            widget = qApp.widgetAt(QCursor.pos())
        current_index, current_widget = self.getIndexOfWidget(widget)
        current_splitter = current_widget.parent()

        # enter full screen
        if is_solo_view is True:
            # adjust parent widget
            if current_splitter.isSoloView() is True:
                current_index1, current_widget1 = self.getIndexOfWidget(current_splitter)
                if current_widget1:
                    parent_splitter = current_widget.parent()
                    parent_splitter.setIsSoloView(True, current_splitter)
                    parent_splitter._is_solo_view = True
            # adjust current widget
            elif current_splitter.isSoloView() is False:
                current_splitter.__displayAllWidgets(False)
                current_widget.show()
                current_splitter._is_solo_view = True
        # exit full screen
        else:
            # adjust current widget
            if current_splitter.isSoloView() is True:
                current_splitter.__displayAllWidgets(True)
                current_splitter._is_solo_view = False
            # adjust parent widget
            elif current_splitter.isSoloView() is False:
                current_index1, current_widget1 = self.getIndexOfWidget(current_splitter)
                if current_widget1:
                    parent_splitter = current_widget.parent()
                    parent_splitter.setIsSoloView(False, current_splitter)
                    parent_splitter._is_solo_view = False

        # set attrs
        current_splitter.setCurrentIndex(current_index)
        current_splitter.setCurrentWidget(current_widget)
        #current_splitter._is_solo_view = is_solo_view

    def soloViewHotkey(self):
        return self._solo_view_hotkey

    def setSoloViewHotkey(self, solo_view_hotkey):
        self._solo_view_hotkey = solo_view_hotkey

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
    main_splitter.setFixedSize(400,400)
    main_splitter.move(QCursor.pos())
    sys.exit(app.exec_())

