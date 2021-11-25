from qtpy.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QWidget

from Katana import UI4, ScenegraphBookmarkManager, NodegraphAPI, Utils

from cgwidgets.widgets import ButtonInputWidget, StringInputWidget, LabelledInputWidget


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

        self._utils_layout.addWidget(self._load_button_widget)
        self._utils_layout.addWidget(self._update_button)

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
    def updateEvent(self, widget):
        self.__update_event()

    def setUpdateEvent(self, event):
        self.__update_event = event

    def loadEvent(self, widget):
        self.__load_event()

    def setLoadEvent(self, event):
        self.__load_event = event

    """ WIDGETS """
    def utilsLayout(self):
        return self._utils_layout

    def organizerWidget(self):
        return self._organizer_widget

