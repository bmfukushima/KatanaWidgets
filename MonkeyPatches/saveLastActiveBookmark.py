from PyUtilModule import ScenegraphBookmarkManager
from Utils2 import widgetutils


def saveLastActiveBookmark():

    def LoadBookmark(bookmarkDict, workingSetNames=None, excludeWorkingSetNames=None):
        """
        Loads a bookmark from the given dictionary of bookmark information.

        @type bookmarkDict: C{dict}
        @type workingSetNames: C{list} of C{str} or C{None}
        @type excludeWorkingSetNames: C{list} of C{str} or C{None}
        @param bookmarkDict: A dictionary containing information about the bookmark
            to be loaded.
        @param workingSetNames: A list of names of Working Sets from which to load
            bookmark information, or C{None} to load all Working Sets contained in
            the given bookmark.
        @param excludeWorkingSetNames: A list of names of Working Sets from which
            to skip loading bookmark information, or C{None} to load all available
            Working Sets contained in the given bookmark.
        @note: If a Working Set name is specified in both C{workingSetNames} and
            C{excludeWorkingSetNames}, the Working Set will be excluded.
        """
        widgetutils.katanaMainWindow()._last_active_bookmark = bookmarkDict["fullName"]
        ScenegraphBookmarkManager.LoadBookmarkOld(bookmarkDict, workingSetNames=None, excludeWorkingSetNames=None)

        return

    ScenegraphBookmarkManager.LoadBookmarkOld = ScenegraphBookmarkManager.LoadBookmark
    ScenegraphBookmarkManager.LoadBookmark = LoadBookmark
