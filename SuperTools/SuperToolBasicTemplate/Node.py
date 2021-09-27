try:
    from Widgets2 import AbstractSuperToolNode
    from Utils2 import nodeutils
except:
    pass


class SuperToolBasicNode(AbstractSuperToolNode):
    def __init__(self):
        super(SuperToolBasicNode, self).__init__()

        # initialize base node
        self.setGroupDisplay(False)
        nodeutils.createIOPorts(self)

        parent = self.getParameters().createChildGroup("GroupParam")
        parent.createChildString("StringParam", "")
        self.getParameters().createChildString("StringParam", "")
