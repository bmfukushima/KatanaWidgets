import json
import os

from Katana import NodegraphAPI, UI4, Callbacks

from Utils2 import gsvutils, paramutils


def gsvChangedEvent(args):
    """
    Runs a user script when a GSV is changed

    Args:
        arg (arg): from Katana Callbacks/Events (parameter_finalizeValue)

    """
    for arg in args:
        # preflight
        if not gsvutils.isGSVOptionEvent(arg): return

        # get param/attrs
        param = arg[2]['param']
        param_name = param.getName()

        # check param type
        if param_name != "value": return

        # get attrs
        gsv = param.getParent().getName()
        option = param.getValue(0)

        # check to see if this GSV is setting to its current value
        old_values = json.loads(gsvutils.paramOldValuesStatic().getValue(0))
        if gsv in old_values.keys():
            if old_values[gsv] == param.getValue(0):
                return

        # update tabs
        gsvutils.updateGSVOptionForAllViewTabs(gsv, option)

        # update old values
        """ This is needed to stop the script from running every time the user selects the same GSV twice"""
        old_values[gsv] = option
        gsvutils.paramOldValuesStatic().setValue(json.dumps(old_values), 0)

        # load events data
        event_data = json.loads(gsvutils.getGSVEventDataParam().getValue(0))

        # preflight
        if gsv not in list(event_data.keys()): return

        # user defined disable on GSV
        if not event_data[gsv]["enabled"]: return
        if option not in list(event_data[gsv]["data"].keys()): return

        # option does not exist
        if not event_data[gsv]["data"][option]["enabled"]: return

        # PREFLIGHT/LOADING COMPLETE --- START RUN OF SCRIPT
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
            script = gsvutils.paramScriptsStatic().getChild(user_data["script"]).getValue(0)
            exec(script, globals(), local_variables)
        elif not user_data["is_script"]:
            if os.path.exists(user_data["filepath"]):
                with open(user_data["filepath"]) as script_descriptor:
                    exec(script_descriptor.read(), local_variables)


def gsvEventChangedEvent(args):
    """ Updates all of the event views when the user updates the event data.
    The GSV Event Data located on gsvutils.EVENT_PARAM_LOCATION (KatanaBebop.GSVEventsData)"""
    # get param/attrs
    for arg in args:
        root_node = NodegraphAPI.GetRootNode()
        if arg[2]["node"] != root_node: return False
        if "param" not in list(arg[2].keys()): return False
        if not arg[2]["param"]: return False
        if arg[2]["param"] != gsvutils.getGSVEventDataParam(): return False

        gsvutils.updateAllGSVEventsTabs()


def gsvNameChangeEvent(args):
    """
    (   'parameter_setName',
        1174573088,
        {
            'param': <NodegraphAPI_cmodule.Parameter object at 0x7f62bc6d96b0 group 'c'>,
            'paramParentName': 'rootNode.variables',
            'oldName': 'b',
            'newName': 'c'
        }
    )
    Args:
        args:

    Returns:

    """
    for arg in args:
        if "param" not in list(arg[2].keys()): return False
        if not arg[2]['param']: return False
        if not arg[2]['param'].getParent(): return False
        if arg[2]['param'].getParent() != gsvutils.getVariablesParameter(): return False

        old_name = arg[2]["oldName"]
        new_name = arg[2]["newName"]
        gsvutils.updateGSVNameForAllViewTabs(old_name, new_name)


def gsvDeleteEvent(args):
    """
    (
        'parameter_deleteChild',
        1174573088,
        {
            'param': <NodegraphAPI_cmodule.Parameter object at 0x7f62ccceef30 group 'variables'>,
            'paramName': 'rootNode.variables',
            'node': <RootNode NodegraphAPI_cmodule.GroupNode 'rootNode'>,
            'childParam': <NodegraphAPI_cmodule.Parameter object at 0x7f62bc6d96b0 group 'c' orphaned>
            'childName': 'c'
            'element': <PyXmlIO.Element object at 0x7f62bc6fde30>
            'index': 0
        }
    )
    Args:
        args:

    Returns:

    """
    for arg in args:
        # check to make sure it is a GSV Create event
        if not gsvutils.isGSVCreateDestroyEvent(arg): return
        gsv = arg[2]["childName"]
        gsvutils.removeGSVFromAllViewTabs(gsv)


