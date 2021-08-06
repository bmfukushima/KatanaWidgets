"""
Abstract class for creating EventsWidgets.  These widgets will be able to create
user driven events based off of the Callbacks and Events in Katana
(https://learn.foundry.com/katana/dev-guide/Scripting/CallbacksAndEvents.html).

This class will most notably be used in:
    SimpleTools (SuperTool)
    GSVManager (Tab)
    Event Manager (tab)

Hierarchy:
EventWidget --> (ShojiLayout)
    | -- main_widget (QWidget)
    |    | -- VBox
    |        | -- newEventButton() --> (QPushButton)
    |        | -- events_widget --> (ShojiModelViewWidget)
    |        |    | -- label type (EventsLabelWidget --> ShojiLabelWidget)
    |        |    | -- Dynamic Widget (UserInputMainWidget --> QWidget)
    |        |        | -- VBox
    |        |            | -- events_type_menu ( EventTypeInputWidget)
    |        |            | -- script_widget (DynamicArgsInputWidget)
    |        |            | -- dynamic_args_widget (DynamicArgsWidget)
    |        |                    | -* DynamicArgsInputWidget
    |        | -- _update_events_button --> (ButtonInputWidget)
    | -- python_widget --> (PythonWidget)
TODO:
    * PYTHON Script (Moving this to have the option between SCRIPT and FILE modes)
        Store hash in the events_data, and use that hash to get a parameter
        which can hold the raw text script (avoid char limits)
        - get/create parameter
        - update events_data to have a "script_mode" option
        - Get Script Text
        - Update text in Python Widget
            UserInputMainWidget --> updateGUI
            ScriptInputWidget --> updateUserInput
            # SAVE TEXT
        - Update events call to handle args...
            EventWidget --> eventHandler
        IDE popup is causing PythonWidget to lose focus

    *   Globals
            - disable does not work
                on simple tools auto toggles/updates
                    - only node set edited...
                    - only on node set true? enabled?
    *   Load nodes init
            on scene load, initialize all handlers
                scene load event
    *   Model
            {
                nodeid
                eventid
    *   EventsLabelWidget
        --> Context Menu...
                | -- enabled
                        Set text styles...
                | -- disable
                        Set text styles...
                | -- delete
                        overlay red/green widet
                            accept / cancel
        --> editing finished
                | -- update model

"""

import json
import os

from qtpy.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QMenu, QSizePolicy)
from qtpy.QtCore import Qt, QEvent
from qtpy.QtGui import QKeySequence

from Katana import Utils, NodegraphAPI, UI4

from cgwidgets.widgets import (
    ListInputWidget, LabelledInputWidget, BooleanInputWidget, ButtonInputWidget, FileBrowserInputWidget,
    ShojiModelViewWidget, ShojiModelItem, OverlayInputWidget,
    ShojiLayout)
from cgwidgets.views import AbstractDragDropListView, AbstractDragDropModelDelegate
from cgwidgets.utils import getWidgetAncestor
from cgwidgets.settings import attrs

from Utils2 import paramutils, getFontSize


""" ABSTRACT EVENTS"""
class AbstractEventListViewItem(ShojiModelItem):
    """
    name (str): name given to this event by the user
    event_type (str): katana event type
    script (path): path on disk to .py file to run as script
    args (dict): dictionary of all the args
    index (int): current index that this item is holding in the model
    enabled (bool): If this event should be enabledd/disabled
    """
    def __init__(self, name=None, event_type=None, script=None, args={}, index=0, enabled=True):
        super(AbstractEventListViewItem, self).__init__(name)
        self.columnData()["name"] = name
        self._event_type = event_type

    """ args """
    def args(self):
        return self.columnData()

    def setArg(self, arg, value):
        self.columnData()[arg] = value

    def getArg(self, arg):
        return self.columnData()[arg]

    def getArgsList(self):
        return list(self.columnData().keys())

    def removeArg(self, arg):
        self.columnData().pop(arg, None)

    def clearArgsList(self):
        for key in list(self.columnData().keys()):
            self.columnData().pop(key, None)


