""" TODO:
        *   Option to center on tab, vs center on screen, vs mouse position
                - if position provided, use that, if not, use center of main window
        *   How to handle actual resolution vs screen size
                Need to just dynamically scale with screen resolution
"""
from qtpy.QtWidgets import QWidget, QVBoxLayout, QFrame
from qtpy.QtCore import Qt, QEvent, QPoint
from qtpy.QtGui import QKeySequence

from Katana import UI4
from cgwidgets.utils import setAsAlwaysOnTop, setAsTool, isCursorOverWidget

class PopupWidget(QFrame):
    """ Creates a popup tab widget that will be displayed over the UI

    Args:
        hide_on_leave (bool): determines if the widget should be hidden on leave
        widget (QWidget): Widget to popup
        size (tuple(float, float)): percent of main window to take
        hide_hotkey (Qt.KEY): special hotkeys for hiding
        hide_modifiers (Qt.MODIFIER): special modifiers for hiding
            multiple modifiers can be provided as:
                (Qt.AltModifier | Qt.ShiftModifier | Qt.ControlModifier)
    """
    def __init__(self, widget, size=(480, 960), hide_on_leave=False, hide_hotkey=Qt.Key_Escape, hide_modifiers=Qt.NoModifier, parent=None):
        super(PopupWidget, self).__init__(parent)
        self.setObjectName("PopupWidget")
        self._main_widget = widget
        self._hide_hotkey = hide_hotkey
        self._hide_modifiers = hide_modifiers
        self._hide_on_leave = hide_on_leave
        self._size = size

        # setup layout
        QVBoxLayout(self)
        self._central_widget = QWidget(self)
        self._central_widget.setObjectName("PopupWidget")

        QVBoxLayout(self._central_widget)
        self.layout().addWidget(self._central_widget)
        self._central_widget.layout().addWidget(self._main_widget)

        # setup style
        self.setStyleSheet("""QWidget#PopupWidget{border: 1px solid rgba(128,128,255,255)}""")

        # install events
        self._main_widget.installEventFilter(self)
        setAsAlwaysOnTop(self)

    """ PROPERTIES """
    def hideModifiers(self):
        return self._hide_modifiers

    def setHideModifiers(self, hide_modifiers):
        self._hide_modifiers = hide_modifiers

    def hideHotkey(self):
        return self._hide_hotkey

    def setHideHotkey(self, hide_hotkey):
        self._hide_hotkey = hide_hotkey

    def hideOnLeave(self):
        return self._hide_on_leave

    def setHideOnLeave(self, hide_on_leave):
        self._hide_on_leave = hide_on_leave

    def mainWidget(self):
        return self._main_widget

    """ EVENTS """
    def __hideOnKeyPress(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()

        if event.key() == self.hideHotkey() and event.modifiers() == self.hideModifiers():
            self.hide()

    def keyPressEvent(self, event):
        if event.type() == QEvent.KeyPress:
            self.__hideOnKeyPress(event)

        return QFrame.keyPressEvent(self, event)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            self.__hideOnKeyPress(event)
        return False

    def leaveEvent(self, event):
        if self.hideOnLeave():
            if not isCursorOverWidget(self):
                self.hide()
        return QFrame.enterEvent(self, event)

    def enterEvent(self, event):
        self.activateWindow()
        self.setFocus()
        return QFrame.enterEvent(self, event)

    """ UTILS """
    @staticmethod
    def getPopupWidget(name):
        """ Returns the popup widget of the given name

        Args:
            name (str): name of popup widget to retrieve
            """
        main_window = UI4.App.MainWindow.CurrentMainWindow()
        popup_widget_attr = f"_popup_{name}"
        if hasattr(main_window, popup_widget_attr):
            return getattr(main_window, popup_widget_attr)
        return None

    @staticmethod
    def doesPopupWidgetExist(name):
        main_window = UI4.App.MainWindow.CurrentMainWindow()
        popup_widget_attr = f"_popup_{name}"
        if hasattr(main_window, popup_widget_attr):
            True
        return False

    @staticmethod
    def showWidget(widget, size=None, pos=None):
        """ Shows the widget

        Args:
            size (tuple(float, float)): percentage of screen to take
            """
        # get attrs
        main_window = UI4.App.MainWindow.CurrentMainWindow()
        if not size:
            size = widget.size()
        if not pos:
            pos = QPoint(main_window.width() * 0.5, main_window.height * 0.5)
        # find geometry bounds
        width = size[0]
        height = size[1]
        xpos = int(pos.x() - (width * 0.5))
        ypos = int(pos.y() - (height * 0.5))

        # set geo
        widget.setGeometry(xpos, ypos, width, height)
        widget.show()

    @staticmethod
    def constructPopupWidget(name, widget, hide_on_leave=False, size=(480, 960), pos=None, show_on_init=False, hide_hotkey=Qt.Key_Escape, hide_modifiers=Qt.NoModifier):
        """ Constructs a new popup widget

        Args:
            name (str): name to be called with
            widget (QWidget): Widget to popup
            size (tuple(float,float)): percent of main window to take
            show_on_init (bool): determines if this widget should be shown on first key press
            hide_hotkey (Qt.KEY): special hotkeys for hiding
            hide_modifiers (Qt.MODIFIER): special modifiers for hiding
                multiple modifiers can be provided as:
                    (Qt.AltModifier | Qt.ShiftModifier | Qt.ControlModifier)
        """
        main_window = UI4.App.MainWindow.CurrentMainWindow()
        popup_widget_attr = f"_popup_{name}"

        # create widget if it doesn't exist
        if not hasattr(main_window, popup_widget_attr):
            popup_tab_widget = PopupWidget(
                widget, hide_on_leave=hide_on_leave, hide_hotkey=hide_hotkey, hide_modifiers=hide_modifiers, size=size)
            setAsTool(popup_tab_widget)
            setattr(main_window, popup_widget_attr, popup_tab_widget)
            popup_tab_widget.hide()

        # show tab
        if show_on_init:
            PopupWidget.togglePopupWidgetVisibility(name, size=size, pos=pos)

    @staticmethod
    def constructPopupTabWidget(tab_type, hide_on_leave=False, size=(480, 960), pos=None, show_on_init=True, hide_hotkey=Qt.Key_Escape, hide_modifiers=Qt.NoModifier):
        """ Constructs a new popup from the tab type provided

        Args:
            name (str): name to be called with
            widget (QWidget): Widget to popup
            size (tuple(float,float)): percent of main window to take
            show_on_init (bool): determines if this widget should be shown on first key press
            hide_hotkey (Qt.KEY): special hotkeys for hiding
            hide_modifiers (Qt.MODIFIER): special modifiers for hiding
                multiple modifiers can be provided as:
                    (Qt.AltModifier | Qt.ShiftModifier | Qt.ControlModifier)
        """
        # get attrs
        main_window = UI4.App.MainWindow.CurrentMainWindow()
        popup_widget_attr = f"_popup_{tab_type}"

        # create widget if it doesn't exist
        if not hasattr(main_window, popup_widget_attr):
            widget = UI4.App.Tabs.CreateTab(tab_type, None)
            popup_tab_widget = PopupWidget(
                widget, size=size, hide_on_leave=hide_on_leave, hide_hotkey=hide_hotkey, hide_modifiers=hide_modifiers, parent=main_window)
            setattr(main_window, popup_widget_attr, popup_tab_widget)
            popup_tab_widget.hide()

        # show tab
        if show_on_init:
            PopupWidget.togglePopupWidgetVisibility(tab_type, size=size, pos=pos)

    @staticmethod
    def togglePopupWidgetVisibility(name, size=(480, 960), pos=None):

        # get attrs
        main_window = UI4.App.MainWindow.CurrentMainWindow()
        popup_name = f"_popup_{name}"
        # create widget if it doesn't exist
        if hasattr(main_window, popup_name):
            widget = getattr(main_window, f"_popup_{name}")
            # show/hide
            if widget.isVisible():
                widget.hide()
            else:
                PopupWidget.showWidget(widget, size, pos)
