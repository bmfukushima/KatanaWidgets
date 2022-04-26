from OpenGL.GL import (
    GL_BLEND,
    glBegin,
    glColor4f,
    glDisable,
    glEnable,
    glEnd,
    glVertex2f,
    GL_POINTS,
    glPointSize,
    GL_TRIANGLES,
    glLineWidth,
    GL_LINES,
    GL_TRIANGLE_FAN
)
from qtpy.QtWidgets import QApplication
from qtpy.QtCore import Qt

# setup prefs
import QT4GLLayerStack

from Katana import NodegraphAPI, Utils
from Utils2 import nodegraphutils, widgetutils, nodeutils


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
        default_color = (0.5, 0.5, 0.5, 1)
        if QApplication.keyboardModifiers() == Qt.AltModifier:
            if quadrant_entered == quadrant_to_color:
                glColor4f(0.5, 0.5, 1, 1)
            elif quadrant_entered == nodegraphutils.CENTER:
                glColor4f(0.5, 0.5, 1, 1)
            else:
                glColor4f(*default_color)
        else:
            glColor4f(*default_color)

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
        node_x_pos = NodegraphAPI.GetNodePosition(backdrop_node)[0]
        node_y_pos = NodegraphAPI.GetNodePosition(backdrop_node)[1]

        width_offset = node_width / 3
        height_offset = node_height / 3

        left = (node_x_pos - (node_width * 0.5))
        right = (node_x_pos + (node_width * 0.5))
        bottom = (node_y_pos - (node_height * 0.5))
        top = (node_y_pos + (node_height * 0.5))

        # get indicator sizes
        indicator_x_size = node_width * 0.05
        indicator_y_size = node_height * 0.05
        i = 3
        ii = i * 2
        if indicator_x_size < 2 * ii:
            indicator_x_size = 2 * ii
        if indicator_y_size < 2 * ii:
            indicator_y_size = 2 * ii

        # draw point at location
        glEnable(GL_BLEND)
        glPointSize(20)
        glLineWidth(ii)

        # DRAW CENTER
        glBegin(GL_TRIANGLES)
        BackdropPreviewLayer.pickTriangleColor(quadrant, nodegraphutils.CENTER)
        # CENTER | TOP LEFT
        glVertex2f(zoom * (right - width_offset) + x_offset, zoom * (top - height_offset) + y_offset)
        glVertex2f(zoom * (right - width_offset - indicator_x_size) + x_offset, zoom * (top - height_offset) + y_offset)
        glVertex2f(zoom * (right - width_offset) + x_offset, zoom * (top - height_offset - indicator_y_size) + y_offset)

        # CENTER | TOP LEFT
        glVertex2f(zoom * (left + width_offset) + x_offset, zoom * (top - height_offset) + y_offset)
        glVertex2f(zoom * (left + width_offset + indicator_x_size) + x_offset, zoom * (top - height_offset) + y_offset)
        glVertex2f(zoom * (left + width_offset) + x_offset, zoom * (top - height_offset - indicator_y_size) + y_offset)

        # CENTER | BOT LEFT
        glVertex2f(zoom * (left + width_offset) + x_offset, zoom * (bottom + height_offset) + y_offset)
        glVertex2f(zoom * (left + width_offset + indicator_x_size) + x_offset, zoom * (bottom + height_offset) + y_offset)
        glVertex2f(zoom * (left + width_offset) + x_offset, zoom * (bottom + height_offset + indicator_y_size) + y_offset)

        # CENTER | BOT RIGHT
        glVertex2f(zoom * (right - width_offset) + x_offset, zoom * (bottom + height_offset) + y_offset)
        glVertex2f(zoom * (right - width_offset - indicator_x_size) + x_offset, zoom * (bottom + height_offset) + y_offset)
        glVertex2f(zoom * (right - width_offset) + x_offset, zoom * (bottom + height_offset + indicator_y_size) + y_offset)

        glEnd()

        # TOP RIGHT
        BackdropPreviewLayer.pickTriangleColor(quadrant, nodegraphutils.TOPRIGHT)
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(zoom * (right + i) + x_offset, zoom * (top + i) + y_offset)
        glVertex2f(zoom * (right - indicator_x_size) + x_offset, zoom * (top + i) + y_offset)
        glVertex2f(zoom * (right - indicator_x_size) + x_offset, zoom * (top - i) + y_offset)
        glVertex2f(zoom * (right - i) + x_offset, zoom * (top- i) + y_offset)
        glVertex2f(zoom * (right - i) + x_offset, zoom * (top - indicator_y_size) + y_offset)
        glVertex2f(zoom * (right + i) + x_offset, zoom * (top - indicator_y_size) + y_offset)
        glEnd()

        # TOP
        BackdropPreviewLayer.pickTriangleColor(quadrant, nodegraphutils.TOP)
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(zoom * (node_x_pos - indicator_x_size) + x_offset, zoom * (top + i) + y_offset)
        glVertex2f(zoom * (node_x_pos + indicator_x_size) + x_offset, zoom * (top + i) + y_offset)
        glVertex2f(zoom * (node_x_pos + indicator_x_size) + x_offset, zoom * (top - i) + y_offset)
        glVertex2f(zoom * (node_x_pos - indicator_x_size) + x_offset, zoom * (top - i) + y_offset)
        glEnd()

        # TOP LEFT
        BackdropPreviewLayer.pickTriangleColor(quadrant, nodegraphutils.TOPLEFT)
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(zoom * (left - i) + x_offset, zoom * (top + i) + y_offset)
        glVertex2f(zoom * (left + indicator_x_size) + x_offset, zoom * (top + i) + y_offset)
        glVertex2f(zoom * (left + indicator_x_size) + x_offset, zoom * (top - i) + y_offset)
        glVertex2f(zoom * (left + i) + x_offset, zoom * (top - i) + y_offset)
        glVertex2f(zoom * (left + i) + x_offset, zoom * (top - indicator_y_size) + y_offset)
        glVertex2f(zoom * (left - i) + x_offset, zoom * (top - indicator_y_size) + y_offset)
        glEnd()

        # LEFT
        BackdropPreviewLayer.pickTriangleColor(quadrant, nodegraphutils.LEFT)
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(zoom * (left - i) + x_offset, zoom * (node_y_pos - indicator_y_size) + y_offset)
        glVertex2f(zoom * (left + i) + x_offset, zoom * (node_y_pos - indicator_y_size) + y_offset)
        glVertex2f(zoom * (left + i) + x_offset, zoom * (node_y_pos + indicator_y_size) + y_offset)
        glVertex2f(zoom * (left - i) + x_offset, zoom * (node_y_pos + indicator_y_size) + y_offset)
        glEnd()

        # BOT LEFT
        BackdropPreviewLayer.pickTriangleColor(quadrant, nodegraphutils.BOTLEFT)
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(zoom * (left - i) + x_offset, zoom * (bottom - i) + y_offset)
        glVertex2f(zoom * (left + indicator_x_size) + x_offset, zoom * (bottom - i) + y_offset)
        glVertex2f(zoom * (left + indicator_x_size) + x_offset, zoom * (bottom + i) + y_offset)
        glVertex2f(zoom * (left + i) + x_offset, zoom * (bottom + i) + y_offset)
        glVertex2f(zoom * (left + i) + x_offset, zoom * (bottom + indicator_y_size) + y_offset)
        glVertex2f(zoom * (left - i) + x_offset, zoom * (bottom + indicator_y_size) + y_offset)
        glEnd()

        # BOT
        glBegin(GL_TRIANGLE_FAN)
        BackdropPreviewLayer.pickTriangleColor(quadrant, nodegraphutils.BOT)
        glVertex2f(zoom * (node_x_pos - indicator_x_size) + x_offset, zoom * (bottom + i) + y_offset)
        glVertex2f(zoom * (node_x_pos + indicator_x_size) + x_offset, zoom * (bottom + i) + y_offset)
        glVertex2f(zoom * (node_x_pos + indicator_x_size) + x_offset, zoom * (bottom - i) + y_offset)
        glVertex2f(zoom * (node_x_pos - indicator_x_size) + x_offset, zoom * (bottom - i) + y_offset)
        glEnd()

        # BOT RIGHT
        BackdropPreviewLayer.pickTriangleColor(quadrant, nodegraphutils.BOTRIGHT)
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(zoom * (right + i) + x_offset, zoom * (bottom - i) + y_offset)
        glVertex2f(zoom * (right - indicator_x_size) + x_offset, zoom * (bottom - i) + y_offset)
        glVertex2f(zoom * (right - indicator_x_size) + x_offset, zoom * (bottom + i) + y_offset)
        glVertex2f(zoom * (right - i) + x_offset, zoom * (bottom + i) + y_offset)
        glVertex2f(zoom * (right - i) + x_offset, zoom * (bottom + indicator_y_size) + y_offset)
        glVertex2f(zoom * (right + i) + x_offset, zoom * (bottom + indicator_y_size) + y_offset)
        glEnd()

        # RIGHT
        BackdropPreviewLayer.pickTriangleColor(quadrant, nodegraphutils.RIGHT)
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(zoom * (right - i) + x_offset, zoom * (node_y_pos - indicator_y_size) + y_offset)
        glVertex2f(zoom * (right + i) + x_offset, zoom * (node_y_pos - indicator_y_size) + y_offset)
        glVertex2f(zoom * (right + i) + x_offset, zoom * (node_y_pos + indicator_y_size) + y_offset)
        glVertex2f(zoom * (right - i) + x_offset, zoom * (node_y_pos + indicator_y_size) + y_offset)
        glEnd()

        # QUADRANT LINES
        glLineWidth(2)
        glColor4f(1, 1, 1, 0.2)
        glBegin(GL_LINES)

        glVertex2f(zoom * (left + width_offset) + x_offset, (zoom * top) + y_offset)
        glVertex2f(zoom * (left + width_offset) + x_offset, (zoom * bottom) + y_offset)

        glVertex2f(zoom * (right - width_offset) + x_offset, (zoom * top) + y_offset)
        glVertex2f(zoom * (right - width_offset) + x_offset, (zoom * bottom) + y_offset)

        glVertex2f((zoom * left) + x_offset, zoom * (top - height_offset) + y_offset)
        glVertex2f((zoom * right) + x_offset, zoom * (top - height_offset) + y_offset)

        glVertex2f((zoom * left) + x_offset, zoom * (bottom + height_offset) + y_offset)
        glVertex2f((zoom * right) + x_offset, zoom * (bottom + height_offset) + y_offset)
        glEnd()

        glLineWidth(1)
        glDisable(GL_BLEND)


