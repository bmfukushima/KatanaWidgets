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
from .AbstractGestureLayer import AbstractGestureLayer, insertLayerIntoNodegraph


LAYER_NAME = "Link Cutting Layer"
ATTR_NAME = "_link_cutting"


class LinkCuttingLayer(AbstractGestureLayer):
    """

    Attributes:
        cursor_trajectory (LinkCuttingLayer.DIRECTION): direction to position the nodes
        last_cursor_points (list): of QPoints that hold the last 5 cursor positions
            This is used for calculating the cursors trajectory
        _link_cutting_active (bool): determines if this event is active or not
        _link_cutting_finishing (bool): determines if the link cutting event is finishing
            This is useful to differentiate between a C+LMB and a C-Release event
    """

    def __init__(self, *args, **kwargs):
        super(LinkCuttingLayer, self).__init__(
            *args,
            attr_name=ATTR_NAME,
            actuation_key=Qt.Key_X,
            undo_name="Slice Links",
            **kwargs)

    def keyReleaseEvent(self, event):
        if event.isAutoRepeat(): return True
        if event.key() == Qt.Key_X and event.modifiers() == Qt.NoModifier:
            if not widgetutils.katanaMainWindow()._link_cutting_finishing:
                self.layerStack().extractNodes(NodegraphAPI.GetAllSelectedNodes())
                nodegraphutils.floatNodes(NodegraphAPI.GetAllSelectedNodes())
            nodegraphutils.setCurrentKeyPressed(None)
            return True

        return False

    def paintGL(self):
        if self.isActive():
            # create point on cursor
            mouse_pos = self.layerStack().getMousePos()
            # align nodes
            if mouse_pos:
                # draw crosshair
                self.drawCrosshair()
                self.drawTrajectory()

                # cut links
                if 0 < len(self.getCursorPoints()):
                    hit_points = nodegraphutils.interpolatePoints(self.getCursorPoints()[-1], mouse_pos, radius=self.crosshairRadius(), step_size=5)
                    link_hits = nodegraphutils.pointsHitTestNode(hit_points, self.layerStack(), hit_type=nodegraphutils.LINK)
                    for link in link_hits:
                        link[0].disconnect(link[1])

                self.addCursorPoint(mouse_pos)


def installLinkCuttingLayer(**kwargs):
    insertLayerIntoNodegraph(LinkCuttingLayer, LAYER_NAME, ATTR_NAME, Qt.Key_X)