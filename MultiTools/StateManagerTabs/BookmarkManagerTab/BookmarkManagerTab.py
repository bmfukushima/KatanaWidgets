from qtpy.QtWidgets import QVBoxLayout, QWidget, QHBoxLayout

from Katana import UI4

from cgwidgets.widgets import ModelViewWidget, ButtonInputWidget
from cgwidgets.views import AbstractDragDropModelDelegate


class BookmarkManagerTab(UI4.Tabs.BaseTab):
    """A tab for users to manager their IRFs with

    Widgets:
        irf_node_widget (ListInputWidget)
        main_widget (ShojiModelViewWidget):
        create_widget
        edit_widget:
        view_widget
    """
    NAME = 'Bookmark Manager'

    def __init__(self, parent=None):
        super(BookmarkManagerTab, self).__init__(parent)
        # setup default attrs

        # setup layout
        QVBoxLayout(self)

        self._organizer_widget = ModelViewWidget(self)
        self._organizer_widget.setPresetViewType(ModelViewWidget.TREE_VIEW)

        self._create_bookmarks_layout = QHBoxLayout()
        self._create_new_bookmark_widget = ButtonInputWidget(
            title="Create New Bookmark", user_clicked_event=self.createNewBookmark)
        self._create_new_category_widget = ButtonInputWidget(
            title="Create New Category", user_clicked_event=self.createNewCategory)

    def createNewBookmark(self, widget):
        pass

    def createNewCategory(self, widget):
        pass

class BookmarkOrganizerWidget(ModelViewWidget):
    def __init__(self, parent=None):
        super(BookmarkOrganizerWidget, self).__init__(parent)

    def createNewBookmark(self):
        pass

    def createNewCategory(self):
        pass

    def populate(self):
        pass

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