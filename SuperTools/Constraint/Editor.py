"""
Todo:
    *   ParentChildConstraint
            override to flip the stack order.  As for some reason this stack order is coming in reversed...
    *   Maintain offset
            - Parent child constraint
                ConstraintNode.__setupMaintainOffsetNodes
                ConstraintTypeWidget.updateConstraintType()
            - Bypass switch for maintain offset?

"""
from qtpy.QtWidgets import (QVBoxLayout)
from qtpy.QtCore import Qt

from Katana import NodegraphAPI, Utils


from cgwidgets.widgets import ListInputWidget, LabelledInputWidget, BooleanInputWidget, OverlayInputWidget
from cgwidgets.utils import getWidgetAncestor

from Widgets2 import AbstractSuperToolEditor, iParameter
from Utils2 import paramutils, getFontSize


class ConstraintEditor(AbstractSuperToolEditor):
    def __init__(self, parent, node):
        super(ConstraintEditor, self).__init__(parent, node)

        self.__setupWidgets()

        self.__updateDefaultValues()

        # setup events
        Utils.EventModule.RegisterCollapsedHandler(self.paramChanged, "parameter_finalizeValue")

    def __setupWidgets(self):
        """ Creates all of the display widgets and adds them to the main layout"""
        # Constraint Type
        self._constraint_type_widget = ConstraintTypeWidget(self)

        constraint_type_widget = LabelledInputWidget(
            name="Type", delegate_widget=self._constraint_type_widget, default_label_length=getFontSize()*8)
        constraint_type_widget.viewWidget().setDisplayMode(OverlayInputWidget.DISABLED)

        self.createCustomParam(
            self._constraint_type_widget,
            'ConstraintType',
            paramutils.STRING,
            self._constraint_type_widget.text,
            self._constraint_type_widget.updateConstraintType,
        )

        # Stack Order
        self._stack_order_widget = StackOrderWidget(self)

        _stack_order_widget = LabelledInputWidget(
            name="Stack Order", delegate_widget=self._stack_order_widget, default_label_length=getFontSize()*8)
        _stack_order_widget.viewWidget().setDisplayMode(OverlayInputWidget.DISABLED)
        self.createCustomParam(
            self._stack_order_widget,
            "StackOrder",
            paramutils.NUMBER,
            self._stack_order_widget.text,
            self._stack_order_widget.updateStackOrder
        )

        # Maintain Offset
        self._maintain_offset_delegate_widget = MaintainOffsetWidget(self)

        self._maintain_offset_widget = LabelledInputWidget(
            name="Maintain Offset", delegate_widget=self._maintain_offset_delegate_widget, default_label_length=getFontSize()*8)
        self._maintain_offset_widget.viewWidget().setDisplayMode(OverlayInputWidget.DISABLED)

        self.createCustomParam(
            self._maintain_offset_delegate_widget,
            "MaintainOffset",
            paramutils.NUMBER,
            self._maintain_offset_delegate_widget.is_selected,
            self._maintain_offset_delegate_widget.updateMaintainOffset
        )

        # setup layout
        QVBoxLayout(self)
        self.layout().setAlignment(Qt.AlignTop)

        self.layout().addWidget(constraint_type_widget)
        self.layout().addWidget(_stack_order_widget)
        self.layout().addWidget(self._maintain_offset_widget)
        self.layout().addWidget(self.createKatanaParam("ConstraintParams"))

    def __updateDefaultValues(self):
        """ Sets up all of the default values."""
        # create params
        constraint_type = self.node().getParameter("ConstraintType").getValue(0)
        stack_order = self.node().getParameter("StackOrder").getValue(0)
        maintain_offset = self.node().getParameter("MaintainOffset").getValue(0)

        # update default display attrs
        self._constraint_type_widget.setIsFrozen(True)
        self._constraint_type_widget.setText(constraint_type)
        self._constraint_type_widget.setIsFrozen(False)

        self._stack_order_widget.setIsFrozen(True)
        if stack_order:
            self._stack_order_widget.setText("first")
        else:
            self._stack_order_widget.setText("last")
        self._stack_order_widget.setIsFrozen(False)

        if maintain_offset:
            self.maintainOffsetDelegateWidget().is_selected = True
        else:
            self.maintainOffsetDelegateWidget().is_selected = False

    """ EVENTS """
    def paramChanged(self, args):
        """ Event run when a param has changed.  This hopefully will update the text correctly
        when a parameter is programmatically set"""
        for arg in args:
            param = arg[2]["param"]
            node = arg[2]["node"]
            if node == self:
                if param in [self.constraintTypeParam(), self.maintainOffsetParam(), self.stackOrderParam()]:
                    if param == self.constraintTypeParam():
                        value = param.getValue(0)
                        if value in ConstraintTypeWidget.OPTIONS:
                            self.constraintTypeWidget().setText(param.getValue(0), 0)
                        else:
                            print(value, "is not a valid option, resetting to", self.constraintTypeWidget().text())
                    elif param == self.stackOrderParam():
                        value = param.getValue(0)
                        if value in ["first", "last"]:
                            self.stackOrderWidget().setText(param.getValue(0), 0)
                        else:
                            print(value, "is not a valid option, resetting to", self.stackOrderWidget().text())
                    elif param == self.maintainOffsetParam():
                        value = param.getValue(0)
                        self.maintainOffsetWidget().is_selected = value
                        print(value, type(value))

    """ WIDGETS """
    def maintainOffsetWidget(self):
        return self._maintain_offset_widget

    def maintainOffsetDelegateWidget(self):
        return self._maintain_offset_delegate_widget

    def stackOrderWidget(self):
        return self._stack_order_widget

    def constraintTypeWidget(self):
        return self._constraint_type_widget


