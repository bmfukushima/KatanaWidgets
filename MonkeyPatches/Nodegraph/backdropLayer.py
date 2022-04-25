from OpenGL.GL import GL_BLEND, glBegin, glColor4f, glDisable, glEnable, glEnd, glVertex2f, GL_POINTS, glPointSize, GL_TRIANGLES, glLineWidth, GL_LINES
from qtpy.QtWidgets import QApplication
from qtpy.QtCore import Qt

# setup prefs
import QT4GLLayerStack

from Katana import NodegraphAPI, Utils
from Utils2 import nodegraphutils, widgetutils


class BackdropPreviewLayer(QT4GLLayerStack.Layer):
    def __init__(self, *args, **kwargs):
        (QT4GLLayerStack.Layer.__init__)(self, *args, **kwargs)
        if not hasattr(widgetutils.katanaMainWindow(), "_backdrop_resize_active"):
            widgetutils.katanaMainWindow()._backdrop_resize_active = False
        if not hasattr(widgetutils.katanaMainWindow(), "_backdrop_orig_attrs"):
            widgetutils.katanaMainWindow()._backdrop_orig_attrs = {}
    @staticmethod
    def pickTriangleColor(quadrant_entered, quadrant_to_color):
        """ Determines the color that should be drawn"""
        if QApplication.keyboardModifiers() == Qt.AltModifier:
            if quadrant_entered == quadrant_to_color:
                glColor4f(0.5, 0.5, 1, 1)
            elif quadrant_entered == nodegraphutils.CENTER:
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
        resize_active = widgetutils.katanaMainWindow()._backdrop_resize_active
        resize_backdrop_attrs = widgetutils.katanaMainWindow()._backdrop_orig_attrs

        # get backdrop under cursor
        backdrop_node = nodegraphutils.getBackdropNodeUnderCursor()

        if not backdrop_node and not resize_active: return
        if self.layerStack().getLayerByName("Floating Nodes").enabled(): return

        # This will be hit during resize events, and the cursor is no longer hovering over the backdrop node
        # determine quadrant
        if resize_active:
            quadrant = resize_backdrop_attrs["quadrant"]
            backdrop_node = NodegraphAPI.GetNode(resize_backdrop_attrs["name"])
        else:
            quadrant = nodegraphutils.getBackdropQuadrantSelected(backdrop_node)

        # setup default sizes
        attrs = backdrop_node.getAttributes()
        if "ns_sizeX" not in attrs:
            attrs["ns_sizeX"] = 128
        if "ns_sizeY" not in attrs:
            attrs["ns_sizeY"] = 64

        # get backdrop sizes
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

        # Draw top right
        glBegin(GL_TRIANGLES)
        BackdropPreviewLayer.pickTriangleColor(quadrant, nodegraphutils.TOPRIGHT)
        glVertex2f((zoom * right) + x_offset, (zoom * top) + y_offset)
        glVertex2f(zoom * (right - size) + x_offset, (zoom * top) + y_offset)
        glVertex2f((zoom * right) + x_offset, zoom * (top - size) + y_offset)
        glEnd()

        # Draw Top
        BackdropPreviewLayer.pickTriangleColor(quadrant, nodegraphutils.TOP)
        glBegin(GL_POINTS)
        glVertex2f(node_x_pos + x_offset, (zoom * top) + y_offset)
        glEnd()

        # Draw top left
        glBegin(GL_TRIANGLES)
        BackdropPreviewLayer.pickTriangleColor(quadrant, nodegraphutils.TOPLEFT)
        glVertex2f((zoom * left) + x_offset, (zoom * top) + y_offset)
        glVertex2f(zoom * (left + size) + x_offset, (zoom * top) + y_offset)
        glVertex2f((zoom * left) + x_offset, zoom * (top - size) + y_offset)
        glEnd()

        # Draw Left
        BackdropPreviewLayer.pickTriangleColor(quadrant, nodegraphutils.LEFT)
        glBegin(GL_POINTS)
        glVertex2f((zoom * left) + x_offset, node_y_pos + y_offset)
        glEnd()

        # Draw bot left
        glBegin(GL_TRIANGLES)
        BackdropPreviewLayer.pickTriangleColor(quadrant, nodegraphutils.BOTLEFT)
        glVertex2f((zoom * left) + x_offset, (zoom * bottom) + y_offset)
        glVertex2f(zoom * (left + size) + x_offset, (zoom * bottom) + y_offset)
        glVertex2f((zoom * left) + x_offset, zoom * (bottom + size) + y_offset)
        glEnd()

        # draw bot
        BackdropPreviewLayer.pickTriangleColor(quadrant, nodegraphutils.BOT)
        glBegin(GL_POINTS)
        glVertex2f(node_x_pos + x_offset, (zoom * bottom) + y_offset)
        glEnd()

        # Draw bot right
        glBegin(GL_TRIANGLES)
        BackdropPreviewLayer.pickTriangleColor(quadrant, nodegraphutils.BOTRIGHT)
        glVertex2f((zoom * right) + x_offset, (zoom * bottom) + y_offset)
        glVertex2f(zoom * (right - size) + x_offset, (zoom * bottom) + y_offset)
        glVertex2f((zoom * right) + x_offset, zoom * (bottom + size) + y_offset)
        glEnd()

        # draw right
        BackdropPreviewLayer.pickTriangleColor(quadrant, nodegraphutils.RIGHT)
        glBegin(GL_POINTS)
        glVertex2f((zoom * right) + x_offset, node_y_pos+ y_offset)
        glEnd()

        # Draw center dot
        BackdropPreviewLayer.pickTriangleColor(quadrant, nodegraphutils.CENTER)
        glBegin(GL_POINTS)
        glVertex2f(
            node_x_pos + x_offset,
            node_y_pos + y_offset
        )
        glEnd()

        # draw quadrant lines
        glLineWidth(2)
        glColor4f(1, 1, 1, 0.2)
        glBegin(GL_LINES)

        width_offset = node_width / 3
        height_offset = node_height / 3
        glVertex2f(zoom * (left + width_offset) + x_offset, (zoom * top) + y_offset)
        glVertex2f(zoom * (left + width_offset) + x_offset, (zoom * bottom) + y_offset)

        glVertex2f(zoom * (right - width_offset) + x_offset, (zoom * top) + y_offset)
        glVertex2f(zoom * (right - width_offset) + x_offset, (zoom * bottom) + y_offset)

        glVertex2f((zoom * left) + x_offset, zoom * (top - height_offset) + y_offset)
        glVertex2f((zoom * right) + x_offset, zoom * (top - height_offset) + y_offset)

        glVertex2f((zoom * left) + x_offset, zoom * (bottom + height_offset) + y_offset)
        glVertex2f((zoom * right) + x_offset, zoom * (bottom + height_offset) + y_offset)
        glEnd()

        glDisable(GL_BLEND)


def calculateBackdropZDepth(args):
    for arg in args:
        if arg[0] == "node_setPosition":
            node = arg[2]['node']
            if node.getType() == "Backdrop":
                # get intersecting backdrops
                #
                print(node)


def installBackdropZDepth(**kwargs):
    Utils.EventModule.RegisterCollapsedHandler(calculateBackdropZDepth, 'node_setPosition')