import sys
import os

from Katana import UI4, Callbacks, KatanaResources

from cgwidgets.widgets import ScriptEditorWidget, ScriptEditorPopupEventFilter, installScriptEditorEventFilter
SCRIPTS_VARIABLE = "KATANABEBOPSCRIPTS"


class KatanaScriptEditorEventFilter(ScriptEditorPopupEventFilter):
    def __init__(self, parent=None):
        main_window = UI4.App.MainWindow.GetMainWindow()
        super(KatanaScriptEditorEventFilter, self).__init__(
            parent, main_window=main_window, scripts_variable=SCRIPTS_VARIABLE)


def installPopupHotkeysEventFilter(**kwargs):
    # setup scripts directories
    katana_bebop_scripts_dir = os.environ["KATANABEBOP"] + "/Scripts"
    sandbox_directory = KatanaResources.GetUserKatanaPath() + "/Scripts"
    ScriptEditorWidget.createScriptDirectories(sandbox_directory, display_name="Sandbox")

    try:
        script_directories = os.environ[SCRIPTS_VARIABLE].split(":") + [katana_bebop_scripts_dir, sandbox_directory]
    except KeyError:
        script_directories = [katana_bebop_scripts_dir, sandbox_directory]

    os.environ[SCRIPTS_VARIABLE] = ":".join(script_directories)


    katana_main = UI4.App.MainWindow.GetMainWindow()
    installScriptEditorEventFilter(katana_main, KatanaScriptEditorEventFilter)
    # katana_main.event_filter_widget = KatanaScriptEditorEventFilter(katana_main)
    # katana_main.installEventFilter(katana_main.event_filter_widget)

