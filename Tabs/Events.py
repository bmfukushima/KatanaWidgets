from Widgets2 import EventWidget
'''
To Do 

    - Drag/Drop move nodes via Node List
    - option for syncing the state
    - option for viewing super tool children
    - sometimes super tool children not sorting correctly inside of supertools?
    - rename nodes
    - sort by node type
'''
from qtpy.QtWidgets import QVBoxLayout
from Katana import UI4 , NodegraphAPI, Utils

class EventsTab(UI4.Tabs.BaseTab):
    def __init__(self, parent=None):
        super(EventsTab, self).__init__(parent)

        QVBoxLayout(self)
        # setup main widget

        self.node = NodegraphAPI.GetRootNode()
        self.main_widget = EventWidget(self, node=self.node)
        self.layout().addWidget(self.main_widget)

        # create default parameter on root node
        if not self.node.getParameter("events_data"):
            self.node.getParameters().createChildString("events_data", "")
        else:
            self.main_widget.loadEventsDataFromJSON()


PluginRegistry = [("KatanaPanel", 2, "Events", EventsTab)]