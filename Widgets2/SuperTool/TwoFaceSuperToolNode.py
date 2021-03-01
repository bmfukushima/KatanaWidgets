from Katana import NodegraphAPI

from .AbstractSuperToolNode import AbstractSuperToolNode
#from Widgets2 import (AbstractSuperToolNode)
from Utils2 import nodeutils


class TwoFaceSuperToolNode(AbstractSuperToolNode):
    def __init__(self):
        self.setGroupDisplay(False)

        # add input ports...
        nodeutils.createIOPorts(self)
        self.getInputPortByIndex(0).connect(self.getSendPort('in'))
        self.getOutputPortByIndex(0).connect(self.getReturnPort('out'))

        # create display param
        self.getParameters().createChildNumber('display_mode', 0)