from Katana import UI4
from UI4.App import Tabs

from cgwidgets.utils import getWidgetUnderCursor

def katanaMainWindow():
    return UI4.App.MainWindow.GetMainWindow()


def getActiveNodegraphWidget():
    # get nodegraph under cursor
    nodegraph_widget = isCursorOverNodeGraphWidget()

    # find nodegraph top tab
    if not nodegraph_widget:
        nodegraph_tab = UI4.App.Tabs.FindTopTab('Node Graph')
        if nodegraph_tab:
            nodegraph_widget = nodegraph_tab.getNodeGraphWidget()

    # find any nodegraph widget

    # no node graph widgets found
    if not nodegraph_widget:
        nodegraph_panel = Tabs._LoadedTabPluginsByTabTypeName["Node Graph"].data(None)
        nodegraph_widget = nodegraph_panel.getNodeGraphWidget()

    return nodegraph_widget


def isCursorOverNodeGraphWidget():
    """ Determines if the cursor is over a nodegraph widget or not.

    If it is, it will return the nodegraph widget.  If it is not, it will return None"""
    widget_under_cursor = getWidgetUnderCursor()
    if not widget_under_cursor: return False
    if not hasattr(widget_under_cursor, "__module__"): return False
    if widget_under_cursor.__module__.split(".")[-1] != "NodegraphWidget": return False
    return widget_under_cursor


