"""
TODO:
    * Handler for user popup bar widgets
        - gsvutils --> getAllGSVViewWidgets, getAllGSVEventsWidgets

TODO CLEANUP:
    *   GSV Updates (GSVEventWidget)
            Move to model
    *   GSV Event Update (cleanup)
            Needs to move to a wrapper GSVEvent --> Events
            deleteOptionEvent, optionChangedEvent, optionChangedEvent, _setMode, setFilepath, setScript
"""

"""
The GSVManagerTab is a TAB that has three separate portions. View, Create/Edit, Events.

View:
    The area that the user can use as a read only aspect to display/change
    the GSV.
Edit:
    The area where the user can:
        1.) create/edit/destroy GSVs/Options
        2.) Reorder GSV's/options
        3.) Enable/Disable
Events:
    The area where the user can setup Python scripts to be run when GSV's are changed
    and the conditions are met.  This works the same way that VariableSwitches/VEG work
    in that when the GSV/Pattern condition is met, then the script will run.

    These scripts will receive two LOCAL VARIABLES in their scope, "gsv" and "option"
    which are both STRINGS that provide the GSV that was changed, and the option it
    was changed to.

    Note:
        Events have their filepath, and the script stored.  The filepath is cached into a
        string, and then the string is executed if a match is made.  There are certain
        procedures in place to auto update the filepath and recache it, if it has changed
        on disk.

Hierarchy:
    GSVManagerTab(UI4.Tabs.BaseTab)
        |- QVBoxLayout
            |- mainWidget --> (ShojiModelViewWidget)
                |- viewWidget --> (GSVViewWidget --> QWidget)
                |    |* ViewGSVWidget --> (LabelledInputWidget)
                |- editWidget --> (GSVEditWidget --> QWidget)
                |   |> VBoxLayout:
                |       |> HBoxLayout
                |       |   |- GSVSelectorWidget --> (LabelledInputWidget --> ListInputWidget)
                |       |   |- CreateNewGSVOptionWidget --> (LabelledInputWidget --> StringInputWidget)
                |       |- displayEditableOptionsWidget --> (ModelViewWidget)
                |- eventsWidget (GSVEventWidget --> ShojiMVW)
                    |- DisplayGSVEventWidget (FrameInputWidgetContainer)
                        |- DisplayGSVEventWidgetHeader (OverlayInputWidget --> ButtonInputWidget)
                        |* GSVEvent
                            |- optionsWidget --> ListInputWidget
                            |- scriptWidget --> StringInputWidget
                            |- buttonsMainWidget --> (QWidget)
                                |> QHBoxLayout
                                    |- disableScriptButton (BooleanInputWidget)
                                    |- deleteButton (ButtonInputWidget)

Data:
    Stored as a parameter on the root node.  Under KatanaBebop.GSVEventsData.data
    eventsWidget() --> eventsData()
        {gsv_name1: {
            data: {
                "option1":{filepath:"path_to_script.py", script: "script text", enabled: boolean},
                "option2":{filepath:"path_to_script.py", script: "script text", enabled: boolean}}
            enabled: boolean}
        {gsv_name2: {
            data: {
                "option1":{filepath:"path_to_script.py", script: "script text", enabled: boolean},
                "option2":{filepath:"path_to_script.py", script: "script text", enabled: boolean}}
            enabled: boolean}
        }

GSVEventWidget --> gsvChangedEvent
"""

import os
import json

from qtpy.QtWidgets import (
    QHBoxLayout,
    QScrollArea,
    QSizePolicy,
    QWidget,
    QVBoxLayout)
from qtpy.QtCore import Qt

from Katana import UI4, NodegraphAPI, Utils

from cgwidgets.widgets import (
    AbstractModelViewItem,
    BooleanInputWidget,
    ButtonInputWidget,
    FrameInputWidgetContainer,
    ListInputWidget,
    LabelledInputWidget,
    ModelViewWidget,
    OverlayInputWidget,
    ShojiModelViewWidget,
    StringInputWidget)
from cgwidgets.utils import getWidgetAncestor, clearLayout
from cgwidgets.settings import attrs, iColor

from Widgets2 import (
    AbstractEventListViewItemDelegate,
    AbstractEventListView,
    AbstractEventWidget,
    AbstractScriptInputWidget,
    PythonWidget
)
from Utils2 import gsvutils, getFontSize, paramutils, widgetutils


class GSVManagerTab(UI4.Tabs.BaseTab):
    """Main convenience widget for displaying GSV manipulators to the user."""
    NAME = "State Managers/GSV Manager"

    def __init__(self, parent=None):
        super(GSVManagerTab, self).__init__(parent)

        # create widgets
        self._main_widget = ShojiModelViewWidget(parent=self)

        self._view_widget = GSVViewWidget(parent=self)
        self._view_scroll_area = QScrollArea(self)
        self._view_scroll_area.setWidget(self._view_widget)
        self._view_scroll_area.setWidgetResizable(True)

        self._edit_widget = GSVEditWidget(parent=self)
        self._events_widget = GSVEventWidget(parent=self)

        # insert widgets
        self._main_widget.insertShojiWidget(0, column_data={"name":"View"}, widget=self._view_scroll_area)
        self._main_widget.insertShojiWidget(1, column_data={"name":"Edit"}, widget=self.editWidget())
        self._main_widget.insertShojiWidget(2, column_data={"name":"Events"}, widget=self.eventsWidget())

        # setup layout
        QVBoxLayout(self)
        self.layout().addWidget(self._main_widget)
        # self.mainWidget().setHeaderItemIsSelectable(False)
        self.mainWidget().setHeaderItemIsDraggable(False)
        self.mainWidget().setHeaderItemIsEditable(False)
        self.mainWidget().setHeaderItemIsDeletable(False)
        self.mainWidget().setHeaderItemIsEnableable(False)
        self.mainWidget().setHeaderItemIsDroppable(False)

        # setup Katana events
        Utils.EventModule.RegisterCollapsedHandler(self.nodegraphLoad, 'nodegraph_loadEnd', None)

    def __name__(self):
        return GSVManagerTab.NAME

    def rename(self, args):
        pass

    """ WIDGETS """
    def mainWidget(self):
        return self._main_widget

    def editWidget(self):
        return self._edit_widget

    def eventsWidget(self):
        return self._events_widget

    def viewWidget(self):
        return self._view_widget

    """ KATANA EVENTS """
    def nodegraphLoad(self, args):
        """ Reload the View Widget when a new Katana scene is opened"""
        # preflight
        if not self.eventsWidget().paramData(): return
        # reload events data
        events_data = json.loads(self.eventsWidget().paramData().getValue(0))
        self.eventsWidget().setEventsData(events_data)
        self.eventsWidget().setNode(NodegraphAPI.GetRootNode())
        # update variable text
        self.editWidget().setText("<variables>")
        # update all widgets
        self.viewWidget().update()
        self.editWidget().update()
        self.eventsWidget().update()

    def update(self, *args):
        self.eventsWidget().update()
        self.editWidget().update()
        self.viewWidget().update()


