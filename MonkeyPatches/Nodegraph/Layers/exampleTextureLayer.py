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
    # start texture import
    glGenLists,
    GL_COMPILE,
    glNewList,
    GL_TRIANGLE_FAN,
    glTexCoord2f,
    glVertex3f,
    glEndList,
    GL_TEXTURE0,
    glGenTextures,
    glBindTexture,
    GL_TEXTURE_2D,
    glPixelStorei,
    GL_UNPACK_ALIGNMENT,
    glTexImage2D,
    glActiveTexture,
    GL_RGBA,
    GL_UNSIGNED_BYTE,
    glTexParameterf,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_LINEAR,
    glLoadIdentity,
    glTranslated,
    glCallList, glClear, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT
)

from PIL import Image
import numpy


# setup prefs
import QT4GLLayerStack

from qtpy.QtCore import QPoint

class TestLayer(QT4GLLayerStack.Layer):
    def __init__(self, *args, **kwargs):
        (QT4GLLayerStack.Layer.__init__)(self, *args, **kwargs)
        self.img = Image.open("/media/ssd02/downloads/emmuh_01.png")
        self.mapWidth, self.mapHeight = self.img.size
        pgImData = numpy.asarray(self.img)
        self.inputMapFile = numpy.flipud(pgImData)

        # should be initialize GL
        self.object = self.makeTextureObject()

        glActiveTexture(GL_TEXTURE0)
        self.text_obj = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.text_obj)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.mapWidth, self.mapHeight, 0, GL_RGBA,
                             GL_UNSIGNED_BYTE, self.inputMapFile.tobytes())
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

    def paintGL(self):
        # glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.text_obj)
        glCallList(self.object)
        glDisable(GL_TEXTURE_2D)

    """ TEXTURE """
    def makeTextureObject(self):
        genList = glGenLists(1)
        glNewList(genList, GL_COMPILE)
        glBegin(GL_TRIANGLE_FAN)
        size = 300
        # top left
        glTexCoord2f(0, 1)
        glVertex3f(0, size, 0)

        # top right
        glTexCoord2f(1, 1)
        glVertex3f(size, size, 0)

        # bot right
        glTexCoord2f(1, 0)
        glVertex3f(size, 0, 0)

        # bot left
        glTexCoord2f(0, 0)
        glVertex3f(0, 0, 0)

        glEnd()
        glEndList()

        return genList

# Insert layer
nodegraph_widget = UI4.App.Tabs.FindTopTab('Node Graph').getNodeGraphWidget()
layer = TestLayer("Test", enabled=True)
nodegraph_widget.appendLayer(layer)

# # Remove layer
# nodegraph_widget = UI4.App.Tabs.FindTopTab('Node Graph').getNodeGraphWidget()
# test_layer = nodegraph_widget.getLayerByName("Test")
# nodegraph_widget.removeLayer(test_layer)
# nodegraph_widget.getLayers()













