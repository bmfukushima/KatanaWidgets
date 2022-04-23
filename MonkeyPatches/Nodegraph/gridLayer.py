"""
Todo:
    - Registering different widgets from the "buildLayers" call and the manual creation mode...
        Doesn't work on init...
            MonkeyPatches.Nodegraph.gridLayer.GridLayer object at 0x7f3eb256aa50
        Works from shell:
            Katana.GridLayer object at 0x7f3ddcd1e190
    - Ladder Delegate... This has been broken forever...
    - Document...
"""

import inspect
from qtpy.QtWidgets import QWidget, QHBoxLayout
from qtpy.QtCore import Qt, QTimer

from OpenGL.GL import GL_BLEND, GL_LINES, glBegin, glColor4f, glDisable, glEnable, glEnd, glVertex2f, GL_POINTS, glPointSize, glLineWidth, GL_LINE_LOOP

try:
    import QT4GLLayerStack
    from Katana import KatanaPrefs, PrefNames, UI4
    from UI4.App import Tabs
except:
    print("fail????")
from cgwidgets.widgets import FrameInputWidgetContainer, BooleanInputWidget, IntInputWidget, ListInputWidget, LabelledInputWidget, FloatInputWidget
from Utils2.widgetutils import getActiveNodegraphWidget
from Utils2 import getFontSize

