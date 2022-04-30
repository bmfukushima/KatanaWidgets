""" When dealing with the nodegraph...

Node Graph is return as
    top left = 0, 0
    bottom right = 1, 1

View is returned as
    bottom left = 0,0
    top right = 1,1

world = nodegraph coordinates
    bottom left = 0,0
    top right = 1,1
local = Qt Local coordinates
    top left = 0, 0
    bottom right = 1, 1
window = view coordinates
    bottom left = 0,0
    top right = 1,1
"""



import math

from qtpy.QtCore import QPoint

from Katana import NodegraphAPI, DrawingModule, Utils, KatanaPrefs

from cgwidgets.utils import getWidgetUnderCursor

CENTER = 0
TOPRIGHT = 1
TOP = 2
TOPLEFT = 3
LEFT = 4
BOTLEFT = 5
BOT = 6
BOTRIGHT = 7
RIGHT = 8

UP = 2
DOWN = 6

FORWARD = 2
BACK = 6
HOME = 0

def clearNodeSelection():
    for node in NodegraphAPI.GetAllSelectedNodes():
        NodegraphAPI.SetNodeSelected(node, False)


def duplicateNodes(nodegraph_layer, nodes_to_duplicate=None):
    """ Duplicate selected nodes, or closest node to cursor

    Args:
        nodegraph_layer (NodeGraphLayer): Current layer of the Nodegraph.
            Most likely the NodeInteractionLayer
        """
    selected_nodes = NodegraphAPI.GetAllSelectedNodes()

    # check selected nodes
    if not nodes_to_duplicate:
        nodes_to_duplicate = [node for node in selected_nodes if not NodegraphAPI.IsNodeLockedByParents(node)]

    # no selected nodes, get closest node
    if not nodes_to_duplicate:
        if not getClosestNode(): return
        nodes_to_duplicate = [getClosestNode()]

    duplicated_nodes = NodegraphAPI.Util.DuplicateNodes(nodes_to_duplicate)
    selectNodes(duplicated_nodes, is_exclusive=True)

    if duplicated_nodes:
        nodegraph_layer.layerStack().parent().prepareFloatingLayerWithPasteBounds(duplicated_nodes)
        nodegraph_layer.layerStack().parent()._NodegraphPanel__nodegraphWidget.enableFloatingLayer()

#
def dynamicInputPortNodes():
    """ Returns a list of nodes that can have additional ports added by the user"""
    return ["Merge", "VariableSwitch", "Switch"]


def getActiveBackdropNodes():
    """ Returns all of the backdrop nodes that are children of the currently viewed node """
    cursor_pos, root_node = getNodegraphCursorPos()
    if not cursor_pos: return []
    backdrop_nodes = NodegraphAPI.GetAllNodesByType("Backdrop")
    active_backdrop_nodes = [backdrop_node for backdrop_node in backdrop_nodes if backdrop_node.getParent() == root_node]
    return list(set(active_backdrop_nodes))


def getAllUpstreamNodes(node):
    nodes = NodegraphAPI.Util.GetAllConnectedInputs([node])
    nodes = __checkBackdropNodes(nodes)
    nodes.insert(0, node)
    return nodes


def getAllUpstreamTerminalNodes(node, node_list=[]):
    """ Gets all nodes upstream of a specific node that have no input nodes

    Args:
        node (Node): node to search from

    Returns (list): of nodes with no inputs
    """
    children = node.getInputPorts()
    if 0 < len(children):
        for input_port in children:
            connected_ports = input_port.getConnectedPorts()
            for port in connected_ports:
                node = port.getNode()
                getAllUpstreamTerminalNodes(node, node_list=node_list)
                terminal = True
                for input_port in node.getInputPorts():
                    if 0 < len(input_port.getConnectedPorts()):
                        terminal = False
                if terminal is True:
                    node_list.append(node)

    return list(set(node_list))


