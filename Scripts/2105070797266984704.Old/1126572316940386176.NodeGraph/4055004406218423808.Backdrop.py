a = NodegraphAPI.GetNode('Backdrop')
NodegraphAPI.SetAllSelectedNodes([a])


def get_backdrop_children(backdrop_node):
    ng = UI4.App.Tabs.FindTopTab('Node Graph')
    widget = ng.getNodeGraphWidget()

    l, b, r, t = DrawingModule.nodeWorld_getBoundsOfListOfNodes([backdrop_node])
    children = widget.hitTestBox(
        (l, b),
        (r, t),
        viewNode=backdrop_node.getParent()
    )
    print(children)
    selected_nodes = [node for node in children if node is not None]
    
    return [ node for node in children if node is not None ]

b = get_backdrop_children(a)
print (b)

