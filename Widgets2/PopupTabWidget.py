from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame
from PyQt5.QtCore import Qt, QEvent

from Katana import UI4

from cgwidgets.utils import setAsAlwaysOnTop, setAsBorderless

class PopupTabWidget(QFrame):
    """ Creates a popup tab widget that will be displayed over the UI

    Args:
        tab_type (str): name of tab type to create
        size (tuple(int,int)): display size
    """
    def __init__(self, tab_type, size=(480, 960), parent=None):
        super(PopupTabWidget, self).__init__(parent)
        self._tab_type = tab_type
        self.setObjectName(tab_type)
        self._size = size
        # create tab
        self._tab_widget = UI4.App.Tabs.CreateTab(tab_type, None)

        # setup layout
        QVBoxLayout(self)
        self._central_widget = QWidget(self)
        self._central_widget.setObjectName(tab_type)
        QVBoxLayout(self._central_widget)
        self.layout().addWidget(self._central_widget)
        self._central_widget.layout().addWidget(self._tab_widget)

        # setup style
        self.setStyleSheet(f"""QWidget#{tab_type}{{border: 1px solid rgba(128,128,255,255)}}""")

        # install events
        self._tab_widget.installEventFilter(self)
        setAsAlwaysOnTop(self)
        #setAsBorderless(self)

    def tabType(self):
        return self._tab_type

    def tabWidget(self):
        return self._tab_widget

    def keyPressEvent(self, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Escape:
                self.close()
        return QFrame.keyPressEvent(self, event)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Escape:
                self.close()
        return False

    def showEvent(self, event):
        QFrame.showEvent(self, event)
        main_window = UI4.App.MainWindow.CurrentMainWindow()

        tab_type = self.tabType()
        tab_attr = f"_popup_{tab_type}"

        if not hasattr(main_window, tab_attr):
            #popup_tab = PopupTabWidget(self.tabType(), parent=main_window)
            setattr(main_window, f"_popup_{tab_type}", self)

            width = main_window.width() * 0.85
            height = main_window.height() * 0.85
            xpos = int((main_window.width() * 0.5) - (width * 0.5))
            ypos = int((main_window.height() * 0.5) - (height * 0.5))
            getattr(main_window, f"_popup_{tab_type}").setGeometry(xpos, ypos, width, height)

        self.setFocus()

    @staticmethod
    def toggleVisibility(tab_type, size=(480, 960)):
        """  Toggles the visibility of the popup widget
        Args:
            tab_type (str): name of tab type to create
            size (tuple(int, int)): size of widget to be displayed

        Returns:

        """

        # get attrs
        main_window = UI4.App.MainWindow.CurrentMainWindow()
        tab_attr = f"_popup_{tab_type}"

        # create widget if it doesn't exist
        if not hasattr(main_window, tab_attr):
            popup_tab_widget = PopupTabWidget(tab_type, size=size, parent=main_window)
            setattr(main_window, f"_popup_{tab_type}", popup_tab_widget)
            getattr(main_window, f"_popup_{tab_type}").hide()

        # show/hide
        if getattr(main_window, f"_popup_{tab_type}").isVisible():
            getattr(main_window, f"_popup_{tab_type}").hide()
        else:
            width = size[0]
            height = size[1]
            xpos = int((main_window.width() * 0.5) - (size[0] * 0.5))
            ypos = int((main_window.height() * 0.5) - (size[1] * 0.5))
            getattr(main_window, f"_popup_{tab_type}").setGeometry(xpos, ypos, width, height)
            getattr(main_window, f"_popup_{tab_type}").show()

