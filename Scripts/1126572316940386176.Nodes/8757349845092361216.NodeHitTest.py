""" Determines the world coordinates of the cursor click """

nodegraph_tab = UI4.App.Tabs.FindTopTab('Node Graph')
nodegraph_widget = nodegraph_tab.getNodeGraphWidget()
nodegraph_widget.getCurrentNodeView()
mouse_pos = nodegraph_widget.getMousePos()
groupNode = nodegraph_widget.getGroupNodeUnderMouse()
worldPos = nodegraph_widget.mapFromQTLocalToWorld(mouse_pos.x(), mouse_pos.y())

x, y = nodegraph_widget.getPointAdjustedToGroupNodeSpace(groupNode, worldPos)
print("%s, %s)" %(x,y))