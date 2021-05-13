"""
Creates a tab that allows users to flags nodes as "desirable".

This tab has multiple groups inside of it so that the user may
make subcategories of desirable nodes.

How it works:
This works by storing a parameter string on the project settings called "KatanaBebop.DesirableNodes.data".
This parameter will essentially be a CSV list of all of the possible groups that the user
has created for this Katana File.

When the user clicks on a specified group in the tab, Katana will look at all of the nodes
and look for a parameter called "_is_desirable", it will then check that parameter
to see if it fits into the current group that the user has selected, and if so, add
a reference to this item for the user.

Please note that at this point in time, sub groups of groups are not available.  This is something
that may or may not be added in the future depending on how many shits I give.

Hierarchy:
    DesiredNodesTab --> (UI4.Tabs.BaseTab)
        |- QVBoxLayout
            |- desired_nodes_tab_widget --> (ShojiModelViewWidget)
                |-* DesiredNodesShojiPanel --> (NodeViewWidget --> ShojiModelViewWidget)

ToDo
    - Add group functionality?
        gross.. then I have to store data or something
            could potentially just save it on the actual param data?
"""
from qtpy.QtWidgets import QVBoxLayout, QSizePolicy, QApplication
from qtpy.QtCore import Qt

from cgwidgets.widgets import ShojiModelViewWidget, StringInputWidget, LabelledInputWidget, OverlayInputWidget
from cgwidgets.views import AbstractDragDropListView
from cgwidgets.utils import getWidgetAncestor
from cgwidgets.settings import attrs

from Katana import UI4 , NodegraphAPI, Utils
from Widgets2 import NodeViewWidget
from Utils2 import nodeutils, getFontSize, paramutils


class DesiredNodesTab(UI4.Tabs.BaseTab):
    """
    Main tab widget for the desirable widgets
    """
    NAME = 'Desired Nodes'
    def __init__(self, parent=None):
        super(DesiredNodesTab, self).__init__(parent)
        # create default parameter
        self.createDesirableNodesParam()

        # create main widget
        self.desired_nodes_frame = DesiredNodesFrame(self)

        # setup main layout
        QVBoxLayout(self)
        self.layout().addWidget(self.desired_nodes_frame)

    def createDesirableNodesParam(self):
        """
        Ensures that the parameter "KatanaBebop.DesirableNodes.data" exists in the project settings.
        """
        param_location = "KatanaBebop.DesirableNodes.data"
        node = NodegraphAPI.GetRootNode()
        param_type = paramutils.STRING
        paramutils.createParamAtLocation(param_location, node, param_type, initial_value="")


