from Katana import Utils, Callbacks
from Utils2 import paramutils
from Utils2.widgetutils import katanaMainWindow
# copy/paste
_param_location = "KatanaBebop.GlobalEventsData"

def cleanupGlobalEvents(**kwargs):
    """ Destroys all global events"""
    from Katana import UI4, NodegraphAPI

    # get attrs
    node = NodegraphAPI.GetRootNode()
    events_data = node.getParameter(_param_location + ".data")

    # cleanup data
    if events_data:
        if hasattr(katanaMainWindow(), "global_events_widget"):
            katanaMainWindow().global_events_widget.disableAllEvents(events_data.getValue(0))


def createDataParamsOnSceneLoad(*args, **kwargs):
    """Creates the parameters that store the event data on scene load/new scene """
    from Katana import NodegraphAPI

    # get attrs
    node = NodegraphAPI.GetRootNode()

    events_data = node.getParameter(_param_location + ".data")

    # create default parameter if needed
    if not events_data:
        paramutils.createParamAtLocation(_param_location + ".data", node, paramutils.STRING, initial_value="{}")
        paramutils.createParamAtLocation(_param_location + ".scripts", node, paramutils.GROUP)


def loadGlobalEvents(*args):
    """ Loads all global events"""
    from Katana import NodegraphAPI, UI4
    from Widgets2 import EventWidget
    node = NodegraphAPI.GetRootNode()

    # load global events
    if katanaMainWindow():
        # create Event Widget if needed
        # if not node.getParameter(_param_location):
        #     paramutils.createParamAtLocation(_param_location, node, paramutils.STRING, initial_value="{}")
        if not hasattr(katanaMainWindow(), "global_events_widget"):
            katanaMainWindow().global_events_widget = EventWidget(katanaMainWindow(), node=node, param=_param_location)

        # load events
        katanaMainWindow().global_events_widget.main_node = node
        katanaMainWindow().global_events_widget.eventsWidget().clearModel()
        katanaMainWindow().global_events_widget.loadEventsDataFromParam()


def installGlobalEvents():
    Utils.EventModule.RegisterCollapsedHandler(loadGlobalEvents, 'nodegraph_setRootNode')
    Utils.EventModule.RegisterCollapsedHandler(createDataParamsOnSceneLoad, 'nodegraph_loadEnd')
    Callbacks.addCallback(Callbacks.Type.onSceneAboutToLoad, cleanupGlobalEvents)