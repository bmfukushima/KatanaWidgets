from Katana import NodegraphAPI

from Widgets2 import (
    AbstractSuperToolNode
)


class TwoFaceSuperToolNode(AbstractSuperToolNode):
    def __init__(self):
        self.setGroupDisplay(False)

        # add input ports...
        self.createIOPorts()
        self.getInputPortByIndex(0).connect(self.getSendPort('in'))
        self.getOutputPortByIndex(0).connect(self.getReturnPort('out'))

        # create display param
        self.getParameters().createChildNumber('display_mode', 0)