def getAllDownstreamNodes(node):
    nodes = NodegraphAPI.Util.GetAllConnectedOutputs([node])
    nodes = __checkBackdropNodes(nodes)
    nodes.insert(0, node)
    return nodes


def getBackdropArea(backdrop_node):
    attrs = backdrop_node.getAttributes()
    try:
        width = attrs["ns_sizeX"]
        height = attrs["ns_sizeY"]
    except KeyError:
        width = 128
        height = 64

    return width * height


def getBackdropChildren(backdrop_node, include_backdrop=True):
    from .widgetutils import getActiveNodegraphWidget

    # get all children
    nodegraph_widget = getActiveNodegraphWidget()
    if not nodegraph_widget: return
    if not backdrop_node: return []
    root_node = nodegraph_widget.getGroupNodeUnderMouse()
    children = root_node.getChildren()
    l1, b1, r1, t1 = getNodeCorners(backdrop_node)

    # initialize backdrop children list
    backdrop_children = []
    if include_backdrop:
        backdrop_children.append(backdrop_node)

    # hit test children to backdrop area
    for child in children:
        l2, b2, r2, t2 = getNodeCorners(child)
        if l1 < l2 < r2 < r1 and b1 < b2 < t2 < t1:
            backdrop_children.append(child)

    return backdrop_children


def getBackdropNodesUnderCursor():
    """ Returns a list of all of the backdrop nodes under the cursor"""
    active_backdrop_nodes = getActiveBackdropNodes()
    cursor_pos, _ = getNodegraphCursorPos()
    backdrop_nodes = []
    for backdrop_node in active_backdrop_nodes:
        attrs = backdrop_node.getAttributes()
        # position test
        node_pos = NodegraphAPI.GetNodePosition(backdrop_node)

        """ Need to duck type this as the ns_sizeXY is not created until the user
        has resized the backdrop node"""
        try:
            width = attrs["ns_sizeX"]
            height = attrs["ns_sizeY"]
        except KeyError:
            width = 128
            height = 64
        left = node_pos[0] - (width * 0.5)
        top = node_pos[1] + (height * 0.5)
        right = node_pos[0] + (width * 0.5)
        bottom = node_pos[1] - (height * 0.5)

        # position test
        if left < cursor_pos.x() and cursor_pos.x() < right and bottom < cursor_pos.y() and cursor_pos.y() < top:
            backdrop_nodes.append(backdrop_node)

    return backdrop_nodes


def getBackdropNodeUnderCursor():
    """ Returns the backdrop node under the cursor"""
    active_backdrop_nodes = getActiveBackdropNodes()
    cursor_pos, _ = getNodegraphCursorPos()
    depth = -10000
    active_backdrop_node = None
    for backdrop_node in active_backdrop_nodes:
        attrs = backdrop_node.getAttributes()
        # position test
        node_pos = NodegraphAPI.GetNodePosition(backdrop_node)
        """ Need to duck type this as the ns_sizeXY is not created until the user
        has resized the backdrop node"""
        try:
            width = attrs["ns_sizeX"]
            height = attrs["ns_sizeY"]
        except KeyError:
            width = 128
            height = 64
        left = node_pos[0] - (width * 0.5)
        top = node_pos[1] + (height * 0.5)
        right = node_pos[0] + (width * 0.5)
        bottom = node_pos[1] - (height * 0.5)

        # position test
        if cursor_pos:
            if left < cursor_pos.x() and cursor_pos.x() < right and bottom < cursor_pos.y() and cursor_pos.y() < top:
                # depth test
                if "ns_zDepth" in attrs:
                    if depth < attrs["ns_zDepth"]:
                        active_backdrop_node = backdrop_node
                        depth = attrs["ns_zDepth"]

    return active_backdrop_node


