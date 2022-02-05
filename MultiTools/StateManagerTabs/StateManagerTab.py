"""
Todo:
    *   Clear last active data on scene load
    *   Import / Export
    *   View Tab, change to activation
    *   New Button
            Kinda like a combo box, but for less than 3-4 values
Data Structure:
    "data" :
        [
            # state item
            {
                "notes": item.getArg("notes")
                "view_node": item.getArg("view_node"),
                "edit_node": item.getArg("edit_nodes"),
                "name": item.getArg("name"),
                "type": item.getArg("type"),
                "irf": item.getArg("irf"),
                "gsv": item.getArg("gsv"),
                "bookmark": item.getArg("bookmark")},
            # folder item
            {
                "name": item.getArg("name"),
                "type": item.getArg("type"),
                "children": [dict(grandchild_a), dict(grandchild_b)]},
            dict(child_c),
            dict(child_d)
        ]
    }

    name (str):
    type (str): AbstractStateManagerTab.ITEMTYPE
    children (list) of folder/state items
    gsv (dict): {gsv_name: option}
    irf (list): of render filter node names
    bookmark (str): of last active bookmark
    view_node (str): name of node viewed
    edit_node (list): of edited node names
    notes (str): notes created by the user

Hierarchy:
    StateManagerTab --> (UI4.Tabs.BaseTab)
        |- QVBoxLayout
            |- view_widget --> (StateManagerActiveView --> ShojiLayout)
            |    |- gsv_view --> (GSVViewWidget)
            |    |- irf_view --> (IRFActivationWidget)
            |    |- bookmarks_view --> (BookmarkViewWidget)
            |    |- state_view --> (StateManagerEditorWidget)
            |- create_widget --> (StateManagerEditorWidget --> AbstractStateManagerTab)
                |- organizer_widget --> (StateManagerOrganizerWidget)
                |- state_viewer_widget --> (StateManagerItemViewWidget)
                    |- QVBoxLayout
                        |- notes_widget --> (QPlainTextEdit)
                        |- gsv_view_widget --> (ReadOnlyGSVViewWidget)
                        |- irf_view_widget --> (ReadOnlyIRFViewWidget)
                        |- bookmark_labelled_widget --> (LabelledInputWidget)
                            |- bookmark_widget --> (StringInputWidget)
"""

import json

from qtpy.QtWidgets import QVBoxLayout, QScrollArea, QWidget, QPlainTextEdit
from qtpy.QtCore import QModelIndex

from Katana import UI4, NodegraphAPI, Utils

from cgwidgets.widgets import ShojiLayout, ShojiModelViewWidget, ButtonInputWidget, StringInputWidget, LabelledInputWidget
from cgwidgets.utils import getWidgetAncestor
from cgwidgets.views import AbstractDragDropModel

from Utils2 import gsvutils, widgetutils, irfutils
from Widgets2 import AbstractStateManagerTab, AbstractStateManagerOrganizerWidget
from .GSVManagerTab import GSVViewWidget, ViewGSVWidget
from .IRFManagerTab import IRFActivationWidget, IRFViewWidget

from .BookmarkManagerTab import Tab as BookmarkViewWidget
from .BookmarkManagerTab.BookmarkUtils import BookmarkUtils


PARAM_LOCATION = "KatanaBebop.StateManagerData"


class StateManagerUtils(object):

    @staticmethod
    def addState(state):
        data = StateManagerUtils.getData()
        data["data"].append(state)
        StateManagerUtils.getParam().setValue(json.dumps(data), 0)

    @staticmethod
    def getStateData(state_location):
        """ Gets the state data dictionary

        Args:
            state_location (str): full path to state
                ie. folder1/folder2/folder3/state"""
        pass

    @staticmethod
    def getData():
        """ Returns the dictionary located at KatanaBebop.StateManagerData"""
        return json.loads(StateManagerUtils.getParam().getValue(0))

    @staticmethod
    def getMainStateList():
        """ Returns the main list containing all of the state items"""
        return StateManagerUtils.getData()["data"]

    @staticmethod
    def getParam():
        """ Returns the param that stores all of the State Manager data located at KatanaBebop.StateManagerData"""
        return NodegraphAPI.GetRootNode().getParameter(PARAM_LOCATION)

    @staticmethod
    def updateData(data):
        StateManagerUtils.getParam().setValue(json.dumps(data), 0)


