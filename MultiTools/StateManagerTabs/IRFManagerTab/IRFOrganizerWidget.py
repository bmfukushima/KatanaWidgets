from qtpy.QtCore import QByteArray

from Katana import UI4, NodegraphAPI, RenderManager, Utils

from cgwidgets.widgets import ModelViewWidget
from cgwidgets.views import AbstractDragDropModelDelegate
from cgwidgets.utils import getWidgetAncestorByObjectName

from Utils2 import nodeutils, irfutils, widgetutils


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
        self._is_category_item_deletable = False
        self._is_category_item_draggable = False
        self.setPresetViewType(ModelViewWidget.TREE_VIEW)
        self.setIsEnableable(False)
        self.setHeaderData(["name", "type"])

        #
        self.view().header().resizeSection(0, 300)
        delegate = DefaultOrganizerDelegate(self)
        self.view().setItemDelegate(delegate)

    """ PROPERTIES """
    def categories(self):
        categories = {}
        for child in self.rootItem().children():
            if child.getArg("type") == irfutils.CATEGORY:
                categories[child.name()] = child
        return categories

    def isCategoryItemDeletable(self):
        return self._is_category_item_deletable

    def setIsCategoryItemDeletable(self, is_deletable):
        self._is_category_item_deletable = is_deletable
        for item in self.categories().values():
            item.setIsDeletable(is_deletable)

    def isCategoryItemDraggable(self):
        return self._is_category_item_draggable

    def setIsCategoryItemDraggable(self, is_draggable):
        self._is_category_item_draggable = is_draggable
        for item in self.categories().values():
            item.setIsDraggable(is_draggable)

    """ UTILS """
    def createCategoryItem(self, category):
        """ Creates a new category item

        Args:
            category (str): name of category to create"""
        data = {"name": category, "type": irfutils.CATEGORY}
        category_index = self.insertNewIndex(
            0, name=category, column_data=data, is_deletable=self.isCategoryItemDeletable(), is_droppable=True, is_draggable=self.isCategoryItemDraggable())
        category_item = category_index.internalPointer()

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

        data = {"name": name, "type": irfutils.FILTER, "node": render_filter_node}
        index = self.insertNewIndex(0, name=name, column_data=data, parent=parent_index, is_droppable=False)

        return index

    """ UPDATE """
    def populate(self):
        pass

    def clear(self):
        self.clearModel()

    def update(self):
        self.clearModel()
        self.populate()

class AbstractIRFAvailableOrganizerWidget(AbstractIRFOrganizerWidget):
    """ Organizer View widget, this will display ALL of the IRFs in the scene"""
    def __init__(self, parent=None):
        super(AbstractIRFAvailableOrganizerWidget, self).__init__(parent)
        self.setAddMimeDataFunction(self.addMimedata)
        # self.populate()

    def addMimedata(self, mimedata, items):
        """ Creates a CSV List of the names of the Render Filter nodes to be activated

        Args:
            mimedata (QMimedata): from dragEvent
            items (list): of ModelViewItems"""

        ba = QByteArray()
        nodes = []
        for item in items:
            if item.getArg("type") == irfutils.FILTER:
                nodes.append(item.getArg("node").getName())
            elif item.getArg("type") == irfutils.CATEGORY:
                for child in item.children():
                    nodes.append(child.getArg("node").getName())

        ba.append(",".join(nodes))

        mimedata.setData(irfutils.IS_IRF, ba)

        return mimedata

    def populate(self):
        """ Creates all of the IRF items/category items"""
        render_filter_nodes = irfutils.getAllRenderFilterNodes()

        for render_filter_node in render_filter_nodes:
            self.createFilterItem(render_filter_node)


class AbstractIRFActiveFiltersOrganizerWidget(AbstractIRFOrganizerWidget):
    """ Holds all of the currently activate filters """
    def __init__(self, parent=None):
        super(AbstractIRFActiveFiltersOrganizerWidget, self).__init__(parent)

    def populate(self):
        active_filters = irfutils.getAllActiveFilters()
        for render_filter_node in active_filters:
            index = self.createFilterItem(render_filter_node)
            self.view().setExpanded(index.parent(), True)


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
    """ Available filters in the CREATE widget"""
    def __init__(self, parent=None):
        super(CreateAvailableFiltersOrganizerWidget, self).__init__(parent)

        # setup custom model
        """ This is needed to ensure all tabs remain synchronized"""
        if not hasattr(widgetutils.katanaMainWindow(), "_irf_create_available_filters_model"):
            widgetutils.katanaMainWindow()._irf_create_available_filters_model = self.model()
            self.populate()
        else:
            self.setModel(widgetutils.katanaMainWindow()._irf_create_available_filters_model)

        # setup events
        self.setIndexSelectedEvent(self.__irfSelectionChanged)
        self.setTextChangedEvent(self.__nameChanged)
        self.setDropEvent(self.__itemParentChanged)
        self.setItemDeleteEvent(self.__deleteFilter)

        # context menu
        self.addContextMenuSeparator()
        self.addContextMenuEvent("Create New Category", self.createNewCategory)
        self.addContextMenuEvent("Create New Filter", self.createNewFilter)

        # setup delegate
        delegate = CreateOrganizerDelegate(self)
        self.view().setItemDelegate(delegate)

    def enterEvent(self, event):
        self.setIsCategoryItemDeletable(True)
        self.setIsCategoryItemDraggable(False)

        self.setIsDroppable(True)
        self.setIsDeletable(True)

        return AbstractIRFAvailableOrganizerWidget.enterEvent(self, event)

    def __itemParentChanged(self, data, items, model, row, parent):
        """ On drop update the item drops category to the new parents"""
        for item in items:
            if parent == self.rootItem():
                item.getArg("node").getParameter("category").setValue("", 0)
            else:
                item.getArg("node").getParameter("category").setValue(parent.name(), 0)

    def __nameChanged(self, item, old_value, new_value, column=0):
        """ When the user changes a name:
                if it is a FILTER, update the filters name
                if it is a CATEGORY, update all categories to that new name"""
        if item.getArg("type") == irfutils.FILTER:
            item.getArg("node").getParameter("name").setValue(new_value, 0)
        if item.getArg("type") == irfutils.CATEGORY:
            for render_filter_node in irfutils.getAllRenderFilterNodes():
                if render_filter_node.getParameter("category").getValue(0) == old_value:
                    render_filter_node.getParameter("category").setValue(new_value, 0)

    def createNewFilter(self, *args):
        """ Creates a new render filter"""
        default_irf_node = irfutils.defaultIRFNode()
        new_filter_node = default_irf_node.buildChildNode()
        self.createFilterItem(new_filter_node)

    def __deleteFilter(self, item):
        if item.getArg("type") == irfutils.FILTER:
            node = item.getArg("node")
            nodeutils.disconnectNode(node, input=True, output=True, reconnect=True)
            node.delete()

        if item.getArg("type") == irfutils.CATEGORY:
            # get all children
            for child in item.children():
                self.__deleteFilter(child)

    def createNewCategory(self, *args):
        self.createCategoryItem("<New Category>")

    def __irfSelectionChanged(self, item, enabled):
        if enabled:
            if item.getArg("type") == irfutils.FILTER:
                irf_create_wiget = getWidgetAncestorByObjectName(self, "Create Widget")
                irf_create_wiget.nodegraphWidget().setNode(item.getArg("node"))


