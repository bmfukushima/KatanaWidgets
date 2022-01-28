import math
#from cgwidgets.interface.AbstractUtilsInterfaceAPI import disconnectNode, connectInsideGroup
try:
    import NodegraphAPI
except ModuleNotFoundError:
    pass

def getNodeAndAllDescendants(node, node_list=None):
    """ Gets the node and all of the descendants inside of it

    Args:
        node (Node): to start searching from"""
    if not node_list:
        node_list = []

    node_list.append(node)
    if hasattr(node, "getChildren"):
        for child in node.getChildren():
            node_list += getNodeAndAllDescendants(child, node_list)
    return list(set(node_list))


def disconnectNode(node, input=False, output=False, reconnect=False):
    """
    Disconnects the node provide from all other nodes.  The same
    as hitting 'x' on the keyboard... or "Extract Nodes" except this
    is in the NodegraphWidget, not the NodegraphAPI. so kinda hard
    to call... so I made my own...

    Args:
        node (node): Node to be extracted
        input (bool): If true disconnect all input ports
        output (bool): If true disconnect all output ports
        reconnect (bool): If true, will rewire the node graphs input/output ports
            will only work if input and output are true
    """
    # disconnect node: Reconnection needs to be updated to handle more than the first ports
    if reconnect is True:
        if input is True and output is True:
            try:
                input_port = node.getInputPortByIndex(0)
                upstream_port = input_port.getConnectedPorts()[0]
                output_port = node.getOutputPortByIndex(0)
                downstream_port = output_port.getConnectedPorts()[0]

                if upstream_port and downstream_port:
                    # reconnect wire
                    upstream_port.connect(downstream_port)
            except IndexError:
                # can't find the .getConnectedPorts()
                pass

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


