""" The Backdrop Layer is an additional OpenGL layered inserted into the NodeGraph Tab
This layer will allow the user to do advanced manipulations on backdrop nodes.

- `B` Create new backdrop
  - `LMB` Select backdrop and children
  - `Alt + LMB` Select and float backdrop and selected children
  - `Alt + Shift + LMB` Select and float backdrop and all children
  - `Ctrl + LMB` Select / Deselect backdrop
  - `Ctrl + Alt + LMB` Select and float backdrop
  - `Shift + LMB` Append/Remove backdrop and children to current selection
  - `Alt + RMB` Resize backdrop
"""
import math

from OpenGL.GL import (
    GL_BLEND,
    glBegin,
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
from qtpy.QtCore import Qt, QEvent
from qtpy.QtGui import QCursor

# setup prefs
from Katana import NodegraphAPI, Utils, PrefNames, KatanaPrefs, UI4, DrawingModule
from UI4.App import Tabs
import QT4GLLayerStack
from UI4.Tabs.NodeGraphTab.Layers.StickyNoteInteractionLayer import EditBackdropNodeDialog
from UI4.Tabs.NodeGraphTab.Layers.BandSelectionLayer import BandSelectionLayer

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
        if widgetutils.katanaMainWindow()._node_iron_active: return
        if widgetutils.katanaMainWindow()._link_cutting_active: return

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


def createBackdropNode(is_floating=False):
    """ Creates a backdrop node around the current selection"""
    Utils.UndoStack.OpenGroup("Create Backdrop")

    # get nodegraph
    nodegraph_widget = widgetutils.isCursorOverNodeGraphWidget()
    if not nodegraph_widget:
        nodegraph_widget = UI4.App.Tabs.FindTopTab('Node Graph').getNodeGraphWidget()

    # create backdrop and fit around selection
    current_group = nodegraph_widget.getCurrentNodeView()
    backdrop_node = NodegraphAPI.CreateNode("Backdrop", current_group)
    NodegraphAPI.SetNodeSelected(backdrop_node, True)
    nodegraph_widget.fitBackdropNode()

    # float if no nodes selected
    if len(NodegraphAPI.GetAllSelectedNodes()) == 1 or is_floating:
        nodegraph_widget.parent().floatNodes(NodegraphAPI.GetAllSelectedNodes())

    # prompt user for setting the node color
    def previewCallback(node, attr_dict):
        """ Callback run when the user updates a parameter in the backdrop node

        Args:
            node (Node): backdrop node to be updated
            attr_dict (dict): attributes to be updated
            """
        # get nodegraph
        nodegraph_widget = widgetutils.isCursorOverNodeGraphWidget()
        if not nodegraph_widget:
            nodegraph_widget = UI4.App.Tabs.FindTopTab('Node Graph').getNodeGraphWidget()

        for attrName, attrValue in attr_dict.items():
            DrawingModule.nodeWorld_setShapeAttr(node, attrName, attrValue)
            DrawingModule.nodeWorld_setShapeAttr(node, "update", 1)

            for layerStack in nodegraph_widget.getAllNodeGraphWidgets():
                layerStack.setNGVShapeAttrs(node, attr_dict)
            # this gives us live updates
            nodegraph_widget.idleUpdate()

    d = EditBackdropNodeDialog(backdrop_node, previewCallback=previewCallback)
    d.exec_()
    d.close()
    d.move(QCursor.pos())
    Utils.UndoStack.CloseGroup()


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

                # Need to reselect the backdrops as the get deselected somewhere in here
                # and I'm to lazy to actually figure this out
                selected_backdrops = []

                # set backdrops zdepth
                for i, item in enumerate(backdrop_node_area_list):
                    node = item[0]
                    updateBackdropZDepth(node)

                    # clone backdrops attrs
                    new_attrs = {}
                    if "selected" in node.getAttributes():
                        if node.getAttributes()["selected"]:
                            selected_backdrops.append(node)

                    nodegraphutils.selectNodes(selected_backdrops)


def resizeBackdropNode():
    """ Resizes the backdrop node when the user has done an Alt+RMB """
    # get attrs
    curr_cursor_pos, _ = nodegraphutils.getNodegraphCursorPos()
    orig_attrs = widgetutils.katanaMainWindow()._backdrop_orig_attrs
    if "name" not in orig_attrs: return

    node = NodegraphAPI.GetNode(orig_attrs["name"])
    orig_node_pos = (orig_attrs["x"], orig_attrs["y"])
    orig_cursor_pos = orig_attrs["orig_cursor_pos"]
    quadrant = orig_attrs["quadrant"]
    min_size = 100
    if "ns_sizeX" not in orig_attrs:
        orig_attrs["ns_sizeX"] = 128
    if "ns_sizeY" not in orig_attrs:
        orig_attrs["ns_sizeY"] = 64

    # setup attrs
    new_attrs = {}
    for attr_name, attr_value in orig_attrs.items():
        if attr_name not in ["quadrant", "orig_cursor_pos", "selected"]:
            new_attrs[attr_name.replace("ns_", "")] = attr_value

    # Get offset
    offset_x, offset_y = 0, 0
    if KatanaPrefs[PrefNames.NODEGRAPH_GRIDSNAP]:
        grid_pos = nodegraphutils.getNearestGridPoint(curr_cursor_pos.x(), curr_cursor_pos.y())
        if quadrant == nodegraphutils.TOPRIGHT:
            offset_x = grid_pos.x() - (orig_node_pos[0] + new_attrs["sizeX"] * 0.5)
            offset_y = grid_pos.y() - (orig_node_pos[1] + new_attrs["sizeY"] * 0.5)
        elif quadrant == nodegraphutils.TOP:
            offset_x = 0
            offset_y = grid_pos.y() - (orig_node_pos[1] + new_attrs["sizeY"] * 0.5)
        elif quadrant == nodegraphutils.TOPLEFT:
            offset_x = grid_pos.x() - (orig_node_pos[0] - new_attrs["sizeX"] * 0.5)
            offset_y = grid_pos.y() - (orig_node_pos[1] + new_attrs["sizeY"] * 0.5)
        elif quadrant == nodegraphutils.LEFT:
            offset_x = grid_pos.x() - (orig_node_pos[0] - new_attrs["sizeX"] * 0.5)
            offset_y = 0
        elif quadrant == nodegraphutils.BOTLEFT:
            offset_x = grid_pos.x() - (orig_node_pos[0] - new_attrs["sizeX"] * 0.5)
            offset_y = grid_pos.y() - (orig_node_pos[1] - new_attrs["sizeY"] * 0.5)
        elif quadrant == nodegraphutils.BOT:
            offset_x = 0
            offset_y = grid_pos.y() - (orig_node_pos[1] - new_attrs["sizeY"] * 0.5)
        elif quadrant == nodegraphutils.BOTRIGHT:
            offset_x = grid_pos.x() - (orig_node_pos[0] + new_attrs["sizeX"] * 0.5)
            offset_y = grid_pos.y() - (orig_node_pos[1] - new_attrs["sizeY"] * 0.5)
        elif quadrant == nodegraphutils.RIGHT:
            offset_x = grid_pos.x() - (orig_node_pos[0] + new_attrs["sizeX"] * 0.5)
            offset_y = 0
        elif quadrant == nodegraphutils.CENTER:
            # Todo update offset
            offset_x = grid_pos.x() - (orig_node_pos[0] + new_attrs["sizeX"] * 0.5)
            offset_y = grid_pos.y() - (orig_node_pos[1] + new_attrs["sizeY"] * 0.5)
    else:
        offset_x = curr_cursor_pos.x() - orig_cursor_pos.x()
        offset_y = curr_cursor_pos.y() - orig_cursor_pos.y()

    # update size
    if quadrant == nodegraphutils.TOPRIGHT:
        new_attrs["sizeX"] += offset_x
        new_attrs["sizeY"] += offset_y

    elif quadrant == nodegraphutils.TOP:
        new_attrs["sizeY"] += offset_y
        offset_x = 0

    elif quadrant == nodegraphutils.TOPLEFT:
        new_attrs["sizeX"] -= offset_x
        new_attrs["sizeY"] += offset_y

    elif quadrant == nodegraphutils.LEFT:
        new_attrs["sizeX"] -= offset_x
        offset_y = 0

    elif quadrant == nodegraphutils.BOTLEFT:
        new_attrs["sizeX"] -= offset_x
        new_attrs["sizeY"] -= offset_y

    elif quadrant == nodegraphutils.BOT:
        new_attrs["sizeY"] -= offset_y
        offset_x = 0

    elif quadrant == nodegraphutils.BOTRIGHT:
        new_attrs["sizeX"] += offset_x
        new_attrs["sizeY"] -= offset_y

    elif quadrant == nodegraphutils.RIGHT:
        new_attrs["sizeX"] += offset_x
        offset_y = 0

    elif quadrant == nodegraphutils.CENTER:
        new_attrs["sizeX"] += offset_x
        new_attrs["sizeY"] += offset_y

    # set min size
    if new_attrs["sizeX"] < min_size:
        new_attrs["sizeX"] = min_size
    if new_attrs["sizeY"] < min_size:
        new_attrs["sizeY"] = min_size

    # node pos
    if quadrant != nodegraphutils.CENTER:
        new_node_pos_x = orig_node_pos[0] + offset_x * 0.5
        new_node_pos_y = orig_node_pos[1] + offset_y * 0.5

        # check min size
        if new_attrs["sizeX"] == min_size:
            new_node_pos_x = NodegraphAPI.GetNodePosition(node)[0]
        if new_attrs["sizeY"] == min_size:
            new_node_pos_y = NodegraphAPI.GetNodePosition(node)[1]
        NodegraphAPI.SetNodePosition(node, (new_node_pos_x, new_node_pos_y))
    else:
        # todo setup node positioning for center
        # really only might need it for snapping?
        pass


    new_attrs["zDepth"] = 1 / (new_attrs["sizeX"] * new_attrs["sizeY"])

    nodegraphutils.updateBackdropDisplay(node, attrs=new_attrs)


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


def updateBackdropZDepth(backdrop_node):
    """ Updates the backdrop nodes zDepth based off of its area.

    The small the area, the larger the zDepth

    Args:
        backdrop_node (Node): backdrop node to be updated"""
    orig_attrs = backdrop_node.getAttributes()
    if "ns_sizeX" not in orig_attrs:
        orig_attrs["ns_sizeX"] = 128
    if "ns_sizeY" not in orig_attrs:
        orig_attrs["ns_sizeY"] = 64

    # clone backdrops attrs
    new_attrs = {}
    for attr_name, attr_value in orig_attrs.items():
        if attr_name not in ["quadrant", "orig_cursor_pos", "selected"]:
            new_attrs[attr_name.replace("ns_", "")] = attr_value

    area = orig_attrs["ns_sizeX"] * orig_attrs["ns_sizeY"]
    new_attrs["zDepth"] = 1 / area

    nodegraphutils.updateBackdropDisplay(backdrop_node, attrs=new_attrs)


""" EVENTS (Backdrop)"""
def backdropInteractionEvent(func):
    """ Overrides the process event for the sticky note interaction layer """
    def __backdropInteractionEvent(self, event):
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton and event.modifiers() == Qt.ControlModifier:
                backdrop_node = nodegraphutils.getBackdropNodeUnderCursor()
                if backdrop_node:
                    NodegraphAPI.SetNodeSelected(backdrop_node, not NodegraphAPI.IsNodeSelected(backdrop_node))
                return True
        return func(self, event)

    return __backdropInteractionEvent


""" EVENTS (Node Interaction)"""
def nodeInteractionEvent(func):
    """ Each event type requires calling its own private methods
    Doing this will probably just obfuscate the shit out of the code...
    """
    def __nodeInteractionEvent(self, event):
        if event.type() == QEvent.MouseButtonPress:
            if nodeInteractionMousePressEvent(self, event): return True
        if event.type() == QEvent.MouseButtonRelease:
            if nodeInteractionMouseReleaseEvent(self, event): return True
        if event.type() == QEvent.MouseMove:
            if nodeInteractionMouseMoveEvent(self, event): return True
        return func(self, event)

    return __nodeInteractionEvent


def nodeInteractionMouseMoveEvent(self, event):
    # resize backdrop
    if event.modifiers() == Qt.AltModifier and event.buttons() == Qt.RightButton:
        resizeBackdropNode()

    # determine if backdrop click was a click, or click + move
    """ Click move will launch the band selection layer"""
    if hasattr(widgetutils.katanaMainWindow(), "_nodegraph_click_pos"):
        p0 = widgetutils.katanaMainWindow()._nodegraph_click_pos
        p1 = self.layerStack().getMousePos()
        magnitude = math.sqrt(
              math.pow(p0.x() - p1.x(), 2)
            + math.pow(p0.y() - p1.y(), 2)
        )

        if 30 < magnitude:
            mouse_pos = self.layerStack().mapFromQTLocalToWorld(event.x(), event.y())
            if event.modifiers() == Qt.NoModifier:
                self.layerStack().appendLayer(BandSelectionLayer(mouse_pos, False, enabled=True))
            if event.modifiers() == Qt.ShiftModifier:
                self.layerStack().appendLayer(BandSelectionLayer(mouse_pos, True, enabled=True))

            delattr(widgetutils.katanaMainWindow(), "_nodegraph_click_pos")

    return False


def nodeInteractionMousePressEvent(self, event):
    """ Need to by pass for special functionality for backdrops"""
    backdrop_node = nodegraphutils.getBackdropNodeUnderCursor()
    if backdrop_node:
        # move backdrop
        # Select backdrop and children OR start band selection
        if event.modifiers() in [Qt.NoModifier, Qt.ShiftModifier] and event.button() == Qt.LeftButton:
            # check to make sure the user didn't hit a node, if they hit a node, do default behavior
            if nodegraphutils.nodeClicked(self.layerStack()): return False
            if nodegraphutils.getCurrentKeyPressed() == Qt.Key_A: return False
            widgetutils.katanaMainWindow()._nodegraph_click_pos = self.layerStack().getMousePos()
            return True

        if event.modifiers() == Qt.ControlModifier and event.button() == Qt.LeftButton:
            # this is now handled on the StickyNoteInteractionLayer
            return True

        # move backdrop and selected children
        if event.modifiers() == Qt.AltModifier and event.button() == Qt.LeftButton:
            backdrop_children = nodegraphutils.getBackdropChildren(backdrop_node)
            selected_nodes = [backdrop_node]
            for child in backdrop_children:
                if NodegraphAPI.IsNodeSelected(child):
                    selected_nodes.append(child)

            nodegraphutils.selectNodes(selected_nodes, is_exclusive=True)
            nodegraphutils.floatNodes(selected_nodes)
            return True

        # pickup node and children
        if event.modifiers() == (Qt.AltModifier | Qt.ShiftModifier) and event.button() == Qt.LeftButton:
            nodes_to_move = nodegraphutils.getBackdropChildren(backdrop_node)
            nodegraphutils.selectNodes(nodes_to_move, is_exclusive=True)
            nodegraphutils.floatNodes(nodes_to_move)
            return True

        # duplicate backdrop and children
        if event.modifiers() == (Qt.ControlModifier | Qt.AltModifier) and event.button() == Qt.LeftButton:
            nodegraphutils.selectNodes([backdrop_node], is_exclusive=True)
            nodegraphutils.floatNodes([backdrop_node])
            return True

        # duplicate backdrop and children
        if event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier) and event.button() == Qt.LeftButton:

            nodes_to_duplicate = nodegraphutils.getBackdropChildren(backdrop_node)
            nodegraphutils.duplicateNodes(self, nodes_to_duplicate=nodes_to_duplicate)
            return True

        # initialize backdrop resize event
        if event.modifiers() == Qt.AltModifier and event.button() == Qt.RightButton:
            quadrant = nodegraphutils.getBackdropQuadrantSelected(backdrop_node)
            attrs = backdrop_node.getAttributes()
            attrs["quadrant"] = quadrant
            attrs["orig_cursor_pos"] = nodegraphutils.getNodegraphCursorPos()[0]
            widgetutils.katanaMainWindow()._backdrop_orig_attrs = attrs
            widgetutils.katanaMainWindow()._backdrop_resize_active = True
            nodeutils.removeNodePreviewColors()
            return True

    return False


