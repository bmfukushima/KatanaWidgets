from Katana import NodegraphAPI

try:
    from Widgets2 import AbstractSuperToolNode
    from Utils2 import nodeutils, paramutils
except:
    pass


class ConstraintNode(AbstractSuperToolNode):
    """ The node portion of the contraint Node

    Params:
        constraint_type_param (String): What type of constraint the user wants to use
        constraint_params (Teleparam): The actual params of the constraint node
        maintain_offset (int): Whether or not the constraint should maintain the offsets"""
    def __init__(self):
        super(ConstraintNode, self).__init__()

        # initialize base node
        self.setGroupDisplay(False)
        nodeutils.createIOPorts(self)

        # setup nodes
        self._constraint_node = NodegraphAPI.CreateNode("Dot", self)
        self._constraint_node.getParameters().createChildString("basePath", "")

        self._duplicate_xform_node = NodegraphAPI.CreateNode("OpScript", self)
        self._duplicate_xform_node.getParameter("CEL").setExpressionFlag(True)
        self._duplicate_xform_node.getParameter("CEL").setExpression("={constraint_node_name}/basePath".format(constraint_node_name=self._constraint_node.getName()))

        self._duplicate_xform_node.getParameter("script.lua").setValue("""
-- Rearranges all of the xform values so that the constraint is on the
-- top of the stack and stores this as a new attribute called "xform2"
local xform = Interface.GetAttr("xform")
local num_children = xform:getNumberOfChildren()

-- copy constraint
constraint = xform:getChildByIndex(num_children-1)
constraint_name = xform:getChildName(num_children-1)
Interface.CopyAttr(
    "xform2.".. constraint_name,
    "xform.".. constraint_name
)

-- copy rest of xform stack
for var=0, num_children  - 2 do

    local name = xform:getChildName(var)
    local child = xform:getChildByIndex(var)
    Interface.CopyAttr(
        "xform2.".. name,
        "xform."..name
    )
end

Interface.DeleteAttr("xform")
-- Interface.CopyAttr("xform", "xform2")
        """, 0)

        self._transfer_xform_node = NodegraphAPI.CreateNode("OpScript", self)
        self._transfer_xform_node.getParameter("CEL").setExpressionFlag(True)
        self._transfer_xform_node.getParameter("CEL").setExpression("={constraint_node_name}/basePath".format(constraint_node_name=self._constraint_node.getName()))
        self._transfer_xform_node.getParameter("script.lua").setValue("""
-- Copies the temp xform attr back to the xform attr

xform2 = Interface.GetAttr("xform2")

for var=0, xform2:getNumberOfChildren() do
    local name = xform2:getChildName(var)
    local child = xform2:getChildByIndex(var)
    Interface.CopyAttr(
        "xform.".. name,
        "xform2."..name
    )
end

Interface.DeleteAttr("xform2")
        """, 0)

        self._maintain_offset_node = NodegraphAPI.CreateNode("Switch", self)
        self._maintain_offset_node.addInputPort("original")
        self._maintain_offset_node.addInputPort("maintain_offset")
        self._maintain_offset_node.getParameter("in").setExpressionFlag(True)
        self._maintain_offset_node.getParameter("in").setExpression("=^/MaintainOffset")

        # connect nodes
        self.getSendPort("in").connect(self._constraint_node.getInputPortByIndex(0))
        self._constraint_node.getOutputPortByIndex(0).connect(self._duplicate_xform_node.getInputPortByIndex(0))
        self._duplicate_xform_node.getOutputPortByIndex(0).connect(self._transfer_xform_node.getInputPortByIndex(0))
        self._transfer_xform_node.getOutputPortByIndex(0).connect(self._maintain_offset_node.getInputPortByIndex(1))
        self._constraint_node.getOutputPortByIndex(0).connect(self._maintain_offset_node.getInputPortByIndex(0))
        self._maintain_offset_node.getOutputPortByIndex(0).connect(self.getReturnPort("out"))

        # place nodes
        NodegraphAPI.SetNodePosition(self._duplicate_xform_node, (0, -100))
        NodegraphAPI.SetNodePosition(self._transfer_xform_node, (0, -200))
        NodegraphAPI.SetNodePosition(self._maintain_offset_node, (0, -300))

        # setup params
        self._constraint_type_param = self.getParameters().createChildString("ConstraintType", "")

        self._maintain_offset_param = self.getParameters().createChildNumber("MaintainOffset", 0)
        self._maintain_offset_param.setHintString(repr({"widget": "checkBox"}))

        self._constraint_display_param = self.getParameters().createChildString("ConstraintParams", "")
        self._constraint_display_param.setHintString(repr({"widget": "teleparam", "hideTitle":True}))
        self._constraint_display_param.setExpressionFlag(True)

    """ NODES """
    def constraintNode(self):
        return self._constraint_node

    def setConstraintNode(self, constraint_node):
        self._constraint_node = constraint_node

    def duplicateXFormNode(self):
        return self._duplicate_xform_node

    def transferXFormNode(self):
        return self._transfer_xform_node

    def maintainOffsetNode(self):
        return self._maintain_offset_node

    """ PARAMS """
    def constraintDisplayParam(self):
        return self._constraint_display_param

    def constraintTypeParam(self):
        return self._constraint_type_param

    def maintainOffsetParam(self):
        return self._maintain_offset_param

