from Katana import NodegraphAPI, RenderManager

class IRFUtils(object):
    FILTER = "filter"
    CATEGORY = "category"
    IS_IRF = "is_irf"

    @staticmethod
    def getAllRenderFilterContainers():
        return NodegraphAPI.GetAllNodesByType("InteractiveRenderFilters")

    @staticmethod
    def getAllRenderFilterNodes():
        """ Returns a list of all the Render Filter nodes in the scene"""
        return NodegraphAPI.GetAllNodesByType("RenderFilter")

    @staticmethod
    def getIRFDelegate():
        return RenderManager.InteractiveRenderDelegateManager.GetRenderFiltersDelegate()

    @staticmethod
    def getAllActiveFilters():
        """ Returns a list of all the active Render Filter nodes

        returns (list): of Render Filter Nodes"""
        return IRFUtils.getIRFDelegate().getActiveRenderFilterNodes()

    @staticmethod
    def enableRenderFilter(node, enable):
        """ Activates/deactivates the render filter provided

        Args:
            node (Render Filter): render filter node to activate"""
        if node.getType() != "RenderFilter": return

        irf_delegate = IRFUtils.getIRFDelegate()
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

    @staticmethod
    def irfNodeParam():
        """ Returns the parameter which stores the default IRF Nodes name"""
        return NodegraphAPI.GetRootNode().getParameter("KatanaBebop.IRFNode")