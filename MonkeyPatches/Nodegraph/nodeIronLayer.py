""" Todo
        - How to release nodes from list? Pen up not working?
        - Direction from node --> cursor?
"""
import math

from OpenGL.GL import (
    GL_BLEND,
    glClear,
    glBegin,
    GL_POINTS,
    glColor4f,
    glDisable,
    glEnable,
    glEnd,
    glVertex2f,
    glPointSize,
    GL_TRIANGLES,
    glLineWidth,
    GL_LINES,
    GL_TRIANGLE_FAN
)
from qtpy.QtWidgets import QApplication
from qtpy.QtCore import Qt, QPoint, QEvent, QTimer

# setup prefs
import QT4GLLayerStack
from Katana import NodegraphAPI, Utils, PrefNames, KatanaPrefs, UI4
from UI4.App import Tabs
from Utils2 import nodegraphutils, widgetutils, nodeutils


class NodeIronLayer(QT4GLLayerStack.Layer):
    LEFT = "left"
    DOWN = "down"
    RIGHT = "right"
    UP = "up"
    def __init__(self, *args, **kwargs):
        (QT4GLLayerStack.Layer.__init__)(self, *args, **kwargs)
        self._aligned_nodes = []
        self._cursor_direction = NodeIronLayer.RIGHT
        self._last_cursor_points = []

    def processEvent(self, event):
        if event.type() == QEvent.MouseButtonRelease:
            print("release??")
            print("aligned nodes ==", self._aligned_nodes)
            nodegraphutils.floatNodes(self._aligned_nodes)
            self._aligned_nodes = []
            self._cursor_direction = NodeIronLayer.RIGHT
            self._last_cursor_points = []
            return True

        return False

    def getAlignXPos(self):
        return NodegraphAPI.GetNodePosition(self._aligned_nodes[-1])[0]

    def getAlignYPos(self):
        return NodegraphAPI.GetNodePosition(self._aligned_nodes[-1])[1]

    def getCursorPoints(self):
        return self._last_cursor_points

    def getCursorDirection(self):
        """ Returns the direction that the cursor is currently travelling

        Returns (NodeIronLayer.DIRECTION)"""
        direction = NodeIronLayer.RIGHT
        if 1 < len(self.getCursorPoints()):
            p0 = self.getCursorPoints()[0]
            p1 = self.getCursorPoints()[-1]
            y_offset = p0.y() - p1.y()
            x_offset = p0.x() - p1.x()
            # cursor travelling left/right
            if math.fabs(y_offset) < math.fabs(x_offset):
                if x_offset < 0:
                    direction = NodeIronLayer.RIGHT
                elif 0 < x_offset:
                    direction = NodeIronLayer.LEFT

            # cursor travelling up/down
            if math.fabs(x_offset) < math.fabs(y_offset):
                if y_offset < 0:
                    direction = NodeIronLayer.UP
                elif 0 < y_offset:
                    direction = NodeIronLayer.DOWN

        return direction

    def updateCursorDirection(self):
        """
        stores the last time/pos coordinates of the mouse move
        prior to it hitting the first node.
        """
        trajectory_list = self._last_cursor_points
        mouse_pos = self.layerStack().getMousePos()
        nodegraph_pos = QPoint(*self.layerStack().mapFromQTLocalToWorld(mouse_pos.x(), mouse_pos.y()))
        trajectory_list.append(nodegraph_pos)

        if 5 < len(self._last_cursor_points):
            self._last_cursor_points = self._last_cursor_points[-5:]

    def paintGL(self):
        if QApplication.keyboardModifiers() == (Qt.ControlModifier | Qt.AltModifier | Qt.ShiftModifier):
            if QApplication.mouseButtons() == Qt.LeftButton:
                # create point on cursor
                mouse_pos = self.layerStack().getMousePos()

                # align nodes
                if mouse_pos:
                    window_pos = QPoint(mouse_pos.x(), self.layerStack().getWindowSize()[1]-mouse_pos.y())
                    self.updateCursorDirection()
                    # draw crosshair
                    radius = 10
                    glColor4f(0.5, 0.5, 1, 1)
                    glPointSize(radius * 2)
                    glBegin(GL_POINTS)
                    glVertex2f(window_pos.x(), window_pos.y())
                    glEnd()

                    # iron nodes
                    nodegraph_pos = self.layerStack().mapFromQTLocalToWorld(mouse_pos.x(), mouse_pos.y())

                    hits = self.layerStack().hitTestPoint(nodegraph_pos)
                    for hit in hits:
                        for node in hit[1].values():
                            if node.getType() != "Backdrop":
                                # first node
                                print(self._aligned_nodes)
                                if node not in self._aligned_nodes:
                                    if len(self._aligned_nodes) == 0:
                                        if KatanaPrefs[PrefNames.NODEGRAPH_GRIDSNAP]:
                                            from Utils2.nodealignutils import AlignUtils
                                            AlignUtils().snapNodeToGrid(node)

                                    if 0 < len(self._aligned_nodes):
                                        from .gridLayer import (
                                            GRID_SIZE_X_PREF_NAME, GRID_SIZE_Y_PREF_NAME, ALIGN_X_OFFSET_PREF_NAME, ALIGN_Y_OFFSET_PREF_NAME)
                                        # GRID_SIZE_X_PREF_NAME = "nodegraph/grid/sizeX"
                                        # GRID_SIZE_Y_PREF_NAME = "nodegraph/grid/sizeY"
                                        # ALIGN_X_OFFSET_PREF_NAME = "nodegraph/grid/alignXOffset"
                                        # ALIGN_Y_OFFSET_PREF_NAME = "nodegraph/grid/alignYOffset"
                                        offset_x = KatanaPrefs[GRID_SIZE_X_PREF_NAME] * KatanaPrefs[ALIGN_X_OFFSET_PREF_NAME]
                                        offset_y = KatanaPrefs[GRID_SIZE_Y_PREF_NAME] * KatanaPrefs[ALIGN_Y_OFFSET_PREF_NAME]

                                        if self.getCursorDirection() == NodeIronLayer.RIGHT:
                                            xpos = self.getAlignXPos() + offset_x
                                            ypos = self.getAlignYPos()
                                        if self.getCursorDirection() == NodeIronLayer.LEFT:
                                            xpos = self.getAlignXPos() - offset_x
                                            ypos = self.getAlignYPos()
                                        if self.getCursorDirection() == NodeIronLayer.UP:
                                            xpos = self.getAlignXPos()
                                            ypos = self.getAlignYPos() + offset_y
                                        if self.getCursorDirection() == NodeIronLayer.DOWN:
                                            xpos = self.getAlignXPos()
                                            ypos = self.getAlignYPos() - offset_y

                                        try:
                                            NodegraphAPI.SetNodePosition(node, (xpos, ypos))
                                        except AttributeError:
                                            # node marked for deletion
                                            pass

                                    self._aligned_nodes.append(node)

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
