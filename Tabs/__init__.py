from DesiredStuffTab import DesiredStuffTab
from MultiTools import EventsTab, GSVManager
from PiPWidget import PiPOrganizerTab

# compile list of tabs

#print(EventsTab.EventsTab)

tabs_list = [
    DesiredStuffTab,
    EventsTab.Tab,
    GSVManager.Tab,
    PiPOrganizerTab,
]
# register all tabs
PluginRegistry = []
for tab in tabs_list:
    PluginRegistry.append(("KatanaPanel", 2, tab.NAME, tab))

# register PiP Tabs
from .PiPWidget.PiPWidgetTabInitializer import pip_tabs

for pip_tab in pip_tabs:
    tab_name = "/". join(["PiP Displays", pip_tab["filename"], pip_tab["pip_widget_name"]])
    PluginRegistry.append(("KatanaPanel", 2, tab_name, pip_tab["constructor"]))
    #print(pip_tab)

# LOG
print("""\t|____  TABS""")
for tab in tabs_list:
    print("\t|\t|__  Loading...  {tab_name}".format(tab_name=tab.NAME))
    if tab == PiPOrganizerTab:
        for pip_tab in pip_tabs:
            tab_name = "/".join([pip_tab["filename"], pip_tab["pip_widget_name"]])
            print("\t|\t\t|__  Loading...  {tab_name}".format(tab_name=tab_name))
