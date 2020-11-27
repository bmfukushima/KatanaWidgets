import os

from qtpy.QtWidgets import QWidget

try:
    from Katana import UI4, QT4Widgets, QT4FormWidgets
    from Katana import NodegraphAPI, Utils, Nodes3DAPI, FnGeolib, NodeGraphView
    from Katana import UniqueName, FormMaster, Utils, Decorators
except ImportError:
    import UI4, QT4Widgets, QT4FormWidgets
    import NodegraphAPI, Utils, Nodes3DAPI, FnGeolib, NodeGraphView
    import UniqueName, FormMaster, Utils

from cgwidgets.settings.colors import iColor

from cgwidgets.widgets import ListInputWidget


class NodeTypeListWidget(ListInputWidget):
    """
    Drop down menu with autocomplete for the user to select
    what Node Type that they wish for the Variable Manager to control
    """
    def __init__(self, parent=None):
        super(NodeTypeListWidget, self).__init__(parent)
        self.previous_text = "<multi>"

        self.setUserFinishedEditingEvent(self.indexChanged)
        self.populate(self.__getAllNodes())

        self.setCleanItemsFunction(self.__getAllNodes)
        self.dynamic_update = True

    @staticmethod
    def __getAllNodes():
        node_list = [["<multi>"]] + [[node] for node in NodegraphAPI.GetNodeTypes()]
        return node_list

    def checkUserInput(self):
        """
        Checks the user input to determine if it is a valid option
        in the current model.  If it is not this will reset the menu
        back to the previous option
        """
        does_node_variable_exist = self.isUserInputValid()
        if does_node_variable_exist is False:
            self.setText(self.previous_text)
            return

    """ VIRTUAL FUNCTIONS """
    def nodeTypeChanged(self, widget, value):
        """
        Needs to be overloaded.

        Args:
            widget (QWidget): This widget
            value (string): current value being set on this widget
        """
        return

    def setNodeTypeChangedEvent(self, function):
        self.nodeTypeChanged = function

    """ EVENTS """
    def mousePressEvent(self, *args, **kwargs):
        self.update()
        return ListInputWidget.mousePressEvent(self, *args, **kwargs)

    def indexChanged(self, widget, value):
        """
        When the user changes the value in the GSV dropdown menu,
        this event is run.  It will first ask the user if they wish to proceed,
        as doing so will essentially reinstated this node back to an initial setting.
        """
        # preflight
        if self.previous_text == self.text(): return
        """
        # without this it randomly allows the user to change to a
        # new node type =\
        """
        # preflight checks
        # return if this node type does not exist
        if self.text() not in NodegraphAPI.GetNodeTypes(): return

        # run user defined signal
        self.nodeTypeChanged(widget, value)


if __name__ == "__main__":
    w = NodeTypeListWidget()
    from qtpy.QtGui import QCursor
    w.show()
    w.move(QCursor.pos())