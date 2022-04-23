""" Todo:
        - Ladder Delegate... This has been broken forever...
        - Store grid settings for reuse?
                Store attributes in this file?
                Will get reset every time...
        - Document...
"""

import inspect
from qtpy.QtWidgets import QWidget, QHBoxLayout
from qtpy.QtCore import Qt, QTimer

from OpenGL.GL import GL_BLEND, GL_LINES, glBegin, glColor4f, glDisable, glEnable, glEnd, glVertex2f, GL_POINTS, glPointSize, glLineWidth, GL_LINE_LOOP

import QT4GLLayerStack
from Katana import KatanaPrefs, PrefNames, UI4

from cgwidgets.widgets import FrameInputWidgetContainer, BooleanInputWidget, IntInputWidget, ListInputWidget, LabelledInputWidget, FloatInputWidget
from Utils2.widgetutils import getActiveNodegraphWidget
from Utils2 import getFontSize


class GridLayer(QT4GLLayerStack.Layer):
    """ OpenGL Drawing layer to show the back ground grid

    Args:
        color (tuple, RGBA 0-1): color to be drawn
        draw_mode (DISPLAYAS): how the grid should be displayed
            POINTS | CROSSHAIR | LINES
        grid_size (tuple): of ints of the grid size
            (int, int)
        line_width (int): Width of lines drawn
        radius (int) Radius of cross sections
        """
    POINT = 0
    CROSSHAIR = 1
    LINE = 2
    DIAMOND = 3
    SQUARE = 4
    ROUND_ARROW = 5

    def __init__(self, *args, draw_mode=SQUARE, color=(1, 1, 1, 0.05), grid_size=None, line_width=1, radius=5, **kwargs):
        (QT4GLLayerStack.Layer.__init__)(self, *args, **kwargs)
        self._color = color
        self._draw_mode = draw_mode
        if not grid_size:
            nodegraph_widget = getActiveNodegraphWidget()
            floating_node_layer = nodegraph_widget.getLayerByName("Floating Nodes")
            module = inspect.getmodule(floating_node_layer)
            grid_size = (module.GRIDSIZEX, module.GRIDSIZEY)
        self._grid_size = grid_size
        self._line_width = line_width
        self._radius = radius

    """ PROPERTIES """
    def color(self):
        return self._color

    def setColor(self, color):
        self._color = color

    def drawMode(self):
        return self._draw_mode

    def setDrawMode(self, draw_mode):
        """ Sets the current grid display mode

        Args:
            draw_mode (GridLayer.DISPLAYMODE):
                POINT | CROSSHAIR | LINES
        """
        self._draw_mode = draw_mode

    def gridSize(self):
        return self._grid_size

    def setGridSize(self, grid_size):
        self._grid_size = grid_size

    def lineWidth(self):
        return self._line_width

    def setLineWidth(self, line_width):
        self._line_width = line_width

    def radius(self):
        return self._radius

    def setRadius(self, radius):
        self._radius = radius

    """ EVENTS"""
    def drawGrid(self):
        self.layerStack().applyWorldSpace()
        GRIDSIZEX = self.gridSize()[0]
        GRIDSIZEY = self.gridSize()[1]
        if KatanaPrefs[PrefNames.NODEGRAPH_GRIDSNAP]:
            leftBottom = self.layerStack().mapFromQTLocalToWorld(0, 0)
            rightTop = self.layerStack().mapFromQTLocalToWorld(self.layerStack().width(), self.layerStack().height())
            left = int(leftBottom[0] / GRIDSIZEX)
            right = int(rightTop[0] / GRIDSIZEX) + 1
            top = int(leftBottom[1] / GRIDSIZEY) + 1
            bottom = int(rightTop[1] / GRIDSIZEY)
            glEnable(GL_BLEND)

            glColor4f(*self.color())

            # Setting cap on number of cross sections to reduce lag
            num_dots = (right-left) * (top-bottom)
            if 50000 < num_dots: return

            # Points
            if self.drawMode() == GridLayer.POINT:
                glPointSize(self.radius())
                glBegin(GL_POINTS)
                for x in range(min(left, right), max(left, right)):
                    for y in range(min(top, bottom), max(top, bottom)):
                        glVertex2f(x * GRIDSIZEX, y * GRIDSIZEY)
                glEnd()

            # Crosshair
            if self.drawMode() == GridLayer.CROSSHAIR:
                glLineWidth(self.lineWidth())
                glBegin(GL_LINES)
                for x in range(min(left, right), max(left, right)):
                    for y in range(min(top, bottom), max(top, bottom)):
                        l = (x * GRIDSIZEX) - self.radius()
                        r = (x * GRIDSIZEX) + self.radius()
                        t = (y * GRIDSIZEY) + self.radius()
                        b = (y * GRIDSIZEY) - self.radius()

                        glVertex2f(l, y * GRIDSIZEY)
                        glVertex2f(r, y * GRIDSIZEY)
                        glVertex2f(x * GRIDSIZEX, t)
                        glVertex2f(x * GRIDSIZEX, b)
                glEnd()

            # Diamond
            if self.drawMode() == GridLayer.DIAMOND:
                glLineWidth(self.lineWidth())
                for x in range(min(left, right), max(left, right)):
                    for y in range(min(top, bottom), max(top, bottom)):
                        l = (x * GRIDSIZEX) - self.radius()
                        r = (x * GRIDSIZEX) + self.radius()
                        t = (y * GRIDSIZEY) + self.radius()
                        b = (y * GRIDSIZEY) - self.radius()
                        glBegin(GL_LINE_LOOP)
                        glVertex2f(l, y * GRIDSIZEY)
                        glVertex2f(x * GRIDSIZEX, t)
                        glVertex2f(r, y * GRIDSIZEY)
                        glVertex2f(x * GRIDSIZEX, b)
                        glEnd()

            if self.drawMode() == GridLayer.SQUARE:
                glLineWidth(self.lineWidth())
                for x in range(min(left, right), max(left, right)):
                    for y in range(min(top, bottom), max(top, bottom)):
                        l = (x * GRIDSIZEX) - self.radius()
                        r = (x * GRIDSIZEX) + self.radius()
                        t = (y * GRIDSIZEY) + self.radius()
                        b = (y * GRIDSIZEY) - self.radius()
                        glBegin(GL_LINE_LOOP)
                        glVertex2f(l, b)
                        glVertex2f(l, t)
                        glVertex2f(r, t)
                        glVertex2f(r, b)
                        glVertex2f(l, b)

                        glEnd()

            # Grid
            if self.drawMode() == GridLayer.LINE:
                glLineWidth(self.lineWidth())
                glBegin(GL_LINES)
                for x in range(left, right):
                    glVertex2f(x * GRIDSIZEX, leftBottom[1])
                    glVertex2f(x * GRIDSIZEX, rightTop[1])

                for x in range(bottom, top):
                    glVertex2f(leftBottom[0], x * GRIDSIZEY)
                    glVertex2f(rightTop[0], x * GRIDSIZEY)
                glEnd()

            # Rounded Arrow
            # if self.drawMode() == GridLayer.ROUND_ARROW:
            #     for x in range(min(left, right), max(left, right)):
            #         for y in range(min(top, bottom), max(top, bottom)):
            #             num_segments = 12
            #             radius = self.radius()
            #             glBegin(GL_LINE_LOOP)
            #             for i in range(num_segments):
            #                 theta = 6.282 * ((i+1) / num_segments)
            #                 xpos = int((math.cos(theta)) + (x * GRIDSIZEX))
            #                 ypos = int((math.sin(theta)) + (y * GRIDSIZEY))
            #                 glVertex2f(xpos, ypos)
            #                 #
            #                 # print(xpos, ypos)
            #
            #             glEnd()
            glDisable(GL_BLEND)

    def paintGL(self):
        def unfreeze():
            self._is_frozen = False

        delay_amount = 100
        # setup frozen attr
        if not hasattr(self, "_is_frozen"):
            self._is_frozen = False

        # run events on timer
        if not self._is_frozen:
            # setup timer
            timer = QTimer()
            timer.start(delay_amount)
            timer.timeout.connect(unfreeze)
            self.drawGrid()


