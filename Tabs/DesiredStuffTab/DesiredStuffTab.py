"""
Creates a tab that allows users to flags nodes as "desirable".

This tab has multiple groups inside of it so that the user may
make subcategories of desirable nodes.

How it works:
Create New Desirable Group:
    Type text into field and hit enter.
Add Desirable Objects:
    After selecting a desirable group, drag/drop parameters into the list view
    that is displayed in the bottom portion.

This works by storing JSON metadata as a parameter under "KatanaBebop.DesirableStuff"
Where each child will store a singular desirable groups metadata in the form of:
    {data: [
        {type: NODE/PARAM, node: node.getName(), param:param.getFullName()},
        {type: NODE/PARAM, node: node.getName(), param:param.getFullName()}
    ]}


When the user clicks an item in the desirable stuff tab, this will look at the metadata
on the item, which will correspond to what is stored under "KatanaBebop.DesirableStuff"
to determine what should be displayed.

Please note that at this point in time, sub groups of groups are not available.  This is something
that may or may not be added in the future depending on how many shits I give.

Hierarchy:
    DesiredStuffTab --> (UI4.Tabs.BaseTab)
        |- QVBoxLayout
            |- desired_nodes_frame --> (ShojiModelViewWidget)
                |-* DesirableStuffShojiPanel --> (NodeViewWidget --> ShojiModelViewWidget)

Data:
KatanaBebop.DesirableStuff.DesirableGroupName
    {data: [
        {type:NODE/PARAM.type(), object_type: NODE/PARAM, node: node.getName(), param:param.getFullName()},
        {type:NODE/PARAM.type(), object_type: NODE/PARAM, node: node.getName(), param:param.getFullName()}
    ]}
"""
"""
TODO:
    * Hold data as ns_attr instead of parameter? test this on load/reload
    * DesirableStuffShojiPanel --> desiredData()
        --> updateDesiredDataFromParam
        - make sure this stays in sync when doing the drag/drop/delete/etc
            - node/parameter reparent
"""
import json

from qtpy.QtWidgets import QVBoxLayout, QSizePolicy, QApplication
from qtpy.QtCore import Qt, QModelIndex

from cgwidgets.widgets import ShojiModelViewWidget, StringInputWidget, LabelledInputWidget, OverlayInputWidget
from cgwidgets.views import AbstractDragDropListView
from cgwidgets.utils import getWidgetAncestor
from cgwidgets.settings import attrs

from Katana import UI4 , NodegraphAPI, Utils
from Widgets2 import NodeViewWidget
from Utils2 import nodeutils, getFontSize, paramutils, NODE, PARAM, getValidName


