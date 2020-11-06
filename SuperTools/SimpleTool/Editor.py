"""
TODO:
    Group Editor:
        Appears to have two levels of Tansus... for some reason...
                Model Tansu View
                    --> Base tansu
                for some reason the base tansu is not working...
    Extract:
        Variable Manager:
            *   Nodegraph Widget
            *   Params display system
            *   Publish System (optional)
        HUD:
            *   UI Create
    Node:
        *   SimpleTool --> Live Group --> Contents of group
        *   Can I just completely overwrite group node/ live group functionality?
    Trigger:
        *   Script Editor
                - Need to refactor this, and make it work with this...
        *   Event Types
                -
        *   --------- Get all args... ---------
                - Hard coded?
            Event Dict {
                event_type: { 'args': [{'arg': argName, 'note': 'description'] , 'note': 'description'},
                event_type: { 'args': [] , 'description': 'note'},
            }
                    [{event_type: {**kwargs}}]
                - Dynamic?
                    - Register dummy, get values, destroy dummy?
                    - Something smarter?
                    - Ask?
        *   Register all Event Types?
                - setupEventHandlers
                    event_types = Utils.EventModule.GetAllRegisteredEventTypes()
                    Utils.EventModule.RegisterCollapsedHandler(
                        self.__undoEventUpdate, 'event_idle', enabled=enabled
                    )
        *   Triggered Function
                - check conditions on args
                - if condition is empty/blank don't count it
                - run python file
                    --------- Pass args to Python file ---------
        *   Args use of Katana Parameters
                - Args need to have a syntax to read parameters on the node
                    so that users can use custom parameters.
                - Can potentially add functionality to Abstract?
                    iParameter interface...
"""

from qtpy.QtWidgets import (
    QLabel, QVBoxLayout, QWidget
)

from qtpy.QtCore import Qt, QEvent

from Widgets2 import (
    TwoFacedSuperToolWidget
)

from cgwidgets.widgets import TansuBaseWidget, TansuHeaderListView

try:
    from Katana import UI4
except ModuleNotFoundError:
    pass

from .GroupNodeEditor import GroupNodeEditorMainWidget
from .EventsWidget import EventWidget


class SimpleToolEditor(TwoFacedSuperToolWidget):
    """
    The top level widget for the editor.  This is here to encapsulate
    the main widget with a stretch box...

    Attributes:
        should_update (bool): determines if this tool should have
            its GUI updated or not during the next event idle process.

    """
    def __init__(self, parent, node):
        super(SimpleToolEditor, self).__init__(parent, node)
        # set up attrs
        self.node = node
        self.main_node = node.getChildByIndex(0)

        self.group_node_editor = GroupNodeEditorMainWidget(self, self.node, self.main_node)
        self.events_widget = EventWidget(self)
        # setup tabs
        self.getDesignWidget().insertTansuWidget(
            0, column_data={'name':"Params"}, widget=self.group_node_editor)
        self.getDesignWidget().insertTansuWidget(
            1, column_data={'name':'Events'}, widget=self.events_widget)
        # self.getDesignWidget().insertTansuWidget(
        #     2, column_data={'name':'GUI Designer'}, widget=QLabel('GUI Designer'))
        # self.getDesignWidget().insertTansuWidget(
        #     3, column_data={'name':'User Params'}, widget=QLabel('User Params'))

        # setup flags
        self.getDesignWidget().setHeaderIsDragEnabled(False)
        self.getDesignWidget().setHeaderIsDropEnabled(False)
        self.getDesignWidget().setHeaderIsEditable(False)

    def getEventTypes(self):
        """
        Right now this is just printing out all the different args and what not...
        """
        import json

        with open('args.json', 'r') as args:
            args_dict = json.load(args)
            for event_type in args_dict.keys():
                print('')
                print(event_type, args_dict[event_type]['note'])
                for arg in args_dict[event_type]['args']:
                    arg_name = arg['arg']
                    arg_note = arg['note']
                    print('-----|', arg_name, arg_note)

    def showEvent(self, event):
        self.getDesignWidget().show()
        return TwoFacedSuperToolWidget.showEvent(self, event)


class SimpleToolViewWidget(TansuHeaderListView):
    def __init__(self, parent=None):
        super(SimpleToolViewWidget, self).__init__(parent)



if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication, QLabel, QVBoxLayout
    from qtpy.QtGui import QCursor
    from cgwidgets.widgets import TansuModelViewWidget
    app = QApplication(sys.argv)

    w = TansuModelViewWidget()
    w.setHeaderPosition(TansuModelViewWidget.NORTH)
    w.setMultiSelect(True)
    w.setMultiSelectDirection(Qt.Vertical)

    new_view = SimpleToolViewWidget()
    w.setHeaderWidget(new_view)

    # dw = TabTansuDynamicWidgetExample
    # w.setDelegateType(
    #     TansuModelViewWidget.DYNAMIC,
    #     dynamic_widget=TabTansuDynamicWidgetExample,
    #     dynamic_function=TabTansuDynamicWidgetExample.updateGUI
    # )

    for x in range(3):
        widget = QLabel(str(x))
        w.insertTansuWidget(x, str(x), widget=widget)

    w.resize(500, 500)

    w.show()
    w.move(QCursor.pos())
    sys.exit(app.exec_())