import os

from qtpy.QtWidgets import QVBoxLayout, QWidget

from Katana import UI4

from cgwidgets.widgets import ScriptEditorWidget, AbstractPythonEditor


class KatanaPythonIDE(QWidget):
    def __init__(self, parent=None):
        super(KatanaPythonIDE, self).__init__(parent)

        layout = QVBoxLayout(self)
        python_tab = UI4.App.Tabs.CreateTab('Python', None)

        layout.addWidget(python_tab)

        widget = python_tab.getWidget()
        python_widget = widget._pythonWidget
        script_widget = python_widget._FullInteractivePython__scriptWidget
        self._code_widget = script_widget.commandWidget()

    def setScript(self, script):
        self._code_widget.setPlainText(script)


class KatanaPythonEditorWidget(AbstractPythonEditor):
    def __init__(self, parent=None):
        super(KatanaPythonEditorWidget, self).__init__(parent, python_ide=KatanaPythonIDE)



class ScriptEditorTab(UI4.Tabs.BaseTab):
    """Main convenience widget for displaying GSV manipulators to the user."""
    NAME = "Script Editor"
    SCRIPTS_VARIABLE = "KATANABEBOPSCRIPTS"

    def __init__(self, parent=None):
        super(ScriptEditorTab, self).__init__(parent)

        # setup GUI
        QVBoxLayout(self)
        self._script_editor_widget = ScriptEditorWidget(
            self, python_editor=KatanaPythonEditorWidget, scripts_variable=ScriptEditorTab.SCRIPTS_VARIABLE)
        self.layout().addWidget(self._script_editor_widget)