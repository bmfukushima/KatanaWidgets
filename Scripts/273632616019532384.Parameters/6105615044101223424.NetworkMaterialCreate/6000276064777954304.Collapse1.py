#x = NodegraphAPI.GetNode('dlPrincipled')
from Katana import NodegraphAPI, Utils
node_list = NodegraphAPI.GetAllSelectedNodes()
for node in node_list:
    NodegraphAPI.SetNodeShapeAttr(node, "viewState", 1)
    Utils.EventModule.QueueEvent('node_setShapeAttributes', hash(node), node=node)
    Utils.EventModule.ProcessAllEvents() 
