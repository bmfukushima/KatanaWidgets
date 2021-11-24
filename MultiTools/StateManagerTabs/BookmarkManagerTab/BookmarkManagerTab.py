"""From Stefan Habel via Discord
You can access scene graph bookmarks through the ScenegraphBookmarkManager module.

For example, ScenegraphBookmarkManager.GetScenegraphBookmarks() provides a list of dictionaries of scene graph bookmarks, each with entries such as a bookmark's full name, and the XML description of the various Working Set states. The full name may contain names of folders in which bookmarks are nested, with / serving as a path separator, .e.g 'My Folder Name/My Bookmark Name'.

For example, to print the full names of all available bookmarks:
for bookmark in ScenegraphBookmarkManager.GetScenegraphBookmarks():
    print(bookmark['fullName'])


The ScenegraphBookmarkManager module provides a function named LoadBookmark() that takes such a bookmark dictionary and activates the bookmark represented by it. Unfortunately, the name of that particular function was not included in the module's __all__ variable (this looks like a bug). That's why it appears that the function doesn't exist in the ScenegraphBookmarkManager module, as that module is made available as a "virtual" Katana module which only considers names that are exposed via __all__.

As a workaround, you can call the LoadBookmark() function by accessing the module directly from where it actually lives, which is  PyUtilModule.ScenegraphBookmarkManager, for example in a custom utility function like the following:
import PyUtilModule.ScenegraphBookmarkManager

bookmark = ScenegraphBookmarkManager.GetScenegraphBookmarks()["folder/bookmark"]

def ActivateBookmark(fullName):
    for bookmark in ScenegraphBookmarkManager.GetScenegraphBookmarks():
        if bookmark['fullName'] == fullName:
            PyUtilModule.ScenegraphBookmarkManager.LoadBookmark(bookmark)
            return

# get all bookmarks
Returns a dictionary of bookmarks with the keys
'name', 'scenegraphExpansion', 'render', 'viewerVisibility', 'scenegraphPinning', 'liveRenderUpdates', 'fullName', 'folder'
for bookmark in ScenegraphBookmarkManager.GetScenegraphBookmarks():
    print(bookmark.keys())
ScenegraphBookmarkManager.GetScenegraphBookmarks()


# create bookmark
workingSetsToSave = ["liveRenderUpdates", "render", "scenegraphExpansion", "scenegraphPinning", "scenegraphSelection", "viewerVisibility"]
ScenegraphBookmarkManager.CreateWorkingSetsBookmark("folder/test", workingSetsToSave)

# delete bookmark
ScenegraphBookmarkManager.DeleteScenegraphBookmark("folder/bookmark")

# load bookmark
ScenegraphBookmarkManager.LoadBookmark("folder/bookmark")
"""

"""
Bookmarks are actually parameters...

root_node = NodegraphAPI.GetRootNode()
param = root_node.getParameter("scenegraphBookmarks")
for child in param.getChildren():
    print("|-", child, child.getChild("name").getValue(0))
    
    for grandchild in child.getChildren():
        print("|\t|-", grandchild)

        

/bin/python/PyUtilModule/ScenegraphBookmarkManager.py

|- <NodegraphAPI_cmodule.Parameter object at 0x7fad24886ab0 group 'folder_name2'>
|	|- <NodegraphAPI_cmodule.Parameter object at 0x7fad24886e30 string 'name'>
|	|- <NodegraphAPI_cmodule.Parameter object at 0x7fad248868f0 string 'scenegraphExpansion'>
|	|- <NodegraphAPI_cmodule.Parameter object at 0x7fad2489c370 string 'viewerVisibility'>
|	|- <NodegraphAPI_cmodule.Parameter object at 0x7fad24892270 string 'scenegraphPinning'>
|	|- <NodegraphAPI_cmodule.Parameter object at 0x7fad24892d30 string 'render'>
|	|- <NodegraphAPI_cmodule.Parameter object at 0x7fad248a0a70 string 'scenegraphSelection'>

TODO
    *   Delete Bookmarks (delete event <>)
            <> don't work for some reason... have to manually delete
    *   Check Save/Load
    *   Flush Caches...
            attach something to this?
            F5 refresh? Event Filter?

"""

from qtpy.QtWidgets import QVBoxLayout, QWidget, QHBoxLayout
from qtpy.QtCore import Qt

from Katana import UI4, ScenegraphBookmarkManager, NodegraphAPI, Utils

from cgwidgets.widgets import ModelViewWidget, ButtonInputWidget, StringInputWidget, LabelledInputWidget
from cgwidgets.views import AbstractDragDropModelDelegate

