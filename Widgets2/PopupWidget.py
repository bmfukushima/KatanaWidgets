""" The PopupWidget is displayed over the Main Katana window.  This can popup
any widget type, including tabs.


Hierarchy
PopupWidget --> (QFrame)
    |- QVBoxLayout
        |- _central_widget --> (QWidget)
            |- QVBoxLayout
                |- main_widget (PopupWidget)
"""
from qtpy.QtWidgets import QWidget, QVBoxLayout
from qtpy.QtCore import Qt, QEvent, QPoint, QSize, QTimer
from qtpy.QtGui import QPainter, QColor, QPen, QRegion, QCursor
from Katana import UI4

from cgwidgets.widgets import BooleanInputWidget
from cgwidgets.utils import setAsAlwaysOnTop, setAsTool, isCursorOverWidget, scaleResolution, setAsBorderless
from cgwidgets.settings import iColor, icons

from Utils2 import getFontSize

PIN_SIZE = scaleResolution(25)

class PopupWidget(QWidget):
    """ Creates a popup tab widget that will be displayed over the UI

    Args:
        hide_on_leave (bool): determines if the widget should be hidden on leave
        widget (QWidget): Widget to popup
        size (tuple(float, float)): percent of main window to take
        hide_hotkey (Qt.KEY): special hotkeys for hiding
        hide_modifiers (Qt.MODIFIER): special modifiers for hiding
            multiple modifiers can be provided as:
                (Qt.AltModifier | Qt.ShiftModifier | Qt.ControlModifier)
        mask_size (QSize): Size of the mask
        is_mask_enabled (bool): determines if this should have the mask applied
    """
    def __init__(self, widget, size=QSize(480, 960), is_pinned=False, hide_hotkey=Qt.Key_Escape, hide_modifiers=Qt.NoModifier, parent=None):
        super(PopupWidget, self).__init__(parent)
        self.setObjectName("PopupWidget")
        self._is_pinned = is_pinned
        self._main_widget = widget
        self._hide_hotkey = hide_hotkey
        self._hide_modifiers = hide_modifiers
        self._move_event_active = True
        self._move_event_cursor_pos = QPoint()
        self._move_event_widget_pos = QPoint()
        self.setFixedSize(scaleResolution(size))
        self._mask_size = QSize(
            scaleResolution(self.width()),
            scaleResolution(self.height())
        )

        self._is_mask_enabled = False
        setAsAlwaysOnTop(self)
        setAsBorderless(self, enabled=True)

        # setup layout
        QVBoxLayout(self)
        self._central_widget = QWidget(self)
        self._central_widget.setObjectName("PopupWidget")

        QVBoxLayout(self._central_widget)
        self.layout().addWidget(self._central_widget)
        self._central_widget.layout().addWidget(self._main_widget)

        self.createPinWidget()
        # install events
        self._main_widget.installEventFilter(self)

        # stylesheet
        rgba_border = iColor["rgba_selected"]
        self.setStyleSheet(f"""
            QWidget#PopupWidget{{
                border-top: 1px solid rgba{rgba_border};
                border-bottom: 1px solid rgba{rgba_border};
            }}
        """)

        # setup mask
        self.setIsMaskEnabled(True)
        self.setMaskSize(scaleResolution(QSize(self.width(), self.height()*2)))
        self.setContentsMargins(0, 0, 0, 0)
        self.layout().setContentsMargins(0, 0, 0, 0)
        offset_x = scaleResolution(getFontSize() * 4.5)
        offset_y = scaleResolution(getFontSize() * 2)
        self.centralWidget().setContentsMargins(offset_x, offset_y, offset_x, offset_y)

    def createPinWidget(self):
        def pinPopupWidget(widget, enabled):
            self.setIsPinned(enabled)
            if enabled:
                widget.setImage(icons["pin_enabled"])
            else:
                widget.setImage(icons["pin_disabled"])

        self._pin_button_widget = BooleanInputWidget(
            self, text="", is_selected=False, image=icons["pin_disabled"])
        self._pin_button_widget.setUserFinishedEditingEvent(pinPopupWidget)
        self._pin_button_widget.setFixedSize(PIN_SIZE, PIN_SIZE)

        self._pin_button_widget.show()
        self._pin_button_widget.resizeImage()

    """ MASKING """
    def maskSize(self):
        return QSize(self.width(), self.height()*2)
        #return self._mask_size

    def setMaskSize(self, size):
        self._mask_size = QSize(
            scaleResolution(size.width()),
            scaleResolution(size.height())
        )

    def isMaskEnabled(self):
        return self._is_mask_enabled

    def setIsMaskEnabled(self, enabled):
        self._is_mask_enabled = enabled

    def paintEvent(self, event=None):
        """ Sets the crop window for the widget"""
        if not self.isMaskEnabled(): return

        painter = QPainter(self)
        painter.setOpacity(0.75)
        bg_color = QColor(*iColor["rgba_selected"])
        painter.setPen(QPen(bg_color))

        # ellipse
        """ Draws an ellipse at the coordinates provided, starting at the upper left corner.
        This is offsetting the radius of the ellipse so that it wills up the entire window"""
        painter.drawEllipse(
            QPoint(
                int(self.width()-(self.width()*0.5)) + 1,
                int(self.height()-(self.height()*0.5)) + 1
            ),
            self.maskSize().width() * 0.5 - 2,
            self.maskSize().height() * 0.5 - 2
        )

    def resizeEvent(self, event):
        """ Draws the border around the cropped area"""
        if not self.isMaskEnabled(): return

        width_offset = int((self.maskSize().width() - self.width()) * 0.5)
        height_offset = int((self.maskSize().height() - self.height()) * 0.5)

        region = QRegion(-width_offset, -height_offset, self.maskSize().width(), self.maskSize().height(), QRegion.Ellipse)
        self.clearMask()
        self.setMask(region)

    """ PROPERTIES """
    def isPinned(self):
        return self._is_pinned

    def setIsPinned(self, enabled):
        self._is_pinned = enabled
        self._pin_button_widget.setIsSelected(enabled)
        if enabled:
            self._pin_button_widget.setImage(icons["pin_enabled"])
        else:
            self._pin_button_widget.setImage(icons["pin_disabled"])

    def hideModifiers(self):
        return self._hide_modifiers

    def setHideModifiers(self, hide_modifiers):
        self._hide_modifiers = hide_modifiers

    def hideHotkey(self):
        return self._hide_hotkey

    def setHideHotkey(self, hide_hotkey):
        self._hide_hotkey = hide_hotkey

    """ WIDGETS """
    def centralWidget(self):
        return self._central_widget

    def mainWidget(self):
        return self._main_widget

    """ EVENTS """
    def mousePressEvent(self, event):
        self._move_event_active = True
        self._move_event_cursor_pos = QCursor().pos()
        self._move_event_widget_pos = self.pos()
        return QWidget.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        if self._move_event_active:
            x_offset = self._move_event_cursor_pos.x() - QCursor.pos().x()
            y_offset = self._move_event_cursor_pos.y() - QCursor.pos().y()
            self.move(self._move_event_widget_pos.x() - x_offset, self._move_event_widget_pos.y() - y_offset)
        return QWidget.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        def disableMoveEvent():
            self._move_event_active = False
            delattr(self, "_timer")
        self._timer = QTimer()
        self._timer.start(100)
        self._timer.timeout.connect(disableMoveEvent)
        return QWidget.mouseReleaseEvent(self, event)

    def __hideOnKeyPress(self, event):
        if event.key() == Qt.Key_Escape and not self.isPinned():
            self.hide()

        if event.key() == self.hideHotkey() and event.modifiers() == self.hideModifiers() and not self.isPinned():
            self.hide()

    def keyPressEvent(self, event):
        if event.type() == QEvent.KeyPress:
            self.__hideOnKeyPress(event)

        return QWidget.keyPressEvent(self, event)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            self.__hideOnKeyPress(event)
        if event.type() == QEvent.DragLeave:
            self.__leaveEvent()
        return False

    def __leaveEvent(self):
        # todo fix for non ellipse/masked widgets
        if self.isMaskEnabled():
            if not isCursorOverWidget(self, is_ellipse=True, mask=True):
                if not self.isPinned():
                    self.hide()
        # non masked/ellipse
        else:
            if not isCursorOverWidget(self):
                if not self.isPinned():
                    self.hide()

    def dragLeaveEvent(self, event):
        self.__leaveEvent()
        return QWidget.dragLeaveEvent(self, event)

    def leaveEvent(self, event):
        if not self._move_event_active:
            self.__leaveEvent()
        return QWidget.leaveEvent(self, event)

    def enterEvent(self, event):
        self.activateWindow()
        self.setFocus()
        return QWidget.enterEvent(self, event)

    def hideEvent(self, event):
        # todo when another window is set to always on top, this doesn't work for leave events
        main_window = UI4.App.MainWindow.CurrentMainWindow()
        main_window.activateWindow()

        return QWidget.hideEvent(self, event)

    def showEvent(self, event):
        # todo figure out contents margins
        return_val = super(PopupWidget, self).showEvent(event)
        self._pin_button_widget.move(
            0.5 * (self.width() - self._pin_button_widget.width()),
            0.5 * (self.centralWidget().getContentsMargins()[1] - self._pin_button_widget.height())
        )
        self.activateWindow()
        self.setFocus()
        return return_val

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
            return True
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
        width = size.width()
        height = size.height()
        xpos = int(pos.x() - (width * 0.5))
        ypos = int(pos.y() - (height * 0.5))

        # set geo
        widget.setGeometry(xpos, ypos, width, height)
        widget.show()

    @staticmethod
    def constructPopupWidget(name, widget, size=QSize(480, 960), pos=None, show_on_init=False, hide_hotkey=Qt.Key_Escape, hide_modifiers=Qt.NoModifier):
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
            popup_widget = PopupWidget(
                widget, hide_hotkey=hide_hotkey, hide_modifiers=hide_modifiers, size=size)
            setAsTool(popup_widget)
            setattr(main_window, popup_widget_attr, popup_widget)
            popup_widget.hide()

            # show tab
            if show_on_init:
                PopupWidget.togglePopupWidgetVisibility(name, size=size, pos=pos)

            return popup_widget

    @staticmethod
    def constructPopupTabWidget(tab_type, hide_on_leave=False, size=QSize(480, 960), pos=None, show_on_init=True, hide_hotkey=Qt.Key_Escape, hide_modifiers=Qt.NoModifier):
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
            popup_widget = PopupWidget(
                widget, size=size, hide_on_leave=hide_on_leave, hide_hotkey=hide_hotkey, hide_modifiers=hide_modifiers, parent=main_window)
            setattr(main_window, popup_widget_attr, popup_widget)
            popup_widget.hide()

            # show tab
            if show_on_init:
                PopupWidget.togglePopupWidgetVisibility(tab_type, size=size, pos=pos)

            return popup_widget

    @staticmethod
    def togglePopupWidgetVisibility(name, size=None, pos=None):
        """ Toggles the visibility of the widget

        Args:
            name (str): name of widget to toggle
            size (QSize): Size to set widget to, if none is provided, this will default to the widgets size
            pos = (QPoint): position to show widget at
            """
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
                if not pos:
                    pos = QPoint(
                        QCursor.pos().x(),
                        QCursor.pos().y() + widget.height() * 0.25

                    )

                PopupWidget.showWidget(widget, size=size, pos=pos)
                # widget.update()
