node = NodegraphAPI.GetNode('Backdrop')
shape_attrs = {
    'text': 'backdrop_2',
    'zDepth': 1,
    'colorr':0.5,
    'colorg':0.5,
    'colorb':1.0,
    }


NodegraphAPI.SetNodeShapeNodeAttrs(node, shape_attrs)
Utils.EventModule.QueueEvent('node_setShapeAttributes', hash(node), node=node)