GRID_COLOR_PREF_NAME = "nodegraph/grid/color"
GRID_DRAW_MODE_PREF_NAME = "nodegraph/grid/drawMode"
GRID_ENABLED_PREF_NAME = "nodegraph/grid/enabled"
GRID_GROUP_PREF_NAME = "nodegraph/grid"
GRID_LINE_WIDTH_PREF_NAME = "nodegraph/grid/lineWidth"
GRID_RADIUS_PREF_NAME = "nodegraph/grid/radius"
GRID_SIZE_X_PREF_NAME = "nodegraph/grid/sizeX"
GRID_SIZE_Y_PREF_NAME = "nodegraph/grid/sizeY"


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
    def __init__(self, *args, **kwargs):
        (QT4GLLayerStack.Layer.__init__)(self, *args, **kwargs)

    """ EVENTS"""
    def drawGrid(self):
        if KatanaPrefs[GRID_ENABLED_PREF_NAME]:
            self.layerStack().applyWorldSpace()
            GRIDSIZEX = GridUtils.gridSizeX()
            GRIDSIZEY = GridUtils.gridSizeY()

            leftBottom = self.layerStack().mapFromQTLocalToWorld(0, 0)
            rightTop = self.layerStack().mapFromQTLocalToWorld(self.layerStack().width(), self.layerStack().height())
            left = int(leftBottom[0] / GRIDSIZEX)
            right = int(rightTop[0] / GRIDSIZEX) + 1
            top = int(leftBottom[1] / GRIDSIZEY) + 1
            bottom = int(rightTop[1] / GRIDSIZEY)
            glEnable(GL_BLEND)

            glColor4f(*GridUtils.color())

            # Setting cap on number of cross sections to reduce lag
            num_dots = (right-left) * (top-bottom)
            if 50000 < num_dots: return

            # Points
            if GridUtils.drawMode() == GridUtils.POINT:
                glPointSize(GridUtils.radius())
                glBegin(GL_POINTS)
                for x in range(min(left, right), max(left, right)):
                    for y in range(min(top, bottom), max(top, bottom)):
                        glVertex2f(x * GRIDSIZEX, y * GRIDSIZEY)
                glEnd()

            # Crosshair
            if GridUtils.drawMode() == GridUtils.CROSSHAIR:
                glLineWidth(GridUtils.lineWidth())
                glBegin(GL_LINES)
                for x in range(min(left, right), max(left, right)):
                    for y in range(min(top, bottom), max(top, bottom)):
                        l = (x * GRIDSIZEX) - GridUtils.radius()
                        r = (x * GRIDSIZEX) + GridUtils.radius()
                        t = (y * GRIDSIZEY) + GridUtils.radius()
                        b = (y * GRIDSIZEY) - GridUtils.radius()

                        glVertex2f(l, y * GRIDSIZEY)
                        glVertex2f(r, y * GRIDSIZEY)
                        glVertex2f(x * GRIDSIZEX, t)
                        glVertex2f(x * GRIDSIZEX, b)
                glEnd()

            # Diamond
            if GridUtils.drawMode() == GridUtils.DIAMOND:
                glLineWidth(GridUtils.lineWidth())
                for x in range(min(left, right), max(left, right)):
                    for y in range(min(top, bottom), max(top, bottom)):
                        l = (x * GRIDSIZEX) - GridUtils.radius()
                        r = (x * GRIDSIZEX) + GridUtils.radius()
                        t = (y * GRIDSIZEY) + GridUtils.radius()
                        b = (y * GRIDSIZEY) - GridUtils.radius()
                        glBegin(GL_LINE_LOOP)
                        glVertex2f(l, y * GRIDSIZEY)
                        glVertex2f(x * GRIDSIZEX, t)
                        glVertex2f(r, y * GRIDSIZEY)
                        glVertex2f(x * GRIDSIZEX, b)
                        glEnd()

            if GridUtils.drawMode() == GridUtils.SQUARE:
                glLineWidth(GridUtils.lineWidth())
                for x in range(min(left, right), max(left, right)):
                    for y in range(min(top, bottom), max(top, bottom)):
                        l = (x * GRIDSIZEX) - GridUtils.radius()
                        r = (x * GRIDSIZEX) + GridUtils.radius()
                        t = (y * GRIDSIZEY) + GridUtils.radius()
                        b = (y * GRIDSIZEY) - GridUtils.radius()
                        glBegin(GL_LINE_LOOP)
                        glVertex2f(l, b)
                        glVertex2f(l, t)
                        glVertex2f(r, t)
                        glVertex2f(r, b)
                        glVertex2f(l, b)

                        glEnd()

            # Grid
            if GridUtils.drawMode() == GridUtils.LINE:
                glLineWidth(GridUtils.lineWidth())
                glBegin(GL_LINES)
                for x in range(left, right):
                    glVertex2f(x * GRIDSIZEX, leftBottom[1])
                    glVertex2f(x * GRIDSIZEX, rightTop[1])

                for x in range(bottom, top):
                    glVertex2f(leftBottom[0], x * GRIDSIZEY)
                    glVertex2f(rightTop[0], x * GRIDSIZEY)
                glEnd()

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
    def __init__(self, parent=None):
        super(GridGUIWidget, self).__init__(parent=parent, title="Grid Settings", direction=Qt.Vertical)
        self.setIsHeaderEditable(False)

        colorr = GridUtils.color()[0]
        colorg = GridUtils.color()[1]
        colorb = GridUtils.color()[2]
        colora = GridUtils.color()[3]
        radius = GridUtils.radius()
        line_width = GridUtils.lineWidth()
        draw_mode = GridUtils.drawMode()
        enabled = GridUtils.isGridEnabled()
        grid_x_size = GridUtils.gridSizeX()
        grid_y_size = GridUtils.gridSizeY()

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
        self._grid_size_x_widget.setUserFinishedEditingEvent(self.setGridSizeX)
        self._grid_size_y_widget.setUserFinishedEditingEvent(self.setGridSizeY)
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
        self._draw_mode_widget.populate([[mode] for mode in list(GridUtils.DRAW_OPTIONS_MAP.keys())])
        self._draw_mode_widget.filter_results = False
        self._draw_mode_widget.setText(GridUtils.DRAW_OPTIONS_MAP_INVERSE[draw_mode])
        self._draw_mode_widget_labelled_widget = LabelledInputWidget(name="Mode", delegate_widget=self._draw_mode_widget)
        self._draw_mode_widget_labelled_widget.setDefaultLabelLength(getFontSize() * 5)

        # SETUP LAYOUT
        self.addInputWidget(self._grid_button, self.setIsGridEnabled)
        self.addInputWidget(self._grid_size_widget_labelled_widget)
        self.addInputWidget(self._radius_widget_labelled_widget, self.setGridRadius)
        self.addInputWidget(self._line_width_widget_labelled_widget, self.setGridLineWidth)
        self.addInputWidget(self._draw_mode_widget_labelled_widget, self.setGridDrawMode)
        self.addInputWidget(self._color_labelled_widget)

    def setGridColorR(self, widget, value):
        color = GridUtils.color()
        color[0] = float(value)
        GridUtils.setColor(color)

    def setGridColorG(self, widget, value):
        color = GridUtils.color()
        color[1] = float(value)
        GridUtils.setColor(color)

    def setGridColorB(self, widget, value):
        color = GridUtils.color()
        color[2] = float(value)
        GridUtils.setColor(color)

    def setGridColorA(self, widget, value):
        color = GridUtils.color()
        color[3] = float(value)
        GridUtils.setColor(color)

    def setGridDrawMode(self, widget, value):
        GridUtils.setDrawMode(GridUtils.DRAW_OPTIONS_MAP[value])

    def setIsGridEnabled(self, widget, enabled):
        GridUtils.setIsGridEnabled(enabled)

    def setGridLineWidth(self, widget, value):
        GridUtils.setLineWidth(int(value))

    def setGridRadius(self, widget, value):
        GridUtils.setRadius(int(value))

    # Todo: Update for LinkConnectionLayer, not sure if necessary... but would be nice
    """ This is dynamically drawn... so would need to do a hack registry
    See in the LinkConnectionLayer Overrides
    """
    def setGridSizeX(self, widget, value):
        GridUtils.setGridSizeX(int(value))

        # update floating node layer grid size
        nodegraph_widget = getActiveNodegraphWidget()
        floating_node_layer = nodegraph_widget.getLayerByName("Floating Nodes")
        module = inspect.getmodule(floating_node_layer)
        module.GRIDSIZEX = int(value)

    def setGridSizeY(self, widget, value):
        GridUtils.setGridSizeY(int(value))

        # update floating node layer grid size
        nodegraph_widget = getActiveNodegraphWidget()
        floating_node_layer = nodegraph_widget.getLayerByName("Floating Nodes")
        module = inspect.getmodule(floating_node_layer)
        module.GRIDSIZEY = int(value)


