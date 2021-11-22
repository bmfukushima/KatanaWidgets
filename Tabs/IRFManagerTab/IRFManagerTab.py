"""TODO
    *   Create
            - Conflicting names
                - Currently this just automagically works...
                - should do a check to make sure that there are no conflicting names
    *   View
"""
"""
Create
    - Can create new categories/filters.
    - Categories MUST have atleast one filter in them, or else they will be deleted
    - New filters/categories can be created by RMB --> Create Category/Filter
    - Drag/Drop to reorganize
    - Changing a category name will update all IRFs category names
    - Changing a filters name, will update only the filter

Hierarchy:
    IRFManagerTab --> UI4.Tabs.BaseTab
        |- QVBoxLayout
            |- main_widget --> (ShojiModelViewWidget)
                |- view_widget --> (QWidget)
                |- activation_widget --> (ShojiLayout)
                |    |- QWidget
                |    |    |- QVBoxLayout
                |    |        |- QLabel
                |    |        |- _available_filters_organizer_widget --> (AbstractIRFOrganizerViewWidget)
                |    |- QWidget
                |        |- QVBoxLayout
                |            |- QLabel
                |            |- _activated_filters_organizer_widget --> (IRFActivationOrganizerWidget)
                |- create_widget --> (ShojiLayout)
                    |- irf_node_widget (ListInputWidget)
                    |- irf_organizer_widget (ModelViewWidget)
                    |- nodegraph_widget (GroupNodeEditorWidget)
"""
import json

from qtpy.QtWidgets import QVBoxLayout, QLabel, QWidget, QHBoxLayout, QSizePolicy
from qtpy.QtCore import Qt

from Katana import UI4, NodegraphAPI, RenderManager, Utils

from cgwidgets.widgets import (
    ShojiModelViewWidget,
    ListInputWidget,
    StringInputWidget,
    LabelledInputWidget,
    ModelViewWidget,
    ModelViewItem,
    ShojiLayout
)
from cgwidgets.views import AbstractDragDropModelDelegate

from cgwidgets.utils import getWidgetAncestor

from Utils2 import widgetutils, paramutils, nodeutils
from Widgets2 import GroupNodeEditorWidget

from .IRFOrganizerWidget import AbstractIRFOrganizerViewWidget, AbstractIRFOrganizerWidget
from .IRFUtils import IRFUtils


class IRFManagerTab(UI4.Tabs.BaseTab):
    """A tab for users to manager their IRFs with

    Widgets:
        irf_node_widget (ListInputWidget)
        main_widget (ShojiModelViewWidget):
        create_widget
        edit_widget:
        view_widget
    """
    NAME = 'IRF Manager'

    def __init__(self, parent=None):
        super(IRFManagerTab, self).__init__(parent)
        # setup default attrs
        self.__setupDefaultIRFNode()

        # setup layout
        QVBoxLayout(self)

        self._main_widget = ShojiModelViewWidget(self)
        self._view_widget = IRFViewWidget(parent=self)
        self._activation_widget = IRFActivationWidget(parent=self)
        self._create_widget = IRFCreateWidget(parent=self)

        # insert widgets
        self._main_widget.insertShojiWidget(0, column_data={"name":"View"}, widget=self._view_widget)
        self._main_widget.insertShojiWidget(1, column_data={"name":"Activate"}, widget=self._activation_widget)
        self._main_widget.insertShojiWidget(2, column_data={"name":"Create"}, widget=self._create_widget)

        self.layout().addWidget(self.mainWidget())

    """ UTILS """
    @staticmethod
    def __setupDefaultIRFParam():
        Utils.UndoStack.DisableCapture()
        paramutils.createParamAtLocation("KatanaBebop.IRFNode", NodegraphAPI.GetRootNode(), paramutils.STRING)
        Utils.UndoStack.EnableCapture()

    def __setupDefaultIRFNode(self):
        """ On init, this creates the default IRF Node if none exist"""
        self.__setupDefaultIRFParam()
        irf_node_name = self.irfNodeParam().getValue(0)
        irf_node = NodegraphAPI.GetNode(irf_node_name)

        if not irf_node:
            irf_node = NodegraphAPI.CreateNode("InteractiveRenderFilters", NodegraphAPI.GetRootNode())
            self.setDefaultIRFNode(irf_node)

    """ PROPERTIES """
    @staticmethod
    def defaultIRFNode():
        if IRFManagerTab.irfNodeParam():
            return NodegraphAPI.GetNode(IRFManagerTab.irfNodeParam().getValue(0))
        return None

    @staticmethod
    def setDefaultIRFNode(irf_node):
        """ Sets the default IRF node

        Args:
            irf_node (Node): Node that will be set as the default IRF node """
        IRFManagerTab.__setupDefaultIRFParam()
        IRFManagerTab.irfNodeParam().setExpressionFlag(True)
        IRFManagerTab.irfNodeParam().setExpression("@{irf_node_name}".format(irf_node_name=irf_node.getName()))

    @staticmethod
    def irfNodeParam():
        return NodegraphAPI.GetRootNode().getParameter("KatanaBebop.IRFNode")

    """ WIDGETS """
    def irfNodeWidget(self):
        return self._irf_node_widget

    def createWidget(self):
        return self._create_widget

    def activationWidget(self):
        return self._activation_widget

    def mainWidget(self):
        return self._main_widget

    def viewWidget(self):
        return self._view_widget

    """ EVENTS """
    def showEvent(self, event):
        self.__setupDefaultIRFNode()
        return UI4.Tabs.BaseTab.showEvent(self, event)