class GridGUIWidget(FrameInputWidgetContainer):
    """ Popup GUI that is displayed when the user opens the Grid Settings Menu"""
    DRAW_OPTIONS_MAP = {
        "POINT": GridLayer.POINT,
        "CROSSHAIR": GridLayer.CROSSHAIR,
        "LINE": GridLayer.LINE,
        "DIAMOND": GridLayer.DIAMOND,
        "SQUARE": GridLayer.SQUARE
    }

    DRAW_OPTIONS_MAP_INVERSE = {
        GridLayer.POINT: "POINT",
        GridLayer.CROSSHAIR: "CROSSHAIR",
        GridLayer.LINE: "LINE",
        GridLayer.DIAMOND: "DIAMOND",
        GridLayer.SQUARE: "SQUARE",
    }

    def __init__(self, parent=None):
        super(GridGUIWidget, self).__init__(parent=parent, title="Grid Settings", direction=Qt.Vertical)
        self.setIsHeaderEditable(False)

        # get default values
        if GridGUIWidget.gridLayer():
            colorr = GridGUIWidget.gridLayer().color()[0]
            colorg = GridGUIWidget.gridLayer().color()[1]
            colorb = GridGUIWidget.gridLayer().color()[2]
            colora = GridGUIWidget.gridLayer().color()[3]
            radius = GridGUIWidget.gridLayer().radius()
            line_width = GridGUIWidget.gridLayer().lineWidth()
            draw_mode = GridGUIWidget.gridLayer().drawMode()
            enabled = True
            grid_x_size = GridGUIWidget.gridLayer().gridSize()[0]
            grid_y_size = GridGUIWidget.gridLayer().gridSize()[1]

        # first init
        else:
            colorr = 1
            colorg = 1
            colorb = 1
            colora = 0.05
            radius = 5
            line_width = 1
            draw_mode = GridLayer.CROSSHAIR
            enabled = False
            grid_x_size = 32
            grid_y_size = 16

        # ENABLE WIDGET
        self._grid_button = BooleanInputWidget(text="Toggle Grid", is_selected=enabled)

        # RADIUS WIDGET
        self._radius_widget = IntInputWidget()
        #self._radius_widget.setUseLadder(True, value_list=[1, 1])
        self._radius_widget.setText(str(radius))
        self._radius_widget_labelled_widget = LabelledInputWidget(name="Radius", delegate_widget=self._radius_widget)
        self._radius_widget_labelled_widget.setDefaultLabelLength(getFontSize() * 5)

        # LINE WIDTH WIDGET
        self._line_width_widget = IntInputWidget()
        #self._line_width_widget.setUseLadder(True, value_list=[1, 1])
        self._line_width_widget.setText(str(line_width))
        self._line_width_widget_labelled_widget = LabelledInputWidget(name="Width", delegate_widget=self._line_width_widget)
        self._line_width_widget_labelled_widget.setDefaultLabelLength(getFontSize() * 5)

        # SIZE WIDGET
        self._grid_widget = QWidget()
        self._grid_layout = QHBoxLayout(self._grid_widget)
        self._grid_size_x_widget = IntInputWidget()
        self._grid_size_y_widget = IntInputWidget()
        self._grid_layout.addWidget(self._grid_size_x_widget)
        self._grid_layout.addWidget(self._grid_size_y_widget)
        self._grid_size_widget_labelled_widget = LabelledInputWidget(name="Size", delegate_widget=self._grid_widget)

        self._grid_size_widget_labelled_widget.setDefaultLabelLength(getFontSize() * 5)
        self._grid_size_x_widget.setUserFinishedEditingEvent(self.setGridXSize)
        self._grid_size_y_widget.setUserFinishedEditingEvent(self.setGridYSize)
        self._grid_size_x_widget.setText(str(grid_x_size))
        self._grid_size_y_widget.setText(str(grid_y_size))

        # COLOR WIDGET
        self._color_widget = QWidget()
        self._color_layout = QHBoxLayout(self._color_widget)
        self._colorr_widget = FloatInputWidget()
        self._colorg_widget = FloatInputWidget()
        self._colorb_widget = FloatInputWidget()
        self._colora_widget = FloatInputWidget()
        self._color_layout.addWidget(self._colorr_widget)
        self._color_layout.addWidget(self._colorg_widget)
        self._color_layout.addWidget(self._colorb_widget)
        self._color_layout.addWidget(self._colora_widget)
        self._color_labelled_widget = LabelledInputWidget(name="Color", delegate_widget=self._color_widget)

        self._color_labelled_widget.setDefaultLabelLength(getFontSize() * 5)
        self._colorr_widget.setUserFinishedEditingEvent(self.setGridColorR)
        self._colorg_widget.setUserFinishedEditingEvent(self.setGridColorG)
        self._colorb_widget.setUserFinishedEditingEvent(self.setGridColorB)
        self._colora_widget.setUserFinishedEditingEvent(self.setGridColorA)
        self._colorr_widget.setText(str(colorr))
        self._colorg_widget.setText(str(colorg))
        self._colorb_widget.setText(str(colorb))
        self._colora_widget.setText(str(colora))

        # MODE WIDGET
        self._draw_mode_widget = ListInputWidget()
        self._draw_mode_widget.populate([[mode] for mode in list(GridGUIWidget.DRAW_OPTIONS_MAP.keys())])
        self._draw_mode_widget.filter_results = False
        self._draw_mode_widget.setText(GridGUIWidget.DRAW_OPTIONS_MAP_INVERSE[draw_mode])
        self._draw_mode_widget_labelled_widget = LabelledInputWidget(name="Mode", delegate_widget=self._draw_mode_widget)
        self._draw_mode_widget_labelled_widget.setDefaultLabelLength(getFontSize() * 5)

        # SETUP LAYOUT
        self.addInputWidget(self._grid_button, self.toggleGrid)
        self.addInputWidget(self._grid_size_widget_labelled_widget)
        self.addInputWidget(self._radius_widget_labelled_widget, self.setGridRadius)
        self.addInputWidget(self._line_width_widget_labelled_widget, self.setGridLineWidth)
        self.addInputWidget(self._draw_mode_widget_labelled_widget, self.setGridDrawMode)
        self.addInputWidget(self._color_labelled_widget)

    @staticmethod
    def updateNodegraph():
        nodegraph_wigdet = getActiveNodegraphWidget()
        if nodegraph_wigdet:
            nodegraph_wigdet.idleUpdate()

    @staticmethod
    def gridLayer():
        nodegraph_widget = getActiveNodegraphWidget()
        grid_layer = nodegraph_widget.getLayerByName("Grid Layer")
        return grid_layer

    @staticmethod
    def isGridEnabled():
        """ Returns if the grid layer is enabled or not"""
        if GridGUIWidget.gridLayer():
            return True
        else:
            return False

    def toggleGrid(self, widget, value):
        """ Toggles the visibility of the grid"""
        nodegraph_widget = getActiveNodegraphWidget()
        grid_layer = nodegraph_widget.getLayerByName("Grid Layer")
        # Disable Grid
        if grid_layer:
            nodegraph_widget.removeLayer(grid_layer)
        # Enable Grid
        else:
            grid_layer = GridLayer("Grid Layer", draw_mode=self.drawMode(), radius=self.radius(), line_width=self.lineWidth(), color=self.color(), enabled=True)
            nodegraph_widget.insertLayer(grid_layer, 2)
            # nodegraph_widget.appendLayer(grid_layer)
        GridGUIWidget.updateNodegraph()

    def drawMode(self):
        draw_mode = GridGUIWidget.DRAW_OPTIONS_MAP[self._draw_mode_widget.text()]
        return draw_mode

    def setGridDrawMode(self, widget, value):
        GridGUIWidget.gridLayer().setDrawMode(GridGUIWidget.DRAW_OPTIONS_MAP[value])
        GridGUIWidget.updateNodegraph()

    def color(self):
        return [
            float(self._colorr_widget.text()),
            float(self._colorg_widget.text()),
            float(self._colorb_widget.text()),
            float(self._colora_widget.text())
        ]

    def setGridColorR(self, widget, value):
        color = self.color()
        color[0] = float(value)
        GridGUIWidget.gridLayer().setColor(color)
        GridGUIWidget.updateNodegraph()

    def setGridColorG(self, widget, value):
        color = self.color()
        color[1] = float(value)
        GridGUIWidget.gridLayer().setColor(color)
        GridGUIWidget.updateNodegraph()

    def setGridColorB(self, widget, value):
        color = self.color()
        color[2] = float(value)
        GridGUIWidget.gridLayer().setColor(color)
        GridGUIWidget.updateNodegraph()

    def setGridColorA(self, widget, value):
        color = self.color()
        color[3] = float(value)
        GridGUIWidget.gridLayer().setColor(color)
        GridGUIWidget.updateNodegraph()

    def radius(self):
        return int(self._radius_widget.text())

    def setGridRadius(self, widget, value):
        GridGUIWidget.gridLayer().setRadius(int(value))
        GridGUIWidget.updateNodegraph()

    def lineWidth(self):
        return int(self._line_width_widget.text())

    def setGridLineWidth(self, widget, value):
        GridGUIWidget.gridLayer().setLineWidth(int(value))
        GridGUIWidget.updateNodegraph()

    def gridXSize(self):
        return int(self._grid_size_x_widget.text())

    def gridYSize(self):
        return int(self._grid_size_y_widget.text())

    # Todo: Update for LinkConnectionLayer, not sure if necessary... but would be nice
    """ This is dynamically drawn... so would need to do a hack registry
    See in the LinkConnectionLayer Overrides
    """
    def setGridXSize(self, widget, value):
        GridGUIWidget.gridLayer().setGridSize((int(value), self.gridYSize()))
        nodegraph_widget = getActiveNodegraphWidget()
        floating_node_layer = nodegraph_widget.getLayerByName("Floating Nodes")
        module = inspect.getmodule(floating_node_layer)
        module.GRIDSIZEX = int(value)
        GridGUIWidget.updateNodegraph()

    def setGridYSize(self, widget, value):
        GridGUIWidget.gridLayer().setGridSize((self.gridXSize(), int(value)))

        nodegraph_widget = getActiveNodegraphWidget()
        floating_node_layer = nodegraph_widget.getLayerByName("Floating Nodes")
        module = inspect.getmodule(floating_node_layer)
        module.GRIDSIZEY = int(value)
        GridGUIWidget.updateNodegraph()