class AbstractEventWidget(ShojiLayout):
    """
    The main widget for setting up the events triggers on the node.

    Args:
        node (Node): Node to store events data on
        param (str): Location of param to create events data at

    Hierarchy:
        | -- VBox
            | -- events_widget --> (ShojiModelViewWidget)
                | -- label type (EventsLabelWidget --> ShojiLabelWidget)
                | -- Dynamic Widget (UserInputMainWidget --> QWidget)
                    | -- VBox
                        | -- events_type_menu ( EventTypeInputWidget)
                        | -- script_widget (DynamicArgsInputWidget)
                        | -- dynamic_args_widget (DynamicArgsWidget)
                                | -* DynamicArgsInputWidget
    """
    def __init__(
            self,
            delegate_widget_type,
            events_list_view=AbstractDragDropListView,
            events_model_item_type=AbstractEventListViewItem,
            parent=None,
            node=None,
            param="events_data"
    ):
        super(AbstractEventWidget, self).__init__(parent)
        self._delegate_widget_type = delegate_widget_type
        self._events_list_view = events_list_view
        self._events_model_item_type = events_model_item_type

        # init data param
        if not node:
            node = NodegraphAPI.GetRootNode()
        if not node.getParameter(param):
            paramutils.createParamAtLocation(param, node, paramutils.STRING, initial_value="{}")
            #node.getParameters().createChildString(param, "")

        self._param_location = param
        self._node = node

        # setup attrs
        self._events_model = []
        self._new_event_key = Qt.Key_Q
        self._events_data = {}

        # setup layout
        # TODO CHANGE MAIN WIDGET...
        self._main_widget = QWidget()
        QVBoxLayout(self.mainWidget())

        # create events widget
        self.setupEventsWidgetGUI()
        self.mainWidget().layout().addWidget(self.eventsWidget())

        # create new event button
        new_event_button_title = 'New Event ({key})'.format(key=QKeySequence(self._new_event_key).toString())
        self._new_event_button = ButtonInputWidget(
            self, title=new_event_button_title, is_toggleable=False, user_clicked_event=self.createNewEvent)

        self.eventsWidget().addHeaderDelegateWidget(
            [self._new_event_key], self.newEventButton())
        self.newEventButton().show()

        # create Python tab
        self._python_widget = PythonWidget()

        # add widgets to layout
        self.addWidget(self.mainWidget())
        self.addWidget(self.pythonWidget())

        # set up stretch
        self.eventsWidget().setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)

        # setup events
        Utils.EventModule.RegisterCollapsedHandler(self.nodeNameChange, 'node_setName')

    def setupEventsWidgetGUI(self):
        """
        Sets up the main Shoji widget that is showing the events to the user
        """
        # create widget
        self._events_widget = ShojiModelViewWidget(self)

        # setup header
        events_view = self.eventsListViewType()(self)
        self.eventsWidget().setHeaderViewWidget(events_view)
        self.eventsWidget().setHeaderData(["name"])

        # setup custom item type
        self.eventsWidget().model().setItemType(self.eventsModelItemType())

        # setup flags
        self.eventsWidget().setHeaderItemIsDropEnabled(False)
        self.eventsWidget().setHeaderItemIsEnableable(True)
        self.eventsWidget().setHeaderItemIsDeleteEnabled(True)

        # set type / position
        self.eventsWidget().setHeaderPosition(attrs.WEST, attrs.SOUTH)
        self.eventsWidget().setDelegateType(
            ShojiModelViewWidget.DYNAMIC,
            dynamic_widget=self.delegateWidgetType(),
            dynamic_function=self.delegateWidgetType().updateGUI
        )

        self.eventsWidget().setHeaderDefaultLength(250)

        return self.eventsWidget()

    """ UTILS """
    def setCurrentScript(self, filepath):
        self.pythonWidget().setFilePath(filepath)

    """ EVENTS """
    def createNewEvent(self, widget, column_data=None):
        """
        Creates a new event item
        """
        if not column_data:
            column_data = {"name": "<New Event>", "enabled": "True", "script": "", "filepath": ""}
        # create model item
        new_index = self.eventsWidget().insertShojiWidget(0, column_data=column_data)
        item = new_index.internalPointer()

        # update script / enabled args
        for arg in ["enabled", "filepath", "script"]:
            item.setArg(arg, column_data[arg])
            if arg == "script":
                self.eventsWidget().model().setItemEnabled(item, column_data["enabled"])

    def loadEventsDataFromParam(self):
        # TODO clear all items
        try:
            json_data = json.loads(self.node().getParameter(self.paramLocation()).getValue(0))
        except ValueError:
            return

        for event_type in json_data:
            event = json_data[str(event_type)]
            self.createNewEvent(None, column_data=event)

    def nodeNameChange(self, args):
        """ Updates the events data when a node name has been changed in Katana """
        for arg in args:
            # get data
            node = arg[2]["node"]
            old_name = arg[2]["oldName"]
            new_name = arg[2]["newName"]

            indexes = self.eventsWidget().getAllIndexes()
            for index in indexes:
                item = index.internalPointer()
                if "node" not in item.getArgsList(): continue
                if item.getArg("node") != old_name: continue
                item.setArg("node", new_name)

            self.updateEventsData()
            self.saveEventsData()
            self.eventsWidget().updateDelegateDisplay()

    """ EVENTS DATA """
    def eventsData(self, from_param=False):
        """
        Returns the dictionary of events data that was set up by the user.
        This is also stored in the parameter on the node() under the paramLocation()
        """
        # load from parameters
        if from_param:
            return json.loads(self.node().getParameter(self.paramLocation()).getValue(0))
        # load from current GUI (unsaved) values
        else:
            self.updateEventsData()
            return self._events_data

    def setEventsData(self, events_data):
        self._events_data = events_data

    def saveEventsData(self, *args):
        """ Saves the events data to the parameter """
        # get data
        events_data = self.eventsData()

        # set data
        new_data = json.dumps(events_data)
        self.param().setValue(new_data, 0)

    def updateEventsData(self):
        """ Needs to be overwritten, this will be called before every
        call to eventsData()"""
        return

    """ PROPERTIES """
    def node(self):
        return self._node

    def setNode(self, node):
        self._node = node

    def param(self):
        return self.node().getParameter(self.paramLocation())

    def paramLocation(self):
        return self._param_location

    def eventsModelItemType(self):
        return self._events_model_item_type

    def delegateWidgetType(self):
        return self._delegate_widget_type

    def eventsListViewType(self):
        return self._events_list_view

    """ WIDGETS """
    def eventsWidget(self):
        return self._events_widget

    def mainWidget(self):
        return self._main_widget

    def newEventButton(self):
        return self._new_event_button

    def pythonWidget(self):
        return self._python_widget


