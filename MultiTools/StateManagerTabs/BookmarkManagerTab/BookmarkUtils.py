from Katana import UI4, ScenegraphBookmarkManager, NodegraphAPI, Utils

class BookmarkUtils(object):
    WORKING_SETS_TO_SAVE = ["liveRenderUpdates", "render", "scenegraphExpansion", "scenegraphPinning", "scenegraphSelection", "viewerVisibility"]
    BOOKMARK = "bookmark"
    FOLDER = "folder"

    @staticmethod
    def getBookmarkMasterParam():
        return NodegraphAPI.GetRootNode().getParameter("scenegraphBookmarks")

    @staticmethod
    def bookmark(full_name):
        """ Returns as bookmark from the full name provided

        Args:
            full_name (str): path to bookmark"""
        for bookmark in ScenegraphBookmarkManager.GetScenegraphBookmarks():
            if bookmark['fullName'] == full_name:
                return bookmark
        return None

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
        bookmarks_param = BookmarkUtils.getBookmarkMasterParam()
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
        bookmarks_param = BookmarkUtils.getBookmarkMasterParam()
        for bookmark in bookmarks_param.getChildren():
            if bookmark.getChild("name").getValue(0) == full_name:
                return bookmark

        return None

    """ UTILS """
    @staticmethod
    def deleteBookmark(bookmark, folder=None):
        full_name = BookmarkUtils.getBookmarkFullName(bookmark, folder)
        BookmarkUtils.deleteBookmarkFromFullName(full_name)

    @staticmethod
    def deleteBookmarkFromFullName(full_name):
        """ Deletes the bookmark parameter.  This is needed as the default delete
        handler relies on the actual name of the parameter group.

        Args:
            full_name (str): full path to bookmark"""
        param = BookmarkUtils.getBookmarkParamFromFullName(full_name)
        BookmarkUtils.getBookmarkMasterParam().deleteChild(param)

    @staticmethod
    def getBookmarkFullName(bookmark, folder=None):
        """ Returns the full name of the bookmark folderName/bookmarkName"""
        fullname = "/".join(filter(None, [folder, bookmark]))
        return fullname

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
    def updateBookmarkFolder(bookmark_name, bookmark_old_name, folder_old_name, folder_new_name):
        """ Updates the bookmarks folder.

        The old bookmark name is required for searching for the update.  As this will look on
        the bookmarkParam for a match to the old name.

        Args:
            bookmark_name (str): new name of bookmark (if valid)
            bookmark_old_name (str): the old name of the bookmark
            folder_old_name (str): old name of folder
            folder_new_name (str): """
        old_full_name = BookmarkUtils.getBookmarkFullName(bookmark_old_name, folder_old_name)
        new_full_name = BookmarkUtils.getBookmarkFullName(bookmark_name, folder_new_name)
        BookmarkUtils.updateBookmarkName(old_full_name, new_full_name)

    @staticmethod
    def updateBookmarkName(old_full_name, new_full_name):
        """ Updates the bookmarks name

        Args:
            old_full_name (str):
            new_full_name (str):"""

        # todo this can't get the param sometimes?
        # same name drop
        bookmark_param = BookmarkUtils.getBookmarkParamFromFullName(old_full_name)
        bookmark_param.setName(new_full_name)
        bookmark_param.getChild("name").setValue(new_full_name, 0)

    """ DISPLAY """
    @staticmethod
    def updateLastActiveBookmarkDisplays(last_active_bookmark):
        """Sets the last active bookmark meta data, and updates all tabs

        Args:
            last_active_bookmark (str):"""

        # update attrs
        for tab in UI4.App.Tabs.GetTabsByType("State Managers/Bookmark Manager"):
            tab.setLastActiveBookmark(last_active_bookmark)
        for tab in UI4.App.Tabs.GetTabsByType("State Manager"):
            tab.viewWidget().bookmarksViewWidget().setLastActiveBookmark(last_active_bookmark)
        # todo update popup bar widgets
        for tab in UI4.App.Tabs.GetTabsByType('Popup Bar Displays/KatanaBebop/State Manager'):
            # get a list of all of the widgets
            popup_widgets = tab.popupBarDisplayWidget().allWidgets()

            for widget in popup_widgets:
                popup_widget = widget.popupWidget()
                if hasattr(popup_widget, "__name__"):
                    if popup_widget.__name__() == "State Managers/Bookmark Manager":
                        popup_widget.setLastActiveBookmark(last_active_bookmark)
                    if popup_widget.__name__() == "State Manager":
                        popup_widget.viewWidget().bookmarksViewWidget().setLastActiveBookmark(last_active_bookmark)