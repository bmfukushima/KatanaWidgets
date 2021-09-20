
"""
ToDo:
    *   Drag/Drop onto none group nodes?
    *   Drag/Drop multiple nodes into nodegraph
"""
from qtpy.QtWidgets import QVBoxLayout
from qtpy.QtCore import Qt, QEvent, QModelIndex, QByteArray

from cgwidgets.utils import getWidgetAncestor
from cgwidgets.widgets import ShojiModelViewWidget, StringInputWidget, NodeTypeListWidget
from cgwidgets.views import AbstractDragDropTreeView
from cgwidgets.interface import AbstractNodeInterfaceAPI as aniAPI

from Katana import UI4, NodegraphAPI, Utils
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

        self._node_type = "<multi>"
        # setup layout
        QVBoxLayout(self)

        # create node tree
        self._node_tree = NodeTreeMainWidget(parent=self, node=self.node)

        # add tree to layout
        self.layout().addWidget(self.nodeTree())
        self.insertResizeBar()

    """ PROPERTIES """
    def nodeTree(self):
        return self._node_tree

    def setNodeTree(self, _node_tree):
        self._node_tree = _node_tree

    def nodeType(self):
        return self._node_type

    def setNodeType(self, _node_type):
        self._node_type = _node_type


class NodeTreeMainWidget(NodeViewWidget):
    """

    Attributes:
        node (NodeTreeNode): This node
    """
    def __init__(self, parent=None, node=None):
        super(NodeTreeMainWidget, self).__init__(parent)
        # setup node

        self._node = node
        # setup view
        view = NodeTreeViewWidget(self)

        # setup header
        self.setHeaderViewWidget(view)

        # setup shoji style
        self.setMultiSelect(True)
        # self.setHeaderItemIsDroppable(True)

        # events
        # self.setHeaderItemMimeDataFunction(self.setDragMimeData)
        self.setHeaderItemDragStartEvent(self.nodePickupEvent)
        self.setHeaderItemDropEvent(self.nodeMovedEvent)
        self.setHeaderItemDeleteEvent(self.nodeDeleteEvent)

        # node create widget
        self._node_create_widget = NodeTreeHeaderDelegate(self)
        self.addHeaderDelegateWidget([], self._node_create_widget, modifier=Qt.NoModifier, focus=True)
        self._node_create_widget.show()
        self._node_create_widget.setUserFinishedEditingEvent(self.createNewNode)
        self._node_create_widget.setFixedHeight(getFontSize() * 2)

    def showEvent(self, event):
        """ refresh UI on show event """
        self.clearModel()
        for node in self.node().getChildren():
            self.populate(node)
        return NodeViewWidget.showEvent(self, event)

    def populate(self, node, parent_index=QModelIndex()):
        # create child item
        # create new item
        new_index = self.createNewIndexFromNode(node, parent_index=parent_index)
        new_item = new_index.internalPointer()

        # setup drop for new item
        if not hasattr(node, 'getChildren'):
            new_item.setIsDroppable(False)

        # recurse through children
        else:
            new_item.setIsDroppable(True)
            children = node.getChildren()
            if 0 < len(children):
                for grand_child in children:
                    self.populate(grand_child, parent_index=new_index)

    """ UTILS """
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

    @staticmethod
    def isNodeDescendantOf(child, ancenstor):
        parent = child.parent()
        if parent:
            if parent == ancenstor:
                return True
            else:
                return NodeTreeMainWidget.isNodeDescendantOf(child, ancenstor)
        else:
            return False

    """ PROPERTIES """
    def node(self):
        return self._node

    def setNode(self, node):
        self._node = node

    """ EVENTS """
    # def setDragMimeData(self, mimedata, items):
    #     """ Adds the mimedata to the drag event
    #
    #     Args:
    #         mimedata (QMimedata): from dragEvent
    #         items (list): of NodeViewWidgetItem
    #     Note:
    #         This only adds the data for nodes... not for parameters, how to handle?"""
    #     nodes = []
    #     python_text = []
    #     for item in items:
    #
    #         if item.type() == NODE:
    #             node_name = item.getName()
    #             nodes.append(node_name)
    #
    #             python_text.append("NodegraphAPI.GetNode(\"{NODE_NAME}\")".format(NODE_NAME=node_name))
    #
    #     nodes_ba = QByteArray()
    #     nodes_ba.append(", ".join(nodes))
    #
    #     python_text_ba = QByteArray()
    #     python_text_ba.append(", ".join(python_text))
    #
    #     listbox_ba = QByteArray()
    #     listbox_ba.append("0")
    #
    #     mimedata.setData("listbox/items", listbox_ba)
    #     mimedata.setData("nodegraph/nodes", nodes_ba)
    #     mimedata.setData("python/text", python_text_ba)
    #     return mimedata
        #nodegraph / nodes == FaceSetCreate, FaceSetCreate1
        #python / text == NodegraphAPI.GetNode("FaceSetCreate"), NodegraphAPI.GetNode("FaceSetCreate1")

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
            if hasattr(new_node, 'getChildren'):
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
                        group_item = self.model().getRootItem()

            else:
                group_item = self.model().getRootItem()
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

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.DragEnter, QEvent.DragMove, QEvent.Drop):
            if event.type() != QEvent.Drop:
                event.acceptProposedAction()
            else:
                node_graph = getCurrentTab()
                parent_node = node_graph.getEnteredGroupNode()
                node_list = []

                for count, index in enumerate(self.getAllSelectedIndexes()):
                    item = index.internalPointer()
                    node = item.node()
                    node_list.append(node)

                    # disconnect node
                    nodeutils.disconnectNode(node, input=True, output=True, reconnect=True)

                    # create ports
                    nodeutils.createIOPorts(node, force_create=False, connect=True)

                    # reparent
                    node.setParent(parent_node)

                    NodegraphAPI.SetNodePosition(node, (0, count * 50))

                    # update GUI
                    self.deleteItem(item)

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
            parent_widget = getWidgetAncestor(self, NodeTreeMainWidget)
            parent_node = parent_widget.node()
            for node_name in nodes_list:
                # get node
                node = NodegraphAPI.GetNode(node_name)
                nodeutils.createIOPorts(node, in_port=True, out_port=True, connect=False, force_create=False)

                # disconnect node and reparent
                nodeutils.disconnectNode(node, input=True, output=True, reconnect=False)
                node.setParent(parent_node)

                # create new model item
                root_index = parent_widget.model().getIndexFromItem(parent_widget.rootItem())
                new_index = parent_widget.createNewIndexFromNode(node, root_index)
                #new_index = parent_widget.insertShojiWidget(0, column_data={'name': node.getName(), 'type': node.getType(), "object_type": NODE}, parent=root_index)

                # setup drop handlers
                if not hasattr(node, 'getChildren'):
                    new_item = new_index.internalPointer()
                    new_item.setIsDroppable(False)
                else:
                    new_item = new_index.internalPointer()
                    new_item.setIsDroppable(True)
            # reconnect all nodes inside of the group
            node_list = parent_widget.getChildNodeListFromItem(parent_widget.rootItem())
            nodeutils.connectInsideGroup(node_list, parent_node)

        return AbstractDragDropTreeView.dropEvent(self, event)



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