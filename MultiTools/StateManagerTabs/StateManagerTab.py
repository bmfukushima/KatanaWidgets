"""

Data Structure:
    same as color registry? just go for an export?
    "data" :
        [
            {
                "children": [dict(child_a), dict(child_b)],
                "color":"(255,255,255,255)",
                "enabled":bool,
                "item_type":COLOR|GROUP,
                "name": item.getName()
            },
            dict(child_c),
            dict(child_d)
        ]
    }

    gsv_map (dict): {gsv_name: option}
    irf (list): of render filter node names
    bookmark (str): of last active bookmark

Hierarchy:
    StateManagerTab --> (UI4.Tabs.BaseTab)
        |- QVBoxLayout
            |- view_widget --> (StateManagerViewWidget --> ShojiLayout)
            |    |- gsv_view --> (GSVViewWidget)
            |    |- irf_view --> (IRFViewWidget)
            |    |- bookmarks_view --> (BookmarkViewWidget)
            |    |- state_view --> (StateManagerEditorWidget)
            |- editor_widget --> (StateManagerEditorWidget --> AbstractStateManagerTab)
                |- organizer_widget --> (StateManagerOrganizerWidget)
"""

import json

from qtpy.QtWidgets import QVBoxLayout, QWidget
from qtpy.QtCore import QModelIndex

from Katana import UI4, NodegraphAPI

from cgwidgets.widgets import ShojiLayout, ShojiModelViewWidget, ModelViewWidget, ButtonInputWidget

from Utils2 import gsvutils
from Widgets2 import AbstractStateManagerTab, AbstractStateManagerOrganizerWidget
from .GSVManagerTab import GSVViewWidget
from .IRFManagerTab import IRFActivationWidget as IRFViewWidget
from .IRFManagerTab.IRFUtils import IRFUtils
from .BookmarkManagerTab import Tab as BookmarkViewWidget
from .BookmarkManagerTab.BookmarkManagerTab import BookmarkManagerTab

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
    NAME = "State Manager"
    def __init__(self, parent=None):
        super(StateManagerTab, self).__init__(parent)

        # setup widgets
        self._view_widget = StateManagerViewWidget(self)
        self._editor_widget = StateManagerEditorWidget(self)

        # setup main layout
        QVBoxLayout(self)
        self._main_widget = ShojiModelViewWidget(self)
        self._main_widget.insertShojiWidget(0, column_data={"name":"View"}, widget=self._view_widget)
        self._main_widget.insertShojiWidget(1, column_data={"name":"Edit"}, widget=self._editor_widget)

        self.layout().addWidget(self._main_widget)

    def pushData(self):
        pass

    def pullData(self):
        pass

    """ WIDGETS """
    def mainWidget(self):
        return self._main_widget

    def viewWidget(self):
        return self._view_widget

    def editorWidget(self):
        return self._editor_widget