class StateManagerTab(UI4.Tabs.BaseTab):
    NAME = "State Managers/State Manager"
    def __init__(self, parent=None):
        super(StateManagerTab, self).__init__(parent)

        # setup widgets
        self._view_widget = StateManagerActiveView(self)
        self._editor_widget = StateManagerEditorMainWidget(self)

        # setup main layout
        QVBoxLayout(self)
        self._main_widget = ShojiModelViewWidget(self)
        self._main_widget.setHeaderItemIsDeletable(False)
        self._main_widget.insertShojiWidget(0, column_data={"name":"Manage"}, widget=self._view_widget)
        self._main_widget.insertShojiWidget(1, column_data={"name":"Create/Edit"}, widget=self._editor_widget)

        self.layout().addWidget(self._main_widget)

        Utils.EventModule.RegisterCollapsedHandler(self.update, 'nodegraph_loadEnd', None)

    def __name__(self):
        return StateManagerTab.NAME

    def update(self, *args):
        self.viewWidget().stateViewWidget().organizerWidget().update()
        self.viewWidget().gsvViewWidget().update()
        self.viewWidget().irfViewWidget().update()
        self.viewWidget().bookmarksViewWidget().update()

    def setLastActive(self, last_active):
        self.viewWidget().stateViewWidget().setLastActive(last_active)
        self.createWidget().setLastActive(last_active)

    """ WIDGETS """
    def mainWidget(self):
        return self._main_widget

    def viewWidget(self):
        return self._view_widget

    def createWidget(self):
        return self._editor_widget


