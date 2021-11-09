from qtpy.QtWidgets import QVBoxLayout

from Katana import UI4, KatanaResources, NodegraphAPI, Utils

from cgwidgets.widgets import NodeColorRegistryWidget

from Utils2 import paramutils

CONFIGS = "KATANABEBOPNODECOLORS"
PARAM_LOCATION = "KatanaBebop.NodeColorRegistry"


class NodeColorRegistryTab(UI4.Tabs.BaseTab):
    """Main tab widget for the desirable widgets"""
    NAME = "Node Color Registry"

    def __init__(self, parent=None):
        super(NodeColorRegistryTab, self).__init__(parent)
        QVBoxLayout(self)
        self._node_color_registry_widget = NodeColorRegistryWidget(self, envar=CONFIGS)
        self._node_color_registry_widget.setDefaultSaveLocation(
            KatanaResources.GetUserKatanaPath() + "/COLORCONFIGS")
        self._node_color_registry_widget.setUserLoadEvent(self.userLoadEvent)
        self._node_color_registry_widget.setUserSaveEvent(self.userSaveEvent)
        self.layout().addWidget(self._node_color_registry_widget)

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