class DesiredStuffTab(UI4.Tabs.BaseTab):
    """Main tab widget for the desirable widgets"""
    NAME = 'Node Graph Pins'

    def __init__(self, parent=None):
        super(DesiredStuffTab, self).__init__(parent)
        # create main widget
        self._desired_stuff_frame = DesirableStuffFrame(self)

        # setup main layout
        QVBoxLayout(self)
        self.layout().addWidget(self._desired_stuff_frame)
        Utils.EventModule.RegisterCollapsedHandler(self.desiredStuffFrame().populate, 'nodegraph_setRootNode')
        Utils.EventModule.RegisterCollapsedHandler(self.updateObjectNameEvent, 'node_setName')
        Utils.EventModule.RegisterCollapsedHandler(self.updateObjectNameEvent, 'parameter_setName')
        Utils.EventModule.RegisterCollapsedHandler(self.updateObjectDeleteEvent, 'parameter_deleteChild')
        Utils.EventModule.RegisterCollapsedHandler(self.updateObjectDeleteEvent, 'node_delete')

        self.desiredStuffFrame().populate()

    """ UTILS """
    @staticmethod
    def desiredStuffParam():
        """ Returns the Group parameter storing all of the desirable data

        Returns (Param)"""
        node = NodegraphAPI.GetNode('rootNode')
        Utils.UndoStack.DisableCapture()
        paramutils.createParamAtLocation("KatanaBebop.DesirableStuff", node, paramutils.GROUP)
        Utils.UndoStack.EnableCapture()
        return node.getParameter('KatanaBebop.DesirableStuff')

    @staticmethod
    def desiredData(child):
        """ Returns a dictionary of the current scene data

        Args:
            child (str): name of Desirable Group's data to return"""
        data_param = DesiredStuffTab.desiredStuffParam().getChild(child)
        if data_param:
            return json.loads(data_param.getValue(0))
        return None

    @staticmethod
    def desirableGroups():
        """ Returns a list of all the desirable groups

        Returns (list): of strings """
        return [child.getName() for child in DesiredStuffTab.desiredStuffParam().getChildren()]

    """ EVENTS  """
    def updateObjectDeleteEvent(self, args):
        """ Updates the metadata when a node/parameter has been deleted"""
        for arg in args:
            # get object name
            if arg[0] == "node_delete":
                object_name = arg[2]["node"].getName().replace("__XX_DELETED_", "")

            if arg[0] == "parameter_deleteChild":
                param_name = arg[2]["childName"]
                param_full_path = arg[2]["paramName"] + "." + param_name
                node_name = arg[2]["node"].getName()
                object_name = f"{param_name} | {node_name} | {param_full_path}"

            # update project settings meta data
            for child in DesiredStuffTab.desiredStuffParam().getChildren():
                data = json.loads(child.getValue(0))
                for i, object_data in enumerate(data["data"]):
                    if object_data["name"] == object_name:
                        del data["data"][i]

                child.setValue(json.dumps(data), 0)

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
        # update project settings meta data
        for child in DesiredStuffTab.desiredStuffParam().getChildren():
            data = json.loads(child.getValue(0))
            for object_data in data["data"]:
                try:
                    if old_name == object_data[object_type]:
                        object_data[object_type] = new_name
                        if object_type == NODE:
                            object_data["name"] = new_name
                        if object_type == PARAM:
                            object_data["name"] = paramutils.getParamDisplayName(obj)

                except KeyError:
                    """ Need to except a key error here, as the node objects do not
                    have the PARAM key"""
                    pass

            child.setValue(json.dumps(data), 0)

    """ WIDGET"""
    def desiredStuffFrame(self):
        return self._desired_stuff_frame


