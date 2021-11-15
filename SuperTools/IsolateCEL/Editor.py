
from qtpy.QtWidgets import QVBoxLayout
from qtpy.QtCore import Qt

from Katana import UI4, Utils

from Widgets2 import AbstractSuperToolEditor


class IsolateCELEditor(AbstractSuperToolEditor):
    def __init__(self, parent, node):
        super(IsolateCELEditor, self).__init__(parent, node)

        self._node = node

        # setup layout
        QVBoxLayout(self)

        cel_param = self.createKatanaParam("CEL")
        isolate_from_param = self.createKatanaParam("isolateFrom")
        inverted_output_param = self.createKatanaParam("invertedOutput")

        self.layout().addWidget(cel_param)
        self.layout().addWidget(isolate_from_param)
        self.layout().addWidget(inverted_output_param)

        self.layout().setAlignment(Qt.AlignTop)

        # setup events
        Utils.EventModule.RegisterCollapsedHandler(self.enabledInvertedOutput, "parameter_finalizeValue", enabled=True)

    def node(self):
        return self._node

    def enableInvertedOutputParam(self):
        return self.node().enableInvertedOutputParam()

    def invertedOutputNode(self):
        return self.node()._inverted_output_node

    def enabledInvertedOutput(self, args):
        """ When the user clicks the "enable secondary (inverse) output button, this
        will enable/disable it.

        todo: Update inverted output
            will need to reconnect the correct node to the output"""
        for arg in args:
            node = arg[2]["node"]
            param = arg[2]["param"]
            if node == self.node() and param == self.enableInvertedOutputParam():
                value = param.getValue(0)
                if value == 0:
                    self.node().removeOutputPort("inverse")
                elif value == 1:
                    self.node().addOutputPort("inverse")
                    self.invertedOutputNode().getOutputPortByIndex(0).connect(self.node().getReturnPort("inverse"))