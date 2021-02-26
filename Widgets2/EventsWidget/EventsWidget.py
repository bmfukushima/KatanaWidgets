"""
Hierarchy:
    EventWidget --> (QWidget)
        | -- VBox
            | -- new_event_button --> (QPushButton)
            | -- main_widget --> (ShojiModelViewWidget)
                | -- label type (EventsLabelWidget --> ShojiLabelWidget)
                | -- Dynamic Widget (UserInputMainWidget --> QWidget)
                    | -- VBox
                        | -- events_type_menu ( EventTypeInputWidget)
                        | -- script_widget (DynamicArgsInputWidget)
                        | -- dynamic_args_widget (DynamicArgsWidget)
                                | -* DynamicArgsInputWidget
TODO:
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

import sys, os, json

from qtpy.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QMenu)
from qtpy.QtCore import Qt
from qtpy.QtGui import QCursor, QKeySequence

from cgwidgets.widgets import (
    ListInputWidget, LabelledInputWidget, StringInputWidget, ButtonInputWidget,
    ShojiModelViewWidget, ShojiModelItem)
from cgwidgets.views import AbstractDragDropListView, AbstractDragDropModelDelegate
from cgwidgets.utils import getWidgetAncestor, attrs


from Katana import Utils, NodegraphAPI


class EventWidget(QWidget):
    """
    The main widget for setting up the events triggers on the node.

    Attributes:
        events_model (list): of EventTypeModelItem's.  This list is the model
            for all of the events.

            All of the tab labels/widgets will automatically call back to this list for
            updating.

    Widgets:
        | -- VBox
            | -- new_event_button (PushButton)
            | -- main_widget (ShojiModelViewWidget)
                | -- label type (EventsLabelWidget --> ShojiLabelWidget)
                | -- Dynamic Widget (UserInputMainWidget --> QWidget)
                    | -- VBox
                        | -- events_type_menu ( EventTypeInputWidget)
                        | -- script_widget (DynamicArgsInputWidget)
                        | -- dynamic_args_widget (DynamicArgsWidget)
                                | -* DynamicArgsInputWidget
    """
    def __init__(self, parent=None, node=None):
        super(EventWidget, self).__init__(parent)
        self.generateDefaultEventTypesDict()
        if not node:
            node = NodegraphAPI.GetRootNode()
        if not node.getParameter("events_data"):
            node.getParameters().createChildString("events_data", "")
        self.main_node = node

        # setup attrs
        self._events_model = []
        self._new_event_key = Qt.Key_Q
        # setup layout
        QVBoxLayout(self)

        # create main widget
        self.main_widget = self.setupEventsWidgetGUI()
        self.layout().addWidget(self.main_widget)

        # create new event button
        new_event_button_title = 'New Event ({key})'.format(key=QKeySequence(self._new_event_key).toString())
        self.new_event_button = ButtonInputWidget(self, title=new_event_button_title, is_toggleable=False, user_clicked_event=self.createNewEvent)

        self.main_widget.addHeaderDelegateWidget(
            [self._new_event_key], self.new_event_button)
        self.new_event_button.show()

        # create update button
        self.update_events_button = ButtonInputWidget(self, title="Update Events", is_toggleable=False, user_clicked_event=self.updateEvents)
        self.layout().addWidget(self.update_events_button)

        # load events
        self.loadEventsDataFromJSON()
        self.__setupNodeDeleteDisableHandler()

        # set up stretch
        from qtpy.QtWidgets import QSizePolicy
        self.main_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        self.update_events_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

    def setupEventsWidgetGUI(self):
        """
        Sets up the main Shoji widget that is showing the events to the user
        """
        # create widget
        main_widget = ShojiModelViewWidget(self)

        # setup header
        events_view = EventsUserInputWidget(self)
        main_widget.setHeaderViewWidget(events_view)
        main_widget.setHeaderData(['event_type'])

        # setup custom item type
        main_widget.model().setItemType(EventTypeModelItem)

        # setup flags
        main_widget.setHeaderItemIsDropEnabled(False)
        main_widget.setHeaderItemIsEnableable(True)
        main_widget.setHeaderItemIsDeleteEnabled(True)

        # setup signals
        main_widget.setHeaderItemDeleteEvent(self.removeItemEvent)
        main_widget.setHeaderItemEnabledEvent(self._updateEvents)
        main_widget.setHeaderItemTextChangedEvent(self.eventTypeChanged)

        # set type / position
        main_widget.setHeaderPosition(attrs.WEST, attrs.SOUTH)
        main_widget.setDelegateType(
            ShojiModelViewWidget.DYNAMIC,
            dynamic_widget=UserInputMainWidget,
            dynamic_function=UserInputMainWidget.updateGUI
        )
        main_widget.setHeaderDefaultLength(250)

        return main_widget

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
            if (node == self.main_node.getParent()
                or node == NodegraphAPI.GetRootNode()
            ):
                # disable event handlers
                event_type = arg[0]
                if event_type == "node_setBypassed":
                    enabled = arg[2]['bypassed']
                    if not enabled:
                        self.updateEvents()
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
            node_name = user_data["node"]
            node = NodegraphAPI.GetNode(node_name)
        except KeyError:
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

    """ EVENTS DICT """
    def getUserEventsDict(self):
        """
        Returns the dictionary of events data that was set up by the user.
        This is also stored in the parameter on the main node as "events_data"
        """
        root_item = self.main_widget.model().getRootItem()
        events_dict = {}
        # get all children
        for child in root_item.children():
            event_name = child.columnData()['event_type']
            if event_name != '<New Event>':
                events_dict[event_name] = {}
                # update all args
                for arg in child.getArgsList():
                    value = child.getArg(arg)
                    if value:
                        events_dict[event_name][arg] = value

                # add additional args (has to come after, or will be overwritten)
                events_dict[event_name]['script'] = child.getScript()
                events_dict[event_name]['enabled'] = child.isEnabled()

        return events_dict

    def generateDefaultEventTypesDict(self):
        """
        Creates a dictionary which has all of the default event data.
        """
        args_file = os.path.dirname(__file__) + '/args.json'
        #args_file = '/media/ssd01/dev/katana/KatanaWidgets/SuperTools/SimpleTool/args.json'
        with open(args_file, 'r') as args:
            self.event_dict = json.load(args)
            for event_type in self.event_dict.keys():
                for arg in self.event_dict[event_type]['args']:
                    arg_name = arg['arg']
                    arg_note = arg['note']
                    #print('-----|', arg_name, arg_note)

    def defaultEventTypes(self):
        """
        returns
        """
        return self.event_dict

    def saveEventsDataToJSON(self):
        events_dict = self.getUserEventsDict()
        events_string = json.dumps(events_dict)
        self.main_node.getParameter("events_data").setValue(events_string, 0)

    def loadEventsDataFromJSON(self):
        # TODO clear all items
        try:
            json_data = json.loads(self.main_node.getParameter("events_data").getValue(0))
        except ValueError:
            return

        for event_type in json_data:
            event = json_data[str(event_type)]
            self.createNewEvent(None, column_data=event)

    """ EVENTS """
    def eventTypeChanged(self, item, old_value, new_value):
        """
        When the user updates the event_type by editing the views
        header.  This will set the event type on the item so that it
        can be properly updated by the dynamic display.

        If an event of that type already exists, this will reset to a null value
        to avoid double event registry in Katana.
        """
        # preflight
        root_item = self.main_widget.model().getRootItem()

        # duplicate event type
        for child in root_item.children():
            if child != item:
                event_name = child.columnData()['event_type']
                if event_name == new_value:
                    item.setArg('event_type', '<New Event>')
                    return

        # invalid event type
        events_list = self.defaultEventTypes()
        if new_value not in events_list:
            item.setArg('event_type', '<New Event>')
            return

        # update display
        else:
            item.clearArgsList()
            item.setArg('event_type', new_value)
            self.main_widget.updateDelegateDisplay()

    def createNewEvent(self, widget, column_data=None):
        """
        Creates a new event item
        """
        if not column_data:
            column_data = {'event_type': "<New Event>"}
        # create model item
        new_index = self.main_widget.insertShojiWidget(0, column_data=column_data)
        item = new_index.internalPointer()

        # update script / enabled args
        # TODO get defaults - these should probably be moved to args?
        try:
            item.setScript(column_data['script'])
        except KeyError:
            pass
        try:
            self.main_widget.model().setItemEnabled(item, column_data['enabled'])
        except KeyError:
            pass

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

            user_event_data = self.getUserEventsDict()
            if event_type in list(user_event_data.keys()):
                user_data = user_event_data[str(event_type)]
                filepath = user_data['script']

                # check params
                if not self.__checkUserData(event_data, user_data): return
                if not filepath: return

                # run script
                if os.path.exists(filepath):
                    with open(filepath) as script_descriptor:
                        event_data['self'] = self.main_node.getParent()
                        exec(script_descriptor.read(), event_data)

    def removeItemEvent(self, item):
        item.setIsEnabled(False)
        self.updateEvents()
        # TODO disable item
        # get item dict
        # disable item
        pass

    def disableAllEvents(self, events_dict=None):
        """
        Disables all of the events associated with this EventsWidget.

        If an events_dict is provided, it will disable all of the events in that
        dict, if none is provided it will use the default call to getUserEventsDict()

        Args:
            events_dict (dict): associated with getUserEventsDict call.
        """
        if events_dict:
            events_dict = json.loads(events_dict)
        else:
            events_dict = self.getUserEventsDict()

        for key in events_dict:
            event_data = events_dict[key]
            event_type = event_data['event_type']

            if event_type in self.defaultEventTypes():
                Utils.EventModule.RegisterCollapsedHandler(
                    self.eventHandler, event_type, enabled=False
                )

        # update events?
        Utils.EventModule.ProcessAllEvents()

    def updateEvents(self, *args):
        """
        In charge of installing / uninstalling events.

        This should be called everytime the user hits the update button
        todo
            * should this be a user input?  Or dynamically updating?
            * uninstall event filters
            * items need enabled / disabled flag to call
        """
        events_dict = self.getUserEventsDict()
        for key in events_dict:
            event_data = events_dict[key]
            enabled = event_data['enabled']
            event_type = event_data['event_type']
            if event_type in self.defaultEventTypes():
                #print('installing event... {event_name} --> {event_type}'.format(event_name=key, event_type=event_type))
                # TODO If already registered creates warning
                try:
                    Utils.EventModule.RegisterCollapsedHandler(
                        self.eventHandler, event_type, enabled=enabled
                    )
                except ValueError:
                    # pass if the handler exists
                    pass

        # save to param
        self.saveEventsDataToJSON()

    def _updateEvents(self, item, enabled):
        """
        Wrapper for updateEvents so that it can be used when the user
        disabled an event.
        """
        self.updateEvents()


class EventTypeModelItem(ShojiModelItem):
    """
    name (str): name given to this event by the user
    event_type (str): katana event type
    script (path): path on disk to .py file to run as script
    args (dict): dictionary of all the args
    index (int): current index that this item is holding in the model
    enabled (bool): If this event should be enabledd/disabled
    """
    def __init__(self, name=None, event_type=None, script=None, args={}, index=0, enabled=True):
        super(EventTypeModelItem, self).__init__(name)
        self.columnData()['event_type'] = name
        #self._name = name
        self._event_type = event_type
        self._script = script
        if not args:
            args = {}
        self._args = args

    def setScript(self, script):
        self._script = script

    def getScript(self):
        return self._script

    """ args """
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


class EventsUserInputWidget(AbstractDragDropListView):
    def __init__(self, parent=None):
        super(EventsUserInputWidget, self).__init__(parent)
        delegate = EventTypeDelegate(self)
        self.setItemDelegate(delegate)

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

    # todo: Hotkey for new event creation...
    # currently overrides the delete handlers and what not... not sure why.. =\
    # def keyPressEvent(self, event):
    #     main_widget = getWidgetAncestor(self, EventWidget)
    #     if event.key() == main_widget._new_event_key:
    #         main_widget.createNewEvent()
    #     return AbstractDragDropListView.keyPressEvent(self, event)

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
        self.generateDefaultEventTypesDict()

        # create scripts thingy
        self.script_widget = ScriptInputWidget(self)

        # create event type args widget
        self.dynamic_args_widget = DynamicArgsWidget(self)

        self.layout().addWidget(self.script_widget)
        self.layout().addWidget(self.dynamic_args_widget)

    def generateDefaultEventTypesDict(self):
        """
        Sets up the event_dict to be usd as global list of possible events
        that the user can create.
        """
        # todo Qt Legacy?
        args_file = os.path.dirname(__file__) + '/args.json'
        with open(args_file, 'r') as args:
            self.event_dict = json.load(args)
            for event_type in self.event_dict.keys():
                for arg in self.event_dict[event_type]['args']:
                    arg_name = arg['arg']
                    arg_note = arg['note']
                    #print('-----|', arg_name, arg_note)

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

        # set title
        # for some reason this isnt necessary...
        #widget.group_box.setTitle(item.columnData()['event_type'])

        # set item
        main_widget = widget.getMainWidget()
        main_widget.setItem(item)

        # # update event type
        #event_type = item.getEventType()
        event_type = item.getArg('event_type')
        # main_widget.events_type_menu.setText(event_type)

        # set script widget to label.item().getScript()
        script_location = item.getScript()
        main_widget.script_widget.setText(script_location)

        # update dynamic args widget
        main_widget.dynamic_args_widget.event_type = event_type
        main_widget.dynamic_args_widget.update()

        # set dynamic args values
        #if main_widget.events_type_menu.text() != '':
        for arg in item.getArgsList():
            try:
                arg_value = item.getArg(arg)
                main_widget.dynamic_args_widget.widget_dict[arg].setText(arg_value)
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
    def __init__(self, parent=None, name='', note='', widget_type=StringInputWidget):
        super(DynamicArgsInputWidget, self).__init__(parent, name=name, widget_type=StringInputWidget)
        # setup args
        self.arg = name
        self.setToolTip(note)
        self.setUserFinishedEditingEvent(self.userInputEvent)

    def setText(self, text):
        self.getInputWidget().setText(text)

    def text(self):
        return self.getInputWidget().text()

    def userInputEvent(self, widget, value):
        """
        When the user inputs something into the arg, this event is triggered
        updating the model item
        """
        main_widget = getWidgetAncestor(self, UserInputMainWidget)
        main_widget.item().setArg(self.arg, value)

    @property
    def arg(self):
        return self._arg

    @arg.setter
    def arg(self, arg):
        self._arg = arg


class EventTypeDelegate(AbstractDragDropModelDelegate):
    def __init__(self, parent=None):
        super(EventTypeDelegate, self).__init__(parent)
        self.setDelegateWidget(ListInputWidget)
        self._parent = parent

    def createEditor(self, parent, option, index):
        delegate_widget = self.delegateWidget(parent)
        # populate events
        event_list = list(getWidgetAncestor(parent, EventWidget).defaultEventTypes())
        delegate_widget.populate([[item] for item in sorted(event_list)])

        # set update trigger
        def updateDisplay(widget, value):
            main_widget = getWidgetAncestor(self._parent, EventWidget)
            main_widget.main_widget.updateDelegateDisplay()

        delegate_widget.setUserFinishedEditingEvent(updateDisplay)
        return delegate_widget


class ScriptInputWidget(DynamicArgsInputWidget):
    """
    The script input widget
    """
    def __init__(self, parent=None):
        name = 'script'
        note = "path on disk to the script you want to run"
        super(ScriptInputWidget, self).__init__(parent, name=name, note=note)

    def userInputEvent(self, widget, value):
        main_widget = getWidgetAncestor(self, UserInputMainWidget)
        main_widget.item().setScript(self.text())


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
                widget.setParent(None)

    def populate(self):
        """
        Populates all of the dynamic widgets that are based on each individual
        model items args
        """
        # preflight
        try: args_list = self.parent().event_dict[self.event_type]['args']
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