def getBackdropQuadrantSelected(backdrop_node):
    """ Takes a backdrop, and returns the quadrant that the user has clicked under

    Assumes a standard cartesian coordinate plane where 1 is in the upper right (+, +)
    then rotates counter clockwise to put 4 in the bottom right (+, -)
    1 = + +
    2 = - +
    3 = - -
    4 = + -

    Returns (Quadrant): TOPLEFT | TOPRIGHT | BOTLEFT | BOTRIGHT """
    cursor_pos, root_node = getNodegraphCursorPos()
    node_pos = NodegraphAPI.GetNodePosition(backdrop_node)
    attrs = backdrop_node.getAttributes()

    # Calculate boundaries
    """ Need to duck type this as the ns_sizeXY is not created until the user
    has resized the backdrop node
    """
    try:
        width = attrs["ns_sizeX"]
        height = attrs["ns_sizeY"]
    except KeyError:
        width = 128
        height = 64

    """ Calculate positions, the points are based off the standard cartesian
    system, where 0 is in the upper right, and 3 is in the bottom right"""
    left = node_pos[0] - (width * 0.5)
    top = node_pos[1] + (height * 0.5)
    right = node_pos[0] + (width * 0.5)
    bottom = node_pos[1] - (height * 0.5)
    width_offset = width / 3
    height_offset = height / 3
    point_00 = QPoint(right - width_offset, top - height_offset)
    point_01 = QPoint(left + width_offset, top - height_offset)
    point_02 = QPoint(left + width_offset, bottom + height_offset)
    point_03 = QPoint(right - width_offset, bottom + height_offset)
    # check if cursor in backdrop
    if left < cursor_pos.x() and cursor_pos.x() < right and bottom < cursor_pos.y() and cursor_pos.y() < top:

        # Top Right
        if point_00.x() < cursor_pos.x() and point_00.y() < cursor_pos.y():
            return TOPRIGHT

        # Top
        elif point_01.x() < cursor_pos.x() and cursor_pos.x() < point_00.x() and point_00.y() < cursor_pos.y():
            return TOP

        # Top Left
        elif cursor_pos.x() < point_01.x() and point_00.y() < cursor_pos.y():
            return TOPLEFT

        # Left
        elif cursor_pos.x() < point_01.x() and cursor_pos.y() < point_00.y() and point_02.y() < cursor_pos.y():
            return LEFT

        # Bottom Left
        elif cursor_pos.x() < point_02.x() and cursor_pos.y() < point_02.y():
            return BOTLEFT

        # Bottom
        elif point_02.x() < cursor_pos.x() and cursor_pos.x() < point_03.x() and cursor_pos.y() < point_02.y():
            return BOT

        # Bottom Right
        elif point_03.x() < cursor_pos.x() and cursor_pos.y() < point_02.y():
            return BOTRIGHT

        # Right
        elif point_00.x() < cursor_pos.x() and cursor_pos.y() < point_00.y() and point_02.y() < cursor_pos.y():
            return RIGHT

        else:
            return CENTER

    return None


def getClosestNode(has_input_ports=False, has_output_ports=False, include_dynamic_port_nodes=False, exclude_nodes=[]):
    """ Returns the closest node to the cursor

    # Todo need to make this work for entered group nodes

    Args:
        exclude_nodes (list): list of nodes to not include in the search
        has_input_ports (bool): determines if the node is required to have an input port
        has_output_ports (bool): determines if the node is required to have an output port
        include_dynamic_port_nodes (bool): Determines if nodes with no input ports, but the possibility of having
            them should be included
    """
    from .widgetutils import getActiveNodegraphWidget

    nodegraph_widget = getActiveNodegraphWidget()
    if not nodegraph_widget: return
    if not hasattr(nodegraph_widget, "getGroupNodeUnderMouse"): return

    # populate node list
    node_list = [node for node in nodegraph_widget.getGroupNodeUnderMouse().getChildren() if node.getType() != "Backdrop"]

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

        # update node list
        if has_output_ports:
            node_list += _node_list
        else:
            node_list = _node_list

    for node in exclude_nodes:
        if node in node_list:
            node_list.remove(node)

    # get cursor position
    cursor_pos = nodegraph_widget.getMousePos()
    if not cursor_pos: return
    group_node = nodegraph_widget.getGroupNodeUnderMouse()
    world_pos = nodegraph_widget.mapFromQTLocalToWorld(cursor_pos.x(), cursor_pos.y())
    cursor_pos = QPoint(*nodegraph_widget.getPointAdjustedToGroupNodeSpace(group_node, world_pos))

    closest_node = None
    mag = None
    for node in node_list:
        # compare vector distance...
        node_pos = NodegraphAPI.GetNodePosition(node)
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


