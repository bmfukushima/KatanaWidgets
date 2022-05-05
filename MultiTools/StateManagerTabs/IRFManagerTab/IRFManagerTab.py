"""TODO
    *   On load, populate (update on nodegraph load)
    *   Move default IRF Node to create
    *   Create
            - Conflicting names
                - Currently this just automagically works...
                - should do a check to make sure that there are no conflicting names

Create
    - Can create new categories/filters.
    - Categories MUST have atleast one filter in them, or else they will be deleted
    - New filters/categories can be created by RMB --> Create Category/Filter
    - Drag/Drop to reorganize
    - Changing a category name will update all IRFs category names
    - Changing a filters name, will update only the filter

Hierarchy:
    IRFManagerTab --> UI4.Tabs.BaseTab
        |- QVBoxLayout
            |- main_widget --> (ShojiModelViewWidget)
                |- view_widget --> (ViewActiveFiltersOrganizerWidget)
                |- activation_widget --> (ShojiLayout)
                |    |- QWidget
                |    |    |- QVBoxLayout
                |    |        |- QLabel
                |    |        |- _available_filters_organizer_widget --> (ActivateAvailableFiltersOrganizerWidget)
                |    |- QWidget
                |        |- QVBoxLayout
                |            |- QLabel
                |            |- _activated_filters_organizer_widget --> (ActivateActiveFiltersOrganizerWidget)
                |- create_widget --> (ShojiLayout)
                    |- QWidget
                    |    |- QVBoxLayout
                    |        |- irf_node_labelled_widget --> (LabelledInputWidget)
                    |        |   |- delegate --> (IRFNodeWidget)
                    |        |- QHBoxLayout
                    |            |- _create_new_filter_button --> (ButtonInputWidget)
                    |            |- _create_new_category_button --> (ButtonInputWidget)
                    |- irf_organizer_widget (CreateAvailableFiltersOrganizerWidget)
                    |- nodegraph_widget (GroupNodeEditorWidget)
"""

from qtpy.QtWidgets import QVBoxLayout, QLabel, QWidget, QSizePolicy, QHBoxLayout
from qtpy.QtCore import Qt

from Katana import UI4, NodegraphAPI, RenderManager, Utils

from cgwidgets.widgets import (
    ButtonInputWidget,
    ShojiModelViewWidget,
    ListInputWidget,
    LabelledInputWidget,
    ShojiLayout
)

from Utils2 import paramutils, irfutils, getFontSize
from Widgets2 import GroupNodeEditorWidget

from .IRFOrganizerWidget import (
    ActivateAvailableFiltersOrganizerWidget,
    ActivateActiveFiltersOrganizerWidget,
    CreateAvailableFiltersOrganizerWidget,
    ViewActiveFiltersOrganizerWidget
)


class IRFManagerTab(UI4.Tabs.BaseTab):
    """A tab for users to manager their IRFs with

    Widgets:
        irf_node_widget (ListInputWidget)
        main_widget (ShojiModelViewWidget):
        create_widget
        edit_widget:
        view_widget
    """
    NAME = 'State Managers/IRF Manager'

    def __init__(self, parent=None):
        super(IRFManagerTab, self).__init__(parent)
        # setup default attrs
        irfutils.setupDefaultIRFNode()

        # setup layout
        QVBoxLayout(self)

        self._main_widget = ShojiModelViewWidget(self)
        self._main_widget.setHeaderItemIsDeletable(False)
        self._view_widget = IRFViewWidget(parent=self)
        self._activation_widget = IRFActivationWidget(parent=self)
        self._create_widget = IRFCreateWidget(parent=self)

        # insert widgets
        self._main_widget.insertShojiWidget(0, column_data={"name":"View"}, widget=self._view_widget)
        self._main_widget.insertShojiWidget(1, column_data={"name":"Activate"}, widget=self._activation_widget)
        self._main_widget.insertShojiWidget(2, column_data={"name":"Create"}, widget=self._create_widget)

        self.layout().addWidget(self.mainWidget())
        # setup Katana events
        Utils.EventModule.RegisterCollapsedHandler(self.nodegraphLoad, 'nodegraph_loadEnd', None)

    def __name__(self):
        return IRFManagerTab.NAME

    """ UTILS """
    def update(self):
        self.activationWidget().update()
        self.viewWidget().update()

    """ WIDGETS """
    def irfNodeWidget(self):
        return self._irf_node_widget

    def createWidget(self):
        return self._create_widget

    def activationWidget(self):
        return self._activation_widget

    def mainWidget(self):
        return self._main_widget

    def viewWidget(self):
        return self._view_widget

    """ EVENTS """
    def showEvent(self, event):
        irfutils.setupDefaultIRFNode()
        return UI4.Tabs.BaseTab.showEvent(self, event)

    def nodegraphLoad(self, args):
        """ Updates all of the models views.  This only needs to update the activationWidget()
        as it stores views for both models on it.  Which should then propogate to the create/viewWidgets()"""
        self.activationWidget().update()


class IRFNodeWidget(ListInputWidget):
    """ Allows the user to choose which IRF Node they want to save their changes to"""
    def __init__(self, parent=None, item_list=[]):
        super(IRFNodeWidget, self).__init__(parent, item_list)
        self.setCleanItemsFunction(self.populateIRFNodes)
        self.setUserFinishedEditingEvent(self.updateDefaultIRFNode)

    def updateDefaultIRFNode(self, widget, value):
        if value in [node.getName() for node in irfutils.getAllRenderFilterContainers()]:
            node = NodegraphAPI.GetNode(value)
            irfutils.setDefaultIRFNode(node)

            # update all
        else:
            self.setText(irfutils.defaultIRFNode().getName())

    def populateIRFNodes(self):
        return [[node.getName()] for node in irfutils.getAllRenderFilterContainers()]