# def toggleGrid(color=(0, 1, 0, 0.1), draw_mode=GridLayer.CROSSHAIR, radius=3, line_width=3):
#     """ Toggles the visibility of the grid"""
#     nodegraph_widget = getActiveNodegraphWidget()
#     grid_layer = nodegraph_widget.getLayerByName("Grid Layer")
#     # Disable Grid
#     if grid_layer:
#         nodegraph_widget.removeLayer(grid_layer)
#     # Enable Grid
#     else:
#         grid_layer = GridLayer("Grid Layer", draw_mode=draw_mode, radius=radius, line_width=line_width, color=color, enabled=True)
#         nodegraph_widget.appendLayer(grid_layer)
#     nodegraph_widget.idleUpdate()
#
#
# color = (0, 1, 0, 0.1)
# radius = 3
# line_width = 3
# draw_mode = GridLayer.DIAMOND
# toggleGrid(color=color, draw_mode=draw_mode, radius=radius, line_width=line_width)

# from cgwidgets.utils import centerWidgetOnCursor, setAsAlwaysOnTop
# grid_gui_widget = GridGUIWidget()
# setAsAlwaysOnTop(grid_gui_widget)
# grid_gui_widget.show()
# centerWidgetOnCursor(grid_gui_widget)
#
#
#
#
