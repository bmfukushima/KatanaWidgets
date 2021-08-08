

# Change tab full screen hotkey
""" """

def changeFullscreenHotkey(hotkey):
    """
    changes the full screen hotkey to the one provided
    Args:
        hotkey (Qt.KEY):
    """
    from Katana import QT4Panels

    def panelFrameKeyPressEvent(self, event):
        from qtpy.QtCore import Qt
        from qtpy.QtWidgets import QTabWidget

        if event.key() == hotkey:
            # isNoModifierPressed = event.modifiers() == Qt.NoModifier
            # isCtrlOnlyModifier = event.modifiers() == Qt.ControlModifier
            # if isNoModifierPressed or isCtrlOnlyModifier:
            if event.modifiers() == Qt.ControlModifier:
                self.setFrameMaximized(not self.getFrameMaximized())
                event.accept()
                return
        QTabWidget.keyPressEvent(self, event)

    # override key press on parent widget
    QT4Panels.PanelFrame.keyPressEvent = panelFrameKeyPressEvent