class StateManagerOrganizerWidget(AbstractStateManagerOrganizerWidget):
    """ Organizer for the CREATE portion"""
    def __init__(self, parent=None):
        super(StateManagerOrganizerWidget, self).__init__(parent)

        # setup custom model
        """ This is needed to ensure all tabs remain synchronized"""
        if not hasattr(widgetutils.katanaMainWindow(), "_state_manager_model"):
            widgetutils.katanaMainWindow()._state_manager_model = self.model()
            self.populate(StateManagerUtils.getMainStateList())
        else:
            self.setModel(widgetutils.katanaMainWindow()._state_manager_model)

        # setup events
        self.setItemDeleteEvent(self.__stateDeleteEvent)
        self.setTextChangedEvent(self.__stateRenameEvent)
        self.setDropEvent(self.__stateReparentEvent)
        self.setItemExportDataFunction(self.exportStateManager)
        self.setIndexSelectedEvent(self.__stateSelectedEvent)

    def populate(self, children, parent=QModelIndex()):

        """ Populates the view

        Args:
            children (list): of item data"""
        for child in reversed(children):
            if child["type"] == AbstractStateManagerTab.STATE_ITEM:
                # column_data = child
                self.createNewStateItem(child["name"], data=child, parent=parent)

            elif child["type"] == AbstractStateManagerTab.FOLDER_ITEM:
                new_item = self.createNewFolderItem(child["name"], parent=parent)
                new_index = self.getIndexFromItem(new_item)
                self.populate(child["children"], new_index)

    def update(self):
        self.clearModel()
        self.populate(StateManagerUtils.getMainStateList())

    """ UPDATE """
    def updateParamData(self):
        data = self.exportModelToDict(self.rootItem())
        StateManagerUtils.updateData(data)

    def getItemFullName(self, item):
        """ Returns the full path of the item provided

        Args:
            item (ModelViewItem)"""
        parents = []
        parent_item = item
        while parent_item.parent() != self.rootItem():
            parents.append(parent_item.parent().name())
            parent_item = parent_item.parent()

        parents = list(reversed(parents))
        parents.append(item.name())

        return "/".join(parents)

    """ EVENTS """
    def exportStateManager(self, item):
        """ Individual items dictionary when exported."""

        # check to see if item is in delete queue
        if item.hasArg("is_deleting"): return

        # return the export data for the rebuild file
        if item.getArg("type") == AbstractStateManagerTab.STATE_ITEM:
            data = {
                "notes": item.getArg("notes"),
                "view_node": item.getArg("view_node"),
                "edit_node": item.getArg("edit_node"),
                "name": item.getArg("name"),
                "type": item.getArg("type"),
                "irf": item.getArg("irf"),
                "gsv": item.getArg("gsv"),
                "bookmark": item.getArg("bookmark")
            }
        elif item.getArg("type") == AbstractStateManagerTab.FOLDER_ITEM:
            data = {
                "name": item.getArg("name"),
                "type": item.getArg("type"),
                "children": []
            }

        return data

    def updateState(self):
        """ Updates the state of the currently selected item"""
        # get item
        items = self.getAllSelectedItems()
        if len(items) == 0: return
        if items[0].getArg("type") == AbstractStateManagerTab.FOLDER_ITEM: return

        item = items[0]
        name = item.name()
        row = item.row()
        parent_item = item.parent()
        parent_index = self.getIndexFromItem(parent_item)

        # update item / data
        self.createNewState(name, parent=parent_index, row=row)
        self.deleteItem(item, event_update=False)
        self.updateParamData()

    def loadState(self):
        """ Loads the state of the currently selected item """
        items = self.getAllSelectedItems()
        if len(items) == 0: return False
        if items[0].getArg("type") == AbstractStateManagerTab.FOLDER_ITEM: return

        item = items[0]

        # update view / edit
        if item.getArg("view_node"):
            view_node = NodegraphAPI.GetNode(item.getArg("view_node"))
            NodegraphAPI.SetNodeViewed(view_node, True, exclusive=True)

        if 0 < len(item.getArg("edit_node")):
            for edit_node in NodegraphAPI.GetAllEditedNodes():
                NodegraphAPI.SetNodeEdited(edit_node, False)

            for edit_node_name in item.getArg("edit_node"):
                edit_node = NodegraphAPI.GetNode(edit_node_name)
                NodegraphAPI.SetNodeEdited(edit_node, True, exclusive=False)

        # set up gsv
        gsv_dict = item.getArg("gsv")

        for gsv, option in gsv_dict.items():
            gsvutils.setGSVOption(gsv, option)

        # irf
        irf_list = item.getArg("irf")
        irfutils.clearAllActiveFilters()
        for irf_name in irf_list:
            irf_node = NodegraphAPI.GetNode(irf_name)
            if irf_node:
                irfutils.enableRenderFilter(irf_node, True)

        # bookmark
        bookmark_name = item.getArg("bookmark")

        if bookmark_name:
            from PyUtilModule import ScenegraphBookmarkManager as SBM
            """ Doing a special load here to ensure we're using the same module that the default
            handler uses.  This needs to be done, as there is a monkey patch, to store the active
            bookmark on katanaMainWindow()._last_active_bookmark"""

            bookmark = BookmarkUtils.bookmark(bookmark_name)
            if bookmark:
                SBM.LoadBookmark(bookmark)

        # set last active
        last_active_state = self.getItemFullName(item)
        for tab in UI4.App.Tabs.GetTabsByType("State Manager"):
            tab.setLastActive(last_active_state)

        # todo update popup bar widgets
        for tab in UI4.App.Tabs.GetTabsByType('Popup Bar Displays/KatanaBebop/State Manager'):
            # get a list of all of the widgets
            popup_widgets = tab.popupBarDisplayWidget().allWidgets()

            for widget in popup_widgets:
                popup_widget = widget.popupWidget()
                if hasattr(popup_widget, "__name__"):
                    if popup_widget.__name__() == "State Manager":
                        popup_widget.setLastActive(last_active_state)

        return True

    def __stateSelectedEvent(self, item, enabled):
        if enabled:
            if item.getArg("type") == AbstractStateManagerTab.STATE_ITEM:
                editor_widget = getWidgetAncestor(self, StateManagerEditorMainWidget)
                if editor_widget:
                    editor_widget.showItemDetails(item)

    def __stateRenameEvent(self, item, old_name, new_name, column=None):
        """ When a user renames a state, this will update the states/folder associated with the rename"""
        # preflight
        if old_name == new_name: return

        item.setArg("name", new_name)

        self.updateParamData()

    def __stateDeleteEvent(self, item):
        """ When the user deletes an item, this will delete the state/folder associated with the item"""
        item.setArg("is_deleting", True)
        self.updateParamData()

    def __stateReparentEvent(self, data, items, model, row, parent):
        """ On drop, reparent the state"""
        self.updateParamData()

    # def showEvent(self, event):
    #     self.clearModel()
    #     self.populate(StateManagerUtils.getMainStateList())
    #     return AbstractStateManagerOrganizerWidget.showEvent(self, event)

    """ CREATE """
    def createNewState(self, name=None, create_item=True, parent=QModelIndex(), row=0):
        """ Creates a new State item

        Args:
            name (str):
            create_item (bool): Determines if the item should be created or not
            parent (QModelIndex): parent index to be created under
            row (int): row to insert item, default is 0"""
        if not name:
            name = self.getUniqueName("New State", self.rootItem(), item_type=AbstractStateManagerTab.STATE_ITEM, exists=False)

        # create item
        if create_item:
            gsv_map = gsvutils.getGSVMap()
            irf_map = [node.getName() for node in irfutils.getAllActiveFilters()]
            if hasattr(widgetutils.katanaMainWindow(), "_last_active_bookmark"):
                active_bookmark = widgetutils.katanaMainWindow()._last_active_bookmark
            else:
                active_bookmark = None

            # get notes
            editor_widget = getWidgetAncestor(self, StateManagerEditorMainWidget)
            notes = editor_widget.notesWidget().toPlainText()

            # this needs to be set as a global attr somewhere, like katana main, or a parameter on KatanaBebop
            state_data = {
                "irf": irf_map,
                "gsv": gsv_map,
                "bookmark": active_bookmark,
                "name": name,
                "view_node": NodegraphAPI.GetViewNode().getName() if NodegraphAPI.GetViewNode() else None,
                "edit_node": [node.getName() for node in NodegraphAPI.GetAllEditedNodes()],
                "notes": notes
            }
            state_item = self.createNewStateItem(name, data=state_data, parent=parent, row=row)

            # update param data
            self.updateParamData()
            return state_item

    def createNewFolder(self):
        new_folder_name = self.getUniqueName("New Folder", self.rootItem(), item_type=AbstractStateManagerTab.FOLDER_ITEM, exists=False)
        folder_item = self.createNewFolderItem(new_folder_name, is_draggable=True)
        # self.addFolder(new_folder_name, folder_item)
        return folder_item


