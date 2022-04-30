""" The iron node layer allows users to "iron" their nodes

As the user swipes through nodes using CTRL+ALT+SHIFT+LMB, all
of the nodes hit will be aligned to the first node, based off
of the direction of the cursor as it passed through the second node.

todo:
    - draw cursor
    - add search radius (nodegraphutils)
"""
import math

from OpenGL.GL import (
    glBegin,
    glLineWidth,
    GL_POINTS,
    GL_LINE_LOOP,
    glColor4f,
    glEnd,
    glVertex2f,
    glPointSize,
)
from qtpy.QtWidgets import QApplication
from qtpy.QtCore import Qt, QPoint, QEvent, QTimer

# setup prefs
import QT4GLLayerStack
from Katana import NodegraphAPI, Utils, PrefNames, KatanaPrefs, UI4
from UI4.App import Tabs
from Utils2 import nodegraphutils, widgetutils, nodeutils


class NodeIronLayer(QT4GLLayerStack.Layer):
    """

    Attributes:
        cursor_trajectory (NodeIronLayer.DIRECTION): direction to position the nodes
        last_cursor_points (list): of QPoints that hold the last 5 cursor positions
            This is used for calculating the cursors trajectory
        _node_iron_aligned_nodes (list): of nodes that have been aligned
        _node_iron_active (bool): determines if this event is active or not
    """

    def __init__(self, *args, **kwargs):
        (QT4GLLayerStack.Layer.__init__)(self, *args, **kwargs)
        self._cursor_trajectory = nodegraphutils.RIGHT
        self._last_cursor_points = []
        if not hasattr(widgetutils.katanaMainWindow(), "_node_iron_finishing"):
            widgetutils.katanaMainWindow()._node_iron_finishing = False

        if not hasattr(widgetutils.katanaMainWindow(), "_node_iron_aligned_nodes"):
            widgetutils.katanaMainWindow()._node_iron_aligned_nodes = []

        if not hasattr(widgetutils.katanaMainWindow(), "_node_iron_active"):
            widgetutils.katanaMainWindow()._node_iron_active = False

    def getAlignedNodes(self):
        return widgetutils.katanaMainWindow()._node_iron_aligned_nodes

    def getAlignXPos(self):
        return NodegraphAPI.GetNodePosition(self.getAlignedNodes()[-1])[0]

    def getAlignYPos(self):
        return NodegraphAPI.GetNodePosition(self.getAlignedNodes()[-1])[1]

    def addCursorPoint(self, point):
        self._last_cursor_points.append(point)

        if 5 < len(self._last_cursor_points):
            self._last_cursor_points = self._last_cursor_points[-5:]

    def getCursorPoints(self):
        return self._last_cursor_points

    def resetCursorPoints(self):
        self._last_cursor_points = []

    def getCursorTrajectory(self):
        """ Returns the direction that the cursor is currently travelling

        Returns (NodeIronLayer.DIRECTION)"""

        return self._cursor_trajectory

    def paintGL(self):
        if widgetutils.katanaMainWindow()._node_iron_active:
            # create point on cursor
            mouse_pos = self.layerStack().getMousePos()
            # align nodes
            if mouse_pos:
                window_pos = QPoint(mouse_pos.x(), self.layerStack().getWindowSize()[1] - mouse_pos.y())
                if len(self.getAlignedNodes()) == 0:
                    if 1 < len(self.getCursorPoints()):
                        self._cursor_trajectory = nodegraphutils.getCursorTrajectory(self.getCursorPoints()[0], self.getCursorPoints()[-1])
                        # print('updating trajectory to..', self._cursor_trajectory)

                # todo draw something more interesting than a dot...
                # draw crosshair
                radius = 10
                glColor4f(0.75, 0.75, 1, 1)
                glPointSize(radius * 2)
                glLineWidth(2)
                glBegin(GL_LINE_LOOP)

                glVertex2f(window_pos.x() - 10, window_pos.y())
                glVertex2f(window_pos.x(), window_pos.y() + 10)
                glVertex2f(window_pos.x() + 10, window_pos.y())
                glVertex2f(window_pos.x(), window_pos.y() - 10)
                glEnd()

                # iron nodes
                if 0 < len(self.getCursorPoints()):
                    hit_points = nodegraphutils.interpolatePoints(self.getCursorPoints()[-1], mouse_pos)
                    node_hits = nodegraphutils.pointsHitTestNode(hit_points, self.layerStack())

                    for node in node_hits:
                        # first node
                        if node not in self.getAlignedNodes():
                            if len(self.getAlignedNodes()) == 0:
                                if KatanaPrefs[PrefNames.NODEGRAPH_GRIDSNAP]:
                                    from Utils2.nodealignutils import AlignUtils
                                    AlignUtils().snapNodeToGrid(node)

                            # set direction
                            if len(self.getAlignedNodes()) == 1:
                                self._cursor_trajectory = nodegraphutils.getCursorTrajectory(self.getCursorPoints()[0], self.getCursorPoints()[-1])

                            # iron node
                            if 0 < len(self.getAlignedNodes()):
                                from .gridLayer import (
                                    GRID_SIZE_X_PREF_NAME, GRID_SIZE_Y_PREF_NAME, ALIGN_X_OFFSET_PREF_NAME, ALIGN_Y_OFFSET_PREF_NAME)

                                offset_x = KatanaPrefs[GRID_SIZE_X_PREF_NAME] * KatanaPrefs[ALIGN_X_OFFSET_PREF_NAME]
                                offset_y = KatanaPrefs[GRID_SIZE_Y_PREF_NAME] * KatanaPrefs[ALIGN_Y_OFFSET_PREF_NAME]

                                if self.getCursorTrajectory() == nodegraphutils.RIGHT:
                                    xpos = self.getAlignXPos() + offset_x
                                    ypos = self.getAlignYPos()
                                if self.getCursorTrajectory() == nodegraphutils.LEFT:
                                    xpos = self.getAlignXPos() - offset_x
                                    ypos = self.getAlignYPos()
                                if self.getCursorTrajectory() == nodegraphutils.UP:
                                    xpos = self.getAlignXPos()
                                    ypos = self.getAlignYPos() + offset_y
                                if self.getCursorTrajectory() == nodegraphutils.DOWN:
                                    xpos = self.getAlignXPos()
                                    ypos = self.getAlignYPos() - offset_y

                                try:
                                    NodegraphAPI.SetNodePosition(node, (xpos, ypos))
                                except AttributeError:
                                    # node marked for deletion
                                    pass

                            self.getAlignedNodes().append(node)

                self.addCursorPoint(mouse_pos)


