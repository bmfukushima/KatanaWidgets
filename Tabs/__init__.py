from DesiredNodesTab import DesiredNodesTab
from MultiTools import EventsTab
from PiPWidget import PiPOrganizerTab
from GSVManager import GSVManager, installGSVManagerEvents
# compile list of tabs

#print(EventsTab.EventsTab)

tabs_list = [
    DesiredNodesTab,
    EventsTab.Tab,
    GSVManager,
    PiPOrganizerTab,
]
# register all tabs
PluginRegistry = []
for tab in tabs_list:
    PluginRegistry.append(("KatanaPanel", 2, tab.NAME, tab))

# register PiP Tabs
from .PiPWidget.PiPWidgetTabInitializer import pip_tabs

for pip_tab in pip_tabs:
    tab_name = "/". join(["PiP Displays", pip_tab["file_name"], pip_tab["widget_name"]])
    PluginRegistry.append(("KatanaPanel", 2, tab_name, pip_tab["constructor"]))
    #print(pip_tab)

# LOG
print("""\t|____  TABS""")
for tab in tabs_list:
    print("\t|\t|__  Loading...  {tab_name}".format(tab_name=tab.NAME))
    if tab == PiPOrganizerTab:
        for pip_tab in pip_tabs:
            tab_name = "/".join([pip_tab["file_name"], pip_tab["widget_name"]])
            print("\t|\t\t|__  Loading...  {tab_name}".format(tab_name=tab_name))
