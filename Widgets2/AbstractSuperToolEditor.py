from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QEvent


class AbstractSuperToolEditor(QWidget):
    """
    Custom Super Tool widget that will hold all of the base functionality
    for the rest of the supertools to inherit from.  This includes the
    * Auto Resizing
        Forces all widgets to automatically constrain to the correct dimensions
        inside of the parameters pane.

    """
    def __init__(self, parent, node):
        super(AbstractSuperToolEditor, self).__init__(parent)
        self._is_frozen = False
        self.node = node

        self.__resizeEventFilter = ResizeFilter(self)
        self.getKatanaParamsScrollAreaWidget().parent().parent().installEventFilter(self.__resizeEventFilter)
        self.setFixedHeight(self.getKatanaParamsScrollAreaWidget().height())

    def getKatanaParamsScrollAreaWidget(self):
        """
        Returns the params widget that is central widget of the scroll area
        so that we can properly set width/height.
        """
        return self.parent().parent().parent().parent()

    def __setupEventHandlers(self, bool):
        """
        Interface to determine where the event handlers will
        be setup.
        """
        pass

    def hideEvent(self, event):
        self.__setupEventHandlers(False)
        self.is_frozen = True
        return QWidget.hideEvent(self, event)

    def showEvent(self, event):
        self.__setupEventHandlers(True)
        self.is_frozen = False
        if self.height() < self.getKatanaParamsScrollAreaWidget().height():
            self.setFixedHeight(self.getKatanaParamsScrollAreaWidget().height())
        return QWidget.showEvent(self, event)

    """ PROPERTIES """
    @property
    def is_frozen(self):
        return self._is_frozen

    @is_frozen.setter
    def is_frozen(self, is_frozen):
        self._is_frozen = is_frozen


class ResizeFilter(QWidget):
    """
    Event filter for auto resizing the GUI
    """
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Resize:
            # resize to fill here...
            """
            This is a horrible function that is going to implode later...
            but removes the horrid fixed size of the params pane which
            drives me borderline insane.
            """
            # widget below the scroll area...
            width = self.parent().getKatanaParamsScrollAreaWidget().width()
            width -= 25
            # remove scroll bar
            # panel_scroll_area = self.parent().getKatanaParamsScrollAreaWidget()
            # vscroll_bar = panel_scroll_area.verticalScrollBar()
            # vscroll_bar_width = vscroll_bar.width()
            # width -= vscroll_bar_width

            self.parent().setFixedWidth(width)
            return True
        return super(ResizeFilter, self).eventFilter(obj, event)
            # needs to include the scroll bar...