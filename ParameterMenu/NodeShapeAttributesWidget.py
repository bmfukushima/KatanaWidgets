
from Widgets2 import AbstractTabWidget

from PyQt5.QtWidgets import  QWidget, QLabel
from PyQt5.QtCore import Qt

# DrawingModule.nodeWorld_setShapeAttr(node, 'badgeText', badgeText)
"""
def _AddGlow(node):
    DrawingModule.nodeWorld_setShapeAttr(node, 'glowColorR', 1.0)
    DrawingModule.nodeWorld_setShapeAttr(node, 'glowColorG', 0.0)
    DrawingModule.nodeWorld_setShapeAttr(node, 'glowColorB', 0.0)
    NodegraphAPI.SetNodeShapeAttr(node, 'errorGlow', 1.0)
    Utils.EventModule.QueueEvent('node_setShapeAttributes', hash(node), node=node)


def _RemoveGlow(node):
    DrawingModule.nodeWorld_setShapeAttr(node, 'removeGlowColor', True)
    NodegraphAPI.SetNodeShapeAttr(node, 'errorGlow', 0.0)
    Utils.EventModule.QueueEvent('node_setShapeAttributes', hash(node), node=node)
"""


class NodeShapeAttrsWidget(AbstractTabWidget):
    NodeShapeTypes = {
        "badgeText":str,
        "drawBadge":bool,
        "glowColorR":float,
        "glowColorG":float,
        "glowColorB":float,
        "errorGlow":bool
    }
    def __init__(self, parent=None):
        super(NodeShapeAttrsWidget, self).__init__(parent)
        self.setType(AbstractTabWidget.STACKED)
        self.setTabPosition(AbstractTabWidget.WEST)
        self.setMultiSelect(True)
        self.setMultiSelectDirection(Qt.Vertical)

        for i, x in enumerate(NodeShapeAttrsWidget.NodeShapeTypes.keys()):
            widget = QLabel(x)
            self.insertTab(i, widget, x)
        # w.setType(AbstractTabWidget.DYNAMIC, dynamic_widget=TabDynamicWidgetExample,
        #           dynamic_function=TabDynamicWidgetExample.updateGUI)



if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QCursor
    app = QApplication(sys.argv)

    w = NodeShapeAttrsWidget()

    # for x in range(3):
    #     nw = QLabel(str(x))
    #     w.insertTab(0, nw, str(x))
    w.show()
    w.move(QCursor.pos())
    sys.exit(app.exec_())

