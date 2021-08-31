from Katana import Utils, Callbacks

def loadLocalEvents(*args):
    """
    Loads all of the events for all SimpleTools in the scene.
    """
    from Katana import NodegraphAPI, UI4, Utils, FormMaster
    # view all Simple Tools to register their event handlers (kinda hacky, but w/e)
    event_nodes = NodegraphAPI.GetAllNodesByType("SimpleTool")
    for node in event_nodes:
        node.installEvents()


def cleanupLocalEvents(*args, **kwargs):
    from Katana import NodegraphAPI, UI4, Utils, FormMaster
    event_nodes = NodegraphAPI.GetAllNodesByType("SimpleTool")
    for node in event_nodes:
        node.disableAllEvents()

def installSimpleTools():
    Callbacks.addCallback(Callbacks.Type.onSceneAboutToLoad, cleanupLocalEvents)
    Utils.EventModule.RegisterCollapsedHandler(loadLocalEvents, 'nodegraph_loadEnd')


