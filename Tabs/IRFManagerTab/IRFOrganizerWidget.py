import json

from qtpy.QtWidgets import QVBoxLayout, QLabel, QWidget
from qtpy.QtCore import Qt, QByteArray

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

from cgwidgets.utils import getWidgetAncestor, getWidgetAncestorByObjectName

from Utils2 import widgetutils, paramutils, nodeutils
from Widgets2 import GroupNodeEditorWidget
from .IRFUtils import IRFUtils

""" ABSTRACT ORGANIZERS"""
class AbstractIRFOrganizerWidget(ModelViewWidget):
    """ This widget is in charge of organizing the different IRF widgets.

    - Inside of here, the user can change IRF names/categories.
    - Batch update category names
    - Create new categories/filters

    Attributes:
        categories (dict): of all of the categories and their coresponding items
            {"categoryName": ModelViewItem}
        """
    def __init__(self, parent=None):
        super(AbstractIRFOrganizerWidget, self).__init__(parent)

        # setup default attrs
        self._categories = {}
        self.setPresetViewType(ModelViewWidget.TREE_VIEW)
        self.setIsEnableable(False)
        self.setHeaderData(["name", "type"])

        #
        self.view().header().resizeSection(0, 300)
        delegate = DefaultOrganizerDelegate(self)
        self.view().setItemDelegate(delegate)

    """ PROPERTIES """
    def categories(self):
        return self._categories

    def defaultIRFNode(self):
        #create_widget = getWidgetAncestor(self, IRFCreateWidget)
        create_widget = getWidgetAncestorByObjectName(self, "Create Widget")
        return create_widget.defaultIRFNode()

    """ UTILS """
    def createCategoryItem(self, category):
        """ Creates a new category item

        Args:
            category (str): name of category to create"""
        data = {"name": category, "type": IRFUtils.CATEGORY}
        category_index = self.insertNewIndex(
            0, name=category, column_data=data, is_deletable=False, is_dropable=True, is_dragable=False)
        category_item = category_index.internalPointer()
        self.categories()[category] = category_item

        return category_item

    def createFilterItem(self, render_filter_node):
        """ Creates a new item from the node provided"""
        name = render_filter_node.getParameter('name').getValue(0)
        category = render_filter_node.getParameter('category').getValue(0)

        # get parent index
        parent_item = self.rootItem()
        if category:
            # get category item
            if category not in self.categories().keys():
                parent_item = self.createCategoryItem(category)
            else:
                parent_item = self.categories()[category]

        parent_index = self.getIndexFromItem(parent_item)

        data = {"name": name, "type": IRFUtils.FILTER, "node": render_filter_node}
        index = self.insertNewIndex(0, name=name, column_data=data, parent=parent_index, is_dropable=False)

        return index


class AbstractIRFAvailableOrganizerWidget(AbstractIRFOrganizerWidget):
    """ Organizer View widget, this will display ALL of the IRFs in the scene"""
    def __init__(self, parent=None):
        super(AbstractIRFAvailableOrganizerWidget, self).__init__(parent)
        self.setAddMimeDataFunction(self.addMimedata)

    def addMimedata(self, mimedata, items):
        """ Adds the node name to the mimedata

        Args:
            mimedata (QMimedata): from dragEvent
            items (list): of ModelViewItems"""

        ba = QByteArray()
        ba.append(items[0].getArg("node").getName())

        mimedata.setData(IRFUtils.IS_IRF, ba)

        return mimedata

    def populate(self):
        """ Creates all of the IRF items/category items"""
        render_filter_nodes = IRFUtils.getAllRenderFilterNodes()
        for render_filter_node in render_filter_nodes:
            self.createFilterItem(render_filter_node)

    """ EVENTS """
    def showEvent(self, event):
        self.clearModel()
        self._categories = {}
        self.populate()
        return ModelViewWidget.showEvent(self, event)


class AbstractIRFActiveFiltersOrganizerWidget(AbstractIRFOrganizerWidget):
    """ Holds all of the currently activate filters """
    def __init__(self, parent=None):
        super(AbstractIRFActiveFiltersOrganizerWidget, self).__init__(parent)

    def showEvent(self, event):
        self._categories = {}
        self.clearModel()
        active_filters = IRFUtils.getAllActiveFilters()
        for render_filter_node in active_filters:
            index = self.createFilterItem(render_filter_node)
            self.view().setExpanded(index.parent(), True)
            # self.view().expand(index.parent())

        return AbstractIRFOrganizerWidget.showEvent(self, event)


