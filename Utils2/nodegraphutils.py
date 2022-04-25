from qtpy.QtCore import QPoint

from Katana import NodegraphAPI, DrawingModule, Utils, KatanaPrefs

# backdrop_nodes = NodegraphAPI.GetAllNodesByType("Backdrop")
#
# pos, root_node = getNodegraphCursorPos()
# active_backdrop_nodes = [backdrop_node for backdrop_node in backdrop_nodes if backdrop_node.getParent() == root_node]
TOPRIGHT = 0
TOPLEFT = 1
BOTLEFT = 2
BOTRIGHT = 3

def getBackdropNodeUnderCursor():
    """ Returns the backdrop node under the cursor"""
    cursor_pos, root_node = getNodegraphCursorPos()
    if not cursor_pos: return None
    backdrop_nodes = NodegraphAPI.GetAllNodesByType("Backdrop")
    active_backdrop_nodes = [backdrop_node for backdrop_node in backdrop_nodes if backdrop_node.getParent() == root_node]

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
        if left < cursor_pos.x() and cursor_pos.x() < right and bottom < cursor_pos.y() and cursor_pos.y() < top:
            # depth test
            if "ns_zDepth" in attrs:
                if depth < attrs["ns_zDepth"]:
                    active_backdrop_node = backdrop_node
                    depth = attrs["ns_zDepth"]

    return active_backdrop_node


def getBackdropQuadrantSelected(backdrop_node):
    """ Takes a backdrop, and returns the quadrant that the user has clicked under

    Returns (Quadrant): TOPLEFT | TOPRIGHT | BOTLEFT | BOTRIGHT """
    cursor_pos, root_node = getNodegraphCursorPos()
    node_pos = NodegraphAPI.GetNodePosition(backdrop_node)
    attrs = backdrop_node.getAttributes()
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

    # check if cursor in backdrop
    if left < cursor_pos.x() and cursor_pos.x() < right and bottom < cursor_pos.y() and cursor_pos.y() < top:
        # Top Left
        if cursor_pos.x() < node_pos[0] and node_pos[1] < cursor_pos.y():
            return TOPLEFT

        # Bottom Left
        if cursor_pos.x() < node_pos[0] and cursor_pos.y() < node_pos[1]:
            return BOTLEFT

        # Top Right
        if node_pos[0] < cursor_pos.x() and node_pos[1] < cursor_pos.y():
            return TOPRIGHT

        # Bottom Right
        if node_pos[0] < cursor_pos.x() and cursor_pos.y() < node_pos[1]:
            return BOTRIGHT
    return None


def getBackdropChildren(backdrop_node):
    from .widgetutils import getActiveNodegraphWidget
    nodegraph_widget = getActiveNodegraphWidget()

    l, b, r, t = DrawingModule.nodeWorld_getBoundsOfListOfNodes([backdrop_node])
    children = nodegraph_widget.hitTestBox(
        (l, b),
        (r, t),
        viewNode=backdrop_node.getParent()
    )

    selected_nodes = [node for node in children if node is not None]

    return selected_nodes


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


def getNodegraphCursorPos():
    """ Gets the position of the cursor relative to the current cartesian system the mouse is over

    Returns (QPoint, Node)"""
    from .widgetutils import getActiveNodegraphWidget
    nodegraph_widget = getActiveNodegraphWidget()
    # get cursor position
    if not hasattr(nodegraph_widget, "getMousePos"): return
    cursor_pos = nodegraph_widget.getMousePos()
    group_node = nodegraph_widget.getGroupNodeUnderMouse()
    if not cursor_pos: return QPoint(0, 0), group_node

    world_pos = nodegraph_widget.mapFromQTLocalToWorld(cursor_pos.x(), cursor_pos.y())
    cursor_pos = QPoint(*nodegraph_widget.getPointAdjustedToGroupNodeSpace(group_node, world_pos))

    return cursor_pos, group_node


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