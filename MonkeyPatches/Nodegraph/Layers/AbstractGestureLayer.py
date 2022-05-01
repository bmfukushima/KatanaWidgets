from OpenGL.GL import (
    glBegin,
    glLineWidth,
    GL_POINTS,
    GL_LINES,
    glRotatef,
    GL_LINE_LOOP,
    GL_LINE_STRIP,
    glColor4f,
    glEnd,
    glVertex2f,
    glPointSize,
)
from qtpy.QtWidgets import QApplication
from qtpy.QtCore import Qt, QPoint, QEvent, QTimer

import QT4GLLayerStack
from UI4.App import Tabs

from Utils2 import nodegraphutils, widgetutils

class AbstractGestureLayer(QT4GLLayerStack.Layer):
    """

    Attributes:
        color (RGBA0-1) Tuple of rgba 0-1 values
        crosshair_radius (int): radius of crosshair
        cursor_trajectory (LinkCuttingLayer.DIRECTION): direction to position the nodes
        last_cursor_points (list): of QPoints that hold the last 5 cursor positions
            This is used for calculating the cursors trajectory
        _link_cutting_active (bool): determines if this event is active or not
        _link_cutting_finishing (bool): determines if the link cutting event is finishing
            This is useful to differentiate between a C+LMB and a C-Release event
    """

    def __init__(self, *args, **kwargs):
        (QT4GLLayerStack.Layer.__init__)(self, *args, **kwargs)
        self._cursor_trajectory = nodegraphutils.RIGHT
        self._last_cursor_points = []
        self._crosshair_radius = 10
        self._color = (0.75, 0.75, 1, 1)

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

        Returns (LinkCuttingLayer.DIRECTION)"""

        return self._cursor_trajectory

    def color(self):
        return self._color

    def setColor(self, color):
        self._color = color

    def crosshairRadius(self):
        return self._crosshair_radius

    def setCrosshairRadius(self, crosshair_radius):
        self._crosshair_radius = crosshair_radius

    def drawCrosshair(self):

        glColor4f(*self.color())
        glLineWidth(2)

        mouse_pos = self.layerStack().getMousePos()
        window_pos = QPoint(mouse_pos.x(), self.layerStack().getWindowSize()[1] - mouse_pos.y())
        glBegin(GL_LINE_LOOP)
        glVertex2f(window_pos.x() - self.crosshairRadius(), window_pos.y())
        glVertex2f(window_pos.x(), window_pos.y() + self.crosshairRadius())
        glVertex2f(window_pos.x() + self.crosshairRadius(), window_pos.y())
        glVertex2f(window_pos.x(), window_pos.y() - self.crosshairRadius())
        glEnd()

    def drawTrajectory(self):
        glColor4f(*self.color())
        glLineWidth(2)

        # get trajectory
        if 0 < len(self.getCursorPoints()):
            glBegin(GL_LINE_STRIP)
            for point in self.getCursorPoints():
                glVertex2f(point.x(), self.layerStack().getWindowSize()[1] - point.y())
            glEnd()


def insertLayerIntoNodegraph(layer, layer_name, attr_name):
    """ Returns a function that can be used to override the NodegraphWidgets show function
    automatically insert the layer provided into the NodegraphTab

    Args:
        layer (AbstractGestureLayer): class of laye to be inserted
        layer_name (str): name of layer
        attr_name (str): name of attr to store the layer as on the NodegraphWidget
        """
    def showEvent(func):
        def __showEvent(self, event):
            # disable floating layer, as it for some reason inits as True...
            self.getLayerByName("Floating Nodes").setEnabled(False)

            # setup grid layer
            node_iron_layer = self.getLayerByName(layer_name)
            if not node_iron_layer:
                setattr(self, attr_name, layer(layer_name, enabled=True))
                self.appendLayer(getattr(self, attr_name))

            return func(self, event)

        return __showEvent

    nodegraph_panel = Tabs._LoadedTabPluginsByTabTypeName["Node Graph"].data(None)
    nodegraph_widget = nodegraph_panel.getNodeGraphWidget()
    nodegraph_widget.__class__.showEvent = showEvent(nodegraph_widget.__class__.showEvent)

    return showEvent
