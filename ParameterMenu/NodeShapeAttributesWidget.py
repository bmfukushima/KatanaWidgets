"""
TODO:
    *   Boolean widgets
            - Set initial values (1.0 vs 0.0)
            - Set Colors for selected/unselected...
    *   Splitter
            - change width way to big atm...
    *   Allow for parameters with special syntax
            Booleans --> context menu --> select param?

"""
#from cgwidgets.utils.attrs
from cgwidgets.widgets import (
    TansuModelViewWidget, ColorInputWidget, StringInputWidget, BooleanInputWidget
)

from qtpy.QtWidgets import  (
    QWidget, QLabel, QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout
)
from qtpy.QtCore import Qt

try:
    from Katana import NodegraphAPI, Utils, UI4, DrawingModule
except ModuleNotFoundError:
    pass


class NodeShapeAttrsTabMainWidget(QWidget):
    def __init__(self, parent=None, node=None):
        super(NodeShapeAttrsTabMainWidget, self).__init__(parent)
        QVBoxLayout(self)
        main_widget = NodeShapeAttrsTab(self, node)
        resizer = UI4.Widgets.VBoxLayoutResizer(self)

        self.layout().addWidget(main_widget)
        self.layout().addWidget(resizer)

        self.setFixedHeight(200)


class NodeShapeAttrsTab(TansuModelViewWidget):
    """
    Widget that holds all of the shape attributes available for the user to
    adjust on the node
    """
    NodeShapeTypes = {
        "badgeText": {"type" : str, "value" : ""},
        "drawBadge" : {"type" : bool, "value" : False},
    }

    def __init__(self, parent, node):
        super(NodeShapeAttrsTab, self).__init__(parent)
        self.setDelegateType(TansuModelViewWidget.STACKED)
        # todo fix scope out
        # why does this scope out?
        from cgwidgets.utils import attrs
        self.setHeaderPosition(attrs.WEST)
        self.setMultiSelect(True)
        self.setMultiSelectDirection(Qt.Vertical)
        self.setNode(node)

        # create all widgets
        # for i, shape_name in enumerate(sorted(NodeShapeAttrsTab.NodeShapeTypes.keys())):
        #     # get attrs
        #     attrs = node.getAttributes()
        #     try:
        #         default_value = attrs['ns_{shape_name}'.format(shape_name=shape_name)]
        #     except KeyError:
        #         default_value = NodeShapeAttrsTab.NodeShapeTypes[shape_name]['value']
        #
        #     value_type = NodeShapeAttrsTab.NodeShapeTypes[shape_name]['type']
        #
        #     # create widget
        #     widget = NodeShapeAttrsWidget(self, node, shape_name, default_value, value_type)
        #     #self.insertTab(i, shape_name, widget)
        #     self.insertTansuWidget(i, shape_name, widget=widget)
        # node color
        node_color_widget = NodeColorWidget(self, node=node)
        self.insertTansuWidget(0, column_data={'name':'Color'}, widget=node_color_widget)

        # glow color
        glow_input_widget = NodeShapeGlowColorWidget(self, node=node)
        self.insertTansuWidget(0, column_data={'name':'Glow Color'}, widget=glow_input_widget)

        # sub text
        badge_input_widget = NodeShapeTextInput(self, node=node)
        self.insertTansuWidget(0, column_data={'name':'Sub Text'}, widget=badge_input_widget)

    def getNode(self):
        return self._node

    def setNode(self, node):
        self._node = node


class NodeShapeAttrsWidget(QWidget):
    """
    TODO:
        These need to get replaced with UserInputWidgets / Custom inputs
    Individual widget holding the GUI to change a shape.
    Attributes:
        node (node): The node to set this shape on
        shape_name (str): the name of the shape to be set
        default_value (value): The original value
        value_type (type): What type of value should be returned for this
            type of shape
    Widgets
        | -- HBox
                | -- Label
                | -- Edit Widget (createUserInputWidget)
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
            widget = QLineEdit()
            widget.setText(str(self.getDefaultValue()))
            widget.editingFinished.connect(self.userInputEvent)
        elif value_type == bool:
            widget = QPushButton()
            widget.setCheckable(True)
            widget.clicked.connect(self.userInputEvent)
        return widget

    def userInputEvent(self):
        """
        The primary event that is triggered whenever the user finishes inputting
        some values
        """
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


class NodeShapeGlowColorWidget(ColorInputWidget):
    """
    GUI for the user to adjust the node glow color
    """
    def __init__(self, parent=None, node=None):
        super(NodeShapeGlowColorWidget, self).__init__(parent)
        self._node = node

        self.setUserInput(self.update)

    def update(self, widget, color):
        red = color.redF()
        green = color.greenF()
        blue = color.blueF()

        NodegraphAPI.SetNodeShapeAttr(self._node, "glowColorR", red)
        NodegraphAPI.SetNodeShapeAttr(self._node, "glowColorG", green)
        NodegraphAPI.SetNodeShapeAttr(self._node, "glowColorB", blue)

        Utils.EventModule.QueueEvent('node_setShapeAttributes', hash(self._node), node=self._node)


class NodeColorWidget(ColorInputWidget):
    """
    GUI for the user to adjust the node glow color
    """
    def __init__(self, parent=None, node=None):
        super(NodeColorWidget, self).__init__(parent)
        self._node = node

        self.setUserInput(self.update)

    def update(self, widget, color):
        red = color.redF()
        green = color.greenF()
        blue = color.blueF()

        DrawingModule.SetCustomNodeColor(self._node, red, green, blue)
        NodegraphAPI.SetNeedsRedraw(True)
        Utils.EventModule.ProcessAllEvents()


class NodeShapeTextInput(QWidget):
    """
    GUI for user to adjust the Badge text
    """
    def __init__(self, parent=None, node=None):
        super(NodeShapeTextInput, self).__init__(parent)
        self._node = node

        # set up GUI

        # create widgets
        self.user_input_widget = StringInputWidget(self)
        self.display_toggle_widget = BooleanInputWidget(self)

        # setup layout
        QHBoxLayout(self)
        self.layout().setAlignment(Qt.AlignTop)
        self.layout().addWidget(self.display_toggle_widget)
        self.layout().addWidget(self.user_input_widget)

        # setup events
        self.display_toggle_widget.setUserFinishedEditingEvent(self.setBadgeEnabled)
        self.user_input_widget.setUserFinishedEditingEvent(self.setBadgeText)

    def setBadgeEnabled(self, widget, value):
        # convert to float, because Katana
        if value is True:
            enabled = 1.0
        else:
            enabled = 0.0
        NodegraphAPI.SetNodeShapeAttr(self._node,  "drawBadge", enabled)
        Utils.EventModule.QueueEvent('node_setShapeAttributes', hash(self._node), node=self._node)

    def setBadgeText(self, widget, value):
        NodegraphAPI.SetNodeShapeAttr(self._node,  "badgeText",  str(value))
        Utils.EventModule.QueueEvent('node_setShapeAttributes', hash(self._node), node=self._node)


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication
    from qtpy.QtGui import QCursor
    app = QApplication(sys.argv)

    w = NodeShapeAttrsTab(None, 'blahblah')

    # for x in range(3):
    #     nw = QLabel(str(x))
    #     w.insertTab(0, nw, str(x))
    w.show()
    w.move(QCursor.pos())
    sys.exit(app.exec_())

