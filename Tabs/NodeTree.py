'''
To Do
    - Filter:
        need to make this recursive... so it removes empty groups
    - updates
        needs to restore state
    - Drag/Drop move nodes via Node List
'''
from qtpy.QtWidgets import QWidget, QVBoxLayout, QLabel
from qtpy.QtCore import Qt, QSortFilterProxyModel, QRegExp

from Katana import UI4, NodegraphAPI, Utils

from cgwidgets.widgets import ShojiModelViewWidget, NodeTypeListWidget, LabelledInputWidget, StringInputWidget, ListInputWidget
from cgwidgets.views import AbstractDragDropTreeView
from cgwidgets.settings import attrs
from Utils2 import nodeutils, getFontSize

class NodeTreeTab(UI4.Tabs.BaseTab):
    NAME = "Node Tree"

    def __init__(self, parent=None):
        super(NodeTreeTab, self).__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.node_tree = NodeTreeWidget(self)
        # self.node_name_filter_widget = NodeNameFilterWidget(self)
        # self.node_type_filter_widget = NodeTypeFilterWidget(self)

        # layout.addWidget(self.node_name_filter_widget)
        # layout.addWidget(self.node_type_filter_widget)
        layout.addWidget(self.node_tree)
    #
    #     Utils.EventModule.RegisterCollapsedHandler(self.update, 'node_create', None)
    #     Utils.EventModule.RegisterCollapsedHandler(self.update, 'node_setName', None)
    #     Utils.EventModule.RegisterCollapsedHandler(self.update, 'node_setParent', None)
    #     Utils.EventModule.RegisterCollapsedHandler(self.updateColor, 'node_setEdited', None)
    #     Utils.EventModule.RegisterCollapsedHandler(self.updateColor, 'node_setViewed', None)
    #
    # def updateColor(self, eventID):
    #     tree_widget = self.node_tree
    #     tree_widget.updateItemColor()
    #
    # def update(self, eventID):
    #     # get tree widget
    #     tree_widget = self.node_tree
    #
    #     # delete list
    #     for index in reversed(range(tree_widget.topLevelItemCount())):
    #         tree_widget.takeTopLevelItem(index)
    #     tree_widget.populate()
    #     tree_widget.updateItemColor()


class NodeTreeWidget(ShojiModelViewWidget):
    def __init__(self, parent=None):
        super(NodeTreeWidget, self).__init__(parent)
        # setup default attrs
        self._node_name_filter = ""
        self._node_type_filter = ""

        # create view
        header_widget = AbstractDragDropTreeView()
        self.setHeaderViewWidget(header_widget)
        self.setHeaderData(['name', 'type'])
        self.setHeaderPosition(attrs.WEST, attrs.SOUTH)

        # setup dynamic display
        self.setDelegateType(
            ShojiModelViewWidget.DYNAMIC,
            dynamic_widget=NodeTreeDelegateWidget,
            dynamic_function=NodeTreeDelegateWidget.updateGUI
        )

        # setup model filtering
        self.makeModelFilterable()
        name_filter = QRegExp("")
        type_filter = QRegExp("")
        self.addFilter(name_filter, arg="name", name="name")
        self.addFilter(type_filter, arg="type", name="type")

        # add filter widgets
        self._name_filter_widget = StringInputWidget(self)
        name_filter_labelled_widget = LabelledInputWidget(
            name="Name", delegate_widget=self._name_filter_widget, default_label_length=getFontSize() * 5)
        self.addHeaderDelegateWidget([], name_filter_labelled_widget, modifier=Qt.NoModifier, focus=True)
        name_filter_labelled_widget.show()
        self._name_filter_widget.setUserFinishedEditingEvent(self.filterByNameUpdated)
        name_filter_labelled_widget.setFixedHeight(getFontSize() * 3)

        self._type_filter_widget = ListInputWidget(self)
        self._type_filter_widget.populate([[node] for node in [""] + NodegraphAPI.GetNodeTypes()])
        type_filter_labelled_widget = LabelledInputWidget(
            name="Type", delegate_widget=self._type_filter_widget, default_label_length=getFontSize() * 5)
        self.addHeaderDelegateWidget([], type_filter_labelled_widget, modifier=Qt.NoModifier, focus=True)
        type_filter_labelled_widget.show()
        self._type_filter_widget.setUserFinishedEditingEvent(self.filterByTypeUpdated)
        type_filter_labelled_widget.setFixedHeight(getFontSize() * 3)

        self.populate(NodegraphAPI.GetRootNode())

    def nodeNameFilter(self):
        return self._node_name_filter

    def setNodeNameFilter(self, node_name_filter):
        self._node_name_filter = node_name_filter

    def nodeTypeFilter(self):
        return self._node_type_filter

    def setNodeTypeFilter(self, node_type_filter):
        self._node_type_filter = node_type_filter

    def filterByTypeUpdated(self, widget, node_type):
        self.updateFilterByName(node_type, "type")

    def filterByNameUpdated(self, widget, node_name):
        self.updateFilterByName(node_name, "name")

    """ UTILS """
    def doesNodeHaveValidDescendants(self, root_node):
        for node in nodeutils.getNodeAndAllDescendants(root_node):
            if self.isNodeValid(node):
                return True
        return False

    def isNodeValid(self, node):
        if self.nodeNameFilter() in node.getName().lower() and self.nodeTypeFilter() in node.getType().lower():
            return True

        return False

    """ EVENTS """
    def updateNodeList(self):
        self.clearModel()
        self.populate(NodegraphAPI.GetRootNode())

    def populate(self, node, parent=None):
        for child in node.getChildren():
            # filters matched
            if self.isNodeValid(node):
                if child.getType() not in ["Dot"]:
                    index = self.insertShojiWidget(
                        0, column_data={"name":child.getName(), "type":child.getType()}, parent=parent)

            # filter unmatched
            if nodeutils.isContainerNode(child):
                if self.doesNodeHaveValidDescendants(child):
                    self.populate(child, parent=index)


class NodeTreeDelegateWidget(QWidget):
    def __init__(self, parent=None):
        super(NodeTreeDelegateWidget, self).__init__(parent)
        QVBoxLayout(self)
        self.label = QLabel("default")

    @staticmethod
    def updateGUI(parent, widget, item):
        """
        parent (ShojiModelViewWidget)
        widget (ShojiModelDelegateWidget)
        item (ShojiModelItem)
        self --> widget.getMainWidget()
        """

        widget.getMainWidget().label.setText(item.name())
        print(item.getArg("name"), item.getArg("type"))
