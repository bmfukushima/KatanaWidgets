
from Widgets2 import AbstractTabWidget

from PyQt5.QtWidgets import  (
    QWidget, QLabel, QHBoxLayout, QLineEdit, QPushButton
)
from PyQt5.QtCore import Qt

try:
    from Katana import NodegraphAPI, Utils
except ModuleNotFoundError:
    pass

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


class NodeShapeAttrsTab(AbstractTabWidget):
    """
    Widget that holds all of the shape attributes available for the user to
    adjust on the node
    """
    NodeShapeTypes = {
        "badgeText": {"type":str, "value":""},
        "drawBadge":{"type":bool, "value":False},
        "glowColorR":{"type":float, "value":0.5},
        "glowColorG":{"type":float, "value":0.5},
        "glowColorB":{"type":float, "value":0.5},
        "errorGlow":{"type":bool, "value":False}
    }

    def __init__(self, parent, node):
        super(NodeShapeAttrsTab, self).__init__(parent)
        self.setType(AbstractTabWidget.STACKED)
        self.setTabPosition(AbstractTabWidget.WEST)
        self.setMultiSelect(True)
        self.setMultiSelectDirection(Qt.Vertical)
        self.setNode(node)

        for i, shape_name in enumerate(sorted(NodeShapeAttrsTab.NodeShapeTypes.keys())):
            default_value = NodeShapeAttrsTab.NodeShapeTypes[shape_name]['value']
            value_type = NodeShapeAttrsTab.NodeShapeTypes[shape_name]['type']
            widget = NodeShapeAttrsWidget(self, node, shape_name, default_value, value_type)
            self.insertTab(i, widget, shape_name)
            # shape name
            # default value
        # w.setType(AbstractTabWidget.DYNAMIC, dynamic_widget=TabDynamicWidgetExample,
        #           dynamic_function=TabDynamicWidgetExample.updateGUI)

    def getNode(self):
        return self._node

    def setNode(self, node):
        self._node = node


class NodeShapeAttrsWidget(QWidget):
    """
    Individual widget holding the GUI to change a shape
    node
    value
    update function?
    """
    def __init__(self, parent, node, shape_name, default_value, value_type):
        super(NodeShapeAttrsWidget, self).__init__(parent)
        # set attrs
        self._node = node
        self._shape_name = shape_name
        self._default_value = default_value
        self._value_type = value_type

        # create widgets
        QHBoxLayout(self)
        label = QLabel(shape_name)
        self.user_input_widget = self.createUserInputWidget()
        # edit_field = QLineEdit()
        # edit_field.setText(str(default_value))
        # edit_field.editingFinished.connect(self.test)

        # setup layout
        self.layout().addWidget(label)
        self.layout().addWidget(self.user_input_widget)

    def createUserInputWidget(self):
        """
        Creates a widget for the user to input stuff with based off of the
        type of data provided
        """
        value_type = self.getValueType()
        if value_type in [str, float]:
            print('string')
            widget = QLineEdit()
            widget.setText(str(self.getDefaultValue()))
            widget.editingFinished.connect(self.userInputEvent)
        elif value_type == bool:
            widget = QPushButton()
            widget.setCheckable(True)
            widget.clicked.connect(self.userInputEvent)
        return widget

    def userInputEvent(self):
        value_type = self.getValueType()
        if value_type == str:
            value = str(self.user_input_widget.text())
        elif value_type == float:
            try:
                value = float(self.user_input_widget.text())
            except ValueError:
                value = 0.5
        elif value_type == bool:
            value = self.user_input_widget.isChecked()
            if value:
                value = 1.0
            else:
                value = 0.0

        NodegraphAPI.SetNodeShapeAttr(self.getNode(), self.getShapeName(), value)
        Utils.EventModule.QueueEvent('node_setShapeAttributes', hash(self.getNode()), node=self.getNode())

    """ PROPERTIES """
    def getNode(self):
        return self._node

    def setNode(self, node):
        self._node = node

    def getShapeName(self):
        return self._shape_name

    def setShapeName(self, shape_name):
        self._shape_name = shape_name

    def getDefaultValue(self):
        return self._default_value

    def setDefaultValue(self, default_value):
        self._default_value = default_value

    def getValueType(self):
        return self._value_type

    def setValueType(self, value_type):
        self._value_type = value_type


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QCursor
    app = QApplication(sys.argv)

    w = NodeShapeAttrsTab(None, 'blahblah')

    # for x in range(3):
    #     nw = QLabel(str(x))
    #     w.insertTab(0, nw, str(x))
    w.show()
    w.move(QCursor.pos())
    sys.exit(app.exec_())

