import json

from cgwidgets.widgets import NodeColorRegistryWidget

from Utils2 import paramutils, nodeutils

PARAM_LOCATION = "KatanaBebop.NodeColorRegistry"


def setNodeColor(args):
    from Katana import NodegraphAPI
    #[('node_create', 2935610080, {'node': < ImageMerge Nodes2DAPI_cmodule.Node2D 'ImageMerge' >, 'nodeName': 'ImageMerge', 'nodeType': 'ImageMerge'})]
    for arg in args:
        if arg[0] == "node_create":
            node = arg[2]["node"]
            node_type = arg[2]["nodeType"]
            filepath = NodegraphAPI.GetRootNode().getParameter(PARAM_LOCATION).getValue(0)
            if NodeColorRegistryWidget.isColorConfigFile(filepath):
                # open file
                with open(filepath, "r") as f:
                    data = json.load(f)["colors"]
                    # set node color
                    if node_type in data.keys():
                        color = data[node_type]
                        if color:
                            nodeutils.setNodeColor(node, [x/255 for x in color[:3]])

def installDefaultNodeColorsEventFilter(**kwargs):
    from Katana import Utils
    Utils.EventModule.RegisterCollapsedHandler(setNodeColor, 'node_create')
