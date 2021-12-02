from qtpy.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QWidget
from qtpy.QtCore import QModelIndex

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

    """ UTILS """
    def setLastActive(self, last_active):
        self.lastActiveWidget().setText(last_active)

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

    def createNewFolderButton(self):
        return self._create_new_folder_widget

    def loadButton(self):
        return self._load_button_widget

    def updateButton(self):
        return self._update_button


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

        self.addContextMenuEvent("Print Data", self.__printData)

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

    def __printData(self, index, indexes):
        if index.internalPointer():
            print("folder == ", index.internalPointer().getArg("folder"))
            print("name == ", index.internalPointer().getArg("name"))

    def populate(self):
        pass

    def update(self):
        self.clearModel()
        self.populate()

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
    def createNewStateItem(self, state, folder_name=None, data=None, parent=QModelIndex(), row=0):
        """ Creates a new state item.

        If a folder name is specified and it does not exist, the item will be created

        Args:
            state (str): name of state
            folder_name (str): name of folder
            data (dict): of additional data to be added to the items
            parent (QModelIndex): to be the parent
                Note: if this is provided, it will overwrite the folder_name input
            row (int): row to insert item, default is 0"""


        # setup data
        item_data = {"name": state, "folder": folder_name, "type": AbstractStateManagerTab.STATE_ITEM}
        if data:
            item_data.update(data)

        # create item
        state_index = self.insertNewIndex(
            row,
            name=state,
            column_data=item_data,
            is_deletable=True,
            is_droppable=False,
            is_draggable=True,
            parent=parent
        )
        state_item = state_index.internalPointer()
        return state_item

    def createNewFolderItem(self, folder, is_draggable=False, parent=QModelIndex()):
        """ Creates a new folder item and returns it

        Args:
            folder (str):
            is_draggable (bool):
            parent (QModelIndex)"""
        data = {"name": folder, "folder": folder, "type": AbstractStateManagerTab.FOLDER_ITEM}
        folder_index = self.insertNewIndex(
            0,
            name=folder,
            parent=parent,
            column_data=data,
            is_deletable=True,
            is_droppable=True,
            is_draggable=is_draggable
        )
        folder_item = folder_index.internalPointer()
        return folder_item

    def createNewFolder(self):
        new_folder_name = self.getUniqueName("New Folder", self.rootItem(), item_type=AbstractStateManagerTab.FOLDER_ITEM, exists=False)
        folder_item = self.createNewFolderItem(new_folder_name)
        self.addFolder(new_folder_name, folder_item)
        return folder_item