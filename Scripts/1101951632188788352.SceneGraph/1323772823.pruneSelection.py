from Katana import ScenegraphManager, NodegraphAPI, UI4
def connectNode(node):
    resolve_node = NodegraphAPI.GetViewNode()
    if resolve_node.getType() != 'Render':
        
        #set node position
        NodegraphAPI.SetNodePosition(node, NodegraphAPI.GetNodePosition(resolve_node))
        upstream_nodes = getAllUpstreamNodes(resolve_node,node_list=[])
        for child_node in upstream_nodes:
            pos = (NodegraphAPI.GetNodePosition(child_node)[0],NodegraphAPI.GetNodePosition(child_node)[1]+50)
            NodegraphAPI.SetNodePosition(child_node, pos)
        #set node flag
        NodegraphAPI.SetNodeViewed(node,True,exclusive=True)
        #connect input
        output_port = resolve_node.getOutputPortByIndex(0)
        node.getInputPortByIndex(0).connect(output_port)
        #need function to run up and move all nodes in graph up 100 units to allow space for the new node...
        port_list = output_port.getConnectedPorts()
        #connect output...
        if len(port_list) > 0:
            #next_node = port_list[0].getNode()
            node.getOutputPortByIndex(0).connect(port_list[0])
    
def getAllUpstreamNodes(node,node_list=[]):
    children = node.getInputPorts()
    node_list.append(node)
    if children > 0:
        for input_port in children:
            connected_ports = input_port.getConnectedPorts()
            for port in connected_ports:
                node = port.getNode()
                
                getAllUpstreamNodes(node,node_list=node_list)
    return node_list
selected_locations = ScenegraphManager.getActiveScenegraph().getSelectedLocations()
prune_string =  '%s'%' '.join(selected_locations)

node_graph = UI4.App.Tabs.FindTopTab('Node Graph')
node = NodegraphAPI.CreateNode('Prune',NodegraphAPI.GetRootNode())
node.getParameter('cel').setValue(prune_string,0)
connectNode(node)
node_graph.floatNodes([node])