def connectInsideGroup(node_list, parent_node):
    """
    Connects all of the nodes inside of a specific node in a linear fashion

    # todo update this so the connections actually work correctly... node positioning is boned
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


def toggleTwoFacedNodeAppearance(node):
    display_mode_param = node.getParameter('display_mode')
    display_mode = display_mode_param.getValue(0)
    display_mode_param.setValue(math.fabs(display_mode - 1))


def isNodeDescendantOf(child, ancestor):
    """ Determines if the node is a descendant of another node.

    Args:
        child (node): to check to see if it is a descendant of
        ancestor (node): node to see if the child node is descended from"""
    parent = child.parent()
    if parent:
        if parent == ancestor:
            return True
        else:
            return isNodeDescendantOf(child, ancestor)
    else:
        return False


def isContainerNode(node):
    """ Determines if this node is a container node.  Such as a Group/GroupStack/etc

    Args:
        node (node)"""
    if hasattr(node, 'getChildren'):
        return True
    else:
        return False
    return False


def insertNode(node, parent_node):
    """
    Inserts the node in the correct position in the Nodegraph, and then
    wires the node into that position.

    Note:
        *   When this happens, the node has already been connected.. Thus the awesome -2
        *   Needs to have the "nodeReference" parameter

    Args:
        node (node): Current node to be inserted
        parent_node (node): The current nodes parent
    """
    # get previous port / position
    if len(parent_node.getChildren()) == 1:
        # previous port
        previous_port = parent_node.getSendPort('in')

        # position
        pos = (0, 0)
    else:
        # get previous node
        # node_references = parent_node.getParameter('nodeReference')
        # previous_node_name = node_references.getChildByIndex(node_references.getNumChildren() - 2)
        # previous_node = NodegraphAPI.GetNode(previous_node_name.getValue(0))
        #
        # # previous port
        # previous_port = previous_node.getOutputPortByIndex(0)
        #
        # # setup pos
        # current_pos = NodegraphAPI.GetNodePosition(previous_node)
        # xpos = current_pos[0]
        # ypos = current_pos[1] - 100
        # pos = (xpos, ypos)

        return_port_name = parent_node.getOutputPortByIndex(0).getName()
        return_port = parent_node.getReturnPort(return_port_name)
        if 0 < len(return_port.getConnectedPorts()):
            previous_port = return_port.getConnectedPorts()[0]
            previous_node = previous_port.getNode()

            # setup pos
            current_pos = NodegraphAPI.GetNodePosition(previous_node)
            xpos = current_pos[0]
            ypos = current_pos[1] - 100
            pos = (xpos, ypos)

        else:
            send_port_name = parent_node.getInputPortByIndex(0).getName()
            previous_port = parent_node.getSendPort(send_port_name)
            pos = (0, 0)

    # wire node
    previous_port.connect(node.getInputPortByIndex(0))
    node.getOutputPortByIndex(0).connect(parent_node.getReturnPort('out'))

    # position node
    NodegraphAPI.SetNodePosition(node, pos)


def createIOPorts(node, in_port=True, out_port=True, connect=True, force_create=True):
    """ Creates / connects the input ports
    Args:
        node:
        in_port:
        out_port:
        connect:
        force_create:

    Returns:

    """
    # create input ports
    if in_port is True:
        if force_create:
            node.addInputPort('in')
        else:
            if len(node.getInputPorts()) == 0:
                node.addInputPort('in')

    # create output ports
    if out_port is True:
        if force_create:
            node.addOutputPort('out')
        else:
            if len(node.getOutputPorts()) == 0:
                node.addOutputPort('out')

    # connect nodes internal structure
    if connect is True:
        if hasattr(node, "getChildren"):
            send_port_name = node.getInputPortByIndex(0).getName()
            return_port_name = node.getOutputPortByIndex(0).getName()
            node.getSendPort(send_port_name).connect(node.getReturnPort(return_port_name))


def goToNode(node, frame=False, nodegraph_panel=None, entered=False):
    """
    Changes the nodegraph to the selected items node,
    if it is not a group node, then it goes to its parent
    as the parent must be a group... (hopefully)

    Args:
        node (node): node to go to

    Kwargs:
        frame (bool): if True will frame all of the nodes inside of the "node" arg.
            Note that this is only valid when 'entered' is set to True
        nodegraph_panel (nodegraph_panel): if exists, will frame in this node graph, if there is no
            node graph tab.  Then it will search for the default node graph.
        entered (bool): determines if this should view the children of the node
    """
    from Katana import UI4
    if not nodegraph_panel:
        nodegraph_panel = UI4.App.Tabs.FindTopTab('Node Graph')


    nodegraph_widget = nodegraph_panel.getNodeGraphWidget()
    if entered:
        # Enter node
        nodegraph_panel._NodegraphPanel__navigationToolbarCallback(node.getName(), 'useless')
        if frame is True:
            # frame all children
            nodegraph_widget.frameNodes(nodegraph_panel.getEnteredGroupNode().getChildren())

    else:
        # deselect all nodes
        for selected_node in NodegraphAPI.GetAllSelectedNodes():
            NodegraphAPI.SetNodeSelected(selected_node, False)

        # select node provided
        NodegraphAPI.SetNodeSelected(node, True)
        root = node.getParent()

        # enter parent node
        nodegraph_panel._NodegraphPanel__navigationToolbarCallback(root.getName(), 'useless')

        # frame node provided
        nodegraph_panel.frameSelection(node)


def setNodeColor(node, color):
    """Sets the nodes color

    Args:
        node (node)
        color (0-1rgb)"""
    from Katana import DrawingModule, UI4
    DrawingModule.SetCustomNodeColor(node, color[0], color[1], color[2])
    UI4.App.Tabs.FindTopTab("Node Graph").update()


def removeNodeColor(node):
    from Katana import DrawingModule, UI4
    DrawingModule.RemoveCustomNodeColor(node)
    UI4.App.Tabs.FindTopTab("Node Graph").update()


def reconnectNode(node_to_be_replaced, replacement_node, input=True, output=True):
    """ Reconnects a node's input/output ports to a new node

    Args:
        node_to_be_replaced (Node): node to remove
        replacement_node (Node): node to insert
        input (bool): determines if the nodes input ports should be reconnected
        output (bool): determines if the nodes output ports should be reconnected
    """
    if input:
        for index, input_port in enumerate(node_to_be_replaced.getInputPorts()):
            connected_ports = input_port.getConnectedPorts()
            for connected_port in connected_ports:
                replacement_node.getInputPortByIndex(index).connect(connected_port)

    if output:
        for index, output_port in enumerate(node_to_be_replaced.getOutputPorts()):
            connected_ports = output_port.getConnectedPorts()
            for connected_port in connected_ports:
                replacement_node.getOutputPortByIndex(index).connect(connected_port)


def replaceNode(node_to_be_replaced, replacement_node, delete=True, place=True, input=True, output=True):
    """ Replaces the node with a new one

    Note:
        Both nodes must have the same amount of input ports, and the same number
        of output ports.

    Args:
        node_to_be_replaced (Node): node to remove
        replacement_node (Node): node to insert
        delete (bool): determines if the old node should be deleted
        place (bool): determines if the node should be placed over the old node
        input (bool): determines if the nodes input ports should be reconnected
        output (bool): determines if the nodes output ports should be reconnected

    """

    # disconnect ports
    reconnectNode(node_to_be_replaced, replacement_node, input=input, output=output)
    # for index, input_port in enumerate(node_to_be_replaced.getInputPorts()):
    #     connected_ports = input_port.getConnectedPorts()
    #     for connected_port in connected_ports:
    #         replacement_node.getInputPortByIndex(index).connect(connected_port)
    #
    # for index, output_port in enumerate(node_to_be_replaced.getOutputPorts()):
    #     connected_ports = output_port.getConnectedPorts()
    #     for connected_port in connected_ports:
    #         replacement_node.getOutputPortByIndex(index).connect(connected_port)

    # place node
    if place:
        pos = NodegraphAPI.GetNodePosition(node_to_be_replaced)
        NodegraphAPI.SetNodePosition(replacement_node, pos)

    # delete old node
    if delete:
        node_to_be_replaced.delete()