"""
TODO:
    *   Tansu dynamic...
            Show null widget to start?
    *   Test multi select
    *   Build out uber function?
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

import sys

from qtpy.QtWidgets import (
    QApplication, QLineEdit, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QMenu
)

from qtpy.QtCore import Qt
from qtpy.QtGui import QCursor
from cgwidgets.widgets import (
    ListInputWidget, FrameInputWidget, StringInputWidget, IntInputWidget, FloatInputWidget,
    TansuModelViewWidget, TansuHeaderListView, TansuModelItem
)

from cgwidgets.utils import getWidgetAncestor, attrs


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
                | -- main_widget (TansuModelViewWidget)
                        | -- label type (EventsLabelWidget --> TansuLabelWidget)
                        | -- Dynamic Widget (UserInputMainWidget --> QWidget)
                            | -- VBox
                                    | -- events_type_menu ( EventTypeInputWidget)
                                    | -- script_widget (DynamicArgsInputWidget)
                                    | -- dynamic_args_widget (DynamicArgsWidget)
                                            | -* DynamicArgsInputWidget
    """
    def __init__(self, parent=None):
        super(EventWidget, self).__init__(parent)

        # setup attrs
        self._events_model = []

        # setup layout
        QVBoxLayout(self)
        self.new_event_button = QPushButton('new_event')
        self.new_event_button.clicked.connect(self.createNewEvent)
        self.main_widget = self.setupEventsWidgetGUI()

        self.layout().addWidget(self.new_event_button)
        self.layout().addWidget(self.main_widget)

        temp_button = QPushButton("test get event dict")
        temp_button.clicked.connect(self.getEventsDict)
        self.layout().addWidget(temp_button)

    def setupEventsWidgetGUI(self):
        """
        Sets up the main Tansu widget that is showing the events to the user
        """
        # create widget
        main_widget = TansuModelViewWidget(self)
        main_widget.model().setItemType(EventTypeModelItem)
        events_view = EventsUserInputWidget()
        main_widget.setHeaderWidget(events_view)

        # set type / position
        main_widget.setHeaderPosition(attrs.WEST)
        main_widget.setDelegateType(
            TansuModelViewWidget.DYNAMIC,
            dynamic_widget=UserInputMainWidget,
            dynamic_function=UserInputMainWidget.updateGUI
        )

        return main_widget

    def createNewEvent(self):
        """
        Creates a new event item
        """
        # create model item
        self.main_widget.insertTansuWidget(0, column_data={'name': "New Event"})

    def getEventsDict(self):
        root_item = self.main_widget.model().getRootItem()
        events_dict = {}
        # get all children
        for child in root_item.children():
            event_name = child.columnData()['name']
            events_dict[event_name] ={}
            events_dict[event_name]['script'] = child.getScript()
            events_dict[event_name]['type'] = child.getEventType()
            for arg in child.getArgsList():
                events_dict[event_name][arg] = child.getArg(arg)

        print(events_dict)
        return events_dict

    """ PROPERTIES """
    def removeEventByIndex(self, index):
        """
        Removes an event by a specified index
        """
        self.getEventsModel().pop(index)
        self.main_widget.removeTab(index)
        #self.updateAllEventItemsIndexes()
        # remove tab label / item

    def removeEvent(self, event_item):
        self.getEventsModel().remove(event_item)
        self.main_widget.removeTab(event_item.getIndex())
        #self.updateAllEventItemsIndexes()
        # remove tab label / item


class EventTypeModelItem(TansuModelItem):
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
        self.columnData()['name'] = name
        #self._name = name
        self._event_type = event_type
        self._script = script
        if not args:
            args = {}
        self._args = args
        #self['index'] = index
        self._enabled = enabled

    # def setName(self, name):
    #     self._name = name
    #
    # def getName(self):
    #     return self._name

    def setEventType(self, event_type):
        self._event_type = event_type

    def getEventType(self):
        return self._event_type

    def setScript(self, script):
        self._script = script

    def getScript(self):
        return self._script

    def setEnable(self, enabled):
        self._enabled = enabled

    def getEnable(self):
        return self._enabled

    """ args """
    def setArg(self, arg, value):
        self.columnData()[arg] = value

    def getArg(self, arg):
        return self.columnData()[arg]

    def getArgsList(self):
        return list(self.columnData().keys())

    def removeArg(self, arg):
        self.columnData().pop(arg, None)


class EventsUserInputWidget(TansuHeaderListView):
    def __init__(self, parent=None):
        super(EventsUserInputWidget, self).__init__(parent)

    # def selectionChanged(self, selected, deselected):
    #     print("selection == %s"%selected.indexes())
    #     for index in selected.indexes():
    #         print(index.internalPointer())
    #     return TansuHeaderListView.selectionChanged(self, selected, deselected)

    def setItemEnable(self, enabled):
        self.item().setEnable(enabled)

    def deleteItem(self):
        main_widget = getWidgetAncestor(self, EventWidget)
        main_widget.removeEvent(self.item())

        # reparent and overlay?
        # this thing really needs a model...
        print ("are you sure?")

    def keyPressEvent(self, event):
        index = self.getIndexUnderCursor()
        # pos = self.mapFromGlobal(QCursor.pos())
        # index = self.indexAt(pos)
        # item = index.internalPointer()

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


