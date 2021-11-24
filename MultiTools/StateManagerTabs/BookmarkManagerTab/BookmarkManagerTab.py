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
    print("|-", child)
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
    *   Rename
            - Need a better system for getting the parameter
                This will break after a drag/drop or a lot of other things, as it has a hard time finding the right param
            
"""

from qtpy.QtWidgets import QVBoxLayout, QWidget, QHBoxLayout

from Katana import UI4, ScenegraphBookmarkManager, NodegraphAPI

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
        self._bookmark_organizer_widget.setPresetViewType(ModelViewWidget.TREE_VIEW)

        # create input buttons
        self._create_new_bookmark_widget = ButtonInputWidget(
            title="Create New Bookmark", user_clicked_event=self.createNewBookmark)
        self._create_new_folder_widget = ButtonInputWidget(
            title="Create New Category", user_clicked_event=self.createNewFolder)
        self._create_bookmarks_layout = QHBoxLayout()
        self._create_bookmarks_layout.addWidget(self._create_new_bookmark_widget)
        self._create_bookmarks_layout.addWidget(self._create_new_folder_widget)

        self._active_bookmark_widget = StringInputWidget(self)
        self._active_bookmark_widget.setReadOnly(True)
        self._active_bookmark_labelled_widget = LabelledInputWidget(
            self, name="Active Bookmark", delegate_widget=self._active_bookmark_widget)

        # setup layout
        QVBoxLayout(self)
        self.layout().addWidget(self._active_bookmark_labelled_widget)
        self.layout().addLayout(self._create_bookmarks_layout)
        self.layout().addWidget(self._bookmark_organizer_widget)

        self.layout().setStretch(0, 0)
        self.layout().setStretch(1, 0)
        self.layout().setStretch(2, 1)

    def createNewBookmark(self, widget):
        """ Creates a new category item

        Args:
            category (str): name of category to create"""
        return self.bookmarkOrganizerWidget().createNewBookmark()

    def createNewFolder(self, widget):
        return self.bookmarkOrganizerWidget().createNewFolder()
        pass

    """ PROPERTIES """
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
        param_name = BookmarkManagerTab.getBookmarkFullName(bookmark, folder)
        return NodegraphAPI.GetRootNode().getParameter("scenegraphBookmarks.{bookmark_name}".format(bookmark_name=param_name))

    @staticmethod
    def getBookmarkParamFromFullName(full_name):
        """ Returns the bookmark parameter located on the root node

        Args:
            full_name (str): full name of bookmark
                ie folder_bookmarket
        Returns (Param):"""
        return NodegraphAPI.GetRootNode().getParameter("scenegraphBookmarks.{bookmark_name}".format(bookmark_name=full_name))

    """ UTILS """
    @staticmethod
    def getKatanaParamNameFromString(name):
        """ Converts a string to a Katana param name

        # todo convert string to katana param name
                Need to map out all illegal characters"""
        bad_chars = [" "]
        for char in bad_chars:
            name = name.replace(char, "_")
        return name

    @staticmethod
    def getBookmarkNameFromFullName(full_name):
        """ Gets the bookmarks name from a full name.

        Args:
            full_name (str): full name of bookmark"""
        separators = ["/", "_"]
        for separator in separators:
            if separator in full_name:
                return full_name.split(separator)[0]
        return full_name

    @staticmethod
    def updateBookmarkName(old_full_name, new_full_name):
        """ Updates the bookmarks name

        Args:
            old_full_name (str):
            new_full_name (str):"""
        old_full_name = BookmarkManagerTab.getKatanaParamNameFromString(old_full_name)

        bookmark_param = BookmarkManagerTab.getBookmarkParamFromFullName(BookmarkManagerTab.getKatanaParamNameFromString(old_full_name))
        bookmark_param.setName(BookmarkManagerTab.getKatanaParamNameFromString(new_full_name))
        bookmark_param.getChild("name").setValue(new_full_name, 0)

    @staticmethod
    def updateBookmarkFolder(bookmark_name, folder_old_name, folder_new_name):
        old_full_name = BookmarkManagerTab.getBookmarkFullName(bookmark_name, folder_old_name)
        new_full_name = BookmarkManagerTab.getBookmarkFullName(bookmark_name, folder_new_name)
        BookmarkManagerTab.updateBookmarkName(old_full_name, new_full_name)

    @staticmethod
    def getBookmarkFullName(bookmark, folder=None):
        """ Returns the full name of the bookmark folderName/bookmarkName"""
        return "/".join(filter(None, [folder, bookmark]))

    """ WIDGETS """
    def activeBookmarkWidget(self):
        return self._active_bookmark_widget

    def bookmarkOrganizerWidget(self):
        return self._bookmark_organizer_widget


class BookmarkOrganizerWidget(ModelViewWidget):
    """ Organizer widget where users can create/delete/modify bookmarks

    Attributes:
        bookmark_folders (list): of names of the currently available bookmark folders"""
    def __init__(self, parent=None):
        super(BookmarkOrganizerWidget, self).__init__(parent)
        self._bookmark_folders = ScenegraphBookmarkManager.GetScenegraphFolders()
        self.setHeaderData(["name", "type"])
        # setup flags
        self.setIsEnableable(False)

        # setup events
        self.setItemDeleteEvent(self.__bookmarkDeleteEvent)
        self.setTextChangedEvent(self.__bookmarkRenameEvent)
        self.setDropEvent(self.__bookmarkReparentEvent)

    """ CREATE """
    def createBookmarkItem(self, bookmark, folder=None):
        data = {"name": bookmark, "folder": folder, "type": BOOKMARK}
        bookmark_index = self.insertNewIndex(
            0,
            name=bookmark,
            column_data=data,
            is_deletable=True,
            is_dropable=False,
            is_dragable=True
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

    def createNewBookmark(self):
        new_bookmark_name = self.__getNewUniqueName("New Bookmark", self.rootItem(), item_type=BOOKMARK, exists=False)
        bookmark_item = self.createBookmarkItem(new_bookmark_name)
        ScenegraphBookmarkManager.CreateWorkingSetsBookmark(new_bookmark_name, BookmarkManagerTab.WORKING_SETS_TO_SAVE)
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
        pass

    """ PROPERTIES """
    def bookmarkFolders(self):
        return self._bookmark_folders

    def removeBookmarkFolder(self, folder):
        if folder in self.bookmarkFolders():
            self.bookmarkFolders().remove(folder)

    def addBookmarkFolder(self, folder):
        if folder not in self.bookmarkFolders():
            self.bookmarkFolders().append(folder)

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
            ScenegraphBookmarkManager.DeleteScenegraphBookmark(
                BookmarkManagerTab.getBookmarkFullName(name, folder))

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