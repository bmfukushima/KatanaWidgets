from Katana import UI4, NodegraphAPI, DrawingModule, NodeGraphView, Utils, KatanaPrefs

from Utils2 import widgetutils, nodegraphutils


""" ALIGNMENT """
class AlignUtils(object):
    def __init__(self):
        from MonkeyPatches.Nodegraph.Layers.gridLayer import (
            GRID_SIZE_X_PREF_NAME, GRID_SIZE_Y_PREF_NAME, ALIGN_X_OFFSET_PREF_NAME, ALIGN_Y_OFFSET_PREF_NAME)

        self._grid_size_x = KatanaPrefs[GRID_SIZE_X_PREF_NAME]
        self._grid_size_y = KatanaPrefs[GRID_SIZE_Y_PREF_NAME]

        # number of grid units to offset by
        GRID_SPACE_X = KatanaPrefs[ALIGN_X_OFFSET_PREF_NAME]
        GRID_SPACE_Y = KatanaPrefs[ALIGN_Y_OFFSET_PREF_NAME]

        self._grid_offset_x = self._grid_size_x * GRID_SPACE_X
        self._grid_offset_y = (self._grid_size_y * GRID_SPACE_Y) * -1

    def alignAllNodes(self, x=0, y=0):
        """ Algorithm to align all of the nodes in the tree selected

        Args:
            x (int): How many grid units the node should be offset
            y (int): How many grid units the node should be offset
        """
        from .nodegraphutils import floatNodes
        Utils.UndoStack.OpenGroup("Align Nodes")
        self._aligned_nodes = []
        if len(NodegraphAPI.GetAllSelectedNodes()) == 0: return
        node = NodegraphAPI.GetAllSelectedNodes()[0]
        root_node = nodegraphutils.getTreeRootNode(node)

        # if x and y:
        NodegraphAPI.SetNodePosition(root_node, (x * self._grid_offset_x, y * self._grid_offset_y))
        self._aligned_nodes.append(root_node)
        # for terminal_node in terminal_nodes:
        self.__alignDownstreamNodes(root_node, x, y, recursive=True)
        Utils.UndoStack.CloseGroup()

        floatNodes(self._aligned_nodes)

    def alignDownstreamNodes(self):
        from .nodegraphutils import getNearestGridPoint, floatNodes

        Utils.UndoStack.OpenGroup("Align Nodes")
        self._aligned_nodes = []
        selected_nodes = NodegraphAPI.GetAllSelectedNodes()
        for selected_node in selected_nodes:
            pos = NodegraphAPI.GetNodePosition(selected_node)
            offset = getNearestGridPoint(pos[0], pos[1])
            xpos = (offset.x()) + self._grid_size_x
            ypos = (offset.y()) + self._grid_size_y

            NodegraphAPI.SetNodePosition(selected_node, (xpos, ypos))
            self._aligned_nodes.append(selected_node)
            self.__alignDownstreamNodes(selected_node, x=0, y=0)

            # offset all nodes back to a relative position of the original node...
            """ Would be smarter to just move the original node to the right position"""
            for node in list(set(self._aligned_nodes)):
                if node != selected_node:
                    orig_pos = NodegraphAPI.GetNodePosition(node)

                    offset_xpos = orig_pos[0] + xpos
                    offset_ypos = orig_pos[1] + ypos

                    NodegraphAPI.SetNodePosition(node, (offset_xpos, offset_ypos))

        Utils.UndoStack.CloseGroup()

        nodegraph_widget = widgetutils.getActiveNodegraphWidget()
        floatNodes(self._aligned_nodes)

    def __alignDownstreamNodes(self, node, x=0, y=0, recursive=False):
        """ Algorithm to align all of the nodes in the tree selected

        Args:
            node (Node): Node currently being looked at
            x (int): How many grid units the node should be offset
            y (int): How many grid units the node should be offset
        """
        output_ports = node.getOutputPorts()
        y += 1
        for count, output_port in enumerate(output_ports):
            if 0 < count:
                x += 1
            connected_ports = output_port.getConnectedPorts()

            for index, input_port in enumerate(connected_ports):
                connected_node = input_port.getNode()
                if connected_node not in self._aligned_nodes:
                    # if there is only one port, set the position and continue
                    """ This needs to be done as when there are multiple connected ports, these show
                    up as an unordered list.  Which means it is hard to sort, so we defer the sorting
                    to later """
                    if 0 < index:
                        x += 1

                    # set position
                    if recursive:
                        if len(connected_ports) == 1:
                            NodegraphAPI.SetNodePosition(connected_node, (self._grid_offset_x * x, self._grid_offset_y * y))
                            self._aligned_nodes.append(connected_node)
                    else:
                        NodegraphAPI.SetNodePosition(connected_node, (self._grid_offset_x * x, self._grid_offset_y * y))
                        self._aligned_nodes.append(connected_node)

                    # recurse through nodes
                    self.__alignDownstreamNodes(connected_node, x=x, y=y, recursive=recursive)

                    # check upstream
                    if recursive:
                        input_ports = connected_node.getInputPorts()
                        if 1 < len(input_ports):
                            for input_port in input_ports[1:]:
                                sibling_node = input_port.getNode()
                                self.__alignUpstreamNodes(sibling_node, x=x, y=y, recursive=recursive)

    def alignUpstreamNodes(self):
        from .nodegraphutils import getNearestGridPoint, floatNodes

        Utils.UndoStack.OpenGroup("Align Nodes")
        self._aligned_nodes = []
        selected_nodes = NodegraphAPI.GetAllSelectedNodes()
        for selected_node in selected_nodes:
            pos = NodegraphAPI.GetNodePosition(selected_node)
            offset = getNearestGridPoint(pos[0], pos[1])
            xpos = (offset.x()) + self._grid_size_x
            ypos = (offset.y()) + self._grid_size_y

            NodegraphAPI.SetNodePosition(selected_node, (xpos, ypos))
            self._aligned_nodes.append(selected_node)
            self.__alignUpstreamNodes(selected_node)
            for node in list(set(self._aligned_nodes)):
                if node != selected_node:
                    orig_pos = NodegraphAPI.GetNodePosition(node)

                    offset_xpos = orig_pos[0] + xpos
                    offset_ypos = orig_pos[1] + ypos

                    NodegraphAPI.SetNodePosition(node, (offset_xpos, offset_ypos))
        Utils.UndoStack.CloseGroup()

        floatNodes(self._aligned_nodes)

    def __alignUpstreamNodes(self, node, x=0, y=0, recursive=False):
        """ Algorithm to align all of the nodes in the tree selected

        Args:
            node (Node): Node currently being looked at
            x (int): How many grid units the node should be offset
            y (int): How many grid units the node should be offset
        """
        input_ports = node.getInputPorts()
        y -= 1
        for count, input_port in enumerate(input_ports):
            if 0 < count:
                x += 1
            connected_ports = input_port.getConnectedPorts()

            for index, output_port in enumerate(connected_ports):
                connected_node = output_port.getNode()
                if 0 < index:
                    x += 1
                if connected_node not in self._aligned_nodes:
                    # if there is only one port, set the position and continue
                    """ This needs to be done as when there are multiple connected ports, these show
                    up as an unordered list.  Which means it is hard to sort, so we defer the sorting
                    to later """
                    if recursive:
                        if len(connected_ports) == 1:
                            NodegraphAPI.SetNodePosition(connected_node, (self._grid_offset_x * x, self._grid_offset_y * y))
                            self._aligned_nodes.append(connected_node)
                    else:
                        NodegraphAPI.SetNodePosition(connected_node, (self._grid_offset_x * x, self._grid_offset_y * y))
                        self._aligned_nodes.append(connected_node)
                    # recurse through nodes
                    self.__alignUpstreamNodes(connected_node, x=x, y=y, recursive=recursive)

                    # check upstream
                    if recursive:
                        output_ports = connected_node.getOutputPorts()
                        if 1 < len(output_ports):
                            for output_port in output_ports[1:]:
                                sibling_node = output_port.getNode()
                                self.__alignDownstreamNodes(sibling_node, x=x, y=y, recursive=recursive)

    """ SNAP TO GRID """
    def snapNodeToGrid(self, node):
        """ Snaps the node provided to the nearest point on the grid"""
        pos = NodegraphAPI.GetNodePosition(node)

        if pos[0] % self._grid_size_x < 0.5 * self._grid_size_x:
            x = self._grid_size_x * (pos[0] // self._grid_size_x)
        else:
            x = self._grid_size_x * ((pos[0] // self._grid_size_x) + 1)

        if pos[1] % self._grid_size_y < 0.5 * self._grid_size_y:
            y = self._grid_size_y * (pos[1] // self._grid_size_y)
        else:
            y = self._grid_size_y * ((pos[1] // self._grid_size_y) + 1)

        NodegraphAPI.SetNodePosition(node, (x, y))

    def snapNodesToGrid(self, node_list=None):
        """ Snaps the nodes provided to the grid

        Args:
            node_list (list): of nodes to be snapped to the grid
                If none is provided, it will use the currently selected nodes
        """
        from .nodegraphutils import getNearestGridPoint

        Utils.UndoStack.OpenGroup("Snap Nodes to Grid")
        if not node_list:
            node_list = NodegraphAPI.GetAllSelectedNodes()
        for node in node_list:
            pos = NodegraphAPI.GetNodePosition(node)
            offset = getNearestGridPoint(pos[0], pos[1])
            NodegraphAPI.SetNodePosition(node, ((offset.x()) + self._grid_size_x, (offset.y()) + self._grid_size_y))
        Utils.UndoStack.CloseGroup()

