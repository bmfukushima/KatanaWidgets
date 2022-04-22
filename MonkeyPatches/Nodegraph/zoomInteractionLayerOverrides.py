""" This is used to return the Alt Modifier back to me... """
from qtpy.QtCore import QEvent, Qt


def zoomInteractionLayerProcessEvent(func):
    def __zoomInteractionLayerProcessEvent(self, event):
        if event.type() == QEvent.MouseButtonPress:
            if (event.modifiers() & Qt.AltModifier) == Qt.AltModifier and event.button() == Qt.LeftButton:
                return False

        return func(self, event)

    return __zoomInteractionLayerProcessEvent

def installZoomLayerOverrides(**kwargs):
    from QT4GLLayerStack.ZoomInteractionLayer import ZoomInteractionLayer
    ZoomInteractionLayer.processEvent = zoomInteractionLayerProcessEvent(ZoomInteractionLayer.processEvent)



# nodegraph_widget = UI4.App.Tabs.FindTopTab('Node Graph').getNodeGraphWidget()
# zoom_layer = nodegraph_widget.getLayerByName("Zoom")
# nodegraph_widget.removeLayer(zoom_layer)
# for layer in nodegraph_widget.getLayers():
#     print(layer)













