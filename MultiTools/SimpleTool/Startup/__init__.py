from Katana import Utils, Callbacks

def loadLocalEvents(*args):
    """
    Loads all of the events for all SimpleTools in the scene.
    """
    from Katana import NodegraphAPI, UI4
    # get attrs
    current_nodes = NodegraphAPI.GetAllEditedNodes()
    node = None

    # view all Simple Tools to register their event handlers (kinda hacky, but w/e)
    event_nodes = NodegraphAPI.GetAllNodesByType("SimpleTool")
    for node in event_nodes:
        NodegraphAPI.SetNodeEdited(node, True, exclusive=False)

    # deselect last node
    if node:
        NodegraphAPI.SetNodeEdited(node, False, exclusive=False)

    # reset view state on nodes
    for node in current_nodes:
        NodegraphAPI.SetNodeEdited(node, True, exclusive=False)


def installSimpleTools():
    Utils.EventModule.RegisterCollapsedHandler(loadLocalEvents, 'nodegraph_loadEnd')