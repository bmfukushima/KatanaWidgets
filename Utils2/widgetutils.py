from Katana import UI4
from cgwidgets.utils import getWidgetUnderCursor

def katanaMainWindow():
    return UI4.App.MainWindow.GetMainWindow()


def getActiveNodegraphWidget():
    nodegraph_widget = isCursorOverNodeGraphWidget()
    if not nodegraph_widget:
        nodegraph_widget = UI4.App.Tabs.FindTopTab('Node Graph').getNodeGraphWidget()

    return nodegraph_widget


def isCursorOverNodeGraphWidget():
    """ Determines if the cursor is over a nodegraph widget or not.

    If it is, it will return the nodegraph widget.  If it is not, it will return None"""
    if not hasattr(getWidgetUnderCursor(), "__module__"): return False
    if not getWidgetUnderCursor(): return False
    if getWidgetUnderCursor().__module__.split(".")[-1] != "NodegraphWidget": return False
    return getWidgetUnderCursor()


