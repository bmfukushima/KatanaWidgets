"""
Todo:
    *   Item type storage Group vs AOV
            - Populate | Expand on startup
    *   Setup Node
        -   Presets, Lights, Custom, Denoise
        -   Create Node data
                AOVManagerItemWidget --> setAOVType
                                     --> updateGUI
        -   RenderSettings node
                enable/disable update

Use a ShojiMVW to create an interface for AOV's
Items
    GROUP | LIGHT | LPE | PRESET
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
    type : TYPE (GROUP | LIGHT | LPE | PRESET)
    name : str()
    children : list()
    enabled : bool
    expanded : bool



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

save_location = "/media/ssd01/dev/sandbox/aovManager.json"

# MAPPING TABLES
LPE = "LPE"
LIGHT = "Light"
AOVGROUP = "Group"
PRESET = "PRESET"
SPEC = "SPEC"

ARNOLD = "Arnold"
PRMAN = "Prman"
DELIGHT = "Delight"
REDSHIFT = "Redshift"

def aovTypes():
    return [LPE, LIGHT, AOVGROUP, PRESET]

def renderEngines():
    return [ARNOLD, DELIGHT, PRMAN, REDSHIFT]


class AOVManagerEditor(AbstractSuperToolEditor):
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
    def saveLocation(self):
        return self.aovManager().saveLocation()

    def setSaveLocation(self, save_location):
        return self.aovManager().setSaveLocation(save_location)

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
        node (Node): current node
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
        self._renderer = ""
        self._save_location = save_location

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
        nodes = [node for node in self.node().getChildren() if node != render_settings_node]
        self.populate(nodes)

    """ UTILS """
    def populate(self, nodes, parent=QModelIndex()):
        """ Populates the user defined AOV's on load

        # Todo populate from children, and not from data
        """
        for node in nodes:
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
        return self._renderer

    def setRenderer(self, renderer):
        self._renderer = renderer

    def saveLocation(self):
        return self._save_location

    def setSaveLocation(self, save_location):
        self._save_location = save_location

    """ EVENTS """
    def aovNameChangedEvent(self, item, old_value, new_value):
        # set node name
        node = NodegraphAPI.GetNode(item.getArg("node"))
        if item.getArg("type") == AOVGROUP:
            node.setName(new_value)
            item.setArg("node", node.getName())

        item.setArg("name", node.getName())
        node.getParameter("name").setValue(node.getName(), 0)

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
        #return_val = super(ShojiModelViewWidget, self).showEvent(event)
        self.setHeaderWidgetToDefaultSize()
        return ShojiModelViewWidget.showEvent(self, event)
        #return return_val


""" AOV DELEGATE WIDGETS"""
class AOVManagerItemWidget(QWidget):
    """ The widget displayed when a user selects an item in the AOVManagerWidget

    Attributes:
        aovType (str(TYPE)): the current type of AOV this is valid options are
            CUSTOM | GROUP | LIGHT | LPE | PRESET
        currentItem (AbstractShojiModelItem):
        isFrozen (bool):
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
    def addParameterWidget(self, name, delegate_widget, finished_editing_function):
        """ Adds a parameter widget to the current display"""
        # create input widget
        input_widget = LabelledInputWidget(name=name, delegate_widget=delegate_widget)
        input_widget.setDefaultLabelLength(getFontSize() * 7)

        # set widget orientation
        input_widget.setDirection(Qt.Horizontal)

        # add to group layout
        self._parameters_widget.addInputWidget(input_widget, finished_editing_function=finished_editing_function)
        delegate_widget.setObjectName(name)
        self.widgets()[name] = delegate_widget

        if self.node().getParameter(name):
            delegate_widget.setText(self.node().getParameter(name).getValue(0))

    def populateParameterWidgets(self):
        """ Populates all of the parameters from the node"""
        node = NodegraphAPI.GetNode(self.currentItem().getArg("node"))
        parameter_map = paramutils.getParameterMapFromNode(node)
        self.clearNonAbstractParameterWidget()
        for param_name, param_value in parameter_map.items():
            if param_name == "type":
                delegate_widget = ListInputWidget(self)
                delegate_widget.filter_results = False
                delegate_widget.populate([[aov] for aov in aovTypes()])
                self.addParameterWidget("type", delegate_widget, self.aovTypeChangedEvent)
            else:
                if isinstance(param_value, str):
                    delegate_widget = StringInputWidget()
                elif isinstance(param_value, float):
                    delegate_widget = FloatInputWidget()
                self.addParameterWidget(param_name, delegate_widget, self.parameterChangedEvent)

        pass

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
        return self.currentItem().getArg("type")

    def createAOVMacro(self, renderer, aov_type):
        """ Creates the Macro/Group node associated with the selected AOV/Engine

        Args:
            renderer (str):
            aov_type (str):
        """
        if aov_type == AOVGROUP:
            node_name = "__aovGroup"
        else:
            node_name = "__aov{RENDERER}{TYPE}".format(RENDERER=renderer, TYPE=aov_type)

        # create node
        old_node = self.node()
        new_node = NodegraphAPI.CreateNode(node_name, self.node().getParent())
        nodeutils.replaceNode(old_node, new_node)

        return new_node

    def setAOVType(self, aov_type):
        """ Sets the current items AOV type and updates the display """
        # preflight
        renderer = self.renderer()
        if renderer not in renderEngines(): return

        # Create new node if needed
        if self.node().getParameter("type").getValue(0) != aov_type:
            self.currentItem().setArg("type", aov_type)
            node = self.createAOVMacro(renderer, aov_type)
            self.currentItem().setArg("node", node.getName())

        # update AOV Parameter Widgets
        if aov_type in aovTypes():
            if aov_type == self.aovType() and not self.isFrozen():
                pass
            else:
                self.clearWidgets()
                self.populateParameterWidgets()

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
        if self.isFrozen(): return

        # illegal value
        if value not in aovTypes():
            widget.setText(self.aovType())
            return

        # set AOV type
        self.setAOVType(value)
        aov_manager = getWidgetAncestor(self, AOVManagerWidget)
        aov_manager.updateDelegateDisplay()

    def aovNameChangedEvent(self, widget, value):
        """ When the user updates the name from the header title, this will run"""
        self.currentItem().setArg("name", value)

        self.parametersWidget().setTitle(value)
        self.widgets()["name"].setText(value)
        if self.aovType() == AOVGROUP:
            self.updateNodeName(self.currentItem().getArg("node"), value)

        return

    def parameterChangedEvent(self, widget, value):
        """ User has changed a dynamic parameter"""
        param_name = widget.objectName()
        if not self.isFrozen():
            self.setIsFrozen(True)
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
                        self.setIsFrozen(False)
                        return

                # update metadata
                self.node().getParameter(param_name).setValue(value, 0)
                self.currentItem().setArg(param_name, value)

            self.setIsFrozen(False)

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
        self.setIsFrozen(True)

        # set type
        aov_type = item.getArg("type")
        if aov_type in aovTypes():
            self.setAOVType(aov_type)
            self.widgets()["type"].setText(str(aov_type))

        # populate parameters
        for arg in item.args():
            if arg != "type":
                self.widgets()[arg].setText(item.getArg(arg))

        # # set name
        item_name = item.getArg("name")
        self.parametersWidget().setTitle(item_name)

        # todo | update parameters on selection change
        if aov_type in aovTypes():
            if aov_type == AOVGROUP:
                pass

            if aov_type == LPE:
                # set lpe
                pass

            if aov_type == LIGHT:
                pass

            if aov_type == PRESET:
                pass

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
            if new_value not in aovTypes():
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
            delegate_widget.populate([[item] for item in sorted(aovTypes())])
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