def nodeInteractionMouseReleaseEvent(self, event):
    # reset backdrop attrs
    if widgetutils.katanaMainWindow()._backdrop_resize_active:
        widgetutils.katanaMainWindow()._backdrop_resize_active = False

    # backdrop click handler
    if hasattr(widgetutils.katanaMainWindow(), "_nodegraph_click_pos"):
        # If node clicked, bypass
        if nodegraphutils.nodeClicked(self.layerStack()): return False

        backdrop_node = nodegraphutils.getBackdropNodeUnderCursor()
        if event.modifiers() == Qt.NoModifier and event.button() == Qt.LeftButton:
            nodes_to_select = nodegraphutils.getBackdropChildren(backdrop_node)
            nodegraphutils.selectNodes(nodes_to_select, is_exclusive=True)

        if event.modifiers() == Qt.ShiftModifier and event.button() == Qt.LeftButton:
            if NodegraphAPI.IsNodeSelected(backdrop_node):
                nodes_to_deselect = nodegraphutils.getBackdropChildren(backdrop_node)
                for node in nodes_to_deselect:
                    NodegraphAPI.SetNodeSelected(node, False)

            else:
                nodes_to_select = nodegraphutils.getBackdropChildren(backdrop_node)
                nodegraphutils.selectNodes(nodes_to_select)

        delattr(widgetutils.katanaMainWindow(), "_nodegraph_click_pos")
    # update view
    self.layerStack().idleUpdate()
    return False