class IRFNodeWidget(ListInputWidget):
    """ Allows the user to choose which IRF Node they want to save their changes to"""
    def __init__(self, parent=None, item_list=[]):
        super(IRFNodeWidget, self).__init__(parent, item_list)
        self.setCleanItemsFunction(self.populateIRFNodes)
        self.setUserFinishedEditingEvent(self.updateDefaultIRFNode)

    def updateDefaultIRFNode(self, widget, value):
        if value in [node.getName() for node in IRFUtils.getAllRenderFilterContainers()]:
            node = NodegraphAPI.GetNode(value)
            IRFManagerTab.setDefaultIRFNode(node)
        else:
            self.setText(IRFManagerTab.defaultIRFNode().getName())

    def populateIRFNodes(self):
        return [[node.getName()] for node in IRFManagerTab.getAllRenderFilterContainers()]


class IRFActivationOrganizerWidget(AbstractIRFOrganizerWidget):
    """ Holds all of the currently activate filters """
    def __init__(self, parent=None):
        super(IRFActivationOrganizerWidget, self).__init__(parent)
        self.setAcceptDrops(True)
        self.setIsRootDroppable(True)
        self.setItemDeleteEvent(self.disableFilter)

    def showEvent(self, event):
        self._categories = {}
        self.clearModel()
        active_filters = IRFUtils.getAllActiveFilters()
        for render_filter_node in active_filters:
            index = self.createFilterItem(render_filter_node)
            self.view().setExpanded(index.parent(), True)
            # self.view().expand(index.parent())

        return AbstractIRFOrganizerWidget.showEvent(self, event)

    def disableFilter(self, item):
        IRFUtils.enableRenderFilter(item.getArg("node"), False)

    def dropEvent(self, event):
        node_name = event.mimeData().data(IRFUtils.IS_IRF).data()
        node = NodegraphAPI.GetNode(node_name)
        self.createFilterItem(node)
        IRFUtils.enableRenderFilter(node, True)

        return AbstractIRFOrganizerWidget.dropEvent(self, event)

    def dragEnterEvent(self, event):
        if IRFUtils.IS_IRF in event.mimeData().formats():
            event.accept()
        return AbstractIRFOrganizerWidget.dragEnterEvent(self, event)


class IRFViewWidget(IRFActivationOrganizerWidget):
    def __init__(self, parent=None):
        super(IRFViewWidget, self).__init__(parent)


class IRFActivationWidget(ShojiLayout):
    """ Widget that will allow the user to enable/disable IRFs"""

    def __init__(self, parent=None):
        super(IRFActivationWidget, self).__init__(parent)

        # setup available filters widget
        self._available_filters_widget = QWidget()
        self._available_filters_layout = QVBoxLayout(self._available_filters_widget)
        self._available_filters_organizer_widget = AbstractIRFOrganizerViewWidget(self)
        self._available_filters_layout.addWidget(QLabel("Available Filters"))
        self._available_filters_layout.addWidget(self._available_filters_organizer_widget)

        # setup active filters widget
        self._activated_filters_widget = QWidget()
        self._activated_filters_layout = QVBoxLayout(self._activated_filters_widget)
        self._activated_filters_organizer_widget = IRFActivationOrganizerWidget(self)
        self._activated_filters_layout.addWidget(QLabel("Active Filters"))
        self._activated_filters_layout.addWidget(self._activated_filters_organizer_widget)

        # setup style
        self.setOrientation(Qt.Horizontal)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # setup main layout
        self.addWidget(self._available_filters_widget)
        self.addWidget(self._activated_filters_widget)