class ViewActiveFiltersOrganizerWidget(AbstractIRFActiveFiltersOrganizerWidget):
    """ Available filters organizer to be used in the VIEW widget"""
    def __init__(self, parent=None):
        super(ViewActiveFiltersOrganizerWidget, self).__init__(parent)
        # setup custom model
        """ This is needed to ensure all tabs remain synchronized"""
        if not hasattr(widgetutils.katanaMainWindow(), "_irf_active_filters_model"):
            widgetutils.katanaMainWindow()._irf_active_filters_model = self.model()
            self.populate()
        else:
            self.setModel(widgetutils.katanaMainWindow()._irf_active_filters_model)

    def enterEvent(self, event):
        self.setAcceptDrops(False)
        self.setIsCategoryItemDeletable(False)
        self.setIsDeletable(False)
        self.setIsDraggable(False)
        self.setIsDroppable(False)
        self.setIsRootDroppable(False)

        return AbstractIRFActiveFiltersOrganizerWidget.enterEvent(self, event)


class ActivateAvailableFiltersOrganizerWidget(AbstractIRFAvailableOrganizerWidget):
    """ Available filters for the ACTIVATE widget"""
    def __init__(self, parent=None):
        super(ActivateAvailableFiltersOrganizerWidget, self).__init__(parent)
        # setup custom model
        """ This is needed to ensure all tabs remain synchronized"""
        if not hasattr(widgetutils.katanaMainWindow(), "_irf_create_available_filters_model"):
            widgetutils.katanaMainWindow()._irf_create_available_filters_model = self.model()
            self.populate()

        else:
            self.setModel(widgetutils.katanaMainWindow()._irf_create_available_filters_model)

        self.setMultiSelect(True)

    def enterEvent(self, event):
        self.setIsDeletable(False)
        self.setIsDroppable(False)

        self.setIsCategoryItemDraggable(True)
        self.setIsCategoryItemDeletable(False)
        return AbstractIRFAvailableOrganizerWidget.enterEvent(self, event)


class ActivateActiveFiltersOrganizerWidget(AbstractIRFActiveFiltersOrganizerWidget):
    """ Available filters to be displayed in the ACTIVATE Widget"""
    def __init__(self, parent=None):
        super(ActivateActiveFiltersOrganizerWidget, self).__init__(parent)
        # setup custom model
        """ This is needed to ensure all tabs remain synchronized"""
        if not hasattr(widgetutils.katanaMainWindow(), "_irf_active_filters_model"):
            widgetutils.katanaMainWindow()._irf_active_filters_model = self.model()
            self.populate()
        else:
            self.setModel(widgetutils.katanaMainWindow()._irf_active_filters_model)

        self.setItemDeleteEvent(self.disableFilter)

    def enterEvent(self, event):
        self.setAcceptDrops(True)
        self.setIsCategoryItemDeletable(True)
        self.setIsDeletable(True)
        self.setIsDraggable(False)
        self.setIsDroppable(True)
        self.setIsRootDroppable(True)
        return AbstractIRFActiveFiltersOrganizerWidget.enterEvent(self, event)

    def disableFilter(self, item):
        """ On delete, disable filters"""
        if item.getArg("type") == irfutils.CATEGORY:
            for child in item.children():
                self.disableFilter(child)
            del self.categories()[item.getArg("name")]
        if item.getArg("type") == irfutils.FILTER:
            irfutils.enableRenderFilter(item.getArg("node"), False)

    def dropEvent(self, event):
        """ On drop, activate filters"""
        nodes = event.mimeData().data(irfutils.IS_IRF).data().decode("utf-8").split(",")
        for node_name in nodes:
            node = NodegraphAPI.GetNode(node_name)
            if node not in irfutils.getAllActiveFilters():
                self.createFilterItem(node)
                irfutils.enableRenderFilter(node, True)

        return AbstractIRFOrganizerWidget.dropEvent(self, event)

    def dragEnterEvent(self, event):
        if irfutils.IS_IRF in event.mimeData().formats():
            event.accept()
        return AbstractIRFOrganizerWidget.dragEnterEvent(self, event)

