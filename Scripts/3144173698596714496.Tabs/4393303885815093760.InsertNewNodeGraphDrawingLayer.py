""" Shows a basic example of how you can insert a new OpenGL drawing layer into the NodeGraph Tab """

from OpenGL.GL import GL_BLEND, glBegin, glColor4f, glDisable, glEnable, glEnd, glVertex2f, GL_POINTS, glPointSize
# setup prefs
import QT4GLLayerStack

class TestLayer(QT4GLLayerStack.Layer):
    def __init__(self, *args, **kwargs):
        (QT4GLLayerStack.Layer.__init__)(self, *args, **kwargs)

    def paintGL(self):
        # get attrs
        cam_x_pos = self.layerStack().getEyePoint()[0]
        cam_y_pos = self.layerStack().getEyePoint()[1]
        width = self.layerStack().width()
        height = self.layerStack().height()
        pos_x_offset = width * 0.5
        pos_y_offset = height * 0.5
        zoom = self.layerStack().getViewScale()[0]

        # create arbitrary point at nodegraph position 100, 100
        node_x_pos = 100 * zoom
        node_y_pos = 100 * zoom
        # node = NodegraphAPI.GetNode("Backdrop")
        # attrs = node.getAttributes()
        # node_x_pos = attrs["x"]
        # node_y_pos = attrs["y"]
        # draw point at location
        glEnable(GL_BLEND)
        glColor4f(0, 1, 0, 1)
        glPointSize(20)
        glBegin(GL_POINTS)

        glVertex2f(
            pos_x_offset + node_x_pos + (-cam_x_pos * zoom),
            pos_y_offset + node_y_pos + (-cam_y_pos * zoom)
        )

        glEnd()
        glDisable(GL_BLEND)


nodegraph_widget = UI4.App.Tabs.FindTopTab('Node Graph').getNodeGraphWidget()
layer = TestLayer("Test", enabled=True)
nodegraph_widget.appendLayer(layer)

# test_layer = nodegraph_widget.getLayerByName("Test")
# nodegraph_widget.removeLayer(test_layer)
# nodegraph_widget.getLayers()















