from Katana import NodegraphAPI, Utils

try:
    from Widgets2 import AbstractSuperToolNode
    from Utils2 import nodeutils, paramutils
except:
    pass


class ConstraintNode(AbstractSuperToolNode):
    """ The node portion of the constraint Node
    def constraintDisplayParam(self):
        return self.getParameter("ConstraintParams")
        #return self._constraint_display_param

    def constraintLocation(self):
        self.duplicateXFormNode().getParameter("user.constraint_location")

    def constraintNodeParam(self):
        return self.getParameter("ConstraintNode")


    Params:
        constraint_type_param (String): What type of constraint the user wants to use
        constraint_display_param (Teleparam): The actual params of the constraint node
        constraint_location (str): Determines the default location of the constraint
            This is needed as the default location for all constraints except for the
            ParentChildConstraint is last.  While the ParentChildConstraint is placed
            at the top of the stack.
        constraint_node_param (str): Reference to name of the current constraint node
        maintain_offset_param (int): Whether or not the offset should be maintained
            0 = Disabled
            1 = Enabled
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
        paramutils.createParamAtLocation("user.constraint_location", self._duplicate_xform_node, param_type=paramutils.STRING)

        self._duplicate_xform_node.getParameter("script.lua").setValue("""
--[[
Rearranges all of the xform values so that the constraint is on the
top of the stack and stores this as a new attribute called "xform2".

Note that this needs to be inverted for the ParentChildConstraint
as it for some reason has inverted the stack order, and by default
comes in as first, instead of the default of last.
]]

local xform = Interface.GetAttr("xform")
local num_children = xform:getNumberOfChildren()
local constraint_location = Interface.GetOpArg("user.constraint_location"):getValue()
-- constraint_location = "first"
-- copy constraint
-- constraint = xform:getChildByIndex(num_children-1)

