
from qtpy.QtWidgets import (QVBoxLayout, QWidget)
from qtpy.QtCore import Qt

from Katana import UI4
from Widgets2 import AbstractSuperToolEditor


class IsolateCELEditor(AbstractSuperToolEditor):
    def __init__(self, parent, node):
        super(IsolateCELEditor, self).__init__(parent, node)

        # setup layout
        QVBoxLayout(self)

        cel_param = self.createValueParam("CEL")
        isolate_from_param = self.createValueParam("isolateFrom")

        self.layout().addWidget(cel_param)
        self.layout().addWidget(isolate_from_param)

        self.layout().setAlignment(Qt.AlignTop)

    def createValueParam(self, name):
        locationPolicy = UI4.FormMaster.CreateParameterPolicy(None, self.node().getParameter(name))
        factory = UI4.FormMaster.KatanaFactory.ParameterWidgetFactory

        w = factory.buildWidget(self, locationPolicy)

        return w
