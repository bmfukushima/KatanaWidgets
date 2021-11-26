from Katana import NodegraphAPI

from Utils2 import paramutils

PARAM_LOCATION = "KatanaBebop.StateManagerData"

def param():
    return NodegraphAPI.GetRootNode().getParameter(PARAM_LOCATION)

def createDataParamsOnSceneLoad(*args, **kwargs):
    """Creates the parameters that store the event data on scene load/new scene """
    from Katana import Utils

    node = NodegraphAPI.GetRootNode()
    events_data = node.getParameter(PARAM_LOCATION)

    # create default parameter if needed
    if not events_data:
        Utils.UndoStack.DisableCapture()
        paramutils.createParamAtLocation(PARAM_LOCATION, node, paramutils.STRING, initial_value="{\"data\":[]}")

        Utils.UndoStack.EnableCapture()

def installStateManagerDefaultParam(*args, **kwargs):
    from Katana import Utils
    # create default param
    Utils.UndoStack.DisableCapture()

    Utils.EventModule.RegisterCollapsedHandler(createDataParamsOnSceneLoad, 'nodegraph_loadEnd')

    Utils.UndoStack.EnableCapture()
