# To get the bounds of a node:
n = NodegraphAPI.GetNode("LocationCreate")
if n:
    print (DrawingModule.nodeWorld_getBounds(n) )