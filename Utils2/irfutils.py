from Katana import NodegraphAPI, RenderManager, Utils


FILTER = "filter"
CATEGORY = "category"
IS_IRF = "is_irf"

def getAllRenderFilterContainers():
    return NodegraphAPI.GetAllNodesByType("InteractiveRenderFilters")


def getAllRenderFilterNodes():
    """ Returns a list of all the Render Filter nodes in the scene"""
    return NodegraphAPI.GetAllNodesByType("RenderFilter")


def getIRFDelegate():
    return RenderManager.InteractiveRenderDelegateManager.GetRenderFiltersDelegate()


def clearAllActiveFilters():
    irf_delegate = getIRFDelegate()
    irf_delegate.setActiveRenderFilterNodes([])


def getAllActiveFilters():
    """ Returns a list of all the active Render Filter nodes

    returns (list): of Render Filter Nodes"""
    return getIRFDelegate().getActiveRenderFilterNodes()


def enableRenderFilter(node, enable):
    """ Activates/deactivates the render filter provided

    Args:
        node (Render Filter): render filter node to activate"""
    if node.getType() != "RenderFilter": return

    irf_delegate = getIRFDelegate()
    active_filters = irf_delegate.getActiveRenderFilterNodes()

    # activate
    if enable:
        active_filters.append(node)
        irf_delegate.setActiveRenderFilterNodes(active_filters)

    # deactivate
    else:
        if node in active_filters:
            active_filters.remove(node)
            irf_delegate.setActiveRenderFilterNodes(active_filters)


def irfNodeParam():
    """ Returns the parameter which stores the default IRF Nodes name"""
    return NodegraphAPI.GetRootNode().getParameter("KatanaBebop.IRFNode")