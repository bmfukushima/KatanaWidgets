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


class SuperToolNode(AbstractSuperToolNode):
    def __init__(self):
        super(SuperToolNode, self).__init__()

        # initialize base node
        self.setGroupDisplay(False)
        nodeutils.createIOPorts(self)

        # create nodes
        _attribute_set_node = NodegraphAPI.CreateNode("AttributeSet", self)
        _prune_node = NodegraphAPI.CreateNode("Prune", self)

        # connect nodes
        _attribute_set_node.getInputPortByIndex(0).connect(self.getSendPort("in"))
        _attribute_set_node.getOutputPortByIndex(0).connect(_prune_node.getInputPortByIndex(0))
        _prune_node.getOutputPortByIndex(0).connect(self.getReturnPort("out"))

        # position nodes
        NodegraphAPI.SetNodePosition(_attribute_set_node, (0, 100))

        # create user parameters
        cel_param = self.getParameters().createChildString("CEL", "")
        cel_param.setHintString(repr({"widget": "cel"}))

        isolate_from_param = self.getParameters().createChildString("isolateFrom", "")
        isolate_from_param.setHintString(repr({"widget": "scenegraphLocation"}))

        node_name = self.getParameters().createChildString("nodeName", "")
        node_name.setExpressionFlag(True)
        node_name.setExpression("@{name}".format(name=self.getName()))

        # link parameters
        prune_cel_param = _prune_node.getParameter('cel')
        prune_cel_param.setExpressionFlag(True)
        prune_cel_param.setExpression("=^/IsolateFrom + \"//*{not hasattr(\\\"\" + ^/nodeName + \"\\\") and attr(\\\"type\\\") != \\\"group\\\"}\"")

        _attribute_set_node.getParameter('mode').setValue("CEL", 0)
        cel_param = _attribute_set_node.getParameter('celSelection')
        cel_param.setExpressionFlag(True)
        cel_param.setExpression("=^/CEL")
        _attribute_set_node.getParameter('attributeName').setValue(self.getName(), 0)
        _attribute_set_node.getParameter('attributeType').setValue("integer", 0)

    def attributeSetNode(self):
        return self._attribute_set_node

    def pruneNode(self):
        return self._prune_node

