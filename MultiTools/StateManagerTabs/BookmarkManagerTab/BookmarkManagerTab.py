"""
Todo:
    *   Update... destroying the folder
    *   Delete Bookmarks (delete event <>)
            <> don't work for some reason... have to manually delete
    *   Flush Caches...
            attach something to this?
            F5 refresh? Event Filter?

Bookmarks are actually parameters...

root_node = NodegraphAPI.GetRootNode()
param = root_node.getParameter("scenegraphBookmarks")
for child in param.getChildren():
    print("|-", child, child.getChild("name").getValue(0))
    
    for grandchild in child.getChildren():
        print("|\t|-", grandchild)

katanaMain._last_active_bookmark = last/bookmark

        

/bin/python/PyUtilModule/ScenegraphBookmarkManager.py

|- <NodegraphAPI_cmodule.Parameter object at 0x7fad24886ab0 group 'folder_name2'>
|	|- <NodegraphAPI_cmodule.Parameter object at 0x7fad24886e30 string 'name'>
|	|- <NodegraphAPI_cmodule.Parameter object at 0x7fad248868f0 string 'scenegraphExpansion'>
|	|- <NodegraphAPI_cmodule.Parameter object at 0x7fad2489c370 string 'viewerVisibility'>
|	|- <NodegraphAPI_cmodule.Parameter object at 0x7fad24892270 string 'scenegraphPinning'>
|	|- <NodegraphAPI_cmodule.Parameter object at 0x7fad24892d30 string 'render'>
|	|- <NodegraphAPI_cmodule.Parameter object at 0x7fad248a0a70 string 'scenegraphSelection'>

"""

from qtpy.QtWidgets import QVBoxLayout, QWidget, QHBoxLayout, QLabel
from qtpy.QtCore import Qt

# from PyUtilModule import ScenegraphBookmarkManager
from Katana import UI4, ScenegraphBookmarkManager, NodegraphAPI, Utils

from cgwidgets.widgets import ModelViewWidget, ButtonInputWidget, StringInputWidget, LabelledInputWidget
from cgwidgets.views import AbstractDragDropModelDelegate

from .BookmarkUtils import BookmarkUtils

from Widgets2 import AbstractStateManagerTab, AbstractStateManagerOrganizerWidget
from Utils2 import widgetutils


