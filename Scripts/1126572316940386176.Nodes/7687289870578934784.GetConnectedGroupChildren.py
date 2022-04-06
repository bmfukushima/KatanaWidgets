""" Looks at the children of a group node, and returns the connected tree from the first input """

parent_node = NodegraphAPI.GetNode('GroupTree')
in_port_name = parent_node.getInputPortByIndex(0).getName()
send_port = parent_node.getSendPort(in_port_name)


child_node = send_port.getConnectedPorts()[0].getNode()
node_list = []

while child_node != parent_node:
    node_list.append(child_node)
    connected_port = child_node.getOutputPortByIndex(0).getConnectedPorts()[0]
    if not connected_port:
        break
    child_node = connected_port.getNode()

print(node_list)