from DesiredNodesTab import DesiredNodesTab
from EventsTab import EventsTab
from PiPWidget import PiPTab
# compile list of tabs
tabs_list = [

]
tabs_list = [
    DesiredNodesTab,
    EventsTab,
    PiPTab
]
# register all tabs
PluginRegistry = []
for tab in tabs_list:
    PluginRegistry.append(("KatanaPanel", 2, tab.NAME, tab))

# LOG
print("""\t|____  TABS""")
for tab in tabs_list:
    print("\t|\t|__  Loading...  {tab_name}".format(tab_name=tab.NAME))