class BookmarkManagerTab(UI4.Tabs.BaseTab):
    """A tab for users to manager their IRFs with

    Widgets:
        |- QVBoxLayout
            |- active_bookmarks_labelled_widget --> (LabelledInputWidget)
            |    |- active_bookmarks_widget --> (StringInputWidget)
            |- QHBoxLayout
            |    |- create_new_bookmark_widget --> (ButtonInputWidget)
            |    |- create_new_category_widget --> (ButtonInputWidget)
            |- organizer_widget (ModelViewWidget)
    Attributes:
        working_sets (list): of strings of the working sets to save
            ["liveRenderUpdates", "render", "scenegraphExpansion", "scenegraphPinning", "scenegraphSelection", "viewerVisibility"]
    """
    NAME = 'Bookmark Manager'

    def __init__(self, parent=None):
        super(BookmarkManagerTab, self).__init__(parent)
        # setup main layout
        QVBoxLayout(self)
        self._main_widget = AbstractStateManagerTab()
        self.layout().addWidget(self._main_widget)

        # setup organizer
        self._bookmark_organizer_widget = BookmarkOrganizerWidget(self)
        self._main_widget.setOrganizerWidget(self._bookmark_organizer_widget)

        # create input buttons
        self._create_new_bookmark_widget = ButtonInputWidget(
            title="New Bookmark", user_clicked_event=self.createNewBookmark)
        self._main_widget.addUtilsButton(self._create_new_bookmark_widget)

        # setup events
        self._main_widget.setLoadEvent(self.loadEvent)
        self._main_widget.setUpdateEvent(self.updateEvent)
        self._main_widget.setCreateNewFolderEvent(self.createNewFolder)

    """ UTILS """
    def lastActiveBookmark(self):

        return self.mainWidget().lastActiveWidget().text()

    def update(self):
        # todo bookmarks update function
        # get active text
        if hasattr(widgetutils.katanaMainWindow(), "_last_active_bookmark"):
            full_name = widgetutils.katanaMainWindow()._last_active_bookmark
            self.mainWidget().lastActiveWidget().setText(full_name)
        pass

    """ EVENTS """
    def updateEvent(self):
        """ Saves the currently selected bookmark"""
        items = self.organizerWidget().getAllSelectedItems()
        if 0 < len(items):
            if items[0].getArg("type") == AbstractStateManagerTab.STATE_ITEM:

                folder = items[0].getArg("folder")
                name = items[0].getArg("name")

                # remove old bookmark
                BookmarkUtils.deleteBookmark(name, folder)

                Utils.EventModule.ProcessAllEvents()

                # create new bookmark
                self.organizerWidget().createNewBookmark(name, folder, create_item=False)

    def loadEvent(self):
        """ Loads the currently selected bookmark """
        items = self.organizerWidget().getAllSelectedItems()
        if 0 < len(items):
            if items[0].getArg("type") == AbstractStateManagerTab.STATE_ITEM:
                folder = items[0].getArg("folder")
                name = items[0].getArg("name")
                full_name = BookmarkUtils.getBookmarkFullName(name, folder)

                for bookmark in BookmarkUtils.bookmarks():
                    if bookmark["fullName"] == full_name:
                        # load bookmark
                        from PyUtilModule import ScenegraphBookmarkManager as SBM
                        """ Doing a special load here to ensure we're using the same module that the default
                        handler uses.  This needs to be done, as there is a monkey patch, to store the active
                        bookmark on katanaMainWindow()._last_active_bookmark"""
                        SBM.LoadBookmark(bookmark)

                        # update attrs
                        self.mainWidget().lastActiveWidget().setText(full_name)

                        return

        print("No bookmark found to load...")

    def createNewBookmark(self, widget):
        """ Creates a new bookmark category item

        Args:
            category (str): name of category to create"""
        return self.organizerWidget().createNewBookmark()

    def createNewFolder(self):
        return self.organizerWidget().createNewFolder()

    """ WIDGETS """
    def mainWidget(self):
        return self._main_widget

    def organizerWidget(self):
        return self._bookmark_organizer_widget


