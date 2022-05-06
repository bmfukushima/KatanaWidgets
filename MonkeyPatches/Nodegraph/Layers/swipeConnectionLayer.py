""" The iron node layer allows users to "iron" their nodes

As the user swipes through nodes using CTRL+ALT+SHIFT+LMB, all
of the nodes hit will be aligned to the first node, based off
of the direction of the cursor as it passed through the second node.

"""
import math

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

# setup prefs
import QT4GLLayerStack
from Katana import NodegraphAPI, Utils, PrefNames, KatanaPrefs, UI4
from UI4.App import Tabs
from Utils2 import nodegraphutils, widgetutils, nodeutils
from .AbstractGestureLayer import (
    AbstractGestureLayer,
    insertLayerIntoNodegraph)


LAYER_NAME = "Swipe Connection Layer"
ATTR_NAME = "_swipe_connection"

class SwipeConnectionLayer(AbstractGestureLayer):
    """
    Attributes:
        cursor_trajectory (SwipeConnectionLayer.DIRECTION): direction to position the nodes
        last_cursor_points (list): of QPoints that hold the last 5 cursor positions
            This is used for calculating the cursors trajectory
        _swipe_connection_active (bool): determines if this event is active or not
        _swipe_connection_finishing (bool): determines if the link cutting event is finishing
            This is useful to differentiate between a C+LMB and a C-Release event
    """

    def __init__(self, *args, **kwargs):
        super(SwipeConnectionLayer, self).__init__(*args, **kwargs)

    def paintGL(self):
        if self.isActive():
            # create point on cursor
            mouse_pos = self.layerStack().getMousePos()
            # align nodes
            if mouse_pos:
                self.drawCrosshair()
                self.drawTrajectory()

                # connect nodes
                if 0 < len(self.getCursorPoints()):
                    hit_points = nodegraphutils.interpolatePoints(self.getCursorPoints()[-1], mouse_pos, radius=self.crosshairRadius(), step_size=5)
                    node_hits = nodegraphutils.pointsHitTestNode(hit_points, self.layerStack(), hit_type=nodegraphutils.NODE)
                    for node in node_hits:
                        if len(self.getHits()) == 0:
                            self.addHit(node)
                        elif node not in self.getHits():
                            input_port = nodeutils.getFirstEmptyPort(node, force_create=True)
                            if input_port:
                                input_port.connect(self.getHits()[-1].getOutputPortByIndex(0))
                            else:
                                self.getHits()[-1].getOutputPortByIndex(0).connect(node.getInputPortByIndex(0))
                            self.addHit(node)

                self.addCursorPoint(mouse_pos)


def installSwipeConnectionLayer(**kwargs):
    insertLayerIntoNodegraph(SwipeConnectionLayer, LAYER_NAME, ATTR_NAME, Qt.Key_C, "Connect Nodes")
