"""
- Needs to move to custom widget and supertool can inherit that
- Need a node interface to connect nodes into it
"""
from qtpy.QtWidgets import QVBoxLayout
from qtpy.QtCore import QModelIndex, QByteArray

from cgwidgets.settings import attrs
from cgwidgets.widgets import ShojiModelViewWidget, ShojiModelItem

from Katana import UI4, NodegraphAPI, Utils

from Widgets2 import AbstractParametersDisplayWidget
from Utils2 import nodeutils, paramutils, NODE, PARAM


class NodeViewWidgetItem(ShojiModelItem):
    """
    name (str): name given to this event by the user
    event_type (str): katana event type
    script (path): path on disk to .py file to run as script
    args (dict): dictionary of all the args
    index (int): current index that this item is holding in the model
    enabled (bool): If this event should be enabledd/disabled
    """

    def __init__(self, name=None):
        super(NodeViewWidgetItem, self).__init__(name)
        self.setArg("name", name)

    def node(self):
        return NodegraphAPI.GetNode(self.getArg("node"))

    def param(self):
        if self.objectType() == PARAM:
            node = NodegraphAPI.getNode(self.getArg("node"))
            param_path = ".".join(self.getArg("param").split(".")[1:])
            return node.getParameter(param_path)

    def objectType(self):
        return self.getArg("object_type")

    def type(self):
        return self.getArg("type")


class NodeViewWidget(ShojiModelViewWidget):
    """ The node view widget allows users to view nodes/parameters
    Each item in the view represents one node or parameter."""
    def __init__(self, parent=None):
        super(NodeViewWidget, self).__init__(parent)
        self.setItemType(NodeViewWidgetItem)
        self.setHeaderPosition(attrs.WEST, attrs.SOUTH)
        self.setHeaderData(["name", "type"])

        # set dynamic
        self.setDelegateType(
            ShojiModelViewWidget.DYNAMIC,
            dynamic_widget=NodeTreeDynamicWidget,
            dynamic_function=NodeTreeDynamicWidget.displayNodeParameters
        )

        self.setHeaderItemTextChangedEvent(self.objectNameChangedEvent)
        self.setHeaderItemEnabledEvent(self.objectDisableEvent)

        # setup attrs
        self.setMultiSelect(True)
        self.setDelegateTitleIsShown(False)

    """ GET ITEM DATA """
    def getNodeFromItem(self, item):
        node_name = item.columnData()["name"]
        node = NodegraphAPI.GetNode(node_name)
        return node


    def createNewIndexFromNode(self, node, parent_index=QModelIndex(), row=0):
        """
        Creates a new index in the model for the node specified.
        Args:
            node (Node): to create index for
            parent_index (QModelIndex): index to create index as child of

        Returns (QModelIndex): of newly created index

        """
        name = node.getName()
        node_type = node.getType()
        new_index = self.insertShojiWidget(row, column_data={"name": name, "type": node_type, "object_type":NODE, "node": name}, parent=parent_index)

        return new_index

    def createNewIndexFromParam(self, param, parent_index=QModelIndex()):
        """
        Creates a new index in the model for the node specified.
        Args:
            node (Node): to create index for
            parent_index (QModelIndex): index to create index as child of

        Returns (QModelIndex): of newly created index

        """
        new_index = self.insertShojiWidget(
            0,
            column_data={
                "name": paramutils.getParamDisplayName(param),
                "type": param.getType(),
                "node": param.getNode().getName(),
                "object_type": PARAM,
            },
            parent=parent_index,
            is_enableable=False)

        return new_index

    def objectDisableEvent(self, item, enabled):
        """ enable/disable event """
        if item.objectType() == NODE:
            node = self.getNodeFromItem(item)
            node.setBypassed(not enabled)
        if item.objectType() == PARAM:
            # todo param disable
            pass

    def objectNameChangedEvent(self, item, old_value, new_value, column=None):

        if item.objectType() == NODE:
            node = NodegraphAPI.GetNode(old_value)
            node.setName(new_value)
            Utils.EventModule.ProcessAllEvents()
            new_name = node.getName()
            item.columnData()["name"] = new_name

        if item.objectType() == PARAM:
            item.columnData()["name"] = old_value
            # todo param name change
            # could also just disable this in the item...
            pass


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
        """ Displays the node/parameter to the user

        Args:
            parent (ShojiHeaderTreeView)
            widget (ShojiModelDelegateWidget)
            item (ShojiModelItem)
        """
        # ToDo Update node selected display
        #
        if item:
            this = widget.getMainWidget()
            if item.columnData()["object_type"] == NODE:
                node_list = [NodegraphAPI.GetNode(item.columnData()["name"])]
            if item.columnData()["object_type"] == PARAM:
                node = item.columnData()["node"]
                param = ".".join(item.columnData()["name"].split(".")[1:])
                node_list = [NodegraphAPI.GetNode(node).getParameter(param)]
            this.populateParameters(node_list, hide_title=False)