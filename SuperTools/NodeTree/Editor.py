from qtpy.QtWidgets import QVBoxLayout
from qtpy.QtCore import Qt, QEvent, QModelIndex, QByteArray
from qtpy.QtGui import QClipboard

from cgwidgets.utils import getWidgetAncestor
from cgwidgets.widgets import NodeTypeListWidget
from cgwidgets.views import AbstractDragDropTreeView, AbstractDragDropModelDelegate
from cgwidgets.interface import AbstractNodeInterfaceAPI as aniAPI

from Katana import UI4, NodegraphAPI, Utils, KatanaFile
from Widgets2 import AbstractSuperToolEditor, NodeViewWidget
from Utils2 import nodeutils, getFontSize, NODE, PARAM, getCurrentTab


class NodeTreeEditor(AbstractSuperToolEditor):
    def __init__(self, parent, node):
        super(NodeTreeEditor, self).__init__(parent, node)
        """
        Class:
        NodeTreeEditor --|> AbstractSuperToolEditor
            | --
        """

        # self._node_type = "<multi>"
        # setup layout
        QVBoxLayout(self)

        # create node tree
        self._node_tree = NodeTreeMainWidget(parent=self, node=self.node())

        # add tree to layout
        self.layout().addWidget(self.nodeTree())
        self.insertResizeBar()

    """ WIDGETS """
    def nodeTree(self):
        return self._node_tree


