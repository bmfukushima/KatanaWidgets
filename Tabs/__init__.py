from Utils2 import isLicenseValid

if isLicenseValid():
    from .DesiredStuffTab import DesiredStuffTab
    from .PopupBar import PopupBarOrganizerTab
    from MultiTools import GlobalEventsTab, ScriptEditorTab, NodeColorRegistryTab
    from MultiTools.StateManagerTabs import StateManagerTab, GSVManagerTab, IRFManagerTab, BookmarkManagerTab
    from .TXMake import TXConverterTab

    # compile list of tabs
    tabs_list = [
        DesiredStuffTab,
        GlobalEventsTab.Tab,
        NodeColorRegistryTab.Tab,
        PopupBarOrganizerTab,
        BookmarkManagerTab.Tab,
        IRFManagerTab.Tab,
        GSVManagerTab.Tab,
        StateManagerTab,
        ScriptEditorTab.Tab,
        TXConverterTab
    ]


    # register all tabs
    PluginRegistry = []
    for tab in tabs_list:
        PluginRegistry.append(("KatanaPanel", 2, tab.NAME, tab))


    # register PiP Tabs
    from .PopupBar.PopupBarTabInitializer import popup_bar_tabs

    for popup_bar_tab in popup_bar_tabs:
        tab_name = "/". join(["Popup Bar Views", popup_bar_tab["filename"], popup_bar_tab["popup_bar_widget_name"]])
        PluginRegistry.append(("KatanaPanel", 2, tab_name, popup_bar_tab["constructor"]))


    # LOG
    print("""\t|____  TABS""")
    for tab in tabs_list:
        # popupbar organizer
        if tab == PopupBarOrganizerTab:
            print("\t \t|__  {tab_name}".format(tab_name=tab.NAME))
            for popup_bar_tab in popup_bar_tabs:
                tab_name = "/".join([popup_bar_tab["filename"], popup_bar_tab["popup_bar_widget_name"]])
                print("\t \t|\t|__  {tab_name}".format(tab_name=tab_name))

        # state managers
        elif tab in [BookmarkManagerTab.Tab, GSVManagerTab.Tab, IRFManagerTab.Tab, StateManagerTab]:
            if tab == BookmarkManagerTab.Tab:
                print("\t \t|__  State Managers")
            print("\t \t|\t|__  {tab_name}".format(tab_name=tab.NAME.split("/")[1]))

        else:
            print("\t \t|__  {tab_name}".format(tab_name=tab.NAME))


    # load test
