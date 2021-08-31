"""
TODO:
    Group Editor:
        Appears to have two levels of Shojis... for some reason...
                Model Shoji View
                    --> Base shoji
                for some reason the base shoji is not working...
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

from qtpy.QtCore import Qt, QEvent

from cgwidgets.views import AbstractDragDropListView
from cgwidgets.widgets import ShojiLayout

from Katana import UI4, Utils
from Widgets2 import (TwoFacedSuperToolWidget, SimpleToolEventWidget)

from .GroupNodeEditor import GroupNodeEditorMainWidget


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

        # self.events_param = self.main_node.getParameters().createChildString("events_data", "")
        self.getDesignWidget().setDelegateTitleIsShown(False)
        # create widgets
        self._group_node_editor_widget = GroupNodeEditorMainWidget(self, self.node, self.main_node)
        self._events_widget = SimpleToolEventWidget(self, self.main_node)

        # setup tabs
        self.getDesignWidget().insertShojiWidget(
            0, column_data={'name':"Params"}, widget=self.groupNodeEditorWidget())
        self.getDesignWidget().insertShojiWidget(
            1, column_data={'name':'Events'}, widget=self.eventsWidget())

        # setup flags
        self.getDesignWidget().setHeaderItemIsDragEnabled(False)
        self.getDesignWidget().setHeaderItemIsDropEnabled(False)
        self.getDesignWidget().setHeaderItemIsEditable(False)

        # setup events

    def showEvent(self, event):
        self.getDesignWidget().show()
        return TwoFacedSuperToolWidget.showEvent(self, event)

    """ WIDGETS """
    def eventsWidget(self):
        return self._events_widget

    def groupNodeEditorWidget(self):
        return self._group_node_editor_widget


class SimpleToolViewWidget(AbstractDragDropListView):
    def __init__(self, parent=None):
        super(SimpleToolViewWidget, self).__init__(parent)


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication, QLabel, QVBoxLayout
    from qtpy.QtGui import QCursor
    from cgwidgets.widgets import ShojiModelViewWidget
    app = QApplication(sys.argv)

    w = ShojiModelViewWidget()
    w.setHeaderPosition(ShojiModelViewWidget.NORTH)
    w.setMultiSelect(True)
    w.setMultiSelectDirection(Qt.Vertical)

    new_view = SimpleToolViewWidget()
    w.setHeaderViewWidget(new_view)

    # dw = TabShojiDynamicWidgetExample
    # w.setDelegateType(
    #     ShojiModelViewWidget.DYNAMIC,
    #     dynamic_widget=TabShojiDynamicWidgetExample,
    #     dynamic_function=TabShojiDynamicWidgetExample.updateGUI
    # )

    for x in range(3):
        widget = QLabel(str(x))
        w.insertShojiWidget(x, str(x), widget=widget)

    w.resize(500, 500)

    w.show()
    w.move(QCursor.pos())
    sys.exit(app.exec_())