class IRFViewWidget(ViewActiveFiltersOrganizerWidget):
    def __init__(self, parent=None):
        super(IRFViewWidget, self).__init__(parent)


class IRFActivationWidget(ShojiLayout):
    """ Widget that will allow the user to enable/disable IRFs"""

    def __init__(self, parent=None):
        super(IRFActivationWidget, self).__init__(parent)

        # setup available filters widget
        self._available_filters_widget = QWidget()
        self._available_filters_layout = QVBoxLayout(self._available_filters_widget)
        self._available_filters_organizer_widget = ActivateAvailableFiltersOrganizerWidget(self)
        self._available_filters_layout.addWidget(QLabel("Available Filters"))
        self._available_filters_layout.addWidget(self._available_filters_organizer_widget)

        # setup active filters widget
        self._activated_filters_widget = QWidget()
        self._activated_filters_layout = QVBoxLayout(self._activated_filters_widget)
        self._activated_filters_organizer_widget = ActivateActiveFiltersOrganizerWidget(self)
        self._activated_filters_layout.addWidget(QLabel("Active Filters"))
        self._activated_filters_layout.addWidget(self._activated_filters_organizer_widget)

        # setup style
        self.setOrientation(Qt.Horizontal)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # setup main layout
        self.addWidget(self._available_filters_widget)
        self.addWidget(self._activated_filters_widget)

        self.setIsSoloViewEnabled(False)
        self.setIsSoloViewEnabled(True, override_children=False)

    def update(self):
        self.availableFiltersWidget().update()
        self.activatedFiltersWidget().update()

    def availableFiltersWidget(self):
        return self._available_filters_organizer_widget

    def activatedFiltersWidget(self):
        return self._activated_filters_organizer_widget


""" CREATE """
class IRFCreateWidget(ShojiLayout):
    """ Widget responsible for creating/modifying IRFs

    Widgets:
        irf_node_widget (ListInputWidget): The current InteractiveRenderFilters node that will be used
            when creating new filters
        irf_organizer_widget (ModelViewWidget): An organizational view of all of the IRF's in the scene.
            The user can rename, delete, edit the name/category, etc, of IRF's here.
        nodegraph_widget (GroupNodeEditorWidget): The area that the user can add nodes to the internal
            structure of the IRF.  Previously, this only had a list view, now it's a nodegraph.
    """
    def __init__(self, parent=None):
        super(IRFCreateWidget, self).__init__(parent)
        self.setObjectName("Create Widget")

        # setup gui
        self._irf_organizer_widget = CreateAvailableFiltersOrganizerWidget(self)

        self._create_new_items_widget = QWidget()
        self._create_new_items_layout = QVBoxLayout(self._create_new_items_widget)
        self._irf_node_widget = IRFNodeWidget(parent=self)
        self._irf_node_labelled_widget = LabelledInputWidget(
            name="Node", delegate_widget=self._irf_node_widget, default_label_length=100)
        self._irf_node_labelled_widget.setViewAsReadOnly(True)

        self._create_buttons_layout = QHBoxLayout()
        self._create_new_filter_button = ButtonInputWidget(title="New Filter", user_clicked_event=self.irfOrganizerWidget().createNewFilter)
        self._create_new_category_button = ButtonInputWidget(title="New Category", user_clicked_event=self.irfOrganizerWidget().createNewCategory)

        self._create_buttons_layout.addWidget(self._create_new_filter_button)
        self._create_buttons_layout.addWidget(self._create_new_category_button)

        self._create_new_items_layout.addWidget(self._irf_node_labelled_widget)
        self._create_new_items_layout.addLayout(self._create_buttons_layout)
        self._create_new_items_layout.addWidget(self._irf_organizer_widget)

        self._nodegraph_widget = GroupNodeEditorWidget(self, node=NodegraphAPI.GetRootNode())

        QVBoxLayout(self)
        self.addWidget(self._create_new_items_widget)
        self.addWidget(self._nodegraph_widget)

        # set default irf node
        self._irf_node_widget.setText(irfutils.defaultIRFNode().getName())

        # setup style
        self._create_new_filter_button.setFixedHeight(getFontSize() * 3)
        self._irf_node_labelled_widget.setFixedHeight(getFontSize() * 3)
        self._create_new_category_button.setFixedHeight(getFontSize() * 3)

        self.setIsSoloViewEnabled(False)
        self.setIsSoloViewEnabled(True, override_children=False)

        self.setSizes([100, 300])

    """ WIDGETS """
    def irfNodeWidget(self):
        return self._irf_node_widget

    def irfOrganizerWidget(self):
        return self._irf_organizer_widget

    def nodegraphWidget(self):
        return self._nodegraph_widget


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication

    from cgwidgets.utils import centerWidgetOnScreen, setAsAlwaysOnTop
    app = QApplication(sys.argv)

    widget = IRFManagerTab()
    setAsAlwaysOnTop(widget)
    widget.show()
    centerWidgetOnScreen(widget)

    sys.exit(app.exec_())