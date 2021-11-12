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
        mode (str): mode to be set
            ParentChildConstraint | OrientConstraint | PointConstraint | ScaleConstraint

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

        # create temp constraint node
        self._constraint_node = NodegraphAPI.CreateNode("Dot", self)
        self._constraint_node.getParameters().createChildString("basePath", "")
        self._constraint_node.getParameters().createChildString("targetPath", "")

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

        self.__setupParams()

    def __setupParams(self):
        node_reference_param = self.getParameters().createChildGroup("NodeReference")
        paramutils.createNodeReference("ConstraintNode", self._constraint_node, node_reference_param)
        paramutils.createNodeReference("ConstraintDotNode", self._constraint_dot_node, node_reference_param)
        paramutils.createNodeReference("DuplicateXFormNode", self._duplicate_xform_node, node_reference_param)
        paramutils.createNodeReference("TransferXFormNode", self._transfer_xform_node, node_reference_param)
        paramutils.createNodeReference("StackOrderSwitchNode", self._stack_order_switch_node, node_reference_param)
        paramutils.createNodeReference("MaintainOffsetSwitchNode", self._maintain_offset_switch_node, node_reference_param)
        paramutils.createNodeReference("MaintainOffsetScriptNode", self._maintain_offset_script_node, node_reference_param)

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
        self._duplicate_xform_node.setName("DuplicateXFormScript")
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
        self._transfer_xform_node.setName("TransferXFormScript")
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
        # setup switch node
        self._stack_order_switch_node = NodegraphAPI.CreateNode("Switch", self)
        self._stack_order_switch_node.setName("StackOrderSwitch")
        self._stack_order_switch_node.addInputPort("last")
        self._stack_order_switch_node.addInputPort("first")
        self._stack_order_switch_node.getParameter("in").setExpressionFlag(True)
        self._stack_order_switch_node.getParameter("in").setExpression("=^/StackOrder")

    def __setupMaintainOffsetNodes(self):

        self._maintain_offset_script_node = NodegraphAPI.CreateNode("OpScript", self)
        self._maintain_offset_script_node.setName("MaintainOffsetScript")

        # create params
        target_xform_param = paramutils.createParamAtLocation("user.targetXFormPath", self._maintain_offset_script_node, paramutils.STRING)
        target_xform_param.setExpressionFlag(True)
        # todo set expression flag here might need to be a teleparam? Since this is going to reference a number
        target_xform_param.setExpression("={constraint_node_name}/targetPath".format(constraint_node_name=self._constraint_node.getName()))

        self._mode_param = paramutils.createParamAtLocation("user.mode", self._maintain_offset_script_node, paramutils.STRING)
        # self._mode_param.setExpressionFlag(True)
        # self._mode_param.setExpression("\'\'")

        self._maintain_offset_script_node.getParameter("CEL").setExpressionFlag(True)
        self._maintain_offset_script_node.getParameter("CEL").setExpression(
            "={constraint_node_name}/basePath".format(constraint_node_name=self._constraint_node.getName()))

        # todo update lua script for ParentChildConstraint
        self._maintain_offset_script_node.getParameter("script.lua").setValue("""
function getXFormMatrix(locationPath)
    local xformAttr = Interface.GetGlobalXFormGroup(locationPath)
    local matAttr = XFormUtils.CalcTransformMatrixAtTime(xformAttr, 0.0)
    local matData = matAttr:getNearestSample(0.0)
    local mat = Imath.M44d(matData)
    return mat
end

target_xform_path = Interface.GetOpArg("user.targetXFormPath"):getValue()
target_xform = getXFormMatrix(target_xform_path)

base_xform_path = Interface.GetOutputLocationPath()
base_xform = getXFormMatrix(base_xform_path)

--offset = target_xform:inverse() * base_xform

offset_mat = base_xform * target_xform:inverse()

-- Rebuild offset matrix
local rebuilt_offset_mat = Imath.M44d()
local scale, shear, rotate, translate, result = offset_mat:extractSHRT()

-- "translate", "scale", "rotate", "parent"
local mode = Interface.GetOpArg("user.mode"):getValue()

if mode == "PointConstraint" then
    inverse_matrix = Imath.M44d()
    inverse_matrix:rotate(rotate)
    inverse_matrix:scale(scale)

    -- inverse_scale = Imath.V3d(1/scale:toTable()[1], 1/scale:toTable()[2], 1/scale:toTable()[3])
    translate = translate * inverse_matrix:inverse()

    rebuilt_offset_mat:translate(translate)

elseif mode == "ScaleConstraint" then
    inverse_matrix = Imath.M44d()
    -- inverse_matrix:translate(translate)
    -- inverse_matrix:rotate(rotate)

    scale = scale * inverse_matrix:inverse()

    rebuilt_offset_mat:scale(scale)

elseif mode == "OrientConstraint" then
    shear_matrix = Imath.M44d()
    rotation_matrix = Imath.M44d()
    inverse_matrix = Imath.M44d()

    shear_matrix:scale(scale)
    rotation_matrix:rotate(rotate)

    rebuilt_offset_mat = shear_matrix * rotation_matrix * shear_matrix:inverse()

elseif mode == "ParentChildConstraint" then
    rebuilt_offset_mat = Imath.M44d()
end





Interface.SetAttr("xform.group0.matrix", DoubleAttribute(rebuilt_offset_mat:toTable(),16))
                """, 0)

        # setup switch node
        self._maintain_offset_switch_node = NodegraphAPI.CreateNode("Switch", self)
        self._maintain_offset_switch_node.setName("MaintainOffsetSwitch")
        self._maintain_offset_switch_node.addInputPort("last")
        self._maintain_offset_switch_node.addInputPort("first")
        self._maintain_offset_switch_node.getParameter("in").setExpressionFlag(True)
        self._maintain_offset_switch_node.getParameter("in").setExpression("=^/MaintainOffset")

        pass

    """ NODES """
    def constraintNode(self):
        return NodegraphAPI.GetNode(self.getParameter("NodeReference.ConstraintNode").getValue(0))

    def setConstraintNode(self, constraint_node):
        self.getParameter("NodeReference.ConstraintNode").setExpression("@{name}".format(name=constraint_node.getName()))
        #self._constraint_node = constraint_node

    def constraintDotNode(self):
        return NodegraphAPI.GetNode(self.getParameter("NodeReference.ConstraintDotNode").getValue(0))

    """ NODES ( STACK ORDER ) """
    def duplicateXFormNode(self):
        return NodegraphAPI.GetNode(self.getParameter("NodeReference.DuplicateXFormNode").getValue(0))

    def transferXFormNode(self):
        return NodegraphAPI.GetNode(self.getParameter("NodeReference.TransferXFormNode").getValue(0))

    def stackOrderSwitchNode(self):
        return NodegraphAPI.GetNode(self.getParameter("NodeReference.StackOrderSwitchNode").getValue(0))

    """ NODES ( MAINTAIN OFFSET )"""
    def maintainOffsetSwitchNode(self):
        return NodegraphAPI.GetNode(self.getParameter("NodeReference.MaintainOffsetSwitchNode").getValue(0))

    def maintainOffsetScriptNode(self):
        return NodegraphAPI.GetNode(self.getParameter("NodeReference.MaintainOffsetScriptNode").getValue(0))

    """ PARAMS """
    def constraintDisplayParam(self):
        return self.getParameter("ConstraintParams")
        #return self._constraint_display_param

    def constraintNodeParam(self):
        return self.getParameter("ConstraintNode")

    def constraintTypeParam(self):
        return self.getParameter("ConstraintType")
        #return self._constraint_type_param

    def maintainOffsetParam(self):
        return self.getParameter("MaintainOffset")
        #return self._maintain_offset_param

    def stackOrderParam(self):
        return self.getParameter("StackOrder")
        # return self._stack_order_param

    """ PARAMS ( MAINTAIN OFFSET )"""
    def modeParam(self):
        return self.maintainOffsetScriptNode().getParameter("user.mode")
        #return self._mode_param