""" VIEW WIDGET """
class GSVViewWidget(FrameInputWidgetContainer):
    """
    Main wigdet for viewing GSV's.

    Attributes:
        widgets (dict): key pair values to map the GSV name to the LabelledInputWidget
    """
    def __init__(self, parent=None):
        super(GSVViewWidget, self).__init__(parent)

        self.setIsHeaderShown(False)
        self.setDirection(Qt.Vertical)
        self._widget_list = {}
        self.populate()

    """ POPULATE """
    def clear(self):
        """
        Removes all of the GSVViewWidgets from the display
        """
        self.clearInputWidgets()
        self._widget_list = {}

    def populate(self):
        """Creates the display for every GSV.  This is the left side of the display."""
        # create a combobox for each GSV that is available
        gsv_keys = gsvutils.getAllGSV(return_as=gsvutils.STRING)
        for gsv in gsv_keys:
            self.addWidget(gsv)

    def update(self, *args):
        """Updates the current view widgets displayed to the user"""
        self.clear()
        self.populate()

    """ PROPERTIES """
    def addWidget(self, gsv):
        """
        Adds a widget to the layout.

        Args:
            gsv (str): name of GSV to create
        """
        widget = ViewGSVWidget(self, name=gsv)
        widget.delegateWidget().setText(gsvutils.getGSVValue(gsv))
        self.addInputWidget(widget)
        self.widgets()[gsv] = widget

    def removeWidget(self, gsv):
        # remove widget
        self.widgets()[gsv].setParent(None)
        self.widgets()[gsv].deleteLater()

        # remove key
        del self.widgets()[gsv]

    def renameWidget(self, gsv, new_name):
        """
        Renames the GSV widget to the new name provided

        Args:
            gsv (str): name of widget to change
            new_name (str): value to change to
        """
        # cast to strings
        gsv = str(gsv)
        new_name = str(new_name)

        # get widget
        widget = self.widgets()[gsv]

        # update widget
        widget.viewWidget().setTitle(new_name)
        widget.gsv = new_name

        # update widgets dict
        self.widgets()[new_name] = widget
        del self.widgets()[gsv]

    def widgets(self):
        return self._widget_list

    def updateGSVOptionDisplayText(self, gsv, option):
        """ Updates the display text of a single GSV Option"""
        self.widgets()[gsv].setIsFrozen(True)
        self.widgets()[gsv].updateGSVOptionDisplayText(option)
        self.widgets()[gsv].setIsFrozen(False)


class ViewGSVWidget(LabelledInputWidget):
    """
    One singular GSV view that is displayed in the GSVViewWidget.

    This will consist of one label showing which GSV it is, and one
    ListInputWidget that will have all of the GSV's
    """
    def __init__(
        self,
        parent=None,
        name="None",
        direction=Qt.Horizontal,
        default_label_length=100
    ):
        delegate_widget = ListInputWidget()
        super(ViewGSVWidget, self).__init__(
            parent,
            name=name,
            default_label_length=default_label_length,
            direction=direction,
            delegate_widget=delegate_widget
        )
        # setup label
        self.viewWidget().setDisplayMode(OverlayInputWidget.DISABLED)
        self._is_frozen = False

        # setup delegate
        self.delegateWidget().dynamic_update = True
        self.delegateWidget().setUserFinishedEditingEvent(self.setGSVOption)
        self.delegateWidget().populate(self.update())
        self.delegateWidget().setCleanItemsFunction(self.update)
        self.delegateWidget().setValidateInputFunction(self.validateGSVEntry)
        self.setFixedHeight(getFontSize()*3)

    def isFrozen(self):
        return self._is_frozen

    def setIsFrozen(self, enabled):
        self._is_frozen = self._is_frozen

    def update(self):
        return [[option] for option in gsvutils.getGSVOptions(self.gsv(), return_as=gsvutils.STRING)]

    def validateGSVEntry(self):
        """
        Determines if the GSV option entered by the user is valid.

        If it is not valid, it will reset this widget back to its original value
        """
        option = self.delegateWidget().text()
        if option in gsvutils.getGSVOptions(self.gsv(), return_as=gsvutils.STRING):
            return True
        elif option == "":
            return True
        else:
            return False

    def updateGSVOptionDisplayText(self, option):
        """ Updates the display text of a single GSV Option"""
        self.setIsFrozen(True)
        self.delegateWidget().setText(option)
        self.setIsFrozen(False)

    def setGSVOption(self, widget, option):
        """Sets the GSV Option parameter to the specified value"""
        if not self.isFrozen():
            gsvutils.setGSVOption(self.gsv(), option)

    def gsv(self):
        return self.name()

    def setGSV(self, gsv):
        self.setName(gsv)


