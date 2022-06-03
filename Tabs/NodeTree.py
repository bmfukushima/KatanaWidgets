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



# class NodeTreeWidget(QtWidgets.QTreeWidget):
#     def __init__(self, parent=None):
#         super(NodeTreeWidget, self).__init__(parent)
#         self.item_dict = {}
#         self.view_item = None
#
#         header = QtWidgets.QTreeWidgetItem(['name', 'type'])
#
#         self.setAlternatingRowColors(True)
#         self.setHeaderItem(header)
#         self.header().resizeSection(0, 300)
#         self.header().setStretchLastSection(True)
#         self.populate()
#
#     def populate(self):
#
#         def set_flag(item):
#             if item == self.invisibleRootItem():
#                 return
#             else:
#                 item.setFlag(True)
#                 if item.parent():
#                     set_flag(item.parent())
#
#         def populateChildren(root, item=None):
#             '''
#             @root: Node(Katana)
#             @item: NodeTreeItem(QTreewidgetItem)
#             need to make this recursive... so it removes empty groups
#             '''
#             if hasattr(self.parent(), 'node_name_filter_widget'):
#                 node_name_filter_widget = self.parent().node_name_filter_widget
#                 node_name_filter_text = node_name_filter_widget.currentText()
#             else:
#                 node_name_filter_text = ''
#
#             if hasattr(self.parent(), 'node_type_filter_widget'):
#                 node_type_filter_widget = self.parent().node_type_filter_widget
#                 node_type_filter_text = node_type_filter_widget.currentText()
#             else:
#                 node_type_filter_text = ''
#
#             if 0 < len(root.getChildren()):
#                 for node in root.getChildren():
#                     if node.getType() in ['Dot', 'Backdrop']: continue
#                     else:
#                         if ((node_name_filter_text in node.getName() and node_type_filter_text in node.getType())
#                             or hasattr(node, 'getChildren')
#                         ):
#                             # create item
#                             new_item = NodeTreeItem(parent=item, name=node.getName())
#                             new_item.setNode(node)
#                             new_item.setNodeParent(root)
#                             if node_name_filter_text in node.getName():
#                                 set_flag(new_item)
#                             item_dict = self.getItemDict()
#                             item_dict[node.getName()] = new_item
#                             self.setItemDict(item_dict)
#
#                             # populate children
#                             if hasattr(node, 'getChildren'):
#                                 if 0 < len(node.getChildren()):
#                                     # todo flag here to show tool children
#                                     #if node.getType() not in NodegraphAPI.GetNodeTypes():
#                                     parent_item = populateChildren(node, new_item)
#                                     #new_item.setExpanded(True)
#                                     if not parent_item.getFlag():
#                                         grand_parent_item = parent_item.parent()
#                                         if not grand_parent_item:
#                                             grand_parent_item = self.invisibleRootItem()
#                                         index = grand_parent_item.indexOfChild(parent_item)
#                                         grand_parent_item.takeChild(index)
#             return item
#
#
#         root = NodegraphAPI.GetRootNode()
#         self.setItemDict({})
#         item = self.invisibleRootItem()
#         populateChildren(root, item=item)
#
#         # todo Remove empty groups
#         self.updateItemColor()
#
#         self.collapseAll()
#
#     def getViewItem(self):
#         return self.view_item
#
#     def setViewItem(self, view_item):
#         self.view_item = view_item
#
#     def getItemDict(self):
#         return self.item_dict
#
#     def setItemDict(self, item_dict):
#         self.item_dict = item_dict
#
#     def updateItemColor(self):
#         item_dict = self.getItemDict()
#         for key in item_dict:
#             item = item_dict[key]
#             node = item.getNode()
#             item.setEdited(NodegraphAPI.IsNodeEdited(node))
#             item.setViewed(NodegraphAPI.IsNodeViewed(node))
#             item.setColor()
#
#     def expandItemAndChildren(self, item, expand=True):
#         """ Expands/collapse an item and all of its children
#
#         Args:
#             item (QTreeWidgetItem): to start expanding/collapsing from
#             expand (bool): determines if this is an expand or collapse event
#             """
#         if 0 < item.childCount():
#             # expand / collapse item
#             if expand:
#                 self.expandItem(item)
#             else:
#                 self.collapseItem(item)
#
#             # recursively search children
#             for index in range(item.childCount()):
#                 child = item.child(index)
#                 if 0 < child.childCount():
#                     self.expandItemAndChildren(child, expand=expand)
#
#     def contextMenuEvent(self, event, *args, **kwargs):
#         def actionPicker(action):
#             item = self.selectedItems()
#             if item:
#                 item = item[0]
#                 if action.text() == "Go To Node":
#                     nodeutils.goToNode(NodegraphAPI.GetNode(item.data(0, QtCore.Qt.DisplayRole)))
#
#                 if action.text() == "Expand All":
#                     self.expandAll()
#
#                 if action.text() == "Collapse All":
#                     self.collapseAll()
#
#                 if action.text() == "Expand All (Children)":
#                     self.expandItemAndChildren(item, expand=True)
#
#                 if action.text() == "Collapse All (Children)":
#                     self.expandItemAndChildren(item, expand=False)
#
#         pos = event.globalPos()
#         menu = QtWidgets.QMenu(self)
#         menu.addAction("Go To Node")
#         menu.addAction("Collapse All")
#         menu.addAction("Collapse All (Children)")
#         menu.addAction("Expand All")
#         menu.addAction("Expand All (Children)")
#
#         menu.popup(pos)
#         action = menu.exec_(QtGui.QCursor.pos())
#         if action is not None:
#             actionPicker(action)
#         return QtWidgets.QTreeWidget.contextMenuEvent(self, event, *args, **kwargs)
#
#     def keyPressEvent(self, event, *args, **kwargs):
#         node = self.currentItem().getNode()
#         if event.key() == QtCore.Qt.Key_E:
#             NodegraphAPI.SetNodeEdited(node, True, exclusive=True)
#         elif event.key() == QtCore.Qt.Key_V:
#             NodegraphAPI.SetNodeViewed(node, True, exclusive=True)
#         self.updateItemColor()
#
#
# class NodeTreeItem(QtWidgets.QTreeWidgetItem):
#     def __init__(self, parent=None, name=''):
#         super(NodeTreeItem, self).__init__(parent)
#         self.viewed = False
#         self.edited = False
#         self.flag = False
#         self.setText(0, name)
#         self.default_text = self.foreground(0)
#         self.setColor()
#
#     def setFlag(self, flag):
#         self.flag = flag
#
#     def getFlag(self):
#         return self.flag
#
#     def resetTextColor(self):
#         self.setForeground(0, self.default_text)
#         pass
#
#     def getViewed(self):
#         return self.viewed
#
#     def setViewed(self, viewed):
#         self.viewed = viewed
#
#     def getEdited(self):
#         return self.edited
#
#     def setEdited(self, edited):
#         self.edited = edited
#
#     def setColor(self):
#         self.setForeground(0, QtGui.QBrush(QtGui.QColor(200, 200, 200)))
#         if self.getViewed() == True:
#             self.setForeground(0, QtGui.QBrush(QtGui.QColor(128, 128, 255)))
#         if self.getEdited() == True:
#             self.setForeground(0, QtGui.QBrush(QtGui.QColor(100, 200, 100)))
#         if self.getViewed() == True and self.getEdited() == True:
#             self.setForeground(0, QtGui.QBrush(QtGui.QColor(255, 200, 0)))
#
#     def getName(self):
#         return self.name
#
#     def setName(self, name):
#         self.name = name
#         self.setText(0, name)
#
#     def getNode(self):
#         return self.node
#
#     def setNode(self, node):
#         self.node = node
#         self.setText(1, node.getType())
#
#     def getNodeParent(self):
#         return self.node_parent
#
#     def setNodeParent(self, node_parent):
#         self.node_parent = node_parent
#
# ## how to filter/search this?
# class NodeFilterWidget(QtWidgets.QComboBox):
#     def __init__(self, parent=None):
#         super(NodeFilterWidget, self).__init__(parent)
#
#         self.setEditable(True)
#         self.main_widget = self.getMainWidget(self)
#         self.lineEdit().textChanged.connect(self.textChanged)
#         self.completer = QtWidgets.QCompleter(self)
#         # self.completer.setCompletionMode( QtWidgets.QCompleter.PopupCompletion)
#         # self.completer.setCompletionMode( QtWidgets.QCompleter.InlineCompletion)
#         # kinda like popup completion... but needs to be shown differently...
#         self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
#         # self.completer.setPopup( self.view() )
#         self.setCompleter(self.completer)
#
#         self.pFilterModel = QtCore.QSortFilterProxyModel(self)
#         node_names = self.main_widget.node_tree.getItemDict().keys()
#         self.nodeTypes = [''] + list(node_names)
#         # self.editTextChanged.connect(self.textChanged)
#         self.populate()
#
#         self.visible = False
#
#     def setVisibility(self, visibility):
#         self.visible = visibility
#
#     def getVisibility(self):
#         return self.visible
#
#     def populate(self):
#         createNewNodeWidget = self
#         model = QtGui.QStandardItemModel()
#         for i, nodeType in enumerate(self.nodeTypes):
#             item = QtGui.QStandardItem(nodeType)
#             model.setItem(i, 0, item)
#
#         createNewNodeWidget.setModel(model)
#         createNewNodeWidget.setModelColumn(0)
#
#     def setModel(self, model):
#         super(NodeFilterWidget, self).setModel(model)
#         self.pFilterModel.setSourceModel(model)
#         self.completer.setModel(self.pFilterModel)
#
#     def setModelColumn(self, column):
#         self.completer.setCompletionColumn(column)
#         self.pFilterModel.setFilterKeyColumn(column)
#         super(NodeFilterWidget, self).setModelColumn(column)
#
#     def view(self):
#         return self.completer.popup()
#
#     def getMainWidget(self, widget):
#         if isinstance(widget, UI4.Tabs.BaseTab):
#             return widget
#         else:
#             return self.getMainWidget(widget.parent())
#
#     def textChanged(self, *args, **kwargs):
#         self.main_widget.update(None)
#
#
# class NodeNameFilterWidget(NodeFilterWidget):
#     def __init__(self, parent=None):
#         super(NodeNameFilterWidget, self).__init__(parent)
#
#         node_names = self.main_widget.node_tree.getItemDict().keys()
#         self.nodeTypes = [""] + list(node_names)
#         self.populate()
#
#         self.visible = False
#
#
# class NodeTypeFilterWidget(NodeFilterWidget):
#     def __init__(self, parent=None):
#         super(NodeTypeFilterWidget, self).__init__(parent)
#
#         self.nodeTypes = [""] + NodegraphAPI.GetNodeTypes()
#         self.populate()
#
#         self.visible = False
