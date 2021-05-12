"""
TODO
    Katana (Events)
        # disable handlers
            * EventWidget
                Disable GSV
                Disable Option
"""
import json
import os

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
    ButtonInputWidget,
    FrameInputWidgetContainer,
    ListInputWidget,
    LabelledInputWidget,
    ModelViewWidget,
    OverlayInputWidget,
    ShojiModelViewWidget,
    StringInputWidget)
from cgwidgets.utils import getWidgetAncestor, convertScriptToString, clearLayout
from cgwidgets.settings import attrs, icons, iColor

from Utils2 import gsvutils, getFontSize


class GSVManager(UI4.Tabs.BaseTab):
    """
    Main convenience widget for displaying GSV manipulators to the user.

    Hierarchy:
        QVBoxLayout
            |- mainWidget --> (ShojiModelViewWidget)
                |- viewWidget --> (ViewWidget --> QWidget)
                |    |* ViewGSVWidget --> (LabelledInputWidget)
                |- editWidget --> (EditWidget --> QWidget)
                |   |> VBoxLayout:
                |       |> HBoxLayout
                |       |   |- GSVSelectorWidget --> (LabelledInputWidget --> ListInputWidget)
                |       |   |- CreateNewGSVOptionWidget --> (LabelledInputWidget --> StringInputWidget)
                |       |- displayEditableOptionsWidget --> (ModelViewWidget)
                |- eventsWidget (EventsWidget --> ShojiMVW)
                    |- GSVEventsListWidget --> (LabelledInputWidget)
                    |- DisplayGSVEventWidget (FrameInputWidgetContainer)
                        |- DisplayGSVEventWidgetHeader (OverlayInputWidget --> ButtonInputWidget)
                        |* GSVEvent

    """
    NAME = "GSVManager"

    def __init__(self, parent=None):
        super(GSVManager, self).__init__(parent)

        # create widgets
        self._main_widget = ShojiModelViewWidget(parent=self)

        self._view_widget = ViewWidget(parent=self)
        self._view_scroll_area = QScrollArea(self)
        self._view_scroll_area.setWidget(self._view_widget)
        self._view_scroll_area.setWidgetResizable(True)

        self._edit_widget = EditWidget(parent=self)
        self._events_widget = EventsWidget(parent=self)

        # insert widgets
        self._main_widget.insertShojiWidget(0, column_data={"name":"View"}, widget=self._view_scroll_area)
        self._main_widget.insertShojiWidget(1, column_data={"name":"Edit"}, widget=self.editWidget())
        self._main_widget.insertShojiWidget(2, column_data={"name":"Events"}, widget=self.eventsWidget())

        # setup layout
        QVBoxLayout(self)
        self.layout().addWidget(self._main_widget)
        self.mainWidget().setHeaderItemIsDragEnabled(False)
        self.mainWidget().setHeaderItemIsEditable(False)
        # setup Katana events
        # Utils.EventModule.RegisterCollapsedHandler(self.gsvChanged, 'parameter_finalizeValue', None)
        # Utils.EventModule.RegisterCollapsedHandler(self.gsvChanged, 'parameter_createChild', None)
        # Utils.EventModule.RegisterCollapsedHandler(self.gsvChanged, 'parameter_deleteChild', None)
        Utils.EventModule.RegisterCollapsedHandler(self.nodeGraphLoad, 'nodegraph_loadEnd', None)
        # Utils.EventModule.RegisterCollapsedHandler(self.paramChildDeleted, 'parameter_deleteChild', None)

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
    def nodeGraphLoad(self, args):
        """ Reload the View Widget when a new Katana scene is opened"""
        self.editWidget().setText("<variables>")
        self.viewWidget().update()
        self.editWidget().update()

    # def gsvChanged(self, args):
    #     for arg in args:
    #         # preflight
    #         is_gsv_event = gsvutils.isGSVEvent(arg)
    #         if is_gsv_event:
    #             # get attrs
    #             param = arg[2]['param']
    #             param_name = param.getName()
    #             gsv = param.getParent().getName()
    #
    #             # GSV changed
    #             if param_name == "value":
    #                 # update view
    #                 view_widget = self.viewWidget().widgets()[gsv]
    #                 option = param.getValue(0)
    #                 view_widget.delegateWidget().setText(option)
    #
    #                 # run user script
    #                 # self.gsvChangedEvent(arg)
    #
    #             if param_name == "enabled":
    #                 # todo: setup hide/show events for the view widget
    #                 # todo: setup disable events on the edit side of the view widget
    #                     #handle the enable/disable handler
    #                 pass


