from Katana import UI4, DrawingModule, NodegraphAPI
from qtpy.QtCore import QPoint


nodegraph_tab = UI4.App.Tabs.FindTopTab('Node Graph')
nodegraph_widget = nodegraph_tab.getNodeGraphWidget()
group_node = NodegraphAPI.GetNode('Group')
root_node = NodegraphAPI.GetRootNode()

# need to get the local pos inside of the layer...
mouse_pos = nodegraph_widget.getMousePos()
world_pos = nodegraph_widget.mapFromQTLocalToWorld(mouse_pos.x(), mouse_pos.y())
world_pos = QPoint(world_pos[0], world_pos[1])

click_point = DrawingModule.nodeWorld_mapFromWorldPositionToCurrentGroupWorldPosition(
     root_node, group_node, world_pos.x(), world_pos.y(), nodegraph_widget.getViewScale()[0])

print("click_point == ", click_point)





