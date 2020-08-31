import logging
import os

from Katana import NodegraphAPI, Utils, UniqueName, DrawingModule

from .Settings import (
    PUBLISH_DIR,
    BLOCK_PREFIX,
    PATTERN_PREFIX
)
from .Utils import (
    connectInsideGroup,
    createNodeReference,
    mkdirRecursive,
    transferNodeReferences
)

from .ItemTypes import (
    BLOCK_ITEM,
    MASTER_ITEM,
    PATTERN_ITEM
)

from Utils2 import (
    createUniqueHash
)

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
        if populate is True:
            self.setupDefaultNodeState()
        else:
            self.setupInstancedNodeState()

    def setupDefaultNodeState(self):
        """
        Sets up the default node state.  This will create all of the parameters,
        internal nodes, and wire everything up for a default working state.
        """
        # undo hack param
        self.getParameters().createChildString('undoozable', 'you like my hack?')

        # setup node
        NodegraphAPI.SetNodeShapeAttr(self, 'basicDisplay', 1)
        self.addOutputPort('out')
        self.addInputPort('in')
        self.getSendPort('in').connect(self.getReturnPort('out'))

        # create parameters
        self.variable_param = self.getParameters().createChildString('variable', '')
        self.variable_param.setHintString(repr({'readOnly': 'True'}))

        self.node_type_param = self.getParameters().createChildString('node_type', '')

        # publish_dir has to exist... to run through preflight checks =\
        #self.publish_dir = self.getParameters().createChildString('publish_dir', PUBLISH_DIR)
        #self.publish_dir.setHintString(repr({'widget': 'fileInput'}))

        # create root node
        self.variable_root_node = self.createBlockRootNode(self, 'master')
        block_node_name = self.variable_root_node.getParameter('nodeReference.block_group').getValue(0)
        self.block_group = NodegraphAPI.GetNode(block_node_name)

        # create parameter node references
        self.variable_root_node.getParameter('hash').setValue('master', 0)

        createNodeReference(self.variable_root_node, 'variable_root_node', node=self)
        createNodeReference(self.block_group, 'block_node', node=self)

        Utils.EventModule.ProcessAllEvents()

        # wire node
        connectInsideGroup([self.variable_root_node], self)

        # create default publish dir
        # mkdirRecursive(PUBLISH_DIR)

    def setupInstancedNodeState(self):
        """
        When a node is instanced, this will restore all of the
        internal attributes on this class from the node.
        """
        self.variable_param = self.getParameter('variable')
        self.node_type_param = self.getParameter('node_type')
        self.publish_dir = self.getParameter('publish_dir')

        self.variable_root_node = self.getChildByIndex(0)
        block_root_node_name = self.variable_root_node.getParameter('nodeReference.block_group').getValue(0)
        self.block_group = NodegraphAPI.GetNode(block_root_node_name)

    def cleanBlockRootNode(self, block_root_node):
        """
        Removes all everything on this node, returning it to a default state.

        TODO
            Needs to be modified to live group loading for block types...

        Args:
                block_root_node (Root Node): The node to restore
                    to a default state of a group node.
        """
        # delete parameters
        params = block_root_node.getParameters()
        for param in block_root_node.getParameters().getChildren():
            params.deleteChild(param)

        # delete children
        for child_node in block_root_node.getChildren():
            child_node.delete()

        # add node reference back
        params.createChildGroup('nodeReference')

        # create new temp block root node
        self.createBlockRootNode(self, 'master', block_root_node=self.variable_root_node)
        self.block_group = NodegraphAPI.GetNode(self.variable_root_node.getParameter('nodeReference.block_group').getValue(0))
        self.vs_node = NodegraphAPI.GetNode(self.variable_root_node.getParameter('nodeReference.vs_node').getValue(0))

    def _reset(self, variable='', node_type=''):
        """
        Deletes the entire inner working structure of this node, and resets
        the master root item.

        This has a hack in it to bypass the delete bug in Katana.  Which
        will keep the same root node... and modify it, rather than recreating
        the entire node hierarchy (which is what I want it to do...).

        Kwargs:
            variable (str): name of the new GSV that this node will be using
        """
        # clean up root node
        self.cleanBlockRootNode(self.variable_root_node)
        self.variable_root_node.getParameter('hash').setValue('master', 0)

        # set GSV
        self.variable = variable
        self.variable_param.setValue(self.variable, 0)
        self.node_type = node_type
        self.node_type_param.setValue(self.node_type, 0)

        # make directories
        publish_dir = self.getParameter('publish_dir').getValue(0)
        base_publish_dir = '{root_dir}/{variable}/{node_type}'.format(
            root_dir=publish_dir,
            variable=self.variable,
            node_type=self.node_type
        )

        mkdirRecursive(base_publish_dir + '/block')
        mkdirRecursive(base_publish_dir + '/pattern')

        # create internal node structure
        self.populateVariable(self.variable)

    # old less hacky method but doesn't work with the UndoStack..
    def _reset_old(self, variable=''):
        """
        Deletes the entire inner working structure of this node, and resets
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
        createNodeReference(self.variable_root_node, 'variable_root_node', node=self)
        createNodeReference(self.block_group, 'block_node', node=self)
        node_list.append(self.variable_root_node)
        Utils.EventModule.ProcessAllEvents()

        # wire nodes
        connectInsideGroup(node_list, self)

        # set GSV
        self.variable = variable

        # make directories
        publish_dir = self.getParameter('publish_dir').getValue(0)
        base_publish_dir = '{root_dir}/{variable}/{node_type}'.format(
            root_dir=publish_dir,
            variable=self.variable,
            node_type=self.node_type
        )

        mkdirRecursive(base_publish_dir + '/block')
        mkdirRecursive(base_publish_dir + '/pattern')

        self.variable_param.setValue(self.variable, 0)
        self.populateVariable(self.variable)

    def populateVariable(self, variable):
        """
        Creates all of the pattern groups on initialization
        """
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
                connectInsideGroup(node_list, self.block_group)

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
        # pre flight
        if node_type == '' or node_type == 'Group': return
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

    def createBlockRootNode(self, parent_node, name='block_01', block_root_node=None):
        """
        Creates a new block or container for holding patterns.

        This will create all of the nodes necessary and wire them into
        the parent node provided (block node).

        Args:
            parent_node (node): the node to create this new block under.
                This should be another block node.
            name (str):
                The name of this block
        Kwargs:
            block_root_node (Root Node): Container root node.  If this is provided
                then it will be used as the container node.  This will not clear the
                existing params/nodes of the existing container.  That will need to be
                done with cleanBlockRootNode()
        Returns (node):
            The new container node that has been created.
        """
        # Create Nodes
        if not block_root_node:
            block_root_node = self.createGroupNode(parent_node, name=name)
        block_root_node.getParameters().createChildString('type', 'root')
        pattern_group = self.createPatternGroupNode(block_root_node, pattern='master')
        block_group = self.createBlockGroupNode(block_root_node, name='block')
        block_group.getParameters().createChildString('type', 'block')
        vs_node = self.createVariableSwitch(block_root_node)

        # initialize default parameters
        unique_hash = self.__createHash(block_root_node.getName(), BLOCK_ITEM)
        add_params_node_list = [block_root_node, block_group]
        for node in add_params_node_list:
            params = node.getParameters()
            params.createChildString('version', 'v000')
            params.createChildString('hash', unique_hash)
            params.createChildString('expanded', 'False')
            params.createChildString('name', name)

        # create parameter node references
        group_params = block_root_node.getParameter('nodeReference')
        createNodeReference(pattern_group, 'pattern_node', param=group_params)
        createNodeReference(block_group, 'block_group', param=group_params)
        createNodeReference(vs_node, 'vs_node', param=group_params)
        param_name = '%s_%s' % (BLOCK_PREFIX, block_root_node.getName())
        createNodeReference(block_root_node, param_name, node=self)

        # create reference if parent is a block node...
        if parent_node != self:
            parent_node_type = parent_node.getParameter('type').getValue(0)
            if parent_node_type == 'block':
                block_string = '{block_prefix}{block_name}'.format(
                    block_prefix=BLOCK_PREFIX,
                    block_name=block_root_node.getName()
                )
                createNodeReference(block_root_node, block_string, param=parent_node.getParameter('nodeReference'))

        # wire node
        block_root_node.getInputPortByIndex(0).connect(parent_node.getSendPort('in'))
        block_root_node.getOutputPortByIndex(0).connect(parent_node.getReturnPort('out'))
        # connect
        connectInsideGroup([pattern_group, block_group, vs_node], block_root_node)
        block_root_node.getSendPort('in').connect(vs_node.getInputPortByIndex(0))

        # create directories
        self.__createPublishDirectories(unique_hash, BLOCK_ITEM)

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
        node_type = self.getParameter('node_type').getValue(0)
        pattern_string = '%s%s' % (PATTERN_PREFIX, pattern)
        # create the pattern root node
        if not name:
            name = pattern
        pattern_root_node = self.createGroupNode(parent_node, name=pattern_string)

        # create parameters

        # create reference to pattern
        parent_node_type = parent_node.getParameter('type').getValue(0)
        if parent_node_type == 'block':
            createNodeReference(pattern_root_node, pattern_string, param=parent_node.getParameter('nodeReference'))

        # create parameters
        unique_hash = '{variable}_{pattern}'.format(
            variable=variable, pattern=pattern
        )
        pattern_root_node.getParameters().createChildString('version', 'v000')
        pattern_root_node.getParameters().createChildString('hash', unique_hash)
        pattern_root_node.getParameters().createChildString('pattern', pattern)
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
        self.__createPublishDirectories(unique_hash, PATTERN_ITEM)

        # create child node
        self.createNodeOfType(veg_node)

        return pattern_root_node

    """ UTILS """
    def updateVariableRootNode(self):
        """
        Updates the variable root node attribute to the node parameter.
        """
        variable_root_node = NodegraphAPI.GetNode(self.getParameter('variable_root_node').getValue(0))
        self.variable_root_node = variable_root_node

    def __getPublishLoc(self, item_type):
        """
        Gets the current publish location as

        Attributes:
            item_type: Which publish directory to get BLOCK_ITEM or PATTERN_ITEM

        Returns (str):
            {root_location}/{variable}/{node_type}/{item_type}
        """
        if not self.getParameter('publish_dir'): return 'hopefullyyoudonthaveadirectorynamedthisonyoursystem'
        variable = self.getVariable()
        node_type = self.getNodeType()
        root_location = self.getParameter('publish_dir').getValue(0)

        if item_type == BLOCK_ITEM:
            location = '{root_location}/{variable}/{node_type}/block'.format(
                root_location=root_location, variable=variable, node_type=node_type
            )

        elif item_type in [MASTER_ITEM, PATTERN_ITEM]:
            location = '{root_location}/{variable}/{node_type}/pattern'.format(
                root_location=root_location, variable=variable, node_type=node_type
            )

        return location

    def __createHash(self, node_name, item_type):
        """
        Creates a unique hash based off of the nodes name

        Attributes:
            node_name (str): base string to create a hash from
            item_type: What type of item to create the hash for...
                This is not really necessary right now, as we are only
                hashing out the Blocks... however, in theory if you wanted
                to hash out the patterns this would support that aswell...
        """
        location = self.__getPublishLoc(item_type)
        if os.path.exists(location):
            unique_hash = createUniqueHash(hash(node_name), location)
        else:
            unique_hash = 'master'
        return str(unique_hash)

    def __createPublishDirectories(self, unique_hash, item_type):
        """
        creates all directories on disk to be used when
        a new item is created (pattern) returns the unique hash

        Args:
            unique_hash (str): The items current unique hash
            item_type (ITEM_TYPE): The item type whose
                directory should be created
        """
        # pre flight checks
        variable = self.getParameter('variable').getValue(0)
        node_type = self.getParameter('node_type').getValue(0)
        publish_dir = self.getParameter('publish_dir')
        if variable == '': return
        if node_type == '': return
        if publish_dir is None: return

        # create directories
        location = self.__getPublishLoc(item_type)
        publish_loc = '%s/%s' % (location, unique_hash)

        mkdirRecursive(publish_loc + '/pattern/live')
        mkdirRecursive(publish_loc + '/block/live')
        # mkdirRecursive(publish_loc + '/pattern/v000')
        # mkdirRecursive(publish_loc + '/block/v000')

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

    def getVariable(self):
        return self.getParameter('variable').getValue(0)

    def setVariable(self, variable):
        self.getParameter('variable').setValue(variable, 0)

    def getNodeType(self):
        return self.getParameter('node_type').getValue(0)

    def setNodeType(self, node_type):
        self.getParameter('node_type').setValue(node_type, 0)