class MaintainOffsetWidget(BooleanInputWidget, iParameter):
    def __init__(self, parent=None):
        super(MaintainOffsetWidget, self).__init__(parent)

    def updateMaintainOffset(self, widget, value):
        constraint_editor = getWidgetAncestor(self, ConstraintEditor)
        constraint_editor.node().maintainOffsetParam().setValue(value, 0)


class StackOrderWidget(ListInputWidget, iParameter):
    def __init__(self, parent=None):
        super(StackOrderWidget, self).__init__(parent)
        self.populate([["first"], ["last"]])
        self.setText("first")
        self.filter_results = False

    def updateStackOrder(self, widget, value):
        constraint_editor = getWidgetAncestor(self, ConstraintEditor)
        if value == "first":
            constraint_editor.node().stackOrderParam().setValue(1, 0)
        elif value == "last":
            constraint_editor.node().stackOrderParam().setValue(0, 0)


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
        constraint_editor = getWidgetAncestor(self, ConstraintEditor)
        previous_node_type = constraint_editor.node().constraintTypeParam().getValue(0)
        if previous_node_type == self.text(): return
        if self.text() not in ConstraintTypeWidget.OPTIONS:
            self.setText(previous_node_type)
            return
        if self.isFrozen(): return

        # get attrs
        node_type = self.text()

        this_node = constraint_editor.node()

        # create / update node
        constraint_node = NodegraphAPI.CreateNode(node_type, this_node)

        # connect node
        constraint_node.getInputPortByIndex(0).connect(this_node.getSendPort("in"))
        constraint_node.getOutputPortByIndex(0).connect(this_node.constraintDotNode().getInputPortByIndex(0))

        # delete old node
        old_node = this_node.constraintNode()
        old_node.delete()

        # update attrs
        this_node.setConstraintNode(constraint_node)
        this_node.constraintDisplayParam().setExpression("@{name}".format(name=constraint_node.getName()))
        this_node.transferXFormNode().getParameter("CEL").setExpression("={name}/basePath".format(name=constraint_node.getName()))
        this_node.duplicateXFormNode().getParameter("CEL").setExpression("={name}/basePath".format(name=constraint_node.getName()))
        this_node.maintainOffsetScriptNode().getParameter("CEL").setExpression("={name}/basePath".format(name=constraint_node.getName()))
        this_node.maintainOffsetScriptNode().getParameter("user.targetXFormPath").setExpression("={name}/targetPath".format(name=constraint_node.getName()))

        # update attrs ( maintain offset )
        # todo update for ParentChildConstraint
        # maintain offset available
        if node_type in ["OrientConstraint", "PointConstraint", "ScaleConstraint"]:
            if node_type == "PointConstraint":
                this_node.maintainOffsetScriptNode().getParameter("user.targetXFormPath").setExpression("={name}/targetPath.i0".format(name=constraint_node.getName()))

            constraint_editor.maintainOffsetWidget().show()

        # maintain offset not available
        else:
            constraint_editor.maintainOffsetWidget().hide()
            constraint_editor.maintainOffsetDelegateWidget().setIsSelected(False)
            constraint_editor.node().maintainOffsetParam().setValue(0, 0)
        this_node.modeParam().setValue(node_type, 0)

        #self.previous_text = node_type
        self.setValue(node_type)

