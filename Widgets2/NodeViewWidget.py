"""
- Needs to move to custom widget and supertool can inherit that
- Need a node interface to connect nodes into it



"""
from qtpy.QtWidgets import QVBoxLayout
from qtpy.QtCore import QModelIndex

from cgwidgets.utils import attrs
from cgwidgets.widgets import ShojiModelViewWidget

from Katana import UI4, NodegraphAPI, Utils

from Widgets2 import AbstractParametersDisplayWidget
from Utils2 import nodeutils

class NodeViewWidget(ShojiModelViewWidget):
    def __init__(self, parent=None):
        super(NodeViewWidget, self).__init__(parent)
        self.setHeaderPosition(attrs.WEST, attrs.SOUTH)
        self.setHeaderData(['name', 'type'])

        # set dynamic
        self.setDelegateType(
            ShojiModelViewWidget.DYNAMIC,
            dynamic_widget=NodeTreeDynamicWidget,
            dynamic_function=NodeTreeDynamicWidget.displayNodeParameters
        )

        self.setHeaderItemTextChangedEvent(self.nodeNameChangedEvent)
        self.setHeaderItemEnabledEvent(self.nodeDisableEvent)

        # setup attrs
        self.setMultiSelect(True)
        self.setDelegateTitleIsShown(False)

    """ GET ITEM DATA """
    def getNodeFromItem(self, item):
        node_name = item.columnData()['name']
        node = NodegraphAPI.GetNode(node_name)
        return node

    def createNewIndexFromNode(self, node, parent_index=QModelIndex()):
        """
        Creates a new index in the model for the node specified.
        Args:
            node (Node): to create index for
            parent_index (QModelIndex): index to create index as child of

        Returns (QModelIndex): of newly created index

        """
        name = node.getName()
        node_type = node.getType()
        new_index = self.insertShojiWidget(0, column_data={'name': name, 'type': node_type}, parent=parent_index)

        return new_index

    def nodeDisableEvent(self, item, enabled):
        """ enable/disable event """
        node = self.getNodeFromItem(item)
        node.setBypassed(not enabled)

    def nodeNameChangedEvent(self, item, old_value, new_value):
        node = NodegraphAPI.GetNode(old_value)
        node.setName(new_value)
        Utils.EventModule.ProcessAllEvents()
        new_name = node.getName()
        item.columnData()['name'] = new_name


class NodeTreeDynamicWidget(AbstractParametersDisplayWidget):
    """
    Simple example of overloaded class to be used as a dynamic widget for
    the ShojiModelViewWidget.
    """
    def __init__(self, parent=None):
        super(NodeTreeDynamicWidget, self).__init__(parent)
        QVBoxLayout(self)

    @staticmethod
    def displayNodeParameters(parent, widget, item):
        """
        parent (ShojiHeaderTreeView)
        widget (ShojiModelDelegateWidget)
        item (ShojiModelItem)
        """
        # ToDo Update node selected display
        #
        if item:
            this = widget.getMainWidget()
            node_list = [NodegraphAPI.GetNode(item.columnData()['name'])]
            this.populateParameters(node_list, hide_title=False)