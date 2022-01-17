"""
Todo:
    *   Item Parameter displays
            Need to create this for the different item types, and connect the signals
    *   Item type storage Group vs AOV
            - Populate | Expand on startup
    *   Item set name/disable/delete (AOVManagerWidget)
            - Update nodes (enable / delete / name change)
    *   Store hierarchical data
            export model (AbstractAOVManagerEditor --> saveData)
    *   Setup Node
    *   Change items from
            CUSTOM | GROUP | LIGHT | LPE | PREDEFINED
                to
            LIGHT | LPE | GROUP | PRESET... | DIFF | SPEC | SPECR
        Need an add preset option

Use a ShojiMVW to create an interface for AOV's
Items
    CUSTOM | GROUP | LIGHT | LPE | PREDEFINED
    AOV Item
        * AOVItems will hold all of the necessary parameters the user needs to create a new AOV
        * Presets / LPE's / Lights

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
    type : TYPE (GROUP | LIGHT | LPE | PREDEFINED)
    name : str()
    children : list()
    enabled : bool
    expanded : bool


"""

import json

from qtpy.QtWidgets import QVBoxLayout, QLabel, QWidget
from qtpy.QtCore import Qt, QModelIndex

from cgwidgets.widgets import (
    ButtonInputWidget,
    FrameInputWidgetContainer,
    ListInputWidget,
    LabelledInputWidget,
    ModelViewWidget,
    ShojiModelViewWidget,
    StringInputWidget
)
from cgwidgets.settings import attrs
from cgwidgets.utils import getFontSize, getJSONData, getWidgetAncestor
from cgwidgets.views import AbstractDragDropModelDelegate
# from Widgets2 import AbstractSuperToolEditor
#

# # class AOVManagerEditor(AbstractSuperToolEditor):
# class AOVManagerEditor(AbstractSuperToolEditor):
#     def __init__(self, parent, node):
#         super(AOVManagerEditor, self).__init__(parent, node)
#
#         # setup layout
#         QVBoxLayout(self)
#         for x in range(5):
#             self.layout().addWidget(QLabel(str(x)))
#         self.layout().setAlignment(Qt.AlignTop)
#         #self.insertResizeBar()

save_location = "/media/ssd01/dev/sandbox/aovManager.json"

LPE = "lpe"
LIGHT = "light"
AOVGROUP = "group"
PREDEFINED = "predefined"

ARNOLD = "arnold"
PRMAN = "prman"
DELIGHT = "delight"
REDSHIFT = "redshift"

def aovTypes():
    return [LPE, LIGHT, AOVGROUP, PREDEFINED]

def renderEngines():
    return [ARNOLD, DELIGHT, PRMAN, REDSHIFT]

class AbstractAOVManagerEditor(QWidget):
    def __init__(self, parent=None):
        super(AbstractAOVManagerEditor, self).__init__(parent)

        # setup attrs
        self._renderer = ""

        # setup widgets
        self._renderer_widget = ListInputWidget(self)
        self._renderer_widget.filter_results = False
        self._renderer_widget.populate([[renderer] for renderer in renderEngines()])
        self._renderer_widget.setUserFinishedEditingEvent(self.rendererChangedEvent)
        renderer_labelled_widget = LabelledInputWidget(
            name="Renderer", delegate_widget=self._renderer_widget)
        renderer_labelled_widget.setFixedHeight(getFontSize() * 3)
        renderer_labelled_widget.setDefaultLabelLength(getFontSize() * 10)

        self._aov_manager = AOVManagerWidget()

        # create layout
        QVBoxLayout(self)
        self.layout().addWidget(renderer_labelled_widget)
        self.layout().addWidget(self._aov_manager)

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

    """ UTILS """
    def exportAOVData(self):
        return self.aovManager().exportAOVData()

    """ EVENTS """
    def rendererChangedEvent(self, widget, value):
        self.setRenderer(value)

    def keyPressEvent(self, event):
        modifiers = event.modifiers()
        if modifiers == Qt.AltModifier:
            if event.key() == Qt.Key_A:
                print(self.exportAOVData())