""" EDIT WIDGET """
class GSVEditWidget(QWidget):
    """
    Widget to hold the view where the users can edit GSVs

    Hierarchy:
        VBoxLayout:
            |>HBoxLayout
            |   |- GSVSelectorWidget --> (LabelledInputWidget --> ListInputWidget)
            |   |- CreateNewGSVOptionWidget --> (LabelledInputWidget --> StringInputWidget)
            |- displayEditableOptionsWidget --> (ModelViewWidget)
    """
    def __init__(self, parent=None):
        super(GSVEditWidget, self).__init__(parent)

        # Set attrs
        self._display_mode = gsvutils.VARIABLES

        # Create Widgets
        self._gsv_selector_widget = GSVSelectorWidget(
            parent=self, default_label_length=getFontSize()*3)
        self._create_new_gsv_option_widget = CreateNewGSVOptionWidget(
            parent=self, default_label_length=getFontSize()*3)
        self._display_editable_options_widget = DisplayEditableOptionsWidget(parent=self)

        # setup default sizes
        font_size = getFontSize()
        #self._create_new_gsv_option_widget.setFixedHeight(font_size * 7)
        #self._gsv_selector_widget.setFixedHeight(font_size * 7)
        self._create_new_gsv_option_widget.resize(self._create_new_gsv_option_widget.width(), getFontSize() * 7)
        self._gsv_selector_widget.resize(self._gsv_selector_widget.width(), getFontSize() * 7)
        self._create_new_gsv_option_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._gsv_selector_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Setup Top Row
        self._user_settings_layout = QHBoxLayout()
        self._user_settings_layout.addWidget(self._gsv_selector_widget)
        self._user_settings_layout.addWidget(self._create_new_gsv_option_widget)

        #
        QVBoxLayout(self)
        self.layout().addLayout(self._user_settings_layout)
        self.layout().addWidget(self._display_editable_options_widget)

        # populate
        # self.populate()

    """ UTILS """
    def text(self):
        return str(self.gsvSelectorWidget().delegateWidget().text())

    def setText(self, text):
        self.gsvSelectorWidget().delegateWidget().setText(text)

    """ PROPERTIES """
    def displayMode(self):
        return self._display_mode

    def setDisplayMode(self, _display_mode):
        self._display_mode = _display_mode

        # toggle enable of the list view
        if _display_mode == gsvutils.VARIABLES:
            self.displayEditableOptionsWidget().setIsEnableable(True)
        if _display_mode == gsvutils.OPTIONS:
            self.displayEditableOptionsWidget().setIsEnableable(False)

    """ WIDGETS """
    def createNewGSVOptionWidget(self):
        return self._create_new_gsv_option_widget

    def gsvSelectorWidget(self):
        return self._gsv_selector_widget

    def displayEditableOptionsWidget(self):
        return self._display_editable_options_widget

    def update(self):
        # update list widget
        self.displayEditableOptionsWidget().update()

        # check to see if current gsv exists
        if self.text() not in gsvutils.getAllGSV(return_as=gsvutils.STRING):
            self.setText("<variables>")


class GSVSelectorWidget(LabelledInputWidget):
    """This will display the currently active GSV to the user

    Changing this drop down will change the edit widgets display of the currently available
    options based off of the GSV selected.

    Setting this to <variables> is a special case, that will allow the user to manipulate
    the GSV's instead of their individual options.
    """

    def __init__(self, parent=None, default_label_length=30):
        super(GSVSelectorWidget, self).__init__(parent, default_label_length=default_label_length, direction=Qt.Vertical)

        # setup attrs
        self.setName("GSV")
        self.viewWidget().setDisplayMode(OverlayInputWidget.DISABLED)
        self.setDirection(Qt.Vertical)

        # setup delegate widget
        delegate_widget = ListInputWidget(self)
        self.setDelegateWidget(delegate_widget)

        # setup delegate widget attrs
        self.delegateWidget().dynamic_update = True
        self.delegateWidget().filter_results = False
        self.delegateWidget().setText("<variables>")

        # setup events
        self.delegateWidget().setUserFinishedEditingEvent(self.changedGSV)
        self.delegateWidget().populate(self.getAllGSVNames())
        self.delegateWidget().setCleanItemsFunction(self.getAllGSVNames)

    def getAllGSVNames(self):
        """
        Returns a list of lists of all of the GSV names
        Returns (list): of lists
            [['var1'], ['var2'], ['var3']]

        """
        variables = ['<variables>'] + gsvutils.getAllGSV(return_as=gsvutils.STRING)
        gsv_keys = [[variable] for variable in variables]
        return gsv_keys

    def setOptionsDisplayMode(self):
        """When the GSV is changed, this will show the OPTIONS available in the displayEditableOptionsWidget

        Args:
            gsv (str): name of GSV
        """

        main_widget = getWidgetAncestor(self, GSVManagerTab)

        if main_widget:
            gsv = str(self.delegateWidget().text())
            edit_widget = main_widget.editWidget()
            edit_widget.setDisplayMode(gsvutils.OPTIONS)
            gsv_list = gsvutils.getAllGSV(return_as=gsvutils.STRING)
            # create new GSV if it doesn't exist
            if gsv not in gsv_list:
                # create new GSV in katana
                param = gsvutils.createNewGSV(gsv)

                # handle invalid user input
                if param.getName() != gsv:
                    self.delegateWidget().setText(param.getName())

            # Update options available to the user
            if hasattr(main_widget, '_edit_widget'):
                edit_widget.displayEditableOptionsWidget().update()

    def setVariablesDisplayMode(self):
        """When the GSV is changed, this will show the VARIABLES available in the displayEditableOptionsWidget

        Args:
            gsv (str): name of GSV
        """
        edit_widget = getWidgetAncestor(self, GSVEditWidget)
        if hasattr(edit_widget, '_display_editable_options_widget'):
            # edit_widget = getWidgetAncestor(self, GSVEditWidget)
            edit_widget.setDisplayMode(gsvutils.VARIABLES)
            # update edit widget
            edit_widget.displayEditableOptionsWidget().update()

    def changedGSV(self, widget, value):
        """ Combo box that will update what is displayed in the list widget
        if it is set to <variables> it will show all the GSVs, if it is something
        else, then it will show the options of that variable"""
        # preflight
        if str(self.delegateWidget().text()) == "": return

        # set modes
        if str(self.delegateWidget().text()) == '<variables>':
            self.setVariablesDisplayMode()
        else:
            self.setOptionsDisplayMode()


class CreateNewGSVOptionWidget(LabelledInputWidget):
    """Line Edit widget that creates new GSV options when enter is pressed"""
    def __init__(self, parent=None, default_label_length=30):
        super(CreateNewGSVOptionWidget, self).__init__(parent, default_label_length=default_label_length, direction=Qt.Vertical)
        # setup attrs
        self.setName("Create Option")
        self.setToolTip(""" Type value in and press ENTER to create a new Option/GSV""")
        self.setDirection(Qt.Vertical)
        self.viewWidget().setDisplayMode(OverlayInputWidget.DISABLED)

        # setup delegate widget
        delegate_widget = StringInputWidget(self)
        self.setDelegateWidget(delegate_widget)
        self.delegateWidget().setUserFinishedEditingEvent(self.createNewItem)

    def createNewItem(self, widget, value):
        """
        Creates a new entry as a GSV or Option of a GSV.

        Which one it sets depends on what is selected in the GSVSelectorWidget

        Args:
            widget (QWidget): sending signal
            value (str): value being set
        """
        main_widget = getWidgetAncestor(self, GSVManagerTab)

        edit_widget = main_widget.editWidget()
        current_gsv_text = str(edit_widget.text())

        # Pre flight
        if value == "": return
        if current_gsv_text == "": return

        # Create new GSV Option
        if current_gsv_text != '<variables>':
            option = str(value)
            if option not in gsvutils.getGSVOptions(current_gsv_text, return_as=gsvutils.STRING):
                if current_gsv_text in gsvutils.getAllGSV(return_as=gsvutils.STRING):
                    param = gsvutils.createNewGSVOption(current_gsv_text, option)
                    new_entry_text = option
            else:
                print("{OPTION} already exists for {GSV}".format(OPTION=option, GSV=current_gsv_text))
                self.delegateWidget().setText('')
                return

        # Create new GSV
        elif current_gsv_text == '<variables>':
            gsv = str(value)
            gsv_list = gsvutils.getAllGSV(return_as=gsvutils.STRING)
            # create new GSV if it doesn't exist
            if gsv not in gsv_list:
                # create new GSV in katana
                param = gsvutils.createNewGSV(gsv)

                # todo why is this necessary
                # create new entry in the view widget
                # main_widget.viewWidget().addWidget(gsv)

                # get new entry text
                new_entry_text = gsv

            # return if GSV exists
            else:
                print("{gsv} already exists you dingus".format(gsv=gsv))
                self.delegateWidget().setText('')
                return

        # create new list entry
        model = main_widget.editWidget().displayEditableOptionsWidget().model()
        root_item = model.rootItem()
        num_children = len(root_item.children())
        main_widget.editWidget().displayEditableOptionsWidget().createNewItem(new_entry_text, param, index=num_children)

        # reset text
        self.delegateWidget().setText('')


