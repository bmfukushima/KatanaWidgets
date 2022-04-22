from qtpy.QtCore import Qt

from OpenGL.GL import GL_BLEND, GL_LINES, glBegin, glColor4f, glDisable, glEnable, glEnd, glVertex2f

import QT4GLLayerStack
from Katana import KatanaPrefs, PrefNames

from cgwidgets.widgets import FrameInputWidgetContainer, BooleanInputWidget
from Utils2.widgetutils import getActiveNodegraphWidget


class GridLayer(QT4GLLayerStack.Layer):
    def __init__(self, *args, **kwargs):
        (QT4GLLayerStack.Layer.__init__)(self, *args, **kwargs)

    def paintGL(self):
        self.layerStack().applyWorldSpace()
        GRIDSIZEX = 32
        GRIDSIZEY = 16
        if KatanaPrefs[PrefNames.NODEGRAPH_GRIDSNAP]:
            leftBottom = self.layerStack().mapFromQTLocalToWorld(0, 0)
            rightTop = self.layerStack().mapFromQTLocalToWorld(self.layerStack().width(), self.layerStack().height())
            left = int(leftBottom[0] / GRIDSIZEX)
            right = int(rightTop[0] / GRIDSIZEX) + 1
            top = int(leftBottom[1] / GRIDSIZEY) + 1
            bottom = int(rightTop[1] / GRIDSIZEY)
            glEnable(GL_BLEND)
            glColor4f(1, 1, 1, 0.05)
            glBegin(GL_LINES)
            for x in range(left, right):
                glVertex2f(x * GRIDSIZEX, leftBottom[1])
                glVertex2f(x * GRIDSIZEX, rightTop[1])

            for x in range(bottom, top):
                glVertex2f(leftBottom[0], x * GRIDSIZEY)
                glVertex2f(rightTop[0], x * GRIDSIZEY)

            glEnd()
            glDisable(GL_BLEND)


class GridGUIWidget(FrameInputWidgetContainer):
    """ Todo
            - Make this a popup widget on the cursor
            - Add grid size? Is that even possible?"""
    def __init__(self, parent=None):
        super(GridGUIWidget, self).__init__(parent=parent, title="Grid Settings", direction=Qt.Horizontal)

        self._toggleGridButton = BooleanInputWidget(text="Toggle Grid", is_selected=self.isGridEnabled())
        self.addInputWidget(self._toggleGridButton, self.toggleGrid)

    def isGridEnabled(self):
        """ Returns if the grid layer is enabled or not"""
        nodegraph_widget = getActiveNodegraphWidget()
        grid_layer = nodegraph_widget.getLayerByName("Grid Layer")
        # Disable Grid
        if grid_layer:
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
            grid_layer = GridLayer("Grid Layer", enabled=True)
            nodegraph_widget.appendLayer(grid_layer)
        nodegraph_widget.idleUpdate()













