import sys

from qtpy.QtWidgets import (
    QApplication, QLineEdit, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton
)

from qtpy.QtCore import Qt
from qtpy.QtGui import QCursor
from cgwidgets.widgets import ListInputWidget, TabLabelWidget, TabTansuWidget


class EventWidget(QWidget):
    """
    The main widget for setting up the events triggers on the node.
    Widgets:
        | -- VBox
                | -- new_event_button (PushButton)
                | -- main_widget (TabTansuWidget)
                        | -- label type (EventsLabelWidget --> TansuLabelWidget)
                        | -- Dynamic Widget (EventsArgsMainWidget --> QWidget)
                            | -- VBox
                                    | -- events_type_menu ( EventTypesMenu)
                                    | -- script_widget (EventTypeArgWidget)
                                    | -- dynamic_args_widget (EventTypeDynamicArgsWidget)
                                            | -* EventTypeArgWidget
    """
    def __init__(self, parent=None):
        super(EventWidget, self).__init__(parent)

        # setup layout
        QVBoxLayout(self)
        self.new_event_button = QPushButton('new_event')
        self.new_event_button.clicked.connect(self.createNewEvent)
        self.main_widget = self.setupEventsWidget()

        self.layout().addWidget(self.new_event_button)
        self.layout().addWidget(self.main_widget)

    def createNewEvent(self):
        self.main_widget.insertTab(0, "New Event")

    def setupEventsWidget(self):
        """
        Sets up the main Tansu widget that is showing the events to the user
        """
        main_widget = TabTansuWidget(self)
        main_widget.setTabLabelInstanceType(EventsLabelWidget)
        main_widget.setTabBarPosition(TabTansuWidget.WEST)
        main_widget.setType(
            TabTansuWidget.DYNAMIC,
            dynamic_widget=EventsArgsMainWidget,
            dynamic_function=EventsArgsMainWidget.updateGUI
        )

        return main_widget


class EventsLabelWidget(TabLabelWidget):
    """
    The label that is displayed back to the user to be selected to show off
    this events arguments
    """
    def __init__(self, parent, text, index):
        super(EventsLabelWidget, self).__init__(parent, text, index)
        self.setReadOnly(False)


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

    @staticmethod
    def updateGUI(widget, label):
        """
        widget (tab widget widget)
        label (tab bar label)
        """
        print(widget, label)
        if label:
            widget.setTitle(label.text())
            # update
            #widget.getMainWidget().label.setText(label.text())


class EventTypesMenu(ListInputWidget):
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

