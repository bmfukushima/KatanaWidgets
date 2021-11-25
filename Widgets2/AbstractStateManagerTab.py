from qtpy.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QWidget

from Katana import UI4, ScenegraphBookmarkManager, NodegraphAPI, Utils

from cgwidgets.widgets import ButtonInputWidget, StringInputWidget, LabelledInputWidget, ModelViewWidget
from cgwidgets.utils import getUniqueName

class AbstractStateManagerTab(QWidget):
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
    NAME = 'Abstract State Manager Tab'
    FOLDER_ITEM = "folder"
    STATE_ITEM = "state"
    def __init__(self, parent=None):
        super(AbstractStateManagerTab, self).__init__(parent)
        # setup default attrs

        # create main organizer
        self._organizer_widget = QLabel("place holder")

        # create input buttons
        self._last_active_widget = StringInputWidget(self)
        self._last_active_widget.setReadOnly(True)
        self._last_active_labelled_widget = LabelledInputWidget(
            self, name="Last Active", delegate_widget=self._last_active_widget, default_label_length=150)
        self._last_active_labelled_widget.setViewAsReadOnly(True)

        # additional buttons
        self._utils_layout = QHBoxLayout()
        self._load_button_widget = ButtonInputWidget(
            self, title="Load", user_clicked_event=self.loadEvent)

        self._update_button = ButtonInputWidget(
            self, title="Update", user_clicked_event=self.updateEvent)

        self._create_new_folder_widget = ButtonInputWidget(
            title="New Folder", user_clicked_event=self.createNewFolderEvent)

        self._utils_layout.addWidget(self._load_button_widget)
        self._utils_layout.addWidget(self._update_button)
        self._utils_layout.addWidget(self._create_new_folder_widget)

        # setup layout
        QVBoxLayout(self)
        self.layout().addWidget(self._last_active_labelled_widget)
        self.layout().addLayout(self._utils_layout)
        self.layout().addWidget(self._organizer_widget)

        self.layout().setStretch(0, 0)
        self.layout().setStretch(1, 0)

    """ SETUP WIDGETS """
    def setOrganizerWidget(self, organizer_widget):
        """Sets the organizer widget to the one provided"""
        self.layout().itemAt(2).widget().setParent(None)
        self.layout().addWidget(organizer_widget)
        self._organizer_widget = organizer_widget
        self.layout().setStretch(2, 1)

    def addUtilsButton(self, utils_widget):
        """ Adds a widget to the utils bar.

        The utils bar that starts with the load/save buttons """
        self._utils_layout.addWidget(utils_widget)

    """ SETUP EVENTS """
    def createNewFolderEvent(self, widget):
        self.__create_new_folder_event()

    def setCreateNewFolderEvent(self, event):
        self.__create_new_folder_event = event

    def __create_new_folder_event(self):
        pass

    def loadEvent(self, widget):
        self.__load_event()

    def setLoadEvent(self, event):
        self.__load_event = event

    def __load_event(self):
        pass

    def updateEvent(self, widget):
        self.__update_event()

    def setUpdateEvent(self, event):
        self.__update_event = event

    def __update_event(self):
        pass

    """ WIDGETS """
    def lastActiveWidget(self):
        return self._last_active_widget

    def utilsLayout(self):
        return self._utils_layout

    def organizerWidget(self):
        return self._organizer_widget


class AbstractStateManagerOrganizerWidget(ModelViewWidget):
    """ Organizer for different states, this is used for the State and Bookmark Managers

    Attributes:
        folders (dict): of bookmark folders
            ie {"folder_name": item}"""

    def __init__(self, parent=None):
        super(AbstractStateManagerOrganizerWidget, self).__init__(parent)
        self.setPresetViewType(ModelViewWidget.TREE_VIEW)
        self._folders = {}
        self.setHeaderData(["name", "type"])
        self.view().header().resizeSection(0, 300)

        # setup flags
        self.setIsEnableable(False)

    """ UTILS """
    def getUniqueName(self, name, parent, item_type=AbstractStateManagerTab.STATE_ITEM, exists=True):
        """ Gets a unique name for an item when it is created

        # todo fix this
        Args:
            name (str): name to search for
            parent (ModelViewItem): to check children of
            item_type (ITEM_TYPE):
            exists (bool): determines if the item exists prior to searching for the name or not"""
        # compile list of same item types
        children = []
        for child in parent.children():
            if child.getArg("type") == item_type:
                children.append(child.getArg("name"))

        return getUniqueName(name, children, exists=exists)

    """ PROPERTIES """
    def folders(self):
        return self._folders

    def addFolder(self, folder, folder_item):
        if folder not in self.folders().keys():
            self.folders()[folder] = folder_item

    def clearFolders(self):
        self._folders = {}

    def removeFolder(self, folder):
        if folder in self.folders().keys():
            del self.folders()[folder]

    def updateFolderName(self, old_name, new_name):
        folder_item = self.folders()[old_name]
        folder_item.setArg("folder", new_name)
        self.removeFolder(old_name)
        self.addFolder(new_name, folder_item)

    """ CREATE """
    def createNewStateItem(self, state, folder_name=None):
        """ Creates a new state item.

        If a folder name is specified and it does not exist, the item will be created

        Args:
            state (str): name of state
            folder_name (str): name of folder"""
        # get folder
        folder_item = self.rootItem()
        if folder_name:
            if folder_name not in self.folders().keys():
                folder_item = self.createNewFolderItem(folder_name)
                self.addFolder(folder_name, folder_item)
            else:
                folder_item = self.folders()[folder_name]
        parent_index = self.getIndexFromItem(folder_item)

        # setup data
        data = {"name": state, "folder": folder_name, "type": AbstractStateManagerTab.STATE_ITEM}

        # create item
        state_index = self.insertNewIndex(
            0,
            name=state,
            column_data=data,
            is_deletable=True,
            is_dropable=False,
            is_dragable=True,
            parent=parent_index
        )
        state_item = state_index.internalPointer()
        return state_item

    def createNewFolderItem(self, folder):
        data = {"name": folder, "folder": folder, "type": AbstractStateManagerTab.FOLDER_ITEM}
        folder_index = self.insertNewIndex(
            0,
            name=folder,
            column_data=data,
            is_deletable=True,
            is_dropable=True,
            is_dragable=False
        )
        folder_item = folder_index.internalPointer()
        return folder_item

