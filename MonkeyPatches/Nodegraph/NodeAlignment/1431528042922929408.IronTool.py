import sys
sys.path.append('/media/ssd01/dev/katana/KatanaResources_old/Shelves/self')
from NodeStraightener import View
from Katana import UI4

nodegraph = UI4.App.Tabs.FindTopTab('Node Graph')
nodegraph_widget = nodegraph.getNodeGraphWidget()
view = View()
view.show()
nodegraph_widget.installEventFilter(view)