class DesiredNodesFrame(ShojiModelViewWidget):
    """
    Main frame for holding all of the individual desirable node panels
    """
    def __init__(self, parent=None):
        super(DesiredNodesFrame, self).__init__(parent)

        self.setHeaderDefaultLength(getFontSize() * 6)
        self._selected_items = []
        self.setHeaderPosition(attrs.NORTH, attrs.SOUTH)
        self.setOrientation(Qt.Vertical)
        self.setDelegateTitleIsShown(True)
        self.setMultiSelect(True)

        # setup dynamic widget
        self.setDelegateType(
            ShojiModelViewWidget.DYNAMIC,
            dynamic_widget=DesiredNodesShojiPanel,
            dynamic_function=DesiredNodesShojiPanel.populate
        )

        # tab create widget
        self.create_desirable_group_input_widget = StringInputWidget()
        self.create_desirable_group_widget = LabelledInputWidget(
            self,
            default_label_length=getFontSize() * 12,
            delegate_widget=self.create_desirable_group_input_widget,
            direction=Qt.Horizontal,
            name="Create New Tab",
            )
        self.addHeaderDelegateWidget([], self.create_desirable_group_widget, modifier=Qt.NoModifier, focus=True)
        self.create_desirable_group_widget.setUserFinishedEditingEvent(self.createNewDesirableGroup)
        self.create_desirable_group_widget.viewWidget().setDisplayMode(OverlayInputWidget.DISABLED)
        self.create_desirable_group_widget.show()

        # setup events
        self.setHeaderItemDeleteEvent(self.purgeDesirableGroup)
        self.setHeaderItemSelectedEvent(self.itemSelected)

        self.setHeaderItemIsEnableable(False)
        self.setHeaderItemIsDropEnabled(False)

        # setup style
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)

    def purgeDesirableGroup(self, item):
        """
        Removes the currently selected desirable group item
        """
        name = item.columnData()['name']
        current_groups = filter(None, self.getParam().getValue(0).split(','))
        current_groups.remove(name)
        new_groups = ','.join(current_groups)
        self.getParam().setValue(new_groups, 0)

    def itemSelected(self, item, enabled, column=0):
        if column == 0:
            if enabled:
                self._selected_items.append(item.columnData()['name'])
            else:
                self._selected_items.remove(item.columnData()['name'])

    def showEvent(self, event):

        self.populate()
        return ShojiModelViewWidget.showEvent(self, event)
    # def enterEvent(self, event):
    #     """
    #     On show, update the view
    #     """
    #     self.populate()
    #     #return ShojiModelViewWidget.enterEvent(self, event)

    def populate(self):
        """
        Loads all of the desirable groups from the root node
        """
        # store temp as will be overwritten
        _selected_items = [item for item in self._selected_items]
        # clear model
        self.clearModel()

        # repopulate
        desirable_groups = filter(None, self.getParam().getValue(0).split(','))
        for group in desirable_groups:
            self.addNewGroup(group)

        # reselect index
        for item in _selected_items:
            for index in self.model().findItems(item):
                self.setIndexSelected(index, True)

    def getParam(self):
        """
        Returns (parameter): that stores the data for all of the desirable node groups
        """
        # create param if it doesnt exist
        param_location = "KatanaBebop.DesirableNodes.data"
        node = NodegraphAPI.GetRootNode()
        param_type = paramutils.STRING
        paramutils.createParamAtLocation(param_location, node, param_type, initial_value="")

        # get param
        desirable_groups_param = node.getParameter("KatanaBebop.DesirableNodes.data")
        return desirable_groups_param

    def desiredNodes(self):
        selection = self.getAllSelectedIndexes()
        if 0 < len(selection):
            selected_index = selection[0]

    def addNewGroup(self, name):
        """
        Creates a new model index
        Args:
            name (str): the name...
        """
        # create new index
        new_index = self.insertShojiWidget(0, column_data={'name': name})
        self.setIndexSelected(new_index, True)
        return new_index

    def createNewDesirableGroup(self, widget, value):
        name = self.create_desirable_group_input_widget.text()
        if name:
            self.addNewGroup(name)

            # update katana settings
            old_value = self.getParam().getValue(0)
            new_value = ','.join(filter(None, [old_value, name]))
            self.getParam().setValue(str(new_value), 0)

            # reset widget
            widget.setText('')
            # widget.hide()

            # TODO Set focus back on header?
            header_view_widget = self.headerViewWidget()
            header_view_widget.setFocus()


