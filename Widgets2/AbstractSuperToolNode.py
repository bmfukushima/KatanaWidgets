from Katana import NodegraphAPI


class AbstractSuperToolNode(NodegraphAPI.SuperTool):

    def __init__(self):
        pass

    def createIOPorts(self, in_port=True, out_port=True, connect=True):

        if in_port is True:
            self.addInputPort('in')

        if out_port is True:
            self.addOutputPort('out')

        if connect is True:
            if in_port is True and out_port is True:
                self.getSendPort('in').connect(self.getReturnPort('out'))

    def setGroupDisplay(self, bool):
        """
        Sets the display of the node from Group --> Basic
        bool (bool): if True will make this node look like a Group,
            if False will make this node appear like every other node.
        """
        if bool:
            NodegraphAPI.SetNodeShapeAttr(self, 'basicDisplay', 0)
        else:
            NodegraphAPI.SetNodeShapeAttr(self, 'basicDisplay', 1)