"""You can access scene graph bookmarks through the ScenegraphBookmarkManager module.

For example, ScenegraphBookmarkManager.GetScenegraphBookmarks() provides a list of dictionaries of scene graph bookmarks, each with entries such as a bookmark's full name, and the XML description of the various Working Set states. The full name may contain names of folders in which bookmarks are nested, with / serving as a path separator, .e.g 'My Folder Name/My Bookmark Name'.

For example, to print the full names of all available bookmarks:
for bookmark in
""" ScenegraphBookmarkManager.GetScenegraphBookmarks():
    print(bookmark['fullName'])

"""
The ScenegraphBookmarkManager module provides a function named LoadBookmark() that takes such a bookmark dictionary and activates the bookmark represented by it. Unfortunately, the name of that particular function was not included in the module's __all__ variable (this looks like a bug). That's why it appears that the function doesn't exist in the ScenegraphBookmarkManager module, as that module is made available as a "virtual" Katana module which only considers names that are exposed via __all__.

As a workaround, you can call the LoadBookmark() function by accessing the module directly from where it actually lives, which is  PyUtilModule.ScenegraphBookmarkManager, for example in a custom utility function like the following:
import PyUtilModule.ScenegraphBookmarkManager
"""
def ActivateBookmark(fullName):
    for bookmark in ScenegraphBookmarkManager.GetScenegraphBookmarks():
        if bookmark['fullName'] == fullName:
            PyUtilModule.ScenegraphBookmarkManager.LoadBookmark(bookmark)
            return