class DesirableStuffFrame(ShojiModelViewWidget):
    """Main frame for holding all of the individual desirable node panels"""
    def __init__(self, parent=None):
        super(DesirableStuffFrame, self).__init__(parent)

        self.setHeaderDefaultLength(getFontSize() * 6)

        self._selected_items = []
        self.setHeaderPosition(attrs.NORTH, attrs.SOUTH)
        self.setOrientation(Qt.Vertical)
        self.setDelegateTitleIsShown(True)
        self.setMultiSelect(True)

        # setup dynamic widget
        self.setDelegateType(
            ShojiModelViewWidget.DYNAMIC,
            dynamic_widget=DesirableStuffShojiPanel,
            dynamic_function=DesirableStuffShojiPanel.populate
        )

        # tab create widget
        self._create_desirable_group_input_widget = StringInputWidget()
        self._create_desirable_group_widget = LabelledInputWidget(
            self,
            default_label_length=getFontSize() * 13,
            delegate_widget=self._create_desirable_group_input_widget,
            direction=Qt.Horizontal,
            name="Create New Group",
            )
        self.addHeaderDelegateWidget([], self._create_desirable_group_widget, modifier=Qt.NoModifier, focus=True)
        self._create_desirable_group_widget.setUserFinishedEditingEvent(self.createNewDesirableGroup)
        self._create_desirable_group_widget.viewWidget().setDisplayMode(OverlayInputWidget.DISABLED)
        self._create_desirable_group_widget.setFixedHeight(getFontSize() * 3)
        self._create_desirable_group_widget.show()

        # setup events
        self.setHeaderItemDeleteEvent(self.purgeDesirableGroup)
        self.setHeaderItemSelectedEvent(self.itemSelected)
        self.setHeaderItemTextChangedEvent(self.desirableGroupNameChanged)
        self.setHeaderItemDropEvent(self.rearrangeDesirableGroups)

        self.setHeaderItemIsEnableable(False)
        self.setHeaderItemIsDroppable(False)

        # setup style
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)

        self.delegateWidget().setObjectName("DesirableStuffFrame")

    def rearrangeDesirableGroups(self, data, items_dropped, model, row, parent):
        desirable_param = DesiredStuffTab.desiredStuffParam()
        child_param = desirable_param.getChild(items_dropped[0].name())
        desirable_param.reorderChild(child_param, row)

    def desirableGroupNameChanged(self, item, old_value, new_value, column=None):
        """ Updates the desirable groups name """
        # preflight
        if new_value == "": return
        if new_value in DesiredStuffTab.desirableGroups():
            item.columnData()["name"] = old_value
            return

        # rename param
        param = DesiredStuffTab.desiredStuffParam().getChild(old_value)
        param.setName(new_value)

        # update internal data
        # todo update display name
        """ for some reason this is all registering, all the data is being passed through,
        however it is not updating...
        GSVManager has a working example somehow?
        """
        item.columnData()["name"] = param.getName()
        self.updateDelegateDisplay()

    def purgeDesirableGroup(self, item):
        """ Removes the currently selected desirable group item """
        param = DesiredStuffTab.desiredStuffParam()
        name = item.columnData()['name']
        param.deleteChild(param.getChild(name))
        self.updateHeaderItemSizes()

    def itemSelected(self, item, enabled, column=0):
        if column == 0:
            name = item.columnData()['name']
            if enabled:
                if name not in self._selected_items:
                    self._selected_items.append(name)
            else:
                if name in self._selected_items:
                    self._selected_items.remove(name)

    def populate(self, *args):
        """
        Loads all of the desirable groups from the root node
        """
        # store temp as will be overwritten
        _selected_items = [item for item in self._selected_items]

        # clear model
        self.clearModel()

        # repopulate
        desirable_groups = DesiredStuffTab.desirableGroups()
        for group in reversed(desirable_groups):
            self.addNewGroup(group)

        # reselect index
        for item in _selected_items:
            for index in self.model().findItems(item):
                self.setIndexSelected(index, True)

    def addNewGroup(self, name):
        """ Creates a new model index for the Group

        Args:
            name (str): the name...
        """
        # create new index
        new_index = self.insertShojiWidget(0, column_data={'name': name})
        self.setIndexSelected(new_index, True)

        self.updateHeaderItemSizes()
        return new_index

    def createNewDesirableGroup(self, widget, value):
        """ Creates a new desirable Group

        This is triggered when the user fills in the "Create New Tab" Widget
        """
        name = self._create_desirable_group_input_widget.text()
        if name:
            name = getValidName(name)
            # setup katana params
            param = DesiredStuffTab.desiredStuffParam()
            new_param = param.createChildString(name, json.dumps({"data": []}))

            # add item
            index = self.addNewGroup(name)
            index.internalPointer().columnData()["name"] = new_param.getName()

            # reset widget
            widget.setText('')
            header_view_widget = self.headerViewWidget()
            header_view_widget.setFocus()