class NodeTreeMainWidget(NodeViewWidget):
    """

    Attributes:
        node (NodeTreeNode): This node
    """
    def __init__(self, parent=None, node=None):
        super(NodeTreeMainWidget, self).__init__(parent)
        # setup attrs
        self._nodes_to_be_copied = ""

        # setup node
        self._node = node
        self.rootItem().setArg("node", node.getName())

        # setup view
        view = NodeTreeViewWidget(self)

        # setup header
        self.setHeaderViewWidget(view)

        # flags
        self.setMultiSelect(True)
        self.setHeaderItemIsDraggable(True)
        self.setHeaderItemIsCopyable(True)

        # events
        self.setHeaderItemDragStartEvent(self.nodePickupEvent)
        self.setHeaderItemDropEvent(self.nodeMovedEvent)
        self.setHeaderItemDeleteEvent(self.nodeDeleteEvent)
        self.setHeaderItemCopyEvent(self.copyNodes)
        self.setHeaderItemPasteEvent(self.pasteNodes)
        self.setHeaderItemDuplicateEvent(self.duplicateNodes)
        self.setHeaderItemCutEvent(self.cutNodes)

        # node create widget
        self._node_create_widget = NodeTreeHeaderDelegate(self)
        self.addHeaderDelegateWidget([], self._node_create_widget, modifier=Qt.NoModifier, focus=True)
        self._node_create_widget.show()
        self._node_create_widget.setUserFinishedEditingEvent(self.createNewNode)
        self._node_create_widget.setFixedHeight(getFontSize() * 2)

        # populate items
        self.clearModel()
        for node in self.node().getChildren():
            self.populate(node)

        self.addContextMenuEvent("Go To Node", self.goToNode)

    # def showEvent(self, event):
    #     """ refresh UI on show event """
    #     self.clearModel()
    #     for node in self.node().getChildren():
    #         self.populate(node)
    #     return NodeViewWidget.showEvent(self, event)

    def populate(self, node, parent_index=QModelIndex(), row=0):
        # create child item
        # create new item
        new_index = self.createNewIndexFromNode(node, parent_index=parent_index, row=row)
        new_item = new_index.internalPointer()

        # setup drop for new item
        if nodeutils.isContainerNode(node):
            new_item.setIsDroppable(True)
            children = node.getChildren()
            if 0 < len(children):
                for row, grand_child in enumerate(children):
                    self.populate(grand_child, parent_index=new_index, row=row)
        else:
            new_item.setIsDroppable(False)

    """ UTILS """
    def goToNode(self, index, indexes):
        node = index.internalPointer().node()
        nodeutils.goToNode(node)

    def removeEventFilterFromNodeGraphs(self):
        """ Removes the current event filter from all of the NodeGraphs"""
        nodegraph_tabs = UI4.App.Tabs.GetTabsByType("Node Graph")
        for nodegraph_tab in nodegraph_tabs:
            nodegraph_tab.getNodeGraphWidget().removeEventFilter(self)

    """ GET ITEM DATA """
    def getSelectedIndex(self):
        """Returns the currently selected item"""
        indexes = self.getAllSelectedIndexes()
        if len(indexes) == 0: return None
        else: return indexes[0]

    def getParentIndex(self):
        """Gets the current parent index for node creation"""
        index = self.getSelectedIndex()
        if index:
            node_name = index.internalPointer().columnData()["name"]
            node = NodegraphAPI.GetNode(node_name)
            if node.getType() != "Group":
                return index.parent()
            else:
                return index

    def getParentNodeFromIndex(self, index):
        """Returns the currently selected node in this widget"""
        if index:
            item = index.internalPointer()

            # top level group
            if item:
                node_name = index.internalPointer().columnData()["name"]
                node = NodegraphAPI.GetNode(node_name)
            # top level, NOT group
            else:
                node = self.node()
        else:
            node = self.node()

        return node

    def getChildNodeListFromItem(self, item):
        """
        Gets all of the node children from the specified item

        Returns (list) of nodes
        """
        # get node list
        children = item.children()
        node_name_list = [child.columnData()['name'] for child in children]
        node_list = [NodegraphAPI.GetNode(node) for node in node_name_list]

        return node_list

    def getAllSelectedNodes(self):
        node_list = []
        for index in self.getAllSelectedIndexes():
            node_list.append(index.internalPointer().node())
        return node_list

    """ PROPERTIES """
    def node(self):
        return self._node

    def setNode(self, node):
        self._node = node

    """ COPY / PASTE"""
    def insertNode(self, node, parent_node, parent_index=None, row=0):
        if not parent_index:
            parent_index = self.getIndexFromItem(self.rootItem())
        nodeutils.createIOPorts(node, in_port=True, out_port=True, connect=False, force_create=False)

        # disconnect node and reparent
        nodeutils.disconnectNode(node, input=True, output=True, reconnect=False)
        node.setParent(parent_node)

        # create new model item
        new_index = self.createNewIndexFromNode(node, parent_index=parent_index, row=row)

        # setup drop handlers
        if nodeutils.isContainerNode(node):
            new_item = new_index.internalPointer()
            new_item.setIsDroppable(True)
            # todo update group node dropping
            """ Right now this is merely looking at all the children and dumping them into a group
            - This should be smarter.  It does not preserve connection order.
            - Could potentially search from the input port, down to the output port.
            - Look for nodes with multiple connections, and flag them as broken
            - Lock internal contents?"""
            for child_node in node.getChildren():
                self.insertNode(child_node, node, parent_index=new_index)
        else:
            new_item = new_index.internalPointer()
            new_item.setIsDroppable(False)

    def copyNodes(self, items):
        """ Copies all of the selected nodes.

        Note:
            If items are in different groups, nodes, cannot be copied,
            and the operation will be aborted.

        Returns (bool): True if succesful in copy, False if failed
            """
        # nodes = self.getAllSelectedNodes()
        nodes = [item.node() for item in items]
        try:
            element = NodegraphAPI.BuildNodesXmlIO(nodes, forcePersistant=True)
            node_text = NodegraphAPI.WriteKatanaString(element, compress=False, archive=False)
            self._nodes_to_be_copied = node_text
            return True
        except ValueError:
            print("Nodes not in same group, copy aborted because I\'m to lazy to write the code for it")
            return False

    def cutNodes(self, items):
        if self.copyNodes(items):
            for item in items:
                self.deleteItem(item, event_update=True)

    def duplicateNodes(self, copied_items, duplicated_items):
        self.copyNodes(copied_items)

        text_nodes = KatanaFile.Paste(self._nodes_to_be_copied, NodegraphAPI.GetRootNode())

        # create new indexes / update nodes parent
        for item, node in zip(duplicated_items, text_nodes):
            # get/update attrs
            parent_node = item.parent().node()
            node.setParent(parent_node)
            item.setArg("node", node.getName())
            item.setArg("name", node.getName())

            # update group node
            if nodeutils.isContainerNode(node):
                parent_index = self.model().getIndexFromItem(item.parent())
                self.populate(node, parent_index, row=item.row())
                self.deleteItem(item, event_update=False)

            # connect internals
            node_list = self.getChildNodeListFromItem(item.parent())
            nodeutils.connectInsideGroup(node_list, parent_node)

    def pasteNodes(self, copied_items, pasted_items, parent_item):
        # paste node XML
        parent_node = parent_item.node()
        text_nodes = KatanaFile.Paste(self._nodes_to_be_copied, parent_node)

        # create new indexes / update nodes parent
        for item, node in zip(pasted_items, text_nodes):
            # get/update attrs
            node.setParent(parent_node)
            item.setArg("node", node.getName())
            item.setArg("name", node.getName())

            # update group
            if nodeutils.isContainerNode(node):
                parent_index = self.model().getIndexFromItem(parent_item)
                self.populate(node, parent_index, row=item.row())
                self.deleteItem(item, event_update=False)

        # connect internals
        node_list = self.getChildNodeListFromItem(parent_item)
        nodeutils.connectInsideGroup(node_list, parent_node)

    """ EVENTS """
    def createNewNode(self, widget, value):
        """ User creating new node """
        # get node
        parent_index = self.getParentIndex()
        parent_node = self.getParentNodeFromIndex(parent_index)

        # get node type to create
        node_type = value

        # create node
        # # check if node type in nodes list...
        all_nodes = NodegraphAPI.GetNodeTypes()

        if node_type in all_nodes:
            # # create node
            new_node = NodegraphAPI.CreateNode(str(node_type), parent_node)

            # create new item
            new_index = self.createNewIndexFromNode(new_node, parent_index=parent_index)
            new_item = new_index.internalPointer()

            # set up node
            # container
            if nodeutils.isContainerNode(new_node):
                new_item.setIsDroppable(True)
                nodeutils.createIOPorts(new_node, force_create=False, connect=True)
            # standard
            else:
                new_item.setIsDroppable(False)
                nodeutils.createIOPorts(new_node, force_create=False, connect=False)

            # get children / parent_node
            if parent_index:
                item = parent_index.internalPointer()
                # if index exists
                if item:
                    group_item = parent_index.internalPointer()
                # special case for root
                else:
                    group_item = parent_index.internalPointer()
                    if not group_item:
                        group_item = self.model().rootItem()

            else:
                group_item = self.model().rootItem()
                parent_node = self.node()

            # get node list
            node_list = self.getChildNodeListFromItem(group_item)
            nodeutils.connectInsideGroup(node_list, parent_node)

            # reset widget
            widget.setText('')
            # widget.hide()

            # TODO Set focus back on header?
            # header_view_widget = self.headerViewWidget()
            # header_view_widget.setFocus()
        else:
            return

    def nodePickupEvent(self, items, model):
        # install all event filters
        nodegraph_tabs = UI4.App.Tabs.GetTabsByType("Node Graph")
        for nodegraph_tab in nodegraph_tabs:
            nodegraph_tab.getNodeGraphWidget().installEventFilter(self)

    def nodeMovedEvent(self, data, items_dropped, model, row, parent):
        """
        Run when the user does a drop.  This is triggered on the dropMimeData funciton
        in the model.

        Args:
            indexes (list): of ShojiModelItems
            parent (ShojiModelItem): parent item that was dropped on

        """
        # get parent node
        parent_node = NodegraphAPI.GetNode(parent.columnData()['name'])
        # if root
        if parent.columnData()["name"] == 'root':
            parent_node = self.node()

        # drop items
        for item in items_dropped:
            # get node
            node = NodegraphAPI.GetNode(item.columnData()['name'])

            # disconnect node
            nodeutils.disconnectNode(node, input=True, output=True, reconnect=True)

            # create ports
            nodeutils.createIOPorts(node, force_create=False, connect=True)

            # reparent
            node.setParent(parent_node)

        # reconnect node to new parent
        node_list = self.getChildNodeListFromItem(parent)
        nodeutils.connectInsideGroup(node_list, parent_node)

        # remove event filters
        self.removeEventFilterFromNodeGraphs()

    def nodeDeleteEvent(self, item):
        """ delete event """
        node = self.getNodeFromItem(item)
        nodeutils.disconnectNode(node, input=True, output=True, reconnect=True)
        node.delete()

    # def keyPressEvent(self, event):
    #     modifiers = event.modifiers()
    #     if modifiers == Qt.ControlModifier:
    #         if event.key() == Qt.Key_C:
    #             self.copyNodes()
    #         if event.key() == Qt.Key_V:
    #             self.pasteNodes()
    #         if event.key() == Qt.Key_X:
    #             self.cutNodes()
    #         if event.key() == Qt.Key_D:
    #             self.duplicateNodes()
    #     return NodeViewWidget.keyPressEvent(self, event)

    def eventFilter(self, obj, event):
        """ Drag/Drop Handler from NodeTree into NodeGraph"""
        if event.type() in (QEvent.DragEnter, QEvent.DragMove, QEvent.Drop):
            if event.type() != QEvent.Drop:
                event.acceptProposedAction()
            else:
                node_graph = getCurrentTab()
                parent_node = node_graph.getEnteredGroupNode()
                node_list = []

                for count, (node, item) in enumerate(
                        zip(self.getAllSelectedNodes(), self.getAllSelectedItems())
                ):
                    node_list.append(node)

                    # disconnect node
                    nodeutils.disconnectNode(node, input=True, output=True, reconnect=True)

                    # create ports
                    nodeutils.createIOPorts(node, force_create=False, connect=True)

                    # reparent/position
                    node.setParent(parent_node)
                    NodegraphAPI.SetNodePosition(node, (0, count * 50))

                    # update GUI
                    try:
                        self.deleteItem(item)
                    except ValueError:
                        # item already deleted, ie was a child of a group
                        pass

                # float nodes
                node_graph.floatNodes(node_list)
                self.removeEventFilterFromNodeGraphs()
            return True

        return False

    """ WIDGETS """
    def nodeCreateWidget(self):
        return self._node_create_widget