class StateManagerOrganizerWidget(AbstractStateManagerOrganizerWidget):
    def __init__(self, parent=None):
        super(StateManagerOrganizerWidget, self).__init__(parent)

        # todo setup events
        # setup events
        self.setItemDeleteEvent(self.__stateDeleteEvent)
        self.setTextChangedEvent(self.__stateRenameEvent)
        self.setDropEvent(self.__stateReparentEvent)
        self.setItemExportDataFunction(self.exportStateManager)

        # populate
        self.populate(StateManagerUtils.getMainStateList())

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


    """ UPDATE """
    def updateParamData(self):
        data = self.exportModelToDict(self.rootItem())
        StateManagerUtils.updateData(data)

    """ EVENTS """
    def exportStateManager(self, item):
        """ Individual items dictionary when exported.

        Note:
            node has to come first.  This is due to how the item.name() function is called.
            As if no "name" arg is found, it will return the first key in the dict"""

        # store data in dictionary for the actual export data

        # return the export data for the rebuild file
        if item.getArg("type") == AbstractStateManagerTab.STATE_ITEM:
            data = {
                "name": item.getArg("name"),
                "type": item.getArg("type"),
                "irf": item.getArg("irf"),
                "gsv": item.getArg("gsv"),
                "bookmark": item.getArg("bookmark")
            }
        elif item.getArg("type") == AbstractStateManagerTab.FOLDER_ITEM:
            data = {
                "name": item.getArg("name"),
                "children": [],
                "type": item.getArg("type")
            }

        return data

    def __stateRenameEvent(self, item, old_name, new_name):
        """ When a user renames a state, this will update the states/folder associated with the rename"""
        # preflight
        if old_name == new_name: return

        item.setArg("name", new_name)

        self.updateParamData()

    def __stateDeleteEvent(self, item):
        """ When the user deletes an item, this will delete the state/folder associated with the item"""
        self.updateParamData()

    def __stateReparentEvent(self, data, items, model, row, parent):
        """ On drop, reparent the state"""
        self.updateParamData()

    def showEvent(self, event):
        self.clearModel()
        self.populate(StateManagerUtils.getMainStateList())
        return AbstractStateManagerOrganizerWidget.showEvent(self, event)

    def createNewState(self, name=None, create_item=True):
        """ Creates a new State item

        Args:
            name (str):
            create_item (bool): Determines if the item should be created or not"""
        if not name:
            name = self.getUniqueName("New State", self.rootItem(), item_type=AbstractStateManagerTab.STATE_ITEM, exists=False)

        # create item
        if create_item:
            gsv_map = gsvutils.getGSVMap()
            irf_map = [node.getName() for node in IRFUtils.getAllActiveFilters()]
            #active_bookmark = BookmarkManagerTab.lastActiveBookmark()
            active_bookmark = "something"
            # todo last active bookmark
            # this needs to be set as a global attr somewhere, like katana main, or a parameter on KatanaBebop
            state_data = {"irf": irf_map, "gsv":gsv_map, "bookmark":active_bookmark, "name":name}
            state_item = self.createNewStateItem(name, data=state_data)

            # update param data
            self.updateParamData()
            return state_item

    def createNewFolder(self):
        new_folder_name = self.getUniqueName("New Folder", self.rootItem(), item_type=AbstractStateManagerTab.FOLDER_ITEM, exists=False)
        folder_item = self.createNewFolderItem(new_folder_name)
        self.addFolder(new_folder_name, folder_item)
        return folder_item


class StateManagerEditorWidget(AbstractStateManagerTab):
    def __init__(self, parent=None):
        super(StateManagerEditorWidget, self).__init__(parent)

        # setup organizer
        self._state_organizer_widget = StateManagerOrganizerWidget(self)
        self.setOrganizerWidget(self._state_organizer_widget)

        # setup events
        self._create_new_state_widget = ButtonInputWidget(
            title="New State", user_clicked_event=self.createNewState)

        self.addUtilsButton(self._create_new_state_widget)

        # setup events
        self.setLoadEvent(self.loadEvent)
        self.setUpdateEvent(self.updateEvent)
        self.setCreateNewFolderEvent(self.createNewFolder)

    def loadEvent(self):
        # todo load event
        print('load')

    def updateEvent(self):
        # todo save event
        print('update')

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
            is_dropable=False,
            is_dragable=True,
            parent=parent_index
        )
        bookmark_item = bookmark_index.internalPointer()
        return bookmark_item


class StateManagerViewWidget(ShojiLayout):
    def __init__(self, parent=None):
        super(StateManagerViewWidget, self).__init__(parent)
        #self._main_layout = ShojiLayout(self)
        self._gsv_view = GSVViewWidget(self)
        self._irf_view = IRFViewWidget(self)
        self._bookmarks_view = BookmarkViewWidget(self)
        self._state_view = StateManagerEditorWidget(self)

        self.addWidget(self._state_view)
        self.addWidget(self._gsv_view)
        self.addWidget(self._irf_view)
        self.addWidget(self._bookmarks_view)
        self.setSizes([100, 100, 100, 100])

        # # setup main layout
        # QVBoxLayout(self)
        # self.layout().addWidget(self._main_layout)

