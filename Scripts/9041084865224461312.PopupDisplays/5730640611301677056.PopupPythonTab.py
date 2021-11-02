from qtpy.QtWidgets import QWidget, QVBoxLayout, QFrame, QApplication
from qtpy.QtCore import Qt, QEvent

from Katana import UI4

from cgwidgets.utils import setAsTool


class PythonWidget(QFrame):
    def __init__(self, parent=None):
        super(PythonWidget, self).__init__(parent)
        self.setObjectName("python_widget")

        # create python widget
        python_tab = UI4.App.Tabs.CreateTab('Python', None)

        widget = python_tab.getWidget()
        python_widget = widget._pythonWidget
        #self._script_widget = python_widget._FullInteractivePython__scriptWidget
        self._script_widget = python_widget.scriptWidget()
        self._command_widget = self._script_widget.commandWidget()

        # setup layout
        QVBoxLayout(self)
        self._central_widget = QWidget(self)
        self._central_widget.setObjectName("python_widget")
        QVBoxLayout(self._central_widget)
        self.layout().addWidget(self._central_widget)
        self._central_widget.layout().addWidget(python_tab)

        # setup style
        self.setStyleSheet("""QWidget#python_widget{border: 1px solid rgba(128,128,255,255)}""")
        splitter = self._script_widget.layout().itemAt(0).widget()
        splitter.setSizes([80, 200])

        # install events
        python_tab.installEventFilter(self)
        self._command_widget.installEventFilter(self)

    def eventFilter(self, obj, event):

        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Escape:
                self.hide()
            if event.key() == 96:
                if event.modifiers() == Qt.AltModifier:
                    self.hide()
                    return True

        return False

    def scriptWidget(self):
        return self._script_widget

    def getCommandWidget(self):
        return self._command_widget


# create popup script editor
main_window = UI4.App.MainWindow.CurrentMainWindow()
if not hasattr(main_window, "_popup_python_editor"):
    # create editor
    main_window._popup_python_editor = PythonWidget(main_window)
    setAsTool(main_window._popup_python_editor)

    # position on screen
    """ Creates the window at the center of the screen with a 16/9 aspect ratio """
    ratio = 0.75
    desktop_width = QApplication.desktop().screenGeometry().width()
    desktop_height = QApplication.desktop().screenGeometry().height()
    height = int(desktop_height * ratio)
    width = int(desktop_height * (15/10) * ratio)
    xpos = int((desktop_width * 0.5) - (width * 0.5))
    ypos = int((desktop_height * 0.5) - (height * 0.5))
    main_window._popup_python_editor.setGeometry(xpos, ypos, width, height)

    main_window._popup_python_editor.hide()

# show/hide
if main_window._popup_python_editor.isVisible():
    main_window._popup_python_editor.hide()
else:
    main_window._popup_python_editor.show()
    main_window._popup_python_editor.getCommandWidget().setFocus()



