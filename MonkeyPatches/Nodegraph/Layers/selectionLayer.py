""" The selection node layer handles all events that happen involving the S key

These events are:
    S+LMB:
        Select nodes
    Shift+S:
        Show popup GSV widget
    S:
        Show GSV layered menu

There are two other handlers on this layer for the
"""

from qtpy.QtCore import Qt, QPoint, QSize
from qtpy.QtGui import QCursor

# setup prefs
from Katana import NodegraphAPI, Utils, PrefNames, KatanaPrefs, UI4, LayeredMenuAPI

from cgwidgets.utils import scaleResolution
from cgwidgets.settings import iColor

from Utils2 import nodegraphutils, widgetutils, nodeutils, getFontSize

from .AbstractGestureLayer import (
    AbstractGestureLayer,
    insertLayerIntoNodegraph
)

ATTR_NAME = "_selection"


class SelectionLayer(AbstractGestureLayer):
    """

    Attributes:
        cursor_trajectory (SelectionLayer.DIRECTION): direction to position the nodes
        last_cursor_points (list): of QPoints that hold the last 5 cursor positions
            This is used for calculating the cursors trajectory
        _node_iron_aligned_nodes (list): of nodes that have been aligned
        _node_iron_active (bool): determines if this event is active or not
        _node_iron_finishing (bool): determines if the link cutting event is finishing
            This is useful to differentiate between a A+LMB and a A-Release event
    """

    def __init__(self, *args, **kwargs):
        super(SelectionLayer, self).__init__(*args, **kwargs)
        self.setCrosshairRadius(QSize(10, 20))

    def keyReleaseEvent(self, event):
        if event.modifiers() == Qt.NoModifier:
            # launch layered menu
            nodegraph_widget = widgetutils.getActiveNodegraphWidget()
            from UIPlugins.GSVMenu import GSVMenuPopulateCallback, GSVMenuActionCallback
            GSVMenu = LayeredMenuAPI.LayeredMenu(
                GSVMenuPopulateCallback,
                GSVMenuActionCallback,
                'S',
                alwaysPopulate=True,
                onlyMatchWordStart=False
            )
            nodegraph_widget.showLayeredMenu(GSVMenu)
        return AbstractGestureLayer.keyReleaseEvent(self, event)

    def mouseReleaseEvent(self, event):
        if self.isActive():
            selected_nodes = self.getHits()
            nodegraphutils.floatNodes(selected_nodes)

        return AbstractGestureLayer.mouseReleaseEvent(self, event)

    def paintGL(self):
        if self.isActive():
            # create point on cursor
            mouse_pos = self.layerStack().getMousePos()
            # align nodes
            if mouse_pos:
                # set initial trajectory
                if len(self.getHits()) == 0:
                    if 1 < len(self.getCursorPoints()):
                        self._cursor_trajectory = nodegraphutils.getCursorTrajectory(self.getCursorPoints()[0], self.getCursorPoints()[-1])

                # draw crosshair
                self.drawCrosshair()
                self.drawTrajectory()

                # iron nodes
                if 0 < len(self.getCursorPoints()):
                    hit_points = nodegraphutils.interpolatePoints(self.getCursorPoints()[-1], mouse_pos, radius=self.crosshairRadius(), step_size=5)
                    node_hits = nodegraphutils.pointsHitTestNode(hit_points, self.layerStack(), hit_type=nodegraphutils.NODE)

                    for node in node_hits:
                        # first node
                        if node not in self.getHits():
                            self.addHit(node)
                            nodeutils.addNodePreviewColor([node])

                self.addCursorPoint(mouse_pos)


""" EVENTS"""
def installSelectionLayer(**kwargs):
    insertLayerIntoNodegraph(SelectionLayer, ATTR_NAME, Qt.Key_S, "Select Nodes")