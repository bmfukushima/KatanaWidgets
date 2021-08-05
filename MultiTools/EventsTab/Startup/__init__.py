from Katana import Utils, Callbacks
from Utils2 import paramutils
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
        paramutils.createParamAtLocation(_param_location, node, paramutils.STRING, initial_value="{}")

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

    # load global events
    if katana_main:
        # create Event Widget if needed
        if not node.getParameter(_param_location):
            paramutils.createParamAtLocation(_param_location, node, paramutils.STRING, initial_value="{}")
        if not hasattr(katana_main, "global_events_widget"):
            katana_main.global_events_widget = EventWidget(katana_main, node=node)

        # load events
        katana_main.global_events_widget.main_node = node
        katana_main.global_events_widget.eventsWidget().clearModel()
        katana_main.global_events_widget.loadEventsDataFromParam()


def installGlobalEvents():
    Utils.EventModule.RegisterCollapsedHandler(loadGlobalEvents, 'nodegraph_setRootNode')
    Callbacks.addCallback(Callbacks.Type.onSceneAboutToLoad, cleanupGlobalEvents)