def setCurrentKeyPressed(key):
    from .widgetutils import katanaMainWindow
    katanaMainWindow()._nodegraph_key_press = key


def getCurrentKeyPressed():
    from .widgetutils import katanaMainWindow
    return katanaMainWindow()._nodegraph_key_press


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


def getBackdropIntersectionAmount(backdrop1, backdrop2):
    """ Returns the intersection amount of two rectangles

    Assuming they are a list of (left, bottom, right, top)

    """
    dx = min(backdrop1[2], backdrop2[2]) - max(backdrop1[0], backdrop2[0])
    dy = min(backdrop1[3], backdrop2[3]) - max(backdrop1[1], backdrop2[1])
    if (dx >= 0) and (dy >= 0):
        return dx * dy
    return None


def getIntersectingBackdropNodes(backdrop_node):
    """ Gets all of the backdrop nodes intersecting with node provided

    Args:
        backdrop_node (Node): backdrop node to check intersections against

    Returns (list): of backdrop nodes intersecting the current one
    """
    # def doesBackdropIntersect(R1, R2):
    #     if (R1[0]>=R2[2]) or (R1[2]<=R2[0]) or (R1[3]<=R2[1]) or (R1[1]>=R2[3]):
    #         return False
    #     else:
    #         return True

    orig_backdrop_node = getNodeCorners(backdrop_node)
    backdrop_nodes = getActiveBackdropNodes()
    intersecting_backdrop_nodes = []
    for node in backdrop_nodes:
        backdrop_to_check = getNodeCorners(node)
        if getBackdropIntersectionAmount(orig_backdrop_node, backdrop_to_check):
            intersecting_backdrop_nodes.append(node)

    return intersecting_backdrop_nodes