def showEvent(func):
    def __showEvent(self, event):
        # disable floating layer, as it for some reason inits as True...
        self.getLayerByName("Floating Nodes").setEnabled(False)

        # setup grid layer
        node_iron_layer = self.getLayerByName("Node Iron Layer")
        if not node_iron_layer:
            self._node_iron_layer = NodeIronLayer("Node Iron Layer", enabled=True)
            self.appendLayer(self._node_iron_layer)
        return func(self, event)

    return __showEvent


def installNodeIronLayer(**kwargs):
    nodegraph_panel = Tabs._LoadedTabPluginsByTabTypeName["Node Graph"].data(None)
    nodegraph_widget = nodegraph_panel.getNodeGraphWidget()
    nodegraph_widget.__class__.showEvent = showEvent(nodegraph_widget.__class__.showEvent)


# nodegraph_widget = UI4.App.Tabs.FindTopTab('Node Graph').getNodeGraphWidget()
# layer = NodeIronLayer("Test", enabled=True)
# nodegraph_widget.appendLayer(layer)

# nodegraph_widget = UI4.App.Tabs.FindTopTab('Node Graph').getNodeGraphWidget()
# test_layer = nodegraph_widget.getLayerByName("Test")
# nodegraph_widget.removeLayer(test_layer)
# nodegraph_widget.getLayers()
