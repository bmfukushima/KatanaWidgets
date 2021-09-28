from qtpy.QtWidgets import (QVBoxLayout)
from qtpy.QtCore import Qt

from Katana import NodegraphAPI, Utils


from cgwidgets.widgets import ListInputWidget, LabelledInputWidget
from cgwidgets.utils import getWidgetAncestor

from Widgets2 import AbstractSuperToolEditor, iParameter
from Utils2 import paramutils, getFontSize


class ConstraintEditor(AbstractSuperToolEditor):
    def __init__(self, parent, node):
        super(ConstraintEditor, self).__init__(parent, node)

        # create params
        constraint_type = self.node().getParameter("ConstraintType").getValue(0)

        self._constraint_type_widget = ConstraintTypeWidget(self)
        self._constraint_type_widget.setIsFrozen(True)
        self._constraint_type_widget.setText(constraint_type)
        self._constraint_type_widget.setIsFrozen(False)

        constraint_type_widget = LabelledInputWidget(
            name="Type", delegate_widget=self._constraint_type_widget, default_label_length=getFontSize()*6)

        self.createCustomParam(
            self._constraint_type_widget,
            'ConstraintType',
            paramutils.STRING,
            self._constraint_type_widget.text,
            self._constraint_type_widget.updateConstraintType,
            initial_value=constraint_type
        )

        # setup layout
        QVBoxLayout(self)
        self.layout().setAlignment(Qt.AlignTop)

        self.layout().addWidget(constraint_type_widget)
        self.layout().addWidget(self.createKatanaParam("MaintainOffset"))
        self.layout().addWidget(self.createKatanaParam("ConstraintParams"))

        Utils.EventModule.RegisterCollapsedHandler(self.constraintParamChanged, "parameter_finalizeValue")

    def constraintParamChanged(self, args):
        for arg in args:
            param = arg[2]["param"]
            node = arg[2]["node"]
            if node == self and param == self.constraintTypeParam():
                value = param.getValue(0)
                if value in ConstraintTypeWidget.OPTIONS:
                    self.constraintTypeWidget.setText(param.getValue(0), 0)
                else:
                    print(value, "is not a valid option, resetting to", self.constraintTypeWidget().text())

    def constraintTypeWidget(self):
        return self._constraint_type_widget

class ConstraintTypeWidget(ListInputWidget, iParameter):
    OPTIONS = [
        'AimConstraint',
        'BillboardConstraint',
        'CameraScreenWindowConstraint',
        'ClippingConstraint',
        'DollyConstraint',
        'FOVConstraint',
        'OrientConstraint',
        'ParentChildConstraint',
        'PointConstraint',
        'ReflectionConstraint',
        'ScaleConstraint',
        'ScreenCoordinateConstraint',
    ]

    def __init__(self, parent):
        super(ConstraintTypeWidget, self).__init__(parent)
        self.setCleanItemsFunction(self.getConstraintTypes)
        self._is_frozen = False

    def isFrozen(self):
        return self._is_frozen

    def setIsFrozen(self, is_frozen):
        self._is_frozen = is_frozen

    def getConstraintTypes(self):
        return [[option] for option in ConstraintTypeWidget.OPTIONS]

    def updateConstraintType(self, widget, value):
        # preflight
        if self.previous_text == self.text(): return
        if self.text() not in ConstraintTypeWidget.OPTIONS:
            self.setText(self.previous_text)
            return
        if self.isFrozen(): return

        # get attrs
        node_type = self.text()
        constraint_editor = getWidgetAncestor(self, ConstraintEditor)


        this_node = constraint_editor.node()

        # create / update node
        new_node = NodegraphAPI.CreateNode(node_type, this_node)

        # connect node
        new_node.getInputPortByIndex(0).connect(this_node.getSendPort("in"))
        new_node.getOutputPortByIndex(0).connect(this_node.duplicateXFormNode().getInputPortByIndex(0))
        new_node.getOutputPortByIndex(0).connect(this_node.maintainOffsetNode().getInputPortByIndex(0))

        # delete old node
        old_node = constraint_editor.node().constraintNode()
        old_node.delete()

        # update attrs
        constraint_editor.node().setConstraintNode(new_node)
        constraint_editor.node().constraintDisplayParam().setExpression("@{name}".format(name=new_node.getName()))
        constraint_editor.node().transferXFormNode().getParameter("CEL").setExpression("={name}/basePath".format(name=new_node.getName()))
        constraint_editor.node().duplicateXFormNode().getParameter("CEL").setExpression("={name}/basePath".format(name=new_node.getName()))

        self.previous_text = node_type
        self.setValue(node_type)
