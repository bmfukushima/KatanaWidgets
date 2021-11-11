'''
ToDo
    *   Deleting item doesn't delete it, only disables?

    - Drag/Drop move nodes via Node List
    - option for syncing the state
    - option for viewing super tool children
    - sometimes super tool children not sorting correctly inside of supertools?
    - rename nodes
    - sort by node type
'''
from qtpy.QtWidgets import QVBoxLayout
from Katana import UI4 , NodegraphAPI, Utils
from Widgets2 import GlobalEventWidget
from Utils2 import widgetutils

class EventsTab(UI4.Tabs.BaseTab):
    NAME = 'Global Events'
    def __init__(self, parent=None):
        super(EventsTab, self).__init__(parent)
        self._param_location = "KatanaBebop.GlobalEventsData"

        QVBoxLayout(self)
        # setup main widget

        self._node = NodegraphAPI.GetRootNode()

        node = NodegraphAPI.GetRootNode()
        if not hasattr(widgetutils.katanaMainWindow(), "global_events_widget"):
            widgetutils.katanaMainWindow().global_events_widget = GlobalEventWidget(
                widgetutils.katanaMainWindow(), node=node, param=self.paramLocation())

        self._events_widget = widgetutils.katanaMainWindow().global_events_widget
        self.layout().addWidget(self.eventsWidget())

    def node(self):
        return self._node

    def paramLocation(self):
        return self._param_location

    def showEvent(self, event):
        """ Overrides show event, as this is a UNIQUE widget.

        So showing it multiple times can cause this to break.  Thus it will use
        the same widget, and reparent that widget to the current Events Tab"""
        self.layout().addWidget(self.eventsWidget())
        node = NodegraphAPI.GetRootNode()
        # if not node.getParameter(self.paramLocation()):
        #     node.getParameters().createChildString(self.paramLocation(), "")

        # update data
        self.eventsWidget().setNode(node)
        self.eventsWidget().eventsWidget().clearModel()
        self.eventsWidget().loadEventsDataFromParam()
        self.eventsWidget().show()

    def closeEvent(self, event):
        self.eventsWidget().setParent(widgetutils.katanaMainWindow())
        self.eventsWidget().hide()

    """ WIDGETS """
    def eventsWidget(self):
        return widgetutils.katanaMainWindow().global_events_widget

#PluginRegistry = [("KatanaPanel", 2, "Events", EventsTab)]