class StateManagerEditorMainWidget(ShojiLayout):
    def __init__(self, parent=None):
        super(StateManagerEditorMainWidget, self).__init__(parent)
        self._editor_widget = StateManagerEditorWidget(self)
        self._viewer_widget = StateManagerItemViewWidget(self)
        self.addWidget(self._editor_widget)
        self.addWidget(self._viewer_widget)

    def setLastActive(self, last_active):
        self.editorWidget().setLastActive(last_active)

    def showItemDetails(self, item):
        """ When an item in the organizer is selected, this will update the view to display that items settings"""
        self.viewerWidget().setNotes(item.getArg("notes"))
        self.viewerWidget().setGSVData(item.getArg("gsv"))
        self.viewerWidget().setBookmarkData(item.getArg("bookmark"))
        self.viewerWidget().setIRFData(item.getArg("irf"))

    """ WIDGETS """
    def notesWidget(self):
        return self._viewer_widget.notesWidget()

    def lastActiveWidget(self):
        return self._editor_widget.lastActiveWidget()

    def editorWidget(self):
        return self._editor_widget

    def viewerWidget(self):
        return self._viewer_widget


class StateManagerEditorWidget(AbstractStateManagerTab):
    """ Main widget for the editor view"""
    def __init__(self, parent=None):
        super(StateManagerEditorWidget, self).__init__(parent)
        # setup organizer
        self._state_organizer_widget = StateManagerOrganizerWidget(self)
        self.setOrganizerWidget(self._state_organizer_widget)

        # setup events
        self._create_new_state_widget = ButtonInputWidget(
            title="New State", user_clicked_event=self.createNewState)

        self.addUtilsButton(self._create_new_state_widget)

        # # setup view
        # self._state_viewer_widget = StateManagerItemViewWidget(self)
        # self.layout().addWidget(self._state_viewer_widget)

        # setup events
        self.setLoadEvent(self.loadStateEvent)
        self.setUpdateEvent(self.updateStateEvent)
        self.setCreateNewFolderEvent(self.createNewFolder)

    def loadStateEvent(self):
        load_state = self.organizerWidget().loadState()

        if load_state:
            Utils.EventModule.ProcessAllEvents()
            # Update all tabs
            for tab_type in ["State Managers/GSV Manager", "State Managers/IRF Manager", "State Managers/State Manager", "State Managers/Bookmark Manager"]:
                tabs = UI4.App.Tabs.GetTabsByType(tab_type)
                for tab in tabs:
                    tab.update()

    def updateStateEvent(self):
        self.organizerWidget().updateState()

    def createNewState(self, widget):
        self.organizerWidget().createNewState()

    def createNewFolder(self):
        self.organizerWidget().createNewFolder()

    def createBookmarkItem(self, bookmark, folder_name=None):
        """ Creates a new bookmark item.

        If a folder name is specified and it does not exist, the item will be created

        Args:
            bookmark (str): name of bookmark
            folder_name (str): name of folder"""
        # get folder
        folder_item = self.rootItem()
        if folder_name:
            if folder_name not in self.bookmarkFolders().keys():
                folder_item = self.createNewFolderItem(folder_name)
                self.addBookmarkFolder(folder_name, folder_item)
            else:
                folder_item = self.bookmarkFolders()[folder_name]
        parent_index = self.getIndexFromItem(folder_item)

        # setup data
        data = {"name": bookmark, "folder": folder_name, "type": AbstractStateManagerTab.STATE_ITEM}

        # create item
        bookmark_index = self.insertNewIndex(
            0,
            name=bookmark,
            column_data=data,
            is_deletable=True,
            is_droppable=False,
            is_draggable=True,
            parent=parent_index
        )
        bookmark_item = bookmark_index.internalPointer()
        return bookmark_item

    """ WIDGETS """
    def createNewStateButton(self):
        return self._create_new_state_widget


