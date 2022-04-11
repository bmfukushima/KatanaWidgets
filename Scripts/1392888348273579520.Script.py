from cgwidgets.utils import getWidgetUnderCursor
from Katana import UI4

w = getWidgetUnderCursor()
print("mouse_pos ==", w.getMousePos())

# nodegraph_tab = UI4.App.Tabs.FindTopTab('Node Graph')
# nodegraph_widget = nodegraph_tab.getNodeGraphWidget()
# print(nodegraph_widget)