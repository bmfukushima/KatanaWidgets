import os
import json

from qtpy.QtWidgets import QVBoxLayout
from qtpy.QtCore import Qt

from Katana import UI4, KatanaResources, NodegraphAPI, Utils, DrawingModule

from cgwidgets.widgets import NodeColorRegistryWidget, ListInputWidget

from Utils2 import paramutils, nodeutils


CONFIGS = "KATANABEBOPNODECOLORS"
PARAM_LOCATION = "KatanaBebop.NodeColorRegistry"
DEFAULT_CONFIG_ENVAR = "KATANABEBOPDEFAULTCOLORCONFIG"
DEFAULT_CONFIG_LOCATION = os.environ["KATANABEBOP"] + "/Settings/nodeColorConfig.json"


class NodeColorRegistryTab(UI4.Tabs.BaseTab):
    """Main tab widget for the desirable widgets"""
    NAME = "Node Color Registry"

    def __init__(self, parent=None):
        super(NodeColorRegistryTab, self).__init__(parent)
        # create main widget
        self._node_color_registry_widget = NodeColorRegistryWidget(self, envar=CONFIGS)

        #
        if CONFIGS in os.environ.keys():
            os.environ[CONFIGS] += ":{USER_RESOURCES}/ColorConfigs/User".format(USER_RESOURCES=KatanaResources.GetUserKatanaPath())

        # setup default color config
        self._node_color_registry_widget.setColorFile(NodeColorRegistryTab.defaultColorConfigFile())

        self._node_color_registry_widget.setDefaultSaveLocation(
            KatanaResources.GetUserKatanaPath() + "/ColorConfigs/User")

        # setup events
        self._node_color_registry_widget.setUserLoadEvent(self.userLoadEvent)
        self._node_color_registry_widget.setUserSaveEvent(self.userSaveEvent)

        # setup user commands
        self._node_color_registry_widget.addCommand("clearAllNodeColors", self.clearAllNodeColors)
        self._node_color_registry_widget.addCommand("clearColorsFromSelectedTypes", self.clearColorsFromSelectedTypes)
        self._node_color_registry_widget.addCommand("clearColorsFromSelection", self.clearColorsFromSelection)
        self._node_color_registry_widget.addCommand("clearColorsFromSelectedNodesAndDescendants", self.clearColorsFromSelectedNodesAndDescendants)
        self._node_color_registry_widget.addCommand("updateAllNodeColors", self.updateAllNodeColors)
        self._node_color_registry_widget.addCommand("updateColorsFromSelection", self.updateColorsFromSelection)
        self._node_color_registry_widget.addCommand("updateColorsFromSelectedNodesAndDescendants", self.updateColorsFromSelectedNodesAndDescendants)
        self._node_color_registry_widget.addCommand("updateColorsFromSelectedTypes", self.updateColorsFromSelectedTypes)

        # setup layout
        QVBoxLayout(self)
        self.layout().addWidget(self._node_color_registry_widget)

    """ COMMANDS """
    @staticmethod
    def __getSelectedTypes():
        # create list of all types selected
        selected_types = []
        for node in NodegraphAPI.GetAllSelectedNodes():
            selected_types.append(node.getType())

        selected_types = list(set(selected_types))
        return selected_types

    @staticmethod
    def clearColorsFromSelectedTypes():
        """ Clears the colors of all of the node types from the current selection"""
        selected_types = NodeColorRegistryTab.__getSelectedTypes()

        # remove colors from nodes
        for node_type in selected_types:
            for node in NodegraphAPI.GetAllNodesByType(node_type):
                nodeutils.removeNodeColor(node)

    @staticmethod
    def clearAllNodeColors():
        """ Removes the custom coloring from ALL nodes in the Nodegraph"""
        for node in NodegraphAPI.GetAllNodes():
            nodeutils.removeNodeColor(node)

    @staticmethod
    def clearColorsFromSelection():
        for node in NodegraphAPI.GetAllSelectedNodes():
            nodeutils.removeNodeColor(node)

    @staticmethod
    def clearColorsFromSelectedNodesAndDescendants():
        color_config_data = NodeColorRegistryTab.getNodeColorConfigData()
        if color_config_data:
            for node in NodegraphAPI.GetAllSelectedNodes():
                descendants = nodeutils.getNodeAndAllDescendants(node)
                for child_node in descendants:
                    nodeutils.removeNodeColor(child_node)

    @staticmethod
    def updateColorsFromSelection():
        """ Updates the color of all of the selected nodes"""
        color_config_data = NodeColorRegistryTab.getNodeColorConfigData()
        if color_config_data:
            for node in NodegraphAPI.GetAllSelectedNodes():
                NodeColorRegistryTab.setNodeColorFromConfigData(node, color_config_data)

    @staticmethod
    def updateColorsFromSelectedNodesAndDescendants():
        """ Updates the color of all of the selected nodes and their descendants"""
        color_config_data = NodeColorRegistryTab.getNodeColorConfigData()
        if color_config_data:
            for node in NodegraphAPI.GetAllSelectedNodes():
                descendants = nodeutils.getNodeAndAllDescendants(node)
                for child_node in descendants:
                    NodeColorRegistryTab.setNodeColorFromConfigData(child_node, color_config_data)

    @staticmethod
    def updateAllNodeColors():
        """ Updates the all of the nodes colors to the current config"""
        color_config_data = NodeColorRegistryTab.getNodeColorConfigData()
        if color_config_data:
            for node in NodegraphAPI.GetAllNodes():
                NodeColorRegistryTab.setNodeColorFromConfigData(node, color_config_data)

    @staticmethod
    def updateColorsFromSelectedTypes():
        """ Gets all of the node types from the selection, and updates their colors"""
        # create list of all types selected
        selected_types = NodeColorRegistryTab.__getSelectedTypes()

        config_data = NodeColorRegistryTab.getNodeColorConfigData()
        # remove colors from nodes
        for node_type in selected_types:
            for node in NodegraphAPI.GetAllNodesByType(node_type):
                NodeColorRegistryTab.setNodeColorFromConfigData(node, config_data)

    """ UTILS """
    @staticmethod
    def setNodeColorFromConfigData(node, color_config_data):
        """ Sets the nodes color from the config data provided

        Args:
            node (Node)
            node_type (string)
            color_config_data (json)
        """
        if color_config_data:
            if node.getType() in color_config_data.keys():
                color = color_config_data[node.getType()]
                if color:
                    nodeutils.setNodeColor(node, [x / 255 for x in color[:3]])

    @staticmethod
    def getNodeColorConfigData():
        filepath = NodegraphAPI.GetRootNode().getParameter(PARAM_LOCATION).getValue(0)
        if NodeColorRegistryWidget.isColorConfigFile(filepath):
            # open file
            with open(filepath, "r") as f:
                data = json.load(f)["colors"]
                return data

        return None

    @staticmethod
    def updateNodeColorFromConfig(node):
        """ Updates a singular nodes color from the current config file

        Notes:
            This is not to be confused with "setNodeColorFromConfigData"

        Args:
            node (Node): to have the color updated"""
        param = NodegraphAPI.GetRootNode().getParameter(PARAM_LOCATION)
        if not param: return
        if DrawingModule.GetCustomNodeColor(node): return

        color_config_data = NodeColorRegistryTab.getNodeColorConfigData()
        NodeColorRegistryTab.setNodeColorFromConfigData(node, color_config_data)

    @staticmethod
    def defaultColorConfigFile():
        """ Gets the default color config file

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

    def createParam(self):
        # get attrs
        node = NodegraphAPI.GetRootNode()
        events_data = node.getParameter(PARAM_LOCATION)

        # create default parameter if needed
        if not events_data:
            Utils.UndoStack.DisableCapture()

            paramutils.createParamAtLocation(PARAM_LOCATION, node, paramutils.STRING, initial_value="")
            Utils.UndoStack.EnableCapture()

    """ EVENTS """
    def userSaveEvent(self, filepath):
        self.createParam()
        NodegraphAPI.GetRootNode().getParameter(PARAM_LOCATION).setValue(filepath, 0)

    def userLoadEvent(self, filepath):
        self.createParam()
        NodegraphAPI.GetRootNode().getParameter(PARAM_LOCATION).setValue(filepath, 0)

    """ WIDGETS """
    def nodeColorRegistryWidget(self):
        return self._node_color_registry_widget

