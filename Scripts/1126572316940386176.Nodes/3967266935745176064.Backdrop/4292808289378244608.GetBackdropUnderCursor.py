from Utils2.widgetutils import getNodegraphCursorPos

def getBackdropNodeUnderCursor():
    cursor_pos, root_node = getNodegraphCursorPos()
    if not cursor_pos: return None
    backdrop_nodes = NodegraphAPI.GetAllNodesByType("Backdrop")
    active_backdrop_nodes = [backdrop_node for backdrop_node in backdrop_nodes if backdrop_node.getParent() == root_node]

    depth = -10000
    active_backdrop_node = None
    for backdrop_node in active_backdrop_nodes:
        attrs = backdrop_node.getAttributes()
        # position test
        pos = NodegraphAPI.GetNodePosition(backdrop_node)
        width = attrs["ns_sizeX"]
        height = attrs["ns_sizeY"]
        left = pos[0] - (width * 0.5)
        top = pos[1] + (height * 0.5)
        right = pos[0] + (width * 0.5)
        bottom = pos[1] - (height * 0.5)

        # position test
        if left < cursor_pos.x() and cursor_pos.x() < right and bottom < cursor_pos.y() and cursor_pos.y() < top:
            # depth test
            if depth < attrs["ns_zDepth"]:
                active_backdrop_node = backdrop_node
                depth = attrs["ns_zDepth"]

    return active_backdrop_node


print(getBackdropNodeUnderCursor())