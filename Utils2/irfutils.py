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


def setupDefaultIRFParam():
    from . import paramutils
    Utils.UndoStack.DisableCapture()
    paramutils.createParamAtLocation("KatanaBebop.IRFNode", NodegraphAPI.GetRootNode(), paramutils.STRING)
    Utils.UndoStack.EnableCapture()


def defaultIRFNode():
    if irfNodeParam():
        return NodegraphAPI.GetNode(irfNodeParam().getValue(0))
    return None


def setDefaultIRFNode(irf_node):
    """ Sets the default IRF node

    Args:
        irf_node (Node): Node that will be set as the default IRF node """
    setupDefaultIRFParam()
    irfNodeParam().setExpressionFlag(True)
    irfNodeParam().setExpression("@{irf_node_name}".format(irf_node_name=irf_node.getName()))

    for tab in getAllIRFTabs():
        irf_node_widget = tab.createWidget().irfNodeWidget()
        irf_node_widget.setText(irf_node.getName())

def getAllIRFTabs():
    """ Returns a list of all of the GSVViewWidgets"""
    from Katana import UI4

    widgets = []
    # update GUIs
    for tab in UI4.App.Tabs.GetTabsByType("IRF Manager"):
        widgets.append(tab)

    for tab in UI4.App.Tabs.GetTabsByType('Popup Bar Displays/KatanaBebop/State Manager'):
        popup_widgets = tab.popupBarDisplayWidget().allWidgets()

        for widget in popup_widgets:
            popup_widget = widget.popupWidget()
            if hasattr(popup_widget, "__name__"):
                if popup_widget.__name__() == "IRF Manager":
                    widgets.append(popup_widget)

    # todo custom handler for custom user popup bar widgets
    return widgets
