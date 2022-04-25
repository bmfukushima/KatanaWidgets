from OpenGL.GL import GL_BLEND, glBegin, glColor4f, glDisable, glEnable, glEnd, glVertex2f, GL_POINTS, glPointSize, GL_TRIANGLES, glLineWidth
from qtpy.QtWidgets import QApplication
from qtpy.QtCore import Qt

# setup prefs
import QT4GLLayerStack

from Katana import NodegraphAPI
from Utils2 import nodegraphutils


class BackdropPreviewLayer(QT4GLLayerStack.Layer):
    def __init__(self, *args, **kwargs):
        (QT4GLLayerStack.Layer.__init__)(self, *args, **kwargs)

    @staticmethod
    def pickTriangleColor(quadrant_entered, quadrant_to_color):
        """ Determines the color that should be drawn"""
        if QApplication.keyboardModifiers() == Qt.AltModifier:
            if quadrant_entered == quadrant_to_color:
                glColor4f(0.5, 0.5, 1, 1)
            else:
                glColor4f(1, 1, 1, 0.2)

    def paintGL(self):
        # get attrs
        cam_x_pos = self.layerStack().getEyePoint()[0]
        cam_y_pos = self.layerStack().getEyePoint()[1]
        width = self.layerStack().width()
        height = self.layerStack().height()
        pos_x_offset = width * 0.5
        pos_y_offset = height * 0.5
        zoom = self.layerStack().getViewScale()[0]
        x_offset = pos_x_offset + (-cam_x_pos * zoom)
        y_offset = pos_y_offset + (-cam_y_pos * zoom)
        size = 30
        # create arbitrary point at nodegraph position 100, 100

        # get abkcdrop under cursor
        backdrop_node = nodegraphutils.getBackdropNodeUnderCursor()
        if not backdrop_node: return
        if self.layerStack().getLayerByName("Floating Nodes").enabled(): return

        quadrant = nodegraphutils.getBackdropQuadrantSelected(backdrop_node)

        attrs = backdrop_node.getAttributes()
        if "ns_sizeX" not in attrs:
            attrs["ns_sizeX"] = 128
        if "ns_sizeY" not in attrs:
            attrs["ns_sizeY"] = 64

        node_width = attrs["ns_sizeX"]
        node_height = attrs["ns_sizeY"]
        node_x_pos = NodegraphAPI.GetNodePosition(backdrop_node)[0] * zoom
        node_y_pos = NodegraphAPI.GetNodePosition(backdrop_node)[1] * zoom

        left = (NodegraphAPI.GetNodePosition(backdrop_node)[0] - (node_width * 0.5))
        right = (NodegraphAPI.GetNodePosition(backdrop_node)[0] + (node_width * 0.5))
        bottom = (NodegraphAPI.GetNodePosition(backdrop_node)[1] - (node_height * 0.5))
        top = (NodegraphAPI.GetNodePosition(backdrop_node)[1] + (node_height * 0.5))

        # draw point at location
        glEnable(GL_BLEND)
        glColor4f(1, 1, 1, 0.2)
        glPointSize(20)
        glLineWidth(2)
        glBegin(GL_TRIANGLES)

        # Draw top right
        BackdropPreviewLayer.pickTriangleColor(quadrant, nodegraphutils.TOPRIGHT)
        glVertex2f((zoom * right) + x_offset, (zoom * top) + y_offset)
        glVertex2f(zoom * (right - size) + x_offset, (zoom * top) + y_offset)
        glVertex2f((zoom * right) + x_offset, zoom * (top - size) + y_offset)

        # Draw top left
        BackdropPreviewLayer.pickTriangleColor(quadrant, nodegraphutils.TOPLEFT)
        glVertex2f((zoom * left) + x_offset, (zoom * top) + y_offset)
        glVertex2f(zoom * (left + size) + x_offset, (zoom * top) + y_offset)
        glVertex2f((zoom * left) + x_offset, zoom * (top - size) + y_offset)

        # Draw bot left
        BackdropPreviewLayer.pickTriangleColor(quadrant, nodegraphutils.BOTLEFT)
        glVertex2f((zoom * left) + x_offset, (zoom * bottom) + y_offset)
        glVertex2f(zoom * (left + size) + x_offset, (zoom * bottom) + y_offset)
        glVertex2f((zoom * left) + x_offset, zoom * (bottom + size) + y_offset)

        # Draw top right
        BackdropPreviewLayer.pickTriangleColor(quadrant, nodegraphutils.BOTRIGHT)
        glVertex2f((zoom * right) + x_offset, (zoom * bottom) + y_offset)
        glVertex2f(zoom * (right - size) + x_offset, (zoom * bottom) + y_offset)
        glVertex2f((zoom * right) + x_offset, zoom * (bottom + size) + y_offset)

        glEnd()

        # Draw center dot
        glColor4f(1, 1, 1, 0.2)
        glBegin(GL_POINTS)
        glVertex2f(
            node_x_pos + x_offset,
            node_y_pos + y_offset
        )

        glEnd()

        glDisable(GL_BLEND)