BOOKMARK = "bookmark"
FOLDER = "folder"

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
    WORKING_SETS_TO_SAVE = ["liveRenderUpdates", "render", "scenegraphExpansion", "scenegraphPinning", "scenegraphSelection", "viewerVisibility"]

    def __init__(self, parent=None):
        super(BookmarkManagerTab, self).__init__(parent)
        # setup default attrs

        # create main organizer
        self._bookmark_organizer_widget = BookmarkOrganizerWidget(self)

        # create input buttons
        self._create_new_bookmark_widget = ButtonInputWidget(
            title="New Bookmark", user_clicked_event=self.createNewBookmark)
        self._create_new_folder_widget = ButtonInputWidget(
            title="New Category", user_clicked_event=self.createNewFolder)
        self._create_bookmarks_layout = QHBoxLayout()
        self._create_bookmarks_layout.addWidget(self._create_new_bookmark_widget)
        self._create_bookmarks_layout.addWidget(self._create_new_folder_widget)

        self._active_bookmark_widget = StringInputWidget(self)
        self._active_bookmark_widget.setReadOnly(True)
        self._active_bookmark_labelled_widget = LabelledInputWidget(
            self, name="Active Bookmark", delegate_widget=self._active_bookmark_widget, default_label_length=150)

        # additional buttons
        #self._save_layout = QHBoxLayout()
        self._load_button_widget = ButtonInputWidget(
            self, title="Load", user_clicked_event=self.loadEvent)

        self._update_button = ButtonInputWidget(
            self, title="Update", user_clicked_event=self.updateEvent)

        self._create_bookmarks_layout.addWidget(self._load_button_widget)
        self._create_bookmarks_layout.addWidget(self._update_button)

        # setup layout
        QVBoxLayout(self)
        self.layout().addWidget(self._active_bookmark_labelled_widget)
        self.layout().addLayout(self._create_bookmarks_layout)
        # self.layout().addLayout(self._save_layout)
        self.layout().addWidget(self._bookmark_organizer_widget)

        self.layout().setStretch(0, 0)
        self.layout().setStretch(1, 0)
        self.layout().setStretch(2, 1)
        #self.layout().setStretch(3, 1)

    """ EVENTS """
    def updateEvent(self, widget):
        """ Saves the currently selected bookmark"""
        items = self.bookmarkOrganizerWidget().getAllSelectedItems()
        if 0 < len(items):
            if items[0].getArg("type") == BOOKMARK:

                folder = items[0].getArg("folder")
                name = items[0].getArg("name")

                # remove old bookmark
                BookmarkManagerTab.deleteBookmark(name, folder)

                Utils.EventModule.ProcessAllEvents()

                # create new bookmark
                self.bookmarkOrganizerWidget().createNewBookmark(name, folder, create_item=False)

    def loadEvent(self, widget):
        """ Loads the currently selected bookmark """
        items = self.bookmarkOrganizerWidget().getAllSelectedItems()
        if 0 < len(items):
            if items[0].getArg("type") == BOOKMARK:
                folder = items[0].getArg("folder")
                name = items[0].getArg("name")
                full_name = BookmarkManagerTab.getBookmarkFullName(name, folder)

                for bookmark in BookmarkManagerTab.bookmarks():
                    if bookmark["fullName"] == full_name:
                        ScenegraphBookmarkManager.LoadBookmark(bookmark)
                        return

        print("No bookmark found to load...")

    def createNewBookmark(self, widget):
        """ Creates a new bookmark category item

        Args:
            category (str): name of category to create"""
        return self.bookmarkOrganizerWidget().createNewBookmark()

    def createNewFolder(self, widget):
        return self.bookmarkOrganizerWidget().createNewFolder()
        pass

    """ PROPERTIES """
    @staticmethod
    def getBookmarkMasterParam():
        return NodegraphAPI.GetRootNode().getParameter("scenegraphBookmarks")

    @staticmethod
    def bookmarks():
        """ Returns a list of all of the scenegraph bookmarks.

        Each item is a dictionary consisting of:
            dict_keys(['name', 'scenegraphExpansion', 'viewerVisibility', 'scenegraphPinning', 'render', 'scenegraphSelection', 'fullName', 'folder'])
        """
        return ScenegraphBookmarkManager.GetScenegraphBookmarks()

    @staticmethod
    def bookmarkFolders():
        """ Returns a list of the names of all the bookmark folders"""
        return ScenegraphBookmarkManager.GetScenegraphFolders()

    @staticmethod
    def getBookmarkParam(bookmark, folder=None):
        """ Returns the bookmark parameter located on the root node

        Args:
            bookmark (str):
            folder (str):

        Returns (Param):"""
        bookmarks_param = BookmarkManagerTab.getBookmarkMasterParam()
        for bookmark in bookmarks_param.getChildren():
            if bookmark.getChild("name").getValue(0) == BookmarkManagerTab.getBookmarkFullName(bookmark, folder):
                return bookmark

        return None
        # param_name = BookmarkManagerTab.getBookmarkFullName(bookmark, folder)
        # return NodegraphAPI.GetRootNode().getParameter("scenegraphBookmarks.{bookmark_name}".format(bookmark_name=param_name))

    @staticmethod
    def getBookmarkParamFromFullName(full_name):
        """ Returns the bookmark parameter located on the root node

        Args:
            full_name (str): full name of bookmark
                ie folder_bookmarket
        Returns (Param):"""
        bookmarks_param = BookmarkManagerTab.getBookmarkMasterParam()
        for bookmark in bookmarks_param.getChildren():
            if bookmark.getChild("name").getValue(0) == full_name:
                return bookmark

        return None

    """ UTILS """
    @staticmethod
    def deleteBookmark(bookmark, folder=None):
        full_name = BookmarkManagerTab.getBookmarkFullName(bookmark, folder)
        BookmarkManagerTab.deleteBookmarkFromFullName(full_name)

    @staticmethod
    def deleteBookmarkFromFullName(full_name):
        """ Deletes the bookmark parameter.  This is needed as the default delete
        handler relies on the actual name of the parameter group.

        Args:
            full_name (str): full path to bookmark"""
        param = BookmarkManagerTab.getBookmarkParamFromFullName(full_name)
        BookmarkManagerTab.getBookmarkMasterParam().deleteChild(param)

    @staticmethod
    def getBookmarkFullName(bookmark, folder=None):
        """ Returns the full name of the bookmark folderName/bookmarkName"""
        return "/".join(filter(None, [folder, bookmark]))

    @staticmethod
    def getBookmarkFolderFromFullName(full_name):
        """ Gets the bookmarks name from a full name.

        Args:
            full_name (str): full name of bookmark"""
        separators = ["/", "_"]
        for separator in separators:
            if separator in full_name:
                return full_name.split(separator)[0]
        return None

    @staticmethod
    def getBookmarkNameFromFullName(full_name):
        """ Gets the bookmarks name from a full name.

        Args:
            full_name (str): full name of bookmark"""
        separators = ["/", "_"]
        for separator in separators:
            if separator in full_name:
                return full_name.split(separator)[1]
        return full_name

    @staticmethod
    def updateBookmarkFolder(bookmark_name, folder_old_name, folder_new_name):
        old_full_name = BookmarkManagerTab.getBookmarkFullName(bookmark_name, folder_old_name)
        new_full_name = BookmarkManagerTab.getBookmarkFullName(bookmark_name, folder_new_name)
        BookmarkManagerTab.updateBookmarkName(old_full_name, new_full_name)

    @staticmethod
    def updateBookmarkName(old_full_name, new_full_name):
        """ Updates the bookmarks name

        Args:
            old_full_name (str):
            new_full_name (str):"""

        bookmark_param = BookmarkManagerTab.getBookmarkParamFromFullName(old_full_name)
        bookmark_param.getChild("name").setValue(new_full_name, 0)

    """ WIDGETS """
    def activeBookmarkWidget(self):
        return self._active_bookmark_widget

    def bookmarkOrganizerWidget(self):
        return self._bookmark_organizer_widget