class AbstractEventListView(AbstractDragDropListView):
    """ List View that is shown on the left side of the widget.

    Args:
        delegate (AbstractDragDropModelDelegate): popup to be displayed
            when the user double clicks on the item.

    """
    def __init__(self, parent=None, delegate=None):
        super(AbstractEventListView, self).__init__(parent)
        if delegate:
            _delegate = delegate(self)
            self.setItemDelegate(_delegate)
        else:
            self.setIsEditable(False)

    def contextMenuEvent(self, event):
        index = self.getIndexUnderCursor()
        # create menu
        menu = QMenu(self)
        menu.addAction('test"')
        action = menu.exec_(self.mapToGlobal(event.pos()))
        # item = self.model().item
        # if self.item().getEnable() is True:
        #     set_disabled = menu.addAction("Disable")
        # else:
        #     set_enabled = menu.addAction("Enable")
        # menu.addSeparator()
        # delete = menu.addAction("Delete")
        #
        # # do menu actions
        # action = menu.exec_(self.mapToGlobal(event.pos()))
        #
        # try:
        #     if action == set_disabled:
        #         self.setItemEnable(False)
        #
        #     if action == set_enabled:
        #         self.setItemEnable(True)
        # except UnboundLocalError:
        #     pass
        #
        # if action == delete:
        #     self.deleteItem()


class AbstractEventListViewItemDelegate(AbstractDragDropModelDelegate):
    """ Creates the popup for the ShojiMVW item

    Args:
        populate_events_list_func (function): returns a list of strings
            that will be displayed when the user clicks on the delegate.
        """
    def __init__(self, populate_events_list_func, parent=None):
        super(AbstractEventListViewItemDelegate, self).__init__(parent)
        self._populate_events_list_func = populate_events_list_func
        self.setDelegateWidget(ListInputWidget)
        self._parent = parent

    def _populate_events_list_func(self, parent):
        """ Should be overwritten, and return a list of strings that
        will be displayed when the user displays the options available"""
        return []

    def getEventsList(self, parent):
        return self._populate_events_list_func(parent)

    def createEditor(self, parent, option, index):
        delegate_widget = self.delegateWidget(parent)

        # populate events
        delegate_widget.populate([[item] for item in sorted(self.getEventsList(parent))])

        # set update trigger
        def updateDisplay(widget, value):
            events_widget = getWidgetAncestor(self._parent, EventWidget)
            events_widget.eventsWidget().updateDelegateDisplay()

        delegate_widget.setUserFinishedEditingEvent(updateDisplay)
        return delegate_widget


