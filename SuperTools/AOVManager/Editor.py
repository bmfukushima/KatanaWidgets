"""
Todo:
    *   Item type storage Group vs AOV
            - Populate | Expand on startup
    *   Setup Node
        -   Lights, Custom, Denoise
        -   Create Node data
                PRMAN | ARNOLD | REDSHIFT | DELIGHT
                AOVManagerItemWidget --> setAOVType
                                     --> updateGUI
        -   RenderSettings node
                enable/disable update
    *   Setup save location
    *   Setup Advanced Parameters
Todo (Bugs)
    *   Setting TYPE from view


Use a ShojiMVW to create an interface for AOV's
Items
    GROUP | LIGHT | LPE | CUSTOM
    AOV Item
        * AOVItems will hold all of the necessary parameters the user needs to create a new AOV
        * Presets / LPE's / Lights
    - Each item is linked to a node via the nodes name
    - Each node's parameters are linked to the column data of the item

Hierarchy
AOVManagerEditor --> (AbstractSuperToolEditor)
    |- QVBoxLayout
        |- aovManager --> (ShojiModelViewWidget)
            |- AOVManagerItemWidget --> (AOVManagerItemWidget)
                |- QVBoxLayout
                    |- parametersWidget
                        |- typeWidget
                        |- lpeWidget

Data:
    type : TYPE (GROUP | LIGHT | LPE)
    name : str()
    children : list()
    enabled : bool
    expanded : bool

AOVMAP
    Needs to have the same items in the dictionary as the parameters on the nodes


"""

import json

from qtpy.QtWidgets import QVBoxLayout, QLabel, QWidget
from qtpy.QtCore import Qt, QModelIndex

from Katana import NodegraphAPI

from cgwidgets.widgets import (
    ButtonInputWidget,
    FrameInputWidgetContainer,
    FloatInputWidget,
    ListInputWidget,
    LabelledInputWidget,
    ModelViewWidget,
    ShojiModelViewWidget,
    StringInputWidget
)
from cgwidgets.settings import attrs
from cgwidgets.utils import getFontSize, getJSONData, getWidgetAncestor
from cgwidgets.views import AbstractDragDropModelDelegate

from Widgets2 import AbstractSuperToolEditor, iParameter
from Utils2 import paramutils, nodeutils

# MAPPING TABLES
SPECULAR = "SPEC"
INDIRECT_SPECULAR = "iSPEC"
SPECULAR_ROUGHNESS = "SPECR"
DIFFUSE = "DIFF"
INDIRECT_DIFFUSE = "iDIFF"
EMISSIVE = "GLOW"
SUBSURFACE = "SSS"
TRANSMISSIVE = "TRANS"

LPE = "LPE"
AOVGROUP = "GROUP"
LIGHT = "LIGHT"

AOVMAP = {
    "Prman": {
        LPE: {"type": LPE, "lpe": "lpe:", "name": "LPE", "rendererType": "color"},
        SPECULAR: {"type": LPE, "lpe": "lpe:C<RS>[<L.>O]", "name": SPECULAR, "rendererType": "color"},
        INDIRECT_SPECULAR: {"type": LPE, "lpe": "lpe:C<RS>.+[<L.>O]", "name": INDIRECT_SPECULAR, "rendererType": "color"},
        INDIRECT_DIFFUSE: {"type": LPE, "lpe": "lpe:C<RD>.+[<L.>O]", "name": INDIRECT_DIFFUSE, "rendererType": "color"},
        SUBSURFACE: {"type": LPE, "lpe": "lpe:C<TD>.*[<L.>O]", "name": SUBSURFACE, "rendererType": "color"},
        TRANSMISSIVE: {"type": LPE, "lpe": "lpe:C<TS>.*[<L.>O]", "name": TRANSMISSIVE, "rendererType": "color"},
        DIFFUSE: {"type": LPE, "lpe": "lpe:C<RD>[<L.>O]", "name": DIFFUSE, "rendererType": "color"}
    },
    "Arnold": {},
    "Redshift": {},
    "Delight": {}
}

