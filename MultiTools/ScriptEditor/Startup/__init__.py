import sys
import os

#from PyQt5 import QtGui, QtCore, QtWidgets
from qtpy.QtWidgets import QWidget
from qtpy.QtCore import QEvent
from qtpy.QtGui import QKeySequence

from Katana import UI4, Callbacks

from cgwidgets.widgets.AbstractWidgets.AbstractScriptEditor.AbstractScriptEditorWidgets import PopupHotkeyMenu, PopupGestureMenu
from cgwidgets.widgets.AbstractWidgets.AbstractScriptEditor.AbstractScriptEditorUtils import Utils as Locals


class eventFilter(QWidget):
    def __init__(self, parent=None):
        super(eventFilter, self).__init__(parent)
        self.widget = UI4.App.MainWindow.GetMainWindow()
        #self.widget.installEventFilter(self)

    def closeEvent(self, *args, **kwargs):
        self.widget.removeEventFilter(self)
        return QWidget.closeEvent(self, *args, **kwargs)

    def eventFilter(self, obj, event, *args, **kwargs):
        if event.type() == QEvent.KeyPress:
            # get user hotkeys
            # needs to repopulate this every time to check...
            # todo hardcode
            hotkeys_file_path = '/media/ssd01/dev/katana/KatanaResources_old/ScriptsTest/hotkeys.json'
            self.hotkey_dict = Locals().getFileDict(hotkeys_file_path)

            # get key input
            user_input = QKeySequence(
                int(event.modifiers()) + event.key()
            ).toString()
            for file_path in list(self.hotkey_dict.keys()):
                hotkey = self.hotkey_dict[file_path]
                if hotkey == user_input:
                    file_type = Locals().checkFileType(file_path)
                    if file_type == 'hotkey':
                        main_widget = PopupHotkeyMenu(self.widget, file_path=file_path)
                        main_widget.show()
                    elif file_type == 'gesture':
                        main_widget = PopupGestureMenu(self.widget, file_path=file_path)
                        main_widget.show()
                    elif file_type == 'script':
                        if os.path.exists(file_path):
                            with open(file_path) as script_descriptor:
                                exec(script_descriptor.read())
                    return QWidget.eventFilter(self, obj, event, *args, **kwargs)

        return QWidget.eventFilter(self, obj, event, *args, **kwargs)


def installPopupHotkeysEventFilter(**kwargs):
    from Katana import UI4
    import sys

    katana_main = UI4.App.MainWindow.GetMainWindow()
    katana_main.event_filter_widget = eventFilter(katana_main)
    katana_main.installEventFilter(katana_main.event_filter_widget)

