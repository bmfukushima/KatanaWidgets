import math
import NodegraphAPI, DrawingModule

from cgwidgets.utils import getWidgetUnderCursor
from qtpy.QtCore import QPoint

def dynamicInputPortNodes():
    """ Returns a list of nodes that can have additional ports added by the user"""
    return ["Merge", "VariableSwitch", "Switch"]

def getFocusedGroupNode(nodegraph_widget=None):
    """ Returns the group node currently under the cursor

    Args:
        nodegraph_widget (NodegraphWidget): if none provided, will get the one
            under the cursor
    """
    widget_under_cursor = getWidgetUnderCursor().__module__.split(".")[-1]
    if widget_under_cursor != "NodegraphWidget": return

    if not nodegraph_widget:
        nodegraph_widget = getWidgetUnderCursor()

    cursor_pos = nodegraph_widget.getMousePos()
    if not cursor_pos:
        cursor_pos = QPoint(0, 0)
    world_pos = nodegraph_widget.mapFromQTLocalToWorld(cursor_pos.x(), cursor_pos.y())

    return DrawingModule.nodeWorld_findGroupNodeOfClick(nodegraph_widget.getCurrentNodeView(), world_pos[0], world_pos[1], nodegraph_widget.getViewScale()[0])


def getClosestNode(has_input_ports=False, has_output_ports=False, include_dynamic_port_nodes=False, exclude_nodes=[], nodegraph_widget=None):
    """ Returns the closest node to the cursor

    # Todo need to make this work for entered group nodes

    Args:
        exclude_nodes (list): list of nodes to not include in the search
        has_input_ports (bool): determines if the node is required to have an input port
        has_output_ports (bool): determines if the node is required to have an output port
        include_dynamic_port_nodes (bool): Determines if nodes with no input ports, but the possibility of having
            them should be included
    """

    widget_under_cursor = getWidgetUnderCursor().__module__.split(".")[-1]
    if widget_under_cursor != "NodegraphWidget": return

    if not nodegraph_widget:
        nodegraph_widget = getWidgetUnderCursor()

    if getFocusedGroupNode() != nodegraph_widget.getCurrentNodeView():
        # populate node list
        node_list = getFocusedGroupNode().getChildren()
    else:
        node_list = nodegraph_widget.getCurrentNodeView().getChildren()

    if has_output_ports:
        node_list = [node for node in node_list if 0 < len(node.getOutputPorts())]

    if has_input_ports:
        _node_list = []
        for node in node_list:
            if 0 < len(node.getInputPorts()):
                _node_list.append(node)
            else:
                if include_dynamic_port_nodes:
                    if node.getType() in dynamicInputPortNodes():
                        _node_list.append(node)

        node_list = _node_list

    for node in exclude_nodes:
        if node in node_list:
            node_list.remove(node)

    # todo how to map this to the popup group
    cursor_pos = nodegraph_widget.getMousePos()
    if getFocusedGroupNode() != nodegraph_widget.getCurrentNodeView():
        #(self.layerStack().getCurrentNodeView(), self.__activeNode, delta[0], delta[1],
        cursor_pos = nodegraph_widget.mapFromQTLocalToWorld(cursor_pos.x(), cursor_pos.y())
        cursor_pos = DrawingModule.nodeWorld_mapFromWorldPositionToCurrentGroupWorldPosition(
             getFocusedGroupNode(), getFocusedGroupNode(), cursor_pos[0], cursor_pos[1], nodegraph_widget.getViewScale()[0])
        print(cursor_pos)
    print(cursor_pos)
    closest_node = None
    mag = None
    for node in node_list:
        # compare vector distance...
        node_pos = NodegraphAPI.GetNodePosition(node)
        node_pos = nodegraph_widget.mapFromWorldToQTLocal(node_pos[0], node_pos[1])
        x = node_pos[0] - cursor_pos.x()
        y = node_pos[1] - cursor_pos.y()
        new_mag = math.sqrt(x*x + y*y)
        if mag == None:
            mag = new_mag
            closest_node = node
        elif new_mag < mag:
            mag = new_mag
            closest_node = node

    return closest_node

node = getClosestNode()
print(node)