class DisplayEditableOptionsItem(AbstractModelViewItem):
    def __init__(self, parent=None, parameter=None):
        super(DisplayEditableOptionsItem, self).__init__(parent)
        self.setParameter(parameter)

    def parameter(self):
        return self._parameter

    def setParameter(self, parameter):
        self._parameter = parameter


class DisplayEditableOptionsWidget(ModelViewWidget):
    def __init__(self, parent=None):
        super(DisplayEditableOptionsWidget, self).__init__(parent)
        self.model().setItemType(DisplayEditableOptionsItem)

        # setup events
        self.setItemDeleteEvent(self.deleteSelection)
        self.setTextChangedEvent(self.renameSelectedItem)
        self.setDropEvent(self.moveSelectedItems)
        self.setItemEnabledEvent(self.enableItem)

        # setup attrs
        self.setMultiSelect(True)

        # populate
        self.populate()

    def createNewItem(self, name, parameter, index=0):
        index = self.model().insertNewIndex(index, name=str(name))
        item = index.internalPointer()
        item.setParameter(parameter)

        return item

    def populate(self):
        """
        Creates all of the corresponding items provided

        Args:
            gsv_list (list): of parameters to be populated
        """
        #

        edit_widget = getWidgetAncestor(self, GSVEditWidget)

        # populate editable options
        if edit_widget:
            # populate ALL options, if no gsv_list provided,
            if edit_widget.displayMode() == gsvutils.OPTIONS:
                self.populateOptions()
            # populate GSV names
            elif edit_widget.displayMode() == gsvutils.VARIABLES:
                self.populateGSV()

    def populateGSV(self):
        """
        Creates the items for all of the GSV available in the scene
        """
        gsv_list = gsvutils.getAllGSV(return_as=gsvutils.PARAMETER)

        # create entries
        for gsv_param in reversed(gsv_list):
            gsv_name = gsv_param.getName()
            if gsv_name.rstrip() != '':
                item = self.createNewItem(gsv_name, gsv_param)

                # set disabled display flag
                if not gsv_param.getChild("enable").getValue(0):
                    self.model().setItemEnabled(item, False)
                    self.model().layoutChanged.emit()

    def populateOptions(self):
        """
        Creates the items for all of the options available in the current GSV
        """
        # get edit widget
        edit_widget = getWidgetAncestor(self, GSVEditWidget)

        # get all GSVs
        gsv_keys = gsvutils.getAllGSV(return_as=gsvutils.STRING)
        gsv = edit_widget.text()
        # if GSV is valid, populate all options
        if gsv in gsv_keys:
            options_list = gsvutils.getGSVOptions(gsv, return_as=gsvutils.PARAMETER)
            for option_param in reversed(options_list):
                option_name = option_param.getValue(0)
                if option_name.rstrip() != '':
                    self.createNewItem(option_name, option_param)

    def update(self):
        """
        Updates the current display based on the list provided.

        If no list is provided, then by default this will populate the options for the current GSV

        Args:
            gsv_list (list): of parameters to be populated

        Returns:

        """
        self.clearModel()
        self.populate()

    """ EVENTS """
    def enableItem(self, item, enabled):
        main_widget = getWidgetAncestor(self, GSVManagerTab)
        view_widget = main_widget.viewWidget()
        edit_widget = main_widget.editWidget()

        if edit_widget.displayMode() == gsvutils.VARIABLES:
            gsv = item.columnData()['name']
            widget = view_widget.widgets()[gsv]
            param = gsvutils.getGSVParameter(gsv)
            if enabled:
                param.getChild("enable").setValue(1.0, 0)
                widget.show()
            elif not enabled:
                param.getChild("enable").setValue(0.0, 0)
                widget.hide()

    def moveSelectedItems(self, data, items, model, row, parent):
        """
        Changes the GSV/Option name to the values provided

        Args:
            items (list): of DisplayEditableOptionsItem currently being dropped
            row (int): row being dropped on


        Note:
            When the user Drag/Drops items in the display

        """
        edit_widget = getWidgetAncestor(self, GSVEditWidget)

        for item in items:
            # Rename Option
            if edit_widget.displayMode() == gsvutils.OPTIONS:
                gsv = edit_widget.text()
                option = item.columnData()['name']
                gsvutils.moveGSVOptionToNewIndex(gsv, option, row)

            # Rename GSV
            if edit_widget.displayMode() == gsvutils.VARIABLES:
                gsv = item.columnData()['name']
                gsvutils.moveGSVtoNewIndex(gsv, row)

                # update view
                main_widget = getWidgetAncestor(self, GSVManagerTab)
                view_widget = main_widget.viewWidget()
                view_widget.update()

    def deleteSelection(self, item):
        """ Deletes the specified item, and removes the relevant data.

        Args:
            item (DisplayEditableOptionsItem): currently selected
        """
        main_widget = getWidgetAncestor(self, GSVManagerTab)
        edit_widget = main_widget.editWidget()
        events_widget = main_widget.eventsWidget()

        # Remove Option
        if edit_widget.displayMode() == gsvutils.OPTIONS:
            # get attrs
            gsv = edit_widget.text()
            option = item.columnData()['name']

            # remove param
            gsvutils.deleteGSVOption(gsv, option)

            # remove event
            if gsv in list(events_widget.eventsData().keys()):
                # check to see if GSV is selected
                selected_indexes = events_widget.getAllSelectedIndexes()
                for index in selected_indexes:
                    if index.internalPointer().columnData()['name'] == gsv:
                        # check to make sure option exists
                        if option in list(events_widget.eventsData()[gsv]["data"].keys()):
                            # get delegate widget
                            main_delegate_widget = events_widget.delegateWidget().widget(1).getMainWidget()

                            # delete widget
                            main_delegate_widget.widgets()[option].deleteLater()
                            main_delegate_widget.widgets()[option].setParent(None)
                            del main_delegate_widget.widgets()[option]

                            # destroy event data
                            del events_widget.eventsData()[gsv]["data"][option]
                            events_widget.saveEventsData()

        # Remove Variable
        if edit_widget.displayMode() == gsvutils.VARIABLES:
            # get attrs
            main_widget = getWidgetAncestor(self, GSVManagerTab)
            # view_widget = main_widget.viewWidget()
            gsv = item.columnData()['name']

            # remove param
            gsvutils.deleteGSV(gsv)

            # remove event
            # todo update model on delete
            if gsv in list(events_widget.eventsData().keys()):
                # remove item
                for item in events_widget.eventsWidget().model().findItems(gsv):
                    events_widget.eventsWidget().model().deleteItem(item.internalPointer(), event_update=True)

    def renameSelectedItem(self, item, old_value, new_value, column=None):
        """
        Changes the GSV/Option name to the values provided

        Args:
            item (DisplayEditableOptionsItem): current item selected
            old_value (str): current value of item
            new_value (str): new value that is being set

        Note:
            When the user Double Clicks to enter the item's text field.

        """
        edit_widget = getWidgetAncestor(self, GSVEditWidget)

        # Rename Option
        if edit_widget.displayMode() == gsvutils.OPTIONS:
            # get attrs
            gsv = edit_widget.text()
            gsvutils.renameGSVOption(gsv, old_value, new_value)

        # Rename GSV
        if edit_widget.displayMode() == gsvutils.VARIABLES:
            # rename
            gsvutils.renameGSV(old_value, new_value)


