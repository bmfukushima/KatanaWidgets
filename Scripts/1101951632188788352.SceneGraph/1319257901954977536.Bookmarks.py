""" From Stefan Habel via Discord
You can access scene graph bookmarks through the ScenegraphBookmarkManager module.

For example, ScenegraphBookmarkManager.GetScenegraphBookmarks() provides a list of dictionaries of scene graph bookmarks, each with entries such as a bookmark's full name, and the XML description of the various Working Set states. The full name may contain names of folders in which bookmarks are nested, with / serving as a path separator, .e.g 'My Folder Name/My Bookmark Name'.

For example, to print the full names of all available bookmarks:
for bookmark in ScenegraphBookmarkManager.GetScenegraphBookmarks():
    print(bookmark['fullName'])

The ScenegraphBookmarkManager module provides a function named LoadBookmark() that takes such a bookmark dictionary and activates the bookmark represented by it. Unfortunately, the name of that particular function was not included in the module's __all__ variable (this looks like a bug). That's why it appears that the function doesn't exist in the ScenegraphBookmarkManager module, as that module is made available as a "virtual" Katana module which only considers names that are exposed via __all__.

As a workaround, you can call the LoadBookmark() function by accessing the module directly from where it actually lives, which is  PyUtilModule.ScenegraphBookmarkManager, for example in a custom utility function like the following:
import PyUtilModule.ScenegraphBookmarkManager
"""
bookmark = ScenegraphBookmarkManager.GetScenegraphBookmarks()["folder/bookmark"]

def ActivateBookmark(fullName):
    for bookmark in ScenegraphBookmarkManager.GetScenegraphBookmarks():
        if bookmark['fullName'] == fullName:
            PyUtilModule.ScenegraphBookmarkManager.LoadBookmark(bookmark)
            return

# get all bookmarks
""" Returns a dictionary of bookmarks with the keys
'name', 'scenegraphExpansion', 'render', 'viewerVisibility', 'scenegraphPinning', 'liveRenderUpdates', 'fullName', 'folder'"""
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

from PyUtilModule import ScenegraphBookmarkManager

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
    print('test')
    ScenegraphBookmarkManager.LoadBookmarkOld(bookmarkDict, workingSetNames=None, excludeWorkingSetNames=None)

    return
ScenegraphBookmarkManager.LoadBookmarkOld = ScenegraphBookmarkManager.LoadBookmark
ScenegraphBookmarkManager.LoadBookmark = LoadBookmark
