from Katana import Utils, Callbacks

# initialize bebop menu
from ParameterMenu import installCustomParametersMenu
installCustomParametersMenu()

# setup backdrop group
# from MultiTools.BackdropGroupNode import installBackdropGroupNode
# installBackdropGroupNode()


# def test(*args):
#     for arg in args:
#         arg = arg[0]
#         if arg[0] == 'node_create':
#             node = arg[2]['node']
#             if node.getType() == 'RenderLayerGenerator':
#                 print ('do stuff here')
#
#
# Utils.EventModule.RegisterCollapsedHandler(test, 'node_create')


# Simple Tools
"""
Current issue in
    EventWidget --> disableAllEvents
        The handle is not static, so this is changing which causes it to
        not be able to find the correct handler =(
        
        Wrap this in something so that it can always find a static method?
"""
def loadUserEvents(*args):
    from Katana import NodegraphAPI, UI4
    from Widgets2 import EventWidget
    print('==========  end loading!!  ==========')
    # get attrs
    katana_main = UI4.App.MainWindow.GetMainWindow()
    node = NodegraphAPI.GetRootNode()

    events_data = node.getParameter("events_data")
    if not events_data:
        node.getParameters().createChildString("events_data", "")
    if katana_main:
        if not hasattr(katana_main, "global_events_widget"):
            katana_main.global_events_widget = EventWidget(katana_main, node=node)

        katana_main.global_events_widget.main_widget.clearModel()
        katana_main.global_events_widget.loadEventsDataFromJSON()

def cleanupEvents(**kwargs):
    from Katana import NodegraphAPI, UI4
    from Widgets2 import EventWidget
    print("====== onSceneAboutToLoad =========")
    node = NodegraphAPI.GetRootNode()
    katana_main = UI4.App.MainWindow.GetMainWindow()

    events_data = node.getParameter("events_data")
    if events_data:
        if hasattr(katana_main, "global_events_widget"):
            katana_main.global_events_widget.disableAllEvents(events_data.getValue(0))

Utils.EventModule.RegisterCollapsedHandler(loadUserEvents, 'nodegraph_loadEnd')
Callbacks.addCallback(Callbacks.Type.onSceneAboutToLoad, cleanupEvents)