""" EVENTS WIDGET (INHERIT)"""
class GSVEventWidget(AbstractEventWidget):
    """
    The main widget for setting up the events triggers on the node.

    Args:
        node (Node): Node to store events data on
        param (str): Location of param to create events data at

    Attributes:
        events_model (list): of EventTypeModelItem's.  This list is the model
            for all of the events.

            All of the tab labels/widgets will automatically call back to this list for
            updating.

    Hierarchy:
        | -- VBox
            | -- events_widget --> (ShojiModelViewWidget)
                | -- label type (EventsLabelWidget --> ShojiLabelWidget)
                | -- Dynamic Widget (EventDelegateWidget --> QWidget)
                    | -- VBox
                        | -- events_type_menu ( EventTypeInputWidget)
                        | -- script_widget (DynamicArgsInputWidget)
                        | -- dynamic_args_widget (DynamicArgsWidget)
                                | -* DynamicArgsInputWidget
    """

    def __init__(self, parent=None, param=gsvutils.EVENT_PARAM_LOCATION):
        super(GSVEventWidget, self).__init__(
            delegate_widget_type=DisplayGSVEventWidget,
            events_list_view=GSVEventsListView,
            parent=parent,
            param=param
        )

        # setup default attrs
        self._is_frozen = False
        self.eventsWidget().setHeaderPosition(attrs.WEST, attrs.SOUTH)

        paramutils.createParamAtLocation(
            gsvutils.EVENT_PARAM_LOCATION + ".old_values", NodegraphAPI.GetRootNode(), paramutils.STRING, initial_value="{}")

        # self.eventsWidget().setHeaderItemIsEditable(False)
        self.eventsWidget().setHeaderItemIsDraggable(False)

        self._events_data = {}

        # set style
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # todo move GSVManager to global model
        """ For some reason this keeps populating the same widget...
        It appears that somehow the "parent" in updateGUI is retrieving
        the same parent..."""
        # # setup custom model
        # """ This is needed to ensure all tabs remain synchronized"""
        # if not hasattr(widgetutils.katanaMainWindow(), "_gsv_events_widget"):
        #     widgetutils.katanaMainWindow()._gsv_events_widget = self.eventsWidget().model()
        #
        #     # populate
        #     self._events_data = json.loads(self.paramData().getValue(0))
        #     gsv_list = list(self.eventsData().keys())
        #     for gsv in gsv_list:
        #         self.eventsWidget().insertShojiWidget(0, column_data={"name": str(gsv)})
        #
        # else:
        #     self.eventsWidget().setModel(widgetutils.katanaMainWindow()._gsv_events_widget)

        # populate
        self._events_data = json.loads(self.paramData().getValue(0))
        gsv_list = list(self.eventsData().keys())
        for gsv in gsv_list:
            self.eventsWidget().insertShojiWidget(0, column_data={"name": str(gsv)})

        # setup signals
        self.eventsWidget().setHeaderItemDeleteEvent(self.deleteGSVEvent)
        self.eventsWidget().setHeaderItemEnabledEvent(self.disableGSVEvent)
        self.eventsWidget().setHeaderItemTextChangedEvent(self.gsvChangedEvent)

        # self.eventsWidget().setDelegateType(
        #     ShojiModelViewWidget.DYNAMIC,
        #     dynamic_widget=DisplayGSVEventWidget,
        #     dynamic_function=DisplayGSVEventWidget.updateGUI
        # )
        # self.eventsWidget().model()

    """ WIDGETS """
    def displayWidget(self):
        # todo this doesnt work...
        self.eventsWidget().delegateWidget().widget(1).getMainWidget()

    """ PROPERTIES """
    def currentGSV(self):
        return self._current_gsv

    def setCurrentGSV(self, gsv):
        self._current_gsv = gsv

    def isFrozen(self):
        return self._is_frozen

    def setIsFrozen(self, is_frozen):
        self._is_frozen = is_frozen

    """ EVENTS """
    def cacheScriptToParam(self, script):
        """ This will cache the script to a local value

        Note: The script must be a valid file in order for it to cache
        """
        scripts_param = self.paramScripts().getChild(self.pythonWidget().filepath())
        if scripts_param:
            # update script
            scripts_param.setValue(str(script), 0)

            # save
            self.saveEventsData()
            return

        print("{name} is invalid.  Enter a valid name to save".format(name=self.pythonWidget().filepath()))

    def deleteGSVEvent(self, item):
        """When the user deletes a GSV event, this will remove the meta data."""

        gsv = item.columnData()['name']
        if gsv not in list(self.eventsData().keys()): return
        # delete data
        del self.eventsData()[gsv]
        self.saveEventsData()

    def disableGSVEvent(self, item, enabled):
        """
        When the user deletes a GSV event, this will remove the meta data.
        """
        # get attrs
        gsv = item.columnData()['name']

        # preflight
        if gsv not in list(self.eventsData().keys()): return

        # disable data
        self.eventsData()[gsv]["enabled"] = enabled
        self.saveEventsData()

    def gsvChangedEvent(self, item, old_value, new_value, column=None):
        """ When the user changes the GSV"""

        """ Create a new event item"""
        # get attrs
        gsv = new_value

        # preflight
        if gsv == "": return
        if gsv in list(self.eventsData(from_param=True).keys()):
            print("{gsv} already exists... update the one that already exists you Derpasaur".format(gsv=gsv))
            item.setArg("name", old_value)
            return
        if gsv not in gsvutils.getAllGSV(return_as=gsvutils.STRING):
            item.setArg("name", old_value)
            return

        # update attr
        item.setArg("name", gsv)

        # create new GSV event item
        self.eventsData()[gsv] = {}
        self.eventsData()[gsv]["data"] = {}
        self.eventsData()[gsv]["enabled"] = True
        if old_value in self.eventsData().keys():
            del self.eventsData()[old_value]

        # update data
        self.saveEventsData()
        self.setCurrentGSV(gsv)
        self.eventsWidget().updateDelegateDisplay()
        gsvutils.updateAllGSVEventsTabs(ignore_widgets=[self])

    def update(self):
        """ Clears the model and repopulates it """
        self.setNode(NodegraphAPI.GetRootNode())

        # clear model
        self.eventsWidget().clearModel()

        # get data
        if NodegraphAPI.GetRootNode().getParameter(gsvutils.EVENT_PARAM_LOCATION):
            event_data = json.loads(NodegraphAPI.GetRootNode().getParameter(gsvutils.EVENT_PARAM_LOCATION+".data").getValue(0))

            # get GSVs
            for gsv in reversed(sorted(list(event_data.keys()))):
                self.eventsWidget().insertShojiWidget(0, column_data={"name": str(gsv)})

            self.setEventsData(event_data)