def getNearestGridPoint(x, y):
    """
    @return: returns an offset of grid units (x, y)
    @x: <float> or <int>
    @y: <float> or <int>

    This should be in the Nodegraph Coordinate System,
    use self.mapToNodegraph() to convert to this sytem
    """
    # pos = NodegraphAPI.GetNodePosition(node)
    from MonkeyPatches.Nodegraph.gridLayer import GRID_SIZE_X_PREF_NAME, GRID_SIZE_Y_PREF_NAME
    grid_x_size = KatanaPrefs[GRID_SIZE_X_PREF_NAME]
    grid_y_size = KatanaPrefs[GRID_SIZE_Y_PREF_NAME]
    x = int(x)
    y = int(y)
    if x % grid_x_size > (grid_x_size * .5):
        x_offset = (x // grid_x_size) + 1
    else:
        x_offset = (x // grid_x_size)
    if y % grid_y_size > (grid_y_size * .5):
        y_offset = (y // grid_y_size) + 1
    else:
        y_offset = (y // grid_y_size)
    return QPoint(x_offset * grid_x_size, y_offset * grid_y_size)


def getNodeCorners(node):
    """ Returns the 4 corners of the backdrop node provided

    Returns (float, float, float, float): left, bottom, right, top"""
    if not node: return 0, 0, 0, 0
    # Is backdrop
    if node.getType() == "Backdrop":
        attrs = node.getAttributes()
        node_pos = NodegraphAPI.GetNodePosition(node)
        try:
            width = attrs["ns_sizeX"]
            height = attrs["ns_sizeY"]
        except KeyError:
            width = 128
            height = 64

        """ Calculate positions, the points are based off the standard cartesian
        system, where 0 is in the upper right, and 3 is in the bottom right"""
        left = node_pos[0] - (width * 0.5)
        top = node_pos[1] + (height * 0.5)
        right = node_pos[0] + (width * 0.5)
        bottom = node_pos[1] - (height * 0.5)
    else:
        left, bottom, right, top = DrawingModule.nodeWorld_getBoundsOfListOfNodes([node], addPadding=False)
    return left, bottom, right, top


def getNodegraphCursorPos():
    """ Gets the position of the cursor relative to the current cartesian system the mouse is over

    Returns (QPoint, Node)"""
    from .widgetutils import getActiveNodegraphWidget
    nodegraph_widget = getActiveNodegraphWidget()
    # get cursor position
    if not hasattr(nodegraph_widget, "getMousePos"): return None, None
    cursor_pos = nodegraph_widget.getMousePos()
    group_node = nodegraph_widget.getGroupNodeUnderMouse()
    if not cursor_pos: return QPoint(0, 0), group_node

    world_pos = nodegraph_widget.mapFromQTLocalToWorld(cursor_pos.x(), cursor_pos.y())
    cursor_pos = QPoint(*nodegraph_widget.getPointAdjustedToGroupNodeSpace(group_node, world_pos))

    return cursor_pos, group_node


def getTreeRootNode(node):
    """ Returns the Root Node of this specific Nodegraph Tree aka the upper left node

    Args:
        node (Node): node to start searching from
    """

    def getFirstNode(input_ports):
        """
        gets the first node connected to a node...
        @ports <port> getConnectedPorts()
        """
        for input_port in input_ports:
            connected_ports = input_port.getConnectedPorts()
            if len(connected_ports) > 0:
                for port in connected_ports:
                    node = port.getNode()
                    if node:
                        return node

        return None

    input_ports = node.getInputPorts()
    if len(input_ports) > 0:
        # get first node
        first_node = getFirstNode(input_ports)
        if first_node:
            return getTreeRootNode(first_node)
        else:
            return node
    else:
        return node


def floatNodes(node_list):
    """ Floats the nodes in the list provided

    Args:
        node_list (list): of nodes to be floated
    """
    from .widgetutils import getActiveNodegraphWidget
    nodegraph_widget = getActiveNodegraphWidget()
    nodegraph_widget.parent().floatNodes(list(node_list))


def interpolatePoints(p0, p1):
    """ creates a list of points between the two points provided

    This assumes the topleft is 0,0
    and the bottom right is 1,1

    # todo add a radius?
    Args:
        p0 (QPoint):
        p1 (QPoint):

    Returns (list): of QPoints
    """
    if p0 == p1: return [p0]

    step_size = 1

    x_offset = math.fabs(math.fabs(p1.x()) - math.fabs(p0.x()))
    y_offset = math.fabs(math.fabs(p1.y()) - math.fabs(p0.y()))
    num_steps = int(max(x_offset, y_offset) // step_size) + 1

    # determine the offset per step
    if y_offset < x_offset:
        y_offset_per_step = y_offset / (num_steps - 1)
        x_offset_per_step = step_size
    else:
        y_offset_per_step = step_size
        x_offset_per_step = x_offset / (num_steps - 1)

    # determine which way the step should go depending on the point order
    if 0 < p0.x() - p1.x():
        x_offset_per_step *= -1
    if 0 < p0.y() - p1.y():
        y_offset_per_step *= -1

    points = []
    for i in range(num_steps):
        points.append(QPoint(
            p0.x() + x_offset_per_step * i,
            p0.y() + y_offset_per_step * i)
        )

    return points


def nodeClicked(nodegraph_widget):
    """ Determines if the user has clicked on a node in the nodegraph"""
    # Bypass if user has clicked on a node
    mouse_pos = nodegraph_widget.mapFromQTLocalToWorld(nodegraph_widget.getMousePos().x(), nodegraph_widget.getMousePos().y())
    hits = nodegraph_widget.hitTestPoint(mouse_pos)
    for hit in hits:
        for node in hit[1].values():
            if node.getType() != "Backdrop":
                return True

    return False


def pointsHitTestNode(point_list, nodegraph_widget=None):
    """ Takes a list of points, and creates a hit test of them

    list(
        tuple("TYPE", {"type": object})
    )
    Args:
        point_list:

    Returns (list): of nodes

    """
    from .widgetutils import getActiveNodegraphWidget
    if not nodegraph_widget:
        nodegraph_widget = getActiveNodegraphWidget()

    hit_list = set()
    for point in point_list:
        hit_pos = nodegraph_widget.mapFromQTLocalToWorld(point.x(), point.y())
        hits = nodegraph_widget.hitTestPoint(hit_pos)

        for hit in hits:
            if hit[0] == "NODE":
                node = hit[1]["node"]
                if node.getType() != "Backdrop":
                    hit_list.add(node)

    return hit_list


def selectAllNodes(upstream=False, downstream=False):
    from .nodegraphutils import floatNodes
    node_list = []
    for node in NodegraphAPI.GetAllSelectedNodes():
        if downstream is True:
            node_list += getAllDownstreamNodes(node)
        if upstream is True:
            node_list += getAllUpstreamNodes(node)
    NodegraphAPI.SetAllSelectedNodes(node_list)
    floatNodes(node_list)


def selectNodes(node_list, is_exclusive=False):
    """ Select all of the nodes in the list provided

    Args:
        node_list (list): of nodes to select
        is_exclusive (bool): determines if these nodes should be exclusive, or appended to
            the current selection

    """
    if is_exclusive:
        clearNodeSelection()

    for node in node_list:
        NodegraphAPI.SetNodeSelected(node, True)


def updateBackdropDisplay(node, attrs=None):
    """ Hacky method to refresh a backdrop nodes by selecting/unselecting it

    Args:
        attrs (dict): of ns attrs for the backdrop, if none are provided,
            this will merely do an update
        node (node):

    """
    if node.getType() == "Backdrop":
        if attrs:
            NodegraphAPI.SetNodeShapeNodeAttrs(node, attrs)

        Utils.EventModule.QueueEvent('node_setShapeAttributes', hash(node), node=node)


        NodegraphAPI.SetNodeSelected(node, True)
        NodegraphAPI.SetNodeSelected(node, False)


def getCursorTrajectory(p0, p1):
    """ Gets the current trajectory of the cursor

    Args:
        p0 (QPoint)
        p1 (QPoint)
    stores the last time/pos coordinates of the mouse move
    prior to it hitting the first node.
    """

    _cursor_trajectory = RIGHT
    y_offset = p0.y() - p1.y()
    x_offset = p0.x() - p1.x()
    # cursor travelling left/right
    if math.fabs(y_offset) < math.fabs(x_offset):
        if x_offset < 0:
            _cursor_trajectory = RIGHT
        elif 0 < x_offset:
            _cursor_trajectory = LEFT

    # cursor travelling up/down
    if math.fabs(x_offset) < math.fabs(y_offset):
        if y_offset < 0:
            _cursor_trajectory = DOWN
        elif 0 < y_offset:
            _cursor_trajectory = UP

    return _cursor_trajectory


def __checkBackdropNodes(nodes):
    """ Checks the nodes list for any background nodes whose children are in the list

    Arg:
        nodes (list): of nodes to see if any backdrop nodes children are in
    """
    backdrop_nodes = getActiveBackdropNodes()
    for backdrop_node in backdrop_nodes:
        children = [node for node in getBackdropChildren(backdrop_node) if node.getType() != "Backdrop"]
        if len(children) == 0: continue

        is_valid = True
        if backdrop_node in nodes: continue
        for child in children:
            if child not in nodes:
                is_valid = False
                break
        if is_valid:
            nodes.insert(0, backdrop_node)

    return nodes