class AOVManagerWidget(ShojiModelViewWidget):
    """ Main display for showing the user the current AOV's available to them.

    Attributes:
        renderer (string): render engine being used
            arnold | delight | prman | redshift
        saveLocation (string): path on disk to save to.
            # todo this will eventually be updated to a parameter

    """
    def __init__(self, parent=None):
        super(AOVManagerWidget, self).__init__(parent)
        # setup attrs
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
        self.setItemExportDataFunction(self.exportAOVItem)

        self.populate(reversed(getJSONData(save_location, ordered=False)["data"]))

    """ UTILS """
    def populate(self, children, parent=QModelIndex()):
        """ Populates the user defined AOV's on load"""
        for child in children:
            new_index = self.createNewIndex(None, parent=parent, column_data=child)

            #
            new_index.internalPointer().setIsEnabled(child["enabled"])

            #
            if 0 < len(child["children"]):
                self.populate(reversed(child["children"]), parent=new_index)

            # todo expand on populate
            # if child["expanded"]:
            #     self.headerViewWidget().setExpanded(new_index, True)

    def exportAOVItem(self, item):
        """ Individual items dictionary when exported.

        Note:
            node has to come first.  This is due to how the item.name() function is called.
            As if no "name" arg is found, it will return the first key in the dict"""

        return {
            "name": item.getArg("name"),
            "children": [],
            "enabled": item.isEnabled(),
            "lpe": item.getArg("lpe"),
            "type": item.getArg("type"),
            "expanded": item.isExpanded(),
        }

    def exportAOVData(self):
        save_data = self.exportModelToDict(self.rootItem())

        # todo save_location
        with open(self.saveLocation(), "w") as file:
            json.dump(save_data, file)

        return save_data

    """ PROPERTIES """
    def saveLocation(self):
        return self._save_location

    def setSaveLocation(self, save_location):
        self._save_location = save_location

    def renderer(self):
        return self._renderer

    def setRenderer(self, renderer):
        self._renderer = renderer

    """ EVENTS """
    def aovNameChangedEvent(self, item, old_value, new_value):
        # todo aov name changed event | update node name
        self.exportAOVData()
        self.updateDelegateDisplay()

    def aovEnabledEvent(self, item, enabled):
        # todo aov enabled/disabled | disable node
        self.exportAOVData()

    def aovDeleteEvent(self, item):
        # todo aov delete event | delete node
        self.exportAOVData()

    def createNewIndex(self, widget, column_data=None, parent=QModelIndex()):
        """ Creates a new AOV Index.

        Args:
            widget (QWidget): button pressed (if applicable)
            column_data (dict): of data to be used for this item
            parent (QModelIndex): Parent index of item being created"""
        if not column_data:
            column_data = {"name": "NEW AOV", "type": "", "lpe":""}
        # todo add node to item
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