class NodeTreeHeaderDelegate(NodeTypeListWidget):
    def __init__(self, parent=None):
        super(NodeTreeHeaderDelegate, self).__init__(parent)


class NodeTreeViewWidget(AbstractDragDropTreeView):
    def __init__(self, parent=None):
        super(NodeTreeViewWidget, self).__init__(parent)
        delegate = NodeTreeViewItemDelegateWidget(self)
        self.setItemDelegate(delegate)
        #self.setupCustomDelegate()

    def dragEnterEvent(self, event):
        mimedata = event.mimeData()
        if mimedata.hasFormat('nodegraph/nodes'):
            event.accept()
        return AbstractDragDropTreeView.dragEnterEvent(self, event)

    def dropEvent(self, event):
        """
        This will handle all drops into the view from the Nodegraph

        Alot of this is copy/paste from nodeMovedEvent
        """
        mimedata = event.mimeData()
        if mimedata.hasFormat('nodegraph/nodes'):
            nodes_list_bytes = mimedata.data('nodegraph/nodes').data()
            nodes_list = nodes_list_bytes.decode("utf-8").split(',')
            node_tree_widget = getWidgetAncestor(self, NodeTreeMainWidget)
            parent_node = node_tree_widget.node()
            for node_name in nodes_list:
                # get node
                node = NodegraphAPI.GetNode(node_name)

                node_tree_widget.insertNode(node, parent_node)

            # reconnect all nodes inside of the group
            node_list = node_tree_widget.getChildNodeListFromItem(node_tree_widget.rootItem())
            nodeutils.connectInsideGroup(node_list, parent_node)

        return AbstractDragDropTreeView.dropEvent(self, event)


class NodeTreeViewItemDelegateWidget(AbstractDragDropModelDelegate):
    """ Delegate for the NodeTreeViewItem

    This will suppress the "type" column, so that users can't inadvertently try to change
    the type.  Which will actually do a name change.
    """
    def __init__(self, parent=None):
        super(NodeTreeViewItemDelegateWidget, self).__init__(parent)

    def createEditor(self, parent, option, index):
        if index.column() == 0:
            return AbstractDragDropModelDelegate.createEditor(self, parent, option, index)
        else:
            return


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication, QLabel
    from qtpy.QtGui import QCursor
    from cgwidgets.widgets import ShojiModelViewWidget
    app = QApplication(sys.argv)

    w = NodeTreeEditor(None, None)
    w.resize(500, 500)

    w.show()
    w.move(QCursor.pos())
    sys.exit(app.exec_())


# import sys
# from qtpy.QtWidgets import QApplication, QLabel, QVBoxLayout
# from qtpy.QtGui import QCursor
# from cgwidgets.widgets import ShojiModelViewWidget
# w = NodeTreeEditor(None, None)
# w.resize(500, 500)
#
# w.show()
# w.move(QCursor.pos())