class GridUtils(object):
    """DRAW MODES """
    # TODO CLEAN THIS UP TO ONE LIST
    POINT = 0
    CROSSHAIR = 1
    LINE = 2
    DIAMOND = 3
    SQUARE = 4
    ROUND_ARROW = 5

    DRAW_MODES = [
        "POINT",
        "CROSSHAIR",
        "LINE",
        "DIAMOND",
        "SQUARE"
    ]

    DRAW_OPTIONS_MAP = {
        "POINT": POINT,
        "CROSSHAIR": CROSSHAIR,
        "LINE": LINE,
        "DIAMOND": DIAMOND,
        "SQUARE": SQUARE
    }

    DRAW_OPTIONS_MAP_INVERSE = {
        POINT: "POINT",
        CROSSHAIR: "CROSSHAIR",
        LINE: "LINE",
        DIAMOND: "DIAMOND",
        SQUARE: "SQUARE",
    }

    """ UTILS """
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
    def toggleGrid(*args):
        """ Toggles the visibility of the grid

        Todo this won't be called anyone, and needs to be injected when a nodegrpah is created
        """
        nodegraph_widget = getActiveNodegraphWidget()
        grid_layer = nodegraph_widget.getLayerByName("Grid Layer")
        # Disable Grid
        if GridUtils.isGridEnabled():
            nodegraph_widget.removeLayer(grid_layer)
        # Enable Grid
        else:
            grid_layer = GridLayer(
                "Grid Layer",
                draw_mode=GridLayer.drawMode(),
                radius=GridLayer.radius(),
                line_width=GridLayer.lineWidth(),
                color=GridLayer.color(),
                enabled=True)
            nodegraph_widget.insertLayer(grid_layer, 2)
            # nodegraph_widget.appendLayer(grid_layer)
        GridUtils.updateNodegraph()

    """ PROPERTIES """
    @staticmethod
    def color():
        return [*KatanaPrefs[GRID_COLOR_PREF_NAME]]

    @staticmethod
    def setColor(color):
        KatanaPrefs[GRID_COLOR_PREF_NAME] = color
        KatanaPrefs.commit()
        GridUtils.updateNodegraph()

    @staticmethod
    def drawMode():
        return KatanaPrefs[GRID_DRAW_MODE_PREF_NAME]

    @staticmethod
    def setDrawMode(draw_mode):
        """ Sets the current grid display mode

        Args:
            draw_mode (GridLayer.DISPLAYMODE):
                POINT | CROSSHAIR | LINES
        """
        KatanaPrefs[GRID_DRAW_MODE_PREF_NAME] = draw_mode
        KatanaPrefs.commit()
        GridUtils.updateNodegraph()

    @staticmethod
    def isGridEnabled():
        """ Returns if the grid layer is enabled or not"""
        return KatanaPrefs[GRID_ENABLED_PREF_NAME]

    @staticmethod
    def setIsGridEnabled(enabled):
        """ Returns if the grid layer is enabled or not"""
        KatanaPrefs[GRID_ENABLED_PREF_NAME] = enabled
        KatanaPrefs.commit()

        for nodegraph_widget in getActiveNodegraphWidget().getAllNodeGraphWidgets():
            grid_layer = nodegraph_widget.getLayerByName("Grid Layer")
            # Disable Grid
            if enabled:
                grid_layer = GridLayer("Grid Layer", enabled=True)
                nodegraph_widget.insertLayer(grid_layer, 2)

            # Enable Grid
            else:
                if grid_layer:
                    nodegraph_widget.removeLayer(grid_layer)
            nodegraph_widget.idleUpdate()

    @staticmethod
    def lineWidth():
        return KatanaPrefs[GRID_LINE_WIDTH_PREF_NAME]

    @staticmethod
    def setLineWidth(line_width):
        KatanaPrefs[GRID_LINE_WIDTH_PREF_NAME] = line_width
        KatanaPrefs.commit()
        GridUtils.updateNodegraph()

    @staticmethod
    def radius():
        return KatanaPrefs[GRID_RADIUS_PREF_NAME]

    @staticmethod
    def setRadius(radius):
        KatanaPrefs[GRID_RADIUS_PREF_NAME] = radius
        KatanaPrefs.commit()
        GridUtils.updateNodegraph()

    @staticmethod
    def gridSizeX():
        return KatanaPrefs[GRID_SIZE_X_PREF_NAME]

    @staticmethod
    def setGridSizeX(grid_size):
        KatanaPrefs[GRID_SIZE_X_PREF_NAME] = grid_size
        KatanaPrefs.commit()
        GridUtils.updateNodegraph()

    @staticmethod
    def gridSizeY():
        return KatanaPrefs[GRID_SIZE_Y_PREF_NAME]

    @staticmethod
    def setGridSizeY(grid_size):
        KatanaPrefs[GRID_SIZE_Y_PREF_NAME] = grid_size
        KatanaPrefs.commit()
        GridUtils.updateNodegraph()