""" VIEW WIDGET """
class ViewWidget(FrameInputWidgetContainer):
    """
    Main wigdet for viewing GSV's.

    Attributes:
        widgets (dict): key pair values to map the GSV name to the LabelledInputWidget
    """
    def __init__(self, parent=None):
        super(ViewWidget, self).__init__(parent)
        self.setIsHeaderShown(False)
        self.setDirection(Qt.Vertical)
        #QVBoxLayout(self)
        self._widget_list = {}
        self.populate()

    """ POPULATE """
    def clear(self):
        """
        Removes all of the GSVViewWidgets from the display
        """
        # clear layout (if it exists)
        if self.layout().count() > 0:
            for index in reversed(range(self.layout().count())):
                self.layout().itemAt(index).widget().setParent(None)

        self._widget_list = {}

    def populate(self):
        """Creates the display for every GSV.  This is the left side of the display."""
        # create a combobox for each GSV that is available
        gsv_keys = gsvutils.getAllGSV(return_as=gsvutils.STRING)
        for gsv in gsv_keys:
            self.addWidget(gsv)

    def update(self):
        """
        Updates the current view widgets dispalyed to the user
        """
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


class ViewGSVWidget(LabelledInputWidget):
    """
    One singular GSV view that is displayed in the ViewWidget.

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
        self.gsv = self.name()

        self.viewWidget().setDisplayMode(OverlayInputWidget.DISABLED)

        # setup delegate
        self.delegateWidget().dynamic_update = True
        self.delegateWidget().setUserFinishedEditingEvent(self.setGSVOption)
        self.delegateWidget().populate(self.update())
        self.delegateWidget().setCleanItemsFunction(self.update)
        self.delegateWidget().setValidateInputFunction(self.validateGSVEntry)

    def update(self):
        return [[option] for option in gsvutils.getGSVOptions(self.gsv, return_as=gsvutils.STRING)]

    def validateGSVEntry(self):
        """
        Determines if the GSV option entered by the user is valid.

        If it is not valid, it will reset this widget back to its original value
        """
        option = self.delegateWidget().text()
        if option not in gsvutils.getGSVOptions(self.gsv, return_as=gsvutils.STRING):
            return False
        else:
            return True

    def setGSVOption(self, widget, option):
        """Sets the GSV Option parameter to the specified value"""
        gsvutils.setGSVOption(self.gsv, option)


""" EDIT WIDGET """
class EditWidget(QWidget):
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
        super(EditWidget, self).__init__(parent)

        # Set attrs
        self._display_mode = gsvutils.VARIABLES

        # Create Widgets
        self._gsv_selector_widget = GSVSelectorWidget(parent=self)
        self._create_new_gsv_option_widget = CreateNewGSVOptionWidget(parent=self)
        self._display_editable_options_widget = DisplayEditableOptionsWidget(parent=self)

        # setup default sizes
        font_size = getFontSize()
        self._create_new_gsv_option_widget.setFixedHeight(font_size*6)
        self._gsv_selector_widget.setFixedHeight(font_size * 6)

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


class GSVSelectorWidget(LabelledInputWidget):
    """This will display the currently active GSV to the user

    Changing this drop down will change the edit widgets display of the currently available
    options based off of the GSV selected.

    Setting this to <variables> is a special case, that will allow the user to manipulate
    the GSV's instead of their individual options.
    """

    def __init__(self, parent=None):
        super(GSVSelectorWidget, self).__init__(parent)

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

        main_widget = getWidgetAncestor(self, GSVManager)

        if main_widget:
            gsv = str(self.delegateWidget().text())
            edit_widget = main_widget.editWidget()
            edit_widget.setDisplayMode(gsvutils.OPTIONS)
            gsv_list = gsvutils.getAllGSV(return_as=gsvutils.STRING)
            # create new GSV if it doesn't exist
            if gsv not in gsv_list:
                # create new GSV in katana
                gsvutils.createNewGSV(gsv)

                # create new entry in the view widget
                main_widget.viewWidget().addWidget(gsv)

            # Update options available to the user
            if hasattr(main_widget, '_edit_widget'):
                edit_widget.displayEditableOptionsWidget().update()

    def setVariablesDisplayMode(self):
        """When the GSV is changed, this will show the VARIABLES available in the displayEditableOptionsWidget

        Args:
            gsv (str): name of GSV
        """
        edit_widget = getWidgetAncestor(self, EditWidget)
        if hasattr(edit_widget, '_display_editable_options_widget'):
            # edit_widget = getWidgetAncestor(self, EditWidget)
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
    def __init__(self, parent=None):
        super(CreateNewGSVOptionWidget, self).__init__(parent)
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
        main_widget = getWidgetAncestor(self, GSVManager)
        edit_widget = main_widget.editWidget()
        current_gsv_text = str(edit_widget.text())

        # Pre flight
        if value == "": return
        if current_gsv_text == "": return

        # Create new GSV Option
        if current_gsv_text != '<variables>':
            option = str(value)
            if current_gsv_text in gsvutils.getAllGSV(return_as=gsvutils.STRING):
                param = gsvutils.createNewGSVOption(current_gsv_text, option)
                new_entry_text = option

        # Create new GSV
        elif current_gsv_text == '<variables>':
            gsv = str(value)
            gsv_list = gsvutils.getAllGSV(return_as=gsvutils.STRING)
            # create new GSV if it doesn't exist
            if gsv not in gsv_list:
                # create new GSV in katana
                param = gsvutils.createNewGSV(gsv)

                # create new entry in the view widget
                main_widget.viewWidget().addWidget(gsv)

                # get new entry text
                new_entry_text = gsv

            # return if GSV exists
            else:
                print("{gsv} already exists you dingus".format(gsv))
                return
        # create new list entry
        model = main_widget.editWidget().displayEditableOptionsWidget().model()
        root_item = model.getRootItem()
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

        edit_widget = getWidgetAncestor(self, EditWidget)

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
        edit_widget = getWidgetAncestor(self, EditWidget)

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
        main_widget = getWidgetAncestor(self, GSVManager)
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
        edit_widget = getWidgetAncestor(self, EditWidget)

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
                main_widget = getWidgetAncestor(self, GSVManager)
                view_widget = main_widget.viewWidget()
                view_widget.update()

    def deleteSelection(self, item):
        """ Deletes the specified item, and removes the relevant data.

        Args:
            item (DisplayEditableOptionsItem): currently selected
        """
        main_widget = getWidgetAncestor(self, GSVManager)
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
                        if option in list(events_widget.eventsData()[gsv].keys()):
                            # get delegate widget
                            main_delegate_widget = events_widget.delegateWidget().widget(1).getMainWidget()

                            # delete widget
                            main_delegate_widget.widgets()[option].deleteLater()
                            main_delegate_widget.widgets()[option].setParent(None)
                            del main_delegate_widget.widgets()[option]

                            # destroy event data
                            del events_widget.eventsData()[gsv][option]
                            events_widget.saveEventsData()

        # Remove Variable
        if edit_widget.displayMode() == gsvutils.VARIABLES:
            # get attrs
            main_widget = getWidgetAncestor(self, GSVManager)
            view_widget = main_widget.viewWidget()
            gsv = item.columnData()['name']

            # remove param
            gsvutils.deleteGSV(gsv)

            # remove widget
            view_widget.removeWidget(gsv)

            # remove event
            if gsv in list(events_widget.eventsData().keys()):
                # remove item
                for item in events_widget.model().findItems(gsv):
                    events_widget.model().deleteItem(item.internalPointer(), event_update=True)

    def renameSelectedItem(self, item, old_value, new_value):
        """
        Changes the GSV/Option name to the values provided

        Args:
            item (DisplayEditableOptionsItem): current item selected
            old_value (str): current value of item
            new_value (str): new value that is being set

        Note:
            When the user Double Clicks to enter the item's text field.

        """
        edit_widget = getWidgetAncestor(self, EditWidget)

        # Rename Option
        if edit_widget.displayMode() == gsvutils.OPTIONS:
            # get attrs
            gsv = edit_widget.text()
            gsvutils.renameGSVOption(gsv, old_value, new_value)

        # Rename GSV
        if edit_widget.displayMode() == gsvutils.VARIABLES:
            # rename
            gsvutils.renameGSV(old_value, new_value)

            # update view widget
            main_widget = getWidgetAncestor(self, GSVManager)
            view_widget = main_widget.viewWidget()
            view_widget.renameWidget(old_value, new_value)

            # print(view_widget.widgets())
            # print(old_value)
            # view_widget.widgets()[old_value].setName(new_value)


""" EVENTS WIDGET """
class EventsWidget(ShojiModelViewWidget):
    """
    Main tab for displaying the GSV Events to the user.

    This is where the user can setup custom handlers for when GSV's change,
    and run Python code for a GSV change.

    Attributes:
        current_gsv (str): name of current GSV that is being manipulated
        events_data (dict): of GSV names that are already created as events in this widget.
            {gsv_name1: {
                "option1":{file_path:"path_to_script.py", script: "script text"},
                "option2":{file_path:"path_to_script.py", script: "script text"}},
            gsv_name2: {
                "option3":{file_path:"path_to_script.py", script: "script text"},
                "option4":{file_path:"path_to_script.py", script: "script text"}},
            }
    Hierarchy:
        |- GSVEventsListWidget --> (LabelledInputWidget)
        |- DisplayGSVEventWidget (FrameInputWidgetContainer)
            |- Header
            |   |- DisplayGSVEventWidgetHeader (OverlayInputWidget --> ButtonInputWidget)
            |- Widgets
                |* GSVEvent
    """
    def __init__(self, parent=None):
        super(EventsWidget, self).__init__(parent)

        # setup default attrs
        self.setHeaderPosition(attrs.WEST, attrs.SOUTH)
        self.setHeaderItemIsEditable(False)
        self.setHeaderItemIsDragEnabled(False)

        self._events_data = {}

        # setup Dynamic Widgets
        self.setDelegateType(
            ShojiModelViewWidget.DYNAMIC,
            dynamic_widget=DisplayGSVEventWidget,
            dynamic_function=EventsWidget.displayGSVEventWidget
        )

        # setup creation widget
        self._gsv_events_list_widget = GSVEventsListWidget(self)
        self.addHeaderDelegateWidget([], self._gsv_events_list_widget)
        self._gsv_events_list_widget.show()

        # setup events
        self.setHeaderItemDeleteEvent(self.deleteGSVEvent)

        # set style
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    """ WIDGETS """
    def gsvEventsListWidget(self):
        return self._gsv_events_list_widget

    def displayWidget(self):
        # todo this doesnt work...
        self.delegateWidget().widget(1).getMainWidget()

    """ PROPERTIES """
    def currentGSV(self):
        return self._current_gsv

    def setCurrentGSV(self, gsv):
        self._current_gsv = gsv

    """ UTILS """
    @staticmethod
    def isScriptDirty(data, widget):
        # display update button if the scripts do not match
        if os.path.exists(data["file_path"]):
            script = data["script"]
            _is_dirty = False
            # read filepath
            with open(data["file_path"], "r") as file_path:
                file_data = file_path.readlines()
                file_data = "".join(file_data).split("\n")

            # compare filepath to current script
            for line1, line2 in zip(file_data, script.split("\n")):
                if str(line1) != str(line2):
                    _is_dirty = True
                    break

            # display update
            widget.setIsScriptDirty(_is_dirty)

    def eventsData(self):
        return self._events_data

    @staticmethod
    def eventsParam():
        """
        Gets the parameter on the root node which holds the event data

        Returns (Parameter)
        """
        EventsWidget.createGSVEventsParam()
        events_param = NodegraphAPI.GetRootNode().getParameter("_gsv_events_data")
        return events_param

    @staticmethod
    def createGSVEventsParam():
        """
        Creates the GSV Events param if one doesn't already exist
        """
        node = NodegraphAPI.GetRootNode()
        if not node.getParameter("_gsv_events_data"):
            node.getParameters().createChildString("_gsv_events_data", "{}")

    def saveEventsData(self):
        """ Saves the events data to the parameter """
        # get data
        events_data = self.eventsData()

        # ensure param exists
        EventsWidget.createGSVEventsParam()

        # set data
        new_data = json.dumps(events_data)
        self.eventsParam().setValue(new_data, 0)

    """ EVENTS """
    def deleteGSVEvent(self, item):
        """
        When the user deletes a GSV event, this will remove the meta data.
        """
        gsv = item.columnData()['name']

        # delete data
        del self.eventsData()[gsv]
        self.saveEventsData()

    def showEvent(self, event):
        EventsWidget.createGSVEventsParam()
        return ShojiModelViewWidget.showEvent(self, event)

    def createNewGSVEvent(self, gsv):
        """
        Creates a new GSVEventItem for the user, and creates the corresponding metadata
        Args:
            gsv (str):
        """
        gsv = str(gsv)

        # store local dictionary
        self.eventsData()[gsv] = {}

        # create new index
        self.insertShojiWidget(0, column_data={"name": str(gsv)})

        # save
        self.saveEventsData()

    @staticmethod
    def displayGSVEventWidget(parent, widget, item):
        """ Updates the Dynamic display for the current GSV Event shown to the user"""
        # preflight
        if not item: return

        # get attrs
        display_widget = widget.getMainWidget()
        gsv = item.columnData()['name']

        # update GSV
        parent.setCurrentGSV(gsv)
        display_widget.setGSV(gsv)

        # remove old display
        clearLayout(display_widget.layout(), start=2)

        # update display
        events_dict = json.loads(parent.eventsParam().getValue(0))[gsv]
        for option, data in events_dict.items():
            # todo: check file status
            """compare script being uploaded to the "script" arg and if they are not the same,
            break set flag available to update."""

            # create widget
            widget = display_widget.createNewOptionEvent(option=str(option), script=str(data["file_path"]))

            # check if cached script is dirty or not
            EventsWidget.isScriptDirty(data, widget)


class GSVEventsListWidget(LabelledInputWidget):
    def __init__(self, parent=None):
        super(GSVEventsListWidget, self).__init__(parent)

        # setup default attrs
        self.setDirection(Qt.Horizontal)

        # setup view widget
        self.setName("GSV")
        self.viewWidget().setDisplayMode(OverlayInputWidget.DISABLED)

        # setup delegate widget
        delegate_widget = ListInputWidget(self)
        self.setDelegateWidget(delegate_widget)

        # setup delegate widget attrs
        self.delegateWidget().dynamic_update = True
        self.delegateWidget().filter_results = False
        self.delegateWidget().setText("")

        # setup events
        self.delegateWidget().setUserFinishedEditingEvent(self.createNewGSVEventItem)
        self.delegateWidget().populate(self.getAllGSVNames())
        self.delegateWidget().setCleanItemsFunction(self.getAllGSVNames)

        #setup display
        self.setFixedHeight(getFontSize() * 4)
        self.setDefaultLabelLength(getFontSize() * 6)

    def getAllGSVNames(self):
        """
        Returns a list of lists of all of the GSV names
        Returns (list): of lists
            [['var1'], ['var2'], ['var3']]

        """
        variables = gsvutils.getAllGSV(return_as=gsvutils.STRING)
        gsv_keys = [[variable] for variable in variables]
        return gsv_keys

    def createNewGSVEventItem(self, widget, value):
        """ Create a new event item"""
        # get attrs
        main_widget = getWidgetAncestor(self, EventsWidget)
        gsv = value

        # preflight
        if value == "": return
        if value in list(main_widget.eventsData().keys()):
            print("{gsv} already exists... update the one that already exists you Derpasaur".format(gsv=value))
            return

        # create new GSV event item
        if gsv in gsvutils.getAllGSV(return_as=gsvutils.STRING):
            main_widget.createNewGSVEvent(gsv)
            self.delegateWidget().setText("")

        # bypass if doesn't exist
        else:
            return


class DisplayGSVEventWidget(FrameInputWidgetContainer):
    def __init__(self, parent=None):
        super(DisplayGSVEventWidget, self).__init__(parent)
        self.setDirection(Qt.Vertical)
        self._widgets = {}

        # setup header widget
        header_widget = DisplayGSVEventWidgetHeader(self)
        self.setHeaderWidget(header_widget)

    def setGSV(self, gsv):
        """ When the dynamic update is run, this updates the title"""
        self.headerWidget().setTitle(gsv)

    def createNewOptionEvent(self, option=None, script=None):
        new_widget = GSVEvent(parent=self, option=option, script=script)
        self.addInputWidget(new_widget)
        return new_widget

    def widgets(self):
        return self._widgets


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
        self.setFixedHeight(getFontSize() * 2)

    def createNewEvent(self, widget):
        """
        Creates a new event for the user

        """

        # add new input
        main_widget = getWidgetAncestor(self, DisplayGSVEventWidget)
        main_widget.createNewOptionEvent()


class GSVEvent(LabelledInputWidget):
    """
    One input event for a specified GSV.

    Args:
        option (str):
        script (str):
    """
    def __init__(self, parent=None, option=None, script=None):
        super(GSVEvent, self).__init__(parent)
        self.setDirection(Qt.Horizontal)

        # setup default attrs
        self._current_option = option
        self._script = script
        self._is_script_dirty = False

        # setup view widget
        view_widget = ListInputWidget()
        view_widget.populate(self.populateGSVOptions())
        view_widget.dynamic_update = True
        view_widget.setCleanItemsFunction(self.populateGSVOptions)
        view_widget.setUserFinishedEditingEvent(self.optionChangedEvent)
        self.setViewWidget(view_widget)

        # setup delegate widget
        self.delegateWidget().setUserFinishedEditingEvent(self.scriptChangedEvent)

        # add update script button
        self._cache_script_button = self.__insertButton(
            2, "", "Cache Script", self.cacheScript, image_path=icons["update"])
        self._cache_script_button.setTextBackgroundColor(iColor["rgba_background_00"])

        # add delete button
        self._delete_button = self.__insertButton(
            3, "-", "Delete", self.deleteOptionEvent)

        # set display attrs
        if option:
            self.viewWidget().setText(option)
        if script:
            self.delegateWidget().setText(script)

        # set fixed height
        self.setFixedHeight(getFontSize() * 2)
        self.setHandleWidth(1)

    """ WIDGETS """
    def __insertButton(self, index, name, tooltip, user_event, image_path=None):
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
        button_widget = ButtonInputWidget(
            user_clicked_event=user_event, title=name, flag=False, is_toggleable=False)

        # add to main widget
        self.mainWidget().insertWidget(index, button_widget)

        # setup attrs todo: fix this later...
        button_widget.setFixedSize(getFontSize() * 2.5, getFontSize() * 2.5)
        button_widget.setToolTip(tooltip)
        if image_path:
            button_widget.setImage(image_path)
        self.mainWidget().setCollapsible(index, False)
        self.mainWidget().setStretchFactor(index, 0)

        return button_widget

    def deleteButton(self):
        return self._delete_button

    def optionsWidget(self):
        return self.viewWidget()

    def scriptWidget(self):
        return self.delegateWidget()

    def cacheScriptButton(self):
        return self._cache_script_button

    """ EVENTS """
    def populateGSVOptions(self):
        events_widget = getWidgetAncestor(self, EventsWidget)
        gsv = events_widget.currentGSV()
        return [[option] for option in gsvutils.getGSVOptions(gsv, return_as=gsvutils.STRING)]

    def deleteOptionEvent(self, widget):
        """
        Deletes the user event created for this GSV/Option pairing
        Args:
            widget:
        """
        # get events widget
        event_widget = getWidgetAncestor(self, EventsWidget)
        display_widget = event_widget.displayWidget()

        # remove data
        del event_widget.eventsData()[event_widget.currentGSV()][self.currentOption()]
        event_widget.saveEventsData()

        del display_widget.widgets()[self.currentOption()]

        # remove widget
        self.deleteLater()
        self.setParent(None)

    def cacheScript(self, widget):
        """ This will cache the script to a local value

        Note: The script must be a valid file in order for it to cache
        """
        # get file path
        file_path = self.scriptWidget().text()

        if os.path.exists(file_path):
            script = convertScriptToString(file_path)
            # get events widget
            event_widget = getWidgetAncestor(self, EventsWidget)

            # update script
            event_widget.eventsData()[event_widget.currentGSV()][self.currentOption()]["script"] = script

            # save
            event_widget.saveEventsData()

        else:
            print('{file_path} does not exist... please make one that does...'.format(file_path=file_path))
        self.setIsScriptDirty(False)

    def optionChangedEvent(self, widget, option):
        """
        When the user changes the GSV Option, this will create the entry.

        Args:
            widget (QWidget):
            option (str):

        https://stackoverflow.com/questions/16475384/rename-a-dictionary-key
        """
        events_widget = getWidgetAncestor(self, EventsWidget)
        display_widget = events_widget.delegateWidget().widget(1).getMainWidget()

        # preflight
        if option == "": return

        # rename existing item
        if self.currentOption():
            # update main events
            data = events_widget.eventsData()[events_widget.currentGSV()]
            data[option] = data.pop(self.currentOption())

            # update DisplayGSVEventWidget
            display_widget.widgets()[option] = display_widget.widgets()[self.currentOption()]

        # create new event
        else:
            # update main events
            events_widget.eventsData()[events_widget.currentGSV()][option] = {"file_path": "", "script": ""}

            # add widget entry into DisplayGSVEventWidget
            display_widget.widgets()[option] = self

        # reset to new value
        self.setCurrentOption(option)

        # save
        events_widget.saveEventsData()

    def scriptChangedEvent(self, widget, filepath):
        """
        When the script changes, this will update the main events dictionary
        Args:
            widget:
            filepath:

        Note: TODO: Check to ensure the python file is valid
        """

        # preflight
        if self.currentOption() == {}: return
        if not self.currentOption(): return

        # get events widget
        event_widget = getWidgetAncestor(self, EventsWidget)

        # update script
        event_widget.eventsData()[event_widget.currentGSV()][self.currentOption()]["file_path"] = filepath

        # save
        event_widget.saveEventsData()

        # update script button
        self.cacheScript(None)
        #EventsWidget.isScriptDirty(event_widget.eventsData()[event_widget.currentGSV()][self.currentOption()], self)

    """ UPDATE SCRIPT """
    def isScriptDirty(self):
        return self._is_script_dirty

    def setIsScriptDirty(self, is_script_dirty):
        """
        Determines if the file_path is the same, or needs to be updated.

        Args:
            is_script_dirty (bool):

        Returns:

        """
        self._is_script_dirty = is_script_dirty
        if is_script_dirty:
            self.cacheScriptButton().setTextBackgroundColor(iColor["rgba_gray_4"])
        if not is_script_dirty:
            self.cacheScriptButton().setTextBackgroundColor(iColor["rgba_background_00"])

    """ PROPERTIES """
    def currentOption(self):
        return self._current_option

    def setCurrentOption(self, current_option):
        self._current_option = current_option

    def script(self):
        return self._script

    def setScript(self, script):
        self._script = script



