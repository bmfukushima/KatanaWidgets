node = NodegraphAPI.GetNode('Switch')

for x in range(10):
    pos = NodegraphAPI.GetNodePosition(node)
    NodegraphAPI.SetNodePosition(node, (pos[0], pos[1] + 100))
    NodegraphAPI.SetNeedsRedraw(True)
    Utils.EventModule.ProcessAllEvents()
    time.sleep(.1)