ARNOLD = "Arnold"
PRMAN = "Prman"
DELIGHT = "Delight"
REDSHIFT = "Redshift"


def renderEngines():
    return [ARNOLD, DELIGHT, PRMAN, REDSHIFT]


class AOVManagerEditor(AbstractSuperToolEditor):
    """ Top level SuperTool Widget"""

    def __init__(self, parent, node):
        super(AOVManagerEditor, self).__init__(parent, node)
        self.__initializing = True
        self._renderer = ""

        # setup widgets
        self._renderer_widget = self.createCustomParameterWidget(ListInputWidget)
        self.createCustomParam(
            self._renderer_widget,
            'renderer',
            paramutils.STRING,
            self._renderer_widget.text,
            self.rendererChangedEvent,
            initial_value=""
        )
        # if self.node().getParameter("renderer"):
        #     self._renderer_widget.setText(self.node().getParameter("renderer").getValue(0))
        self._renderer_widget.filter_results = False
        self._renderer_widget.populate([[renderer] for renderer in renderEngines()])
        self._renderer_labelled_widget = LabelledInputWidget(
            name="Renderer", delegate_widget=self._renderer_widget)
        self._renderer_labelled_widget.setFixedHeight(getFontSize() * 3)
        self._renderer_labelled_widget.setDefaultLabelLength(getFontSize() * 10)

        self._render_location_widget = self.createCustomParameterWidget(StringInputWidget)
        self.createCustomParam(
            self._render_location_widget,
            'renderLocation',
            paramutils.STRING,
            self._render_location_widget.text,
            self.renderLocationChangedEvent,
            initial_value=""
        )

        self._render_location_labelled_widget = LabelledInputWidget(
            name="Location", delegate_widget=self._render_location_widget)
        self._render_location_labelled_widget.setFixedHeight(getFontSize() * 3)
        self._render_location_labelled_widget.setDefaultLabelLength(getFontSize() * 10)

        self._aov_manager = AOVManagerWidget(self, node)

        # create layout
        QVBoxLayout(self)
        self.layout().addWidget(self._renderer_labelled_widget)
        self.layout().addWidget(self._render_location_labelled_widget)
        self.layout().addWidget(self._aov_manager)
        self.insertResizeBar()

    """ PROPERTIES """
    def renderLocation(self):
        return self.aovManager().renderLocation()

    def setRenderLocation(self, render_location):
        return self.aovManager().setRenderLocation(render_location)

    def renderer(self):
        return self.aovManager().renderer()

    def setRenderer(self, renderer):
        self.aovManager().setRenderer(renderer)

    """ WIDGETS """
    def aovManager(self):
        return self._aov_manager

    def rendererWidget(self):
        return self._renderer_widget

    """ EVENTS """
    def rendererChangedEvent(self, widget, value):
        """ User has changed the renderer """
        self.setRenderer(value)
        self.node().getParameter("renderer").setValue(value, 0)
        # todo update renderer parameter
        # todo remove/flag all bad nodes?

    def renderLocationChangedEvent(self, widget, value):
        """ User has changed the renderer """
        # todo update render location changed parameters
        self.node().getParameter("renderLocation").setValue(value, 0)
        self.setRenderLocation(value)

    def showEvent(self, event):
        """ Set all of the default widget sizes on show"""
        return_val = AbstractSuperToolEditor.showEvent(self, event)
        if self.__initializing:
            self._renderer_labelled_widget.resetSliderPositionToDefault()
            self._render_location_labelled_widget.resetSliderPositionToDefault()

            min_width = 300
            if min_width < self.width() * 0.5:
                self._aov_manager.setHeaderDefaultLength(self.width() * 0.5)
            else:
                self._aov_manager.setHeaderDefaultLength(min_width)
            self._aov_manager.setHeaderWidgetToDefaultSize()
            self.__initializing = False
        return return_val