def showEvent(func):
    def __showEvent(self, event):
        # disable floating layer, as it for some reason inits as True...
        self.getLayerByName("Floating Nodes").setEnabled(False)

        # setup grid layer
        backdrop_preview_layer = self.getLayerByName("Backdrop Preview Layer")
        if not backdrop_preview_layer:
            self._backdrop_preview_layer = BackdropPreviewLayer("Backdrop Preview Layer", enabled=True)

            self.appendLayer(self._backdrop_preview_layer)
        return func(self, event)

    return __showEvent


def installBackdropLayer(**kwargs):
    nodegraph_panel = Tabs._LoadedTabPluginsByTabTypeName["Node Graph"].data(None)
    nodegraph_widget = nodegraph_panel.getNodeGraphWidget()
    nodegraph_widget.__class__.showEvent = showEvent(nodegraph_widget.__class__.showEvent)

    # NORMAL NODEGRAPH
    node_interaction_layer = nodegraph_widget.getLayerByName("NodeInteractions")
    node_interaction_layer.__class__.processEvent = nodeInteractionEvent(node_interaction_layer.__class__.processEvent)

    # NETWORK MATERIAL
    nodegraph_view_interaction_layer = nodegraph_widget.getLayerByName("NodeGraphViewInteraction")
    nodegraph_view_interaction_layer.__class__.processEvent = nodeInteractionEvent(nodegraph_view_interaction_layer.__class__.processEvent)

    # override interactions
    backdrop_interaction_layer = nodegraph_widget.getLayerByName("Backdrop Node Interaction")
    backdrop_interaction_layer.__class__.processEvent = backdropInteractionEvent(backdrop_interaction_layer.__class__.processEvent)

    Utils.EventModule.RegisterCollapsedHandler(calculateBackdropZDepth, 'node_setPosition')