class BookmarkOrganizerWidget(AbstractStateManagerOrganizerWidget):
    """ Organizer widget where users can create/delete/modify bookmarks"""

    def __init__(self, parent=None):
        super(BookmarkOrganizerWidget, self).__init__(parent)

        # setup events
        self.setItemDeleteEvent(self.__bookmarkDeleteEvent)
        self.setTextChangedEvent(self.__bookmarkRenameEvent)
        self.setDropEvent(self.__bookmarkReparentEvent)

        self.populate()

    """ CREATE """
    def createNewBookmark(self, name=None, folder=None, create_item=True):
        """ Creates a new Scenegraph Bookmark

        Args:
            name (str):
            folder (str):
            create_item (bool): Determines if the item should be created or not"""
        if not name:
            name = self.getUniqueName(
                "New Bookmark", self.rootItem(), item_type=AbstractStateManagerTab.STATE_ITEM, exists=False)
        # BookmarkUtils.getBookmarkFullName(name, folder)

        # create bookmark
        full_name = BookmarkUtils.getBookmarkFullName(name, folder)
        ScenegraphBookmarkManager.CreateWorkingSetsBookmark(full_name, BookmarkUtils.WORKING_SETS_TO_SAVE)
        # create item
        if create_item:
            bookmark_item = self.createNewBookmarkItem(name, folder_name=folder)
            return bookmark_item

    """ UTILS """
    def populate(self):
        # clear old UI
        self.clearModel()
        self.clearFolders()

        # preflight
        if not BookmarkUtils.getBookmarkMasterParam(): return

        # populate
        for bookmark_param in BookmarkUtils.getBookmarkMasterParam().getChildren():
            full_name = bookmark_param.getChild("name").getValue(0)
            folder_name = BookmarkUtils.getBookmarkFolderFromFullName(full_name)
            bookmark_name = BookmarkUtils.getBookmarkNameFromFullName(full_name)

            # setup bookmark
            self.createNewBookmarkItem(bookmark_name, folder_name)

    """ EVENTS """
    def createNewBookmarkItem(self, state, folder_name=None, data=None):
        """ Creates a new state item.

        If a folder name is specified and it does not exist, the item will be created

        Args:
            state (str): name of state
            folder_name (str): name of folder
            data (dict): of additional data to be added to the items
            parent (QModelIndex): to be the parent
                Note: if this is provided, it will overwrite the folder_name input"""
        # get folder
        folder_item = self.rootItem()
        if folder_name:
            if folder_name not in self.folders().keys():
                folder_item = self.createNewFolderItem(folder_name)
                self.addFolder(folder_name, folder_item)
            else:
                folder_item = self.folders()[folder_name]
        parent_index = self.getIndexFromItem(folder_item)
        AbstractStateManagerOrganizerWidget.createNewStateItem(self, state, folder_name, data=data, parent=parent_index)

    def __bookmarkRenameEvent(self, item, old_name, new_name):
        """ When a user renames a bookmark, this will update the bookmarks/folder associated with the rename"""
        # preflight
        if old_name == new_name: return

        # rename bookmark
        if item.getArg("type") == AbstractStateManagerTab.STATE_ITEM:
            new_name = self.getUniqueName(new_name, item.parent(), item_type=AbstractStateManagerTab.STATE_ITEM)
            folder = item.getArg("folder")
            old_full_name = BookmarkUtils.getBookmarkFullName(old_name, folder)
            new_full_name = BookmarkUtils.getBookmarkFullName(new_name, folder)
            BookmarkUtils.updateBookmarkName(old_full_name, new_full_name)

        # rename folder
        if item.getArg("type") == AbstractStateManagerTab.FOLDER_ITEM:
            for child in item.children():
                # update bookmarks
                bookmark_name = child.getArg("name")
                folder_old_name = child.getArg("folder")
                #folder_new_name = new_name
                BookmarkUtils.updateBookmarkFolder(bookmark_name, bookmark_name, folder_old_name, new_name)

                # update internal property
                child.setArg("folder", new_name)

            # update folder item
            self.updateFolderName(old_name, new_name)

        # update items name
        item.setArg("name", new_name)

    def __bookmarkDeleteEvent(self, item):
        """ When the user deletes an item, this will delete the bookmark/folder associated with the item"""
        # delete bookmark
        if item.getArg("type") == AbstractStateManagerTab.STATE_ITEM:
            folder = item.getArg("folder")
            name = item.getArg("name")
            BookmarkUtils.deleteBookmark(name, folder)

        # delete folder
        if item.getArg("type") == AbstractStateManagerTab.FOLDER_ITEM:
            # remove bookmarks
            for child in item.children():
                self.__bookmarkDeleteEvent(child)

            # update internal property
            self.removeFolder(item.getArg("name"))

    def __bookmarkReparentEvent(self, data, items, model, row, parent):
        """ On drop, reparent the bookmark"""
        for item in items:
            # get attrs
            folder_old_name = item.getArg("folder")
            if parent == self.rootItem():
                folder_new_name = None
            else:
                folder_new_name = parent.name()
            old_name = item.getArg("name")
            new_name = self.getUniqueName(old_name, item.parent(), item_type=AbstractStateManagerTab.STATE_ITEM)

            # reset folder_new_name arg
            item.setArg("folder", folder_new_name)
            item.setArg("name", new_name)

            # update folder
            BookmarkUtils.updateBookmarkFolder(new_name, old_name, folder_old_name, folder_new_name)

    def showEvent(self, event):
        self.populate()
        return AbstractStateManagerOrganizerWidget.showEvent(self, event)

    # def keyPressEvent(self, event):
    #     if event.key() == Qt.Key_F5:
    #         self.populate()
    #     return ModelViewWidget.keyPressEvent(self, event)


class OrganizerDelegateWidget(AbstractDragDropModelDelegate):
    def __init__(self, parent=None):
        super(OrganizerDelegateWidget, self).__init__(parent)

    def createEditor(self, parent, option, index):
        """ Creates the editor widget.

        This is needed to set a different delegate for different columns"""
        if index.column() == 0:
            return AbstractDragDropModelDelegate.createEditor(self, parent, option, index)
        else:
            return None