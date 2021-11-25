"""
TODO
    *   Extract BookmarkManagerTab to abstraction layer
            - organizer
            - new state/folder
                New State Item
                New Folder Item
"""

from qtpy.QtWidgets import QVBoxLayout, QWidget

from Katana import UI4

from cgwidgets.widgets import ShojiLayout, ShojiModelViewWidget, ModelViewWidget, ButtonInputWidget

from Widgets2 import AbstractStateManagerTab

from .GSVManagerTab import GSVViewWidget
from .IRFManagerTab import IRFActivationWidget as IRFViewWidget
from .BookmarkManagerTab import Tab as BookmarkViewWidget


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

    """ WIDGETS """
    def mainWidget(self):
        return self._main_widget

    def viewWidget(self):
        return self._view_widget

    def editorWidget(self):
        return self._editor_widget


class StateManagerOrganizerWidget(ModelViewWidget):
    def __init__(self, parent=None):
        super(StateManagerOrganizerWidget, self).__init__(parent)


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
        print('load')

    def updateEvent(self):
        print('update')

    def createNewState(self, widget):
        print('create new state')
        pass

    def createNewFolder(self, widget):
        print('create new folder')
        pass

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

    def createNewFolderItem(self, folder):
        data = {"name": folder, "folder": folder, "type": AbstractStateManagerTab.FOLDER_ITEM}
        bookmark_index = self.insertNewIndex(
            0,
            name=folder,
            column_data=data,
            is_deletable=True,
            is_dropable=True,
            is_dragable=False
        )
        bookmark_item = bookmark_index.internalPointer()
        return bookmark_item

    def createNewBookmark(self, name=None, folder=None, create_item=True):
        """ Creates a new Scenegraph Bookmark

        Args:
            name (str):
            folder (str):
            create_item (bool): Determines if the item should be created or not"""
        if not name:
            name = self.__getNewUniqueName("New Bookmark", self.rootItem(), item_type=AbstractStateManagerTab.STATE_ITEM, exists=False)
        BookmarkUtils.getBookmarkFullName(name, folder)

        # create bookmark
        ScenegraphBookmarkManager.CreateWorkingSetsBookmark(name, BookmarkUtils.WORKING_SETS_TO_SAVE)

        # create item
        if create_item:
            bookmark_item = self.createBookmarkItem(name)
            return bookmark_item

    def createNewFolder(self):
        new_folder_name = self.__getNewUniqueName("New Folder", self.rootItem(), item_type=AbstractStateManagerTab.FOLDER_ITEM, exists=False)
        folder_item = self.createNewFolderItem(new_folder_name)
        self.addBookmarkFolder(new_folder_name, folder_item)
        return folder_item


class StateManagerViewWidget(ShojiLayout):
    def __init__(self, parent=None):
        super(StateManagerViewWidget, self).__init__(parent)
        self._main_layout = ShojiLayout(self)
        self._gsv_view = GSVViewWidget(self)
        self._irf_view = IRFViewWidget(self)
        self._bookmarks_view = BookmarkViewWidget(self)
        self._state_view = StateManagerEditorWidget(self)

        self._main_layout.addWidget(self._state_view)
        self._main_layout.addWidget(self._gsv_view)
        self._main_layout.addWidget(self._irf_view)
        self._main_layout.addWidget(self._bookmarks_view)
        self._main_layout.setSizes([100, 100, 100, 100])

        # setup main layout
        QVBoxLayout(self)
        self.layout().addWidget(self._main_layout)