def sortBackdropByArea(backdrop_list, sort_index=0):
    """ Simple bubble sort to sort the backdrops into ascending order by area"""
    # We set swapped to True so the loop looks runs at least once
    swapped = True
    while swapped:
        swapped = False
        for i in range(len(backdrop_list) - 1):
            if backdrop_list[i][sort_index] < backdrop_list[i + 1][sort_index]:
                # Swap the elements
                backdrop_list[i], backdrop_list[i + 1] = backdrop_list[i + 1], backdrop_list[i]
                # Set the flag to True so we'll loop again
                swapped = True

    return backdrop_list


def calculateBackdropZDepth(args):
    """ When a backdrop is placed, this will sort their zdepth by total area """
    for arg in args:
        if arg[0] == "node_setPosition":
            node = arg[2]['node']
            if node.getType() == "Backdrop":
                backdrop_nodes = nodegraphutils.getIntersectingBackdropNodes(node)

                # create a list of backdrop nodes ordered by total area
                backdrop_node_area_list = [(node, nodegraphutils.getBackdropArea(node))]
                for backdrop_node in backdrop_nodes:
                    backdrop_node_area_list.append((backdrop_node, nodegraphutils.getBackdropArea(backdrop_node)))
                backdrop_node_area_list = sortBackdropByArea(backdrop_node_area_list, 1)

                # set backdrops zdepth
                for i, item in enumerate(backdrop_node_area_list):
                    node = item[0]

                    # clone backdrops attrs
                    new_attrs = {}
                    for attr_name, attr_value in node.getAttributes().items():
                        if attr_name not in ["quadrant", "orig_cursor_pos", "selected"]:
                            new_attrs[attr_name.replace("ns_", "")] = attr_value

                    # update backdrops zdepth
                    new_attrs["zDepth"] = i + 1
                    nodegraphutils.updateBackdropDisplay(node, attrs=new_attrs)


def installBackdropZDepth(**kwargs):
    Utils.EventModule.RegisterCollapsedHandler(calculateBackdropZDepth, 'node_setPosition')