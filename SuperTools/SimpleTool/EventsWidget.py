"""
TODO:
    *    How to handle script widget?
            same as args?
    *   EventType change
            errors out if invalid selection?
    *   EventsLabelWidget
        --> Context Menu...
                | -- enable
                | -- disable
                | -- delete
        --> editing finished
                | -- update model
"""

import sys

from qtpy.QtWidgets import (
    QApplication, QLineEdit, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton
)

from qtpy.QtCore import Qt
from qtpy.QtGui import QCursor
from cgwidgets.widgets import ListInputWidget, TabLabelWidget, TabTansuWidget

from cgwidgets.utils import getWidgetAncestor


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
                | -- main_widget (TabTansuWidget)
                        | -- label type (EventsLabelWidget --> TansuLabelWidget)
                        | -- Dynamic Widget (UserInputMainWidget --> QWidget)
                            | -- VBox
                                    | -- events_type_menu ( EventTypeInputWidget)
                                    | -- script_widget (ArgInputWidget)
                                    | -- dynamic_args_widget (ArgsInputMainWidget)
                                            | -* ArgInputWidget
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

    def setupEventsWidgetGUI(self):
        """
        Sets up the main Tansu widget that is showing the events to the user
        """
        main_widget = TabTansuWidget(self)
        main_widget.setTabLabelInstanceType(EventsLabelWidget)
        main_widget.setTabBarPosition(TabTansuWidget.WEST)
        main_widget.setType(
            TabTansuWidget.DYNAMIC,
            dynamic_widget=UserInputMainWidget,
            dynamic_function=UserInputMainWidget.updateGUI
        )

        return main_widget

    def createNewEvent(self):
        """
        Creates a new event item
        """
        # create model item
        new_event_item = EventTypeModelItem()
        self.insertEventIntoEventsModel(new_event_item)

        # create new tab label/widget
        tab_label = self.main_widget.insertTab(0, "New Event")
        tab_label.setItem(new_event_item)

    """ PROPERTIES """
    def getEventsModel(self):
        return self._events_model

    def setEventsModel(self, _events_model):
        return self._events_model

    def insertEventIntoEventsModel(self, _event, index=0):
        """
        Inserts a new event into the model

        event (EventTypeModelItem): The new event to be added
        index (int): the index to insert the new item into the model
        """
        self.getEventsModel().insert(index, _event)
        self.updateAllEventItemsIndexes()

    def removeEventByIndex(self, index):
        """
        Removes an event by a specified index
        """
        self.getEventsModel().pop(index)
        self.main_widget.removeTab(index)
        self.updateAllEventItemsIndexes()
        # remove tab label / item

    def removeEvent(self, event_item):
        self.getEventsModel().remove(event_item)
        self.main_widget.removeTab(event_item.index())
        self.updateAllEventItemsIndexes()
        # remove tab label / item

    def updateAllEventItemsIndexes(self):
        """
        Updates all of the event indexes to the correct index in the model
        """
        for index, event_item in enumerate(self.getEventsModel()):
            event_item.index = index


class EventsLabelWidget(TabLabelWidget):
    """
    The label that is displayed back to the user to be selected to show off
    this events arguments
    """
    def __init__(self, parent, text, index):
        super(EventsLabelWidget, self).__init__(parent, text, index)
        self.setReadOnly(False)
        self.editingFinished.connect(self.nameChanged)

    def nameChanged(self):
        self.item().setName(self.text())

    """ PROPERTIES """
    def setItem(self, item):
        self._item = item

    def item(self):
        return self._item