""" INPUT WIDGETS"""
class UserInputMainWidget(QWidget):
    """
    Main widgets for inputting args to the Events widget.  This is the dynamic
    widget that will be used for the tansu widget.

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

        self.loadEventTypesDict()

        # create events type menu
        self.events_type_menu = EventTypeInputWidget(self)
        event_types = [[item] for item in list(self.event_dict.keys())]
        self.events_type_menu.populate(event_types)

        # create scripts thingy
        self.script_widget = ScriptInputWidget(self)

        # create event type args widget
        self.dynamic_args_widget = DynamicArgsWidget(self)

        self.layout().addWidget(self.events_type_menu)
        self.layout().addWidget(self.script_widget)
        self.layout().addWidget(self.dynamic_args_widget)

    def loadEventTypesDict(self):
        """
        Right now this is just printing out all the different args and what not...
        """
        import json

        with open('args.json', 'r') as args:
            self.event_dict = json.load(args)
            for event_type in self.event_dict.keys():
                #print('')
                #print(event_type, self.event_dict[event_type]['note'])
                for arg in self.event_dict[event_type]['args']:
                    arg_name = arg['arg']
                    arg_note = arg['note']
                    #print('-----|', arg_name, arg_note)

    def setEventType(self, event_type):
        if hasattr(self, '_item'):
            self._event_type = event_type
            self.dynamic_args_widget.event_type = event_type
            self.dynamic_args_widget.update()
            self.item().setEventType(event_type)

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
        widget.group_box.setTitle(item.columnData()['name'])

        # set item
        main_widget = widget.getMainWidget()
        main_widget.setItem(item)

        # update event type
        event_type = item.getEventType()
        main_widget.events_type_menu.setText(event_type)

        # set script widget to label.item().getScript()
        script_location = item.getScript()
        main_widget.script_widget.setText(script_location)

        # update dynamic args widget
        main_widget.dynamic_args_widget.event_type = event_type
        main_widget.dynamic_args_widget.update()

        # set dynamic args values
        if main_widget.events_type_menu.text() != '':
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


class DynamicArgsInputWidget(FrameInputWidget):
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


class EventTypeInputWidget(ListInputWidget):
    """
    Drop down menu containing all of the different event types
    that the user can choose from for a specific operation
    """
    def __init__(self, parent=None):
        super(EventTypeInputWidget, self).__init__(parent)
        self.setUserFinishedEditingEvent(self.eventTypeChanged)

    def eventTypeChanged(self, widget, value):
        """
        Event that is triggered when the user changes the event type
        selection.
        """
        # preflight
        if self.previous_text == self.text(): return

        event_type = str(self.text())
        if event_type:
            event_list = list(getWidgetAncestor(self, UserInputMainWidget).event_dict.keys())
            if event_type in event_list:
                self.parent().setEventType(event_type)
                note = self.parent().event_dict[event_type]['note']
                self.setToolTip(note)
                self.previous_text = event_type
                return

        # if invalid input reset text
        self.setText(self.previous_text)


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

    def clear(self):
        self.widget_dict = {}
        for index in reversed(range(self.layout().count())):
            widget = self.layout().itemAt(index).widget()
            if widget:
                widget.setParent(None)

    def populate(self):
        try:
            args_list = self.parent().event_dict[self.event_type]['args']
        except KeyError:
            return
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


if __name__ == "__main__":
    # import sys
    # from qtpy.QtWidgets import QApplication
    # from qtpy.QtGui import QCursor
    # app = QApplication(sys.argv)
    #
    # w = TabTansuWidget()
    #
    # # stacked widget example
    # w.setType(TabTansuWidget.STACKED)
    # w.setTabBarPosition(TabTansuWidget.WEST)
    # w.setMultiSelect(True)
    # w.setMultiSelectDirection(Qt.Horizontal)
    #
    # # for x in range(3):
    # #     nw = TansuBaseWidget(w)
    # #     for b in ['a','b','c']:
    # #         nw.addWidget(QLabel(b))
    # #     w.insertTab(0, nw, str(x))
    #
    # #
    #
    #
    # # # dynamic widget example
    # dw = TabTansuDynamicWidgetExample
    # w.setType(
    #     TabTansuWidget.DYNAMIC,
    #     dynamic_widget=TabTansuDynamicWidgetExample,
    #     dynamic_function=TabTansuDynamicWidgetExample.updateGUI
    # )
    # for x in range(3):
    #     nw = QLabel(str(x))
    #     w.insertTab(0, nw, str(x))
    # # for x in range(3):
    # #     nw = TansuBaseWidget(w)
    # #     for b in ['a','b','c']:
    # #         nw.addWidget(QLabel(b))
    # #     w.insertTab(0, nw, str(x))
    #
    #
    #
    # w.resize(500,500)
    # w.show()
    # #w.setCurrentIndex(0)
    # w.setTabLabelBarToDefaultSize()
    # #w.main_widget.setSizes([200,800])
    # w.move(QCursor.pos())
    # sys.exit(app.exec_())

    app = QApplication(sys.argv)
    mw = EventWidget()
    mw.show()
    mw.move(QCursor().pos())
    sys.exit(app.exec_())