class AOVManagerWidget(ShojiModelViewWidget):
    """ Main display for showing the user the current AOV's available to them.

    Attributes:
        node (Node): AOVManager node
        renderer (string): render engine being used
            arnold | delight | prman | redshift
        saveLocation (string): path on disk to save to.
            # todo this will eventually be updated to a parameter

    """
    def __init__(self, parent=None, node=None):
        super(AOVManagerWidget, self).__init__(parent)
        # setup attrs
        self._node = node
        self.rootItem().setArg("node", node.getName())

        self.setHeaderViewType(ModelViewWidget.TREE_VIEW)
        self._delegate = AOVManagerItemDelegate(parent=self)
        self.headerViewWidget().setItemDelegate(self._delegate)
        self.setHeaderPosition(attrs.WEST, attrs.SOUTH)
        self.setDelegateTitleIsShown(False)
        self.setHeaderData(["name", "type", "lpe"])

        # create new item button
        self._createNewItemWidget = ButtonInputWidget(
            title="Create New Item", user_clicked_event=self.createNewIndex)
        self.addHeaderDelegateWidget([], self._createNewItemWidget, modifier=Qt.NoModifier, focus=True)
        self._createNewItemWidget.setFixedHeight(getFontSize() * 3)
        self._createNewItemWidget.show()

        # set custom delegate
        self.setDelegateType(
            ShojiModelViewWidget.DYNAMIC,
            dynamic_widget=AOVManagerItemWidget,
            dynamic_function=AOVManagerItemWidget.updateGUI
        )

        # setup events
        self.setHeaderItemTextChangedEvent(self.aovNameChangedEvent)
        self.setHeaderItemEnabledEvent(self.aovEnabledEvent)
        self.setHeaderItemDeleteEvent(self.aovDeleteEvent, update_first=False)
        self.setHeaderItemDropEvent(self.aovDroppedEvent)

        render_settings_node = None
        nodes = [node for node in reversed(self.node().getChildren()) if node != render_settings_node]
        self.populate(nodes)

    """ UTILS """
    def populate(self, nodes, parent=QModelIndex()):
        """ Populates the user defined AOV's on load"""
        for node in nodes:
            if self.isAOVManagerNode(node):
                # create new item
                column_data = paramutils.getParameterMapFromNode(node)
                new_index = self.createNewIndex(None, parent=parent, column_data=column_data)
                new_index.internalPointer().setIsEnabled(not node.isBypassed())

                # populate children
                if hasattr(node, "getChildren"):
                    if 0 < len(node.getChildren()):
                        self.populate(reversed(node.getChildren()), parent=new_index)

                # todo expand on populate
                # if child["expanded"]:
                #     self.headerViewWidget().setExpanded(new_index, True)

    def isAOVManagerNode(self, node):
        if not node.getParameter("type"): return False
        if not node.getParameter("name"): return False
        if not node.getParameter("node"): return False
        if node.getParameter("node").getValue(0) != node.getName(): return False

        return True

    def getChildNodeListFromItem(self, item):
        """
        Gets all of the node children from the specified item

        Returns (list) of nodes

        Todo: duplicate from NodeTree/Editor
        """
        # get node list
        children = item.children()
        node_name_list = [child.columnData()['node'] for child in children]
        node_list = [NodegraphAPI.GetNode(node) for node in node_name_list]

        return node_list

    """ PROPERTIES """
    def node(self):
        return self._node

    def setNode(self, node):
        self._node = node

    def renderer(self):
        return self.node().getParameter("renderer").getValue(0)

    def setRenderer(self, renderer):
        self.node().getParameter("renderer").setValue(renderer, 0)

    def renderLocation(self):
        return self.node().getParameter("renderLocation").getValue(0)

    def renderLocation(self, render_location):
        self.node().getParameter("renderLocation").setValue(render_location, 0)

    """ EVENTS """
    def aovNameChangedEvent(self, item, old_value, new_value):
        # set node name
        node = NodegraphAPI.GetNode(item.getArg("node"))
        if item.getArg("type") == AOVGROUP:
            node.setName(new_value)
            item.setArg("node", node.getName())

        item.setArg("name", new_value)
        node.getParameter("name").setValue(new_value, 0)

        # export data
        self.updateDelegateDisplay()

    def aovDroppedEvent(self, data, items_dropped, model, row, parent):
        """Run when the user does a drop.  This is triggered on the dropMimeData funciton
        in the model.

        Args:
            indexes (list): of ShojiModelItems
            parent (ShojiModelItem): parent item that was dropped on
        """
        # get parent node
        try:
            parent_node = NodegraphAPI.GetNode(parent.getArg("node"))
        except KeyError:
            parent_node = self.node()

        # if root
        if parent.getArg("name") == 'root':
            parent_node = self.node()

        # drop items
        for item in items_dropped:
            # get node
            node = NodegraphAPI.GetNode(item.getArg("node"))

            # disconnect node
            nodeutils.disconnectNode(node, input=True, output=True, reconnect=True)

            # create ports
            nodeutils.createIOPorts(node, force_create=False, connect=True)

            # reparent
            node.setParent(parent_node)

        # reconnect node to new parent
        node_list = self.getChildNodeListFromItem(parent)
        nodeutils.connectInsideGroup(node_list, parent_node)

    def aovEnabledEvent(self, item, enabled):
        """ On enable/disable set the args"""
        node = NodegraphAPI.GetNode(item.getArg("node"))
        node.setBypassed(not enabled)

    def aovDeleteEvent(self, item):
        """ On delete, removes the node"""
        node = NodegraphAPI.GetNode(item.getArg("node"))
        nodeutils.disconnectNode(node, input=True, output=True, reconnect=True)
        node.delete()

    def createNewAOVGroupNode(self):
        node = NodegraphAPI.CreateNode("__aovGroup", self.node())
        nodeutils.insertNode(node, self.node())
        return node

    def createNewIndex(self, widget, column_data=None, parent=QModelIndex()):
        """ Creates a new AOV Index.

        Args:
            widget (QWidget): button pressed (if applicable)
            column_data (dict): of data to be used for this item
            parent (QModelIndex): Parent index of item being created"""
        if not column_data:
            node = self.createNewAOVGroupNode()
            column_data = paramutils.getParameterMapFromNode(node)

        new_index = self.insertShojiWidget(
            0,
            column_data=column_data,
            is_draggable=True,
            is_droppable=False,
            parent=parent)

        if column_data["type"] == AOVGROUP:
            item = new_index.internalPointer()
            item.setIsDroppable(True)
        return new_index

    def showEvent(self, event):
        self.setHeaderWidgetToDefaultSize()
        return ShojiModelViewWidget.showEvent(self, event)

    def aovTypes(self):
        """ Returns a list of the different AOV types available"""
        aovs = AOVMAP[self.renderer()]
        aovs[AOVGROUP] = {"type": AOVGROUP}
        return aovs.keys()