class ReadOnlyGSVViewWidget(GSVViewWidget):
    """ Read only GSVView for the StateManagerItemViewWidget

    Attributes:
        gsv_data (dict): {gsv_name: option}"""

    def __init__(self, parent=None):
        self._gsv_data = {}
        super(ReadOnlyGSVViewWidget, self).__init__(parent)

    """ POPULATE """
    def clear(self):
        """
        Removes all of the GSVViewWidgets from the display
        """
        # clear layout (if it exists)
        if self.layout().count() > 0:
            for index in reversed(range(self.layout().count())):
                self.layout().itemAt(index).widget().setParent(None)

        self._widget_list = {}

    def populate(self):
        """Creates the display for every GSV.  This is the left side of the display."""
        # create a combobox for each GSV that is available
        for gsv, option in self.gsvData().items():
            self.addWidget(gsv, option)

    def addWidget(self, gsv, option):
        """
        Adds a widget to the layout.

        Args:
            gsv (str): name of GSV to create
        """
        widget = ViewGSVWidget(self, name=gsv)
        widget.delegateWidget().setText(option)
        self.addInputWidget(widget)
        self.widgets()[gsv] = widget

    def gsvData(self):
        return self._gsv_data

    def setGSVData(self, gsv_data):
        self._gsv_data = gsv_data


class ReadOnlyIRFViewWidget(IRFViewWidget):
    """ Read only IRFView for the StateManagerItemViewWidget

    Attributes:
        activeFilters (list): of the names of active render filter nodes"""

    def __init__(self, parent=None):
        self._active_filters = []
        super(ReadOnlyIRFViewWidget, self).__init__(parent)
        # todo model2
        model = AbstractDragDropModel(self)
        self.setModel(model)

    def populate(self):
        for render_filter_name in self.activeFilters():
            render_filter_node = NodegraphAPI.GetNode(render_filter_name)
            index = self.createFilterItem(render_filter_node)
            self.view().setExpanded(index.parent(), True)

    def activeFilters(self):
        return self._active_filters

    def setActiveFilters(self, active_filters):
        self._active_filters = active_filters


