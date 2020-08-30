import os

from .ItemTypes import (
    BLOCK_ITEM,
    PATTERN_ITEM
)

from Widgets2 import (
    AbstractComboBox
)


# class VariableManagerComboBox(AbstractComboBox):
#     def __init__(self, parent=None):
#         super(VariableManagerComboBox, self).__init__(parent)
#
#     def checkBesterestVersion(self):
#         publish_dir = self.main_widget.getBasePublishDir(include_node_type=True)
#         for item_type in [PATTERN_ITEM, BLOCK_ITEM]:
#             publish_loc = '{publish_dir}/patterns/master/{item_type}/v000'.format(
#                 publish_dir=publish_dir, item_type=item_type.TYPE
#             )
#             # LOAD
#             if os.path.exists(publish_loc) is True:
#                 # Load besterest version
#                 self.main_widget.versions_display_widget.loadBesterestVersion(item_type=item_type)
#
#             # CREATE
#             else:
#                 # Publish
#                 self.main_widget.publish_display_widget.publishNewItem(
#                     item_type=item_type
#                 )


def checkBesterestVersion(main_widget, item=None):
    """
    Looks at an item and determines if there are versions available to load or not.
    If there are versions available, it will load the besterest version, if there are not
    versions available, it will create the new item.

    # currently only checks patterns
    # currently only checks master item...
    # add to block create in VaraiableManagerWidget
    """
    publish_dir = main_widget.getBasePublishDir(include_node_type=True)
    # if not item:
    #     item = main_widget.getWorkingItem()

    for item_type in [PATTERN_ITEM, BLOCK_ITEM]:
        publish_loc = '{publish_dir}/patterns/master/{item_type}/v000'.format(
            publish_dir=publish_dir, item_type=item_type.TYPE
        )
        # LOAD
        if os.path.exists(publish_loc) is True:
            # Load besterest version
            main_widget.versions_display_widget.loadBesterestVersion(item_type=item_type)

        # CREATE
        else:
            # Publish
            main_widget.publish_display_widget.publishNewItem(
                item_type=item_type
            )


def connectInsideGroup(node_list, parent_node):
    """
    Connects all of the nodes inside of a specific node in a linear fashion

    Args:
        node_list (list): list of nodes to be connected together, the order
            of the nodes in this list, will be the order that they are connected in
        parent_node (node): node have the nodes from the node_list
            wired into.
    """
    import NodegraphAPI
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


def convertStringBoolToBool(string_bool):
    """
    Converts a string boolean to a boolean

    Args:
        string_bool (str): string value of the boolean
            such as "True" or "False"

    Returns (bool)
    """
    if string_bool == "True":
        return True
    elif string_bool == "False":
        return False
    else:
        return False


def createNodeReference(node_ref, param_name, param=None, node=None, index=-1):
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


def disconnectNode(node, input=False, output=False):
    """
    Disconnects the node provide from all over nodes.  The same
    as hitting 'x' on the keyboard... or "Extract Nodes" except this
    is in the NodegraphWidget, not the NodegraphAPI. so kinda hard
    to call... so I made my own...

    Args:
        node (node): Node to be extracted
        input (bool): If true disconnect all input ports
        output (bool): If true disconnect all output ports

    """
    if input is True:
        for input_port in node.getInputPorts():
            output_ports = input_port.getConnectedPorts()
            for port in output_ports:
                port.disconnect(input_port)

    if output is True:
        for output in node.getOutputPorts():
            input_ports = output.getConnectedPorts()
            for port in input_ports:
                port.disconnect(output)


def mkdirRecursive(path):
    """
    Creates a directory and all parent directories leading
    to that directory.  This is not as necessary in Python 3.x+
    as you can do stuff like os.mkdirs.

    Args:
        path (str): directory to be created
    """
    sub_path = os.path.dirname(path)
    if not os.path.exists(sub_path):
        mkdirRecursive(sub_path)
    if not os.path.exists(path):
        os.mkdir(path)


def goToNode(node, frame=False, nodegraph_tab=None):
    """
    Changes the nodegraph to the selected items node,
    if it is not a group node, then it goes to its parent
    as the parent must be a group... (hopefully)

    Args:
        node (node): node to go to

    Kwargs:
        frame (bool): if True will frame all of the nodes inside of the "node" arg
        nodegraph_tab (nodegraph_panel): if exists, will frame in this node graph, if there is no
            node graph tab.  Then it will search for the default node graph.
    """
    from Katana import UI4
    if not nodegraph_tab:
        nodegraph_tab = UI4.App.Tabs.FindTopTab('Node Graph')
    nodegraph_tab._NodegraphPanel__navigationToolbarCallback(node.getName(), 'useless')

    if frame is True:
        nodegraph_widget = nodegraph_tab.getNodeGraphWidget()
        nodegraph_widget.frameNodes(nodegraph_tab.getEnteredGroupNode().getChildren())


def getNextVersion(location):
    """
    Args:
        location (str): path on disk to to publish dir

    return (str): A string of the next version with the format of v000
    """
    # if it dir doesn't exist return init version
    if not os.path.exists(location): return 'v000'

    # find version
    versions = os.listdir(location)
    if 'live' in versions:
        versions.remove('live')

    if len(versions) == 0:
        next_version = 'v000'
    else:
        versions = [int(version[1:]) for version in versions]
        next_version = 'v'+str(sorted(versions)[-1] + 1).zfill(3)

    return next_version


# HACK
def transferNodeReferences(xfer_from, xfer_to):
    """
    Transfer the node references from one node to another.

    xfer_from (param): the nodeReference param to transfer FROM
    xfer_to  (param): the nodeReference param to transfer TO

    """
    import NodegraphAPI
    # transfer node refs
    for param in xfer_from.getChildren():
        param_name = param.getName()
        node_ref = NodegraphAPI.GetNode(param.getValue(0))
        createNodeReference(
            node_ref, param_name, param=xfer_to
        )


def updateNodeName(node, name=None):
    """
    updates the nodes name.  If a name is provided
    then this will update it to that name.  If not, it will
    merely check to ensure that no funky digits have
    been automatically added to this nodes name...

    Kwarg:
        name (str): name to update to
    """
    # set name
    if name:
        node.setName(str(name))
        node.getParameter('name').setValue(str(name), 0)
    else:
        # update name
        node.setName(node.getName())
        node.getParameter('name').setValue(node.getName(), 0)

# TODO what have I done here...
'''from Katana import Utils
Utils.EventModule.RegisterEventHandler(updateNodeName, '_update_node_name')'''