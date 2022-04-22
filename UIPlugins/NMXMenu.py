from Katana import NodegraphAPI, RenderingAPI, LayeredMenuAPI, UI4, Utils
from Utils2 import widgetutils


def NMXMenuPopulateCallback(layeredMenu):
    """
    The populate call back is given to the layeredMenu as an argument.  This
    function will determine what options are displayed to the user when the user
    displays the layered menu.
    """
    nmc_nodes = NodegraphAPI.GetAllNodesByType("NetworkMaterialCreate")
    for nmc_node in nmc_nodes:
        layeredMenu.addEntry(nmc_node, text=nmc_node.getName(), color=(128, 0, 128))

    nme_nodes = NodegraphAPI.GetAllNodesByType("NetworkMaterialEdit")
    for nme_node in nme_nodes:
        layeredMenu.addEntry(nme_node, text=nme_node.getName(), color=(0, 128, 128))


def NMXMenuActionCallback(node):
    """
    The ActionCallback is given to the LayeredMenu as an argument.  This function
    will determine what should happen when the user selects an option in the
    LayeredMenu.
    """
    widgetutils.katanaMainWindow()._is_recursive_layered_menu_event = True
    nodegraph_widget = widgetutils.getActiveNodegraphWidget()
    nodegraph_widget.setCurrentNodeView(node)
    return ""


nmx_menu = LayeredMenuAPI.LayeredMenu(
    NMXMenuPopulateCallback,
    NMXMenuActionCallback,
    'N',
    alwaysPopulate=True,
    onlyMatchWordStart=False
)