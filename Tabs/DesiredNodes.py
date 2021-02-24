'''
Creates a tab that allows users to flags nodes as "desirable".

This tab has multiple groups inside of it so that the user may
make subcategories of desirable nodes.

How it works:
This works by storing a parameter string on the project settings called "_desirable_nodes".
This parameter will essentially be a CSV list of all of the possible groups that the user
has created for this Katana File.

When the user clicks on a specified group in the tab, Katana will look at all of the nodes
and look for a parameter called "_is_desirable", it will then check that parameter
to see if it fits into the current group that the user has selected, and if so, add
a reference to this item for the user.

Please note that at this point in time, sub groups of groups are not available.  This is something
that may or may not be added in the future depending on how many shits I give.

Hierarchy:
    DesiredNodes --> (UI4.Tabs.BaseTab)
        |- QVBoxLayout
            |- desired_nodes_tab_widget --> (ShojiModelViewWidget)
                |-* DesiredNodesShojiPanel --> (NodeViewWidget --> ShojiModelViewWidget)

ToDo
    - Add group functionality?
        gross.. then I have to store data or something
            could potentially just save it on the actual param data?
'''
from qtpy.QtWidgets import QVBoxLayout, QSizePolicy
from qtpy.QtCore import Qt

from cgwidgets.widgets import ShojiModelViewWidget, StringInputWidget
from cgwidgets.views import AbstractDragDropListView
from cgwidgets.utils import getWidgetAncestor, attrs

from Katana import UI4 , NodegraphAPI, Utils
from Widgets2 import NodeViewWidget


class DesiredNodes(UI4.Tabs.BaseTab):
    def __init__(self, parent=None):
        super(DesiredNodes, self).__init__(parent)
        # create default parameter
        self.createProjectSettingsEntry()

        # create main widget
        self.desired_nodes_frame = DesiredNodesFrame(self)

        # setup main layout
        QVBoxLayout(self)
        self.layout().addWidget(self.desired_nodes_frame)

    def createProjectSettingsEntry(self):
        """
        Ensures that the parameter "_desirable_nodes" exists in the project settings.
        """
        root_node = NodegraphAPI.GetRootNode()
        desirable_groups_param = root_node.getParameter("_desirable_nodes")

        # create param if it doesn't exist
        if not desirable_groups_param:
            root_node.getParameters().createChildString("_desirable_nodes", "")


class DesiredNodesFrame(ShojiModelViewWidget):
    """
    Main frame for holding all of the individual desirable node panels
    """
    def __init__(self, parent=None):
        super(DesiredNodesFrame, self).__init__(parent)

        self.setHeaderPosition(attrs.NORTH, attrs.SOUTH)

        self.setDelegateTitleIsShown(False)
        self.setMultiSelect(False)

        # setup dynamic widget
        self.setDelegateType(
            ShojiModelViewWidget.DYNAMIC,
            dynamic_widget=DesiredNodesShojiPanel,
            dynamic_function=DesiredNodesShojiPanel.populate
        )

        # node create widget
        self.create_desirable_group_widget = StringInputWidget(self)
        self.addHeaderDelegateWidget([Qt.Key_Q], self.create_desirable_group_widget, modifier=Qt.NoModifier, focus=True)
        self.create_desirable_group_widget.setUserFinishedEditingEvent(self.createNewDesirableGroup)

        # setup events
        self.setHeaderItemDeleteEvent(self.purgeDesirableGroup)


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

    def showEvent(self, event):
        """
        On show, update the view
        """
        self.populate()
        return ShojiModelViewWidget.showEvent(self, event)

    def populate(self):
        """
        Loads all of the desirable groups from the root node
        """
        # clear model
        self.clearModel()

        # repopulate
        desirable_groups = filter(None, self.getParam().getValue(0).split(','))
        for group in desirable_groups:
            self.addNewGroup(group)

    def getParam(self):
        """
        Returns (parameter): that stores the data for all of the desirable node groups
        """
        root_node = NodegraphAPI.GetRootNode()
        desirable_groups_param = root_node.getParameter("_desirable_nodes")
        return desirable_groups_param

    def desiredNodes(self):
        selection = self.getAllSelectedIndexes()
        if 0 < len(selection):
            selected_index = selection[0]
            print(selected_index)

    def addNewGroup(self, name):
        """
        Creates a new model index
        Args:
            name (str): the name...
        """
        # create new index
        self.insertShojiWidget(0, column_data={'name': name})

    def createNewDesirableGroup(self, widget, value):
        name = self.create_desirable_group_widget.text()
        if name:
            self.addNewGroup(name)

            # update katana settings
            old_value = self.getParam().getValue(0)
            new_value = ','.join(filter(None, [old_value, name]))
            self.getParam().setValue(str(new_value), 0)

            # reset widget
            widget.setText('')
            widget.hide()

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


PluginRegistry = [("KatanaPanel", 2, "Desired Nodes", DesiredNodes)]