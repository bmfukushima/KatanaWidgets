import json
import os

from cgwidgets.widgets import NodeColorRegistryWidget

from Utils2 import paramutils, nodeutils

from .NodeColorRegistryTab import NodeColorRegistryTab, PARAM_LOCATION, DEFAULT_CONFIG_ENVAR, DEFAULT_CONFIG_LOCATION


def defaultColorConfigFile():
    """ Gets the default color config file

    Note:
        copy/paste from ../Tab/NodeColorRegistryTab due to local import errors
        and directory structure

    Returns (str): path on disk to color config file"""
    if DEFAULT_CONFIG_ENVAR not in os.environ:
        default_color_config_file = DEFAULT_CONFIG_LOCATION
        # use katana bebop default
        pass
    else:
        default_color_config_file = os.environ[DEFAULT_CONFIG_ENVAR]
        if not NodeColorRegistryWidget.isColorConfigFile(default_color_config_file):
            print("{file} is not a valid config.  Using Katana Bebop default color config".format(
                file=default_color_config_file))
            default_color_config_file = DEFAULT_CONFIG_LOCATION
    return default_color_config_file


def setupDefaultColorConfigs(*args, **kwargs):
    """ Sets up the default color config file

    This event occurs when Katana opens, or a new file is created."""
    from Katana import NodegraphAPI, Utils

    default_config_file = defaultColorConfigFile()
    # get attrs
    node = NodegraphAPI.GetRootNode()
    config_file_param = node.getParameter(PARAM_LOCATION)

    # create default parameter if needed
    if not config_file_param:
        Utils.UndoStack.DisableCapture()
        paramutils.createParamAtLocation(
            PARAM_LOCATION, node, paramutils.STRING, initial_value=default_config_file)
        Utils.UndoStack.EnableCapture()


def setNodeColor(args):
    """ On node create, this will set the custom node color from the config file

    If the node already has a custom color, then this will bypass"""
    from Katana import NodegraphAPI, DrawingModule
    #[('node_create', 2935610080, {'node': < ImageMerge Nodes2DAPI_cmodule.Node2D 'ImageMerge' >, 'nodeName': 'ImageMerge', 'nodeType': 'ImageMerge'})]
    for arg in args:
        if arg[0] == "node_create":
            # preflight
            node = arg[2]["node"]
            # node_type = arg[2]["nodeType"]
            NodeColorRegistryTab.updateNodeColorFromConfig(node)


def installDefaultNodeColorsEventFilter(**kwargs):
    # os.environ[DEFAULT_CONFIG_ENVAR] = "/home/brian/.katana/ColorConfigs/User/test.json"
    # os.environ["KATANABEBOPNODECOLORS"] = "/home/brian/.cgwidgets/colorConfigs_01/;/home/brian/.cgwidgets/colorConfigs_02"
    from Katana import Utils
    Utils.EventModule.RegisterCollapsedHandler(setNodeColor, 'node_create')
    Utils.EventModule.RegisterCollapsedHandler(setupDefaultColorConfigs, 'nodegraph_loadEnd')