class BookmarkOrganizerWidget(ModelViewWidget):
    """ Organizer widget where users can create/delete/modify bookmarks

    Attributes:
        bookmark_folders (dict): of bookmark folders
            ie {"folder_name": item}"""

    def __init__(self, parent=None):
        super(BookmarkOrganizerWidget, self).__init__(parent)
        self.setPresetViewType(ModelViewWidget.TREE_VIEW)
        self._bookmark_folders = {}
        self.setHeaderData(["name", "type"])
        self.view().header().resizeSection(0, 300)

        # setup flags
        self.setIsEnableable(False)

        # setup events
        self.setItemDeleteEvent(self.__bookmarkDeleteEvent)
        self.setTextChangedEvent(self.__bookmarkRenameEvent)
        self.setDropEvent(self.__bookmarkReparentEvent)

        self.addContextMenuEvent("print data", self.printData)

        self.populate()

    def printData(self, index, indexes):
        print("folder == ", index.internalPointer().getArg("folder"))
        print("name == ", index.internalPointer().getArg("name"))

    """ CREATE """
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
        data = {"name": bookmark, "folder": folder_name, "type": BOOKMARK}

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
        data = {"name": folder, "folder": folder, "type": FOLDER}
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
            name = self.__getNewUniqueName("New Bookmark", self.rootItem(), item_type=BOOKMARK, exists=False)
        BookmarkManagerTab.getBookmarkFullName(name, folder)

        # create bookmark
        ScenegraphBookmarkManager.CreateWorkingSetsBookmark(name, BookmarkManagerTab.WORKING_SETS_TO_SAVE)

        # create item
        if create_item:
            bookmark_item = self.createBookmarkItem(name)
            return bookmark_item

    def createNewFolder(self):
        new_folder_name = self.__getNewUniqueName("New Folder", self.rootItem(), item_type=FOLDER, exists=False)
        folder_item = self.createNewFolderItem(new_folder_name)
        self.addBookmarkFolder(new_folder_name)
        return folder_item

    """ UTILS """
    def __getNewUniqueName(self, name, parent, item_type=BOOKMARK, exists=True):
        """ Gets a unique name for an item when it is created

        # todo fix this
        Args:
            name (str): name to search for
            parent (ModelViewItem): to check children of
            item_type (ITEM_TYPE):
            exists (bool): determines if the item exists prior to searching for the name or not"""
        name = name
        # compile list of same item types
        children = []
        for child in parent.children():
            if child.getArg("type") == item_type:
                children.append(child.getArg("name"))

        # remove one instance of name, as it has already been added
        if exists:
            if name in children:
                children.remove(name)

        # get unique name of item
        if name in children:
            while name in children:
                try:
                    suffix = str(int(name[-1]) + 1)
                    name = name[:-1] + suffix
                except ValueError:
                    name = name + "0"

        return name

    def populate(self):
        if not BookmarkManagerTab.getBookmarkMasterParam(): return
        self.clearModel()

        for bookmark_param in BookmarkManagerTab.getBookmarkMasterParam().getChildren():
            full_name = bookmark_param.getChild("name").getValue(0)
            folder_name = BookmarkManagerTab.getBookmarkFolderFromFullName(full_name)
            bookmark_name = BookmarkManagerTab.getBookmarkNameFromFullName(full_name)

            # setup bookmark
            self.createBookmarkItem(bookmark_name, folder_name)

    """ PROPERTIES """
    def bookmarkFolders(self):
        return self._bookmark_folders

    def removeBookmarkFolder(self, folder):
        if folder in self.bookmarkFolders().keys():
            del self.bookmarkFolders()[folder]

    def addBookmarkFolder(self, folder, folder_item):
        if folder not in self.bookmarkFolders().keys():
            self.bookmarkFolders()[folder] = folder_item

    """ EVENTS """
    def __bookmarkRenameEvent(self, item, old_name, new_name):
        """ When a user renames a bookmark, this will update the bookmarks/folder associated with the rename"""
        # preflight
        if old_name == new_name: return

        # rename bookmark
        if item.getArg("type") == BOOKMARK:
            new_name = self.__getNewUniqueName(new_name, item.parent(), item_type=BOOKMARK)
            folder = item.getArg("folder")
            old_full_name = BookmarkManagerTab.getBookmarkFullName(old_name, folder)
            new_full_name = BookmarkManagerTab.getBookmarkFullName(new_name, folder)

            BookmarkManagerTab.updateBookmarkName(old_full_name, new_full_name)

        # rename folder
        if item.getArg("type") == FOLDER:
            for child in item.children():
                # update bookmarks
                bookmark_name = child.getArg("name")
                folder_old_name = child.getArg("folder")
                folder_new_name = new_name
                BookmarkManagerTab.updateBookmarkFolder(bookmark_name, folder_old_name, folder_new_name)

                # update internal property
                self.removeBookmarkFolder(old_name)
                self.addBookmarkFolder(new_name)

        # update items name
        item.setArg("name", new_name)

    def __bookmarkDeleteEvent(self, item):
        """ When the user deletes an item, this will delete the bookmark/folder associated with the item"""
        # delete bookmark
        if item.getArg("type") == BOOKMARK:
            folder = item.getArg("folder")
            name = item.getArg("name")
            BookmarkManagerTab.deleteBookmark(name, folder)

        # delete folder
        if item.getArg("type") == FOLDER:
            # remove bookmarks
            for child in item.children():
                self.__bookmarkDeleteEvent(child)

            # update internal property
            self.removeBookmarkFolder(item.getArg("name"))

    def __bookmarkReparentEvent(self, data, items, model, row, parent):
        """ On drop, reparent the bookmark"""
        for item in items:
            # get attrs
            folder_old_name = item.getArg("folder")
            if parent == self.rootItem():
                folder_new_name = None
            else:
                folder_new_name = parent.name()
            new_name = self.__getNewUniqueName(item.getArg("name"), item.parent(), item_type=BOOKMARK)

            # reset folder_new_name arg
            item.setArg("folder", folder_new_name)
            item.setArg("name", new_name)

            # update folder
            BookmarkManagerTab.updateBookmarkFolder(new_name, folder_old_name, folder_new_name)

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