from qtpy.QtWidgets import QWidget, QVBoxLayout, QLabel
from qtpy.QtCore import Qt

from Widgets2 import (
    AbstractNodegraphWidget,
    AbstractParametersDisplayWidget)

from cgwidgets.widgets import ShojiLayout

from Katana import UI4


class GroupNodeEditorMainWidget(QWidget):
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
    def __init__(self, parent, node, main_node):
        super(GroupNodeEditorMainWidget, self).__init__(parent)
        # setup attrs
        self.node = node
        self.main_node = main_node

        # setup GUI
        QVBoxLayout(self)
        self.live_group_widget = QLabel("Live Group")
        self.node_editor_widget = GroupNodeEditor(self)

        self.layout().addWidget(self.live_group_widget)
        self.layout().addWidget(self.node_editor_widget)

        # create gui
        self.nodegraph_widget = NodegraphWidget(self, node=self.node)
        self.nodegraph_widget.setupDestroyNodegraphEvent()
        self.parameters_widget = ParametersDisplayWidget(self, node=self.main_node)

        self.node_editor_widget.addWidget(self.nodegraph_widget)
        self.node_editor_widget.addWidget(self.parameters_widget)


class GroupNodeEditor(ShojiLayout):
    def __init__(self, parent):
        super(GroupNodeEditor, self).__init__(parent)

        self.setOrientation(Qt.Vertical)
        self.setFocusPolicy(Qt.WheelFocus)


class NodegraphWidget(AbstractNodegraphWidget):
    def __init__(self, parent=None, node=None):
        super(NodegraphWidget, self).__init__(parent)
        # setup attrs
        self.setNode(node)

        AbstractNodegraphWidget.displayMenus(False, self.getPanel())
        self.enableScrollWheel(False)
        self.goToNode(node.getChildByIndex(0))
        #self.setupDestroyNodegraphEvent()


class ParametersDisplayWidget(AbstractParametersDisplayWidget):
    """
    The widget that will display all of the parameters to the user.
    """
    def __init__(self, parent=None, node=None):
        super(ParametersDisplayWidget, self).__init__(parent)
        self.node = node
        self.setNodeFilter(self.nodeFilter)
        self.enableSelectionDisplay(True)

    def nodeFilter(self, node):
        """
        Filter for the node list to ensure that the selected nodes are a child of this one

        Args:
            node (Node): The node that is being filtered
        """
        if not node: return False
        if node.getParent() != self.node: return False

        return True