""" PYTHON SCRIPT """
class PythonWidget(QWidget):
    def __init__(self, parent=None):
        super(PythonWidget, self).__init__(parent)
        self._filepath = ""

        self.createUI()

    def createUI(self):
        layout = QVBoxLayout(self)

        filepath_layout = QHBoxLayout()

        # create filepath widget
        self._filepath_widget = FileBrowserInputWidget(self)
        self._filepath_widget.setUserFinishedEditingEvent(self.filepathChanged)
        # create save widget
        self._save_widget = ButtonInputWidget(title="Save", user_clicked_event=self.saveEvent)
        self._save_widget.setFixedWidth(125)

        # create is changed widget
        # self._is_dirty_widget = BooleanInputWidget(self)
        # self._is_dirty_widget.setFixedWidth(25)

        filepath_layout.addWidget(self.filepathWidget())
        filepath_layout.addWidget(self.saveWidget())
        #filepath_layout.addWidget(self.isDirtyWidget())

        # create Python Tab
        python_tab = UI4.App.Tabs.CreateTab('Python', None)

        self._python_tab_widget = python_tab.getWidget()
        python_widget = self._python_tab_widget._pythonWidget
        script_widget = python_widget._FullInteractivePython__scriptWidget
        self._command_widget = script_widget.commandWidget()
        self._command_widget.installEventFilter(self)

        # add widgets to layout
        layout.addWidget(python_tab)
        layout.addLayout(filepath_layout)

        # set size
        self._filepath_widget.setFixedHeight(getFontSize() * 2)
        self._save_widget.setFixedHeight(getFontSize() * 2)

    """ PROPERTIES """
    def filepath(self):
        return self._filepath

    def setFilePath(self, filepath):
        self.filepathWidget().setText(filepath)
        self.filepathChanged(self, filepath)
        self._filepath = filepath
        if filepath.endswith(".py"):
            # todo update save button to valid
            pass
        else:
            # todo update save button to invalid
            pass

    def getCurrentScript(self):
        return self.commandWidget().toPlainText()

    """ EVENTS """
    def saveEvent(self, widget):
        """ Saves the current IDE text to the current file"""
        text = self.getCurrentScript()
        with open(self.filepath(), "w") as file:
            file.write(text)

    def filepathChanged(self, widget, filepath):
        """ Sets the IDE text to the filepath provided

        Args:
            filepath (str): path on disk to file
        """
        if filepath.endswith(".py"):
            with open(filepath, "r") as file:
                text_list = file.readlines()
                text = "".join(text_list)
        else:
            # todo update save button to invalid
            text = ""
        self.commandWidget().setPlainText(text)

    def eventFilter(self, obj, event, *args, **kwargs):
        if event.type() == QEvent.Enter:
            obj.setFocus()

        return False

    """ WIDGETS """
    def filepathWidget(self):
        return self._filepath_widget

    def saveWidget(self):
        return self._save_widget

    def isDirtyWidget(self):
        return self._is_dirty_widget

    def pythonTabWidget(self):
        return self._python_tab_widget

    def commandWidget(self):
        return self._command_widget


