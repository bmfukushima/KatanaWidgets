from Katana import Utils, Callbacks

# copy/paste
_param_location = "KatanaBebop.GlobalEventsData.data"

def cleanupGlobalEvents(**kwargs):
    """ Destroys all global events"""
    from Katana import NodegraphAPI, UI4

    # get attrs
    node = NodegraphAPI.GetRootNode()

    katana_main = UI4.App.MainWindow.GetMainWindow()
    events_data = node.getParameter(_param_location)

    # create default parameter if needed
    if not events_data:
        node.getParameters().createChildString(_param_location, "")

    # cleanup data
    if events_data:
        if hasattr(katana_main, "global_events_widget"):
            katana_main.global_events_widget.disableAllEvents(events_data.getValue(0))


def loadGlobalEvents(*args):
    """ Loads all global events"""
    from Katana import NodegraphAPI, UI4
    from Widgets2 import EventWidget

    katana_main = UI4.App.MainWindow.GetMainWindow()
    node = NodegraphAPI.GetRootNode()
    #

    # load global events
    if katana_main:
        # create Event Widget if needed
        if not node.getParameter(_param_location):
            node.getParameters().createChildString(_param_location, "")
        if not hasattr(katana_main, "global_events_widget"):
            katana_main.global_events_widget = EventWidget(katana_main, node=node)

        katana_main.global_events_widget.main_node = node
        katana_main.global_events_widget.eventsWidget().clearModel()
        katana_main.global_events_widget.loadEventsDataFromJSON()


def installGlobalEvents():
    Utils.EventModule.RegisterCollapsedHandler(loadGlobalEvents, 'nodegraph_setRootNode')
    Callbacks.addCallback(Callbacks.Type.onSceneAboutToLoad, cleanupGlobalEvents)