def buildLayers(func):
    def __buildLayers(self):
        func(self)
        from MonkeyPatches.Nodegraph.gridLayer import GridLayer as Test
        self._grid_layer = Test("Grid Layer", enabled=True)

        # self.insertLayer(grid_layer, 2)
        self.appendLayer(self._grid_layer)

    return __buildLayers


def installGridLayer(**kwargs):
    # create proxy nodegraph
    # todo for some reason this registry doesn't work
    nodegraph_panel = Tabs._LoadedTabPluginsByTabTypeName["Node Graph"].data(None)
    nodegraph_widget = nodegraph_panel.getNodeGraphWidget()

    nodegraph_widget.__class__._NodegraphWidget__buildLayers = buildLayers(nodegraph_widget.__class__._NodegraphWidget__buildLayers)

    # setup prefs
    from Katana import KatanaPrefs, Utils

    KatanaPrefs.declareGroupPref(GRID_GROUP_PREF_NAME)

    KatanaPrefs.declareColorPref(GRID_COLOR_PREF_NAME, (1, 1, 1, 0.05), 'Color of grid')
    KatanaPrefs.declareBoolPref(GRID_ENABLED_PREF_NAME, False, helpText="Determines if the nodegraph grid is enabled")
    # Prefs.declareIntPref((PrefNames.RENDERING_UPDATEMODE2D), (RenderGlobals.RENDERMODE_PROCESS),
    #   'Specifies what UI actions will trigger a render of the currently viewed 2D node',
    #   hints={'widget':'mapper',
    #  'options':RenderGlobals.RENDERMODE_OPTIONS})
    options = []
    for i, draw_mode in enumerate(GridUtils.DRAW_MODES):
        options.append(f"{draw_mode}:{i}|")
    options = "|".join(options)

    KatanaPrefs.declareIntPref(
        (GRID_DRAW_MODE_PREF_NAME),
        0,
        'Specifies the draw mode of the grid',
        hints={'widget': 'mapper', 'options': options}
    )
    KatanaPrefs.declareIntPref(GRID_LINE_WIDTH_PREF_NAME, 1, helpText="Determines the grid line width")
    KatanaPrefs.declareIntPref(GRID_RADIUS_PREF_NAME, 5, helpText="Determines the grid radius")
    KatanaPrefs.declareIntPref(GRID_SIZE_X_PREF_NAME, 32, helpText="Determines the grid x spacing")
    KatanaPrefs.declareIntPref(GRID_SIZE_Y_PREF_NAME, 16, helpText="Determines the grid y spacing")
    #
    #
    def gridPrefChangedEvent(*args, **kwargs):
        if kwargs["prefKey"] in [
            "nodegraph/grid/color",
            "nodegraph/grid/drawMode",
            "nodegraph/grid/enabled",
            "nodegraph/grid",
            "nodegraph/grid/lineWidth",
            "nodegraph/grid/radius",
            "nodegraph/grid/sizeX",
            "nodegraph/grid/sizeY",
        ]:
            GridUtils.updateNodegraph()

    Utils.EventModule.RegisterEventHandler(gridPrefChangedEvent, 'pref_changed')

    # declare a new preference
    # if pref_name not in KatanaPrefs.keys():
    # KatanaPrefs.declareBoolPref(pref_name, False, helpText="Determines if the nodegraph grid is enabled")
    KatanaPrefs.commit()


def toggleGrid():
    """ Toggles the visibility of the grid"""
    nodegraph_widget = getActiveNodegraphWidget()
    grid_layer = nodegraph_widget.getLayerByName("Grid Layer")
    # Disable Grid
    if grid_layer:
        nodegraph_widget.removeLayer(grid_layer)
    # Enable Grid
    else:
        grid_layer = GridLayer("Grid Layer", enabled=True)
        nodegraph_widget.insertLayer(grid_layer, 2)
    nodegraph_widget.idleUpdate()
# #
# g = GridGUIWidget()
# g.show()
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
