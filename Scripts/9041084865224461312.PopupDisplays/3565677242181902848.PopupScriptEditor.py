from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame
from PyQt5.QtCore import Qt, QEvent

from Katana import UI4

class ScriptEditorWidget(QFrame):
    def __init__(self, parent=None):
        super(ScriptEditorWidget, self).__init__(parent)
        self.setObjectName("python_widget")

        # create python widget
        script_editor = UI4.App.Tabs.CreateTab('Script Manager', None)
        self._command_widget = script_editor.getWidget().scriptEditorWidget().pythonWidget().codeWidget()

        # setup layout
        QVBoxLayout(self)
        self._central_widget = QWidget(self)
        self._central_widget.setObjectName("python_widget")
        QVBoxLayout(self._central_widget)
        self.layout().addWidget(self._central_widget)
        self._central_widget.layout().addWidget(script_editor)

        # setup style
        self.setStyleSheet("""QWidget#python_widget{border: 1px solid rgba(128,128,255,255)}""")

        # install events
        script_editor.installEventFilter(self)
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

    def getCommandWidget(self):
        return self._command_widget

# create popup script editor
main_window = UI4.App.MainWindow.CurrentMainWindow()
if not hasattr(main_window, "_popup_script_editor"):
    main_window._popup_script_editor = ScriptEditorWidget(main_window)

    # position on screen
    width = main_window.width() * 0.85
    height = main_window.height() * 0.85
    xpos = int((main_window.width() * 0.5) - (width * 0.5))
    ypos = int((main_window.height() * 0.5) - (height * 0.5))
    main_window._popup_script_editor.setGeometry(xpos, ypos, width, height)
    main_window._popup_script_editor.hide()

# show/hide
if main_window._popup_script_editor.isVisible():
    main_window._popup_script_editor.hide()
else:
    main_window._popup_script_editor.show()
    main_window._popup_script_editor.getCommandWidget().setFocus()



