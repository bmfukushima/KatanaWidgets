from Katana import Utils

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

def loadUserEvents(*args):
    from Katana import NodegraphAPI, UI4
    print('==========  loading!!  ==========')
    print(args)
    node = NodegraphAPI.GetRootNode()
    tab = UI4.App.Tabs.FindTopTab('Events')
    if not tab:
        tab = UI4.App.Tabs.CreateTab("Events", None)._TabWithTimeline__widget

    print ("tab ====", tab)
    print ("node ==== ", node)
    tab.main_widget.loadEventsDataFromJSON()

    # todo LOAD EVENTS HERE
    # events need to be loaded from a tab...
    """
    if not tab:
        create tab
    
    tab.loadEventsDataFromJSON()
        
    """
    #UI4.App.Tabs.CreateTab("Events", None)

def cleanupEvents(*args):
    from Katana import NodegraphAPI, UI4
    print('==========  loading!!  ==========')
    print(args)
    node = NodegraphAPI.GetRootNode()
    tab = UI4.App.Tabs.FindTopTab('Events')
    print (node)
    print (tab)
    # todo CLEAR EVENTS HERE
    # events need to be loaded from a tab...
    """
    if not tab:
        create tab

    tab.clear events data
    """


Utils.EventModule.RegisterCollapsedHandler(loadUserEvents, 'nodegraph_loadEnd')
#Utils.EventModule.RegisterCollapsedHandler(cleanupEvents, 'nodegraph_loadBegin')