""" GLOBAL EVENTS"""
class EventWidget(AbstractEventWidget):
    """
    The main widget for setting up the events triggers on the node.

    Args:
        node (Node): Node to store events data on
        param (str): Location of param to create events data at

    Hierarchy:
        | -- VBox
            | -- events_widget --> (ShojiModelViewWidget)
                | -- label type (EventsLabelWidget --> ShojiLabelWidget)
                | -- Dynamic Widget (UserInputMainWidget --> QWidget)
                    | -- VBox
                        | -- events_type_menu ( EventTypeInputWidget)
                        | -- script_widget (DynamicArgsInputWidget)
                        | -- dynamic_args_widget (DynamicArgsWidget)
                                | -* DynamicArgsInputWidget
    """
    def __init__(self, parent=None, node=None, param="events_data"):
        delegate_widget_type = UserInputMainWidget
        events_list_view = EventListView

        super(EventWidget, self).__init__(
            delegate_widget_type,
            events_list_view=events_list_view,
            parent=parent,
            node=node,
            param=param)

        self.generateDefaultEventTypesDict()
        # create update button
        self._update_events_button = ButtonInputWidget(
            self, title="Update Events", is_toggleable=False, user_clicked_event=self.installEvents)
        self.mainWidget().layout().addWidget(self.updateEventsButton())
        self.updateEventsButton().setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        # load events
        self.loadEventsDataFromParam()
        self.__setupNodeDeleteDisableHandler()

        # setup signals
        self.eventsWidget().setHeaderItemDeleteEvent(self.removeItemEvent)
        self.eventsWidget().setHeaderItemEnabledEvent(self._installEvents)
        self.eventsWidget().setHeaderItemTextChangedEvent(self.eventTypeChanged)

        self.eventsWidget().setHeaderItemSelectedEvent(self.updateScriptWidget)

    """ Node Disabled / Deleted """
    def __nodeDeleteDisable(self, *args, **kwargs):
        """
        When this node is deleted or disabled, this function will check
        update all of the event handlers that have been registered by the
        node associated with this event widget.
        """
        for arg in args:
            # preflight
            arg = arg[0]
            node = arg[2]['node']
            if (node == self.node().getParent()
                or node == NodegraphAPI.GetRootNode()
            ):
                # disable event handlers
                event_type = arg[0]
                if event_type == "node_setBypassed":
                    enabled = arg[2]['bypassed']
                    if not enabled:
                        self.installEvents()
                    else:
                        self.disableAllEvents()

                # delete events
                elif event_type == "node_delete":
                    self.disableAllEvents()
                    Utils.EventModule.RegisterCollapsedHandler(
                        self.__nodeDeleteDisable, "node_delete", enabled=False
                    )
                    Utils.EventModule.RegisterCollapsedHandler(
                        self.__nodeDeleteDisable, "node_setBypassed", enabled=False
                    )

    def __setupNodeDeleteDisableHandler(self):
        """
        Sets up the handlers for when a node is disabled/deleted.

        On these two handles, the event handlers will need to be disabled/enabled.
        """
        Utils.EventModule.RegisterCollapsedHandler(
            self.__nodeDeleteDisable, "node_delete", enabled=True
        )

        Utils.EventModule.RegisterCollapsedHandler(
            self.__nodeDeleteDisable, "node_setBypassed", enabled=True
        )

    """ UTILS """
    def __checkUserData(self, event_data, user_data):
        """
        Checks the user data against the event data to determine
        if the the script should be running during an event

        Args:
            event_data (dict):
            user_data (dict):

        Returns (bool):
        """
        # Get Node
        try:
            print("try")
            node_name = user_data["node"]
            print(node_name)
            node = NodegraphAPI.GetNode(node_name)
            print(node)
        except KeyError:
            print("fail")
            node = None

        for key in event_data.keys():
            event_arg_data = event_data[key]
            try:
                user_arg_data = user_data[key]
                #print(key, type(event_data[key]), event_data[key], user_arg_data)

                # Port
                # if isinstance(event_arg_data, "Port"):
                if type(event_arg_data) == "Port":
                    # output = 0
                    # input = 1
                    port_type = event_arg_data.getType()
                    if port_type == 0:
                        port = NodegraphAPI.GetOutputPort(user_arg_data)
                    else:
                        port = NodegraphAPI.GetInputPort(user_arg_data)
                    if port != event_arg_data:
                        return False

                # Param
                # if isinstance(event_arg_data, "Parameter"):
                elif type(event_arg_data) == "Parameter":
                    param = node.getParameter(user_arg_data)
                    if param != event_arg_data:
                        return False
                    pass

                # Node
                elif key == "node":
                    if node:
                        if node != event_arg_data:
                            return False
                    else:
                        return False

                # PyXmlIO

                # default data types
                else:
                    if event_arg_data != user_arg_data:
                        return False

            except KeyError:
                pass

        # passed all checks
        return True

    """ EVENTS DATA """
    def defaultEventsData(self):
        return self._default_events_data

    def generateDefaultEventTypesDict(self):
        """
        Creates a dictionary which has all of the default event data.
        """
        args_file = os.path.dirname(__file__) + '/args.json'
        #args_file = '/media/ssd01/dev/katana/KatanaWidgets/SuperTools/SimpleTool/args.json'
        with open(args_file, 'r') as args:
            self._default_events_data = json.load(args)
            # for event_type in self._events_data.keys():
            #     for arg in self._events_data[event_type]['args']:
            #         arg_name = arg['arg']
            #         arg_note = arg['note']
            #         print('-----|', arg_name, arg_note)

    def updateEventsData(self):
        """ Updates the internal _events_data attr with all of the options
        add by the user..."""
        root_item = self.eventsWidget().model().getRootItem()
        events_data = {}
        # get all children
        for child in root_item.children():
            event_name = child.columnData()["name"]
            if event_name != '<New Event>':
                events_data[event_name] = {}
                # update all args
                for arg in child.getArgsList():
                    value = child.getArg(arg)
                    if value:
                        events_data[event_name][arg] = value

                # add additional args (has to come after, or will be overwritten)
                """ Script needs to be down here to ensure that a SCRIPT attr exists """
                events_data[event_name]["filepath"] = child.getArg("filepath")
                events_data[event_name]["script"] = child.getArg("script")
                events_data[event_name]["enabled"] = child.isEnabled()

        self._events_data = events_data

    """ EVENTS """
    def updateScriptWidget(self, item, enabled):
        """ When the user changes the selected item, this will update the current script

        Args:
            item (AbstractEventListViewItem):
            enabled (bool):
        """
        if enabled:
            self.setCurrentScript(item.getArg("script"))

    def eventTypeChanged(self, item, old_value, new_value):
        """
        When the user updates the event_type by editing the views
        header.  This will set the event type on the item so that it
        can be properly updated by the dynamic display.

        If an event of that type already exists, this will reset to a null value
        to avoid double event registry in Katana.
        """
        # preflight
        root_item = self.eventsWidget().model().getRootItem()

        # duplicate event type
        for child in root_item.children():
            if child != item:
                event_name = child.columnData()["name"]
                if event_name == new_value:
                    item.setArg("name", '<New Event>')
                    return

        # invalid event type
        events_list = self.defaultEventsData()
        if new_value not in events_list:
            item.setArg("name", '<New Event>')
            return

        # update display
        else:
            item.clearArgsList()
            item.setArg("name", new_value)
            item.setArg("script", "")
            item.setArg("enabled", "")
            item.setArg("filepath", "")
            self.updateEventsData()
            self.eventsWidget().updateDelegateDisplay()

    def installEvents(self, *args):
        """
        In charge of installing / uninstalling events.

        This should be called everytime the user hits the update button
        todo
            * should this be a user input?  Or dynamically updating?
            * uninstall event filters
            * items need enabled / disabled flag to call
        """
        events_dict = self.eventsData()
        for key in events_dict:
            event_data = events_dict[key]
            enabled = event_data['enabled']
            event_type = event_data["name"]

            #if event_type in self.eventsData():
            # TODO If already registered creates warning
            try:
                Utils.EventModule.RegisterCollapsedHandler(
                    self.eventHandler, event_type, enabled=enabled
                )
            except ValueError:
                # pass if the handler exists
                pass

        # save to param
        self.saveEventsData()

    def _installEvents(self, item, enabled):
        """
        Wrapper for installEvents so that it can be used when the user
        disabled an event.
        """
        self.installEvents()

    @classmethod
    def test(cls, instance, *args, **kwargs):
        instance.eventHandler()

    def eventHandler(self, *args, **kwargs):
        """
        This is run every time Katana does an event that is registered with this
        node.  This will filter through the current events dict, and run a script
        based off of the parameters provided.  The event data is provided to this
        script so that all of the variables that are seen can be used inside of the
        script as local variables.

        TODO: preflight for args...
            do I even need this?  You could do preflight in the script?
        """
        for arg in args:
            arg = arg[0]
            event_type = arg[0]
            event_data = arg[2]

            user_event_data = self.eventsData(from_param=True)
            if event_type in list(user_event_data.keys()):
                user_data = user_event_data[str(event_type)]
                filepath = user_data['script']

                # check params
                if not self.__checkUserData(event_data, user_data): return
                if not filepath: return

                # run script
                if os.path.exists(filepath):
                    with open(filepath) as script_descriptor:
                        event_data['self'] = self.node().getParent()
                        exec(script_descriptor.read(), event_data)

    def removeItemEvent(self, item):
        item.setIsEnabled(False)
        self.installEvents()
        # TODO disable item
        # get item dict
        # disable item
        pass

    def disableAllEvents(self, events_dict=None):
        """
        Disables all of the events associated with this EventsWidget.

        If an events_dict is provided, it will disable all of the events in that
        dict, if none is provided it will use the default call to eventsData()

        Args:
            events_dict (dict): associated with eventsData call.
        """
        if events_dict:
            events_dict = json.loads(events_dict)
        else:
            events_dict = self.eventsData()

        for key in events_dict:
            event_data = events_dict[key]
            event_type = event_data["name"]
            if event_type in self.eventsData():
                Utils.EventModule.RegisterCollapsedHandler(
                    self.eventHandler, event_type, enabled=False
                )

        # update events?
        Utils.EventModule.ProcessAllEvents()

    """ WIDGETS """
    def updateEventsButton(self):
        return self._update_events_button