""" CREATE """
class IRFCreateOrganizerWidget(AbstractIRFOrganizerViewWidget):
    def __init__(self, parent=None):
        super(IRFCreateOrganizerWidget, self).__init__(parent)

        # setup events
        self.setIndexSelectedEvent(self.__irfSelectionChanged)
        self.setTextChangedEvent(self.__nameChanged)
        self.setDropEvent(self.__itemParentChanged)
        self.setItemDeleteEvent(self.__deleteFilter)

        self.addContextMenuEvent("Create New Category", self.__createNewCategory)
        self.addContextMenuEvent("Create New Filter", self.__createNewFilter)

    def __itemParentChanged(self, data, items, model, row, parent):
        """ On drop update the item drops category to the new parents"""
        for item in items:
            if parent == self.rootItem():
                item.getArg("node").getParameter("category").setValue("", 0)
            else:
                item.getArg("node").getParameter("category").setValue(parent.name(), 0)

    def __nameChanged(self, item, old_value, new_value):
        """ When the user changes a name:
                if it is a FILTER, update the filters name
                if it is a CATEGORY, update all categories to that new name"""
        if item.getArg("type") == IRFManagerTab.FILTER:
            item.getArg("node").getParameter("name").setValue(new_value, 0)
        if item.getArg("type") == IRFManagerTab.CATEGORY:
            for render_filter_node in IRFManagerTab.getAllRenderFilterNodes():
                if render_filter_node.getParameter("category").getValue(0) == old_value:
                    render_filter_node.getParameter("category").setValue(new_value, 0)

    def __createNewFilter(self, item, indexes):
        """ Creates a new render filter"""
        default_irf_node = self.defaultIRFNode()
        new_filter_node = default_irf_node.buildChildNode()
        self.__createFilterItem(new_filter_node)

    def __deleteFilter(self, item):
        node = item.getArg("node")
        nodeutils.disconnectNode(node, input=True, output=True, reconnect=True)
        # input_port = node.getInputPortByIndex(0).getConnectedPorts()[0]
        # output_port = node.getOutputPortByIndex(0).getConnectedPorts()[0]
        # input_port.connect(output_port)
        node.delete()

    def __createNewCategory(self, item, indexes):
        self.__createCategoryItem("<New Category>")

    def __irfSelectionChanged(self, item, enabled):
        if enabled:
            if item.getArg("type") == IRFUtils.FILTER:
                irf_create_wiget = getWidgetAncestor(self, IRFCreateWidget)
                irf_create_wiget.nodegraphWidget().setNode(item.getArg("node"))


class IRFCreateWidget(ShojiLayout):
    """ Widget responsible for creating/modifying IRFs

    Widgets:
        irf_node_widget (ListInputWidget): The current InteractiveRenderFilters node that will be used
            when creating new filters
        irf_organizer_widget (ModelViewWidget): An organizational view of all of the IRF's in the scene.
            The user can rename, delete, edit the name/category, etc, of IRF's here.
        nodegraph_widget (GroupNodeEditorWidget): The area that the user can add nodes to the internal
            structure of the IRF.  Previously, this only had a list view, now it's a nodegraph.
    """
    def __init__(self, parent=None):
        super(IRFCreateWidget, self).__init__(parent)
        self.setObjectName("Create Widget")

        # setup gui
        QVBoxLayout(self)
        self._irf_node_widget = IRFNodeWidget(parent=self)
        self._irf_node_labelled_widget = LabelledInputWidget(
            name="Node", delegate_widget=self._irf_node_widget, default_label_length=100)

        self._irf_organizer_widget = IRFCreateOrganizerWidget(self)
        self._nodegraph_widget = GroupNodeEditorWidget(self, node=NodegraphAPI.GetRootNode())

        self.addWidget(self._irf_node_labelled_widget)
        self.addWidget(self._irf_organizer_widget)
        self.addWidget(self._nodegraph_widget)

        # set default irf node
        self._irf_node_widget.setText(IRFManagerTab.defaultIRFNode().getName())

    def defaultIRFNode(self):
        return NodegraphAPI.GetNode(self.irfNodeWidget().text())

    """ WIDGETS """
    def irfNodeWidget(self):
        return self._irf_node_widget

    def irfOrganizerWidget(self):
        return self._irf_organizer_widget

    def nodegraphWidget(self):
        return self._nodegraph_widget



if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication

    from cgwidgets.utils import centerWidgetOnScreen, setAsAlwaysOnTop
    app = QApplication(sys.argv)

    widget = IRFManagerTab()
    setAsAlwaysOnTop(widget)
    widget.show()
    centerWidgetOnScreen(widget)

    sys.exit(app.exec_())