import sys
import os

#from PyQt5 import QtGui, QtCore, QtWidgets
from qtpy.QtWidgets import QWidget
from qtpy.QtCore import QEvent
from qtpy.QtGui import QKeySequence

from Katana import UI4, Callbacks

from cgwidgets.widgets.AbstractWidgets.AbstractScriptEditor.AbstractScriptEditorWidgets import PopupHotkeyMenu, PopupGestureMenu
from cgwidgets.widgets.AbstractWidgets.AbstractScriptEditor.AbstractScriptEditorUtils import Utils as Locals
from cgwidgets.widgets.AbstractWidgets.AbstractScriptEditor.AbstractScriptEditorEventFilter import AbstractEventFilter

SCRIPTS_VARIABLE = "KATANABEBOPSCRIPTS"

class scriptEditorEventFilter(AbstractEventFilter):
    def __init__(self, parent=None):
        main_window = UI4.App.MainWindow.GetMainWindow()
        super(scriptEditorEventFilter, self).__init__(
            parent, main_window=main_window, scripts_variable=SCRIPTS_VARIABLE)


def installPopupHotkeysEventFilter(**kwargs):
    from Katana import UI4
    import sys
    # setup scripts directories
    katana_bebop_scripts_dir = os.environ["KATANABEBOP"] + "/Scripts"
    old_scripts_dir = "/media/ssd01/dev/katana/KatanaResources_old/ScriptsTest"

    try:
        script_directories = os.environ[SCRIPTS_VARIABLE].split(":") + [katana_bebop_scripts_dir, old_scripts_dir]
    except KeyError:
        script_directories = [katana_bebop_scripts_dir, old_scripts_dir]

    os.environ[SCRIPTS_VARIABLE] = ":".join(script_directories)

    katana_main = UI4.App.MainWindow.GetMainWindow()
    katana_main.event_filter_widget = scriptEditorEventFilter(katana_main)
    katana_main.installEventFilter(katana_main.event_filter_widget)