class EventListView(AbstractEventListView):
    def __init__(self, parent=None):
        delegate = EventListViewItemDelegate
        super(EventListView, self).__init__(parent=parent, delegate=delegate)


class EventListViewItemDelegate(AbstractEventListViewItemDelegate):
    """ Creates the popup for the ShojiMVW item"""
    def __init__(self, parent=None):
        super(EventListViewItemDelegate, self).__init__(self._getEventsList, parent=parent)
        self._parent = parent

    def _getEventsList(self, parent):
        return list(getWidgetAncestor(parent, EventWidget).defaultEventsData())


""" INPUT WIDGETS"""
class UserInputMainWidget(QWidget):
    """
    Main widgets for inputting args to the Events widget.  This is the dynamic
    widget that will be used for the shoji widget.

    Widgets
    UserInputMainWidget
        | -- QVBoxLayout
            | -- events_type_menu (EventTypeInputWidget)
            | -- script_widget (ScriptInputWidget)
            | -- dynamic_args_widget (DynamicArgsWidget)
                    | -- DynamicArgsInputWidget

    Attributes:
        events_dict (JSON): json dict containing all of the relevant information for
            each individual event type packed as:
                events_dict {
                    event_type: {
                        'note': 'description',
                        'args': [{'arg': argName, 'note': 'description']
                    },
                    event_type: { 'args': [] , 'description': 'note'},
                    "nodegraph_loadBegin" : {
                        "note" : "About to load nodes from a node graph document.",
                        "args" : []
                    },
                }

    """
    def __init__(self, parent=None):
        super(UserInputMainWidget, self).__init__(parent)
        QVBoxLayout(self)
        self.layout().setAlignment(Qt.AlignTop)

        # create scripts thingy
        self.script_widget = ScriptInputWidget(self)

        # create event type args widget
        self.dynamic_args_widget = DynamicArgsWidget(self)

        self.layout().addWidget(self.script_widget)
        self.layout().addWidget(self.dynamic_args_widget)

    def setEventType(self, event_type):
        if hasattr(self, '_item'):
            self._event_type = event_type
            self.dynamic_args_widget.event_type = event_type
            self.dynamic_args_widget.update()

    def getEventType(self):
        return self._event_type

    @staticmethod
    def updateGUI(parent, widget, item):
        """
        widget (tab widget widget)
            can get main widget with widget.getMainWidget()
        label (tab bar label)
        """
        # preflight
        if not item: return

        # set item
        events_widget = widget.getMainWidget()
        events_widget.setItem(item)

        # update event type
        event_type = item.getArg("name")

        # set script widget to label.item().getScript()
        script_location = item.getArg("script")
        events_widget.script_widget.setText(script_location)
        # TODO Update Script Text
        """
        events_widget = getWidgetAncestor(widget, EventWidget)
        python_widget = events_widget.python_widget"""
        events_widget.script_widget.resetSliderPositionToDefault()

        """dynamic_args_widget --> DynamicArgsWidget"""
        # update dynamic args widget
        events_widget.dynamic_args_widget.event_type = event_type
        events_widget.dynamic_args_widget.update()

        # set dynamic args values
        for arg in item.getArgsList():
            try:
                arg_value = item.getArg(arg)
                events_widget.dynamic_args_widget.widget_dict[arg].setText(arg_value)
            except KeyError:
                pass

    """ PROPERTIES """
    def setItem(self, item):
        self._item = item

    def item(self):
        return self._item