""" DELEGATES """
class CreateOrganizerDelegate(AbstractDragDropModelDelegate):
    def __init__(self, parent=None):
        super(CreateOrganizerDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        """ Creates the editor widget.

        This is needed to set a different delegate for different columns"""
        if index.column() == 0:
            return AbstractDragDropModelDelegate.createEditor(self, parent, option, index)
        else:
            return None


class DefaultOrganizerDelegate(AbstractDragDropModelDelegate):
    """ Default delegate to block editing"""
    def __init__(self, parent=None):
        super(DefaultOrganizerDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        return


""" ORGANIZERS"""
class CreateAvailableFiltersOrganizerWidget(AbstractIRFAvailableOrganizerWidget):
    """ Available filters in the Create widget"""
    def __init__(self, parent=None):
        super(CreateAvailableFiltersOrganizerWidget, self).__init__(parent)

        # setup events
        self.setIndexSelectedEvent(self.__irfSelectionChanged)
        self.setTextChangedEvent(self.__nameChanged)
        self.setDropEvent(self.__itemParentChanged)
        self.setItemDeleteEvent(self.__deleteFilter)

        # context menu
        self.addContextMenuSeparator()
        self.addContextMenuEvent("Create New Category", self.__createNewCategory)
        self.addContextMenuEvent("Create New Filter", self.__createNewFilter)

        # setup delegate
        delegate = CreateOrganizerDelegate(self)
        self.view().setItemDelegate(delegate)

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
        if item.getArg("type") == IRFUtils.FILTER:
            item.getArg("node").getParameter("name").setValue(new_value, 0)
        if item.getArg("type") == IRFUtils.CATEGORY:
            for render_filter_node in IRFUtils.getAllRenderFilterNodes():
                if render_filter_node.getParameter("category").getValue(0) == old_value:
                    render_filter_node.getParameter("category").setValue(new_value, 0)

    def __createNewFilter(self, item, indexes):
        """ Creates a new render filter"""
        default_irf_node = self.defaultIRFNode()
        new_filter_node = default_irf_node.buildChildNode()
        self.createFilterItem(new_filter_node)

    def __deleteFilter(self, item):
        node = item.getArg("node")
        nodeutils.disconnectNode(node, input=True, output=True, reconnect=True)
        # input_port = node.getInputPortByIndex(0).getConnectedPorts()[0]
        # output_port = node.getOutputPortByIndex(0).getConnectedPorts()[0]
        # input_port.connect(output_port)
        node.delete()

    def __createNewCategory(self, item, indexes):
        self.createCategoryItem("<New Category>")

    def __irfSelectionChanged(self, item, enabled):
        if enabled:
            if item.getArg("type") == IRFUtils.FILTER:
                irf_create_wiget = getWidgetAncestorByObjectName(self, "Create Widget")
                irf_create_wiget.nodegraphWidget().setNode(item.getArg("node"))


class ViewActiveFiltersOrganizerWidget(AbstractIRFActiveFiltersOrganizerWidget):
    """ Available filters organizer to be used in the VIEW widget"""
    def __init__(self, parent=None):
        super(ViewActiveFiltersOrganizerWidget, self).__init__(parent)
        self.setAcceptDrops(False)
        self.setIsDeletable(False)
        self.setIsDraggable(False)
        self.setIsDroppable(False)
        self.setIsRootDroppable(False)


class ActivateAvailableFiltersOrganizerWidget(AbstractIRFAvailableOrganizerWidget):
    def __init__(self, parent=None):
        super(ActivateAvailableFiltersOrganizerWidget, self).__init__(parent)
        self.setIsDeletable(False)


class ActivateActiveFiltersOrganizerWidget(AbstractIRFActiveFiltersOrganizerWidget):
    """ Available filters to be displayed in the Activation Widget"""
    def __init__(self, parent=None):
        super(ActivateActiveFiltersOrganizerWidget, self).__init__(parent)
        self.setAcceptDrops(True)
        self.setIsRootDroppable(True)
        self.setItemDeleteEvent(self.disableFilter)
        self.setIsDraggable(False)

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