class DesirableStuffShojiPanel(NodeViewWidget):
    """A single panel in of desirable nodes/parameters.

    This will display one Desirable Groups nodes/parameters to the user.

    Attributes:
        desired_data (list): of dicts of desirable data
            {type: NODE/PARAM, node: node.getName(), param:param.getFullName()}

        name (str): name of the current group that is being shown.
        param (param): the parameter on the Root Node which holds the data for this desirable group
    """
    def __init__(self, parent=None):
        super(DesirableStuffShojiPanel, self).__init__(parent)

        # setup custom view
        view = DesirableStuffView(self)
        self.setHeaderViewWidget(view)

        # setup flags
        self.setMultiSelect(True)
        self.setHeaderItemIsEnableable(False)
        self.setHeaderItemIsDeletable(True)
        self.setHeaderItemIsDroppable(False)
        self.setHeaderItemIsRootDroppable(True)
        self.setHeaderItemIsDraggable(True)

        self.setHeaderItemDeleteEvent(self.purgeUndesirableObject)
        self.setHeaderItemDropEvent(self.reorganizeDesirableObjects)

        self._desired_data = []
        self._name = "Hello"

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)

        # setup context menu
        # for some reason I have to add this here.. instead of in the base widget...
        self.addContextMenuEvent("Go To Node", self.goToNode)
        self.addContextMenuEvent("Go To Param", self.goToParam, {"object_type":PARAM})

        self.delegateWidget().setObjectName("Panel")

    """ EVENTS """
    def goToNode(self, index, selected_indexes):
        item = index.internalPointer()

        if item:
            node = self.getNodeFromItem(item)
            if item.getArg("object_type") == PARAM:
                node = NodegraphAPI.GetNode(item.getArg("node"))

            nodeutils.goToNode(node, frame=True)

    def goToParam(self, index, selected_indexes):
        item = index.internalPointer()
        if item:
            if item.getArg("object_type") == PARAM:
                node = NodegraphAPI.GetNode(item.getArg("node"))
                NodegraphAPI.SetNodeEdited(node, True, exclusive=True)

    """ PROPERTIES """
    def name(self):
        return self._name

    def setName(self, name):
        self._name = name

    def param(self):
        param = DesiredStuffTab.desiredStuffParam()
        return param.getChild(self.name())

    def paramData(self):
        return json.loads(self.param().getValue(0))

    def desiredData(self):
        return self._desired_data

    def desiredNodes(self):
        """ All of the nodes that this desirable group owns

        Returns (list): of nodes"""
        _desired_nodes = []
        for item in self.desiredData():
            if item["object_type"] == NODE:
                _desired_nodes.append(NodegraphAPI.GetNode(item["node"]))
        return _desired_nodes

    def desiredParams(self):
        """ All of the params] that this desirable group owns

        Returns (list): of params"""
        _desired_params = []
        for item in self.desiredData():
            if item["object_type"] == PARAM:
                node = NodegraphAPI.GetNode(item["node"])
                param_path = ".".join(item["param"].split(".")[1:])
                param = node.getParameter(param_path)
                _desired_params.append(param)
        return _desired_params

    def addDesirableNodeData(self, node):
        """ Adds a desirable node to the internal data structures"""
        data = {"name":node.getName(), "object_type": NODE, "node":node.getName()}
        self.desiredData().append(data)

        desirable_data = json.loads(self.param().getValue(0))
        desirable_data["data"].append(data)

        self.param().setValue(json.dumps(desirable_data), 0)
        # update desirable data

    def addDesirableParamData(self, param, node):
        """ Adds a desirable param to the internal data structures"""
        data = {"name":paramutils.getParamDisplayName(param), "object_type": PARAM, "param":param.getFullName(), "node":node}
        self.desiredData().append(data)

        desirable_data = json.loads(self.param().getValue(0))
        desirable_data["data"].append(data)

        self.param().setValue(json.dumps(desirable_data), 0)

    """ DESIRABLE """
    def setDesirability(self, obj, enabled, object_type):
        """ Sets a objs flag to be desirable

        Args:
            obj (Node/Param): to make desirable
            enabled (bool): how $3xy this obj is
            object_type (DesiredStuffTab.TYPE): object_type to do
                NODE | PARAM
        """
        if enabled:
            if object_type == NODE:
                if obj not in self.desiredNodes():
                    node_view_widget = getWidgetAncestor(self, NodeViewWidget)
                    node_view_widget.createNewIndexFromNode(obj)
                    self.addDesirableNodeData(obj)

            if object_type == PARAM:
                if obj not in self.desiredParams():
                    node_view_widget = getWidgetAncestor(self, NodeViewWidget)
                    node_view_widget.createNewIndexFromParam(obj)
                    self.addDesirableParamData(obj, obj.getNode().getName())

        else:
            self._makeDesirableParam(obj, False)

    def updateDesiredDataFromParam(self):
        pass

    """ UTILS """
    def doesItemExist(self, obj_data):
        """ Determines if the object data provided exists

        Args:
            obj_data (dict): data to be checked
                {name:obj.getName(), type:NODE/PARAM.type(), object_type: NODE/PARAM, node: node.getName(), param:param.getFullName()},
        """
        for index in self.getAllIndexes():
            item = index.internalPointer()
            is_match = True
            for arg in ["name", "type", "object_type", "node"]:
                try:
                    if item.getArg(arg) != obj_data[arg]:
                        is_match = False
                        break
                except KeyError:
                    pass

            if is_match:
                return True

        return False

    """ EVENTS """
    def purgeUndesirableObject(self, item):
        """On Delete, this will remove the desirable reference to the node

        Args:
            item (ShojiModelItem): item currently selected"""
        data = self.paramData()
        for obj in data["data"]:
            if item.name() == obj["name"]:
                data["data"].remove(obj)

        self.param().setValue(json.dumps(data), 0)

        self.updateDesiredDataFromParam()

    def reorganizeDesirableObjects(self, data, items, model, row, parent):
        data = self.paramData()
        # remove data
        for item in items:
            item_data = item.columnData()
            if item.objectType() == NODE:
                _temp_data = {"name":item.name(), "object_type": NODE, "node": item.getArg("node")}
            if item.objectType() == PARAM:
                _temp_data = {"name":item.name(), "object_type": PARAM, "param": item.getArg("param"), "node": item.getArg("node")}
            data["data"].remove(_temp_data)

        # reinsert data
        for item in items:
            if item.objectType() == NODE:
                new_data = {"name":item.name(), "object_type": NODE, "node": item.getArg("node")}
            if item.objectType() == PARAM:
                new_data = {"name":item.name(), "object_type": PARAM, "param": item.getArg("param"), "node": item.getArg("node")}
            data["data"].insert(row, new_data)

        # save data
        self.param().setValue(json.dumps(data), 0)
        self.updateDesiredDataFromParam()

    @staticmethod
    def populate(parent, widget, item):
        """
        Adds all of the indexes for every node that has been
        chosen as "desirable" by the user
            def updateGUI(parent, widget, item):

            parent (ShojiModelViewWidget)
            widget (ShojiModelDelegateWidget)
            item (ShojiModelItem)
            self --> widget.getMainWidget()

        """
        # todo update desirable group names
        this = widget.getMainWidget()

        # set attrs
        this.setName(item.columnData()['name'])

        # force repopulate
        this._desired_data = []
        desired_data = reversed(json.loads(this.param().getValue(0))["data"])
        for obj_data in desired_data:
            exists = this.doesItemExist(obj_data)

            if not exists:
                if obj_data["object_type"] == NODE:
                    obj = NodegraphAPI.GetNode(obj_data["node"])

                    this.createNewIndexFromNode(obj)

                if obj_data["object_type"] == PARAM:
                    node = NodegraphAPI.GetNode(obj_data["node"])
                    param = ".".join(obj_data["param"].split(".")[1:])
                    obj = node.getParameter(param)
                    this.createNewIndexFromParam(obj)


