import sys

from PyQt5.QtWidgets import (
    QApplication, QLineEdit, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QSplitter
)

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor
from Widgets2 import AbstractComboBox


class EventWidget(QWidget):
    """
    The main widget for setting up the events triggers on the node.
    HBox
        |-- VBox
        |       |-- NewEventButton
        |       |-- EventListWidget
        |-- VBox
                |-- EventArgsWidget
                        |-- VBox
                            |-- EventTypesMenu
                            |-- Script Argument
                            |-- EventTypeArgumentsWidget
    """
    def __init__(self, parent=None):
        super(EventWidget, self).__init__(parent)
        QHBoxLayout(self)
        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Horizontal)

        self.events_list_widget = EventListWidget(self)
        self.events_args_widget = EventsArgsMainWidget(self)

        self.splitter.addWidget(self.events_list_widget)
        self.splitter.addWidget(self.events_args_widget)
        self.layout().addWidget(self.splitter)
        self.splitter.setSizes([300, 700])


class EventListWidget(QListWidget):
    def __init__(self, parent=None):
        super(EventListWidget, self).__init__(parent)


class EventListWidgetItem(QListWidgetItem):
    def __init__(self, parent=None):
        super(EventListWidgetItem, self).__init__(parent)


class EventsArgsMainWidget(QWidget):
    """

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
        super(EventsArgsMainWidget, self).__init__(parent)
        QVBoxLayout(self)
        self.layout().setAlignment(Qt.AlignTop)

        self.loadEventTypesDict()

        # create events type menu
        self.events_type_menu = EventTypesMenu(self)
        event_types = list(self.event_dict.keys())
        self.events_type_menu.populate(event_types)

        # create scripts thingy
        self.script_widget = EventTypeArgWidget(self, "script", "path on disk to the script you want to run")

        # create event type args widget
        self.dynamic_args_widget = EventTypeDynamicArgsWidget(self)

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
                print('')
                print(event_type, self.event_dict[event_type]['note'])
                for arg in self.event_dict[event_type]['args']:
                    arg_name = arg['arg']
                    arg_note = arg['note']
                    print('-----|', arg_name, arg_note)

    def setEventType(self, event_type):
        self._event_type = event_type
        self.dynamic_args_widget.event_type = event_type
        self.dynamic_args_widget.update()

    def getEventType(self):
        return self._event_type


class EventTypesMenu(AbstractComboBox):
    """
    Drop down menu containing all of the different event types
    that the user can choose from for a specific operation
    """
    def __init__(self, parent=None):
        super(EventTypesMenu, self).__init__(parent)
        self.setSelectionChangedEmitEvent(self.eventTypeChanged)

    def eventTypeChanged(self):
        event_type = str(self.currentText())
        if event_type:
            self.parent().setEventType(event_type)
            note = self.parent().event_dict[event_type]['note']
            self.setToolTip(note)


class EventTypeDynamicArgsWidget(QWidget):
    """
    The widget that contains all of the options for a specific event type.  This
    will dynamically populate when the event type changes in the parent.
    """
    def __init__(self, parent=None):
        super(EventTypeDynamicArgsWidget, self).__init__(parent)
        QVBoxLayout(self)
        self.layout().setAlignment(Qt.AlignTop)

    def clear(self):
        for index in reversed(range(self.layout().count())):
            widget = self.layout().itemAt(index).widget()
            if widget:
                widget.setParent(None)

    def populate(self):
        args_list = self.parent().event_dict[self.event_type]['args']
        for arg in args_list:
            arg_name = arg['arg']
            arg_note = arg['note']
            widget = EventTypeArgWidget(self, arg_name, arg_note)
            self.layout().addWidget(widget)

    def update(self):
        self.clear()
        self.populate()

    @property
    def event_type(self):
        return self._event_type

    @event_type.setter
    def event_type(self, event_type):
        self._event_type = event_type


class EventTypeArgWidget(QWidget):
    """
    One individual arg

    TODO:
        Connect the signal changes in the line edit to where I'm going
        to store this JSON date type container thingy...

    """
    def __init__(self, parent=None, name='', note=''):
        super(EventTypeArgWidget, self).__init__(parent)
        QHBoxLayout(self)
        self.label = QLabel(name)
        self.label.setToolTip(note)
        self.lineedit = QLineEdit()
        self.layout().addWidget(self.label)
        self.layout().addWidget(self.lineedit)


app = QApplication(sys.argv)
mw = EventWidget()
mw.show()
mw.move(QCursor().pos())
sys.exit(app.exec_())