class DynamicArgsInputWidget(LabelledInputWidget):
    """
    One individual arg

    TODO:
        Connect the signal changes in the line edit to where I'm going
        to store this JSON date type container thingy...

    """
    def __init__(self, parent=None, name='', note='', delegate_widget=None):
        super(DynamicArgsInputWidget, self).__init__(parent, name=name, delegate_widget=delegate_widget)
        # setup args
        self.arg = name
        self.setToolTip(note)
        self.setUserFinishedEditingEvent(self.userInputEvent)
        self.setDefaultLabelLength(200)
        self.viewWidget().setDisplayMode(OverlayInputWidget.DISABLED)

    def setText(self, text):
        self.delegateWidget().setText(text)

    def text(self):
        return self.delegateWidget().text()

    def userInputEvent(self, widget, value):
        """
        When the user inputs something into the arg, this event is triggered
        updating the model item
        """
        events_widget = getWidgetAncestor(self, UserInputMainWidget)
        events_widget.item().setArg(self.arg, value)

    @property
    def arg(self):
        return self._arg

    @arg.setter
    def arg(self, arg):
        self._arg = arg


class ScriptInputWidget(DynamicArgsInputWidget):
    """
    The script input widget
    """

    FILE = 0
    SCRIPT = 1
    def __init__(self, parent=None):
        name = 'script'
        note = "Click to toggle between SCRIPT and FILE modes"
        super(ScriptInputWidget, self).__init__(parent, name=name, note=note)
        self.setMode(ScriptInputWidget.SCRIPT)
        self._toggle_mode_button = ButtonInputWidget(title="script", user_clicked_event=self.toggleMode)
        self.setViewWidget(self._toggle_mode_button)

    def mode(self):
        return self._mode

    def setMode(self, mode):
        self._mode = mode

    def toggleMode(self, widget):
        if self.mode() == ScriptInputWidget.FILE:
            self.setMode(ScriptInputWidget.SCRIPT)
            self.viewWidget().setText("script")
        elif self.mode() == ScriptInputWidget.SCRIPT:
            self.setMode(ScriptInputWidget.FILE)
            self.viewWidget().setText("file")

    def userInputEvent(self, widget, value):
        # TODO Update Python Widget text
        """
        events_widget = getWidgetAncestor(widget, EventWidget)
        python_widget = events_widget.python_widget
        """
        input_widget = getWidgetAncestor(self, UserInputMainWidget)
        input_widget.item().setArg("script", self.text())

        events_widget = getWidgetAncestor(self, EventWidget)
        events_widget.setCurrentScript(self.text())


