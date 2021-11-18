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
    |        |    | -- Dynamic Widget (EventDelegateWidget --> QWidget)
    |        |        | -- VBox
    |        |            | -- events_type_menu ( EventTypeInputWidget)
    |        |            | -- script_widget (DynamicArgsInputWidget)
    |        |            | -- dynamic_args_widget (DynamicArgsWidget)
    |        |                    | -* DynamicArgsInputWidget
    |        | -- _update_events_button --> (ButtonInputWidget)
    | -- python_widget --> (PythonWidget)
        |-- VBoxLayout
            |-- QHBoxLayout
            |    |-- filepath_widget --> (ListInputWidget)
            |    |-- save_widget --> (ButtonInputWidget)
            |-- python_tab --> (PythonTab)
                    main widget to get can be gotten through pythonWidget()
TODO:
    *   EventsLabelWidget
        --> Context Menu...
                | -- enabled
                        Set text styles...
                | -- disable
                        Set text styles...
                | -- delete
                        overlay red/green widget
                            accept / cancel
        --> editing finished
                | -- update model

"""

import json
import os

from qtpy import API_NAME
from qtpy.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QMenu, QSizePolicy)
from qtpy.QtCore import Qt, QEvent
from qtpy.QtGui import QKeySequence

from Katana import Utils, NodegraphAPI, UI4

from cgwidgets.widgets import (
    ButtonInputWidget,
    ListInputWidget,
    LabelledInputWidget,
    ShojiLayout,
    ShojiModelViewWidget,
    ShojiModelItem,
    OverlayInputWidget,
)
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
        self.columnData()["previous_text"] = "<New Event>"
        self._event_type = event_type


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
                | -- Dynamic Widget (EventDelegateWidget --> QWidget)
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
            paramutils.createParamAtLocation(param + ".data", node, paramutils.STRING, initial_value="{}")
            paramutils.createParamAtLocation(param + ".scripts", node, paramutils.GROUP)

        self._param_location = param
        self._node = node

        # setup attrs
        self._events_model = []
        self._new_event_key = Qt.Key_Q
        self._events_data = {}

        # setup layout
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
        self.eventsWidget().delegateWidget().setMinimumHeight(500)

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
        self.eventsWidget().setItemType(self.eventsModelItemType())

        # setup flags
        self.eventsWidget().setHeaderItemIsDroppable(False)
        self.eventsWidget().setHeaderItemIsEnableable(True)
        self.eventsWidget().setHeaderItemIsDeletable(True)

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
    def currentScript(self):
        self.pythonWidget().filepath()

    def setCurrentScript(self, filepath):
        self.pythonWidget().setFilePath(filepath)

    """ EVENTS """
    def createNewEvent(self, widget, column_data=None):
        """Creates a new event item"""
        # create default data
        if not column_data:
            column_data = {
                "name": "<New Event>",
                "enabled": "True",
                "is_script": "True",
                "script": "",
                "filepath": "",
                "previous_text": "<New Event>"}

        # create model item
        new_index = self.eventsWidget().insertShojiWidget(0, column_data=column_data)
        item = new_index.internalPointer()
        self.eventsWidget().model().setItemEnabled(item, column_data["enabled"])

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
            return json.loads(self.paramData().getValue(0))
        # load from current GUI (unsaved) values
        else:
            self.updateEventsData()
            return self._events_data

    def setEventsData(self, events_data):
        self._events_data = events_data

    def saveEventsData(self, delete_items=[]):
        """ Saves the events data to the parameter

        Args:
            delete_items (list): of AbstractEventListViewItem that will be removed from the update
                This is needed for updates during the deletion event
        """
        # get data
        events_data = self.eventsData()

        # remove indexes that are meant for deletion
        for item in delete_items:
            if item.name() in events_data.keys():
                del events_data[item.name()]
        # set data
        new_data = json.dumps(events_data)
        if self.paramData():
            self.paramData().setValue(new_data, 0)

    # virtual
    def updateEventsData(self):
        """ Needs to be overwritten, this will be called before every
        call to eventsData()"""
        return

    # virtual
    def cacheScriptToParam(self, script):
        """ Caches the script provided to a parameter

        Args:
            script (str): plain text of current text in the Python Widget

        Note:
            This function is virtual and needs to be overridden
            """
        print("override this...")

    """ PROPERTIES """
    def node(self):
        return self._node

    def setNode(self, node):
        self._node = node

    def param(self):
        return self.node().getParameter(self.paramLocation())

    def paramData(self):
        return self.node().getParameter(self.paramLocation() + ".data")

    def paramScripts(self):
        return self.node().getParameter(self.paramLocation() + ".scripts")

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
            self.setIsEditable(True)
        else:
            self.setIsEditable(False)

    def contextMenuEvent(self, event):
        index = self.getIndexUnderCursor()
        item = index.internalPointer()

        for arg in item.getArgsList():
            print("{arg} == ".format(arg=arg), item.getArg(arg))
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


class AbstractEventListViewItemDelegateWidget(ListInputWidget):
    """ The drop down menu that pops up when the user double clicks on an item in the list view"""
    def __init__(self, parent=None):
        super(AbstractEventListViewItemDelegateWidget, self).__init__(parent)

    def showEvent(self, event):
        if self.text() == "<New Event>":
            self.setText("")
            # todo show completer...
            """ So that its a double click to enter/show, instead of a tripple click"""
            # self.completer().setCompletionMode(QCompleter.UnfilteredPopupCompletion)
            # self.completer().complete()
        return ListInputWidget.showEvent(self, event)


class AbstractEventListViewItemDelegate(AbstractDragDropModelDelegate):
    """ The delegate for the ListView that holds that creates the popup for the user.

    Args:
        populate_events_list_func (function): returns a list of strings
            that will be displayed when the user clicks on the delegate.
        """
    def __init__(self, populate_events_list_func, parent=None):
        super(AbstractEventListViewItemDelegate, self).__init__(parent)
        self._populate_events_list_func = populate_events_list_func
        self.setDelegateWidget(AbstractEventListViewItemDelegateWidget)
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
            # events_widget.eventsWidget().updateDelegateDisplay()

        delegate_widget.setUserFinishedEditingEvent(updateDisplay)

        return delegate_widget


""" PYTHON SCRIPT """
class PythonWidget(QWidget):
    SCRIPT = 0
    FILE = 1
    def __init__(self, parent=None):
        super(PythonWidget, self).__init__(parent)
        self._filepath = ""
        self._previous_filepaths = []
        self._mode = PythonWidget.SCRIPT

        self.createUI()

    def createUI(self):
        layout = QVBoxLayout(self)
        filepath_layout = QHBoxLayout()

        # create filepath widget
        self._filepath_widget = ListInputWidget(self)
        self._filepath_widget.setReadOnly(True)
        # self._filepath_widget.setCleanItemsFunction(self.showPreviousFilepaths)
        self._filepath_widget.setUserFinishedEditingEvent(self.filepathChanged)
        # self._filepath_widget.filter_results = False
        # self._filepath_widget.setDi
        # create save widget
        self._save_widget = ButtonInputWidget(title="Save", user_clicked_event=self.saveEvent)
        self._save_widget.setFixedWidth(125)

        filepath_layout.addWidget(self.filepathWidget())
        filepath_layout.addWidget(self.saveWidget())

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

    """ UTILS """
    def previousFilepaths(self):
        return self._previous_filepaths

    """ PROPERTIES """
    def filepath(self):
        return self._filepath

    def setFilePath(self, filepath):
        """ Sets the current script that is displayed

        Args:
            filepath (str): Depending on the current mode set (self.mode()),
                this can either be the name of a param located under
                eventsWidget.paramScripts().getChild(filepath)
                    OR
                a path on disk to a file. """
        self.filepathWidget().setText(filepath)
        self._filepath = filepath
        text = ""
        if self.mode() == PythonWidget.FILE:
            if filepath.endswith(".py"):
                with open(filepath, "r") as file:
                    text_list = file.readlines()
                    text = "".join(text_list)

                # append to previous paths
                if filepath not in self.previousFilepaths():
                    self.previousFilepaths().insert(0, filepath)
                    if 10 < len(self.previousFilepaths()):
                        self._previous_filepaths = self.previousFilepaths()[:10]

        elif self.mode() == PythonWidget.SCRIPT:
            event_widget = getWidgetAncestor(self, AbstractEventWidget)
            try:
                text = event_widget.paramScripts().getChild(filepath).getValue(0)
            except:
                # no param found
                pass

        # update text
        self.commandWidget().setPlainText(text)

    def getCurrentScript(self):
        return self.commandWidget().toPlainText()

    def mode(self):
        return self._mode

    def setMode(self, mode):
        self._mode = mode

    """ EVENTS """
    def saveEvent(self, widget):
        """ Saves the current IDE text to the current file"""
        text = self.getCurrentScript()
        if self.mode() == PythonWidget.FILE:
            with open(self.filepath(), "w") as file:
                file.write(text)

        elif self.mode() == PythonWidget.SCRIPT:
            events_widget = getWidgetAncestor(self, AbstractEventWidget)
            events_widget.cacheScriptToParam(text)

    def filepathChanged(self, widget, filepath):
        """ Sets the IDE text to the filepath provided

        Args:
            filepath (str): path on disk to file OR param name
        """
        self.setFilePath(filepath)

    def eventFilter(self, obj, event, *args, **kwargs):
        if event.type() == QEvent.Enter:
            obj.setFocus()
        # for some reason the leave/re-enter doesn't actually set the focus...
        # if event.type() == QEvent.HoverEnter:
        #     print('hover enter')
        #
        # if event.type() == QEvent.HoverLeave:
        #     print('hover leave')
        # if event.type() == QEvent.Leave:
        #     print('leave')
        #    #obj.clearFocus()

        return False

    def showPreviousFilepaths(self):
        if self.mode() == PythonWidget.FILE:
            return [[filepath] for filepath in self.previousFilepaths()]
        else:
            return []

    """ WIDGETS """
    def filepathWidget(self):
        return self._filepath_widget

    def saveWidget(self):
        return self._save_widget

    def pythonTabWidget(self):
        return self._python_tab_widget

    def commandWidget(self):
        return self._command_widget


class AbstractScriptInputWidget(LabelledInputWidget):
    """
    The script input widget
    """
    def __init__(self, parent=None, delegate_widget=None):
        name = 'script'

        super(AbstractScriptInputWidget, self).__init__(parent, name=name, delegate_widget=delegate_widget)

        self.setDefaultLabelLength(200)
        self._toggle_mode_button = ButtonInputWidget(title="script", user_clicked_event=self.toggleMode)
        self.setViewWidget(self._toggle_mode_button)
        self._mode = PythonWidget.SCRIPT

        _delegate_widget = ListInputWidget()
        self.setDelegateWidget(_delegate_widget)
        _delegate_widget.setCleanItemsFunction(self.getAllScripts)
        _delegate_widget.setUserFinishedEditingEvent(self.userInputEvent)
        _delegate_widget.filter_results = False

        # set tooltips
        self.viewWidget().setToolTip("Click to toggle between SCRIPT and FILE modes")
        self.delegateWidget().setToolTip("The name/location of the script/filepath")

    """ EVENTS """
    def userInputEvent(self, widget, value):
        # TODO Update Python Widget text
        """
        events_widget = getWidgetAncestor(widget, EventWidget)
        python_widget = events_widget.python_widget
        """
        events_widget = getWidgetAncestor(self, AbstractEventWidget)

        # preflight
        if value == "": return

        if self.mode() == PythonWidget.FILE:
            self._filepath = self.text()
            self.setFilepath(self.text())

        elif self.mode() == PythonWidget.SCRIPT:
            # preflight
            if self.text().rstrip("") != "":
                if self.text()[0].isdigit():
                    text = "_" + self.text()[1:]
                    self.setText(text)
                    return

            self._script = self.text()
            # create param
            paramutils.createParamAtLocation(
                events_widget.paramLocation() + ".scripts." + self.text(),
                events_widget.node(),
                paramutils.STRING,
                initial_value=""
            )

            # set
            self.setScript(self.text())

    # VIRTUAL
    def setFilepath(self, filepath):
        """ Needs to be overridden to set the filepath"""
        pass

    # VIRTUAL
    def setScript(self, script):
        pass

    """ UTILS """
    def getAllScripts(self):
        if self.mode() == PythonWidget.SCRIPT:
            events_widget = getWidgetAncestor(self, AbstractEventWidget)
            return [[child.getName()] for child in events_widget.paramScripts().getChildren()]
        else:
            return []

    """ PROPERTIES """
    def text(self):
        return self.delegateWidget().text()

    def setText(self, text):
        self.delegateWidget().setText(text)

    def mode(self):
        return self._mode

    def setMode(self, mode):
        # set mode
        self._mode = mode
        events_widget = getWidgetAncestor(self, AbstractEventWidget)
        events_widget.pythonWidget().setMode(mode)

        # update display / item data
        if self.mode() == PythonWidget.FILE:
            self.viewWidget().setText("file")

        elif self.mode() == PythonWidget.SCRIPT:
            self.viewWidget().setText("script")

        # custom functionality
        self._setMode(self.mode())

    # VIRTUAL
    def _setMode(self, mode):
        """ Needs to be overwritten """
        pass

    def toggleMode(self, *args):
        if self.mode() == PythonWidget.FILE:
            self.setMode(PythonWidget.SCRIPT)
        elif self.mode() == PythonWidget.SCRIPT:
            self.setMode(PythonWidget.FILE)

        # install events
        """ Note: this will not install for the GSVManager, as the GSVManager
        has all of its events controlled by a single handler"""
        events_widget = getWidgetAncestor(self, AbstractEventWidget)
        if hasattr(events_widget, "installEvents"):
            events_widget.installEvents()


""" GLOBAL EVENTS"""
class EventInterface(object):
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

            try:
                Utils.EventModule.RegisterCollapsedHandler(
                    self.eventHandler, event_type, enabled=enabled
                )
            except ValueError:
                # pass if the handler exists
                pass

        # save to param
        self.saveEventsData()

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

    def eventHandler(self, *args, **kwargs):
        """
        This is run every time Katana does an event that is registered with this
        node.  This will filter through the current events dict, and run a script
        based off of the parameters provided.  The event data is provided to this
        script so that all of the variables that are seen can be used inside of the
        script as local variables.

        Duplicate code to SimpleTools --> node --> eventHandler
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
                filepath = user_data["filepath"]

                # check params
                if not EventInterface.checkUserData(event_data, user_data): return
                #event_data["self"] = self.node().parent()
                # run script
                if user_data["is_script"]:
                    script = self.paramScripts().getChild(user_data["script"]).getValue(0)
                    exec(script, globals(), event_data)
                # run as filepath
                elif not user_data["is_script"]:
                    if os.path.exists(filepath):
                        with open(filepath) as script_descriptor:
                            event_data['self'] = self.node().getParent()
                            exec(script_descriptor.read(), event_data)

    @staticmethod
    def checkUserData(event_data, user_data):
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
                | -- Dynamic Widget (EventDelegateWidget --> QWidget)
                    | -- VBox
                        | -- events_type_menu ( EventTypeInputWidget)
                        | -- script_widget (DynamicArgsInputWidget)
                        | -- dynamic_args_widget (DynamicArgsWidget)
                                | -* DynamicArgsInputWidget
    """
    def __init__(self, parent=None, node=None, param="events_data"):
        delegate_widget_type = EventDelegateWidget
        events_list_view = EventListView

        super(EventWidget, self).__init__(
            delegate_widget_type,
            events_list_view=events_list_view,
            parent=parent,
            node=node,
            param=param)

        self.generateDefaultEventTypesDict()

        # load events
        self.loadEventsDataFromParam()
        self.__setupNodeDeleteDisableHandler()

        # setup signals
        self.eventsWidget().setHeaderItemDeleteEvent(self.removeItemEvent)
        self.eventsWidget().setHeaderItemEnabledEvent(self.installEvents)
        self.eventsWidget().setHeaderItemTextChangedEvent(self.eventTypeChanged)

    """ Node Disabled / Deleted """
    def __nodeDeleteDisable(self, *args, **kwargs):
        """ Delete/Disable the node (Root/SimpleTool)

        When this node is deleted or disabled, this function will check
        update all of the event handlers that have been registered by the
        node associated with this event widget.
        """
        for arg in args:
            # preflight
            arg = arg[0]
            node = arg[2]['node']
            if node == self.node() or node == NodegraphAPI.GetRootNode():
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

    """ EVENTS DATA """
    def defaultEventsData(self):
        return self._default_events_data

    def generateDefaultEventTypesDict(self):
        """
        Creates a dictionary which has all of the default event data.
        """
        args_file = os.path.dirname(__file__) + '/args.json'
        with open(args_file, 'rb') as file:
            self._default_events_data = json.loads(file.read())

    def loadEventsDataFromParam(self):
        """ Loads all of the events data from the param and resets the current events data"""
        # clear model
        self.eventsWidget().clearModel()

        # get data
        try:
            json_data = json.loads(self.paramData().getValue(0))
        except ValueError:
            return
        except AttributeError:
            return

        # create new events
        for event_type in json_data:
            event = json_data[str(event_type)]
            self.createNewEvent(None, column_data=event)

        # set data
        self.setEventsData(json_data)

    def updateEventsData(self):
        """ Updates the internal _events_data attr with the user data"""
        root_item = self.eventsWidget().model().rootItem()
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
                events_data[event_name]["is_script"] = child.getArg("is_script")
                events_data[event_name]["enabled"] = child.isEnabled()

        self._events_data = events_data

    """ EVENTS """
    def removeItemEvent(self, item):
        item.setIsEnabled(False)
        self.installEvents()
        self.saveEventsData(delete_items=[item])

    def cacheScriptToParam(self, script):
        """ This will cache the script to a local value

        Note: The script must be a valid file in order for it to cache
        """
        # update script
        selected_indexes = self.eventsWidget().getAllSelectedIndexes()
        if 0 < len(selected_indexes):
            item = selected_indexes[0].internalPointer()
            event_type = item.getArg("name")

            if event_type in self.defaultEventsData():
                self.paramScripts().getChild(item.getArg("script")).setValue(str(script), 0)

                # save
                self.saveEventsData()

    def eventTypeChanged(self, item, old_value, new_value):
        """
        When the user updates the event_type by editing the views
        header.  This will set the event type on the item so that it
        can be properly updated by the dynamic display.

        If an event of that type already exists, this will reset to a null value
        to avoid double event registry in Katana.
        """
        # preflight
        root_item = self.eventsWidget().model().rootItem()

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
            item.setArg("name", item.getArg("previous_text"))
            return

        # update display
        else:
            item.clearArgsList()
            item.setArg("name", new_value)
            item.setArg("previous_text", new_value)
            item.setArg("enabled", "")
            item.setArg("filepath", "")
            item.setArg("is_script", "")
            param_location = self.paramLocation() + ".scripts." + new_value
            paramutils.createParamAtLocation(param_location, self.node(), paramutils.STRING, initial_value="")
            item.setArg("script", new_value)

            self.updateEventsData()
            self.eventsWidget().updateDelegateDisplay()
            self.installEvents()


class GlobalEventWidget(EventWidget, EventInterface):
    def __init__(self, parent=None, node=None, param="events_data"):
        super(GlobalEventWidget, self).__init__(parent, node, param)
        if API_NAME == "PySide2":
            EventInterface.__init__(self)

    # def removeItemEvent(self, item):
    #     item.setIsEnabled(False)
    #     self.installEvents()
    #     self.saveEventsData(delete_items=[item])


class SimpleToolEventWidget(EventWidget):
    def __init__(self, parent=None, node=None, param="events_data"):
        super(SimpleToolEventWidget, self).__init__(parent, node, param)

    def installEvents(self, *args):
        """
        In charge of installing / uninstalling events.

        This should be called everytime the user hits the update button
        todo
            * should this be a user input?  Or dynamically updating?
            * uninstall event filters
            * items need enabled / disabled flag to call
        """
        # save to param
        self.updateEventsData()
        self.saveEventsData()
        self.node().installEvents()

    # def removeItemEvent(self, item):
    #     item.setIsEnabled(False)
    #     self.installEvents()
    #     self.saveEventsData(delete_items=[item])

    def disableAllEvents(self, events_dict=None):
        """
        Disables all of the events associated with this EventsWidget.

        If an events_dict is provided, it will disable all of the events in that
        dict, if none is provided it will use the default call to eventsData()

        Args:
            events_dict (dict): associated with eventsData call.
        """
        self.updateEventsData()
        self.saveEventsData()
        self.node().disableAllEvents(events_dict)


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


class EventDelegateWidget(QWidget):
    """
    Main widgets for inputting args to the Events widget.  This is the dynamic
    widget that will be used for the shoji widget.

    Widgets
    EventDelegateWidget
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
        super(EventDelegateWidget, self).__init__(parent)
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

        events_widget = getWidgetAncestor(widget, EventWidget)
        # set item
        this = widget.getMainWidget()
        this.setItem(item)

        # update event type
        event_type = item.getArg("name")

        # update if script
        if item.getArg("is_script"):
            this.script_widget.setMode(PythonWidget.SCRIPT)
            events_widget.pythonWidget().setMode(PythonWidget.SCRIPT)
            events_widget.setCurrentScript(item.getArg("script"))

            # this.script_widget.setText(item.getArg("script"))
            # try:
            #     script_text = events_widget.paramScripts().getChild(item.getArg("script")).getValue(0)
            #     #script_text = events_widget.node().getParameter(item.getArg("script")).getValue(0)
            #     events_widget.pythonWidget().commandWidget().setText(script_text)
            # except AttributeError:
            #     pass

        # update if file
        elif not item.getArg("is_script"):
            this.script_widget.setMode(PythonWidget.FILE)
            events_widget.pythonWidget().setMode(PythonWidget.FILE)
            this.script_widget.setText(item.getArg("filepath"))

        # TODO Update Script Text
        """
        this = getWidgetAncestor(widget, EventWidget)
        python_widget = this.python_widget"""
        this.script_widget.resetSliderPositionToDefault()

        """dynamic_args_widget --> DynamicArgsWidget"""
        # update dynamic args widget
        this.dynamic_args_widget.event_type = event_type
        this.dynamic_args_widget.update()

        # set dynamic args values
        for arg in item.getArgsList():
            try:
                arg_value = item.getArg(arg)
                this.dynamic_args_widget.widget_dict[arg].setText(arg_value)
            except KeyError:
                pass

    """ PROPERTIES """
    def setItem(self, item):
        self._item = item

    def item(self):
        return self._item


