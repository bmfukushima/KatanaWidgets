from qtpy.QtWidgets import QWidget, QVBoxLayout
from qtpy.QtCore import Qt

from Widgets2 import (
    AbstractNodegraphWidget,
    AbstractParametersDisplayWidget)

from cgwidgets.widgets import ShojiLayout


class GroupNodeEditorWidget(ShojiLayout):
    """
    The tab that will display the default parameters adjustment pane to the user.
    This is a new way of adjusting group nodes where it will essentially have three
    areas.
        | -- Live Group Toggle
        | -- Mini Nodegraph
        | -- Parameters

    Attributes:
        parent (QWidget):
        node (node): top level node, this is the node that is displayed to the user
            in the nodegraph.
        main_node (node): this is the first node inside of the top level node,
            this node acts as a toggle to switch between a live group, and a normal
            group on this node.

    Widgets:
        QWidget
            | -- QVBoxLayout
                    | -- live_group_widget (QLabel)
                    | -- node_editor_widget (GroupNodeEditor --> ShojiLayout)
                            | -- nodegraph_widget (NodegraphWidget)
                            | -- parameters_widget (ParametersDisplayWidget)
    """
    def __init__(self, parent, node):
        super(GroupNodeEditorWidget, self).__init__(parent)
        # setup attrs
        self._node = node

        # setup GUI
        QVBoxLayout(self)
        self.setOrientation(Qt.Vertical)
        self.setFocusPolicy(Qt.WheelFocus)

        # create gui
        self._nodegraph_widget = NodegraphWidget(self, node=self.node())
        self._parameters_widget = ParametersDisplayWidget(self, node=self.node())

        self.addWidget(self._nodegraph_widget)
        self.addWidget(self._parameters_widget)

        self.setSizes([100, 100])

    def parametersWidget(self):
        return self._parameters_widget

    def nodegraphWidget(self):
        return self._nodegraph_widget

    def goToNode(self, node):
        self.nodegraphWidget().goToNode(node)

    def node(self):
        return self._node

    def setNode(self, node):
        self._node = node
        self.nodegraphWidget().setNode(node)
        self.nodegraphWidget().goToNode(node)
        self.parametersWidget().setNode(node)


class NodegraphWidget(AbstractNodegraphWidget):
    def __init__(self, parent=None, node=None):
        super(NodegraphWidget, self).__init__(parent)
        # setup attrs
        self.setNode(node)

        # AbstractNodegraphWidget.displayMenus(False, self.getPanel())
        self.enableScrollWheel(False)
        # todo
        # self.goToNode(node.getChildByIndex(0))
        self.goToNode(node)
        #self.setupDestroyNodegraphEvent()


class ParametersDisplayWidget(AbstractParametersDisplayWidget):
    """
    The widget that will display all of the parameters to the user.
    """
    def __init__(self, parent=None, node=None):
        super(ParametersDisplayWidget, self).__init__(parent)
        self._node = node
        self.setNodeFilter(self.nodeFilter)
        self.enableSelectionDisplay(True)

    def node(self):
        return self._node

    def setNode(self, node):
        self._node = node

    def nodeFilter(self, node):
        """
        Filter for the node list to ensure that the selected nodes are a child of this one

        Args:
            node (Node): The node that is being filtered
        """
        if not node: return False
        if node.getParent() != self.node(): return False

        return True