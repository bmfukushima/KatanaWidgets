
from qtpy.QtWidgets import (
    QLabel, QVBoxLayout, QWidget
)

from qtpy.QtCore import Qt, QEvent

from cgwidgets.utils import attrs
from cgwidgets.widgets import TansuModelViewWidget, TansuHeaderTreeView, StringInputWidget

try:
    from Katana import UI4, NodegraphAPI
    from Widgets2 import AbstractSuperToolEditor, NodeTypeListWidget
    from Utils2 import nodeutils
except (ImportError, ModuleNotFoundError) as e:
    pass

# class NodeTreeEditor(AbstractSuperToolEditor):
#     def __init__(self, parent, node):
#         super(NodeTreeEditor, self).__init__(parent, node)
#         """
#         Class:
#         NodeTreeEditor --|> AbstractSuperToolEditor
#             | --
#         """
class NodeTreeEditor(QWidget):
    """
    The top level widget for the editor.  This is here to encapsulate
    the main widget with a stretch box...

    Attributes:
        should_update (bool): determines if this tool should have
            its GUI updated or not during the next event idle process.

    """
    def __init__(self, parent, node):
        super(NodeTreeEditor, self).__init__(parent)
        # set up attrs
        self.node = node

        self._node_type = "<multi>"
        # setup layout
        QVBoxLayout(self)
        self.layout().setAlignment(Qt.AlignTop)

        # create node tree
        self._node_tree = NodeTreeMainWidget(parent=self, node=self.node)

        # add tree to layout
        self.layout().addWidget(self.nodeTree())

    """ PROPERTIES """
    def nodeTree(self):
        return self._node_tree

    def setNodeTree(self, _node_tree):
        self._node_tree = _node_tree

    def nodeType(self):
        return self._node_type

    def setNodeType(self, _node_type):
        self._node_type = _node_type


class NodeTreeMainWidget(TansuModelViewWidget):
    def __init__(self, parent=None, node=None):
        super(NodeTreeMainWidget, self).__init__(parent)
        self.node = node

        # setup view
        view = NodeTreeViewWidget(self)
        # setup header
        self.setHeaderViewWidget(view)
        self.setHeaderPosition(attrs.WEST, attrs.SOUTH)
        self.setHeaderData(['name', 'type'])

        # set dynamic
        self.setDelegateType(
            TansuModelViewWidget.DYNAMIC,
            dynamic_widget=NodeTreeDynamicWidget,
            dynamic_function=NodeTreeDynamicWidget.updateGUI
        )

        header_delegate_widget = NodeTreeHeaderDelegate(self)
        self.setHeaderDelegateWidget(header_delegate_widget)

        self.setHeaderItemDropEvent(self.nodeMovedEvent)
        header_delegate_widget.setUserFinishedEditingEvent(self.delegateFinishedEditing)

        # set hotkey to activate
        # TODO Key List
        # 'd' toggle?
        self.TOGGLE_DELEGATE_KEYS = [Qt.Key_T, Qt.Key_1]

        print(self, self.node)

    def getSelectedIndex(self):
        """
        Returns the currently selected item
        """
        indexes = self.getAllSelectedIndexes()
        if len(indexes) == 0: return None
        else: return indexes[0]

    def getParentIndex(self):
        index = self.getSelectedIndex()
        if index:
            node_name = index.internalPointer().columnData()["name"]
            node = NodegraphAPI.GetNode(node_name)
            if node.getType() != "Group":
                return index.parent()
            else:
                return index

    def getNodeFromIndex(self, index):
        """
        Returns the currently selected node in this widget
        """
        if index:
            node_name = index.internalPointer().columnData()["name"]
            node = NodegraphAPI.GetNode(node_name)
        else:
            return self.node

        return node

    def getParentNode(self):
        """
        Returns the node that the newly created node should be parented to.
        """

    def delegateFinishedEditing(self, widget, value):
        # TODO delegateFinishedEditing
        # get current node
        # todo need to set this up
        # get node
        parent_index = self.getParentIndex()
        parent_node = self.getNodeFromIndex(parent_index)

        # get node type to create
        node_type = value

        # create node
        # # check if node type in nodes list...
        node_list = NodegraphAPI.GetNodeTypes()

        if node_type in node_list:
            # # create node
            new_node = NodegraphAPI.CreateNode(str(node_type), parent_node)

            name = str(new_node.getName())
            node_type = new_node.getType()

            # TODO Wire Node after creation.
            nodeutils.createIOPorts(new_node, force_create=True, connect=False)
            #insertNode(new_node, parent_node)

            # create new item
            self.insertTansuWidget(0, column_data={'name': name, 'type': node_type}, parent=parent_index)

            # reset widget
            widget.setText('')
            widget.hide()
        else:
            return

    def nodeMovedEvent(self, row, indexes, parent):
        """
        Run when the user does a drop.  This is triggered on the dropMimeData funciton
        in the model.

        Args:
            indexes (list): of TansuModelItems
            parent (TansuModelItem): parent item that was dropped on

        """
        # TODO DROP EVENT
        print("---- DROP EVENT ----")
        print(row, indexes, parent)


class NodeTreeHeaderDelegate(NodeTypeListWidget):
    def __init__(self, parent=None):
        super(NodeTreeHeaderDelegate, self).__init__(parent)


class NodeTreeViewWidget(TansuHeaderTreeView):
    def __init__(self, parent=None):
        super(NodeTreeViewWidget, self).__init__(parent)


class NodeTreeDynamicWidget(QWidget):
    """
    Simple example of overloaded class to be used as a dynamic widget for
    the TansuModelViewWidget.
    """
    def __init__(self, parent=None):
        super(NodeTreeDynamicWidget, self).__init__(parent)
        QVBoxLayout(self)
        self.label = QLabel('init')
        self.layout().addWidget(self.label)

    @staticmethod
    def updateGUI(parent, widget, item):
        """
        widget (TansuModelDelegateWidget)
        item (TansuModelItem)
        """
        # ToDo Update node selected display
        #
        if item:
            print ('----------------------------')
            #print(parent, widget, item)
            print(item.columnData())
            name = parent.model().getItemName(item)
            widget.setName(name)
            widget.getMainWidget().label.setText(name)


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication, QLabel, QVBoxLayout
    from qtpy.QtGui import QCursor
    from cgwidgets.widgets import TansuModelViewWidget
    app = QApplication(sys.argv)

    w = NodeTreeEditor(None, None)
    w.resize(500, 500)

    w.show()
    w.move(QCursor.pos())
    sys.exit(app.exec_())


import sys
from qtpy.QtWidgets import QApplication, QLabel, QVBoxLayout
from qtpy.QtGui import QCursor
from cgwidgets.widgets import TansuModelViewWidget
w = NodeTreeEditor(None, None)
w.resize(500, 500)

w.show()
w.move(QCursor.pos())