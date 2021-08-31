import json
import os

from Katana import NodegraphAPI, UI4, Callbacks

from Utils2 import gsvutils, paramutils

PARAM_LOCATION = "KatanaBebop.GSVEventsData"

def paramScriptsStatic():
    return NodegraphAPI.GetRootNode().getParameter(PARAM_LOCATION + ".scripts")


def paramDataStatic():
    """ Gets the events data

    Returns (str): repr of JSON
    """
    return NodegraphAPI.GetRootNode().getParameter(PARAM_LOCATION+".data").getValue(0)


def gsvChangedEvent(args):
    """
    Runs a user script when a GSV is changed

    Args:
        arg (arg): from Katana Callbacks/Events (parameter_finalizeValue)

    """
    for arg in args:
        # preflight
        if not gsvutils.isGSVEvent(arg): return
        # get param
        param = arg[2]['param']
        param_name = param.getName()

        # check param type
        if param_name != "value": return

        # get attrs
        gsv = param.getParent().getName()
        option = param.getValue(0)
        event_data = json.loads(paramDataStatic())

        # preflight
        if gsv not in list(event_data.keys()): return

        # user defined disable on GSV
        if not event_data[gsv]["enabled"]: return
        if option not in list(event_data[gsv]["data"].keys()): return

        # option does not exist
        if not event_data[gsv]["data"][option]["enabled"]: return

        # user defined option disable
        # script does not exist
        # if "script" not in list(event_data[gsv]["data"][option].keys()): return

        # setup local variables
        local_variables = {}
        local_variables["gsv"] = gsv
        local_variables["option"] = option

        # get data
        user_data = event_data[gsv]["data"][option]

        # execute script
        if user_data["is_script"]:
            script = paramScriptsStatic().getChild(user_data["script"]).getValue(0)
            exec(script, globals(), local_variables)
        elif not user_data["is_script"]:
            if os.path.exists(user_data["filepath"]):
                with open(user_data["filepath"]) as script_descriptor:
                    exec(script_descriptor.read(), local_variables)


def updateGSVsOnSceneLoad(args):
    """ When a new scene is loaded, this will reset all of the GSVManager tabs to the new data"""
    # get all tabs
    gsv_manager_tabs = UI4.App.Tabs.GetTabsByType("GSVManager")

    # # for each tab, update tab data
    for gsv_manager in gsv_manager_tabs:
        gsv_manager.eventsWidget().setNode(NodegraphAPI.GetRootNode())
        gsv_manager.update()
        # set event data
        # update events view
        pass


def createDataParamsOnSceneLoad(*args, **kwargs):
    """Creates the parameters that store the event data on scene load/new scene """
    node = NodegraphAPI.GetRootNode()
    events_data = node.getParameter(PARAM_LOCATION)
    # create default parameter if needed
    if not events_data:
        paramutils.createParamAtLocation(PARAM_LOCATION + ".data", node, paramutils.STRING, initial_value="{}")
        paramutils.createParamAtLocation(PARAM_LOCATION + ".scripts", node, paramutils.GROUP)


def installGSVManagerEvents(*args, **kwargs):
    from Katana import Utils
    # create default param
    # EventWidget.createGSVEventsParam()

    gsvutils.hideEngineersGSVUI()
    #Callbacks.addCallback(Callbacks.Type.onSceneAboutToLoad, createDataParamsOnSceneLoad)

    Utils.EventModule.RegisterCollapsedHandler(updateGSVsOnSceneLoad, 'nodegraph_setRootNode')
    Utils.EventModule.RegisterCollapsedHandler(createDataParamsOnSceneLoad, 'nodegraph_loadEnd')
    Utils.EventModule.RegisterCollapsedHandler(gsvChangedEvent, 'parameter_finalizeValue', None)