class DynamicArgsWidget(QWidget):
    """
    The widget that contains all of the options for a specific event type.  This
    will dynamically populate when the event type changes in the parent.
    DynamicArgsWidget
        | -* DynamicArgsInputWidget
    Attributes:
        widget_dict (dict): key pair values of args to widgets
        event_type (str): the current event type that is set
    """
    def __init__(self, parent=None):
        super(DynamicArgsWidget, self).__init__(parent)
        QVBoxLayout(self)
        self.layout().setAlignment(Qt.AlignTop)
        self._widget_dict = {}
        self._event_type = ''

    def clear(self):
        """
        Removes all of the dynamic widgets
        """
        self.widget_dict = {}
        for index in reversed(range(self.layout().count())):
            widget = self.layout().itemAt(index).widget()
            if widget:
                widget.deleteLater()
                #widget.setParent(None)

    def populate(self):
        """
        Populates all of the dynamic widgets that are based on each individual
        model items args
        """
        # preflight
        try:
            events_widget = getWidgetAncestor(self, EventWidget)
            args_list = events_widget.defaultEventsData()[self.event_type]['args']
        except KeyError: return

        # update dynamic widget
        for arg in args_list:
            widget = DynamicArgsInputWidget(self, name=arg['arg'], note=arg['note'])
            self.layout().addWidget(widget)
            self.widget_dict[arg['arg']] = widget

    def update(self):
        self.clear()
        self.populate()

    """ PROPERTIES """
    @property
    def widget_dict(self):
        return self._widget_dict

    @widget_dict.setter
    def widget_dict(self, widget_dict):
        self._widget_dict = widget_dict

    @property
    def event_type(self):
        return self._event_type

    @event_type.setter
    def event_type(self, event_type):
        self._event_type = event_type


