from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea
)
from qtpy.QtCore import Qt

try:
    from Katana import UI4, QT4FormWidgets, NodegraphAPI, Utils
except ModuleNotFoundError:
    pass


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

    def enableSelectionDisplay(self, enabled):
        """
        Determines if the auto selection should be active.
        """
        Utils.EventModule.RegisterCollapsedHandler(
            self.__displaySelectedParameters, 'node_setSelected', enabled=enabled
        )

    def __displaySelectedParameters(self, *args):
        self.populateParameters(node_list=NodegraphAPI.GetAllSelectedNodes())

    """ populate parameters"""
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

    def populateParameters(self, node_list, hide_title=None):
        """
        Displays the parameters in the bottom of the GUI,
        this is currently linked to the Alt+W hotkey.

        Args:
            node_list (list): list of nodes that will have their parameters displayed.
            hide_title (bool): determines if the title should be hidden or not.  The
                default value of None will force it to choose.  If there is more than 1
                node it will be shown, less than 1 node, hidden.
        """
        # clear layout
        self.clearLayout()

        node_list = self.filterNodeList(node_list)

        # get hide
        if hide_title is None:
            if len(node_list) < 2:
                hide_title = True
            else:
                hide_title = False

        # display nodes
        for node in node_list:
            self.showParameter(node.getName(), hide_title)

    def showParameter(self, node_name, hide_title=False):
        """
        Creates and displays one individual teleparam based off of the node name
        that is provided.
        Args:
            *   node_name (str): name of node to be referenced
            **  hide_title (bool): Determines if the title of the parameter will be hidden.
                    If there is more than one parameter, the title will not be hidden,
                    if there is only 1 then it will be hidden.
        """
        teleparam_widget = self.__createTeleparamWidget(node_name, hide_title=hide_title)
        self.getLayout().addWidget(teleparam_widget)
        teleparam_widget.show()
        self.update()

    """ Get node list"""
    def filterNodeList(self, node_list):
        for index, node in enumerate(reversed(node_list)):
            value = self.filterNode(node)
            if value is False:
                node_list.pop(index)

        return node_list

    def filterNode(self, *args, **kwargs):
        """
        Determines whether or not a node should be included in the node
        list based on the function provided to the setNodeFilter method
        """
        value = self.__nodeFilter(*args, **kwargs)
        return value

    def setNodeFilter(self, function):
        self.__nodeFilter = function

    def __nodeFilter(self, *args):
        """
        Abstract function that should be overrwritten
        """
        return True

    @staticmethod
    def __createTeleparamWidget(node_name, hide_title=False):
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
