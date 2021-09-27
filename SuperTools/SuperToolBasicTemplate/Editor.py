
from qtpy.QtWidgets import (
    QLabel, QVBoxLayout, QWidget
)

from qtpy.QtCore import Qt, QEvent

from cgwidgets.settings import attrs
from cgwidgets.widgets import ShojiModelViewWidget
from cgwidgets.views import AbstractDragDropListView

from Katana import UI4
from Widgets2 import AbstractSuperToolEditor


class SuperToolBasicEditor(AbstractSuperToolEditor):
    def __init__(self, parent, node):
        super(SuperToolBasicEditor, self).__init__(parent, node)

        # setup layout
        QVBoxLayout(self)

        self.createKatanaParam("GroupParam")
        self.createKatanaParam("StringParam")
        self.createKatanaParam("StringParam", self.node().getParameter("GroupParam"))