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
    *   Populate rendererType

Todo (BUGS):
    *   Renderer changed and updating from view causes conflicts

ToDo (Light Groups)
    *   Get all Light Groups list (getLightGroups)
    *   Add Arnold

Use a ShojiMVW to create an interface for AOV"s
Items
    GROUP | LIGHT | LPE | CUSTOM
    AOV Item
        * AOVItems will hold all of the necessary parameters the user needs to create a new AOV
        * Presets / LPE"s / Lights
    - Each item is linked to a node via the nodes name
    - Each node"s parameters are linked to the column data of the item

Hierarchy
AOVManagerEditor --> (AbstractSuperToolEditor)
    |- QVBoxLayout
        |- aovManager --> (ShojiModelViewWidget)
            |- AOVManagerItemWidget --> (AOVManagerItemWidget)
                |- QVBoxLayout
                    |- parametersWidget
                        |* parameter_widgets --> (LabelledInputWidget (LIST | STRING | FLOAT)
                        |- advanced_button_scroll_area_widget --> (QScrollArea)
                            |- advanced_button_main_widget --> (QWidget)
                                |- advanced_button_layout --> (QVBoxLayout)
                                    |- advanced_button_widget --> (ButtonInputWidget)
                                    |- teleparam_widget
                                    |- teleparam_widget

Data:
    type : TYPE (GROUP | LIGHT | LPE)
    name : str()
    children : list()
    enabled : bool
    expanded : bool

AOVMAP
    Needs to have the same items in the dictionary as the parameters on the nodes


"""

from qtpy.QtWidgets import QVBoxLayout, QLabel, QWidget, QScrollArea
from qtpy.QtCore import Qt, QModelIndex

from Katana import NodegraphAPI

from cgwidgets.widgets import (
    ButtonInputWidget,
    ButtonInputWidgetContainer,
    FrameInputWidgetContainer,
    FloatInputWidget,
    ListInputWidget,
    LabelledInputWidget,
    ModelViewWidget,
    ShojiModelViewWidget,
    StringInputWidget
)
from cgwidgets.settings import attrs
from cgwidgets.utils import getFontSize, getWidgetAncestor
from cgwidgets.views import AbstractDragDropModelDelegate

from Widgets2 import AbstractSuperToolEditor, iParameter
from Utils2 import paramutils, nodeutils

# MAPPING TABLES

# Renderers
ARNOLD = "Arnold"
PRMAN = "Prman"
DELIGHT = "Delight"
REDSHIFT = "Redshift"

# LPE AOVS
SPECULAR = "SPEC"
SPECULAR_INDIRECT = "iSPEC"
SPECULAR_ROUGHNESS = "SPECR"
DIFFUSE_RAW = "rDIFF"
DIFFUSE = "DIFF"
DIFFUSE_INDIRECT = "iDIFF"
EMISSIVE = "GLOW"
SUBSURFACE = "SSS"
TRANSMISSIVE = "TRANS"

LPE = "LPE"
AOVGROUP = "GROUP"
LIGHT = "LIGHT"
CUSTOM = "CUSTOM"

AOVMAP = {
    "Prman": {
        LPE: {"base_type": LPE, "lpe": "lpe:", "name": "<NewAOV>", "renderer_type": "color"},
        SPECULAR: {"base_type": LPE, "lpe": "lpe:C<RS>[<L.>O]", "name": SPECULAR, "renderer_type": "color"},
        SPECULAR_INDIRECT: {"base_type": LPE, "lpe": "lpe:C<RS>.+[<L.>O]", "name": SPECULAR_INDIRECT, "renderer_type": "color"},
        DIFFUSE: {"base_type": LPE, "lpe": "lpe:C<RD>[<L.>O]", "name": DIFFUSE, "renderer_type": "color"},
        DIFFUSE_INDIRECT: {"base_type": LPE, "lpe": "lpe:C<RD>.+[<L.>O]", "name": DIFFUSE_INDIRECT, "renderer_type": "color"},
        DIFFUSE_RAW: {"base_type": LPE, "lpe": "lpe:CU2[<L.>O]", "name": DIFFUSE_RAW, "renderer_type": "color"},
        SUBSURFACE: {"base_type": LPE, "lpe": "lpe:C<TD>.*[<L.>O]", "name": SUBSURFACE, "renderer_type": "color"},
        TRANSMISSIVE: {"base_type": LPE, "lpe": "lpe:C<TS>.*[<L.>O]", "name": TRANSMISSIVE, "renderer_type": "color"},
        LIGHT: {"base_type": LIGHT, "lpe": "", "name": LIGHT, "renderer_type": "color", "light_group":"", "light_group_type":"BOTH"}

    },
    "Arnold": {
        LPE: {"base_type": LPE, "lpe": "", "name": "<NewAOV>", "renderer_type": "RGB"},
        SPECULAR: {"base_type": LPE, "lpe": "C<RS>L", "name": SPECULAR, "renderer_type": "RGB"},
        SPECULAR_INDIRECT: {"base_type": LPE, "lpe": "C<RS>[DSVOB].*", "name": SPECULAR_INDIRECT, "renderer_type": "RGB"},
        DIFFUSE: {"base_type": LPE, "lpe": "C<RD>L", "name": DIFFUSE, "renderer_type": "RGB"},
        DIFFUSE_INDIRECT: {"base_type": LPE, "lpe": "C<RD>[DSVOB].*", "name": DIFFUSE_INDIRECT, "renderer_type": "RGB"},
        DIFFUSE_RAW: {"base_type": LPE, "lpe": "C<RD>A", "name": DIFFUSE_RAW, "renderer_type": "RGB"},
        SUBSURFACE: {"base_type": LPE, "lpe": "C<TD>.*", "name": SUBSURFACE, "renderer_type": "RGB"},
        TRANSMISSIVE: {"base_type": LPE, "lpe": "C<TS>.*", "name": TRANSMISSIVE, "renderer_type": "RGB"},

    },
    "Redshift": {},
    "Delight": {}
}
TYPESMAP = {
    "Arnold": [
        "BYTE",
        "INT",
        "UINT",
        "BOOL",
        "FLOAT",
        "RGB",
        "RGBA",
        "VECTOR",
        "VECTOR2",
        "STRING",
        "POINTER",
        "NODE",
        "ARRAY",
        "MATRIX"
    ],
    "Prman": [
        "color",
        "float",
        "point",
        "normal",
        "vector",
        "int"
    ],
    "Redshift": [],
    "Delight": []
}
LIGHT_TYPE_DIFF = DIFFUSE
LIGHT_TYPE_SPEC = SPECULAR
LIGHT_TYPE_BOTH = "BOTH"

LPEAOVS = [
    SPECULAR,
    SPECULAR_INDIRECT,
    SPECULAR_ROUGHNESS,
    DIFFUSE_RAW,
    DIFFUSE,
    DIFFUSE_INDIRECT,
    EMISSIVE,
    SUBSURFACE,
    TRANSMISSIVE,
    LPE
]
RENDERENGINES = [ARNOLD, DELIGHT, PRMAN, REDSHIFT]


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
            "renderer",
            paramutils.STRING,
            self._renderer_widget.text,
            self.rendererChangedEvent,
            initial_value=""
        )
        # if self.node().getParameter("renderer"):
        #     self._renderer_widget.setText(self.node().getParameter("renderer").getValue(0))
        self._renderer_widget.filter_results = False
        self._renderer_widget.populate([[renderer] for renderer in RENDERENGINES])
        self._renderer_labelled_widget = LabelledInputWidget(
            name="Renderer", delegate_widget=self._renderer_widget)
        self._renderer_labelled_widget.setFixedHeight(getFontSize() * 3)
        self._renderer_labelled_widget.setDefaultLabelLength(getFontSize() * 10)

        self._render_location_widget = self.createCustomParameterWidget(StringInputWidget)
        self.createCustomParam(
            self._render_location_widget,
            "renderLocation",
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
    """ Main display for showing the user the current AOV"s available to them.

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
        self.setHeaderItemTextChangedEvent(self.aovTextChangedEvent)
        self.setHeaderItemEnabledEvent(self.aovEnabledEvent)
        self.setHeaderItemDeleteEvent(self.aovDeleteEvent, update_first=False)
        self.setHeaderItemDropEvent(self.aovDroppedEvent)

        render_settings_node = None
        nodes = [node for node in reversed(self.node().getChildren()) if node != render_settings_node]
        self.populate(nodes)

    """ UTILS """
    def populate(self, nodes, parent=QModelIndex()):
        """ Populates the user defined AOV"s on load"""
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
        node_name_list = [child.columnData()["node"] for child in children]
        node_list = [NodegraphAPI.GetNode(node) for node in node_name_list]

        return node_list

    def aovTypes(self):
        """ Returns a list of the different AOV types available"""
        aovs = AOVMAP[self.renderer()]
        aovs[AOVGROUP] = {"type": AOVGROUP}
        return aovs.keys()

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
    def aovTextChangedEvent(self, item, old_value, new_value, column):
        """ Run when the user updates an item in the view

        Note:
            Only need to set the widget for the AOVType change as that is the
            only arg that needs to dynamically repopulate parameters"""
        # name changed
        if column == 0:
            # set node name
            node = NodegraphAPI.GetNode(item.getArg("node"))
            if item.getArg("type") == AOVGROUP:
                node.setName(new_value)
                item.setArg("node", node.getName())

            item.setArg("name", new_value)
            node.getParameter("name").setValue(new_value, 0)

        # type changed
        if column == 1:
            aov_type = new_value
            delegate_widget = self.activeDelegateWidgets()[0]
            delegate_widget.widgets()["type"].setText(aov_type)
            delegate_widget.setAOVType(aov_type, new=True)

        # lpe
        if column == 2:
            lpe = new_value
            node = NodegraphAPI.GetNode(item.getArg("node"))

            item.setArg("lpe", lpe)
            node.getParameter("lpe").setValue(lpe, 0)

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
        if parent.getArg("name") == "root":
            parent_node = self.node()

        # drop items
        for item in items_dropped:
            # get node
            node = NodegraphAPI.GetNode(item.getArg("node"))

            # disconnect node
            nodeutils.disconnectNode(node, input=True, output=True, reconnect=True)

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


""" AOV DELEGATE WIDGETS"""
class AOVManagerItemWidget(QWidget):
    """ The widget displayed when a user selects an item in the AOVManagerWidget

    Attributes:
        aovType (str(TYPE)): the current type of AOV this is valid options are
            CUSTOM | GROUP | LIGHT | LPE
        currentItem (AbstractShojiModelItem):
        isFrozen (bool):
        node (Node): current node being manipulated
        widgets (dict): of parameters widgets.  Each key is an arg"s name, and the value
            is the widget.

    Hierarchy
    QWidget
        |- QVBoxLayout
            |- parametersWidget
                |- typeWidget
                |- lpeWidget
    """
    NON_DISPLAYABLE_PARAMETERS = ["node", "name"]

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
    def createAOVMacro(self, renderer, aov_type):
        """ Creates the Macro/Group node associated with the selected AOV/Engine

        Args:
            renderer (str):
            aov_type (str):
        """

        if aov_type == AOVGROUP:
            node_name = "__aovGroup"
        else:
            base_aov_type = AOVMAP[renderer][aov_type]["base_type"]
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

    def getLightGroups(self):
        # todo get light groups
        return []

    """ WIDGETS ( INIT )"""
    def addParameterWidget(self, name, delegate_widget, finished_editing_function=None, new=True):
        """ Adds a parameter widget to the current display

        Args:
            name (str): name of arg
            delegate_widget (QWidget): Widget for user to input values
            finished_editing_function (func): Function to be run when the user
                has finished editing.  This function should take the args (widget, value)
            new (bool): determines if this is a new parameter, or updating an existing one

        Returns (LabelledInputWidget)
        """

        # create input widget
        input_widget = LabelledInputWidget(name=name, delegate_widget=delegate_widget)
        input_widget.setDefaultLabelLength(getFontSize() * 7)
        input_widget.setFixedHeight(getFontSize() * 3)

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

        return input_widget

    def populateParameterWidgets(self, new=True):
        """ Populates all of the parameters from the node

        Args:
            new (bool): determines if these are new parameters, or existing ones"""
        # cleanup old widgets
        self.clearNonAbstractParameterWidget()

        # populate parameters
        if (self.aovType() in LPEAOVS) or (self.aovType() == AOVGROUP):
            self.__createLPEParameterWidgets(new=new)

        # todo LIGHT GROUPS
        if self.aovType() == LIGHT:
            self.__createLightGroupParameterWidgets(new)

    def __createTypeParameterWidget(self, new=True):
        """ Creates the type parameter widget"""
        delegate_widget = ListInputWidget(self)
        delegate_widget.filter_results = False
        delegate_widget.populate([[aov] for aov in self.aovTypes()])
        input_widget = self.addParameterWidget("type", delegate_widget, self.aovTypeChangedEvent, new=new)
        return input_widget

    def __createLightGroupParameterWidgets(self, new=True):
        """ Creates all of the necessary widgets for the Light Group type"""
        self.__createTypeParameterWidget(new)

        light_group_widget = ListInputWidget()
        self.addParameterWidget("light_group", light_group_widget, self.lightGroupChangedEvent, new=new)
        self.widgets()["light_group"].setPopulateFunction(self.getLightGroups)

        self.widgets()["light_group_type"] = ButtonInputWidgetContainer()
        self.widgets()["light_group_type"].addButton(LIGHT_TYPE_DIFF, LIGHT_TYPE_DIFF, self.lightGroupTypeChangedEvent, False)
        self.widgets()["light_group_type"].addButton(LIGHT_TYPE_SPEC, LIGHT_TYPE_SPEC, self.lightGroupTypeChangedEvent, False)
        self.widgets()["light_group_type"].addButton(LIGHT_TYPE_BOTH, LIGHT_TYPE_BOTH, self.lightGroupTypeChangedEvent, True)
        self.widgets()["light_group_type"].setIsMultiSelect(False)
        self._parameters_widget.addInputWidget(self.widgets()["light_group_type"])

        # update default item args
        self.currentItem().setArg("name", self.node().getParameter("name").getValue(0))
        self.currentItem().setArg("light_group_type", self.node().getParameter("light_group_type").getValue(0))
        self.currentItem().setArg("light_group", self.node().getParameter("light_group").getValue(0))
        self.currentItem().setArg("lpe", self.node().getParameter("lpe").getValue(0))

    def __createLPEParameterWidgets(self, new=True):
        """ Creates all of the parameter widgets associated with an LPE aov"""
        # get attrs
        node = NodegraphAPI.GetNode(self.currentItem().getArg("node"))
        parameter_map = paramutils.getParameterMapFromNode(node)

        for param_name, param_value in parameter_map.items():
            if param_name == "type":
                input_widget = self.__createTypeParameterWidget(new)
            else:
                if isinstance(param_value, str):
                    delegate_widget = StringInputWidget()
                elif isinstance(param_value, float):
                    delegate_widget = FloatInputWidget()
                input_widget = self.addParameterWidget(param_name, delegate_widget, self.parameterChangedEvent, new=new)

            # hide non displayable parameters
            if param_name in AOVManagerItemWidget.NON_DISPLAYABLE_PARAMETERS:
                input_widget.hide()

        self.__createAdvancedButtonWidget()

    def __createAdvancedButtonWidget(self):
        """ Creates the advanced button display
        advanced_button_scroll_area_widget --> (QScrollArea)
            |- advanced_button_main_widget --> (QWidget)
                |- advanced_button_layout --> (QVBoxLayout)
                    |- advanced_button_widget --> (ButtonInputWidget)
                    |- teleparam_widget
                    |- teleparam_widget
        """
        # create widgets
        self._advanced_button_main_widget = QWidget()
        self._advanced_button_scroll_area = QScrollArea()
        self._advanced_button_scroll_area.setWidgetResizable(True)

        self._advanced_button_scroll_area.setWidget(self._advanced_button_main_widget)

        self._advanced_button_layout = QVBoxLayout(self._advanced_button_main_widget)
        self._advanced_button_layout.setAlignment(Qt.AlignTop)

        self._advanced_button_widget = ButtonInputWidget(
            title="Advanced", is_toggleable=True, user_clicked_event=self.advancedButtonPressedEvent)

        # setup layout
        self._advanced_button_widget.setFixedHeight(getFontSize() * 3)
        self._advanced_button_layout.addWidget(self._advanced_button_widget)
        self.parametersWidget().addInputWidget(self._advanced_button_scroll_area)

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

    def advancedButtonWidget(self):
        return self._advanced_button_widget

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
        if renderer not in RENDERENGINES: return
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
    def aovTypeChangedEvent(self, widget, value):
        """ Called when the user changes the AOV type using the "type" """
        # preflight
        if self.isFrozen(): return
        if value == self.aovType(): return

        # illegal value
        if value not in self.aovTypes():
            widget.setText(self.aovType())
            return

        # set AOV type
        self.setAOVType(value)

    def aovNameChangedEvent(self, widget, value):
        """ When the user updates the name from the header title, this will run"""
        if not self.isFrozen():
            self.currentItem().setArg("name", value)

            self.parametersWidget().setTitle(value)
            self.node().getParameter("name").setValue(value, 0)
            # self.widgets()["name"].setText(value)
            if self.aovType() == AOVGROUP:
                self.nodeNameChangedEvent(self.currentItem().getArg("node"), value)

        return

    def advancedButtonPressedEvent(self, widget):
        if widget.is_selected:
            # create tele param widgets
            for node in self.node().getChildren():
                param_widget = paramutils.createTeleparamWidget(node.getName(), open=str(False))
                self._advanced_button_layout.addWidget(param_widget)
                param_widget.show()

            # update text
            widget.setText("simple")

        else:
            # remove tele param widgets
            for i in reversed(range(1, 3)):
                self._advanced_button_layout.itemAt(i).widget().setParent(None)

            # set text to advanced
            widget.setText("advanced")

    def lightGroupChangedEvent(self, widget, value):
        self.parameterChangedEvent(widget, value)
        self.currentItem().setArg("lpe", self.node().getParameter("lpe").getValue(0))

    def lightGroupTypeChangedEvent(self, widget):
        """ Updates the LPE to catch the correct lights"""
        light_group_type = widget.flag()
        self.currentItem().setArg("light_group_type", light_group_type)
        self.node().getParameter("light_group_type").setValue(light_group_type, 0)

        self.currentItem().setArg("lpe", self.node().getParameter("lpe").getValue(0))

    def nodeNameChangedEvent(self, old_name, new_name):
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
            new_node_name = self.nodeNameChangedEvent(self.currentItem().getArg("node"), value)
            if self.aovType() == AOVGROUP:
                self.parametersWidget().setTitle(new_node_name)
                #self.widgets()["name"].setText(new_node_name)

        else:
            if param_name == "name":
                self.parametersWidget().setTitle(value)
                if self.aovType() == AOVGROUP:
                    self.nodeNameChangedEvent(self.currentItem().getArg("node"), value)
                    """ Need to freeze/exit here to ensure the node name stays synchronized"""
                    return

            # update metadata
            self.node().getParameter(param_name).setValue(value, 0)
            self.currentItem().setArg(param_name, value)
            # print("setting ", param_name, "to", value)

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
        if renderer not in RENDERENGINES: return

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

        # Update LPE / GROUP
        # if (self.aovType() in LPEAOVS) or (self.aovType() == AOVGROUP):
        #     for arg, value in item.args().items():
        #         if arg != "type":
        #             self.widgets()[arg].setText(value)

        # Update Light
        if self.aovType() == LIGHT:
            # update light group type
            self.widgets()["light_group_type"].setButtonAsCurrent(
                self.widgets()["light_group_type"].buttons()[item.getArg("light_group_type")], True
            )

            # update light group name
            # self.widgets()["light_group"].setText(item.getArg("light_group"))
        # unfreeze
        self.setIsFrozen(False)


class AOVManagerItemDelegate(AbstractDragDropModelDelegate):
    """ Item delegate used for the main header view

    This will show different delegates for the name change, and the AOV type change."""
    def __init__(self, parent=None):
        super(AOVManagerItemDelegate, self).__init__(parent)
        self.setDelegateWidget(ListInputWidget)
        self._parent = parent

    # def setAOVType(self, widget, value):
    #     aov_manager = getWidgetAncestor(self, AOVManagerWidget)
    #     selected_items = aov_manager.self.getAllSelectedItems()
    #     if 0 < len(selected_items):
    #         current_item = selected_items[0]
    #         current_item.

    def setModelData(self, editor, model, index):
        """ Create custom delegate for the type popup"""
        # check TYPE set
        # if index.column() == 1:
        #     new_value = editor.text()
        #     aov_manager = getWidgetAncestor(self, AOVManagerWidget)
        #     if new_value not in aov_manager.aovTypes():
        #         editor.setText(self._aov_type)
        #         return
        #     AbstractDragDropModelDelegate.setModelData(self, editor, model, index)
        #     aov_manager.updateDelegateDisplay()
        #     return

        # update LPE display
        if index.column() == 2:
            aov_manager = getWidgetAncestor(self, AOVManagerWidget)
            aov_manager.updateDelegateDisplay()

        # todo update display
        """ When the user finishes editing an item in the view, this will be run"""
        return AbstractDragDropModelDelegate.setModelData(self, editor, model, index)

    def createEditor(self, parent, option, index):
        """ Creates a custom editor for the "type" column """
        # preflight
        aov_manager_widget = getWidgetAncestor(parent, AOVManagerWidget)

        if index.column() == 1:
            # preflight
            if aov_manager_widget.renderer() not in RENDERENGINES: return

            # create delegate
            delegate_widget = self.delegateWidget(parent)
            delegate_widget.filter_results = False
            aov_manager_widget = getWidgetAncestor(parent, AOVManagerWidget)
            delegate_widget.populate([[item] for item in sorted(aov_manager_widget.aovTypes())])

            self._aov_type = delegate_widget.text()
            return delegate_widget

        if index.column() == 2:
            # preflight
            if aov_manager_widget.renderer() not in RENDERENGINES: return
            if index.internalPointer().getArg("type") not in LPEAOVS: return

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