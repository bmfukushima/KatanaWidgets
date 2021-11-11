from Katana import Utils, Callbacks
from Utils2 import paramutils
from Utils2.widgetutils import katanaMainWindow
# copy/paste
PARAM_LOCATION = "KatanaBebop.GlobalEventsData"

def cleanupGlobalEvents(**kwargs):
    """ Destroys all global events"""
    from Katana import UI4, NodegraphAPI
    # get attrs
    node = NodegraphAPI.GetRootNode()
    events_data = node.getParameter(PARAM_LOCATION + ".data")

    # cleanup data
    if events_data:
        if hasattr(katanaMainWindow(), "global_events_widget"):
            katanaMainWindow().global_events_widget.disableAllEvents(events_data.getValue(0))
            katanaMainWindow().global_events_widget.setEventsData({})

    # reset param data
    data_group = node.getParameter(PARAM_LOCATION)
    if not data_group:
        paramutils.createParamAtLocation(PARAM_LOCATION, node, paramutils.GROUP)
    if data_group:
        data_group.deleteChild(data_group.getChild("scripts"))
        data_group.deleteChild(data_group.getChild("data"))
        paramutils.createParamAtLocation(PARAM_LOCATION + ".data", node, paramutils.STRING, initial_value="{}")
        paramutils.createParamAtLocation(PARAM_LOCATION + ".scripts", node, paramutils.GROUP)


def createDataParamsOnSceneLoad(*args, **kwargs):
    """Creates the parameters that store the event data on scene load/new scene """
    from Katana import NodegraphAPI, Utils

    # get attrs
    node = NodegraphAPI.GetRootNode()
    events_data = node.getParameter(PARAM_LOCATION + ".data")

    # create default parameter if needed
    if not events_data:
        Utils.UndoStack.DisableCapture()

        paramutils.createParamAtLocation(PARAM_LOCATION + ".data", node, paramutils.STRING, initial_value="{}")
        paramutils.createParamAtLocation(PARAM_LOCATION + ".scripts", node, paramutils.GROUP)

        Utils.UndoStack.EnableCapture()

def loadGlobalEvents(*args):
    """ Loads all global events"""
    from Katana import NodegraphAPI, UI4
    from Widgets2 import GlobalEventWidget

    node = NodegraphAPI.GetRootNode()
    # load global events
    if katanaMainWindow():
        # create Event Widget if needed
        # if not node.getParameter(PARAM_LOCATION):
        #     paramutils.createParamAtLocation(PARAM_LOCATION, node, paramutils.STRING, initial_value="{}")
        if not hasattr(katanaMainWindow(), "global_events_widget"):
            katanaMainWindow().global_events_widget = GlobalEventWidget(katanaMainWindow(), node=node, param=PARAM_LOCATION)

        # load events
        katanaMainWindow().global_events_widget.setNode(node)
        katanaMainWindow().global_events_widget.eventsWidget().clearModel()
        katanaMainWindow().global_events_widget.loadEventsDataFromParam()

def installGlobalEvents():
    # createDataParamsOnSceneLoad()

    Callbacks.addCallback(Callbacks.Type.onSceneAboutToLoad, cleanupGlobalEvents)
    Utils.EventModule.RegisterCollapsedHandler(createDataParamsOnSceneLoad, 'nodegraph_loadEnd')
    Utils.EventModule.RegisterCollapsedHandler(loadGlobalEvents, 'nodegraph_setRootNode')