""" AOV DELEGATE WIDGETS"""
class AOVManagerItemWidget(QWidget):
    """ The widget displayed when a user selects an item in the AOVManagerWidget

    Attributes:
        aovType (str(TYPE)): the current type of AOV this is valid options are
            CUSTOM | GROUP | LIGHT | LPE | PREDEFINED
        currentItem (AbstractShojiModelItem):
        isFrozen (bool):

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

        # create main widget
        self._parameters_widget = FrameInputWidgetContainer(self, direction=Qt.Vertical)
        self._parameters_widget.setIsHeaderShown(True)
        self._parameters_widget.setHeaderTextChangedEvent(self.aovNameChangedEvent)

        # add type
        self._type_widget = ListInputWidget(self)
        self._type_widget.filter_results = False
        self._type_widget.populate([[aov] for aov in aovTypes()])

        # add lpe
        self._lpe_widget = StringInputWidget(self._parameters_widget)

        # setup layout
        QVBoxLayout(self)
        self.addParameterWidget("type", self._type_widget, self.aovTypeChangedEvent)
        self.addParameterWidget("lpe", self._lpe_widget, self.lpeChangedEvent)

        self.layout().addWidget(self._parameters_widget)
        self.layout().setContentsMargins(0, 0, 0, 0)

    def addParameterWidget(self, name, delegate_widget, finished_editing_function):

        input_widget = LabelledInputWidget(name=name, delegate_widget=delegate_widget)

        # set widget orientation
        input_widget.setDirection(Qt.Horizontal)

        # add to group layout
        self._parameters_widget.addInputWidget(input_widget, finished_editing_function=finished_editing_function)

    def clearNonAbstractParameterWidget(self):
        """ Sets the parametersWidget to a blank slate"""
        for widget in self.parametersWidget().delegateWidgets()[2:]:
            widget.setParent(None)
            widget.deleteLater()

    def __name__(self):
        return "abstract"
    #
    # def parametersWidget(self):
    #     return self._parameters_widget

    def item(self):
        return self._item

    def setItem(self, item):
        self._item = item

    """ WIDGETS """
    def parametersWidget(self):
        return self._parameters_widget

    def typeWidget(self):
        return self._type_widget

    def lpeWidget(self):
        return self._lpe_widget

    """ PROPERTIES """
    def aovType(self):
        return self.currentItem().getArg("type")

    def setAOVType(self, aov_type):
        """ Sets the current items AOV type and updates the display """

        # set items aov type
        self.currentItem().setArg("type", aov_type)

        # update display
        # todo update parameter display's
        self.clearNonAbstractParameterWidget()
        def updateFunction(widget, value):
            """ temp update function"""
            #print("update")
            pass

        if aov_type in aovTypes():
            if aov_type == AOVGROUP:
                widget = StringInputWidget("AOVGROUP")
                self.addParameterWidget("AOVGROUP", widget, updateFunction)

            if aov_type == LPE:
                widget = StringInputWidget("LPE")
                self.addParameterWidget("LPE", widget, updateFunction)

            if aov_type == LIGHT:
                widget = StringInputWidget("LIGHT")
                self.addParameterWidget("LIGHT", widget, updateFunction)

            if aov_type == PREDEFINED:
                widget = StringInputWidget("PREDEFINED")
                self.addParameterWidget("PREDEFINED", widget, updateFunction)

        self.setItem(self.currentItem())

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

    """ EVENTS """
    def lpeChangedEvent(self, widget, value):
        self.currentItem().setArg("lpe", value)

        aov_manager = getWidgetAncestor(self, AOVManagerWidget)
        aov_manager.exportAOVData()
        return

    def aovTypeChangedEvent(self, widget, value):
        """ Called when the user changes the AOV type using the "typeWidget" """
        # preflight
        if self.isFrozen(): return

        # illegal value
        if value not in aovTypes():
            widget.setText(self.aovType())
            return

        # set AOV type
        self.setAOVType(value)
        aov_manager = getWidgetAncestor(self, AOVManagerWidget)
        aov_manager.exportAOVData()

    def aovNameChangedEvent(self, widget, value):
        """ Updates the AOV's name """
        self.currentItem().setArg("name", value)

        self.parametersWidget().setTitle(value)

        aov_manager = getWidgetAncestor(self, AOVManagerWidget)
        aov_manager.exportAOVData()
        return

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
        self.setIsFrozen(True)

        # set item
        self.setCurrentItem(item)

        # set type
        item_type = item.getArg("type")
        if item_type in aovTypes():
            self.typeWidget().setText(str(item_type))
            self.setAOVType(item_type)

        # set name
        item_name = item.getArg("name")
        self.parametersWidget().setTitle(item_name)

        # set lpe
        lpe = item.getArg("lpe")
        self.lpeWidget().setText(str(lpe))

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
            aov_manager.exportAOVData()
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
    widget = AbstractAOVManagerEditor()
    widget.show()
    widget.resize(512, 512)
    centerWidgetOnScreen(widget)
    sys.exit(app.exec_())