import sys

from PyQt5 import QtWidgets , QtGui, QtCore, Qt

from Katana import UI4, NodegraphAPI


class DragButton(QtWidgets.QPushButton):
    def __init__(self, parent=None):
        super(DragButton,self).__init__(parent)
        self.setText('lkjasdf')
        self.node_graph_widget = UI4.App.Tabs.FindTopTab('Node Graph').getNodeGraphWidget()
        self.node_graph_widget.installEventFilter(self)

    def mousePressEvent(self, event, *args, **kwargs):
        drag = QtGui.QDrag(self)
        image_path = '/media/ssd01/Eclipse/Python/PyQt5Examples/image.jpg'
        pixmap = QtGui.QPixmap(image_path)

        pixmap = pixmap.scaledToWidth(500)

        drag.setPixmap(pixmap)

        hotspot = QtCore.QPoint(pixmap.width() * .5 , pixmap.height() *.5)
        drag.setHotSpot(hotspot)
        mime_data = QtCore.QMimeData()
        mime_data.setText('test')
        mime_data.setData('test/this','this is a test string')
        
        drag.setMimeData(mime_data)
        drag.exec_(QtCore.Qt.MoveAction)
        return QtWidgets.QPushButton.mousePressEvent(self, event, *args, **kwargs)

    def eventFilter(self, obj, event, *args, **kwargs):

        if event.type() in (QtCore.QEvent.DragEnter, QtCore.QEvent.DragMove, QtCore.QEvent.Drop):
            if event.type() != QtCore.QEvent.Drop:
                event.acceptProposedAction()
            else:
                node_list = []
                for x in range(0, 5):
                    node = NodegraphAPI.CreateNode('Group', NodegraphAPI.GetRootNode())
                    NodegraphAPI.SetNodePosition(node, (0, x*50))
                    node_list.append(node)

                self.node_graph_widget.parent().floatNodes(node_list)
            return True

        return QtWidgets.QPushButton.eventFilter(self, obj, event, *args, **kwargs)


main_widget = DragButton()
main_widget.show()
