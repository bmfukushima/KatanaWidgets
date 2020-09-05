from PyQt5.QtWidgets import (
    QLineEdit, QVBoxLayout
)

from Widgets2 import (
    AbstractSuperToolEditor


class Editor(AbstractSuperToolEditor):
    """
    The top level widget for the editor.  This is here to encapsulate
    the main widget with a stretch box...

    Attributes:
        should_update (bool): determines if this tool should have
            its GUI updated or not during the next event idle process.
    """
    def __init__(self, parent, node):
        super(Editor, self).__init__(parent, node)
        layout = QVBoxLayout(self)
        test = QLineEdit('test')
        layout.addWidget(test)