class StateManagerItemViewWidget(QWidget):
    """ Displays the options as read only to the user when an item is selected"""
    def __init__(self, parent):
        super(StateManagerItemViewWidget, self).__init__(parent)
        QVBoxLayout(self)
        self._notes_widget = QPlainTextEdit(self)

        self._gsv_view_widget = ReadOnlyGSVViewWidget(self)
        self._gsv_scroll_area = QScrollArea(self)
        self._gsv_scroll_area.setWidget(self._gsv_view_widget)
        self._gsv_scroll_area.setWidgetResizable(True)

        self._irf_view_widget = ReadOnlyIRFViewWidget(self)

        # create input buttons
        self._bookmark_widget = StringInputWidget(self)
        self._bookmark_widget.setReadOnly(True)
        self._bookmark_labelled_widget = LabelledInputWidget(
            self, name="Bookmark", delegate_widget=self._bookmark_widget, default_label_length=150)
        self._bookmark_labelled_widget.setViewAsReadOnly(True)

        self.layout().addWidget(self._notes_widget)
        self.layout().addWidget(self._gsv_scroll_area)
        self.layout().addWidget(self._irf_view_widget)
        self.layout().addWidget(self._bookmark_labelled_widget)

    def setNotes(self, notes):
        self.notesWidget().setPlainText(notes)

    def setIRFData(self, irf_data):
        self.irfViewWidget().setActiveFilters(irf_data)
        self.irfViewWidget().update()

    def setBookmarkData(self, bookmark_data):
        self.bookmarkWidget().setText(bookmark_data)

    def setGSVData(self, gsv_data):
        self.gsvViewWidget().setGSVData(gsv_data)
        self.gsvViewWidget().update()

    """ WIDGETS """
    def bookmarkWidget(self):
        return self._bookmark_widget

    def gsvViewWidget(self):
        return self._gsv_view_widget

    def irfViewWidget(self):
        return self._irf_view_widget

    def notesWidget(self):
        return self._notes_widget


class StateManagerActiveView(ShojiLayout):
    """ Widget to show all of the different activation managers managers"""
    def __init__(self, parent=None):
        super(StateManagerActiveView, self).__init__(parent)
        #self._main_layout = ShojiLayout(self)
        self._gsv_view_widget = GSVViewWidget(self)
        self._gsv_scroll_area = QScrollArea(self)
        self._gsv_scroll_area.setWidget(self._gsv_view_widget)
        self._gsv_scroll_area.setWidgetResizable(True)

        self._irf_view_widget = IRFActivationWidget(self)
        #todo model 1
        # model = AbstractDragDropModel(self)
        # self._irf_view_widget.activatedFiltersWidget().setModel(model)

        self._bookmarks_view_widget = BookmarkViewWidget(self)
        self._state_view_widget = StateManagerEditorWidget(self)

        self.addWidget(self._state_view_widget)
        self.addWidget(self._gsv_scroll_area)
        self.addWidget(self._irf_view_widget)
        self.addWidget(self._bookmarks_view_widget)

        # setup style
        self._state_view_widget.createNewStateButton().hide()
        self._state_view_widget.createNewFolderButton().hide()
        self._state_view_widget.updateButton().hide()
        self.setSizes([100, 100, 100, 100])

        # # setup main layout
        # QVBoxLayout(self)
        # self.layout().addWidget(self._main_layout)

    """ WIDGETS """
    def bookmarksViewWidget(self):
        return self._bookmarks_view_widget

    def gsvViewWidget(self):
        return self._gsv_view_widget

    def lastActiveWidget(self):
        return self.stateViewWidget().lastActiveWidget()

    def irfViewWidget(self):
        return self._irf_view_widget

    def stateViewWidget(self):
        return self._state_view_widget