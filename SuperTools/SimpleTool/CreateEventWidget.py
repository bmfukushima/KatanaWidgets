import sys

from PyQt5.QtWidgets import (
    QApplication, QLineEdit, QWidget, QVBoxLayout
)

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor
from Widgets2 import AbstractComboBox


class CreateEventWidget(QWidget):
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
        super(CreateEventWidget, self).__init__(parent)
        QVBoxLayout(self)

        self.loadEventTypesDict()
        self.events_type_menu = EventTypesMenu(self)
        event_types = list(self.event_dict.keys())
        self.events_type_menu.populate(event_types)
        self.layout().addWidget(self.events_type_menu)


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


class EventTypesMenu(AbstractComboBox):
    def __init__(self, parent=None):
        super(EventTypesMenu, self).__init__(parent)



app = QApplication(sys.argv)
mw = CreateEventWidget()
mw.show()
mw.move(QCursor().pos())
sys.exit(app.exec_())