class DesiredNodesShojiPanel(NodeViewWidget):
    """
    A single panel in the Shoji.

    This will display one group of desirable nodes to the user.

    Attributes:
        name (str): name of the current group that is being shown.
    """
    def __init__(self, parent=None):
        super(DesiredNodesShojiPanel, self).__init__(parent)
        # setup custom view
        view = DesiredNodesView(self)
        self.setHeaderViewWidget(view)
        self.setHeaderItemDeleteEvent(self.makeUndesirable)

        # setup shoji style
        self.setMultiSelect(True)

        self.desired_nodes = []
        self._name = "Hello"

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)

        # setup context menu
        # for some reason I have to add this here.. instead of in the base widget...
        self.addContextMenuEvent("Go To Node", self.goToNode)

    """ EVENTS """
    def goToNode(self, index, selected_indexes):
        item = index.internalPointer()

        if item:
            node = self.getNodeFromItem(item)
            nodeutils.goToNode(node, frame=True)

    """ PROPERTIES """
    def name(self):
        return self._name

    def setName(self, name):
        self._name = name

    """ DESIRABLE """
    def setNodeDesirability(self, node, enabled):
        """
        Sets a nodes flag to be desirable

        Args:
            node (Node): to make desirable
            enabled (bool): how $3xy this node is
        """
        if enabled:
            if node not in self.desired_nodes:
                node_view_widget = getWidgetAncestor(self, NodeViewWidget)
                node_view_widget.createNewIndexFromNode(node)
                self.desired_nodes.append(node)
                self._makeDesirableParam(node, enabled)

        else:
            self._makeDesirableParam(node, False)

    def _makeDesirableParam(self, node, enabled):
        """
        Creates/Destroys the hidden reference to the "_is_desired" param

        Args:
            node (Node): to make desirable
            enabled (bool): how $3xy this node is

        # todo make this reference hidden
        """
        desirable_param = node.getParameter("_is_desired")

        if enabled:
            node.getParameters().createChildString("_is_desired", self.name())
        else:
            if desirable_param:
                node.getParameters().deleteChild(desirable_param)

    def makeUndesirable(self, item):
        """
        On Delete, this will remove the desirable reference to the node
        Args:
            item (ShojiModelItem): item currently selected

        """
        node = self.getNodeFromItem(item)
        self.setNodeDesirability(node, False)
        self.desired_nodes.remove(node)

    @staticmethod
    def populate(parent, widget, item):
        """
        Adds all of the indexes for every node that has been
        chosen as "desirable" by the user
            def updateGUI(parent, widget, item):

            parent (ShojiModelViewWidget)
            widget (ShojiModelDelegateWidget)
            item (ShojiModelItem)
            self --> widget.getMainWidget()

        """
        this = widget.getMainWidget()

        # clear model
        this.clearModel()

        # set attrs
        this.setName(item.columnData()['name'])
        # force repopulate
        this.desired_nodes = []
        for node in NodegraphAPI.GetAllNodes():
            is_desired = node.getParameter('_is_desired')
            if is_desired:
                if is_desired.getValue(0) == this.name():
                    this.createNewIndexFromNode(node)
                    this.desired_nodes.append(node)


class DesiredNodesView(AbstractDragDropListView):
    """


    """
    def __init__(self, parent=None):
        super(DesiredNodesView, self).__init__(parent)

    """ EVENTS """
    def dragEnterEvent(self, event):
        mimedata = event.mimeData()
        if mimedata.hasFormat('nodegraph/nodes'):
            event.accept()
        return AbstractDragDropListView.dragEnterEvent(self, event)

    def dropEvent(self, event):
        """
        This will handle all drops into the view from the Nodegraph

        Alot of this is copy/paste from nodeMovedEvent
        """
        mimedata = event.mimeData()
        if mimedata.hasFormat('nodegraph/nodes'):
            nodes_list = mimedata.data('nodegraph/nodes').data().split(',')
            parent_widget = getWidgetAncestor(self, DesiredNodesShojiPanel)
            for node_name in nodes_list:
                # get node
                node = NodegraphAPI.GetNode(node_name)
                parent_widget.setNodeDesirability(node, True)

        return AbstractDragDropListView.dropEvent(self, event)


class CreateDesirableGroupWidget(LabelledInputWidget):
    def __init__(self, parent=None, delegate_widget=None):
        super(CreateDesirableGroupWidget, self).__init__(
            parent,
            name="Create New Item",
            default_label_length=100,
            direction=Qt.Horizontal,
            delegate_widget=delegate_widget
        )