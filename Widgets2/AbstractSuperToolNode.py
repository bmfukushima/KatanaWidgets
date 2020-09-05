from Katana import NodegraphAPI


class AbstractSuperToolNode(NodegraphAPI.SuperTool):

    def __init__(self):
        pass

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