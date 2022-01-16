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
            LIGHT | LPE | GROUP | PREDEFINED... | DIFF | SPEC | SPECR

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
                    |- type_labelled_widget --> (LabelledInputWidget)
                    |    |- type_widget --> (ListInputWidget)
                    |- parametersWidget ( one of the following )
                        |- CustomParametersWidget --> (QWidget)
                        |- GroupParametersWidget --> (QWidget)
                        |- LightParametersWidget --> (QWidget)
                        |- LPEParametersWidget --> (QWidget)
                        |- PredefinedParametersWidget --> (QWidget)
Data:
    type : TYPE (CUSTOM | GROUP | LIGHT | LPE | PREDEFINED)
    name : str()
    children : list()
    enabled : bool
    expanded : bool


"""

import json

from qtpy.QtWidgets import QVBoxLayout, QLabel, QWidget
from qtpy.QtCore import Qt, QModelIndex

from cgwidgets.widgets import (

    ShojiModelViewWidget,
    ButtonInputWidget,
    ListInputWidget,
    LabelledInputWidget,
    ModelViewWidget
)
from cgwidgets.settings import attrs
from cgwidgets.utils import getFontSize, getJSONData
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
CUSTOM = "custom"
PREDEFINED = "predefined"

def aovTypes():
    return [LPE, LIGHT, AOVGROUP, CUSTOM, PREDEFINED]


class AbstractAOVManagerEditor(QWidget):
    def __init__(self, parent=None):
        super(AbstractAOVManagerEditor, self).__init__(parent)

        # create layout
        QVBoxLayout(self)
        self._aov_manager = AOVManagerWidget()
        self.layout().addWidget(self._aov_manager)

    """ WIDGETS """
    def aovManager(self):
        return self._aov_manager

    """ UTILS """
    def exportAOVData(self):
        return self.aovManager().exportAOVData()

    def keyPressEvent(self, event):
        modifiers = event.modifiers()
        if modifiers == Qt.AltModifier:
            if event.key() == Qt.Key_A:
                print(self.exportAOVData())


class AOVManagerWidget(ShojiModelViewWidget):
    """ Main display for showing the user the current AOV's available to them."""
    def __init__(self, parent=None):
        super(AOVManagerWidget, self).__init__(parent)
        # setup attrs
        self._save_location = save_location

        self.setHeaderViewType(ModelViewWidget.TREE_VIEW)
        self._delegate = AOVManagerItemDelegate(parent=self)
        self.headerViewWidget().setItemDelegate(self._delegate)
        self.setHeaderPosition(attrs.WEST, attrs.SOUTH)
        self.setDelegateTitleIsShown(True)
        self.setHeaderData(["name", "type"])

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

        self.populate(getJSONData(save_location, ordered=False)["data"])

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
            column_data = {"name": "NEW AOV", "type": ""}
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
            |- type_labelled_widget --> (LabelledInputWidget)
            |    |- type_widget --> (ListInputWidget)
            |- parametersWidget ( one of the following )
                |- CustomParametersWidget --> (QWidget)
                |- GroupParametersWidget --> (QWidget)
                |- LightParametersWidget --> (QWidget)
                |- LPEParametersWidget --> (QWidget)
                |- PredefinedParametersWidget --> (QWidget)
    """

    def __init__(self, parent=None):
        super(AOVManagerItemWidget, self).__init__(parent)
        # attrs
        self._is_frozen = False

        # create type widget
        self._type_widget = ListInputWidget(self)
        self._type_widget.filter_results = False
        self._type_widget.setUserFinishedEditingEvent(self.aovTypeChangedEvent)
        self._type_widget.populate([[aov] for aov in aovTypes()])
        self._type_labelled_widget = LabelledInputWidget(name="type", delegate_widget=self._type_widget)

        # create type parameters
        self._parameters_widget = None

        # setup layout
        QVBoxLayout(self)
        self.layout().addWidget(self._type_labelled_widget)

    """ WIDGETS """
    def parametersWidget(self):
        return self._parameters_widget

    def setParametersWidget(self, widget):
        """ Sets the parameters widget to the one provided.

        This will also delete/remove the old parameters widget

        Args:
            widget (QWidget): Widget to use as parameters widget"""
        # remove old widget
        if self.parametersWidget():
            self.layout().removeWidget(self.parametersWidget())
            self.parametersWidget().deleteLater()
            # todo for some reason this seg faults...
            # self.parametersWidget().setParent(None)

        # add
        self.layout().addWidget(widget)
        self._parameters_widget = widget

    def typeWidget(self):
        return self._type_widget

    """ PROPERTIES """
    def aovType(self):
        return self.currentItem().getArg("type")

    def setAOVType(self, aov_type):
        """ Sets the current items AOV type and updates the display """

        # set items aov type
        self.currentItem().setArg("type", aov_type)

        # update display
        if aov_type in aovTypes():
            if aov_type == CUSTOM:
                parameter_widget = CustomParametersWidget()
            if aov_type == AOVGROUP:
                parameter_widget = AOVGroupParametersWidget()
            if aov_type == LPE:
                parameter_widget = LPEParametersWidget()
            if aov_type == LIGHT:
                parameter_widget = LightParametersWidget()
            if aov_type == PREDEFINED:
                parameter_widget = PredefinedParametersWidget()

            parameter_widget.setItem(self.currentItem())
            self.setParametersWidget(parameter_widget)

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

        # update attrs
        self.setCurrentItem(item)

        # update widgets

        # set item type
        item_type = item.getArg("type")
        if item_type in aovTypes():
            self.typeWidget().setText(str(item_type))
            self.setAOVType(item_type)

        # name = item.name()
        # name = parent.model().getItemName(item)
        # # self.testWidget().setText(name)
        #
        # print("===============")
        # print(item.getArg("type"))
        # print(widget)
        # print(name)

        self.setIsFrozen(False)


class AOVManagerItemDelegate(AbstractDragDropModelDelegate):
    """ Item delegate used for the main header view

    This will show different delegates for the name change, and the AOV type change."""
    def __init__(self, parent=None):
        super(AOVManagerItemDelegate, self).__init__(parent)
        self.setDelegateWidget(ListInputWidget)
        self._parent = parent

    def setModelData(self, editor, model, index):
        # illegal value
        if index.column() == 1:
            new_value = editor.text()
            if new_value not in aovTypes():
                editor.setText(self._aov_type)
                return
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

        return AbstractDragDropModelDelegate.createEditor(self, parent, option, index)


class AbstractParametersWidget(QWidget):
    def __init__(self, parent=None):
        super(AbstractParametersWidget, self).__init__(parent)
        QVBoxLayout(self)
        self.layout().addWidget(QLabel(self.__name__()))

    def __name__(self):
        return "abstract"

    def item(self):
        return self._item

    def setItem(self, item):
        self._item = item


class CustomParametersWidget(AbstractParametersWidget):
    def __init__(self, parent=None):
        super(CustomParametersWidget, self).__init__(parent)

    def __name__(self):
        return CUSTOM


class AOVGroupParametersWidget(AbstractParametersWidget):
    def __init__(self, parent=None):
        super(AOVGroupParametersWidget, self).__init__(parent)

    def __name__(self):
        return AOVGROUP


class LightParametersWidget(AbstractParametersWidget):
    def __init__(self, parent=None):
        super(LightParametersWidget, self).__init__(parent)

    def __name__(self):
        return LIGHT


class LPEParametersWidget(AbstractParametersWidget):
    def __init__(self, parent=None):
        super(LPEParametersWidget, self).__init__(parent)

    def __name__(self):
        return LPE


class PredefinedParametersWidget(AbstractParametersWidget):
    def __init__(self, parent=None):
        super(PredefinedParametersWidget, self).__init__(parent)

    def __name__(self):
        return PREDEFINED


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication
    from cgwidgets.utils import centerWidgetOnScreen

    app = QApplication(sys.argv)
    widget = AbstractAOVManagerEditor()
    widget.show()
    centerWidgetOnScreen(widget)
    sys.exit(app.exec_())