"""
- Needs to move to custom widget and supertool can inherit that
- Need a node interface to connect nodes into it



"""
from qtpy.QtWidgets import (
    QLabel, QVBoxLayout, QWidget
)

from qtpy.QtCore import Qt, QEvent

from cgwidgets.utils import attrs, getWidgetAncestor
from cgwidgets.widgets import ShojiModelViewWidget, StringInputWidget, NodeTypeListWidget
from cgwidgets.views import AbstractDragDropTreeView
from cgwidgets.interface import AbstractNodeInterfaceAPI as aniAPI



from Katana import UI4, NodegraphAPI, Utils
from Widgets2 import AbstractSuperToolEditor, NodeViewWidget
from Utils2 import nodeutils


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
    def __init__(self, parent=None, node=None):
        super(NodeTreeMainWidget, self).__init__(parent)
        # setup node

        self.node = node
        # setup view
        view = NodeTreeViewWidget(self)

        # setup header
        self.setHeaderViewWidget(view)

        # setup shoji style
        self.main_widget.setMultiSelect(True)

        # events
        self.setHeaderItemDropEvent(self.nodeMovedEvent)
        self.setHeaderItemDeleteEvent(self.nodeDeleteEvent)

        # node create widget
        self.node_create_widget = NodeTreeHeaderDelegate(self)
        self.addHeaderDelegateWidget([Qt.Key_Q, Qt.Key_Tab], self.node_create_widget, modifier=Qt.NoModifier, focus=True)
        self.node_create_widget.setUserFinishedEditingEvent(self.createNewNode)

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
                node = self.node
        else:
            node = self.node

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
            #new_index = self.insertShojiWidget(0, column_data={'name': name, 'type': node_type}, parent=parent_index)
            new_item = new_index.internalPointer()
            if not hasattr(new_node, 'getChildren'):
                new_item.setIsDropEnabled(False)
            # wire node
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
                parent_node = self.node

            # get node list
            node_list = self.getChildNodeListFromItem(group_item)
            nodeutils.connectInsideGroup(node_list, parent_node)

            # reset widget
            widget.setText('')
            widget.hide()

            # TODO Set focus back on header?
            header_view_widget = self.headerViewWidget()
            header_view_widget.setFocus()
        else:
            return

    def nodeMovedEvent(self, data, items_dropped, model, row, parent):
        """
        Run when the user does a drop.  This is triggered on the dropMimeData funciton
        in the model.

        Args:
            indexes (list): of ShojiModelItems
            parent (ShojiModelItem): parent item that was dropped on

        """
        # disconnect... not working... input ports not reconnect to group send?

        # get parent node
        parent_node = NodegraphAPI.GetNode(parent.columnData()['name'])
        # if root
        if parent.columnData()["name"] == 'root':
            parent_node = self.node

        # drop items
        for item in items_dropped:
            # get node
            node = NodegraphAPI.GetNode(item.columnData()['name'])

            # disconnect node
            nodeutils.disconnectNode(node, input=True, output=True, reconnect=True)

            # reparent
            node.setParent(parent_node)

        # reconnect node to new parent
        node_list = self.getChildNodeListFromItem(parent)
        nodeutils.connectInsideGroup(node_list, parent_node)

    def nodeDeleteEvent(self, item):
        """ delete event """
        node = self.getNodeFromItem(item)
        nodeutils.disconnectNode(node, input=True, output=True, reconnect=True)
        node.delete()

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
            nodes_list = mimedata.data('nodegraph/nodes').data().split(',')
            parent_widget = getWidgetAncestor(self, NodeTreeMainWidget)
            parent_node = parent_widget.node
            for node_name in nodes_list:
                # get node
                node = NodegraphAPI.GetNode(node_name)

                # disconnect node and reparent
                nodeutils.disconnectNode(node, input=True, output=True, reconnect=False)
                node.setParent(parent_node)

                # create new model item
                root_index = parent_widget.model().getIndexFromItem(parent_widget.rootItem())
                new_index = parent_widget.insertShojiWidget(0, column_data={'name': node.getName(), 'type': node.getType()}, parent=root_index)

                # setup drop handlers
                if not hasattr(node, 'getChildren'):
                    new_item = new_index.internalPointer()
                    new_item.setIsDropEnabled(False)

            # reconnect all nodes inside of the group
            node_list = parent_widget.getChildNodeListFromItem(parent_widget.rootItem())
            nodeutils.connectInsideGroup(node_list, parent_node)

        return AbstractDragDropTreeView.dropEvent(self, event)



if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication, QLabel, QVBoxLayout
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