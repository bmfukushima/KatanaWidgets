from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea
)
from PyQt5.QtCore import Qt

from Katana import UI4, QT4FormWidgets


class AbstractParametersDisplayWidget(QScrollArea):
    """
    Abstract class for display parameters.
    """
    def __init__(self, parent=None):
        super(AbstractParametersDisplayWidget, self).__init__(parent)

        # create main widget
        self.setWidget(QWidget(self))
        QVBoxLayout(self.widget())

        self.widget().layout().setAlignment(Qt.AlignTop)

        # set main widget
        self.setWidgetResizable(True)

    def getLayout(self):
        """
        returns the current widgets layout
        """
        return self.widget().layout()

    def clearLayout(self):
        """
        Removes all of the items/widgets from the main items layout
        """
        for i in reversed(range(self.getLayout().count())):
            self.getLayout().itemAt(i).widget().setParent(None)

    def showParameter(self, node_name, hide_title=False):
        """
        Args:
            *   node_name (str): name of node to be referenced
            **  hide_title (bool): Determines if the title of the parameter will be hidden.
                    If there is more than one parameter, the title will not be hidden,
                    if there is only 1 then it will be hidden.
        """
        teleparam_widget = self.createTeleparamWidget(node_name, hide_title=False)
        teleparam_widget.show()
        self.getLayout().addWidget(teleparam_widget)

    @staticmethod
    def createTeleparamWidget(node_name, hide_title=False):
        """
        Creates a teledrop parameter widget

        Args:
            *   node_name (str): name of node to be referenced
            **  hide_title (bool): Determines if the title of the parameter will be hidden.
                    If there is more than one parameter, the title will not be hidden,
                    if there is only 1 then it will be hidden.

        Returns:
            teledropparam
        """
        policyData = dict(displayNode="")
        rootPolicy = QT4FormWidgets.PythonValuePolicy("cels", policyData)
        params_policy = rootPolicy.getChildByName("displayNode")
        params_policy.getWidgetHints().update(
            widget='teleparam',
            open="True",
            hideTitle=repr(hide_title)
        )
        param_widget = UI4.FormMaster.KatanaWidgetFactory.buildWidget(None, params_policy)
        params_policy.setValue(node_name, 0)
        return param_widget
