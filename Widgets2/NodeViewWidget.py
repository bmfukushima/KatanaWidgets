"""
- Needs to move to custom widget and supertool can inherit that
- Need a node interface to connect nodes into it
"""
from qtpy.QtWidgets import QVBoxLayout
from qtpy.QtCore import QModelIndex, Qt

from cgwidgets.settings import attrs
from cgwidgets.widgets import ShojiModelViewWidget, ShojiModelItem

from Katana import UI4, NodegraphAPI, Utils

from Widgets2 import AbstractParametersDisplayWidget
from Utils2 import paramutils, NODE, PARAM


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

        # setup events
        self.setHeaderItemTextChangedEvent(self.objectNameChangedEvent)
        self.setHeaderItemEnabledEvent(self.objectDisableEvent)
        Utils.EventModule.RegisterCollapsedHandler(self.updateObjectNameEvent, 'node_setName')
        Utils.EventModule.RegisterCollapsedHandler(self.updateObjectNameEvent, 'parameter_setName')
        Utils.EventModule.RegisterCollapsedHandler(self.updateObjectDeleteEvent, 'node_delete')
        Utils.EventModule.RegisterCollapsedHandler(self.updateObjectDeleteEvent, 'parameter_deleteChild')

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
                "object_type": PARAM,
                "node": param.getNode().getName(),
                "param": param.getFullName(),

            },
            parent=parent_index,
            is_enableable=False,
            is_editable=False)

        return new_index

    """ EVENTS """
    def objectDisableEvent(self, item, enabled):
        """ enable/disable event """
        if item.objectType() == NODE:
            node = self.getNodeFromItem(item)
            node.setBypassed(not enabled)
        if item.objectType() == PARAM:
            # todo param disable
            pass

    def objectNameChangedEvent(self, item, old_value, new_value, column=None):
        """ Update the object name when the user changes the name """
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

    def updateObjectDeleteEvent(self, args):
        """ When a node/parameter is deleted, this will remove the item from the display"""
        for arg in args:
            print(arg)
            if arg[0] == "node_delete":
                object_name = arg[2]["node"].getName().replace("__XX_DELETED_", "")

            if arg[0] == "parameter_deleteChild":
                param_name = arg[2]["childName"]
                param_full_path = arg[2]["paramName"] + "." + param_name
                node_name = arg[2]["node"].getName()
                object_name = f"{param_name} | {node_name} | {param_full_path}"

            indexes = self.findItems(object_name, Qt.MatchExactly)
            for index in indexes:
                item = index.internalPointer()
                self.deleteItem(item)

    def updateObjectNameEvent(self, args):
        """ Updates the desired objects names when a nodes name is changed """
        for arg in args:
            # get data
            old_name = arg[2]["oldName"]
            new_name = arg[2]["newName"]
            if arg[0] == "node_setName":
                node = arg[2][NODE]
                self.updateObjectName(node, NODE, old_name, new_name)

            if arg[0] == "parameter_setName":
                param = arg[2][PARAM]
                parent_path = ".".join(param.getFullName().split(".")[:-1])
                old_name = f"{parent_path}.{old_name}"
                new_name = f"{parent_path}.{new_name}"
                self.updateObjectName(param, PARAM, old_name, new_name)

    def updateObjectName(self, obj, object_type, old_name, new_name):
        """ Updates the metadata when a desired objects name has changed

        Args:
            obj (Node/Param): object that is being updated
            object_type (NODE/PARAM) object type that is being updated
            old_name (str): old name
            new_name (str): new name

        Returns:

        """

        # need to change the display name for the param as it has a special display name
        if object_type == PARAM:
            old_name = paramutils.getParamDisplayName(obj).replace(new_name.split(".")[-1], old_name.split(".")[-1])

        # find matches and update
        indexes = self.findItems(old_name, match_type=Qt.MatchExactly)
        for index in indexes:
            item = index.internalPointer()
            if item:
                if object_type == NODE:
                    item.setArg("node", new_name)
                    item.setArg("name", new_name)
                if object_type == PARAM:
                    item.setArg("param", new_name)
                    item.setArg("name", paramutils.getParamDisplayName(obj))


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