from Katana import NodegraphAPI, Utils

try:
    from Widgets2 import AbstractSuperToolNode
    from Utils2 import nodeutils, paramutils
except:
    pass


class ConstraintNode(AbstractSuperToolNode):
    """ The node portion of the constraint Node

    Params:
        constraint_type_param (String): What type of constraint the user wants to use
        constraint_display_param (Teleparam): The actual params of the constraint node
        stack_order_param (int): Whether or not the constraint should maintain the offsets

    Nodes:
        constraint_node (ConstraintNode): Constraint node
        constraint_dot_node (Dot): helper dot node for reconnection purposes
        duplicate_xform_node (OpScript): puts the new constraint xform at the top of the stack,
            and sets the attr as "xform2"
        transfer_xform_node (OpScript): copies the "xform2" attr made in the "duplicate_xform_node"
            back to the "xform" attr
        stack_order_switch_node (Switch): Switch node that will control the stack order.
            This is controlled by the stackOrderParam()
            0 = last
            1 = first

        maintain_offset_script_node (OpScript): Creates an inverse matrix of the offset between
            the base/target items.

            Applies this inverse matrix to the end of the stack

        maintain_offset_switch_node (Switch): Switch node that will control the maintain offset option.
            This is controlled by the maintainOffsetParam()
    """

    def __init__(self):
        super(ConstraintNode, self).__init__()

        # initialize base node
        self.setGroupDisplay(False)
        nodeutils.createIOPorts(self)

        # create nodes
        self._constraint_node = None

        self._constraint_node = NodegraphAPI.CreateNode("Dot", self)
        self._constraint_node.getParameters().createChildString("basePath", "")

        self._constraint_dot_node = NodegraphAPI.CreateNode("Dot", self)

        self.__setupStackOrderNodes()
        self.__setupMaintainOffsetNodes()

        # connect nodes
        self.getSendPort("in").connect(self._constraint_node.getInputPortByIndex(0))
        self._constraint_node.getOutputPortByIndex(0).connect(self._constraint_dot_node.getInputPortByIndex(0))
        self._constraint_dot_node.getOutputPortByIndex(0).connect(self._stack_order_switch_node.getInputPortByIndex(0))

        # connect nodes (stack order)
        self._constraint_dot_node.getOutputPortByIndex(0).connect(self._duplicate_xform_node.getInputPortByIndex(0))
        self._duplicate_xform_node.getOutputPortByIndex(0).connect(self._transfer_xform_node.getInputPortByIndex(0))
        self._transfer_xform_node.getOutputPortByIndex(0).connect(self._stack_order_switch_node.getInputPortByIndex(1))

        # connect nodes (maintain offset)
        self._stack_order_switch_node.getOutputPortByIndex(0).connect(self._maintain_offset_script_node.getInputPortByIndex(0))
        self._stack_order_switch_node.getOutputPortByIndex(0).connect(self._maintain_offset_switch_node.getInputPortByIndex(0))
        self._maintain_offset_script_node.getOutputPortByIndex(0).connect(self._maintain_offset_switch_node.getInputPortByIndex(1))
        self._maintain_offset_switch_node.getOutputPortByIndex(0).connect(self.getReturnPort("out"))

        # place nodes
        NodegraphAPI.SetNodePosition(self._constraint_dot_node, (0, -100))
        NodegraphAPI.SetNodePosition(self._duplicate_xform_node, (0, -200))
        NodegraphAPI.SetNodePosition(self._transfer_xform_node, (0, -300))
        NodegraphAPI.SetNodePosition(self._stack_order_switch_node, (0, -400))
        NodegraphAPI.SetNodePosition(self._maintain_offset_script_node, (0, -500))
        NodegraphAPI.SetNodePosition(self._maintain_offset_switch_node, (0, -600))

        # setup params
        self._constraint_type_param = self.getParameters().createChildString("ConstraintType", "")
        self._stack_order_param = self.getParameters().createChildNumber("StackOrder", 0)
        self._maintain_offset_param = self.getParameters().createChildNumber("MaintainOffset", 0)

        # self._stack_order_param.setHintString(repr({"widget": "checkBox"}))

        self._constraint_display_param = self.getParameters().createChildString("ConstraintParams", "")
        self._constraint_display_param.setHintString(repr({"widget": "teleparam", "hideTitle":True}))
        self._constraint_display_param.setExpressionFlag(True)

    def __setupStackOrderNodes(self):
        """ Helper function to setup the stack order nodes"""
        # puts the new constraint xform at the top of the stack, and sets the attr as "xform2"
        self._duplicate_xform_node = NodegraphAPI.CreateNode("OpScript", self)
        self._duplicate_xform_node.getParameter("CEL").setExpressionFlag(True)
        self._duplicate_xform_node.getParameter("CEL").setExpression(
            "={constraint_node_name}/basePath".format(constraint_node_name=self._constraint_node.getName()))

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

        # copies the "xform2" attr made in the "duplicate_xform_node" back to the "xform" attr
        self._transfer_xform_node = NodegraphAPI.CreateNode("OpScript", self)
        self._transfer_xform_node.getParameter("CEL").setExpressionFlag(True)
        self._transfer_xform_node.getParameter("CEL").setExpression(
            "={constraint_node_name}/basePath".format(constraint_node_name=self._constraint_node.getName()))
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

        self._stack_order_switch_node = NodegraphAPI.CreateNode("Switch", self)
        self._stack_order_switch_node.addInputPort("last")
        self._stack_order_switch_node.addInputPort("first")
        self._stack_order_switch_node.getParameter("in").setExpressionFlag(True)
        self._stack_order_switch_node.getParameter("in").setExpression("=^/StackOrder")

    def __setupMaintainOffsetNodes(self):
        self._stack_order_switch_node

        self._maintain_offset_script_node = NodegraphAPI.CreateNode("OpScript", self)
        self._maintain_offset_script_node.getParameter("CEL").setExpressionFlag(True)
        self._maintain_offset_script_node.getParameter("CEL").setExpression(
            "={constraint_node_name}/basePath".format(constraint_node_name=self._constraint_node.getName()))

        self._maintain_offset_script_node.getParameter("script.lua").setValue("""
-- Maintain offset code placeholder
                """, 0)

        self._maintain_offset_switch_node = NodegraphAPI.CreateNode("Switch", self)
        self._maintain_offset_switch_node.addInputPort("last")
        self._maintain_offset_switch_node.addInputPort("first")
        self._maintain_offset_switch_node.getParameter("in").setExpressionFlag(True)
        self._maintain_offset_switch_node.getParameter("in").setExpression("=^/MaintainOffset")

        pass

    """ NODES """
    def constraintNode(self):
        return self._constraint_node

    def constraintDotNode(self):
        return self._constraint_dot_node

    def setConstraintNode(self, constraint_node):
        self._constraint_node = constraint_node

    """ NODES ( STACK ORDER ) """
    def duplicateXFormNode(self):
        return self._duplicate_xform_node

    def transferXFormNode(self):
        return self._transfer_xform_node

    def stackOrderSwitchNode(self):
        return self._stack_order_switch_node

    """ NODES ( MAINTAIN OFFSET )"""
    def maintainOffsetSwitchNode(self):
        return self._maintain_offset_switch_node

    def maintainOffsetScriptNode(self):
        return self._maintain_offset_script_node

    """ PARAMS """
    def constraintDisplayParam(self):
        return self._constraint_display_param

    def constraintTypeParam(self):
        return self._constraint_type_param

    def maintainOffsetParam(self):
        return self._maintain_offset_param

    def stackOrderParam(self):
        return self._stack_order_param


