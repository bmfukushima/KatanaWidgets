""" Shows a basic example of how you can insert a new OpenGL drawing layer into the NodeGraph Tab

world = nodegraph coordinates
    bottom left = 0,0
    top right = 1,1

window = OpenGL Coordinates
    top right = 1,1
    bottom left = 0,0

local = Qt Event Local coordinates
Returned when using nodegraphWidget.getMousePos()
    top left = 0, 0
    bottom right = 1, 1
"""
from OpenGL.GL import GL_BLEND, glBegin, glColor4f, glDisable, glEnable, glEnd, glVertex2f, GL_POINTS, glPointSize
# setup prefs
import QT4GLLayerStack

from qtpy.QtCore import QPoint

class TestLayer(QT4GLLayerStack.Layer):
    def __init__(self, *args, **kwargs):
        (QT4GLLayerStack.Layer.__init__)(self, *args, **kwargs)

    def getCameraZoom(self):
        return self.layerStack().getViewScale()[0]

    def getCameraOffset(self):
        # get attrs
        cam_x_pos = self.layerStack().getEyePoint()[0]
        cam_y_pos = self.layerStack().getEyePoint()[1]
        width = self.layerStack().width()
        height = self.layerStack().height()
        pos_x_offset = width * 0.5
        pos_y_offset = height * 0.5
        zoom = self.getCameraZoom()
        x_offset = pos_x_offset + (-cam_x_pos * zoom)
        y_offset = pos_y_offset + (-cam_y_pos * zoom)
        return QPoint(x_offset, y_offset)

    def paintGL(self):
        # get attrs

        camera_offset = self.getCameraOffset()
        camera_zoom = self.getCameraZoom()
        # create arbitrary point at nodegraph position 100, 100
        node_x_pos = 100 * camera_zoom
        node_y_pos = 100 * camera_zoom

        # draw point at location
        glEnable(GL_BLEND)
        glColor4f(0, 1, 0, 1)
        glPointSize(20)

        glBegin(GL_POINTS)

        # use my own math to map from Nodegraph World Space to OpenGL window space
        glVertex2f(
            node_x_pos + camera_offset.x(),
            node_y_pos + camera_offset.y()
        )

        # use internal function to map from Nodegraph World Space to OpenGL window space
        glVertex2f(*self.layerStack().mapFromWorldToWindow(200, 200))

        # draw point at openGL coordinate 100, 100
        glVertex2f(100, 100)

        # draw point on cursor
        mouse_pos = self.layerStack().getMousePos()
        window_pos = self.layerStack().mapFromQTLocalToWindow(mouse_pos.x(), mouse_pos.y())
        glVertex2f(*window_pos)

        glEnd()
        glDisable(GL_BLEND)


# Insert layer
nodegraph_widget = UI4.App.Tabs.FindTopTab('Node Graph').getNodeGraphWidget()
layer = TestLayer("Test", enabled=True)
nodegraph_widget.appendLayer(layer)

# # Remove layer
# nodegraph_widget = UI4.App.Tabs.FindTopTab('Node Graph').getNodeGraphWidget()
# test_layer = nodegraph_widget.getLayerByName("Test")
# nodegraph_widget.removeLayer(test_layer)
# nodegraph_widget.getLayers()













