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
        delegate = AbstractIRFOrganizerWidgetDelegate(self)
        self.view().setItemDelegate(delegate)

        # context menu
        self.addContextMenuEvent("Expand All", self.expandAll)
        self.addContextMenuEvent("Collapse All", self.collapseAll)

    def expandAll(self, item, indexes):
        self.view().expandAll()

    def collapseAll(self,  item, indexes):
        self.view().collapseAll()

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
        # self.view().setExpanded(category_index, True)
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


class AbstractIRFOrganizerViewWidget(AbstractIRFOrganizerWidget):
    """ Organizer View widget, this will display ALL of the IRFs in the scene"""
    def __init__(self, parent=None):
        super(AbstractIRFOrganizerViewWidget, self).__init__(parent)
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


class AbstractIRFOrganizerWidgetDelegate(AbstractDragDropModelDelegate):
    def __init__(self, parent=None):
        super(AbstractIRFOrganizerWidgetDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        """ Creates the editor widget.

        This is needed to set a different delegate for different columns"""
        if index.column() == 0:
            return AbstractDragDropModelDelegate.createEditor(self, parent, option, index)
        else:
            return None