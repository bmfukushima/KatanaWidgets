import os

from qtpy.QtWidgets import QVBoxLayout

from Katana import UI4, KatanaResources, NodegraphAPI, Utils

from cgwidgets.widgets import NodeColorRegistryWidget

from Utils2 import paramutils


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

        # setup default color config
        self._node_color_registry_widget.setColorFile(self.defaultColorConfigFile())

        self._node_color_registry_widget.setDefaultSaveLocation(
            KatanaResources.GetUserKatanaPath() + "/ColorConfigs/User")

        # setup events
        self._node_color_registry_widget.setUserLoadEvent(self.userLoadEvent)
        self._node_color_registry_widget.setUserSaveEvent(self.userSaveEvent)

        # setup layout
        QVBoxLayout(self)
        self.layout().addWidget(self._node_color_registry_widget)

    def defaultColorConfigFile(self):
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

    def userSaveEvent(self, filepath):
        self.createParam()
        NodegraphAPI.GetRootNode().getParameter(PARAM_LOCATION).setValue(filepath, 0)

    def userLoadEvent(self, filepath):
        self.createParam()
        NodegraphAPI.GetRootNode().getParameter(PARAM_LOCATION).setValue(filepath, 0)

    def nodeColorRegistryWidget(self):
        return self._node_color_registry_widget