if constraint_location == "last" then
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
elseif constraint_location == "first" then
    constraint_name = xform:getChildName(0)

    -- copy rest of xform stack
    for var=1, num_children  - 1 do
        local name = xform:getChildName(var)
        local child = xform:getChildByIndex(var)
        Interface.CopyAttr(
            "xform2.".. name,
            "xform."..name
        )
    end

    Interface.CopyAttr(
        "xform2.".. constraint_name,
        "xform.".. constraint_name
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
        self._maintain_offset_stack_order_param = paramutils.createParamAtLocation("user.stackOrder", self._maintain_offset_script_node, paramutils.NUMBER)
        self._maintain_offset_stack_order_param.setExpressionFlag(True)
        self._maintain_offset_stack_order_param.setExpression("=^/StackOrder")

        self._maintain_offset_script_node.getParameter("CEL").setExpressionFlag(True)
        self._maintain_offset_script_node.getParameter("CEL").setExpression(
            "={constraint_node_name}/basePath".format(constraint_node_name=self._constraint_node.getName()))

        # todo update lua script for ParentChildConstraint
        self._maintain_offset_script_node.getParameter("script.lua").setValue("""
function getXFormMatrix(locationPath, index)
    local xformAttr = Interface.GetGlobalXFormGroup(locationPath, index)
    local matAttr = XFormUtils.CalcTransformMatrixAtTime(xformAttr, 0.0)
    local matData = matAttr:getNearestSample(0.0)
    local mat = Imath.M44d(matData)
    return mat
end

-- get xform matrices
target_xform_path = Interface.GetOpArg("user.targetXFormPath"):getValue()
target_xform_mat = getXFormMatrix(target_xform_path, 0)

base_xform_path = Interface.GetOutputLocationPath()
base_xform_mat = getXFormMatrix(base_xform_path, 0)

offset_mat = base_xform_mat * target_xform_mat:inverse()

-- Rebuild offset matrix
--[[
    The xform matrix will need to be rebuilt depending on the type of constraint being used,
    and the current stack order.
]]
local stack_order = Interface.GetOpArg("user.stackOrder"):getValue()
local rebuilt_offset_mat = Imath.M44d()
local scale, shear, rotate, translate, result = offset_mat:extractSHRT()


-- "translate", "scale", "rotate", "parent"
local mode = Interface.GetOpArg("user.mode"):getValue()

-- stack order is last
if stack_order == 0 then
    -- Point Constraint
    if mode == "PointConstraint" then
        inverse_matrix = Imath.M44d()
        inverse_matrix:rotate(rotate)
        inverse_matrix:scale(scale)

        -- inverse_scale = Imath.V3d(1/scale:toTable()[1], 1/scale:toTable()[2], 1/scale:toTable()[3])
        translate = translate * inverse_matrix:inverse()

        rebuilt_offset_mat:translate(translate)

    -- Scale Constraint
    elseif mode == "ScaleConstraint" then
        rebuilt_offset_mat:scale(scale)

    -- Orient Constraint
    elseif mode == "OrientConstraint" then
        shear_matrix = Imath.M44d()
        rotation_matrix = Imath.M44d()
        inverse_matrix = Imath.M44d()

        shear_matrix:scale(scale)
        rotation_matrix:rotate(rotate)

        rebuilt_offset_mat = shear_matrix * rotation_matrix * shear_matrix:inverse()

    elseif mode == "ParentChildConstraint" then
        -- rebuilt_offset_mat = offset_mat:inverse()
    end

-- stack order is first
elseif stack_order == 1 then
    local xform_scale, xform_shear, xform_rotate, xform_translate, xform_result = target_xform_mat:extractSHRT()
    local base_scale, base_shear, base_rotate, base_translate, base_result = base_xform_mat:extractSHRT()
    local inverse_matrix = Imath.M44d()

    -- Point Constraint
    if mode == "PointConstraint" then
        inverse_matrix:rotate(base_rotate)
        inverse_matrix:scale(base_scale)


        xform_translate = xform_translate * inverse_matrix:inverse()

        rebuilt_offset_mat:translate(xform_translate)
        rebuilt_offset_mat = rebuilt_offset_mat:inverse()

    -- Scale Constraint
    elseif mode == "ScaleConstraint" then
        -- get base original matrix, prior to moving updating the stack order
        -- Need this for the final offset
        local base_orig_mat = getXFormMatrix(base_xform_path, 1)
        local orig_scale, orig_shear, orig_rotate, orig_translate, orig_result = base_orig_mat:extractSHRT()
        local base_orig_translation_mat = Imath.M44d()

        base_orig_translation_mat:translate(orig_translate)
        inverse_matrix:translate(base_translate)
        rebuilt_offset_mat:scale(xform_scale)

        rebuilt_offset_mat = base_orig_translation_mat * rebuilt_offset_mat:inverse() * inverse_matrix:inverse() 

    -- Orient Constraint
    elseif mode == "OrientConstraint" then
        shear_matrix = Imath.M44d()
        rotation_matrix = Imath.M44d()
        inverse_matrix = Imath.M44d()

        shear_matrix:scale(scale)
        rotation_matrix:rotate(xform_rotate)

        rebuilt_offset_mat = shear_matrix * rotation_matrix * shear_matrix:inverse()


    elseif mode == "ParentChildConstraint" then
    end
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

    """ NODES """
    def constraintNode(self):
        return NodegraphAPI.GetNode(self.getParameter("NodeReference.ConstraintNode").getValue(0))

    def setConstraintNode(self, constraint_node):
        self.getParameter("NodeReference.ConstraintNode").setExpression("@{name}".format(name=constraint_node.getName()))

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

    def constraintLocationParam(self):
        return self.duplicateXFormNode().getParameter("user.constraint_location")

    def constraintNodeParam(self):
        return self.getParameter("ConstraintNode")

    def constraintTypeParam(self):
        return self.getParameter("ConstraintType")

    def maintainOffsetParam(self):
        return self.getParameter("MaintainOffset")

    def stackOrderParam(self):
        return self.getParameter("StackOrder")

    """ PARAMS ( MAINTAIN OFFSET )"""
    def modeParam(self):
        return self.maintainOffsetScriptNode().getParameter("user.mode")