""" AOV DELEGATE WIDGETS"""
class AOVManagerItemWidget(QWidget):
    """ The widget displayed when a user selects an item in the AOVManagerWidget

    Attributes:
        aovType (str(TYPE)): the current type of AOV this is valid options are
            CUSTOM | GROUP | LIGHT | LPE
        currentItem (AbstractShojiModelItem):
        isFrozen (bool):
        node (Node): current node being manipulated
        widgets (dict): of parameters widgets.  Each key is an arg's name, and the value
            is the widget.

    Hierarchy
    QWidget
        |- QVBoxLayout
            |- parametersWidget
                |- typeWidget
                |- lpeWidget
    """

    def __init__(self, parent=None):
        super(AOVManagerItemWidget, self).__init__(parent)
        # attrs
        self._is_frozen = False
        self._widgets = {}

        # create main widget
        self._parameters_widget = FrameInputWidgetContainer(self, direction=Qt.Vertical)
        self._parameters_widget.setIsHeaderShown(True)
        self._parameters_widget.setHeaderTextChangedEvent(self.aovNameChangedEvent)

        # add type

        # setup layout
        QVBoxLayout(self)

        self.layout().addWidget(self._parameters_widget)
        self.layout().setContentsMargins(0, 0, 0, 0)

    def __name__(self):
        return "abstract"

    """ UTILS """
    def addParameterWidget(self, name, delegate_widget, finished_editing_function, new=True):
        """ Adds a parameter widget to the current display

        Args:
            name (str): name of arg
            delegate_widget (QWidget): Widget for user to input values
            finished_editing_function (func): Function to be run when the user
                has finished editing.  This function should take the args (widget, value)
            new (bool): determines if this is a new parameter, or updating an existing one
        """

        # create input widget
        input_widget = LabelledInputWidget(name=name, delegate_widget=delegate_widget)
        input_widget.setDefaultLabelLength(getFontSize() * 7)

        # set widget orientation
        input_widget.setDirection(Qt.Horizontal)

        # add to group layout
        self._parameters_widget.addInputWidget(input_widget, finished_editing_function=finished_editing_function)
        delegate_widget.setObjectName(name)
        self.widgets()[name] = delegate_widget

        # setup default parameter
        if self.node().getParameter(name):
            # # get default value
            if new:
                value = self.getDefaultArg(self.aovType(), name)
            else:
                value = self.node().getParameter(name).getValue(0)

            """ If no value, then only set the display text from the parameter
            Need to bypass "type" or else it will query from the wrong mapping table"""
            if name != "type":
                if name == "name" and self.aovType() == AOVGROUP:
                    value = self.node().getParameter(name).getValue(0)

                if name != "node":
                    delegate_widget.setText(value)
                    self.node().getParameter(name).setValue(value, 0)
                    self.currentItem().setArg(name, value)
                else:
                    # mainly used for setting the node
                    delegate_widget.setText(self.node().getParameter(name).getValue(0))
            # set type
            else:
                self.node().getParameter(name).setValue(self.getItemArg("type"), 0)
                delegate_widget.setText(self.getItemArg("type"))

    def createAOVMacro(self, renderer, aov_type):
        """ Creates the Macro/Group node associated with the selected AOV/Engine

        Args:
            renderer (str):
            aov_type (str):
        """
        if aov_type == AOVGROUP:
            node_name = "__aovGroup"
        else:
            base_aov_type = AOVMAP[renderer][aov_type]["type"]
            node_name = "__aov{RENDERER}{TYPE}".format(RENDERER=renderer, TYPE=base_aov_type)

        # create node
        old_node = self.node()
        new_node = NodegraphAPI.CreateNode(node_name, self.node().getParent())
        nodeutils.replaceNode(old_node, new_node)

        return new_node

    def getItemArg(self, arg_name):
        try:
            return self.currentItem().getArg(arg_name)
        except KeyError:
            return None

    def getDefaultArg(self, aov_type, arg_name):
        """ Gets the default AOV value from the mapping table

        Note:
            Need the try/except in case an arg doesnt exist such as "node"

        Args:
            aov_type (str): base type of AOV to be found in the mapping table
            arg_name (str): arg name found in the mapping table
            """
        try:
            return AOVMAP[self.renderer()][aov_type][arg_name]
        except KeyError:
            return ""

    def populateParameterWidgets(self, new=True):
        """ Populates all of the parameters from the node

        Args:
            new (bool): determines if these are new parameters, or existing ones"""
        # get attrs
        node = NodegraphAPI.GetNode(self.currentItem().getArg("node"))
        parameter_map = paramutils.getParameterMapFromNode(node)

        # cleanup old widgets
        self.clearNonAbstractParameterWidget()

        # populate parameters
        for param_name, param_value in parameter_map.items():
            if param_name == "type":
                delegate_widget = ListInputWidget(self)
                delegate_widget.filter_results = False
                delegate_widget.populate([[aov] for aov in self.aovTypes()])
                self.addParameterWidget("type", delegate_widget, self.aovTypeChangedEvent, new=new)
            else:
                if isinstance(param_value, str):
                    delegate_widget = StringInputWidget()
                elif isinstance(param_value, float):
                    delegate_widget = FloatInputWidget()
                self.addParameterWidget(param_name, delegate_widget, self.parameterChangedEvent, new=new)

    """ WIDGETS """
    def clearNonAbstractParameterWidget(self):
        """ Sets the parametersWidget to a blank slate"""
        for widget in self.parametersWidget().delegateWidgets():
            widget.setParent(None)
            widget.deleteLater()

    def clearWidgets(self):
        """ Clears all of the widgets from the display, and resets the widgets attr"""
        self.clearNonAbstractParameterWidget()
        self._widgets = {}

    def parametersWidget(self):
        return self._parameters_widget

    def widgets(self):
        return self._widgets

    """ PROPERTIES """
    def aovType(self):
        """ The currenet AOV type that is set"""
        return self.currentItem().getArg("type")

    def aovTypes(self):
        """ Returns a list of all of the potential AOV types available"""
        aov_manager_widget = getWidgetAncestor(self, AOVManagerWidget)
        return aov_manager_widget.aovTypes()

    def setAOVType(self, aov_type, new=True):
        """ Sets the current items AOV type and updates the display

        Args:
            aov_type (str): name of aov to be set
            new (bool): determines if a new node should be created or not.
                This is needed as this function is called by multiple functions
                (updateGUI & aovTypeChangedEvent).  Default value is True.
            """
        # preflight
        renderer = self.renderer()
        if renderer not in renderEngines(): return
        if aov_type not in self.aovTypes(): return

        # clear args
        """ Note need to set node here so that the parent node can be found in
        the call to "createAOVMacro()" """
        node = self.node()
        self.currentItem().clearArgsList()
        self.currentItem().setArg("node", node.getName())

        # Create new node
        self.currentItem().setArg("type", aov_type)
        if new:
            node = self.createAOVMacro(renderer, aov_type)
            self.currentItem().setArg("node", node.getName())
            self.clearWidgets()
            self.populateParameterWidgets(new=new)

        # existing node
        else:
            # update AOV Parameter Widgets
            if aov_type == self.aovType() and not self.isFrozen():
                pass
            else:
                self.clearWidgets()
                self.populateParameterWidgets(new=new)

        # update drag/drop
        if aov_type == AOVGROUP:
            self.currentItem().setIsDroppable(True)
        else:
            self.currentItem().setIsDroppable(False)

    def currentItem(self):
        return self._current_item

    def setCurrentItem(self, item):
        self._current_item = item

    def isFrozen(self):
        return self._is_frozen

    def setIsFrozen(self, enabled):
        self._is_frozen = enabled

    def renderer(self):
        aov_manager = getWidgetAncestor(self, AOVManagerWidget)
        return aov_manager.renderer()

    def setRenderer(self, renderer):
        aov_manager = getWidgetAncestor(self, AOVManagerWidget)
        aov_manager.setRenderer(renderer)

    """ NODE"""
    def node(self):
        return NodegraphAPI.GetNode(self.currentItem().getArg("node"))

    def deleteNode(self):
        node = self.currentItem().getArg("node")
        if node:
            node.delete()

    def __createPrmanLPENode(self):
        return

    """ EVENTS """
    def updateNodeName(self, old_name, new_name):
        """ Updates a nodes name and returns the new name

        Args:
            old_name (str):
            new_name (str):
        """
        if not self.isFrozen():
            node = NodegraphAPI.GetNode(old_name)
            node.setName(new_name)
            self.currentItem().setArg("node", node.getName())
            if self.aovType() == AOVGROUP:
                self.currentItem().setArg("name", node.getName())
            self.widgets()["node"].setText(node.getName())
            return node.getName()

    def aovTypeChangedEvent(self, widget, value):
        """ Called when the user changes the AOV type using the "type" """
        # preflight
        # todo aov type changed event

        if self.isFrozen(): return

        if value == self.aovType(): return

        # illegal value
        if value not in self.aovTypes():
            widget.setText(self.aovType())
            return

        # set AOV type
        self.setAOVType(value)
        #aov_manager = getWidgetAncestor(self, AOVManagerWidget)
        #aov_manager.updateDelegateDisplay()

    def aovNameChangedEvent(self, widget, value):
        """ When the user updates the name from the header title, this will run"""
        if not self.isFrozen():
            self.currentItem().setArg("name", value)

            self.parametersWidget().setTitle(value)
            self.widgets()["name"].setText(value)
            if self.aovType() == AOVGROUP:
                self.updateNodeName(self.currentItem().getArg("node"), value)

        return

    def parameterChangedEvent(self, widget, value):
        """ User has changed a dynamic parameter"""
        param_name = widget.objectName()

        # preflight
        if self.getItemArg(param_name):
            if value == self.getItemArg(param_name): return
        if self.isFrozen(): return

        # update parameter
        #self.setIsFrozen(True)
        # update node name
        """ Special case is needed here as the node name may change when set"""
        if param_name == "node":
            new_node_name = self.updateNodeName(self.currentItem().getArg("node"), value)
            if self.aovType() == AOVGROUP:
                self.parametersWidget().setTitle(new_node_name)
                self.widgets()["name"].setText(new_node_name)

        else:
            if param_name == "name":
                self.parametersWidget().setTitle(value)
                if self.aovType() == AOVGROUP:
                    self.updateNodeName(self.currentItem().getArg("node"), value)
                    """ Need to freeze/exit here to ensure the node name stays synchronized"""
                    return

            # update metadata
            self.node().getParameter(param_name).setValue(value, 0)
            self.currentItem().setArg(param_name, value)

    @staticmethod
    def updateGUI(parent, widget, item):
        """
        parent (ShojiModelViewWidget)
        widget (ShojiModelDelegateWidget)
        item (ShojiModelItem)
        self --> widget.getMainWidget()
        """
        # get attrs
        self = widget.getMainWidget()

        # preflight
        renderer = self.renderer()
        if renderer not in renderEngines(): return

        # set item
        self.setCurrentItem(item)
        # print(item.columnData())
        self.setIsFrozen(True)

        # set type
        aov_type = item.getArg("type")
        if aov_type in self.aovTypes():
            self.setAOVType(aov_type, new=False)
            self.widgets()["type"].setText(str(aov_type))

        # set name
        item_name = item.getArg("name")
        self.parametersWidget().setTitle(item_name)

        for arg, value in item.args().items():
            if arg != "type":
                self.widgets()[arg].setText(value)

        self.setIsFrozen(False)


