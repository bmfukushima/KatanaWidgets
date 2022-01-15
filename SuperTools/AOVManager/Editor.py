"""
Todo:
    *   Item Parameter displays
            Need to create this for the different item types, and connect the signals
    *   Item type storage Group vs AOV
    *   Item set name/disable/delete (AOVManagerWidget)
            aov delete event
            aov enabled/disabled
            aov name changed event
    *   Store hierarchical data
            export model to json?
            - Populate model
            - Drag/Drop

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


"""

from qtpy.QtWidgets import QVBoxLayout, QLabel, QWidget
from qtpy.QtCore import Qt

from cgwidgets.widgets import (
    ShojiModelViewWidget,
    ButtonInputWidget,
    ListInputWidget,
    LabelledInputWidget,
    ModelViewWidget
)
from cgwidgets.settings import attrs
from cgwidgets.utils import getFontSize

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


class AOVManagerWidget(ShojiModelViewWidget):
    """ Main display for showing the user the current AOV's available to them."""
    AOV = 0
    GROUP = 1
    def __init__(self, parent=None):
        super(AOVManagerWidget, self).__init__(parent)
        self.setHeaderViewType(ModelViewWidget.TREE_VIEW)
        self.setHeaderPosition(attrs.WEST, attrs.SOUTH)
        self.setDelegateTitleIsShown(True)

        # create new item button
        self._createNewItemWidget = ButtonInputWidget(
            title="Create New Item", user_clicked_event=self.createNewItem)
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
        self.setHeaderItemDeleteEvent(self.aovDeleteEvent)

    """ EVENTS """
    def aovNameChangedEvent(self, item, old_value, new_value):
        # todo aov name changed event
        pass

    def aovEnabledEvent(self, item, enabled):
        # todo aov enabled/disabled
        pass

    def aovDeleteEvent(self, item):
        # todo aov delete event
        pass

    def createNewItem(self, widget):
        self.createNewAOV()

    def createNewAOV(self):
        aov_name = "NEW AOV"
        column_data = {"name": aov_name, "type": ""}
        widget = QLabel("new aov")
        new_index = self.insertShojiWidget(
            self.rootItem().childCount(),
            column_data=column_data,
            widget=widget,
            is_draggable=True)


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
            self.currentItem().setIsDroppable(True)

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