class GSVEventsListView(AbstractEventListView):
    def __init__(self, parent=None):
        delegate = GSVPopupSelector
        super(GSVEventsListView, self).__init__(parent, delegate)


class GSVPopupSelector(AbstractEventListViewItemDelegate):
    """ Creates the popup for the ShojiMVW item"""

    def __init__(self, parent=None):
        super(GSVPopupSelector, self).__init__(self._getEventsList, parent=parent)
        self._parent = parent

    def _getEventsList(self, parent):
        return gsvutils.getAllGSV(gsvutils.STRING)


""" EVENTS WIDGET """
class DisplayGSVEventWidget(FrameInputWidgetContainer):
    """Widget that is shown when the user clicks on a GSV item in the GSVEventWidget"""
    def __init__(self, parent=None):
        super(DisplayGSVEventWidget, self).__init__(parent)
        self.setDirection(Qt.Vertical)
        self._widgets = {}
        self._active_path = ""

        # setup header widget
        header_widget = DisplayGSVEventWidgetHeader(self)
        self.setHeaderWidget(header_widget)

    def activePath(self):
        return self._active_path

    def setActivePath(self, active_path):
        self._active_path = active_path

    def setGSV(self, gsv):
        """ When the dynamic update is run, this updates the title"""
        self.headerWidget().setTitle(gsv)

    def createNewOptionEvent(self, option=None, text=None, enabled=True):
        new_widget = GSVEvent(parent=self, option=option, text=text, enabled=enabled)
        self.addInputWidget(new_widget)
        return new_widget

    def widgets(self):
        return self._widgets

    @staticmethod
    def updateGUI(parent, widget, item):
        """ Updates the Dynamic display for the current GSV Event shown to the user"""
        # preflight
        if not item: return

        # get widgets
        events_widgets = gsvutils.getAllGSVEventsWidgets()
        for ew in events_widgets:
            ew.setIsFrozen(True)

        events_widget = getWidgetAncestor(parent, GSVEventWidget)
        display_widget = widget.getMainWidget()

        # get attrs
        gsv = item.columnData()['name']
        param_data = events_widget.paramData().getValue(0)

        if gsv not in json.loads(param_data).keys():
            events_widget.setCurrentGSV(None)
            display_widget.headerWidget().setDisplayMode(OverlayInputWidget.DISABLED)
            return

        # update GSV
        events_widget.setCurrentGSV(gsv)
        display_widget.setGSV(gsv)

        # remove old display
        display_widget.clearInputWidgets()

        # update display
        events_dict = json.loads(param_data)[gsv]["data"]
        display_widget.headerWidget().setDisplayMode(OverlayInputWidget.ENTER)

        for option, data in events_dict.items():
            # create widget
            widget = display_widget.createNewOptionEvent(
                option=str(option), text=str(data["filepath"]), enabled=data["enabled"])
            widget.setCurrentOption(str(option))
            display_widget.widgets()[option] = widget

            # check to see if script or filepath
            if data["is_script"]:
                text = data["script"]
                widget.setMode(PythonWidget.SCRIPT)
            elif not data["is_script"]:
                text = data["filepath"]
                widget.setMode(PythonWidget.FILE)

            widget.setText(text)
            # check to see if script is active
            """ for some reason events_widget.currentScript(),
            which literally calls events_widget.pythonWidget().filepath()
            doesnt work =/"""
            if str(text) == events_widget.pythonWidget().filepath():
                widget.updateScriptDisplayFlag()

        Utils.EventModule.ProcessAllEvents()
        for ew in events_widgets:
            ew.setIsFrozen(False)


class DisplayGSVEventWidgetHeader(OverlayInputWidget):
    """
    Header for the DisplayGSVEventWidget.  This will automatically turn into a
    button when the user hovers over it.  Clicking on the button will create a
    new event input for the user
    """
    def __init__(self, parent=None):
        super(DisplayGSVEventWidgetHeader, self).__init__(parent)

        # setup default attrs
        self._current_option = None

        # setup delegate
        delegate_widget = ButtonInputWidget(
            user_clicked_event=self.createNewEvent, title="Create New Event", flag=False, is_toggleable=False)
        self.setDelegateWidget(delegate_widget)

        # setup display mode
        self.setDisplayMode(OverlayInputWidget.ENTER)
        self.setFixedHeight(getFontSize() * 3)

    def createNewEvent(self, widget):
        """
        Creates a new event for the user

        """

        # add new input
        main_widget = getWidgetAncestor(self, DisplayGSVEventWidget)
        main_widget.createNewOptionEvent()


