'''
ToDo
    - Add group functionality?
        gross.. then I have to store data or something
            could potentially just save it on the actual param data?
    - Add another layer
        - so that it all sits in another ShojiModelViewWidget
        and you can select the category of desired nodes
        - will need to register the categories on the project settings
'''
from qtpy.QtWidgets import QVBoxLayout
from cgwidgets.views import AbstractDragDropListView
from cgwidgets.utils import getWidgetAncestor

from Katana import UI4 , NodegraphAPI, Utils
from Widgets2 import NodeViewWidget


class DesiredNodes(UI4.Tabs.BaseTab):
    def __init__(self, parent=None):
        super(DesiredNodes, self).__init__(parent)

        self.desired_nodes = []

        # setup main widget
        self.main_widget = NodeViewWidget()

        # setup custom view
        view = DesiredNodesView(self)
        self.main_widget.setHeaderViewWidget(view)
        self.main_widget.setHeaderItemDeleteEvent(self.makeUndesirable)

        # setup shoji style
        self.main_widget.setMultiSelect(True)

        # setup main layout
        QVBoxLayout(self)
        self.layout().addWidget(self.main_widget)

        # populate UI
        self.populate()

    def makeNodeDesirable(self, node, enabled):
        if enabled:
            if node not in self.desired_nodes:
                self.main_widget.createNewIndexFromNode(node)
                self.desired_nodes.append(node)
                self._makeDesirableParam(node, enabled)

        else:
            self._makeDesirableParam(node, False)

    def _makeDesirableParam(self, node, enabled):
        """
        Creates/Destroys the hidden reference to the "_is_desired" param

        Args:
            node (Node): to make desirable
            enabled (bool): how $3xy this node is

        """
        desirable_param = node.getParameter("_is_desired")

        if enabled:
            node.getParameters().createChildString("_is_desired", "<3")
        else:
            if desirable_param:
                node.getParameters().deleteChild(desirable_param)

    def makeUndesirable(self, item):
        """
        On Delete, this will remove the desirable reference to the node
        Args:
            item (ShojiModelItem): item currently selected

        """
        node = self.main_widget.getNodeFromItem(item)
        self.makeNodeDesirable(node, False)
        #self.main_widget.model().deleteItem(item)
        self.desired_nodes.remove(node)

    def populate(self):
        """
        Adds all of the indexes for every node that has been
        chosen as "desirable" by the user
        """
        # clear model
        self.main_widget.clearModel()

        # force repopulate
        self.desired_nodes = []
        for node in NodegraphAPI.GetAllNodes():
            is_desired = node.getParameter('_is_desired')
            if is_desired:
                self.main_widget.createNewIndexFromNode(node)
                self.desired_nodes.append(node)


class DesiredNodesView(AbstractDragDropListView):
    def __init__(self, parent=None):
        super(DesiredNodesView, self).__init__(parent)

    def dragEnterEvent(self, event):
        mimedata = event.mimeData()
        if mimedata.hasFormat('nodegraph/nodes'):
            event.accept()
        return AbstractDragDropListView.dragEnterEvent(self, event)

    def dropEvent(self, event):
        """
        This will handle all drops into the view from the Nodegraph

        Alot of this is copy/paste from nodeMovedEvent
        """
        mimedata = event.mimeData()
        if mimedata.hasFormat('nodegraph/nodes'):
            nodes_list = mimedata.data('nodegraph/nodes').data().split(',')
            parent_widget = getWidgetAncestor(self, DesiredNodes)
            for node_name in nodes_list:
                # get node
                node = NodegraphAPI.GetNode(node_name)
                parent_widget.makeNodeDesirable(node, True)

        return AbstractDragDropListView.dropEvent(self, event)


PluginRegistry = [("KatanaPanel", 2, "Desired Nodes", DesiredNodes)]