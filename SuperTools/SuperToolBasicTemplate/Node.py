from Katana import NodegraphAPI
# todo import error...
"""
This is a repeating error for all of the imports from anything thats not
located relatively to this lib...

for some reason katana actually tries to load this twice...

amazingly it still fails and loads... but should fix... the error is really
a python 2-3 thing right now... so meh
"""
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
