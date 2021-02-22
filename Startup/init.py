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

    node = NodegraphAPI.GetRootNode()
    _temp_events_widget = EventWidget(node=node)
    _temp_events_widget.loadEventsDataFromJSON()

def cleanupEvents(**kwargs):
    from Katana import NodegraphAPI
    from Widgets2 import EventWidget
    print("====== onSceneAboutToLoad =========")
    node = NodegraphAPI.GetRootNode()
    _temp_events_widget = EventWidget(node=node)

    events_data = node.getParameter("events_data")
    if events_data:
        _temp_events_widget.disableAllEvents(events_data.getValue(0))

Utils.EventModule.RegisterCollapsedHandler(loadUserEvents, 'nodegraph_loadEnd')
Callbacks.addCallback(Callbacks.Type.onSceneAboutToLoad, cleanupEvents)