class UserInputMainWidget(QWidget):
    """
    Main widgets for inputting args to the Events widget.  This is the dynamic
    widget that will be used for the tansu widget.

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
        event_types = list(self.event_dict.keys())
        self.events_type_menu.populate(event_types)

        # create scripts thingy
        self.script_widget = InputScriptWidget(self)

        # create event type args widget
        self.dynamic_args_widget = ArgsInputMainWidget(self)

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
        self._event_type = event_type
        self.dynamic_args_widget.event_type = event_type
        self.dynamic_args_widget.update()
        self.item().setEventType(event_type)

    def getEventType(self):
        return self._event_type

    @staticmethod
    def updateGUI(widget, label):
        """
        widget (tab widget widget)
            can get main widget with widget.getMainWidget()
        label (tab bar label)
        """
        # preflight
        if not label: return

        # set title
        widget.setTitle(label.text())

        # set item
        main_widget = widget.getMainWidget()
        main_widget.setItem(label.item())

        # update event type
        event_type = label.item().getEventType()
        main_widget.events_type_menu.setCurrentIndexToText(event_type)

        # set script widget to label.item().getScript()
        script_location = label.item().getScript()
        main_widget.script_widget.setText(script_location)

        # update dynamic args widget
        main_widget.dynamic_args_widget.event_type = event_type
        main_widget.dynamic_args_widget.update()

        # set dynamic args values
        if main_widget.events_type_menu.currentText() != '':
            for arg in label.item().getArgsList():
                arg_value = label.item().getArg(arg)
                main_widget.dynamic_args_widget.widget_dict[arg].setText(arg_value)

    """ PROPERTIES """
    def setItem(self, item):
        self._item = item

    def item(self):
        return self._item


class EventTypeInputWidget(ListInputWidget):
    """
    Drop down menu containing all of the different event types
    that the user can choose from for a specific operation
    """
    def __init__(self, parent=None):
        super(EventTypeInputWidget, self).__init__(parent)
        self.setSelectionChangedEmitEvent(self.eventTypeChanged)

    def eventTypeChanged(self):
        event_type = str(self.currentText())
        if event_type:
            if event_type in self.getItemList():
                self.parent().setEventType(event_type)
                note = self.parent().event_dict[event_type]['note']
                self.setToolTip(note)
                return

        # if invalid input reset texta
        self.setCurrentIndexToText(self.previous_text)


class ArgsInputMainWidget(QWidget):
    """
    The widget that contains all of the options for a specific event type.  This
    will dynamically populate when the event type changes in the parent.
    ArgsInputMainWidget
        | -* ArgInputWidget
    Attributes:
        widget_dict (dict): key pair values of args to widgets
        event_type (str): the current event type that is set
    """
    def __init__(self, parent=None):
        super(ArgsInputMainWidget, self).__init__(parent)
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
            arg_name = arg['arg']
            arg_note = arg['note']
            widget = ArgInputWidget(self, arg_name, arg_note)
            self.layout().addWidget(widget)
            self.widget_dict[arg_name] = widget

    def update(self):
        self.clear()
        self.populate()

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


class ArgInputWidget(QWidget):
    """
    One individual arg

    TODO:
        Connect the signal changes in the line edit to where I'm going
        to store this JSON date type container thingy...

    """
    def __init__(self, parent=None, name='', note=''):
        super(ArgInputWidget, self).__init__(parent)
        # setup args
        self.arg = name

        # setup layout
        QHBoxLayout(self)
        self.label = QLabel(name)
        self.label.setToolTip(note)
        self.lineedit = QLineEdit()
        self.lineedit.editingFinished.connect(self.userInput)
        self.layout().addWidget(self.label)
        self.layout().addWidget(self.lineedit)

    def setText(self, text):
        self.lineedit.setText(text)

    def currentText(self):
        return self.lineedit.text()

    def userInput(self):
        main_widget = getWidgetAncestor(self, UserInputMainWidget)
        main_widget.item().setArg(self.arg, self.currentText())

    @property
    def arg(self):
        return self._arg

    @arg.setter
    def arg(self, arg):
        self._arg = arg


class InputScriptWidget(ArgInputWidget):
    """
    The script input widget
    """
    def __init__(self, parent=None):
        name = 'script'
        note = "path on disk to the script you want to run"
        super(InputScriptWidget, self).__init__(parent, name=name, note=note)

    def userInput(self):
        main_widget = getWidgetAncestor(self, UserInputMainWidget)
        main_widget.item().setScript(self.currentText())


class EventTypeModelItem(dict):
    """
    name (str): name given to this event by the user
    event_type (str): katana event type
    script (path): path on disk to .py file to run as script
    args (dict): dictionary of all the args
    index (int): current index that this item is holding in the model
    """
    def __init__(self, name=None, event_type=None, script=None, args=None):
        self['name'] = name
        self['event_type'] = event_type
        self['script'] = script
        if not args:
            args = {}
        self['args'] = args

    def setName(self, name):
        self['name'] = name

    def getName(self):
        return self['name']

    def setEventType(self, event_type):
        self['event_type'] = event_type

    def getEventType(self):
        return self['event_type']

    def setScript(self, script):
        self['script'] = script

    def getScript(self):
        return self['script']

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, index):
        self._index = index

    """ args"""
    def setArg(self, arg, value):
        self['args'][arg] = value

    def getArg(self, arg):
        return self['args'][arg]

    def getArgsList(self):
        return list(self['args'].keys())

    def removeArg(self, arg):
        self.pop(arg, None)


if __name__ == "__main__":
    # import sys
    # from PyQt5.QtWidgets import QApplication
    # from PyQt5.QtGui import QCursor
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
    # #     nw = BaseTansuWidget(w)
    # #     for b in ['a','b','c']:
    # #         nw.addWidget(QLabel(b))
    # #     w.insertTab(0, nw, str(x))
    #
    # #
    #
    #
    # # # dynamic widget example
    # dw = TabDynamicWidgetExample
    # w.setType(
    #     TabTansuWidget.DYNAMIC,
    #     dynamic_widget=TabDynamicWidgetExample,
    #     dynamic_function=TabDynamicWidgetExample.updateGUI
    # )
    # for x in range(3):
    #     nw = QLabel(str(x))
    #     w.insertTab(0, nw, str(x))
    # # for x in range(3):
    # #     nw = BaseTansuWidget(w)
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
