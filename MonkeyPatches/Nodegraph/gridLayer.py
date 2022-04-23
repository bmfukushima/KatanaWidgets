from qtpy.QtCore import Qt, QTimer

from OpenGL.GL import GL_BLEND, GL_LINES, glBegin, glColor4f, glDisable, glEnable, glEnd, glVertex2f, GL_POINTS, glPointSize, glLineWidth, GL_LINE_LOOP

import QT4GLLayerStack
from Katana import KatanaPrefs, PrefNames

from cgwidgets.widgets import FrameInputWidgetContainer, BooleanInputWidget, IntInputWidget, ListInputWidget, LabelledInputWidget
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

    def __init__(self, *args, draw_mode=SQUARE, color=(1, 1, 1, 0.05), grid_size=(32, 16), line_width=1, radius=5, **kwargs):
        (QT4GLLayerStack.Layer.__init__)(self, *args, **kwargs)
        self._color = color
        self._draw_mode = draw_mode
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
            color = GridGUIWidget.gridLayer().color()
            radius = GridGUIWidget.gridLayer().radius()
            line_width = GridGUIWidget.gridLayer().lineWidth()
            draw_mode = GridGUIWidget.gridLayer().drawMode()
            enabled = True
        else:
            color = (1, 1, 1, 0.5)
            radius = 5
            line_width = 1
            draw_mode = GridLayer.CROSSHAIR
            enabled = False

        self._grid_button = BooleanInputWidget(text="Toggle Grid", is_selected=enabled)

        self._radius_widget = IntInputWidget()
        self._radius_widget.setText(str(radius))
        self._radius_widget_labelled_widget = LabelledInputWidget(name="Radius", delegate_widget=self._radius_widget)
        self._radius_widget_labelled_widget.setDefaultLabelLength(getFontSize() * 5)

        self._line_width_widget = IntInputWidget()
        self._line_width_widget.setText(str(line_width))
        self._line_width_widget_labelled_widget = LabelledInputWidget(name="Width", delegate_widget=self._line_width_widget)
        self._line_width_widget_labelled_widget.setDefaultLabelLength(getFontSize() * 5)

        self._draw_mode_widget = ListInputWidget()
        self._draw_mode_widget.populate([[mode] for mode in list(GridGUIWidget.DRAW_OPTIONS_MAP.keys())])
        self._draw_mode_widget.filter_results = False
        self._draw_mode_widget.setText(GridGUIWidget.DRAW_OPTIONS_MAP_INVERSE[draw_mode])
        self._draw_mode_widget_labelled_widget = LabelledInputWidget(name="Mode", delegate_widget=self._draw_mode_widget)
        self._draw_mode_widget_labelled_widget.setDefaultLabelLength(getFontSize() * 5)

        self.addInputWidget(self._grid_button, self.toggleGrid)
        self.addInputWidget(self._radius_widget_labelled_widget, self.setGridRadius)
        self.addInputWidget(self._line_width_widget_labelled_widget, self.setGridLineWidth)
        self.addInputWidget(self._draw_mode_widget_labelled_widget, self.setGridDrawMode)

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
            nodegraph_widget.appendLayer(grid_layer)
        GridGUIWidget.updateNodegraph()

    def drawMode(self):
        draw_mode = GridGUIWidget.DRAW_OPTIONS_MAP[self._draw_mode_widget.text()]
        return draw_mode

    def setGridDrawMode(self, widget, value):
        GridGUIWidget.gridLayer().setDrawMode(GridGUIWidget.DRAW_OPTIONS_MAP[value])
        GridGUIWidget.updateNodegraph()

    def color(self):
        return (1, 1, 1, 0.1)

    def setGridColor(self, widget, value):
        GridGUIWidget.gridLayer().setColor(value)
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

    def gridSize(self):
        return (32, 16)

    def setGridSize(self, widget, value):
        GridGUIWidget.gridLayer().setGridSize(value)


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

from cgwidgets.utils import centerWidgetOnCursor, setAsAlwaysOnTop
grid_gui_widget = GridGUIWidget()
setAsAlwaysOnTop(grid_gui_widget)
grid_gui_widget.show()
centerWidgetOnCursor(grid_gui_widget)




