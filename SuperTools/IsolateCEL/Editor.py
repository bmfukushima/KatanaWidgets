from qtpy.QtWidgets import QVBoxLayout
from qtpy.QtCore import Qt

from Katana import UI4
from Widgets2 import AbstractSuperToolEditor


class IsolateCELEditor(AbstractSuperToolEditor):
    def __init__(self, parent, node):
        super(IsolateCELEditor, self).__init__(parent, node)

        # setup layout
        QVBoxLayout(self)

        cel_param = self.createKatanaParam("CEL")
        isolate_from_param = self.createKatanaParam("isolateFrom")

        self.layout().addWidget(cel_param)
        self.layout().addWidget(isolate_from_param)

        self.layout().setAlignment(Qt.AlignTop)

