def connectNode(node):
    resolve_node = NodegraphAPI.GetViewNode()
    if resolve_node.getType() != 'Render':
        
        #set node position
        NodegraphAPI.SetNodePosition(node, NodegraphAPI.GetNodePosition(resolve_node))
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

print getAllUpstreamNodes(node,node_list=[])

node = NodegraphAPI.CreateNode('Prune',NodegraphAPI.GetRootNode())

connectNode(node)