class AOVManagerItemDelegate(AbstractDragDropModelDelegate):
    """ Item delegate used for the main header view

    This will show different delegates for the name change, and the AOV type change."""
    def __init__(self, parent=None):
        super(AOVManagerItemDelegate, self).__init__(parent)
        self.setDelegateWidget(ListInputWidget)
        self._parent = parent

    def setModelData(self, editor, model, index):
        """ Create custom delegate for the type popup"""

        # check TYPE set
        if index.column() == 1:
            new_value = editor.text()
            aov_manager_item_widget = getWidgetAncestor(self, AOVManagerWidget)
            if new_value not in aov_manager_item_widget.aovTypes():
                editor.setText(self._aov_type)
                return

        # update LPE display
        if index.column() == 2:
            aov_manager = getWidgetAncestor(self, AOVManagerWidget)
            aov_manager.updateDelegateDisplay()

        # todo update display
        """ When the user finishes editing an item in the view, this will be run"""
        return AbstractDragDropModelDelegate.setModelData(self, editor, model, index)

    def createEditor(self, parent, option, index):
        """ Creates a custom editor for the "type" column """
        if index.column() == 1:
            delegate_widget = self.delegateWidget(parent)
            delegate_widget.filter_results = False
            aov_manager_item_widget = getWidgetAncestor(parent, AOVManagerWidget)
            delegate_widget.populate([[item] for item in sorted(aov_manager_item_widget.aovTypes())])
            self._aov_type = delegate_widget.text()
            return delegate_widget

        if index.column() == 2:
            if index.internalPointer().getArg("type") == AOVGROUP:
                return
        return AbstractDragDropModelDelegate.createEditor(self, parent, option, index)


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication
    from cgwidgets.utils import centerWidgetOnScreen

    app = QApplication(sys.argv)
    widget = AOVManagerEditor()
    widget.show()
    widget.resize(512, 512)
    centerWidgetOnScreen(widget)
    sys.exit(app.exec_())