from qtpy.QtWidgets import QVBoxLayout

from Widgets2 import AbstractSuperToolEditor


class SuperToolBasicEditor(AbstractSuperToolEditor):
    def __init__(self, parent, node):
        super(SuperToolBasicEditor, self).__init__(parent, node)

        # setup layout
        QVBoxLayout(self)

        self.layout().addWidget(self.createKatanaParam("GroupParam"))
        self.layout().addWidget(self.createKatanaParam("StringParam"))
        self.layout().addWidget(self.createKatanaParam("StringParam", self.node().getParameter("GroupParam")))