def gsvCreateEvent(args):
    """
 (  'parameter_createChild',
    1024916048,
    {
        'param': <NodegraphAPI_cmodule.Parameter object at 0x7f3af0c21eb0 group 'variables'>
        'paramName': 'rootNode.variables'
        'node': <RootNode NodegraphAPI_cmodule.GroupNode 'rootNode'>
        'childParam': <NodegraphAPI_cmodule.Parameter object at 0x7f3be000baf0 group 'var1'>
        'element': <PyXmlIO.Element object at 0x7f3be000bbb0>
        'index': 2
    }
)
    Args:
        args:

    Returns:

    """
    for arg in args:
        # check to make sure it is a GSV Create event
        if not gsvutils.isGSVCreateDestroyEvent(arg): return
        gsv = arg[2]["childParam"].getName()
        gsvutils.addGSVToAllViewTabs(gsv)

# def updateGSVsOnSceneLoad(args):
#     """ When a new scene is loaded, this will reset all of the GSVManager tabs to the new data"""
#     # get all tabs
#     gsv_manager_tabs = UI4.App.Tabs.GetTabsByType("GSV Manager")
#
#     # # for each tab, update tab data
#     for gsv_manager in gsv_manager_tabs:
#         print("============= gsv manager")
#         print(gsv_manager)
#         gsv_manager.eventsWidget().setNode(NodegraphAPI.GetRootNode())
#         gsv_manager.update()

    # update state managers
    # for tab in UI4.App.Tabs.GetTabsByType("State Manager"):
    #     print("========= state manager")
    #     print(tab)
    #     print(tab.viewWidget())
    #     print(tab.viewWidget().gsvViewWidget())
    #     tab.viewWidget().gsvViewWidget().update()


def createDataParamsOnSceneLoad(*args, **kwargs):
    """Creates the parameters that store the event data on scene load/new scene """
    from Katana import Utils

    node = NodegraphAPI.GetRootNode()
    events_data = node.getParameter(gsvutils.EVENT_PARAM_LOCATION)

    # create default parameter if needed
    if not events_data:
        Utils.UndoStack.DisableCapture()
        paramutils.createParamAtLocation(gsvutils.EVENT_PARAM_LOCATION + ".data", node, paramutils.STRING, initial_value="{}")
        paramutils.createParamAtLocation(gsvutils.EVENT_PARAM_LOCATION + ".old_values", node, paramutils.STRING, initial_value="{}")
        paramutils.createParamAtLocation(gsvutils.EVENT_PARAM_LOCATION + ".scripts", node, paramutils.GROUP)

        Utils.UndoStack.EnableCapture()


def installGSVManagerEvents(*args, **kwargs):
    from Katana import Utils
    # create default param
    # EventWidget.createGSVEventsParam()
    Utils.UndoStack.DisableCapture()

    # gsvutils.hideEngineersGSVUI()
    #Callbacks.addCallback(Callbacks.Type.onSceneAboutToLoad, createDataParamsOnSceneLoad)

    # Utils.EventModule.RegisterCollapsedHandler(updateGSVsOnSceneLoad, 'nodegraph_setRootNode')
    Utils.EventModule.RegisterCollapsedHandler(createDataParamsOnSceneLoad, "nodegraph_loadEnd")
    Utils.EventModule.RegisterCollapsedHandler(gsvChangedEvent, "parameter_finalizeValue", None)
    Utils.EventModule.RegisterCollapsedHandler(gsvEventChangedEvent, "parameter_finalizeValue", None)
    Utils.EventModule.RegisterCollapsedHandler(gsvNameChangeEvent, "parameter_setName", None)
    Utils.EventModule.RegisterCollapsedHandler(gsvDeleteEvent, "parameter_deleteChild", None)
    Utils.EventModule.RegisterCollapsedHandler(gsvCreateEvent, "parameter_createChild", None)

    Utils.UndoStack.EnableCapture()