class GSVEvent(AbstractScriptInputWidget):
    """
    One input event for a specified GSV.

    Args:
        option (str):
        script (str):
    """
    def __init__(self, parent=None, option=None, text=None, enabled=True):
        super(GSVEvent, self).__init__(parent)
        self.setDirection(Qt.Horizontal)

        # setup default attrs
        self._current_option = option
        self._text = text
        self._is_editing_active = False
        self._is_enabled = True
        self._script = ""
        self._filepath = ""

        # setup buttons widget
        self._buttons_main_widget = QWidget()
        self._buttons_layout = QHBoxLayout(self._buttons_main_widget)
        self.mainWidget().insertWidget(2, self._buttons_main_widget)

        # setup view widget
        self._gsv_widget = ListInputWidget()
        self._gsv_widget.populate(self.populateGSVOptions())
        self._gsv_widget.dynamic_update = True
        self._gsv_widget.setCleanItemsFunction(self.populateGSVOptions)
        self._gsv_widget.setUserFinishedEditingEvent(self.optionChangedEvent)
        self._gsv_widget.setValidateInputFunction(self.validateOptionInputEvent)
        self.__insertButton(self._gsv_widget, "Set GSV", fixed_size=False)

        # add show script button
        self._show_script_button = ButtonInputWidget(
            title="py", user_clicked_event=self.showScript, is_toggleable=True, flag=False)
        self.__insertButton(self._show_script_button, "Click to edit this script")

        # add disable script button
        if enabled:
            self._disable_script_button = BooleanInputWidget(text="E", is_selected=True)
        if not enabled:
            self._disable_script_button = BooleanInputWidget(text="D", is_selected=False)
        self._disable_script_button.setUserFinishedEditingEvent(self.toggleScriptEnabled)
        self.__insertButton(self._disable_script_button, "Handicap")

        # add delete button
        self._delete_button = ButtonInputWidget(
            user_clicked_event=self.deleteOptionEvent, title="-", flag=False, is_toggleable=False)
        self.__insertButton(self._delete_button, "Delete")

        # set display attrs
        if option:
            self.gsvWidget().setText(option)
        if text:
            self.setText(text)

        # setup stretch/collapse
        self.mainWidget().setCollapsible(0, False)
        self.mainWidget().setCollapsible(2, False)
        self.mainWidget().setStretchFactor(2, 0)
        self.mainWidget().setStretchFactor(1, 100)
        self.mainWidget().setStretchFactor(0, 0)

        self._buttons_layout.setStretch(0, 100)
        self._buttons_layout.setStretch(1, 0)
        self._buttons_layout.setStretch(2, 0)
        self._buttons_layout.setStretch(3, 0)

        # set sizes
        self.setFixedHeight(getFontSize() * 3)
        self.setHandleWidth(1)
        self.setDefaultLabelLength(100)
        self._buttons_layout.setContentsMargins(0, 0, 0, 0)

    """ WIDGETS """
    def __insertButton(self, widget, tooltip, fixed_size=True):
        """
        Inserts a new clickable button for the user

        Args:
            index (int):
            name (str):
            tooltip (str):
            user_event (event):

        Returns:

        """
        # create button

        # add to main widget
        self._buttons_layout.addWidget(widget)

        # setup attrs todo: fix this later...
        if fixed_size:
            widget.setFixedSize(getFontSize() * 2.5, getFontSize() * 2.5)
        widget.setToolTip(tooltip)

        return widget

    def buttonsMainWidget(self):
        return self._buttons_main_widget

    def deleteButton(self):
        return self._delete_button

    def gsvWidget(self):
        return self._gsv_widget

    def scriptWidget(self):
        return self.delegateWidget()

    def showScriptWidget(self):
        return self._show_script_button

    def disableScriptButton(self):
        return self._disable_script_button

    """ EVENTS """
    # todo move this to a wrapper
    # deleteOptionEvent, optionChangedEvent, optionChangedEvent, _setMode, setFilepath, setScript
    def populateGSVOptions(self):
        """ Returns a list of options for the current GSV

        These will be displayed to the user in the GSV popup"""
        events_widget = getWidgetAncestor(self, GSVEventWidget)
        gsv = events_widget.currentGSV()
        return [[option] for option in gsvutils.getGSVOptions(gsv, return_as=gsvutils.STRING)]

    def deleteOptionEvent(self, widget):
        """Deletes the user event created for this GSV/Option pairing"""
        events_widget = getWidgetAncestor(self, GSVEventWidget)
        events_widget.setIsFrozen(True)

        # get events widget
        event_widget = getWidgetAncestor(self, GSVEventWidget)
        display_widget = event_widget.eventsWidget().delegateWidget().widget(1).getMainWidget()

        # remove data
        if self.currentOption():
            del event_widget.eventsData()[event_widget.currentGSV()]["data"][self.currentOption()]
            event_widget.saveEventsData()

            del display_widget.widgets()[self.currentOption()]

        # remove widget
        self.deleteLater()
        self.setParent(None)

        Utils.EventModule.ProcessAllEvents()
        events_widget.setIsFrozen(False)

    def showEvent(self, event):
        """ Sets the default size of the main buttons widget (far right buttons)"""
        super(GSVEvent, self).showEvent(event)
        self.mainWidget().moveSplitter(self.width() - self.defaultLabelLength() - 200, 2)

        return AbstractScriptInputWidget.showEvent(self, event)

    def showScript(self, *args):
        """ Show the current script in the Python tab."""
        events_widget = getWidgetAncestor(self, GSVEventWidget)

        # update Python Widget
        events_widget.pythonWidget().setMode(self.mode())
        events_widget.setCurrentScript(self.text())

        # update display
        self.updateScriptDisplayFlag()

    def updateScriptDisplayFlag(self):
        """ Updates the color of all of the show script display buttons"""
        #disable all other scripts displays
        display_gsv_events_widget = getWidgetAncestor(self, DisplayGSVEventWidget)
        for child in display_gsv_events_widget.widgets().values():
            child.setIsEditingActive(False)
            child.showScriptWidget().setTextColor(iColor["rgba_text"])
            child.showScriptWidget().setIsSelected(False)

        # enable this script
        self.setIsEditingActive(True)
        self.showScriptWidget().setIsSelected(True)
        self.showScriptWidget().setTextColor(iColor["rgba_selected"])

    def validateOptionInputEvent(self):
        """
        Determines if the optionsWidget() should update or not.

        When the user changes the value in the options widget, this will
        be called to determine if the user input is valid or not. If the option
        already exists, it will be considered invalid, and set to the pervious value.

        Returns (bool):
        """
        # get attrs
        events_widget = getWidgetAncestor(self, GSVEventWidget)
        option = self.gsvWidget().text()

        #check if already exists
        if option == self.currentOption():
            return True
        elif option in list(events_widget.eventsData()[events_widget.currentGSV()]["data"].keys()):
            return False
        else:
            return True

    def optionChangedEvent(self, widget, option):
        """
        When the user changes the GSV Option, this will create the entry.

        Args:
            widget (QWidget):
            option (str):

        https://stackoverflow.com/questions/16475384/rename-a-dictionary-key
        """
        events_widget = getWidgetAncestor(self, GSVEventWidget)
        display_widget = events_widget.eventsWidget().delegateWidget().widget(1).getMainWidget()

        # preflight
        if option == "": return
        if option == self.currentOption(): return

        # rename existing item
        if self.currentOption():
            # update main events
            data = events_widget.eventsData()[events_widget.currentGSV()]["data"]
            data[option] = data.pop(self.currentOption())

        # create new event
        else:
            # get script status
            if self.mode() == PythonWidget.FILE:
                is_script = False
            elif self.mode() == PythonWidget.SCRIPT:
                is_script = True
            else:
                is_script = True

            # create data entry
            events_widget.eventsData()[events_widget.currentGSV()]["data"][option] = {
                "filepath": self.filepath(),
                "script": self.script(),
                "is_script": is_script,
                "enabled": self.isEnabled()
            }

            # add widget entry into DisplayGSVEventWidget
            display_widget.widgets()[option] = self

        # reset to new value
        self.setCurrentOption(option)
        self.setOrigValue(option)

        # save
        # events_widget = getWidgetAncestor(self, GSVEventWidget)
        events_widget.setIsFrozen(True)

        events_widget.saveEventsData()

        Utils.EventModule.ProcessAllEvents()
        events_widget.setIsFrozen(False)

    """ VIRTUAL """
    def _setMode(self, mode):
        """ Custom functionality when changing between SCRIPT and FILE modes"""
        event_widget = getWidgetAncestor(self, AbstractEventWidget)

        # preflight
        if self.currentOption() == "": return
        if self.currentOption() not in list(event_widget.eventsData()[event_widget.currentGSV()]["data"].keys()): return

        # update meta data
        if self.mode() == PythonWidget.FILE:
            event_widget.eventsData()[event_widget.currentGSV()]["data"][self.currentOption()]["is_script"] = False
            text = event_widget.eventsData()[event_widget.currentGSV()]["data"][self.currentOption()]["filepath"]

        elif self.mode() == PythonWidget.SCRIPT:
            event_widget.eventsData()[event_widget.currentGSV()]["data"][self.currentOption()]["is_script"] = True
            text = event_widget.eventsData()[event_widget.currentGSV()]["data"][self.currentOption()]["script"]

        # show if enabled
        if self.isEditingActive():
            event_widget.pythonWidget().setFilePath(text)

        # update
        self.setText(text)

        # save
        events_widget = getWidgetAncestor(self, GSVEventWidget)
        events_widget.setIsFrozen(True)

        events_widget.saveEventsData()

        Utils.EventModule.ProcessAllEvents()
        events_widget.setIsFrozen(False)

    def setFilepath(self, filepath):
        # preflight
        if self.currentOption() == {}: return
        if not self.currentOption(): return

        self._filepath = filepath

        #
        event_widget = getWidgetAncestor(self, GSVEventWidget)
        event_widget.eventsData()[event_widget.currentGSV()]["data"][self.currentOption()]["filepath"] = filepath

        # save
        events_widget = getWidgetAncestor(self, GSVEventWidget)
        events_widget.setIsFrozen(True)

        events_widget.saveEventsData()

        Utils.EventModule.ProcessAllEvents()
        events_widget.setIsFrozen(False)

        # showScript
        if self.isEditingActive():
            self.showScript()

    def setScript(self, script):
        # preflight
        if self.currentOption() == {}: return
        if not self.currentOption(): return
        self._script = script
        #
        event_widget = getWidgetAncestor(self, GSVEventWidget)
        event_widget.eventsData()[event_widget.currentGSV()]["data"][self.currentOption()]["script"] = script

        # save
        events_widget = getWidgetAncestor(self, GSVEventWidget)
        events_widget.setIsFrozen(True)

        events_widget.saveEventsData()

        Utils.EventModule.ProcessAllEvents()
        events_widget.setIsFrozen(False)


        # showScript
        if self.isEditingActive():
            self.showScript()

    def toggleScriptEnabled(self, widget, enabled):
        """
        When the user presses the disable button.  This will disable/enable the current option

        Args:
            widget (QWidget):
            enabled (bool):
        """

        # preflight
        if self.currentOption() == {}: return
        if not self.currentOption(): return

        # update display
        if enabled:
            widget.setText("E")
            widget.setToolTip("Script is (E)nabled")
        if not enabled:
            widget.setText("D")
            widget.setToolTip("Script is (D)isabled")

        # update data
        self.setIsEnabled(enabled)
        events_widget = getWidgetAncestor(widget, GSVEventWidget)
        events_widget.eventsData()[events_widget.currentGSV()]["data"][self.currentOption()]["enabled"] = enabled

        events_widget = getWidgetAncestor(self, GSVEventWidget)
        events_widget.setIsFrozen(True)
        events_widget.saveEventsData()
        Utils.EventModule.ProcessAllEvents()
        events_widget.setIsFrozen(False)


    """ PROPERTIES """
    def isEnabled(self):
        return self._is_enabled

    def setIsEnabled(self, is_enabled):
        self._is_enabled = is_enabled

    def currentOption(self):
        return self._current_option

    def setCurrentOption(self, current_option):
        self._current_option = current_option

    def script(self):
        return self._script

    def filepath(self):
        return self.delegateWidget().text()

    def isEditingActive(self):
        return self._is_editing_active

    def setIsEditingActive(self, enabled):
        self._is_editing_active = enabled


# from cgwidgets.utils import centerWidgetOnCursor, setAsAlwaysOnTop
# w = GSVManagerTab()
# setAsAlwaysOnTop(w)
# w.show()
# w.resize(512,512)
# centerWidgetOnCursor(w)