class DesirableStuffView(AbstractDragDropListView):
    """ Displays the Desirable Nodes/Parameters for each group

    This contains the drag/drop events from the Nodegraph/Parameters pane."""
    def __init__(self, parent=None):
        super(DesirableStuffView, self).__init__(parent)

    """ EVENTS """
    def dragEnterEvent(self, event):
        mimedata = event.mimeData()
        if mimedata.hasFormat('nodegraph/nodes'):
            event.accept()

        if mimedata.hasFormat("parameter/path"):
            event.accept()

        return AbstractDragDropListView.dragEnterEvent(self, event)

    def dropEvent(self, event):
        """
        This will handle all drops into the view from the Nodegraph

        Alot of this is copy/paste from nodeMovedEvent
        """
        mimedata = event.mimeData()
        if mimedata.hasFormat('nodegraph/nodes'):
            nodes_list = mimedata.data('nodegraph/nodes').data().decode("utf-8").split(',')
            parent_widget = getWidgetAncestor(self, DesirableStuffShojiPanel)
            for node_name in nodes_list:
                # get node
                node = NodegraphAPI.GetNode(node_name)
                parent_widget.setDesirability(node, True, NODE)

        if mimedata.hasFormat("parameter/path"):
            # param = eval(mimedata.data('python/text').decode("utf-8").data())
            # print(type(mimedata.data("python/text")), mimedata.data("python/text"))

            # param = eval(mimedata.data('python/text').decode("utf-8").data())
            param = eval(str(mimedata.data('python/text').data(), encoding='utf-8'))
            if param.getName() == "value":
                param = param.getParent()
            parent_widget = getWidgetAncestor(self, DesirableStuffShojiPanel)
            parent_widget.setDesirability(param, True, PARAM)

        return AbstractDragDropListView.dropEvent(self, event)


# from cgwidgets.utils import centerWidgetOnCursor, setAsAlwaysOnTop
# w = DesiredStuffTab()
# setAsAlwaysOnTop(w)
# w.show()
# w.resize(512, 512)
# centerWidgetOnCursor(w)
