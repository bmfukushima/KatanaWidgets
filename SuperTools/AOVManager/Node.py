try:
    from Widgets2 import AbstractSuperToolNode
    from Utils2 import nodeutils
except:
    pass


class AOVManagerNode(AbstractSuperToolNode):
    def __init__(self):
        super(AOVManagerNode, self).__init__()

        # initialize base node
        self.setGroupDisplay(False)
        nodeutils.createIOPorts(self)

        # create parameters
        #self.getParameters().createChildString("renderLocation", "")
        #self.getParameters().createChildString("renderer", "")