""" INPUT WIDGETS"""
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
        """ When the user finishes editing, update the param/item data"""
        # update item
        events_delegate = getWidgetAncestor(self, EventDelegateWidget)
        events_delegate.item().setArg(self.arg, value)

        # update param
        events_widget = getWidgetAncestor(self, AbstractEventWidget)
        events_widget.saveEventsData()

    @property
    def arg(self):
        return self._arg

    @arg.setter
    def arg(self, arg):
        self._arg = arg


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


class ScriptInputWidget(AbstractScriptInputWidget):
    def __init__(self, parent=None, name='', delegate_widget=None):
        super(ScriptInputWidget, self).__init__(parent, delegate_widget=delegate_widget)
        self.arg = name
        self.setDefaultLabelLength(200)

    def _updatePythonWidgetPath(self):
        events_widget = getWidgetAncestor(self, AbstractEventWidget)
        events_widget.setCurrentScript(self.text())
        script_text = events_widget.paramScripts().getChild(self.text()).getValue(0)
        events_widget.pythonWidget().commandWidget().setText(script_text)

    def setFilepath(self, filepath):
        input_widget = getWidgetAncestor(self, EventDelegateWidget)
        input_widget.item().setArg("filepath", self.text())

        # update python widget
        self._updatePythonWidgetPath()

    def setScript(self, script):
        input_widget = getWidgetAncestor(self, EventDelegateWidget)
        input_widget.item().setArg("script", self.text())

        # update python widget
        self._updatePythonWidgetPath()

    def _setMode(self, mode):
        events_widget = getWidgetAncestor(self, AbstractEventWidget)
        input_widget = getWidgetAncestor(self, EventDelegateWidget)

        if self.mode() == PythonWidget.FILE:
            events_widget.pythonWidget().setFilePath(input_widget.item().getArg("filepath"))
            input_widget.item().setArg("is_script", False)
            self.setText(input_widget.item().getArg("filepath"))

        elif self.mode() == PythonWidget.SCRIPT:
            events_widget.pythonWidget().setFilePath(input_widget.item().getArg("script"))
            input_widget.item().setArg("is_script", True)
            self.setText(input_widget.item().getArg("script"))

        events_widget.updateEventsData()

    @property
    def arg(self):
        return self._arg

    @arg.setter
    def arg(self, arg):
        self._arg = arg