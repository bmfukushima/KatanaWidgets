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

def cleanupGlobalEvents(**kwargs):
    from Katana import NodegraphAPI, UI4

    # get attrs
    node = NodegraphAPI.GetRootNode()

    katana_main = UI4.App.MainWindow.GetMainWindow()
    events_data = node.getParameter("events_data")

    # create default parameter if needed
    if not events_data:
        node.getParameters().createChildString("events_data", "")

    # cleanup data
    if events_data:
        if hasattr(katana_main, "global_events_widget"):
            katana_main.global_events_widget.disableAllEvents(events_data.getValue(0))

def loadGlobalEvents(*args):
    from Katana import NodegraphAPI, UI4
    from Widgets2 import EventWidget

    katana_main = UI4.App.MainWindow.GetMainWindow()
    node = NodegraphAPI.GetRootNode()
    #

    # load global events
    if katana_main:
        # create Event Widget if needed
        if not node.getParameter("events_data"):
            node.getParameters().createChildString("events_data", "")
        if not hasattr(katana_main, "global_events_widget"):
            katana_main.global_events_widget = EventWidget(katana_main, node=node)

        katana_main.global_events_widget.main_node = node
        katana_main.global_events_widget.main_widget.clearModel()
        katana_main.global_events_widget.loadEventsDataFromJSON()

def installBebopGlobalEvents():
    Utils.EventModule.RegisterCollapsedHandler(loadLocalEvents, 'nodegraph_loadEnd')
    Utils.EventModule.RegisterCollapsedHandler(loadGlobalEvents, 'nodegraph_setRootNode')
    Callbacks.addCallback(Callbacks.Type.onSceneAboutToLoad, cleanupGlobalEvents)