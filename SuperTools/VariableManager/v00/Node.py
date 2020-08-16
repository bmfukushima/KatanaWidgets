import logging
import os

from Katana import NodegraphAPI, Utils, UniqueName, DrawingModule

from Settings import (
    PUBLISH_DIR,
    BLOCK_PREFIX,
    PATTERN_PREFIX
)
from Utils import mkdirRecursive, updateNodeName

log = logging.getLogger("Test.Node")


class VariableManagerNode(NodegraphAPI.SuperTool):
    """
    Node Parameters:
        variable_root_node (str): returns the variable root node name.
            This is the top level node of the variable stack.  This is
            store as the attribute variable_root_node in this class

    Attributes:
        variable_root_node (node): the top level node of the variable stack.
    """
    def __init__(self, populate=True):
        """
        Creates the default node hierarchy for this tool.  If
        populate is not true, this means that some other event
        happened, such as a copy/paste creation event.

        Args:
            populate (bool): determines whether or not
                this node should be populated from a default
                state (initialization), or if it should be left as in
                (instantiate).  This should only be True on the
                FIRST run, every other call should be forcing this
                to False.

        Attributes:
            block_group (node): The top most nodes block group
            node_type_param (param): String parameter that has the
                name of the current node type that this will be editing.
            publish_dir (param): string parameter that has the location
                of the current publish directory.  This is the root publish
                directory.
            variable_param (param): String parameter of the current
                GSV that is set up for editing.
            variable_root_node (node): The top most node that is not
                this node.  Can also be called with self.getChildByIndex(0)
        """
        print('init node')
        if populate is True:
            self.setupDefaultNodeState()
        else:
            self.setupInstancedNodeState()

    def setupInstancedNodeState(self):
        """
        When a node is instanced, this will restore all of the
        internal attributes on this class from the node.
        """
        self.variable_param = self.getParameter('variable')
        self.node_type_param = self.getParameter('node_type')
        self.publish_dir = self.getParameter('publish_dir')

        self.variable_root_node = self.getChildByIndex(0)
        block_node_name = self.variable_root_node.getParameter('nodeReference.block_group').getValue(0)
        self.block_group = NodegraphAPI.GetNode(block_node_name)

    def setupDefaultNodeState(self):
        """
        Sets up the default node state.  This will create all of the parameters,
        internal nodes, and wire everything up for a default working state.
        """

        # setup node
        NodegraphAPI.SetNodeShapeAttr(self, 'basicDisplay', 1)
        self.addOutputPort('out')
        self.addInputPort('in')
        self.getSendPort('in').connect(self.getReturnPort('out'))

        # create parameters
        self.variable_param = self.getParameters().createChildString('variable', '')
        self.variable_param.setHintString(repr({'readOnly': 'True'}))

        self.node_type_param = self.getParameters().createChildString('node_type', 'Group')
        self.publish_dir = self.getParameters().createChildString('publish_dir', PUBLISH_DIR)
        self.publish_dir.setHintString(repr({'widget': 'fileInput'}))

        # create root node
        self.variable_root_node = self.createBlockRootNode(self, 'master')
        block_node_name = self.variable_root_node.getParameter('nodeReference.block_group').getValue(0)
        self.block_group = NodegraphAPI.GetNode(block_node_name)

        # create parameter node references
        self.variable_root_node.getParameter('hash').setValue('master', 0)

        self.createNodeReference(self.variable_root_node, 'variable_root_node', node=self)
        self.createNodeReference(self.block_group, 'block_node', node=self)

        Utils.EventModule.ProcessAllEvents()

        # wire node
        self.connectInsideGroup([self.variable_root_node], self)

        if not os.path.exists(PUBLISH_DIR):
            os.mkdir(PUBLISH_DIR)

    def _reset(self, variable=''):
        """
        Deletes the entire inner working strucutre of this node, and resets
        the master root item.

        Kwargs:
            variable (str): name of the new GSV that this node will be using
        """
        self.updateVariableRootNode()
        self.variable_root_node.delete()
        self.getSendPort('in').connect(self.getReturnPort('out'))

        # Create directories
        node_list = []

        # Get references
        self.variable_root_node = self.createBlockRootNode(self, 'master')
        self.variable_root_node.getParameter('hash').setValue('master', 0)
        self.block_group = NodegraphAPI.GetNode(self.variable_root_node.getParameter('nodeReference.block_group').getValue(0))
        self.vs_node = NodegraphAPI.GetNode(self.variable_root_node.getParameter('nodeReference.vs_node').getValue(0))

        # Update references to nodes
        self.createNodeReference(self.variable_root_node, 'variable_root_node', node=self)
        self.createNodeReference(self.block_group, 'block_node', node=self)
        node_list.append(self.variable_root_node)
        Utils.EventModule.ProcessAllEvents()

        # wire nodes
        self.connectInsideGroup(node_list, self)

        # set GSV
        self.variable = variable

        # make directores
        if not os.path.exists(PUBLISH_DIR):
            os.mkdir(PUBLISH_DIR)

        if not os.path.exists(PUBLISH_DIR + '/%s' % self.variable):
            os.mkdir(PUBLISH_DIR + '/%s' % self.variable)
            os.mkdir(PUBLISH_DIR + '/%s/blocks' % self.variable)
            os.mkdir(PUBLISH_DIR + '/%s/patterns' % self.variable)

        self.variable_param.setValue(self.variable, 0)
        self.populateShots(self.variable)

    def createNodeReference(self, node_ref, param_name, param=None, node=None, index=-1):
        """
        Creates a new string parameter whose expression value
        returns a reference to a node.

        Args:
            node_ref (node): the node to be referenced
            param_name (str): the name of the new parameter to create
        Kwargs:
            node (node): node to create parameter on if param kwarg
                param is not provided
            param (group param): the param to create the new parameter as
                a child of
        Returns (string param)
        """
        if not param:
            param = node.getParameters()
        new_param = param.createChildString(param_name, '', index)
        new_param.setExpressionFlag(True)
        new_param.setExpression('@%s' % node_ref.getName())
        return new_param

    def populateShots(self, variable):
        root = NodegraphAPI.GetRootNode()
        node_list = []
        if root.getParameter('variables.%s' % variable):
            # VEG --> LG --> GS
            if root.getParameter('variables.%s.options' % variable):
                patterns = root.getParameter('variables.%s.options' % variable)
                for child in patterns.getChildren():
                    group_node = self.createPatternGroupNode(self.block_group, pattern=child.getValue(0))
                    node_list.append(group_node)
                    # connect VS NODE

                self.connectInsideGroup(node_list, self.block_group)

    def connectInsideGroup(self, node_list, parent_node):
        send_port = parent_node.getSendPort('in')
        return_port = parent_node.getReturnPort('out')
        if len(node_list) == 0:
            send_port.connect(return_port)
        elif len(node_list) == 1:
            node_list[0].getOutputPortByIndex(0).connect(return_port)
            node_list[0].getInputPortByIndex(0).connect(send_port)
        elif len(node_list) == 2:
            node_list[0].getInputPortByIndex(0).connect(send_port)
            node_list[1].getOutputPortByIndex(0).connect(return_port)
            node_list[0].getOutputPortByIndex(0).connect(node_list[1].getInputPortByIndex(0))
            NodegraphAPI.SetNodePosition(node_list[0], (0, 100))
        elif len(node_list) > 2:
            for index, node in enumerate(node_list[:-1]):
                node.getOutputPortByIndex(0).connect(node_list[index+1].getInputPortByIndex(0))
                NodegraphAPI.SetNodePosition(node, (0, index * -100))
            node_list[0].getInputPortByIndex(0).connect(send_port)
            node_list[-1].getOutputPortByIndex(0).connect(return_port)
            NodegraphAPI.SetNodePosition(node_list[-1], (0, len(node_list) * -100))

    """ NODE CREATION """
    def createVariableSwitch(self, parent_node):
        """
        Args:
            parent_node (node): the parent node that the variable switch
                should be created under.  This will always be a "block node".
        """
        vs_node = NodegraphAPI.CreateNode('VariableSwitch', parent_node)
        vs_node.addInputPort('default')
        variable = self.getParameter('variable').getValue(0)
        vs_node.getParameter('variableName').setValue(variable, 0)
        return vs_node

    def createNodeOfType(self, parent_node):
        """
        Creates a new node of a specifc type in a pattern node.
        The node type is chosen by the user with the Node Type
        menu.

        Args:
            parent_node (node): the parent node to create this new
                node under.  This will always be a "pattern" node.
        """
        node_type = self.getParameter('node_type').getValue(0)

        child_node = NodegraphAPI.CreateNode(node_type, parent_node)

        if len(child_node.getInputPorts()) == 0:
            child_node.addInputPort('i0')
        child_node.getInputPortByIndex(0).connect(parent_node.getSendPort('in'))
        child_node.getOutputPortByIndex(0).connect(parent_node.getReturnPort('out'))

    def createGroupNode(self, parent_node, name=''):
        """
        Creates an empty group node to be used as a container for other things...

        Args:
            parent_node (node)
            name (str)

        Returns:
            node (Group Node)
        """
        # create node
        group_node = NodegraphAPI.CreateNode('Group', parent_node)

        # set params
        group_node.setName(name)
        group_node.getParameters().createChildGroup('nodeReference')

        # wire
        group_node.addOutputPort('out')
        group_node.addInputPort('in')
        group_node.getReturnPort('out').connect(group_node.getSendPort('in'))

        return group_node

    def createBlockGroupNode(self, block_root_node, name='None'):
        group_node = self.createGroupNode(block_root_node, name=name)
        return group_node

    def createBlockRootNode(self, parent_node, name='block_01'):
        """
        Creates a new block or container for holding patterns.

        This will create all of the nodes necessary and wire them into
        the parent node provided (block node).

        Args:
            parent_node (node): the node to create this new block under.
                This should be another block node.
            name (str):
                The name of this block
        """
        # Create Nodes
        block_root_node = self.createGroupNode(parent_node, name=name)
        block_root_node.getParameters().createChildString('type', 'root')
        pattern_group = self.createPatternGroupNode(block_root_node, pattern='master')
        block_group = self.createBlockGroupNode(block_root_node, name='block')
        block_group.getParameters().createChildString('type', 'block')
        vs_node = self.createVariableSwitch(block_root_node)

        # initialize default parameters

        add_params_node_list = [block_root_node, block_group]
        for node in add_params_node_list:
            params = node.getParameters()
            params.createChildString('version', '')
            params.createChildString('hash', '')
            params.createChildString('expanded', 'False')
            params.createChildString('name', name)

        # create parameter node references
        group_params = block_root_node.getParameter('nodeReference')
        self.createNodeReference(pattern_group, 'pattern_node', param=group_params)
        self.createNodeReference(block_group, 'block_group', param=group_params)
        self.createNodeReference(vs_node, 'vs_node', param=group_params)
        param_name = '%s_%s' % (BLOCK_PREFIX, block_root_node.getName())
        self.createNodeReference(block_root_node, param_name, node=self)

        # create reference if parent is a block node...
        if parent_node != self:
            parent_node_type = parent_node.getParameter('type').getValue(0)
            if parent_node_type == 'block':
                block_string = '{block_prefix}{block_name}'.format(
                    block_prefix=BLOCK_PREFIX,
                    block_name=block_root_node.getName()
                )
                self.createNodeReference(block_root_node, block_string, param=parent_node.getParameter('nodeReference'))

        # connect
        self.connectInsideGroup([pattern_group, block_group, vs_node], block_root_node)
        block_root_node.getSendPort('in').connect(vs_node.getInputPortByIndex(0))

        # finalize block root node params
        updateNodeName(block_root_node)

        return block_root_node

    def createPatternGroupNode(self, parent_node, pattern='<None>', name='pattern'):
        """
        Creates a group to hold changes on this specific pattern
        live group --> variable enable group -->  gaffer three

        Args:
            parent_node (node): the node that this group should
                become a child of
            pattern (str): The GSV Pattern to be created
        """

        variable = self.getParameter('variable').getValue(0)
        pattern_string = '%s%s' % (PATTERN_PREFIX, pattern)
        # create the pattern root node
        if not name:
            name = pattern
        pattern_root_node = self.createGroupNode(parent_node, name=pattern_string)

        # create parameters

        # create reference to pattern
        parent_node_type = parent_node.getParameter('type').getValue(0)
        if parent_node_type == 'block':
            self.createNodeReference(pattern_root_node, pattern_string, param=parent_node.getParameter('nodeReference'))

        # create parameters
        pattern_root_node.getParameters().createChildString('version', '')
        pattern_root_node.getParameters().createChildString('hash', '%s_%s' % (variable, pattern))
        pattern_root_node.getParameters().createChildString('pattern', '%s' % (pattern))
        pattern_root_node.getParameters().createChildString('type', 'pattern')

        # wire node
        pattern_root_node.getInputPortByIndex(0).connect(parent_node.getSendPort('in'))
        pattern_root_node.getOutputPortByIndex(0).connect(parent_node.getReturnPort('out'))
        # Create Variable Enabled Group Container
        veg_node = NodegraphAPI.CreateNode('VariableEnabledGroup', pattern_root_node)

        # wire node
        veg_node.addOutputPort('out')
        veg_node.addInputPort('in')
        veg_node.getSendPort('in').connect(veg_node.getReturnPort('out'))
        veg_node.getInputPortByIndex(0).connect(pattern_root_node.getSendPort('in'))
        veg_node.getOutputPortByIndex(0).connect(pattern_root_node.getReturnPort('out'))

        # set up params
        veg_node.getParameter('variableName').setValue(variable, 0)
        if parent_node_type == 'root':
            veg_node.getParameter('pattern').setValue('*', 0)
        else:
            veg_node.getParameter('pattern').setValue(pattern, 0)
        veg_node.setName(pattern_string)

        # create publish dirs
        if variable != '':
            publish_dir = '{publish_dir}/{variable}/patterns/{variable}_{pattern}'.format(
                publish_dir=self.getParameter('publish_dir').getValue(0),
                variable=variable,
                pattern=pattern
            )
            if not os.path.exists(publish_dir):
                dir_list = ['pattern', 'block']
                mkdirRecursive(publish_dir)
                for dir_item in dir_list:
                    os.mkdir(publish_dir + '/%s' % dir_item)
                    os.mkdir(publish_dir + '/%s/live' % dir_item)

        # create node of specific type
        if self.getParameter('node_type').getValue(0) != 'Group':
            self.createNodeOfType(veg_node)

        return pattern_root_node

    """ UTILS """
    def updateVariableRootNode(self):
        """
        Updates the variable root node attribute to the node parameter.
        """
        variable_root_node = NodegraphAPI.GetNode(self.getParameter('variable_root_node').getValue(0))
        self.variable_root_node = variable_root_node

    """ PROPERTIES """
    @property
    def variable_root_node(self):
        try:
            return self._variable_root_node
        except AttributeError:
            return self.getChildByIndex(0)

    @variable_root_node.setter
    def variable_root_node(self, variable_root_node):
        self._variable_root_node = variable_root_node
